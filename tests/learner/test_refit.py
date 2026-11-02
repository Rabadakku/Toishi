"""The MAP refit and its adoption rule (design 3.6)."""

import math
from dataclasses import replace

import pytest

from core.learner.model import StudentModel, logit, order_key, sigmoid
from core.learner.refit import (
    ADOPT_MARGIN,
    ADOPT_P,
    BlockDecision,
    Coordinate,
    _AccuracyObjective,
    _decide,
    accuracy_log_prior,
    calibration_drift,
    coordinate_search,
    held_out_losses,
    paired_bootstrap_p,
    refit,
    refit_due,
    time_nll,
)
from core.learner.simulate import Simulation, simulate, synthetic_course
from core.learner.types import SharedParams

PRIOR = SharedParams()
COURSE = synthetic_course(seed=3, course_components=24, background_components=6)
MODEL = StudentModel(COURSE.catalog)


@pytest.fixture(scope="module")
def fast_student() -> Simulation:
    """Accuracy parameters at their priors; much faster and steadier than the time prior."""
    return simulate(COURSE, replace(PRIOR, tau=-0.2, sigma_t=0.3), 500, seed=2)


def test_coordinate_search_finds_a_bounded_minimum_deterministically():
    coordinates = (Coordinate("x", -5.0, 5.0, 1.0, 1e-5), Coordinate("y", 0.0, 3.0, 0.5, 1e-5))

    def f(v):
        return (v[0] - 1.234) ** 2 + 3.0 * (v[1] + 1.0) ** 2  # y's minimum is out of bounds

    x, value, evaluations = coordinate_search(f, [4.0, 2.0], coordinates)
    assert x[0] == pytest.approx(1.234, abs=1e-4)
    assert x[1] == 0.0
    assert value == pytest.approx(3.0, abs=1e-6)
    assert coordinate_search(f, [4.0, 2.0], coordinates) == (x, value, evaluations)


def test_coordinate_search_stops_at_its_evaluation_budget():
    calls = []

    def f(v):
        calls.append(v)
        return -v[0]

    coordinates = (Coordinate("x", 0.0, 1e9, 1.0, 1e-9),)
    coordinate_search(f, [0.0], coordinates, max_evaluations=25)
    assert len(calls) == 25


def test_paired_bootstrap_p_is_one_sided_and_seeded():
    assert paired_bootstrap_p([0.01] * 50, 999, 1) == pytest.approx(1 / 1000)
    assert paired_bootstrap_p([-0.01] * 50, 999, 1) == 1.0
    assert paired_bootstrap_p([0.0] * 50, 999, 1) == 1.0
    assert paired_bootstrap_p([], 999, 1) == 1.0
    noisy = [0.05 * math.sin(i * 1.7) + 0.004 for i in range(200)]
    p = paired_bootstrap_p(noisy, 2000, 7)
    assert p == paired_bootstrap_p(noisy, 2000, 7)
    assert 0.0 < p < 1.0


def test_adoption_needs_both_the_margin_and_the_paired_test():
    current = [0.5] * 100
    better = [0.5 - 0.01] * 100  # 0.01 nats better on every attempt
    slightly = [0.5 - 0.001] * 100  # consistent, but below the 0.003 margin
    noisy = [0.5 - 0.01 + (0.3 if i % 2 else -0.29) for i in range(100)]  # mean gain 0.005

    def decide(candidate: list[float], enough: bool = True) -> BlockDecision:
        return _decide("b", ("x",), current, candidate, enough, ADOPT_MARGIN, ADOPT_P, 2000, 1)

    assert decide(better).adopted
    assert not decide(slightly).adopted
    assert decide(slightly).p_value < ADOPT_P
    noisy_decision = decide(noisy)
    assert noisy_decision.improvement >= ADOPT_MARGIN
    assert noisy_decision.p_value >= ADOPT_P
    assert not noisy_decision.adopted
    assert not decide(better, enough=False).adopted


def test_refit_due_on_evidence_not_the_calendar():
    # The first refit once the log can hold MIN_HELD_OUT attempts out.
    assert not refit_due(attempts=149, at_last_refit=None)
    assert refit_due(attempts=150, at_last_refit=None)
    # Later ones when the log has grown by half ...
    assert not refit_due(attempts=224, at_last_refit=150)
    assert refit_due(attempts=225, at_last_refit=150)
    # ... or by 1,000 attempts, whichever comes first.
    assert not refit_due(attempts=4_999, at_last_refit=4_000)
    assert refit_due(attempts=5_000, at_last_refit=4_000)
    # Drift brings it forward; nothing new, nothing to refit.
    assert refit_due(attempts=160, at_last_refit=150, drift=True)
    assert not refit_due(attempts=150, at_last_refit=150, drift=True)


def test_the_schedule_front_loads_refits():
    sizes, last = [], None
    for n in range(1, 2_001):
        if refit_due(attempts=n, at_last_refit=last):
            sizes.append(n)
            last = n
    assert sizes == [150, 225, 338, 507, 761, 1142, 1713]


def test_calibration_drift_is_a_z_test_on_the_success_count():
    calibrated = [(i % 10 < 8, 0.8) for i in range(100)]  # 80 of 100 at p = 0.8
    assert not calibration_drift(calibrated)
    over = [(i % 2 == 0, 0.8) for i in range(100)]  # 50 of 100: z = -30/4 = -7.5
    assert calibration_drift(over)
    under = [(True, 0.5)] * 49  # too few to judge
    assert not calibration_drift(under)
    assert calibration_drift([(True, 0.5)] * 50)  # 25 above 25 expected: z = 25/3.54
    edge = [(i < 66, 0.5) for i in range(100)]  # z = 16/5 = 3.2
    assert calibration_drift(edge)
    assert not calibration_drift([(i < 65, 0.5) for i in range(100)])  # z = 3.0, not beyond


def test_time_nll_is_the_filters_time_model(fast_student):
    """The search scores tau and sigma_T with the time part of the filter alone; it must
    equal the time losses of a full replay."""
    ordered = sorted(fast_student.observations, key=order_key)
    for tau, sigma_t in ((PRIOR.tau, PRIOR.sigma_t), (-0.3, 0.25)):
        params = replace(PRIOR, tau=tau, sigma_t=sigma_t)
        _, timing = held_out_losses(MODEL, params, ordered, 0)
        attempts = MODEL.time_attempts(params.alpha, ordered)
        assert len(attempts) == sum(1 for t in timing if t != 0.0)
        assert time_nll(attempts, tau, sigma_t) == pytest.approx(sum(timing), rel=1e-9)


def test_accuracy_objective_equals_a_full_replay(fast_student):
    """Cached replays plus (a_l, b) applied afterwards score exactly what a replay with
    every parameter set scores."""
    train = sorted(fast_student.observations, key=order_key)[:300]
    objective = _AccuracyObjective(MODEL, train, PRIOR)
    x = [logit(0.1), 0.5, math.log(1.5), 0.1, -0.1, 0.0, 0.2, 0.0, 0.9]
    params = replace(
        PRIOR,
        slip=sigmoid(x[0]),
        delta4=x[1],
        phi=1.5,
        calib_a=(0.1, -0.1, 0.0, 0.2, 0.0),
        calib_b=0.9,
    )
    accuracy, _ = held_out_losses(MODEL, params, train, 0)
    prior = accuracy_log_prior(x[0], x[1], x[2], x[3:8], x[8])
    assert objective(x) == pytest.approx(sum(accuracy) - prior, rel=1e-9)
    objective(x)
    assert objective.replays == 1  # cached


def test_beta_prior_on_logit_slip_peaks_at_its_mean():
    """Beta(0.4, 19.6) as a density of logit s (Jacobian included) has its mode at 0.02."""
    values = {
        s: accuracy_log_prior(logit(s), 0.3, 0.0, (0.0,) * 5, 1.0) for s in (0.01, 0.02, 0.03)
    }
    assert values[0.02] > values[0.01]
    assert values[0.02] > values[0.03]


@pytest.fixture(scope="module")
def decision(fast_student):
    return refit(MODEL, fast_student.observations, PRIOR)


def test_refit_adopts_a_clearly_better_time_block(decision):
    time_block = decision.blocks[1]
    assert time_block.name == "time"
    assert time_block.adopted
    assert time_block.improvement >= ADOPT_MARGIN
    assert time_block.p_value < ADOPT_P
    assert decision.adopted
    assert decision.params.tau == decision.candidate.tau
    assert decision.params.sigma_t == decision.candidate.sigma_t
    assert decision.candidate.tau == pytest.approx(-0.2, abs=0.15)
    assert decision.params.version.startswith("map-")
    assert (decision.train_attempts, decision.held_out_attempts) == (400, 100)


def test_each_block_follows_its_own_rule(decision):
    accuracy_fields = ("slip", "delta4", "calib_a", "calib_b", "phi")
    for block in decision.blocks:
        rule = block.improvement >= ADOPT_MARGIN and block.p_value < ADOPT_P
        assert block.adopted == rule
        source = decision.candidate if block.adopted else decision.current
        for name in accuracy_fields if block.name == "accuracy" else ("tau", "sigma_t"):
            assert getattr(decision.params, name) == getattr(source, name)


def test_refit_is_deterministic_and_the_model_method_delegates(fast_student, decision):
    assert MODEL.refit(fast_student.observations, PRIOR) == decision


def test_a_short_held_out_tail_adopts_nothing(fast_student):
    short = refit(MODEL, fast_student.observations[:120], PRIOR)
    assert short.held_out_attempts == 24
    assert not short.adopted
    assert short.params == PRIOR
    assert short.blocks[1].improvement > 0.0  # it would have helped: the rule held it back


@pytest.mark.parametrize("attempts", [0, 1, 5])
def test_empty_and_tiny_logs_refit_without_adopting(attempts):
    observations = simulate(COURSE, PRIOR, attempts, seed=1).observations if attempts else ()
    decision = refit(MODEL, observations, PRIOR)
    assert decision.train_attempts + decision.held_out_attempts == attempts
    assert not decision.adopted
    assert decision.params == PRIOR
    assert all(math.isfinite(v) for v in (decision.current_score, decision.candidate_score))
