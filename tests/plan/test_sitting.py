"""Certification sittings for M2 and M3 (docs/design/wave2-planner.md section 2, design v1.3):
the pace and pass chances, when a skill sits, what it gets, where the block goes, how it is
resumed and how its outcome certifies."""

from datetime import date, timedelta

import pytest

from core.learner.types import Prediction, ProblemSpec, UpdateRecord
from core.plan.certify import Certifier, SittingResult, model_priors
from core.plan.config import SIGMA_T_DEFAULT, SITTING_PASS_MIN, SITTING_WARMUP_MINUTES
from core.plan.daily import plan_day
from core.plan.sitting import (
    pace_chance,
    pass_chance,
    practice_ready,
    sigma_of,
    sitting_id,
    waiting,
)
from core.plan.types import CourseSettings, DayPlan, ServedItem, SkillInfo, WorkItem
from tests.plan.fakes import FakeState
from tests.plan.helpers import Log, at, course, fake, pool, problem, rng, skill

A, B, C, D = "K::U::A", "K::U::B", "K::U::C", "K::U::D"
D0 = date(2026, 9, 1)  # sections A, B, C, D start on days 0, 2, 4 and 6


def day(n: int) -> date:
    return D0 + timedelta(days=n)


def tier3(sid: str, families: int = 5, per: int = 2) -> tuple[ProblemSpec, ...]:
    """`per` tier-3 problems in each of `families` template families (T* 3.5 minutes)."""
    return tuple(
        problem(f"{sid}.t3.f{f}.{k}", sid, 3, family=f"{sid}.f{f}")
        for f in range(families)
        for k in range(per)
    )


def make_skill(sid: str, deck: str, order: int) -> SkillInfo:
    return skill(sid, deck, order, problems=(*pool(sid, {1: 2, 2: 4}), *tier3(sid)))


COURSE = course(
    [(A, 1.0), (B, 1.0), (C, 1.0), (D, 1.0)],
    [
        make_skill("a", A, 1),
        make_skill("b", B, 2),
        make_skill("c", C, 3),
        make_skill("d", D, 4),
        make_skill("g", A, 5),
    ],
    weekly=3.5,
)
SK = {s.skill_id: s for s in COURSE.skills}
INTRO = {"a": 0, "b": 2, "c": 4, "d": 6, "g": 0}
MODEL = fake(COURSE)
SETTINGS = CourseSettings("c", start=D0)
FAST = FakeState(default_e=0.97, speed=0.6)


def ready(log: Log, sid: str, d: int, practice: str = "01") -> None:
    """The skill's block on its introduction day, M1 on day d (3 of 3 at tier 2), then
    tier-3 practice on day d (default: a miss, then a success)."""
    sp = SK[sid].pool
    log.add(sp[0], day(INTRO[sid]), True, role="new")
    log.many(sp[2], day(d), "111")
    for k, ch in enumerate(practice):
        log.add(sp[6 + k], day(d), ch == "1", minutes=1.0)


def plan(
    log: Log,
    today: date,
    state: FakeState = FAST,
    served: list[ServedItem] | None = None,
    minute: int = 600,
) -> DayPlan:
    now = at(today, minute)
    priors = model_priors(MODEL, state, COURSE, now)
    cert = Certifier.for_course(log.items, COURSE, SETTINGS, today=today, priors=priors)
    return plan_day(
        MODEL, state, cert, COURSE, SETTINGS, today, now, served or [], rng=rng(len(served or []))
    )


def sitting_items(p: DayPlan) -> list[WorkItem]:
    return [i for i in p.items if i.role == "sitting"]


# ---------------------------------------------------------------------- the chances


def test_pace_chance_is_the_fenton_wilkinson_lognormal_sum() -> None:
    """Three problems with medians at 0.8 T* and sigma 0.45: P(sum <= sum T*) = 0.722 (a
    400,000-draw Monte Carlo gives 0.724); at medians of T*, 0.404 (0.405). The formula:
    m = med e^(s^2/2), v = med^2 e^(s^2)(e^(s^2) - 1), s2 = ln(1 + V/M^2),
    mu = ln M - s2/2, P = Phi((ln L - mu)/sqrt(s2))."""
    assert pace_chance([0.8] * 3, [1.0] * 3, 0.45) == pytest.approx(0.72177, abs=1e-4)
    assert pace_chance([1.0] * 3, [1.0] * 3, 0.45) == pytest.approx(0.40415, abs=1e-4)
    # The block limit is a sum: one slow problem is made up by fast ones.
    assert pace_chance([1.4, 0.5], [1.0, 1.0], 0.2) > 0.6
    # Scale-free, and certain at sigma 0.
    assert pace_chance([2.4] * 3, [3.0] * 3, 0.45) == pytest.approx(0.72177, abs=1e-4)
    assert pace_chance([0.9, 0.9], [1.0, 1.0], 0.0) == 1.0
    assert pace_chance([1.1, 1.0], [1.0, 1.0], 0.0) == 0.0
    assert pace_chance([], [], 0.45) == 1.0


def test_pass_chance_multiplies_the_calibrated_chances_by_the_pace_chance() -> None:
    probs = [problem(f"x{i}", "x", 3, minutes=4.0) for i in range(3)]
    preds = [
        Prediction(p=p, p_raw=p, q=(), e=(), r=(), median_minutes=3.2, pace_ok=True)
        for p in (0.95, 0.9, 0.97)
    ]
    got = pass_chance(preds, probs, 0.45)
    assert got.accuracy == pytest.approx(0.95 * 0.9 * 0.97)
    assert got.pace == pytest.approx(pace_chance([3.2] * 3, [4.0] * 3, 0.45))
    assert got.chance == pytest.approx(got.accuracy * got.pace)
    assert SITTING_PASS_MIN == 0.5


def test_sigma_comes_from_the_model_when_it_has_one() -> None:
    assert sigma_of(MODEL, FakeState(sigma=0.3)) == 0.3

    class Bare:
        pass

    assert sigma_of(Bare(), None) == SIGMA_T_DEFAULT  # type: ignore[arg-type]


# ---------------------------------------------------------------------- when


def test_a_due_skill_sits_after_the_warm_up_with_unseen_problems_from_different_families() -> None:
    """Day 3: a has M1 and two tier-3 practice tries (the last right), readiness 0.97: a
    sitting of 3 never-served tier-3 problems from 3 families (4 families still have unseen
    problems), role sitting, one block, after at least 20 minutes of the day's other work.
    Each item carries the day's sitting id, the block, its skill's time limit (the sum of
    their T*: 3 x 3.5) and the M2 milestone; the plan logs the sitting and the pass
    chance."""
    log = Log()
    ready(log, "a", 1)
    log.add(SK["g"].pool[0], D0, True, role="new")
    p = plan(log, day(3))
    items = sitting_items(p)
    assert [i.skill_id for i in items] == ["a"] * 3
    assert len({i.problem.family for i in items if i.problem}) == 3
    history_cards = {o.problem.card_id for o in log.items}
    assert not {i.problem.card_id for i in items if i.problem} & history_cards
    assert all(i.problem is not None and i.problem.tier == 3 for i in items)
    sid = sitting_id("c", day(3))
    assert {(i.sitting, i.milestone, i.time_limit) for i in items} == {(sid, "M2", 10.5)}
    assert items[0].sitting_block == tuple(i.problem.problem_id for i in items if i.problem)
    assert p.sittings == ((sid, ("a",)),)
    assert [s for s, _ in p.sitting_chances] == ["a"]
    k = p.items.index(items[0])
    assert p.items[k : k + 3] == tuple(items)
    before = sum(i.expected_minutes for i in p.items[:k])
    others = sum(i.expected_minutes for i in p.items if i.role != "sitting")
    assert before >= min(SITTING_WARMUP_MINUTES, others) - 1e-9


@pytest.mark.parametrize(
    ("case", "sits"),
    [
        ("due", True),
        ("m1-current", False),
        ("one-practice-try", False),
        ("last-try-a-miss", False),
        ("low-readiness", False),
    ],
)
def test_each_condition_of_a_sitting(case: str, sits: bool) -> None:
    """M2 or M3 current, 2 or more practice first tries at the tier with the last a success,
    and readiness at the target: each one missing means no sitting."""
    log = Log()
    state = FAST
    if case == "m1-current":
        sp = SK["a"].pool
        log.add(sp[0], D0, True, role="new")
        log.many(sp[6], day(1), "11", minutes=1.0)
    elif case == "one-practice-try":
        ready(log, "a", 1, practice="1")
    elif case == "last-try-a-miss":
        ready(log, "a", 1, practice="10")
    else:
        ready(log, "a", 1)
    if case == "low-readiness":
        state = FakeState(default_e=0.97, tier_factor={3: 0.9}, speed=0.6)
    assert bool(sitting_items(plan(log, day(3), state))) == sits


def test_a_failed_sitting_waits_two_study_days_and_a_void_one_does_not() -> None:
    """A sitting failed on day 2 (a wrong answer): none on days 3 and 4, one on day 5 (the
    practice rule holds: the failed sitting's problems are practice, so a later success is
    needed first). A void one on day 2 (a correct answer without a valid time): one on day
    3."""
    log = Log()
    ready(log, "a", 1)
    fam = tier3("a")
    log.sitting([fam[2], fam[4]], day(2), "10")
    log.add(fam[6], day(2), True, minutes=1.0)  # practice after the sitting: right
    assert not sitting_items(plan(log, day(3)))
    assert not sitting_items(plan(log, day(4)))
    assert sitting_items(plan(log, day(5)))
    log = Log()
    ready(log, "a", 1)
    log.sitting([fam[2], fam[4]], day(2), minutes=None)
    assert Certifier(log.items, today=day(2)).sittings("a")[0].outcome == "void"
    assert sitting_items(plan(log, day(3)))


def test_the_practice_rule_and_the_wait() -> None:
    log = Log()
    t = tier3("a")
    log.add(t[0], day(1), False)
    log.add(t[1], day(1), True, minutes=1.0)
    assert practice_ready(log.items, [])
    log.sitting([t[2], t[3]], day(2), "10")  # failed: its problems are practice
    assert not practice_ready(log.items, [])
    log = Log()
    log.add(t[0], day(1), True, minutes=1.0)
    log.sitting([t[2], t[3]], day(2))  # passed: not practice
    assert not practice_ready(log.items, [day(2)])

    def failed(d: int) -> SittingResult:
        return SittingResult("a", 3, day(d), "fail", 2, None, 7.0)

    assert waiting([failed(2)], day(3))
    assert waiting([failed(2)], day(4))
    assert not waiting([failed(2)], day(5))
    assert not waiting([SittingResult("a", 3, day(2), "void", 2, None, 7.0)], day(3))


def test_below_the_pass_chance_the_skill_keeps_growing_with_a_note() -> None:
    """At medians of T* (speed 1.0) the time part for 3 problems is 0.40 and the pass chance
    0.97^3 x 0.40 = 0.37 < 0.5: no sitting, a growth day instead, the chance logged, and one
    note that the skill is not yet at pace."""
    log = Log()
    ready(log, "a", 1)
    slow = FakeState(default_e=0.97, speed=1.0)
    p = plan(log, day(3), slow)
    assert not sitting_items(p)
    chance = dict(p.sitting_chances)["a"]
    assert chance == pytest.approx(0.97**3 * pace_chance([1.0] * 3, [1.0] * 3, 0.45), rel=1e-4)
    assert any(i.skill_id == "a" and i.role == "growth" for i in p.items)
    assert sum(1 for n in p.notes if n.startswith("a: not yet at pace")) == 1


def test_at_most_three_skills_sit_earliest_deadline_first() -> None:
    """a, b, c and d are all due on day 8; their M2 deadlines are days 14, 16, 18 and 20:
    a, b and c sit, d waits."""
    log = Log()
    for sid in ("a", "b", "c", "d"):
        ready(log, sid, INTRO[sid] + 1)
    p = plan(log, day(8))
    assert p.sittings[0][1] == ("a", "b", "c")
    assert {i.skill_id for i in sitting_items(p)} == {"a", "b", "c"}


def test_a_thin_pool_reuses_the_least_recently_served_problems_with_a_note() -> None:
    """a's tier 3 has 3 problems, all served before (two in practice on day 1, one on day
    0): too few unseen, so the sitting takes the least recently served ones and a note says
    the pool is thin."""
    t3 = (problem("a.t3.x", "a", 3), problem("a.t3.y", "a", 3), problem("a.t3.z", "a", 3))
    sk = skill("a", A, 1, problems=(*pool("a", {1: 2, 2: 4}), *t3))
    cr = course([(A, 1.0)], [sk], weekly=3.5)
    log = Log()
    log.add(sk.pool[0], D0, True, role="new")
    log.many(sk.pool[2], day(1), "111")
    log.add(t3[2], D0, True, minutes=1.0)
    log.add(t3[0], day(1), False)
    log.add(t3[1], day(1), True, minutes=1.0)
    model = fake(cr)
    now = at(day(3), 600)
    cert = Certifier.for_course(
        log.items, cr, SETTINGS, today=day(3), priors=model_priors(model, FAST, cr, now)
    )
    p = plan_day(model, FAST, cert, cr, SETTINGS, day(3), now, rng=rng())
    picked = [i.problem.problem_id for i in sitting_items(p) if i.problem]
    assert sorted(picked) == ["a.t3.x", "a.t3.z"]  # z (day 0) first, then x by id
    assert any("a: few unseen tier-3 problems" in n for n in p.notes)


# ---------------------------------------------------------------------- serving


def test_a_sitting_under_way_is_served_to_the_end_first() -> None:
    """Once the first sitting problem is served, the next plan starts with the rest of the
    block in its order, and nothing else comes between; the block's frame comes from the
    served item. A set-aside skill's remaining problems leave it."""
    log = Log()
    ready(log, "a", 1)
    ready(log, "b", 3)
    p = plan(log, day(5))
    items = sitting_items(p)
    assert {i.skill_id for i in items} == {"a", "b"}
    first = items[0]
    assert first.problem is not None
    log.add(first.problem, day(5), True, minutes=1.0, role="sitting")
    served = [ServedItem(first, correct=True, minutes=1.0)]
    nxt = plan(log, day(5), served=served, minute=601)
    rest = [i.problem.problem_id for i in items[1:] if i.problem]
    assert [i.problem.problem_id for i in nxt.items[: len(rest)] if i.problem] == rest
    assert nxt.sittings == p.sittings


def test_a_passed_sitting_certifies_and_the_skill_moves_on() -> None:
    """Every sitting problem right and the block within its time: M2 certified that day. The
    pools stop at tier 3, so M3 (tier 4) has no problems and is left out: the next day a is
    in maintenance at level 3, and no new sitting is planned for it."""
    log = Log()
    ready(log, "a", 1)
    items = sitting_items(plan(log, day(3)))
    for it in items:
        assert it.problem is not None
        log.add(it.problem, day(3), True, minutes=1.0, role="sitting")
    p = plan(log, day(4))
    st = next(s for s in p.statuses if s.skill_id == "a")
    assert (st.state, st.current, st.level) == ("maintenance", None, 3)
    assert not sitting_items(p)
    cert = Certifier(log.items, today=day(3), priors={("a", 3): 0.97})
    assert cert.sittings("a")[0].outcome == "pass"
    assert cert.state("a", 3).since == day(3)


def test_a_sitting_over_its_block_limit_fails() -> None:
    """All right but 4.0 minutes each against T* 3.5: 12.0 > 10.5, a fail."""
    log = Log()
    ready(log, "a", 1)
    for it in sitting_items(plan(log, day(3))):
        assert it.problem is not None
        log.add(it.problem, day(3), True, minutes=4.0, role="sitting")
    result = Certifier(log.items, today=day(3)).sittings("a")[0]
    assert (result.outcome, result.minutes, result.limit) == ("fail", 12.0, 10.5)


def test_a_skill_set_aside_before_the_sitting_does_not_sit() -> None:
    """a misses three in a row today before its sitting starts: it is set aside, and the
    sitting goes ahead without it."""
    log = Log()
    ready(log, "a", 1)
    ready(log, "b", 3)
    pred = Prediction(p=0.7, p_raw=0.7, q=(), e=(), r=(), median_minutes=2.0, pace_ok=True)
    served: list[ServedItem] = []
    for k in range(3):
        p = plan(log, day(5), served=served, minute=600 + k)
        item = next(i for i in p.items if i.ladder_for == "a" or i.skill_id == "a")
        assert item.role != "sitting"
        assert item.problem is not None
        log.add(item.problem, day(5), False, role=item.role)
        upd = UpdateRecord(pred, ((item.problem.main_skill, 1.0),), ())
        served.append(ServedItem(item, correct=False, update=upd))
    p = plan(log, day(5), served=served, minute=610)
    assert p.set_aside == ("a",)
    assert [i.skill_id for i in sitting_items(p)] == ["b"] * 3
    assert p.sittings[0][1] == ("b",)
