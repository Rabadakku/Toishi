"""Speed: active-time accounting (TIME-4..6), log-time baselines, target times (ENG-13).

The speed time every rule uses is solve time plus a typing allowance (5 s + 0.3 s per
character of the expected answer), capped at four times the target (3..30 minutes). It is
stored on the attempt as extra["speed_ms"], beside the raw and capped active times.
"""

import math
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from core.engine.config import (
    BASELINE_LONG_PAUSE_MS,
    BASELINE_WINDOW,
    CAP_MAX_MS,
    CAP_MIN_MS,
    CAP_TARGET_MULTIPLE,
    DAY_MS,
    EARLY_CORRECT_COUNT,
    EARLY_MEDIAN_SHARE,
    EXAM_TIME_USABLE,
    TARGET_TIGHTEN_PER_WEEK,
    TIER_EXAM_SHARE,
    TIER_FLOOR_MS,
    TYPING_BASE_MS,
    TYPING_PER_CHAR_MS,
)
from core.model import Attempt, Exam, SkillTierState


def typing_allowance_ms(expected_chars: int) -> int:
    return TYPING_BASE_MS + TYPING_PER_CHAR_MS * max(0, expected_chars)


def cap_ms(target_ms: int | None, tier: int) -> int:
    """TIME-5: four times the target (the tier floor before a target exists), 3..30 min."""
    base = target_ms if target_ms is not None else TIER_FLOOR_MS[tier]
    return min(max(CAP_TARGET_MULTIPLE * base, CAP_MIN_MS), CAP_MAX_MS)


def speed_time_ms(
    solve_ms: int | None, expected_chars: int, *, target_ms: int | None, tier: int
) -> int | None:
    """TIME-4: solve time plus the typing allowance, capped (TIME-5)."""
    if solve_ms is None:
        return None
    return min(solve_ms + typing_allowance_ms(expected_chars), cap_ms(target_ms, tier))


@dataclass(frozen=True, slots=True, kw_only=True)
class TimingFacts:
    """What the study screen measured for one submission."""

    solve_ms: int | None = None
    entry_ms: int | None = None
    active_ms: int | None = None
    raw_ms: int | None = None
    pause_count: int = 0
    longest_pause_ms: int | None = None
    after_wake: bool = False
    expected_chars: int = 0


def excluded_from_baseline(
    timing: TimingFacts, *, untimed: bool, hints_used: int, example_opened: bool
) -> bool:
    """TIME-5/6: untimed sessions, a pause over 2 minutes, the first attempt after the Mac
    wakes, and attempts with a hint or worked example opened stay out of speed baselines."""
    return (
        untimed
        or timing.solve_ms is None
        or (timing.longest_pause_ms or 0) > BASELINE_LONG_PAUSE_MS
        or timing.after_wake
        or hints_used > 0
        or example_opened
    )


def log_median(values: Iterable[float]) -> float | None:
    """Median of log times, back in ms (one long problem can't skew it)."""
    logs = [math.log(v) for v in values if v > 0]
    if not logs:
        return None
    return math.exp(statistics.median(logs))


def baseline_samples(history: Sequence[Attempt], tier: int, learned_at: int | None) -> list[int]:
    """Speed times of eligible successes at a tier after Learned, oldest first (last 20)."""
    out = [
        int(a.extra["speed_ms"])
        for a in history
        if a.tier == tier
        and a.final
        and a.verdict == "correct"
        and a.voided_by is None
        and a.extra.get("baseline_ok") is True
        and "speed_ms" in a.extra
        and (learned_at is None or a.at >= learned_at)
    ]
    return out[-BASELINE_WINDOW:]


def exam_problem_ms(exam: Exam | None) -> int | None:
    """85% of the exam's minutes spread over its problems."""
    if exam is None or not exam.minutes or not exam.problems:
        return None
    return round(exam.minutes * 60_000 * EXAM_TIME_USABLE / exam.problems)


def exam_pace_ms(tier: int, exam_problem: int | None) -> int | None:
    if exam_problem is None:
        return None
    return round(exam_problem * TIER_EXAM_SHARE[tier])


def computed_target_ms(
    tier: int, first_correct_ms: Sequence[int], exam_problem: int | None
) -> int | None:
    """ENG-13: max(floor, min(exam pace, 70% of the median of the first five correct
    answers after Learned)). None until either number exists."""
    candidates: list[float] = []
    pace = exam_pace_ms(tier, exam_problem)
    if pace is not None:
        candidates.append(pace)
    if len(first_correct_ms) >= EARLY_CORRECT_COUNT:
        early = log_median(first_correct_ms[:EARLY_CORRECT_COUNT])
        if early is not None:
            candidates.append(EARLY_MEDIAN_SHARE * early)
    if not candidates:
        return None
    return max(TIER_FLOOR_MS[tier], round(min(candidates)))


def next_target(
    previous: SkillTierState | None, computed: int | None, now_ms: int
) -> tuple[int | None, int | None]:
    """(target_ms, target_at) after limiting tightening to 10% a week. Loosening is
    immediate. A tighter target waits until a week has passed since the last change."""
    prev = previous.target_ms if previous is not None else None
    prev_at = previous.target_at if previous is not None else None
    if computed is None:
        return prev, prev_at
    if prev is None or computed >= prev:
        return computed, now_ms if computed != prev else prev_at
    if prev_at is not None and now_ms - prev_at < 7 * DAY_MS:
        return prev, prev_at
    return max(computed, round(prev * (1.0 - TARGET_TIGHTEN_PER_WEEK))), now_ms


def tier_update(
    previous: SkillTierState | None,
    *,
    skill_id: str,
    tier: int,
    history: Sequence[Attempt],
    learned_at: int | None,
    new_success_ms: int | None,
    exam_problem: int | None,
    now_ms: int,
) -> SkillTierState:
    """The skill/tier row after one graded answer: baseline over eligible successes
    (history plus this one), the first five correct times after Learned, the target."""
    samples = baseline_samples(history, tier, learned_at)
    first = tuple(previous.first_correct_ms) if previous is not None else ()
    if new_success_ms is not None:
        samples = [*samples, new_success_ms][-BASELINE_WINDOW:]
        if len(first) < EARLY_CORRECT_COUNT:
            first = (*first, new_success_ms)
    median = log_median(samples)
    target, target_at = next_target(previous, computed_target_ms(tier, first, exam_problem), now_ms)
    return SkillTierState(
        skill_id=skill_id,
        tier=tier,
        target_ms=target,
        target_at=target_at,
        baseline_median_ms=None if median is None else round(median),
        baseline_n=len(samples),
        first_correct_ms=first,
    )
