"""Due skills for a study day, and the scheduled load ahead (inputs to the daily queue).

The queue builder (fair share, triage, ordering) is a later milestone; this module only
answers "what is due, how overdue, how recallable" from live due dates (ENG-1).

Live due dates follow the goal in force, so a goal that raises retention moves dues
earlier at once (I2, ADR-0014). Overdue time and QUE-4 escalation are therefore measured
from the due date cached when the skill was last graded (`SkillState.due_at`), never from
the live one, and a due date that moved into the past counts from today. `goal_change`
previews how many skills a new goal makes due and spreads them over the following days
with the load balancer's weights, like Anki's opt-in "reschedule cards on change".
"""

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.lifecycle import (
    RELEARNING,
    balance_weight,
    due_day,
    due_note,
    easy_day,
    easy_days_modifiers,
    interval_of,
    memory_of,
    weighted_index,
    with_adjust,
)
from core.model import SkillState

SPREAD_DAYS = 7  # a goal change spreads newly due skills over today and the next 6 days

DueReason = Literal["review", "relearn"]


@dataclass(frozen=True, slots=True, kw_only=True)
class DueSkill:
    skill_id: str
    due_day: date
    days_overdue: int
    recall: float  # predicted recall at the day's review moment
    reason: DueReason
    escalated: bool  # QUE-4: waited longer than the longest wait; moves up to order 4
    note: str | None = None  # why an adjusted due date moved (ENG-6 pull-forward, ...)


def due_skills(
    states: Iterable[SkillState],
    day: date,
    *,
    retention_of: Callable[[str], float],
    adapter: FsrsAdapter,
    days: StudyDays,
    longest_wait_days: int = 7,
    active: Callable[[str], bool] | None = None,
) -> list[DueSkill]:
    """Skills with an FSRS card due on or before `day`, most overdue first. `active`
    filters out skills in Off sections (they stay in the graph, out of the queue)."""
    moment = days.moment(day)
    out: list[DueSkill] = []
    for state in states:
        if active is not None and not active(state.skill_id):
            continue
        memory = memory_of(state)
        retention = retention_of(state.skill_id)
        due = due_day(state, retention, adapter, days)
        if memory is None or due is None or due > day:
            continue
        due = effective_due(state, due, day, days)
        overdue = (day - due).days
        recall = adapter.retrievability(memory, moment)
        out.append(
            DueSkill(
                skill_id=state.skill_id,
                due_day=due,
                days_overdue=overdue,
                recall=recall,
                reason="relearn" if state.fsrs_state == RELEARNING else "review",
                escalated=escalated(
                    state, day, recall, retention, adapter, days, longest_wait_days
                ),
                note=due_note(state),
            )
        )
    out.sort(key=lambda d: (-d.days_overdue, d.recall, d.skill_id))
    return out


def cached_due(state: SkillState, days: StudyDays) -> date | None:
    """The due day cached when the skill was last graded (None for rows without one)."""
    return None if state.due_at is None else days.day_of(state.due_at)


def effective_due(state: SkillState, live: date, today: date, days: StudyDays) -> date:
    """The live due day, except that one which moved earlier than the cached one (a goal
    that raised retention) counts from the cached day, clamped to today: a due date that
    moved into the past is due today, not overdue."""
    cached = cached_due(state, days)
    if cached is None or cached <= live:
        return live
    return max(live, min(cached, today))


def escalated(
    state: SkillState,
    day: date,
    recall: float,
    retention: float,
    adapter: FsrsAdapter,
    days: StudyDays,
    longest_wait_days: int,
) -> bool:
    """QUE-4 on the due day cached at review time, never the live one (I2): a goal change
    alone never escalates. Rows without a cached due day use an R deficit instead: recall
    below what the skill would have after waiting the longest wait past its live due."""
    cached = cached_due(state, days)
    if cached is not None:
        return (day - cached).days > longest_wait_days
    stability = state.stability or 0.0
    wait = interval_of(state, retention, adapter) + longest_wait_days
    return recall < adapter.retrievability_after(float(wait), stability)


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalChange:
    """What a new goal does to the queue: the skills it makes due (their live due day
    moves to today or earlier) and the day each is spread to; `states` carry the spread
    as a due-date adjustment ("not before" its day, keyed by its last review)."""

    newly_due: tuple[str, ...] = ()
    spread: Mapping[str, date] = field(default_factory=dict)
    states: tuple[SkillState, ...] = ()

    @property
    def message(self) -> str:
        n = len(self.newly_due)
        if n == 0:
            return "This changes no due dates today."
        return f"This makes {n} skill{'s' if n != 1 else ''} due."

    def per_day(self) -> dict[date, int]:
        return dict(sorted(Counter(self.spread.values()).items()))


def goal_change(
    states: Iterable[SkillState],
    today: date,
    *,
    old_retention: Callable[[str], float],
    new_retention: Callable[[str], float],
    adapter: FsrsAdapter,
    days: StudyDays,
    load: Mapping[date, int] | None = None,
    spread_days: int = SPREAD_DAYS,
    easy_days: Mapping[str, float] | None = None,
    adapter_of: Callable[[str], FsrsAdapter] | None = None,
) -> GoalChange:
    """I2: preview a goal change and spread the skills it makes due. A skill counts when
    its live due day under the new retention is today or earlier while under the old one
    it was later. Each goes to a day in [today, today + spread_days) chosen with the load
    balancer's weights, (1/n)^2.15 * (1/interval)^3 (1 for an empty day), counting the
    skills placed before it; the draw is seeded by the skill and its last review.
    `adapter_of`: each skill's own parameter set (decision 6); None: `adapter` for all."""
    counts: Counter[date] = Counter(load or {})
    newly: list[SkillState] = []
    for state in states:
        model = adapter if adapter_of is None else adapter_of(state.skill_id)
        old = due_day(state, old_retention(state.skill_id), model, days)
        new = due_day(state, new_retention(state.skill_id), model, days)
        if old is None or new is None or state.fsrs_state == RELEARNING:
            continue
        if new <= today < old:
            newly.append(state)
    newly.sort(key=lambda s: (s.last_review_at or 0, s.skill_id))
    spread: dict[str, date] = {}
    out: list[SkillState] = []
    for state in newly:
        last = days.day_of(state.last_review_at or 0)
        options = [today + timedelta(days=i) for i in range(max(1, spread_days))]
        easy = easy_days_modifiers(
            [easy_day(easy_days, d.weekday()) for d in options], [counts[d] for d in options]
        )
        weights = [
            balance_weight(counts[d], max(1, (d - last).days), m)
            for d, m in zip(options, easy, strict=True)
        ]
        chosen = options[weighted_index(weights, f"goal|{state.skill_id}|{state.last_review_at}")]
        counts[chosen] += 1
        spread[state.skill_id] = chosen
        out.append(
            with_adjust(
                state, not_before=chosen, reason="Spread over a few days after a goal change"
            )
        )
    return GoalChange(newly_due=tuple(s.skill_id for s in newly), spread=spread, states=tuple(out))


def scheduled_load(
    states: Iterable[SkillState],
    start: date,
    n_days: int,
    *,
    retention_of: Callable[[str], float],
    adapter: FsrsAdapter,
    days: StudyDays,
    adapter_of: Callable[[str], FsrsAdapter] | None = None,
) -> dict[date, int]:
    """Reviews already scheduled per day for the next n days (overdue ones count today).
    `adapter_of`: each skill's own parameter set (decision 6); None: `adapter` for all."""
    load: Counter[date] = Counter({start + timedelta(days=i): 0 for i in range(n_days)})
    end = start + timedelta(days=n_days)
    for state in states:
        model = adapter if adapter_of is None else adapter_of(state.skill_id)
        due = due_day(state, retention_of(state.skill_id), model, days)
        if due is None:
            continue
        due = max(due, start)
        if due < end:
            load[due] += 1
    return dict(sorted(load.items()))


def new_skill_room(
    projected: Mapping[date, int],
    *,
    daily_count: int,
    per_skill: int = 4,
    early_reviews: int = 1,
    max_new: int = 4,
) -> int:
    """QUE-5: how many new skills fit today while the projected 7-day average load stays at
    or under the daily count. It assumes the same number is introduced every day of the
    window: each new skill costs its learning block (`per_skill` problems, three to five)
    plus about one early review inside the week."""
    loads = list(projected.values())[:7]
    average = sum(loads) / len(loads) if loads else 0.0
    room = 0
    while room < max_new and average + (room + 1) * (per_skill + early_reviews) <= daily_count:
        room += 1
    return room
