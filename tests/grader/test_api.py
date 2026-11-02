"""Public API: preview, grade results, known wrong answers, check_key, AnswerSpec."""

import pytest

from core.grader import (
    AnswerSpec,
    Choice,
    Status,
    WrongAnswer,
    check_key,
    grade,
    parse_wrong_field,
    preview,
)
from core.grader.errors import SpecError
from core.grader.spec import resolve

# ------------------------------------------------------------------ preview (MATH-6)


def test_preview_makes_multiplication_explicit() -> None:
    p = preview("2x(x+1)", AnswerSpec("expression", "2x^2 + 2x"))
    assert p.ok
    assert p.read_as_latex == r"2 \cdot x \cdot \left(x + 1\right)"


def test_preview_e_2x_note() -> None:
    p = preview("e^2x", AnswerSpec("expression", "e^(2x)"))
    assert p.ok
    assert p.read_as_latex == r"{e}^{2} \cdot x"
    assert p.hints == ("e^2x is read as e^2 times x. For e^(2x), add parentheses.",)


def test_preview_fraction_note() -> None:
    p = preview("1/2x", AnswerSpec("expression", "x/2"))
    assert p.read_as_latex == r"\frac{1}{2} \cdot x"
    assert p.hints == ("1/2x is read as (1/2)*x. Write 1/(2x) if x belongs in the denominator.",)


def test_preview_sinx_hint() -> None:
    p = preview("sinx", AnswerSpec("expression", "sin(x)"))
    assert not p.ok
    assert p.read_as_latex is None
    assert p.hints == ("Did you mean sin(x)?",)


def test_preview_shape_error_still_shows_the_reading() -> None:
    p = preview("(1, 2)", AnswerSpec("number", "3"))
    assert not p.ok
    assert p.read_as_latex == r"\left(1, 2\right)"
    assert p.message == "Expected a number."


@pytest.mark.parametrize(
    ("raw", "latex"),
    [
        ("sqrt(x)/2", r"\frac{\sqrt{x}}{2}"),
        ("root(x, 3)", r"\sqrt[3]{x}"),
        ("log_2(x)", r"\log_{2}\left(x\right)"),
        ("|x|", r"\left|x\right|"),
        ("sin(x)^2", r"{\left(\sin\left(x\right)\right)}^{2}"),
        ("arcsec(x)", r"\operatorname{arcsec}\left(x\right)"),
        ("x <= 2", r"x \le 2"),
        ("(-inf, 0) U [2, inf)", r"\left(-\infty, 0\right) \cup \left[2, \infty\right)"),
        ("<1, 2>", r"\left\langle 1, 2\right\rangle"),
        ("[[1, 2], [3, 4]]", r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}"),
        ("theta_1", r"\theta_{1}"),
        ("30°", r"30^{\circ}"),
        ("DNE", r"\text{DNE}"),
        ("none", r"\varnothing"),
    ],
)
def test_preview_latex(raw: str, latex: str) -> None:
    keys = {
        "(-inf": ("interval", "(0, 1)"),
        "<1": ("vector", "<1, 1>"),
        "[[": ("matrix", "[[1, 1], [1, 1]]"),
        "DNE": ("number", "2"),
        "none": ("set", "1"),
    }
    kind, key = next(
        (v for prefix, v in keys.items() if raw.startswith(prefix)), ("expression", "x")
    )
    p = preview(raw, AnswerSpec(kind, key, vars=("x", "theta_1")))
    assert p.read_as_latex == latex


def test_preview_from_mathlive() -> None:
    p = preview(r"\sin x\cos x", AnswerSpec("expression", "sin(2x)"), "mathlive")
    assert p.ok
    assert p.read_as_latex == r"\sin\left(x\right) \cdot \cos\left(x\right)"


def test_preview_of_a_text_card_needs_no_math() -> None:
    assert preview("concave up", AnswerSpec("text", "concave up")).ok


# ------------------------------------------------------------------ grade results


def test_grade_result_fields() -> None:
    r = grade("x^2 - 4", AnswerSpec("expression", "(x-2)(x+2)"))
    assert r.status is Status.CORRECT
    assert r.counts_as_attempt
    assert r.read_as_latex == r"{x}^{2} - 4"
    assert {"parse", "worker", "numeric", "total"} <= set(r.timings)


def test_invalid_answers_never_count() -> None:
    for raw in ["sinx", "(1, 2)", "x = 2", ""]:
        r = grade(raw, AnswerSpec("number", "2"))
        assert r.status is Status.INVALID
        assert not r.counts_as_attempt
        assert r.message


def test_shape_message() -> None:
    r = grade("3", AnswerSpec("interval", "(0, 1)"))
    assert r.status is Status.INVALID
    assert r.message == "Expected an interval."


def test_unsupported_types() -> None:
    q = grade("9.8 m/s^2", AnswerSpec("quantity", "9.8 m/s^2", units="m/s^2"))
    assert q.status is Status.UNSUPPORTED
    assert "1.1" in q.message
    assert q.read_as_latex == r"\frac{9.8 \cdot m}{{s}^{2}}"
    assert not q.counts_as_attempt
    assert grade("x", AnswerSpec("self")).status is Status.UNSUPPORTED


def test_card_problem_is_undecidable() -> None:
    r = grade("1", AnswerSpec("number", "1", form="pretty"))
    assert r.status is Status.UNDECIDABLE
    assert r.message.startswith("Card problem")


def test_mathlive_source() -> None:
    spec = AnswerSpec("number", "sqrt(2)/2")
    assert grade(r"\frac{1}{\sqrt{2}}", spec, "mathlive").status is Status.CORRECT
    r = grade(r"\frac{1}{\placeholder{}}", spec, "mathlive")
    assert r.status is Status.INVALID
    assert r.message == "Fill in the empty box."
    with pytest.raises(ValueError, match="unknown source"):
        grade("1", spec, "latex")  # type: ignore[arg-type]


# ------------------------------------------------------------------ known wrong answers


def test_matched_wrong_answer_feedback_and_step() -> None:
    spec = AnswerSpec(
        "set",
        "-1, 0, 1",
        wrong=parse_wrong_field(
            "0, 1 => x + 1 = 0 gives a critical number too @3; 0 => missed two"
        ),
    )
    r = grade("1, 0", spec)
    assert r.status is Status.INCORRECT
    assert r.matched_wrong == WrongAnswer("0, 1", "x + 1 = 0 gives a critical number too", 3)
    assert r.message == "x + 1 = 0 gives a critical number too"
    assert grade("0", spec).matched_wrong == WrongAnswer("0", "missed two", None)
    assert grade("5", spec).matched_wrong is None
    assert grade("-1, 0, 1", spec).matched_wrong is None


def test_matched_wrong_uses_the_same_equivalence() -> None:
    spec = AnswerSpec(
        "expression", "2x*cos(x^2)", wrong=parse_wrong_field("cos(x^2) => chain rule @2")
    )
    r = grade("cos(x*x)", spec)
    assert r.matched_wrong is not None
    assert r.matched_wrong.step == 2
    r = grade("-2x*sin(x^2)", spec)
    assert r.status is Status.INCORRECT
    assert r.matched_wrong is None


def test_text_wrong_answer() -> None:
    spec = AnswerSpec("text", "local maximum", wrong=parse_wrong_field("local minimum => sign @2"))
    r = grade("Local  Minimum", spec)
    assert r.status is Status.INCORRECT
    assert r.matched_wrong == WrongAnswer("local minimum", "sign", 2)


def test_parse_wrong_field() -> None:
    assert parse_wrong_field("") == ()
    assert parse_wrong_field("2 => no; 3 @4; 4") == (
        WrongAnswer("2", "no", None),
        WrongAnswer("3", None, 4),
        WrongAnswer("4", None, None),
    )
    assert parse_wrong_field("x^2 => forgot the 2 @ 1") == (WrongAnswer("x^2", "forgot the 2", 1),)


# ------------------------------------------------------------------ check_key (MATH-13)


def test_check_key_passes() -> None:
    spec = AnswerSpec(
        "expression", "6x(x^2 + 1)^2", wrong=parse_wrong_field("6x(x^2+1); 3(x^2+1)^2")
    )
    assert check_key(spec).ok


def test_check_key_alternatives() -> None:
    assert check_key(AnswerSpec("text", "concave up; concave upward")).ok
    assert check_key(AnswerSpec("number", "1/2; 0.5")).ok


@pytest.mark.parametrize(
    ("spec", "problem"),
    [
        (
            AnswerSpec("expression", "x^2", wrong=parse_wrong_field("x*x")),
            "wrong answer 'x*x' grades correct",
        ),
        (AnswerSpec("expression", "x^2-4", form="factored"), "key 'x^2-4' grades incorrect"),
        (
            AnswerSpec("antiderivative", "x^2/2", require_constant=True),
            "key 'x^2/2' grades incorrect",
        ),
        (AnswerSpec("number", "x + 1"), "answer 'x + 1': Expected a number"),
        (AnswerSpec("number", "sinx"), "answer 'sinx': Can't read 'sinx'"),
        (AnswerSpec("number", ""), "answer: missing"),
        (
            AnswerSpec("number", "1", wrong=parse_wrong_field("(1, 2)")),
            "wrong answer '(1, 2)' has the wrong shape",
        ),
        (
            AnswerSpec("number", "1", wrong=parse_wrong_field("2x")),
            "wrong answer '2x' can't be read",
        ),
        (AnswerSpec("quantity", "9.8 m/s^2"), "not supported until version 1.1"),
        (AnswerSpec("number", "ln(-1)"), "has no real value"),
        (AnswerSpec("expression", "sqrt(x)", domain="x < -1"), "isn't defined at enough points"),
        (AnswerSpec("magic", "1"), "unknown type"),
        (AnswerSpec("number", "1", tolerance="lots"), "tolerance"),
        (AnswerSpec("expression", "x", domain="x"), "domain"),
        (AnswerSpec("expression", "x", vars=("x frobnicated",)), "unknown assumption"),
        (AnswerSpec("choice", "", choices=(Choice("a", False),)), "no option is marked"),
        (AnswerSpec("truefalse", "maybe"), "expected true or false"),
    ],
)
def test_check_key_problems(spec: AnswerSpec, problem: str) -> None:
    result = check_key(spec)
    assert not result.ok
    assert any(problem in p for p in result.problems), result.problems


def test_choice_key_checks_itself() -> None:
    spec = AnswerSpec("choice", choices=(Choice("yes", True), Choice("no", False)))
    assert check_key(spec).ok


# ------------------------------------------------------------------ AnswerSpec


def test_from_fields() -> None:
    spec = AnswerSpec.from_fields(
        {
            "answer-type": "antiderivative",
            "answer": "x^3/3 + C",
            "wrong": "x^3 => divide by 3 @1",
            "vars": "x",
            "require-constant": "yes",
            "tolerance": "1%",
            "angles": "Degrees",
        }
    )
    assert spec.answer_type == "antiderivative"
    assert spec.require_constant
    assert spec.wrong == (WrongAnswer("x^3", "divide by 3", 1),)
    assert spec.vars == ("x",)
    assert spec.angles == "degrees"
    assert AnswerSpec.from_fields({}).answer_type == "self"
    with pytest.raises(SpecError):
        AnswerSpec.from_fields({"exact": "sure"})


def test_template_parameters_are_not_checker_variables() -> None:
    spec = AnswerSpec.from_fields(
        {"answer-type": "set", "answer": "-3, 3", "vars": "k = int(1, 9)"}
    )
    card = resolve(spec)
    assert card.variables == ()
    assert grade("3, -3", spec).status is Status.CORRECT


def test_declared_assumptions() -> None:
    card = resolve(AnswerSpec("expression", "sqrt(t^2)", vars=("t positive", "i imaginary")))
    assert card.variables == (("t", "positive"),)
    assert card.imaginary


def test_the_app_process_never_loads_sympy() -> None:
    """Parsing and previews run in the app's process; SymPy and mpmath stay in the worker."""
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import sys\n"
        "from core.grader import AnswerSpec, preview\n"
        "assert preview('2x + sin(x)', AnswerSpec('expression', '2x + sin(x)')).ok\n"
        "assert preview(r'\\frac{1}{2}', AnswerSpec('number', '1/2'), 'mathlive').ok\n"
        "print(sorted(m for m in ('sympy', 'mpmath') if m in sys.modules))\n"
    )
    root = Path(__file__).resolve().parents[2]
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "[]"
