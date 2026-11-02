"""The card's answer fields (AnswerSpec) and their parsed, checked form (Card).

`AnswerSpec` mirrors the key lines of docs/card-format.md. `resolve()` turns it into a
`Card`: the key and known wrong answers parsed and shape-checked, options validated.
A broken card raises SpecError (an authoring error, never the student's fault).
"""

import functools
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

from core.grader import errors
from core.grader import nodes as n
from core.grader.parser import parse
from core.grader.shapes import Value, shape_value
from core.grader.tokens import Vocabulary, is_variable_name

type AnswerType = Literal[
    "number",
    "expression",
    "equation",
    "antiderivative",
    "set",
    "list",
    "interval",
    "point",
    "vector",
    "matrix",
    "choice",
    "truefalse",
    "text",
    "quantity",
    "self",
]
ANSWER_TYPES: tuple[str, ...] = AnswerType.__value__.__args__
MATH_TYPES = frozenset(ANSWER_TYPES) - {"choice", "truefalse", "text", "quantity", "self"}
ASSUMPTIONS = frozenset(
    {"real", "positive", "negative", "nonnegative", "nonpositive", "integer", "complex"}
)
INTEGRATION_CONSTANTS = ("C", "K", "c", "k")
FORMS = frozenset({"factored", "expanded", "simplified", "lowest-terms", "exact"})
# Typed decimals when the card asks for no rounding (ADR-0019 item 11, card format 1.1): 1%
# relative (PrairieLearn's documented rtol default) with an absolute floor, so that a key of
# 0 still has a tolerance. The floor is provisional (DEV-16): PrairieLearn's atol is 1e-8,
# but that would accept 1.1e-10 for a key of 1e-10, so it is set where 1% of 1e-10 lands.
# A requested rounding (form: decimal(n), sig-figs: n) gives half a unit in the last place.
DEFAULT_RELATIVE_TOLERANCE = Fraction(1, 100)
DEFAULT_ABSOLUTE_FLOOR = Fraction(1, 10**12)


@dataclass(frozen=True, slots=True)
class WrongAnswer:
    """One entry of the card's `wrong` line: `answer => feedback @step`."""

    answer: str
    feedback: str | None = None
    step: int | None = None


@dataclass(frozen=True, slots=True)
class Choice:
    """One option of a `### Choices` list (`- [x] right`, `- [ ] wrong`)."""

    text: str
    correct: bool


@dataclass(frozen=True, slots=True)
class AnswerSpec:
    """The answer-checking fields of a card (or of one part of a multi-part card).

    Field names follow the card's key lines: `answer-type` -> answer_type,
    `require-constant` -> require_constant, `sig-figs` -> sig_figs. `vars` holds the
    checker's variables, each optionally with an assumption (`x`, `n integer`,
    `z complex`); `i imaginary` makes `i` the imaginary unit. Template parameter
    definitions such as `k = int(1, 9)` are not checker variables and are ignored.
    """

    answer_type: str
    answer: str = ""
    wrong: tuple[WrongAnswer, ...] = ()
    vars: tuple[str, ...] = ()
    domain: str | None = None
    tolerance: str | None = None
    exact: bool = False
    form: str | None = None
    endpoints: str | None = None
    require_constant: bool = False
    domain_strict: bool = False  # format 1.1: holes are wrong, not a "check its form" note
    units: str | None = None
    sig_figs: int | None = None
    angles: str = "radians"
    choices: tuple[Choice, ...] = ()

    @classmethod
    def from_fields(cls, fields: Mapping[str, str], choices: tuple[Choice, ...] = ()) -> AnswerSpec:
        """Build a spec from a card's raw `key: value` lines (values taken literally)."""

        def get(key: str) -> str | None:
            value = fields.get(key)
            return value.strip() if value is not None and value.strip() else None

        def yes(key: str) -> bool:
            value = get(key)
            if value is None:
                return False
            if value.lower() not in {"yes", "no"}:
                raise errors.SpecError(f"{key}: expected yes or no, got {value!r}")
            return value.lower() == "yes"

        sig_figs = get("sig-figs")
        return cls(
            answer_type=get("answer-type") or "self",
            answer=get("answer") or "",
            wrong=parse_wrong_field(get("wrong") or ""),
            vars=split_vars(get("vars") or ""),
            domain=get("domain"),
            tolerance=get("tolerance"),
            exact=yes("exact"),
            form=get("form"),
            endpoints=get("endpoints"),
            require_constant=yes("require-constant"),
            domain_strict=yes("domain-strict"),
            units=get("units"),
            sig_figs=int(sig_figs) if sig_figs and sig_figs.isdigit() else None,
            angles=(get("angles") or "radians").lower(),
            choices=choices,
        )


def split_vars(text: str) -> tuple[str, ...]:
    """`x, t` -> ("x", "t"). Template parameters (`k = int(1, 9); m = choice(2, 3)`,
    separated by `;`) are not checker variables and are dropped."""
    out: list[str] = []
    for part in text.split(";"):
        if "=" in part:
            continue
        out += [v.strip() for v in part.split(",") if v.strip()]
    return tuple(out)


def parse_wrong_field(text: str) -> tuple[WrongAnswer, ...]:
    """Split a `wrong:` line: `answer => feedback @step; ...` (feedback has no `;`)."""
    out: list[WrongAnswer] = []
    for entry in text.split(";"):
        if not entry.strip():
            continue
        answer, arrow, rest = entry.partition("=>")
        feedback: str | None = None
        step: int | None = None
        if arrow:
            m = re.search(r"@\s*(\d+)\s*$", rest)
            if m:
                step = int(m.group(1))
                rest = rest[: m.start()]
            feedback = rest.strip() or None
        else:
            m = re.search(r"@\s*(\d+)\s*$", answer)
            if m:
                step = int(m.group(1))
                answer = answer[: m.start()]
        out.append(WrongAnswer(answer.strip(), feedback, step))
    return tuple(out)


type Form = tuple[str, int]  # ("factored", 0) ... ("decimal", places)


@dataclass(frozen=True, slots=True)
class Tolerance:
    kind: Literal["relative", "absolute", "sig-figs"]
    value: Fraction  # sig-figs: the number of significant figures
    explicit: bool  # set by the card (tolerance, or a requested rounding)
    floor: Fraction = Fraction(0)  # relative: never less than this, absolutely


@dataclass(frozen=True, slots=True)
class Card:
    """A resolved spec: everything the checker needs, parsed and validated (picklable)."""

    answer_type: str
    keys: tuple[Value, ...]  # `;`-separated alternatives
    key_texts: tuple[str, ...]
    wrong: tuple[tuple[WrongAnswer, Value | None], ...]
    variables: tuple[tuple[str, str], ...]  # (name, assumption)
    constants: tuple[str, ...]  # integration constants allowed in antiderivatives
    vocab: Vocabulary  # how the student's answer is read
    domain: tuple[n.Node, ...]  # conditions, all must hold
    tolerance: Tolerance
    exact: bool
    form: Form | None
    endpoints_either: bool
    require_constant: bool
    degrees: bool
    imaginary: bool
    domain_strict: bool = False  # the card's domain is strict: an answer with a hole is wrong
    choices: tuple[Choice, ...] = ()
    texts: tuple[str, ...] = field(default=())  # text / truefalse keys, normalized


def _parse_vars(entries: tuple[str, ...]) -> tuple[list[tuple[str, str]], bool]:
    out: list[tuple[str, str]] = []
    imaginary = False
    for raw in entries:
        entry = raw.strip()
        if not entry or "=" in entry or "(" in entry:
            continue  # template parameters (`k = int(1, 9)`) are not checker variables
        parts = entry.split()
        name, assumption = parts[0], (parts[1].lower() if len(parts) > 1 else "real")
        if len(parts) > 2:
            raise errors.SpecError(f"vars: can't read {entry!r}")
        if name == "i" and assumption == "imaginary":
            imaginary = True
            continue
        if not is_variable_name(name) or name in {"e", "U"}:
            raise errors.SpecError(f"vars: {name!r} can't be a variable name")
        if assumption not in ASSUMPTIONS:
            raise errors.SpecError(f"vars: unknown assumption {assumption!r} for {name}")
        out.append((name, assumption))
    return out, imaginary


def _parse_tolerance(text: str | None, sig_figs: int | None = None) -> Tolerance:
    if text is None:
        if sig_figs:  # half a unit in the last requested significant figure
            return Tolerance("sig-figs", Fraction(sig_figs), explicit=True)
        return Tolerance(
            "relative", DEFAULT_RELATIVE_TOLERANCE, explicit=False, floor=DEFAULT_ABSOLUTE_FLOOR
        )
    m = re.fullmatch(r"\s*((?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d{1,3})?)\s*(%?)\s*", text)
    if not m:
        raise errors.SpecError(f"tolerance: expected a number or a percentage, got {text!r}")
    value = Fraction(m.group(1))
    if m.group(2):
        return Tolerance("relative", value / 100, explicit=True)
    return Tolerance("absolute", value, explicit=True)


def _parse_form(text: str | None, exact: bool) -> Form | None:
    if text is None:
        return ("exact", 0) if exact else None
    value = text.strip().lower()
    m = re.fullmatch(r"decimal\((\d+)\)", value)
    if m:
        if exact:
            raise errors.SpecError("exact: yes contradicts form: decimal(n)")
        return ("decimal", int(m.group(1)))
    if value not in FORMS:
        raise errors.SpecError(f"form: unknown form {text!r}")
    return (value, 0)


def _key_vocab(imaginary: bool) -> Vocabulary:
    return Vocabulary(open_vars=True, imaginary=imaginary)


def _discover(texts: list[str], imaginary: bool) -> list[str]:
    names: set[str] = set()
    for text in texts:
        try:
            parsed = parse(text, _key_vocab(imaginary))
        except errors.InputError:
            continue  # reported when the key itself is parsed below
        for alt in parsed.alternatives:
            for item in alt:
                names |= n.free_vars(item)
    return sorted(names)


@functools.lru_cache(maxsize=256)
def resolve(spec: AnswerSpec) -> Card:
    """Parse and validate a spec. Raises SpecError if the card is broken."""
    kind = spec.answer_type
    if kind not in ANSWER_TYPES:
        raise errors.SpecError(f"answer-type: unknown type {kind!r}")
    declared, imaginary = _parse_vars(spec.vars)
    if spec.angles not in {"radians", "degrees"}:
        raise errors.SpecError(f"angles: expected radians or degrees, got {spec.angles!r}")
    if spec.endpoints not in {None, "either", "exact"}:
        raise errors.SpecError(f"endpoints: expected either, got {spec.endpoints!r}")
    tolerance = _parse_tolerance(spec.tolerance, spec.sig_figs)
    form = _parse_form(spec.form, spec.exact)
    common = {
        "tolerance": tolerance,
        "exact": spec.exact,
        "form": form,
        "endpoints_either": spec.endpoints == "either",
        "require_constant": spec.require_constant,
        "domain_strict": spec.domain_strict,
        "degrees": spec.angles == "degrees",
        "imaginary": imaginary,
    }
    if kind in {"choice", "truefalse", "text", "quantity", "self"}:
        return _resolve_plain(spec, common)

    key_texts = tuple(t.strip() for t in spec.answer.split(";") if t.strip())
    if not key_texts:
        raise errors.SpecError("answer: missing")
    constants: tuple[str, ...] = ()
    if declared:
        variables = declared
    else:
        found = _discover(list(key_texts), imaginary)
        variables = [(name, "real") for name in found]
    names = {name for name, _ in variables}
    if kind == "antiderivative":
        constants = tuple(c for c in INTEGRATION_CONSTANTS if c not in names or not declared)
        variables = [(v, a) for v, a in variables if v not in constants]
        names = {name for name, _ in variables}
    # Interval and inequality answers use the declared variable only (MATH-9): an interval
    # card with no `vars` (and no variable in its key) takes interval notation only.
    vocab = Vocabulary(frozenset(names | set(constants)), imaginary=imaginary)
    keys: list[Value] = []
    for text in key_texts:
        try:
            parsed = parse(text, vocab)
            keys.append(shape_value(parsed, kind, names, constants))
        except errors.InputError as exc:
            raise errors.SpecError(f"answer {text!r}: {exc.message}") from None
    domain = _parse_domain(spec.domain, vocab)
    wrong: list[tuple[WrongAnswer, Value | None]] = []
    for w in spec.wrong:
        try:
            wrong.append((w, shape_value(parse(w.answer, vocab), kind, names, constants)))
        except errors.InputError:
            wrong.append((w, None))  # check_key reports it; grading skips it
    return Card(
        answer_type=kind,
        keys=tuple(keys),
        key_texts=key_texts,
        wrong=tuple(wrong),
        variables=tuple(variables),
        constants=constants,
        vocab=vocab,
        domain=domain,
        **common,  # type: ignore[arg-type]
    )


def _resolve_plain(spec: AnswerSpec, common: dict[str, object]) -> Card:
    from core.grader.plain import normalize_text, parse_bool

    kind = spec.answer_type
    texts: tuple[str, ...] = ()
    if kind == "text":
        texts = tuple(normalize_text(t) for t in spec.answer.split(";") if t.strip())
        if not texts:
            raise errors.SpecError("answer: missing")
    elif kind == "truefalse":
        value = parse_bool(spec.answer)
        if value is None:
            raise errors.SpecError(f"answer: expected true or false, got {spec.answer!r}")
        texts = ("true" if value else "false",)
    elif kind == "choice":
        if not spec.choices:
            raise errors.SpecError("choice cards need a ### Choices list")
        if not any(c.correct for c in spec.choices):
            raise errors.SpecError("### Choices: no option is marked [x]")
    return Card(
        answer_type=kind,
        keys=(),
        key_texts=texts if kind == "text" else (spec.answer,),
        wrong=tuple((w, None) for w in spec.wrong),
        variables=(),
        constants=(),
        vocab=Vocabulary(),
        domain=(),
        choices=spec.choices,
        texts=texts,
        **common,  # type: ignore[arg-type]
    )


def _parse_domain(text: str | None, vocab: Vocabulary) -> tuple[n.Node, ...]:
    if text is None:
        return ()
    try:
        parsed = parse(text, vocab)
    except errors.InputError as exc:
        raise errors.SpecError(f"domain {text!r}: {exc.message}") from None
    if len(parsed.alternatives) != 1:
        raise errors.SpecError(f"domain {text!r}: use commas or 'and', not ';'")
    conditions = parsed.alternatives[0]
    for cond in conditions:
        if not _is_condition(cond):
            raise errors.SpecError(f"domain {text!r}: expected inequalities such as x > 0")
    return conditions


def _is_condition(node: n.Node) -> bool:
    match node:
        case n.Chain(_, ops):
            return all(op != "=" for op in ops)
        case n.Or(items) | n.And(items):
            return all(_is_condition(i) for i in items)
        case _:
            return False
