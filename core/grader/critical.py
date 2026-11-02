"""Critical points of answer trees: where a piecewise or partial expression changes.

Random sampling (compare.py) can miss a difference that lives only past a threshold
(`x + abs(x) - 45 + abs(abs(x) - 45)` equals x for |x| <= 45), inside a narrow band
(`abs(x - 0.7) < 0.001`), beyond a far domain boundary (`0*sqrt(1000 - x)`), or at a
single point (the hole in `(x^2-1)/(x-1)`). Between consecutive real zeros of every
abs()/sign() argument, domain-restricting argument and divisor, both expressions are
analytic, so a few points in each such region are good evidence; the zeros themselves
are where holes live. This module finds the zeros of an argument along one variable
(compare.py holds any others at a few sample points), with SymPy's solveset under a time
limit, falling back to a numeric scan when solveset gives up. Periodic zero sets give
their members near 0 only; the residual risks are listed in docs/decisions/0006.
"""

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

import mpmath
import sympy
from mpmath import mp

from core.grader import nodes as n
from core.grader.exact import exact_rational
from core.grader.symbolic import SymbolicTimeout, time_limit

MAX_ZEROS = 40  # per argument; more than this is a periodic set, left to sampling
MAX_MAGNITUDE = mpmath.mpf(10) ** 12
SCAN_POINTS = 400
PERIODIC_MEMBERS = range(-3, 4)


@dataclass(frozen=True, slots=True)
class Part:
    """A sub-expression whose zeros (or +-1 for arcsin-like) split the real line."""

    node: n.Node
    levels: tuple[int, ...]
    singular: bool  # a divisor: the whole expression is undefined where node = 0


def parts(node: n.Node) -> list[Part]:
    """The sub-expressions of a tree whose level sets are critical, parents first."""
    out: list[Part] = []
    for sub in n.walk(node):
        match sub:
            case n.Call("abs" | "sign" | "sqrt" | "ln" | "root", args):
                out.append(Part(args[0], (0,), False))
            case n.Call("log", args, base):
                out.append(Part(args[0], (0,), False))
                if base is not None and n.free_vars(base):
                    out.append(Part(base, (0, 1), False))
            case n.Call("arcsin" | "arccos" | "arcsec" | "arccsc", args):
                out.append(Part(args[0], (-1, 1), False))
            case n.Call("tan" | "sec", args):
                out.append(Part(n.Call("cos", args), (0,), True))  # undefined where cos = 0
            case n.Call("cot" | "csc", args):
                out.append(Part(n.Call("sin", args), (0,), True))
            case n.Product(factors):
                for op, f in factors:
                    if op == "/" and n.free_vars(f):
                        out.append(Part(f, (0,), True))
            case n.Power(base, exp) if n.free_vars(base) or n.free_vars(exp):
                q = exact_rational(exp)
                if q is not None and q.denominator == 1 and q > 0:
                    continue  # whole powers are analytic everywhere
                if n.free_vars(base):
                    out.append(Part(base, (0,), q is not None and q <= 0))
    return [p for p in out if n.free_vars(p.node)]


def finite_points(found: sympy.Set) -> list[sympy.Expr] | None:
    """The finite real points of a solveset result (zeros or interval ends), or None."""
    if isinstance(found, sympy.FiniteSet):
        return list(found.args)
    if isinstance(found, sympy.Interval):
        return [e for e in (found.start, found.end) if e.is_finite]
    if isinstance(found, sympy.Union):
        out: list[sympy.Expr] = []
        for arg in found.args:
            got = finite_points(arg)
            if got is None:
                return None
            out += got
        return out
    if found is sympy.EmptySet:
        return []
    if isinstance(found, sympy.ImageSet) and found.base_sets == (sympy.Integers,):
        # A periodic family (pi/2 + n*pi): its members near 0 are enough to test holes
        # and to cut the line; the far ones are left to sampling.
        (n_sym,) = found.lamda.variables
        return [found.lamda.expr.subs(n_sym, k) for k in PERIODIC_MEMBERS]
    return None  # ConditionSet, Complement, ...: unknown


def real_value(value: sympy.Expr, dps: int) -> mpmath.mpf | None:
    """A real SymPy number as an mpmath value at `dps` digits (None if not real/finite)."""
    try:
        approx = sympy.N(value, dps)
        re, im = approx.as_real_imag()
        if not re.is_Number or not im.is_Number or abs(im) > sympy.Float("1e-20"):
            return None
        out = mpmath.mpf(sympy.Float(re, dps)._mpf_)
    except TypeError, ValueError, AttributeError:
        return None
    if not mp.isfinite(out) or abs(out) > MAX_MAGNITUDE:
        return None
    return out


def dyadic(value: sympy.Expr) -> Fraction | None:
    """The value if it is a small rational that binary floating point holds exactly."""
    if not value.is_Rational:
        return None
    p, q = int(value.p), int(value.q)
    if q & (q - 1) or abs(p) >= 2**80 or q > 2**40:
        return None
    return Fraction(p, q)


def solve_zeros(expr: sympy.Expr, sym: sympy.Symbol, seconds: float) -> list[sympy.Expr] | None:
    """Real solutions of expr = 0 as exact SymPy numbers; None if unknown or infinite."""
    if seconds <= 0.02:
        return None
    try:
        with time_limit(seconds):
            found = sympy.solveset(expr, sym, domain=sympy.Reals)
            points = finite_points(found)
    except SymbolicTimeout, RecursionError, TypeError, ValueError, NotImplementedError:
        return None
    except Exception:  # SymPy raises many internal errors; unknown is the safe answer
        return None
    if points is None or len(points) > MAX_ZEROS:
        return None
    return points


def scan_zeros(f: Callable[[mpmath.mpf], mpmath.mpf | None]) -> list[mpmath.mpf]:
    """Approximate sign changes of f on a wide grid (fallback when solveset gives up)."""
    grid = sorted(
        {mpmath.mpf(i) / 4 for i in range(-200, 201)}
        | {s * mpmath.mpf(10) ** (k / 8) for k in range(16, 97) for s in (-1, 1)}
    )
    values = [(x, f(x)) for x in grid[: SCAN_POINTS * 2]]
    found: list[mpmath.mpf] = []
    for (x0, y0), (x1, y1) in itertools.pairwise(values):
        if y0 is None or y1 is None:
            if (y0 is None) != (y1 is None):
                found.append((x0 + x1) / 2)  # a domain edge: put a point on it
            continue
        if y0 == 0:
            found.append(x0)
        elif (y0 < 0) != (y1 < 0):
            lo, hi, ylo = x0, x1, y0
            for _ in range(60):
                mid = (lo + hi) / 2
                ym = f(mid)
                if ym is None or ym == 0:
                    lo = hi = mid
                    break
                if (ym < 0) == (ylo < 0):
                    lo, ylo = mid, ym
                else:
                    hi = mid
            found.append((lo + hi) / 2)
        if len(found) > MAX_ZEROS:
            return found[:MAX_ZEROS]
    return found


def region_values(criticals: list[mpmath.mpf]) -> list[mpmath.mpf]:
    """Sample values in every region the critical values cut the line into."""
    cs = sorted(set(criticals))
    if not cs:
        return []
    out: list[mpmath.mpf] = []
    for lo, hi in itertools.pairwise(cs):
        gap = hi - lo
        out += [lo + gap * t for t in (mpmath.mpf("0.5"), mpmath.mpf("0.137"), mpmath.mpf("0.861"))]
    for c in cs:
        nudge = mpmath.mpf("1e-6") * (1 + abs(c))
        out += [c - nudge, c + nudge]
    span = cs[-1] - cs[0]
    for w in (mpmath.mpf("0.5"), mpmath.mpf(3), 30 + 2 * span, 10 * (1 + abs(cs[0]) + span)):
        out.append(cs[0] - w)
    for w in (mpmath.mpf("0.5"), mpmath.mpf(3), 30 + 2 * span, 10 * (1 + abs(cs[-1]) + span)):
        out.append(cs[-1] + w)
    return out
