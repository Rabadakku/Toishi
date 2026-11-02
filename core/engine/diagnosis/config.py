"""Diagnosis constants (docs/spec.md: "What went wrong?", ENG-6, ENG-7, ENG-15, ENG-16) and
the settings the diagnosis reads. The numbers are the spec's starting values, or this
module's reading of the spec where it gives none (marked "reading").
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from core.storage import settings as setting_specs

CreditSetting = Literal["off", "shadow", "on"]

# ---- blame ("What went wrong?", ENG-15)
TAP_SHARE = 0.6  # blame on the tapped step's skill
TAP_SHARE_MATCHED = 0.8  # ... when the typed answer matched a known wrong answer of that step
MAIN_TAG_WEIGHT = 1.0
USES_TAG_WEIGHT = 0.4
UNKNOWN_RECALL = 0.5  # reading: a skill with no FSRS card counts as half known
# Self-calibration: if fewer than half of the checked taps are confirmed (minimum sample),
# taps count for less: their share scales by rate / 0.5, never below the floor.
TAP_MIN_SAMPLE = 20
TAP_CONFIRM_TARGET = 0.5
TAP_SHARE_FLOOR = 0.3
TAP_LOG_DAYS = 365

# ---- checks (What went wrong?, ENG-6, QUE "how the session is ordered" 5)
CHECK_AFTER_ITEMS = 3  # at least three items later (or next session)
CHECK_MAX_TIER = 2  # ENG-6: a tier 1 or 2 problem
UNVERIFIED = "unverified"  # ENG-6: diagnosis key listing prerequisites with no pool yet
CHECK_MIN_P = 0.6  # predicted success of a check problem
LOW_RECALL = 0.85  # reading: "low-recall" prerequisites get checks
MAX_PREREQ_CHECKS = 4  # reading: at most this many prerequisite checks per failure
CHECK_EXPIRY_DAYS = 7  # reading: a check not served within a week is cancelled
ABOVE_LEVEL_P = 0.35  # a miss on a problem predicted below this may be "just a hard problem"

# ---- slips (What went wrong?)
SLIP_MIN_RECALL = 0.90
SLIP_CLEAN_RUN = 2  # its last two attempts correct
SLIP_WINDOW_DAYS = 30

# ---- ENG-6 pull-forward
PULL_MIN_WEIGHT = 0.5
PULL_DAYS = 2  # reading: due no later than two study days after the lapse

# ---- ENG-7 partial credit (shadow mode)
CREDIT_MIN_PRODUCT = 0.25
CREDIT_FAILED_DAYS = 7
CREDIT_VERY_DIFFICULT = 9.0  # reading: FSRS difficulty (1..10) at or above this
CREDIT_FORCE_RATIO = 2.0

# ---- ENG-15 weak-spot finder
WEAK_WINDOW_DAYS = 30
WEAK_TAU = 0.75  # prior variance added under the square root
WEAK_Z = -2.0  # display only since ADR-0019: the flag is the exact tail below
WEAK_TAIL_P = 0.025  # ENG-15: one-sided exact binomial tail (Poisson-binomial) at or below
WEAK_MIN_EVIDENCE = 5.0  # problems' worth of evidence
WEAK_MIN_PROBLEMS = 3  # misses on this many different problems ...
WEAK_MIN_DAYS = 2  # ... on this many different days
# ENG-15 / ADR-0019 item 9: sequential confirmation (truncated SPRT, Wald), H0 success 0.85
# against H1 0.55, alpha 0.10, beta 0.20, at most 8 fresh problems (provisional; the
# derivation is in the full evidence review, engine notes section 9, scripts/sim_sprt.py).
DIAG_SET_MAX = 8
DIAG_SET_MIN = 3
DIAG_CONFIRM_MISSES = 2  # the fewest misses that can confirm (two in the first two)
SPRT_P0 = 0.85
SPRT_P1 = 0.55
SPRT_ALPHA = 0.10
SPRT_BETA = 0.20
WEEK_DAYS = 7
# The stated false-positive budget: a student the model describes (outcomes as Elo predicts,
# honest taps) is flagged in at most 5% of skill-months (the simulation checks it).
FALSE_POSITIVE_BUDGET = 0.05

# ---- possible wrong tier (ENG-5): a run of surprising results on a template or family
WRONG_TIER_RUN = 3
WRONG_TIER_SURPRISE = 0.6

# ---- ENG-16 and the extra item kinds
METHOD_ACTIVE_LEARNED = 2  # active once two of its methods are learned
FIND_ERROR_UNLOCK = 2  # successful uncued reviews before find-the-error items
FIND_ERROR_HIGHLIGHT_UNTIL = 2  # reading: highlighted until this many solved
# Multi-part problems: a part answered right credits its own skill like an encompassed skill
# of weight 1 (ENG-7's formula, setting and exclusions; one part is not a full review).
PART_CREDIT_WEIGHT = 1.0


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosisSettings:
    credit: CreditSetting = "shadow"
    diagnostic_per_week: int = 2
    find_error_one_in: int | None = 10  # None: find-the-error items are off

    @classmethod
    def from_settings(cls, values: Mapping[str, Any]) -> DiagnosisSettings:
        def get(key: str) -> Any:
            return values[key] if key in values else setting_specs.default(key)

        one_in = get("queue.find_error_one_in")
        return cls(
            credit=str(get("credit.partial")),  # type: ignore[arg-type]
            diagnostic_per_week=int(get("diagnostic.max_per_week")),
            find_error_one_in=None if one_in is None else int(one_in),
        )
