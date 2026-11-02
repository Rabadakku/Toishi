"""Simulated learners for the diagnosis: hidden gaps, honest-ish taps, slips.

A learner solves a step-tagged problem step by step: each step succeeds with the learner's
true ability on that step's skill (a method-choice step with `choose` when uncued, always
when cued). The first failing step is the true error; with no failing step a careless slip
happens with probability `slip`. In the picker the learner reports the truth with
probability `honesty` (the step, Step 0 for a method-choice failure, "slip" for a slip),
otherwise taps another step or says "can't tell". The engine never sees the abilities.
"""

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

from core.engine.config import DAY_MS, TIER_DIFFICULTY
from core.engine.diagnosis import hold_of, queue_order
from core.engine.selection import core_band
from core.model import Card, PendingCheck
from tests.engine.diagnosis.fixtures import answer
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import at_day

ITEM_MS = 3 * 60_000


def rng(seed: int) -> random.Random:
    return random.Random(seed)  # noqa: S311 -- reproducible simulations, not security


@dataclass
class Learner:
    ability: dict[str, float] = field(default_factory=dict)
    choose: float = 0.97  # uncued method choice
    slip: float = 0.0
    honesty: float = 0.6
    default: float = 0.97
    calibrated: bool = False  # succeed as an Elo model with these true abilities predicts
    theta: dict[str, float] = field(default_factory=dict)
    rng: random.Random = field(default_factory=lambda: rng(1))

    def skill_p(self, w: MemoryWorld, skill_id: str, cued: bool) -> float:
        skill = w.skills().get(skill_id)
        if skill is not None and skill.method_choice:
            return 1.0 if cued else self.choose
        return self.ability.get(skill_id, self.default)

    def solve(self, w: MemoryWorld, card: Card, cued: bool) -> tuple[bool, int | None, str | None]:
        """(correct, true failing step, cause "step" | "slip" | None)."""
        steps = [(s.number, s.skill_id or card.skill_id or "") for s in card.solution]
        if not steps:
            steps = [(0, card.skill_id or "")]
        if self.calibrated:  # a fixed true ability the Elo model can learn
            theta = self.theta.get(card.skill_id or "", 1.0)
            p = 1 / (1 + math.exp(-(theta - TIER_DIFFICULTY[card.tier])))
            if self.rng.random() < p:
                return True, None, None
            # The failing step falls on the steps in proportion to their tag weights
            # (main 1, uses 0.4): the null the weak-spot finder's weights describe.
            weights = [1.0 if k == card.skill_id else 0.4 for _, k in steps]
            return False, self.rng.choices(steps, weights=weights)[0][0], "step"
        for number, skill in steps:
            if self.rng.random() >= self.skill_p(w, skill, cued):
                return False, number, "step"
        if self.rng.random() < self.slip:
            return False, self.rng.choice(steps)[0], "slip"
        return True, None, None

    def report(
        self, w: MemoryWorld, card: Card, step: int | None, cause: str | None
    ) -> dict[str, object]:
        numbers = [s.number for s in card.solution] or [0]
        honest = self.rng.random() < self.honesty
        if cause == "slip":
            return {"choice": "slip"} if honest else _tap(self.rng.choice(numbers))
        if honest:
            return _tap(step)
        others = [n for n in numbers if n != step]
        if not others or self.rng.random() < 0.3:
            return {"choice": "cant-tell"}
        return _tap(self.rng.choice(others))


def _tap(step: int | None) -> dict[str, object]:
    if step == 0:
        return {"choice": "setup", "didnt_know_start": True}
    return {"choice": "step", "step": step}


@dataclass
class Run:
    w: MemoryWorld
    learner: Learner
    focus: list[str]
    per_day: int = 4  # focus problems per day (checks come on top)
    rng: random.Random = field(default_factory=lambda: rng(7))
    problems: int = 0  # every graded problem, checks included
    misses: int = 0
    weak_spots: int = 0
    _item: int = 0
    _created: dict[int, int] = field(default_factory=dict)  # check id -> item index

    def pick(self, skill_id: str, last: str | None) -> Card:
        state = self.w.states.get(skill_id)
        band = core_band(state.stability if state else None)
        pool = [
            c
            for c in self.w._cards.values()
            if c.skill_id == skill_id and c.kind == "problem" and c.tier in band and c.id != last
        ]
        return self.rng.choice(pool)

    def serve(self, card: Card, at: int, check: PendingCheck | None = None) -> None:
        cued = check is not None and check.kind == "cued-twin"
        correct, step, cause = self.learner.solve(self.w, card, cued)
        extra: dict[str, object] = {"cued": True} if cued else {}
        kw: dict[str, object] = {} if correct else self.learner.report(self.w, card, step, cause)
        outcome = answer(
            self.w,
            card.id,
            at,
            correct=correct,
            check_of=check.id if check is not None else None,
            extra=extra,
            **kw,  # type: ignore[arg-type]
        )
        self.w.grade(outcome)
        self.problems += 1
        self.misses += 0 if correct else 1
        self._item += 1
        for c in self.w.pending():
            self._created.setdefault(c.id or 0, self._item)

    def ready_checks(self) -> list[PendingCheck]:
        return [
            c
            for c in queue_order(self.w.pending())
            if c.kind == "diagnostic"
            or self._item >= self._created.get(c.id or 0, 0) + c.after_items
        ]

    def day(self, n: int, done: Callable[[], bool] = lambda: False) -> bool:
        """One session; True as soon as `done` holds."""
        start = at_day(n)
        self.weak_spots += len(self.w.daily(start).weak_spots)
        self._created = {k: -99 for k in self._created}  # a new session: all checks ready
        at = start
        last: dict[str, str] = {}
        for i in range(self.per_day * len(self.focus)):
            for check in self.ready_checks():
                card = self.w.card(check.card_id or "")
                if card is not None:
                    self.serve(card, at, check)
                    at += ITEM_MS
                    if done():
                        return True
            skill = self.focus[i % len(self.focus)]
            if hold_of(self.w.states.get(skill)) is not None:
                continue  # waiting for its check: not due again until tomorrow
            card = self.pick(skill, last.get(skill))
            last[skill] = card.id
            self.serve(card, at)
            at += ITEM_MS
            if done():
                return True
        return False

    def until(self, done: Callable[[], bool], *, max_days: int) -> int | None:
        """Problems served until `done` holds (None: not within max_days)."""
        for n in range(max_days):
            if self.day(n, done):
                return self.problems
        return None


def agains(w: MemoryWorld, skill_id: str) -> int:
    return sum(1 for e in w.events_for(skill_id) if e.rating == 1)


def day_ms(n: int) -> int:
    return n * DAY_MS
