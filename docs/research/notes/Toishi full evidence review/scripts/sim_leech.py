import random, sys, statistics
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler
T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
def time_to_leech(q, threshold, rnd, dr=0.90, horizon=400):
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    c, _ = sch.review_card(Card(), Rating.Good, T0)   # learned
    lapses = 0; reviews = 0
    d = 0
    while True:
        due = c.due
        d = (due - T0).days
        if d > horizon:
            return None, reviews, lapses
        now = T0 + timedelta(days=d)
        ok = rnd.random() < q
        c, _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
        reviews += 1
        if not ok:
            lapses += 1
            if lapses >= threshold:
                return d, reviews, lapses
rnd = random.Random(3)
print("true per-review success q | threshold | share reaching threshold within 400 d | median days | median reviews")
for q in (0.5, 0.6, 0.7, 0.8, 0.9):
    for th in (4, 6, 8):
        res = [time_to_leech(q, th, rnd) for _ in range(400)]
        hit = [r for r in res if r[0] is not None]
        md = statistics.median([r[0] for r in hit]) if hit else float('nan')
        mr = statistics.median([r[1] for r in hit]) if hit else float('nan')
        print(f"{q:.1f} | {th} | {len(hit)/len(res):.2f} | {md:.0f} | {mr:.0f}")
