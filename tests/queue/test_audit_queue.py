"""Acceptance tests for the scheduler-gap audit's queue items (ADR-0014): C5 (unanswered
practice-test problems), I2 (goal changes), I5 (flashcards to Anki parity), D5 (rated
reviews aim at the desired retention) and the backlog's Off-section flashcards."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from core.engine import Engine, FsrsAdapter, Memory, StudyDays, due_day
from core.engine.fsrs_adapter import DEFAULT_PARAMS_ID
from core.engine.selection import Pick
from core.model import CourseGoal, Exam, FlashcardState
from core.queue import Plan, build_plan, gather
from core.queue.flashcards import FLASHCARD_REWRITE, grade_flashcard
from core.storage.clock import to_ms
from tests.queue.helpers import NY, World, answer, make_world, review_state

SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]
DAYS = StudyDays(NY, 4)


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    """One course, all sections Solid, every skill in review and due today; flashcards."""
    w = make_world(tmp_path, ("ca",), sections=2, skills=3, flashcards=True, state="solid")
    now = w.clock.now_ms()
    w.storage.users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in SKILLS])
    yield w
    w.storage.close(backup=False)


def plan_of(w: World) -> Plan:
    session = w.storage.users.latest_open_session()
    assert session is not None
    return Plan.from_json(session.plan)


# ---------------------------------------------------------------- C5


def test_C5_a_stopped_test_with_three_unanswered_problems_writes_unrated_attempts(
    world: World,
) -> None:
    users = world.storage.users
    exam_at = to_ms(datetime(2026, 9, 11, 9, tzinfo=NY))
    exam = users.add_exam(Exam(course_id="ca", name="Quiz", at=exam_at, minutes=40, problems=4))
    lapses = {k: s.lapses for k, s in users.skill_states().items()}
    events = len(users.review_events())
    svc = world.service()
    svc.start({"mode": "practice-test", "exam_id": exam.id})
    answer(svc, world.clock)  # one answered, then stopped
    summary = svc.end()
    test = summary.test
    assert test is not None
    assert (test.total, test.answered, test.unanswered) == (4, 1, "skip")
    unanswered = [a for a in users.attempts() if a.final and a.extra.get("unanswered")]
    assert len(unanswered) == 3  # three unrated attempts ...
    assert all(a.rating is None and a.verdict == "gave-up" for a in unanswered)
    assert all(a.strict_ok is False for a in unanswered)
    assert len(users.review_events()) == events + 1  # ... no ReviewEvent of their own ...
    assert {k: s.lapses for k, s in users.skill_states().items()} == lapses  # ... no lapse
    zeros = [x for x in test.lines if not x.answered]
    assert len(zeros) == 3
    assert all(not x.correct and x.rating is None for x in zeros)  # zero in the score


# ---------------------------------------------------------------- I5: flashcards


def test_I5_again_while_relearning_or_twice_the_same_day_leaves_lapses_unchanged() -> None:
    fsrs = FsrsAdapter()
    t0 = to_ms(datetime(2026, 9, 1, 12, tzinfo=NY))
    review = FlashcardState(
        card_id="f", fsrs_state=2, stability=10.0, difficulty=5.0, last_review_at=t0, reps=3
    )
    day = 86_400_000
    lapsed, _, _ = grade_flashcard(
        review, card_id="f", card_ord=0, rating=1, at_ms=t0 + 10 * day, adapter=fsrs, days=DAYS
    )
    assert lapsed.lapses == 1  # Again on a review card on a new day: a lapse
    again, _, _ = grade_flashcard(
        lapsed, card_id="f", card_ord=0, rating=1, at_ms=t0 + 10 * day + 600_000,
        adapter=fsrs, days=DAYS,
    )  # fmt: skip
    assert again.lapses == 1  # a second Again the same day
    relearning, _, _ = grade_flashcard(
        again, card_id="f", card_ord=0, rating=1, at_ms=t0 + 11 * day, adapter=fsrs, days=DAYS
    )
    assert relearning.lapses == 1  # an Again while relearning
    same_day_review, _, _ = grade_flashcard(
        review, card_id="f", card_ord=0, rating=1, at_ms=t0 + 600_000, adapter=fsrs, days=DAYS
    )
    assert same_day_review.lapses == 0  # same study day as its last review: not a new day


def test_I5_a_card_at_8_lapses_is_not_served_and_needs_a_rewrite(world: World) -> None:
    users = world.storage.users
    now = world.clock.now_ms()
    leech = FlashcardState(
        card_id="ca.s1.k1.fc", fsrs_state=3, stability=0.5, difficulty=9.0,
        last_review_at=now - 86_400_000, due_at=now - 3_600_000, reps=20, lapses=8, leech=True,
    )  # fmt: skip
    users.apply([leech])
    snap = gather(world.storage, Engine(world.storage))
    assert "ca.s1.k1.fc" not in {c for c, _, _ in snap.flashcards_due}
    assert snap.flashcard_leeches == 1
    assert world.service().today().flashcards_to_rewrite == 1
    # Rating the 8th lapse says so.
    users.apply([FlashcardState(
        card_id="ca.s1.k2.fc", fsrs_state=2, stability=5.0, difficulty=9.0,
        last_review_at=now - 10 * 86_400_000, due_at=now - 3_600_000, reps=20, lapses=7,
    )])  # fmt: skip
    svc = world.service()
    turn = svc.start()
    while turn.problem is not None and turn.problem.card.id != "ca.s1.k2.fc":
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        else:
            answer(svc, world.clock)
        turn = svc.next()
    assert turn.problem is not None
    result = svc.rate_flashcard(1)
    assert result.message == FLASHCARD_REWRITE
    state = users.flashcard_state("ca.s1.k2.fc", 0)
    assert state is not None
    assert (state.lapses, state.leech) == (8, True)
    assert not [i for i in plan_of(world).pending if i.card_id == "ca.s1.k2.fc"]  # no re-show


def test_I5_a_second_plan_the_same_day_offers_M_minus_done(world: World) -> None:
    users = world.storage.users
    users.set_setting("daily.flashcards", 4)
    for k in SKILLS:  # every flashcard is due
        users.apply([FlashcardState(
            card_id=f"{k}.fc", fsrs_state=2, stability=3.0, difficulty=5.0,
            last_review_at=world.clock.now_ms() - 5 * 86_400_000,
            due_at=world.clock.now_ms() - 3_600_000, reps=2,
        )])  # fmt: skip
    svc = world.service()
    turn = svc.start()
    assert plan_of(world).flashcards == 0
    assert sum(1 for i in plan_of(world).items if i.kind == "flashcard") == 4
    done = 0
    while turn.problem is not None and done < 3:
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
            done += 1
        else:
            answer(svc, world.clock)
        turn = svc.next()
    svc.end()
    snap = gather(world.storage, Engine(world.storage))
    assert snap.flashcards_done_today == 3
    second = build_plan(snap, mode="extra", flashcards=True)
    assert sum(1 for i in second.items if i.kind == "flashcard") == 4 - 3


def test_I5_new_flashcards_respect_their_own_daily_limit(world: World) -> None:
    world.storage.users.set_setting("daily.new_flashcards", 2)
    snap = gather(world.storage, Engine(world.storage))
    assert len(snap.flashcards_new) == len(SKILLS)  # all six are new
    plan = build_plan(snap)
    assert sum(1 for i in plan.items if i.kind == "flashcard") == 2


def test_I5_after_a_math_fit_the_flashcard_adapter_keeps_the_defaults(world: World) -> None:
    from fsrs.scheduler import DEFAULT_PARAMETERS

    fitted = list(DEFAULT_PARAMETERS)
    fitted[0] = 0.3
    world.storage.users.set_setting("fsrs.params.math", {"w": fitted, "id": "fit-test"})
    engine = Engine(world.storage)
    assert engine.adapter().params_id != DEFAULT_PARAMS_ID
    assert engine.adapter_for("flashcard").params_id == DEFAULT_PARAMS_ID
    # And a rated flashcard records the flashcard set's parameters.
    svc = world.service()
    turn = svc.start()
    while turn.problem is not None and turn.problem.kind != "flashcard":
        answer(svc, world.clock)
        turn = svc.next()
    assert turn.problem is not None
    svc.rate_flashcard(3)
    (attempt,) = [a for a in world.storage.users.attempts() if a.card_kind == "flashcard"]
    assert attempt.params_id == DEFAULT_PARAMS_ID
    assert attempt.strict_ok is True


def test_I5_a_missed_flashcard_comes_back_5_items_later_with_the_same_day_update(
    world: World,
) -> None:
    svc = world.service()
    turn = svc.start()
    while turn.problem is not None and turn.problem.kind != "flashcard":
        answer(svc, world.clock)
        turn = svc.next()
    assert turn.problem is not None
    missed = turn.problem.card.id
    key = turn.problem.item_key
    svc.rate_flashcard(1)
    plan = plan_of(world)
    order = [i.key for i in plan.items if i.status != "skipped"]
    (reshow,) = [i for i in plan.pending if i.card_id == missed]
    assert (reshow.anchor, reshow.purpose) == (key, "relearn")
    assert order.index(reshow.key) - order.index(key) > 5 or reshow.key == order[-1]
    first = world.storage.users.flashcard_state(missed, 0)
    assert first is not None
    turn = svc.next()
    while turn.problem is not None and turn.problem.item_key != reshow.key:
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        else:
            answer(svc, world.clock)
        turn = svc.next()
    assert turn.problem is not None
    svc.rate_flashcard(3)
    second = world.storage.users.flashcard_state(missed, 0)
    assert second is not None
    # FSRS's same-day (short-term) update, and still no lapse for a new card.
    memory = Memory(first.stability or 0, first.difficulty or 0, first.last_review_at or 0)
    same = FsrsAdapter().review(memory, 3, second.last_review_at or 0, same_day=True)
    assert second.stability == pytest.approx(same.stability)
    assert second.lapses == 0


# ---------------------------------------------------------------- backlog: Off sections


def test_backlog_flashcards_from_off_sections_are_not_served(tmp_path: Path) -> None:
    w = make_world(tmp_path, ("ca",), sections=2, skills=3, flashcards=True, state="off")
    try:
        snap = gather(w.storage, Engine(w.storage))
        assert snap.flashcards_due == []
        assert w.service().today().flashcards == 0
        w.storage.users.set_section_state("ca.s1", "solid")
        now = w.clock.now_ms()
        w.storage.users.apply([review_state("ca.s1.k1", now, days_ago=5, stability=2.0)])
        snap = gather(w.storage, Engine(w.storage))
        assert {c for c, _, _ in snap.flashcards_due} == {"ca.s1.k1.fc"}
    finally:
        w.storage.close(backup=False)


# ---------------------------------------------------------------- I2: goal change service


def test_I2_set_goal_previews_n_skills_due_and_spreads_them(world: World) -> None:
    users = world.storage.users
    now = world.clock.now_ms()
    users.set_course_goal(CourseGoal(course_id="ca", goal="Keep"))
    engine = Engine(world.storage)
    fsrs, days = engine.adapter(), engine.days()
    rows = []
    for i, k in enumerate(SKILLS):  # S = 30 reviewed 40-45 days ago: due under A, not Keep
        state = review_state(k, now, days_ago=40 + i, stability=30.0)
        cached = due_day(state, 0.80, fsrs, days)  # cached when graded, under Keep
        assert cached is not None
        rows.append(replace(state, due_at=days.start(cached)))
    users.apply(rows)
    svc = world.service()
    preview = svc.preview_goal({"course_id": "ca", "goal": "A"})
    assert preview.newly_due == len(SKILLS)
    assert preview.message == f"This makes {len(SKILLS)} skills due."
    assert users.course_goal("ca").goal == "Keep"  # type: ignore[union-attr]  # nothing saved
    applied = svc.set_goal({"course_id": "ca", "goal": "A"})
    assert applied.newly_due == len(SKILLS)
    assert sum(applied.per_day.values()) == len(SKILLS)
    assert len(applied.per_day) > 1  # spread over the following days
    today = days.day_of(now)
    due = Engine(world.storage).due_skills(today)
    assert len(due) == applied.per_day.get(today.isoformat(), 0)
    assert not any(d.escalated for d in due)
    later = Engine(world.storage).due_skills(today + timedelta(days=6))
    assert len(later) == len(SKILLS)


# ---------------------------------------------------------------- D5: Elo target


def test_D5_engine_aims_rated_reviews_at_the_course_retention(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.engine import service

    seen: list[float] = []
    real = service.pick_problem  # type: ignore[attr-defined]

    def spy(*args: Any, **kw: Any) -> Pick | None:
        seen.append(kw["target_p"])
        return real(*args, **kw)

    monkeypatch.setattr(service, "pick_problem", spy)
    engine = Engine(world.storage)
    assert engine.pick_problem("ca.s1.k1") is not None
    assert seen[-1] == pytest.approx(engine.retention("ca.s1.k1"))  # 0.90 under goal A
    world.storage.users.set_course_goal(CourseGoal(course_id="ca", goal="B"))
    engine.pick_problem("ca.s1.k1")
    assert seen[-1] == pytest.approx(0.88)
    engine.pick_problem("ca.s1.k1", stretch=True)  # stretch (unrated): 0.80
    assert seen[-1] == pytest.approx(0.80)
