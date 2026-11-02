"""Goals (LIB-4, LIB-8, goal presets): desired retention, exam-day targets, course lookups.

Desired retention is resolved per skill and per day, never stored: changing a goal or
passing a goal date reschedules nothing, it only changes the live due dates (ENG-1).
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from core.engine.config import KEEP_RETENTION, NEXT_COURSE_PREREQ_RETENTION
from core.model import CourseGoal, Exam, Section, Skill, Unit


@dataclass(frozen=True, slots=True)
class GoalPreset:
    retention: float
    exam_recall: float | None
    hardest_tier: int | None  # None: unchanged (Keep)


PRESETS: Mapping[str, GoalPreset] = {
    "A": GoalPreset(0.90, 0.95, 5),
    "B": GoalPreset(0.88, 0.92, 4),
    "Keep": GoalPreset(KEEP_RETENTION, None, None),
}
DEFAULT_GOAL = "A"


def preset_for(goal: CourseGoal | None) -> GoalPreset:
    """The preset for a goal. A custom retention r gets an exam-day target of
    min(0.95, r + 0.05) (none at 0.80, like Keep) and tier 5 from 0.90 up, else tier 4."""
    if goal is None:
        return PRESETS[DEFAULT_GOAL]
    if goal.goal == "custom":
        r = float(goal.custom_retention or KEEP_RETENTION)
        exam = None if r <= KEEP_RETENTION else min(0.95, round(r + 0.05, 4))
        return GoalPreset(r, exam, 5 if r >= 0.90 else 4)
    return PRESETS[goal.goal]


def past_goal_date(goal: CourseGoal | None, day: date) -> bool:
    return goal is not None and goal.goal_date is not None and day > goal.goal_date


def course_retention(goal: CourseGoal | None, day: date) -> float:
    """Everyday retention for a course on a day; Keep after the goal date (LIB-8)."""
    if past_goal_date(goal, day):
        return KEEP_RETENTION
    return preset_for(goal).retention


def hardest_tier(goal: CourseGoal | None, day: date) -> int:
    if past_goal_date(goal, day):
        return 5
    tier = preset_for(goal).hardest_tier
    return 5 if tier is None else tier


def exam_target(exam: Exam, goal: CourseGoal | None, exam_day: date) -> float | None:
    """An exam's exam-day recall target: its own, else the goal's (None: no boosters).
    An exam after the course's goal date falls under Keep, which has no target."""
    if exam.target_recall is not None:
        return exam.target_recall
    if past_goal_date(goal, exam_day):
        return None
    return preset_for(goal).exam_recall


@dataclass(frozen=True, slots=True)
class Catalog:
    """The skill graph and course tree the engine needs, built from PackStore lists."""

    skills: Mapping[str, Skill]
    course_of_section: Mapping[str, str]
    section_order: Mapping[str, tuple[int, int]] = field(default_factory=dict)

    @classmethod
    def build(
        cls, skills: Iterable[Skill], sections: Iterable[Section], units: Iterable[Unit]
    ) -> Catalog:
        unit_course = {u.id: (u.course_id, u.ord) for u in units}
        course_of_section: dict[str, str] = {}
        order: dict[str, tuple[int, int]] = {}
        for s in sections:
            course, unit_ord = unit_course.get(s.unit_id, ("", 0))
            if course:
                course_of_section[s.id] = course
            order[s.id] = (unit_ord, s.ord)
        return cls({k.id: k for k in skills}, course_of_section, order)

    def course_of(self, skill_id: str) -> str | None:
        skill = self.skills.get(skill_id)
        if skill is None or skill.section_id is None:
            return None
        return self.course_of_section.get(skill.section_id)

    def skills_of_course(self, course_id: str) -> list[str]:
        return sorted(k for k in self.skills if self.course_of(k) == course_id)

    def skills_in_sections(self, section_ids: Iterable[str]) -> list[str]:
        wanted = set(section_ids)
        return sorted(k.id for k in self.skills.values() if k.section_id in wanted)

    def prerequisites(self, skill_ids: Iterable[str]) -> set[str]:
        """Every skill reachable by `requires` edges (transitively), excluding the start set."""
        start = set(skill_ids)
        seen: set[str] = set()
        stack = [r for k in start if k in self.skills for r in self.skills[k].requires]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            skill = self.skills.get(current)
            if skill is not None:
                stack.extend(skill.requires)
        return seen - start

    def exam_tier(self, skill_id: str) -> int:
        skill = self.skills.get(skill_id)
        return skill.exam_tier if skill is not None and skill.exam_tier is not None else 3


def next_course_prerequisites(
    catalog: Catalog, goals: Mapping[str, CourseGoal], day: date
) -> dict[str, set[str]]:
    """Courses he is taking next (a start date set, goal date not passed) -> the skills of
    other courses they require (LIB-8)."""
    out: dict[str, set[str]] = {}
    for course_id, goal in goals.items():
        if goal.starts_on is None or past_goal_date(goal, day):
            continue
        own = catalog.skills_of_course(course_id)
        out[course_id] = {
            k for k in catalog.prerequisites(own) if catalog.course_of(k) != course_id
        }
    return out


def skill_retention(
    skill_id: str,
    day: date,
    catalog: Catalog,
    goals: Mapping[str, CourseGoal],
    next_prereqs: Mapping[str, set[str]] | None = None,
) -> float:
    """Desired retention for one skill on one day: its course's, raised to 0.85 when it is
    a prerequisite of a course he is taking next (LIB-8). Unknown course: goal A."""
    course = catalog.course_of(skill_id)
    retention = course_retention(goals.get(course) if course else None, day)
    prereqs = (
        next_course_prerequisites(catalog, goals, day) if next_prereqs is None else next_prereqs
    )
    if any(skill_id in skills for skills in prereqs.values()):
        retention = max(retention, NEXT_COURSE_PREREQ_RETENTION)
    return retention


def retention_map(
    skill_ids: Sequence[str], day: date, catalog: Catalog, goals: Mapping[str, CourseGoal]
) -> dict[str, float]:
    prereqs = next_course_prerequisites(catalog, goals, day)
    return {k: skill_retention(k, day, catalog, goals, prereqs) for k in skill_ids}
