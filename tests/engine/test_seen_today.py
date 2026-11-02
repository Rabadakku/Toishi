"""Hand test item 3: never a card already served in the current study day (ENG-2, ENG-3)."""

from core.engine.config import DAY_MS
from core.engine.selection import (
    SeenIndex,
    learning_pool_size,
    learning_streak_needed,
    pick_problem,
)
from tests.engine.helpers import at_day, card


def test_a_card_seen_today_is_never_picked_even_when_every_rule_relaxes() -> None:
    pool = [card(1, cid="a"), card(2, cid="b")]
    today = at_day(10)
    now = today + 3_600_000
    seen = SeenIndex(card_seen_at={"a": today + 60_000, "b": today - DAY_MS})
    pick = pick_problem(pool, theta=0.0, tiers=(1, 2), now_ms=now, seen=seen, today_start_ms=today)
    assert pick is not None
    assert pick.card.id == "b"  # seen yesterday: relaxed "recently seen" allows it
    seen = SeenIndex(card_seen_at={"a": today + 60_000, "b": today + 120_000})
    assert (
        pick_problem(pool, theta=0.0, tiers=(1, 2), now_ms=now, seen=seen, today_start_ms=today)
        is None  # the slot is skipped
    )
    # Without a study day the old behaviour stays (callers that don't know the day).
    assert pick_problem(pool, theta=0.0, tiers=(1, 2), now_ms=now, seen=seen) is not None


def test_a_template_parameter_set_used_today_counts_as_seen() -> None:
    pool = [card(1, cid="t.v1", template="t", seed=1), card(1, cid="other")]
    today = at_day(3)
    seen = SeenIndex(params_seen_at={("t", 1): today + 1})
    pick = pick_problem(
        pool, theta=0.0, tiers=(1,), now_ms=today + 2, seen=seen, today_start_ms=today
    )
    assert pick is not None
    assert pick.card.id == "other"


def test_the_learning_run_is_min_of_three_and_the_distinct_problems() -> None:
    assert learning_streak_needed(3, None) == 3
    assert learning_streak_needed(3, 0) == 3  # no problem at all: nothing changes
    assert learning_streak_needed(3, 1) == 1
    assert learning_streak_needed(3, 2) == 2
    assert learning_streak_needed(3, 7) == 3
    pool = [
        card(1, cid="a"),
        card(2, cid="b"),
        card(3, cid="c"),
        card(1, cid="ex", kind="example"),
        card(2, cid="hidden"),
    ]
    assert learning_pool_size(pool, hidden={"hidden"}) == 2  # tier 1-2 problems only
    assert learning_pool_size([card(3, cid="c"), card(4, cid="d")]) == 2  # widened tiers
