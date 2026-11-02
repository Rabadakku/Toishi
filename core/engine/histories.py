"""Review histories for fitting and for rebuilding memory (C6, I1; ADR-0013).

One history per FSRS card: the steps from its last fresh start, in time order, each with
whole study days since the previous step. The fitter turns every target step with
delta > 0 into one training item that carries its whole prefix (as Anki's
`reviews_for_fsrs` does); recompute replays the last history through the same updates.

What starts a history:
- a **block start**: the first event of a learning block (the first learning phase after
  a fresh card, a leech repair or a provisional demotion, failed phases included). Written
  explicitly in the attempt's extra (`FIT_EVENTS_KEY`); older rows are inferred: an event
  with no stability before it, whose previous event was not a learning event. So a
  learning phase that crosses the 04:00 rollover stays one history.
- an **anchor**: an event whose card was set outside the log (a placement seed): the
  history starts from that seed's memory. Such histories are replayed, never trained on.

What is never a prediction target (prefix only): events under other RULES_VERSIONs,
failed learning-phase ratings, stretch events, check-settled events, the core-band
follow-up served after a stretch miss (I1), and below-band items (ENG-4, ADR-0019 item 5:
the Lighter set and checks under the core band). Same-day steps (delta 0) never are either.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from typing import Any, Final, Literal

from core.engine.config import RULES_VERSION
from core.engine.days import stored_days
from core.engine.fsrs_adapter import Memory
from core.model import Attempt, GradedAnswer, JsonObject, ReviewEvent

# Attempt.extra keys this module reads and writes.
FIT_EVENTS_KEY: Final = "fsrs_events"  # [{target, ord, at, rating, block_start, role, kind}]
STRICT_OK_KEY: Final = "strict_ok"  # first try, final answer correct, no hint (I1)
RECALL_DAYS_KEY: Final = "recall_days"  # predicted recall on whole study days (C4)
BELOW_BAND_KEY: Final = "below_band"  # graded below the skill's core band (ENG-4)

Kind = Literal[
    "learning", "learning-failed", "review", "stretch", "settled", "post-stretch", "below-band"
]
TARGET_KINDS: Final = frozenset({"learning", "review"})
LEARNING_KINDS: Final = frozenset({"learning", "learning-failed"})
type TargetKey = tuple[str, str, int]  # (target_kind, target_id, target_ord)


def target_key(e: ReviewEvent) -> TargetKey:
    return (e.target_kind, e.target_id, e.target_ord)


@dataclass(frozen=True, slots=True)
class Step:
    event_id: int | None
    at: int
    day: date
    rating: int
    kind: Kind
    target: bool  # may be a prediction target (still needs delta > 0)
    delta: int  # whole study days since the previous step (0 for the first)


@dataclass(frozen=True, slots=True)
class History:
    key: TargetKey
    steps: tuple[Step, ...]
    seed: Memory | None = None  # an anchored history starts from this memory
    anchored: bool = False  # starts from a card set outside the log (never trained on)

    @property
    def reviews(self) -> list[tuple[int, int]]:
        return [(s.rating, s.delta) for s in self.steps]


@dataclass(frozen=True, slots=True)
class Item:
    """One training item: (rating, whole days) pairs, the last one the target."""

    key: TargetKey
    reviews: tuple[tuple[int, int], ...]
    at: int  # the target's time (items are fitted and split in this order)


# ---------------------------------------------------------------- the strict label (I1)


def strict_ok_of(attempt: Attempt) -> bool:
    """Final answer correct on the first try with no hint. Grading writes it to
    extra["strict_ok"]; rows without it derive the same thing from the attempt."""
    raw = attempt.extra.get(STRICT_OK_KEY)
    if isinstance(raw, bool):
        return raw
    return (
        attempt.verdict == "correct"
        and attempt.attempt_number == 1
        and attempt.hints_used == 0
        and not attempt.example_opened
    )


# ---------------------------------------------------------------- annotations


def _annotations(attempt: Attempt | None) -> list[JsonObject]:
    raw = None if attempt is None else attempt.extra.get(FIT_EVENTS_KEY)
    return [a for a in raw if isinstance(a, dict)] if isinstance(raw, list) else []


def annotation_of(e: ReviewEvent, attempt: Attempt | None, nth: int = 0) -> JsonObject | None:
    """The entry written for this event (match: target, ord, at, rating). One answer can log
    several events that match the same entries (a learning phase answered within one
    millisecond): `nth` is the event's rank among them by row id, the order the entries
    were written in (annotate_answer, record_answer)."""
    found = [
        a
        for a in _annotations(attempt)
        if a.get("target") == e.target_id
        and int(a.get("ord", 0)) == e.target_ord
        and a.get("at") == e.at
        and a.get("rating") == e.rating
    ]
    return found[nth] if nth < len(found) else None


def annotation(
    e: ReviewEvent, *, kind: Kind, block_start: bool = False, role: str | None = None
) -> JsonObject:
    """The extra entry for one event of an answer (match: target, ord, at, rating)."""
    return {
        "target": e.target_id,
        "ord": e.target_ord,
        "at": e.at,
        "rating": e.rating,
        "kind": kind,
        "block_start": block_start,
        "role": role or ("target" if kind in TARGET_KINDS else "prefix"),
    }


# ---------------------------------------------------------------- classifying events


def _stability_before(e: ReviewEvent) -> float | None:
    raw = (e.state_before or {}).get("stability")
    return None if raw is None else float(raw)


def _last_before(e: ReviewEvent) -> int | None:
    raw = (e.state_before or {}).get("last_review_at")
    return None if raw is None else int(raw)


def _stage(attempt: Attempt | None) -> str | None:
    raw = None if attempt is None else attempt.extra.get("stage")
    return None if raw is None else str(raw)


def _base_kind(e: ReviewEvent, attempt: Attempt | None) -> Kind:
    stage = _stage(attempt)
    if (
        stage == "learning"
        and _stability_before(e) is not None  # a card before the answer: see annotate_answer
        and attempt is not None
        and attempt.at
        and e.target_kind == "skill"
        and e.at != attempt.at
    ):
        return "settled"  # a held miss settled as a leech's lapse
    if stage == "learning" or _stability_before(e) is None:
        return "learning"
    if attempt is not None and e.target_kind == "skill":
        own = e.target_id == attempt.skill_id
        if attempt.at and e.at != attempt.at:
            return "settled"  # a held verdict, applied at the miss's own time
        if stage == "stretch" and own:
            return "stretch"
        if e.predicted_recall is None and stage == "review":
            return "settled"
    return "review"


def _below_band(e: ReviewEvent, attempt: Attempt | None) -> bool:
    """ENG-4: the attempt's own event, graded below its core band. Rows from before the flag
    were graded under older rules (RULES_VERSION r3), so they are prefixes already."""
    if attempt is None or e.target_kind != "skill" or e.target_id != attempt.skill_id:
        return False
    return bool(attempt.extra.get(BELOW_BAND_KEY)) and not (attempt.at and e.at != attempt.at)


def build_histories(
    events: Iterable[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    attempts: Mapping[int, Attempt] | None = None,
    rules_version: str = RULES_VERSION,
) -> list[History]:
    """Every history of every card, oldest first per card (voided events are skipped)."""
    attempts = attempts or {}
    stored = stored_days(attempts.values())  # ENG-23: replays use the days stored at grading
    computed = day_of

    def frozen_day(ms: int) -> date:
        day = stored.get(ms)
        return day if day is not None else computed(ms)

    day_of = frozen_day
    all_events = sorted(events, key=lambda e: (e.at, e.id or 0))
    known_at: dict[TargetKey, set[int]] = defaultdict(set)
    by_target: dict[TargetKey, list[ReviewEvent]] = defaultdict(list)
    for e in all_events:
        known_at[target_key(e)].add(e.at)  # voided ones too: a void is not an outside change
        if e.voided_by is None:
            by_target[target_key(e)].append(e)
    # Stretch misses that left no event on their skill: the next event that day follows up.
    with_events = {(e.attempt_id, e.target_id) for e in all_events if e.voided_by is None}
    pending = {
        f"{a.skill_id}|{day_of(a.at).isoformat()}": a.at
        for a in sorted(attempts.values(), key=lambda a: a.at)
        if a.final
        and _stage(a) == "stretch"
        and a.voided_by is None
        and a.skill_id
        and (a.id, a.skill_id) not in with_events
    }
    out: list[History] = []
    for key, evs in by_target.items():
        out.extend(_histories_of(key, evs, day_of, attempts, rules_version, known_at[key], pending))
    return out


def _histories_of(
    key: TargetKey,
    evs: Sequence[ReviewEvent],
    day_of: Callable[[int], date],
    attempts: Mapping[int, Attempt],
    rules_version: str,
    known_at: set[int],
    pending: dict[str, int],
) -> list[History]:
    out: list[History] = []
    steps: list[Step] = []
    seed: Memory | None = None
    anchored = False
    started = False
    prev_kind: Kind | None = None
    prev_at: int | None = None
    ties: dict[tuple[int | None, int, int], int] = defaultdict(int)  # events seen per entry
    for e in evs:  # in (at, id) order, so tied events of one answer come in row order
        attempt = attempts.get(e.attempt_id) if e.attempt_id is not None else None
        tie = (e.attempt_id, e.at, e.rating)
        note = annotation_of(e, attempt, ties[tie])
        ties[tie] += 1
        kind: Kind = note["kind"] if note and note.get("kind") else _base_kind(e, attempt)
        if kind == "review" and _below_band(e, attempt):
            kind = "below-band"
        if kind == "review" and e.target_kind == "skill":
            miss = f"{e.target_id}|{day_of(e.at).isoformat()}"
            if miss in pending and pending[miss] < e.at:
                kind = "post-stretch"
                del pending[miss]
        if note is not None and "block_start" in note:
            block_start = bool(note["block_start"])
        else:
            block_start = kind in LEARNING_KINDS and prev_kind not in LEARNING_KINDS
        last = _last_before(e)
        stability = _stability_before(e)
        anchor = (
            not block_start
            and stability is not None
            and last is not None
            and last not in known_at
            and (prev_at is None or last != prev_at)
        )
        if block_start or anchor or not started:
            if steps:
                out.append(History(key, tuple(steps), seed, anchored))
            steps = []
            seed = None
            started = True
            anchored = not block_start and stability is not None
            difficulty = (e.state_before or {}).get("difficulty")
            if anchored and last is not None and stability is not None and difficulty is not None:
                seed = Memory(stability, float(difficulty), last)
        if seed is not None and not steps:
            delta = (day_of(e.at) - day_of(seed.last_review_at)).days
        elif steps:
            delta = (day_of(e.at) - steps[-1].day).days
        else:
            delta = 0
        target = (
            kind in TARGET_KINDS
            and e.rules_version == rules_version
            and (note is None or note.get("role", "target") == "target")
        )
        steps.append(
            Step(
                event_id=e.id,
                at=e.at,
                day=day_of(e.at),
                rating=e.rating,
                kind=kind,
                target=target,
                delta=max(0, delta),
            )
        )
        prev_kind = kind
        prev_at = e.at
    if steps:
        out.append(History(key, tuple(steps), seed, anchored))
    return out


def training_items(histories: Iterable[History]) -> list[Item]:
    """Fit items, in target time order: every target step with delta > 0 in a history that
    starts at a first review, carrying its whole prefix."""
    items: list[Item] = []
    for h in histories:
        if h.anchored:
            continue
        pairs = h.reviews
        for k in range(1, len(h.steps)):
            step = h.steps[k]
            if step.target and step.delta > 0:
                items.append(Item(key=h.key, reviews=tuple(pairs[: k + 1]), at=step.at))
    items.sort(key=lambda i: (i.at, i.key))
    return items


def last_histories(histories: Iterable[History]) -> dict[TargetKey, History]:
    """Each card's latest history (what its memory is rebuilt from)."""
    out: dict[TargetKey, History] = {}
    for h in histories:
        prev = out.get(h.key)
        if prev is None or h.steps[0].at >= prev.steps[0].at:
            out[h.key] = h
    return out


# ---------------------------------------------------------------- writing annotations


def failed_phase_events(
    skill_id: str,
    phase: Sequence[Sequence[int]],
    *,
    params_id: str | None,
    retention: float | None,
) -> list[ReviewEvent]:
    """C6: the ratings of a failed learning phase as prefix-only events (rating, at)."""
    return [
        ReviewEvent(
            at=int(at),
            target_kind="skill",
            target_id=skill_id,
            rating=int(rating),
            rules_version=RULES_VERSION,
            params_id=params_id,
            retention=retention,
        )
        for rating, at in phase
    ]


def annotate_answer(
    answer: GradedAnswer,
    *,
    stage: str | None,
    previous_kind: Callable[[TargetKey], Kind | None],
    extra_events: Sequence[ReviewEvent] = (),
    recall_days: float | None = None,
    card_before: bool = False,
) -> GradedAnswer:
    """Add the fit annotations to a graded answer before it is stored: one entry per event
    (kind, explicit block start, role), the strict label's default and whole-day recall.
    `extra_events` (a failed phase's ratings) are appended as learning-failed events.
    `card_before`: the skill had an FSRS card before this answer. Graded in a learning phase
    all the same, the phase began within this answer (a held miss settled as a leech's
    lapse), so an own event at another time is that settled lapse, not the phase."""
    events = [*answer.reviews, *extra_events]
    attempt = answer.attempt
    notes: list[JsonObject] = []
    open_blocks: dict[TargetKey, Kind | None] = {}
    for i, e in enumerate(events):
        k = target_key(e)
        if k not in open_blocks:
            open_blocks[k] = previous_kind(k)
        if i >= len(answer.reviews):
            kind: Kind = "learning-failed"
        elif (
            stage == "learning"
            and e.target_id == attempt.skill_id
            and not (card_before and e.at != attempt.at)
        ):
            kind = "learning"
        elif attempt.at and e.at != attempt.at and e.target_kind == "skill":
            kind = "settled"
        elif stage == "stretch" and e.target_id == attempt.skill_id:
            kind = "stretch"
        elif attempt.extra.get(BELOW_BAND_KEY) and e.target_id == attempt.skill_id:
            kind = "below-band"
        else:
            kind = "review"
        start = kind in LEARNING_KINDS and open_blocks[k] not in LEARNING_KINDS
        notes.append(annotation(e, kind=kind, block_start=start))
        open_blocks[k] = kind
    extra: dict[str, Any] = dict(attempt.extra)
    if notes:
        extra[FIT_EVENTS_KEY] = notes
    if STRICT_OK_KEY not in extra and attempt.final and attempt.rating is not None:
        extra[STRICT_OK_KEY] = strict_ok_of(attempt)
    if recall_days is not None and RECALL_DAYS_KEY not in extra:
        extra[RECALL_DAYS_KEY] = min(1.0, max(0.0, recall_days))
    return replace(answer, attempt=replace(attempt, extra=extra), reviews=tuple(events))
