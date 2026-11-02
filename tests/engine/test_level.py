"""ENG-10: Level transitions, shaky and demotion, Fading, mixed check-ups."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from core.engine.config import AGAIN, GOOD, HARD
from core.engine.level import (
    Evidence,
    checkup_candidates,
    checkup_due,
    evidence_log,
    exam_level_met,
    is_fading,
    mastered_met,
    update_level,
)
from core.model import SkillState

TARGETS = {2: 40_000, 3: 60_000, 4: 90_000}
D0 = date(2026, 9, 1)


def ev(n: int, **kw: object) -> Evidence:
    base: dict[str, object] = {
        "day": (D0 + timedelta(days=n)).isoformat(),
        "tier": 3,
        "clean": True,
        "rating": GOOD,
        "speed_ms": 50_000,
        "form": "template:a",
        "recall": 0.95,
        "elapsed_days": 3.0,
    }
    base.update(kw)
    return Evidence(**base)  # type: ignore[arg-type]


def state(level: str = "learned", log: list[Evidence] = (), **kw: object) -> SkillState:  # type: ignore[assignment]
    return SkillState(
        skill_id="s.one",
        fsrs_state=2,
        stability=10.0,
        difficulty=5.0,
        last_review_at=0,
        level=level,  # type: ignore[arg-type]
        level_evidence={"log": [e.as_json() for e in log]},
        **kw,  # type: ignore[arg-type]
    )


def step(s: SkillState, entry: Evidence) -> SkillState:
    change = update_level(s, entry, exam_tier=3, targets=TARGETS, correct_in_a_row=3)
    return replace(
        s,
        level=change.level,
        shaky=change.shaky,
        shaky_reviews=change.shaky_reviews,
        learning_streak=change.learning_streak,
        level_evidence=change.evidence,
    )


# ---------------------------------------------------------------- Exam-level


def test_learned_to_exam_level_needs_two_days_and_pace():
    s = state()
    s = step(s, ev(0))
    s = step(s, ev(0))
    s = step(s, ev(0))
    assert s.level == "learned"  # three on one day
    s = step(s, ev(1))
    assert s.level == "exam"


def test_exam_level_uses_median_of_last_three_times():
    log = [ev(0, speed_ms=50_000), ev(1, speed_ms=70_000), ev(2, speed_ms=80_000)]
    assert not exam_level_met(log, 3, TARGETS)  # median 70 s > 60 s
    log.append(ev(3, speed_ms=40_000))
    log.append(ev(4, speed_ms=55_000))
    assert exam_level_met(log, 3, TARGETS)  # last three 80, 40, 55 -> 55 s


@pytest.mark.parametrize(
    "log",
    [
        [ev(0, tier=2), ev(1, tier=2), ev(2, tier=2)],  # not at the exam tier
        [ev(0, clean=False), ev(1, clean=False), ev(2)],  # not correct
        [ev(0), ev(1), ev(2, speed_ms=None)],  # only two timed
    ],
)
def test_exam_level_blocked(log):
    assert not exam_level_met(log, 3, TARGETS)


def test_exam_level_needs_a_target():
    assert not exam_level_met([ev(0), ev(1), ev(2)], 3, {})


# ---------------------------------------------------------------- Mastered


def mastered_log() -> list[Evidence]:
    return [
        ev(0, form="template:a"),
        ev(3, form="template:b", elapsed_days=8.0, recall=0.88),
        ev(9, tier=4, form="card:x", speed_ms=80_000),  # above the exam tier
        ev(12),
    ]


def test_mastered_when_every_condition_holds():
    assert mastered_met(mastered_log(), 3, TARGETS)


@pytest.mark.parametrize(
    "spoil",
    [
        lambda log: [replace(e, day=log[0].day) for e in log],  # one day only
        lambda log: [replace(e, elapsed_days=3.0) for e in log],  # never after 7+ days
        lambda log: [replace(e, recall=0.95) for e in log],  # never at recall <= 0.90
        lambda log: [replace(e, form="template:a") for e in log],  # one form
        lambda log: [replace(e, tier=3) for e in log],  # nothing above exam tier, no checkup
        lambda log: [*log[:-1], replace(log[-1], speed_ms=61_000)],  # last three not at pace
    ],
)
def test_mastered_blocked_by_each_missing_condition(spoil):
    assert not mastered_met(spoil(mastered_log()), 3, TARGETS)


def test_mixed_checkup_success_satisfies_the_above_exam_tier_rule():
    log = [replace(e, tier=3) for e in mastered_log()]
    log[2] = replace(log[2], checkup=True, speed_ms=50_000)
    assert mastered_met(log, 3, TARGETS)


def test_exam_level_promotes_to_mastered():
    s = state("exam", mastered_log()[:-1])
    s = step(s, mastered_log()[-1])
    assert s.level == "mastered"


# ---------------------------------------------------------------- shaky and demotion


def test_one_miss_marks_shaky_and_a_second_within_three_reviews_drops_a_level():
    s = state("mastered", mastered_log())
    s = step(s, ev(20, rating=AGAIN, clean=False))
    assert s.level == "mastered"
    assert s.shaky
    s = step(s, ev(21, rating=GOOD))
    s = step(s, ev(22, rating=AGAIN, clean=False))
    assert s.level == "exam"
    assert not s.shaky
    assert evidence_log(s) == []  # getting Mastered back needs new evidence
    s = step(s, ev(23, rating=AGAIN, clean=False))
    assert s.shaky
    s = step(s, ev(24, rating=AGAIN, clean=False))
    assert s.level == "learned"


def test_three_clean_reviews_clear_shaky():
    s = state("exam", [ev(0), ev(1), ev(2)])
    s = step(s, ev(5, rating=AGAIN, clean=False))
    assert s.shaky
    for n in (6, 7):
        s = step(s, ev(n, rating=HARD))
        assert s.shaky
    s = step(s, ev(8))
    assert not s.shaky
    assert s.level == "exam"
    s = step(s, ev(9, rating=AGAIN, clean=False))
    assert s.shaky
    assert s.level == "exam"


def test_unrated_answers_do_not_count_as_shaky_reviews():
    s = state("exam", [ev(0), ev(1), ev(2)], shaky=True, shaky_reviews=2)
    s = step(s, ev(6, rating=None))  # stretch or reinforcement
    assert s.shaky
    assert s.shaky_reviews == 2


def test_shaky_blocks_promotion():
    s = state("exam", mastered_log()[:-1], shaky=True)
    s = step(s, mastered_log()[-1])
    assert s.level == "exam"


def test_miss_while_learned_returns_to_learning_and_three_clean_bring_it_back():
    s = state("learned", [ev(0)])
    s = step(s, ev(1, rating=AGAIN, clean=False))
    assert s.level == "learning"
    s = step(s, ev(1, rating=None))  # the reinforcement problem counts
    s = step(s, ev(2, clean=False, rating=HARD))
    assert s.level == "learning"
    assert s.learning_streak == 0
    for n in (3, 4):
        s = step(s, ev(n))
    assert s.level == "learning"
    s = step(s, ev(5))
    assert s.level == "learned"
    assert evidence_log(s) == []


def test_slip_rated_hard_is_not_a_miss():
    s = state("exam", [ev(0), ev(1), ev(2)])
    s = step(s, ev(3, rating=HARD, clean=False))
    assert not s.shaky


# ---------------------------------------------------------------- Fading and check-ups


def test_fading_is_a_recall_warning():
    assert is_fading(0.79)
    assert not is_fading(0.80)
    assert not is_fading(None)


def test_checkup_due_every_three_weeks():
    assert checkup_due(None, D0, 3)
    assert not checkup_due(D0, D0 + timedelta(days=20), 3)
    assert checkup_due(D0, D0 + timedelta(days=21), 3)
    assert not checkup_due(None, D0, None)


def test_checkup_candidates_skip_due_recent_and_unlearned():
    rows = [
        replace(state("exam"), skill_id="a.exam"),
        replace(state("learned"), skill_id="b.learned"),
        replace(state("mastered"), skill_id="c.mastered"),
        replace(state("learning"), skill_id="d.learning"),
        replace(state("exam"), skill_id="e.due"),
        replace(state("exam"), skill_id="f.recent"),
    ]
    today = D0 + timedelta(days=30)
    due = {r.skill_id: today + timedelta(days=5) for r in rows}
    due["e.due"] = today
    last = {r.skill_id: D0 for r in rows}
    last["f.recent"] = today - timedelta(days=2)
    picked = checkup_candidates(rows, today=today, due_days=due, day_of_review=last)
    assert picked == ["a.exam", "b.learned", "c.mastered"]
