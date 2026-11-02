"""Simulated students with known forgetting and speed curves (see tests/engine/sim.py)."""

import itertools
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta

import pytest

from core.engine import BoostTarget, calibrate
from core.engine.config import AGAIN
from core.engine.level import rank
from core.engine.lifecycle import memory_of
from tests.engine.helpers import DAYS, some
from tests.engine.sim import Student, World

START = date(2026, 9, 1)
STEADY = Student("steady")
FORGETFUL = Student("forgetful", scale=0.25)  # true recall at 0.90 predicted: ~0.78
STRONG = Student(
    "strong",
    learn_p=(0.9, 0.95, 0.97),
    base_ms={1: 20_000, 2: 35_000, 3: 55_000, 4: 85_000, 5: 120_000},
    speedup=0.3,
)


def skills(n: int) -> list[str]:
    return [f"sim.k{i:02d}" for i in range(n)]


@pytest.fixture(scope="module")
def steady_runs() -> list[World]:
    runs = []
    for seed in (1, 2, 3):
        world = World(STEADY, skills(60), start=START, days=DAYS, seed=seed)
        world.run(60)
        runs.append(world)
    return runs


def test_intervals_are_sensible(steady_runs):
    ratios: list[float] = []
    for world in steady_runs:
        # A clean learning phase gives two days; a lapse is relearned the next study day.
        assert world.log.clean_learning_intervals
        assert set(world.log.clean_learning_intervals) == {2}
        # After a failed phase the whole learning block is replayed (C3/C6): 1 or 2 days.
        for interval, replayed in world.log.clean_after_failed_intervals:
            assert interval == replayed
            assert interval in (1, 2)
        assert set(world.log.relearn_intervals) == {1}
        by_skill: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for skill, streak, interval in world.log.intervals:
            assert 1 <= interval <= 365
            by_skill[skill].append((streak, interval))
        for seq in by_skill.values():
            for (s1, a), (s2, b) in itertools.pairwise(seq):
                if s2 == s1 + 1:
                    ratios.append(b / a)
    # Each success in a row spaces the next review further out (fuzz aside).
    assert len(ratios) > 500
    assert statistics.median(ratios) >= 1.8
    assert sum(r < 1 for r in ratios) <= 0.01 * len(ratios)
    assert min(ratios) >= 0.7


def test_predicted_recall_is_calibrated_against_the_truth(steady_runs):
    pairs = [
        (p, r > AGAIN) for w in steady_runs for _, _, r, p, _ in w.log.reviews if p is not None
    ]
    report = calibrate(pairs)
    assert report.total > 800
    # The truth equals the prediction review by review here, so what is left is sampling
    # noise: every bin of 30+ is within three standard errors. (ENG-11's fixed 0.10 notice
    # is noisier: one standard error of a 30-review bin at p = 0.65 is 0.087.)
    for b in report.bins:
        if b.n >= 30:
            assert abs(b.error) <= 3 * math.sqrt(b.predicted * (1 - b.predicted) / b.n), b
    assert abs(report.mean_error) < 0.03
    predicted = statistics.mean(p for p, _ in pairs)
    truth = statistics.mean(t for w in steady_runs for *_, t in w.log.reviews)
    assert predicted == pytest.approx(truth, abs=0.01)


def test_a_student_who_forgets_faster_raises_the_calibration_notice():
    world = World(FORGETFUL, skills(60), start=START, days=DAYS, seed=4)
    world.run(60)
    report = calibrate([(p, r > AGAIN) for _, _, r, p, _ in world.log.reviews if p is not None])
    assert report.notice
    assert report.mean_error < -0.08


def test_a_month_stays_within_a_sane_budget(steady_runs):
    for world in steady_runs:
        month = [START + timedelta(days=i) for i in range(30)]
        problems = [world.log.per_day.get(d, 0) for d in month]
        rated = [world.log.rated_per_day.get(d, 0) for d in month]
        assert max(rated) <= 20  # the daily count
        assert max(problems) <= 26  # plus same-day reinforcement and stretch follow-ups
        assert statistics.mean(problems) <= 20
        assert len(world.log.learned_at) == 60  # yet everything gets introduced


def exam_run(seed: int, *, boosters: bool) -> tuple[list[float], list[float], World]:
    names = skills(30)
    exam_day = START + timedelta(days=50)
    exam_at = DAYS.start(exam_day) + 5 * 3_600_000  # 9 AM
    target = BoostTarget(
        key="exam:1", name="Final", day=exam_day, at_ms=exam_at, target=0.95, skill_ids=tuple(names)
    )
    world = World(
        STEADY, names, start=START, days=DAYS, seed=seed, targets=[target], boosters=boosters
    )
    world.run(50)
    truth = [world.true_recall(k, exam_at) for k in names]
    predicted = [
        world.fsrs.retrievability(some(memory_of(world.states[k])), exam_at) for k in names
    ]
    return truth, predicted, world


def test_boosters_reach_the_exam_day_target():
    boosted_truth, unboosted_truth = [], []
    for seed in (1, 2, 3):
        truth, predicted, world = exam_run(seed, boosters=True)
        boosted_truth += truth
        assert world.log.boosters_done > 10
        assert sum(p >= 0.95 for p in predicted) >= 0.9 * len(predicted)
        assert max(world.log.per_day.values()) <= 26
        plain, _, _ = exam_run(seed, boosters=False)
        unboosted_truth += plain
    # Seeds 1-3: 86/90 skills truly at 0.95 on exam day with boosters, 50/90 without.
    at_target = sum(r >= 0.95 for r in boosted_truth)
    assert at_target >= 0.9 * len(boosted_truth)
    assert at_target >= sum(r >= 0.95 for r in unboosted_truth) + 0.2 * len(boosted_truth)
    assert statistics.mean(boosted_truth) >= 0.955


LEGAL = {
    ("learning", "learned"),
    ("learned", "exam"),
    ("learned", "mastered"),  # both rules met by one answer
    ("exam", "mastered"),
    ("mastered", "exam"),
    ("exam", "learned"),
    ("learned", "learning"),
    ("exam", "learning"),  # a leech repair or provisional reset restarts the phase
    ("mastered", "learning"),
}


def test_level_rises_and_falls_as_specified():
    world = World(STRONG, skills(12), start=START, days=DAYS, seed=3)
    world.run(150)
    levels = [s.level for s in world.states.values()]
    assert levels.count("mastered") >= 2
    assert levels.count("exam") + levels.count("mastered") >= 4
    assert {(a, b) for _, _, a, b in world.log.level_changes} <= LEGAL
    strong = {k for k, s in world.states.items() if rank(s.level) >= rank("exam")}
    before = {k: world.states[k].level for k in strong}
    reviews_before = {k: len(world.history[k]) for k in strong}
    world.start = START + timedelta(days=150)
    world.run(120, force_wrong=frozenset(strong))
    served = [k for k in strong if len(world.history[k]) - reviews_before[k] >= 2]
    assert served
    for k in served:
        assert rank(world.states[k].level) < rank(before[k]), k
    assert world.log.demotions >= len(served)
    assert {(a, b) for _, _, a, b in world.log.level_changes} <= LEGAL
