"""Effect on steady-state workload of grading a share h of successful reviews Hard instead of Good (ENG-14), FSRS-6 defaults, DR 0.90."""
import random, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler
T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
W20 = 0.1542
F = 0.9 ** (-1 / W20) - 1
def retr(c, now):
    t = (now - c.last_review).total_seconds() / 86400.0
    return (1 + F * t / c.stability) ** (-W20)
def run(h, seed, dr=0.90, n=150, start=120, end=420):
    rnd = random.Random(seed)
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    learn_day = [rnd.randrange(0, 90) for _ in range(n)]
    cards = [None]*n; reviews = 0; lapses = 0; rs = 0.0; rc = 0
    for d in range(end):
        now = T0 + timedelta(days=d)
        for i in range(n):
            if learn_day[i] == d:
                c, _ = sch.review_card(Card(), Rating.Good, now); cards[i] = c
        for i in range(n):
            c = cards[i]
            if c is None or learn_day[i] >= d: continue
            r = retr(c, now)
            if d >= start: rs += r; rc += 1
            if c.due <= now:
                ok = rnd.random() < r
                rating = Rating.Again if not ok else (Rating.Hard if rnd.random() < h else Rating.Good)
                c, _ = sch.review_card(c, rating, now); cards[i] = c
                if d >= start:
                    reviews += 1; lapses += (not ok)
    days = end - start
    return reviews/(n*days), rs/rc, lapses/max(reviews,1)
base=None
print("share of passes graded Hard | reviews/skill/day | relative to h=0 | mean R over skill-days | lapse share of reviews")
for h in (0.0, 0.05, 0.10, 0.20, 0.40):
    rows=[run(h,s) for s in range(16)]
    m=[sum(x[k] for x in rows)/len(rows) for k in range(3)]
    if base is None: base=m[0]
    print(f"{h:.2f} | {m[0]:.4f} | {m[0]/base:.2f}x | {m[1]:.3f} | {m[2]:.3f}")
