"""Checks that need the grader: the self-check (every key grades itself correct, every
`wrong` answer grades incorrect), plus the warnings that never reject a card."""

import difflib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from core.grader import AnswerSpec, Choice, check_key
from core.grader.errors import SpecError
from core.model import Card, CardPart, CheckerOptions, WrongAnswer

AUTO_TYPES = frozenset(
    {"number", "expression", "equation", "antiderivative", "set", "list", "interval", "point",
     "vector", "matrix", "choice", "truefalse", "text", "quantity"}
)  # fmt: skip
NEAR_DUPLICATE = 0.92
MAX_PAIRWISE = 1500
MIN_NEAR_LENGTH = 40  # shorter texts are only compared for exact duplicates
_DOLLAR_MATH = re.compile(r"(?<![\\$\w])\$(?=[^\s\d$])[^$\n]*?[^\s\\$]\$(?!\d)")


def format_wrong(items: Iterable[WrongAnswer]) -> str:
    """WrongAnswer records back to the `wrong:` line (`answer => feedback @step; ...`)."""
    out: list[str] = []
    for w in items:
        text = w.answer
        if w.feedback:
            text += f" => {w.feedback}"
        if w.step is not None:
            text += f" @{w.step}"
        out.append(text)
    return "; ".join(out)


def checker_fields(checker: CheckerOptions) -> dict[str, str]:
    values = {
        "vars": checker.vars,
        "domain": checker.domain,
        "tolerance": checker.tolerance,
        "exact": checker.exact,
        "form": checker.form,
        "endpoints": checker.endpoints,
        "require-constant": checker.require_constant,
        "units": checker.units,
        "sig-figs": checker.sig_figs,
        "domain-strict": checker.domain_strict,
    }
    return {k: v for k, v in values.items() if v is not None}


def answer_spec(card: Card, part: CardPart | None = None) -> AnswerSpec:
    """The grader's AnswerSpec for a card or one of its parts, built from the stored key
    lines exactly as the grader reads them (AnswerSpec.from_fields). Raises SpecError."""
    source = part if part is not None else card
    fields = checker_fields(source.checker)
    fields["answer-type"] = source.answer_type
    if source.answer is not None:
        fields["answer"] = source.answer
    if source.wrong:
        fields["wrong"] = format_wrong(source.wrong)
    fields["angles"] = card.angles
    choices = tuple(Choice(c.text_md, c.correct) for c in source.choices)
    return AnswerSpec.from_fields(fields, choices)


@dataclass(frozen=True, slots=True)
class KeyProblem:
    where: str  # "answer" or "part a"
    message: str


def self_check(card: Card) -> list[KeyProblem]:
    """MATH-13 for every auto-checked answer of the card (the card itself and its parts)."""
    targets: list[tuple[str, CardPart | None, str]] = []
    if card.answer_type in AUTO_TYPES:
        targets.append(("answer", None, card.answer_type))
    for p in card.parts:
        if p.answer_type in AUTO_TYPES:
            targets.append((f"part {p.label}", p, p.answer_type))
    out: list[KeyProblem] = []
    for where, part, _ in targets:
        label = "" if part is None else f"### Part {part.label}: "
        try:
            spec = answer_spec(card, part)
        except SpecError as exc:
            out.append(KeyProblem(where, f"{label}{exc}"))
            continue
        result = check_key(spec)
        for message in result.problems:
            out.append(KeyProblem(where, f"{label}{message}"))
    return out


# ---------------------------------------------------------------- warnings


def labeled_texts(card: Card) -> list[tuple[str, str]]:
    """Every piece of Markdown the student can see, with where it sits on the card."""
    out: list[tuple[str, str | None]] = [
        ("question", card.question_md),
        ("cued question", card.cued_question_md),
        ("answer", card.answer_md),
        ("solution", card.solution_md),
        ("alternative solution", card.alternative_solution_md),
        ("front", card.front_md),
        ("back", card.back_md),
        ("text", card.text_md),
        ("extra", card.extra_md),
    ]
    out += [(f"hint {i}", h) for i, h in enumerate(card.hints, start=1)]
    out += [(f"rubric {i}", r) for i, r in enumerate(card.rubric, start=1)]
    out += [(f"choice {i}", c.text_md) for i, c in enumerate(card.choices, start=1)]
    out += [(f"reason {i}", c.text_md) for i, c in enumerate(card.reasons, start=1)]
    for name, steps in (
        ("solution", card.solution),
        ("alternative solution", card.alternative_solution),
        ("shown work", card.shown_work),
    ):
        out += [(f"{name} step {s.number}", f"{s.label}: {s.body_md}") for s in steps]
    for p in card.parts:
        out.append((f"part {p.label}", p.prompt_md))
        out += [(f"part {p.label} choice {i}", c.text_md) for i, c in enumerate(p.choices, 1)]
        out += [(f"part {p.label} wrong {w.answer}", w.feedback) for w in p.wrong]
    out += [(f"wrong {w.answer}", w.feedback) for w in card.wrong]
    return [(where, text) for where, text in out if text]


def card_texts(card: Card) -> list[str]:
    return [text for _, text in labeled_texts(card)]


_MATH = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", re.DOTALL)


def math_segments(card: Card) -> list[tuple[str, str, bool]]:
    """(where, LaTeX, display) for every \\( \\) and \\[ \\] on the card (for KaTeX)."""
    out: list[tuple[str, str, bool]] = []
    for where, text in labeled_texts(card):
        for m in _MATH.finditer(text):
            display = m.group(2) is not None
            out.append((where, m.group(2) if display else m.group(1), display))
    return out


def dollar_math(card: Card) -> str | None:
    """A `$...$` that looks like math (math goes between \\( \\) instead)."""
    for text in card_texts(card):
        m = _DOLLAR_MATH.search(text)
        if m is not None:
            return m.group()
    return None


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _math_and_prose(text: str) -> tuple[tuple[str, ...], str]:
    math = tuple(re.sub(r"\s+", "", m.group()) for m in _MATH.finditer(text))
    return math, _normalized(_MATH.sub(" $ ", text))


def stem(card: Card) -> str:
    return card.question_md or card.front_md or card.text_md or ""


def near_duplicates(stems: Sequence[tuple[str, str]]) -> list[tuple[int, int, float]]:
    """Pairs (i, j, ratio) of the same or nearly the same text. Texts that differ in their
    math are different problems (a drill set shares its wording), so only texts with the
    same math are compared, by their prose. Large groups get exact matching only."""
    out: list[tuple[int, int, float]] = []
    seen: dict[str, int] = {}
    groups: dict[tuple[str, ...], list[tuple[int, str]]] = {}
    for i, (_, text) in enumerate(stems):
        exact = _normalized(text)
        if not exact:
            continue
        if exact in seen:
            out.append((seen[exact], i, 1.0))
            continue
        seen[exact] = i
        math, prose = _math_and_prose(text)
        groups.setdefault(math, []).append((i, prose))
    for members in groups.values():
        if len(members) > MAX_PAIRWISE:
            continue
        for k, (i, a) in enumerate(members):
            if len(a) < MIN_NEAR_LENGTH:
                continue
            matcher = difflib.SequenceMatcher(None, "", a, autojunk=False)  # caches seq2
            for j, b in members[k + 1 :]:
                if min(len(a), len(b)) / max(len(a), len(b)) < NEAR_DUPLICATE:
                    continue
                matcher.set_seq1(b)
                if matcher.real_quick_ratio() < NEAR_DUPLICATE:
                    continue
                if matcher.quick_ratio() < NEAR_DUPLICATE:
                    continue
                ratio = matcher.ratio()
                if ratio >= NEAR_DUPLICATE:
                    out.append((min(i, j), max(i, j), ratio))
    return sorted(out)
