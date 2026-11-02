"""ENG-16 method-choice skills, which-method and find-the-error items, self-graded problems."""

from dataclasses import replace

import pytest

from core.engine import rate
from core.engine.config import AGAIN, EASY, GOOD, HARD
from core.engine.diagnosis import (
    find_error_highlighted,
    find_error_slot_open,
    find_error_unlocked,
    grade_find_error,
    method_choice_active,
    method_choice_skill,
    self_graded_facts,
)
from core.engine.rating import RatingRules
from tests.engine.diagnosis.fixtures import ALG, CRIT, MC, POW, PROD, QUOT, answer, seed, world
from tests.engine.diagnosis.memory import MemoryWorld, ref_of
from tests.engine.helpers import at_day, some

T = at_day(0)


def mc_world(*, mc_days_ago: float = 12, quot: bool = True) -> MemoryWorld:
    w = world()
    for k in (ALG, POW):
        seed(w, k, stability=30, days_ago=3, theta=2.0)
    seed(w, PROD, stability=15, days_ago=16, theta=2.0)
    if quot:
        seed(w, QUOT, stability=15, days_ago=16, theta=2.0)
    seed(w, MC, stability=5, days_ago=mc_days_ago, theta=1.0)
    return w


def test_method_choice_skill_is_active_once_two_methods_are_learned() -> None:
    w = mc_world(quot=False)
    mc = some(method_choice_skill(PROD, w.skills()))
    assert mc.id == MC
    assert not method_choice_active(mc, w.state)
    seed(w, QUOT, stability=15, days_ago=1)
    assert method_choice_active(mc, w.state)
    assert method_choice_skill(CRIT, w.skills()) is None


def test_uncued_problem_counts_toward_a_due_method_choice_skill() -> None:
    w = mc_world()
    w.grade(answer(w, "c.prod.t2.0", T, correct=True))
    (event,) = w.events_for(MC)
    assert event.rating == GOOD
    assert event.predicted_recall is not None
    # A miss whose tap shows the method was chosen right counts as a right choice too.
    w2 = mc_world()
    w2.grade(answer(w2, "c.prod.t2.0", T, correct=False, choice="step", step=2))
    assert [e.rating for e in w2.events_for(MC)] == [GOOD]


def test_cued_problems_and_not_due_or_inactive_skills_do_not_count() -> None:
    w = mc_world()
    w.grade(answer(w, "c.prod.t2.0", T, correct=True, extra={"cued": True}))
    assert w.events_for(MC) == []
    w = mc_world(mc_days_ago=0.5)  # reviewed yesterday: not due
    w.grade(answer(w, "c.prod.t2.0", T, correct=True))
    assert w.events_for(MC) == []
    w = mc_world(quot=False)
    w.grade(answer(w, "c.prod.t2.0", T, correct=True))
    assert w.events_for(MC) == []


def test_step0_miss_leaves_the_method_choice_review_to_the_cued_twin() -> None:
    w = mc_world()
    w.grade(answer(w, "c.prod.t2.0", T, correct=False, choice="setup", didnt_know_start=True))
    assert w.events_for(MC) == []


def test_which_method_item_is_a_review_of_the_method_choice_skill() -> None:
    w = mc_world()
    w.grade(answer(w, "mc.0", T, correct=True))
    assert [e.rating for e in w.events_for(MC)] == [GOOD]
    assert w.events_for(PROD) == []


# ---------------------------------------------------------------- find-the-error


def test_find_the_error_unlocks_after_two_successful_uncued_reviews() -> None:
    w = mc_world()
    seed(w, CRIT, stability=20, days_ago=25, theta=2.0)
    w.grade(answer(w, "crit.t2.0", T, correct=True, extra={"cued": True}))
    seed(w, CRIT, stability=20, days_ago=25, at=T + 86_400_000, theta=2.0)
    w.grade(answer(w, "crit.t2.1", T + 86_400_000, correct=True))
    assert not find_error_unlocked(w.history(CRIT))
    seed(w, CRIT, stability=20, days_ago=25, at=T + 2 * 86_400_000, theta=2.0)
    w.grade(answer(w, "crit.t2.2", T + 2 * 86_400_000, correct=True))
    assert find_error_unlocked(w.history(CRIT))


def test_find_the_error_comes_at_most_once_in_n_reviews() -> None:
    recent = ["problem"] * 3 + ["find-error"] + ["problem"] * 5
    assert not find_error_slot_open(recent, 10)  # type: ignore[arg-type]
    assert find_error_slot_open(recent, 6)  # type: ignore[arg-type]
    assert not find_error_slot_open(["problem"] * 20, None)


@pytest.mark.parametrize(
    ("step", "reason", "value", "correct"),
    [(2, 1, True, True), (1, 1, True, False), (2, 0, True, False), (2, 1, False, False)],
)
def test_find_the_error_is_graded_on_step_reason_and_value(
    step: int, reason: int, value: bool, correct: bool
) -> None:
    card = some(world().card("crit.fe"))
    assert grade_find_error(card, step=step, reason=reason, value_correct=value).correct is correct


def test_find_the_error_counts_as_a_review_and_is_highlighted_early() -> None:
    w = mc_world()
    seed(w, CRIT, stability=20, days_ago=25, theta=2.0)
    assert find_error_highlighted(w.history(CRIT))
    card = some(w.card("crit.fe"))
    facts = grade_find_error(card, step=2, reason=1, value_correct=True).facts()
    outcome = replace(answer(w, "crit.fe", T, correct=True), facts=facts)
    w.grade(outcome)
    assert [e.rating for e in w.events_for(CRIT)] == [GOOD]
    assert ref_of(card).kind == "find-error"


# ---------------------------------------------------------------- self-graded problems


@pytest.mark.parametrize(
    ("ticked", "rating"), [(4, GOOD), (3, HARD), (2, AGAIN), (0, AGAIN), (9, GOOD)]
)
def test_rubric_ticks_map_to_good_hard_again(ticked: int, rating: int) -> None:
    facts = self_graded_facts(rubric_total=4, rubric_ticked=ticked)
    assert rate(facts, None, RatingRules()).rating == rating


@pytest.mark.parametrize(
    ("choice", "rating"), [("matched", GOOD), ("minor-slip", AGAIN), ("missed", AGAIN)]
)
def test_without_a_rubric_matched_minor_slip_didnt_get_it(choice: str, rating: int) -> None:
    facts = self_graded_facts(choice=choice)  # type: ignore[arg-type]
    decision = rate(facts, None, RatingRules())
    assert decision.rating == rating
    assert decision.rating != EASY
