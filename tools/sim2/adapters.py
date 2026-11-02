"""Where `core.learner` and `core.plan` plug into the simulator (design section 8).

Policy P1 talks to a `Backend`: a model (`ModelLike`, the `StudentModel` contract) and a
per-student planner session (`PlannerLike`). Two backends exist:

- `stand-in` (`tools.sim2.standin`): used until branches model-core and plan-core merge.
  Its results are provisional and the report labels them "stand-in".
- `core`: the real implementations. `load_backend("auto")` picks it as soon as
  `core.learner.StudentModel` and `core.plan.plan_day` exist.

The `core` wiring follows the code on branches model-core and plan-core as of 2026-11-02:

- the planner's model protocol (`core.plan.Predictor`) asks for `component_info()` and
  `slip()`, which `StudentModel` does not define there; `_PlannerModel` adds them from the
  catalog and the shared parameters (and defers to the model's own if it gains them);
- `Certifier` is an immutable snapshot of the observation log with the model's priors
  (`Certifier.for_course(log, course, settings, today=..., priors=model_priors(...))`), so it
  is rebuilt after each answer; the priors are computed once per study day;
- `next_item` is the first item of a fresh `plan_day` over the items served today
  (`ServedItem`s with outcomes, updates and minutes), as wave 2 will call it;
- a refit runs when `core.learner.refit_due` says so, and `RefitDecision.params` is adopted.

`core_backend_problems()` lists what no longer matches; run it after the merge.
"""

import importlib
import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Protocol, cast

from core.learner.types import (
    ComponentId,
    ComponentInfo,
    Observation,
    Prediction,
    ProblemSpec,
    SharedParams,
    StudentState,
    UpdateRecord,
)
from core.plan.types import Course, CourseSettings, DayPlan, WorkItem
from tools.sim2 import standin

type BackendKind = Literal["auto", "stand-in", "core"]


class ModelLike(Protocol):
    def new_state(self, params: SharedParams) -> StudentState: ...

    def predict(self, state: StudentState, problem: ProblemSpec, at_ms: int) -> Prediction: ...

    def update(self, state: StudentState, obs: Observation) -> UpdateRecord: ...


class PlannerLike(Protocol):
    """One student's planner session: plans and serves a day, ingests what happened."""

    def plan_day(self, state: StudentState, today: date, now_ms: int) -> DayPlan: ...

    def next_item(
        self, state: StudentState, today: date, now_ms: int, served_today: Sequence[WorkItem]
    ) -> WorkItem | None: ...

    def observe(
        self,
        state: StudentState,
        item: WorkItem,
        obs: Observation | None,
        record: UpdateRecord | None,
        minutes: float,
    ) -> None:
        """A served item: its first try and model update (None for a worked example) and
        the minutes spent on it."""
        ...

    def end_day(self, state: StudentState, today: date, now_ms: int) -> None: ...

    def certified(
        self, state: StudentState, skill: ComponentId, tier: int, today: date
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class Backend:
    name: str  # "stand-in" or "core"
    final: bool  # False: P1 results are provisional and labelled "stand-in"
    intro_dates: Callable[[Course, CourseSettings], dict[ComponentId, date]]
    new_model: Callable[[Mapping[ComponentId, ComponentInfo]], ModelLike]
    default_params: Callable[[], SharedParams]
    new_planner: Callable[[ModelLike, Course, CourseSettings, int], PlannerLike]


# ---------------------------------------------------------------- stand-in


def _standin_planner(
    model: ModelLike, course: Course, settings: CourseSettings, seed: int
) -> PlannerLike:
    if not isinstance(model, standin.StandinModel):
        raise TypeError("the stand-in planner needs the stand-in model")
    return standin.StandinPlanner(model, course, settings, seed)


STANDIN = Backend(
    name="stand-in",
    final=False,
    intro_dates=standin.intro_dates,
    new_model=standin.StandinModel,
    default_params=SharedParams,
    new_planner=_standin_planner,
)


# ---------------------------------------------------------------- core

REQUIRED: dict[str, tuple[str, ...]] = {
    "core.learner": ("StudentModel", "refit_due", "calibration_drift"),
    "core.plan": ("intro_dates", "plan_day", "next_item", "Certifier", "model_priors"),
    "core.plan.types": ("ServedItem",),
}
PLAN_DAY_ARGS = (
    "model",
    "state",
    "certifier",
    "course",
    "settings",
    "today",
    "now_ms",
    "served_today",
)
PLAN_DAY_KEYWORDS = ("examples_seen", "spent_minutes")


def core_available() -> bool:
    """True once the real modules export what the core wiring uses."""
    try:
        for module, names in REQUIRED.items():
            loaded = importlib.import_module(module)
            if not all(hasattr(loaded, n) for n in names):
                return False
    except ImportError:
        return False
    return True


def core_backend_problems() -> list[str]:
    """Mismatches between the merged modules and what `_CorePlanner` assumes."""
    if not core_available():
        return ["core.learner / core.plan do not export the names the core wiring uses yet"]
    plan: Any = importlib.import_module("core.plan")
    learner: Any = importlib.import_module("core.learner")
    problems: list[str] = []
    params = list(inspect.signature(plan.plan_day).parameters)
    if params[: len(PLAN_DAY_ARGS)] != list(PLAN_DAY_ARGS):
        problems.append(f"core.plan.plan_day{tuple(params)} does not start {PLAN_DAY_ARGS}")
    problems += [
        f"core.plan.plan_day has no keyword {k!r}" for k in PLAN_DAY_KEYWORDS if k not in params
    ]
    for method in ("new_state", "predict", "update", "copy", "refit"):
        if not hasattr(learner.StudentModel, method):
            problems.append(f"core.learner.StudentModel has no {method}()")
    if not hasattr(plan.Certifier, "for_course") or not hasattr(plan.Certifier, "certified"):
        problems.append("core.plan.Certifier has no for_course() or certified()")
    return problems


class _PlannerModel:
    """`core.learner.StudentModel` as `core.plan.Predictor` wants it."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.catalog: Mapping[ComponentId, ComponentInfo] = getattr(inner, "catalog", {})

    def new_state(self, params: SharedParams) -> StudentState:
        return cast(StudentState, self.inner.new_state(params))

    def predict(self, state: StudentState, problem: ProblemSpec, at_ms: int) -> Prediction:
        return cast(Prediction, self.inner.predict(state, problem, at_ms))

    def update(self, state: StudentState, obs: Observation) -> UpdateRecord:
        return cast(UpdateRecord, self.inner.update(state, obs))

    def copy(self, state: StudentState) -> StudentState:
        return cast(StudentState, self.inner.copy(state))

    def component_info(self, component_id: ComponentId) -> ComponentInfo | None:
        own = getattr(self.inner, "component_info", None)
        if own is not None:
            return cast(ComponentInfo | None, own(component_id))
        return self.catalog.get(component_id)

    def slip(self, state: StudentState) -> float:
        own = getattr(self.inner, "slip", None)
        return float(own(state)) if own is not None else state.params.slip

    def sigma_t(self, state: StudentState) -> float:
        """sigma_T for a sitting's pace chance (the planner's optional protocol method)."""
        own = getattr(self.inner, "sigma_t", None)
        return float(own(state)) if own is not None else state.params.sigma_t


class _CorePlanner:
    """The real planner behind `PlannerLike` (see the module docstring)."""

    def __init__(
        self, model: ModelLike, course: Course, settings: CourseSettings, seed: int
    ) -> None:
        self.plan: Any = importlib.import_module("core.plan")
        self.served_cls: Any = importlib.import_module("core.plan.types").ServedItem
        self.learner: Any = importlib.import_module("core.learner")
        self.model = model
        self.course = course
        self.settings = settings
        self.observations: list[Observation] = []
        self.spent: dict[int, float] = {}
        self.served: list[Any] = []
        self.examples_seen: set[ComponentId] = set()
        self.examples_today: set[ComponentId] = set()
        self.priors: dict[tuple[ComponentId, int], float] = {}
        self.certifier: Any = None
        self.attempts_at_refit: int | None = None  # the log's size at the last refit
        self.since_refit: list[tuple[bool, float]] = []  # (success, prediction) since then

    def _certify(self, today: date) -> None:
        self.certifier = self.plan.Certifier.for_course(
            self.observations, self.course, self.settings, today=today, priors=self.priors
        )

    def _plan(self, state: StudentState, today: date, now_ms: int) -> DayPlan:
        plan = self.plan.plan_day(
            self.model,
            state,
            self.certifier,
            self.course,
            self.settings,
            today,
            now_ms,
            tuple(self.served),
            examples_seen=frozenset(self.examples_seen),
            spent_minutes=self.spent,
        )
        return cast(DayPlan, plan)

    def plan_day(self, state: StudentState, today: date, now_ms: int) -> DayPlan:
        self.examples_seen |= self.examples_today
        self.examples_today = set()
        self.served = []
        self.priors = cast(
            dict[tuple[ComponentId, int], float],
            self.plan.model_priors(self.model, state, self.course, now_ms),
        )
        self._certify(today)
        return self._plan(state, today, now_ms)

    def next_item(
        self, state: StudentState, today: date, now_ms: int, served_today: Sequence[WorkItem]
    ) -> WorkItem | None:
        plan = self._plan(state, today, now_ms)
        return plan.items[0] if plan.items else None

    def observe(
        self,
        state: StudentState,
        item: WorkItem,
        obs: Observation | None,
        record: UpdateRecord | None,
        minutes: float,
    ) -> None:
        if obs is None:
            self.examples_today.add(item.skill_id)
            self.served.append(self.served_cls(item, correct=None, minutes=minutes))
            return
        self.observations.append(obs)
        self.spent[obs.attempt_id] = minutes
        success = obs.correct and not obs.aided
        self.served.append(self.served_cls(item, correct=success, update=record, minutes=minutes))
        if record is not None:
            self.since_refit.append((success, record.prediction.p))
        if self.certifier is None:
            self._certify(obs.study_day)
        else:
            self.certifier.add(obs)

    def end_day(self, state: StudentState, today: date, now_ms: int) -> None:
        drift = self.learner.calibration_drift(self.since_refit)
        if not self.learner.refit_due(
            attempts=len(self.observations), at_last_refit=self.attempts_at_refit, drift=drift
        ):
            return
        inner: Any = getattr(self.model, "inner", self.model)
        decision = inner.refit(self.observations, state.params)
        self.attempts_at_refit = len(self.observations)
        self.since_refit = []
        if decision.adopted:
            # A new parameter version: the state is the replay of the log under it (C3).
            state_new, _ = inner.replay(decision.params, self.observations)
            state.params = state_new.params
            state.components = state_new.components
            state.skill_speed = state_new.skill_speed
            state.time_stats = state_new.time_stats
            state.theta_hat = state_new.theta_hat
            state.last_at_ms = state_new.last_at_ms

    def certified(self, state: StudentState, skill: ComponentId, tier: int, today: date) -> bool:
        if self.certifier is None:
            return False
        return bool(self.certifier.certified(skill, tier, today))


def _core_backend() -> Backend:
    learner: Any = importlib.import_module("core.learner")
    plan: Any = importlib.import_module("core.plan")

    def new_model(catalog: Mapping[ComponentId, ComponentInfo]) -> ModelLike:
        return _PlannerModel(learner.StudentModel(catalog))

    def intro(course: Course, settings: CourseSettings) -> dict[ComponentId, date]:
        return cast(dict[ComponentId, date], plan.intro_dates(course, settings))

    return Backend(
        name="core",
        final=True,
        intro_dates=intro,
        new_model=new_model,
        default_params=SharedParams,
        new_planner=_CorePlanner,
    )


def load_backend(kind: BackendKind = "auto") -> Backend:
    """`auto`: the real modules when they exist, otherwise the stand-in."""
    if kind == "stand-in":
        return STANDIN
    if kind == "core" or (kind == "auto" and core_available()):
        problems = core_backend_problems()
        if problems:
            raise RuntimeError(
                "core backend does not match tools/sim2/adapters.py: " + "; ".join(problems)
            )
        return _core_backend()
    return STANDIN
