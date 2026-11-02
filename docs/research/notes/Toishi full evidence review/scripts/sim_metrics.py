import statistics
from collections import Counter, defaultdict
from datetime import timedelta
from tests.engine.test_simulation import *
from core.engine import calibrate
runs = []
for seed in (1,2,3):
    w = World(STEADY, skills(60), start=START, days=DAYS, seed=seed); w.run(60); runs.append(w)
month = [START + timedelta(days=i) for i in range(30)]
print("budget: max problems/day", max(max(w.log.per_day.get(d,0) for d in month) for w in runs),
      "max rated/day", max(max(w.log.rated_per_day.get(d,0) for d in month) for w in runs),
      "mean problems/day", round(statistics.mean(statistics.mean(w.log.per_day.get(d,0) for d in month) for w in runs),1))
pairs = [(p, r > 1) for w in runs for _, _, r, p, _ in w.log.reviews if p is not None]
rep = calibrate(pairs); print("steady calib n", rep.total, "mean err", round(rep.mean_error,3), "notice", rep.notice)
f = World(FORGETFUL, skills(60), start=START, days=DAYS, seed=4); f.run(60)
rep = calibrate([(p, r > 1) for _, _, r, p, _ in f.log.reviews if p is not None]); print("forgetful mean err", round(rep.mean_error,3), "notice", rep.notice)
ratios = []
for w in runs:
    seq = defaultdict(list)
    for k, s, iv in w.log.intervals: seq[k].append((s, iv))
    for xs in seq.values():
        for (s1,a),(s2,b) in zip(xs, xs[1:]):
            if s2 == s1+1: ratios.append(b/a)
print("interval growth median", statistics.median(ratios), "shrinking", sum(r<1 for r in ratios), "/", len(ratios), "max interval", max(iv for w in runs for _,_,iv in w.log.intervals))
bt, ut, bp = [], [], []
for seed in (1,2,3):
    t, p, w = exam_run(seed, boosters=True); bt += t; bp += p
    u, _, _ = exam_run(seed, boosters=False); ut += u
print("exam-day true recall boosted", round(statistics.mean(bt),3), "unboosted", round(statistics.mean(ut),3), "projected>=.95", sum(x>=.95 for x in bp), "/", len(bp))
w = World(STRONG, skills(12), start=START, days=DAYS, seed=3); w.run(150)
print("strong 150d levels", Counter(s.level for s in w.states.values()))
