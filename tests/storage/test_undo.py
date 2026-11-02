"""QUE-15: undo restores the exact state before the last answer, in one transaction."""

from dataclasses import replace

import pytest

from core.model import (
    THIS_ATTEMPT,
    Attempt,
    CardUser,
    DiagnosticSet,
    GradedAnswer,
    ImplicitCredit,
    PendingCheck,
    ReviewEvent,
    SessionState,
    SkillShadow,
    SkillState,
    SkillTierState,
    WeakSpot,
)
from core.storage import NothingToUndoError, Storage, UndoConflictError
from core.storage.clock import FixedClock
from tests.storage import data
from tests.storage.data import some

STATE_TABLES = (
    "skill_state",
    "skill_tier",
    "skill_shadow",
    "flashcard_state",
    "card_user",
    "pending_check",
    "weak_spot",
    "diagnostic_set",
)


def state(storage: Storage) -> dict[str, list[tuple[object, ...]]]:
    with storage.db.reading() as conn:
        dump = data.dump_state(conn)
    return {t: dump[t] for t in STATE_TABLES}


def answer(skill: str, stability: float, *, pres: str | None = None, final: bool = True, **extra):
    return GradedAnswer(
        attempt=Attempt(
            card_id="c1",
            skill_id=skill,
            verdict="correct" if final else "incorrect",
            presentation_id=pres,
            final=final,
            rating=3 if final else None,
            **extra,
        ),
        changes=(
            SkillState(
                skill_id=skill,
                fsrs_state=2,
                stability=stability,
                difficulty=5.0,
                reps=int(stability),
            ),
            CardUser(card_id="c1", times_seen=int(stability)),
            PendingCheck(skill_id="pre", attempt_id=THIS_ATTEMPT),
        )
        if final
        else (CardUser(card_id="c1", times_seen=99),),
        reviews=(ReviewEvent(target_kind="skill", target_id=skill, rating=3, rules_version="r1"),)
        if final
        else (),
        credits=(ImplicitCredit(from_skill=skill, to_skill="pre", weight=0.5, mode="on"),)
        if final
        else (),
    )


def test_undo_restores_exact_state_and_voids_logs(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    users.record_answer(answer("s", 2.0))
    clock.advance(minutes=1)
    before = state(storage)
    last = users.record_answer(answer("s", 5.0))
    assert state(storage) != before
    result = users.undo_last_answer()
    assert state(storage) == before
    assert [a.id for a in result.attempts] == [last.id]
    assert result.attempts[0].voided_by == result.void.id
    assert result.void.reason == "undo"
    assert result.void.at == clock.now_ms()
    assert [r.attempt_id for r in users.review_events()] == [1]
    assert [r.voided_by for r in users.review_events(include_voided=True)] == [None, result.void.id]
    assert [c.voided_by for c in users.credits(include_voided=True)] == [None, result.void.id]
    assert some(users.last_attempt()).id == 1
    # the void records exactly what it changed, so it is auditable
    assert result.void.state_before == last.state_after


def test_undo_of_first_answer_deletes_rows_it_created(storage: Storage) -> None:
    users = storage.users
    empty = state(storage)
    users.record_answer(answer("s", 1.0))
    users.undo_last_answer()
    assert state(storage) == empty


def test_undo_takes_back_every_try_of_the_last_presentation(storage: Storage) -> None:
    users = storage.users
    users.record_answer(answer("s", 2.0, pres="p1"))
    before = state(storage)
    first = users.record_answer(answer("s", 0, pres="p2", final=False, attempt_number=1))
    second = users.record_answer(answer("s", 4.0, pres="p2", attempt_number=2))
    result = users.undo_last_answer()
    assert [a.id for a in result.attempts] == [second.id, first.id]
    assert state(storage) == before
    assert [a.presentation_id for a in users.attempts()] == ["p1"]


def test_successive_undos_walk_back_exactly(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    states = [state(storage)]
    for stability in (1.0, 2.0, 3.0):
        users.record_answer(answer("s", stability))
        clock.advance(seconds=10)
        states.append(state(storage))
    for expected in reversed(states[:-1]):
        users.undo_last_answer()
        assert state(storage) == expected
    with pytest.raises(NothingToUndoError):
        users.undo_last_answer()


def test_undo_refuses_when_rows_changed_since(storage: Storage) -> None:
    users = storage.users
    users.record_answer(answer("s", 2.0))
    users.apply([SkillState(skill_id="s", stability=9.0)])  # e.g. a daily recomputation
    changed = state(storage)
    with pytest.raises(UndoConflictError):
        users.undo_last_answer()
    assert state(storage) == changed
    assert users.voids() == []
    assert len(users.attempts()) == 1


def test_undo_refuses_when_a_later_row_points_at_one_it_would_delete(storage: Storage) -> None:
    users = storage.users
    spot = WeakSpot(
        skill_id="s",
        flagged_at=0,
        study_day="2026-11-01",
        z=2,
        evidence=1,
        misses=3,
        problems=5,
        days=2,
    )
    users.record_answer(replace(answer("s", 2.0), changes=(spot,)))  # the answer flags it
    spot_id = some(users.weak_spots()[0].id)
    users.apply([DiagnosticSet(skill_id="s", weak_spot_id=spot_id, created_at=0)])  # later
    changed = state(storage)
    with pytest.raises(UndoConflictError):
        users.undo_last_answer()
    assert state(storage) == changed
    assert users.voids() == []


def test_undo_saves_the_session_in_the_same_transaction(storage: Storage) -> None:
    users = storage.users
    session = users.start_session(SessionState(study_day=users.study_day(), position=3))
    users.record_answer(replace(answer("s", 2.0), session=replace(session, position=4)))
    assert some(users.session(some(session.id))).position == 4
    users.undo_last_answer(session=replace(session, position=3, draft=""))
    assert some(users.session(some(session.id))).position == 3


def test_void_older_attempts_with_recomputed_state(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    reported = users.record_answer(answer("s", 2.0))
    users.record_answer(answer("t", 3.0))
    recomputed = (SkillState(skill_id="s", fsrs_state=None, stability=None),)
    result = users.void_attempts(
        [some(reported.id)], reason="report", changes=recomputed, note="bad key"
    )
    assert result.void.reason == "report"
    assert result.void.note == "bad key"
    assert some(users.skill_state("s")).stability is None
    assert some(users.skill_state("t")).stability == 3.0
    assert [a.id for a in users.attempts()] == [2]
    assert some(result.void.state_after)["rows"][0]["row"]["stability"] is None
    with pytest.raises(Exception, match="already voided"):
        users.void_attempts([some(reported.id)], reason="report")
    with pytest.raises(Exception, match="no attempt"):
        users.void_attempts([99], reason="recompute")


def test_undo_covers_tier_and_shadow_rows(storage: Storage) -> None:
    users = storage.users
    users.apply([SkillTierState(skill_id="s", tier=2, target_ms=60_000)])
    before = state(storage)
    users.record_answer(
        GradedAnswer(
            attempt=Attempt(card_id="c", verdict="correct"),
            changes=(
                SkillTierState(skill_id="s", tier=2, target_ms=54_000, first_correct_ms=(1, 2)),
                SkillShadow(skill_id="s", credited_stability=4.5),
            ),
        )
    )
    users.undo_last_answer(reason="dispute")
    assert state(storage) == before
    assert users.voids()[0].reason == "dispute"
