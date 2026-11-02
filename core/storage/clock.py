"""Time: UTC epoch milliseconds, an injectable clock, and the study day (ENG-1).

Everything stored is UTC epoch milliseconds. The study day is a local calendar date that
rolls over at a local wall-clock hour (default 4 AM), so it follows DST correctly: a
study day is 23 or 25 hours long across a change, and the rollover never moves.
"""

import os
import time
from datetime import UTC, date, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_ROLLOVER_HOUR = 4
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MS = timedelta(milliseconds=1)


class Clock(Protocol):
    """What storage asks for the time. Tests inject a FixedClock."""

    def now_ms(self) -> int: ...

    @property
    def tz(self) -> tzinfo: ...


def zone(name: str | tzinfo) -> tzinfo:
    return ZoneInfo(name) if isinstance(name, str) else name


def local_zone() -> tzinfo:
    """The Mac's IANA time zone (TZ, then /etc/localtime), so DST rules are known.

    Falls back to the current fixed offset only when no zone name can be found.
    """
    candidates: list[str] = []
    env = os.environ.get("TZ", "").lstrip(":")
    if env:
        candidates.append(env)
    try:
        target = str(Path("/etc/localtime").readlink())
    except OSError:
        target = ""
    if "zoneinfo/" in target:
        candidates.append(target.split("zoneinfo/", 1)[1])
    for name in candidates:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError, ValueError:
            continue
    fallback = datetime.now().astimezone().tzinfo
    return fallback if fallback is not None else UTC


class SystemClock:
    def __init__(self, tz: str | tzinfo | None = None) -> None:
        self._tz = zone(tz) if tz is not None else local_zone()

    def now_ms(self) -> int:
        return time.time_ns() // 1_000_000

    @property
    def tz(self) -> tzinfo:
        return self._tz


class FixedClock:
    """A clock that only moves when told to."""

    def __init__(self, at: int | datetime, tz: str | tzinfo = "UTC") -> None:
        self._now = at if isinstance(at, int) else to_ms(at)
        self._tz = zone(tz)

    def now_ms(self) -> int:
        return self._now

    @property
    def tz(self) -> tzinfo:
        return self._tz

    def set(self, at: int | datetime) -> None:
        self._now = at if isinstance(at, int) else to_ms(at)

    def advance(
        self,
        ms: int = 0,
        *,
        seconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        days: float = 0,
    ) -> int:
        delta = timedelta(milliseconds=ms, seconds=seconds, minutes=minutes, hours=hours, days=days)
        self._now += delta // _MS
        return self._now


def to_ms(moment: datetime) -> int:
    if moment.tzinfo is None:
        raise ValueError("naive datetime: give a time zone")
    return (moment - _EPOCH) // _MS


def from_ms(at_ms: int, tz: tzinfo = UTC) -> datetime:
    return (_EPOCH + timedelta(milliseconds=at_ms)).astimezone(tz)


def study_day(at_ms: int, tz: tzinfo, rollover_hour: int = DEFAULT_ROLLOVER_HOUR) -> date:
    """The study day containing the instant: local date, minus one before the rollover hour."""
    _check_hour(rollover_hour)
    local = from_ms(at_ms, tz)
    return local.date() - timedelta(days=1) if local.hour < rollover_hour else local.date()


def study_day_iso(at_ms: int, tz: tzinfo, rollover_hour: int = DEFAULT_ROLLOVER_HOUR) -> str:
    return study_day(at_ms, tz, rollover_hour).isoformat()


def day_start_ms(day: date, tz: tzinfo, rollover_hour: int = DEFAULT_ROLLOVER_HOUR) -> int:
    """The first instant of a study day: rollover_hour:00 local time on that date.

    In a DST gap (the hour does not exist) it is the moment the clocks jump; when the
    hour happens twice it is the first occurrence.
    """
    _check_hour(rollover_hour)
    naive = datetime(day.year, day.month, day.day, rollover_hour)
    first = naive.replace(tzinfo=tz, fold=0)
    candidate = to_ms(first)
    if from_ms(candidate, tz).replace(tzinfo=None) != naive:
        # Nonexistent wall time: fold=0 maps it with the offset from before the jump,
        # which lands later than the jump. The day starts at the jump itself.
        candidate = _transition_before(candidate, tz)
    return candidate


def day_bounds_ms(
    day: date, tz: tzinfo, rollover_hour: int = DEFAULT_ROLLOVER_HOUR
) -> tuple[int, int]:
    """[start, end) of a study day in UTC ms."""
    return (
        day_start_ms(day, tz, rollover_hour),
        day_start_ms(day + timedelta(days=1), tz, rollover_hour),
    )


def _transition_before(at_ms: int, tz: tzinfo) -> int:
    """The offset-change instant within the 3 hours before at_ms (binary search, to 1 ms)."""
    lo, hi = at_ms - 3 * 3_600_000, at_ms
    offset_hi = from_ms(hi, tz).utcoffset()
    if from_ms(lo, tz).utcoffset() == offset_hi:
        return at_ms
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if from_ms(mid, tz).utcoffset() == offset_hi:
            hi = mid
        else:
            lo = mid
    return hi


def _check_hour(hour: int) -> None:
    if not 0 <= hour <= 23:
        raise ValueError(f"rollover hour must be 0..23, got {hour}")


def zone_name(tz: tzinfo) -> str:
    return str(getattr(tz, "key", None) or tz.tzname(None) or "UTC")
