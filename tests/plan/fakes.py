"""A deterministic fake student model for planner tests.

It follows the shape of design 3.2 with numbers a test can set directly:

- execution e_k at a tier: `e_tier[(k, tier)]`, else `e[k]` (default `default_e`) times
  `tier_factor[tier]` (default 1), clipped to [0, 1];
- memory: R_k = 0.9 ** (days since `last_ms[k]` / `stability[k]`) for a course component
  with a stability, else 1 (background components and components never reviewed);
- q_k = e_k * R_k, P_raw = (1 - slip) * prod q_k, P = P_raw (no recalibration);
- median minutes = standard minutes * `speed`; pace_ok = median <= standard.
"""

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from core.learner.types import ComponentId, ComponentInfo, Prediction, ProblemSpec

DAY_MS = 86_400_000


@dataclass
class FakeState:
    e: dict[ComponentId, float] = field(default_factory=dict)
    e_tier: dict[tuple[ComponentId, int], float] = field(default_factory=dict)
    tier_factor: dict[int, float] = field(default_factory=dict)
    default_e: float = 0.9
    stability: dict[ComponentId, float] = field(default_factory=dict)
    last_ms: dict[ComponentId, int] = field(default_factory=dict)
    slip: float = 0.0
    speed: float = 1.0
    speed_skill: dict[ComponentId, float] = field(default_factory=dict)


class FakePredictor:
    """Satisfies core.plan.protocol.Predictor[FakeState]."""

    def __init__(self, catalog: Mapping[ComponentId, ComponentInfo]) -> None:
        self.catalog = dict(catalog)
        self.calls = 0

    def component_info(self, component_id: ComponentId) -> ComponentInfo | None:
        return self.catalog.get(component_id)

    def slip(self, state: FakeState) -> float:
        return state.slip

    def copy(self, state: FakeState) -> FakeState:
        return copy.deepcopy(state)

    def execution(self, state: FakeState, component: ComponentId, tier: int) -> float:
        found = state.e_tier.get((component, tier))
        if found is None:
            found = state.e.get(component, state.default_e) * state.tier_factor.get(tier, 1.0)
        return min(1.0, max(0.0, found))

    def memory(self, state: FakeState, component: ComponentId, at_ms: int) -> float:
        info = self.catalog.get(component)
        if info is None or info.background or component not in state.stability:
            return 1.0
        last = state.last_ms.get(component)
        if last is None:
            return 1.0
        days = max(0.0, (at_ms - last) / DAY_MS)
        return float(0.9 ** (days / state.stability[component]))

    def predict(self, state: FakeState, problem: ProblemSpec, at_ms: int) -> Prediction:
        self.calls += 1
        e = tuple((k, self.execution(state, k, problem.tier)) for k in problem.components)
        r = tuple((k, self.memory(state, k, at_ms)) for k in problem.components)
        q = tuple((k, ek * rk) for (k, ek), (_, rk) in zip(e, r, strict=True))
        p_raw = (1.0 - state.slip) * math.prod(v for _, v in q)
        speed = state.speed_skill.get(problem.main_skill, state.speed)
        median = problem.standard_minutes * speed
        return Prediction(
            p=p_raw,
            p_raw=p_raw,
            q=q,
            e=e,
            r=r,
            median_minutes=median,
            pace_ok=median <= problem.standard_minutes,
        )
