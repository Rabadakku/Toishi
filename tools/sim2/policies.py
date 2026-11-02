"""The policies under evaluation.

- **P1** (`DesignPolicy`): the new design, `core.learner` + `core.plan` through the backend in
  `adapters` (the stand-in until the branches merge).
- **P0** (`BaselinePolicy`): the design's 6.2 baseline. One FSRS-6 card per skill with the
  defaults of `core/engine/fsrs_adapter.py` (desired retention = the accuracy target, maximum
  interval 365 days, fuzz on). A skill is introduced on its pace date: worked example, then
  random unseen tier 1-2 problems (at most 8 a day, ENG-2) until 3 first tries in a row are
  correct. The card is then created with a Good review, and every due review is one random
  problem at the target tier, rated Good or Again by the first try.

P0 certifies by its own rule: M1 when learning ends (3 in a row); M2 and M3 together after 3
correct first tries in a row at tier 3 or above within the standard time (its reviews are at
the target tier). It never revokes.
"""

from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from typing import Final, Protocol

from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.types import CourseSettings, DayPlan, WorkItem
from tools.sim2.adapters import Backend, ModelLike, PlannerLike
from tools.sim2.common import rng_for
from tools.sim2.course import SimCourse

LEARN_CAP: Final = 8
LEARN_STREAK: Final = 3
REVIEW_STREAK: Final = 3
EXAMPLE_MINUTES: Final = 3.0


class Policy(Protocol):
    name: str  # "P0" or "P1"
    backend: str  # "baseline", "stand-in" or "core"

    def start_day(self, day: date, now_ms: int) -> DayPlan: ...

    def next_item(self, day: date, now_ms: int) -> WorkItem | None: ...

    def predict(self, problem: ProblemSpec, at_ms: int) -> float | None:
        """The policy's chance of a correct first try, before answering (for calibration)."""
        ...

    def observe(self, item: WorkItem, obs: Observation | None, minutes: float) -> None:
        """An answered item (`obs`), or a worked example that was read (`obs` None), and the
        minutes spent on it."""
        ...

    def end_day(self, day: date, now_ms: int) -> None: ...

    def certified(self, skill: ComponentId, tier: int, day: date) -> bool: ...


class DesignPolicy:
    """P1: the student model and planner behind `adapters.Backend`."""

    name = "P1"

    def __init__(
        self, view: SimCourse, settings: CourseSettings, backend: Backend, seed: int
    ) -> None:
        self.backend = backend.name
        self.model: ModelLike = backend.new_model(view.catalog)
        self.state = self.model.new_state(backend.default_params())
        self.planner: PlannerLike = backend.new_planner(self.model, view.course, settings, seed)
        self.served: list[WorkItem] = []

    def start_day(self, day: date, now_ms: int) -> DayPlan:
        self.served = []
        return self.planner.plan_day(self.state, day, now_ms)

    def next_item(self, day: date, now_ms: int) -> WorkItem | None:
        return self.planner.next_item(self.state, day, now_ms, self.served)

    def predict(self, problem: ProblemSpec, at_ms: int) -> float | None:
        return self.model.predict(self.state, problem, at_ms).p

    def observe(self, item: WorkItem, obs: Observation | None, minutes: float) -> None:
        record = self.model.update(self.state, obs) if obs is not None else None
        self.planner.observe(self.state, item, obs, record, minutes)
        self.served.append(item)

    def end_day(self, day: date, now_ms: int) -> None:
        self.planner.end_day(self.state, day, now_ms)

    def certified(self, skill: ComponentId, tier: int, day: date) -> bool:
        return self.planner.certified(self.state, skill, tier, day)


class BaselinePolicy:
    """P0 (see the module docstring)."""

    name = "P0"
    backend = "baseline"

    def __init__(
        self,
        view: SimCourse,
        settings: CourseSettings,
        intro: Mapping[ComponentId, date],
        seed: int,
    ) -> None:
        self.fsrs = FsrsAdapter()
        self.retention = settings.accuracy_target
        self.target_tier = settings.target_tier
        self.pools = view.pools
        self.order = view.skill_ids
        self.example_card = {s: view.skills[s].example_card for s in view.skill_ids}
        self.intro = intro
        self.rng = rng_for("baseline", seed)
        self.cards: dict[ComponentId, Memory] = {}
        self.due: dict[ComponentId, date] = {}
        self.started: set[ComponentId] = set()
        self.learned: set[ComponentId] = set()
        self.learn_streak: dict[ComponentId, int] = {}
        self.review_streak: dict[ComponentId, int] = {}
        self.cert: set[tuple[ComponentId, int]] = set()
        self.last_served: dict[str, int] = {}
        self.queue: list[WorkItem] = []
        self.count_today: dict[ComponentId, int] = {}

    def start_day(self, day: date, now_ms: int) -> DayPlan:
        self.count_today = {}
        items: list[WorkItem] = []
        for s in self.order:
            if self.intro[s] > day or s in self.learned:
                continue
            if s not in self.started:
                items.append(WorkItem(s, "new", None, self.example_card[s], EXAMPLE_MINUTES, 0))
            first = self.pools[s][1][0] if self.pools[s][1] else self.pools[s][2][0]
            items.extend(
                WorkItem(s, "new", first, None, first.standard_minutes, 0) for _ in range(LEARN_CAP)
            )
        due = [s for s in self.order if s in self.learned and self.due[s] <= day]
        due.sort(key=lambda s: self.fsrs.retrievability(self.cards[s], now_ms))
        for s in due:
            rep = self.pools[s][self.target_tier][0]
            items.append(WorkItem(s, "maintenance", rep, None, rep.standard_minutes, 1))
        self.queue = items
        return DayPlan(
            day=day,
            items=tuple(items),
            minutes=sum(i.expected_minutes for i in items),
            hours_to_keep_pace=None,
            standard_hours=None,
        )

    def _pick(self, pool: tuple[ProblemSpec, ...], day: date) -> ProblemSpec | None:
        today = day.toordinal()
        fresh = [p for p in pool if self.last_served.get(p.problem_id, -(10**6)) < today]
        unseen = [p for p in fresh if p.problem_id not in self.last_served]
        cands = unseen or fresh
        return self.rng.choice(cands) if cands else None

    def next_item(self, day: date, now_ms: int) -> WorkItem | None:
        while self.queue:
            item = self.queue.pop(0)
            s = item.skill_id
            if item.problem is None:
                if s in self.started:
                    continue
                return item
            if item.role == "new":
                if s in self.learned or self.count_today.get(s, 0) >= LEARN_CAP:
                    continue
                problem = self._pick((*self.pools[s][1], *self.pools[s][2]), day)
            else:
                problem = self._pick(self.pools[s][self.target_tier], day)
            if problem is None:
                continue
            return replace(item, problem=problem, expected_minutes=problem.standard_minutes)
        return None

    def predict(self, problem: ProblemSpec, at_ms: int) -> float | None:
        card = self.cards.get(problem.main_skill)
        return None if card is None else self.fsrs.retrievability(card, at_ms)

    def observe(self, item: WorkItem, obs: Observation | None, minutes: float) -> None:
        s = item.skill_id
        self.started.add(s)
        if obs is None:
            return
        problem = obs.problem
        day = obs.study_day
        self.last_served[problem.problem_id] = day.toordinal()
        self.count_today[s] = self.count_today.get(s, 0) + 1
        success = obs.correct and not obs.aided
        if item.role == "new":
            streak = self.learn_streak.get(s, 0) + 1 if success else 0
            self.learn_streak[s] = streak
            if streak >= LEARN_STREAK and s not in self.learned:
                self.learned.add(s)
                self._review(s, None, success=True, at_ms=obs.at_ms, day=day)
                self.cert.add((s, 2))
            return
        self._review(s, self.cards[s], success=success, at_ms=obs.at_ms, day=day)
        fast = obs.minutes is not None and obs.minutes <= problem.standard_minutes
        if problem.tier >= 3 and success and fast:
            self.review_streak[s] = self.review_streak.get(s, 0) + 1
        else:
            self.review_streak[s] = 0
        if self.review_streak[s] >= REVIEW_STREAK:
            self.cert.add((s, 3))
            self.cert.add((s, self.target_tier))

    def _review(
        self, skill: ComponentId, card: Memory | None, *, success: bool, at_ms: int, day: date
    ) -> None:
        card = self.fsrs.review(card, 3 if success else 1, at_ms)
        self.cards[skill] = card
        days = self.fsrs.interval_days(card.stability, self.retention, f"{skill}:{at_ms}")
        self.due[skill] = date.fromordinal(day.toordinal() + days)

    def end_day(self, day: date, now_ms: int) -> None:
        return None

    def certified(self, skill: ComponentId, tier: int, day: date) -> bool:
        return (skill, tier) in self.cert
