"""The order of the day (design 4.3, 4.5): new first, mixed set, checks, confusable pairs."""

from itertools import pairwise

from core.plan.order import confusable_pairs, order
from core.plan.types import WorkItem
from tests.plan.helpers import problem, rng, skill


def wi(sid: str, n: int = 1, *, role: str = "growth", missed: bool = False) -> WorkItem:
    return WorkItem(
        skill_id=sid,
        role=role,  # type: ignore[arg-type]
        problem=problem(f"{sid}.{role}.{n}", sid, 3),
        example_card=None,
        expected_minutes=3.0,
        priority=2 if missed else 1,
        missed=missed,
    )


def block(sid: str, n: int = 3) -> list[WorkItem]:
    ex = WorkItem(sid, "new", None, f"ex.{sid}", 2.0, 0, block=True)
    return [ex] + [
        WorkItem(sid, "new", problem(f"{sid}.new.{i}", sid, 1), None, 2.0, 0, block=True)
        for i in range(1, n + 1)
    ]


def check(sid: str, n: int = 1) -> WorkItem:
    return WorkItem(sid, "check", problem(f"{sid}.chk.{n}", sid, 3), None, 3.0, 1)


def no_adjacent_pairs(items: list[WorkItem] | tuple[WorkItem, ...]) -> bool:
    return all(x.skill_id != y.skill_id or (x.block and y.block) for x, y in pairwise(items))


def test_new_blocks_come_first_whole_and_in_order() -> None:
    got = order([block("a"), block("b")], [wi("c"), wi("d")], rng=rng())
    assert [i.skill_id for i in got.items] == ["a"] * 4 + ["b"] * 4 + ["c", "d"]


def test_a_block_in_progress_goes_first_and_may_follow_its_own_skill() -> None:
    served = block("b")[:2]
    got = order([block("a"), block("b")[2:]], [wi("c")], rng=rng(), served=served, continuing="b")
    assert [i.skill_id for i in got.items] == ["b", "b", "a", "a", "a", "a", "c"]


def test_mixed_set_never_puts_one_skill_twice_in_a_row() -> None:
    """a x3, b x2, c x1: 6 items, a fills every other place: a b a c a b (or similar)."""
    items = [wi("a", 1), wi("a", 2), wi("a", 3), wi("b", 1), wi("b", 2), wi("c", 1)]
    got = order([], items, rng=rng())
    assert len(got.items) == 6
    assert no_adjacent_pairs(got.items)
    assert got.dropped == ()


def test_items_that_cannot_be_separated_are_dropped() -> None:
    """Three a's and nothing else: one is served, two dropped. After a served a, the only a
    can't go at all. The block's last a can't be followed by another a either."""
    got = order([], [wi("a", 1), wi("a", 2), wi("a", 3)], rng=rng())
    assert (len(got.items), len(got.dropped)) == (1, 2)
    got = order([], [wi("a", 1)], rng=rng(), served=[wi("a", 9)])
    assert (got.items, len(got.dropped)) == ((), 1)
    got = order([block("a")], [wi("a", 1)], rng=rng())
    assert (len(got.items), len(got.dropped)) == (4, 1)


def test_every_tenth_item_is_a_check() -> None:
    """12 regular items of distinct skills: positions 1-9 regular, 10 the check, 11-13
    regular. The second check (due at 20) is never reached and goes unused."""
    mixed = [wi(f"s{i}") for i in range(12)]
    got = order([], mixed, [check("x"), check("y")], rng=rng())
    roles = [i.role for i in got.items]
    assert len(got.items) == 13
    assert roles.index("check") == 9
    assert roles.count("check") == 1


def test_a_check_due_inside_a_new_block_follows_the_block() -> None:
    """Blocks of 4 fill positions 1-12; the 10th falls in the third block, so the check is
    13th, right after it."""
    got = order([block("a"), block("b"), block("c")], [wi("d"), wi("e")], [check("x")], rng=rng())
    assert [i.role for i in got.items][12] == "check"
    assert [i.skill_id for i in got.items][:12] == ["a"] * 4 + ["b"] * 4 + ["c"] * 4


def test_a_check_whose_skill_was_just_served_waits_one_item() -> None:
    """Nine plan items served, the last of skill a; the check (skill a) can't be 10th next
    to it, so a regular item of another skill goes first and the check is 11th."""
    served = [wi(f"s{i}") for i in range(8)] + [wi("a", 9)]
    got = order([], [wi("b"), wi("c")], [check("a")], rng=rng(), served=served)
    assert [i.role for i in got.items] == ["growth", "check", "growth"]
    assert no_adjacent_pairs([served[-1], *got.items])


def test_checks_keep_their_skill_off_both_neighbours() -> None:
    """The check (skill b) is 10th; the 9th and 11th items are not b."""
    mixed = [wi("a", 1), wi("b", 1), wi("a", 2), wi("b", 2), wi("c", 1)] + [
        wi(f"s{i}") for i in range(8)
    ]
    got = order([], mixed, [check("b")], rng=rng())
    seq = list(got.items)
    assert seq[9].role == "check"
    assert seq[8].skill_id != "b"
    assert seq[10].skill_id != "b"
    assert no_adjacent_pairs(seq)


def test_missed_items_are_spread_evenly_and_the_overflow_comes_last() -> None:
    """6 regular + 4 missed (share 0.4): no prefix holds more than 40% missed. The tail's two
    missed items come after everything else."""
    mixed = [wi(f"r{i}") for i in range(6)] + [wi(f"m{i}", missed=True) for i in range(4)]
    got = order([], mixed, rng=rng(), tail=[wi("t1", missed=True), wi("t2", missed=True)])
    seq = list(got.items)
    for k in range(1, 11):
        assert sum(i.missed for i in seq[:k]) <= 0.4 * k + 1e-9
    assert [i.skill_id for i in seq[-2:]] == ["t1", "t2"]


def seed_for(adjacent: bool) -> int:
    """A seed whose first draw puts the pair adjacent (< 0.5) or apart."""
    return next(s for s in range(100) if (rng(s).random() < 0.5) == adjacent)


def test_confusable_pairs_are_drawn_adjacent_or_apart_and_logged() -> None:
    """Pair (a, b) with other skills around. Drawn adjacent: one a and one b are glued, and
    the log says placed. Drawn apart: they don't touch."""
    mixed = [wi("a"), wi("x"), wi("y"), wi("z"), wi("b")]
    got = order([], mixed, rng=rng(seed_for(True)), confusable=[("a", "b")])
    assert len(got.confusable) == 1
    d = got.confusable[0]
    assert (d.a, d.b, d.adjacent, d.placed) == ("a", "b", True, True)
    got = order([], mixed, rng=rng(seed_for(False)), confusable=[("a", "b")])
    d = got.confusable[0]
    assert (d.adjacent, d.placed) == (False, False)
    seq = [i.skill_id for i in got.items]
    assert abs(seq.index("a") - seq.index("b")) > 1


def test_pairs_absent_from_the_plan_draw_nothing() -> None:
    got = order([], [wi("a"), wi("c")], rng=rng(), confusable=[("a", "b")])
    assert got.confusable == ()


def test_confusable_pairs_come_from_the_skills_lists() -> None:
    skills = [
        skill("b", "K::U::A", 1, confusable=["a"]),
        skill("a", "K::U::A", 2, confusable=["b", "c", "a"]),
    ]
    assert confusable_pairs(skills) == [("a", "b"), ("a", "c")]


def test_the_same_seed_gives_the_same_order() -> None:
    mixed = [wi(s, n) for s in "abcde" for n in (1, 2)]
    pairs = [("a", "b"), ("c", "d")]
    one = order([block("n")], mixed, [check("z")], rng=rng(7), confusable=pairs)
    two = order([block("n")], mixed, [check("z")], rng=rng(7), confusable=pairs)
    assert one == two
