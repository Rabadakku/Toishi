"""Answer AST / SymPy objects -> plain answer syntax that our parser reads back.

Template instances store their computed keys as text, so `to_answer_syntax` must
round-trip: parse(to_answer_syntax(x)) translates back to an equal SymPy object.
Multiplication is always written explicitly, so the text never depends on the
implicit-multiplication rules.
"""

from collections.abc import Iterable
from fractions import Fraction
from typing import Any

from core.grader import nodes as n

_REL = {"=": "=", "<": "<", "<=": "<=", ">": ">", ">=": ">=", "!=": "!="}

# Binding strength: higher binds tighter.
_SUM, _PRODUCT, _NEG, _POWER, _ATOM = 1, 2, 3, 4, 5


def _level(node: n.Node) -> int:
    match node:
        case n.Sum():
            return _SUM
        case n.Product():
            return _PRODUCT
        case n.Neg():
            return _NEG
        case n.Power() | n.Degree():
            return _POWER
    return _ATOM


def to_text(node: n.Node) -> str:
    """One AST node as answer syntax."""
    match node:
        case n.Num(text):
            return text
        case n.Var(name):
            return name
        case n.Const(name):
            return name
        case n.Group(arg):
            return f"({to_text(arg)})"
        case n.Neg(arg):
            inner = to_text(arg)
            return f"-{inner}" if _level(arg) >= _PRODUCT else f"-({inner})"
        case n.Sum(terms):
            parts: list[str] = []
            for i, (op, t) in enumerate(terms):
                text = to_text(t)
                if _level(t) <= _SUM or (i > 0 and _level(t) == _NEG):
                    text = f"({text})"
                parts.append(text if i == 0 and op == "+" else f"{op} {text}" if i else f"-{text}")
            return " ".join(parts)
        case n.Product(factors):
            out = ""
            for i, (op, f) in enumerate(factors):
                text = to_text(f)
                needs = _level(f) <= _NEG if i else _level(f) <= _SUM
                if i and op == "/" and _level(f) == _PRODUCT:
                    needs = True
                if needs:
                    text = f"({text})"
                out = text if i == 0 else f"{out}{'/' if op == '/' else '*'}{text}"
            return out
        case n.Power(base, exp):
            b = to_text(base)
            if _level(base) < _ATOM:
                b = f"({b})"
            e = to_text(exp)
            if _level(exp) < _ATOM or isinstance(exp, n.Neg):
                e = f"({e})"
            return f"{b}^{e}"
        case n.Degree(arg):
            text = to_text(arg)
            return f"({text})°" if _level(arg) < _ATOM else f"{text}°"
        case n.Call(func, args, base):
            inner = ", ".join(to_text(a) for a in args)
            if func == "log" and base is not None:
                return f"log_{to_text(base)}({inner})"
            return f"{func}({inner})"
        case n.Chain(operands, ops):
            out = to_text(operands[0])
            for op, o in zip(ops, operands[1:], strict=True):
                out += f" {_REL[op]} {to_text(o)}"
            return out
        case n.Or(items):
            return " or ".join(to_text(i) for i in items)
        case n.And(items):
            return " and ".join(to_text(i) for i in items)
        case n.Tuple(items, left, right):
            return f"{left}{', '.join(to_text(i) for i in items)}{right}"
        case n.SetLit(items):
            return "{" + ", ".join(to_text(i) for i in items) + "}"
        case n.Vector(items):
            return "<" + ", ".join(to_text(i) for i in items) + ">"
        case n.Matrix(rows):
            return "[" + ", ".join("[" + ", ".join(to_text(x) for x in r) + "]" for r in rows) + "]"
        case n.Union(items):
            return " U ".join(to_text(i) for i in items)
        case n.Dne():
            return "DNE"
        case n.NoneSet():
            return "none"
    raise TypeError(f"can't serialize {node!r}")


def parsed_text(parsed: n.Parsed) -> str:
    return "; ".join(", ".join(to_text(i) for i in alt) for alt in parsed.alternatives)


def to_answer_syntax(value: Any) -> str:
    """Write a SymPy object (or a list/tuple of them) in the card answer syntax.

    Expressions, Eq, FiniteSet (a set: `a, b`), EmptySet (`none`), Interval and Union
    (interval notation), Tuple (a point), Matrix, and Python lists (a list). Raises
    ValueError for anything the syntax can't express (complex infinity, nan, Piecewise).
    """
    import sympy

    from core.grader.translate import TranslateError, from_sympy

    try:
        if isinstance(value, list):
            return ", ".join(to_answer_syntax(v) for v in value)
        if isinstance(value, int | Fraction):
            return to_text(from_sympy(sympy.Rational(value)))
        if isinstance(value, tuple | sympy.Tuple):
            return "(" + ", ".join(to_answer_syntax(v) for v in value) + ")"
        if isinstance(value, sympy.MatrixBase):
            rows = [[to_answer_syntax(x) for x in value.row(i)] for i in range(value.rows)]
            return "[" + ", ".join("[" + ", ".join(r) + "]" for r in rows) + "]"
        if value is sympy.S.EmptySet:
            return "none"
        if value is sympy.S.Reals:
            return "(-inf, inf)"
        if isinstance(value, sympy.FiniteSet):
            return ", ".join(to_answer_syntax(v) for v in _sorted(value.args))
        if isinstance(value, sympy.Interval):
            left = "[" if not value.left_open and value.start.is_finite else "("
            right = "]" if not value.right_open and value.end.is_finite else ")"
            return f"{left}{to_answer_syntax(value.start)}, {to_answer_syntax(value.end)}{right}"
        if isinstance(value, sympy.Union):
            return " U ".join(_interval_part(a) for a in value.args)
        return to_text(from_sympy(value))
    except TranslateError as exc:
        raise ValueError(str(exc)) from None


def _interval_part(value: Any) -> str:
    import sympy

    if isinstance(value, sympy.FiniteSet):
        return "{" + to_answer_syntax(value) + "}"
    return to_answer_syntax(value)


def _sorted(items: Iterable[Any]) -> list[Any]:
    import sympy

    return sorted(items, key=sympy.default_sort_key)
