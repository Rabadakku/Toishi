"""IMP-8: the template renderer is a port of Anki's rules, checked against the anki package."""

import pytest

from core.importers.anki import read_package
from core.importers.anki.cloze import cloze_numbers, reveal_cloze_text, reveal_cloze_text_only
from core.importers.anki.htmltext import decode_entities, encode_attribute, field_is_empty
from core.importers.anki.mapping import note_key
from core.importers.anki.template import TemplateError, card_fields, parse, render_card
from tests.importers.conftest import fixture
from tests.importers.oracle import (
    av_tags,
    collection,
    full_render,
    import_package,
    same_hint,
)


def render(qfmt: str, afmt: str = "{{FrontSide}}", **fields: str) -> tuple[str, str, bool]:
    out = render_card(qfmt, afmt, card_fields(fields, card_ord=0), card_ord=0, is_cloze=False)
    return out.question, out.answer, out.empty


# ---------------------------------------------------------------- the rules, one by one


def test_empty_field_is_whitespace_br_and_div_only() -> None:
    assert field_is_empty("")
    assert field_is_empty(" <br> <div></div>\n<BR/>")
    assert not field_is_empty("x")
    assert not field_is_empty("\xa0")  # a non-breaking space is content to Anki
    assert not field_is_empty("<p></p>")


def test_conditionals_follow_the_empty_rule() -> None:
    q, _, _ = render("{{Front}}{{#Back}}[{{Back}}]{{/Back}}{{^Back}}(none){{/Back}}",
                     Front="a", Back="<br>")  # fmt: skip
    assert q == "a(none)"


def test_filters_apply_right_to_left() -> None:
    q, _, _ = render("{{text:cloze:Text}}", Text="<b>{{c1::x}}</b> y")
    assert q == "[...] y"  # cloze first, then text strips the markup it made


def test_frontside_is_the_rendered_question() -> None:
    q, a, _ = render("<i>{{Front}}</i>", "{{FrontSide}}<hr id=answer>{{Back}}", Front="f", Back="b")
    assert (q, a) == ("<i>f</i>", "<i>f</i><hr id=answer>b")


def test_special_fields_never_hide_note_fields() -> None:
    fields = card_fields({"Deck": "mine"}, card_ord=1, tags=("t1", "t2"), notetype="NT",
                         deck="A::B", template_name="Card 2")  # fmt: skip
    out = render_card("{{Deck}} {{Subdeck}} {{Tags}} {{Type}} {{Card}} {{#c2}}c2{{/c2}}", "",
                      fields, card_ord=1, is_cloze=False)  # fmt: skip
    assert out.question == "mine B t1 t2 NT Card 2 c2"


def test_unknown_fields_and_bad_nesting_are_errors() -> None:
    with pytest.raises(TemplateError, match="no field named 'Nope'"):
        render("{{Nope}}", Front="x")
    with pytest.raises(TemplateError, match="missing"):
        parse("{{#Front}}x")
    with pytest.raises(TemplateError, match="without a matching"):
        parse("x{{/Front}}")


def test_comments_and_alternative_delimiters() -> None:
    q, _, _ = render("<!-- {{Nope}} -->{{Front}}", Front="x")
    assert q == "<!-- {{Nope}} -->x"
    q, _, _ = render("{{=<% %>=}}<%Front%> {{Front}}", Front="x")
    assert q == "x {{Front}}"


def test_empty_front_and_missing_cloze() -> None:
    assert render("{{Back}}", Front="x", Back="")[2]
    out = render_card("{{cloze:Text}}", "", card_fields({"Text": "{{c1::a}}"}, card_ord=1),
                      card_ord=1, is_cloze=True)  # fmt: skip
    assert out.empty


def test_hints_are_native_details_unless_asked_for_ankis_markup() -> None:
    q, _, _ = render("{{hint:Front}}", Front="psst")
    assert q == '<details class="hint"><summary>Front</summary>psst</details>'
    anki = render_card("{{hint:Front}}", "", {"Front": "psst"}, card_ord=0, is_cloze=False,
                       hint_style="anki")  # fmt: skip
    assert "onclick=" in anki.question
    assert "psst" in anki.question


def test_type_filters_as_anki_26_09() -> None:
    q, _, _ = render("{{type:Back}}|{{type:cloze:Back}}|{{type:nc:Back}}|{{type:ci:Back}}",
                     Back="b")  # fmt: skip
    assert q == "[[type:Back]]|[[type:cloze:Back]]|[[type:nc:Back]]|[[type:Back]]"


def test_cloze_numbering_nesting_hints_and_mathjax() -> None:
    text = r"{{c1::a {{c2::b}}::hint}} \(x{{c3::}}}\) {{c4,5::both}} {{c0::zero}}"
    assert cloze_numbers(text) == {1, 2, 3, 4, 5}  # c0 never counts
    assert reveal_cloze_text(text, 1, True).startswith('<span class="cloze" data-cloze="a&#x20;')
    assert "[hint]" in reveal_cloze_text(text, 1, True)
    assert reveal_cloze_text(text, 9, True) == ""
    assert reveal_cloze_text_only("{{c1::a}} {{c1::b::h}}", 1, True) == "..., h"


def test_entities_decode_like_htmlescape() -> None:
    assert decode_entities("&amp; &nbsp;&hellip;&#60;&#x3c;") == "&  …<<"
    assert decode_entities("a & b &amp;") == "a & b &amp;"  # one bad & keeps it all
    assert decode_entities("&check; &apos;") == "&check; &apos;"
    assert encode_attribute("a b<é€") == "a&#x20;b&lt;&#xE9;€"


# ---------------------------------------------------------------- parity with the anki package

TEMPLATES = [
    ("{{Front}}", "{{FrontSide}}<hr id=answer>{{Back}}"),
    ("{{#Back}}has {{Back}}{{/Back}}{{^Back}}none{{/Back}}", "{{FrontSide}}|{{text:Back}}"),
    ("{{hint:Back}} {{kana:Front}} {{kanji:Front}} {{furigana:Front}}",
     "{{type:Back}}{{type:nc:ci:Back}}{{foo:bar:Front}}{{tts en_US:Front}}"),
    ("<!-- {{Nope}} -->{{Front}}", "{{FrontSide}}{{cloze:Back}}{{cloze-only:Back}}"),
    ("{{=<% %>=}}<%Front%> <%#Back%>B<%/Back%>", "<%FrontSide%>"),
    ("{{{Front}}}", "{{ Front }}{{#Tags}}T:{{Tags}}{{/Tags}} {{Deck}} {{Subdeck}} {{Card}}"),
    ("{{text:}}{{Front}}{{#c1}}one{{/c1}}{{^c2}}not two{{/c2}}", "{{::Back}}{{type:cloze:Front}}"),
]  # fmt: skip
VALUES = [
    ("a", "b"),
    ("x", ""),
    ("<br> <div></div>", "z"),
    ("漢字[かんじ] x[sound:a.mp3]", "&nbsp;b&amp; & c"),
    ("{{c1::Paris::city}} {{c2::France}}", "<b>bold</b> &lt;x&gt; {{c1::q}}"),
]


@pytest.mark.parametrize("index", range(len(TEMPLATES)))
def test_templates_render_exactly_as_anki(index: int) -> None:
    qfmt, afmt = TEMPLATES[index]
    with collection() as col:
        model = col.models.copy(col.models.by_name("Basic"))
        model["name"] = "Probe"
        model["tmpls"][0]["qfmt"], model["tmpls"][0]["afmt"] = qfmt, afmt
        col.models.update_dict(model)
        model = col.models.by_name("Probe")
        for front, back in VALUES:
            note = col.new_note(model)
            note["Front"], note["Back"] = front, back
            note.tags = ["t1", "x::y"]
            col.add_note(note, col.decks.id("P::Q"))
            card = note.cards()[0]
            expected = full_render(col, card.id)
            fields = card_fields({"Front": front, "Back": back}, card_ord=0, tags=note.tags,
                                 notetype="Probe", deck="P::Q", template_name="Card 1",
                                 card_id=card.id)  # fmt: skip
            mine = render_card(qfmt, afmt, fields, card_ord=0, is_cloze=False, hint_style="anki")
            assert mine.empty == expected[2], (front, back)
            if not mine.empty:
                assert same_hint(mine.question) == same_hint(expected[0]), (front, back)
                assert same_hint(mine.answer) == same_hint(expected[1]), (front, back)


CLOZE_TEXTS = [
    "{{c1::Paris::city}} is in {{c2::France}}",
    "foo {{c1::bar {{c2::baz}}::qux}}",
    "{{c1,2::both}} {{c2,1,1::x}} {{c3::y}}",
    r"\({{c1::x}}^2\) and \[ {{c2::\frac{a}{b}}} \] and \(a}}b\) {{c3::q}}",
    '{{c1::<b>bold</b> & "q"}}',
    "a }} b {{c1::x",
    r"\( {{c1::x}} \) <b>\(y<i>z</i>\)</b> {{c2::{{c3::deep}}}}",
    "{{c0::zero}} {{c1::one}} {{c1::a::}} {{c2::::h}}",
]


def test_cloze_renders_exactly_as_anki() -> None:
    with collection() as col:
        stock = col.models.by_name("Cloze")
        custom = col.models.copy(stock)
        custom["name"] = "C2"
        custom["tmpls"][0]["qfmt"] = "{{cloze:Text}}|{{cloze-only:Text}}|{{text:cloze:Text}}"
        custom["tmpls"][0]["afmt"] = "{{cloze:Text}}|{{cloze-only:Text}}<br>{{Back Extra}}"
        col.models.update_dict(custom)
        checked = 0
        for model in (stock, col.models.by_name("C2")):
            for text in CLOZE_TEXTS:
                note = col.new_note(model)
                note["Text"], note["Back Extra"] = text, "extra"
                col.add_note(note, 1)
                template = model["tmpls"][0]
                for card in note.cards():
                    q, a, empty = full_render(col, card.id)
                    fields = card_fields({"Text": text, "Back Extra": "extra"}, card_ord=card.ord,
                                         notetype=model["name"], template_name=template["name"],
                                         card_id=card.id)  # fmt: skip
                    mine = render_card(template["qfmt"], template["afmt"], fields,
                                       card_ord=card.ord, is_cloze=True)  # fmt: skip
                    assert mine.empty == empty, (text, card.ord)
                    if not empty:
                        assert (mine.question, mine.answer) == (q, a), (text, card.ord)
                    checked += 1
        assert checked > 30


FIXTURE_DECKS = ["basic.apkg", "basic-legacy.apkg", "cloze.apkg", "custom.apkg", "mastery.apkg",
                 "history.apkg", "history.colpkg"]  # fmt: skip


@pytest.mark.parametrize("name", FIXTURE_DECKS)
def test_fixture_decks_render_as_in_anki(name: str) -> None:
    """Every card of every fixture deck, read by our reader and drawn by our renderer, is
    what Anki draws for it: the full render, and card.question() / card.answer()."""
    data = read_package(fixture(name))
    notes = {n.id: n for n in data.notes}
    with collection() as col:
        import_package(col, fixture(name))
        by_guid = {col.get_note(nid).guid: nid for nid in col.find_notes("")}
        assert data.cards
        for card in data.cards:
            note = notes[card.note_id]
            nt = data.notetypes[note.notetype_id]
            template = nt.templates[0] if nt.is_cloze else nt.templates[card.ord]
            anki_card = next(c for c in col.get_note(by_guid[note.guid]).cards()
                             if c.ord == card.ord)  # fmt: skip
            q, a, empty = full_render(col, anki_card.id)
            fields = card_fields(dict(zip(nt.fields, note.fields, strict=True)),
                                 card_ord=card.ord, tags=note.tags, notetype=nt.name,
                                 deck=card.deck, template_name=template.name,
                                 flags=card.flags, card_id=anki_card.id)  # fmt: skip
            mine = render_card(template.qfmt, template.afmt, fields, card_ord=card.ord,
                               is_cloze=nt.is_cloze, hint_style="anki")  # fmt: skip
            assert mine.empty == empty
            assert same_hint(mine.question) == same_hint(q), (name, note.guid, card.ord)
            assert same_hint(mine.answer) == same_hint(a), (name, note.guid, card.ord)
            style = f"<style>{nt.css}</style>"
            question = anki_card.question()
            assert same_hint(question) == same_hint(style + av_tags(mine.question, "q"))
            if av_tags(mine.question, "q") == mine.question:  # FrontSide holds no sounds
                assert same_hint(anki_card.answer()) == same_hint(style + av_tags(mine.answer, "a"))
            assert note_key(note.guid)  # every note gets a stable key


def test_unknown_filter_is_skipped_and_reported() -> None:
    out = render_card("{{myaddon:Front}}", "", {"Front": "x"}, card_ord=0, is_cloze=False)
    assert (out.question, out.unknown_filters) == ("x", ("myaddon",))
