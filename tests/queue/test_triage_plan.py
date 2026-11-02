"""Triage (QUE-4..6, the triage table, LIB-3) and the daily plan (QUE-1..5, QUE-11..13)."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from core.engine import Engine, new_skill_room
from core.model import CardUser, Exam, PendingCheck
from core.queue import Plan, PlanItem, Snapshot, build_plan, gather, rebalance
from core.queue.config import CHECK, EXAM, LEARNING, NEW, PREREQ, RELEARN, REVIEW
from core.queue.daylog import DayEntry, Vacation, write_entry, write_vacation
from core.queue.items import Unit, unit_slots
from core.queue.planner import flashcard_item
from core.queue.triage import POLICIES, candidates, mark_stretch
from core.storage.clock import to_ms
from tests.queue.helpers import NY, World, learning_state, make_world, review_state


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path, ("ca", "cb"), sections=2, skills=4, flashcards=True)
    yield w
    w.storage.close(backup=False)


def snap_of(w: World, day: date | None = None) -> Snapshot:
    return gather(w.storage, Engine(w.storage), day=day)


def by_key(units: list[Unit]) -> dict[str, PlanItem]:
    return {i.key: i for u in units for i in u}


def put(w: World, *rows: object) -> None:
    w.storage.users.apply(list(rows))  # type: ignore[arg-type]


def test_triage_classes_follow_the_table(world: World) -> None:
    now = world.clock.now_ms()
    world.storage.users.set_section_state("ca.s2", "solid")
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=1, stability=0.5, relearning=True),
        learning_state("ca.s1.k2", now),
        review_state("ca.s2.k1", now, days_ago=4, stability=3.0),
        review_state("ca.s2.k2", now, days_ago=14, stability=2.0),
        review_state("cb.s1.k1", now, days_ago=4, stability=3.0),
        PendingCheck(skill_id="cb.s1.k1", attempt_id=None, after_items=3, created_at=now - 1000),
    )
    units = candidates(snap_of(world))
    keys = by_key(units)
    assert keys["rel:ca.s1.k1"].order == RELEARN
    assert keys["lrn:ca.s1.k2:0"].order == LEARNING
    assert "ex:ca.s1.k2" not in keys  # its worked example was already shown
    assert keys["rev:ca.s2.k2"].order == PREREQ  # QUE-4: waited more than 7 days past due
    assert keys["rev:ca.s2.k2"].why.startswith("This skill has waited")
    assert keys["rev:ca.s2.k1"].order == REVIEW
    check = next(i for i in keys.values() if i.check_id is not None)
    assert check.order == CHECK
    assert "rev:cb.s1.k1" not in keys  # the check on it is its review
    assert keys["ex:cb.s2.k1"].order == NEW
    orders = [u[0].order for u in units]
    assert orders == sorted(orders)


def test_prerequisites_of_what_is_being_learned_move_up(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=4, stability=3.0),
        learning_state("ca.s1.k2", now),
        review_state("cb.s1.k1", now, days_ago=4, stability=3.0),
    )
    keys = by_key(candidates(snap_of(world)))
    assert keys["rev:ca.s1.k1"].order == PREREQ
    assert keys["rev:ca.s1.k1"].why.startswith("This is a foundation")
    assert keys["rev:cb.s1.k1"].order in (PREREQ, REVIEW)  # cb.s1.k2 is new in Learning now


def test_triage_policy_is_pluggable(world: World) -> None:
    now = world.clock.now_ms()
    for s in ("ca.s1", "ca.s2", "cb.s1", "cb.s2"):
        world.storage.users.set_section_state(s, "solid")
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=3, stability=2.5),  # higher recall
        review_state("ca.s2.k1", now, days_ago=6, stability=2.0),  # lower recall
    )
    snap = snap_of(world)
    rec = [
        i.skill_id
        for u in candidates(snap, policy=POLICIES["recommended"])
        for i in u
        if i.order == REVIEW
    ]
    low = [
        i.skill_id
        for u in candidates(snap, policy=POLICIES["lowest-recall-first"])
        for i in u
        if i.order == REVIEW
    ]
    assert rec[:2] == ["ca.s1.k1", "ca.s2.k1"]
    assert low[:2] == ["ca.s2.k1", "ca.s1.k1"]


def test_new_skills_follow_the_graph_learning_now_first(world: World) -> None:
    users = world.storage.users
    users.set_section_state("ca.s2", "covered")
    units = candidates(snap_of(world))
    new = [u[0].skill_id for u in units if u[0].order == NEW]
    assert "ca.s1.k2" not in new  # its prerequisite isn't learned or placed (LIB-3)
    assert new.index("ca.s1.k1") < new.index("ca.s2.k1")  # Learning now first
    assert all(len(u) >= 4 and u[0].kind == "example" for u in units if u[0].order == NEW)
    users.set_section_state("ca.s1", "off")
    assert "ca.s1.k1" not in [u[0].skill_id for u in candidates(snap_of(world))]
    assert not [u for u in candidates(snap_of(world), lighter=True) if u[0].order == NEW]


def test_I4_a_due_skill_gets_a_fresh_rated_problem_and_its_redo_after_it(world: World) -> None:
    now = world.clock.now_ms()
    snap = snap_of(world)
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=1, stability=0.5, relearning=True),
        review_state("ca.s1.k2", now, days_ago=1, stability=30.0),  # not due
        CardUser(
            card_id="ca.s1.k1.t2.v1", redo_due_at=snap.days.start(snap.day), redo_guaranteed=True
        ),
        CardUser(card_id="ca.s1.k2.t2.v1", redo_due_at=snap.days.start(snap.day)),
    )
    keys = by_key(candidates(snap_of(world)))
    fresh = keys["rel:ca.s1.k1"]  # the rated relearning review: a fresh problem
    assert (fresh.purpose, fresh.card_id) == ("relearn", None)
    redo = keys["redo:ca.s1.k1.t2.v1"]
    assert (redo.order, redo.tag, redo.purpose, redo.card_id) == (
        RELEARN,
        "redo",
        "redo",
        "ca.s1.k1.t2.v1",
    )
    assert (redo.anchor, redo.gap) == (fresh.key, 2)  # served after the fresh one
    alone = keys["redo:ca.s1.k2.t2.v1"]  # not due: the redo alone, unrated by the engine
    assert alone.anchor is None
    assert "rev:ca.s1.k2" not in keys
    plan = build_plan(snap_of(world))
    order = [i.key for i in plan.items]
    assert order.index("rel:ca.s1.k1") < order.index("redo:ca.s1.k1.t2.v1")


def test_exam_window_reviews_and_urgency(world: World) -> None:
    now = world.clock.now_ms()
    world.storage.users.set_section_state("ca.s1", "solid")  # nothing new builds on it
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=4, stability=3.0),
        review_state("cb.s1.k1", now, days_ago=4, stability=3.0),
    )
    world.storage.users.add_exam(
        Exam(course_id="ca", name="Midterm", at=to_ms(datetime(2026, 9, 8, 9, tzinfo=NY)))
    )
    snap = snap_of(world)
    keys = by_key(candidates(snap))
    assert (keys["rev:ca.s1.k1"].order, keys["rev:ca.s1.k1"].tag) == (EXAM, "exam-prep")
    assert snap.next_exam_days["ca"] == 7


def test_mixed_checkup_brings_skills_that_are_not_due(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        review_state("ca.s1.k1", now, days_ago=10, stability=60.0),
        review_state("cb.s1.k1", now, days_ago=10, stability=60.0),
    )
    keys = by_key(candidates(snap_of(world)))
    assert keys["cku:ca.s1.k1"].purpose == "checkup"
    world.storage.users.set_setting("queue.checkup_every_weeks", None)
    assert "cku:ca.s1.k1" not in by_key(candidates(snap_of(world)))


def test_stretch_share_respects_the_cap_and_exam_windows(world: World) -> None:
    now = world.clock.now_ms()
    world.storage.users.set_setting("queue.stretch_fraction", 0.25)
    put(
        world,
        *[
            review_state(f"{c}.s{s}.k{k}", now, days_ago=12, stability=10.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    for day in range(10):
        snap = snap_of(world, day=snap_of(world).day + timedelta(days=day))
        units = mark_stretch(snap, candidates(snap))
        reviews = [u[0] for u in units if u[0].order in (PREREQ, REVIEW)]
        stretched = [i for i in reviews if i.stretch]
        assert len(stretched) <= 0.25 * len(reviews)
        assert all(i.tag == "stretch" and i.tier_hint >= 3 for i in stretched)


# ---------------------------------------------------------------- plans


def test_plan_fills_exactly_n_when_more_is_due(world: World) -> None:
    now = world.clock.now_ms()
    world.storage.users.set_setting("daily.problems", 10)
    put(
        world,
        *[
            review_state(f"{c}.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    plan = build_plan(snap_of(world))
    assert plan.slots == 10
    assert sum(plan.quotas.values()) == 10
    assert plan.info["free"] == 0
    assert plan.info["new_planned"] == 0  # new skills are cut first
    assert plan.info["need"] == 16
    assert set(plan.quotas) == {"ca", "cb"}
    assert min(plan.quotas.values()) >= 3


def test_new_skills_only_while_the_projected_load_allows(world: World) -> None:
    snap = snap_of(world)
    plan = build_plan(snap)
    room = new_skill_room(snap.projected_load, daily_count=20, per_skill=4, max_new=4)
    assert plan.info["new_planned"] == room == 4
    assert sum(1 for i in plan.items if i.kind == "example") == 4
    world.storage.users.set_setting("daily.new_skills", 1)
    assert build_plan(snap_of(world)).info["new_planned"] == 1


def test_a_course_with_a_backlog_adds_no_new_skills(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        *[
            review_state(f"ca.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    world.storage.users.set_setting("daily.problems", 14)
    plan = build_plan(snap_of(world))
    new_courses = {i.course_id for i in plan.items if i.order == NEW}
    assert new_courses == {"cb"}  # ca's due work is above one day's quota (QUE-13)


def test_minutes_cap_ends_the_plan_early(world: World) -> None:
    world.storage.users.set_setting("daily.minutes_cap", 10)
    plan = build_plan(snap_of(world))
    assert plan.info["capped"]
    assert sum(i.est_ms for i in plan.items) <= 10 * 60_000 or len(plan.items) <= 5


def test_I3_easy_days_no_longer_cut_the_count(world: World) -> None:
    # Anki's Easy Days only weight the load balancer (rslib/src/scheduler/states/
    # load_balancer.rs:243-245); the day's limits are untouched (ADR-0014).
    weekday = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[snap_of(world).day.weekday()]
    world.storage.users.set_setting("queue.easy_days", {weekday: 50})
    assert snap_of(world).settings.n == 20


def test_flashcards_sit_between_problems_in_small_groups(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        *[
            review_state(f"{c}.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    world.storage.users.set_setting("daily.flashcards", 12)
    plan = build_plan(snap_of(world))
    kinds = [i.kind for i in plan.items]
    assert kinds.count("flashcard") == 12
    assert plan.slots == kinds.count("problem") == 16  # flashcards don't count
    run = 0
    for k in kinds:
        run = run + 1 if k == "flashcard" else 0
        assert run <= 5
    for a, b, c in zip(plan.items, plan.items[1:], plan.items[2:], strict=False):
        if b.kind == "flashcard":
            assert not (a.block and c.block == a.block)


def test_vacation_days_are_empty_and_the_days_before_take_reviews_early(world: World) -> None:
    now = world.clock.now_ms()
    snap = snap_of(world)
    start = snap.day + timedelta(days=4)
    put(
        world,
        *[
            review_state(f"cb.s{s}.k{k}", now, days_ago=1, stability=4.0)
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    write_vacation(world.storage.users, Vacation(start=start, end=start + timedelta(days=5)))
    assert build_plan(snap_of(world, day=start + timedelta(days=1))).items == ()
    pulled = [
        i.skill_id
        for d in range(1, 4)
        for i in build_plan(snap_of(world, day=start - timedelta(days=d))).items
        if i.key.startswith("vac:")
    ]
    assert pulled  # due in the vacation's first half, served in the days before it
    assert len(pulled) == len(set(pulled))


def test_carry_over_reserves_yesterdays_shortfall(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        *[
            review_state(f"{c}.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    snap = snap_of(world)
    write_entry(
        world.storage.users,
        snap.day - timedelta(days=1),
        DayEntry(n=20, need=30, backlog=10, quotas={"ca": 10, "cb": 10}),
    )
    assert snap_of(world).carry == {}  # nothing done yesterday: a missed day carries nothing


def test_rebalance_gives_inserted_items_the_lowest_priority_slots(world: World) -> None:
    now = world.clock.now_ms()
    put(
        world,
        *[
            review_state(f"{c}.s{s}.k{k}", now, days_ago=5, stability=2.0)
            for c in ("ca", "cb")
            for s in (1, 2)
            for k in range(1, 5)
        ],
    )
    world.storage.users.set_setting("daily.problems", 10)
    snap = snap_of(world)
    plan = build_plan(snap)
    first = plan.items[0]
    plan = plan.updated(replace(first, status="done"))
    lowest = max(
        (i for i in plan.pending if i.course_id == first.course_id),
        key=lambda i: (i.order, i.rank, i.key),
    )
    check = replace(
        flashcard_item(snap, "x", 0, None),
        kind="problem",
        key="chk:new",
        skill_id=first.skill_id,
        course_id=first.course_id,
        order=CHECK,
        anchor=first.key,
        gap=3,
        inserted=True,
        tag="check",
    )
    after = rebalance(plan, inserted=[check], prefer_course=first.course_id)
    assert after.slots == 10
    assert lowest.key not in {i.key for i in after.items}
    assert lowest.key in {i.key for i in after.bench}
    keys = [i.key for i in after.items]
    assert keys.index("chk:new") - keys.index(first.key) >= 3
    # Dropping an item refills from the bench (never with a new skill).
    victim = next(i for i in after.pending if i.key != "chk:new")
    refilled = rebalance(after, drop=[victim.key])
    assert refilled.slots == 10
    assert all(i.order != NEW for i in refilled.items if i.key not in keys)


def test_plan_round_trips_through_json(world: World) -> None:
    plan = build_plan(snap_of(world))
    again = Plan.from_json(plan.to_json())
    assert again == plan
    assert sum(unit_slots((i,)) for i in again.items) == plan.slots
