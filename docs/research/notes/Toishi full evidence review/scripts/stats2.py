# Exact-binomial checks cited in content_and_answer_checking.md (Sections 4, 7, 8, 12)
from math import comb

def sf(k, n, p):  # P(X >= k)
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def pmf(n, p):
    return [comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)]

def notice_prob(n, p_rep, p_first, thr=0.15):
    a, b = pmf(n, p_rep), pmf(n, p_first)
    return sum(a[i] * b[j] for i in range(n + 1) for j in range(n + 1) if (i - j) / n >= thr - 1e-12)

print("Smallest k correct that certifies true precision > 0.85 at 95% one-sided confidence")
for n in (30, 50, 100, 150):
    for k in range(n + 1):
        if sf(k, n, 0.85) <= 0.05:
            print(f"  n={n}: k>={k} (tail under p=0.85: {sf(k, n, 0.85):.4f})")
            break

print("ENG-5 notice (repeated beats first-seen by >= 15 points), two independent groups of 30")
print("  false alarm, both 0.8:", round(notice_prob(30, .8, .8), 4))
print("  false alarm, both 0.6:", round(notice_prob(30, .6, .6), 4))
print("  false alarm, both 0.5:", round(notice_prob(30, .5, .5), 4))
print("  power, 0.95 vs 0.80  :", round(notice_prob(30, .95, .80), 4))
print("  power, 0.90 vs 0.75  :", round(notice_prob(30, .90, .75), 4))
print("  smallest reachable gap >= 0.15 with n=30:", min(d for d in range(31) if d / 30 >= 0.15 - 1e-12), "of 30")
