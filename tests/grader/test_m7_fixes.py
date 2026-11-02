"""M7 answer-checker fixes from the full evidence review (ADR-0019 items 10 and 11).

Each test here failed before its fix. The probe cases of the review (battery*.py in
docs/research/notes/Toishi full evidence review/scripts) are golden rows in
tests/grader/data/golden_probes.toml.
"""

import pytest

from core.grader import HOLE_ONLY, AnswerSpec, Status, grade, preview


def spec(kind: str, key: str, **kw: object) -> AnswerSpec:
    return AnswerSpec(answer_type=kind, answer=key, **kw)  # type: ignore[arg-type]


# ---------------------------------------------------------------- item 4: e-notation


@pytest.mark.parametrize(
    ("raw", "key"),
    [
        ("1.2e4", "12000"),
        ("6.02e23", "6.02*10^23"),
        ("1e100", "10^100"),
        ("3E-5", "3*10^(-5)"),
        ("1.6e-19", "1.6*10^(-19)"),
        ("2E-1", "1/5"),
    ],
)
def test_e_notation_is_a_number(raw: str, key: str) -> None:
    result = grade(raw, spec("number", key))
    assert result.status == Status.CORRECT, result.message
    assert r"\times 10^{" in (result.read_as_latex or "")


def test_e_notation_keeps_eulers_e_where_it_meant_e_before() -> None:
    # 2e-1 was always 2e - 1 (e is Euler's number); only forms that were errors changed.
    assert grade("2e-1", spec("number", "2e - 1")).status == Status.CORRECT
    assert grade("2e-1", spec("number", "1/5")).status == Status.INCORRECT


def test_e_notation_limits_and_exactness() -> None:
    assert grade("1e1001", spec("number", "2")).status == Status.INVALID
    assert grade("1.2e4", spec("number", "12000", exact=True)).status == Status.INCORRECT
    assert preview("6.02e23", spec("number", "1")).ok


def test_e_notation_respects_a_variable_named_E() -> None:
    assert grade("2E-3", spec("expression", "2E - 3", vars=("E",))).status == Status.CORRECT


# ---------------------------------------------------------------- item 1: declared variables


@pytest.mark.parametrize("raw", ["t > 1", "x > 1", "x > 1 and y > 1", "x > 1 or t < 0"])
def test_interval_without_vars_takes_interval_notation_only(raw: str) -> None:
    assert grade(raw, spec("interval", "(1, inf)")).status == Status.INVALID


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("x > 1", Status.CORRECT),
        ("(1, inf)", Status.CORRECT),
        ("t > 1", Status.INVALID),
        ("x > 1 and y > 1", Status.INVALID),
        ("x > 1 and t > 1", Status.INVALID),
    ],
)
def test_interval_inequalities_use_the_declared_variable(raw: str, expected: Status) -> None:
    assert grade(raw, spec("interval", "(1, inf)", vars=("x",))).status == expected


def test_two_declared_variables_still_make_one_line() -> None:
    card = spec("interval", "(1, inf)", vars=("x", "y"))
    assert grade("x > 1 and y > 1", card).status == Status.INVALID
    assert grade("y > 1", card).status == Status.CORRECT


# ---------------------------------------------------------------- item 5: tolerance


@pytest.mark.parametrize(
    ("key", "raw", "expected"),
    [
        ("2/3", "0.67", Status.CORRECT),  # 0.5% off: a natural two-place rounding
        ("2/3", "0.66", Status.CORRECT),  # exactly 1% off: the bound is inclusive, decided exactly
        ("2/3", "0.659", Status.INCORRECT),
        ("sqrt(2)", "1.41", Status.CORRECT),
        ("pi", "3.1", Status.INCORRECT),
        ("100", "100.9", Status.CORRECT),
        ("100", "101.1", Status.INCORRECT),
        ("pi", "22/7", Status.INCORRECT),  # exact answers stay exact
        ("1/3", "33/100", Status.INCORRECT),
        ("0", "0.0000000000005", Status.CORRECT),  # the absolute floor (1e-12)
        ("0", "0.000000001", Status.INCORRECT),
        ("10^(-10)", "0.00000000011", Status.INCORRECT),  # 10% off a tiny key
        ("0", "10^(-30)", Status.INCORRECT),  # exact: no floor
    ],
)
def test_default_tolerance_is_one_percent_with_a_floor(
    key: str, raw: str, expected: Status
) -> None:
    assert grade(raw, spec("number", key)).status == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.1667", Status.CORRECT),  # STACK #107: 0.1667 at 4 figures is 0.1667
        ("0.16674", Status.CORRECT),
        ("0.1666", Status.INCORRECT),
        ("0.167", Status.INCORRECT),
        ("1.667e-1", Status.CORRECT),
    ],
)
def test_sig_figs_give_half_a_unit_in_the_last_figure(raw: str, expected: Status) -> None:
    assert grade(raw, spec("number", "0.1667", sig_figs=4)).status == expected


def test_sig_figs_at_a_power_of_ten() -> None:
    card = spec("number", "100", sig_figs=3)  # last place is the units: +-0.5
    assert grade("100.4", card).status == Status.CORRECT
    assert grade("100.6", card).status == Status.INCORRECT
    card = spec("number", "1/1000", sig_figs=1)  # +-0.0005
    assert grade("0.0014", card).status == Status.CORRECT
    assert grade("0.0016", card).status == Status.INCORRECT


def test_decimal_places_give_half_a_unit_in_the_last_place() -> None:
    card = spec("number", "2/3", form="decimal(2)")
    assert grade("0.67", card).status == Status.CORRECT
    assert grade("0.66", card).status == Status.INCORRECT


def test_tolerance_line_accepts_e_notation() -> None:
    card = spec("number", "pi", tolerance="1e-9")
    assert grade("3.14159265", card).status == Status.INCORRECT
    assert grade("3.1415926536", card).status == Status.CORRECT


# ---------------------------------------------------------------- item 3: simplified forms


@pytest.mark.parametrize(
    ("key", "raw"),
    [
        ("2*sqrt(2)", "sqrt(8)"),
        ("2*sqrt(2)", "4/sqrt(2)"),
        ("2*sqrt(3)", "sqrt(12)"),
        ("2*sqrt(3)", "6/sqrt(3)"),
        ("3*sqrt(5)", "sqrt(45)"),
        ("5*sqrt(2)/2", "5/sqrt(2)"),
        ("5*sqrt(2)/2", "sqrt(50)/2"),
        ("sqrt(3)/3", "1/sqrt(3)"),
        ("sqrt(2)/2", "1/sqrt(2)"),
        ("sqrt(2)/2", "sqrt(1/2)"),
        ("2", "root(8, 3)"),
        ("2*sqrt(2)", "2^(3/2)"),
        ("sqrt(2)/2", "2^(-1/2)"),
        ("2*x*sqrt(3)", "x*sqrt(12)"),
        ("2*sqrt(2*x)", "sqrt(8x)"),
        ("x/6", "(x/2)/3"),
    ],
)
def test_simplified_names_canonical_forms(key: str, raw: str) -> None:
    card = spec("expression" if "x" in key else "number", key, form="simplified")
    result = grade(raw, card)
    assert result.status == Status.INCORRECT, (raw, result.message)
    assert "simplified" in result.message


@pytest.mark.parametrize(
    ("key", "raw"),
    [
        ("2*sqrt(2)", "2*sqrt(2)"),
        ("2*sqrt(2)", "sqrt(2)*2"),
        ("sqrt(3)/3", "sqrt(3)/3"),
        ("x^(3/2)", "x^(3/2)"),
        ("x/2", "(1/2)x"),
        ("1/(2*sqrt(3))", "1/(2*sqrt(3))"),  # a key that keeps a radical below allows it
        ("1/(2*sqrt(x))", "1/(2sqrt(x))"),
    ],
)
def test_simplified_accepts_canonical_forms(key: str, raw: str) -> None:
    card = spec("expression" if "x" in key else "number", key, form="simplified")
    assert grade(raw, card).status == Status.CORRECT


# ---------------------------------------------------------------- item 2: holes


@pytest.mark.parametrize(
    ("kind", "key", "raw", "where"),
    [
        ("expression", "x + 1", "(x^2-1)/(x-1)", "x = 1"),
        ("expression", "1/(x-1)", "x/(x^2-x)", "x = 0"),
        ("expression", "1/(x+1)", "(x-1)/(x^2-1)", "x = 1"),
        ("expression", "sin(x)", "tan(x)*cos(x)", "x = "),
        ("expression", "1/(1-cos(x))", "(1+cos(x))/sin(x)^2", "x = "),
        ("antiderivative", "x^2/2 + C", "x^3/(2x)", "x = 0"),
        ("equation", "y = x^2", "y/x^2 = 1", "x = 0"),
    ],
)
def test_hole_only_answers_are_not_wrong(kind: str, key: str, raw: str, where: str) -> None:
    result = grade(raw, spec(kind, key))
    assert result.status == Status.INVALID, result.message
    assert result.category == HOLE_ONLY
    assert not result.counts_as_attempt
    assert result.message.startswith(f"Your answer is undefined at {where}")
    assert result.message.endswith("where the expected answer isn't; check its form.")


def test_hole_only_needs_the_variable_declared_when_the_key_has_none() -> None:
    assert grade("sec(x)^2 - tan(x)^2", spec("expression", "1", vars=("x",))).category == HOLE_ONLY


@pytest.mark.parametrize(
    ("kind", "key", "raw"),
    [
        ("expression", "ln(x^2)", "2*ln(x)"),  # undefined on a whole region
        ("expression", "x", "sqrt(x)^2"),
        ("expression", "sqrt(x*y)", "sqrt(x)*sqrt(y)"),
        ("expression", "x + 2", "(x^2-1)/(x-1)"),  # a hole and a wrong value
        ("antiderivative", "arctan(x) + C", "-arctan(1/x)"),  # a jump, not a hole
        ("antiderivative", "ln(abs(x)) + C", "ln(x)"),
        ("equation", "x^2 + y^2 = 1", "y = sqrt(1 - x^2)"),
    ],
)
def test_undefined_regions_and_jumps_are_still_wrong(kind: str, key: str, raw: str) -> None:
    assert grade(raw, spec(kind, key)).status == Status.INCORRECT


@pytest.mark.parametrize(
    ("kind", "key", "raw"),
    [
        ("expression", "x + 1", "(x^2-1)/(x-1)"),
        ("equation", "y = x^2", "y/x^2 = 1"),
        ("expression", "sin(x)", "tan(x)*cos(x)"),
    ],
)
def test_a_strict_domain_still_makes_holes_wrong(kind: str, key: str, raw: str) -> None:
    result = grade(raw, spec(kind, key, domain_strict=True))
    assert result.status == Status.INCORRECT
    assert result.category == ""


def test_strict_domain_is_a_card_key() -> None:
    fields = {"answer-type": "expression", "answer": "x + 1", "domain-strict": "yes"}
    assert AnswerSpec.from_fields(fields).domain_strict


def test_a_form_the_card_asks_for_still_fails_a_hole() -> None:
    card = spec("expression", "x + 1", form="simplified")
    assert grade("(x^2-1)/(x-1)", card).status == Status.INCORRECT


def test_shared_holes_and_declared_domains_are_correct() -> None:
    assert grade("sin(x)/cos(x)", spec("expression", "tan(x)")).status == Status.CORRECT
    assert grade("x + 1", spec("expression", "(x^2-1)/(x-1)")).status == Status.CORRECT
    card = spec("expression", "x + 1", domain="x != 1")
    assert grade("(x^2-1)/(x-1)", card).status == Status.CORRECT


def test_hole_only_answers_are_logged_as_their_own_category(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("INFO", logger="core.grader"):
        grade("(x^2-1)/(x-1)", spec("expression", "x + 1"))
    assert [getattr(r, "category", None) for r in caplog.records] == [HOLE_ONLY]
