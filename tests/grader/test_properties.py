"""MATH-12 property tests: equivalent rewrites pass, perturbations fail, junk never breaks.

Keys are random polynomials, rational functions and trig expressions built with SymPy;
rewrites come from SymPy's own algebra (expand, factor, apart, ...) and reach the
checker as text through to_answer_syntax, exactly like template keys.
"""

import os
import time

import pytest
import sympy
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.grader import AnswerSpec, Status, grade, to_answer_syntax

x = sympy.Symbol("x", real=True)
pytestmark = pytest.mark.filterwarnings("ignore:Generating overly large repr")
# GRADER_EXAMPLES_SCALE=10 runs ten times as many examples (a deeper local run).
SCALE = max(1, int(os.environ.get("GRADER_EXAMPLES_SCALE", "1")))


def examples(count: int) -> settings:
    return settings(
        max_examples=count * SCALE,
        database=None,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    )


FAST = examples(40)

coeff = st.integers(-6, 6)
nonzero = coeff.filter(lambda c: c != 0)


@st.composite
def factored_polys(draw: st.DrawFn) -> sympy.Expr:
    lead = draw(nonzero)
    roots = draw(st.lists(st.integers(-5, 5), min_size=1, max_size=3))
    expr = sympy.Integer(lead)
    for r in roots:
        expr *= x - r
    if draw(st.booleans()):
        expr *= x**2 + draw(st.integers(1, 5))
    return expr


@st.composite
def rationals(draw: st.DrawFn) -> sympy.Expr:
    num = draw(factored_polys())
    den = (x - draw(st.integers(-4, 4))) * (x**2 + draw(st.integers(1, 4)))
    return num / den


TRIG_PAIRS = [
    (sympy.sin(2 * x), 2 * sympy.sin(x) * sympy.cos(x)),
    (sympy.cos(2 * x), 1 - 2 * sympy.sin(x) ** 2),
    (sympy.cos(2 * x), 2 * sympy.cos(x) ** 2 - 1),
    (sympy.tan(x), sympy.sin(x) / sympy.cos(x)),
    (sympy.sec(x) ** 2, 1 + sympy.tan(x) ** 2),
    (sympy.sin(x) ** 2, (1 - sympy.cos(2 * x)) / 2),
    (sympy.cos(x), sympy.sin(x + sympy.pi / 2)),
    (sympy.sin(3 * x), 3 * sympy.sin(x) - 4 * sympy.sin(x) ** 3),
]


def verdict(answer: sympy.Expr, key: sympy.Expr) -> Status:
    spec = AnswerSpec("expression", to_answer_syntax(key), vars=("x",))
    return grade(to_answer_syntax(answer), spec).status


# ------------------------------------------------------------------ equivalent rewrites pass


@FAST
@given(factored_polys())
def test_expanded_and_factored_agree(poly: sympy.Expr) -> None:
    expanded = sympy.expand(poly)
    assert verdict(expanded, poly) is Status.CORRECT
    assert verdict(poly, expanded) is Status.CORRECT


@FAST
@given(rationals())
def test_rational_rewrites_agree(expr: sympy.Expr) -> None:
    for rewrite in (sympy.apart(expr, x), sympy.together(expr), sympy.cancel(expr)):
        assert verdict(rewrite, expr) is Status.CORRECT, rewrite


@FAST
@given(st.sampled_from(TRIG_PAIRS), nonzero, st.integers(-4, 4))
def test_trig_identities_agree(pair: tuple[sympy.Expr, sympy.Expr], a: int, b: int) -> None:
    left, right = pair
    assert verdict(a * right + b, a * left + b) is Status.CORRECT


@FAST
@given(st.integers(2, 50).filter(lambda k: sympy.sqrt(k).is_irrational), nonzero)
def test_rationalized_forms_agree(k: int, b: int) -> None:
    expr = 1 / (sympy.sqrt(k) + b)
    rationalized = sympy.radsimp(expr)
    spec = AnswerSpec("number", to_answer_syntax(expr))
    assert grade(to_answer_syntax(rationalized), spec).status is Status.CORRECT


# ------------------------------------------------------------------ perturbations fail


@FAST
@given(factored_polys(), st.data())
def test_coefficient_off_by_one_fails(poly: sympy.Expr, data: st.DataObject) -> None:
    p = sympy.Poly(sympy.expand(poly), x)
    coeffs = p.all_coeffs()
    i = data.draw(st.integers(0, len(coeffs) - 1))
    delta = data.draw(st.sampled_from([-1, 1]))
    coeffs[i] += delta
    perturbed = sympy.Poly(coeffs, x).as_expr()
    assert verdict(perturbed, poly) is Status.INCORRECT, perturbed


@FAST
@given(factored_polys(), st.data())
def test_flipped_sign_fails(poly: sympy.Expr, data: st.DataObject) -> None:
    terms = sympy.Add.make_args(sympy.expand(poly))
    i = data.draw(st.integers(0, len(terms) - 1))
    flipped = sympy.Add(*[-t if j == i else t for j, t in enumerate(terms)])
    assert verdict(flipped, poly) is Status.INCORRECT, flipped


@FAST
@given(st.sampled_from(TRIG_PAIRS), nonzero, st.sampled_from([-1, 1]))
def test_trig_perturbations_fail(pair: tuple[sympy.Expr, sympy.Expr], a: int, d: int) -> None:
    left, right = pair
    assert verdict(a * right + d, a * left) is Status.INCORRECT
    assert verdict(-a * right, a * left) is Status.INCORRECT


@FAST
@given(rationals(), st.sampled_from([-1, 1]))
def test_rational_perturbations_fail(expr: sympy.Expr, d: int) -> None:
    num, den = sympy.fraction(expr)
    assert verdict((num + d) / den, expr) is Status.INCORRECT


# ------------------------------------------------------------------ junk never breaks

ALPHABET = "0123456789x+-*/^()[]{}|<>=,;. e pi sqrt sin ln log_2 abs DNE none inf U or C"
SPECS = [
    AnswerSpec("expression", "x^2 - 4"),
    AnswerSpec("number", "sqrt(2)/2"),
    AnswerSpec("interval", "(-inf, 0) U (2, inf)"),
    AnswerSpec("set", "-1, 0, 1"),
    AnswerSpec("equation", "y = 2x + 1"),
    AnswerSpec("antiderivative", "x^3/3 + C"),
    AnswerSpec("point", "(2, -4)"),
    AnswerSpec("matrix", "[[1, 2], [3, 4]]"),
    AnswerSpec("text", "concave up"),
]
WORDS = st.sampled_from(
    ["x", "2", "0.5", "+", "-", "*", "/", "^", "(", ")", "[", "]", "|", ",", "<", ">", "=",
     "sin", "ln", "sqrt", "root", "log_2", "e", "pi", "inf", "DNE", "none", "U", "or",
     "C", " ", "<=", "{", "}", "°", "10^9", "x^999"]
)  # fmt: skip


def _check(raw: str, spec: AnswerSpec, source: str = "text") -> None:
    start = time.monotonic()
    result = grade(raw, spec, source)  # type: ignore[arg-type]
    assert isinstance(result.status, Status)
    assert time.monotonic() - start < 2.5


@examples(150)
@given(st.text(alphabet=ALPHABET, max_size=60), st.sampled_from(SPECS))
def test_random_text_never_crashes(raw: str, spec: AnswerSpec) -> None:
    _check(raw, spec)


@examples(150)
@given(st.lists(WORDS, max_size=25).map("".join), st.sampled_from(SPECS))
def test_random_token_soup_never_crashes(raw: str, spec: AnswerSpec) -> None:
    _check(raw, spec)


@examples(80)
@given(st.text(max_size=80), st.sampled_from(SPECS[:3]))
def test_any_unicode_never_crashes(raw: str, spec: AnswerSpec) -> None:
    _check(raw, spec)


LATEX = st.sampled_from(
    ["\\frac", "{", "}", "x", "2", "\\sqrt", "[", "]", "\\left(", "\\right)", "\\left|", "\\right|",
     "^", "_", "\\sin", "\\ln", "\\log", "\\pi", "\\cdot", "+", "-", "\\placeholder{}", "\\infty",
     "\\cup", "\\begin{bmatrix}", "\\end{bmatrix}", "&", "\\\\", "\\text{or}", " ", "\\circ"]
)  # fmt: skip


@examples(150)
@given(st.lists(LATEX, max_size=25).map("".join), st.sampled_from(SPECS[:4]))
def test_random_latex_never_crashes(raw: str, spec: AnswerSpec) -> None:
    _check(raw, spec, "mathlive")
