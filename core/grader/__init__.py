"""The answer checker (milestone M3): decides whether a typed answer is right.

It must never accept a wrong answer and must almost never reject a right one
(docs/spec.md, "Math system"). Nothing the student types is evaluated as code: text
goes through our tokenizer and Lark grammar into our own tree, then a whitelist
translator builds SymPy objects (ADR-0003). MathLive input arrives as LaTeX and is
lowered to the same plain syntax first (ADR-0005).

Public API
----------
``AnswerSpec``
    The card's answer fields (``answer-type``, ``answer``, ``wrong``, checker options).
    ``AnswerSpec.from_fields(key_lines)`` builds one from raw card key lines.
``grade(raw, spec, source="text" | "mathlive") -> GradeResult``
    Status, the "read as" LaTeX, a message, the matched known-wrong answer, timings.
    ``INVALID`` (syntax or shape error) and ``UNSUPPORTED`` never count as attempts.
    An answer equal to the key except at removable points (ADR-0019 item 10) is
    ``INVALID`` with category ``"hole-only"``: no attempt, and logged on its own.
``preview(raw, spec, source) -> Preview``
    The live "We read your answer as ..." line with hints (``sinx``, ``e^2x``, ``1/2x``).
``check_key(spec) -> KeyCheck``
    MATH-13: every key grades itself correct, every ``wrong`` answer grades incorrect.
``cross_check(raw, spec, source) -> tuple[str, ...]``
    DEV-18: SymPy and our mpmath evaluator, side by side, on this answer, its key and its
    verdict (core/grader/differential.py). Empty when they agree.
``to_answer_syntax(sympy_object) -> str``
    Writes a SymPy object in answer syntax that parses back to an equal object.
``warm_up()`` / ``shutdown()``
    Start the checker's worker process early (at app launch) / stop it.

Pipeline (parsing and shape here; the rest in a reusable worker process that is killed
after 2 s, which makes the verdict UNDECIDABLE): shape -> exact canonical match ->
numeric sampling (mpmath, 30 digits, mismatches rechecked at 60/120/240, 12 points per
variable, one per connected piece of the domain, plus points in every region cut out by
abs()/domain/divisor critical points; undefined where the key is defined is wrong, except
at removable points: a hole-only answer is not wrong, ADR-0019 item 10) -> form -> symbolic
confirmation. Form runs
before the symbolic step so that a kill during the (slow) symbolic step still leaves a
complete verdict. Symbolic work can confirm a match or prove an exact nonzero difference;
it never overrules a numeric mismatch.

The app process never imports SymPy or mpmath; `multiprocessing` uses "spawn", so the
frozen app's entry point must call `multiprocessing.freeze_support()`.
"""

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from core.grader import errors
from core.grader import nodes as n
from core.grader.latex_in import lower
from core.grader.latex_out import parsed_latex, reading_notes
from core.grader.parser import parse
from core.grader.pipeline import Job
from core.grader.plain import normalize_text, parse_bool, parse_choice
from core.grader.serialize import to_answer_syntax
from core.grader.shapes import shape_value
from core.grader.spec import (
    MATH_TYPES,
    AnswerSpec,
    Card,
    Choice,
    WrongAnswer,
    parse_wrong_field,
    resolve,
)
from core.grader.tokens import MAX_CHARS, Vocabulary
from core.grader.worker import HARD_LIMIT_SECONDS
from core.grader.worker import worker as _worker

__all__ = [
    "HOLE_ONLY",
    "AnswerSpec",
    "Choice",
    "GradeResult",
    "KeyCheck",
    "Preview",
    "Source",
    "Status",
    "WrongAnswer",
    "check_key",
    "cross_check",
    "grade",
    "parse_wrong_field",
    "preview",
    "shutdown",
    "to_answer_syntax",
    "warm_up",
]

type Source = Literal["text", "mathlive"]

log = logging.getLogger("core.grader")
HOLE_ONLY = "hole-only"  # GradeResult.category of an answer that differs only at holes


class Status(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNDECIDABLE = "undecidable"  # self-grade and log for review
    INVALID = "invalid"  # syntax or shape error: show inline, not an attempt
    UNSUPPORTED = "unsupported"  # quantity (1.1) or self-graded: the importer rejects these


@dataclass(frozen=True, slots=True)
class GradeResult:
    status: Status
    read_as_latex: str | None = None
    message: str = ""
    matched_wrong: WrongAnswer | None = None
    timings: Mapping[str, float] = field(default_factory=dict)
    hints: tuple[str, ...] = ()
    category: str = ""  # why it is not an attempt, when that is its own category (HOLE_ONLY)

    @property
    def counts_as_attempt(self) -> bool:
        return self.status in {Status.CORRECT, Status.INCORRECT}


@dataclass(frozen=True, slots=True)
class Preview:
    ok: bool
    read_as_latex: str | None = None
    message: str = ""
    hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KeyCheck:
    ok: bool
    problems: tuple[str, ...] = ()


_PLAIN_TYPES = {"choice", "truefalse", "text"}


def _read(raw: str, card: Card, source: Source) -> n.Parsed:
    if source == "mathlive":
        return parse(lower(raw), card.vocab, max_chars=2 * MAX_CHARS)
    if source != "text":
        raise ValueError(f"unknown source {source!r}")
    return parse(raw, card.vocab)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def preview(raw: str, spec: AnswerSpec, source: Source = "text") -> Preview:
    """How the answer will be read, before submitting (MATH-6). Never touches SymPy."""
    try:
        card = resolve(spec)
    except errors.SpecError as exc:
        return Preview(False, message=f"Card problem: {exc}")
    if card.answer_type not in MATH_TYPES:
        return Preview(bool(raw.strip()))
    try:
        parsed = _read(raw, card, source)
    except errors.InputError as exc:
        return Preview(False, message=exc.message, hints=exc.hints)
    latex = parsed_latex(parsed)
    notes = reading_notes(parsed) if source == "text" else ()
    try:
        shape_value(parsed, card.answer_type, [v for v, _ in card.variables], card.constants)
    except errors.InputError as exc:
        return Preview(False, latex, exc.message, exc.hints + notes)
    return Preview(True, latex, hints=notes)


def grade(raw: str, spec: AnswerSpec, source: Source = "text") -> GradeResult:
    """Grade one answer. Thread-safe; blocks at most about 2 s (then UNDECIDABLE)."""
    t0 = time.perf_counter()
    try:
        card = resolve(spec)
    except errors.SpecError as exc:
        return GradeResult(Status.UNDECIDABLE, message=f"Card problem: {exc}")
    kind = card.answer_type
    if kind == "quantity":
        # Parsed (units as one-letter symbols) so the reading can be shown, never graded.
        try:
            latex: str | None = parsed_latex(parse(raw, Vocabulary(open_vars=True)))
        except errors.InputError:
            latex = None
        message = "quantity answers (numbers with units) arrive in version 1.1."
        return GradeResult(Status.UNSUPPORTED, latex, message)
    if kind == "self":
        return GradeResult(Status.UNSUPPORTED, message="This card is self-graded.")
    if kind in _PLAIN_TYPES:
        return _grade_plain(raw, card, t0)
    try:
        parsed = _read(raw, card, source)
    except errors.InputError as exc:
        return GradeResult(Status.INVALID, None, exc.message, timings={"parse": _ms(t0)},
                           hints=exc.hints)  # fmt: skip
    latex = parsed_latex(parsed)
    notes = reading_notes(parsed) if source == "text" else ()
    try:
        value = shape_value(parsed, kind, [v for v, _ in card.variables], card.constants)
    except errors.InputError as exc:
        return GradeResult(Status.INVALID, latex, exc.message, timings={"parse": _ms(t0)},
                           hints=exc.hints + notes)  # fmt: skip
    parse_ms = _ms(t0)
    t1 = time.perf_counter()
    result, timed_out = _worker().run(Job(card, value), hard_limit=HARD_LIMIT_SECONDS)
    timings: dict[str, float] = {"parse": parse_ms, "worker": _ms(t1)}
    if result is None:
        message = "The checker took too long." if timed_out else "The checker failed."
        timings["total"] = _ms(t0)
        return GradeResult(Status.UNDECIDABLE, latex, message, timings=timings, hints=notes)
    timings.update(result.timings)
    timings["total"] = _ms(t0)
    if result.status == "hole":
        # Not wrong and not an attempt (ADR-0019 item 10): the existing invalid-input path,
        # so callers need no change, with its own category for the logs.
        log.info("hole-only answer", extra={"category": HOLE_ONLY, "detail": result.message})
        return GradeResult(Status.INVALID, latex, result.message, None, timings, notes,
                           category=HOLE_ONLY)  # fmt: skip
    matched = card.wrong[result.matched_wrong][0] if result.matched_wrong is not None else None
    message = result.message
    if matched is not None and matched.feedback:
        message = matched.feedback
    return GradeResult(Status(result.status), latex, message, matched, timings, notes)


def _grade_plain(raw: str, card: Card, t0: float) -> GradeResult:
    kind = card.answer_type
    if not raw.strip():
        return GradeResult(Status.INVALID, message="Type an answer.")
    verdict: bool
    if kind == "truefalse":
        value = parse_bool(raw)
        if value is None:
            return GradeResult(Status.INVALID, message="Answer true or false.")
        verdict = ("true" if value else "false") == card.texts[0]
    elif kind == "choice":
        picked = parse_choice(raw, len(card.choices))
        if picked is None:
            return GradeResult(Status.INVALID, message="Pick one or more of the options.")
        verdict = picked == frozenset(i for i, c in enumerate(card.choices) if c.correct)
    else:
        verdict = normalize_text(raw) in card.texts
    matched = None
    if not verdict:
        for w, _ in card.wrong:
            if normalize_text(w.answer) == normalize_text(raw):
                matched = w
                break
    status = Status.CORRECT if verdict else Status.INCORRECT
    message = matched.feedback or "" if matched is not None else ""
    return GradeResult(status, None, message, matched, {"total": _ms(t0)})


def check_key(spec: AnswerSpec) -> KeyCheck:
    """MATH-13: the key grades itself correct and every `wrong` answer grades incorrect."""
    try:
        card = resolve(spec)
    except errors.SpecError as exc:
        return KeyCheck(False, (str(exc),))
    if card.answer_type == "quantity":
        return KeyCheck(False, ("answer-type quantity is not supported until version 1.1",))
    if card.answer_type == "self":
        return KeyCheck(True)
    problems: list[str] = []
    for text, key in zip(card.key_texts, card.keys, strict=False):
        checked, _ = _worker().run(Job(card, key, mode="key"))
        if checked is None:
            problems.append(f"key {text!r} took too long to check")
        elif checked.status != "correct":
            problems.append(f"key {text!r}: {checked.message}")
    keys: list[str] = list(card.key_texts)
    if card.answer_type == "choice":
        keys = [", ".join(str(i + 1) for i, c in enumerate(card.choices) if c.correct)]
    for text in keys:
        result = grade(text, spec)
        if result.status != Status.CORRECT:
            why = f": {result.message}" if result.message else ""
            problems.append(f"key {text!r} grades {result.status.value}{why}")
    for w, wrong_value in card.wrong:
        if card.answer_type in MATH_TYPES and wrong_value is None:
            try:
                _read(w.answer, card, "text")
                problems.append(f"wrong answer {w.answer!r} has the wrong shape")
            except errors.InputError as exc:
                problems.append(f"wrong answer {w.answer!r} can't be read: {exc.message}")
            continue
        result = grade(w.answer, spec)
        if result.status != Status.INCORRECT:
            problems.append(f"wrong answer {w.answer!r} grades {result.status.value}")
    return KeyCheck(not problems, tuple(problems))


def cross_check(raw: str, spec: AnswerSpec, source: Source = "text") -> tuple[str, ...]:
    """DEV-18: disagreements between SymPy and mpmath on this answer, its key and its verdict.

    Number and expression cards only; a verdict that is not correct or incorrect, or a
    check that runs out of time, reports nothing.
    """
    result = grade(raw, spec, source)
    if result.status not in {Status.CORRECT, Status.INCORRECT}:
        return ()
    card = resolve(spec)
    if card.answer_type not in {"number", "expression"}:
        return ()
    value = shape_value(_read(raw, card, source), card.answer_type,
                        [v for v, _ in card.variables], card.constants)  # fmt: skip
    checked, _ = _worker().run(Job(card, value, mode="cross", status=result.status.value))
    if checked is None or checked.status == "correct":
        return ()
    return tuple(checked.message.splitlines())


def warm_up() -> None:
    """Start the worker process now (it takes about a second to import SymPy)."""
    _worker().start()


def shutdown() -> None:
    _worker().stop()
