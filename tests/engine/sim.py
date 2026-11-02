"""A simulation harness: simulated students with known forgetting and speed curves.

The truth model is FSRS-6 itself, driven by the true outcomes (Good or Again), with the
student's true recall R(t, scale x S_true): scale 1.0 is a student the default model
describes exactly; scale < 1 forgets faster than predicted. Solve times follow a power law
of practice with log-normal noise. The study loop uses only the engine's pure API:
due_skills, plan_boosters, new_skill_room, pick_problem, grade_answer.
"""

import math
import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from core.engine import (
    AnswerFacts,
    BoostTarget,
    EngineSettings,
    FsrsAdapter,
    Memory,
    ProblemOutcome,
    SeenIndex,
    SkillContext,
    StudyDays,
    TimingFacts,
    core_band,
    due_skills,
    grade_answer,
    new_skill_room,
    pick_problem,
    plan_boosters,
    scheduled_load,
    stretch_tier,
)
from core.engine.config import AGAIN, GOOD
from core.engine.grading import GradeResult
from core.engine.level import checkup_candidates, checkup_due
from core.engine.lifecycle import (
    FAILED_PHASES,
    due_day,
    in_learning_phase,
    learning_step,
    memory_of,
    review_on,
)
from core.engine.selection import stretch_allowed, wants_stretch
from core.model import Attempt, CardRef, CardUser, Skill, SkillState, SkillTierState


@dataclass(frozen=True, slots=True)
class Student:
    name: str
    scale: float = 1.0  # true stability = scale x FSRS stability
    learn_p: tuple[float, ...] = (0.6, 0.8, 0.9, 0.95)  # k-th learning problem
    base_ms: Mapping[int, float] = field(
        default_factory=lambda: {1: 30_000, 2: 55_000, 3: 90_000, 4: 140_000, 5: 200_000}
    )
    speedup: float = 0.25
    noise: float = 0.2
    stretch_penalty: float = 0.8
    slip: float = 0.0  # share of recalled review answers lost to a careless slip (Hard)


@dataclass
class Log:
    reviews: list[tuple[str, date, int, float | None, float]] = field(default_factory=list)
    # (skill, day, rating, engine predicted recall, true recall)
    per_day: dict[date, int] = field(default_factory=lambda: defaultdict(int))
    rated_per_day: dict[date, int] = field(default_factory=lambda: defaultdict(int))
    level_changes: list[tuple[str, date, str | None, str | None]] = field(default_factory=list)
    demotions: int = 0
    boosters_done: int = 0
    learned_at: dict[str, date] = field(default_factory=dict)
    # (skill, successes in a row since learning or the last lapse, scheduled interval)
    intervals: list[tuple[str, int, int]] = field(default_factory=list)
    # A clean learning phase (three Goods) that was the skill's first phase ...
    clean_learning_intervals: list[int] = field(default_factory=list)
    # ... and one that passed after a failed phase: (interval, the interval that replaying
    # the whole learning block through the FSRS adapter gives) (C3/C6).
    clean_after_failed_intervals: list[tuple[int, int]] = field(default_factory=list)
    relearn_intervals: list[int] = field(default_factory=list)


class World:
    def __init__(
        self,
        student: Student,
        skills: Sequence[str],
        *,
        start: date,
        days: StudyDays,
        seed: int = 0,
        settings: EngineSettings | None = None,
        retention: float = 0.90,
        exam_problem_ms: int | None = 255_000,
        targets: Sequence[BoostTarget] = (),
        boosters: bool = True,
        new_per_day: int = 4,
    ) -> None:
        self.student = student
        self.skills = {k: Skill(id=k, name=k, section_id="sim.sec", exam_tier=3) for k in skills}
        self.order = list(skills)
        self.start = start
        self.days = days
        self.rng = random.Random(seed)  # noqa: S311
        self.settings = settings or EngineSettings(daily_problems=20)
        self.retention = retention
        self.exam_problem_ms = exam_problem_ms
        self.targets = list(targets)
        self.boosters = boosters
        self.new_per_day = new_per_day
        self.fsrs = FsrsAdapter()
        self.truth_model = FsrsAdapter(fuzz=False)
        self.states: dict[str, SkillState] = {}
        self.tiers: dict[str, dict[int, SkillTierState]] = defaultdict(dict)
        self.history: dict[str, list[Attempt]] = defaultdict(list)
        self.cards: dict[str, CardUser] = {}
        self.truth: dict[str, Memory] = {}
        self.practice: dict[str, int] = defaultdict(int)
        self.learning_answers: dict[str, int] = defaultdict(int)
        self.streak: dict[str, int] = defaultdict(int)
        self.refs = {k: self._refs(k) for k in skills}
        self.log = Log()
        self.last_checkup: date | None = None
        self.next_id = 1

    # ------------------------------------------------------------ the student

    def _refs(self, skill: str) -> list[CardRef]:
        def ref(
            card_id: str, kind: str, tier: int, template: str | None, seed: int | None
        ) -> CardRef:
            return CardRef(
                id=card_id,
                rev=1,
                kind=kind,  # type: ignore[arg-type]
                skill_id=skill,
                tier=tier,
                template_id=template,
                seed=seed,
                status="active",
                cue_required=False,
                has_cued_question=False,
                source="sim",
            )

        out = [ref(f"{skill}.ex", "example", 1, None, None)]
        for tier in range(1, 6):
            for m in range(3):
                template = f"{skill}.t{tier}.m{m}"
                out += [
                    ref(f"{template}.{seed}", "problem", tier, template, seed) for seed in range(40)
                ]
        return out

    def true_recall(self, skill: str, at: int) -> float:
        memory = self.truth.get(skill)
        if memory is None:
            return 0.0
        scaled = Memory(
            memory.stability * self.student.scale, memory.difficulty, memory.last_review_at
        )
        return self.truth_model.retrievability(scaled, at)

    def solve_ms(self, skill: str, tier: int) -> int:
        n = self.practice[skill]
        base = float(self.student.base_ms[tier]) * float((1 + n) ** (-self.student.speedup))
        return max(3_000, round(base * math.exp(self.rng.gauss(0, self.student.noise))))

    # ------------------------------------------------------------ one problem

    def ctx(self, skill: str, card_id: str, exam_window: bool = False) -> SkillContext:
        return SkillContext(
            skill=self.skills[skill],
            state=self.states.get(skill),
            tiers=dict(self.tiers[skill]),
            history=tuple(self.history[skill]),
            card_user=self.cards.get(card_id),
            retention=self.retention,
            exam_window=exam_window,
            exam_problem_ms=self.exam_problem_ms,
        )

    def serve(
        self,
        skill: str,
        at: int,
        *,
        purpose: str = "review",
        stretch: bool = False,
        tiers: tuple[int, ...] | None = None,
        force_wrong: bool = False,
    ) -> GradeResult:
        state = self.states.get(skill)
        memory = memory_of(state)
        learning = in_learning_phase(state)
        if tiers is None:
            tiers = (1, 2) if learning else core_band(memory.stability if memory else None)
        stretch_used = False
        if stretch and not learning:
            tier = stretch_tier(memory.stability if memory else None, elite=True)
            if tier is not None:
                tiers, stretch_used = (tier,), True
        seen = SeenIndex.from_attempts(self.history[skill])
        theta = state.elo_theta if state else 0.0
        pick = pick_problem(
            self.refs[skill], theta=theta, tiers=tiers, now_ms=at, seen=seen, stretch=stretch_used
        )
        assert pick is not None
        ref = pick.card
        if learning:
            k = self.learning_answers[skill]
            p = self.student.learn_p[min(k, len(self.student.learn_p) - 1)]
            self.learning_answers[skill] += 1
        else:
            p = self.true_recall(skill, at) * (
                self.student.stretch_penalty if stretch_used else 1.0
            )
        recalled = (not force_wrong) and self.rng.random() < p
        slipped = (
            recalled and not learning and self.student.slip > 0
        ) and self.rng.random() < self.student.slip
        correct = recalled and not slipped
        solve = self.solve_ms(skill, ref.tier)
        outcome = ProblemOutcome(
            card=ref,
            facts=AnswerFacts(correct=correct, slip_within_cap=slipped),
            at=at,
            timing=TimingFacts(solve_ms=solve, active_ms=solve + 6_000, expected_chars=4),
            purpose=purpose,  # type: ignore[arg-type]
            stretch=stretch_used if not learning else None,
        )
        failed_phases = [
            (int(r), int(t))
            for r, t in (state.level_evidence if state else {}).get(FAILED_PHASES, [])
        ]
        result = grade_answer(
            self.ctx(skill, ref.id),
            outcome,
            settings=self.settings,
            adapter=self.fsrs,
            days=self.days,
        )
        self.apply(skill, result)
        self.practice[skill] += 1
        day = self.days.day_of(at)
        self.log.per_day[day] += 1
        if result.answer.reviews and result.state.due_at is not None:
            interval = (self.days.day_of(result.state.due_at) - day).days
            ratings = [e.rating for e in result.answer.reviews]
            if result.effects.learned:
                self.streak[skill] = 0
                if ratings == [GOOD, GOOD, GOOD] and not failed_phases:
                    self.log.clean_learning_intervals.append(interval)
                elif ratings == [GOOD, GOOD, GOOD]:
                    block = [*failed_phases, *((e.rating, e.at) for e in result.answer.reviews)]
                    memory = self.fsrs.replay(block, self.days)
                    assert memory is not None
                    whole = replace(
                        result.state,
                        stability=memory.stability,
                        difficulty=memory.difficulty,
                        last_review_at=memory.last_review_at,
                    )
                    expected = due_day(whole, self.retention, self.fsrs, self.days)
                    assert expected is not None
                    self.log.clean_after_failed_intervals.append((interval, (expected - day).days))
            elif ratings[-1] == AGAIN:
                self.streak[skill] = 0
                self.log.relearn_intervals.append(interval)
            else:
                self.streak[skill] += 1
                self.log.intervals.append((skill, self.streak[skill], interval))
        # The truth follows the true outcome.
        if result.effects.learned:
            replayed = [(e.rating, e.at) for e in result.answer.reviews]
            self.truth[skill] = self.truth_model.replay(
                [(GOOD if r > AGAIN else AGAIN, t) for r, t in replayed]
            )  # type: ignore[assignment]
            self.log.learned_at.setdefault(skill, day)  # the first time
        elif (
            result.effects.stage in ("review", "stretch")
            and skill in self.truth
            and result.answer.reviews
        ):
            if result.effects.stage == "review":
                event = result.answer.reviews[0]
                self.log.reviews.append((skill, day, event.rating, event.predicted_recall, p))
            self.log.rated_per_day[day] += 1
            self.truth[skill] = review_on(
                self.truth_model, self.truth[skill], GOOD if recalled else AGAIN, at, self.days
            )
        elif result.effects.leech or result.effects.provisional_demoted:
            self.truth.pop(skill, None)
        if result.effects.level_before != result.effects.level_after:
            self.log.level_changes.append(
                (skill, day, result.effects.level_before, result.effects.level_after)
            )
        if result.effects.demoted:
            self.log.demotions += 1
        return result

    def apply(self, skill: str, result: GradeResult) -> None:
        for change in result.answer.changes:
            if isinstance(change, SkillState):
                self.states[skill] = change
            elif isinstance(change, SkillTierState):
                self.tiers[skill][change.tier] = change
            elif isinstance(change, CardUser):
                self.cards[change.card_id] = change
        self.history[skill].append(replace(result.answer.attempt, id=self.next_id))
        self.next_id += 1

    # ------------------------------------------------------------ one day

    def learn(self, skill: str, at: int) -> int:
        """Run a learning block; returns the time after it."""
        state = self.states.get(skill)
        if learning_step(state, self.days.day_of(at)) in ("example", "none"):
            example = self.refs[skill][0]
            outcome = ProblemOutcome(
                card=example, facts=AnswerFacts(correct=False), at=at, verdict="shown"
            )
            self.apply(
                skill,
                grade_answer(
                    self.ctx(skill, example.id),
                    outcome,
                    settings=self.settings,
                    adapter=self.fsrs,
                    days=self.days,
                ),
            )
        for _ in range(self.settings.max_learning_problems):
            at += 90_000
            result = self.serve(skill, at)
            if result.effects.learned or result.effects.learning_failed:
                break
        return at

    def run_day(self, day: date, *, force_wrong: frozenset[str] = frozenset()) -> None:
        at = self.days.moment(day)

        def retention_of(_skill: str) -> float:
            return self.retention

        due = due_skills(
            self.states.values(), day, retention_of=retention_of, adapter=self.fsrs, days=self.days
        )
        items: list[tuple[str, str]] = [(d.skill_id, "review") for d in due]
        if self.boosters and self.targets:
            plan = plan_boosters(
                self.targets,
                self.states,
                today=day,
                retention_of=retention_of,
                adapter=self.fsrs,
                days=self.days,
            )
            due_ids = {d.skill_id for d in due}
            items += [
                (b.skill_id, "booster") for b in plan.due_on(day) if b.skill_id not in due_ids
            ]
        if (
            checkup_due(self.last_checkup, day, self.settings.checkup_every_weeks)
            and day > self.start
        ):
            due_days = {
                k: due_day(s, self.retention, self.fsrs, self.days) for k, s in self.states.items()
            }
            last = {
                k: self.days.day_of(s.last_review_at)
                for k, s in self.states.items()
                if s.last_review_at
            }
            picked = checkup_candidates(
                list(self.states.values()), today=day, due_days=due_days, day_of_review=last
            )
            items += [(k, "checkup") for k in picked]
            self.last_checkup = day
        stretches = 0
        for reviews, (skill, purpose) in enumerate(items):
            at += 120_000
            want = (
                wants_stretch(skill, day.isoformat(), self.settings.stretch_fraction)
                and purpose == "review"
            )
            stretch = want and stretch_allowed(
                reviews_so_far=reviews,
                stretches_so_far=stretches,
                elite_used=False,
                tier=4,
                fraction=self.settings.stretch_fraction,
            )
            result = self.serve(
                skill, at, purpose=purpose, stretch=stretch, force_wrong=skill in force_wrong
            )
            stretches += int(result.effects.stage == "stretch")
            if purpose == "booster":
                self.log.boosters_done += 1
            if result.effects.reinforcement_due:
                at += 120_000
                self.serve(skill, at, purpose="reinforcement")
            if result.effects.core_followup_due:
                at += 120_000
                self.serve(skill, at)
        # Learning blocks: restarts first, then new skills while the projected load allows.
        restarts = [
            k for k, s in self.states.items() if learning_step(s, day) in ("example", "problem")
        ]
        load = scheduled_load(
            self.states.values(),
            day,
            7,
            retention_of=retention_of,
            adapter=self.fsrs,
            days=self.days,
        )
        room = new_skill_room(
            load, daily_count=self.settings.daily_problems, max_new=self.new_per_day
        )
        fresh = [k for k in self.order if k not in self.states][: max(0, room - len(restarts))]
        for skill in [*restarts, *fresh]:
            # The queue cuts new skills first when the day is full (order 7).
            if self.log.per_day[day] + 4 > self.settings.daily_problems:
                break
            at = self.learn(skill, at + 120_000)

    def run(self, n_days: int, **kw: frozenset[str]) -> None:
        for i in range(n_days):
            self.run_day(self.start + timedelta(days=i), **kw)
