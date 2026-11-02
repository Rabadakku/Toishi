"""What gets picked when more is due than N (the triage table, QUE-4..6). Pure.

`candidates` turns a Snapshot into units (single problems, or a learning block: worked
example plus problems), each carrying its triage class (config.CHECK .. config.NEW), a rank
inside the class, its reason tag and the one-sentence "Why is this here?" text. Every skill
appears in at most one unit: a skill with a check gets no separate review (the check is
its review). A redo card is unrated reinforcement; when its skill is due, a fresh problem
is the rated review and the redo follows it (I4, ADR-0014).

Order 6 (other due reviews) is pluggable (QUE-6): `POLICIES` maps a policy name to a sort
key; the session records the policy's name on every attempt so stats can compare them.
"""

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from core.engine import (
    DueSkill,
    checkup_candidates,
    checkup_due,
    core_band,
    learning_step,
    memory_of,
    stretch_allowed,
    stretch_tier,
)
from core.engine.diagnosis import method_choice_active
from core.model import SkillState
from core.queue.config import (
    CHECK,
    CHECKUP_SIZE,
    EXAM,
    LEARNING,
    METHOD_MS,
    NEW,
    PREREQ,
    REDO_GAP,
    RELEARN,
    REVIEW,
)
from core.queue.daylog import pulled_forward
from core.queue.items import TAG_LABELS, PlanItem, ReasonTag, Unit, why
from core.queue.snapshot import Snapshot


@dataclass(frozen=True, slots=True)
class TriagePolicy:
    """Sort key for order 6 (lower first) and the variant of its "why" text."""

    name: str
    key: Callable[[DueSkill], float]
    why_variant: str = "review"


POLICIES: Mapping[str, TriagePolicy] = {
    # QUE-6: the recommended policy saves the skills that are still saveable.
    "recommended": TriagePolicy("recommended", lambda d: -d.recall),
    "lowest-recall-first": TriagePolicy(
        "lowest-recall-first", lambda d: d.recall, "review.policy-low"
    ),
}


def policy_for(name: str | None) -> TriagePolicy:
    return POLICIES.get(name or "recommended", POLICIES["recommended"])


def _stability(state: SkillState | None) -> float | None:
    memory = memory_of(state)
    return memory.stability if memory is not None else None


def band_tier(snap: Snapshot, skill_id: str, *, lighter: bool = False) -> float:
    """Expected tier of a skill's next problem (ordering and minutes)."""
    state = snap.states.get(skill_id)
    if lighter or memory_of(state) is None:
        return 1.5
    band = core_band(_stability(state), exam_window=skill_id in snap.exam_scope)
    return sum(band) / len(band)


class ItemBuilder:
    def __init__(self, snap: Snapshot, *, lighter: bool) -> None:
        self.snap = snap
        self.lighter = lighter
        self.units: list[Unit] = []
        self.taken: set[str] = set()

    def item(
        self,
        key: str,
        skill_id: str | None,
        *,
        order: int,
        rank: float,
        tag: ReasonTag,
        variant: str | None = None,
        purpose: str = "review",
        kind: str = "problem",
        tier: float | None = None,
        course: str | None = None,
        label: str | None = None,
        why_text: str | None = None,
        **extra: object,
    ) -> PlanItem:
        snap = self.snap
        tier_hint = (
            tier if tier is not None else band_tier(snap, skill_id or "", lighter=self.lighter)
        )
        skill = snap.catalog.skills.get(skill_id or "")
        if kind == "problem" and skill is not None and skill.method_choice:
            # ENG-16: a method-choice skill is practised with which-method items, mixed in
            # with full problems and never taking one's slot.
            extra.setdefault("method", True)
            if tag == "review" and variant in (None, "review", "review.policy-low"):
                variant = "review.method"
        est_ms = METHOD_MS if extra.get("method") else snap.times.item_ms(kind, skill_id, tier_hint)
        return PlanItem(
            key=key,
            kind=kind,  # type: ignore[arg-type]
            skill_id=skill_id,
            course_id=course or snap.course_of(skill_id) or "",
            section_id=snap.section_of(skill_id),
            order=order,
            rank=rank,
            tag=tag,
            label=label or TAG_LABELS[tag],
            why=why_text or why(variant or tag),
            purpose=purpose,
            tier_hint=tier_hint,
            est_ms=est_ms,
            **extra,  # type: ignore[arg-type]
        )

    def add(self, *items: PlanItem) -> None:
        self.units.append(tuple(items))
        for item in items:
            if item.skill_id is not None:
                self.taken.add(item.skill_id)


def candidates(
    snap: Snapshot,
    *,
    lighter: bool = False,
    policy: TriagePolicy | None = None,
    include_new: bool = True,
    include_checks: bool = True,
) -> list[Unit]:
    """All units that could fill today's slots, in triage order (class, then rank)."""
    policy = policy or policy_for(snap.settings.policy)
    b = ItemBuilder(snap, lighter=lighter)
    due = {d.skill_id: d for d in snap.due}
    if include_checks:
        _checks(b)
    _relearn(b, due)
    _learning(b)
    _prerequisites(b, due)
    _exam(b, due)
    _reviews(b, due, policy)
    if include_new and not lighter:
        _new_skills(b)
    return sorted(b.units, key=lambda u: (u[0].order, u[0].rank, u[0].key))


# ---------------------------------------------------------------- classes 1-7


def _checks(b: ItemBuilder) -> None:
    """Order 1: the diagnosis flow's pending checks in its own serving order (queue_order:
    earliest allowed, then deepest prerequisite first). A diagnostic set's checks (one per
    card) all come; otherwise one check per skill, and it stands in for that skill's review."""
    snap = b.snap
    for i, check in enumerate(snap.checks):
        if check.id is None or (check.kind != "diagnostic" and check.skill_id in b.taken):
            continue
        missed = snap.skill_name(snap.check_missed.get(check.id))
        diagnostic = check.kind == "diagnostic"
        b.add(
            b.item(
                f"chk:{check.id}",
                check.skill_id,
                order=CHECK,
                rank=float(i),
                tag="check",
                variant="check.diagnostic" if diagnostic else "check",
                why_text=snap.check_reasons.get(check.id),
                label=f"Check (after a miss on {missed})" if missed and not diagnostic else "Check",
                tier=2.0,
                course=snap.check_course.get(check.id),
                check_id=check.id,
                check_kind=check.kind,
                card_id=check.card_id,
            )
        )


def _relearn(b: ItemBuilder, due: Mapping[str, DueSkill]) -> None:
    snap = b.snap
    redo_by_skill: dict[str, tuple[str, bool]] = {}
    for card_id, (skill, sure) in sorted(snap.redo.items()):
        if skill not in redo_by_skill or (sure and not redo_by_skill[skill][1]):
            redo_by_skill[skill] = (card_id, sure)
    for skill, (card_id, sure) in sorted(redo_by_skill.items()):
        if skill in b.taken or not snap.active_skill(skill):
            continue
        d = due.get(skill)
        rank = (0.0 if sure else 0.5) - (d.days_overdue if d else 0) / 1e3
        redo = b.item(
            f"redo:{card_id}",
            skill,
            order=RELEARN,
            rank=rank,
            tag="redo",
            purpose="redo",
            card_id=card_id,
        )
        if d is None:  # not due: the redo is unrated reinforcement (I4)
            b.add(redo)
            continue
        # Due: a fresh problem is the rated review and the redo follows it, unrated (I4):
        # one known problem measures item memory, not the skill.
        relearn = d.reason == "relearn"
        fresh = b.item(
            f"{'rel' if relearn else 'rev'}:{skill}",
            skill,
            why_text=_note(d),
            order=RELEARN,
            rank=rank - 1e-4,
            tag="relearn" if relearn else "review",
            purpose="relearn" if relearn else "review",
        )
        b.add(fresh)
        b.add(replace(redo, anchor=fresh.key, gap=REDO_GAP))
    for d in snap.due:
        if d.reason != "relearn" or d.skill_id in b.taken:
            continue
        b.add(
            b.item(
                f"rel:{d.skill_id}",
                d.skill_id,
                why_text=_note(d),
                order=RELEARN,
                rank=1.0 - d.days_overdue / 1e3,
                tag="relearn",
                purpose="relearn",
            )
        )


def _note(d: DueSkill) -> str | None:
    """A due date the diagnosis flow moved explains itself (ENG-6 pull-forward, ...)."""
    return None if not d.note else d.note.rstrip(".") + "."


def learning_block(
    b: ItemBuilder, skill_id: str, state: SkillState | None, *, order: int, rank: float
) -> Unit:
    snap, settings = b.snap, b.snap.settings
    need = settings.correct_in_a_row
    left = settings.max_learning_problems
    example = True
    variant = "new-skill"
    if state is not None and state.introduced_at is not None:
        need = max(1, settings.correct_in_a_row - state.learning_streak)
        left = max(1, settings.max_learning_problems - state.learning_count)
        example = learning_step(state, snap.day) == "example"
        variant = "new-skill.continue"
    size = max(1, min(need + 1, left))
    items: list[PlanItem] = []
    if example:
        items.append(
            b.item(
                f"ex:{skill_id}",
                skill_id,
                order=order,
                rank=rank,
                tag="new-skill",
                variant=variant,
                kind="example",
                tier=1.0,
                block=f"blk:{skill_id}",
            )
        )
    for i in range(size):
        items.append(
            b.item(
                f"lrn:{skill_id}:{i}",
                skill_id,
                order=order,
                rank=rank,
                tag="new-skill",
                variant=variant,
                tier=1.5,
                block=f"blk:{skill_id}",
            )
        )
    return tuple(items)


def _learning(b: ItemBuilder) -> None:
    snap = b.snap
    for skill_id, state in sorted(snap.states.items(), key=lambda kv: kv[1].introduced_at or 0):
        if skill_id in b.taken or state.introduced_at is None or memory_of(state) is not None:
            continue
        if state.fsrs_state is not None or not snap.active_skill(skill_id):
            continue
        if learning_step(state, snap.day) not in ("example", "problem"):
            continue
        b.add(*learning_block(b, skill_id, state, order=LEARNING, rank=state.introduced_at / 1e13))


def _learning_targets(snap: Snapshot) -> set[str]:
    """Skills being learned now (in their learning phase, or next in line in a Learning-now
    section) or recently failed: their due prerequisites are order 4."""
    out = set(snap.recent_fails)
    for skill_id, skill in snap.catalog.skills.items():
        state = snap.states.get(skill_id)
        in_phase = (
            state is not None and state.introduced_at is not None and memory_of(state) is None
        )
        next_up = snap.section_states.get(skill.section_id or "") == "learning" and new_skill_ready(
            snap, skill_id
        )
        if in_phase or next_up:
            out.add(skill_id)
    return out


def _prerequisites(b: ItemBuilder, due: Mapping[str, DueSkill]) -> None:
    snap = b.snap
    prereqs = snap.catalog.prerequisites(_learning_targets(snap))
    for d in snap.due:
        if d.skill_id in b.taken:
            continue
        if d.escalated:
            b.add(
                b.item(
                    f"rev:{d.skill_id}",
                    d.skill_id,
                    why_text=_note(d),
                    order=PREREQ,
                    rank=-d.days_overdue,
                    tag="review",
                    variant="review.overdue",
                )
            )
        elif d.skill_id in prereqs:
            b.add(
                b.item(
                    f"rev:{d.skill_id}",
                    d.skill_id,
                    why_text=_note(d),
                    order=PREREQ,
                    rank=1 + d.recall,
                    tag="review",
                    variant="review.prereq",
                )
            )


def _exam(b: ItemBuilder, due: Mapping[str, DueSkill]) -> None:
    snap = b.snap
    for booster in sorted(snap.boosters, key=lambda x: (x.recall_without, x.skill_id)):
        if booster.skill_id in b.taken or not snap.active_skill(booster.skill_id):
            continue
        b.add(
            b.item(
                f"bst:{booster.skill_id}",
                booster.skill_id,
                order=EXAM,
                rank=booster.recall_without,
                tag="exam-prep",
                purpose="booster",
            )
        )
    for d in snap.due:
        if d.skill_id in b.taken or d.skill_id not in snap.exam_scope:
            continue
        b.add(
            b.item(
                f"rev:{d.skill_id}",
                d.skill_id,
                why_text=_note(d),
                order=EXAM,
                rank=1 + d.recall,
                tag="exam-prep",
            )
        )


def _reviews(b: ItemBuilder, due: Mapping[str, DueSkill], policy: TriagePolicy) -> None:
    snap = b.snap
    every = snap.settings.checkup_every_weeks
    if checkup_due(snap.last_checkup, snap.day, every):
        last_review = {
            k: snap.days.day_of(s.last_review_at)
            for k, s in snap.states.items()
            if s.last_review_at is not None
        }
        eligible = [s for k, s in snap.states.items() if k not in b.taken and snap.active_skill(k)]
        picks = checkup_candidates(
            eligible,
            today=snap.day,
            due_days=snap.due_days,
            day_of_review=last_review,
            limit=CHECKUP_SIZE,
        )
        for i, skill_id in enumerate(picks):
            b.add(
                b.item(
                    f"cku:{skill_id}",
                    skill_id,
                    order=REVIEW,
                    rank=-10 + i / 100,
                    tag="review",
                    variant="review.checkup",
                    purpose="checkup",
                )
            )
    if snap.vacation is not None:
        early = pulled_forward(snap.vacation, snap.day, snap.due_days)
        for i, skill_id in enumerate(early):
            if skill_id in b.taken or skill_id in due or not snap.active_skill(skill_id):
                continue
            b.add(
                b.item(
                    f"vac:{skill_id}",
                    skill_id,
                    order=REVIEW,
                    rank=-5 + i / 1000,
                    tag="review",
                    variant="review.vacation",
                )
            )
    for d in sorted(snap.due, key=lambda x: (policy.key(x), x.skill_id)):
        if d.skill_id in b.taken:
            continue
        b.add(
            b.item(
                f"rev:{d.skill_id}",
                d.skill_id,
                why_text=_note(d),
                order=REVIEW,
                rank=policy.key(d),
                tag="review",
                variant=policy.why_variant,
            )
        )


def _depths(snap: Snapshot) -> dict[str, int]:
    skills = snap.catalog.skills
    memo: dict[str, int] = {}

    def depth(k: str, trail: frozenset[str] = frozenset()) -> int:
        if k in memo:
            return memo[k]
        if k in trail or k not in skills:
            return 0
        reqs = skills[k].requires
        value = 1 + max((depth(r, trail | {k}) for r in reqs), default=-1)
        memo[k] = value
        return value

    for k in skills:
        depth(k)
    return memo


def new_skill_ready(snap: Snapshot, skill_id: str) -> bool:
    """LIB-3: in an active section, not started, every prerequisite learned or placed."""
    if not snap.active_skill(skill_id):
        return False
    state = snap.states.get(skill_id)
    if state is not None and (state.introduced_at is not None or memory_of(state) is not None):
        return False
    skill = snap.catalog.skills[skill_id]
    if skill.method_choice:  # ENG-16: active once two of the methods it chooses among are learned
        return method_choice_active(skill, snap.states.get)
    return all(
        r not in snap.catalog.skills or memory_of(snap.states.get(r)) is not None
        for r in skill.requires
    )


def _new_skills(b: ItemBuilder) -> None:
    snap = b.snap
    depths = _depths(snap)
    order = snap.catalog.section_order
    ready = [k for k in snap.catalog.skills if k not in b.taken and new_skill_ready(snap, k)]

    def rank(k: str) -> float:
        section = snap.section_of(k) or ""
        learning_now = snap.section_states.get(section) == "learning"
        unit_ord, sec_ord = order.get(section, (0, 0))
        return (
            (0 if learning_now else 1) * 1e7
            + depths.get(k, 0) * 1e5
            + min(unit_ord, 99) * 1e3
            + min(sec_ord, 999)
        )

    for i, k in enumerate(sorted(ready, key=lambda k: (rank(k), k))):
        b.add(*learning_block(b, k, None, order=NEW, rank=rank(k) + i / 1e3))


# ---------------------------------------------------------------- stretch share


def wants_stretch(skill_id: str, day: date, fraction: float) -> bool:
    """A stable, even spread: about `fraction` of review skill-days get a stretch problem."""
    digest = hashlib.sha256(f"stretch|{skill_id}|{day.isoformat()}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64 < fraction


def mark_stretch(snap: Snapshot, units: Sequence[Unit]) -> list[Unit]:
    """Turn about `queue.stretch_fraction` of the plan's plain reviews into stretch problems
    (never in an exam window or a Lighter set; at most one Elite problem). A stretch problem
    is unrated and its skill's review moves to the next study day (ADR-0014), so only skills
    due today exactly are picked: one already moved by a stretch is never moved again."""
    fraction = snap.settings.stretch_fraction
    due_today = {d.skill_id for d in snap.due if d.days_overdue == 0}
    out: list[Unit] = []
    reviews = stretches = 0
    elite_used = False
    for unit in units:
        item = unit[0]
        plain = (
            len(unit) == 1
            and item.kind == "problem"
            and item.order in (PREREQ, REVIEW)
            and item.purpose == "review"
            and item.anchor is None
            and item.skill_id is not None
            and item.skill_id not in snap.exam_scope
            and item.skill_id in due_today
        )
        if not plain or item.skill_id is None:
            out.append(unit)
            continue
        tier = stretch_tier(_stability(snap.states.get(item.skill_id)), elite=snap.settings.elite)
        if (
            tier is not None
            and wants_stretch(item.skill_id, snap.day, fraction)
            and stretch_allowed(
                reviews_so_far=reviews,
                stretches_so_far=stretches,
                elite_used=elite_used,
                tier=tier,
                fraction=fraction,
            )
        ):
            stretches += 1
            elite_used = elite_used or tier == 5
            out.append(
                (
                    replace(
                        item,
                        stretch=True,
                        tag="stretch",
                        label=TAG_LABELS["stretch"],
                        why=why("stretch"),
                        tier_hint=float(tier),
                        est_ms=snap.times.problem_ms(item.skill_id, tier),
                    ),
                )
            )
        else:
            out.append(unit)
        reviews += 1
    return out
