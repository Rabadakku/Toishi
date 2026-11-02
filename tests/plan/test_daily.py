"""The day's plan (design 4.3, 4.6): new blocks, growth, maintenance, checks, caps, minutes,
hours to keep pace and the feasibility note."""

from collections import Counter
from collections.abc import Sequence
from datetime import date, timedelta
from itertools import pairwise

import pytest

from core.learner.types import Prediction, ProblemSpec, UpdateRecord
from core.plan.certify import Certifier, model_priors
from core.plan.daily import (
    _nearest,
    attempt_minutes,
    feasibility,
    main_share,
    next_item,
    plan_day,
)
from core.plan.types import CourseSettings, DayPlan, ExamSpec, ServedItem, WorkItem
from tests.plan.fakes import DAY_MS, FakeState
from tests.plan.helpers import Log, at, course, fake, pool, problem, rng, skill

A, B, C = "K::U1::A", "K::U1::B", "K::U2::C"
D0 = date(2026, 9, 1)  # A on day 0, B on day 7, C on day 14 (2 h sections, 2 h a week)


def day(n: int) -> date:
    return D0 + timedelta(days=n)


def big(sid: str) -> tuple[ProblemSpec, ...]:
    return pool(sid, {1: 3, 2: 6, 3: 6, 4: 6})


COURSE = course(
    [(A, 2.0), (B, 2.0), (C, 2.0)],
    [
        skill("a1", A, 1, example="ex.a1", problems=big("a1")),
        skill("a2", A, 2, problems=big("a2")),
        skill("a3", A, 3, problems=big("a3")),
        skill("b1", B, 4, requires=["a1"], problems=big("b1")),
        skill("b2", B, 5, problems=big("b2")),
        skill("c1", C, 6, problems=big("c1")),
    ],
)
SK = {s.skill_id: s for s in COURSE.skills}
INTRO = {"a1": 0, "a2": 0, "a3": 0, "b1": 7, "b2": 7, "c1": 14}
MODEL = fake(COURSE)
SETTINGS = CourseSettings("c", start=D0)


def plan(
    log: Log,
    today: date,
    *,
    state: FakeState | None = None,
    settings: CourseSettings = SETTINGS,
    served: Sequence[ServedItem] = (),
    seed: int = 0,
    spent: dict[int, float] | None = None,
) -> DayPlan:
    state = state or FakeState()
    priors = model_priors(MODEL, state, COURSE, at(today))
    cert = Certifier.for_course(log.items, COURSE, settings, today=today, priors=priors)
    return plan_day(
        MODEL,
        state,
        cert,
        COURSE,
        settings,
        today,
        at(today, 600),
        served,
        rng=rng(seed),
        spent_minutes=spent,
    )


def blocks_done(log: Log, *skills: str) -> None:
    """Each skill's block ended with a tier-1 success on its introduction day."""
    for s in skills:
        log.add(SK[s].pool[0], day(INTRO[s]), True, role="new")


def serve(
    log: Log, served: list[ServedItem], item: WorkItem, today: date, correct: bool | None
) -> None:
    """Record a served item (and its first try) the way wave 2 will."""
    if item.problem is not None and correct is not None:
        log.add(item.problem, today, correct, minutes=3.0, role=item.role)
    served.append(ServedItem(item, correct=correct))


def roles(p: DayPlan) -> list[str]:
    return [i.role for i in p.items]


def test_new_blocks_example_then_up_to_three_problems_minutes_from_medians() -> None:
    """Day 0, nothing done: a1, a2, a3 each get the worked example (a1's card; a tier-1
    problem shown solved for the others) and 3 tier-1 problems, highest chance first.
    Minutes: 3 x (2.0 example + 3 x 3.5 for a 2-step problem) = 37.5. No check: the 10th
    item falls in a3's block and nothing follows it."""
    p = plan(Log(), D0)
    assert [i.skill_id for i in p.items] == ["a1"] * 4 + ["a2"] * 4 + ["a3"] * 4
    assert all(i.role == "new" and i.block and i.priority == 0 for i in p.items)
    assert p.items[0].example_card == "ex.a1"
    assert p.items[4].example_card == "a2.t1.01"
    assert [i.problem.problem_id for i in p.items[5:8]] == [  # type: ignore[union-attr]
        "a2.t1.02",
        "a2.t1.03",
        "a2.t2.01",
    ]
    assert p.minutes == pytest.approx(37.5)


def test_a_block_continues_until_its_first_success() -> None:
    """After a1's example and a miss, a1's block continues next. After a success, a1 joins
    the mixed set: the other blocks first, then one growth problem (3 a day, 2 used). Here
    the 10th position falls in a3's block, so the day's check follows it; a1 is the only
    skill past its block, so the check is a1's and a1's growth problem, which can't sit next
    to it, is dropped (and reported)."""
    log = Log()
    served: list[ServedItem] = []
    first = plan(log, D0)
    serve(log, served, first.items[0], D0, None)
    serve(log, served, first.items[1], D0, False)
    nxt = plan(log, D0, served=served)
    assert (nxt.items[0].skill_id, nxt.items[0].role, nxt.items[0].block) == ("a1", "new", True)
    serve(log, served, nxt.items[0], D0, True)
    after = plan(log, D0, served=served)
    assert [i.skill_id for i in after.items[:8]] == ["a2"] * 4 + ["a3"] * 4
    assert [(i.skill_id, i.role) for i in after.items[8:]] == [("a1", "check")]
    assert [(i.skill_id, i.role) for i in after.dropped] == [("a1", "growth")]


def test_growth_up_to_three_a_day_interleaved() -> None:
    """Day 1, blocks done: a1, a2, a3 each get 3 growth problems at M1's tier (2), no two of
    a skill in a row: 9 items, all growth, all at tier 2 or 1."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    p = plan(log, day(1))
    assert Counter(i.skill_id for i in p.items) == {"a1": 3, "a2": 3, "a3": 3}
    assert set(roles(p)) == {"growth"}
    assert all(i.tier in (1, 2) for i in p.items)
    assert all(x.skill_id != y.skill_id for x, y in pairwise(p.items))


def test_growth_stops_after_two_consecutive_successes() -> None:
    """a1 succeeds twice in a row (a2 between them doesn't break a1's run): no more a1
    growth today. a2's miss keeps a2 going."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    served: list[ServedItem] = []
    p = plan(log, day(1))
    by_skill = {s: [i for i in p.items if i.skill_id == s] for s in ("a1", "a2")}
    serve(log, served, by_skill["a1"][0], day(1), True)
    serve(log, served, by_skill["a2"][0], day(1), False)
    serve(log, served, by_skill["a1"][1], day(1), True)
    left = plan(log, day(1), served=served)
    assert "a1" not in {i.skill_id for i in left.items}
    assert sum(i.skill_id == "a2" for i in left.items) == 2


def test_per_skill_cap_of_three_problems_a_day() -> None:
    """a1 had 3 block problems today (two misses, then a success): no growth today."""
    log = Log()
    served: list[ServedItem] = []
    p = plan(log, D0)
    for item, ok in zip(p.items[:4], (None, False, False, True), strict=True):
        serve(log, served, item, D0, ok)
    left = plan(log, D0, served=served)
    assert "a1" not in {i.skill_id for i in left.items}


def certified_a1(log: Log, d: int = 1) -> None:
    """a1: block success, then M1 (3 of 3 at tier 2), M2 and M3 (4 of 4 in time)."""
    log.add(SK["a1"].pool[0], D0, True, role="new")
    log.many(SK["a1"].pool[3], day(d), "111")
    log.many(SK["a1"].pool[9], day(d), "1111", minutes=3.0)
    log.many(SK["a1"].pool[15], day(d), "1111", minutes=4.0)


def maint(state: FakeState, today: date, settings: CourseSettings = SETTINGS) -> list[WorkItem]:
    log = Log()
    certified_a1(log)
    p = plan(log, today, state=state, settings=settings)
    return [i for i in p.items if i.role == "maintenance"]


def test_maintenance_when_tomorrows_forecast_falls_below_target() -> None:
    """a1 certified at tier 4 (e 0.97). Last practised a day ago with stability 1 day:
    tomorrow R = 0.9^2 = 0.81, readiness 0.97 x 0.81 = 0.79 < 0.9: one tier-4 problem,
    reason "forecast". Stability 100 days: R = 0.998, readiness 0.968: none."""
    today = day(5)
    last = at(today, 600) - DAY_MS
    weak = FakeState(default_e=0.97, stability={"a1": 1.0}, last_ms={"a1": last})
    got = maint(weak, today)
    assert [(i.skill_id, i.tier, i.reason) for i in got] == [("a1", 4, "forecast")]
    strong = FakeState(default_e=0.97, stability={"a1": 100.0}, last_ms={"a1": last})
    assert maint(strong, today) == []


def test_an_exam_within_21_days_adds_its_date_as_a_horizon() -> None:
    """Stability 8 days, last practised a day ago. Tomorrow: R = 0.9^(2/8) = 0.974,
    readiness 0.945 >= 0.9, not due. Exam in 10 days covering U1: R = 0.9^(11/8) = 0.865,
    readiness 0.839 < 0.9: due, reason "exam". The same exam 30 days out is beyond the
    horizon; an exam covering only U2 doesn't concern a1."""
    today = day(5)
    state = FakeState(
        default_e=0.97, stability={"a1": 8.0}, last_ms={"a1": at(today, 600) - DAY_MS}
    )
    assert maint(state, today) == []
    near = CourseSettings(
        "c", start=D0, exams=(ExamSpec(1, today + timedelta(days=10), ("K::U1",)),)
    )
    assert [i.reason for i in maint(state, today, settings=near)] == ["exam"]
    far = CourseSettings(
        "c", start=D0, exams=(ExamSpec(1, today + timedelta(days=30), ("K::U1",)),)
    )
    assert maint(state, today, settings=far) == []
    other = CourseSettings(
        "c", start=D0, exams=(ExamSpec(1, today + timedelta(days=10), ("K::U2",)),)
    )
    assert maint(state, today, settings=other) == []


def test_every_tenth_item_is_a_reference_check() -> None:
    """Day 15, every block done: six skills in growth at tier 2, 18 growth problems. The
    10th item is a check (an unseen tier-2 problem of an introduced skill, none of today's
    cards); 18 regular items fill positions 1-9 and 11-19, so the 20th check never comes."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3", "b1", "b2", "c1")
    p = plan(log, day(15))
    assert len(p.items) == 19
    assert [i for i, it in enumerate(p.items) if it.role == "check"] == [9]
    chk = p.items[9]
    assert chk.tier == 2
    others = {i.problem.card_id for i in p.items if i is not chk}  # type: ignore[union-attr]
    assert chk.problem is not None
    assert chk.problem.card_id not in others


def test_missed_milestone_work_is_held_to_40_percent_then_overflows() -> None:
    """Day 14: a1-a3 are behind M1 (due day 5) and b1, b2 behind theirs (due day 12); c1 is
    new today. The day's other work is c1's block (4 items): missed work k obeys
    k <= 0.4 (4 + k), so k = 2 (2 <= 2.4; 3 > 2.8), earliest deadline first; the other 13
    come after everything else (a reference check lands in them at the 10th position)."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3", "b1", "b2")
    p = plan(log, day(14))
    missed = [i for i in p.items if i.missed]
    assert len(missed) == 15
    assert {i.skill_id for i in missed} == {"a1", "a2", "a3", "b1", "b2"}
    assert p.overflow == 13
    assert main_share([], p.items) <= 0.4 + 1e-9
    assert [i.role for i in p.items[:4]] == ["new"] * 4
    last = max(k for k, i in enumerate(p.items) if not i.missed and i.role != "check")
    after = p.items[last + 1 :]
    assert all(i.missed or i.role == "check" for i in after)
    assert sum(i.missed for i in after) >= p.overflow
    assert any("40%" in n for n in p.notes)
    assert set(p.behind) == {"a1", "a2", "a3", "b1", "b2"}


def test_with_nothing_but_catch_up_the_whole_backlog_is_planned() -> None:
    """Day 40, every M1 missed and nothing new: catch-up is all there is, and it is planned
    in full (not starved by the share)."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3", "b1", "b2", "c1")
    p = plan(log, day(40))
    assert sum(i.missed for i in p.items) == 18
    assert p.overflow == 18


def test_minutes_follow_the_predicted_medians() -> None:
    """Speed 2: every growth problem's median is 2 x 3.5 = 7 minutes; 9 problems = 63."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    p = plan(log, day(1), state=FakeState(speed=2.0))
    assert p.minutes == pytest.approx(63.0)
    assert all(i.expected_minutes == pytest.approx(7.0) for i in p.items)


def test_items_that_cannot_be_interleaved_are_reported() -> None:
    """Day 2 with a1 alone in growth (a2, a3 certified out of the way? no: only a1 has its
    block done and a2, a3 still owe their blocks): a2, a3 blocks first, then a1's 3 growth
    problems can be separated only by... nothing after the blocks: 1 a1 item is placed (the
    first follows a3's block), 2 are dropped, with a note."""
    log = Log()
    blocks_done(log, "a1")
    p = plan(log, day(2))
    growth = [i for i in p.items if i.role == "growth"]
    assert len(growth) == 1
    assert len(p.dropped) == 2
    assert any("left out" in n for n in p.notes)


def test_after_an_execution_miss_one_more_problem_later() -> None:
    """a1 is in maintenance and served its one maintenance problem today: a miss whose top
    suspect (a1, blame 1.0) has memory share 0.2 < 0.5 -> one more problem later (reason
    "retry"), among a2's and a3's growth. Memory share 0.8: none."""
    today = day(5)
    state = FakeState(
        default_e=0.97, stability={"a1": 1.0}, last_ms={"a1": at(today, 600) - DAY_MS}
    )

    def after(m: float) -> list[WorkItem]:
        log = Log()
        certified_a1(log)
        blocks_done(log, "a2", "a3")
        first = next(i for i in plan(log, today, state=state).items if i.role == "maintenance")
        assert first.problem is not None
        log.add(first.problem, today, False, role="maintenance")
        pred = Prediction(p=0.8, p_raw=0.8, q=(), e=(), r=(), median_minutes=5.0, pace_ok=True)
        upd = UpdateRecord(pred, (("a1", 1.0),), (("a1", m),))
        served = [ServedItem(first, correct=False, update=upd)]
        return [i for i in plan(log, today, state=state, served=served).items if i.skill_id == "a1"]

    assert [i.reason for i in after(0.2)] == ["retry"]
    assert after(0.8) == []


def test_spread_blame_steers_the_next_growth_problem() -> None:
    """a2's tier-2 problems: some use a1 (the top suspect), some b1 (the runner-up). After a
    miss with blame a1 0.5, b1 0.4, a2 0.1, a2's next growth problem has a1 and not b1."""
    probs = [problem(f"a2.t2.{i}", "a2", 2, uses=["a1"]) for i in range(3)] + [
        problem(f"a2.t2.x{i}", "a2", 2, uses=["b1"]) for i in range(3)
    ]
    sk = skill("a2", A, 2, problems=[problem("a2.t1.01", "a2", 1), *probs])
    cr = course([(A, 2.0), (B, 2.0), (C, 2.0)], [SK["a1"], sk, SK["a3"]])
    model = fake(cr)
    log = Log()
    log.add(SK["a1"].pool[0], D0, True, role="new")
    log.add(sk.pool[0], D0, True, role="new")
    log.add(SK["a3"].pool[0], D0, True, role="new")
    log.add(probs[3], day(1), False)
    pred = Prediction(p=0.8, p_raw=0.8, q=(), e=(), r=(), median_minutes=3.5, pace_ok=True)
    upd = UpdateRecord(pred, (("a1", 0.5), ("b1", 0.4), ("a2", 0.1)), ())
    item = WorkItem("a2", "growth", probs[3], None, 3.5, 1, tier=2)
    served = [ServedItem(item, correct=False, update=upd)]
    state = FakeState(default_e=0.92)
    cert = Certifier.for_course(log.items, cr, SETTINGS, today=day(1))
    p = plan_day(model, state, cert, cr, SETTINGS, day(1), at(day(1), 600), served, rng=rng())
    first = next(i for i in p.items if i.skill_id == "a2")
    assert first.problem is not None
    assert first.reason == "suspect"
    assert "a1" in first.problem.components
    assert "b1" not in first.problem.components


def test_next_item_is_the_head_of_the_plan_and_the_default_seed_is_stable() -> None:
    log = Log()
    blocks_done(log, "a1", "a2", "a3", "b1", "b2", "c1")
    state = FakeState()
    cert = Certifier.for_course(log.items, COURSE, SETTINGS, today=day(15))
    args = (MODEL, state, cert, COURSE, SETTINGS, day(15), at(day(15), 600))
    one = plan_day(*args)
    assert one == plan_day(*args)
    assert next_item(*args) == one.items[0]
    assert next_item(*args, rng=rng(3)) == plan_day(*args, rng=rng(3)).items[0]


def test_hours_fall_back_to_the_standard_until_ten_certifications() -> None:
    """No certification yet: 2 h outside per class hour x 2 class h a week = 4 h (pace 1).
    The pack's own figure (7 h) at pace 1.5: 10.5 h."""
    p = plan(Log(), D0)
    assert (p.hours_to_keep_pace, p.standard_hours, p.hours_basis) == (4.0, 4.0, "standard")
    cr = course([(A, 2.0)], [SK["a1"]], outside=7.0)
    s = CourseSettings("c", start=D0, pace_factor=1.5)
    cert = Certifier.for_course([], cr, s, today=D0)
    got = plan_day(fake(cr), FakeState(), cert, cr, s, D0, at(D0), rng=rng())
    assert got.hours_to_keep_pace == pytest.approx(10.5)


def test_hours_from_history_per_certified_milestone() -> None:
    """a1-a3 certify M1 (day 1), M2 (day 2), M3 (day 3) and b1 M1 (day 8): 10 milestones. Each
    attempt took 2 minutes (as recorded): a1-a3's M1 windows hold the block success and 3
    tier-2 tries (8 min), M2 and M3 four tries each (8 min); b1's M1, 8 min. Day 16: the
    next 7 days (17-23) hold b1's and b2's M2 deadlines (day 21, tier 3; the schedule counts
    them whether or not they're certified) and c1's M1 (day 19, tier 2): 3 x 8 = 24 min. No
    maintenance is due (no forgetting): 24/60 h."""
    log = Log()
    for s in ("a1", "a2", "a3"):
        log.add(SK[s].pool[0], D0, True, role="new")
        log.many(SK[s].pool[3], day(1), "111")
        log.many(SK[s].pool[9], day(2), "1111", minutes=3.0)
        log.many(SK[s].pool[15], day(3), "1111", minutes=4.0)
    log.add(SK["b1"].pool[0], day(7), True, role="new")
    log.many(SK["b1"].pool[3], day(8), "111")
    spent = {o.attempt_id: 2.0 for o in log.items}
    p = plan(log, day(16), state=FakeState(default_e=0.97), spent=spent)
    assert p.hours_basis == "history"
    assert p.hours_to_keep_pace == pytest.approx(24 / 60)


def test_hours_borrow_the_nearest_tier_and_attempt_minutes_fall_back() -> None:
    assert _nearest({2: 10.0, 4: 30.0}, 3) == 30.0  # tie: the higher tier
    assert _nearest({2: 10.0}, 4) == 10.0
    log = Log()
    ok = log.add(SK["a1"].pool[3], D0, True, minutes=2.5)
    miss = log.add(SK["a1"].pool[3], D0, False)
    assert attempt_minutes(ok, {}) == 2.5
    assert attempt_minutes(miss, {}) == 3.5  # the standard time stands in
    assert attempt_minutes(miss, {miss.attempt_id: 9.0}) == 9.0


def test_feasibility_note_when_slips_cap_the_target() -> None:
    """Tier-4 problems with one component: (1 - 0.12) x 0.99 = 0.871 < 0.9: a note with the
    numbers. Slip 0.02: 0.970, fine."""
    f = feasibility(MODEL, FakeState(slip=0.12), COURSE, SETTINGS)
    assert f is not None
    assert f.components == 1.0
    assert f.best == pytest.approx(0.88 * 0.99)
    assert not f.ok
    assert any("best attainable" in n for n in plan(Log(), D0, state=FakeState(slip=0.12)).notes)
    g = feasibility(MODEL, FakeState(slip=0.02), COURSE, SETTINGS)
    assert g is not None
    assert g.ok
    assert not any("best attainable" in n for n in plan(Log(), D0).notes)


def test_retired_cards_are_never_planned() -> None:
    """With a1's tier-2 cards retired, a1's growth comes from the rung below (tier 1), and no
    retired card appears anywhere in the plan."""
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    retired = {p.card_id for p in SK["a1"].pool if p.tier == 2}
    cert = Certifier.for_course(log.items, COURSE, SETTINGS, today=day(1))
    p = plan_day(
        MODEL, FakeState(), cert, COURSE, SETTINGS, day(1), at(day(1)), rng=rng(), retired=retired
    )
    cards = {i.problem.card_id for i in p.items if i.problem is not None}
    assert not cards & retired
    a1 = [i for i in p.items if i.skill_id == "a1"]
    assert a1
    assert all(i.tier == 1 for i in a1)


def test_the_next_study_day_sets_the_maintenance_horizon() -> None:
    """a1 certified (e 0.97), stability 20 days, practised a day ago. Next study day
    tomorrow: R = 0.9^(2/20) = 0.990, readiness 0.960, not due. Next study day in 19 days:
    R = 0.9^(20/20) = 0.9, readiness 0.873 < 0.9: due today."""
    today = day(5)
    state = FakeState(
        default_e=0.97, stability={"a1": 20.0}, last_ms={"a1": at(today, 600) - DAY_MS}
    )
    log = Log()
    certified_a1(log)
    priors = model_priors(MODEL, state, COURSE, at(today, 600))
    cert = Certifier.for_course(log.items, COURSE, SETTINGS, today=today, priors=priors)
    args = (MODEL, state, cert, COURSE, SETTINGS, today, at(today, 600))

    def maintained(nxt: date | None) -> list[str]:
        p = plan_day(*args, rng=rng(), next_study_day=nxt)
        return [i.reason for i in p.items if i.role == "maintenance"]

    assert maintained(None) == []
    assert maintained(today + timedelta(days=19)) == ["forecast"]


def test_hours_add_the_maintenance_the_week_makes_due() -> None:
    """The history of the previous test (24 minutes of milestones next week), with a1
    forgetting fast (stability 1 day, practised just now): its tier-4 readiness falls to
    0.97 x 0.9 = 0.873 < 0.9 within the week, adding one tier-4 problem (median 5.0 min):
    29/60 h."""
    log = Log()
    for s in ("a1", "a2", "a3"):
        log.add(SK[s].pool[0], D0, True, role="new")
        log.many(SK[s].pool[3], day(1), "111")
        log.many(SK[s].pool[9], day(2), "1111", minutes=3.0)
        log.many(SK[s].pool[15], day(3), "1111", minutes=4.0)
    log.add(SK["b1"].pool[0], day(7), True, role="new")
    log.many(SK["b1"].pool[3], day(8), "111")
    spent = {o.attempt_id: 2.0 for o in log.items}
    state = FakeState(default_e=0.97, stability={"a1": 1.0}, last_ms={"a1": at(day(16), 600)})
    p = plan(log, day(16), state=state, spent=spent)
    assert p.hours_basis == "history"
    assert p.hours_to_keep_pace == pytest.approx(29 / 60)
