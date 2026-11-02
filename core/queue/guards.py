"""Server-side timing guards (TIME-4, TIME-5): the UI measures, the core checks.

The page reports active, solve and entry times; nothing it sends is trusted as is. Times
are made non-negative and bounded by the wall clock since the problem was shown; solve and
entry time must fit inside active time. An inconsistent report keeps its (bounded) active
time for the log but loses its solve time, which leaves it out of speed baselines (the
engine excludes attempts without a solve time). The engine then stores raw and capped
times (four times the target, 3..30 minutes) and applies the other TIME-5 exclusions:
a pause over 2 minutes, the first attempt after the Mac wakes, a hint or worked example.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.engine import TimingFacts
from core.queue.config import CLOCK_SLACK_MS, MAX_REPORTED_MS


@dataclass(frozen=True, slots=True, kw_only=True)
class TimingReport:
    """What the study screen measured for one submission (all ms)."""

    active_ms: int | None = None
    solve_ms: int | None = None  # problem shown -> first keystroke in the answer box
    entry_ms: int | None = None  # first keystroke -> submit
    paused_ms: int | None = None
    pause_count: int = 0
    longest_pause_ms: int | None = None
    after_wake: bool = False
    idle_trimmed: bool = False  # TIME-3 "Still working?" trimmed the clock

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> TimingReport:
        if not data:
            return cls()

        def num(key: str) -> int | None:
            value = data.get(key)
            if isinstance(value, bool) or not isinstance(value, int | float):
                return None
            return int(value)

        return cls(
            active_ms=num("active_ms"),
            solve_ms=num("solve_ms"),
            entry_ms=num("entry_ms"),
            paused_ms=num("paused_ms"),
            pause_count=num("pause_count") or 0,
            longest_pause_ms=num("longest_pause_ms"),
            after_wake=bool(data.get("after_wake", False)),
            idle_trimmed=bool(data.get("idle_trimmed", False)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Guarded:
    timing: TimingFacts
    flags: tuple[str, ...] = ()  # what was corrected (logged in the attempt's extra)


def _bound(value: int | None, high: int) -> int | None:
    if value is None:
        return None
    return min(max(0, value), high)


def guard_timing(
    report: TimingReport,
    *,
    shown_at: int | None,
    now_ms: int,
    saved_active_ms: int = 0,
    expected_chars: int = 0,
) -> Guarded:
    """Validate and bound a timing report. `saved_active_ms`: the active time the session
    already saved for this problem (QUE-16), which a resumed page may not have counted."""
    flags: list[str] = []
    wall = MAX_REPORTED_MS
    if shown_at is not None:
        wall = min(wall, max(0, now_ms - shown_at) + CLOCK_SLACK_MS)
    active = report.active_ms
    if active is None:
        flags.append("no active time")
        active = saved_active_ms or None
    else:
        if active < 0:
            flags.append("negative active time")
        if saved_active_ms > active:
            active = saved_active_ms
        if active > wall:
            flags.append("active time over wall clock")
    active = _bound(active, wall)
    solve = _bound(report.solve_ms, wall)
    entry = _bound(report.entry_ms, wall)
    consistent = solve is not None and active is not None
    if solve is not None and active is not None and solve > active + CLOCK_SLACK_MS:
        flags.append("solve time over active time")
        consistent = False
    if (
        solve is not None
        and entry is not None
        and active is not None
        and solve + entry > active + CLOCK_SLACK_MS
    ):
        flags.append("solve and entry time over active time")
        consistent = False
    if report.solve_ms is not None and report.solve_ms < 0:
        consistent = False
    longest = _bound(report.longest_pause_ms, wall)
    timing = TimingFacts(
        solve_ms=solve if consistent else None,
        entry_ms=entry,
        active_ms=active,
        raw_ms=active,
        pause_count=max(0, report.pause_count),
        longest_pause_ms=longest,
        after_wake=report.after_wake,
        expected_chars=max(0, expected_chars),
    )
    return Guarded(timing=timing, flags=tuple(flags))
