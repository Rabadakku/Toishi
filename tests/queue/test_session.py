"""The wave 2 study session (docs/design/wave2-integration.md section 4): problems planned by
core.practice, retried freely with only the first try counting, committed one answer per
transaction with what the planner chose, re-planned after each answer, undone exactly.

Most tests serve chosen problems through `Script` (a stand-in for the planner); the first
ones run the real planner."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from core.engine import TimingFacts
from core.model import CourseSetup, Exam
from core.practice import PracticeEngine
from core.queue import Plan, QueueError, StudyService, to_dict
from core.queue.session import valid_minutes
from core.storage.clock import to_ms
from tests.queue.helpers import (
    FEEDBACK,
    START,
    Script,
    World,
    answer,
    make_world,
)

S1 = ["ca.s1.k1", "ca.s1.k2", "ca.s1.k3"]
TIMING = {"active_ms": 40_000, "solve_ms": 32_000, "entry_ms": 4_000}


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path, ("ca",), sections=2, skills=3)
    yield w
    w.storage.close(backup=False)


def submit(svc: StudyService, value: str, **kw: Any) -> Any:
    """Type `value` after 40 seconds of work (TIMING) and submit it."""
    clock = svc.storage.db.clock
    clock.advance(seconds=40)  # type: ignore[attr-defined]
    return svc.submit({"answers": [{"value": value}], "timing": TIMING, **kw})


def scripted(world: World, *cards: str, role: str = "growth") -> tuple[StudyService, Script]:
    svc = world.service()
    script = Script(svc)
    for card in cards:
        script.problem(card, role=role)
    return svc, script


def finals(world: World, card_id: str | None = None) -> list[Any]:
    return [a for a in world.storage.users.attempts(card_id=card_id) if a.final]


def replayed(world: World, svc: StudyService) -> None:
    """C3: the service's cached learner state equals a fresh replay of the log."""
    assert svc.practice.state() == PracticeEngine(world.storage).state()


# ---------------------------------------------------------------- the real planner


def test_without_a_set_up_course_there_is_nothing_to_plan(tmp_path: Path) -> None:
    w = make_world(tmp_path, ("ca",), setup=False)
    try:
        svc = w.service()
        assert svc.today().problems == 0
        turn = svc.start()
        assert turn.type == "empty"
        assert "Set up a course" in turn.message
    finally:
        w.storage.close(backup=False)


def test_a_daily_session_serves_the_planners_new_skill_blocks(world: World) -> None:
    svc = world.service()
    today = svc.today()
    assert today.problems > 0
    assert today.by_role.get("new", 0) > 0
    assert today.hours_basis == "none"  # the pack has no pace data
    turn = svc.start()
    assert turn.type == "problem"
    assert turn.problem is not None
    assert turn.problem.kind == "example"  # a new skill starts with its worked example
    turn = svc.next()
    assert turn.problem is not None
    view = turn.problem
    assert (view.kind, view.role) == ("problem", "new")
    assert view.reason.tag == "new-skill"
    assert view.attempts_allowed == 0  # no limit: retried freely
    assert view.textbook is not None
    assert view.textbook.book == "Book"  # "Book 1.1": the section's textbook line
    assert view.sitting is None
    result = answer(svc, world.clock)
    assert result.outcome == "correct"
    assert result.first_try_counted
    turn = svc.next()
    (example, first) = finals(world)
    assert (example.verdict, example.role) == ("shown", "new")
    assert (first.role, first.attempt_number, first.verdict) == ("new", 1, "correct")
    assert first.extra["plan"]["course"] == "ca"
    assert first.extra["plan"]["problem"] == first.card_id
    assert first.plan_p is not None
    assert first.learner_version == "prior"
    assert first.valid_minutes == pytest.approx(
        valid_minutes(
            TimingFacts(active_ms=40_000, solve_ms=32_000, entry_ms=4_000),
            untimed=False,
            example_opened=False,
            tier=first.tier or 1,
            target_ms=round(
                svc.practice.catalog().problems[first.card_id].standard_minutes * 60_000
            ),
        ),
        abs=0.05,
    )
    assert first.rating is None  # problems no longer get an FSRS rating ...
    assert world.storage.users.review_events() == []  # ... or a review event
    assert world.storage.users.skill_states() == {}  # ... or state rows: the log is the state
    replayed(world, svc)
    assert [o.attempt_id for o in svc.practice.observations()] == [first.id]


# ---------------------------------------------------------------- trying again


def test_a_wrong_try_is_logged_at_once_and_says_only_not_quite(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    result = submit(svc, "7")  # a known wrong answer, with feedback
    assert result.outcome == "retry"
    assert result.message == "Not quite."
    assert (result.can_retry, result.first_try_counted) == (True, True)
    assert result.solution is None
    (verdict,) = result.verdicts
    assert verdict.status == "incorrect"
    assert (verdict.message, verdict.feedback, verdict.wrong_step) == ("", None, None)
    assert FEEDBACK not in str(to_dict(result))  # the matched feedback never reaches a retry
    (row,) = world.storage.users.attempts()
    assert (row.final, row.attempt_number, row.verdict) == (False, 1, "incorrect")
    assert row.matched_wrong == 0  # kept in the log
    assert row.role == "growth"
    (obs,) = svc.practice.observations()  # the first try is the observation, at once
    assert (obs.attempt_id, obs.correct, obs.matched_wrong) == (row.id, False, 0)
    second = submit(svc, "7")
    assert second.outcome == "retry"
    assert (second.first_try_counted, second.tries_used) == (False, 2)
    assert FEEDBACK not in str(to_dict(second))
    third = submit(svc, "1")
    assert third.outcome == "correct"
    assert third.first_try_counted is False
    assert third.solution is not None
    svc.next()
    rows = world.storage.users.attempts()
    assert [(a.attempt_number, a.final, a.valid_minutes) for a in rows] == [
        (1, False, None),
        (2, False, None),
        (3, True, None),  # a later try's time is not a first try's
    ]
    assert len(svc.practice.observations()) == 1  # only the first try counts
    replayed(world, svc)


def test_give_up_shows_the_solution_with_the_matched_feedback(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    submit(svc, "7")
    result = svc.give_up(TIMING)
    assert result.outcome == "incorrect"
    assert result.first_try_counted is False
    assert result.solution is not None
    (verdict,) = result.verdicts  # the last try stays "Your answer", with its feedback now
    assert verdict.feedback == FEEDBACK
    assert verdict.wrong_step == 2
    svc.next()
    final = finals(world)[0]
    assert (final.verdict, final.attempt_number) == ("gave-up", 2)
    (obs,) = svc.practice.observations()
    assert (obs.correct, obs.aided) == (False, False)  # a wrong first try, not an aided one


def test_give_up_before_any_answer_is_an_aided_first_try(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    result = svc.give_up(TIMING)
    assert result.outcome == "incorrect"
    assert result.first_try_counted is True  # the give-up was the item's first try
    assert result.verdicts == ()
    svc.next()
    (obs,) = svc.practice.observations()
    assert (obs.correct, obs.aided, obs.minutes) == (False, True, None)


def test_show_solution_needs_a_wrong_first_try_and_ends_the_problem(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    with pytest.raises(QueueError, match="Try it first"):
        svc.show_solution()
    submit(svc, "0")
    shown = svc.show_solution()
    assert shown.outcome == "incorrect"
    assert shown.solution is not None
    with pytest.raises(QueueError, match="already answered"):
        submit(svc, "1")
    svc.next()
    assert finals(world)[0].verdict == "gave-up"


def test_an_invalid_answer_is_not_a_try_and_an_undecidable_one_is_self_graded(
    world: World,
) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    invalid = submit(svc, "?")
    assert invalid.outcome == "invalid"
    assert invalid.can_retry
    assert world.storage.users.attempts() == []
    undecided = submit(svc, "!")
    assert undecided.outcome == "self-grade"
    assert undecided.solution is not None
    graded = svc.submit({"self_grade": "matched", "timing": TIMING})
    assert graded.outcome == "correct"
    svc.next()
    (row,) = finals(world)
    assert (row.verdict, row.extra["correct"], row.extra["grader_review"]) == (
        "undecided",
        True,
        True,
    )
    (obs,) = svc.practice.observations()
    assert obs.correct


def test_too_easy_is_logged_with_a_correct_answer(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    result = submit(svc, "1")
    assert result.solution is not None
    assert result.solution.can_mark_too_easy
    assert svc.flag("too_easy").ok
    svc.next()
    assert finals(world)[0].too_easy


def test_a_sitting_is_closed_book_with_its_skill_blocks_limit(world: World) -> None:
    svc = world.service()
    script = Script(svc)
    sit: dict[str, Any] = {"sitting": "sit-1", "milestone": "M2", "time_limit": 3.5}
    a = script.problem("ca.s1.k1.t3.v0", "sitting", **sit)
    b = script.problem("ca.s1.k1.t3.v1", "sitting", **sit)
    script.problem("ca.s1.k2.t3.v0", "sitting", **sit)
    assert a.problem is not None
    assert b.problem is not None
    limit = a.problem.standard_minutes + b.problem.standard_minutes
    turn = svc.start()
    assert turn.problem is not None
    sitting = turn.problem.sitting
    assert sitting is not None
    assert (sitting.id, sitting.index, sitting.total) == ("sit-1", 1, 3)
    assert sitting.time_limit_ms == round(limit * 60_000)  # the k1 block: its two problems
    assert sitting.block_elapsed_ms == 0
    assert turn.problem.textbook is None  # closed book
    assert turn.problem.reason.tag == "exam-prep"
    with pytest.raises(QueueError, match="closed book"):
        svc.open_example()
    submit(svc, "1")
    turn = svc.next()
    assert turn.problem is not None
    second = turn.problem.sitting
    assert second is not None
    assert (second.index, second.time_limit_ms) == (2, sitting.time_limit_ms)
    assert second.block_elapsed_ms == 40_000  # the block's first problem took 40 s
    world.clock.advance(seconds=15)
    svc.tick(15_000)
    third = svc.current().problem
    assert third is not None
    assert third.sitting is not None
    assert third.sitting.block_elapsed_ms == 55_000
    submit(svc, "1")
    turn = svc.next()
    assert turn.problem is not None
    assert turn.problem.sitting is not None
    assert turn.problem.sitting.block_elapsed_ms == 0  # another skill's block
    row = finals(world)[0]
    assert (row.role, row.sitting, row.milestone) == ("sitting", "sit-1", "M2")
    assert row.extra["plan"]["time_limit"] == 3.5


def test_a_skill_set_aside_by_the_replan_says_so_with_its_textbook(world: World) -> None:
    svc, script = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    submit(svc, "0")
    svc.give_up(TIMING)
    script.set_aside = ("ca.s1.k1",)  # the re-plan after this answer sets the skill aside
    script.notes = ("ca.s1.k1: set aside for today after 3 misses in a row. Textbook: ca.s1.",)
    turn = svc.next()
    assert turn.message == "CA skill 1.1 is set aside for today. See Book 1.1."
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k2.t2.v0"
    today = svc.today()
    assert today.set_aside == ("CA skill 1.1",)
    assert today.notes == (turn.message,)  # the planner's note, in the same plain words
    assert svc.current().message == ""  # said once, on the turn after the answer


def test_ladder_items_carry_their_reason_code(world: World) -> None:
    svc = world.service()
    script = Script(svc)
    script.problem("ca.s1.k1.t1.v0", reason="ladder:smaller", ladder=1)
    turn = svc.start()
    assert turn.problem is not None
    assert turn.problem.plan_reason == "ladder:smaller"
    assert turn.problem.reason.label == "Smaller step"
    submit(svc, "1")
    svc.next()
    row = finals(world)[0]
    assert (row.ladder, row.extra["plan"]["reason"]) == (1, "ladder:smaller")


# ---------------------------------------------------------------- committing


def test_a_final_answer_is_held_until_continue_then_committed_with_the_session(
    world: World,
) -> None:
    svc, script = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    submit(svc, "1")
    assert world.storage.users.attempts() == []  # held in the session row
    session = world.storage.users.latest_open_session()
    assert session is not None
    assert session.current is not None
    assert session.current["pending"]["correct"]
    calls = script.calls
    turn = svc.next()
    (row,) = world.storage.users.attempts()
    assert row.final
    assert row.session_id == session.id
    assert script.calls > calls  # the rest of the day was planned again
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k2.t2.v0"
    row_session = world.storage.users.session(session.id or 0)
    assert row_session is not None
    assert "replan" not in row_session.extra


def test_the_replan_after_each_answer_uses_the_served_items(world: World) -> None:
    svc, _script = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0", "ca.s1.k3.t2.v0")
    svc.start()
    submit(svc, "1")
    svc.next()
    served = svc.practice.served(svc.practice.days().day_of(world.clock.now_ms()))
    assert [
        (c, s.item.problem.problem_id if s.item.problem else None, s.correct) for c, s in served
    ] == [("ca", "ca.s1.k1.t2.v0", True)]
    # A second session the same day goes on where the first stopped.
    svc.end()
    turn = svc.start()
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k2.t2.v0"


def test_undo_on_the_verdict_screen_voids_the_tries_and_brings_it_back_aided(
    world: World,
) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    submit(svc, "0")
    submit(svc, "1")  # right on the second try: the solution is on screen
    turn = svc.undo()
    assert turn.message.startswith("Undone")
    assert turn.problem is not None
    assert turn.result is None
    assert [a.voided_by is not None for a in world.storage.users.attempts(include_voided=True)] == [
        True
    ]
    assert svc.practice.observations() == []
    submit(svc, "1")
    svc.next()
    row = finals(world)[0]
    assert row.extra["solution_seen"]
    (obs,) = svc.practice.observations()
    assert (obs.correct, obs.aided) == (True, True)  # undo never turns a miss into a success
    replayed(world, svc)


def test_undo_after_continue_restores_the_plan_and_replays_the_learner(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0", "ca.s1.k3.t2.v0")
    svc.start()
    submit(svc, "1")
    svc.next()
    before = svc.practice.state()
    assert len(svc.practice.observations()) == 1
    turn = svc.undo()
    assert turn.message.startswith("Undone")
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k1.t2.v0"
    assert svc.practice.observations() == []
    assert svc.practice.state() != before
    assert svc.practice.state() == PracticeEngine(world.storage).state()
    # A clean first-try success comes back clean (its solution taught nothing new).
    submit(svc, "1")
    svc.next()
    (obs,) = svc.practice.observations()
    assert (obs.correct, obs.aided) == (True, False)
    # ... a miss comes back aided.
    submit(svc, "0")
    svc.give_up(TIMING)
    svc.next()
    svc.undo()
    submit(svc, "1")
    svc.next()
    last = svc.practice.observations()[-1]
    assert (last.correct, last.aided) == (True, True)
    replayed(world, svc)


def test_undo_is_refused_after_a_later_answer(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    submit(svc, "1")
    svc.next()
    submit(svc, "0")  # a "Not quite" on the next problem is a later answer
    turn = svc.undo()
    assert not turn.message.startswith("Undone")
    assert len(finals(world)) == 1


def test_a_dispute_voids_the_answer_and_logs_it_together(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    submit(svc, "0")
    svc.give_up(TIMING)
    result = svc.flag("dispute", "my answer was right")
    assert (result.ok, result.attempt_counts) == (True, False)
    rows = world.storage.users.attempts(include_voided=True)
    assert rows
    assert all(a.voided_by is not None for a in rows)
    (dispute,) = world.storage.users.disputes()
    assert dispute.attempt_id == rows[-1].id
    assert svc.practice.observations() == []


def test_report_hides_the_card_and_serves_another(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    turn = svc.start()
    assert turn.problem is not None
    assert svc.flag("report", "typo").ok
    assert "ca.s1.k1.t2.v0" in svc.practice.unavailable()
    turn = svc.current()
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k2.t2.v0"


# ---------------------------------------------------------------- the day rolls over


def test_a_held_answer_is_committed_at_its_own_time_when_the_day_rolls_over(
    world: World,
) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    first = svc.start()
    submit(svc, "1")
    answered_at = world.clock.now_ms()
    day = first.session_id
    world.clock.advance(days=1)  # left on the verdict screen overnight
    turn = svc.start()
    (row,) = world.storage.users.attempts()
    assert row.at == answered_at
    assert row.study_day == START.date().isoformat()  # yesterday's answer
    assert row.final
    assert row.verdict == "correct"
    old = world.storage.users.session(day or 0)
    assert old is not None
    assert old.ended_at is not None
    assert turn.session_id != day
    assert turn.problem is not None
    assert turn.problem.card.id == "ca.s1.k1.t2.v0"  # a new day: the plan starts over
    (obs,) = svc.practice.observations()
    assert obs.study_day == START.date()
    replayed(world, svc)


def test_resume_after_a_reopen_keeps_the_tries(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    submit(svc, "0")
    world.clock.advance(seconds=10)
    svc.tick(50_000, draft="1")
    world.reopen()
    svc2 = world.service()
    Script(svc2).problem("ca.s1.k1.t2.v0")
    turn = svc2.resume()
    assert turn is not None
    assert turn.problem is not None
    assert (turn.problem.tries_used, turn.problem.draft, turn.problem.active_ms) == (
        1,
        "1",
        50_000,
    )
    result = submit(svc2, "1")
    assert (result.outcome, result.first_try_counted) == ("correct", False)


def test_a_crash_between_the_commit_and_the_replan_is_finished_on_resume(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc, script = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    svc.start()
    submit(svc, "1")

    def crash(*_: Any, **__: Any) -> Any:
        raise SystemExit("killed after the commit")

    monkeypatch.setattr(svc, "_replan", crash)
    with pytest.raises(SystemExit):
        svc.next()
    session = world.storage.users.latest_open_session()
    assert session is not None
    assert session.extra.get("replan")  # the commit went in with its follow-up marked
    assert len(finals(world)) == 1
    world.reopen()
    svc2 = world.service()
    script2 = Script(svc2)
    script2.items = list(script.items)
    turn = svc2.resume()
    assert turn is not None
    assert turn.problem is not None
    session = world.storage.users.latest_open_session()
    assert session is not None
    assert "replan" not in session.extra
    assert script2.calls >= 1  # the re-plan ran
    assert len(finals(world)) == 1  # and the answer was not committed twice


# ---------------------------------------------------------------- other modes


def test_extra_practice_takes_tomorrows_growth_and_maintenance(world: World) -> None:
    svc = world.service()
    script = Script(svc)
    script.problem("ca.s1.k1.t2.v0", role="growth")
    script.problem("ca.s1.k2.t2.v0", role="check")
    script.problem("ca.s1.k3.t2.v0", role="maintenance")
    turn = svc.start({"mode": "extra"})
    assert turn.mode == "extra"
    session = world.storage.users.latest_open_session()
    assert session is not None
    plan = Plan.from_json(session.plan)
    assert [i.card_id for i in plan.items] == ["ca.s1.k1.t2.v0", "ca.s1.k3.t2.v0"]
    assert turn.problem is not None
    assert "tomorrow" in turn.problem.reason.why


def test_a_practice_test_is_graded_at_the_end_and_unanswered_problems_are_no_evidence(
    world: World,
) -> None:
    users = world.storage.users
    exam_at = to_ms(START + timedelta(days=10))
    exam = users.add_exam(Exam(course_id="ca", name="Midterm", at=exam_at, sections=("ca.s1",)))
    svc = world.service()
    with pytest.raises(QueueError, match="Pick an exam"):
        svc.start({"mode": "practice-test", "exam_id": 999})
    turn = svc.start({"mode": "practice-test", "exam_id": exam.id, "count": 4})
    assert turn.mode == "practice-test"
    session = users.latest_open_session()
    assert session is not None
    plan = Plan.from_json(session.plan)
    assert len(plan.items) == 4  # tier-3 problems over the scope's skills, each once first
    assert [i.skill_id for i in plan.items] == [*S1, S1[0]]
    assert all((i.meta or {}).get("tier") == 3 for i in plan.items)
    first = submit(svc, "1")
    assert first.outcome == "recorded"
    assert first.solution is None
    assert users.attempts() == []  # nothing graded until the end
    svc.next()
    submit(svc, "0")
    summary = svc.end()  # stopped with two problems unanswered
    test = summary.test
    assert test is not None
    assert (test.total, test.answered, test.correct) == (4, 2, 1)
    rows = users.attempts()
    assert len(rows) == 4
    assert {a.role for a in rows} == {"practice-test"}
    assert sum(1 for a in rows if a.extra.get("unanswered")) == 2
    observed = svc.practice.observations()
    assert len(observed) == 2  # the unanswered problem is not evidence (C5)
    assert {o.role for o in observed} == {"practice-test"}
    # Not the day's plan: the planner's served items leave the test out.
    assert svc.practice.served(svc.practice.days().day_of(world.clock.now_ms())) == []


def test_an_unknown_mode_is_refused_without_closing_the_open_session(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    svc.start()
    submit(svc, "1")
    with pytest.raises(QueueError, match="Unknown study mode"):
        svc.start({"mode": "lighter"})
    session = world.storage.users.latest_open_session()
    assert session is not None
    assert session.current is not None
    assert session.current["pending"]  # still held, still on screen


# ---------------------------------------------------------------- home and summary


def test_home_shows_the_plan_in_plain_words(world: World) -> None:
    svc, script = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0")
    script.behind = ("ca.s1.k2",)
    script.notes = (
        "At tier 4 the best attainable first-try chance is (1 - 0.050) x 0.99^3.0 = 0.922, "
        "below the accuracy target 0.95.",
        "ca.s1.k2: not yet at pace for its sitting (predicted pass 0.41: accuracy 0.62, "
        "time 0.66; it needs 0.50).",
    )
    today = svc.today()
    assert (today.problems, today.by_role) == (2, {"growth": 2})
    assert today.behind == ("CA skill 1.2",)
    assert today.notes == (
        "Your accuracy target of 95% is above what tier 4 allows: even with every skill in "
        "place, first tries top out near 92%.",
        "CA skill 1.2: not yet at pace for its sitting.",
    )
    for text in today.notes:
        assert "ca.s1" not in text
        assert "0.41" not in text
        assert "^" not in text


def test_the_summary_counts_first_tries_and_names_what_is_left_today(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0", "ca.s1.k2.t2.v0", "ca.s1.k3.t2.v0")
    svc.start()
    submit(svc, "0")
    submit(svc, "1")  # right on the second try: a miss
    svc.next()
    submit(svc, "1")
    svc.next()
    summary = svc.end()
    assert (summary.problems, summary.correct, summary.missed) == (2, 1, 1)
    assert [m.card_id for m in summary.misses] == ["ca.s1.k1.t2.v0"]
    assert summary.ready_today == 1  # the plan's third problem is still there today
    assert summary.forecast.problems == 3


def test_a_session_from_an_older_build_is_closed_not_resumed(world: World) -> None:
    svc, _ = scripted(world, "ca.s1.k1.t2.v0")
    users = world.storage.users
    from core.model import SessionState

    old = Plan(day=START.date().isoformat(), mode="daily")
    users.start_session(SessionState(study_day=START.date().isoformat(), plan=old.to_json()))
    turn = svc.start()
    assert turn.problem is not None  # a fresh wave 2 plan
    session = users.latest_open_session()
    assert session is not None
    assert Plan.from_json(session.plan).info.get("engine") == 2


def test_setup_changes_reach_the_next_plan(world: World) -> None:
    users = world.storage.users
    svc = world.service()
    before = svc.today().problems
    assert before > 0
    later = CourseSetup(course_id="ca", start=START.date() + timedelta(days=30))
    users.set_course_setup(later)
    assert svc.today().problems == 0  # nothing is introduced before the course starts
    users.set_course_setup(replace(later, start=START.date()))
    assert svc.today().problems == before
