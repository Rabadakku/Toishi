"""Exam-booster workload (ENG-8) under FSRS-6 default parameters, self-consistent simulation.

150 skills learned on random days in 0-89 under base desired retention DR (steady-state schedule), exam on day EXAM,
booster window = last 21 days. Policy (spec ENG-8): for a skill not due before the exam whose predicted exam-day recall
without another review is below the target, review it on the first day from which a Good review keeps exam-day recall at
the target. Normal reviews continue as usual; success ~ Bernoulli(R); success -> Good, failure -> Again.
Compared with the same course without boosters. Reported per skill over the 21-day window.
"""
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/.venv/lib/python3.14/site-packages")
from fsrs import Card, Rating, Scheduler

T0 = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
W20 = 0.1542
F = 0.9 ** (-1 / W20) - 1
N = 150
EXAM = 200
WINDOW = 21


def retr(stab, t_days):
    return (1 + F * t_days / stab) ** (-W20)


def run(dr, target, boosters, seed):
    rnd = random.Random(seed)
    sch = Scheduler(desired_retention=dr, enable_fuzzing=False, learning_steps=(), relearning_steps=(), maximum_interval=365)
    learn_day = [rnd.randrange(0, 90) for _ in range(N)]
    cards = [None] * N
    reviews_window = 0
    boosters_done = 0
    for d in range(EXAM + 1):
        now = T0 + timedelta(days=d)
        for i in range(N):
            if learn_day[i] == d:
                c, _ = sch.review_card(Card(), Rating.Good, now)
                cards[i] = c
        if d == EXAM:
            break
        for i in range(N):
            c = cards[i]
            if c is None or learn_day[i] >= d:
                continue
            r = retr(c.stability, (now - c.last_review).total_seconds() / 86400.0)
            do_review = c.due <= now
            is_boost = False
            if (not do_review) and boosters and d >= EXAM - WINDOW:
                exam_dt = T0 + timedelta(days=EXAM)
                r_exam = retr(c.stability, (exam_dt - c.last_review).total_seconds() / 86400.0)
                if c.due > exam_dt and r_exam < target:
                    # feasible today? preview a Good review today
                    pv, _ = sch.review_card(c, Rating.Good, now)
                    r_exam_after = retr(pv.stability, (exam_dt - now).total_seconds() / 86400.0)
                    if r_exam_after >= target:
                        do_review = True
                        is_boost = True
            if do_review:
                ok = rnd.random() < r
                c2, _ = sch.review_card(c, Rating.Good if ok else Rating.Again, now)
                cards[i] = c2
                if d >= EXAM - WINDOW:
                    reviews_window += 1
                    boosters_done += 1 if is_boost else 0
    exam_dt = T0 + timedelta(days=EXAM)
    rex = [retr(c.stability, (exam_dt - c.last_review).total_seconds() / 86400.0) for c in cards]
    return reviews_window / N, boosters_done / N, sum(rex) / N, sum(1 for x in rex if x >= target) / N, sum(1 for x in rex if x >= 0.90) / N


print("base DR, target | boosters | reviews/skill in 21d window | of which boosters | mean R on exam day | share >= target | share >= 0.90")
for dr, target in ((0.90, 0.95), (0.88, 0.92), (0.80, 0.95), (0.80, 0.90)):
    for boosters in (False, True):
        rows = [run(dr, target, boosters, s) for s in range(8)]
        m = [sum(x[k] for x in rows) / len(rows) for k in range(5)]
        print(f"DR {dr:.2f}, target {target:.2f} | {str(boosters):5s} | {m[0]:.3f} | {m[1]:.3f} | {m[2]:.3f} | {m[3]:.3f} | {m[4]:.3f}")
