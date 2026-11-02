"""Study days for the engine, on top of the storage clock (DST-safe, 4 AM rollover)."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, timedelta, tzinfo
from typing import Any

from core.storage import clock

# Projections need a moment inside a future study day. Reviews are assumed to happen this
# long after the day starts (noon with the default 4 AM rollover).
REVIEW_OFFSET_MS = 8 * 3_600_000


@dataclass(frozen=True, slots=True)
class StudyDays:
    tz: tzinfo
    rollover_hour: int = clock.DEFAULT_ROLLOVER_HOUR
    # ENG-23: study days stored when past answers were graded, by their time; a later
    # time-zone, DST or rollover change never moves them.
    pinned: Mapping[int, date] = field(default_factory=dict, compare=False, hash=False)

    def day_of(self, at_ms: int) -> date:
        day = self.pinned.get(at_ms)
        return day if day is not None else clock.study_day(at_ms, self.tz, self.rollover_hour)

    def pin(self, attempts: Iterable[Any]) -> StudyDays:
        """These days with the stored study day of each graded attempt pinned (ENG-23)."""
        return replace(self, pinned={**self.pinned, **stored_days(attempts)})

    def start(self, day: date) -> int:
        return clock.day_start_ms(day, self.tz, self.rollover_hour)

    def bounds(self, day: date) -> tuple[int, int]:
        return clock.day_bounds_ms(day, self.tz, self.rollover_hour)

    def moment(self, day: date) -> int:
        """A typical review time on that study day (for projections and booster previews)."""
        start, end = self.bounds(day)
        return min(start + REVIEW_OFFSET_MS, end - 1)

    def add(self, day: date, days: int) -> date:
        return day + timedelta(days=days)

    def between(self, earlier_ms: int, later_ms: int) -> int:
        """Whole study days from one instant's day to another's."""
        return (self.day_of(later_ms) - self.day_of(earlier_ms)).days


def stored_days(attempts: Iterable[Any]) -> dict[int, date]:
    """time -> study day stored at grading (ENG-23), for attempts that carry one."""
    out: dict[int, date] = {}
    for a in attempts:
        raw = getattr(a, "study_day", None)
        if raw and getattr(a, "voided_by", None) is None:
            out[int(a.at)] = date.fromisoformat(str(raw))
    return out
