"""Seeded-error test of the acceptance pipeline (review R8.1; content-tools/seeded_errors.py).

About 100 plausible wrong keys (sign, factor, chain rule, off by one) are seeded into
verified fixture cards whose worked solutions carry `check:` claims. The whole pack-build
pipeline must reject every one; the table (also printed by the script) records the
fraction rejected by error type, with the self-check alone for comparison.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def seeded() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "seeded_errors", ROOT / "content-tools" / "seeded_errors.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.slow
def test_the_pipeline_rejects_every_seeded_wrong_key() -> None:
    tool = seeded()
    report = tool.run()
    print("\n" + report.table())
    assert report.control_errors == []  # the true keys build clean
    assert sum(report.total.values()) >= 100
    assert set(report.total) == set(tool.ERROR_TYPES)
    for kind in tool.ERROR_TYPES:
        assert report.fraction("pipeline", kind) == 1.0, (kind, report.missed)
    # The self-check alone catches only the slips a card lists as known wrong answers.
    assert report.fraction("self-check", "sign") == 0.0
    assert 0 < report.fraction("self-check", "chain-rule") < 1
