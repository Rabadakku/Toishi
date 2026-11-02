"""Standard times (student-model spec 2.4): the minutes a well-prepared student at a top
school needs for a problem; the student model's pace target is measured against them.

    T* = time                                    when the card (or part) sets `time:`
    T* = 0.5 + m * steps + m * max(0, tier - 3)  otherwise

`steps` is the number of ### Solution steps and `m` the course's minutes per step (the
skills file's `pace-minutes-per-step`, 1.5 by default). A card with no solution steps
takes its tier's default instead (TIER_DEFAULTS), which the pack build reports.

A multi-part problem is timed as a whole: without its own `time:`, a card whose parts all
set one takes their sum. A part without `time:` gets an equal share of its card's time.
"""

import math

from core.model import Card, CardPart

READ_MINUTES = 0.5  # reading the problem
BASE_TIER = 3  # a standard exam problem: each tier above it adds a step's minutes
TIER_DEFAULTS: dict[int, float] = {1: 1.0, 2: 2.0, 3: 4.0, 4: 6.0, 5: 8.0}  # no steps to count
TIMED_KINDS = frozenset({"problem", "find-error", "method"})  # graded through a skill


def standard_minutes(
    item: Card | CardPart, minutes_per_step: float, *, card: Card | None = None
) -> float:
    """T* in minutes of a card, or of one of its parts (then pass the part's `card`; it is
    needed only when the part has no `time:` of its own)."""
    if not (math.isfinite(minutes_per_step) and minutes_per_step > 0):
        raise ValueError(f"minutes per step must be a positive number, got {minutes_per_step!r}")
    if item.time_minutes is not None:
        return item.time_minutes
    if isinstance(item, CardPart):
        if card is None or item not in card.parts:
            raise ValueError(f"part {item.label} has no time: pass the card it belongs to")
        return standard_minutes(card, minutes_per_step) / len(card.parts)
    times = [p.time_minutes for p in item.parts]
    if times and all(t is not None for t in times):
        return math.fsum(t for t in times if t is not None)
    steps = len(item.solution)
    if not steps:
        return TIER_DEFAULTS[item.tier]
    m = minutes_per_step
    return READ_MINUTES + m * steps + m * max(0, item.tier - BASE_TIER)


def uses_tier_default(card: Card) -> bool:
    """The card's standard time is its tier's default: no `time:` on it (or on every one
    of its parts) and no solution steps to count."""
    parts_timed = bool(card.parts) and all(p.time_minutes is not None for p in card.parts)
    return card.time_minutes is None and not parts_timed and not card.solution
