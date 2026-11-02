"""DEV-8: the acknowledged-write kill loop (HAZ-1, HAZ-5).

A child process (tests/storage/kill_child.py, forked per round from a process that imported
the core once) works through the real StudyService on an on-disk profile with the Test pack
attached: right, wrong and unsure answers, hints, give-ups, continue, undo and session end.
After each step returns it writes an acknowledgment to a pipe. This test kills it with
SIGKILL at seeded random moments, hundreds of times, and after every kill checks:

- every acknowledged answer is present (and every acknowledged undo is still undone);
- PRAGMA integrity_check (and foreign_key_check) is ok;
- the stored memory equals a replay of the log (Engine.recompute_memory changes nothing);
- the session resumes at the item that was on screen.

It also kills Anki imports of the fixture decks (read, plan, apply, the engine hook, each
after a pre-import backup) and migrations of the schema-v1 fixture, at random moments.
Marked slow: check.sh full and app run it, fast does not.
"""

import json
import os
import random
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import IO, Any
from zoneinfo import ZoneInfo

import pytest

from app.packs import shipped_packs
from core import cards, grader
from core.engine import Engine
from core.queue import StudyService
from core.storage import Storage
from core.storage.backups import BackupManager
from core.storage.clock import FixedClock, to_ms
from core.storage.connection import connect, integrity_problems
from core.storage.profiles import ProfilePaths
from core.storage.schema import USER_SCHEMA_VERSION, user_version
from tests.importers.conftest import FIXTURES as DECKS
from tests.storage.data import dump_state
from tests.storage.study_driver import key_checker
from tests.storage.test_migrations import load_v1_fixture

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
START = to_ms(datetime(2026, 11, 2, 9, 0, tzinfo=NY))
SEED = 20261102
STUDY_KILLS = 300
IMPORT_KILLS = 40
MIGRATION_KILLS = 40
KILLS: dict[str, int] = {}  # what landed where, for the report


@dataclass
class Round:
    pid: int
    lines: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    status: int | None = None

    @property
    def acks(self) -> list[dict[str, Any]]:
        return [p for k, p in self.lines if k == "ack"]

    @property
    def in_flight(self) -> str | None:
        """The step that had begun but not been acknowledged when the child died."""
        last = None
        for kind, payload in self.lines:
            if kind == "begin":
                last = payload["step"]
            elif kind == "ack":
                last = None
        return last

    @property
    def last_now(self) -> int:
        times = [p["now"] for _, p in self.lines if "now" in p]
        return max(times) if times else 0


class Children:
    """The fork server; one job at a time."""

    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "tests.storage.kill_child"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

    @property
    def out(self) -> IO[str]:
        assert self.proc.stdout is not None
        return self.proc.stdout

    def _line(self) -> tuple[str, str]:
        line = self.out.readline()
        assert line, "the fork server died"
        kind, _, rest = line.rstrip("\n").partition(" ")
        assert kind != "error", rest.replace(" | ", "\n")
        return kind, rest

    def run(self, job: dict[str, Any], *, acks: int | None, delay: float = 0.0) -> Round:
        """Start a job; after `acks` acknowledgments (None: never) and `delay` seconds,
        SIGKILL its process group. Returns everything it said."""
        assert self.proc.stdin is not None
        job = {**job, "linger": acks is not None}
        self.proc.stdin.write(json.dumps(job) + "\n")
        self.proc.stdin.flush()
        kind, rest = self._line()
        assert kind == "forked", (kind, rest)
        current = Round(int(rest))
        killed = False
        while True:
            if not killed and acks is not None and current.lines and len(current.acks) >= acks:
                time.sleep(delay)
                os.killpg(current.pid, signal.SIGKILL)
                killed = True
            kind, rest = self._line()
            if kind == "exit":
                pid, status = rest.split()
                assert int(pid) == current.pid
                current.status = int(status)
                break
            current.lines.append((kind, json.loads(rest)))
        if killed:
            assert os.WIFSIGNALED(current.status), current.status
            assert os.WTERMSIG(current.status) == signal.SIGKILL
        else:
            assert current.status == 0, current.lines[-3:]
        return current

    def close(self) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.close()
        self.proc.wait(timeout=30)


@pytest.fixture(scope="module")
def children() -> Iterator[Children]:
    server = Children()
    try:
        yield server
    finally:
        server.close()
        grader.shutdown()
        cards.shutdown()


@pytest.fixture(scope="module")
def test_pack() -> Path:
    return next(p for p in shipped_packs() if p.stem == "test")


def check_database(db: Path) -> None:
    assert integrity_problems(db, full=True) == []


def rows(db: Path, sql: str) -> list[tuple[Any, ...]]:
    conn = connect(db, mode="ro")
    try:
        return [tuple(r) for r in conn.execute(sql)]
    finally:
        conn.close()


# ---------------------------------------------------------------- answers


@dataclass
class Expected:
    """What the acknowledgments promise."""

    attempts: set[int] = field(default_factory=set)
    voided: set[int] = field(default_factory=set)
    answered: set[str] = field(default_factory=set)  # presentation ids whose verdict was shown
    pending: str | None = None
    session: int | None = None
    key: str | None = None

    def note(self, acks: list[dict[str, Any]]) -> None:
        for ack in acks:
            if ack["step"] == "open":
                continue
            self.attempts |= set(ack["new"])
            self.voided |= set(ack["voided"])
            if ack["answered"]:
                self.answered.add(ack["answered"])
            if ack["undid"]:  # undone before it was graded: the problem is back, unanswered
                self.answered.discard(ack["undid"])
            self.pending, self.session, self.key = ack["pending"], ack["session"], ack["key"]


def open_screen(db: Path) -> tuple[int | None, str | None, str | None]:
    """The open session in the file: its id, the item on screen, the pending presentation."""
    found = rows(db, "SELECT id, current FROM session WHERE ended_at IS NULL ORDER BY id DESC")
    if not found:
        return None, None, None
    current = json.loads(found[0][1] or "null") or {}
    pending = current.get("presentation_id") if current.get("pending") else None
    return found[0][0], current.get("key"), pending


def check_answers(root: Path, pack: Path, expected: Expected, done: Round) -> None:
    db = root / "user.db"
    check_database(db)
    stored = dict(rows(db, "SELECT id, voided_by FROM attempt"))
    missing = expected.attempts - set(stored)
    assert not missing, f"acknowledged attempts lost: {sorted(missing)}"
    undone = {i for i in expected.voided if stored.get(i) is None}
    assert not undone, f"acknowledged undos lost: {sorted(undone)}"
    step = done.in_flight
    session, key, pending = open_screen(db)
    if step in (None, "open", "answer"):  # nothing in flight moves the session on
        assert (session, key) == (expected.session, expected.key), step
    # Every answer whose verdict was shown is graded, or saved to be graded on continue.
    graded = {r[0] for r in rows(db, "SELECT presentation_id FROM attempt WHERE final = 1")}
    lost = expected.answered - graded - {pending}
    if step == "undo" and expected.pending in lost:
        lost.discard(expected.pending)  # the undo in flight took it back: no longer promised
        expected.answered.discard(expected.pending)
    assert not lost, f"acknowledged answers lost: {sorted(lost)}"
    clock = FixedClock(done.last_now + 1000, tz=NY)
    with Storage.open(ProfilePaths(root), pack_paths=[pack], clock=clock) as storage:
        engine = Engine(storage)
        assert engine.recompute_memory().changed == ()  # stored state == replay of the log
        today = engine.days().day_of(clock.now_ms()).isoformat()
        open_session = storage.users.latest_open_session()
        turn = StudyService(storage, checker=key_checker).resume()
        if open_session is not None and open_session.study_day == today:
            assert turn is not None, "today's open session did not resume"
            if turn.problem is not None and key is not None:
                assert turn.problem.item_key == key  # at the same item (QUE-16)
    # resume() may close an earlier day's session: the next round starts from the file.
    expected.session, expected.key, expected.pending = open_screen(db)


def test_acknowledged_answers_survive_sigkill(
    tmp_path: Path, children: Children, test_pack: Path
) -> None:
    root = tmp_path / "profile"
    clock = FixedClock(START, tz=NY)
    with Storage.open(ProfilePaths(root), pack_paths=[test_pack], clock=clock, create=True) as s:
        s.users.set_setting("study.timezone", "America/New_York")
        for section in s.packs.sections():
            s.users.set_section_state(section.id, "learning")
    rng = random.Random(SEED)  # noqa: S311 -- reproducible kill moments
    expected = Expected()
    now, steps = START + 60_000, 0
    for _ in range(STUDY_KILLS):
        job: dict[str, Any] = {"job": "study", "root": str(root), "pack": str(test_pack)}
        job |= {"seed": rng.randrange(2**32), "start_ms": now}
        acks = rng.choice([0, 1, 1, 2, 3, 5, 8, 13])
        done = children.run(job, acks=acks, delay=rng.uniform(0, 0.03))
        expected.note(done.acks)
        steps += len(done.acks)
        KILLS[f"answers: during {done.in_flight or 'between steps'}"] = (
            KILLS.get(f"answers: during {done.in_flight or 'between steps'}", 0) + 1
        )
        check_answers(root, test_pack, expected, done)
        now = done.last_now + 60_000
    total = len(expected.attempts)
    print(f"\nDEV-8 answers: {STUDY_KILLS} kills, {steps} acknowledged steps, {total} attempts")
    assert total > STUDY_KILLS  # it really answered, round after round


# ---------------------------------------------------------------- imports


def anki_decks() -> list[str]:
    return [str(p) for p in sorted(DECKS.iterdir()) if p.suffix in (".apkg", ".colpkg", ".txt")]


def test_anki_imports_survive_sigkill(tmp_path: Path, children: Children) -> None:
    root = tmp_path / "profile"
    clock = FixedClock(START, tz=NY)
    Storage.open(ProfilePaths(root), clock=clock, create=True).close(backup=False)
    rng = random.Random(SEED + 1)  # noqa: S311
    newest_backup: str | None = None
    records: set[int] = set()
    now = START + 60_000
    for _ in range(IMPORT_KILLS):
        job: dict[str, Any] = {"job": "import", "root": str(root), "seed": rng.randrange(2**32)}
        job |= {"start_ms": now, "decks": anki_decks()}
        done = children.run(job, acks=rng.randint(1, 12), delay=rng.uniform(0, 0.05))
        step = done.in_flight
        KILLS[f"imports: during {step or 'between steps'}"] = (
            KILLS.get(f"imports: during {step or 'between steps'}", 0) + 1
        )
        taken = [a["backup"] for a in done.acks if a["step"] == "backup"]
        newest_backup = taken[-1] if taken else newest_backup
        records |= {a["record"] for a in done.acks if a["step"] == "apply" and a["record"]}
        db = root / "user.db"
        check_database(db)
        stored = {r[0] for r in rows(db, "SELECT id FROM import_record")}
        assert records <= stored  # every acknowledged import is there, whole
        assert len(stored - records) <= (1 if step == "apply" else 0)  # or the one in flight
        records |= stored  # committed: later rounds must keep it too
        manager = BackupManager(db, root / "backups", clock=clock)
        present = {b.path.name: b for b in manager.all()}
        assert all(manager.preview(b).ok for b in present.values())  # no half-written backup
        if newest_backup is not None:  # pruning keeps the last 10 pre-import backups
            assert newest_backup in present
        later = FixedClock(done.last_now + 1000, tz=NY)
        with Storage.open(ProfilePaths(root), clock=later) as storage:
            assert Engine(storage).recompute_memory().changed == ()
        now = done.last_now + 60_000
    finished = children.run(
        {"job": "import", "root": str(root), "seed": 1, "start_ms": now, "decks": anki_decks()},
        acks=None,
    )
    assert finished.acks[-1]["step"] == "done"  # after all that, an import still completes
    check_database(root / "user.db")


# ---------------------------------------------------------------- migrations


def test_migrations_survive_sigkill(tmp_path: Path, children: Children) -> None:
    template = tmp_path / "v1" / "user.db"
    load_v1_fixture(template)
    conn = sqlite3.connect(template)
    original = dump_state(conn)
    conn.close()
    counts = {t: len(r) for t, r in original.items()}
    rng = random.Random(SEED + 2)  # noqa: S311
    # How long an open with its migration takes here, to aim the kills inside it.
    spans = []
    for n in range(3):
        probe = tmp_path / f"probe{n}"
        shutil.copytree(template.parent, probe)
        timed = children.run({"job": "migrate", "root": str(probe), "start_ms": START}, acks=None)
        spans.append(timed.acks[-1]["t"] - timed.lines[0][1]["t"])
    span = sorted(spans)[1]
    during = 0
    for index in range(MIGRATION_KILLS):
        root = tmp_path / f"m{index}"
        shutil.copytree(template.parent, root)
        job: dict[str, Any] = {"job": "migrate", "root": str(root), "start_ms": START + index}
        done = children.run(job, acks=0, delay=rng.uniform(0, span))
        during += done.in_flight == "migrate"
        db = root / "user.db"
        check_database(db)
        conn = connect(db, mode="ro")
        try:
            version = user_version(conn)
            state = dump_state(conn)
        finally:
            conn.close()
        assert version in (1, USER_SCHEMA_VERSION)
        if version == 1:
            assert state == original  # rolled back: exactly the v1 data
        else:
            assert {t: len(state[t]) for t in original} == counts  # migrated: nothing lost
        for backup in BackupManager(db, root / "backups", clock=FixedClock(START, tz=NY)).all():
            conn = sqlite3.connect(backup.path)
            try:
                assert dump_state(conn) == original  # a finished backup is the v1 data
            finally:
                conn.close()
        with Storage.open(ProfilePaths(root), clock=FixedClock(START + 10_000, tz=NY)) as s:
            assert s.users.counts()["attempts"] == counts["attempt"]
        conn = connect(db, mode="ro")
        try:
            assert user_version(conn) == USER_SCHEMA_VERSION  # the next open finishes it
        finally:
            conn.close()
    KILLS["migrations: during the open"] = during
    KILLS["migrations: after it"] = MIGRATION_KILLS - during
    print(f"\nDEV-8 migrations: {MIGRATION_KILLS} kills, {during} inside the open ({span:.3f} s)")
    print(f"DEV-8 kills: {sum(KILLS.values())} {json.dumps(KILLS, sort_keys=True)}")
    assert during >= MIGRATION_KILLS // 3  # the kills really landed inside migrations
