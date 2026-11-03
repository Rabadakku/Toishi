"""Which speed model predicts a student's future solve times best? (run with python -I)

Usage: speed_heldout.py ednet KT1_ZIP QUESTIONS_CSV OUT_JSON [n_users]
       speed_heldout.py statics STEP_CSV OUT_JSON

Correct first tries with a time, in time order per student. Each student's last 20% is
held out. Item effects (net of student speed) come from the training rows only. Candidates for
the log-time residual r = log t - item effect on the held-out rows:
  A  shared speed-up: r = c_u - alpha x, alpha pooled over students (within-student fit)
  B  per-student speed-up shrunk toward the pooled one (empirical Bayes)
  C  no speed-up: r = c_u (the student's training mean)
  D  recency: c_u = exponentially weighted mean of the training residuals (half-life h rows)
  E  recency plus the shared speed-up
x = ln(1 + practice count). Score: mean squared error of r on held-out rows, and the
mean bias (observed - predicted) in the held-out rows.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import speed_slopes as ss  # noqa: E402


def item_effects_fit(lt, i, s, ni, ns, iters=30):
    ci = np.bincount(i, minlength=ni).astype(float)
    cs = np.bincount(s, minlength=ns).astype(float)
    v = lt - lt.mean()
    a, b = np.zeros(ni), np.zeros(ns)
    for _ in range(iters):
        a = np.bincount(i, v - b[s], ni) / np.maximum(ci, 1)
        b = np.bincount(s, v - a[i], ns) / np.maximum(cs, 1)
    return lt.mean(), a, ci


def run(d: pd.DataFrame) -> dict:
    ok = d[(d["y"] == 1) & (d["secs"] > 0)].copy()
    ok = ok[ok["secs"] <= ok["secs"].quantile(0.99)]
    ok = ok[ok.groupby("s")["s"].transform("size") >= 50]
    ok["lt"] = np.log(ok["secs"])
    ok["x"] = np.log1p(ok["n"].to_numpy(float))
    ok["k"] = ok.groupby("s").cumcount()
    ok["N"] = ok.groupby("s")["s"].transform("size")
    ok["test"] = ok["k"] >= (0.8 * ok["N"]).astype(int)
    tr = ok[~ok["test"]]
    items = pd.factorize(ok["item"])[0]
    ok["ii"] = items
    tr = ok[~ok["test"]]
    sidx = pd.factorize(ok["s"])[0]
    ok["si"] = sidx
    tr = ok[~ok["test"]]
    mu, a, ci = item_effects_fit(tr["lt"].to_numpy(), tr["ii"].to_numpy(), tr["si"].to_numpy(),
                                 int(ok["ii"].max()) + 1, int(ok["si"].max()) + 1)
    known = ci[ok["ii"].to_numpy()] >= 3
    ok = ok[known].copy()
    ok["r"] = ok["lt"] - mu - a[ok["ii"].to_numpy()]
    tr, te = ok[~ok["test"]], ok[ok["test"]]

    # pooled within-student alpha from training rows
    def dm(df, col):
        return df[col] - df.groupby("s")[col].transform("mean")
    xr, rr = dm(tr, "x"), dm(tr, "r")
    alpha = float(-(xr * rr).sum() / (xr * xr).sum())

    # per-student slopes and their sampling variance (training rows)
    stats = []
    for s, g in tr.groupby("s", sort=False):
        x, y = g["x"].to_numpy(), g["r"].to_numpy()
        xc = x - x.mean()
        sxx = (xc * xc).sum()
        if sxx < 1e-9 or len(y) < 10:
            stats.append((s, y.mean(), x.mean(), -alpha, np.inf))
            continue
        b = (xc * (y - y.mean())).sum() / sxx
        res = (y - y.mean()) - b * xc
        se2 = (res @ res) / (len(y) - 2) / sxx
        stats.append((s, y.mean(), x.mean(), b, se2))
    st = pd.DataFrame(stats, columns=["s", "ybar", "xbar", "b", "se2"]).set_index("s")
    finite = np.isfinite(st["se2"])
    tau2 = max(0.0, st.loc[finite, "b"].var() - st.loc[finite, "se2"].mean())
    k = tau2 / (tau2 + st["se2"].replace(np.inf, 1e9))
    st["b_shrunk"] = -alpha + k * (st["b"] - (-alpha))

    res = {"alpha_pooled": alpha, "alpha_sd_true": float(np.sqrt(tau2)), "students": int(len(st)),
           "test_rows": int(len(te)), "train_rows": int(len(tr))}
    y = te["r"].to_numpy()
    sid = te["s"].to_numpy()
    x = te["x"].to_numpy()
    ybar = st.loc[sid, "ybar"].to_numpy()
    xbar = st.loc[sid, "xbar"].to_numpy()

    def score(name, pred):
        e = y - pred
        res[name] = {"mse": float((e * e).mean()), "bias": float(e.mean())}

    score("A_shared_speedup", ybar - alpha * (x - xbar))
    score("B_per_student_speedup", ybar + st.loc[sid, "b_shrunk"].to_numpy() * (x - xbar))
    score("C_no_speedup", ybar)
    for h in (10, 25, 50, 100):
        lam = 0.5 ** (1.0 / h)
        ew = {}
        for s, g in tr.groupby("s", sort=False):
            r = g["r"].to_numpy()
            w = lam ** np.arange(len(r))[::-1]
            ew[s] = (w * r).sum() / w.sum()
            ew[s + "|x"] = (w * g["x"].to_numpy()).sum() / w.sum()
        c = np.array([ew[s] for s in sid])
        cx = np.array([ew[s + "|x"] for s in sid])
        score(f"D_recency_h{h}", c)
        score(f"E_recency_h{h}_plus_shared", c - alpha * (x - cx))
    return res


def main() -> None:
    d, out, name = ss.load(sys.argv)
    res = run(d)
    res["dataset"] = name
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
