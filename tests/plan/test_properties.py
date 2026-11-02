"""Hypothesis properties of the day's plan on random courses, histories and served prefixes.

Each example builds a course (1-4 sections of 1-3 skills, random pools, prerequisites,
confusable pairs, an optional exam and end date), a fake student and a history, then serves
a random number of items one at a time through `next_item` with random outcomes, and checks
the whole day (served items, then the remaining plan):

- caps: at most 3 problems per skill a day (reference checks aside), at most 3 growth
  problems per skill a day, at most 3 block problems per skill ever;
- new material comes before any missed-milestone work, and missed-milestone work is at most
  40% of the day up to its last item of other work;
- never two items of one skill in a row, except inside a new skill's block;
- never a card twice in the day;
- at most one reference check per ten items and none before the 10th (and, on a plan with
  enough skills, exactly at every 10th position, or right after a new block covering it);
- the same seed gives the same plan, and `next_item` is the plan's first item.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import pairwise

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.learner.types import Observation, Prediction, UpdateRecord
from core.plan.certify import Certifier, model_priors
from core.plan.config import CHECK_EVERY, MISSED_SHARE
from core.plan.daily import main_share, next_item, plan_day
from core.plan.types import Course, CourseSettings, DayPlan, ExamSpec, ServedItem
from tests.plan.fakes import FakePredictor, FakeState
from tests.plan.helpers import Log, at, course, fake, pool, rng, skill

D0 = date(2026, 9, 1)
PLAN_ROLES = ("new", "growth", "maintenance", "check")


@dataclass
class World:
    course: Course
    settings: CourseSettings
    model: FakePredictor
    state: FakeState
    log: Log
    today: date
    seed: int


@st.composite
def worlds(draw: st.DrawFn) -> World:
    n_sections = draw(st.integers(1, 4))
    per = draw(st.integers(1, 3))
    sections = [(f"K::U{i // 2}::S{i}", float(draw(st.integers(1, 4)))) for i in range(n_sections)]
    skills = []
    order = 0
    for i, (deck, _) in enumerate(sections):
        for j in range(per):
            order += 1
            sid = f"s{i}{j}"
            counts = {t: draw(st.integers(0, 5)) for t in (1, 2, 3, 4)}
            counts[draw(st.sampled_from([1, 2]))] += 1  # something to start a block with
            requires = [f"s{i - 1}{j}"] if i and draw(st.booleans()) else []
            confusable = [f"s{i}{(j + 1) % per}"] if per > 1 and draw(st.booleans()) else []
            example = f"ex.{sid}" if draw(st.booleans()) else None
            skills.append(
                skill(
                    sid,
                    deck,
                    order,
                    requires=requires,
                    confusable=confusable,
                    example=example,
                    problems=pool(sid, counts),
                )
            )
    cr = course(sections, skills, weekly=draw(st.sampled_from([1.0, 2.0, 4.0])))
    today = D0 + timedelta(days=draw(st.integers(0, 70)))
    exams: tuple[ExamSpec, ...] = ()
    if draw(st.booleans()):
        exams = (ExamSpec(1, D0 + timedelta(days=draw(st.integers(5, 80))), (sections[0][0],)),)
    end = D0 + timedelta(days=draw(st.integers(20, 90))) if draw(st.booleans()) else None
    s = CourseSettings(
        "c",
        start=D0,
        pace_factor=draw(st.sampled_from([0.75, 1.0, 1.5])),
        target_tier=draw(st.sampled_from([3, 4])),
        exams=exams,
        end=end,
    )
    state = FakeState(
        default_e=draw(st.sampled_from([0.5, 0.75, 0.9, 0.97])),
        slip=draw(st.sampled_from([0.0, 0.05, 0.15])),
        speed=draw(st.sampled_from([0.8, 1.0, 1.4])),
    )
    model = fake(cr)
    # A history: block outcomes and some first tries on past days.
    log = Log()
    intro_days = {sk.skill_id: D0 + timedelta(days=7 * k) for k, sk in enumerate(skills)}
    for sk in skills:
        first = intro_days[sk.skill_id]
        if first >= today or not draw(st.booleans()):
            continue
        block = [p for p in sk.pool if p.tier <= 2]
        if draw(st.booleans()):
            log.add(block[0], first, True, role="new")
        else:
            for p in block[:3]:
                log.add(p, first, False, role="new")
        for _ in range(draw(st.integers(0, 6))):
            p = draw(st.sampled_from(sk.pool))
            d = first + timedelta(days=draw(st.integers(0, max(0, (today - first).days - 1))))
            ok = draw(st.booleans())
            log.add(p, d, ok, minutes=p.standard_minutes * 0.8 if ok else None)
    log.items.sort(key=lambda o: (o.study_day, o.attempt_id))
    log.items[:] = [
        Observation(
            i + 1,
            at(o.study_day, i),
            o.study_day,
            o.problem,
            o.correct,
            o.aided,
            None,
            o.minutes,
            o.role,
        )
        for i, o in enumerate(log.items)
    ]
    return World(cr, s, model, state, log, today, draw(st.integers(0, 10**6)))


def make_plan(w: World, served: Sequence[ServedItem], minute: int, seed: int) -> DayPlan:
    now = at(w.today, minute)
    priors = model_priors(w.model, w.state, w.course, now)
    cert = Certifier.for_course(w.log.items, w.course, w.settings, today=w.today, priors=priors)
    return plan_day(
        w.model, w.state, cert, w.course, w.settings, w.today, now, served, rng=rng(seed)
    )


def serve_some(w: World, data: st.DataObject, steps: int) -> tuple[list[ServedItem], DayPlan]:
    """Serve up to `steps` items one at a time, re-planning after each answer."""
    served: list[ServedItem] = []
    plan = make_plan(w, served, 0, w.seed)
    for k in range(steps):
        if not plan.items:
            break
        item = plan.items[0]
        correct: bool | None = None
        update = None
        if item.problem is not None:
            correct = data.draw(st.booleans(), label="correct")
            w.log.add(item.problem, w.today, correct, minutes=1.0, role=item.role)
            if not correct:
                comps = item.problem.components
                share = data.draw(st.sampled_from([0.1, 0.9]), label="m")
                pred = Prediction(
                    p=0.5, p_raw=0.5, q=(), e=(), r=(), median_minutes=1.0, pace_ok=True
                )
                update = UpdateRecord(
                    pred,
                    tuple((c, 1.0 / len(comps)) for c in comps),
                    tuple((c, share) for c in comps),
                )
        served.append(ServedItem(item, correct=correct, update=update))
        plan = make_plan(w, served, k + 1, w.seed + k + 1)
    return served, plan


def check_day(w: World, served: Sequence[ServedItem], plan: DayPlan) -> None:
    done = [x.item for x in served if x.item.role in PLAN_ROLES]
    day = [*done, *plan.items]

    # Caps.
    problems = Counter(i.skill_id for i in day if i.problem is not None and i.role != "check")
    assert all(n <= 3 for n in problems.values()), problems
    growth = Counter(i.skill_id for i in day if i.role == "growth")
    assert all(n <= 3 for n in growth.values()), growth
    past_new = Counter(
        o.problem.main_skill for o in w.log.items if o.role == "new" and o.study_day < w.today
    )
    block = Counter(i.skill_id for i in day if i.role == "new" and i.problem is not None)
    assert all(past_new[s] + n <= 3 for s, n in block.items()), (past_new, block)

    # New material before missed-milestone work; the 40% share up to the last other item.
    first_missed = next((k for k, i in enumerate(day) if i.missed), len(day))
    assert all(i.role != "new" for i in day[first_missed:])
    assert main_share(done, plan.items) <= MISSED_SHARE + 1e-9

    # Never two of one skill in a row outside a new block.
    for x, y in pairwise(day):
        assert x.skill_id != y.skill_id or (x.block and y.block), (x, y)

    # Never a card twice in the day.
    cards = [i.problem.card_id if i.problem else i.example_card for i in day]
    assert len(cards) == len(set(cards))

    # At most one reference check per ten items, none before the 10th.
    positions = [k + 1 for k, i in enumerate(day) if i.role == "check"]
    assert all(p >= CHECK_EVERY for p in positions)
    decades = Counter(p // CHECK_EVERY for p in positions)
    assert all(n == 1 for n in decades.values()), positions


@settings(
    max_examples=60,
    deadline=None,
    database=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(w=worlds(), data=st.data(), steps=st.integers(0, 12))
def test_day_invariants(w: World, data: st.DataObject, steps: int) -> None:
    served, plan = serve_some(w, data, steps)
    check_day(w, served, plan)


@settings(
    max_examples=40, deadline=None, database=None, suppress_health_check=[HealthCheck.too_slow]
)
@given(w=worlds())
def test_same_seed_same_plan_and_next_item_is_its_head(w: World) -> None:
    one = make_plan(w, [], 0, w.seed)
    two = make_plan(w, [], 0, w.seed)
    assert one == two
    now = at(w.today)
    priors = model_priors(w.model, w.state, w.course, now)
    cert = Certifier.for_course(w.log.items, w.course, w.settings, today=w.today, priors=priors)
    head = next_item(w.model, w.state, cert, w.course, w.settings, w.today, now, rng=rng(w.seed))
    assert head == (one.items[0] if one.items else None)


@st.composite
def wide_days(draw: st.DrawFn) -> tuple[Course, int, int, int]:
    """Many skills past their blocks (so a check and a neighbour are always available),
    plus some new skills today."""
    n_old = draw(st.integers(6, 12))
    n_new = draw(st.integers(0, 4))
    old = [
        skill(f"o{i}", "K::U::A", i, problems=pool(f"o{i}", {1: 2, 2: 8, 3: 8, 4: 8}))
        for i in range(n_old)
    ]
    new = [skill(f"n{i}", "K::U::B", 100 + i, example=f"ex.n{i}") for i in range(n_new)]
    return (
        course([("K::U::A", 2.0), ("K::U::B", 2.0)], old + new),
        n_old,
        n_new,
        draw(st.integers(0, 10**6)),
    )


@settings(
    max_examples=60, deadline=None, database=None, suppress_health_check=[HealthCheck.too_slow]
)
@given(day=wide_days())
def test_a_reference_check_every_tenth_item(day: tuple[Course, int, int, int]) -> None:
    """With enough skills to choose from, the check is exactly the 10th, 20th, ... item, or
    the item right after a new block that covers that position."""
    cr, n_old, _, seed = day
    log = Log()
    for sk in cr.skills[:n_old]:
        log.add(sk.pool[0], D0, True, role="new")
    today = D0 + timedelta(days=7)  # B is introduced today; A's skills grow (M1 on time)
    s = CourseSettings("c", start=D0)
    model = fake(cr)
    cert = Certifier.for_course(log.items, cr, s, today=today)
    plan = plan_day(model, FakeState(), cert, cr, s, today, at(today), rng=rng(seed))
    items = list(plan.items)
    assert plan.dropped == ()
    for slot in range(CHECK_EVERY, len(items) + 1, CHECK_EVERY):
        it = items[slot - 1]
        if it.role == "check":
            continue
        # Otherwise the slot falls inside a new block, after its first item ...
        before = items[slot - 2]
        assert it.block, (slot, [i.role for i in items])
        assert before.block, (slot, [i.role for i in items])
        assert before.skill_id == it.skill_id, (slot, [i.skill_id for i in items])
        # ... and the check comes right after that block (unless the day ends with it).
        end = slot - 1
        while end < len(items) and items[end].block and items[end].skill_id == it.skill_id:
            end += 1
        if end < len(items):
            assert items[end].role == "check", (slot, [i.role for i in items])
