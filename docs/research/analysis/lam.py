"""Offline check of the combination rule: P_raw = (1 - s) * prod(q_k ** lam)."""
import pickle, sys
import numpy as np

def fit_recal(z, y):
    a, b = 0.0, 1.0
    for _ in range(60):
        q = 1 / (1 + np.exp(-(a + b * z)))
        g = np.array([(q - y).sum(), ((q - y) * z).sum()])
        w = q * (1 - q)
        h = np.array([[w.sum(), (w * z).sum()], [(w * z).sum(), (w * z * z).sum()]])
        a, b = np.array([a, b]) - np.linalg.solve(h + 1e-9 * np.eye(2), g)
    return np.clip(1 / (1 + np.exp(-(a + b * z))), 1e-6, 1 - 1e-6)

d = pickle.load(open(sys.argv[1], "rb"))
y = np.array([r[0] for r in d["rows"]], float)
lq = [np.log(np.clip(np.array(r[2]), 1e-9, 1)) for r in d["rows"]]
k = np.array([len(r[2]) for r in d["rows"]])
mins = np.array([x.min() for x in lq]); sums = np.array([x.sum() for x in lq])
s = d["slip"]
variants = [("product", sums)] + [(f"K^-{c}", sums * k ** (-c)) for c in (0.5, 0.75, 1.0)] + [("min", mins)]
for name, logprod in variants:
    p = np.clip((1 - s) * np.exp(logprod), 1e-6, 1 - 1e-6)
    q = fit_recal(np.log(p / (1 - p)), y)
    ll = -(y * np.log(q) + (1 - y) * np.log1p(-q))
    m = k > 1
    print(f"{name:9s} recal_ll={ll.mean():.5f} multi_ll={ll[m].mean():.5f} single_ll={ll[~m].mean():.5f} bias_multi={q[m].mean()-y[m].mean():+.4f} bias_single={q[~m].mean()-y[~m].mean():+.4f}")
