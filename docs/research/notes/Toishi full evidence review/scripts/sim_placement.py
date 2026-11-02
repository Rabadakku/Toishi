"""Placement check (spec "Placement check", core/engine/placement.py) on synthetic layered skill graphs.

Policy A (as implemented): ask the deepest unresolved skill first (longest prerequisite chain, ties random);
a pass marks every transitive prerequisite provisionally known; a fail or "I don't know" changes nothing; stop at 25.
Policy B (alternative, ALEKS / Math Academy style): ask the unresolved skill that best splits the unresolved set
(maximise min(gain if pass, gain if fail)); a pass resolves its prerequisites as known, a fail resolves its
dependents as unknown; stop at 25.

Student: knows a downward-closed set (skill known only if all prerequisites known), difficulty rises with layer.
Responses: known -> pass with prob 1-slip; unknown -> pass with prob guess.
Outcome: share of truly known skills that the check seeds as known (sensitivity), share of seeded skills that are
truly unknown (false-known), and truly known skills left as new (wasted learning phases).
"""
import random
import sys

def make_graph(rnd, layers, width):
    n = layers * width
    layer_of = [i // width for i in range(n)]
    req = [[] for _ in range(n)]
    for i in range(width, n):
        l = layer_of[i]
        k = rnd.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        pool_prev = list(range((l - 1) * width, l * width))
        pool_prev2 = list(range((l - 2) * width, (l - 1) * width)) if l >= 2 else []
        chosen = set()
        while len(chosen) < k:
            src = pool_prev2 if (pool_prev2 and rnd.random() < 0.2) else pool_prev
            chosen.add(rnd.choice(src))
        req[i] = sorted(chosen)
    return n, layer_of, req

def closure(n, req):
    anc = [None] * n
    def get(i):
        if anc[i] is not None:
            return anc[i]
        s = set()
        for r in req[i]:
            s.add(r)
            s |= get(r)
        anc[i] = s
        return s
    for i in range(n):
        get(i)
    desc = [set() for _ in range(n)]
    for i in range(n):
        for a in anc[i]:
            desc[a].add(i)
    return anc, desc

def depths(n, req):
    d = [0] * n
    for i in range(n):  # skills are numbered by layer, prerequisites have lower index
        d[i] = 1 + max((d[r] for r in req[i]), default=-1)
    return d

def make_student(rnd, n, layer_of, req, layers, target):
    b = [layer_of[i] / layers + rnd.gauss(0, 0.12) for i in range(n)]
    def known_for(theta):
        known = [False] * n
        for i in range(n):
            known[i] = b[i] <= theta and all(known[r] for r in req[i])
        return known
    lo, hi = -0.5, 1.6
    for _ in range(40):
        mid = (lo + hi) / 2
        k = sum(known_for(mid)) / n
        if k < target:
            lo = mid
        else:
            hi = mid
    return known_for((lo + hi) / 2)

def respond(rnd, truth, i, slip, guess):
    return rnd.random() < ((1 - slip) if truth[i] else guess)

def policy_a(rnd, n, req, anc, desc, dep, truth, slip, guess, q=25):
    order = sorted(range(n), key=lambda i: (-dep[i], rnd.random()))
    answered = {}
    inferred = set()
    for i in order:
        if len(answered) >= q:
            break
        if i in answered or i in inferred:
            continue
        ok = respond(rnd, truth, i, slip, guess)
        answered[i] = ok
        if ok:
            inferred |= anc[i]
    seeded = {i for i, ok in answered.items() if ok} | {i for i in inferred if answered.get(i) is not False}
    return seeded

def policy_b(rnd, n, req, anc, desc, dep, truth, slip, guess, q=25):
    known = set()
    unknown = set()
    answered = {}
    for _ in range(q):
        unresolved = set(range(n)) - known - unknown
        if not unresolved:
            break
        best, best_key = None, None
        for c in unresolved:
            gp = 1 + len(anc[c] & unresolved)
            gf = 1 + len(desc[c] & unresolved)
            key = (min(gp, gf), gp + gf, rnd.random())
            if best_key is None or key > best_key:
                best, best_key = c, key
        ok = respond(rnd, truth, best, slip, guess)
        answered[best] = ok
        if ok:
            known |= {best} | (anc[best] - unknown)
        else:
            unknown |= {best} | (desc[best] - known)
    return known

def run(layers, width, slip, guess, targets, draws, seed):
    rows = []
    for target in targets:
        res = {"A": [0, 0, 0, 0], "B": [0, 0, 0, 0]}
        actual = 0.0
        for d in range(draws):
            rnd = random.Random(f"{seed}-{layers}-{width}-{target}-{d}")
            n, layer_of, req = make_graph(rnd, layers, width)
            anc, desc = closure(n, req)
            dep = depths(n, req)
            truth = make_student(rnd, n, layer_of, req, layers, target)
            nk = sum(truth)
            actual += nk / n
            for name, fn in (("A", policy_a), ("B", policy_b)):
                seeded = fn(random.Random(f"{seed}-{name}-{d}-{target}"), n, req, anc, desc, dep, truth, slip, guess)
                tp = sum(1 for i in seeded if truth[i])
                fp = len(seeded) - tp
                res[name][0] += (tp / nk) if nk else 0.0
                res[name][1] += (fp / len(seeded)) if seeded else 0.0
                res[name][2] += nk - tp
                res[name][3] += len(seeded)
        rows.append((target, actual / draws, {k: [x / draws for x in v] for k, v in res.items()}))
    return rows

if __name__ == "__main__":
    draws = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    for layers, width in ((10, 20), (15, 13)):
        for slip, guess in ((0.05, 0.03), (0.10, 0.10)):
            print(f"\n=== {layers} layers x {width} skills = {layers*width}; slip {slip}, guess {guess}; {draws} draws; 25 questions")
            print("true known share | A sens | A false-known | A known-left-new | A seeded | B sens | B false-known | B known-left-new | B seeded")
            for target, act, r in run(layers, width, slip, guess, (0.1, 0.25, 0.5, 0.75, 0.9), draws, 7):
                a, b = r["A"], r["B"]
                print(f"{act:.2f} | {a[0]:.2f} | {a[1]:.3f} | {a[2]:.1f} | {a[3]:.1f} | {b[0]:.2f} | {b[1]:.3f} | {b[2]:.1f} | {b[3]:.1f}")
