"""Certification from direct evidence (docs/design/student-model.md, sections 3.7, 3.8, with
the certification sittings of docs/design/wave2-planner.md section 2 and design v1.3).

For a skill s and tier l, a Beta posterior over s's first-try success at l:

- evidence: first tries on problems whose main skill is s, at tier l, from any role (sittings
  included); a correct, unaided first try is a success whatever its time (v1.3: accuracy only
  at every tier);
- each attempt weighs 2^(-age / 30 days), age in study days;
- prior Beta(kappa0 p, kappa0 (1 - p)) at the model's calibrated prediction p for the
  representative problems, kappa0 = 4;
- **M1 and Keep** (the untimed rule) are certified when the mean reaches the target with
  n_eff >= 3; **M2 and M3** (the sitting rule, still called `timed` for compatibility) only on
  the day of a passed sitting (pace is the sitting's: its problems right, unaided, and their
  summed time within their summed T*); n_eff 4 marks their evidence as enough to judge;
- **revoked** when the mean falls below target - 0.10 (hysteresis), for every rule.

Hysteresis needs the path, so each query replays the key's evidence day by day: on every day
with evidence, before and after adding that day's attempts, and on the query day. Between
those days nothing is added, the weights all shrink by the same factor, and the mean moves
monotonically toward the prior mean, so a revocation is never missed.
"""

from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.config import (
    DEFAULT_PRIOR,
    EPS,
    HALF_LIFE_DAYS,
    KAPPA0,
    N_EFF_TIMED,
    N_EFF_UNTIMED,
    REPRESENTATIVES_MAX,
    REVOKE_MARGIN,
    SITTING_PROBLEMS,
    TIMED_FROM_TIER,
)
from core.plan.pace import keep_tier, schedule
from core.plan.protocol import Forecast, Predict, Predictor
from core.plan.types import Course, CourseSettings, SkillInfo

PRIOR_FLOOR = 1e-6


@dataclass(frozen=True, slots=True)
class Posterior:
    alpha: float
    beta: float
    n_eff: float  # recency-weighted direct observations (the prior left out)
    prior_mean: float

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)


@dataclass(frozen=True, slots=True)
class CertState:
    posterior: Posterior
    certified: bool
    since: date | None  # the day it last became certified from evidence
    first: date | None  # the first day it became certified from evidence
    ever: bool  # certified at some point, from evidence or by assumption


def first_try_success(obs: Observation, *, timed: bool = False) -> bool:
    """The attempt's outcome for certification: a correct, unaided first try is a success,
    whatever its time; a wrong, aided or given-up one is a failure. (`timed` is accepted for
    compatibility and changes nothing: design v1.3 made every posterior accuracy only.)"""
    del timed
    return obs.correct and not obs.aided


def recency_weight(age_days: float) -> float:
    """2^(-age / 30 days)."""
    return float(2.0 ** (-age_days / HALF_LIFE_DAYS))


def n_eff_needed(*, timed: bool) -> float:
    """3 effective observations for M1 and Keep, 4 for M2 and M3 (`timed`: the M2/M3 rule)."""
    return N_EFF_TIMED if timed else N_EFF_UNTIMED


def timed_for_tier(tier: int) -> bool:
    """The rule a bare (skill, tier) query uses: M1's below tier 3, M2/M3's from tier 3."""
    return tier >= TIMED_FROM_TIER


type SittingOutcome = Literal["pass", "fail", "void"]


@dataclass(frozen=True, slots=True)
class SittingResult:
    """One skill's part of one day's sitting (its role "sitting" first tries at one tier)."""

    skill: ComponentId
    tier: int
    day: date
    outcome: SittingOutcome
    problems: int
    minutes: float | None  # their summed valid active time (None: one is unknown, or a miss)
    limit: float  # the sum of their standard times T*


def sitting_outcome(observations: Sequence[Observation]) -> SittingOutcome:
    """A skill's sitting (design v1.3): **pass** when every problem is correct on the first try
    and unaided and their summed valid active time is at or under the sum of their T*; **fail**
    when one is wrong or aided, or the summed time is over; **void** when all are right but a
    time is unknown (a pause over the limit, a Mac waking), or fewer than 2 were answered (an
    interrupted sitting): neither a pass nor a fail."""
    if any(not o.correct or o.aided for o in observations):
        return "fail"
    if len(observations) < SITTING_PROBLEMS or any(o.minutes is None for o in observations):
        return "void"
    total = sum(o.minutes or 0.0 for o in observations)
    limit = sum(o.problem.standard_minutes for o in observations)
    return "pass" if total <= limit + EPS else "fail"


def sitting_results(
    skill: ComponentId, tier: int, observations: Iterable[Observation]
) -> tuple[SittingResult, ...]:
    """The skill's sittings at the tier, one per study day, from its first tries there."""
    by_day: dict[date, list[Observation]] = defaultdict(list)
    for obs in observations:
        if obs.role == "sitting":
            by_day[obs.study_day].append(obs)
    out: list[SittingResult] = []
    for day in sorted(by_day):
        mine = by_day[day]
        known = [o.minutes for o in mine]
        minutes = None if any(m is None for m in known) else sum(m or 0.0 for m in known)
        out.append(
            SittingResult(
                skill=skill,
                tier=tier,
                day=day,
                outcome=sitting_outcome(mine),
                problems=len(mine),
                minutes=minutes,
                limit=sum(o.problem.standard_minutes for o in mine),
            )
        )
    return tuple(out)


type _Days = tuple[tuple[date, float, float], ...]  # (study day, successes, attempts)


class Certifier:
    """Direct-evidence posteriors per (skill, tier) from the observation log and model priors.

    - `observations`: every first try (any role, any day; later days than a query are
      ignored by it), sorted by time;
    - `priors[(skill, tier)]`: the model's calibrated prediction for the representative
      problems (see `model_priors`); `default_prior` stands in for missing keys;
    - `tiers[skill]`: the tiers where the skill has problems (for `level`);
    - `assumed[skill] = (tier, target)`: a mid-course start's assumed-learned skills, whose
      Keep key starts certified with its prior mean raised to at least the Keep target;
    - `today`: the default query day.
    """

    def __init__(
        self,
        observations: Iterable[Observation],
        *,
        today: date,
        target: float = 0.90,
        priors: Mapping[tuple[ComponentId, int], float] | None = None,
        tiers: Mapping[ComponentId, Collection[int]] | None = None,
        assumed: Mapping[ComponentId, tuple[int, float]] | None = None,
        default_prior: float = DEFAULT_PRIOR,
    ) -> None:
        self.today = today
        self.target = target
        self.observations: tuple[Observation, ...] = tuple(
            sorted(observations, key=lambda o: (o.at_ms, o.attempt_id))
        )
        self._priors = dict(priors or {})
        self._tiers = {k: frozenset(v) for k, v in (tiers or {}).items()}
        self._assumed = dict(assumed or {})
        self._default = default_prior
        grouped: dict[tuple[ComponentId, int], list[Observation]] = defaultdict(list)
        for obs in self.observations:
            grouped[(obs.problem.main_skill, obs.problem.tier)].append(obs)
        self._grouped = dict(grouped)
        self._days: dict[tuple[ComponentId, int], _Days] = {}
        self._sittings: dict[tuple[ComponentId, int], tuple[SittingResult, ...]] = {}
        self._runs: dict[tuple[ComponentId, int, bool, float, date, bool], CertState] = {}

    @classmethod
    def for_course(
        cls,
        observations: Iterable[Observation],
        course: Course,
        settings: CourseSettings,
        *,
        today: date,
        priors: Mapping[tuple[ComponentId, int], float] | None = None,
    ) -> Certifier:
        """A certifier with the course's tiers, target and assumed-learned skills."""
        sch = schedule(course, settings)
        skills = {s.skill_id: s for s in course.skills}
        assumed: dict[ComponentId, tuple[int, float]] = {}
        for sid in sch.assumed:
            kt = keep_tier(skills[sid], settings)
            if kt is not None:
                assumed[sid] = (kt, settings.keep_target)
        return cls(
            observations,
            today=today,
            target=settings.accuracy_target,
            priors=priors,
            tiers={s.skill_id: {p.tier for p in s.pool} for s in course.skills},
            assumed=assumed,
        )

    @classmethod
    def from_model[S](
        cls,
        model: Predictor[S],
        state: S,
        observations: Iterable[Observation],
        course: Course,
        settings: CourseSettings,
        *,
        today: date,
        now_ms: int,
        retired: Collection[str] = (),
    ) -> Certifier:
        """The planner's certifier: `for_course` with the model's priors at `now_ms`. Without
        them every prior sits at 0.5, and certifying at 0.9 takes 16 straight successes."""
        priors = model_priors(model, state, course, now_ms, retired)
        return cls.for_course(observations, course, settings, today=today, priors=priors)

    def add(self, obs: Observation) -> None:
        """Record one more first try, at or after every one already held (the session adds
        each graded first try as it happens), and drop the cached results it changes: its
        (skill, tier) evidence and runs. Equivalent to rebuilding with the longer log."""
        last = self.observations[-1] if self.observations else None
        if last is not None and (obs.at_ms, obs.attempt_id) < (last.at_ms, last.attempt_id):
            raise ValueError("Certifier.add takes first tries in time order")
        self.observations = (*self.observations, obs)
        key = (obs.problem.main_skill, obs.problem.tier)
        self._grouped.setdefault(key, []).append(obs)
        self._days.pop(key, None)
        self._sittings.pop(key, None)
        for run_key in [k for k in self._runs if k[:2] == key]:
            del self._runs[run_key]

    # ------------------------------------------------------------------ queries

    def prior(
        self,
        skill: ComponentId,
        tier: int,
        *,
        timed: bool | None = None,
        target: float | None = None,
    ) -> float:
        """The prior mean of a key: the model's prediction, raised to the Keep target for an
        assumed-learned skill's Keep key."""
        timed = timed_for_tier(tier) if timed is None else timed
        target = self.target if target is None else target
        p = self._priors.get((skill, tier), self._default)
        if self._is_assumed(skill, tier, timed, target):
            p = max(p, target)
        return min(1.0 - PRIOR_FLOOR, max(PRIOR_FLOOR, p))

    def state(
        self,
        skill: ComponentId,
        tier: int,
        today: date | None = None,
        *,
        timed: bool | None = None,
        target: float | None = None,
        before: bool = False,
    ) -> CertState:
        """The posterior and certification at the end of `today` (or, with `before`, at its
        start: that day's evidence left out)."""
        timed = timed_for_tier(tier) if timed is None else timed
        target = self.target if target is None else target
        day = self.today if today is None else today
        key = (skill, tier, timed, round(target, 9), day, not before)
        found = self._runs.get(key)
        if found is None:
            found = self._run(skill, tier, timed, target, day, include_day=not before)
            self._runs[key] = found
        return found

    def posterior(
        self,
        skill: ComponentId,
        tier: int,
        today: date | None = None,
        *,
        timed: bool | None = None,
        target: float | None = None,
        before: bool = False,
    ) -> Posterior:
        return self.state(skill, tier, today, timed=timed, target=target, before=before).posterior

    def certified(
        self,
        skill: ComponentId,
        tier: int,
        today: date | None = None,
        *,
        timed: bool | None = None,
        target: float | None = None,
    ) -> bool:
        return self.state(skill, tier, today, timed=timed, target=target).certified

    def level(self, skill: ComponentId, today: date | None = None) -> int | None:
        """The highest tier l that is certified with no lower tier holding it back (design
        3.7, critique 17). Tiers without problems are skipped. A lower tier holds the level
        back when it is uncertified and either has the evidence to be judged (n_eff at its
        threshold) or was certified before; a tier the planner never tested (tier 1 drills
        after the new block, typically) neither counts nor blocks."""
        best: int | None = None
        for tier in sorted(self._tiers.get(skill, ())):
            st = self.state(skill, tier, today)
            if st.certified:
                best = tier
                continue
            judged = st.posterior.n_eff >= n_eff_needed(timed=timed_for_tier(tier)) - EPS
            if judged or st.ever:
                break
        return best

    def sittings(
        self, skill: ComponentId, today: date | None = None, *, tier: int | None = None
    ) -> tuple[SittingResult, ...]:
        """The skill's sittings up to `today` (default: the certifier's day), by day; at one
        tier when `tier` is given."""
        day = self.today if today is None else today
        tiers = [t for s, t in self._grouped if s == skill and (tier is None or t == tier)]
        found = [r for t in tiers for r in self._sitting_results(skill, t) if r.day <= day]
        return tuple(sorted(found, key=lambda r: (r.day, r.tier)))

    # ------------------------------------------------------------------ internals

    def _is_assumed(self, skill: ComponentId, tier: int, timed: bool, target: float) -> bool:
        found = self._assumed.get(skill)
        if found is None or timed:
            return False
        return found[0] == tier and abs(found[1] - target) < EPS

    def _evidence(self, skill: ComponentId, tier: int) -> _Days:
        """Successes and attempts per study day: every first try, accuracy only (v1.3)."""
        key = (skill, tier)
        found = self._days.get(key)
        if found is not None:
            return found
        per_day: dict[date, list[float]] = {}
        for obs in self._grouped.get(key, ()):
            slot = per_day.setdefault(obs.study_day, [0.0, 0.0])
            slot[0] += 1.0 if first_try_success(obs) else 0.0
            slot[1] += 1.0
        found = tuple((d, s, n) for d, (s, n) in sorted(per_day.items()))
        self._days[key] = found
        return found

    def _sitting_results(self, skill: ComponentId, tier: int) -> tuple[SittingResult, ...]:
        key = (skill, tier)
        found = self._sittings.get(key)
        if found is None:
            found = sitting_results(skill, tier, self._grouped.get(key, ()))
            self._sittings[key] = found
        return found

    def _run(
        self,
        skill: ComponentId,
        tier: int,
        timed: bool,
        target: float,
        day: date,
        *,
        include_day: bool,
    ) -> CertState:
        prior = self.prior(skill, tier, timed=timed, target=target)
        a0, b0 = KAPPA0 * prior, KAPPA0 * (1.0 - prior)
        needed = n_eff_needed(timed=timed)
        revoke_below = target - REVOKE_MARGIN
        passed = (
            {r.day for r in self._sitting_results(skill, tier) if r.outcome == "pass"}
            if timed
            else set()
        )

        certified = self._is_assumed(skill, tier, timed, target)
        ever = certified
        since: date | None = None
        first: date | None = None
        s_w = n_w = 0.0

        def check(d: date, *, sat: bool = False) -> None:
            """`sat`: after day d's attempts, so a sitting passed that day can certify."""
            nonlocal certified, ever, since, first
            m = (a0 + s_w) / (a0 + b0 + n_w)
            if certified:
                if m < revoke_below - EPS:
                    certified = False
                return
            if timed:
                # M2/M3: only through a passed sitting, unless the evidence would revoke it.
                ok = sat and d in passed and m >= revoke_below - EPS
            else:
                ok = m >= target - EPS and n_w >= needed - EPS
            if ok:
                certified, ever, since = True, True, d
                first = first or d

        last: date | None = None
        for d, s, n in self._evidence(skill, tier):
            if d > day or (d == day and not include_day):
                break
            if last is not None:
                f = recency_weight((d - last).days)
                s_w, n_w = s_w * f, n_w * f
                check(d)  # the end of the gap, before this day's attempts
            last = d
            s_w, n_w = s_w + s, n_w + n
            check(d, sat=True)
        if last is not None and day > last:
            f = recency_weight((day - last).days)
            s_w, n_w = s_w * f, n_w * f
        check(day)
        post = Posterior(alpha=a0 + s_w, beta=b0 + (n_w - s_w), n_eff=n_w, prior_mean=prior)
        return CertState(
            posterior=post,
            certified=certified,
            since=since if certified else None,
            first=first,
            ever=ever,
        )


def representatives(
    skill: SkillInfo, tier: int, retired: Collection[str] = ()
) -> tuple[ProblemSpec, ...]:
    """Design 3.8: the skill's pool problems at the tier, at most 10, lowest problem IDs
    first, retired cards left out."""
    found = sorted(
        (p for p in skill.pool if p.tier == tier and p.card_id not in retired),
        key=lambda p: p.problem_id,
    )
    return tuple(found[:REPRESENTATIVES_MAX])


def readiness(
    predict: Predict, skill: SkillInfo, tier: int, retired: Collection[str] = ()
) -> float | None:
    """The mean calibrated prediction over the representative problems (None: no problem at
    the tier)."""
    reps = representatives(skill, tier, retired)
    if not reps:
        return None
    return sum(predict(p).p for p in reps) / len(reps)


def model_priors[S](
    model: Predictor[S],
    state: S,
    course: Course,
    at_ms: int,
    retired: Collection[str] = (),
) -> dict[tuple[ComponentId, int], float]:
    """The certification prior p for every (skill, tier) with problems: the model's
    calibrated prediction for the representative problems at `at_ms`."""
    forecast = Forecast(model, state, at_ms)
    out: dict[tuple[ComponentId, int], float] = {}
    for skill in course.skills:
        for tier in sorted({p.tier for p in skill.pool}):
            r = readiness(forecast, skill, tier, retired)
            if r is not None:
                out[(skill.skill_id, tier)] = r
    return out
