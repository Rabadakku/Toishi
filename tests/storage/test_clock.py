from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from core.storage.clock import (
    FixedClock,
    SystemClock,
    day_bounds_ms,
    day_start_ms,
    from_ms,
    study_day,
    to_ms,
)

NY = ZoneInfo("America/New_York")
HOUR = 3_600_000


def at(tz: ZoneInfo, y: int, mo: int, d: int, h: int, mi: int, *, fold: int = 0) -> int:
    return to_ms(datetime(y, mo, d, h, mi, tzinfo=tz, fold=fold))


def test_ms_round_trip_is_exact() -> None:
    for ms in (0, 1, 1_793_545_200_123, -1, 4_102_444_800_999):
        assert to_ms(from_ms(ms)) == ms
    with pytest.raises(ValueError, match="naive"):
        to_ms(datetime(2026, 1, 1))


def test_rollover_at_four_local() -> None:
    assert study_day(at(NY, 2026, 11, 10, 3, 59), NY) == date(2026, 11, 9)
    assert study_day(at(NY, 2026, 11, 10, 4, 0), NY) == date(2026, 11, 10)
    assert study_day(at(NY, 2026, 11, 10, 23, 59), NY) == date(2026, 11, 10)
    assert study_day(at(NY, 2026, 11, 10, 0, 30), NY, rollover_hour=0) == date(2026, 11, 10)
    with pytest.raises(ValueError, match="rollover hour"):
        study_day(0, NY, rollover_hour=24)


def test_spring_forward_day_is_23_hours() -> None:
    # 2026-03-08: 02:00 EST jumps to 03:00 EDT, inside study day 03-07 (it ends at 04:00)
    start, end = day_bounds_ms(date(2026, 3, 7), NY)
    assert end - start == 23 * HOUR
    assert day_bounds_ms(date(2026, 3, 8), NY)[1] - end == 24 * HOUR
    assert from_ms(start, NY).hour == 4
    assert from_ms(end, NY).hour == 4
    # 03:30 EDT that morning is still the previous study day; 04:00 starts the new one
    assert study_day(at(NY, 2026, 3, 8, 3, 30), NY) == date(2026, 3, 7)
    assert study_day(at(NY, 2026, 3, 8, 4, 0), NY) == date(2026, 3, 8)


def test_fall_back_day_is_25_hours_and_repeated_hour_stays_put() -> None:
    # 2026-11-01: 02:00 EDT falls back to 01:00 EST, inside study day 10-31
    start, end = day_bounds_ms(date(2026, 10, 31), NY)
    assert end - start == 25 * HOUR
    first = at(NY, 2026, 11, 1, 1, 30, fold=0)
    second = at(NY, 2026, 11, 1, 1, 30, fold=1)
    assert second - first == HOUR
    assert study_day(first, NY) == study_day(second, NY) == date(2026, 10, 31)


def test_rollover_inside_the_gap_starts_at_the_jump() -> None:
    # rollover at 2 AM on spring-forward day: 02:00 does not exist; the day starts at 03:00 EDT
    start = day_start_ms(date(2026, 3, 8), NY, rollover_hour=2)
    assert from_ms(start, NY) == datetime(2026, 3, 8, 3, 0, tzinfo=NY)
    assert study_day(start - 1, NY, 2) == date(2026, 3, 7)
    assert study_day(start, NY, 2) == date(2026, 3, 8)


def test_rollover_in_the_repeated_hour_uses_the_first() -> None:
    start = day_start_ms(date(2026, 11, 1), NY, rollover_hour=1)
    assert start == at(NY, 2026, 11, 1, 1, 0, fold=0)
    assert study_day(at(NY, 2026, 11, 1, 1, 30, fold=1), NY, 1) == date(2026, 11, 1)


@pytest.mark.parametrize(
    ("zone", "transitions"),
    [
        ("America/New_York", [date(2026, 3, 8), date(2026, 11, 1)]),
        ("Europe/London", [date(2026, 3, 29), date(2026, 10, 25)]),
        ("Australia/Lord_Howe", [date(2026, 4, 5), date(2026, 10, 4)]),  # 30-minute shifts
        ("America/Santiago", [date(2026, 4, 5), date(2026, 9, 6)]),  # changes at midnight
        ("UTC", [date(2026, 6, 1)]),
    ],
)
@pytest.mark.parametrize("rollover", [0, 1, 2, 3, 4, 23])
def test_every_instant_falls_inside_its_own_study_day(zone: str, transitions, rollover) -> None:
    tz = ZoneInfo(zone)
    for day in transitions:
        t = to_ms(datetime(day.year, day.month, day.day, tzinfo=UTC)) - 2 * 86_400_000
        stop = t + 4 * 86_400_000
        while t < stop:
            d = study_day(t, tz, rollover)
            start, end = day_bounds_ms(d, tz, rollover)
            assert start <= t < end, (zone, rollover, from_ms(t, tz))
            assert 22 * HOUR <= end - start <= 26 * HOUR
            assert study_day(start, tz, rollover) == d
            assert study_day(start - 1, tz, rollover) == d - timedelta(days=1)
            t += 7 * 60_000 + 13_000


def test_fixed_clock_moves_only_when_told() -> None:
    clock = FixedClock(datetime(2026, 11, 1, tzinfo=UTC), tz="America/New_York")
    first = clock.now_ms()
    assert clock.now_ms() == first
    assert clock.advance(days=1, minutes=1, ms=5) == first + 86_400_000 + 60_000 + 5
    clock.set(0)
    assert clock.now_ms() == 0
    assert clock.tz == NY


def test_system_clock_is_utc_ms_with_a_zone() -> None:
    clock = SystemClock("Europe/Paris")
    now = to_ms(datetime.now(UTC))
    assert abs(clock.now_ms() - now) < 5_000
    assert str(clock.tz) == "Europe/Paris"
    assert SystemClock().tz is not None
