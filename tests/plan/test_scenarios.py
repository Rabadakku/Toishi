"""Scenarios, one per status, on the fake predictor: slip-limited, struggling, behind, a
mid-course start, and an exam pulling M2."""

from datetime import date, timedelta

import pytest

from core.plan.certify import Certifier, model_priors
from core.plan.daily import main_share, plan_day
from core.plan.types import (
    Course,
    CourseSettings,
    DayPlan,
    ExamSpec,
    Milestone,
    ServedItem,
    SkillStatus,
)
from tests.plan.fakes import DAY_MS, FakeState
from tests.plan.helpers import Log, at, course, fake, pool, rng, skill

A, B, C = "K::U1::A", "K::U1::B", "K::U2::C"
D0 = date(2026, 9, 1)  # A on day 0, B on day 7, C on day 14 (2 h sections, 2 h a week)


def day(n: int) -> date:
    return D0 + timedelta(days=n)


def make_course() -> Course:
    big = {1: 3, 2: 6, 3: 6, 4: 6}
    return course(
        [(A, 2.0), (B, 2.0), (C, 2.0)],
        [
            skill("a1", A, 1, example="ex.a1", problems=pool("a1", big)),
            skill("a2", A, 2, requires=["a1"], problems=pool("a2", big)),
            skill("a3", A, 3, problems=pool("a3", big)),
            skill("b1", B, 4, requires=["a1"], problems=pool("b1", big)),
            skill("b2", B, 5, problems=pool("b2", big)),
            skill("c1", C, 6, problems=pool("c1", big)),
        ],
    )


COURSE = make_course()
SK = {s.skill_id: s for s in COURSE.skills}
INTRO = {"a1": 0, "a2": 0, "a3": 0, "b1": 7, "b2": 7, "c1": 14}
MODEL = fake(COURSE)


def plan(
    log: Log,
    today: date,
    state: FakeState,
    settings: CourseSettings,
    served: list[ServedItem] | None = None,
    minute: int = 600,
) -> DayPlan:
    now = at(today, minute)
    priors = model_priors(MODEL, state, COURSE, now)
    cert = Certifier.for_course(log.items, COURSE, settings, today=today, priors=priors)
    return plan_day(
        MODEL, state, cert, COURSE, settings, today, now, served or [], rng=rng(today.toordinal())
    )


def status_of(p: DayPlan, sid: str) -> SkillStatus:
    return next(s for s in p.statuses if s.skill_id == sid)


def blocks_done(log: Log, *skills: str) -> None:
    for s in skills:
        log.add(SK[s].pool[0], day(INTRO[s]), True, role="new")


def certify_all(log: Log, sid: str, d: int) -> None:
    """M1 (3 of 3 at tier 2), M2 and M3 (4 of 4 in time at tiers 3 and 4) on day d."""
    log.many(SK[sid].pool[3], day(d), "111")
    log.many(SK[sid].pool[9], day(d), "1111", minutes=3.0)
    log.many(SK[sid].pool[15], day(d), "1111", minutes=4.0)


def test_slip_limited_skill_gets_no_growth_and_a_check_your_work_note() -> None:
    """a1's components are excellent (e 0.99) but the student slips 12% of the time: the
    model's chance is 0.88 x 0.99 = 0.871 and the best attainable at tier 4 is 0.871, below
    0.9 (the feasibility note). A week of tier-2 practice at about 85% (14 of 17) keeps the
    posterior near 0.83: below 0.9 but above (1 - 0.12) x 0.9 = 0.792, so slips explain it.
    On day 8 a1 is slip-limited: no growth, one problem at its milestone tier (the
    forecast stays below target), "check your work". At slip 0.02 the same history means
    plain growth."""
    s = CourseSettings("c", start=D0)
    state = FakeState(default_e=0.99, slip=0.12)
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    for d, outcomes in enumerate(("011", "11", "11", "011", "11", "11", "011"), start=1):
        log.many(SK["a1"].pool[3 + d % 6], day(d), outcomes)
    p = plan(log, day(8), state, s)
    st = status_of(p, "a1")
    assert st.state == "slip-limited"
    assert st.posterior_mean is not None
    assert 0.792 <= st.posterior_mean < 0.9
    mine = [i for i in p.items if i.skill_id == "a1"]
    assert [(i.role, i.tier) for i in mine if i.role != "check"] == [("maintenance", 2)]
    assert any("a1: limited by careless errors" in n for n in p.notes)
    assert any("best attainable" in n for n in p.notes)
    # Served and answered: nothing more for a1 today.
    item = next(i for i in mine if i.role == "maintenance")
    assert item.problem is not None
    log.add(item.problem, day(8), True, minutes=2.0, role="maintenance")
    left = plan(log, day(8), state, s, [ServedItem(item, correct=True)], minute=601)
    assert not [i for i in left.items if i.skill_id == "a1" and i.role != "check"]
    careful = plan(log, day(8), FakeState(default_e=0.99, slip=0.02), s)
    assert status_of(careful, "a1").state in ("growth", "maintenance")


def test_struggling_skill_adds_growth_for_its_weakest_components_prerequisites() -> None:
    """a1 is certified (e 0.97, nothing due). a2 (requires a1) spends days 2-4 at the full
    growth allowance, missing every problem: its posterior falls, so it is struggling. Its
    weakest component at tier 2 is a2 itself, whose prerequisite a1 gets growth today
    (reason "prerequisite"), next to a2's own growth; the note points to the textbook."""
    s = CourseSettings("c", start=D0)
    state = FakeState(e={"a1": 0.97, "a2": 0.85})
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    certify_all(log, "a1", 1)
    for d in (2, 3, 4):
        log.many(SK["a2"].pool[3 + d], day(d), "000")
    p = plan(log, day(5), state, s)
    st = status_of(p, "a2")
    assert (st.state, st.prerequisites) == ("struggling", ("a1",))
    assert status_of(p, "a1").state == "maintenance"
    a1_items = [i for i in p.items if i.skill_id == "a1" and i.role != "check"]
    assert a1_items
    assert all(i.reason == "prerequisite" and i.role == "growth" for i in a1_items)
    assert any(i.skill_id == "a2" and i.role == "growth" for i in p.items)
    assert any("a2: struggling" in n and "a1" in n for n in p.notes)


def test_behind_student_gets_new_material_first_and_catch_up_within_the_share() -> None:
    """The student did a1-a3's blocks on day 0 and nothing since. Day 15: a1-a3 missed M1
    (day 7), b1 and b2 missed theirs (day 14) and still owe their blocks, c1 is new. The
    day opens with the three blocks; catch-up is held to 40% of the day up to its last item
    of other work, at every step of the session, and the rest is planned after it."""
    s = CourseSettings("c", start=D0)
    state = FakeState()
    log = Log()
    blocks_done(log, "a1", "a2", "a3")
    p = plan(log, day(15), state, s)
    assert set(p.behind) == {"a1", "a2", "a3", "b1", "b2"}
    firsts = [i.skill_id for i in p.items[:12]]
    assert firsts == ["b1"] * 4 + ["b2"] * 4 + ["c1"] * 4
    assert all(i.role == "new" for i in p.items[:12])
    assert sum(i.missed for i in p.items) == 9
    served: list[ServedItem] = []
    for k in range(25):
        p = plan(log, day(15), state, s, served, minute=600 + k)
        if not p.items:
            break
        done = [x.item for x in served]
        assert main_share(done, p.items) <= 0.4 + 1e-9
        first_missed = next((j for j, i in enumerate([*done, *p.items]) if i.missed), None)
        if first_missed is not None:
            assert all(i.role != "new" for i in [*done, *p.items][first_missed:])
        item = p.items[0]
        if item.problem is not None:
            log.add(item.problem, day(15), True, minutes=2.0, role=item.role)
        served.append(ServedItem(item, correct=True if item.problem else None))
    assert any(x.item.missed for x in served)


def test_mid_course_start_keeps_earlier_skills_until_a_check_says_otherwise() -> None:
    """ "My class is at C today" on day 20: a1-b2 are assumed learned (Keep, tier 3, 0.80)
    and get no maintenance until they have evidence of their own; c1's block comes first.
    A failed reference check on a1 (tier 3): its Keep prior 0.8 becomes 3.2/5 = 0.64 < 0.70,
    so a1 returns to growth toward Keep at tier 3 (or 2). Four passed checks on a2 give it
    evidence of its own (n_eff 4), and its forecast is then honoured: with forgetting it
    gets a maintenance problem."""
    s = CourseSettings("c", aligned=(C, day(20)))
    state = FakeState(default_e=0.6)
    p = plan(Log(), day(20), state, s)
    for sid in ("a1", "a2", "a3", "b1", "b2"):
        st = status_of(p, sid)
        assert (st.state, st.assumed, st.milestones) == (
            "keep",
            True,
            (Milestone("keep", 3, None),),
        )
    assert not [i for i in p.items if i.role == "maintenance"]
    assert [i.skill_id for i in p.items[:4]] == ["c1"] * 4
    log = Log()
    log.add(SK["a1"].pool[9], day(20), False, role="check")
    p = plan(log, day(20), state, s)
    st = status_of(p, "a1")
    assert (st.state, st.current) == ("growth", Milestone("keep", 3, None))
    a1 = [i for i in p.items if i.skill_id == "a1" and i.role == "growth"]
    assert a1
    assert all(i.tier in (2, 3) for i in a1)
    log.many(SK["a2"].pool[9], day(20), "1111", role="check")
    forgetful = FakeState(
        default_e=0.95, stability={"a2": 1.0}, last_ms={"a2": at(day(20), 600) - DAY_MS}
    )
    p = plan(log, day(20), forgetful, s)
    assert status_of(p, "a2").state == "keep"
    assert [i.reason for i in p.items if i.skill_id == "a2" and i.role == "maintenance"] == [
        "forecast"
    ]


def test_exam_pulls_m2_and_adds_its_day_as_a_maintenance_horizon() -> None:
    """Exam on day 20 covering unit U1 (sections A and B). b1 (intro day 7): M2 is pulled
    from day 21 to day 18; a1 (intro day 0) keeps M2 on day 14 (already earlier); c1 (U2)
    is untouched (M2 on day 28). On day 17, a1 is certified with a 4-day stability, last
    practised on day 16: tomorrow R = 0.9^(2/4) = 0.949 (readiness 0.920, fine), but on the
    exam day R = 0.9^(4/4) = 0.9 (readiness 0.873 < 0.9): a maintenance problem, reason
    "exam". On day 24, b1 has M1 but not M2: behind, its growth counts as missed."""
    exam = ExamSpec(1, day(20), ("K::U1",))
    s = CourseSettings("c", start=D0, exams=(exam,))
    log = Log()
    blocks_done(log, "a1", "a2", "a3", "b1", "b2", "c1")
    certify_all(log, "a1", 1)
    state = FakeState(
        default_e=0.97, stability={"a1": 4.0}, last_ms={"a1": at(day(17), 600) - DAY_MS}
    )
    p = plan(log, day(17), state, s)
    ms = {st.skill_id: st.milestones for st in p.statuses}
    assert [m.deadline for m in ms["b1"]] == [day(12), day(18), day(35)]
    assert [m.deadline for m in ms["a1"]] == [day(5), day(14), day(28)]
    assert [m.deadline for m in ms["c1"]] == [day(19), day(28), day(42)]
    a1 = [i for i in p.items if i.skill_id == "a1" and i.role == "maintenance"]
    assert [i.reason for i in a1] == ["exam"]
    assert a1[0].p == pytest.approx(0.97 * 0.9 ** (1 / 4))
    log.many(SK["b1"].pool[3], day(15), "111")  # M1 at tier 2
    p = plan(log, day(24), FakeState(default_e=0.97), s)
    st = status_of(p, "b1")
    assert (st.current, st.track) == (Milestone("M2", 3, day(18)), "behind")
    b1 = [i for i in p.items if i.skill_id == "b1" and i.role == "growth"]
    assert b1
    assert all(i.missed and i.priority == 2 for i in b1)
