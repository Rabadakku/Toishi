"""One test per row of the "What went wrong?" table, plus checks, holds and slips."""

from datetime import date, timedelta

import pytest

from core.engine.config import AGAIN, DAY_MS, GOOD
from core.engine.diagnosis import hold_of
from core.engine.diagnosis.verdict import EXAMPLE_FIRST
from core.engine.lifecycle import due_day
from tests.engine.diagnosis.fixtures import (
    ALG,
    CRIT,
    MC,
    POW,
    PROD,
    QUOT,
    answer,
    seed,
    world,
)
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import DAYS, at_day, some

T = at_day(0)
MIN = 60_000


def base() -> MemoryWorld:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0)
    return w


def miss(w: MemoryWorld, card: str = "crit.t2.0", at: int = T, **kw: object) -> None:
    w.grade(answer(w, card, at, correct=False, **kw))  # type: ignore[arg-type]


def due(w: MemoryWorld, skill: str) -> date | None:
    return due_day(w.states[skill], 0.9, w.fsrs, DAYS)


# ---------------------------------------------------------------- row: a step (tap it)


def test_step_tap_holds_the_rating_and_asks_for_a_check_three_items_later() -> None:
    w = base()
    miss(w, choice="step", step=2)
    assert w.last.rating is None
    assert w.events_for(CRIT) == []
    (check,) = w.pending()
    assert (check.skill_id, check.kind, check.attempt_id) == (ALG, "step", w.last.id)
    assert check.after_items >= 3
    assert check.not_before_at is None
    card = some(w.card(some(check.card_id)))
    assert card.skill_id == ALG
    assert card.tier <= 2
    reason = some(check.reason)  # on the check itself, not in the attempt's extra
    assert "reason" not in w.last.extra["diagnosis"]["checks"][0]
    assert "Critical numbers" in reason
    assert "Factor" in reason
    assert hold_of(w.states[CRIT]) is not None
    assert due(w, CRIT) == DAYS.day_of(T) + timedelta(days=1)  # not again today


def test_step_check_fails_the_tapped_skill_gets_again_and_its_prerequisites_checks() -> None:
    w = base()
    seed(w, ALG, stability=2, days_ago=20, theta=0.0)  # low recall: gets a check
    miss(w, choice="step", step=1)  # tapped Differentiate: power rule
    (check,) = w.pending()
    assert check.skill_id == POW
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=False, check_of=check.id))
    assert w.checks[some(check.id)].status == "failed"
    assert [e.rating for e in w.events_for(POW)] == [AGAIN]
    (prereq,) = w.pending()
    assert (prereq.skill_id, prereq.kind, prereq.depth) == (ALG, "prerequisite", 1)
    # The problem's own skill keeps its miss (ADR-0014: an excused Again at the miss's
    # time, which Level and the leech counter ignore since the blame went to the power
    # rule), waits a day, and ENG-6 pulls it in: it encompasses the lapsed power rule.
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, T)]
    assert w.states[CRIT].level == "learned"
    assert w.states[CRIT].level_evidence["leech_base"] == 1
    assert hold_of(w.states[CRIT]) is None
    assert DAYS.day_of(T) < some(due(w, CRIT)) <= DAYS.day_of(T) + timedelta(days=2)


def test_step_check_passes_the_problem_skill_keeps_again_at_the_miss() -> None:
    # ADR-0014: the checked step holds, so the integration failed: the miss stays Again.
    w = base()
    miss(w, choice="step", step=2)
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=True, check_of=check.id))
    (event,) = w.events_for(CRIT)
    assert (event.rating, event.at, event.predicted_recall) == (AGAIN, T, None)
    assert hold_of(w.states[CRIT]) is None
    assert w.states[CRIT].fsrs_state == 3
    assert w.last.extra["diagnosis"]["resolved"]["confirmed"] is False


def test_tap_on_the_problems_own_step_settles_in_time_order() -> None:
    w = base()
    miss(w, choice="step", step=0)  # Step 0 tapped as a step: the card's own skill
    (check,) = w.pending()
    assert check.skill_id == CRIT
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=True, check_of=check.id))
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, T), (GOOD, T + 5 * MIN)]


def test_matched_wrong_answer_preselects_its_step_with_more_blame() -> None:
    w = base()
    miss(w, choice="step", step=2, matched=0)
    assert w.last.extra["diagnosis"]["blame"][ALG] == pytest.approx(0.8)


# ---------------------------------------------------------------- row: Step 0


def method_world() -> MemoryWorld:
    w = base()
    for k in (PROD, QUOT):
        seed(w, k, stability=15, days_ago=16, theta=1.0)
    seed(w, MC, stability=10, days_ago=2, theta=0.5)
    return w


def test_step0_solved_twin_is_a_method_choice_gap() -> None:
    w = method_world()
    miss(w, "c.prod.t2.0", choice="setup", didnt_know_start=True)
    (twin,) = w.pending()
    assert (twin.skill_id, twin.kind) == (PROD, "cued-twin")
    assert some(w.card(some(twin.card_id))).cued_question_md is not None
    w.grade(answer(w, some(twin.card_id), T + 5 * MIN, correct=True, check_of=twin.id))
    assert [e.rating for e in w.events_for(MC)] == [AGAIN]
    # ADR-0014: the original miss stays Again (excused: the method choice failed), then
    # the twin's own review the same day.
    assert [(e.rating, e.at) for e in w.events_for(PROD)] == [(AGAIN, T), (GOOD, T + 5 * MIN)]
    assert w.states[PROD].level_evidence["leech_base"] == 1
    assert hold_of(w.states[PROD]) is None


def test_step0_unsolved_twin_lapses_the_skill_and_asks_for_a_worked_example() -> None:
    w = method_world()
    miss(w, "c.prod.t2.0", choice="setup", didnt_know_start=True)
    (twin,) = w.pending()
    w.grade(answer(w, some(twin.card_id), T + 5 * MIN, correct=False, check_of=twin.id))
    assert [e.rating for e in w.events_for(PROD)] == [AGAIN, AGAIN]  # the miss, the twin
    assert w.states[PROD].lapses == 1  # the twin's same-day Again is no second lapse
    assert "leech_base" not in w.states[PROD].level_evidence  # its own miss: not excused
    assert w.events_for(MC) == []
    assert w.states[PROD].level_evidence.get(EXAMPLE_FIRST) is True


# ---------------------------------------------------------------- rows: slips and misreads


def strong(w: MemoryWorld, skill: str = CRIT) -> None:
    seed(w, skill, stability=60, days_ago=2, theta=2.0)
    for i in range(2):  # its last two attempts correct
        w.grade(answer(w, f"crit.t3.{i + 3}", T - (40 - i) * DAY_MS, correct=True))
    seed(w, skill, stability=60, days_ago=2, theta=2.0)


@pytest.mark.parametrize("choice", ["slip", "misread"])
def test_slip_on_a_strong_skill_is_an_excused_again(choice: str) -> None:
    w = base()
    strong(w)
    level = w.states[CRIT].level
    miss(w, "crit.t3.0", choice=choice)
    assert [e.rating for e in w.events_for(CRIT) if e.at == T] == [AGAIN]
    assert w.last.extra["slip"] is True
    assert w.states[CRIT].level == level  # Level ignores it ...
    assert w.states[CRIT].level_evidence["leech_base"] == 1  # ... and so do leeches
    assert w.pending() == []
    assert w.last.extra["diagnosis"]["slip"] == "accepted"
    # A confident slip still guarantees the next-day redo.
    redo = w.card_users["crit.t3.0"]
    assert redo.redo_guaranteed
    assert DAYS.day_of(some(redo.redo_due_at)) == DAYS.day_of(T) + timedelta(1)


def test_slip_on_a_weak_skill_is_again() -> None:
    w = base()  # crit recall about 0.88 < 0.90
    miss(w, choice="slip")
    assert [e.rating for e in w.events_for(CRIT)] == [AGAIN]
    assert w.last.extra["diagnosis"]["slip"] == "rejected"
    assert w.pending() == []


def test_second_slip_within_30_days_becomes_a_step_error_with_a_check() -> None:
    w = base()
    strong(w)
    miss(w, "crit.t3.0", choice="slip")
    seed(w, CRIT, stability=60, days_ago=1, theta=2.0)
    miss(w, "crit.t3.1", at=T + 10 * DAY_MS, choice="misread")  # shares the limit
    assert w.last.extra["diagnosis"]["slip"] == "second"
    assert hold_of(w.states[CRIT]) is not None
    assert [c.kind for c in w.pending()] == ["step"]


def test_slip_cap_resets_after_30_days() -> None:
    w = base()
    strong(w)
    miss(w, "crit.t3.0", choice="slip")
    later = T + 31 * DAY_MS
    for i in range(2):
        w.grade(answer(w, f"crit.t3.{i + 4}", later - (2 - i) * DAY_MS, correct=True))
    seed(w, CRIT, stability=60, days_ago=1, at=later, theta=2.0)
    miss(w, "crit.t3.2", at=later, choice="slip")
    assert w.last.extra["diagnosis"]["slip"] == "accepted"


# ---------------------------------------------------------------- rows: other method, can't tell


def test_different_valid_method_lapses_the_skill_without_step_blame() -> None:
    w = base()
    miss(w, choice="other-method")
    assert [e.rating for e in w.events_for(CRIT)] == [AGAIN]
    assert w.last.extra["diagnosis"]["blame"] == {CRIT: 1.0}
    assert w.pending() == []


def test_cant_tell_lapses_without_a_check() -> None:
    w = base()
    miss(w, choice="cant-tell")
    assert [e.rating for e in w.events_for(CRIT)] == [AGAIN]
    assert w.states[CRIT].lapses == 1
    assert w.pending() == []


# ---------------------------------------------------------------- above-level misses


def test_above_level_miss_whose_check_passes_is_a_plain_again() -> None:
    # ADR-0019 item 4: a passed step check is an integration error; it counts.
    w = base()
    seed(w, CRIT, stability=20, days_ago=25, theta=-1.5)  # tier 2 predicted about 0.27
    miss(w, choice="cant-tell")
    assert w.last.extra["diagnosis"]["above_level"] is True
    (check,) = w.pending()
    assert check.skill_id == CRIT
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=True, check_of=check.id))
    assert next(e.rating for e in w.events_for(CRIT)) == AGAIN
    assert "leech_base" not in w.states[CRIT].level_evidence


def test_above_level_miss_whose_check_fails_is_again() -> None:
    w = base()
    seed(w, CRIT, stability=20, days_ago=25, theta=-1.5)
    miss(w, choice="cant-tell")
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=False, check_of=check.id))
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, T), (AGAIN, T + 5 * MIN)]
    assert w.states[CRIT].lapses == 1


# ---------------------------------------------------------------- holds that never meet a check


def test_a_held_miss_served_again_first_settles_as_again() -> None:
    w = base()
    miss(w, choice="step", step=2)
    tomorrow = T + DAY_MS
    w.grade(answer(w, "crit.t2.3", tomorrow, correct=True))
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, T), (GOOD, tomorrow)]
    assert hold_of(w.states[CRIT]) is None
    # The check still resolves later; it only feeds the tap log now.
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), tomorrow + MIN, correct=True, check_of=check.id))
    assert len(w.events_for(CRIT)) == 2


def test_unserved_checks_expire_after_a_week() -> None:
    w = base()
    miss(w, choice="step", step=2)
    report = w.daily(T + 8 * DAY_MS)
    assert [c.status for c in report.expired] == ["cancelled"]
    assert w.pending() == []


def test_checks_are_matched_by_card_when_the_queue_gives_no_check_id() -> None:
    w = base()
    miss(w, choice="step", step=2)
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=True))
    assert w.checks[some(check.id)].status == "passed"


def test_learning_failure_and_leech_ask_for_prerequisite_checks() -> None:
    w = base()
    seed(w, ALG, stability=1, days_ago=30, theta=0.0)
    w.states.pop(CRIT)
    for i in range(6):  # 6 misses in the learning phase: the phase fails
        w.grade(answer(w, f"crit.t1.{i}", T + i * MIN, correct=False))
    kinds = {(c.skill_id, c.kind) for c in w.pending()}
    assert (POW, "prerequisite") in kinds
    assert (ALG, "prerequisite") in kinds
    deepest = min(w.pending(), key=lambda c: c.after_items)
    assert deepest.skill_id == ALG  # ALG is under POW: deepest first


def test_no_check_problem_available_leaves_the_rating_map_alone() -> None:
    w = MemoryWorld(
        [s for s in world().skills().values()],
        [c for c in world()._cards.values() if c.skill_id != ALG],
    )
    seed(w, ALG, stability=30, days_ago=3)
    seed(w, POW, stability=30, days_ago=3)
    seed(w, CRIT, stability=20, days_ago=25)
    miss(w, choice="step", step=2)
    assert [e.rating for e in w.events_for(CRIT)] == [AGAIN]
    assert w.last.extra["diagnosis"]["check"] == "no problem available"


def test_confident_error_guarantees_the_next_day_redo() -> None:
    w = base()
    miss(w, choice="cant-tell")
    redo = w.card_users["crit.t2.0"]
    assert redo.redo_guaranteed
    assert DAYS.day_of(some(redo.redo_due_at)) == DAYS.day_of(T) + timedelta(days=1)
    w2 = base()
    miss(w2, choice="cant-tell", unsure=True)
    assert not w2.card_users["crit.t2.0"].redo_guaranteed


def test_level_waits_for_the_verdict_of_the_check() -> None:
    w = base()
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0, level="exam")
    miss(w, choice="step", step=2)
    assert not w.states[CRIT].shaky  # held: no Level evidence yet
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), T + 5 * MIN, correct=False, check_of=check.id))
    assert not w.states[CRIT].shaky  # traced to the factoring step: an excused Again
    assert w.states[CRIT].level == "exam"
    w2 = base()
    seed(w2, CRIT, stability=20, days_ago=25, theta=1.0, level="exam")
    miss(w2, choice="cant-tell")
    assert w2.states[CRIT].shaky  # a plain lapse marks it shaky at once
