"""Memory rebuilt from the log (C3) and data guards with a "Check database" repair (I6)."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.engine import AnswerFacts, Engine, ProblemOutcome
from core.engine.config import DAY_MS
from core.engine.lifecycle import FAILED_PHASES
from core.engine.recompute import validate_state
from core.model import (
    Attempt,
    FlashcardState,
    GradedAnswer,
    ReviewEvent,
    ShapeError,
    SkillState,
)
from tests.engine.reference import ref_fsrs6
from tests.engine.test_service import answer, learn

SKILLS = ("calc1.alg", "calc1.lim", "calc1.der")


def study(engine: Engine, clock, plan: list[tuple[int, bool]]) -> None:
    """Learn every skill, then review each after the given gaps (days, correct)."""
    for skill in SKILLS:
        learn(engine, clock, skill)
    for gap, correct in plan:
        clock.advance(days=gap)
        for skill in SKILLS:
            answer(engine, clock, skill, correct=correct)


def replayed(storage, skill: str, params) -> tuple[float, float]:
    """An independent replay (the pure-Python FSRS-6 reference) of a skill's log."""
    days = Engine(storage).days()
    events = sorted(storage.users.review_events(target_id=skill), key=lambda e: (e.at, e.id or 0))
    reviews = [
        (e.rating, 0 if i == 0 else days.between(events[i - 1].at, e.at))
        for i, e in enumerate(events)
    ]
    s, d = ref_fsrs6.replay(list(params), reviews)
    return float(s), float(d)


# ---------------------------------------------------------------- C3


def test_C3_after_a_fit_every_stored_state_equals_a_fresh_replay(storage, clock):
    engine = Engine(storage)
    study(engine, clock, [(5, True), (15, True), (40, True), (90, True)])
    # Every late review succeeded: a model with longer memories describes this learner.
    candidate = [5.0, 10.0, 20.0, 40.0, *ref_fsrs6.W[4:8], 2.5, *ref_fsrs6.W[9:]]
    report = engine.fit(candidate=candidate)
    assert report.adopted, report.decision.reason
    assert report.recomputed is not None
    assert len(report.recomputed.changed) == 3
    params = engine.adapter().parameters
    assert params[0] == 5.0
    for skill in SKILLS:
        state = storage.users.skill_state(skill)
        s, d = replayed(storage, skill, params)
        assert state.stability == pytest.approx(s, rel=1e-9)
        assert state.difficulty == pytest.approx(d, rel=1e-9)
    void = storage.users.voids()[-1]
    assert void.reason == "recompute"
    assert void.note == f"fit {engine.adapter().params_id}"
    assert engine.recompute_memory().changed == ()  # already in step


def write_answer(storage, skill: str, events: list[tuple[int, int]], state: SkillState) -> None:
    """Log FSRS events directly (as grading would), with a deliberately wrong state."""
    attempt = Attempt(
        at=events[-1][1],
        card_id=f"{skill}.t1.v0",
        skill_id=skill,
        verdict="correct",
        rating=events[-1][0],
        extra={"stage": "learning" if state.reps == 0 else "review"},
    )
    reviews = tuple(
        ReviewEvent(
            at=at, target_kind="skill", target_id=skill, rating=r, rules_version="2026.11-r1"
        )
        for r, at in events
    )
    storage.users.record_answer(GradedAnswer(attempt=attempt, changes=(state,), reviews=reviews))


def test_C3_the_replay_vector_with_the_default_parameters(storage, clock):
    t = clock.now_ms()
    skill = "calc1.alg"
    bogus = SkillState(skill_id=skill, fsrs_state=2, stability=1.0, difficulty=5.0)
    write_answer(storage, skill, [(1, t), (3, t + 60_000)], replace_last(bogus, t + 60_000, 0))
    at = t + 60_000
    for n, gap in enumerate((1, 3, 8, 21), start=1):
        at += gap * DAY_MS
        write_answer(storage, skill, [(3, at)], replace_last(bogus, at, n))
    result = Engine(storage).recompute_memory(note="repair")
    (changed,) = result.changed
    assert changed.stability == pytest.approx(53.62691, abs=1e-4)
    assert changed.difficulty == pytest.approx(6.357487, abs=1e-4)
    state = storage.users.skill_state(skill)
    assert (state.stability, state.difficulty) == (changed.stability, changed.difficulty)
    assert result.void is not None
    assert result.void.reason == "recompute"


def replace_last(state: SkillState, at: int, reps: int) -> SkillState:
    from dataclasses import replace

    return replace(state, last_review_at=at, reps=reps)


def test_C3_voiding_an_older_attempt_rebuilds_memory_without_it(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    clock.advance(days=3)
    lapse = answer(engine, clock, "calc1.lim", correct=False)
    assert lapse.result.effects.lapse
    clock.advance(days=1)
    answer(engine, clock, "calc1.lim")
    clock.advance(days=6)
    answer(engine, clock, "calc1.lim")
    disputed = lapse.attempt.id
    assert disputed is not None
    result = engine.void_attempts([disputed], reason="dispute", note="the key was wrong")
    assert result.void.reason == "dispute"
    events = storage.users.review_events(target_id="calc1.lim")
    assert lapse.attempt.at not in [e.at for e in events]
    s, d = replayed(storage, "calc1.lim", engine.adapter().parameters)
    state = storage.users.skill_state("calc1.lim")
    assert state.stability == pytest.approx(s, rel=1e-9)
    assert state.difficulty == pytest.approx(d, rel=1e-9)
    assert state.fsrs_state == 2


def test_C3_reverting_parameters_recomputes_with_the_recompute_reason(storage, clock):
    engine = Engine(storage)
    study(engine, clock, [(5, True), (15, True)])
    before = {k: storage.users.skill_state(k).stability for k in SKILLS}
    candidate = [5.0, 10.0, 20.0, 40.0, *ref_fsrs6.W[4:8], 2.5, *ref_fsrs6.W[9:]]
    assert engine.fit(candidate=candidate).adopted
    (entry,) = engine.parameter_history()
    assert entry["source"] == "import"
    back = engine.revert_parameters("skills", "fsrs6-default")
    assert {c.skill_id: c.stability for c in back.changed if isinstance(c, SkillState)} == (
        pytest.approx(before)
    )
    assert engine.adapter().params_id == "fsrs6-default"
    assert back.void is not None
    assert back.void.reason == "recompute"
    assert [e["source"] for e in engine.parameter_history()] == ["import", "revert"]
    with pytest.raises(KeyError):
        engine.revert_parameters("skills", "fit-000000000000")


# ---------------------------------------------------------------- I6

bad_stability = st.sampled_from([math.nan, math.inf, -math.inf, 0.0, -1.0, 0.0009, 36_500.5])
bad_difficulty = st.sampled_from([math.nan, math.inf, 0.0, 0.99, 10.01, -3.0])


@settings(max_examples=100, deadline=None)
@given(
    st.one_of(
        st.tuples(bad_stability, st.floats(1.0, 10.0)),
        st.tuples(st.floats(0.001, 36_500.0), bad_difficulty),
    )
)
def test_I6_invalid_states_raise(pair):
    stability, difficulty = pair
    with pytest.raises(ShapeError):
        SkillState(skill_id="s.a", fsrs_state=2, stability=stability, difficulty=difficulty)
    with pytest.raises(ShapeError):
        FlashcardState(card_id="c", fsrs_state=2, stability=stability, difficulty=difficulty)


@settings(max_examples=100, deadline=None)
@given(st.floats(0.001, 36_500.0), st.floats(1.0, 10.0), st.integers(0, 10**13))
def test_I6_valid_states_build_and_a_future_review_is_caught(stability, difficulty, last):
    state = SkillState(
        skill_id="s.a",
        fsrs_state=2,
        stability=stability,
        difficulty=difficulty,
        last_review_at=last,
    )
    now = 5 * 10**12
    if last > now + DAY_MS // 24:
        with pytest.raises(ShapeError, match="future"):
            validate_state(state, now)
    else:
        validate_state(state, now)


def test_I6_check_database_restores_a_corrupted_fixture_to_its_replay_values(storage, clock):
    engine = Engine(storage)
    study(engine, clock, [(3, True), (8, False), (1, True)])
    good = {
        k: (s.stability, s.difficulty, s.last_review_at)
        for k, s in storage.users.skill_states().items()
    }

    def corrupt(conn):
        conn.execute(
            "UPDATE skill_state SET stability = 1e9, difficulty = 42 WHERE skill_id = 'calc1.alg'"
        )
        conn.execute(
            "UPDATE skill_state SET last_review_at = ? WHERE skill_id = 'calc1.lim'",
            (clock.now_ms() + 400 * DAY_MS,),
        )
        conn.execute("UPDATE skill_state SET stability = 0.0001 WHERE skill_id = 'calc1.der'")

    storage.db.write(corrupt)
    report = engine.check_database()
    assert set(report.problems) == {"skill:calc1.alg", "skill:calc1.lim", "skill:calc1.der"}
    assert any("stability" in p for p in report.problems["skill:calc1.alg"])
    assert any("future" in p for p in report.problems["skill:calc1.lim"])
    restored = storage.users.skill_states()
    for skill, (s, d, last) in good.items():
        state = restored[skill]
        assert state.stability == pytest.approx(s, rel=1e-12)
        assert state.difficulty == pytest.approx(d, rel=1e-12)
        assert state.last_review_at == last
    assert {v.reason for v in storage.users.voids()} == {"recompute"}
    assert engine.check_database().problems == {}


def _example(engine: Engine, clock, skill: str) -> None:
    refs = engine._storage.packs.card_refs(skill_id=skill)
    example = next(r for r in refs if r.kind == "example")
    engine.grade(
        ProblemOutcome(
            card=example, facts=AnswerFacts(correct=False), at=clock.now_ms(), verdict="shown"
        )
    )


def test_C3_recompute_after_a_failed_then_passed_learning_phase_changes_nothing(storage, clock):
    engine = Engine(storage)
    _example(engine, clock, "calc1.alg")
    for _ in range(6):
        rec = answer(engine, clock, "calc1.alg", correct=False)
    assert rec.result.effects.learning_failed
    failed = storage.users.skill_state("calc1.alg")
    assert failed is not None
    assert len(failed.level_evidence[FAILED_PHASES]) == 6
    clock.advance(days=1)
    learn(engine, clock, "calc1.alg")
    state = storage.users.skill_state("calc1.alg")
    assert state is not None
    assert state.fsrs_state == 2
    assert FAILED_PHASES not in state.level_evidence  # the block is closed
    # The card was built from the failed phase's six Agains and the passing phase: the
    # whole learning block, as the log holds it.
    (history,) = engine.histories()
    assert len(history.steps) == 9
    assert engine.recompute_memory().changed == ()
    assert storage.users.skill_state("calc1.alg") == state
