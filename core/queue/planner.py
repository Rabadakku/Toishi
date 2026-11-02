"""The daily plan (QUE-1..5, QUE-11..13) and the re-plan after every answer. Pure.

`build_plan` fills N problem slots: each course's quota (share.split) is filled from its
own triage list (triage applies inside each course's share); slots no course has due work
for go to new skills while QUE-5's projected load allows, Learning-now sections first, and
only for courses whose due work is under one day's quota (QUE-13). An optional minutes cap
then cuts the lowest-priority units. Flashcards (up to M) sit between problems in groups of
up to five. Candidates that did not fit stay on the bench for refills.

`rebalance` keeps a plan at N slots after a re-plan inserted or dropped items: inserted
checks and reinforcements take the slots of the lowest-priority pending items (the same
course's first), freed slots are refilled from the bench, and the pending tail is ordered
again after what has been served.
"""

import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace

from core.engine import Catalog, new_skill_room
from core.queue.config import BENCH_FACTOR, FLASHCARD, FLASHCARD_GROUP, MINUTE_MS, NEW
from core.queue.items import (
    Mode,
    Plan,
    PlanItem,
    Unit,
    priority_order,
    unit_priority,
    unit_slots,
    units_of,
    why,
)
from core.queue.order import order_items
from core.queue.share import CourseDemand, goal_weight, split, urgency
from core.queue.snapshot import DAILY_MODES, Snapshot
from core.queue.triage import TriagePolicy, candidates, mark_stretch, policy_for


def confusable_map(catalog: Catalog) -> dict[str, frozenset[str]]:
    pairs: dict[str, set[str]] = {}
    for skill in catalog.skills.values():
        for other in skill.confusable:
            pairs.setdefault(skill.id, set()).add(other)
            pairs.setdefault(other, set()).add(skill.id)
    return {k: frozenset(v) for k, v in pairs.items()}


def _take(units: Sequence[Unit], quota: int, *, min_block: int) -> tuple[list[Unit], list[Unit]]:
    """Fill `quota` slots in priority order; a learning block may shrink to fit (it grows
    again in re-plans while the skill is still being learned)."""
    chosen: list[Unit] = []
    rest: list[Unit] = []
    left = quota
    for unit in units:
        slots = unit_slots(unit)
        if slots <= left:
            chosen.append(unit)
            left -= slots
        elif unit[0].block is not None and left >= min(min_block, slots):
            chosen.append(_shrink(unit, left))
            left = 0
        else:
            rest.append(unit)
    return chosen, rest


def _shrink(unit: Unit, slots: int) -> Unit:
    out: list[PlanItem] = []
    for item in unit:
        if item.slots and slots <= 0:
            continue
        out.append(item)
        slots -= item.slots
    return tuple(out)


def _course(unit: Unit) -> str:
    return unit[-1].course_id or ""


def build_plan(
    snap: Snapshot,
    *,
    mode: Mode = "daily",
    lighter: bool = False,
    n: int | None = None,
    policy: TriagePolicy | None = None,
    include_new: bool = True,
    flashcards: bool | None = None,
) -> Plan:
    settings = snap.settings
    policy = policy or policy_for(settings.policy)
    daily = mode in DAILY_MODES
    lighter = lighter or mode == "lighter"
    day = snap.day.isoformat()
    if daily and snap.vacation is not None and snap.vacation.covers(snap.day):
        return Plan(day=day, mode=mode, policy=policy.name, info={"vacation": True})
    n_total = settings.n if n is None else n
    done_today = sum(snap.done_today.values()) if daily else 0
    n_eff = max(0, n_total - done_today)

    units = candidates(snap, lighter=lighter, policy=policy, include_new=include_new)
    due_units = [u for u in units if u[0].order < NEW]
    new_units = [u for u in units if u[0].order == NEW]
    due_slots: Counter[str] = Counter()
    by_course: dict[str, list[Unit]] = {}
    for u in due_units:
        due_slots[_course(u)] += unit_slots(u)
        by_course.setdefault(_course(u), []).append(u)
    courses = sorted(set(due_slots) | set(snap.courses) | {_course(u) for u in new_units})

    def demand(course: str, due: int) -> CourseDemand:
        return CourseDemand(
            course_id=course,
            goal=goal_weight(snap.goals.get(course), snap.day),
            urgency=urgency(snap.next_exam_days.get(course)),
            due=due,
            carry=snap.carry.get(course, 0) if daily else 0,
        )

    share = split(
        [demand(c, due_slots[c]) for c in courses],
        n_eff,
        min_problems=settings.min_per_course,
        min_fraction=settings.min_fraction,
    )
    selected: list[Unit] = []
    bench: list[Unit] = []
    used: Counter[str] = Counter()
    for course in courses:
        chosen, rest = _take(
            by_course.get(course, []),
            share.quotas.get(course, 0),
            min_block=settings.correct_in_a_row,
        )
        selected += chosen
        bench += rest
        used[course] = sum(unit_slots(u) for u in chosen)

    # New skills in the slots due work left free (QUE-5, QUE-13).
    leftover = n_eff - sum(used.values())
    block = settings.correct_in_a_row + 1
    room = 0
    if include_new and not lighter and daily:
        room = new_skill_room(
            snap.projected_load,
            daily_count=n_total,
            per_skill=block,
            max_new=settings.new_per_day,
        )
        room = max(0, room - snap.introduced_today)
    elif include_new and not lighter:
        room = settings.new_per_day
    nominal = split([demand(c, n_eff) for c in courses], n_eff).quotas
    open_courses = {c for c in courses if due_slots[c] < max(1, nominal.get(c, 0))}
    new_by_course: dict[str, list[Unit]] = {}
    for u in new_units:
        if _course(u) in open_courses:
            new_by_course.setdefault(_course(u), []).append(u)
        else:
            bench.append(u)
    new_taken: Counter[str] = Counter()
    while room > 0 and leftover > 0:
        options = [c for c, us in new_by_course.items() if us]
        if not options:
            break
        course = min(
            options,
            key=lambda c: (
                new_by_course[c][0][0].rank >= 1e7,  # Learning-now sections first
                new_taken[c] / max(share.weights.get(c, 1.0), 1e-9),
                c,
            ),
        )
        unit = new_by_course[course].pop(0)
        slots = unit_slots(unit)
        if slots > leftover:
            if leftover < settings.correct_in_a_row:
                new_by_course[course].insert(0, unit)
                break
            unit = _shrink(unit, leftover)
            slots = leftover
        selected.append(unit)
        leftover -= slots
        used[course] += slots
        new_taken[course] += 1
        room -= 1
    for us in new_by_course.values():
        bench += us

    # Optional minutes cap (QUE-3): cut the lowest-priority units.
    capped = False
    if settings.minutes_cap and daily:
        limit = settings.minutes_cap * MINUTE_MS
        selected = priority_order(selected)
        while len(selected) > 1 and sum(i.est_ms for u in selected for i in u) > limit:
            victim = selected.pop()
            bench.append(victim)
            used[_course(victim)] -= unit_slots(victim)
            capped = True

    selected = mark_stretch(snap, priority_order(selected))
    quotas = {c: used[c] for c in courses if used[c] > 0}
    items = order_items(
        [], [i for u in selected for i in u], shares=quotas, confusable=confusable_map(snap.catalog)
    )

    # Flashcards (I5, like Anki's limits): the day's limit M minus the flashcards already
    # done today, and new ones only up to daily.new_flashcards minus today's new ones.
    flash: list[PlanItem] = []
    wanted = flashcards if flashcards is not None else daily
    limit_fc = max(0, settings.flashcards - snap.flashcards_done_today) if wanted else 0
    new_left = max(0, settings.new_flashcards - snap.new_flashcards_done_today)
    for card_id, card_ord, skill in snap.flashcards_due:
        if len(flash) >= limit_fc:
            break
        if (card_id, card_ord) in snap.flashcards_new:
            if new_left <= 0:
                continue
            new_left -= 1
        flash.append(flashcard_item(snap, card_id, card_ord, skill))
    items = place_flashcards(items, flash)

    bench_units = priority_order(bench)[: max(BENCH_FACTOR * max(n_total, 1), 10)]
    backlog = sum(1 for u in bench if u[0].order < NEW)
    est = sum(i.est_ms for i in items)
    return Plan(
        day=day,
        mode=mode,
        policy=policy.name,
        n=sum(unit_slots(u) for u in selected) if capped else n_eff,
        items=tuple(items),
        bench=tuple(i for u in bench_units for i in u),
        quotas=quotas,
        shares={c: float(q) for c, q in quotas.items()},
        lighter=lighter,
        flashcards=max(0, limit_fc - len(flash)),
        info={
            "need": sum(due_slots.values()),
            "backlog": backlog,
            "free": n_eff - sum(used.values()),
            "count": n_total,
            "done_before": done_today,
            "new_room": room,
            "new_planned": sum(new_taken.values()),
            "share": dict(share.quotas),
            "carried": dict(share.carried),
            "est_ms": est,
            "capped": capped,
            "vacation": False,
        },
    )


def flashcard_item(
    snap: Snapshot, card_id: str, card_ord: int, skill: str | None, *, refresher: bool = False
) -> PlanItem:
    return PlanItem(
        key=f"fc:{card_id}:{card_ord}" + (":r" if refresher else ""),
        kind="flashcard",
        skill_id=skill,
        course_id=snap.course_of(skill) or "",
        section_id=snap.section_of(skill),
        order=FLASHCARD,
        tag="review",
        label="Flashcard",
        why=why("flashcard.refresher" if refresher else "flashcard"),
        purpose="review",
        tier_hint=1.0,
        est_ms=snap.times.item_ms("flashcard", skill, 1),
        card_id=card_id,
        card_ord=card_ord,
        inserted=refresher,
    )


def place_flashcards(
    ordered: Sequence[PlanItem],
    flash: Sequence[PlanItem],
    *,
    refreshers: Sequence[PlanItem] = (),
) -> list[PlanItem]:
    """Refreshers first (right after the miss's solution); the rest in groups of up to five
    spread evenly between problems, never inside a learning block."""
    out = list(refreshers)
    groups = [list(flash[i : i + FLASHCARD_GROUP]) for i in range(0, len(flash), FLASHCARD_GROUP)]
    if not groups:
        return out + list(ordered)
    p = len(ordered)
    cuts = [round((g + 1) * p / (len(groups) + 1)) for g in range(len(groups))]
    gi = 0
    for i, item in enumerate(ordered):
        out.append(item)
        nxt = ordered[i + 1] if i + 1 < len(ordered) else None
        inside_block = nxt is not None and item.block is not None and nxt.block == item.block
        while gi < len(groups) and cuts[gi] <= i + 1 and not inside_block:
            out += groups[gi]
            gi += 1
    for g in groups[gi:]:
        out += g
    return out


def rebalance(
    plan: Plan,
    *,
    inserted: Sequence[PlanItem] = (),
    drop: Iterable[str] = (),
    prefer_course: str | None = None,
    confusable: Mapping[str, frozenset[str]] | None = None,
    refill: bool = True,
) -> Plan:
    """Keep the plan at `plan.n` problem slots after inserting or dropping items."""
    drop_keys = set(drop)
    done = plan.done
    pending = [i for i in plan.pending if i.key not in drop_keys]
    refreshers = [i for i in inserted if i.kind == "flashcard" and i.anchor is None]
    flash = [i for i in pending if i.kind == "flashcard" and i.anchor is None]
    reshows = [i for i in (*pending, *inserted) if i.kind == "flashcard" and i.anchor is not None]
    probs = [i for i in pending if i.kind != "flashcard"] + [
        i for i in inserted if i.kind != "flashcard"
    ]
    units = units_of(probs)
    started = {i.block for i in done if i.block is not None}
    new_keys = {i.key for i in inserted}
    bench = units_of([i for i in plan.bench if i.key not in drop_keys])
    used = sum(i.slots for i in done if i.status == "done") + sum(unit_slots(u) for u in units)

    def protected(u: Unit) -> bool:
        return any(i.key in new_keys or i.inserted for i in u) or u[0].block in started

    while used > plan.n:
        victims = [u for u in units if not protected(u)]
        if not victims:
            break
        pool = [u for u in victims if _course(u) == prefer_course] or victims
        victim = max(pool, key=unit_priority)
        units.remove(victim)
        used -= unit_slots(victim)
        bench.append(victim)
    bench = priority_order(bench)
    planned_skills = {i.skill_id for u in units for i in u} | {
        i.skill_id for i in done if i.status == "done"
    }
    while refill and used < plan.n:
        room = plan.n - used
        fits = [
            u
            for u in bench
            if 0 < unit_slots(u) <= room
            and u[0].order < NEW  # new skills only come in through the day's plan (QUE-5)
            and u[0].skill_id not in planned_skills
        ]
        if not fits:
            break
        pick = min(fits, key=lambda u: (u[0].order, _course(u) != prefer_course, u[0].rank))
        bench.remove(pick)
        units.append(pick)
        used += unit_slots(pick)
        planned_skills |= {i.skill_id for i in pick}
    shares = plan.shares or {c: float(q) for c, q in plan.quotas.items()}
    ordered = order_items(
        done,
        [i for u in units for i in u],
        shares=shares,
        confusable=confusable,
        warmup=not any(i.status == "done" for i in done),
    )
    tail = place_flashcards(ordered, flash, refreshers=refreshers)
    for item in reshows:  # I5: a missed flashcard at least `gap` items after its miss
        keys = [i.key for i in done if i.status != "skipped"]
        after = len(keys) - 1 - keys.index(item.anchor) if item.anchor in keys else 0
        tail.insert(min(max(0, item.gap - after), len(tail)), item)
    return replace(plan, items=(*done, *tail), bench=tuple(i for u in bench for i in u))


def projected_minutes(items: Iterable[PlanItem]) -> int:
    return math.ceil(sum(i.est_ms for i in items if i.pending) / MINUTE_MS)
