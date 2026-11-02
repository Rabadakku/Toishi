"""Daily queue and study sessions (milestone M5): what the student does each day, in what
order, and every study session. docs/spec.md "The daily queue"; ADR-0009, and ADR-0010
(every card kind, practice tests).

Public API (what the bridge calls), `StudyService(storage, hooks=(), checker=None)`:

Home and plans
- today() -> TodayView            today's problems and minutes per course, exams, proposals
- forecast(day=None) -> Forecast  tomorrow's (or a day's) problems and minutes
- plan_preview(day=None) -> Plan  the plan start() would build (stats, tests)
- set_vacation(start, end) / clear_vacation()                       QUE-9

Sessions (each returns a Turn: a problem, a summary or nothing to do)
- start(StartRequest | dict) -> Turn   daily | lighter | focused | extra | practice-test;
                                       resumes today's open session (QUE-16)
- resume() -> Turn | None; current() -> Turn
- next() -> Turn                       continue: grade the answer on screen, serve the next
- set_lighter(on=True) -> Turn         QUE-10 mid-session
- undo() -> Turn                       QUE-15 (refused with a message when not exact)
- end() -> Summary                     summary and tomorrow's forecast (practice tests graded)

Answering the problem on screen
- read_answer(raw, part=, source=) -> grader.Preview    "We read your answer as ..."
- submit(SubmitRequest | dict) -> AttemptResult        retry | correct | incorrect |
                                                        invalid | self-grade | recorded
  Multi-part problems: answers labeled by part, each part with its own verdict and tries
  (PartVerdictView.final / tries_used); a part already final is not checked again.
  Find-the-error: also `error_step` and `reason` (AttemptResult.find_error says which
  of step, reason and value were right). Which-method items: one try, a choice.
- show_solution() -> AttemptResult     self-graded problems: the solution and rubric; then
                                       submit rubric_ticked or self_grade
- give_up(timing) -> AttemptResult; hint() -> HintReveal; open_example()
- diagnose(choice, step=None) -> Diagnosis  "What went wrong?" (grades with the choice)
- flag(kind, note=None) -> FlagResult  too_easy | dispute | report | flag | suspend
- rate_flashcard(rating=None, answer=None) -> AttemptResult
- tick(active_ms, draft=None) -> Tick  saves active time and draft; break reminder

Pure pieces (no storage): share.split (QUE-11 quotas), triage.candidates and POLICIES
(QUE-6), order.order_items (session ordering), planner.build_plan / rebalance,
guards.guard_timing (TIME-4/5), estimate.TimeTable (QUE-3), daylog (QUE-8/9/12/13).
Requests and responses are dataclasses in `views`; `to_dict` makes JSON-ready dicts.
"""

from core.queue.daylog import DayEntry, Vacation
from core.queue.guards import Guarded, TimingReport, guard_timing
from core.queue.items import Mode, Plan, PlanItem, ReasonTag
from core.queue.order import order_items
from core.queue.planner import build_plan, rebalance
from core.queue.session import QueueError, StudyService
from core.queue.share import CourseDemand, Share, split
from core.queue.snapshot import QueueSettings, Snapshot, gather
from core.queue.triage import POLICIES, TriagePolicy, candidates
from core.queue.views import (
    AttemptResult,
    CourseLine,
    Diagnosis,
    ExamLine,
    FindErrorView,
    FlagResult,
    Forecast,
    HintReveal,
    PartAnswer,
    ProblemView,
    Progress,
    Proposal,
    Reason,
    SolutionView,
    StartRequest,
    SubmitRequest,
    Summary,
    TestResult,
    Tick,
    TodayView,
    Turn,
    to_dict,
)

__all__ = [
    "POLICIES",
    "AttemptResult",
    "CourseDemand",
    "CourseLine",
    "DayEntry",
    "Diagnosis",
    "ExamLine",
    "FindErrorView",
    "FlagResult",
    "Forecast",
    "Guarded",
    "HintReveal",
    "Mode",
    "PartAnswer",
    "Plan",
    "PlanItem",
    "ProblemView",
    "Progress",
    "Proposal",
    "QueueError",
    "QueueSettings",
    "Reason",
    "ReasonTag",
    "Share",
    "Snapshot",
    "SolutionView",
    "StartRequest",
    "StudyService",
    "SubmitRequest",
    "Summary",
    "TestResult",
    "Tick",
    "TimingReport",
    "TodayView",
    "TriagePolicy",
    "Turn",
    "Vacation",
    "build_plan",
    "candidates",
    "gather",
    "guard_timing",
    "order_items",
    "rebalance",
    "split",
    "to_dict",
]
