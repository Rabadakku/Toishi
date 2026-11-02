"""Design 6.1: parameter recovery from one simulated student at 1,000 attempts.

The student is sampled from the model itself (core.learner.simulate) on a synthetic course
of 60 components (48 course, 12 background) whose problems have 1-5 components across tiers
1-4, with known non-default s, delta4, phi, tau and sigma_T. The refit starts from the
priors. The test prints every value and asserts only s and tau within +-50%; the rest are
reported (docs/design/student-model-impl-notes.md has the results across seeds). The seeds
were fixed before the first run and are not tuned.

phi is not recovered: the refit leaves it at its prior (about 2% of the gap closed). Its
+-50% band around the true 2.0 happens to include the prior 1.0, so read the "gap closed"
column, not the band.
"""

import pytest

from core.learner.model import StudentModel
from core.learner.refit import refit
from core.learner.simulate import simulate, synthetic_course
from core.learner.types import SharedParams

TRUTH = SharedParams(version="truth", slip=0.12, delta4=0.8, phi=2.0, tau=0.3, sigma_t=0.3)
COURSE_SEED = 11
STUDENT_SEED = 7
ATTEMPTS = 1000


def _within_half(value: float, truth: float) -> bool:
    return abs(value - truth) <= 0.5 * abs(truth)


@pytest.mark.slow
def test_parameter_recovery_at_1000_attempts(capsys):
    course = synthetic_course(seed=COURSE_SEED)
    sim = simulate(course, TRUTH, ATTEMPTS, seed=STUDENT_SEED)
    prior = SharedParams()
    decision = refit(StudentModel(course.catalog), sim.observations, prior)
    fit = decision.candidate
    rows = [
        ("slip", TRUTH.slip, prior.slip, fit.slip),
        ("delta4", TRUTH.delta4, prior.delta4, fit.delta4),
        ("phi", TRUTH.phi, prior.phi, fit.phi),
        ("tau", TRUTH.tau, prior.tau, fit.tau),
        ("sigma_t", TRUTH.sigma_t, prior.sigma_t, fit.sigma_t),
        ("calib_b", TRUTH.calib_b, prior.calib_b, fit.calib_b),
        *(
            (f"calib_a{tier}", TRUTH.calib_a[tier - 1], 0.0, fit.calib_a[tier - 1])
            for tier in range(1, 5)
        ),
    ]
    lines = [
        f"\n6.1 recovery, {ATTEMPTS} attempts (course seed {COURSE_SEED}, "
        f"student seed {STUDENT_SEED}). 'gap closed' = (prior - refit) / (prior - true):",
        f"  {'parameter':10} {'true':>7} {'prior':>7} {'refit':>7} {'rel.err':>8} "
        f"{'gap closed':>10}",
    ]
    for name, true, start, value in rows:
        error = f"{abs(value - true) / abs(true):8.2f}" if true != 0.0 else f"{'-':>8}"
        gap = f"{(start - value) / (start - true):10.2f}" if start != true else f"{'-':>10}"
        lines.append(f"  {name:10} {true:7.3f} {start:7.3f} {value:7.3f} {error} {gap}")
    for block in decision.blocks:
        lines.append(
            f"  block {block.name}: held-out {block.current_score:.4f} -> "
            f"{block.candidate_score:.4f} nats/attempt, p = {block.p_value:.3f}, "
            f"adopted {block.adopted}"
        )
    with capsys.disabled():
        print("\n".join(lines))
    assert _within_half(fit.slip, TRUTH.slip)
    assert _within_half(fit.tau, TRUTH.tau)
