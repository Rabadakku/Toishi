"""IMP-5: every Anki import is a dry run first, then one transaction; GUIDs keep re-imports
idempotent; nothing is deleted."""

from dataclasses import replace

import pytest

from core.importers.anki import (
    apply_anki_import,
    plan_anki_import,
    read_anki_file,
    read_package,
    read_text,
)
from core.model import Attempt, GradedAnswer
from core.storage import UserStore
from core.storage.media import media_file_name
from tests.importers.conftest import fixture

ALL = ["basic.apkg", "basic-legacy.apkg", "cloze.apkg", "custom.apkg", "mastery.apkg",
       "history.apkg", "history.colpkg", "notes.txt"]  # fmt: skip


def test_the_dry_run_writes_nothing(store: UserStore) -> None:
    plan = plan_anki_import(store, read_package(fixture("history.apkg")))
    assert len(plan.cards.added) == 5
    assert plan.history.review_count == 17
    assert store.user_cards() == []
    assert store.review_events() == []
    assert store.imports() == []
    assert store.media.all_links() == []


def test_apply_stores_cards_media_revisions_and_the_log(store: UserStore) -> None:
    data = read_package(fixture("basic.apkg"))
    plan = plan_anki_import(store, data)
    result = apply_anki_import(store, plan)
    cards = {c.id: c for c in store.user_cards()}
    assert len(cards) == 8
    assert all(c.verified == "unverified" for c in cards.values())
    hola = next(c for c in cards.values() if "Hola" in (c.front_md or ""))
    links = store.media.links(hola.id)
    assert set(links) == {"pic.png", "sound.mp3"}
    assert links["pic.png"] == media_file_name(data.media.read("pic.png"), "pic.png")
    assert store.media.read(hola.id, "pic.png") == data.media.read("pic.png")
    assert (result.record.kind, result.record.file) == ("apkg", "basic.apkg")
    assert result.record.summary["anki"]["notes"] == 6
    assert set(result.record.summary["files"]["basic.apkg"]["ids"]) == set(cards)
    assert store.media.problems() == []


def test_the_import_is_one_transaction(store: UserStore, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = plan_anki_import(store, read_package(fixture("history.apkg")))
    calls = {"n": 0}
    original = UserStore.record_answer

    def flaky(self: UserStore, answer: GradedAnswer) -> Attempt:
        calls["n"] += 1
        if calls["n"] == 10:
            raise RuntimeError("power cut")
        return original(self, answer)

    monkeypatch.setattr(UserStore, "record_answer", flaky)
    with pytest.raises(RuntimeError, match="power cut"):
        apply_anki_import(store, plan)
    assert store.user_cards() == []
    assert store.review_events() == []
    assert store.attempts() == []
    assert store.imports() == []
    assert store.flashcard_states() == []


@pytest.mark.parametrize("name", ALL)
def test_importing_again_changes_nothing(store: UserStore, name: str) -> None:
    first = plan_anki_import(store, read_anki_file(fixture(name)))
    apply_anki_import(store, first)
    cards, events = store.user_cards(), store.review_events()
    again = plan_anki_import(store, read_anki_file(fixture(name)))
    assert again.nothing_to_do, again.report()
    assert len(again.cards.unchanged) == len(first.cards.added)
    apply_anki_import(store, again)
    assert store.user_cards() == cards
    assert store.review_events() == events


def test_a_changed_note_updates_its_cards_and_keeps_their_id(store: UserStore) -> None:
    data = read_package(fixture("basic.apkg"))
    apply_anki_import(store, plan_anki_import(store, data))
    perro = next(n for n in data.notes if n.fields[0] == "perro")
    data.notes[data.notes.index(perro)] = replace(perro, fields=("perro", "dog (animal)"))
    plan = plan_anki_import(store, data)
    assert len(plan.cards.updated) == 2  # both directions of the reversed note
    assert len(plan.cards.unchanged) == 6
    assert all(c.card.rev == 2 and not c.key_changed for c in plan.cards.updated)
    apply_anki_import(store, plan)
    updated = store.user_card(plan.cards.updated[0].card.id)
    assert updated is not None
    assert "dog (animal)" in (updated.front_md or "") + (updated.back_md or "")


def test_notes_gone_from_a_file_are_listed_never_deleted(store: UserStore) -> None:
    apply_anki_import(store, plan_anki_import(store, read_text("a\tb\nc\td\n", name="v.txt")))
    plan = plan_anki_import(store, read_text("a\tb\n", name="v.txt"))
    assert len(plan.cards.missing) == 1
    assert "no longer in the file" in plan.report()
    apply_anki_import(store, plan, retire=plan.cards.missing)
    retired = store.user_card(plan.cards.missing[0])
    assert retired is not None
    assert retired.status == "retired"


def test_ids_used_by_a_pack_are_rejected(store: UserStore) -> None:
    data = read_text("a\tb\n", name="v.txt")
    card_id = plan_anki_import(store, data).cards.added[0].card.id
    plan = plan_anki_import(store, data, pack_cards={card_id: "calc1"})
    assert [r.reasons[0] for r in plan.cards.rejected] == [
        f"ID {card_id} is already used by pack calc1"
    ]


def test_rejections_report_file_line_and_reason(store: UserStore) -> None:
    plan = plan_anki_import(store, read_package(fixture("mastery.apkg")))
    report = plan.report()
    assert "added: 1  updated: 0  unchanged: 0  rejected: 2" in report
    assert "mastery.apkg:2: anki.mp.002 rejected: answer 'x +'" in report
    assert "mastery.apkg:3: card rejected: a Mastery Problem note needs its ID field" in report


def test_a_text_export_after_the_package_keeps_the_images(store: UserStore) -> None:
    apply_anki_import(store, plan_anki_import(store, read_package(fixture("basic.apkg"))))
    links = {link.card_id: link for link in store.media.all_links()}
    plan = plan_anki_import(store, read_text(fixture("notes.txt")))
    assert plan.cards.media_changed == []
    assert plan.nothing_to_do
    apply_anki_import(store, plan)
    assert {link.card_id: link for link in store.media.all_links()} == links


def test_text_import_logs_its_kind(store: UserStore) -> None:
    result = apply_anki_import(store, plan_anki_import(store, read_text("a\tb\n", name="v.txt")))
    assert result.record.kind == "anki-text"
