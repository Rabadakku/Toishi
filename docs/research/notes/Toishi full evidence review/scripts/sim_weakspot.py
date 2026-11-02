"""False-flag and power analysis of the ENG-15 weak-spot rule under simple assumptions.

Rule (spec): flag a skill when, over the last 30 days, z <= -2 versus the tier-predicted success,
with >= 5 problems' worth of evidence, misses on >= 3 different problems and on >= 2 different days.
Here every problem counts as 1 and "different days" is ignored (it can only lower the rates below).
"""
import numpy as np
from math import sqrt
from scipy.stats import binom

print("Exact binomial: P(flag) per skill-evaluation when the student's true success equals the predicted success p0")
print("n   p0=0.80   p0=0.85   p0=0.90   | power if true p=0.60 (p0=0.80)   true p=0.50 (p0=0.80)   true p=0.70 (p0=0.85)")
def flag_prob(n, p0, p_true):
    tot = 0.0
    for misses in range(0, n + 1):
        succ = n - misses
        z = (succ - n * p0) / sqrt(n * p0 * (1 - p0))
        if z <= -2 and misses >= 3:
            tot += binom.pmf(misses, n, 1 - p_true)
    return tot
for n in (5, 6, 7, 8, 10, 12, 15):
    print(f"{n:2d}  {flag_prob(n,.80,.80):.4f}    {flag_prob(n,.85,.85):.4f}    {flag_prob(n,.90,.90):.4f}   |  {flag_prob(n,.80,.60):.3f}                         {flag_prob(n,.80,.50):.3f}                       {flag_prob(n,.85,.70):.3f}")

print()
print("Confirmation by a diagnostic set (>= 2 misses of k fresh problems):")
for k in (3, 4):
    for p in (0.5, 0.6, 0.7, 0.8, 0.9):
        print(f"  k={k}, true success {p:.1f}: P(confirm) = {1 - binom.cdf(1, k, 1 - p):.3f}")
# ^ P(misses >= 2) with miss prob 1-p

print()
print("Monte Carlo: one course, S skills, daily evaluation over a 120-day semester, 30-day windows.")
rng = np.random.default_rng(11)
def sim(S=150, reviews_per_skill_per_30d=4.0, p_true_mean=0.85, p_pred_offset=0.0, days=120, weak_frac=0.0, weak_p=0.5, cap_sets_per_week=2):
    # each skill has Poisson-timed "problems' worth" events; expected success p_pred (Elo) vs true p
    flags = []  # (day, skill, is_weak, confirmed)
    sets_this_week = 0
    # build events
    rate = reviews_per_skill_per_30d / 30.0
    ev_days = [np.sort(np.nonzero(rng.random(days) < rate)[0]) for _ in range(S)]  # at most one per day
    weak = rng.random(S) < weak_frac
    p_true = np.where(weak, weak_p, np.clip(rng.normal(p_true_mean, 0.05, S), 0.5, 0.97))
    p_pred = np.clip(p_true + p_pred_offset, 0.3, 0.97)
    p_pred = np.where(weak, np.clip(rng.normal(p_true_mean, 0.05, S), 0.5, 0.97), p_pred)
    outcomes = [rng.random(len(ev_days[i])) < p_true[i] for i in range(S)]
    flagged_before = np.zeros(S, bool)
    n_false_flag = n_false_confirm = n_true_flag = n_true_confirm = 0
    for day in range(30, days):
        if day % 7 == 0:
            sets_this_week = 0
        for i in range(S):
            if flagged_before[i]:
                continue
            m = (ev_days[i] > day - 30) & (ev_days[i] <= day)
            n = int(m.sum())
            if n < 5:
                continue
            succ = int(outcomes[i][m].sum())
            misses = n - succ
            z = (succ - n * p_pred[i]) / sqrt(n * p_pred[i] * (1 - p_pred[i]))
            if z <= -2 and misses >= 3 and sets_this_week < cap_sets_per_week:
                sets_this_week += 1
                flagged_before[i] = True
                k = 4
                miss_k = int((rng.random(k) > p_true[i]).sum())
                conf = miss_k >= 2
                if weak[i]:
                    n_true_flag += 1; n_true_confirm += conf
                else:
                    n_false_flag += 1; n_false_confirm += conf
    return n_false_flag, n_false_confirm, n_true_flag, n_true_confirm, int(weak.sum())

for label, kw in [
    ("calibrated Elo, no weak skills (pure false alarms)", dict(weak_frac=0.0)),
    ("Elo over-optimistic by 0.05, no weak skills", dict(weak_frac=0.0, p_pred_offset=0.05)),
    ("Elo over-optimistic by 0.10, no weak skills", dict(weak_frac=0.0, p_pred_offset=0.10)),
    ("calibrated, 8% of skills truly weak (p=0.5)", dict(weak_frac=0.08)),
    ("calibrated, 8% truly weak, only 2.5 problems/skill/30d", dict(weak_frac=0.08, reviews_per_skill_per_30d=2.5)),
    ("calibrated, 8% truly weak, 6 problems/skill/30d", dict(weak_frac=0.08, reviews_per_skill_per_30d=6.0)),
]:
    res = np.array([sim(**kw) for _ in range(200)])
    m = res.mean(axis=0)
    print(f"{label:58s} false flags/semester {m[0]:.2f}, false confirms {m[1]:.2f}, true flags {m[2]:.2f}/{m[4]:.1f} weak, true confirms {m[3]:.2f}")
