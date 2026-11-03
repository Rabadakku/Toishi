"""Do students differ in how fast they speed up? (run with python -I)

Usage: speed_slopes.py statics STEP_CSV OUT_JSON | speed_slopes.py ednet KT1_ZIP QUESTIONS_CSV OUT_JSON [n_users]

On correct first tries with a time: log time minus the item's mean (item effect removed,
student effect kept). Per student, an OLS slope of that residual on ln(1 + practice count),
where practice is the count of the student's earlier attempts on the same KC (Statics) or on
any part-5 question (EdNet). The true spread of slopes is the observed variance minus the mean
squared standard error. Slow starters: early speed measured on odd attempts of the first
quintile, change measured as the last quintile minus the even attempts of the first quintile,
so the two share no attempts (no regression-to-the-mean artifact from shared noise).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import times  # noqa: E402  (loaders)


def item_effects(lt: np.ndarray, i: np.ndarray, s: np.ndarray, iters: int = 30) -> np.ndarray:
    """Item effects net of student effects (alternating projections, as times.two_way)."""
    ni, ns = i.max() + 1, s.max() + 1
    ci, cs = np.bincount(i, minlength=ni), np.bincount(s, minlength=ns)
    v = lt - lt.mean()
    a, b = np.zeros(ni), np.zeros(ns)
    for _ in range(iters):
        a = np.bincount(i, v - b[s], ni) / ci
        b = np.bincount(s, v - a[i], ns) / cs
    return a[i]


def prepare(d: pd.DataFrame) -> pd.DataFrame:
    ok = d[(d["y"] == 1) & (d["secs"] > 0)].copy()
    ok = ok[ok["secs"] <= ok["secs"].quantile(0.99)]
    ok = ok[ok.groupby("item")["item"].transform("size") >= 5]
    ok = ok[ok.groupby("s")["s"].transform("size") >= 40]
    ok["lt"] = np.log(ok["secs"])
    i = pd.factorize(ok["item"])[0]
    s = pd.factorize(ok["s"])[0]
    # residual after item effects estimated net of student speed; the student's level is kept
    ok["r"] = ok["lt"] - ok["lt"].mean() - item_effects(ok["lt"].to_numpy(), i, s)
    # practice counts net of item position: everyone meets item j after similar practice, so
    # without this the item effects absorb the practice effect (times.analyse does the same)
    for col in ("n", "n_all"):
        if col in ok:
            x = np.log1p(ok[col].to_numpy(float))
            ok[col + "_x"] = x - x.mean() - item_effects(x, i, s)
    return ok


def slopes(ok: pd.DataFrame, col: str) -> dict:
    rows = []
    for s, g in ok.groupby("s", sort=False):
        x = g[col + "_x"].to_numpy()
        y = g["r"].to_numpy()
        if x.std() < 1e-9:
            continue
        xc, yc = x - x.mean(), y - y.mean()
        b = (xc * yc).sum() / (xc * xc).sum()
        res = yc - b * xc
        se2 = (res @ res) / (len(y) - 2) / (xc * xc).sum()
        rows.append((b, se2, len(y)))
    a = np.array(rows)
    b, se2 = a[:, 0], a[:, 1]
    var_true = max(0.0, b.var() - se2.mean())
    return {
        "students": int(len(a)),
        "median_attempts": float(np.median(a[:, 2])),
        "alpha_mean": float(-b.mean()),
        "alpha_median": float(-np.median(b)),
        "alpha_sd_observed": float(b.std()),
        "alpha_sd_true": float(np.sqrt(var_true)),
        "alpha_p10_p90_true_normal": [float(-b.mean() - 1.2816 * np.sqrt(var_true)), float(-b.mean() + 1.2816 * np.sqrt(var_true))],
        "share_slower_with_practice": float((b > 0).mean()),
    }


def slow_starters(ok: pd.DataFrame) -> dict:
    early, change, total = [], [], []
    for s, g in ok.groupby("s", sort=False):
        r = g["r"].to_numpy()
        n = len(r)
        q = n // 5
        if q < 8:
            continue
        first, last = r[:q], r[-q:]
        e_odd, e_even = first[1::2], first[0::2]
        early.append(e_odd.mean())
        change.append(last.mean() - e_even.mean())
        total.append(n)
    early, change = np.array(early), np.array(change)
    third = np.quantile(early, [1 / 3, 2 / 3])
    slow, fast = change[early >= third[1]], change[early <= third[0]]
    return {
        "students": int(len(early)),
        "median_attempts": float(np.median(total)),
        "corr_early_speed_vs_change": float(np.corrcoef(early, change)[0, 1]),
        "mean_change_all_log": float(change.mean()),
        "speedup_factor_all": float(np.exp(change.mean())),
        "speedup_factor_slowest_third": float(np.exp(slow.mean())),
        "speedup_factor_fastest_third": float(np.exp(fast.mean())),
        "early_gap_slowest_vs_fastest_third_factor": float(np.exp(early[early >= third[1]].mean() - early[early <= third[0]].mean())),
    }


def pooled_both(ok: pd.DataFrame) -> dict | None:
    """Statics: KC practice and overall practice together, within student."""
    if "n_all" not in ok or "n" not in ok:
        return None
    x1 = ok["n_x"].to_numpy()
    x2 = ok["n_all_x"].to_numpy()
    s = pd.factorize(ok["s"])[0]
    def dm(v):
        return v - (np.bincount(s, v) / np.bincount(s))[s]
    X = np.column_stack([dm(x1), dm(x2)])
    y = dm(ok["r"].to_numpy())
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {"alpha_kc": float(-beta[0]), "alpha_overall": float(-beta[1])}


def load(argv: list[str]) -> tuple[pd.DataFrame, str, str]:
    captured: dict = {}

    def grab(d: pd.DataFrame) -> dict:
        captured["d"] = d
        return {}

    times.analyse = grab
    if argv[1] == "statics":
        cols = ["Anon Student Id", "Problem Name", "Step Name", "First Transaction Time", "First Attempt", "KC (F2011)", "Step Duration (sec)"]
        raw = pd.read_csv(argv[2], usecols=cols, dtype=str).dropna(subset=["KC (F2011)", "First Transaction Time"])
        raw["t"] = pd.to_datetime(raw["First Transaction Time"], errors="coerce")
        raw = raw.dropna(subset=["t"]).sort_values(["Anon Student Id", "t"], kind="stable")
        d = pd.DataFrame({
            "s": raw["Anon Student Id"].to_numpy(),
            "item": (raw["Problem Name"] + "|" + raw["Step Name"]).to_numpy(),
            "kc": raw["KC (F2011)"].str.split("~~").str[0].to_numpy(),
            "y": (raw["First Attempt"] == "correct").astype(int).to_numpy(),
            "secs": pd.to_numeric(raw["Step Duration (sec)"], errors="coerce").to_numpy(),
        })
        d["n"] = d.groupby(["s", "kc"]).cumcount()
        return d, argv[3], "statics"
    times.ednet(argv[2], argv[3], int(argv[5]) if len(argv) > 5 else 3000)
    return captured["d"], argv[4], "ednet"


def main() -> None:
    d, out, name = load(sys.argv)
    if name == "statics":
        d["n_all"] = d.groupby("s").cumcount()
    ok = prepare(d)
    res = {"dataset": name, "timed_correct": int(len(ok))}
    res["per_student_slope"] = slopes(ok, "n")
    if name == "statics":
        res["per_student_slope_overall_practice"] = slopes(ok, "n_all")
        res["pooled_kc_vs_overall"] = pooled_both(ok)
    res["slow_starters"] = slow_starters(ok)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
