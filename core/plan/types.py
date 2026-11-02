"""Data contract of the practice planner (docs/design/student-model.md, sections 4 and 8, and
the wave 2 additions of docs/design/wave2-planner.md section 5).

Implementations may add fields but must not rename or remove these.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from core.learner.types import ComponentId, ProblemSpec, UpdateRecord
from core.plan.config import GROWTH_BAND

type Role = Literal["new", "growth", "maintenance", "check", "practice-test", "focused", "sitting"]
type MilestoneName = Literal["M1", "M2", "M3", "keep"]
type SkillState = Literal[
    "not-introduced", "new", "growth", "maintenance", "keep", "slip-limited", "struggling"
]
type Track = Literal["ahead", "on-track", "behind"]
type HoursBasis = Literal["history", "standard", "none"]


@dataclass(frozen=True, slots=True)
class SectionPace:
    deck: str  # Course::Unit::Section
    hours: float  # standard class hours for the section


@dataclass(frozen=True, slots=True)
class PaceStandard:
    sections: tuple[SectionPace, ...]  # in course order
    weekly_hours: float  # standard class hours per week
    minutes_per_step: float = 1.5
    standard_outside_hours: float | None = None  # reference hours per week outside class


@dataclass(frozen=True, slots=True)
class SkillInfo:
    skill_id: ComponentId
    deck: str
    order: int  # position in the course
    requires: tuple[ComponentId, ...] = ()
    confusable: tuple[ComponentId, ...] = ()
    example_card: str | None = None
    pool: tuple[ProblemSpec, ...] = ()  # problems whose main skill is this one
    background: bool = False


@dataclass(frozen=True, slots=True)
class Course:
    course_id: str
    standard: PaceStandard
    skills: tuple[SkillInfo, ...]


@dataclass(frozen=True, slots=True)
class ExamSpec:
    exam_id: int
    day: date
    scope_decks: tuple[str, ...]
    target: float | None = None  # None: the course accuracy target


@dataclass(frozen=True, slots=True)
class CourseSettings:
    course_id: str
    start: date | None = None
    aligned: tuple[str, date] | None = None  # (section deck, day): "my class is at X today"
    pace_factor: float = 1.0
    accuracy_target: float = 0.90
    target_tier: int = 4
    end: date | None = None  # None: self-study, never drops to Keep
    exams: tuple[ExamSpec, ...] = ()
    keep_target: float = 0.80
    keep_tier: int = 3
    # Wave 2: the growth band of predicted first-try chances (the owner may choose (0.50, 0.75));
    # an empty band takes the problem closest to its midpoint.
    growth_band: tuple[float, float] = GROWTH_BAND


@dataclass(frozen=True, slots=True)
class Milestone:
    name: MilestoneName
    tier: int
    deadline: date | None  # None for keep


@dataclass(frozen=True, slots=True)
class SkillStatus:
    skill_id: ComponentId
    intro: date | None
    milestones: tuple[Milestone, ...]
    current: Milestone | None  # the next uncertified milestone, or None when all are certified
    state: SkillState
    track: Track
    level: int | None  # highest tier with every tier at or below it certified
    posterior_mean: float | None  # direct-evidence posterior at the current milestone tier
    readiness: float | None  # calibrated model prediction at the current or certified tier
    pace_ok: bool | None
    # Added by the implementation (core/plan/status.py):
    bottleneck: ComponentId | None = None  # course component with the lowest q at the tier
    prerequisites: tuple[ComponentId, ...] = ()  # struggling: prerequisites given growth
    assumed: bool = False  # mid-course start: assumed learned, in Keep maintenance


@dataclass(frozen=True, slots=True)
class WorkItem:
    skill_id: ComponentId
    role: Role
    problem: ProblemSpec | None  # None for a worked example
    example_card: str | None
    expected_minutes: float
    priority: int  # lower is served earlier when the session is cut short
    # Added by the implementation (logged with the attempt; design 3.4 and 6.4):
    tier: int | None = None  # the problem's tier (None for a worked example)
    milestone: MilestoneName | None = None  # the milestone the item works toward
    missed: bool = False  # growth for a milestone whose deadline has passed (40% share)
    block: bool = False  # part of a new skill's block (example and first problems)
    p: float | None = None  # predicted first-try chance when chosen
    reason: str = ""  # why this problem: band, bottleneck, suspect, fallback, target, ...
    # Wave 2 (docs/design/wave2-planner.md section 5):
    ladder: int = 0  # the stuck ladder's rung: 1 a smaller problem, 2 a prerequisite's problem
    sitting: str | None = None  # the day's certification sitting (role "sitting")
    # A sitting item: the limit on the summed active time of its skill's sitting problems (the
    # sum of their T*, design v1.3); shown with the elapsed time, never a cut-off.
    time_limit: float | None = None
    # Added by the implementation (planner-impl-notes.md, "Wave 2"). The session passes served
    # items back as it got them (ServedItem.item), so later plans can read these:
    ladder_for: ComponentId | None = None  # a ladder item: the stuck skill whose slot it fills
    day_items: int | None = None  # the day's first plan's item count: later plans stay within it
    sitting_block: tuple[str, ...] = ()  # a sitting item: the sitting's problem ids, serve order


@dataclass(frozen=True, slots=True)
class ConfusableDecision:
    """One confusable pair in a plan: whether it was drawn adjacent (probability 0.5) and
    whether the final order has an item of one right next to an item of the other."""

    a: ComponentId
    b: ComponentId
    adjacent: bool
    placed: bool


@dataclass(frozen=True, slots=True)
class DayPlan:
    day: date
    items: tuple[WorkItem, ...]
    minutes: float
    hours_to_keep_pace: float | None  # per week, from the student's own history
    standard_hours: float | None  # the course's reference outside-class hours per week
    behind: tuple[ComponentId, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)  # feasibility and other notices
    # Added by the implementation (core/plan/daily.py):
    hours_basis: HoursBasis = "none"  # history, or the standard hours standing in
    statuses: tuple[SkillStatus, ...] = ()  # every course skill, in course order
    confusable: tuple[ConfusableDecision, ...] = ()  # randomized adjacency, logged (4.5)
    overflow: int = 0  # missed-milestone items past the 40% share, served after the rest
    dropped: tuple[WorkItem, ...] = ()  # items no order could place at all (none so far)
    # Wave 2 (docs/design/wave2-planner.md section 5):
    set_aside: tuple[ComponentId, ...] = ()  # skills with 3 misses in a row today: no more today
    sittings: tuple[tuple[str, tuple[ComponentId, ...]], ...] = ()  # sitting id and its skills
    # Added by the implementation:
    adjacent: tuple[ComponentId, ...] = ()  # skills placed next to themselves: nothing between
    # The predicted chance of passing a sitting today, for each skill that met the other
    # conditions (design v1.3's SITTING_PASS_MIN gate, logged).
    sitting_chances: tuple[tuple[ComponentId, float], ...] = ()


@dataclass(frozen=True, slots=True)
class ServedItem:
    """An item already served today, with its outcome. Wave 2 reads these from storage and
    passes them in order; `next_item` re-plans from them after each answer."""

    item: WorkItem
    correct: bool | None = None  # the first try, unaided; None: a worked example or unanswered
    update: UpdateRecord | None = None  # the model update of a graded first try (blame, m_k)
    minutes: float | None = None  # time spent on the item
