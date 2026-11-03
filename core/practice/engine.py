"""PracticeEngine: the student model and the planner over one profile's storage (wave 2,
docs/design/wave2-integration.md section 3, `engine.py`).

- **The state is a pure function of the log (C3).** `state()` keeps the learner state cached
  under a key of the newest non-voided attempt id, the voided count, the current parameter
  version, the catalog and the study-day clock. New attempt rows update it incrementally with
  `StudentModel.update`; anything else (an undo, a dispute, a new parameter version, a pack
  change) replays the log. So the engine never holds an observation the log does not, and
  `record` reads the committed row back from the log rather than taking one from the caller.
- **Certifiers** come from `Certifier.from_model` once per course and study day (and again
  after a replay or a settings change); each new first try goes in with `Certifier.add`.
- **Plans.** `plan_day` plans each active course (one with a setup row and its pack loaded)
  separately and merges them: every course's new-skill blocks first, then their other items
  round-robin, each course in its own plan's order (its checks and overflow where its plan put
  them). `next_item` is the merged plan's first item.
- **Parameters.** `params()` is the current `learner_params` version; with none, the prior is
  written first. `refit` runs `StudentModel.refit` on the log and records the outcome (source
  refit, its report, current only if adopted); `reset_params` writes the prior as a new
  current version.
- **Thread safety.** One re-entrant lock guards the caches; it is held while they are read or
  brought up to date. A refit computes outside it and takes it (with the caller's write lock)
  only to record its outcome.
"""

import math
import threading
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import date
from typing import Any

from core.engine.days import StudyDays
from core.learner import StudentModel, calibration_drift, is_success
from core.learner import refit_due as learner_refit_due
from core.learner.refit import RefitDecision
from core.learner.types import (
    ComponentId,
    ComponentInfo,
    Observation,
    Prediction,
    ProblemSpec,
    SharedParams,
    StudentState,
    UpdateRecord,
)
from core.model import Attempt, CourseSetup, Exam, LearnerParams
from core.plan import Certifier, intro_dates
from core.plan import plan_day as plan_course_day
from core.plan import statuses as plan_statuses
from core.plan.status import PlanContext
from core.plan.types import CourseSettings, DayPlan, ExamSpec, ServedItem, SkillStatus, WorkItem
from core.practice.catalog import Catalog, build_catalog, catalog_key
from core.practice.observations import build_observations, observations_of, order
from core.storage import Storage, StorageError

DAY_MS = 86_400_000
MS_PER_MINUTE = 60_000.0
PRIOR_VERSION = SharedParams().version  # "prior"
GROWTH_BANDS: Mapping[str, tuple[float, float]] = {
    "standard": (0.70, 0.90),  # design 4.4
    "hard": (0.50, 0.75),  # wave2-planner.md 3: the owner's harder band
}
# Calibration bins as the Model page shows them (plain words, sent as they are).
TIER_LABELS = tuple(f"Tier {t}" for t in range(1, 6))
GAP_LABELS = ("First practice", "Under a day", "1 to 7 days", "8 to 30 days", "Over 30 days")
GAP_LAST = GAP_LABELS[-1]
COMPONENT_LABELS = ("1 skill", "2 skills", "3 or more skills")


# ---------------------------------------------------------------------- the planner's model


class PlannerModel:
    """`core.learner.StudentModel` as `core.plan.Predictor` wants it: the catalog answers
    `component_info`, and the slip rate is the state's shared parameter."""

    def __init__(self, model: StudentModel, components: Mapping[ComponentId, ComponentInfo]):
        self.model = model
        self.components = components

    def predict(self, state: StudentState, problem: ProblemSpec, at_ms: int) -> Prediction:
        return self.model.predict(state, problem, at_ms)

    def copy(self, state: StudentState) -> StudentState:
        return self.model.copy(state)

    def component_info(self, component_id: ComponentId) -> ComponentInfo | None:
        return self.components.get(component_id)

    def slip(self, state: StudentState) -> float:
        return state.params.slip


# ---------------------------------------------------------------------- parameters as JSON


def params_json(params: SharedParams) -> dict[str, Any]:
    out = asdict(params)
    return {k: list(v) if isinstance(v, tuple) else v for k, v in out.items()}


def params_from_json(data: Mapping[str, Any], version: str) -> SharedParams:
    """A stored version's parameters; fields it lacks keep their defaults, unknown ones are
    ignored, and the row's version names it."""
    known = {f.name for f in fields(SharedParams)}
    values: dict[str, Any] = {}
    for key, value in data.items():
        if key in known:
            values[key] = tuple(value) if isinstance(value, list) else value
    values["version"] = version
    return SharedParams(**values)


# ---------------------------------------------------------------------- plans


@dataclass(frozen=True, slots=True)
class PlannedItem:
    course_id: str
    item: WorkItem


@dataclass(frozen=True, slots=True)
class PracticePlan:
    """Today's plan over every active course."""

    day: date
    items: tuple[PlannedItem, ...]
    plans: Mapping[str, DayPlan]  # course id -> its own plan
    minutes: float
    hours_to_keep_pace: float | None
    hours_basis: str  # history, standard or none
    standard_hours: float | None

    @property
    def first(self) -> PlannedItem | None:
        return self.items[0] if self.items else None


@dataclass(frozen=True, slots=True)
class Bin:
    label: str
    n: int
    predicted: float
    observed: float


@dataclass(frozen=True, slots=True)
class Calibration:
    by_tier: tuple[Bin, ...]
    by_gap: tuple[Bin, ...]
    by_components: tuple[Bin, ...]


@dataclass(frozen=True, slots=True)
class RefitOutcome:
    decision: RefitDecision
    record: LearnerParams


def work_item(**values: Any) -> WorkItem:
    """A WorkItem from stored values, keeping only the fields this core.plan has (rows from
    before the planner's item was logged whole, see `work_json`)."""
    known = {f.name for f in fields(WorkItem)}
    return WorkItem(**{k: v for k, v in values.items() if k in known})


def work_json(item: WorkItem) -> dict[str, Any]:
    """A planner item as JSON, every field, the problem by its id: the session logs it with
    the attempt, so the planner gets each served item back exactly as it returned it (its
    `day_items` cap, `ladder_for` and sitting fields ride on them; planner-impl-notes.md)."""
    out: dict[str, Any] = {}
    for f in fields(WorkItem):
        value = getattr(item, f.name)
        if f.name == "problem":
            value = None if value is None else value.problem_id
        elif isinstance(value, tuple):
            value = list(value)
        out[f.name] = value
    return out


def work_from_json(data: Mapping[str, Any], catalog: Catalog) -> WorkItem | None:
    """`work_json`'s item back; None when its problem is no longer loaded. Fields this
    core.plan does not have are dropped; fields the JSON lacks keep their defaults."""
    known = {f.name for f in fields(WorkItem)}
    values: dict[str, Any] = {}
    for key, value in data.items():
        if key in known:
            values[key] = tuple(value) if isinstance(value, list) else value
    problem_id = values.get("problem")
    if problem_id is not None:
        problem = catalog.problems.get(str(problem_id))
        if problem is None:
            return None
        values["problem"] = problem
    return WorkItem(**values)


def plan_settings(
    setup: CourseSetup, exams: Sequence[ExamSpec], *, sections: Sequence[str] = ()
) -> CourseSettings:
    """The planner's settings from a course's setup row and its exams. An alignment whose
    section the course no longer has (a pack update) is dropped, falling back to the start."""
    aligned = None
    deck, aligned_day = setup.aligned_deck, setup.aligned_day
    if deck is not None and aligned_day is not None and (not sections or deck in sections):
        aligned = (deck, aligned_day)
    values: dict[str, Any] = {
        "course_id": setup.course_id,
        "start": setup.start,
        "aligned": aligned,
        "pace_factor": setup.pace_factor,
        "accuracy_target": setup.accuracy_target,
        "target_tier": setup.target_tier,
        "end": setup.end_day,
        "exams": tuple(exams),
        "keep_target": setup.keep_target,
        "keep_tier": setup.keep_tier,
        "growth_band": GROWTH_BANDS.get(setup.growth_band, GROWTH_BANDS["standard"]),
    }
    return CourseSettings(**values)


def exam_spec(exam: Exam, days: StudyDays) -> ExamSpec | None:
    if exam.id is None:
        return None
    return ExamSpec(
        exam_id=exam.id,
        day=days.day_of(exam.at),
        scope_decks=tuple(exam.sections),
        target=exam.target_recall,
    )


def merge(plans: Mapping[str, DayPlan], order_of: Sequence[str]) -> tuple[PlannedItem, ...]:
    """Every course's new-skill blocks first (each plan's items up to its last block item,
    in course order), then the rest round-robin, each course in its own plan's order."""
    heads: list[PlannedItem] = []
    tails: list[list[PlannedItem]] = []
    for course_id in order_of:
        plan = plans.get(course_id)
        if plan is None:
            continue
        items = list(plan.items)
        last_block = max((i for i, it in enumerate(items) if it.block), default=-1)
        heads.extend(PlannedItem(course_id, it) for it in items[: last_block + 1])
        tails.append([PlannedItem(course_id, it) for it in items[last_block + 1 :]])
    out = list(heads)
    for r in range(max((len(t) for t in tails), default=0)):
        out.extend(t[r] for t in tails if r < len(t))
    return tuple(out)


# ---------------------------------------------------------------------- the engine


@dataclass(slots=True)
class _Learned:
    """The learner state for one log, catalog, parameter version and clock."""

    key: tuple[object, ...]  # catalog key, days
    params: SharedParams
    voided: int
    last_id: int
    generation: int
    state: StudentState
    observations: list[Observation] = field(default_factory=list)
    records: dict[tuple[int, str], UpdateRecord] = field(default_factory=dict)
    seen: dict[tuple[int, str], Observation] = field(default_factory=dict)  # same keys
    examples: dict[ComponentId, date] = field(default_factory=dict)  # first day shown
    spent: dict[int, float] = field(default_factory=dict)  # attempt id -> its presentation's
    presentations: dict[str, list[int]] = field(default_factory=dict)  # minutes; row ids
    totals: dict[str, float] = field(default_factory=dict)  # presentation -> minutes


@dataclass(slots=True)
class _CertCache:
    generation: int
    settings: CourseSettings
    unavailable: frozenset[str]
    certifier: Certifier


class PracticeEngine:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._lock = threading.RLock()
        self._catalog: Catalog | None = None
        self._model: StudentModel | None = None
        self._planner: PlannerModel | None = None
        self._model_key: tuple[object, ...] = ()
        self._learned: _Learned | None = None
        self._generation = 0
        self._certifiers: dict[tuple[str, date], _CertCache] = {}

    # ------------------------------------------------------------------ wiring

    @property
    def storage(self) -> Storage:
        return self._storage

    def days(self) -> StudyDays:
        users = self._storage.users
        return StudyDays(users.timezone(), users.rollover_hour())

    def catalog(self) -> Catalog:
        """The catalog of the loaded content, rebuilt when packs or own content change."""
        with self._lock:
            key = catalog_key(self._storage)
            if self._catalog is None or self._catalog.key != key:
                self._catalog = build_catalog(self._storage)
            return self._catalog

    def model(self) -> StudentModel:
        with self._lock:
            return self._ensure_model()[1].model

    def planner_model(self) -> PlannerModel:
        with self._lock:
            return self._ensure_model()[1]

    def _ensure_model(self) -> tuple[tuple[object, ...], PlannerModel]:
        """The model over the current catalog and study-day clock, and its cache key."""
        catalog = self.catalog()
        days = self.days()
        key = (catalog.key, days.tz, days.rollover_hour)
        planner = self._planner
        if planner is None or self._model_key != key:
            model = StudentModel(catalog.components, day_of=days.day_of)
            planner = PlannerModel(model, catalog.components)
            self._model, self._planner, self._model_key = model, planner, key
        return key, planner

    def unavailable(self) -> frozenset[str]:
        """Cards the planner must not choose: suspended or reported (hidden)."""
        marks = self._storage.users.card_marks()
        return frozenset(k for k, m in marks.items() if m.hidden or m.suspended)

    # ------------------------------------------------------------------ parameters

    def params(self) -> SharedParams:
        """The current shared parameters; the prior is written first when there are none."""
        users = self._storage.users
        row = users.learner_params()
        if row is None:
            prior = SharedParams()
            try:
                users.add_learner_params(
                    LearnerParams(
                        version=prior.version,
                        params=params_json(prior),
                        source="prior",
                        current=True,
                    )
                )
            except StorageError:
                row = users.learner_params()
                if row is None:
                    raise
                return params_from_json(row.params, row.version)
            return prior
        return params_from_json(row.params, row.version)

    def param_record(self) -> LearnerParams:
        """The current version's row (the prior is written first when there is none)."""
        self.params()
        row = self._storage.users.learner_params()
        if row is None:
            raise StorageError("no current learner parameter version")
        return row

    def reset_params(self) -> LearnerParams:
        """The prior as a new current version (source reset); the state replays under it."""
        with self._lock:
            users = self._storage.users
            now = self._storage.db.clock.now_ms()
            version = self._fresh_version(f"reset-{now}")
            prior = replace(SharedParams(), version=version)
            record = users.add_learner_params(
                LearnerParams(
                    version=version,
                    params=params_json(prior),
                    source="reset",
                    current=True,
                )
            )
            self._invalidate()
            return record

    def _fresh_version(self, wanted: str) -> str:
        users = self._storage.users
        version, n = wanted, 1
        while users.learner_params(version) is not None:
            n += 1
            version = f"{wanted}.{n}"
        return version

    def _invalidate(self) -> None:
        self._learned = None
        self._certifiers.clear()

    # ------------------------------------------------------------------ the learner state

    def state(self) -> StudentState:
        with self._lock:
            return self._sync().state

    def observations(self) -> list[Observation]:
        with self._lock:
            return list(self._sync().observations)

    def update_of(self, attempt_id: int, problem_id: str) -> UpdateRecord | None:
        with self._lock:
            return self._sync().records.get((attempt_id, problem_id))

    def record(self, attempt_id: int) -> tuple[UpdateRecord, ...]:
        """After the session's transaction committed attempt `attempt_id`: bring the state
        (and the certifiers) up to date with the log and return the updates its first tries
        made (none when the row carries no observation)."""
        with self._lock:
            learned = self._sync()
            return tuple(r for (a, _), r in learned.records.items() if a == attempt_id)

    def _sync(self) -> _Learned:
        """The cached state, brought up to date with the log (see the module docstring)."""
        users = self._storage.users
        key, planner = self._ensure_model()
        model = planner.model
        catalog = self.catalog()
        params = self.params()
        newest, voided = users.attempt_log_key()
        learned = self._learned
        if (
            learned is None
            or learned.key != key
            or learned.params != params
            or learned.voided != voided
            or newest < learned.last_id
        ):
            return self._rebuild(key, model, catalog, params, newest, voided)
        if newest > learned.last_id:
            rows = users.attempts(after_id=learned.last_id)
            new = sorted((o for a in rows for o in observations_of(a, catalog)), key=order)
            if new and learned.observations and order(new[0]) < order(learned.observations[-1]):
                return self._rebuild(key, model, catalog, params, newest, voided)
            for obs in new:
                key_of = (obs.attempt_id, obs.problem.problem_id)
                learned.records[key_of] = model.update(learned.state, obs)
                learned.seen[key_of] = obs
                learned.observations.append(obs)
            for cached in self._certifiers.values():
                if cached.generation == learned.generation:
                    for obs in new:
                        cached.certifier.add(obs)
            _note_rows(learned, rows)
            learned.last_id = max([newest, *(a.id or 0 for a in rows)])
        return learned

    def _rebuild(
        self,
        key: tuple[object, ...],
        model: StudentModel,
        catalog: Catalog,
        params: SharedParams,
        newest: int,
        voided: int,
    ) -> _Learned:
        rows = self._storage.users.attempts()
        observations = build_observations(rows, catalog)
        state, records = model.replay(params, observations)
        self._generation += 1
        learned = _Learned(
            key=key,
            params=params,
            voided=voided,
            last_id=max([newest, *(a.id or 0 for a in rows)]),
            generation=self._generation,
            state=state,
            observations=observations,
            records={
                (o.attempt_id, o.problem.problem_id): r
                for o, r in zip(observations, records, strict=True)
            },
            seen={(o.attempt_id, o.problem.problem_id): o for o in observations},
        )
        _note_rows(learned, rows)
        self._learned = learned
        self._certifiers.clear()
        return learned

    # ------------------------------------------------------------------ courses

    def setups(self) -> dict[str, CourseSetup]:
        return {s.course_id: s for s in self._storage.users.course_setups()}

    def active_courses(self) -> list[str]:
        """Courses with a setup row whose content is loaded, in course order."""
        catalog = self.catalog()
        setups = self.setups()
        return [c for c in catalog.courses if c in setups]

    def exams_for(self, course_id: str) -> list[Exam]:
        catalog = self.catalog()
        entry = catalog.courses.get(course_id)
        decks = {s.deck for s in entry.sections} if entry is not None else set()
        out = []
        for exam in self._storage.users.exams():
            mine = exam.course_id == course_id or (
                exam.course_id is None and any(d in decks for d in exam.sections)
            )
            if mine:
                out.append(exam)
        return out

    def settings(self, course_id: str) -> CourseSettings | None:
        """The planner's settings for a course (None: the course is not set up)."""
        setup = self._storage.users.course_setup(course_id)
        if setup is None:
            return None
        days = self.days()
        entry = self.catalog().courses.get(course_id)
        sections = [s.deck for s in entry.course.standard.sections] if entry is not None else []
        exams = [e for e in (exam_spec(x, days) for x in self.exams_for(course_id)) if e]
        return plan_settings(setup, exams, sections=sections)

    def certifier(self, course_id: str, day: date, now_ms: int) -> Certifier:
        """The course's certifier for the study day (built from the model once per day)."""
        with self._lock:
            learned = self._sync()
            entry = self.catalog().courses[course_id]
            settings = self.settings(course_id) or CourseSettings(course_id=course_id)
            unavailable = self.unavailable()
            cached = self._certifiers.get((course_id, day))
            if (
                cached is None
                or cached.generation != learned.generation
                or cached.settings != settings
                or cached.unavailable != unavailable
            ):
                certifier = Certifier.from_model(
                    self.planner_model(),
                    learned.state,
                    learned.observations,
                    entry.course,
                    settings,
                    today=day,
                    now_ms=now_ms,
                    retired=unavailable,
                )
                cached = _CertCache(learned.generation, settings, unavailable, certifier)
                self._certifiers[(course_id, day)] = cached
            return cached.certifier

    def examples_seen(self, day: date) -> frozenset[ComponentId]:
        """Skills whose worked example was shown on an earlier study day."""
        with self._lock:
            return frozenset(k for k, d in self._sync().examples.items() if d < day)

    def served(self, day: date) -> list[tuple[str, ServedItem]]:
        """The day's served plan items, from the log: each presentation the session wrote
        with its plan (`extra.plan`) once, in the order served, as the planner planned it,
        with its first try's outcome (None for a worked example), the model's update and the
        minutes spent. Every session of the day counts, so a second session goes on where the
        first stopped. Practice-test problems are in it too: the planner counts them toward a
        skill's streak but keeps them out of the day's plan and its cap (by role)."""
        with self._lock:
            learned = self._sync()
            catalog = self.catalog()
            rows = self._storage.users.attempts(since=self.days().start(day) - DAY_MS)
            groups: dict[str, list[Attempt]] = {}
            for row in sorted(rows, key=lambda a: a.id or 0):
                plan = row.extra.get("plan")
                if row.study_day != day.isoformat() or row.presentation_id is None:
                    continue
                if isinstance(plan, Mapping):
                    groups.setdefault(row.presentation_id, []).append(row)
            out: list[tuple[str, ServedItem]] = []
            for group in sorted(groups.values(), key=lambda g: g[0].id or 0):
                served = _served_item(group, catalog, learned)
                if served is not None:
                    out.append(served)
            return out

    def scheduled_skills(self) -> frozenset[ComponentId]:
        """The course skills of the set-up courses: their pace schedule says when each is
        introduced (flashcards on them follow it, not the Library's section states)."""
        with self._lock:
            catalog = self.catalog()
            out: set[ComponentId] = set()
            for course_id in self.active_courses():
                out |= {
                    s.skill_id for s in catalog.courses[course_id].course.skills if not s.background
                }
            return frozenset(out)

    def introduced(self, day: date) -> frozenset[ComponentId]:
        """Skills of the set-up courses introduced on or before the day (design 4.1)."""
        with self._lock:
            catalog = self.catalog()
            out: set[ComponentId] = set()
            for course_id in self.active_courses():
                settings = self.settings(course_id)
                if settings is None:
                    continue
                try:
                    intro = intro_dates(catalog.courses[course_id].course, settings)
                except ValueError:  # settings the pack no longer fits: nothing introduced
                    continue
                out |= {k for k, d in intro.items() if d <= day}
            return frozenset(out)

    # ------------------------------------------------------------------ plans

    def plan_day(
        self, day: date, now_ms: int, served: Sequence[tuple[str, ServedItem]] = ()
    ) -> PracticePlan:
        """Everything left to do today over the active courses (see the module docstring).
        `served`: today's served items so far, each with the course it was planned for."""
        with self._lock:
            learned = self._sync()
            model = self.planner_model()
            catalog = self.catalog()
            unavailable = self.unavailable()
            seen = self.examples_seen(day)
            plans: dict[str, DayPlan] = {}
            for course_id in self.active_courses():
                entry = catalog.courses[course_id]
                settings = self.settings(course_id)
                if settings is None:
                    continue
                mine = [s for c, s in served if c == course_id]
                plans[course_id] = plan_course_day(
                    model,
                    learned.state,
                    self.certifier(course_id, day, now_ms),
                    entry.course,
                    settings,
                    day,
                    now_ms,
                    mine,
                    examples_seen=seen,
                    retired=unavailable,
                    spent_minutes=learned.spent,
                )
            order_of = list(plans)
            return self._summarize(day, plans, merge(plans, order_of), catalog)

    def next_item(
        self, day: date, now_ms: int, served: Sequence[tuple[str, ServedItem]] = ()
    ) -> PlannedItem | None:
        return self.plan_day(day, now_ms, served).first

    def _summarize(
        self,
        day: date,
        plans: Mapping[str, DayPlan],
        items: tuple[PlannedItem, ...],
        catalog: Catalog,
    ) -> PracticePlan:
        hours: list[float] = []
        standard: list[float] = []
        bases: set[str] = set()
        for course_id, plan in plans.items():
            entry = catalog.courses[course_id]
            basis = plan.hours_basis
            if not entry.has_pace and basis == "standard":
                continue  # no pace data: the planner's stand-in hours are not the pack's
            if plan.hours_to_keep_pace is not None:
                hours.append(plan.hours_to_keep_pace)
                bases.add(basis)
            if entry.has_pace and plan.standard_hours is not None:
                standard.append(plan.standard_hours)
        basis = "history" if "history" in bases else "standard" if "standard" in bases else "none"
        return PracticePlan(
            day=day,
            items=items,
            plans=plans,
            minutes=round(sum(p.item.expected_minutes for p in items), 6),
            hours_to_keep_pace=round(sum(hours), 6) if hours else None,
            hours_basis=basis,
            standard_hours=round(sum(standard), 6) if standard else None,
        )

    def statuses(self, course_id: str, day: date, now_ms: int) -> tuple[SkillStatus, ...]:
        """Every skill of the course with its state, track, milestones and readiness."""
        with self._lock:
            learned = self._sync()
            settings = self.settings(course_id)
            if settings is None:
                return ()
            entry = self.catalog().courses[course_id]
            return plan_statuses(
                self.planner_model(),
                learned.state,
                self.certifier(course_id, day, now_ms),
                entry.course,
                settings,
                day,
                now_ms,
                examples_seen=self.examples_seen(day),
                retired=self.unavailable(),
            )

    def certified(self, course_id: str, day: date, now_ms: int, status: SkillStatus) -> list[bool]:
        """Whether each of the skill's milestones is certified on the day, by the planner's
        own rule (core.plan.status.PlanContext.certified)."""
        with self._lock:
            settings = self.settings(course_id)
            if settings is None:
                return [False for _ in status.milestones]
            learned = self._sync()
            entry = self.catalog().courses[course_id]
            ctx = PlanContext(
                self.planner_model(),
                learned.state,
                self.certifier(course_id, day, now_ms),
                entry.course,
                settings,
                day,
                now_ms,
                retired=self.unavailable(),
            )
            return [ctx.certified(status.skill_id, m) for m in status.milestones]

    # ------------------------------------------------------------------ calibration and refit

    def calibration(self) -> Calibration:
        """Prediction against outcome over the log under the current parameters (the per-tier
        recalibration included): by tier, by days since the main skill was last practised and
        by the number of course components (design 6.4)."""
        with self._lock:
            learned = self._sync()
            catalog = self.catalog()
            pairs: list[tuple[Observation, float]] = [
                (o, learned.records[(o.attempt_id, o.problem.problem_id)].prediction.p)
                for o in learned.observations
            ]
        by_tier: dict[str, list[tuple[bool, float]]] = defaultdict(list)
        by_gap: dict[str, list[tuple[bool, float]]] = defaultdict(list)
        by_k: dict[str, list[tuple[bool, float]]] = defaultdict(list)
        last: dict[ComponentId, int] = {}
        for obs, p in pairs:
            y = is_success(obs)
            by_tier[TIER_LABELS[min(max(obs.problem.tier, 1), 5) - 1]].append((y, p))
            previous = last.get(obs.problem.main_skill)
            by_gap[_gap_label(previous, obs.at_ms)].append((y, p))
            last[obs.problem.main_skill] = obs.at_ms
            course = sum(
                1
                for k in obs.problem.components
                if k not in catalog.components or not catalog.components[k].background
            )
            by_k[COMPONENT_LABELS[min(max(course, 1), 3) - 1]].append((y, p))
        return Calibration(
            by_tier=_bins(by_tier, TIER_LABELS),
            by_gap=_bins(by_gap, GAP_LABELS),
            by_components=_bins(by_k, COMPONENT_LABELS),
        )

    def last_refit(self) -> LearnerParams | None:
        found = [p for p in self._storage.users.learner_param_history() if p.source == "refit"]
        return found[-1] if found else None

    def refit_due(self) -> bool:
        with self._lock:
            return self._refit_due(self._sync())

    def _refit_due(self, learned: _Learned) -> bool:
        last = self.last_refit()
        report = last.report if last is not None and last.report else {}
        at_last = report.get("attempts") if last is not None else None
        after = int(report.get("last_attempt_id", 0) or 0)
        since = [
            (is_success(o), learned.records[(o.attempt_id, o.problem.problem_id)].prediction.p)
            for o in learned.observations
            if o.attempt_id > after
        ]
        return learner_refit_due(
            attempts=len(learned.observations),
            at_last_refit=None if at_last is None else int(at_last),
            drift=calibration_drift(since),
        )

    def refit(
        self,
        *,
        force: bool = False,
        writing: Callable[[], AbstractContextManager[object]] = nullcontext,
    ) -> RefitOutcome | None:
        """Refit when due (or always, with `force`: the student's Refit now). The fit runs
        outside the cache lock; recording it takes `writing` (the service's lock), so it never
        interleaves with a graded answer. A version made current meanwhile (a reset) wins: the
        fit is then recorded but not adopted."""
        with self._lock:
            learned = self._sync()
            if not force and not self._refit_due(learned):
                return None
            observations = list(learned.observations)
            current = learned.params
            model = self.model()
        decision = model.refit(observations, current)
        with writing(), self._lock:
            users = self._storage.users
            now = self._storage.db.clock.now_ms()
            still = self.params().version == current.version
            adopted = decision.adopted and still
            chosen = decision.params if adopted else decision.candidate
            version = self._fresh_version(chosen.version)
            report = refit_report(decision, now, observations, adopted=adopted, version=version)
            record = users.add_learner_params(
                LearnerParams(
                    version=version,
                    params=params_json(replace(chosen, version=version)),
                    source="refit",
                    report=report,
                    current=adopted,
                )
            )
            if adopted:
                self._invalidate()
            return RefitOutcome(decision=decision, record=record)


def refit_report(
    decision: RefitDecision,
    at: int,
    observations: Sequence[Observation],
    *,
    adopted: bool,
    version: str,
) -> dict[str, Any]:
    """What a refit row keeps: the held-out comparison per block and overall, and the log's
    size (the next refit is due from it)."""
    return {
        "at": at,
        "attempts": len(observations),
        "last_attempt_id": max((o.attempt_id for o in observations), default=0),
        "adopted": adopted,
        "p_value": _finite(decision.p_value),
        "current_score": _finite(decision.current_score),
        "candidate_score": _finite(decision.candidate_score),
        "train_attempts": decision.train_attempts,
        "held_out_attempts": decision.held_out_attempts,
        "current_version": decision.current.version,
        "version": version,
        "blocks": [
            {
                "name": b.name,
                "parameters": list(b.parameters),
                "current": _finite(b.current_score),
                "candidate": _finite(b.candidate_score),
                "p_value": _finite(b.p_value),
                "adopted": b.adopted and adopted,
            }
            for b in decision.blocks
        ],
    }


def _finite(value: float) -> float:
    return float(value) if math.isfinite(value) else 0.0


def _gap_label(previous: int | None, at_ms: int) -> str:
    """Days since the main skill's previous first try: none (first practice); under 1; 1 to 7
    (1 <= gap <= 7); 8 to 30 (7 < gap <= 30); over 30."""
    if previous is None:
        return GAP_LABELS[0]
    gap = (at_ms - previous) / DAY_MS
    if gap < 1.0:
        return GAP_LABELS[1]
    if gap <= 7.0:
        return GAP_LABELS[2]
    if gap <= 30.0:
        return GAP_LABELS[3]
    return GAP_LAST


def _bins(groups: Mapping[str, list[tuple[bool, float]]], labels: Sequence[str]) -> tuple[Bin, ...]:
    out = []
    for label in labels:
        pairs = groups.get(label, [])
        n = len(pairs)
        predicted = sum(p for _, p in pairs) / n if n else 0.0
        observed = sum(1.0 for y, _ in pairs if y) / n if n else 0.0
        out.append(Bin(label, n, round(predicted, 6), round(observed, 6)))
    return tuple(out)


def _served_item(
    group: Sequence[Attempt], catalog: Catalog, learned: _Learned
) -> tuple[str, ServedItem] | None:
    """One presentation's rows (id order) as the planner's served item: the item from the
    plan the first row carries, the outcome from the observation of the item's problem (the
    first try's row, or a multi-part card's final row)."""
    first = group[0]
    plan = first.extra.get("plan")
    if not isinstance(plan, Mapping):
        return None
    work = plan.get("work")
    if isinstance(work, Mapping):  # logged whole: the item exactly as the planner returned it
        found = work_from_json(work, catalog)
        if found is None:
            return None  # its card is no longer loaded
        return _outcome(first, group, found, plan, learned)
    problem_id = plan.get("problem")
    problem = catalog.problems.get(str(problem_id)) if problem_id else None
    if problem_id and problem is None:
        return None  # its card is no longer loaded
    tier = plan.get("tier")
    item = work_item(
        skill_id=str(plan.get("skill") or first.skill_id or ""),
        role=first.role or "growth",
        problem=problem,
        example_card=None if problem is not None else first.card_id,
        expected_minutes=float(plan.get("minutes") or 0.0),
        priority=int(plan.get("priority") or 1),
        tier=None if tier is None else int(tier),
        milestone=first.milestone,
        missed=bool(first.missed),
        block=bool(plan.get("block")),
        p=first.plan_p,
        reason=str(plan.get("reason") or ""),
        ladder=int(first.ladder or 0),
        sitting=first.sitting,
        time_limit=plan.get("time_limit"),
    )
    return _outcome(first, group, item, plan, learned)


def _outcome(
    first: Attempt,
    group: Sequence[Attempt],
    item: WorkItem,
    plan: Mapping[str, Any],
    learned: _Learned,
) -> tuple[str, ServedItem] | None:
    """A served item with its outcome: the first try's observation of the item's problem
    (None for a worked example), the model's update and the minutes spent."""
    correct: bool | None = None
    update: UpdateRecord | None = None
    problem = item.problem
    if problem is not None:
        for row in group:
            obs = learned.seen.get((row.id or 0, problem.problem_id))
            if obs is not None:
                correct = is_success(obs)
                update = learned.records.get((row.id or 0, problem.problem_id))
                break
        if correct is None:
            return None  # nothing answered yet (a held answer is graded before re-planning)
    minutes = learned.spent.get(first.id or 0)
    course = str(plan.get("course") or "")
    return course, ServedItem(item=item, correct=correct, update=update, minutes=minutes)


def _note_rows(learned: _Learned, rows: Sequence[Attempt]) -> None:
    """From new rows: the examples shown (each skill's first day) and the minutes spent on
    each presentation (all its rows' active time), kept under every row id of the
    presentation, since an observation sits on its first try (or a multi-part card's final
    row)."""
    for row in sorted(rows, key=lambda a: a.id or 0):
        if row.voided_by is not None or row.id is None:
            continue
        day = date.fromisoformat(row.study_day) if row.study_day else None
        if row.verdict == "shown" and row.skill_id and day is not None:
            first = learned.examples.get(row.skill_id)
            if first is None or day < first:
                learned.examples[row.skill_id] = day
            continue
        if row.card_kind != "problem" or row.presentation_id is None:
            continue
        ids = learned.presentations.setdefault(row.presentation_id, [])
        ids.append(row.id)
        total = learned.totals.get(row.presentation_id, 0.0) + (row.active_ms or 0) / MS_PER_MINUTE
        learned.totals[row.presentation_id] = total
        for rid in ids:
            learned.spent[rid] = total
