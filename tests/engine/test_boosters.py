"""ENG-8 exam boosters and LIB-8 pre-course boosts."""

from collections import Counter
from dataclasses import replace
from datetime import date, timedelta

import pytest

from core.engine.boosters import (
    BoosterPlan,
    BoostTarget,
    booster_targets,
    plan_boosters,
    practice_tests_open,
)
from core.engine.config import AGAIN, GOOD
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.goals import Catalog
from core.engine.lifecycle import RELEARNING, due_day, memory_of
from core.model import CourseGoal, Exam, Section, Skill, SkillState, Unit
from tests.engine.helpers import DAYS, at_day, day, learned_state, some

FSRS = FsrsAdapter(fuzz=False)
TODAY = day(at_day(0))


def skill_ids(n: int) -> list[str]:
    return [f"calc1.s{i:02d}" for i in range(n)]


def cat(n: int = 12) -> Catalog:
    skills = [Skill(id=k, name=k, section_id="calc1.sec1") for k in skill_ids(n)]
    skills.append(
        Skill(id="calc2.int", name="Integrals", section_id="calc2.sec", requires=("calc1.s00",))
    )
    return Catalog.build(
        skills,
        [
            Section(id="calc1.sec1", unit_id="u1", title="s"),
            Section(id="calc2.sec", unit_id="u2", title="s"),
        ],
        [Unit(id="u1", course_id="calc1", title="u"), Unit(id="u2", course_id="calc2", title="u")],
    )


def exam(days_out: int, *, exam_id: int = 1, target: float | None = None) -> Exam:
    return Exam(
        id=exam_id,
        course_id="calc1",
        name=f"Exam {exam_id}",
        at=at_day(days_out),
        sections=("calc1.sec1",),
        target_recall=target,
    )


def target(
    days_out: int, skills: list[str], goal: float = 0.95, key: str = "exam:1"
) -> BoostTarget:
    return BoostTarget(
        key=key,
        name=key,
        day=day(at_day(days_out)),
        at_ms=at_day(days_out),
        target=goal,
        skill_ids=tuple(skills),
    )


def state(skill_id: str, stability: float, reviewed_days_ago: int = 0) -> SkillState:
    return replace(learned_state(stability, at=at_day(-reviewed_days_ago)), skill_id=skill_id)


def plan(
    targets: list[BoostTarget],
    states: list[SkillState],
    today: date = TODAY,
    load: dict[date, int] | None = None,
    retention: float = 0.90,
) -> BoosterPlan:
    return plan_boosters(
        targets,
        {s.skill_id: s for s in states},
        today=today,
        retention_of=lambda _: retention,
        adapter=FSRS,
        days=DAYS,
        base_load=load,
    )


def test_targets_start_21_days_out():
    goals = {"calc1": CourseGoal(course_id="calc1", goal="A")}
    found = booster_targets(
        [exam(21), exam(22, exam_id=2), exam(0, exam_id=3)], goals, cat(), today=TODAY, days=DAYS
    )
    assert [t.key for t in found] == ["exam:1"]
    assert found[0].target == 0.95
    assert len(found[0].skill_ids) == 12
    keep = {"calc1": CourseGoal(course_id="calc1", goal="Keep")}
    assert booster_targets([exam(10)], keep, cat(), today=TODAY, days=DAYS) == []
    own = booster_targets([exam(10, target=0.9)], keep, cat(), today=TODAY, days=DAYS)
    assert own[0].target == 0.9
    b = {"calc1": CourseGoal(course_id="calc1", goal="B")}
    assert booster_targets([exam(10)], b, cat(), today=TODAY, days=DAYS)[0].target == 0.92


def test_skill_due_before_the_exam_is_left_alone():
    s = state("calc1.s00", 5.0)  # due in 5 days, exam in 15
    result = plan([target(15, ["calc1.s00"])], [s])
    assert not result.boosters
    assert result.outlooks[0].left_alone == ("calc1.s00",)
    # Its projected exam-day recall assumes that review (rated Good) happens.
    assert some(result.outlooks[0].recall["calc1.s00"]) > FSRS.retrievability(
        some(memory_of(s)), at_day(15)
    )


def test_booster_window_starts_about_04_new_stabilities_before_the_exam():
    s = state("calc1.s00", 40.0)
    exam_day = 20
    result = plan([target(exam_day, ["calc1.s00"])], [s])
    (b,) = result.boosters
    assert b.feasible
    assert b.recall_without < 0.95 <= b.recall_with
    first, last = b.window
    assert last == day(at_day(exam_day - 1))
    after = FSRS.review(some(memory_of(s)), GOOD, DAYS.moment(first))
    gap = (at_day(exam_day) - DAYS.moment(first)) / 86_400_000
    assert gap <= 0.4025 * after.stability + 1e-9  # the spec's "0.4 x new stability"
    before = first - timedelta(days=1)
    if before >= TODAY:
        earlier = FSRS.review(some(memory_of(s)), GOOD, DAYS.moment(before))
        assert FSRS.retrievability(earlier, at_day(exam_day)) < 0.95
    assert b.day == first  # empty calendar: the earliest day, leaving room to re-plan


def test_no_booster_when_exam_day_recall_already_meets_the_target():
    s = state("calc1.s00", 300.0)
    assert not plan([target(10, ["calc1.s00"])], [s]).boosters


def test_boosters_spread_evenly_over_the_window():
    states = [state(k, 40.0) for k in skill_ids(12)]
    result = plan([target(20, skill_ids(12))], states)
    per_day = Counter(b.day for b in result.boosters)
    assert len(result.boosters) == 12
    window = result.boosters[0].window
    width = (window[1] - window[0]).days + 1
    assert max(per_day.values()) <= -(-12 // width)  # ceil(12 / width)
    assert all(b.window[0] <= b.day <= b.window[1] for b in result.boosters)


def test_existing_load_pushes_boosters_to_quieter_days():
    s = state("calc1.s00", 40.0)
    first = plan([target(20, ["calc1.s00"])], [s]).boosters[0]
    busy = plan([target(20, ["calc1.s00"])], [s], load={first.day: 30}).boosters[0]
    assert busy.day != first.day
    assert busy.window[0] <= busy.day <= busy.window[1]


def test_failed_booster_relearns_and_is_replanned():
    s = state("calc1.s00", 40.0)
    exam_day = 20
    (b,) = plan([target(exam_day, ["calc1.s00"])], [s]).boosters
    booster_at = DAYS.moment(b.day)
    failed_memory = FSRS.review(some(memory_of(s)), AGAIN, booster_at)
    failed = replace(
        s,
        fsrs_state=RELEARNING,
        stability=failed_memory.stability,
        difficulty=failed_memory.difficulty,
        last_review_at=booster_at,
        lapses=1,
    )
    next_day = b.day + timedelta(days=1)
    assert due_day(failed, 0.9, FSRS, DAYS) == next_day
    replanned = plan([target(exam_day, ["calc1.s00"])], [failed], today=next_day)
    assert not replanned.boosters
    assert replanned.outlooks[0].left_alone == ("calc1.s00",)
    # After the relearning review (Good) the next day's plan boosts it again if needed.
    relearn_at = DAYS.moment(next_day)
    relearned_memory = FSRS.review(some(memory_of(failed)), GOOD, relearn_at)
    relearned = replace(
        failed,
        fsrs_state=2,
        stability=relearned_memory.stability,
        difficulty=relearned_memory.difficulty,
        last_review_at=relearn_at,
    )
    later = plan([target(exam_day, ["calc1.s00"])], [relearned], today=next_day + timedelta(days=1))
    if some(due_day(relearned, 0.9, FSRS, DAYS)) >= day(at_day(exam_day)):
        assert (later.boosters and later.boosters[0].recall_with >= 0.95) or not later.boosters[
            0
        ].feasible
    else:
        assert later.outlooks[0].left_alone == ("calc1.s00",)


def test_final_builds_on_the_midterm():
    s = state("calc1.s00", 20.0)  # due on the final's day; misses both targets
    mid = target(12, ["calc1.s00"], key="exam:mid")
    final = target(20, ["calc1.s00"], key="exam:final")
    both = plan([final, mid], [s])
    alone = plan([final], [s])
    assert next(b.target_key for b in both.boosters) == "exam:mid"
    final_outlook = next(o for o in both.outlooks if o.target.key == "exam:final")
    alone_outlook = alone.outlooks[0]
    assert some(final_outlook.recall["calc1.s00"]) >= 0.95
    # The midterm booster changes what the final needs: fewer or different boosters.
    final_boosters = [b for b in both.boosters if b.target_key == "exam:final"]
    assert len(final_boosters) <= len(alone.boosters)
    if final_boosters and alone.boosters:
        assert final_boosters[0].recall_without != alone.boosters[0].recall_without
    assert some(alone_outlook.recall["calc1.s00"]) >= 0.95


def test_unreachable_target_is_best_effort_on_the_last_day():
    s = state("calc1.s00", 30.0)
    (b,) = plan([target(20, ["calc1.s00"], goal=0.999)], [s]).boosters
    assert not b.feasible
    assert b.day == day(at_day(19))
    assert b.window == (b.day, b.day)


def test_unlearned_skills_have_no_projection():
    result = plan([target(10, ["calc1.s00", "calc1.s01"])], [state("calc1.s00", 300.0)])
    assert result.outlooks[0].recall["calc1.s01"] is None


def test_pre_course_boost_targets_prerequisites_at_090():
    goals = {
        "calc1": CourseGoal(course_id="calc1", goal="A", goal_date=TODAY - timedelta(days=30)),
        "calc2": CourseGoal(course_id="calc2", goal="A", starts_on=TODAY + timedelta(days=15)),
    }
    found = booster_targets([], goals, cat(), today=TODAY, days=DAYS)
    assert [(t.key, t.target, t.skill_ids) for t in found] == [
        ("course:calc2", 0.90, ("calc1.s00",))
    ]
    too_early = {**goals, "calc2": replace(goals["calc2"], starts_on=TODAY + timedelta(days=40))}
    assert booster_targets([], too_early, cat(), today=TODAY, days=DAYS) == []
    # Held at 0.85, a 10-day skill is due after the course starts with recall under 0.90.
    s = state("calc1.s00", 10.0)
    result = plan(found, [s], retention=0.85)
    assert result.boosters
    assert result.boosters[0].recall_with >= 0.90
    assert result.boosters[0].recall_without < 0.90


@pytest.mark.parametrize("days_out", [1, 2, 3])
def test_exam_tomorrow_or_soon_still_plans_today_or_later(days_out):
    s = state("calc1.s00", 40.0, reviewed_days_ago=25)
    result = plan([target(days_out, ["calc1.s00"])], [s])
    for b in result.boosters:
        assert TODAY <= b.day < day(at_day(days_out))
    assert plan([target(0, ["calc1.s00"])], [s]).boosters == ()


def test_practice_tests_open_from_the_21_day_booster_window():
    # ENG-8 / QUE-18: tests open with the booster window, 21 days out (was 14).
    assert practice_tests_open(TODAY + timedelta(days=21), TODAY)
    assert practice_tests_open(TODAY + timedelta(days=15), TODAY)
    assert practice_tests_open(TODAY, TODAY)
    assert not practice_tests_open(TODAY + timedelta(days=22), TODAY)
    assert not practice_tests_open(TODAY - timedelta(days=1), TODAY)
