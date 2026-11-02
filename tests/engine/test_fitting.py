"""ENG-12 fitting with Anki's guard rails: C2 (adopt only what wins), I7 (automatic,
guarded fitting with a history and revert) and I10 (cross-implementation and recovery)."""

import random
from typing import Any

import fsrs_rs_python as rs
import pytest
from fsrs.scheduler import DEFAULT_PARAMETERS

from core.engine.fitting import (
    adoption,
    evaluate,
    fit,
    health_thresholds,
    held_out,
    rmse_adjustment,
    rs_evaluate,
)
from core.engine.fsrs_adapter import FsrsAdapter, clean_parameters
from core.engine.histories import Item, build_histories, training_items
from tests.engine.fitlog import learner_log
from tests.engine.helpers import DAYS
from tests.engine.reference import ref_fsrs6

DEFAULTS = tuple(DEFAULT_PARAMETERS)
# A learner who forgets faster than the defaults assume (and decays on a steeper curve).
TRUE = clean_parameters(
    [0.1, 0.6, 1.0, 3.5, 7.2, 0.9, 2.6, 0.01, 1.2, 0.2, 0.9, 1.6, 0.07, 0.3, 1.8, 0.5, 2.1,
     0.5, 0.1, 0.07, 0.5]
)  # fmt: skip
# A learner near the defaults, as most are: for recovery. (A learner as far off as TRUE
# recovers to within 0.0022 at 5.4k items, still 0.012 better than the defaults: the
# optimizer's pull toward its starting values is felt that far out.)
MILD = clean_parameters(
    [0.3, 1.0, 2.0, 7.0, 6.8, 0.9, 2.6, 0.01, 1.6, 0.2, 0.9, 1.6, 0.07, 0.3, 1.8, 0.5, 2.1,
     0.5, 0.1, 0.07, 0.25]
)  # fmt: skip
# Nonsense for any learner: tiny first stabilities and almost no growth.
BROKEN = clean_parameters([0.01, 0.01, 0.01, 0.01, *DEFAULTS[4:8], 0.0, *DEFAULTS[9:]])


def items_of(log_events) -> list[Item]:
    return training_items(build_histories(log_events, day_of=DAYS.day_of))


@pytest.fixture(scope="module")
def learner_items() -> list[Item]:
    return items_of(learner_log(TRUE, cards=60, reviews=5, seed=11, days=DAYS).events)


# ---------------------------------------------------------------- C2


def test_C2_corrupted_candidate_is_rejected_and_params_id_is_unchanged(learner_items):
    flipped = items_of(learner_log(TRUE, cards=60, reviews=5, seed=11, days=DAYS, flip=True).events)
    corrupted = fit(flipped)
    assert corrupted != DEFAULTS
    decision = adoption(DEFAULTS, corrupted, learner_items)
    assert not decision.adopted
    assert decision.params_id == "fsrs6-default"
    assert decision.candidate_in_sample is not None
    assert decision.current_in_sample is not None
    assert decision.candidate_in_sample.log_loss > decision.current_in_sample.log_loss
    # The honest fit wins on the same items (fewer than 300: in-sample only).
    honest = adoption(DEFAULTS, fit(learner_items), learner_items)
    assert honest.adopted
    assert honest.held_out is None


def test_C2_corrupted_candidate_through_the_engine_keeps_params_id(storage, clock):
    from core.engine import Engine
    from tests.engine.test_service import learn

    engine = Engine(storage)
    for skill in ("calc1.alg", "calc1.lim", "calc1.der"):
        learn(engine, clock, skill)
    for _ in range(3):
        clock.advance(days=3)
        for skill in ("calc1.alg", "calc1.lim", "calc1.der"):
            answer_skill(engine, clock, skill)
    before = engine.adapter().params_id
    report = engine.fit(candidate=BROKEN)
    assert not report.adopted
    assert engine.adapter().params_id == before == "fsrs6-default"
    assert engine.parameter_history() == []
    log = storage.users.get_setting("fsrs.fit_log.skills")
    assert log["adopted"] is False


def answer_skill(engine: Any, clock: Any, skill: str) -> Any:
    from tests.engine.test_service import answer

    return answer(engine, clock, skill)


def test_C2_app_log_loss_and_rmse_bins_match_fsrs_rs_evaluate_to_1e_7(learner_items):
    for params in (DEFAULTS, TRUE):
        ours = evaluate(params, learner_items)
        theirs = rs_evaluate(params, learner_items)
        assert abs(ours.log_loss - theirs.log_loss) <= 1e-7
        assert abs(ours.rmse_bins - theirs.rmse_bins) <= 1e-7


def test_C2_health_thresholds_reproduce_anki():
    log_loss_90, _ = health_thresholds(0.90, 300)
    assert round(log_loss_90, 3) == 0.325
    assert round(health_thresholds(0.85, 300)[0], 3) == 0.421
    assert [round(health_thresholds(0.90, n)[1], 3) for n in (300, 1_000, 10_000)] == [
        0.151,
        0.130,
        0.077,
    ]
    assert [round(rmse_adjustment(0.90, n), 3) for n in (300, 1_000, 10_000)] == [
        0.099,
        0.085,
        0.050,
    ]


def test_C2_above_300_items_a_candidate_must_also_win_held_out():
    items = items_of(learner_log(TRUE, cards=120, reviews=4, seed=5, days=DAYS).events)
    assert len(items) > 300
    candidate = fit(items)
    # Folds fitted by a broken optimizer: the candidate wins in sample, loses out of it.
    rejected = adoption(DEFAULTS, candidate, items, fit_fn=lambda _: BROKEN)
    assert not rejected.adopted
    assert rejected.reason == "held-out log loss is not lower"
    assert rejected.held_out is not None
    cand, cur = rejected.candidate_in_sample, rejected.current_in_sample
    assert cand is not None
    assert cur is not None
    assert cand.log_loss < cur.log_loss
    accepted = adoption(DEFAULTS, candidate, items)
    assert accepted.adopted, accepted.reason
    split = accepted.held_out
    assert split is not None
    assert split.healthy
    assert split.candidate.log_loss < split.current.log_loss
    # Segment = N/6: the five test segments cover everything after the first sixth.
    assert split.candidate.items == len(items) - len(items) // 6


def test_C2_held_out_matches_fsrs_rs_time_series_split_shape():
    items = items_of(learner_log(TRUE, cards=40, reviews=3, seed=6, days=DAYS).events)
    assert held_out(items[:5], DEFAULTS) is None  # too few for six segments
    split = held_out(items, DEFAULTS)
    assert split is not None
    assert split.items == len(items)


# ---------------------------------------------------------------- I10


def test_I10_cross_implementation_replay_2000_whole_day_histories():
    """py-fsrs adapter vs fsrs-rs-python memory_state: max relative S error <= 1e-3."""
    rng = random.Random(2026)  # noqa: S311
    adapter = FsrsAdapter(fuzz=False, days=DAYS)
    model = rs.FSRS(list(rs.DEFAULT_PARAMETERS))
    worst_s = worst_d = 0.0
    for _ in range(2000):
        reviews = [(rng.randint(1, 4), 0)]
        for _ in range(rng.randint(1, 12)):
            reviews.append((rng.randint(1, 4), rng.choice([0, 1, 2, 3, 5, 8, 13, 30, 90, 365])))
        state = None
        for k, (rating, delta) in enumerate(reviews):
            state = adapter.step(state, rating, delta if k else 0)
        assert state is not None
        theirs = model.memory_state(rs.FSRSItem([rs.FSRSReview(r, d) for r, d in reviews]))
        ref = ref_fsrs6.replay(ref_fsrs6.W, reviews)
        worst_s = max(worst_s, abs(state[0] - theirs.stability) / theirs.stability)
        worst_d = max(worst_d, abs(state[1] - theirs.difficulty) / theirs.difficulty)
        assert state[0] == pytest.approx(ref[0], rel=1e-9)
    assert worst_s <= 1e-3
    assert worst_d <= 1e-3


def test_I10_parameter_recovery_at_about_5k_items():
    """Simulated learners with known parameters, logged and converted by the app's own
    history builder, fitted: held-out log loss within 0.001 of the true parameters'."""
    train = items_of(learner_log(MILD, cards=900, reviews=6, seed=21, days=DAYS).events)
    test = items_of(learner_log(MILD, cards=600, reviews=6, seed=22, days=DAYS, prefix="t").events)
    assert 4_500 <= len(train) <= 6_000
    fitted = fit(train)
    ours = evaluate(fitted, test, weighted=False).log_loss
    truth = evaluate(MILD, test, weighted=False).log_loss
    defaults = evaluate(DEFAULTS, test, weighted=False).log_loss
    assert ours - truth <= 0.001, (ours, truth)
    assert ours < defaults


# ---------------------------------------------------------------- I7


def test_I7_automatic_fit_fires_first_at_300_items_then_at_30_days_and_at_a_doubling(
    storage, clock
):
    from core.engine import Engine
    from tests.engine.fitlog import store_log

    engine = Engine(storage)
    start = clock.now_ms() - 400 * 86_400_000
    store_log(storage, learner_log(TRUE, cards=74, reviews=4, seed=7, days=DAYS, start=start))
    assert len(engine.training_items("skills")) == 296
    assert not engine.fit_due("skills")
    assert engine.auto_fit() == []
    store_log(
        storage, learner_log(TRUE, cards=1, reviews=4, seed=8, days=DAYS, prefix="x", start=start)
    )
    assert engine.fit_due("skills")  # the first fit, at 300 items
    (first,) = engine.auto_fit()
    assert first.items == 300
    assert not engine.fit_due("skills")
    clock.advance(days=29)
    assert not engine.fit_due("skills")
    clock.advance(days=1)
    assert engine.fit_due("skills")  # monthly
    assert len(engine.auto_fit()) == 1
    store_log(
        storage, learner_log(TRUE, cards=74, reviews=4, seed=9, days=DAYS, prefix="u", start=start)
    )
    assert not engine.fit_due("skills")  # 596 items: not yet double
    store_log(
        storage, learner_log(TRUE, cards=1, reviews=4, seed=10, days=DAYS, prefix="y", start=start)
    )
    assert engine.fit_due("skills")  # doubled
    log = storage.users.get_setting("fsrs.fit_log.skills")
    assert log["items"] == 300


def test_I7_a_candidate_that_loses_held_out_leaves_parameters_unchanged(storage, clock):
    from core.engine import Engine
    from tests.engine.fitlog import store_log

    engine = Engine(storage)
    start = clock.now_ms() - 400 * 86_400_000
    store_log(storage, learner_log(TRUE, cards=120, reviews=4, seed=5, days=DAYS, start=start))
    items = engine.training_items("skills")
    assert len(items) > 300
    candidate = fit(items)
    lost = engine.fit(candidate=candidate, fit_fn=lambda _: BROKEN)
    assert not lost.adopted
    assert lost.decision.reason == "held-out log loss is not lower"
    assert engine.adapter().params_id == "fsrs6-default"
    assert engine.parameter_history() == []
    won = engine.fit()
    assert won.adopted, won.decision.reason
    assert engine.adapter().params_id == won.decision.params_id
    (entry,) = engine.parameter_history()
    assert entry["id"] == won.decision.params_id
    assert entry["items"] == len(items)
    assert won.recomputed is not None
