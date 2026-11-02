"""Certification from direct evidence (design 3.7) and representative problems (3.8)."""

from datetime import date, timedelta

import pytest

from core.plan.certify import (
    Certifier,
    first_try_success,
    model_priors,
    readiness,
    recency_weight,
    representatives,
    sitting_results,
)
from core.plan.protocol import Forecast
from core.plan.types import CourseSettings
from tests.plan.fakes import FakeState
from tests.plan.helpers import Log, at, course, fake, pool, problem, skill

D0 = date(2026, 9, 1)
T2 = problem("s.t2.01", "s", 2)  # T* = 0.5 + 1.5*2 = 3.5 min
T3 = problem("s.t3.01", "s", 3)  # T* = 3.5 min
T4 = problem("s.t4.01", "s", 4)  # T* = 0.5 + 3 + 1.5 = 5.0 min


def day(n: int) -> date:
    return D0 + timedelta(days=n)


def cert(log: Log, today: date, prior: float = 0.9, **kw: object) -> Certifier:
    priors = {("s", t): prior for t in range(1, 6)}
    return Certifier(log.items, today=today, priors=priors, **kw)  # type: ignore[arg-type]


def test_recency_weight_halves_every_30_days() -> None:
    assert recency_weight(0) == 1.0
    assert recency_weight(30) == pytest.approx(0.5)
    assert recency_weight(60) == pytest.approx(0.25)


def test_first_try_success_is_accuracy_only() -> None:
    """Design v1.3: a correct, unaided first try is a success whatever its time (slow or
    untimed); wrong or aided ones fail. `timed` no longer changes anything."""
    log = Log()
    ok = log.add(T3, D0, True, minutes=3.5)
    slow = log.add(T3, D0, True, minutes=4.0)
    untimed = log.add(T3, D0, True)
    wrong = log.add(T3, D0, False)
    aided = log.add(T3, D0, True, minutes=1.0, aided=True)
    tries = (ok, slow, untimed, wrong, aided)
    expected = [True, True, True, False, False]
    assert [first_try_success(o) for o in tries] == expected
    assert [first_try_success(o, timed=True) for o in tries] == expected


def test_posterior_counts_recency_weighted_evidence_on_a_kappa0_4_prior() -> None:
    """Prior 0.5 -> Beta(2, 2). Three successes today: Beta(5, 2), mean 5/7, n_eff 3.
    One success 30 days before the query at prior 0.9: Beta(3.6 + 0.5, 0.4), mean
    4.1/4.5 = 0.911, n_eff 0.5."""
    log = Log()
    log.many(T2, D0, "111")
    post = cert(log, D0, prior=0.5).posterior("s", 2)
    assert (post.alpha, post.beta, post.n_eff) == pytest.approx((5.0, 2.0, 3.0))
    assert post.mean == pytest.approx(5 / 7)
    log = Log()
    log.add(T2, D0, True)
    post = cert(log, day(30)).posterior("s", 2)
    assert post.n_eff == pytest.approx(0.5)
    assert post.mean == pytest.approx(4.1 / 4.5)


def test_add_matches_a_rebuild_with_the_longer_log() -> None:
    """The session adds each first try as it is graded. Queries in between fill the caches;
    add refreshes exactly what the new try changes, so every answer equals a rebuild."""
    log = Log()
    other = problem("o.t2.01", "o", 2)
    plan = [(T2, True), (T3, True), (other, False), (T2, False), (T2, True), (T3, True)]
    plan += [(T2, True), (other, True), (T3, False), (T2, True)]
    for n, (p, ok) in enumerate(plan):
        log.add(p, day(n // 4), ok, minutes=2.0)
    priors = {(s, t): 0.9 for s in ("s", "o") for t in range(1, 6)}
    tiers = {"s": {2, 3}, "o": {2}}
    keys = [("s", 2), ("s", 3), ("o", 2)]
    grown = Certifier(log.items[:2], today=day(2), priors=priors, tiers=tiers)
    for obs in log.items[2:]:
        for s, t in keys:
            grown.state(s, t)
            grown.state(s, t, day(1), before=True)
        grown.add(obs)
    full = Certifier(log.items, today=day(2), priors=priors, tiers=tiers)
    assert grown.observations == full.observations
    for s, t in keys:
        assert grown.state(s, t) == full.state(s, t)
        assert grown.state(s, t, day(1), before=True) == full.state(s, t, day(1), before=True)
    assert [grown.level(s) for s in ("s", "o")] == [full.level(s) for s in ("s", "o")]
    with pytest.raises(ValueError, match="time order"):
        grown.add(log.items[0])


def test_add_refreshes_the_sitting_results() -> None:
    """A sitting graded one problem at a time: after the first, the sitting is void (one
    problem) and nothing is certified; after the second, it passes and M2's tier certifies,
    exactly as a rebuild would say."""
    log = Log()
    log.many(T3, D0, "11", minutes=3.0)
    first = log.add(T3B, day(1), True, minutes=3.0, role="sitting")
    second = log.add(T3C, day(1), True, minutes=3.0, role="sitting")
    c = cert(Log(), day(1))
    for obs in log.items[:2]:
        c.add(obs)
    assert not c.certified("s", 3)
    c.add(first)
    assert [r.outcome for r in c.sittings("s")] == ["void"]
    assert not c.certified("s", 3)
    c.add(second)
    assert [r.outcome for r in c.sittings("s")] == ["pass"]
    assert c.certified("s", 3)
    assert c.state("s", 3) == cert(log, day(1)).state("s", 3)


def test_evidence_is_per_main_skill_and_tier_and_ignores_later_days() -> None:
    log = Log()
    log.add(problem("o.t2.01", "o", 2, uses=["s"]), D0, True)  # another skill's problem
    log.add(T3, D0, True, minutes=1.0)  # another tier
    log.add(T2, day(5), True)  # after the query day
    assert cert(log, D0).posterior("s", 2).n_eff == 0.0


def test_m1_needs_three_effective_observations_and_the_target_mean() -> None:
    """Prior 0.9 (Beta(3.6, 0.4)). Two successes: mean 5.6/6 = 0.933 but n_eff 2 < 3.
    Three: mean 6.6/7 = 0.943, n_eff 3 -> certified. At prior 0.5, (2 + n)/(4 + n) >= 0.9
    needs n >= 16 successes: 15 give 17/19 = 0.895."""
    log = Log()
    log.many(T2, D0, "11")
    assert not cert(log, D0).certified("s", 2)
    log.add(T2, D0, True)
    assert cert(log, D0).certified("s", 2)
    log = Log()
    log.many(T2, D0, "1" * 15)
    assert not cert(log, D0, prior=0.5).certified("s", 2)
    log.add(T2, D0, True)
    assert cert(log, D0, prior=0.5).certified("s", 2)


T3B = problem("s.t3.02", "s", 3)  # T* 3.5 min, another tier-3 problem
T3C = problem("s.t3.03", "s", 3)


def test_m2_m3_certify_only_through_a_passed_sitting() -> None:
    """Wave 2: practice never certifies M2 or M3. Tier 3 (the M2/M3 rule by default), prior
    0.9: eight correct practice tries give the accuracy posterior (3.6 + 8)/12 = 0.967, but no
    certification. A sitting on day 1, two problems right in 3.0 + 3.9 = 6.9 <= 7.0 minutes,
    certifies on that day; the untimed (M1) rule on the same evidence needs no sitting."""
    log = Log()
    log.many(T3, D0, "11111111", minutes=1.0)
    c = cert(log, D0)
    assert c.posterior("s", 3).mean == pytest.approx(11.6 / 12)
    assert not c.certified("s", 3)
    assert c.certified("s", 3, timed=False)
    log.add(T3B, day(1), True, minutes=3.0, role="sitting")
    log.add(T3C, day(1), True, minutes=3.9, role="sitting")
    c = cert(log, day(1))
    assert c.certified("s", 3)
    assert c.state("s", 3).since == day(1)
    assert not c.certified("s", 3, day(0))


def test_sitting_outcomes_pass_fail_and_void() -> None:
    """A skill's sitting passes when every problem is right, unaided, and the summed valid
    time is within the summed T* (7.0 minutes for two tier-3 problems): one problem may run
    over its own T* (4.5 + 2.0). A wrong answer, an aided one or a slow block (4.0 + 3.5 =
    7.5) fails; an unknown time with every answer right, or a single answered problem, is
    void."""

    def outcome(*tries: tuple[bool, float | None], aided: bool = False) -> str:
        log = Log()
        for (ok, minutes), p in zip(tries, (T3B, T3C), strict=False):
            obs = log.add(p, D0, ok, minutes=minutes, role="sitting", aided=aided)
            assert obs.role == "sitting"
        found = Certifier(log.items, today=D0).sittings("s")
        assert len(found) == 1
        return found[0].outcome

    assert outcome((True, 4.5), (True, 2.0)) == "pass"
    assert outcome((True, 4.0), (True, 3.5)) == "fail"
    assert outcome((True, 1.0), (False, None)) == "fail"
    assert outcome((True, 1.0), (True, 1.0), aided=True) == "fail"
    assert outcome((True, None), (True, 1.0)) == "void"
    assert outcome((True, 1.0)) == "void"
    results = sitting_results("s", 3, [])
    assert results == ()


def test_a_sitting_pass_under_the_revocation_line_does_not_certify() -> None:
    """Prior 0.9 (Beta(3.6, 0.4)) and six practice misses at tier 3: (3.6 + 0)/10 = 0.36.
    A passed two-problem sitting brings it to 5.6/12 = 0.467, still below 0.8: the pass
    would be revoked at once, so it does not certify (revocation is unchanged)."""
    log = Log()
    log.many(T3, D0, "000000")
    log.add(T3B, D0, True, minutes=1.0, role="sitting")
    log.add(T3C, D0, True, minutes=1.0, role="sitting")
    c = cert(log, D0)
    assert c.sittings("s")[0].outcome == "pass"
    assert c.posterior("s", 3).mean == pytest.approx(5.6 / 12)
    assert not c.certified("s", 3)


def test_a_sitting_certification_is_revoked_on_the_accuracy_posterior() -> None:
    """Certified by a sitting on day 0 (prior 0.9: (3.6 + 2)/6 = 0.933). Slow but correct
    practice afterwards keeps it (accuracy only). Three practice misses on day 1:
    (3.6 + 1.95)/(4 + 4.95) = 0.62 < 0.8 -> revoked; ten successes on day 2 lift the mean
    to 0.82, but certifying again needs another sitting."""
    log = Log()
    log.add(T3B, D0, True, minutes=3.0, role="sitting")
    log.add(T3C, D0, True, minutes=3.0, role="sitting")
    log.add(T3, D0, True, minutes=20.0)
    assert cert(log, D0).certified("s", 3)
    log = Log()
    log.add(T3B, D0, True, minutes=3.0, role="sitting")
    log.add(T3C, D0, True, minutes=3.0, role="sitting")
    log.many(T3, day(1), "000")
    c = cert(log, day(1))
    assert not c.certified("s", 3)
    assert c.state("s", 3).ever
    log.many(T3, day(2), "1111111111", minutes=1.0)
    assert not cert(log, day(2)).certified("s", 3)


def test_n_eff_decays_so_old_evidence_needs_fresh_support() -> None:
    """Two successes on day 0 and one on day 10: n_eff = 2 * 2^(-1/3) + 1 = 2.587 < 3.
    A second success on day 10 makes 3.587 -> certified."""
    log = Log()
    log.many(T2, D0, "11")
    log.add(T2, day(10), True)
    assert cert(log, day(10)).posterior("s", 2).n_eff == pytest.approx(2 * 2 ** (-1 / 3) + 1)
    assert not cert(log, day(10)).certified("s", 2)
    log.add(T2, day(10), True)
    assert cert(log, day(10)).certified("s", 2)


def _mean_after(days: list[tuple[int, int, int]], query: int, prior: float) -> float:
    """Reference: (kappa0 p + sum w s) / (kappa0 + sum w n), w = 2^(-age/30)."""
    s = sum(succ * 2 ** (-(query - d) / 30) for d, succ, _ in days)
    n = sum(tot * 2 ** (-(query - d) / 30) for d, _, tot in days)
    return (4 * prior + s) / (4 + n)


def test_revocation_has_hysteresis() -> None:
    """Prior 0.9, target 0.9, revoked below 0.8. Day 0: 4 of 4 -> 0.95, certified.
    Day 1, a miss: (3.6 + 3.909)/(4 + 4.909) = 0.843: below 0.9 but above 0.8, still
    certified. Day 2, a miss: 7.419/9.797 = 0.757 < 0.8 -> revoked. Day 3, a success:
    8.332/10.664 = 0.781, below the 0.9 needed to certify again."""
    log = Log()
    log.many(T2, D0, "1111")
    log.add(T2, day(1), False)
    c = cert(log, day(1))
    assert c.posterior("s", 2).mean == pytest.approx(_mean_after([(0, 4, 4), (1, 0, 1)], 1, 0.9))
    assert c.posterior("s", 2).mean == pytest.approx(0.8428, abs=1e-4)
    assert c.certified("s", 2)
    log.add(T2, day(2), False)
    c = cert(log, day(2))
    assert c.posterior("s", 2).mean == pytest.approx(0.7574, abs=1e-4)
    assert not c.certified("s", 2)
    log.add(T2, day(3), True)
    c = cert(log, day(3))
    assert c.posterior("s", 2).mean == pytest.approx(0.7813, abs=1e-4)
    assert not c.certified("s", 2)
    assert c.state("s", 2).ever
    assert c.state("s", 2).first == D0


def test_fading_evidence_revokes_on_the_day_the_mean_crosses() -> None:
    """Prior 0.5; 16 successes on day 0 certify (18/20 = 0.9). With no new evidence the mean
    (2 + 16f)/(4 + 16f), f = 2^(-d/30), falls below 0.8 when f < 0.375, i.e. d > 42.45:
    day 42 gives 0.8012 (kept), day 43 gives 0.7985 (revoked)."""
    log = Log()
    log.many(T2, D0, "1" * 16)
    assert cert(log, day(42), prior=0.5).certified("s", 2)
    assert cert(log, day(42), prior=0.5).posterior("s", 2).mean == pytest.approx(0.8012, abs=1e-4)
    assert not cert(log, day(43), prior=0.5).certified("s", 2)


def test_certification_survives_low_n_eff_until_the_mean_drops() -> None:
    """Three successes on day 0 certify M1 (6.6/7 = 0.943). On day 30 n_eff is 1.5, but the
    mean (3.6 + 1.5)/5.5 = 0.927 is far above 0.8: still certified."""
    log = Log()
    log.many(T2, D0, "111")
    c = cert(log, day(30))
    assert c.posterior("s", 2).n_eff == pytest.approx(1.5)
    assert c.certified("s", 2)
    assert c.state("s", 2).since == D0


def test_before_leaves_out_the_days_evidence() -> None:
    log = Log()
    log.many(T2, D0, "111")
    c = cert(log, D0)
    assert c.posterior("s", 2, before=True).n_eff == 0.0
    assert not c.state("s", 2, before=True).certified


def sit(log: Log, tier: int, d: date, *, ok: str = "11", minutes: float = 1.0) -> None:
    """A two-problem sitting of skill s at the tier on day d."""
    for k, ch in enumerate(ok):
        log.add(
            problem(f"s.t{tier}.s{k}", "s", tier), d, ch == "1", minutes=minutes, role="sitting"
        )


def test_level_needs_every_judged_lower_tier() -> None:
    """Tiers 1-4 have problems; prior 0.9. Tier 1 untested (no evidence): skipped. Tier 2:
    3 of 3 -> certified. Tier 3: 2 of 2 practice and a passed sitting -> certified. Tier 4:
    two misses, n_eff 2 < 4 and never certified: untested, so it neither counts nor blocks.
    Level 3. With tier 3 judged and failing (2 of 4 practice, a failed sitting), a tier 4
    certified by its sitting can't lift the level past 2."""
    tiers = {"s": {1, 2, 3, 4}}
    log = Log()
    log.many(T2, D0, "111")
    log.many(T3, D0, "11", minutes=3.0)
    sit(log, 3, D0)
    log.many(T4, D0, "00")
    assert cert(log, D0, tiers=tiers).level("s") == 3
    log = Log()
    log.many(T2, D0, "111")
    log.many(T3, D0, "1010", minutes=3.0)
    sit(log, 3, D0, ok="10")
    log.many(T4, D0, "1111", minutes=4.0)
    sit(log, 4, D0)
    c = cert(log, D0, tiers=tiers)
    assert c.certified("s", 4)
    assert not c.certified("s", 3)
    assert c.level("s") == 2
    assert cert(Log(), D0, tiers=tiers).level("s") is None


def test_assumed_keep_key_starts_certified_and_one_miss_revokes() -> None:
    """Mid-course start: Keep (tier 3, 0.80) assumed. The model's prior 0.3 is raised to
    0.8: Beta(3.2, 0.8), certified with no evidence. One miss: 3.2/5 = 0.64 < 0.70 ->
    revoked. Two successes then a miss: 5.2/7 = 0.743 -> kept. Other keys are not assumed."""
    assumed = {"s": (3, 0.8)}
    c = cert(Log(), D0, prior=0.3, assumed=assumed)
    assert c.certified("s", 3, timed=False, target=0.8)
    assert not c.certified("s", 3)
    assert c.prior("s", 3, timed=False, target=0.8) == pytest.approx(0.8)
    log = Log()
    log.add(T3, D0, False)
    assert not cert(log, D0, prior=0.3, assumed=assumed).certified("s", 3, timed=False, target=0.8)
    log = Log()
    log.many(T3, D0, "110")
    assert cert(log, D0, prior=0.3, assumed=assumed).certified("s", 3, timed=False, target=0.8)


def test_for_course_reads_tiers_targets_and_assumptions() -> None:
    a, b = "C::U::A", "C::U::B"
    cr = course([(a, 2.0), (b, 2.0)], [skill("a1", a, 1), skill("b1", b, 2)])
    s = CourseSettings("c", aligned=(b, D0), accuracy_target=0.85)
    c = Certifier.for_course([], cr, s, today=D0)
    assert c.target == 0.85
    assert c.certified("a1", 3, timed=False, target=0.8)  # assumed learned
    assert not c.certified("b1", 3, timed=False, target=0.8)


def test_representatives_are_the_ten_lowest_ids_without_retired_cards() -> None:
    sk = skill("s", "C::U::A", 1, problems=pool("s", {2: 12}))
    reps = representatives(sk, 2, retired={"s.t2.01"})
    assert [p.problem_id for p in reps] == [f"s.t2.{i:02d}" for i in range(2, 12)]
    assert representatives(sk, 3) == ()


def test_model_priors_and_readiness_average_the_representatives() -> None:
    """Tier-2 problems use s (e 0.9) and background alg.x (e 1.0): p = 0.9 each. Tier 3
    problems use s and t (e 0.8): p = 0.72."""
    sk = skill("s", "C::U::A", 1, problems=pool("s", {2: 2, 3: 2}, uses={2: ["alg.x"], 3: ["t"]}))
    cr = course([("C::U::A", 1.0)], [sk, skill("t", "C::U::A", 2)])
    model = fake(cr, extra_background=["alg.x"])
    state = FakeState(e={"s": 0.9, "t": 0.8, "alg.x": 1.0})
    priors = model_priors(model, state, cr, at(D0))
    assert priors[("s", 2)] == pytest.approx(0.9)
    assert priors[("s", 3)] == pytest.approx(0.72)
    assert readiness(Forecast(model, state, at(D0)), sk, 4) is None


def test_from_model_builds_the_course_certifier_on_the_models_priors() -> None:
    """With e 0.97 the prior for a1 at tier 2 is 0.97: 3 of 3 certify M1 (6.88/7 = 0.983).
    The same evidence on the default prior 0.5 does not (5/7 = 0.714)."""
    a = "C::U::A"
    cr = course([(a, 2.0)], [skill("a1", a, 1)])
    log = Log()
    log.many(cr.skills[0].pool[3], D0, "111")
    model, state = fake(cr), FakeState(default_e=0.97)
    c = Certifier.from_model(
        model, state, log.items, cr, CourseSettings("c", start=D0), today=D0, now_ms=at(D0)
    )
    assert c.prior("a1", 2) == pytest.approx(0.97)
    assert c.certified("a1", 2)
    bare = Certifier.for_course(log.items, cr, CourseSettings("c", start=D0), today=D0)
    assert not bare.certified("a1", 2)
