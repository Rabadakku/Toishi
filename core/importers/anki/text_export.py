"""Anki's "Notes in Plain Text" export and other delimited text files (IMP-3), read the way
Anki 26.09 reads them (rslib/src/import_export/text/csv).

Header lines come first: `#separator:` (a name such as tab, comma, semicolon, pipe, colon,
space, or the character), `#html:true|false`, `#tags:` (added to every note), `#columns:`
(column labels, matched to field names), `#notetype:` and `#deck:` (one for the file), and
`#notetype column:`, `#deck column:`, `#tags column:`, `#guid column:` (1-based). A first
line `tags:...` (no #) is the old way to give file tags. Without `#separator` the delimiter
is the first of tab, |, ;, :, comma found in the first 8 KiB, else space; without `#html`
the file is HTML when any of its first five rows has a tag.

The body is CSV: fields in double quotes may hold the delimiter and line breaks, `""` is a
quote, and any line starting with # is skipped. Without HTML, text is escaped and line
breaks become `<br>`. A headerless two-column file is Basic: front, back (a third column is
the tags, as in Anki). Rows whose first field is empty are skipped.
"""

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from core.importers.anki.errors import AnkiImportError
from core.importers.anki.htmltext import encode_minimal, is_html
from core.importers.anki.model import AnkiData, Note, Notetype, Template
from core.importers.anki.stock import stock_notetype

MAX_TEXT_BYTES = 64 << 20
DELIMITERS = {"tab": "\t", "pipe": "|", "semicolon": ";", "colon": ":", "comma": ",", "space": " "}
_DETECT_ORDER = ("\t", "|", ";", ":", ",")
_PREVIEW = 5


@dataclass(slots=True)
class TextMeta:
    delimiter: str = "\t"
    delimiter_forced: bool = False
    html: bool | None = None
    global_tags: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    notetype: str | None = None
    deck: str | None = None
    notetype_column: int = 0
    deck_column: int = 0
    tags_column: int = 0
    guid_column: int = 0
    ignored: list[str] = field(default_factory=list)

    def meta_columns(self) -> set[int]:
        cols = (self.notetype_column, self.deck_column, self.tags_column, self.guid_column)
        return {c for c in cols if c > 0}


def _trimmed(value: str) -> str:
    """Anki cuts a value at the first non-alphanumeric character after its first one, so a
    header exported as a row (`#separator:tab<TAB><TAB>`) still reads."""
    for i in range(1, len(value)):
        ch = value[i]
        if not (ch.isascii() and ch.isalnum()):
            return value[:i]
    return value


def _number(value: str) -> int:
    text = _trimmed(value).strip()
    return int(text) if text.isascii() and text.isdigit() else 0


def _parse_meta(lines: list[str], meta: TextMeta) -> int:
    """Read the header lines; returns how many lines they take."""
    count = 0
    for index, line in enumerate(lines):
        if index == 0 and line.startswith("tags:"):
            meta.global_tags = line[5:].split()
        elif line.startswith("#"):
            key, sep, value = line[1:].partition(":")
            if sep:
                _meta_value(key, value, meta)
        else:
            break
        count += 1
    return count


def _meta_value(key: str, value: str, meta: TextMeta) -> None:
    name = key.strip().lower()
    trimmed = _trimmed(value)
    if name == "separator":
        lowered = trimmed.lower()
        delimiter = DELIMITERS.get(lowered.strip()) or (
            lowered if lowered in DELIMITERS.values() else None
        )
        if delimiter is not None:
            meta.delimiter, meta.delimiter_forced = delimiter, True
    elif name == "html":
        if trimmed.lower() in ("true", "false"):
            meta.html = trimmed.lower() == "true"
    elif name == "tags":
        meta.global_tags = value.split()
    elif name == "columns":
        records = parse_csv(value, meta.delimiter)
        if records:
            meta.columns = records[0][1]
    elif name == "notetype":
        meta.notetype = value
    elif name == "deck":
        meta.deck = value or meta.deck
    elif name == "notetype column":
        meta.notetype_column = _number(value)
    elif name == "deck column":
        meta.deck_column = _number(value)
    elif name == "tags column":
        meta.tags_column = _number(value)
    elif name == "guid column":
        meta.guid_column = _number(value)
    else:
        meta.ignored.append(name)


def parse_csv(text: str, delimiter: str, first_line: int = 1) -> list[tuple[int, list[str]]]:
    """Records as the Rust csv crate reads them (flexible, no headers, # comments): a list of
    (line the record starts on, fields). Blank lines are skipped."""
    out: list[tuple[int, list[str]]] = []
    pos, line, n = 0, first_line, len(text)
    while pos < n:
        ch = text[pos]
        if ch in "\r\n":  # a blank line
            pos += 2 if text.startswith("\r\n", pos) else 1
            line += 1
            continue
        if ch == "#":  # a comment line
            end = _line_end(text, pos)
            pos, line = _after_line_end(text, end), line + 1
            continue
        start_line = line
        fields: list[str] = []
        while True:
            value: list[str] = []
            if pos < n and text[pos] == '"':
                pos += 1
                while pos < n:
                    ch = text[pos]
                    if ch == '"':
                        if text.startswith('""', pos):
                            value.append('"')
                            pos += 2
                            continue
                        pos += 1
                        break
                    if ch == "\n" or (ch == "\r" and not text.startswith("\r\n", pos)):
                        line += 1
                    value.append(ch)
                    pos += 1
            while pos < n and text[pos] != delimiter and text[pos] not in "\r\n":
                value.append(text[pos])
                pos += 1
            fields.append("".join(value))
            if pos < n and text[pos] == delimiter:
                pos += 1
                continue
            break
        out.append((start_line, fields))
        if pos < n:
            pos, line = _after_line_end(text, pos), line + 1
    return out


def _line_end(text: str, pos: int) -> int:
    ends = [i for i in (text.find("\n", pos), text.find("\r", pos)) if i >= 0]
    return min(ends) if ends else len(text)


def _after_line_end(text: str, pos: int) -> int:
    if text.startswith("\r\n", pos):
        return pos + 2
    return pos + 1 if pos < len(text) else pos


def _detect_delimiter(body: str) -> str:
    sample = body.encode()[: 8 * 1024]
    for delimiter in _DETECT_ORDER:
        if delimiter.encode() in sample:
            return delimiter
    return " "


def _field_columns(meta: TextMeta, notetype: Notetype, column_count: int) -> list[int]:
    """Which column (1-based, 0 = none) feeds each field of a file-wide note type."""
    meta_cols = meta.meta_columns()
    columns = [0] * len(notetype.fields)
    if columns:
        columns[0] = 1
    labels = meta.columns or [""] * column_count
    if all(not label for label in labels):
        free = (i for i in range(1, len(labels) + 1) if i not in meta_cols)
        for k in range(len(columns)):
            index = next(free, None)
            if index is None:
                break
            columns[k] = index
    else:
        by_name = {lab: i for i, lab in enumerate(labels, 1) if i not in meta_cols}
        for k, name in enumerate(notetype.fields):
            if name in by_name:
                columns[k] = by_name[name]
    if columns and columns[0] == 0:
        free_cols = [i for i in range(1, len(labels) + 1) if i not in meta_cols]
        if not free_cols:
            raise AnkiImportError("the file has no column for the note's first field")
        columns[0] = free_cols[0]
    if meta.tags_column == 0:
        for index in range(max(columns, default=0) + 1, len(labels) + 1):
            if index not in meta_cols:
                meta.tags_column = index
                break
    return columns


def _cell(record: list[str], column: int) -> str | None:
    return record[column - 1] if 0 < column <= len(record) else None


def read_text(
    source: bytes | str | Path,
    *,
    name: str | None = None,
    deck: str | None = None,
    notetype: str | None = None,
) -> AnkiData:
    """Read a plain-text export. `deck` is used when the file names none (default: the file
    name without its extension); `notetype` when the file names none (default: Basic)."""
    if isinstance(source, Path):
        display = name or source.name
        if source.stat().st_size > MAX_TEXT_BYTES:
            raise AnkiImportError("the text file is larger than an import allows")
        source = source.read_bytes()
    else:
        display = name or "notes.txt"
    if isinstance(source, bytes):
        if len(source) > MAX_TEXT_BYTES:
            raise AnkiImportError("the text file is larger than an import allows")
        try:
            source = source.decode("utf-8")
        except UnicodeDecodeError:
            raise AnkiImportError("the text file is not UTF-8 text") from None
    text = source.removeprefix("﻿")
    meta = TextMeta()
    lines = text.splitlines()
    header = _parse_meta(lines, meta)
    first_line = 1
    if lines and lines[0].startswith("tags:"):  # the reader skips it, as in Anki
        text = text[_after_line_end(text, _line_end(text, 0)) :]
        first_line = 2
    if not meta.delimiter_forced:
        meta.delimiter = _detect_delimiter("\n".join(lines[header:]))
    records = parse_csv(text, meta.delimiter, first_line)
    if not records:
        raise AnkiImportError("the text file has no notes")
    if meta.html is None:
        meta.html = any(is_html(f) for _, rec in records[:_PREVIEW] for f in rec)
    default_deck = deck or meta.deck or (Path(display).stem or "Default")
    data = AnkiData(name=display, format="anki-text", notetypes={}, notes=[], cards=None)
    data.warnings += [f"header #{key} is not used" for key in meta.ignored if key]

    def resolve(nt_name: str) -> Notetype:
        found = stock_notetype(nt_name)
        if found is None:
            found = _fallback(nt_name, data)
        data.notetypes[found.id] = found
        return found

    file_notetype = None
    columns: list[int] = []
    if meta.notetype_column == 0:
        file_notetype = resolve(notetype or meta.notetype or "Basic")
        columns = _field_columns(meta, file_notetype, max(1, len(records[0][1])))
    meta_cols = meta.meta_columns()
    for line, record in records:
        nt = file_notetype or resolve(_cell(record, meta.notetype_column) or "Basic")
        if file_notetype is not None:
            raw = [_cell(record, c) if c else None for c in columns]
        else:
            raw = [v for i, v in enumerate(record, 1) if i not in meta_cols]
        values = [_stringify(v, meta.html) if v is not None else "" for v in raw]
        values = (values + [""] * len(nt.fields))[: len(nt.fields)]
        if not raw or raw[0] is None or raw[0] == "":
            data.warnings.append(f"{display}:{line}: skipped: the first field is empty")
            continue
        tags = (_cell(record, meta.tags_column) or "").split() if meta.tags_column else []
        note_deck = _cell(record, meta.deck_column) if meta.deck_column else None
        data.notes.append(
            Note(
                id=line,
                guid=(_cell(record, meta.guid_column) or "") if meta.guid_column else "",
                notetype_id=nt.id,
                fields=tuple(values),
                tags=tuple(dict.fromkeys(tags + meta.global_tags)),
                line=line,
                deck=(note_deck or default_deck).strip() or default_deck,
            )
        )
    return data


def _stringify(value: str, html: bool) -> str:
    """As Anki stores an imported field: escaped unless HTML, line breaks as <br>, ASCII
    control characters other than tab and newline removed, NFC."""
    value = value if html else encode_minimal(value).replace("\n", "<br>")
    value = "".join(ch for ch in value if ch in "\t\n" or not (ord(ch) < 32 or ch == "\x7f"))
    return unicodedata.normalize("NFC", value)


_FALLBACK_ID = -100


def _fallback(name: str, data: AnkiData) -> Notetype:
    """A note type the file names but the app doesn't know: front is the first field, back
    the rest ("plain front and back as a fallback")."""
    for nt in data.notetypes.values():
        if nt.name == name:
            return nt
    data.warnings.append(f"note type {name!r} is unknown: its notes become front/back cards")
    fields = tuple(f"Field {i}" for i in range(1, 33))
    back = "".join(f"{{{{#{f}}}}}<div>{{{{{f}}}}}</div>{{{{/{f}}}}}" for f in fields[1:])
    template = Template("Card 1", 0, "{{Field 1}}", "{{FrontSide}}\n\n<hr id=answer>\n\n" + back)
    return Notetype(_FALLBACK_ID - len(data.notetypes), name, False, fields, (template,))
