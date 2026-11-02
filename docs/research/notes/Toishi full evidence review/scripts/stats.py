import math
from math import comb

def binom_cdf(k, n, p):
    return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(0, k+1))

def binom_sf_ge(k, n, p):
    return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

def cp_upper(x, n, conf=0.95, one_sided=True):
    # exact (Clopper-Pearson) upper bound on error rate given x errors in n
    alpha = 1 - conf
    a = alpha if one_sided else alpha/2
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo+hi)/2
        # P(X <= x | p=mid) = a  -> find p
        if binom_cdf(x, n, mid) > a:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

def wilson(x, n, z=1.96):
    p = x/n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return c-h, c+h

print("== 0 errors found in n checked: 95% one-sided upper bound on true error rate")
for n in (30, 50, 100, 150, 200, 300, 600, 1000):
    print(f"n={n:5d}  exact CP upper={cp_upper(0,n):.4f}  rule-of-three={3/n:.4f}")

print("\n== P(see zero wrong keys among N viewed problems) if true wrong-key rate is p")
for p in (0.002, 0.005, 0.01, 0.02, 0.05):
    row = []
    for N_ in (50, 100, 200, 300, 600):
        row.append(f"N={N_}: {(1-p)**N_:.3f}")
    print(f"p={p:.3f}  " + "  ".join(row))

print("\n== N needed so that P(see >=1 wrong key) >= 0.95, true rate p")
for p in (0.002, 0.005, 0.01, 0.02, 0.05):
    print(f"p={p:.3f}  N>={math.ceil(math.log(0.05)/math.log(1-p))}")

print("\n== Tag-precision gate: pass if sample precision >= 85% (n sampled)")
for n in (30, 50, 100):
    need = math.ceil(0.85*n - 1e-9)
    print(f"n={n}: need >= {need} correct ({need/n:.3f})")
    for q in (0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
        print(f"   true precision {q:.2f}: P(pass)={binom_sf_ge(need, n, q):.3f}")
    # CI at exactly the threshold
    lo, hi = wilson(need, n)
    print(f"   Wilson 95% CI at {need}/{n}: [{lo:.3f}, {hi:.3f}]")
    # one-sided lower bound: largest n? Show 95% lower bound for observed 100% 
    # observed all correct
    # lower bound for q given x=n: alpha^(1/n)
    print(f"   if {n}/{n} correct, 95% one-sided lower bound on precision = {0.05**(1/n):.3f}")

print("\n== Consensus rule (80% of runs) with k runs: need >= ceil(0.8k) hits")
for k in (3,4,5):
    need = math.ceil(0.8*k - 1e-9)
    print(f"k={k}: main if hits >= {need}")
    for r in (0.5, 0.7, 0.8, 0.9, 0.95):
        print(f"   per-run inclusion prob {r:.2f}: P(kept as main)={binom_sf_ge(need, k, r):.3f}")

print("\n== Schwartz-Zippel style bound, d/|S| per point, m independent points")
for d in (5, 10, 20):
    for S_ in (100, 1000):
        for m in (5, 12):
            print(f"d={d} |S|={S_} m={m}: bound {(d/S_)**m:.3e}")
