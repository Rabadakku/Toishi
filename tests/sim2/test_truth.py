"""Truth models: answers, side-effect-free chances, profiles, matched errors and calibration."""

from datetime import date, timedelta

import pytest

from core.learner.types import ProblemSpec
from tools.sim2.common import DAY_MS, session_ms
from tools.sim2.course import calc1, toy
from tools.sim2.truth import (
    PPE_B,
    PPE_C,
    PPE_M,
    PPE_X,
    PROFILES,
    TRUTH_MODELS,
    AdditiveTruth,
    ConjunctiveTruth,
    FsrsMemory,
    PpeTruth,
    RohrerTaylorMemory,
    TimeTruth,
    make_truth,
    rohrer_taylor_exp1,
)

START = date(2027, 1, 11)


@pytest.mark.parametrize("model", TRUTH_MODELS)
@pytest.mark.parametrize("profile", PROFILES)
def test_truths_answer_and_chances_have_no_side_effects(model: str, profile: str) -> None:
    sim = toy()
    truth = make_truth(model, profile, 1, sim, START)
    spec = sim.true_pools["toy.b2"][4][0]
    at = session_ms(START)
    p = truth.p_correct(spec, at)
    assert 0.0 < p < 1.0
    assert truth.p_correct(spec, at) == p
    assert 0.0 < truth.p_fast(spec) < 1.0
    lines = dict(spec.wrong_components)
    for i in range(30):
        answer = truth.answer(spec, at + i * 120_000, START)
        assert answer.minutes > 0.0
        if answer.correct:
            assert answer.matched_wrong is None
        else:
            assert answer.matched_wrong is None or answer.matched_wrong in lines
    twin = make_truth(model, profile, 1, sim, START)
    assert twin.p_correct(spec, at) == p  # the same student for every policy


def test_matched_wrong_names_the_failed_component() -> None:
    spec = ProblemSpec("p", "p", None, "k.a", ("k.a", "k.b"), 2, 2, 3.5, ((0, "k.a"), (1, "k.b")))
    rng_seeded = make_truth("a-model", "typical", 1, toy(), START)
    assert isinstance(rng_seeded, ConjunctiveTruth)
    truth = ConjunctiveTruth(
        "t",
        "x",
        beta={"k.a": 30.0, "k.b": -30.0},
        background=frozenset(),
        slip=0.0,
        delta4=0.3,
        memory=FsrsMemory(1.0),
        time=TimeTruth(0.0, 0.3, 0.3, {}, frozenset()),
        rng=rng_seeded.rng,
    )
    answers = [truth.answer(spec, session_ms(START) + i, START) for i in range(5)]
    assert all(not a.correct and a.matched_wrong == 1 for a in answers)


def test_strong_students_start_above_the_targets() -> None:
    sim = calc1()
    at = session_ms(START)
    skills = sim.skill_ids[::12]
    for model in TRUTH_MODELS:
        truth = make_truth(model, "strong", 1, sim, START)
        pool = [p for s in skills for p in sim.true_pools[s][4]]
        acc = sum(truth.p_correct(p, at) for p in pool) / len(pool)
        fast = sum(truth.p_fast(p) for p in pool) / len(pool)
        if model == "e-careless":
            assert acc < 0.89  # slip 0.12 caps it
        else:
            assert acc > 0.92, model
        assert fast > 0.95, model


def test_weak_students_start_well_below_the_target() -> None:
    sim = calc1()
    at = session_ms(START)
    for model in TRUTH_MODELS:
        truth = make_truth(model, "weak", 1, sim, START)
        pool = [p for s in sim.skill_ids[::12] for p in sim.true_pools[s][2]]
        assert sum(truth.p_correct(p, at) for p in pool) / len(pool) < 0.6, model


@pytest.mark.parametrize("model", ["a-model", "b-additive", "c-ppe", "d-rohrer-taylor"])
def test_practice_helps_and_time_without_it_hurts(model: str) -> None:
    sim = toy()
    truth = make_truth(model, "typical", 2, sim, START)
    probe = sim.true_pools["toy.a1"][1][0]
    practice = sim.true_pools["toy.a1"][1][1:]
    before = truth.p_correct(probe, session_ms(START))
    day = START
    for d in range(12):
        day = START + timedelta(days=d)
        for j, spec in enumerate(practice[:2]):
            truth.answer(spec, session_ms(day) + j * 300_000, day)
    after = truth.p_correct(probe, session_ms(day) + DAY_MS)
    later = truth.p_correct(probe, session_ms(day) + 60 * DAY_MS)
    assert after > before
    assert later < after


def test_slow_and_careless_variants() -> None:
    sim = toy()
    slow = make_truth("e-slow", "typical", 3, sim, START)
    base = make_truth("a-model", "typical", 3, sim, START)
    careless = make_truth("e-careless", "typical", 3, sim, START)
    assert isinstance(slow, ConjunctiveTruth)
    assert isinstance(base, ConjunctiveTruth)
    assert isinstance(careless, ConjunctiveTruth)
    assert slow.gamma == base.gamma / 2
    assert slow.rho == base.rho / 2
    assert slow.time.alpha == base.time.alpha / 2
    assert careless.slip == 0.12
    assert slow.beta == base.beta == careless.beta  # same student otherwise


def test_ppe_uses_the_notes_values() -> None:
    truth = make_truth("c-ppe", "typical", 1, toy(), START)
    assert isinstance(truth, PpeTruth)
    assert (truth.c, truth.b, truth.m, truth.x) == (PPE_C, PPE_B, PPE_M, PPE_X)
    assert (PPE_C, PPE_B, PPE_M, PPE_X) == (0.3491901, 0.2045801, 1e-05, 0.9734477)


def test_additive_counts_windows() -> None:
    truth = make_truth("b-additive", "typical", 1, toy(), START)
    assert isinstance(truth, AdditiveTruth)
    t0 = session_ms(START)
    base = truth.term("toy.a1", t0)
    truth.attempts["toy.a1"] = [t0, t0 + 1000]
    truth.successes["toy.a1"] = [t0, t0 + 1000]
    fresh = truth.term("toy.a1", t0 + 2000)
    month = truth.term("toy.a1", t0 + 40 * DAY_MS)
    assert fresh > month > base  # recent windows fade, the long-run term stays


def test_rohrer_taylor_truth_reproduces_exp1() -> None:
    result = rohrer_taylor_exp1(RohrerTaylorMemory, students=1500)
    assert result.massed_ratio == pytest.approx(0.43, abs=0.03)
    assert result.spaced_over_massed_4w == pytest.approx(2.0, abs=0.15)


def test_fsrs_defaults_do_not_reproduce_exp1() -> None:
    """The critique's finding 8: FSRS-6 defaults forget too little and space too weakly."""
    result = rohrer_taylor_exp1(lambda: FsrsMemory(1.0), students=500)
    assert result.massed_ratio > 0.75
    assert result.spaced_over_massed_4w < 1.4


def test_time_speeds_up_with_practice() -> None:
    spec = toy().true_pools["toy.c1"][3][0]
    time = TimeTruth(0.7, 0.45, 0.3, {}, frozenset({"alg.x", "alg.y"}))
    slow, p_slow = time.log_median(spec), time.p_fast(spec)
    for _ in range(30):
        time.practiced(spec)
    assert time.log_median(spec) < slow
    assert time.p_fast(spec) > p_slow
    assert all(c not in time.n for c in ("alg.x", "alg.y"))


def test_rohrer_taylor_memory_gains_only_from_spaced_reviews() -> None:
    mem = RohrerTaylorMemory()
    day = START
    mem.event("k", session_ms(day), day, recalled=True)
    first = mem.cards["k"].stability
    mem.event("k", session_ms(day) + 600_000, day, recalled=True)
    assert mem.cards["k"].stability == first  # same day: nothing
    later = day + timedelta(days=7)
    mem.event("k", session_ms(later), later, recalled=True)
    assert mem.cards["k"].stability > first
    mem.event("k", session_ms(later + timedelta(days=30)), later + timedelta(days=30), False)
    assert mem.cards["k"].stability == first  # a lapse re-encodes
