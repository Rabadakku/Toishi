"""Steady-state review workload and average recall vs desired retention, FSRS-6 default parameters (py-fsrs 6.3.2).

Skills are learned on random days in 0-89 (first review Good on the learning day), then reviewed when due:
success with probability equal to the model's retrievability at that moment, success -> Good, failure -> Again.
Measured over days 120-419. Averaged over seeds.
No fuzz, no learning steps, max interval 365 (the spec's ENG-1 settings).
"""
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler

T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
W20 = 0.1542
F = 0.9 ** (-1 / W20) - 1


def retr(c, now):
    t = (now - c.last_review).total_seconds() / 86400.0
    return (1 + F * t / c.stability) ** (-W20)


def run(dr, seed, n=150, start=120, end=420):
    rnd = random.Random(seed)
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    learn_day = [rnd.randrange(0, 90) for i in range(n)]
    cards = [None] * n
    reviews = 0
    lapses = 0
    rsum = 0.0
    rcount = 0
    r_at_review = 0.0
    for d in range(end):
        now = T0 + timedelta(days=d)
        for i in range(n):
            if learn_day[i] == d:
                c = Card()
                c, _ = sch.review_card(c, Rating.Good, now)
                cards[i] = c
        for i in range(n):
            c = cards[i]
            if c is None or learn_day[i] >= d:
                continue
            r = retr(c, now)
            if d >= start:
                rsum += r
                rcount += 1
            if c.due <= now:
                ok = rnd.random() < r
                c, _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
                cards[i] = c
                if d >= start:
                    reviews += 1
                    r_at_review += r
                    if not ok:
                        lapses += 1
    days = end - start
    return reviews / (n * days), rsum / rcount, lapses / max(reviews, 1), r_at_review / max(reviews, 1)


DRS = (0.70, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95)
SEEDS = range(12)
res = {}
for dr in DRS:
    rows = [run(dr, s) for s in SEEDS]
    res[dr] = [sum(x[k] for x in rows) / len(rows) for k in range(4)]
base = res[0.90][0]
print("DR     reviews/skill/day   relative to 0.90   mean R (all skill-days)   lapse share of reviews   mean R at review")
for dr in DRS:
    a, b, c, d = res[dr]
    print(f"{dr:.2f}   {a:.4f}              {a/base:5.2f}x             {b:.3f}                    {c:.3f}                    {d:.3f}")
