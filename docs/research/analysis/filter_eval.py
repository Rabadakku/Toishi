"""Run the app's own student model (core.learner) over a real log, prequentially.

Usage: filter_eval.py statics|xes DATA OUT_JSON [n_students] [grid]
Each student's first tries are replayed from the priors; every prediction is made before its
update, so the mean log loss is an honest out-of-sample score of the model and its constants.
"""

import json
import math
import sys
from pathlib import Path
import time
from dataclasses import replace
from datetime import UTC, date, datetime

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # the repository root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.learner import StudentModel  # noqa: E402
from core.learner.types import Observation, ProblemSpec, SharedParams  # noqa: E402
from fit import load_statics, load_xes  # noqa: E402

DAY = 86_400_000


def observations(a, shift: int) -> dict[object, list[Observation]]:
    out: dict[object, list[Observation]] = {}
    specs: dict[tuple, ProblemSpec] = {}
    s_arr, item_arr, kcs_arr, y_arr, ts_arr = (a[c].to_numpy() for c in ("s", "item", "kcs", "y", "ts"))
    for i in range(len(a)):
        kcs = tuple(dict.fromkeys(str(k) for k in kcs_arr[i]))
        key = (item_arr[i], kcs)
        spec = specs.get(key)
        if spec is None:
            pid = f"{item_arr[i]}"
            spec = specs[key] = ProblemSpec(problem_id=pid, card_id=pid, part=None, main_skill=kcs[0],
                                            components=kcs, tier=2, steps=1, standard_minutes=2.0)
        ts = int(ts_arr[i])
        day = datetime.fromtimestamp((ts + shift) / 1000, UTC).date()
        out.setdefault(s_arr[i], []).append(Observation(attempt_id=i, at_ms=ts, study_day=day, problem=spec,
                                                        correct=bool(y_arr[i]), role="growth"))
    return out


def score(model: StudentModel, params: SharedParams, logs: dict, dump: str | None = None) -> dict:
    ys, ps, first, multi, gaps = [], [], [], [], []
    rows = []
    for obs_list in logs.values():
        _, records = model.replay(params, obs_list)
        seen: dict[tuple, date] = {}
        last_at: dict[str, int] = {}
        for obs, rec in zip(sorted(obs_list, key=lambda o: (o.at_ms, o.attempt_id)), records, strict=True):
            ys.append(1.0 if obs.correct else 0.0)
            ps.append(rec.prediction.p)
            if dump is not None:
                rows.append((int(obs.correct), rec.prediction.p_raw, [q for _, q in rec.prediction.q]))
            key = obs.problem.components
            multi.append(len(key) > 1)
            main = obs.problem.main_skill
            gaps.append((obs.at_ms - last_at[main]) / 86_400_000 if main in last_at else -1.0)
            last_at[main] = obs.at_ms
            first.append(all(seen.get(k) != obs.study_day for k in key))
            for k in key:
                seen[k] = obs.study_day
    if dump is not None:
        import pickle
        with open(dump, "wb") as fh:
            pickle.dump({"rows": rows, "gaps": gaps, "slip": params.slip}, fh)
    y, p, f = np.array(ys), np.clip(np.array(ps), 1e-6, 1 - 1e-6), np.array(first)
    mk = np.array(multi)
    gp = np.array(gaps)
    edges = [(-1.5, -0.5, "first"), (0, 0.5, "<12h"), (0.5, 3, "0.5-3d"), (3, 7, "3-7d"), (7, 30, "7-30d"), (30, 1e9, "30d+")]
    ll = -(y * np.log(p) + (1 - y) * np.log1p(-p))
    order = np.argsort(p)
    ranks = np.empty(len(p))
    ranks[order] = np.arange(1, len(p) + 1)
    n1 = y.sum()
    auc = (ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))
    # Best global recalibration sigma(a + b logit p): the loss left once calibration is fixed.
    z = np.log(p / (1 - p))
    a_, b_ = 0.0, 1.0
    for _ in range(50):
        q = 1 / (1 + np.exp(-(a_ + b_ * z)))
        g = np.array([(q - y).sum(), ((q - y) * z).sum()])
        w = q * (1 - q)
        h = np.array([[w.sum(), (w * z).sum()], [(w * z).sum(), (w * z * z).sum()]])
        a_, b_ = np.array([a_, b_]) - np.linalg.solve(h + 1e-9 * np.eye(2), g)
    q = np.clip(1 / (1 + np.exp(-(a_ + b_ * z))), 1e-6, 1 - 1e-6)
    llr = -(y * np.log(q) + (1 - y) * np.log1p(-q))
    return {"logloss": round(float(ll.mean()), 5), "firstday_logloss": round(float(ll[f].mean()), 5),
            "auc": round(float(auc), 4), "mean_p_minus_y": round(float(p.mean() - y.mean()), 4),
            "recal_logloss": round(float(llr.mean()), 5), "recal_a_b": [round(float(a_), 3), round(float(b_), 3)], "n": len(y),
            # calibration in the large after the global recalibration, single- vs multi-component
            "recal_bias_single": round(float(q[~mk].mean() - y[~mk].mean()), 4) if (~mk).any() else None,
            "recal_bias_multi": round(float(q[mk].mean() - y[mk].mean()), 4) if mk.any() else None,
            "multi_share": round(float(mk.mean()), 3),
            # calibration by gap since the main skill was last practised: raw and recalibrated
            "by_gap": {name: [int(m.sum()), round(float(p[m].mean() - y[m].mean()), 4), round(float(q[m].mean() - y[m].mean()), 4)]
                       for lo, hi, name in edges for m in [(gp >= lo) & (gp < hi)] if m.any()}}


def logit(x: float) -> float:
    return math.log(x / (1 - x))


GRIDS = {
    "main": [
        ("default", {}),
        ("phi0.25", {"phi": 0.25}), ("phi0.05", {"phi": 0.05}), ("phi0.001", {"phi": 0.001}), ("phi4", {"phi": 4.0}),
        ("sameday0", {"same_day_weight": 0.0}), ("sameday1", {"same_day_weight": 1.0}),
        ("gamma0.2", {"gamma": 0.2}), ("gamma0.6", {"gamma": 0.6}),
        ("rho0", {"rho": 0.0}), ("rho0.3", {"rho": 0.3}),
        ("prior0.55", {"prior_new_mean": logit(0.55)}), ("prior0.75", {"prior_new_mean": logit(0.75)}),
        ("priorvar1", {"prior_new_var": 1.0}), ("priorvar3", {"prior_new_var": 3.0}),
        ("slip0.02", {"slip": 0.02}), ("slip0.1", {"slip": 0.1}),
        ("drift0", {"q_drift": 0.0}), ("drift0.05", {"q_drift": 0.05}),
    ],
}


def main() -> None:
    which, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    extra = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None
    t0 = time.time()
    a, shift = (load_xes if which == "xes" else load_statics)(path, n)
    logs = observations(a, shift)
    model = StudentModel({})
    base = SharedParams()
    grid = [(k, v) for k, v in extra] if extra else GRIDS["main"]
    res = {"dataset": which, "students": len(logs), "grid": {}}
    dump_dir = sys.argv[6] if len(sys.argv) > 6 else None
    for name, change in grid:
        r = score(model, replace(base, **change), logs, f"{dump_dir}/{which}_{name}.pkl" if dump_dir else None)
        res["grid"][name] = r
        print(name, json.dumps(r), f"{time.time() - t0:.0f}s", flush=True)
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
