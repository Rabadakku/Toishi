"""Canonical sets of real numbers: unions merged, intersections taken, endpoints numeric.

Endpoints are evaluated at 120 digits and compared to 1e-100 (relative, with a floor of
1e-115 for endpoints at 0), so `sqrt(8)` and `2sqrt(2)` are the same endpoint while
`1.414`, `99/70` and `sqrt(2) + 10^(-40)` are not `sqrt(2)` ("endpoints compared exactly").
"""

from dataclasses import dataclass, replace
from fractions import Fraction

import mpmath
from mpmath import mp

from core.grader import nodes as n
from core.grader.exact import exact_rational
from core.grader.numeric import Evaluator, Overflow, Undefined
from core.grader.shapes import Intervals, Piece, SetExpr, SetOp

ENDPOINT_DPS = 120
ENDPOINT_RELATIVE = mpmath.mpf("1e-100")
ENDPOINT_FLOOR = mpmath.mpf("1e-15")  # times ENDPOINT_RELATIVE: rounding of a zero endpoint


class BadEndpoint(Exception):
    """An endpoint has no real value (e.g. ln(-1))."""


@dataclass(frozen=True, slots=True)
class Iv:
    lo: mpmath.mpf | None  # None = -inf
    hi: mpmath.mpf | None  # None = +inf
    lo_closed: bool
    hi_closed: bool
    lo_q: Fraction | None = None  # exact value when the endpoint is rational
    hi_q: Fraction | None = None


def same_endpoint(a: mpmath.mpf | None, b: mpmath.mpf | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(abs(a - b) <= ENDPOINT_RELATIVE * max(ENDPOINT_FLOOR, abs(a), abs(b)))


def _lt(a: mpmath.mpf | None, b: mpmath.mpf | None, a_is_lo: bool, b_is_lo: bool) -> bool:
    """a < b, where None means -inf for a low endpoint and +inf for a high one."""
    if a is None:
        return a_is_lo and not (b is None and b_is_lo)
    if b is None:
        return not b_is_lo
    return bool(a < b) and not same_endpoint(a, b)


def _valid(iv: Iv) -> bool:
    if iv.lo is None or iv.hi is None:
        return True
    if same_endpoint(iv.lo, iv.hi):
        return iv.lo_closed and iv.hi_closed
    return bool(iv.lo < iv.hi)


def merge(ivs: list[Iv]) -> list[Iv]:
    ivs = [iv for iv in ivs if _valid(iv)]
    ivs.sort(
        key=lambda iv: (iv.lo is not None, iv.lo if iv.lo is not None else 0, not iv.lo_closed)
    )
    out: list[Iv] = []
    for iv in ivs:
        if not out:
            out.append(iv)
            continue
        cur = out[-1]
        touching = (
            cur.hi is not None
            and iv.lo is not None
            and same_endpoint(cur.hi, iv.lo)
            and (cur.hi_closed or iv.lo_closed)
        )
        overlapping = cur.hi is None or (iv.lo is None) or _lt(iv.lo, cur.hi, True, False)
        if touching or overlapping:
            if _lt(cur.hi, iv.hi, False, False):
                hi, hi_closed, hi_q = iv.hi, iv.hi_closed, iv.hi_q
            elif same_endpoint(cur.hi, iv.hi):
                hi, hi_closed, hi_q = cur.hi, cur.hi_closed or iv.hi_closed, cur.hi_q
            else:
                hi, hi_closed, hi_q = cur.hi, cur.hi_closed, cur.hi_q
            out[-1] = replace(cur, hi=hi, hi_closed=hi_closed, hi_q=hi_q)
        else:
            out.append(iv)
    return out


def _intersect2(a: Iv, b: Iv) -> Iv:
    if _lt(a.lo, b.lo, True, True):
        lo, lo_closed, lo_q = b.lo, b.lo_closed, b.lo_q
    elif same_endpoint(a.lo, b.lo):
        lo, lo_closed, lo_q = a.lo, a.lo_closed and b.lo_closed, a.lo_q
    else:
        lo, lo_closed, lo_q = a.lo, a.lo_closed, a.lo_q
    if _lt(a.hi, b.hi, False, False):
        hi, hi_closed, hi_q = a.hi, a.hi_closed, a.hi_q
    elif same_endpoint(a.hi, b.hi):
        hi, hi_closed, hi_q = a.hi, a.hi_closed and b.hi_closed, a.hi_q
    else:
        hi, hi_closed, hi_q = b.hi, b.hi_closed, b.hi_q
    return Iv(lo, hi, lo_closed, hi_closed, lo_q, hi_q)


def intersect(a: list[Iv], b: list[Iv]) -> list[Iv]:
    return merge([_intersect2(x, y) for x in a for y in b])


def canonical(expr: SetExpr, ev: Evaluator, *, either: bool = False) -> list[Iv]:
    """Evaluate a set expression to merged intervals.

    With `either` (endpoints: either), the set is merged with the brackets as typed and
    only then are the remaining finite endpoints opened. Closing them first, as before,
    merged (-inf, 0) U (0, inf) into (-inf, inf), so "where is 1/x decreasing?" accepted
    (-inf, inf), and [-1, 1) U (1, 3] passed for [-1, 3]: a point inside the set is not
    an endpoint, and its bracket still matters. Single points ([2, 2]) stay as they are.
    """
    with mp.workdps(ENDPOINT_DPS):
        ivs = _canon(expr, ev)
    if either:
        ivs = [
            iv
            if iv.lo is not None and iv.hi is not None and same_endpoint(iv.lo, iv.hi)
            else replace(iv, lo_closed=False, hi_closed=False)
            for iv in ivs
        ]
    return ivs


def _value(node: n.Node | None, ev: Evaluator) -> mpmath.mpf | None:
    if node is None:
        return None
    try:
        value = ev(node, {})
    except Undefined, Overflow:
        raise BadEndpoint from None
    if isinstance(value, mpmath.mpc):
        raise BadEndpoint
    return value


def _canon(expr: SetExpr, ev: Evaluator) -> list[Iv]:
    if isinstance(expr, Piece):
        lo_q = exact_rational(expr.lo) if expr.lo is not None else None
        hi_q = exact_rational(expr.hi) if expr.hi is not None else None
        iv = Iv(
            _value(expr.lo, ev), _value(expr.hi, ev), expr.lo_closed, expr.hi_closed, lo_q, hi_q
        )
        return merge([iv])
    parts = [_canon(x, ev) for x in expr.items]
    if expr.op == "union":
        return merge([iv for p in parts for iv in p])
    result = parts[0] if parts else [Iv(None, None, False, False)]
    for p in parts[1:]:
        result = intersect(result, p)
    return result


def _same_exact(
    a: mpmath.mpf | None, b: mpmath.mpf | None, qa: Fraction | None, qb: Fraction | None
) -> bool:
    if qa is not None and qb is not None:
        return qa == qb
    return same_endpoint(a, b)


def equal(a: list[Iv], b: list[Iv]) -> bool:
    return len(a) == len(b) and all(
        _same_exact(x.lo, y.lo, x.lo_q, y.lo_q)
        and _same_exact(x.hi, y.hi, x.hi_q, y.hi_q)
        and (x.lo is None or x.lo_closed == y.lo_closed)
        and (x.hi is None or x.hi_closed == y.hi_closed)
        for x, y in zip(a, b, strict=True)
    )


def describe(ivs: list[Iv]) -> str:
    if not ivs:
        return "none"
    parts = []
    for iv in ivs:
        lo = "-inf" if iv.lo is None else mpmath.nstr(iv.lo, 8)
        hi = "inf" if iv.hi is None else mpmath.nstr(iv.hi, 8)
        parts.append(f"{'[' if iv.lo_closed else '('}{lo}, {hi}{']' if iv.hi_closed else ')'}")
    return " U ".join(parts)


def condition_set(cond: n.Node, var: str, ev: Evaluator) -> list[Iv] | None:
    """The set where a one-variable domain condition holds, or None if it isn't one."""
    from core.grader import errors
    from core.grader.shapes import shape_value

    if n.free_vars(cond) != {var}:
        return None
    try:
        value = shape_value(n.Parsed(((cond,),)), "interval", (var,))
    except errors.InputError:
        return None
    if not isinstance(value, Intervals):
        return None
    try:
        return canonical(value.expr, ev)
    except BadEndpoint:
        return None


EMPTY_OP = SetOp("union", ())
