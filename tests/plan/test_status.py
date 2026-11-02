"""Skill statuses (design 4.2): states, tracks, bottleneck, readiness and pace."""

from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from core.plan.certify import Certifier, model_priors
from core.plan.status import PlanContext, status, statuses, track
from core.plan.types import CourseSettings, Milestone, ServedItem, WorkItem
from tests.plan.fakes import FakeState
from tests.plan.helpers import Log, at, course, fake, pool, skill

A, B = "K::U::A", "K::U::B"
D0 = date(2026, 9, 1)  # section A; B starts on day 7 (2 h at 2 h a week)


def day(n: int) -> date:
    return D0 + timedelta(days=n)


COURSE = course(
    [(A, 2.0), (B, 2.0)],
    [
        skill("a1", A, 1, example="ex.a1"),
        skill("a2", A, 2, requires=["a1"], problems=pool("a2", uses={3: ["a1", "alg.x"]})),
        skill("b1", B, 3, requires=["a2"]),
    ],
)
MODEL = fake(COURSE, extra_background=["alg.x"])
SETTINGS = CourseSettings("c", start=D0)


def context(
    log: Log,
    today: date,
    state: FakeState | None = None,
    settings: CourseSettings = SETTINGS,
    served: Sequence[ServedItem] = (),
) -> PlanContext[FakeState]:
    state = state or FakeState()
    priors = model_priors(MODEL, state, COURSE, at(today))
    cert = Certifier.for_course(log.items, COURSE, settings, today=today, priors=priors)
    return PlanContext(MODEL, state, cert, COURSE, settings, today, at(today), served)


def test_not_introduced_until_the_section_date() -> None:
    v = context(Log(), day(3)).view("b1")
    assert (v.state, v.intro, v.current, v.track) == ("not-introduced", day(7), None, "on-track")


def test_new_until_the_block_is_done() -> None:
    """Day 0: a1 is new, its milestone M1 (tier 2) due day 7; the example is its card. a2
    has no example card: a tier-1 problem shown solved stands in."""
    ctx = context(Log(), D0)
    v = ctx.view("a1")
    assert (v.state, v.current, v.track) == ("new", Milestone("M1", 2, day(7)), "on-track")
    assert (v.block.example_card, v.block.problems, v.block.done) == ("ex.a1", 0, False)
    assert ctx.view("a2").block.example_card == "a2.t1.01"


def test_block_ends_at_the_first_success_or_after_three_problems() -> None:
    a1 = COURSE.skills[0].pool
    log = Log()
    log.add(a1[0], D0, False, role="new")
    assert context(log, D0).view("a1").state == "new"
    log.add(a1[1], D0, True, role="new")
    assert context(log, D0).view("a1").state == "growth"
    log = Log()
    log.many(a1[0], D0, "000", role="new")
    v = context(log, D0).view("a1")
    assert (v.block.problems, v.block.done, v.state) == (3, True, "growth")


def test_block_in_progress_after_its_example_and_a_miss() -> None:
    a1 = COURSE.skills[0].pool
    log = Log()
    log.add(a1[0], D0, False, role="new")
    served = [
        ServedItem(WorkItem("a1", "new", None, "ex.a1", 2.0, 0, block=True)),
        ServedItem(WorkItem("a1", "new", a1[0], None, 3.5, 0, block=True), correct=False),
    ]
    b = context(log, D0, served=served).view("a1").block
    assert (b.example_today, b.in_progress, b.done) == (True, True, False)


def test_growth_tracks_against_the_current_milestone() -> None:
    """After a block success on day 0, a1 grows toward M1 (tier 2, due day 7): on track on
    day 3, behind on day 8. With M1 certified on day 2 (3 of 3 at tier 2, prior 0.9), the
    current milestone is M2 while the schedule is still on M1: ahead."""
    a1 = COURSE.skills[0].pool
    log = Log()
    log.add(a1[0], D0, True, role="new")
    assert context(log, day(3)).view("a1").track == "on-track"
    assert context(log, day(8)).view("a1").track == "behind"
    log.many(a1[3], day(2), "111")
    v = context(log, day(3)).view("a1")
    assert v.current is not None
    assert (v.state, v.current.name, v.track) == ("growth", "M2", "ahead")


def certify_all(log: Log, sid: str, d: date) -> None:
    """3 of 3 at tier 2, then 4 of 4 in time at tiers 3 and 4 (T* 3.5 and 5.0 min)."""
    sk = next(s for s in COURSE.skills if s.skill_id == sid)
    t2, t3, t4 = sk.pool[3], sk.pool[6], sk.pool[9]
    log.many(t2, d, "111", role="new")
    log.many(t3, d, "1111", minutes=3.0)
    log.many(t4, d, "1111", minutes=4.0)


def test_maintenance_when_every_milestone_is_certified() -> None:
    """Prior 0.97 (e 0.97, one component): every milestone certifies on day 2; on day 3 the
    schedule is still on M1, so a1 is ahead; level 4 (tier 1 untested)."""
    log = Log()
    certify_all(log, "a1", day(2))
    v = context(log, day(3), FakeState(default_e=0.97)).view("a1")
    assert (v.state, v.current, v.track, v.level, v.tier) == ("maintenance", None, "ahead", 4, 4)


def test_keep_after_the_course_end_date() -> None:
    """End day 10. On day 11 a1 drops to Keep (tier 3, 0.80, accuracy only): with its tier-3
    evidence it is Keep-certified; b1, never practised, grows toward Keep."""
    s = CourseSettings("c", start=D0, end=day(10))
    log = Log()
    certify_all(log, "a1", day(2))
    b1 = COURSE.skills[2].pool
    log.add(b1[0], day(7), True, role="new")
    ctx = context(log, day(11), FakeState(default_e=0.97), settings=s)
    v = ctx.view("a1")
    assert (v.state, v.current, v.tier, v.target, v.timed) == ("keep", None, 3, 0.8, False)
    w = ctx.view("b1")
    assert (w.state, w.current, w.track) == ("growth", Milestone("keep", 3, None), "on-track")


def test_mid_course_start_assumes_earlier_skills_learned() -> None:
    s = CourseSettings("c", aligned=(B, day(7)))
    ctx = context(Log(), day(7), settings=s)
    v = ctx.view("a1")
    assert (v.state, v.assumed, v.current, v.tier) == ("keep", True, None, 3)
    assert ctx.view("b1").state == "new"


def test_slip_limited_when_slips_explain_the_shortfall() -> None:
    """a1 at tier 2: e = 0.99 >= 0.97, slip 0.12, so P_raw = 0.88 x 0.99 = 0.871 < 0.9 while
    the slip-free 0.99 >= 0.9. Evidence: 9 of 10 at tier 2 on a prior of 0.871:
    (3.485 + 9)/14 = 0.892 < 0.9, n_eff 10, and 0.892 / 0.88 = 1.01 >= 0.9: slip-limited.
    With slip 0.02 (P_raw 0.970) slips don't explain it; with e 0.95 execution is too low:
    growth either way."""
    a1 = COURSE.skills[0].pool
    log = Log()
    log.add(a1[0], D0, True, role="new")
    log.many(a1[3], day(1), "1111111110")
    v = context(log, day(1), FakeState(e={"a1": 0.99}, slip=0.12)).view("a1")
    assert v.posterior is not None
    assert v.posterior.mean == pytest.approx((4 * 0.88 * 0.99 + 9) / 14)
    assert v.state == "slip-limited"
    assert context(log, day(1), FakeState(e={"a1": 0.99}, slip=0.02)).view("a1").state == "growth"
    assert context(log, day(1), FakeState(e={"a1": 0.95}, slip=0.12)).view("a1").state == "growth"


def test_struggling_after_three_full_growth_days_without_a_rise() -> None:
    """a2 (block done with a tier-1 success on day 0) has 3 growth misses at tier 2 on each
    of days 1-3: the posterior falls from its prior 0.9 to below it: struggling. Its weakest
    component at tier 2 is a2 itself, whose prerequisite a1 (introduced) gets growth."""
    a2 = COURSE.skills[1].pool
    log = Log()
    log.add(a2[0], D0, True, role="new")
    for d in (1, 2, 3):
        log.many(a2[3 + d % 3], day(d), "000")
    v = context(log, day(3)).view("a2")
    assert (v.state, v.bottleneck, v.prerequisites) == ("struggling", "a2", ("a1",))
    assert v.status().prerequisites == ("a1",)


def test_not_struggling_with_a_short_day_or_a_rising_posterior() -> None:
    """Day 2 had only 2 growth problems: not three full days. And at a prior of 0.3 with 2 of
    3 each day the posterior rises (to about 0.55): not struggling either."""
    a2 = COURSE.skills[1].pool
    log = Log()
    log.add(a2[0], D0, True, role="new")
    log.many(a2[3], day(1), "000")
    log.many(a2[4], day(2), "00")
    log.many(a2[5], day(3), "000")
    assert context(log, day(3)).view("a2").state == "growth"
    log = Log()
    log.add(a2[0], D0, True, role="new")
    for d in (1, 2, 3):
        log.many(a2[3 + d % 3], day(d), "110")
    assert context(log, day(3), FakeState(e={"a2": 0.3})).view("a2").state == "growth"


def test_bottleneck_is_the_lowest_q_course_component() -> None:
    """a2's tier-3 problems use a2 (0.9), a1 (0.8) and background alg.x (0.5): the
    bottleneck is a1; alg.x is never one."""
    state = FakeState(e={"a2": 0.9, "a1": 0.8, "alg.x": 0.5})
    ctx = context(Log(), D0, state)
    assert ctx.bottleneck(COURSE.skills[1], 3) == "a1"
    assert ctx.bottleneck(COURSE.skills[1], 2) == "a2"


def test_readiness_and_pace_over_the_representative_problems() -> None:
    """a1 at tier 2 (one component, e 0.8): readiness 0.8. Median = T* x speed: at pace with
    speed 1.0, not with 1.2."""
    log = Log()
    log.add(COURSE.skills[0].pool[0], D0, True, role="new")
    v = context(log, D0, FakeState(e={"a1": 0.8})).view("a1")
    assert v.readiness == pytest.approx(0.8)
    assert v.pace_ok is True
    assert context(log, D0, FakeState(e={"a1": 0.8}, speed=1.2)).view("a1").pace_ok is False


def test_track_rules() -> None:
    m1, m2, m3 = (
        Milestone("M1", 2, day(7)),
        Milestone("M2", 3, day(21)),
        Milestone("M3", 4, day(35)),
    )
    ms = (m1, m2, m3)
    assert track(ms, m1, day(7)) == "on-track"
    assert track(ms, m1, day(8)) == "behind"
    assert track(ms, m2, day(5)) == "ahead"
    assert track(ms, m3, day(10)) == "ahead"  # the schedule is on M2 (due day 21)
    assert track(ms, m3, day(30)) == "on-track"  # the schedule is on M3 too
    assert track(ms, None, day(30)) == "ahead"
    assert track(ms, None, day(40)) == "on-track"
    assert track(ms, m3, day(40)) == "behind"


def test_public_status_functions_match_the_views() -> None:
    log = Log()
    log.add(COURSE.skills[0].pool[0], D0, True, role="new")
    state = FakeState()
    cert = Certifier.for_course(log.items, COURSE, SETTINGS, today=D0)
    one = status(MODEL, state, cert, COURSE, SETTINGS, "a1", D0, at(D0))
    every = statuses(MODEL, state, cert, COURSE, SETTINGS, D0, at(D0))
    assert [s.skill_id for s in every] == ["a1", "a2", "b1"]
    assert every[0] == one
    assert (one.state, one.posterior_mean is not None) == ("growth", True)


def test_examples_seen_end_the_new_phase_without_block_problems() -> None:
    """x1 has an example card but no tier 1-2 problems, so its block is the example alone:
    new until the example is seen, today or on an earlier day (`examples_seen`). x2 has
    neither an example card nor block problems: it skips the new phase."""
    x1 = skill("x1", A, 1, example="ex.x1", problems=pool("x1", {3: 2, 4: 2}))
    x2 = skill("x2", A, 2, problems=pool("x2", {3: 2}))
    cr = course([(A, 2.0), (B, 2.0)], [x1, x2])
    model = fake(cr)
    cert = Certifier.for_course([], cr, SETTINGS, today=day(1))
    args = (model, FakeState(), cert, cr, SETTINGS, day(1), at(day(1)))
    assert PlanContext(*args).view("x1").state == "new"
    assert PlanContext(*args, examples_seen={"x1"}).view("x1").state == "growth"
    shown = [ServedItem(WorkItem("x1", "new", None, "ex.x1", 2.0, 0, block=True))]
    assert PlanContext(*args, shown).view("x1").state == "growth"
    assert PlanContext(*args).view("x2").state == "growth"
