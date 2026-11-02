"""DEV-9: a Hypothesis state machine over the real StudyService, on an on-disk profile with
the Test pack attached.

Rules: start, answer (right, wrong, unsure, hint first, give up), continue, undo, end,
reopen storage (close, then a new Storage on the same files) and the clock moving by
minutes, by days, across the 4 AM rollover and across a daylight-saving change in
America/New_York. Invariants after every step: nothing but a QueueError (the message the
student sees) escapes; every committed attempt survives, reopens included; the stored
memory equals a replay of the log; due dates are finite and never before the last review;
an undo restores exactly the state before the answer.

The fast profile runs in check.sh fast (well under 30 s); the long one is marked slow.
"""

import math
import shutil
import tempfile
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    precondition,
    rule,
    run_state_machine_as_test,
)

from app.packs import shipped_packs
from core import cards, grader
from core.engine import Engine
from core.model import FlashcardState, SkillState
from core.queue import Plan, QueueError, StudyService, Turn
from core.storage import Storage
from core.storage.clock import DEFAULT_ROLLOVER_HOUR, FixedClock, from_ms, to_ms
from core.storage.profiles import ProfilePaths
from tests.storage.study_driver import (
    How,
    answer,
    attempt_ids,
    current_key,
    key_checker,
    progress,
)

NY = ZoneInfo("America/New_York")
START = datetime(2026, 10, 31, 9, 0, tzinfo=NY)  # the clocks go back at 2 AM on Nov 1
HOWS: list[How] = ["right", "right", "wrong", "unsure", "hint", "give-up"]


@pytest.fixture(scope="module")
def test_pack() -> Iterator[list[Path]]:
    yield [p for p in shipped_packs() if p.stem == "test"]
    grader.shutdown()
    cards.shutdown()


def dst_changes_after(moment: datetime) -> datetime:
    """The next instant New York's UTC offset changes (scanned by the hour, then minute)."""
    t = moment.astimezone(NY)
    for _ in range(24 * 400):
        later = t + timedelta(hours=1)
        if later.utcoffset() != t.utcoffset():
            while (t + timedelta(minutes=1)).utcoffset() == t.utcoffset():
                t += timedelta(minutes=1)
            return t + timedelta(minutes=1)
        t = later
    raise AssertionError("no DST change within 400 days")


class StudyMachine(RuleBasedStateMachine):
    pack: ClassVar[list[Path]] = []
    stats: ClassVar[dict[str, int]] = {}

    def __init__(self) -> None:
        super().__init__()
        self.tmp = Path(tempfile.mkdtemp(prefix="dev9-"))
        self.paths = ProfilePaths(self.tmp / "p")
        self.clock = FixedClock(START, tz=NY)
        self.storage: Storage | None = None
        self.svc: StudyService | None = None
        self.turn: Turn | None = None
        self.committed: set[int] = set()
        self.before_answer: dict[str, Any] | None = None  # for the undo check
        self.session_open = False
        self.on_screen: Turn | None = None
        self.pending = False

    # ------------------------------------------------------------ setup and teardown

    def _open(self, *, create: bool = False) -> None:
        self.storage = Storage.open(
            self.paths, pack_paths=self.pack, clock=self.clock, create=create
        )
        self.svc = StudyService(self.storage, checker=key_checker)

    @initialize()
    def setup(self) -> None:
        self._open(create=True)
        users = self.store.users
        users.set_setting("study.timezone", "America/New_York")
        for section in self.store.packs.sections():
            users.set_section_state(section.id, "learning")
        self._look()

    def teardown(self) -> None:
        if self.storage is not None:
            self.storage.close(backup=False)
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def store(self) -> Storage:
        assert self.storage is not None
        return self.storage

    @property
    def service(self) -> StudyService:
        assert self.svc is not None
        return self.svc

    def _count(self, name: str) -> None:
        self.stats[name] = self.stats.get(name, 0) + 1

    def _quietly(self, action: Callable[[], Any]) -> Any:
        """Run a step; a QueueError is the refusal the student sees, nothing else may escape."""
        try:
            return action()
        except QueueError:
            self._count("refused")
            return None

    def _on_screen(self) -> Turn | None:
        session = self.store.users.latest_open_session()
        if session is None or session.current is None:
            return None
        turn: Turn | None = self._quietly(self.service.current)
        return turn if turn is not None and turn.type == "problem" else None

    def _pending(self) -> bool:
        session = self.store.users.latest_open_session()
        return bool(session and session.current and session.current.get("pending"))

    def _look(self) -> None:
        """What is on screen now, for the rules' preconditions."""
        self.session_open = self.store.users.latest_open_session() is not None
        self.on_screen = self._on_screen()
        self.pending = self._pending()

    def can_answer(self) -> bool:
        turn = self.on_screen
        return (
            turn is not None
            and turn.problem is not None
            and turn.problem.kind != "example"
            and turn.result is None  # not answered yet (a rated flashcard has its result)
            and not self.pending
        )

    # ------------------------------------------------------------ rules

    def _final_ids(self) -> set[int]:
        with self.store.db.reading() as conn:
            return {int(r[0]) for r in conn.execute("SELECT id FROM attempt WHERE final = 1")}

    def _open_mode(self) -> str | None:
        session = self.store.users.latest_open_session()
        return None if session is None else str(Plan.from_json(session.plan).mode)

    @precondition(lambda self: not self.session_open)
    @rule(mode=st.sampled_from(["daily", "daily", "daily", "extra", "lighter"]))
    def start(self, mode: str) -> None:
        finals = self._final_ids()
        self.turn = self._quietly(lambda: self.service.start({"mode": mode}))
        if self._final_ids() != finals:
            self.before_answer = None
        self._count(f"start-{mode}")
        self._look()

    @precondition(lambda self: self.session_open)
    @rule(mode=st.sampled_from(["daily", "extra", "lighter"]))
    def start_again(self, mode: str) -> None:
        # Start with a session open resumes it when it is of that mode (QUE-16); another mode
        # grades the answer on screen and ends it first. Lighter over daily turns the open
        # session into a Lighter set (QUE-10; test_lighter_start_over_an_open_daily_session).
        key, same = current_key(self.store), self._open_mode() == mode
        finals = self._final_ids()
        self.turn = self._quietly(lambda: self.service.start({"mode": mode}))
        if same and self.turn is not None:
            assert current_key(self.store) == key
        if self._final_ids() != finals or not same:
            self.before_answer = None
        self._count("start-again")
        self._look()

    @precondition(lambda self: self.can_answer())
    @rule(how=st.sampled_from(HOWS))
    def answer(self, how: How) -> None:
        turn = self.on_screen
        assert turn is not None
        self.clock.advance(seconds=40)  # answering takes a student some time
        snapshot = progress(self.store)
        result = self._quietly(lambda: answer(self.service, self.store, turn, how))
        if result is not None:
            self.before_answer = snapshot  # what undo must bring back (QUE-15)
            self._count(f"answer-{how}")
        self._look()

    @precondition(lambda self: self.can_answer())
    @rule()
    def hint(self) -> None:
        self._quietly(self.service.hint)
        self._count("hint")
        self._look()

    @rule(how=st.sampled_from(HOWS))
    def study(self, how: How) -> None:
        """The natural next step: start, answer what is on screen, or continue."""
        if not self.session_open:
            self.start("daily")
        elif self.can_answer():
            self.answer(how)
        elif self.on_screen is not None:
            self.continue_()
        else:
            self.end()

    @rule(how=st.sampled_from(HOWS))
    def study_more(self, how: How) -> None:
        self.study(how)

    @rule(how=st.sampled_from(HOWS))
    def study_on(self, how: How) -> None:
        self.study(how)

    @precondition(lambda self: self.on_screen is not None)
    @rule()
    def continue_(self) -> None:
        self.clock.advance(seconds=5)
        was_pending = self.pending
        snapshot = progress(self.store)
        finals = self._final_ids()
        self.turn = self._quietly(self.service.next)
        if self._final_ids() != finals and not was_pending:
            self.before_answer = snapshot  # a worked example's "shown" attempt
        self._count("continue")
        self._look()

    @precondition(lambda self: self.session_open)
    @rule()
    def undo(self) -> None:
        before = progress(self.store)
        turn = self._quietly(self.service.undo)
        if turn is not None:
            after = progress(self.store)
            if (turn.message or "").startswith("Undone"):
                self._count("undo")
                if self.before_answer is not None:
                    assert after == self.before_answer  # exactly the state before the answer
                    self._count("undo-checked")
            else:
                assert after == before  # a refused undo changes nothing
        self.before_answer = None
        self._look()

    @precondition(lambda self: self.session_open)
    @rule()
    def end(self) -> None:
        self._quietly(self.service.end)
        self.before_answer = None
        self._count("end")
        self._look()

    @rule()
    def reopen(self) -> None:
        key = current_key(self.store)
        pending = self._pending()
        self.store.close(backup=False)
        self._open()
        assert attempt_ids(self.store) >= self.committed
        assert current_key(self.store) == key  # the open session resumes where it was
        assert self._pending() == pending
        self._count("reopen")
        self._look()

    @rule(
        kind=st.sampled_from(["minutes", "minutes", "days", "rollover", "dst"]),
        minutes=st.integers(1, 240),
        days=st.integers(1, 3),
    )
    def time_passes(self, kind: str, minutes: int, days: int) -> None:
        before = self._study_day()
        now = from_ms(self.clock.now_ms(), NY)
        if kind == "minutes":
            self.clock.advance(minutes=minutes)
        elif kind == "days":
            self.clock.advance(days=days)
        else:
            if kind == "rollover":
                edge = now.replace(hour=DEFAULT_ROLLOVER_HOUR, minute=0, second=0, microsecond=0)
                edge += timedelta(days=1) if edge <= now else timedelta(0)
            else:
                edge = dst_changes_after(now)
            self.clock.set(edge - timedelta(minutes=30))
            self._quietly(self.service.today)  # the app is in use as the change happens
            self.clock.set(edge + timedelta(minutes=30))
        if self._study_day() != before:
            self.before_answer = None  # a new study day runs its daily jobs first
        self._count(kind)
        self._look()

    def _study_day(self) -> str:
        return self.service.engine().days().day_of(self.clock.now_ms()).isoformat()

    # ------------------------------------------------------------ invariants

    @invariant()
    def committed_attempts_survive(self) -> None:
        if self.storage is None:
            return
        ids = attempt_ids(self.store)
        assert ids >= self.committed
        self.committed = ids

    @invariant()
    def due_dates_are_finite_and_after_the_last_review(self) -> None:
        if self.storage is None:
            return
        for record in (SkillState, FlashcardState):
            for row in self.store.users.raw_state_rows(record):
                for field in ("stability", "difficulty"):
                    value = row.get(field)
                    assert value is None or math.isfinite(value), row
                due, last = row.get("due_at"), row.get("last_review_at")
                if due is not None:
                    assert isinstance(due, int), row
                    assert last is None or due >= last, row

    @invariant()
    def memory_equals_a_replay_of_the_log(self) -> None:
        if self.storage is None:
            return
        assert Engine(self.store).recompute_memory().changed == ()


def run(examples: int, steps: int, *, pack: list[Path]) -> dict[str, int]:
    StudyMachine.pack = pack
    StudyMachine.stats = {}
    run_state_machine_as_test(
        StudyMachine,
        settings=settings(
            max_examples=examples,
            stateful_step_count=steps,
            deadline=None,
            database=None,
            derandomize=True,
            suppress_health_check=[HealthCheck.too_slow],
        ),
    )
    return dict(StudyMachine.stats)


def test_lighter_start_over_an_open_daily_session(test_pack: list[Path], tmp_path: Path) -> None:
    """Found by DEV-9: Lighter over a daily session whose new skill's worked example is on
    screen dropped that item from the plan and raised StorageError, leaving the session
    unresumable. The skill leaves with its example (QUE-10) and the session moves on."""
    clock = FixedClock(START, tz=NY)
    with Storage.open(
        ProfilePaths(tmp_path / "p"), pack_paths=test_pack, clock=clock, create=True
    ) as storage:
        for section in storage.packs.sections():
            storage.users.set_section_state(section.id, "learning")
        svc = StudyService(storage, checker=key_checker)
        daily = svc.start({"mode": "daily"})
        assert daily.type == "problem"
        lighter = svc.start({"mode": "lighter"})
        assert (lighter.session_id, lighter.mode) == (daily.session_id, "lighter")
        resumed = svc.resume()
        assert resumed is not None
        assert current_key(storage) is not None


def test_learning_answers_in_one_millisecond_replay_to_the_stored_memory(
    test_pack: list[Path], tmp_path: Path
) -> None:
    """Found by DEV-9: a skill graduating with its answers in one millisecond stored a
    difficulty its replay did not give (C3). Its events tie on target, time and rating, and
    each took the first (block start) annotation, so the replay kept only the last one."""
    clock = FixedClock(START, tz=NY)  # never moves: every answer at the same instant
    with Storage.open(
        ProfilePaths(tmp_path / "p"), pack_paths=test_pack, clock=clock, create=True
    ) as storage:
        for section in storage.packs.sections():
            storage.users.set_section_state(section.id, "learning")
        svc = StudyService(storage, checker=key_checker)
        turn = svc.next() if svc.start({"mode": "daily"}).type == "problem" else None
        while turn is not None and turn.type == "problem" and turn.problem is not None:
            if storage.users.skill_states().get("test.alg.arithmetic", None) is not None and (
                storage.users.skill_states()["test.alg.arithmetic"].stability is not None
            ):
                break
            answer(svc, storage, turn, "right")
            turn = svc.next()
        assert Engine(storage).recompute_memory().changed == ()


def test_dst_change_is_found() -> None:
    change = dst_changes_after(START)
    assert change.utcoffset() != (change - timedelta(minutes=1)).utcoffset()
    assert (change.month, change.day) == (11, 1)
    assert to_ms(change) > to_ms(START)


def test_study_state_machine_fast(test_pack: list[Path]) -> None:
    stats = run(20, 40, pack=test_pack)
    print(f"DEV-9 fast: {stats}")
    assert stats.get("reopen", 0) > 0
    assert sum(v for k, v in stats.items() if k.startswith("answer-")) > 0


@pytest.mark.slow
def test_study_state_machine_long(test_pack: list[Path]) -> None:
    stats = run(120, 80, pack=test_pack)
    print(f"DEV-9 long: {stats}")
    for name in ("reopen", "undo", "dst", "rollover", "days", "end"):
        assert stats.get(name, 0) > 0, (name, stats)
