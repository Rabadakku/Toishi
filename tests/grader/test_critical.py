"""Critical points (core/grader/critical.py) and the precision-aware comparison.

Random sampling alone accepted answers that differ only past |x| = 45, inside a narrow
band, beyond a far domain edge or at a single hole; these pin the pieces that stop it.
"""

from collections.abc import Callable

import mpmath
import sympy
from mpmath import mp

from core.grader import AnswerSpec, Status, critical, grade
from core.grader import nodes as n
from core.grader.compare import Checker
from core.grader.parser import parse
from core.grader.spec import resolve


def tree(text: str, spec: AnswerSpec) -> n.Node:
    return parse(text, resolve(spec).vocab).alternatives[0][0]


def test_parts_cover_breakpoints_domain_edges_and_divisors() -> None:
    spec = AnswerSpec("expression", "x")
    node = tree("abs(abs(x) - 45) + sqrt(1000 - x) + 1/(x - 1) + tan(x) + arcsin(x/9)", spec)
    found = {(n.free_vars(p.node) == {"x"}, p.levels, p.singular) for p in critical.parts(node)}
    assert (True, (0,), False) in found  # abs and sqrt arguments
    assert (True, (-1, 1), False) in found  # arcsin argument
    assert (True, (0,), True) in found  # the divisor x - 1 and tan's cos(x)
    assert len(critical.parts(node)) == 6


def test_finite_points_reads_solveset_results() -> None:
    x = sympy.Symbol("x", real=True)
    assert critical.finite_points(sympy.FiniteSet(1, 2)) == [1, 2]
    assert critical.finite_points(sympy.Interval(0, sympy.oo)) == [0]
    assert critical.finite_points(sympy.EmptySet) == []
    periodic = sympy.solveset(sympy.cos(x), x, domain=sympy.Reals)
    members = critical.finite_points(periodic)
    assert members is not None
    assert sympy.pi / 2 in members
    assert -sympy.pi / 2 in members
    assert critical.finite_points(sympy.ConditionSet(x, sympy.Eq(x**x, 3), sympy.Reals)) is None


def test_scan_zeros_finds_sign_changes_and_domain_edges() -> None:
    def f(v: mpmath.mpf) -> mpmath.mpf | None:
        return None if v > 1000 else v**2 - 2

    found = critical.scan_zeros(f)
    # Approximate (bisection at the ambient precision): good enough to place points.
    assert any(abs(z - mp.sqrt(2)) < mpmath.mpf("1e-12") for z in found)
    assert any(abs(z + mp.sqrt(2)) < mpmath.mpf("1e-12") for z in found)
    assert any(900 < z < 1400 for z in found)  # the edge where f stops being defined


def test_extra_points_reach_every_region() -> None:
    spec = AnswerSpec("expression", "x")
    checker = Checker(resolve(spec))
    far = tree("x + abs(x) - 45 + abs(abs(x) - 45)", spec)
    xs = [p["x"] for p in checker._extra_points((far,), ("x",), [])]
    assert any(v > 45 for v in xs)
    assert any(v < -45 for v in xs)
    band = tree("x + 1/1000 - abs(x - 7/10) + abs(1/1000 - abs(x - 7/10))", spec)
    xs = [p["x"] for p in checker._extra_points((band,), ("x",), [])]
    assert any(mpmath.mpf("0.699") < v < mpmath.mpf("0.701") for v in xs)


def test_extra_points_respect_the_domain() -> None:
    spec = AnswerSpec("expression", "x", domain="x > 0")
    checker = Checker(resolve(spec))
    node = tree("abs(x - 45) + abs(x + 45)", spec)
    xs = [p["x"] for p in checker._extra_points((node,), ("x",), [])]
    assert xs
    assert all(v > 0 for v in xs)
    assert any(v > 45 for v in xs)


def test_agree_separates_rounding_noise_from_tiny_real_differences() -> None:
    checker = Checker(resolve(AnswerSpec("number", "0")))

    def value(f: Callable[[], mpmath.mpf]) -> Callable[[object, int], mpmath.mpf]:
        def at(env: object, dps: int) -> mpmath.mpf:
            with mp.workdps(dps):
                return f()

        return at

    zero = value(lambda: mpmath.mpf(0))
    assert checker._agree({}, value(lambda: mp.sin(mp.pi)), zero) is True  # noise
    assert checker._agree({}, value(lambda: mp.exp(-1000)), zero) is False
    tiny = value(lambda: mp.exp(-200))
    assert checker._agree({}, value(lambda: 2 * mp.exp(-200)), tiny) is False
    assert checker._agree({}, value(lambda: mp.exp(-200) * 1), tiny) is True


def test_a_hole_is_reported_where_it_is() -> None:
    # M7 (ADR-0019 item 10): a hole-only answer is invalid (no attempt), not incorrect.
    result = grade("(x^2-1)/(x-1)", AnswerSpec("expression", "x + 1"))
    assert result.status == Status.INVALID
    assert "x = 1" in result.message
    result = grade("y/x^2 = 1", AnswerSpec("equation", "y = x^2"))
    assert result.status == Status.INVALID
    assert "x = 0" in result.message
    assert "y = 0" in result.message


def test_holes_shared_with_the_key_are_fine() -> None:
    assert grade("x/x^2", AnswerSpec("expression", "1/x")).status == Status.CORRECT
    assert grade("sin(x)/cos(x)", AnswerSpec("expression", "tan(x)")).status == Status.CORRECT
    assert grade("x*y = 1", AnswerSpec("equation", "y = 1/x")).status == Status.CORRECT
    assert grade("y = 1/x", AnswerSpec("equation", "x*y = 1")).status == Status.CORRECT
    domain = AnswerSpec("expression", "x + 1", domain="x != 1")
    assert grade("(x^2-1)/(x-1)", domain).status == Status.CORRECT
