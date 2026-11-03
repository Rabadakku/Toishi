"""The day's flashcards and cloze blanks (QUE-2, I5), as wave 2's session plans them: FSRS per
card like Anki, unchanged, with the course's schedule deciding when a skill's cards start.

- **Due cards** come first, oldest due first; then **new** ones, up to the daily limits
  (`daily.flashcards`, `daily.new_flashcards`, less what was done today).
- **Which cards are in play.** A card on a skill of a set-up course follows that course's pace
  schedule: in play once the skill is introduced (core.practice). Any other card follows the
  Library as before: not in an Off section (its skill's or its own deck's), and, for a new card
  on a skill, that skill introduced by the earlier engine (`skill_state.introduced_at`).
- Like Anki's "bury new siblings", a cloze card brings at most one new blank a day, and none on
  a day another of its blanks is due or was reviewed. Leeches (I5) wait for a rewrite.
"""

from collections.abc import Collection, Mapping
from dataclasses import dataclass

from core.model import CardRef, FlashcardState, SectionStateName
from core.queue.cloze import ords as cloze_ords
from core.storage import Storage


@dataclass(frozen=True, slots=True)
class Deck:
    due: tuple[tuple[str, int, str | None], ...]  # (card, ord, skill), due first then new
    new: frozenset[tuple[str, int]]  # those never reviewed
    leeches: int  # leech cards waiting for a rewrite


def flashcards(
    storage: Storage,
    *,
    hidden: Collection[str],
    skill_sections: Mapping[str, str | None],
    section_states: Mapping[str, SectionStateName],
    scheduled: Collection[str],
    introduced: Collection[str],
    tomorrow_start: int,
    today_start: int,
) -> Deck:
    """`scheduled`: the course skills of set-up courses; `introduced`: skills introduced so
    far (by those schedules, or by the earlier engine)."""
    refs: dict[str, CardRef] = {
        r.id: r for r in storage.packs.card_refs() if r.kind in ("flashcard", "cloze")
    }

    def in_play(ref: CardRef) -> bool:
        if ref.id in hidden or ref.status != "active":
            return False
        if ref.skill_id is not None and ref.skill_id in scheduled:
            return ref.skill_id in introduced
        sections = {ref.section_id, skill_sections.get(ref.skill_id or "")} - {None}
        return all(section_states.get(str(k), "off") != "off" for k in sections)

    rows = storage.users.flashcard_states()
    seen: dict[tuple[str, int], FlashcardState] = {(f.card_id, f.ord): f for f in rows}
    leeches = sum(1 for f in seen.values() if f.leech and f.card_id in refs)
    due = sorted(
        (f.due_at or 0, f.card_id, f.ord)
        for f in seen.values()
        if f.card_id in refs
        and not f.leech
        and in_play(refs[f.card_id])
        and (f.due_at or 0) < tomorrow_start
    )
    out = [(card, ord_, refs[card].skill_id) for _, card, ord_ in due]
    new: set[tuple[str, int]] = set()
    busy = {card for _, card, _ in due} | {
        f.card_id for f in rows if (f.last_review_at or 0) >= today_start
    }
    for ref in refs.values():
        if not in_play(ref):
            continue
        if ref.skill_id is not None and ref.skill_id not in introduced:
            continue
        if ref.kind == "cloze":
            if ref.id in busy:
                continue
            card = storage.packs.card(ref.id)
            blanks = [
                o for o in cloze_ords(card.text_md if card else None) if (ref.id, o) not in seen
            ]
            if blanks:
                out.append((ref.id, blanks[0], ref.skill_id))
                new.add((ref.id, blanks[0]))
        elif (ref.id, 0) not in seen:
            out.append((ref.id, 0, ref.skill_id))
            new.add((ref.id, 0))
    return Deck(due=tuple(out), new=frozenset(new), leeches=leeches)
