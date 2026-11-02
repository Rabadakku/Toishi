"""Training data kept whole (C6) and clean targets with a strict label (I1)."""

from dataclasses import replace
from datetime import date, datetime
from typing import Any

from core.engine import AnswerFacts, Engine, ProblemOutcome
from core.engine.calibration import calibrate
from core.engine.config import DAY_MS, RULES_VERSION
from core.engine.histories import (
    FIT_EVENTS_KEY,
    RECALL_DAYS_KEY,
    STRICT_OK_KEY,
    build_histories,
    strict_ok_of,
    training_items,
)
from core.model import Attempt, ReviewEvent
from core.storage.clock import to_ms
from tests.engine.fitlog import learner_log
from tests.engine.helpers import DAYS
from tests.engine.sim import Student, World
from tests.engine.test_service import NY, answer, learn

OLD_RULES = "2026.10-r0"


# ---------------------------------------------------------------- C6


def test_C6_rules_version_bump_keeps_every_prefix_and_new_reviews_become_targets():
    log = learner_log(None, cards=50, reviews=4, seed=3, days=DAYS, rules_version=OLD_RULES)
    last = {}
    for e in log.events:
        last[e.target_id] = e
    # The newest review of each of the 50 learned skills is graded under the new rules.
    events = [
        replace(e, rules_version=RULES_VERSION) if last[e.target_id] is e else e for e in log.events
    ]
    histories = build_histories(events, day_of=DAYS.day_of)
    assert len(histories) == 50
    assert all(h.steps[0].delta == 0 and not h.anchored for h in histories)
    lengths = {h.key[1]: len(h.steps) for h in histories}
    items = training_items(histories)
    assert len(items) == 50  # only current-rules targets ...
    for item in items:
        assert len(item.reviews) == lengths[item.key[1]]  # ... each with its whole prefix
        assert item.at == last[item.key[1]].at
    # Before the bump the same log trains on every long-term review.
    before = training_items(
        build_histories(log.events, day_of=DAYS.day_of, rules_version=OLD_RULES)
    )
    assert len(before) == 50 * 4


def _at(day: int, hour: int, minute: int = 0) -> int:
    return to_ms(datetime(2026, 9, day, hour, minute, tzinfo=NY))


def test_C6_a_learning_phase_across_the_0400_rollover_stays_one_history(storage, clock):
    clock.set(datetime(2026, 9, 2, 3, 50, tzinfo=NY))
    engine = Engine(storage)
    refs = storage.packs.card_refs(skill_id="calc1.alg")
    example = next(r for r in refs if r.kind == "example")
    engine.grade(
        ProblemOutcome(
            card=example, facts=AnswerFacts(correct=False), at=clock.now_ms(), verdict="shown"
        )
    )
    answer(engine, clock, "calc1.alg")  # 03:50, study day Sep 1
    clock.set(datetime(2026, 9, 2, 4, 10, tzinfo=NY))  # study day Sep 2
    answer(engine, clock, "calc1.alg")
    answer(engine, clock, "calc1.alg")
    state = storage.users.skill_state("calc1.alg")
    assert state is not None
    assert state.fsrs_state == 2
    events = storage.users.review_events(target_id="calc1.alg")
    assert len({DAYS.day_of(e.at) for e in events}) == 2
    histories = engine.histories()
    assert len(histories) == 1
    assert [s.delta for s in histories[0].steps] == [0, 1, 0]
    # The block start is written explicitly ...
    notes = storage.users.attempt(events[0].attempt_id).extra[FIT_EVENTS_KEY]
    assert [n["block_start"] for n in notes] == [True, False, False]
    # ... and inferred the same way for rows written before it was (no attempts given).
    assert len(build_histories(events, day_of=DAYS.day_of)) == 1
    # The live card and a replay from the log agree (one clock).
    assert engine.recompute_memory().changed == ()


def test_C6_failed_learning_phase_ratings_are_prefix_only_events(storage, clock):
    engine = Engine(storage)
    refs = storage.packs.card_refs(skill_id="calc1.alg")
    example = next(r for r in refs if r.kind == "example")
    engine.grade(
        ProblemOutcome(
            card=example, facts=AnswerFacts(correct=False), at=clock.now_ms(), verdict="shown"
        )
    )
    for _ in range(6):
        rec = answer(engine, clock, "calc1.alg", correct=False)
    assert rec.result.effects.learning_failed
    failed = storage.users.review_events(target_id="calc1.alg")
    assert [e.rating for e in failed] == [1] * 6
    notes = rec.attempt.extra[FIT_EVENTS_KEY]
    assert {n["kind"] for n in notes} == {"learning-failed"}
    assert {n["role"] for n in notes} == {"prefix"}
    assert [n["block_start"] for n in notes] == [True] + [False] * 5
    assert storage.users.skill_state("calc1.alg").fsrs_state is None  # still no card
    clock.advance(days=1)
    learn(engine, clock, "calc1.alg")
    passed = storage.users.attempts(skill_id="calc1.alg")[-1].extra[FIT_EVENTS_KEY]
    assert [n["block_start"] for n in passed] == [False, False, False]  # same block
    (history,) = engine.histories()
    assert [s.kind for s in history.steps] == ["learning-failed"] * 6 + ["learning"] * 3
    assert not any(s.target for s in history.steps[:6])
    (item,) = training_items([history])  # the next day's first answer, after the prefix
    assert len(item.reviews) == 7
    assert item.reviews[-1] == (3, 1)


def test_C3_learning_answers_in_one_millisecond_replay_to_the_stored_memory(storage, clock):
    """DEV-9: one answer logs several events with the same target, time and rating (a phase
    answered within one millisecond). Each must get its own annotation, in row order, not
    the first match: that one is the block start, so every event restarted the history and
    the replay kept only the last rating."""
    engine = Engine(storage)
    refs = storage.packs.card_refs(skill_id="calc1.alg")
    example = next(r for r in refs if r.kind == "example")

    def phase(correct: bool, n: int) -> Any:
        at = clock.now_ms()  # the clock stands still: every answer at the same instant
        engine.grade(
            ProblemOutcome(card=example, facts=AnswerFacts(correct=False), at=at, verdict="shown")
        )
        for _ in range(n):
            pick = engine.pick_problem("calc1.alg")
            assert pick is not None
            rec = engine.grade(
                ProblemOutcome(card=pick.card, facts=AnswerFacts(correct=correct), at=at)
            )
        return rec

    assert phase(False, 6).result.effects.learning_failed  # six Again, prefix events
    clock.advance(days=1)
    phase(True, 3)  # passes: three Good, one attempt
    state = storage.users.skill_state("calc1.alg")
    assert state is not None
    assert state.fsrs_state == 2
    events = storage.users.review_events(target_id="calc1.alg")
    assert [(e.rating, e.at - events[0].at) for e in events] == [(1, 0)] * 6 + [(3, DAY_MS)] * 3
    (history,) = engine.histories()
    assert [s.kind for s in history.steps] == ["learning-failed"] * 6 + ["learning"] * 3
    assert engine.recompute_memory().changed == ()


# ---------------------------------------------------------------- I1


def _attempt(aid: int, at: int, stage: str, **kw: object) -> Attempt:
    base: dict[str, object] = {
        "id": aid,
        "at": at,
        "card_id": f"c{aid}",
        "skill_id": "s.a",
        "verdict": "correct",
        "rating": 3,
        "extra": {"stage": stage},
    }
    base.update(kw)
    return Attempt(**base)  # type: ignore[arg-type]


def _event(eid: int, at: int, rating: int, last: int | None, aid: int, **kw: object) -> ReviewEvent:
    return ReviewEvent(
        id=eid,
        at=at,
        attempt_id=aid,
        target_kind="skill",
        target_id="s.a",
        rating=rating,
        rules_version=RULES_VERSION,
        predicted_recall=kw.pop("predicted", 0.9),  # type: ignore[arg-type]
        state_before={
            "stability": None if last is None else 5.0,
            "difficulty": None if last is None else 5.0,
            "last_review_at": last,
        },
    )


def test_I1_no_fit_item_ends_on_a_settled_stretch_or_post_stretch_event():
    d = DAY_MS
    t = _at(1, 12)
    attempts = {
        1: _attempt(1, t + 2, "learning"),
        2: _attempt(2, t + 3 * d, "review"),
        3: _attempt(3, t + 8 * d, "stretch"),  # a stretch success: rated
        4: _attempt(4, t + 20 * d, "review", check_of=9),  # settles the day-19 miss
        5: _attempt(5, t + 30 * d, "stretch", verdict="incorrect", rating=None),  # no event
        6: _attempt(6, t + 30 * d + 600_000, "review"),  # the core-band follow-up
        7: _attempt(7, t + 40 * d, "review"),
    }
    events = [
        _event(1, t, 3, None, 1, predicted=None),
        _event(2, t + 1, 3, None, 1, predicted=None),
        _event(3, t + 2, 3, None, 1, predicted=None),
        _event(4, t + 3 * d, 3, t + 2, 2),
        _event(5, t + 8 * d, 3, t + 3 * d, 3, predicted=None),
        _event(6, t + 19 * d, 2, t + 8 * d, 4, predicted=None),
        _event(7, t + 30 * d + 600_000, 3, t + 19 * d, 6),
        _event(8, t + 40 * d, 1, t + 30 * d + 600_000, 7),
    ]
    (history,) = build_histories(events, day_of=DAYS.day_of, attempts=attempts)
    kinds = [s.kind for s in history.steps]
    assert kinds == [
        "learning",
        "learning",
        "learning",
        "review",
        "stretch",
        "settled",
        "post-stretch",
        "review",
    ]
    items = training_items([history])
    ends = [history.steps[len(i.reviews) - 1].kind for i in items]
    assert ends == ["review", "review"]
    assert [len(i.reviews) for i in items] == [4, 8]  # prefixes keep every event


def test_I1_strict_label_defaults_safely_and_grading_can_set_it():
    clean = _attempt(1, 0, "review")
    assert strict_ok_of(clean)
    assert not strict_ok_of(replace(clean, verdict="incorrect", rating=2))  # a slip (Hard)
    assert not strict_ok_of(replace(clean, attempt_number=2))
    assert not strict_ok_of(replace(clean, hints_used=1))
    assert not strict_ok_of(replace(clean, extra={STRICT_OK_KEY: False}))
    assert strict_ok_of(replace(clean, verdict="incorrect", extra={STRICT_OK_KEY: True}))


def test_I1_engine_logs_the_strict_label_and_whole_day_recall(storage, clock):
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    clock.advance(days=2, hours=10)
    rec = answer(engine, clock, "calc1.lim")
    extra = rec.attempt.extra
    assert extra[STRICT_OK_KEY] is True
    # Fractional recall (2.4 days) is logged as predicted_recall, whole-day recall beside it.
    assert extra[RECALL_DAYS_KEY] > rec.attempt.predicted_recall
    assert extra[FIT_EVENTS_KEY][0]["kind"] == "review"


def test_I1_a_slipping_learner_shows_strict_success_below_predicted_recall():
    """10% of recalled answers are careless slips. Since decision D1 (ADR-0014) a slip is
    Again, so the rated bins see it too: rated and strict labels agree and both fall short.
    FSRS also sees each slip and shortens the next interval, so the gap is smaller than
    slip rate x mean recall (0.1 x 0.88)."""
    rated: list[tuple[float, bool]] = []
    strict: list[tuple[float, bool]] = []
    for seed in (1, 2, 3):
        world = World(
            Student("slippy", slip=0.10),
            [f"sim.k{i:02d}" for i in range(60)],
            start=date(2026, 9, 1),
            days=DAYS,
            seed=seed,
        )
        world.run(60)
        for history in world.history.values():
            for a in history:
                if a.extra.get("stage") == "review" and a.rating and a.predicted_recall:
                    rated.append((a.predicted_recall, a.rating > 1))
                    strict.append((a.predicted_recall, strict_ok_of(a)))
    old_rule = calibrate(rated)
    label = calibrate(strict)
    assert old_rule.total > 900
    gap = label.observed - label.expected
    assert -0.13 < gap < -0.03  # a learner without slips: about -0.01
    # The rated bins are no longer blind to slips: every slip is a fail there as well.
    assert [ok for _, ok in rated] == [ok for _, ok in strict]
    assert old_rule.mean_error == label.mean_error
    assert label.alarm
    assert old_rule.alarm
