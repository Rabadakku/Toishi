"""I10: simulation properties of the whole scheduling loop (tests/engine/sim.py)."""

import itertools
from datetime import date, timedelta

import pytest

from core.engine.config import EngineSettings
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.lifecycle import due_day
from tests.engine.helpers import DAYS
from tests.engine.sim import Student, World

START = date(2026, 9, 1)
MAX_DAYS = 60


def run(retention: float, seed: int) -> World:
    world = World(
        Student("steady"),
        [f"sim.k{i:02d}" for i in range(40)],
        start=START,
        days=DAYS,
        seed=seed,
        retention=retention,
        settings=EngineSettings(daily_problems=200, maximum_interval_days=MAX_DAYS),
    )
    world.fsrs = FsrsAdapter(maximum_interval_days=MAX_DAYS)
    world.run(90)
    return world


@pytest.fixture(scope="module")
def worlds() -> dict[float, list[World]]:
    return {r: [run(r, seed) for seed in (1, 2)] for r in (0.80, 0.85, 0.90, 0.95)}


def test_I10_workload_rises_steadily_and_ever_faster_with_desired_retention(worlds):
    load = [sum(sum(w.log.rated_per_day.values()) for w in worlds[r]) for r in sorted(worlds)]
    steps = [b - a for a, b in itertools.pairwise(load)]
    assert all(s > 0 for s in steps), load
    assert steps == sorted(steps), load  # each 0.05 of retention costs more than the last


def test_I10_due_review_success_is_about_the_desired_retention(worlds):
    for retention, runs in worlds.items():
        outcomes = [r > 1 for w in runs for _, _, r, _, _ in w.log.reviews]
        assert len(outcomes) > 300
        assert sum(outcomes) / len(outcomes) == pytest.approx(retention, abs=0.04)


def test_I10_no_due_date_in_the_past_and_no_interval_above_the_maximum(worlds):
    for runs in worlds.values():
        for world in runs:
            assert all(1 <= interval <= MAX_DAYS for _, _, interval in world.log.intervals)
            end = START + timedelta(days=90)
            for state in world.states.values():
                due = due_day(state, world.retention, world.fsrs, DAYS)
                if due is None or state.last_review_at is None:
                    continue
                last = DAYS.day_of(state.last_review_at)
                assert last < due <= last + timedelta(days=MAX_DAYS)
                assert last <= end
