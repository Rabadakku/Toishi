"""Bugs found by hand-testing the full build on the Mac (docs/backlog.md, "Hand test of the
full build", items 1-5): each test replays the Mac scenario."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from core.queue import StudyService
from core.queue.items import Plan
from tests.queue.helpers import World, answer, make_world, review_state

SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    """Every skill in review and due: the session's problems are review problems."""
    w = make_world(tmp_path, ("ca",), sections=2, skills=3, state="solid")
    now = w.clock.now_ms()
    w.storage.users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in SKILLS])
    yield w
    w.storage.close(backup=False)


def _card_on_screen(svc: StudyService) -> str:
    turn = svc.current()
    assert turn.problem is not None
    return turn.problem.card.id


def _redo_guaranteed(world: World, card_id: str) -> bool:
    cu = world.storage.users.card_user(card_id)
    assert cu is not None
    assert cu.redo_due_at is not None
    return cu.redo_guaranteed


# ---------------------------------------------------------------- 1: give-up is not "sure"


@pytest.mark.parametrize(
    "how",
    ["give-up", "give-up-after-a-wrong-try", "last-hint", "didnt-know-start"],
)
def test_1_a_miss_not_submitted_sure_is_never_a_confident_error(world: World, how: str) -> None:
    svc = world.service()
    svc.start()
    card = _card_on_screen(svc)
    if how == "last-hint":
        while True:
            if svc.hint().rating_effect == "again":
                break
        result = answer(svc, world.clock, correct=False)
        result = answer(svc, world.clock, correct=False) if result.solution is None else result
    elif how == "didnt-know-start":
        result = answer(svc, world.clock, correct=False)
        result = answer(svc, world.clock, correct=False) if result.solution is None else result
    else:
        if how == "give-up-after-a-wrong-try":
            assert answer(svc, world.clock, correct=False).solution is None  # "Not quite"
        result = svc.give_up({"active_ms": 20_000})
    assert result.solution is not None
    assert not result.solution.confident_error  # the Mac showed "You marked this one as sure"
    choice = "setup" if how == "didnt-know-start" else "cant_tell"
    diagnosis = svc.diagnose(choice, 0 if choice == "setup" else None)
    assert "sure" not in diagnosis.follow_up
    assert not _redo_guaranteed(world, card)
    reloaded = svc.current().result  # the solution after grading reads the engine's record
    assert reloaded is not None
    assert reloaded.solution is not None
    assert not reloaded.solution.confident_error


def test_1_a_miss_submitted_sure_is_a_confident_error_as_the_engine_recorded(world: World) -> None:
    svc = world.service()
    svc.start()
    card = _card_on_screen(svc)
    result = answer(svc, world.clock, correct=False)
    result = answer(svc, world.clock, correct=False) if result.solution is None else result
    assert result.solution is not None
    assert not result.solution.confident_error  # not graded yet: nothing recorded to show
    diagnosis = svc.diagnose("cant_tell")
    assert "sure" in diagnosis.follow_up
    assert _redo_guaranteed(world, card)
    reloaded = svc.current().result
    assert reloaded is not None
    assert reloaded.solution is not None
    assert reloaded.solution.confident_error


def test_1_a_miss_submitted_unsure_is_not_a_confident_error(world: World) -> None:
    svc = world.service()
    svc.start()
    card = _card_on_screen(svc)
    kw: dict[str, Any] = {"confidence": "unsure"}
    result = answer(svc, world.clock, correct=False, **kw)
    if result.solution is None:
        answer(svc, world.clock, correct=False, **kw)
    diagnosis = svc.diagnose("cant_tell")
    assert "sure" not in diagnosis.follow_up
    assert not _redo_guaranteed(world, card)


# ---------------------------------------------------------------- 2: "Your answer" after give-up


def test_2_give_up_after_a_wrong_try_keeps_that_try_as_your_answer(world: World) -> None:
    svc = world.service()
    svc.start()
    tried = answer(svc, world.clock, correct=False)
    assert tried.outcome == "retry"
    given = svc.give_up({"active_ms": 20_000})
    assert given.outcome == "incorrect"
    assert [p.read_as for p in given.verdicts] == ["0"]  # the Mac showed "No answer"
    reloaded = svc.current().result
    assert reloaded is not None
    assert [p.read_as for p in reloaded.verdicts] == ["0"]


def test_2_give_up_before_any_try_has_no_answer_to_show(world: World) -> None:
    svc = world.service()
    svc.start()
    given = svc.give_up({"active_ms": 20_000})
    assert given.verdicts == ()


# ---------------------------------------------------------------- 3, 4: a tiny pool, no example


def tiny_world(
    tmp_path: Path, *, tiers: tuple[int, ...] = (1, 2), example: bool = False, skills: int = 1
) -> World:
    """One section in Learning now whose skills have only `tiers` problems (one each) and,
    unless `example`, no worked example card: an imported or user-made deck's shape."""
    from core.model import Card, Course, PackInfo, Section, Skill, SolutionStep, Unit
    from core.storage import Storage, build_pack
    from core.storage.clock import FixedClock
    from core.storage.profiles import ProfilePaths
    from tests.queue.helpers import NY, START

    records: list[object] = [
        Course(id="tp", title="TP", ord=0),
        Unit(id="tp.u1", course_id="tp", title="Unit 1"),
        Section(id="tp.s1", unit_id="tp.u1", title="1", ord=1),
    ]
    ids = []
    for k in range(1, skills + 1):
        sid = f"tp.s1.k{k}"
        ids.append(sid)
        records.append(Skill(id=sid, name=f"Tiny skill {k}", section_id="tp.s1", exam_tier=3))
        if example:
            records.append(
                Card(id=f"{sid}.ex", kind="example", skill_id=sid, tier=1, question_md="Ex.")
            )
        for i, tier in enumerate(tiers):
            records.append(
                Card(
                    id=f"{sid}.p{i}",
                    skill_id=sid,
                    tier=tier,
                    answer_type="number",
                    answer="1",
                    question_md=f"Problem {i}.",
                    hints=("hint 1", "hint 2"),
                    solution=(
                        SolutionStep(number=1, skill_id=sid, label="Set up", body_md="x = 1"),
                    ),
                )
            )
    pack = tmp_path / "tiny.db"
    build_pack(pack, PackInfo(id="tiny", title="Tiny", version="1"), records)  # type: ignore[arg-type]
    clock = FixedClock(START, tz=NY)
    paths = ProfilePaths(tmp_path / "profile")
    storage = Storage.open(paths, pack_paths=[pack], clock=clock, create=True)
    storage.users.set_setting("study.timezone", "America/New_York")
    storage.users.set_section_state("tp.s1", "learning")
    return World(storage, clock, ids, ["tp"], ["tp.s1"], paths, [pack])


def _play(svc: StudyService, world: World, *, correct: bool = True) -> list[tuple[str, str]]:
    """Work through the session; (item kind, card id) per item served."""
    served: list[tuple[str, str]] = []
    turn = svc.start()
    while turn.type == "problem":
        assert turn.problem is not None
        served.append((turn.problem.kind, turn.problem.card.id))
        if turn.problem.kind == "problem":
            result = answer(svc, world.clock, correct=correct)
            if result.solution is None:  # "Not quite": the second try
                result = answer(svc, world.clock, correct=correct)
            if result.solution is not None and result.solution.needs_diagnosis:
                svc.diagnose("cant_tell")
        turn = svc.next()
    return served


def test_3_a_card_is_never_served_twice_in_a_study_day_and_a_tiny_pool_still_learns(
    tmp_path: Path,
) -> None:
    world = tiny_world(tmp_path, tiers=(1, 2), example=True)
    try:
        svc = world.service()
        served = _play(svc, world)
        problems = [card for kind, card in served if kind == "problem"]
        assert problems  # the Mac served p0, p1, p0, p1
        assert len(problems) == len(set(problems))
        state = world.storage.users.skill_state("tp.s1.k1")
        assert state is not None
        assert state.level == "learned"  # min(3, 2 distinct problems) correct in a row
        again = _play(svc, world)  # "Study more" the same day: nothing left to serve
        assert [c for k, c in again if k == "problem"] == []
    finally:
        world.storage.close(backup=False)


@pytest.mark.parametrize("tiers", [(1,), (1, 2)])
def test_3_the_reinforcement_problem_after_a_miss_is_another_card_or_skipped(
    tmp_path: Path, tiers: tuple[int, ...]
) -> None:
    world = tiny_world(tmp_path, tiers=tiers, example=True, skills=8)  # room for the gap
    try:
        _reinforcement_after_a_miss(world)
    finally:
        world.storage.close(backup=False)


def test_3_the_reinforcement_problem_in_a_large_pool_is_another_card(world: World) -> None:
    _reinforcement_after_a_miss(world)


def _reinforcement_after_a_miss(world: World) -> None:
    users = world.storage.users
    now = world.clock.now_ms()
    for section in world.sections:
        users.set_section_state(section, "solid")
    users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in world.skills])
    svc = world.service()
    turn = svc.start()
    assert turn.session_id is not None
    session_id = turn.session_id
    served: list[str] = []
    missed: str | None = None
    while turn.type == "problem":
        assert turn.problem is not None
        served.append(turn.problem.card.id)
        if turn.problem.kind == "problem":
            wrong = missed is None
            result = answer(svc, world.clock, correct=not wrong)
            if result.solution is None:
                result = answer(svc, world.clock, correct=not wrong)
            if wrong:
                missed = turn.problem.card.id
                svc.diagnose("cant_tell")
        turn = svc.next()
    assert missed is not None
    assert served.count(missed) == 1  # the Mac's "fresh problem" was the missed one
    assert len(served) == len(set(served))
    session = users.session(session_id)
    assert session is not None
    plan = Plan.from_json(session.plan)
    (rf,) = [i for i in plan.items if i.purpose == "reinforcement"]
    refs = world.storage.packs.card_refs(skill_id=rf.skill_id)
    pool = sum(1 for r in refs if r.kind == "problem")
    # A one-problem pool skips the slot gracefully; a bigger one serves another card.
    assert rf.status == ("skipped" if pool == 1 else "done")


def test_3_the_library_flags_a_skill_whose_pool_is_too_small(tmp_path: Path) -> None:
    from core.engine import Engine

    world = tiny_world(tmp_path, tiers=(1, 2, 3), skills=1)
    try:
        assert Engine(world.storage).small_learning_pools() == {"tp.s1.k1": 2}
    finally:
        world.storage.close(backup=False)


def test_4_with_no_example_card_a_new_skill_starts_with_a_tier_1_problem_shown_solved(
    tmp_path: Path,
) -> None:
    world = tiny_world(tmp_path, tiers=(1, 1, 2, 2), example=False)
    try:
        svc = world.service()
        turn = svc.start()
        assert turn.problem is not None
        assert turn.problem.kind == "example"  # the Mac went straight to a problem
        card = turn.problem.card
        assert card.kind == "problem"
        assert card.solution_md is not None
        assert "x = 1" in card.solution_md
        assert "**Answer:** 1" in card.solution_md
        shown = card.id
        assert world.storage.packs.card(shown).tier == 1  # type: ignore[union-attr]
        turn = svc.next()  # read it, continue: shown, never graded
        (example_attempt,) = world.storage.users.attempts(skill_id="tp.s1.k1")
        assert example_attempt.verdict == "shown"
        assert example_attempt.rating is None
        assert turn.problem is not None
        assert turn.problem.kind == "problem"
        assert turn.problem.card.id != shown  # not served again as a problem today
    finally:
        world.storage.close(backup=False)


# ---------------------------------------------------------------- 5: the summary


def test_5_the_summary_says_more_learning_problems_are_ready_today(tmp_path: Path) -> None:
    world = make_world(tmp_path, ("ca",), sections=1, skills=3)  # new skills, Learning now
    try:
        svc = world.service()
        turn = svc.start()
        n = 0
        while turn.type == "problem":
            assert turn.problem is not None
            if turn.problem.kind == "problem":
                result = answer(svc, world.clock, correct=n % 2 == 1)  # no run of three
                n += 1
                if result.solution is None:
                    result = answer(svc, world.clock, correct=False)
                if result.solution is not None and result.solution.needs_diagnosis:
                    svc.diagnose("cant_tell")
            turn = svc.next()
        assert turn.summary is not None
        home = svc.today()
        assert home.problems > 0  # Home offers more today (the learning phase goes on) ...
        assert turn.summary.ready_today == home.problems  # ... and the summary says so
        assert len({m.skill_id for m in turn.summary.misses}) < len(turn.summary.misses)
    finally:
        world.storage.close(backup=False)
