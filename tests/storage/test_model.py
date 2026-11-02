from dataclasses import replace
from typing import Any

import pytest

from core.model import (
    DEFAULT_MINUTES_PER_STEP,
    Attempt,
    Card,
    CardMedia,
    CardPart,
    CourseGoal,
    PackPace,
    PackPaceSection,
    ReviewEvent,
    SessionState,
    ShapeError,
    Skill,
    SkillEdge,
    SkillState,
    SolutionStep,
    TemplateSource,
)
from tests.storage import data


def test_full_card_is_a_valid_shape() -> None:
    card = data.full_card()
    assert card.kind == "problem"
    assert not card.retired
    assert [s.number for s in card.solution] == [0, 1, 2]


@pytest.mark.parametrize(
    "changes",
    [
        {"id": "Calc1.Bad"},  # uppercase
        {"id": "has space"},
        {"tier": 6},
        {"kind": "essay"},
        {"answer_type": "vibes"},
        {"angles": "gradians"},
        {"rev": 0},
        {"status": "deleted"},
        {"error_step": -1},
        {"uses": ("Not An Id",)},
        {"solution": (SolutionStep(number=1, skill_id=None, label="a"),) * 2},
        {"template_id": None},  # it has parameters: only template instances do
        {"time_minutes": 0.0},
        {"time_minutes": -2.5},
        {"time_minutes": float("nan")},
        {"time_minutes": float("inf")},
    ],
)
def test_card_rejects_bad_shapes(changes: dict[str, Any]) -> None:
    with pytest.raises(ShapeError):
        replace(data.full_card(), **changes)


def test_part_times_and_pace_standards_are_checked() -> None:
    with pytest.raises(ShapeError, match="part time"):
        CardPart(label="a", prompt_md="P", time_minutes=0.0)
    assert PackPace() == PackPace(minutes_per_step=DEFAULT_MINUTES_PER_STEP)
    assert DEFAULT_MINUTES_PER_STEP == 1.5
    section = PackPaceSection(deck="C::U::S", hours=6.0)
    for bad in (
        lambda: PackPace(minutes_per_step=0.0),
        lambda: PackPace(weekly_hours=-1.0),
        lambda: PackPace(sections=(section, replace(section, hours=2.0))),  # twice
        lambda: PackPaceSection(deck="C::U::S", hours=0.0),
        lambda: PackPaceSection(deck=" ", hours=1.0),
    ):
        with pytest.raises(ShapeError):
            bad()


def test_card_needs_some_stem() -> None:
    with pytest.raises(ShapeError, match="question"):
        Card(id="x.1")
    assert Card(id="x.2", kind="flashcard", front_md="f").front_md == "f"
    assert Card(id="x.3", kind="cloze", text_md="{{c1::a}}").text_md


def test_skill_edges_are_checked() -> None:
    skill = data.skills()[0]
    kinds = [e.kind for e in skill.edges()]
    assert kinds == ["requires", "requires", "encompasses", "encompasses", "confusable"]
    with pytest.raises(ShapeError):
        Skill(id="a", name="A", encompasses=(("b", 0.3),))
    with pytest.raises(ShapeError):
        Skill(id="a", name="A", requires=("a",))
    with pytest.raises(ShapeError):
        SkillEdge(kind="requires", skill_id="a", other_id="b", weight=0.5)
    with pytest.raises(ShapeError):
        Skill(id="a", name=" ")


def test_user_records_check_enums_and_ranges() -> None:
    with pytest.raises(ShapeError):
        Attempt(card_id="c", verdict="maybe")  # type: ignore[arg-type]
    with pytest.raises(ShapeError):
        Attempt(card_id="c", verdict="correct", rating=5)
    with pytest.raises(ShapeError):
        Attempt(card_id="c", verdict="correct", attempt_number=0)
    with pytest.raises(ShapeError):
        Attempt(card_id="c", verdict="correct", study_day="2026-13-01")
    with pytest.raises(ShapeError):
        Attempt(card_id="c", verdict="correct", active_ms=-1)
    with pytest.raises(ShapeError):
        ReviewEvent(target_kind="skill", target_id="s", rating=0, rules_version="r1")
    with pytest.raises(ShapeError):
        SkillState(skill_id="s", fsrs_state=4)
    with pytest.raises(ShapeError):
        SkillState(skill_id="s", level="expert")  # type: ignore[arg-type]
    with pytest.raises(ShapeError):
        CourseGoal(course_id="c", goal="custom")
    with pytest.raises(ShapeError):
        CourseGoal(course_id="c", goal="A", custom_retention=0.9)
    with pytest.raises(ShapeError):
        SessionState(study_day="yesterday")
    assert CourseGoal(course_id="c", goal="custom", custom_retention=0.8).goal == "custom"


def test_v2_records_check_their_shape() -> None:
    assert TemplateSource(id="t.001", source_md="## Card t.001").updated_at == 0
    with pytest.raises(ShapeError):
        TemplateSource(id="Bad ID", source_md="x")
    with pytest.raises(ShapeError):
        TemplateSource(id="t.001", source_md=" ")
    assert CardMedia(card_id="c", ref="g.svg", file="f").ref == "g.svg"
    with pytest.raises(ShapeError):
        CardMedia(card_id="c", ref="", file="f")
