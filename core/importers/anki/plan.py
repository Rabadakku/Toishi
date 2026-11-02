"""Importing an Anki deck into a profile: a dry run, then one transaction (IMP-5).

`plan_anki_import` maps the notes (mapping.py), checks Mastery Problem notes through the
card-file pipeline, and compares everything with the profile through core.cards' import
plan: added / updated / unchanged / rejected, each with file, line (a note's number in a
package, a row's line in a text file) and reason. With history, it also lists the review
history and FSRS memory states to import. Nothing is written.

`apply_anki_import` writes the plan in one transaction: cards, media (scoped CSS too),
revisions and the import log through core.cards.apply_import, then the history:

- every review as an append-only attempt (verdict "self", the Anki rating, the Anki study
  day as its study day, rules version `anki-import-1`) with its review event. Reviews the
  profile already has (same card, item and time) are skipped, so importing again adds none;
- FSRS memory states imported as they are, as flashcard state rows, only where the profile
  has none (studying in the app since wins);
- the deck groups' parameter sets and the items to replay, in the import log's summary.

Memory state for histories without FSRS state is the engine's to compute by replaying the
events: after applying, call `recompute_memory(storage, result.record)`
(`ENGINE_RECOMPUTE_HOOK`), which also registers the deck groups' parameter sets.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.cards.importer import ImportPlan, apply_import, plan_loaded
from core.cards.load import LoadResult, Rejected, load
from core.cards.sweep import SweepRunner
from core.importers.anki import history as hist
from core.importers.anki.mapping import ImportMedia, Mapped, map_notes, note_line
from core.importers.anki.model import AnkiData, Revlog
from core.importers.anki.package import read_package
from core.importers.anki.stock import TOISHI_PROBLEM
from core.importers.anki.text_export import read_text
from core.model import Attempt, FlashcardState, GradedAnswer, ImportRecord, ReviewEvent
from core.storage import UserStore
from core.storage import clock as clock_mod

if TYPE_CHECKING:
    from core.storage import Storage

RULES_VERSION = "anki-import-1"
ENGINE_RECOMPUTE_HOOK = "recompute_memory"
PACKAGE_SUFFIXES = (".apkg", ".colpkg")
TEXT_SUFFIXES = (".txt", ".csv", ".tsv")

type ItemKey = tuple[str, int]  # (card id, study item ord)


def read_anki_file(path: Path, *, deck: str | None = None) -> AnkiData:
    """Read an .apkg / .colpkg / plain-text export, by its suffix (else by its content: a zip
    archive is a package). Raises AnkiImportError when the file can't be imported."""
    suffix = path.suffix.lower()
    if suffix in PACKAGE_SUFFIXES:
        return read_package(path)
    if suffix not in TEXT_SUFFIXES:
        with path.open("rb") as handle:
            if handle.read(4) == b"PK\x03\x04":
                return read_package(path)
    return read_text(path, deck=deck)


@dataclass(frozen=True, slots=True)
class HistoryPlan:
    targets: tuple[hist.TargetHistory, ...] = ()
    param_sets: tuple[hist.ParamSet, ...] = ()
    skipped_mastery: int = 0  # Anki cards of Mastery Problem notes (scheduled by skill)
    new_reviews: Mapping[ItemKey, tuple[hist.AnkiReview, ...]] = field(default_factory=dict)
    new_memory: frozenset[ItemKey] = frozenset()

    @property
    def review_count(self) -> int:
        return sum(len(v) for v in self.new_reviews.values())

    def replay(self) -> list[hist.TargetHistory]:
        """Items with new reviews and no imported memory: the engine replays them."""
        return [
            t for t in self.targets if t.memory is None and self.new_reviews.get((t.card_id, t.ord))
        ]


@dataclass(slots=True)
class AnkiImportPlan:
    """The dry run (IMP-5): `cards` is core.cards' plan, `history` what applying adds."""

    source: str
    format: str
    cards: ImportPlan
    history: HistoryPlan = field(default_factory=HistoryPlan)
    notes: int = 0
    reader_warnings: list[str] = field(default_factory=list)

    @property
    def nothing_to_do(self) -> bool:
        h = self.history
        return self.cards.nothing_to_do and not h.review_count and not h.new_memory

    def summary(self) -> dict[str, Any]:
        return self.cards.summary()

    def report(self) -> str:
        lines = [f"{self.source}: {self.notes} notes", self.cards.report()]
        lines += [f"{self.source}: {w}" for w in self.reader_warnings]
        h = self.history
        if h.targets:
            lines.append(
                f"history: {h.review_count} new reviews for {len(h.new_reviews)} study items; "
                f"{len(h.new_memory)} FSRS memory states imported as they are"
            )
        lines += [
            f"FSRS parameters of deck options {p.name!r}: {len(p.parameters)} values"
            for p in h.param_sets
        ]
        if h.skipped_mastery:
            lines.append(
                f"history of {h.skipped_mastery} Mastery Problem cards is not imported "
                "(problems are scheduled through their skills)"
            )
        return "\n".join(lines)


def plan_anki_import(
    store: UserStore,
    data: AnkiData,
    *,
    with_history: bool = True,
    pack_skills: Mapping[str, str] | None = None,
    pack_cards: Mapping[str, str] | None = None,
    runner: SweepRunner | None = None,
) -> AnkiImportPlan:
    """The dry run for one Anki file (from read_package / read_text / read_anki_file)."""
    stored: dict[str, dict[str, str]] = {}
    for link in store.media.all_links():
        stored.setdefault(link.card_id, {})[link.ref] = link.file
    media = ImportMedia(data, stored, store.media)
    mapped = map_notes(data, media)
    loaded = _load_mastery(mapped, runner)
    _merge(loaded, data, mapped, media)
    cards = plan_loaded(
        store, loaded, pack_skills=pack_skills, pack_cards=pack_cards, kind=data.format
    )
    plan = AnkiImportPlan(
        data.name, data.format, cards, notes=len(data.notes), reader_warnings=list(data.warnings)
    )
    if with_history and data.cards:
        plan.history = _plan_history(store, data, mapped, cards)
    cards.extra["anki"] = _summary(plan)
    return plan


def _summary(plan: AnkiImportPlan) -> dict[str, Any]:
    h = plan.history
    return {
        "format": plan.format,
        "notes": plan.notes,
        "reviews": h.review_count,
        "memory_states": len(h.new_memory),
        "param_sets": [
            {
                "id": p.id,
                "name": p.name,
                "parameters": list(p.parameters),
                "fsrs6": list(p.fsrs6),
                "desired_retention": p.desired_retention,
                "decks": list(p.decks),
            }
            for p in h.param_sets
        ],
        "replay": [
            {"card": t.card_id, "ord": t.ord, "complete": t.complete, "param_set": t.param_set}
            | ({"sm2_seed": dict(t.sm2_seed)} if t.sm2_seed else {})
            for t in h.replay()
        ],
    }


def _load_mastery(mapped: Mapped, runner: SweepRunner | None) -> LoadResult:
    if mapped.mastery is None:
        return LoadResult()
    loaded = load([mapped.mastery], runner=runner)

    def fix(line: int) -> int:
        return note_line(mapped, line)

    loaded.cards = [replace(a, line=fix(a.line)) for a in loaded.cards]
    loaded.rejected = [
        replace(r, line=fix(r.line), lines=tuple(fix(n) for n in r.lines)) for r in loaded.rejected
    ]
    loaded.warnings = [replace(p, line=fix(p.line)) for p in loaded.warnings]
    loaded.file_problems = [replace(p, line=fix(p.line)) for p in loaded.file_problems]
    return loaded


def _merge(loaded: LoadResult, data: AnkiData, mapped: Mapped, media: ImportMedia) -> None:
    taken = {a.card.id for a in loaded.cards}
    for item in mapped.accepted:
        if item.card.id in taken:
            reason = f"ID {item.card.id} is also a Mastery Problem card's ID"
            loaded.rejected.append(Rejected(item.card.id, item.file, item.line, (reason,)))
            continue
        loaded.cards.append(item)
        for _, name in item.images:
            loaded.media[name] = media
    loaded.rejected += mapped.rejected
    loaded.warnings += mapped.warnings
    ids = loaded.files.setdefault(data.name, [])
    ids += [i for i in mapped.ids if i not in ids]


# ---------------------------------------------------------------- history


def _offset_east(data: AnkiData, store: UserStore) -> int:
    """The fixed UTC offset Anki days are counted in: the collection's own when it has one
    (colpkg), else the profile time zone's offset now (what Anki does on this Mac)."""
    if data.minutes_west is not None:
        return -data.minutes_west * 60
    offset = clock_mod.from_ms(store.db.clock.now_ms(), store.timezone()).utcoffset()
    return int(offset.total_seconds()) if offset is not None else 0


def _plan_history(
    store: UserStore, data: AnkiData, mapped: Mapped, cards: ImportPlan
) -> HistoryPlan:
    planned = {c.card.id for c in cards.added + cards.updated}
    planned |= {a.card.id for a in cards.unchanged}
    rollover = hist.DEFAULT_ROLLOVER_HOUR if data.rollover_hour is None else data.rollover_hour
    offset = _offset_east(data, store)
    tz, profile_rollover = store.timezone(), store.rollover_hour()

    def day_start(at_ms: int, days: int) -> int:
        day = clock_mod.study_day(at_ms, tz, profile_rollover) + timedelta(days=days)
        return clock_mod.day_start_ms(day, tz, profile_rollover)

    by_card: dict[int, list[Revlog]] = {}
    for entry in data.revlog:
        by_card.setdefault(entry.card_id, []).append(entry)
    mastery_notes = {
        n.id
        for n in data.notes
        if (nt := data.notetypes.get(n.notetype_id)) is not None and nt.name == TOISHI_PROBLEM
    }
    groups: dict[int, set[str]] = {}
    targets: list[hist.TargetHistory] = []
    skipped = 0
    for card in data.cards or ():
        target = mapped.targets.get(card.id)
        entries = by_card.get(card.id, [])
        if target is None or target.card_id not in planned:
            skipped += 1 if entries and card.note_id in mastery_notes else 0
            continue
        config = data.deck_configs.get(card.config_id) if card.config_id is not None else None
        filtered = hist.reviews_for_fsrs(entries, config.ignore_before_ms if config else 0)
        reviews = tuple(
            hist.AnkiReview(e.id, hist.anki_day(e.id, rollover, offset), e.ease, e)
            for e in (filtered.entries if filtered else ())
        )
        memory = hist.imported_memory(card, config, reviews[-1].at if reviews else None, day_start)
        if not reviews and memory is None:
            continue
        param_set = hist.param_set_for(config, ()) if config is not None else None
        if param_set is not None and config is not None:
            groups.setdefault(config.id, set()).add(card.deck)
        complete = filtered.complete if filtered else True
        targets.append(
            hist.TargetHistory(
                card_id=target.card_id,
                ord=target.ord,
                kind=target.kind,
                reviews=reviews,
                complete=complete,
                memory=memory,
                param_set=param_set.id if param_set else None,
                sm2_seed=None if complete or filtered is None else hist.sm2_seed(filtered.entries),
            )
        )
    param_sets = tuple(
        p
        for cid, decks in sorted(groups.items())
        if (p := hist.param_set_for(data.deck_configs[cid], decks)) is not None
    )
    new_reviews, new_memory = _new_items(store, targets)
    return HistoryPlan(tuple(targets), param_sets, skipped, new_reviews, new_memory)


def _new_items(
    store: UserStore, targets: Iterable[hist.TargetHistory]
) -> tuple[dict[ItemKey, tuple[hist.AnkiReview, ...]], frozenset[ItemKey]]:
    """Per study item, the reviews the profile doesn't have yet (same card, item and time),
    and the items whose FSRS state to import (those with no state in the profile)."""
    existing = {
        (e.target_id, e.target_ord, e.at)
        for e in store.review_events(target_kind="flashcard", include_voided=True)
    }
    states = {(s.card_id, s.ord) for s in store.flashcard_states()}
    reviews: dict[ItemKey, tuple[hist.AnkiReview, ...]] = {}
    memory: set[ItemKey] = set()
    for t in targets:
        key = (t.card_id, t.ord)
        fresh = tuple(r for r in t.reviews if (t.card_id, t.ord, r.at) not in existing)
        if fresh:
            reviews[key] = fresh
        if t.memory is not None and key not in states:
            memory.add(key)
    return reviews, frozenset(memory)


# ---------------------------------------------------------------- applying


@dataclass(frozen=True, slots=True)
class AnkiImportResult:
    record: ImportRecord
    reviews: int  # review events written
    memory_states: int  # FSRS memory states imported as they are
    needs_replay: tuple[ItemKey, ...]  # items whose memory the engine must replay


def apply_anki_import(
    store: UserStore, plan: AnkiImportPlan, retire: Iterable[str] = ()
) -> AnkiImportResult:
    """Write the plan in one transaction: cards, media, revisions, the log, then history."""
    revs = {c.card.id: c.card.rev for c in plan.cards.added + plan.cards.updated}
    revs |= {a.card.id: a.card.rev for a in plan.cards.unchanged}
    h = plan.history

    def work(s: UserStore) -> AnkiImportResult:
        record = apply_import(s, plan.cards, retire)
        states = {(st.card_id, st.ord) for st in s.flashcard_states()}
        written = 0
        memories: list[FlashcardState] = []
        for t in h.targets:
            key = (t.card_id, t.ord)
            for review in h.new_reviews.get(key, ()):
                s.record_answer(_answer(t, review, revs.get(t.card_id, 1)))
                written += 1
            if key in h.new_memory and key not in states:
                memories.append(_state(t))
        if memories:
            s.apply(memories)
        replay = tuple((t.card_id, t.ord) for t in h.replay())
        return AnkiImportResult(record, written, len(memories), replay)

    return store.atomic(work)


def _answer(t: hist.TargetHistory, review: hist.AnkiReview, rev: int) -> GradedAnswer:
    e = review.entry
    anki: dict[str, Any] = {
        "revlog": e.id,
        "card": e.card_id,
        "type": e.type,
        "ivl": e.ivl,
        "last_ivl": e.last_ivl,
        "factor": e.factor,
        "time": e.time,
        "day": (review.day - hist.EPOCH).days,
    }
    if t.sm2_seed is not None and review is t.reviews[0]:
        anki["sm2_seed"] = dict(t.sm2_seed)
    attempt = Attempt(
        at=review.at,
        study_day=review.day.isoformat(),
        card_id=t.card_id,
        card_rev=rev,
        card_kind="cloze" if t.kind == "cloze" else "flashcard",
        verdict="self",
        rating=review.rating,
        explicit_rating=True,
        active_ms=max(0, e.time),
        params_id=t.param_set,
        rules_version=RULES_VERSION,
        extra={"source": "anki", "anki": anki},
    )
    event = ReviewEvent(
        at=review.at,
        target_kind="flashcard",
        target_id=t.card_id,
        target_ord=t.ord,
        rating=review.rating,
        rules_version=RULES_VERSION,
        params_id=t.param_set,
    )
    return GradedAnswer(attempt=attempt, reviews=(event,))


def _state(t: hist.TargetHistory) -> FlashcardState:
    m = t.memory
    if m is None:  # pragma: no cover - only called for items with imported memory
        raise ValueError(f"{t.card_id}: no memory state to import")
    return FlashcardState(
        card_id=t.card_id,
        ord=t.ord,
        fsrs_state=m.fsrs_state,
        stability=m.stability,
        difficulty=m.difficulty,
        due_at=m.due_at,
        last_review_at=m.last_review_at,
        reps=m.reps,
        lapses=m.lapses,
    )


ANKI_KINDS = ("apkg", "colpkg", "anki-text")
ANKI_GROUP_PREFIX = "anki-"


def recompute_memory(storage: Storage, record: ImportRecord | None = None) -> bool:
    """The hook to run after `apply_anki_import` (`AnkiImportResult.record`): each imported
    deck group's FSRS preset becomes that group's parameter set (decision 6, ADR-0013; the
    set "anki.<preset id>", for the decks that used it), items stored without FSRS state
    get their memory replayed from their reviews with those parameters, then the engine
    rebuilds memory from the log (`Engine.recompute_memory`, C3). `record`: the import to
    register (default: every Anki import in the log, oldest first). Histories cut short
    before Anki's last learning block (an `sm2_seed`) are not replayed: Anki seeds those
    from SM-2, which the engine doesn't do yet. Returns True once the engine ran."""
    from core.engine import Engine

    engine = Engine(storage)
    records = [record] if record is not None else storage.users.imports()
    replay: list[tuple[str, int]] = []
    for r in sorted(records, key=lambda r: (r.at, r.id or 0)):
        anki = r.summary.get("anki") if r.kind in ANKI_KINDS else None
        if not isinstance(anki, dict):
            continue
        for p in anki.get("param_sets", ()):
            group = str(p["id"]).removeprefix(ANKI_GROUP_PREFIX)
            engine.register_deck_group(group, p.get("decks", ()), p.get("fsrs6"))
        replay += [
            (str(t["card"]), int(t["ord"]))
            for t in anki.get("replay", ())
            if t.get("complete", True) and not t.get("sm2_seed")
        ]
    if replay:
        engine.replay_flashcards(replay)
    engine.recompute_memory()
    return True
