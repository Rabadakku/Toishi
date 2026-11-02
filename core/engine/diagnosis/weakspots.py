"""ENG-15 weak-spot finder.

Algorithm A (once a day): over the last 30 days, each graded problem's expected success is
p = sigma(theta - d(tier)), theta being the problem skill's Elo ability before the answer and
d the tier's anchor difficulty (ENG-5). Its residual o - p goes to every tagged skill: a
success with the tag weights (main 1, uses 0.4), a miss with its blame shares (the step
taps, or toward the weakest tagged skill) scaled to the same total, so a skill's residual
sum has mean zero for a student the model describes. Per skill:

    R = sum w (o - p),   V = sum w^2 p (1 - p),   z = R / sqrt(V + tau)

A skill is flagged when an exact one-sided tail test shows it clearly worse than expected:
P(sum w o <= observed) under the predicted p of each answer, w being the skill's tag weight
on the problem (outcome-independent, on a 0.05 grid; a miss counts only when the skill's
blame share reaches 0.15), is at most 0.025 (ADR-0019 item 9; with equal weights this is
the exact binomial tail, a Poisson-binomial one when the p differ; the old z <= -2
delivered 0.9-7.4% instead of its nominal 2.3%). It also needs at least five problems'
worth of evidence (sum of min(1, w)), misses on three different problems and on two
different days, and it is not already being diagnosed. z is still computed, for display
and ordering ties. Accepted slips carry no evidence. After a diagnostic set settles, the
skill's earlier residuals are excluded (only answers after it count).

Algorithm B: a flag schedules a diagnostic set of up to eight fresh problems where that
skill is the only main skill, at or below the student's level. Its problems are logged but
not rated one by one; a truncated sequential test (SPRT: success 0.85 against 0.55, alpha
0.10, beta 0.20) decides after each one: confirm the gap (a lapse, then checks on its
low-recall prerequisites, deepest first) or clear the flag, the rest of the set being
cancelled; when the set runs out, a positive log-likelihood ratio confirms. At most two
sets a week.
"""

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from core.engine.config import DAY_MS, TIER_DIFFICULTY
from core.engine.diagnosis.checks import counted_diagnostic_reason, level_tier
from core.engine.diagnosis.config import (
    DIAG_CONFIRM_MISSES,
    DIAG_SET_MAX,
    DIAG_SET_MIN,
    SPRT_ALPHA,
    SPRT_BETA,
    SPRT_P0,
    SPRT_P1,
    WEAK_MIN_DAYS,
    WEAK_MIN_EVIDENCE,
    WEAK_MIN_PROBLEMS,
    WEAK_TAIL_P,
    WEAK_TAU,
    WEAK_WINDOW_DAYS,
    WEEK_DAYS,
    WRONG_TIER_SURPRISE,
)
from core.engine.diagnosis.verdict import attempt_success, diagnosis_of
from core.engine.selection import SeenIndex, difficulty_of, form_key, p_correct
from core.model import Attempt, CardRef, DiagnosticSet, PendingCheck, Skill, SkillState, WeakSpot

DIAG_TARGET_P = 0.85  # reading: "at or below his level" aims at problems he should solve
MISS_SHARE_MIN = 0.15  # a miss counts toward a skill's "misses" when its weight reaches this
GRADED_KINDS = ("problem", "find-error")


def expected_success(a: Attempt) -> float | None:
    elo = a.extra.get("elo")
    if not isinstance(elo, dict) or a.tier is None:
        return None
    return 1.0 / (1.0 + math.exp(-(float(elo["theta"]) - TIER_DIFFICULTY[a.tier])))


def attempt_weights(a: Attempt) -> dict[str, float] | None:
    """Per-skill weights of one answer's residual (None: no evidence)."""
    d = diagnosis_of(a)
    o = attempt_success(a)
    if o is None or d.get("no_evidence"):
        return None
    raw = d.get("tags")
    tags = {str(k): float(v) for k, v in raw.items()} if isinstance(raw, dict) and raw else {}
    if not tags and a.skill_id:
        tags = {a.skill_id: 1.0}
    if o:
        return tags
    shares = d.get("blame")
    mass = sum(tags.values())
    if isinstance(shares, dict) and shares:
        return {str(k): float(v) * mass for k, v in shares.items()}
    return tags


def _tag_weights(a: Attempt) -> dict[str, float]:
    raw = diagnosis_of(a).get("tags")
    tags = {str(k): float(v) for k, v in raw.items()} if isinstance(raw, dict) and raw else {}
    return tags or ({a.skill_id: 1.0} if a.skill_id else {})


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillEvidence:
    skill_id: str
    z: float
    residual: float
    variance: float
    evidence: float
    misses: int  # distinct problems missed
    days: int  # distinct days with a miss
    answers: int
    tail: float = 1.0  # exact P(successes <= observed) under the predictions

    @property
    def flagged(self) -> bool:
        return (
            self.tail <= WEAK_TAIL_P
            and self.evidence >= WEAK_MIN_EVIDENCE
            and self.misses >= WEAK_MIN_PROBLEMS
            and self.days >= WEAK_MIN_DAYS
        )


def skill_evidence(
    attempts: Iterable[Attempt],
    *,
    now: int,
    cutoff_of: Callable[[str], int | None] = lambda _k: None,
    tau: float = WEAK_TAU,
) -> dict[str, SkillEvidence]:
    since = now - WEAK_WINDOW_DAYS * DAY_MS
    acc: dict[str, list[float]] = {}
    trials: dict[str, list[tuple[float, float, bool]]] = {}  # (w, p, success): exact tail
    missed: dict[str, set[str]] = {}
    days: dict[str, set[str]] = {}
    for a in attempts:
        if a.voided_by is not None or not a.final or a.at < since or a.at > now:
            continue
        if a.card_kind not in GRADED_KINDS or a.extra.get("stage") == "example":
            continue
        weights = attempt_weights(a)
        p = expected_success(a)
        o = attempt_success(a)
        if weights is None or p is None or o is None:
            continue
        tag_weights = _tag_weights(a)
        mass = sum(tag_weights.values()) or 1.0
        for k, w in weights.items():
            cutoff = cutoff_of(k)
            if w <= 0 or (cutoff is not None and a.at <= cutoff):
                continue
            row = acc.setdefault(k, [0.0, 0.0, 0.0, 0.0])
            row[0] += w * ((1.0 if o else 0.0) - p)
            row[1] += w * w * p * (1.0 - p)
            row[2] += min(1.0, w)
            row[3] += 1
            # The exact tail needs a weight that does not depend on the outcome: the skill's
            # tag weight on the problem (main 1, uses 0.4). A miss counts for the skill only
            # when its blame share reaches MISS_SHARE_MIN (it says nothing about the others).
            if o or w / mass >= MISS_SHARE_MIN:
                trials.setdefault(k, []).append((tag_weights.get(k, w), p, bool(o)))
            if not o and w >= MISS_SHARE_MIN:
                missed.setdefault(k, set()).add(a.card_id)
                days.setdefault(k, set()).add(a.study_day or str(a.at // DAY_MS))
    return {
        k: SkillEvidence(
            skill_id=k,
            z=r / math.sqrt(v + tau),
            residual=r,
            variance=v,
            evidence=e,
            misses=len(missed.get(k, ())),
            days=len(days.get(k, ())),
            answers=int(n),
            tail=lower_tail(trials.get(k, [])),
        )
        for k, (r, v, e, n) in acc.items()
    }


TAIL_GRID = 0.05  # weights are rounded to this grid for the exact distribution


def lower_tail(trials: Sequence[tuple[float, float, bool]]) -> float:
    """Exact P(sum w_i O_i <= observed) for independent answers O_i ~ Bernoulli(p_i) with
    weights w_i rounded to TAIL_GRID: the exact binomial tail when every w and p are equal,
    a Poisson-binomial one when only the p differ. 1.0 with no evidence."""
    units = [(round(w / TAIL_GRID), p, ok) for w, p, ok in trials]
    units = [(u, p, ok) for u, p, ok in units if u > 0]
    if not units:
        return 1.0
    dist = [1.0]  # dist[s] = P(weighted successes so far = s grid units)
    for u, p, _ in units:
        nxt = [0.0] * (len(dist) + u)
        for s, q in enumerate(dist):
            if q:
                nxt[s] += q * (1.0 - p)
                nxt[s + u] += q * p
        dist = nxt
    observed = sum(u for u, _, ok in units if ok)
    return min(1.0, sum(dist[: observed + 1]))


def find_weak_spots(
    attempts: Iterable[Attempt],
    *,
    now: int,
    busy: Iterable[str] = (),
    cutoff_of: Callable[[str], int | None] = lambda _k: None,
) -> list[SkillEvidence]:
    """Algorithm A: flagged skills, smallest tail first (`busy`: already diagnosed)."""
    skip = set(busy)
    found = skill_evidence(attempts, now=now, cutoff_of=cutoff_of)
    flagged = (e for k, e in found.items() if e.flagged and k not in skip)
    return sorted(flagged, key=lambda e: (e.tail, e.z))


def residual_cutoffs(spots: Iterable[WeakSpot]) -> dict[str, int]:
    """Per skill, the time its last diagnosis settled: earlier residuals are excluded."""
    out: dict[str, int] = {}
    for s in spots:
        if s.status != "open" and s.resolved_at is not None:
            out[s.skill_id] = max(out.get(s.skill_id, 0), s.resolved_at)
    return out


def busy_skills(spots: Iterable[WeakSpot], sets: Iterable[DiagnosticSet]) -> set[str]:
    return {s.skill_id for s in spots if s.status == "open"} | {
        d.skill_id for d in sets if d.status in ("pending", "active")
    }


def sets_left_this_week(sets: Iterable[DiagnosticSet], *, now: int, per_week: int) -> int:
    recent = sum(1 for d in sets if now - d.created_at < WEEK_DAYS * DAY_MS)
    return max(0, per_week - recent)


# ---------------------------------------------------------------- Algorithm B


def diagnostic_cards(
    refs: Sequence[CardRef],
    *,
    skill: Skill,
    state: SkillState | None,
    now: int,
    seen: SeenIndex,
    hidden: Iterable[str] = (),
) -> tuple[str, ...] | None:
    """Up to eight fresh problems (DIAG_SET_MAX) where `skill` is the only main skill, at
    or below the student's level, different forms first, those the model expects solved
    (predicted success nearest 0.85) first: a real gap then shows as misses. The sequential
    test usually stops after four to six. None when fewer than three exist."""
    top = level_tier(skill, state)
    theta = state.elo_theta if state is not None else 0.0
    skip = set(hidden)
    pool = [
        r
        for r in refs
        if r.kind == "problem"
        and r.status == "active"
        and r.skill_id == skill.id
        and r.tier <= top
        and r.id not in skip
    ]

    def stale(r: CardRef) -> bool:
        at = seen.card_seen_at.get(r.id)
        return at is not None and now - at < 90 * DAY_MS

    def p_of(r: CardRef) -> float:
        return p_correct(theta, difficulty_of(form_key(r.id, r.template_id), r.tier, seen.forms))

    pool.sort(key=lambda r: (stale(r), round(abs(p_of(r) - DIAG_TARGET_P), 6), r.id))
    chosen: list[CardRef] = []
    forms: set[str] = set()
    for r in pool:  # one per form first, then fill
        form = form_key(r.id, r.template_id)
        if form not in forms:
            chosen.append(r)
            forms.add(form)
        if len(chosen) == DIAG_SET_MAX:
            break
    for r in pool:
        if len(chosen) == DIAG_SET_MAX:
            break
        if r not in chosen:
            chosen.append(r)
    return tuple(r.id for r in chosen) if len(chosen) >= DIAG_SET_MIN else None


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticPlan:
    """A flag and its set, ready to write (the weak spot first: the set links to its id)."""

    finding: SkillEvidence
    card_ids: tuple[str, ...]
    reason: str

    def weak_spot(self, *, now: int, study_day: str) -> WeakSpot:
        f = self.finding
        return WeakSpot(
            skill_id=f.skill_id,
            flagged_at=now,
            study_day=study_day,
            z=round(f.z, 4),
            evidence=round(f.evidence, 4),
            misses=f.misses,
            problems=f.answers,
            days=f.days,
        )

    def records(
        self, *, weak_spot_id: int | None, now: int
    ) -> tuple[DiagnosticSet, list[PendingCheck]]:
        diag = DiagnosticSet(
            skill_id=self.finding.skill_id,
            weak_spot_id=weak_spot_id,
            created_at=now,
            card_ids=self.card_ids,
        )
        checks = [
            PendingCheck(
                created_at=now,
                attempt_id=None,
                skill_id=self.finding.skill_id,
                kind="diagnostic",
                card_id=card,
                after_items=0,
                not_before_at=now,
                depth=0,
                reason=self.reason,
            )
            for card in self.card_ids
        ]
        return diag, checks


def plan_diagnostics(
    findings: Sequence[SkillEvidence],
    *,
    budget: int,
    skills: Mapping[str, Skill],
    cards_for: Callable[[str], tuple[str, ...] | None],
) -> list[DiagnosticPlan]:
    plans: list[DiagnosticPlan] = []
    for f in findings:
        if len(plans) >= budget:
            break
        cards = cards_for(f.skill_id)
        if cards is None:
            continue
        # the sentence Diagnosis.reason composed from the weak spot before checks kept one
        reason = counted_diagnostic_reason(
            skills, f.skill_id, misses=f.misses, problems=f.answers, days=f.days
        )
        plans.append(DiagnosticPlan(finding=f, card_ids=cards, reason=reason))
    return plans


Decision = Literal["confirmed", "cleared"]


SPRT_UPPER = math.log((1 - SPRT_BETA) / SPRT_ALPHA)  # confirm at or above
SPRT_LOWER = math.log(SPRT_BETA / (1 - SPRT_ALPHA))  # clear at or below
SPRT_MISS = math.log((1 - SPRT_P1) / (1 - SPRT_P0))
SPRT_SUCCESS = math.log(SPRT_P1 / SPRT_P0)


def sprt_llr(misses: int, successes: int) -> float:
    """Log-likelihood ratio of "weak" (success SPRT_P1) against "fine" (SPRT_P0)."""
    return misses * SPRT_MISS + successes * SPRT_SUCCESS


def diagnostic_step(diag: DiagnosticSet, *, missed: bool) -> tuple[DiagnosticSet, Decision | None]:
    """One answered set problem, then the sequential test (ENG-15, ADR-0019 item 9):
    confirm when the log-likelihood ratio reaches SPRT_UPPER, clear when it falls to
    SPRT_LOWER; when a full set of eight runs out, a positive ratio confirms. A shorter set
    (the pool had fewer fresh problems) ends on the fixed-set rule: two misses confirm."""
    done = diag.done + 1
    misses = diag.misses + (1 if missed else 0)
    llr = sprt_llr(misses, done - misses)
    size = min(len(diag.card_ids), DIAG_SET_MAX)
    remaining = max(0, size - done)
    full = size >= DIAG_SET_MAX
    decision: Decision | None = None
    if llr >= SPRT_UPPER - 1e-12:
        decision = "confirmed"
    elif llr <= SPRT_LOWER + 1e-12:
        decision = "cleared"
    elif full:
        # The truncated test ends on the sign of the ratio; decide as soon as no remaining
        # answers can change that (the same outcome, fewer problems).
        if llr + remaining * SPRT_MISS <= 0:
            decision = "cleared"
        elif llr + remaining * SPRT_SUCCESS > 0:
            decision = "confirmed"
    elif misses >= DIAG_CONFIRM_MISSES:
        decision = "confirmed"  # a short set (a small pool) ends on the fixed-set rule
    elif misses + remaining < DIAG_CONFIRM_MISSES:
        decision = "cleared"
    status = decision or "active"
    return replace(diag, done=done, misses=misses, status=status), decision


# ---------------------------------------------------------------- possible wrong tier (ENG-5)


@dataclass(frozen=True, slots=True, kw_only=True)
class TierFlagNote:
    """A template or family whose recent results keep surprising the model the same way.
    A note for review only: tiers never change automatically."""

    family: str
    direction: Literal["harder-than-tier", "easier-than-tier"]
    card_ids: tuple[str, ...]


def family_of(a: Attempt) -> str:
    """A template's variants are one family; hand-written cards group by skill and tier."""
    return f"template:{a.template_id}" if a.template_id else f"cards:{a.skill_id}:t{a.tier}"


def wrong_tier_flags(attempts: Sequence[Attempt], *, now: int, run: int = 3) -> list[TierFlagNote]:
    """A run of `run` surprising results in a row on one family (|o - p| >= 0.6, same
    direction). Misses traced to a confirmed skill gap (their check failed) and accepted
    slips are not surprises about the problem, so they are left out."""
    gaps: set[int] = set()
    for a in attempts:
        resolved = diagnosis_of(a).get("resolved")
        if isinstance(resolved, dict) and resolved.get("confirmed") and resolved.get("trigger"):
            gaps.add(int(resolved["trigger"]))
    since = now - WEAK_WINDOW_DAYS * 3 * DAY_MS
    runs: dict[str, list[tuple[float, str]]] = {}
    for a in sorted(attempts, key=lambda x: x.at):
        if a.voided_by is not None or not a.final or a.at < since or a.card_kind != "problem":
            continue
        elo = a.extra.get("elo")
        if not isinstance(elo, dict) or diagnosis_of(a).get("no_evidence") or a.id in gaps:
            continue
        runs.setdefault(family_of(a), []).append((float(elo["o"]) - float(elo["p"]), a.card_id))
    out: list[TierFlagNote] = []
    for family, results in sorted(runs.items()):
        last = results[-run:]
        if len(last) < run:
            continue
        if all(s <= -WRONG_TIER_SURPRISE for s, _ in last):
            direction: Literal["harder-than-tier", "easier-than-tier"] = "harder-than-tier"
        elif all(s >= WRONG_TIER_SURPRISE for s, _ in last):
            direction = "easier-than-tier"
        else:
            continue
        cards = tuple(dict.fromkeys(c for _, c in last))
        out.append(TierFlagNote(family=family, direction=direction, card_ids=cards))
    return out
