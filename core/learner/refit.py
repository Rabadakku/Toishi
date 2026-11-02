"""MAP refit of the shared parameters (docs/design/student-model.md v1.1, section 3.6).

When the log has grown enough since the last refit, or the predictions have drifted
(`refit_due`, `calibration_drift`), or the student asks (Refit now), the slip s, delta4,
the per-tier recalibration (a_1..a_5, b), phi, tau and sigma_T are refit by MAP:

- A candidate parameter set means "the filter run with these shared parameters". Its
  objective is the prequential log-likelihood of the first 80% of the attempts (each first
  try predicted by the filter before it sees it) plus the log prior of section 3.5.
- The search is a bounded coordinate (pattern) search in plain Python.
- The candidate and the current set are each scored by re-running the filter over the whole
  log and taking the held-out log loss on the most recent 20% (a time-series split).

The refit parameters form two separable blocks. The accuracy block (s, delta4, a_l, b, phi)
moves only the first-try predictions; the time block (tau, sigma_T) moves only the time
predictions. An attempt's held-out log loss is the binary log loss of its first try plus,
for a timed success, the negative log density of its log time under the time model. Each
block is adopted only if it improves its held-out loss by at least 0.003 nats per attempt
and the paired per-attempt differences give a one-sided bootstrap p < 0.1 (seeded,
deterministic); otherwise the current values stay. See student-model-impl-notes.md.
"""

import hashlib
import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Final

from core.learner.model import (
    SPEED_SHRINKAGE,
    StudentModel,
    TimedAttempt,
    is_success,
    is_timed,
    logit,
    order_key,
    sigmoid,
)
from core.learner.types import CALIBRATION_TIERS, ComponentId, Observation, SharedParams

HELD_OUT_SHARE: Final = 0.2
ADOPT_MARGIN: Final = 0.003  # nats per attempt
ADOPT_P: Final = 0.1
MIN_HELD_OUT: Final = 30  # fewer held-out attempts: report the candidate, adopt nothing
# When a refit is due (3.6): on evidence, not the calendar. A fit of k parameters on n
# attempts has an expected excess log loss of about k/(2n) nats per attempt, so a refit pays
# when the log has grown by a fixed fraction since the last one. With growth 1.5 the stale
# fit costs at most 0.25 k/n per attempt, under the adoption margin from n = 750 (k = 9).
REFIT_FIRST_ATTEMPTS: Final = 150  # the first refit: MIN_HELD_OUT attempts held out at 20%
REFIT_GROWTH: Final = 1.5  # later ones: the log has grown by half since the last refit ...
REFIT_MAX_NEW: Final = 1_000  # ... or by this many attempts (slow drift)
DRIFT_MIN_ATTEMPTS: Final = 50  # the calibration check needs this many predictions ...
DRIFT_Z: Final = 3.0  # ... and calls drift beyond this many standard errors
BOOTSTRAP_SAMPLES: Final = 2000
BOOTSTRAP_SEED: Final = 20_261_102
MAX_EVALUATIONS: Final = 600  # objective evaluations per block

# Section 3.5 priors.
SLIP_PRIOR: Final = (0.4, 19.6)  # Beta(alpha, beta): mean 0.02, v1.1's strength (audit 2026-11-02)
DELTA4_PRIOR: Final = (0.3, 0.3)  # normal (mean, sd)
CALIB_A_PRIOR: Final = (0.0, 0.5)
CALIB_B_PRIOR: Final = (1.0, 0.2)
LOG_PHI_PRIOR: Final = (-2.995732273553991, 0.5)  # ln 0.05 (audit 2026-11-02)
TAU_PRIOR: Final = (math.log(2.0), 0.5)
# 3.5 gives sigma_T only a value (0.45); its spread is ours: log sigma_T ~ N(ln 0.45, 0.5^2).
LOG_SIGMA_T_PRIOR: Final = (math.log(0.45), 0.5)

_HALF_LOG_2PI: Final = 0.5 * math.log(2.0 * math.pi)

ACCURACY_PARAMETERS: Final = ("slip", "delta4", "calib_a", "calib_b", "phi")
TIME_PARAMETERS: Final = ("tau", "sigma_t")


@dataclass(frozen=True, slots=True)
class Coordinate:
    """One search coordinate: bounds, first step and the step at which it stops."""

    name: str
    low: float
    high: float
    step: float
    tolerance: float

    def clip(self, value: float) -> float:
        return min(max(value, self.low), self.high)


# Accuracy coordinates: logit s, delta4, ln phi, a_1..a_5, b. phi's bounds are the design's.
# s and phi are searched on unconstrained scales, where their priors' modes are the stated
# centres (Beta(0.4, 19.6) on logit s peaks at its mean 0.02; on s itself it peaks at 0).
ACCURACY_COORDINATES: Final = (
    Coordinate("logit_slip", math.log(0.001 / 0.999), 0.0, 0.25, 0.005),
    # delta4 and phi are held at their current values in v1 (step 0 skips them): the 6.1
    # recovery test at 1,000 attempts did not recover phi (it stayed at its prior), and the
    # tier-4 recalibration a_4 absorbed delta4. Design 6.1 says to fix such parameters.
    Coordinate("delta4", -1.5, 2.1, 0.0, 0.005),
    Coordinate("log_phi", math.log(0.01), math.log(0.5), 0.0, 0.005),
    *(Coordinate(f"calib_a{tier}", -2.0, 2.0, 0.25, 0.005) for tier in range(1, 6)),
    Coordinate("calib_b", 0.2, 2.0, 0.1, 0.0025),
)
TIME_COORDINATES: Final = (
    Coordinate("tau", math.log(2.0) - 2.5, math.log(2.0) + 2.5, 0.2, 0.001),
    Coordinate("log_sigma_t", math.log(0.05), math.log(2.0), 0.2, 0.001),
)


@dataclass(frozen=True, slots=True)
class BlockDecision:
    """The held-out comparison and the adoption decision for one block of parameters."""

    name: str  # "accuracy" or "time"
    parameters: tuple[str, ...]
    current_score: float  # held-out loss per attempt (nats), current values
    candidate_score: float  # the same for the candidate's values
    p_value: float  # one-sided paired bootstrap p for "no improvement"
    adopted: bool

    @property
    def improvement(self) -> float:
        return self.current_score - self.candidate_score


@dataclass(frozen=True, slots=True)
class RefitDecision:
    """A refit's outcome. `params` is what to use from now on."""

    current: SharedParams
    candidate: SharedParams  # the MAP fit of every refit parameter on the training part
    params: SharedParams  # current, with each adopted block's values from the candidate
    current_score: float  # held-out log loss per attempt, both blocks, current values
    candidate_score: float  # the same for the whole candidate
    p_value: float  # one-sided paired bootstrap p of the whole candidate (reported)
    adopted: bool  # some block was adopted (params differ from current)
    blocks: tuple[BlockDecision, ...]
    train_attempts: int
    held_out_attempts: int
    replays: int  # filter replays the search ran


def refit_due(*, attempts: int, at_last_refit: int | None, drift: bool = False) -> bool:
    """Is a refit due (3.6)? `attempts`: first tries in the whole log; `at_last_refit`: the
    log's size at the last refit (None: none yet). The first refit comes once the log holds
    REFIT_FIRST_ATTEMPTS; later ones once it has grown by REFIT_GROWTH or REFIT_MAX_NEW
    attempts since the last, or at once on `drift` (`calibration_drift` of the predictions
    made since the last refit). No new attempts: nothing to refit. A manual refit (the
    student's Refit now) runs whatever this says."""
    if at_last_refit is None:
        return attempts >= REFIT_FIRST_ATTEMPTS
    new = attempts - at_last_refit
    if new <= 0:
        return False
    return drift or attempts >= REFIT_GROWTH * at_last_refit or new >= REFIT_MAX_NEW


def calibration_drift(outcomes: Sequence[tuple[bool, float]]) -> bool:
    """Calibration in the large of the first tries since the last refit, as (success,
    calibrated prediction) pairs: do the successes differ from the predicted number by more
    than DRIFT_Z standard errors, z = sum(y - p) / sqrt(sum p (1 - p))? Needs
    DRIFT_MIN_ATTEMPTS pairs."""
    if len(outcomes) < DRIFT_MIN_ATTEMPTS:
        return False
    gap = sum((1.0 if y else 0.0) - p for y, p in outcomes)
    var = sum(p * (1.0 - p) for _, p in outcomes)
    return var > 0.0 and abs(gap) > DRIFT_Z * math.sqrt(var)


def refit(
    model: StudentModel,
    observations: Sequence[Observation],
    current: SharedParams,
    *,
    held_out: float = HELD_OUT_SHARE,
    margin: float = ADOPT_MARGIN,
    p_threshold: float = ADOPT_P,
    min_held_out: int = MIN_HELD_OUT,
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = BOOTSTRAP_SEED,
    max_evaluations: int = MAX_EVALUATIONS,
) -> RefitDecision:
    """MAP refit on the first (1 - held_out) of the attempts, scored on the rest (3.6)."""
    ordered = sorted(observations, key=order_key)
    n = len(ordered)
    n_tail = min(n, math.ceil(n * held_out))
    n_train = n - n_tail
    train = ordered[:n_train]

    accuracy = _AccuracyObjective(model, train, current)
    acc_x, _, _ = coordinate_search(
        accuracy, accuracy.start(), ACCURACY_COORDINATES, max_evaluations=max_evaluations
    )
    timing = _TimeObjective(model.time_attempts(current.alpha, train))
    time_x, _, _ = coordinate_search(
        timing, timing.start(current), TIME_COORDINATES, max_evaluations=max_evaluations
    )
    fitted = replace(
        current,
        slip=sigmoid(acc_x[0]),
        delta4=acc_x[1],
        phi=math.exp(acc_x[2]),
        calib_a=(acc_x[3], acc_x[4], acc_x[5], acc_x[6], acc_x[7]),
        calib_b=acc_x[8],
        tau=time_x[0],
        sigma_t=math.exp(time_x[1]),
    )
    candidate = replace(fitted, version=version_of(fitted))

    cur_acc, cur_time = held_out_losses(model, current, ordered, n_train)
    cand_acc, cand_time = held_out_losses(model, candidate, ordered, n_train)
    enough = n_tail >= max(1, min_held_out)
    blocks = (
        _decide(
            "accuracy",
            ACCURACY_PARAMETERS,
            cur_acc,
            cand_acc,
            enough,
            margin,
            p_threshold,
            samples,
            seed,
        ),
        _decide(
            "time",
            TIME_PARAMETERS,
            cur_time,
            cand_time,
            enough,
            margin,
            p_threshold,
            samples,
            seed,
        ),
    )
    params = current
    if blocks[0].adopted:
        params = replace(
            params,
            slip=candidate.slip,
            delta4=candidate.delta4,
            calib_a=candidate.calib_a,
            calib_b=candidate.calib_b,
            phi=candidate.phi,
        )
    if blocks[1].adopted:
        params = replace(params, tau=candidate.tau, sigma_t=candidate.sigma_t)
    adopted = blocks[0].adopted or blocks[1].adopted
    if adopted:
        params = replace(params, version=version_of(params))

    current_total = [a + t for a, t in zip(cur_acc, cur_time, strict=True)]
    candidate_total = [a + t for a, t in zip(cand_acc, cand_time, strict=True)]
    return RefitDecision(
        current=current,
        candidate=candidate,
        params=params,
        current_score=_mean(current_total),
        candidate_score=_mean(candidate_total),
        p_value=paired_bootstrap_p(
            [c - d for c, d in zip(current_total, candidate_total, strict=True)], samples, seed
        ),
        adopted=adopted,
        blocks=blocks,
        train_attempts=n_train,
        held_out_attempts=n_tail,
        replays=accuracy.replays,
    )


def held_out_losses(
    model: StudentModel,
    params: SharedParams,
    ordered: Sequence[Observation],
    start: int,
) -> tuple[list[float], list[float]]:
    """Per-attempt losses (nats) from `start` on, re-running the filter over the whole log
    with `params`: the first try's binary log loss, and minus the log density of the log
    time for a timed success (0 otherwise)."""
    _, records = model.replay(params, ordered)
    accuracy: list[float] = []
    timing: list[float] = []
    log_sigma = math.log(params.sigma_t)
    inverse = 1.0 / (2.0 * params.sigma_t * params.sigma_t)
    for obs, record in zip(ordered[start:], records[start:], strict=True):
        tier = obs.problem.tier
        v = params.calib_a[tier - 1] + params.calib_b * logit(record.prediction.p_raw)
        accuracy.append(softplus(-v) if is_success(obs) else softplus(v))
        minutes = obs.minutes
        if is_timed(obs) and minutes is not None:
            z = math.log(minutes) - math.log(record.prediction.median_minutes)
            timing.append(log_sigma + _HALF_LOG_2PI + z * z * inverse)
        else:
            timing.append(0.0)
    return accuracy, timing


def coordinate_search(
    objective: Callable[[Sequence[float]], float],
    start: Sequence[float],
    coordinates: Sequence[Coordinate],
    *,
    max_evaluations: int = MAX_EVALUATIONS,
) -> tuple[list[float], float, int]:
    """Minimize `objective` by bounded coordinate (pattern) search, deterministically.

    Each coordinate in turn steps up while that improves, else down; a coordinate that
    improves in neither direction halves its step. The search ends when every step is
    below its tolerance or after `max_evaluations`. Returns (x, value, evaluations)."""
    x = [c.clip(v) for v, c in zip(start, coordinates, strict=True)]
    best = objective(x)
    evaluations = 1
    steps = [c.step for c in coordinates]
    while evaluations < max_evaluations:
        for i, c in enumerate(coordinates):
            if steps[i] < c.tolerance:
                continue
            improved = False
            for direction in (1.0, -1.0):
                while evaluations < max_evaluations:
                    trial = list(x)
                    trial[i] = c.clip(x[i] + direction * steps[i])
                    if trial[i] == x[i]:
                        break
                    value = objective(trial)
                    evaluations += 1
                    if value < best:
                        x, best, improved = trial, value, True
                    else:
                        break
                if improved:
                    break
            if not improved:
                steps[i] /= 2.0
        if all(s < c.tolerance for s, c in zip(steps, coordinates, strict=True)):
            break
    return x, best, evaluations


def paired_bootstrap_p(differences: Sequence[float], samples: int, seed: int) -> float:
    """One-sided bootstrap p for "the candidate is no better": the share of resampled means
    of the paired differences (current minus candidate loss) at or below 0, with the +1
    correction. Seeded, so the same inputs always give the same p."""
    n = len(differences)
    if n == 0 or samples <= 0:
        return 1.0
    rng = random.Random(seed)  # noqa: S311 - a seeded, reproducible bootstrap
    at_or_below = sum(1 for _ in range(samples) if sum(rng.choices(differences, k=n)) <= 0.0)
    return (at_or_below + 1) / (samples + 1)


def softplus(v: float) -> float:
    """ln(1 + e^v), stably: the log loss of a miss at logit v (and of a success at -v)."""
    if v > 0.0:
        return v + math.log1p(math.exp(-v))
    return math.log1p(math.exp(v))


def version_of(params: SharedParams) -> str:
    """A deterministic id for a set of refit values."""
    values = (
        params.slip,
        params.delta4,
        *params.calib_a,
        params.calib_b,
        params.phi,
        params.tau,
        params.sigma_t,
    )
    digest = hashlib.sha256(",".join(repr(v) for v in values).encode()).hexdigest()
    return f"map-{digest[:12]}"


def accuracy_log_prior(
    logit_slip: float, delta4: float, log_phi: float, calib_a: Sequence[float], calib_b: float
) -> float:
    """Log density (up to a constant) of the 3.5 priors of the accuracy block, on the search
    scales: Beta(0.4, 19.6) for s as a density of logit s (Jacobian s (1 - s) included, so its
    mode is the prior mean 0.02), normal for delta4, ln phi, a_l and b."""
    alpha, beta = SLIP_PRIOR
    slip = sigmoid(logit_slip)
    value = alpha * math.log(slip) + beta * math.log1p(-slip)
    value += _normal(delta4, DELTA4_PRIOR) + _normal(log_phi, LOG_PHI_PRIOR)
    value += sum(_normal(a, CALIB_A_PRIOR) for a in calib_a)
    return value + _normal(calib_b, CALIB_B_PRIOR)


def time_log_prior(tau: float, log_sigma_t: float) -> float:
    """Log density (up to a constant) of the time block's priors."""
    return _normal(tau, TAU_PRIOR) + _normal(log_sigma_t, LOG_SIGMA_T_PRIOR)


def time_nll(attempts: Sequence[TimedAttempt], tau: float, sigma_t: float) -> float:
    """Minus the log-likelihood of the log times, running the time part of the filter: each
    attempt is predicted with tau and the skill's shrunk offset tau_s from the earlier ones,
    exactly as StudentModel predicts it."""
    sums: dict[ComponentId, tuple[float, int]] = {}
    log_norm = math.log(sigma_t) + _HALF_LOG_2PI
    inverse = 1.0 / (2.0 * sigma_t * sigma_t)
    total = 0.0
    for attempt in attempts:
        residuals, count = sums.get(attempt.skill, (0.0, 0))
        tau_s = residuals / (count + SPEED_SHRINKAGE)
        z = attempt.x - tau - tau_s
        total += log_norm + z * z * inverse
        sums[attempt.skill] = (residuals + attempt.x - tau, count + 1)
    return total


class _AccuracyObjective:
    """Minus the log posterior of the accuracy block on the training attempts.

    A replay depends on (s, delta4, phi) only: the recalibration never feeds back into the
    filter (blame and the Newton steps use P_raw), so a replay's logit(P_raw) values are
    cached and (a_l, b) are scored on them without re-running."""

    def __init__(
        self, model: StudentModel, train: Sequence[Observation], base: SharedParams
    ) -> None:
        self.model = model
        self.train = list(train)
        self.base = base
        self.tiers = [obs.problem.tier for obs in train]
        self.outcomes = [is_success(obs) for obs in train]
        self.cache: dict[tuple[float, float, float], list[float]] = {}
        self.replays = 0

    def start(self) -> list[float]:
        b = self.base
        return [logit(b.slip), b.delta4, math.log(b.phi), *b.calib_a, b.calib_b]

    def logits(self, slip: float, delta4: float, phi: float) -> list[float]:
        key = (slip, delta4, phi)
        cached = self.cache.get(key)
        if cached is None:
            params = replace(self.base, slip=slip, delta4=delta4, phi=phi)
            _, records = self.model.replay(params, self.train)
            cached = [logit(r.prediction.p_raw) for r in records]
            self.cache[key] = cached
            self.replays += 1
        return cached

    def __call__(self, x: Sequence[float]) -> float:
        logit_slip, delta4, log_phi = x[0], x[1], x[2]
        calib_a = x[3 : 3 + CALIBRATION_TIERS]
        calib_b = x[3 + CALIBRATION_TIERS]
        nll = 0.0
        logits = self.logits(sigmoid(logit_slip), delta4, math.exp(log_phi))
        for z, tier, success in zip(logits, self.tiers, self.outcomes, strict=True):
            v = calib_a[tier - 1] + calib_b * z
            nll += softplus(-v) if success else softplus(v)
        return nll - accuracy_log_prior(logit_slip, delta4, log_phi, calib_a, calib_b)


class _TimeObjective:
    """Minus the log posterior of the time block on the training attempts."""

    def __init__(self, attempts: Sequence[TimedAttempt]) -> None:
        self.attempts = list(attempts)

    @staticmethod
    def start(params: SharedParams) -> list[float]:
        return [params.tau, math.log(params.sigma_t)]

    def __call__(self, x: Sequence[float]) -> float:
        tau, log_sigma_t = x[0], x[1]
        return time_nll(self.attempts, tau, math.exp(log_sigma_t)) - time_log_prior(
            tau, log_sigma_t
        )


def _decide(
    name: str,
    parameters: tuple[str, ...],
    current: Sequence[float],
    candidate: Sequence[float],
    enough: bool,
    margin: float,
    p_threshold: float,
    samples: int,
    seed: int,
) -> BlockDecision:
    differences = [c - d for c, d in zip(current, candidate, strict=True)]
    current_score = _mean(current)
    candidate_score = _mean(candidate)
    p_value = paired_bootstrap_p(differences, samples, seed)
    adopted = enough and current_score - candidate_score >= margin and p_value < p_threshold
    return BlockDecision(name, parameters, current_score, candidate_score, p_value, adopted)


def _normal(x: float, prior: tuple[float, float]) -> float:
    mean, sd = prior
    return -0.5 * ((x - mean) / sd) ** 2


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
