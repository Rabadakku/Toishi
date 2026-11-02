"""Triage of overdue skills under a daily cap (QUE-6), FSRS-6 default parameters, self-consistent learner.
300 skills learned on random days 0-59, DR 0.90, then (A) a 15-day break (days 80-94) followed by a daily cap C,
or (B) a persistent cap from day 60. Policies choose which due skills to review each day.
Metrics: mean recall R over all skill-days after the break, lapses (failed reviews) per skill, reviews per skill."""
import random, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler
T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
W20 = 0.1542
F = 0.9 ** (-1 / W20) - 1
N = 300
def retr(c, now):
    return (1 + F * ((now - c.last_review).total_seconds() / 86400.0) / c.stability) ** (-W20)
def pol_key(policy, c, now, rnd):
    r = retr(c, now)
    if policy == "highest R first (spec QUE-6)": return -r
    if policy == "lowest R first (most forgotten)": return r
    if policy == "oldest due first": return (c.due - now).total_seconds()
    if policy == "spec QUE-6 + QUE-4 (7-day rule)":
        overdue_days = (now - c.due).total_seconds() / 86400.0
        return (0, (c.due - now).total_seconds()) if overdue_days > 7 else (1, -r)
    if policy == "largest 1-day loss in R": return -(r - retr(c, now + timedelta(days=1)))
    return rnd.random()
POLICIES = ["spec QUE-6 + QUE-4 (7-day rule)", "highest R first (spec QUE-6)", "lowest R first (most forgotten)", "oldest due first", "largest 1-day loss in R", "random"]
def run(policy, seed, scenario, cap):
    rnd = random.Random(seed)
    sch = Scheduler(desired_retention=0.90, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    learn_day = [rnd.randrange(0, 60) for _ in range(N)]
    cards = [None] * N
    start = 95 if scenario == "A" else 60
    end = 95 + 90 if scenario == "A" else 60 + 120
    rsum = 0.0; rcount = 0; lapses = 0; revs = 0
    for d in range(end):
        now = T0 + timedelta(days=d)
        for i in range(N):
            if learn_day[i] == d:
                cards[i], _ = sch.review_card(Card(), Rating.Good, now)
        if scenario == "A" and 80 <= d < 95:
            pass
        else:
            due = [i for i in range(N) if cards[i] is not None and learn_day[i] < d and cards[i].due <= now]
            if d < start:
                chosen = due
            else:
                due.sort(key=lambda i: pol_key(policy, cards[i], now, rnd))
                chosen = due[:cap]
            for i in chosen:
                c = cards[i]
                r = retr(c, now)
                ok = rnd.random() < r
                cards[i], _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
                if d >= start:
                    revs += 1
                    if not ok: lapses += 1
        if d >= start:
            for i in range(N):
                if cards[i] is not None and learn_day[i] <= d:
                    rsum += retr(cards[i], now); rcount += 1
    return rsum / rcount, lapses / N, revs / N
for scenario, cap in (("A", 4), ("A", 6), ("B", 2), ("B", 3)):
    label = {"A": "return from 15-day break", "B": "persistent cap from day 60"}[scenario]
    print(f"\nScenario {scenario}: {label}; cap {cap}/day for {N} skills (steady-state demand about 3.5/day)")
    print("policy | mean R over all skill-days | lapses per skill | reviews per skill")
    for pol in POLICIES:
        rows = [run(pol, s, scenario, cap) for s in range(12)]
        m = [sum(x[k] for x in rows) / len(rows) for k in range(3)]
        print(f"{pol:34s} | {m[0]:.3f} | {m[1]:.2f} | {m[2]:.2f}")
