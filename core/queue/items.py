"""Plan items and plans: what the session serves, why, and in which order.

A plan is stored as JSON in the session row (QUE-16), so every record here round-trips
through plain dicts. Items keep their position in `Plan.items`: answered ones first (in the
order served), then the pending tail, which re-plans reorder.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, fields, replace
from typing import Any, Literal

from core.queue.config import CHECK, EXAM, FLASHCARD, LEARNING, NEW, PREREQ, RELEARN, REVIEW

type JsonObject = dict[str, Any]

ReasonTag = Literal["review", "relearn", "new-skill", "check", "exam-prep", "redo", "stretch"]
ItemKind = Literal["problem", "example", "flashcard"]
ItemStatus = Literal["pending", "done", "skipped"]
Mode = Literal["daily", "lighter", "focused", "practice-test", "extra"]

TAG_LABELS: Mapping[ReasonTag, str] = {
    "review": "Review",
    "relearn": "Relearn",
    "new-skill": "New skill",
    "check": "Check",
    "exam-prep": "Exam prep",
    "redo": "Redo",
    "stretch": "Stretch",
}

# One sentence each for the "Why is this here?" link. Variants refine the tag's text.
WHY: Mapping[str, str] = {
    "review": "This skill is due today, so a fresh problem now keeps your recall near your goal.",
    "review.policy-low": "This skill is due today and among your least recallable, so it goes "
    "early.",
    "review.checkup": "A mixed check-up: a skill that isn't due, to confirm it has really stuck.",
    "review.vacation": "Moved a little earlier so the days around your vacation carry an even "
    "load.",
    "review.prereq": "This is a foundation for a skill you are learning or recently missed, and "
    "forgotten foundations block new learning.",
    "review.overdue": "This skill has waited more than a week past due, so it moves up today.",
    "review.followup": "A problem at this skill's usual level after the harder one you missed.",
    "review.focused": "Focused practice you chose; it counts as an ordinary review.",
    "review.extra": "Extra practice from tomorrow's most useful items.",
    "relearn": "You missed this skill recently; following up now keeps the lapse from being "
    "wasted.",
    "relearn.reinforcement": "You missed this skill earlier in this session; one more fresh "
    "problem helps the fix stick.",
    "relearn.example": "A worked example first: the method behind this skill needs another "
    "look before its next problem.",
    "new-skill": "A new skill, introduced through a worked example and a short block of problems.",
    "new-skill.continue": "This skill's learning block is in progress, and half-learned skills "
    "fade fastest.",
    "check": "A quick check on a step you missed; it decides where the next repair goes.",
    "check.diagnostic": "A short set on a possible weak spot, to confirm it or clear it.",
    "exam-prep": "An exam covers this skill, and without a review now its recall on exam day "
    "would miss your goal.",
    "exam-prep.test": "A practice test problem at exam level, graded at the end like the real "
    "exam.",
    "redo": "You missed this exact problem a few days ago; solving it now shows the fix held.",
    "stretch": "A harder problem than usual for this skill, to stretch how far you can take it.",
    "review.method": "A quick which-method question: choosing the method is a skill of its own.",
    "review.find-error": "Find the error in another student's work: spotting a common mistake "
    "is a review of this skill.",
    "flashcard": "A flashcard due today.",
    "flashcard.refresher": "A flashcard on the skill you just missed, as a quick refresher.",
    "flashcard.reshow": "A flashcard you just missed, once more after a few other items.",
}


def why(variant: str) -> str:
    return WHY.get(variant) or WHY[variant.split(".", 1)[0]]


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanItem:
    """One thing to serve. `order` is the triage class (config.CHECK .. config.NEW, or
    FLASHCARD); `rank` sorts inside it (lower first). A learning block is the items sharing
    `block` (its worked example, then its problems). `anchor`/`gap`: serve at least `gap`
    items after the item `anchor` (the miss that asked for it)."""

    key: str
    kind: ItemKind
    skill_id: str | None
    course_id: str | None = None
    section_id: str | None = None
    order: int
    rank: float = 0.0
    tag: ReasonTag = "review"
    label: str = "Review"
    why: str = ""
    purpose: str = "review"  # the engine's ProblemOutcome.purpose
    tier_hint: float = 2.0  # expected tier (ordering and minutes)
    est_ms: int = 0
    stretch: bool = False
    block: str | None = None
    anchor: str | None = None
    gap: int = 0
    check_id: int | None = None
    check_kind: str | None = None  # step, prerequisite, cued-twin (shown cued), diagnostic
    card_id: str | None = None  # a fixed card; otherwise one is picked when served
    card_ord: int = 0  # flashcards: cloze blank (0 for flashcards)
    inserted: bool = False  # added by a re-plan (check, reinforcement, refresher)
    method: bool = False  # a which-method item (ENG-16): mixed in, outside the problem count
    status: ItemStatus = "pending"
    result: JsonObject | None = None

    @property
    def slots(self) -> int:
        """Problem slots (QUE-1): worked examples, flashcards and which-method items (mixed
        in with full problems, never replacing one) don't count."""
        return 1 if self.kind == "problem" and not self.method else 0

    @property
    def pending(self) -> bool:
        return self.status == "pending"

    @property
    def unit_key(self) -> str:
        return self.block or self.key

    def to_json(self) -> JsonObject:
        out = {name: getattr(self, name) for name in _ITEM_FIELDS}
        if self.result is not None:
            out["result"] = dict(self.result)
        return out

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> PlanItem:
        return cls(**{k: v for k, v in data.items() if k in _ITEM_FIELDS})


_ITEM_FIELDS = frozenset(f.name for f in fields(PlanItem))


@dataclass(frozen=True, slots=True, kw_only=True)
class Plan:
    """A session's plan. `n`: problem slots the plan keeps filled (it re-plans to stay at
    `n` while candidates last). `quotas`: problem slots per course as planned; `shares`:
    each course's share of the day, used to interleave courses. `bench`: candidates that
    did not fit, in priority order, for refills when slots free up."""

    day: str
    mode: Mode = "daily"
    policy: str = "recommended"
    n: int = 0
    items: tuple[PlanItem, ...] = ()
    bench: tuple[PlanItem, ...] = ()
    quotas: Mapping[str, int] = field(default_factory=dict)
    shares: Mapping[str, float] = field(default_factory=dict)
    lighter: bool = False
    flashcards: int = 0  # flashcard limit left for this plan (refreshers draw on it)
    counter: int = 0  # for keys of inserted items
    replanned: tuple[str, ...] = ()  # answered item keys whose follow-ups were planned
    info: JsonObject = field(default_factory=dict)

    # ------------------------------------------------------------ views

    def item(self, key: str) -> PlanItem | None:
        return next((i for i in self.items if i.key == key), None)

    def index(self, key: str) -> int:
        for i, item in enumerate(self.items):
            if item.key == key:
                return i
        raise KeyError(key)

    @property
    def done(self) -> list[PlanItem]:
        return [i for i in self.items if not i.pending]

    @property
    def pending(self) -> list[PlanItem]:
        return [i for i in self.items if i.pending]

    @property
    def slots(self) -> int:
        return sum(i.slots for i in self.items if i.status != "skipped")

    def first_pending(self) -> PlanItem | None:
        return next((i for i in self.items if i.pending), None)

    # ------------------------------------------------------------ changes

    def with_items(self, items: Iterable[PlanItem]) -> Plan:
        return replace(self, items=tuple(items))

    def updated(self, item: PlanItem) -> Plan:
        return self.with_items(item if i.key == item.key else i for i in self.items)

    def next_key(self, prefix: str) -> tuple[Plan, str]:
        counter = self.counter + 1
        return replace(self, counter=counter), f"{prefix}{counter}"

    # ------------------------------------------------------------ JSON

    def to_json(self) -> JsonObject:
        return {
            "day": self.day,
            "mode": self.mode,
            "policy": self.policy,
            "n": self.n,
            "items": [i.to_json() for i in self.items],
            "bench": [i.to_json() for i in self.bench],
            "quotas": dict(self.quotas),
            "shares": dict(self.shares),
            "lighter": self.lighter,
            "flashcards": self.flashcards,
            "counter": self.counter,
            "replanned": list(self.replanned),
            "info": dict(self.info),
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Plan:
        return cls(
            day=str(data["day"]),
            mode=data.get("mode", "daily"),
            policy=str(data.get("policy", "recommended")),
            n=int(data.get("n", 0)),
            items=tuple(PlanItem.from_json(i) for i in data.get("items", ())),
            bench=tuple(PlanItem.from_json(i) for i in data.get("bench", ())),
            quotas={str(k): int(v) for k, v in dict(data.get("quotas", {})).items()},
            shares={str(k): float(v) for k, v in dict(data.get("shares", {})).items()},
            lighter=bool(data.get("lighter", False)),
            flashcards=int(data.get("flashcards", 0)),
            counter=int(data.get("counter", 0)),
            replanned=tuple(str(k) for k in data.get("replanned", ())),
            info=dict(data.get("info", {})),
        )


# ---------------------------------------------------------------- units

type Unit = tuple[PlanItem, ...]


def units_of(items: Sequence[PlanItem]) -> list[Unit]:
    """Group items into units (a learning block is one unit), keeping first appearance order
    and, inside a block, the worked example first."""
    groups: dict[str, list[PlanItem]] = {}
    for item in items:
        groups.setdefault(item.unit_key, []).append(item)
    out: list[Unit] = []
    for group in groups.values():
        group.sort(key=lambda i: 0 if i.kind == "example" else 1)
        out.append(tuple(group))
    return out


def unit_slots(unit: Unit) -> int:
    return sum(i.slots for i in unit)


def unit_priority(unit: Unit) -> tuple[int, float, str]:
    head = min(unit, key=lambda i: (i.order, i.rank))
    return (head.order, head.rank, head.key)


def priority_order(units: Iterable[Unit]) -> list[Unit]:
    return sorted(units, key=unit_priority)


ORDER_NAMES: Mapping[int, str] = {
    FLASHCARD: "flashcard",
    CHECK: "check",
    RELEARN: "relearn",
    LEARNING: "learning",
    PREREQ: "prerequisite",
    EXAM: "exam",
    REVIEW: "review",
    NEW: "new",
}
