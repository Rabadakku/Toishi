"""to_answer_syntax: SymPy -> answer text that parses back to the same object."""

import os

import pytest
import sympy
from hypothesis import given, settings
from hypothesis import strategies as st

from core.grader import AnswerSpec, Status, grade, to_answer_syntax
from core.grader import nodes as n
from core.grader.parser import parse
from core.grader.tokens import Vocabulary
from core.grader.translate import SympyContext, make_symbols, to_sympy

x, y = sympy.symbols("x y", real=True)
CTX = SympyContext(make_symbols((("x", "real"), ("y", "real"))))
VOCAB = Vocabulary(frozenset({"x", "y"}))


def back(text: str) -> sympy.Expr:
    node = parse(text, VOCAB).alternatives[0][0]
    if isinstance(node, n.Chain):
        return sympy.Eq(to_sympy(node.operands[0], CTX), to_sympy(node.operands[1], CTX))
    return to_sympy(node, CTX)


@pytest.mark.parametrize(
    ("expr", "text"),
    [
        (sympy.Integer(-3), "-3"),
        (sympy.Rational(-2, 3), "-2/3"),
        (sympy.sqrt(2) / 2, "sqrt(2)/2"),
        (sympy.pi / 4, "pi/4"),
        (sympy.E**2, "e^2"),
        (x**2 - 4, "x^2 - 4"),
        ((x - 2) * (x + 2), "(x - 2)*(x + 2)"),
        (sympy.sin(x) ** 2, "sin(x)^2"),
        (sympy.asin(x), "arcsin(x)"),
        (sympy.log(x), "ln(x)"),
        (sympy.log(x) / sympy.log(2), "ln(x)/ln(2)"),
        (sympy.exp(2 * x), "e^(2*x)"),
        (sympy.Abs(x - 1), "abs(x - 1)"),
        (sympy.real_root(x, 3), "root(x, 3)"),
        (1 / sympy.real_root(x, 3), "1/root(x, 3)"),
        (x / (x + 1), "x/(x + 1)"),
        (-x / 2, "-x/2"),
        (3 * x / (2 * y), "3*x/(2*y)"),
        (x ** (-2), "1/x^2"),
        (sympy.Eq(y, 2 * x + 1), "y = 2*x + 1"),
        (sympy.oo, "inf"),
        (-sympy.oo, "-inf"),
        (sympy.Float("0.125"), "0.125"),
        (sympy.Float("-2.5"), "-2.5"),
    ],
)
def test_expressions_round_trip(expr: sympy.Expr, text: str) -> None:
    assert to_answer_syntax(expr) == text
    if expr.is_infinite:
        return
    got = back(text)
    if expr.is_Float:
        assert got == sympy.Rational(str(expr))
    else:
        assert got == expr


@pytest.mark.parametrize(
    ("value", "text", "kind"),
    [
        (sympy.FiniteSet(1, -1, 0), "-1, 0, 1", "set"),
        (sympy.S.EmptySet, "none", "set"),
        ([1, 2, 3], "1, 2, 3", "list"),
        (sympy.Interval.Lopen(0, 1), "(0, 1]", "interval"),
        (
            sympy.Interval(-sympy.oo, 0, True, True) | sympy.Interval(2, sympy.oo, False, True),
            "(-inf, 0) U [2, inf)",
            "interval",
        ),
        (sympy.Interval(0, 1) | sympy.FiniteSet(3), "[0, 1] U {3}", "interval"),
        (sympy.S.Reals, "(-inf, inf)", "interval"),
        (sympy.Tuple(2, -4), "(2, -4)", "point"),
        ((sympy.Rational(1, 2), sympy.sqrt(3)), "(1/2, sqrt(3))", "point"),
        (sympy.Matrix([[1, 2], [3, 4]]), "[[1, 2], [3, 4]]", "matrix"),
    ],
)
def test_structures_round_trip(value: object, text: str, kind: str) -> None:
    assert to_answer_syntax(value) == text
    assert grade(text, AnswerSpec(kind, text)).status is Status.CORRECT


@pytest.mark.parametrize(
    "value",
    [sympy.zoo, sympy.nan, sympy.Piecewise((x, x > 0), (0, True)), sympy.Symbol("xy"),
     sympy.Function("f")(x), sympy.Integral(x, x), sympy.Symbol("e")],
)  # fmt: skip
def test_unwritable_values(value: object) -> None:
    with pytest.raises(ValueError, match=r"."):
        to_answer_syntax(value)


# Random expressions over a whitelist: the text must parse back to the identical object.
_leaves = st.sampled_from(
    [x, y, 2, -3, sympy.Rational(1, 2), sympy.Rational(-5, 7), sympy.pi, sympy.E, 10]
).map(lambda v: v if isinstance(v, sympy.Basic) else sympy.Integer(v))


def _extend(children: st.SearchStrategy[sympy.Expr]) -> st.SearchStrategy[sympy.Expr]:
    unary = st.sampled_from(
        [sympy.sin, sympy.cos, sympy.tan, sympy.exp, sympy.atan, sympy.Abs, sympy.sqrt, sympy.asin]
    )
    return st.one_of(
        st.tuples(children, children).map(lambda p: p[0] + p[1]),
        st.tuples(children, children).map(lambda p: p[0] * p[1]),
        st.tuples(children, children).map(lambda p: p[0] - p[1]),
        st.tuples(children, children.filter(lambda c: c != 0)).map(lambda p: p[0] / p[1]),
        st.tuples(children, st.integers(-3, 4)).map(lambda p: p[0] ** p[1]),
        st.tuples(unary, children).map(lambda p: p[0](p[1])),
        children.map(lambda c: sympy.log(sympy.Abs(c) + 1)),
    )


exprs = st.recursive(_leaves, _extend, max_leaves=8).filter(
    lambda e: (
        not e.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo, sympy.I)
        and not e.atoms(sympy.re, sympy.im, sympy.arg)
        and e.is_finite is not False
    )
)


POINTS = [{x: sympy.Rational(7, 10), y: sympy.Rational(13, 10)}, {x: -2, y: sympy.Rational(-2, 5)}]


def same_value(a: sympy.Expr, b: sympy.Expr) -> bool:
    """Equal at sample points to 25 digits (SymPy may rebuild Abs(1/y) as 1/Abs(y)). A point
    that is exactly a pole of either form is skipped: evalf(subs=) does not return zoo there
    but precision noise (1e137 vs 1e146 for 1/(2*x + 4) and 1/(2*(x + 2)) at x = -2), which
    differs between equal forms."""
    for point in POINTS:
        if any(e.subs(point).has(sympy.nan, sympy.zoo) for e in (a, b)):
            continue
        va, vb = a.evalf(30, subs=point), b.evalf(30, subs=point)
        if va.has(sympy.nan, sympy.zoo) or vb.has(sympy.nan, sympy.zoo):
            if va != vb:
                return False
            continue
        if abs(sympy.N(va - vb, 30)) > sympy.Float("1e-25") * (1 + abs(sympy.N(vb, 30))):
            return False
    return True


@pytest.mark.filterwarnings("ignore:Generating overly large repr")
@settings(
    max_examples=100 * max(1, int(os.environ.get("GRADER_EXAMPLES_SCALE", "1"))),
    database=None,
    deadline=None,
)
@given(exprs)
def test_random_expressions_round_trip(expr: sympy.Expr) -> None:
    text = to_answer_syntax(expr)
    got = back(text)
    assert got == expr or same_value(got, expr), text
