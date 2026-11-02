"""Profile settings: keys, defaults and allowed ranges (spec "Settings and defaults").

Values are stored as JSON in user.db's `setting` table; a key that was never set reads
as its default. Validation checks shapes only (type, range, options). Unknown keys are
accepted as any JSON value so newer engine code can add settings without a migration.
Course goals live in `course_goal`, not here; the data folder lives outside user.db.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.model import ShapeError
from core.storage.clock import DEFAULT_ROLLOVER_HOUR


@dataclass(frozen=True, slots=True)
class SettingSpec:
    default: Any
    kind: type  # bool, int, float, str or dict
    low: float | None = None
    high: float | None = None
    options: tuple[str, ...] = ()
    nullable: bool = False  # None means "Off"

    def check(self, key: str, value: Any) -> None:
        if value is None:
            if not self.nullable:
                raise ShapeError(f"setting {key} cannot be off")
            return
        ok_type = (
            isinstance(value, bool)
            if self.kind is bool
            else isinstance(value, int | float) and not isinstance(value, bool)
            if self.kind is float
            else isinstance(value, self.kind) and not isinstance(value, bool)
        )
        if not ok_type:
            raise ShapeError(f"setting {key} must be {self.kind.__name__}, got {value!r}")
        if self.options and value not in self.options:
            raise ShapeError(f"setting {key} must be one of {self.options}, got {value!r}")
        if self.low is not None and value < self.low:
            raise ShapeError(f"setting {key} must be >= {self.low}, got {value!r}")
        if self.high is not None and value > self.high:
            raise ShapeError(f"setting {key} must be <= {self.high}, got {value!r}")


WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

SETTINGS: dict[str, SettingSpec] = {
    "daily.problems": SettingSpec(20, int, 1, 200),
    "daily.flashcards": SettingSpec(50, int, 0, 500),
    "daily.new_flashcards": SettingSpec(20, int, 0, 500),  # inside daily.flashcards (Anki)
    "daily.minutes_cap": SettingSpec(None, int, 10, 480, nullable=True),
    "daily.new_skills": SettingSpec(4, int, 0, 20),
    "learning.correct_in_a_row": SettingSpec(3, int, 2, 5),
    "learning.max_problems": SettingSpec(8, int, 4, 15),
    "study.attempts_per_problem": SettingSpec(2, int, 1, 3),
    "study.hints": SettingSpec(True, bool),
    "fsrs.maximum_interval_days": SettingSpec(365, int, 30, 3650),
    "study.day_start_hour": SettingSpec(DEFAULT_ROLLOVER_HOUR, int, 0, 23),
    "study.timezone": SettingSpec(None, str, nullable=True),  # None: the Mac's zone
    "queue.longest_wait_days": SettingSpec(7, int, 1, 30),
    "queue.stretch_fraction": SettingSpec(0.10, float, 0.0, 0.25),
    "queue.elite": SettingSpec(True, bool),
    "rating.too_easy_key": SettingSpec(True, bool),
    "credit.partial": SettingSpec("shadow", str, options=("off", "shadow", "on")),
    "queue.triage_policy": SettingSpec(
        "recommended", str, options=("recommended", "lowest-recall-first")
    ),
    "leech.skill_lapses": SettingSpec(8, int, 3, 20),  # provisional (ADR-0019 item 9)
    "leech.flashcard_lapses": SettingSpec(8, int, 3, 20),
    "queue.easy_days": SettingSpec({}, dict),  # weekday ("mon".."sun") -> load percent
    "ui.show_time": SettingSpec(True, bool),
    "ui.break_reminder_minutes": SettingSpec(50, int, 25, 90, nullable=True),
    "ui.theme": SettingSpec("automatic", str, options=("automatic", "day", "night")),
    "ui.text_size_px": SettingSpec(18, int, 14, 28),
    "backup.interval_minutes": SettingSpec(30, int, 5, 240),
    "backup.keep_last": SettingSpec(10, int, 1, 100),
    "backup.keep_daily": SettingSpec(7, int, 0, 60),
    "backup.keep_weekly": SettingSpec(4, int, 0, 52),
    "backup.keep_monthly": SettingSpec(6, int, 0, 60),
    "export.daily_summary": SettingSpec(False, bool),
    "session.untimed_default": SettingSpec(False, bool),
    "time.still_working_floor_minutes": SettingSpec(5, int, 2, 30),
    "rating.slow_rule": SettingSpec(True, bool),
    "diagnostic.max_per_week": SettingSpec(2, int, 0, 5),
    "queue.find_error_one_in": SettingSpec(10, int, 5, 20, nullable=True),
    "queue.min_per_course_problems": SettingSpec(3, int, 0, 10),
    "queue.min_per_course_fraction": SettingSpec(0.10, float, 0.0, 1.0),
    "queue.checkup_every_weeks": SettingSpec(3, int, 1, 6, nullable=True),
}


def default(key: str) -> Any:
    spec = SETTINGS.get(key)
    if spec is None:
        raise KeyError(f"unknown setting {key!r} and no default given")
    value = spec.default
    return dict(value) if isinstance(value, dict) else value


def validate(key: str, value: Any) -> None:
    spec = SETTINGS.get(key)
    if spec is not None:
        spec.check(key, value)
        if key == "queue.easy_days":
            _check_easy_days(value)
        if key == "study.timezone" and value is not None:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError) as error:
                raise ShapeError(f"unknown time zone {value!r}") from error
    elif not key or len(key) > 200:
        raise ShapeError("setting keys are 1 to 200 characters")


def _check_easy_days(value: Mapping[str, Any]) -> None:
    for day, percent in value.items():
        if day not in WEEKDAYS:
            raise ShapeError(f"easy day {day!r} is not one of {WEEKDAYS}")
        if not isinstance(percent, int | float) or isinstance(percent, bool):
            raise ShapeError(f"easy day load for {day} must be a number")
        if not 0 <= percent <= 100:
            raise ShapeError(f"easy day load for {day} must be 0..100")


def defaults() -> dict[str, Any]:
    return {key: default(key) for key in SETTINGS}
