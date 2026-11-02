"""The synthetic course and the generator that samples students from the model."""

import itertools
import math
from dataclasses import replace

from core.learner.model import StudentModel
from core.learner.simulate import simulate, synthetic_course
from core.learner.types import SharedParams
from tests.learner.helpers import DAYS

COURSE = synthetic_course(seed=11)


def test_synthetic_course_shape():
    assert len(COURSE.catalog) == 60
    assert sum(info.background for info in COURSE.catalog.values()) == 12
    assert len(COURSE.problems) == 48 * 8
    sizes = {1: (1, 1), 2: (1, 2), 3: (2, 4), 4: (3, 5)}
    for p in COURSE.problems:
        low, high = sizes[p.tier]
        assert low <= len(p.components) <= high
        assert len(set(p.components)) == len(p.components)
        assert p.components[0] == p.main_skill
        assert not COURSE.catalog[p.main_skill].background
        expected = 0.5 + 1.5 * p.steps + 1.5 * max(0, p.tier - 3)
        assert p.standard_minutes == expected
    assert {p.tier for p in COURSE.problems} == {1, 2, 3, 4}


def test_a_small_course_has_problems_no_larger_than_its_components_allow():
    """The first component has no earlier ones: with 2 background components its problems
    have at most 3 components (this used to loop forever)."""
    small = synthetic_course(seed=1, course_components=6, background_components=2)
    first = [p for p in small.problems if p.main_skill == "c000"]
    assert max(len(p.components) for p in first) == 3
    assert all(len(set(p.components)) == len(p.components) for p in small.problems)
    none = synthetic_course(seed=1, course_components=3, background_components=0)
    assert all(len(p.components) == 1 for p in none.problems if p.main_skill == "c000")


def test_simulation_is_deterministic_and_well_formed():
    truth = SharedParams()
    first = simulate(COURSE, truth, 300, seed=4)
    assert first == simulate(COURSE, truth, 300, seed=4)
    obs = first.observations
    assert [o.attempt_id for o in obs] == list(range(300))
    assert all(a.at_ms < b.at_ms for a, b in itertools.pairwise(obs))
    assert all(o.study_day == DAYS.day_of(o.at_ms) for o in obs)
    assert all((o.minutes is not None) == o.correct for o in obs)
    assert all(o.minutes is None or o.minutes > 0 for o in obs)
    assert abs(sum(first.speed.values())) < 1e-9  # centred speed offsets


def test_slip_caps_the_success_rate_of_a_student_who_knows_everything():
    """theta = 20: every component is certain to execute; with phi small and no drift,
    memory barely fails, so successes run at about 1 - s."""
    truth = replace(SharedParams(), slip=0.2, phi=0.5, q_drift=0.0)
    sim = simulate(COURSE, truth, 800, seed=5, theta=20.0)
    rate = sum(o.correct for o in sim.observations) / len(sim.observations)
    assert 0.74 < rate <= 0.82


def test_times_follow_the_model_time_equation():
    """With no noise and no per-skill offsets, ln T - ln T* + alpha ln(1 + nbar) = tau for
    every timed success, nbar counted the way the model counts it."""
    truth = replace(SharedParams(), tau=0.4, sigma_t=1e-9)
    sim = simulate(COURSE, truth, 400, seed=6, speed_sd=0.0)
    attempts = StudentModel(COURSE.catalog).time_attempts(truth.alpha, sim.observations)
    assert attempts
    assert all(math.isclose(a.x, 0.4, abs_tol=1e-6) for a in attempts)
