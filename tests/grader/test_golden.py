"""MATH-11: the golden suite. Every case goes through the real worker process."""

import pytest

from core.grader import Status, grade
from tests.grader.golden import Case, load_cases

CASES = load_cases()


def test_golden_suite_is_big_enough() -> None:
    assert len(CASES) >= 600
    kinds = {c.spec.answer_type for c in CASES}
    assert kinds >= {
        "number", "expression", "equation", "antiderivative", "set", "list", "interval",
        "point", "vector", "matrix", "choice", "truefalse", "text", "quantity",
    }  # fmt: skip
    assert {c.expected for c in CASES} >= {"correct", "incorrect", "invalid", "undecidable"}


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_golden(case: Case) -> None:
    result = grade(case.raw, case.spec, case.source)  # type: ignore[arg-type]
    assert result.status == Status(case.expected), (
        f"{case.raw!r} against {case.spec.answer!r}: got {result.status.value}"
        f" ({result.message}; hints {result.hints})"
    )
