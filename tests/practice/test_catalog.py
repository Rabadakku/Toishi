"""core/practice/catalog.py: components, problems and courses from the loaded content."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from core.learner.types import ComponentInfo
from core.model import CardMark
from core.practice import Textbook, build_catalog, problem_specs, textbook_of
from core.practice.engine import PracticeEngine
from tests.practice.helpers import COURSE, O1, OTHER, S0, S1, S2, World, card, make_world


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path)
    yield w
    w.storage.close(backup=False)


def test_components_are_course_or_background(world: World) -> None:
    catalog = build_catalog(world.storage)
    assert catalog.components["c.limit"] == ComponentInfo("c.limit", False, COURSE)
    assert catalog.components["o.thing"] == ComponentInfo("o.thing", False, OTHER)
    # alg. prefix: a prerequisite from earlier courses, even inside the course's own sections
    assert catalog.components["alg.factor"] == ComponentInfo("alg.factor", True, COURSE)


def test_a_problem_lists_its_skill_then_uses_and_step_tags_once(world: World) -> None:
    catalog = build_catalog(world.storage)
    p = catalog.problems["c.limit.t3.v1"]
    assert (p.card_id, p.part, p.main_skill) == ("c.limit.t3.v1", None, "c.limit")
    assert p.components == ("c.limit", "alg.factor")
    assert (p.tier, p.steps) == (3, 3)
    assert p.standard_minutes == pytest.approx(0.5 + 2.0 * 3)  # the pack's 2 minutes a step
    assert p.wrong_components == ((0, "alg.factor"),)  # "7 @2"; "8" names no step
    assert p.family == "c.limit.tm3"  # template instances share their template's family
    tier4 = catalog.problems["c.limit.t4.v0"]
    assert tier4.standard_minutes == pytest.approx(0.5 + 2.0 * 3 + 2.0)
    assert catalog.problems["alg.factor.t2.v0"].family == "alg.factor.t2.v0"


def test_multi_part_cards_give_a_problem_per_part(world: World) -> None:
    catalog = build_catalog(world.storage)
    a, b = catalog.by_card["c.multi"]
    assert (a.problem_id, a.part, a.main_skill) == ("c.multi#a", "a", "c.limit")
    assert a.components == ("c.limit", "alg.factor")  # not part b's own skill
    assert a.wrong_components == ((0, "alg.factor"),)
    assert (b.problem_id, b.main_skill, b.components) == ("c.multi#b", "c.squeeze", ("c.squeeze",))
    assert a.standard_minutes == pytest.approx(b.standard_minutes)
    assert a.standard_minutes * 2 == pytest.approx(0.5 + 2.0 * 2)
    assert catalog.problem("c.multi") is None
    assert catalog.problem("c.multi", "b") == b


def test_pools_leave_out_retired_cards_and_other_kinds(world: World) -> None:
    catalog = build_catalog(world.storage)
    assert "c.limit.retired" not in catalog.problems
    assert "c.limit.ex" not in catalog.problems
    assert catalog.examples["c.limit"] == "c.limit.ex"


def test_a_course_with_pace_data(world: World) -> None:
    entry = build_catalog(world.storage).courses[COURSE]
    course = entry.course
    assert entry.has_pace
    assert entry.source == "pk"
    assert entry.title == "Calculus"
    assert [s.deck for s in course.standard.sections] == [S1, S2]
    assert course.standard.weekly_hours == 4.0
    assert course.standard.minutes_per_step == 2.0
    own = [s for s in course.skills if not s.background]
    assert [s.skill_id for s in own] == ["c.limit", "c.squeeze", "c.lhopital"]
    assert [s.order for s in course.skills] == list(range(len(course.skills)))
    limit = own[0]
    assert (limit.deck, limit.requires, limit.example_card) == (S1, ("alg.factor",), "c.limit.ex")
    assert {p.problem_id for p in limit.pool} >= {"c.limit.t1.v0", "c.multi#a"}
    assert own[1].confusable == ("c.lhopital",)
    background = [s for s in course.skills if s.background]
    assert [(s.skill_id, s.deck) for s in background] == [("alg.factor", S0)]
    assert len(background[0].pool) == 4
    assert [(s.deck, s.hours) for s in entry.sections] == [(S0, None), (S1, 4.0), (S2, 4.0)]


def test_a_pack_without_pace_data_introduces_every_section_on_the_anchor_day(
    tmp_path: Path,
) -> None:
    w = make_world(tmp_path, pace=False)
    try:
        entry = build_catalog(w.storage).courses[COURSE]
        assert not entry.has_pace
        assert [(s.deck, s.hours) for s in entry.course.standard.sections] == [
            (S0, 0.0),
            (S1, 0.0),
            (S2, 0.0),
        ]
        assert all(s.hours is None for s in entry.sections)
        assert build_catalog(w.storage).courses[OTHER].sections[0].deck == O1
    finally:
        w.storage.close(backup=False)


def test_textbook_pointers() -> None:
    assert textbook_of("OpenStax Calculus Vol 1 §4.3") == Textbook(
        "OpenStax Calculus Vol 1", "§4.3"
    )
    assert textbook_of("A §1; B §2") == Textbook("A", "§1")
    assert textbook_of("Stewart") == Textbook("Stewart", "")
    assert textbook_of(None) is None
    assert textbook_of("  ") is None


def test_skills_take_their_own_textbook_line_else_their_sections(world: World) -> None:
    catalog = build_catalog(world.storage)
    assert catalog.textbooks["c.squeeze"] == Textbook("Book Two", "§2.3")
    assert catalog.textbooks["c.limit"] == Textbook("Book One", "§1.1")  # its section's
    assert "c.lhopital" not in catalog.textbooks


def test_a_card_without_a_skill_is_its_own_component() -> None:
    lone = replace(card("mine.one", "mine.one", 2, steps=()), skill_id=None)
    (spec,) = problem_specs(lone, 1.5)
    assert (spec.main_skill, spec.components) == ("mine.one", ("mine.one",))


def test_the_engine_rebuilds_its_catalog_only_when_content_changes(world: World) -> None:
    engine = PracticeEngine(world.storage)
    first = engine.catalog()
    assert engine.catalog() is first
    world.storage.users.set_card_mark(CardMark(card_id="c.limit.t1.v0", suspended=True))
    assert engine.catalog() is first  # marks are passed to the planner, not rebuilt
    assert engine.unavailable() == frozenset({"c.limit.t1.v0"})
    world.storage.users.put_user_content(card("mine.limit.001", "c.limit", 2, steps=("c.limit",)))
    second = engine.catalog()
    assert second is not first
    assert "mine.limit.001" in second.problems
    assert S2 in {s.deck for s in second.courses[COURSE].course.standard.sections}
