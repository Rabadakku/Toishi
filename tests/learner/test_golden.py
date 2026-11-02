"""Golden numbers for the student model, worked by hand from design 3.2-3.4.

Constants used below: FSRS-6 default decay w20 = 0.1542, so F = 0.9^(-1/w20) - 1 =
0.9803465; the probit factor is pi/8 = 0.3926991; gamma = 0.37, rho = 0.10, alpha = 0.3,
kappa = 0.95, slip 0.05 and phi 1 (GOLDEN, the v1.1 values the arithmetic was worked with;
the 2026-11-02 audit changed some defaults, not the math). Values are rounded to 7
decimals in the arithmetic; the assertions allow 1e-6.
"""

from dataclasses import replace
from datetime import timedelta

import pytest

from core.engine.config import DAY_MS
from core.engine.fsrs_adapter import FsrsAdapter
from core.learner.model import StudentModel, failure_step, mix_memory
from core.learner.types import (
    ComponentInfo,
    ComponentState,
    MemoryState,
    SharedParams,
    StudentState,
)
from tests.learner.helpers import DAY0, START_MS, observation, problem, state_with

CATALOG = {
    "k": ComponentInfo("k", False),
    "k1": ComponentInfo("k1", False),
    "k2": ComponentInfo("k2", False),
    "alg.bg": ComponentInfo("alg.bg", True),
}
MODEL = StudentModel(CATALOG)
FSRS = FsrsAdapter(fuzz=False)
TOL = 1e-6
GOLDEN = SharedParams(slip=0.05, phi=1.0, rho=0.10, alpha=0.3)


def test_one_component_prediction():
    """A new course component, tier 2, default parameters (s = 0.05, a = 0, b = 1, tau = ln 2).

    Prior: mu = logit(0.65) = ln(0.65 / 0.35) = 0.6190392, v = 2.0; no counts, no memory.
        sqrt(1 + pi/8 * 2.0) = sqrt(1.7853982) = 1.3361879
        e     = sigma(0.6190392 / 1.3361879) = sigma(0.4632875) = 0.6137938
        R     = 1 (before the component's first event), q = e
        P_raw = (1 - 0.05) * 0.6137938 = 0.5831041
        P     = sigma(0 + 1 * logit(0.5831041)) = 0.5831041
    Time: T* = 5 min, nbar = 0, tau_s = 0: median = 5 * exp(ln 2) = 10 min > T*: not at pace.
    """
    state = MODEL.new_state(GOLDEN)
    prediction = MODEL.predict(state, problem("k", tier=2, minutes=5.0), START_MS)
    assert dict(prediction.e)["k"] == pytest.approx(0.6137938, abs=TOL)
    assert dict(prediction.r)["k"] == 1.0
    assert prediction.p_raw == pytest.approx(0.5831041, abs=TOL)
    assert prediction.p == pytest.approx(0.5831041, abs=TOL)
    assert prediction.median_minutes == pytest.approx(10.0, abs=TOL)
    assert prediction.pace_ok is False
    assert state.components == {}  # predict stores nothing


def _three_component_state() -> tuple[SharedParams, StudentState]:
    params = replace(
        GOLDEN,
        slip=0.08,
        delta4=0.4,
        calib_a=(0.0, 0.0, 0.0, 0.2, 0.0),
        calib_b=0.9,
        phi=1.5,
        tau=0.5,
    )
    last = START_MS - 5 * DAY_MS
    state = state_with(
        params,
        {
            "k1": ComponentState(
                mu=1.2,
                var=0.5,
                c=3.0,
                f=1.0,
                memory=MemoryState(10.0, 5.0, last, DAY0 - timedelta(days=5)),
                n=12.0,
                last_var_day=DAY0,
            ),
            "k2": ComponentState(mu=0.3, var=1.0, n=3.0, last_var_day=DAY0),
            "alg.bg": ComponentState(mu=3.0, var=0.4, last_var_day=DAY0),
        },
    )
    state.skill_speed["k1"] = (0.6, 3)
    return params, state


THREE = problem("k1", "k2", "alg.bg", tier=4, minutes=9.5, wrong=((0, "k2"),))


def test_three_component_prediction():
    """Tier 4 (delta4 = 0.4), s = 0.08, a_4 = 0.2, b = 0.9, phi = 1.5, tau = 0.5.

    k1 (course): mu = 1.2, v = 0.5, C = 3, F = 1; memory S = 10 d, last event 5 days ago.
        mu_eta = 1.2 + 0.37 ln 4 + 0.10 ln 2 = 1.2 + 0.5129289 + 0.0693147 = 1.7822436
        e = sigma((1.7822436 - 0.4) / sqrt(1 + pi/8 * 0.5)) = sigma(1.3822436 / 1.0937776)
          = sigma(1.2637337) = 0.7796682
        R = (1 + F * (1.5 * 5) / 10)^(-w20) = 1.7352599^(-0.1542) = 0.9185229
        q = 0.7796682 * 0.9185229 = 0.7161431
    k2 (course, never practised): mu = 0.3, v = 1.0, R = 1.
        e = sigma(-0.1 / sqrt(1 + pi/8)) = sigma(-0.1 / 1.1801267) = sigma(-0.0847367) = 0.4788285
    alg.bg (background): mu = 3.0, v = 0.4, R = 1.
        e = sigma(2.6 / sqrt(1 + pi/8 * 0.4)) = sigma(2.6 / 1.0756764) = sigma(2.4170839)
          = 0.9181208
    P_raw = 0.92 * 0.7161431 * 0.4788285 * 0.9181208 = 0.2896459
    P = sigma(0.2 + 0.9 * logit(0.2896459)) = sigma(0.2 + 0.9 * -0.8971043) = sigma(-0.6073938)
      = 0.3526539
    Time: n_k1 = 12, n_k2 = 3 (the background component is left out): nbar = 7.5;
    tau_s(k1) = 0.6 / (3 + 5) = 0.075.
        median = 9.5 * exp(0.5 + 0.075 - 0.3 ln 8.5) = 9.5 * exp(-0.0670198) = 8.8841781 <= 9.5
    """
    _, state = _three_component_state()
    prediction = MODEL.predict(state, THREE, START_MS, study_day=DAY0)
    q, e, r = dict(prediction.q), dict(prediction.e), dict(prediction.r)
    assert e["k1"] == pytest.approx(0.7796682, abs=TOL)
    assert r["k1"] == pytest.approx(0.9185229, abs=TOL)
    assert q["k1"] == pytest.approx(0.7161431, abs=TOL)
    assert q["k2"] == pytest.approx(0.4788285, abs=TOL)
    assert r["alg.bg"] == 1.0
    assert q["alg.bg"] == pytest.approx(0.9181208, abs=TOL)
    assert prediction.p_raw == pytest.approx(0.2896459, abs=TOL)
    assert prediction.p == pytest.approx(0.3526539, abs=TOL)
    assert prediction.median_minutes == pytest.approx(8.8841781, abs=TOL)
    assert prediction.pace_ok is True


def test_blame_after_a_failure():
    """The three-component problem above, answered wrong (no matched wrong answer).

    b_k = (1 - q_k) / (1 - P_raw), with 1 - P_raw = 1 - 0.2896459 = 0.7103541:
        k1:     (1 - 0.7161431) / 0.7103541 = 0.2838569 / 0.7103541 = 0.3995992
        k2:     (1 - 0.4788285) / 0.7103541 = 0.5211715 / 0.7103541 = 0.7336785
        alg.bg: (1 - 0.9181208) / 0.7103541 = 0.0818792 / 0.7103541 = 0.1152653
    Each is at most 1 (P_raw <= q_k).
    """
    _, state = _three_component_state()
    record = MODEL.update(state, observation(1, START_MS, THREE, False, day=DAY0))
    blame = dict(record.blame)
    assert blame["k1"] == pytest.approx(0.3995992, abs=TOL)
    assert blame["k2"] == pytest.approx(0.7336785, abs=TOL)
    assert blame["alg.bg"] == pytest.approx(0.1152653, abs=TOL)


def test_matched_wrong_answer_failure():
    """The same miss, but the wrong answer matched wrong-line 0, whose step names k2.

    kappa = 0.95: b_k2 = kappa + (1 - kappa) b_k2, every other b_k = (1 - kappa) b_k.
        k2:     0.95 + 0.05 * 0.7336785 = 0.95 + 0.0366839 = 0.9866839
        k1:     0.05 * 0.3995992 = 0.0199800
        alg.bg: 0.05 * 0.1152653 = 0.0057633
    """
    _, state = _three_component_state()
    record = MODEL.update(state, observation(1, START_MS, THREE, False, day=DAY0, matched_wrong=0))
    blame = dict(record.blame)
    assert blame["k2"] == pytest.approx(0.9866839, abs=TOL)
    assert blame["k1"] == pytest.approx(0.0199800, abs=TOL)
    assert blame["alg.bg"] == pytest.approx(0.0057633, abs=TOL)


def test_memory_share():
    """m_k = (1 - R_k) / (1 - e_k R_k): the chance memory failed given that k failed.

        k1: (1 - 0.9185229) / (1 - 0.7796682 * 0.9185229) = 0.0814771 / 0.2838569 = 0.2870358
        k2: R = 1 (no memory event yet): m = 0
        alg.bg: background, R = 1: m = 0
    The recall probability used for k1's FSRS mixture after the miss in the blame test is
    then r = 1 - b m = 1 - 0.3995992 * 0.2870358 = 0.8853007.
    """
    _, state = _three_component_state()
    record = MODEL.update(state, observation(1, START_MS, THREE, False, day=DAY0))
    share = dict(record.memory_share)
    assert share["k1"] == pytest.approx(0.2870358, abs=TOL)
    assert share["k2"] == 0.0
    assert share["alg.bg"] == 0.0
    r = 1 - dict(record.blame)["k1"] * share["k1"]
    assert r == pytest.approx(0.8853007, abs=TOL)


def test_seven_day_matched_stability():
    """S' with R(7 d; S') = r R(7 d; S_good) + (1 - r) R(7 d; S_again), phi = 1 (horizon 7).

    S_good = 25, D_good = 4.0; S_again = 3, D_again = 6.5; r = 0.7.
        R(7; 25) = (1 + 0.9803465 * 7 / 25)^(-0.1542) = 1.2744970^(-0.1542) = 0.9632893
        R(7; 3)  = (1 + 0.9803465 * 7 / 3)^(-0.1542)  = 3.2874752^(-0.1542) = 0.8323382
        target   = 0.7 * 0.9632893 + 0.3 * 0.8323382 = 0.9240040
        S' = 7 F / (target^(-1/0.1542) - 1) = 6.8624255 / (1.6695830 - 1) = 10.2488047
        D' = 0.7 * 4.0 + 0.3 * 6.5 = 4.75
    (v1's log mix, exp(0.7 ln 25 + 0.3 ln 3) = 13.23, is the optimistic value critique 16
    replaced.) With phi = 2 the horizon is 14 FSRS days: 7 real days.
    """
    stability, difficulty = mix_memory(FSRS, (25.0, 4.0), (3.0, 6.5), 0.7, 7.0)
    assert stability == pytest.approx(10.2488047, abs=TOL)
    assert difficulty == pytest.approx(4.75, abs=TOL)
    assert FSRS.retrievability_after(7.0, stability) == pytest.approx(0.9240040, abs=TOL)


def test_failure_observed_information_and_its_clip():
    """g = -u'/(1 - u), h = max(0, [u''(1 - u) + u'^2] / (1 - u)^2), u = A s, u' = u (1 - s),
    u'' = u' (1 - 2 s).

    A = 0.6, s = 0.3: u = 0.18, u' = 0.126, u'' = 0.126 * 0.4 = 0.0504
        h = (0.0504 * 0.82 + 0.126^2) / 0.82^2 = (0.041328 + 0.015876) / 0.6724 = 0.0850744
        g = -0.126 / 0.82 = -0.1536585
    A = 0.5, s = 0.9: u = 0.45, u' = 0.045, u'' = 0.045 * (1 - 1.8) = -0.036
        h = (-0.036 * 0.55 + 0.045^2) / 0.55^2 = -0.017775 / 0.3025 = -0.0587603 -> clipped to 0
        g = -0.045 / 0.55 = -0.0818182
    """
    g, h = failure_step(0.6, 0.3)
    assert h == pytest.approx(0.0850744, abs=TOL)
    assert g == pytest.approx(-0.1536585, abs=TOL)
    g, h = failure_step(0.5, 0.9)
    assert h == 0.0
    assert g == pytest.approx(-0.0818182, abs=TOL)


def test_failure_update_end_to_end():
    """A miss on (k, alg.bg) at tier 1, default parameters (s = 0.05).

    k: mu = 0.5, v = 1.0, no counts, no memory. alg.bg: mu = 3.0, v = 0.5.
    Prediction: e_k = sigma(0.5 / 1.1801267) = sigma(0.4236833) = 0.6043643;
        e_bg = sigma(3.0 / 1.0937776) = sigma(2.7427914) = 0.9395047;
        P_raw = 0.95 * 0.6043643 * 0.9395047 = 0.5394130.
    Blame: b_k = 0.3956357 / 0.4605870 = 0.8589814; R_k = 1, so m_k = 0 and r = 1: the first
    event is FSRS's initial Good state (S = w2 = 2.3065), C_k = (1 - b) * 1 = 0.1410186,
    F_k = b * (1 - 0) = 0.8589814.
    Newton step for k (sigma unadjusted: s = sigma(0.5) = 0.6224593):
        A = 0.95 * R_k * q_bg = 0.95 * 0.9395047 = 0.8925295; u = A s = 0.5555633
        u' = 0.5555633 * 0.3775407 = 0.2097477; u'' = 0.2097477 * (1 - 1.2449187) = -0.0513711
        h = (-0.0513711 * 0.4444367 + 0.2097477^2) / 0.4444367^2
          = (-0.0228311 + 0.0439941) / 0.1975240 = 0.1071409
        g = -0.2097477 / 0.4444367 = -0.4719407
        v' = 1 / (1 / 1.0 + 0.1071409) = 0.9032274; mu' = 0.5 + 0.9032274 * -0.4719407 = 0.0737303
    Newton step for alg.bg (s = sigma(3.0) = 0.9525741):
        A = 0.95 * 1 * q_k = 0.5741461; u = 0.5469167; u' = 0.5469167 * 0.0474259 = 0.0259380
        u'' = 0.0259380 * (1 - 1.9051483) = -0.0234777
        h = (-0.0234777 * 0.4530833 + 0.0259380^2) / 0.4530833^2 = -0.0099646 / 0.2052845
          = -0.0485404 -> clipped to 0, so v stays 0.5 (critique 4)
        g = -0.0259380 / 0.4530833 = -0.0572478; mu' = 3.0 + 0.5 * -0.0572478 = 2.9713761
    """
    params = GOLDEN
    state = state_with(
        params,
        {
            "k": ComponentState(mu=0.5, var=1.0, last_var_day=DAY0),
            "alg.bg": ComponentState(mu=3.0, var=0.5, last_var_day=DAY0),
        },
    )
    record = MODEL.update(
        state, observation(1, START_MS, problem("k", "alg.bg", tier=1), False, day=DAY0)
    )
    assert record.prediction.p_raw == pytest.approx(0.5394130, abs=TOL)
    assert dict(record.blame)["k"] == pytest.approx(0.8589814, abs=TOL)
    k, bg = state.components["k"], state.components["alg.bg"]
    assert k.var == pytest.approx(0.9032274, abs=TOL)
    assert k.mu == pytest.approx(0.0737303, abs=TOL)
    assert k.c == pytest.approx(0.1410186, abs=TOL)
    assert k.f == pytest.approx(0.8589814, abs=TOL)
    assert k.memory is not None
    assert k.memory.stability == pytest.approx(2.3065, abs=TOL)
    assert (k.memory.last_ms, k.memory.last_day) == (START_MS, DAY0)
    assert bg.var == 0.5
    assert bg.mu == pytest.approx(2.9713761, abs=TOL)
    assert bg.memory is None
    assert (bg.c, bg.f, bg.n) == (0.0, 0.0, 0.0)
    assert (k.n, k.attempts, bg.attempts) == (1.0, 1, 1)


def test_phi_scales_elapsed_time():
    """R_k(t) is FSRS recall after phi * (t - last): with S = 10 and 4 real days, phi = 2
    gives (1 + 0.9803465 * 8 / 10)^(-0.1542) = 1.7842772^(-0.1542) = 0.9145859."""
    state = state_with(
        replace(GOLDEN, phi=2.0),
        {
            "k": ComponentState(
                mu=0.0,
                var=1.0,
                memory=MemoryState(10.0, 5.0, START_MS - 4 * DAY_MS, DAY0 - timedelta(days=4)),
                last_var_day=DAY0,
            )
        },
    )
    prediction = MODEL.predict(state, problem("k"), START_MS, study_day=DAY0)
    assert dict(prediction.r)["k"] == pytest.approx(0.9145859, abs=TOL)
