"""Core band (ENG-4) and Elo problem selection (ENG-5).

Problem difficulty is kept per problem form (a template's variants share one, a hand-written
card is its own form). It starts at its tier's anchor and moves at most 0.05 per answer and
0.5 in total; a run of surprising results flags a possible wrong tier instead. Each
answer's Elo numbers live in Attempt.extra["elo"], so undoing an answer (which voids the
attempt) also undoes its difficulty change. Elo never changes the FSRS schedule.
"""

import hashlib
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from core.engine.config import (
    DAY_MS,
    ELO_A,
    ELO_B,
    ELO_MAX_DRIFT_PER_ANSWER,
    ELO_MAX_DRIFT_TOTAL,
    ELO_TARGET_P,
    PARAMS_SKIP_DAYS,
    SEEN_SKIP_DAYS,
    TIER_DIFFICULTY,
)
from core.model import Attempt, CardRef

TierFlag = Literal["harder-than-tier", "easier-than-tier"]
FLAG_RUN = 3
FLAG_SURPRISE = 0.6
SAME_FORM_PENALTY = 0.10
SAME_SOURCE_PENALTY = 0.05
PROBLEM_KINDS = ("problem",)
LEARNING_TIERS = (1, 2)


def form_key(card_id: str, template_id: str | None) -> str:
    """A problem form: a template's variants share one; any other card is its own form."""
    return f"template:{template_id}" if template_id else f"card:{card_id}"


# ---------------------------------------------------------------- core band (ENG-4)


def core_band(stability: float | None, *, exam_window: bool = False) -> tuple[int, ...]:
    """Tiers that produce FSRS events. Learning (no card yet) uses tiers 1 and 2; inside an
    exam window an in-scope skill uses tier 3."""
    if exam_window:
        return (3,)
    if stability is None or stability < 7:
        return (1, 2)
    if stability < 30:
        return (2, 3)
    if stability <= 90:
        return (3,)
    return (3, 4)


def exam_band(exam_tier: int | None) -> tuple[int, ...]:
    """The rated band inside an exam window and on a practice test (ENG-4, QUE-19): the
    skill's exam tier, together with tier 3, which the window serves, so neither is off band."""
    lo, hi = sorted((3, exam_tier or 3))
    return tuple(range(lo, hi + 1))


def is_below_band(tier: int, band: Sequence[int]) -> bool:
    """ENG-4: below the core band (the Lighter set, a check under the band)."""
    return tier < min(band)


def stretch_tier(stability: float | None, *, elite: bool) -> int | None:
    """The occasional stretch tier above the band (tier 5 only with Elite problems on)."""
    if stability is None or stability < 7:
        return 3
    if stability <= 90:
        return 4
    return 5 if elite else None


def is_stretch(tier: int, band: Sequence[int]) -> bool:
    return tier > max(band)


def stretch_allowed(
    *,
    reviews_so_far: int,
    stretches_so_far: int,
    elite_used: bool,
    tier: int | None,
    fraction: float,
) -> bool:
    """At most `fraction` (10%) of a session's reviews, and one Elite problem per session."""
    if tier is None or fraction <= 0:
        return False
    if tier == 5 and elite_used:
        return False
    return (stretches_so_far + 1) <= fraction * (reviews_so_far + 1)


def wants_stretch(skill_id: str, study_day: str, fraction: float) -> bool:
    """A stable, even spread of stretch picks: about `fraction` of skill-days."""
    digest = hashlib.sha256(f"stretch|{skill_id}|{study_day}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64 < fraction


# ---------------------------------------------------------------- Elo (ENG-5)


def p_correct(theta: float, difficulty: float) -> float:
    return 1.0 / (1.0 + math.exp(-(theta - difficulty)))


@dataclass(frozen=True, slots=True, kw_only=True)
class EloUpdate:
    form: str
    p: float
    theta_before: float
    theta_after: float
    n_after: int
    d_before: float
    d_after: float
    outcome: int
    tier_flag: TierFlag | None = None

    def as_extra(self) -> dict[str, object]:
        return {
            "form": self.form,
            "p": round(self.p, 6),
            "theta": round(self.theta_before, 6),
            "d": round(self.d_before, 6),
            "d_after": round(self.d_after, 6),
            "o": self.outcome,
        }


@dataclass(frozen=True, slots=True)
class FormStats:
    difficulty: float
    answers: int
    surprises: tuple[float, ...] = ()  # o - p of recent answers, oldest first


def form_stats(history: Iterable[Attempt]) -> dict[str, FormStats]:
    """Current difficulty, answer count and recent surprises per form, from the attempt
    log (non-voided attempts whose extra holds the Elo numbers)."""
    out: dict[str, FormStats] = {}
    for a in history:
        elo = a.extra.get("elo") if a.voided_by is None else None
        if not isinstance(elo, dict):
            continue
        key = str(elo["form"])
        prev = out.get(key)
        surprise = float(elo["o"]) - float(elo["p"])
        surprises = (*(prev.surprises if prev else ()), surprise)[-FLAG_RUN:]
        out[key] = FormStats(float(elo["d_after"]), (prev.answers if prev else 0) + 1, surprises)
    return out


def difficulty_of(form: str, tier: int, stats: Mapping[str, FormStats]) -> float:
    found = stats.get(form)
    return found.difficulty if found is not None else TIER_DIFFICULTY[tier]


def elo_update(
    *,
    theta: float,
    n: int,
    form: str,
    tier: int,
    success: bool,
    stats: Mapping[str, FormStats],
) -> EloUpdate:
    """theta += a/(1 + b n) (o - P); the form's difficulty moves the other way, by at most
    0.05 per answer and 0.5 from its tier anchor."""
    d = difficulty_of(form, tier, stats)
    p = p_correct(theta, d)
    o = 1 if success else 0
    theta_after = theta + ELO_A / (1.0 + ELO_B * n) * (o - p)
    prior = stats.get(form)
    k = ELO_A / (1.0 + ELO_B * (prior.answers if prior else 0))
    step = max(-ELO_MAX_DRIFT_PER_ANSWER, min(ELO_MAX_DRIFT_PER_ANSWER, -k * (o - p)))
    anchor = TIER_DIFFICULTY[tier]
    d_after = max(anchor - ELO_MAX_DRIFT_TOTAL, min(anchor + ELO_MAX_DRIFT_TOTAL, d + step))
    surprises = (*(prior.surprises if prior else ()), o - p)[-FLAG_RUN:]
    flag: TierFlag | None = None
    if len(surprises) == FLAG_RUN:
        if all(s <= -FLAG_SURPRISE for s in surprises):
            flag = "harder-than-tier"
        elif all(s >= FLAG_SURPRISE for s in surprises):
            flag = "easier-than-tier"
    return EloUpdate(
        form=form,
        p=p,
        theta_before=theta,
        theta_after=theta_after,
        n_after=n + 1,
        d_before=d,
        d_after=d_after,
        outcome=o,
        tier_flag=flag,
    )


# ---------------------------------------------------------------- selection (ENG-5)


@dataclass(frozen=True, slots=True, kw_only=True)
class SeenIndex:
    """When cards and template parameter sets were last served, plus form stats."""

    card_seen_at: Mapping[str, int] = field(default_factory=dict)
    params_seen_at: Mapping[tuple[str, int], int] = field(default_factory=dict)
    forms: Mapping[str, FormStats] = field(default_factory=dict)

    @classmethod
    def from_attempts(
        cls, history: Iterable[Attempt], card_seen_at: Mapping[str, int] | None = None
    ) -> SeenIndex:
        history = list(history)
        cards: dict[str, int] = dict(card_seen_at or {})
        params: dict[tuple[str, int], int] = {}
        for a in history:
            if a.voided_by is not None:
                continue
            cards[a.card_id] = max(cards.get(a.card_id, 0), a.at)
            if a.template_id is not None and a.seed is not None:
                key = (a.template_id, a.seed)
                params[key] = max(params.get(key, 0), a.at)
        return cls(card_seen_at=cards, params_seen_at=params, forms=form_stats(history))


@dataclass(frozen=True, slots=True, kw_only=True)
class Pick:
    card: CardRef
    p: float  # predicted success
    stretch: bool
    relaxed: tuple[str, ...] = ()  # rules dropped to find a problem


def pick_problem(
    refs: Sequence[CardRef],
    *,
    theta: float,
    tiers: Sequence[int],
    now_ms: int,
    seen: SeenIndex,
    last: CardRef | None = None,
    hidden: Iterable[str] = (),
    stretch: bool = False,
    kinds: Sequence[str] = PROBLEM_KINDS,
    target_p: float = ELO_TARGET_P,
    today_start_ms: int | None = None,
) -> Pick | None:
    """The problem in the given tiers whose predicted success is closest to `target_p`
    (0.80; rated reviews aim at the course's desired retention, ADR-0014). Skips
    cards seen in 90 days and template parameter sets used in 180 days, and prefers a
    different form and source from the skill's last problem. When nothing qualifies it
    relaxes, in order: the 90/180-day rules, then the tiers (nearest first). `kinds`: the
    card kinds to pick from (full problems; which-method or find-the-error items on request).
    `today_start_ms`: the start of the current study day; a card (or template parameter set)
    served since then is never picked, whatever is relaxed. None when nothing qualifies."""
    hidden_set = set(hidden)
    pool = [r for r in refs if r.kind in kinds and r.status == "active"]
    pool = [r for r in pool if r.id not in hidden_set]
    if today_start_ms is not None:
        pool = [r for r in pool if not seen_since(r, seen, today_start_ms)]
    if not pool:
        return None

    attempts: list[tuple[tuple[int, ...], bool, tuple[str, ...]]] = [
        (tuple(tiers), True, ()),
        (tuple(tiers), False, ("recently seen",)),
    ]
    for distance in range(1, 5):
        widened = sorted(
            {t + d for t in tiers for d in (-distance, distance) if 1 <= t + d <= 5} | set(tiers)
        )
        attempts.append((tuple(widened), True, ("tier widened",)))
        attempts.append((tuple(widened), False, ("tier widened", "recently seen")))
    for allowed, need_fresh, relaxed in attempts:
        candidates = [
            r for r in pool if r.tier in allowed and (is_fresh(r, seen, now_ms) or not need_fresh)
        ]
        if not need_fresh and last is not None and len(candidates) > 1:
            candidates = [r for r in candidates if r.id != last.id]
        if candidates:
            best = min(candidates, key=lambda r: _score(r, theta, seen, last, need_fresh, target_p))
            p = p_correct(
                theta, difficulty_of(form_key(best.id, best.template_id), best.tier, seen.forms)
            )
            return Pick(card=best, p=p, stretch=stretch, relaxed=relaxed)
    return None


def is_fresh(ref: CardRef, seen: SeenIndex, now_ms: int) -> bool:
    """ENG-5: not served in 90 days, and its template parameter set not used in 180. One
    helper for every picker (reviews and checks)."""
    seen_at = seen.card_seen_at.get(ref.id)
    if seen_at is not None and now_ms - seen_at < SEEN_SKIP_DAYS * DAY_MS:
        return False
    if ref.template_id is not None and ref.seed is not None:
        used = seen.params_seen_at.get((ref.template_id, ref.seed))
        if used is not None and now_ms - used < PARAMS_SKIP_DAYS * DAY_MS:
            return False
    return True


def seen_since(ref: CardRef, seen: SeenIndex, since_ms: int) -> bool:
    """Served (the card or its template parameter set) since `since_ms`: with the study
    day's start, the no-card-twice-in-a-study-day rule (ENG-5) for every picker."""
    if seen.card_seen_at.get(ref.id, since_ms - 1) >= since_ms:
        return True
    if ref.template_id is not None and ref.seed is not None:
        return seen.params_seen_at.get((ref.template_id, ref.seed), since_ms - 1) >= since_ms
    return False


def learning_pool_size(
    refs: Iterable[CardRef], *, hidden: Iterable[str] = (), kinds: Sequence[str] = PROBLEM_KINDS
) -> int:
    """Distinct problems a learning phase can serve (ENG-2: active tier 1-2 problems; with
    none, the picker widens the tiers, so then every active problem of the skill)."""
    hidden_set = set(hidden)
    active = [
        r for r in refs if r.kind in kinds and r.status == "active" and r.id not in hidden_set
    ]
    learning = {r.id for r in active if r.tier in LEARNING_TIERS}
    return len(learning or {r.id for r in active})


def learning_streak_needed(correct_in_a_row: int, pool: int | None) -> int:
    """ENG-2: `correct_in_a_row` clean answers in a row, or every distinct problem the
    skill has when its pool is smaller (a card is never served twice in a study day), so a
    skill with a tiny pool can still be learned. None: the pool is unknown."""
    if not pool:  # unknown, or no tier 1-2 problem at all (the picker widens the tiers)
        return correct_in_a_row
    return max(1, min(correct_in_a_row, pool))


def _score(
    ref: CardRef,
    theta: float,
    seen: SeenIndex,
    last: CardRef | None,
    need_fresh: bool,
    target_p: float = ELO_TARGET_P,
) -> tuple[float, int, str]:
    form = form_key(ref.id, ref.template_id)
    p = p_correct(theta, difficulty_of(form, ref.tier, seen.forms))
    score = abs(p - target_p)
    if last is not None:
        if form == form_key(last.id, last.template_id):
            score += SAME_FORM_PENALTY
        if ref.source == last.source:
            score += SAME_SOURCE_PENALTY
    # Among stale candidates the least recently seen goes first.
    seen_at = 0 if need_fresh else seen.card_seen_at.get(ref.id, 0)
    return (round(score, 9), seen_at, ref.id)
