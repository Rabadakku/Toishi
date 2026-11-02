"""DATA-3: PRAGMA user_version, forward-only migrations, each preceded by a backup."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from core.storage import (
    Database,
    MigrationError,
    NotOurDatabaseError,
    SchemaTooNewError,
    Storage,
)
from core.storage.connection import integrity_problems
from core.storage.profiles import ProfilePaths
from core.storage.schema import (
    MIGRATIONS,
    USER_APP_ID,
    USER_SCHEMA_VERSION,
    Migration,
    migrate,
    schema_signature,
    statements,
    user_version,
)
from tests.storage import data
from tests.storage.data import some

FIXTURE = Path(__file__).parent / "fixtures" / "user_v1.sql"


def load_v1_fixture(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(FIXTURE.read_text())
    conn.execute("PRAGMA user_version = 1")
    conn.execute(f"PRAGMA application_id = {USER_APP_ID}")
    conn.commit()
    conn.close()


def table_counts(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        return {t: len(rows) for t, rows in data.dump_state(conn).items()}
    finally:
        conn.close()


def signature(db_path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(db_path)
    try:
        return schema_signature(conn)
    finally:
        conn.close()


def test_v1_fixture_migrates_to_the_current_schema(tmp_path: Path, clock) -> None:
    paths = ProfilePaths(tmp_path / "old")
    load_v1_fixture(paths.user_db)
    rows_before = table_counts(paths.user_db)
    assert rows_before["attempt"] == 12
    assert rows_before["review_log"] == 6

    with Storage.open(paths, clock=clock) as storage:
        users = storage.users
        assert users.counts()["attempts"] == 12
        assert some(users.skill_state(data.SKILL)).stability == 15.625
        assert users.get_setting("custom.flag") == [1, 2]
        assert users.user_cards()[0].id == "mine.trig.001"
        expected_backups = ["pre-migration"] * (USER_SCHEMA_VERSION - 1)
        assert [b.reason for b in storage.backups.all()] == expected_backups

    fresh = ProfilePaths(tmp_path / "fresh")
    Storage.open(fresh, clock=clock, create=True).close(backup=False)
    assert signature(paths.user_db) == signature(fresh.user_db)
    new_tables = {"user_template": 0, "user_media": 0}  # v2; this history has nothing for them
    assert table_counts(paths.user_db) == rows_before | new_tables  # nothing lost
    assert integrity_problems(paths.user_db, full=True) == []


NEXT = len(MIGRATIONS) + 1  # the next migration's number (examples below)


def next_rebuilds_a_table(conn: sqlite3.Connection) -> None:
    """A realistic step: rebuild `setting` with a new column, keeping every row."""
    conn.execute(
        "CREATE TABLE setting_new (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL "
        "CHECK (json_valid(value)), updated_at INTEGER NOT NULL, source TEXT) STRICT"
    )
    conn.execute("INSERT INTO setting_new SELECT key, value, updated_at, 'user' FROM setting")
    conn.execute("DROP TABLE setting")
    conn.execute("ALTER TABLE setting_new RENAME TO setting")


def next_adds_an_index(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX attempt_verdict ON attempt(verdict)")


STEPS = (
    *MIGRATIONS,
    Migration(NEXT, "setting source", next_rebuilds_a_table),
    Migration(NEXT + 1, "verdict index", next_adds_an_index),
)


def test_forward_steps_each_take_a_backup_first(tmp_path: Path, clock) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_v1_fixture(paths.user_db)
    storage = Storage.open(paths, clock=clock)  # current schema, no extra steps
    storage.close(backup=False)
    earlier = set(storage.backups.all())  # the one before reaching the current schema
    calls: list[tuple[int, int]] = []

    def backup(old: int, new: int) -> None:
        calls.append((old, new))
        storage.backups.create("pre-migration")
        clock.advance(seconds=1)

    db = Database.open(
        paths.user_db,
        clock=clock,
        migrations=STEPS,
        target_version=NEXT + 1,
        before_migration=backup,
    )
    try:
        with db.reading() as conn:
            assert user_version(conn) == NEXT + 1
            assert conn.execute("SELECT count(*) FROM setting WHERE source = 'user'").fetchone()[0]
    finally:
        db.close()
    assert calls == [(NEXT - 1, NEXT), (NEXT, NEXT + 1)]
    backups = [b for b in storage.backups.all() if b not in earlier]
    assert len(backups) == 2
    versions: list[int] = []
    for b in backups:
        versions.append(some(storage.backups.preview(b).schema_version))
        assert table_counts(b.path)["attempt"] == 12
    assert sorted(versions) == [NEXT - 1, NEXT]  # each backup: the state right before its step


def test_a_failing_step_rolls_back_and_keeps_the_old_version(tmp_path: Path, clock) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_v1_fixture(paths.user_db)
    before = table_counts(paths.user_db)

    def broken(conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM skill_state")
        raise RuntimeError("bug in migration")

    steps = (*MIGRATIONS[:1], Migration(2, "broken", broken))  # instead of the real v2
    with pytest.raises(MigrationError, match="rolled back"):
        Database.open(paths.user_db, migrations=steps, target_version=2)
    assert table_counts(paths.user_db) == before
    v1 = Database.open(paths.user_db, migrations=MIGRATIONS[:1], target_version=1)
    with v1, v1.reading() as conn:
        assert user_version(conn) == 1


def test_a_step_that_breaks_foreign_keys_is_refused(tmp_path: Path) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_v1_fixture(paths.user_db)

    def orphaning(conn: sqlite3.Connection) -> None:
        conn.execute("INSERT INTO dispute (attempt_id, at) VALUES (9999, 0)")

    steps = (*MIGRATIONS, Migration(NEXT, "orphans", orphaning))
    with pytest.raises(MigrationError, match="foreign keys"):
        Database.open(paths.user_db, migrations=steps, target_version=NEXT)


def test_newer_or_foreign_databases_are_never_touched(tmp_path: Path) -> None:
    newer = tmp_path / "newer" / "user.db"
    load_v1_fixture(newer)
    conn = sqlite3.connect(newer)
    conn.execute("PRAGMA user_version = 99")
    conn.commit()
    conn.close()
    digest = hashlib.sha256(newer.read_bytes()).hexdigest()
    with pytest.raises(SchemaTooNewError):
        Database.open(newer)
    assert hashlib.sha256(newer.read_bytes()).hexdigest() == digest

    foreign = tmp_path / "foreign" / "user.db"
    foreign.parent.mkdir()
    conn = sqlite3.connect(foreign)
    conn.execute("CREATE TABLE notes (x)")
    conn.commit()
    conn.close()
    with pytest.raises(NotOurDatabaseError):
        Database.open(foreign)
    conn = sqlite3.connect(foreign)
    conn.execute("PRAGMA user_version = 1")
    conn.commit()
    conn.close()
    with pytest.raises(NotOurDatabaseError):
        Database.open(foreign)


def test_migration_lists_are_checked() -> None:
    conn = sqlite3.connect(":memory:", autocommit=True)
    with pytest.raises(ValueError, match="numbered"):
        migrate(conn, migrations=(Migration(2, "gap", lambda c: None),), target=2)
    with pytest.raises(ValueError, match="no migration reaches"):
        migrate(conn, target=USER_SCHEMA_VERSION + 1)
    assert migrate(conn) == list(range(1, USER_SCHEMA_VERSION + 1))
    assert migrate(conn) == []


def test_statement_splitter_keeps_triggers_whole() -> None:
    script = (
        "-- comment\nCREATE TABLE t (x);\n\nCREATE TRIGGER g BEFORE DELETE ON t\n"
        "BEGIN SELECT RAISE(ABORT, 'no; really'); END;\n"
    )
    parts = list(statements(script))
    assert len(parts) == 2
    assert parts[1].endswith("END;")
    with pytest.raises(ValueError, match="incomplete"):
        list(statements("CREATE TABLE t (x"))
