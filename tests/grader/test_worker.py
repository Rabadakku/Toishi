"""MATH-15: the worker process, its hard 2-second limit, and the latency budget."""

import os
import signal
import statistics
import threading
import time

import pytest

from core.grader import AnswerSpec, Status, grade
from core.grader.parser import parse
from core.grader.pipeline import Job, JobResult, run_job
from core.grader.shapes import shape_value
from core.grader.spec import resolve
from core.grader.worker import HARD_LIMIT_SECONDS, worker
from tests.grader.golden import load_cases


def _job(raw: str, spec: AnswerSpec) -> Job:
    card = resolve(spec)
    value = shape_value(parse(raw, card.vocab), card.answer_type, [v for v, _ in card.variables])
    return Job(card, value)


def test_hard_limit_kills_and_restarts_the_worker() -> None:
    w = worker()
    assert grade("1", AnswerSpec("number", "1")).status is Status.CORRECT
    pid = w.pid
    restarts = w.restarts
    start = time.monotonic()
    result, timed_out = w.run(None, sleep=30.0)  # a job that hangs past every soft limit
    elapsed = time.monotonic() - start
    assert result is None
    assert timed_out
    assert HARD_LIMIT_SECONDS <= elapsed < HARD_LIMIT_SECONDS + 1.0
    assert w.restarts == restarts + 1
    assert w.pid != pid
    # The fresh worker serves the next answer.
    assert grade("x + x", AnswerSpec("expression", "2x")).status is Status.CORRECT


def test_a_timeout_is_undecidable(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(job: Job | None, **kwargs: object) -> tuple[JobResult | None, bool]:
        return None, True

    monkeypatch.setattr(worker(), "run", slow)
    r = grade("x^2", AnswerSpec("expression", "x*x"))
    assert r.status is Status.UNDECIDABLE
    assert r.message == "The checker took too long."
    assert not r.counts_as_attempt


def test_preliminary_result_stands_when_confirmation_is_cut_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prelim = JobResult("correct", step="numeric", final=False)
    monkeypatch.setattr(worker(), "run", lambda job, **kw: (prelim, True))
    assert grade("x^2", AnswerSpec("expression", "x*x")).status is Status.CORRECT


def test_numeric_verdict_is_reported_before_symbolic_confirmation() -> None:
    reports: list[JobResult] = []
    final = run_job(
        _job("sin(x)^2 + cos(x)^2", AnswerSpec("expression", "1", vars=("x",))), reports.append
    )
    assert [r.final for r in reports] == [False]
    assert reports[0].status == "correct"
    assert final.status == "correct"
    assert final.final


def test_worker_recovers_after_being_killed() -> None:
    w = worker()
    grade("1", AnswerSpec("number", "1"))
    assert w.pid is not None
    os.kill(w.pid, signal.SIGKILL)
    time.sleep(0.1)
    assert grade("2", AnswerSpec("number", "4/2")).status is Status.CORRECT


def test_concurrent_grades_are_serialized_safely() -> None:
    spec = AnswerSpec("expression", "(x+1)^2")
    answers = ["x^2+2x+1", "x^2+1", "(1+x)^2", "x^2+2x"] * 4
    results: dict[int, Status] = {}

    def run(i: int, raw: str) -> None:
        results[i] = grade(raw, spec).status

    threads = [threading.Thread(target=run, args=(i, a)) for i, a in enumerate(answers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    expected = {"x^2+2x+1": Status.CORRECT, "(1+x)^2": Status.CORRECT}
    for i, raw in enumerate(answers):
        assert results[i] == expected.get(raw, Status.INCORRECT), raw


def test_stop_and_restart() -> None:
    worker().stop()
    assert worker().pid is None
    assert grade("3", AnswerSpec("number", "3")).status is Status.CORRECT


@pytest.mark.slow
def test_benchmark_math_15() -> None:
    """95% of answers graded in under 300 ms; none over the 2 s hard limit.

    The sample is every golden case that reaches the worker (correct or incorrect),
    timed end to end through grade(), so parsing and IPC are included.
    """
    cases = [c for c in load_cases() if c.expected in {"correct", "incorrect"}]
    cases = [c for c in cases if c.spec.answer_type not in {"choice", "truefalse", "text"}]
    grade("1", AnswerSpec("number", "1"))  # warm
    times: list[float] = []
    for c in cases:
        start = time.perf_counter()
        grade(c.raw, c.spec, c.source)  # type: ignore[arg-type]
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    p50 = statistics.median(times)
    p95 = times[int(0.95 * len(times)) - 1]
    print(f"\nMATH-15 benchmark: n={len(times)} p50={p50:.1f} ms p95={p95:.1f} ms "
          f"p99={times[int(0.99 * len(times)) - 1]:.1f} ms max={times[-1]:.1f} ms")  # fmt: skip
    assert len(times) >= 500
    assert p95 < 300
    assert times[-1] < HARD_LIMIT_SECONDS * 1000 + 500
