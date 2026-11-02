"""Certification sittings for M2 and M3 (docs/design/wave2-planner.md section 2, design v1.3).

Practice keeps feeding the model and the certifier's posterior, but M2 and M3 certify only
through a sitting: a closed-book block of problems the student has never been served, at the
milestone tier, served consecutively in random order across its skills (role "sitting").

- **When.** A skill sits when its current milestone is M2 or M3, the model's readiness at the
  tier is at least the target, it has 2 or more practice first tries at the tier with the last
  one a success, no failed sitting in the 2 study days before today, and the model's chance of
  passing on the chosen problems is at least `SITTING_PASS_MIN` (see `pass_chance`). One
  sitting a day, at most 3 skills, earliest deadline first, never in the first 20 minutes of
  the day's expected time.
- **Pass** (judged in `core.plan.certify`): every problem right on the first try, unaided, and
  their summed valid active time at or under their summed standard time. A wrong answer or a
  slow block fails (and the skill waits 2 study days); an unknown time with every answer right
  voids the sitting (no wait).

This module holds the pure helpers: the pace and pass chances, the sitting's id, the frame of a
sitting already under way, and the practice rule.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from core.learner.types import ComponentId, Observation, Prediction, ProblemSpec
from core.plan.certify import SittingResult, first_try_success
from core.plan.config import (
    EPS,
    SIGMA_T_DEFAULT,
    SITTING_PRACTICE,
    SITTING_WAIT_DAYS,
)
from core.plan.protocol import Predictor
from core.plan.types import ServedItem


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def pace_chance(medians: Sequence[float], limits: Sequence[float], sigma: float) -> float:
    """P(the summed solve times are at most the summed limits), each time lognormal with the
    given median and log standard deviation `sigma` (design 3.3's sigma_T): the
    Fenton-Wilkinson approximation, which treats the sum as one lognormal with the same mean
    and variance:

        m_j = median_j e^(s^2/2),  v_j = median_j^2 e^(s^2) (e^(s^2) - 1),
        M = sum m_j,  V = sum v_j,  s2 = ln(1 + V / M^2),  mu = ln M - s2 / 2,
        P = Phi((ln L - mu) / sqrt(s2)),  L = sum of the limits.
    """
    if not medians:
        return 1.0
    total_limit = sum(limits)
    if total_limit <= 0.0:
        return 0.0
    if sigma <= 0.0:
        return 1.0 if sum(medians) <= total_limit + EPS else 0.0
    s2 = sigma * sigma
    grow = math.exp(s2)
    mean = sum(m * math.exp(s2 / 2.0) for m in medians)
    var = sum(m * m * grow * (grow - 1.0) for m in medians)
    if mean <= 0.0:
        return 1.0
    spread = math.log1p(var / (mean * mean))
    mu = math.log(mean) - spread / 2.0
    return normal_cdf((math.log(total_limit) - mu) / math.sqrt(spread))


@dataclass(frozen=True, slots=True)
class PassChance:
    """The model's chance of passing a skill's sitting on its chosen problems (design v1.3)."""

    accuracy: float  # the product of their calibrated first-try chances
    pace: float  # P(their summed times <= their summed T*)

    @property
    def chance(self) -> float:
        return self.accuracy * self.pace


def pass_chance(
    predictions: Sequence[Prediction], problems: Sequence[ProblemSpec], sigma: float
) -> PassChance:
    """P_pass = (product of the problems' calibrated P_j) x P(sum of times <= sum of T*), the
    time part from each problem's predicted median (`pace_chance`)."""
    accuracy = math.prod(p.p for p in predictions)
    pace = pace_chance(
        [p.median_minutes for p in predictions], [p.standard_minutes for p in problems], sigma
    )
    return PassChance(accuracy=accuracy, pace=pace)


def sigma_of[S](model: Predictor[S], state: S) -> float:
    """sigma_T, the spread of the student's log solve times: the model's `sigma_t(state)` when
    it has one (an optional part of the planner's protocol), else design 3.5's prior 0.45."""
    found = getattr(model, "sigma_t", None)
    if callable(found):
        value = float(found(state))
        if value > 0.0:
            return value
    return SIGMA_T_DEFAULT


def sitting_id(course_id: str, day: date) -> str:
    """The day's sitting (one a day per course)."""
    return f"sitting:{course_id}:{day.isoformat()}"


@dataclass(frozen=True, slots=True)
class SittingToday:
    """Today's sitting as the served items show it."""

    sitting: str | None  # its id, once a sitting item has been served today
    block: tuple[str, ...]  # its problem ids in serve order (from the served items' frame)
    served: tuple[str, ...]  # the problem ids served so far

    @property
    def started(self) -> bool:
        return self.sitting is not None

    @property
    def remaining(self) -> tuple[str, ...]:
        done = set(self.served)
        return tuple(pid for pid in self.block if pid not in done)


def sitting_today(served: Sequence[ServedItem]) -> SittingToday:
    """The day's sitting from today's served items: the first served sitting item's frame (a
    sitting item whose frame was lost leaves the sitting finished with what was served)."""
    items = [x.item for x in served if x.item.role == "sitting" and x.item.problem is not None]
    if not items:
        return SittingToday(None, (), ())
    block = next((i.sitting_block for i in items if i.sitting_block), ())
    done = tuple(i.problem.problem_id for i in items if i.problem is not None)
    return SittingToday(items[0].sitting, block or done, done)


def practice_ready(observations: Iterable[Observation], passed: Iterable[date]) -> bool:
    """At least 2 practice first tries at the tier, the last one a success. Practice is every
    first try there but those of passed sittings (a failed or void sitting's problems count as
    practice evidence)."""
    passed_days = set(passed)
    practice = [o for o in observations if not (o.role == "sitting" and o.study_day in passed_days)]
    if len(practice) < SITTING_PRACTICE:
        return False
    last = max(practice, key=lambda o: (o.at_ms, o.attempt_id))
    return first_try_success(last)


def waiting(results: Iterable[SittingResult], today: date) -> bool:
    """A failed sitting in the 2 study days before today (a void one needs no wait)."""
    return any(
        r.outcome == "fail" and 1 <= (today - r.day).days <= SITTING_WAIT_DAYS for r in results
    )


def sat_today(results: Iterable[SittingResult], today: date) -> bool:
    return any(r.day == today for r in results)


def block_limits(problems: Sequence[ProblemSpec]) -> Mapping[ComponentId, float]:
    """Each skill's time limit in a sitting: the sum of its problems' T* (design v1.3)."""
    out: dict[ComponentId, float] = {}
    for p in problems:
        out[p.main_skill] = out.get(p.main_skill, 0.0) + p.standard_minutes
    return out
