"""DEV-18: SymPy and our mpmath evaluator cross-check verdicts (core/grader/differential.py)."""

import mpmath
import pytest
import sympy

from core.grader import AnswerSpec, cross_check, differential
from core.grader.compare import _rational
from core.grader.parser import parse
from core.grader.shapes import shape_value
from core.grader.spec import resolve
from core.grader.symbolic import Deadline
from tests.grader.golden import load_cases


def test_exact_points_keep_their_sign() -> None:
    # Found by the differential check: man_exp drops the sign, so the symbolic tiny-
    # difference step (compare._tiny_difference) evaluated at |x| instead of x.
    assert _rational(mpmath.mpf(-2)) == -2
    assert _rational(mpmath.mpf("-0.75")) == sympy.Rational(-3, 4)


def _cross(raw: str, key: str, status: str) -> list[str]:
    card = resolve(AnswerSpec("expression", key))
    value = shape_value(parse(raw, card.vocab), "expression", [v for v, _ in card.variables])
    return differential.cross(card, value, status, Deadline(5.0))


def test_a_false_accept_is_reported() -> None:
    assert _cross("x^2 + 1", "x^2", "correct")
    assert _cross("x^2", "x^2", "correct") == []


def test_engines_that_disagree_are_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    real = differential._sympy
    monkeypatch.setattr(differential, "_sympy", lambda e, subs: (real(e, subs) or 0) + 1)
    problems = _cross("sin(x)", "sin(x)", "correct")
    assert any("the engines disagree" in p for p in problems)


def test_cross_check_api() -> None:
    assert cross_check("2sin(x)cos(x)", AnswerSpec("expression", "sin(2x)")) == ()
    assert cross_check("x^2 - 4", AnswerSpec("expression", "(x-2)(x+2)")) == ()


@pytest.mark.slow
def test_golden_suite_has_no_disagreements() -> None:
    """Every number and expression case of the golden suite: both engines agree with each
    other and with every correct verdict."""
    found: list[str] = []
    for case in load_cases():
        if case.spec.answer_type not in {"number", "expression"}:
            continue
        if case.expected not in {"correct", "incorrect"}:
            continue
        found += [f"{case.id}: {p}" for p in cross_check(case.raw, case.spec, case.source)]  # type: ignore[arg-type]
    assert found == []
