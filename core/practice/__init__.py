"""Practice: the student model and the planner in the app (wave 2,
docs/design/wave2-integration.md section 3). Pure Python, no GUI imports. The only place that
joins storage, packs, `core.learner` and `core.plan`.

- `catalog`: components, problems and per-course plan courses from the loaded content;
- `observations`: attempt rows -> the student model's observations;
- `engine`: `PracticeEngine`, the cached learner state (a pure function of the log), the
  certifiers, the merged daily plan, calibration, refits and parameter resets.

Implementation notes: docs/design/wave2-impl-notes.md.
"""

from core.practice.catalog import (
    BACKGROUND_PREFIXES,
    Catalog,
    CourseEntry,
    SectionRef,
    Textbook,
    build_catalog,
    problem_specs,
    textbook_of,
)
from core.practice.engine import (
    GROWTH_BANDS,
    Bin,
    Calibration,
    PlannedItem,
    PlannerModel,
    PracticeEngine,
    PracticePlan,
    RefitOutcome,
    merge,
    params_from_json,
    params_json,
    plan_settings,
    work_from_json,
    work_item,
    work_json,
)
from core.practice.observations import build_observations, minutes_of, observations_of

__all__ = [
    "BACKGROUND_PREFIXES",
    "GROWTH_BANDS",
    "Bin",
    "Calibration",
    "Catalog",
    "CourseEntry",
    "PlannedItem",
    "PlannerModel",
    "PracticeEngine",
    "PracticePlan",
    "RefitOutcome",
    "SectionRef",
    "Textbook",
    "build_catalog",
    "build_observations",
    "merge",
    "minutes_of",
    "observations_of",
    "params_from_json",
    "params_json",
    "plan_settings",
    "problem_specs",
    "textbook_of",
    "work_from_json",
    "work_item",
    "work_json",
]
