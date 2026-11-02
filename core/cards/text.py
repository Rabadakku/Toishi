"""The line layer shared by card files and skills files (docs/card-format.md, "File layout").

A file is a `---` header of `key: value` lines, then blocks that start with
`## Card <id>` (or `## Skill <id>`, or a skills file's `## Section <deck path>`). A block
has key lines, then `### Name` sections that run to the next `###` heading or block. Key
lines are not YAML: everything after the first `: ` is the value, taken literally.
`<!-- ... -->` comments are removed before anything else, keeping every line number.
Nothing here interprets values, except the number helper at the end.
"""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from core.cards.problems import Problem

KEY_LINE = re.compile(r"([a-z][a-z0-9-]*):(?:[ \t]+(.*))?[ \t]*$")
DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?")
BLOCK_HEADING = re.compile(r"##(?!#)[ \t]*(.*?)[ \t]*$")
SECTION_HEADING = re.compile(r"###(?!#)[ \t]*(.*?)[ \t]*$")
CONTENT_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
CHECKLIST_ITEM = re.compile(r"[-*][ \t]+\[([ xX])\][ \t]+(.*?)[ \t]*$")
NUMBERED_ITEM = re.compile(r"(\d{1,4})\.[ \t]+(.*?)[ \t]*$")
NUMBERED_EMPTY = re.compile(r"(\d{1,4})\.[ \t]*$")


@dataclass(frozen=True, slots=True)
class KeyLine:
    key: str
    value: str
    line: int


@dataclass(slots=True)
class SectionSrc:
    """A `### Name` section: its heading line and its content lines (number, text)."""

    name: str
    line: int
    lines: list[tuple[int, str]] = field(default_factory=list)

    def text(self) -> str:
        return join_lines([t for _, t in self.lines])

    def first_line(self) -> int:
        for number, text in self.lines:
            if text.strip():
                return number
        return self.line


@dataclass(slots=True)
class BlockSrc:
    """`## Card <id>` or `## Skill <id>` with its key lines and sections."""

    kind: str
    id: str
    line: int
    keys: dict[str, KeyLine] = field(default_factory=dict)
    sections: list[SectionSrc] = field(default_factory=list)
    start: int = 0  # index of the heading in FileSrc.lines
    end: int = 0  # index one past the block's last line


@dataclass(slots=True)
class FileSrc:
    name: str
    lines: list[str]  # comments removed, one entry per source line
    original: list[str]  # the lines as written (comments kept)
    header: dict[str, KeyLine] = field(default_factory=dict)
    blocks: list[BlockSrc] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)

    def error(self, line: int, message: str, card_id: str | None = None) -> None:
        self.problems.append(Problem(self.name, line, message, "error", card_id))


def join_lines(lines: list[str]) -> str:
    """Section text: trailing spaces dropped, blank lines trimmed at both ends."""
    out = [t.rstrip() for t in lines]
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def decode(data: bytes | str, name: str) -> tuple[str | None, Problem | None]:
    """UTF-8 (a leading BOM is dropped). A decoding error names the line."""
    if isinstance(data, str):
        text = data
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            line = data[: exc.start].count(b"\n") + 1
            return None, Problem(name, line, "the file is not UTF-8 text")
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n"), None


def strip_comments(lines: list[str], name: str) -> tuple[list[str], list[Problem]]:
    """Remove `<!-- ... -->` (possibly over several lines), keeping the line count."""
    out: list[str] = []
    problems: list[Problem] = []
    inside_since: int | None = None
    for number, line in enumerate(lines, start=1):
        kept: list[str] = []
        pos = 0
        while pos <= len(line):
            if inside_since is None:
                start = line.find("<!--", pos)
                if start < 0:
                    kept.append(line[pos:])
                    break
                kept.append(line[pos:start])
                inside_since = number
                pos = start + 4
            else:
                end = line.find("-->", pos)
                if end < 0:
                    break
                inside_since = None
                pos = end + 3
        out.append("".join(kept))
    if inside_since is not None:
        problems.append(Problem(name, inside_since, "comment '<!--' is never closed with '-->'"))
    return out, problems


def read_file(
    data: bytes | str, name: str, block_kind: str, *, other_blocks: Mapping[str, str] | None = None
) -> FileSrc:
    """Split a card or skills file into header and blocks. Problems are located, never raised.
    `other_blocks` adds block kinds whose title is not an ID but text the caller checks
    (heading word -> what the title is, for messages: {"Section": "a deck path"})."""
    text, problem = decode(data, name)
    if text is None:
        src = FileSrc(name, [], [])
        src.problems.append(problem or Problem(name, 1, "the file can't be read"))
        return src
    original = text.split("\n")
    lines, comment_problems = strip_comments(original, name)
    src = FileSrc(name, lines, original)
    src.problems.extend(comment_problems)
    index = _read_header(src)
    if index is None:
        return src
    _read_blocks(src, index, block_kind, other_blocks=other_blocks)
    return src


def _read_header(src: FileSrc) -> int | None:
    lines = src.lines
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or lines[i].strip() != "---":
        src.error(
            i + 1 if i < len(lines) else max(len(lines), 1),
            "the file must start with a '---' header",
        )
        return None
    opening = i + 1
    i += 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            if "format" not in src.header:
                src.error(opening, "the header has no 'format:' line")
            return i + 1
        if line.startswith("##"):
            break  # a block heading: the header was never closed
        if line.strip():
            m = KEY_LINE.fullmatch(line.strip())
            if m is None:
                src.error(i + 1, f"expected 'key: value' in the header, got {line.strip()!r}")
            else:
                _add_key(src, src.header, m, i + 1, "the header")
        i += 1
    src.error(opening, "the header is never closed with '---'")
    return None


def _add_key(
    src: FileSrc,
    keys: dict[str, KeyLine],
    m: re.Match[str],
    number: int,
    where: str,
    card_id: str | None = None,
) -> None:
    key, value = m.group(1), (m.group(2) or "").strip()
    if key in keys:
        src.error(
            number, f"{key} appears twice in {where} (first at line {keys[key].line})", card_id
        )
        return
    if not value:
        src.error(number, f"{key} has no value", card_id)
        return
    keys[key] = KeyLine(key, value, number)


def reread_block(
    src: FileSrc, block: BlockSrc, new_lines: list[str]
) -> tuple[BlockSrc | None, list[Problem]]:
    """Read one block again from replacement lines (same count, so same line numbers)."""
    if len(new_lines) != block.end - block.start:
        raise ValueError("replacement lines must keep the block's line count")
    lines = list(src.lines)
    lines[block.start : block.end] = new_lines
    tmp = FileSrc(src.name, lines, lines)
    _read_blocks(tmp, block.start, block.kind, stop=block.end)
    found = tmp.blocks[0] if tmp.blocks else None
    return found, tmp.problems


def _read_blocks(
    src: FileSrc,
    index: int,
    block_kind: str,
    stop: int | None = None,
    *,
    other_blocks: Mapping[str, str] | None = None,
) -> None:
    lines = src.lines
    block: BlockSrc | None = None
    section: SectionSrc | None = None
    for i in range(index, len(lines) if stop is None else stop):
        number = i + 1
        line = lines[i]
        stripped = line.strip()
        heading = BLOCK_HEADING.fullmatch(line) if line.startswith("##") else None
        if heading is not None:
            if block is not None:
                block.end = i
            title = heading.group(1)
            block = _start_block(src, title, number, i, block_kind, other_blocks or {})
            section = None
            continue
        sub = SECTION_HEADING.fullmatch(line) if line.startswith("###") else None
        if block is None:
            if stripped and not (stripped.startswith("# ") or stripped == "#"):
                what = "a ### section" if sub is not None else repr(stripped[:40])
                src.error(number, f"{what} outside a block: start one with '## {block_kind} <id>'")
            continue
        if sub is not None:
            section = SectionSrc(sub.group(1), number)
            block.sections.append(section)
            continue
        if section is not None:
            section.lines.append((number, line))
            continue
        if not stripped:
            continue
        m = KEY_LINE.fullmatch(stripped)
        if m is None or line[:1].isspace():
            src.error(
                number,
                f"expected 'key: value' or a ### section, got {stripped[:40]!r}",
                block.id or None,
            )
            continue
        where = f"{(block.kind or block_kind).lower()} {block.id}"
        _add_key(src, block.keys, m, number, where, block.id or None)
    if block is not None:
        block.end = len(lines) if stop is None else stop


def _start_block(
    src: FileSrc,
    title: str,
    number: int,
    index: int,
    block_kind: str,
    other_blocks: Mapping[str, str],
) -> BlockSrc:
    word, _, rest = title.partition(" ")
    rest = rest.strip()
    if word in other_blocks:
        if not rest:
            src.error(number, f"'## {word}' needs {other_blocks[word]}")
        block = BlockSrc(word, rest, number, start=index)
        src.blocks.append(block)
        return block
    if word != block_kind:
        starts = [f"'## {block_kind} <id>'"] + [
            f"'## {kind} <{what.removeprefix('a ')}>'" for kind, what in other_blocks.items()
        ]
        src.error(number, f"unknown heading '## {title}': blocks start with {' or '.join(starts)}")
        block = BlockSrc("", "", number, start=index)
        src.blocks.append(block)
        return block
    if not rest:
        src.error(number, f"'## {block_kind}' needs an ID")
    elif not CONTENT_ID.fullmatch(rest):
        src.error(number, f"bad ID {rest!r}: use lowercase letters, digits, '.', '-' and '_'")
        rest = ""
    block = BlockSrc(block_kind, rest, number, start=index)
    src.blocks.append(block)
    return block


# ---------------------------------------------------------------- list helpers


@dataclass(frozen=True, slots=True)
class Item:
    line: int
    marker: str  # the number of a numbered item, or ' '/'x' of a checklist item
    text: str  # first line plus continuation lines, stripped


def numbered_items(section: SectionSrc) -> tuple[list[Item], list[tuple[int, str]]]:
    """A numbered list (`1. text`); continuation lines join the item before them.
    Returns the items and any (line, text) that came before the first item."""
    items: list[tuple[int, str, list[str]]] = []
    stray: list[tuple[int, str]] = []
    for number, line in section.lines:
        m = NUMBERED_ITEM.fullmatch(line) or NUMBERED_EMPTY.fullmatch(line)
        if m is not None and not line[:1].isspace():
            text = m.group(2) if m.re is NUMBERED_ITEM else ""
            items.append((number, m.group(1), [text]))
        elif items:
            items[-1][2].append(line)
        elif line.strip():
            stray.append((number, line.strip()))
    return [Item(n, marker, join_lines(body).strip()) for n, marker, body in items], stray


def checklist_items(lines: list[tuple[int, str]]) -> tuple[list[Item], list[tuple[int, str]]]:
    """`- [x] right` / `- [ ] wrong`, one per line. Returns items and other non-blank lines."""
    items: list[Item] = []
    stray: list[tuple[int, str]] = []
    for number, line in lines:
        m = CHECKLIST_ITEM.fullmatch(line.strip())
        if m is not None:
            items.append(Item(number, m.group(1).lower(), m.group(2)))
        elif line.strip():
            stray.append((number, line.strip()))
    return items, stray


def positive_decimal(text: str) -> float | None:
    """A positive number written as digits with an optional decimal part (`6`, `2.5`), as
    `time:`, `hours:` and the pace keys take it; None for anything else."""
    if not DECIMAL.fullmatch(text):
        return None
    value = float(text)
    return value if 0 < value < math.inf else None


def split_top(text: str, sep: str) -> list[str]:
    """Split at `sep` outside (), [] and {} (`k = int(1, 9); m = 2` -> two parts)."""
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(text):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(depth - 1, 0)
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def insertion_starts(line: str) -> list[int]:
    """Where `[[` opens an insertion: not right after a backslash (`\\[[0, 1]\\]` is display
    math starting with an interval) and not inside a `code span` (written literally)."""
    spans: list[tuple[int, int]] = []
    pos = 0
    while (open_tick := line.find("`", pos)) >= 0:
        close_tick = line.find("`", open_tick + 1)
        if close_tick < 0:
            break
        spans.append((open_tick, close_tick))
        pos = close_tick + 1
    starts: list[int] = []
    pos = 0
    while (start := line.find("[[", pos)) >= 0:
        pos = start + 1
        if start > 0 and line[start - 1] == "\\":
            continue
        if any(a < start < b for a, b in spans):
            continue
        if starts and start == starts[-1] + 1:
            continue  # [[[ : the first [[ already counts
        starts.append(start)
    return starts
