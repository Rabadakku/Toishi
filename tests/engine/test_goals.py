"""Goal presets, retention per skill and day (ENG-1, LIB-4, LIB-8)."""

from datetime import date

import pytest

from core.engine.goals import (
    Catalog,
    course_retention,
    exam_target,
    hardest_tier,
    next_course_prerequisites,
    preset_for,
    retention_map,
    skill_retention,
)
from core.engine.lifecycle import due_day
from core.model import CourseGoal, Exam, Section, Skill, Unit
from tests.engine.helpers import DAYS, adapter, at_day, learned_state

D = date(2026, 10, 1)


def catalog() -> Catalog:
    return Catalog.build(
        [
            Skill(id="alg.factor", name="Factor", section_id="alg.s1"),
            Skill(id="calc1.limits", name="Limits", section_id="c1.s1", requires=("alg.factor",)),
            Skill(
                id="calc1.deriv", name="Derivatives", section_id="c1.s2", requires=("calc1.limits",)
            ),
            Skill(id="calc2.int", name="Integrals", section_id="c2.s1", requires=("calc1.deriv",)),
            Skill(id="loose", name="No section"),
        ],
        [
            Section(id="alg.s1", unit_id="alg.u", title="s"),
            Section(id="c1.s1", unit_id="c1.u", title="s", ord=1),
            Section(id="c1.s2", unit_id="c1.u", title="s", ord=2),
            Section(id="c2.s1", unit_id="c2.u", title="s"),
        ],
        [
            Unit(id="alg.u", course_id="alg", title="u"),
            Unit(id="c1.u", course_id="calc1", title="u"),
            Unit(id="c2.u", course_id="calc2", title="u"),
        ],
    )


def test_presets():
    assert preset_for(None).retention == 0.90
    assert preset_for(CourseGoal(course_id="c", goal="A")).exam_recall == 0.95
    b = preset_for(CourseGoal(course_id="c", goal="B"))
    assert (b.retention, b.exam_recall, b.hardest_tier) == (0.88, 0.92, 4)
    keep = preset_for(CourseGoal(course_id="c", goal="Keep"))
    assert (keep.retention, keep.exam_recall) == (0.80, None)
    custom = preset_for(CourseGoal(course_id="c", goal="custom", custom_retention=0.85))
    assert custom.retention == 0.85
    assert custom.exam_recall == pytest.approx(0.90)
    assert (
        preset_for(CourseGoal(course_id="c", goal="custom", custom_retention=0.80)).exam_recall
        is None
    )
    assert (
        preset_for(CourseGoal(course_id="c", goal="custom", custom_retention=0.93)).exam_recall
        == 0.95
    )


def test_course_drops_to_keep_after_its_goal_date():
    goal = CourseGoal(course_id="calc1", goal="A", goal_date=D)
    assert course_retention(goal, D) == 0.90
    assert course_retention(goal, date(2026, 10, 2)) == 0.80
    assert hardest_tier(CourseGoal(course_id="c", goal="B", goal_date=D), D) == 4
    assert exam_target(Exam(name="Final", at=0), goal, D) == 0.95
    assert exam_target(Exam(name="Late", at=0), goal, date(2026, 10, 5)) is None
    assert exam_target(Exam(name="Own", at=0, target_recall=0.9), goal, date(2026, 10, 5)) == 0.9


def test_catalog_lookups():
    cat = catalog()
    assert cat.course_of("calc1.deriv") == "calc1"
    assert cat.course_of("loose") is None
    assert cat.skills_of_course("calc1") == ["calc1.deriv", "calc1.limits"]
    assert cat.prerequisites(["calc2.int"]) == {"calc1.deriv", "calc1.limits", "alg.factor"}
    assert cat.skills_in_sections(["c1.s2"]) == ["calc1.deriv"]


def test_next_course_prerequisites_are_held_at_085_after_keep():
    cat = catalog()
    goals = {
        "calc1": CourseGoal(course_id="calc1", goal="A", goal_date=D),
        "calc2": CourseGoal(course_id="calc2", goal="A", starts_on=date(2027, 1, 10)),
    }
    after = date(2026, 12, 1)
    assert next_course_prerequisites(cat, goals, after) == {
        "calc2": {"calc1.deriv", "calc1.limits", "alg.factor"}
    }
    assert skill_retention("calc1.deriv", after, cat, goals) == 0.85  # instead of 0.80
    assert skill_retention("calc1.deriv", D, cat, goals) == 0.90  # still under goal A
    assert skill_retention("alg.factor", after, cat, goals) == 0.90  # alg: default goal A
    assert skill_retention("loose", after, cat, goals) == 0.90
    assert retention_map(["calc2.int", "calc1.deriv"], after, cat, goals) == {
        "calc2.int": 0.90,
        "calc1.deriv": 0.85,
    }


def test_changing_a_goal_reschedules_nothing_but_moves_due_dates_live():
    fsrs = adapter()
    state = learned_state(20.0, at=at_day(0))
    due_a = due_day(state, 0.90, fsrs, DAYS)
    due_keep = due_day(state, 0.80, fsrs, DAYS)
    assert due_a is not None
    assert due_keep is not None
    assert due_keep > due_a
    # The stored row is the same object either way: only the live computation differs.
    assert state.stability == 20.0
