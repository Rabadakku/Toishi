"""The planner's view of the student model (docs/design/student-model.md v1.1, section 8).

The planner never looks inside the student state. It asks the model for predictions (the
calibrated chance `p`, the per-component execution `e`, memory `r` and product `q`, and the
median time) and for two facts: whether a component is a course or a background component
(the bottleneck rule, design 4.4; background components never gate, 4.1) and the slip rate
(the slip-limited status, 4.2, and the feasibility check, 4.3).

`core.learner.StudentModel` satisfies this protocol; tests use a deterministic fake.

Optional (wave 2): `sigma_t(state) -> float`, the spread of the student's log solve times
(design 3.3's sigma_T), for a sitting's chance of finishing within its time. A model without
it gets design 3.5's prior 0.45 (`core.plan.sitting.sigma_of`); the protocol's required
methods are unchanged.
"""

from collections.abc import Callable
from typing import Protocol

from core.learner.types import ComponentId, ComponentInfo, Prediction, ProblemSpec


class Predictor[S](Protocol):
    """What the planner needs from a student model whose state type is `S`.

    `predict` must depend on the problem only through `main_skill`, `components`, `tier`,
    `steps` and `standard_minutes` (true of design 3.2-3.3): the planner caches predictions
    on those fields, so a template's instances share one prediction.
    """

    def predict(self, state: S, problem: ProblemSpec, at_ms: int) -> Prediction:
        """The prediction for a first try at `problem` at `at_ms`. Never mutates `state`."""
        ...

    def copy(self, state: S) -> S:
        """A deep copy of `state`, for what-if questions."""
        ...

    def component_info(self, component_id: ComponentId) -> ComponentInfo | None:
        """The catalog entry of a component; None when the model does not know it (the
        planner then treats it as background: outside the course's sections)."""
        ...

    def slip(self, state: S) -> float:
        """The student's slip rate s."""
        ...


type ProblemKey = tuple[ComponentId, tuple[ComponentId, ...], int, int, float]


def problem_key(problem: ProblemSpec) -> ProblemKey:
    """The fields a prediction depends on (see `Predictor`)."""
    return (
        problem.main_skill,
        problem.components,
        problem.tier,
        problem.steps,
        problem.standard_minutes,
    )


class Forecast[S]:
    """Predictions for one state at one moment, cached per `problem_key`. Callable."""

    __slots__ = ("_cache", "at_ms", "model", "state")

    def __init__(self, model: Predictor[S], state: S, at_ms: int) -> None:
        self.model = model
        self.state = state
        self.at_ms = at_ms
        self._cache: dict[ProblemKey, Prediction] = {}

    def __call__(self, problem: ProblemSpec) -> Prediction:
        key = problem_key(problem)
        found = self._cache.get(key)
        if found is None:
            found = self.model.predict(self.state, problem, self.at_ms)
            self._cache[key] = found
        return found


type Predict = Callable[[ProblemSpec], Prediction]


def is_course_component[S](
    model: Predictor[S], component_id: ComponentId, course_id: str | None = None
) -> bool:
    """A component of the course's own sections (design 2.1): known to the model, not
    background, and of this course when the catalog names one."""
    info = model.component_info(component_id)
    if info is None or info.background:
        return False
    return course_id is None or info.course_id is None or info.course_id == course_id
