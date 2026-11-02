"""The synthetic courses: pools, component sets, standard times and the pace standard."""

from collections import Counter

import pytest

from tools.sim2.course import (
    CALC1_SKILLS,
    PoolSizes,
    build_course,
    calc1,
    calc1_ch4,
    is_background,
    perturb_tags,
    read_map,
    toy,
)


def test_calc1_uses_the_real_component_map() -> None:
    sim = calc1()
    background = [c for c, info in sim.catalog.items() if info.background]
    assert len(sim.skill_ids) == 123
    assert len(background) == 39
    assert all(is_background(c) for c in background)
    assert all(not is_background(s) for s in sim.skill_ids)
    assert sim.skill_ids[0] == "calc1.rates.average-rate"


def test_calc1_pace_standard_takes_fifteen_weeks() -> None:
    std = calc1().course.standard
    assert std.weekly_hours == 2.5
    assert std.minutes_per_step == 1.5
    assert sum(s.hours for s in std.sections) == pytest.approx(37.5, abs=0.01)
    assert len(std.sections) == 31  # chapters 2-5; the six precalculus decks are background
    assert calc1().course_days == 105
    # hours follow components: 2.3 has 9 components, 3.8 has 1
    hours = {s.deck.rsplit("::", 1)[1]: s.hours for s in std.sections}
    assert hours["2.3 The Limit Laws"] == pytest.approx(
        9 * hours["3.8 Implicit Differentiation"], abs=1e-3
    )


def test_pools_have_the_tier_shapes() -> None:
    sim = calc1()
    order = {s.skill_id: s.order for s in sim.course.skills}
    deck = {s.skill_id: s.deck for s in sim.course.skills}
    sizes: Counter[int] = Counter()
    for skill in sim.skill_ids:
        for tier in (1, 2, 3, 4):
            pool = sim.pools[skill][tier]
            sizes[tier] += len(pool)
            for p in pool:
                k = len(p.components)
                assert p.main_skill == skill == p.components[0]
                assert len(set(p.components)) == k
                assert {1: k == 1, 2: k in (1, 2), 3: k in (3, 4), 4: 4 <= k <= 6}[tier]
                for c in p.components[1:]:
                    assert is_background(c) or order[c] < order[skill]
                assert p.standard_minutes == pytest.approx(
                    0.5 + 1.5 * p.steps + 1.5 * max(0, tier - 3)
                )
                assert p.steps >= (1 if tier == 1 else k)
                listed = {c for _, c in p.wrong_components}
                assert listed <= set(p.components)
                if tier >= 2:
                    assert (0, skill) in p.wrong_components
                if tier == 4 and any(
                    not is_background(o) and deck[o] != deck[skill] and order[o] < order[skill]
                    for o in sim.skill_ids
                ):
                    assert any(
                        not is_background(c) and deck[c] != deck[skill] for c in p.components
                    )
    assert sizes == {1: 123 * 8, 2: 123 * 10, 3: 123 * 10, 4: 123 * 10}


def test_generation_is_deterministic() -> None:
    skills = read_map(CALC1_SKILLS)
    a = build_course("x", skills, weeks=15, weekly_hours=2.5, sizes=PoolSizes(2, 2, 2, 2), seed=3)
    b = build_course("x", skills, weeks=15, weekly_hours=2.5, sizes=PoolSizes(2, 2, 2, 2), seed=3)
    c = build_course("x", skills, weeks=15, weekly_hours=2.5, sizes=PoolSizes(2, 2, 2, 2), seed=4)
    assert a.true_specs == b.true_specs
    assert a.true_specs != c.true_specs


def test_toy_course() -> None:
    sim = toy()
    assert sim.skill_ids == ("toy.a1", "toy.a2", "toy.b1", "toy.b2", "toy.c1", "toy.c2")
    assert sim.course_days == 14
    assert len(sim.true_specs) == 6 * (3 + 4 + 4 + 4)
    background = {s.skill_id for s in sim.course.skills if s.background}
    assert background == {"alg.x", "alg.y"}


def test_perturbed_tags_keep_the_truth_and_the_main_skills() -> None:
    sim = calc1()
    view = perturb_tags(sim)
    noise = view.tag_noise
    assert noise is not None
    assert view.true_specs is sim.true_specs
    assert noise.dropped / noise.non_main_tags == pytest.approx(0.10, abs=0.015)
    assert noise.swapped / noise.non_main_tags == pytest.approx(0.10, abs=0.015)
    changed = 0
    for skill in sim.skill_ids:
        for tier in (1, 2, 3, 4):
            for shown, real in zip(view.pools[skill][tier], sim.pools[skill][tier], strict=True):
                assert shown.problem_id == real.problem_id
                assert shown.components[0] == real.components[0] == skill
                assert len(set(shown.components)) == len(shown.components)
                assert {c for _, c in shown.wrong_components} <= set(shown.components)
                shown_lines = dict(shown.wrong_components)
                for index, comp in real.wrong_components:
                    if comp == skill:
                        assert shown_lines[index] == skill
                changed += shown.components != real.components
    assert changed > 1000
    assert perturb_tags(sim).course == view.course  # deterministic


def test_chapter_4_subset_keeps_its_prerequisites() -> None:
    sim = calc1_ch4()
    skills = {s.skill_id: s for s in sim.course.skills}
    assert len(sim.skill_ids) == 72
    assert sum(1 for s in skills.values() if s.background) == 23
    assert sum("::4 " in skills[s].deck for s in sim.skill_ids) == 48
    assert all(r in skills for s in skills.values() for r in s.requires)
    assert sim.course_days == 70  # 10 weeks
