"""Engine constants (the spec's numbers) and the per-profile settings the engine reads.

Every number here comes from docs/spec.md ("Learning engine", "Study screen", "Library",
"Settings and defaults"). They are starting values; changing a rating rule means bumping
RULES_VERSION so ENG-12 fitting only uses reviews graded under the current rules.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.storage import settings as setting_specs

# Stored on every Attempt and ReviewEvent (ENG-12: "only reviews graded under the current
# rating rules are used"). Bump it whenever rating.rate() or the slow-answer rule changes.
# Events under older rules stay in fit histories as prefixes; only current-rules events
# are prediction targets (ADR-0013). r2: a wrong final answer is never a pass (ADR-0014);
# r3: r2 merged with ADR-0013's whole-day clock and learning-phase replay (ADR-0016).
# r4: below-band items never train and a below-band success has no event; time never
# changes a rating; a practice-test miss is Again at every tier (ADR-0019).
RULES_VERSION = "2026.11-r4"

AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4

DAY_MS = 86_400_000
MINUTE_MS = 60_000

# ENG-5: tier 1..5 anchor difficulties, Elo constants, target success.
TIER_DIFFICULTY: Mapping[int, float] = {1: -1.5, 2: -0.5, 3: 0.5, 4: 1.5, 5: 2.5}
ELO_A = 1.0
ELO_B = 0.05
ELO_TARGET_P = 0.80
ELO_MAX_DRIFT_PER_ANSWER = 0.05
ELO_MAX_DRIFT_TOTAL = 0.5  # half a tier: beyond it a card is flagged, never re-tiered
SEEN_SKIP_DAYS = 90
PARAMS_SKIP_DAYS = 180

# ENG-13 / TIME-4 / TIME-5: speed.
TIER_FLOOR_MS: Mapping[int, int] = {1: 20_000, 2: 40_000, 3: 60_000, 4: 90_000, 5: 120_000}
# Share of one exam problem's time per tier: tiers 1-2 "a quarter to two fifths", 3-4 "a
# half to four fifths"; the range is spread over the pair. Tier 5 (above exam) gets a whole one.
TIER_EXAM_SHARE: Mapping[int, float] = {1: 0.25, 2: 0.40, 3: 0.50, 4: 0.80, 5: 1.0}
EXAM_TIME_USABLE = 0.85
EARLY_MEDIAN_SHARE = 0.70
EARLY_CORRECT_COUNT = 5
TARGET_TIGHTEN_PER_WEEK = 0.10
TYPING_BASE_MS = 5_000
TYPING_PER_CHAR_MS = 300
CAP_TARGET_MULTIPLE = 4
CAP_MIN_MS = 3 * MINUTE_MS
CAP_MAX_MS = 30 * MINUTE_MS
BASELINE_LONG_PAUSE_MS = 2 * MINUTE_MS
BASELINE_WINDOW = 20  # most recent eligible successes per skill and tier

# ENG-14: slow answers.
SLOW_MULTIPLE = 2.0
SLOW_MULTIPLE_LOW_RECALL = 2.5
SLOW_LOW_RECALL = 0.85
SLOW_MIN_TIMED_SUCCESSES = 5

# ENG-10: Level and Recall.
FADING_RECALL = 0.80
MASTERED_MIN_ELAPSED_DAYS = 7.0
MASTERED_MAX_RECALL = 0.90
SHAKY_WINDOW = 3
LEVEL_LOG_LIMIT = 30

# ENG-8 / LIB-8 / goal presets.
BOOSTER_WINDOW_DAYS = 21
PRACTICE_TEST_DAYS = BOOSTER_WINDOW_DAYS  # tests open with the booster window (ENG-8, QUE-18)
NEXT_COURSE_PREREQ_RETENTION = 0.85
PRE_COURSE_RECALL = 0.90
KEEP_RETENTION = 0.80

# Placement and section states (Library).
PLACEMENT_DIRECT_STABILITY = 10.0
PLACEMENT_INFERRED_STABILITY = 2.3
PLACEMENT_MAX_QUESTIONS = 25

# ENG-11 / ENG-12.
CALIBRATION_BINS = 10
CALIBRATION_MIN_BIN = 30  # bins with fewer reviews are greyed out and never alarm
CALIBRATION_MAX_ERROR = 0.10  # the old notice rule, kept only for comparison (ADR-0013)
CALIBRATION_ALPHA = 0.05  # family-wise alarm level, Bonferroni-split over the shown bins
MATURE_DAYS = 21  # true retention: young below, mature at or above (Anki's Stats)

# ENG-12 fitting, adopted only when it wins (ADR-0013; Anki params.rs, fsrs-rs).
PARAM_DECIMALS = 6
FIT_MIN_ITEMS = 300  # long-term items before the first automatic fit (and the health check)
FIT_MIN_REVIEWS = FIT_MIN_ITEMS  # old name
FIT_EVERY_DAYS = 30  # refit monthly ...
FIT_GROWTH = 2.0  # ... or when the long-term items double
FIT_EPOCHS = 8  # as Anki trains
HELD_OUT_FOLDS = 5  # time-ordered folds, segment = N / (folds + 1)
HEALTH_MAX_LOG_LOSS = 1.11  # adjusted log loss (Anki params.rs)
HEALTH_MAX_RMSE = 1.53  # adjusted RMSE(bins)
PARAM_HISTORY_LIMIT = 50  # parameter-set history entries kept per set


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineSettings:
    """The settings the engine reads, with the spec's defaults (see core.storage.settings)."""

    correct_in_a_row: int = 3
    max_learning_problems: int = 8
    maximum_interval_days: int = 365
    rollover_hour: int = 4
    stretch_fraction: float = 0.10
    elite: bool = True
    too_easy_key: bool = True
    slow_rule: bool = True
    leech_lapses: int = 8  # ENG-9: Anki's default, provisional (ADR-0019 item 9)
    longest_wait_days: int = 7
    new_skills_per_day: int = 4
    daily_problems: int = 20
    checkup_every_weeks: int | None = 3

    @classmethod
    def from_settings(cls, values: Mapping[str, Any]) -> EngineSettings:
        """Build from UserStore.settings() (missing keys take the storage defaults)."""

        def get(key: str) -> Any:
            return values[key] if key in values else setting_specs.default(key)

        return cls(
            correct_in_a_row=int(get("learning.correct_in_a_row")),
            max_learning_problems=int(get("learning.max_problems")),
            maximum_interval_days=int(get("fsrs.maximum_interval_days")),
            rollover_hour=int(get("study.day_start_hour")),
            stretch_fraction=float(get("queue.stretch_fraction")),
            elite=bool(get("queue.elite")),
            too_easy_key=bool(get("rating.too_easy_key")),
            slow_rule=bool(get("rating.slow_rule")),
            leech_lapses=int(get("leech.skill_lapses")),
            longest_wait_days=int(get("queue.longest_wait_days")),
            new_skills_per_day=int(get("daily.new_skills")),
            daily_problems=int(get("daily.problems")),
            checkup_every_weeks=get("queue.checkup_every_weeks"),
        )
