"""Placement check (Library) and section-state seeding.

The check halves the unresolved range (spec "Placement check", ADR-0019 item 9; the ALEKS
and Math Academy principle): it asks the unresolved skill that best splits what is left
(the larger of the smaller side: prerequisites a pass would settle, dependents a fail
would). A pass marks the skill's prerequisites provisionally known up to INFER_DEPTH
levels down; deeper ones need a confirming pass on another skill in the same ancestry, so a
single pass never marks a deep chain known. A fail or "I don't know" prunes the skills that
depend on it, and no inference contradicts a failed skill. It stops after 25 questions per
course, or when nothing is unresolved. In simulation (scripts/sim_placement.py's graphs)
the old deepest-first walk seeded 10-15% of known skills against 60-80%.

A skill passed directly starts in review with a provisional stability of about 10 days; one
inferred from a passed descendant, about 2.3 days. Failed and "I don't know" skills stay as
they are. Placement only ever adds knowledge.

Sections marked Covered or Solid without a placement check seed the same way: Covered
like an inferred pass (2.3 days), Solid like a direct pass (10 days).
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal

from core.engine.config import (
    PLACEMENT_DIRECT_STABILITY,
    PLACEMENT_INFERRED_STABILITY,
    PLACEMENT_MAX_QUESTIONS,
)
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.goals import Catalog
from core.engine.lifecycle import Provisional, seed_provisional
from core.model import SkillState

PlacementAnswer = Literal["pass", "fail", "unknown"]

INFER_DEPTH = 2  # a single pass marks prerequisites this many levels down (provisional)


def depth(
    catalog: Catalog, skill_id: str, within: set[str], _memo: dict[str, int] | None = None
) -> int:
    """Longest prerequisite chain under a skill, counting only skills in `within`."""
    memo = {} if _memo is None else _memo
    if skill_id in memo:
        return memo[skill_id]
    memo[skill_id] = 0  # cycle guard
    skill = catalog.skills.get(skill_id)
    below = [r for r in (skill.requires if skill else ()) if r in within]
    memo[skill_id] = 1 + max((depth(catalog, r, within, memo) for r in below), default=-1)
    return memo[skill_id]


def placement_order(catalog: Catalog, skill_ids: Iterable[str]) -> list[str]:
    """Most advanced first: deepest prerequisite chain, then later sections first (the
    tie-break among equally good splits)."""
    wanted = set(skill_ids)
    memo: dict[str, int] = {}

    def key(k: str) -> tuple[int, tuple[int, int], str]:
        skill = catalog.skills.get(k)
        order = catalog.section_order.get(skill.section_id or "", (0, 0)) if skill else (0, 0)
        return (-depth(catalog, k, wanted, memo), (-order[0], -order[1]), k)

    return sorted(wanted, key=key)


def _below(catalog: Catalog, skill_id: str) -> dict[str, int]:
    """Every prerequisite of a skill with its shortest distance (1 = direct)."""
    out: dict[str, int] = {}
    frontier, level = [skill_id], 0
    while frontier:
        level += 1
        nxt: list[str] = []
        for current in frontier:
            skill = catalog.skills.get(current)
            for r in skill.requires if skill is not None else ():
                if r != skill_id and r not in out:
                    out[r] = level
                    nxt.append(r)
        frontier = nxt
    return out


@dataclass(slots=True)
class PlacementWalk:
    """One course's placement check. Can be paused (it is plain data) and re-run."""

    catalog: Catalog
    order: list[str]
    answers: dict[str, PlacementAnswer] = field(default_factory=dict)
    max_questions: int = PLACEMENT_MAX_QUESTIONS
    _anc: dict[str, dict[str, int]] = field(default_factory=dict)
    _desc: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def start(cls, catalog: Catalog, skill_ids: Iterable[str]) -> PlacementWalk:
        walk = cls(catalog=catalog, order=placement_order(catalog, skill_ids))
        for k in walk.order:
            walk._anc[k] = _below(catalog, k)
        for k, below in walk._anc.items():
            for a in below:
                walk._desc.setdefault(a, set()).add(k)
        return walk

    def anc(self, skill_id: str) -> dict[str, int]:
        if skill_id not in self._anc:
            self._anc[skill_id] = _below(self.catalog, skill_id)
        return self._anc[skill_id]

    @property
    def asked(self) -> int:
        return len(self.answers)

    @property
    def pruned(self) -> set[str]:
        """Failed and "I don't know" skills and every skill in the check depending on one."""
        out: set[str] = set()
        for k, v in self.answers.items():
            if v != "pass":
                out.add(k)
                out |= self._desc.get(k, set())
        return out - {k for k, v in self.answers.items() if v == "pass"}

    @property
    def inferred(self) -> set[str]:
        """Prerequisites inferred known from passes: within INFER_DEPTH levels of a pass, or
        any depth once another pass in the same ancestry confirms the chain; never a
        pruned skill."""
        passed = [k for k, v in self.answers.items() if v == "pass"]
        out: set[str] = set()
        for k in passed:
            below = self.anc(k)
            confirmed = any(other in below for other in passed if other != k)
            out |= {a for a, d in below.items() if confirmed or d <= INFER_DEPTH}
        return out - self.pruned - set(passed)

    def unresolved(self) -> list[str]:
        settled = set(self.answers) | self.inferred | self.pruned
        return [k for k in self.order if k not in settled]

    def next_skill(self) -> str | None:
        if self.asked >= self.max_questions:
            return None
        left = self.unresolved()
        if not left:
            return None
        open_ = set(left)
        best: str | None = None
        best_key: tuple[int, int] | None = None
        for k in left:  # `order` breaks ties: the most advanced first
            gain_pass = 1 + len(open_.intersection(self.anc(k)))
            gain_fail = 1 + len(open_ & self._desc.get(k, set()))
            key = (min(gain_pass, gain_fail), gain_pass + gain_fail)
            if best_key is None or key > best_key:
                best, best_key = k, key
        return best

    def answer(self, skill_id: str, result: PlacementAnswer) -> None:
        self.answers[skill_id] = result

    def seeds(self) -> dict[str, Provisional]:
        direct = {k for k, v in self.answers.items() if v == "pass"}
        out: dict[str, Provisional] = dict.fromkeys(direct, "direct")
        for k in self.inferred - direct:
            if self.answers.get(k) not in ("fail", "unknown"):
                out[k] = "inferred"
        return out


STABILITY: Mapping[Provisional, float] = {
    "direct": PLACEMENT_DIRECT_STABILITY,
    "inferred": PLACEMENT_INFERRED_STABILITY,
    "solid": PLACEMENT_DIRECT_STABILITY,
    "covered": PLACEMENT_INFERRED_STABILITY,
}


def apply_seeds(
    states: Mapping[str, SkillState],
    seeds: Mapping[str, Provisional],
    *,
    at_ms: int,
    adapter: FsrsAdapter,
    adapter_of: Callable[[str], FsrsAdapter] | None = None,
) -> list[SkillState]:
    """The rows to write for a placement result or a Covered/Solid section; skills whose
    existing card is already as strong are left out (placement never takes progress)."""
    out: list[SkillState] = []
    for skill_id, kind in sorted(seeds.items()):
        seeded = seed_provisional(
            states.get(skill_id),
            skill_id,
            kind=kind,
            stability=STABILITY[kind],
            at_ms=at_ms,
            adapter=adapter if adapter_of is None else adapter_of(skill_id),
        )
        if seeded is not None:
            out.append(seeded)
    return out
