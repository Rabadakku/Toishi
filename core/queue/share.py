"""Sharing the day across courses (QUE-11..13). Pure functions.

Weight = goal (A 1.5, B 1.0, Keep 0.5) x exam urgency (1, rising to 3 over the two weeks
before an exam) x backlog (a course's due work against the other courses', clamped to
0.5..2). Carried shortfalls are reserved first (already capped at half of yesterday's
quota) and come on top of the course's usual share: then each course with due work gets
its floor, max(3, 10% of N); the rest is shared
by weight with largest-remainder rounding. A course never gets more than its due work: the
surplus goes back to the others, so the quotas add up to exactly min(N, total due work).
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from core.model import CourseGoal
from core.queue.config import (
    BACKLOG_MAX,
    BACKLOG_MIN,
    CARRY_SHARE,
    GOAL_WEIGHT,
    URGENCY_DAYS,
    URGENCY_MAX,
)


def goal_weight(goal: CourseGoal | None, day: date) -> float:
    """A custom goal weighs like the preset its retention is closest to; after the goal
    date a course is Keep (LIB-8)."""
    if goal is None:
        return GOAL_WEIGHT["A"]
    if goal.goal_date is not None and day > goal.goal_date:
        return GOAL_WEIGHT["Keep"]
    if goal.goal == "custom":
        r = goal.custom_retention or 0.80
        return GOAL_WEIGHT["A"] if r >= 0.90 else GOAL_WEIGHT["B"] if r >= 0.85 else 0.5
    return GOAL_WEIGHT[goal.goal]


def urgency(days_to_exam: int | None) -> float:
    """1, rising linearly to 3 over the two weeks before the course's next exam."""
    if days_to_exam is None or days_to_exam < 0 or days_to_exam > URGENCY_DAYS:
        return 1.0
    return 1.0 + (URGENCY_MAX - 1.0) * (URGENCY_DAYS - days_to_exam) / URGENCY_DAYS


def backlog_factors(due: Mapping[str, int]) -> dict[str, float]:
    """Each course's due work against the mean of the other courses that have due work."""
    out: dict[str, float] = {}
    for course, mine in due.items():
        others = [v for k, v in due.items() if k != course and v > 0]
        if mine <= 0 or not others:
            out[course] = 1.0
            continue
        ratio = mine / (sum(others) / len(others))
        out[course] = min(BACKLOG_MAX, max(BACKLOG_MIN, ratio))
    return out


def floor_size(n: int, min_problems: int, fraction: float) -> int:
    return max(min_problems, math.floor(fraction * n + 0.5))


def carry_over(quota: int, done: int) -> int:
    """QUE-12: yesterday's shortfall, capped at half of yesterday's quota."""
    return max(0, min(quota - done, math.floor(quota * CARRY_SHARE)))


@dataclass(frozen=True, slots=True, kw_only=True)
class CourseDemand:
    course_id: str
    goal: float  # goal_weight
    urgency: float = 1.0
    due: int = 0  # problem slots of due work (triage classes 1-6)
    carry: int = 0  # shortfall carried from yesterday (already capped)


@dataclass(frozen=True, slots=True, kw_only=True)
class Share:
    quotas: Mapping[str, int]
    weights: Mapping[str, float]
    floors: Mapping[str, int] = field(default_factory=dict)
    carried: Mapping[str, int] = field(default_factory=dict)
    free: int = 0  # slots no course had due work for

    @property
    def total(self) -> int:
        return sum(self.quotas.values())


def split(
    demands: Sequence[CourseDemand],
    n: int,
    *,
    min_problems: int = 3,
    min_fraction: float = 0.10,
) -> Share:
    """Quotas per course that add up to exactly min(n, total due work)."""
    n = max(0, n)
    due = {d.course_id: max(0, d.due) for d in demands}
    backlog = backlog_factors(due)
    weights = {d.course_id: d.goal * d.urgency * backlog[d.course_id] for d in demands}
    alloc = dict.fromkeys(due, 0)
    budget = n

    # Carried shortfalls first, then floors; by weight when they don't all fit.
    by_weight = sorted(demands, key=lambda d: (-weights[d.course_id], d.course_id))
    carried: dict[str, int] = {}
    for d in by_weight:
        take = min(max(0, d.carry), due[d.course_id], budget)
        if take:
            carried[d.course_id] = take
            alloc[d.course_id] += take
            budget -= take
    floor = floor_size(n, min_problems, min_fraction)
    floors: dict[str, int] = {}
    for d in by_weight:
        c = d.course_id
        if due[c] <= 0:
            continue
        take = min(floor, due[c] - alloc[c], budget)  # on top of any carried shortfall
        if take > 0:
            floors[c] = take
            alloc[c] += take
            budget -= take

    remaining = {c: due[c] - alloc[c] for c in due}
    _water_fill(alloc, remaining, weights, budget)
    total = sum(alloc.values())
    return Share(
        quotas=alloc,
        weights=weights,
        floors=floors,
        carried=carried,
        free=n - total,
    )


def _water_fill(
    alloc: dict[str, int],
    room: dict[str, int],
    weights: Mapping[str, float],
    budget: int,
) -> None:
    """Share `budget` by weight, each course capped at its room; the surplus of a capped
    course is shared again; largest remainders round the last pass."""
    active = {c for c, r in room.items() if r > 0 and weights.get(c, 0.0) > 0}
    if not active:  # zero weights: share evenly among courses with room
        active = {c for c, r in room.items() if r > 0}
        weights = dict.fromkeys(active, 1.0)
    while budget > 0 and active:
        total_w = sum(weights[c] for c in active)
        ideal = {c: budget * weights[c] / total_w for c in active}
        capped = [c for c in active if ideal[c] >= room[c]]
        if capped:
            for c in sorted(capped):
                give = min(room[c], budget)
                alloc[c] += give
                room[c] -= give
                budget -= give
                active.discard(c)
            continue
        base = {c: math.floor(ideal[c]) for c in active}
        for c, v in base.items():
            alloc[c] += v
            room[c] -= v
            budget -= v
        order = sorted(active, key=lambda c: (-(ideal[c] - base[c]), -weights[c], c))
        for c in order:
            if budget <= 0:
                break
            if room[c] > 0:
                alloc[c] += 1
                room[c] -= 1
                budget -= 1
        active = {c for c in active if room[c] > 0}
