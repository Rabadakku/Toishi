"""IMP-3: Anki's plain-text export and other delimited text, read as Anki reads them."""

from pathlib import Path

import pytest

from core.importers.anki import AnkiImportError, plan_anki_import, read_package, read_text
from core.importers.anki.model import AnkiData
from core.importers.anki.text_export import parse_csv
from core.storage import UserStore
from tests.importers.conftest import fixture
from tests.importers.oracle import collection


def notes(data: AnkiData) -> list[tuple[str, tuple[str, ...], tuple[str, ...], str | None]]:
    return [
        (data.notetypes[n.notetype_id].name, n.fields, tuple(sorted(n.tags)), n.deck)
        for n in data.notes
    ]


def test_anki_export_with_every_header_column() -> None:
    data = read_text(fixture("notes.txt"))
    assert [n[0] for n in notes(data)] == [
        "Basic", "Basic (and reversed card)", "Basic (optional reversed card)",
        "Basic (optional reversed card)", "Basic (type in the answer)", "Basic",
    ]  # fmt: skip
    hola = data.notes[0]
    assert hola.fields == ('Hola <img src="pic.png">', "Hello &amp; welcome<br>[sound:sound.mp3]")
    assert (hola.tags, hola.deck) == (("es::basics", "greeting"), "Lang::Spanish")
    assert data.notes[-1].deck == "Lang::Math"
    package = read_package(fixture("basic.apkg"))
    assert {n.guid for n in data.notes} == {n.guid for n in package.notes}


def test_text_export_and_package_give_the_same_cards(store: UserStore) -> None:
    text = plan_anki_import(store, read_text(fixture("notes.txt"))).cards
    package = plan_anki_import(store, read_package(fixture("basic.apkg"))).cards
    assert {c.card.id for c in text.added} == {c.card.id for c in package.added}
    by_id = {c.card.id: c.card for c in package.added}
    for change in text.added:
        assert change.card.front_md == by_id[change.card.id].front_md


def test_headerless_two_columns_are_basic_flashcards(store: UserStore) -> None:
    data = read_text("front 1\tback 1\nfront 2\tback 2 & 3\n", name="vocab.txt")
    assert notes(data) == [
        ("Basic", ("front 1", "back 1"), (), "vocab"),
        ("Basic", ("front 2", "back 2 &amp; 3"), (), "vocab"),  # no tags: not HTML, escaped
    ]
    assert read_text("a\tb <2>\n").notes[0].fields == ("a", "b <2>")  # a "tag": HTML
    plan = plan_anki_import(store, data).cards
    assert [c.card.kind for c in plan.added] == ["flashcard", "flashcard"]
    assert plan.added[1].card.back_md == '<div class="anki-card card1">back 2 &amp; 3</div>'
    assert [c.line for c in plan.added] == [1, 2]


def test_third_column_is_tags_as_in_anki() -> None:
    data = read_text("a,b,t1 t2\nc,d\n")
    assert notes(data) == [
        ("Basic", ("a", "b"), ("t1", "t2"), "notes"),
        ("Basic", ("c", "d"), (), "notes"),
    ]


def test_header_lines() -> None:
    text = (
        "#separator:Comma\n#html:true\n#tags:g1 g2\n#deck:Spanish::Verbs\n"
        "#notetype:Basic (and reversed card)\n#columns:Back,Front\n"
        "<b>to be</b>,ser\n"
    )
    data = read_text(text)
    assert notes(data) == [
        ("Basic (and reversed card)", ("ser", "<b>to be</b>"), ("g1", "g2"), "Spanish::Verbs")
    ]


def test_old_tags_line_bom_and_separator_by_character() -> None:
    data = read_text("﻿tags:old\n#separator:;\na;b\n")
    assert notes(data) == [("Basic", ("a", "b"), ("old",), "notes")]
    assert data.notes[0].line == 3


def test_quotes_comments_blank_lines_and_crlf() -> None:
    text = '"q1\r\nstill"\tb\r\n#comment\r\n\r\nc\t"d""x"\r\n"e"f\tg\r\n'
    data = read_text(text)
    assert notes(data) == [
        ("Basic", ("q1<br>still", "b"), (), "notes"),
        ("Basic", ("c", "d&quot;x"), (), "notes"),
        ("Basic", ("ef", "g"), (), "notes"),
    ]
    assert [n.line for n in data.notes] == [1, 5, 6]


def test_delimiter_detection_order() -> None:
    assert parse_csv("a|b;c", "|") == [(1, ["a", "b;c"])]
    assert read_text("a;b|c\n").notes[0].fields == ("a;b", "c")
    assert read_text("a b\n").notes[0].fields == ("a", "b")


def test_cloze_and_guid_columns(store: UserStore) -> None:
    text = (
        "#separator:tab\n#html:true\n#guid column:1\n#notetype column:2\n#deck column:3\n"
        "#tags column:6\nG1\tCloze\tD::E\t{{c1::x}} {{c2::y}}\textra\tt\n"
    )
    data = read_text(text)
    assert notes(data) == [("Cloze", ("{{c1::x}} {{c2::y}}", "extra"), ("t",), "D::E")]
    plan = plan_anki_import(store, data).cards
    [card] = [c.card for c in plan.added]
    assert (card.kind, card.deck, card.extra_md) == (
        "cloze",
        "D::E",
        '<div class="anki-card">extra</div>',
    )


def test_rows_with_an_empty_first_field_are_skipped() -> None:
    data = read_text("\tb\nc\td\n")
    assert [n.fields for n in data.notes] == [("c", "d")]
    assert data.warnings == ["notes.txt:1: skipped: the first field is empty"]


def test_unknown_note_type_falls_back_to_front_and_back(store: UserStore) -> None:
    data = read_text("#notetype:My Vocab\nword\tmeaning\tnote\n")
    assert any("'My Vocab' is unknown" in w for w in data.warnings)
    plan = plan_anki_import(store, data).cards
    [card] = [c.card for c in plan.added]
    assert card.front_md == '<div class="anki-card card1">word</div>'
    assert card.back_md == '<div class="anki-card card1"><div>meaning</div><div>note</div></div>'


def test_mastery_problem_from_text(store: UserStore) -> None:
    text = (
        "#separator:tab\n#html:false\n#notetype:Mastery Problem\n"
        "#columns:ID\tAnswerType\tAnswer\tQuestion\tSolution\tSkill\n"
        "t.001\tnumber\t4\tWhat is \\(2 + 2\\)?\t0. [s.add] Add: \\(2 + 2 = 4\\).\ts.add\n"
    )
    plan = plan_anki_import(store, read_text(text, name="problems.txt")).cards
    [card] = [c.card for c in plan.added]
    assert (card.id, card.answer, card.question_md, card.deck) == (
        "t.001", "4", "What is \\(2 + 2\\)?", "problems",
    )  # fmt: skip


def test_not_utf8_or_empty() -> None:
    with pytest.raises(AnkiImportError, match="not UTF-8"):
        read_text(b"\xff\xfe\x00a")
    with pytest.raises(AnkiImportError, match="no notes"):
        read_text("#separator:tab\n")


TRICKY = (
    '#separator:tab\n#html:false\n#tags:global\n"a ""quoted""\nline"\tb & <c>\tt1\n'
    '#comment line\n\nd\te\n\'single\'\t"x"y\n"crlf\r\nin quotes"\tz\x01\r\n'
)


def test_parity_with_ankis_own_text_import(tmp_path: Path) -> None:
    from anki.collection import ImportCsvRequest

    path = tmp_path / "tricky.txt"
    path.write_bytes(TRICKY.encode())
    ours = read_text(path)
    with collection() as col:
        meta = col.get_csv_metadata(str(path), delimiter=None)
        col.import_csv(ImportCsvRequest(path=str(path), metadata=meta))
        theirs = []
        for nid in sorted(col.find_notes("")):
            note = col.get_note(nid)
            theirs.append((tuple(note.fields), tuple(sorted(note.tags))))
    assert [(n.fields, tuple(sorted(n.tags))) for n in ours.notes] == theirs
