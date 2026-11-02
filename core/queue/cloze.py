"""Cloze cards, Anki's way (card-format "Kinds": scheduled per blank). A card's text marks
blanks `{{c1::answer}}` or `{{c1::answer::hint}}`; every blank number is its own schedulable
item, stored as FlashcardState.ord = number - 1 (Anki's card ord, so ord 0 is c1). The item
for blank n shows the text with every c<n> blank hidden ("[...]", or "[hint]") and the
others filled in; its back shows the text with the c<n> answers marked.

Parsing is Anki's (core.importers.anki.cloze, a port of rslib's cloze.rs, ADR-0015):
several numbers on one blank (`{{c1,2::x}}`), nested blanks, and MathJax-aware closing.
A pack card's text is Markdown, so its answers are marked `**x**`; an imported Anki card's
text is sanitized HTML (ADR-0017), drawn as HTML, so it is revealed Anki's way instead
(`<span class="cloze">`, styled by the note type's CSS), never with literal asterisks.
"""

from core.importers.anki.cloze import (
    Cloze,
    UnsupportedCloze,
    cloze_numbers,
    parse,
    reveal_cloze_text,
)
from core.importers.anki.mapping import is_anki_html


def blank_numbers(text: str | None) -> list[int]:
    """The blank numbers in a cloze text, in order (c1 -> 1)."""
    return sorted(cloze_numbers(text or ""))


def ords(text: str | None) -> list[int]:
    """Schedulable items of a cloze card: ord = blank number - 1."""
    return [n - 1 for n in blank_numbers(text)]


def front(text: str | None, ord_: int) -> str:
    """The question side of blank ord + 1."""
    return _render(text, ord_ + 1, question=True)


def back(text: str | None, ord_: int) -> str:
    """The answer side of blank ord + 1: its answers in bold, the other blanks filled in."""
    return _render(text, ord_ + 1, question=False)


def _render(text: str | None, number: int, *, question: bool) -> str:
    if is_anki_html(text):
        try:
            revealed = reveal_cloze_text(text or "", number, question)
        except UnsupportedCloze:
            revealed = ""
        if revealed:
            return revealed

    def node(n: str | Cloze) -> str:
        if isinstance(n, str):
            return n
        inner = "".join(node(c) for c in n.nodes)
        if number not in n.ordinals:
            return inner
        if question:
            return f"[{n.hint}]" if n.hint else "[...]"
        return f"**{inner}**"

    return "".join(node(n) for n in parse(text or ""))
