"""Queue simulations: a month of three courses with exams, crashes, undo, practice tests."""

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from core.model import CourseGoal, Exam
from core.queue import Plan, StudyService, Turn
from core.storage.clock import to_ms
from tests.queue.helpers import NY, World, answer, make_world
from tests.queue.sim import DayLog, Student, per_course, run, summary


@pytest.fixture
def month(tmp_path: Path) -> Iterator[World]:
    w = make_world(
        tmp_path,
        ("ca", "cb", "cc"),
        sections=3,
        skills=4,
        seeds=6,
        flashcards=True,
        confusable=[("ca.s1.k2", "ca.s1.k3")],
    )
    users = w.storage.users
    users.set_course_goal(CourseGoal(course_id="cb", goal="B"))
    users.set_course_goal(CourseGoal(course_id="cc", goal="Keep"))
    users.add_exam(
        Exam(
            course_id="ca",
            name="Midterm A",
            minutes=60,
            problems=6,
            at=to_ms(datetime(2026, 9, 22, 9, tzinfo=NY)),
        )
    )
    users.add_exam(
        Exam(course_id="cb", name="Midterm B", at=to_ms(datetime(2026, 9, 26, 9, tzinfo=NY)))
    )
    yield w
    w.storage.close(backup=False)


def check_days(student: Student) -> list[DayLog]:
    """Invariants of every simulated day; returns the days that had a plan."""
    days = [d for d in student.days if d.count]
    for log in days:
        # Quotas add up to the count exactly (free = slots no course had work for).
        assert sum(log.quotas.values()) + log.free == log.count == 20
        if log.need >= log.count:
            assert log.free == 0
        if not log.stopped_early:
            for course, quota in log.quotas.items():
                if quota > 0:
                    assert log.served[course] > 0, (log.day, course)  # no course starved
        assert all(g >= 3 for g in log.check_gaps)
        assert all(g >= 5 for g in log.reinforcement_gaps)
    return days


def test_a_week_with_three_courses(month: World) -> None:
    student = run(month, 7, stop_on=lambda d: 4 if d == 3 else None)
    days = check_days(student)
    assert len(days) == 7
    assert {c for d in days for c in d.served} == {"ca", "cb", "cc"}


@pytest.mark.slow
def test_a_month_with_three_courses_and_exams(month: World) -> None:
    student = run(month, 30, stop_on=lambda d: 5 if d in (5, 13) else None, skip=lambda d: d == 9)
    days = check_days(student)
    assert len(days) >= 25
    served = {c: sum(v) for c, v in per_course(days).items()}
    total = sum(served.values())
    assert set(served) == {"ca", "cb", "cc"}
    assert min(served.values()) >= 0.15 * total
    gaps = [g for d in days for g in d.check_gaps]
    assert gaps
    assert min(gaps) >= 3
    reinforcement = [g for d in days for g in d.reinforcement_gaps]
    assert reinforcement
    assert min(reinforcement) >= 5
    tags = summary(student)["tags"]
    assert {"new-skill", "review", "check", "exam-prep"} <= set(tags)


def test_resume_after_a_crash_continues_the_same_session(month: World) -> None:
    student = run(month, 3)
    svc = student.service
    turn = svc.start()
    session = month.storage.users.latest_open_session()
    assert session is not None
    turn = student.work(turn, stop_after=3)
    assert turn.problem is not None
    on_screen = turn.problem.item_key
    month.clock.advance(seconds=20)
    svc.tick(20_000, draft="draft")
    month.reopen()
    svc2 = month.service()
    resumed = svc2.start()
    assert resumed.session_id == session.id
    assert resumed.problem is not None
    assert resumed.problem.item_key == on_screen
    assert resumed.problem.draft == "draft"
    assert resumed.problem.active_ms == 20_000
    student2 = Student(month, svc2, student.rng)
    end = student2.work(resumed)
    assert end.type == "summary"
    final = Plan.from_json((month.storage.users.session(session.id or 0) or session).plan)
    ids = [(i.result or {}).get("attempt_id") for i in final.items if i.status == "done"]
    assert None not in ids
    assert len(ids) == len(set(ids))


def to_problem(student: Student, turn: Turn) -> Turn:
    """Serve worked examples and flashcards until a problem is on screen."""
    while turn.problem is not None and turn.problem.kind != "problem":
        if turn.problem.kind == "flashcard":
            student.service.rate_flashcard(3)
        turn = student.service.next()
    return turn


def test_a_crash_between_grading_and_replanning_is_recovered(
    month: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    student = run(month, 2)
    svc = student.service
    turn = to_problem(student, svc.start())

    def in_review(t: Turn) -> bool:
        card = month.storage.packs.card(t.problem.card.id)  # type: ignore[union-attr]
        state = month.storage.users.skill_state(card.skill_id or "")  # type: ignore[union-attr]
        return state is not None and state.fsrs_state == 2

    while not in_review(turn):  # a review problem, so the miss has follow-ups
        answer(svc, month.clock)
        turn = to_problem(student, svc.next())
    assert turn.problem is not None
    assert turn.problem.kind == "problem"
    answer(svc, month.clock, correct=False)
    answer(svc, month.clock, correct=False)
    calls: list[Any] = []

    def crash(*args: Any, **kw: Any) -> Any:
        calls.append(args)
        raise RuntimeError("power cut")

    monkeypatch.setattr(StudyService, "_after_answer", crash)
    with pytest.raises(RuntimeError):
        svc.next()
    monkeypatch.undo()
    graded = [a for a in month.storage.users.attempts() if a.final]
    month.reopen()
    svc2 = month.service()
    resumed = svc2.resume()
    assert resumed is not None
    session = month.storage.users.latest_open_session()
    assert session is not None
    assert "replan" not in session.extra
    plan = Plan.from_json(session.plan)
    item = plan.item(turn.problem.item_key)
    assert item is not None
    assert item.key in plan.replanned
    assert (item.result or {}).get("attempt_id") == graded[-1].id
    # The miss's follow-ups were planned from the stored attempt.
    assert [i for i in plan.items if i.anchor == item.key]
    assert len([a for a in month.storage.users.attempts() if a.final]) == len(graded)


def test_undo_in_a_busy_session_is_exact(month: World) -> None:
    student = run(month, 4)
    svc = student.service
    users = month.storage.users
    turn = to_problem(student, student.work(svc.start(), stop_after=2))
    assert turn.problem is not None
    assert turn.problem.kind == "problem"
    before = (
        users.skill_states(),
        users.card_users(),
        users.skill_tiers(),
        users.pending_checks(None),
        len(users.review_events()),
    )
    plan_before = Plan.from_json((users.latest_open_session() or None).plan)  # type: ignore[union-attr]
    turn = student.work(turn, stop_after=1)
    back = svc.undo()
    after = (
        users.skill_states(),
        users.card_users(),
        users.skill_tiers(),
        users.pending_checks(None),
        len(users.review_events()),
    )
    assert after == before
    plan_after = Plan.from_json((users.latest_open_session() or None).plan)  # type: ignore[union-attr]
    assert plan_after.items == plan_before.items
    assert back.problem is not None


def test_practice_test_in_the_exam_window_is_graded_at_the_end(month: World) -> None:
    month.storage.users.add_exam(
        Exam(course_id="cc", name="Quiz C", at=to_ms(datetime(2026, 9, 12, 9, tzinfo=NY)))
    )
    student = run(month, 4)  # Sep 5: the quiz is 7 days away
    svc = student.service
    today = svc.today()
    offer = next(e for e in today.exams if e.name == "Quiz C")
    assert offer.practice_test
    events = len(month.storage.users.review_events())
    turn = svc.start({"mode": "practice-test", "exam_id": offer.exam_id, "count": 4})
    answered = 0
    while turn.type == "problem":
        result = answer(month.service(), month.clock, correct=answered % 2 == 0)
        assert result.outcome == "recorded"
        answered += 1
        turn = svc.current()
    assert turn.summary is not None
    assert turn.summary.test is not None
    assert turn.summary.test.answered == answered == 4
    assert turn.summary.test.correct == 2
    assert len(month.storage.users.review_events()) > events  # results count as reviews
