"""Tokenizer and grammar: what parses, how, and the hints when it doesn't (MATH-5, MATH-10)."""

import pytest

from core.grader import nodes as n
from core.grader.errors import InputError
from core.grader.parser import parse
from core.grader.serialize import parsed_text
from core.grader.tokens import MAX_CHARS, MAX_DEPTH, Vocabulary

OPEN = Vocabulary(open_vars=True)
X = Vocabulary(frozenset({"x"}))


def text(raw: str, vocab: Vocabulary = OPEN) -> str:
    """Parse and write back with explicit operators: shows how the input was read."""
    return parsed_text(parse(raw, vocab))


def error(raw: str, vocab: Vocabulary = OPEN) -> InputError:
    with pytest.raises(InputError) as info:
        parse(raw, vocab)
    return info.value


@pytest.mark.parametrize(
    ("raw", "read"),
    [
        ("2x", "2*x"),
        ("3(x+1)", "3*(x + 1)"),
        ("(x+1)(x-1)", "(x + 1)*(x - 1)"),
        ("x(x+1)", "x*(x + 1)"),
        ("e^2x", "e^2*x"),
        ("e^(2x)", "e^(2*x)"),
        ("2x^2", "2*x^2"),
        ("-x^2", "-x^2"),
        ("2^3^2", "2^(3^2)"),
        ("x^-2", "x^(-2)"),
        ("1/2x", "1/2*x"),
        ("2*-3", "2*(-3)"),
        ("sin(x)^2", "sin(x)^2"),
        ("sin(x)cos(x)", "sin(x)*cos(x)"),
        ("2ln|x|", "2*ln(abs(x))"),
        ("|x||y|", "abs(x)*abs(y)"),
        ("||x|-1|", "abs(abs(x) - 1)"),
        ("2|x - 1|", "2*abs(x - 1)"),
        ("log_2(x)", "log_2(x)"),
        ("log_e(x)", "ln(x)"),
        ("asin(x)", "arcsin(x)"),
        ("x**2", "x^2"),
        ("x²", "x^(2)"),
        ("x⁻¹", "x^(-1)"),
        ("2π", "2*pi"),
        ("θ", "theta"),
        ("x ≤ 2", "x <= 2"),
        ("a ≠ b", "a != b"),
        ("(−∞, 0) ∪ (2, ∞)", "(-inf, 0) U (2, inf)"),  # noqa: RUF001
        ("-1 <= x < 3", "-1 <= x < 3"),
        ("x < 0 or x > 2", "x < 0 or x > 2"),
        ("<1, -2, 3>", "<1, -2, 3>"),
        ("[[1, 2], [3, 4]]", "[[1, 2], [3, 4]]"),
        ("{1, 2}", "{1, 2}"),
        ("[1, 2)", "[1, 2)"),
        ("(0, 0), (2, -4)", "(0, 0), (2, -4)"),
        ("1; 2", "1; 2"),
        ("x_1 + x_2", "x_1 + x_2"),
        ("30°", "30°"),
        ("DNE", "DNE"),
        ("none", "none"),
        ("oo", "inf"),
    ],
)
def test_reads(raw: str, read: str) -> None:
    assert text(raw) == read


@pytest.mark.parametrize(
    ("raw", "hint"),
    [
        ("sinx", "Did you mean sin(x)?"),
        ("lnx", "Did you mean ln(x)?"),
        ("sqrtx", "Did you mean sqrt(x)?"),
        ("sin 2x", "Did you mean sin(2x)?"),
        ("sin x + 1", "Did you mean sin(x)?"),
        ("xy", "Write x*y."),
        ("pix", "Write pi*x."),
        ("xe^x", "Write x*e."),
        ("x2", "Write 2x, x*2 or x^2."),
        ("3 1/2", "Mixed numbers aren't allowed: write 3 + 1/2 or 7/2."),
        ("sin^2(x)", "Write sin(x)^2 for the power of sin."),
        ("sin^-1(x)", "Write arcsin(x) for the inverse."),
        ("ln|x|^2", "Write ln(|x|^2) or ln(|x|)^2."),
        ("pi x", "Write pi*x."),
        ("x sin(x)", "Write x*sin(...)."),
        ("1,000", "Don't use commas inside numbers: 1,000 reads as two numbers."),
    ],
)
def test_hints(raw: str, hint: str) -> None:
    exc = error(raw)
    assert exc.kind == "syntax"
    assert hint in exc.hints, exc.hints


def test_unknown_variable_names_the_card_variables() -> None:
    exc = error("y^2", X)
    assert exc.message == "y isn't a variable in this problem."
    assert exc.hints == ("This answer uses x.",)


def test_i_is_only_imaginary_when_the_card_says_so() -> None:
    assert error("2i", X).hints[0].startswith("i isn't the imaginary unit")
    assert text("2i", Vocabulary(imaginary=True)) == "2*i"


def test_e_is_always_eulers_number() -> None:
    parsed = parse("e", Vocabulary(frozenset({"e"}), open_vars=True))
    assert parsed.alternatives[0][0] == n.Const("e")


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "x +", "(x", "x)", "|x", "x^^2", "@", "x $", "2.", "1.2.3", "05", "log_1(x)",
     "root(x)", "sin()", "[1]", "x == 2", "=3", "----x", "1⁄2"],  # noqa: RUF001
)  # fmt: skip
def test_syntax_errors(raw: str) -> None:
    assert error(raw).kind in {"syntax", "limit"}


def test_input_limits() -> None:
    assert error("1+" * 200 + "1").kind == "limit"  # 401 characters
    assert parse("1+" * 199 + "1", OPEN)  # 399 is fine
    deep = "(" * (MAX_DEPTH + 1) + "x" + ")" * (MAX_DEPTH + 1)
    assert error(deep).kind == "limit"
    assert parse("(" * MAX_DEPTH + "x" + ")" * MAX_DEPTH, OPEN)
    assert error("2^" * 13 + "2").kind == "limit"
    assert error("x^1001").kind == "limit"
    assert error("2^(10^10)").kind == "limit"
    assert parse("x^1000", OPEN)
    assert len("1+" * 200 + "1") == MAX_CHARS + 1


def test_long_sums_stay_flat() -> None:
    parsed = parse("+".join(["x"] * 150), OPEN)
    node = parsed.alternatives[0][0]
    assert isinstance(node, n.Sum)
    assert len(node.terms) == 150


def test_abs_bars_pair_up() -> None:
    node = parse("|x - |y||", OPEN).alternatives[0][0]
    assert node == n.Call("abs", (n.Sum((("+", n.Var("x")), ("-", n.Call("abs", (n.Var("y"),))))),))


def test_points_and_intervals_share_syntax() -> None:
    node = parse("(1, 2)", OPEN).alternatives[0][0]
    assert node == n.Tuple((n.Num("1"), n.Num("2")), "(", ")")
