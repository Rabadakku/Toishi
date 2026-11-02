"""Multi-part problems (spec "Multi-part problems"): one answer box, verdict and attempt count
per part. A part with its own `skill` reports to that skill: the diagnosis flow gives a
success partial credit (ENG-7) and starts a prerequisite check after a miss. The card's own
skill takes the worst rating among its remaining parts.

The worst rating needs no per-part rating pass: the rating map is monotone in what differs
between parts (right or wrong, which try), and hints, timing, "too easy" and confidence are
the card's. So the worst part's rating is the rating of the card's facts with `correct` =
every remaining part right and `attempt_number` = the most tries a remaining part took
(tests check this against `rating.worst_rating` over parts rated one by one).
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from core.engine.rating import AnswerFacts
from core.model import JsonObject


@dataclass(frozen=True, slots=True, kw_only=True)
class PartOutcome:
    """One part's final verdict. `skill_id`: the part's own skill (None: the card's)."""

    label: str
    correct: bool
    skill_id: str | None = None
    attempts: int = 1  # tries used on this part (1: right, or wrong, at the first)
    gave_up: bool = False

    def reports_to(self, card_skill: str) -> str:
        return self.skill_id or card_skill

    def as_json(self) -> JsonObject:
        return {
            "label": self.label,
            "skill": self.skill_id,
            "correct": self.correct,
            "attempts": self.attempts,
            "gave_up": self.gave_up,
        }

    @classmethod
    def from_json(cls, data: JsonObject) -> PartOutcome:
        return cls(
            label=str(data["label"]),
            skill_id=data.get("skill"),
            correct=bool(data.get("correct")),
            attempts=int(data.get("attempts", 1)),
            gave_up=bool(data.get("gave_up")),
        )


def own_skill_parts(parts: Sequence[PartOutcome], card_skill: str) -> list[PartOutcome]:
    """Parts that report to a skill other than the card's."""
    return [p for p in parts if p.reports_to(card_skill) != card_skill]


def remaining_parts(parts: Sequence[PartOutcome], card_skill: str) -> list[PartOutcome]:
    """Parts that report to the card's own skill. When every part has a skill of its own,
    the card's skill is rated on all of them (it was still practised as a whole)."""
    rest = [p for p in parts if p.reports_to(card_skill) == card_skill]
    return rest or list(parts)


def card_facts(facts: AnswerFacts, parts: Sequence[PartOutcome], card_skill: str) -> AnswerFacts:
    """The facts that rate the card's own skill: the worst among its remaining parts."""
    rest = remaining_parts(parts, card_skill)
    if not rest:
        return facts
    return replace(
        facts,
        correct=all(p.correct for p in rest),
        attempt_number=max(p.attempts for p in rest),
        gave_up=any(p.gave_up for p in rest) and not all(p.correct for p in rest),
    )


def part_facts(facts: AnswerFacts, part: PartOutcome) -> AnswerFacts:
    """One part's facts on its own (the card's hints, timing and confidence)."""
    return replace(facts, correct=part.correct, attempt_number=part.attempts, gave_up=part.gave_up)
