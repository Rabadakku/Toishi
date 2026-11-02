"""The default matrix (Chapter 4 + prerequisites, one seed) against the design 6.2 gates.

P1 runs on whatever `adapters.load_backend("auto")` returns: the stand-in until model-core
and plan-core merge, the real `core.learner` + `core.plan` after, when these become the
shipping gates the design asks for.
"""

import os

import pytest

from tools.sim2.harness import RunConfig
from tools.sim2.metrics import gates
from tools.sim2.run import run_matrix, specs
from tools.sim2.truth import DEFAULT_TRUTHS, PROFILES

pytestmark = [pytest.mark.slow, pytest.mark.gates]


def test_calc1_matrix_passes_the_design_gates() -> None:
    summaries = run_matrix(
        specs("calc1-ch4", DEFAULT_TRUTHS, PROFILES, (1,)),
        RunConfig(),
        processes=os.cpu_count() or 1,
    )
    assert len(summaries) == len(DEFAULT_TRUTHS) * len(PROFILES) * 2
    p1_gates = [g for g in gates(summaries) if g.policy in ("P1", "P1 vs P0")]
    assert len(p1_gates) == 4
    failed = [f"{g.name}: {g.detail}" for g in p1_gates if not g.passed]
    assert not failed, failed
