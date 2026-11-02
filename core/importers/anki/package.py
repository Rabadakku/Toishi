""".apkg and .colpkg packages (IMP-2): zip archives sharing one layout across Anki versions.

- `meta` (protobuf) names the format: 1/2 legacy, 3 latest; 0 or anything newer is "made by
  a newer Anki". Without `meta`: `collection.anki21` if present, else `collection.anki2`.
- The latest format zstd-compresses the collection, the media map (protobuf MediaEntries)
  and every media file. Anki writes streaming frames without a content size, so everything
  is decompressed as a stream, with a cap.
- Modern Anki always adds a placeholder `collection.anki2` ("Please update to the latest
  Anki version"); it is never read when a newer collection file exists, and a package that
  holds only the placeholder is refused.
- Media map names must be one plain path component (Anki's rule; a package breaking it is
  corrupt). Legacy names are normalized; latest-format names must be normalized already
  and carry a 20-byte SHA-1, which is checked when the file is read.

Untrusted input: entry counts, sizes and compression ratios are capped (zip bombs), the
SQLite file is opened in memory, read-only, with the defensive flag on, and nothing in the
archive is ever used as a path.
"""

import hashlib
import io
import json
import sqlite3
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import zstandard

from core.importers.anki import protobuf as pb
from core.importers.anki.collection import read_collection
from core.importers.anki.errors import AnkiImportError
from core.importers.anki.media import filename_is_safe, normalize_filename
from core.importers.anki.model import AnkiData, AnkiFormat

COLLECTION_FILES = {1: "collection.anki2", 2: "collection.anki21", 3: "collection.anki21b"}
PLACEHOLDER_TEXT = "Please update to the latest Anki version"
_SQLITE_MAGIC = b"SQLite format 3\x00"
_CHUNK = 1 << 16


@dataclass(frozen=True, slots=True)
class Limits:
    max_entries: int = 200_000
    max_collection_bytes: int = 2 << 30
    max_media_bytes: int = 512 << 20  # one media file
    max_total_bytes: int = 8 << 30  # everything read from one package
    max_ratio: int = 1_000  # uncompressed / compressed, for entries over 1 MiB
    max_meta_bytes: int = 4_096


DEFAULT_LIMITS = Limits()


class _Budget:
    def __init__(self, limits: Limits) -> None:
        self.limits = limits
        self.used = 0

    def take(self, size: int) -> None:
        self.used += size
        if self.used > self.limits.max_total_bytes:
            raise AnkiImportError("the package expands to more data than an import allows")


class _Readable(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


def _read_capped(stream: _Readable, cap: int, what: str) -> bytes:
    out = bytearray()
    while True:
        chunk = stream.read(_CHUNK)
        if not chunk:
            return bytes(out)
        out += chunk
        if len(out) > cap:
            raise AnkiImportError(f"{what} is larger than an import allows")


class PackageMedia:
    """The media files of an open package, by normalized name, read on demand."""

    def __init__(
        self,
        archive: zipfile.ZipFile,
        entries: dict[str, tuple[str, bytes | None]],
        compressed: bool,
        budget: _Budget,
    ) -> None:
        self._archive = archive
        self._entries = entries  # name -> (zip member, sha1 or None)
        self._compressed = compressed
        self._budget = budget
        self._cache: dict[str, bytes] = {}

    def names(self) -> frozenset[str]:
        return frozenset(self._entries)

    def read(self, name: str) -> bytes:
        if name in self._cache:
            return self._cache[name]
        member, sha1 = self._entries[name]
        data = _member(
            self._archive,
            member,
            self._budget,
            self._budget.limits.max_media_bytes,
            f"media file {name!r}",
            zstd=self._compressed,
        )
        if sha1 is not None and hashlib.sha1(data, usedforsecurity=False).digest() != sha1:
            raise AnkiImportError(f"media file {name!r} does not match its checksum")
        self._cache[name] = data
        return data


def _member(
    archive: zipfile.ZipFile, name: str, budget: _Budget, cap: int, what: str, *, zstd: bool
) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError:
        raise AnkiImportError(f"{what} is missing from the package") from None
    limits = budget.limits
    if info.file_size > cap:
        raise AnkiImportError(f"{what} is larger than an import allows")
    if info.file_size > 1 << 20 and info.file_size > limits.max_ratio * max(info.compress_size, 1):
        raise AnkiImportError(f"{what} is compressed suspiciously well (a zip bomb?)")
    try:
        with archive.open(info) as handle:
            if not zstd:
                data = _read_capped(handle, cap, what)
            else:
                reader = zstandard.ZstdDecompressor().stream_reader(handle, read_across_frames=True)
                data = _read_capped(reader, cap, what)
    except (zipfile.BadZipFile, zstandard.ZstdError, OSError, EOFError) as exc:
        raise AnkiImportError(f"{what} can't be read: {exc}") from None
    budget.take(len(data))
    return data


def _open_archive(source: bytes | Path) -> zipfile.ZipFile:
    try:
        if isinstance(source, Path):
            return zipfile.ZipFile(source)
        return zipfile.ZipFile(io.BytesIO(source))
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise AnkiImportError(f"not an Anki package (not a zip archive): {exc}") from None


def _version(archive: zipfile.ZipFile, names: set[str], budget: _Budget) -> int:
    if "meta" not in names:
        return 2 if COLLECTION_FILES[2] in names else 1
    data = _member(archive, "meta", budget, budget.limits.max_meta_bytes, "meta", zstd=False)
    try:
        version = pb.integer(pb.decode(data), 1)
    except pb.ProtoError as exc:
        raise AnkiImportError(f"the package's meta file is damaged: {exc}") from None
    if version not in COLLECTION_FILES:
        raise AnkiImportError(
            "this package was made by a newer version of Anki; export it again with "
            '"Support older Anki versions" checked'
        )
    return version


def _collection_name(version: int, names: set[str]) -> str:
    name = COLLECTION_FILES[version]
    if name == COLLECTION_FILES[1]:
        newer = [COLLECTION_FILES[v] for v in (2, 3) if COLLECTION_FILES[v] in names]
        if newer:  # never the placeholder when a real collection is there
            if COLLECTION_FILES[2] not in names:
                raise AnkiImportError("the package's meta file does not match its collection")
            name = COLLECTION_FILES[2]
    if name not in names:
        raise AnkiImportError(f"the package has no {name}")
    return name


def open_sqlite(data: bytes) -> sqlite3.Connection:
    """An untrusted collection file as a read-only in-memory database."""
    if not data.startswith(_SQLITE_MAGIC):
        raise AnkiImportError("the collection inside the package is not a SQLite database")
    if len(data) > 19 and data[18:20] == b"\x02\x02":  # WAL mode: memory databases can't
        data = data[:18] + b"\x01\x01" + data[20:]
    conn = sqlite3.connect(":memory:")
    try:
        conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        conn.deserialize(data)
        conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        conn.execute("PRAGMA trusted_schema = OFF")
        conn.execute("PRAGMA query_only = ON")
        conn.create_collation("unicase", _unicase)
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except sqlite3.Error as exc:
        conn.close()
        raise AnkiImportError(f"the collection inside the package is damaged: {exc}") from None
    return conn


def _unicase(a: str, b: str) -> int:
    x, y = a.casefold(), b.casefold()
    return (x > y) - (x < y)


def _media_entries(
    archive: zipfile.ZipFile, names: set[str], version: int, budget: _Budget
) -> dict[str, tuple[str, bytes | None]]:
    if "media" not in names:
        return {}  # older AnkiDroid versions wrote no media map
    latest = version == 3
    data = _member(archive, "media", budget, 256 << 20, "the media list", zstd=latest)
    out: dict[str, tuple[str, bytes | None]] = {}
    if not latest:
        try:
            mapping = json.loads(data or b"{}")
        except (ValueError, UnicodeDecodeError) as exc:
            raise AnkiImportError(f"the media list is damaged: {exc}") from None
        if not isinstance(mapping, dict):
            raise AnkiImportError("the media list is damaged")
        for member, name in mapping.items():
            if not (isinstance(name, str) and member.isascii() and member.isdigit()):
                raise AnkiImportError(f"the media list is damaged near {member!r}")
            if not filename_is_safe(name):
                raise AnkiImportError(f"the media list has an unsafe file name: {name!r}")
            out[normalize_filename(name)] = (member, None)
        return out
    try:
        entries = pb.messages(pb.decode(data), 1)
        for index, entry in enumerate(entries):
            name, sha1 = pb.text(entry, 1), pb.raw(entry, 3)
            if not filename_is_safe(name) or normalize_filename(name) != name:
                raise AnkiImportError(f"the media list has an unsafe file name: {name!r}")
            if sha1 is None or len(sha1) != 20:
                raise AnkiImportError(f"the media list has no checksum for {name!r}")
            out[name] = (str(index), sha1)
    except pb.ProtoError as exc:
        raise AnkiImportError(f"the media list is damaged: {exc}") from None
    return out


def read_package(
    source: bytes | Path,
    *,
    name: str | None = None,
    format: AnkiFormat | None = None,
    limits: Limits = DEFAULT_LIMITS,
) -> AnkiData:
    """Read an .apkg or .colpkg (bytes or a path). Raises AnkiImportError for anything that
    can't be imported (the whole file is rejected)."""
    display = name or (source.name if isinstance(source, Path) else "deck.apkg")
    if format is None:
        format = "colpkg" if display.lower().endswith(".colpkg") else "apkg"
    budget = _Budget(limits)
    archive = _open_archive(source)
    infos = archive.infolist()
    if len(infos) > limits.max_entries:
        raise AnkiImportError("the package has more files than an import allows")
    names = {info.filename for info in infos}
    if len(names) != len(infos):
        raise AnkiImportError("the package lists a file twice (damaged or tampered with)")
    version = _version(archive, names, budget)
    member = _collection_name(version, names)
    db = _member(
        archive, member, budget, limits.max_collection_bytes, "the collection", zstd=version == 3
    )
    conn = open_sqlite(db)
    del db
    try:
        data = read_collection(conn, name=display, format=format)
    finally:
        conn.close()
    if _only_placeholder(data):
        raise AnkiImportError(
            "this package holds only Anki's placeholder note; export it again from Anki"
        )
    data.package_version = version
    data.media = PackageMedia(
        archive, _media_entries(archive, names, version, budget), version == 3, budget
    )
    return data


def _only_placeholder(data: AnkiData) -> bool:
    return len(data.notes) == 1 and any(PLACEHOLDER_TEXT in f for f in data.notes[0].fields)
