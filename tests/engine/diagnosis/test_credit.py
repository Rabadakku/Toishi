"""ENG-6 pull-forward and ENG-7 partial credit in shadow mode."""

from dataclasses import replace
from datetime import timedelta

import pytest

from core.engine import due_skills
from core.engine.config import AGAIN, DAY_MS
from core.engine.diagnosis import DiagnosisSettings, credit_targets, partial_credit
from core.engine.lifecycle import due_day, memory_of, review_on
from core.model import Skill
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, allow_credit_on, answer, seed, world
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import DAYS, at_day, some

T = at_day(0)


def setup(**kw: object) -> MemoryWorld:
    w = world(**kw)
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=10, days_ago=5, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=20, theta=2.0)
    return w


# ---------------------------------------------------------------- ENG-6


def test_lapse_pulls_encompassing_skills_earlier_without_cutting_stability() -> None:
    w = setup()
    seed(w, POW, stability=10, days_ago=12, theta=0.5)
    seed(w, CRIT, stability=40, days_ago=1, theta=2.0)  # due in about a month
    before = w.states[CRIT]
    w.grade(answer(w, "c.pow.t2.0", T, correct=False, choice="cant-tell"))
    assert [e.rating for e in w.events_for(POW)] == [AGAIN]
    after = w.states[CRIT]
    assert after.stability == before.stability
    assert after.last_review_at == before.last_review_at
    assert due_day(after, 0.9, w.fsrs, DAYS) == DAYS.day_of(T) + timedelta(days=2)
    (pulled,) = [
        d
        for d in due_skills(
            w.states.values(),
            DAYS.day_of(T) + timedelta(days=2),
            retention_of=lambda _k: 0.9,
            adapter=w.fsrs,
            days=DAYS,
        )
        if d.skill_id == CRIT
    ]
    assert pulled.note is not None
    assert "Power rule" in pulled.note


def test_weight_below_half_does_not_pull() -> None:
    w = setup()
    seed(w, ALG, stability=10, days_ago=12, theta=0.5)
    seed(w, CRIT, stability=40, days_ago=1, theta=2.0)
    w.grade(answer(w, "c.alg.t2.0", T, correct=False, choice="cant-tell"))
    assert "due_adjust" not in w.states[CRIT].level_evidence  # CRIT encompasses ALG at 0.25


# ---------------------------------------------------------------- ENG-7


def test_explicit_pass_credits_encompassed_skills_in_shadow_only() -> None:
    w = setup()
    plain = w.states[POW]
    w.grade(answer(w, "crit.t3.0", T, correct=True))
    credits = {c.to_skill: c for c in w.credits}
    assert set(credits) == {POW, ALG}
    assert credits[POW].weight == 0.5
    assert credits[ALG].weight == 0.25
    assert all(c.mode == "shadow" for c in credits.values())
    shadow = w.shadows[POW].credited_stability
    assert shadow is not None
    assert shadow > some(plain.stability)
    assert w.states[POW] == plain  # the schedule keeps the plain stability
    assert {e.target_id for e in w.events} == {CRIT}  # never in review_log (optimizer data)


def test_credit_follows_the_formula_and_early_credit_is_tiny() -> None:
    w = setup()
    state = w.states[POW]
    memory = memory_of(state)
    assert memory is not None
    s_good = review_on(w.fsrs, memory, 3, T, DAYS).stability
    w.grade(answer(w, "crit.t3.0", T, correct=True))
    expected = state.stability + 0.5 * (s_good - state.stability)  # type: ignore[operator]
    assert w.shadows[POW].credited_stability == pytest.approx(expected)
    w2 = setup()
    seed(w2, POW, stability=10, days_ago=0.01, theta=2.0)  # reviewed minutes ago
    w2.grade(answer(w2, "crit.t3.0", T, correct=True))
    gain = (w2.shadows[POW].credited_stability or 0) - 10
    assert 0 <= gain < 0.5


def test_chain_weights_multiply_and_small_products_are_ignored() -> None:
    skills = {
        "a": Skill(id="a", name="A", encompasses=(("b", 0.5), ("d", 0.25))),
        "b": Skill(id="b", name="B", encompasses=(("c", 0.5), ("e", 0.25))),
        "c": Skill(id="c", name="C"),
        "d": Skill(id="d", name="D"),
        "e": Skill(id="e", name="E"),
    }
    assert credit_targets("a", skills) == {"b": 0.5, "c": 0.25, "d": 0.25}  # e: 0.125


@pytest.mark.parametrize(
    ("change", "why"),
    [
        ({"fsrs_state": 3}, "relearning"),
        ({"difficulty": 9.5}, "very difficult"),
        ({"fsrs_state": None, "stability": None}, "learning"),
    ],
)
def test_no_credit_to_relearning_learning_or_very_difficult_skills(
    change: dict[str, object], why: str
) -> None:
    w = setup()
    w.states[POW] = replace(w.states[POW], **change)  # type: ignore[arg-type]
    result = partial_credit(
        CRIT,
        now=T,
        mode="shadow",
        skills=w.skills(),
        state_of=w.state,
        shadow_of=w.shadow,
        last_failure_at=w.last_failure_at,
        adapter=w.fsrs,
        days=DAYS,
    )
    assert result.skipped[POW] == why
    assert POW not in {c.to_skill for c in result.credits}


def test_no_credit_after_a_failure_in_the_last_7_days() -> None:
    w = setup()
    seed(w, POW, stability=10, days_ago=12, theta=0.5)
    w.grade(answer(w, "c.pow.t2.0", T - 3 * DAY_MS, correct=False, choice="cant-tell"))
    w.grade(answer(w, "c.pow.t2.1", T - 2 * DAY_MS, correct=True))
    w.grade(answer(w, "crit.t3.0", T, correct=True))
    assert POW not in {c.to_skill for c in w.credits}


def test_forced_review_after_doubling_from_credit_alone() -> None:
    w = setup()
    seed(w, POW, stability=2, days_ago=8, theta=2.0)  # low recall: big credited gains
    t = T
    for i in range(6):
        seed(w, CRIT, stability=20, days_ago=20, at=t, theta=2.0)
        w.grade(answer(w, f"crit.t3.{i}", t, correct=True))
        if "credit_forced" in w.last.extra["diagnosis"]:
            break
        t += DAY_MS
    assert POW in w.last.extra["diagnosis"]["credit_forced"]
    assert (w.shadows[POW].credited_stability or 0) >= 2 * 2
    assert w.states[POW].stability == 2  # shadow mode: no schedule effect


def test_credit_on_mode_changes_stability_and_forces_a_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_credit_on(monkeypatch)
    w = setup(config=DiagnosisSettings(credit="on"))
    seed(w, POW, stability=2, days_ago=8, theta=2.0)
    t = T
    for i in range(6):
        seed(w, CRIT, stability=20, days_ago=20, at=t, theta=2.0)
        w.grade(answer(w, f"crit.t3.{i}", t, correct=True))
        if "credit_forced" in w.last.extra["diagnosis"]:
            break
        t += DAY_MS
    assert (w.states[POW].stability or 0) >= 4
    assert due_day(w.states[POW], 0.9, w.fsrs, DAYS) <= DAYS.day_of(t) + timedelta(days=1)  # type: ignore[operator]
    assert all(c.mode == "on" for c in w.credits)


def test_explicit_review_moves_the_shadow_track_and_logs_both_predictions() -> None:
    w = setup()
    w.grade(answer(w, "crit.t3.0", T, correct=True))
    credited = w.shadows[POW].credited_stability
    w.grade(answer(w, "c.pow.t3.0", T + 3 * DAY_MS, correct=True))
    logged = w.last.extra["diagnosis"]["shadow"]
    assert logged["credited"] > logged["plain"]
    assert w.shadows[POW].credited_stability != credited


def test_credit_off_and_non_core_answers_give_nothing() -> None:
    w = setup(config=DiagnosisSettings(credit="off"))
    w.grade(answer(w, "crit.t3.0", T, correct=True))
    assert w.credits == []
    w = setup()
    w.grade(answer(w, "crit.t3.1", T, correct=True, purpose="reinforcement"))
    w.grade(replace(answer(w, "crit.t4.1", T + 60_000, correct=True), stretch=True))
    assert w.credits == []
