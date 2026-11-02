"""Blame shares and the self-calibration of taps."""

import pytest

from core.engine.diagnosis import Tags, TapRecord, blame, card_tags, tap_calibration
from core.engine.diagnosis.blame import tap_share
from core.engine.diagnosis.checks import level_tier, pick_check_card, queue_order
from core.engine.selection import SeenIndex
from core.model import PendingCheck, SkillState
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, SKILLS, answer, seed, world
from tests.engine.diagnosis.memory import ref_of
from tests.engine.helpers import at_day, some

T = at_day(0)
RECALL = {CRIT: 0.9, POW: 0.5, ALG: 0.8}


def tags() -> Tags:
    return card_tags(world().card("crit.t2.0"), CRIT)


def test_tags_main_weighs_one_uses_point_four() -> None:
    t = tags()
    assert t.weights() == {CRIT: 1.0, POW: 0.4, ALG: 0.4}
    assert [s.skill_id for s in t.steps] == [CRIT, POW, ALG]


def test_tap_puts_0_6_on_the_step_and_spreads_the_rest_by_weakness() -> None:
    shares = blame(tags(), choice="step", step=1, recall=RECALL.get)
    assert shares[POW] == pytest.approx(0.6)
    # the rest 0.4 by (1 - recall) x tag weight: CRIT 0.1 x 1, ALG 0.2 x 0.4
    assert shares[CRIT] == pytest.approx(0.4 * 0.1 / 0.18)
    assert shares[ALG] == pytest.approx(0.4 * 0.08 / 0.18)
    assert sum(shares.values()) == pytest.approx(1.0)


def test_known_wrong_answer_of_that_step_raises_the_share_to_0_8() -> None:
    shares = blame(tags(), choice="step", step=2, matched=True, matched_step=2, recall=RECALL.get)
    assert shares[ALG] == pytest.approx(0.8)
    other = blame(tags(), choice="step", step=1, matched=True, matched_step=2, recall=RECALL.get)
    assert other[POW] == pytest.approx(0.6)  # the tap disagrees with the wrong answer's step


def test_without_a_tap_blame_goes_toward_the_weakest_tagged_skill() -> None:
    shares = blame(tags(), choice=None, recall=RECALL.get)
    total = 0.1 * 1 + 0.5 * 0.4 + 0.2 * 0.4
    assert shares[POW] == pytest.approx(0.2 / total)
    assert max(shares, key=shares.__getitem__) == POW
    assert blame(tags(), choice="cant-tell", recall=RECALL.get) == shares


def test_setup_blames_step_zero_and_other_method_only_the_problem() -> None:
    assert blame(tags(), choice="setup", step=None, recall=RECALL.get)[CRIT] >= 0.6
    assert blame(tags(), choice="other-method", step=None, recall=RECALL.get) == {CRIT: 1.0}


def test_untagged_card_blames_its_skill() -> None:
    t = card_tags(None, CRIT)
    assert blame(t, choice="step", step=1, recall=RECALL.get) == {CRIT: 1.0}


def records(n: int, confirmed: int) -> list[TapRecord]:
    return [
        TapRecord(at=i, choice="step", skill_id=POW, kind="step", confirmed=i < confirmed)
        for i in range(n)
    ]


def test_taps_count_for_less_when_fewer_than_half_are_confirmed() -> None:
    assert tap_calibration(records(19, 2)).factor == 1.0  # below the minimum sample
    assert tap_calibration(records(20, 10)).factor == 1.0
    cal = tap_calibration(records(20, 6))
    assert cal.rate == pytest.approx(0.3)
    assert cal.factor == pytest.approx(0.6)
    assert tap_share(matched=False, factor=cal.factor) == pytest.approx(0.36)
    assert tap_share(matched=False, factor=0.1) == pytest.approx(0.3)  # never below the floor


def test_every_resolved_tap_is_logged_and_lowers_the_weight_in_the_flow() -> None:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    t = T
    for i in range(20):  # 20 taps on step 2 whose checks all pass: never confirmed
        seed(w, CRIT, stability=20, days_ago=25, at=t)
        w.grade(answer(w, f"crit.t2.{i % 6}", t, correct=False, choice="step", step=2))
        (check,) = w.pending()
        w.grade(answer(w, some(check.card_id), t + 60_000, correct=True, check_of=check.id))
        t += 86_400_000
    log = w.tap_log(t)
    assert len(log) == 20
    assert not any(r.confirmed for r in log)
    seed(w, CRIT, stability=20, days_ago=25, at=t)
    w.grade(answer(w, "crit.t2.5", t, correct=False, choice="step", step=2))
    assert w.last.extra["diagnosis"]["blame"][ALG] == pytest.approx(0.3)


def test_check_problem_is_at_or_below_level_and_likely_solved() -> None:
    w = world()
    state = seed(w, ALG, stability=30, theta=0.0)
    assert level_tier(SKILLS[0], state) == 3
    pick = pick_check_card(
        [ref_of(c) for c in w._cards.values() if c.skill_id == ALG],
        theta=0.0,
        tiers=(1, 2),
        now_ms=T,
        seen=SeenIndex(),
    )
    assert pick is not None
    assert pick.card.tier <= 2
    assert pick.p >= 0.6
    assert level_tier(SKILLS[0], SkillState(skill_id=ALG)) == 2


def test_queue_order_serves_deepest_prerequisite_first() -> None:
    def check(i: int, skill: str, depth: int, after: int) -> PendingCheck:
        return PendingCheck(
            id=i, created_at=5, skill_id=skill, kind="prerequisite", depth=depth, after_items=after
        )

    checks = [check(1, POW, 1, 4), check(2, ALG, 2, 3)]
    assert [c.skill_id for c in queue_order(checks)] == [ALG, POW]
