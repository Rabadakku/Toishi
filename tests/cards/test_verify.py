"""MATH-17 and DEV-18 at pack build: worked solutions are machine-checked, keys cross-checked."""

import pytest

from core.cards.load import Source
from core.cards.mepack import PackBuild, PackMeta, check_pack

SKILLS = "---\nformat: mastery-skills 1\ndeck: P::U::S\n---\n\n## Skill p.a\nname: A\n"
HEAD = "---\nformat: mastery-cards 1\ndeck: P::U::S\nsource: original\nlicense: personal\n---\n"


def card(answer: str, steps: str, *, cid: str = "p.c.001", extra: str = "") -> str:
    return f"""
## Card {cid}
skill: p.a
difficulty: 1
answer-type: expression
answer: {answer}
{extra}
### Question
Q \\(f(x) = x^4 - 2x^2\\)

### Hints
1. H

### Solution
{steps}
"""


GOOD = """0. [p.a] Set up: differentiate.
1. [p.a] Differentiate: \\(f'(x) = 4x^3 - 4x\\).
   check: diff(x^4 - 2x^2, x) = 4x^3 - 4x
2. [p.a] Factor: \\(f'(x) = 4x(x - 1)(x + 1)\\).
   check: 4x^3 - 4x = 4x(x - 1)(x + 1)"""


def build(*cards: str) -> PackBuild:
    meta = PackMeta("p", "P", "1.0.0", "personal")
    source = Source("p.cards.md", HEAD + "".join(cards))
    return check_pack(meta, [source], [Source("skills.md", SKILLS)], built_at=1)


def test_checked_steps_and_final_line_pass_and_are_not_displayed() -> None:
    result = build(card("4x(x-1)(x+1)", GOOD))
    assert result.ok, result.report()
    assert result.unverified == []
    assert any("2 step checks hold, 1 final lines match the key" in c for c in result.checks)
    steps = result.cards[0].solution
    assert all("check:" not in s.body_md for s in steps)
    assert steps[1].body_md == "\\(f'(x) = 4x^3 - 4x\\)."


def test_a_wrong_step_is_an_error() -> None:
    wrong = GOOD.replace(
        "check: diff(x^4 - 2x^2, x) = 4x^3 - 4x", "check: diff(x^4 - 2x^2, x) = 4x^3 - 2x"
    )
    result = build(card("4x(x-1)(x+1)", wrong))
    assert any("solution step 1: check" in e and "is false" in e for e in result.errors)


def test_a_wrong_key_is_caught_by_the_final_line() -> None:
    result = build(card("4x(x-1)(x-1)", GOOD))  # a seeded wrong key
    assert any("final line" in e and "does not match the key" in e for e in result.errors)


def test_unchecked_math_is_reported_as_unverified() -> None:
    steps = GOOD.rsplit("\n", 1)[0] + "\n3. [p.a] Note: \\(x^2 \\ge 0\\) here."
    result = build(card("4x(x-1)(x+1)", steps))
    assert result.ok, result.report()
    assert result.unverified, result.report()
    assert "steps 2, 3 have no check" in result.unverified[0]
    assert "final line could not be matched" in result.unverified[0]


def test_the_final_line_is_read_from_the_last_math_without_a_claim() -> None:
    steps = "0. [p.a] Set up: differentiate.\n1. [p.a] Differentiate: \\(f'(x) = 4x^3 - 4x\\)."
    result = build(card("4x^3 - 4x", steps))
    assert result.ok, result.report()
    assert result.unverified == []
    result = build(card("4x^3 - 2x", steps))  # not matched: reported, not passed
    assert result.ok
    assert "final line could not be matched" in result.unverified[0]


def test_sets_limits_and_integrals_in_claims() -> None:
    steps = """0. [p.a] Set up: solve f'(x) = 0.
1. [p.a] Solve: \\(x = -1, 0, 1\\).
   check: limit(sin(x)/x, x, 0) = 1
   check: integrate(2x, x, 0, 3) = 9
   check: solve(4x^3 - 4x, x) = {-1, 0, 1}"""
    text = card("-1, 0, 1", steps).replace("answer-type: expression", "answer-type: set")
    result = build(text)
    assert result.ok, result.report()
    assert result.unverified == []


def test_a_claim_that_is_not_an_equality_is_an_error() -> None:
    steps = GOOD.replace("check: 4x^3 - 4x = 4x(x - 1)(x + 1)", "check: 4x^3 - 4x")
    result = build(card("4x(x-1)(x+1)", steps))
    assert any("is not an equality" in e for e in result.errors)


TEMPLATE = """
## Card p.t.t01
skill: p.a
difficulty: 1
answer-type: expression
vars: k = int(2, 4)
answer: diff(k*x^3, x)

### Question
Q \\(f(x) = [[k]]x^3\\)

### Hints
1. H

### Solution
0. [p.a] Set up: power rule.
1. [p.a] Differentiate: \\(f'(x) = [[diff(k*x^3, x)]]\\).
   check: diff(k*x^3, x) = 3*k*x^2
"""


def test_template_claims_hold_for_every_instance() -> None:
    result = build(TEMPLATE)
    assert result.ok, result.report()
    assert len(result.cards) == 3
    assert result.unverified == []


def test_a_template_claim_false_for_an_instance_rejects_the_template() -> None:
    result = build(TEMPLATE.replace("= 3*k*x^2", "= 9*x^2"))  # true only for k = 3
    assert any("check" in e and "is false" in e for e in result.errors), result.report()


@pytest.mark.parametrize("bad", ["solve(x^2 - 4, x) = {2}", "diff(sin(x^2), x) = cos(x^2)"])
def test_claims_are_checked_against_mpmath_too(bad: str) -> None:
    steps = f"0. [p.a] Set up: go.\n1. [p.a] Work: \\(x\\).\n   check: {bad}"
    result = build(card("x", steps))
    assert any("solution step 1" in e for e in result.errors), result.report()


def test_the_build_reports_differential_checks() -> None:
    result = build(card("4x(x-1)(x+1)", GOOD))
    assert any(c.startswith("differential checks (DEV-18)") for c in result.checks)
