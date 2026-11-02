"""Schema versions and forward-only migrations (DATA-3).

user.db carries its version in PRAGMA user_version and the id 'MEUS' in application_id;
packs carry 'MEPK'. Each migration runs in its own transaction with foreign keys
checked before commit, after the caller's backup hook has run. A database newer than
this app is refused, never modified. SQL files are frozen once released: a change is
a new migration plus new files, so the v1 files keep describing v1 forever.

v2 (ADR-0011) gives four v1 stop-gaps real homes: template instance parameters (card.params,
packs too), own template sources (user_template), own media (user_media + media/), check
reasons (pending_check.reason). Packs are never migrated: the app reads v1, v2 and v3 packs.

Pack schema v3 adds pack-only tables for the student model (pack_v3.sql): `time:` standard
times (card_time) and the pace standard (pace, pace_section). The content tables are
unchanged (content v2), so user.db stays at v2 and keeps exactly the shape of a pack's.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import json
import sqlite3
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from importlib import resources
from typing import Any

from core.storage.errors import MigrationError, NotOurDatabaseError, SchemaTooNewError

USER_SCHEMA_VERSION = 2
PACK_SCHEMA_VERSION = 3
CONTENT_SCHEMA_VERSION = 2  # the content tables (content_v2.sql) of packs and user.db
MODEL_TABLES_SINCE = 3  # packs from v3 on have card_time, pace and pace_section
USER_APP_ID = 0x4D455553  # "MEUS"
PACK_APP_ID = 0x4D45504B  # "MEPK"
USER_CONTENT_PREFIX = "user_"

type BeforeStep = Callable[[int, int], object]


def sql_file(name: str) -> str:
    return resources.files("core.storage").joinpath("sql", name).read_text(encoding="utf-8")


def content_sql(version: int, prefix: str) -> str:
    return sql_file(f"content_v{version}.sql").replace("{p}", prefix)


def statements(script: str) -> Iterator[str]:
    """Split a script into complete statements (triggers keep their inner semicolons)."""
    buffer: list[str] = []
    for line in script.splitlines(keepends=True):
        if not buffer and (not line.strip() or line.lstrip().startswith("--")):
            continue
        buffer.append(line)
        text = "".join(buffer)
        if sqlite3.complete_statement(text):
            yield text.strip()
            buffer = []
    if "".join(buffer).strip():
        raise ValueError(f"incomplete SQL statement: {''.join(buffer)[:80]!r}")


def run_script(conn: sqlite3.Connection, script: str) -> None:
    """Execute statement by statement inside the caller's transaction (no executescript,
    which would commit on its own under legacy transaction control)."""
    for statement in statements(script):
        conn.execute(statement)


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


def _v1_baseline(conn: sqlite3.Connection) -> None:
    run_script(conn, sql_file("user_v1.sql"))
    run_script(conn, content_sql(1, USER_CONTENT_PREFIX))
    conn.execute(f"PRAGMA application_id = {USER_APP_ID}")


# ---------------------------------------------------------------- v2 (ADR-0011)

V1_PARAMS_PREFIX = "template parameters: "  # how v1 wrote an instance's parameters
V1_IMPORT_KIND = "cards"  # the import records whose summary kept template sources


def split_v1_notes(template_id: str | None, notes_md: str | None) -> tuple[str | None, str | None]:
    """(params, notes) of a card stored by v1, which kept a template instance's parameter
    set as the first line of notes_md: "template parameters: k = 3", then a blank line and
    the template's own notes, if any. Anything else is not that stop-gap and is returned
    as it is, (None, notes_md): only text v1 itself wrote is ever moved."""
    if template_id is None or notes_md is None or not notes_md.startswith(V1_PARAMS_PREFIX):
        return None, notes_md
    first, newline, rest = notes_md.partition("\n")
    params = first.removeprefix(V1_PARAMS_PREFIX)
    if not newline:
        return params, None
    if rest.startswith("\n") and rest[1:]:
        return params, rest[1:]
    return None, notes_md


def v1_template_sources(kind: str, summary: Any) -> dict[str, str]:
    """The template sources one v1 import record kept: for a card import, its
    summary["files"][file]["templates"] maps template ID -> source text."""
    out: dict[str, str] = {}
    files = summary.get("files") if kind == V1_IMPORT_KIND and isinstance(summary, dict) else None
    for info in files.values() if isinstance(files, dict) else ():
        templates = info.get("templates") if isinstance(info, dict) else None
        for tid, source in templates.items() if isinstance(templates, dict) else ():
            if isinstance(tid, str) and isinstance(source, str) and source:
                out[tid] = source
    return out


def v1_check_reason(extra: Any, skill_id: str, kind: str) -> str | None:
    """The reason v1 kept for a check in its attempt's extra["diagnosis"]["checks"]: the
    first entry for the same skill and kind (as core.engine.diagnosis read it)."""
    diagnosis = extra.get("diagnosis") if isinstance(extra, dict) else None
    entries = diagnosis.get("checks") if isinstance(diagnosis, dict) else None
    for item in entries if isinstance(entries, list) else ():
        if isinstance(item, dict) and item.get("skill") == skill_id and item.get("kind") == kind:
            reason = item.get("reason")
            return reason if isinstance(reason, str) else None
    return None


def _v2_homes(conn: sqlite3.Connection) -> None:
    """New columns and tables, then the v1 data moved into them. One transaction (with the
    version bump), so a crash leaves v1 untouched and the step simply runs again.

    The attempt log and the import log are append-only (DATA-5), so the reasons and
    template sources they hold are copied, not cut: they stay there as history, and the
    new homes are what the app reads from now on."""
    run_script(conn, sql_file("migrate_user_v2.sql"))
    p = USER_CONTENT_PREFIX
    instances = conn.execute(
        f"SELECT id, template_id, notes_md FROM {p}card "
        "WHERE template_id IS NOT NULL AND notes_md IS NOT NULL AND params IS NULL ORDER BY id"
    ).fetchall()
    for card_id, template_id, notes_md in instances:
        params, notes = split_v1_notes(template_id, notes_md)
        if params is not None:
            conn.execute(
                f"UPDATE {p}card SET params = ?, notes_md = ? WHERE id = ?",
                (params, notes, card_id),
            )
    latest: dict[str, tuple[str, int]] = {}  # template ID -> (source, import time)
    for kind, summary, at in conn.execute(
        "SELECT kind, summary, at FROM import_record ORDER BY at, id"
    ).fetchall():
        for tid, source in v1_template_sources(kind, json.loads(summary)).items():
            latest[tid] = (source, at)
    for tid, (source, at) in sorted(latest.items()):
        conn.execute(
            f"INSERT INTO {p}template (id, source_md, updated_at) VALUES (?, ?, ?)",
            (tid, source, at),
        )
    checks = conn.execute(
        "SELECT c.id, c.skill_id, c.kind, a.extra FROM pending_check c "
        "JOIN attempt a ON a.id = c.attempt_id WHERE c.reason IS NULL ORDER BY c.id"
    ).fetchall()
    for check_id, skill_id, kind, extra in checks:
        reason = v1_check_reason(json.loads(extra), skill_id, kind)
        if reason is not None:
            conn.execute("UPDATE pending_check SET reason = ? WHERE id = ?", (reason, check_id))


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "baseline", _v1_baseline),
    Migration(2, "homes for template parameters and sources, own media, check reasons", _v2_homes),
)


def user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def application_id(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA application_id").fetchone()[0])


def _is_empty(conn: sqlite3.Connection) -> bool:
    return bool(conn.execute("SELECT count(*) FROM sqlite_schema").fetchone()[0] == 0)


def check_user_db(conn: sqlite3.Connection, *, target: int = USER_SCHEMA_VERSION) -> int:
    """Raise unless this is an empty file or one of our user.dbs at or below target."""
    version = user_version(conn)
    if version == 0:
        if not _is_empty(conn):
            raise NotOurDatabaseError("not a Toishi user.db (unversioned, not empty)")
        return 0
    if application_id(conn) != USER_APP_ID:
        raise NotOurDatabaseError("not a Toishi user.db (application_id)")
    if version > target:
        raise SchemaTooNewError(
            f"user.db is schema v{version}; this app understands up to v{target}. "
            "Update the app; the file was left untouched."
        )
    return version


def migrate(
    conn: sqlite3.Connection,
    *,
    target: int = USER_SCHEMA_VERSION,
    migrations: Sequence[Migration] = MIGRATIONS,
    before_step: BeforeStep | None = None,
) -> list[int]:
    """Bring the database forward to `target`; return the versions applied.

    `conn` must be in autocommit mode. `before_step(from, to)` runs before each step on a
    database that existed before this call (the backup hook); an exception there stops
    the migration. A new database has nothing to back up, even past its baseline.
    """
    versions = [m.version for m in migrations]
    if versions != list(range(1, len(versions) + 1)):
        raise ValueError(f"migrations must be numbered 1..n in order, got {versions}")
    if target > len(migrations):
        raise ValueError(f"no migration reaches v{target}")
    current = check_user_db(conn, target=target)
    existed = current > 0
    applied: list[int] = []
    for step in migrations[current:target]:
        if existed and before_step is not None:
            before_step(current, step.version)
        conn.execute("PRAGMA foreign_keys = OFF")  # table rebuilds; checked below instead
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                step.apply(conn)
                problems = conn.execute("PRAGMA foreign_key_check").fetchall()
                if problems:
                    raise MigrationError(f"v{step.version} broke foreign keys: {problems[:5]}")
                conn.execute(f"PRAGMA user_version = {step.version}")
                conn.execute("COMMIT")
            except BaseException as error:
                conn.execute("ROLLBACK")
                if isinstance(error, MigrationError):
                    raise
                if isinstance(error, Exception):
                    raise MigrationError(
                        f"migration to v{step.version} ({step.name}) failed and was rolled "
                        f"back: {error}"
                    ) from error
                raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
        current = step.version
        applied.append(step.version)
    return applied


def schema_signature(conn: sqlite3.Connection, schema: str = "main") -> list[tuple[str, str]]:
    """(name, normalized sql) of every table, index and trigger, for drift tests."""
    rows = conn.execute(
        f"SELECT name, sql FROM {schema}.sqlite_schema "
        "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [(str(name), " ".join(str(sql).split())) for name, sql in rows]
