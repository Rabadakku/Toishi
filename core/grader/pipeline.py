"""One grading job, as run inside the worker: compare, form, wrong answers, confirm.

Order matters for the hard time limit: the numeric verdict, the form check and the
known-wrong match are reported as a preliminary result before the (slower) symbolic
confirmation, so a kill at 2 s still leaves a sound verdict.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from core.grader import shapes as s
from core.grader.spec import Card

if TYPE_CHECKING:
    from core.grader.compare import Verdict

FORM_SOFT_SECONDS = 0.5
MARGIN = 0.15


@dataclass(frozen=True, slots=True)
class Job:
    card: Card
    answer: s.Value
    check_wrong: bool = True
    seconds: float = 2.0
    skip_form: bool = False
    mode: str = "grade"  # "key": only check that the key itself is usable (MATH-13)
    # "cross": DEV-18, compare SymPy and mpmath on this answer and key, given the verdict
    status: str = ""


@dataclass(frozen=True, slots=True)
class JobResult:
    status: str  # correct / incorrect / undecidable / hole (matches except at removable points)
    message: str = ""
    step: str = ""
    confirmed: bool = False
    matched_wrong: int | None = None
    timings: dict[str, float] = field(default_factory=dict)
    final: bool = True


def _best(verdicts: list[Verdict]) -> tuple[Verdict, int | None]:
    from core.grader.compare import Verdict

    for wanted in ("correct", "hole"):
        for i, v in enumerate(verdicts):
            if v.status == wanted:
                return v, i
    for v in verdicts:
        if v.status == "undecidable":
            return v, None
    return (verdicts[0] if verdicts else Verdict("undecidable", "No key.")), None


def run_job(job: Job, report: Callable[[JobResult], None] | None = None) -> JobResult:
    # SymPy and mpmath load here, in the worker, never in the app's own process.
    from core.grader.compare import Checker, Verdict
    from core.grader.forms import form_problem
    from core.grader.symbolic import Deadline

    t0 = time.perf_counter()
    timings: dict[str, float] = {}
    deadline = Deadline(job.seconds - MARGIN)
    card = job.card
    checker = Checker(card, deadline, symbolic=False)
    if job.mode == "cross":
        from core.grader.differential import cross

        problems = cross(card, job.answer, job.status, deadline)
        status = "incorrect" if problems else "correct"
        return JobResult(status, "\n".join(problems), "cross", timings={"cross": _ms(t0)})
    if job.mode == "key":
        problem = checker.key_problem(job.answer)
        status = "undecidable" if problem else "correct"
        return JobResult(status, problem or "", "key", timings={"key": _ms(t0)})
    verdicts: list[Verdict] = []
    for key in card.keys:
        verdict = checker.compare(job.answer, key)
        verdicts.append(verdict)
        if verdict.status == "correct":
            break
    verdict, key_index = _best(verdicts)
    timings["numeric"] = _ms(t0)

    t1 = time.perf_counter()
    if (
        verdict.status in {"correct", "hole"}
        and card.form is not None
        and key_index is not None
        and not job.skip_form
    ):
        budget = min(FORM_SOFT_SECONDS, deadline.left() - 0.2)
        problem = form_problem(card.form, job.answer, card.keys[key_index], checker.ctx, budget)
        if problem is not None:
            verdict = Verdict("incorrect", problem, "form")
    timings["form"] = _ms(t1)

    t2 = time.perf_counter()
    matched: int | None = None
    if verdict.status == "incorrect" and job.check_wrong:
        for i, (_, wrong_value) in enumerate(card.wrong):
            if wrong_value is None or deadline.left() < 0.3:
                continue
            if checker.compare(job.answer, wrong_value).status == "correct":
                matched = i
                break
    timings["wrong"] = _ms(t2)

    result = JobResult(
        verdict.status, verdict.message, verdict.step, verdict.confirmed, matched, dict(timings)
    )
    needs_symbolic = verdict.status in {"correct", "undecidable", "hole"} and verdict.step != "form"
    if not needs_symbolic or verdict.confirmed:
        return result
    if report is not None:
        report(replace(result, final=False))

    # Step 4: symbolic confirmation, with whatever time is left.
    t3 = time.perf_counter()
    checker.symbolic = True
    keys = [card.keys[key_index]] if key_index is not None else list(card.keys)
    confirmed = [checker.compare(job.answer, k) for k in keys]
    final, _ = _best(confirmed)
    timings["symbolic"] = _ms(t3)
    if verdict.status in {"correct", "hole"} and final.status not in {"correct", "hole"}:
        # The second pass repeats the same deterministic sampling; it can only turn a
        # match into a miss through a symbolic proof of a nonzero difference.
        if final.status == "incorrect":
            return JobResult("incorrect", final.message, "symbolic", False, None, timings)
        return replace(result, timings=timings)
    return JobResult(final.status, final.message, final.step, final.confirmed, matched, timings)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)
