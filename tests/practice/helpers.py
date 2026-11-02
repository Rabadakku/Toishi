"""A small course world for core/practice tests: a pack with a pace standard, background skills,
templates, step-tagged solutions with known wrong answers, a multi-part card and examples."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from core.model import (
    Attempt,
    Card,
    CardPart,
    Course,
    CourseSetup,
    GradedAnswer,
    PackInfo,
    PackPace,
    PackPaceSection,
    Section,
    Skill,
    SolutionStep,
    Unit,
    WrongAnswer,
)
from core.storage import Storage, build_pack
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths

NY = ZoneInfo("America/New_York")
START = datetime(2026, 9, 7, 12, tzinfo=NY)  # a Monday, noon
COURSE = "Calc"
UNIT = "Calc::1 Limits"
PRE = "Calc::0 Precalculus"
S1 = "Calc::1 Limits::1.1 Intro"
S2 = "Calc::1 Limits::1.2 Rules"
S0 = "Calc::0 Precalculus::0.1 Algebra"
OTHER = "Other"
O1 = "Other::1 U::1.1 A"


def card(
    card_id: str,
    skill: str,
    tier: int,
    *,
    uses: Sequence[str] = (),
    steps: Sequence[str] = (),
    wrong: Sequence[tuple[str, int | None]] = (),
    template: str | None = None,
    seed: int | None = None,
    kind: str = "problem",
    status: str = "active",
) -> Card:
    return Card(
        id=card_id,
        kind=kind,  # type: ignore[arg-type]
        skill_id=skill,
        uses=tuple(uses),
        tier=tier,
        answer_type="number" if kind == "problem" else "self",
        answer="1" if kind == "problem" else None,
        wrong=tuple(WrongAnswer(answer=a, step=s) for a, s in wrong),
        question_md="Solve.",
        solution=tuple(
            SolutionStep(number=i + 1, skill_id=k, label=f"Step {i + 1}")
            for i, k in enumerate(steps)
        ),
        template_id=template,
        seed=seed,
        status=status,  # type: ignore[arg-type]
    )


def records(*, pace: bool = True) -> list[object]:
    out: list[object] = [
        Course(id=COURSE, title="Calculus", ord=0),
        Unit(id=PRE, course_id=COURSE, title="0 Precalculus", ord=0),
        Unit(id=UNIT, course_id=COURSE, title="1 Limits", ord=1),
        Section(id=S0, unit_id=PRE, title="0.1 Algebra", ord=0),
        Section(id=S1, unit_id=UNIT, title="1.1 Intro", ord=0, textbook_ref="Book One §1.1"),
        Section(id=S2, unit_id=UNIT, title="1.2 Rules", ord=1),
        Course(id=OTHER, title="Other course", ord=1),
        Unit(id="Other::1 U", course_id=OTHER, title="1 U", ord=0),
        Section(id=O1, unit_id="Other::1 U", title="1.1 A", ord=0),
        Skill(id="alg.factor", name="Factor", deck=S0, section_id=S0),
        Skill(id="c.limit", name="Find a limit", deck=S1, section_id=S1, requires=("alg.factor",)),
        Skill(
            id="c.squeeze",
            name="Squeeze",
            deck=S1,
            section_id=S1,
            requires=("c.limit",),
            confusable=("c.lhopital",),
            textbook_ref="Book Two §2.3; Book One §1.4",
        ),
        Skill(id="c.lhopital", name="L'Hopital", deck=S2, section_id=S2, requires=("c.limit",)),
        Skill(id="o.thing", name="Other thing", deck=O1, section_id=O1),
    ]
    for skill, uses in (("c.limit", ("alg.factor",)), ("c.squeeze", ()), ("c.lhopital", ())):
        for tier in (1, 2, 3, 4):
            for seed in range(3):
                out.append(
                    card(
                        f"{skill}.t{tier}.v{seed}",
                        skill,
                        tier,
                        uses=uses,
                        steps=(skill, *uses, skill),
                        wrong=(("7", 2), ("8", None)),
                        template=f"{skill}.tm{tier}",
                        seed=seed,
                    )
                )
        out.append(card(f"{skill}.ex", skill, 1, kind="example"))
    for seed in range(4):
        out.append(card(f"alg.factor.t2.v{seed}", "alg.factor", 2, steps=("alg.factor",)))
    out.append(card("c.limit.retired", "c.limit", 2, status="retired"))
    out.append(card("o.thing.t2", "o.thing", 2, steps=("o.thing",)))
    out.append(
        Card(
            id="c.multi",
            skill_id="c.limit",
            uses=("alg.factor", "c.squeeze"),
            tier=3,
            question_md="Several things.",
            parts=(
                CardPart(
                    label="a",
                    prompt_md="First",
                    answer_type="number",
                    answer="1",
                    wrong=(WrongAnswer(answer="2", step=1),),
                ),
                CardPart(
                    label="b",
                    prompt_md="Second",
                    answer_type="number",
                    answer="2",
                    skill_id="c.squeeze",
                ),
            ),
            solution=(
                SolutionStep(number=1, skill_id="alg.factor", label="Factor"),
                SolutionStep(number=2, skill_id="c.squeeze", label="Squeeze"),
            ),
        )
    )
    if pace:
        out.append(
            PackPace(
                minutes_per_step=2.0,
                weekly_hours=4.0,
                sections=(PackPaceSection(deck=S1, hours=4.0), PackPaceSection(deck=S2, hours=4.0)),
            )
        )
    return out


@dataclass
class World:
    storage: Storage
    clock: FixedClock
    paths: ProfilePaths
    pack_paths: list[Path] = field(default_factory=list)

    def reopen(self) -> None:
        self.storage.close(backup=False)
        self.storage = Storage.open(self.paths, pack_paths=self.pack_paths, clock=self.clock)

    def today(self) -> date:
        return date.fromisoformat(self.storage.users.study_day())

    def now(self) -> int:
        return self.clock.now_ms()


def make_world(tmp_path: Path, *, pace: bool = True) -> World:
    pack = tmp_path / "pack.db"
    build_pack(pack, PackInfo(id="pk", title="Pack", version="1"), records(pace=pace))  # type: ignore[arg-type]
    clock = FixedClock(START, tz=NY)
    paths = ProfilePaths(tmp_path / "profile")
    storage = Storage.open(paths, pack_paths=[pack], clock=clock, create=True)
    storage.users.set_setting("study.timezone", "America/New_York")
    return World(storage, clock, paths, [pack])


@contextmanager
def world_ctx(tmp_path: Path, **kw: Any) -> Iterator[World]:
    w = make_world(tmp_path, **kw)
    try:
        yield w
    finally:
        w.storage.close(backup=False)


def set_up(world: World, *, start: date | None = None, **kw: Any) -> CourseSetup:
    day = start or START.date()
    return world.storage.users.set_course_setup(CourseSetup(course_id=COURSE, start=day, **kw))


def answer(
    world: World,
    card_id: str,
    *,
    correct: bool = True,
    attempt_number: int = 1,
    final: bool = True,
    presentation: str | None = None,
    role: str = "growth",
    minutes: float | None = 2.0,
    verdict: str | None = None,
    **extra_fields: Any,
) -> Attempt:
    """Commit one problem attempt row the way the v3 session writes it."""
    world.clock.advance(seconds=60)
    found = world.storage.packs.card(card_id)
    assert found is not None
    return world.storage.users.record_answer(
        GradedAnswer(
            attempt=Attempt(
                card_id=card_id,
                skill_id=found.skill_id,
                tier=found.tier,
                card_kind=found.kind,
                presentation_id=presentation or f"p{world.clock.now_ms()}",
                verdict=verdict or ("correct" if correct else "incorrect"),  # type: ignore[arg-type]
                attempt_number=attempt_number,
                final=final,
                role=role,  # type: ignore[arg-type]
                valid_minutes=minutes if correct and attempt_number == 1 else None,
                **extra_fields,
            )
        )
    )
