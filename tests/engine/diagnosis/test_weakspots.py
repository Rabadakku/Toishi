"""ENG-15 weak-spot finder (Algorithms A and B) and the possible-wrong-tier note."""

import math

import pytest

from core.engine.config import AGAIN, DAY_MS
from core.engine.diagnosis import diagnostic_step, find_weak_spots, skill_evidence, wrong_tier_flags
from core.model import Attempt, DiagnosticSet
from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, answer, seed, world
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.helpers import DAYS, at_day, some

T = at_day(0)
TAGS = {CRIT: 1.0, POW: 0.4, ALG: 0.4}


def att(
    i: int,
    *,
    at: int,
    ok: bool,
    card: str | None = None,
    skill: str = CRIT,
    theta: float = 1.0,
    tier: int = 2,
    blame: dict[str, float] | None = None,
    tags: dict[str, float] | None = None,
    template: str | None = None,
    **diag: object,
) -> Attempt:
    p = 1 / (1 + math.exp(-(theta - {1: -1.5, 2: -0.5, 3: 0.5, 4: 1.5}[tier])))
    d: dict[str, object] = {"tags": tags or TAGS, **diag}
    if blame is not None:
        d["blame"] = blame
    return Attempt(
        id=i,
        at=at,
        study_day=DAYS.day_of(at).isoformat(),
        card_id=card or f"crit.t{tier}.{i % 6}",
        skill_id=skill,
        tier=tier,
        template_id=template,
        verdict="correct" if ok else "incorrect",
        rating=3 if ok else 1,
        extra={
            "stage": "review",
            "elo": {
                "form": f"card:{i}",
                "p": p,
                "theta": theta,
                "d": 0,
                "d_after": 0,
                "o": int(ok),
            },
            "diagnosis": d,
        },
    )


ALG_TAP = {ALG: 0.6, CRIT: 0.3, POW: 0.1}


def alg_gap(n_miss: int = 8, n_ok: int = 4, days: int = 4) -> list[Attempt]:
    """Misses of well-predicted problems (p = 0.82) whose taps point at factoring."""
    out = []
    for i in range(n_miss):
        out.append(att(i, at=T - (i % days) * DAY_MS, ok=False, blame=ALG_TAP))
    for i in range(n_ok):
        out.append(att(100 + i, at=T - i * DAY_MS, ok=True))
    return out


def test_algorithm_a_flags_a_skill_clearly_worse_than_predicted() -> None:
    (flag,) = [f for f in find_weak_spots(alg_gap(), now=T) if f.skill_id == ALG]
    assert flag.z <= -2.0
    assert flag.evidence >= 5
    assert flag.misses >= 3
    assert flag.days >= 2


def test_z_uses_blame_weights_scaled_to_the_tag_mass() -> None:
    attempts = [att(1, at=T, ok=False, blame=ALG_TAP), att(2, at=T, ok=True)]
    ev = skill_evidence(attempts, now=T)[ALG]
    p = attempts[0].extra["elo"]["p"]
    w_miss, w_ok = 0.6 * 1.8, 0.4  # blame x (1 + 0.4 + 0.4); a success uses its tag weight
    r = w_miss * (0 - p) + w_ok * (1 - p)
    v = (w_miss**2 + w_ok**2) * p * (1 - p)
    assert ev.residual == pytest.approx(r)
    assert ev.z == pytest.approx(r / math.sqrt(v + 0.75))


@pytest.mark.parametrize(
    ("attempts", "why"),
    [
        (alg_gap(n_miss=3, n_ok=0), "evidence under five problems"),
        (
            [
                att(i, at=T - (i % 3) * DAY_MS, ok=False, blame=ALG_TAP, card="crit.t2.0")
                for i in range(10)
            ],
            "one problem",
        ),
        (alg_gap(days=1), "one day"),
    ],
)
def test_algorithm_a_needs_evidence_problems_and_days(attempts: list[Attempt], why: str) -> None:
    assert ALG not in {f.skill_id for f in find_weak_spots(attempts, now=T)}, why


def test_not_flagged_while_already_diagnosed_or_before_a_cleared_diagnosis() -> None:
    attempts = alg_gap()
    assert ALG not in {f.skill_id for f in find_weak_spots(attempts, now=T, busy=[ALG])}
    cut = {ALG: T + 1}
    assert ALG not in {f.skill_id for f in find_weak_spots(attempts, now=T, cutoff_of=cut.get)}


def test_accepted_slips_and_old_answers_carry_no_evidence() -> None:
    slips = [
        att(i, at=T - (i % 4) * DAY_MS, ok=False, blame=ALG_TAP, no_evidence=True)
        for i in range(10)
    ]
    assert skill_evidence(slips, now=T) == {}
    old = [att(i, at=T - 40 * DAY_MS, ok=False, blame=ALG_TAP) for i in range(10)]
    assert skill_evidence(old, now=T) == {}


# ---------------------------------------------------------------- Algorithm B


def flagged_world() -> MemoryWorld:
    w = world()
    seed(w, ALG, stability=30, days_ago=3, theta=1.5)
    seed(w, POW, stability=2, days_ago=20, theta=1.0)
    seed(w, CRIT, stability=20, days_ago=2, theta=1.0)
    w.attempts.extend(alg_gap())
    return w


def test_a_flag_schedules_a_diagnostic_set_of_fresh_single_skill_problems() -> None:
    w = flagged_world()
    report = w.daily(T + 3600_000)
    (spot,) = [s for s in report.weak_spots if s.skill_id == ALG]
    (diag,) = [d for d in report.sets if d.skill_id == ALG]
    assert spot.skill_id == ALG
    assert diag.weak_spot_id == spot.id
    assert 3 <= len(diag.card_ids) <= 8  # ENG-15 / ADR-0019: a sequential set, at most 8
    cards = [some(w.card(c)) for c in diag.card_ids]
    assert all(c.skill_id == ALG and c.uses == () and c.tier <= 3 for c in cards)
    assert len({c.template_id for c in cards}) == 3  # every form at or below level first
    checks = [c for c in w.pending() if c.kind == "diagnostic" and c.skill_id == ALG]
    assert sorted(some(c.card_id) for c in checks) == sorted(diag.card_ids)
    assert all(c.attempt_id is None and c.not_before_at is not None for c in checks)


def serve_set(w: MemoryWorld, results: list[bool], at: int) -> None:
    for i, ok in enumerate(results):
        checks = sorted(
            (c for c in w.pending() if c.kind == "diagnostic" and c.skill_id == ALG),
            key=lambda c: c.id or 0,
        )
        if not checks:
            return
        check = checks[0]
        w.grade(answer(w, some(check.card_id), at + i * 60_000, correct=ok, check_of=check.id))


def test_the_sequential_test_confirms_the_gap_lapse_then_prerequisite_checks() -> None:
    # ADR-0019 item 9: the SPRT confirms on 3 misses with 1 success (was 2 misses of 3-4).
    w = flagged_world()
    w.daily(T + 3600_000)
    before = len(w.events_for(ALG))
    serve_set(w, [False, True, False, False], T + 2 * 3600_000)
    (diag,) = [d for d in w.sets.values() if d.skill_id == ALG]
    assert diag.status == "confirmed"
    assert diag.misses == 3
    assert diag.done == 4
    assert w.spots[some(diag.weak_spot_id)].status == "confirmed"
    events = w.events_for(ALG)[before:]
    assert [e.rating for e in events] == [AGAIN]  # set problems themselves are not rated
    assert [c for c in w.pending(ALG) if c.kind == "diagnostic"] == []  # the rest cancelled


def test_the_sequential_test_clears_the_flag_and_its_residuals() -> None:
    # ADR-0019 item 9: the SPRT clears after 4 successes with no miss.
    w = flagged_world()
    w.daily(T + 3600_000)
    serve_set(w, [True, True, True, True], T + 2 * 3600_000)
    (diag,) = [d for d in w.sets.values() if d.skill_id == ALG]
    assert diag.status == "cleared"
    assert w.spots[some(diag.weak_spot_id)].status == "cleared"
    assert w.events_for(ALG) == []
    again = w.daily(T + DAY_MS)
    assert ALG not in {f.skill_id for f in again.flagged}


def test_diagnostic_step_decides_early() -> None:
    diag = DiagnosticSet(skill_id=ALG, created_at=0, card_ids=("a", "b", "c"))
    diag, decided = diagnostic_step(diag, missed=True)
    assert decided is None
    assert diag.status == "active"
    _, decided = diagnostic_step(diag, missed=True)
    assert decided == "confirmed"
    diag = DiagnosticSet(skill_id=ALG, created_at=0, card_ids=("a", "b", "c"), done=1)
    _, decided = diagnostic_step(diag, missed=False)
    assert decided == "cleared"  # 0 misses, 1 left: two can no longer be reached


def test_at_most_two_diagnostic_sets_a_week() -> None:
    w = flagged_world()
    for skill in (POW, CRIT):  # two more flagged skills
        tags = {skill: 1.0}
        w.attempts.extend(
            att(
                500 + i + 50 * len(skill),
                at=T - (i % 4) * DAY_MS,
                ok=False,
                skill=skill,
                tags=tags,
                card=f"{skill}.t2.{i % 6}",
            )
            for i in range(9)
        )
    report = w.daily(T + 3600_000)
    assert len(report.flagged) == 3
    assert len(report.sets) == 2
    assert w.daily(T + 2 * DAY_MS).sets == []  # still the same week
    assert len(w.daily(T + 8 * DAY_MS).sets) <= 2


# ---------------------------------------------------------------- possible wrong tier


def test_a_run_of_surprises_on_a_template_raises_a_wrong_tier_note() -> None:
    attempts = [
        att(i, at=T - i * DAY_MS, ok=False, theta=2.5, template="crit.t2") for i in range(3)
    ]
    (note,) = wrong_tier_flags(attempts, now=T)
    assert (note.family, note.direction) == ("template:crit.t2", "harder-than-tier")
    easy = [att(i, at=T - i * DAY_MS, ok=True, theta=-2.5, template="crit.t2") for i in range(3)]
    assert wrong_tier_flags(easy, now=T)[0].direction == "easier-than-tier"


def test_misses_traced_to_a_confirmed_gap_are_not_tier_surprises() -> None:
    misses = [att(i, at=T - i * DAY_MS, ok=False, theta=2.5, template="crit.t2") for i in range(3)]
    check = att(
        99,
        at=T,
        ok=False,
        skill=ALG,
        card="c.alg.t1.0",
        resolved={"trigger": 1, "confirmed": True, "kind": "step", "choice": "step"},
    )
    assert wrong_tier_flags([*misses, check], now=T) == []


def test_wrong_tier_note_never_changes_a_tier() -> None:
    w = world()
    seed(w, CRIT, stability=20, days_ago=25, theta=3.0)
    seed(w, ALG, stability=30, days_ago=3, theta=2.0)
    seed(w, POW, stability=30, days_ago=3, theta=2.0)
    tiers = {c.id: c.tier for c in w._cards.values()}
    for i in range(3):
        w.grade(answer(w, f"crit.t2.{i}", T + i * DAY_MS, correct=False, choice="other-method"))
    assert wrong_tier_flags(w.attempts, now=T + 3 * DAY_MS)
    assert {c.id: c.tier for c in w._cards.values()} == tiers
