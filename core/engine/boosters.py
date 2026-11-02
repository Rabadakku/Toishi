"""Exam boosters (ENG-8) and pre-course boosts (LIB-8).

Every day from 21 days before a target (an exam, or the start of a course he is taking
next), each in-scope skill's recall at the target time is predicted as if it were not
reviewed again. A skill already due before the target is left alone. For one due after it
whose predicted recall misses the target, a booster is planned inside its feasible window:
the days from which a Good review (previewed with FSRS) keeps recall at the target, up to
the day before. The window's first day is the spec's "about 0.4 x the new stability before
the exam" for a 0.95 target. Boosters are spread over their windows by load (fewest reviews
first; ties go to the earlier day, leaving room to re-plan after a failed booster).

The plan is a pure function of today's states, recomputed daily, so a failed booster
(a lapse: relearning tomorrow, which is before the exam) is re-planned automatically, and
targets are planned in date order with the projected effect of earlier boosters and reviews,
so a final's boosters build on the midterm's.
"""

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from core.engine.config import BOOSTER_WINDOW_DAYS, GOOD, PRACTICE_TEST_DAYS, PRE_COURSE_RECALL
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.engine.goals import Catalog, exam_target, next_course_prerequisites
from core.engine.lifecycle import RELEARNING, due_day, fuzz_key, memory_of, review_on
from core.model import CourseGoal, Exam, SkillState


@dataclass(frozen=True, slots=True, kw_only=True)
class BoostTarget:
    key: str  # "exam:<id>" or "course:<course id>"
    name: str
    day: date  # study day of the target
    at_ms: int  # the moment recall is predicted for
    target: float
    skill_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Booster:
    skill_id: str
    target_key: str
    day: date
    window: tuple[date, date]
    recall_without: float
    recall_with: float
    feasible: bool  # False: even the day before can't reach the target (best effort)


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetOutlook:
    """Projected recall of each in-scope skill at the target (boosters and scheduled
    reviews assumed done, rated Good); None for skills with no FSRS card yet."""

    target: BoostTarget
    recall: Mapping[str, float | None]
    left_alone: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class BoosterPlan:
    today: date
    boosters: tuple[Booster, ...] = ()
    outlooks: tuple[TargetOutlook, ...] = ()
    load: Mapping[date, int] = field(default_factory=dict)

    def due_on(self, day: date) -> list[Booster]:
        return [b for b in self.boosters if b.day == day]


def practice_tests_open(exam_day: date, today: date) -> bool:
    """ENG-8: practice tests are offered from the 21-day booster window before an exam."""
    return 0 <= (exam_day - today).days <= PRACTICE_TEST_DAYS


def booster_targets(
    exams: Iterable[Exam],
    goals: Mapping[str, CourseGoal],
    catalog: Catalog,
    *,
    today: date,
    days: StudyDays,
    window_days: int = BOOSTER_WINDOW_DAYS,
) -> list[BoostTarget]:
    """Targets within the window: exams with an exam-day target, and course starts (0.90
    for prerequisites of a course he is taking next)."""
    out: list[BoostTarget] = []
    for exam in exams:
        day = days.day_of(exam.at)
        if not 0 < (day - today).days <= window_days:
            continue
        goal = goals.get(exam.course_id) if exam.course_id else None
        target = exam_target(exam, goal, day)
        if target is None:
            continue
        scope = catalog.skills_in_sections(exam.sections)
        if not exam.sections and exam.course_id:
            scope = catalog.skills_of_course(exam.course_id)
        out.append(
            BoostTarget(
                key=f"exam:{exam.id}",
                name=exam.name,
                day=day,
                at_ms=exam.at,
                target=target,
                skill_ids=tuple(scope),
            )
        )
    prereqs = next_course_prerequisites(catalog, goals, today)
    for course_id, skills in sorted(prereqs.items()):
        start = goals[course_id].starts_on
        if start is None or not 0 < (start - today).days <= window_days:
            continue
        out.append(
            BoostTarget(
                key=f"course:{course_id}",
                name=course_id,
                day=start,
                at_ms=days.start(start),
                target=PRE_COURSE_RECALL,
                skill_ids=tuple(sorted(skills)),
            )
        )
    return sorted(out, key=lambda t: (t.at_ms, t.key))


@dataclass(slots=True)
class _Projection:
    memory: Memory
    due: date
    relearning: bool
    key: str


def plan_boosters(
    targets: Sequence[BoostTarget],
    states: Mapping[str, SkillState],
    *,
    today: date,
    retention_of: Callable[[str], float],
    adapter: FsrsAdapter,
    days: StudyDays,
    base_load: Mapping[date, int] | None = None,
    adapter_of: Callable[[str], FsrsAdapter] | None = None,
) -> BoosterPlan:
    """Boosters before each target. `adapter_of`: each skill's own parameter set
    (decision 6); None: `adapter` for every skill."""

    def model(skill_id: str) -> FsrsAdapter:
        return adapter if adapter_of is None else adapter_of(skill_id)

    projections: dict[str, _Projection] = {}
    for skill_id, state in states.items():
        memory = memory_of(state)
        due = due_day(state, retention_of(skill_id), model(skill_id), days)
        if memory is not None and due is not None:
            projections[skill_id] = _Projection(
                memory, max(due, today), state.fsrs_state == RELEARNING, fuzz_key(state)
            )
    load: Counter[date] = Counter(base_load or {})
    boosters: list[Booster] = []
    outlooks: list[TargetOutlook] = []
    for target in sorted(targets, key=lambda t: (t.at_ms, t.key)):
        last_day = target.day - timedelta(days=1)
        if last_day < today:
            continue
        left_alone: list[str] = []
        wanted: list[tuple[str, list[date], bool, float]] = []
        for skill_id in target.skill_ids:
            proj = projections.get(skill_id)
            if proj is None:
                continue
            if proj.due < target.day:
                left_alone.append(skill_id)
                _advance(proj, target.day, retention_of(skill_id), model(skill_id), days)
                continue
            without = model(skill_id).retrievability(proj.memory, target.at_ms)
            if without >= target.target:
                continue
            window = [
                d
                for d in _days(today, last_day)
                if _with_good(proj.memory, d, target, model(skill_id), days) >= target.target
            ]
            wanted.append((skill_id, window or [last_day], bool(window), without))
        for skill_id, window, feasible, without in sorted(
            wanted, key=lambda w: (len(w[1]), w[1][0], w[0])
        ):
            day = min(window, key=lambda d: (load[d], d))
            load[day] += 1
            proj = projections[skill_id]
            own = model(skill_id)
            after = review_on(own, proj.memory, GOOD, days.moment(day), days)
            boosters.append(
                Booster(
                    skill_id=skill_id,
                    target_key=target.key,
                    day=day,
                    window=(window[0], window[-1]),
                    recall_without=without,
                    recall_with=own.retrievability(after, target.at_ms),
                    feasible=feasible,
                )
            )
            proj.memory = after
            proj.relearning = False
            proj.key = f"{skill_id}|{after.last_review_at}"
            proj.due = day + timedelta(
                days=own.interval_days(after.stability, retention_of(skill_id), proj.key)
            )
        recall: dict[str, float | None] = {}
        for skill_id in target.skill_ids:
            proj = projections.get(skill_id)
            recall[skill_id] = (
                None if proj is None else model(skill_id).retrievability(proj.memory, target.at_ms)
            )
        outlooks.append(TargetOutlook(target=target, recall=recall, left_alone=tuple(left_alone)))
    return BoosterPlan(
        today=today, boosters=tuple(boosters), outlooks=tuple(outlooks), load=dict(load)
    )


def _days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _with_good(
    memory: Memory, day: date, target: BoostTarget, adapter: FsrsAdapter, days: StudyDays
) -> float:
    after = review_on(adapter, memory, GOOD, days.moment(day), days)
    return adapter.retrievability(after, target.at_ms)


def _advance(
    proj: _Projection, before: date, retention: float, adapter: FsrsAdapter, days: StudyDays
) -> None:
    """Project the scheduled reviews (rated Good) that fall before a day."""
    for _ in range(64):
        if proj.due >= before:
            return
        after = review_on(adapter, proj.memory, GOOD, days.moment(proj.due), days)
        proj.key = f"{proj.key}+"
        proj.due = proj.due + timedelta(
            days=adapter.interval_days(after.stability, retention, proj.key)
        )
        proj.memory = after
        proj.relearning = False
