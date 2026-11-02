"""Error diagnosis (milestone M4b): after a miss, find which skill actually broke and route
practice there, without over-trusting the student's own diagnosis (ADR-0008).

Storage-bound facade, `Diagnosis(storage)`:

- engine() -> Engine whose grade() runs the diagnosis hook; grade(outcome) -> Recorded
- daily(at_ms=None) -> DailyReport   expire unserved checks, ENG-15 finder, diagnostic sets
- reason(check) -> str                "Why is this here?" text of a PendingCheck
- tap_calibration() -> TapCalibration self-calibration of step taps (STA: confirmation rate)
- tier_flags() -> [TierFlagNote]      possible wrong tiers (a note; never re-tiers)
- needs_example(skill) / method_choice_active(skill) / find_error_status(skill)

Records the daily queue consumes (UserStore.pending_checks() / diagnostic_sets()):

- PendingCheck(skill_id, kind, card_id, attempt_id, after_items, not_before_at, depth,
  reason): kind "step" (a tapped step's skill, a second slip, an above-level miss),
  "prerequisite" (deepest first: lower after_items first), "cued-twin" (card has a cued
  stem: show it cued), "diagnostic" (one per card of a DiagnosticSet; attempt_id None).
  `reason` is the "Why is this here?" sentence (None on some checks written before
  schema v2: use reason(check)). Pass the check's id as ProblemOutcome.check_of when
  serving it.
- DiagnosticSet(skill_id, weak_spot_id, card_ids, status pending/active/confirmed/cleared).
- Due-date notes: DueSkill.note (ENG-6 pull-forward, a miss waiting for its check).

Pure parts: blame, card_tags, tap_calibration (blame.py); pick_check_card,
prerequisite_targets, check_reason, queue_order (checks.py); place_hold, settle,
slip_decision (verdict.py); pull_forward, partial_credit, credit_targets (credit.py);
skill_evidence, find_weak_spots, diagnostic_cards, diagnostic_step, wrong_tier_flags
(weakspots.py); method_choice_skill, method_choice_active, grade_find_error,
find_error_unlocked, find_error_slot_open, self_graded_facts (items.py).
"""

from core.engine.diagnosis.blame import (
    Tags,
    TapCalibration,
    TapRecord,
    blame,
    card_tags,
    tap_calibration,
)
from core.engine.diagnosis.checks import (
    NewCheck,
    check_reason,
    level_tier,
    pick_check_card,
    prerequisite_targets,
    queue_order,
)
from core.engine.diagnosis.config import DiagnosisSettings
from core.engine.diagnosis.credit import credit_targets, partial_credit, pull_forward
from core.engine.diagnosis.hook import DiagnosisHook, find_check
from core.engine.diagnosis.items import (
    FindErrorGrade,
    find_error_highlighted,
    find_error_slot_open,
    find_error_unlocked,
    grade_find_error,
    method_choice_active,
    method_choice_skill,
    self_graded_facts,
)
from core.engine.diagnosis.service import DailyReport, Diagnosis, daily_run
from core.engine.diagnosis.verdict import SlipDecision, hold_of, settle, slip_decision
from core.engine.diagnosis.weakspots import (
    DiagnosticPlan,
    SkillEvidence,
    TierFlagNote,
    diagnostic_cards,
    diagnostic_step,
    find_weak_spots,
    skill_evidence,
    wrong_tier_flags,
)
from core.engine.diagnosis.world import StorageWorld, World

__all__ = [
    "DailyReport",
    "Diagnosis",
    "DiagnosisHook",
    "DiagnosisSettings",
    "DiagnosticPlan",
    "FindErrorGrade",
    "NewCheck",
    "SkillEvidence",
    "SlipDecision",
    "StorageWorld",
    "Tags",
    "TapCalibration",
    "TapRecord",
    "TierFlagNote",
    "World",
    "blame",
    "card_tags",
    "check_reason",
    "credit_targets",
    "daily_run",
    "diagnostic_cards",
    "diagnostic_step",
    "find_check",
    "find_error_highlighted",
    "find_error_slot_open",
    "find_error_unlocked",
    "find_weak_spots",
    "grade_find_error",
    "hold_of",
    "level_tier",
    "method_choice_active",
    "method_choice_skill",
    "partial_credit",
    "pick_check_card",
    "prerequisite_targets",
    "pull_forward",
    "queue_order",
    "self_graded_facts",
    "settle",
    "skill_evidence",
    "slip_decision",
    "tap_calibration",
    "wrong_tier_flags",
]
