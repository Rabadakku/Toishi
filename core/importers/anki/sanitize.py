"""Imported HTML and CSS made safe to show (IMP-6): scripts never run.

`sanitize_html` keeps an allow-list of formatting tags and attributes and drops the rest:
`<script>`, `<style>`, frames, objects, forms and SVG go with their content; event handlers
(`on...`), `id`, links' targets and anything pointing outside the deck's own media go too.
Media references (`<img src>`, `<audio>`, `<video>`, `<source>`, `[sound:...]`) must be plain
file names; they are normalized like Anki's (NFC, at most 120 bytes) and collected, so the
importer can store the files with the card. `[sound:x]` becomes an `<audio controls>`
element; Anki's TTS tags keep only their text.

`scope_css` rewrites a note type's CSS so it applies only inside that note type's cards:
every selector is prefixed with the scope class, and Anki's root selectors (`.card`, `body`,
`html`, `:root`, `.cardN`, `.nightMode`) are mapped onto the card's own wrapper. `@import`
and remote `url()`s are dropped; `@media`, `@supports` and similar are scoped inside.
"""

import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from core.importers.anki.media import SOUND, normalize_filename

ALLOWED_TAGS = frozenset(
    {
        "a",
        "abbr",
        "b",
        "big",
        "blockquote",
        "br",
        "caption",
        "center",
        "cite",
        "code",
        "col",
        "colgroup",
        "dd",
        "del",
        "details",
        "dfn",
        "div",
        "dl",
        "dt",
        "em",
        "figcaption",
        "figure",
        "font",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "ins",
        "kbd",
        "li",
        "mark",
        "ol",
        "p",
        "pre",
        "q",
        "rb",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "section",
        "small",
        "source",
        "span",
        "strike",
        "strong",
        "sub",
        "summary",
        "sup",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "tt",
        "u",
        "ul",
        "var",
        "wbr",
        "audio",
        "video",
        "article",
        "aside",
        "header",
        "footer",
        "main",
        "nav",
        "label",
        "time",
    }
)
DROP_WITH_CONTENT = frozenset(
    {
        "script",
        "style",
        "iframe",
        "frame",
        "frameset",
        "object",
        "embed",
        "applet",
        "noscript",
        "template",
        "title",
        "head",
        "textarea",
        "select",
        "button",
        "svg",
        "math",
        "canvas",
        "input",
        "option",
        "dialog",
        "noembed",
        "noframes",
        "xmp",
        "plaintext",
    }
)
VOID_TAGS = frozenset({"br", "hr", "img", "source", "col", "wbr"})
# Every void element in HTML: they have no end tag, so they never open a dropped region.
_HTML_VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
        "keygen",
    }
)
_GLOBAL_ATTRS = frozenset({"class", "style", "title", "lang", "dir"})
_TAG_ATTRS: dict[str, frozenset[str]] = {
    "img": frozenset({"src", "alt", "width", "height"}),
    "audio": frozenset({"src", "controls", "loop"}),
    "video": frozenset({"src", "controls", "loop", "width", "height"}),
    "source": frozenset({"src", "type"}),
    "td": frozenset({"colspan", "rowspan", "align", "valign", "width", "height"}),
    "th": frozenset({"colspan", "rowspan", "align", "valign", "width", "height"}),
    "table": frozenset({"border", "cellpadding", "cellspacing", "width", "align"}),
    "col": frozenset({"span", "width"}),
    "colgroup": frozenset({"span", "width"}),
    "font": frozenset({"color", "face", "size"}),
    "ol": frozenset({"start", "type", "reversed"}),
    "li": frozenset({"value"}),
    "div": frozenset({"align"}),
    "p": frozenset({"align"}),
    "details": frozenset({"open"}),
}
_MEDIA_TAGS = frozenset({"img", "audio", "video", "source"})
_BAD_CSS = re.compile(
    r"expression\s*\(|javascript:|vbscript:|behavior\s*:|-moz-binding|@import", re.I
)
_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I | re.S)
_TTS = re.compile(r"\[anki:tts[^\]]*\](.*?)\[/anki:tts\]", re.S)
_TYPE = re.compile(r"\[\[type:[^]]+\]\]")
_AUDIO_EXT = frozenset({"mp3", "ogg", "oga", "wav", "m4a", "aac", "flac", "opus", "spx", "amr"})


@dataclass(slots=True)
class Sanitized:
    html: str
    media: list[str] = field(default_factory=list)  # normalized names, in order, no repeats


def is_local_ref(value: str) -> bool:
    """A reference to a file of the deck itself: no scheme, no path, nothing remote."""
    v = value.strip()
    return bool(v) and not (
        "/" in v or "\\" in v or v.startswith("#") or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", v)
    )


def media_ref(value: str) -> str | None:
    return normalize_filename(value.strip()) if is_local_ref(value) else None


def clean_style(style: str, media: list[str] | None = None) -> str:
    """A style attribute's declarations, without anything that can run code or fetch."""
    kept: list[str] = []
    for decl in style.split(";"):
        if not decl.strip() or _BAD_CSS.search(decl):
            continue
        bad = False
        for m in _URL.finditer(decl):
            ref = media_ref(m.group(2))
            if ref is None:
                bad = True
            elif media is not None and ref not in media:
                media.append(ref)
        if not bad:
            kept.append(decl.strip())
    return "; ".join(kept)


class _Cleaner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.media: list[str] = []
        self.dropping: list[str] = []  # open elements whose content is being dropped
        self.open: list[str] = []

    def _note_media(self, ref: str) -> None:
        if ref not in self.media:
            self.media.append(ref)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, closed=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, closed=True)

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], closed: bool) -> None:
        opens = not closed and tag not in _HTML_VOID
        if self.dropping:
            if tag in DROP_WITH_CONTENT and opens:
                self.dropping.append(tag)
            return
        if tag in DROP_WITH_CONTENT:
            if opens:
                self.dropping.append(tag)
            return
        if tag not in ALLOWED_TAGS:
            return  # unwrap: its content stays
        allowed = _GLOBAL_ATTRS | _TAG_ATTRS.get(tag, frozenset())
        kept: list[str] = []
        for name, value in attrs:
            name = name.lower()
            if name not in allowed and not (name.startswith("data-") and name[5:].isidentifier()):
                continue
            value = value or ""
            if name == "src":
                ref = media_ref(value)
                if ref is None:
                    continue
                self._note_media(ref)
                value = ref
            elif name == "style":
                value = clean_style(value, self.media)
                if not value:
                    continue
            kept.append(f' {name}="{html.escape(value, quote=True)}"')
        if tag == "img" and not any(k.startswith(" src=") for k in kept):
            return  # an image from outside the deck: dropped
        if tag in ("audio", "video") and not any(k.startswith(" controls") for k in kept):
            kept.append(' controls=""')
        self.out.append(f"<{tag}{''.join(kept)}>")
        if tag not in VOID_TAGS:
            if closed:
                self.out.append(f"</{tag}>")
            else:
                self.open.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.dropping:
            if tag == self.dropping[-1]:
                self.dropping.pop()
            return
        if tag in VOID_TAGS or tag not in ALLOWED_TAGS or tag not in self.open:
            return
        while self.open:
            top = self.open.pop()
            self.out.append(f"</{top}>")
            if top == tag:
                break

    def handle_data(self, data: str) -> None:
        if not self.dropping:
            self.out.append(html.escape(data, quote=False))

    def close_all(self) -> str:
        self.close()
        while self.open:
            self.out.append(f"</{self.open.pop()}>")
        return "".join(self.out)


def _sound(m: re.Match[str]) -> str:
    name = html.unescape(m.group(1))
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    tag = "audio" if ext in _AUDIO_EXT else "video"
    return f'<{tag} controls src="{html.escape(name, quote=True)}"></{tag}>'


def sanitize_html(text: str, *, keep_type_placeholders: bool = False) -> Sanitized:
    """Safe HTML for one side of a card, and the media files it shows."""
    text = _TTS.sub(lambda m: m.group(1), text)
    if not keep_type_placeholders:
        text = _TYPE.sub("", text)
    text = SOUND.sub(_sound, text)
    cleaner = _Cleaner()
    cleaner.feed(text)
    out = cleaner.close_all()
    return Sanitized(out, cleaner.media)


# ---------------------------------------------------------------- CSS


_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_ROOT_TAGS = ("html", "body", ":root")
_NIGHT = (".nightMode", ".night_mode")
_GROUPING_AT = ("@media", "@supports", "@container", "@layer", "@document")
_KEPT_AT = (
    "@font-face",
    "@keyframes",
    "@-webkit-keyframes",
    "@page",
    "@counter-style",
    "@font-feature-values",
    "@property",
)
NIGHT_CLASS = "anki-night"


def _split_top(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    depth, start = 0, 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _compounds(selector: str) -> list[str]:
    """A selector cut into compounds and combinators, e.g. ['.a', ' ', 'b', '>', '.c']."""
    out: list[str] = []
    current: list[str] = []
    depth = 0
    i = 0
    while i < len(selector):
        ch = selector[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if depth == 0 and (ch.isspace() or ch in ">+~"):
            if current:
                out.append("".join(current))
                current = []
            j = i
            comb = ""
            while j < len(selector) and (selector[j].isspace() or selector[j] in ">+~"):
                if not selector[j].isspace():
                    comb = selector[j]
                j += 1
            if out and j < len(selector):
                out.append(comb or " ")
            i = j
            continue
        current.append(ch)
        i += 1
    if current:
        out.append("".join(current))
    return out


_CLASS_CARD = re.compile(r"\.card(?![\w-])")
_CLASS_CARDN = re.compile(r"\.card\d+(?![\w-])")
_NIGHT_RE = re.compile(r"\.night(?:Mode|_mode)(?![\w-])")


def _root_compound(compound: str) -> bool:
    bare = re.sub(r"[.:#\[].*$", "", compound)
    return (
        bare in ("html", "body")
        or compound.startswith(":root")
        or bool(_CLASS_CARD.search(compound) or _CLASS_CARDN.search(compound))
        or (bool(_NIGHT_RE.search(compound)) and not bare)
    )


def _as_root(compound: str) -> str:
    c = re.sub(r"^(html|body|:root)", "", compound)
    c = _CLASS_CARD.sub("", c)
    return _NIGHT_RE.sub(f".{NIGHT_CLASS}", c)


def scope_selector(selector: str, scope: str) -> str:
    """One selector moved inside `.scope`. Leading compounds that name Anki's page or card
    (html, body, :root, .card, .cardN, .nightMode), joined by spaces, become the wrapper."""
    parts = _compounds(selector.strip())
    if not parts:
        return ""
    extra: list[str] = []
    i = 0
    while i < len(parts) and _root_compound(parts[i]):
        extra.append(_as_root(parts[i]))
        i += 1
        if i + 1 < len(parts) and parts[i] == " " and _root_compound(parts[i + 1]):
            i += 1
            continue
        break
    if not extra:
        return f".{scope} {_join(parts)}"
    return f".{scope}{''.join(extra)}{_join(parts[i:])}"


def _join(parts: list[str]) -> str:
    return "".join(" " if p == " " else f" {p} " if p in ">+~" else p for p in parts)


def _clean_block(body: str, media: list[str]) -> str:
    return clean_style(body.replace("\n", " "), media)


@dataclass(slots=True)
class ScopedCss:
    css: str
    media: list[str] = field(default_factory=list)  # underscore files and other url() refs


def scope_css(css: str, scope: str) -> ScopedCss:
    media: list[str] = []
    out = _scope_rules(_COMMENT.sub("", css), scope, media)
    return ScopedCss(out, media)


def _scope_rules(css: str, scope: str, media: list[str]) -> str:
    out: list[str] = []
    pos = 0
    n = len(css)
    while pos < n:
        brace = css.find("{", pos)
        semi = css.find(";", pos)
        if semi >= 0 and (brace < 0 or semi < brace):  # a statement: @import, @charset ...
            pos = semi + 1
            continue
        if brace < 0:
            break
        prelude = css[pos:brace].strip()
        end = _matching_brace(css, brace)
        body = css[brace + 1 : end]
        pos = end + 1
        lowered = prelude.lower()
        if lowered.startswith(_GROUPING_AT):
            inner = _scope_rules(body, scope, media)
            if inner:
                out.append(f"{prelude} {{\n{inner}}}\n")
        elif lowered.startswith(_KEPT_AT):
            if lowered.startswith("@font-face"):
                body = _clean_block(body, media)
            remote = any(media_ref(m.group(2)) is None for m in _URL.finditer(body))
            if not _BAD_CSS.search(body) and not remote:
                out.append(f"{prelude} {{{body}}}\n")
        elif prelude.startswith("@"):
            continue
        elif prelude:
            selectors = [scope_selector(s, scope) for s in _split_top(prelude, ",") if s.strip()]
            declarations = _clean_block(body, media)
            if selectors and declarations:
                out.append(f"{', '.join(selectors)} {{ {declarations}; }}\n")
    return "".join(out)


def _matching_brace(css: str, start: int) -> int:
    depth = 0
    quote = ""
    for i in range(start, len(css)):
        ch = css[i]
        if quote:
            if ch == quote and css[i - 1] != "\\":
                quote = ""
        elif ch in "'\"":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(css)
