"""How the session is ordered (spec, "How the session is ordered"). Pure functions.

`order_items` places the pending units after the items already served, one at a time:

- hard: a learning block stays one unit (worked example, then its problems) and never
  opens the session; an anchored item (reinforcement, check) waits at least `gap` items
  after its miss; the same skill never comes back to back, with a look-ahead that keeps
  that possible for the rest of the session whenever the counts allow it;
- the warm-up: the session opens with two or three quick reviews when there are some;
- courses are interleaved by their shares (the course furthest behind its share goes
  next), so stopping partway still serves each fairly;
- inside a course: triage priority first, then soft rules: same section at least two
  apart, confusable skills one to three apart, harder and easier alternating.

Hard rules relax only when nothing else can go next (the anchor rule never relaxes: an
anchored item that can't reach its distance goes last).
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from core.queue.config import (
    CONFUSABLE_MAX_GAP,
    FLASHCARD,
    HARD_TIER,
    PREREQ,
    QUICK_TIER,
    WARMUP_MAX,
    WARMUP_MIN,
    WARMUP_PLAN_MIN,
)
from core.queue.items import PlanItem, Unit, unit_priority, unit_slots, units_of

SECTION_PENALTY = 3.0
DIFFICULTY_PENALTY = 1.5
CONFUSABLE_BONUS = 10.0
ANCHOR_BONUS = 50.0


@dataclass(slots=True)
class _U:
    items: Unit
    skill: str | None
    section: str | None
    course: str
    anchor: str | None
    gap: int
    block: bool
    quick: bool
    hard: bool
    index: int  # priority position inside its course


def is_quick(unit: Unit) -> bool:
    """A quick review for the warm-up: one plain review problem at an easy expected tier."""
    if len(unit) != 1:
        return False
    item = unit[0]
    return (
        item.kind == "problem"
        and item.order >= PREREQ
        and item.anchor is None
        and not item.stretch
        and item.tag in ("review", "exam-prep")
        and item.tier_hint <= QUICK_TIER
    )


def _wrap(units: Sequence[Unit]) -> list[_U]:
    by_course: dict[str, list[Unit]] = {}
    for u in units:
        by_course.setdefault(u[-1].course_id or "", []).append(u)
    index: dict[str, int] = {}
    for group in by_course.values():
        for i, u in enumerate(sorted(group, key=unit_priority)):
            index[u[0].key] = i
    out = []
    for u in units:
        last = u[-1]
        out.append(
            _U(
                items=u,
                skill=last.skill_id,
                section=last.section_id,
                course=last.course_id or "",
                anchor=next((i.anchor for i in u if i.anchor), None),
                gap=max(i.gap for i in u),
                block=last.block is not None,
                quick=is_quick(u),
                hard=last.block is not None or last.tier_hint >= HARD_TIER,
                index=index[u[0].key],
            )
        )
    return out


def _feasible(counts: Counter[str], last: str | None) -> bool:
    """Can the remaining units (counted per skill) follow `last` without a repeat?"""
    total = sum(counts.values())
    return all(c <= total - c + (0 if s == last else 1) for s, c in counts.items())


def warmup_length(units: Sequence[Unit], plan_size: int) -> int:
    quick = sum(1 for u in units if is_quick(u))
    if quick < WARMUP_MIN:
        return quick
    return WARMUP_MAX if quick >= WARMUP_MAX and plan_size >= WARMUP_PLAN_MIN else WARMUP_MIN


def order_items(
    done: Sequence[PlanItem],
    pending: Sequence[PlanItem],
    *,
    shares: Mapping[str, float],
    confusable: Mapping[str, frozenset[str]] | None = None,
    warmup: bool | None = None,
) -> list[PlanItem]:
    """The pending items (flashcards excluded) in serving order after `done`."""
    confusable = confusable or {}
    seq = [i for i in done if i.kind != "flashcard" and i.status != "skipped"]
    units = _wrap(units_of([i for i in pending if i.order != FLASHCARD]))
    if warmup is None:
        warmup = not seq
    warm = warmup_length([u.items for u in units], sum(len(u.items) for u in units))
    pos_of = {item.key: i for i, item in enumerate(seq)}
    served: Counter[str] = Counter()
    for item in seq:
        served[item.course_id or ""] += item.slots
    total_share = sum(shares.values()) or 1.0
    out: list[PlanItem] = []

    while units:
        open_block = seq[-1].block if seq else None
        started = [u for u in units if open_block is not None and u.items[0].block == open_block]
        if started:  # a learning block runs as one unit, even across re-plans
            best = started[0]
            units.remove(best)
            for item in best.items:
                pos_of[item.key] = len(seq)
                seq.append(item)
                out.append(item)
            served[best.course] += unit_slots(best.items)
            continue
        checks = _checks(units, seq, pos_of, warm if warmup else 0)
        eligible: list[_U] = []
        for keep in range(len(next(iter(checks.values()))), 0, -1):  # relax the last first
            eligible = [u for u in units if all(checks[id(u)][:keep])]
            if eligible:
                break
        if not eligible:  # only anchored items that can't reach their distance yet
            eligible = list(units)

        # Course: the one furthest behind its share of the slots served so far.
        slots_so_far = sum(served.values())

        def deficit(course: str, slots: int = slots_so_far) -> float:
            share = shares.get(course, 0.0) / total_share
            return share * (slots + 1) - served[course]

        courses = sorted(
            {u.course for u in eligible},
            key=lambda c: (-deficit(c), -shares.get(c, 0.0), c),
        )
        anchored_ready = [u for u in eligible if u.anchor is not None]
        pool = anchored_ready or [u for u in eligible if u.course == courses[0]]
        best = min(pool, key=lambda u: (_score(u, seq, pos_of, confusable), unit_priority(u.items)))
        units.remove(best)
        for item in best.items:
            pos_of[item.key] = len(seq)
            seq.append(item)
            out.append(item)
        served[best.course] += unit_slots(best.items)
    return out


def _checks(
    units: Sequence[_U], seq: Sequence[PlanItem], pos_of: Mapping[str, int], warm: int
) -> dict[int, tuple[bool, ...]]:
    """Per unit, the hard rules in relaxing order: anchor distance, block not first, no
    repeat of the last skill, the rest still arrangeable without repeats, warm-up."""
    pos = len(seq)
    last = seq[-1].skill_id if seq else None
    counts = Counter(_skill_key(u) for u in units)
    others_exist = any(not u.block for u in units)

    waiting = {i.key for w in units for i in w.items}

    def anchor_ok(u: _U) -> bool:
        if u.anchor is None:
            return True
        if u.anchor not in pos_of:  # an anchor still to come goes first (a redo's review)
            return u.anchor not in waiting
        return pos - pos_of[u.anchor] >= u.gap

    want_warm = pos < warm and any(u.quick and anchor_ok(u) for u in units)
    out: dict[int, tuple[bool, ...]] = {}
    for u in units:
        rest = counts.copy()
        rest[_skill_key(u)] -= 1
        rest += Counter()  # drop zero counts
        rules = (
            anchor_ok(u),
            not (u.block and pos == 0 and others_exist),
            not (last is not None and u.skill == last),
            _feasible(rest, u.skill),
        )
        out[id(u)] = (*rules, u.quick) if want_warm else rules
    return out


def _skill_key(u: _U) -> str:
    return u.skill or f"~{id(u)}"


def _score(
    u: _U,
    seq: Sequence[PlanItem],
    pos_of: Mapping[str, int],
    confusable: Mapping[str, frozenset[str]],
) -> float:
    score = float(u.index)
    pos = len(seq)
    if seq:
        last = seq[-1]
        if u.section is not None and u.section == last.section_id and u.skill != last.skill_id:
            score += SECTION_PENALTY
        last_hard = last.block is not None or last.tier_hint >= HARD_TIER
        if u.hard == last_hard:
            score += DIFFICULTY_PENALTY
    partners = confusable.get(u.skill or "", frozenset())
    if partners:
        for back in range(1, min(CONFUSABLE_MAX_GAP, pos) + 1):
            if seq[pos - back].skill_id in partners:
                score -= CONFUSABLE_BONUS
                break
    if u.anchor is not None and u.anchor in pos_of:
        score -= ANCHOR_BONUS
    return score
