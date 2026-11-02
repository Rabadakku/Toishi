"""Skill lifecycle: learning phase (ENG-2), lapses (ENG-3), leeches (ENG-9), provisional
seeds from placement or section states, and due dates.

A skill with no FSRS card (fsrs_state None) is in a learning phase: a worked example, then
tier 1-2 problems until `correct_in_a_row` clean answers in a row within
`max_learning_problems`. The phase's (rating, time) pairs are kept in
level_evidence["phase"]; on success the FSRS card is created by replaying them. The phase
fails as soon as the streak can no longer be reached; it restarts the next study day.

fsrs_state 2 is an ordinary review card; 3 means relearning: a lapse whose real relearning
review is the next study day (the same-day reinforcement problem is logged, not rated).

Due dates (ENG-1, ADR-0014): live from stability and the retention in force, placed inside
the fuzz range by Anki's load balancer when the review is graded (intervals up to 90 days;
the chosen day is stored keyed by `last_review_at` in level_evidence["balance"], like
"due_adjust", and holds while the live interval is the one it was chosen for).
"""

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Literal

from core.engine.config import AGAIN
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.model import JsonObject, SkillState

REVIEW, RELEARNING = 2, 3
LearningStep = Literal["example", "problem", "waiting", "none"]
Provisional = Literal["direct", "inferred", "covered", "solid"]
# Evidence keys kept across every transition.
_STICKY = ("leech_base",)
# (rating, at) of the learning block's failed phases, replayed when a phase passes (C3).
FAILED_PHASES = "failed_phases"
ADJUST = "due_adjust"
BALANCE = "balance"
# Anki's load balancer (rslib/src/scheduler/states/load_balancer.rs, 26.09.3).
BALANCE_MAX_INTERVAL = 90
BALANCE_COUNT_POWER = 2.15
BALANCE_INTERVAL_POWER = 3
BALANCE_DAYS = 99  # days of load the balancer looks at (Anki: 90 * 1.1)
# Easy Days (Anki load_balancer.rs EasyDay::load_modifier): a weekday's setting is a load
# percent, 100 Normal, 0 Minimum, anything else Reduced (`impl From<f32> for EasyDay`).
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
EASY_MODIFIER = {"normal": 1.0, "reduced": 0.5, "minimum": 0.0001}


def memory_of(state: SkillState | None) -> Memory | None:
    if (
        state is None
        or state.fsrs_state is None
        or state.stability is None
        or state.difficulty is None
        or state.last_review_at is None
    ):
        return None
    return Memory(state.stability, state.difficulty, state.last_review_at)


def review_on(
    adapter: FsrsAdapter, memory: Memory | None, rating: int, at_ms: int, days: StudyDays
) -> Memory:
    """An FSRS review on whole study days counted on `days` (C4): 0 = the same study day
    (short-term formula), else the days between, as replay and recompute count them."""
    elapsed = 0 if memory is None else days.between(memory.last_review_at, at_ms)
    return adapter.review(memory, rating, at_ms, elapsed_days=elapsed)


def with_memory(state: SkillState, memory: Memory, fsrs_state: int) -> SkillState:
    return replace(
        state,
        fsrs_state=fsrs_state,
        fsrs_step=None,
        stability=memory.stability,
        difficulty=memory.difficulty,
        last_review_at=memory.last_review_at,
    )


def sticky(evidence: JsonObject) -> JsonObject:
    return {k: evidence[k] for k in _STICKY if k in evidence}


def in_learning_phase(state: SkillState | None) -> bool:
    return state is None or state.fsrs_state is None


def provisional_kind(state: SkillState | None) -> str | None:
    raw = None if state is None else state.level_evidence.get("provisional")
    return None if raw is None else str(raw)


# ---------------------------------------------------------------- due dates


def fuzz_key(state: SkillState) -> str:
    return f"{state.skill_id}|{state.last_review_at}"


def due_day(
    state: SkillState | None, retention: float, adapter: FsrsAdapter, days: StudyDays
) -> date | None:
    """The study day a skill is due, computed live from stability and the retention in force
    (ENG-1). Relearning: the next study day (ENG-3). No card: None."""
    memory = memory_of(state)
    if state is None or memory is None:
        return None
    last_day = days.day_of(memory.last_review_at)
    if state.fsrs_state == RELEARNING:
        return adjusted_due(state, last_day + timedelta(days=1))
    return adjusted_due(state, last_day + timedelta(days=interval_of(state, retention, adapter)))


def interval_of(state: SkillState, retention: float, adapter: FsrsAdapter) -> int:
    """Whole days from the last review to the due day: the load balancer's choice when one
    is stored for this review and this live interval, else the hash fuzz."""
    stability = state.stability or 0.0
    base = adapter.interval_days(stability, retention, None)
    chosen = balanced_days(state, base)
    if chosen is not None:
        return chosen
    return adapter.interval_days(stability, retention, fuzz_key(state))


def balanced_days(state: SkillState, base: int) -> int | None:
    raw = state.level_evidence.get(BALANCE)
    if (
        not isinstance(raw, dict)
        or raw.get("last_review_at") != state.last_review_at
        or raw.get("base") != base
    ):
        return None
    return int(raw["days"])


def balance(
    state: SkillState,
    retention: float,
    adapter: FsrsAdapter,
    days: StudyDays,
    load: Mapping[date, int],
    easy_days: Mapping[str, float] | None = None,
) -> SkillState:
    """I3: choose the due day inside the fuzz range with Anki's load-balancer weights,
    (1/n)^2.15 * (1/interval)^3 * the Easy Days modifier (1 for an empty day), drawn with a
    seed from the skill and its last review; stored keyed by `last_review_at`. Intervals
    over 90 days, short ones (no fuzz) and relearning cards keep the hash fuzz. `load`:
    reviews already due per day (this skill not counted); `easy_days`: weekday -> load
    percent (setting queue.easy_days)."""
    memory = memory_of(state)
    if memory is None or state.fsrs_state != REVIEW or not adapter.fuzz:
        return state
    base = adapter.interval_days(memory.stability, retention, None)
    if base < 3 or base > BALANCE_MAX_INTERVAL:
        return state
    low, high = adapter.fuzz_range(base)
    last_day = days.day_of(memory.last_review_at)
    options = list(range(low, high + 1))
    counts = [load.get(last_day + timedelta(days=d), 0) for d in options]
    weekdays = [(last_day + timedelta(days=d)).weekday() for d in options]
    easy = easy_days_modifiers([easy_day(easy_days, w) for w in weekdays], counts)
    weights = [balance_weight(n, d, m) for n, d, m in zip(counts, options, easy, strict=True)]
    chosen = options[weighted_index(weights, f"lb|{fuzz_key(state)}")]
    entry: JsonObject = {"last_review_at": state.last_review_at, "base": base, "days": chosen}
    return replace(state, level_evidence={**state.level_evidence, BALANCE: entry})


def balance_weight(count: int, interval: int, easy: float = 1.0) -> float:
    """Anki's load-balancer weight of a day with `count` reviews due, `interval` days out
    (load_balancer.rs `select_weighted_interval`): 1 for an empty day whatever its Easy Days
    setting, else (1/count)^2.15 * (1/interval)^3 * the Easy Days modifier."""
    if count == 0:
        return 1.0
    return float(
        (1.0 / count) ** BALANCE_COUNT_POWER * (1.0 / interval) ** BALANCE_INTERVAL_POWER * easy
    )


def easy_day(easy_days: Mapping[str, float] | None, weekday: int) -> str:
    """A weekday's Easy Days kind: load percent 100 (or unset) Normal, 0 Minimum, else
    Reduced (Anki `impl From<f32> for EasyDay`: 1.0 Normal, 0.0 Minimum, else Reduced)."""
    percent = float((easy_days or {}).get(WEEKDAYS[weekday], 100))
    return "normal" if percent >= 100 else "minimum" if percent <= 0 else "reduced"


def easy_days_modifiers(kinds: Sequence[str], counts: Sequence[int]) -> list[float]:
    """Anki's `calculate_easy_days_modifiers` (load_balancer.rs, 26.09.3): a Reduced day
    becomes Minimum when its count / 0.5 exceeds the other days' count per remaining load
    share, else Normal; Normal and Minimum days keep their modifier (1, 0.0001)."""
    total = sum(counts)
    shares = sum(EASY_MODIFIER[k] for k in kinds)
    out: list[float] = []
    for kind, count in zip(kinds, counts, strict=True):
        if kind == "reduced":
            others = shares - 0.5
            threshold = (total - count) / others if others else float("inf")
            kind = "minimum" if count / 0.5 > threshold else "normal"
        out.append(EASY_MODIFIER[kind])
    return out


def weighted_index(weights: Sequence[float], key: str) -> int:
    """A weighted draw seeded by `key` (the same key always picks the same index)."""
    digest = hashlib.sha256(key.encode()).digest()
    position = int.from_bytes(digest[:8], "big") / 2**64 * sum(weights)
    for i, w in enumerate(weights):
        position -= w
        if position < 0:
            return i
    return len(weights) - 1


def adjust_of(state: SkillState | None) -> JsonObject | None:
    raw = None if state is None else state.level_evidence.get(ADJUST)
    if not isinstance(raw, dict) or state is None:
        return None
    return raw if raw.get("last_review_at") == state.last_review_at else None


def with_adjust(
    state: SkillState,
    *,
    not_before: date | None = None,
    not_after: date | None = None,
    reason: str,
) -> SkillState:
    """Merge a due-date adjustment into the one in force (tightest bounds win)."""
    current = adjust_of(state) or {}
    nb = current.get("not_before")
    na = current.get("not_after")
    if not_before is not None:
        nb = max(str(nb), not_before.isoformat()) if nb else not_before.isoformat()
    if not_after is not None:
        na = min(str(na), not_after.isoformat()) if na else not_after.isoformat()
    adjust: JsonObject = {"last_review_at": state.last_review_at, "reason": reason}
    if nb:
        adjust["not_before"] = nb
    if na:
        adjust["not_after"] = na
    return replace(state, level_evidence={**state.level_evidence, ADJUST: adjust})


def adjusted_due(state: SkillState, due: date) -> date:
    """Apply a due-date adjustment the diagnosis wrote (level_evidence["due_adjust"]: an
    ENG-6 pull-forward, a forced review, a miss awaiting its check). It holds only until
    the skill's next FSRS review, so it never outlives the memory it was written for."""
    adjust = state.level_evidence.get(ADJUST)
    if not isinstance(adjust, dict) or adjust.get("last_review_at") != state.last_review_at:
        return due
    if adjust.get("not_after") is not None:
        due = min(due, date.fromisoformat(str(adjust["not_after"])))
    if adjust.get("not_before") is not None:
        due = max(due, date.fromisoformat(str(adjust["not_before"])))
    return due


def due_note(state: SkillState | None) -> str | None:
    """The reason text of a due-date adjustment in force ("Why is this here?")."""
    adjust = None if state is None else state.level_evidence.get(ADJUST)
    if not isinstance(adjust, dict) or state is None:
        return None
    if adjust.get("last_review_at") != state.last_review_at:
        return None
    reason = adjust.get("reason")
    return None if reason is None else str(reason)


def due_at(
    state: SkillState, retention: float, adapter: FsrsAdapter, days: StudyDays
) -> int | None:
    day = due_day(state, retention, adapter, days)
    return None if day is None else days.start(day)


# ---------------------------------------------------------------- learning phase (ENG-2)


def start_learning(state: SkillState | None, skill_id: str, at_ms: int) -> SkillState:
    """Introduce a new skill: Level Learning, a worked example first."""
    base = state or SkillState(skill_id=skill_id)
    return replace(
        base,
        introduced_at=base.introduced_at or at_ms,
        level=base.level or "learning",
        level_at=base.level_at or at_ms,
        learning_streak=0,
        learning_count=0,
        level_evidence={**sticky(base.level_evidence), "phase": [], "example_due": True},
    )


def learning_step(state: SkillState | None, today: date) -> LearningStep:
    """What a skill in its learning phase needs next on a study day."""
    if not in_learning_phase(state) or state is None or state.introduced_at is None:
        return "none"
    restart = state.level_evidence.get("restart_on")
    if restart is not None and date.fromisoformat(str(restart)) > today:
        return "waiting"
    if state.level_evidence.get("example_due", True):
        return "example"
    return "problem"


def example_shown(state: SkillState) -> SkillState:
    evidence = {
        k: v for k, v in state.level_evidence.items() if k not in ("example_due", "restart_on")
    }
    return replace(state, level_evidence={**evidence, "example_due": False})


@dataclass(frozen=True, slots=True, kw_only=True)
class LearningResult:
    state: SkillState
    passed: bool = False
    failed: bool = False
    replayed: tuple[tuple[int, int], ...] = ()  # (rating, at) pairs that built the card


def learning_answer(
    state: SkillState,
    *,
    rating: int,
    counts: bool,
    at_ms: int,
    today: date,
    correct_in_a_row: int,
    max_problems: int,
    adapter: FsrsAdapter,
) -> LearningResult:
    """One tier 1-2 problem in the learning phase. `counts`: clean (first attempt, no
    hints, not guessed). Time is never judged here.

    A failed phase's ratings are logged as prefix events of the same learning block (C6), so
    the card is built by replaying them before the passing phase: the stored stability is
    what a recompute from the log gives (C3). `replayed` is the passing phase only (the
    failed ratings already have their events)."""
    earlier = [(int(r), int(t)) for r, t in state.level_evidence.get(FAILED_PHASES, [])]
    phase = [(int(r), int(t)) for r, t in state.level_evidence.get("phase", [])]
    phase.append((rating, at_ms))
    count = state.learning_count + 1
    streak = state.learning_streak + 1 if counts else 0
    evidence = dict(state.level_evidence)
    evidence.pop("example_due", None)
    if streak >= correct_in_a_row:
        memory = adapter.replay([*earlier, *phase])
        if memory is None:
            raise ValueError("a passed learning phase has attempts to replay")
        learned = replace(
            with_memory(state, memory, REVIEW),
            reps=state.reps + len(phase),
            level="learned",
            level_at=at_ms,
            learned_at=at_ms,
            learning_streak=0,
            learning_count=0,
            leech=False,
            shaky=False,
            shaky_reviews=0,
            level_evidence={**sticky(evidence), "log": []},
        )
        return LearningResult(state=learned, passed=True, replayed=tuple(phase))
    if count >= max_problems or (max_problems - count) < (correct_in_a_row - streak):
        restart = (today + timedelta(days=1)).isoformat()
        failed = replace(
            state,
            learning_streak=0,
            learning_count=0,
            level_evidence={
                **sticky(evidence),
                "phase": [],
                "example_due": True,
                "restart_on": restart,
                FAILED_PHASES: [list(p) for p in (*earlier, *phase)],
            },
        )
        return LearningResult(state=failed, failed=True)
    evidence["phase"] = [list(p) for p in phase]
    return LearningResult(
        state=replace(state, learning_streak=streak, learning_count=count, level_evidence=evidence)
    )


# ---------------------------------------------------------------- reviews, lapses, leeches


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviewResult:
    state: SkillState
    lapse: bool = False
    leech: bool = False
    provisional_demoted: bool = False
    fsrs_event: bool = True


def review_answer(
    state: SkillState,
    *,
    rating: int,
    at_ms: int,
    adapter: FsrsAdapter,
    days: StudyDays,
    leech_lapses: int,
    excused: bool = False,
) -> ReviewResult:
    """A rated core-band review. Again on a review card is a lapse: relearning tomorrow,
    reinforcement later today. Reaching the leech threshold starts the repair (ENG-9).
    `excused`: an Again the leech counter ignores (an accepted careless slip, or a miss the
    check traced to another skill, ADR-0014): FSRS and the lapse count still see it."""
    memory = memory_of(state)
    if memory is None:
        raise ValueError("review_answer needs an FSRS card")
    provisional = provisional_kind(state)
    if provisional is not None and rating == AGAIN and not excused:
        # The first real review demotes a provisional seed: it starts as new (no lapse).
        return ReviewResult(
            state=start_learning(_cleared(state, at_ms), state.skill_id, at_ms),
            provisional_demoted=True,
            fsrs_event=False,
        )
    after = review_on(adapter, memory, rating, at_ms, days)
    lapse = rating == AGAIN and state.fsrs_state == REVIEW
    evidence = dict(state.level_evidence)
    evidence.pop("provisional", None)
    new = replace(
        with_memory(state, after, RELEARNING if rating == AGAIN else REVIEW),
        reps=state.reps + 1,
        lapses=state.lapses + (1 if lapse else 0),
        level_evidence=evidence,
    )
    base = int(evidence.get("leech_base", 0))
    if lapse and excused:
        evidence["leech_base"] = base + 1
        return ReviewResult(state=replace(new, level_evidence=evidence), lapse=True)
    if lapse and new.lapses - base >= leech_lapses:
        repair = start_learning(_cleared(new, at_ms), new.skill_id, at_ms)
        repair = replace(
            repair,
            leech=True,
            leech_at=at_ms,
            level="learning",
            level_at=at_ms,
            level_evidence={
                **repair.level_evidence,
                "leech_repair": True,
                "leech_base": new.lapses,
            },
        )
        return ReviewResult(state=repair, lapse=True, leech=True)
    return ReviewResult(state=new, lapse=lapse)


def _cleared(state: SkillState, at_ms: int) -> SkillState:
    """No FSRS card any more (a fresh learning phase follows). History counters stay."""
    return replace(
        state,
        fsrs_state=None,
        fsrs_step=None,
        stability=None,
        difficulty=None,
        due_at=None,
        level="learning",
        level_at=at_ms,
        shaky=False,
        shaky_reviews=0,
        learning_streak=0,
        learning_count=0,
        introduced_at=None,
    )


# ---------------------------------------------------------------- provisional seeds


def seed_provisional(
    state: SkillState | None,
    skill_id: str,
    *,
    kind: Provisional,
    stability: float,
    at_ms: int,
    adapter: FsrsAdapter,
) -> SkillState | None:
    """Start a skill in review with a provisional stability (placement or a Covered/Solid
    section). Only ever adds knowledge: a stronger existing card is left alone (None)."""
    existing = memory_of(state)
    if existing is not None and existing.stability >= stability:
        return None
    base = state or SkillState(skill_id=skill_id)
    if existing is not None:
        # A real card that is weaker: raise it, but never mark it provisional (a miss on a
        # provisional seed resets it, and placement must not take progress away).
        raised = Memory(stability, existing.difficulty, at_ms)
        return replace(with_memory(base, raised, REVIEW), fsrs_state=base.fsrs_state)
    good = adapter.review(None, 3, at_ms)
    memory = Memory(stability, good.difficulty, at_ms)
    level = base.level if base.level in ("learned", "exam", "mastered") else "learned"
    return replace(
        with_memory(base, memory, REVIEW),
        introduced_at=base.introduced_at or at_ms,
        level=level,
        level_at=base.level_at if level == base.level else at_ms,
        learned_at=base.learned_at or at_ms,
        learning_streak=0,
        learning_count=0,
        level_evidence={**sticky(base.level_evidence), "log": [], "provisional": kind},
    )
