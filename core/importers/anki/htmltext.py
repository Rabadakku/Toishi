"""Anki's small text helpers (rslib/src/text.rs, template.rs), ported to match its output.

- `decode_entities` behaves like the htmlescape crate Anki uses: HTML 4 named entities and
  `&#123;` / `&#x7b;` (a lowercase x) only. One malformed `&` anywhere and the text comes back
  unchanged. Non-breaking spaces then become plain spaces.
- `encode_attribute` and `encode_minimal` are htmlescape's two encoders (the cloze filter's
  data-cloze attribute; plain-text imports with `#html:false`).
- `field_is_empty`: only ASCII whitespace and `<br>` / `<div>` tags.
"""

import re
from html.entities import name2codepoint

_HTML = re.compile(
    r"(<!--.*?-->)|(<style.*?>.*?</style>)|(<script.*?>.*?</script>)|(<.*?>)", re.S | re.I
)
_EMPTY_FIELD = re.compile(r"(?:[ \t\n\x0b\f\r]|</?(?:br|div) ?/?>)*", re.S | re.I)
_ENTITY = re.compile(r"&(?:#([0-9]+)|#x([0-9a-fA-F]+)|([A-Za-z0-9]+));")
_MINIMAL = {'"': "&quot;", "&": "&amp;", "'": "&#x27;", "<": "&lt;", ">": "&gt;"}
_ATTRIBUTE_NAMED = {'"': "&quot;", "&": "&amp;", "<": "&lt;", ">": "&gt;"}


def is_html(text: str) -> bool:
    """Anki's `is_html`: the text has a tag, a comment, or a style or script block."""
    return _HTML.search(text) is not None


def strip_html_preserving_entities(html: str) -> str:
    return _HTML.sub("", html)


def strip_html(html: str) -> str:
    """The `text:` filter: tags, comments, style and script blocks removed, entities decoded."""
    return decode_entities(strip_html_preserving_entities(html))


def decode_entities(html: str) -> str:
    if "&" not in html:
        return html
    out: list[str] = []
    pos = 0
    while True:
        amp = html.find("&", pos)
        if amp < 0:
            out.append(html[pos:])
            break
        out.append(html[pos:amp])
        m = _ENTITY.match(html, amp)
        char = _entity_char(m) if m is not None else None
        if m is None or char is None:
            return html  # htmlescape refuses the whole text
        out.append(char)
        pos = m.end()
    return "".join(out).replace("\xa0", " ")


def _entity_char(m: re.Match[str]) -> str | None:
    decimal, hexadecimal, name = m.groups()
    if name is not None:
        code = name2codepoint.get(name)
        return None if code is None else chr(code)
    digits = decimal if decimal is not None else hexadecimal
    if len(digits.lstrip("0")) > 12:
        return None
    value = int(digits, 10 if decimal is not None else 16)
    if value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
        return None
    return chr(value)


def encode_attribute(text: str) -> str:
    """htmlescape::encode_attribute: ASCII letters and digits kept, other characters below
    256 escaped (four of them by name), everything from 256 up kept."""
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in _ATTRIBUTE_NAMED:
            out.append(_ATTRIBUTE_NAMED[ch])
        elif code < 256:
            out.append(f"&#x{code:02X};")
        else:
            out.append(ch)
    return "".join(out)


def encode_minimal(text: str) -> str:
    """htmlescape::encode_minimal: only " & ' < > are escaped."""
    return "".join(_MINIMAL.get(ch, ch) for ch in text)


def field_is_empty(text: str) -> bool:
    return _EMPTY_FIELD.fullmatch(text) is not None
