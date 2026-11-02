"""Acceptance tests for the scheduler-gap audit's grading items (ADR-0014).

Names follow the audit's item ids: D1 (Decision 1: a miss stays a miss), I2 (goal changes
without false escalations), I3 (load balancer), I4 (redo without item memory), I9 (partial
credit that can't compound), D5 (Decision 5: rated reviews aim at the desired retention).
"""

from dataclasses import replace
from datetime import timedelta

import pytest

from core.engine import EngineSettings, FsrsAdapter
from core.engine.config import AGAIN, ELO_TARGET_P, GOOD
from core.engine.diagnosis import DiagnosisSettings, partial_credit
from core.engine.diagnosis.credit import credit_switch
from core.engine.grading import record_try
from core.engine.lifecycle import (
    BALANCE,
    WEEKDAYS,
    balance,
    balance_weight,
    due_day,
    easy_day,
    easy_days_modifiers,
    interval_of,
    memory_of,
    review_on,
)
from core.engine.schedule import due_skills, goal_change, scheduled_load
from core.engine.selection import FormStats, SeenIndex, p_correct, pick_problem
from core.model import Attempt, ImplicitCredit, SkillShadow, SkillState
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, answer, seed, world
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import (
    DAYS,
    SKILL,
    Sim,
    at_day,
    card,
    learned_state,
    outcome,
    some,
)

MIN = 60_000


# ---------------------------------------------------------------- D1: a miss stays a miss


def test_D1_a_careless_slip_is_again_with_a_slip_flag_level_and_leeches_ignore() -> None:
    sim = Sim(learned_state(60.0, at=at_day(0), level="exam"))
    result = sim.grade(outcome(at_day(30), tier=3, correct=False, slip_within_cap=True))
    assert [e.rating for e in result.answer.reviews] == [AGAIN]  # never a pass (was Hard)
    assert result.decision.slip
    assert result.effects.slip
    assert result.answer.attempt.extra["slip"] is True
    state = some(sim.state)
    assert state.level == "exam"  # no Level demotion ...
    assert not state.shaky
    assert state.lapses == 1  # ... the card did lapse for FSRS ...
    assert state.level_evidence["leech_base"] == 1  # ... but the leech counter ignores it
    assert not result.effects.reinforcement_due


def test_D1_a_self_graded_minor_slip_is_again_with_the_slip_flag() -> None:
    sim = Sim(learned_state(60.0, at=at_day(0), level="exam"))
    result = sim.grade(outcome(at_day(30), tier=3, self_grade="minor-slip"))
    assert [e.rating for e in result.answer.reviews] == [AGAIN]  # was Hard
    assert result.decision.slip
    assert some(sim.state).level == "exam"
    assert some(sim.state).level_evidence["leech_base"] == 1


def test_D1_a_solved_cued_twin_keeps_the_original_miss_as_again() -> None:
    from tests.engine.diagnosis.fixtures import MC, PROD, QUOT

    w = world()
    for k in (ALG, POW):
        seed(w, k, stability=30, days_ago=3, theta=2.0)
    for k in (PROD, QUOT):
        seed(w, k, stability=15, days_ago=16, theta=1.0)
    seed(w, MC, stability=10, days_ago=2, theta=0.5)
    t = at_day(0)
    w.grade(answer(w, "c.prod.t2.0", t, correct=False, choice="setup", didnt_know_start=True))
    (twin,) = w.pending()
    w.grade(answer(w, some(twin.card_id), t + 5 * MIN, correct=True, check_of=twin.id))
    assert next((e.rating, e.at) for e in w.events_for(PROD)) == (AGAIN, t)  # not released


def test_D1_slips_never_make_a_leech() -> None:
    settings = EngineSettings()
    sim = Sim(learned_state(60.0, at=at_day(0)), settings=settings)
    day = 0
    for _ in range(settings.leech_lapses + 2):
        day += 10
        sim.grade(outcome(at_day(day), tier=2, correct=False, slip_within_cap=True))
        day += 1
        sim.grade(outcome(at_day(day), tier=2, ref=card(2, cid=f"ok{day}")))  # relearned
    state = some(sim.state)
    assert state.lapses == settings.leech_lapses + 2
    assert not state.leech
    assert state.leech_at is None


def test_D1_a_passed_step_check_keeps_the_original_miss_as_again() -> None:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0)
    t = at_day(0)
    w.grade(answer(w, "crit.t2.0", t, correct=False, choice="step", step=2))
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), t + 5 * MIN, correct=True, check_of=check.id))
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, t)]  # not Hard


def test_D1_a_failed_step_check_does_not_leave_the_original_miss_unrated() -> None:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0)
    t = at_day(0)
    w.grade(answer(w, "crit.t2.0", t, correct=False, choice="step", step=2))
    (check,) = w.pending()
    w.grade(answer(w, some(check.card_id), t + 5 * MIN, correct=False, check_of=check.id))
    assert [(e.rating, e.at) for e in w.events_for(CRIT)] == [(AGAIN, t)]  # not silence
    assert [e.rating for e in w.events_for(ALG)] == [AGAIN]  # the checked skill lapses too


def test_D1_a_stretch_miss_follow_up_never_comes_right_after_the_worked_solution() -> None:
    sim = Sim(learned_state(10.0, at=at_day(0)))
    miss = sim.grade(outcome(at_day(10), tier=4, correct=False))
    assert miss.effects.stage == "stretch"
    assert not miss.answer.reviews
    today = DAYS.day_of(at_day(10))
    # The skill's owed core-band review is not due again before the next study day.
    assert due_day(sim.state, 0.9, sim.fsrs, DAYS) == today + timedelta(days=1)
    assert due_skills([some(sim.state)], today, retention_of=lambda _: 0.9, adapter=sim.fsrs,
                      days=DAYS) == []  # fmt: skip


def test_D1_strict_ok_is_set_on_every_attempt() -> None:
    sim = Sim(learned_state(10.0, at=at_day(0)))
    rows = [
        sim.grade(outcome(at_day(10), tier=2)),  # right first try, no hint
        sim.grade(outcome(at_day(11), tier=2, attempt_number=2)),  # right on a later try
        sim.grade(outcome(at_day(12), tier=2, hints_used=1)),  # after a hint
        sim.grade(outcome(at_day(13), tier=2, correct=False, slip_within_cap=True)),
        sim.grade(outcome(at_day(14), tier=2, unsure=True)),  # Hard, but strictly right
        sim.grade(outcome(at_day(15), tier=2, self_grade="minor-slip")),
        sim.grade(outcome(at_day(16), tier=2, self_grade="matched")),
    ]
    assert [r.answer.attempt.strict_ok for r in rows] == [
        True,
        False,
        False,
        False,
        True,
        False,
        True,
    ]
    tried = record_try(sim.ctx(), outcome(at_day(17), tier=2, correct=False))
    assert tried.attempt.strict_ok is False
    example = sim.grade(outcome(at_day(18), ref=card(1, kind="example", cid="ex"), solve_ms=None))
    assert example.answer.attempt.strict_ok is False


# ---------------------------------------------------------------- I2: goal changes


def keep_to_a() -> tuple[SkillState, FsrsAdapter, int]:
    fsrs = FsrsAdapter(fuzz=False)
    reviewed = at_day(0)
    state = learned_state(30.0, at=reviewed)
    due = due_day(state, 0.80, fsrs, DAYS)  # cached at review time, under Keep
    state = replace(state, due_at=DAYS.start(some(due)))
    return state, fsrs, at_day(45)


def test_I2_S30_reviewed_45_days_ago_is_not_escalated_after_keep_to_a() -> None:
    state, fsrs, now = keep_to_a()
    assert fsrs.raw_interval(30.0, 0.80) == pytest.approx(99.5, abs=0.05)
    assert fsrs.raw_interval(30.0, 0.90) == pytest.approx(30.0, abs=0.05)
    today = DAYS.day_of(now)
    (due,) = due_skills([state], today, retention_of=lambda _: 0.90, adapter=fsrs, days=DAYS)
    assert due_day(state, 0.90, fsrs, DAYS) == today - timedelta(days=15)  # live: 15 d late
    assert not due.escalated  # escalation reads the due date cached under Keep
    assert due.due_day == today  # a due date that moved into the past is clamped to today
    assert due.days_overdue == 0


def test_I2_a_skill_really_overdue_by_its_cached_due_date_still_escalates() -> None:
    state, fsrs, _ = keep_to_a()
    late = DAYS.day_of(some(state.due_at)) + timedelta(days=8)
    (due,) = due_skills([state], late, retention_of=lambda _: 0.80, adapter=fsrs, days=DAYS)
    assert due.escalated
    # Rows without a cached due date fall back to an R deficit.
    bare = replace(state, due_at=None)
    (due,) = due_skills([bare], late, retention_of=lambda _: 0.80, adapter=fsrs, days=DAYS)
    assert due.escalated
    on_time = DAYS.day_of(some(state.due_at)) + timedelta(days=2)
    (due,) = due_skills([bare], on_time, retention_of=lambda _: 0.80, adapter=fsrs, days=DAYS)
    assert not due.escalated


def test_I2_goal_preview_counts_skills_whose_live_due_moves_to_today_or_earlier() -> None:
    fsrs = FsrsAdapter(fuzz=False)
    today = DAYS.day_of(at_day(45))
    states = []
    for i, (stability, days_ago) in enumerate(
        [(30, 45), (30, 31), (30, 20), (30, 100), (10, 12), (10, 40), (60, 70), (5, 3)]
    ):
        state = replace(learned_state(float(stability), at=at_day(45 - days_ago)), skill_id=f"s{i}")
        states.append(state)
    change = goal_change(
        states,
        today,
        old_retention=lambda _: 0.80,
        new_retention=lambda _: 0.90,
        adapter=fsrs,
        days=DAYS,
    )
    expected = {
        s.skill_id
        for s in states
        if some(due_day(s, 0.90, fsrs, DAYS)) <= today < some(due_day(s, 0.80, fsrs, DAYS))
    }
    assert set(change.newly_due) == expected
    assert len(change.newly_due) == 4
    assert change.message == "This makes 4 skills due."
    # Spread with the load balancer over the following days, never into the past.
    assert all(today <= d < today + timedelta(days=7) for d in change.spread.values())
    assert len(set(change.spread.values())) > 1
    for row in change.states:
        assert due_day(row, 0.90, fsrs, DAYS) == change.spread[row.skill_id]


# ---------------------------------------------------------------- I3: load balancer


def _simulate(*, balanced: bool, n_skills: int = 300, days_n: int = 90) -> list[int]:
    """Every skill due is reviewed Good on its due day; returns reviews per day."""
    import random

    fsrs = FsrsAdapter()
    rnd = random.Random(42)  # noqa: S311
    start = DAYS.day_of(at_day(0))
    states: dict[str, SkillState] = {}
    for i in range(n_skills):
        s = rnd.uniform(1.0, 25.0)
        state = replace(
            learned_state(s, at=at_day(-rnd.randrange(0, 20))),
            skill_id=f"k{i}",
            difficulty=rnd.uniform(3, 8),
        )
        states[state.skill_id] = state
    per_day: list[int] = []
    for n in range(days_n):
        day = start + timedelta(days=n)
        moment = DAYS.moment(day)
        todo = [k for k, s in states.items() if some(due_day(s, 0.9, fsrs, DAYS)) <= day]
        per_day.append(len(todo))
        for k in todo:
            state = states[k]
            memory = review_on(fsrs, memory_of(state), GOOD, moment, DAYS)
            new = replace(
                state,
                stability=memory.stability,
                difficulty=memory.difficulty,
                last_review_at=moment,
            )
            if balanced:
                others = [v for kk, v in states.items() if kk != k]
                load = scheduled_load(
                    others, day, 99, retention_of=lambda _: 0.9, adapter=fsrs, days=DAYS
                )
                new = balance(new, 0.9, fsrs, DAYS, load)
            states[k] = new
            # No due date outside its fuzz range.
            base = fsrs.interval_days(memory.stability, 0.9, None)
            got = interval_of(new, 0.9, fsrs)
            if base >= 3:
                low, high = fsrs.fuzz_range(base)
                assert low <= got <= high
            if balanced and 3 <= base <= 90:
                assert new.level_evidence[BALANCE]["last_review_at"] == moment
    return per_day


def test_I3_seeded_90_day_simulation_same_mean_load_lower_variance() -> None:
    import statistics

    hashed = _simulate(balanced=False)[30:]
    balanced = _simulate(balanced=True)[30:]
    assert statistics.mean(balanced) == pytest.approx(statistics.mean(hashed), rel=0.03)
    assert statistics.pvariance(balanced) < statistics.pvariance(hashed)


def test_I3_balancer_picks_inside_the_fuzz_range_keyed_by_the_last_review() -> None:
    fsrs = FsrsAdapter()
    state = learned_state(20.0, at=at_day(0))
    base = fsrs.interval_days(20.0, 0.9, None)
    low, high = fsrs.fuzz_range(base)
    last = DAYS.day_of(at_day(0))
    # Every day full but one: the empty day wins (weight 1 against tiny weights).
    empty = low + 1
    load = {last + timedelta(days=d): 0 if d == empty else 30 for d in range(low, high + 1)}
    chosen = balance(state, 0.9, fsrs, DAYS, load)
    assert interval_of(chosen, 0.9, fsrs) == empty
    assert due_day(chosen, 0.9, fsrs, DAYS) == last + timedelta(days=empty)
    # Valid only for the review it was chosen for, and the live interval it was chosen in.
    moved = replace(chosen, last_review_at=at_day(1))
    assert interval_of(moved, 0.9, fsrs) == fsrs.interval_days(20.0, 0.9, f"{SKILL.id}|{at_day(1)}")
    assert interval_of(chosen, 0.8, fsrs) == fsrs.interval_days(
        20.0, 0.8, f"{SKILL.id}|{at_day(0)}"
    )
    # Over 90 days: no balancing (Anki's MAX_LOAD_BALANCE_INTERVAL).
    long = learned_state(120.0, at=at_day(0))
    assert BALANCE not in balance(long, 0.9, fsrs, DAYS, load).level_evidence


def test_I3_grading_balances_the_new_due_date() -> None:
    sim = Sim(learned_state(10.0, at=at_day(0)), fsrs=FsrsAdapter())
    result = sim.grade(outcome(at_day(10), tier=2))
    assert result.state.level_evidence[BALANCE]["last_review_at"] == at_day(10)


# ---------------------------------------------------------------- I4: redo


def test_I4_a_redo_of_a_skill_that_is_not_due_leaves_S_and_D_and_writes_no_event() -> None:
    sim = Sim(learned_state(30.0, at=at_day(0)))
    before = some(sim.state)
    result = sim.grade(outcome(at_day(3), tier=2, purpose="redo"))
    assert result.effects.stage == "reinforcement"
    assert result.answer.reviews == ()
    assert result.answer.attempt.rating is None
    assert (result.state.stability, result.state.difficulty) == (
        before.stability,
        before.difficulty,
    )
    assert result.state.last_review_at == before.last_review_at


def test_I4_a_redo_of_a_due_skill_is_rated_when_nothing_fresher_was_served() -> None:
    sim = Sim(learned_state(3.0, at=at_day(0)))
    result = sim.grade(outcome(at_day(10), tier=2, purpose="redo"))
    assert result.effects.stage == "review"
    assert [e.rating for e in result.answer.reviews] == [GOOD]


# ---------------------------------------------------------------- D5: Elo target


def test_D5_rated_reviews_aim_at_the_desired_retention_not_080() -> None:
    refs = [card(2, cid=f"c{i}", template=f"t{i}") for i in range(5)]
    forms = {f"template:t{i}": FormStats(d, 5) for i, d in enumerate([-2.0, -1.0, -0.6, 0.0, 0.5])}
    seen = SeenIndex(forms=forms)
    theta = 1.2
    rated = pick_problem(refs, theta=theta, tiers=(2,), now_ms=0, seen=seen, target_p=0.90)
    plain = pick_problem(refs, theta=theta, tiers=(2,), now_ms=0, seen=seen)
    assert some(rated).p == pytest.approx(p_correct(theta, -1.0))  # 0.90
    assert some(plain).p == pytest.approx(p_correct(theta, 0.0))  # 0.77, nearest 0.80
    assert ELO_TARGET_P == 0.80


# ---------------------------------------------------------------- I9: partial credit


def credit_world() -> MemoryWorld:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=10, days_ago=5, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=20, theta=2.0)
    return w


def test_I9_two_encompassing_passes_on_one_day_credit_skill_B_once() -> None:
    w = credit_world()
    t = at_day(0)
    w.grade(answer(w, "crit.t3.0", t, correct=True))
    first = some(w.shadows[POW].credited_stability)
    w.grade(answer(w, "crit.t3.1", t + 30 * MIN, correct=True))
    assert [c.to_skill for c in w.credits].count(POW) == 1
    assert w.shadows[POW].credited_stability == first  # no compounding
    assert w.last.extra["diagnosis"].get("credit_forced") is None
    # The next study day credits again.
    w.grade(answer(w, "crit.t3.2", at_day(1), correct=True))
    assert [c.to_skill for c in w.credits].count(POW) == 2


def test_I9_a_larger_weight_later_the_same_day_replaces_the_days_credit() -> None:
    w = credit_world()
    t = at_day(0)
    state = w.states[POW]
    memory = some(memory_of(state))
    small = ImplicitCredit(
        at=t, from_skill=CRIT, to_skill=POW, weight=0.25, mode="shadow",
        stability_before=memory.stability, stability_after=memory.stability + 1,
    )  # fmt: skip
    result = partial_credit(
        CRIT,
        now=t + MIN,
        mode="shadow",
        skills=w.skills(),
        state_of=w.state,
        shadow_of=lambda _: SkillShadow(skill_id=POW, credited_stability=memory.stability + 1),
        last_failure_at=lambda _: None,
        adapter=w.fsrs,
        days=DAYS,
        targets={POW: 0.5},
        credited_today=lambda k: small if k == POW else None,
    )
    (credit,) = result.credits
    assert credit.stability_before == memory.stability  # from the day's base, not on top
    skipped = partial_credit(
        CRIT,
        now=t + MIN,
        mode="shadow",
        skills=w.skills(),
        state_of=w.state,
        shadow_of=lambda _: None,
        last_failure_at=lambda _: None,
        adapter=w.fsrs,
        days=DAYS,
        targets={POW: 0.25},
        credited_today=lambda k: small if k == POW else None,
    )
    assert skipped.credits == []
    assert skipped.skipped[POW] == "credited today"


def logged(plain: float, credited: float, ok: bool, params_id: str = "fsrs6-default") -> Attempt:
    return Attempt(
        card_id="c",
        verdict="correct" if ok else "incorrect",
        rating=GOOD if ok else AGAIN,
        params_id=params_id,
        extra={"diagnosis": {"shadow": {"plain": plain, "credited": credited}}},
    )


def test_I9_switch_on_check_refuses_when_the_credited_log_loss_is_worse() -> None:
    # Outcomes match the plain prediction (0.8); the credited one (0.97) is overconfident.
    rows = [logged(0.8, 0.97, i % 5 != 0) for i in range(250)]
    switch = credit_switch(rows, "fsrs6-default")
    assert switch.reviews == 250
    assert some(switch.credited_log_loss) > some(switch.plain_log_loss)
    assert not switch.allowed
    # Credited predictions that win, on enough held-out reviews, allow it.
    # ENG-7 / ADR-0019 item 9: at least 800 held-out reviews (was 200).
    better = [logged(0.6, 0.8, i % 5 != 0) for i in range(900)]
    assert credit_switch(better, "fsrs6-default").allowed
    # Too few reviews, or reviews predicted with other parameters (not held out): refused.
    assert not credit_switch(better[:750], "fsrs6-default").allowed
    assert not credit_switch(better, "fit-abc").allowed


def test_I9_credit_on_runs_as_shadow_until_the_switch_on_check_passes() -> None:
    w = world(config=DiagnosisSettings(credit="on"))
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=10, days_ago=5, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=20, theta=2.0)
    before = w.states[POW].stability
    w.grade(answer(w, "crit.t3.0", at_day(0), correct=True))
    assert w.states[POW].stability == before  # the schedule keeps the plain stability
    assert {c.mode for c in w.credits} == {"shadow"}
    assert "held-out" in w.last.extra["diagnosis"]["credit_on"]


# ---------------------------------------------------------------- I3: Easy Days (Anki)
# Against Anki 26.09.3, rslib/src/scheduler/states/load_balancer.rs: EasyDay from a load
# share (:43-51), load_modifier Minimum 0.0001 / Reduced 0.5 / Normal 1.0 (:54-62),
# calculate_easy_days_modifiers (:324-357), an empty day weighs 1.0 (:425-426). The audit's
# "Reduced multiplies by 0.5" rule is not what Anki does (ADR-0014).


def test_I3_easy_days_modifiers_match_anki_calculate_easy_days_modifiers() -> None:
    # All Reduced, counts 10/2/4: total 16, load shares 1.5, other shares 1.0 per day.
    # Day 0: 10/0.5 = 20 > (16-10)/1.0 = 6 -> Minimum; day 1: 4 > 14 no; day 2: 8 > 12 no.
    reduced = ["reduced"] * 3
    assert easy_days_modifiers(reduced, [10, 2, 4]) == [0.0001, 1.0, 1.0]
    # Normal, Reduced, Minimum with 3 each: shares 1.5001, the Reduced day's threshold is
    # 6 / 1.0001 = 5.9994 < 3/0.5 = 6 -> Minimum.
    assert easy_days_modifiers(["normal", "reduced", "minimum"], [3, 3, 3]) == [
        1.0,
        0.0001,
        0.0001,
    ]
    # A lone Reduced day (no other share): threshold infinite -> Normal.
    assert easy_days_modifiers(["reduced"], [7]) == [1.0]
    # So all Reduced is not all Normal in Anki (the audit's acceptance line assumed it was).
    assert easy_days_modifiers(reduced, [10, 2, 4]) != easy_days_modifiers(
        ["normal"] * 3, [10, 2, 4]
    )
    # Settings: load percent 100 (or unset) Normal, 0 Minimum, anything else Reduced.
    assert [easy_day({"mon": 100, "tue": 0, "wed": 50}, d) for d in range(4)] == [
        "normal",
        "minimum",
        "reduced",
        "normal",
    ]
    # An empty day weighs 1.0 whatever its Easy Days setting.
    assert balance_weight(0, 10, 0.0001) == 1.0
    assert balance_weight(2, 10, 0.0001) == pytest.approx(0.0001 * 0.5**2.15 / 1000)


def test_I3_a_minimum_weekday_with_reviews_is_avoided_by_the_balancer() -> None:
    fsrs = FsrsAdapter()
    state = learned_state(20.0, at=at_day(0))
    base = fsrs.interval_days(20.0, 0.9, None)
    low, high = fsrs.fuzz_range(base)
    last = DAYS.day_of(at_day(0))
    load = {last + timedelta(days=d): 5 for d in range(low, high + 1)}  # evenly loaded
    plain = interval_of(balance(state, 0.9, fsrs, DAYS, load), 0.9, fsrs)
    weekday = WEEKDAYS[(last + timedelta(days=plain)).weekday()]
    moved = interval_of(balance(state, 0.9, fsrs, DAYS, load, {weekday: 0}), 0.9, fsrs)
    assert moved != plain
    assert WEEKDAYS[(last + timedelta(days=moved)).weekday()] != weekday
    assert low <= moved <= high
