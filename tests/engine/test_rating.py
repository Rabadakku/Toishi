"""The rating map (Study screen) and the slow-answer rule (ENG-14), row by row."""

import pytest

from core.engine.config import AGAIN, EASY, GOOD, HARD
from core.engine.rating import (
    AnswerFacts,
    RatingRules,
    SpeedFacts,
    is_slow,
    rate,
    worst_rating,
)

RULES = RatingRules()
FAST = SpeedFacts(
    speed_ms=30_000,
    baseline_ms=30_000,
    timed_successes=8,
    target_ms=60_000,
    recall=0.9,
    learned=True,
)
SLOW = SpeedFacts(
    speed_ms=130_000,
    baseline_ms=60_000,
    timed_successes=8,
    target_ms=90_000,
    recall=0.9,
    learned=True,
)


def facts(**kw: object) -> AnswerFacts:
    kw.setdefault("correct", True)
    return AnswerFacts(**kw)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        # Correct on the first attempt, no hints, submitted sure -> Good
        (facts(), GOOD),
        # Correct on the second attempt / after a non-final hint / unsure / guessed -> Hard
        (facts(attempt_number=2), HARD),
        (facts(attempt_number=3), HARD),
        (facts(hints_used=1), HARD),
        (facts(unsure=True), HARD),
        (facts(guessed=True), HARD),
        # Careless slip or misread, within the cap -> still Again (flagged, ADR-0014)
        (facts(correct=False, slip_within_cap=True), AGAIN),
        # Wrong after the last attempt, gave up, used the last hint, didn't know where to start
        (facts(correct=False), AGAIN),
        (facts(correct=False, gave_up=True), AGAIN),
        (facts(correct=False, gave_up=True, slip_within_cap=True), AGAIN),
        (facts(hints_used=3, last_hint_used=True), AGAIN),
        (facts(correct=False, didnt_know_start=True), AGAIN),
        # Self-graded: rubric all / all but one / fewer; matched / minor slip / didn't get it
        (facts(rubric_total=4, rubric_ticked=4), GOOD),
        (facts(rubric_total=4, rubric_ticked=3), HARD),
        (facts(rubric_total=4, rubric_ticked=2), AGAIN),
        (facts(self_grade="matched"), GOOD),
        (facts(self_grade="minor-slip"), AGAIN),  # a wrong final answer (ADR-0014)
        (facts(self_grade="missed"), AGAIN),
    ],
)
def test_rating_map_rows(answer, expected):
    assert rate(answer, FAST, RULES).rating == expected


def test_too_easy_gives_easy_unless_disabled():
    assert rate(facts(too_easy=True), FAST, RULES).rating == EASY
    assert rate(facts(too_easy=True), FAST, RatingRules(easy_enabled=False)).rating == GOOD
    # "The same" means correct first time, no hints, sure: otherwise the key changes nothing.
    assert rate(facts(too_easy=True, unsure=True), FAST, RULES).rating == HARD


def test_slow_correct_answer_is_good_with_a_slow_label():
    # ENG-14 / ADR-0019 item 6: time never changes a rating; slow is a label.
    decision = rate(facts(), SLOW, RULES)
    assert decision.rating == GOOD
    assert decision.slow
    assert decision.success
    assert rate(facts(too_easy=True), SLOW, RULES).rating == EASY


@pytest.mark.parametrize(
    "rules", [RatingRules(below_band=True), RatingRules(below_band=True, easy_enabled=True)]
)
def test_below_band_success_has_no_fsrs_event_and_a_miss_is_again(rules):
    # ENG-4 / ADR-0019 item 5 (the Lighter set, checks under the band).
    assert rate(facts(), FAST, rules).rating is None
    assert rate(facts(too_easy=True), FAST, rules).rating is None
    assert rate(facts(self_grade="matched"), FAST, rules).rating is None
    assert rate(facts(correct=False), FAST, rules).rating == AGAIN


def test_stretch_answered_wrong_has_no_fsrs_event():
    miss = rate(facts(correct=False), FAST, RatingRules(stretch=True))
    assert miss.rating is None
    assert miss.stretch
    assert miss.core_followup
    assert not miss.success
    slip = rate(facts(correct=False, slip_within_cap=True), FAST, RatingRules(stretch=True))
    assert slip.rating is None
    assert slip.core_followup


def test_stretch_answered_right_is_unrated_too():
    # ADR-0014 (Decision 5): harder problems are unrated stretch, right or wrong.
    hit = rate(facts(), FAST, RatingRules(stretch=True))
    assert hit.rating is None
    assert hit.stretch
    assert hit.success
    assert not hit.core_followup
    assert rate(facts(unsure=True), FAST, RatingRules(stretch=True)).rating is None


# ---------------------------------------------------------------- ENG-14


def speed(**kw: object) -> SpeedFacts:
    base: dict[str, object] = {
        "speed_ms": 130_000,
        "baseline_ms": 60_000,
        "timed_successes": 5,
        "target_ms": 90_000,
        "recall": 0.9,
        "learned": True,
    }
    base.update(kw)
    return SpeedFacts(**base)  # type: ignore[arg-type]


def test_slow_needs_both_conditions():
    assert is_slow(speed(), enabled=True, untimed=False)
    # Over twice the median but under the target: not slow.
    assert not is_slow(speed(target_ms=140_000), enabled=True, untimed=False)
    # Over the target but under twice the median: not slow.
    assert not is_slow(speed(baseline_ms=70_000), enabled=True, untimed=False)


def test_low_recall_uses_two_and_a_half_times():
    at_2_2x = speed(speed_ms=132_000)
    assert is_slow(at_2_2x, enabled=True, untimed=False)
    assert not is_slow(speed(speed_ms=132_000, recall=0.84), enabled=True, untimed=False)
    assert is_slow(speed(speed_ms=151_000, recall=0.84), enabled=True, untimed=False)
    assert is_slow(speed(speed_ms=132_000, recall=0.85), enabled=True, untimed=False)


@pytest.mark.parametrize(
    "case",
    [
        speed(learned=False),
        speed(timed_successes=4),
        speed(speed_ms=None),
        speed(baseline_ms=None),
        speed(target_ms=None),
    ],
)
def test_slow_rule_preconditions(case):
    assert not is_slow(case, enabled=True, untimed=False)


def test_slow_rule_never_in_untimed_sessions_or_when_off():
    assert not is_slow(speed(), enabled=True, untimed=True)
    assert not is_slow(speed(), enabled=False, untimed=False)
    assert rate(facts(), speed(), RatingRules(untimed=True)).rating == GOOD
    assert rate(facts(), speed(), RatingRules(slow_rule=False)).rating == GOOD


def test_slow_only_turns_good_into_hard():
    assert rate(facts(unsure=True), speed(), RULES).rating == HARD
    assert not rate(facts(unsure=True), speed(), RULES).slow
    assert rate(facts(correct=False), speed(), RULES).rating == AGAIN


def test_multi_part_takes_the_worst_rating():
    assert worst_rating([GOOD, HARD, None]) == HARD
    assert worst_rating([GOOD, AGAIN]) == AGAIN
    assert worst_rating([None]) is None


def test_clean_and_success():
    assert facts().clean
    assert not facts(attempt_number=2).clean
    assert not facts(hints_used=1).clean
    assert not facts(correct=False, slip_within_cap=True).success
    assert not facts(self_grade="minor-slip").success
    assert rate(facts(self_grade="minor-slip"), None, RatingRules()).slip
    assert not facts(self_grade="missed").success
