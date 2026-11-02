"""Day-to-day memory of the queue: what each study day's plan asked for, vacations, and the
proposals that need several days of history (QUE-8, QUE-9, QUE-12, QUE-13).

The log lives in the profile setting `queue.day_log` ({study day: entry}), trimmed to the
last five weeks; vacations in `queue.vacation`. Both are plain JSON settings, so they are
exported and backed up with the profile and need no schema change. Pure functions except
`read_*`/`write_*`, which take the UserStore.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from core.queue.config import (
    BACKLOG_DAYS,
    BACKLOG_MULTIPLE,
    DAY_LOG_KEEP,
    DAY_LOG_KEY,
    OVERLOAD_DAYS,
    VACATION_KEY,
    VACATION_LEAD_MAX,
)
from core.storage.user_store import UserStore


@dataclass(frozen=True, slots=True, kw_only=True)
class DayEntry:
    n: int
    need: int  # due work across courses (problem slots of triage classes 1-6)
    backlog: int  # due reviews left out of the day's plan
    quotas: Mapping[str, int] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "need": self.need,
            "backlog": self.backlog,
            "quotas": dict(self.quotas),
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> DayEntry:
        return cls(
            n=int(data.get("n", 0)),
            need=int(data.get("need", 0)),
            backlog=int(data.get("backlog", 0)),
            quotas={str(k): int(v) for k, v in dict(data.get("quotas", {})).items()},
        )


def read_log(users: UserStore) -> dict[date, DayEntry]:
    raw = users.get_setting(DAY_LOG_KEY, {}) or {}
    out: dict[date, DayEntry] = {}
    for key, value in dict(raw).items():
        try:
            out[date.fromisoformat(str(key))] = DayEntry.from_json(value)
        except ValueError, TypeError, AttributeError:
            continue  # a damaged entry never blocks planning
    return out


def write_entry(users: UserStore, day: date, entry: DayEntry) -> None:
    log = read_log(users)
    if log.get(day) == entry:
        return
    log[day] = entry
    keep = sorted(log)[-DAY_LOG_KEEP:]
    users.set_setting(DAY_LOG_KEY, {d.isoformat(): log[d].to_json() for d in keep})


def overloaded(log: Mapping[date, DayEntry], today: date) -> bool:
    """QUE-13: total need above the count on each of the last 3 study days, today included."""
    days = [today - timedelta(days=i) for i in range(OVERLOAD_DAYS)]
    return all(d in log and log[d].need > log[d].n for d in days)


def backlog_stuck(log: Mapping[date, DayEntry], today: date) -> bool:
    """QUE-8: the backlog stayed above 2N for 7 days (days without a plan don't break it,
    but the window must start with a logged day a full week back)."""
    start = today - timedelta(days=BACKLOG_DAYS - 1)
    window = [d for d in log if start <= d <= today]
    if start not in log or today not in log:
        return False
    return all(log[d].backlog > BACKLOG_MULTIPLE * log[d].n for d in window)


# ---------------------------------------------------------------- vacation (QUE-9)


@dataclass(frozen=True, slots=True, kw_only=True)
class Vacation:
    start: date
    end: date  # inclusive

    @property
    def length(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def lead_days(self) -> int:
        """Days before it that take the first half's reviews early."""
        return max(1, min(VACATION_LEAD_MAX, self.length // 2))

    @property
    def middle(self) -> date:
        """Reviews due before this day move earlier; the rest wait until after."""
        return self.start + timedelta(days=(self.length + 1) // 2)

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end

    def lead_index(self, day: date) -> int | None:
        """0 for the first lead day ... lead_days - 1 for the day before the vacation."""
        before = (self.start - day).days
        if 1 <= before <= self.lead_days:
            return self.lead_days - before
        return None

    def to_json(self) -> dict[str, str]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


def read_vacation(users: UserStore) -> Vacation | None:
    raw = users.get_setting(VACATION_KEY, None)
    if not raw:
        return None
    try:
        start, end = date.fromisoformat(raw["start"]), date.fromisoformat(raw["end"])
    except KeyError, TypeError, ValueError:
        return None
    return Vacation(start=start, end=end) if start <= end else None


def write_vacation(users: UserStore, vacation: Vacation | None) -> None:
    users.set_setting(VACATION_KEY, None if vacation is None else vacation.to_json())


def pulled_forward(vacation: Vacation, day: date, due_days: Mapping[str, date | None]) -> list[str]:
    """Skills due in the first half of the vacation, spread evenly over the lead days
    (earliest due first, dealt round robin); the ones dealt to `day`."""
    index = vacation.lead_index(day)
    if index is None:
        return []
    inside = sorted(
        (d, k)
        for k, d in due_days.items()
        if d is not None and vacation.start <= d < vacation.middle
    )
    return [k for i, (_, k) in enumerate(inside) if i % vacation.lead_days == index]
