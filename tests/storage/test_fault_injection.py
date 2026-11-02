"""No crash, kill or interrupted migration/backup/restore may lose or corrupt progress.

Each test runs the real storage code in a child process (tests/storage/fault_child.py)
that dies abruptly (os._exit or SIGKILL), then checks the database from the outside.
"""

import fcntl
import os
import random
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from core.storage import Storage, connection
from core.storage.connection import connect, integrity_problems
from core.storage.profiles import ProfilePaths
from core.storage.schema import USER_SCHEMA_VERSION, user_version
from tests.storage.data import some

ROOT = Path(__file__).resolve().parents[2]


def child(mode: str, root: Path, *, timeout: float = 60) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "-m", "tests.storage.fault_child", mode, str(root)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.splitlines()


def acked(lines: list[str]) -> list[int]:
    return [int(line.split()[1]) for line in lines if line.startswith("ok ")]


def check_consistent(root: Path) -> int:
    """The database is intact and every committed answer is whole. Returns the count."""
    db = root / "user.db"
    assert integrity_problems(db, full=True) == []
    conn = connect(db, mode="rw")
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM attempt ORDER BY id")]
        reviews = [r[0] for r in conn.execute("SELECT attempt_id FROM review_log ORDER BY id")]
        reps = conn.execute("SELECT reps FROM skill_state").fetchone()
        seen = conn.execute("SELECT times_seen FROM card_user").fetchone()
        half = conn.execute("SELECT count(*) FROM setting WHERE key = 'half'").fetchone()[0]
    finally:
        conn.close()
    assert ids == list(range(1, len(ids) + 1))
    assert reviews == ids  # each answer's review committed with it, or neither
    if ids:
        assert reps[0] == seen[0] == len(ids)  # state rows match the last committed answer
    assert half == 0
    return len(ids)


DURABILITY_PRAGMAS = ("synchronous", "fullfsync", "checkpoint_fullfsync")


def durability(conn: sqlite3.Connection) -> dict[str, int]:
    return {name: conn.execute(f"PRAGMA {name}").fetchone()[0] for name in DURABILITY_PRAGMAS}


def test_commits_reach_the_disk_itself_not_just_its_cache(storage: Storage) -> None:
    # On macOS fsync() only hands data to the drive, whose volatile cache can still lose
    # it (or write it out of order) on power loss. SQLite uses F_FULLFSYNC only when
    # fullfsync / checkpoint_fullfsync are on; every connection that may commit or
    # checkpoint (the last one to close checkpoints) needs them.
    full = {"synchronous": 2, "fullfsync": 1, "checkpoint_fullfsync": 1}
    assert storage.db.write(durability) == full
    with storage.db.reading() as conn:
        assert durability(conn) == full
    other = connect(storage.paths.user_db)
    try:
        assert durability(other) == full
    finally:
        other.close()


def test_file_syncs_use_full_fsync_where_the_os_has_it(tmp_path: Path, monkeypatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr(fcntl, "F_FULLFSYNC", 51, raising=False)
    monkeypatch.setattr(fcntl, "fcntl", lambda fd, op, *args: calls.append(op))
    target = tmp_path / "backup.db"
    target.write_bytes(b"x")
    connection.fsync_path(target)
    assert calls == [51]


def test_exit_in_the_middle_of_a_transaction_leaves_nothing_half_done(tmp_path: Path) -> None:
    code, lines = child("mid-transaction", tmp_path)
    assert code == 9
    assert lines[-1] == "dying"
    assert check_consistent(tmp_path) == 5 == len(acked(lines))


def test_exit_right_after_commit_keeps_the_answer(tmp_path: Path) -> None:
    code, lines = child("after-commit", tmp_path)
    assert code == 9
    assert check_consistent(tmp_path) == 3 == len(acked(lines))
    with Storage.open(ProfilePaths(tmp_path)) as storage:  # reopens cleanly
        assert some(storage.users.skill_state("calc1.s")).reps == 3


def test_sigkill_at_random_moments_never_loses_a_committed_answer(tmp_path: Path) -> None:
    rng = random.Random(20261101)  # noqa: S311 -- reproducible timing, not crypto
    total_acked = 0
    for _round in range(6):
        proc = subprocess.Popen(
            [sys.executable, "-m", "tests.storage.fault_child", "loop", str(tmp_path)],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            stdout=subprocess.PIPE,
            text=True,
        )
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "ready"
        wanted = rng.randint(1, 25)
        ids: list[int] = []
        while len(ids) < wanted:
            ids.append(int(proc.stdout.readline().split()[1]))
        time.sleep(rng.random() * 0.02)  # land somewhere inside a later write
        proc.kill()
        proc.wait()
        ids += acked(proc.stdout.read().splitlines())  # acks still in the pipe
        total_acked = ids[-1]
        count = check_consistent(tmp_path)
        assert total_acked <= count <= total_acked + 1  # the one in flight: all or nothing
    with Storage.open(ProfilePaths(tmp_path)) as storage:
        assert some(storage.users.counts()["attempts"]) >= total_acked


def test_crash_during_a_backup_leaves_no_broken_backup(tmp_path: Path) -> None:
    code, lines = child("mid-backup", tmp_path)
    assert code == 9
    assert lines[-1] == "dying"
    assert list((tmp_path / "backups").glob("*.tmp"))  # the partial file is there ...
    with Storage.open(ProfilePaths(tmp_path)) as storage:
        assert storage.backups.all() == []  # ... but never listed as a backup
        made = storage.backups.create("manual")
        assert storage.backups.preview(made).ok
    assert not list((tmp_path / "backups").glob("*.tmp"))  # and cleaned up next time
    assert check_consistent(tmp_path) == 2


def test_crash_during_a_migration_leaves_the_old_version_intact(tmp_path: Path) -> None:
    code, lines = child("mid-migration", tmp_path)
    assert code == 9
    assert lines[-1] == "dying"
    assert check_consistent(tmp_path) == 4
    conn = connect(tmp_path / "user.db", mode="rw")
    try:
        assert user_version(conn) == USER_SCHEMA_VERSION
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(setting)")]
        assert "extra" not in columns
    finally:
        conn.close()
    with Storage.open(ProfilePaths(tmp_path)) as storage:
        assert [b.reason for b in storage.backups.all()] == ["pre-migration"]
        assert some(storage.users.skill_state("calc1.s")).reps == 4


def test_crash_during_a_restore_is_finished_on_next_open(tmp_path: Path) -> None:
    code, lines = child("mid-restore", tmp_path)
    assert code == 9
    assert lines[-1] == "dying"
    assert not (tmp_path / "user.db").exists()
    assert (tmp_path / "user.db.incoming").exists()
    with Storage.open(ProfilePaths(tmp_path)) as storage:
        assert storage.users.counts()["attempts"] == 2  # the backup's state
        reasons = sorted(b.reason for b in storage.backups.all())
        assert reasons == ["manual", "pre-restore"]
    replaced = list((tmp_path / "backups").glob("replaced-*/user.db"))
    assert len(replaced) == 1  # the state before the restore is kept too
    assert check_consistent(tmp_path) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="flock")
def test_a_second_process_cannot_open_the_same_profile(tmp_path: Path) -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "tests.storage.fault_child", "sleep", str(tmp_path)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "ready"
        assert proc.stdout.readline().startswith("ok ")
        from core.storage import ProfileInUseError

        with pytest.raises(ProfileInUseError):
            Storage.open(ProfilePaths(tmp_path))
    finally:
        proc.kill()
        proc.wait()
    with Storage.open(ProfilePaths(tmp_path)) as storage:  # the lock died with it
        assert storage.users.counts()["attempts"] == 1
