"""Anki notes -> cards (card-format "Anki compatibility"), sanitized HTML and scoped CSS."""

import pytest

from core.cards import ImportPlan
from core.importers.anki import (
    is_anki_html,
    note_key,
    plan_anki_import,
    read_package,
    sanitize_html,
    scope_css,
)
from core.importers.anki.media import normalize_filename
from core.importers.anki.sanitize import scope_selector
from core.model import Card, Course, Section, Unit
from core.queue.cloze import ords as queue_ords
from core.storage import UserStore
from tests.importers.conftest import fixture


def planned(store: UserStore, name: str) -> tuple[ImportPlan, dict[str, Card]]:
    plan = plan_anki_import(store, read_package(fixture(name))).cards
    return plan, {c.card.id: c.card for c in plan.added}


def key_of(name: str, field: str) -> str:
    """The note key of the note whose first field is `field`."""
    data = read_package(fixture(name))
    return note_key(next(n.guid for n in data.notes if n.fields[0].startswith(field)))


def test_basic_note_types_become_one_flashcard_per_anki_card(store: UserStore) -> None:
    plan, cards = planned(store, "basic.apkg")
    assert len(cards) == 8
    assert not plan.rejected
    perro, gato, casa = (key_of("basic.apkg", w) for w in ("perro", "gato", "casa"))
    assert {f"anki.{perro}.1", f"anki.{perro}.2", f"anki.{gato}.1", f"anki.{gato}.2"} <= set(cards)
    assert f"anki.{casa}.2" not in cards  # optional reverse left empty: Anki made one card
    reverse = cards[f"anki.{perro}.2"]
    assert reverse.kind == "flashcard"
    assert reverse.front_md == '<div class="anki-card card2">dog</div>'
    assert reverse.back_md == '<div class="anki-card card2">perro</div>'
    assert all(c.verified == "unverified" and c.provenance.source == "anki" for c in cards.values())


def test_tags_decks_and_the_course_tree(store: UserStore) -> None:
    plan, cards = planned(store, "basic.apkg")
    hola = cards[f"anki.{key_of('basic.apkg', 'Hola')}.1"]
    assert (hola.deck, hola.section_id, hola.tags) == (
        "Lang::Spanish", "Lang::Spanish", ("es::basics", "greeting"),
    )  # fmt: skip
    tree = {(type(r).__name__, r.id) for r in plan.tree}
    assert {("Course", "Lang"), ("Unit", "Lang::Spanish"), ("Unit", "Lang::Math")} <= tree
    assert all(isinstance(r, Course | Unit | Section) for r in plan.tree)


def test_media_is_found_normalized_and_planned(store: UserStore) -> None:
    plan, cards = planned(store, "basic.apkg")
    hola = f"anki.{key_of('basic.apkg', 'Hola')}.1"
    assert set(plan.media[hola]) == {"pic.png", "sound.mp3"}
    assert '<audio controls="" src="sound.mp3"></audio>' in (cards[hola].back_md or "")
    math = next(c for c in cards.values() if c.deck == "Lang::Math")
    assert set(plan.media[math.id]) == {"café.png"}


def test_scripts_handlers_and_links_are_stripped(store: UserStore) -> None:
    _, cards = planned(store, "basic.apkg")
    math = next(c for c in cards.values() if c.deck == "Lang::Math")
    assert math.front_md == '<div class="anki-card card1"><b>Square</b> \\(x^2\\)</div>'
    assert math.back_md == '<div class="anki-card card1"><img src="café.png"> <a>link</a></div>'


def test_type_in_answers_show_the_answer_on_the_back(store: UserStore) -> None:
    _, cards = planned(store, "basic.apkg")
    typed = cards[f"anki.{key_of('basic.apkg', '2 + 2')}.1"]
    assert typed.front_md == '<div class="anki-card card1">2 + 2</div>'
    assert typed.back_md == '<div class="anki-card card1">cuatro</div>'
    assert typed.answer is None  # typing in Anki is self-graded too


def test_stock_cloze_is_one_cloze_card_with_an_item_per_blank(store: UserStore) -> None:
    _plan, cards = planned(store, "cloze.apkg")
    paris = cards[f"anki.{key_of('cloze.apkg', '{{c1::Paris')}"]
    assert paris.kind == "cloze"
    assert paris.text_md == (
        '<div class="anki-card">{{c1::Paris::city}} is the capital of {{c2::France}}.</div>'
    )
    assert paris.extra_md == '<div class="anki-card"><i>Europe</i></div>'
    assert queue_ords(paris.text_md) == [0, 1]  # the queue serves one item per blank
    assert paris.tags == ("capitals",)


def test_a_customized_cloze_type_renders_with_its_own_templates(store: UserStore) -> None:
    plan, cards = planned(store, "cloze.apkg")
    key = key_of("cloze.apkg", "{{c1::Rome")
    first, second = cards[f"anki.{key}.1"], cards[f"anki.{key}.2"]
    assert first.kind == second.kind == "flashcard"
    assert '<span class="cloze" data-cloze="Rome" data-ordinal="1">[...]</span>' in (
        first.front_md or ""
    )
    assert "data-anki-css=" in (first.front_md or "")
    css_ref = next(ref for ref in plan.media[first.id] if ref.endswith(".css"))
    assert b".src { font-size: 12px; }" in plan.media[first.id][css_ref]


def test_custom_note_type_keeps_templates_and_scoped_css(store: UserStore) -> None:
    plan, cards = planned(store, "custom.apkg")
    assert len(cards) == 3  # the note with an empty Meaning has no Recall card, as in Anki
    key = key_of("custom.apkg", "日本")
    recognize, recall = cards[f"anki.{key}.1"], cards[f"anki.{key}.2"]
    front = recognize.front_md or ""
    assert front.startswith('<div class="anki-card card1 anki-nt-')
    assert "<script" not in front
    assert "pwned" not in front
    assert "<style" not in front
    assert '<details class="hint"><summary>Example</summary>日本に行く</details>' in front
    assert (recall.front_md or "").endswith(">Japan</div>")
    assert "<ruby><rb>日本</rb><rt>にほん</rt></ruby>" in (recall.back_md or "")
    css_ref = next(r for r in plan.media[recognize.id] if r.endswith(".css"))
    scope = css_ref.removeprefix("_").removesuffix(".css")
    css = plan.media[recognize.id][css_ref].decode()
    assert "@import" not in css
    assert "evil.example" not in css
    assert f'.{scope} {{ font-family: "MyFont"; background: url(_bg.png); color: #222; }}' in css
    assert f".{scope}.anki-night {{ color: white; }}" in css
    assert f".{scope} .word {{ font-size: 40px; }}" in css  # a template's <style> block
    assert "@media (max-width: 600px)" in css
    assert f".{scope} .ex" in css
    assert {"_font.woff", "_bg.png", "sound.mp3"} <= set(plan.media[recognize.id])
    warnings = [w.message for w in plan.warnings]
    assert any("'unknownfilter' is not supported" in w for w in warnings)


def test_mastery_problem_maps_field_by_field(store: UserStore) -> None:
    plan, cards = planned(store, "mastery.apkg")
    card = cards["anki.mp.001"]
    assert (card.kind, card.skill_id, card.tier, card.answer_type, card.answer) == (
        "problem", "alg.linear", 2, "number", "3",
    )  # fmt: skip
    assert card.question_md == "Solve \\(2x + 1 = 7\\).\nGive \\(x\\).\n![](graph.png)"
    assert card.hints == ("Subtract 1 from both sides.", "Divide by 2.")
    assert card.solution[0].skill_id == "alg.linear"
    assert card.solution[0].label == "Isolate"
    assert [(w.answer, w.feedback) for w in card.wrong] == [("6", "forgot to divide by 2")]
    assert card.checker.tolerance == "0"
    assert card.calculator is False
    assert (card.deck, card.provenance.source, card.provenance.license) == (
        "Algebra::Linear", "original", "personal",
    )  # fmt: skip
    assert set(plan.media["anki.mp.001"]) == {"graph.png"}
    rejected = {(r.card_id, r.line, r.reasons[0]) for r in plan.rejected}
    assert ("anki.mp.002", 2, "answer 'x +': x isn't a variable in this problem.") in rejected
    assert (None, 3, "a Mastery Problem note needs its ID field") in rejected
    assert any(s.id == "alg.linear" for s in plan.skills_created)


def test_is_anki_html() -> None:
    assert is_anki_html('<div class="anki-card card1">x</div>')
    assert not is_anki_html("Plain *markdown*")
    assert not is_anki_html(None)


# ---------------------------------------------------------------- sanitizer and CSS


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<b onclick='x()' onmouseover=y>b</b>", "<b>b</b>"),
        ("<a href='javascript:alert(1)' title=t>l</a>", '<a title="t">l</a>'),
        ("<img src=x onerror=alert(1)>", '<img src="x">'),
        ("<img src='https://evil/x.png'><img src='data:image/png;base64,AA'>", ""),
        ("<iframe src=x>in</iframe><svg><script>s</script></svg>ok", "ok"),
        ("<div style='color:red; background:url(http://x/y.png)'>t</div>",
         '<div style="color:red">t</div>'),
        ("<div style='width: expression(alert(1))'>t</div>", "<div>t</div>"),
        ("<p id=answer class=c data-ordinal=2>t", '<p class="c" data-ordinal="2">t</p>'),
        ("&lt;tag&gt; &amp; <!-- c --><br/>", "&lt;tag&gt; &amp; <br>"),
        ("[sound:a b.mp3][sound:v.mp4]",
         '<audio controls="" src="a b.mp3"></audio><video controls="" src="v.mp4"></video>'),
        ("[anki:tts lang=en_US]spoken[/anki:tts] [[type:Back]]", "spoken "),
        ("<object data=x></object><form><input value=1>t</form>", "t"),
        ("<unknown>kept text</unknown>", "kept text"),
    ],
)  # fmt: skip
def test_sanitize_html(html: str, expected: str) -> None:
    assert sanitize_html(html).html == expected


def test_sanitized_media_names_are_normalized() -> None:
    out = sanitize_html('<img src="café.png"><img src="a:b.png">')
    assert out.media == ["café.png"]


@pytest.mark.parametrize(
    ("selector", "scoped"),
    [
        (".card", ".S"),
        ("body", ".S"),
        (".nightMode .card", ".S.anki-night"),
        (".card.nightMode b", ".S.anki-night b"),
        (".card1 .x", ".S.card1 .x"),
        (".card > b", ".S > b"),
        ("div.x:hover", ".S div.x:hover"),
        (".card::before", ".S::before"),
        ("*", ".S *"),
    ],
)
def test_scope_selector(selector: str, scoped: str) -> None:
    assert scope_selector(selector, "S") == scoped


def test_kept_at_rules_lose_remote_urls() -> None:
    out = scope_css("@keyframes k { from { background: url(https://e/x.png) } } "
                    "@keyframes ok { from { opacity: 0 } to { opacity: 1 } }", "S")  # fmt: skip
    assert out.css == "@keyframes ok { from { opacity: 0 } to { opacity: 1 } }\n"


def test_scope_css_drops_imports_remote_urls_and_code() -> None:
    out = scope_css(
        '@import "x.css"; @charset "utf-8"; .a, .card { color: red; x: url(https://e/f) }'
        " .b { behavior: url(x.htc); top: 0 } @font-face { src: url(_f.woff) }"
        " @media print { .c { d: e } } @unknown { .z { y: 1 } }",
        "S",
    )
    assert out.css == (
        ".S .a, .S { color: red; }\n.S .b { top: 0; }\n@font-face {src: url(_f.woff)}\n"
        "@media print {\n.S .c { d: e; }\n}\n"
    )
    assert out.media == ["_f.woff"]


@pytest.mark.parametrize(
    ("name", "normalized"),
    [
        ("café.png", "café.png"),
        ('a<b>:c"d/e\\f|g?h*i^j[k].png', "abcdefghijk.png"),
        ("CON.txt", "CON_.txt"),
        ("lpt1", "lpt1_"),
        ("trailing.", "trailing._"),
        ("a\xa0b.png", "a b.png"),
        ("x" * 200 + ".png", "x" * 115 + ".png"),
    ],
)
def test_media_names_like_anki(name: str, normalized: str) -> None:
    assert normalize_filename(name) == normalized
    assert len(normalize_filename(name).encode()) <= 120
