"""A problem's components and the component a matched wrong answer points at (student-model
spec 2.1 and 2.3)."""

from core.cards.components import components, step_component, wrong_component
from core.grader import WrongAnswer as GraderWrongAnswer
from core.model import Card
from core.queue.answers import check_answers, default_checker
from tests.cards.helpers import cards_file, load_text, only_card

CARD = """
## Card c.001
skill: calc.crit
uses: calc.power, alg.factor
difficulty: 2
answer-type: set
answer: -1, 0, 1
wrong: 0, 1 => x + 1 = 0 gives one too. @2; -1, 1 => x = 0 is one too. @1; 2 => Not a root.

### Question
Find all critical numbers of \\(f(x) = x^4 - 2x^2\\).

### Hints
1. Differentiate.

### Solution
0. [calc.crit] Set up: critical numbers are where \\(f'\\) is zero or undefined.
1. [calc.power] Differentiate: \\(f'(x) = 4x^3 - 4x\\).
2. [alg.factor] Factor: \\(f'(x) = 4x(x - 1)(x + 1)\\), zero at \\(-1, 0, 1\\).
"""

PARTS = """
## Card c.parts.001
skill: calc.crit
uses: calc.power
difficulty: 2

### Question
Let \\(f(x) = x^2 - 2x\\).

### Part a
answer-type: expression
answer: 2x - 2
wrong: 2x => The derivative of -2x is -2. @1
Find \\(f'(x)\\).

### Part b
answer-type: number
answer: 1
skill: alg.solve
wrong: -1 => Solve 2x - 2 = 0. @2; 2 => Check the sign.
Find the critical number.

### Hints
1. Differentiate.

### Solution
0. [calc.crit] Set up: critical numbers are where \\(f'\\) is zero.
1. [calc.power] Differentiate: \\(f'(x) = 2x - 2\\).
2. [alg.solve] Solve: \\(2x - 2 = 0\\) at \\(x = 1\\).
"""


LOOSE = """
## Card c.loose.001

### Question
Explain why \\(0\\) is a critical number of \\(|x|\\).

### Solution
The slope jumps from \\(-1\\) to \\(1\\) at \\(0\\).
"""


def card_of(body: str) -> Card:
    return only_card(load_text(cards_file(body)))


def test_components_are_skill_uses_part_skills_and_step_tags_once() -> None:
    assert components(card_of(CARD)) == ("calc.crit", "calc.power", "alg.factor")
    assert components(card_of(PARTS)) == ("calc.crit", "calc.power", "alg.solve")
    assert components(card_of(LOOSE)) == ()  # no skill tags: scheduled on its own


def test_a_matched_wrong_answer_names_its_steps_component() -> None:
    card = card_of(CARD)
    assert wrong_component(card, 0) == "alg.factor"  # @2
    assert wrong_component(card, 1) == "calc.power"  # @1
    assert wrong_component(card, 2) is None  # no @step
    for nothing in (None, 3, -1):
        assert wrong_component(card, nothing) is None


def test_a_parts_wrong_answers_index_its_own_list() -> None:
    card = card_of(PARTS)
    assert wrong_component(card, 0, part="a") == "calc.power"
    assert wrong_component(card, 0, part="b") == "alg.solve"
    assert wrong_component(card, 1, part="b") is None  # no @step
    assert wrong_component(card, 1, part="a") is None  # part a lists one
    assert wrong_component(card, 0, part="z") is None
    assert wrong_component(card, 0) is None  # the card itself lists none


def test_step_component_takes_a_grader_wrong_answer() -> None:
    card = card_of(CARD)
    assert step_component(card, GraderWrongAnswer("0, 1", step=2).step) == "alg.factor"
    assert step_component(card, 0) == "calc.crit"
    assert step_component(card, None) is None
    assert step_component(card, 9) is None


def test_from_a_typed_answer_to_the_component() -> None:
    """The checker reports the match; the attempt keeps its index; the step gives the
    component."""
    card = card_of(CARD)
    checked = check_answers(card, [(None, "1, -1")], "text", default_checker)
    assert checked.matched_index == 1
    assert checked.matched_wrong == 1  # the step
    assert wrong_component(card, checked.matched_index) == "calc.power"
    right = check_answers(card, [(None, "0, 1, -1")], "text", default_checker)
    assert right.correct
    assert wrong_component(card, right.matched_index) is None
