"""Property tests of the student model (design 3.2-3.4, 3.10)."""

import random
from collections import defaultdict
from dataclasses import replace
from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from core.engine.config import AGAIN, DAY_MS, GOOD
from core.engine.fsrs_adapter import FsrsAdapter
from core.learner.model import (
    MATCH_HORIZON_DAYS,
    StudentModel,
    is_success,
    mix_memory,
    order_key,
)
from core.learner.types import SharedParams, StudentState
from tests.learner.helpers import (
    BACKGROUND,
    CATALOG,
    COURSE,
    logs,
    observation,
    problem,
    problems,
    shared_params,
    with_ties,
)

MODEL = StudentModel(CATALOG)
FSRS = FsrsAdapter(fuzz=False)
SETTINGS = settings(max_examples=100, deadline=None)


@SETTINGS
@given(params=shared_params(), log=logs())
def test_every_probability_is_in_0_1_and_blame_at_most_1(params, log):
    state = MODEL.new_state(params)
    for obs in log:
        before = MODEL.predict(state, obs.problem, obs.at_ms, study_day=obs.study_day)
        record = MODEL.update(state, obs)
        assert record.prediction == before
        prediction = record.prediction
        assert 0.0 <= prediction.p <= 1.0
        assert 0.0 <= prediction.p_raw <= 1.0
        for pairs in (prediction.q, prediction.e, prediction.r, record.memory_share):
            assert all(0.0 <= v <= 1.0 for _, v in pairs)
        for _, b in record.blame:
            assert 0.0 <= b <= 1.0
        if is_success(obs):
            assert all(b == 0.0 for _, b in record.blame)


@SETTINGS
@given(params=shared_params(), log=logs(max_size=12), spec=problems(), gap=st.integers(0, 3))
def test_a_success_never_lowers_mu_or_execution(params, log, spec, gap):
    state = MODEL.new_state(params)
    for obs in log:
        MODEL.update(state, obs)
    at_ms = log[-1].at_ms + gap * DAY_MS
    success = observation(len(log), at_ms, spec, True, minutes=3.0)
    day = success.study_day
    mu_before = {c: state.components[c].mu for c in spec.components if c in state.components}
    e_before = dict(MODEL.predict(state, spec, at_ms, study_day=day).e)
    MODEL.update(state, success)
    e_after = dict(MODEL.predict(state, spec, at_ms, study_day=day).e)
    for cid in spec.components:
        assert state.components[cid].mu >= mu_before.get(cid, -float("inf"))
        assert e_after[cid] >= e_before[cid]


@SETTINGS
@given(
    good=st.tuples(st.floats(0.01, 5000.0), st.floats(1.0, 10.0)),
    again=st.tuples(st.floats(0.01, 5000.0), st.floats(1.0, 10.0)),
    phi=st.floats(0.5, 4.0),
)
def test_fsrs_mixture_is_plain_fsrs_when_r_is_0_or_1(good, again, phi):
    horizon = MATCH_HORIZON_DAYS * phi
    assert mix_memory(FSRS, good, again, 1.0, horizon) == good
    assert mix_memory(FSRS, good, again, 0.0, horizon) == again


@SETTINGS
@given(
    good=st.tuples(st.floats(0.01, 5000.0), st.floats(1.0, 10.0)),
    again=st.tuples(st.floats(0.01, 5000.0), st.floats(1.0, 10.0)),
    r=st.floats(0.001, 0.999),
)
def test_fsrs_mixture_matches_recall_at_the_horizon(good, again, r):
    stability, difficulty = mix_memory(FSRS, good, again, r, 7.0)
    low, high = sorted((good[0], again[0]))
    assert low * (1 - 1e-9) <= stability <= high * (1 + 1e-9)
    assert min(good[1], again[1]) - 1e-12 <= difficulty <= max(good[1], again[1]) + 1e-12
    target = r * FSRS.retrievability_after(7.0, good[0]) + (1 - r) * FSRS.retrievability_after(
        7.0, again[0]
    )
    assert abs(FSRS.retrievability_after(7.0, stability) - target) < 1e-9


@SETTINGS
@given(params=shared_params(), log=logs())
def test_a_success_is_exactly_an_fsrs_good_review(params, log):
    """r = 1 on every success: each course component's memory is the plain FSRS Good state
    (same-day formula on the same study day, elapsed time scaled by phi)."""
    state = MODEL.new_state(params)
    for obs in log:
        previous = {
            c: state.components[c].memory for c in obs.problem.components if c in state.components
        }
        MODEL.update(state, obs)
        if not is_success(obs):
            continue
        for cid in obs.problem.components:
            if cid in BACKGROUND:
                continue
            before = previous.get(cid)
            if before is None:
                expected = FSRS.step_fractional(None, GOOD, 0.0, same_day=False)
            else:
                expected = FSRS.step_fractional(
                    (before.stability, before.difficulty),
                    GOOD,
                    params.phi * max(0, obs.at_ms - before.last_ms) / DAY_MS,
                    same_day=before.last_day == obs.study_day,
                )
            after = state.components[cid].memory
            assert after is not None
            assert (after.stability, after.difficulty) == expected
            assert (after.last_ms, after.last_day) == (obs.at_ms, obs.study_day)


def test_a_certain_memory_failure_is_exactly_an_fsrs_again_review():
    """r = 0 needs b m = 1: a lone component whose execution is certain (e = 1) and no slip.
    Then the update is plain FSRS Again, here on the same study day."""
    params = replace(SharedParams(), slip=0.0)
    state = MODEL.new_state(params)
    spec = problem("c1", tier=1)
    first = observation(0, 1_000 * DAY_MS, spec, True)
    MODEL.update(state, first)
    comp = state.components["c1"]
    comp.mu = 60.0  # e rounds to 1.0: execution is certain
    comp.var = 1e-9
    memory = comp.memory
    assert memory is not None
    miss = observation(1, first.at_ms + 3_600_000, spec, False)
    record = MODEL.update(state, miss)
    assert dict(record.blame)["c1"] == 1.0
    assert dict(record.memory_share)["c1"] == 1.0
    expected = FSRS.step_fractional(
        (memory.stability, memory.difficulty), AGAIN, params.phi / 24, same_day=True
    )
    after = state.components["c1"].memory
    assert after is not None
    assert (after.stability, after.difficulty) == expected


@SETTINGS
@given(params=shared_params(), log=logs())
def test_background_components_always_have_recall_1(params, log):
    state = MODEL.new_state(params)
    for obs in log:
        record = MODEL.update(state, obs)
        r = dict(record.prediction.r)
        for cid in obs.problem.components:
            if cid in BACKGROUND:
                assert r[cid] == 1.0
                assert dict(record.memory_share)[cid] == 0.0
    for cid in BACKGROUND:
        comp = state.components.get(cid)
        if comp is not None:
            assert comp.memory is None
            assert (comp.c, comp.f, comp.n) == (0.0, 0.0, 0.0)


@SETTINGS
@given(params=shared_params(), log=logs(), seed=st.integers(0, 2**32 - 1))
def test_replay_equals_incremental_updates_exactly(params, log, seed):
    """C3: the state built one answer at a time (with predictions and what-if copies in
    between) equals a replay of the log, given in any order."""
    state = MODEL.new_state(params)
    records = []
    for obs in log:
        what_if = MODEL.copy(state)
        MODEL.update(what_if, obs)  # a what-if never touches the real state
        MODEL.predict(state, obs.problem, obs.at_ms + DAY_MS)
        records.append(MODEL.update(state, obs))
    shuffled = list(log)
    random.Random(seed).shuffle(shuffled)  # noqa: S311 - reproducible order
    replayed, replay_records = MODEL.replay(params, shuffled)
    assert replayed == state
    assert replay_records == records


@SETTINGS
@given(params=shared_params(), log=logs(min_size=2), seed=st.integers(0, 2**32 - 1))
def test_ties_are_ordered_by_attempt_id(params, log, seed):
    """Observations at the same instant are replayed in attempt_id order, whatever order
    they arrive in; renumbering the ties changes the order the model sees."""
    tied = with_ties(log)
    shuffled = list(tied)
    random.Random(seed).shuffle(shuffled)  # noqa: S311 - reproducible order
    state = MODEL.new_state(params)
    for obs in sorted(tied, key=lambda o: (o.at_ms, o.attempt_id)):
        MODEL.update(state, obs)
    assert MODEL.replay(params, shuffled)[0] == state
    # Reverse the ids within each instant: the replay now follows the reversed order.
    renumbered = [replace(o, attempt_id=-o.attempt_id) for o in tied]
    state2 = MODEL.new_state(params)
    for obs in sorted(renumbered, key=order_key):
        MODEL.update(state2, obs)
    assert MODEL.replay(params, list(reversed(renumbered)))[0] == state2


@SETTINGS
@given(params=shared_params(), log=logs(max_size=30))
def test_same_day_weight_applies_after_the_first_success_of_the_day(params, log):
    """C_k grows by (1 - b_k) w: w = 1 until the component's first success of the study
    day, then same_day_weight. Background components keep no counts."""
    state: StudentState = MODEL.new_state(params)
    successes: dict[tuple[str, date], int] = defaultdict(int)
    for obs in log:
        before = {cid: state.components[cid].c for cid in COURSE if cid in state.components}
        record = MODEL.update(state, obs)
        blame = dict(record.blame)
        for cid in dict.fromkeys(obs.problem.components):
            if cid not in COURSE:
                continue
            first = successes[(cid, obs.study_day)] == 0
            weight = 1.0 if first else params.same_day_weight
            assert state.components[cid].c == before.get(cid, 0.0) + (1.0 - blame[cid]) * weight
            if is_success(obs):
                successes[(cid, obs.study_day)] += 1


@SETTINGS
@given(params=shared_params(), log=logs(max_size=10), spec=problems())
def test_predict_changes_nothing(params, log, spec):
    state = MODEL.new_state(params)
    for obs in log:
        MODEL.update(state, obs)
    snapshot = MODEL.copy(state)
    later = log[-1].at_ms + 9 * DAY_MS
    first = MODEL.predict(state, spec, later)
    assert state == snapshot
    assert MODEL.predict(state, spec, later) == first
