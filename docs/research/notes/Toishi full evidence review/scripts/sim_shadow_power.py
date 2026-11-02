import numpy as np
from scipy import stats
rng = np.random.default_rng(5)
def power(n, delta, base=0.85, sims=4000):
    hits = 0
    for _ in range(sims):
        p = np.clip(rng.normal(base, 0.06, n), 0.5, 0.97)       # true P(success) for the credited skill's next review
        y = rng.random(n) < p
        pa = np.clip(p - delta, 0.01, 0.99)                      # plain FSRS misses the implicit credit
        la = -(y*np.log(pa) + (~y)*np.log(1-pa))
        lb = -(y*np.log(p) + (~y)*np.log(1-p))
        d = la - lb
        t = d.mean() / (d.std(ddof=1)/np.sqrt(n))
        hits += (t > 1.645)
    return hits / sims
print("power (one-sided alpha .05) to detect that credited predictions beat plain FSRS in held-out log loss")
print("n credited-skill reviews | delta=0.02 | 0.03 | 0.05 | 0.08")
for n in (100, 200, 400, 800, 1600):
    print(n, *[f"{power(n, d):.2f}" for d in (0.02, 0.03, 0.05, 0.08)])
