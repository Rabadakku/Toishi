"""Randomized parity with the anki package: random templates and cloze texts, drawn by Anki
and by our port, must match (slow; runs in full mode)."""

import random
from typing import Any

import pytest

from core.importers.anki.template import TemplateError, card_fields, render_card
from tests.importers.oracle import collection, full_render, same_hint

AnkiTemplateError = pytest.importorskip("anki.errors").TemplateError

pytestmark = pytest.mark.slow

PIECES = [
    "{{Front}}", "{{Back}}", "{{text:Front}}", "{{hint:Back}}", "{{#Back}}", "{{/Back}}",
    "{{^Front}}", "{{/Front}}", "{{cloze:Front}}", "{{cloze-only:Back}}", "{{kana:Front}}",
    "{{furigana:Back}}", "{{type:Back}}", "{{Tags}}", "{{Deck}}", "{{Card}}", "{{#c1}}",
    "{{/c1}}", "<!-- {{x}} -->", "<br>", " ", "x", "{{", "}}", "{{tts fr_FR:Front}}",
]  # fmt: skip
TEXT = ["a", " ", "<br>", "<b>", "</b>", "&amp;", "&", "{{c1::", "{{c2::", "}}", "::h",
        "\\(", "\\)", "日本[にほん]", "[sound:x.mp3]", "<div>", "</div>", "é", "\""]  # fmt: skip


def _saved(col: Any, model: Any) -> bool:
    try:
        col.models.update_dict(model)
    except Exception:  # TemplateError, CardTypeError, ...: Anki won't save it
        return False
    return True


def _random(rng: random.Random, parts: list[str], n: int) -> str:
    return "".join(rng.choice(parts) for _ in range(rng.randint(0, n)))


def test_random_templates_and_fields_match_anki() -> None:
    rng = random.Random(20261101)  # noqa: S311 - reproducible test data
    compared = 0
    with collection() as col:
        base = col.models.by_name("Basic")
        for i in range(600):
            qfmt = "{{Front}}" + _random(rng, PIECES, 6)
            afmt = "{{FrontSide}}" + _random(rng, PIECES, 6)
            model = col.models.copy(base)
            model["name"] = f"F{i}"
            model["tmpls"][0]["qfmt"], model["tmpls"][0]["afmt"] = qfmt, afmt
            if not _saved(col, model):
                continue  # Anki refuses some templates at save time: nothing to compare
            model = col.models.by_name(f"F{i}")
            for _ in range(5):
                front, back = "x" + _random(rng, TEXT, 8), _random(rng, TEXT, 8)
                note = col.new_note(model)
                note["Front"], note["Back"] = front, back
                col.add_note(note, 1)
                card = note.cards()[0]
                fields = card_fields({"Front": note["Front"], "Back": note["Back"]}, card_ord=0,
                                     notetype=f"F{i}", deck="Default", template_name="Card 1",
                                     card_id=card.id)  # fmt: skip
                try:
                    q, a, empty = full_render(col, card.id)
                except AnkiTemplateError:
                    with pytest.raises(TemplateError):
                        render_card(qfmt, afmt, fields, card_ord=0, is_cloze=False)
                    compared += 1
                    continue
                mine = render_card(qfmt, afmt, fields, card_ord=0, is_cloze=False,
                                   hint_style="anki")  # fmt: skip
                assert mine.empty == empty, (qfmt, afmt, front, back)
                if not empty:
                    assert same_hint(mine.question) == same_hint(q), (qfmt, front, back)
                    assert same_hint(mine.answer) == same_hint(a), (afmt, front, back)
                compared += 1
    assert compared > 500


def test_random_cloze_texts_match_anki() -> None:
    rng = random.Random(7)  # noqa: S311 - reproducible test data
    compared = 0
    with collection() as col:
        model = col.models.by_name("Cloze")
        template = model["tmpls"][0]
        for _ in range(1500):
            text = "{{c1::a}}" + _random(rng, TEXT, 12)
            note = col.new_note(model)
            note["Text"] = text
            col.add_note(note, 1)
            text = note["Text"]  # Anki may normalize what it stores
            for card in note.cards():
                q, a, empty = full_render(col, card.id)
                fields = card_fields({"Text": text, "Back Extra": ""}, card_ord=card.ord,
                                     notetype="Cloze", template_name="Cloze",
                                     card_id=card.id)  # fmt: skip
                mine = render_card(template["qfmt"], template["afmt"], fields,
                                   card_ord=card.ord, is_cloze=True)  # fmt: skip
                assert mine.empty == empty, (text, card.ord)
                if not empty:
                    assert (mine.question, mine.answer) == (q, a), (text, card.ord)
                compared += 1
    assert compared > 1500
