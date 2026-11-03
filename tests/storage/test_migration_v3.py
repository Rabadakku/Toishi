"""Schema v3 (wave 2): the v2 -> v3 migration of a student's progress, exact and safe.

A frozen v2 database goes through it: user_v2.sql, written by the v2 code through the real
StudyService on the Test pack (tests/storage/v2_user.py), so it holds a v2 history exactly as
that code wrote it. Every row and value is checked afterwards; a crash anywhere inside the
step leaves either the untouched v2 or a complete v3; and v2 code refuses a v3 database
without touching it.
"""

import copy
import hashlib
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

import pytest

from core.model import Attempt, CourseSetup, LearnerParams
from core.storage import Database, SchemaTooNewError, Storage, StorageError
from core.storage.backups import BackupManager
from core.storage.clock import FixedClock
from core.storage.connection import integrity_problems
from core.storage.profiles import ProfilePaths
from core.storage.schema import MIGRATIONS, USER_SCHEMA_VERSION, schema_signature, user_version
from tests.storage.data import some
from tests.storage.v1_cards import load_fixture
from tests.storage.v2_user import COURSE, COURSE_START, USER_V2

ROOT = Path(__file__).resolve().parents[2]
# The last commit with schema v2: the parent of the commit that added the v3 migration (found
# from the history, so a rebase or a rewritten history does not lose it).
V3_MIGRATION = "core/storage/sql/migrate_user_v3.sql"

Rows = dict[str, list[dict[str, Any]]]

V3_ATTEMPT_COLUMNS = (
    "role",
    "milestone",
    "missed",
    "plan_p",
    "ladder",
    "sitting",
    "learner_version",
    "valid_minutes",
)


def rows_of(db: Path) -> Rows:
    """Every row of every table, as dicts, in rowid order."""
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        tables = [
            str(r[0])
            for r in conn.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            t: [dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")]  # noqa: S608
            for t in tables
        }
    finally:
        conn.close()


def version_of(db: Path) -> int:
    conn = sqlite3.connect(db)
    try:
        return user_version(conn)
    finally:
        conn.close()


def expected_v3(v2: Rows) -> Rows:
    """The v2 rows as v3 must hold them: every row and value kept, the attempt's new columns
    empty, a course_settings row for each course goal with a start or goal date (start and
    end_day copied, the rest at their defaults, stamped with the goal's time), no parameter
    version yet (the app writes the prior on first use)."""
    out = copy.deepcopy(v2)
    for row in out["attempt"]:
        row.update(dict.fromkeys(V3_ATTEMPT_COLUMNS))
    goals = sorted(v2["course_goal"], key=lambda g: g["course_id"])
    out["course_settings"] = [
        {
            "course_id": g["course_id"],
            "start": g["starts_on"],
            "aligned_deck": None,
            "aligned_day": None,
            "pace_factor": 1.0,
            "accuracy_target": 0.9,
            "target_tier": 4,
            "end_day": g["goal_date"],
            "keep_target": 0.8,
            "keep_tier": 3,
            "growth_band": "standard",
            "updated_at": g["updated_at"],
        }
        for g in goals
        if g["starts_on"] is not None or g["goal_date"] is not None
    ]
    out["learner_params"] = []
    return out


def fresh_signature(tmp: Path) -> list[tuple[str, str]]:
    db = Database.open(tmp / "fresh" / "user.db", create=True)
    db.close()
    conn = sqlite3.connect(tmp / "fresh" / "user.db")
    try:
        return schema_signature(conn)
    finally:
        conn.close()


def assert_complete_v3(db: Path, v2: Rows) -> None:
    assert version_of(db) == USER_SCHEMA_VERSION == 3
    assert integrity_problems(db, full=True) == []
    assert rows_of(db) == expected_v3(v2)


def v2_profile(root: Path) -> tuple[ProfilePaths, Rows]:
    paths = ProfilePaths(root)
    load_fixture(USER_V2, paths.user_db, version=2)
    return paths, rows_of(paths.user_db)


# ---------------------------------------------------------------- the frozen database


def test_the_v2_fixture_holds_a_real_history() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(USER_V2.read_text())

    def one(sql: str) -> Any:
        return conn.execute(sql).fetchone()[0]

    assert one("SELECT count(*) FROM attempt") > 50
    assert one("SELECT count(*) FROM attempt WHERE final = 0 AND verdict = 'incorrect'") > 0
    assert one("SELECT count(*) FROM attempt WHERE attempt_number = 2 AND verdict = 'correct'")
    assert one("SELECT count(*) FROM attempt WHERE verdict = 'gave-up'") > 0
    assert one("SELECT count(*) FROM attempt WHERE hints_used > 0") > 0
    assert one("SELECT count(*) FROM attempt WHERE voided_by IS NOT NULL") > 0
    assert one("SELECT count(*) FROM attempt WHERE json_extract(extra, '$.parts') IS NOT NULL")
    assert one("SELECT count(*) FROM attempt WHERE card_kind IN ('flashcard', 'cloze')") > 0
    assert one("SELECT count(*) FROM attempt WHERE card_kind = 'problem' AND verdict = 'shown'")
    queue_modes = {
        r[0] for r in conn.execute("SELECT json_extract(extra, '$.queue_mode') FROM attempt")
    }
    assert {"daily", "focused", "practice-test"} <= queue_modes
    assert one("SELECT starts_on FROM course_goal WHERE course_id = 'Test Course'") == "2026-09-28"
    assert one("SELECT count(*) FROM exam") == 2
    conn.close()


def test_the_v2_fixture_migrates_every_row_and_value(tmp_path: Path) -> None:
    paths, v2 = v2_profile(tmp_path / "p")
    clock = FixedClock(1_800_000_000_000)
    Storage.open(paths, clock=clock).close(backup=False)
    assert_complete_v3(paths.user_db, v2)
    conn = sqlite3.connect(paths.user_db)
    try:
        assert schema_signature(conn) == fresh_signature(tmp_path)
    finally:
        conn.close()
    (backup,) = BackupManager(paths.user_db, paths.backups_dir, clock=clock).all()
    assert backup.reason == "pre-migration"  # BAK-2: the v2 state, kept
    assert rows_of(backup.path) == v2


def test_migrating_again_finds_nothing_to_do(tmp_path: Path) -> None:
    paths, v2 = v2_profile(tmp_path / "p")
    Storage.open(paths).close(backup=False)
    with Storage.open(paths) as storage:
        assert [b.reason for b in storage.backups.all()].count("pre-migration") == 1
    assert_complete_v3(paths.user_db, v2)


def test_the_new_columns_are_append_only_too(tmp_path: Path) -> None:
    paths, _ = v2_profile(tmp_path / "p")
    with Storage.open(paths) as storage:
        for sql in (
            "UPDATE attempt SET role = 'growth' WHERE id = 1",
            "UPDATE attempt SET valid_minutes = 2.0 WHERE id = 1",
            "UPDATE attempt SET learner_version = 'x' WHERE id = 1",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                run_sql(storage, sql)


def run_sql(storage: Storage, sql: str) -> None:
    def write(conn: sqlite3.Connection) -> None:
        conn.execute(sql)

    storage.db.write(write)


# ---------------------------------------------------------------- the app on a migrated profile


def test_the_course_start_carries_over_and_old_attempts_read_back(tmp_path: Path) -> None:
    paths, v2 = v2_profile(tmp_path / "p")
    with Storage.open(paths) as storage:
        users = storage.users
        setup = some(users.course_setup(COURSE))
        assert setup == CourseSetup(
            course_id=COURSE, start=COURSE_START, updated_at=setup.updated_at
        )
        assert users.course_setup("Answer Input Tutorial") is None  # no start, no goal date
        attempts = users.attempts(include_voided=True)
        assert len(attempts) == len(v2["attempt"])
        assert all(a.role is None and a.valid_minutes is None for a in attempts)
        assert users.learner_params() is None  # the app writes the prior on first use


def test_the_last_v2_answer_can_still_be_undone(tmp_path: Path) -> None:
    """Its snapshots were taken before the new columns existed."""
    paths, _ = v2_profile(tmp_path / "p")
    with Storage.open(paths) as storage:
        users = storage.users
        last = some(users.last_attempt())
        users.undo_last_answer()
        assert some(users.attempt(some(last.id))).voided_by is not None


def test_v3_attempts_store_what_the_planner_chose(tmp_path: Path) -> None:
    from core.model import GradedAnswer

    paths, _ = v2_profile(tmp_path / "p")
    with Storage.open(paths) as storage:
        stored = storage.users.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    card_id="test.linear.solve.001",
                    skill_id="test.alg.linear-solve",
                    verdict="correct",
                    role="sitting",
                    milestone="M2",
                    missed=False,
                    plan_p=0.81,
                    ladder=0,
                    sitting="2026-11-02#1",
                    learner_version="prior",
                    valid_minutes=1.5,
                )
            )
        )
        back = some(storage.users.attempt(some(stored.id)))
        assert (back.role, back.milestone, back.missed, back.plan_p) == (
            "sitting",
            "M2",
            False,
            0.81,
        )
        assert (back.ladder, back.sitting, back.learner_version) == (0, "2026-11-02#1", "prior")
        assert back.valid_minutes == 1.5


def test_parameter_versions_keep_one_current_and_never_change(tmp_path: Path) -> None:
    paths, _ = v2_profile(tmp_path / "p")
    with Storage.open(paths) as storage:
        users = storage.users
        prior = users.add_learner_params(
            LearnerParams(version="prior", params={"slip": 0.02}, source="prior", current=True)
        )
        assert some(users.learner_params()).version == "prior"
        users.add_learner_params(
            LearnerParams(version="map-1", params={"slip": 0.03}, source="refit", report={"a": 1})
        )
        assert some(users.learner_params()).version == "prior"  # not adopted: not current
        users.add_learner_params(
            LearnerParams(version="map-2", params={"slip": 0.04}, source="refit", current=True)
        )
        assert some(users.learner_params()).version == "map-2"
        assert [p.version for p in users.learner_param_history()] == ["prior", "map-1", "map-2"]
        assert not some(users.learner_params("prior")).current
        with pytest.raises(StorageError, match="already exists"):
            users.add_learner_params(prior)
        for sql in (
            "UPDATE learner_params SET params = '{}' WHERE version = 'prior'",
            "DELETE FROM learner_params WHERE version = 'map-1'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                run_sql(storage, sql)
        with pytest.raises(sqlite3.IntegrityError):  # exactly one current row
            run_sql(storage, "UPDATE learner_params SET current = 1 WHERE version = 'prior'")


def test_course_setups_are_checked(tmp_path: Path) -> None:
    from core.model import ShapeError

    bad: dict[str, Any]
    for bad in (
        {"pace_factor": 2.0},
        {"accuracy_target": 1.0},
        {"target_tier": 6},
        {"growth_band": "easy"},
        {"aligned_deck": "C::U::S"},  # without its day
    ):
        with pytest.raises(ShapeError):
            CourseSetup(course_id="c", **bad)
    paths, _ = v2_profile(tmp_path / "p")
    sql = "INSERT INTO course_settings (course_id, pace_factor, updated_at) VALUES ('c', 3.0, 0)"
    with Storage.open(paths) as storage, pytest.raises(sqlite3.IntegrityError):
        run_sql(storage, sql)  # the table checks the same ranges


# ---------------------------------------------------------------- crashes inside the step


def run_child(*args: str, timeout: float = 120) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "-m", "tests.storage.fault_child", *args],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.splitlines()


def count_steps(tmp_path: Path) -> int:
    paths, _ = v2_profile(tmp_path / "count")
    code, lines = run_child("v3-count", str(paths.root))
    assert code == 0, lines
    steps = int(lines[-1].split()[1])
    assert steps > 200
    return steps


def assert_v2_or_complete_v3(paths: ProfilePaths, v2: Rows) -> str:
    """After a crash: the untouched v2 (still usable by v2 code) or a complete v3. Then the
    current app opens it, migrating if needed, and ends at a complete v3 either way."""
    db = paths.user_db
    assert integrity_problems(db, full=True) == []
    if version_of(db) == 2:
        assert rows_of(db) == v2
        old = Database.open(db, migrations=MIGRATIONS[:2], target_version=2)
        with old, old.reading() as conn:  # what the v2 app does on open
            assert conn.execute("SELECT count(*) FROM attempt").fetchone()[0] == len(v2["attempt"])
        found = "v2"
    else:
        assert_complete_v3(db, v2)
        found = "v3"
    Storage.open(paths).close(backup=False)
    assert_complete_v3(db, v2)
    backups = BackupManager(db, paths.backups_dir, clock=FixedClock(0)).all()
    assert backups
    assert all(b.reason == "pre-migration" for b in backups)
    assert all(rows_of(b.path) == v2 for b in backups)  # each one the v2 state
    return found


def crash_at(tmp_path: Path, name: str, steps: int) -> str:
    paths, v2 = v2_profile(tmp_path / name)
    code, lines = run_child("v3-die", str(paths.root), str(steps))
    assert code in (0, 9), lines
    return assert_v2_or_complete_v3(paths, v2)


def test_a_crash_inside_the_migration_leaves_v2_or_a_complete_v3(tmp_path: Path) -> None:
    total = count_steps(tmp_path)
    found = [crash_at(tmp_path, f"at-{n}", n) for n in (1, total // 3, 2 * total // 3, total)]
    assert found[:3] == ["v2", "v2", "v2"]  # rolled back, as if it never started
    assert found[3] == "v3"  # its last instruction runs after the commit
    assert crash_at(tmp_path, "never", total + 1) == "v3"


@pytest.mark.slow
def test_crashes_all_through_the_migration(tmp_path: Path) -> None:
    total = count_steps(tmp_path)
    points = [*range(1, total, max(1, total // 40)), total - 1, total, total + 1]
    seen = {crash_at(tmp_path, f"at-{n}", n) for n in points}
    assert seen == {"v2", "v3"}


@pytest.mark.slow
def test_sigkill_at_random_moments_of_the_migration(tmp_path: Path) -> None:
    rng = random.Random(20261103)  # noqa: S311 -- reproducible timing, not crypto
    found = []
    for round_ in range(8):
        paths, v2 = v2_profile(tmp_path / f"kill-{round_}")
        proc = subprocess.Popen(
            [sys.executable, "-m", "tests.storage.fault_child", "v3-slow", str(paths.root)],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            stdout=subprocess.PIPE,
            text=True,
        )
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "migrating"
        time.sleep(rng.random() * 0.5)
        proc.kill()
        proc.wait()
        found.append(assert_v2_or_complete_v3(paths, v2))
    assert "v2" in found  # at least one kill landed inside the step


# ---------------------------------------------------------------- v2 code meets v3


def test_the_v2_code_path_refuses_a_v3_database_untouched(tmp_path: Path) -> None:
    paths, _ = v2_profile(tmp_path / "p")
    Storage.open(paths).close(backup=False)
    digest = hashlib.sha256(paths.user_db.read_bytes()).hexdigest()
    with pytest.raises(SchemaTooNewError, match="v3; this app understands up to v2"):
        Database.open(paths.user_db, migrations=MIGRATIONS[:2], target_version=2)
    assert hashlib.sha256(paths.user_db.read_bytes()).hexdigest() == digest


def v2_code(tmp_path: Path) -> Path:
    """core/ exactly as the last v2 commit had it, unpacked from git."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not installed")
    added = subprocess.run(
        [git, "-C", str(ROOT), "log", "--diff-filter=A", "--format=%H", "--", V3_MIGRATION],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    if not added:
        pytest.skip("this clone has no history of the v3 migration")
    last_v2 = f"{added[-1]}^"
    found = subprocess.run(
        [git, "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{last_v2}{{commit}}"],
        capture_output=True,
        check=False,
    )
    if found.returncode != 0:
        pytest.skip(f"commit {last_v2} is not in this clone")
    archive = tmp_path / "v2.tar"
    subprocess.run(
        [git, "-C", str(ROOT), "archive", "-o", str(archive), last_v2, "core"],
        check=True,
    )
    out = tmp_path / "v2-code"
    with tarfile.open(archive) as tar:
        tar.extractall(out, filter="data")
    return out


V2_SCRIPT = """
import hashlib, sys
from pathlib import Path
import core.storage.schema as schema
assert schema.USER_SCHEMA_VERSION == 2, schema.__file__
from core.storage import ProfileManager, SchemaTooNewError, Storage
from core.storage.profiles import ProfilePaths

profile, meprofile, data_dir = map(Path, sys.argv[1:4])
db = profile / "user.db"
before = hashlib.sha256(db.read_bytes()).hexdigest()
try:
    Storage.open(ProfilePaths(profile))
except SchemaTooNewError as error:
    print("refused profile:", error)
assert hashlib.sha256(db.read_bytes()).hexdigest() == before, "the v3 file was changed"
try:
    ProfileManager(data_dir).import_profile(meprofile)
except SchemaTooNewError as error:
    print("refused meprofile:", error)
"""


def test_the_released_v2_code_refuses_v3_files_untouched(tmp_path: Path) -> None:
    code = v2_code(tmp_path)
    paths, _ = v2_profile(tmp_path / "p")
    Storage.open(paths).close(backup=False)  # now v3
    from core.storage.export import export_profile

    meprofile = tmp_path / "p.meprofile"
    export_profile(paths.user_db, paths.media_dir, meprofile, name="P", clock=FixedClock(0))
    proc = subprocess.run(
        [sys.executable, "-c", V2_SCRIPT, str(paths.root), str(meprofile), str(tmp_path / "data")],
        cwd=code,
        env={**os.environ, "PYTHONPATH": str(code)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    message = (
        "user.db is schema v3; this app understands up to v2. "
        "Update the app; the file was left untouched."
    )
    assert proc.stdout.splitlines() == [
        f"refused profile: {message}",
        f"refused meprofile: {message}",
    ]
