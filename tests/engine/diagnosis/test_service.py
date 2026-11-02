"""Diagnosis through Storage: one transaction per answer, undo, the daily run, reasons."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from core.engine import ProblemOutcome
from core.engine.config import AGAIN, DAY_MS
from core.engine.diagnosis import Diagnosis, hold_of
from core.engine.diagnosis.checks import check_reason, step_reason
from core.engine.histories import FIT_EVENTS_KEY, build_histories, last_histories
from core.model import Attempt, Course, GradedAnswer, PackInfo, PendingCheck, Section, Unit
from core.storage import Storage, build_pack
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, SKILLS, answer, cards, seed
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.diagnosis.test_weakspots import alg_gap
from tests.engine.helpers import some

NY = ZoneInfo("America/New_York")


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 9, 1, 12, tzinfo=NY), tz=NY)


@pytest.fixture
def storage(tmp_path: Path, clock: FixedClock) -> Iterator[Storage]:
    pack = tmp_path / "c.db"
    sections = sorted({k.section_id for k in SKILLS if k.section_id})
    records: list[object] = [
        Course(id="c", title="Calc"),
        Unit(id="c.u", course_id="c", title="U"),
        *(Section(id=s, unit_id="c.u", title=s, ord=i) for i, s in enumerate(sections)),
        *SKILLS,
        *cards(),
    ]
    build_pack(pack, PackInfo(id="c", title="Calc", version="1"), records)  # type: ignore[arg-type]
    opened = Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=[pack], clock=clock, create=True)
    opened.users.set_setting("study.timezone", "America/New_York")
    yield opened
    opened.close(backup=False)


def seeded(storage: Storage, clock: FixedClock) -> None:
    mem = MemoryWorld(SKILLS, [])
    now = clock.now_ms()
    seed(mem, ALG, stability=30, days_ago=3, at=now, theta=2.0)
    seed(mem, POW, stability=30, days_ago=3, at=now, theta=2.0)
    seed(mem, CRIT, stability=20, days_ago=25, at=now, theta=1.0)
    storage.users.apply(list(mem.states.values()))


def outcome(storage: Storage, card: str, at: int, **kw: object) -> ProblemOutcome:
    mem = MemoryWorld(SKILLS, [some(storage.packs.card(card))])
    return answer(mem, card, at, **kw)  # type: ignore[arg-type]


def test_a_tapped_miss_commits_its_check_with_the_attempt_and_undo_removes_both(
    storage: Storage, clock: FixedClock
) -> None:
    seeded(storage, clock)
    diag = Diagnosis(storage)
    rec = diag.grade(
        outcome(storage, "crit.t2.0", clock.now_ms(), correct=False, choice="step", step=2)
    )
    (check,) = storage.users.pending_checks()
    assert check.attempt_id == rec.attempt.id
    assert check.skill_id == ALG
    assert check.kind == "step"
    assert check.card_id is not None
    assert check.after_items == 3
    assert "Factor" in diag.reason(check)
    assert diag.reason(check) == check.reason  # stored on the check ...
    assert "reason" not in rec.attempt.extra["diagnosis"]["checks"][0]  # ... not in extra
    assert hold_of(storage.users.skill_state(CRIT)) is not None
    assert storage.users.review_events(target_id=CRIT) == []
    storage.users.undo_last_answer()
    assert storage.users.pending_checks() == []
    assert hold_of(storage.users.skill_state(CRIT)) is None


def test_serving_the_check_settles_the_problem_skill(storage: Storage, clock: FixedClock) -> None:
    seeded(storage, clock)
    diag = Diagnosis(storage)
    engine = diag.engine()  # one Engine for the whole session: each answer reads fresh rows
    miss_at = clock.now_ms()
    engine.grade(outcome(storage, "crit.t2.0", miss_at, correct=False, choice="step", step=2))
    (check,) = storage.users.pending_checks()
    clock.advance(minutes=5)
    rec = engine.grade(
        outcome(storage, some(check.card_id), clock.now_ms(), correct=True, check_of=check.id)
    )
    assert rec.attempt.check_of == check.id
    resolved = storage.users.pending_checks(None)[0]
    assert resolved.status == "passed"
    assert resolved.resolved_by == rec.attempt.id
    (event,) = storage.users.review_events(target_id=CRIT)
    assert (event.rating, event.at, event.attempt_id) == (AGAIN, miss_at, rec.attempt.id)
    assert diag.tap_calibration().taps == 1


def test_a_held_miss_settled_into_a_leech_stays_out_of_the_repair_phase(
    storage: Storage, clock: FixedClock
) -> None:
    """C3 (found by DEV-8): the skill is served again before its check, so its held miss
    settles as Again at the miss's time, which makes it a leech; the answer is graded in the
    new learning phase. The settled Again belongs to the old card, as an ordinary lapse
    would: the repaired card is built from the new phase alone, and so is its replay."""
    seeded(storage, clock)
    row = storage.users.skill_state(CRIT)
    assert row is not None
    storage.users.apply([replace(row, lapses=7)])  # one lapse short of a leech (8)
    engine = Diagnosis(storage).engine()
    miss_at = clock.now_ms()
    engine.grade(outcome(storage, "crit.t2.0", miss_at, correct=False, choice="step", step=2))
    assert hold_of(storage.users.skill_state(CRIT)) is not None
    clock.advance(minutes=5)
    rec = engine.grade(outcome(storage, "crit.t2.1", clock.now_ms(), correct=False))
    assert rec.result.effects.stage == "learning"  # the settled Again made it a leech
    (settled,) = storage.users.review_events(target_id=CRIT)
    assert (settled.rating, settled.at, settled.attempt_id) == (AGAIN, miss_at, rec.attempt.id)
    (note,) = rec.attempt.extra[FIT_EVENTS_KEY]
    assert (note["kind"], note["block_start"]) == ("settled", False)
    for _ in range(3):  # three clean answers pass the repair phase
        clock.advance(minutes=3)
        engine.grade(outcome(storage, "crit.t1.0", clock.now_ms(), correct=True))
    assert storage.users.skill_state(CRIT).fsrs_state == 2  # type: ignore[union-attr]
    phase = [("learning", AGAIN)] + [("learning", 3)] * 3  # the settling answer's own miss first
    key = ("skill", CRIT, 0)
    assert [(s.kind, s.rating) for s in last_histories(engine.histories())[key].steps] == phase
    # Rows without annotations are inferred the same way.
    bare = {
        a.id: replace(a, extra={k: v for k, v in a.extra.items() if k != FIT_EVENTS_KEY})
        for a in storage.users.attempts()
        if a.id is not None
    }
    events = storage.users.review_events(target_id=CRIT)
    inferred = build_histories(events, day_of=engine.days().day_of, attempts=bare)
    assert [(s.kind, s.rating) for s in last_histories(inferred)[key].steps] == phase
    assert engine.recompute_memory().changed == ()


def test_daily_run_writes_weak_spot_set_and_checks_linked(
    storage: Storage, clock: FixedClock
) -> None:
    seeded(storage, clock)
    now = clock.now_ms()
    for a in alg_gap():
        shifted = replace(a, id=None, at=a.at - (0 if a.at < now else 3600_000), study_day=None)
        storage.users.record_answer(GradedAnswer(attempt=shifted))
    report = Diagnosis(storage).daily(now + 3600_000)
    spot = next(s for s in report.weak_spots if s.skill_id == ALG)
    diag_set = next(d for d in report.sets if d.skill_id == ALG)
    assert diag_set.weak_spot_id == spot.id
    assert spot.id is not None
    stored = [c for c in storage.users.pending_checks() if c.skill_id == ALG]
    assert {c.card_id for c in stored} == set(diag_set.card_ids)
    assert all(c.kind == "diagnostic" for c in stored)
    reason = Diagnosis(storage).reason(stored[0])
    assert "Factor polynomials" in reason
    assert "misses" in reason
    assert {c.reason for c in stored} == {reason}  # stored with each check (schema v2)


def test_due_note_explains_a_pulled_forward_review(storage: Storage, clock: FixedClock) -> None:
    seeded(storage, clock)
    mem = MemoryWorld(SKILLS, [])
    now = clock.now_ms()
    seed(mem, POW, stability=10, days_ago=12, at=now, theta=0.5)
    seed(mem, CRIT, stability=40, days_ago=1, at=now, theta=2.0)
    storage.users.apply([mem.states[POW], mem.states[CRIT]])
    diag = Diagnosis(storage)
    diag.grade(outcome(storage, "c.pow.t2.0", now, correct=False, choice="cant-tell"))
    clock.advance(days=2)
    due = {d.skill_id: d for d in diag.engine().due_skills()}
    assert CRIT in due
    assert "Power rule" in (due[CRIT].note or "")


def test_attempt_rows_carry_the_diagnosis_for_the_finder(
    storage: Storage, clock: FixedClock
) -> None:
    seeded(storage, clock)
    rec = Diagnosis(storage).grade(
        outcome(storage, "crit.t2.0", clock.now_ms(), correct=False, choice="step", step=1)
    )
    stored: Attempt = some(storage.users.attempt(some(rec.attempt.id)))
    d = stored.extra["diagnosis"]
    assert d["tags"] == {CRIT: 1.0, POW: 0.4, ALG: 0.4}
    assert d["blame"][POW] == pytest.approx(0.6)
    assert d["choice"] == "step"
    assert stored.error_choice == "step"
    assert stored.error_step == 1
    assert stored.at <= clock.now_ms() < stored.at + DAY_MS


def test_check_reason_reads_the_column_then_the_v1_extra_then_composes() -> None:
    skills = {k.id: k for k in SKILLS}
    legacy = {"diagnosis": {"checks": [{"skill": ALG, "kind": "step", "reason": "v1 text"}]}}
    asked = Attempt(id=1, card_id="crit.t2.0", skill_id=CRIT, verdict="incorrect", extra=legacy)
    check = PendingCheck(skill_id=ALG, kind="step", attempt_id=1)
    assert check_reason(replace(check, reason="stored"), skills=skills, attempt=asked) == "stored"
    assert check_reason(check, skills=skills, attempt=asked) == "v1 text"  # before v2
    assert check_reason(check, skills=skills, attempt=replace(asked, extra={})) == step_reason(
        skills, CRIT, ALG, None
    )
