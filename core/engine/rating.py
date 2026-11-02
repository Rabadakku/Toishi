"""The rating map (Study screen) and the slow-answer rule (ENG-14).

`rate` turns what happened on one problem into an FSRS rating, or into no FSRS event for a
stretch problem. Rows, in the order they are applied:

1. Stretch problem (above the core band): no FSRS event, Elo and Level only, right or wrong
   (ADR-0014: harder problems are unrated stretch; the skill's rated review is a core-band
   problem on a later study day, never right after the stretch's worked solution).
2. Used the last hint, or didn't know where to start: Again.
3. Wrong after the last attempt, or gave up: Again. A careless slip or misread within the
   cap is still Again (a wrong final answer never counts as a pass, ADR-0014), flagged
   `slip` so Level and the leech counter ignore it.
4. Self-graded: rubric all / all but one / fewer ticked: Good / Hard / Again; Matched /
   Minor slip / Didn't get it: Good / Again flagged `slip` (a wrong final answer, ADR-0014) /
   Again.
5. Correct on a later attempt, after a non-final hint, submitted unsure, or marked guessed:
   Hard.
6. Correct on the first attempt, no hints, sure: Good; Easy when marked too easy (the
   setting can disable it). Time never changes a rating (ENG-14, ADR-0019 item 6): a slow
   answer is Good with a `slow` label, which feeds attempt labels and Level's pace evidence.
7. Below the core band (the Lighter set, below-band checks; ENG-4, ADR-0019 item 5): a miss
   is Again, a success has no FSRS event.
"""

from dataclasses import dataclass
from typing import Literal

from core.engine.config import (
    AGAIN,
    EASY,
    GOOD,
    HARD,
    SLOW_LOW_RECALL,
    SLOW_MIN_TIMED_SUCCESSES,
    SLOW_MULTIPLE,
    SLOW_MULTIPLE_LOW_RECALL,
)

SelfGrade = Literal["matched", "minor-slip", "missed"]


@dataclass(frozen=True, slots=True, kw_only=True)
class AnswerFacts:
    """What the student did on the problem (final submission)."""

    correct: bool
    attempt_number: int = 1
    hints_used: int = 0
    last_hint_used: bool = False  # the last hint gives the first step
    gave_up: bool = False
    unsure: bool = False
    guessed: bool = False
    too_easy: bool = False
    didnt_know_start: bool = False  # "Step 0" in the picker
    slip_within_cap: bool = False  # careless slip/misread accepted (the cap is decided upstream)
    self_grade: SelfGrade | None = None
    rubric_total: int | None = None  # self-graded with a rubric: steps in it ...
    rubric_ticked: int | None = None  # ... and steps the student matched

    @property
    def clean(self) -> bool:
        """Correct on the first attempt with no hints: Level's notion of "correct"."""
        return self.success and self.attempt_number == 1 and self.hints_used == 0

    @property
    def strict_ok(self) -> bool:
        """The strict outcome label (audit I1): the final answer correct on the first try
        with no hint, whatever the rating map makes of it."""
        if self.self_grade is not None or self.rubric_total is not None:
            full = self.rubric_total is not None and (self.rubric_ticked or 0) >= self.rubric_total
            right = full or self.self_grade == "matched"
        else:
            right = self.correct and not self.gave_up
        return right and self.attempt_number == 1 and self.hints_used == 0

    @property
    def submitted_sure_miss(self) -> bool:
        """A wrong answer the student submitted as sure: the only miss that can be a
        confident error (spec, What went wrong?). Giving up, using the last hint and "didn't
        know where to start" are not submissions of a wrong answer."""
        return not (
            self.success
            or self.correct
            or self.unsure
            or self.gave_up
            or self.last_hint_used
            or self.didnt_know_start
        )

    @property
    def success(self) -> bool:
        if self.self_grade is not None or self.rubric_total is not None:
            return _self_rating(self) >= HARD
        return self.correct and not self.gave_up and not self.last_hint_used


@dataclass(frozen=True, slots=True, kw_only=True)
class SpeedFacts:
    """The numbers ENG-14 compares (all speed times in ms)."""

    speed_ms: int | None  # None when untimed or excluded from speed rules
    baseline_ms: float | None  # log-time median for this skill and tier
    timed_successes: int  # eligible successes after Learned at this tier
    target_ms: int | None
    recall: float | None  # predicted recall at review
    learned: bool  # Level is Learned or above


@dataclass(frozen=True, slots=True, kw_only=True)
class RatingRules:
    easy_enabled: bool = True
    slow_rule: bool = True
    untimed: bool = False
    below_band: bool = False  # ENG-4: below the skill's core band
    stretch: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class RatingDecision:
    rating: int | None  # None: no FSRS event
    success: bool  # for Elo and Level evidence
    slow: bool = False
    stretch: bool = False
    core_followup: bool = False  # a failed stretch problem: serve a core-band one later
    reasons: tuple[str, ...] = ()
    slip: bool = False  # Again from an accepted careless slip: Level and leeches ignore it


def is_slow(speed: SpeedFacts, *, enabled: bool, untimed: bool) -> bool:
    """ENG-14: over k x his log-time median (k = 2, or 2.5 when recall < 0.85) AND over the
    target; only once Learned with five timed successes, never in Untimed sessions."""
    if not enabled or untimed or not speed.learned:
        return False
    if speed.speed_ms is None or speed.baseline_ms is None or speed.target_ms is None:
        return False
    if speed.timed_successes < SLOW_MIN_TIMED_SUCCESSES:
        return False
    low = speed.recall is not None and speed.recall < SLOW_LOW_RECALL
    multiple = SLOW_MULTIPLE_LOW_RECALL if low else SLOW_MULTIPLE
    return speed.speed_ms > multiple * speed.baseline_ms and speed.speed_ms > speed.target_ms


def _self_rating(facts: AnswerFacts) -> int:
    if facts.rubric_total is not None:
        missed = facts.rubric_total - (facts.rubric_ticked or 0)
        return GOOD if missed <= 0 else HARD if missed == 1 else AGAIN
    return {"matched": GOOD, "minor-slip": AGAIN, "missed": AGAIN}[facts.self_grade or "missed"]


def rate(facts: AnswerFacts, speed: SpeedFacts | None, rules: RatingRules) -> RatingDecision:
    success = facts.success
    if rules.stretch:
        return RatingDecision(
            rating=None,
            success=success,
            stretch=True,
            core_followup=not success,
            reasons=("stretch: no FSRS event",),
        )
    reasons: list[str] = []
    slow = False
    slip = False
    if facts.last_hint_used or facts.didnt_know_start:
        rating = AGAIN
        reasons.append("last hint" if facts.last_hint_used else "didn't know where to start")
    elif facts.self_grade is not None or facts.rubric_total is not None:
        rating = _self_rating(facts)
        reasons.append("self-graded")
        if facts.self_grade == "minor-slip":  # a wrong final answer: Again, flagged a slip
            slip = True
            reasons.append("minor slip")
    elif not facts.correct or facts.gave_up:
        rating = AGAIN
        if facts.slip_within_cap and not facts.gave_up:
            slip = True
            reasons.append("slip within cap")
        else:
            reasons.append("gave up" if facts.gave_up else "wrong")
    elif facts.attempt_number > 1 or facts.hints_used > 0 or facts.unsure or facts.guessed:
        rating = HARD
        reasons.append(
            "later attempt"
            if facts.attempt_number > 1
            else "hint"
            if facts.hints_used > 0
            else "unsure"
            if facts.unsure
            else "guessed"
        )
    else:
        rating = GOOD
    if rating == GOOD:
        # A label only: time never changes a rating (ENG-14).
        slow = speed is not None and is_slow(speed, enabled=rules.slow_rule, untimed=rules.untimed)
        if facts.too_easy and rules.easy_enabled and facts.self_grade is None:
            rating = EASY
            reasons.append("too easy")
    final: int | None = rating
    if rules.below_band and rating >= HARD:
        final = None  # a below-band success changes nothing (ENG-4)
        reasons.append("below band: no FSRS event")
    return RatingDecision(
        rating=final,
        success=success,
        slow=slow,
        stretch=rules.stretch,
        reasons=tuple(reasons),
        slip=slip,
    )


def worst_rating(ratings: list[int | None]) -> int | None:
    """Multi-part problems: the card's skill takes the worst rating among its parts."""
    present = [r for r in ratings if r is not None]
    return min(present) if present else None
