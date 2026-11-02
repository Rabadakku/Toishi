"""TIME-4/5/6 active-time accounting and ENG-13 target times."""

import pytest

from core.engine.config import DAY_MS
from core.engine.timing import (
    TimingFacts,
    baseline_samples,
    cap_ms,
    computed_target_ms,
    exam_pace_ms,
    exam_problem_ms,
    excluded_from_baseline,
    log_median,
    next_target,
    speed_time_ms,
    tier_update,
    typing_allowance_ms,
)
from core.model import Attempt, Exam, SkillTierState


def test_typing_allowance_and_speed_time():
    assert typing_allowance_ms(0) == 5_000
    assert typing_allowance_ms(10) == 8_000
    # Speed = solve time + allowance, never the actual typing time.
    assert speed_time_ms(40_000, 10, target_ms=None, tier=2) == 48_000
    assert speed_time_ms(None, 10, target_ms=None, tier=2) is None


def test_cap_is_four_targets_within_three_to_thirty_minutes():
    assert cap_ms(60_000, 3) == 240_000
    assert cap_ms(20_000, 1) == 180_000  # at least 3 minutes
    assert cap_ms(900_000, 5) == 1_800_000  # at most 30 minutes
    assert cap_ms(None, 4) == 360_000  # floor (90 s) before a target exists
    assert speed_time_ms(10_000_000, 0, target_ms=60_000, tier=3) == 240_000


@pytest.mark.parametrize(
    ("timing", "untimed", "hints", "example", "excluded"),
    [
        (TimingFacts(solve_ms=1_000), False, 0, False, False),
        (TimingFacts(solve_ms=1_000), True, 0, False, True),
        (TimingFacts(solve_ms=1_000, longest_pause_ms=120_001), False, 0, False, True),
        (TimingFacts(solve_ms=1_000, longest_pause_ms=120_000), False, 0, False, False),
        (TimingFacts(solve_ms=1_000, after_wake=True), False, 0, False, True),
        (TimingFacts(solve_ms=1_000), False, 1, False, True),
        (TimingFacts(solve_ms=1_000), False, 0, True, True),
        (TimingFacts(solve_ms=None), False, 0, False, True),
    ],
)
def test_baseline_exclusions(timing, untimed, hints, example, excluded):
    assert (
        excluded_from_baseline(timing, untimed=untimed, hints_used=hints, example_opened=example)
        == excluded
    )


def test_log_median_resists_one_long_problem():
    assert log_median([10, 1000]) == pytest.approx(100)
    assert log_median([30, 30, 30, 30, 10_000]) == pytest.approx(30)
    assert log_median([]) is None


def attempt(i: int, ms: int, **kw: object) -> Attempt:
    base: dict[str, object] = {
        "id": i,
        "at": i * DAY_MS,
        "card_id": f"c{i}",
        "tier": 2,
        "verdict": "correct",
        "extra": {"speed_ms": ms, "baseline_ok": True},
    }
    base.update(kw)
    return Attempt(**base)  # type: ignore[arg-type]


def test_baseline_samples_filter_and_window():
    history = [attempt(i, 1_000 * i) for i in range(1, 30)]
    history.append(attempt(40, 99, tier=3))
    history.append(attempt(41, 99, verdict="incorrect"))
    history.append(attempt(42, 99, extra={"speed_ms": 99, "baseline_ok": False}))
    history.append(attempt(43, 99, voided_by=1))
    samples = baseline_samples(history, 2, learned_at=5 * DAY_MS)
    assert samples == [1_000 * i for i in range(10, 30)]  # last 20, after Learned


def test_exam_pace():
    exam = Exam(name="Midterm", at=0, minutes=50, problems=10)
    assert exam_problem_ms(exam) == 255_000  # 85% of 50 minutes over 10 problems
    assert exam_problem_ms(Exam(name="x", at=0)) is None
    assert exam_pace_ms(1, 255_000) == 63_750
    assert exam_pace_ms(2, 255_000) == 102_000
    assert exam_pace_ms(3, 255_000) == 127_500
    assert exam_pace_ms(4, 255_000) == 204_000


def test_target_is_max_of_floor_and_min_of_pace_and_early_median():
    early = (100_000, 110_000, 90_000, 120_000, 100_000)
    # 0.7 x median(100k) = 70k; pace tier 2 = 102k -> 70k
    assert computed_target_ms(2, early, 255_000) == 70_000
    # Without an exam the early median decides.
    assert computed_target_ms(2, early, None) == 70_000
    # Floors: tier 2 is 40 s.
    assert computed_target_ms(2, (20_000,) * 5, None) == 40_000
    # Fewer than five correct answers and no exam: no target yet.
    assert computed_target_ms(2, early[:4], None) is None
    # Exam pace alone.
    assert computed_target_ms(3, (), 255_000) == 127_500


def test_target_tightens_at_most_ten_percent_a_week():
    prev = SkillTierState(skill_id="s", tier=2, target_ms=100_000, target_at=0)
    # Tighter within a week: unchanged.
    assert next_target(prev, 50_000, 6 * DAY_MS) == (100_000, 0)
    # After a week: at most 10% tighter.
    assert next_target(prev, 50_000, 7 * DAY_MS) == (90_000, 7 * DAY_MS)
    assert next_target(prev, 95_000, 8 * DAY_MS) == (95_000, 8 * DAY_MS)
    # Looser: immediate.
    assert next_target(prev, 120_000, DAY_MS) == (120_000, DAY_MS)
    # Same: keeps its date.
    assert next_target(prev, 100_000, 30 * DAY_MS) == (100_000, 0)
    assert next_target(None, 70_000, 5) == (70_000, 5)
    assert next_target(prev, None, 5) == (100_000, 0)


def test_tier_update_collects_first_five_and_baseline():
    row = None
    for i in range(7):
        row = tier_update(
            row,
            skill_id="s",
            tier=2,
            history=[],
            learned_at=0,
            new_success_ms=50_000 + i,
            exam_problem=None,
            now_ms=i * DAY_MS,
        )
    assert row is not None
    assert row.first_correct_ms == tuple(50_000 + i for i in range(5))
    assert row.target_ms == 40_000  # max(floor 40 s, 0.7 x 50 s = 35 s)
    assert row.baseline_n == 1  # history is the caller's; only this answer here
