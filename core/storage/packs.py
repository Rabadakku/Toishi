"""Pack files (DATA-1, PACK-1..6): built once, sealed, then only ever read.

The pack builder (content-tools) calls PackWriter: create a file from records, then
seal() it, which records a content hash, switches to a rollback journal, vacuums,
makes the file read-only and moves it into place atomically. At runtime packs are
opened with `mode=ro` (read_pack_info, open_pack) and ATTACHed to user.db readers.
The writer builds the current pack schema (v3); readers take v1, v2 and v3 packs, which
are never migrated (ADR-0011). v3 adds the pack-only tables card_time (`time:` standard
times) and pace / pace_section (the pace standard); older packs read as having none.
"""

# ruff: noqa: S608 -- table names come from our own constants; values are always bound parameters.

import os
import sqlite3
import time
import urllib.parse
from collections.abc import Iterable
from pathlib import Path
from types import TracebackType

from core.model import (
    Card,
    CardRevision,
    Course,
    Media,
    PackInfo,
    PackPace,
    PackPaceSection,
    Section,
    Skill,
    Unit,
)
from core.storage import content, schema
from core.storage.errors import NotOurDatabaseError, PackError

BUILDING_SUFFIX = ".building"

type PackRecord = Course | Unit | Section | Skill | Card | CardRevision | Media | PackPace


def has_model_tables(version: int) -> bool:
    """Packs of schema v3 and later have card_time, pace and pace_section."""
    return version >= schema.MODEL_TABLES_SINCE


def pack_tables(version: int) -> tuple[str, ...]:
    """The tables a pack's content hash covers, by its schema version."""
    tables: tuple[str, ...] = (*content.CONTENT_TABLES, "media")
    if has_model_tables(version):
        tables += ("card_time", "pace", "pace_section")
    return tables


PACK_TABLES = pack_tables(schema.PACK_SCHEMA_VERSION)


def read_pace(conn: sqlite3.Connection, alias: str, version: int) -> PackPace:
    """A pack's pace standard: the minutes per step and weekly hours of skills.md's header,
    and its ## Section blocks with their hours, in course order. Packs before v3, and packs
    whose skills.md sets none, have the defaults."""
    if not has_model_tables(version):
        return PackPace()
    row = conn.execute(f"SELECT minutes_per_step, weekly_hours FROM {alias}.pace").fetchone()
    sections = tuple(
        PackPaceSection(deck=r[0], hours=r[1])
        for r in conn.execute(f"SELECT section_id, hours FROM {alias}.pace_section ORDER BY ord")
    )
    if row is None:
        return PackPace(sections=sections)
    return PackPace(minutes_per_step=row[0], weekly_hours=row[1], sections=sections)


def _write_pace(conn: sqlite3.Connection, pace: PackPace) -> None:
    conn.execute(
        "INSERT INTO pace (singleton, minutes_per_step, weekly_hours) VALUES (1, ?, ?) "
        "ON CONFLICT (singleton) DO UPDATE SET minutes_per_step = excluded.minutes_per_step, "
        "weekly_hours = excluded.weekly_hours",
        (pace.minutes_per_step, pace.weekly_hours),
    )
    conn.execute("DELETE FROM pace_section")
    conn.executemany(
        "INSERT INTO pace_section (ord, section_id, hours) VALUES (?, ?, ?)",
        [(i, s.deck, s.hours) for i, s in enumerate(pace.sections)],
    )


def _ro_connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise PackError(f"no pack file at {path}")
    uri = "file:" + urllib.parse.quote(str(path.absolute())) + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, autocommit=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA trusted_schema = OFF")
    return conn


def _info(conn: sqlite3.Connection, path: Path) -> PackInfo:
    try:
        app_id = schema.application_id(conn)
        version = schema.user_version(conn)
    except sqlite3.DatabaseError as error:
        raise PackError(f"{path} is not a SQLite pack: {error}") from error
    if app_id != schema.PACK_APP_ID:
        raise NotOurDatabaseError(f"{path} is not a Toishi pack")
    if not 1 <= version <= schema.PACK_SCHEMA_VERSION:
        raise PackError(
            f"{path} is pack schema v{version}; this app reads up to v{schema.PACK_SCHEMA_VERSION}"
        )
    row = conn.execute("SELECT * FROM pack").fetchone()
    if row is None or not row["content_hash"]:
        raise PackError(f"{path} was never sealed")
    return PackInfo(
        id=row["id"],
        title=row["title"],
        version=row["version"],
        format=row["format"],
        built_at=row["built_at"],
        content_hash=row["content_hash"],
        schema_version=version,
    )


def read_pack_info(path: Path) -> PackInfo:
    """Validate a sealed pack (read-only) and return its header."""
    try:
        conn = _ro_connect(path)
        try:
            return _info(conn, path)
        finally:
            conn.close()
    except sqlite3.Error as error:  # damaged or unreadable: still a PackError for callers
        raise PackError(f"{path} cannot be read as a pack: {error}") from error


class PackReader:
    """One pack file opened on its own, read-only: for inspection and verification."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn = _ro_connect(path)
        try:
            self.info = _info(self._conn, path)
        except BaseException:
            self._conn.close()
            raise
        version = self.info.schema_version
        self.content = content.ContentReader(
            self._conn, "main", "", self.info.id, version=version,
            card_times=has_model_tables(version),
        )  # fmt: skip

    def pace(self) -> PackPace:
        return read_pace(self._conn, "main", self.info.schema_version)

    def media(self, name: str) -> bytes | None:
        row = self._conn.execute("SELECT data FROM media WHERE name = ?", (name,)).fetchone()
        return None if row is None else bytes(row[0])

    def media_names(self) -> list[str]:
        return [str(r[0]) for r in self._conn.execute("SELECT name FROM media ORDER BY name")]

    def verify(self) -> bool:
        """True when the content still matches the hash recorded at sealing."""
        tables = pack_tables(self.info.schema_version)
        return content.content_hash(self._conn, tables) == self.info.content_hash

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> PackReader:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def open_pack(path: Path) -> PackReader:
    return PackReader(path)


class PackWriter:
    """Builds one pack file. Use as a context manager; leaving without seal() aborts."""

    def __init__(self, final: Path, building: Path, conn: sqlite3.Connection) -> None:
        self.final = final
        self.building = building
        self._conn: sqlite3.Connection | None = conn
        self.sealed: PackInfo | None = None

    @classmethod
    def create(cls, path: Path, info: PackInfo, *, overwrite: bool = False) -> PackWriter:
        path = path.absolute()
        if path.exists() and not overwrite:
            raise FileExistsError(f"{path} exists; packs are replaced only with overwrite=True")
        building = path.with_name(path.name + BUILDING_SUFFIX)
        building.unlink(missing_ok=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(building, autocommit=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = MEMORY")  # a scratch file until sealed
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        schema.run_script(conn, schema.sql_file(f"pack_v{schema.PACK_SCHEMA_VERSION}.sql"))
        schema.run_script(conn, schema.content_sql(schema.CONTENT_SCHEMA_VERSION, ""))
        conn.execute(f"PRAGMA application_id = {schema.PACK_APP_ID}")
        conn.execute(f"PRAGMA user_version = {schema.PACK_SCHEMA_VERSION}")
        conn.execute(
            "INSERT INTO pack (singleton, id, title, version, format, built_at) "
            "VALUES (1, ?, ?, ?, ?, ?)",
            (info.id, info.title, info.version, info.format, info.built_at or _now_ms()),
        )
        return cls(path, building, conn)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise PackError("this pack writer is closed")
        return self._conn

    def add(self, *records: PackRecord) -> None:
        self.add_all(records)

    def add_all(self, records: Iterable[PackRecord]) -> None:
        conn = self.conn
        for record in records:
            match record:
                case Course():
                    content.write_course(conn, "", record)
                case Unit():
                    content.write_unit(conn, "", record)
                case Section():
                    content.write_section(conn, "", record)
                case Skill():
                    content.write_skill(conn, "", record)
                case Card():
                    content.write_card(conn, "", record)
                    content.write_card_times(conn, record)
                case PackPace():
                    _write_pace(conn, record)
                case CardRevision():
                    content.write_revision(conn, "", record)
                case Media():
                    conn.execute(
                        "INSERT INTO media (name, data) VALUES (?, ?) "
                        "ON CONFLICT (name) DO UPDATE SET data = excluded.data",
                        (record.name, record.data),
                    )
                case _:
                    raise TypeError(f"cannot put {type(record).__name__} in a pack")

    def seal(self) -> PackInfo:
        """Validate, hash, compact, make read-only and move into place. Returns the header."""
        conn = self.conn
        problems = conn.execute("PRAGMA foreign_key_check").fetchall()
        if problems:
            raise PackError(f"pack rows point at missing rows: {[tuple(p) for p in problems[:5]]}")
        digest = content.content_hash(conn, PACK_TABLES)
        conn.execute("UPDATE pack SET content_hash = ?", (digest,))
        conn.execute("COMMIT")
        conn.execute("PRAGMA journal_mode = DELETE")
        conn.execute("VACUUM")
        check = [str(r[0]) for r in conn.execute("PRAGMA integrity_check")]
        if check != ["ok"]:
            raise PackError(f"sealed pack failed integrity_check: {check[:5]}")
        conn.close()
        self._conn = None
        _fsync(self.building)
        self.building.chmod(0o444)
        self.building.replace(self.final)
        _fsync(self.final.parent)
        self.sealed = read_pack_info(self.final)
        return self.sealed

    def abort(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        self.building.unlink(missing_ok=True)

    def __enter__(self) -> PackWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.sealed is None:
            self.abort()


def build_pack(path: Path, info: PackInfo, records: Iterable[PackRecord]) -> PackInfo:
    """Create, fill and seal a pack in one call."""
    with PackWriter.create(path, info) as writer:
        writer.add_all(records)
        return writer.seal()


def _fsync(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _now_ms() -> int:
    return time.time_ns() // 1_000_000
