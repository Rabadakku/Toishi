import random, statistics, time
from tests.engine.diagnosis.fixtures import *
from tests.engine.diagnosis.sim import Learner, Run, agains

def base_world():
    w = world()
    for k in (ALG, POW): seed(w, k, stability=60, days_ago=4, theta=2.0)
    seed(w, CRIT, stability=10, days_ago=10, theta=1.0)
    for k in (PROD, QUOT): seed(w, k, stability=15, days_ago=10, theta=1.5)
    seed(w, MC, stability=10, days_ago=10, theta=1.0)
    return w

t0=time.time()
res=[]
for sd in range(30):
    w = base_world()
    L = Learner(ability={ALG: 0.5}, honesty=0.6, rng=random.Random(sd))
    r = Run(w, L, focus=[CRIT], rng=random.Random(100+sd))
    n = r.until(lambda: agains(w, ALG) > 0, max_days=20)
    res.append(n)
print("prereq gap: problems to ALG Again", res, "median", statistics.median([x for x in res if x]), time.time()-t0)
res=[]
for sd in range(30):
    w = base_world()
    L = Learner(choose=0.4, honesty=0.6, rng=random.Random(sd))
    r = Run(w, L, focus=[PROD, QUOT], rng=random.Random(100+sd))
    n = r.until(lambda: agains(w, MC) > 0, max_days=20)
    res.append(n)
print("method gap: problems to MC Again", res, "median", statistics.median([x for x in res if x]))
# slips only
for sd in range(5):
    w = base_world()
    L = Learner(default=0.99, slip=0.12, honesty=0.8, rng=random.Random(sd))
    r = Run(w, L, focus=[CRIT], per_day=3, rng=random.Random(100+sd))
    r.until(lambda: False, max_days=60)
    lapses = {k: agains(w, k) for k in (CRIT, POW, ALG)}
    slips = [a.extra["diagnosis"].get("slip") for a in w.attempts if a.extra.get("diagnosis",{}).get("slip")]
    print("slips", r.problems, r.misses, lapses, "weak", r.weak_spots, {s: slips.count(s) for s in set(slips)})
print(time.time()-t0)
