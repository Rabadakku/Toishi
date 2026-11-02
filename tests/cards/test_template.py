"""Template expansion: generators, the whitelist evaluator, sweeps checked by an
independent route, stable seeds, and located errors."""

import re
from dataclasses import replace
from fractions import Fraction

import pytest

from core.cards import answer_spec
from core.cards.cardfile import read_card_file
from core.cards.sweep import SweepRunner, runner
from core.cards.template import (
    Param,
    TemplateError,
    TemplateJob,
    compile_expr,
    compile_template,
    parse_params,
)
from core.grader import Status, grade
from core.model import Card
from tests.cards.helpers import cards_file, load_text, rejection


def template(keys: str, question: str = "Q [[k]]", solution: str = "S") -> str:
    return cards_file(
        f"## Card t.001\n{keys}\n\n### Question\n{question}\n\n### Solution\n{solution}\n"
    )


def instances(text: str) -> list[Card]:
    result = load_text(text)
    assert not result.errors(), result.errors()
    return [a.card for a in result.cards]


def params(card: Card) -> dict[str, str]:
    assert card.params is not None
    return dict(part.split(" = ") for part in card.params.split("; "))


def line_of(text: str, marker: str) -> int:
    return next(i for i, line in enumerate(text.split("\n"), start=1) if marker in line)


# ---------------------------------------------------------------- generators


def test_int_domain_with_exclusions_matches_a_list() -> None:
    (p,), checker = parse_params("k = int(-3, 4, not 0, not 2); x, t", 1)
    expected = [v for v in range(-3, 5) if v not in (0, 2)]
    assert checker == "x, t"
    assert p.size() == len(expected)
    assert [p.value_at(i) for i in range(p.size())] == expected


def test_decimal_and_choice_domains() -> None:
    d, c = parse_params("d = decimal(1.5, 2, 2); c = choice(1/2, sqrt(2), x^2)", 3)[0]
    assert d.size() == 51
    assert d.value_at(0) == Fraction(3, 2)
    assert d.value_at(50) == 2
    assert c.kind == "choice"
    assert c.size() == 3


@pytest.mark.parametrize(
    ("vars_line", "fragment"),
    [
        ("k = int(5, 1)", "5 is more than 1"),
        ("k = int(1, 2.5)", "whole numbers"),
        ("k = rand(1, 9)", "needs a generator"),
        ("k = choice(1)", "at least two choices"),
        ("k = decimal(1, 2, 9)", "places is a whole number from 0 to 6"),
        ("k = decimal(1.25, 2, 1)", "at most 1 decimal places"),
        ("k = int(0, 0, not 0)", "no values left"),
    ],
)
def test_bad_generators_name_the_vars_line(vars_line: str, fragment: str) -> None:
    text = template(f"answer-type: number\nvars: {vars_line}\nanswer: k")
    line, reason = rejection(load_text(text))
    assert line == line_of(text, "vars:")
    assert fragment in reason


# ---------------------------------------------------------------- expansion


def test_every_combination_when_there_are_few() -> None:
    cards = instances(
        template("answer-type: number\nvars: a = int(1, 4); b = int(1, 5)\nanswer: a*b")
    )
    assert len(cards) == 20
    assert {(p["a"], p["b"]) for p in map(params, cards)} == {
        (str(a), str(b)) for a in range(1, 5) for b in range(1, 6)
    }
    for card in cards:
        p = params(card)
        assert card.answer == str(int(p["a"]) * int(p["b"]))


def test_sampling_is_capped_at_200_and_reproducible() -> None:
    text = template("answer-type: number\nvars: a = int(1, 100); k = int(1, 100)\nanswer: a + k")
    first = instances(text)
    assert len(first) == 200
    assert len({c.seed for c in first}) == 200
    assert [c.id for c in instances(text)] == [c.id for c in first]


def test_require_filters_instances() -> None:
    cards = instances(
        template(
            "answer-type: number\nvars: r = int(1, 5); s = int(1, 5)\nrequire: r < s\nanswer: s - r"
        )
    )
    assert len(cards) == 10
    assert all(int(params(c)["r"]) < int(params(c)["s"]) for c in cards)


def test_require_runs_before_a_let_that_would_be_undefined() -> None:
    keys = (
        "answer-type: number\nvars: k = int(1, 3)\nrequire: k != 2\nlet: m = 1/(k - 2)\nanswer: m"
    )
    cards = instances(template(keys))
    assert sorted(str(c.answer) for c in cards) == ["-1", "1"]


def test_seed_depends_only_on_the_parameters() -> None:
    a = instances(template("answer-type: number\nvars: k = int(1, 3)\nanswer: k"))
    b = instances(template("answer-type: number\nvars: k = int(1, 3)\nanswer: 2*k", "Other [[k]]"))
    assert {c.seed for c in a} == {c.seed for c in b}
    assert all(re.fullmatch(r"t\.001--[0-9a-f]{8}", c.id) for c in a)


def test_template_without_parameters_makes_one_instance() -> None:
    (card,) = instances(template("answer-type: number\nanswer: 2 + 3", "What is [[2 + 3]]?"))
    assert card.answer == "2 + 3"  # no template names: kept as written
    assert card.question_md == "What is 5?"
    assert card.params == ""
    assert card.notes_md is None


# ---------------------------------------------------------------- independent routes


def test_linear_sweep_against_fractions() -> None:
    keys = (
        "answer-type: number\nvars: a = int(2, 9); b = int(-9, 9, not 0); c = int(-20, 20)\n"
        "answer: solve(a*x + b = c, x)\nwrong: (c + b)/a"
    )
    cards = instances(template(keys, "Solve \\([[tex(a*x + b)]] = [[c]]\\)."))
    assert len(cards) == 200
    for card in cards:
        p = {k: int(v) for k, v in params(card).items()}
        expected = Fraction(p["c"] - p["b"], p["a"])
        assert Fraction(card.answer.replace(" ", "")) == expected  # type: ignore[union-attr]
        assert card.wrong[0].answer.replace(" ", "") in {
            str(Fraction(p["c"] + p["b"], p["a"])),
            f"-{Fraction(-(p['c'] + p['b']), p['a'])}",
        }
        assert "+ -" not in (card.question_md or "")
        assert " 1 x" not in (card.question_md or "")


def test_quadratic_roots_sweep() -> None:
    keys = (
        "answer-type: set\nvars: r = int(-6, 6); s = int(-6, 6)\nrequire: r < s\n"
        "let: f = expand((x - r)*(x - s))\nanswer: solve(f, x)"
    )
    cards = instances(template(keys, "Solve \\([[tex(f)]] = 0\\)."))
    assert len(cards) == 78
    for card in cards:
        p = params(card)
        assert card.answer == f"{p['r']}, {p['s']}"


def test_derivative_sweep_graded_like_a_student() -> None:
    keys = (
        "answer-type: expression\nvars: a = int(2, 6); n = int(3, 6)\n"
        "let: f = a*x^n\nanswer: diff(f, x)"
    )
    cards = instances(template(keys, "Differentiate \\([[tex(f)]]\\)."))
    assert len(cards) == 20
    for card in cards:
        p = {k: int(v) for k, v in params(card).items()}
        typed = f"{p['a'] * p['n']}x^{p['n'] - 1}"
        assert grade(typed, answer_spec(card)).status == Status.CORRECT
        assert grade(f"{p['a']}x^{p['n'] - 1}", answer_spec(card)).status == Status.INCORRECT


# ---------------------------------------------------------------- operations


@pytest.mark.parametrize(
    ("answer_type", "answer", "expected"),
    [
        ("number", "limit(abs(x)/x, x, 0)", "DNE"),
        ("number", "limit(1/x^2, x, 0)", "inf"),
        ("number", "limit(1/x, x, 0)", "DNE"),
        ("number", "limit(abs(x)/x, x, 0, left)", "-1"),
        ("number", "limit(abs(x)/x, x, 0, right)", "1"),
        ("number", "limit((k*x + 1)/(x + 2), x, inf)", "3"),
        ("number", "limit(sin(1/x), x, 0)", "DNE"),
        ("number", "integrate(k*x^2, x, 0, 1)", "1"),
        ("antiderivative", "integrate(k*x^2, x) + C", "C + x^3"),
        ("interval", "solve(x^2 - k^2 < 0, x)", "(-3, 3)"),
        ("set", "solve(x^2 + k, x)", "none"),
        ("number", "subs(x^2 + 1, x, k)", "10"),
        ("expression", "factor(x^2 - k^2)", "(x - 3)*(x + 3)"),
        ("expression", "expand((x + k)^2)", "x^2 + 6*x + 9"),
        ("expression", "simplify((x^2 - k^2)/(x - k))", "x + 3"),
        ("point", "(k, subs(x^2, x, k))", "(3, 9)"),
        ("equation", "y = diff(k*x^2, x)", "y = 6*x"),
        ("vector", "<k, -k>", "<3, -3>"),
        ("matrix", "[[k, 0], [0, k]]", "[[3, 0], [0, 3]]"),
        ("interval", "(-inf, k) U (k, inf)", "(-inf, 3) U (3, inf)"),
    ],
)
def test_operations(answer_type: str, answer: str, expected: str) -> None:
    keys = f"answer-type: {answer_type}\nvars: k = choice(3, 3)\nanswer: {answer}"  # one set
    if answer_type == "expression" and "simplify" in answer:
        keys += "\ndomain: x != 3"
    cards = instances(template(keys))
    assert {c.answer for c in cards} == {expected}


def test_insertions_render_plain_and_tex() -> None:
    keys = "answer-type: number\nvars: k = choice(3, 5)\nlet: f = x^2 - k*x\nanswer: -k/2"
    q = "Plain [[-k/2]], tex \\([[tex(-k/2)]]\\), poly \\([[tex(f)]]\\), roots [[solve(f, x)]]"
    by_k = {params(c)["k"]: c for c in instances(template(keys, q))}
    assert by_k["3"].question_md == (
        "Plain -3/2, tex \\(- \\frac{3}{2}\\), poly \\(x^{2} - 3 x\\), roots 0, 3"
    )
    assert by_k["3"].answer == "-3/2"


def test_decimal_parameters_display_as_decimals_and_keys_stay_exact() -> None:
    keys = "answer-type: number\nvars: d = decimal(1.5, 1.7, 1)\nanswer: 2*d"
    by_d = {
        params(c)["d"]: c
        for c in instances(template(keys, "Double [[d]] is [[2*d]], \\([[tex(d*x)]]\\)"))
    }
    assert sorted(by_d) == ["1.5", "1.6", "1.7"]
    assert by_d["1.7"].question_md == "Double 1.7 is 3.4, \\(1.7 x\\)"
    assert by_d["1.7"].answer == "17/5"
    assert by_d["1.5"].answer == "3"


def test_choice_parameter_with_expressions() -> None:
    keys = "answer-type: expression\nvars: g = choice(x^2, x^3)\nanswer: diff(g, x)"
    assert {c.answer for c in instances(template(keys, "Q [[g]]"))} == {"2*x", "3*x^2"}


def test_wrong_answers_and_feedback_are_computed_per_instance() -> None:
    keys = (
        "answer-type: number\nvars: k = int(3, 4)\nanswer: k^2\nwrong: 2*k => You doubled [[k]]. @1"
    )
    cards = instances(template(keys, "Square [[k]].", "1. [s.a] Square: [[k^2]]"))
    by_k = {params(c)["k"]: c for c in cards}
    assert (by_k["3"].wrong[0].answer, by_k["3"].wrong[0].feedback, by_k["3"].wrong[0].step) == (
        "6",
        "You doubled 3.",
        1,
    )


def test_multipart_template() -> None:
    body = (
        "## Card t.001\nvars: k = int(1, 2)\nlet: f = x^2 - k^2\n\n"
        "### Question\nLet \\(f(x) = [[tex(f)]]\\).\n\n"
        "### Part a\nanswer-type: set\nanswer: solve(f, x)\nFind the zeros.\n\n"
        "### Part b\nanswer-type: number\nanswer: subs(f, x, 0)\nFind \\(f(0)\\).\n\n"
        "### Solution\nS\n"
    )
    cards = instances(cards_file(body))
    by_k = {params(c)["k"]: c for c in cards}
    assert [(p.label, p.answer) for p in by_k["2"].parts] == [("a", "-2, 2"), ("b", "-4")]


# ---------------------------------------------------------------- errors


@pytest.mark.parametrize(
    ("keys", "marker", "fragment"),
    [
        (
            "answer-type: number\nvars: k = int(1, 3)\nlet: m = 1/(k - 2)\nanswer: m",
            "let:",
            "let m",
        ),
        (
            "answer-type: number\nvars: k = int(1, 3)\nrequire: k > 5\nanswer: k",
            "require:",
            "no parameter set meets require",
        ),
        ("answer-type: number\nvars: k = int(1, 3)\nanswer: 1/(k - 2)", "answer:", "undefined"),
        (
            "answer-type: expression\nvars: k = int(1, 2)\nanswer: integrate(e^(x^2), x)",
            "answer:",
            "can't be written as an answer",
        ),
        (
            "answer-type: number\nvars: kk = int(1, 2)\nanswer: kk",
            "vars:",
            "can't be a template name",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nlet: f = g + 1; g = k\nanswer: f",
            "let:",
            "uses g before it is defined",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nrequire: q > 0\nanswer: k",
            "require:",
            "require uses q",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nanswer: tex(k)",
            "answer:",
            "tex(...) can't be used here",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nanswer: diff(k)",
            "answer:",
            "diff takes 2 to 3 arguments",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nanswer: diff(x^2, 2)",
            "answer:",
            "must be a variable",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nanswer: diff(x^2, k)",
            "answer:",
            "is a template name",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nanswer: solve(x^2 - k, x)",
            "answer:",
            "instance k = 1",
        ),
        (
            "answer-type: number\nvars: e = int(1, 2)\nanswer: e",
            "vars:",
            "can't be a template name",
        ),
        (
            "answer-type: number\nvars: k = int(1, 2)\nlet: f = __import__('os')\nanswer: f",
            "let:",
            "can't read",
        ),
        (
            "answer-type: number\nvars: k = choice(1, j)\nlet: j = 2\nanswer: k",
            "vars:",
            "can't use the template names j",
        ),
    ],
)
def test_template_errors_are_located(keys: str, marker: str, fragment: str) -> None:
    text = template(keys)
    line, reason = rejection(load_text(text))
    assert fragment in reason, reason
    assert line == line_of(text, marker), reason


def test_unclosed_insertion_is_located() -> None:
    text = template("answer-type: number\nvars: k = int(1, 2)\nanswer: k", "First line\nSecond [[k")
    assert rejection(load_text(text)) == (
        line_of(text, "Second"),
        "[[ is never closed with ]] on the same line",
    )


def test_one_bad_instance_rejects_the_whole_template() -> None:
    keys = "answer-type: number\nvars: k = int(-2, 2)\nanswer: sqrt(k)"
    result = load_text(template(keys))
    assert result.cards == []
    assert result.templates == {}
    assert "instance k = -2" in result.rejected[0].reasons[0]


def test_expression_layer_never_evaluates_python() -> None:
    for text in ("__import__('os').system('true')", "().__class__", "exec('1')", "lambda: 1"):
        with pytest.raises(TemplateError):
            compile_expr(text)


# ---------------------------------------------------------------- time limits


def job_for(keys: str) -> TemplateJob:
    src = read_card_file(template(keys), "t.cards.md")
    return compile_template(src.blocks[0], src.lines, src.header, src.name)


def test_an_instance_over_the_limit_rejects_the_template() -> None:
    job = replace(
        job_for("answer-type: number\nvars: k = int(1, 2)\nanswer: k"), seconds=0.05, test_sleep=0.1
    )
    result = runner().run(job)
    assert result.error is not None
    # The measured time varies with machine load (0.2 s on a busy Mac); the wording doesn't.
    assert re.search(r"took \d+(\.\d+)? s \(the limit is 0\.05 s\)", result.error)


def test_a_hung_instance_is_killed_and_the_runner_recovers() -> None:
    own = SweepRunner()
    try:
        job = job_for("answer-type: number\nvars: k = int(1, 2)\nanswer: k")
        hung = own.run(replace(job, seconds=0.2, test_sleep=5.0))
        assert hung.error == "an instance took longer than 0.2 s"
        assert own.kills == 1
        ok = own.run(job)
        assert ok.error is None
        assert len(ok.instances) == 2
    finally:
        own.stop()


def test_param_value_at_rejects_nothing_silently() -> None:
    p = Param("k", "int", 1, Fraction(1), Fraction(3), exclude=(2,))
    assert [p.value_at(i) for i in range(p.size())] == [1, 3]


# ---------------------------------------------------------------- real numbers only, literal [[


@pytest.mark.parametrize(
    ("answer_type", "answer"),
    [("expression", "sqrt(k)*x"), ("expression", "ln(k) + x"), ("number", "k^(1/2)")],
)
def test_complex_values_reject_the_template(answer_type: str, answer: str) -> None:
    text = template(f"answer-type: {answer_type}\nvars: k = int(-2, 2, not 0)\nanswer: {answer}")
    line, reason = rejection(load_text(text))
    assert line == line_of(text, "answer:")
    assert "not a real number" in reason


def test_display_math_and_code_spans_are_not_insertions() -> None:
    body = (
        "## Card m.001\nanswer-type: matrix\nanswer: [[1, 2], [3, 4]]\n\n"
        "### Question\nType `[[1, 2], [3, 4]]` for the matrix on \\[[0, 1]\\].\n\n### Solution\nS\n"
    )
    result = load_text(cards_file(body))
    assert not result.errors(), result.errors()
    assert result.templates == {}
    card = result.cards[0].card
    assert card.question_md == "Type `[[1, 2], [3, 4]]` for the matrix on \\[[0, 1]\\]."


def test_sympy_stays_out_of_the_callers_process() -> None:
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import sys\n"
        "from core.cards import Source, load, shutdown\n"
        "from core.grader import shutdown as grader_shutdown\n"
        "if __name__ == '__main__':\n"
        "    text = '---\\nformat: mastery-cards 1\\n---\\n\\n## Card t.001\\n'\n"
        "    text += 'answer-type: set\\nvars: k = int(1, 3)\\n'\n"
        "    text += 'answer: solve(x^2 - k^2, x)\\n\\n### Question\\nQ [[k]]\\n'\n"
        "    result = load([Source('t.cards.md', text)])\n"
        "    assert len(result.cards) == 3, result.errors()\n"
        "    print(sorted(m for m in ('sympy', 'mpmath') if m in sys.modules))\n"
        "    shutdown(); grader_shutdown()\n"
    )
    root = Path(__file__).resolve().parents[2]
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
    )
    assert out.stdout.strip().splitlines()[-1] == "[]"


def test_a_sweep_process_that_died_is_replaced() -> None:
    own = SweepRunner()
    try:
        own.start()
        own._proc.kill()
        own._proc.join(5)
        result = own.run(job_for("answer-type: number\nvars: k = int(1, 2)\nanswer: k"))
        assert result.error is None
        assert len(result.instances) == 2
    finally:
        own.stop()
