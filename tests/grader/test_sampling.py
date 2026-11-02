"""Sampling (pipeline step 3): points inside the domain, at least one per connected piece."""

from mpmath import mp

from core.grader import AnswerSpec
from core.grader.compare import POINTS_PER_VAR, Checker
from core.grader.parser import parse
from core.grader.spec import resolve


def points(key: str, *names: str, **opts: object) -> list[dict[str, mp.mpf]]:
    spec = AnswerSpec("expression", key, **opts)  # type: ignore[arg-type]
    card = resolve(spec)
    node = parse(key, card.vocab).alternatives[0][0]
    got = Checker(card).points_for(node, names or ("x",))
    assert got is not None
    return got


def test_twelve_points_per_variable() -> None:
    assert len(points("x^2")) == POINTS_PER_VAR
    assert len(points("x*y", "x", "y")) == 2 * POINTS_PER_VAR


def test_every_piece_gets_a_point() -> None:
    xs = [p["x"] for p in points("sqrt(x^2 - 4)")]
    assert any(v < -2 for v in xs)
    assert any(v > 2 for v in xs)
    assert all(abs(v) >= 2 for v in xs)


def test_points_stay_inside_the_card_domain() -> None:
    xs = [p["x"] for p in points("1/x", domain="x != 0")]
    assert any(v < 0 for v in xs)
    assert any(v > 0 for v in xs)
    xs = [p["x"] for p in points("ln(x)", domain="1 < x <= 3")]
    assert all(1 < v <= 3 for v in xs)


def test_assumptions_shape_the_pools() -> None:
    assert all(p["t"] > 0 for p in points("t", "t", vars=("t positive",)))
    ns = [p["n"] for p in points("n", "n", vars=("n integer",))]
    assert all(v == int(v) for v in ns)
    assert len(set(ns)) == len(ns)


def test_multi_variable_conditions_filter_points() -> None:
    for p in points("sqrt(x - y)", "x", "y", vars=("x", "y"), domain="x > y"):
        assert p["x"] > p["y"]


def test_sampling_is_deterministic() -> None:
    assert points("sin(x)") == points("sin(x)")
