"""Differential checks (DEV-18): mpmath cross-checks what SymPy computes for templates.

SymPy computes every template value (cas.py) and drives the grader's symbolic step, so a
bug in it would be invisible to both. This module recomputes each template operation by
an independent route: our own mpmath evaluator (core/grader/numeric.py, which never calls
SymPy) on trees translated from SymPy's input and output, with mpmath's own calculus:

- diff: mp.diff of the input against the derivative SymPy gave;
- integrate: mp.diff of the antiderivative back to the integrand, or mp.quad for a
  definite integral;
- limit: mp.limit from the requested side(s);
- solve: every solution substituted back, and a sign-change scan for a missed root
  (inequalities: membership at sample points against the relation itself);
- subs, simplify, expand, factor: both sides at sample points.

A disagreement raises Disagreement. A value mpmath can't compute (a singular integral,
a limit that doesn't settle) is counted as unverified, never as a pass. Runs in the sweep
process only (it imports SymPy through cas.py).
"""

import itertools
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import mpmath
import sympy
from mpmath import mp

from core.grader import nodes as n
from core.grader.numeric import Evaluator, Number, Overflow, Undefined
from core.grader.translate import TranslateError, from_sympy

DPS = 30
SAMPLES = (-2.7, -1.3, -0.6, 0.35, 0.8, 1.7, 2.9, 4.1)  # off the integers and small fractions
OTHER_VALUES = (0.77, 1.31, 2.23, 0.41)  # for free symbols other than the operation's variable
CLOSE = mpmath.mpf("1e-9")  # relative agreement for values mpmath computes directly
LIMIT_CLOSE = mpmath.mpf("1e-6")  # mp.limit extrapolates: looser
MIN_POINTS = 2
SCAN = (-20, 20, 801)  # missed-root scan for solve: from, to, points


class Disagreement(Exception):
    """SymPy and mpmath give different values."""


@dataclass(slots=True)
class Tally:
    checked: int = 0
    unverified: int = 0


type Fn = Callable[[Number], Number]


def _node(expr: Any) -> n.Node | None:
    try:
        return from_sympy(sympy.Integer(expr) if isinstance(expr, int) else expr)
    except TranslateError, TypeError, ValueError, AttributeError:
        return None


def _function(expr: Any, x: sympy.Symbol, others: Mapping[str, Number]) -> Fn | None:
    """expr as a function of x, evaluated by our own mpmath evaluator (not SymPy)."""
    node = _node(expr)
    if node is None:
        return None
    ev = Evaluator()
    name = str(x)

    def f(t: Number) -> Number:
        return ev(node, {**others, name: t})

    return f


def _others(*exprs: Any, x: sympy.Symbol) -> dict[str, Number] | None:
    names: set[str] = set()
    for e in exprs:
        if isinstance(e, sympy.Basic):
            names |= {str(s) for s in e.free_symbols}
    names.discard(str(x))
    if len(names) > len(OTHER_VALUES):
        return None
    return {nm: mpmath.mpf(v) for nm, v in zip(sorted(names), OTHER_VALUES, strict=False)}


def _close(a: Number, b: Number, tol: Number = CLOSE) -> bool:
    return bool(abs(a - b) <= tol * (1 + abs(a) + abs(b)))


def _value(f: Fn, t: Number) -> Number | None:
    try:
        v = f(t)
    except Undefined, Overflow, ZeroDivisionError, ValueError:
        return None
    return v if mpmath.isfinite(v) else None


def _pointwise(
    what: str,
    expected: Callable[[Number], Number | None],
    got: Fn,
    tally: Tally,
    points: Sequence[float] = SAMPLES,
) -> None:
    compared = 0
    for p in points:
        t = mpmath.mpf(p)
        want = expected(t)
        have = _value(got, t)
        if want is None or have is None or not mpmath.isfinite(want):
            continue
        if not _close(want, have):
            raise Disagreement(
                f"{what}: SymPy and mpmath disagree at {p}: {mpmath.nstr(have, 10)} "
                f"(SymPy) against {mpmath.nstr(want, 10)} (mpmath)"
            )
        compared += 1
    if compared >= MIN_POINTS:
        tally.checked += 1
    else:
        tally.unverified += 1


def same_values(a: Any, b: Any) -> bool | None:
    """Do two SymPy values agree at sample points by our mpmath evaluator? None: can't tell."""
    with mp.workdps(DPS):
        symbols = sorted(
            getattr(a, "free_symbols", set()) | getattr(b, "free_symbols", set()), key=str
        )
        if not symbols:
            va, vb = _number(a), _number(b)
            if va is None or vb is None:
                return None
            return _close(va, vb)
        x = symbols[0]
        others = _others(a, b, x=x)
        fa = _function(a, x, others or {})
        fb = _function(b, x, others or {})
        if others is None or fa is None or fb is None:
            return None
        compared = 0
        for p in SAMPLES:
            t = mpmath.mpf(p)
            va, vb = _value(fa, t), _value(fb, t)
            if va is None or vb is None:
                continue
            if not _close(va, vb):
                return False
            compared += 1
        return True if compared >= MIN_POINTS else None


def check(name: str, f: Any, x: sympy.Symbol | None, args: Sequence[Any], result: Any,
          tally: Tally) -> None:  # fmt: skip
    """Cross-check one template operation. `args` are the evaluated extra arguments."""
    with mp.workdps(DPS):
        try:
            _check(name, f, x, args, result, tally)
        except Disagreement:
            raise
        except Exception:  # mpmath could not compute it: unverified, never a pass
            tally.unverified += 1


def _check(name: str, f: Any, x: sympy.Symbol | None, args: Sequence[Any], result: Any,
           tally: Tally) -> None:  # fmt: skip
    if x is None:  # simplify, expand, factor: any free symbol will do
        symbols = sorted(getattr(f, "free_symbols", set()), key=str)
        if not symbols:
            _constant(name, f, result, tally)
            return
        x = symbols[0]
    others = _others(f, result, *args, x=x)
    if others is None:
        tally.unverified += 1
        return
    if name == "solve":
        _solve(f, x, result, others, tally)
        return
    r = _function(result, x, others)
    if name == "limit":
        _limit(f, x, args, result, others, tally)
        return
    if name == "integrate" and len(args) == 2:
        _definite(f, x, args, result, others, tally)
        return
    fn = _function(f, x, others)
    if fn is None or r is None:
        tally.unverified += 1
        return
    if name == "diff":
        order = int(args[0]) if args else 1
        _pointwise("diff", lambda t: mp.diff(fn, t, order), r, tally)
    elif name == "integrate":
        _pointwise("integrate", lambda t: _value(fn, t), lambda t: mp.diff(r, t), tally)
    elif name == "subs":
        value = _function(args[0], x, others)
        if value is None:
            tally.unverified += 1
            return
        _pointwise("subs", lambda t: _value(fn, value(t)), r, tally)
    else:  # simplify, expand, factor
        _pointwise(name, lambda t: _value(fn, t), r, tally)


def _constant(name: str, f: Any, result: Any, tally: Tally) -> None:
    a, b = _node(f), _node(result)
    if a is None or b is None:
        tally.unverified += 1
        return
    try:
        va, vb = Evaluator()(a, {}), Evaluator()(b, {})
    except Undefined, Overflow:
        tally.unverified += 1
        return
    if not _close(va, vb):
        raise Disagreement(
            f"{name}: SymPy gives {mpmath.nstr(vb, 10)}, mpmath {mpmath.nstr(va, 10)}"
        )
    tally.checked += 1


def _number(value: Any) -> Number | None:
    if value is sympy.oo:
        return mpmath.inf
    if value is -sympy.oo:
        return -mpmath.inf
    node = _node(value)
    if node is None:
        return None
    try:
        return Evaluator()(node, {})
    except Undefined, Overflow:
        return None


def _definite(f: Any, x: sympy.Symbol, args: Sequence[Any], result: Any,
              others: Mapping[str, Number], tally: Tally) -> None:  # fmt: skip
    fn = _function(f, x, others)
    lo, hi, want = _number(args[0]), _number(args[1]), _number(result)
    if fn is None or lo is None or hi is None or want is None or others:
        tally.unverified += 1
        return
    value, err = mp.quad(fn, [lo, hi], error=True)
    if not mpmath.isfinite(value) or err > mpmath.mpf("1e-12") * (1 + abs(value)):
        tally.unverified += 1  # mp.quad isn't sure (a singular or oscillating integrand)
        return
    if not _close(value, want, max(CLOSE, 100 * err)):
        raise Disagreement(
            f"integrate: SymPy gives {mpmath.nstr(want, 10)}, mp.quad {mpmath.nstr(value, 10)}"
        )
    tally.checked += 1


def _limit(f: Any, x: sympy.Symbol, args: Sequence[Any], result: Any,
           others: Mapping[str, Number], tally: Tally) -> None:  # fmt: skip
    fn = _function(f, x, others)
    at = _number(args[0]) if args else None
    want = _number(result)
    if fn is None or at is None or want is None or others:
        tally.unverified += 1
        return
    side = str(args[1]) if len(args) > 1 else "+-"
    directions = [1] if side == "+" else [-1] if side == "-" else [1, -1]
    if mpmath.isinf(at):
        directions = [1]
    for d in directions:
        got = mpmath.limit(fn, at, direction=d) if mpmath.isfinite(at) else mpmath.limit(fn, at)
        if not mpmath.isfinite(got) or not mpmath.isfinite(want):
            tally.unverified += 1
            return
        if not _close(got, want, LIMIT_CLOSE):
            # Extrapolation can be off for slow approaches: look much closer before failing.
            near = (
                _value(fn, at + d * mpmath.mpf("1e-15"))
                if mpmath.isfinite(at)
                else _value(fn, mpmath.mpf("1e15") * mpmath.sign(at))
            )
            if near is not None and _close(near, want, mpmath.mpf("1e-4")):
                continue
            raise Disagreement(
                f"limit: SymPy gives {mpmath.nstr(want, 10)}, mpmath {mpmath.nstr(got, 10)}"
            )
    tally.checked += 1


def _solve(f: Any, x: sympy.Symbol, result: Any, others: Mapping[str, Number],
           tally: Tally) -> None:  # fmt: skip
    if others:
        tally.unverified += 1
        return
    if isinstance(f, sympy.core.relational.Relational) and not isinstance(f, sympy.Eq):
        _inequality(f, x, result, tally)
        return
    expr = f.lhs - f.rhs if isinstance(f, sympy.Eq) else f
    fn = _function(expr, x, {})
    if fn is None or not isinstance(result, sympy.FiniteSet | type(sympy.S.EmptySet)):
        tally.unverified += 1
        return
    found = [_number(s) for s in (result if isinstance(result, sympy.FiniteSet) else ())]
    roots = [r for r in found if r is not None]
    if len(roots) != len(found):
        tally.unverified += 1
        return
    for r in roots:
        v = _value(fn, r)
        scale = max((abs(w) for p in SAMPLES if (w := _value(fn, mpmath.mpf(p))) is not None),
                    default=mpmath.mpf(1))  # fmt: skip
        if v is None or abs(v) > mpmath.mpf("1e-15") * (1 + scale):
            raise Disagreement(f"solve: {mpmath.nstr(r, 10)} is not a solution (mpmath)")
    lo, hi, count = SCAN
    shift = mpmath.mpf(1) / 97  # off the round numbers, where a grid point could be a root
    grid = [lo + shift + (hi - lo) * mpmath.mpf(i) / (count - 1) for i in range(count)]
    values = [_value(fn, t) for t in grid]
    candidates: list[Number] = [t for t, v in zip(grid, values, strict=True) if v == 0]
    for (a, va), (b, vb) in itertools.pairwise(zip(grid, values, strict=True)):
        if va is None or vb is None or va == 0 or vb == 0 or (va > 0) == (vb > 0):
            continue
        try:
            root = mpmath.findroot(fn, (a, b), solver="anderson")
        except ValueError, ZeroDivisionError, Undefined, Overflow:
            continue
        rv = _value(fn, root)
        if rv is None or abs(rv) > mpmath.mpf("1e-10") * (1 + abs(va) + abs(vb)):
            continue  # a pole changes sign too
        candidates.append(root)
    for root in candidates:
        if not any(abs(root - r) <= mpmath.mpf("1e-8") * (1 + abs(root)) for r in roots):
            raise Disagreement(f"solve: SymPy misses a solution near {mpmath.nstr(root, 10)}")
    tally.checked += 1


def _inequality(f: Any, x: sympy.Symbol, result: Any, tally: Tally) -> None:
    lhs, rhs = _function(f.lhs, x, {}), _function(f.rhs, x, {})
    if lhs is None or rhs is None:
        tally.unverified += 1
        return
    ops = {sympy.StrictLessThan: "<", sympy.LessThan: "<=", sympy.StrictGreaterThan: ">",
           sympy.GreaterThan: ">="}  # fmt: skip
    op = ops.get(type(f))
    if op is None:
        tally.unverified += 1
        return
    compared = 0
    for p in SAMPLES:
        t = mpmath.mpf(p)
        a, b = _value(lhs, t), _value(rhs, t)
        if a is None or b is None or _close(a, b, mpmath.mpf("1e-9")):
            continue
        holds = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        inside = bool(result.contains(sympy.Rational(str(p))))
        if holds != inside:
            raise Disagreement(
                f"solve: at x = {p} the inequality is {holds}, SymPy's set says {inside}"
            )
        compared += 1
    if compared >= MIN_POINTS:
        tally.checked += 1
    else:
        tally.unverified += 1
