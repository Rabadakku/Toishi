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
    mode: Mode = "daily"
    untimed: bool | None = None  # None: the profile's default (session.untimed_default)
    count: int | None = None  # focused, extra practice, practice test size
    section_id: str | None = None  # focused practice on a section ...
    skill_id: str | None = None  # ... or one skill ...
    weak_spots: bool = False  # ... or the current weak spots
    exam_id: int | None = None  # practice test
    timed: bool = False  # practice test at exam pace

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> StartRequest:
        data = data or {}
        return cls(
            mode=data.get("mode", "daily"),
            untimed=data.get("untimed"),
            count=data.get("count"),
            section_id=data.get("section_id"),
            skill_id=data.get("skill_id"),
            weak_spots=bool(data.get("weak_spots", False)),
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
    hint_count: int
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
class ProblemView:
    item_key: str
    kind: Literal["problem", "example", "flashcard"]
    card: CardView
    reason: Reason
    attempts_allowed: int
    tries_used: int
    hints_shown: tuple[str, ...] = ()
    draft: str | None = None
    active_ms: int = 0  # active time already counted (resume)
    target_ms: int | None = None  # shown only after submitting
    untimed: bool = False
    practice_test: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PartVerdictView:
    part: str | None
    status: str  # correct, incorrect, invalid, undecidable, unsupported
    read_as: str | None = None
    message: str = ""
    feedback: str | None = None
    wrong_step: int | None = None  # the matched known wrong answer's @step (picker preselect)
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
    needs_diagnosis: bool  # show "What went wrong?"
    confident_error: bool
    can_mark_too_easy: bool
    textbook_ref: str | None = None
    rubric: tuple[str, ...] = ()  # self-graded: the checklist to tick
    shown_work: tuple[StepView, ...] = ()  # find-error: the work beside the correct solution
    preselect_step: int | None = None  # "What went wrong?": the matched wrong answer's step


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
    item_key: str
    outcome: Literal["retry", "correct", "incorrect", "invalid", "self-grade", "recorded"]
    verdicts: tuple[PartVerdictView, ...] = ()
    message: str = ""
    solution: SolutionView | None = None
    tries_used: int = 0
    attempts_allowed: int = 1
    rating: int | None = None  # flashcards: the rating recorded
    break_due: bool = False
    find_error: FindErrorView | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class HintReveal:
    item_key: str
    index: int  # 1-based
    total: int
    text: str
    rating_effect: Literal["hard", "again"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Diagnosis:
    item_key: str
    choice: str
    follow_up: str  # one sentence: what happens next
    rating: int | None  # the rating the answer was recorded with
    slip_accepted: bool = False
    checks: tuple[str, ...] = ()  # names of skills a check was planned on


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
    practice_test: bool  # ENG-8: offered in the final 14 days


@dataclass(frozen=True, slots=True, kw_only=True)
class Proposal:
    kind: Literal["overload", "backlog"]
    message: str
    options: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalPreview:
    """I2: what a goal change does to the queue. A goal that raises retention moves live
    due dates earlier; the skills it makes due are spread over the next days."""

    newly_due: int  # skills whose due date moves to today or earlier
    message: str  # "This makes 12 skills due."
    per_day: Mapping[str, int] = field(default_factory=dict)  # ISO day -> skills spread there


@dataclass(frozen=True, slots=True, kw_only=True)
class TodayView:
    """Home: "Today: 20 problems, about 55 minutes", split by course. Never an overdue count."""

    day: str
    problems: int
    minutes: int
    flashcards: int
    courses: tuple[CourseLine, ...]
    exams: tuple[ExamLine, ...]
    proposals: tuple[Proposal, ...] = ()
    session_open: bool = False
    done_today: bool = False
    vacation: bool = False
    extra_practice_available: bool = False
    flashcards_to_rewrite: int = 0  # I5: leech flashcards, not shown until rewritten


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
    # Learning-phase problems ready later today (a new skill's block goes on, ENG-2): the
    # summary says so instead of only "Tomorrow: ...".
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
    message: str = ""
    break_due: bool = False
    lighter: bool = False
    mode: str = "daily"


@dataclass(frozen=True, slots=True, kw_only=True)
class Tick:
    saved: bool
    active_ms: int
    break_due: bool = False
