"""Media file names and references, as Anki handles them (rslib/src/media/files.rs, text.rs).

- `normalize_filename`: NFC; characters that break some file system removed; non-breaking
  spaces become spaces; Windows device names get "_"; at most 120 bytes (IMP-6).
- `filename_is_safe`: one plain path component (the rule Anki applies to every name in a
  package's media map; anything else makes the package corrupt).
- `underscored_css_refs`: the `_font.woff` style files a note type's CSS pulls in.
"""

import re
import unicodedata

MAX_NAME_BYTES = 120
_DISALLOWED = frozenset('[]<>:"/?*^\\|')
_DEVICE = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)", re.I)
_TRAILING = re.compile(r"[ .]$")
_UNDERSCORED_CSS = re.compile(
    r"""(?:@import\s+"(_[^"]*.css)"|'(_[^']*.css)')|(?:url\(\s*"(_[^"]+)"|'(_[^']+)'|(_.+?)\s*\))""",
    re.I,
)
SOUND = re.compile(r"\[sound:([^]]+)\]")


def _disallowed(ch: str) -> bool:
    return (
        ch in _DISALLOWED or ord(ch) < 0x20 or ord(ch) == 0x7F or (unicodedata.category(ch) == "Cn")
    )


def _cut(text: str, max_bytes: int) -> str:
    encoded = text.encode()
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode(errors="ignore")


def _truncate(name: str) -> str:
    if len(name.encode()) <= MAX_NAME_BYTES:
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    ext = _cut(ext, 10)
    stem = _cut(stem, MAX_NAME_BYTES - len(ext.encode()) - 2)
    out = f"{stem}.{ext}" if ext else stem
    return out + "_" if _TRAILING.search(out) else out


def normalize_filename(name: str) -> str:
    out = unicodedata.normalize("NFC", name)
    out = "".join(ch for ch in out if not _disallowed(ch)).replace("\xa0", " ")
    out = _DEVICE.sub(r"\1_\2", out)
    if _TRAILING.search(out):
        out += "_"
    return _truncate(out)


def filename_is_safe(name: str) -> bool:
    return bool(name) and "/" not in name and "\x00" not in name and name not in (".", "..")


def underscored_css_refs(css: str) -> list[str]:
    return [next(g for g in m.groups() if g) for m in _UNDERSCORED_CSS.finditer(css)]
