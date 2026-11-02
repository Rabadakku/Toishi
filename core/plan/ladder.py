"""The stuck ladder (docs/design/wave2-planner.md section 1).

Per skill and study day, `streak` counts the consecutive misses since the skill's last success
today, over its first tries today (any role, a `ServedItem` with `correct` not None). The
skill's next planned item today is then, by the streak:

| streak | next item |
|---|---|
| 0 | as planned |
| 1 | a smaller problem: one tier lower, with the last miss's most-blamed component |
| 2 | a tier 1-2 problem of the prerequisite most blamed over the last two misses |
| 3 | none: the skill is set aside until the next study day |

A ladder item replaces the skill's next planned item and never adds one. A rung-2 item is a
problem of another skill (its `skill_id` is the prerequisite), so it carries
`ladder_for` = the stuck skill: it fills that skill's slot and its outcome is the stuck
skill's next ladder step (`owners`). Without that, the stuck skill's streak could never pass 2
(planner-impl-notes.md, "Wave 2").
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from core.learner.types import ComponentId, Observation
from core.plan.config import LADDER_SET_ASIDE
from core.plan.types import ServedItem, WorkItem


def owners(item: WorkItem) -> tuple[ComponentId, ...]:
    """The skills an item's outcome counts for: its skill, and the stuck skill whose slot a
    ladder item fills."""
    if item.ladder_for is not None and item.ladder_for != item.skill_id:
        return (item.skill_id, item.ladder_for)
    return (item.skill_id,)


def owner(item: WorkItem) -> ComponentId:
    """The skill whose daily slot the item uses."""
    return item.ladder_for or item.skill_id


@dataclass(frozen=True, slots=True)
class Ladder:
    """Today's streaks, from the served items."""

    streak: Mapping[ComponentId, int] = field(default_factory=dict)
    misses: Mapping[ComponentId, tuple[ServedItem, ...]] = field(default_factory=dict)
    set_aside: frozenset[ComponentId] = frozenset()  # reached 3 today: no more items today

    def rung(self, skill: ComponentId) -> int:
        return min(self.streak.get(skill, 0), LADDER_SET_ASIDE)


def read_ladder(served: Sequence[ServedItem]) -> Ladder:
    """Streaks over today's first tries, in serve order; a success resets a skill's streak.
    A skill that reached 3 stays set aside for the day."""
    streak: dict[ComponentId, int] = defaultdict(int)
    misses: dict[ComponentId, list[ServedItem]] = defaultdict(list)
    aside: set[ComponentId] = set()
    for x in served:
        if x.item.problem is None or x.correct is None:
            continue
        for sid in owners(x.item):
            if x.correct:
                streak[sid] = 0
                misses[sid] = []
            else:
                streak[sid] += 1
                misses[sid].append(x)
                if streak[sid] >= LADDER_SET_ASIDE:
                    aside.add(sid)
    return Ladder(
        streak=dict(streak),
        misses={k: tuple(v) for k, v in misses.items()},
        set_aside=frozenset(aside),
    )


def blame_of(x: ServedItem) -> dict[ComponentId, float]:
    return dict(x.update.blame) if x.update is not None else {}


def top_blamed(miss: ServedItem, skill: ComponentId) -> ComponentId:
    """k*: the component with the largest blame b in the miss's update; on a tie the skill
    itself, then the lowest id; the skill itself when the miss carries no blame."""
    blame = blame_of(miss)
    if not blame:
        return skill
    return min(blame, key=lambda k: (-round(blame[k], 12), k != skill, k))


def blamed_prerequisite(
    last_two: Sequence[ServedItem], skill: ComponentId, rank: Mapping[ComponentId, int]
) -> ComponentId | None:
    """The most-blamed component other than the skill itself over the last two misses, their
    blame summed (ties: the earlier in course order, then the lower id). None without one."""
    total: dict[ComponentId, float] = defaultdict(float)
    for x in last_two:
        for k, b in blame_of(x).items():
            if k != skill:
                total[k] += b
    found = [k for k, b in total.items() if b > 0.0]
    if not found:
        return None
    return min(found, key=lambda k: (-round(total[k], 12), rank.get(k, len(rank)), k))


def returning(
    observations: Sequence[Observation], today: date, set_aside_at: int = 2
) -> int | None:
    """The tier a skill returns at after a set-aside (wave 2: "the next study day, ... at the
    tier where it was failing"), from its own first tries (problems whose main skill it is):
    when its last day of first tries before today ended with `set_aside_at` or more misses in
    a row, and it has no first try today yet, the tier of the first miss of that run. The
    observations can't show a rung-2 item (its problem is the prerequisite's), so a
    set-aside day shows as two misses of the skill's own at its end (impl notes)."""
    if any(o.study_day == today for o in observations):
        return None
    earlier = [o for o in observations if o.study_day < today]
    if not earlier:
        return None
    last_day = max(o.study_day for o in earlier)
    run: list[Observation] = []
    for o in sorted(
        (o for o in earlier if o.study_day == last_day), key=lambda o: (o.at_ms, o.attempt_id)
    ):
        if o.correct and not o.aided:
            run = []
        else:
            run.append(o)
    if len(run) < set_aside_at:
        return None
    return run[0].problem.tier
