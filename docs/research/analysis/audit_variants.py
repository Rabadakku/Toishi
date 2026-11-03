"""Structural variants of the app's student model, scored prequentially on real logs.

Usage: audit_variants.py statics|xes DATA OUT_JSON [n_students]

Tests claims of the external design audit (2026-11-02) against data instead of argument:
- base: core.learner as built (phi 0.05, rho 0, slip 0.02).
- fisher_fail (audit 1.7): a failure's information is the expected (Fisher) information
  a s (1 - s)^2 / (1 - a s) instead of the observed information clipped at 0.
- adf: the execution posterior updated by assumed-density filtering (moment matching under
  the probit approximation sigma(x) ~ Phi(lambda x), lambda^2 = pi/8, the approximation the
  prediction already uses) instead of one Newton step, for successes and failures.
- first_fail_again (audit 1.3): a failed first try at a never-practised course component
  starts its memory as a Good/Again mixture with weight 1 - b (b its blame) instead of Good.
- no_credit_fail (audit 1.4): a failed first try adds no soft success to any component.
Also counts how often the clipped observed information is 0 on a failure.
"""

import json
import math
import sys
from pathlib import Path
import time
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # the repository root
sys.path.insert(0, str(Path(__file__).resolve().parent))

import core.learner.model as M  # noqa: E402
from core.learner.types import Observation, SharedParams, UpdateRecord  # noqa: E402
from filter_eval import observations, score  # noqa: E402
from fit import load_statics, load_xes  # noqa: E402

LAM2 = math.pi / 8.0
LAM = math.sqrt(LAM2)
COUNT = {"fail": 0, "clipped": 0}


def norm_pdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def norm_cdf(z: float) -> float:
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def mills(z: float) -> float:
    """phi(z) / Phi(z), stable for very negative z."""
    if z < -30.0:
        return -z + 1.0 / max(-z, 1e-12)
    return norm_pdf(z) / max(norm_cdf(z), 1e-300)


def adf_step(m: float, v: float, a: float, success: bool) -> tuple[float, float]:
    """(change of the mean, new variance) of x ~ N(m, v) after a success (likelihood
    Phi(lambda x)) or a failure (likelihood 1 - a Phi(lambda x)), by moment matching."""
    s = math.sqrt(1.0 + LAM2 * v)
    z = LAM * m / s
    r = mills(z)
    m1 = m + v * LAM * r / s
    v1 = v - v * v * LAM2 * r * (z + r) / (s * s)
    if success:
        return m1 - m, max(v1, 1e-6)
    p = norm_cdf(z)
    z0 = max(1.0 - a * p, 1e-300)
    mean = (m - a * p * m1) / z0
    second = ((v + m * m) - a * p * (v1 + m1 * m1)) / z0
    return mean - m, max(second - mean * mean, 1e-6)


class Variant(M.StudentModel):
    def __init__(self, catalog, *, fisher_fail=False, adf=False, first_fail_again=False,
                 no_credit_fail=False):
        super().__init__(catalog)
        self.fisher_fail = fisher_fail
        self.adf = adf
        self.first_fail_again = first_fail_again
        self.no_credit_fail = no_credit_fail

    def update(self, state, obs: Observation) -> UpdateRecord:
        params = state.params
        problem = obs.problem
        day = obs.study_day
        terms = self._terms(state, problem, obs.at_ms, day, store=True)
        prediction, timing = self._prediction(state, problem, terms)
        success = M.is_success(obs)
        cids = tuple(t.cid for t in terms)
        if success:
            blame = [0.0] * len(terms)
        else:
            denominator = max(1.0 - prediction.p_raw, M._TINY)
            blame = [(1.0 - t.q) / denominator for t in terms]
        shares = [M.memory_share(t.e, t.r) if not t.background else 0.0 for t in terms]
        others = M._products_without([t.q for t in terms])
        keep = 1.0 - params.slip
        adapter = self._adapter(params)
        horizon = M.MATCH_HORIZON_DAYS * params.phi
        delta = M.tier_offset(params, problem.tier)
        for i, t in enumerate(terms):
            comp = t.comp
            b = blame[i]
            if not t.background:
                if comp.today != day:
                    comp.today = day
                    comp.successes_today = 0
                weight = 1.0 if comp.successes_today == 0 else params.same_day_weight
                m = shares[i]
                r_mix = 1.0 - b * m
                if self.first_fail_again and comp.memory is None and not success:
                    r_mix = 1.0 - b
                comp.memory = self._remember(adapter, comp.memory, r_mix, obs.at_ms, day,
                                             params.phi, horizon)
                if not (self.no_credit_fail and not success):
                    comp.c += (1.0 - b) * weight
                comp.f += b * (1.0 - m)
            a = keep * t.r * others[i]
            if self.adf:
                x = math.log(t.sigma / (1.0 - t.sigma)) if 0.0 < t.sigma < 1.0 else (
                    40.0 if t.sigma >= 1.0 else -40.0)
                dm, new_var = adf_step(x, t.var, a, success)
                comp.var = new_var
                comp.mu += dm
            else:
                if success:
                    g, h = M.success_step(t.sigma)
                else:
                    g, h = M.failure_step(a, t.sigma)
                    COUNT["fail"] += 1
                    if h == 0.0:
                        COUNT["clipped"] += 1
                    if self.fisher_fail:
                        s = t.sigma
                        h = a * s * (1.0 - s) ** 2 / max(1.0 - a * s, M._TINY)
                comp.var = 1.0 / (1.0 / t.var + h)
                comp.mu += comp.var * g
            comp.attempts += 1
            if not t.background:
                comp.n += 1.0
                if success:
                    comp.successes_today += 1
        minutes = obs.minutes
        if M.is_timed(obs) and minutes is not None:
            self._time_update(state, problem.main_skill, math.log(minutes), timing)
        state.theta_hat = self._theta_hat(state)
        state.last_at_ms = obs.at_ms
        del delta
        return UpdateRecord(prediction=prediction, blame=tuple(zip(cids, blame, strict=True)),
                            memory_share=tuple(zip(cids, shares, strict=True)),
                            attempt_id=obs.attempt_id)


VARIANTS = [
    ("base", {}, {}),
    ("fisher_fail", {"fisher_fail": True}, {}),
    ("adf", {"adf": True}, {}),
    ("first_fail_again", {"first_fail_again": True}, {}),
    ("first_fail_again_phi0.1", {"first_fail_again": True}, {"phi": 0.1}),
    ("first_fail_again_phi0.02", {"first_fail_again": True}, {"phi": 0.02}),
    ("no_credit_fail", {"no_credit_fail": True}, {}),
    ("adf_first_fail_again", {"adf": True, "first_fail_again": True}, {}),
]


def main() -> None:
    which, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    t0 = time.time()
    a, shift = (load_xes if which == "xes" else load_statics)(path, n)
    logs = observations(a, shift)
    base = SharedParams()
    res = {"dataset": which, "students": len(logs), "variants": {}}
    for name, flags, change in VARIANTS:
        COUNT["fail"] = COUNT["clipped"] = 0
        model = Variant({}, **flags)
        r = score(model, replace(base, **change), logs)
        if name == "base":
            r["failures"] = COUNT["fail"]
            r["failures_clipped"] = COUNT["clipped"]
        res["variants"][name] = r
        print(name, json.dumps(r), f"{time.time() - t0:.0f}s", flush=True)
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
