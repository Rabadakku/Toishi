"""Whitelist translation between the answer AST and SymPy (MATH-8).

`to_sympy` builds SymPy objects node by node from our own tree; no string ever reaches
SymPy. `from_sympy` goes back (used by the serializer and by checks that need SymPy's
algebra, such as clearing denominators). Both raise TranslateError on anything outside
the whitelist.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

import sympy

from core.grader import nodes as n
from core.grader.exact import exact_rational
from core.grader.tokens import is_variable_name

MAX_NUMERIC_POWER_DIGITS = 5_000


class TranslateError(Exception):
    """Can't translate (outside the whitelist, undefined, or too large)."""


_ASSUMPTIONS: dict[str, dict[str, bool]] = {
    "real": {"real": True},
    "positive": {"positive": True},
    "negative": {"negative": True},
    "nonnegative": {"nonnegative": True},
    "nonpositive": {"nonpositive": True},
    "integer": {"integer": True},
    "complex": {},
}

_TRIG = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "sec": sympy.sec,
    "csc": sympy.csc,
    "cot": sympy.cot,
}
_INVERSE = {
    "arcsin": sympy.asin,
    "arccos": sympy.acos,
    "arctan": sympy.atan,
    "arcsec": sympy.asec,
    "arccsc": sympy.acsc,
    "arccot": sympy.acot,
}
_HYPERBOLIC = {"sinh": sympy.sinh, "cosh": sympy.cosh, "tanh": sympy.tanh}


@dataclass(frozen=True, slots=True)
class SympyContext:
    symbols: Mapping[str, sympy.Symbol]
    degrees: bool = False
    complex_mode: bool = False


def make_symbols(
    variables: tuple[tuple[str, str], ...], extra: tuple[str, ...] = ()
) -> dict[str, sympy.Symbol]:
    out = {name: sympy.Symbol(name, **_ASSUMPTIONS[a]) for name, a in variables}
    for name in extra:
        out.setdefault(name, sympy.Symbol(name, real=True))
    return out


def _number(text: str) -> sympy.Rational:
    if "E" in text:  # e-notation
        q = Fraction(text)
        return sympy.Rational(q.numerator, q.denominator)
    whole, _, frac = text.partition(".")
    digits = int((whole or "0") + frac)
    return sympy.Rational(digits, 10 ** len(frac))


def _check_power_size(b: sympy.Expr, e: sympy.Expr) -> None:
    if b.is_Rational and e.is_Integer and b not in (0, 1, -1):
        num_digits = max(len(str(abs(b.p))), len(str(b.q)))
        if abs(int(e)) * num_digits > MAX_NUMERIC_POWER_DIGITS:
            raise TranslateError("number too large")


def to_sympy(node: n.Node, ctx: SympyContext) -> sympy.Expr:
    """Translate a scalar answer tree. Raises TranslateError."""
    try:
        result = _to(node, ctx)
    except (TypeError, ValueError, ZeroDivisionError, RecursionError) as exc:
        raise TranslateError(str(exc)) from None
    if result.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo):
        raise TranslateError("undefined")
    return result


def _to(node: n.Node, ctx: SympyContext) -> sympy.Expr:
    to = _to
    match node:
        case n.Num(text):
            return _number(text)
        case n.Var(name):
            if name not in ctx.symbols:
                raise TranslateError(f"unknown variable {name}")
            return ctx.symbols[name]
        case n.Const("pi"):
            return sympy.pi
        case n.Const("e"):
            return sympy.E
        case n.Const("i") if ctx.complex_mode:
            return sympy.I
        case n.Group(arg):
            return to(arg, ctx)
        case n.Neg(arg):
            return -to(arg, ctx)
        case n.Degree(arg):
            value = to(arg, ctx)
            return value if ctx.degrees else value * sympy.pi / 180
        case n.Sum(terms):
            return sympy.Add(*[to(t, ctx) if op == "+" else -to(t, ctx) for op, t in terms])
        case n.Product(factors):
            parts = []
            for op, f in factors:
                v = to(f, ctx)
                parts.append(sympy.Pow(v, -1) if op == "/" else v)
            return sympy.Mul(*parts)
        case n.Power(base, exp):
            b = to(base, ctx)
            q = exact_rational(exp)
            if q is not None and q.denominator > 1 and q.denominator % 2 and not ctx.complex_mode:
                # Real odd root: (-8)^(1/3) = -2, as in real-valued calculus.
                p, r = q.numerator, sympy.Rational(q.numerator, q.denominator)
                return sympy.Mul(sympy.Pow(sympy.sign(b), p % 2 or 2), sympy.Pow(sympy.Abs(b), r))
            e = sympy.Rational(q.numerator, q.denominator) if q is not None else to(exp, ctx)
            if b == 0 and e == 0:
                raise TranslateError("0^0 is undefined")  # SymPy would make it 1
            _check_power_size(b, e)
            return sympy.Pow(b, e)
        case n.Call(func, args, base):
            return _call(func, args, base, ctx)
    raise TranslateError(f"can't translate {type(node).__name__}")


def _call(
    func: str, args: tuple[n.Node, ...], base: n.Node | None, ctx: SympyContext
) -> sympy.Expr:
    x = _to(args[0], ctx)
    deg = sympy.pi / 180
    if func in _TRIG:
        return _TRIG[func](x * deg if ctx.degrees else x)
    if func in _INVERSE:
        value = _INVERSE[func](x)
        return value / deg if ctx.degrees else value
    if func in _HYPERBOLIC:
        return _HYPERBOLIC[func](x)
    if func == "ln":
        return sympy.log(x)
    if func == "log":
        b = _to(base, ctx) if base is not None else sympy.Integer(10)
        return sympy.log(x) / sympy.log(b)
    if func == "exp":
        return sympy.exp(x)
    if func == "sqrt":
        return sympy.sqrt(x)
    if func == "abs":
        return sympy.Abs(x)
    if func == "sign":
        return sympy.sign(x)
    if func == "root":
        q = exact_rational(args[1])
        if q is None or q.denominator != 1 or q < 2:
            raise TranslateError("root index must be a whole number >= 2")
        k = int(q)
        if k % 2 and not ctx.complex_mode:
            return sympy.sign(x) * sympy.Abs(x) ** sympy.Rational(1, k)
        return sympy.Pow(x, sympy.Rational(1, k))
    raise TranslateError(f"unknown function {func}")


# ---------------------------------------------------------------------- SymPy -> AST


def _num(value: int | Fraction) -> n.Node:
    frac = Fraction(value)
    node: n.Node = n.Num(str(abs(frac.numerator)))
    if frac.denominator != 1:
        node = n.Product((("*", node), ("/", n.Num(str(frac.denominator)))))
    return n.Neg(node) if frac < 0 else node


def _float_text(value: sympy.Float) -> n.Node:
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".") or "0"
    negative = text.startswith("-")
    text = text.lstrip("-")
    if "." in text:
        whole, frac = text.split(".")
        text = f"{int(whole)}.{frac}"
    node: n.Node = n.Num(text)
    return n.Neg(node) if negative else node


_FROM_FUNCS = {
    sympy.sin: "sin",
    sympy.cos: "cos",
    sympy.tan: "tan",
    sympy.sec: "sec",
    sympy.csc: "csc",
    sympy.cot: "cot",
    sympy.asin: "arcsin",
    sympy.acos: "arccos",
    sympy.atan: "arctan",
    sympy.asec: "arcsec",
    sympy.acsc: "arccsc",
    sympy.acot: "arccot",
    sympy.sinh: "sinh",
    sympy.cosh: "cosh",
    sympy.tanh: "tanh",
    sympy.Abs: "abs",
    sympy.sign: "sign",
}


def from_sympy(expr: sympy.Basic) -> n.Node:
    """SymPy expression -> answer AST. Raises TranslateError outside the whitelist."""
    if isinstance(expr, bool | int):
        return _num(int(expr))
    if expr is sympy.oo:
        return n.Const("inf")
    if expr is sympy.S.NegativeInfinity:
        return n.Neg(n.Const("inf"))
    if expr.is_Integer:
        return _num(int(expr))
    if expr.is_Rational:
        return _num(Fraction(int(expr.p), int(expr.q)))
    if expr.is_Float:
        return _float_text(expr)
    if expr is sympy.pi:
        return n.Const("pi")
    if expr is sympy.E:
        return n.Const("e")
    if expr is sympy.I:
        return n.Const("i")
    if expr.is_Symbol:
        if not is_variable_name(expr.name) or expr.name in {"e", "U"}:
            raise TranslateError(f"symbol name {expr.name!r} isn't valid in answers")
        return n.Var(expr.name)
    if isinstance(expr, sympy.Equality):
        return n.Chain((from_sympy(expr.lhs), from_sympy(expr.rhs)), ("=",))
    if expr.is_Add:
        return _from_add(expr)
    if expr.is_Mul:
        return _from_mul(expr)
    if expr.is_Pow:
        return _from_pow(expr.base, expr.exp)
    if isinstance(expr, sympy.exp):
        return n.Power(n.Const("e"), from_sympy(expr.args[0]))
    if isinstance(expr, sympy.log):
        if len(expr.args) != 1:
            raise TranslateError("log with base")
        return n.Call("ln", (from_sympy(expr.args[0]),))
    for cls, name in _FROM_FUNCS.items():
        if isinstance(expr, cls):
            return n.Call(name, (from_sympy(expr.args[0]),))
    raise TranslateError(f"can't write {type(expr).__name__} in answer syntax")


def _from_add(expr: sympy.Expr) -> n.Node:
    terms: list[tuple[str, n.Node]] = []
    for t in expr.as_ordered_terms():
        coeff = t.as_coeff_Mul()[0]
        if terms and coeff.is_negative:
            terms.append(("-", from_sympy(-t)))
        else:
            terms.append(("+", from_sympy(t)))
    return n.Sum(tuple(terms))


def _from_mul(expr: sympy.Expr) -> n.Node:
    coeff, rest = expr.as_coeff_Mul()
    if coeff.is_negative:
        return n.Neg(from_sympy(-expr))
    num: list[n.Node] = []
    den: list[n.Node] = []
    if coeff != 1:
        frac = Fraction(int(coeff.p), int(coeff.q)) if coeff.is_Rational else None
        if frac is not None:
            if frac.numerator != 1:
                num.append(n.Num(str(frac.numerator)))
            if frac.denominator != 1:
                den.append(n.Num(str(frac.denominator)))
        else:
            num.append(from_sympy(coeff))
    factors = list(sympy.Mul.make_args(rest))
    for s in [f for f in factors if _sign_of(f) is not None]:
        # sign(b)^(+-1) * Abs(b)^(p/q) with p, q odd is the real root root(b, q)^p.
        base, power = _sign_of(s)  # type: ignore[misc]
        match = next(
            (
                f
                for f in factors
                if f.is_Pow
                and isinstance(f.base, sympy.Abs)
                and f.base.args[0] == base
                and f.exp.is_Rational
                and f.exp.q % 2 == 1
                and f.exp.p % 2 == 1
                and (f.exp > 0) == (power > 0)
            ),
            None,
        )
        if match is not None:
            factors.remove(s)
            factors.remove(match)
            factors.append(_RealRoot(base, match.exp))
    for f in factors:
        if isinstance(f, _RealRoot):
            node = f.node()
            (den if f.negative else num).append(node)
        elif f.is_Pow and f.exp.is_negative and f.exp.is_Rational:
            den.append(_from_pow(f.base, -f.exp))
        else:
            num.append(from_sympy(f))
    if not num:
        num.append(n.Num("1"))
    parts: list[tuple[str, n.Node]] = [("*", _factor(num[0]))]
    parts += [("*", _factor(x)) for x in num[1:]]
    if len(den) == 1:
        parts.append(("/", _factor(den[0], divisor=True)))
    elif den:
        grouped = n.Product(tuple(("*", _factor(x)) for x in den))
        parts.append(("/", n.Group(grouped)))
    if len(parts) == 1:
        return parts[0][1]
    return n.Product(tuple(parts))


def _sign_of(f: sympy.Expr) -> tuple[sympy.Expr, int] | None:
    """sign(b) -> (b, 1); 1/sign(b) -> (b, -1); anything else -> None."""
    if isinstance(f, sympy.sign):
        return f.args[0], 1
    if f.is_Pow and isinstance(f.base, sympy.sign) and f.exp in (1, -1):
        return f.base.args[0], int(f.exp)
    return None


class _RealRoot:
    def __init__(self, base: sympy.Expr, exp: sympy.Rational) -> None:
        self.base = base
        self.negative = bool(exp < 0)
        self.p = abs(int(exp.p))
        self.q = int(exp.q)

    def node(self) -> n.Node:
        root = n.Call("root", (from_sympy(self.base), n.Num(str(self.q))))
        return root if self.p == 1 else n.Power(root, n.Num(str(self.p)))


def _factor(node: n.Node, divisor: bool = False) -> n.Node:
    if isinstance(node, n.Sum | n.Neg) or (divisor and isinstance(node, n.Product)):
        return n.Group(node)
    return node


def _from_pow(base: sympy.Expr, exp: sympy.Expr) -> n.Node:
    if exp == 1:
        return from_sympy(base)
    if exp == sympy.Rational(1, 2):
        return n.Call("sqrt", (from_sympy(base),))
    if exp.is_Rational and exp.is_negative:
        inner = _from_pow(base, -exp)
        return n.Product((("*", n.Num("1")), ("/", _factor(inner, divisor=True))))
    b = from_sympy(base)
    if not isinstance(b, n.Num | n.Var | n.Const | n.Call):
        b = n.Group(b)
    e = from_sympy(exp)
    if not isinstance(e, n.Num | n.Var | n.Const):
        e = n.Group(e)
    return n.Power(b, e)
