"""ENG-10: Level (evidence only) and Recall (FSRS, fades with time).

Level evidence is a short log in SkillState.level_evidence["log"], one entry per graded
answer outside the learning phase, holding only what the rules need. A demotion clears it:
getting a Level back means meeting its rule again with new evidence.

- Learning: started; the learning phase isn't passed (or a miss while Learned; it comes
  back after `correct_in_a_row` clean answers in a row, like the learning phase's rule).
- Learned: the learning phase passed. Time is ignored.
- Exam-level: clean at the exam tier on >= 2 different days, and the median of the last
  three timed clean exam-tier times at or under that tier's target.
- Mastered: >= 3 successful reviews on different days, one of them after >= 7 days at a
  predicted recall <= 0.90; successes on >= 2 forms; a success above the exam tier or in
  a mixed check-up; the last three timed clean answers each at target pace.
- Shaky: one miss (an Again) on Exam-level/Mastered; a second miss within the next three
  rated reviews drops one Level; three without a miss clear it. Fading is recall < 0.80.
"""

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from core.engine.config import (
    AGAIN,
    FADING_RECALL,
    HARD,
    LEVEL_LOG_LIMIT,
    MASTERED_MAX_RECALL,
    MASTERED_MIN_ELAPSED_DAYS,
    SHAKY_WINDOW,
)
from core.model import JsonObject, LevelName, SkillState

ORDER: tuple[LevelName, ...] = ("learning", "learned", "exam", "mastered")


def rank(level: LevelName | None) -> int:
    return -1 if level is None else ORDER.index(level)


@dataclass(frozen=True, slots=True, kw_only=True)
class Evidence:
    """One graded answer as Level sees it."""

    day: str  # study day, ISO
    tier: int
    clean: bool  # correct on the first attempt, no hints
    rating: int | None  # None: no FSRS event (stretch, reinforcement)
    speed_ms: int | None  # None: untimed or excluded
    form: str
    recall: float | None  # predicted recall at review
    elapsed_days: float | None  # since the previous review
    checkup: bool = False
    above_exam_tier: bool = False

    @property
    def rated_success(self) -> bool:
        return self.rating is not None and self.rating >= HARD

    @property
    def miss(self) -> bool:
        return self.rating == AGAIN

    def as_json(self) -> JsonObject:
        return {
            "d": self.day,
            "t": self.tier,
            "ok": self.clean,
            "r": self.rating,
            "ms": self.speed_ms,
            "f": self.form,
            "p": None if self.recall is None else round(self.recall, 4),
            "e": None if self.elapsed_days is None else round(self.elapsed_days, 3),
            "c": self.checkup,
            "x": self.above_exam_tier,
        }

    @classmethod
    def from_json(cls, raw: Mapping[str, Any]) -> Evidence:
        return cls(
            day=str(raw["d"]),
            tier=int(raw["t"]),
            clean=bool(raw["ok"]),
            rating=None if raw.get("r") is None else int(raw["r"]),
            speed_ms=None if raw.get("ms") is None else int(raw["ms"]),
            form=str(raw["f"]),
            recall=None if raw.get("p") is None else float(raw["p"]),
            elapsed_days=None if raw.get("e") is None else float(raw["e"]),
            checkup=bool(raw.get("c", False)),
            above_exam_tier=bool(raw.get("x", False)),
        )


def evidence_log(state: SkillState) -> list[Evidence]:
    return [Evidence.from_json(e) for e in state.level_evidence.get("log", [])]


def exam_level_met(
    log: Sequence[Evidence],
    exam_tier: int,
    targets: Mapping[int, int | None],
    *,
    pace: bool = True,
) -> bool:
    """`pace`: an exam with a length is entered (ENG-13); without one, time is information
    only and Level has no pace condition (ENG-14, ADR-0019 item 6)."""
    at_tier = [e for e in log if e.tier == exam_tier and e.clean]
    if len({e.day for e in at_tier}) < 2:
        return False
    if not pace:
        return True
    target = targets.get(exam_tier)
    timed = [e.speed_ms for e in at_tier if e.speed_ms is not None]
    if target is None or len(timed) < 3:
        return False
    return statistics.median(timed[-3:]) <= target


def mastered_met(
    log: Sequence[Evidence],
    exam_tier: int,
    targets: Mapping[int, int | None],
    *,
    pace: bool = True,
) -> bool:
    rated = [e for e in log if e.rated_success]
    if len({e.day for e in rated}) < 3:
        return False
    if not any(
        e.elapsed_days is not None
        and e.elapsed_days >= MASTERED_MIN_ELAPSED_DAYS
        and e.recall is not None
        and e.recall <= MASTERED_MAX_RECALL
        for e in rated
    ):
        return False
    successes = [e for e in log if e.clean or e.rated_success]
    if len({e.form for e in successes}) < 2:
        return False
    if not any(e.clean and (e.tier > exam_tier or e.checkup) for e in log):
        return False
    if not pace:
        return True
    timed_clean = [e for e in log if e.clean and e.speed_ms is not None]
    if len(timed_clean) < 3:
        return False
    for e in timed_clean[-3:]:
        target = targets.get(e.tier)
        if target is None or e.speed_ms is None or e.speed_ms > target:
            return False
    return True


@dataclass(frozen=True, slots=True, kw_only=True)
class LevelChange:
    level: LevelName
    shaky: bool
    shaky_reviews: int
    learning_streak: int
    evidence: JsonObject
    changed: bool
    demoted: bool = False


def update_level(
    state: SkillState,
    entry: Evidence,
    *,
    exam_tier: int,
    targets: Mapping[int, int | None],
    correct_in_a_row: int,
    pace: bool = True,
) -> LevelChange:
    """Level after one graded answer on a skill that has passed its learning phase once."""
    level: LevelName = state.level or "learned"
    shaky, shaky_reviews, streak = state.shaky, state.shaky_reviews, state.learning_streak
    evidence = dict(state.level_evidence)
    log = [*evidence_log(state), entry][-LEVEL_LOG_LIMIT:]
    demoted = False
    if level in ("exam", "mastered"):
        if shaky and entry.rating is not None:
            if entry.miss:
                level, shaky, shaky_reviews, demoted = ORDER[rank(level) - 1], False, 0, True
            else:
                shaky_reviews += 1
                if shaky_reviews >= SHAKY_WINDOW:
                    shaky, shaky_reviews = False, 0
        elif entry.miss:
            shaky, shaky_reviews = True, 0
    elif level == "learned" and entry.miss:
        level, demoted, streak = "learning", True, 0
    elif level == "learning":
        streak = streak + 1 if entry.clean else 0
        if streak >= correct_in_a_row:
            level, streak, log = "learned", 0, []
    if demoted:
        log = []
    elif not shaky:
        if level == "learned" and exam_level_met(log, exam_tier, targets, pace=pace):
            level = "exam"
        if level == "exam" and mastered_met(log, exam_tier, targets, pace=pace):
            level = "mastered"
    evidence["log"] = [e.as_json() for e in log]
    return LevelChange(
        level=level,
        shaky=shaky,
        shaky_reviews=shaky_reviews,
        learning_streak=streak,
        evidence=evidence,
        changed=level != state.level,
        demoted=demoted,
    )


def is_fading(recall: float | None) -> bool:
    """A Recall warning, not a Level."""
    return recall is not None and recall < FADING_RECALL


def checkup_due(last_checkup: date | None, today: date, every_weeks: int | None) -> bool:
    if every_weeks is None:
        return False
    return last_checkup is None or today - last_checkup >= timedelta(weeks=every_weeks)


def checkup_candidates(
    states: Sequence[SkillState],
    *,
    today: date,
    due_days: Mapping[str, date | None],
    day_of_review: Mapping[str, date],
    limit: int = 4,
) -> list[str]:
    """Skills for a mixed check-up: Learned or above, not due today, not reviewed in the last
    7 days. Exam-level skills still short of Mastered go first, then the least recent."""
    eligible = []
    for s in states:
        due = due_days.get(s.skill_id)
        last = day_of_review.get(s.skill_id)
        if rank(s.level) < rank("learned") or s.fsrs_state is None:
            continue
        if due is not None and due <= today:
            continue
        if last is not None and (today - last).days < 7:
            continue
        priority = 0 if s.level == "exam" else 1 if s.level == "learned" else 2
        eligible.append((priority, last or date.min, s.skill_id))
    return [k for _, _, k in sorted(eligible)[:limit]]
