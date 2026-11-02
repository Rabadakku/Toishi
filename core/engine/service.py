"""Engine: the storage-bound facade over the pure engine functions.

It loads rows from a Storage, calls the pure functions, and writes through UserStore
(one transaction per graded answer). It keeps no state of its own, so one instance per
thread (or per call) is fine; every method reads fresh rows.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from core.engine.boosters import BoosterPlan, BoostTarget, booster_targets, plan_boosters
from core.engine.calibration import (
    CalibrationReport,
    FitOffer,
    TrueRetention,
    calibration_by_course,
    calibration_series,
    fit_offer,
    true_retention,
)
from core.engine.config import (
    BOOSTER_WINDOW_DAYS,
    DAY_MS,
    ELO_TARGET_P,
    FIT_EVERY_DAYS,
    FIT_GROWTH,
    FIT_MIN_ITEMS,
    EngineSettings,
)
from core.engine.days import StudyDays
from core.engine.fitting import Adoption, HeldOut, adoption, held_out
from core.engine.fitting import fit as fit_items
from core.engine.fsrs_adapter import (
    FsrsAdapter,
    ParameterError,
    clean_parameters,
    params_id_for,
)
from core.engine.goals import Catalog, hardest_tier, retention_map, skill_retention
from core.engine.grading import (
    GradeHook,
    GradeResult,
    ProblemOutcome,
    SkillContext,
    grade_answer,
    record_try,
)
from core.engine.histories import (
    History,
    Item,
    Kind,
    TargetKey,
    annotate_answer,
    annotation_of,
    build_histories,
    failed_phase_events,
    last_histories,
    target_key,
    training_items,
)
from core.engine.lifecycle import BALANCE_DAYS, Provisional, in_learning_phase, memory_of
from core.engine.param_sets import (
    DECK_GROUPS_SETTING,
    ParameterSet,
    deck_group_of,
    domain_of,
    fit_log_key,
    history_key,
    load_set,
    params_key,
    recomputed_key,
    set_id_for,
    stored_value,
    with_entry,
)
from core.engine.param_sets import history as set_history
from core.engine.placement import apply_seeds
from core.engine.projection import ExamProjection, LoadProjection, project_exam, project_load
from core.engine.recompute import fsrs_problems, rebuild, recompute_all, recomputed
from core.engine.schedule import DueSkill, due_skills, scheduled_load
from core.engine.selection import (
    Pick,
    SeenIndex,
    core_band,
    learning_pool_size,
    pick_problem,
    stretch_tier,
)
from core.engine.timing import computed_target_ms, exam_problem_ms, next_target
from core.model import (
    Attempt,
    AttemptVoid,
    CardRef,
    CourseGoal,
    Exam,
    FlashcardState,
    GradedAnswer,
    LevelName,
    ReviewEvent,
    SessionState,
    Skill,
    SkillState,
    TargetKind,
    VoidReason,
)
from core.storage import Storage, rows
from core.storage.user_store import UndoResult


@dataclass(frozen=True, slots=True)
class Recorded:
    attempt: Attempt  # as stored (id, snapshots)
    result: GradeResult


@dataclass(frozen=True, slots=True, kw_only=True)
class Recomputed:
    """C3: rows whose memory was rebuilt from the log, and the void row that logged it."""

    changed: tuple[SkillState | FlashcardState, ...]
    void: AttemptVoid | None


@dataclass(frozen=True, slots=True, kw_only=True)
class FitDecision:
    """A fitted candidate judged against the set in force (C2), not yet written."""

    set_id: str
    decision: Adoption
    items: int
    imported: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class FitReport:
    """One guarded fit (C2, I7): the decision, the items and what recompute changed."""

    set_id: str
    decision: Adoption
    items: int
    recomputed: Recomputed | None = None

    @property
    def adopted(self) -> bool:
        return self.decision.adopted


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckReport:
    """I6: rows with impossible FSRS fields, and the repair through C3."""

    problems: dict[str, list[str]]  # "skill:<id>" / "flashcard:<id>:<ord>" -> what's wrong
    repaired: Recomputed


@dataclass(frozen=True, slots=True, kw_only=True)
class CalibrationStats:
    """I8: data for the stats screen (no UI yet)."""

    by_course: dict[str, CalibrationReport]
    series: dict[str, CalibrationReport]
    true_retention: TrueRetention
    items: int
    held_out: HeldOut | None  # above 300 items, when asked for


class Engine:
    def __init__(
        self,
        storage: Storage,
        *,
        hooks: Sequence[GradeHook] = (),
        adapter: FsrsAdapter | None = None,
    ) -> None:
        self._storage = storage
        self._hooks = tuple(hooks)
        self._adapter = adapter

    # ------------------------------------------------------------ wiring

    def settings(self) -> EngineSettings:
        return EngineSettings.from_settings(self._storage.users.settings())

    def days(self) -> StudyDays:
        users = self._storage.users
        return StudyDays(users.timezone(), users.rollover_hour())

    def adapter(self) -> FsrsAdapter:
        """The adapter for skills of the default domain (parameter set "skills")."""
        return self.adapter_for("skill")

    def adapter_for(self, kind: TargetKind = "skill", group: str | None = None) -> FsrsAdapter:
        """Decision 6: the adapter of a parameter set. kind "skill": `group` is a domain
        (None: courses with no domain); kind "flashcard": `group` is an imported Anki deck
        group (None: plain flashcards). Flashcards use the defaults until their own fit."""
        return self._adapter_of_set(set_id_for(kind, group))

    def adapter_for_skill(self, skill_id: str) -> FsrsAdapter:
        return self._adapter_of_set(self.set_of_skill(skill_id))

    def skill_adapters(self) -> Callable[[str], FsrsAdapter]:
        """skill id -> its set's adapter, with settings read now (decision 6); for code that
        schedules many skills at once."""
        sets = self._sets()
        return lambda skill_id: sets.adapter(sets.skill(skill_id))

    def adapter_for_card(self, card_id: str) -> FsrsAdapter:
        """The adapter for a flashcard or cloze card (its Anki deck group's, if any)."""
        return self._adapter_of_set(self.set_of_card(card_id))

    def _adapter_of_set(
        self, set_id: str, settings: Mapping[str, Any] | None = None
    ) -> FsrsAdapter:
        if self._adapter is not None:
            return self._adapter.with_days(self.days())  # one clock: the profile's days
        values = self._storage.users.settings() if settings is None else settings
        found = load_set(values, set_id)
        return FsrsAdapter(
            found.parameters,
            maximum_interval_days=EngineSettings.from_settings(values).maximum_interval_days,
            params_id=found.params_id,
            days=self.days(),
        )

    def parameter_set(self, set_id: str) -> ParameterSet:
        """The set in force; `notice` says when stored parameters were unusable (C1)."""
        return load_set(self._storage.users.settings(), set_id)

    def set_of_skill(self, skill_id: str) -> str:
        return self._sets().skill(skill_id)

    def set_of_card(self, card_id: str) -> str:
        return self._sets().card(card_id)

    def _sets(self) -> _Sets:
        return _Sets(self, self._storage.users.settings())

    def catalog(self) -> Catalog:
        packs = self._storage.packs
        return Catalog.build(packs.skills(), packs.sections(), packs.units())

    def goals(self) -> dict[str, CourseGoal]:
        return {g.course_id: g for g in self._storage.users.course_goals()}

    def today(self) -> date:
        return self.days().day_of(self._now())

    def _now(self) -> int:
        return self._storage.db.clock.now_ms()

    # ------------------------------------------------------------ per skill

    def retention(self, skill_id: str, day: date | None = None) -> float:
        return skill_retention(skill_id, day or self.today(), self.catalog(), self.goals())

    def _exam_info(self, skill_id: str, day: date, catalog: Catalog) -> tuple[bool, int | None]:
        """(in an exam window, exam problem time) for a skill on a day."""
        days = self.days()
        course = catalog.course_of(skill_id)
        window = False
        best: Exam | None = None
        for exam in sorted(self._storage.users.exams(), key=lambda e: e.at):
            exam_day = days.day_of(exam.at)
            in_scope = (
                skill_id in catalog.skills_in_sections(exam.sections)
                if exam.sections
                else exam.course_id is not None and exam.course_id == course
            )
            if in_scope and 0 <= (exam_day - day).days <= BOOSTER_WINDOW_DAYS:
                window = True
            timed = exam.course_id == course and bool(exam.minutes and exam.problems)
            if timed and (best is None or exam_day >= day):
                best = exam
                if exam_day >= day:
                    break
        return window, exam_problem_ms(best)

    def context(
        self, skill_id: str, *, card_id: str | None = None, at_ms: int | None = None
    ) -> SkillContext:
        users, packs = self._storage.users, self._storage.packs
        skill = packs.skill(skill_id)
        if skill is None:
            raise KeyError(f"unknown skill {skill_id!r}")
        day = self.days().day_of(at_ms if at_ms is not None else self._now())
        catalog = self.catalog()
        window, exam_ms = self._exam_info(skill_id, day, catalog)
        return SkillContext(
            skill=skill,
            state=users.skill_state(skill_id),
            tiers={t.tier: t for t in users.skill_tiers(skill_id)},
            history=users.attempts(skill_id=skill_id),
            card_user=users.card_user(card_id) if card_id else None,
            retention=skill_retention(skill_id, day, catalog, self.goals()),
            exam_window=window,
            exam_problem_ms=exam_ms,
            learning_pool=self._learning_pool(skill, users.card_marks()),
        )

    def _learning_pool(
        self, skill: Skill, marks: Mapping[str, Any], refs: Sequence[CardRef] | None = None
    ) -> int:
        """Distinct tier 1-2 problems the skill's learning phase can serve (ENG-2)."""
        hidden = {k for k, m in marks.items() if m.hidden or m.suspended}
        if refs is None:
            refs = self._storage.packs.card_refs(skill_id=skill.id)
        kinds = ("method", "problem") if skill.method_choice else ("problem",)
        return learning_pool_size(refs, hidden=hidden, kinds=kinds)

    def unseen_today(self, skill_id: str) -> int:
        """The skill's learning-pool problems not served yet this study day (a card is
        never served twice in a study day)."""
        skill = self._storage.packs.skill(skill_id)
        if skill is None:
            return 0
        users = self._storage.users
        today = self.days().start(self.days().day_of(self._now()))
        seen = {k for k, v in users.card_users().items() if (v.last_seen_at or 0) >= today}
        refs = [r for r in self._storage.packs.card_refs(skill_id=skill_id) if r.id not in seen]
        return self._learning_pool(skill, users.card_marks(), refs)

    def small_learning_pools(self) -> dict[str, int]:
        """Skills whose learning pool is smaller than the learning phase's run of correct
        answers (ENG-2), with their pool size: the Library flags them ("pool too small").
        Such a skill is learned after every one of its problems in a row."""
        users, packs = self._storage.users, self._storage.packs
        need = self.settings().correct_in_a_row
        marks = users.card_marks()
        by_skill: dict[str, list[CardRef]] = defaultdict(list)
        for ref in packs.card_refs():
            if ref.skill_id:
                by_skill[ref.skill_id].append(ref)
        out: dict[str, int] = {}
        for skill_id, skill in self.catalog().skills.items():
            pool = self._learning_pool(skill, marks, by_skill.get(skill_id, []))
            if pool < need:
                out[skill_id] = pool
        return out

    def grade(self, outcome: ProblemOutcome) -> Recorded:
        """Grade the final submission of a problem and commit it (one transaction)."""
        skill_id = outcome.card.skill_id or ""
        ctx = self.context(skill_id, card_id=outcome.card.id, at_ms=outcome.at)
        days = self.days().pin(ctx.history)  # ENG-23: past reviews keep their stored days
        adapter = self.adapter_for_skill(skill_id) if ctx.skill else self.adapter()
        adapter = adapter.with_days(days)
        easy = self._storage.users.settings().get("queue.easy_days") or {}
        ctx = replace(
            ctx,
            load=self._load(ctx.skill.id, self.days().day_of(outcome.at)),
            easy_days=easy if isinstance(easy, dict) else {},
        )
        result = grade_answer(
            ctx,
            outcome,
            settings=self.settings(),
            adapter=adapter,
            days=days,
            hooks=self._hooks,
        )
        answer = self._annotated(ctx, outcome, result, adapter)
        return Recorded(self._storage.users.record_answer(answer), replace(result, answer=answer))

    def _annotated(
        self,
        ctx: SkillContext,
        outcome: ProblemOutcome,
        result: GradeResult,
        adapter: FsrsAdapter,
    ) -> GradedAnswer:
        """C4 and C6 annotations: whole-day recall beside the logged (fractional) one, the
        failed learning phase as prefix-only events, explicit block starts."""
        extra: list[ReviewEvent] = []
        if result.effects.learning_failed and ctx.state is not None:
            phase = [*ctx.state.level_evidence.get("phase", [])]
            rating = result.answer.attempt.rating
            if rating is not None:
                phase.append([rating, outcome.at])
            extra = failed_phase_events(
                ctx.skill.id, phase, params_id=adapter.params_id, retention=ctx.retention
            )
        memory = memory_of(ctx.state)
        return annotate_answer(
            result.answer,
            stage=result.effects.stage,
            previous_kind=self._last_kind,
            extra_events=extra,
            recall_days=None if memory is None else adapter.recall_days(memory, outcome.at),
            card_before=memory is not None,
        )

    def _last_kind(self, key: TargetKey) -> Kind | None:
        users = self._storage.users
        events = users.review_events(target_kind=key[0], target_id=key[1])
        events = [e for e in events if e.target_ord == key[2]]
        if not events:
            return None
        last = max(events, key=lambda e: (e.at, e.id or 0))
        attempt = users.attempt(last.attempt_id) if last.attempt_id is not None else None
        note = annotation_of(last, attempt)
        if note is not None and note.get("kind"):
            return note["kind"]  # type: ignore[no-any-return]
        if (last.state_before or {}).get("stability") is None:
            return "learning"
        return "review"

    def _load(self, skill_id: str, day: date) -> dict[date, int]:
        """Reviews of the other skills due per study day, for the load balancer (I3)."""
        states = {k: v for k, v in self._states().items() if k != skill_id}
        retention = self._retention_of(day, list(states))
        return scheduled_load(
            states.values(),
            day,
            BALANCE_DAYS,
            retention_of=lambda k: retention.get(k, 0.90),
            adapter=self.adapter(),
            days=self.days(),
            adapter_of=self.skill_adapters(),
        )

    def record_try(self, outcome: ProblemOutcome) -> Attempt:
        ctx = self.context(outcome.card.skill_id or "", at_ms=outcome.at)
        return self._storage.users.record_answer(record_try(ctx, outcome))

    def pick_problem(
        self,
        skill_id: str,
        *,
        stretch: bool = False,
        lighter_set: bool = False,
        last_card_id: str | None = None,
        at_ms: int | None = None,
        kinds: Sequence[str] | None = None,
        tiers: Sequence[int] | None = None,
    ) -> Pick | None:
        """A problem for a skill: its core band (tiers 1-2 while learning or in a Lighter
        set, tier 3 in an exam window), or its stretch tier when the queue asks for one.
        `kinds`: card kinds to pick from; by default full problems, and which-method items
        for a method-choice skill (ENG-16: its reviews are which-method items). A rated
        review aims Elo at the course's desired retention, so success at due time matches
        what the schedule targets; learning phases and stretch problems aim at 0.80
        (ADR-0014, Decision 5). `tiers`: these tiers instead (ENG-2: the tier 1 problem
        shown solved when the skill has no example card); nothing is rated from it."""
        users, packs = self._storage.users, self._storage.packs
        now = at_ms if at_ms is not None else self._now()
        ctx = self.context(skill_id, at_ms=now)
        memory = memory_of(ctx.state)
        goal = self.goals().get(self.catalog().course_of(skill_id) or "")
        hardest = hardest_tier(goal, self.days().day_of(now))
        settings = self.settings()
        if tiers is not None:
            stretch = False
        elif in_learning_phase(ctx.state) or lighter_set:
            tiers = (1, 2)
            stretch = False
        else:
            tiers = core_band(memory.stability if memory else None, exam_window=ctx.exam_window)
            if stretch:
                tier = stretch_tier(memory.stability if memory else None, elite=settings.elite)
                if tier is None or tier > hardest or ctx.exam_window:
                    stretch = False
                else:
                    tiers = (tier,)
        tiers = tuple(t for t in tiers if t <= hardest) or (min(tiers),)
        rated = not in_learning_phase(ctx.state) and not stretch
        marks = users.card_marks()
        hidden = {k for k, m in marks.items() if m.hidden or m.suspended}
        refs = packs.card_refs(skill_id=skill_id)
        last = next((r for r in refs if r.id == last_card_id), None) if last_card_id else None
        seen = SeenIndex.from_attempts(
            ctx.history,
            {k: v.last_seen_at for k, v in users.card_users().items() if v.last_seen_at},
        )
        theta = ctx.state.elo_theta if ctx.state else 0.0
        if kinds is None:
            kinds = ("method", "problem") if ctx.skill.method_choice else ("problem",)
        return pick_problem(
            refs,
            theta=theta,
            tiers=tiers,
            now_ms=now,
            seen=seen,
            last=last,
            hidden=hidden,
            stretch=stretch,
            kinds=tuple(kinds),
            target_p=ctx.retention if rated else ELO_TARGET_P,
            # Never a card already served this study day (hand test 3): a skipped slot is
            # better than the same problem minutes after its solution was shown.
            today_start_ms=self.days().start(self.days().day_of(now)),
        )

    def recall(self, skill_id: str, at_ms: int | None = None) -> float | None:
        memory = memory_of(self._storage.users.skill_state(skill_id))
        if memory is None:
            return None
        at = at_ms if at_ms is not None else self._now()
        return self.adapter_for_skill(skill_id).retrievability(memory, at)

    def recall_on(self, skill_id: str, day: date) -> float | None:
        return self.recall(skill_id, self.days().moment(day))

    def level(self, skill_id: str) -> LevelName | None:
        state = self._storage.users.skill_state(skill_id)
        return None if state is None else state.level

    def target_time(self, skill_id: str, tier: int) -> int | None:
        """The target solve time now (recomputed live from the logs and the next exam)."""
        rows = {t.tier: t for t in self._storage.users.skill_tiers(skill_id)}
        row = rows.get(tier)
        _, exam_ms = self._exam_info(skill_id, self.today(), self.catalog())
        computed = computed_target_ms(tier, row.first_correct_ms if row else (), exam_ms)
        return next_target(row, computed, self._now())[0]

    # ------------------------------------------------------------ many skills

    def _states(self) -> dict[str, SkillState]:
        return self._storage.users.skill_states()

    def _retention_of(self, day: date, skill_ids: Sequence[str]) -> Mapping[str, float]:
        return retention_map(skill_ids, day, self.catalog(), self.goals())

    def due_skills(self, day: date | None = None) -> list[DueSkill]:
        day = day or self.today()
        states = self._states()
        catalog = self.catalog()
        retention = self._retention_of(day, list(states))
        sections = self._storage.users.section_states()

        def active(skill_id: str) -> bool:
            skill = catalog.skills.get(skill_id)
            if skill is None or skill.section_id is None:
                return True
            row = sections.get(skill.section_id)
            return row is None or row.state != "off"

        out: list[DueSkill] = []
        for adapter, group in self._by_set(states.values()):
            out += due_skills(
                group,
                day,
                retention_of=lambda k: retention.get(k, 0.90),
                adapter=adapter,
                days=self.days(),
                longest_wait_days=self.settings().longest_wait_days,
                active=active,
            )
        out.sort(key=lambda d: (-d.days_overdue, d.recall, d.skill_id))
        return out

    def _by_set(self, states: Sequence[SkillState] | Any) -> list[tuple[FsrsAdapter, list[Any]]]:
        """Skill states grouped by parameter set, each with its adapter (decision 6)."""
        sets = self._sets()
        groups: dict[str, list[SkillState]] = defaultdict(list)
        for state in states:
            groups[sets.skill(state.skill_id)].append(state)
        return [(self._adapter_of_set(k, sets.values), v) for k, v in sorted(groups.items())]

    def _targets(self, day: date, window: int | None = BOOSTER_WINDOW_DAYS) -> list[BoostTarget]:
        return booster_targets(
            self._storage.users.exams(),
            self.goals(),
            self.catalog(),
            today=day,
            days=self.days(),
            window_days=window if window is not None else 10_000,
        )

    def booster_plan(self, day: date | None = None) -> BoosterPlan:
        day = day or self.today()
        states = self._states()
        retention = self._retention_of(day, list(states))
        adapter, days = self.adapter(), self.days()
        adapter_of = self.skill_adapters()
        load = scheduled_load(
            states.values(),
            day,
            BOOSTER_WINDOW_DAYS + 1,
            retention_of=lambda k: retention.get(k, 0.90),
            adapter=adapter,
            days=days,
            adapter_of=adapter_of,
        )
        return plan_boosters(
            self._targets(day),
            states,
            today=day,
            retention_of=lambda k: retention.get(k, 0.90),
            adapter=adapter,
            days=days,
            base_load=load,
            adapter_of=adapter_of,
        )

    def exam_projection(self, exam_id: int, day: date | None = None) -> ExamProjection | None:
        day = day or self.today()
        targets = [t for t in self._targets(day, window=None) if t.key == f"exam:{exam_id}"]
        if not targets:
            return None
        states = self._states()
        retention = self._retention_of(day, list(states))
        plan = plan_boosters(
            targets,
            states,
            today=day,
            retention_of=lambda k: retention.get(k, 0.90),
            adapter=self.adapter(),
            days=self.days(),
            adapter_of=self.skill_adapters(),
        )
        return project_exam(plan.outlooks[0], states, today=day) if plan.outlooks else None

    def adapter_for_course(self, course_id: str | None) -> FsrsAdapter:
        values = self._storage.users.settings()
        return self._adapter_of_set(set_id_for("skill", domain_of(values, course_id)), values)

    def course_load(
        self, course_id: str, *, horizon_days: int = 28, minutes_per_problem: float = 2.5
    ) -> LoadProjection:
        """LIB-4: the goal's projected daily load for one course."""
        day = self.today()
        catalog = self.catalog()
        skill_ids = catalog.skills_of_course(course_id)
        states = {k: v for k, v in self._states().items() if k in set(skill_ids)}
        new = [k for k in skill_ids if k not in states or in_learning_phase(states[k])]
        sections = self._storage.users.section_states()
        new = [
            k
            for k in new
            if (s := catalog.skills[k].section_id) is None
            or (sections.get(s) is not None and sections[s].state != "off")
        ]
        retention = self._retention_of(day, skill_ids)
        targets = [
            t for t in self._targets(day, window=horizon_days) if set(t.skill_ids) & set(skill_ids)
        ]
        return project_load(
            states,
            new,
            today=day,
            horizon_days=horizon_days,
            retention_of=lambda k: retention.get(k, 0.90),
            adapter=self.adapter_for_course(course_id),
            days=self.days(),
            targets=targets,
            new_per_day=self.settings().new_skills_per_day,
            minutes_per_problem=minutes_per_problem,
        )

    # ------------------------------------------------------------ calibration, fitting

    def calibration(self) -> dict[str, CalibrationReport]:
        catalog = self.catalog()
        return calibration_by_course(self._storage.users.review_events(), catalog.course_of)

    def _log(self) -> tuple[list[ReviewEvent], dict[int, Attempt]]:
        users = self._storage.users
        attempts = {a.id: a for a in users.attempts(include_voided=True) if a.id is not None}
        return users.review_events(include_voided=True), attempts

    def histories(self, set_id: str | None = None, *, exclude: Sequence[int] = ()) -> list[History]:
        """Histories of the cards in a parameter set (all sets: None). `exclude`: attempt
        ids whose events are left out (being voided)."""
        events, attempts = self._log()
        sets = self._sets()
        skip = set(exclude)
        chosen = [
            # Excluded events count as voided: still known, so the next event is no anchor.
            replace(e, voided_by=-1) if e.attempt_id in skip and e.voided_by is None else e
            for e in events
            if set_id is None or sets.event(e) == set_id
        ]
        return build_histories(chosen, day_of=self.days().day_of, attempts=attempts)

    def training_items(self, set_id: str) -> list[Item]:
        return training_items(self.histories(set_id))

    def calibration_stats(
        self, set_id: str | None = None, *, with_held_out: bool = False
    ) -> CalibrationStats:
        """I8 + I1: calibration with Wilson intervals and a Bonferroni alarm per course and
        per series (core, strict, settled, stretch, post-stretch), true retention, and,
        above 300 items when asked (it fits five times), held-out log loss and RMSE(bins)
        against the size-adjusted baseline (HeldOut.thresholds)."""
        events, attempts = self._log()
        sets = self._sets()
        values = sets.values
        if set_id is not None:
            events = [e for e in events if sets.event(e) == set_id]
        live = [e for e in events if e.voided_by is None]

        def adapter_of(e: ReviewEvent) -> FsrsAdapter:
            return sets.adapter(sets.event(e))

        day_of = self.days().day_of
        items = training_items(build_histories(events, day_of=day_of, attempts=attempts))
        split = None
        if with_held_out and len(items) > FIT_MIN_ITEMS:
            current = load_set(values, set_id or set_id_for("skill")).parameters
            split = held_out(items, current)
        catalog = self.catalog()
        return CalibrationStats(
            by_course=calibration_by_course(live, catalog.course_of),
            series=calibration_series(
                events, attempts=attempts, day_of=day_of, adapter_of=adapter_of
            ),
            true_retention=true_retention(live, day_of=day_of, adapter_of=adapter_of),
            items=len(items),
            held_out=split,
        )

    def fit_offer(self) -> FitOffer:
        events, attempts = self._log()
        return fit_offer(events, day_of=self.days().day_of, attempts=attempts)

    def fit(
        self,
        set_id: str | None = None,
        *,
        candidate: Sequence[float] | None = None,
        fit_fn: Callable[[Sequence[Item]], Sequence[float]] = fit_items,
    ) -> FitReport:
        """Fit a parameter set and adopt the result only if it wins (C2), then rebuild
        memory from the log (C3). `candidate`: judge given parameters instead of fitting
        (an imported Anki preset, say). Every attempt is logged in the set's fit log, a
        failed one too (ADR-0019 item 8)."""
        set_id = set_id or set_id_for("skill")
        try:
            decision = self.fit_decision(set_id, candidate=candidate, fit_fn=fit_fn)
        except KeyboardInterrupt, SystemExit, GeneratorExit:
            raise
        except BaseException as error:  # FitError, ParameterError, a fitter's panic
            return self._fit_failed(set_id, error)
        return self.apply_fit(decision)

    def _fit_failed(self, set_id: str, error: BaseException) -> FitReport:
        """Persist a failed fit in the set's fit log (ADR-0019 item 8); nothing else changes."""
        current = self.parameter_set(set_id).parameters
        try:
            items = len(self.training_items(set_id))
        except Exception:
            items = 0
        reason = f"failed: {type(error).__name__}: {error}"
        self._storage.users.set_setting(
            fit_log_key(set_id),
            {"at": self._now(), "items": items, "adopted": False, "failed": True, "reason": reason},
        )
        decision = Adoption(
            current=current, candidate=current, adopted=False, reason=reason, items=items
        )
        return FitReport(set_id=set_id, decision=decision, items=items)

    def fit_decision(
        self,
        set_id: str | None = None,
        *,
        candidate: Sequence[float] | None = None,
        fit_fn: Callable[[Sequence[Item]], Sequence[float]] = fit_items,
    ) -> FitDecision:
        """The slow, read-only half of `fit`: fit and judge a candidate (C2)."""
        set_id = set_id or set_id_for("skill")
        items = self.training_items(set_id)
        current = self.parameter_set(set_id)
        proposal = clean_parameters(candidate) if candidate is not None else tuple(fit_fn(items))
        decision = adoption(current.parameters, proposal, items, fit_fn=fit_fn)
        return FitDecision(
            set_id=set_id, decision=decision, items=len(items), imported=candidate is not None
        )

    def apply_fit(self, fit: FitDecision) -> FitReport:
        """The write half of `fit`: log it, store an adopted set and recompute (C3)."""
        users = self._storage.users
        decision, set_id = fit.decision, fit.set_id
        now = self._now()
        log = {
            "at": now,
            "items": fit.items,
            "adopted": decision.adopted,
            "reason": decision.reason,
            "candidate": params_id_for(decision.candidate),
        }
        value: dict[str, Any] | None = None
        changed: list[SkillState | FlashcardState] = []
        marks: dict[str, str] = {}
        if decision.adopted:
            value = stored_value(
                decision.candidate,
                at=now,
                source="import" if fit.imported else "fit",
                items=fit.items,
            )
            after = {**users.settings(), **self._set_values(set_id, value)}
            changed = self._rebuilt(set_id, settings=after)  # reads, before the write job
            marks = self._replayed_ids(set_id, after)

        def write(_: Any) -> Recomputed | None:
            # One transaction (ADR-0019 item 8): the adopted set, the memory rebuilt under
            # it and the fit log, all or none.
            recomputed = None
            if value is not None:
                self._store_set(set_id, value)
                recomputed = self._write_recompute(changed, marks, f"fit {value['id']}")
            users.set_setting(fit_log_key(set_id), log)
            return recomputed

        recomputed = users.atomic(write)
        return FitReport(set_id=set_id, decision=decision, items=fit.items, recomputed=recomputed)

    def void_changed_keys(self) -> UndoResult | None:
        """PACK-14: attempts graded under an answer key that a later card revision changed
        (a pack or import revision marked answer_changed) are voided, and memory is rebuilt
        from the log without them, in one transaction. Idempotent; None when none are left."""
        users, packs = self._storage.users, self._storage.packs
        by_card: dict[str, list[Attempt]] = defaultdict(list)
        for a in users.attempts():
            if a.id is not None:
                by_card[a.card_id].append(a)
        stale: list[int] = []
        for card_id, graded in by_card.items():
            changed = [r.rev for r in packs.revisions(card_id) if r.answer_changed]
            if changed:
                stale += [a.id for a in graded if a.id is not None and a.card_rev < max(changed)]
        if not stale:
            return None
        return self.void_attempts(
            stale, reason="recompute", note="PACK-14: graded under an answer key since changed"
        )

    def repair_fit(self) -> list[str]:
        """At launch (ADR-0019 item 8): rebuild memory for every set whose parameters in
        force are not the ones memory was last rebuilt under (a fit an older build adopted
        without its recompute). Idempotent. Returns the sets rebuilt."""
        values = self._storage.users.settings()
        repaired: list[str] = []
        for set_id in self.parameter_sets():
            in_force = load_set(values, set_id)
            if in_force.source == "default" or values.get(recomputed_key(set_id)) == (
                in_force.params_id
            ):
                continue
            self.recompute_memory(set_id, note="repair: parameters in force were not replayed")
            repaired.append(set_id)
        return repaired

    def _set_values(self, set_id: str, value: Mapping[str, Any]) -> dict[str, Any]:
        values = self._storage.users.settings()
        return {
            params_key(set_id): dict(value),
            history_key(set_id): with_entry(set_history(values, set_id), value),
        }

    def _store_set(self, set_id: str, value: Mapping[str, Any]) -> None:
        self._storage.users.set_settings(self._set_values(set_id, value))

    def parameter_sets(self) -> list[str]:
        """Every set in use: the skill domains, the flashcard and Anki deck-group sets."""
        events, _ = self._log()
        sets = self._sets()
        values = sets.values
        found = {set_id_for("skill")}
        found |= {sets.event(e) for e in events if e.voided_by is None}
        found |= {k.removeprefix("fsrs.params.") for k in values if k.startswith("fsrs.params.")}
        found.discard("math")
        return sorted(found)

    def fit_due(self, set_id: str) -> bool:
        """I7: refit monthly or when long-term items double; the first fit at 300 items."""
        items = len(self.training_items(set_id))
        if items < FIT_MIN_ITEMS:
            return False
        last = self._storage.users.settings().get(fit_log_key(set_id))
        if not isinstance(last, Mapping) or "at" not in last:
            return True
        if self._now() - int(last["at"]) >= FIT_EVERY_DAYS * DAY_MS:
            return True
        return items >= FIT_GROWTH * max(1, int(last.get("items") or 0))

    def auto_fit(
        self, *, writing: Callable[[], AbstractContextManager[Any]] | None = None
    ) -> list[FitReport]:
        """I7: run every due fit (guarded by C2, followed by C3). Call it when the app is
        idle, e.g. at the end of a session or on launch. `writing`: a lock held only while
        a decision is written and memory recomputed, so a caller can fit in the background
        without a recompute interleaving with a graded answer (the fitting itself, the
        slow part, runs outside it)."""
        reports: list[FitReport] = []
        for set_id in self.parameter_sets():
            if not self.fit_due(set_id):
                continue
            try:
                decision = self.fit_decision(set_id)
            except KeyboardInterrupt, SystemExit, GeneratorExit:
                raise
            except BaseException as error:  # persisted, and the next set still fits
                with writing() if writing is not None else nullcontext():
                    reports.append(self._fit_failed(set_id, error))
                continue
            with writing() if writing is not None else nullcontext():
                reports.append(self.apply_fit(decision))
        return reports

    def parameter_history(self, set_id: str | None = None) -> list[dict[str, Any]]:
        """Adopted sets, oldest first ({"w", "id", "at", "items", "source"})."""
        return set_history(self._storage.users.settings(), set_id or set_id_for("skill"))

    def revert_parameters(self, set_id: str, params_id: str) -> Recomputed:
        """One-click revert to an earlier set (or "fsrs6-default"), then recompute (C3)."""
        entries = self.parameter_history(set_id)
        found = next((e for e in reversed(entries) if e.get("id") == params_id), None)
        params = None if found is None else found.get("w")
        if params is None:
            if params_id != load_set({}, set_id).params_id:
                raise KeyError(f"no parameters {params_id!r} in the history of {set_id!r}")
            params = list(load_set({}, set_id).parameters)
        value = stored_value(params, at=self._now(), source="revert")
        self._store_set(set_id, value)
        return self.recompute_memory(set_id, note=f"revert to {params_id}")

    # ------------------------------------------------------------ imported histories (decision 6)

    def register_deck_group(
        self, group: str, decks: Sequence[str], parameters: Sequence[float] | None = None
    ) -> str:
        """An imported Anki deck group (decision 6): its decks join `group` in
        `fsrs.deck_groups` (a later import wins a deck) and the preset's parameters become
        the set "anki.<group>", unless that set already has stored parameters (a fit or a
        revert since). Parameters that can't be cleaned (C1) leave the set on the defaults.
        Returns the set id."""
        set_id = set_id_for("flashcard", group)
        users = self._storage.users
        values = users.settings()
        groups = values.get(DECK_GROUPS_SETTING)
        mapping = dict(groups) if isinstance(groups, Mapping) else {}
        mapping.update({str(d): group for d in decks})
        updates: dict[str, Any] = {DECK_GROUPS_SETTING: mapping}
        if parameters is not None and values.get(params_key(set_id)) is None:
            try:
                value = stored_value(parameters, at=self._now(), source="import")
            except ParameterError:
                value = None
            if value is not None:
                updates[params_key(set_id)] = value
                updates[history_key(set_id)] = with_entry(set_history(values, set_id), value)
        users.set_settings(updates)
        return set_id

    def replay_flashcards(
        self, items: Iterable[tuple[str, int]], *, retention: float = 0.90
    ) -> Recomputed:
        """Flashcard items whose reviews are logged but which have no state row (an
        imported history): their memory replayed from the log with their own set's
        parameters (C3), due at `retention` like a flashcard graded now. One transaction.
        Items with a state are left to `recompute_memory`."""
        users = self._storage.users
        have = {(s.card_id, s.ord) for s in users.flashcard_states()}
        wanted = sorted({(c, int(o)) for c, o in items} - have)
        if not wanted:
            return Recomputed(changed=(), void=None)
        sets = self._sets()
        days = self.days()
        latest = last_histories(self.histories(None))
        rows: list[FlashcardState] = []
        for card_id, ord_ in wanted:
            history = latest.get(("flashcard", card_id, ord_))
            if history is None or history.anchored:
                continue
            adapter = sets.adapter(sets.card(card_id))
            memory = rebuild(history, adapter)
            if memory is None:
                continue
            last = history.steps[-1]
            again = last.rating == 1
            interval = (
                1
                if again
                else adapter.interval_days(
                    memory.stability, retention, f"fc|{card_id}|{ord_}|{memory.last_review_at}"
                )
            )
            due = days.add(days.day_of(memory.last_review_at), max(1, interval))
            rows.append(
                FlashcardState(
                    card_id=card_id,
                    ord=ord_,
                    fsrs_state=3 if again else 2,
                    stability=memory.stability,
                    difficulty=memory.difficulty,
                    last_review_at=memory.last_review_at,
                    due_at=days.start(due),
                    reps=len(history.steps),
                    lapses=sum(1 for s in history.steps[1:] if s.rating == 1 and s.delta > 0),
                )
            )
        void = users.rewrite_states(rows, reason="recompute", note="replay imported history")
        return Recomputed(changed=tuple(rows), void=void)

    # ------------------------------------------------------------ recompute, repair (C3, I6)

    def _rebuilt(
        self,
        set_id: str | None,
        *,
        exclude: Sequence[int] = (),
        voided_at: Mapping[TargetKey, list[int]] | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> list[SkillState | FlashcardState]:
        """Every card's memory replayed from the log; `settings`: replay under these (a set
        about to be adopted) instead of the stored ones. Reads only."""
        users = self._storage.users
        sets = self._sets() if settings is None else _Sets(self, settings)
        latest = last_histories(self.histories(set_id, exclude=exclude))
        skills = [
            s
            for s in users.skill_states().values()
            if set_id is None or sets.skill(s.skill_id) == set_id
        ]
        cards = [
            c for c in users.flashcard_states() if set_id is None or sets.card(c.card_id) == set_id
        ]
        changed: list[SkillState | FlashcardState] = []
        changed += recompute_all(
            skills, latest, lambda s: sets.adapter(sets.skill(s.skill_id)), voided_at=voided_at
        )
        changed += recompute_all(
            cards, latest, lambda c: sets.adapter(sets.card(c.card_id)), voided_at=voided_at
        )
        return changed

    def recompute_memory(self, set_id: str | None = None, *, note: str | None = None) -> Recomputed:
        """C3: replay every card's non-voided events from its last fresh start and write the
        rebuilt memory in one transaction, logged with the void reason "recompute"."""
        changed = self._rebuilt(set_id)
        marks = self._replayed_ids(set_id, self._storage.users.settings())
        return self._storage.users.atomic(lambda _: self._write_recompute(changed, marks, note))

    def _replayed_ids(self, set_id: str | None, values: Mapping[str, Any]) -> dict[str, str]:
        """set id -> the params id its memory is replayed under (reads; before a write)."""
        ids = [set_id] if set_id is not None else self.parameter_sets()
        return {sid: load_set(values, sid).params_id for sid in ids}

    def _write_recompute(
        self,
        changed: Sequence[SkillState | FlashcardState],
        marks: Mapping[str, str],
        note: str | None,
    ) -> Recomputed:
        """Write rebuilt memory and, in the same transaction, which params ids it was
        rebuilt under (ADR-0019 item 8: launch repairs a set adopted without this)."""
        users = self._storage.users
        void = users.rewrite_states(changed, reason="recompute", note=note)
        for sid, params_id in marks.items():
            users.set_setting(recomputed_key(sid), params_id)
        return Recomputed(changed=tuple(changed), void=void)

    def void_attempts(
        self,
        attempt_ids: Sequence[int],
        *,
        reason: VoidReason,
        note: str | None = None,
        session: SessionState | None = None,
    ) -> UndoResult:
        """Void older attempts (a dispute, a report) and rebuild the memory of the cards
        their events touched, in one transaction (C3). Other rows are not restored. A card
        with no event left since its seed (a placement) goes back to the memory its first
        voided event started from. `session`: saved in the same transaction."""
        users = self._storage.users
        ids = set(attempt_ids)
        hit = [e for e in users.review_events() if e.attempt_id in ids]
        voided_at: dict[TargetKey, list[int]] = defaultdict(list)
        for e in hit:
            voided_at[(e.target_kind, e.target_id, e.target_ord)].append(e.at)
        changed = [
            c
            for c in self._rebuilt(None, exclude=list(ids), voided_at=voided_at)
            if _key_of(c) in voided_at
        ]
        done = {_key_of(c) for c in changed}
        for key, times in voided_at.items():
            if key in done:
                continue
            row = (
                users.skill_state(key[1])
                if key[0] == "skill"
                else users.flashcard_state(key[1], key[2])
            )
            first = min((e for e in hit if target_key(e) == key), key=lambda e: (e.at, e.id or 0))
            if row is None or row.last_review_at not in times or first.state_before is None:
                continue
            fields = {k: v for k, v in first.state_before.items() if hasattr(row, k)}
            changed.append(replace(row, **fields))
        return users.void_attempts(
            list(ids), reason=reason, changes=changed, note=note, session=session
        )

    def check_database(self) -> CheckReport:
        """I6 "Check database": find rows with impossible FSRS fields and rebuild them from
        the log (a broken card without history goes back to its learning phase), then
        rebuild every other card's memory too (C3). Both writes are logged as recomputes."""
        users = self._storage.users
        now = self._now()
        sets = self._sets()
        latest = last_histories(self.histories(None))
        problems: dict[str, list[str]] = {}
        fixed: list[SkillState | FlashcardState] = []
        for record_type in (SkillState, FlashcardState):
            for row in users.raw_state_rows(record_type):
                found = fsrs_problems(row, now)
                if not found:
                    continue
                if record_type is SkillState:
                    label = f"skill:{row['skill_id']}"
                    key: TargetKey = ("skill", row["skill_id"], 0)
                    set_id = sets.skill(row["skill_id"])
                else:
                    label = f"flashcard:{row['card_id']}:{row['ord']}"
                    key = ("flashcard", row["card_id"], row["ord"])
                    set_id = sets.card(row["card_id"])
                problems[label] = found
                fixed.append(_repaired(record_type, row, latest.get(key), sets.adapter(set_id)))
        first = users.rewrite_states(fixed, reason="recompute", note="check database: repair")
        changed = self._rebuilt(None)
        void = users.rewrite_states(changed, reason="recompute", note="check database")
        return CheckReport(
            problems=problems,
            repaired=Recomputed(changed=(*fixed, *changed), void=void or first),
        )

    # ------------------------------------------------------------ placement

    def place(self, seeds: Mapping[str, Provisional]) -> list[SkillState]:
        """Write placement (or Covered/Solid) seeds. Returns the rows written."""
        users = self._storage.users
        rows = apply_seeds(
            users.skill_states(list(seeds)),
            seeds,
            at_ms=self._now(),
            adapter=self.adapter(),
            adapter_of=self.skill_adapters(),
        )
        if rows:
            users.apply(rows)
        return [replace(r) for r in rows]


class _Sets:
    """Which parameter set each skill, card and event belongs to (memoized for one pass)."""

    def __init__(self, engine: Engine, values: Mapping[str, Any]) -> None:
        self.values = values
        self._engine = engine
        self._catalog: Catalog | None = None
        self._memo: dict[tuple[str, str], str] = {}
        self._adapters: dict[str, FsrsAdapter] = {}

    def skill(self, skill_id: str) -> str:
        key = ("skill", skill_id)
        if key not in self._memo:
            if self._catalog is None:
                self._catalog = self._engine.catalog()
            course = self._catalog.course_of(skill_id)
            self._memo[key] = set_id_for("skill", domain_of(self.values, course))
        return self._memo[key]

    def card(self, card_id: str) -> str:
        key = ("flashcard", card_id)
        if key not in self._memo:
            card = self._engine._storage.packs.card(card_id)
            group = deck_group_of(self.values, None if card is None else card.deck)
            self._memo[key] = set_id_for("flashcard", group)
        return self._memo[key]

    def event(self, e: ReviewEvent) -> str:
        return self.skill(e.target_id) if e.target_kind == "skill" else self.card(e.target_id)

    def adapter(self, set_id: str) -> FsrsAdapter:
        if set_id not in self._adapters:
            self._adapters[set_id] = self._engine._adapter_of_set(set_id, self.values)
        return self._adapters[set_id]


def _key_of(state: SkillState | FlashcardState) -> TargetKey:
    if isinstance(state, SkillState):
        return ("skill", state.skill_id, 0)
    return ("flashcard", state.card_id, state.ord)


def _repaired(
    record_type: type[Any], row: Mapping[str, Any], history: History | None, adapter: FsrsAdapter
) -> Any:
    """A broken row rebuilt from its history, or without a card when there is none."""
    clean = dict(row)
    clean.update(fsrs_state=None, stability=None, difficulty=None, due_at=None)
    base = rows.from_row(record_type, clean)
    if row.get("fsrs_state") is None or history is None:
        return base
    placeholder = replace(
        base,
        fsrs_state=row["fsrs_state"],
        stability=1.0,
        difficulty=5.0,
        last_review_at=history.steps[-1].at,
    )
    return recomputed(placeholder, history, adapter) or placeholder
