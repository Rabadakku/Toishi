"""Loose ends between the fitting (ADR-0013) and grading (ADR-0014) branches (ADR-0016)."""

from datetime import datetime, timedelta

from fsrs.scheduler import DEFAULT_PARAMETERS

from core.engine import FsrsAdapter
from core.engine.boosters import BoostTarget, plan_boosters
from core.engine.config import GOOD
from core.engine.lifecycle import due_day, review_on
from core.engine.placement import apply_seeds
from core.engine.schedule import goal_change, scheduled_load
from core.model import SkillState
from core.storage.clock import to_ms
from tests.engine.helpers import DAYS, UTC_DAYS, ZONE


def test_C4_review_on_counts_whole_study_days_on_the_calendar_it_is_given():
    adapter = FsrsAdapter(days=UTC_DAYS)  # counts days on another calendar than the profile's
    first = adapter.review(None, GOOD, to_ms(datetime(2026, 9, 1, 22, 0, tzinfo=ZONE)))
    at = to_ms(datetime(2026, 9, 3, 1, 0, tzinfo=ZONE))
    assert DAYS.between(first.last_review_at, at) == 1  # New York: Sep 1 -> Sep 2
    assert UTC_DAYS.between(first.last_review_at, at) == 2  # UTC: Sep 1 -> Sep 3
    after = review_on(adapter, first, GOOD, at, DAYS)
    assert after == adapter.review(first, GOOD, at, elapsed_days=1)
    # Live updates, replay and recompute share one clock.
    assert after == adapter.replay([(GOOD, first.last_review_at), (GOOD, at)], DAYS)
    later = first.last_review_at + 3_600_000
    same_day = review_on(adapter, first, GOOD, later, DAYS)
    assert same_day == adapter.review(first, GOOD, later, elapsed_days=0)


def test_I7_auto_fit_takes_the_writing_lock_only_to_write_and_recompute(storage, clock):
    from contextlib import contextmanager

    from core.engine import Engine
    from core.engine.param_sets import fit_log_key
    from tests.engine.fitlog import learner_log, store_log
    from tests.engine.test_fitting import TRUE

    engine = Engine(storage)
    start = clock.now_ms() - 400 * 86_400_000
    store_log(storage, learner_log(TRUE, cards=75, reviews=4, seed=7, days=DAYS, start=start))
    assert engine.fit_due("skills")
    held: list[bool] = []
    written: list[bool] = []
    real_apply = engine.apply_fit

    def apply(fit):  # the write half: only ever inside the lock
        written.append(bool(held) and held[-1])
        return real_apply(fit)

    real_decide = engine.fit_decision

    def decide(*args, **kw):  # the slow half: never inside it
        assert not (held and held[-1])
        return real_decide(*args, **kw)

    engine.apply_fit = apply  # type: ignore[method-assign]
    engine.fit_decision = decide  # type: ignore[method-assign]

    @contextmanager
    def writing():
        held.append(True)
        try:
            yield
        finally:
            held.append(False)

    (report,) = engine.auto_fit(writing=writing)
    assert report.items == 300
    assert written == [True]
    assert held == [True, False]
    assert storage.users.get_setting(fit_log_key("skills"))["items"] == 300
    assert not engine.fit_due("skills")


# ---------------------------------------------------------------- decision 6 in scheduling

OTHER_SET = [*DEFAULT_PARAMETERS[:4], 3.0, *DEFAULT_PARAMETERS[5:20], 0.6]


def _two_sets() -> tuple[FsrsAdapter, FsrsAdapter, dict[str, FsrsAdapter]]:
    default = FsrsAdapter(days=DAYS, fuzz=False)
    other = FsrsAdapter(OTHER_SET, days=DAYS, fuzz=False)
    return default, other, {"a.one": default, "b.two": other}


def _in_review(skill: str, stability: float, last: int) -> SkillState:
    return SkillState(
        skill_id=skill, fsrs_state=2, stability=stability, difficulty=5.0, last_review_at=last
    )


def test_D6_load_boosters_goal_changes_and_seeds_use_each_skills_own_set():
    default, other, by_skill = _two_sets()
    t0 = to_ms(datetime(2026, 9, 1, 12, tzinfo=ZONE))
    today = DAYS.day_of(t0)
    states = {k: _in_review(k, 20.0, t0) for k in by_skill}
    # Load at retention 0.8, where the decay changes the interval.
    load = scheduled_load(
        states.values(),
        today,
        90,
        retention_of=lambda _k: 0.8,
        adapter=default,
        days=DAYS,
        adapter_of=by_skill.__getitem__,
    )
    own_days = {due_day(states[k], 0.8, a, DAYS) for k, a in by_skill.items()}
    assert len(own_days) == 2  # the two sets schedule the same memory differently
    assert {d for d, n in load.items() if n} == own_days
    # Boosters: each skill's outlook comes from its own set.
    target = BoostTarget(
        key="exam:1",
        name="Exam",
        day=today + timedelta(days=40),
        at_ms=t0 + 40 * 86_400_000,
        target=0.99,
        skill_ids=tuple(by_skill),
    )
    plan = plan_boosters(
        [target],
        states,
        today=today,
        retention_of=lambda _k: 0.99,
        adapter=default,
        days=DAYS,
        adapter_of=by_skill.__getitem__,
    )
    single = plan_boosters(
        [target], states, today=today, retention_of=lambda _k: 0.99, adapter=default, days=DAYS
    )
    (outlook,) = plan.outlooks
    (shared,) = single.outlooks
    assert outlook.recall["a.one"] == shared.recall["a.one"]
    assert outlook.recall["b.two"] != shared.recall["b.two"]
    # Goal changes: a skill is newly due by its own set's interval.
    change = goal_change(
        states.values(),
        today + timedelta(days=49),
        old_retention=lambda _k: 0.5,
        new_retention=lambda _k: 0.8,
        adapter=default,
        days=DAYS,
        adapter_of=by_skill.__getitem__,
    )
    alone = goal_change(
        states.values(),
        today + timedelta(days=49),
        old_retention=lambda _k: 0.5,
        new_retention=lambda _k: 0.8,
        adapter=default,
        days=DAYS,
    )
    assert change.newly_due == ("b.two",)  # due by day 49 under its own set only
    assert alone.newly_due == ()
    # Placement seeds start from the set's initial difficulty.
    seeds = apply_seeds(
        {}, {"b.two": "solid"}, at_ms=t0, adapter=default, adapter_of=by_skill.__getitem__
    )
    (seeded,) = seeds
    assert seeded.difficulty == other.review(None, GOOD, t0).difficulty
    assert seeded.difficulty != default.review(None, GOOD, t0).difficulty


def test_D6_engine_places_and_plans_with_the_domains_set(storage, clock):
    from core.engine import Engine
    from core.engine.param_sets import params_key, stored_value

    storage.users.set_settings(
        {
            "fsrs.domains": {"calc1": "math"},
            params_key("skills.math"): stored_value(OTHER_SET, at=0, source="fit"),
        }
    )
    engine = Engine(storage)
    (row,) = engine.place({"calc1.alg": "solid"})
    own = engine.adapter_for_skill("calc1.alg")
    assert own.params_id != engine.adapter().params_id
    assert row.difficulty == own.review(None, GOOD, clock.now_ms()).difficulty
