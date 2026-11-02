"""Flashcards (QUE-2, Study screen "Flashcards"): FSRS per card with the student's own
rating, like Anki. The engine schedules skills only, so the queue keeps this small piece:
FsrsAdapter for the memory update, Again = relearn the next study day (and a re-show later
in the session, I5), leeches marked and no longer served. Typed answers are graded by the
checker: correct is Good, wrong is Again.

Anki parity (I5, ADR-0014): a lapse is an Again on a card in review on a new study day
(Anki rslib/src/scheduler/states/review.rs, `answer_again`), so an Again while relearning
or a second Again the same day is no lapse. Flashcards get their own FSRS parameters
(`Engine.adapter_for_card`: the "flashcards" set or the card's Anki deck group's), never the
skills' fitted ones."""

from dataclasses import replace
from datetime import timedelta

from core.engine import RULES_VERSION, FsrsAdapter, Memory, StudyDays
from core.engine.lifecycle import review_on
from core.model import FlashcardState, ReviewEvent

FLASHCARD_RETENTION = 0.90
REVIEW, RELEARNING = 2, 3
FLASHCARD_REWRITE = "This card keeps lapsing, so it needs a rewrite: it won't be shown until then."


def _memory(state: FlashcardState | None) -> Memory | None:
    if (
        state is None
        or state.stability is None
        or state.difficulty is None
        or state.last_review_at is None
    ):
        return None
    return Memory(state.stability, state.difficulty, state.last_review_at)


def grade_flashcard(
    state: FlashcardState | None,
    *,
    card_id: str,
    card_ord: int,
    rating: int,
    at_ms: int,
    adapter: FsrsAdapter,
    days: StudyDays,
    leech_lapses: int = 8,
) -> tuple[FlashcardState, ReviewEvent, float | None]:
    """The card's next state, its review event, and the recall predicted before it."""
    base = state or FlashcardState(card_id=card_id, ord=card_ord)
    memory = _memory(state)
    recall = adapter.retrievability(memory, at_ms) if memory is not None else None
    same = memory is not None and days.day_of(at_ms) == days.day_of(memory.last_review_at)
    after = review_on(adapter, memory, rating, at_ms, days)  # whole study days (C4)
    today = days.day_of(at_ms)
    lapse = rating == 1 and base.fsrs_state == REVIEW and memory is not None and not same
    if rating == 1:
        due_day = today + timedelta(days=1)
    else:
        interval = adapter.interval_days(
            after.stability, FLASHCARD_RETENTION, f"fc|{card_id}|{card_ord}|{at_ms}"
        )
        due_day = today + timedelta(days=max(1, interval))
    lapses = base.lapses + (1 if lapse else 0)
    new_state = replace(
        base,
        fsrs_state=RELEARNING if rating == 1 else REVIEW,
        fsrs_step=None,
        stability=after.stability,
        difficulty=after.difficulty,
        last_review_at=at_ms,
        due_at=days.start(due_day),
        reps=base.reps + 1,
        lapses=lapses,
        leech=base.leech or lapses >= leech_lapses,
    )
    event = ReviewEvent(
        at=at_ms,
        target_kind="flashcard",
        target_id=card_id,
        target_ord=card_ord,
        rating=rating,
        rules_version=RULES_VERSION,
        params_id=adapter.params_id,
        retention=FLASHCARD_RETENTION,
        predicted_recall=None if recall is None else min(1.0, max(0.0, recall)),
    )
    return new_state, event, recall
