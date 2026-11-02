"""Boosters vs higher desired retention all along; FSRS-6 default parameters; self-consistent learner.
Two course lengths: exam on day 120 (one semester) and day 200 (mature course). 300 skills, learned on random days 0-89
(or 0-59 for exam 120 so that most skills have >= 60 days), 30 seeds."""
import random, sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler
T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
W20 = 0.1542
F = 0.9 ** (-1 / W20) - 1
N = 300
WINDOW = 21
def retr(stab, t):
    return (1 + F * t / stab) ** (-W20)
def run(dr, target, boosters, seed, exam, learn_max, count_from):
    rnd = random.Random(seed)
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    learn_day = [rnd.randrange(0, learn_max) for _ in range(N)]
    cards = [None] * N
    rev = 0; rev_win = 0; boost = 0
    exam_dt = T0 + timedelta(days=exam)
    for d in range(exam + 1):
        now = T0 + timedelta(days=d)
        for i in range(N):
            if learn_day[i] == d:
                cards[i], _ = sch.review_card(Card(), Rating.Good, now)
        if d == exam:
            break
        for i in range(N):
            c = cards[i]
            if c is None or learn_day[i] >= d:
                continue
            r = retr(c.stability, (now - c.last_review).total_seconds() / 86400.0)
            do_review = c.due <= now
            is_boost = False
            if (not do_review) and boosters and d >= exam - WINDOW:
                r_exam = retr(c.stability, (exam_dt - c.last_review).total_seconds() / 86400.0)
                if c.due > exam_dt and r_exam < target:
                    pv, _ = sch.review_card(c, Rating.Good, now)
                    if retr(pv.stability, (exam_dt - now).total_seconds() / 86400.0) >= target:
                        do_review = True; is_boost = True
            if do_review:
                ok = rnd.random() < r
                cards[i], _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
                if d >= count_from: rev += 1
                if d >= exam - WINDOW:
                    rev_win += 1
                    if is_boost: boost += 1
    rex = [retr(c.stability, (exam_dt - c.last_review).total_seconds() / 86400.0) for c in cards if c is not None]
    n = len(rex)
    return rev / n, rev_win / n, boost / n, sum(rex) / n, sum(x >= 0.95 for x in rex) / n, sum(x >= 0.92 for x in rex) / n
configs = (("DR .80 (Keep), no boosters", 0.80, 0.95, False), ("DR .88, no boosters", 0.88, 0.92, False), ("DR .88 + boosters to .92 (goal B)", 0.88, 0.92, True),
           ("DR .90, no boosters", 0.90, 0.95, False), ("DR .90 + boosters to .95 (goal A)", 0.90, 0.95, True),
           ("DR .92 all along", 0.92, 0.95, False), ("DR .95 all along", 0.95, 0.95, False))
for exam, learn_max, count_from in ((120, 60, 60), (200, 90, 100)):
    print(f"\nExam on day {exam}; skills learned on days 0-{learn_max-1}; counting reviews from day {count_from}")
    print("config | reviews/skill from count_from to exam | reviews/skill in last 21 d | boosters/skill | mean R at exam | share R>=.95 | share R>=.92")
    for label, dr, tg, bo in configs:
        rows = [run(dr, tg, bo, sd, exam, learn_max, count_from) for sd in range(30)]
        m = [sum(x[k] for x in rows) / len(rows) for k in range(6)]
        print(f"{label:36s} | {m[0]:.2f} | {m[1]:.2f} | {m[2]:.2f} | {m[3]:.3f} | {m[4]:.3f} | {m[5]:.3f}")
