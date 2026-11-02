"""Evaluates template jobs with SymPy. Runs only in the sweep process (sweep.py).

A whitelist evaluator: the grader's parser built the trees (template.py), the grader's
translator turns scalar trees into SymPy objects (no string ever reaches SymPy), and
only the operations listed in template.OPS are applied. Parameters are substituted
before any operation runs, so SymPy only ever sees concrete numbers and free variables.
"""

import hashlib
import itertools
import random
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import sympy

from core.cards import differential
from core.cards import template as tp
from core.grader import nodes as n
from core.grader.serialize import to_answer_syntax, to_text
from core.grader.translate import SympyContext, TranslateError, from_sympy, to_sympy

MAX_DRAWS_PER_INSTANCE = 20
DECIMAL_DIGITS = 15


class EvalError(Exception):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


class _Dne:
    """A limit that does not exist."""

    def __repr__(self) -> str:
        return "DNE"


DNE = _Dne()
_SET_TYPES = (sympy.FiniteSet, sympy.Interval, sympy.Union)


@dataclass(frozen=True, slots=True)
class Value:
    v: Any  # sympy.Expr (scalar), a set, sympy.Rel (only inside solve), or DNE
    decimal: bool = False

    @property
    def scalar(self) -> bool:
        return isinstance(self.v, sympy.Expr)


def _symbol(name: str) -> sympy.Symbol:
    return sympy.Symbol(name, real=True)


def _bad(expr: Any) -> bool:
    return isinstance(expr, sympy.Basic) and expr.has(sympy.zoo, sympy.nan)


def _complex(expr: Any) -> bool:
    """Templates work over the reals: a value with i in it is a template error."""
    return isinstance(expr, sympy.Basic) and (expr.has(sympy.I) or expr.is_extended_real is False)


def _infinity(node: n.Node) -> sympy.Expr | None:
    node = n.unwrap(node)
    if isinstance(node, n.Const) and node.name == "inf":
        return sympy.oo
    if isinstance(node, n.Neg) and n.unwrap(node.arg) == n.Const("inf"):
        return -sympy.oo
    return None


class Evaluator:
    def __init__(self, env: dict[str, Value], tally: differential.Tally | None = None) -> None:
        self.env = env
        self.tally = tally if tally is not None else differential.Tally()

    # ------------------------------------------------------------ scalars and items

    def _calls(self, expr: tp.Expr) -> dict[str, Value]:
        return {name: self.call(call) for name, call in expr.calls}

    def scalar(self, node: n.Node, ph: dict[str, Value]) -> Value:
        inf = _infinity(node)
        if inf is not None:
            return Value(inf)
        names = n.free_vars(node)
        bound = {name: (ph.get(name) or self.env.get(name)) for name in names}
        for name, value in bound.items():
            if value is not None and not value.scalar:
                what = "DNE" if value.v is DNE else "a set or list"
                raise EvalError(f"{name} is {what}, not a number: use it on its own")
        try:
            raw = to_sympy(node, SympyContext({name: _symbol(name) for name in names}))
        except TranslateError as exc:
            raise EvalError(f"can't compute {to_text(node)!r}: {exc}") from None
        mapping = {_symbol(k): v.v for k, v in bound.items() if v is not None}
        result = raw.xreplace(mapping) if mapping else raw
        if _bad(result):
            raise EvalError(f"{to_text(node)!r} is undefined here (division by zero?)")
        if _complex(result):
            raise EvalError(f"{to_text(node)!r} is not a real number here")
        decimal = any(v.decimal for v in bound.values() if v is not None)
        return Value(result, decimal)

    def item(self, node: n.Node, ph: dict[str, Value]) -> Value:
        """One value: a scalar, or a bare name holding a set, a list or DNE."""
        bare = n.unwrap(node)
        if isinstance(bare, n.Var):
            found = ph.get(bare.name) or self.env.get(bare.name)
            if found is not None and not found.scalar:
                return found
        if isinstance(bare, n.Chain) and len(bare.ops) == 1:
            a, b = (self.scalar(o, ph) for o in bare.operands)
            rel = {"=": sympy.Eq, "<": sympy.Lt, "<=": sympy.Le, ">": sympy.Gt, ">=": sympy.Ge}
            op = bare.ops[0]
            if op not in rel:
                raise EvalError(f"can't use {op} here")
            return Value(rel[op](a.v, b.v, evaluate=False), a.decimal or b.decimal)
        if isinstance(bare, n.SCALAR_NODES):
            return self.scalar(bare, ph)
        raise EvalError(f"{to_text(node)!r} is not a single value")

    def single(self, expr: tp.Expr) -> Value:
        return self.item(expr.single(), self._calls(expr))

    # ------------------------------------------------------------ template functions

    def call(self, call: tp.OpCall) -> Value:
        name = call.name
        args = call.args

        def value(i: int) -> Value:
            return self.single(_expr(args[i]))

        def number(i: int) -> sympy.Expr:
            got = value(i)
            if not got.scalar:
                raise EvalError(f"{name}: argument {i + 1} must be a number or expression")
            return got.v

        def variable(i: int) -> sympy.Symbol:
            node = _expr(args[i]).single()
            if not isinstance(node, n.Var):  # template.py checked this already
                raise EvalError(f"{name}: argument {i + 1} must be a variable")
            if node.name in self.env:
                raise EvalError(f"{name}: {node.name} is a template name, not a variable")
            return _symbol(node.name)

        first = value(0)
        f = first.v
        decimal = first.decimal
        if name != "solve" and not first.scalar:
            raise EvalError(f"{name} needs a number or expression, not a set or list")
        x: sympy.Symbol | None = None
        extra: list[Any] = []  # the arguments the differential check needs (DEV-18)
        try:
            if name == "diff":
                order = int(number(2)) if len(args) == 3 else 1
                x, extra = variable(1), [order]
                result: Any = sympy.diff(f, x, order)
            elif name == "integrate":
                x = variable(1)
                if len(args) == 4:
                    extra = [number(2), number(3)]
                    result = sympy.integrate(f, (x, extra[0], extra[1]))
                else:
                    result = sympy.integrate(f, x)
                if result.has(sympy.Integral):
                    raise EvalError(f"integrate: SymPy can't integrate {to_answer_syntax(f)}")
            elif name == "limit":
                side = (
                    {"left": "-", "right": "+"}.get(str(args[3]), "+-") if len(args) == 4 else "+-"
                )
                x, extra = variable(1), [number(2), side]
                result = self._limit(f, x, extra[0], side)
                if result is DNE:
                    return Value(DNE)
            elif name == "solve":
                x = variable(1)
                result = self._solve(f, x)
                self._cross(name, f, x, extra, result)
                return Value(result, decimal)
            elif name == "subs":
                replacement = value(2)
                if not replacement.scalar:
                    raise EvalError("subs: the value must be a number or expression")
                x, extra = variable(1), [replacement.v]
                result = f.subs(x, replacement.v)
                decimal = decimal or replacement.decimal
            elif name == "simplify":
                result = sympy.simplify(f)
            elif name == "expand":
                result = sympy.expand(f)
            else:
                result = sympy.factor(f)
        except (TypeError, ValueError, NotImplementedError, ZeroDivisionError) as exc:
            raise EvalError(f"{name} failed: {exc}") from None
        if _bad(result):
            raise EvalError(f"{name} gives an undefined result")
        if _complex(result):
            raise EvalError(f"{name} gives a value that is not a real number")
        if not isinstance(result, sympy.Expr):
            raise EvalError(f"{name} gives {type(result).__name__}, not a value")
        self._cross(name, f, x, extra, result)
        return Value(result, decimal)

    def _cross(self, name: str, f: Any, x: Any, extra: list[Any], result: Any) -> None:
        """DEV-18: an independent mpmath route must agree with SymPy's result."""
        try:
            differential.check(name, f, x, extra, result, self.tally)
        except differential.Disagreement as exc:
            raise EvalError(str(exc)) from None

    @staticmethod
    def _limit(f: sympy.Expr, x: sympy.Symbol, a: sympy.Expr, side: str) -> Any:
        if a.is_infinite:
            side = "-" if a == sympy.oo else "+"
        try:
            result = sympy.limit(f, x, a, dir=side)
        except ValueError:
            return DNE  # SymPy: "The limit does not exist since left ... and right ..."
        if isinstance(result, sympy.AccumBounds) or result is sympy.zoo:
            return DNE
        if result.has(sympy.Limit) or result is sympy.nan:
            raise EvalError("limit: SymPy can't find this limit")
        return result

    @staticmethod
    def _solve(f: Any, x: sympy.Symbol) -> Any:
        if not isinstance(f, sympy.Expr | sympy.core.relational.Relational):
            raise EvalError("solve needs an expression or an equation")
        result = sympy.solveset(f, x, domain=sympy.S.Reals)
        if result is sympy.S.EmptySet or isinstance(result, sympy.Interval):
            return result
        if isinstance(result, sympy.FiniteSet):
            if not all(isinstance(v, sympy.Expr) and v.is_real and v.is_finite for v in result):
                raise EvalError("solve: the solutions are not all real numbers")
            return result
        if isinstance(result, sympy.Union) and all(
            isinstance(a, sympy.Interval | sympy.FiniteSet) for a in result.args
        ):
            return result
        raise EvalError(f"solve: SymPy can't list the real solutions ({type(result).__name__})")

    # ------------------------------------------------------------ conditions

    def truth(self, node: n.Node, ph: dict[str, Value]) -> bool:
        node = n.unwrap(node)
        match node:
            case n.Or(items):
                return any(self.truth(i, ph) for i in items)
            case n.And(items):
                return all(self.truth(i, ph) for i in items)
            case n.Chain(operands, ops):
                values = [self.scalar(o, ph).v for o in operands]
                for a, op, b in zip(values, ops, values[1:], strict=False):
                    if not _compare(a, op, b):
                        return False
                return True
        raise EvalError(f"{to_text(node)!r} is not a condition")

    def holds(self, cond: tp.Condition) -> bool:
        return self.truth(cond.expr.single(), self._calls(cond.expr))

    # ------------------------------------------------------------ worked-solution claims

    def side(self, expr: tp.Expr) -> Value:
        """One side of a `check:` claim: a value, a set (`{-1, 0, 1}` or `-1, 0, 1`) or DNE."""
        ph = self._calls(expr)
        if len(expr.parsed.alternatives) != 1:
            raise EvalError(f"{expr.text!r}: use one value, not alternatives")
        items = expr.parsed.alternatives[0]
        if len(items) == 1:
            node = n.unwrap(items[0])
            if isinstance(node, n.NoneSet):
                return Value(sympy.S.EmptySet)
            if isinstance(node, n.Dne):
                return Value(DNE)
            if isinstance(node, n.SetLit):
                items = node.items
            else:
                return self.item(items[0], ph)
        return Value(sympy.FiniteSet(*(self.scalar(i, ph).v for i in items)))

    def claim_holds(self, claim: tp.Claim) -> bool:
        values = [self.side(s) for s in claim.sides]
        for (ea, a), (eb, b) in itertools.pairwise(zip(claim.sides, values, strict=True)):
            x = _antiderivative_var(ea) or _antiderivative_var(eb)
            if x is not None and a.scalar and b.scalar:  # antiderivatives: up to a constant
                if not _same_scalar(sympy.diff(a.v, _symbol(x)), sympy.diff(b.v, _symbol(x))):
                    return False
            elif not _same(a, b):
                return False
        return True

    # ------------------------------------------------------------ output

    def side_text(self, expr: tp.Expr) -> str:
        """A claim's side in answer syntax (sets as their elements, like a set answer)."""
        value = self.side(expr)
        if value.v is DNE:
            return "DNE"
        if isinstance(value.v, sympy.FiniteSet):
            return ", ".join(to_answer_syntax(v) for v in _sorted(value.v)) or "none"
        if value.scalar:
            return to_answer_syntax(value.v)
        return _set_text(value, display=False)

    def answer_text(self, expr: tp.Expr) -> str:
        """An answer key, exact, in answer syntax (to_answer_syntax for computed values)."""
        ph = self._calls(expr)
        alternatives: list[str] = []
        for alt in expr.parsed.alternatives:
            alternatives.append(", ".join(self._item_text(item, ph, display=False) for item in alt))
        return "; ".join(alternatives)

    def insertion_text(self, ins: tp.Insertion) -> str:
        ph = self._calls(ins.expr)
        if ins.tex:
            return self._tex(ins.expr, ph)
        alts = ins.expr.parsed.alternatives
        return "; ".join(
            ", ".join(self._item_text(i, ph, display=True) for i in alt) for alt in alts
        )

    def _item_text(self, node: n.Node, ph: dict[str, Value], *, display: bool) -> str:
        bare = n.unwrap(node)
        if isinstance(bare, n.Var):
            found = ph.get(bare.name) or self.env.get(bare.name)
            if found is not None and not found.scalar:
                return _set_text(found, display)
        return to_text(self._rebuild(node, ph, display))

    def _rebuild(self, node: n.Node, ph: dict[str, Value], display: bool) -> n.Node:
        """Containers keep their shape; scalars that use template names are computed."""
        if isinstance(node, n.SCALAR_NODES):
            names = n.free_vars(node)
            if not display and not names & (set(ph) | set(self.env)):
                return node  # an answer the author wrote out: kept exactly as written
            value = self.scalar(node, ph)
            return _scalar_node(value, display)
        match node:
            case n.Tuple(items, left, right):
                return n.Tuple(tuple(self._rebuild(i, ph, display) for i in items), left, right)
            case n.SetLit(items):
                return n.SetLit(tuple(self._rebuild(i, ph, display) for i in items))
            case n.Vector(items):
                return n.Vector(tuple(self._rebuild(i, ph, display) for i in items))
            case n.Matrix(rows):
                return n.Matrix(
                    tuple(tuple(self._rebuild(x, ph, display) for x in r) for r in rows)
                )
            case n.Union(items):
                return n.Union(tuple(self._rebuild(i, ph, display) for i in items))
            case n.Chain(operands, ops):
                return n.Chain(tuple(self._rebuild(o, ph, display) for o in operands), ops)
            case n.Or(items):
                return n.Or(tuple(self._rebuild(i, ph, display) for i in items))
            case n.And(items):
                return n.And(tuple(self._rebuild(i, ph, display) for i in items))
        for sub in n.walk(node):
            if isinstance(sub, n.Var) and (sub.name in ph or sub.name in self.env):
                raise EvalError(f"can't compute inside {to_text(node)!r}")
        return node

    def _tex(self, expr: tp.Expr, ph: dict[str, Value]) -> str:
        node = expr.single()
        bare = n.unwrap(node)
        if isinstance(bare, n.Var):
            found = ph.get(bare.name) or self.env.get(bare.name)
            if found is not None and not found.scalar:
                if found.v is DNE:
                    return r"\text{DNE}"
                return _set_tex(found)
        value = self.item(node, ph)
        if not value.scalar:
            raise EvalError("tex() takes a single value")
        return _latex(_decimalize(value.v) if value.decimal else value.v)


def _expr(arg: tp.Expr | str) -> tp.Expr:
    if not isinstance(arg, tp.Expr):
        raise EvalError(f"expected an expression, got {arg!r}")
    return arg


def _antiderivative_var(expr: tp.Expr) -> str | None:
    """The variable of `integrate(f, x)` when that is the whole side, else None."""
    try:
        node = n.unwrap(expr.single())
    except tp.TemplateError:
        return None
    call = dict(expr.calls).get(node.name) if isinstance(node, n.Var) else None
    if call is None or call.name != "integrate" or len(call.args) != 2:
        return None
    var = _expr(call.args[1]).single()
    return var.name if isinstance(var, n.Var) else None


def _same(a: Value, b: Value) -> bool:
    """Equal values of a claim: numbers and expressions (sampled by mpmath, then SymPy),
    sets element by element, DNE only with DNE."""
    if a.v is DNE or b.v is DNE:
        return a.v is DNE and b.v is DNE
    if a.scalar and b.scalar:
        return _same_scalar(a.v, b.v)
    if isinstance(a.v, sympy.FiniteSet) and isinstance(b.v, sympy.FiniteSet):
        xs, ys = list(a.v), list(b.v)
        return all(any(_same_scalar(p, q) for q in ys) for p in xs) and all(
            any(_same_scalar(p, q) for p in xs) for q in ys
        )
    if isinstance(a.v, sympy.Set) and isinstance(b.v, sympy.Set):
        return bool(a.v == b.v or a.v.symmetric_difference(b.v) is sympy.S.EmptySet)
    return False


def _same_scalar(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    numeric = differential.same_values(a, b)  # the independent route first (DEV-18)
    if numeric is False:
        return False
    try:
        zero = sympy.simplify(a - b) == 0
    except TypeError, ValueError, NotImplementedError, RecursionError:
        zero = False
    if numeric is None and not zero:
        raise EvalError(f"can't check that {to_answer_syntax(a)} = {to_answer_syntax(b)}")
    return True


def _compare(a: sympy.Expr, op: str, b: sympy.Expr) -> bool:
    sign = _sign(a - b) if not (a.is_infinite or b.is_infinite) else _sign_inf(a, b)
    return {
        "=": sign == 0,
        "!=": sign != 0,
        "<": sign < 0,
        "<=": sign <= 0,
        ">": sign > 0,
        ">=": sign >= 0,
    }[op]


def _sign_inf(a: sympy.Expr, b: sympy.Expr) -> int:
    if a == b:
        return 0
    if a == sympy.oo or b == -sympy.oo:
        return 1
    return -1


def _sign(d: sympy.Expr) -> int:
    if d.free_symbols:
        names = ", ".join(sorted(str(s) for s in d.free_symbols))
        raise EvalError(f"require: the condition depends on {names}")
    if d.is_zero:
        return 0
    if d.is_positive:
        return 1
    if d.is_negative:
        return -1
    approx = sympy.N(d, 50)
    if approx.is_Number and abs(approx) > sympy.Float("1e-40", 50):
        return 1 if approx > 0 else -1
    if sympy.simplify(d).is_zero:
        return 0
    raise EvalError(f"require: can't decide the sign of {d}")


def _terminating(r: sympy.Rational) -> bool:
    q = int(r.q)
    for p in (2, 5):
        while q % p == 0:
            q //= p
    return q == 1


def _decimalize(e: Any) -> Any:
    """Show terminating fractions as decimals (values computed from decimal parameters)."""
    if isinstance(e, sympy.Rational) and not e.is_Integer and _terminating(e):
        return sympy.Float(e, DECIMAL_DIGITS)
    if isinstance(e, sympy.Pow):
        return sympy.Pow(_decimalize(e.base), e.exp)
    if isinstance(e, sympy.Basic) and e.args and not isinstance(e, sympy.Rational):
        return e.func(*[_decimalize(a) for a in e.args])
    return e


def _scalar_node(value: Value, display: bool) -> n.Node:
    if _complex(value.v):  # never write i: the checker would read it as a variable
        raise EvalError("the result is not a real number")
    v = _decimalize(value.v) if display and value.decimal else value.v
    try:
        node = from_sympy(v)
    except TranslateError as exc:
        raise EvalError(f"the result can't be written as an answer: {exc}") from None
    return node


def _set_text(value: Value, display: bool) -> str:
    if value.v is DNE:
        return "DNE"
    v = value.v
    try:
        if isinstance(v, sympy.FiniteSet):
            items = _sorted(v)
            return ", ".join(to_text(_scalar_node(Value(x, value.decimal), display)) for x in items)
        if _complex(v):
            raise EvalError("the result is not a real number")
        return str(to_answer_syntax(v))
    except ValueError as exc:
        raise EvalError(f"the result can't be written as an answer: {exc}") from None


def _set_tex(value: Value) -> str:
    v = value.v
    if v is sympy.S.EmptySet:
        return r"\varnothing"
    if isinstance(v, sympy.FiniteSet):
        items = _sorted(v)
        return ", ".join(_latex(_decimalize(x) if value.decimal else x) for x in items)
    return _latex(v)


def _sorted(values: sympy.FiniteSet) -> list[Any]:
    items = list(values)
    if all(x.is_real and x.is_number for x in items):
        return sorted(items, key=lambda x: sympy.N(x, 30))
    return sorted(items, key=sympy.default_sort_key)


def _latex(v: Any) -> str:
    return str(sympy.latex(v, ln_notation=True, inv_trig_style="full"))


# ---------------------------------------------------------------- running a job


def _param_value(param: tp.Param, raw: Fraction | tp.Expr) -> Value:
    if isinstance(raw, tp.Expr):
        value = Evaluator({}).single(raw)
        if not value.scalar:
            raise EvalError(f"choice for {param.name}: {raw.text!r} is not a single value")
        return value
    return Value(sympy.Rational(raw.numerator, raw.denominator), param.kind == "decimal")


def _param_text(name: str, value: Value) -> str:
    return f"{name} = {to_text(_scalar_node(value, display=True))}"


def seed_of(params_text: str) -> int:
    return int(hashlib.sha256(params_text.encode()).hexdigest()[:8], 16)


def _draws(job: tp.TemplateJob) -> Iterator[tuple[int, ...]]:
    sizes = [p.size() for p in job.params]
    total = job.combinations()
    if total <= job.max_instances:
        yield from itertools.product(*(range(s) for s in sizes))
        return
    rng = random.Random(job.template_id)  # noqa: S311 - reproducible draws, not security
    for _ in range(job.max_instances * MAX_DRAWS_PER_INSTANCE):
        yield tuple(rng.randrange(s) for s in sizes)


type Report = Callable[[str, Any], None]


def run(job: tp.TemplateJob, report: Report) -> tp.SweepResult:
    """Expand a template. Calls report("instance", Instance) / report("tick", None) as it
    goes (the sweep process forwards them so the caller can enforce the time limit)."""
    instances: list[tp.Instance] = []
    seen: set[tuple[int, ...]] = set()
    seeds: dict[int, str] = {}
    tried = 0
    rejected = 0
    tally = differential.Tally()
    for draw in _draws(job):
        if len(instances) >= job.max_instances:
            break
        if draw in seen:
            report("tick", None)
            continue
        seen.add(draw)
        tried += 1
        start = time.perf_counter()
        env: dict[str, Value] = {}
        texts: list[str] = []
        line = job.first_line
        try:
            for param, index in zip(job.params, draw, strict=True):
                line = param.line
                env[param.name] = _param_value(param, param.value_at(index))
                texts.append(_param_text(param.name, env[param.name]))
            params_text = "; ".join(texts)
            ok, line = _evaluate(job, env, tally)
            if not ok:
                rejected += 1
                report("tick", None)
                continue
            if job.test_sleep:
                time.sleep(job.test_sleep)
            final = _claims(job, Evaluator(env, tally))
            lines, line = _render(job, Evaluator(env, tally))
        except (EvalError, tp.TemplateError) as exc:
            where = f"instance {'; '.join(texts)}: " if texts else ""
            message = exc.message if isinstance(exc, tp.TemplateError) else str(exc)
            line = exc.line or line
            result = tp.SweepResult(
                tuple(instances), f"{where}{message}", line, job.combinations(), tried, rejected
            )
            return result
        seconds = time.perf_counter() - start
        if seconds > job.seconds:
            return tp.SweepResult(
                tuple(instances),
                f"instance {params_text}: took {seconds:.1f} s (the limit is {job.seconds:g} s)",
                job.first_line,
                job.combinations(),
                tried,
                rejected,
            )
        seed = seed_of(params_text)
        if seeds.get(seed) == params_text:  # equal choices made the same parameter set
            report("tick", None)
            continue
        if seed in seeds:
            message = f"instances {seeds[seed]!r} and {params_text!r} share a seed"
            return tp.SweepResult(
                tuple(instances), message, job.first_line, job.combinations(), tried, rejected
            )
        seeds[seed] = params_text
        instance = tp.Instance(seed, params_text, tuple(lines), seconds, final)
        instances.append(instance)
        report("instance", instance)
    if not instances:
        message = "no parameter set meets require" if rejected else "the template made no instances"
        line = job.requires[0].line if job.requires else job.first_line
        return tp.SweepResult((), message, line, job.combinations(), tried, rejected)
    return tp.SweepResult(
        tuple(instances), None, None, job.combinations(), tried, rejected,
        tally.checked, tally.unverified,
    )  # fmt: skip


def _evaluate(
    job: tp.TemplateJob, env: dict[str, Value], tally: differential.Tally | None = None
) -> tuple[bool, int]:
    """Lets in order; each require as soon as the names it uses are defined."""
    pending = list(job.requires)
    ev = Evaluator(env, tally)

    def check() -> tuple[bool, int]:
        for cond in list(pending):
            if cond.expr.names <= set(env):
                pending.remove(cond)
                try:
                    holds = ev.holds(cond)
                except EvalError as exc:
                    raise EvalError(str(exc), cond.line) from None
                if not holds:
                    return False, cond.line
        return True, job.first_line

    ok, line = check()
    if not ok:
        return False, line
    for definition in job.lets:
        try:
            env[definition.name] = ev.single(definition.expr)
        except EvalError as exc:
            raise EvalError(f"let {definition.name}: {exc}", definition.line) from None
        ok, line = check()
        if not ok:
            return False, line
    return True, job.first_line


def _claims(job: tp.TemplateJob, ev: Evaluator) -> str | None:
    """Check every worked-solution claim (MATH-17); the final line's value, if one gives it."""
    final: str | None = None
    for claim in job.claims:
        try:
            holds = ev.claim_holds(claim)
        except EvalError as exc:
            raise EvalError(f"solution step {claim.step}: check {claim.text!r}: {exc}",
                            claim.line) from None  # fmt: skip
        if not holds:
            raise EvalError(f"solution step {claim.step}: check {claim.text!r} is false",
                            claim.line)  # fmt: skip
        if claim.step == job.final_step:
            final = ev.side_text(claim.sides[-1])
    return final


def _render(job: tp.TemplateJob, ev: Evaluator) -> tuple[list[str], int]:
    lines = list(job.lines)
    for slot in job.slots:
        number = job.first_line + slot.index
        try:
            lines[slot.index] = _render_slot(slot, lines[slot.index], ev)
        except EvalError as exc:
            raise EvalError(str(exc), number) from None
    return lines, job.first_line


def _substitute(line: str, insertions: tuple[tp.Insertion, ...], ev: Evaluator) -> str:
    for ins in sorted(insertions, key=lambda i: i.start, reverse=True):
        line = line[: ins.start] + ev.insertion_text(ins) + line[ins.end :]
    return line


def _render_slot(slot: tp.Slot, line: str, ev: Evaluator) -> str:
    if slot.role == "drop":
        return ""
    if slot.role == "vars":
        return f"vars: {slot.value}" if slot.value else ""
    if slot.role == "text":
        return _substitute(line, slot.insertions, ev)
    if slot.role == "answer":
        if slot.expr is not None:
            return slot.prefix + ev.answer_text(slot.expr)
        return slot.prefix + _substitute(slot.value, slot.insertions, ev)
    entries: list[str] = []
    for w in slot.wrong:
        answer = ev.answer_text(w.answer) if w.answer is not None else w.answer_text
        text = answer
        if w.feedback:
            feedback = w.feedback
            for ins in sorted(w.feedback_insertions, key=lambda i: i.start, reverse=True):
                feedback = feedback[: ins.start] + ev.insertion_text(ins) + feedback[ins.end :]
            text += f" => {feedback}"
        if w.step is not None:
            text += f" @{w.step}"
        entries.append(text)
    return slot.prefix + "; ".join(entries)
