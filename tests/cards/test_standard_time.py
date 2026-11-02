"""Standard times (student-model spec 2.4), checked against values worked out by hand:
T* = time, or 0.5 + m * steps + m * max(0, tier - 3), or a tier default with no steps."""

import math

import pytest

from core.cards import Source, load
from core.cards.mepack import PackBuild, PackMeta, tier_default_times
from core.cards.standard_time import TIER_DEFAULTS, standard_minutes, uses_tier_default
from core.model import Card, CardPart, SolutionStep


def card(
    tier: int, steps: int, *, time: float | None = None, parts: tuple[CardPart, ...] = ()
) -> Card:
    solution = tuple(SolutionStep(number=n, skill_id="s.a", label="Step") for n in range(steps))
    return Card(
        id="c.001", question_md="Q", tier=tier, solution=solution, time_minutes=time, parts=parts
    )


def part(label: str, time: float | None = None) -> CardPart:
    return CardPart(label=label, prompt_md="P", time_minutes=time)


@pytest.mark.parametrize(
    ("tier", "steps", "m", "minutes"),
    [
        (1, 1, 1.5, 2.0),  # 0.5 + 1 * 1.5: the spec's one-step drill
        (2, 4, 1.5, 6.5),  # 0.5 + 4 * 1.5
        (3, 4, 1.5, 6.5),  # tier 3 adds nothing: the spec's 4-step exam problem
        (3, 6, 1.5, 9.5),  # 0.5 + 6 * 1.5: the spec's 6-step exam problem
        (4, 5, 1.5, 9.5),  # 0.5 + 5 * 1.5 + 1 * 1.5
        (5, 3, 1.5, 8.0),  # 0.5 + 3 * 1.5 + 2 * 1.5
        (4, 3, 2.0, 8.5),  # 0.5 + 3 * 2 + 1 * 2
        (3, 10, 0.38, 4.3),  # 0.5 + 10 * 0.38
    ],
)
def test_the_default_counts_steps_and_tiers_above_3(
    tier: int, steps: int, m: float, minutes: float
) -> None:
    assert standard_minutes(card(tier, steps), m) == pytest.approx(minutes)


def test_time_overrides_the_default() -> None:
    assert standard_minutes(card(3, 6, time=3.25), 1.5) == 3.25
    assert standard_minutes(card(5, 0, time=12.0), 1.5) == 12.0


@pytest.mark.parametrize(("tier", "minutes"), [(1, 1.0), (2, 2.0), (3, 4.0), (4, 6.0), (5, 8.0)])
def test_without_steps_a_card_takes_its_tiers_default(tier: int, minutes: float) -> None:
    assert TIER_DEFAULTS[tier] == minutes
    assert standard_minutes(card(tier, 0), 1.5) == minutes
    assert standard_minutes(card(tier, 0), 3.0) == minutes  # not scaled by m
    assert uses_tier_default(card(tier, 0))
    assert not uses_tier_default(card(tier, 1))
    assert not uses_tier_default(card(tier, 0, time=2.0))


def test_multi_part_problems_are_timed_as_a_whole() -> None:
    whole = card(3, 5, parts=(part("a"), part("b")))
    assert standard_minutes(whole, 1.5) == 8.0  # 0.5 + 5 * 1.5
    assert standard_minutes(whole.parts[0], 1.5, card=whole) == 4.0  # an equal share: 8 / 2
    timed = card(3, 5, parts=(part("a", 2.0), part("b", 3.5)))
    assert standard_minutes(timed, 1.5) == 5.5  # every part timed: 2 + 3.5
    assert standard_minutes(timed.parts[1], 1.5) == 3.5  # its own: no card needed
    own = card(3, 5, time=9.0, parts=(part("a"), part("b"), part("c")))
    assert standard_minutes(own.parts[0], 1.5, card=own) == 3.0  # 9 / 3
    mixed = card(3, 5, parts=(part("a", 2.0), part("b")))
    assert standard_minutes(mixed, 1.5) == 8.0  # not every part timed: the formula
    assert standard_minutes(mixed.parts[1], 1.5, card=mixed) == 4.0  # 8 / 2
    assert not uses_tier_default(card(2, 0, parts=(part("a", 1.0),)))  # its parts' sum
    assert uses_tier_default(card(2, 0, parts=(part("a"),)))


def test_bad_inputs_raise() -> None:
    whole = card(3, 5, parts=(part("a"),))
    with pytest.raises(ValueError, match="pass the card"):
        standard_minutes(whole.parts[0], 1.5)
    with pytest.raises(ValueError, match="pass the card"):
        standard_minutes(part("z"), 1.5, card=whole)
    for m in (0.0, -1.5, math.nan, math.inf):
        with pytest.raises(ValueError, match="minutes per step"):
            standard_minutes(whole, m)


UNTAGGED = """---
format: mastery-cards 1
deck: P::U::S
---

## Card p.001
skill: p.a
difficulty: 3
answer-type: number
answer: 2

### Question
Q \\(1 + 1\\)

### Solution
It is \\(2\\).
"""


def test_the_build_report_names_cards_timed_by_a_tier_default() -> None:
    """Pack problems always have solution steps, so a personal deck shows the report line."""
    loaded = load([Source("p.cards.md", UNTAGGED)])
    lines = tier_default_times(loaded)
    assert lines == [
        "p.cards.md:6: card p.001: no solution steps, so the tier 3 default of 4 minutes"
    ]
    build = PackBuild(PackMeta("p", "P", "1.0.0", "personal"), loaded, standard_times=lines)
    assert f"standard time: {lines[0]}" in build.report().split("\n")
    timed = UNTAGGED.replace("difficulty: 3", "difficulty: 3\ntime: 2")
    tagged = UNTAGGED.replace("It is \\(2\\).", "0. [p.a] Add: \\(2\\).")
    for other in (timed, tagged):
        assert tier_default_times(load([Source("p.cards.md", other)])) == []
