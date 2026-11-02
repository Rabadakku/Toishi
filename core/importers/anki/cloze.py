"""Cloze deletions, ported from Anki's rslib/src/cloze.rs so imported decks render the same.

- `{{c1::text}}`, `{{c1::text::hint}}`, several ordinals `{{c1,2::text}}` (deduplicated and
  sorted), nesting up to ten deep.
- Inside MathJax `\\( \\)` / `\\[ \\]`, a `}}` closes only a cloze opened inside the same
  expression; an unterminated delimiter is plain text.
- A cloze left open at the end of the text is dropped, as in Anki.
- Image occlusion clozes (`image-occlusion:`) need Anki's own script; they raise
  `UnsupportedCloze` and the importer rejects the note.
"""

import re
from dataclasses import dataclass, field

from core.importers.anki.htmltext import encode_attribute, strip_html_preserving_entities

_MATHJAX = re.compile(r"(\\[(\[])(.*?)(\\[\])])", re.S | re.I)
_DELIMITERS = (("\\(", "\\)"), ("\\[", "\\]"))
_MAX_OPEN = 10
_IMAGE_OCCLUSION = "image-occlusion:"


class UnsupportedCloze(ValueError):
    """An image occlusion cloze: it is drawn by Anki's own JavaScript."""


@dataclass(frozen=True, slots=True)
class _Open:
    ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class _Close:
    pass


type _Token = _Open | _Close | str


@dataclass(slots=True)
class Cloze:
    ordinals: tuple[int, ...]
    nodes: list[str | Cloze] = field(default_factory=list)
    hint: str | None = None

    def clozed_text(self) -> str:
        return "".join(n if isinstance(n, str) else n.clozed_text() for n in self.nodes)

    def image_occlusion(self) -> bool:
        return (
            bool(self.nodes)
            and isinstance(self.nodes[0], str)
            and (self.nodes[0].startswith(_IMAGE_OCCLUSION))
        )


def _open_cloze(text: str, pos: int) -> tuple[int, tuple[int, ...]] | None:
    if not text.startswith("{{c", pos):
        return None
    end = pos + 3
    while end < len(text) and text[end] in "0123456789,":
        end += 1
    ordinals = {int(s) for s in text[pos + 3 : end].split(",") if s and int(s) <= 0xFFFF}
    if not ordinals or not text.startswith("::", end):
        return None
    return end + 2, tuple(sorted(ordinals))


class _MathJax:
    """Which MathJax expression the tokenizer is in, and where each open cloze began."""

    def __init__(self) -> None:
        self.current: tuple[str, int] | None = None
        self.next_id = 0
        self.regions: list[int | None] = []

    def region(self) -> int | None:
        return None if self.current is None else self.current[1]

    def can_close(self) -> bool:
        here = self.region()
        return here is None or (bool(self.regions) and self.regions[-1] == here)

    def consume(self, text: str, pos: int) -> int | None:
        if self.current is None:
            for opener, closer in _DELIMITERS:
                if text.startswith(opener, pos) and text.find(closer, pos + len(opener)) >= 0:
                    self.current = (closer, self.next_id)
                    self.next_id += 1
                    return len(opener)
            return None
        closer = self.current[0]
        if text.startswith(closer, pos):
            self.current = None
            return len(closer)
        return None


def _tokens(text: str) -> list[_Token]:
    out: list[_Token] = []
    state = _MathJax()
    pos = 0
    while pos < len(text):
        opened = _open_cloze(text, pos)
        if opened is not None:
            state.regions.append(state.region())
            pos = opened[0]
            out.append(_Open(opened[1]))
            continue
        if state.can_close() and text.startswith("}}", pos):
            if state.regions:
                state.regions.pop()
            pos += 2
            out.append(_Close())
            continue
        start = pos
        while pos < len(text):
            if _open_cloze(text, pos) is not None or (
                state.can_close() and text.startswith("}}", pos)
            ):
                break
            pos += state.consume(text, pos) or 1
        out.append(text[start:pos])
    return out


def parse(text: str) -> list[str | Cloze]:
    """The text as plain runs and (possibly nested) clozes."""
    stack: list[Cloze] = []
    output: list[str | Cloze] = []
    for token in _tokens(text):
        if isinstance(token, _Open):
            if len(stack) < _MAX_OPEN:
                stack.append(Cloze(token.ordinals))
        elif isinstance(token, _Close):
            if stack:
                done = stack.pop()
                (stack[-1].nodes if stack else output).append(done)
            else:
                output.append("}}")
        elif stack:
            cloze = stack[-1]
            if not token.startswith(_IMAGE_OCCLUSION) and "::" in token:
                token, cloze.hint = token.split("::", 1)
            cloze.nodes.append(token)
        else:
            output.append(token)
    return output


def _ordinals(ordinals: tuple[int, ...]) -> str:
    return ",".join(str(o) for o in ordinals)


def _reveal(cloze: Cloze, ordinal: int, question: bool, found: list[bool]) -> str:
    active = ordinal in cloze.ordinals
    found[0] = found[0] or active
    if cloze.image_occlusion():
        raise UnsupportedCloze("image occlusion clozes need Anki's own script")

    def children() -> str:
        return "".join(
            n if isinstance(n, str) else _reveal(n, ordinal, question, found) for n in cloze.nodes
        )

    if question and active:
        inner = children()
        hint = cloze.hint if cloze.hint is not None else "..."
        return (
            f'<span class="cloze" data-cloze="{encode_attribute(inner)}" '
            f'data-ordinal="{_ordinals(cloze.ordinals)}">[{hint}]</span>'
        )
    css = "cloze" if active else "cloze-inactive"
    return f'<span class="{css}" data-ordinal="{_ordinals(cloze.ordinals)}">{children()}</span>'


def reveal_cloze_text(text: str, ordinal: int, question: bool) -> str:
    """The text with cloze `ordinal` hidden (question) or shown (answer); "" when the text
    has no cloze with that number."""
    found = [False]
    out = "".join(
        n if isinstance(n, str) else _reveal(n, ordinal, question, found) for n in parse(text)
    )
    return out if found[0] else ""


def reveal_cloze_text_only(text: str, ordinal: int, question: bool) -> str:
    """The `cloze-only:` filter: just the hints (question) or answers, joined by ", "."""
    out: list[str] = []

    def walk(node: str | Cloze) -> None:
        if isinstance(node, Cloze):
            if ordinal in node.ordinals and question:
                out.append(node.hint if node.hint is not None else "...")
            elif ordinal in node.ordinals:
                out.append(node.clozed_text())
            for child in node.nodes:
                walk(child)

    for node in parse(text):
        walk(node)
    return ", ".join(out)


def cloze_numbers(text: str) -> set[int]:
    """Every cloze number (above 0) in the text, nested ones included."""
    found: set[int] = set()

    def walk(nodes: list[str | Cloze]) -> None:
        for node in nodes:
            if isinstance(node, Cloze):
                found.update(o for o in node.ordinals if o != 0)
                walk(node.nodes)

    walk(parse(text))
    return found


def has_image_occlusion(text: str) -> bool:
    def walk(nodes: list[str | Cloze]) -> bool:
        return any(isinstance(n, Cloze) and (n.image_occlusion() or walk(n.nodes)) for n in nodes)

    return walk(parse(text))


def strip_html_inside_mathjax(text: str) -> str:
    return _MATHJAX.sub(
        lambda m: m.group(1) + strip_html_preserving_entities(m.group(2)) + m.group(3), text
    )


def cloze_filter(text: str, card_ord: int, question: bool) -> str:
    return strip_html_inside_mathjax(reveal_cloze_text(text, card_ord + 1, question))


def cloze_only_filter(text: str, card_ord: int, question: bool) -> str:
    return reveal_cloze_text_only(text, card_ord + 1, question)
