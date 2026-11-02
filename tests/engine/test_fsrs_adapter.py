"""ENG-1: the FSRS adapter (py-fsrs 6.3.2 behind one module)."""

import math
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fsrs import Card, Rating, Scheduler, State
from fsrs.scheduler import DEFAULT_PARAMETERS
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.engine.config import DAY_MS
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import (
    DEFAULT_PARAMS_ID,
    PARAMETER_BOUNDS,
    FsrsAdapter,
    Memory,
    ParameterError,
    clean_parameters,
    params_id_for,
)
from core.storage.clock import to_ms

FSRS = FsrsAdapter(fuzz=False)
START = datetime(2026, 9, 1, 12, tzinfo=UTC)


def test_retrievability_matches_the_spec_formula_with_fractional_days():
    w20 = DEFAULT_PARAMETERS[20]
    factor = 0.9 ** (-1 / w20) - 1
    memory = Memory(10.0, 5.0, 0)
    for days in (0.25, 1.5, 7.3, 10.0, 40.9):
        expected = (1 + factor * days / 10.0) ** (-w20)
        assert FSRS.retrievability(memory, round(days * DAY_MS)) == pytest.approx(expected)
    assert FSRS.retrievability(memory, 10 * DAY_MS) == pytest.approx(0.9)
    # Fractional days count: py-fsrs would truncate 1.9 days to 1.
    assert FSRS.retrievability(memory, round(1.9 * DAY_MS)) < FSRS.retrievability(memory, DAY_MS)


@pytest.mark.parametrize("ratings", [(3, 3, 3, 1, 3, 3), (1, 2, 3, 4), (4, 1, 1, 3), (2, 2, 2)])
def test_whole_day_reviews_match_py_fsrs_exactly(ratings):
    """With elapsed time in exact days the adapter and py-fsrs agree (same formulas)."""
    scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)
    card = Card()
    memory = None
    at = START
    for i, rating in enumerate(ratings):
        card, _ = scheduler.review_card(card, Rating(rating), at)
        memory = FSRS.review(memory, rating, to_ms(at))
        assert card.state == State.Review
        assert memory.stability == pytest.approx(card.stability, rel=1e-12)
        assert memory.difficulty == pytest.approx(card.difficulty, rel=1e-12)
        at += timedelta(days=3 + 2 * i)


def test_same_day_review_uses_short_term_stability():
    first = FSRS.review(None, 3, 0)
    again_today = FSRS.review(first, 3, 3_600_000)
    assert again_today.stability == pytest.approx(first.stability)  # clamped to >= 1x
    lapse_today = FSRS.review(first, 1, 3_600_000)
    assert lapse_today.stability < first.stability


def test_three_good_answers_replayed_give_about_two_days():
    memory = FSRS.replay([(3, 0), (3, 60_000), (3, 120_000)])
    assert memory is not None
    assert FSRS.interval_days(memory.stability, 0.90, None) == 2


def test_interval_respects_retention_and_maximum():
    assert FSRS.interval_days(10.0, 0.90, None) == 10
    assert FSRS.interval_days(10.0, 0.80, None) > 10
    assert FSRS.interval_days(10.0, 0.95, None) < 10
    assert FSRS.interval_days(0.01, 0.90, None) == 1
    assert FSRS.interval_days(5000.0, 0.80, None) == 365
    capped = FsrsAdapter(maximum_interval_days=30, fuzz=False)
    assert capped.interval_days(100.0, 0.90, None) == 30


def test_fuzz_is_deterministic_and_inside_py_fsrs_range():
    fuzzy = FsrsAdapter(fuzz=True)
    scheduler = Scheduler(maximum_interval=365)
    for days in (3, 8, 25, 60, 200):
        stability = fuzzy.elapsed_for(0.9, float(days))
        assert round(fuzzy.raw_interval(stability, 0.9)) == days
        seen = {
            scheduler._get_fuzzed_interval(interval=timedelta(days=days)).days for _ in range(400)
        }
        low, high = fuzzy.fuzz_range(days)
        ours = {fuzzy.interval_days(float(days), 0.9, f"k{i}") for i in range(400)}
        assert ours <= set(range(min(seen), max(seen) + 1))
        assert low >= min(seen)
        assert high <= max(seen)
        assert len(ours) > 1
        assert fuzzy.interval_days(float(days), 0.9, "k1") == fuzzy.interval_days(
            float(days), 0.9, "k1"
        )
    assert fuzzy.interval_days(2.0, 0.9, "short") == 2  # no fuzz under 2.5 days


def test_params_id():
    assert params_id_for(DEFAULT_PARAMETERS) == DEFAULT_PARAMS_ID
    other = list(DEFAULT_PARAMETERS)
    other[0] = 0.3
    assert params_id_for(other).startswith("fit-")
    assert FsrsAdapter(other).params_id == params_id_for(other)


def test_bad_inputs():
    with pytest.raises(ValueError, match="rating"):
        FSRS.review(None, 5, 0)
    with pytest.raises(ValueError, match="retention"):
        FSRS.raw_interval(10.0, 1.0)


stabilities = st.floats(min_value=0.05, max_value=3000, allow_nan=False)
elapsed = st.floats(min_value=0, max_value=2000, allow_nan=False)


@settings(max_examples=200, deadline=None)
@given(stabilities, elapsed, elapsed)
def test_recall_falls_monotonically_with_time(stability, t1, t2):
    early, late = sorted((t1, t2))
    r_early = FSRS.retrievability_after(early, stability)
    r_late = FSRS.retrievability_after(late, stability)
    assert 0.0 < r_late <= r_early <= 1.0


@settings(max_examples=200, deadline=None)
@given(stabilities, st.floats(0.80, 0.95), st.floats(0.80, 0.95))
def test_due_date_moves_later_as_retention_falls(stability, r1, r2):
    high, low = max(r1, r2), min(r1, r2)
    assert FSRS.raw_interval(stability, low) >= FSRS.raw_interval(stability, high)
    assert FSRS.interval_days(stability, low, None) >= FSRS.interval_days(stability, high, None)


@settings(max_examples=200, deadline=None)
@given(stabilities, st.floats(0.5, 0.99))
def test_elapsed_for_inverts_recall(stability, recall):
    t = FSRS.elapsed_for(recall, stability)
    assert FSRS.retrievability_after(t, stability) == pytest.approx(recall, rel=1e-9)


@settings(max_examples=150, deadline=None)
@given(
    stabilities,
    st.floats(1.0, 10.0),
    st.floats(1.0, 400.0),
    st.sampled_from([2, 3, 4]),
)
def test_success_never_lowers_stability_and_a_lapse_does(stability, difficulty, days, rating):
    memory = Memory(stability, difficulty, 0)
    at = round(days * DAY_MS)
    assert FSRS.review(memory, rating, at).stability >= stability * (1 - 1e-12)
    assert FSRS.review(memory, 1, at).stability <= stability
    assert math.isfinite(FSRS.review(memory, 1, at).difficulty)


@settings(max_examples=150, deadline=None)
@given(
    st.one_of(st.none(), st.tuples(stabilities, st.floats(1.0, 10.0))),
    st.sampled_from([1, 2, 3, 4]),
    st.integers(0, 400),
)
def test_step_is_step_fractional_on_whole_days(state, rating, days):
    """The student model's helper is the flashcard step itself for whole days."""
    expected = FSRS.step_fractional(state, rating, days, same_day=days <= 0)
    assert FSRS.step(state, rating, days) == expected


def test_step_fractional_same_day_flag_and_fractional_recall():
    """same_day picks the short-term formula whatever the elapsed time; otherwise the
    long-term update sees recall after the fractional elapsed days."""
    state = (10.0, 5.0)
    short = FSRS.step(state, 3, 0)
    assert FSRS.step_fractional(state, 3, 2.5, same_day=True) == short
    scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)
    for rating in (1, 3):
        long_term = scheduler._next_stability(
            difficulty=5.0,
            stability=10.0,
            retrievability=FSRS.retrievability_after(0.4, 10.0),
            rating=Rating(rating),
        )
        stability, _ = FSRS.step_fractional(state, rating, 0.4, same_day=False)
        assert stability == pytest.approx(long_term, rel=1e-12)
    assert FSRS.step_fractional(None, 3, 7.0, same_day=False) == FSRS.step(None, 3, 0)
    with pytest.raises(ValueError, match="rating"):
        FSRS.step_fractional(state, 0, 1.0, same_day=False)


def test_next_study_day_review_uses_long_term_stability_even_under_24_hours():
    """Learned at 23:00, reviewed next study day at 21:00 (22 h later): not same-day. The
    adapter has no 24-hour fallback any more (C4): it counts study days itself."""
    from core.engine.lifecycle import review_on
    from tests.engine.helpers import DAYS

    fsrs = FsrsAdapter(fuzz=False, days=DAYS)
    learned_at = to_ms(datetime(2026, 9, 2, 3, tzinfo=UTC))  # 23:00 New York, Sep 1
    memory = fsrs.replay([(1, learned_at), (3, learned_at + 1), (3, learned_at + 2)])
    assert memory is not None
    next_day = learned_at + 22 * 3_600_000
    assert DAYS.day_of(next_day) != DAYS.day_of(learned_at)
    long_term = review_on(fsrs, memory, 3, next_day, DAYS)
    assert long_term.stability > 2 * memory.stability
    assert fsrs.review(memory, 3, next_day) == long_term
    same_study_day = review_on(fsrs, memory, 3, learned_at + 3_600_000, DAYS)
    assert same_study_day == fsrs.review(memory, 3, learned_at + 3_600_000)


# ---------------------------------------------------------------- C1: clean parameters

FLOAT32_08 = 0.800000011920929  # what fsrs-rs returns for a value clipped to 0.8


def test_C1_fit_result_with_w20_at_the_float32_bound_stores_0_8_and_adapter_builds(storage):
    from core.engine import Engine
    from core.engine.param_sets import params_key, stored_value

    with pytest.raises(ValueError, match="out of bounds"):
        Scheduler(parameters=(*DEFAULT_PARAMETERS[:20], FLOAT32_08))  # what py-fsrs does
    fitted = [*DEFAULT_PARAMETERS[:9], FLOAT32_08, *DEFAULT_PARAMETERS[10:19], FLOAT32_08]
    fitted.append(FLOAT32_08)
    assert clean_parameters(fitted)[20] == 0.8
    value = stored_value(fitted, at=0, source="fit")
    assert value["w"][9] == value["w"][19] == value["w"][20] == 0.8
    # Even the raw float32 vector, stored as the old code did, builds the adapter.
    storage.users.set_setting(params_key("skills"), {"w": fitted})
    adapter = Engine(storage).adapter()
    assert adapter.parameters[20] == 0.8
    assert adapter.params_id.startswith("fit-")


any_floats = st.floats(allow_nan=True, allow_infinity=True, width=64)


@settings(max_examples=300, deadline=None)
@given(st.lists(any_floats, min_size=21, max_size=21) | st.lists(any_floats, max_size=30))
def test_C1_arbitrary_21_float_vectors_never_make_the_adapter_raise(vector):
    from core.engine.param_sets import load_set

    found = load_set({"fsrs.params.skills": {"w": vector}}, "skills")
    adapter = FsrsAdapter(found.parameters, params_id=found.params_id)  # what adapter() builds
    assert len(adapter.parameters) == 21
    usable = len(vector) == 21 and all(math.isfinite(v) for v in vector)
    assert (found.notice is None) == usable
    if not usable:
        assert found.parameters == tuple(DEFAULT_PARAMETERS)
    for (low, high), w in zip(PARAMETER_BOUNDS, adapter.parameters, strict=True):
        assert low <= w <= high


@settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(st.lists(st.floats(-1e6, 1e6), min_size=21, max_size=21))
def test_C1_engine_adapter_never_raises_for_stored_vectors(storage, vector):
    from core.engine import Engine

    storage.users.set_setting("fsrs.params.skills", {"w": vector})
    engine = Engine(storage)
    assert len(engine.adapter().parameters) == 21
    assert engine.parameter_set("skills").notice is None


def test_C1_unusable_stored_parameters_fall_back_to_defaults_with_a_notice(storage):
    from core.engine import Engine

    storage.users.set_setting("fsrs.params.skills", {"w": [1, 2, 3]})
    engine = Engine(storage)
    assert engine.adapter().params_id == DEFAULT_PARAMS_ID
    notice = engine.parameter_set("skills").notice
    assert notice is not None
    assert "defaults" in notice
    with pytest.raises(ParameterError):
        clean_parameters([math.nan] * 21)


# ---------------------------------------------------------------- C4: one clock

NY_DAYS = StudyDays(ZoneInfo("America/New_York"), 4)


def test_C4_good_at_2300_then_good_at_0800_two_study_days_later_gives_10_964():
    from core.engine.lifecycle import review_on

    fsrs = FsrsAdapter(fuzz=False, days=NY_DAYS)
    ny = ZoneInfo("America/New_York")
    learned = to_ms(datetime(2026, 9, 1, 23, tzinfo=ny))
    first = fsrs.review(None, 3, learned)
    assert (first.stability, first.difficulty) == pytest.approx((2.3065, 2.1181), abs=1e-4)
    review_at = to_ms(datetime(2026, 9, 3, 8, tzinfo=ny))
    assert (review_at - learned) / DAY_MS == 1.375
    assert NY_DAYS.between(learned, review_at) == 2
    after = review_on(fsrs, first, 3, review_at, NY_DAYS)
    assert after.stability == pytest.approx(10.964, abs=5e-4)  # t = 2
    fractional = fsrs.step((first.stability, first.difficulty), 3, 1.375)  # type: ignore[arg-type]
    assert fractional[0] == pytest.approx(8.802, abs=5e-4)  # what the old clock gave
    # Fractional recall stays for display; both are logged by Engine.grade.
    assert fsrs.retrievability(first, review_at) > fsrs.recall_days(first, review_at)


@pytest.mark.parametrize(
    ("rating", "long_term", "same_day"),
    [
        (1, (1.39199, 8.34176), (3.05125, 8.34176)),
        (2, (23.2469, 6.66600), (10.0, 6.66600)),
        (3, (32.0267, 4.99023), (10.0, 4.99023)),
        (4, (51.2539, 3.31446), (15.5343, 3.31446)),
    ],
)
def test_C4_long_term_and_same_day_vectors(rating, long_term, same_day):
    fsrs = FsrsAdapter(fuzz=False, days=NY_DAYS)
    memory = Memory(10.0, 5.0, to_ms(datetime(2026, 9, 1, 16, tzinfo=UTC)))
    later = fsrs.review(memory, rating, memory.last_review_at + 10 * DAY_MS)
    assert (later.stability, later.difficulty) == pytest.approx(long_term, abs=1e-4)
    today = fsrs.review(memory, rating, memory.last_review_at + 3_600_000)
    assert (today.stability, today.difficulty) == pytest.approx(same_day, abs=1e-4)


def test_C4_first_review_curve_and_replay_vectors():
    fsrs = FsrsAdapter(fuzz=False)
    firsts = [fsrs.step(None, g, 0) for g in (1, 2, 3, 4)]
    expected = [(0.212, 6.4133), (1.2931, 5.11217), (2.3065, 2.11810), (8.2956, 1.0)]
    for got, want in zip(firsts, expected, strict=True):
        assert got == pytest.approx(want, abs=1e-4)
    state = None
    for k, (g, t) in enumerate([(1, 0), (3, 0), (3, 1), (3, 3), (3, 8), (3, 21)]):
        state = fsrs.step(state, g, t if k else 0)
    assert state == pytest.approx((53.62691, 6.357487), abs=1e-4)
    assert fsrs.retrievability_after(20, 10) == pytest.approx(0.845885, abs=1e-6)
    assert fsrs.factor == pytest.approx(0.980346, abs=1e-6)
    intervals = [fsrs.raw_interval(10, r) for r in (0.8, 0.95, 0.7)]
    assert intervals == pytest.approx([33.1596, 4.02559, 92.879], abs=1e-3)


# Instants around 04:00 New York, across both 2026 daylight-saving changes.
_EDGES = [
    to_ms(datetime(2026, m, d, h, mi, tzinfo=ZoneInfo("America/New_York")))
    for m, d in ((3, 7), (3, 8), (3, 9), (10, 31), (11, 1), (11, 2), (6, 1))
    for h, mi in ((3, 50), (4, 10), (23, 30), (1, 30))
]


@settings(max_examples=150, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from([1, 2, 3, 4]),
            st.sampled_from(_EDGES) | st.integers(0, 3 * DAY_MS),
        ),
        min_size=1,
        max_size=10,
    )
)
def test_C4_replay_equals_sequential_review_on_across_0400_and_dst(pairs):
    from core.engine.lifecycle import review_on

    fsrs = FsrsAdapter(fuzz=False, days=NY_DAYS)
    times = sorted(t if t > 10 * DAY_MS else _EDGES[0] + t for _, t in pairs)
    reviews = [(r, t) for (r, _), t in zip(pairs, times, strict=True)]
    memory = None
    for rating, at in reviews:
        memory = review_on(fsrs, memory, rating, at, NY_DAYS)
    assert fsrs.replay(reviews, NY_DAYS) == memory
    assert FsrsAdapter(fuzz=False).replay(reviews, NY_DAYS) == memory  # days given wins
