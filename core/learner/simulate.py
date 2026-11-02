"""Synthetic students sampled from the model itself (design 6.1, parameter recovery).

`synthetic_course` builds a course of course and background components, with problems of
1-5 components across tiers 1-4. `simulate` samples one student's first tries and times
from the model's own generative story, with known shared parameters:

- each component has a true easiness beta_k drawn from its 3.5 prior (plus a student offset
  theta), which drifts as a random walk with variance q_drift per study day;
- a course component is recalled with its FSRS-6 recall after phi times the elapsed time
  (always, before its first event), and executed with probability
  sigma(beta_k + gamma ln(1 + C_k) + rho ln(1 + F_k) - delta_l); a background component is
  always recalled and executed with probability sigma(beta_k - delta_l);
- the first try is right when nothing slips (probability 1 - s) and every component is
  recalled and executed; the recalibration is the identity (a_l = 0, b = 1);
- the truth then learns as the model assumes: Good or Again on the component's memory (same-
  day rules on the same study day), C_k += 1 on a correct execution (0.25 after the first
  that study day), F_k += 1 on a wrong one, n_k += 1;
- a right answer takes ln T = ln T* + tau + tau_s - alpha ln(1 + nbar) + N(0, sigma_T^2),
  nbar over the problem's course components, tau_s the main skill's true offset.

The schedule is a plain mixed one: components are introduced in course order, and each
study day draws problems from introduced skills, half of them from recent ones.
"""

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Final

from core.engine.config import AGAIN, DAY_MS, GOOD
from core.engine.fsrs_adapter import FsrsAdapter
from core.learner.model import sigmoid, tier_offset
from core.learner.types import ComponentId, ComponentInfo, Observation, ProblemSpec, SharedParams

_EPOCH: Final = date(1970, 1, 1)
_HOUR_MS: Final = 3_600_000
_MINUTE_MS: Final = 60_000


@dataclass(frozen=True, slots=True)
class SyntheticCourse:
    catalog: Mapping[ComponentId, ComponentInfo]
    problems: tuple[ProblemSpec, ...]
    order: tuple[ComponentId, ...]  # course components in teaching order


def synthetic_course(
    seed: int = 0,
    *,
    course_components: int = 48,
    background_components: int = 12,
    problems_per_component: int = 8,
    minutes_per_step: float = 1.5,
    course_id: str = "synthetic",
) -> SyntheticCourse:
    """A course whose problems have 1 component at tier 1, 1-2 at tier 2, 2-4 at tier 3
    and 3-5 at tier 4: the main component, then recent earlier course components and
    background ones. T* follows design 2.4: 0.5 + m * steps + m * max(0, tier - 3)."""
    rng = random.Random(seed)  # noqa: S311 - seeded simulation, not security
    order = tuple(f"c{i:03d}" for i in range(course_components))
    background = tuple(f"bg{i:03d}" for i in range(background_components))
    catalog: dict[ComponentId, ComponentInfo] = {
        cid: ComponentInfo(cid, False, course_id) for cid in order
    }
    catalog.update({cid: ComponentInfo(cid, True, None) for cid in background})
    problems: list[ProblemSpec] = []
    for index, main in enumerate(order):
        earlier = list(order[max(0, index - 10) : index])
        for j in range(problems_per_component):
            tier = 1 + j % 4
            size = {
                1: 1,
                2: rng.choice((1, 2)),
                3: rng.randint(2, 4),
                4: rng.randint(3, 5),
            }[tier]
            size = min(size, 1 + len(earlier) + len(background))  # small courses: what exists
            components = [main]
            while len(components) < size:
                use_background = (rng.random() < 0.4 or not earlier) and background
                pool = background if use_background else earlier
                pick = rng.choice(pool)
                if pick not in components:
                    components.append(pick)
            steps = size + tier - 1
            standard = 0.5 + minutes_per_step * steps + minutes_per_step * max(0, tier - 3)
            problems.append(
                ProblemSpec(
                    problem_id=f"{main}#{j}",
                    card_id=f"{main}#{j}",
                    part=None,
                    main_skill=main,
                    components=tuple(components),
                    tier=tier,
                    steps=steps,
                    standard_minutes=standard,
                    family=main,
                )
            )
    return SyntheticCourse(catalog, tuple(problems), order)


@dataclass(frozen=True, slots=True)
class Schedule:
    attempts_per_day: int = 12
    day_off: float = 0.25  # chance that a calendar day has no study
    new_every: float = 1.5  # study days between new course components
    recent_share: float = 0.5  # share of items whose main skill is at most 7 study days old
    start: date = date(2026, 1, 5)
    session_hour: int = 18  # UTC
    minutes_between: int = 4


@dataclass(slots=True)
class _Latent:
    beta: float
    c: float = 0.0
    f: float = 0.0
    n: float = 0.0
    memory: tuple[float, float] | None = None  # (stability, difficulty)
    last_ms: int = 0
    last_day: date | None = None
    drift_day: date | None = None
    success_day: date | None = None


@dataclass(frozen=True, slots=True)
class Simulation:
    observations: tuple[Observation, ...]
    truth: SharedParams
    beta: Mapping[ComponentId, float] = field(default_factory=dict)  # starting easiness
    speed: Mapping[ComponentId, float] = field(default_factory=dict)  # true tau_s per skill


def simulate(
    course: SyntheticCourse,
    truth: SharedParams,
    attempts: int,
    seed: int,
    *,
    schedule: Schedule | None = None,
    theta: float = 0.0,
    speed_sd: float = 0.3,
) -> Simulation:
    """Sample `attempts` first tries of one student whose shared parameters are `truth`.
    The per-skill speed offsets are drawn from N(0, speed_sd^2) and centred, so tau is the
    student's overall speed."""
    plan = schedule or Schedule()
    rng = random.Random(seed)  # noqa: S311 - seeded simulation, not security
    adapter = FsrsAdapter(truth.fsrs_weights or None, fuzz=False)
    background = {cid for cid, info in course.catalog.items() if info.background}
    latent: dict[ComponentId, _Latent] = {}
    for cid in course.catalog:
        if cid in background:
            mean, var = truth.prior_background_mean, truth.prior_background_var
        else:
            mean, var = truth.prior_new_mean, truth.prior_new_var
        latent[cid] = _Latent(beta=rng.gauss(mean + theta, math.sqrt(var)))
    raw_speed = {cid: rng.gauss(0.0, speed_sd) for cid in course.order}
    centre = sum(raw_speed.values()) / len(raw_speed) if raw_speed else 0.0
    speed = {cid: v - centre for cid, v in raw_speed.items()}
    by_skill: dict[ComponentId, list[ProblemSpec]] = {}
    for problem in course.problems:
        by_skill.setdefault(problem.main_skill, []).append(problem)
    introduced_on: dict[ComponentId, int] = {}

    observations: list[Observation] = []
    day = plan.start
    study_day_index = 0
    while len(observations) < attempts:
        if rng.random() < plan.day_off:
            day += timedelta(days=1)
            continue
        count = min(len(course.order), 1 + math.floor(study_day_index / plan.new_every))
        for cid in course.order[:count]:
            introduced_on.setdefault(cid, study_day_index)
        skills = [cid for cid in course.order[:count] if cid in by_skill]
        recent = [cid for cid in skills if study_day_index - introduced_on[cid] < 7]
        used: set[str] = set()
        base_ms = (day - _EPOCH).days * DAY_MS + plan.session_hour * _HOUR_MS
        for k in range(plan.attempts_per_day):
            if len(observations) >= attempts or not skills:
                break
            pool = recent if recent and rng.random() < plan.recent_share else skills
            choices = [p for s in pool for p in by_skill[s] if p.problem_id not in used]
            if not choices:
                choices = [p for s in skills for p in by_skill[s] if p.problem_id not in used]
            if not choices:
                break
            problem = rng.choice(choices)
            used.add(problem.problem_id)
            at_ms = base_ms + k * plan.minutes_between * _MINUTE_MS
            observations.append(
                _attempt(
                    rng,
                    adapter,
                    truth,
                    latent,
                    background,
                    speed,
                    problem,
                    len(observations),
                    at_ms,
                    day,
                )
            )
        study_day_index += 1
        day += timedelta(days=1)
    start_beta = {cid: lat.beta for cid, lat in latent.items()}
    return Simulation(tuple(observations), truth, start_beta, speed)


def _attempt(
    rng: random.Random,
    adapter: FsrsAdapter,
    truth: SharedParams,
    latent: dict[ComponentId, _Latent],
    background: set[ComponentId],
    speed: Mapping[ComponentId, float],
    problem: ProblemSpec,
    attempt_id: int,
    at_ms: int,
    day: date,
) -> Observation:
    delta = tier_offset(truth, problem.tier)
    components = list(dict.fromkeys(problem.components))
    outcomes: list[tuple[ComponentId, bool, bool]] = []  # (component, recalled, executed)
    for cid in components:
        lat = latent[cid]
        if lat.drift_day is not None and day > lat.drift_day and truth.q_drift > 0.0:
            lat.beta += rng.gauss(0.0, math.sqrt(truth.q_drift * (day - lat.drift_day).days))
        lat.drift_day = day
        if cid in background:
            recalled = True
            eta = lat.beta
        else:
            if lat.memory is None:
                recalled = True
            else:
                elapsed = truth.phi * max(0, at_ms - lat.last_ms) / DAY_MS
                recalled = rng.random() < adapter.retrievability_after(elapsed, lat.memory[0])
            eta = lat.beta + truth.gamma * math.log1p(lat.c) + truth.rho * math.log1p(lat.f)
        executed = rng.random() < sigmoid(eta - delta)
        outcomes.append((cid, recalled, executed))
    correct = rng.random() >= truth.slip and all(r and e for _, r, e in outcomes)

    minutes: float | None = None
    course_parts = [cid for cid in components if cid not in background]
    if correct:
        nbar = sum(latent[c].n for c in course_parts) / len(course_parts) if course_parts else 0.0
        log_minutes = (
            math.log(problem.standard_minutes)
            + truth.tau
            + speed.get(problem.main_skill, 0.0)
            - truth.alpha * math.log1p(nbar)
            + rng.gauss(0.0, truth.sigma_t)
        )
        minutes = math.exp(log_minutes)

    for cid, recalled, executed in outcomes:
        if cid in background:
            continue
        lat = latent[cid]
        same_day = lat.last_day == day
        elapsed = truth.phi * max(0, at_ms - lat.last_ms) / DAY_MS
        lat.memory = adapter.step_fractional(
            lat.memory, GOOD if recalled else AGAIN, elapsed, same_day=same_day
        )
        lat.last_ms, lat.last_day = at_ms, day
        if recalled and executed:
            lat.c += 1.0 if lat.success_day != day else truth.same_day_weight
            lat.success_day = day
        elif recalled:
            lat.f += 1.0
        lat.n += 1.0

    return Observation(
        attempt_id=attempt_id,
        at_ms=at_ms,
        study_day=day,
        problem=problem,
        correct=correct,
        minutes=minutes,
    )
