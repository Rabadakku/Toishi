"""P0's rules, and the stand-in model, certifier and planner that P1 uses until the merge."""

import math
from dataclasses import replace
from datetime import date, timedelta

import pytest

from core.learner.types import Observation, ProblemSpec, SharedParams, StudentState
from core.plan.types import CourseSettings, WorkItem
from tools.sim2.common import session_ms, sigmoid
from tools.sim2.course import toy
from tools.sim2.fsrs6 import DEFAULT, GOOD
from tools.sim2.policies import LEARN_CAP, BaselinePolicy
from tools.sim2.standin import (
    StandinCertifier,
    StandinModel,
    StandinPlanner,
    intro_dates,
    milestones,
)

START = date(2027, 1, 11)
SETTINGS = CourseSettings(course_id="toy", start=START)


def _obs(
    spec: ProblemSpec,
    day: date,
    correct: bool,
    *,
    minutes: float | None = 1.0,
    offset: int = 0,
    matched: int | None = None,
    role: str = "growth",
) -> Observation:
    return Observation(
        attempt_id=offset,
        at_ms=session_ms(day) + offset * 60_000,
        study_day=day,
        problem=spec,
        correct=correct,
        matched_wrong=matched,
        minutes=minutes if correct else None,
        role=role,
    )


# ---------------------------------------------------------------- pace schedule


def test_intro_dates_follow_section_hours() -> None:
    sim = toy()
    intro = intro_dates(sim.course, SETTINGS)
    assert intro["toy.a1"] == intro["toy.a2"] == START
    assert intro["toy.b1"] == intro["toy.b2"] == START + timedelta(days=5)
    assert intro["toy.c1"] == intro["toy.c2"] == START + timedelta(days=9)
    ms = milestones("toy.a1", START, SETTINGS)
    assert [(m.name, m.tier, m.deadline) for m in ms] == [
        ("M1", 2, START + timedelta(days=7)),
        ("M2", 3, START + timedelta(days=21)),
        ("M3", 4, START + timedelta(days=35)),
    ]


# ---------------------------------------------------------------- P0


def _serve_p0(policy: BaselinePolicy, day: date) -> WorkItem | None:
    return policy.next_item(day, session_ms(day))


def _next_review(policy: BaselinePolicy, day: date) -> WorkItem:
    while (item := _serve_p0(policy, day)) is not None:
        if item.role == "maintenance":
            return item
    raise AssertionError("no review served")


def test_baseline_learns_with_three_in_a_row_then_reviews_at_the_target_tier() -> None:
    sim = toy()
    policy = BaselinePolicy(sim, SETTINGS, intro_dates(sim.course, SETTINGS), seed=1)
    plan = policy.start_day(START, session_ms(START))
    assert [i.skill_id for i in plan.items[: 1 + LEARN_CAP]] == ["toy.a1"] * (1 + LEARN_CAP)
    example = _serve_p0(policy, START)
    assert example is not None
    assert example.problem is None
    assert example.role == "new"
    policy.observe(example, None, 3.0)
    outcomes = [True, False, True, True, True]
    for i, ok in enumerate(outcomes):
        item = _serve_p0(policy, START)
        assert item is not None
        assert item.skill_id == "toy.a1"
        assert item.problem is not None
        assert item.problem.tier in (1, 2)
        assert policy.predict(item.problem, session_ms(START)) is None
        policy.observe(item, _obs(item.problem, START, ok, offset=i, role="new"), 1.0)
    assert policy.certified("toy.a1", 2, START)
    assert not policy.certified("toy.a1", 3, START)
    nxt = _serve_p0(policy, START)
    assert nxt is not None
    assert nxt.skill_id == "toy.a2"
    day = policy.due["toy.a1"]
    assert day > START
    plan = policy.start_day(day, session_ms(day))
    reviews = [i for i in plan.items if i.role == "maintenance"]
    assert [i.skill_id for i in reviews] == ["toy.a1"]
    for k in range(3):
        day = policy.due["toy.a1"]
        policy.start_day(day, session_ms(day))
        item = _next_review(policy, day)
        assert item.problem is not None
        assert item.problem.tier == 4
        p = policy.predict(item.problem, session_ms(day))
        assert p is not None
        assert 0.0 < p < 1.0
        slow = k == 1
        minutes = item.problem.standard_minutes * (1.5 if slow else 0.5)
        policy.observe(
            item, _obs(item.problem, day, True, minutes=minutes, role="maintenance"), minutes
        )
    assert not policy.certified("toy.a1", 4, day)  # the slow answer broke the streak


# ---------------------------------------------------------------- stand-in model


def _model() -> tuple[StandinModel, SharedParams]:
    return StandinModel(toy().catalog), SharedParams()


def test_prediction_from_priors() -> None:
    model, params = _model()
    state = model.new_state(params)
    spec = toy().pools["toy.a2"][2][0]
    pred = model.predict(state, spec, session_ms(START))
    expected = 1.0 - params.slip
    for comp in spec.components:
        background = toy().catalog[comp].background
        mean = params.prior_background_mean if background else params.prior_new_mean
        var = params.prior_background_var if background else params.prior_new_var
        expected *= sigmoid(mean / math.sqrt(1.0 + math.pi * var / 8.0))
    assert pred.p_raw == pytest.approx(expected)
    assert pred.p == pytest.approx(pred.p_raw)  # calibration starts at a = 0, b = 1
    assert all(r == 1.0 for _, r in pred.r)
    assert pred.median_minutes == pytest.approx(spec.standard_minutes * 2.0)


def test_success_raises_execution_and_creates_good_memory() -> None:
    model, params = _model()
    state = model.new_state(params)
    spec = toy().pools["toy.a1"][1][0]
    before = model.predict(state, spec, session_ms(START)).p
    model.update(state, _obs(spec, START, True))
    cs = state.components["toy.a1"]
    assert cs.c == 1.0
    assert cs.f == 0.0
    assert cs.n == 1.0
    assert cs.memory is not None
    assert (cs.memory.stability, cs.memory.difficulty) == pytest.approx(DEFAULT.initial(GOOD))
    model.update(state, _obs(spec, START, True, offset=5))
    assert cs.c == 1.25  # same-day successes count 0.25
    later = session_ms(START) + 60_000 * 10
    assert model.predict(state, spec, later).p > before
    assert state.time_stats[2] == 2


def test_failure_blame_and_matched_error() -> None:
    model, params = _model()
    state = model.new_state(params)
    spec = toy().pools["toy.c2"][3][0]
    assert len(spec.components) >= 3
    record = model.update(state, _obs(spec, START, False))
    blame = dict(record.blame)
    pred = record.prediction
    q = dict(pred.q)
    for comp, b in blame.items():
        assert b == pytest.approx((1.0 - q[comp]) / (1.0 - pred.p_raw))
    state2 = model.new_state(params)
    index, named = spec.wrong_components[0]
    record2 = model.update(state2, _obs(spec, START, False, matched=index))
    blame2 = dict(record2.blame)
    assert blame2[named] >= params.kappa
    assert all(blame2[c] < 0.1 for c in blame2 if c != named)
    assert state2.components[named].mu < params.prior_new_mean


def test_seven_day_memory_match_is_exact_at_the_extremes() -> None:
    model, params = _model()
    state = model.new_state(replace(params, phi=1.0))  # the reference FSRS-6 clock
    spec = toy().pools["toy.a1"][1][0]
    model.update(state, _obs(spec, START, True))
    mem = state.components["toy.a1"].memory
    assert mem is not None
    s0, d0 = mem.stability, mem.difficulty
    later = START + timedelta(days=3)
    model.update(state, _obs(spec, later, True))
    r_now = DEFAULT.retrievability(3.0, s0)
    expected = DEFAULT.review(s0, d0, GOOD, 3, r_now)
    mem = state.components["toy.a1"].memory
    assert mem is not None
    assert (mem.stability, mem.difficulty) == pytest.approx(expected)


def test_background_components_have_no_memory_or_counts() -> None:
    model, params = _model()
    state = model.new_state(params)
    spec = next(p for p in toy().pools["toy.a2"][3] if "alg.x" in p.components)
    model.update(state, _obs(spec, START, True))
    bg = state.components["alg.x"]
    assert bg.memory is None
    assert bg.c == 0.0
    assert bg.n == 0.0
    assert bg.attempts == 1
    assert bg.mu > params.prior_background_mean


# ---------------------------------------------------------------- stand-in certifier


def test_certifier_posterior_and_hysteresis() -> None:
    cert = StandinCertifier(target=0.9)
    for _ in range(4):
        cert.add("s", 2, START, True)
    mean, n_eff = cert.posterior("s", 2, START, prior=0.5)
    assert (mean, n_eff) == pytest.approx(((2.0 + 4.0) / 8.0, 4.0))
    assert not cert.refresh("s", 2, START, prior=0.5, needed=3)
    assert cert.refresh("s", 2, START, prior=0.95, needed=3)
    aged, n_aged = cert.posterior("s", 2, START + timedelta(days=30), prior=0.95)
    assert n_aged == pytest.approx(2.0)
    cert.add("s", 2, START, False)
    assert cert.refresh("s", 2, START, prior=0.95, needed=3)  # 7.8 / 9 = 0.87: kept
    cert.add("s", 2, START, False)
    assert not cert.refresh("s", 2, START, prior=0.95, needed=3)  # 7.8 / 10: revoked
    assert aged > 0.9


# ---------------------------------------------------------------- stand-in planner


def _serve_day(
    planner: StandinPlanner,
    model: StandinModel,
    state: StudentState,
    day: date,
    outcome: bool = True,
) -> tuple[int, list[WorkItem]]:
    served: list[WorkItem] = []
    plan = planner.plan_day(state, day, session_ms(day))
    for i in range(500):
        item = planner.next_item(state, day, session_ms(day) + i, served)
        if item is None:
            break
        if item.problem is not None:
            obs = _obs(item.problem, day, outcome, offset=i, minutes=0.1, role=item.role)
            planner.observe(state, item, obs, model.update(state, obs), 0.1)
        else:
            planner.observe(state, item, None, None, 3.0)
        served.append(item)
    planner.end_day(state, day, session_ms(day))
    return len(plan.items), served


def test_planner_serves_new_material_first_and_never_beyond_the_plan() -> None:
    sim = toy()
    model = StandinModel(sim.catalog)
    state = model.new_state(SharedParams())
    planner = StandinPlanner(model, sim.course, SETTINGS, seed=1)
    planned, served = _serve_day(planner, model, state, START)
    assert len(served) <= planned
    assert [i.role for i in served[:2]] == ["new", "new"]
    assert served[0].problem is None
    assert served[0].skill_id == "toy.a1"
    # one success ends a new skill's block
    a1 = [i for i in served if i.skill_id == "toy.a1"]
    assert [i.problem is None for i in a1] == [True, False]
    seen_other = False
    for item in served:
        if item.role != "new":
            seen_other = True
        assert not (seen_other and item.role == "new")
    for d in range(1, 12):
        day = START + timedelta(days=d)
        planned, served = _serve_day(planner, model, state, day)
        assert len(served) <= planned
        per_skill: dict[str, int] = {}
        for item in served:
            if item.problem is not None:
                per_skill[item.skill_id] = per_skill.get(item.skill_id, 0) + 1
        assert max(per_skill.values(), default=0) <= 3
        growth = [i for i in served if i.role == "growth"]
        for skill in {i.skill_id for i in growth}:
            # always right: growth stops after two successes in a row
            assert sum(1 for i in growth if i.skill_id == skill) <= 2
    assert planner.cert.certified("toy.a1", 2)


def test_reference_checks_come_every_tenth_item() -> None:
    sim = toy()
    model = StandinModel(sim.catalog)
    state = model.new_state(SharedParams())
    planner = StandinPlanner(model, sim.course, SETTINGS, seed=2)
    roles: list[str] = []
    for d in range(0, 20):
        day = START + timedelta(days=d)
        _, served = _serve_day(planner, model, state, day, outcome=d % 3 != 0)
        roles.extend(i.role for i in served)
    checks = [i for i, r in enumerate(roles) if r == "check"]
    assert checks
    assert all((i + 1) % 10 == 0 for i in checks)


def test_work_item_contract_fields() -> None:
    item = WorkItem("s", "growth", None, "s#example", 3.0, 0)
    assert replace(item, role="check").role == "check"
