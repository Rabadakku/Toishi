"""ENG-6 pull-forward and ENG-7 partial credit (shadow mode in 1.0).

ENG-6: when a foundational skill lapses, every skill that encompasses it with weight 0.5 or
more gets its next review pulled earlier (due within two study days), never its stability
cut; the due-date note says why.

ENG-7: when skill A passes an explicit core-band review, each skill B it encompasses with
weight w (weights multiply along a chain; products under 0.25 are ignored) gets
S_B' = S_B + w (S_B^Good - S_B), where S_B^Good is the stability a Good review now would
give, at B's fractional-day recall; B's last-review time is not reset. No credit to skills
that are learning, relearning, failed in the last 7 days or rated very difficult. In shadow
mode the credited stability is stored beside the plain one (SkillShadow) and the schedule
keeps the plain one; with credit On it replaces the plain one, and a skill whose stability
has doubled from credit alone gets a forced explicit review. Credit events go to the
implicit_credit table, never to review_log, so they never reach the optimizer (ENG-12).

I9 (ADR-0014): credit can't compound. A target skill gets at most one credit per study
day, at the largest weight offered that day: a later, larger offer replaces the day's
credit (it starts again from the stability the day's first credit started from), a
smaller or equal one is skipped. And credit On takes effect only once credited
predictions beat plain ones on held-out log loss (`credit_switch`); until then it runs
as Shadow.
"""

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from core.engine.config import DAY_MS, GOOD, HARD
from core.engine.days import StudyDays
from core.engine.diagnosis.checks import name_of
from core.engine.diagnosis.config import (
    CREDIT_FAILED_DAYS,
    CREDIT_FORCE_RATIO,
    CREDIT_MIN_PRODUCT,
    CREDIT_VERY_DIFFICULT,
    PULL_DAYS,
    PULL_MIN_WEIGHT,
    CreditSetting,
)
from core.engine.diagnosis.verdict import hold_of, with_adjust
from core.engine.fsrs_adapter import FsrsAdapter, Memory
from core.engine.lifecycle import RELEARNING, in_learning_phase, memory_of, review_on
from core.model import Attempt, ImplicitCredit, JsonObject, Skill, SkillShadow, SkillState

EXPLICIT = "credit_explicit"  # On mode: the stability of the last explicit review
# ENG-7 / ADR-0019 item 9: credit On needs a paired 90% interval of (credited - plain) log
# loss per review that lies below -MARGIN, over at least 800 held-out credited reviews.
CREDIT_SWITCH_MIN = 800
CREDIT_SWITCH_MARGIN = 0.002  # nats per review; provisional, logged for evaluation (DEV-16)
CREDIT_SWITCH_Z = 1.6449  # a two-sided 90% interval


def encompassers(skill_id: str, skills: Mapping[str, Skill], min_weight: float) -> list[str]:
    return sorted(
        e.id
        for e in skills.values()
        if any(k == skill_id and w >= min_weight for k, w in e.encompasses)
    )


def pull_forward(
    lapsed: str,
    *,
    today: date,
    skills: Mapping[str, Skill],
    state_of: Callable[[str], SkillState | None],
) -> list[SkillState]:
    """ENG-6: encompassing skills (weight >= 0.5) of a lapsed skill are due within two
    study days. Only the due date moves; stability is untouched."""
    out: list[SkillState] = []
    reason = f"Earlier review: {name_of(skills, lapsed)}, which it builds on, just lapsed"
    for e in encompassers(lapsed, skills, PULL_MIN_WEIGHT):
        state = state_of(e)
        if e == lapsed or state is None or in_learning_phase(state) or hold_of(state):
            continue
        out.append(with_adjust(state, not_after=today + timedelta(days=PULL_DAYS), reason=reason))
    return out


def credit_targets(skill_id: str, skills: Mapping[str, Skill]) -> dict[str, float]:
    """Skills A encompasses, directly or along a chain, with the largest weight product
    (products under 0.25 are ignored)."""
    best: dict[str, float] = {}
    stack: list[tuple[str, float]] = [(skill_id, 1.0)]
    while stack:
        current, weight = stack.pop()
        skill = skills.get(current)
        for k, w in skill.encompasses if skill is not None else ():
            product = weight * w
            if k == skill_id or product < CREDIT_MIN_PRODUCT or product <= best.get(k, 0.0):
                continue
            best[k] = product
            stack.append((k, product))
    return best


@dataclass(frozen=True, slots=True, kw_only=True)
class CreditResult:
    credits: list[ImplicitCredit] = field(default_factory=list)
    shadows: list[SkillShadow] = field(default_factory=list)
    states: list[SkillState] = field(default_factory=list)  # credit On only
    forced: list[str] = field(default_factory=list)  # doubled from credit alone
    skipped: dict[str, str] = field(default_factory=dict)  # skill -> why no credit


def excluded(state: SkillState | None, *, now: int, last_failure_at: int | None) -> str | None:
    if state is None or in_learning_phase(state) or memory_of(state) is None:
        return "learning"
    if state.fsrs_state == RELEARNING or hold_of(state) is not None:
        return "relearning"
    if last_failure_at is not None and now - last_failure_at < CREDIT_FAILED_DAYS * DAY_MS:
        return "failed in the last 7 days"
    if state.difficulty is not None and state.difficulty >= CREDIT_VERY_DIFFICULT:
        return "very difficult"
    return None


def credited(
    stability: float, memory: Memory, weight: float, now: int, adapter: FsrsAdapter, days: StudyDays
) -> float:
    current = Memory(stability, memory.difficulty, memory.last_review_at)
    good = review_on(adapter, current, GOOD, now, days).stability
    return max(stability, stability + weight * (good - stability))


def partial_credit(
    from_skill: str,
    *,
    now: int,
    mode: CreditSetting,
    skills: Mapping[str, Skill],
    state_of: Callable[[str], SkillState | None],
    shadow_of: Callable[[str], SkillShadow | None],
    last_failure_at: Callable[[str], int | None],
    adapter: FsrsAdapter,
    days: StudyDays,
    targets: Mapping[str, float] | None = None,
    credited_today: Callable[[str], ImplicitCredit | None] = lambda _: None,
    adapter_of: Callable[[str], FsrsAdapter] | None = None,
) -> CreditResult:
    """ENG-7 after `from_skill` passed an explicit core-band review at `now`. `targets`
    (skill -> weight) replaces the encompassed skills: a multi-part problem credits a part's
    own skill after that part was answered right. `credited_today`: the target's largest
    credit already given this study day (I9: one credit per target per day). `adapter_of`:
    each target's own parameter set (decision 6); None: `adapter` for every target."""
    result = CreditResult()
    if mode == "off":
        return result
    chosen = credit_targets(from_skill, skills) if targets is None else targets
    for target, weight in sorted(chosen.items()):
        state = state_of(target)
        why = excluded(state, now=now, last_failure_at=last_failure_at(target))
        memory = memory_of(state)
        if why is not None or state is None or memory is None:
            result.skipped[target] = why or "learning"
            continue
        model = adapter if adapter_of is None else adapter_of(target)
        today = credited_today(target)
        if today is not None and today.weight >= weight:
            result.skipped[target] = "credited today"
            continue
        if mode == "shadow":
            shadow = shadow_of(target)
            before = (
                shadow.credited_stability
                if shadow is not None and shadow.credited_stability is not None
                else memory.stability
            )
            if today is not None and today.stability_before is not None:
                before = today.stability_before  # replace the day's smaller credit
            after = credited(before, memory, weight, now, model, days)
            result.shadows.append(SkillShadow(skill_id=target, credited_stability=after))
            plain = memory.stability
        else:
            before = memory.stability
            if today is not None and today.stability_before is not None:
                before = today.stability_before  # replace the day's smaller credit
            after = credited(before, memory, weight, now, model, days)
            plain = _explicit_stability(state)
            evidence: JsonObject = {
                **state.level_evidence,
                EXPLICIT: {"last_review_at": state.last_review_at, "stability": plain},
            }
            new = replace(state, stability=after, level_evidence=evidence)
            if after >= CREDIT_FORCE_RATIO * plain:
                new = with_adjust(
                    new,
                    not_after=days.day_of(now) + timedelta(days=1),
                    reason="Explicit review: its stability doubled from partial credit alone",
                )
            result.states.append(new)
        if after >= CREDIT_FORCE_RATIO * plain:
            result.forced.append(target)
        result.credits.append(
            ImplicitCredit(
                at=now,
                from_skill=from_skill,
                to_skill=target,
                weight=weight,
                mode="shadow" if mode == "shadow" else "on",
                stability_before=before,
                stability_after=after,
            )
        )
    return result


@dataclass(frozen=True, slots=True, kw_only=True)
class CreditSwitch:
    """I9: may credit On take effect? Credited predictions must beat plain ones on held-out
    log loss for the credited skills' next explicit core-band reviews."""

    allowed: bool
    reviews: int
    plain_log_loss: float | None
    credited_log_loss: float | None
    reason: str


def credit_switch(
    attempts: Iterable[Attempt], params_id: str | None, *, minimum: int = CREDIT_SWITCH_MIN
) -> CreditSwitch:
    """Score the plain and credited recalls logged at explicit reviews (extra["diagnosis"]
    ["shadow"], STA-4) against their outcomes (rating Hard or better). Held out: only
    reviews predicted with the parameters in force (`params_id`), which were fitted before
    those reviews happened. Allowed only with `minimum` reviews (800) and a paired 90%
    interval of the per-review log-loss difference (credited - plain) wholly below
    -CREDIT_SWITCH_MARGIN (ENG-7): a point estimate at 200 passed about half the time when
    credit was no better."""
    pairs: list[tuple[float, float, bool]] = []
    for a in attempts:
        diag = a.extra.get("diagnosis")
        shadow = diag.get("shadow") if isinstance(diag, dict) else None
        if a.voided_by is not None or a.rating is None or not isinstance(shadow, dict):
            continue
        if params_id is not None and a.params_id != params_id:
            continue
        pairs.append((float(shadow["plain"]), float(shadow["credited"]), a.rating >= HARD))
    n = len(pairs)
    if n == 0:
        return CreditSwitch(
            allowed=False,
            reviews=0,
            plain_log_loss=None,
            credited_log_loss=None,
            reason="no held-out reviews yet",
        )
    plain = _log_loss((p, ok) for p, _, ok in pairs)
    credited_ll = _log_loss((c, ok) for _, c, ok in pairs)
    diffs = [_loss(c, ok) - _loss(p, ok) for p, c, ok in pairs]
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1) if n > 1 else math.inf
    upper = mean + CREDIT_SWITCH_Z * math.sqrt(var / n)
    allowed = n >= minimum and upper < -CREDIT_SWITCH_MARGIN
    if n < minimum:
        reason = f"needs {minimum} held-out reviews, has {n}"
    elif not allowed:
        reason = "credited predictions do not beat plain ones by the margin (90% interval)"
    else:
        reason = "credited predictions beat plain ones by the margin (90% interval)"
    return CreditSwitch(
        allowed=allowed,
        reviews=n,
        plain_log_loss=plain,
        credited_log_loss=credited_ll,
        reason=reason,
    )


def _loss(p: float, ok: bool) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return -math.log(p if ok else 1 - p)


def _log_loss(rows: Iterable[tuple[float, bool]]) -> float:
    total = count = 0.0
    for p, ok in rows:
        p = min(1 - 1e-6, max(1e-6, p))
        total -= math.log(p if ok else 1 - p)
        count += 1
    return total / count if count else 0.0


def _explicit_stability(state: SkillState) -> float:
    raw = state.level_evidence.get(EXPLICIT)
    if isinstance(raw, dict) and raw.get("last_review_at") == state.last_review_at:
        return float(raw["stability"])
    return float(state.stability or 0.0)


def shadow_after_review(
    shadow: SkillShadow | None,
    before: SkillState | None,
    rating: int,
    at: int,
    adapter: FsrsAdapter,
    days: StudyDays,
) -> SkillShadow | None:
    """An explicit review moves the credited track too (same rating, same moment), so the
    two predictions stay comparable (STA-4). None when the skill has no shadow yet."""
    memory = memory_of(before)
    if shadow is None or shadow.credited_stability is None or memory is None:
        return None
    current = Memory(shadow.credited_stability, memory.difficulty, memory.last_review_at)
    after = review_on(adapter, current, rating, at, days)
    return replace(shadow, credited_stability=after.stability, updated_at=0)


def shadow_recalls(
    shadow: SkillShadow | None, before: SkillState | None, at: int, adapter: FsrsAdapter
) -> JsonObject | None:
    """Plain and credited predicted recall at an explicit review (the STA-4 comparison)."""
    memory = memory_of(before)
    if shadow is None or shadow.credited_stability is None or memory is None:
        return None
    credited_memory = Memory(shadow.credited_stability, memory.difficulty, memory.last_review_at)
    return {
        "plain": round(adapter.retrievability(memory, at), 6),
        "credited": round(adapter.retrievability(credited_memory, at), 6),
    }
