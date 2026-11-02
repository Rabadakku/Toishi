"""Anki notes -> the app's cards (docs/card-format.md "Anki compatibility").

| Anki note type                       | Becomes                                              |
|--------------------------------------|------------------------------------------------------|
| Basic, Basic (and reversed), ...     | one flashcard per Anki card, rendered by its templates |
| Cloze (stock templates)              | one cloze card; one study item per blank             |
| Mastery Problem                      | a full problem: card-file text through core.cards    |
| any other (cloze ones too)           | one flashcard per Anki card, with the note type's     |
|                                      | templates and its CSS scoped to its own cards         |
| Image Occlusion                      | rejected: it needs Anki's own script                  |

Flashcard HTML is rendered at import (template.py), sanitized (sanitize.py) and wrapped:
`<div class="anki-card cardN [scope]" [data-anki-css="_anki-nt-....css"]>...</div>`. A note
type whose CSS isn't Anki's default gets it scoped to `.anki-nt-<hash>` and stored as one
more media file of each of its cards, so the page loads it once. The back of a flashcard is
the answer after `<hr id=answer>` (the page shows the front above it); `[[type:F]]` shows
F's text on the back (typing in Anki is self-graded too).

IDs come from the note's GUID (the same in .apkg, .colpkg and a text export with a GUID
column), so importing again updates instead of duplicating: `anki.<key>.<card number>` for
flashcards, `anki.<key>` for cloze cards; a text row without a GUID gets a key from its note
type and first field, Anki's own duplicate test.
"""

import base64
import hashlib
import html as htmllib
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol

from core.cards.load import Accepted, Rejected, Source
from core.cards.problems import Problem
from core.importers.anki import cloze as cz
from core.importers.anki.htmltext import field_is_empty, strip_html
from core.importers.anki.model import (
    STOCK_IMAGE_OCCLUSION,
    AnkiData,
    Card,
    Note,
    Notetype,
    Template,
)
from core.importers.anki.sanitize import media_ref, sanitize_html, scope_css
from core.importers.anki.stock import TOISHI_PROBLEM, is_stock_css
from core.importers.anki.template import (
    SPECIAL_FIELDS,
    TemplateError,
    card_fields,
    nonempty_fields,
    parse,
    render_card,
    renders_with_fields,
)
from core.model import Card as AppCard
from core.model import Provenance

ANKI_HTML_CLASS = "anki-card"
CSS_PREFIX = "anki-nt-"
_KEY_LENGTH = 16
_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
_ANSWER_RULE = re.compile(r"<hr[^>]*\bid\s*=\s*['\"]?answer\b['\"]?[^>]*>", re.I)
_TYPE_TAG = re.compile(r"\[\[type:((?:cloze:|nc:)?)([^]]+)\]\]")
_CLOZE_TEMPLATE = re.compile(r"\{\{cloze:([^}:]+)\}\}")


def note_key(guid: str) -> str:
    digest = hashlib.sha1(guid.encode(), usedforsecurity=False).digest()
    return base64.b32encode(digest).decode().lower()[:_KEY_LENGTH]


def text_note_guid(notetype: str, first_field: str) -> str:
    """A stand-in GUID for a text row without one: its note type and first field (Anki's
    duplicate test), hashed."""
    basis = f"{notetype}\x1f{strip_html(first_field).strip()}".encode()
    return "text-" + hashlib.sha1(basis, usedforsecurity=False).hexdigest()[:20]


def is_anki_html(text: str | None) -> bool:
    """True for card text the Anki importer wrote as sanitized HTML (not Markdown)."""
    return bool(text) and text.startswith(f'<div class="{ANKI_HTML_CLASS}')  # type: ignore[union-attr]


@dataclass(frozen=True, slots=True)
class Target:
    """Where an Anki card's history goes: an own card and its study item (ord)."""

    card_id: str
    ord: int
    kind: str  # flashcard or cloze


class StoredFiles(Protocol):
    def read_file(self, name: str) -> bytes | None: ...


class ImportMedia:
    """Media for core.cards: package files by "pkg:<name>", scoped CSS by "css:<scope>", and
    files a card already has in the profile by "user:<file>" (a text export carries no
    media, so importing one after the deck's package keeps the images it stored)."""

    def __init__(
        self,
        data: AnkiData,
        stored: Mapping[str, Mapping[str, str]] | None = None,
        files: StoredFiles | None = None,
    ) -> None:
        self._data = data
        self._names = data.media.names()
        self._stored = stored or {}
        self._files = files
        self.css: dict[str, bytes] = {}

    def has(self, name: str) -> bool:
        return name in self._names

    def find(self, card_id: str, ref: str) -> str | None:
        if ref in self._names:
            return f"pkg:{ref}"
        stored = self._stored.get(card_id, {}).get(ref)
        return f"user:{stored}" if stored is not None and self._files is not None else None

    def resolve(self, file_name: str, ref: str) -> str | None:  # card-file images
        name = media_ref(ref)
        return f"pkg:{name}" if name is not None and name in self._names else None

    def read(self, name: str) -> bytes:
        kind, _, key = name.partition(":")
        if kind == "css":
            return self.css[key]
        if kind == "user" and self._files is not None:
            data = self._files.read_file(key)
            if data is None:
                raise FileNotFoundError(f"media file {key} is not in the profile")
            return data
        return self._data.media.read(key)


@dataclass(slots=True)
class Mapped:
    accepted: list[Accepted] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    warnings: list[Problem] = field(default_factory=list)
    targets: dict[int, Target] = field(default_factory=dict)  # anki card id -> target
    mastery: Source | None = None
    mastery_lines: list[tuple[int, int]] = field(default_factory=list)  # (text line, note line)
    ids: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Style:
    scope: str | None
    css_ref: str | None
    css_media: tuple[str, ...]


def _kind(nt: Notetype) -> str:
    if nt.name == TOISHI_PROBLEM:
        return "mastery"
    if nt.stock_kind == STOCK_IMAGE_OCCLUSION or (nt.is_cloze and nt.name == "Image Occlusion"):
        return "image-occlusion"
    if nt.is_cloze and len(nt.templates) == 1 and _stock_cloze_fields(nt) is not None:
        return "cloze"
    return "templates"


def _stock_cloze_fields(nt: Notetype) -> tuple[str, str | None] | None:
    """(cloze field, extra field) when the note type's one template is Anki's stock cloze
    layout (`{{cloze:Text}}`, then optionally `<br>` and one more field on the back)."""
    t = nt.templates[0]
    q = re.fullmatch(r"\s*\{\{cloze:([^}:]+)\}\}\s*", t.qfmt)
    if q is None or q.group(1) not in nt.fields:
        return None
    a = re.fullmatch(
        r"\s*\{\{cloze:" + re.escape(q.group(1)) + r"\}\}\s*(?:<br\s*/?>)?\s*"
        r"(?:\{\{([^#^/}:][^}:]*)\}\})?\s*",
        t.afmt,
    )
    if a is None or (a.group(1) is not None and a.group(1) not in nt.fields):
        return None
    return q.group(1), a.group(1)


def map_notes(data: AnkiData, media: ImportMedia) -> Mapped:
    out = Mapped()
    styles: dict[int, _Style] = {}
    cards_by_note: dict[int, list[Card]] = {}
    for card in data.cards or ():
        cards_by_note.setdefault(card.note_id, []).append(card)
    seen_guid: dict[str, int] = {}
    mastery_notes: list[tuple[Note, Notetype, str]] = []
    for note in data.notes:
        nt = data.notetypes.get(note.notetype_id)
        where = (data.name, note.line)
        if nt is None:
            out.rejected.append(Rejected(None, *where, ("its note type is not in the file",)))
            continue
        guid = note.guid or text_note_guid(nt.name, note.fields[0] if note.fields else "")
        if guid in seen_guid:
            reason = f"duplicate note (same GUID as the note at line {seen_guid[guid]})"
            out.rejected.append(Rejected(None, *where, (reason,)))
            continue
        seen_guid[guid] = note.line
        if len(note.fields) != len(nt.fields) and data.cards is not None:
            reason = f"the note has {len(note.fields)} fields, its note type {len(nt.fields)}"
            out.rejected.append(Rejected(None, *where, (reason,)))
            continue
        kind = _kind(nt)
        if kind == "mastery":
            mastery_notes.append((note, nt, _deck_of(note, cards_by_note)))
        elif kind == "image-occlusion":
            reason = "image occlusion notes need Anki's own script; they are not imported"
            out.rejected.append(Rejected(None, *where, (reason,)))
        elif kind == "cloze":
            _map_cloze(data, media, out, note, nt, guid, cards_by_note.get(note.id))
        else:
            if nt.id not in styles:
                styles[nt.id] = _style(nt, media)
            cards = cards_by_note.get(note.id)
            _map_templates(data, media, out, note, nt, guid, cards, styles[nt.id])
    if mastery_notes:
        _mastery_source(data, media, out, mastery_notes)
    return out


def _deck_of(note: Note, cards_by_note: Mapping[int, list[Card]]) -> str:
    cards = cards_by_note.get(note.id)
    return cards[0].deck if cards else (note.deck or "Default")


def _fields(note: Note, nt: Notetype) -> dict[str, str]:
    values = (list(note.fields) + [""] * len(nt.fields))[: len(nt.fields)]
    return dict(zip(nt.fields, values, strict=True))


def _style(nt: Notetype, media: ImportMedia) -> _Style:
    css = nt.css
    for t in nt.templates:
        css += "".join(m.group(1) + "\n" for m in _STYLE_BLOCK.finditer(t.qfmt + t.afmt))
    if is_stock_css(css):
        return _Style(None, None, ())
    digest = hashlib.sha1(css.encode(), usedforsecurity=False).hexdigest()[:12]
    scope = f"{CSS_PREFIX}{digest}"
    scoped = scope_css(css, scope)
    if not scoped.css.strip():
        return _Style(scope, None, ())
    media.css[scope] = scoped.css.encode()
    files = tuple(m for m in scoped.media if media.has(m))
    return _Style(scope, f"_{scope}.css", files)


def _wrap(body: str, classes: Iterable[str], css_ref: str | None) -> str:
    attrs = f' data-anki-css="{css_ref}"' if css_ref else ""
    return f'<div class="{" ".join([ANKI_HTML_CLASS, *classes])}"{attrs}>{body.strip()}</div>'


def _new_card(
    data: AnkiData, card_id: str, note: Note, deck: str, guid: str, **content: str | None
) -> AppCard:
    return AppCard(
        id=card_id,
        kind="cloze" if "text_md" in content else "flashcard",
        deck=deck,
        section_id=deck,
        tags=tuple(note.tags),
        provenance=Provenance(source="anki", original_path=f"anki-guid:{guid}"),
        **content,  # type: ignore[arg-type]
    )


def _images(
    card_id: str, refs: Iterable[str], media: ImportMedia, warn: Callable[[str], None]
) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for ref in dict.fromkeys(refs):
        name = media.find(card_id, ref)
        if name is not None:
            out.append((ref, name))
        else:
            warn(f"media file {ref!r} is not in the file")
    return tuple(out)


def _back(answer: str, question: str) -> str:
    rule = _ANSWER_RULE.search(answer)
    if rule is not None:
        return answer[rule.end() :]
    if question and answer.startswith(question):
        return answer[len(question) :]
    return answer


def _typed_answer(answer: str, fields: Mapping[str, str], card_ord: int) -> str:
    def sub(m: re.Match[str]) -> str:
        value = fields.get(m.group(2), "")
        if m.group(1) == "cloze:":
            return cz.reveal_cloze_text_only(value, card_ord + 1, question=False)
        return value

    return _TYPE_TAG.sub(sub, answer)


def _generated_ords(nt: Notetype, fields: Mapping[str, str], note: Note) -> list[int]:
    """The cards Anki would make for a note (notetype/cardgen.rs)."""
    if nt.is_cloze:
        numbers: set[int] = set()
        for value in fields.values():
            numbers |= cz.cloze_numbers(value)
        blanks = sorted(n - 1 for n in numbers if n <= 500)
        return blanks or [0]
    nonempty = nonempty_fields(fields)
    for special in SPECIAL_FIELDS:
        if special not in fields and special not in ("FrontSide", "Tags"):
            nonempty.add(special)
    if note.tags and "Tags" not in fields:
        nonempty.add("Tags")
    ords: list[int] = []
    for t in nt.templates:
        try:
            if renders_with_fields(parse(t.qfmt), nonempty):
                ords.append(t.ord)
        except TemplateError:
            continue
    return ords or [0]


def _map_templates(
    data: AnkiData,
    media: ImportMedia,
    out: Mapped,
    note: Note,
    nt: Notetype,
    guid: str,
    cards: list[Card] | None,
    style: _Style,
) -> None:
    fields = _fields(note, nt)
    key = note_key(guid)
    planned: list[tuple[int, str, Card | None]]
    if data.cards is None:
        deck = note.deck or "Default"
        planned = [(o, deck, None) for o in _generated_ords(nt, fields, note)]
    else:
        planned = [(c.ord, c.deck, c) for c in cards or ()]
    if not planned:
        out.rejected.append(Rejected(None, data.name, note.line, ("the note has no cards",)))
    for card_ord, deck, anki_card in planned:
        template: Template | None = (
            nt.templates[0]
            if nt.is_cloze
            else next((t for t in nt.templates if t.ord == card_ord), None)
        )
        card_id = f"anki.{key}.{card_ord + 1}"
        where = (data.name, note.line)
        if template is None:
            out.rejected.append(
                Rejected(card_id, *where, (f"card {card_ord + 1} has no template",))
            )
            continue
        mapping = card_fields(
            fields,
            card_ord=card_ord,
            tags=note.tags,
            notetype=nt.name,
            deck=deck,
            template_name=template.name,
            flags=anki_card.flags if anki_card else 0,
            card_id=anki_card.id if anki_card else 0,
        )
        try:
            rendered = render_card(
                template.qfmt, template.afmt, mapping, card_ord=card_ord, is_cloze=nt.is_cloze
            )
        except (TemplateError, cz.UnsupportedCloze) as exc:
            out.rejected.append(Rejected(card_id, *where, (f"the card can't be drawn: {exc}",)))
            continue
        if rendered.empty:
            out.rejected.append(Rejected(card_id, *where, ("the front of this card is empty",)))
            continue

        def warn(message: str, card_id: str = card_id, line: int = note.line) -> None:
            out.warnings.append(Problem(data.name, line, message, "warning", card_id))

        for name in rendered.unknown_filters:
            warn(f"template filter {name!r} is not supported (skipped, as Anki does without it)")
        front = sanitize_html(rendered.question)
        back = sanitize_html(
            _typed_answer(_back(rendered.answer, rendered.question), mapping, card_ord)
        )
        classes = [f"card{card_ord + 1}", *([style.scope] if style.scope else [])]
        card = _new_card(
            data,
            card_id,
            note,
            deck,
            guid,
            front_md=_wrap(front.html, classes, style.css_ref),
            back_md=_wrap(back.html, classes, style.css_ref) if back.html.strip() else None,
        )
        images = _images(card_id, front.media + back.media + list(style.css_media), media, warn)
        if style.css_ref is not None and style.scope is not None:
            images += ((style.css_ref, f"css:{style.scope}"),)
        out.accepted.append(Accepted(card, data.name, note.line, images))
        out.ids.append(card_id)
        if anki_card is not None:
            out.targets[anki_card.id] = Target(card_id, 0, "flashcard")


def _map_cloze(
    data: AnkiData,
    media: ImportMedia,
    out: Mapped,
    note: Note,
    nt: Notetype,
    guid: str,
    cards: list[Card] | None,
) -> None:
    fields = _fields(note, nt)
    found = _stock_cloze_fields(nt)
    if found is None:  # pragma: no cover - _kind chose "cloze" because this matched
        raise ValueError(f"note type {nt.name!r} is not a stock cloze")
    text_field, extra_field = found
    card_id = f"anki.{note_key(guid)}"
    where = (data.name, note.line)
    text = fields[text_field]
    if cz.has_image_occlusion(text):
        out.rejected.append(Rejected(card_id, *where, ("image occlusion clozes are not imported",)))
        return
    if not cz.cloze_numbers(text):
        out.rejected.append(Rejected(card_id, *where, ("the cloze text has no {{c1::...}}",)))
        return

    def warn(message: str) -> None:
        out.warnings.append(Problem(data.name, note.line, message, "warning", card_id))

    body = sanitize_html(text)
    extra_text = fields.get(extra_field or "", "")
    extra = sanitize_html(extra_text) if extra_field and not field_is_empty(extra_text) else None
    deck = cards[0].deck if cards else (note.deck or "Default")
    card = _new_card(
        data,
        card_id,
        note,
        deck,
        guid,
        text_md=_wrap(body.html, (), None),
        extra_md=_wrap(extra.html, (), None) if extra is not None else None,
    )
    images = _images(card_id, body.media + (extra.media if extra else []), media, warn)
    out.accepted.append(Accepted(card, data.name, note.line, images))
    out.ids.append(card_id)
    for anki_card in cards or ():
        out.targets[anki_card.id] = Target(card_id, anki_card.ord, "cloze")


# ---------------------------------------------------------------- Mastery Problem


_KEY_FIELDS = (
    ("Kind", "kind"),
    ("Skill", "skill"),
    ("Uses", "uses"),
    ("Difficulty", "difficulty"),
    ("AnswerType", "answer-type"),
    ("Answer", "answer"),
    ("Wrong", "wrong"),
    ("Calculator", "calculator"),
    ("Source", "source"),
    ("License", "license"),
)
_BLOCK_BREAKS = re.compile(r"<br\s*/?>|</?(?:div|p|li|h[1-6]|tr|blockquote|pre)\b[^>]*>", re.I)
_IMG = re.compile(r"""<img\b[^>]*?\bsrc\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>""", re.I)
_BOLD = re.compile(r"</?(?:b|strong)\b[^>]*>", re.I)
_ITALIC = re.compile(r"</?(?:i|em)\b[^>]*>", re.I)


def html_to_text(value: str) -> str:
    """A Mastery Problem field back to card-file text: line breaks back, images as
    `![](name)`, bold/italic as Markdown, other tags dropped, entities decoded; the math
    between \\( \\) stays as typed."""
    text = re.sub(r"<!--.*?-->|<(style|script)\b.*?</\1\s*>", "", value, flags=re.S | re.I)
    text = text.replace("\r\n", "\n").replace("\n", " ")
    text = _IMG.sub(lambda m: f"![]({m.group(1) or m.group(2) or m.group(3)})", text)
    text = _BLOCK_BREAKS.sub("\n", text)
    text = _BOLD.sub("**", text)
    text = _ITALIC.sub("*", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = htmllib.unescape(text).replace("\xa0", " ")
    lines = [line.rstrip() for line in text.split("\n")]
    out = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", out)


def _one_line(value: str) -> str:
    return " ".join(html_to_text(value).split())


def _section_text(value: str) -> str:
    lines = html_to_text(value).split("\n")
    return "\n".join("\\" + line if line.lstrip().startswith("#") else line for line in lines)


def _mastery_source(
    data: AnkiData, media: ImportMedia, out: Mapped, notes: list[tuple[Note, Notetype, str]]
) -> None:
    lines = ["---", "format: mastery-cards 1", "---", ""]
    for note, nt, deck in notes:
        by_name = {"".join(k.split()).lower(): v for k, v in _fields(note, nt).items()}

        def get(name: str, by_name: dict[str, str] = by_name) -> str:
            return by_name.get(name.lower(), "")

        card_id = _one_line(get("ID"))
        if not card_id:
            reason = "a Mastery Problem note needs its ID field"
            out.rejected.append(Rejected(None, data.name, note.line, (reason,)))
            continue
        out.mastery_lines.append((len(lines) + 1, note.line))
        lines.append(f"## Card {card_id}")
        for anki_name, key in _KEY_FIELDS:
            value = _one_line(get(anki_name))
            if value:
                lines.append(f"{key}: {value}")
        for option in html_to_text(get("Options")).split("\n"):
            if ":" in option and option.strip():
                lines.append(option.strip())
        lines.append(f"deck: {deck}")
        tags = [t.replace(",", "") for t in note.tags if t.replace(",", "")]
        if tags:
            lines.append(f"tags: {', '.join(tags)}")
        for anki_name, heading in (("Question", "Question"), ("CuedQuestion", "Cued Question")):
            text = _section_text(get(anki_name))
            if text:
                lines += ["", f"### {heading}", text]
        hints = [h.strip() for h in html_to_text(get("Hints")).split("\n") if h.strip()]
        if hints:
            lines += ["", "### Hints", *(f"{i}. {h}" for i, h in enumerate(hints, 1))]
        solution = _section_text(get("Solution"))
        if solution:
            lines += ["", "### Solution", solution]
        lines.append("")
    if out.mastery_lines:
        out.mastery = Source(data.name, "\n".join(lines) + "\n", media)


def note_line(mapped: Mapped, text_line: int) -> int:
    """The note (package) or row (text file) a line of the generated card-file text is from."""
    found = 0
    for start, line in mapped.mastery_lines:
        if start > text_line:
            break
        found = line
    return found or (mapped.mastery_lines[0][1] if mapped.mastery_lines else 0)
