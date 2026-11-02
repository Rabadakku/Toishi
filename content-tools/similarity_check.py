"""Flag new cards that are too close to the problems they were inspired by.

Used in the clean-room content workflow (docs/prompts/clean-room-decks.md): sources stay in the
author's private folder, and this check compares every drafted card against them before the
card may enter a pack. It reports only card IDs, source file names and scores, never any source
text, so its output can be shared with anyone.

usage: python content-tools/similarity_check.py --sources DIR --drafts DIR [--json]
  --sources  one problem (with its solution, if any) per .txt or .md file, any depth
  --drafts   card files in the Toishi card format (`## Card <id>` sections)
Exit status: 0 when nothing is flagged, 1 when something is, 2 on bad input.

A card is flagged when, against any one source problem:
  - 30% or more of its 5-word runs also occur in that source (with at least 4 shared runs),
  - it shares a run of 12 or more words in a row, or
  - its question's three or more distinct numbers (other than 0, 1, 2) all occur in that source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

GRAM = 5
CONTAINMENT = 0.30
MIN_SHARED = 4
RUN = 12
TRIVIAL_NUMBERS = frozenset({"0", "1", "2"})
SOURCE_SUFFIXES = (".txt", ".md")

_CARD = re.compile(r"^## Card (\S+)\s*$", re.MULTILINE)
_SECTION = re.compile(r"^### (.+?)\s*$", re.MULTILINE)
_KEY_LINE = re.compile(r"^[a-z][a-z-]*:\s.*$", re.MULTILINE)
_LATEX_CMD = re.compile(r"\\([a-zA-Z]+)")
_TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
_QUESTION_SECTIONS = ("question", "cued question", "front")


@dataclass(frozen=True)
class Flag:
    card: str
    draft_file: str
    source: str
    containment: float
    longest_run: int
    same_numbers: bool


def tokens(text: str) -> list[str]:
    """Words and numbers, lowercased; LaTeX commands kept as words (\\frac -> frac)."""
    text = _LATEX_CMD.sub(r" \1 ", text.lower())
    return _TOKEN.findall(text)


def grams(toks: list[str]) -> set[tuple[str, ...]]:
    return {tuple(toks[i : i + GRAM]) for i in range(len(toks) - GRAM + 1)}


def numbers(toks: list[str]) -> frozenset[str]:
    return frozenset(t for t in toks if t[0].isdigit() and t not in TRIVIAL_NUMBERS)


def longest_common_run(a: list[str], b: list[str]) -> int:
    """Length of the longest run of tokens that appears in both (dynamic programming)."""
    best = 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def split_cards(text: str) -> list[tuple[str, str, str]]:
    """(card id, whole card text without key lines, question text) for each card."""
    heads = list(_CARD.finditer(text))
    out = []
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[head.end() : end]
        sections = list(_SECTION.finditer(body))
        question = []
        for k, sec in enumerate(sections):
            stop = sections[k + 1].start() if k + 1 < len(sections) else len(body)
            name = sec.group(1).strip().lower()
            if name in _QUESTION_SECTIONS or name.startswith("part "):
                question.append(body[sec.end() : stop])
        out.append((head.group(1), _KEY_LINE.sub(" ", body), "\n".join(question)))
    return out


def load_sources(folder: Path) -> dict[str, list[str]]:
    sources = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
            sources[str(path.relative_to(folder))] = tokens(path.read_text(errors="replace"))
    return sources


def check(sources: dict[str, list[str]], drafts: Path) -> tuple[list[Flag], int]:
    index: dict[tuple[str, ...], set[str]] = defaultdict(set)
    by_number: dict[str, set[str]] = defaultdict(set)
    for name, toks in sources.items():
        for g in grams(toks):
            index[g].add(name)
        for n in numbers(toks):
            by_number[n].add(name)

    flags: list[Flag] = []
    cards = 0
    for path in sorted(drafts.rglob("*.md")):
        for card_id, body, question in split_cards(path.read_text(errors="replace")):
            cards += 1
            toks = tokens(body)
            mine = grams(toks)
            shared: dict[str, int] = defaultdict(int)
            for g in mine:
                for name in index.get(g, ()):
                    shared[name] += 1
            q_nums = numbers(tokens(question))
            # Sources that use every one of the question's (three or more) numbers.
            same: set[str] = set()
            if len(q_nums) >= 3:
                same = set.intersection(*(by_number.get(n, set()) for n in q_nums))
            for name in set(shared) | same:
                containment = shared.get(name, 0) / len(mine) if mine else 0.0
                run = longest_common_run(toks, sources[name]) if shared.get(name) else 0
                too_close = (
                    containment >= CONTAINMENT and shared[name] >= MIN_SHARED
                ) or run >= RUN
                if too_close or name in same:
                    flags.append(
                        Flag(
                            card_id,
                            str(path.relative_to(drafts)),
                            name,
                            round(containment, 3),
                            run,
                            name in same,
                        )
                    )
    return flags, cards


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--drafts", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="print the flags as JSON")
    args = parser.parse_args(argv)
    for folder in (args.sources, args.drafts):
        if not folder.is_dir():
            print(f"error: not a folder: {folder}", file=sys.stderr)
            return 2
    sources = load_sources(args.sources)
    if not sources:
        print(f"error: no .txt or .md source files in {args.sources}", file=sys.stderr)
        return 2
    flags, cards = check(sources, args.drafts)
    if args.json:
        print(json.dumps([asdict(f) for f in flags], indent=2))
    else:
        for f in flags:
            reasons = []
            if f.containment >= CONTAINMENT:
                reasons.append(f"{f.containment:.0%} of its 5-word runs")
            if f.longest_run >= RUN:
                reasons.append(f"a {f.longest_run}-word run")
            if f.same_numbers:
                reasons.append("the same numbers")
            print(f"FLAG {f.card} ({f.draft_file}) ~ {f.source}: {', '.join(reasons)}")
        print(
            f"{cards} cards checked against {len(sources)} source problems: "
            f"{len({f.card for f in flags})} flagged."
        )
    return 1 if flags else 0


if __name__ == "__main__":
    raise SystemExit(main())
