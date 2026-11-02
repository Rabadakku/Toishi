"""Check problems: which card, which prerequisites in which order, and the PendingCheck
records the daily queue serves (What went wrong?, ENG-6, QUE-1 order 1).

A check is a quick problem on one skill, at a tier at or below the student's level (ENG-6:
tier 1 or 2) with predicted success at least 0.6, served at least three items after the
miss that asked for it, or next session. Prerequisite checks go deepest first: the queue
serves a lower `after_items` first, and deeper checks get the lower numbers.

Each check's reason sentence is stored on its PendingCheck (`reason`, schema v2). Checks
written before v2 kept it in the asking attempt's extra["diagnosis"]["checks"]; the v2
migration copied it over, and `check_reason` still reads it there for any row it could not
match (ADR-0009), else composes one.
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from core.engine.diagnosis.config import (
    CHECK_AFTER_ITEMS,
    CHECK_MAX_TIER,
    CHECK_MIN_P,
    LOW_RECALL,
    MAX_PREREQ_CHECKS,
)
from core.engine.lifecycle import in_learning_phase
from core.engine.selection import (
    SeenIndex,
    core_band,
    difficulty_of,
    form_key,
    is_fresh,
    p_correct,
    seen_since,
)
from core.model import THIS_ATTEMPT, Attempt, CardRef, CheckKind, PendingCheck, Skill, SkillState
from core.model import WeakSpot as WeakSpotRow

type RecallOf = Callable[[str], float | None]


def level_tier(skill: Skill | None, state: SkillState | None) -> int:
    """The highest tier at the student's level: tier 2 while learning or Learned below
    stability 7, the top of the core band once Learned, the exam tier at Exam-level, one
    above it at Mastered."""
    exam_tier = (skill.exam_tier if skill is not None else None) or 3
    if state is None or in_learning_phase(state):
        return 2
    if state.level == "mastered":
        return min(5, exam_tier + 1)
    if state.level == "exam":
        return exam_tier
    return max(core_band(state.stability))


def check_tiers(skill: Skill | None, state: SkillState | None) -> tuple[int, ...]:
    top = min(CHECK_MAX_TIER, level_tier(skill, state))
    return tuple(range(1, top + 1))


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckPick:
    card: CardRef
    p: float


def pick_check_card(
    refs: Sequence[CardRef],
    *,
    theta: float,
    tiers: Sequence[int],
    now_ms: int,
    seen: SeenIndex,
    exclude: Iterable[str] = (),
    cued: bool = False,
    prefer_form: str | None = None,
    hidden: Iterable[str] = (),
    today_start_ms: int | None = None,
) -> CheckPick | None:
    """A check problem: in `tiers`, predicted success >= 0.6 (closest to 0.8 among those;
    the most likely one when none reaches 0.6), fresh cards first. `cued`: only cards with
    a cued stem (a cued twin), preferring `prefer_form` (the missed problem's form).
    `today_start_ms`: the study day's start; a card served since then is never picked."""
    skip = set(exclude) | set(hidden)
    pool = [
        r
        for r in refs
        if r.kind == "problem" and r.status == "active" and r.id not in skip and r.tier in tiers
    ]
    if cued:
        pool = [r for r in pool if r.has_cued_question]
    if today_start_ms is not None:  # ENG-6: checks obey the no-card-twice-a-day rule
        pool = [r for r in pool if not seen_since(r, seen, today_start_ms)]
    if not pool:
        return None

    def p_of(r: CardRef) -> float:
        return p_correct(theta, difficulty_of(form_key(r.id, r.template_id), r.tier, seen.forms))

    def key(r: CardRef) -> tuple[int, int, float, str]:
        p = p_of(r)
        same = prefer_form is not None and form_key(r.id, r.template_id) == prefer_form
        return (
            0 if is_fresh(r, seen, now_ms) else 1,
            0 if same else 1,
            abs(p - 0.8) if p >= CHECK_MIN_P else 2 - p,
            r.id,
        )

    best = min(pool, key=key)
    return CheckPick(card=best, p=p_of(best))


def prerequisites_by_depth(skill_id: str, skills: Mapping[str, Skill]) -> dict[str, int]:
    """Every skill reachable by `requires` edges, with its shortest distance (1 = direct)."""
    depth: dict[str, int] = {}
    frontier = [skill_id]
    level = 0
    while frontier:
        level += 1
        nxt: list[str] = []
        for current in frontier:
            skill = skills.get(current)
            for r in skill.requires if skill is not None else ():
                if r != skill_id and r not in depth:
                    depth[r] = level
                    nxt.append(r)
        frontier = nxt
    return depth


def low_recall(recall: float | None, state: SkillState | None) -> bool:
    return state is None or in_learning_phase(state) or recall is None or recall < LOW_RECALL


def prerequisite_targets(
    skill_id: str,
    skills: Mapping[str, Skill],
    states: Callable[[str], SkillState | None],
    recall: RecallOf,
    *,
    every_direct: bool = False,
    every: bool = False,
    limit: int = MAX_PREREQ_CHECKS,
) -> list[tuple[str, int]]:
    """(prerequisite, depth) pairs to check, deepest first: the low-recall ones (or every
    direct one, or every one), weakest first within a depth. Skills never started (no
    state) are left out: there is nothing to check yet."""
    chosen: list[tuple[str, int, float]] = []
    for k, d in prerequisites_by_depth(skill_id, skills).items():
        state = states(k)
        if state is None or (state.introduced_at is None and state.fsrs_state is None):
            continue
        r = recall(k)
        if every or (every_direct and d == 1) or low_recall(r, state):
            chosen.append((k, d, -1.0 if r is None else r))
    chosen.sort(key=lambda t: (-t[1], t[2], t[0]))
    return [(k, d) for k, d, _ in chosen[:limit]]


# ---------------------------------------------------------------- records and reasons


@dataclass(frozen=True, slots=True, kw_only=True)
class NewCheck:
    """A check to create, with its reason sentence (stored on the check)."""

    skill_id: str
    kind: CheckKind
    reason: str
    card_id: str | None = None
    depth: int = 0
    after_items: int = CHECK_AFTER_ITEMS
    not_before_at: int | None = None

    def record(self, *, created_at: int, attempt_id: int | None = THIS_ATTEMPT) -> PendingCheck:
        return PendingCheck(
            created_at=created_at,
            attempt_id=attempt_id,
            skill_id=self.skill_id,
            kind=self.kind,
            card_id=self.card_id,
            after_items=self.after_items,
            not_before_at=self.not_before_at,
            depth=self.depth,
            reason=self.reason,
        )

    def as_json(self) -> dict[str, object]:
        """What the attempt's extra["diagnosis"]["checks"] logs (the reason is on the check)."""
        return {
            "skill": self.skill_id,
            "kind": self.kind,
            "card": self.card_id,
            "depth": self.depth,
        }


def name_of(skills: Mapping[str, Skill], skill_id: str) -> str:
    skill = skills.get(skill_id)
    return skill.name if skill is not None else skill_id


def step_reason(skills: Mapping[str, Skill], problem: str, check: str, label: str | None) -> str:
    where = f" at the step “{label}”" if label else ""
    if check == problem:
        return f"Check after a miss on {name_of(skills, problem)}{where}"
    return (
        f"Check after a miss on {name_of(skills, problem)}: did {name_of(skills, check)}"
        f"{where} break?"
    )


def prerequisite_reason(skills: Mapping[str, Skill], prereq: str, failed: str) -> str:
    return (
        f"Check: {name_of(skills, prereq)} is a prerequisite of {name_of(skills, failed)}, "
        "which was just missed"
    )


def part_reason(skills: Mapping[str, Skill], part_skill: str, card_skill: str, label: str) -> str:
    return (
        f"Check: part {label} of a {name_of(skills, card_skill)} problem, which uses "
        f"{name_of(skills, part_skill)}, was just missed"
    )


def twin_reason(skills: Mapping[str, Skill], problem: str) -> str:
    return (
        f"The same kind of {name_of(skills, problem)} problem with the method named: "
        "was it the method, or choosing it?"
    )


def diagnostic_reason(skills: Mapping[str, Skill], skill_id: str, spot: WeakSpotRow | None) -> str:
    if spot is None:
        return counted_diagnostic_reason(skills, skill_id)
    return counted_diagnostic_reason(
        skills, skill_id, misses=spot.misses, problems=spot.problems, days=spot.days
    )


def counted_diagnostic_reason(
    skills: Mapping[str, Skill],
    skill_id: str,
    *,
    misses: int | None = None,
    problems: int | None = None,
    days: int | None = None,
) -> str:
    base = f"Diagnostic: {name_of(skills, skill_id)} has gone worse than expected lately"
    if misses is None or problems is None or days is None:
        return base
    return f"{base} ({misses} misses on {problems} problems over {days} days)"


def legacy_reason(check: PendingCheck, attempt: Attempt | None) -> str | None:
    """The reason a check written before schema v2 kept in its asking attempt's extra."""
    if attempt is None:
        return None
    stored = attempt.extra.get("diagnosis", {}).get("checks", [])
    for item in stored if isinstance(stored, list) else []:
        if item.get("skill") == check.skill_id and item.get("kind") == check.kind:
            return str(item.get("reason"))
    return None


def check_reason(
    check: PendingCheck,
    *,
    skills: Mapping[str, Skill],
    attempt: Attempt | None = None,
    weak_spot: WeakSpotRow | None = None,
) -> str:
    """The "Why is this here?" sentence of a check: the one stored on it, else (a check
    written before schema v2) the one its asking attempt kept, else one composed from the
    record."""
    if check.reason is not None:
        return check.reason
    legacy = legacy_reason(check, attempt)
    if legacy is not None:
        return legacy
    problem = attempt.skill_id if attempt is not None and attempt.skill_id else check.skill_id
    if check.kind == "diagnostic":
        return diagnostic_reason(skills, check.skill_id, weak_spot)
    if check.kind == "cued-twin":
        return twin_reason(skills, problem)
    if check.kind == "prerequisite":
        return prerequisite_reason(skills, check.skill_id, problem)
    return step_reason(skills, problem, check.skill_id, None)


def queue_order(checks: Iterable[PendingCheck]) -> list[PendingCheck]:
    """Pending checks in serving order: earliest allowed first, then deepest first."""
    return sorted(
        (c for c in checks if c.status == "pending"),
        key=lambda c: (c.not_before_at or 0, c.created_at, c.after_items, -c.depth, c.id or 0),
    )
