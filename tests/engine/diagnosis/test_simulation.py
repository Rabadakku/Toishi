"""Simulated learners: hidden gaps are found within a few problems, slips stay slips, and a
student the model describes is rarely flagged (ENG-15's false-positive budget)."""

import statistics

from core.engine.diagnosis.config import FALSE_POSITIVE_BUDGET
from tests.engine.diagnosis.fixtures import ALG, CRIT, MC, POW, PROD, QUOT, seed, world
from tests.engine.diagnosis.memory import MemoryWorld
from tests.engine.diagnosis.sim import Learner, Run, agains, rng


def engine_view() -> MemoryWorld:
    """What the engine believes: every skill learned and fine; nothing about the gaps."""
    w = world()
    for k in (ALG, POW):
        seed(w, k, stability=60, days_ago=4, theta=2.0)
    seed(w, CRIT, stability=10, days_ago=10, theta=1.0)
    for k in (PROD, QUOT):
        seed(w, k, stability=15, days_ago=10, theta=1.5)
    seed(w, MC, stability=10, days_ago=10, theta=1.0)
    return w


def problems_until(learner: Learner, focus: list[str], gap: str, seed_: int) -> int | None:
    w = engine_view()
    run = Run(w, learner, focus=focus, rng=rng(100 + seed_))
    return run.until(lambda: agains(w, gap) > 0, max_days=20)


def test_hidden_prerequisite_gap_is_found_within_a_few_problems() -> None:
    # Factoring succeeds half the time; the engine thinks it is solid (recall ~0.98).
    found = [
        problems_until(Learner(ability={ALG: 0.5}, rng=rng(s)), [CRIT], ALG, s) for s in range(12)
    ]
    assert all(n is not None and n <= 40 for n in found), found
    assert statistics.median(n or 99 for n in found) <= 8, found


def test_method_choice_gap_is_found_within_a_few_problems() -> None:
    # Chooses the right rule 40% of the time uncued; executes either rule well.
    found = [
        problems_until(Learner(choose=0.4, rng=rng(s)), [PROD, QUOT], MC, s) for s in range(12)
    ]
    assert all(n is not None and n <= 30 for n in found), found
    assert statistics.median(n or 99 for n in found) <= 8, found


def test_a_student_who_only_slips_gets_again_and_only_capped_slips_are_excused() -> None:
    # ADR-0019 item 4 (amends ADR-0014): only a slip or misread within its 30-day cap is
    # excused; a passed step check is an integration error that counts for Level and leeches.
    # So a student who slips one problem in eight lapses for real beyond the cap (he may leech).
    misses = lapses = accepted = confirmed = 0
    for s in range(4):
        w = engine_view()
        learner = Learner(default=0.99, slip=0.12, honesty=0.8, rng=rng(s))
        Run(w, learner, focus=[CRIT], per_day=3, rng=rng(100 + s)).until(lambda: False, max_days=45)
        crit = [a for a in w.attempts if a.skill_id == CRIT]
        misses += sum(1 for a in crit if not a.extra["elo"]["o"])
        lapses += agains(w, CRIT)
        run_accepted = sum(
            1 for a in crit if a.extra.get("diagnosis", {}).get("slip") == "accepted"
        )
        assert run_accepted <= 2  # once per skill per 30 days, over 45 days
        accepted += run_accepted
        confirmed += sum(1 for spot in w.spots.values() if spot.status == "confirmed")
    assert misses >= 40  # about one problem in eight slips
    # ADR-0014: every miss is an Again for FSRS (a wrong answer is never a pass) ...
    assert lapses >= 0.6 * misses, (lapses, misses)
    # ... and the cap still excuses some slips.
    assert accepted >= 1
    # Honest misses lower stability and so the core band, which moves the model's
    # expectations; a chance confirmation of a 4-problem set stays rare.
    assert confirmed <= 1


def test_a_student_the_model_describes_stays_within_the_false_positive_budget() -> None:
    focus = [CRIT, PROD, QUOT, POW, ALG]
    flags = skill_months = 0
    for s in range(4):
        w = world()
        for k in focus:
            seed(w, k, stability=15, days_ago=10, theta=1.0)
        learner = Learner(calibrated=True, honesty=0.6, rng=rng(s))
        run = Run(w, learner, focus=focus, per_day=3, rng=rng(50 + s))
        run.until(lambda: False, max_days=60)
        flags += run.weak_spots
        skill_months += len(focus) * 2
    assert flags / skill_months <= FALSE_POSITIVE_BUDGET, (flags, skill_months)


def flagged_after(seed_: int) -> int | None:
    w = engine_view()
    learner = Learner(ability={ALG: 0.5}, honesty=0.2, rng=rng(seed_))
    run = Run(w, learner, focus=[CRIT], rng=rng(100 + seed_))
    return run.until(lambda: any(x.skill_id == ALG for x in w.spots.values()), max_days=30)


def test_the_finder_flags_a_gap_even_when_taps_mislead() -> None:
    found = [flagged_after(s) for s in range(5)]
    assert sum(n is not None and n <= 60 for n in found) >= 4, found
