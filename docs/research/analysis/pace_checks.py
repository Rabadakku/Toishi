"""Numbers for the pace/sitting and refit-trigger claims of the external audit (2026-11-02).

1. P(sum of N lognormal solve times <= sum of T*) at median ratio r (Fenton-Wilkinson, as
   core.plan.sitting.pace_chance computes it, checked by Monte Carlo).
2. The expected share of an N-problem exam finished inside its time (Monte Carlo).
3. The median ratio at which an N-problem exam is finished in time with probability 0.8 / 0.9.
4. The false-alarm rate of the calibration-drift trigger (|z| > 3, n >= 50, looked at after
   every attempt) for a perfectly calibrated model.
"""

import json
import math

import numpy as np

SIGMA = 0.45
rng = np.random.default_rng(20261102)


def fw(r: float, n: int, sigma: float = SIGMA) -> float:
    s2 = sigma * sigma
    mean = n * r * math.exp(s2 / 2)
    var = n * r * r * math.exp(s2) * (math.exp(s2) - 1)
    spread = math.log1p(var / mean**2)
    mu = math.log(mean) - spread / 2
    z = (math.log(n) - mu) / math.sqrt(spread)
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def mc(r: float, n: int, reps: int = 400_000) -> tuple[float, float]:
    t = r * np.exp(rng.normal(0.0, SIGMA, size=(reps, n)))
    cum = np.cumsum(t, axis=1)
    finished = (cum[:, -1] <= n).mean()
    share = (cum <= n).sum(axis=1).mean() / n
    return float(finished), float(share)


def ratio_for(n: int, prob: float) -> float:
    lo, hi = 0.3, 1.5
    for _ in range(60):
        mid = (lo + hi) / 2
        if fw(mid, n) >= prob:
            lo = mid
        else:
            hi = mid
    return lo


def drift_false_alarm(horizon: int, reps: int = 20_000) -> float:
    p = rng.uniform(0.5, 0.95, size=(reps, horizon))
    y = (rng.uniform(size=(reps, horizon)) < p).astype(float)
    gap = np.cumsum(y - p, axis=1)
    var = np.cumsum(p * (1 - p), axis=1)
    z = np.abs(gap) / np.sqrt(var)
    looked = z[:, 49:]  # from the 50th prediction on
    return float((looked > 3.0).any(axis=1).mean())


out: dict = {"sigma_t": SIGMA, "pass_time": {}, "exam": {}, "ratio_for": {}, "drift": {}}
for n in (2, 3, 6, 10):
    for r in (0.7, 0.72, 0.78, 0.8, 0.9, 1.0, 1.25):
        f, share = mc(r, n)
        out["pass_time"][f"n{n}_r{r}"] = {"fw": round(fw(r, n), 3), "mc": round(f, 3),
                                          "share_done_mc": round(share, 3)}
for n in (3, 6, 10):
    out["ratio_for"][f"n{n}"] = {"p0.8": round(ratio_for(n, 0.8), 3), "p0.9": round(ratio_for(n, 0.9), 3)}
for h in (200, 500, 1000):
    out["drift"][f"to_{h}"] = round(drift_false_alarm(h), 4)
print(json.dumps(out, indent=1))
