"""Imported Anki cloze cards are HTML: their answers are revealed Anki's way, never as
Markdown `**x**`, which an HTML card would show as literal asterisks."""

from core.importers.anki.mapping import ANKI_HTML_CLASS
from core.queue.cloze import back, front

HTML = f'<div class="{ANKI_HTML_CLASS}">{{{{c1::Paris::city}}}} is in {{{{c2::France}}}}</div>'


def test_an_anki_html_cloze_marks_its_answer_with_a_cloze_span_not_asterisks() -> None:
    answer = back(HTML, 0)
    assert "**" not in answer
    assert answer.startswith(f'<div class="{ANKI_HTML_CLASS}">')
    assert '<span class="cloze" data-ordinal="1">Paris</span>' in answer
    assert '<span class="cloze-inactive" data-ordinal="2">France</span>' in answer
    question = front(HTML, 0)
    assert "**" not in question
    assert "Paris" not in question.replace('data-cloze="Paris"', "")
    assert "[city]" in question
    assert "France" in question


def test_a_pack_cloze_keeps_markdown() -> None:
    text = "{{c1::Paris::city}} is in {{c2::France}}"
    assert back(text, 0) == "**Paris** is in France"
    assert front(text, 1) == "Paris is in [...]"
