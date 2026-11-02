"""Every example in docs/card-format.md imports exactly."""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from core.cards import LoadResult, Source, load
from core.cards.skillfile import read_skills, read_skills_file
from core.model import Card, Choice, PackPace, PackPaceSection, SolutionStep, WrongAnswer
from tests.cards.helpers import HEADER, only_card

DOC = Path(__file__).resolve().parents[2] / "docs" / "card-format.md"


def examples() -> list[str]:
    return re.findall(r"```text\n(.*?)```", DOC.read_text(), re.DOTALL)


def example(first_line: str) -> str:
    found = [b for b in examples() if b.lstrip().startswith(first_line)]
    assert len(found) == 1, first_line
    return found[0]


def test_every_text_block_is_checked() -> None:
    starts = sorted(b.split("\n", 1)[0] for b in examples())
    assert starts == sorted(
        [
            "---",  # file layout
            "### Solution",  # step-tagged solution
            "## Card calc1.4-1.crit-cubic.t01",  # variant
            "---",  # skills file
            "---",  # example file
        ]
    )


def test_file_layout_example() -> None:
    block = next(b for b in examples() if "crit-numbers.001" in b)
    card = only_card(load([Source("layout.cards.md", block)]))
    assert card.id == "calc1.4-1.crit-numbers.001"
    assert card.skill_id == "calc1.extrema.critical-numbers"
    assert card.tier == 2
    assert card.answer_type == "set"
    assert card.answer == "-1, 0, 1"
    assert card.wrong == (
        WrongAnswer(answer="0, 1", feedback="x + 1 = 0 gives a critical number too", step=3),
    )
    assert (
        card.deck == "Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values"
    )
    assert card.section_id == card.deck
    assert card.provenance.source == "original"
    assert card.provenance.license == "personal"
    assert card.question_md == r"Find all critical numbers of \(f(x) = x^4 - 2x^2\)."
    assert [s.number for s in card.solution] == [0, 1, 2, 3]
    assert card.solution[1] == SolutionStep(
        number=1,
        skill_id="calc1.deriv.power-rule",
        label="Differentiate",
        body_md=r"\(f'(x) = 4x^3 - 4x\).",
    )
    assert card.solution_md is None


def test_step_tagged_solution_example() -> None:
    body = "## Card ex.steps.001\nskill: calc1.extrema.critical-numbers\n\n### Question\nQ?\n\n"
    card = only_card(load([Source("steps.cards.md", HEADER + body + example("### Solution"))]))
    assert [(s.number, s.skill_id, s.label) for s in card.solution] == [
        (0, "calc1.extrema.critical-numbers", "Set up"),
        (1, "calc1.deriv.power-rule", "Differentiate"),
        (2, "alg.factor.polynomials", "Factor"),
    ]
    assert card.solution[0].body_md == "critical numbers are where f' is zero or undefined."


def test_variant_example() -> None:
    result = load(
        [Source("variant.cards.md", HEADER + example("## Card calc1.4-1.crit-cubic.t01"))]
    )
    assert not result.errors()
    info = result.templates["calc1.4-1.crit-cubic.t01"]
    assert info.combinations == 9
    by_k = {}
    for accepted in result.cards:
        card = accepted.card
        assert card.params is not None
        k = int(card.params.removeprefix("k = "))
        assert card.notes_md is None
        by_k[k] = card
        assert card.id == f"calc1.4-1.crit-cubic.t01--{card.seed:08x}"
        assert card.template_id == "calc1.4-1.crit-cubic.t01"
        assert card.answer == f"-{k}, {k}"
        assert card.tier == 1
        assert card.answer_type == "set"
        assert card.checker.vars is None  # the parameters are not stored with the instance
    assert sorted(by_k) == list(range(1, 10))
    assert by_k[1].question_md == r"Find all critical numbers of \(f(x) = x^{3} - 3 x\)."
    assert by_k[2].question_md == r"Find all critical numbers of \(f(x) = x^{3} - 12 x\)."
    assert by_k[3].solution_md == (
        r"\(f'(x) = 3x^2 - 27 = 3(x - 3)(x + 3)\), defined everywhere and zero at \(x = \pm 3\)."
    )


def test_skills_file_example() -> None:
    entries, problems = read_skills_file(example("---\nformat: mastery-skills 1"), "skills.md")
    assert problems == []
    (entry,) = entries
    skill = entry.skill
    assert skill.id == "calc1.extrema.critical-numbers"
    assert skill.name == "Find critical numbers"
    assert skill.requires == (
        "calc1.deriv.power-rule",
        "alg.factor.polynomials",
        "alg.solve.polynomial",
    )
    assert skill.encompasses == (("calc1.deriv.power-rule", 0.5), ("alg.factor.polynomials", 0.5))
    assert skill.confusable == ("calc1.shape.inflection-points",)
    assert skill.textbook_ref == "Stewart 4.1"
    assert (
        skill.section_id
        == "Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values"
    )
    assert not skill.method_choice
    assert not skill.core
    assert skill.exam_tier is None
    _, pace, _ = read_skills(example("---\nformat: mastery-skills 1"), "skills.md")
    assert pace is not None
    assert pace.standard() == PackPace(
        minutes_per_step=1.5,
        weekly_hours=3.0,
        sections=(PackPaceSection(deck=skill.section_id, hours=2.0),),
    )


def component_warnings(result: LoadResult) -> list[str]:
    return [w.message for w in result.warnings if "tagged" in w.message or "step tags" in w.message]


def test_the_examples_follow_the_component_rule(sample: Sample) -> None:
    block = next(b for b in examples() if "crit-numbers.001" in b)
    layout = load([Source("layout.cards.md", block)])
    assert only_card(layout).uses == (
        "calc1.deriv.power-rule",
        "alg.factor.polynomials",
        "alg.solve.polynomial",
    )
    assert component_warnings(layout) == []
    assert component_warnings(sample.result) == []


@dataclass
class Sample:
    result: LoadResult
    cards: dict[str, Card]


@pytest.fixture(scope="module")
def sample() -> Sample:
    block = next(b for b in examples() if "calc1.4-4.method-limit.001" in b)
    result = load([Source("calc1-ch4-sample.cards.md", block)])
    assert not result.errors(), result.errors()
    return Sample(result, {a.card.template_id or a.card.id: a.card for a in result.cards})


def test_example_file_imports_every_card(sample: Sample) -> None:
    ids = sorted(sample.cards)
    assert ids == [
        "calc1.3-4.chain-error.001",
        "calc1.4-1.crit-abs.001",
        "calc1.4-1.crit-cubic.t01",
        "calc1.4-2.mvt-statement.001",
        "calc1.4-3.cubic-shape.001",
        "calc1.4-4.method-limit.001",
    ]


def test_example_minimal_card(sample: Sample) -> None:
    card = sample.cards["calc1.4-1.crit-abs.001"]
    assert card.kind == "problem"
    assert card.answer_type == "self"
    assert card.answer is None
    assert (
        card.deck == "Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values"
    )
    assert card.solution == ()
    assert str(card.solution_md).startswith(r"\(0\) is in the domain")


def test_example_multipart(sample: Sample) -> None:
    card = sample.cards["calc1.4-3.cubic-shape.001"]
    assert card.tier == 3
    assert card.uses == (
        "calc1.deriv.power-rule",
        "alg.factor.polynomials",
        "calc1.shape.inflection-points",
    )
    parts = card.parts
    assert [(p.label, p.answer_type, p.answer) for p in parts] == [
        ("a", "interval", "(-inf, 0) U (2, inf)"),
        ("b", "point", "(0, 0)"),
        ("c", "point", "(2, -4)"),
        ("d", "point", "(1, -2)"),
    ]
    assert parts[0].checker.endpoints == "either"
    assert parts[0].prompt_md == r"On what intervals is \(f\) increasing?"
    assert parts[3].skill_id == "calc1.shape.inflection-points"
    assert card.hints == (
        r"Find where \(f'(x) > 0\).",
        r"\(f'(x) = 3x(x - 2)\). Make a sign chart.",
    )
    assert [s.number for s in card.solution] == [0, 1, 2, 3, 4, 5]


def test_example_flashcard(sample: Sample) -> None:
    card = sample.cards["calc1.4-2.mvt-statement.001"]
    assert card.kind == "flashcard"
    assert card.front_md == "State the Mean Value Theorem."
    assert str(card.back_md).endswith(r"\[ f'(c) = \frac{f(b) - f(a)}{b - a}. \]")


def test_example_variant(sample: Sample) -> None:
    instances = [
        a.card for a in sample.result.cards if a.card.template_id == "calc1.4-1.crit-cubic.t01"
    ]
    assert len(instances) == 9
    assert {c.answer for c in instances} == {f"-{k}, {k}" for k in range(1, 10)}
    k5 = next(c for c in instances if c.answer == "-5, 5")
    assert k5.solution[1].body_md == r"\(f'(x) = 3x^2 - 75\)."
    assert k5.solution[2].body_md == r"\(f'(x) = 3(x - 5)(x + 5)\)."


def test_example_find_error(sample: Sample) -> None:
    card = sample.cards["calc1.3-4.chain-error.001"]
    assert card.kind == "find-error"
    assert card.error_step == 2
    assert card.answer_type == "expression"
    assert card.answer == "6x(x^2 + 1)^2"
    assert [s.number for s in card.shown_work] == [1, 2, 3]
    assert [r.correct for r in card.reasons] == [False, True, False]


def test_example_method(sample: Sample) -> None:
    card = sample.cards["calc1.4-4.method-limit.001"]
    assert card.kind == "method"
    assert card.answer_type == "choice"
    assert card.choices[3] == Choice(
        text_md="L'Hôpital's rule, or the known limit of sin(u)/u", correct=True
    )
    assert str(card.deck).endswith("4.4 Indeterminate Forms and l'Hospital's Rule")
