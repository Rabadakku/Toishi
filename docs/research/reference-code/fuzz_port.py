import math
def rround(x):  # Rust f32::round: half away from zero
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))
RANGES = [(2.5, 7.0, 0.15), (7.0, math.inf, 0.1) if False else (7.0, 20.0, 0.1), (20.0, math.inf, 0.05)]
def fuzz_delta(i):
    if i < 2.5: return 0.0
    d = 1.0
    for s, e, f in RANGES:
        d += f * max(min(i, e) - s, 0.0)
    return d
def fuzz_bounds(i):
    d = fuzz_delta(i); return rround(i - d), rround(i + d)
def constrained(i, mn, mx):
    mn = min(mn, mx); i = min(max(i, mn), mx)
    lo, up = fuzz_bounds(i)
    lo = min(max(lo, mn), mx); up = min(max(up, mn), mx)
    if up == lo and up > 2 and up < mx: up = lo + 1
    return lo, up
def with_fuzz(factor, i, mn, mx):
    if factor is None: return min(max(rround(i), mn), mx)
    lo, up = constrained(i, mn, mx)
    return int(math.floor(lo + factor * (1 + up - lo)))
def min_fuzz_interval(i, prev, mx):
    r = rround(i); _, up = constrained(i, 1, mx)
    if r > prev: return prev + 1
    if prev <= up: return prev
    return 0
if __name__ == "__main__":
    t = [(1.0,1,1000,1,1,1),(2.49,1,1000,2,2,2),(2.5,1,1000,2,3,4),(7.0,1,1000,5,7,9),(17.0,1,1000,14,17,20),
         (37.0,1,1000,33,37,41),(2.0,2,1000,2,2,2),(2.0,3,1000,3,4,4),(2.0,3,3,3,3,3),(6.9,3,1000,5,7,9),
         (19.9,3,1000,17,20,23),(20.1,3,1000,17,20,23),(100.0,101,1000,101,105,108),(100.0,1,99,92,96,99),(100.0,97,103,97,100,103)]
    ok=True
    for i,mn,mx,lo,mid,up in t:
        got=tuple(with_fuzz(f,i,mn,mx) for f in (0.0,0.5,0.99))
        if got!=(lo,mid,up): ok=False; print("MISMATCH",i,mn,mx,got,(lo,mid,up))
    print("all Anki fuzz.rs unit-test rows reproduced:", ok)
