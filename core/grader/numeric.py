"""Strict numeric evaluation of answer trees with mpmath.

Real mode follows real-valued calculus: any step that leaves the reals (the square root
of a negative, ln of a non-positive number, arcsin(2)) makes the whole value undefined,
even if a later step would come back (sqrt(x)^2 at x = -1). Odd roots of negatives are
real: root(-8, 3) = (-8)^(1/3) = -2. Complex mode (cards that enable i) uses principal
branches. Values too large to compare meaningfully raise Overflow, and that point is
skipped rather than judged.
"""

from collections.abc import Mapping
from fractions import Fraction

import mpmath
from mpmath import mp

from core.grader import nodes as n
from core.grader.exact import exact_rational

type Number = mpmath.mpf | mpmath.mpc

MAX_EXP_ARG = 100_000  # exp(x) beyond this is not compared
MAX_LOG10_MAGNITUDE = 200_000
MAX_TRIG_ARG = 10**8


class Undefined(Exception):
    """The expression has no (real) value at this point."""


class Overflow(Exception):
    """The value is too large to evaluate or compare; skip this point."""


class Evaluator:
    """Evaluate answer trees at one point. Not thread-safe (uses mpmath's global mp)."""

    def __init__(self, *, degrees: bool = False, complex_mode: bool = False) -> None:
        self.degrees = degrees
        self.complex_mode = complex_mode
        # Keyed by id(); the node is kept alive and checked so an id is never reused.
        self._exact_cache: dict[int, tuple[n.Node, Fraction | None]] = {}

    def __call__(self, node: n.Node, env: Mapping[str, Number]) -> Number:
        value = self._ev(node, env)
        return self._check(value)

    # ------------------------------------------------------------------ helpers
    def _check(self, value: Number) -> Number:
        if isinstance(value, mpmath.mpc):
            if self.complex_mode:
                if not (mp.isfinite(value.real) and mp.isfinite(value.imag)):
                    raise Undefined
                return value
            raise Undefined
        if not mp.isfinite(value):
            raise Undefined
        return value

    def _exact_of(self, node: n.Node) -> Fraction | None:
        hit = self._exact_cache.get(id(node))
        if hit is not None and hit[0] is node:
            return hit[1]
        value = exact_rational(node)
        self._exact_cache[id(node)] = (node, value)
        return value

    def _real(self, value: Number) -> mpmath.mpf:
        if isinstance(value, mpmath.mpc):
            raise Undefined
        return value

    # ------------------------------------------------------------------ evaluation
    def _ev(self, node: n.Node, env: Mapping[str, Number]) -> Number:
        ev = self._ev
        match node:
            case n.Num(text):
                return mpmath.mpf(text)
            case n.Var(name):
                return env[name]
            case n.Const(name):
                if name == "pi":
                    return +mp.pi
                if name == "e":
                    return +mp.e
                if name == "i" and self.complex_mode:
                    return mpmath.mpc(0, 1)
                raise Undefined
            case n.Group(arg):
                return ev(arg, env)
            case n.Neg(arg):
                return -ev(arg, env)
            case n.Degree(arg):
                value = ev(arg, env)
                return value if self.degrees else value * mp.pi / 180
            case n.Sum(terms):
                total: Number = mpmath.mpf(0)
                for op, t in terms:
                    v = ev(t, env)
                    total = total + v if op == "+" else total - v
                return self._check(total)
            case n.Product(factors):
                acc: Number = mpmath.mpf(1)
                for op, f in factors:
                    v = ev(f, env)
                    if op == "/":
                        if v == 0:
                            raise Undefined
                        acc = acc / v
                    else:
                        acc = acc * v
                return self._check(acc)
            case n.Power(base, exp):
                return self._power(base, exp, env)
            case n.Call(func, args, base):
                return self._call(func, args, base, env)
        raise Undefined

    def _magnitude_guard(self, b: Number, e: Number) -> None:
        if b == 0:
            return
        size = abs(e) * abs(mp.log10(abs(b)))
        if size > MAX_LOG10_MAGNITUDE:
            raise Overflow

    def _power(self, base: n.Node, exp: n.Node, env: Mapping[str, Number]) -> Number:
        b = self._ev(base, env)
        q = self._exact_of(exp)
        if self.complex_mode or isinstance(b, mpmath.mpc):
            e = self._ev(exp, env) if q is None else mpmath.mpf(q.numerator) / q.denominator
            if b == 0:
                if (isinstance(e, mpmath.mpc) and e.real <= 0) or (
                    not isinstance(e, mpmath.mpc) and e <= 0
                ):
                    raise Undefined
                return mpmath.mpf(0)
            self._magnitude_guard(b, abs(e))
            return self._check(mp.power(b, e))
        if q is not None:
            if q.denominator == 1:
                if b == 0 and q <= 0:
                    raise Undefined  # 0^0 is an indeterminate form, not 1
                self._magnitude_guard(b, abs(q.numerator))
                return self._check(mp.power(b, q.numerator))
            e_real = mpmath.mpf(q.numerator) / q.denominator
            if b == 0:
                if q > 0:
                    return mpmath.mpf(0)
                raise Undefined
            if b < 0:
                if q.denominator % 2 == 0:
                    raise Undefined
                self._magnitude_guard(b, e_real)
                sign = -1 if q.numerator % 2 else 1
                return self._check(sign * mp.power(-b, e_real))
            self._magnitude_guard(b, e_real)
            return self._check(mp.power(b, e_real))
        e = self._real(self._ev(exp, env))
        if b > 0:
            self._magnitude_guard(b, e)
            return self._check(mp.power(b, e))
        if b == 0:
            if e > 0:
                return mpmath.mpf(0)
            raise Undefined
        if e == mp.nint(e):
            self._magnitude_guard(b, e)
            return self._check(mp.power(b, int(mp.nint(e))))
        raise Undefined

    def _angle_in(self, x: Number) -> Number:
        return x * mp.pi / 180 if self.degrees else x

    def _angle_out(self, x: Number) -> Number:
        return x * 180 / mp.pi if self.degrees else x

    def _call(
        self, func: str, args: tuple[n.Node, ...], base: n.Node | None, env: Mapping[str, Number]
    ) -> Number:
        x = self._ev(args[0], env)
        cplx = self.complex_mode or isinstance(x, mpmath.mpc)
        if func in {"sin", "cos", "tan", "sec", "csc", "cot"}:
            a = self._angle_in(x)
            if abs(a) > MAX_TRIG_ARG:
                raise Overflow
            if func == "sin":
                return self._check(mp.sin(a))
            if func == "cos":
                return self._check(mp.cos(a))
            s, c = mp.sin(a), mp.cos(a)
            num, den = {"tan": (s, c), "sec": (1, c), "csc": (1, s), "cot": (c, s)}[func]
            if den == 0:
                raise Undefined
            return self._check(num / den)
        if func in {"arcsin", "arccos", "arcsec", "arccsc"}:
            if not cplx:
                if func in {"arcsin", "arccos"} and abs(x) > 1:
                    raise Undefined
                if func in {"arcsec", "arccsc"} and abs(x) < 1:
                    raise Undefined
            if func in {"arcsec", "arccsc"}:
                if x == 0:
                    raise Undefined
                x = 1 / x
            raw = mp.asin(x) if func in {"arcsin", "arccsc"} else mp.acos(x)
            return self._check(self._angle_out(raw))
        if func == "arctan":
            return self._check(self._angle_out(mp.atan(x)))
        if func == "arccot":
            return self._check(self._angle_out(mp.acot(x)))
        if func in {"sinh", "cosh", "tanh"}:
            if not cplx and abs(x) > MAX_EXP_ARG:
                raise Overflow
            return self._check({"sinh": mp.sinh, "cosh": mp.cosh, "tanh": mp.tanh}[func](x))
        if func == "exp":
            if (x.real if isinstance(x, mpmath.mpc) else x) > MAX_EXP_ARG:
                raise Overflow
            return self._check(mp.exp(x))
        if func in {"ln", "log"}:
            if x == 0 or (not cplx and x < 0):
                raise Undefined
            value = mp.ln(x)
            if func == "log":
                b = self._ev(base, env) if base is not None else mpmath.mpf(10)
                if b == 1 or b == 0 or (not cplx and b < 0):
                    raise Undefined
                value = value / mp.ln(b)
            return self._check(value)
        if func == "sqrt":
            if not cplx and x < 0:
                raise Undefined
            return self._check(mp.sqrt(x))
        if func == "root":
            q = self._exact_of(args[1])
            if q is None or q.denominator != 1 or q < 2:
                raise Undefined
            index = int(q)
            if cplx:
                return self._check(mp.root(x, index))
            if x < 0:
                if index % 2 == 0:
                    raise Undefined
                return self._check(-mp.root(-x, index))
            return self._check(mp.root(x, index))
        if func == "abs":
            return self._check(mpmath.mpf(abs(x)))
        if func == "sign" and not isinstance(x, mpmath.mpc):
            return mpmath.mpf(mp.sign(x))
        raise Undefined
