"""Synthetic courses for the simulator (design 6.2, item 1 of the brief).

`calc1()` reads the real component map (`packs/calc1/skills.md`) and generates a problem pool
for each course skill at tiers 1 to 4. A problem's components are the skill plus components
drawn from its prerequisites, the other components of its section and the rest of the course:

| Tier | Components |
|---|---|
| 1 | the skill alone |
| 2 | 1-2: the skill, maybe one prerequisite or earlier component of its section |
| 3 | 3-4: prerequisites and section components first, other sections and background less often |
| 4 | 4-6, with at least one component from another section when one exists |

Only components earlier in course order, or background components, are drawn, so no problem
needs something taught later. Standard times follow design 2.4:
T* = 0.5 + m * steps + m * max(0, tier - 3). Section hours are spread in proportion to each
section's components so that the course takes `weeks` weeks at `weekly_hours` class hours a week.
Background components are the design's `alg.`, `trig.` and `pre.` prefixes (2.1).

`calc1_ch4()` is the default for the gate runs: Chapter 4 plus its prerequisites over a
10-week semester. `toy()` is a six-skill course for fast tests. `perturb_tags()` makes truth
model (f)'s view.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from functools import cache
from pathlib import Path
from random import Random

from core.cards.skillfile import read_skills_file
from core.learner.types import ComponentId, ComponentInfo, ProblemSpec
from core.plan.types import Course, PaceStandard, SectionPace, SkillInfo
from tools.sim2.common import rng_for

REPO = Path(__file__).resolve().parents[2]
CALC1_SKILLS = REPO / "packs" / "calc1" / "skills.md"
BACKGROUND_PREFIXES = ("alg.", "trig.", "pre.")
TIERS = (1, 2, 3, 4)


def is_background(component: str) -> bool:
    return component.startswith(BACKGROUND_PREFIXES)


@dataclass(frozen=True, slots=True)
class MapSkill:
    """One component of a component map: what the generator needs from a skills file."""

    skill_id: ComponentId
    deck: str
    requires: tuple[ComponentId, ...] = ()
    confusable: tuple[ComponentId, ...] = ()


@dataclass(frozen=True, slots=True)
class PoolSizes:
    """Problems per course skill and tier."""

    t1: int = 8
    t2: int = 10
    t3: int = 10
    t4: int = 10

    def size(self, tier: int) -> int:
        return (self.t1, self.t2, self.t3, self.t4)[tier - 1]


@dataclass(frozen=True, slots=True)
class TagNoise:
    """Truth model (f): the share of non-main tags dropped and swapped in the planner's view."""

    drop: float
    swap: float
    non_main_tags: int
    all_tags: int
    dropped: int
    swapped: int


@dataclass(frozen=True, slots=True)
class SimCourse:
    """A course as the policies see it (`course`) and as the truth models see it."""

    name: str
    course: Course
    catalog: Mapping[ComponentId, ComponentInfo]
    true_specs: Mapping[str, ProblemSpec]  # problem_id -> spec with the real tags
    weeks: float
    tag_noise: TagNoise | None = None
    skill_ids: tuple[ComponentId, ...] = field(init=False)
    skills: Mapping[ComponentId, SkillInfo] = field(init=False)
    pools: Mapping[ComponentId, Mapping[int, tuple[ProblemSpec, ...]]] = field(init=False)
    true_pools: Mapping[ComponentId, Mapping[int, tuple[ProblemSpec, ...]]] = field(init=False)

    def __post_init__(self) -> None:
        skills = {s.skill_id: s for s in self.course.skills if not s.background}
        pools: dict[ComponentId, dict[int, tuple[ProblemSpec, ...]]] = {}
        true_pools: dict[ComponentId, dict[int, tuple[ProblemSpec, ...]]] = {}
        for sid, info in skills.items():
            pools[sid] = {t: tuple(p for p in info.pool if p.tier == t) for t in TIERS}
            true_pools[sid] = {
                t: tuple(self.true_specs[p.problem_id] for p in pools[sid][t]) for t in TIERS
            }
        object.__setattr__(self, "skills", skills)
        object.__setattr__(self, "skill_ids", tuple(skills))
        object.__setattr__(self, "pools", pools)
        object.__setattr__(self, "true_pools", true_pools)

    @property
    def course_days(self) -> int:
        """Days of class: total section hours at the standard weekly hours."""
        hours = sum(s.hours for s in self.course.standard.sections)
        return round(hours / self.course.standard.weekly_hours * 7)


@dataclass(frozen=True, slots=True)
class _Context:
    order: Mapping[ComponentId, int]
    section: Mapping[ComponentId, str]
    chapter: Mapping[ComponentId, str]
    prereqs: Mapping[ComponentId, Mapping[ComponentId, int]]  # transitive, with distance
    section_earlier: Mapping[ComponentId, tuple[ComponentId, ...]]
    course_earlier: Mapping[ComponentId, tuple[ComponentId, ...]]  # other sections
    background: tuple[ComponentId, ...]


def build_course(
    name: str,
    skills: Sequence[MapSkill],
    *,
    weeks: float,
    weekly_hours: float,
    minutes_per_step: float = 1.5,
    outside_hours: float | None = 7.0,
    sizes: PoolSizes | None = None,
    seed: int = 0,
    background: Callable[[str], bool] = is_background,
) -> SimCourse:
    """A course with generated pools from a component map in course order."""
    sizes = sizes or PoolSizes()
    course_skills = [s for s in skills if not background(s.skill_id)]
    if not course_skills:
        raise ValueError("the map has no course components")
    ctx = _context(skills, background)
    sections: list[str] = []
    for s in course_skills:
        if s.deck not in sections:
            sections.append(s.deck)
    total_hours = weeks * weekly_hours
    per_section = {d: sum(1 for s in course_skills if s.deck == d) for d in sections}
    pace = PaceStandard(
        sections=tuple(
            SectionPace(d, round(total_hours * per_section[d] / len(course_skills), 4))
            for d in sections
        ),
        weekly_hours=weekly_hours,
        minutes_per_step=minutes_per_step,
        standard_outside_hours=outside_hours,
    )
    infos: list[SkillInfo] = []
    specs: dict[str, ProblemSpec] = {}
    for s in course_skills:
        pool: list[ProblemSpec] = []
        for tier in TIERS:
            for index in range(sizes.size(tier)):
                rng = rng_for("pool", name, seed, s.skill_id, tier, index)
                spec = _problem(s.skill_id, tier, index, rng, ctx, minutes_per_step)
                pool.append(spec)
                specs[spec.problem_id] = spec
        infos.append(
            SkillInfo(
                skill_id=s.skill_id,
                deck=s.deck,
                order=ctx.order[s.skill_id],
                requires=s.requires,
                confusable=s.confusable,
                example_card=f"{s.skill_id}#example",
                pool=tuple(pool),
                background=False,
            )
        )
    for s in skills:
        if background(s.skill_id):
            infos.append(
                SkillInfo(
                    skill_id=s.skill_id,
                    deck=s.deck,
                    order=ctx.order[s.skill_id],
                    requires=s.requires,
                    confusable=s.confusable,
                    background=True,
                )
            )
    catalog = {s.skill_id: ComponentInfo(s.skill_id, background(s.skill_id), name) for s in skills}
    return SimCourse(
        name=name,
        course=Course(course_id=name, standard=pace, skills=tuple(infos)),
        catalog=catalog,
        true_specs=specs,
        weeks=weeks,
    )


def _context(skills: Sequence[MapSkill], background: Callable[[str], bool]) -> _Context:
    order = {s.skill_id: i for i, s in enumerate(skills)}
    by_id = {s.skill_id: s for s in skills}
    section = {s.skill_id: s.deck for s in skills}
    chapter = {s.skill_id: "::".join(s.deck.split("::")[:2]) for s in skills}
    prereqs: dict[ComponentId, dict[ComponentId, int]] = {}
    for s in skills:
        found: dict[ComponentId, int] = {}
        frontier = [(r, 1) for r in s.requires]
        while frontier:
            comp, dist = frontier.pop()
            if comp not in by_id or (comp in found and found[comp] <= dist):
                continue
            found[comp] = dist
            frontier.extend((r, dist + 1) for r in by_id[comp].requires)
        prereqs[s.skill_id] = found
    course_ids = [s.skill_id for s in skills if not background(s.skill_id)]
    section_earlier = {
        sid: tuple(o for o in course_ids if section[o] == section[sid] and order[o] < order[sid])
        for sid in course_ids
    }
    course_earlier = {
        sid: tuple(o for o in course_ids if section[o] != section[sid] and order[o] < order[sid])
        for sid in course_ids
    }
    return _Context(
        order=order,
        section=section,
        chapter=chapter,
        prereqs=prereqs,
        section_earlier=section_earlier,
        course_earlier=course_earlier,
        background=tuple(s.skill_id for s in skills if background(s.skill_id)),
    )


def _problem(
    skill: ComponentId, tier: int, index: int, rng: Random, ctx: _Context, m: float
) -> ProblemSpec:
    extras = _extras(skill, tier, rng, ctx)
    comps = (skill, *extras)
    if tier == 1:
        steps = 1
    elif tier == 4:
        steps = len(comps) + rng.choice((0, 1, 2))
    else:
        steps = len(comps) + rng.choice((0, 1))
    listed: list[ComponentId] = []
    if tier >= 2 or rng.random() < 0.6:
        listed.append(skill)
    for comp in extras:
        if rng.random() < (0.3 if comp in ctx.background else 0.5):
            listed.append(comp)
    pid = f"{skill}.t{tier}.{index:02d}"
    return ProblemSpec(
        problem_id=pid,
        card_id=pid,
        part=None,
        main_skill=skill,
        components=comps,
        tier=tier,
        steps=steps,
        standard_minutes=round(0.5 + m * steps + m * max(0, tier - 3), 4),
        wrong_components=tuple(enumerate(listed)),
        family=f"{skill}.t{tier}.f{index // 2}",
    )


def _extras(skill: ComponentId, tier: int, rng: Random, ctx: _Context) -> list[ComponentId]:
    if tier == 1:
        return []
    near: dict[ComponentId, float] = {}
    for comp, dist in ctx.prereqs[skill].items():
        near[comp] = 4.0 if dist == 1 else 2.0
    for comp in ctx.section_earlier[skill]:
        near[comp] = max(near.get(comp, 0.0), 2.0)
    if tier == 2:
        count = rng.choice((0, 1))
        pool = near or {b: 1.0 for b in ctx.background}
        return _sample(pool, count, rng)
    weights = dict(near)
    for comp in ctx.course_earlier[skill]:
        same_chapter = ctx.chapter[comp] == ctx.chapter[skill]
        if tier == 3:
            weights.setdefault(comp, 0.5 if same_chapter else 0.2)
        else:
            weights.setdefault(comp, 1.0 if same_chapter else 0.6)
    for comp in ctx.background:
        weights.setdefault(comp, 0.5 if tier == 3 else 0.8)
    count = rng.choice((2, 3)) if tier == 3 else rng.choice((3, 4, 5))
    picked = _sample(weights, count, rng)
    if tier == 4:
        others = [c for c in ctx.course_earlier[skill] if c not in picked]
        if others and not any(c in ctx.course_earlier[skill] for c in picked):
            picked[-1] = rng.choice(others)
    return picked


def _sample(weights: Mapping[ComponentId, float], count: int, rng: Random) -> list[ComponentId]:
    """`count` distinct keys drawn with probability proportional to weight (fewer if short)."""
    left = dict(sorted(weights.items()))
    out: list[ComponentId] = []
    while left and len(out) < count:
        total = sum(left.values())
        x = rng.random() * total
        chosen = next(reversed(left))
        for comp, w in left.items():
            x -= w
            if x < 0.0:
                chosen = comp
                break
        out.append(chosen)
        del left[chosen]
    return out


def read_map(path: Path) -> list[MapSkill]:
    """The components of a skills file in file (course) order."""
    entries, problems = read_skills_file(path.read_bytes(), path.name)
    errors = [p for p in problems if p.is_error]
    if errors:
        raise ValueError(f"{path}: {errors[0].message} (line {errors[0].line})")
    return [
        MapSkill(e.skill.id, e.skill.deck or "", e.skill.requires, e.skill.confusable)
        for e in entries
    ]


@cache
def calc1(sizes: PoolSizes | None = None, seed: int = 0) -> SimCourse:
    """The Calculus I map with generated pools: 15 weeks at 2.5 class hours a week."""
    return build_course(
        "calc1", read_map(CALC1_SKILLS), weeks=15.0, weekly_hours=2.5, sizes=sizes, seed=seed
    )


def with_prerequisites(
    skills: Sequence[MapSkill], keep: Callable[[MapSkill], bool]
) -> list[MapSkill]:
    """The components `keep` selects plus everything they require, in map order."""
    by_id = {s.skill_id: s for s in skills}
    chosen = {s.skill_id for s in skills if keep(s)}
    frontier = list(chosen)
    while frontier:
        for req in by_id[frontier.pop()].requires:
            if req in by_id and req not in chosen:
                chosen.add(req)
                frontier.append(req)
    return [s for s in skills if s.skill_id in chosen]


@cache
def calc1_ch4(seed: int = 0) -> SimCourse:
    """Chapter 4 of the Calculus I map plus its prerequisites (72 course and 23 background
    components): a 10-week semester at 2.5 class hours a week."""
    skills = with_prerequisites(read_map(CALC1_SKILLS), lambda s: "::4 " in s.deck)
    return build_course("calc1-ch4", skills, weeks=10.0, weekly_hours=2.5, seed=seed)


TOY_MAP: tuple[MapSkill, ...] = (
    MapSkill("alg.x", "Toy::0 Background::0.1 Algebra"),
    MapSkill("alg.y", "Toy::0 Background::0.1 Algebra"),
    MapSkill("toy.a1", "Toy::1 Basics::1.1 First", ("alg.x",)),
    MapSkill("toy.a2", "Toy::1 Basics::1.1 First", ("toy.a1",), ("toy.b1",)),
    MapSkill("toy.b1", "Toy::1 Basics::1.2 Second", ("toy.a1", "alg.y"), ("toy.a2",)),
    MapSkill("toy.b2", "Toy::1 Basics::1.2 Second", ("toy.b1",)),
    MapSkill("toy.c1", "Toy::2 More::2.1 Third", ("toy.a2", "toy.b2")),
    MapSkill("toy.c2", "Toy::2 More::2.1 Third", ("toy.c1", "alg.x")),
)


@cache
def toy(seed: int = 0) -> SimCourse:
    """Six course skills in three sections over two weeks, small pools: for fast tests."""
    return build_course(
        "toy",
        TOY_MAP,
        weeks=2.0,
        weekly_hours=2.5,
        sizes=PoolSizes(3, 4, 4, 4),
        seed=seed,
    )


def perturb_tags(
    sim: SimCourse, drop: float = 0.10, swap: float = 0.10, seed: int = 0
) -> SimCourse:
    """Truth model (f): the planner's view loses a share of tags and gets wrong ones instead.

    Each non-main tag of each problem is dropped with probability `drop` or replaced by
    another component (earlier in course order or background, not already on the problem)
    with probability `swap`. Main skills stay: they decide a problem's pool. `wrong:` lines
    keep their indices; a dropped tag's lines go and a swapped tag's lines follow the new tag.
    The truth keeps `sim.true_specs`.
    """
    order = {s.skill_id: s.order for s in sim.course.skills}
    background = [c for c, info in sim.catalog.items() if info.background]
    course_ids = [s.skill_id for s in sim.course.skills if not s.background]
    rng = rng_for("tags", sim.name, seed)
    seen = dropped = swapped = mains = 0
    new_skills: list[SkillInfo] = []
    for info in sim.course.skills:
        pool: list[ProblemSpec] = []
        for spec in info.pool:
            mains += 1
            mapping: dict[ComponentId, ComponentId | None] = {spec.main_skill: spec.main_skill}
            comps = [spec.main_skill]
            for comp in spec.components[1:]:
                seen += 1
                u = rng.random()
                if u < drop:
                    mapping[comp] = None
                    dropped += 1
                    continue
                if u < drop + swap:
                    choices = sorted(
                        c
                        for c in (*course_ids, *background)
                        if c not in spec.components
                        and c not in comps
                        and (c in background or order[c] < order[spec.main_skill])
                    )
                    if choices:
                        new = rng.choice(choices)
                        mapping[comp] = new
                        comps.append(new)
                        swapped += 1
                        continue
                mapping[comp] = comp
                comps.append(comp)
            wrong = tuple(
                (i, new_c)
                for i, c in spec.wrong_components
                if (new_c := mapping.get(c)) is not None
            )
            pool.append(replace(spec, components=tuple(comps), wrong_components=wrong))
        new_skills.append(replace(info, pool=tuple(pool)))
    noise = TagNoise(
        drop=drop,
        swap=swap,
        non_main_tags=seen,
        all_tags=seen + mains,
        dropped=dropped,
        swapped=swapped,
    )
    return SimCourse(
        name=f"{sim.name}+tags",
        course=replace(sim.course, skills=tuple(new_skills)),
        catalog=sim.catalog,
        true_specs=sim.true_specs,
        weeks=sim.weeks,
        tag_noise=noise,
    )
