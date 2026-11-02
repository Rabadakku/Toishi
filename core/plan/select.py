"""Choosing the problem (docs/design/student-model.md, section 4.4, and the wave 2 additions of
docs/design/wave2-planner.md). Pure functions; the only randomness (the reference check's and
the sitting's uniform draws) goes through the `random.Random` passed in.

| Role | Choice |
|---|---|
| new | tier 1-2 problems of the skill, the highest predicted chance first |
| growth | the milestone tier or one below, predicted P in the course's growth band (default
  [0.70, 0.90]), preferring problems that contain the bottleneck; after a miss with spread
  blame (top suspect b < 0.7), a problem with the top suspect and without the runner-up; an
  empty band takes the problem closest to the band's midpoint |
| maintenance | the certified tier, P closest to the target |
| check | uniform over the skill's unseen problems at the tier |
| ladder 1 | a problem of the skill one tier lower containing the most-blamed component |
| ladder 2 | a tier 1-2 problem of the blamed prerequisite |
| return | after a set-aside: the failing tier, a family not served in the last 7 days |
| sitting | 2 unseen problems at the milestone tier from different families, 3 when the pool
  allows, drawn uniformly; the least recently served ones when too few are unseen |

Variety, for every role: never a card already served (or planned) today; no card seen in the
last 90 days (a template instance, its parameter set, 180) while the pool has one that wasn't,
the least recently seen breaking ties otherwise; a different surface form (`family`: a
template, or the card itself) from the skill's previous problem when there is a choice.
"""

import random
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.config import (
    EPS,
    GROWTH_BAND,
    LADDER_PREREQUISITE_TIERS,
    NEW_TIERS,
    REPEAT_DAYS,
    SITTING_PROBLEMS,
    SITTING_PROBLEMS_MAX,
    SPREAD_BLAME,
    TEMPLATE_REPEAT_DAYS,
)
from core.plan.protocol import Predict
from core.plan.types import Role, ServedItem, SkillInfo

type Band = tuple[float, float]


def band_midpoint(band: Band) -> float:
    """The fallback target of an empty growth band: its midpoint (0.80 for the default)."""
    return (band[0] + band[1]) / 2.0


def is_template_instance(problem: ProblemSpec) -> bool:
    """A template instance's family is its template ID; any other card is its own family."""
    return problem.family not in ("", problem.card_id)


def repeat_window(problem: ProblemSpec) -> int:
    """Days before a card may be served again while the pool allows: 90, or 180 for a
    template instance (its parameter set)."""
    return TEMPLATE_REPEAT_DAYS if is_template_instance(problem) else REPEAT_DAYS


class Seen:
    """When each card (and each family) was last served, in study days, plus the cards served
    or planned today (never served twice in a study day)."""

    def __init__(
        self,
        history: Iterable[Observation],
        today: date,
        served_today: Iterable[ServedItem] = (),
    ) -> None:
        self.today = today
        self.last_day: dict[str, date] = {}
        self.family_day: dict[str, date] = {}
        for obs in history:
            card = obs.problem.card_id
            prev = self.last_day.get(card)
            if prev is None or obs.study_day > prev:
                self.last_day[card] = obs.study_day
            fam = obs.problem.family or card
            prev = self.family_day.get(fam)
            if prev is None or obs.study_day > prev:
                self.family_day[fam] = obs.study_day
        self.today_cards: set[str] = {c for c, d in self.last_day.items() if d == today}
        for served in served_today:
            if served.item.problem is not None:
                self.today_cards.add(served.item.problem.card_id)
                self.family_day[served.item.problem.family or served.item.problem.card_id] = today
            if served.item.example_card is not None:
                self.today_cards.add(served.item.example_card)
        self.planned: set[str] = set()  # planned today by the plan being built

    def add(self, card_id: str) -> None:
        """Plan a card for today: it can't be chosen again today."""
        self.planned.add(card_id)

    def discard(self, card_id: str) -> None:
        """Take back a planned card (its item was replaced or removed)."""
        self.planned.discard(card_id)

    def served_today(self, card_id: str) -> bool:
        return card_id in self.today_cards or card_id in self.planned

    def fresh(self, problem: ProblemSpec) -> bool:
        last = self.last_day.get(problem.card_id)
        return last is None or (self.today - last).days >= repeat_window(problem)

    def unseen(self, problem: ProblemSpec) -> bool:
        """Never served: not in the history and not today."""
        return problem.card_id not in self.last_day and not self.served_today(problem.card_id)

    def staleness(self, problem: ProblemSpec) -> int:
        """Order key among recently seen candidates: the least recently seen first."""
        last = self.last_day.get(problem.card_id)
        return 0 if last is None else last.toordinal()

    def family_recent(self, problem: ProblemSpec, days: int) -> bool:
        """The problem's family was served in the last `days` study days (or today)."""
        last = self.family_day.get(problem.family or problem.card_id)
        return last is not None and last >= self.today - timedelta(days=days)


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
    """Growth at the milestone tier or one below, in the default band [0.70, 0.90] (the
    planner uses the course's band: `choose_growth_in`)."""
    return choose_growth_in(
        GROWTH_BAND,
        skill,
        tier,
        predict,
        seen,
        previous=previous,
        bottleneck=bottleneck,
        suspect=suspect,
        retired=retired,
    )


def choose_growth_in(
    band: Band,
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
    """Growth at the milestone tier or one below, in `band` (CourseSettings.growth_band); an
    empty band takes the problem closest to its midpoint."""
    tiers = {tier, tier - 1} - {0}
    cands, relaxed = _pool(skill, tiers, seen, retired)
    if not cands:
        return None
    lo, hi = band
    middle = band_midpoint(band)
    top = suspect[0] if suspect else None
    runner = suspect[1] if len(suspect) > 1 else None

    def suspect_ok(c: ProblemSpec) -> bool:
        if top is None:
            return True
        return top in c.components and (runner is None or runner not in c.components)

    def has_bottleneck(c: ProblemSpec) -> bool:
        return bottleneck is not None and bottleneck in c.components

    def dist(c: ProblemSpec) -> float:
        return round(abs(predict(c).p - middle), 9)

    inside = [c for c in cands if lo - EPS <= predict(c).p <= hi + EPS]
    if inside:
        best = min(
            inside,
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


def _usable(
    skill: SkillInfo, tiers: Collection[int], seen: Seen, retired: Collection[str]
) -> list[ProblemSpec]:
    """The skill's problems at the tiers that are not retired and not served or planned
    today, by problem id."""
    return sorted(
        (
            p
            for p in skill.pool
            if p.tier in tiers and p.card_id not in retired and not seen.served_today(p.card_id)
        ),
        key=lambda p: p.problem_id,
    )


def _least_served_key(
    c: ProblemSpec, seen: Seen, predict: Predict, middle: float, previous: ProblemSpec | None
) -> tuple[bool, int, bool, float, str]:
    """Never served first, then the least recently served; then a different surface form from
    the previous problem, then the predicted chance closest to `middle`."""
    return (
        c.card_id in seen.last_day,
        seen.staleness(c),
        _same_form(c, previous),
        round(abs(predict(c).p - middle), 9),
        c.problem_id,
    )


def choose_smaller(
    skill: SkillInfo,
    tier: int,
    component: ComponentId,
    predict: Predict,
    seen: Seen,
    *,
    band: Band = GROWTH_BAND,
    previous: ProblemSpec | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """Ladder rung 1 (wave 2): a problem of the skill one tier below `tier` (at least tier 1)
    whose components include `component`, the most-blamed one of the last miss (when that is
    the skill itself, any problem of the skill at that tier). Never served first, then the
    least recently served. When no problem at that tier has the component, the skill's other
    problems there stand in; when the tier has none left, the next tier down."""
    middle = band_midpoint(band)
    for t in range(max(1, tier - 1), 0, -1):
        cands = _usable(skill, {t}, seen, retired)
        if not cands:
            continue
        pool = [p for p in cands if component in p.components] or cands
        best = min(pool, key=lambda c: _least_served_key(c, seen, predict, middle, previous))
        return Choice(best, predict(best).p, "ladder:smaller")
    return None


def choose_prerequisite(
    skill: SkillInfo,
    predict: Predict,
    seen: Seen,
    *,
    band: Band = GROWTH_BAND,
    previous: ProblemSpec | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """Ladder rung 2 (wave 2): a tier 1-2 problem of the prerequisite `skill`, never served
    first, then the least recently served, then closest to the band's midpoint."""
    cands = _usable(skill, LADDER_PREREQUISITE_TIERS, seen, retired)
    if not cands:
        return None
    middle = band_midpoint(band)
    best = min(cands, key=lambda c: _least_served_key(c, seen, predict, middle, previous))
    return Choice(best, predict(best).p, "ladder:prerequisite")


def choose_return(
    skill: SkillInfo,
    tier: int,
    predict: Predict,
    seen: Seen,
    *,
    days: int,
    band: Band = GROWTH_BAND,
    previous: ProblemSpec | None = None,
    retired: Collection[str] = (),
) -> Choice | None:
    """The first problem after a set-aside day (wave 2): at `tier`, the tier where the skill
    was failing, from a family not served in the last `days` study days; never served first,
    then the least recently served. None when every such family was served that recently."""
    cands = [p for p in _usable(skill, {tier}, seen, retired) if not seen.family_recent(p, days)]
    if not cands:
        return None
    middle = band_midpoint(band)
    best = min(cands, key=lambda c: _least_served_key(c, seen, predict, middle, previous))
    return Choice(best, predict(best).p, "return")


@dataclass(frozen=True, slots=True)
class SittingPick:
    problems: tuple[ProblemSpec, ...]
    thin: bool  # too few unseen problems: least recently served ones stand in


def choose_sitting(
    skill: SkillInfo,
    tier: int,
    seen: Seen,
    rng: random.Random,
    *,
    retired: Collection[str] = (),
) -> SittingPick | None:
    """A skill's sitting problems (wave 2): 2 problems at the tier that the student has never
    been served (any role), from different families, drawn uniformly (families, then a problem
    of each); 3 when 3 such families exist. With fewer than 2 such families, the least
    recently served problems stand in, one per family while families last (`thin`). None
    when fewer than 2 problems at the tier are left today."""
    usable = _usable(skill, {tier}, seen, retired)
    by_family: dict[str, list[ProblemSpec]] = {}
    for p in usable:
        if p.card_id not in seen.last_day:
            by_family.setdefault(p.family or p.card_id, []).append(p)
    if len(by_family) >= SITTING_PROBLEMS:
        families = rng.sample(sorted(by_family), min(SITTING_PROBLEMS_MAX, len(by_family)))
        return SittingPick(tuple(rng.choice(by_family[f]) for f in families), thin=False)
    if len(usable) < SITTING_PROBLEMS:
        return None
    ranked = sorted(
        usable, key=lambda p: (p.card_id in seen.last_day, seen.staleness(p), p.problem_id)
    )
    picked: list[ProblemSpec] = []
    families_used: set[str] = set()
    for p in ranked:
        if len(picked) < SITTING_PROBLEMS and (p.family or p.card_id) not in families_used:
            picked.append(p)
            families_used.add(p.family or p.card_id)
    for p in ranked:  # a tier whose problems share one family
        if len(picked) < SITTING_PROBLEMS and p not in picked:
            picked.append(p)
    return SittingPick(tuple(picked), thin=True)


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
