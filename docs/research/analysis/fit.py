"""Fit student-model constants on public learning logs (run with python -I).

Usage: fit.py xes|statics DATA_PATH OUT_JSON [n_students]

Builds first-attempt tables, replays per-(student, KC) histories (counts, gaps, FSRS-6 memory
under several time scales phi) and fits P = (1 - s) * sigmoid(theta_s + beta_k + w . x) * R by
penalized maximum likelihood, scoring each variant on every student's last 20% of attempts.
"""

import json
import math
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
from fsrs import Rating, Scheduler
from scipy.optimize import minimize
from scipy.special import expit

DAY = 86_400_000
PHIS = (0.02, 0.05, 0.1, 0.25, 1.0)
SCHED = Scheduler(enable_fuzzing=False)
DECAY = -SCHED.parameters[20]
FACTOR = 0.9 ** (1 / DECAY) - 1


def load_xes(path: str, n_students: int, seed: int = 0) -> tuple[pd.DataFrame, int]:
    frames = []
    for i, name in enumerate(("seq_train.parquet", "seq_test.parquet")):
        t = pq.read_table(f"{path}/{name}", columns=["uid", "questions", "concepts", "responses", "timestamps", "is_repeat"])
        q = t["questions"].combine_chunks()
        par = pc.list_parent_indices(q).to_numpy()
        col = {c: pc.list_flatten(t[c].combine_chunks()).to_numpy() for c in ("concepts", "responses", "timestamps", "is_repeat")}
        d = pd.DataFrame({"s": t["uid"].to_numpy()[par], "row": par + i * 10**7, "item": pc.list_flatten(q).to_numpy(),
                          "kc": col["concepts"], "y": col["responses"], "ts": col["timestamps"], "rep": col["is_repeat"]})
        frames.append(d[d["item"] >= 0])
    d = pd.concat(frames, ignore_index=True)
    rng = np.random.default_rng(seed)
    uids = d["s"].unique()
    keep = set(rng.choice(uids, size=min(n_students, len(uids)), replace=False).tolist())
    d = d[d["s"].isin(keep)].reset_index(drop=True)
    start = np.r_[True, d["row"].to_numpy()[1:] != d["row"].to_numpy()[:-1]]
    d["att"] = np.cumsum((d["rep"].to_numpy() == 0) | start) - 1
    g = d.groupby("att", sort=False)
    a = g.agg(s=("s", "first"), item=("item", "first"), y=("y", "first"), ts=("ts", "first"), row=("row", "first"))
    a["kcs"] = g["kc"].agg(lambda x: tuple(dict.fromkeys(x.tolist())))
    a["secs"] = np.nan
    a = a.reset_index().sort_values(["s", "ts", "att"], kind="stable").reset_index(drop=True)
    return a[["s", "item", "kcs", "y", "ts", "secs"]], 4 * 3_600_000  # China UTC+8, 4 AM rollover


def load_statics(path: str, n_students: int = 0, seed: int = 0) -> tuple[pd.DataFrame, int]:
    cols = ["Anon Student Id", "Problem Name", "Step Name", "First Transaction Time", "First Attempt", "KC (F2011)", "Correct Step Duration (sec)"]
    d = pd.read_csv(path, usecols=cols, dtype=str).dropna(subset=["KC (F2011)", "First Transaction Time"])
    out = pd.DataFrame({
        "s": d["Anon Student Id"].to_numpy(),
        "item": (d["Problem Name"] + "|" + d["Step Name"]).to_numpy(),
        "kcs": d["KC (F2011)"].str.split("~~").map(tuple).to_numpy(),
        "y": (d["First Attempt"] == "correct").astype(int).to_numpy(),
        "ts": pd.to_datetime(d["First Transaction Time"], format="%Y/%m/%d %H:%M").astype("datetime64[ms]").astype("int64").to_numpy(),
        "secs": pd.to_numeric(d["Correct Step Duration (sec)"], errors="coerce").to_numpy(),
    })
    out = out.reset_index(drop=True)
    out["ord"] = np.arange(len(out))
    out = out.sort_values(["s", "ts", "ord"], kind="stable").reset_index(drop=True)
    return out.drop(columns="ord"), -4 * 3_600_000  # local times, 4 AM rollover


def replay(a: pd.DataFrame, day_shift: int) -> dict[str, np.ndarray]:
    """Per attempt and each of its KCs, the state before the attempt. One row per (attempt, KC)."""
    rows: dict[str, list] = {k: [] for k in ("att", "kc", "nk", "C", "F", "Cd", "Cx", "gap", "E", "first_today")}
    for p in PHIS:
        rows[f"R{p}"] = []
    state: dict = {}
    seen: dict = {}
    s_arr, kcs_arr, y_arr, ts_arr = a["s"].to_numpy(), a["kcs"].to_numpy(), a["y"].to_numpy(), a["ts"].to_numpy()
    good, again = Rating.Good, Rating.Again
    for i in range(len(a)):
        s, kcs, y, ts = s_arr[i], kcs_arr[i], int(y_arr[i]), int(ts_arr[i])
        day = (ts + day_shift) // DAY
        e = seen.get(s, 0)
        for k in kcs:
            st = state.get((s, k))
            if st is None:
                st = state[(s, k)] = {"C": 0, "F": 0, "Cd": 0, "Cx": 0, "last": None, "lastday": None, "sday": None, "mem": {p: None for p in PHIS}}
            rows["att"].append(i)
            rows["kc"].append(k)
            rows["nk"].append(len(kcs))
            rows["C"].append(st["C"])
            rows["F"].append(st["F"])
            rows["Cd"].append(st["Cd"])
            rows["Cx"].append(st["Cx"])
            rows["gap"].append(np.nan if st["last"] is None else (ts - st["last"]) / DAY)
            rows["E"].append(e)
            rows["first_today"].append(st["lastday"] != day)
            same = st["lastday"] == day
            for p in PHIS:
                m = st["mem"][p]
                if m is None:
                    rows[f"R{p}"].append(1.0)
                    stab = SCHED._initial_stability(rating=good if y else again)
                    diff = SCHED._initial_difficulty(rating=good if y else again, clamp=True)
                else:
                    stab0, diff0 = m
                    t = p * (ts - st["last"]) / DAY
                    r = (1 + FACTOR * t / stab0) ** DECAY
                    rows[f"R{p}"].append(r)
                    g = good if y else again
                    if same:
                        stab = SCHED._short_term_stability(stability=stab0, rating=g)
                    else:
                        stab = SCHED._next_stability(difficulty=diff0, stability=stab0, retrievability=r, rating=g)
                    diff = SCHED._next_difficulty(difficulty=diff0, rating=g)
                st["mem"][p] = (min(stab, 36_500.0), diff)
            if y:
                st["C"] += 1
                if st["sday"] == day:
                    st["Cx"] += 1
                else:
                    st["Cd"] += 1
                    st["sday"] = day
            else:
                st["F"] += 1
            st["last"], st["lastday"] = ts, day
        seen[s] = e + 1
    return {k: np.asarray(v) for k, v in rows.items()}


def layout(ns, nk, m, kslope, sslope):
    sizes = [ns, nk, m, nk if kslope else 0, ns if sslope else 0, 1]
    cuts = np.cumsum([0] + sizes)
    return [slice(cuts[i], cuts[i + 1]) for i in range(6)], int(cuts[-1])


def linear(p, sl_, si, ki, X, lc, kslope, sslope):
    z = p[sl_[0]][si] + p[sl_[1]][ki] + X @ p[sl_[2]]
    if kslope:
        z = z + p[sl_[3]][ki] * lc
    if sslope:
        z = z + p[sl_[4]][si] * lc
    return z


def fit(si, ki, X, y, M, ns, nk, sig=2.0, slip=True, x0=None, lc=None, kslope=False, sslope=False, sig_slope=0.3):
    sl_, size = layout(ns, nk, X.shape[1], kslope, sslope)

    def f(p):
        sg = expit(linear(p, sl_, si, ki, X, lc, kslope, sslope))
        s_ = expit(p[-1]) if slip else 0.0
        c = (1 - s_) * M
        P = np.clip(c * sg, 1e-9, 1 - 1e-9)
        th, be, gk, gs = p[sl_[0]], p[sl_[1]], p[sl_[3]], p[sl_[4]]
        nll = -(y * np.log(P) + (1 - y) * np.log1p(-P)).sum()
        nll += 0.5 * ((th ** 2).sum() + (be ** 2).sum()) / sig ** 2 + 0.5 * ((gk ** 2).sum() + (gs ** 2).sum()) / sig_slope ** 2
        gz = np.where(y == 1, -(1 - sg), c * sg * (1 - sg) / (1 - P))
        g = np.zeros(size)
        g[sl_[0]] = np.bincount(si, gz, ns) + th / sig ** 2
        g[sl_[1]] = np.bincount(ki, gz, nk) + be / sig ** 2
        g[sl_[2]] = X.T @ gz
        if kslope:
            g[sl_[3]] = np.bincount(ki, gz * lc, nk) + gk / sig_slope ** 2
        if sslope:
            g[sl_[4]] = np.bincount(si, gz * lc, ns) + gs / sig_slope ** 2
        g[-1] = float(np.where(y == 1, s_, -P * s_ / (1 - P)).sum()) if slip else 0.0
        return nll, g

    p0 = np.zeros(size) if x0 is None else x0.copy()
    if x0 is None:
        p0[-1] = -3.0
    r = minimize(f, p0, jac=True, method="L-BFGS-B", options={"maxiter": 3000, "maxfun": 6000})
    return r.x, sl_


def predict(p, sl_, si, ki, X, M, lc=None, kslope=False, sslope=False, slip=True):
    s_ = expit(p[-1]) if slip else 0.0
    return np.clip((1 - s_) * M * expit(linear(p, sl_, si, ki, X, lc, kslope, sslope)), 1e-9, 1 - 1e-9)


def logloss(y, P) -> float:
    return float(-(y * np.log(P) + (1 - y) * np.log1p(-P)).mean())


def auc(y, P) -> float:
    order = np.argsort(P)
    ranks = np.empty(len(P))
    ranks[order] = np.arange(1, len(P) + 1)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> None:
    which, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n_students = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
    t0 = time.time()
    a, shift = (load_xes if which == "xes" else load_statics)(path, n_students)
    res: dict = {"dataset": which, "students": int(a["s"].nunique()), "items": int(a["item"].nunique()),
                 "attempts": len(a), "mean_acc": float(a["y"].mean()),
                 "multi_kc_share": float((a["kcs"].map(len) > 1).mean())}
    f = replay(a, shift)
    res["kcs"] = int(len(set(f["kc"].tolist())))
    print(json.dumps(res), f"{time.time() - t0:.0f}s", flush=True)

    # Single-KC first tries only; each student's last 20% of them held out.
    single = f["nk"] == 1
    att = f["att"][single]
    d = pd.DataFrame({"att": att, "s": a["s"].to_numpy()[att], "y": a["y"].to_numpy()[att], "kc": f["kc"][single]})
    for k in ("C", "F", "Cd", "Cx", "gap", "E", "first_today", *[f"R{p}" for p in PHIS]):
        d[k] = f[k][single]
    rank = d.groupby("s").cumcount()
    size = d.groupby("s")["s"].transform("size")
    d["test"] = rank >= np.ceil(0.8 * size)
    si = pd.factorize(d["s"])[0]
    ki_codes, ki_uni = pd.factorize(d["kc"])
    ns, nk = si.max() + 1, len(ki_uni)
    tr, te = ~d["test"].to_numpy(), d["test"].to_numpy()
    y = d["y"].to_numpy().astype(float)

    # Descriptives: first-opportunity accuracy, ceiling after a run of successes.
    first = d[d["C"] + d["F"] == 0]
    res["first_opp_acc"] = float(first["y"].mean())
    kc_first = first.groupby("kc")["y"].agg(["mean", "size"])
    kc_first = kc_first[kc_first["size"] >= 30]
    lg = np.log(np.clip(kc_first["mean"], 0.02, 0.98) / (1 - np.clip(kc_first["mean"], 0.02, 0.98)))
    res["first_opp_kc_logit_sd"] = float(lg.std())
    hi = d[(d["C"] >= 10) & (d["F"] <= 0.2 * d["C"])]
    res["acc_after_10plus_success_low_fail"] = float(hi["y"].mean()) if len(hi) else None
    res["n_after_10plus"] = int(len(hi))
    curve = d.assign(o=(d["C"] + d["F"]).clip(upper=20)).groupby("o")["y"].mean()
    res["curve_by_opportunity"] = {int(k): round(float(v), 3) for k, v in curve.items() if k in (0, 1, 2, 3, 4, 5, 7, 10, 15, 20)}
    gapd = d[d["gap"].notna()].copy()
    gapd["gb"] = pd.cut(gapd["gap"], [-1e-9, 1 / 24, 1, 3, 7, 14, 30, 90, 1e9], labels=["<1h", "1h-1d", "1-3d", "3-7d", "7-14d", "14-30d", "30-90d", "90d+"])
    res["acc_by_gap_raw"] = {str(k): [round(float(v), 3), int(n)] for k, (v, n) in gapd.groupby("gb", observed=True)["y"].agg(["mean", "size"]).iterrows()}

    firstday = d["first_today"].to_numpy()[te]

    def run(name, cols, M=None, slip=True, x0=None, kslope=False, sslope=False):
        X = np.column_stack([np.ones(len(d))] + [c for c in cols])
        Mv = np.ones(len(d)) if M is None else M
        p, sl_ = fit(si[tr], ki_codes[tr], X[tr], y[tr], Mv[tr], ns, nk, slip=slip, x0=x0, lc=lc[tr], kslope=kslope, sslope=sslope)
        P = predict(p, sl_, si[te], ki_codes[te], X[te], Mv[te], lc=lc[te], kslope=kslope, sslope=sslope, slip=slip)
        r = {"test_logloss": round(logloss(y[te], P), 5), "test_auc": round(auc(y[te], P), 4),
             "firstday_logloss": round(logloss(y[te][firstday], P[firstday]), 5),
             "w": [round(v, 4) for v in p[sl_[2]].tolist()], "slip": round(float(expit(p[-1])), 4) if slip else 0.0,
             "sd_student": round(float(p[sl_[0]].std()), 3), "sd_kc": round(float(p[sl_[1]].std()), 3)}
        if kslope:
            r["sd_kc_slope"] = round(float(p[sl_[3]].std()), 3)
        if sslope:
            r["sd_student_slope"] = round(float(p[sl_[4]].std()), 3)
        res.setdefault("fits", {})[name] = r
        print(name, json.dumps(r), f"{time.time() - t0:.0f}s", flush=True)
        return p

    lc, lf = np.log1p(d["C"].to_numpy()), np.log1p(d["F"].to_numpy())  # noqa: F841 (lc is read by run)
    opp = (d["C"] + d["F"]).to_numpy().astype(float)
    run("afm_linear", [opp])
    base = run("ours_noR", [lc, lf])
    for p_ in PHIS:
        run(f"ours_R_phi{p_}", [lc, lf], M=d[f"R{p_}"].to_numpy(), x0=base)
    gap = d["gap"].fillna(0).to_numpy()
    run("ours_noR_loggap", [lc, lf, np.log1p(gap), (d["gap"].isna()).to_numpy().astype(float)], x0=None)
    for wgt in (0.0, 0.25, 0.5, 1.0):
        ceff = d["Cd"].to_numpy() + wgt * d["Cx"].to_numpy()
        run(f"sameday_w{wgt}", [np.log1p(ceff), lf])
    le = np.log1p(d["E"].to_numpy())
    run("experience", [lc, lf, le, le * lc])
    run("kc_slopes", [lc, lf], kslope=True)
    run("student_slopes", [lc, lf], sslope=True)
    run("experience_kc_slopes", [lc, lf, le, le * lc], kslope=True)
    json.dump(res, open(out, "w"), indent=1)
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
