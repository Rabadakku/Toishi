"""Optional review history from an Anki package (IMP-4).

Two paths, per card:

1. **FSRS memory state as it is.** When the card's data holds stability and difficulty
   (`s`, `d`) and its deck's options preset has FSRS parameters, the state is imported
   unchanged (last review from `lrt`, due date from the last review plus Anki's interval).
   The preset's parameters become a parameter set (`ParamSet`) for that deck group.
2. **The review log, for replay.** Otherwise the card's revlog is filtered the way Anki
   does before computing FSRS memory (scheduler/fsrs/params.rs `reviews_for_fsrs`): cram
   entries dropped, history starting at the last learning block (or after the last reset;
   nothing graded since a reset means no history), manual / ease-0 rows dropped. Each review
   keeps its Anki study day, counted from the collection's rollover hour (4 AM when an .apkg
   doesn't carry it) in one fixed UTC offset, exactly as Anki counts `delta_t`; replaying
   with 24-hour periods instead gives different stability (9.3 vs 12.65 days in a test).
   A history that doesn't start with learning (an SM-2 era card) is marked incomplete, with
   the first interday review's ease and interval to seed it, as Anki does.

Both paths write review events (append-only attempts, verdict "self", with the Anki study
day as the attempt's study day); the memory state of path 2 is left to the engine's
replay (`ENGINE_RECOMPUTE_HOOK`).
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from core.engine.fsrs_adapter import params_id_for
from core.importers.anki.model import Card, DeckConfig, Revlog

DEFAULT_ROLLOVER_HOUR = 4
LEARNING, REVIEW, RELEARNING, FILTERED, MANUAL, RESCHEDULED = range(6)
EPOCH = date(1970, 1, 1)
DAY_SECONDS = 86_400


def is_cramming(r: Revlog) -> bool:
    return r.type == FILTERED and r.factor == 0


def is_reset(r: Revlog) -> bool:
    return r.type == MANUAL and r.factor == 0


def has_rating(r: Revlog) -> bool:
    return r.ease > 0


def counts_for_scheduling(r: Revlog) -> bool:
    return has_rating(r) and not is_cramming(r)


@dataclass(frozen=True, slots=True)
class Filtered:
    entries: tuple[Revlog, ...]
    complete: bool  # starts with a learning step; else seed from SM-2 (`sm2_seed`)


def reviews_for_fsrs(entries: Sequence[Revlog], ignore_before_ms: int = 0) -> Filtered | None:
    """Anki's filter for one card's revlog (sorted by id), when computing memory (not
    training). None when nothing usable is left."""
    first_learn: int | None = None
    first_grade: int | None = None
    complete = False
    for index in range(len(entries) - 1, -1, -1):
        entry = entries[index]
        if is_cramming(entry):
            continue
        graded = has_rating(entry)
        interday = entry.ivl >= 1 or entry.ivl <= -DAY_SECONDS
        if graded and entry.id > ignore_before_ms and interday:
            first_grade = index
        if graded and entry.type == LEARNING:
            first_learn = index
            complete = True
        elif is_reset(entry):
            if first_learn is not None:
                complete = True
                break
            if first_grade is not None:
                complete = False
                break
            return None
        elif first_learn is not None:
            break
    if (
        first_learn is not None
        and entries[first_learn].id < ignore_before_ms
        and first_learn < len(entries) - 1
    ):
        complete = False
        first_learn = None
    if first_learn is not None:
        kept = entries[first_learn:]
    elif first_grade is not None:
        kept = entries[first_grade:]
    else:
        return None
    usable = tuple(e for e in kept if counts_for_scheduling(e) and 1 <= e.ease <= 4)
    return Filtered(usable, complete) if usable else None


def anki_day(at_ms: int, rollover_hour: int, offset_seconds_east: int) -> date:
    """The Anki study day of a review: days roll over at `rollover_hour` local time, in one
    fixed UTC offset (Anki counts delta_t from the current offset, ignoring DST)."""
    seconds = at_ms // 1000 + offset_seconds_east - rollover_hour * 3600
    return EPOCH + timedelta(days=math.ceil(seconds / DAY_SECONDS) - 1)


@dataclass(frozen=True, slots=True)
class AnkiReview:
    at: int  # epoch ms (the revlog id)
    day: date  # Anki study day
    rating: int
    entry: Revlog


@dataclass(frozen=True, slots=True)
class ImportedMemory:
    """An FSRS memory state taken as it is from the card (path 1)."""

    stability: float
    difficulty: float
    last_review_at: int
    due_at: int
    fsrs_state: int  # 1 learning, 2 review, 3 relearning
    reps: int
    lapses: int
    desired_retention: float | None


@dataclass(frozen=True, slots=True)
class ParamSet:
    """FSRS parameters of one Anki deck options preset (a deck group)."""

    id: str
    name: str
    parameters: tuple[float, ...]  # as stored (21 for FSRS-6, 19 for 5, 17 for 4.5)
    fsrs6: tuple[float, ...]  # filled out to FSRS-6's 21 (what py-fsrs takes)
    desired_retention: float | None
    decks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetHistory:
    """The history of one schedulable item: an own flashcard (ord 0) or one cloze blank."""

    card_id: str
    ord: int
    kind: str  # flashcard or cloze (the attempts' card kind)
    reviews: tuple[AnkiReview, ...]
    complete: bool
    memory: ImportedMemory | None
    param_set: str | None
    sm2_seed: Mapping[str, Any] | None  # {"ease": 2.5, "ivl": 10} for incomplete histories


def fsrs6(parameters: Sequence[float]) -> tuple[float, ...]:
    """FSRS-4.5 (17) and FSRS-5 (19) parameters as FSRS-6's 21, the way fsrs-rs fills them:
    no same-day terms for 4.5, and the fixed decay 0.5 of earlier versions."""
    values = tuple(float(v) for v in parameters)
    if len(values) == 17:
        values += (0.0, 0.0)
    if len(values) == 19:
        values += (0.0, 0.5)
    return values


def param_set_for(config: DeckConfig, decks: Iterable[str]) -> ParamSet | None:
    if not config.fsrs_params:
        return None
    full = fsrs6(config.fsrs_params)
    return ParamSet(
        id=f"anki-{params_id_for(full)}" if len(full) == 21 else f"anki-{config.id}",
        name=config.name,
        parameters=config.fsrs_params,
        fsrs6=full,
        desired_retention=config.desired_retention,
        decks=tuple(sorted(set(decks))),
    )


def imported_memory(
    card: Card, config: DeckConfig | None, last_review_ms: int | None, day_start: Any
) -> ImportedMemory | None:
    """Path 1: the card's own FSRS state, or None. `day_start(at_ms, days)` gives the start
    (UTC ms) of the study day `days` after the one holding `at_ms`."""
    data = card.data
    s, d = data.get("s"), data.get("d")
    if config is None or not config.fsrs_params or card.type not in (1, 2, 3):
        return None
    if not isinstance(s, int | float) or not isinstance(d, int | float) or s <= 0:
        return None
    lrt = data.get("lrt")
    last = int(lrt) * 1000 if isinstance(lrt, int | float) and lrt > 0 else last_review_ms
    if last is None:
        return None
    due = day_start(last, max(1, card.ivl)) if card.type == 2 else last
    retention = data.get("dr")
    return ImportedMemory(
        stability=float(s),
        difficulty=float(d),
        last_review_at=last,
        due_at=due,
        fsrs_state=card.type,
        reps=max(0, card.reps),
        lapses=max(0, card.lapses),
        desired_retention=float(retention)
        if isinstance(retention, int | float)
        else config.desired_retention,
    )


def sm2_seed(entries: Sequence[Revlog]) -> dict[str, Any] | None:
    for e in entries:
        if has_rating(e) and (e.ivl >= 1 or e.ivl <= -DAY_SECONDS):
            ease = e.factor / 1000 if e.factor else 2.5
            seed: dict[str, Any] = {"ease": ease, "ivl": max(e.ivl, 1), "revlog": e.id}
            if 0 < e.factor <= 1100:  # written by FSRS: the difficulty is recoverable
                seed["difficulty"] = (e.factor / 1000 - 0.1) * 9 + 1
            return seed
    return None
