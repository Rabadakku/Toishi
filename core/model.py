"""Shared typed records for Toishi.

Content records (what ships in packs, or what the student writes) mirror
docs/card-format.md; user-side records mirror the tables of a profile's user.db.
They hold data only: validation here checks shapes (enums, ranges, id syntax),
never business rules. Times are UTC epoch milliseconds (`*_at` fields and `at`);
durations are milliseconds (`*_ms`); study days are ISO dates ("2026-11-01").
"""

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal, get_args

type JsonObject = dict[str, Any]

CardKind = Literal["problem", "example", "flashcard", "cloze", "find-error", "method"]
AnswerType = Literal[
    "number",
    "expression",
    "equation",
    "antiderivative",
    "set",
    "list",
    "interval",
    "point",
    "vector",
    "matrix",
    "choice",
    "truefalse",
    "text",
    "quantity",
    "self",
]
Angles = Literal["radians", "degrees"]
CardStatus = Literal["active", "retired"]
StepSection = Literal["solution", "alternative", "shown-work"]
ChoiceRole = Literal["choice", "reason"]
EdgeKind = Literal["requires", "encompasses", "confusable"]
SectionStateName = Literal["off", "learning", "covered", "solid"]
GoalName = Literal["A", "B", "Keep", "custom"]
LevelName = Literal["learning", "learned", "exam", "mastered"]
Verdict = Literal["correct", "incorrect", "gave-up", "self", "undecided", "shown"]
Confidence = Literal["sure", "unsure"]
ErrorChoice = Literal["step", "setup", "slip", "misread", "other-method", "cant-tell"]
TargetKind = Literal["skill", "flashcard"]
CreditMode = Literal["shadow", "on"]
VoidReason = Literal["undo", "dispute", "report", "recompute"]
CheckKind = Literal["step", "prerequisite", "cued-twin", "diagnostic"]
CheckStatus = Literal["pending", "passed", "failed", "cancelled"]
WeakSpotStatus = Literal["open", "confirmed", "cleared"]
DiagnosticStatus = Literal["pending", "active", "confirmed", "cleared", "cancelled"]
DisputeStatus = Literal["open", "upheld", "rejected"]
ReportStatus = Literal["open", "fixed", "dismissed"]
# v3 (wave 2): the planner's roles and milestones as attempts log them (core.plan's types,
# repeated here so core.model stays free of imports), and the learner's parameter sources.
PlanRole = Literal[
    "new", "growth", "maintenance", "check", "practice-test", "focused", "sitting", "placement"
]
MilestoneName = Literal["M1", "M2", "M3", "keep"]
GrowthBand = Literal["standard", "hard"]
ParamsSource = Literal["prior", "refit", "reset"]
LADDER_RUNGS = (0, 1, 2)  # the stuck ladder's item rungs (3, set aside, serves nothing)

# In a GradedAnswer, a PendingCheck's attempt_id or resolved_by may be THIS_ATTEMPT:
# storage replaces it with the id of the attempt being recorded.
THIS_ATTEMPT = -1

FSRS_STATES = (1, 2, 3)  # py-fsrs State: Learning, Review, Relearning. None = not started.
RATINGS = (1, 2, 3, 4)  # Again, Hard, Good, Easy
TIERS = (1, 2, 3, 4, 5)  # Drill, Standard, Exam, Challenge, Elite
DEFAULT_MINUTES_PER_STEP = 1.5  # standard times (student-model spec 2.4); packs set their own
ENCOMPASS_WEIGHTS = (0.25, 0.5, 1.0)
FSRS_STABILITY = (0.001, 36_500.0)  # days (fsrs-rs S_MIN, S_MAX)
FSRS_DIFFICULTY = (1.0, 10.0)

_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------- shape checks


class ShapeError(ValueError):
    """A record (or setting) does not have a valid shape: bad enum, range or id."""


def _one_of(name: str, value: object, allowed: Iterable[object]) -> None:
    options = tuple(allowed)
    if value not in options:
        raise ShapeError(f"{name} must be one of {options}, got {value!r}")


def _content_id(name: str, value: str | None) -> None:
    if value is not None and not _ID.fullmatch(value):
        raise ShapeError(f"{name} {value!r}: use lowercase letters, digits, '.', '-' and '_'")


def _ids(name: str, values: Iterable[str]) -> None:
    for value in values:
        _content_id(name, value)


def _nonneg(name: str, value: int | float | None) -> None:
    if value is not None and value < 0:
        raise ShapeError(f"{name} must be >= 0, got {value!r}")


def _positive(name: str, value: float | None) -> None:
    if value is not None and not (math.isfinite(value) and value > 0):
        raise ShapeError(f"{name} must be a positive number, got {value!r}")


def _unit_interval(name: str, value: float | None) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ShapeError(f"{name} must be within [0, 1], got {value!r}")


def _fsrs_memory(stability: float | None, difficulty: float | None) -> None:
    """I6: stability finite within [0.001, 36500] days, difficulty finite within [1, 10]."""
    if stability is not None and not (
        math.isfinite(stability) and FSRS_STABILITY[0] <= stability <= FSRS_STABILITY[1]
    ):
        raise ShapeError(f"stability must be finite within {FSRS_STABILITY}, got {stability!r}")
    if difficulty is not None and not (
        math.isfinite(difficulty) and FSRS_DIFFICULTY[0] <= difficulty <= FSRS_DIFFICULTY[1]
    ):
        raise ShapeError(f"difficulty must be finite within {FSRS_DIFFICULTY}, got {difficulty!r}")


def _nonempty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ShapeError(f"{name} must not be empty")


def check_study_day(name: str, value: str | None) -> None:
    if value is None:
        return
    try:
        valid = bool(_DAY.fullmatch(value)) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        valid = False
    if not valid:
        raise ShapeError(f"{name} must be an ISO date like 2026-11-01, got {value!r}")


# ---------------------------------------------------------------- content: course tree


@dataclass(frozen=True, slots=True, kw_only=True)
class Course:
    id: str
    title: str
    ord: int = 0

    def __post_init__(self) -> None:
        _nonempty("course id", self.id)


@dataclass(frozen=True, slots=True, kw_only=True)
class Unit:
    id: str
    course_id: str
    title: str
    ord: int = 0

    def __post_init__(self) -> None:
        _nonempty("unit id", self.id)


@dataclass(frozen=True, slots=True, kw_only=True)
class Section:
    id: str
    unit_id: str
    title: str
    ord: int = 0
    textbook_ref: str | None = None

    def __post_init__(self) -> None:
        _nonempty("section id", self.id)


# ---------------------------------------------------------------- content: skills


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillEdge:
    """requires: skill_id needs other_id first. encompasses: skill_id practices other_id
    (weight 0.25, 0.5 or 1). confusable: easily mixed up (stored once per direction given)."""

    kind: EdgeKind
    skill_id: str
    other_id: str
    weight: float | None = None

    def __post_init__(self) -> None:
        _one_of("edge kind", self.kind, get_args(EdgeKind))
        _ids("skill id", (self.skill_id, self.other_id))
        if self.skill_id == self.other_id:
            raise ShapeError(f"skill {self.skill_id} cannot point at itself")
        if self.kind == "encompasses":
            _one_of("encompass weight", self.weight, ENCOMPASS_WEIGHTS)
        elif self.weight is not None:
            raise ShapeError(f"{self.kind} edges carry no weight")


@dataclass(frozen=True, slots=True, kw_only=True)
class Skill:
    id: str
    name: str
    deck: str | None = None  # Course::Unit::Section
    section_id: str | None = None
    textbook_ref: str | None = None
    method_choice: bool = False  # ENG-16 method-choice skill
    core: bool = False  # goal presets: "Mastered for core skills"
    exam_tier: int | None = None  # ENG-10 Exam-level is judged at this tier
    requires: tuple[str, ...] = ()
    encompasses: tuple[tuple[str, float], ...] = ()
    confusable: tuple[str, ...] = ()
    notes_md: str | None = None

    def __post_init__(self) -> None:
        _content_id("skill id", self.id)
        _nonempty("skill name", self.name)
        if self.exam_tier is not None:
            _one_of("exam tier", self.exam_tier, TIERS)
        self.edges()  # validates every edge

    def edges(self) -> tuple[SkillEdge, ...]:
        out = [SkillEdge(kind="requires", skill_id=self.id, other_id=o) for o in self.requires]
        out += [
            SkillEdge(kind="encompasses", skill_id=self.id, other_id=o, weight=w)
            for o, w in self.encompasses
        ]
        out += [SkillEdge(kind="confusable", skill_id=self.id, other_id=o) for o in self.confusable]
        return tuple(out)


# ---------------------------------------------------------------- content: cards


@dataclass(frozen=True, slots=True, kw_only=True)
class SolutionStep:
    """One numbered step of a step-tagged solution or of find-error shown work."""

    number: int
    skill_id: str | None
    label: str
    body_md: str = ""

    def __post_init__(self) -> None:
        _nonneg("step number", self.number)
        _content_id("step skill", self.skill_id)


@dataclass(frozen=True, slots=True, kw_only=True)
class Choice:
    """A `- [x]` / `- [ ]` line of ### Choices or ### Reasons."""

    text_md: str
    correct: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class WrongAnswer:
    """`wrong: answer => feedback @step`."""

    answer: str
    feedback: str | None = None
    step: int | None = None

    def __post_init__(self) -> None:
        _nonempty("wrong answer", self.answer)
        _nonneg("wrong answer step", self.step)


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckerOptions:
    """Checker option key lines, kept as the literal text of the card file."""

    vars: str | None = None
    domain: str | None = None
    tolerance: str | None = None
    exact: str | None = None
    form: str | None = None
    endpoints: str | None = None
    require_constant: str | None = None
    units: str | None = None
    sig_figs: str | None = None
    domain_strict: str | None = None  # format 1.1: holes are wrong on this card


@dataclass(frozen=True, slots=True, kw_only=True)
class CardPart:
    label: str  # "a", "b", ...
    prompt_md: str
    answer_type: AnswerType = "self"
    answer: str | None = None
    checker: CheckerOptions = field(default_factory=CheckerOptions)
    skill_id: str | None = None
    choices: tuple[Choice, ...] = ()
    wrong: tuple[WrongAnswer, ...] = ()
    time_minutes: float | None = None  # `time:` the part's standard time (packs only)

    def __post_init__(self) -> None:
        _nonempty("part label", self.label)
        _one_of("part answer type", self.answer_type, get_args(AnswerType))
        _content_id("part skill", self.skill_id)
        _positive("part time", self.time_minutes)


@dataclass(frozen=True, slots=True, kw_only=True)
class Provenance:
    """PACK-4: where a card came from and what may be done with it."""

    source: str | None = None  # original, personal, or a citation
    source_url: str | None = None
    license: str | None = None
    creators: tuple[str, ...] = ()
    original_path: str | None = None
    original_commit: str | None = None
    modified: bool = False
    modification_note: str | None = None
    third_party: tuple[str, ...] = ()
    translation: str | None = None
    unofficial_solution: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class CardRevision:
    """PACK-2: a fix adds a revision; a changed key is noted."""

    card_id: str
    rev: int
    changed_at: int
    note: str = ""
    answer_changed: bool = False

    def __post_init__(self) -> None:
        _content_id("card id", self.card_id)
        if self.rev < 1:
            raise ShapeError("revisions start at 1")


@dataclass(frozen=True, slots=True, kw_only=True)
class Card:
    """Every field of docs/card-format.md. Only id plus a stem are needed for a valid shape."""

    id: str
    rev: int = 1
    kind: CardKind = "problem"
    skill_id: str | None = None
    uses: tuple[str, ...] = ()
    tier: int = 2
    time_minutes: float | None = None  # `time:` standard time (packs only); None: the default
    answer_type: AnswerType = "self"
    answer: str | None = None
    checker: CheckerOptions = field(default_factory=CheckerOptions)
    wrong: tuple[WrongAnswer, ...] = ()
    plot: str | None = None
    calculator: bool = False
    angles: Angles = "radians"
    cue_required: bool = False  # `cue: required`
    error_step: int | None = None  # find-error: wrong step in shown_work
    tagged: str | None = None  # e.g. "ai:model prompt-v3 0.86"
    deck: str | None = None
    section_id: str | None = None
    tags: tuple[str, ...] = ()
    # Sections
    question_md: str | None = None  # the uncued stem used in reviews
    cued_question_md: str | None = None  # ### Cued Question
    choices: tuple[Choice, ...] = ()
    shown_work: tuple[SolutionStep, ...] = ()
    reasons: tuple[Choice, ...] = ()
    parts: tuple[CardPart, ...] = ()
    hints: tuple[str, ...] = ()
    answer_md: str | None = None
    solution: tuple[SolutionStep, ...] = ()  # step-tagged
    solution_md: str | None = None  # untagged or original text
    rubric: tuple[str, ...] = ()
    alternative_solution: tuple[SolutionStep, ...] = ()
    alternative_solution_md: str | None = None
    front_md: str | None = None
    back_md: str | None = None
    text_md: str | None = None  # cloze
    extra_md: str | None = None
    notes_md: str | None = None
    # Variants expanded at build time (PACK-3)
    template_id: str | None = None
    seed: int | None = None
    params: str | None = None  # an instance's parameter set, "k = 3; m = 1/2" ("" for none)
    # Provenance and verification (PACK-4, PACK-5)
    provenance: Provenance = field(default_factory=Provenance)
    verified: str | None = None
    status: CardStatus = "active"

    def __post_init__(self) -> None:
        _content_id("card id", self.id)
        _content_id("skill id", self.skill_id)
        _ids("uses skill id", self.uses)
        if self.rev < 1:
            raise ShapeError("card revisions start at 1")
        _one_of("card kind", self.kind, get_args(CardKind))
        _one_of("tier", self.tier, TIERS)
        _positive("time", self.time_minutes)
        _one_of("answer type", self.answer_type, get_args(AnswerType))
        _one_of("angles", self.angles, get_args(Angles))
        _one_of("card status", self.status, get_args(CardStatus))
        _nonneg("error step", self.error_step)
        for name, steps in (
            ("solution", self.solution),
            ("alternative solution", self.alternative_solution),
            ("shown work", self.shown_work),
        ):
            numbers = [s.number for s in steps]
            if len(set(numbers)) != len(numbers):
                raise ShapeError(f"card {self.id}: duplicate step numbers in {name}")
        labels = [p.label for p in self.parts]
        if len(set(labels)) != len(labels):
            raise ShapeError(f"card {self.id}: duplicate part labels")
        if not any((self.question_md, self.front_md, self.text_md, self.parts)):
            raise ShapeError(f"card {self.id}: needs a question, front, cloze text or parts")
        if self.params is not None and self.template_id is None:
            raise ShapeError(f"card {self.id}: only template instances have parameters")

    @property
    def retired(self) -> bool:
        return self.status == "retired"


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateSource:
    """The source text of one of the student's own templates (its block as written, with
    the file's defaults made explicit): what export writes and the editor opens. Its
    instances are cards whose template_id is this id."""

    id: str
    source_md: str
    updated_at: int = 0

    def __post_init__(self) -> None:
        _content_id("template id", self.id)
        _nonempty("template source", self.source_md)


@dataclass(frozen=True, slots=True, kw_only=True)
class CardMedia:
    """One image reference of an own card (`ref`, as written in its text) and the stored
    file it shows: a content-addressed name in the profile's media folder."""

    card_id: str
    ref: str
    file: str

    def __post_init__(self) -> None:
        _nonempty("card id", self.card_id)
        _nonempty("media reference", self.ref)
        _nonempty("media file", self.file)


@dataclass(frozen=True, slots=True, kw_only=True)
class CardRef:
    """The light view of a card the queue picks from."""

    id: str
    rev: int
    kind: CardKind
    skill_id: str | None
    tier: int
    template_id: str | None
    seed: int | None
    status: CardStatus
    cue_required: bool
    has_cued_question: bool
    source: str  # pack id, or "user"
    section_id: str | None = None  # the card's own section (a flashcard may have no skill)


@dataclass(frozen=True, slots=True, kw_only=True)
class PackInfo:
    id: str
    title: str
    version: str
    format: int = 1
    built_at: int = 0
    content_hash: str = ""
    schema_version: int = 0

    def __post_init__(self) -> None:
        _content_id("pack id", self.id)


@dataclass(frozen=True, slots=True, kw_only=True)
class PackPaceSection:
    """A `## Section <deck path>` block of a pack's skills file: the standard class hours a
    top school spends on that section (student-model spec 4.1)."""

    deck: str  # Course::Unit::Section
    hours: float

    def __post_init__(self) -> None:
        _nonempty("pace section", self.deck)
        _positive("section hours", self.hours)


@dataclass(frozen=True, slots=True, kw_only=True)
class PackPace:
    """A pack's pace standard as its skills file sets it (student-model spec 2.4 and 4.1):
    minutes per solution step for standard times, the weekly class hours (None: not given),
    and the sections in the order the course covers them. A pack that sets none has the
    defaults. The planner builds its own PaceStandard (core.plan) from this record."""

    minutes_per_step: float = DEFAULT_MINUTES_PER_STEP
    weekly_hours: float | None = None
    sections: tuple[PackPaceSection, ...] = ()

    def __post_init__(self) -> None:
        _positive("minutes per step", self.minutes_per_step)
        _positive("weekly hours", self.weekly_hours)
        ids = [s.deck for s in self.sections]
        if len(set(ids)) != len(ids):
            raise ShapeError("a pace standard lists a section twice")


@dataclass(frozen=True, slots=True, kw_only=True)
class Media:
    name: str
    data: bytes

    def __post_init__(self) -> None:
        _nonempty("media name", self.name)
        if self.name.startswith("/") or ".." in self.name.split("/"):
            raise ShapeError(f"media name {self.name!r} must be a relative path")


# ---------------------------------------------------------------- user side: plans and goals


@dataclass(frozen=True, slots=True, kw_only=True)
class CourseGoal:
    course_id: str
    goal: GoalName = "A"
    custom_retention: float | None = None  # only for goal "custom": 0.80..0.95
    goal_date: date | None = None
    starts_on: date | None = None  # LIB-8: when a course taken next begins
    updated_at: int = 0

    def __post_init__(self) -> None:
        _nonempty("course id", self.course_id)
        _one_of("goal", self.goal, get_args(GoalName))
        if self.goal == "custom":
            if self.custom_retention is None or not 0.80 <= self.custom_retention <= 0.95:
                raise ShapeError("a custom goal needs a retention from 0.80 to 0.95")
        elif self.custom_retention is not None:
            raise ShapeError("custom_retention is only for the custom goal")


@dataclass(frozen=True, slots=True, kw_only=True)
class Exam:
    id: int | None = None
    course_id: str | None = None
    name: str
    at: int  # UTC ms of the exam start
    minutes: int | None = None
    problems: int | None = None
    sections: tuple[str, ...] = ()
    target_recall: float | None = None
    created_at: int = 0

    def __post_init__(self) -> None:
        _nonempty("exam name", self.name)
        _nonneg("exam minutes", self.minutes)
        _nonneg("exam problems", self.problems)
        _unit_interval("target recall", self.target_recall)


@dataclass(frozen=True, slots=True, kw_only=True)
class CourseSetup:
    """A course's setup for the planner (v3, table course_settings; student-model design
    4.1): the pace anchor (a start date, or "my class is at section X today"), the pace
    factor, the targets, the end date and the growth band. Without a start or an alignment
    the course has no schedule."""

    course_id: str
    start: date | None = None
    aligned_deck: str | None = None  # "my class is at this section ..."
    aligned_day: date | None = None  # "... today"
    pace_factor: float = 1.0
    accuracy_target: float = 0.90
    target_tier: int = 4
    end_day: date | None = None  # None: self-study, never drops to Keep
    keep_target: float = 0.80
    keep_tier: int = 3
    growth_band: GrowthBand = "standard"  # standard 0.70-0.90, hard 0.50-0.75
    updated_at: int = 0

    def __post_init__(self) -> None:
        _nonempty("course id", self.course_id)
        if (self.aligned_deck is None) != (self.aligned_day is None):
            raise ShapeError("an alignment needs both its section and its day")
        if self.aligned_deck is not None:
            _nonempty("aligned section", self.aligned_deck)
        if not (math.isfinite(self.pace_factor) and 0.75 <= self.pace_factor <= 1.5):
            raise ShapeError(f"pace factor must be within [0.75, 1.5], got {self.pace_factor!r}")
        for name, value in (
            ("accuracy target", self.accuracy_target),
            ("keep target", self.keep_target),
        ):
            if not (math.isfinite(value) and 0.0 < value < 1.0):
                raise ShapeError(f"{name} must be between 0 and 1, got {value!r}")
        _one_of("target tier", self.target_tier, TIERS)
        _one_of("keep tier", self.keep_tier, TIERS)
        _one_of("growth band", self.growth_band, get_args(GrowthBand))


@dataclass(frozen=True, slots=True, kw_only=True)
class LearnerParams:
    """One version of the student model's shared parameters (v3, table learner_params;
    design 3.6): the prior, a refit (adopted or not, with its report) or a reset. `params`
    is the JSON of core.learner.SharedParams; exactly one version is current."""

    version: str
    created_at: int = 0
    params: JsonObject = field(default_factory=dict)
    source: ParamsSource = "prior"
    report: JsonObject | None = None
    current: bool = False

    def __post_init__(self) -> None:
        _nonempty("parameter version", self.version)
        _one_of("parameter source", self.source, get_args(ParamsSource))


@dataclass(frozen=True, slots=True, kw_only=True)
class SectionState:
    section_id: str
    state: SectionStateName
    changed_at: int = 0

    def __post_init__(self) -> None:
        _one_of("section state", self.state, get_args(SectionStateName))


# ---------------------------------------------------------------- user side: memory state


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillState:
    """Everything the engine keeps per skill. Storage never computes these."""

    skill_id: str
    fsrs_state: int | None = None
    fsrs_step: int | None = None
    stability: float | None = None
    difficulty: float | None = None
    due_at: int | None = None
    last_review_at: int | None = None
    reps: int = 0
    lapses: int = 0
    leech: bool = False
    leech_at: int | None = None
    introduced_at: int | None = None
    learning_streak: int = 0
    learning_count: int = 0
    level: LevelName | None = None
    level_at: int | None = None
    level_evidence: JsonObject = field(default_factory=dict)
    shaky: bool = False
    shaky_reviews: int = 0
    learned_at: int | None = None
    mastered_at: int | None = None
    elo_theta: float = 0.0
    elo_n: int = 0
    updated_at: int = 0

    def __post_init__(self) -> None:
        _content_id("skill id", self.skill_id)
        if self.fsrs_state is not None:
            _one_of("fsrs state", self.fsrs_state, FSRS_STATES)
        if self.level is not None:
            _one_of("level", self.level, get_args(LevelName))
        for name in ("reps", "lapses", "learning_streak", "learning_count", "elo_n"):
            _nonneg(name, getattr(self, name))
        _fsrs_memory(self.stability, self.difficulty)


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillTierState:
    """Per skill and tier: speed baseline (TIME-5, ENG-14) and target time (ENG-13)."""

    skill_id: str
    tier: int
    target_ms: int | None = None
    target_at: int | None = None
    baseline_median_ms: int | None = None
    baseline_n: int = 0
    first_correct_ms: tuple[int, ...] = ()
    updated_at: int = 0

    def __post_init__(self) -> None:
        _one_of("tier", self.tier, TIERS)
        _nonneg("target", self.target_ms)


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillShadow:
    """Partial credit in shadow mode: what the stability would be with credit applied."""

    skill_id: str
    credited_stability: float | None = None
    updated_at: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class FlashcardState:
    card_id: str
    ord: int = 0  # cloze blank number; 0 for flashcards
    fsrs_state: int | None = None
    fsrs_step: int | None = None
    stability: float | None = None
    difficulty: float | None = None
    due_at: int | None = None
    last_review_at: int | None = None
    reps: int = 0
    lapses: int = 0
    leech: bool = False
    updated_at: int = 0

    def __post_init__(self) -> None:
        if self.fsrs_state is not None:
            _one_of("fsrs state", self.fsrs_state, FSRS_STATES)
        _fsrs_memory(self.stability, self.difficulty)


@dataclass(frozen=True, slots=True, kw_only=True)
class CardUser:
    """Per-card study history the queue uses (redo, last seen)."""

    card_id: str
    last_seen_at: int | None = None
    times_seen: int = 0
    last_correct_at: int | None = None
    redo_due_at: int | None = None
    redo_guaranteed: bool = False
    updated_at: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class CardMark:
    """Student actions on a card: flag, suspend, hide (reported)."""

    card_id: str
    flagged: bool = False
    flag_note: str | None = None
    suspended: bool = False
    hidden: bool = False
    updated_at: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class PendingCheck:
    id: int | None = None
    created_at: int = 0
    attempt_id: int | None = None  # the miss that asked for it
    skill_id: str
    kind: CheckKind = "step"
    card_id: str | None = None
    after_items: int = 3
    not_before_at: int | None = None
    depth: int = 0
    status: CheckStatus = "pending"
    resolved_at: int | None = None
    resolved_by: int | None = None  # attempt id
    reason: str | None = None  # "Why is this here?"; None: composed when asked (v1 rows)

    def __post_init__(self) -> None:
        _one_of("check kind", self.kind, get_args(CheckKind))
        _one_of("check status", self.status, get_args(CheckStatus))


@dataclass(frozen=True, slots=True, kw_only=True)
class WeakSpot:
    id: int | None = None
    skill_id: str
    flagged_at: int
    study_day: str
    z: float
    evidence: float
    misses: int
    problems: int
    days: int
    status: WeakSpotStatus = "open"
    resolved_at: int | None = None

    def __post_init__(self) -> None:
        check_study_day("study day", self.study_day)
        _one_of("weak spot status", self.status, get_args(WeakSpotStatus))


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticSet:
    id: int | None = None
    skill_id: str
    weak_spot_id: int | None = None
    created_at: int
    status: DiagnosticStatus = "pending"
    card_ids: tuple[str, ...] = ()
    done: int = 0
    misses: int = 0
    resolved_at: int | None = None

    def __post_init__(self) -> None:
        _one_of("diagnostic status", self.status, get_args(DiagnosticStatus))


# ---------------------------------------------------------------- user side: logs


@dataclass(frozen=True, slots=True, kw_only=True)
class Attempt:
    """One graded submission (append-only). Storage fills id, at (if 0), study_day (if
    None), state_before, state_after and voided_by; everything else comes from the caller."""

    id: int | None = None
    at: int = 0
    study_day: str | None = None
    shown_at: int | None = None
    session_id: int | None = None
    presentation_id: str | None = None  # groups the tries of one showing of a problem
    card_id: str
    card_rev: int = 1
    pack_id: str | None = None  # None for the student's own cards
    card_kind: CardKind = "problem"
    skill_id: str | None = None
    part: str | None = None
    tier: int | None = None
    seed: int | None = None
    template_id: str | None = None
    reason_tag: str | None = None
    raw_input: str | None = None
    parsed: str | None = None
    verdict: Verdict
    attempt_number: int = 1
    final: bool = True
    hints_used: int = 0
    example_opened: bool = False
    confidence: Confidence = "sure"
    guessed: bool = False
    too_easy: bool = False
    active_ms: int | None = None
    solve_ms: int | None = None
    entry_ms: int | None = None
    raw_ms: int | None = None
    capped_ms: int | None = None
    pause_count: int = 0
    longest_pause_ms: int | None = None
    after_wake: bool = False
    untimed: bool = False
    rating: int | None = None
    explicit_rating: bool = False
    predicted_recall: float | None = None
    params_id: str | None = None
    rules_version: str | None = None
    triage_policy: str | None = None
    error_choice: ErrorChoice | None = None
    error_step: int | None = None
    matched_wrong: int | None = None
    check_of: int | None = None
    app_version: str | None = None
    extra: JsonObject = field(default_factory=dict)
    state_before: JsonObject | None = None
    state_after: JsonObject | None = None
    voided_by: int | None = None
    # v3 (wave 2): what the planner chose and the learner used. None for flashcards and
    # for attempts logged before v3.
    role: PlanRole | None = None
    milestone: MilestoneName | None = None
    missed: bool | None = None  # missed-milestone catch-up work
    plan_p: float | None = None  # the calibrated prediction when the item was chosen
    ladder: int | None = None  # the stuck-ladder rung, 0-2
    sitting: str | None = None  # the certification sitting's id
    learner_version: str | None = None  # the parameter version that made plan_p
    valid_minutes: float | None = None  # a correct first try's valid solving time

    def __post_init__(self) -> None:
        _nonempty("card id", self.card_id)
        check_study_day("study day", self.study_day)
        _one_of("verdict", self.verdict, get_args(Verdict))
        _one_of("confidence", self.confidence, get_args(Confidence))
        if self.tier is not None:
            _one_of("tier", self.tier, TIERS)
        if self.rating is not None:
            _one_of("rating", self.rating, RATINGS)
        if self.error_choice is not None:
            _one_of("error choice", self.error_choice, get_args(ErrorChoice))
        if self.attempt_number < 1:
            raise ShapeError("attempt_number starts at 1")
        _unit_interval("predicted recall", self.predicted_recall)
        for name in ("active_ms", "solve_ms", "entry_ms", "raw_ms", "capped_ms", "hints_used"):
            _nonneg(name, getattr(self, name))
        if self.role is not None:
            _one_of("role", self.role, get_args(PlanRole))
        if self.milestone is not None:
            _one_of("milestone", self.milestone, get_args(MilestoneName))
        _unit_interval("plan p", self.plan_p)
        if self.ladder is not None:
            _one_of("ladder rung", self.ladder, LADDER_RUNGS)
        _positive("valid minutes", self.valid_minutes)

    @property
    def strict_ok(self) -> bool | None:
        """The strict outcome label (ADR-0014): the final answer correct on the first try
        with no hint. Kept in `extra["strict_ok"]` (no schema change); None on attempts
        logged before it existed."""
        raw = self.extra.get("strict_ok")
        return None if raw is None else bool(raw)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviewEvent:
    """One FSRS event (append-only). Storage fills id, at, attempt_id and the FSRS
    state_before/state_after from the attempt's own snapshot of the target's row."""

    id: int | None = None
    at: int = 0
    attempt_id: int | None = None
    target_kind: TargetKind
    target_id: str
    target_ord: int = 0
    rating: int
    rules_version: str
    params_id: str | None = None
    retention: float | None = None
    predicted_recall: float | None = None
    state_before: JsonObject | None = None
    state_after: JsonObject | None = None
    voided_by: int | None = None

    def __post_init__(self) -> None:
        _one_of("target kind", self.target_kind, get_args(TargetKind))
        _one_of("rating", self.rating, RATINGS)
        _nonempty("rules version", self.rules_version)
        _unit_interval("retention", self.retention)
        _unit_interval("predicted recall", self.predicted_recall)


@dataclass(frozen=True, slots=True, kw_only=True)
class ImplicitCredit:
    """Partial credit from skill A to an encompassed skill B (append-only)."""

    id: int | None = None
    at: int = 0
    attempt_id: int | None = None
    from_skill: str
    to_skill: str
    weight: float
    mode: CreditMode
    stability_before: float | None = None
    stability_after: float | None = None
    voided_by: int | None = None

    def __post_init__(self) -> None:
        _one_of("credit mode", self.mode, get_args(CreditMode))
        if not 0.0 < self.weight <= 1.0:
            raise ShapeError("credit weight must be within (0, 1]")


@dataclass(frozen=True, slots=True, kw_only=True)
class AttemptVoid:
    id: int | None = None
    at: int = 0
    reason: VoidReason
    note: str | None = None
    state_before: JsonObject | None = None
    state_after: JsonObject | None = None

    def __post_init__(self) -> None:
        _one_of("void reason", self.reason, get_args(VoidReason))


@dataclass(frozen=True, slots=True, kw_only=True)
class Dispute:
    id: int | None = None
    attempt_id: int
    at: int = 0
    raw_input: str | None = None
    status: DisputeStatus = "open"
    resolved_at: int | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        _one_of("dispute status", self.status, get_args(DisputeStatus))


@dataclass(frozen=True, slots=True, kw_only=True)
class Report:
    id: int | None = None
    card_id: str
    card_rev: int = 1
    attempt_id: int | None = None
    at: int = 0
    reason: str = ""
    status: ReportStatus = "open"
    resolved_at: int | None = None

    def __post_init__(self) -> None:
        _one_of("report status", self.status, get_args(ReportStatus))


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportRecord:
    id: int | None = None
    at: int = 0
    file: str
    kind: str  # cards, skills, mepack, apkg, colpkg, anki-text, meprofile, ...
    summary: JsonObject = field(default_factory=dict)
    backup: str | None = None  # file name of the backup taken before it

    def __post_init__(self) -> None:
        _nonempty("import kind", self.kind)


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionState:
    """QUE-16: everything needed to resume at the same problem after a quit or crash."""

    id: int | None = None
    study_day: str
    started_at: int = 0
    updated_at: int = 0
    ended_at: int | None = None
    untimed: bool = False
    plan: JsonObject = field(default_factory=dict)
    position: int = 0
    current: JsonObject | None = None  # card id, rev, seed, part, presentation id ...
    active_ms: int = 0  # active time so far on the current problem
    draft: str | None = None  # any typed answer
    extra: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        check_study_day("study day", self.study_day)
        _nonneg("position", self.position)
        _nonneg("active_ms", self.active_ms)


# The user-side rows an attempt (or a void) may change; each is snapshotted for undo.
type StateRecord = (
    SkillState
    | SkillTierState
    | SkillShadow
    | FlashcardState
    | CardUser
    | PendingCheck
    | WeakSpot
    | DiagnosticSet
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GradedAnswer:
    """Everything one graded answer writes, committed together in one transaction."""

    attempt: Attempt
    changes: tuple[StateRecord, ...] = ()
    reviews: tuple[ReviewEvent, ...] = ()
    credits: tuple[ImplicitCredit, ...] = ()
    session: SessionState | None = None
