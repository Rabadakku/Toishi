"""The study session service: serving, grading, resume, undo, dispute, report, modes."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from core.model import CourseGoal, Exam
from core.queue import Plan, QueueError, StudyService, Turn, to_dict
from core.queue.daylog import DayEntry, write_entry
from core.storage.clock import to_ms
from tests.queue.helpers import NY, World, answer, make_world, review_state
from tests.queue.sim import check_hook

SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    """One course, all sections Solid, every skill in review and due today."""
    w = make_world(
        tmp_path,
        ("ca",),
        sections=2,
        skills=3,
        flashcards=True,
        state="solid",
        settings={"daily.flashcards": 0},
    )
    now = w.clock.now_ms()
    w.storage.users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in SKILLS])
    yield w
    w.storage.close(backup=False)


@pytest.fixture
def fresh(tmp_path: Path) -> Iterator[World]:
    """Two courses, Learning now, nothing studied yet."""
    w = make_world(tmp_path, ("ca", "cb"), sections=2, skills=3)
    yield w
    w.storage.close(backup=False)


def to_problem(svc: StudyService, turn: Turn) -> Turn:
    """Continue through worked examples and flashcards to the next problem."""
    while turn.type == "problem" and turn.problem is not None and turn.problem.kind != "problem":
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        turn = svc.next()
    return turn


def finals(w: World, **kw: Any) -> list[Any]:
    return [a for a in w.storage.users.attempts(**kw) if a.final]


def plan_of(w: World) -> Plan:
    session = w.storage.users.latest_open_session()
    assert session is not None
    return Plan.from_json(session.plan)


def state_rows(w: World) -> tuple[Any, ...]:
    u = w.storage.users
    return (
        u.skill_states(),
        u.card_users(),
        u.skill_tiers(),
        u.pending_checks(None),
        u.flashcard_states(),
        len(u.review_events()),
    )


# ---------------------------------------------------------------- serving and resume


def test_start_serves_the_plan_and_resumes_after_a_crash(world: World) -> None:
    svc = world.service()
    turn = svc.start()
    assert turn.type == "problem"
    assert turn.problem is not None
    assert turn.progress is not None
    assert turn.progress.total == 6
    assert turn.problem.reason.tag in ("review", "stretch")
    assert turn.problem.reason.why
    assert "skill" not in to_dict(turn.problem)["card"]  # names stay hidden until answered
    world.clock.advance(seconds=30)
    svc.tick(30_000, draft="1/2")
    hint = svc.hint()
    assert (hint.index, hint.total, hint.rating_effect) == (1, 2, "hard")
    world.reopen()  # Cmd+Q or a crash: nothing ended, nothing flushed by us
    svc2 = world.service()
    resumed = svc2.resume()
    assert resumed is not None
    assert resumed.problem is not None
    assert resumed.session_id == turn.session_id
    assert resumed.problem.item_key == turn.problem.item_key
    assert resumed.problem.card.id == turn.problem.card.id
    assert resumed.problem.active_ms == 30_000
    assert resumed.problem.draft == "1/2"
    assert resumed.problem.hints_shown == ("hint 1",)
    assert svc2.start().session_id == turn.session_id  # Start resumes too


def test_retry_then_correct_is_graded_on_continue(world: World) -> None:
    svc = world.service()
    svc.start()
    first = answer(svc, world.clock, correct=False)
    assert (first.outcome, first.message, first.tries_used) == ("retry", "Not quite.", 1)
    tries = world.storage.users.attempts()
    assert len(tries) == 1
    assert not tries[0].final
    assert tries[0].rating is None
    second = answer(svc, world.clock, correct=True)
    assert second.outcome == "correct"
    assert second.solution is not None
    assert second.solution.skill_name  # revealed after the answer
    assert not finals(world)  # graded on continue (too easy / picker come first)
    svc.next()
    graded = finals(world)
    assert len(graded) == 1
    assert graded[0].attempt_number == 2
    assert graded[0].rating == 2
    assert graded[0].presentation_id == tries[0].presentation_id
    assert graded[0].triage_policy == "recommended"
    assert graded[0].extra["queue_mode"] == "daily"


def test_invalid_answers_are_not_attempts_and_undecidable_ones_self_grade(world: World) -> None:
    svc = world.service()
    svc.start()
    bad = svc.submit({"answers": [{"value": "?"}], "timing": {"active_ms": 5000}})
    assert bad.outcome == "invalid"
    assert bad.tries_used == 0
    assert world.storage.users.attempts() == []
    odd = svc.submit({"answers": [{"value": "!"}], "timing": {"active_ms": 5000}})
    assert odd.outcome == "self-grade"
    assert odd.solution is not None
    graded = svc.submit({"self_grade": "matched", "timing": {"active_ms": 9000}})
    assert graded.outcome == "correct"
    svc.next()
    (attempt,) = finals(world)
    assert attempt.verdict == "undecided"
    assert attempt.extra.get("grader_review") is True
    assert attempt.rating == 3


def test_hints_cap_the_rating_and_the_last_counts_as_again(world: World) -> None:
    svc = world.service()
    svc.start()
    svc.hint()
    answer(svc, world.clock)
    svc.next()
    svc.hint()
    last = svc.hint()
    assert last.rating_effect == "again"
    with pytest.raises(QueueError):
        svc.hint()
    answer(svc, world.clock)
    svc.next()
    ratings = [a.rating for a in finals(world)]
    assert ratings == [2, 1]


def test_too_easy_and_give_up(world: World) -> None:
    svc = world.service()
    svc.start()
    result = answer(svc, world.clock)
    assert result.solution is not None
    assert result.solution.can_mark_too_easy
    assert svc.flag("too_easy").ok
    svc.next()
    given = svc.give_up({"active_ms": 20_000})
    assert given.outcome == "incorrect"
    assert given.solution is not None
    assert given.solution.needs_diagnosis
    diagnosis = svc.diagnose("cant_tell")
    assert diagnosis.rating == 1
    attempts = finals(world)
    assert [a.rating for a in attempts] == [4, 1]
    assert attempts[1].verdict == "gave-up"
    assert attempts[1].error_choice == "cant-tell"


def test_untimed_session_and_timing_guards(world: World) -> None:
    svc = world.service()
    svc.start({"untimed": True})
    world.clock.advance(seconds=40)
    result = svc.submit(
        {
            "answers": [{"value": "1"}],
            "timing": {"active_ms": 3_600_000, "solve_ms": 4_000_000, "entry_ms": 1000},
        }
    )
    assert result.solution is not None
    assert result.solution.time_text is None
    svc.next()
    (attempt,) = finals(world)
    assert attempt.untimed
    assert attempt.active_ms is not None
    assert attempt.active_ms <= 42_000
    assert "active time over wall clock" in attempt.extra["timing_flags"]


def test_break_reminder_and_usage_backups(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[int] = []
    monkeypatch.setattr(world.storage, "note_use", lambda ms: used.append(ms))
    svc = world.service()
    svc.start()
    world.clock.advance(minutes=52)
    assert svc.tick(51 * 60_000).break_due
    world.clock.advance(minutes=1)
    assert not svc.tick(52 * 60_000).break_due
    assert sum(used) == 52 * 60_000


# ---------------------------------------------------------------- follow-ups


def test_a_tapped_miss_brings_a_check_at_its_distance(world: World) -> None:
    world.storage.users.set_setting("daily.problems", 6)  # a full day: no free slots
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    diagnosis = svc.diagnose("step", 1)  # the diagnosis flow asks for a check
    assert diagnosis.checks
    assert diagnosis.follow_up.startswith("A quick check on")
    plan = plan_of(world)
    seq = [i for i in plan.items if i.kind != "flashcard"]
    keys = [i.key for i in seq]
    miss = next(i for i in seq if i.status == "done")
    check = next(i for i in seq if i.check_id is not None)
    assert check.anchor == miss.key
    assert keys.index(check.key) - keys.index(miss.key) >= 3
    assert "after a miss on" in check.label
    assert check.why  # the diagnosis flow's own reason sentence
    assert plan.slots == 6  # the check takes the lowest-priority slot
    turn = svc.next()
    while turn.type == "problem" and turn.problem is not None:
        if turn.problem.item_key == check.key:
            assert turn.problem.reason.tag == "check"
        answer(svc, world.clock, correct=True)
        turn = svc.next()
    resolved = [c for c in world.storage.users.pending_checks(None) if c.id == check.check_id]
    assert resolved[0].status == "passed"
    by_check = [a for a in finals(world) if a.check_of == check.check_id]
    assert len(by_check) == 1


def test_a_lapse_brings_a_reinforcement_five_items_later(world: World) -> None:
    world.storage.users.set_setting("daily.problems", 6)
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("cant_tell")
    plan = plan_of(world)
    keys = [i.key for i in plan.items if i.kind != "flashcard"]
    miss = next(i for i in plan.items if i.status == "done")
    rf = [i for i in plan.items if i.purpose == "reinforcement"]
    assert rf
    assert rf[0].anchor == miss.key
    assert keys.index(rf[0].key) - keys.index(miss.key) >= 5


def test_without_the_diagnosis_flow_a_served_check_is_still_resolved(world: World) -> None:
    svc = world.service(diagnosis=False, hooks=(check_hook(world),))
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("cant_tell")
    check = next(i for i in plan_of(world).items if i.check_id is not None)
    turn = svc.next()
    while turn.type == "problem":
        answer(svc, world.clock)
        turn = svc.next()
    resolved = [c for c in world.storage.users.pending_checks(None) if c.id == check.check_id]
    assert resolved[0].status == "passed"


def test_a_flashcard_refresher_follows_a_miss(world: World) -> None:
    world.storage.users.set_setting("daily.flashcards", 5)
    svc = world.service()
    turn = to_problem(svc, svc.start())
    assert turn.problem is not None
    skill = world.storage.packs.card(turn.problem.card.id).skill_id  # type: ignore[union-attr]
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    nxt = svc.next()
    assert nxt.problem is not None
    assert nxt.problem.kind == "flashcard"
    assert nxt.problem.card.id == f"{skill}.fc"
    assert nxt.problem.reason.why.startswith("A flashcard on the skill you just missed")
    rated = svc.rate_flashcard(3)
    assert rated.rating == 3
    fs = world.storage.users.flashcard_state(f"{skill}.fc")
    assert fs is not None
    assert fs.reps == 1
    events = world.storage.users.review_events(target_kind="flashcard")
    assert [e.target_id for e in events] == [f"{skill}.fc"]


def test_learning_blocks_and_skills_learned(fresh: World) -> None:
    svc = fresh.service()
    turn = svc.start()
    assert turn.problem is not None
    assert turn.problem.kind == "example"
    assert turn.problem.reason.tag == "new-skill"
    block = plan_of(fresh).item(turn.problem.item_key).block  # type: ignore[union-attr]
    turn = svc.next()
    for _ in range(3):
        assert turn.problem is not None
        assert turn.problem.kind == "problem"
        assert plan_of(fresh).item(turn.problem.item_key).block == block  # type: ignore[union-attr]
        answer(svc, fresh.clock)
        turn = svc.next()
    plan = plan_of(fresh)
    assert not [i for i in plan.items if i.block == block and i.pending]  # passed: slot freed
    summary = svc.end()
    assert summary.learned
    assert summary.problems == 3


# ---------------------------------------------------------------- undo, dispute, report


def test_undo_is_exact_and_shows_the_problem_again(world: World) -> None:
    svc = world.service()
    turn = svc.start()
    assert turn.problem is not None
    before = state_rows(world)
    plan_before = plan_of(world)
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("step", 1)
    svc.next()
    assert state_rows(world) != before
    back = svc.undo()
    assert back.message.startswith("Undone")
    assert back.problem is not None
    assert back.problem.card.id == turn.problem.card.id
    assert back.problem.item_key == turn.problem.item_key
    assert state_rows(world) == before
    assert [i.key for i in plan_of(world).items] == [i.key for i in plan_before.items]
    assert world.storage.users.voids()[-1].reason == "undo"
    # Undo works again after re-answering; after the next answer is submitted it doesn't.
    answer(svc, world.clock)
    svc.next()
    answer(svc, world.clock, correct=False)  # "Not quite" on the next problem
    refused = svc.undo()
    assert refused.message.startswith("Undo is only available")


def test_undo_on_the_verdict_screen_voids_the_tries(world: World) -> None:
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=True)
    back = svc.undo()
    assert back.result is None
    assert back.problem is not None
    assert back.problem.tries_used == 0
    assert world.storage.users.attempts() == []  # the try is voided
    assert world.storage.users.attempts(include_voided=True)


def test_undo_refuses_cleanly_when_storage_refuses(world: World) -> None:
    svc = world.service()
    svc.start()
    answer(svc, world.clock)
    svc.next()
    (attempt,) = finals(world)
    users = world.storage.users
    state = users.skill_state(attempt.skill_id or "")
    assert state is not None
    users.apply([replace(state, elo_theta=state.elo_theta + 1)])  # a later change
    refused = svc.undo()
    assert "can't be undone exactly" in refused.message
    assert finals(world) == [attempt]


def test_dispute_keeps_the_attempt_out_of_scheduling(world: World) -> None:
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    before = state_rows(world)
    result = svc.flag("dispute", "I was right")
    assert result.ok
    assert not result.attempt_counts
    assert state_rows(world) == before
    disputes = world.storage.users.disputes()
    assert len(disputes) == 1
    assert disputes[0].note == "I was right"
    voided = world.storage.users.attempts(include_voided=True)
    assert voided
    assert all(a.voided_by is not None for a in voided)
    svc.next()  # moves on without grading
    assert finals(world) == []


def test_dispute_after_the_picker_undoes_the_graded_answer(world: World) -> None:
    svc = world.service()
    svc.start()
    before = state_rows(world)
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("step", 1)
    assert svc.flag("dispute").attempt_counts is False
    assert state_rows(world) == before
    assert not [i for i in plan_of(world).items if i.check_id is not None and i.pending]
    assert world.storage.users.voids()[-1].reason == "dispute"


def test_report_hides_the_card_and_serves_another(world: World) -> None:
    svc = world.service()
    turn = svc.start()
    assert turn.problem is not None
    card = turn.problem.card.id
    result = svc.flag("report", "the key is wrong")
    assert result.ok
    assert world.storage.users.card_mark(card).hidden  # type: ignore[union-attr]
    assert world.storage.users.reports()[0].reason == "the key is wrong"
    now = svc.current()
    assert now.problem is not None
    assert now.problem.card.id != card
    assert now.problem.item_key == turn.problem.item_key
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.flag("report")
    assert all(a.voided_by is not None for a in world.storage.users.attempts(include_voided=True))


def test_flag_and_suspend(world: World) -> None:
    svc = world.service()
    turn = svc.start()
    assert turn.problem is not None
    card = turn.problem.card.id
    assert svc.flag("flag", "check later").ok
    assert world.storage.users.card_mark(card).flagged  # type: ignore[union-attr]
    svc.flag("suspend")
    assert world.storage.users.card_mark(card).suspended  # type: ignore[union-attr]
    again = svc.current()
    assert again.problem is not None
    assert again.problem.card.id != card


# ---------------------------------------------------------------- modes


def test_lighter_set_serves_easy_problems_below_the_band_unrated(fresh: World) -> None:
    now = fresh.clock.now_ms()
    fresh.storage.users.apply([review_state("ca.s1.k1", now, days_ago=12, stability=40.0)])
    svc = fresh.service()
    turn = svc.start({"mode": "lighter"})
    plan = plan_of(fresh)
    assert plan.lighter
    assert not [i for i in plan.items if i.order == 7]
    assert turn.problem is not None
    assert turn.problem.card.id.split(".")[3] in ("t1", "t2")
    answer(svc, fresh.clock)
    svc.next()
    (attempt,) = finals(fresh)
    assert attempt.rating is None  # a below-band success changes nothing (ENG-4)
    assert attempt.extra.get("lighter_set") is True
    assert attempt.extra.get("below_band") is True


def test_lighter_over_a_new_skills_example_on_screen_serves_the_next_item(fresh: World) -> None:
    """QUE-10, QUE-16 (DEV-9): Lighter over an open daily session while a new skill's worked
    example is on screen. Its block has not started, so the skill leaves the plan with the
    example and the same session moves on to the next item; it stays resumable."""
    now = fresh.clock.now_ms()
    due = [f"{c}.s1.k{k}" for c in ("ca", "cb") for k in (1, 2, 3)]
    fresh.storage.users.apply([review_state(k, now, days_ago=12, stability=40.0) for k in due])
    svc = fresh.service()
    turn = svc.start({"mode": "daily"})
    while turn.problem is not None and turn.problem.kind != "example":
        answer(svc, fresh.clock)
        turn = svc.next()
    assert turn.problem is not None, "the daily plan teaches a new skill"
    example = turn.problem.item_key
    item = plan_of(fresh).item(example)
    assert item is not None
    assert (item.order, item.block) == (7, f"blk:{item.skill_id}")

    lighter = svc.start({"mode": "lighter"})  # raised StorageError before the fix

    plan = plan_of(fresh)
    assert (plan.mode, plan.lighter) == ("lighter", True)
    assert plan.item(example) is None
    assert not [i for i in plan.pending if i.order == 7]  # no new skills (QUE-10)
    assert (lighter.session_id, lighter.mode) == (turn.session_id, "lighter")
    assert lighter.problem is not None
    assert lighter.problem.item_key != example
    resumed = svc.resume()
    assert resumed is not None
    assert resumed.problem is not None
    assert resumed.problem.item_key == lighter.problem.item_key
    assert not finals(fresh, skill_id=item.skill_id)  # nothing of the dropped skill graded


def test_focused_practice_and_slip_allowance(world: World) -> None:
    now = world.clock.now_ms()
    world.storage.users.apply([review_state("ca.s1.k1", now, days_ago=0.5, stability=60.0)])
    svc = world.service()
    turn = svc.start({"mode": "focused", "skill_id": "ca.s1.k1", "count": 4})
    assert turn.mode == "focused"
    for _ in range(2):
        answer(svc, world.clock)
        svc.next()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    slip = svc.diagnose("slip")
    assert slip.slip_accepted
    assert slip.rating == 1  # a slip is still a miss for FSRS (ADR-0014)
    svc.next()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    again = svc.diagnose("misread")  # a second slip within 30 days becomes a step error
    assert not again.slip_accepted
    assert again.rating is None  # held for its check (ADR-0008)
    assert [c.kind for c in world.storage.users.pending_checks()] == ["step"]
    assert {a.extra["purpose"] for a in finals(world)} == {"focused"}


def test_focused_practice_on_a_new_section_teaches_first(fresh: World) -> None:
    svc = fresh.service()
    turn = svc.start({"mode": "focused", "section_id": "cb.s2"})
    assert turn.problem is not None
    assert turn.problem.kind == "example"


def test_practice_test_is_graded_at_the_end(world: World) -> None:
    users = world.storage.users
    exam_at = to_ms(datetime(2026, 9, 11, 9, tzinfo=NY))
    exam = users.add_exam(Exam(course_id="ca", name="Test 1", at=exam_at, minutes=30, problems=3))
    far = users.add_exam(
        Exam(course_id="ca", name="Final", at=to_ms(datetime(2026, 12, 11, 9, tzinfo=NY)))
    )
    svc = world.service()
    with pytest.raises(QueueError):
        svc.start({"mode": "practice-test", "exam_id": far.id})
    turn = svc.start({"mode": "practice-test", "exam_id": exam.id})
    assert turn.problem is not None
    assert turn.problem.practice_test
    results = []
    for right in (True, False, True):
        results.append(answer(svc, world.clock, correct=right).outcome)
        assert finals(world) == []  # nothing graded until the end
    assert results == ["recorded"] * 3
    end = svc.current()
    assert end.type == "summary"
    assert end.summary is not None
    assert end.summary.test is not None
    assert (end.summary.test.correct, end.summary.test.total) == (2, 3)
    graded = finals(world)
    assert len(graded) == 3
    assert {a.extra["purpose"] for a in graded} == {"practice-test"}
    assert all(a.tier == 3 for a in graded)


@pytest.mark.parametrize("unanswered", ["again", "skip"])
def test_timed_practice_test_stops_when_time_is_up(world: World, unanswered: str) -> None:
    """Problems never answered when time runs out score zero in the test and are logged as
    unrated attempts (C5, the default "skip"); the setting "again" counts them as Again."""
    if unanswered == "again":
        world.storage.users.set_setting("queue.test_unanswered", "again")
    exam_at = to_ms(datetime(2026, 9, 11, 9, tzinfo=NY))
    exam = world.storage.users.add_exam(
        Exam(course_id="ca", name="Quiz", at=exam_at, minutes=30, problems=3)
    )
    svc = world.service()
    svc.start({"mode": "practice-test", "exam_id": exam.id, "timed": True})
    world.clock.advance(minutes=31)
    svc.submit({"answers": [{"value": "1"}], "timing": {"active_ms": 31 * 60_000}})
    end = svc.current()
    assert end.summary is not None
    test = end.summary.test
    assert test is not None
    assert test.time_up
    assert test.answered == 1
    assert test.unanswered == unanswered
    assert test.limit_ms == 30 * 60_000
    graded = finals(world)
    if unanswered == "skip":
        assert len(graded) == 3
        assert [a.rating for a in graded if a.extra.get("unanswered")] == [None, None]
        assert [x.rating for x in test.lines if not x.answered] == [None, None]
    else:
        assert len(graded) == 3
        missed = [a for a in graded if a.extra.get("unanswered")]
        assert len(missed) == 2
        assert {a.rating for a in missed} == {1}
        assert {a.verdict for a in missed} == {"gave-up"}
        assert [x.rating for x in test.lines if not x.answered] == [1, 1]


def test_extra_practice_takes_tomorrows_items(world: World) -> None:
    svc = world.service()
    turn = svc.start()
    while turn.type == "problem":
        answer(svc, world.clock, correct=False)  # lapses: relearning is due tomorrow
        answer(svc, world.clock, correct=False)
        turn = svc.next()
    assert turn.type == "summary"
    assert turn.summary is not None
    assert turn.summary.extra_practice_available
    assert svc.start().type == "empty"  # the day's plan is done
    extra = svc.start({"mode": "extra", "count": 3})
    assert extra.type == "problem"
    assert extra.mode == "extra"
    assert plan_of(world).slots == 3
    answer(svc, world.clock)
    svc.next()
    assert finals(world)[-1].extra["queue_mode"] == "extra"


# ---------------------------------------------------------------- home, days, summary


def test_today_shows_problems_minutes_and_never_an_overdue_count(world: World) -> None:
    svc = world.service()
    world.storage.users.add_exam(
        Exam(course_id="ca", name="Midterm", at=to_ms(datetime(2026, 9, 10, 9, tzinfo=NY)))
    )
    today = svc.today()
    assert today.problems == 6
    assert today.minutes > 0
    assert [c.course_id for c in today.courses] == ["ca"]
    assert today.exams[0].days_left == 9
    assert today.exams[0].practice_test

    def keys(obj: Any) -> list[str]:
        if isinstance(obj, dict):
            return [k for k, v in obj.items() for k in (k, *keys(v))]
        if isinstance(obj, list | tuple):
            return [k for v in obj for k in keys(v)]
        return []

    assert not [k for k in keys(to_dict(today)) if "overdue" in k or "backlog" in k]


def test_proposals_after_days_of_overload_and_backlog(world: World) -> None:
    users = world.storage.users
    day = world.service().engine().today()
    users.set_setting("daily.problems", 1)
    assert world.service().today().proposals == ()
    for i in range(1, 7):
        write_entry(users, day - timedelta(days=i), DayEntry(n=1, need=6, backlog=5))
    proposals = world.service().today().proposals
    assert [p.kind for p in proposals] == ["overload", "backlog"]
    assert all(not any(ch.isdigit() for ch in p.message) for p in proposals)  # QUE-7


def test_a_session_left_open_past_rollover_is_graded_and_rebuilt(world: World) -> None:
    svc = world.service()
    first = svc.start()
    answer(svc, world.clock)  # on the verdict screen, not continued
    world.clock.set(datetime(2026, 9, 2, 12, tzinfo=NY))
    turn = svc.start()
    assert turn.session_id != first.session_id
    (attempt,) = finals(world)
    assert attempt.study_day == "2026-09-01"
    old = world.storage.users.session(first.session_id or 0)
    assert old is not None
    assert old.ended_at is not None


def test_carry_over_after_stopping_early(fresh: World) -> None:
    now = fresh.clock.now_ms()
    fresh.storage.users.apply(
        [
            review_state(f"{c}.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in (1, 2, 3)
        ]
    )
    fresh.storage.users.set_setting("daily.problems", 8)
    svc = fresh.service()
    turn = svc.start()
    quotas = dict(plan_of(fresh).quotas)
    for _ in range(2):
        turn = to_problem(svc, turn)
        answer(svc, fresh.clock)
        turn = svc.next()
    svc.end()
    fresh.clock.set(datetime(2026, 9, 2, 12, tzinfo=NY))
    plan = svc.plan_preview()
    carried = plan.info["carried"]
    assert carried
    assert all(v <= quotas[c] // 2 for c, v in carried.items())
    assert sum(plan.quotas.values()) == 8


def test_vacation_mode(world: World) -> None:
    svc = world.service()
    day = svc.engine().today()
    svc.set_vacation(day, day + timedelta(days=3))
    turn = svc.start()
    assert turn.type == "empty"
    assert "Vacation" in turn.message
    assert svc.today().vacation
    svc.clear_vacation()
    assert svc.start().type == "problem"


def test_summary_and_forecast(world: World) -> None:
    world.storage.users.set_course_goal(CourseGoal(course_id="ca", goal="B"))
    svc = world.service()
    turn = svc.start()
    misses = 0
    while turn.type == "problem":
        right = misses > 0
        if not right:
            answer(svc, world.clock, correct=False)
            answer(svc, world.clock, correct=False)
            misses += 1
        else:
            answer(svc, world.clock)
        turn = svc.next()
    summary = turn.summary
    assert summary is not None
    assert summary.missed == 1
    assert summary.misses[0].skill_name.startswith("CA skill")
    assert summary.problems >= 6
    assert summary.active_ms > 0
    assert summary.forecast.day == "2026-09-02"
    assert to_dict(summary)["forecast"]["problems"] == summary.forecast.problems
    assert svc.resume() is None  # ended


def test_policy_is_recorded_on_every_attempt(world: World) -> None:
    world.storage.users.set_setting("queue.triage_policy", "lowest-recall-first")
    svc = world.service()
    svc.start()
    answer(svc, world.clock)
    svc.next()
    assert {a.triage_policy for a in finals(world)} == {"lowest-recall-first"}


def test_requests_and_errors(world: World) -> None:
    svc = world.service()
    with pytest.raises(QueueError):
        svc.submit({"answers": [{"value": "1"}]})
    svc.start()
    with pytest.raises(QueueError):
        svc.next()  # answer or give up first
    with pytest.raises(QueueError):
        svc.diagnose("slip")  # nothing missed
    with pytest.raises(QueueError):
        svc.submit({"answers": [{"value": "1"}], "item_key": "not-on-screen"})
    preview = svc.read_answer("2x")
    assert preview.ok
    assert date.fromisoformat(svc.forecast().day)


def test_the_diagnosis_daily_run_happens_once_a_study_day(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.engine.diagnosis import Diagnosis

    runs: list[int] = []
    real = Diagnosis.daily

    def counted(self: Diagnosis, at_ms: int | None = None) -> Any:
        runs.append(1)
        return real(self, at_ms)

    monkeypatch.setattr(Diagnosis, "daily", counted)
    svc = world.service()
    svc.today()
    svc.start()
    svc.today()
    assert len(runs) == 1
    world.clock.set(datetime(2026, 9, 2, 12, tzinfo=NY))
    svc.today()
    assert len(runs) == 2
    assert len(world.storage.users.pending_checks()) == 0  # nothing to diagnose yet
