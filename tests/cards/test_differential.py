"""DEV-18: mpmath recomputes what SymPy computes for templates (core/cards/differential.py)."""

from fractions import Fraction

import pytest
import sympy

from core.cards import cas, differential
from core.cards import template as tp
from core.cards.differential import Disagreement, Tally

x = sympy.Symbol("x", real=True)


def run(name: str, f: object, args: list[object], result: object) -> Tally:
    tally = Tally()
    differential.check(name, f, x, args, result, tally)
    return tally


@pytest.mark.parametrize(
    ("name", "f", "args", "right", "wrong"),
    [
        ("diff", sympy.sin(x**2), [1], 2 * x * sympy.cos(x**2), x * sympy.cos(x**2)),  # chain rule
        ("diff", x**3, [2], 6 * x, 3 * x**2),
        ("integrate", x * sympy.exp(x), [], (x - 1) * sympy.exp(x), (x + 1) * sympy.exp(x)),
        ("integrate", x**2, [0, 3], sympy.Integer(9), sympy.Integer(8)),
        ("limit", sympy.sin(3 * x) / x, [0, "+-"], sympy.Integer(3), sympy.Integer(1)),
        ("limit", (1 + 1 / x) ** x, [sympy.oo, "+-"], sympy.E, sympy.Integer(1)),
        ("subs", x**2 + 1, [sympy.Integer(3)], sympy.Integer(10), sympy.Integer(9)),
        ("simplify", (x**2 - 1) / (x - 1), [], x + 1, x - 1),
        ("factor", x**2 - 4, [], (x - 2) * (x + 2), (x - 2) ** 2),
        ("solve", x**3 - x, [], sympy.FiniteSet(-1, 0, 1), sympy.FiniteSet(0, 1)),  # missed root
        ("solve", x**2 - 4, [], sympy.FiniteSet(-2, 2), sympy.FiniteSet(-2, 2, 3)),  # extra root
        ("solve", x**2 < 4, [], sympy.Interval.open(-2, 2), sympy.Interval.open(-2, 3)),
    ],
)
def test_mpmath_agrees_with_right_results_and_catches_wrong_ones(
    name: str, f: object, args: list[object], right: object, wrong: object
) -> None:
    assert run(name, f, args, right).checked == 1
    with pytest.raises(Disagreement):
        run(name, f, args, wrong)


def test_what_mpmath_cannot_recompute_is_unverified_not_passed() -> None:
    tally = run(
        "integrate", sympy.sin(1 / x) / x, [sympy.Rational(-1), sympy.Integer(1)], sympy.Integer(0)
    )
    assert (tally.checked, tally.unverified) == (0, 1)


def test_a_wrong_sympy_result_fails_the_template(monkeypatch: pytest.MonkeyPatch) -> None:
    job = tp.TemplateJob(
        template_id="t", file="t.cards.md", first_line=1, lines=(), slots=(),
        params=(tp.Param("k", "int", 1, Fraction(2), Fraction(3)),),
        lets=(tp.Definition("d", tp.compile_expr("diff(k*x^3, x)"), 1),),
    )  # fmt: skip
    good = cas.run(job, lambda kind, payload: None)
    assert good.error is None
    assert good.cross_checked == 2
    monkeypatch.setattr(sympy, "diff", lambda f, *a: f)  # a "derivative" that is wrong
    bad = cas.run(job, lambda kind, payload: None)
    assert bad.error is not None
    assert "disagree" in bad.error
