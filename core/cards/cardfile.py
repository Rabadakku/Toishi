"""Card files (`format: mastery-cards 1`) -> core.model.Card, with file:line problems.

`read_card_file` splits the file (text.py); `build_card` turns one `## Card` block into
a Card, checking everything that needs no computer algebra: keys, kinds, sections,
step tags, choices, cloze blanks, images, math delimiters. Answers are parsed and
self-checked later (checks.py), and templates are expanded by template.py/sweep.py.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import get_args

from core.cards import decks
from core.cards import text as t
from core.cards.problems import Problem
from core.grader import parse_wrong_field
from core.grader.errors import InputError
from core.grader.parser import parse as parse_math
from core.grader.tokens import Vocabulary
from core.model import (
    AnswerType,
    Card,
    CardKind,
    CardPart,
    CheckerOptions,
    Choice,
    Provenance,
    ShapeError,
    SolutionStep,
    WrongAnswer,
)

FORMAT = "mastery-cards 1"
INSTANCE_SEPARATOR = "--"  # template instance ids: <template id>--<seed as 8 hex digits>

CHECKER_KEYS = ("vars", "domain", "tolerance", "exact", "form", "endpoints", "require-constant",
                "units", "sig-figs", "domain-strict")  # fmt: skip
TEMPLATE_KEYS = ("let", "require")
CARD_KEYS = frozenset(
    {
        "kind", "skill", "uses", "difficulty", "answer-type", "answer", "wrong", "plot",
        "calculator", "angles", "cue", "error-step", "tagged", "deck", "tags", "source",
        "source-url", "license", "modified", "verified", "time", *CHECKER_KEYS, *TEMPLATE_KEYS,
    }
)  # fmt: skip
NOT_IN_HEADER = frozenset(
    {"answer", "wrong", "error-step", "plot", "cue", "vars", "let", "require", "time"}
)
HEADER_KEYS = (CARD_KEYS - NOT_IN_HEADER) | {"format"}
PART_KEYS = frozenset({"answer-type", "answer", "wrong", "skill", "time", *CHECKER_KEYS})
UNTIMED_KINDS = frozenset({"example", "flashcard", "cloze"})  # no standard time

KINDS: tuple[str, ...] = get_args(CardKind)
ANSWER_TYPES: tuple[str, ...] = get_args(AnswerType)
QUESTION_KINDS = frozenset({"problem", "example", "find-error", "method"})
ALL_KINDS = frozenset(KINDS)
SECTIONS: dict[str, frozenset[str]] = {
    "Question": QUESTION_KINDS,
    "Choices": ALL_KINDS,
    "Cued Question": frozenset({"problem"}),
    "Shown Work": frozenset({"find-error"}),
    "Reasons": frozenset({"find-error"}),
    "Hints": frozenset({"problem", "find-error", "method"}),
    "Answer": frozenset({"problem", "find-error"}),
    "Solution": QUESTION_KINDS,
    "Rubric": frozenset({"problem"}),
    "Alternative Solution": frozenset({"problem"}),
    "Front": frozenset({"flashcard"}),
    "Back": frozenset({"flashcard"}),
    "Text": frozenset({"cloze"}),
    "Extra": frozenset({"flashcard", "cloze"}),
    "Notes": ALL_KINDS,
}
_SECTION_BY_LOWER = {name.lower(): name for name in SECTIONS}
PART_HEADING = re.compile(r"part[ \t]+([A-Za-z0-9]+)", re.IGNORECASE)
_STEP = re.compile(r"\[([^\]]*)\][ \t]*([^:\n]*?)[ \t]*:[ \t]*(.*)", re.DOTALL)
_STEP_START = re.compile(r"\d{1,4}\.[ \t]+\[")
_IMAGE = re.compile(r"!\[[^\]\n]*\]\(([^)\s]*)(?:[ \t]+\"[^\"\n]*\")?\)")
_CLOZE_OPEN = re.compile(r"\{\{c")
_CLOZE = re.compile(r"\{\{c(\d+)::(.+?)(?:::([^{}]*?))?\}\}", re.DOTALL)

type MediaLookup = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class BuildContext:
    """Where a card comes from. `media(ref)` returns the media name an image reference
    resolves to, or None when the file is missing; None skips the image check."""

    file: str
    media: MediaLookup | None = None
    pack: bool = False  # content-pack rules: step tags, deck and known skills required


@dataclass(frozen=True, slots=True)
class StepClaim:
    """A `check:` line of a ### Solution step (format 1.1), as written (MATH-17)."""

    step: int
    text: str
    line: int


_CLAIM = re.compile(r"check:[ \t]*(.*?)[ \t]*", re.IGNORECASE)


@dataclass(slots=True)
class Built:
    """The result of building one block. `card` is None when there were errors."""

    card: Card | None
    problems: list[Problem]
    line: int
    lines: dict[str, int] = field(default_factory=dict)  # "answer", "part a", ... -> line
    explicit_difficulty: bool = False
    media: list[str] = field(default_factory=list)
    images: list[tuple[str, str]] = field(default_factory=list)  # (reference, media name)
    claims: list[StepClaim] = field(default_factory=list)  # the solution's `check:` lines


def read_card_file(data: bytes | str, name: str) -> t.FileSrc:
    src = t.read_file(data, name, "Card")
    if src.header:
        fmt = src.header.get("format")
        if fmt is not None and fmt.value != FORMAT:
            src.error(fmt.line, f"format is {fmt.value!r}; this app reads {FORMAT!r}")
        for key, kl in src.header.items():
            if key in NOT_IN_HEADER:
                src.error(kl.line, f"{key} can't be a file default; put it on each card")
            elif key not in HEADER_KEYS:
                src.error(kl.line, f"unknown key {key!r} in the header")
    return src


def is_template(block: t.BlockSrc) -> bool:
    """Params in `vars`, a `let` or `require` line, or a [[...]] insertion in the text."""
    if "let" in block.keys or "require" in block.keys:
        return True
    vars_line = block.keys.get("vars")
    if vars_line is not None and any("=" in p for p in t.split_top(vars_line.value, ";")):
        return True
    for key, kl in block.keys.items():
        if key not in {"answer", "wrong", "vars"} and t.insertion_starts(kl.value):
            return True
    return any(t.insertion_starts(line) for s in block.sections for _, line in s.lines)


class _Builder:
    def __init__(self, block: t.BlockSrc, header: Mapping[str, t.KeyLine], ctx: BuildContext):
        self.block = block
        self.ctx = ctx
        self.problems: list[Problem] = []
        self.lines: dict[str, int] = {}
        self.media: list[str] = []
        self.images: list[tuple[str, str]] = []
        self.claims: list[StepClaim] = []
        self.part_skill_lines: dict[str, int] = {}  # part label -> its `skill:` line
        self.keys: dict[str, t.KeyLine] = {k: v for k, v in header.items() if k != "format"}
        self.keys.update(block.keys)

    # ------------------------------------------------------------ helpers

    def error(self, line: int, message: str) -> None:
        self.problems.append(Problem(self.ctx.file, line, message, "error", self.block.id))

    def warn(self, line: int, message: str) -> None:
        self.problems.append(Problem(self.ctx.file, line, message, "warning", self.block.id))

    def get(self, key: str) -> str | None:
        kl = self.keys.get(key)
        return kl.value if kl is not None else None

    def line_of(self, key: str) -> int:
        kl = self.keys.get(key)
        return kl.line if kl is not None else self.block.line

    def choose(self, key: str, allowed: tuple[str, ...], default: str) -> str:
        value = self.get(key)
        if value is None:
            return default
        if value not in allowed:
            self.error(self.line_of(key), f"{key}: expected {' or '.join(allowed)}, got {value!r}")
            return default
        return value

    def yes_no(self, key: str) -> bool:
        return self.choose(key, ("yes", "no"), "no") == "yes"

    def ids(self, key: str, value: str, line: int) -> tuple[str, ...]:
        out: list[str] = []
        for raw in value.split(","):
            item = raw.strip()
            if not item:
                self.error(line, f"{key}: empty item in {value!r}")
            elif not t.CONTENT_ID.fullmatch(item):
                self.error(line, f"{key}: bad skill ID {item!r}")
            else:
                out.append(item)
        return tuple(out)

    def skill_id(self, value: str | None, line: int, what: str = "skill") -> str | None:
        if value is None:
            return None
        if not t.CONTENT_ID.fullmatch(value):
            self.error(line, f"{what}: bad skill ID {value!r}")
            return None
        return value

    def minutes(self, kl: t.KeyLine | None, owner: str = "") -> float | None:
        """`time:` a standard time in minutes, a positive decimal such as 6 or 2.5. A
        template's `[[...]]` is checked in each instance."""
        if kl is None or t.insertion_starts(kl.value):
            return None
        value = t.positive_decimal(kl.value)
        if value is None:
            self.error(
                kl.line, f"{owner}time: expected a positive number of minutes, got {kl.value!r}"
            )
        return value

    def checker(self, keys: Mapping[str, t.KeyLine]) -> CheckerOptions:
        values = {k.replace("-", "_"): keys[k].value for k in CHECKER_KEYS if k in keys}
        return CheckerOptions(**values)

    def wrong(self, kl: t.KeyLine | None) -> tuple[WrongAnswer, ...]:
        if kl is None:
            return ()
        out: list[WrongAnswer] = []
        for w in parse_wrong_field(kl.value):
            if not w.answer:
                self.error(kl.line, "wrong: an entry has no answer before '=>'")
                continue
            out.append(WrongAnswer(answer=w.answer, feedback=w.feedback, step=w.step))
        if not out:
            self.error(kl.line, "wrong: no answers given")
        return tuple(out)

    # ------------------------------------------------------------ sections

    def sections(self, kind: str) -> tuple[dict[str, t.SectionSrc], list[t.SectionSrc]]:
        named: dict[str, t.SectionSrc] = {}
        parts: list[t.SectionSrc] = []
        for sec in self.block.sections:
            part = PART_HEADING.fullmatch(sec.name)
            if part is not None:
                sec.name = f"Part {part.group(1)}"
                if kind != "problem":
                    self.error(sec.line, f"### {sec.name} is only for problem cards, not {kind}")
                elif any(p.name == sec.name for p in parts):
                    self.error(sec.line, f"### {sec.name} appears twice")
                else:
                    parts.append(sec)
                continue
            name = _SECTION_BY_LOWER.get(sec.name.lower())
            if name is None:
                self.error(sec.line, f"unknown section '### {sec.name}'")
                continue
            if name in named:
                self.error(sec.line, f"### {name} appears twice (first at line {named[name].line})")
                continue
            if kind not in SECTIONS[name]:
                self.error(sec.line, f"### {name} isn't used by {kind} cards")
                continue
            sec.name = name
            named[name] = sec
        return named, parts

    def markdown(self, sec: t.SectionSrc | None, *, required: str | None = None) -> str | None:
        if sec is None:
            if required:
                self.error(self.block.line, required)
            return None
        value = sec.text()
        if not value:
            self.error(sec.line, f"### {sec.name} is empty")
            return None
        self.check_text(value, sec.first_line())
        return value

    def check_text(self, value: str, line: int) -> None:
        """Images exist, math delimiters pair up, no cloze-looking text outside clozes."""
        for m in _IMAGE.finditer(value):
            ref = m.group(1)
            at = line + value.count("\n", 0, m.start())
            self.check_image(ref, at)
        problem = math_delimiter_problem(value)
        if problem is not None:
            offset, message = problem
            self.error(line + value.count("\n", 0, offset), message)

    def check_image(self, ref: str, line: int) -> None:
        lower = ref.lower()
        if not ref:
            self.error(line, "an image has no path")
        elif "://" in ref or lower.startswith(("data:", "/", "\\")) or re.match(r"[a-z]:", lower):
            self.error(line, f"image {ref!r}: use a path relative to the card file")
        elif not lower.endswith((".svg", ".png")):
            self.error(line, f"image {ref!r}: images must be SVG or PNG")
        elif self.ctx.media is not None:
            name = self.ctx.media(ref)
            if name is None:
                self.error(line, f"image {ref!r} not found next to {self.ctx.file}")
            else:
                self.media.append(name)
                self.images.append((ref, name))

    def checklist(self, sec: t.SectionSrc, what: str) -> tuple[Choice, ...]:
        items, stray = t.checklist_items(sec.lines)
        for number, text in stray:
            self.error(
                number, f"### {what}: expected '- [x] ...' or '- [ ] ...', got {text[:40]!r}"
            )
        out: list[Choice] = []
        for item in items:
            if not item.text:
                self.error(item.line, f"### {what}: an option is empty")
                continue
            self.check_text(item.text, item.line)
            out.append(Choice(text_md=item.text, correct=item.marker == "x"))
        if not items and not stray:
            self.error(sec.line, f"### {what} is empty")
        return tuple(out)

    def hints(self, sec: t.SectionSrc | None) -> tuple[str, ...]:
        if sec is None:
            return ()
        items, stray = t.numbered_items(sec)
        for number, text in stray:
            self.error(number, f"### Hints must be a numbered list (1. ...), got {text[:40]!r}")
        out: list[str] = []
        for item in items:
            if not item.text:
                self.error(item.line, "### Hints: a hint is empty")
                continue
            self.check_text(item.text, item.line)
            out.append(item.text)
        if not items and not stray:
            self.error(sec.line, "### Hints is empty")
        return tuple(out)

    def steps(
        self, sec: t.SectionSrc | None, *, require_tags: bool
    ) -> tuple[tuple[SolutionStep, ...], str | None]:
        """A step-tagged list (`N. [skill-id] Label: content`) or, if untagged, Markdown."""
        if sec is None:
            return (), None
        body = sec.text()
        if not body:
            self.error(sec.line, f"### {sec.name} is empty")
            return (), None
        first = body.lstrip("\n").split("\n", 1)[0]
        if not _STEP_START.match(first):
            later = next(
                (n for n, line in sec.lines if _STEP_START.match(line) and n > sec.first_line()),
                None,
            )
            if later is not None:
                self.error(
                    later, f"### {sec.name}: a step-tagged list must start at the first line"
                )
            elif require_tags:
                self.error(
                    sec.first_line(),
                    f"### {sec.name} must be numbered, skill-tagged steps: "
                    "N. [skill-id] Label: ...",
                )
            else:
                self.check_text(body, sec.first_line())
                return (), body
            return (), None
        items, _ = t.numbered_items(sec)
        steps: list[SolutionStep] = []
        expected: int | None = None
        for item in items:
            number = int(item.marker)
            m = _STEP.fullmatch(item.text)
            if m is None or not m.group(2):
                self.error(item.line, f"step {number}: write it as {number}. [skill-id] Label: ...")
                continue
            skill = m.group(1).strip()
            if not t.CONTENT_ID.fullmatch(skill):
                self.error(item.line, f"step {number}: bad skill ID {skill!r}")
                continue
            if expected is None and number not in (0, 1):
                self.error(item.line, f"### {sec.name}: steps start at 0 or 1, not {number}")
            elif expected is not None and number != expected:
                self.error(item.line, f"### {sec.name}: step {number} should be step {expected}")
            expected = number + 1
            content = m.group(3).strip()
            if sec.name == "Solution":
                content = self.take_claims(number, content, sec)
            self.check_text(f"{m.group(2)}\n{content}", item.line)
            steps.append(
                SolutionStep(
                    number=number, skill_id=skill, label=m.group(2).strip(), body_md=content
                )
            )
        return tuple(steps), None

    def take_claims(self, step: int, content: str, sec: t.SectionSrc) -> str:
        """Move the step's `check:` lines (continuation lines) out of what is displayed."""
        kept: list[str] = []
        for i, line in enumerate(content.split("\n")):
            m = _CLAIM.fullmatch(line.strip()) if i else None
            if m is None:
                kept.append(line)
                continue
            number = next(
                (n for n, raw in sec.lines if raw.strip() == line.strip()), sec.first_line()
            )
            self.claims.append(StepClaim(step, m.group(1), number))
        return "\n".join(kept).strip()

    def part(self, sec: t.SectionSrc) -> CardPart | None:
        label = sec.name.split(" ", 1)[1]
        keys: dict[str, t.KeyLine] = {}
        prompt: list[tuple[int, str]] = []
        for number, line in sec.lines:
            if not prompt:
                if not line.strip():
                    continue
                m = t.KEY_LINE.fullmatch(line) if not line[:1].isspace() else None
                if m is not None:
                    key, value = m.group(1), (m.group(2) or "").strip()
                    if key not in PART_KEYS:
                        self.error(number, f"unknown key {key!r} in ### Part {label}")
                    elif key in keys:
                        self.error(number, f"{key} appears twice in ### Part {label}")
                    elif not value:
                        self.error(number, f"{key} has no value")
                    else:
                        keys[key] = t.KeyLine(key, value, number)
                    continue
            prompt.append((number, line))
        answer_type = keys["answer-type"].value if "answer-type" in keys else "self"
        if answer_type not in ANSWER_TYPES:
            self.error(keys["answer-type"].line, f"unknown answer type {answer_type!r}")
            return None
        choices: tuple[Choice, ...] = ()
        if answer_type == "choice":
            items, rest = t.checklist_items(prompt)
            choices = tuple(Choice(text_md=i.text, correct=i.marker == "x") for i in items)
            prompt = [
                (n, line) for n, line in prompt if (n, line.strip()) in rest or not line.strip()
            ]
            if not choices:
                self.error(sec.line, f"### Part {label} is a choice: list options as - [x] / - [ ]")
        prompt_md = t.join_lines([line for _, line in prompt])
        if not prompt_md:
            self.error(sec.line, f"### Part {label} has no prompt")
            return None
        self.check_text(prompt_md, prompt[0][0] if prompt else sec.line)
        answer = keys.get("answer")
        self.lines[f"part {label}"] = answer.line if answer else sec.line
        if answer is not None and answer_type == "self":
            self.error(answer.line, f"### Part {label}: answer given but answer-type is self")
        if answer is None and answer_type not in {"self", "choice"}:
            self.error(sec.line, f"### Part {label}: answer-type {answer_type} needs an answer")
        skill = keys.get("skill")
        if skill is not None:
            self.part_skill_lines[label] = skill.line
        return CardPart(
            label=label,
            prompt_md=prompt_md,
            answer_type=answer_type,  # type: ignore[arg-type]
            answer=answer.value if answer else None,
            checker=self.checker(keys),
            skill_id=self.skill_id(skill.value, skill.line) if skill else None,
            choices=choices,
            wrong=self.wrong(keys.get("wrong")),
            time_minutes=self.minutes(keys.get("time"), f"### Part {label}: "),
        )

    # ------------------------------------------------------------ the card

    def build(self) -> Built:
        block = self.block
        for key, kl in block.keys.items():
            if key not in CARD_KEYS:
                self.error(kl.line, f"unknown key {key!r}")
        kind = self.choose("kind", KINDS, "problem")
        answer_type = self.choose("answer-type", ANSWER_TYPES, "self")
        if "answer-type" in self.keys and self.get("answer-type") not in ANSWER_TYPES:
            answer_type = "self"
        tier = 2
        explicit = "difficulty" in self.keys
        if explicit:
            raw = self.get("difficulty") or ""
            if raw in {"1", "2", "3", "4", "5"}:
                tier = int(raw)
            else:
                self.error(self.line_of("difficulty"), f"difficulty: expected 1 to 5, got {raw!r}")
        error_step: int | None = None
        if "error-step" in self.keys:
            raw = self.get("error-step") or ""
            if raw.isdigit():
                error_step = int(raw)
            else:
                self.error(
                    self.line_of("error-step"), f"error-step: expected a step number, got {raw!r}"
                )
            if kind != "find-error":
                self.error(self.line_of("error-step"), "error-step is only for find-error cards")
        cue = self.get("cue")
        if cue is not None and cue != "required":
            self.error(self.line_of("cue"), f"cue: the only value is 'required', got {cue!r}")
        time_minutes = self.minutes(self.keys.get("time"))
        if "time" in self.keys and kind in UNTIMED_KINDS:
            self.error(self.line_of("time"), f"time: {kind} cards have no standard time")
        deck = self.get("deck")
        if deck is not None and any(not seg.strip() for seg in deck.split("::")):
            self.error(self.line_of("deck"), f"deck: empty level in {deck!r}")
        elif deck is not None:
            deck = decks.normalize(deck)
        skill = self.skill_id(self.get("skill"), self.line_of("skill"))
        uses = (
            self.ids("uses", self.get("uses") or "", self.line_of("uses"))
            if "uses" in self.keys
            else ()
        )
        tags = tuple(x.strip() for x in (self.get("tags") or "").split(",") if x.strip())
        plot = self.get("plot")
        answer = self.get("answer")
        self.lines["answer"] = self.line_of("answer") if answer else self.line_of("answer-type")
        wrong = self.wrong(self.keys.get("wrong"))

        named, part_secs = self.sections(kind)
        parts = tuple(p for p in (self.part(s) for s in part_secs) if p is not None)
        if parts and ("answer" in self.keys or "answer-type" in self.keys):
            where = self.line_of("answer-type" if "answer-type" in self.keys else "answer")
            self.error(where, "a multi-part card sets answer-type and answer in each ### Part")
        if answer is not None and answer_type == "self":
            self.error(
                self.line_of("answer"), "answer given but answer-type is self: set answer-type"
            )
        if answer is None and answer_type not in {"self", "choice"} and not parts:
            self.error(self.line_of("answer-type"), f"answer-type {answer_type} needs an answer")
        if wrong and answer_type in {"self", "choice"}:
            self.error(
                self.line_of("wrong"),
                f"wrong answers need an auto-checked answer-type, not {answer_type}",
            )

        choices: tuple[Choice, ...] = ()
        if "Choices" in named:
            if answer_type != "choice":
                self.error(named["Choices"].line, "### Choices needs answer-type: choice")
            choices = self.checklist(named["Choices"], "Choices")
        elif answer_type == "choice":
            self.error(self.line_of("answer-type"), "answer-type choice needs a ### Choices list")
        if answer_type == "choice" and answer is not None:
            self.error(
                self.line_of("answer"),
                "choice answers are marked [x] in ### Choices, not in answer",
            )

        question = self.markdown(named.get("Question"))
        solution, solution_md = self.steps(
            named.get("Solution"), require_tags=self.ctx.pack and kind in QUESTION_KINDS
        )
        alt, alt_md = self.steps(named.get("Alternative Solution"), require_tags=self.ctx.pack)
        shown: tuple[SolutionStep, ...] = ()
        reasons: tuple[Choice, ...] = ()
        front = back = text_md = None
        if kind in QUESTION_KINDS and question is None:
            self.error(block.line, f"{kind} card has no ### Question")
        if kind in QUESTION_KINDS and not solution and solution_md is None:
            if kind == "example" or self.ctx.pack:
                self.error(block.line, f"{kind} card has no ### Solution")
            elif "Solution" not in named:
                self.warn(block.line, "no ### Solution: the student can't check their work")
        if kind == "flashcard":
            front = self.markdown(named.get("Front"), required="flashcard has no ### Front")
            back = self.markdown(named.get("Back"), required="flashcard has no ### Back")
        if kind == "cloze":
            text_md = self.markdown(named.get("Text"), required="cloze card has no ### Text")
            if text_md is not None:
                self.check_cloze(text_md, named["Text"].first_line())
        if kind == "find-error":
            shown, _ = self.steps(named.get("Shown Work"), require_tags=True)
            if "Shown Work" not in named:
                self.error(block.line, "find-error card has no ### Shown Work")
            if error_step is None:
                self.error(
                    block.line, "find-error card needs error-step: the number of the wrong step"
                )
            elif shown and error_step not in {s.number for s in shown}:
                self.error(
                    self.line_of("error-step"),
                    f"error-step {error_step} is not a step of ### Shown Work",
                )
            if "Reasons" not in named:
                self.error(block.line, "find-error card has no ### Reasons")
            else:
                reasons = self.checklist(named["Reasons"], "Reasons")
                right = sum(r.correct for r in reasons)
                if reasons and right != 1:
                    self.error(
                        named["Reasons"].line, f"### Reasons must mark exactly one [x], not {right}"
                    )
                elif reasons and not 3 <= len(reasons) <= 4:
                    self.warn(
                        named["Reasons"].line,
                        f"### Reasons should list three or four reasons, not {len(reasons)}",
                    )
            if answer_type in {"self", "choice"}:
                self.error(
                    self.line_of("answer-type"),
                    "find-error cards need an answer: the corrected value",
                )
        if kind == "method" and answer_type != "choice":
            self.error(self.line_of("answer-type"), "method cards need answer-type: choice")
        if kind in {"flashcard", "cloze", "example"} and (answer is not None or parts):
            self.error(self.line_of("answer"), f"{kind} cards are not graded: remove the answer")
        if "Rubric" in named and answer_type != "self":
            self.error(named["Rubric"].line, "### Rubric is for self-graded cards")
        rubric = (
            tuple(c.text_md for c in self.checklist(named["Rubric"], "Rubric"))
            if "Rubric" in named
            else ()
        )
        cued = self.markdown(named.get("Cued Question"))
        hints = self.hints(named.get("Hints"))
        answer_md = self.markdown(named.get("Answer"))
        extra = self.markdown(named.get("Extra"))
        notes = named["Notes"].text() if "Notes" in named else None

        step_numbers = {s.number for s in solution}
        for owner, items, line in [("", wrong, self.line_of("wrong"))] + [
            (f"### Part {p.label}: ", p.wrong, self.lines.get(f"part {p.label}", block.line))
            for p in parts
        ]:
            for w in items:
                if w.step is not None and w.step not in step_numbers:
                    target = (
                        "a step-tagged ### Solution"
                        if not solution
                        else f"step {w.step} in ### Solution"
                    )
                    self.error(
                        line,
                        f"{owner}wrong answer {w.answer!r} points at @{w.step}, "
                        f"but there is no {target}",
                    )
        if plot is not None and "[[" not in plot:  # a template's plot is checked per instance
            self.check_plot(plot, self.line_of("plot"))
        self.check_step_tags(kind, skill, uses, solution, parts)

        if any(p.is_error for p in self.problems):
            return Built(
                None, self.problems, block.line, self.lines, explicit, self.media, self.images
            )
        try:
            card = Card(
                id=block.id,
                kind=kind,  # type: ignore[arg-type]
                skill_id=skill,
                uses=uses,
                tier=tier,
                time_minutes=time_minutes,
                answer_type=answer_type,  # type: ignore[arg-type]
                answer=answer,
                checker=self.checker(self.keys),
                wrong=wrong,
                plot=plot,
                calculator=self.yes_no("calculator"),
                angles=self.choose("angles", ("radians", "degrees"), "radians"),  # type: ignore[arg-type]
                cue_required=cue == "required",
                error_step=error_step,
                tagged=self.get("tagged"),
                deck=deck,
                section_id=deck,
                tags=tags,
                question_md=question,
                cued_question_md=cued,
                choices=choices,
                shown_work=shown,
                reasons=reasons,
                parts=parts,
                hints=hints,
                answer_md=answer_md,
                solution=solution,
                solution_md=solution_md,
                rubric=rubric,
                alternative_solution=alt,
                alternative_solution_md=alt_md,
                front_md=front,
                back_md=back,
                text_md=text_md,
                extra_md=extra,
                notes_md=notes,
                provenance=Provenance(
                    source=self.get("source"),
                    source_url=self.get("source-url"),
                    license=self.get("license"),
                    modified=self.yes_no("modified"),
                ),
                verified=self.get("verified"),
            )
        except ShapeError as exc:
            self.error(block.line, str(exc))
            return Built(
                None, self.problems, block.line, self.lines, explicit, self.media, self.images
            )
        if any(p.is_error for p in self.problems):  # yes_no / choose above may have added some
            return Built(
                None, self.problems, block.line, self.lines, explicit, self.media, self.images
            )
        return Built(card, self.problems, block.line, self.lines, explicit, self.media, self.images,
                     self.claims)  # fmt: skip

    def check_cloze(self, value: str, line: int) -> None:
        numbers: set[int] = set()
        pos = 0
        for opening in _CLOZE_OPEN.finditer(value):
            if opening.start() < pos:
                continue
            m = _CLOZE.match(value, opening.start())
            at = line + value.count("\n", 0, opening.start())
            if m is None or "{{c" in m.group(2):
                self.error(at, "a cloze blank must look like {{c1::text}} or {{c1::text::hint}}")
                return
            if int(m.group(1)) < 1:
                self.error(at, "cloze blanks are numbered from c1")
            numbers.add(int(m.group(1)))
            pos = m.end()
        if not numbers:
            self.error(line, "### Text has no {{c1::...}} blank")

    def check_plot(self, plot: str, line: int) -> None:
        for item in plot.split(";"):
            expr, comma, rng = item.rpartition(",")
            m = re.fullmatch(r"\s*([A-Za-z])\s*=\s*(.+?)\s*\.\.\s*(.+?)\s*", rng) if comma else None
            if m is None or not expr.strip():
                self.error(line, f"plot: expected 'f(x), x = a..b', got {item.strip()!r}")
                continue
            try:
                parse_math(expr, Vocabulary(frozenset({m.group(1)})))
                for end in (m.group(2), m.group(3)):
                    parse_math(end, Vocabulary())
            except InputError as exc:
                self.error(line, f"plot {item.strip()!r}: {exc.message}")

    def check_step_tags(
        self,
        kind: str,
        skill: str | None,
        uses: tuple[str, ...],
        steps: tuple[SolutionStep, ...],
        parts: tuple[CardPart, ...],
    ) -> None:
        """The component rule: a problem's components are its skill, its uses and the tags
        of its ### Solution steps, so the three must agree. Every step tag is the card's
        skill, a part's skill or in uses; every uses entry, and every part's own skill, is
        the tag of at least one step. A multi-part problem has one solution for all its
        parts, so the rule holds for the card as a whole and a part's skill counts as
        declared, like the card's. Errors for problems in content packs, warnings elsewhere
        (personal decks, and the other kinds in packs)."""
        if not steps or skill is None:
            return
        report = self.error if self.ctx.pack and kind == "problem" else self.warn
        tags = {s.skill_id for s in steps if s.skill_id}
        known = {skill, *uses, *(p.skill_id for p in parts if p.skill_id)}
        missing = sorted(tags - known)
        if missing:
            report(self.line_of("uses") if uses else self.line_of("skill"),
                   f"step tags not in skill or uses: {', '.join(missing)}")  # fmt: skip
        idle = [u for u in uses if u not in tags]
        if idle:
            report(self.line_of("uses"), f"uses: no solution step is tagged {', '.join(idle)}")
        for p in parts:
            if p.skill_id in tags or p.skill_id in {None, skill, *uses}:
                continue  # tagged, the card's own, or already reported with uses
            report(self.part_skill_lines.get(p.label, self.block.line),
                   f"### Part {p.label}: no solution step is tagged {p.skill_id}")  # fmt: skip


def build_card(block: t.BlockSrc, header: Mapping[str, t.KeyLine], ctx: BuildContext) -> Built:
    return _Builder(block, header, ctx).build()


def math_delimiter_problem(value: str) -> tuple[int, str] | None:
    r"""Pairs of \( \) and \[ \], nothing nested, braces balanced inside. (offset, message)."""
    pos = 0
    while True:
        m = re.search(r"\\[\(\)\[\]]", value[pos:])
        if m is None:
            return None
        start = pos + m.start()
        token = m.group()
        if token in {"\\)", "\\]"}:
            return start, f"{token} without a matching opening delimiter"
        close = {"\\(": "\\)", "\\[": "\\]"}[token]
        end = value.find(close, start + 2)
        inner_open = re.search(r"\\[\(\[]", value[start + 2 : end if end >= 0 else len(value)])
        if end < 0 or inner_open is not None:
            return start, f"{token} is never closed with {close}"
        math = value[start + 2 : end]
        depth = 0
        stripped = math.replace("\\\\", "  ").replace("\\{", "  ").replace("\\}", "  ")
        for ch in stripped:
            depth += (ch == "{") - (ch == "}")
            if depth < 0:
                break
        if depth != 0:
            return start, f"unbalanced braces in math {math.strip()[:40]!r}"
        pos = end + 2
