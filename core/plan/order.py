"""The order of the day's items (docs/design/student-model.md v1.1, sections 4.3 and 4.5).

- New material first: each new skill's block (worked example, then its first problems) is
  served whole, a block already in progress before any other.
- Then the mixed set: no two consecutive items of one skill (a new skill's block is the only
  exception), missed-milestone items spread evenly through it (no prefix of the mixed part
  holds more than its overall share), the caller's order kept otherwise.
- Last, the missed-milestone items beyond the 40% share (the caller decides which), so the
  share holds for everything up to the day's last item of other work.
- Every 10th item of the study day is a reference check. When the 10th position falls inside
  a new skill's block, or the check's skill would sit next to its own skill, the check comes
  at the next free boundary of the same ten; a decade's check is never made up later.
- Confusable pairs present in the plan are drawn adjacent or apart with probability 0.5; an
  adjacent pair is glued into one unit (in random order), an apart pair is kept from
  touching where there is a choice. Every draw is logged in `Ordered.confusable`.
- An item that can't be placed without two same-skill items in a row is dropped (and
  reported), never placed: the no-adjacency rule is hard.

The only randomness is `rng`.
"""

import random
from collections import Counter, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise

from core.learner.types import ComponentId
from core.plan.config import CHECK_EVERY, CONFUSABLE_ADJACENT_P, EPS
from core.plan.types import ConfusableDecision, SkillInfo, WorkItem

SEARCH_UNITS = 8  # the last units of a part are ordered by an exact search ...
SEARCH_BUDGET = 20_000  # ... of at most this many steps (else the greedy order stands)


@dataclass(frozen=True, slots=True)
class Ordered:
    items: tuple[WorkItem, ...]
    dropped: tuple[WorkItem, ...]
    confusable: tuple[ConfusableDecision, ...]


@dataclass(frozen=True, slots=True)
class _Unit:
    items: tuple[WorkItem, ...]
    index: int  # the caller's preference: lower first

    @property
    def first(self) -> ComponentId:
        return self.items[0].skill_id

    @property
    def last(self) -> ComponentId:
        return self.items[-1].skill_id

    @property
    def missed(self) -> bool:
        return any(i.missed for i in self.items)


def confusable_pairs(skills: Iterable[SkillInfo]) -> list[tuple[ComponentId, ComponentId]]:
    """Unordered confusable pairs from the skills' `confusable` lists, sorted."""
    pairs: set[tuple[ComponentId, ComponentId]] = set()
    for s in skills:
        for other in s.confusable:
            if other != s.skill_id:
                a, b = sorted((s.skill_id, other))
                pairs.add((a, b))
    return sorted(pairs)


def _feasible(counts: Counter[ComponentId], n: int, last: ComponentId | None) -> bool:
    """Can n items with these per-skill counts follow `last` with no two of a skill in a
    row? (Exact for single items: a skill fills at most every other place.)"""
    for skill, c in counts.items():
        limit = n // 2 if skill == last else (n + 1) // 2
        if c > limit:
            return False
    return True


class _Sequencer:
    def __init__(self, served: Sequence[WorkItem], checks: Sequence[WorkItem]) -> None:
        self.served_n = len(served)
        self.seq: list[WorkItem] = []
        self.checks = deque(checks)
        self.check_at = [i + 1 for i, it in enumerate(served) if it.role == "check"]
        self.last: ComponentId | None = served[-1].skill_id if served else None

    @property
    def next_pos(self) -> int:
        return self.served_n + len(self.seq) + 1

    def pending(self, pos: int) -> bool:
        """Position `pos` still owes its ten's check (one per ten, from the 10th on)."""
        decade = pos // CHECK_EVERY
        if decade < 1:
            return False
        start = decade * CHECK_EVERY
        return not any(start <= q < pos for q in self.check_at)

    def upcoming(self) -> WorkItem | None:
        return self.checks[0] if self.checks else None

    def straddles(self, length: int) -> bool:
        """A unit of `length` items placed now would cover a check slot that isn't its
        first position (the check would then wait for the unit's end)."""
        if not self.checks or length < 2:
            return False
        pos = self.next_pos
        return any(self.pending(q) and q % CHECK_EVERY == 0 for q in range(pos + 1, pos + length))

    def place(self, item: WorkItem) -> None:
        if item.role == "check":
            self.check_at.append(self.next_pos)
        self.seq.append(item)
        self.last = item.skill_id

    def maybe_check(self, before: ComponentId | None = None) -> bool:
        """Place the due check now if its skill touches neither neighbour."""
        check = self.upcoming()
        if check is None or not self.pending(self.next_pos):
            return False
        if check.skill_id in (self.last, before):
            return False
        self.place(self.checks.popleft())
        return True


def order(
    blocks: Sequence[Sequence[WorkItem]],
    mixed: Sequence[WorkItem],
    checks: Sequence[WorkItem] = (),
    *,
    rng: random.Random,
    served: Sequence[WorkItem] = (),
    confusable: Iterable[tuple[ComponentId, ComponentId]] = (),
    continuing: ComponentId | None = None,
    tail: Sequence[WorkItem] = (),
) -> Ordered:
    """Order the rest of the day after the plan items already `served` today.

    `blocks`: new skills' blocks, each in serve order (example first), the blocks in course
    order. `continuing`: the skill whose block is in progress (it goes first and may follow
    its own skill). `mixed`: every other regular item, in the caller's preferred order.
    `tail`: missed-milestone items beyond the 40% share, served after everything else.
    `checks`: reference checks in draw order; as many are used as the day's tens need.
    """
    sq = _Sequencer(served, checks)

    # New material first.
    ordered_blocks = sorted(
        (tuple(b) for b in blocks if b), key=lambda b: 0 if b[0].skill_id == continuing else 1
    )
    for i, block in enumerate(ordered_blocks):
        own = i == 0 and block[0].skill_id == continuing
        if not own:
            sq.maybe_check(before=block[0].skill_id)
        for item in block:
            sq.place(item)

    # The mixed set, then the overflow of missed-milestone work.
    units, decisions = _glue(mixed, confusable, rng)
    apart: dict[ComponentId, set[ComponentId]] = {}
    for a, b, adjacent in decisions:
        if not adjacent:
            apart.setdefault(a, set()).add(b)
            apart.setdefault(b, set()).add(a)
    dropped: list[WorkItem] = []
    _place(sq, units, apart, dropped)
    _place(sq, [_Unit((item,), i) for i, item in enumerate(tail)], apart, dropped)

    seq = sq.seq
    logged = []
    for a, b, adjacent in decisions:
        together = any({x.skill_id, y.skill_id} == {a, b} for x, y in pairwise(seq))
        logged.append(ConfusableDecision(a, b, adjacent, together))
    return Ordered(tuple(seq), tuple(dropped), tuple(logged))


def _place(
    sq: _Sequencer,
    units: Sequence[_Unit],
    apart: dict[ComponentId, set[ComponentId]],
    dropped: list[WorkItem],
) -> None:
    """Place the units one at a time: never the last item's skill next (a unit that can't go
    anywhere is dropped), keeping the rest arrangeable, keeping the next check's skill off
    its neighbours, spreading missed-milestone units evenly (no prefix above their share),
    keeping apart-drawn confusable pairs from touching, the caller's order otherwise."""
    remaining = sorted(units, key=lambda u: u.index)
    counts: Counter[ComponentId] = Counter(i.skill_id for u in remaining for i in u.items)
    left = sum(len(u.items) for u in remaining)
    share = sum(u.missed for u in remaining) / len(remaining) if remaining else 0.0
    placed = placed_missed = 0

    def take(u: _Unit) -> None:
        nonlocal left
        remaining.remove(u)
        counts.subtract(i.skill_id for i in u.items)
        left -= len(u.items)

    while remaining:
        if sq.maybe_check():
            continue
        if len(remaining) <= SEARCH_UNITS:
            found = _search(sq, remaining, strict=True) or _search(sq, remaining, strict=False)
            if found is not None:
                for u in found:
                    sq.maybe_check()
                    for item in u.items:
                        sq.place(item)
                return
        cands = [u for u in remaining if u.first != sq.last]
        if not cands:
            victim = max((u for u in remaining if u.first == sq.last), key=lambda u: u.index)
            take(victim)
            dropped.extend(victim.items)
            continue
        feasible = [
            u
            for u in cands
            if _feasible(counts - Counter(i.skill_id for i in u.items), left - len(u.items), u.last)
        ]
        check = sq.upcoming()
        want_missed = placed_missed + 1 <= share * (placed + 1) + EPS
        keys = {
            id(u): (
                check is not None
                and u.last == check.skill_id
                and sq.pending(sq.next_pos + len(u.items)),
                sq.straddles(len(u.items)),
                0.0 < share < 1.0 and u.missed != want_missed,
                sq.last is not None and u.first in apart.get(sq.last, ()),
                u.index,
            )
            for u in feasible or cands
        }
        best = min(feasible or cands, key=lambda u: keys[id(u)])
        take(best)
        for item in best.items:
            sq.place(item)
        placed += 1
        placed_missed += best.missed


class _Exhausted(Exception):
    pass


def _search(sq: _Sequencer, units: Sequence[_Unit], *, strict: bool) -> list[_Unit] | None:
    """An order of every unit that breaks no adjacency rule, with the checks placed as the
    sequencer will place them; `strict` also keeps every check on its slot (no unit
    covering a slot, no check waiting for a same-skill neighbour). The caller's order is
    tried first, so the result is the earliest such order in it. None: there is none, or
    the search ran out of budget."""
    checks = [c.skill_id for c in sq.checks]
    budget = SEARCH_BUDGET

    def rec(
        pos: int, last: ComponentId | None, ci: int, done: frozenset[int], left: tuple[_Unit, ...]
    ) -> list[_Unit] | None:
        nonlocal budget
        budget -= 1
        if budget < 0:
            raise _Exhausted
        if not left:
            return []
        decade = pos // CHECK_EVERY
        if ci < len(checks) and decade >= 1 and decade not in done:
            if checks[ci] != last:
                return rec(pos + 1, checks[ci], ci + 1, done | {decade}, left)
            if strict:
                return None
        nxt = (decade + 1) * CHECK_EVERY if decade < 1 or decade in done else pos
        for u in left:
            if u.first == last:
                continue
            if strict and ci < len(checks) and pos < nxt < pos + len(u.items):
                continue
            rest = tuple(x for x in left if x is not u)
            found = rec(pos + len(u.items), u.last, ci, done, rest)
            if found is not None:
                return [u, *found]
        return None

    decades = frozenset(q // CHECK_EVERY for q in sq.check_at)
    try:
        return rec(sq.next_pos, sq.last, 0, decades, tuple(sorted(units, key=lambda u: u.index)))
    except _Exhausted:
        return None


def _glue(
    mixed: Sequence[WorkItem],
    confusable: Iterable[tuple[ComponentId, ComponentId]],
    rng: random.Random,
) -> tuple[list[_Unit], list[tuple[ComponentId, ComponentId, bool]]]:
    """Single-item units, with one item of each pair drawn adjacent glued to one of the
    other. Draws one number per present pair, and one more for the glued order."""
    singles = [_Unit((item,), i) for i, item in enumerate(mixed)]
    present = {item.skill_id for item in mixed}
    decisions: list[tuple[ComponentId, ComponentId, bool]] = []
    glued: list[_Unit] = []
    for a, b in sorted(set(confusable)):
        if a not in present or b not in present:
            continue
        adjacent = rng.random() < CONFUSABLE_ADJACENT_P
        decisions.append((a, b, adjacent))
        if not adjacent:
            continue
        ua = next((u for u in singles if u.first == a), None)
        ub = next((u for u in singles if u.first == b), None)
        if ua is None or ub is None:
            continue
        first, second = (ub, ua) if rng.random() < 0.5 else (ua, ub)
        singles.remove(ua)
        singles.remove(ub)
        glued.append(_Unit(first.items + second.items, min(ua.index, ub.index)))
    return singles + glued, decisions
