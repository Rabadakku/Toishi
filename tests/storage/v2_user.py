"""Builder of the frozen realistic v2 fixture for the schema v3 migration (wave 2).

    python -m tests.storage.v2_user <user_v2.sql>

user_v2.sql was written once by the schema v2 code (commit 18fd93b) through the real
StudyService on the Test pack, so it holds a v2 history exactly as that code wrote it:

- three study days of daily sessions: right and wrong first tries, a wrong try then a right
  one, give-ups, a hint before answering, worked examples, flashcards and cloze blanks, an
  undo (voided attempts) and session ends;
- on the fourth day a practice test over the first midterm's scope (a multi-part problem
  among its exam-tier problems, graded at the end) and focused practice on one skill;
- course goals: the Test Course with a start date (`starts_on`, which v3 copies into
  course_settings.start) and the tutorial course without one;
- two exams, one with sections in scope.

The code that wrote it is kept here to document what it holds; it only runs at v2.
"""

import contextlib
import random
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FIXTURES = Path(__file__).parent / "fixtures"
USER_V2 = FIXTURES / "user_v2.sql"
NY = ZoneInfo("America/New_York")
START = datetime(2026, 10, 5, 9, 0, tzinfo=NY)
COURSE = "Test Course"
TUTORIAL = "Answer Input Tutorial"
COURSE_START = date(2026, 9, 28)  # course_goal.starts_on of the Test Course
HOWS = ("right", "wrong", "wrong-right", "give-up", "right", "hint", "wrong", "unsure", "right")


def answer_as(svc: Any, storage: Any, turn: Any, how: Any) -> Any:
    """The study driver's answer, plus "wrong-right": a wrong try, then the right answer."""
    from tests.storage.study_driver import answer, typed

    problem = turn.problem
    if how != "wrong-right" or problem.kind != "problem" or problem.card.self_graded:
        return answer(svc, storage, turn, "wrong" if how == "wrong-right" else how)
    card = storage.packs.card(problem.card.id)
    timing = {"active_ms": 40_000, "solve_ms": 30_000, "entry_ms": 4_000}
    first = svc.submit({"answers": typed(card, False), "timing": timing})
    if first.outcome != "retry":
        return first
    return svc.submit({"answers": typed(card, True), "timing": timing})


def write_user_v2(out: Path) -> None:
    from app.packs import shipped_packs
    from core import cards, grader
    from core.model import CourseGoal, Exam
    from core.queue import QueueError, StudyService
    from core.storage import Storage
    from core.storage.clock import FixedClock, to_ms
    from core.storage.profiles import ProfilePaths
    from core.storage.schema import USER_SCHEMA_VERSION
    from tests.storage.study_driver import key_checker, typed

    assert USER_SCHEMA_VERSION == 2, "this fixture must be written by schema v2"
    packs = [p for p in shipped_packs() if p.stem in ("test", "tutorial")]
    rng = random.Random(20261102)  # noqa: S311 -- a reproducible history, not crypto
    with tempfile.TemporaryDirectory() as tmp:
        clock = FixedClock(START, tz=NY)
        paths = ProfilePaths(Path(tmp) / "p")
        storage = Storage.open(paths, pack_paths=packs, clock=clock, create=True)
        users = storage.users
        users.set_setting("study.timezone", "America/New_York")
        for section in storage.packs.sections():
            users.set_section_state(section.id, "learning")
        users.set_course_goal(CourseGoal(course_id=COURSE, goal="A", starts_on=COURSE_START))
        users.set_course_goal(CourseGoal(course_id=TUTORIAL, goal="B"))
        exam_at = to_ms(datetime(2026, 10, 20, 10, 0, tzinfo=NY))
        users.add_exam(
            Exam(
                course_id=COURSE,
                name="Midterm 1",
                at=exam_at,
                minutes=50,
                problems=5,
                sections=(
                    "Test Course::1 Algebra::1.1 Linear Equations",
                    "Test Course::1 Algebra::1.2 Quadratics",
                ),
                target_recall=0.85,
            )
        )
        users.add_exam(Exam(course_id=COURSE, name="Final", at=exam_at + 50 * 86_400_000))
        svc = StudyService(storage, checker=key_checker)
        undone = False
        for day in range(3):
            clock.set(START + timedelta(days=day))
            turn = svc.start({"mode": "daily"})
            for step in range(14):
                if turn.type != "problem" or turn.problem is None:
                    break
                clock.advance(seconds=rng.randint(20, 90))
                if turn.result is None and turn.problem.kind != "example":
                    with contextlib.suppress(QueueError):
                        answer_as(svc, storage, turn, HOWS[(day * 14 + step) % len(HOWS)])
                if day == 1 and step == 3 and not undone:
                    svc.next()
                    svc.undo()  # voids the last answer's attempts
                    undone = True
                    turn = svc.current()
                    continue
                clock.advance(seconds=5)
                turn = svc.next()
            if turn.type == "problem":
                svc.end()
        clock.set(START + timedelta(days=3))
        exam_id = users.exams()[0].id
        turn = svc.start({"mode": "practice-test", "exam_id": exam_id, "count": 18})
        for n in range(20):  # answered with no feedback; graded when the test ends
            if turn.type != "problem" or turn.problem is None:
                break
            clock.advance(seconds=rng.randint(60, 200))
            card = storage.packs.card(turn.problem.card.id)
            assert card is not None
            svc.submit({"answers": typed(card, n % 2 == 0), "timing": {"active_ms": 90_000}})
            turn = svc.current()
        if turn.type == "problem":
            svc.end()
        clock.advance(minutes=10)
        turn = svc.start({"mode": "focused", "skill_id": "test.alg.linear-solve", "count": 6})
        for step in range(10):
            if turn.type != "problem" or turn.problem is None:
                break
            clock.advance(seconds=rng.randint(20, 90))
            if turn.result is None and turn.problem.kind != "example":
                answer_as(svc, storage, turn, HOWS[step % len(HOWS)])
            turn = svc.next()
        if turn.type == "problem":
            svc.end()
        storage.close(backup=False)
        grader.shutdown()
        cards.shutdown()
        conn = sqlite3.connect(paths.user_db)
        lines = list(conn.iterdump())
        conn.close()
    out.write_text(
        "-- Frozen user.db at schema v2 with a study history (tests/storage/v2_user.py),\n"
        "-- written by the v2 code. Never edit.\n" + "\n".join(lines) + "\n"
    )


if __name__ == "__main__":
    write_user_v2(Path(sys.argv[1]))
