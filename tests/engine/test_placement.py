"""Placement check walk and seeding (Library)."""

from dataclasses import replace

from core.engine.goals import Catalog
from core.engine.placement import PlacementWalk, apply_seeds, placement_order
from core.model import Section, Skill, Unit
from tests.engine.helpers import adapter, at_day, learned_state


def chain_catalog(n: int = 30) -> Catalog:
    """s00 <- s01 <- ... (each requires the previous), plus an unrelated skill."""
    skills = [
        Skill(
            id=f"c.s{i:02d}",
            name=f"s{i}",
            section_id="c.sec",
            requires=(f"c.s{i - 1:02d}",) if i else (),
        )
        for i in range(n)
    ]
    skills.append(Skill(id="c.other", name="other", section_id="c.sec"))
    return Catalog.build(
        skills,
        [Section(id="c.sec", unit_id="c.u", title="s")],
        [Unit(id="c.u", course_id="c", title="u")],
    )


def test_order_starts_with_the_most_advanced_skills():
    cat = chain_catalog(5)
    assert placement_order(cat, cat.skills)[:2] == ["c.s04", "c.s03"]


def test_a_pass_infers_prerequisites_and_skips_them():
    # ADR-0019 item 9: the middle first; a pass infers prerequisites up to two levels down.
    cat = chain_catalog(5)
    walk = PlacementWalk.start(cat, cat.skills)
    first = walk.next_skill()
    assert first == "c.s02"
    walk.answer(first, "pass")
    assert walk.seeds() == {"c.s02": "direct", "c.s01": "inferred", "c.s00": "inferred"}
    asked = {first}
    while (k := walk.next_skill()) is not None:
        assert k not in ("c.s01", "c.s00")  # inferred: never asked
        walk.answer(k, "unknown" if k == "c.other" else "pass")
        asked.add(k)
    assert asked == {"c.s02", "c.s04", "c.other"}  # s04 passed: s03 inferred


def test_failed_and_unknown_skills_start_as_new():
    cat = chain_catalog(3)
    walk = PlacementWalk.start(cat, cat.skills)
    walk.answer("c.s02", "fail")
    walk.answer("c.s01", "unknown")
    walk.answer("c.s00", "pass")
    assert walk.seeds() == {"c.s00": "direct"}


def test_stops_after_25_questions():
    cat = Catalog.build(
        [Skill(id=f"c.k{i:02d}", name="k", section_id="c.sec") for i in range(40)],
        [Section(id="c.sec", unit_id="c.u", title="s")],
        [Unit(id="c.u", course_id="c", title="u")],
    )
    walk = PlacementWalk.start(cat, cat.skills)
    asked = 0
    while (k := walk.next_skill()) is not None:
        walk.answer(k, "fail")
        asked += 1
    assert asked == 25


def test_seeds_get_provisional_stabilities_and_never_remove_knowledge():
    fsrs = adapter()
    existing = {"c.strong": replace(learned_state(50.0, at=at_day(0)), skill_id="c.strong")}
    rows = apply_seeds(
        existing,
        {
            "c.direct": "direct",
            "c.inferred": "inferred",
            "c.strong": "direct",
            "c.solid": "solid",
            "c.covered": "covered",
        },
        at_ms=at_day(1),
        adapter=fsrs,
    )
    by_id = {r.skill_id: r for r in rows}
    assert set(by_id) == {"c.direct", "c.inferred", "c.solid", "c.covered"}
    assert by_id["c.direct"].stability == 10.0
    assert by_id["c.solid"].stability == 10.0
    assert by_id["c.inferred"].stability == 2.3
    assert by_id["c.covered"].stability == 2.3
    assert all(r.level == "learned" and r.fsrs_state == 2 for r in rows)
    assert by_id["c.inferred"].level_evidence["provisional"] == "inferred"


# ---------------------------------------------------------------- ADR-0019 item 9 (halving)


def test_asks_a_middle_skill_first_then_halves():
    cat = chain_catalog(9)
    walk = PlacementWalk.start(cat, [k for k in cat.skills if k != "c.other"])
    assert walk.next_skill() == "c.s04"  # the middle of s00..s08
    walk.answer("c.s04", "fail")  # prunes s05..s08
    assert walk.seeds() == {}
    assert walk.next_skill() == "c.s02"  # the middle of what is left, s00..s03
    walk.answer("c.s02", "pass")  # s00, s01: prerequisites within two levels
    assert walk.seeds() == {"c.s02": "direct", "c.s01": "inferred", "c.s00": "inferred"}
    assert walk.next_skill() == "c.s03"
    walk.answer("c.s03", "pass")
    assert walk.next_skill() is None  # everything resolved after 3 questions


def test_a_single_pass_never_marks_a_deep_chain_known_without_a_confirming_question():
    cat = chain_catalog(12)
    walk = PlacementWalk.start(cat, ["c.s11"])  # only the top skill is in the check
    walk.answer("c.s11", "pass")
    seeds = walk.seeds()
    assert seeds["c.s09"] == "inferred"  # two levels down
    assert "c.s05" not in seeds  # deeper: not on one pass
    walk = PlacementWalk.start(cat, [k for k in cat.skills if k != "c.other"])
    walk.answer("c.s11", "pass")
    walk.answer("c.s06", "pass")  # a confirming pass inside the chain
    assert {f"c.s{i:02d}" for i in range(12)} <= set(walk.seeds())


def test_a_fail_prunes_dependents_and_inference_never_contradicts_it():
    cat = chain_catalog(6)
    walk = PlacementWalk.start(cat, [k for k in cat.skills if k != "c.other"])
    walk.answer("c.s05", "pass")
    walk.answer("c.s03", "fail")
    seeds = walk.seeds()
    assert seeds["c.s05"] == "direct"  # placement only adds what was shown
    assert "c.s03" not in seeds
    assert "c.s04" not in seeds  # depends on a failed skill


def _layered(rnd, layers: int, width: int) -> Catalog:
    skills = []
    for i in range(layers * width):
        layer = i // width
        req: set[int] = set()
        if layer:
            k = rnd.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            while len(req) < k:
                back = 2 if layer >= 2 and rnd.random() < 0.2 else 1
                req.add(rnd.randrange((layer - back) * width, (layer - back + 1) * width))
        skills.append(
            Skill(
                id=f"c.k{i:03d}",
                name="k",
                section_id="c.sec",
                requires=tuple(f"c.k{r:03d}" for r in sorted(req)),
            )
        )
    return Catalog.build(
        skills,
        [Section(id="c.sec", unit_id="c.u", title="s")],
        [Unit(id="c.u", course_id="c", title="u")],
    )


def _student(rnd, cat: Catalog, layers: int, width: int, target: float) -> set[str]:
    """A downward-closed known set (sim_placement.py's student), about `target` of skills."""
    ids = sorted(cat.skills)
    b = {k: (int(k[3:]) // width) / layers + rnd.gauss(0, 0.12) for k in ids}

    def known_for(theta: float) -> set[str]:
        known: set[str] = set()
        for k in ids:  # prerequisites have lower numbers
            if b[k] <= theta and all(r in known for r in cat.skills[k].requires):
                known.add(k)
        return known

    lo, hi = -0.5, 1.6
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if len(known_for(mid)) / len(ids) < target else (lo, mid)
    return known_for((lo + hi) / 2)


def _simulate(slip: float, guess: float, target: float, draws: int = 20) -> tuple[float, float]:
    import random

    sens = false_known = 0.0
    for d in range(draws):
        rnd = random.Random(f"place-{target}-{d}")  # noqa: S311 -- reproducible simulation
        cat = _layered(rnd, 10, 20)
        truth = _student(rnd, cat, 10, 20, target)
        walk = PlacementWalk.start(cat, cat.skills)
        while (k := walk.next_skill()) is not None:
            ok = rnd.random() < ((1 - slip) if k in truth else guess)
            walk.answer(k, "pass" if ok else "fail")
        seeded = set(walk.seeds())
        sens += len(seeded & truth) / len(truth) if truth else 0.0
        false_known += len(seeded - truth) / len(seeded) if seeded else 0.0
    return sens / draws, false_known / draws


def test_placement_seeds_most_known_skills_and_few_false_ones_in_simulation():
    # sim_placement.py's graphs (10 layers x 20 skills), 25 questions. The old deepest-first
    # walk seeded about 10% of known skills at 50% knowledge.
    sens, false_known = _simulate(slip=0.05, guess=0.03, target=0.5)
    assert sens >= 0.60, sens
    assert false_known <= 0.05, false_known
