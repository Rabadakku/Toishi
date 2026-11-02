"""Exports: a whole profile as one .meprofile file (EXP-2), and CSV logs (EXP-3).

A .meprofile is a zip with manifest.json, a consistent snapshot of user.db (backup
API) and the profile's media folder. Import treats the file as untrusted: only those
entries are accepted, paths are checked, sizes are capped, checksums and the database
are verified, and the profile is assembled in a staging folder that is renamed into
place only when everything checks out. Own media round-trip (v2, ADR-0011): export
refuses a profile whose cards point at a missing or damaged file, and import refuses
one whose user_media rows name an unsafe file or one the archive lacks or holds damaged.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import csv
import hashlib
import json
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

from core import __version__ as APP_VERSION
from core.storage import schema
from core.storage.backups import backup_database
from core.storage.clock import Clock, from_ms
from core.storage.connection import (
    Database,
    connect,
    fsync_path,
    full_fsync,
    integrity_problems,
)
from core.storage.errors import MediaError, ProfileError
from core.storage.media import FILE_NAME, MEDIA_DIR, check_file_name, file_intact, unsafe_name
from core.storage.user_store import count_rows

MEPROFILE_FORMAT = "meprofile"
MEPROFILE_VERSION = 1
MAX_UNPACKED_BYTES = 4 * 1024**3
MAX_ENTRIES = 100_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_files(media_dir: Path) -> Iterator[tuple[str, Path]]:
    if not media_dir.is_dir():
        return
    for path in sorted(media_dir.rglob("*")):
        if path.is_file() and not path.is_symlink():
            yield f"{MEDIA_DIR}/" + path.relative_to(media_dir).as_posix(), path


def _media_links(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(card, ref, file) of every own-card image (user_media, from schema v2 on)."""
    if schema.user_version(conn) < 2:
        return []
    found = conn.execute("SELECT card_id, ref, file FROM user_media ORDER BY card_id, ref")
    return [(str(r[0]), str(r[1]), str(r[2])) for r in found]


def export_profile(
    user_db: Path, media_dir: Path, dest: Path, *, name: str, clock: Clock
) -> dict[str, Any]:
    """Write a .meprofile (atomically) and return its manifest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent, prefix=".export-") as tmp:
        snapshot = Path(tmp) / "user.db"
        backup_database(user_db, snapshot)
        conn = connect(snapshot, mode="ro")
        try:
            version = schema.user_version(conn)
            counts = count_rows(conn)
            links = _media_links(conn)
        finally:
            conn.close()
        for card_id, ref, file in links:  # import would refuse these; say so now
            try:
                intact = file_intact(media_dir / check_file_name(file), file)
            except MediaError:
                intact = False
            if not intact:
                raise ProfileError(
                    f"the image {ref!r} of card {card_id} (media file {file}) is missing or "
                    "damaged; import that card's file again to store the image, then export"
                )
        files = {"user.db": _sha256(snapshot)}
        media = list(_media_files(media_dir))
        for arcname, path in media:  # import refuses these names; say so now, not then
            try:
                _safe_name(arcname)
            except ProfileError:
                raise ProfileError(
                    f"media file {path} cannot go in a .meprofile (its name has a "
                    "backslash or is too long); rename it and export again"
                ) from None
        files.update({arcname: _sha256(path) for arcname, path in media})
        manifest: dict[str, Any] = {
            "format": MEPROFILE_FORMAT,
            "version": MEPROFILE_VERSION,
            "name": name,
            "exported_at": clock.now_ms(),
            "schema_version": version,
            "app_version": APP_VERSION,
            "counts": counts,
            "files": files,
        }
        partial = Path(tmp) / "out.meprofile"
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            archive.write(snapshot, "user.db")
            for arcname, path in media:
                archive.write(path, arcname)
        fsync_path(partial)
        partial.replace(dest)
    fsync_path(dest.parent)
    return manifest


def _safe_name(name: str) -> PurePosixPath:
    if unsafe_name(name):
        raise ProfileError(f"unsafe path in profile file: {name!r}")
    return PurePosixPath(name)


def read_manifest(src: Path) -> dict[str, Any]:
    try:
        archive = zipfile.ZipFile(src)
    except (OSError, zipfile.BadZipFile) as error:
        raise ProfileError(f"cannot read {src}: {error}") from error
    with archive:
        return _manifest(archive)


def _manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read("manifest.json"))
    except (KeyError, ValueError) as error:
        raise ProfileError("not a .meprofile file (no readable manifest)") from error
    if not isinstance(manifest, dict) or manifest.get("format") != MEPROFILE_FORMAT:
        raise ProfileError("not a .meprofile file")
    if manifest.get("version") != MEPROFILE_VERSION:
        raise ProfileError(f"unsupported .meprofile version {manifest.get('version')!r}")
    if not isinstance(manifest.get("files"), dict) or "user.db" not in manifest["files"]:
        raise ProfileError(".meprofile manifest lists no user.db")
    return manifest


def import_profile(src: Path, target_root: Path) -> dict[str, Any]:
    """Unpack a .meprofile into a new profile folder; returns its manifest."""
    if target_root.exists() and any(target_root.iterdir()):
        raise ProfileError(f"{target_root} already holds a profile")
    try:
        archive = zipfile.ZipFile(src)
    except (OSError, zipfile.BadZipFile) as error:
        raise ProfileError(f"cannot read {src}: {error}") from error
    target_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=target_root.parent, prefix=".import-"))
    try:
        with archive:
            manifest = _manifest(archive)
            _unpack(archive, manifest, staging)
        _verify_user_db(staging / "user.db")
        _verify_media(staging / "user.db", manifest)
        (staging / "backups").mkdir(exist_ok=True)
        (staging / "media").mkdir(exist_ok=True)
        if target_root.exists():
            target_root.rmdir()  # empty, checked above
        staging.replace(target_root)
        fsync_path(target_root.parent)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def _unpack(archive: zipfile.ZipFile, manifest: dict[str, Any], staging: Path) -> None:
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES:
        raise ProfileError("too many entries in profile file")
    expected: dict[str, str] = manifest["files"]
    seen: set[str] = set()
    budget = MAX_UNPACKED_BYTES
    for info in entries:
        if info.is_dir() or info.filename == "manifest.json":
            continue
        name = _safe_name(info.filename)
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ProfileError(f"symbolic link in profile file: {info.filename}")
        if not (info.filename == "user.db" or (name.parts[0] == "media" and len(name.parts) > 1)):
            raise ProfileError(f"unexpected entry in profile file: {info.filename}")
        if info.filename not in expected or info.filename in seen:
            raise ProfileError(f"entry not in manifest (or repeated): {info.filename}")
        seen.add(info.filename)
        out = staging.joinpath(*name.parts)
        out.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        with archive.open(info) as source, out.open("xb") as sink:
            while chunk := source.read(1 << 20):
                budget -= len(chunk)
                if budget < 0:
                    raise ProfileError("profile file unpacks to more than 4 GiB")
                digest.update(chunk)
                sink.write(chunk)
            sink.flush()
            full_fsync(sink.fileno())
        if digest.hexdigest() != expected[info.filename]:
            raise ProfileError(f"checksum mismatch for {info.filename}")
    missing = set(expected) - seen
    if missing:
        raise ProfileError(f"profile file is missing {sorted(missing)[:5]}")


def _verify_user_db(path: Path) -> None:
    problems = integrity_problems(path)
    if problems:
        raise ProfileError(f"user.db in the profile file is damaged: {problems[:3]}")
    conn = connect(path, mode="ro")
    try:
        schema.check_user_db(conn)  # ours, and not newer than this app
    finally:
        conn.close()


def _verify_media(path: Path, manifest: dict[str, Any]) -> None:
    """Every own-card image the profile maps is a safe content-addressed name whose file
    came in the archive with the checksum its name says (checked against the bytes by
    _unpack)."""
    conn = connect(path, mode="ro")
    try:
        links = _media_links(conn)
    except sqlite3.Error as error:  # a v2 user.db without the v2 tables: not ours
        raise ProfileError(f"user.db in the profile file is not usable: {error}") from error
    finally:
        conn.close()
    files: dict[str, Any] = manifest["files"]
    for card_id, ref, file in links:
        try:
            match = FILE_NAME.fullmatch(check_file_name(str(file)))
        except MediaError:
            raise ProfileError(f"unsafe media file name in profile file: {file!r}") from None
        if match is None or files.get(f"{MEDIA_DIR}/{file}") != match.group(1):
            raise ProfileError(
                f"the image {ref!r} of card {card_id} (media file {file}) is missing or "
                "damaged in the profile file"
            )


# ---------------------------------------------------------------- CSV (EXP-3)

REVIEW_CSV_COLUMNS = (
    "id",
    "at_ms",
    "at_utc",
    "study_day",
    "attempt_id",
    "target_kind",
    "target_id",
    "target_ord",
    "rating",
    "rules_version",
    "params_id",
    "retention",
    "predicted_recall",
    "active_ms",
    "solve_ms",
    "state_before",
    "stability_before",
    "difficulty_before",
    "due_before",
    "last_review_before",
    "state_after",
    "stability_after",
    "difficulty_after",
    "due_after",
    "voided",
)


def _write_csv(dest: Path, header: tuple[str, ...], records: Iterator[list[Any]]) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    count = 0
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for record in records:
            writer.writerow(record)
            count += 1
        handle.flush()
        full_fsync(handle.fileno())
    tmp.replace(dest)
    return count


def export_review_log_csv(db: Database, dest: Path, *, include_voided: bool = False) -> int:
    """One row per FSRS event, ready for fitting elsewhere. Returns the row count."""
    where = "" if include_voided else "WHERE r.voided_by IS NULL"
    sql = (
        "SELECT r.*, a.study_day, a.active_ms, a.solve_ms FROM review_log r "
        f"JOIN attempt a ON a.id = r.attempt_id {where} ORDER BY r.id"
    )

    def records(conn: sqlite3.Connection) -> Iterator[list[Any]]:
        for row in conn.execute(sql):
            before = json.loads(row["state_before"]) if row["state_before"] else {}
            after = json.loads(row["state_after"]) if row["state_after"] else {}
            yield [
                row["id"],
                row["at"],
                from_ms(row["at"]).isoformat(timespec="milliseconds"),
                row["study_day"],
                row["attempt_id"],
                row["target_kind"],
                row["target_id"],
                row["target_ord"],
                row["rating"],
                row["rules_version"],
                row["params_id"],
                row["retention"],
                row["predicted_recall"],
                row["active_ms"],
                row["solve_ms"],
                before.get("fsrs_state"),
                before.get("stability"),
                before.get("difficulty"),
                before.get("due_at"),
                before.get("last_review_at"),
                after.get("fsrs_state"),
                after.get("stability"),
                after.get("difficulty"),
                after.get("due_at"),
                int(row["voided_by"] is not None),
            ]

    with db.reading() as conn:
        return _write_csv(dest, REVIEW_CSV_COLUMNS, records(conn))


def export_attempts_csv(db: Database, dest: Path, *, include_voided: bool = False) -> int:
    """Every attempt column except the undo snapshots, plus an ISO time. Returns rows."""
    with db.reading() as conn:
        columns = [
            str(r["name"])
            for r in conn.execute("PRAGMA table_info(attempt)")
            if r["name"] not in ("state_before", "state_after")
        ]
        where = "" if include_voided else " WHERE voided_by IS NULL"
        sql = f"SELECT {', '.join(columns)} FROM attempt{where} ORDER BY id"

        def records() -> Iterator[list[Any]]:
            for row in conn.execute(sql):
                values = list(row)
                at = values[columns.index("at")]
                yield [*values[:2], from_ms(at).isoformat(timespec="milliseconds"), *values[2:]]

        header = (*columns[:2], "at_utc", *columns[2:])
        return _write_csv(dest, header, records())
