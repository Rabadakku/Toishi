"""The stuck ladder and re-plans that never add items (docs/design/wave2-planner.md sections 1
and 4): streaks, the smaller problem, the prerequisite, the set-aside and its return, the held
retry slot and the day's first-plan size."""

from datetime import date, timedelta

import pytest

from core.learner.types import Prediction, UpdateRecord
from core.plan.certify import Certifier, model_priors
from core.plan.daily import plan_day
from core.plan.ladder import blamed_prerequisite, owners, read_ladder, returning, top_blamed
from core.plan.select import Seen, choose_smaller
from core.plan.types import CourseSettings, DayPlan, ServedItem, WorkItem
from tests.plan.fakes import FakeState
from tests.plan.helpers import Log, at, course, fake, pool, problem, rng, skill

A = "K::U::A"
D0 = date(2026, 9, 1)  # every skill is introduced on day 0 (one section)
SETTINGS = CourseSettings("c", start=D0)


def day(n: int) -> date:
    return D0 + timedelta(days=n)


S_POOL = (
    *pool("s", {1: 2}),
    problem("s.t2.k1", "s", 2, uses=["k"]),
    problem("s.t2.k2", "s", 2, uses=["k"]),
    problem("s.t2.x1", "s", 2),
    problem("s.t2.x2", "s", 2),
    problem("s.t2.x3", "s", 2),
    *(problem(f"s.t3.{i:02d}", "s", 3, uses=["k", "p"]) for i in range(1, 7)),
)
COURSE = course(
    [(A, 2.0)],
    [
        skill("p", A, 1, problems=pool("p", {1: 2, 2: 4})),
        skill("k", A, 2, problems=pool("k", {1: 2, 2: 4})),
        skill("s", A, 3, requires=["k", "p"], problems=S_POOL),
        skill("o", A, 4, problems=pool("o")),
        skill("q", A, 5, problems=pool("q")),
    ],
)
SK = {s.skill_id: s for s in COURSE.skills}
MODEL = fake(COURSE, extra_background=["alg.x"])
PRED = Prediction(p=0.7, p_raw=0.7, q=(), e=(), r=(), median_minutes=3.5, pace_ok=True)


def history() -> Log:
    """Every block done on day 0; s certifies M1 on day 1 (3 of 3 at tier 2), so on day 2
    it grows toward M2 at tier 3 (or 2)."""
    log = Log()
    for sid in SK:
        log.add(SK[sid].pool[0], D0, True, role="new")
    log.many(SK["s"].pool[4], day(1), "111")  # s.t2.x1
    return log


def certify_q(log: Log) -> None:
    """q certifies M1-M3 on day 1: 3 of 3 at tier 2, then 2 practice tries and a passed
    sitting at tiers 3 and 4."""
    q = SK["q"].pool  # tiers 1-4, three problems each
    log.many(q[3], day(1), "111")
    log.many(q[6], day(1), "11", minutes=1.0)
    log.sitting(q[7:9], day(1))
    log.many(q[9], day(1), "11", minutes=1.0)
    log.sitting(q[10:12], day(1))


class Day:
    """One study day served item by item, the way the session will."""

    def __init__(self, log: Log, today: date, state: FakeState | None = None) -> None:
        self.log = log
        self.today = today
        self.state = state or FakeState()
        self.served: list[ServedItem] = []
        self.next_study_day: date | None = None
        self.plans: list[DayPlan] = [self.plan()]

    def plan(self) -> DayPlan:
        now = at(self.today, 600 + len(self.served))
        priors = model_priors(MODEL, self.state, COURSE, now)
        cert = Certifier.for_course(
            self.log.items, COURSE, SETTINGS, today=self.today, priors=priors
        )
        return plan_day(
            MODEL,
            self.state,
            cert,
            COURSE,
            SETTINGS,
            self.today,
            now,
            self.served,
            rng=rng(len(self.served)),
            next_study_day=self.next_study_day,
        )

    @property
    def last(self) -> DayPlan:
        return self.plans[-1]

    def next_of(self, sid: str) -> WorkItem:
        """The skill's next planned item (the first item whose slot it owns)."""
        return next(i for i in self.last.items if sid in owners(i) and i.role != "check")

    def serve(
        self, item: WorkItem, correct: bool, blame: tuple[tuple[str, float], ...] = ()
    ) -> None:
        assert item.problem is not None
        self.log.add(item.problem, self.today, correct, minutes=2.0, role=item.role)
        update = None if correct else UpdateRecord(PRED, blame, tuple((k, 0.1) for k, _ in blame))
        self.served.append(ServedItem(item, correct=correct, update=update))
        self.plans.append(self.plan())

    def total(self) -> int:
        return len(self.served) + len(self.last.items)


# ---------------------------------------------------------------------- streaks


def served(
    sid: str, correct: bool | None, *, role: str = "growth", ladder_for: str | None = None
) -> ServedItem:
    p = problem(f"{sid}.x", sid, 2)
    item = WorkItem(sid, role, p, None, 3.0, 1, ladder_for=ladder_for)  # type: ignore[arg-type]
    return ServedItem(item, correct=correct)


def test_the_streak_counts_misses_since_the_last_success_today_in_any_role() -> None:
    """Misses of s as growth, a reference check and a sitting count; a success resets; an
    unanswered item (a worked example) counts nothing. A rung-2 item (a problem of k filling
    s's slot) counts for both s and k. Three in a row set s aside for the day, even after a
    later success."""
    lad = read_ladder(
        [
            served("s", False),
            served("s", True),
            served("s", False, role="check"),
            served("s", None),
            served("s", False, role="sitting"),
        ]
    )
    assert lad.streak["s"] == 2
    assert [x.item.role for x in lad.misses["s"]] == ["check", "sitting"]
    lad = read_ladder([served("s", False), served("s", False), served("k", False, ladder_for="s")])
    assert (lad.streak["s"], lad.streak["k"]) == (3, 1)
    assert lad.set_aside == frozenset({"s"})
    lad = read_ladder([served("s", False)] * 3 + [served("s", True)])
    assert lad.streak["s"] == 0
    assert "s" in lad.set_aside


def test_blame_picks_the_component_and_the_prerequisite() -> None:
    """k*: the largest blame of the last miss, the skill itself on a tie or without blame.
    The prerequisite: the largest blame other than the skill over the last two misses."""
    miss = ServedItem(
        WorkItem("s", "growth", S_POOL[0], None, 3.0, 1),
        correct=False,
        update=UpdateRecord(PRED, (("k", 0.5), ("s", 0.5), ("p", 0.2)), ()),
    )
    assert top_blamed(miss, "s") == "s"
    assert top_blamed(ServedItem(miss.item, correct=False), "s") == "s"
    other = ServedItem(
        miss.item, correct=False, update=UpdateRecord(PRED, (("p", 0.4), ("s", 0.6)), ())
    )
    assert blamed_prerequisite([miss, other], "s", {"p": 1, "k": 2}) == "p"  # p 0.6, k 0.5
    assert blamed_prerequisite([ServedItem(miss.item, correct=False)], "s", {}) is None


# ---------------------------------------------------------------------- rung 1


def test_after_one_miss_the_next_item_is_a_smaller_problem_with_the_blamed_component() -> None:
    """Day 2: s misses a tier-3 problem, blame k 0.6 (k*), s 0.3, p 0.1. Its next item is a
    tier-2 problem of s that contains k (s.t2.k1, never served), rung 1, in the slot of its
    next planned growth problem; the day's items stay within the first plan."""
    d = Day(history(), day(2))
    first_size = len(d.plans[0].items)
    d.serve(d.next_of("s"), False, (("k", 0.6), ("s", 0.3), ("p", 0.1)))
    nxt = d.next_of("s")
    assert nxt.problem is not None
    assert (nxt.problem.problem_id, nxt.ladder, nxt.reason) == ("s.t2.k1", 1, "ladder:smaller")
    assert (nxt.skill_id, nxt.role, nxt.ladder_for) == ("s", "growth", "s")
    assert d.total() <= first_size
    assert sum(1 for i in d.last.items if i.skill_id == "s" and i.role != "check") == 2


def test_a_smaller_problem_prefers_unseen_then_least_recently_served() -> None:
    """At tier 2 with k: s.t2.k1 seen 3 days ago, s.t2.k2 10 days ago: k2. Both seen and a
    tier-1 miss: tier 1 again (at least tier 1). Without k at the tier: the skill's others."""
    log = Log()
    log.add(S_POOL[2], day(7), True)  # s.t2.k1
    log.add(S_POOL[3], D0, True)  # s.t2.k2
    seen = Seen(log.items, day(10))

    def pred(p: object) -> Prediction:
        return PRED

    got = choose_smaller(SK["s"], 3, "k", pred, seen)
    assert got is not None
    assert got.problem.problem_id == "s.t2.k2"
    got = choose_smaller(SK["s"], 1, "s", pred, seen)
    assert got is not None
    assert got.problem.tier == 1
    got = choose_smaller(SK["s"], 3, "alg.x", pred, seen)
    assert got is not None
    assert got.problem.problem_id == "s.t2.x1"  # no problem has alg.x: never served first


# ---------------------------------------------------------------------- rung 2


def test_after_two_misses_a_problem_of_the_most_blamed_prerequisite() -> None:
    """s misses (k 0.6, s 0.3, p 0.1), then misses the smaller problem (k 0.5, s 0.5): over
    both, k leads (1.1). s's next slot is a tier 1-2 problem of k (skill_id k, ladder_for s,
    rung 2). k keeps to 3 problems today: the ladder item takes one of its planned slots."""
    d = Day(history(), day(2))
    first_size = len(d.plans[0].items)
    d.serve(d.next_of("s"), False, (("k", 0.6), ("s", 0.3), ("p", 0.1)))
    d.serve(d.next_of("s"), False, (("k", 0.5), ("s", 0.5)))
    nxt = d.next_of("s")
    assert nxt.problem is not None
    assert (nxt.skill_id, nxt.ladder_for, nxt.ladder) == ("k", "s", 2)
    assert nxt.reason == "ladder:prerequisite"
    assert nxt.problem.main_skill == "k"
    assert nxt.problem.tier in (1, 2)
    k_today = [i for i in d.last.items if i.skill_id == "k" and i.role != "check"]
    assert len(k_today) <= 3
    assert d.total() <= first_size


def test_rung_two_without_a_pool_takes_the_requires_in_course_order() -> None:
    """The blame points at background alg.x (no problems): s's requires in course order, p
    (order 1) before k (order 2)."""
    d = Day(history(), day(2))
    d.serve(d.next_of("s"), False, (("alg.x", 0.7), ("s", 0.3)))
    d.serve(d.next_of("s"), False, (("alg.x", 0.6), ("s", 0.4)))
    nxt = d.next_of("s")
    assert (nxt.skill_id, nxt.ladder, nxt.reason) == ("p", 2, "ladder:prerequisite")


def test_rung_two_with_no_prerequisite_gives_a_smaller_problem_again() -> None:
    """o has no requires and the blame is all its own: rung 2 falls back to a smaller
    problem of o (ladder 2, reason ladder:smaller)."""
    d = Day(history(), day(2))
    d.serve(d.next_of("o"), False, (("o", 1.0),))
    d.serve(d.next_of("o"), False, (("o", 1.0),))
    nxt = d.next_of("o")
    assert (nxt.skill_id, nxt.ladder, nxt.reason) == ("o", 2, "ladder:smaller")


# ---------------------------------------------------------------------- rung 3


def test_three_misses_set_the_skill_aside_for_the_day() -> None:
    """A miss on the rung-2 item (a problem of k in s's slot) is s's third in a row: no
    more items of s today (no reference check either), DayPlan.set_aside has s, and a note
    names its deck (the session's textbook pointer). k only gets its first miss."""
    d = Day(history(), day(2))
    d.serve(d.next_of("s"), False, (("k", 0.6), ("s", 0.3), ("p", 0.1)))
    d.serve(d.next_of("s"), False, (("k", 0.5), ("s", 0.5)))
    rung2 = d.next_of("s")
    assert rung2.ladder == 2
    d.serve(rung2, False, (("k", 1.0),))
    plan = d.last
    assert plan.set_aside == ("s",)
    assert not [i for i in plan.items if i.skill_id == "s" or i.ladder_for == "s"]
    assert any("s: set aside" in n and A in n for n in plan.notes)
    k_next = next(i for i in plan.items if i.skill_id == "k" and i.role != "check")
    assert k_next.ladder == 1  # k's own ladder: one miss


def test_a_set_aside_skill_returns_with_a_fresh_family_at_the_failing_tier() -> None:
    """Day 2 ended with s's misses at tier 3 then tier 2 (its own problems; the rung-2 miss
    was k's problem). On day 3, s's first problem is from a family not served in the last 7
    days, at tier 3, the tier where it was failing (reason "return")."""
    d = Day(history(), day(2))
    first = d.next_of("s")
    d.serve(first, False, (("k", 0.6), ("s", 0.3), ("p", 0.1)))
    d.serve(d.next_of("s"), False, (("k", 0.5), ("s", 0.5)))
    d.serve(d.next_of("s"), False, (("k", 1.0),))
    own = [o for o in d.log.items if o.problem.main_skill == "s"]
    assert returning(own, day(3)) == 3
    assert returning(own, day(2)) is None  # it has first tries today
    nxt = Day(d.log, day(3)).next_of("s")
    assert nxt.problem is not None
    assert (nxt.reason, nxt.tier) == ("return", 3)
    assert first.problem is not None
    assert nxt.problem.family != first.problem.family


def test_a_skill_with_nothing_left_today_gets_no_ladder_item() -> None:
    """The ladder replaces, never adds: s misses, gets its smaller problem right (the streak
    resets), then misses its third and last slot: its streak is 1 again, but nothing of s is
    left to replace, so nothing comes."""
    d = Day(history(), day(2))
    for ok in (False, True, False):
        d.serve(d.next_of("s"), ok, (("s", 1.0),))
    assert read_ladder(d.served).streak["s"] == 1
    assert not [i for i in d.last.items if owners(i)[-1] == "s" and i.role != "check"]


def test_the_band_option_reaches_the_ladder_and_growth() -> None:
    """CourseSettings.growth_band (0.50, 0.75): s's growth problems on day 2 are chosen in
    that band (tier 3 at 0.73 qualifies; tier-2 problems at 0.81 and 0.9 don't)."""
    hard = CourseSettings("c", start=D0, growth_band=(0.50, 0.75))
    log = history()
    now = at(day(2), 600)
    state = FakeState()
    cert = Certifier.for_course(
        log.items, COURSE, hard, today=day(2), priors=model_priors(MODEL, state, COURSE, now)
    )
    p = plan_day(MODEL, state, cert, COURSE, hard, day(2), now, rng=rng())
    s_items = [i for i in p.items if i.skill_id == "s" and i.role == "growth"]
    assert s_items
    assert all(i.p is not None and 0.5 <= i.p <= 0.75 for i in s_items)


# ---------------------------------------------------------------------- never adds


def test_a_maintenance_item_falling_due_later_only_takes_a_released_slot() -> None:
    """The first plan stamps its size on every item. q is certified (stability 20 days) and
    not due for tomorrow: R = 0.9^(2/20) = 0.99, readiness 0.96. Mid-day the next study day
    moves 20 days out: R = 0.9^(21/20) = 0.895, readiness 0.87 < 0.9, due. Maintenance for q
    comes into the plan (with its retry slot), yet the day stays within the first plan's
    size: the lowest-priority items give way."""
    log = history()
    certify_q(log)
    state = FakeState(default_e=0.97, stability={"q": 20.0}, last_ms={"q": at(day(1), 600)})
    d = Day(log, day(2), state)
    size = len(d.plans[0].items)
    assert all(i.day_items == size for i in d.plans[0].items)
    assert not [i for i in d.plans[0].items if i.role == "maintenance"]
    d.next_study_day = day(22)
    head = d.last.items[0]
    d.serve(head, True)
    assert [i.reason for i in d.last.items if i.role == "maintenance"] == ["forecast", "retry"]
    assert d.total() <= size
    assert all(i.day_items == size for i in d.last.items)


@pytest.mark.parametrize("m", [0.2, 0.8])
def test_the_retry_slot_is_held_from_the_first_plan(m: float) -> None:
    """A due maintenance skill's plan holds a second slot (4.6's retry). A miss that was
    mostly memory (m 0.8) releases it; an execution miss (m 0.2) keeps it for one more
    problem (which the ladder makes a smaller one)."""
    log = history()
    certify_q(log)
    state = FakeState(default_e=0.97, stability={"q": 1.0}, last_ms={"q": at(day(1), 600)})
    d = Day(log, day(2), state)
    mine = [i for i in d.last.items if i.skill_id == "q" and i.role == "maintenance"]
    assert [i.reason for i in mine] == ["forecast", "retry"]
    d.serve(mine[0], False, (("q", 1.0),))
    d.served[-1] = ServedItem(
        mine[0], correct=False, update=UpdateRecord(PRED, (("q", 1.0),), (("q", m),))
    )
    d.plans.append(d.plan())
    left = [i for i in d.last.items if i.skill_id == "q" and i.role != "check"]
    assert len(left) == (1 if m < 0.5 else 0)
