"""Two more checks of the external audit (2026-11-02), on real logs.

Usage: audit_extra.py statics|xes DATA OUT_JSON [n_students]

1. fail_no_good (audit 1.1, Q2 "failures interpolate between S_k and S_Again, never S_Good"):
   on a failed first try at a practised course component, the Good post-state of the memory
   mixture is replaced by the unchanged previous state, so a failure never raises stability.
2. Combination rules (audit Q1): from the base model's per-component chances q_k, the problem's
   chance by the product (the app's), the geometric mean, the weakest link, and the audit's
   soft minimum logit P = -(1/b) ln(mean exp(-b logit q_k)) - lam ln K (b = 2, lam = 0.25, and
   the best (b, lam) on a grid), each times (1 - s) and then recalibrated globally (Platt).
   Post hoc on the same filter run, like the original combination audit.
"""

import json
import math
import sys
from pathlib import Path
import time
from dataclasses import replace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # the repository root
sys.path.insert(0, str(Path(__file__).resolve().parent))

import core.learner.model as M  # noqa: E402
from audit_variants import Variant  # noqa: E402
from core.engine.config import AGAIN  # noqa: E402
from core.learner.types import MemoryState, SharedParams  # noqa: E402
from filter_eval import observations, score  # noqa: E402
from fit import load_statics, load_xes  # noqa: E402


class FailNoGood(Variant):
    """A failure never raises stability: Good is replaced by the previous state."""

    def update(self, state, obs):
        self._failing = not M.is_success(obs)
        return super().update(state, obs)

    def _remember(self, adapter, memory, r, at_ms, day, phi, horizon):
        if memory is None or not getattr(self, "_failing", False):
            return super()._remember(adapter, memory, r, at_ms, day, phi, horizon)
        previous = (memory.stability, memory.difficulty)
        same_day = memory.last_day == day
        elapsed = phi * max(0, at_ms - memory.last_ms) / M.DAY_MS
        good = previous
        again = adapter.step_fractional(previous, AGAIN, elapsed, same_day=same_day)
        stability, difficulty = M.mix_memory(adapter, good, again, r, horizon)
        return MemoryState(stability, difficulty, at_ms, day)


def recal_ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    z = np.log(p / (1 - p))
    a, b = 0.0, 1.0
    for _ in range(60):
        q = 1 / (1 + np.exp(-(a + b * z)))
        g = np.array([(q - y).sum(), ((q - y) * z).sum()])
        w = q * (1 - q)
        h = np.array([[w.sum(), (w * z).sum()], [(w * z).sum(), (w * z * z).sum()]])
        a, b = np.array([a, b]) - np.linalg.solve(h + 1e-9 * np.eye(2), g)
    q = np.clip(1 / (1 + np.exp(-(a + b * z))), 1e-6, 1 - 1e-6)
    ll = -(y * np.log(q) + (1 - y) * np.log1p(-q))
    return float(ll.mean()), q


def softmin(qs, b, lam):
    lg = np.log(np.clip(qs, 1e-9, 1 - 1e-9) / (1 - np.clip(qs, 1e-9, 1 - 1e-9)))
    k = len(qs)
    m = -(1.0 / b) * (np.logaddexp.reduce(-b * lg) - math.log(k)) - lam * math.log(k)
    return 1 / (1 + math.exp(-m))


def main():
    which, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    t0 = time.time()
    a, shift = (load_xes if which == "xes" else load_statics)(path, n)
    logs = observations(a, shift)
    base = SharedParams()
    res = {"dataset": which, "students": len(logs)}
    res["fail_no_good"] = score(FailNoGood({}), base, logs)
    print("fail_no_good", json.dumps(res["fail_no_good"]), f"{time.time() - t0:.0f}s", flush=True)

    import pickle
    import tempfile
    dump = tempfile.mktemp(suffix=".pkl")
    res["base"] = score(Variant({}), base, logs, dump)
    rows = pickle.load(open(dump, "rb"))["rows"]
    y = np.array([r[0] for r in rows], dtype=float)
    qs = [np.array(r[2]) for r in rows]
    keep = 1 - base.slip
    multi = np.array([len(q) > 1 for q in qs])
    combos = {
        "product": np.array([keep * q.prod() for q in qs]),
        "geometric": np.array([keep * q.prod() ** (1 / len(q)) for q in qs]),
        "weakest": np.array([keep * q.min() for q in qs]),
        "softmin_b2_lam0.25": np.array([keep * softmin(q, 2.0, 0.25) for q in qs]),
    }
    best = None
    for b in (0.5, 1.0, 2.0, 4.0, 8.0):
        for lam in (0.0, 0.25, 0.5, 1.0):
            p = np.array([keep * softmin(q, b, lam) for q in qs])
            ll, _ = recal_ll(y, p)
            if best is None or ll < best[0]:
                best = (ll, b, lam, p)
    combos[f"softmin_best_b{best[1]}_lam{best[2]}"] = best[3]
    res["combination"] = {}
    for name, p in combos.items():
        ll, q = recal_ll(y, p)
        res["combination"][name] = {
            "recal_logloss": round(ll, 5),
            "recal_bias_single": round(float(q[~multi].mean() - y[~multi].mean()), 4),
            "recal_bias_multi": round(float(q[multi].mean() - y[multi].mean()), 4),
        }
    print("combination", json.dumps(res["combination"]), f"{time.time() - t0:.0f}s", flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
