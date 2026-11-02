"""Workload and knowledge vs desired retention with py-fsrs 6.3.2 defaults.

Cohort of skills all learned on day 0 (first review Good). Each is reviewed on its due
day; success is drawn with probability equal to the model's own retrievability (so the
simulated learner forgets exactly as FSRS predicts). Success -> Good, failure -> Again.
Fuzz off, no learning steps (same settings as the spec's ENG-1).
"""
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
from fsrs import Card, Rating, Scheduler

HORIZON = 120  # one semester
N = 300
rng = np.random.default_rng(7)
T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)


def run(dr: float, horizon: int = HORIZON, boost_day: int | None = None, boost_target: float | None = None):
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    cards = []
    for _ in range(N):
        c = Card()
        c, _ = sch.review_card(c, Rating.Good, T0)  # learned on day 0
        cards.append(c)
    reviews_per_day = np.zeros(horizon + 1)
    r_sum = np.zeros(horizon + 1)
    lapses = 0
    for d in range(1, horizon + 1):
        now = T0 + timedelta(days=d)
        for i, c in enumerate(cards):
            r = sch.get_card_retrievability(c, now)
            r_sum[d] += r
            if c.due <= now:
                ok = rng.random() < r
                c, _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
                cards[i] = c
                reviews_per_day[d] += 1
                if not ok:
                    lapses += 1
    return reviews_per_day, r_sum / N, lapses


print("DR   reviews/skill (120d)  reviews/skill days 61-120   mean R over days 1-120   mean R on day 120   lapses/skill")
base = None
for dr in (0.70, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95):
    rpd, mr, lapses = run(dr)
    tot = rpd.sum() / N
    late = rpd[61:].sum() / N
    if dr == 0.90:
        base = (tot, late)
    print(f"{dr:.2f}  {tot:6.2f}               {late:6.2f}                     {mr[1:].mean():.3f}                    {mr[-1]:.3f}              {lapses/N:.2f}")

print()
print("ratio to 0.90 (total reviews in 120 days / reviews in days 61-120):")
for dr in (0.70, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95):
    rpd, mr, lapses = run(dr)
    print(f"{dr:.2f}: {rpd.sum()/N/base[0]:.2f}x / {rpd[61:].sum()/N/base[1]:.2f}x")

# Interval multipliers from the FSRS-6 default curve
w20 = 0.1542
F = 0.9 ** (-1 / w20) - 1
def interval(r, s):
    return s / F * (r ** (-1 / w20) - 1)
print()
print("interval(r)/interval(0.90) at S=10:")
for r in (0.70, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.97):
    print(f"  r={r:.2f}: {interval(r,10)/interval(0.90,10):.3f}  (I={interval(r,10):.2f} d)")
