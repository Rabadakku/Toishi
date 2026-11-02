"""Learning engine, scheduling core (milestone M4a): FSRS per skill, a fresh problem per review.

The engine computes; storage persists. Everything below is a pure function over the
records in core.model except `Engine`, which loads rows from a Storage, calls them and
writes the results through UserStore (one transaction per graded answer).

Public API (what the daily queue and the bridge call)
-----------------------------------------------------

Storage-bound facade, `Engine(storage, hooks=())`:

- grade(outcome) -> Recorded            grade a final submission and commit it
- record_try(outcome) -> Attempt         log a non-final wrong attempt (never rated)
- pick_problem(skill_id, stretch=, lighter_set=, last_card_id=) -> Pick | None
- due_skills(day=None) -> list[DueSkill] due on a study day, most overdue first (QUE-4 flag)
- recall(skill_id, at_ms=None) / recall_on(skill_id, day) -> float | None
- booster_plan(day=None) -> BoosterPlan  exam and pre-course boosters (ENG-8, LIB-8)
- exam_projection(exam_id) -> ExamProjection     exam-day recall, share at Exam-level,
                                                 projected score, holding back (LIB-9)
- course_load(course_id) -> LoadProjection       goal's projected daily load (LIB-4)
- level(skill_id) -> LevelName | None; target_time(skill_id, tier) -> int | None (ms)
- retention(skill_id, day=None) -> float          desired retention in force (goals)
- calibration() / calibration_stats() / fit_offer()   ENG-11 bins, I8 stats data, items
- fit(set_id, candidate=) / auto_fit() / fit_due()     ENG-12 fits adopted only if they win
- recompute_memory() / void_attempts() / check_database()   memory rebuilt from the log
- adapter_for(kind, group) / adapter_for_skill() / adapter_for_card()   parameter sets
- parameter_history(set_id) / revert_parameters(set_id, params_id)   (ADR-0013)
- place(seeds)                                    placement / Covered / Solid seeds
- context(skill_id) -> SkillContext               the rows grading reads

Pure functions (same inputs, same outputs; no clock, no I/O):

- grade_answer(ctx, outcome, settings=, adapter=, days=, hooks=) -> GradeResult
  GradeResult.answer is the GradedAnswer for UserStore.record_answer.
- rate(facts, speed, rules) -> RatingDecision     the rating map + ENG-14 (rating.py)
- FsrsAdapter: retrievability, review (= next-state preview), replay, interval_days
- due_day(state, retention, adapter, days); due_skills(...); scheduled_load(...)
- core_band, stretch_tier, stretch_allowed, pick_problem, elo_update (selection.py)
- update_level, is_fading, checkup_due, checkup_candidates (level.py)
- booster_targets, plan_boosters, practice_tests_open (boosters.py)
- project_exam, project_load, load_warning (projection.py)
- computed_target_ms, next_target, speed_time_ms, cap_ms (timing.py)
- PlacementWalk, apply_seeds (placement.py); calibrate, fit_offer, fit_parameters

Extension point for the diagnosis milestone: `GradeHook` callables passed to Engine or
grade_answer run after base grading and return a (possibly changed) GradeResult. Base
grading reports what they act on in `Effects` (lapse, reinforcement_due, core_followup_due,
prerequisite_checks, leech, confident_error, ...) and takes the careless-slip cap decision
as an input (`AnswerFacts.slip_within_cap`).
"""

from core.engine.boosters import (
    Booster,
    BoosterPlan,
    BoostTarget,
    booster_targets,
    plan_boosters,
    practice_tests_open,
)
from core.engine.calibration import (
    CalibrationReport,
    FitOffer,
    FitResult,
    FitUnavailable,
    calibrate,
    fit_offer,
    fit_parameters,
)
from core.engine.config import RULES_VERSION, EngineSettings
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.engine.goals import Catalog, course_retention, preset_for, skill_retention
from core.engine.grading import (
    Effects,
    GradeHook,
    GradeResult,
    ProblemOutcome,
    SkillContext,
    grade_answer,
    record_try,
)
from core.engine.level import Evidence, checkup_candidates, checkup_due, is_fading, update_level
from core.engine.lifecycle import due_day, learning_step, memory_of
from core.engine.parts import PartOutcome, card_facts, own_skill_parts, remaining_parts
from core.engine.placement import PlacementWalk, apply_seeds
from core.engine.projection import ExamProjection, LoadProjection, project_exam, project_load
from core.engine.rating import AnswerFacts, RatingDecision, RatingRules, SpeedFacts, rate
from core.engine.schedule import DueSkill, due_skills, new_skill_room, scheduled_load
from core.engine.selection import (
    Pick,
    SeenIndex,
    core_band,
    elo_update,
    pick_problem,
    stretch_allowed,
    stretch_tier,
)
from core.engine.service import Engine, Recorded
from core.engine.timing import TimingFacts, computed_target_ms, next_target, speed_time_ms

__all__ = [
    "RULES_VERSION",
    "AnswerFacts",
    "BoostTarget",
    "Booster",
    "BoosterPlan",
    "CalibrationReport",
    "Catalog",
    "DueSkill",
    "Effects",
    "Engine",
    "EngineSettings",
    "Evidence",
    "ExamProjection",
    "FitOffer",
    "FitResult",
    "FitUnavailable",
    "FsrsAdapter",
    "GradeHook",
    "GradeResult",
    "LoadProjection",
    "Memory",
    "PartOutcome",
    "Pick",
    "PlacementWalk",
    "ProblemOutcome",
    "RatingDecision",
    "RatingRules",
    "Recorded",
    "SeenIndex",
    "SkillContext",
    "SpeedFacts",
    "StudyDays",
    "TimingFacts",
    "apply_seeds",
    "booster_targets",
    "calibrate",
    "card_facts",
    "checkup_candidates",
    "checkup_due",
    "computed_target_ms",
    "core_band",
    "course_retention",
    "due_day",
    "due_skills",
    "elo_update",
    "fit_offer",
    "fit_parameters",
    "grade_answer",
    "is_fading",
    "learning_step",
    "memory_of",
    "new_skill_room",
    "next_target",
    "own_skill_parts",
    "pick_problem",
    "plan_boosters",
    "practice_tests_open",
    "preset_for",
    "project_exam",
    "project_load",
    "rate",
    "record_try",
    "remaining_parts",
    "scheduled_load",
    "skill_retention",
    "speed_time_ms",
    "stretch_allowed",
    "stretch_tier",
    "update_level",
]
