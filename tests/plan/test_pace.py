"""The pace schedule (design 4.1): section and introduction dates, milestones, exams, Keep."""

from dataclasses import replace
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.plan.pace import (
    assumed_learned,
    check_settings,
    in_scope,
    intro_dates,
    keep_tier,
    milestone_rule,
    milestones,
    schedule,
    section_dates,
    standard_hours,
)
from core.plan.types import CourseSettings, ExamSpec, Milestone, PaceStandard, SectionPace
from tests.plan.helpers import course, pool, skill

A, B, C = "Calc::U1::A", "Calc::U1::B", "Calc::U2::C"
SECTIONS = [(A, 6.0), (B, 8.0), (C, 8.0)]
START = date(2026, 9, 1)


def standard(weekly: float = 2.0) -> PaceStandard:
    return PaceStandard(tuple(SectionPace(d, h) for d, h in SECTIONS), weekly_hours=weekly)


def test_section_dates_from_start() -> None:
    """At 2 class hours a week: A starts at 0 h (day 0), B after 6 h = 3 weeks = day 21,
    C after 14 h = 7 weeks = day 49."""
    got = section_dates(standard(), CourseSettings("c", start=START))
    assert got == {A: date(2026, 9, 1), B: date(2026, 9, 22), C: date(2026, 10, 20)}


def test_pace_factor_scales_the_calendar_and_days_are_floored() -> None:
    """1.5x: 3 h a week, B at 6/3*7 = 14 days, C at 14/3*7 = 32.67 -> day 32.
    0.75x: 1.5 h a week, B at 6/1.5*7 = 28 days, C at 14/1.5*7 = 65.33 -> day 65."""
    fast = section_dates(standard(), CourseSettings("c", start=START, pace_factor=1.5))
    assert fast[B] == START + timedelta(days=14)
    assert fast[C] == START + timedelta(days=32)
    slow = section_dates(standard(), CourseSettings("c", start=START, pace_factor=0.75))
    assert slow[B] == START + timedelta(days=28)
    assert slow[C] == START + timedelta(days=65)


def test_aligned_section_anchors_the_calendar() -> None:
    """ "My class is at B on Oct 5": B is day 21 of the calendar, so A is 21 days earlier
    (Sep 14) and C 28 days later (49 - 21), Nov 2."""
    got = section_dates(standard(), CourseSettings("c", aligned=(B, date(2026, 10, 5))))
    assert got == {A: date(2026, 9, 14), B: date(2026, 10, 5), C: date(2026, 11, 2)}


def test_alignment_wins_over_a_start_date_and_no_anchor_means_no_dates() -> None:
    both = CourseSettings("c", start=START, aligned=(B, date(2026, 10, 5)))
    assert section_dates(standard(), both)[B] == date(2026, 10, 5)
    assert section_dates(standard(), CourseSettings("c")) == {}


def test_bad_settings_and_standards_raise() -> None:
    with pytest.raises(ValueError, match="pace factor"):
        check_settings(CourseSettings("c", pace_factor=2.0))
    with pytest.raises(ValueError, match="accuracy target"):
        check_settings(CourseSettings("c", accuracy_target=1.0))
    with pytest.raises(ValueError, match="target tier"):
        check_settings(CourseSettings("c", target_tier=6))
    with pytest.raises(ValueError, match="aligned section"):
        section_dates(standard(), CourseSettings("c", aligned=("nope", START)))
    with pytest.raises(ValueError, match="weekly hours"):
        section_dates(standard(weekly=0.0), CourseSettings("c", start=START))
    twice = PaceStandard((SectionPace(A, 1.0), SectionPace(A, 1.0)), weekly_hours=2.0)
    with pytest.raises(ValueError, match="twice"):
        section_dates(twice, CourseSettings("c", start=START))


def test_intro_waits_for_course_prerequisites_only() -> None:
    """b1 (section B, Sep 22) requires c1 (section C, Oct 20): introduced Oct 20.
    b2 requires a background component and a background skill: never gated, Sep 22.
    c1 requires a1 (Sep 1): its own date, Oct 20. Background skills get no date."""
    cr = course(
        SECTIONS,
        [
            skill("a1", A, 1),
            skill("b1", B, 2, requires=["c1"]),
            skill("b2", B, 3, requires=["alg.factor", "pre.bg"]),
            skill("c1", C, 4, requires=["a1"]),
            skill("pre.bg", "Pre::X", 0, background=True),
        ],
    )
    got = intro_dates(cr, CourseSettings("c", start=START))
    assert got == {
        "a1": date(2026, 9, 1),
        "b1": date(2026, 10, 20),
        "b2": date(2026, 9, 22),
        "c1": date(2026, 10, 20),
    }


def test_unscheduled_section_blocks_its_dependents_and_cycles_settle() -> None:
    """x1's section is not in the pace standard: no date, and b1 that requires it has none.
    b2 <-> c2 require each other: both at the later section date (C, Oct 20)."""
    cr = course(
        SECTIONS,
        [
            skill("x1", "Calc::Optional::X", 1),
            skill("b1", B, 2, requires=["x1"]),
            skill("b2", B, 3, requires=["c2"]),
            skill("c2", C, 4, requires=["b2"]),
        ],
    )
    got = intro_dates(cr, CourseSettings("c", start=START))
    assert got == {"b2": date(2026, 10, 20), "c2": date(2026, 10, 20)}


INTRO = date(2026, 9, 22)


def test_milestones_at_plus_7_21_35() -> None:
    """Introduced Sep 22: M1 at tier 2 by Sep 29, M2 at tier 3 by Oct 13, M3 at tier 4 by
    Oct 27. No end date: no Keep."""
    got = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", start=START))
    assert got == (
        Milestone("M1", 2, date(2026, 9, 29)),
        Milestone("M2", 3, date(2026, 10, 13)),
        Milestone("M3", 4, date(2026, 10, 27)),
    )


def test_exam_pulls_m2_only() -> None:
    """Exam Oct 8 covering unit U1 (B's parent deck): M2 = min(Oct 13, Oct 8 - 2) = Oct 6.
    M1 (Sep 29) is already earlier; M3 stays Oct 27."""
    exam = ExamSpec(1, date(2026, 10, 8), ("Calc::U1",))
    got = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", start=START, exams=(exam,)))
    assert [m.deadline for m in got] == [date(2026, 9, 29), date(2026, 10, 6), date(2026, 10, 27)]


def test_exam_right_after_intro_pulls_m2_to_intro_and_m1_with_it() -> None:
    """Exam Sep 25, three days after the Sep 22 intro: M2 = max(Sep 22, Sep 23) = Sep 23, and
    M1 = min(Sep 29, Sep 23) = Sep 23. An exam on Sep 23: M2 = max(Sep 22, Sep 21) = Sep 22."""
    exam = ExamSpec(1, date(2026, 9, 25), (B,))
    got = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", exams=(exam,)))
    assert got[0].deadline == got[1].deadline == date(2026, 9, 23)
    exam = ExamSpec(1, date(2026, 9, 23), (B,))
    got = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", exams=(exam,)))
    assert got[1].deadline == INTRO


def test_exams_before_intro_or_out_of_scope_do_not_pull() -> None:
    early = ExamSpec(1, date(2026, 9, 20), (B,))
    other = ExamSpec(2, date(2026, 10, 1), ("Calc::U2",))
    got = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", exams=(early, other)))
    assert got[1].deadline == date(2026, 10, 13)
    assert in_scope("Calc::U1::B", ExamSpec(3, INTRO, ("Calc::U1",)))
    assert not in_scope("Calc::U10::B", ExamSpec(3, INTRO, ("Calc::U1",)))


def test_end_date_adds_keep_and_assumed_skills_keep_only() -> None:
    s = CourseSettings("c", start=START, end=date(2026, 12, 15))
    got = milestones(skill("b1", B, 2), INTRO, s)
    assert got[-1] == Milestone("keep", 3, None)
    assert milestones(skill("b1", B, 2), INTRO, s, assumed=True) == (Milestone("keep", 3, None),)


def test_milestones_skip_tiers_without_problems_and_never_exceed_the_target_tier() -> None:
    """Pool at tiers 1-2 only: M1 only. Target tier 3: M2 and M3 both at tier 3. Target
    tier 2: every milestone at tier 2 (M2 and M3 timed, M1 not)."""
    drills = skill("b1", B, 2, problems=pool("b1", {1: 2, 2: 2}))
    assert [m.name for m in milestones(drills, INTRO, CourseSettings("c"))] == ["M1"]
    t3 = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", target_tier=3))
    assert [(m.name, m.tier) for m in t3] == [("M1", 2), ("M2", 3), ("M3", 3)]
    t2 = milestones(skill("b1", B, 2), INTRO, CourseSettings("c", target_tier=2))
    assert [(m.name, m.tier) for m in t2] == [("M1", 2), ("M2", 2), ("M3", 2)]


def test_keep_tier_is_the_nearest_tier_with_problems() -> None:
    s = CourseSettings("c")
    assert keep_tier(skill("x", B, 1), s) == 3
    assert keep_tier(skill("x", B, 1, problems=pool("x", {2: 1, 4: 1})), s) == 2
    assert keep_tier(skill("x", B, 1, problems=pool("x", {4: 1, 5: 1})), s) == 4
    assert keep_tier(skill("x", B, 1, problems=()), s) is None


def test_milestone_rules() -> None:
    s = CourseSettings("c", accuracy_target=0.9, keep_target=0.8)
    assert milestone_rule(Milestone("M1", 2, INTRO), s) == (2, False, 0.9)
    assert milestone_rule(Milestone("M2", 3, INTRO), s) == (3, True, 0.9)
    assert milestone_rule(Milestone("M3", 4, INTRO), s) == (4, True, 0.9)
    assert milestone_rule(Milestone("keep", 3, None), s) == (3, False, 0.8)


def test_mid_course_start_assumes_earlier_sections_learned() -> None:
    """Aligned at B: A's skills are assumed learned (Keep only); B's and C's are not."""
    cr = course(SECTIONS, [skill("a1", A, 1), skill("b1", B, 2), skill("c1", C, 3)])
    s = CourseSettings("c", aligned=(B, date(2026, 10, 5)))
    assert assumed_learned(cr, s) == {"a1"}
    sch = schedule(cr, s)
    assert sch.milestones["a1"] == (Milestone("keep", 3, None),)
    assert sch.milestones["b1"][0] == Milestone("M1", 2, date(2026, 10, 12))
    assert assumed_learned(cr, CourseSettings("c", start=START)) == frozenset()


def test_standard_hours_fall_back_to_two_hours_per_class_hour() -> None:
    """Pack figure 7 h at pace 1.5 -> 10.5 h; no figure at 2.5 class h/week -> 5 h."""
    assert standard_hours(
        replace(standard(), standard_outside_hours=7.0), CourseSettings("c", pace_factor=1.5)
    ) == pytest.approx(10.5)
    assert standard_hours(standard(weekly=2.5), CourseSettings("c")) == pytest.approx(5.0)


@settings(max_examples=200, deadline=None, database=None)
@given(
    a=st.integers(0, 400),
    gap=st.integers(0, 60),
    exams=st.lists(st.tuples(st.integers(-30, 460), st.booleans()), max_size=3),
    target=st.integers(2, 5),
)
def test_milestone_dates_are_monotone_in_intro_dates(
    a: int, gap: int, exams: list[tuple[int, bool]], target: int
) -> None:
    """Property: for one skill and fixed settings, a later introduction never gives an
    earlier deadline for any milestone; and deadlines never fall before the introduction and
    run M1 <= M2 <= M3."""
    base = date(2026, 1, 1)
    specs = tuple(
        ExamSpec(i, base + timedelta(days=d), (B if covers else "Other::X",))
        for i, (d, covers) in enumerate(exams)
    )
    s = CourseSettings("c", target_tier=target, exams=specs)
    sk = skill("b1", B, 2, problems=pool("b1", {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}))
    early = base + timedelta(days=a)
    late = early + timedelta(days=gap)
    m_early = milestones(sk, early, s)
    m_late = milestones(sk, late, s)
    assert [m.name for m in m_early] == [m.name for m in m_late]
    for x, y in zip(m_early, m_late, strict=True):
        assert x.deadline is not None
        assert y.deadline is not None
        assert x.deadline <= y.deadline
    for ms, intro in ((m_early, early), (m_late, late)):
        deadlines = [m.deadline for m in ms if m.deadline is not None]
        assert all(d >= intro for d in deadlines)
        assert deadlines == sorted(deadlines)
