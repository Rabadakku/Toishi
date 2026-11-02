"""ENG-4 core band and ENG-5 Elo problem selection."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.engine.config import DAY_MS, TIER_DIFFICULTY
from core.engine.selection import (
    FormStats,
    SeenIndex,
    core_band,
    elo_update,
    form_key,
    form_stats,
    is_stretch,
    p_correct,
    pick_problem,
    stretch_allowed,
    stretch_tier,
    wants_stretch,
)
from core.model import Attempt, CardRef
from tests.engine.helpers import Sim, at_day, card, learned_state, outcome, some


@pytest.mark.parametrize(
    ("stability", "band", "stretch"),
    [
        (None, (1, 2), 3),
        (2.0, (1, 2), 3),
        (6.99, (1, 2), 3),
        (7.0, (2, 3), 4),
        (29.9, (2, 3), 4),
        (30.0, (3,), 4),
        (90.0, (3,), 4),
        (90.1, (3, 4), 5),
    ],
)
def test_core_band_table(stability, band, stretch):
    assert core_band(stability) == band
    assert stretch_tier(stability, elite=True) == stretch


def test_exam_window_uses_tier_three_and_elite_can_be_off():
    assert core_band(200.0, exam_window=True) == (3,)
    assert core_band(None, exam_window=True) == (3,)
    assert stretch_tier(200.0, elite=False) is None
    assert is_stretch(4, (2, 3))
    assert not is_stretch(3, (2, 3))
    assert not is_stretch(1, (3,))


def test_stretch_is_at_most_ten_percent_and_one_elite_per_session():
    assert not stretch_allowed(
        reviews_so_far=0, stretches_so_far=0, elite_used=False, tier=4, fraction=0.1
    )
    assert stretch_allowed(
        reviews_so_far=9, stretches_so_far=0, elite_used=False, tier=4, fraction=0.1
    )
    assert not stretch_allowed(
        reviews_so_far=9, stretches_so_far=1, elite_used=False, tier=4, fraction=0.1
    )
    assert stretch_allowed(
        reviews_so_far=19, stretches_so_far=1, elite_used=False, tier=4, fraction=0.1
    )
    assert not stretch_allowed(
        reviews_so_far=99, stretches_so_far=0, elite_used=True, tier=5, fraction=0.1
    )
    assert not stretch_allowed(
        reviews_so_far=99, stretches_so_far=0, elite_used=False, tier=None, fraction=0.1
    )
    assert not stretch_allowed(
        reviews_so_far=99, stretches_so_far=0, elite_used=False, tier=4, fraction=0.0
    )
    picks = sum(wants_stretch(f"s{i}", "2026-09-01", 0.1) for i in range(2000))
    assert 150 < picks < 250


def test_elo_update_follows_the_formula():
    up = elo_update(theta=0.0, n=0, form="template:a", tier=2, success=True, stats={})
    p = 1 / (1 + math.exp(-(0.0 - TIER_DIFFICULTY[2])))
    assert up.p == pytest.approx(p)
    assert up.theta_after == pytest.approx(0.0 + 1.0 * (1 - p))
    later = elo_update(theta=0.0, n=20, form="template:a", tier=2, success=True, stats={})
    assert later.theta_after == pytest.approx((1 - p) / (1 + 0.05 * 20))


def test_problem_difficulty_drifts_at_most_005_per_answer_and_05_total():
    stats: dict[str, FormStats] = {}
    d = TIER_DIFFICULTY[3]
    for _ in range(40):
        up = elo_update(theta=3.0, n=0, form="card:x", tier=3, success=False, stats=stats)
        assert abs(up.d_after - up.d_before) <= 0.05 + 1e-12
        stats["card:x"] = FormStats(up.d_after, stats.get("card:x", FormStats(d, 0)).answers + 1)
    assert stats["card:x"].difficulty == pytest.approx(d + 0.5)


def test_run_of_surprises_flags_the_tier():
    stats: dict[str, FormStats] = {}
    flags = []
    for _ in range(3):
        up = elo_update(theta=3.0, n=50, form="card:x", tier=1, success=False, stats=stats)
        flags.append(up.tier_flag)
        prev = stats.get("card:x")
        stats["card:x"] = FormStats(
            up.d_after,
            (prev.answers if prev else 0) + 1,
            (*(prev.surprises if prev else ()), -up.p),
        )
    assert flags == [None, None, "harder-than-tier"]


def test_form_stats_come_from_non_voided_attempts():
    def a(i: int, d_after: float, voided: int | None = None) -> Attempt:
        return Attempt(
            id=i,
            card_id="c",
            verdict="correct",
            voided_by=voided,
            extra={"elo": {"form": "card:c", "p": 0.8, "o": 1, "d_after": d_after}},
        )

    stats = form_stats([a(1, 0.45), a(2, 0.40), a(3, 0.35, voided=9)])
    assert stats["card:c"].difficulty == 0.40
    assert stats["card:c"].answers == 2


def refs() -> list[CardRef]:
    return [
        card(1, cid="t1"),
        card(2, cid="t2.a", template="ta", seed=1),
        card(2, cid="t2.b", template="ta", seed=2),
        card(2, cid="t2.c", template="tb", seed=1),
        card(3, cid="t3"),
        card(2, cid="t2.ex", kind="example"),
    ]


def test_pick_closest_to_eighty_percent_within_the_band():
    # theta 0.886: P(tier 2) = 0.8 exactly
    theta = TIER_DIFFICULTY[2] + math.log(4)
    pick = pick_problem(refs(), theta=theta, tiers=(1, 2), now_ms=at_day(0), seen=SeenIndex())
    assert pick is not None
    assert pick.card.tier == 2
    assert pick.p == pytest.approx(0.8)
    assert pick.card.kind == "problem"


def test_pick_skips_recent_cards_and_parameter_sets():
    now = at_day(200)
    seen = SeenIndex(
        card_seen_at={"t2.a": now - 10 * DAY_MS, "t2.c": now - 91 * DAY_MS},
        params_seen_at={("tb", 1): now - 100 * DAY_MS},
    )
    pick = pick_problem(refs(), theta=0.886, tiers=(2,), now_ms=now, seen=seen)
    assert pick is not None
    assert pick.card.id == "t2.b"
    assert not pick.relaxed


def test_pick_prefers_a_different_form_from_the_last_problem():
    last = card(2, cid="t2.a", template="ta", seed=1)
    seen = SeenIndex(card_seen_at={"t2.a": at_day(0)})
    pick = pick_problem(refs(), theta=0.886, tiers=(2,), now_ms=at_day(1), seen=seen, last=last)
    assert pick is not None
    assert pick.card.id == "t2.c"


def test_pick_relaxes_rules_when_nothing_qualifies():
    now = at_day(10)
    seen = SeenIndex(card_seen_at={r.id: now - DAY_MS * (i + 1) for i, r in enumerate(refs())})
    pick = pick_problem(refs(), theta=0.886, tiers=(2,), now_ms=now, seen=seen)
    assert pick is not None
    assert pick.relaxed == ("recently seen",)
    assert pick.card.id == "t2.c"  # least recently seen of the tier-2 problems
    wide = pick_problem(refs(), theta=0.886, tiers=(5,), now_ms=now, seen=SeenIndex())
    assert wide is not None
    assert "tier widened" in wide.relaxed
    assert wide.card.tier == 3
    assert pick_problem([], theta=0.0, tiers=(2,), now_ms=now, seen=SeenIndex()) is None
    assert (
        pick_problem(
            refs(),
            theta=0.0,
            tiers=(2,),
            now_ms=now,
            seen=SeenIndex(),
            hidden=[r.id for r in refs()],
        )
        is None
    )


def test_elo_never_changes_the_schedule():
    a = Sim(learned_state(10.0, at=at_day(0)))
    b = Sim(learned_state(10.0, at=at_day(0), elo_theta=-3.0))
    ra = a.grade(outcome(at_day(10), tier=2))
    rb = b.grade(outcome(at_day(10), tier=2))
    assert ra.state.stability == rb.state.stability
    assert ra.state.due_at == rb.state.due_at
    assert ra.state.elo_theta != rb.state.elo_theta
    assert ra.answer.attempt.extra["elo"]["form"] == form_key(ra.answer.attempt.card_id, None)


def test_stretch_problem_updates_elo_only_and_asks_for_a_core_followup():
    sim = Sim(learned_state(10.0, at=at_day(0)))
    before = some(sim.state)
    miss = sim.grade(outcome(at_day(10), tier=4, correct=False))
    assert miss.effects.stage == "stretch"
    assert miss.effects.core_followup_due
    assert not miss.answer.reviews
    assert miss.answer.attempt.rating is None
    assert not miss.effects.lapse
    assert miss.state.lapses == 0
    assert miss.state.stability == before.stability
    assert miss.state.elo_theta < before.elo_theta
    hit = Sim(learned_state(10.0, at=at_day(0))).grade(outcome(at_day(10), tier=4))
    assert hit.effects.stage == "stretch"
    assert not hit.answer.reviews  # ADR-0014: stretch is unrated, right or wrong
    assert hit.state.stability == before.stability
    assert hit.state.elo_theta > before.elo_theta
    assert not hit.effects.core_followup_due


@settings(max_examples=100, deadline=None)
@given(st.floats(-4, 4), st.floats(-3, 3))
def test_p_correct_is_a_probability_and_falls_with_difficulty(theta, d):
    assert 0 < p_correct(theta, d) < 1
    assert p_correct(theta, d + 0.1) < p_correct(theta, d)
