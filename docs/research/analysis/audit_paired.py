"""Paired, student-clustered comparison of model variants (audit 2026-11-02).

Usage: audit_paired.py statics|xes DATA OUT_JSON [n_students]

For each variant, every first try is predicted before its update (prequential). The
difference to the base model is bootstrapped over students (2,000 resamples), for the raw log
loss and for the log loss after each variant's own best global recalibration. A robustness
grid repeats the ADF-vs-Newton comparison at other constants.
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

from audit_variants import Variant  # noqa: E402
from core.learner.types import SharedParams  # noqa: E402
from filter_eval import observations  # noqa: E402
from fit import load_statics, load_xes  # noqa: E402


def predictions(model, params, logs):
    ys, ps, sid = [], [], []
    for k, (student, obs_list) in enumerate(logs.items()):
        _, records = model.replay(params, obs_list)
        for obs, rec in zip(sorted(obs_list, key=lambda o: (o.at_ms, o.attempt_id)), records, strict=True):
            ys.append(1.0 if obs.correct else 0.0)
            ps.append(rec.prediction.p)
            sid.append(k)
    return np.array(ys), np.clip(np.array(ps), 1e-6, 1 - 1e-6), np.array(sid)


def recal(y, p):
    z = np.log(p / (1 - p))
    a, b = 0.0, 1.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-(a + b * z)))
        g = np.array([(q - y).sum(), ((q - y) * z).sum()])
        w = q * (1 - q)
        h = np.array([[w.sum(), (w * z).sum()], [(w * z).sum(), (w * z * z).sum()]])
        a, b = np.array([a, b]) - np.linalg.solve(h + 1e-9 * np.eye(2), g)
    return np.clip(1 / (1 + np.exp(-(a + b * z))), 1e-6, 1 - 1e-6)


def ll(y, p):
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))


def auc(y, p):
    order = np.argsort(p)
    ranks = np.empty(len(p))
    ranks[order] = np.arange(1, len(p) + 1)
    n1 = y.sum()
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


def clustered(diff, sid, n_students, reps=2000, seed=0):
    """Mean per-attempt difference and its 95% interval, resampling students."""
    sums = np.bincount(sid, weights=diff, minlength=n_students)
    counts = np.bincount(sid, minlength=n_students).astype(float)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(reps):
        pick = rng.integers(0, n_students, n_students)
        boots.append(sums[pick].sum() / counts[pick].sum())
    boots = np.array(boots)
    return {"mean": round(float(sums.sum() / counts.sum()), 5),
            "ci95": [round(float(np.quantile(boots, 0.025)), 5), round(float(np.quantile(boots, 0.975)), 5)],
            "share_students_better": round(float(((sums / np.maximum(counts, 1)) > 0).mean()), 3)}


def main():
    which, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    t0 = time.time()
    a, shift = (load_xes if which == "xes" else load_statics)(path, n)
    logs = observations(a, shift)
    base = SharedParams()
    grid = [
        ("default", {}),
        ("priorvar1", {"prior_new_var": 1.0}),
        ("priorvar3", {"prior_new_var": 3.0}),
        ("gamma0.2", {"gamma": 0.2}),
        ("gamma0.6", {"gamma": 0.6}),
        ("drift0", {"q_drift": 0.0}),
        ("drift0.05", {"q_drift": 0.05}),
        ("slip0.05", {"slip": 0.05}),
    ]
    res = {"dataset": which, "students": len(logs), "grid": {}}
    for name, change in grid:
        params = replace(base, **change)
        y, p0, sid = predictions(Variant({}), params, logs)
        _, p1, _ = predictions(Variant({}, adf=True), params, logs)
        q0, q1 = recal(y, p0), recal(y, p1)
        row = {
            "newton": {"logloss": round(float(ll(y, p0).mean()), 5), "recal": round(float(ll(y, q0).mean()), 5), "auc": round(auc(y, p0), 4)},
            "adf": {"logloss": round(float(ll(y, p1).mean()), 5), "recal": round(float(ll(y, q1).mean()), 5), "auc": round(auc(y, p1), 4)},
            # positive = ADF better
            "raw_gain": clustered(ll(y, p0) - ll(y, p1), sid, len(logs)),
            "recal_gain": clustered(ll(y, q0) - ll(y, q1), sid, len(logs)),
        }
        res["grid"][name] = row
        print(name, json.dumps(row), f"{time.time() - t0:.0f}s", flush=True)
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
