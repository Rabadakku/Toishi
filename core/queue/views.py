"""Requests and responses of the queue API: plain dataclasses that turn into JSON-ready
dicts with `to_dict` (and requests build from dicts with `from_dict`), for the JS bridge.

Times are milliseconds; the page formats them. Skill names appear only in views shown
after an answer (solution, summary), never in a problem view (Study screen rule 7).
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from core.queue.guards import TimingReport
from core.queue.items import Mode

type Source = Literal["text", "mathlive"]
SelfGrade = Literal["matched", "minor-slip", "missed"]


def to_dict(obj: Any) -> dict[str, Any]:
    """A dataclass response as a JSON-ready dict."""
    return asdict(obj)


# ---------------------------------------------------------------- requests


@dataclass(frozen=True, slots=True, kw_only=True)
class StartRequest:
    """Wave 2 has three modes: the daily plan, extra practice (tomorrow's planned problems)
    and practice tests. Focused, weak-spot and lighter sessions are gone; a request that still
    names their fields is read without them."""

    mode: Mode = "daily"
    untimed: bool | None = None  # None: the profile's default (session.untimed_default)
    count: int | None = None  # extra practice, practice test size
    exam_id: int | None = None  # practice test
    timed: bool = False  # practice test at exam pace

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> StartRequest:
        data = data or {}
        return cls(
            mode=data.get("mode", "daily"),
            untimed=data.get("untimed"),
            count=data.get("count"),
            exam_id=data.get("exam_id"),
            timed=bool(data.get("timed", False)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PartAnswer:
    part: str | None = None  # part label; None for a single-box card
    value: str = ""
    source: Source = "text"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PartAnswer:
        return cls(
            part=data.get("part", data.get("part_id")),
            value=str(data.get("value", "")),
            source="mathlive"
            if data.get("source", data.get("format")) in ("mathlive", "latex")
            else "text",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitRequest:
    answers: tuple[PartAnswer, ...] = ()
    confidence: Literal["sure", "unsure"] = "sure"
    guessed: bool = False
    self_grade: SelfGrade | None = None  # self-graded cards and undecidable answers
    rubric_ticked: int | None = None
    timing: TimingReport = field(default_factory=TimingReport)
    item_key: str | None = None  # optional guard against a stale page
    error_step: int | None = None  # find-the-error: the step picked as wrong
    reason: int | None = None  # find-the-error: index of the reason picked (### Reasons)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SubmitRequest:
        step = data.get("error_step", data.get("wrong_step"))
        reason = data.get("reason")
        return cls(
            error_step=None if step is None else int(step),
            reason=None if reason is None else int(reason),
            answers=tuple(PartAnswer.from_dict(a) for a in data.get("answers", ())),
            confidence="unsure" if data.get("confidence") == "unsure" else "sure",
            guessed=bool(data.get("guessed", False)),
            self_grade=data.get("self_grade"),
            rubric_ticked=data.get("rubric_ticked"),
            timing=TimingReport.from_dict(data.get("timing")),
            item_key=data.get("item_key", data.get("problem_id")),
        )


# ---------------------------------------------------------------- problem turn


@dataclass(frozen=True, slots=True, kw_only=True)
class Reason:
    tag: str  # review, relearn, new-skill, check, exam-prep, redo, stretch
    label: str  # "Review", "Check (after a miss on Chain rule)", ...
    why: str  # the "Why is this here?" sentence


@dataclass(frozen=True, slots=True, kw_only=True)
class ChoiceView:
    index: int
    text_md: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PartView:
    label: str | None
    prompt_md: str | None
    answer_type: str
    choices: tuple[ChoiceView, ...] = ()
    multiple: bool = False  # a choice part with several right options: select all that apply


@dataclass(frozen=True, slots=True, kw_only=True)
class StepView:
    number: int
    skill_id: str | None
    skill_name: str | None
    label: str
    body_md: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CardView:
    id: str
    rev: int
    kind: str  # problem, example, flashcard, cloze, find-error, method
    prompt_md: str
    parts: tuple[PartView, ...]
    calculator: bool
    angles: str
    plot: str | None = None
    self_graded: bool = False
    back_md: str | None = None  # examples show their worked solution at once
    solution_md: str | None = None
    # find-error: another student's numbered steps (no skill names), the reasons to choose
    # from, and the wrong step when the highlighted version is used ("Step 3 is wrong. Why?")
    shown_work: tuple[StepView, ...] = ()
    reasons: tuple[ChoiceView, ...] = ()
    error_step: int | None = None
    cloze: int | None = None  # cloze: the blank number asked (c1 -> 1)
    type_answer: bool = False  # a flashcard with an answer: type it, graded automatically


@dataclass(frozen=True, slots=True, kw_only=True)
class Progress:
    position: int  # 1-based number of the problem on screen ("7 of 20")
    total: int
    answered: int
    correct: int


@dataclass(frozen=True, slots=True, kw_only=True)
class TextbookView:
    """The textbook line under a problem: "OpenStax Calculus Volume 1" "§4.1"."""

    book: str
    section: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SittingView:
    """A certification sitting's item: closed book, its skill block's time limit (the sum of
    that skill's problems' standard times) and the active time spent on that block so far.
    Nothing is cut off at the limit."""

    id: str
    index: int  # 1-based position of this problem in the sitting
    total: int  # problems in the sitting
    time_limit_ms: int
    block_elapsed_ms: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ProblemView:
    item_key: str
    kind: Literal["problem", "example", "flashcard"]
    card: CardView
    reason: Reason
    attempts_allowed: int  # tries per answer box; 0: no limit (problems are retried freely)
    tries_used: int
    draft: str | None = None
    active_ms: int = 0  # active time already counted (resume)
    target_ms: int | None = None  # shown only after submitting
    untimed: bool = False
    practice_test: bool = False
    # Wave 2: the planner's role and reason code ("band", "ladder:smaller", ...), the
    # textbook pointer, and the sitting this problem belongs to.
    role: str | None = None
    plan_reason: str | None = None
    textbook: TextbookView | None = None
    sitting: SittingView | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PartVerdictView:
    part: str | None
    status: str  # correct, incorrect, invalid, undecidable, unsupported
    read_as: str | None = None
    message: str = ""
    feedback: str | None = None
    # The matched known wrong answer's @step: shown with the solution only (None in a retry)
    wrong_step: int | None = None
    final: bool = True  # multi-part: this part's verdict is final (right, or out of tries)
    tries_used: int = 0  # multi-part: tries used on this part


@dataclass(frozen=True, slots=True, kw_only=True)
class SolutionView:
    skill_id: str | None
    skill_name: str | None
    answer_md: str | None
    solution_md: str | None
    steps: tuple[StepView, ...]
    alternative_md: str | None
    active_ms: int | None
    target_ms: int | None
    time_text: str | None  # "3:40 · target 4:00"
    confident_error: bool
    can_mark_too_easy: bool
    textbook_ref: str | None = None
    rubric: tuple[str, ...] = ()  # self-graded: the checklist to tick
    shown_work: tuple[StepView, ...] = ()  # find-error: the work beside the correct solution


@dataclass(frozen=True, slots=True, kw_only=True)
class FindErrorView:
    """How a find-the-error answer was graded: the step, the reason and the value."""

    error_step: int | None  # the wrong step
    right_reason: int | None  # index of the right reason
    step_ok: bool
    reason_ok: bool
    value_ok: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class AttemptResult:
    """A submission's result. After a wrong try (outcome retry) it carries the verdict only:
    no checker message, no known-wrong-answer feedback and no step, which the student sees
    only with the solution (a give-up, or Show solution after a wrong first try)."""

    item_key: str
    outcome: Literal["retry", "correct", "incorrect", "invalid", "self-grade", "recorded"]
    verdicts: tuple[PartVerdictView, ...] = ()
    message: str = ""
    solution: SolutionView | None = None
    tries_used: int = 0
    attempts_allowed: int = 1  # 0: no limit
    rating: int | None = None  # flashcards: the rating recorded
    break_due: bool = False
    find_error: FindErrorView | None = None
    can_retry: bool = False  # a wrong try: the problem stays open (Retry or Give up)
    first_try_counted: bool = False  # this submission was the problem's first try


@dataclass(frozen=True, slots=True, kw_only=True)
class FlagResult:
    ok: bool
    message: str
    attempt_counts: bool = True


# ---------------------------------------------------------------- plans, summaries


@dataclass(frozen=True, slots=True, kw_only=True)
class CourseLine:
    course_id: str
    title: str
    problems: int
    minutes: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Forecast:
    day: str
    problems: int
    minutes: int
    courses: tuple[CourseLine, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ExamLine:
    exam_id: int | None
    name: str
    course_id: str | None
    days_left: int
    practice_test: bool  # ENG-8: offered in the final 21 days


@dataclass(frozen=True, slots=True, kw_only=True)
class SittingLine:
    """A sitting planned today and its skills (names)."""

    id: str
    skills: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TodayView:
    """Home: today's items and minutes by course and by role, what keeping pace costs, the
    skills behind or set aside, today's sittings and the planner's notes. Never an overdue
    count. Skill lists hold names, not ids."""

    day: str
    problems: int
    minutes: int
    flashcards: int
    courses: tuple[CourseLine, ...]
    exams: tuple[ExamLine, ...]
    session_open: bool = False
    done_today: bool = False
    extra_practice_available: bool = False  # tomorrow's planned problems, to do early
    flashcards_to_rewrite: int = 0  # I5: leech flashcards, not shown until rewritten
    by_role: Mapping[str, int] = field(default_factory=dict)
    hours_to_keep_pace: float | None = None  # per week
    hours_basis: Literal["history", "standard", "none"] = "none"
    standard_hours: float | None = None  # the courses' reference hours per week
    behind: tuple[str, ...] = ()
    set_aside: tuple[str, ...] = ()
    sittings: tuple[SittingLine, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class MissLine:
    item_key: str
    card_id: str | None
    skill_id: str | None
    skill_name: str
    tag: str
    label: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TestLine:
    item_key: str
    card_id: str | None
    skill_name: str
    answered: bool
    correct: bool
    your_answer: str | None
    rating: int | None = None  # the review it counted as (None: not graded)


@dataclass(frozen=True, slots=True, kw_only=True)
class TestResult:
    exam_id: int | None
    answered: int
    correct: int
    total: int
    timed: bool
    time_up: bool
    lines: tuple[TestLine, ...] = ()
    unanswered: Literal["again", "skip"] = "skip"  # how unanswered problems counted
    limit_ms: int | None = None  # the time allowed when timed


@dataclass(frozen=True, slots=True, kw_only=True)
class Summary:
    mode: str
    problems: int
    correct: int
    missed: int
    active_ms: int
    misses: tuple[MissLine, ...]
    learned: tuple[str, ...]
    flashcards: int
    forecast: Forecast
    extra_practice_available: bool
    practice_tests: tuple[ExamLine, ...] = ()
    test: TestResult | None = None
    # Problems today's plan still holds after this session (it ended before the plan was
    # done): the summary says so as well as "Tomorrow: ...".
    ready_today: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class Turn:
    """What the study screen shows next: a problem (maybe already answered, after a resume),
    the end-of-session summary, or nothing to do."""

    type: Literal["problem", "summary", "empty"]
    session_id: int | None = None
    problem: ProblemView | None = None
    progress: Progress | None = None
    result: AttemptResult | None = None  # the verdict screen, when resuming after an answer
    summary: Summary | None = None
    message: str = ""  # e.g. the set-aside notice after the answer that set a skill aside
    break_due: bool = False
    mode: str = "daily"


@dataclass(frozen=True, slots=True, kw_only=True)
class Tick:
    saved: bool
    active_ms: int
    break_due: bool = False
