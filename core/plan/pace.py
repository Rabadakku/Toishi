"""The pace schedule (docs/design/student-model.md v1.1, section 4.1). Pure functions.

- Each section starts when the class reaches it: its cumulative standard hours divided by
  the weekly hours times the pace factor, in weeks, floored to whole days. The calendar is
  anchored at the start date, or so that the aligned section ("my class is at section X
  today") falls on its day.
- A course skill is introduced on its section's date once its **course** prerequisites are
  introduced (introduced is enough; they need not be certified). Background skills never gate
  and are never introduced: they come from earlier courses.
- Milestones: M1 certified at tier 2 by introduction + 7 days, M2 at tier 3 at pace by + 21,
  M3 at the target tier at pace by + 35. An exam whose scope holds the skill pulls M2 (only)
  to the exam date minus 2 days; M1's deadline never falls after M2's.
- After the course end date every skill drops to Keep (0.80 at tier 3). On a mid-course start,
  skills in sections before the aligned section start in Keep maintenance, assumed learned.
"""

import math
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from core.learner.types import ComponentId
from core.plan.config import (
    EPS,
    EXAM_PULL_DAYS,
    M1_DAYS,
    M1_TIER,
    M2_DAYS,
    M2_TIER,
    M3_DAYS,
    OUTSIDE_HOURS_PER_CLASS_HOUR,
    PACE_FACTOR_MAX,
    PACE_FACTOR_MIN,
)
from core.plan.types import Course, CourseSettings, ExamSpec, Milestone, PaceStandard, SkillInfo


def check_settings(settings: CourseSettings) -> None:
    """Raise ValueError on settings the planner can't honour (the UI validates them first)."""
    if not PACE_FACTOR_MIN - EPS <= settings.pace_factor <= PACE_FACTOR_MAX + EPS:
        raise ValueError(
            f"pace factor {settings.pace_factor} is outside {PACE_FACTOR_MIN}-{PACE_FACTOR_MAX}"
        )
    for name, value in (
        ("accuracy target", settings.accuracy_target),
        ("keep target", settings.keep_target),
    ):
        if not 0.0 < value < 1.0:
            raise ValueError(f"{name} {value} must be between 0 and 1")
    for name, tier in (("target tier", settings.target_tier), ("keep tier", settings.keep_tier)):
        if not 1 <= tier <= 5:
            raise ValueError(f"{name} {tier} must be 1 to 5")


def _days(hours: float, rate: float) -> int:
    """Whole days after the course's first class at which `hours` of class have passed."""
    return math.floor(hours / rate * 7.0 + EPS)


def section_dates(standard: PaceStandard, settings: CourseSettings) -> dict[str, date]:
    """The day each section starts. Empty when the course has neither a start date nor an
    aligned section (not started). With both, the alignment wins (it is the newer fact)."""
    check_settings(settings)
    rate = standard.weekly_hours * settings.pace_factor
    if rate <= 0:
        raise ValueError(f"weekly hours must be positive, got {standard.weekly_hours}")
    offsets: dict[str, float] = {}
    hours = 0.0
    for section in standard.sections:
        if section.deck in offsets:
            raise ValueError(f"section {section.deck!r} appears twice in the pace standard")
        if section.hours < 0:
            raise ValueError(f"section {section.deck!r} has negative hours")
        offsets[section.deck] = hours
        hours += section.hours
    if settings.aligned is not None:
        deck, day = settings.aligned
        if deck not in offsets:
            raise ValueError(f"aligned section {deck!r} is not in the course's pace standard")
        anchor = _days(offsets[deck], rate)
        return {d: day + timedelta(days=_days(h, rate) - anchor) for d, h in offsets.items()}
    if settings.start is None:
        return {}
    start = settings.start
    return {d: start + timedelta(days=_days(h, rate)) for d, h in offsets.items()}


def course_skills(course: Course) -> dict[ComponentId, SkillInfo]:
    """The course's own (non-background) skills by id."""
    return {s.skill_id: s for s in course.skills if not s.background}


def course_prerequisites(skill: SkillInfo, own: Collection[ComponentId]) -> tuple[ComponentId, ...]:
    """The prerequisites that gate the skill: those that are course skills (not background,
    not outside the course's sections), the skill itself excluded."""
    return tuple(r for r in skill.requires if r in own and r != skill.skill_id)


def intro_dates(course: Course, settings: CourseSettings) -> dict[ComponentId, date]:
    """Introduction date of each course skill (design 4.1).

    A skill gets its section's date, or the latest introduction date among its course
    prerequisites when that is later. A skill whose section is not in the pace standard has
    no date, and neither has any skill that requires it. Requirement cycles resolve to the
    latest section date in the cycle (the values only rise and are bounded).
    """
    sections = section_dates(course.standard, settings)
    own = course_skills(course)
    base = {sid: sections[s.deck] for sid, s in own.items() if s.deck in sections}
    blocked = set(own) - set(base)
    intro = dict(base)
    changed = True
    while changed:
        changed = False
        for sid, skill in own.items():
            if sid in blocked:
                continue
            prereqs = course_prerequisites(skill, own)
            if any(r in blocked for r in prereqs):
                blocked.add(sid)
                del intro[sid]
                changed = True
                continue
            day = max([base[sid], *(intro[r] for r in prereqs)])
            if day != intro[sid]:
                intro[sid] = day
                changed = True
    return intro


def assumed_learned(course: Course, settings: CourseSettings) -> frozenset[ComponentId]:
    """Mid-course start: the course skills in sections before the aligned section. They start
    in Keep maintenance, assumed learned (design 4.1, critique 14)."""
    if settings.aligned is None:
        return frozenset()
    order = [s.deck for s in course.standard.sections]
    deck = settings.aligned[0]
    if deck not in order:
        raise ValueError(f"aligned section {deck!r} is not in the course's pace standard")
    earlier = set(order[: order.index(deck)])
    return frozenset(s.skill_id for s in course.skills if not s.background and s.deck in earlier)


def in_scope(deck: str, exam: ExamSpec) -> bool:
    """A section deck is in an exam's scope when a scope deck is it or one of its parents
    (a unit deck covers its sections)."""
    return any(deck == d or deck.startswith(d + "::") for d in exam.scope_decks)


def keep_tier(skill: SkillInfo, settings: CourseSettings) -> int | None:
    """The tier Keep certifies at: the keep tier when the skill has problems there, else the
    nearest tier that has problems (the lower one on a tie); None with an empty pool."""
    tiers = {p.tier for p in skill.pool}
    if not tiers:
        return None
    return min(tiers, key=lambda t: (abs(t - settings.keep_tier), t))


def milestones(
    skill: SkillInfo, intro: date, settings: CourseSettings, *, assumed: bool = False
) -> tuple[Milestone, ...]:
    """The skill's milestones in order (design 4.1).

    M1 (tier 2, intro + 7), M2 (tier 3 at pace, intro + 21), M3 (target tier at pace,
    intro + 35); no milestone tier exceeds the target tier. Exams whose scope holds the skill
    and that fall on or after its introduction pull M2 to exam - 2 days (never before the
    introduction), and M1's deadline is then at most M2's. A milestone at a tier where the
    skill has no problems is left out (it can't be certified from direct evidence; as for
    `level`, design 3.7). A course with an end date adds Keep last (no deadline). An assumed
    skill (mid-course start) has Keep only.
    """
    tiers = {p.tier for p in skill.pool}
    keep: tuple[Milestone, ...] = ()
    kt = keep_tier(skill, settings)
    if kt is not None and (assumed or settings.end is not None):
        keep = (Milestone("keep", kt, None),)
    if assumed:
        return keep
    m2 = intro + timedelta(days=M2_DAYS)
    for exam in settings.exams:
        if exam.day >= intro and in_scope(skill.deck, exam):
            m2 = min(m2, max(intro, exam.day - timedelta(days=EXAM_PULL_DAYS)))
    m1 = min(intro + timedelta(days=M1_DAYS), m2)
    m3 = intro + timedelta(days=M3_DAYS)
    target = settings.target_tier
    plan = (
        Milestone("M1", min(M1_TIER, target), m1),
        Milestone("M2", min(M2_TIER, target), m2),
        Milestone("M3", target, m3),
    )
    return tuple(m for m in plan if m.tier in tiers) + keep


@dataclass(frozen=True, slots=True)
class Schedule:
    """The pace schedule of one course under one student's settings."""

    sections: Mapping[str, date]
    intro: Mapping[ComponentId, date]
    assumed: frozenset[ComponentId]
    milestones: Mapping[ComponentId, tuple[Milestone, ...]]


def schedule(course: Course, settings: CourseSettings) -> Schedule:
    """Section dates, introduction dates, the assumed-learned set and every skill's
    milestones."""
    sections = section_dates(course.standard, settings)
    intro = intro_dates(course, settings)
    assumed = assumed_learned(course, settings)
    own = course_skills(course)
    ms = {
        sid: milestones(own[sid], day, settings, assumed=sid in assumed)
        for sid, day in intro.items()
    }
    return Schedule(sections=sections, intro=intro, assumed=assumed, milestones=ms)


def milestone_rule(milestone: Milestone, settings: CourseSettings) -> tuple[int, bool, float]:
    """(tier, timed, target) of a milestone: M2 and M3 need time <= standard (design 3.7);
    Keep is accuracy only, at the keep target."""
    if milestone.name == "keep":
        return milestone.tier, False, settings.keep_target
    return milestone.tier, milestone.name in ("M2", "M3"), settings.accuracy_target


def standard_hours(standard: PaceStandard, settings: CourseSettings) -> float:
    """The course's reference outside-class hours per week at the student's pace factor: the
    pack's figure, or 2 hours per weekly class hour (34 CFR 600.2) when it gives none."""
    base = standard.standard_outside_hours
    if base is None:
        base = OUTSIDE_HOURS_PER_CLASS_HOUR * standard.weekly_hours
    return base * settings.pace_factor
