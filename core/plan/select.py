"""Choosing the problem (docs/design/student-model.md v1.1, section 4.4). Pure functions; the
only randomness, the reference check's uniform draw, goes through the `random.Random` passed
in.

| Role | Choice |
|---|---|
| new | tier 1-2 problems of the skill, the highest predicted chance first |
| growth | the milestone tier or one below, predicted P in [0.70, 0.90], preferring problems that
  contain the bottleneck; after a miss with spread blame (top suspect b < 0.7), a problem with
  the top suspect and without the runner-up; an empty band takes the problem closest to 0.80 |
| maintenance | the certified tier, P closest to the target |
| check | uniform over the skill's unseen problems at the tier |

Variety, for every role: never a card already served (or planned) today; no card seen in the
last 90 days (a template instance, its parameter set, 180) while the pool has one that wasn't,
the least recently seen breaking ties otherwise; a different surface form (`family`: a
template, or the card itself) from the skill's previous problem when there is a choice.
"""

import random
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import date

from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.config import (
    EPS,
    GROWTH_BAND,
    GROWTH_FALLBACK_P,
    NEW_TIERS,
    REPEAT_DAYS,
    SPREAD_BLAME,
    TEMPLATE_REPEAT_DAYS,
)
from core.plan.protocol import Predict
from core.plan.types import Role, ServedItem, SkillInfo


def is_template_instance(problem: ProblemSpec) -> bool:
    """A template instance's family is its template ID; any other card is its own family."""
    return problem.family not in ("", problem.card_id)


def repeat_window(problem: ProblemSpec) -> int:
    """Days before a card may be served again while the pool allows: 90, or 180 for a
    template instance (its parameter set)."""
    return TEMPLATE_REPEAT_DAYS if is_template_instance(problem) else REPEAT_DAYS


class Seen:
    """When each card was last served, in study days, plus the cards served or planned today
    (never served twice in a study day)."""

    def __init__(
        self,
        history: Iterable[Observation],
        today: date,
        served_today: Iterable[ServedItem] = (),
    ) -> None:
        self.today = today
        self.last_day: dict[str, date] = {}
        for obs in history:
            card = obs.problem.card_id
            prev = self.last_day.get(card)
            if prev is None or obs.study_day > prev:
                self.last_day[card] = obs.study_day
        self.today_cards: set[str] = {c for c, d in self.last_day.items() if d == today}
        for served in served_today:
            if served.item.problem is not None:
                self.today_cards.add(served.item.problem.card_id)
            if served.item.example_card is not None:
                self.today_cards.add(served.item.example_card)

    def add(self, card_id: str) -> None:
        """Plan a card for today: it can't be chosen again today."""
        self.today_cards.add(card_id)

    def served_today(self, card_id: str) -> bool:
        return card_id in self.today_cards

    def fresh(self, problem: ProblemSpec) -> bool:
        last = self.last_day.get(problem.card_id)
        return last is None or (self.today - last).days >= repeat_window(problem)

    def unseen(self, problem: ProblemSpec) -> bool:
        """Never served: not in the history and not today."""
        return problem.card_id not in self.last_day and problem.card_id not in self.today_cards

    def staleness(self, problem: ProblemSpec) -> int:
        """Order key among recently seen candidates: the least recently seen first."""
        last = self.last_day.get(problem.card_id)
        return 0 if last is None else last.toordinal()


@dataclass(frozen=True, slots=True)
class Choice:
    problem: ProblemSpec
    p: float
    reason: str  # new, band, bottleneck, suspect, fallback, target, check
    relaxed: bool = False  # every candidate had been seen within its repeat window


def suspects(served: Sequence[ServedItem], skill_id: ComponentId) -> tuple[ComponentId, ...]:
    """After a miss with spread blame (design 4.4): when the skill's latest first try today
    was a miss whose top suspect's blame is below 0.7, (top suspect, runner-up); else ()."""
    for x in reversed(served):
        if x.item.skill_id != skill_id or x.item.problem is None or x.correct is None:
            continue
        if x.correct or x.update is None or not x.update.blame:
            return ()
        ranked = sorted(x.update.blame, key=lambda kv: (-kv[1], kv[0]))
        if ranked[0][1] >= SPREAD_BLAME - EPS:
            return ()
        return tuple(k for k, _ in ranked[:2])
    return ()


def _pool(
    skill: SkillInfo, tiers: Collection[int], seen: Seen, retired: Collection[str]
) -> tuple[list[ProblemSpec], bool]:
    """Candidates at the tiers, never one served today, fresh ones only while there are any.
    Returns (candidates, relaxed)."""
    cands = [
        p
        for p in skill.pool
        if p.tier in tiers and p.card_id not in retired and not seen.served_today(p.card_id)
    ]
    fresh = [p for p in cands if seen.fresh(p)]
    return (fresh, False) if fresh else (cands, bool(cands))


def _same_form(problem: ProblemSpec, previous: ProblemSpec | None) -> bool:
    return previous is not None and problem.family == previous.family


def choose_new(
    skill: SkillInfo,
    predict: Predict,
    seen: Seen,
    *,
    previous: ProblemSpec | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """A new skill's blocked problem: tier 1-2, the highest predicted chance first."""
    cands, relaxed = _pool(skill, NEW_TIERS, seen, retired)
    if not cands:
        return None
    best = min(
        cands,
        key=lambda c: (
            -round(predict(c).p, 9),
            _same_form(c, previous),
            seen.staleness(c) if relaxed else 0,
            c.problem_id,
        ),
    )
    return Choice(best, predict(best).p, "new", relaxed)


def choose_growth(
    skill: SkillInfo,
    tier: int,
    predict: Predict,
    seen: Seen,
    *,
    previous: ProblemSpec | None = None,
    bottleneck: ComponentId | None = None,
    suspect: Sequence[ComponentId] = (),
    retired: Collection[str] = (),
) -> Choice | None:
    """Growth at the milestone tier or one below, in the band [0.70, 0.90]."""
    tiers = {tier, tier - 1} - {0}
    cands, relaxed = _pool(skill, tiers, seen, retired)
    if not cands:
        return None
    lo, hi = GROWTH_BAND
    top = suspect[0] if suspect else None
    runner = suspect[1] if len(suspect) > 1 else None

    def suspect_ok(c: ProblemSpec) -> bool:
        if top is None:
            return True
        return top in c.components and (runner is None or runner not in c.components)

    def has_bottleneck(c: ProblemSpec) -> bool:
        return bottleneck is not None and bottleneck in c.components

    def dist(c: ProblemSpec) -> float:
        return round(abs(predict(c).p - GROWTH_FALLBACK_P), 9)

    band = [c for c in cands if lo - EPS <= predict(c).p <= hi + EPS]
    if band:
        best = min(
            band,
            key=lambda c: (
                not suspect_ok(c),
                not has_bottleneck(c),
                _same_form(c, previous),
                c.tier != tier,
                dist(c),
                seen.staleness(c) if relaxed else 0,
                c.problem_id,
            ),
        )
        if top is not None and suspect_ok(best):
            reason = "suspect"
        elif has_bottleneck(best):
            reason = "bottleneck"
        else:
            reason = "band"
        return Choice(best, predict(best).p, reason, relaxed)
    best = min(
        cands,
        key=lambda c: (
            dist(c),
            not suspect_ok(c),
            not has_bottleneck(c),
            _same_form(c, previous),
            c.tier != tier,
            seen.staleness(c) if relaxed else 0,
            c.problem_id,
        ),
    )
    return Choice(best, predict(best).p, "fallback", relaxed)


def choose_maintenance(
    skill: SkillInfo,
    tier: int,
    predict: Predict,
    seen: Seen,
    *,
    target: float,
    previous: ProblemSpec | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """Maintenance at the certified tier: P closest to the target."""
    cands, relaxed = _pool(skill, {tier}, seen, retired)
    if not cands:
        return None
    best = min(
        cands,
        key=lambda c: (
            round(abs(predict(c).p - target), 9),
            _same_form(c, previous),
            seen.staleness(c) if relaxed else 0,
            c.problem_id,
        ),
    )
    return Choice(best, predict(best).p, "target", relaxed)


def check_candidates(
    skill: SkillInfo, tier: int, seen: Seen, retired: Collection[str] = ()
) -> list[ProblemSpec]:
    """A reference check's eligible problems: the skill's unseen problems at the tier."""
    return sorted(
        (p for p in skill.pool if p.tier == tier and p.card_id not in retired and seen.unseen(p)),
        key=lambda p: p.problem_id,
    )


def choose_check(
    skill: SkillInfo,
    tier: int,
    seen: Seen,
    rng: random.Random,
    *,
    retired: Collection[str] = (),
) -> ProblemSpec | None:
    """A reference check: uniform over the skill's unseen problems at the tier."""
    cands = check_candidates(skill, tier, seen, retired)
    return rng.choice(cands) if cands else None


def choose(
    role: Role,
    skill: SkillInfo,
    tier: int,
    predict: Predict,
    seen: Seen,
    *,
    previous: ProblemSpec | None = None,
    target: float = 0.90,
    bottleneck: ComponentId | None = None,
    suspect: Sequence[ComponentId] = (),
    rng: random.Random | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """The problem for one item of `role` (see the module table); None when nothing
    qualifies. `tier`: the milestone tier (growth, check) or the certified tier
    (maintenance); new items ignore it (tiers 1-2)."""
    if role == "new":
        return choose_new(skill, predict, seen, previous=previous, retired=retired)
    if role == "growth":
        return choose_growth(
            skill,
            tier,
            predict,
            seen,
            previous=previous,
            bottleneck=bottleneck,
            suspect=suspect,
            retired=retired,
        )
    if role == "maintenance":
        return choose_maintenance(
            skill, tier, predict, seen, target=target, previous=previous, retired=retired
        )
    if role == "check":
        if rng is None:
            raise ValueError("a reference check needs the random.Random of the plan")
        found = choose_check(skill, tier, seen, rng, retired=retired)
        return None if found is None else Choice(found, predict(found).p, "check")
    raise ValueError(f"the planner chooses no problems for role {role!r}")


def choose_problem(
    role: Role,
    skill: SkillInfo,
    tier: int,
    predict: Predict,
    seen: Seen,
    *,
    previous: ProblemSpec | None = None,
    target: float = 0.90,
    bottleneck: ComponentId | None = None,
    suspect: Sequence[ComponentId] = (),
    rng: random.Random | None = None,
    retired: Collection[str] = (),
) -> ProblemSpec | None:
    """Design 8's `choose_problem`: the chosen problem only (None: nothing qualifies)."""
    found = choose(
        role,
        skill,
        tier,
        predict,
        seen,
        previous=previous,
        target=target,
        bottleneck=bottleneck,
        suspect=suspect,
        rng=rng,
        retired=retired,
    )
    return None if found is None else found.problem
