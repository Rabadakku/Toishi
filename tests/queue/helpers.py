"""A small course world for queue tests: courses, sections, skills, cards, a fake checker,
and `Script`, a stand-in for the planner that serves chosen problems."""

from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from zoneinfo import ZoneInfo

from core import grader
from core.grader import AnswerSpec, Status
from core.model import (
    Card,
    Course,
    CourseSetup,
    PackInfo,
    Section,
    Skill,
    SkillState,
    SolutionStep,
    Unit,
    WrongAnswer,
)
from core.plan.types import ServedItem, WorkItem
from core.practice import PlannedItem, PracticePlan
from core.queue import StudyService
from core.queue.guards import TimingReport
from core.storage import Storage, build_pack
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths

NY = ZoneInfo("America/New_York")
START = datetime(2026, 9, 1, 12, tzinfo=NY)


FEEDBACK = "Check the sign of the second term."  # every problem's known wrong answer "7"


def fake_checker(raw: str, spec: AnswerSpec, source: Any) -> grader.GradeResult:
    """'?' is a syntax error, '!' undecidable, the key's text is correct, a known wrong
    answer is matched (its feedback in the message, like the real grader), else incorrect."""
    text = raw.strip()
    if text == "?":
        return grader.GradeResult(Status.INVALID, None, "syntax error")
    if text == "!":
        return grader.GradeResult(Status.UNDECIDABLE, text, "too slow")
    if text == spec.answer.strip():
        return grader.GradeResult(Status.CORRECT, text)
    known = next((w for w in spec.wrong if w.answer == text), None)
    if known is not None:
        return grader.GradeResult(Status.INCORRECT, text, known.feedback or "", matched_wrong=known)
    return grader.GradeResult(Status.INCORRECT, text)


def fake_preview(raw: str, spec: AnswerSpec, source: Any) -> grader.Preview:
    return grader.Preview(raw.strip() != "?", raw.strip())


@dataclass
class World:
    storage: Storage
    clock: FixedClock
    skills: list[str]
    courses: list[str]
    sections: list[str]
    paths: ProfilePaths
    pack_paths: list[Path] = field(default_factory=list)

    def service(self, **kw: Any) -> StudyService:
        return StudyService(self.storage, checker=fake_checker, previewer=fake_preview, **kw)

    def reopen(self) -> None:
        """Close the profile without ending anything (a crash or Cmd+Q) and open it again."""
        self.storage.close(backup=False)
        self.storage = Storage.open(self.paths, pack_paths=self.pack_paths, clock=self.clock)


def skill_id(course: str, section: int, k: int) -> str:
    return f"{course}.s{section}.k{k}"


def world_records(
    courses: Sequence[str] = ("ca",),
    *,
    sections: int = 2,
    skills: int = 3,
    seeds: int = 4,
    flashcards: bool = False,
    confusable: Iterable[tuple[str, str]] = (),
    hints: int = 2,
) -> tuple[list[object], list[str], list[str]]:
    records: list[object] = []
    skill_ids: list[str] = []
    section_ids: list[str] = []
    pairs = list(confusable)
    for ci, course in enumerate(courses):
        records.append(Course(id=course, title=course.upper(), ord=ci))
        records.append(Unit(id=f"{course}.u1", course_id=course, title="Unit 1"))
        for s in range(1, sections + 1):
            previous: str | None = None
            section = f"{course}.s{s}"
            section_ids.append(section)
            records.append(
                Section(
                    id=section,
                    unit_id=f"{course}.u1",
                    title=f"{s}",
                    ord=s,
                    textbook_ref=f"Book {s}.1",
                )
            )
            for k in range(1, skills + 1):
                sid = skill_id(course, s, k)
                conf = tuple(b for a, b in pairs if a == sid)
                records.append(
                    Skill(
                        id=sid,
                        name=f"{course.upper()} skill {s}.{k}",
                        section_id=section,
                        requires=(previous,) if previous else (),
                        confusable=conf,
                        exam_tier=3,
                    )
                )
                skill_ids.append(sid)
                step_one = previous or sid  # a solution's first step uses the prerequisite
                previous = sid
                records.append(
                    Card(
                        id=f"{sid}.ex",
                        kind="example",
                        skill_id=sid,
                        tier=1,
                        question_md="Worked example.",
                        solution_md="Steps.",
                    )
                )
                if flashcards:
                    records.append(
                        Card(
                            id=f"{sid}.fc",
                            kind="flashcard",
                            skill_id=sid,
                            tier=1,
                            front_md="Front",
                            back_md="Back",
                        )
                    )
                for tier in range(1, 6):
                    for seed in range(seeds):
                        records.append(
                            Card(
                                id=f"{sid}.t{tier}.v{seed}",
                                skill_id=sid,
                                tier=tier,
                                template_id=f"{sid}.tmpl{tier}",
                                seed=seed,
                                answer_type="number",
                                answer="1",
                                question_md="Solve.",
                                hints=tuple(f"hint {h + 1}" for h in range(hints)),
                                wrong=(WrongAnswer(answer="7", feedback=FEEDBACK, step=2),),
                                solution=(
                                    SolutionStep(number=1, skill_id=step_one, label="Set up"),
                                    SolutionStep(number=2, skill_id=sid, label="Finish"),
                                ),
                            )
                        )
    return records, skill_ids, section_ids


def make_world(
    tmp_path: Path,
    courses: Sequence[str] = ("ca",),
    *,
    state: str = "learning",
    settings: dict[str, Any] | None = None,
    setup: bool = True,
    **kw: Any,
) -> World:
    """`setup`: each course set up for the planner, starting today (wave 2: a course without
    a setup has no schedule, so nothing of it is planned). The packs have no pace data, so a
    set-up course introduces every skill on its start day."""
    records, skills, sections = world_records(courses, **kw)
    pack = tmp_path / "pack.db"
    build_pack(pack, PackInfo(id="pk", title="Pack", version="1"), records)  # type: ignore[arg-type]
    clock = FixedClock(START, tz=NY)
    paths = ProfilePaths(tmp_path / "profile")
    storage = Storage.open(paths, pack_paths=[pack], clock=clock, create=True)
    users = storage.users
    users.set_setting("study.timezone", "America/New_York")
    for key, value in (settings or {}).items():
        users.set_setting(key, value)
    for section in sections:
        users.set_section_state(section, state)  # type: ignore[arg-type]
    if setup:
        for course in courses:
            users.set_course_setup(CourseSetup(course_id=course, start=START.date()))
    return World(storage, clock, skills, list(courses), sections, paths, [pack])


@contextmanager
def world_ctx(tmp_path: Path, *args: Any, **kw: Any) -> Iterator[World]:
    w = make_world(tmp_path, *args, **kw)
    try:
        yield w
    finally:
        w.storage.close(backup=False)


def timing(active_s: float = 40, solve_s: float | None = None) -> TimingReport:
    active = int(active_s * 1000)
    solve = int((solve_s if solve_s is not None else active_s * 0.8) * 1000)
    return TimingReport(active_ms=active, solve_ms=solve, entry_ms=max(0, active - solve - 500))


def answer(
    service: StudyService, clock: FixedClock, *, correct: bool = True, seconds: int = 40, **kw: Any
) -> Any:
    """Submit the problem on screen (after `seconds` of work) and return the result."""
    clock.advance(seconds=seconds)
    return service.submit(
        {
            "answers": [{"value": "1" if correct else "0"}],
            "timing": {
                "active_ms": seconds * 1000,
                "solve_ms": seconds * 800,
                "entry_ms": seconds * 100,
            },
            **kw,
        }
    )


DAY = 86_400_000


def review_state(
    skill: str,
    now: int,
    *,
    days_ago: float,
    stability: float,
    level: str = "learned",
    relearning: bool = False,
) -> SkillState:
    """A skill in review, last reviewed `days_ago` days before `now`."""
    last = int(now - days_ago * DAY)
    return SkillState(
        skill_id=skill,
        fsrs_state=3 if relearning else 2,
        stability=stability,
        difficulty=5.0,
        last_review_at=last,
        reps=4,
        introduced_at=last - 20 * DAY,
        learned_at=last - 15 * DAY,
        level=level,  # type: ignore[arg-type]
        level_at=last - 15 * DAY,
        level_evidence={"log": []},
    )


def learning_state(skill: str, now: int, *, streak: int = 1, count: int = 2) -> SkillState:
    return SkillState(
        skill_id=skill,
        introduced_at=now - DAY,
        level="learning",
        level_at=now - DAY,
        learning_streak=streak,
        learning_count=count,
        level_evidence={"phase": [[3, now - DAY]], "example_due": False},
    )


# ---------------------------------------------------------------- a scripted planner


def _key(item: WorkItem) -> str:
    return item.problem.problem_id if item.problem is not None else str(item.example_card)


class Script:
    """Stands in for the planner (`PracticeEngine.plan_day`) so a test chooses what is served:
    its items in order, each once a study day (an item the log shows served today is left
    out, the way a re-plan leaves it out). `set_aside`, `notes`, `behind`: what the day's plan
    says. `calls` counts the plans asked for."""

    def __init__(self, svc: StudyService, course: str = "ca") -> None:
        self.svc = svc
        self.course = course
        self.items: list[WorkItem] = []
        self.set_aside: tuple[str, ...] = ()
        self.notes: tuple[str, ...] = ()
        self.behind: tuple[str, ...] = ()
        self.calls = 0
        svc.practice.plan_day = self  # type: ignore[method-assign]

    def problem(self, card_id: str, role: str = "growth", **kw: Any) -> WorkItem:
        """Plan `card_id` (or a part, "card#a") next."""
        catalog = self.svc.practice.catalog()
        spec = catalog.problems.get(card_id) or catalog.by_card[card_id][0]
        item = WorkItem(
            skill_id=kw.pop("skill_id", spec.main_skill),
            role=role,  # type: ignore[arg-type]
            problem=spec,
            example_card=None,
            expected_minutes=spec.standard_minutes,
            priority=kw.pop("priority", 1),
            tier=spec.tier,
            p=kw.pop("p", 0.8),
            reason=kw.pop("reason", "band"),
            **kw,
        )
        self.items.append(item)
        return item

    def example(self, skill: str, card_id: str | None = None) -> WorkItem:
        item = WorkItem(
            skill_id=skill,
            role="new",
            problem=None,
            example_card=card_id or f"{skill}.ex",
            expected_minutes=2.0,
            priority=0,
            block=True,
            reason="example",
        )
        self.items.append(item)
        return item

    def __call__(
        self, day: date, now_ms: int, served: Sequence[tuple[str, ServedItem]] = ()
    ) -> PracticePlan:
        self.calls += 1
        done = {_key(s.item) for _, s in served}
        left = tuple(PlannedItem(self.course, it) for it in self.items if _key(it) not in done)
        plan = SimpleNamespace(
            behind=self.behind, set_aside=self.set_aside, sittings=(), notes=self.notes
        )
        return PracticePlan(
            day=day,
            items=left,
            plans={self.course: cast(Any, plan)},
            minutes=sum(p.item.expected_minutes for p in left),
            hours_to_keep_pace=None,
            hours_basis="none",
            standard_hours=None,
        )
