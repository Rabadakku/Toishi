"""Operating characteristics of the ENG-15 diagnostic set (3 or 4 fresh problems, >= 2 misses confirm)
against a truncated sequential probability ratio test (SPRT) with the same maximum length."""
from math import log
from itertools import product

def fixed_rule(k, p):
    # P(misses >= 2 of k)
    from math import comb
    q = 1 - p
    return sum(comb(k, m) * q**m * p**(k - m) for m in range(2, k + 1))

def sprt(p_true, p0=0.85, p1=0.55, alpha=0.10, beta=0.20, nmax=8):
    A = log((1 - beta) / alpha)   # accept "weak" when LLR >= A
    B = log(beta / (1 - alpha))   # accept "OK" when LLR <= B
    up = log((1 - p1) / (1 - p0))  # miss
    dn = log(p1 / p0)              # success
    # dynamic programming over (misses, successes) with absorption
    states = {(0, 0): 1.0}
    p_weak = 0.0
    exp_n = 0.0
    for n in range(nmax):
        new = {}
        for (m, s), pr in states.items():
            for outcome, prob in (("miss", 1 - p_true), ("succ", p_true)):
                m2, s2 = (m + 1, s) if outcome == "miss" else (m, s + 1)
                llr = m2 * up + s2 * dn
                pp = pr * prob
                if llr >= A:
                    p_weak += pp; exp_n += pp * (n + 1)
                elif llr <= B:
                    exp_n += pp * (n + 1)
                elif n + 1 == nmax:
                    exp_n += pp * (n + 1)
                    if llr > 0:
                        p_weak += pp
                else:
                    new[(m2, s2)] = new.get((m2, s2), 0.0) + pp
        states = new
    return p_weak, exp_n

print("true p | fixed 3-problem: P(confirm) | fixed 4-problem: P(confirm) | SPRT(p0=.85,p1=.55,a=.10,b=.20,max 8): P(confirm), E[n]")
for p in (0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40):
    pw, en = sprt(p)
    print(f"{p:.2f}   | {fixed_rule(3,p):.3f}                       | {fixed_rule(4,p):.3f}                        | {pw:.3f}, {en:.2f}")
print()
print("Variant: SPRT(p0=.85,p1=.55,a=.05,b=.20,max 10)")
for p in (0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40):
    pw, en = sprt(p, alpha=0.05, nmax=10)
    print(f"{p:.2f}   | {pw:.3f}, {en:.2f}")
