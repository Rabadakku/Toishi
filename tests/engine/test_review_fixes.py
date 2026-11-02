"""Fixes from the full evidence review (ADR-0019), one test per defect, each failing before
its fix. Items are numbered as in the M7 engine brief."""

import random
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from core.engine import AnswerFacts as Facts
from core.engine import Engine, ProblemOutcome, TimingFacts
from core.engine.config import AGAIN, GOOD
from core.engine.histories import build_histories, training_items
from core.engine.level import Evidence, update_level
from core.engine.rating import AnswerFacts, RatingRules, SpeedFacts, rate
from core.model import Attempt, Skill
from core.storage import Storage
from core.storage.clock import FixedClock
from tests.engine.helpers import SKILL, Sim, at_day, card, learned_state, outcome, some
from tests.engine.test_service import answer, learn

# ---------------------------------------------------------------- 1. below the core band


def _targets(engine: Engine, *, retag: str | None = None) -> list[tuple[int, int]]:
    """(rating, delta) of every fit target of calc1.lim. `retag`: the last event's rules
    version is rewritten to this (a row graded under older rules)."""
    users = engine._storage.users
    events = users.review_events(target_id="calc1.lim")
    if retag is not None:
        events = [*events[:-1], replace(events[-1], rules_version=retag)]
    attempts = {a.id: a for a in users.attempts(include_voided=True) if a.id is not None}
    histories = build_histories(events, day_of=engine.days().day_of, attempts=attempts)
    return [i.reviews[-1] for i in training_items(histories)]


def _grown(storage: Storage, clock: FixedClock) -> Engine:
    """calc1.lim with a real log: a learning phase, then Good reviews up to S of about 45
    (core band: tier 3). Its two reviews are fit targets."""
    engine = Engine(storage)
    learn(engine, clock, "calc1.lim")
    for gap in (3, 9):
        clock.advance(days=gap)
        answer(engine, clock, "calc1.lim")
    assert some(some(storage.users.skill_state("calc1.lim")).stability) > 30
    assert len(_targets(engine)) == 2
    return engine


def test_1_below_band_success_writes_no_fsrs_event() -> None:
    # S = 40: the core band is tier 3; a tier 1 problem (Lighter set or a check) sits below.
    sim = Sim(learned_state(40.0, at=at_day(0)))
    before = sim.state
    lighter = sim.grade(outcome(at_day(30), tier=1, lighter_set=True))
    assert lighter.decision.rating is None
    assert lighter.answer.reviews == ()
    assert sim.state is not None
    assert before is not None
    assert sim.state.stability == before.stability
    assert sim.state.last_review_at == before.last_review_at
    check = sim.grade(outcome(at_day(31), tier=2))  # a below-band check pass, same rule
    assert check.answer.reviews == ()


def test_1_below_band_miss_is_again_but_never_a_fit_target(storage, clock) -> None:
    engine = _grown(storage, clock)
    clock.advance(days=20)
    pick = some(engine.pick_problem("calc1.lim", lighter_set=True))
    assert pick.card.tier in (1, 2)
    engine.grade(
        ProblemOutcome(
            card=pick.card,
            facts=Facts(correct=False),
            at=clock.now_ms(),
            timing=TimingFacts(solve_ms=30_000, active_ms=30_000, expected_chars=3),
            lighter_set=True,
        )
    )
    events = storage.users.review_events(target_id="calc1.lim")
    assert events[-1].rating == AGAIN  # the live schedule takes the Again ...
    assert some(storage.users.skill_state("calc1.lim")).lapses == 1
    assert len(_targets(engine)) == 2  # ... and the fitter sees it only as a prefix


def test_1_rules_version_moves_so_old_lighter_hard_rows_stop_training(storage, clock) -> None:
    # Rows graded by the old rules (a Lighter-set success rated Hard, a below-band check
    # pass rated Good, a slow pass rated Hard) stay prefixes under the new rules version.
    from core.engine.config import RULES_VERSION

    assert RULES_VERSION != "2026.11-r3"
    engine = _grown(storage, clock)
    clock.advance(days=20)
    answer(engine, clock, "calc1.lim")
    assert len(_targets(engine)) == 3
    assert len(_targets(engine, retag="2026.11-r3")) == 2


def test_1_exam_window_tier_3_on_a_young_skill_is_in_band() -> None:
    sim = Sim(learned_state(3.0, at=at_day(0)))
    sim.exam_window = True
    result = sim.grade(outcome(at_day(3), tier=3))
    assert result.effects.stage == "review"
    assert [e.rating for e in result.answer.reviews] == [GOOD]


# ---------------------------------------------------------------- 2. practice-test misses


EXAM4 = Skill(id=SKILL.id, name=SKILL.name, section_id=SKILL.section_id, exam_tier=4)


def test_2_practice_test_miss_at_exam_tier_4_is_again() -> None:
    for window in (True, False):
        sim = Sim(learned_state(10.0, at=at_day(0)), skill=EXAM4)
        sim.exam_window = window
        result = sim.grade(outcome(at_day(10), tier=4, correct=False, purpose="practice-test"))
        assert result.effects.stage == "review", window
        assert [e.rating for e in result.answer.reviews] == [AGAIN], window


def test_2_practice_test_miss_above_the_exam_tier_is_still_again() -> None:
    sim = Sim(learned_state(10.0, at=at_day(0)))  # exam tier 3
    result = sim.grade(outcome(at_day(10), tier=5, correct=False, purpose="practice-test"))
    assert [e.rating for e in result.answer.reviews] == [AGAIN]


# ---------------------------------------------------------------- 12. time never rates


def test_12_slow_correct_answer_is_good_with_a_slow_label() -> None:
    slow = SpeedFacts(
        speed_ms=300_000,
        baseline_ms=60_000,
        timed_successes=10,
        target_ms=90_000,
        recall=0.9,
        learned=True,
    )
    decision = rate(AnswerFacts(correct=True), slow, RatingRules())
    assert decision.rating == GOOD
    assert decision.slow


def _ev(n: int, speed_ms: int) -> Evidence:
    return Evidence(
        day=f"2026-09-{n + 1:02d}",
        tier=3,
        clean=True,
        rating=GOOD,
        speed_ms=speed_ms,
        form=f"card:{n}",
        recall=0.9,
        elapsed_days=1.0,
    )


def test_12_pace_feeds_level_only_with_an_exam_length() -> None:
    state = learned_state(10.0)
    log = [_ev(0, 500_000), _ev(1, 500_000)]
    state = replace(state, level_evidence={"log": [e.as_json() for e in log]})
    slow = _ev(2, 500_000)
    # No exam length: pace is off, two clean exam-tier days make Exam-level however slow.
    off = update_level(state, slow, exam_tier=3, targets={}, correct_in_a_row=3, pace=False)
    assert off.level == "exam"
    # An exam with a length: the slow median keeps it at Learned.
    on = update_level(state, slow, exam_tier=3, targets={3: 60_000}, correct_in_a_row=3)
    assert on.level == "learned"


def test_12_grading_turns_pace_off_without_an_exam_length() -> None:
    sim = Sim(learned_state(10.0, at=at_day(0)))
    assert sim.exam_problem_ms is None
    for n in (10, 11):
        sim.grade(outcome(at_day(n), tier=3, ref=card(3, cid=f"x{n}"), solve_ms=900_000))
    assert sim.state is not None
    assert sim.state.level == "exam"


# ---------------------------------------------------------------- 10. passed step checks


def test_10_a_passed_step_check_is_a_plain_again_for_level_and_leeches() -> None:
    from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, answer, seed, world

    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0, level="exam")
    lapses = []
    for n in range(4):  # four tapped misses within 30 days, each check passing
        t = at_day(6 * n)
        w.grade(answer(w, f"crit.t2.{n}", t, correct=False, choice="step", step=1))
        (check,) = w.pending()
        assert check.skill_id == POW
        w.grade(answer(w, some(check.card_id), t + 5 * 60_000, correct=True, check_of=check.id))
        lapses.append(w.states[CRIT].lapses)
        if n == 0:  # Level drops after the first: an integration error is a real miss
            assert w.states[CRIT].shaky or w.states[CRIT].level != "exam"
        # A success the next days brings it back to review, so the next miss lapses again.
        w.grade(answer(w, f"crit.t1.{n}", t + 2 * 86_400_000, correct=True))
    assert "leech_base" not in w.states[CRIT].level_evidence  # nothing was excused
    assert lapses == [1, 2, 3, 4]


# ---------------------------------------------------------------- 11. checks and the day


def test_11_a_check_never_repeats_a_card_served_this_study_day() -> None:
    from core.model import CardUser
    from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, answer, seed, world

    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    seed(w, CRIT, stability=20, days_ago=25, theta=1.0)
    t = at_day(0)
    pow_cards = [r.id for r in w.refs(POW) if r.kind == "problem" and r.tier <= 2]
    old = pow_cards[-1]  # served 10 days ago: not "fresh" either, but allowed today
    for cid in pow_cards:
        at = t - 10 * 86_400_000 if cid == old else t - 3_600_000
        w.card_users[cid] = CardUser(card_id=cid, last_seen_at=at)
    w.grade(answer(w, "crit.t2.0", t, correct=False, choice="step", step=1))
    (check,) = w.pending()
    assert check.skill_id == POW
    assert check.card_id == old
    # Every candidate served today: no check card is picked, and the miss stands.
    w2 = world()
    seed(w2, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w2, POW, stability=30, days_ago=3, theta=2.0)
    seed(w2, CRIT, stability=20, days_ago=25, theta=1.0)
    for cid in pow_cards:
        w2.card_users[cid] = CardUser(card_id=cid, last_seen_at=t - 3_600_000)
    w2.grade(answer(w2, "crit.t2.0", t, correct=False, choice="step", step=1))
    assert [c for c in w2.pending() if c.skill_id == POW] == []


def test_11_one_freshness_helper_serves_both_pickers() -> None:
    import inspect

    from core.engine import selection
    from core.engine.diagnosis import checks

    assert "def fresh" not in inspect.getsource(checks)
    assert "def fresh" not in inspect.getsource(selection.pick_problem)
    assert vars(checks)["is_fresh"] is selection.is_fresh


# ---------------------------------------------------------------- 13. holds that never settle


def _diagnosis_profile(tmp_path: Path, clock: FixedClock, *, without: str = "") -> Storage:
    """The diagnosis tests' pack (tests/engine/diagnosis/fixtures.py) in a real profile;
    `without`: a skill whose problems are left out (no pool yet)."""
    from core.model import Course, PackInfo, Section, Unit
    from core.storage import build_pack
    from core.storage.profiles import ProfilePaths
    from tests.engine.diagnosis.fixtures import SKILLS, cards

    pack = tmp_path / "c.db"
    sections = sorted({k.section_id for k in SKILLS if k.section_id})
    records: list[object] = [
        Course(id="c", title="Calc"),
        Unit(id="c.u", course_id="c", title="U"),
        *(Section(id=s, unit_id="c.u", title=s, ord=i) for i, s in enumerate(sections)),
        *SKILLS,
        *(c for c in cards() if c.skill_id != without),
    ]
    build_pack(pack, PackInfo(id="c", title="Calc", version="1"), records)  # type: ignore[arg-type]
    opened = Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=[pack], clock=clock, create=True)
    opened.users.set_setting("study.timezone", "America/New_York")
    return opened


@pytest.fixture
def dstorage(tmp_path: Path, clock: FixedClock) -> Iterator[Storage]:
    opened = _diagnosis_profile(tmp_path, clock)
    yield opened
    opened.close(backup=False)


def test_13_a_held_miss_whose_check_expires_settles_as_again_at_the_miss(
    dstorage: Storage, clock: FixedClock
) -> None:
    from core.engine.diagnosis import Diagnosis, hold_of
    from tests.engine.diagnosis.fixtures import CRIT
    from tests.engine.diagnosis.test_service import outcome as doutcome
    from tests.engine.diagnosis.test_service import seeded

    seeded(dstorage, clock)
    users = dstorage.users
    lapses = some(users.skill_state(CRIT)).lapses
    miss_at = clock.now_ms()
    Diagnosis(dstorage).grade(
        doutcome(dstorage, "crit.t2.0", miss_at, correct=False, choice="step", step=2)
    )
    assert hold_of(users.skill_state(CRIT)) is not None
    section = some(dstorage.packs.skill(CRIT)).section_id
    users.set_section_state(some(section), "off")  # nothing serves the skill or its check
    clock.advance(days=6)
    Diagnosis(dstorage).daily()
    assert hold_of(users.skill_state(CRIT)) is not None  # not yet: 7 days
    clock.advance(days=2)
    Diagnosis(dstorage).daily()
    state = some(users.skill_state(CRIT))
    assert hold_of(state) is None
    assert [(e.rating, e.at) for e in users.review_events(target_id=CRIT)] == [(AGAIN, miss_at)]
    assert state.lapses == lapses + 1  # a plain Again: it counts
    assert "leech_base" not in state.level_evidence
    assert all(c.status != "pending" for c in users.pending_checks(None))
    assert Engine(dstorage).recompute_memory().changed == ()  # the log replays to it


# ---------------------------------------------------------------- 14. frozen study days


def test_14_a_time_zone_change_never_moves_past_reviews(
    storage: Storage, clock: FixedClock
) -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ny = ZoneInfo("America/New_York")
    engine = Engine(storage)
    clock.set(datetime(2026, 9, 1, 22, 0, tzinfo=ny))  # Sep 2, 11:00 in Tokyo
    learn(engine, clock, "calc1.lim")
    clock.set(datetime(2026, 9, 4, 10, 0, tzinfo=ny))  # Sep 4, 23:00 in Tokyo
    answer(engine, clock, "calc1.lim")
    days_before = [s.day for h in engine.histories() for s in h.steps]
    storage.users.set_setting("study.timezone", "Asia/Tokyo")  # he travels
    assert [s.day for h in Engine(storage).histories() for s in h.steps] == days_before
    assert Engine(storage).recompute_memory().changed == ()  # replay equals the live state
    clock.set(datetime(2026, 9, 10, 12, 0, tzinfo=ny))
    answer(Engine(storage), clock, "calc1.lim")
    assert Engine(storage).recompute_memory().changed == ()


# ---------------------------------------------------------------- 5. atomic, guarded fitting


def _studied(storage: Storage, clock: FixedClock) -> Engine:
    engine = Engine(storage)
    for skill in ("calc1.alg", "calc1.lim"):
        learn(engine, clock, skill)
    for gap in (3, 9):
        clock.advance(days=gap)
        for skill in ("calc1.alg", "calc1.lim"):
            answer(engine, clock, skill)
    return engine


def _adopted(engine: Engine) -> object:
    from core.engine.fitting import Adoption
    from core.engine.param_sets import DEFAULTS as DEFAULT_PARAMETERS
    from core.engine.service import FitDecision

    current = engine.parameter_set("skills").parameters
    candidate = (*DEFAULT_PARAMETERS[:2], DEFAULT_PARAMETERS[2] * 2, *DEFAULT_PARAMETERS[3:])
    decision = Adoption(current=current, candidate=candidate, adopted=True, reason="t", items=9)
    return FitDecision(set_id="skills", decision=decision, items=9)


def test_5_adopting_a_fit_is_one_transaction(
    storage: Storage, clock: FixedClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = _studied(storage, clock)
    before = storage.users.skill_states()

    def killed(*_: object, **__: object) -> object:
        raise RuntimeError("the process ended between storing and recomputing")

    monkeypatch.setattr(Engine, "_rebuilt", killed)
    with pytest.raises(RuntimeError):
        engine.apply_fit(_adopted(engine))  # type: ignore[arg-type]
    monkeypatch.undo()
    assert Engine(storage).parameter_set("skills").source == "default"  # nothing half-applied
    assert storage.users.skill_states() == before


def test_5_startup_repairs_a_half_applied_fit(storage: Storage, clock: FixedClock) -> None:
    from core.engine.param_sets import stored_value
    from core.queue import StudyService

    engine = _studied(storage, clock)
    decision = _adopted(engine).decision  # type: ignore[attr-defined]
    # An older build quit after storing the set and before recomputing memory.
    engine._store_set("skills", stored_value(decision.candidate, at=clock.now_ms(), source="fit"))
    assert Engine(storage)._rebuilt("skills") != []  # memory is stale (read-only check) ...
    StudyService(storage).today()  # launch
    assert Engine(storage)._rebuilt("skills") == []  # ... and repaired at launch


class FakePanic(BaseException):
    """Stands in for pyo3_runtime.PanicException, which derives from BaseException."""


def test_5_a_fit_failure_is_persisted_and_grading_continues(
    storage: Storage, clock: FixedClock
) -> None:
    engine = _studied(storage, clock)

    def panics(items: object) -> tuple[float, ...]:
        raise FakePanic("Invalid FSRS item")

    report = engine.fit("skills", fit_fn=panics)
    assert not report.decision.adopted
    log = storage.users.get_setting("fsrs.fit_log.skills")
    assert log["failed"] is True
    assert "Invalid FSRS item" in log["reason"]
    clock.advance(days=1)
    answer(engine, clock, "calc1.lim")  # grading continues


def test_5_the_fitter_validates_items_and_turns_a_rust_panic_into_an_error() -> None:
    from core.engine.fitting import FitError, fit
    from core.engine.histories import Item

    bad = [Item(key=("skill", "k", 0), reviews=((3, 0), (3, 0)), at=i) for i in range(10)]
    with pytest.raises(FitError, match="delta"):
        fit(bad)


# ---------------------------------------------------------------- 6. the partial-credit switch


def _credit_rows(r: random.Random, n: int, scenario: str) -> list[Attempt]:
    rows: list[Attempt] = []
    for _ in range(n):
        true = min(0.99, max(0.5, r.gauss(0.85, 0.06)))
        if scenario == "neutral":  # credit as good as plain: independent noise, sd 0.03 each
            plain, credited = true + r.gauss(0, 0.03), true + r.gauss(0, 0.03)
        elif scenario == "biased":  # credit biased high by 0.03, plain exact
            plain, credited = true, true + 0.03
        else:  # "better": credit exact, plain off by 0.05
            plain, credited = true - 0.05, true
        ok = r.random() < true
        rows.append(
            Attempt(
                card_id="c",
                verdict="correct" if ok else "incorrect",
                rating=GOOD if ok else AGAIN,
                params_id="p",
                extra={"diagnosis": {"shadow": {"plain": plain, "credited": credited}}},
            )
        )
    return rows


def test_6_credit_switch_needs_a_paired_interval_with_a_margin_over_800_reviews() -> None:
    import random

    from core.engine.diagnosis.credit import credit_switch

    def rate_allowed(scenario: str, n: int, runs: int = 200) -> float:
        rng = random.Random(f"{scenario}{n}")  # noqa: S311 -- reproducible simulation
        return (
            sum(credit_switch(_credit_rows(rng, n, scenario), "p").allowed for _ in range(runs))
            / runs
        )

    assert rate_allowed("neutral", 900) <= 0.05  # the old rule: about half
    assert rate_allowed("biased", 900) <= 0.01
    assert rate_allowed("better", 900) >= 0.4  # real benefit still gets through
    assert rate_allowed("better", 700) == 0.0  # never under 800 held-out reviews


# ---------------------------------------------------------------- 7. the weak-spot finder

DAY = 86_400_000
NOW = 1000 + 400 * DAY


def _window(p: float, outcomes: list[bool]) -> list[Attempt]:
    """One skill's answers in the 30-day window, each expected to succeed with `p`."""
    import math

    from core.engine.config import TIER_DIFFICULTY

    theta = math.log(p / (1 - p)) + TIER_DIFFICULTY[2]
    return [
        Attempt(
            id=i + 1,
            card_id=f"c{i}",
            verdict="correct" if o else "incorrect",
            at=NOW - (i + 1) * (DAY // 2),
            final=True,
            tier=2,
            skill_id="k",
            study_day=f"2026-{9 + i // 28:02d}-{1 + i % 28:02d}",
            rating=GOOD if o else AGAIN,
            extra={"elo": {"theta": theta, "o": int(o)}, "diagnosis": {"tags": {"k": 1.0}}},
        )
        for i, o in enumerate(outcomes)
    ]


def _flagged(p: float, n: int, misses: int) -> bool:
    from core.engine.diagnosis.weakspots import skill_evidence

    found = skill_evidence(_window(p, [False] * misses + [True] * (n - misses)), now=NOW)
    return found["k"].flagged


def test_7_the_flag_uses_an_exact_binomial_tail() -> None:
    from math import comb

    # 8 misses of 20 at a predicted 0.8: z = -2.01 flagged it; the exact tail is 0.032.
    assert not _flagged(0.8, 20, 8)
    assert _flagged(0.8, 20, 9)  # tail 0.0100
    # A student the model describes is flagged at most 2.5% of evaluations, whatever n.
    for p in (0.7, 0.8, 0.85, 0.9):
        for n in range(5, 31):
            rate = sum(
                comb(n, m) * (1 - p) ** m * p ** (n - m) for m in range(n + 1) if _flagged(p, n, m)
            )
            assert rate <= 0.025, (p, n, rate)


def test_7_confirmation_is_sequential_and_capped_at_eight_problems() -> None:
    from core.engine.diagnosis.config import DIAG_SET_MAX
    from core.engine.diagnosis.weakspots import diagnostic_step
    from core.model import DiagnosticSet

    assert DIAG_SET_MAX == 8

    def run(outcomes: list[bool], cards: int = 8) -> tuple[str | None, int]:
        diag = DiagnosticSet(
            skill_id="k", created_at=0, card_ids=tuple(f"c{i}" for i in range(cards))
        )
        for i, missed in enumerate(outcomes):
            diag, decision = diagnostic_step(diag, missed=missed)
            if decision is not None:
                return decision, i + 1
        return None, len(outcomes)

    assert run([True, True]) == ("confirmed", 2)  # 2 misses in the first 2
    assert run([False] * 4) == ("cleared", 4)  # 4 correct, no miss
    assert run([True] + [False] * 6) == ("cleared", 7)  # 6 correct with 1 miss
    assert run([True, False, True, False, True]) == ("confirmed", 5)  # 3 misses, 2 correct
    assert run([True, False, False, True, False, False, False, True]) == ("confirmed", 8)
    assert run([True, False, False, False, True, False, False, False]) == ("cleared", 8)

    def p_confirm(p: float) -> float:
        total = 0.0
        for bits in range(2**8):
            seq = [bool(bits >> i & 1) for i in range(8)]  # True: a miss
            decision, used = run(seq)
            prob = 1.0
            for missed in seq[:used]:
                prob *= (1 - p) if missed else p
            if decision == "confirmed":
                total += prob / 2 ** (8 - used)  # each prefix is counted 2^(8-used) times
        return total

    assert p_confirm(0.85) <= 0.11  # the false-confirmation rate stays at the fixed set's
    assert p_confirm(0.60) >= 0.65  # a real gap is confirmed 67% of the time (was 35-53%)


# ---------------------------------------------------------------- 16. a changed answer key


def test_16_a_revision_that_changes_a_key_voids_old_attempts_and_rebuilds_memory(
    storage: Storage, clock: FixedClock, tmp_path: Path
) -> None:
    from core.model import Card, CardRevision
    from core.queue import StudyService
    from core.storage import build_pack
    from tests.engine.test_service import PACK, pack_records

    engine = _studied(storage, clock)
    users = storage.users
    lim = [a for a in users.attempts(skill_id="calc1.lim") if a.final and a.card_kind == "problem"]
    wrong_key = lim[-1].card_id  # graded under a key the next version fixes
    stale = [a.id for a in users.attempts() if a.card_id == wrong_key]
    kept = [a.id for a in users.attempts() if a.card_id != wrong_key]
    records: list[object] = []
    for r in pack_records():
        if isinstance(r, Card) and r.id == wrong_key:
            r = replace(r, rev=2, answer="2")
        records.append(r)
    records.append(CardRevision(card_id=wrong_key, rev=2, changed_at=1, answer_changed=True))
    newer = tmp_path / "calc1-v2.db"
    build_pack(newer, replace(PACK, version="2"), records)  # type: ignore[arg-type]
    storage.update_pack(newer)
    StudyService(storage).today()  # launch: PACK-14 runs on the revised pack
    voided = {a.id for a in users.attempts(include_voided=True) if a.voided_by is not None}
    assert set(stale) <= voided
    assert not voided & set(kept)
    assert Engine(storage)._rebuilt(None) == []  # memory equals a replay without them
    assert engine.recompute_memory().changed == ()


# ---------------------------------------------------------------- 17. prerequisites without a pool


def test_17_a_prerequisite_without_problems_gets_no_check_and_is_listed_unverified(
    tmp_path: Path, clock: FixedClock
) -> None:
    from core.engine.diagnosis import Diagnosis
    from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, seed
    from tests.engine.diagnosis.memory import MemoryWorld
    from tests.engine.diagnosis.test_service import outcome as doutcome

    storage = _diagnosis_profile(tmp_path, clock, without=ALG)  # no algebra pack yet
    try:
        from tests.engine.diagnosis.fixtures import SKILLS

        mem = MemoryWorld(SKILLS, [])
        now = clock.now_ms()
        seed(mem, ALG, stability=2, days_ago=20, at=now, theta=0.0)  # low recall
        seed(mem, POW, stability=30, days_ago=3, at=now, theta=2.0)
        seed(mem, CRIT, stability=20, days_ago=25, at=now, theta=1.0)
        storage.users.apply(list(mem.states.values()))
        diag = Diagnosis(storage)
        diag.grade(doutcome(storage, "crit.t2.0", now, correct=False, choice="step", step=1))
        (check,) = storage.users.pending_checks()
        assert check.skill_id == POW
        clock.advance(minutes=5)
        diag.grade(
            doutcome(storage, some(check.card_id), clock.now_ms(), correct=False, check_of=check.id)
        )
        assert [c for c in storage.users.pending_checks() if c.skill_id == ALG] == []
        (entry,) = diag.unverified_prerequisites()
        assert entry.skill_id == ALG
        assert entry.name == "Factor polynomials"
        assert POW in entry.needed_by
    finally:
        storage.close(backup=False)
