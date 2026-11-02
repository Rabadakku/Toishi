"""Unit tests of StudentModel behaviours (design 3.1-3.5, section 8)."""

import math
from dataclasses import replace
from datetime import timedelta

import pytest

from core.engine.config import DAY_MS
from core.learner.model import (
    SPEED_SHRINKAGE,
    THETA_SHRINKAGE,
    StudentModel,
    failure_step,
    order_key,
    success_step,
)
from core.learner.types import ComponentState, SharedParams
from tests.learner.helpers import (
    CATALOG,
    DAY0,
    START_MS,
    noon,
    observation,
    problem,
    state_with,
)

MODEL = StudentModel(CATALOG)
PARAMS = SharedParams()


@pytest.mark.parametrize(
    "change",
    [
        {"slip": 1.0},
        {"slip": -0.1},
        {"phi": 0.0},
        {"sigma_t": 0.0},
        {"calib_a": (0.0, 0.0, 0.0, 0.0)},
        {"kappa": 1.5},
        {"same_day_weight": -0.1},
        {"q_drift": -0.01},
        {"prior_new_var": 0.0},
        {"tau": math.nan},
    ],
)
def test_new_state_rejects_unusable_parameters(change):
    with pytest.raises(ValueError, match="bad shared parameters"):
        MODEL.new_state(replace(PARAMS, **change))


@pytest.mark.parametrize("tier", [0, 6])
def test_tiers_outside_1_to_5_are_rejected(tier):
    with pytest.raises(ValueError, match="tier"):
        MODEL.predict(MODEL.new_state(PARAMS), problem("c1", tier=tier), START_MS)


def test_copy_is_deep():
    state = MODEL.new_state(PARAMS)
    MODEL.update(state, observation(0, START_MS, problem("c1", "alg.b1"), True, minutes=4.0))
    snapshot = MODEL.copy(state)
    copied = MODEL.copy(state)
    assert copied == state
    memory = copied.components["c1"].memory
    assert memory is not None
    memory.stability = 99.0
    copied.components["c1"].mu = 5.0
    copied.skill_speed["c1"] = (1.0, 9)
    MODEL.update(copied, observation(1, START_MS + DAY_MS, problem("c2"), False))
    assert state == snapshot


def test_an_unknown_component_is_a_course_component():
    """Design 3.9: a problem with no skill tag is its own component, with memory."""
    state = MODEL.new_state(PARAMS)
    MODEL.update(state, observation(0, START_MS, problem("card-17"), True))
    comp = state.components["card-17"]
    assert comp.memory is not None
    assert comp.mu > PARAMS.prior_new_mean  # started from the course prior
    assert comp.n == 1.0


def test_new_components_start_at_their_priors():
    state = MODEL.new_state(PARAMS)
    prediction = MODEL.predict(state, problem("c1", "alg.b1", tier=1), START_MS)
    e = dict(prediction.e)
    course = 1 / (1 + math.exp(-PARAMS.prior_new_mean / math.sqrt(1 + math.pi / 8 * 2.0)))
    background = 1 / (
        1 + math.exp(-PARAMS.prior_background_mean / math.sqrt(1 + math.pi / 8 * 1.0))
    )
    assert e["c1"] == pytest.approx(course, rel=1e-12)
    assert e["alg.b1"] == pytest.approx(background, rel=1e-12)


def test_variance_drifts_by_q_drift_per_study_day():
    params = replace(PARAMS, q_drift=0.05)
    state = MODEL.new_state(params)
    spec = problem("c1")
    MODEL.update(state, observation(0, START_MS, spec, True))
    var = state.components["c1"].var
    # Same study day: no drift. Three study days later: +0.15, in the prediction too.
    MODEL.update(state, observation(1, START_MS + 3_600_000, spec, True))
    var_same_day = state.components["c1"].var
    assert var_same_day < var
    later = START_MS + 3 * DAY_MS
    before = MODEL.predict(state, spec, later)
    assert state.components["c1"].var == var_same_day  # predict stored nothing
    drifted = replace(
        state.components["c1"],
        var=var_same_day + params.q_drift * 3,
        last_var_day=DAY0 + timedelta(days=3),
    )
    assert before.e == MODEL.predict(state_with(params, {"c1": drifted}), spec, later).e
    record = MODEL.update(state, observation(2, later, spec, True))
    assert record.prediction == before
    assert state.components["c1"].last_var_day == DAY0 + timedelta(days=3)


def test_theta_hat_is_a_shrunk_precision_weighted_mean():
    """theta = n / (n + 20) * sum w (mu - m0) / sum w over components with 3+ attempts."""
    state = state_with(
        PARAMS,
        {
            "c1": ComponentState(mu=1.5, var=0.5, attempts=3),
            "c2": ComponentState(mu=-0.5, var=1.0, attempts=7),
            "alg.b1": ComponentState(mu=4.0, var=0.25, attempts=4),
            "c3": ComponentState(mu=9.0, var=0.1, attempts=2),  # too few attempts
        },
    )
    m_course, m_bg = PARAMS.prior_new_mean, PARAMS.prior_background_mean
    weighted = 2.0 * (1.5 - m_course) + 1.0 * (-0.5 - m_course) + 4.0 * (4.0 - m_bg)
    expected = 3 / (3 + THETA_SHRINKAGE) * weighted / 7.0
    assert MODEL._theta_hat(state) == pytest.approx(expected, rel=1e-12)
    # A new component starts at its prior mean plus theta.
    state.theta_hat = expected
    record = MODEL.update(state, observation(0, START_MS, problem("c4"), False))
    e = dict(record.prediction.e)["c4"]
    arg = (m_course + expected) / math.sqrt(1 + math.pi / 8 * PARAMS.prior_new_var)
    assert e == pytest.approx(1 / (1 + math.exp(-arg)), rel=1e-12)


def test_theta_hat_stays_0_until_components_have_3_attempts():
    state = MODEL.new_state(PARAMS)
    spec = problem("c1")
    for i in range(2):
        MODEL.update(state, observation(i, START_MS + i * DAY_MS, spec, True))
        assert state.theta_hat == 0.0
    MODEL.update(state, observation(2, START_MS + 2 * DAY_MS, spec, True))
    comp = state.components["c1"]
    assert state.theta_hat == pytest.approx(
        1 / (1 + THETA_SHRINKAGE) * (comp.mu - PARAMS.prior_new_mean), rel=1e-12
    )


def test_time_model_speed_offsets_and_residual_statistics():
    """x = ln T - ln T* + alpha ln(1 + nbar) - tau feeds tau_s = sum x / (count + 5); the
    running statistics hold the prediction residuals ln T - ln median."""
    state = MODEL.new_state(PARAMS)
    spec = problem("c1", "c2", "alg.b1", minutes=6.0)
    MODEL.update(state, observation(0, START_MS, spec, True, minutes=3.0))
    x0 = math.log(3.0) - math.log(6.0) - PARAMS.tau  # nbar = 0
    assert state.skill_speed["c1"] == pytest.approx((x0, 1), rel=1e-12)
    prediction = MODEL.predict(state, spec, START_MS + DAY_MS)
    tau_s = x0 / (1 + SPEED_SHRINKAGE)
    nbar = 1.0  # c1 and c2 have one attempt each; the background component is left out
    median = 6.0 * math.exp(PARAMS.tau + tau_s - PARAMS.alpha * math.log1p(nbar))
    assert prediction.median_minutes == pytest.approx(median, rel=1e-12)
    assert prediction.pace_ok is (median <= 6.0)
    MODEL.update(state, observation(1, START_MS + DAY_MS, spec, True, minutes=8.0))
    residuals = [x0, math.log(8.0) - math.log(median)]
    mean, m2, count = state.time_stats
    assert count == 2
    assert mean == pytest.approx(sum(residuals) / 2, rel=1e-12)
    assert m2 == pytest.approx((residuals[0] - residuals[1]) ** 2 / 2, rel=1e-12)


@pytest.mark.parametrize(
    ("correct", "aided", "minutes"),
    [(False, False, None), (True, True, 4.0), (True, False, None), (True, False, 0.0)],
)
def test_only_timed_unaided_successes_feed_the_time_model(correct, aided, minutes):
    state = MODEL.new_state(PARAMS)
    obs = observation(0, START_MS, problem("c1"), correct, aided=aided, minutes=minutes)
    MODEL.update(state, obs)
    assert state.skill_speed == {}
    assert state.time_stats == (0.0, 0.0, 0)


def test_an_aided_right_answer_is_a_miss():
    state = MODEL.new_state(PARAMS)
    record = MODEL.update(
        state, observation(0, START_MS, problem("c1"), True, aided=True, minutes=2.0)
    )
    assert dict(record.blame)["c1"] > 0.0
    assert state.components["c1"].mu < PARAMS.prior_new_mean


def test_matched_wrong_answer_naming_no_problem_component_is_a_plain_miss():
    spec = problem("c1", "c2", wrong=((0, "c3"), (1, "c2")))
    plain = MODEL.new_state(PARAMS)
    unmatched = MODEL.update(plain, observation(0, START_MS, spec, False))
    for index in (0, 5):  # names c3 (not in the problem) / no such line
        state = MODEL.new_state(PARAMS)
        record = MODEL.update(state, observation(0, START_MS, spec, False, matched_wrong=index))
        assert record.blame == unmatched.blame
        assert state == plain


def test_matched_wrong_answer_moves_execution_as_a_kappa_mixture():
    """With probability kappa the matched line's component failed and every other one was
    right; otherwise it is an ordinary miss. The Newton step mixes the two the same way."""
    spec = problem("c1", "c2", "alg.b1", tier=1, wrong=((1, "c2"),))
    state = MODEL.new_state(PARAMS)
    record = MODEL.update(state, observation(0, START_MS, spec, False, matched_wrong=1))
    q = dict(record.prediction.q)
    keep = 1 - PARAMS.slip
    kappa = PARAMS.kappa
    s_course = 1 / (1 + math.exp(-PARAMS.prior_new_mean))
    s_bg = 1 / (1 + math.exp(-PARAMS.prior_background_mean))
    others = {
        "c1": q["c2"] * q["alg.b1"],
        "c2": q["c1"] * q["alg.b1"],
        "alg.b1": q["c1"] * q["c2"],
    }
    for cid, s, prior_var, mu0 in (
        ("c1", s_course, 2.0, PARAMS.prior_new_mean),
        ("c2", s_course, 2.0, PARAMS.prior_new_mean),
        ("alg.b1", s_bg, 1.0, PARAMS.prior_background_mean),
    ):
        g_fail, h_fail = failure_step(keep * others[cid], s)
        g_match, h_match = failure_step(1.0, s) if cid == "c2" else success_step(s)
        g = kappa * g_match + (1 - kappa) * g_fail
        h = kappa * h_match + (1 - kappa) * h_fail
        var = 1 / (1 / prior_var + h)
        assert state.components[cid].var == pytest.approx(var, rel=1e-12)
        assert state.components[cid].mu == pytest.approx(mu0 + var * g, rel=1e-12)
    assert state.components["c2"].mu < PARAMS.prior_new_mean  # the matched step: down
    assert state.components["c1"].mu > PARAMS.prior_new_mean  # the others: nearly a success


def test_duplicate_components_count_once():
    once, twice = MODEL.new_state(PARAMS), MODEL.new_state(PARAMS)
    MODEL.update(once, observation(0, START_MS, problem("c1", "c2"), False))
    record = MODEL.update(twice, observation(0, START_MS, problem("c1", "c2", "c1"), False))
    assert [cid for cid, _ in record.blame] == ["c1", "c2"]
    assert once == twice


def test_same_study_day_events_use_the_same_day_formula():
    """The 4 AM rollover decides the study day: 01:00 belongs to the day before."""
    state = MODEL.new_state(PARAMS)
    spec = problem("c1")
    late = noon(DAY0) + 12 * 3_600_000  # midnight UTC, still DAY0's study day
    MODEL.update(state, observation(0, START_MS, spec, True))
    first = state.components["c1"].memory
    assert first is not None
    MODEL.update(state, observation(1, late + 3_600_000, spec, True))
    second = state.components["c1"].memory
    assert second is not None
    assert second.last_day == DAY0
    adapter = MODEL._adapter(PARAMS)
    assert (second.stability, second.difficulty) == adapter.step_fractional(
        (first.stability, first.difficulty), 3, 0.0, same_day=True
    )


def test_the_recalibration_never_feeds_back_into_the_filter():
    """(a_l, b) map P_raw to P and nothing else: blame and the Newton steps use P_raw.
    The refit relies on it to score (a_l, b) without re-running the filter."""
    log = [
        observation(i, START_MS + i * DAY_MS // 3, problem("c1", "c2", tier=1 + i % 5), i % 3 > 0)
        for i in range(20)
    ]
    other = replace(PARAMS, calib_a=(0.3, -0.2, 0.1, 0.5, -0.4), calib_b=0.7)
    state_a, records_a = MODEL.replay(PARAMS, log)
    state_b, records_b = MODEL.replay(other, log)
    assert state_a.components == state_b.components
    assert [r.prediction.p_raw for r in records_a] == [r.prediction.p_raw for r in records_b]
    assert [r.prediction.p for r in records_a] != [r.prediction.p for r in records_b]


def test_replay_orders_by_time_then_attempt_id_and_records_ids():
    spec = problem("c1")
    log = [
        observation(5, START_MS + DAY_MS, spec, True),
        observation(9, START_MS, spec, False),
        observation(2, START_MS, spec, True),
    ]
    _, records = MODEL.replay(PARAMS, log)
    assert [r.attempt_id for r in records] == [2, 9, 5]
    assert [o.attempt_id for o in sorted(log, key=order_key)] == [2, 9, 5]
