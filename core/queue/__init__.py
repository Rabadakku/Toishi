"""Daily queue and study sessions: what the student does each day, in what order, and every
study session. docs/spec.md "The daily queue"; ADR-0009, ADR-0010 (every card kind, practice
tests); wave 2: docs/design/wave2-integration.md section 4 (problems planned by core.practice).

Public API (what the bridge calls), `StudyService(storage, checker=None, previewer=None)`:

Home and plans
- today() -> TodayView            today's items and minutes by course and role, hours to keep
                                  pace, skills behind or set aside, sittings, the planner's notes
- forecast(day=None) -> Forecast  tomorrow's (or a day's) problems and minutes
- plan_preview(day=None) -> Plan  the plan start() would build (stats, tests)

Sessions (each returns a Turn: a problem, a summary or nothing to do)
- start(StartRequest | dict) -> Turn   daily | extra | practice-test; resumes today's open
                                       session (QUE-16)
- resume() -> Turn | None; current() -> Turn
- next() -> Turn                       continue: commit the answer on screen, serve the next
- undo() -> Turn                       QUE-15 (refused with a message when not exact)
- end() -> Summary                     summary and tomorrow's forecast (practice tests graded)

Answering the problem on screen
- read_answer(raw, part=, source=) -> grader.Preview    "We read your answer as ..."
- submit(SubmitRequest | dict) -> AttemptResult        retry | correct | incorrect |
                                                        invalid | self-grade | recorded
  A wrong try is "retry": the verdict alone ("Not quite"), `can_retry`, and
  `first_try_counted` (it was the problem's first try, the one that counts). Multi-part
  problems: answers labeled by part, each part with its own verdict and tries
  (PartVerdictView.final / tries_used); a part already right is not checked again.
- show_solution() -> AttemptResult     self-graded problems: the solution and rubric, then
                                       submit rubric_ticked or self_grade; any other problem:
                                       after a wrong first try, ending it like give_up
- give_up(timing) -> AttemptResult     the full solution; open_example()
- flag(kind, note=None) -> FlagResult  too_easy | dispute | report | flag | suspend
- rate_flashcard(rating=None, answer=None) -> AttemptResult
- tick(active_ms, draft=None) -> Tick  saves active time and draft; break reminder

Pure pieces (no storage): deck.flashcards (the day's flashcards), planner.place_flashcards,
guards.guard_timing (TIME-4/5). The pieces of the earlier problem engine (share, triage,
order, planner.build_plan, snapshot, estimate, daylog) go with wave 2's removals.
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
    ExamLine,
    FindErrorView,
    FlagResult,
    Forecast,
    PartAnswer,
    ProblemView,
    Progress,
    Reason,
    SittingView,
    SolutionView,
    StartRequest,
    SubmitRequest,
    Summary,
    TestResult,
    TextbookView,
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
    "ExamLine",
    "FindErrorView",
    "FlagResult",
    "Forecast",
    "Guarded",
    "Mode",
    "PartAnswer",
    "Plan",
    "PlanItem",
    "ProblemView",
    "Progress",
    "QueueError",
    "QueueSettings",
    "Reason",
    "ReasonTag",
    "Share",
    "SittingView",
    "Snapshot",
    "SolutionView",
    "StartRequest",
    "StudyService",
    "SubmitRequest",
    "Summary",
    "TestResult",
    "TextbookView",
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
