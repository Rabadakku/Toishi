"""The storage-bound Engine: grading committed through UserStore, undo, DST, plans."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from core.engine import AnswerFacts, Engine, ProblemOutcome, TimingFacts
from core.engine.config import DAY_MS, RULES_VERSION
from core.engine.grading import GradeResult, SkillContext
from core.engine.grading import ProblemOutcome as Outcome
from core.engine.selection import form_stats
from core.model import Card, Course, CourseGoal, Exam, PackInfo, Section, Skill, Unit
from core.storage import Storage, build_pack
from core.storage.clock import FixedClock, day_start_ms, to_ms
from core.storage.profiles import ProfilePaths
from tests.engine.helpers import some

NY = ZoneInfo("America/New_York")
PACK = PackInfo(id="calc1", title="Calculus I", version="1")
SKILLS = ["calc1.alg", "calc1.lim", "calc1.der"]


def pack_records() -> list[object]:
    records: list[object] = [
        Course(id="calc1", title="Calculus I"),
        Unit(id="calc1.u1", course_id="calc1", title="Unit 1"),
        Section(id="calc1.s1", unit_id="calc1.u1", title="1.1", ord=1, textbook_ref="Stewart 1.1"),
        Section(id="calc1.s2", unit_id="calc1.u1", title="1.2", ord=2),
        Skill(id="calc1.alg", name="Algebra", section_id="calc1.s1", textbook_ref="Stewart 1.1"),
        Skill(
            id="calc1.lim",
            name="Limits",
            section_id="calc1.s1",
            requires=("calc1.alg",),
            exam_tier=3,
        ),
        Skill(id="calc1.der", name="Derivatives", section_id="calc1.s2", requires=("calc1.lim",)),
    ]
    for skill in SKILLS:
        records.append(
            Card(id=f"{skill}.ex", kind="example", skill_id=skill, tier=1, question_md="Worked.")
        )
        for tier in range(1, 6):
            for seed in range(4):
                records.append(
                    Card(
                        id=f"{skill}.t{tier}.v{seed}",
                        skill_id=skill,
                        tier=tier,
                        template_id=f"{skill}.tmpl{tier}",
                        seed=seed,
                        answer_type="number",
                        answer="1",
                        question_md="Solve.",
                    )
                )
    return records


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 9, 1, 12, tzinfo=NY), tz=NY)


@pytest.fixture
def storage(tmp_path: Path, clock: FixedClock) -> Iterator[Storage]:
    pack = tmp_path / "calc1.db"
    build_pack(pack, PACK, pack_records())  # type: ignore[arg-type]
    opened = Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=[pack], clock=clock, create=True)
    opened.users.set_setting("study.timezone", "America/New_York")
    yield opened
    opened.close(backup=False)


def answer(engine: Engine, clock: FixedClock, skill: str, *, correct: bool = True, **kw: object):
    pick = engine.pick_problem(skill)
    assert pick is not None
    out = ProblemOutcome(
        card=pick.card,
        facts=AnswerFacts(correct=correct),
        at=clock.now_ms(),
        timing=TimingFacts(solve_ms=30_000, active_ms=34_000, expected_chars=3),
        **kw,  # type: ignore[arg-type]
    )
    recorded = engine.grade(out)
    clock.advance(minutes=1)
    return recorded


def learn(engine: Engine, clock: FixedClock, skill: str) -> None:
    refs = engine._storage.packs.card_refs(skill_id=skill)
    example = next(r for r in refs if r.kind == "example")
    engine.grade(
        ProblemOutcome(
            card=example, facts=AnswerFacts(correct=False), at=clock.now_ms(), verdict="shown"
        )
    )
    for _ in range(3):
        answer(engine, clock, skill)


def test_learning_and_review_are_committed_with_rules_and_predictions(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    state = storage.users.skill_state("calc1.lim")
    assert state is not None
    assert state.level == "learned"
    assert state.fsrs_state == 2
    events = storage.users.review_events(target_id="calc1.lim")
    assert [e.rating for e in events] == [3, 3, 3]
    assert all(e.rules_version == RULES_VERSION and e.params_id == "fsrs6-default" for e in events)
    assert events[-1].state_before["stability"] is None
    assert events[-1].state_after["stability"] > 2
    clock.advance(days=2)
    rec = answer(engine, clock, "calc1.lim")
    assert rec.attempt.id is not None
    assert rec.attempt.rules_version == RULES_VERSION
    assert rec.attempt.predicted_recall == pytest.approx(
        rec.result.answer.reviews[0].predicted_recall
    )
    stored = storage.users.review_events(target_id="calc1.lim")[-1]
    assert 0.85 < stored.predicted_recall < 0.95
    assert stored.retention == 0.90
    assert rec.attempt.capped_ms == 34_000
    assert rec.attempt.extra["speed_ms"] == 30_000 + 5_000 + 900


def test_undo_restores_fsrs_level_elo_and_problem_difficulty(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    clock.advance(days=3)
    before = storage.users.skill_state("calc1.lim")
    forms_before = form_stats(storage.users.attempts(skill_id="calc1.lim"))
    rec = answer(engine, clock, "calc1.lim", correct=False)
    assert storage.users.skill_state("calc1.lim").lapses == 1
    storage.users.undo_last_answer()
    after = storage.users.skill_state("calc1.lim")
    assert replace(after, updated_at=0) == replace(before, updated_at=0)
    assert form_stats(storage.users.attempts(skill_id="calc1.lim")) == forms_before
    assert storage.users.review_events(target_id="calc1.lim")[-1].attempt_id != rec.attempt.id


def test_due_dates_are_dst_safe(storage, clock):
    """Learned on Friday Oct 30 (EDT); due two study days later on Sunday Nov 1, the day the
    clocks fall back: the day starts at 4 AM EST, not 4 AM EDT."""
    clock.set(datetime(2026, 10, 30, 21, tzinfo=NY))
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    state = storage.users.skill_state("calc1.lim")
    nov1 = date(2026, 11, 1)
    assert state.due_at == day_start_ms(nov1, NY, 4)
    assert state.due_at == to_ms(datetime(2026, 11, 1, 9, tzinfo=ZoneInfo("UTC")))
    assert [d.skill_id for d in engine.due_skills(date(2026, 10, 31))] == []
    assert [d.skill_id for d in engine.due_skills(nov1)] == ["calc1.lim"]
    # 3:30 AM on Nov 2 still belongs to study day Nov 1.
    clock.set(datetime(2026, 11, 2, 3, 30, tzinfo=NY))
    assert engine.today() == nov1


def test_spring_forward_day(storage, clock):
    clock.set(datetime(2027, 3, 12, 20, tzinfo=NY))
    engine = Engine(storage)
    learn(engine, clock, "calc1.alg")
    state = storage.users.skill_state("calc1.alg")
    assert state.due_at == day_start_ms(date(2027, 3, 14), NY, 4)
    assert state.due_at == to_ms(datetime(2027, 3, 14, 8, tzinfo=ZoneInfo("UTC")))  # 4 AM EDT


def test_off_sections_leave_the_queue_but_keep_progress(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.der")
    day3 = engine.today() + timedelta(days=3)
    assert [d.skill_id for d in engine.due_skills(day3)] == ["calc1.der"]
    storage.users.set_section_state("calc1.s2", "off")
    assert engine.due_skills(day3) == []
    assert storage.users.skill_state("calc1.der").stability is not None


def test_pick_problem_bands_and_stretch(storage, clock):
    engine = Engine(storage)
    first = engine.pick_problem("calc1.lim")
    assert first is not None
    assert first.card.tier in (1, 2)
    learn(engine, clock, "calc1.lim")
    stretch = engine.pick_problem("calc1.lim", stretch=True)
    assert stretch is not None
    assert stretch.stretch
    assert stretch.card.tier == 3
    lighter = engine.pick_problem("calc1.lim", lighter_set=True)
    assert lighter is not None
    assert lighter.card.tier in (1, 2)
    storage.users.set_course_goal(CourseGoal(course_id="calc1", goal="B"))
    storage.users.add_exam(
        Exam(
            course_id="calc1",
            name="Midterm",
            at=clock.now_ms() + 10 * DAY_MS,
            sections=("calc1.s1",),
        )
    )
    windowed = engine.pick_problem("calc1.lim")
    assert windowed is not None
    assert windowed.card.tier == 3
    assert not some(engine.pick_problem("calc1.lim", stretch=True)).stretch  # not in the window


def test_exam_window_uses_tier_three_and_boosters_are_planned(storage, clock):
    engine = Engine(storage)
    for skill in SKILLS:
        learn(engine, clock, skill)
    # Spread the reviews so that some skills are due after the exam.
    for _ in range(4):
        clock.advance(days=5)
        for skill in SKILLS:
            answer(engine, clock, skill)
    exam_at = clock.now_ms() + 18 * DAY_MS
    storage.users.set_course_goal(CourseGoal(course_id="calc1", goal="A"))
    exam = storage.users.add_exam(
        Exam(
            course_id="calc1",
            name="Final",
            at=exam_at,
            minutes=60,
            problems=10,
            sections=("calc1.s1", "calc1.s2"),
        )
    )
    plan = engine.booster_plan()
    assert plan.outlooks
    assert plan.outlooks[0].target.target == 0.95
    for b in plan.boosters:
        assert b.recall_with >= 0.95 or not b.feasible
    projection = engine.exam_projection(exam.id)
    assert projection is not None
    assert projection.skills == 3
    assert 0 < projection.projected_score <= 1
    ctx = engine.context("calc1.lim")
    assert ctx.exam_window
    assert ctx.exam_problem_ms == 306_000
    load = engine.course_load("calc1")
    # Four early Good reviews took every skill to ~70-day stability: little is due in 28 days.
    assert load.horizon_days == 28
    assert 0 <= load.problems_per_day < 1
    assert engine.target_time("calc1.lim", 3) == 153_000  # exam pace for tier 3
    assert engine.level("calc1.lim") in ("learned", "exam")
    assert 0 < some(engine.recall("calc1.lim")) <= 1
    assert some(engine.recall_on("calc1.lim", engine.today() + timedelta(days=30))) < some(
        engine.recall("calc1.lim")
    )
    assert engine.retention("calc1.lim") == 0.90


def test_hooks_run_after_base_grading(storage, clock):
    seen: list[str] = []

    def hook(ctx: SkillContext, outcome: Outcome, result: GradeResult) -> GradeResult:
        seen.append(result.effects.stage)
        return replace(
            result,
            answer=replace(
                result.answer, attempt=replace(result.answer.attempt, reason_tag="Check")
            ),
        )

    engine = Engine(storage, hooks=[hook])
    rec = answer(engine, clock, "calc1.alg")
    assert seen == ["learning"]
    assert rec.attempt.reason_tag == "Check"


def test_record_try_is_never_rated(storage, clock):
    engine = Engine(storage)
    pick = some(engine.pick_problem("calc1.alg"))
    attempt = engine.record_try(
        ProblemOutcome(card=pick.card, facts=AnswerFacts(correct=False), at=clock.now_ms())
    )
    assert not attempt.final
    assert attempt.rating is None
    assert attempt.verdict == "incorrect"
    assert storage.users.skill_state("calc1.alg") is None


def test_placement_and_calibration_through_storage(storage, clock):
    engine = Engine(storage)
    written = engine.place({"calc1.der": "direct", "calc1.lim": "inferred"})
    assert {r.skill_id: r.stability for r in written} == {"calc1.der": 10.0, "calc1.lim": 2.3}
    assert storage.users.skill_state("calc1.der").level == "learned"
    assert engine.place({"calc1.der": "inferred"}) == []  # never takes progress away
    offer = engine.fit_offer()
    assert not offer.offer
    assert offer.needed == 300
    assert engine.calibration() == {}


def test_fitted_parameters_are_used_live(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.alg")
    default_due = engine.due_skills(engine.today() + timedelta(days=2))
    params = list(engine.adapter().parameters)
    params[20] = 0.3  # a different decay
    storage.users.set_setting("fsrs.params.math", {"w": params})
    assert engine.adapter().params_id.startswith("fit-")
    assert [d.skill_id for d in default_due] == ["calc1.alg"]
    # A slower decay changes the live recall; the stored row is untouched.
    assert engine.recall("calc1.alg", clock.now_ms() + 2 * DAY_MS) != pytest.approx(
        Engine(storage, adapter=engine.adapter().__class__()).recall(
            "calc1.alg", clock.now_ms() + 2 * DAY_MS
        )
    )
