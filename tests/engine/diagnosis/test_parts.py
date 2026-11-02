"""Multi-part problems: one verdict and attempt count per part; a part with its own skill
reports to it (partial credit on success, a prerequisite check on a miss); the card's own
skill takes the worst rating among its remaining parts."""

import itertools
from dataclasses import replace

import pytest

from core.engine import AnswerFacts, PartOutcome, card_facts, rate
from core.engine.config import AGAIN, GOOD, HARD
from core.engine.diagnosis import DiagnosisSettings
from core.engine.parts import part_facts, remaining_parts
from core.engine.rating import RatingRules, worst_rating
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, allow_credit_on, answer, seed, world
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import at_day

T = at_day(0)


def test_the_card_facts_rate_as_the_worst_remaining_part() -> None:
    """card_facts needs no per-part rating pass: the rating of the aggregated facts equals
    rating.worst_rating over the remaining parts rated one by one, for every combination."""
    rules = RatingRules()
    verdicts = [(True, 1), (True, 2), (False, 1), (False, 2)]
    for combo in itertools.product(verdicts, repeat=3):
        flags: tuple[bool, bool] = (False, True)
        for hints, unsure, too_easy, last_hint in itertools.product((0, 1), flags, flags, flags):
            base = AnswerFacts(
                correct=False,
                hints_used=hints,
                unsure=unsure,
                too_easy=too_easy,
                last_hint_used=last_hint and hints > 0,
            )
            parts = [
                PartOutcome(label=label, correct=ok, attempts=n, skill_id=skill)
                for label, (ok, n), skill in zip("abc", combo, (None, None, POW), strict=True)
            ]
            rest = remaining_parts(parts, CRIT)
            assert [p.label for p in rest] == ["a", "b"]
            one_by_one = worst_rating([rate(part_facts(base, p), None, rules).rating for p in rest])
            assert rate(card_facts(base, parts, CRIT), None, rules).rating == one_by_one


def test_every_part_with_its_own_skill_still_rates_the_card() -> None:
    parts = [PartOutcome(label="a", skill_id=POW, correct=True)]
    assert remaining_parts(parts, CRIT) == parts
    facts = card_facts(AnswerFacts(correct=False), parts, CRIT)
    assert facts.correct


def three_parts(w: MemoryWorld, a: tuple[bool, int], b: bool, c: bool) -> None:
    """crit.t2.0 answered as parts a (the card's skill), b (Power rule), c (Factor)."""
    parts = (
        PartOutcome(label="a", correct=a[0], attempts=a[1]),
        PartOutcome(label="b", skill_id=POW, correct=b),
        PartOutcome(label="c", skill_id=ALG, correct=c, gave_up=not c),
    )
    w.grade(replace(answer(w, "crit.t2.0", T, correct=False), parts=parts))


def base(credit: str = "shadow") -> MemoryWorld:
    w = world(config=DiagnosisSettings(credit=credit))  # type: ignore[arg-type]
    for skill in (ALG, POW):
        seed(w, skill, stability=30, days_ago=10, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0)
    return w


@pytest.mark.parametrize(("a", "rating"), [((True, 1), GOOD), ((True, 2), HARD)])
def test_own_skill_parts_report_to_their_skills(a: tuple[bool, int], rating: int) -> None:
    w = base()
    three_parts(w, a, b=True, c=False)
    # The card's skill: rated on part a only (a miss on part c is not its miss).
    assert w.last.rating == rating
    assert [e.rating for e in w.events_for(CRIT)] == [rating]
    assert [p["label"] for p in w.last.extra["parts"]] == ["a", "b", "c"]
    assert w.last.extra["diagnosis"]["parts"] == {"b": "credit", "c": "check"}
    # Part b right: Power rule gets ENG-7 credit (shadow mode: stored beside the plain one).
    (credit,) = [c for c in w.credits if c.to_skill == POW]
    assert (credit.from_skill, credit.weight, credit.mode) == (CRIT, 1.0, "shadow")
    assert credit.stability_after is not None
    assert credit.stability_before is not None
    assert credit.stability_after > credit.stability_before
    assert w.events_for(POW) == []  # credit is never an FSRS review
    assert w.shadows[POW].credited_stability == credit.stability_after
    # Part c missed: a prerequisite check on Factor, a few items later.
    (check,) = w.pending(ALG)
    assert (check.kind, check.depth) == ("prerequisite", 1)
    assert check.after_items >= 3
    assert "part c" in (check.reason or "")
    assert w.events_for(ALG) == []


def test_a_missed_remaining_part_is_the_cards_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    allow_credit_on(monkeypatch)
    w = base(credit="on")
    before = w.states[POW].stability
    three_parts(w, (False, 2), b=True, c=True)
    assert w.last.rating == AGAIN
    assert [e.rating for e in w.events_for(CRIT)] == [AGAIN]
    # Parts with their own skill still report: credit On moves Power rule's stability.
    after = w.states[POW].stability
    assert after is not None
    assert before is not None
    assert after > before
    assert {c.to_skill for c in w.credits} >= {POW, ALG}
    assert w.pending(ALG) == []


def test_credit_off_gives_nothing_but_a_miss_still_checks() -> None:
    w = base(credit="off")
    three_parts(w, (True, 1), b=True, c=False)
    assert w.credits == []
    assert len(w.pending(ALG)) == 1
