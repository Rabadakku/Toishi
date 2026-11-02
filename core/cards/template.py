"""Variant templates (docs/card-format.md, "Variants"): the program, without SymPy.

A template card has parameters in `vars` (`k = int(1, 9); m = choice(2, 3)`), helpers
in `let`, conditions in `require`, an `answer` computed from them, and `[[expr]]` /
`[[tex(expr)]]` insertions in its text. This module reads all of that into plain
data (a TemplateJob) using the grader's own tokenizer and Lark grammar: template
functions (`diff`, `solve`, ...) are cut out of the text first and replaced by
placeholder variables, so every piece of math is parsed by the one answer parser.
Nothing is evaluated here; cas.py evaluates a job in the sweep process (sweep.py).
"""

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

from core.cards import text as t
from core.cards.cardfile import PART_HEADING, PART_KEYS
from core.grader import nodes as n
from core.grader.errors import InputError
from core.grader.parser import parse
from core.grader.spec import MATH_TYPES
from core.grader.tokens import RESERVED, Vocabulary, is_variable_name

MAX_INSTANCES = 200
INSTANCE_SECONDS = 2.0
MAX_EXPR_CHARS = 2000
OPS: dict[str, tuple[int, int]] = {  # name -> (min args, max args)
    "diff": (2, 3),
    "integrate": (2, 4),
    "limit": (3, 4),
    "solve": (2, 2),
    "simplify": (1, 1),
    "expand": (1, 1),
    "factor": (1, 1),
    "subs": (3, 3),
}
GENERATORS = ("int", "choice", "decimal")
LIMIT_SIDES = ("left", "right")
_CALL = re.compile(r"(?<![A-Za-z_])([A-Za-z]+)\s*\(")
_DEFINITION = re.compile(r"\s*([A-Za-z][A-Za-z0-9_]*)\s*=(?!=)\s*(.*?)\s*", re.DOTALL)
_GENERATOR = re.compile(r"([a-z]+)\s*\((.*)\)", re.DOTALL)
_INT = re.compile(r"-?\d+")
_DECIMAL = re.compile(r"-?(\d+(\.\d*)?|\.\d+)")


class TemplateError(Exception):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line


# ---------------------------------------------------------------- expressions


@dataclass(frozen=True, slots=True)
class OpCall:
    name: str
    args: tuple[Expr | str, ...]  # str only for limit's side: "left" / "right"


@dataclass(frozen=True, slots=True)
class Expr:
    """A template expression: grader AST with placeholders for template function calls."""

    text: str
    parsed: n.Parsed
    calls: tuple[tuple[str, OpCall], ...] = ()
    names: frozenset[str] = frozenset()  # every name used, inside calls too (no placeholders)

    def single(self) -> n.Node:
        if len(self.parsed.alternatives) != 1 or len(self.parsed.alternatives[0]) != 1:
            raise TemplateError(f"{self.text!r}: expected one value, not a list")
        return self.parsed.alternatives[0][0]


def _matching(text: str, start: int) -> int:
    """Index of the bracket closing the one opened just before `start`, or -1."""
    depth = 1
    for i in range(start, len(text)):
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def compile_expr(text: str, *, _depth: int = 0) -> Expr:
    """Read a template expression. Raises TemplateError with a readable message."""
    if _depth > 20:
        raise TemplateError("template functions are nested too deeply")
    if len(text) > MAX_EXPR_CHARS:
        raise TemplateError(f"expressions are limited to {MAX_EXPR_CHARS} characters")
    calls: list[tuple[str, OpCall]] = []
    names: set[str] = set()
    out: list[str] = []
    pos = 0
    while True:
        m = _CALL.search(text, pos)
        while m is not None and m.group(1) not in OPS:
            if m.group(1) in {"tex", *GENERATORS}:
                raise TemplateError(f"{m.group(1)}(...) can't be used here")
            m = _CALL.search(text, m.end())
        if m is None:
            out.append(text[pos:])
            break
        close = _matching(text, m.end())
        if close < 0:
            raise TemplateError(f"{m.group(1)}( is never closed")
        name = m.group(1)
        raw_args = [a.strip() for a in t.split_top(text[m.end() : close], ",")]
        low, high = OPS[name]
        if not low <= len(raw_args) <= high or any(not a for a in raw_args):
            counts = str(low) if low == high else f"{low} to {high}"
            raise TemplateError(f"{name} takes {counts} arguments")
        args: list[Expr | str] = []
        for i, raw in enumerate(raw_args):
            if name == "limit" and i == 3:
                if raw not in LIMIT_SIDES:
                    raise TemplateError("limit's fourth argument is left or right")
                args.append(raw)
                continue
            sub = compile_expr(raw, _depth=_depth + 1)
            names |= sub.names
            args.append(sub)
        _check_variable_args(name, args)
        placeholder = f"Z_tpl{_depth}x{len(calls)}"
        calls.append((placeholder, OpCall(name, tuple(args))))
        out.append(f"{text[pos : m.start()]} {placeholder} ")
        pos = close + 1
    rewritten = "".join(out)
    if "Z_tpl" in text:
        raise TemplateError("names starting with Z_tpl are reserved")
    try:
        parsed = parse(rewritten, Vocabulary(open_vars=True), max_chars=2 * MAX_EXPR_CHARS)
    except InputError as exc:
        raise TemplateError(f"can't read {text.strip()!r}: {exc.message}") from None
    placeholders = {p for p, _ in calls}
    for alt in parsed.alternatives:
        for item in alt:
            names |= n.free_vars(item) - placeholders
    return Expr(text.strip(), parsed, tuple(calls), frozenset(names))


def _check_variable_args(name: str, args: list[Expr | str]) -> None:
    """diff/integrate/limit/solve/subs take a bare variable as their second argument."""
    if name in {"simplify", "expand", "factor"}:
        return
    var = args[1]
    node = var.single() if isinstance(var, Expr) else None
    if not isinstance(node, n.Var):
        raise TemplateError(f"{name}: the second argument must be a variable such as x")
    if name == "diff" and len(args) == 3:
        order = args[2]
        node = order.single() if isinstance(order, Expr) else None
        if not (isinstance(node, n.Num) and node.text.isdigit() and 1 <= int(node.text) <= 10):
            raise TemplateError("diff: the order must be a whole number from 1 to 10")
    if name == "integrate" and len(args) == 3:
        raise TemplateError("integrate takes (f, x) or (f, x, a, b)")


@dataclass(frozen=True, slots=True)
class Insertion:
    start: int
    end: int
    expr: Expr
    tex: bool


def find_insertions(line: str) -> list[Insertion]:
    """`[[expr]]` and `[[tex(expr)]]` markers on one line."""
    out: list[Insertion] = []
    pos = 0
    for start in t.insertion_starts(line):
        if start < pos:
            continue
        depth = 0
        end = -1
        for i in range(start + 2, len(line) - 1):
            ch = line[i]
            if ch in "([{":
                depth += 1
            elif line.startswith("]]", i) and depth == 0:
                end = i
                break
            elif ch in ")]}":
                depth -= 1
        if end < 0:
            raise TemplateError("[[ is never closed with ]] on the same line")
        inner = line[start + 2 : end].strip()
        if not inner:
            raise TemplateError("empty [[ ]]")
        tex = False
        m = re.fullmatch(r"tex\s*\((.*)\)", inner, re.DOTALL)
        if m is not None and _matching(inner, inner.index("(") + 1) == len(inner) - 1:
            inner, tex = m.group(1).strip(), True
        out.append(Insertion(start, end + 2, compile_expr(inner), tex))
        pos = end + 2
    return out


# ---------------------------------------------------------------- parameters


@dataclass(frozen=True, slots=True)
class Param:
    name: str
    kind: Literal["int", "choice", "decimal"]
    line: int
    lo: Fraction = Fraction(0)
    hi: Fraction = Fraction(0)
    places: int = 0
    exclude: tuple[int, ...] = ()
    items: tuple[Expr, ...] = ()

    def size(self) -> int:
        if self.kind == "choice":
            return len(self.items)
        if self.kind == "decimal":
            return int((self.hi - self.lo) * 10**self.places) + 1
        span = int(self.hi - self.lo) + 1
        return span - sum(1 for x in set(self.exclude) if self.lo <= x <= self.hi)

    def value_at(self, index: int) -> Fraction | Expr:
        """The index-th value of the domain (int and decimal only enumerate lazily)."""
        if self.kind == "choice":
            return self.items[index]
        if self.kind == "decimal":
            return self.lo + Fraction(index, 10**self.places)
        value = int(self.lo)
        excluded = sorted(set(self.exclude))
        value += index
        for x in excluded:
            if self.lo <= x <= value:
                value += 1
        return Fraction(value)


@dataclass(frozen=True, slots=True)
class Definition:
    name: str
    expr: Expr
    line: int


@dataclass(frozen=True, slots=True)
class Condition:
    expr: Expr
    line: int


def parse_params(value: str, line: int) -> tuple[list[Param], str]:
    """`vars:` -> template parameters, and the checker variables left over (`x, t`)."""
    params: list[Param] = []
    checker: list[str] = []
    for part in t.split_top(value, ";"):
        if not part.strip():
            continue
        if "=" not in part:
            checker.append(part.strip())
            continue
        m = _DEFINITION.fullmatch(part)
        if m is None:
            raise TemplateError(f"vars: expected name = generator(...), got {part.strip()!r}", line)
        name, rhs = m.group(1), m.group(2)
        g = _GENERATOR.fullmatch(rhs)
        if g is None or g.group(1) not in GENERATORS:
            raise TemplateError(
                f"vars: {name} needs a generator: int(lo, hi), choice(a, b, ...) "
                "or decimal(lo, hi, places)",
                line,
            )
        args = [a.strip() for a in t.split_top(g.group(2), ",")]
        params.append(_generator(name, g.group(1), args, line))
    return params, ", ".join(checker)


def _generator(name: str, kind: str, args: list[str], line: int) -> Param:
    def fail(message: str) -> TemplateError:
        return TemplateError(f"vars: {name} = {kind}(...): {message}", line)

    if kind == "choice":
        if len(args) < 2 or any(not a for a in args):
            raise fail("give at least two choices")
        try:
            items = tuple(compile_expr(a) for a in args)
        except TemplateError as exc:
            raise fail(exc.message) from None
        for item in items:
            item.single()
        if any(item.calls for item in items):
            raise fail("choices can't use template functions")
        return Param(name, "choice", line, items=items)
    if kind == "int":
        if len(args) < 2 or not all(_INT.fullmatch(a) for a in args[:2]):
            raise fail("expected int(lo, hi) with whole numbers")
        lo, hi = int(args[0]), int(args[1])
        exclude: list[int] = []
        for extra in args[2:]:
            m = re.fullmatch(r"not\s+(-?\d+)", extra)
            if m is None:
                raise fail(f"expected 'not N', got {extra!r}")
            exclude.append(int(m.group(1)))
        if lo > hi:
            raise fail(f"{lo} is more than {hi}")
        param = Param(name, "int", line, Fraction(lo), Fraction(hi), exclude=tuple(exclude))
    else:
        if len(args) != 3 or not all(_DECIMAL.fullmatch(a) for a in args[:2]):
            raise fail("expected decimal(lo, hi, places)")
        if not args[2].isdigit() or not 0 <= int(args[2]) <= 6:
            raise fail("places is a whole number from 0 to 6")
        places = int(args[2])
        low, high = Fraction(args[0]), Fraction(args[1])
        step = Fraction(1, 10**places)
        if low > high or (low / step).denominator != 1 or (high / step).denominator != 1:
            raise fail(f"lo and hi must have at most {places} decimal places, lo <= hi")
        param = Param(name, "decimal", line, low, high, places)
    if param.size() < 1:
        raise fail("no values left")
    return param


def parse_definitions(value: str, line: int) -> list[Definition]:
    out: list[Definition] = []
    for part in t.split_top(value, ";"):
        if not part.strip():
            continue
        m = _DEFINITION.fullmatch(part)
        if m is None or not m.group(2):
            raise TemplateError(f"let: expected name = expression, got {part.strip()!r}", line)
        try:
            expr = compile_expr(m.group(2))
            expr.single()
        except TemplateError as exc:
            raise TemplateError(f"let {m.group(1)}: {exc.message}", line) from None
        out.append(Definition(m.group(1), expr, line))
    return out


def parse_conditions(value: str, line: int) -> list[Condition]:
    out: list[Condition] = []
    for part in t.split_top(value, ";"):
        if not part.strip():
            continue
        try:
            expr = compile_expr(part)
            node = n.unwrap(expr.single())
        except TemplateError as exc:
            raise TemplateError(f"require: {exc.message}", line) from None
        if not _is_condition(node):
            raise TemplateError(
                f"require: {part.strip()!r} is not a condition such as a != b", line
            )
        out.append(Condition(expr, line))
    return out


def _is_condition(node: n.Node) -> bool:
    match node:
        case n.Chain(_, ops):
            return bool(ops)
        case n.Or(items) | n.And(items):
            return all(_is_condition(n.unwrap(i)) for i in items)
    return False


# ---------------------------------------------------------------- the job


# ---------------------------------------------------------------- worked-solution checks

# Format 1.1 (MATH-17): a step of a ### Solution may carry indented `check:` lines, each an
# equality in answer syntax that may use the template functions and names, such as
# `check: diff(x^4 - 2x^2, x) = 4x^3 - 4x` or `check: solve(4x^3 - 4x, x) = {-1, 0, 1}`.
# The importer takes them out of the displayed step; the pack build checks them.
CLAIM_LINE = re.compile(r"[ \t]+check:[ \t]*(.*?)[ \t]*")
STEP_LINE = re.compile(r"(\d+)\.[ \t]")
_EQUALS = re.compile(r"(?<![<>!=])=(?!=)")


@dataclass(frozen=True, slots=True)
class Claim:
    """One `check:` line: its sides must all be equal."""

    step: int
    text: str
    sides: tuple[Expr, ...]
    line: int


def parse_claim(text: str, step: int, line: int) -> Claim:
    parts = [p.strip() for p in _EQUALS.split(text)]
    if len(parts) < 2 or not all(parts):
        raise TemplateError(f"check: {text!r} is not an equality such as diff(x^2, x) = 2x", line)
    try:
        sides = tuple(compile_expr(p) for p in parts)
    except TemplateError as exc:
        raise TemplateError(f"check: {exc.message}", line) from None
    return Claim(step, text, sides, line)


def solution_claims(lines: list[tuple[int, str]]) -> tuple[list[Claim], int | None]:
    """The `check:` lines of a ### Solution section (number, line) and its last step."""
    claims: list[Claim] = []
    step: int | None = None
    for number, line in lines:
        m = STEP_LINE.match(line)
        if m is not None:
            step = int(m.group(1))
            continue
        c = CLAIM_LINE.fullmatch(line)
        if c is not None and step is not None:
            claims.append(parse_claim(c.group(1), step, number))
    return claims, step


@dataclass(frozen=True, slots=True)
class WrongEntry:
    answer: Expr | None  # None for plain answer types (text, choice): kept as written
    answer_text: str
    feedback: str | None
    feedback_insertions: tuple[Insertion, ...]
    step: int | None


@dataclass(frozen=True, slots=True)
class Slot:
    """What happens to one line of the block in each instance."""

    index: int  # into TemplateJob.lines
    role: Literal["text", "answer", "wrong", "drop", "vars"]
    prefix: str = ""  # "answer: " ... (the key and separator as written)
    answer_type: str = ""
    expr: Expr | None = None  # answer
    insertions: tuple[Insertion, ...] = ()  # text, or a plain-type answer
    wrong: tuple[WrongEntry, ...] = ()
    value: str = ""  # vars: the checker variables left after removing parameters


@dataclass(frozen=True, slots=True)
class TemplateJob:
    template_id: str
    file: str
    first_line: int  # line number of lines[0]
    lines: tuple[str, ...]
    slots: tuple[Slot, ...]
    params: tuple[Param, ...] = ()
    lets: tuple[Definition, ...] = ()
    requires: tuple[Condition, ...] = ()
    claims: tuple[Claim, ...] = ()  # worked-solution checks, for every instance
    final_step: int | None = None  # the solution's last step: its last claim is the final line
    max_instances: int = MAX_INSTANCES
    seconds: float = INSTANCE_SECONDS
    test_sleep: float = 0.0  # tests only: sleep this long inside every instance

    def combinations(self) -> int:
        total = 1
        for p in self.params:
            total *= p.size()
        return total


@dataclass(frozen=True, slots=True)
class Instance:
    seed: int
    params: str  # "k = 3; m = 1/2"
    lines: tuple[str, ...]
    seconds: float
    final: str | None = None  # the final line's value in answer syntax, when a claim gives it


@dataclass(frozen=True, slots=True)
class SweepResult:
    instances: tuple[Instance, ...] = ()
    error: str | None = None
    line: int | None = None
    combinations: int = 0
    tried: int = 0
    rejected_by_require: int = 0
    cross_checked: int = 0  # DEV-18: template operations mpmath agreed with
    cross_unverified: int = 0  # ... and those mpmath could not compute


@dataclass(slots=True)
class _Scan:
    job_lines: list[str]
    first: int
    slots: list[Slot] = field(default_factory=list)


def compile_template(
    block: t.BlockSrc, lines: list[str], header: dict[str, t.KeyLine], file: str
) -> TemplateJob:
    """Read a template block into a job. Raises TemplateError with the line."""
    first = block.line
    body = lines[block.start : block.end]
    scan = _Scan(list(body), first)
    params: list[Param] = []
    checker_vars = ""
    lets: list[Definition] = []
    requires: list[Condition] = []
    keys = block.keys
    if "vars" in keys:
        params, checker_vars = parse_params(keys["vars"].value, keys["vars"].line)
    if "let" in keys:
        lets = parse_definitions(keys["let"].value, keys["let"].line)
    if "require" in keys:
        requires = parse_conditions(keys["require"].value, keys["require"].line)
    _check_names(params, lets, requires)

    card_type = (
        keys.get("answer-type") or header.get("answer-type") or t.KeyLine("", "self", 0)
    ).value
    for key, kl in keys.items():
        index = kl.line - first
        if key == "vars":
            scan.slots.append(Slot(index, "vars", value=checker_vars))
        elif key in {"let", "require"}:
            scan.slots.append(Slot(index, "drop"))
        elif key in {"answer", "wrong"}:
            _answer_slot(scan, index, key, kl.value, card_type, kl.line)
        else:
            _text_slot(scan, index, kl.line)
    key_lines = {kl.line for kl in keys.values()}
    claims: list[Claim] = []
    final_step: int | None = None
    for sec in block.sections:
        if sec.name == "Solution":
            claims, final_step = solution_claims(list(sec.lines))
        part_type = "self"
        part_keys: dict[str, int] = {}
        if PART_HEADING.fullmatch(sec.name):
            for number, line in sec.lines:
                if not line.strip():
                    continue
                m = t.KEY_LINE.fullmatch(line)
                if m is None or m.group(1) not in PART_KEYS:
                    break
                part_keys[m.group(1)] = number
                if m.group(1) == "answer-type":
                    part_type = (m.group(2) or "").strip()
        for number, line in sec.lines:
            index = number - first
            role = next((k for k, v in part_keys.items() if v == number), None)
            if role in {"answer", "wrong"}:
                m = t.KEY_LINE.fullmatch(line)
                value = (m.group(2) or "").strip() if m is not None else ""
                _answer_slot(scan, index, role, value, part_type, number)
            elif number not in key_lines:
                _text_slot(scan, index, number)
    return TemplateJob(
        template_id=block.id,
        file=file,
        first_line=first,
        lines=tuple(scan.job_lines),
        slots=tuple(scan.slots),
        params=tuple(params),
        lets=tuple(lets),
        requires=tuple(requires),
        claims=tuple(claims),
        final_step=final_step,
    )


def _check_names(params: list[Param], lets: list[Definition], requires: list[Condition]) -> None:
    seen: dict[str, int] = {}
    for name, line in [(p.name, p.line) for p in params] + [(d.name, d.line) for d in lets]:
        if not is_variable_name(name) or name in RESERVED:
            raise TemplateError(
                f"{name!r} can't be a template name: use one letter, a Greek letter or a_1", line
            )
        if name in seen:
            raise TemplateError(f"{name} is defined twice", line)
        seen[name] = line
    for p in params:
        used = sorted({name for item in p.items for name in item.names} & set(seen))
        if used:
            raise TemplateError(
                f"choices for {p.name} can't use the template names {', '.join(used)}", p.line
            )
    let_names = [d.name for d in lets]
    for i, d in enumerate(lets):
        later = sorted(d.expr.names & set(let_names[i:]))
        if later:
            raise TemplateError(
                f"let {d.name} uses {', '.join(later)} before it is defined", d.line
            )
    for c in requires:
        unknown = sorted(c.expr.names - set(seen))
        if unknown:
            raise TemplateError(
                f"require uses {', '.join(unknown)}, which is not a parameter or let", c.line
            )


def _text_slot(scan: _Scan, index: int, number: int) -> None:
    line = scan.job_lines[index]
    if "[[" not in line:
        return
    try:
        found = find_insertions(line)
    except TemplateError as exc:
        raise TemplateError(exc.message, number) from None
    scan.slots.append(Slot(index, "text", insertions=tuple(found)))


def _answer_slot(
    scan: _Scan, index: int, key: str, value: str, answer_type: str, number: int
) -> None:
    line = scan.job_lines[index]
    prefix = line[: line.index(":") + 1] + " "
    math = answer_type in MATH_TYPES
    try:
        if key == "answer":
            if math:
                scan.slots.append(
                    Slot(index, "answer", prefix, answer_type, expr=compile_expr(value))
                )
            elif "[[" in value:
                found = tuple(find_insertions(value))
                scan.slots.append(
                    Slot(index, "answer", prefix, answer_type, insertions=found, value=value)
                )
            return
        from core.grader import parse_wrong_field

        entries: list[WrongEntry] = []
        for w in parse_wrong_field(value):
            feedback_ins = tuple(find_insertions(w.feedback)) if w.feedback else ()
            expr = compile_expr(w.answer) if math and w.answer else None
            entries.append(WrongEntry(expr, w.answer, w.feedback, feedback_ins, w.step))
        scan.slots.append(Slot(index, "wrong", prefix, answer_type, wrong=tuple(entries)))
    except TemplateError as exc:
        raise TemplateError(f"{key}: {exc.message}", number) from None
