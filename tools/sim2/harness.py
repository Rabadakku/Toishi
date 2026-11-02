"""The day-by-day loop (design 6.2): one policy, one truth student, one course.

Each day is a study day unless it is skipped (a share of days, drawn per student so both
policies skip the same days). On a study day the policy plans the day, then serves items one
at a time; the truth student answers each problem (a worked example just costs reading time)
and the policy observes the first try. The session ends when the policy has nothing more to
serve or the minutes budget is used up, whichever comes first (the item in progress
finishes).

The run lasts from the course start to the last skill's M3 deadline plus the longest
readiness offset (90 days), so every skill's readiness 30 and 90 days after M3 is measured.
The course keeps running in self-study mode after the last class (no end date, no Keep).

Recorded: the plan and what was served each day, every attempt with the policy's prediction
and the truth's chance, each change of milestone certification with the truth's readiness at
that moment, the truth's readiness at each milestone deadline, readiness snapshots after the
M3 deadline, minutes per skill and where new material was served.
"""

import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Final, Literal

from core.learner.types import ComponentId, Observation
from core.plan.types import CourseSettings
from tools.sim2.adapters import BackendKind, load_backend
from tools.sim2.common import MINUTE_MS, rng_for, session_ms
from tools.sim2.course import SimCourse, TagNoise, calc1, calc1_ch4, perturb_tags, toy
from tools.sim2.policies import BaselinePolicy, DesignPolicy, Policy
from tools.sim2.truth import Truth, make_truth

MILESTONES: Final = ("M1", "M2", "M3")
MILESTONE_DAYS: Final = {"M1": 7, "M2": 21, "M3": 35}
PACE_MILESTONES: Final = frozenset({"M2", "M3"})

type PolicyName = Literal["P0", "P1"]


@dataclass(frozen=True, slots=True)
class RunConfig:
    budget_minutes: float = 60.0
    skip_share: float = 0.15
    example_minutes: float = 3.0
    start: date = date(2027, 1, 11)  # a Monday
    horizon_days: int | None = None  # None: through the last M3 deadline + 90 days
    readiness_offsets: tuple[int, ...] = (30, 90)
    accuracy_target: float = 0.90
    target_tier: int = 4

    def settings(self, course_id: str) -> CourseSettings:
        return CourseSettings(
            course_id=course_id,
            start=self.start,
            accuracy_target=self.accuracy_target,
            target_tier=self.target_tier,
        )


@dataclass(frozen=True, slots=True)
class RunSpec:
    course: str  # "calc1-ch4", "calc1" or "toy"
    truth: str
    profile: str
    seed: int
    policy: PolicyName
    backend: BackendKind = "auto"


@dataclass(frozen=True, slots=True)
class DayRecord:
    index: int
    studied: bool
    planned_items: int = 0
    served_items: int = 0
    planned_minutes: float = 0.0
    served_minutes: float = 0.0
    budget_hit: bool = False
    roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    day: int
    skill: ComponentId
    tier: int
    role: str
    correct: bool
    predicted: float | None  # the policy's chance before answering
    p_true: float  # the truth's chance
    minutes: float
    fast: bool  # minutes <= T*


@dataclass(frozen=True, slots=True)
class CertEvent:
    skill: ComponentId
    milestone: str
    tier: int
    day: int
    certified: bool  # False: revoked
    truth: float  # true readiness at the milestone tier (with pace for M2 and M3)


@dataclass(slots=True)
class RunResult:
    spec: RunSpec
    backend: str  # "baseline", "stand-in" or "core"
    final: bool  # False: P1 ran on the stand-in
    target: float
    horizon: int
    skills: tuple[ComponentId, ...]
    intro: dict[ComponentId, int]
    first_study: dict[ComponentId, int | None]
    first_new: dict[ComponentId, int]
    first_cert: dict[tuple[ComponentId, str], int] = field(default_factory=dict)
    events: list[CertEvent] = field(default_factory=list)
    readiness: dict[tuple[ComponentId, int], tuple[float, float]] = field(default_factory=dict)
    # truth readiness at each milestone's tier (with pace for M2 and M3) at the end of its
    # deadline day: what a perfect certifier would have certified by then
    deadline_ready: dict[tuple[ComponentId, str], float] = field(default_factory=dict)
    minutes_to_m3: dict[ComponentId, float] = field(default_factory=dict)
    skill_minutes: dict[ComponentId, float] = field(default_factory=dict)
    attempts: list[AttemptRecord] = field(default_factory=list)
    days: list[DayRecord] = field(default_factory=list)
    tag_noise: TagNoise | None = None
    seconds: float = 0.0

    def deadline(self, skill: ComponentId, milestone: str) -> int:
        return self.intro[skill] + MILESTONE_DAYS[milestone]


def course_named(name: str) -> SimCourse:
    if name == "calc1":
        return calc1()
    if name == "calc1-ch4":
        return calc1_ch4()
    if name == "toy":
        return toy()
    raise ValueError(f"unknown course {name!r}")


def readiness(
    truth: Truth, sim: SimCourse, skill: ComponentId, tier: int, at_ms: int, pace: bool
) -> float:
    """The truth's mean first-try chance over the skill's pool at `tier` (real tags);
    with `pace`, the chance of a correct answer within the standard time."""
    pool = sim.true_pools[skill].get(tier, ())
    if not pool:
        return 0.0
    total = 0.0
    for spec in pool:
        p = truth.p_correct(spec, at_ms)
        total += p * truth.p_fast(spec) if pace else p
    return total / len(pool)


def run(spec: RunSpec, config: RunConfig | None = None) -> RunResult:
    config = config or RunConfig()
    clock = time.perf_counter()
    base = course_named(spec.course)
    view = perturb_tags(base) if spec.truth == "f-tags" else base
    settings = config.settings(view.course.course_id)
    backend = load_backend(spec.backend)
    intro_dates = backend.intro_dates(view.course, settings)
    truth = make_truth(spec.truth, spec.profile, spec.seed, base, config.start)
    policy: Policy
    if spec.policy == "P1":
        policy = DesignPolicy(view, settings, backend, spec.seed)
    else:
        policy = BaselinePolicy(view, settings, intro_dates, spec.seed)
    skills = view.skill_ids
    intro = {s: (intro_dates[s] - config.start).days for s in skills}
    last_m3 = max(intro.values()) + MILESTONE_DAYS["M3"]
    horizon = config.horizon_days or last_m3 + max(config.readiness_offsets, default=0) + 1
    skips = rng_for("skips", spec.course, spec.truth, spec.profile, spec.seed)
    studied = [skips.random() >= config.skip_share for _ in range(horizon)]
    first_study = {
        s: next((i for i in range(intro[s], horizon) if studied[i]), None) for s in skills
    }
    result = RunResult(
        spec=spec,
        backend=policy.backend,
        final=spec.policy == "P0" or backend.final,
        target=config.accuracy_target,
        horizon=horizon,
        skills=skills,
        intro=intro,
        first_study=first_study,
        first_new={},
        tag_noise=view.tag_noise,
    )
    snapshots: dict[int, list[tuple[ComponentId, int]]] = {}
    for s in skills:
        for offset in config.readiness_offsets:
            when = intro[s] + MILESTONE_DAYS["M3"] + offset
            if when < horizon:
                snapshots.setdefault(when, []).append((s, offset))
    tiers = {"M1": 2, "M2": 3, "M3": config.target_tier}
    status: dict[tuple[ComponentId, str], bool] = {}
    minutes_by_skill = dict.fromkeys(skills, 0.0)
    attempt_id = 0
    for i in range(horizon):
        day = config.start + timedelta(days=i)
        now = session_ms(day)
        for s, offset in snapshots.get(i, ()):
            acc = readiness(truth, base, s, config.target_tier, now, pace=False)
            fast = readiness(truth, base, s, config.target_tier, now, pace=True)
            result.readiness[(s, offset)] = (acc, fast)
        if not studied[i]:
            result.days.append(DayRecord(i, studied=False))
        else:
            plan = policy.start_day(day, now)
            served = 0
            spent_today = 0.0
            roles: list[str] = []
            while spent_today < config.budget_minutes:
                item = policy.next_item(day, now)
                if item is None:
                    break
                if item.problem is None:
                    spent = config.example_minutes
                    policy.observe(item, None, spent)
                else:
                    shown = item.problem
                    real = base.true_specs[shown.problem_id]
                    predicted = policy.predict(shown, now)
                    p_true = truth.p_correct(real, now)
                    answer = truth.answer(real, now, day)
                    attempt_id += 1
                    obs = Observation(
                        attempt_id=attempt_id,
                        at_ms=now,
                        study_day=day,
                        problem=shown,
                        correct=answer.correct,
                        aided=False,
                        matched_wrong=answer.matched_wrong,
                        minutes=answer.minutes if answer.correct else None,
                        role=item.role,
                    )
                    spent = answer.minutes
                    policy.observe(item, obs, spent)
                    result.attempts.append(
                        AttemptRecord(
                            day=i,
                            skill=item.skill_id,
                            tier=shown.tier,
                            role=item.role,
                            correct=answer.correct,
                            predicted=predicted,
                            p_true=p_true,
                            minutes=answer.minutes,
                            fast=answer.minutes <= shown.standard_minutes,
                        )
                    )
                if item.role == "new" and item.skill_id not in result.first_new:
                    result.first_new[item.skill_id] = i
                minutes_by_skill[item.skill_id] = minutes_by_skill.get(item.skill_id, 0.0) + spent
                spent_today += spent
                now += round(spent * MINUTE_MS)
                served += 1
                roles.append(item.role)
            policy.end_day(day, now)
            result.days.append(
                DayRecord(
                    index=i,
                    studied=True,
                    planned_items=len(plan.items),
                    served_items=served,
                    planned_minutes=plan.minutes,
                    served_minutes=spent_today,
                    budget_hit=spent_today >= config.budget_minutes,
                    roles=tuple(roles),
                )
            )
        for s in skills:
            if intro[s] > i:
                continue
            reached = True
            for m in MILESTONES:
                if i == intro[s] + MILESTONE_DAYS[m]:
                    result.deadline_ready[(s, m)] = readiness(
                        truth, base, s, tiers[m], now, pace=m in PACE_MILESTONES
                    )
                reached = reached and policy.certified(s, tiers[m], day)
                if reached == status.get((s, m), False):
                    continue
                status[(s, m)] = reached
                value = readiness(truth, base, s, tiers[m], now, pace=m in PACE_MILESTONES)
                result.events.append(CertEvent(s, m, tiers[m], i, reached, value))
                if reached and (s, m) not in result.first_cert:
                    result.first_cert[(s, m)] = i
                    if m == "M3":
                        result.minutes_to_m3[s] = minutes_by_skill[s]
    result.skill_minutes = minutes_by_skill
    result.seconds = time.perf_counter() - clock
    return result
