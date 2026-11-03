"""Response-time structure on public logs (run with python -I).

Usage: times.py statics STEP_CSV OUT_JSON | times.py ednet KT1_ZIP QUESTIONS_CSV OUT_JSON [n_users]

On correct first tries: the spread of log time in total, after item effects, after item and
student effects (the model's sigma_T), the practice speedup alpha in
ln T = item + student - alpha ln(1 + n), and the split-half reliability of student speed.
"""

import json
import sys
import zipfile

import numpy as np
import pandas as pd


def two_way(v: np.ndarray, i: np.ndarray, s: np.ndarray, iters: int = 30) -> np.ndarray:
    """v minus item and student effects (alternating projections)."""
    ni, ns = i.max() + 1, s.max() + 1
    ci, cs = np.bincount(i, minlength=ni), np.bincount(s, minlength=ns)
    r = v - v.mean()
    for _ in range(iters):
        r = r - (np.bincount(i, r, ni) / ci)[i]
        r = r - (np.bincount(s, r, ns) / cs)[s]
    return r


def analyse(d: pd.DataFrame) -> dict:
    """d: s, item, n (prior practice), secs, y; time order within student."""
    out: dict = {"rows": len(d)}
    wrong = d[(d["y"] == 0) & (d["secs"] > 0)]
    ok = d[(d["y"] == 1) & (d["secs"] > 0)].copy()
    out["median_secs_correct"] = float(ok["secs"].median())
    out["median_ratio_wrong_to_correct"] = float(wrong["secs"].median() / ok["secs"].median()) if len(wrong) else None
    cap = ok["secs"].quantile(0.99)
    ok = ok[ok["secs"] <= cap]
    ok = ok[ok.groupby("item")["item"].transform("size") >= 5]
    ok = ok[ok.groupby("s")["s"].transform("size") >= 10]
    lt = np.log(ok["secs"].to_numpy())
    i = pd.factorize(ok["item"])[0]
    s = pd.factorize(ok["s"])[0]
    out["n_timed"] = len(ok)
    out["sd_log_total"] = float(lt.std())
    ri = lt - (np.bincount(i, lt) / np.bincount(i))[i]
    out["sd_log_after_item"] = float(ri.std())
    r = two_way(lt, i, s)
    out["sd_log_after_item_student"] = float(r.std())
    out["resid_share_beyond_3sd"] = float((np.abs(r) > 3 * r.std()).mean())
    x = two_way(np.log1p(ok["n"].to_numpy().astype(float)), i, s)
    out["alpha"] = float(-(x * r).sum() / (x * x).sum())
    # student speed: mean of (lt - item effect) on even vs odd items, students with 20+ of each
    par = pd.Series(ok["item"]).map(hash).to_numpy() % 2
    sp = pd.DataFrame({"s": s, "p": par, "r": ri}).groupby(["s", "p"])["r"].agg(["mean", "size"]).unstack()
    sp = sp[(sp["size"][0] >= 20) & (sp["size"][1] >= 20)]
    out["speed_split_half_r"] = float(np.corrcoef(sp["mean"][0], sp["mean"][1])[0, 1]) if len(sp) > 10 else None
    out["sd_student_speed"] = float(pd.Series(ri).groupby(s).mean().std())
    out["students_speed_split"] = int(len(sp))
    return out


def statics(path: str) -> dict:
    cols = ["Anon Student Id", "Problem Name", "Step Name", "First Transaction Time", "First Attempt", "KC (F2011)", "Correct Step Duration (sec)", "Step Duration (sec)"]
    d = pd.read_csv(path, usecols=cols, dtype=str).dropna(subset=["KC (F2011)", "First Transaction Time"])
    d = pd.DataFrame({
        "s": d["Anon Student Id"].to_numpy(),
        "item": (d["Problem Name"] + "|" + d["Step Name"]).to_numpy(),
        "kc": d["KC (F2011)"].str.split("~~").str[0].to_numpy(),
        "y": (d["First Attempt"] == "correct").astype(int).to_numpy(),
        "secs": pd.to_numeric(d["Step Duration (sec)"], errors="coerce").to_numpy(),
    })
    d["n"] = d.groupby(["s", "kc"]).cumcount()
    return analyse(d)


def ednet(zpath: str, qpath: str, n_users: int, seed: int = 0) -> dict:
    q = pd.read_csv(qpath)
    q = q[q["part"] == 5].set_index("question_id")
    z = zipfile.ZipFile(zpath)
    names = [n for n in z.namelist() if n.endswith(".csv")]
    rng = np.random.default_rng(seed)
    rng.shuffle(names)
    frames, used = [], 0
    for n in names:
        u = pd.read_csv(z.open(n))
        if len(u) < 100:
            continue
        u = u[u["question_id"].isin(q.index)].drop_duplicates("question_id")
        if len(u) < 30:
            continue
        u = u.sort_values("timestamp", kind="stable")
        u["s"] = n
        frames.append(u)
        used += 1
        if used >= n_users:
            break
    d = pd.concat(frames, ignore_index=True)
    d["y"] = (d["user_answer"] == q.loc[d["question_id"], "correct_answer"].to_numpy()).astype(int)
    d["item"] = d["question_id"]
    d["secs"] = d["elapsed_time"] / 1000.0
    d["n"] = d.groupby("s").cumcount()  # prior part-5 questions answered
    out = analyse(d)
    out["users"] = used
    return out


def main() -> None:
    if sys.argv[1] == "statics":
        res, out = statics(sys.argv[2]), sys.argv[3]
    else:
        res, out = ednet(sys.argv[2], sys.argv[3], int(sys.argv[5]) if len(sys.argv) > 5 else 3000), sys.argv[4]
    res["dataset"] = sys.argv[1]
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
