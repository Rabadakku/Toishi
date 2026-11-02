"""Drive StudyService day after day with a simulated student (queue simulations).

The student answers right with a probability from the skill's recall (0.9 for a skill in
its learning phase), works 40-120 s per problem, may stop early, and taps the first step
of half of his misses in "What went wrong?" (the real diagnosis flow then asks for
checks). `check_hook` is a stand-in for the diagnosis flow, for runs without it.
"""

import random
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Any

from core.engine import GradeResult, ProblemOutcome, SkillContext
from core.model import THIS_ATTEMPT, PendingCheck
from core.queue import Plan, StudyService, Turn
from tests.queue.helpers import NY, World


def check_hook(world: World) -> Callable[[SkillContext, ProblemOutcome, GradeResult], GradeResult]:
    def hook(ctx: SkillContext, outcome: ProblemOutcome, result: GradeResult) -> GradeResult:
        if (
            result.decision.success
            or result.effects.stage != "review"
            or outcome.purpose != "review"
            or "check_id" in outcome.extra
        ):
            return result
        target = ctx.skill.requires[0] if ctx.skill.requires else ctx.skill.id
        check = PendingCheck(
            skill_id=target,
            attempt_id=THIS_ATTEMPT,
            kind="step",
            after_items=3,
            created_at=outcome.at,
        )
        answer = replace(result.answer, changes=(*result.answer.changes, check))
        return replace(result, answer=answer)

    return hook


@dataclass
class DayLog:
    day: date
    count: int
    quotas: dict[str, int]
    free: int
    need: int
    served: Counter[str] = field(default_factory=Counter)
    planned: int = 0
    check_gaps: list[int] = field(default_factory=list)
    reinforcement_gaps: list[int] = field(default_factory=list)
    tags: Counter[str] = field(default_factory=Counter)
    stopped_early: bool = False
    learned: int = 0


@dataclass
class Student:
    world: World
    service: StudyService
    rng: random.Random
    days: list[DayLog] = field(default_factory=list)
    answers: int = 0

    def p_correct(self, skill_id: str | None) -> float:
        if skill_id is None:
            return 0.9
        recall = self.service.engine().recall(skill_id)
        return 0.9 if recall is None else max(0.35, min(0.97, recall))

    def work(self, turn: Turn, *, stop_after: int | None = None) -> Turn:
        """Answer problems until the session ends (or `stop_after` problems)."""
        svc, clock = self.service, self.world.clock
        done = 0
        while turn.type == "problem" and turn.problem is not None:
            if stop_after is not None and done >= stop_after:
                break
            p = turn.problem
            if p.kind == "example":
                clock.advance(seconds=60)
                turn = svc.next()
                continue
            if p.kind == "flashcard":
                clock.advance(seconds=10)
                svc.rate_flashcard(3 if self.rng.random() < 0.9 else 1)
                turn = svc.next()
                continue
            card = self.world.storage.packs.card(p.card.id)
            right = self.rng.random() < self.p_correct(card.skill_id if card else None)
            seconds = self.rng.randint(40, 120)
            clock.advance(seconds=seconds)
            result = svc.submit(
                {
                    "answers": [{"value": "1" if right else "0"}],
                    "timing": {
                        "active_ms": seconds * 1000,
                        "solve_ms": seconds * 800,
                        "entry_ms": seconds * 100,
                    },
                }
            )
            if result.outcome == "retry":
                second = self.rng.random() < 0.5
                clock.advance(seconds=30)
                result = svc.submit(
                    {
                        "answers": [{"value": "1" if second else "0"}],
                        "timing": {
                            "active_ms": (seconds + 30) * 1000,
                            "solve_ms": (seconds + 25) * 1000,
                            "entry_ms": 2000,
                        },
                    }
                )
            if result.outcome == "incorrect":  # half the misses tap the first step
                if self.rng.random() < 0.5:
                    svc.diagnose("step", 1)
                else:
                    svc.diagnose("cant_tell")
            self.answers += 1
            done += 1
            turn = svc.next()
        return turn

    def study_day(self, *, stop_after: int | None = None) -> DayLog:
        svc = self.service
        users = self.world.storage.users
        turn = svc.start()
        session = users.latest_open_session()
        plan = Plan.from_json(session.plan) if session is not None else None
        day = svc.engine().today()
        log = DayLog(
            day=day,
            count=int(plan.info.get("count", 0)) if plan else 0,
            quotas=dict(plan.quotas) if plan else {},
            free=int(plan.info.get("free", 0)) if plan else 0,
            need=int(plan.info.get("need", 0)) if plan else 0,
            planned=plan.slots if plan else 0,
        )
        sid = session.id if session is not None else None
        turn = self.work(turn, stop_after=stop_after)
        log.stopped_early = turn.type == "problem"
        if sid is not None:
            final = Plan.from_json((users.session(sid) or session).plan)  # type: ignore[union-attr]
            self.measure(final, log)
            if turn.type == "problem":
                svc.end()
        self.days.append(log)
        return log

    def measure(self, plan: Plan, log: DayLog) -> None:
        seq = [i for i in plan.items if i.kind != "flashcard" and i.status != "skipped"]
        pos = {i.key: n for n, i in enumerate(seq)}
        for item in seq:
            if item.status != "done":
                continue
            if item.kind == "problem":
                log.served[item.course_id or ""] += 1
                log.tags[item.tag] += 1
            if item.anchor and item.anchor in pos:
                gap = pos[item.key] - pos[item.anchor]
                if item.check_id is not None:
                    log.check_gaps.append(gap)
                elif item.purpose == "reinforcement":
                    log.reinforcement_gaps.append(gap)
            if (item.result or {}).get("learned"):
                log.learned += 1

    def next_day(self, days: int = 1) -> None:
        clock = self.world.clock
        now = clock.now_ms()
        noon = datetime.fromtimestamp(now / 1000, NY).replace(hour=12, minute=0, second=0)
        clock.set(noon + timedelta(days=days))


def run(
    world: World,
    days: int,
    *,
    seed: int = 7,
    stop_on: Callable[[int], int | None] = lambda _d: None,
    skip: Callable[[int], bool] = lambda _d: False,
    stand_in: bool = False,
) -> Student:
    """`stand_in`: the stand-in check hook instead of the real diagnosis flow."""
    service = (
        world.service(diagnosis=False, hooks=(check_hook(world),)) if stand_in else world.service()
    )
    student = Student(world, service, random.Random(seed))  # noqa: S311 - a simulation, not a secret
    for d in range(days):
        if not skip(d):
            student.study_day(stop_after=stop_on(d))
        student.next_day()
    return student


def per_course(days: list[DayLog]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for log in days:
        for course in set(log.quotas) | set(log.served):
            out[course].append(log.served.get(course, 0))
    return dict(out)


def summary(student: Student) -> dict[str, Any]:
    days = student.days
    return {
        "days": len(days),
        "answers": student.answers,
        "check_gaps": sorted(Counter(g for d in days for g in d.check_gaps).items()),
        "reinforcement_gaps": sorted(
            Counter(g for d in days for g in d.reinforcement_gaps).items()
        ),
        "tags": sum((d.tags for d in days), Counter()),
        "served": {c: sum(v) for c, v in per_course(days).items()},
        "learned": sum(d.learned for d in days),
    }
