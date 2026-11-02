"""Rebuild FSRS memory from the review log (C3) and check stored states (I6; ADR-0013).

Each card's stability, difficulty and last review are replayed from its latest history
(histories.py: from the last block start, or from a placement seed) through the same
whole-day updates live grading uses. Anki does the same after a parameter change and in
Check Database (memory_state.rs). Due dates (the `due_at` cache) are left alone: live due
dates follow the new stability, and nothing is rescheduled on its own.

Cards whose row moved after their last logged event (a later placement seed) are left
alone, as are cards without a card (learning phase) and cards without history.
"""

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from typing import Any

from core.engine.config import AGAIN, DAY_MS
from core.engine.fsrs_adapter import STABILITY_MAX, FsrsAdapter, Memory
from core.engine.histories import History, TargetKey
from core.model import FlashcardState, ShapeError, SkillState

REVIEW, RELEARNING = 2, 3
STABILITY_MIN = 0.001


def rebuild(history: History, adapter: FsrsAdapter) -> Memory | None:
    """Replay one history (whole study days, the stability update's own clock)."""
    memory = history.seed
    for step in history.steps:
        t = step.delta if memory is not None else 0
        memory = adapter.review(memory, step.rating, step.at, elapsed_days=t)
    return memory


type CardState = SkillState | FlashcardState


def key_of(state: CardState) -> TargetKey:
    if isinstance(state, SkillState):
        return ("skill", state.skill_id, 0)
    return ("flashcard", state.card_id, state.ord)


def _same(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def recomputed[S: (SkillState, FlashcardState)](
    state: S,
    history: History | None,
    adapter: FsrsAdapter,
    *,
    voided_at: Iterable[int] = (),
) -> S | None:
    """The state with its memory rebuilt, or None when nothing changes or the card is
    left alone. `voided_at`: times of events being voided now (the row may still show one
    of them as its last review)."""
    if history is None or state.fsrs_state is None or state.last_review_at is None:
        return None
    if history.anchored and history.seed is None:
        return None  # a seed without its memory: nothing to replay from
    last = history.steps[-1]
    if state.last_review_at != last.at and state.last_review_at not in set(voided_at):
        return None  # the row moved after its last event (a later seed): keep it
    memory = rebuild(history, adapter)
    if memory is None:
        return None
    fsrs_state = state.fsrs_state  # a flashcard's queue state belongs to the queue
    if isinstance(state, SkillState):
        fsrs_state = RELEARNING if last.rating == AGAIN and last.kind != "learning" else REVIEW
    if (
        _same(state.stability, memory.stability)
        and _same(state.difficulty, memory.difficulty)
        and state.last_review_at == memory.last_review_at
        and state.fsrs_state == fsrs_state
    ):
        return None
    return replace(
        state,
        stability=memory.stability,
        difficulty=memory.difficulty,
        last_review_at=memory.last_review_at,
        fsrs_state=fsrs_state,
    )


def recompute_all[S: (SkillState, FlashcardState)](
    states: Iterable[S],
    histories: Mapping[TargetKey, History],
    adapter_of: Callable[[S], FsrsAdapter],
    *,
    voided_at: Mapping[TargetKey, Iterable[int]] | None = None,
) -> list[S]:
    out: list[S] = []
    for state in states:
        k = key_of(state)
        new = recomputed(
            state,
            histories.get(k),
            adapter_of(state),
            voided_at=(voided_at or {}).get(k, ()),
        )
        if new is not None:
            out.append(new)
    return out


# ---------------------------------------------------------------- data guards (I6)


def fsrs_problems(row: Mapping[str, Any], now_ms: int) -> list[str]:
    """What is wrong with a stored row's FSRS fields (raw values, before the model sees
    them): non-finite or out-of-range stability or difficulty, a review in the future, or
    a card with missing memory."""
    problems: list[str] = []
    s, d, last = row.get("stability"), row.get("difficulty"), row.get("last_review_at")
    if s is not None and not (
        isinstance(s, int | float) and math.isfinite(s) and STABILITY_MIN <= s <= STABILITY_MAX
    ):
        problems.append(f"stability {s!r} outside [{STABILITY_MIN}, {STABILITY_MAX:g}]")
    if d is not None and not (isinstance(d, int | float) and math.isfinite(d) and 1 <= d <= 10):
        problems.append(f"difficulty {d!r} outside [1, 10]")
    if last is not None and isinstance(last, int) and last > now_ms + DAY_MS // 24:
        problems.append("last review is in the future")
    if row.get("fsrs_state") is not None and None in (s, d, last):
        problems.append("a card without stability, difficulty or last review")
    return problems


def validate_state(state: CardState, now_ms: int) -> None:
    """Raise ShapeError for a state the engine must never write (I6)."""
    problems = fsrs_problems(
        {
            "stability": state.stability,
            "difficulty": state.difficulty,
            "last_review_at": state.last_review_at,
            "fsrs_state": state.fsrs_state,
        },
        now_ms,
    )
    if problems:
        raise ShapeError("; ".join(problems))
