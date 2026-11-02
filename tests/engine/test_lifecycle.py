"""ENG-2 learning phase, ENG-3 lapses, ENG-9 leeches, provisional seeds — through grading."""

from dataclasses import replace

import pytest

from core.engine.config import AGAIN, GOOD, HARD, RULES_VERSION, EngineSettings
from core.engine.lifecycle import (
    RELEARNING,
    REVIEW,
    due_day,
    learning_step,
    memory_of,
    seed_provisional,
    start_learning,
)
from tests.engine.helpers import (
    DAYS,
    SKILL,
    T0,
    Sim,
    adapter,
    at_day,
    card,
    day,
    learned_state,
    outcome,
)


def test_new_skill_starts_with_a_worked_example():
    state = start_learning(None, SKILL.id, T0)
    assert state.level == "learning"
    assert state.introduced_at == T0
    assert learning_step(state, day(T0)) == "example"
    sim = Sim(state)
    shown = sim.grade(outcome(T0, ref=card(1, kind="example", cid="ex"), solve_ms=None))
    assert shown.effects.stage == "example"
    assert shown.answer.attempt.rating is None
    assert not shown.answer.reviews
    assert learning_step(sim.state, day(T0)) == "problem"


def test_learning_phase_passes_after_three_clean_in_a_row_and_replays():
    sim = Sim()
    results = [
        sim.grade(outcome(T0, tier=1, ref=card(1, cid="a"), correct=False)),
        sim.grade(outcome(T0 + 60_000, tier=1, ref=card(1, cid="b"))),
        sim.grade(outcome(T0 + 120_000, tier=2, ref=card(2, cid="c"), hints_used=1)),  # breaks
        sim.grade(outcome(T0 + 180_000, tier=2, ref=card(2, cid="d"))),
        sim.grade(outcome(T0 + 240_000, tier=1, ref=card(1, cid="e"))),
    ]
    assert all(not r.answer.reviews for r in results)
    assert sim.state is not None
    assert sim.state.fsrs_state is None
    assert sim.state.learning_streak == 2
    assert sim.state.learning_count == 5
    final = sim.grade(outcome(T0 + 300_000, tier=2, ref=card(2, cid="f")))
    assert final.effects.learned
    assert final.state.level == "learned"
    assert final.state.fsrs_state == REVIEW
    assert final.state.learned_at == T0 + 300_000
    # The FSRS card is created by replaying the phase's six attempts.
    assert [e.rating for e in final.answer.reviews] == [AGAIN, GOOD, HARD, GOOD, GOOD, GOOD]
    assert [e.at for e in final.answer.reviews] == [T0 + i * 60_000 for i in range(6)]
    assert all(e.rules_version == RULES_VERSION for e in final.answer.reviews)
    replayed = sim.fsrs.replay([(e.rating, e.at) for e in final.answer.reviews])
    assert replayed is not None
    assert final.state.stability == pytest.approx(replayed.stability)
    assert final.state.reps == 6


def test_clean_learning_gives_about_two_days():
    sim = Sim()
    result = sim.learn(T0)
    assert result.state.stability == pytest.approx(2.3065, abs=1e-3)
    assert due_day(result.state, 0.90, sim.fsrs, DAYS) == DAYS.add(day(T0), 2)
    assert result.state.due_at == DAYS.start(DAYS.add(day(T0), 2))


def test_time_is_never_judged_during_learning():
    sim = Sim()
    sim.grade(outcome(T0, ref=card(1, kind="example", cid="ex"), solve_ms=None))
    for i in range(3):
        result = sim.grade(
            outcome(T0 + i * 60_000, tier=1, ref=card(1, cid=f"x{i}"), solve_ms=1_700_000)
        )
    assert [e.rating for e in result.answer.reviews] == [GOOD] * 3
    assert not sim.tiers  # no speed baseline from the learning phase


def test_learning_phase_fails_at_most_problems_and_restarts_tomorrow():
    sim = Sim()
    # The streak stays reachable until the eighth problem, which misses.
    pattern = [True, True, False, True, False, True, True]
    for i, correct in enumerate(pattern):
        r = sim.grade(outcome(T0 + i * 60_000, tier=1, ref=card(1, cid=f"m{i}"), correct=correct))
        assert not r.effects.learning_failed, i
    last = sim.grade(outcome(T0 + 8 * 60_000, tier=1, ref=card(1, cid="m8"), correct=False))
    assert last.effects.learning_failed
    assert last.effects.prerequisite_checks
    assert last.state.fsrs_state is None
    assert last.state.learning_count == 0
    assert learning_step(last.state, day(T0)) == "waiting"
    assert learning_step(last.state, DAYS.add(day(T0), 1)) == "example"


def test_learning_phase_fails_as_soon_as_the_streak_is_out_of_reach():
    sim = Sim(settings=EngineSettings(correct_in_a_row=3, max_learning_problems=4))
    sim.grade(outcome(T0, tier=1, ref=card(1, cid="a"), correct=False))
    second = sim.grade(outcome(T0 + 1, tier=1, ref=card(1, cid="b"), correct=False))
    assert second.effects.learning_failed  # 2 left, 3 needed


def test_guessed_answers_do_not_count_toward_the_streak():
    sim = Sim()
    for i in range(3):
        r = sim.grade(outcome(T0 + i, tier=1, ref=card(1, cid=f"g{i}"), guessed=True))
    assert not r.effects.learned
    assert r.state.learning_streak == 0


def test_lapse_relearns_next_day_with_unrated_reinforcement_today():
    sim = Sim(learned_state(10.0, at=at_day(0)))
    miss = sim.grade(outcome(at_day(10), tier=2, ref=card(2, cid="r1"), correct=False))
    assert miss.effects.lapse
    assert miss.effects.reinforcement_due
    assert miss.state.fsrs_state == RELEARNING
    assert miss.state.lapses == 1
    assert [e.rating for e in miss.answer.reviews] == [AGAIN]
    assert miss.answer.reviews[0].predicted_recall == pytest.approx(0.9, abs=0.01)
    assert due_day(miss.state, 0.9, sim.fsrs, DAYS) == DAYS.add(day(at_day(10)), 1)
    stability = miss.state.stability
    reinforcement = sim.grade(
        outcome(at_day(10) + 600_000, tier=2, ref=card(2, cid="r2"), purpose="reinforcement")
    )
    assert reinforcement.effects.stage == "reinforcement"
    assert reinforcement.answer.attempt.rating is None
    assert not reinforcement.answer.reviews
    assert reinforcement.state.stability == stability
    relearn = sim.grade(outcome(at_day(11), tier=2, ref=card(2, cid="r3")))
    assert [e.rating for e in relearn.answer.reviews] == [GOOD]
    assert relearn.state.fsrs_state == REVIEW
    assert relearn.state.lapses == 1


def test_failed_relearning_review_is_not_another_lapse():
    sim = Sim(learned_state(10.0, at=at_day(0)))
    sim.grade(outcome(at_day(10), ref=card(2, cid="a"), correct=False))
    again = sim.grade(outcome(at_day(11), ref=card(2, cid="b"), correct=False))
    assert again.state.lapses == 1
    assert again.state.fsrs_state == RELEARNING


def test_redo_comes_back_three_days_later_or_next_day_when_confident():
    sim = Sim(learned_state(10.0, at=at_day(0)))
    sim.grade(outcome(at_day(10), ref=card(2, cid="sure"), correct=False))
    assert sim.cards["sure"].redo_due_at == DAYS.start(DAYS.add(day(at_day(10)), 1))
    assert sim.cards["sure"].redo_guaranteed
    sim.grade(outcome(at_day(12), ref=card(2, cid="unsure"), correct=False, unsure=True))
    assert sim.cards["unsure"].redo_due_at == DAYS.start(DAYS.add(day(at_day(12)), 3))
    assert not sim.cards["unsure"].redo_guaranteed
    # The redo comes back once: missing it again sets no new redo.
    sim.grade(outcome(at_day(15), ref=card(2, cid="unsure"), correct=False))
    assert sim.cards["unsure"].redo_due_at is None


def test_leech_threshold_defaults_to_eight_lapses_provisional():
    # ENG-9 / ADR-0019 item 9: 8 lapses (Anki's default), provisional; a 7th is no leech.
    from core.storage import settings as setting_specs

    assert EngineSettings().leech_lapses == 8
    assert setting_specs.default("leech.skill_lapses") == 8
    sim = Sim(learned_state(10.0, at=at_day(0), lapses=6))
    assert not sim.grade(outcome(at_day(10), correct=False)).effects.leech


def test_leech_at_eight_lapses_is_repaired_with_a_fresh_learning_phase():
    sim = Sim(learned_state(10.0, at=at_day(0), lapses=7))
    result = sim.grade(outcome(at_day(10), ref=card(2, cid="l"), correct=False))
    assert result.effects.leech
    assert result.effects.prerequisite_checks
    assert result.state.leech
    assert result.state.leech_at == at_day(10)
    assert result.state.fsrs_state is None
    assert result.state.level == "learning"
    assert learning_step(result.state, day(at_day(10))) == "example"
    assert not result.effects.reinforcement_due
    relearned = sim.learn(at_day(11))
    assert relearned.effects.learned
    assert not relearned.state.leech
    # The threshold counts from the repair: one more lapse is not a leech again.
    later = sim.grade(outcome(at_day(14), ref=card(2, cid="l2"), correct=False))
    assert later.effects.lapse
    assert not later.effects.leech


def test_leech_threshold_is_a_setting():
    sim = Sim(learned_state(10.0, at=at_day(0), lapses=2), settings=EngineSettings(leech_lapses=3))
    assert sim.grade(outcome(at_day(10), correct=False)).effects.leech


def test_provisional_seed_confirmed_or_demoted_by_first_review():
    fsrs = adapter()
    seeded = seed_provisional(
        None, SKILL.id, kind="direct", stability=10.0, at_ms=at_day(0), adapter=fsrs
    )
    assert seeded is not None
    assert seeded.level == "learned"
    assert seeded.stability == 10.0
    ok = Sim(seeded).grade(outcome(at_day(10), tier=2))
    assert ok.state.level_evidence.get("provisional") is None
    assert ok.answer.reviews
    miss = Sim(seeded).grade(outcome(at_day(10), tier=2, correct=False))
    assert miss.effects.provisional_demoted
    assert not miss.answer.reviews
    assert miss.state.fsrs_state is None
    assert miss.state.lapses == 0
    assert learning_step(miss.state, day(at_day(10))) == "example"


def test_placement_never_takes_progress_away():
    fsrs = adapter()
    strong = learned_state(40.0, at=at_day(0), level="mastered")
    assert (
        seed_provisional(
            strong, SKILL.id, kind="direct", stability=10.0, at_ms=at_day(5), adapter=fsrs
        )
        is None
    )
    weak = learned_state(3.0, at=at_day(0), level="exam")
    raised = seed_provisional(
        weak, SKILL.id, kind="direct", stability=10.0, at_ms=at_day(5), adapter=fsrs
    )
    assert raised is not None
    assert raised.stability == 10.0
    assert raised.level == "exam"
    assert "provisional" not in raised.level_evidence  # a real card is never made provisional


def test_relearning_due_ignores_retention():
    state = replace(learned_state(1.0, at=at_day(3)), fsrs_state=RELEARNING)
    assert due_day(state, 0.80, adapter(), DAYS) == DAYS.add(day(at_day(3)), 1)
    assert memory_of(state) is not None
    assert memory_of(replace(state, fsrs_state=None)) is None
