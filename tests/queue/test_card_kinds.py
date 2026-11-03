"""Every card kind through the wave 2 session on the Test pack: multi-part problems (tries and
verdicts per part, an observation per part), self-graded problems (Show solution first, then
rubric ticks), cloze cards (one blank a day, like Anki), flashcards (FSRS per card, I5) and
the kinds the planner no longer serves (find-the-error, which-method)."""

from collections import Counter
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.packs import shipped_packs
from core import cards, grader
from core.engine import Engine, FsrsAdapter, Memory
from core.engine.fsrs_adapter import DEFAULT_PARAMS_ID
from core.grader import AnswerSpec, GradeResult, Status
from core.model import CourseSetup, FlashcardState
from core.practice import PracticeEngine
from core.queue import Plan, StudyService, Turn
from core.queue.flashcards import FLASHCARD_REWRITE
from core.storage import Storage
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths
from tests.queue.helpers import NY, Script, World, make_world
from tests.storage.study_driver import key_checker

START = datetime(2026, 9, 1, 12, tzinfo=NY)
COURSE = "Test Course"
QUAD = "test.alg.quadratic-solve"
VERTEX = "test.alg.vertex"
PARABOLA = "test.quad.parabola.001"
EXPLAIN = "test.linear.explain.001"
CLOZE = "test.linear.cloze.001"
TIMING = {"active_ms": 30_000, "solve_ms": 25_000, "entry_ms": 3_000}
RIGHT = {"a": "-1, 1", "b": "(0, -1)", "c": "a"}


def matching_checker(raw: str, spec: AnswerSpec, source: Any) -> GradeResult:
    """key_checker, and a known wrong answer matched with its feedback (like the grader)."""
    known = next((w for w in spec.wrong if w.answer == raw.strip()), None)
    if known is not None:
        return GradeResult(Status.INCORRECT, raw, known.feedback or "", matched_wrong=known)
    return key_checker(raw, spec, source)


@pytest.fixture(scope="module")
def pack() -> Iterator[list[Path]]:
    yield [p for p in shipped_packs() if p.stem == "test"]
    grader.shutdown()
    cards.shutdown()


@pytest.fixture
def storage(tmp_path: Path, pack: list[Path]) -> Iterator[Storage]:
    clock = FixedClock(START, tz=NY)
    opened = Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=pack, clock=clock, create=True)
    users = opened.users
    users.set_setting("study.timezone", "America/New_York")
    for section in opened.packs.sections():
        users.set_section_state(section.id, "learning")
    users.set_course_setup(CourseSetup(course_id=COURSE, start=START.date()))
    yield opened
    opened.close(backup=False)


def clock_of(storage: Storage) -> FixedClock:
    clock = storage.db.clock
    assert isinstance(clock, FixedClock)
    return clock


def parts(**values: str) -> dict[str, Any]:
    """A submission of these parts' answers."""
    return {"answers": [{"part": k, "value": v} for k, v in values.items()], "timing": TIMING}


def serving(storage: Storage, card: str, role: str = "growth") -> tuple[StudyService, Turn]:
    svc = StudyService(storage, checker=matching_checker)
    script = Script(svc, course=COURSE)
    script.problem(card, role=role)
    turn = svc.start()
    assert turn.problem is not None
    assert turn.problem.card.id == card.split("#")[0]
    clock_of(storage).advance(seconds=40)
    return svc, turn


# ---------------------------------------------------------------- multi-part problems


def test_each_part_is_retried_until_right_and_counts_on_its_own_first_try(
    storage: Storage,
) -> None:
    svc, turn = serving(storage, f"{PARABOLA}#a")
    assert turn.problem is not None
    assert [p.label for p in turn.problem.card.parts] == ["a", "b", "c"]
    first = svc.submit(parts(a="1", b=RIGHT["b"], c=RIGHT["c"]))  # a: a known wrong answer
    assert first.outcome == "retry"
    assert (first.can_retry, first.first_try_counted) == (True, True)
    by_part = {p.part: p for p in first.verdicts}
    assert (by_part["a"].status, by_part["a"].final, by_part["a"].tries_used) == (
        "incorrect",
        False,
        1,
    )
    assert (by_part["a"].message, by_part["a"].feedback, by_part["a"].wrong_step) == (
        "",
        None,
        None,
    )
    assert by_part["b"].final
    assert by_part["c"].final
    users = storage.users
    (tried,) = users.attempts()
    assert (tried.part, tried.final, tried.attempt_number) == ("a", False, 1)
    assert tried.matched_wrong == 0  # part a's own known wrong answer
    clock_of(storage).advance(seconds=20)
    second = svc.submit(parts(a=RIGHT["a"]))  # only the open part is checked again
    assert second.outcome == "correct"
    assert second.first_try_counted is False
    assert {p.part: p.tries_used for p in second.verdicts} == {"a": 2, "b": 1, "c": 1}
    svc.next()
    (final,) = [a for a in users.attempts(card_id=PARABOLA) if a.final]
    assert [(p["label"], p["attempts"], p["correct"]) for p in final.extra["parts"]] == [
        ("a", 2, True),
        ("b", 1, True),
        ("c", 1, True),
    ]
    observed = {o.problem.problem_id: o.correct for o in svc.practice.observations()}
    assert observed == {f"{PARABOLA}#a": False, f"{PARABOLA}#b": True, f"{PARABOLA}#c": True}
    # The plan's item was part a: its first try was the miss that counts.
    (_, served), *_ = svc.practice.served(START.date())
    assert served.correct is False


def test_giving_up_a_multi_part_problem_gives_up_its_open_parts(storage: Storage) -> None:
    svc, _ = serving(storage, f"{PARABOLA}#a")
    svc.submit(parts(a=RIGHT["a"], c=RIGHT["c"]))  # b left open
    result = svc.give_up(TIMING)
    assert result.outcome == "incorrect"
    assert result.first_try_counted is False  # parts were answered before
    svc.next()
    (final,) = [a for a in storage.users.attempts(card_id=PARABOLA) if a.final]
    by_label = {p["label"]: p for p in final.extra["parts"]}
    assert by_label["b"]["gave_up"]
    assert not by_label["a"]["gave_up"]
    observed = {o.problem.problem_id: (o.correct, o.aided) for o in svc.practice.observations()}
    assert observed[f"{PARABOLA}#b"] == (False, True)  # given up before any answer: aided
    assert observed[f"{PARABOLA}#a"] == (True, False)


# ---------------------------------------------------------------- self-graded problems


def test_a_self_graded_problem_shows_its_solution_first_then_is_graded_by_rubric(
    storage: Storage,
) -> None:
    svc, turn = serving(storage, EXPLAIN)
    assert turn.problem is not None
    assert turn.problem.card.self_graded
    shown = svc.show_solution()  # allowed before any try: it is how these are graded
    assert shown.outcome == "self-grade"
    assert shown.solution is not None
    card = storage.packs.card(EXPLAIN)
    assert card is not None
    assert shown.solution.rubric == card.rubric
    result = svc.submit({"rubric_ticked": len(card.rubric), "timing": TIMING})
    assert result.outcome == "correct"
    assert result.first_try_counted
    svc.next()
    (row,) = storage.users.attempts()
    assert (row.verdict, row.extra["correct"], row.attempt_number) == ("self", True, 1)
    assert row.valid_minutes is None  # a self-graded time is not a solving time
    (obs,) = svc.practice.observations()
    assert (obs.correct, obs.aided) == (True, False)


def test_a_rubric_with_two_steps_missed_is_a_miss(storage: Storage) -> None:
    svc, _ = serving(storage, EXPLAIN)
    svc.show_solution()
    assert svc.submit({"rubric_ticked": 0, "timing": TIMING}).outcome == "incorrect"
    svc.next()
    (obs,) = svc.practice.observations()
    assert obs.correct is False


# ---------------------------------------------------------------- a day on the Test pack


def study(svc: StudyService, storage: Storage, seen: list[tuple[str, str, int | None]]) -> Turn:
    """Answer everything today: problems right (multi-part and self-graded included)."""
    turn = svc.start()
    for _ in range(200):
        if turn.type != "problem" or turn.problem is None:
            return turn
        p = turn.problem
        seen.append((p.kind, p.card.kind, p.card.cloze))
        clock_of(storage).advance(seconds=40)
        if p.kind == "example":
            turn = svc.next()
            continue
        if p.kind == "flashcard":
            assert svc.rate_flashcard(3).outcome == "recorded"
            turn = svc.next()
            continue
        card = storage.packs.card(p.card.id)
        assert card is not None
        if p.card.self_graded:
            svc.show_solution()
            grade = (
                {"rubric_ticked": len(card.rubric)} if card.rubric else {"self_grade": "matched"}
            )
            result = svc.submit({**grade, "timing": TIMING})
        elif card.parts:
            result = svc.submit(parts(**RIGHT))
        else:
            value = card.answer or ""
            if card.answer_type == "text":
                value = value.split(";")[0].strip()
            result = svc.submit({"answers": [{"value": value}], "timing": TIMING})
            if result.outcome != "correct":
                result = svc.give_up(TIMING)
        assert result.outcome in ("correct", "incorrect"), (p.card.id, result)
        turn = svc.next()
    raise AssertionError("the day did not end")


def test_a_day_serves_cloze_blanks_one_by_one_and_never_find_error_or_method_items(
    storage: Storage,
) -> None:
    svc = StudyService(storage, checker=key_checker)
    seen: list[tuple[str, str, int | None]] = []
    end = study(svc, storage, seen)
    assert end.type == "summary"
    kinds = Counter(card_kind for _, card_kind, _ in seen)
    assert {"problem", "example"} <= set(kinds)
    assert "find-error" not in kinds
    assert "method" not in kinds
    assert ("flashcard", "cloze", 1) in seen  # blank c1 today ...
    assert ("flashcard", "cloze", 2) not in seen
    assert svc.practice.state() == PracticeEngine(storage).state()  # C3
    assert Engine(storage).recompute_memory().changed == ()  # flashcard memory, C3
    clock_of(storage).set(START + timedelta(days=1))
    seen2: list[tuple[str, str, int | None]] = []
    study(svc, storage, seen2)
    assert ("flashcard", "cloze", 2) in seen2  # ... and c2 the next study day, like Anki
    assert {(f.card_id, f.ord) for f in storage.users.flashcard_states() if f.card_id == CLOZE} == {
        (CLOZE, 0),
        (CLOZE, 1),
    }


# ---------------------------------------------------------------- flashcards (I5)


SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]


@pytest.fixture
def flash(tmp_path: Path) -> Iterator[World]:
    """One course, set up today, with a flashcard per skill."""
    w = make_world(tmp_path, ("ca",), sections=2, skills=3, flashcards=True)
    yield w
    w.storage.close(backup=False)


def due(card: str, now: int, **kw: Any) -> FlashcardState:
    values: dict[str, Any] = {
        "fsrs_state": 2,
        "stability": 3.0,
        "difficulty": 5.0,
        "last_review_at": now - 5 * 86_400_000,
        "due_at": now - 3_600_000,
        "reps": 2,
    } | kw
    return FlashcardState(card_id=card, **values)


def flashcard_turn(svc: StudyService, turn: Turn, w: World) -> Turn:
    """Answer problems until a flashcard is on screen."""
    while turn.problem is not None and turn.problem.kind != "flashcard":
        w.clock.advance(seconds=30)
        if turn.problem.kind == "problem":
            svc.submit({"answers": [{"value": "1"}], "timing": TIMING})
        turn = svc.next()
    return turn


def plan_of(w: World) -> Plan:
    session = w.storage.users.latest_open_session()
    assert session is not None
    return Plan.from_json(session.plan)


def test_flashcards_of_introduced_skills_sit_between_the_problems(flash: World) -> None:
    svc = flash.service()
    svc.start()
    items = plan_of(flash).items
    kinds = [i.kind for i in items]
    assert "flashcard" in kinds
    assert "problem" in kinds
    assert kinds.count("flashcard") == len(SKILLS)  # every skill is introduced today


def test_a_leech_is_not_served_and_the_8th_lapse_asks_for_a_rewrite(flash: World) -> None:
    users = flash.storage.users
    now = flash.clock.now_ms()
    users.apply([due("ca.s1.k1.fc", now, fsrs_state=3, lapses=8, leech=True, stability=0.5)])
    users.apply([due("ca.s1.k2.fc", now, stability=5.0, lapses=7, reps=20)])
    svc = flash.service()
    assert svc.today().flashcards_to_rewrite == 1
    turn = svc.start()
    assert "ca.s1.k1.fc" not in {i.card_id for i in plan_of(flash).items}
    while turn.problem is not None and turn.problem.card.id != "ca.s1.k2.fc":
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        elif turn.problem.kind == "problem":
            flash.clock.advance(seconds=30)
            svc.submit({"answers": [{"value": "1"}], "timing": TIMING})
        turn = svc.next()
    assert turn.problem is not None
    result = svc.rate_flashcard(1)
    assert result.message == FLASHCARD_REWRITE
    state = users.flashcard_state("ca.s1.k2.fc", 0)
    assert state is not None
    assert (state.lapses, state.leech) == (8, True)
    assert not [i for i in plan_of(flash).pending if i.card_id == "ca.s1.k2.fc"]  # no re-show


def test_the_daily_flashcard_limits_count_what_was_done_today(flash: World) -> None:
    users = flash.storage.users
    users.set_setting("daily.flashcards", 4)
    now = flash.clock.now_ms()
    users.apply([due(f"{k}.fc", now) for k in SKILLS])
    svc = flash.service()
    turn = svc.start()
    assert sum(1 for i in plan_of(flash).items if i.kind == "flashcard") == 4
    done = 0
    while turn.problem is not None and done < 3:
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
            done += 1
        elif turn.problem.kind == "problem":
            flash.clock.advance(seconds=30)
            svc.submit({"answers": [{"value": "1"}], "timing": TIMING})
        turn = svc.next()
    svc.end()
    svc.start()  # a second session the same day: the limit less the three done
    assert sum(1 for i in plan_of(flash).items if i.kind == "flashcard") == 1


def test_new_flashcards_respect_their_own_daily_limit(flash: World) -> None:
    flash.storage.users.set_setting("daily.new_flashcards", 2)
    svc = flash.service()
    svc.start()
    assert sum(1 for i in plan_of(flash).items if i.kind == "flashcard") == 2


def test_a_missed_flashcard_comes_back_5_items_later_with_the_same_day_update(
    flash: World,
) -> None:
    svc = flash.service()
    turn = flashcard_turn(svc, svc.start(), flash)
    assert turn.problem is not None
    missed, key = turn.problem.card.id, turn.problem.item_key
    svc.rate_flashcard(1)
    plan = plan_of(flash)
    order = [i.key for i in plan.items if i.status != "skipped"]
    (reshow,) = [i for i in plan.pending if i.card_id == missed]
    assert (reshow.anchor, reshow.purpose) == (key, "relearn")
    assert order.index(reshow.key) - order.index(key) > 5 or reshow.key == order[-1]
    first = flash.storage.users.flashcard_state(missed, 0)
    assert first is not None
    turn = svc.next()
    while turn.problem is not None and turn.problem.item_key != reshow.key:
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        elif turn.problem.kind == "problem":
            flash.clock.advance(seconds=30)
            svc.submit({"answers": [{"value": "1"}], "timing": TIMING})
        turn = svc.next()
    assert turn.problem is not None
    svc.rate_flashcard(3)
    second = flash.storage.users.flashcard_state(missed, 0)
    assert second is not None
    memory = Memory(first.stability or 0, first.difficulty or 0, first.last_review_at or 0)
    same = FsrsAdapter().review(memory, 3, second.last_review_at or 0, same_day=True)
    assert second.stability == pytest.approx(same.stability)
    assert second.lapses == 0


def test_a_flashcard_uses_the_flashcard_parameters_and_no_problem_is_fsrs_rated(
    flash: World,
) -> None:
    svc = flash.service()
    turn = flashcard_turn(svc, svc.start(), flash)
    assert turn.problem is not None
    svc.rate_flashcard(3)
    rows = flash.storage.users.attempts()
    (card,) = [a for a in rows if a.card_kind == "flashcard"]
    assert card.params_id == DEFAULT_PARAMS_ID
    assert card.role is None  # flashcards are not the planner's
    assert all(a.rating is None for a in rows if a.card_kind == "problem")
    events = flash.storage.users.review_events()
    assert {e.target_kind for e in events} == {"flashcard"}


def test_without_a_setup_flashcards_follow_the_library(tmp_path: Path) -> None:
    w = make_world(
        tmp_path, ("ca",), sections=2, skills=3, flashcards=True, state="off", setup=False
    )
    try:
        now = w.clock.now_ms()
        w.storage.users.apply([due("ca.s1.k1.fc", now)])
        svc = w.service()
        assert svc.today().flashcards == 0  # an Off section's cards wait
        w.storage.users.set_section_state("ca.s1", "solid")
        assert svc.today().flashcards == 1  # the one reviewed before; new ones need a schedule
    finally:
        w.storage.close(backup=False)
