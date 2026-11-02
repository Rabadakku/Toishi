"""Builders for planner tests: problems, pools, skills, courses and observations."""

import random
from collections.abc import Iterable, Mapping, Sequence
from datetime import date

from core.learner.types import ComponentId, ComponentInfo, Observation, ProblemSpec
from core.plan.types import Course, PaceStandard, SectionPace, SkillInfo
from tests.plan.fakes import DAY_MS, FakePredictor

EPOCH = date(1970, 1, 1)
NOON_MS = 12 * 3_600_000


def rng(seed: int | str = 0) -> random.Random:
    """A seeded generator (tests are reproducible; nothing here is security)."""
    return random.Random(seed)  # noqa: S311


def at(day: date, minutes: int = 0) -> int:
    """Epoch ms at noon of `day`, plus `minutes`."""
    return (day - EPOCH).days * DAY_MS + NOON_MS + minutes * 60_000


def standard_minutes(steps: int, tier: int, m: float = 1.5) -> float:
    """Design 2.4: T* = 0.5 + m*steps + m*max(0, tier - 3)."""
    return 0.5 + m * steps + m * max(0, tier - 3)


def problem(
    pid: str,
    skill: ComponentId,
    tier: int,
    *,
    uses: Sequence[ComponentId] = (),
    steps: int = 2,
    minutes: float | None = None,
    family: str | None = None,
    card: str | None = None,
) -> ProblemSpec:
    components = tuple(dict.fromkeys((skill, *uses)))
    card_id = card or pid
    return ProblemSpec(
        problem_id=pid,
        card_id=card_id,
        part=None,
        main_skill=skill,
        components=components,
        tier=tier,
        steps=steps,
        standard_minutes=standard_minutes(steps, tier) if minutes is None else minutes,
        family=family or card_id,
    )


def pool(
    skill: ComponentId,
    per_tier: Mapping[int, int] | None = None,
    *,
    uses: Mapping[int, Sequence[ComponentId]] | None = None,
    steps: int = 2,
) -> tuple[ProblemSpec, ...]:
    """`per_tier[t]` problems at each tier t, ids `<skill>.t<t>.<nn>`; tier t problems also
    use `uses[t]`. Default: three problems at each of tiers 1 to 4."""
    per_tier = per_tier if per_tier is not None else {1: 3, 2: 3, 3: 3, 4: 3}
    uses = uses or {}
    return tuple(
        problem(f"{skill}.t{t}.{i:02d}", skill, t, uses=uses.get(t, ()), steps=steps)
        for t, n in sorted(per_tier.items())
        for i in range(1, n + 1)
    )


def skill(
    sid: ComponentId,
    deck: str,
    order: int,
    *,
    requires: Sequence[ComponentId] = (),
    confusable: Sequence[ComponentId] = (),
    example: str | None = None,
    problems: Iterable[ProblemSpec] | None = None,
    background: bool = False,
) -> SkillInfo:
    return SkillInfo(
        skill_id=sid,
        deck=deck,
        order=order,
        requires=tuple(requires),
        confusable=tuple(confusable),
        example_card=example,
        pool=tuple(problems) if problems is not None else pool(sid),
        background=background,
    )


def course(
    sections: Sequence[tuple[str, float]],
    skills: Sequence[SkillInfo],
    *,
    weekly: float = 2.0,
    outside: float | None = None,
    course_id: str = "c",
) -> Course:
    return Course(
        course_id=course_id,
        standard=PaceStandard(
            sections=tuple(SectionPace(d, h) for d, h in sections),
            weekly_hours=weekly,
            standard_outside_hours=outside,
        ),
        skills=tuple(skills),
    )


def catalog(
    course_: Course, extra_background: Iterable[ComponentId] = ()
) -> dict[ComponentId, ComponentInfo]:
    """Course components from the course's skills, plus background components."""
    out = {
        s.skill_id: ComponentInfo(s.skill_id, background=s.background, course_id=course_.course_id)
        for s in course_.skills
    }
    for cid in extra_background:
        out[cid] = ComponentInfo(cid, background=True, course_id=None)
    return out


def fake(course_: Course, extra_background: Iterable[ComponentId] = ()) -> FakePredictor:
    return FakePredictor(catalog(course_, extra_background))


class Log:
    """Observations with increasing attempt ids, one study day at a time."""

    def __init__(self) -> None:
        self.items: list[Observation] = []

    def add(
        self,
        p: ProblemSpec,
        day: date,
        correct: bool,
        *,
        minutes: float | None = None,
        role: str = "growth",
        aided: bool = False,
    ) -> Observation:
        n = len(self.items) + 1
        obs = Observation(
            attempt_id=n,
            at_ms=at(day, n),
            study_day=day,
            problem=p,
            correct=correct,
            aided=aided,
            minutes=minutes if correct else None,
            role=role,
        )
        self.items.append(obs)
        return obs

    def many(
        self,
        p: ProblemSpec,
        day: date,
        outcomes: str,
        *,
        minutes: float | None = None,
        role: str = "growth",
    ) -> None:
        """One observation per character: '1' a success, '0' a miss."""
        for ch in outcomes:
            self.add(p, day, ch == "1", minutes=minutes, role=role)

    def sitting(
        self,
        problems: Sequence[ProblemSpec],
        day: date,
        outcomes: str | None = None,
        *,
        minutes: float | None = 1.0,
    ) -> None:
        """One skill's sitting: a role "sitting" first try per problem ('1' right, taking
        `minutes`; '0' wrong). All right and in time by default: a pass."""
        for p, ch in zip(problems, outcomes or "1" * len(problems), strict=True):
            self.add(p, day, ch == "1", minutes=minutes, role="sitting")
