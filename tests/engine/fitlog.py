"""Synthetic review logs for the fitting tests: learners whose true memory is FSRS-6 with
known parameters, reviewed on whole study days, logged the way grading logs them."""

import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from core.engine.config import DAY_MS, RULES_VERSION
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter
from core.model import ReviewEvent

T0 = 1_788_278_400_000  # 2026-09-01 12:00 New York (16:00 UTC)


@dataclass
class Log:
    events: list[ReviewEvent] = field(default_factory=list)
    next_id: int = 1

    def add(self, event: ReviewEvent) -> ReviewEvent:
        stored = ReviewEvent(
            id=self.next_id,
            at=event.at,
            attempt_id=self.next_id,
            target_kind=event.target_kind,
            target_id=event.target_id,
            target_ord=event.target_ord,
            rating=event.rating,
            rules_version=event.rules_version,
            params_id=event.params_id,
            retention=event.retention,
            predicted_recall=event.predicted_recall,
            state_before=event.state_before,
            state_after=event.state_after,
        )
        self.next_id += 1
        self.events.append(stored)
        return stored


def learner_log(
    parameters: Sequence[float] | None,
    *,
    cards: int,
    reviews: int,
    seed: int,
    days: StudyDays,
    prefix: str = "s",
    rules_version: str = RULES_VERSION,
    start: int = T0,
    spread_days: int = 60,
    flip: bool = False,
) -> Log:
    """Each card: a first review (Good, or Again then Good the same day), then `reviews`
    reviews near the 0.9-retention interval, each outcome drawn from the true recall on
    whole study days. `flip`: log the opposite outcome (a corrupted log)."""
    truth = FsrsAdapter(parameters, fuzz=False, days=days)
    rng = random.Random(seed)  # noqa: S311
    log = Log()
    for k in range(cards):
        target = f"{prefix}.{k}"
        at = start + rng.randrange(spread_days) * DAY_MS + rng.randrange(6) * 3_600_000
        memory = None
        first = [1, 3] if rng.random() < 0.3 else [3]
        for i, rating in enumerate(first):
            log.add(_event(target, rating, at + i * 60_000, memory, rules_version))
            memory = truth.review(memory, rating, at + i * 60_000)
        assert memory is not None
        for _ in range(reviews):
            interval = max(
                1, round(truth.raw_interval(memory.stability, 0.9) * rng.uniform(0.6, 1.5))
            )
            at = days.moment(days.add(days.day_of(memory.last_review_at), interval))
            at += rng.randrange(-3, 4) * 3_600_000
            recall = truth.recall_days(memory, at)
            ok = rng.random() < recall
            rating = (2 if rng.random() < 0.1 else 3) if ok else 1
            logged = (1 if ok else 3) if flip else rating
            log.add(_event(target, logged, at, memory, rules_version, predicted=recall))
            memory = truth.review(memory, rating, at)
    log.events.sort(key=lambda e: (e.at, e.id or 0))
    return log


def _event(
    target: str,
    rating: int,
    at: int,
    before: object,
    rules_version: str,
    *,
    predicted: float | None = None,
) -> ReviewEvent:
    state = (
        {"stability": None, "difficulty": None, "last_review_at": None}
        if before is None
        else {
            "stability": before.stability,  # type: ignore[attr-defined]
            "difficulty": before.difficulty,  # type: ignore[attr-defined]
            "last_review_at": before.last_review_at,  # type: ignore[attr-defined]
        }
    )
    return ReviewEvent(
        at=at,
        target_kind="skill",
        target_id=target,
        rating=rating,
        rules_version=rules_version,
        predicted_recall=predicted,
        state_before=state,
    )


def store_log(storage: object, log: Log) -> None:
    """Record a synthetic log through UserStore, one attempt per event (time order)."""
    from dataclasses import replace

    from core.model import Attempt, GradedAnswer, SkillState

    users = storage.users  # type: ignore[attr-defined]
    for e in log.events:
        first = (e.state_before or {}).get("stability") is None
        attempt = Attempt(
            at=e.at,
            card_id=f"{e.target_id}.card",
            skill_id=e.target_id,
            verdict="correct" if e.rating > 1 else "incorrect",
            rating=e.rating,
            predicted_recall=e.predicted_recall,
            extra={"stage": "learning" if first else "review"},
        )
        state = SkillState(
            skill_id=e.target_id, fsrs_state=2, stability=1.0, difficulty=5.0, last_review_at=e.at
        )
        event = replace(e, id=None, attempt_id=None, state_before=None)
        users.record_answer(GradedAnswer(attempt=attempt, changes=(state,), reviews=(event,)))
