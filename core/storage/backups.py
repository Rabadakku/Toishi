"""Backups of a profile's user.db (BAK-1..6).

- Copies use SQLite's online backup API, so they are consistent while the app runs, and
  are saved as standalone rollback-journal files (no -wal to lose), checked, fsynced and
  moved into place atomically: a crash never leaves a half-written backup behind.
- Policy: one every 30 minutes of use and one on close; keep the last 10 of those plus
  the newest of each of the last 7 study days, 4 ISO weeks and 6 months. Extra backups
  before migrations, imports, pack updates and restores keep their own last 10.
- Restore takes a pre-restore backup, keeps the replaced files, and swaps the database
  in with a rename; Database.open finishes a swap a crash interrupted.
- An integrity check on open (Database.open) points at the newest good backup.
- cloud_sync_warning flags data folders where SQLite is unsafe (BAK-5).
"""

import re
import sqlite3
import subprocess
import threading
from collections.abc import Callable, Hashable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, tzinfo
from pathlib import Path
from typing import Any, Literal

from core.storage import schema
from core.storage.clock import DEFAULT_ROLLOVER_HOUR, Clock, from_ms, study_day, to_ms
from core.storage.connection import (
    RESTORE_SUFFIX,
    SIDE_SUFFIXES,
    connect,
    fsync_path,
    integrity_problems,
    profile_lock,
)
from core.storage.errors import BackupError
from core.storage.user_store import count_rows

BackupReason = Literal[
    "periodic", "close", "manual", "pre-migration", "pre-import", "pre-pack-update", "pre-restore"
]
REGULAR_REASONS = frozenset({"periodic", "close", "manual"})
_NAME = re.compile(r"user-(\d{8}T\d{6})(\d{3})Z-([a-z-]+?)(?:~(\d+))?\.db")


@dataclass(frozen=True, slots=True, order=True)
class BackupInfo:
    created_at: int
    serial: int
    path: Path = field(compare=False)
    reason: str = field(compare=False)

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def regular(self) -> bool:
        return self.reason in REGULAR_REASONS


@dataclass(frozen=True, slots=True)
class BackupPolicy:
    interval_ms: int = 30 * 60_000
    keep_last: int = 10
    keep_daily: int = 7
    keep_weekly: int = 4
    keep_monthly: int = 6
    keep_extra: int = 10

    @classmethod
    def from_settings(cls, values: dict[str, Any]) -> BackupPolicy:
        return cls(
            interval_ms=int(values["backup.interval_minutes"]) * 60_000,
            keep_last=int(values["backup.keep_last"]),
            keep_daily=int(values["backup.keep_daily"]),
            keep_weekly=int(values["backup.keep_weekly"]),
            keep_monthly=int(values["backup.keep_monthly"]),
        )


@dataclass(frozen=True, slots=True)
class BackupPreview:
    """What BAK-3 shows before a restore: date, counts and whether the copy is sound."""

    backup: BackupInfo
    ok: bool
    problems: list[str]
    schema_version: int | None
    counts: dict[str, int | None]


def backup_database(source: Path, dest: Path) -> None:
    """Copy a live (WAL) database to dest with the online backup API, atomically."""
    if not source.is_file():
        raise BackupError(f"nothing to back up at {source}")
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.unlink(missing_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        src = connect(source, mode="rw")
        try:
            src.execute("PRAGMA query_only = ON")
            dst = sqlite3.connect(tmp, autocommit=True)
            try:
                src.backup(dst)
                dst.execute("PRAGMA journal_mode = DELETE")
                check = [str(r[0]) for r in dst.execute("PRAGMA quick_check")]
            finally:
                dst.close()
        finally:
            src.close()
        if check != ["ok"]:
            raise BackupError(f"backup copy failed its check: {check[:5]}")
        fsync_path(tmp)
        tmp.replace(dest)
        fsync_path(dest.parent)
    except (sqlite3.Error, OSError) as error:  # disk full, a vanished file: still a BackupError
        raise BackupError(f"backup of {source} failed: {error}") from error
    finally:
        tmp.unlink(missing_ok=True)


def parse_backup_name(path: Path) -> BackupInfo | None:
    match = _NAME.fullmatch(path.name)
    if match is None:
        return None
    stamp, millis, reason, serial = match.groups()
    created = datetime.strptime(stamp, "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
    return BackupInfo(to_ms(created) + int(millis), int(serial or 0), path, reason)


def utc_stamp(at_ms: int) -> str:
    """20261101T164154123Z: sortable, file-name safe."""
    return from_ms(at_ms).strftime("%Y%m%dT%H%M%S") + f"{at_ms % 1000:03d}Z"


def backup_name(created_at: int, reason: str, serial: int = 0) -> str:
    return f"user-{utc_stamp(created_at)}-{reason}" + (f"~{serial}" if serial else "") + ".db"


def select_keep(
    backups: Sequence[BackupInfo],
    policy: BackupPolicy,
    tz: tzinfo,
    rollover_hour: int = DEFAULT_ROLLOVER_HOUR,
) -> set[Path]:
    """The backups the retention policy keeps (BAK-1). Pure, for testing."""
    newest = sorted(backups, reverse=True)
    keep: set[Path] = set()
    if newest:
        keep.add(newest[0].path)
    keep.update(b.path for b in [b for b in newest if b.regular][: policy.keep_last])
    keep.update(b.path for b in [b for b in newest if not b.regular][: policy.keep_extra])

    def day_of(b: BackupInfo) -> date:
        return study_day(b.created_at, tz, rollover_hour)

    buckets: list[tuple[int, Callable[[BackupInfo], Hashable]]] = [
        (policy.keep_daily, day_of),
        (policy.keep_weekly, lambda b: day_of(b).isocalendar()[:2]),
        (policy.keep_monthly, lambda b: (day_of(b).year, day_of(b).month)),
    ]
    for count, bucket in buckets:
        seen: set[Hashable] = set()
        for b in newest:
            key = bucket(b)
            if key not in seen and len(seen) < count:
                seen.add(key)
                keep.add(b.path)
    return keep


class BackupManager:
    def __init__(
        self,
        db_path: Path,
        backups_dir: Path,
        *,
        clock: Clock,
        policy: BackupPolicy | None = None,
        tz: tzinfo | None = None,
        rollover_hour: int = DEFAULT_ROLLOVER_HOUR,
    ) -> None:
        self.db_path = db_path
        self.dir = backups_dir
        self.clock = clock
        self.policy = policy or BackupPolicy()
        self.tz = tz or clock.tz
        self.rollover_hour = rollover_hour
        self._use_ms = 0
        # Backups come from several threads (the 30-minute one, manual, on close): one at
        # a time, or a prune deletes another's .tmp copy mid-write and names collide.
        self._lock = threading.RLock()

    def all(self) -> list[BackupInfo]:
        """Every backup, newest first."""
        if not self.dir.is_dir():
            return []
        found = (parse_backup_name(p) for p in self.dir.iterdir() if p.is_file())
        return sorted((b for b in found if b is not None), reverse=True)

    def create(self, reason: BackupReason, *, prune: bool = True) -> BackupInfo:
        with self._lock:
            return self._create(reason, prune=prune)

    def _create(self, reason: BackupReason, *, prune: bool) -> BackupInfo:
        now = self.clock.now_ms()
        serial = 0
        while (self.dir / backup_name(now, reason, serial)).exists():
            serial += 1
        dest = self.dir / backup_name(now, reason, serial)
        backup_database(self.db_path, dest)
        info = parse_backup_name(dest)
        if info is None:
            raise BackupError(f"unexpected backup name {dest.name}")
        if prune:
            self.prune()
        return info

    def add_use(self, ms: int) -> BackupInfo | None:
        """Count active use; back up once every policy.interval_ms of it (BAK-1)."""
        with self._lock:
            self._use_ms += max(0, ms)
            if self._use_ms < self.policy.interval_ms:
                return None
            self._use_ms = 0
            return self.create("periodic")

    def on_close(self) -> BackupInfo:
        with self._lock:
            self._use_ms = 0
            return self.create("close")

    def prune(self) -> list[BackupInfo]:
        with self._lock:
            for stale in self.dir.glob("user-*.db.tmp"):  # left by a crash mid-backup
                stale.unlink(missing_ok=True)
            backups = self.all()
            keep = select_keep(backups, self.policy, self.tz, self.rollover_hour)
            removed = [b for b in backups if b.path not in keep]
            for b in removed:
                b.path.unlink(missing_ok=True)
            return removed

    def preview(self, backup: BackupInfo) -> BackupPreview:
        problems = integrity_problems(backup.path)
        version: int | None = None
        counts: dict[str, int | None] = {}
        try:
            conn = connect(backup.path, mode="ro")
            try:
                version = schema.user_version(conn)
                if schema.application_id(conn) != schema.USER_APP_ID:
                    problems.append("not a Toishi user.db")
                elif version > schema.USER_SCHEMA_VERSION:
                    problems.append(f"written by a newer app (schema v{version})")
                else:
                    counts = count_rows(conn)
            finally:
                conn.close()
        except sqlite3.Error as error:
            problems.append(f"{type(error).__name__}: {error}")
        return BackupPreview(backup, not problems, problems, version, counts)

    def newest_good(self) -> BackupInfo | None:
        for backup in self.all():
            if self.preview(backup).ok:
                return backup
        return None

    def restore(self, backup: BackupInfo) -> Path:
        """Replace user.db with a backup (the profile must be closed). Returns the folder
        that keeps the replaced files; a pre-restore backup is taken when possible.

        Nothing is pruned here: after a failed integrity check (BAK-4) this manager cannot
        know the student's retention settings. The next backup of the reopened profile
        prunes under its own policy."""
        preview = self.preview(backup)
        if not preview.ok:
            raise BackupError(f"backup {backup.path.name} is not usable: {preview.problems}")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, profile_lock(self.db_path):
            incoming = self.db_path.with_name(self.db_path.name + RESTORE_SUFFIX)
            backup_database(backup.path, incoming)  # first, so no pruning can remove it
            if self.db_path.exists() and not integrity_problems(self.db_path):
                self.create("pre-restore", prune=False)
            kept = self.dir / f"replaced-{utc_stamp(self.clock.now_ms())}"
            serial = 1
            while kept.exists():
                serial += 1
                kept = kept.with_name(f"replaced-{utc_stamp(self.clock.now_ms())}~{serial}")
            kept.mkdir(parents=True)
            for suffix in ("", *SIDE_SUFFIXES):  # user.db first: see recover_interrupted_restore
                old = self.db_path.with_name(self.db_path.name + suffix)
                if old.exists():
                    old.replace(kept / old.name)  # a stale -wal must never meet the new file
            fsync_path(kept)
            incoming.replace(self.db_path)
            fsync_path(self.db_path.parent)
        return kept


# ---------------------------------------------------------------- unsafe folders (BAK-5)

NETWORK_FS = frozenset(
    {"nfs", "nfs4", "smbfs", "cifs", "smb3", "afpfs", "webdav", "davfs", "fuse.sshfs", "sshfs"}
    | {"9p", "ftp", "fuse.rclone", "osxfuse", "macfuse"}
)


def read_mounts() -> list[tuple[str, str]]:
    """(mount point, file system type) pairs of this machine."""
    proc = Path("/proc/self/mounts")
    if proc.exists():
        out = []
        for line in proc.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3:
                out.append((parts[1].replace("\\040", " "), parts[2]))
        return out
    try:
        text = subprocess.run(
            ["/sbin/mount"], capture_output=True, text=True, timeout=5, check=False
        ).stdout
    except OSError, subprocess.SubprocessError:
        return []
    pattern = re.compile(r"^.* on (.+) \(([^,)]+)")
    return [(m.group(1), m.group(2)) for m in map(pattern.match, text.splitlines()) if m]


def cloud_sync_warning(
    path: Path, *, home: Path | None = None, mounts: Iterable[tuple[str, str]] | None = None
) -> str | None:
    """A warning when the data folder sits where SQLite is unsafe, else None."""
    home = home or Path.home()
    path = path.absolute()
    inside: list[tuple[Path, str]] = [
        (home / "Library" / "Mobile Documents", "iCloud Drive"),
        (home / "Library" / "CloudStorage", "a cloud storage folder"),
    ]
    for parent, label in inside:
        if path == parent or parent in path.parents:
            return _warn(path, label)
    for part in path.parts:
        lowered = part.lower()
        if lowered == "dropbox" or lowered.startswith("dropbox ("):
            return _warn(path, "Dropbox")
        if lowered.startswith("onedrive"):
            return _warn(path, "OneDrive")
        if lowered in ("icloud drive", "icloud~com~apple~clouddocs"):
            return _warn(path, "iCloud Drive")
    best: tuple[int, str] | None = None
    for mount_point, fs_type in mounts if mounts is not None else read_mounts():
        point = Path(mount_point)
        if (path == point or point in path.parents) and (
            best is None or len(point.parts) > best[0]
        ):
            best = (len(point.parts), fs_type)
    if best is not None and best[1].lower() in NETWORK_FS:
        return _warn(path, f"a network drive ({best[1]})")
    return None


def _warn(path: Path, where: str) -> str:
    return (
        f"The data folder {path} is inside {where}. Syncing or network file systems can "
        "corrupt SQLite databases; move it to a local folder in Settings."
    )
