"""Held verdicts and the careless-slip cap.

When a miss is routed to a check (a step tap, Step 0, a second slip, an above-level miss),
the problem's own rating depends on how the check goes, so it is held: the skill keeps the
FSRS memory it had before the miss (no event yet), the miss's Level evidence waits in the
hold, and the skill is due the next study day (as after a lapse) unless the check settles
it first. The hold lives in SkillState.level_evidence["hold"] and is valid only while
`last_review_at` is unchanged. Settling applies the final rating at the miss's own time,
and since a wrong final answer never counts as a pass (ADR-0014) that rating is Again
whatever the check shows. The check decides only whether Level and the leech counter see
it: an Again that is "excused" (a passed check, or a miss the check traced to another
skill) moves FSRS but neither demotes Level nor counts toward a leech.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any

from core.engine.config import DAY_MS, RULES_VERSION, EngineSettings
from core.engine.days import StudyDays
from core.engine.diagnosis.config import SLIP_CLEAN_RUN, SLIP_MIN_RECALL, SLIP_WINDOW_DAYS
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.level import Evidence, update_level
from core.engine.lifecycle import (
    ADJUST,
    adjust_of,
    due_at,
    in_learning_phase,
    review_answer,
    with_adjust,
)
from core.model import Attempt, JsonObject, ReviewEvent, SkillState

__all__ = ["ADJUST", "adjust_of", "with_adjust"]

HOLD = "hold"
EXAMPLE_FIRST = "example_first"


def hold_of(state: SkillState | None) -> JsonObject | None:
    raw = None if state is None else state.level_evidence.get(HOLD)
    if not isinstance(raw, dict) or state is None:
        return None
    return raw if raw.get("last_review_at") == state.last_review_at else None


def without(state: SkillState, *keys: str) -> SkillState:
    if not any(k in state.level_evidence for k in keys):
        return state
    return replace(
        state, level_evidence={k: v for k, v in state.level_evidence.items() if k not in keys}
    )


def place_hold(
    before: SkillState,
    graded: SkillState,
    *,
    at: int,
    today: date,
    entry: Evidence,
    check_skill: str,
    kind: str,
    pass_rating: int | None,
    reason: str,
) -> SkillState:
    """The skill as it was before the miss (FSRS memory, Level), with the miss's Elo update
    kept and the verdict waiting for its check. Due the next study day at the latest."""
    hold: JsonObject = {
        "at": at,
        "day": today.isoformat(),
        "last_review_at": before.last_review_at,
        "entry": entry.as_json(),
        "check_skill": check_skill,
        "kind": kind,
        "pass_rating": pass_rating,
    }
    before = without(before, ADJUST)
    state = replace(
        before,
        elo_theta=graded.elo_theta,
        elo_n=graded.elo_n,
        level_evidence={**before.level_evidence, HOLD: hold},
    )
    tomorrow = today + timedelta(days=1)
    return with_adjust(state, not_before=tomorrow, not_after=tomorrow, reason=reason)


@dataclass(frozen=True, slots=True, kw_only=True)
class Settled:
    state: SkillState
    event: ReviewEvent | None = None
    lapse: bool = False
    leech: bool = False
    rating: int | None = None


def settle(
    state: SkillState,
    rating: int | None,
    *,
    adapter: FsrsAdapter,
    days: StudyDays,
    settings: EngineSettings,
    exam_tier: int,
    targets: Mapping[int, int | None],
    retention: float,
    excused: bool = False,
) -> Settled:
    """Settle a held verdict with `rating` at the miss's time (None: no FSRS event).
    `excused`: Level and the leech counter ignore this Again (ADR-0014)."""
    hold = hold_of(state)
    if hold is None:
        return Settled(state=state)
    base = without(state, HOLD)
    if adjust_of(base) is not None:
        base = without(base, ADJUST)
    at = int(hold["at"])
    if rating is None:
        return Settled(state=replace(base, due_at=due_at(base, retention, adapter, days)))
    reviewed = review_answer(
        base,
        rating=rating,
        at_ms=at,
        adapter=adapter,
        days=days,
        leech_lapses=settings.leech_lapses,
        excused=excused,
    )
    new = reviewed.state
    event = None
    if reviewed.fsrs_event:
        event = ReviewEvent(
            at=at,
            target_kind="skill",
            target_id=state.skill_id,
            rating=rating,
            rules_version=RULES_VERSION,
            params_id=adapter.params_id,
            retention=retention,
            predicted_recall=None,  # settled after a check: kept out of ENG-11's bins
        )
    if not in_learning_phase(new):
        entry = replace(Evidence.from_json(hold["entry"]), rating=None if excused else rating)
        change = update_level(
            new,
            entry,
            exam_tier=exam_tier,
            targets=targets,
            correct_in_a_row=settings.correct_in_a_row,
        )
        new = replace(
            new,
            level=change.level,
            level_at=at if change.changed else new.level_at,
            shaky=change.shaky,
            shaky_reviews=change.shaky_reviews,
            learning_streak=change.learning_streak,
            level_evidence=change.evidence,
        )
    new = replace(new, due_at=due_at(new, retention, adapter, days))
    return Settled(
        state=new, event=event, lapse=reviewed.lapse, leech=reviewed.leech, rating=rating
    )


# ---------------------------------------------------------------- careless slips


@dataclass(frozen=True, slots=True, kw_only=True)
class SlipDecision:
    accepted: bool  # an excused Again: Level and the leech counter ignore it
    second: bool  # a second slip within 30 days: a step error with a check
    reason: str


def attempt_success(a: Attempt) -> bool | None:
    elo = a.extra.get("elo")
    return None if not isinstance(elo, dict) else bool(elo.get("o"))


def diagnosis_of(a: Attempt) -> dict[str, Any]:
    raw = a.extra.get("diagnosis")
    return raw if isinstance(raw, dict) else {}


def slip_decision(history: Sequence[Attempt], *, at: int, recall: float | None) -> SlipDecision:
    """Careless slip or misread: accepted only when the skill is strong (recall >= 0.90,
    its last two attempts correct), at most once per skill per 30 days; a second slip
    within 30 days of an accepted one becomes a step error with a check."""
    prior = [a for a in history if a.final and a.voided_by is None and a.at < at]
    window = SLIP_WINDOW_DAYS * DAY_MS
    if any(diagnosis_of(a).get("slip") == "accepted" and at - a.at < window for a in prior):
        return SlipDecision(accepted=False, second=True, reason="second slip within 30 days")
    graded = [a for a in prior if attempt_success(a) is not None][-SLIP_CLEAN_RUN:]
    clean = len(graded) == SLIP_CLEAN_RUN and all(attempt_success(a) for a in graded)
    if recall is not None and recall >= SLIP_MIN_RECALL and clean:
        return SlipDecision(accepted=True, second=False, reason="slip within the cap")
    return SlipDecision(accepted=False, second=False, reason="skill not strong enough for a slip")
