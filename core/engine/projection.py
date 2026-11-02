"""Course and exam projections (LIB-4, LIB-9).

- `project_exam`: projected exam-day recall per skill (boosters and scheduled reviews
  assumed done), the share of exam skills at Exam-level or above, a projected exam score
  and what holds it back (recall or level), plus a proposal of extra daily problems that the
  app shows and never applies silently.
- `project_load`: a goal's projected daily load ("about 14 problems, 40 minutes a day") by
  a fast seeded Monte Carlo over each skill's own review sequence, with new skills, lapses
  (relearn + reinforcement) and exam boosters.

Level factors (how much of a skill's recall turns into exam points) are starting guesses,
like the goal presets, to be tuned from his results.
"""

import math
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from core.engine.boosters import BoostTarget, TargetOutlook
from core.engine.config import AGAIN, BOOSTER_WINDOW_DAYS, GOOD
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.engine.level import rank
from core.engine.lifecycle import due_day, memory_of, review_on
from core.model import LevelName, SkillState

LEVEL_FACTOR: Mapping[LevelName | None, float] = {
    None: 0.0,
    "learning": 0.4,
    "learned": 0.75,
    "exam": 0.95,
    "mastered": 1.0,
}
PROBLEMS_PER_NEW_SKILL = 5  # worked example excluded; three to five problems (QUE-1)
EXTRA_PER_LEVEL_STEP = 2


@dataclass(frozen=True, slots=True, kw_only=True)
class ExamProjection:
    target_key: str
    days_left: int
    skills: int
    share_exam_level: float
    mean_recall: float
    projected_score: float
    target: float
    holding_back: Literal["recall", "level"] | None
    proposed_extra_per_day: int


def project_exam(
    outlook: TargetOutlook, states: Mapping[str, SkillState], *, today: date
) -> ExamProjection:
    target = outlook.target
    scope = list(target.skill_ids)
    n = max(len(scope), 1)
    days_left = max((target.day - today).days, 0)
    recalls = [outlook.recall.get(k) or 0.0 for k in scope]
    levels = [states[k].level if k in states else None for k in scope]
    factors = [LEVEL_FACTOR[lv] for lv in levels]
    score = sum(r * f for r, f in zip(recalls, factors, strict=True)) / n
    recall_loss = sum((1 - r) * f for r, f in zip(recalls, factors, strict=True)) / n
    level_loss = sum(1 - f for f in factors) / n  # 1 - r f = (1 - f) + f (1 - r)
    at_exam = sum(1 for lv in levels if rank(lv) >= rank("exam"))
    holding: Literal["recall", "level"] | None = None
    extra = 0
    if score < target.target and scope:
        holding = "recall" if recall_loss >= level_loss else "level"
        unlearned = sum(1 for k in scope if k not in states or memory_of(states[k]) is None)
        below = sum(1 for lv in levels if rank("learning") <= rank(lv) < rank("exam"))
        work = unlearned * PROBLEMS_PER_NEW_SKILL + below * EXTRA_PER_LEVEL_STEP
        extra = math.ceil(work / max(days_left, 1))
    return ExamProjection(
        target_key=target.key,
        days_left=days_left,
        skills=len(scope),
        share_exam_level=at_exam / n if scope else 0.0,
        mean_recall=sum(recalls) / n if scope else 0.0,
        projected_score=score if scope else 0.0,
        target=target.target,
        holding_back=holding,
        proposed_extra_per_day=extra,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadProjection:
    problems_per_day: float
    minutes_per_day: float
    peak_day_problems: float
    horizon_days: int
    daily: Mapping[date, float]


def project_load(
    states: Mapping[str, SkillState],
    new_skills: Sequence[str],
    *,
    today: date,
    horizon_days: int,
    retention_of: Callable[[str], float],
    adapter: FsrsAdapter,
    days: StudyDays,
    targets: Sequence[BoostTarget] = (),
    new_per_day: int = 4,
    minutes_per_problem: float = 2.5,
    runs: int = 8,
    seed: int = 0,
) -> LoadProjection:
    """Average problems a day over the horizon. Each skill's reviews are simulated with
    success drawn from FSRS's own predicted recall (Good or Again); a lapse costs a
    reinforcement problem that day and a relearning review the next."""
    end = today + timedelta(days=horizon_days)
    totals = {today + timedelta(days=i): 0.0 for i in range(horizon_days)}
    rng = random.Random(seed)  # noqa: S311 - simulation, not security
    starts: list[tuple[str, Memory | None, date]] = []
    for skill_id, state in sorted(states.items()):
        memory = memory_of(state)
        due = due_day(state, retention_of(skill_id), adapter, days)
        if memory is not None and due is not None:
            starts.append((skill_id, memory, max(due, today)))
    for i, skill_id in enumerate(new_skills):
        starts.append((skill_id, None, today + timedelta(days=i // max(new_per_day, 1))))
    by_skill: dict[str, list[BoostTarget]] = {}
    for t in sorted(targets, key=lambda t: t.at_ms):
        for k in t.skill_ids:
            by_skill.setdefault(k, []).append(t)
    for _ in range(runs):
        for skill_id, memory, first in starts:
            _simulate_skill(
                skill_id, memory, first, end, totals, rng,
                retention=retention_of(skill_id), adapter=adapter, days=days,
                targets=by_skill.get(skill_id, []),
            )  # fmt: skip
    daily = {d: v / runs for d, v in totals.items()}
    mean = sum(daily.values()) / max(horizon_days, 1)
    return LoadProjection(
        problems_per_day=mean,
        minutes_per_day=mean * minutes_per_problem,
        peak_day_problems=max(daily.values(), default=0.0),
        horizon_days=horizon_days,
        daily=daily,
    )


def _simulate_skill(
    skill_id: str,
    memory: Memory | None,
    first: date,
    end: date,
    totals: dict[date, float],
    rng: random.Random,
    *,
    retention: float,
    adapter: FsrsAdapter,
    days: StudyDays,
    targets: Sequence[BoostTarget],
) -> None:
    day = first
    if memory is None:
        if day >= end:
            return
        at = days.moment(day)
        memory = adapter.replay([(GOOD, at), (GOOD, at + 1), (GOOD, at + 2)])
        if memory is None:
            return
        totals[day] += PROBLEMS_PER_NEW_SKILL
        day = day + timedelta(days=adapter.interval_days(memory.stability, retention, None))
    for _ in range(400):
        booster = _booster_day(memory, day, targets, adapter, days)
        if booster is not None and booster < day:
            day = booster
        if day >= end:
            return
        at = days.moment(day)
        success = rng.random() < adapter.retrievability(memory, at)
        memory = review_on(adapter, memory, GOOD if success else AGAIN, at, days)
        totals[day] += 1 if success else 2  # a lapse adds the same-day reinforcement
        step = adapter.interval_days(memory.stability, retention, None) if success else 1
        day = day + timedelta(days=step)


def _booster_day(
    memory: Memory,
    next_due: date,
    targets: Sequence[BoostTarget],
    adapter: FsrsAdapter,
    days: StudyDays,
) -> date | None:
    """The first feasible booster day for the next target the scheduled review would miss."""
    last_seen = days.day_of(memory.last_review_at)
    for t in targets:
        if t.day <= last_seen:
            continue
        if next_due < t.day or adapter.retrievability(memory, t.at_ms) >= t.target:
            return None
        start = max(last_seen + timedelta(days=1), t.day - timedelta(days=BOOSTER_WINDOW_DAYS))
        d = start
        while d < t.day:
            after = review_on(adapter, memory, GOOD, days.moment(d), days)
            if adapter.retrievability(after, t.at_ms) >= t.target:
                return d
            d += timedelta(days=1)
        return t.day - timedelta(days=1)
    return None


def load_warning(loads: Sequence[LoadProjection], daily_count: int) -> bool:
    """LIB-4: all goals together exceed the daily count."""
    return sum(p.problems_per_day for p in loads) > daily_count
