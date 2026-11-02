"""Profiles (PRO-1, PRO-2): one folder per student, chosen at startup, no passwords.

Layout under the data folder (platformdirs; TOISHI_DATA_DIR overrides):

    profiles.db                    registry: id, display name, created, last opened
    profiles/<id>/user.db          progress, settings (WAL; -wal/-shm beside it)
    profiles/<id>/media/           the student's own media (media.py, content-addressed)
    profiles/<id>/backups/         backups (see backups.py)
    deleted-profiles/<id>-<time>/  deleted profiles are moved here, not erased

The folder id never changes, so renaming is a registry update. A folder with a user.db
but no registry row (say, after the registry was lost) is adopted under its id.
"""

import re
import sqlite3
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.paths import app_data_dir
from core.storage.backups import utc_stamp
from core.storage.clock import Clock, SystemClock
from core.storage.connection import Database, connect, fsync_path, profile_lock
from core.storage.errors import ProfileError
from core.storage.export import export_profile, import_profile, read_manifest
from core.storage.media import MEDIA_DIR

PROFILES_DIR = "profiles"
DELETED_DIR = "deleted-profiles"
REGISTRY = "profiles.db"
MAX_NAME = 80

_REGISTRY_SQL = """
CREATE TABLE IF NOT EXISTS profile (
  id             TEXT PRIMARY KEY NOT NULL,
  name           TEXT NOT NULL,
  name_key       TEXT NOT NULL UNIQUE,  -- casefolded name: names are unique ignoring case
  created_at     INTEGER NOT NULL,
  last_opened_at INTEGER
) STRICT
"""


@dataclass(frozen=True, slots=True)
class ProfilePaths:
    root: Path

    @property
    def user_db(self) -> Path:
        return self.root / "user.db"

    @property
    def media_dir(self) -> Path:
        return self.root / MEDIA_DIR

    @property
    def backups_dir(self) -> Path:
        return self.root / "backups"

    def ensure(self) -> None:
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ProfileInfo:
    id: str
    name: str
    created_at: int
    last_opened_at: int | None
    paths: ProfilePaths


def clean_name(name: str) -> str:
    name = unicodedata.normalize("NFC", " ".join(name.split()))
    if not name:
        raise ProfileError("a profile needs a name")
    if len(name) > MAX_NAME:
        raise ProfileError(f"profile names are at most {MAX_NAME} characters")
    if any(unicodedata.category(c).startswith("C") for c in name):
        raise ProfileError("profile names cannot contain control characters")
    return name


def name_key(name: str) -> str:
    return unicodedata.normalize("NFC", name.casefold())


def _slug(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:40]
    return slug or "profile"


class ProfileManager:
    def __init__(self, data_dir: Path | None = None, *, clock: Clock | None = None) -> None:
        self.data_dir = (data_dir or app_data_dir()).absolute()
        self.profiles_dir = self.data_dir / PROFILES_DIR
        self.deleted_dir = self.data_dir / DELETED_DIR
        self.clock = clock or SystemClock()

    # ------------------------------------------------------------ registry

    @contextmanager
    def _registry(self) -> Iterator[sqlite3.Connection]:
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / REGISTRY
        try:
            conn = self._open_registry(path)
        except sqlite3.DatabaseError:
            # Names only: set the damaged file aside and rebuild from the folders.
            path.replace(path.with_name(f"{REGISTRY}.damaged-{utc_stamp(self.clock.now_ms())}"))
            conn = self._open_registry(path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._adopt_orphans(conn)
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()

    @staticmethod
    def _open_registry(path: Path) -> sqlite3.Connection:
        conn = connect(path, mode="rwc")
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute(_REGISTRY_SQL)
        except BaseException:
            conn.close()
            raise
        return conn

    def _adopt_orphans(self, conn: sqlite3.Connection) -> None:
        known = {str(r[0]) for r in conn.execute("SELECT id FROM profile")}
        for folder in sorted(self.profiles_dir.iterdir()):
            if folder.name in known or folder.name.startswith("."):
                continue
            if (folder / "user.db").is_file():
                name = self._free_name(conn, folder.name)
                self._insert(conn, folder.name, name, int(folder.stat().st_mtime * 1000))

    @staticmethod
    def _taken(conn: sqlite3.Connection, name: str, other_than: str = "") -> bool:
        row = conn.execute(
            "SELECT 1 FROM profile WHERE name_key = ? AND id <> ?", (name_key(name), other_than)
        ).fetchone()
        return row is not None

    @classmethod
    def _free_name(cls, conn: sqlite3.Connection, wanted: str) -> str:
        name, n = wanted, 1
        while cls._taken(conn, name):
            n += 1
            name = f"{wanted} ({n})"
        return name

    @staticmethod
    def _insert(conn: sqlite3.Connection, profile_id: str, name: str, created_at: int) -> None:
        conn.execute(
            "INSERT INTO profile (id, name, name_key, created_at) VALUES (?, ?, ?, ?)",
            (profile_id, name, name_key(name), created_at),
        )

    def _info(self, row: Any) -> ProfileInfo:
        return ProfileInfo(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
            last_opened_at=row["last_opened_at"],
            paths=ProfilePaths(self.profiles_dir / row["id"]),
        )

    def _row(self, conn: sqlite3.Connection, profile_id: str) -> Any:
        row = conn.execute("SELECT * FROM profile WHERE id = ?", (profile_id,)).fetchone()
        if row is None or not (self.profiles_dir / profile_id).is_dir():
            raise ProfileError(f"no profile {profile_id!r}")
        return row

    # ------------------------------------------------------------ operations

    def list(self) -> list[ProfileInfo]:
        with self._registry() as conn:
            rows = conn.execute("SELECT * FROM profile ORDER BY name_key, id").fetchall()
        return [self._info(r) for r in rows if (self.profiles_dir / r["id"]).is_dir()]

    def get(self, profile_id: str) -> ProfileInfo:
        with self._registry() as conn:
            return self._info(self._row(conn, profile_id))

    def _new_id(self, name: str) -> str:
        base = _slug(name)
        candidate, n = base, 1
        while (self.profiles_dir / candidate).exists() or (self.deleted_dir / candidate).exists():
            n += 1
            candidate = f"{base}-{n}"
        return candidate

    def create(self, name: str) -> ProfileInfo:
        """Make the folder and an initialized user.db, then register it."""
        name = clean_name(name)
        with self._registry() as conn:
            if self._taken(conn, name):
                raise ProfileError(f"a profile named {name!r} exists")
            profile_id = self._new_id(name)
            paths = ProfilePaths(self.profiles_dir / profile_id)
            paths.ensure()
            Database.open(paths.user_db, clock=self.clock, create=True).close()
            self._insert(conn, profile_id, name, self.clock.now_ms())
            return self._info(self._row(conn, profile_id))

    def rename(self, profile_id: str, name: str) -> ProfileInfo:
        name = clean_name(name)
        with self._registry() as conn:
            self._row(conn, profile_id)
            if self._taken(conn, name, other_than=profile_id):
                raise ProfileError(f"a profile named {name!r} exists")
            conn.execute(
                "UPDATE profile SET name = ?, name_key = ? WHERE id = ?",
                (name, name_key(name), profile_id),
            )
            return self._info(self._row(conn, profile_id))

    def choose(self, profile_id: str) -> ProfileInfo:
        """Mark a profile as the one in use (it is offered first next time)."""
        with self._registry() as conn:
            self._row(conn, profile_id)
            conn.execute(
                "UPDATE profile SET last_opened_at = ? WHERE id = ?",
                (self.clock.now_ms(), profile_id),
            )
            return self._info(self._row(conn, profile_id))

    def last_chosen(self) -> ProfileInfo | None:
        chosen = [p for p in self.list() if p.last_opened_at is not None]
        return max(chosen, key=lambda p: p.last_opened_at or 0) if chosen else None

    def delete(self, profile_id: str, *, confirm: bool = False) -> Path:
        """Remove a profile from the list. Needs confirm=True; the folder (progress,
        media, backups) is moved to deleted-profiles/, never erased here."""
        if confirm is not True:
            raise ProfileError("deleting a profile needs confirm=True")
        with self._registry() as conn:
            self._row(conn, profile_id)
            source = self.profiles_dir / profile_id
            self.deleted_dir.mkdir(parents=True, exist_ok=True)
            dest = self.deleted_dir / f"{profile_id}-{utc_stamp(self.clock.now_ms())}"
            with profile_lock(source / "user.db"):  # refuses while it is open
                source.replace(dest)
            lock_file = dest / "user.db.lock"
            lock_file.unlink(missing_ok=True)
            fsync_path(self.profiles_dir)
            conn.execute("DELETE FROM profile WHERE id = ?", (profile_id,))
            return dest

    # ------------------------------------------------------------ .meprofile

    def export(self, profile_id: str, dest: Path) -> dict[str, Any]:
        info = self.get(profile_id)
        return export_profile(
            info.paths.user_db, info.paths.media_dir, dest, name=info.name, clock=self.clock
        )

    def import_profile(self, src: Path, name: str | None = None) -> ProfileInfo:
        """Add a .meprofile as a new profile; never overwrites an existing one."""
        manifest = read_manifest(src)
        wanted = clean_name(name or str(manifest.get("name") or "Imported"))
        with self._registry() as conn:
            final_name = self._free_name(conn, wanted)
            profile_id = self._new_id(final_name)
            import_profile(src, self.profiles_dir / profile_id)
            self._insert(conn, profile_id, final_name, self.clock.now_ms())
            return self._info(self._row(conn, profile_id))
