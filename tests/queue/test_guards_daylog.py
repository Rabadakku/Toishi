"""Timing guards (TIME-4/5), the day log (QUE-8, QUE-13) and vacation helpers (QUE-9)."""

from datetime import date, timedelta

from core.queue.daylog import DayEntry, Vacation, backlog_stuck, overloaded, pulled_forward
from core.queue.guards import TimingReport, guard_timing

NOW = 1_800_000_000_000


def test_consistent_report_passes_through() -> None:
    g = guard_timing(
        TimingReport(active_ms=60_000, solve_ms=50_000, entry_ms=8_000, longest_pause_ms=5_000),
        shown_at=NOW - 90_000,
        now_ms=NOW,
        expected_chars=4,
    )
    assert g.flags == ()
    assert g.timing.active_ms == 60_000
    assert g.timing.solve_ms == 50_000
    assert g.timing.raw_ms == 60_000
    assert g.timing.expected_chars == 4


def test_active_time_is_bounded_by_the_wall_clock() -> None:
    g = guard_timing(
        TimingReport(active_ms=600_000, solve_ms=500_000, entry_ms=1_000),
        shown_at=NOW - 60_000,
        now_ms=NOW,
    )
    assert "active time over wall clock" in g.flags
    assert g.timing.active_ms is not None
    assert g.timing.active_ms <= 62_000


def test_inconsistent_solve_time_leaves_the_speed_baselines() -> None:
    g = guard_timing(
        TimingReport(active_ms=30_000, solve_ms=50_000, entry_ms=1_000),
        shown_at=NOW - 120_000,
        now_ms=NOW,
    )
    assert g.timing.solve_ms is None  # the engine excludes it from baselines
    assert g.timing.active_ms == 30_000
    g = guard_timing(
        TimingReport(active_ms=30_000, solve_ms=-5, entry_ms=1_000),
        shown_at=NOW - 120_000,
        now_ms=NOW,
    )
    assert g.timing.solve_ms is None


def test_saved_active_time_is_a_floor_after_a_resume() -> None:
    g = guard_timing(
        TimingReport(active_ms=5_000, solve_ms=4_000),
        shown_at=NOW - 3_600_000,
        now_ms=NOW,
        saved_active_ms=90_000,
    )
    assert g.timing.active_ms == 90_000
    missing = guard_timing(TimingReport(), shown_at=NOW - 10_000, now_ms=NOW, saved_active_ms=0)
    assert missing.timing.active_ms is None
    assert "no active time" in missing.flags


def test_report_from_untrusted_dict() -> None:
    r = TimingReport.from_dict({"active_ms": "12", "solve_ms": 3.7, "after_wake": 1})
    assert r.active_ms is None
    assert r.solve_ms == 3
    assert r.after_wake is True


def entries(days: int, *, need: int, backlog: int, n: int = 20) -> dict[date, DayEntry]:
    today = date(2026, 10, 10)
    return {
        today - timedelta(days=i): DayEntry(n=n, need=need, backlog=backlog) for i in range(days)
    }


def test_overload_needs_three_days_running() -> None:
    today = date(2026, 10, 10)
    assert overloaded(entries(3, need=25, backlog=0), today)
    assert not overloaded(entries(2, need=25, backlog=0), today)
    log = entries(3, need=25, backlog=0)
    log[today - timedelta(days=1)] = DayEntry(n=20, need=15, backlog=0)
    assert not overloaded(log, today)


def test_backlog_suggestion_after_a_week_above_2n() -> None:
    today = date(2026, 10, 10)
    assert backlog_stuck(entries(7, need=60, backlog=41), today)
    assert not backlog_stuck(entries(6, need=60, backlog=41), today)
    assert not backlog_stuck(entries(7, need=60, backlog=40), today)
    gappy = entries(7, need=60, backlog=41)
    del gappy[today - timedelta(days=3)]  # a day without a plan doesn't break it
    assert backlog_stuck(gappy, today)


def test_vacation_spreads_the_first_half_over_the_days_before() -> None:
    vac = Vacation(start=date(2026, 12, 20), end=date(2026, 12, 29))  # 10 days
    assert vac.lead_days == 5
    assert vac.middle == date(2026, 12, 25)
    due = {f"k{i}": date(2026, 12, 20) + timedelta(days=i % 10) for i in range(30)}
    early = [
        k for d in range(1, 6) for k in pulled_forward(vac, vac.start - timedelta(days=d), due)
    ]
    first_half = {k for k, d in due.items() if d < vac.middle}
    assert sorted(early) == sorted(first_half)
    per_day = [len(pulled_forward(vac, vac.start - timedelta(days=d), due)) for d in range(1, 6)]
    assert max(per_day) - min(per_day) <= 1
    assert pulled_forward(vac, vac.start - timedelta(days=6), due) == []
    assert vac.covers(date(2026, 12, 24))
    assert not vac.covers(date(2026, 12, 30))
