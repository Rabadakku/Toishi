"""The component student model (docs/design/student-model.md v1.1, sections 3.1-3.6, 3.10).

A pure function of the attempt log: `replay(params, observations)` gives exactly the state
that `update` gives when applied to each observation in (at_ms, attempt_id) order (C3).
Nothing here reads a clock or does I/O. Implementation choices where the design left room
are recorded in docs/design/student-model-impl-notes.md.

Prediction for problem j at tier l with components K_j (3.2, 3.3):

    eta_k    = beta_k + gamma ln(1 + C_k) + rho ln(1 + F_k)    (background: beta_k)
    e_k      = sigma((mu_eta - delta_l) / sqrt(1 + pi v_k / 8))
    R_k      = FSRS-6 recall after phi * (t - last) days      (1: background, never practised)
    q_k      = e_k R_k
    P_raw    = (1 - s) prod q_k
    P        = sigma(a_l + b logit P_raw)
    median_j = T*_j exp(tau + tau_s - alpha ln(1 + nbar_j))   (nbar over course components)

Update after a first try (3.4): failure blame b_k (pinned by a matched wrong answer), the
memory share m_k, then per course component the FSRS Good/Again mixture matched at 7 days,
the soft counts, and one Newton step of the execution posterior; per background component
the execution step only. A timed success feeds the per-skill speed offset tau_s.
"""

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date
from typing import TYPE_CHECKING, Final

from core.engine.config import AGAIN, DAY_MS, GOOD
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import STABILITY_MAX, FsrsAdapter
from core.learner.types import (
    CALIBRATION_TIERS,
    ComponentId,
    ComponentInfo,
    ComponentState,
    MemoryState,
    Observation,
    Prediction,
    ProblemSpec,
    SharedParams,
    StudentState,
    UpdateRecord,
)

if TYPE_CHECKING:
    from core.learner.refit import RefitDecision

MATCH_HORIZON_DAYS: Final = 7.0  # S' matches the mixture's recall 7 days ahead (3.4)
SPEED_SHRINKAGE: Final = 5.0  # tau_s = sum of residuals / (count + 5) (3.3)
THETA_MIN_ATTEMPTS: Final = 3  # components that inform theta-hat (3.5)
THETA_SHRINKAGE: Final = 20.0  # theta-hat shrunk by n / (n + 20) (3.5)
TIERS: Final = range(1, CALIBRATION_TIERS + 1)

_PROBIT: Final = math.pi / 8.0  # uncertainty adjustment sigma(mu / sqrt(1 + pi v / 8))
_TINY: Final = 1e-300  # floor for denominators that only vanish on impossible outcomes
_LOGIT_CLAMP: Final = 1e-15  # P_raw is clamped into [eps, 1 - eps] before the logit


def order_key(obs: Observation) -> tuple[int, int]:
    """Replay order: time, then attempt id for ties (C3)."""
    return obs.at_ms, obs.attempt_id


def is_success(obs: Observation) -> bool:
    """A correct first try, unaided (3.4). A hint, the solution or a give-up first is a miss."""
    return obs.correct and not obs.aided


def is_timed(obs: Observation) -> bool:
    """A success with a valid active time on a problem with a standard time: it feeds the
    time model (3.3, 3.4)."""
    minutes = obs.minutes
    return (
        is_success(obs)
        and minutes is not None
        and math.isfinite(minutes)
        and minutes > 0.0
        and math.isfinite(obs.problem.standard_minutes)
        and obs.problem.standard_minutes > 0.0
    )


def sigmoid(x: float) -> float:
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def logit(p: float) -> float:
    p = min(max(p, _LOGIT_CLAMP), 1.0 - _LOGIT_CLAMP)
    return math.log(p / (1.0 - p))


def tier_offset(params: SharedParams, tier: int) -> float:
    """delta_l: 0 for tiers 1-3, delta4 and delta5 above (3.2)."""
    if tier not in TIERS:
        raise ValueError(f"tier must be 1..{CALIBRATION_TIERS}, got {tier}")
    if tier == 4:
        return params.delta4
    if tier == 5:
        return params.delta5
    return 0.0


def check_params(params: SharedParams) -> None:
    """Raise ValueError for shared parameters the model cannot use."""
    problems = []
    if not 0.0 <= params.slip < 1.0:
        problems.append("slip must be in [0, 1)")
    if not params.phi > 0.0:
        problems.append("phi must be positive")
    if not params.sigma_t > 0.0:
        problems.append("sigma_t must be positive")
    if len(params.calib_a) != CALIBRATION_TIERS:
        problems.append(f"calib_a needs {CALIBRATION_TIERS} values")
    if not 0.0 <= params.kappa <= 1.0:
        problems.append("kappa must be in [0, 1]")
    if not 0.0 <= params.same_day_weight <= 1.0:
        problems.append("same_day_weight must be in [0, 1]")
    if not params.q_drift >= 0.0:
        problems.append("q_drift must be >= 0")
    if not (params.prior_new_var > 0.0 and params.prior_background_var > 0.0):
        problems.append("prior variances must be positive")
    values = (
        params.slip,
        params.delta4,
        params.delta5,
        *params.calib_a,
        params.calib_b,
        params.phi,
        params.tau,
        params.sigma_t,
        params.gamma,
        params.rho,
        params.alpha,
        params.prior_new_mean,
        params.prior_background_mean,
    )
    if not all(math.isfinite(v) for v in values):
        problems.append("parameters must be finite")
    if problems:
        raise ValueError("bad shared parameters: " + "; ".join(problems))


def mix_memory(
    adapter: FsrsAdapter,
    good: tuple[float, float],
    again: tuple[float, float],
    r: float,
    horizon_days: float,
) -> tuple[float, float]:
    """The collapsed FSRS state of a Good/Again mixture with recall probability r (3.4).

    D' = r D_good + (1 - r) D_again; S' is chosen so that recall `horizon_days` (FSRS time)
    ahead equals r R(S_good) + (1 - r) R(S_again). r = 1 and r = 0 return the Good and the
    Again state themselves, so a certain outcome is exactly FSRS."""
    if r >= 1.0:
        return good
    if r <= 0.0:
        return again
    difficulty = r * good[1] + (1.0 - r) * again[1]
    target = r * adapter.retrievability_after(horizon_days, good[0]) + (
        1.0 - r
    ) * adapter.retrievability_after(horizon_days, again[0])
    per_unit = adapter.elapsed_for(target, 1.0)  # days for recall to reach target at S = 1
    if per_unit <= 0.0:
        return STABILITY_MAX, difficulty
    return min(horizon_days / per_unit, STABILITY_MAX), difficulty


def failure_step(a: float, s: float) -> tuple[float, float]:
    """Score and clipped observed information of L(eta) = 1 - a sigma(eta) at sigma = s
    (3.4, failure): g = -u'/(1 - u), h = max(0, [u''(1 - u) + u'^2] / (1 - u)^2) with
    u = a s, u' = a s (1 - s), u'' = a s (1 - s)(1 - 2 s)."""
    u = a * s
    rest = max(1.0 - u, _TINY)
    du = u * (1.0 - s)
    d2u = du * (1.0 - 2.0 * s)
    g = -du / rest
    h = (d2u * rest + du * du) / (rest * rest)
    return g, max(0.0, h)


def success_step(s: float) -> tuple[float, float]:
    """Score and information of a success at sigma = s (3.4): exact, the likelihood
    factorizes."""
    return 1.0 - s, s * (1.0 - s)


@dataclass(slots=True)
class _Term:
    """One component's part of a prediction, with the state it was computed from."""

    cid: ComponentId
    comp: ComponentState  # the stored state, or a fresh prior that predict() does not store
    background: bool
    var: float  # posterior variance with the drift up to the prediction's study day
    sigma: float  # sigma(mu_eta - delta), no uncertainty adjustment (the Newton step's)
    e: float  # execution, uncertainty-adjusted
    r: float  # memory
    q: float  # e * r


@dataclass(frozen=True, slots=True)
class _Time:
    log_base: float  # ln T* - alpha ln(1 + nbar)
    log_median: float  # log_base + tau + tau_s


@dataclass(frozen=True, slots=True)
class TimedAttempt:
    """A timed success as the time model sees it: x = ln T - ln T* + alpha ln(1 + nbar),
    which tau + tau_s + noise explain (3.3). `index` is its position in replay order."""

    index: int
    skill: ComponentId
    x: float


class StudentModel:
    """The student model over a component catalog (design section 8).

    Components missing from the catalog are course components (design 3.9: a problem with
    no skill tag is its own single component). `day_of` maps an instant to its study day,
    for predictions made without one (the drift of the execution variance counts study
    days); it defaults to UTC days with the 4 AM rollover, as FsrsAdapter does."""

    def __init__(
        self,
        catalog: Mapping[ComponentId, ComponentInfo],
        *,
        day_of: Callable[[int], date] | None = None,
    ) -> None:
        self.catalog: dict[ComponentId, ComponentInfo] = dict(catalog)
        self._background = frozenset(cid for cid, info in catalog.items() if info.background)
        self._day_of = day_of or StudyDays(UTC).day_of
        self._adapters: dict[tuple[float, ...], FsrsAdapter] = {}

    # ------------------------------------------------------------------ public API

    def is_background(self, component: ComponentId) -> bool:
        return component in self._background

    def new_state(self, params: SharedParams) -> StudentState:
        check_params(params)
        return StudentState(params=params)

    def copy(self, state: StudentState) -> StudentState:
        """A deep copy, for what-if questions."""
        return replace(
            state,
            components={cid: _copy_component(c) for cid, c in state.components.items()},
            skill_speed=dict(state.skill_speed),
        )

    def predict(
        self,
        state: StudentState,
        problem: ProblemSpec,
        at_ms: int,
        *,
        study_day: date | None = None,
    ) -> Prediction:
        """The first-try prediction for `problem` at `at_ms`. Changes nothing.

        `study_day` is the study day of `at_ms` (for the variance drift); without it the
        model's own calendar decides."""
        day = self._day_of(at_ms) if study_day is None else study_day
        terms = self._terms(state, problem, at_ms, day, store=False)
        prediction, _ = self._prediction(state, problem, terms)
        return prediction

    def update(self, state: StudentState, obs: Observation) -> UpdateRecord:
        """Update `state` with one first try (3.4) and return what was predicted before it,
        the blame and the memory shares."""
        params = state.params
        problem = obs.problem
        day = obs.study_day
        terms = self._terms(state, problem, obs.at_ms, day, store=True)
        prediction, timing = self._prediction(state, problem, terms)
        success = is_success(obs)
        cids = tuple(t.cid for t in terms)
        kappa = params.kappa

        matched: ComponentId | None = None
        if success:
            blame = [0.0] * len(terms)
        else:
            denominator = max(1.0 - prediction.p_raw, _TINY)
            blame = [(1.0 - t.q) / denominator for t in terms]
            matched = matched_component(problem, obs.matched_wrong)
            if matched is not None and matched in cids:
                blame = [
                    kappa + (1.0 - kappa) * b if cid == matched else (1.0 - kappa) * b
                    for cid, b in zip(cids, blame, strict=True)
                ]
            else:
                matched = None
        shares = [memory_share(t.e, t.r) if not t.background else 0.0 for t in terms]

        others = _products_without([t.q for t in terms])
        keep = 1.0 - params.slip
        adapter = self._adapter(params)
        horizon = MATCH_HORIZON_DAYS * params.phi
        for i, t in enumerate(terms):
            comp = t.comp
            b = blame[i]
            if not t.background:
                if comp.today != day:
                    comp.today = day
                    comp.successes_today = 0
                weight = 1.0 if comp.successes_today == 0 else params.same_day_weight
                m = shares[i]
                comp.memory = self._remember(
                    adapter, comp.memory, 1.0 - b * m, obs.at_ms, day, params.phi, horizon
                )
                comp.c += (1.0 - b) * weight
                comp.f += b * (1.0 - m)
            # Execution posterior: one Newton step at the posterior mean, from the counts and
            # memory in force when the problem was answered (the prediction's).
            if success:
                g, h = success_step(t.sigma)
            else:
                g, h = failure_step(keep * t.r * others[i], t.sigma)
                if matched is not None:
                    # A matched wrong answer: with probability kappa it is k*'s own error and
                    # every other component was right; otherwise an ordinary miss (3.4).
                    if t.cid == matched:
                        g_match, h_match = failure_step(t.r, t.sigma)
                    else:
                        g_match, h_match = success_step(t.sigma)
                    g = kappa * g_match + (1.0 - kappa) * g
                    h = kappa * h_match + (1.0 - kappa) * h
            comp.var = 1.0 / (1.0 / t.var + h)
            comp.mu += comp.var * g
            comp.attempts += 1
            if not t.background:
                comp.n += 1.0
                if success:
                    comp.successes_today += 1

        minutes = obs.minutes
        if is_timed(obs) and minutes is not None:
            self._time_update(state, problem.main_skill, math.log(minutes), timing)
        state.theta_hat = self._theta_hat(state)
        state.last_at_ms = obs.at_ms
        return UpdateRecord(
            prediction=prediction,
            blame=tuple(zip(cids, blame, strict=True)),
            memory_share=tuple(zip(cids, shares, strict=True)),
            attempt_id=obs.attempt_id,
        )

    def replay(
        self, params: SharedParams, observations: Iterable[Observation]
    ) -> tuple[StudentState, list[UpdateRecord]]:
        """The state after every observation, in (at_ms, attempt_id) order, from the priors
        (3.10). Equal to incremental `update` calls in that order."""
        state = self.new_state(params)
        records = [self.update(state, obs) for obs in sorted(observations, key=order_key)]
        return state, records

    def refit(self, observations: Sequence[Observation], current: SharedParams) -> RefitDecision:
        """MAP refit of the shared parameters with the adoption rule of 3.6
        (`core.learner.refit.refit` with its defaults)."""
        from core.learner.refit import refit  # refit.py builds on this module

        return refit(self, observations, current)

    def time_attempts(
        self, alpha: float, observations: Iterable[Observation]
    ) -> list[TimedAttempt]:
        """The time model's inputs for the timed successes, in replay order. Only alpha
        enters them: the practice counts n_k count attempts, whatever the parameters."""
        practice: dict[ComponentId, float] = {}
        out: list[TimedAttempt] = []
        for index, obs in enumerate(sorted(observations, key=order_key)):
            course = [c for c in _unique(obs.problem.components) if c not in self._background]
            minutes = obs.minutes
            if is_timed(obs) and minutes is not None:
                nbar = sum(practice.get(c, 0.0) for c in course) / len(course) if course else 0.0
                problem = obs.problem
                log_base = math.log(problem.standard_minutes) - alpha * math.log1p(nbar)
                out.append(TimedAttempt(index, problem.main_skill, math.log(minutes) - log_base))
            for c in course:
                practice[c] = practice.get(c, 0.0) + 1.0
        return out

    # ------------------------------------------------------------------ internals

    def _adapter(self, params: SharedParams) -> FsrsAdapter:
        weights = params.fsrs_weights
        adapter = self._adapters.get(weights)
        if adapter is None:
            adapter = FsrsAdapter(weights or None, fuzz=False)
            self._adapters[weights] = adapter
        return adapter

    def _prior(self, params: SharedParams, theta: float, background: bool) -> ComponentState:
        if background:
            return ComponentState(
                mu=params.prior_background_mean + theta, var=params.prior_background_var
            )
        return ComponentState(mu=params.prior_new_mean + theta, var=params.prior_new_var)

    def _terms(
        self,
        state: StudentState,
        problem: ProblemSpec,
        at_ms: int,
        day: date,
        *,
        store: bool,
    ) -> list[_Term]:
        params = state.params
        delta = tier_offset(params, problem.tier)
        adapter = self._adapter(params)
        terms: list[_Term] = []
        for cid in _unique(problem.components):
            background = cid in self._background
            comp = state.components.get(cid)
            if comp is None:
                comp = self._prior(params, state.theta_hat, background)
                if store:
                    comp.last_var_day = day
                    state.components[cid] = comp
            var = comp.var
            if comp.last_var_day is None:
                if store:
                    comp.last_var_day = day
            else:
                days = (day - comp.last_var_day).days
                if days > 0:  # drift between study days (3.4)
                    var += params.q_drift * days
                    if store:
                        comp.var = var
                        comp.last_var_day = day
            if background:
                mu_eta = comp.mu
            else:
                mu_eta = (
                    comp.mu + params.gamma * math.log1p(comp.c) + params.rho * math.log1p(comp.f)
                )
            x = mu_eta - delta
            e = sigmoid(x / math.sqrt(1.0 + _PROBIT * var))
            memory = None if background else comp.memory
            if memory is None:
                r = 1.0
            else:
                elapsed = params.phi * max(0, at_ms - memory.last_ms) / DAY_MS
                r = adapter.retrievability_after(elapsed, memory.stability)
            terms.append(_Term(cid, comp, background, var, sigmoid(x), e, r, e * r))
        return terms

    def _prediction(
        self, state: StudentState, problem: ProblemSpec, terms: Sequence[_Term]
    ) -> tuple[Prediction, _Time]:
        params = state.params
        p_raw = 1.0 - params.slip
        for t in terms:
            p_raw *= t.q
        p = sigmoid(params.calib_a[problem.tier - 1] + params.calib_b * logit(p_raw))

        practice = [t.comp.n for t in terms if not t.background]
        nbar = sum(practice) / len(practice) if practice else 0.0
        total, count = state.skill_speed.get(problem.main_skill, (0.0, 0))
        tau_s = total / (count + SPEED_SHRINKAGE)
        exponent = params.tau + tau_s - params.alpha * math.log1p(nbar)
        standard = problem.standard_minutes
        if math.isfinite(standard) and standard > 0.0:
            median = standard * math.exp(exponent)
            log_base = math.log(standard) - params.alpha * math.log1p(nbar)
            timing = _Time(log_base, log_base + params.tau + tau_s)
        else:  # no standard time: no time prediction
            median = 0.0
            timing = _Time(0.0, 0.0)
        prediction = Prediction(
            p=p,
            p_raw=p_raw,
            q=tuple((t.cid, t.q) for t in terms),
            e=tuple((t.cid, t.e) for t in terms),
            r=tuple((t.cid, t.r) for t in terms),
            median_minutes=median,
            pace_ok=median <= standard,
        )
        return prediction, timing

    def _remember(
        self,
        adapter: FsrsAdapter,
        memory: MemoryState | None,
        r: float,
        at_ms: int,
        day: date,
        phi: float,
        horizon: float,
    ) -> MemoryState:
        """FSRS-6 Good/Again post-states (same-day rules on the same study day), mixed by
        the recall probability r and matched at the horizon (3.4)."""
        if memory is None:
            good = adapter.step_fractional(None, GOOD, 0.0, same_day=False)
            again = good if r >= 1.0 else adapter.step_fractional(None, AGAIN, 0.0, same_day=False)
        else:
            previous = (memory.stability, memory.difficulty)
            same_day = memory.last_day == day
            elapsed = phi * max(0, at_ms - memory.last_ms) / DAY_MS
            good = (
                previous
                if r <= 0.0
                else adapter.step_fractional(previous, GOOD, elapsed, same_day=same_day)
            )
            again = (
                good
                if r >= 1.0
                else adapter.step_fractional(previous, AGAIN, elapsed, same_day=same_day)
            )
        stability, difficulty = mix_memory(adapter, good, again, r, horizon)
        return MemoryState(stability, difficulty, at_ms, day)

    def _time_update(
        self, state: StudentState, skill: ComponentId, log_minutes: float, timing: _Time
    ) -> None:
        """A timed success feeds the skill's speed offset and the running residual
        statistics of the time predictions (3.3, 3.4)."""
        total, count = state.skill_speed.get(skill, (0.0, 0))
        residual = log_minutes - timing.log_base - state.params.tau
        state.skill_speed[skill] = (total + residual, count + 1)
        z = log_minutes - timing.log_median
        mean, m2, n = state.time_stats
        n += 1
        delta = z - mean
        mean += delta / n
        state.time_stats = (mean, m2 + delta * (z - mean), n)

    def _theta_hat(self, state: StudentState) -> float:
        """Precision-weighted mean of (mu_k - prior mean) over components with 3 or more
        attempts, shrunk by n / (n + 20) (3.5)."""
        params = state.params
        weight = total = 0.0
        n = 0
        for cid, comp in state.components.items():
            if comp.attempts >= THETA_MIN_ATTEMPTS:
                prior = (
                    params.prior_background_mean
                    if cid in self._background
                    else params.prior_new_mean
                )
                w = 1.0 / comp.var
                weight += w
                total += w * (comp.mu - prior)
                n += 1
        if n == 0:
            return 0.0
        return n / (n + THETA_SHRINKAGE) * total / weight


def matched_component(problem: ProblemSpec, matched_wrong: int | None) -> ComponentId | None:
    """The component named by the matched `wrong:` line, if it names one."""
    if matched_wrong is None:
        return None
    for index, component in problem.wrong_components:
        if index == matched_wrong:
            return component
    return None


def memory_share(e: float, r: float) -> float:
    """m = (1 - R) / (1 - e R): the probability that memory failed given that the component
    failed (3.4)."""
    if r >= 1.0:
        return 0.0
    return (1.0 - r) / max(1.0 - e * r, _TINY)


def _unique(components: Iterable[ComponentId]) -> list[ComponentId]:
    return list(dict.fromkeys(components))


def _products_without(values: Sequence[float]) -> list[float]:
    """For each i, the product of all values except the i-th (prefix and suffix products)."""
    n = len(values)
    prefix = [1.0] * (n + 1)
    for i, v in enumerate(values):
        prefix[i + 1] = prefix[i] * v
    out = [1.0] * n
    suffix = 1.0
    for i in range(n - 1, -1, -1):
        out[i] = prefix[i] * suffix
        suffix *= values[i]
    return out


def _copy_component(comp: ComponentState) -> ComponentState:
    memory = None if comp.memory is None else replace(comp.memory)
    return replace(comp, memory=memory)
