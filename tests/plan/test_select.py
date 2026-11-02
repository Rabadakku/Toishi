"""Choosing the problem (design 4.4) and the variety rules."""

from collections import Counter
from collections.abc import Callable, Mapping
from datetime import date, timedelta

import pytest

from core.learner.types import Prediction, ProblemSpec, UpdateRecord
from core.plan.select import (
    Seen,
    band_midpoint,
    choose,
    choose_check,
    choose_growth,
    choose_growth_in,
    choose_maintenance,
    choose_new,
    choose_prerequisite,
    choose_problem,
    choose_return,
    choose_sitting,
    is_template_instance,
    suspects,
)
from core.plan.types import ServedItem, WorkItem
from tests.plan.helpers import Log, problem, rng, skill

TODAY = date(2026, 10, 1)


def predict_from(table: Mapping[str, float]) -> Callable[[ProblemSpec], Prediction]:
    """A Predict that returns p = table[problem_id] (q, e, r unused here)."""

    def predict(p: ProblemSpec) -> Prediction:
        v = table[p.problem_id]
        return Prediction(p=v, p_raw=v, q=(), e=(), r=(), median_minutes=3.0, pace_ok=True)

    return predict


def seen(log: Log | None = None, served: list[ServedItem] | None = None) -> Seen:
    return Seen(log.items if log else [], TODAY, served or [])


def test_new_takes_tier_1_2_problems_highest_chance_first() -> None:
    """t1.01 0.95, t1.02 0.97, t2.01 0.99, t3.01 0.999 (tier 3 is not a new problem):
    t2.01 wins."""
    probs = [
        problem("t1.01", "s", 1),
        problem("t1.02", "s", 1),
        problem("t2.01", "s", 2),
        problem("t3.01", "s", 3),
    ]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"t1.01": 0.95, "t1.02": 0.97, "t2.01": 0.99, "t3.01": 0.999})
    got = choose_new(sk, pred, seen())
    assert got is not None
    assert (got.problem.problem_id, got.p, got.reason) == ("t2.01", 0.99, "new")


def test_growth_band_prefers_the_bottleneck_over_closeness_to_080() -> None:
    """Milestone tier 3. In the band [0.70, 0.90]: b (0.85, contains bottleneck k) and
    c (0.80, without it); a (0.95) and d (0.60) are outside. The bottleneck wins: b."""
    probs = [
        problem("a", "s", 3),
        problem("b", "s", 3, uses=["k"]),
        problem("c", "s", 3),
        problem("d", "s", 2),
    ]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"a": 0.95, "b": 0.85, "c": 0.80, "d": 0.60})
    got = choose_growth(sk, 3, pred, seen(), bottleneck="k")
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("b", "bottleneck")


def test_growth_uses_the_milestone_tier_or_one_below_and_prefers_the_milestone_tier() -> None:
    """Milestone tier 3: x (tier 2, 0.80) and y (tier 3, 0.75) are both in the band with no
    bottleneck: y, at the milestone tier, wins over x's exact 0.80. z (tier 1) never counts."""
    probs = [problem("x", "s", 2), problem("y", "s", 3), problem("z", "s", 1)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"x": 0.80, "y": 0.75, "z": 0.80})
    got = choose_growth(sk, 3, pred, seen())
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("y", "band")


def test_empty_band_falls_back_to_the_problem_closest_to_080() -> None:
    """0.95 (|0.15|), 0.60 (|0.20|), 0.66 (|0.14|): 0.66 is closest."""
    probs = [problem("a", "s", 3), problem("b", "s", 3), problem("c", "s", 3)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    got = choose_growth(sk, 3, predict_from({"a": 0.95, "b": 0.60, "c": 0.66}), seen())
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("c", "fallback")


def test_the_owners_harder_band_and_its_midpoint_fallback() -> None:
    """Wave 2 section 3: with the band (0.50, 0.75), a (0.85) and c (0.40) are out and b
    (0.70) in; with no problem inside it, the fallback is the problem closest to its
    midpoint 0.625 (c at 0.45), where the default band takes a."""
    probs = [problem("a", "s", 3), problem("b", "s", 3), problem("c", "s", 3)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"a": 0.85, "b": 0.70, "c": 0.40})
    got = choose_growth_in((0.50, 0.75), sk, 3, pred, seen())
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("b", "band")
    out = predict_from({"a": 0.85, "b": 0.95, "c": 0.45})
    got = choose_growth_in((0.50, 0.75), sk, 3, out, seen())
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("c", "fallback")  # |0.45 - 0.625| < 0.225
    got = choose_growth(sk, 3, out, seen())
    assert got is not None
    assert got.problem.problem_id == "a"  # inside the default band [0.70, 0.90]
    assert band_midpoint((0.50, 0.75)) == pytest.approx(0.625)


def test_spread_blame_prefers_the_top_suspect_without_the_runner_up() -> None:
    """Suspects (k1, k2). P1 has both, P2 has k1 only, P3 has k2 only, all in the band and P1
    closest to 0.80: P2 wins."""
    probs = [
        problem("p1", "s", 3, uses=["k1", "k2"]),
        problem("p2", "s", 3, uses=["k1"]),
        problem("p3", "s", 3, uses=["k2"]),
    ]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"p1": 0.80, "p2": 0.88, "p3": 0.80})
    got = choose_growth(sk, 3, pred, seen(), bottleneck="k2", suspect=("k1", "k2"))
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("p2", "suspect")


def served_miss(blame: tuple[tuple[str, float], ...], *, correct: bool = False) -> ServedItem:
    p = problem("x", "s", 3, uses=["k1", "k2"])
    item = WorkItem("s", "growth", p, None, 3.0, 1)
    pred = Prediction(p=0.8, p_raw=0.8, q=(), e=(), r=(), median_minutes=3.0, pace_ok=True)
    return ServedItem(item, correct=correct, update=UpdateRecord(pred, blame, ()))


def test_suspects_need_a_latest_miss_with_spread_blame() -> None:
    """Blame k1 0.6, k2 0.3, s 0.1: top suspect below 0.7 -> (k1, k2). Top 0.8: not
    spread. A success or another skill's miss: nothing."""
    spread = served_miss((("k1", 0.6), ("k2", 0.3), ("s", 0.1)))
    assert suspects([spread], "s") == ("k1", "k2")
    pinned = served_miss((("k1", 0.8), ("k2", 0.2)))
    assert suspects([pinned], "s") == ()
    assert suspects([spread, served_miss((), correct=True)], "s") == ()
    assert suspects([spread], "other") == ()


def test_maintenance_takes_the_problem_closest_to_target() -> None:
    probs = [problem("a", "s", 4), problem("b", "s", 4), problem("c", "s", 4)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    got = choose_maintenance(
        sk, 4, predict_from({"a": 0.95, "b": 0.91, "c": 0.85}), seen(), target=0.9
    )
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("b", "target")


def test_no_card_twice_in_a_study_day_even_when_relaxed() -> None:
    probs = [problem("a", "s", 4), problem("b", "s", 4)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    log = Log()
    log.add(probs[0], TODAY, True)
    s = seen(log)
    got = choose_maintenance(sk, 4, predict_from({"a": 0.9, "b": 0.5}), s, target=0.9)
    assert got is not None
    assert got.problem.problem_id == "b"
    s.add("b")
    assert choose_maintenance(sk, 4, predict_from({"a": 0.9, "b": 0.5}), s, target=0.9) is None


def test_no_repeat_within_90_days_while_the_pool_allows() -> None:
    """a (best match) was seen 30 days ago, b never: b. When every card was seen in the
    window, the rule relaxes and the role's order decides, the least recently seen breaking
    ties."""
    probs = [problem("a", "s", 4), problem("b", "s", 4), problem("c", "s", 4)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"a": 0.9, "b": 0.8, "c": 0.8})
    log = Log()
    log.add(probs[0], TODAY - timedelta(days=30), True)
    got = choose_maintenance(sk, 4, pred, seen(log), target=0.9)
    assert got is not None
    assert (got.problem.problem_id, got.relaxed) == ("b", False)
    log.add(probs[1], TODAY - timedelta(days=10), True)
    log.add(probs[2], TODAY - timedelta(days=20), True)
    got = choose_maintenance(sk, 4, pred, seen(log), target=0.9)
    assert got is not None
    assert (got.problem.problem_id, got.relaxed) == ("a", True)
    got = choose_maintenance(sk, 4, pred, seen(log), target=0.8)
    assert got is not None
    assert got.problem.problem_id == "c"  # b and c tie at 0.8; c was seen longer ago


def test_template_instances_wait_180_days() -> None:
    """A template instance (family = template id) seen 100 days ago is not fresh; a plain
    card seen 100 days ago is."""
    inst = problem("tpl--0001", "s", 4, family="tpl")
    plain = problem("plain", "s", 4)
    assert is_template_instance(inst)
    assert not is_template_instance(plain)
    log = Log()
    log.add(inst, TODAY - timedelta(days=100), True)
    log.add(plain, TODAY - timedelta(days=100), True)
    s = seen(log)
    assert not s.fresh(inst)
    assert s.fresh(plain)
    log.add(problem("tpl--0002", "s", 4, family="tpl"), TODAY - timedelta(days=181), True)
    assert seen(log).fresh(problem("tpl--0002", "s", 4, family="tpl"))


def test_a_different_surface_form_from_the_previous_problem_when_possible() -> None:
    """Two template families, equally good: the one the previous problem did not use."""
    probs = [problem("f1--01", "s", 4, family="f1"), problem("f2--01", "s", 4, family="f2")]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"f1--01": 0.9, "f2--01": 0.9})
    prev = problem("f1--00", "s", 4, family="f1")
    got = choose_maintenance(sk, 4, pred, seen(), target=0.9, previous=prev)
    assert got is not None
    assert got.problem.problem_id == "f2--01"


def test_check_is_uniform_over_unseen_problems_at_the_tier() -> None:
    """Five tier-3 problems, one already seen: over 4,000 seeded draws each of the four
    unseen ones comes up 1,000 +- 120 times (about 4 standard deviations); the seen one and
    other tiers never."""
    probs = [problem(f"t3.{i}", "s", 3) for i in range(5)] + [problem("t4.0", "s", 4)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    log = Log()
    log.add(probs[0], TODAY - timedelta(days=400), True)
    s = seen(log)
    gen = rng(42)
    counts = Counter(choose_check(sk, 3, s, gen).problem_id for _ in range(4000))  # type: ignore[union-attr]
    assert set(counts) == {"t3.1", "t3.2", "t3.3", "t3.4"}
    assert all(abs(n - 1000) < 120 for n in counts.values())
    again = rng(42)
    first = choose_check(sk, 3, s, again)
    assert first is not None
    assert first.problem_id == choose_check(sk, 3, s, rng(42)).problem_id  # type: ignore[union-attr]


def test_choose_dispatches_and_rejects_roles_it_does_not_plan() -> None:
    probs = [problem("a", "s", 1), problem("b", "s", 3)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    pred = predict_from({"a": 0.9, "b": 0.8})
    assert choose_problem("new", sk, 0, pred, seen()) == probs[0]
    assert choose_problem("growth", sk, 3, pred, seen()) == probs[1]
    assert choose_problem("maintenance", sk, 3, pred, seen(), target=0.9) == probs[1]
    found = choose("check", sk, 3, pred, seen(), rng=rng(1))
    assert found is not None
    assert found.reason == "check"
    with pytest.raises(ValueError, match="needs the random"):
        choose("check", sk, 3, pred, seen())
    with pytest.raises(ValueError, match="no problems for role"):
        choose("focused", sk, 3, pred, seen())


def test_the_prerequisite_problem_is_tier_1_2_never_served_first() -> None:
    """Rung 2: p's tier 1-2 problems; t2.01 was served, so t1.01 and t2.02 remain, both
    unseen: the one closest to the band's midpoint (0.80): t2.02 at 0.78. Tier 3 never."""
    probs = [problem(f"p.{n}", "p", t) for n, t in (("t1.01", 1), ("t2.01", 2), ("t2.02", 2))]
    sk = skill("p", "C::U::A", 1, problems=[*probs, problem("p.t3.01", "p", 3)])
    log = Log()
    log.add(probs[1], TODAY - timedelta(days=1), True)
    pred = predict_from({"p.t1.01": 0.95, "p.t2.01": 0.8, "p.t2.02": 0.78, "p.t3.01": 0.8})
    got = choose_prerequisite(sk, pred, seen(log))
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("p.t2.02", "ladder:prerequisite")


def test_the_return_problem_is_from_a_family_not_served_in_seven_days() -> None:
    """The tier-3 families f1 (served 3 days ago) and f2 (served 9 days ago), and f3 unseen:
    f1 is out; f2 and f3 qualify, and their problems were never served, so the lower id
    wins (s.t3.f2). With f2 and f3 also served within the week, none qualifies."""
    probs = [problem(f"s.t3.{f}", "s", 3, family=f) for f in ("f1", "f2", "f3")]
    sk = skill("s", "C::U::A", 1, problems=probs)
    log = Log()
    log.add(problem("s.t3.f1b", "s", 3, family="f1"), TODAY - timedelta(days=3), False)
    log.add(problem("s.t3.f2b", "s", 3, family="f2"), TODAY - timedelta(days=9), False)
    pred = predict_from({p.problem_id: 0.8 for p in probs})
    got = choose_return(sk, 3, pred, seen(log), days=7)
    assert got is not None
    assert (got.problem.problem_id, got.reason) == ("s.t3.f2", "return")
    log.add(probs[1], TODAY - timedelta(days=2), False)
    log.add(probs[2], TODAY - timedelta(days=1), False)
    assert choose_return(sk, 3, pred, seen(log), days=7) is None


def test_sitting_problems_are_unseen_from_different_families_and_uniform() -> None:
    """Four families with unseen tier-3 problems: 3 problems from 3 different families, all
    unseen; over 3,000 draws every unseen problem comes up. With one unseen family the pool
    is thin: unseen first, then the least recently served, one per family. Fewer than 2
    usable problems: no sitting."""
    probs = [problem(f"s.{f}.{k}", "s", 3, family=f) for f in "wxyz" for k in (1, 2)]
    sk = skill("s", "C::U::A", 1, problems=probs)
    log = Log()
    log.add(probs[0], TODAY - timedelta(days=5), True)  # w.1 seen
    gen = rng(5)
    counts: Counter[str] = Counter()
    for _ in range(3000):
        pick = choose_sitting(sk, 3, seen(log), gen)
        assert pick is not None
        assert not pick.thin
        assert len(pick.problems) == 3
        assert len({p.family for p in pick.problems}) == 3
        assert "s.w.1" not in {p.problem_id for p in pick.problems}
        counts.update(p.problem_id for p in pick.problems)
    assert set(counts) == {p.problem_id for p in probs[1:]}
    thin_log = Log()
    for k, p in enumerate(probs[:6]):  # w, x and y seen, oldest first; z unseen
        thin_log.add(p, TODAY - timedelta(days=10 - k), True)
    pick = choose_sitting(sk, 3, seen(thin_log), rng(1))
    assert pick is not None
    assert pick.thin
    assert [p.problem_id for p in pick.problems] == ["s.z.1", "s.w.1"]
    lone = skill("s", "C::U::A", 1, problems=probs[:1])
    assert choose_sitting(lone, 3, seen(), rng(1)) is None
