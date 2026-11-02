"""Exact rational values of constant answer trees (stdlib only: safe to import anywhere)."""

from fractions import Fraction

from core.grader import nodes as n

MAX_EXACT_EXPONENT = 10_000
MAX_EXACT_DIGITS = 2_000


def exact_rational(node: n.Node) -> Fraction | None:
    """The exact rational value of a constant tree, or None (irrational, variable, huge)."""
    try:
        return _exact(node)
    except ZeroDivisionError, OverflowError, ValueError:
        return None


def _exact(node: n.Node) -> Fraction | None:
    match node:
        case n.Num(text):
            return Fraction(text)
        case n.Group(arg):
            return _exact(arg)
        case n.Neg(arg):
            v = _exact(arg)
            return -v if v is not None else None
        case n.Sum(terms):
            total = Fraction(0)
            for op, t in terms:
                v = _exact(t)
                if v is None:
                    return None
                total = total + v if op == "+" else total - v
            return total
        case n.Product(factors):
            acc = Fraction(1)
            for op, f in factors:
                v = _exact(f)
                if v is None:
                    return None
                acc = acc / v if op == "/" else acc * v
            return acc
        case n.Power(base, exp):
            b, e = _exact(base), _exact(exp)
            if b is None or e is None or e.denominator != 1:
                return None
            if abs(e) > MAX_EXACT_EXPONENT:
                return None
            if b != 0 and abs(e) * max(len(str(b.numerator)), len(str(b.denominator))) > (
                MAX_EXACT_DIGITS
            ):
                return None
            return b ** int(e)
    return None
