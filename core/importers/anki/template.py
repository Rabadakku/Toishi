"""Anki's card template language, ported from rslib/src/template.rs and template_filters.rs
(IMP-8). Generic Mustache libraries get these rules wrong:

- `{{Field}}` inserts the field's HTML as is. Unknown fields are errors.
- `{{#F}}...{{/F}}` / `{{^F}}...{{/F}}` test whether F is non-empty; a field holding only
  whitespace, `<br>` or `<div>` is empty. `{{#c1}}` on card 1 of a cloze note is true.
- Filters chain right to left: `{{text:cloze:Text}}` runs cloze, then text. Unknown filters
  (add-ons) are skipped. `type:` leaves the placeholder `[[type:Field]]`; exactly
  `{{type:cloze:F}}` and `{{type:nc:F}}` give `[[type:cloze:F]]` / `[[type:nc:F]]`. This is
  Anki 26.09.3, the release students run and the test oracle; Anki's main branch has since
  added `ci:` and folds any modifiers into an outermost `type:`.
- `{{FrontSide}}` on the answer side is the rendered question.
- Special fields: Tags, Type, Deck, Subdeck, Card, CardFlag, CardID (never over a note field).
- `<!-- comments -->` are copied through untouched; `{{=<% %>=}}` switches to `<% %>`.

`hint_style="anki"` gives Anki's exact hint markup (a link with an onclick handler; the id
uses BLAKE2b where Anki uses BLAKE3, the only difference). The importer uses "native": a
`<details>` element, so no script is needed.
"""

import hashlib
import html
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from core.importers.anki import cloze
from core.importers.anki.htmltext import field_is_empty, strip_html

type HintStyle = Literal["anki", "native"]

ALT_SYNTAX = "{{=<% %>=}}"
SPECIAL_FIELDS = ("FrontSide", "Card", "CardFlag", "Deck", "Subdeck", "Tags", "Type", "CardID")
_FURIGANA = re.compile(r" ?([^ >]+?)\[(.+?)\]")


class TemplateError(ValueError):
    """The template can't be rendered: Anki shows an error card instead."""


# ---------------------------------------------------------------- parsing


@dataclass(frozen=True, slots=True)
class Text:
    text: str


@dataclass(frozen=True, slots=True)
class Comment:
    text: str


@dataclass(frozen=True, slots=True)
class Replacement:
    key: str
    filters: tuple[str, ...]  # in the order they apply


@dataclass(frozen=True, slots=True)
class Conditional:
    key: str
    children: tuple[Node, ...]
    negated: bool = False


type Node = Text | Comment | Replacement | Conditional


def _classify(inner: str) -> tuple[str, str]:
    start = inner.lstrip("{").strip()
    if len(start.encode()) < 2:
        return "replace", start
    for prefix, kind in (("#", "open"), ("/", "close"), ("^", "negated")):
        if start.startswith(prefix):
            return kind, start[1:].lstrip()
    return "replace", start


def _tokens(template: str) -> list[tuple[str, str]]:
    start_tag, end_tag = "{{", "}}"
    if template.lstrip().startswith(ALT_SYNTAX):
        template = template.lstrip()
        while template.startswith(ALT_SYNTAX):
            template = template[len(ALT_SYNTAX) :]
        start_tag, end_tag = "<%", "%>"
    out: list[tuple[str, str]] = []
    pos = 0
    text_start = 0
    while pos < len(template):
        found: tuple[str, str, int] | None = None
        if template.startswith(start_tag, pos):
            end = template.find(end_tag, pos + len(start_tag))
            if end >= 0:
                kind, value = _classify(template[pos + len(start_tag) : end])
                found = (kind, value, end + len(end_tag))
        if found is None and template.startswith("<!--", pos):
            end = template.find("-->", pos + 4)
            if end >= 0:
                found = ("comment", template[pos + 4 : end], end + 3)
        if found is None:
            pos += 1
            continue
        if pos > text_start:
            out.append(("text", template[text_start:pos]))
        out.append((found[0], found[1]))
        pos = text_start = found[2]
    if text_start < len(template):
        out.append(("text", template[text_start:]))
    return out


def parse(template: str) -> tuple[Node, ...]:
    tokens = _tokens(template)
    nodes, rest = _parse(tokens, 0, None)
    if rest != len(tokens):  # pragma: no cover - _parse consumes everything or raises
        raise TemplateError("template did not parse")
    return nodes


def _parse(
    tokens: Sequence[tuple[str, str]], pos: int, open_tag: str | None
) -> tuple[tuple[Node, ...], int]:
    nodes: list[Node] = []
    while pos < len(tokens):
        kind, value = tokens[pos]
        pos += 1
        if kind == "text":
            nodes.append(Text(value))
        elif kind == "comment":
            nodes.append(Comment(value))
        elif kind == "replace":
            parts = value.split(":")
            nodes.append(Replacement(parts[-1], tuple(reversed(parts[:-1]))))
        elif kind in ("open", "negated"):
            children, pos = _parse(tokens, pos, value)
            nodes.append(Conditional(value, children, negated=kind == "negated"))
        else:  # close
            if open_tag == value:
                return tuple(nodes), pos
            if open_tag is not None:
                raise TemplateError(
                    f"found {{{{/{value}}}}} where {{{{/{open_tag}}}}} was expected"
                )
            raise TemplateError(f"found {{{{/{value}}}}} without a matching {{{{#{value}}}}}")
    if open_tag is not None:
        raise TemplateError(f"missing {{{{/{open_tag}}}}}")
    return tuple(nodes), pos


def is_cloze_conditional(key: str) -> bool:
    return key.startswith("c") and key[1:].isascii() and key[1:].isdigit() and len(key) > 1


def renders_with_fields(nodes: Sequence[Node], nonempty: set[str]) -> bool:
    """Anki's empty-front test: some replacement of a non-empty field would be shown."""
    return not _is_empty(nodes, nonempty)


def _is_empty(nodes: Sequence[Node], nonempty: set[str]) -> bool:
    for node in nodes:
        if isinstance(node, Replacement):
            if node.key in nonempty:
                return False
        elif isinstance(node, Conditional):
            if node.negated:
                if node.key in nonempty:
                    continue
            elif node.key not in nonempty:
                continue
            if not _is_empty(node.children, nonempty):
                return False
    return True


# ---------------------------------------------------------------- rendering


@dataclass(slots=True)
class _Context:
    fields: Mapping[str, str]
    nonempty: set[str]
    card_ord: int
    hint_style: HintStyle
    frontside: str | None = None  # None on the question side
    unknown_filters: list[str] = field(default_factory=list)


def _render(nodes: Sequence[Node], ctx: _Context, out: list[str]) -> None:
    for node in nodes:
        if isinstance(node, Text):
            out.append(node.text)
        elif isinstance(node, Comment):
            out.append(f"<!--{node.text}-->")
        elif isinstance(node, Replacement):
            if node.key == "FrontSide":
                out.append(ctx.frontside or "")
            elif node.key == "" and node.filters:
                continue  # a filter given no field adds nothing in a full render
            elif node.key not in ctx.fields:
                written = "".join(f"{f}:" for f in reversed(node.filters))
                raise TemplateError(f"no field named {node.key!r} ({{{{{written}{node.key}}}}})")
            else:
                out.append(_apply_filters(ctx.fields[node.key], node.filters, node.key, ctx))
        else:
            known = node.key in ctx.fields or is_cloze_conditional(node.key)
            if node.key not in ctx.nonempty and not known:
                mark = "^" if node.negated else "#"
                raise TemplateError(f"no field named {node.key!r} ({{{{{mark}{node.key}}}}})")
            shown = (node.key in ctx.nonempty) != node.negated
            _render(node.children, ctx, out if shown else [])  # errors still count when hidden


def type_placeholder(field_name: str, modifier: str = "") -> str:
    return f"[[type:{modifier}{field_name}]]"


def _apply_filters(text: str, filters: Sequence[str], field_name: str, ctx: _Context) -> str:
    if tuple(filters) in (("cloze", "type"), ("nc", "type")):
        filters = (f"type-{filters[0]}",)
    for name in filters:
        text = _apply_filter(name, text, field_name, ctx)
    return text


def _apply_filter(name: str, text: str, field_name: str, ctx: _Context) -> str:
    question = ctx.frontside is None
    simple: dict[str, Callable[[], str]] = {
        "text": lambda: strip_html(text),
        "furigana": lambda: _ruby(text, "furigana"),
        "kanji": lambda: _ruby(text, "kanji"),
        "kana": lambda: _ruby(text, "kana"),
        "type": lambda: type_placeholder(field_name),
        "type-cloze": lambda: type_placeholder(field_name, "cloze:"),
        "type-nc": lambda: type_placeholder(field_name, "nc:"),
        "hint": lambda: _hint(text, field_name, ctx.hint_style),
        "cloze": lambda: cloze.cloze_filter(text, ctx.card_ord, question),
        "cloze-only": lambda: cloze.cloze_only_filter(text, ctx.card_ord, question),
        "": lambda: text,
    }
    if name in simple:
        return simple[name]()
    if name.startswith("tts "):
        return f"[anki:tts lang={name[4:]}]{text}[/anki:tts]"
    ctx.unknown_filters.append(name)
    return text  # an add-on filter: skipped


def _ruby(text: str, kind: str) -> str:
    def sub(m: re.Match[str]) -> str:
        if m.group(2).startswith("sound:"):
            return m.group(0)
        if kind == "kana":
            return m.group(2)
        if kind == "kanji":
            return m.group(1)
        return f"<ruby><rb>{m.group(1)}</rb><rt>{m.group(2)}</rt></ruby>"

    return _FURIGANA.sub(sub, text.replace("&nbsp;", " "))


def _hint(text: str, field_name: str, style: HintStyle) -> str:
    if not text.strip():
        return text
    if style == "native":
        return (
            f'<details class="hint"><summary>{html.escape(field_name, quote=False)}</summary>'
            f"{text}</details>"
        )
    digest = hashlib.blake2b((text + field_name).encode(), digest_size=8).hexdigest()
    return (
        '\n<a class=hint href="#"\n'
        "onclick=\"this.style.display='none';\n"
        f"document.getElementById('hint{digest}').style.display='block';\n"
        'return false;" draggable=false>\n'
        f"{field_name}</a>\n"
        f'<div id="hint{digest}" class=hint style="display: none">{text}</div>\n'
    )


# ---------------------------------------------------------------- both sides of a card


@dataclass(frozen=True, slots=True)
class RenderedCard:
    question: str
    answer: str
    empty: bool  # Anki would show "the front of this card is blank" (or no such cloze)
    unknown_filters: tuple[str, ...] = ()


def card_fields(
    note_fields: Mapping[str, str],
    *,
    card_ord: int,
    tags: Sequence[str] = (),
    notetype: str = "",
    deck: str = "Default",
    template_name: str = "",
    flags: int = 0,
    card_id: int = 0,
) -> dict[str, str]:
    """The field map a card renders with: the note's fields, then the special fields that
    don't clash with them, then `c<ord + 1>` (cloze conditionals)."""
    out = dict(note_fields)
    specials = {
        "Tags": " ".join(tags),
        "Type": notetype,
        "Subdeck": deck.rsplit("::", 1)[-1],
        "Deck": deck,
        "CardFlag": f"flag{flags}",
        "Card": template_name,
        "CardID": str(card_id),
        f"c{card_ord + 1}": "1",
    }
    for key, value in specials.items():
        out.setdefault(key, value)
    return out


def nonempty_fields(fields: Mapping[str, str]) -> set[str]:
    return {name for name, value in fields.items() if not field_is_empty(value)}


def render_card(
    qfmt: str | Sequence[Node],
    afmt: str | Sequence[Node],
    fields: Mapping[str, str],
    *,
    card_ord: int,
    is_cloze: bool,
    hint_style: HintStyle = "native",
) -> RenderedCard:
    """Both sides of one card, as Anki's full render produces them (no CSS, no av tags).
    Raises TemplateError where Anki shows an error card; UnsupportedCloze for image
    occlusion."""
    question_nodes = parse(qfmt) if isinstance(qfmt, str) else qfmt
    answer_nodes = parse(afmt) if isinstance(afmt, str) else afmt
    ctx = _Context(fields, nonempty_fields(fields), card_ord, hint_style)
    out: list[str] = []
    _render(question_nodes, ctx, out)
    question = "".join(out)
    if is_cloze:
        numbers: set[int] = set()
        for value in fields.values():
            numbers |= cloze.cloze_numbers(value)
        empty = card_ord + 1 not in numbers
    else:
        empty = not renders_with_fields(question_nodes, ctx.nonempty)
    if empty:
        return RenderedCard(question, "", True, tuple(ctx.unknown_filters))
    ctx.frontside = question
    out = []
    _render(answer_nodes, ctx, out)
    return RenderedCard(question, "".join(out), False, tuple(dict.fromkeys(ctx.unknown_filters)))
