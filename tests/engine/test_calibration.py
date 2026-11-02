"""ENG-11 calibration and ENG-12 fitting."""

import random
from datetime import UTC, date

import pytest

from core.engine.calibration import (
    FitUnavailable,
    calibrate,
    calibration_by_course,
    fit_offer,
    fit_parameters,
    fitter_installed,
    qualifying_reviews,
    review_histories,
    review_pairs,
    stored_parameters,
)
from core.engine.config import DAY_MS, RULES_VERSION
from core.engine.days import StudyDays
from core.model import ReviewEvent

DAYS = StudyDays(UTC, 4)


def day_of(at: int) -> date:
    return DAYS.day_of(at)


def event(
    at: int, rating: int, *, last: int | None, stability: float | None = 5.0, **kw: object
) -> ReviewEvent:
    base: dict[str, object] = {
        "attempt_id": kw.get("id"),
        "at": at,
        "target_kind": "skill",
        "target_id": "s.a",
        "rating": rating,
        "rules_version": RULES_VERSION,
        "predicted_recall": 0.9,
        "state_before": {"stability": stability, "last_review_at": last},
    }
    base.update(kw)
    return ReviewEvent(**base)  # type: ignore[arg-type]


def test_bins_and_notice_rule():
    rng = random.Random(1)  # noqa: S311
    calibrated = [(p, rng.random() < p) for p in (rng.uniform(0.6, 1.0) for _ in range(4000))]
    report = calibrate(calibrated)
    assert report.total == 4000
    assert not report.notice
    assert abs(report.mean_error) < 0.02
    # Predictions 0.10+ too high in a bin of 30+ raise a notice.
    off = [(0.95, rng.random() < 0.80) for _ in range(60)]
    assert calibrate(off).notice
    small = [(0.95, False)] * 29
    assert not calibrate(small).notice  # under 30 reviews
    edge = calibrate([(1.0, True), (0.0, False)])
    assert [b.low for b in edge.bins] == [0.0, 0.9]


def test_review_pairs_skip_missing_predictions_and_voided():
    events = [
        event(0, 3, last=None),
        event(0, 1, last=None, predicted_recall=None),
        event(0, 1, last=None, voided_by=4),
    ]
    assert review_pairs(events) == [(0.9, True)]
    by_course = calibration_by_course(events, lambda _: "calc1")
    assert by_course["calc1"].total == 1


def test_qualifying_reviews_need_current_rules_and_a_day_gap():
    t = 100 * DAY_MS
    events = [
        event(t, 3, last=t - 3 * DAY_MS),
        event(t, 3, last=t - 3 * DAY_MS, rules_version="old"),
        event(t, 3, last=t - 3 * DAY_MS, voided_by=1),
        event(t, 3, last=t - 3_600_000),  # same day
        event(t, 3, last=None),  # first review
        event(t, 3, last=t - 3 * DAY_MS, target_kind="flashcard"),
    ]
    assert len(qualifying_reviews(events, day_of=day_of)) == 1


def test_fit_offer_counts_long_term_items_from_300():
    t = 100 * DAY_MS
    many: list[ReviewEvent] = []
    for i in range(300):
        many.append(event(t, 3, last=None, stability=None, target_id=f"s.{i}"))
        many.append(event(t + 2 * DAY_MS, 3, last=t, target_id=f"s.{i}"))
    offer = fit_offer(many, day_of=day_of)
    assert offer.offer
    assert offer.qualifying == 300
    assert offer.needed == 300
    assert not fit_offer(many[:-1], day_of=day_of).offer
    assert (
        fit_offer(many, day_of=day_of, domain="coding", domain_of=lambda _: "math").qualifying == 0
    )


def test_review_histories_start_at_fresh_cards():
    d = DAY_MS
    events = [
        # A provisional seed: no fresh start, left out until a fresh card appears.
        event(1 * d, 3, last=0, stability=10.0, target_id="s.placed"),
        # A learning-phase replay (three same-day events), then reviews.
        event(10 * d, 1, last=None, stability=None),
        event(10 * d + 1, 3, last=None, stability=None),
        event(10 * d + 2, 3, last=None, stability=None),
        event(12 * d, 3, last=10 * d + 2),
        event(20 * d, 1, last=12 * d),
    ]
    assert review_histories(events, day_of=day_of) == [[(1, 0), (3, 0), (3, 0), (3, 2), (1, 8)]]


def test_stored_parameters():
    from fsrs.scheduler import DEFAULT_PARAMETERS

    assert stored_parameters({}) is None
    assert stored_parameters({"fsrs.params.math": {"w": [1, 2]}}) is None  # unusable (C1)
    w = [*DEFAULT_PARAMETERS[:20], 0.800000011920929]
    assert stored_parameters({"fsrs.params.math": {"w": w}}) == (*DEFAULT_PARAMETERS[:20], 0.8)


def test_the_fitter_ships_with_the_app():
    assert fitter_installed()
    assert issubclass(FitUnavailable, RuntimeError)


def test_fit_with_fsrs_rs_python():
    from core.engine.fsrs_adapter import FsrsAdapter

    truth = FsrsAdapter(fuzz=False)
    rng = random.Random(7)  # noqa: S311
    events: list[ReviewEvent] = []
    for k in range(120):
        memory = None
        at = (k % 30) * DAY_MS
        last = None
        for _ in range(8):
            if memory is None:
                rating = 3
            else:
                rating = 3 if rng.random() < truth.retrievability(memory, at) else 1
            events.append(
                event(
                    at,
                    rating,
                    last=last,
                    stability=None if memory is None else memory.stability,
                    target_id=f"s.{k}",
                )
            )
            memory = truth.review(memory, rating, at)
            last = at
            at += max(1, round(truth.raw_interval(memory.stability, 0.9))) * DAY_MS
    result = fit_parameters(events, day_of=day_of)
    assert len(result.parameters) == 21
    assert result.items > 500
    FsrsAdapter(result.parameters)  # plugs straight into py-fsrs


# ---------------------------------------------------------------- I8


def test_I8_a_calibrated_learner_with_ten_30_review_bins_alarms_in_at_most_5_percent_of_runs():
    rng = random.Random(8)  # noqa: S311
    runs = 2000
    alarms = old_rule = 0
    for _ in range(runs):
        pairs = []
        for i in range(10):
            for _ in range(30):
                p = rng.uniform(i / 10, (i + 1) / 10)
                pairs.append((p, rng.random() < p))
        report = calibrate(pairs)
        assert [b.n for b in report.bins] == [30] * 10
        alarms += report.alarm
        old_rule += any(abs(b.error) > 0.10 for b in report.bins)
    assert alarms / runs <= 0.05
    assert old_rule / runs > 0.5  # "30 reviews off by 0.10" cries wolf most of the time


def test_I8_wilson_intervals_and_greyed_bins():
    from core.engine.calibration import wilson

    got = [tuple(round(x, 3) for x in wilson(round(0.9 * n), n)) for n in (30, 100, 400, 1000)]
    assert got == [(0.744, 0.965), (0.826, 0.945), (0.867, 0.926), (0.88, 0.917)]
    report = calibrate([(0.95, False)] * 29 + [(0.55, True)] * 40)
    large, small = report.bins  # bins in order: 0.5-0.6, then 0.9-1.0
    assert small.greyed
    assert not small.alarm
    assert not large.greyed
    assert large.ci_low <= large.observed <= large.ci_high


def test_I8_true_retention_first_interday_review_per_day_young_and_mature():
    from core.engine.calibration import true_retention
    from core.engine.fsrs_adapter import FsrsAdapter

    d = DAY_MS
    events = [
        event(0, 3, last=None, stability=None, id=1),
        event(2 * d, 3, last=0, id=2),  # young pass
        event(2 * d + 60_000, 1, last=2 * d, id=3),  # same day again: not counted
        event(5 * d, 1, last=2 * d + 60_000, id=4),  # young fail
        event(30 * d, 3, last=5 * d, id=5),  # mature (25 days) pass
        event(30 * d, 3, last=5 * d, id=6, voided_by=1),
    ]
    table = true_retention(events, day_of=day_of, adapter_of=lambda _: FsrsAdapter())
    assert (table.young.n, table.young.passed) == (2, 1)
    assert (table.mature.n, table.mature.passed) == (1, 1)
    assert table.total.n == 3
    assert table.total.ci_low < table.total.observed < table.total.ci_high
    assert table.young.expected == pytest.approx(0.9)


def test_I8_stats_screen_data_with_held_out_metrics_above_300_items(storage, clock):
    from core.engine import Engine
    from core.engine.fitting import health_thresholds
    from tests.engine.fitlog import learner_log, store_log
    from tests.engine.helpers import DAYS as NY_DAYS

    start = clock.now_ms() - 400 * DAY_MS
    store_log(storage, learner_log(None, cards=90, reviews=4, seed=4, days=NY_DAYS, start=start))
    engine = Engine(storage)
    stats = engine.calibration_stats(with_held_out=True)
    assert stats.items == 360
    assert stats.series["core"].total == 360
    assert stats.series["strict"].total == 360
    assert stats.true_retention.total.n == 360
    split = stats.held_out
    assert split is not None
    assert split.thresholds == health_thresholds(split.retention, 360)
    assert split.baseline_rmse == pytest.approx(split.thresholds[1] / 1.53)
    assert split.healthy
    assert engine.calibration_stats().held_out is None  # only when asked (it fits 5 times)
