"""How the session is ordered: unit tests per rule and Hypothesis properties on random plans."""

from collections import Counter
from collections.abc import Sequence
from itertools import pairwise

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from core.queue.config import CHECK, NEW, RELEARN, REVIEW
from core.queue.items import PlanItem
from core.queue.order import order_items


def item(
    key: str,
    skill: str,
    *,
    course: str = "a",
    section: str | None = None,
    order: int = REVIEW,
    rank: float = 0.0,
    tier: float = 2.0,
    block: str | None = None,
    kind: str = "problem",
    anchor: str | None = None,
    gap: int = 0,
    tag: str = "review",
    status: str = "pending",
) -> PlanItem:
    return PlanItem(
        key=key,
        kind=kind,  # type: ignore[arg-type]
        skill_id=skill,
        course_id=course,
        section_id=section or f"{course}.{skill}",
        order=order,
        rank=rank,
        tag=tag,  # type: ignore[arg-type]
        tier_hint=tier,
        block=block,
        anchor=anchor,
        gap=gap,
        status=status,  # type: ignore[arg-type]
    )


def block(skill: str, n: int = 3, *, course: str = "a", order: int = NEW) -> list[PlanItem]:
    b = f"blk:{skill}"
    out = [
        item(
            f"ex:{skill}",
            skill,
            course=course,
            order=order,
            block=b,
            kind="example",
            tag="new-skill",
            tier=1.0,
        )
    ]
    out += [
        item(
            f"lrn:{skill}:{i}",
            skill,
            course=course,
            order=order,
            block=b,
            tag="new-skill",
            tier=1.5,
        )
        for i in range(n)
    ]
    return out


def keys(items: Sequence[PlanItem]) -> list[str]:
    return [i.key for i in items]


def test_learning_block_is_one_unit_and_never_first() -> None:
    items = block("n1") + [item(f"r{i}", f"s{i}") for i in range(4)]
    out = order_items([], items, shares={"a": 1})
    assert out[0].block is None
    start = keys(out).index("ex:n1")
    assert keys(out)[start : start + 4] == ["ex:n1", "lrn:n1:0", "lrn:n1:1", "lrn:n1:2"]


def test_a_started_block_continues_after_a_replan() -> None:
    items = block("n1")
    done = [replace_status(items[0]), replace_status(items[1])]
    pending = [*items[2:], item("r1", "s1"), item("r2", "s2")]
    out = order_items(done, pending, shares={"a": 1})
    assert keys(out)[:2] == ["lrn:n1:1", "lrn:n1:2"]


def replace_status(i: PlanItem) -> PlanItem:
    from dataclasses import replace

    return replace(i, status="done")


def test_warmup_opens_with_quick_reviews() -> None:
    items = [item("chk", "c1", order=CHECK, tag="check"), *block("n1")]
    items += [item(f"r{i}", f"s{i}", tier=2.0, rank=i) for i in range(3)]
    items += [item(f"h{i}", f"h{i}", tier=3.5, rank=10 + i) for i in range(3)]
    out = order_items([], items, shares={"a": 1})
    assert {i.key for i in out[:3]} <= {"r0", "r1", "r2"}


def test_same_section_items_sit_apart_where_possible() -> None:
    items = [item(f"x{i}", f"x{i}", section="sec.x", rank=i) for i in range(3)]
    items += [item(f"y{i}", f"y{i}", section=f"sec.y{i}", rank=10 + i) for i in range(3)]
    out = order_items([], items, shares={"a": 1}, warmup=False)
    sections = [i.section_id for i in out]
    assert all(a != b or a != "sec.x" for a, b in pairwise(sections))


def test_confusable_skills_sit_one_to_three_apart() -> None:
    items = [item(f"r{i}", f"s{i}", rank=i) for i in range(8)]
    items += [item("p", "conf.p", rank=1.5), item("q", "conf.q", rank=20)]
    out = order_items(
        [],
        items,
        shares={"a": 1},
        warmup=False,
        confusable={"conf.p": frozenset({"conf.q"}), "conf.q": frozenset({"conf.p"})},
    )
    pos = {k: n for n, k in enumerate(keys(out))}
    assert 1 <= abs(pos["p"] - pos["q"]) <= 3


def test_harder_and_easier_alternate_when_they_can() -> None:
    items = [item(f"e{i}", f"e{i}", tier=1.5, rank=i) for i in range(3)]
    items += [item(f"h{i}", f"h{i}", tier=3.5, rank=i + 0.5) for i in range(3)]
    out = order_items([], items, shares={"a": 1}, warmup=False)
    hard = [i.tier_hint >= 2.5 for i in out]
    assert all(a != b for a, b in pairwise(hard))


def test_reinforcement_and_check_wait_their_distance() -> None:
    done = [item("miss", "m", status="done")]
    pending = [
        item("rf", "m", order=RELEARN, anchor="miss", gap=5, tag="relearn"),
        item("chk", "c", order=CHECK, anchor="miss", gap=3, tag="check"),
    ] + [item(f"r{i}", f"s{i}", rank=i) for i in range(6)]
    out = order_items(done, pending, shares={"a": 1})
    pos = {k: n + 1 for n, k in enumerate(keys(out))}  # the miss sits at 0
    assert pos["rf"] >= 5
    assert pos["chk"] >= 3
    assert pos["chk"] == 3  # as soon as allowed


def test_courses_are_interleaved_by_quota() -> None:
    items = [item(f"a{i}", f"a{i}", course="a", rank=i) for i in range(10)]
    items += [item(f"b{i}", f"b{i}", course="b", rank=i) for i in range(5)]
    out = order_items([], items, shares={"a": 10, "b": 5}, warmup=False)
    courses = "".join(i.course_id or "" for i in out)
    for n in range(1, len(courses) + 1):
        assert abs(courses[:n].count("a") - n * 10 / 15) <= 1.5, courses


# ---------------------------------------------------------------- properties


@st.composite
def plans(draw: st.DrawFn) -> tuple[list[PlanItem], dict[str, float]]:
    n_courses = draw(st.integers(1, 3))
    courses = [f"c{i}" for i in range(n_courses)]
    n = draw(st.integers(1, 24))
    skills = draw(st.integers(1, 10))
    items: list[PlanItem] = []
    for i in range(n):
        s = draw(st.integers(0, skills - 1))
        course = courses[s % n_courses]
        items.append(
            item(
                f"i{i}",
                f"{course}.k{s}",
                course=course,
                section=f"{course}.sec{s % 3}",
                order=draw(st.sampled_from([CHECK, RELEARN, 4, 5, REVIEW])),
                rank=draw(st.floats(0, 1)),
                tier=draw(st.sampled_from([1.5, 2.0, 2.5, 3.0, 4.0])),
            )
        )
    for b in range(draw(st.integers(0, 2))):
        course = courses[b % n_courses]
        items += block(f"{course}.new{b}", draw(st.integers(1, 4)), course=course)
    shares = {c: float(draw(st.integers(1, 10))) for c in courses}
    return items, shares


@settings(max_examples=150, deadline=None)
@given(plans())
def test_ordering_properties(plan: tuple[list[PlanItem], dict[str, float]]) -> None:
    items, shares = plan
    out = order_items([], items, shares=shares)
    # A permutation of the input.
    assert sorted(keys(out)) == sorted(keys(items))
    # Blocks: contiguous, worked example first, never first when anything else exists.
    blocks = {i.block for i in items if i.block}
    for b in blocks:
        where = [n for n, i in enumerate(out) if i.block == b]
        assert where == list(range(where[0], where[0] + len(where)))
        assert out[where[0]].kind == "example"
    if blocks and any(i.block is None for i in items):
        assert out[0].block is None
    # No skill back to back (outside a block) whenever the counts allow it.
    units = Counter(i.skill_id for i in items if i.block is None) + Counter(
        i.skill_id for i in items if i.kind == "example"
    )
    total = sum(units.values())
    if max(units.values(), default=0) <= (total + 1) // 2:
        for x, y in pairwise(out):
            if x.block is not None and x.block == y.block:
                continue
            assert x.skill_id != y.skill_id, keys(out)


@settings(max_examples=100, deadline=None)
@given(plans(), st.integers(0, 6))
def test_anchored_items_keep_their_distance(
    plan: tuple[list[PlanItem], dict[str, float]], gap: int
) -> None:
    items, shares = plan
    singles = [i for i in items if i.block is None]
    assume(len(singles) > gap + 1)
    done = [item("miss", "zz.miss", course="c0", status="done")]
    anchored = item("rf", "zz.miss", course="c0", order=RELEARN, anchor="miss", gap=gap)
    out = order_items(done, [*items, anchored], shares=shares)
    pos = keys(out).index("rf") + 1
    assert pos >= gap
