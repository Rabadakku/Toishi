"""core/practice/engine.py: the cached learner state, parameters, plans, calibration, refits."""

import threading
from collections.abc import Iterator
from dataclasses import fields, replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from core.learner.types import ProblemSpec, SharedParams
from core.model import CourseSetup, Exam
from core.plan.types import CourseSettings, DayPlan, WorkItem
from core.practice import (
    GROWTH_BANDS,
    PracticeEngine,
    build_observations,
    merge,
    params_from_json,
    params_json,
    plan_settings,
)
from core.practice.engine import exam_spec
from core.storage.clock import to_ms
from tests.practice.helpers import COURSE, NY, S1, S2, START, World, answer, make_world, set_up


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path)
    yield w
    w.storage.close(backup=False)


def replayed(engine: PracticeEngine) -> object:
    """The state a full replay of the stored log gives (C3)."""
    rows = engine.storage.users.attempts()
    observations = build_observations(rows, engine.catalog())
    state, _ = engine.model().replay(engine.params(), observations)
    return state


def test_the_state_follows_the_log_incrementally_and_equals_a_replay(world: World) -> None:
    engine = PracticeEngine(world.storage)
    empty = engine.state()
    assert empty.components == {}
    answer(world, "c.limit.t1.v0")
    first = engine.state()
    assert first is empty  # the same cached state, updated in place
    assert first.components["c.limit"].attempts == 1
    answer(world, "c.limit.t2.v0", correct=False, final=False, presentation="p2")
    answer(world, "c.limit.t2.v0", attempt_number=2, presentation="p2")  # not an observation
    answer(world, "c.squeeze.t1.v1", correct=False, verdict="gave-up")
    state = engine.state()
    assert state == replayed(engine)
    assert len(engine.observations()) == 3


def test_an_undo_or_a_void_replays_the_log(world: World) -> None:
    engine = PracticeEngine(world.storage)
    for card_id in ("c.limit.t1.v0", "c.limit.t1.v1", "c.squeeze.t1.v0"):
        answer(world, card_id)
    before = engine.state()
    world.storage.users.undo_last_answer()
    after = engine.state()
    assert after is not before
    assert after == replayed(engine)
    assert len(engine.observations()) == 2
    assert "c.squeeze" not in after.components


def test_record_returns_the_updates_of_a_committed_row(world: World) -> None:
    engine = PracticeEngine(world.storage)
    engine.state()
    row = answer(world, "c.limit.t2.v1", correct=False, matched_wrong=0)
    (update,) = engine.record(row.id or 0)
    assert update.attempt_id == row.id
    blame = dict(update.blame)
    assert blame["alg.factor"] > blame["c.limit"]  # the matched wrong line names alg.factor
    shown = answer(world, "c.limit.ex", verdict="shown")
    assert engine.record(shown.id or 0) == ()


def test_the_prior_is_written_once_and_a_reset_is_a_new_current_version(world: World) -> None:
    engine = PracticeEngine(world.storage)
    users = world.storage.users
    assert engine.params() == SharedParams()
    assert engine.params() == SharedParams()
    (prior,) = users.learner_param_history()
    assert (prior.version, prior.source, prior.current) == ("prior", "prior", True)
    answer(world, "c.limit.t1.v0")
    before = engine.state()
    world.clock.advance(minutes=1)
    reset = engine.reset_params()
    assert (reset.source, reset.current) == ("reset", True)
    assert reset.version.startswith("reset-")
    assert engine.params().version == reset.version
    assert replace(engine.params(), version="prior") == SharedParams()
    after = engine.state()
    assert after is not before  # a new version: the log replays under it
    assert after.params.version == reset.version
    assert [p.version for p in users.learner_param_history()] == ["prior", reset.version]


def test_parameters_round_trip_through_json() -> None:
    params = replace(SharedParams(), slip=0.031, calib_a=(0.1, -0.2, 0.0, 0.3, 0.0), tau=0.5)
    back = params_from_json(params_json(params), "v7")
    assert back == replace(params, version="v7")
    assert params_from_json({"slip": 0.05, "unknown": 1}, "v8") == replace(
        SharedParams(), slip=0.05, version="v8"
    )


def test_a_course_is_planned_only_once_it_is_set_up(world: World) -> None:
    engine = PracticeEngine(world.storage)
    today, now = world.today(), world.now()
    assert engine.plan_day(today, now).items == ()
    set_up(world, start=today)
    plan = engine.plan_day(today, now)
    assert set(plan.plans) == {COURSE}
    skills = {p.item.skill_id for p in plan.items}
    assert {"c.limit", "c.squeeze"} <= skills  # section 1.1 starts today
    assert "c.lhopital" not in skills  # section 1.2 a week later (4 h at 4 h a week)
    assert all(p.course_id == COURSE for p in plan.items)
    first = plan.items[0].item
    assert (first.role, first.problem, first.example_card) == ("new", None, "c.limit.ex")
    assert plan.minutes == pytest.approx(sum(p.item.expected_minutes for p in plan.items))
    assert plan.hours_basis == "standard"
    assert plan.standard_hours == pytest.approx(8.0)  # 2 h per weekly class hour
    later = engine.plan_day(today + timedelta(days=7), now + 7 * 86_400_000)
    assert "c.lhopital" in {p.item.skill_id for p in later.items}


def test_a_course_without_pace_data_reports_no_standard_hours(tmp_path: Path) -> None:
    w = make_world(tmp_path, pace=False)
    try:
        set_up(w, start=w.today())
        plan = PracticeEngine(w.storage).plan_day(w.today(), w.now())
        assert "c.lhopital" in {p.item.skill_id for p in plan.items}  # everything on day one
        assert (plan.hours_basis, plan.standard_hours, plan.hours_to_keep_pace) == (
            "none",
            None,
            None,
        )
    finally:
        w.storage.close(backup=False)


def test_statuses_and_certified_milestones(world: World) -> None:
    engine = PracticeEngine(world.storage)
    set_up(world, start=world.today())
    statuses = {s.skill_id: s for s in engine.statuses(COURSE, world.today(), world.now())}
    assert statuses["c.limit"].state == "new"
    assert statuses["c.lhopital"].state == "not-introduced"
    assert [m.name for m in statuses["c.limit"].milestones] == ["M1", "M2", "M3"]
    assert engine.certified(COURSE, world.today(), world.now(), statuses["c.limit"]) == [
        False,
        False,
        False,
    ]
    assert engine.statuses("Other", world.today(), world.now()) == ()  # not set up


def problem(skill: str, n: int = 0) -> ProblemSpec:
    return ProblemSpec(f"{skill}.{n}", f"{skill}.{n}", None, skill, (skill,), 2, 2, 3.0)


def item(skill: str, *, block: bool = False, n: int = 0) -> WorkItem:
    return WorkItem(
        skill, "new" if block else "growth", problem(skill, n), None, 3.0, 1, block=block
    )


def test_courses_merge_with_every_block_first_then_round_robin() -> None:
    day = date(2026, 9, 7)
    a = DayPlan(day, (item("a1", block=True), item("a2"), item("a3")), 9.0, None, None)
    b = DayPlan(
        day, (item("b1", block=True), item("b1", block=True, n=1), item("b2")), 9, None, None
    )
    c = DayPlan(day, (item("c1"), item("c2")), 6.0, None, None)
    merged = merge({"A": a, "B": b, "C": c}, ["A", "B", "C"])
    assert [(p.course_id, p.item.skill_id) for p in merged] == [
        ("A", "a1"),
        ("B", "b1"),
        ("B", "b1"),
        ("A", "a2"),
        ("B", "b2"),
        ("C", "c1"),
        ("A", "a3"),
        ("C", "c2"),
    ]


def test_settings_come_from_the_setup_and_the_courses_exams(world: World) -> None:
    users = world.storage.users
    engine = PracticeEngine(world.storage)
    exam_at = to_ms(START.replace(day=28, hour=10))
    users.add_exam(
        Exam(course_id=COURSE, name="Midterm", at=exam_at, sections=(S1,), target_recall=0.85)
    )
    users.add_exam(Exam(course_id="Other", name="Elsewhere", at=exam_at))
    users.add_exam(Exam(name="No course", at=exam_at, sections=(S2,)))
    assert engine.settings(COURSE) is None
    users.set_course_setup(
        CourseSetup(
            course_id=COURSE,
            aligned_deck=S2,
            aligned_day=date(2026, 9, 10),
            pace_factor=1.25,
            accuracy_target=0.85,
            target_tier=3,
            end_day=date(2026, 12, 15),
            growth_band="hard",
        )
    )
    settings = engine.settings(COURSE)
    assert settings is not None
    assert settings.aligned == (S2, date(2026, 9, 10))
    assert (settings.pace_factor, settings.accuracy_target, settings.target_tier) == (1.25, 0.85, 3)
    assert settings.end == date(2026, 12, 15)
    assert [(e.day, e.scope_decks, e.target) for e in settings.exams] == [
        (date(2026, 9, 28), (S1,), 0.85),
        (date(2026, 9, 28), (S2,), None),
    ]
    if "growth_band" in {f.name for f in fields(CourseSettings)}:  # the planner's wave 2
        assert getattr(settings, "growth_band", None) == GROWTH_BANDS["hard"]


def test_an_alignment_on_a_section_the_course_lost_falls_back_to_the_start() -> None:
    setup = CourseSetup(
        course_id="c", start=date(2026, 9, 1), aligned_deck="gone", aligned_day=date(2026, 9, 2)
    )
    assert plan_settings(setup, (), sections=["kept"]).aligned is None
    assert plan_settings(setup, (), sections=["gone"]).aligned == ("gone", date(2026, 9, 2))


def test_exam_days_are_study_days(world: World) -> None:
    engine = PracticeEngine(world.storage)
    late = Exam(id=1, name="Late", at=to_ms(START.replace(day=9, hour=2)))  # 2 AM: the day before
    spec = exam_spec(late, engine.days())
    assert spec is not None
    assert spec.day == date(2026, 9, 8)
    assert START.tzinfo is NY


def test_calibration_bins_every_first_try(world: World) -> None:
    engine = PracticeEngine(world.storage)
    answer(world, "c.limit.t1.v0")
    answer(world, "c.limit.t1.v1", correct=False)
    world.clock.advance(days=3)
    answer(world, "c.limit.t3.v0")
    answer(world, "alg.factor.t2.v0")
    cal = engine.calibration()
    # The labels reach the Model page as they are: plain words
    assert [b.label for b in cal.by_tier] == ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]
    assert [b.n for b in cal.by_tier] == [2, 1, 1, 0, 0]
    assert [b.label for b in cal.by_gap] == [
        "First practice",
        "Under a day",
        "1 to 7 days",
        "8 to 30 days",
        "Over 30 days",
    ]
    assert [b.n for b in cal.by_gap] == [2, 1, 1, 0, 0]
    # c.limit's problems also use alg.factor, a background component; the factoring problem
    # has no course component at all and counts as one
    assert [b.label for b in cal.by_components] == ["1 skill", "2 skills", "3 or more skills"]
    assert [b.n for b in cal.by_components] == [4, 0, 0]
    tier1 = cal.by_tier[0]
    assert tier1.observed == 0.5
    assert 0.0 < tier1.predicted < 1.0


def test_refits_are_recorded_and_adopted_only_on_held_out_evidence(world: World) -> None:
    engine = PracticeEngine(world.storage)
    for n in range(6):
        answer(world, f"c.limit.t1.v{n % 3}", correct=n % 3 != 0)
    assert not engine.refit_due()  # the first refit waits for 150 first tries
    assert engine.refit() is None
    outcome = engine.refit(force=True)  # Refit now
    assert outcome is not None
    record = outcome.record
    assert (record.source, record.current) == ("refit", False)  # 2 held out: nothing adopted
    report = record.report or {}
    assert report["attempts"] == 6
    assert report["adopted"] is False
    assert [b["name"] for b in report["blocks"]] == ["accuracy", "time"]
    assert engine.params().version == "prior"
    assert engine.last_refit() == record


def test_a_refit_never_overrides_a_reset_made_meanwhile(world: World) -> None:
    engine = PracticeEngine(world.storage)
    answer(world, "c.limit.t1.v0")
    started = threading.Event()

    class Writing:
        def __enter__(self) -> None:
            if not started.is_set():
                started.set()
                engine.reset_params()  # a reset lands while the fit ran

        def __exit__(self, *exc: object) -> None:
            pass

    outcome = engine.refit(force=True, writing=Writing)
    assert outcome is not None
    assert not outcome.record.current
    assert world.storage.users.learner_params() is not None
    assert world.storage.users.learner_params().source == "reset"  # type: ignore[union-attr]


def test_concurrent_readers_see_one_consistent_state(world: World) -> None:
    engine = PracticeEngine(world.storage)
    for n in range(4):
        answer(world, f"c.limit.t1.v{n % 3}")
    results: list[int] = []
    errors: list[BaseException] = []

    def read() -> None:
        try:
            results.append(len(engine.observations()))
        except BaseException as error:
            errors.append(error)

    threads = [threading.Thread(target=read) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert results == [4] * 8
