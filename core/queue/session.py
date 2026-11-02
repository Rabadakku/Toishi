"""The study session service: start or resume, serve, grade, re-plan, undo, summarize.

`StudyService(storage)` is what the bridge calls. It keeps no state of its own: every
call reads the open session row (QUE-16), acts, and saves the row again, so a quit, crash
or restart resumes at the same problem with its active time, typed draft, tries, hints and
any verdict not yet continued from. A lock serializes calls (bridge methods run on worker
threads, AGENTS rule 6).

Grading flow for a problem:

1. `submit` checks the answer (core.grader). A syntax or shape error is not an attempt. A
   wrong non-final attempt is logged at once (Engine.record_try) and the page shows "Not
   quite". A final answer (correct, or wrong after the last attempt, or Give up) is saved
   in the session row with its verdict and shown with the full solution.
2. The rating needs what the student does on that screen: "too easy" (E) after a correct
   answer, or the "What went wrong?" choice after a miss. `diagnose` and `next` grade the
   saved answer through Engine.grade, committing the attempt, its FSRS event and the
   session in one transaction (rule 5). A saved answer is never lost: resuming shows the
   same verdict screen, and a session left open past the study-day rollover is graded
   with its original time before a new plan is built.
3. The re-plan reads what the answer changed: a lapse adds a reinforcement problem at
   least 5 items later (a stretch problem's owed core-band review waits for the next
   study day, ADR-0014); checks made by the diagnosis flow (PendingCheck rows) land at
   least `after_items` (3) later; a learning block grows or ends with the learning phase;
   a flashcard on the missed skill follows at once. Each takes the slot of the
   lowest-priority pending item.

Card kinds (ADR-0010): a multi-part problem keeps a verdict and tries per part in the
session row and is final when every part is; a find-the-error item can stand in for a
skill's review problem once the diagnosis flow unlocks it; a method-choice skill's items are
which-method items outside the problem count; cloze cards come one blank number at a time;
self-graded problems show their solution (and rubric) before the student grades them.
"""

import hashlib
import math
import threading
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, timedelta
from typing import Any, Literal, cast

from core.engine import (
    AnswerFacts,
    Catalog,
    Engine,
    FsrsAdapter,
    GradeHook,
    GradeResult,
    PartOutcome,
    ProblemOutcome,
    SkillContext,
    TimingFacts,
    card_facts,
    due_day,
    learning_step,
    memory_of,
    practice_tests_open,
    record_try,
    scheduled_load,
    skill_retention,
)
from core.engine.config import SEEN_SKIP_DAYS
from core.engine.diagnosis import (
    Diagnosis,
    DiagnosisHook,
    DiagnosisSettings,
    StorageWorld,
    find_error_highlighted,
    find_error_slot_open,
    find_error_unlocked,
    grade_find_error,
    queue_order,
)
from core.engine.grading import Effects, Purpose, record_unrated
from core.engine.schedule import SPREAD_DAYS, GoalChange, goal_change
from core.engine.service import FitReport
from core.grader import Status
from core.model import (
    THIS_ATTEMPT,
    Attempt,
    Card,
    CardMark,
    CardRef,
    CourseGoal,
    Dispute,
    ErrorChoice,
    GradedAnswer,
    PendingCheck,
    Report,
    SessionState,
    SkillState,
    VoidReason,
)
from core.queue import cloze
from core.queue import views as v
from core.queue.answers import (
    Checker,
    Previewer,
    check_answers,
    default_checker,
    default_previewer,
    specs_for,
)
from core.queue.config import (
    CHECK,
    CHECK_GAP,
    DAY_MS,
    DEFAULT_TEST_MINUTES_PER_PROBLEM,
    DIAGNOSIS_DAY_KEY,
    EXAMPLE_MS,
    EXTRA_DEFAULT,
    FLASHCARD_RESHOW_GAP,
    FOCUSED_DEFAULT,
    LEARNING,
    MINUTE_MS,
    NEW,
    PRACTICE_TEST_DEFAULT,
    RELEARN,
    REVIEW,
    TEST_RECALL_FLOOR,
    TEST_UNANSWERED_DEFAULT,
    TEST_UNANSWERED_KEY,
)
from core.queue.daylog import (
    DayEntry,
    Vacation,
    backlog_stuck,
    overloaded,
    read_log,
    write_entry,
    write_vacation,
)
from core.queue.estimate import TimeTable
from core.queue.flashcards import FLASHCARD_REWRITE, grade_flashcard
from core.queue.guards import TimingReport, guard_timing
from core.queue.items import TAG_LABELS, Plan, PlanItem, Unit, why
from core.queue.order import order_items
from core.queue.planner import (
    build_plan,
    confusable_map,
    flashcard_item,
    projected_minutes,
    rebalance,
)
from core.queue.snapshot import DAILY_MODES, QueueSettings, Snapshot, gather
from core.queue.triage import ItemBuilder as TriageBuilder
from core.queue.triage import learning_block, policy_for
from core.storage import NothingToUndoError, Storage, StorageError, UndoConflictError


class QueueError(Exception):
    """A request the session can't act on now (shown to the student as a message)."""


def _uid() -> str:
    return uuid.uuid4().hex


def _goal(goal: CourseGoal | Mapping[str, Any]) -> CourseGoal:
    if isinstance(goal, CourseGoal):
        return goal

    def day(key: str) -> date | None:
        raw = goal.get(key)
        return None if raw is None else date.fromisoformat(str(raw))

    return CourseGoal(
        course_id=str(goal["course_id"]),
        goal=goal.get("goal", "A"),
        custom_retention=goal.get("custom_retention"),
        goal_date=day("goal_date"),
        starts_on=day("starts_on"),
    )


class StudyService:
    def __init__(
        self,
        storage: Storage,
        *,
        hooks: Sequence[GradeHook] = (),
        checker: Checker | None = None,
        previewer: Previewer | None = None,
        diagnosis: bool = True,
        app_version: str | None = None,
    ) -> None:
        self._storage = storage
        self._hooks = tuple(hooks)
        self._checker = checker or default_checker
        self._previewer = previewer or default_previewer
        self._diagnosis = diagnosis
        self._app_version = app_version
        self._lock = threading.RLock()
        self._cards: dict[str, Card] = {}
        self._fitter: threading.Thread | None = None
        self._launched = False  # the launch repair ran (ADR-0019 item 8)
        # The last background fit's reports, or the error that stopped it (I7).
        self.last_auto_fit: list[FitReport] | Exception | None = None

    # ================================================================ wiring

    @property
    def storage(self) -> Storage:
        return self._storage

    def engine(self) -> Engine:
        """A fresh engine per call (it builds the skill catalog once, see _CallEngine) whose
        grading runs the error-diagnosis hook (ADR-0008), then any extra hooks."""
        if not self._diagnosis:
            return _CallEngine(self._storage, hooks=(*self._hooks, self._bookkeeping_hook))
        base = Engine(self._storage)
        holder: list[Engine] = []
        hook = DiagnosisHook(
            lambda: StorageWorld(self._storage, retention=holder[0].retention),
            settings=base.settings(),
            adapter=base.adapter(),
            days=base.days(),
            adapter_of=base.skill_adapters(),
        )
        engine = _CallEngine(self._storage, hooks=(hook, *self._hooks))
        holder.append(engine)
        return engine

    def _daily_run(self, engine: Engine) -> None:
        """Once per study day, before the day's plan: the diagnosis flow cancels stale
        checks, runs the weak-spot finder and schedules diagnostic sets (ENG-15). First,
        once per launch: attempts graded under a since-changed answer key are voided
        (PACK-14), and memory is rebuilt for a fit an older build left half-applied."""
        if not self._launched:
            self._launched = True
            launch = Engine(self._storage)
            launch.void_changed_keys()  # PACK-14: a revised pack fixed an answer key
            launch.repair_fit()
        if not self._diagnosis:
            return
        users = self._storage.users
        today = self._today(engine).isoformat()
        if users.get_setting(DIAGNOSIS_DAY_KEY, None) == today:
            return
        Diagnosis(self._storage).daily()
        users.set_setting(DIAGNOSIS_DAY_KEY, today)

    def _now(self) -> int:
        return self._storage.db.clock.now_ms()

    def _today(self, engine: Engine | None = None) -> date:
        return (engine or self.engine()).days().day_of(self._now())

    def _settings(self, day: date) -> QueueSettings:
        return QueueSettings.from_values(self._storage.users.settings(), day)

    def _card(self, card_id: str) -> Card:
        """Cards are read-only while a pack is open (a pack update reopens storage)."""
        card = self._cards.get(card_id)
        if card is None:
            card = self._storage.packs.card(card_id)
            if card is None:
                raise QueueError(f"card {card_id} is no longer available")
            self._cards[card_id] = card
        return card

    def _ref(self, card: Card) -> CardRef:
        return CardRef(
            id=card.id,
            rev=card.rev,
            kind=card.kind,
            skill_id=card.skill_id,
            tier=card.tier,
            template_id=card.template_id,
            seed=card.seed,
            status=card.status,
            cue_required=card.cue_required,
            has_cued_question=card.cued_question_md is not None,
            source=self._storage.packs.card_source(card.id) or "user",
        )

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._lock:
            yield

    # ================================================================ home and plans

    def today(self) -> v.TodayView:
        """Home: today's problems and minutes per course, exams, proposals (QUE-3, 8, 13)."""
        with self._locked():
            engine = self.engine()
            open_session = self._open_session(engine)
            if open_session is None:
                self._daily_run(engine)
            snap = gather(self._storage, engine)
            if open_session is not None:
                plan = Plan.from_json(open_session.plan)
            else:
                plan = build_plan(snap)
                self._log_day(snap, plan)
            pending = [i for i in plan.items if i.pending]
            log = read_log(self._storage.users)
            proposals = []
            if snap.vacation is None or not snap.vacation.covers(snap.day):
                if overloaded(log, snap.day):
                    proposals.append(
                        v.Proposal(
                            kind="overload",
                            message="For three days your courses have needed more than your "
                            "daily count. A higher count for a while, a lower goal or moving "
                            "a course to Keep would bring it back in line.",
                            options=("raise-count", "lower-goal", "move-to-keep"),
                        )
                    )
                if backlog_stuck(log, snap.day):
                    proposals.append(
                        v.Proposal(
                            kind="backlog",
                            message="Reviews have been piling up for a week. A higher count, a "
                            "short re-check, or spreading the load over the next week would "
                            "clear it.",
                            options=("raise-count", "re-check", "spread"),
                        )
                    )
            return v.TodayView(
                day=snap.day.isoformat(),
                problems=sum(i.slots for i in pending),
                minutes=projected_minutes(pending),
                flashcards=sum(1 for i in pending if i.kind == "flashcard"),
                courses=self._course_lines(snap, pending),
                exams=self._exam_lines(snap),
                proposals=tuple(proposals),
                session_open=open_session is not None,
                done_today=open_session is None and not pending and bool(snap.done_today),
                vacation=bool(plan.info.get("vacation")),
                extra_practice_available=self._extra_available(engine),
                flashcards_to_rewrite=snap.flashcard_leeches,
            )

    def forecast(self, day: date | None = None) -> v.Forecast:
        """Tomorrow's plan (or any day's): problems and minutes, per course."""
        with self._locked():
            engine = self.engine()
            day = day or self._today(engine) + timedelta(days=1)
            snap = gather(self._storage, engine, day=day)
            plan = build_plan(snap)
            pending = plan.pending
            return v.Forecast(
                day=day.isoformat(),
                problems=sum(i.slots for i in pending),
                minutes=projected_minutes(pending),
                courses=self._course_lines(snap, pending),
            )

    def plan_preview(self, day: date | None = None) -> Plan:
        """The plan `start` would build for a day (tests, stats, debugging)."""
        with self._locked():
            engine = self.engine()
            return build_plan(gather(self._storage, engine, day=day))

    def _course_lines(self, snap: Snapshot, items: Sequence[PlanItem]) -> tuple[v.CourseLine, ...]:
        lines: dict[str, list[PlanItem]] = {}
        for item in items:
            lines.setdefault(item.course_id or "", []).append(item)
        titles = {c.id: c.title for c in self._storage.packs.courses()}
        return tuple(
            v.CourseLine(
                course_id=c,
                title=titles.get(c, c),
                problems=sum(i.slots for i in group),
                minutes=projected_minutes(group),
            )
            for c, group in sorted(lines.items())
        )

    def _exam_lines(self, snap: Snapshot) -> tuple[v.ExamLine, ...]:
        out = []
        for exam in sorted(self._storage.users.exams(), key=lambda e: e.at):
            exam_day = snap.days.day_of(exam.at)
            left = (exam_day - snap.day).days
            if left < 0:
                continue
            out.append(
                v.ExamLine(
                    exam_id=exam.id,
                    name=exam.name,
                    course_id=exam.course_id,
                    days_left=left,
                    practice_test=practice_tests_open(exam_day, snap.day),
                )
            )
        return tuple(out)

    def _log_day(self, snap: Snapshot, plan: Plan) -> None:
        """Record what today's fresh plan asked for (carry-over, QUE-8, QUE-13)."""
        if plan.mode not in DAILY_MODES or plan.info.get("vacation"):
            return
        if plan.info.get("done_before", 0) and snap.day in snap.log:
            return  # a restart later in the day plans the rest; keep the day's real quotas
        write_entry(
            self._storage.users,
            snap.day,
            DayEntry(
                n=int(plan.info.get("count", snap.settings.n)),
                need=int(plan.info.get("need", 0)),
                backlog=int(plan.info.get("backlog", 0)),
                quotas=dict(plan.quotas),
            ),
        )

    def _extra_available(self, engine: Engine) -> bool:
        return bool(engine.due_skills(self._today(engine) + timedelta(days=1)))

    # ================================================================ vacation (QUE-9)

    def set_vacation(self, start: date, end: date) -> None:
        if end < start:
            raise QueueError("A vacation ends on or after its first day.")
        write_vacation(self._storage.users, Vacation(start=start, end=end))

    def clear_vacation(self) -> None:
        write_vacation(self._storage.users, None)

    # ================================================================ goals (I2)

    def preview_goal(self, goal: CourseGoal | Mapping[str, Any]) -> v.GoalPreview:
        """What a new course goal would do to the queue: "This makes N skills due", and
        the days they would be spread over (nothing is saved)."""
        with self._locked():
            engine = self.engine()
            return self._goal_view(self._goal_change(_goal(goal), engine)[0])

    def set_goal(self, goal: CourseGoal | Mapping[str, Any]) -> v.GoalPreview:
        """Save a course goal. Live due dates follow it (ENG-1), so skills it makes due at
        once are spread over the next days with the load balancer, and every skill's cached
        due date is refreshed so QUE-4 escalation counts from the new dates (I2)."""
        with self._locked():
            engine = self.engine()
            new = _goal(goal)
            change, rows = self._goal_change(new, engine)
            users = self._storage.users
            users.set_course_goal(new)
            if rows:
                users.apply(rows)
            return self._goal_view(change)

    def _goal_change(self, new: CourseGoal, engine: Engine) -> tuple[GoalChange, list[SkillState]]:
        users = self._storage.users
        days, adapter, catalog = engine.days(), engine.adapter(), engine.catalog()
        adapter_of = engine.skill_adapters()  # each skill's own parameter set (decision 6)
        today = self._today(engine)
        old_goals = engine.goals()
        new_goals = {**old_goals, new.course_id: new}
        states = {
            k: s for k, s in users.skill_states().items() if catalog.course_of(k) == new.course_id
        }
        others = [s for k, s in users.skill_states().items() if k not in states]

        def old(k: str) -> float:
            return skill_retention(k, today, catalog, old_goals)

        def fresh(k: str) -> float:
            return skill_retention(k, today, catalog, new_goals)

        load = scheduled_load(
            others,
            today,
            SPREAD_DAYS,
            retention_of=old,
            adapter=adapter,
            days=days,
            adapter_of=adapter_of,
        )
        easy = users.settings().get("queue.easy_days") or {}
        change = goal_change(
            states.values(),
            today,
            old_retention=old,
            new_retention=fresh,
            adapter=adapter,
            days=days,
            load=load,
            easy_days=easy if isinstance(easy, dict) else {},
            adapter_of=adapter_of,
        )
        spread = {s.skill_id: s for s in change.states}
        rows = []
        for k, state in states.items():
            row = spread.get(k, state)
            due = due_day(row, fresh(k), adapter_of(k), days)
            cached = None if due is None else days.start(due)
            if row is not state or cached != state.due_at:
                rows.append(replace(row, due_at=cached))
        return change, rows

    def _goal_view(self, change: GoalChange) -> v.GoalPreview:
        return v.GoalPreview(
            newly_due=len(change.newly_due),
            message=change.message,
            per_day={d.isoformat(): n for d, n in change.per_day().items()},
        )

    # ================================================================ sessions

    def _open_session(self, engine: Engine) -> SessionState | None:
        """Today's open session. One left open from an earlier study day is closed first:
        its saved answer is graded, a practice test is graded, and the row is ended (QUE-16:
        a plan from before the rollover is rebuilt)."""
        users = self._storage.users
        session = users.latest_open_session()
        if session is None:
            return None
        if session.study_day == self._today(engine).isoformat():
            return self._recover(session, engine)
        session = self._recover(session, engine)
        plan = Plan.from_json(session.plan)
        if session.current and session.current.get("pending"):
            session, plan, _ = self._finalize(session, plan, engine)
        if plan.mode == "practice-test":
            self._grade_test(session, plan, engine)
        users.end_session(_id(session))
        return None

    def _recover(self, session: SessionState, engine: Engine) -> SessionState:
        """Finish a re-plan a crash interrupted (the answer committed, its follow-ups not)."""
        key = session.extra.get("replan")
        if not key:
            return session
        plan = Plan.from_json(session.plan)
        presentation = (session.current or {}).get("presentation_id")
        attempt = next(
            (
                a
                for a in self._storage.users.attempts(session_id=session.id, newest_first=True)
                if a.final and a.presentation_id == presentation
            ),
            None,
        )
        if attempt is not None:
            plan, extra = self._after_answer(session, plan, str(key), attempt, None, engine)
        else:
            extra = dict(session.extra)
        extra.pop("replan", None)
        current = dict(session.current or {})
        if attempt is not None:
            current["attempt_id"] = attempt.id
        return self._storage.users.save_session(
            replace(session, plan=plan.to_json(), current=current or None, extra=extra)
        )

    def _require(self, engine: Engine) -> tuple[SessionState, Plan]:
        session = self._open_session(engine)
        if session is None:
            raise QueueError("No study session is open. Press Start.")
        return session, Plan.from_json(session.plan)

    def resume(self) -> v.Turn | None:
        """QUE-16: the open session at the same problem, or None."""
        with self._locked():
            engine = self.engine()
            session = self._open_session(engine)
            return None if session is None else self._turn(session, engine)

    def current(self) -> v.Turn:
        with self._locked():
            engine = self.engine()
            session, _ = self._require(engine)
            return self._turn(session, engine)

    def start(self, request: v.StartRequest | Mapping[str, Any] | None = None) -> v.Turn:
        """Start a session, or resume today's open one (a daily start always resumes)."""
        req = request if isinstance(request, v.StartRequest) else v.StartRequest.from_dict(request)
        with self._locked():
            engine = self.engine()
            users = self._storage.users
            open_session = self._open_session(engine)
            if open_session is not None:
                mode = Plan.from_json(open_session.plan).mode
                if (req.mode in DAILY_MODES and mode in DAILY_MODES) or req.mode == mode:
                    if req.mode == "lighter" and mode == "daily":
                        return self._set_lighter(open_session, True, engine)
                    return self._turn(open_session, engine)
                self._close(open_session, engine)
            day = self._today(engine)
            settings = self._settings(day)
            plan = self._new_plan(req, engine, day)
            if not plan.items:
                return self._empty_turn(plan, engine)
            session = users.start_session(
                SessionState(
                    study_day=day.isoformat(),
                    started_at=self._now(),
                    untimed=settings.untimed_default if req.untimed is None else req.untimed,
                    plan=plan.to_json(),
                    extra={"active_total_ms": 0, "breaks": 0, "learned": []},
                )
            )
            session = self._advance(session, plan, engine)
            return self._turn(session, engine)

    def _new_plan(self, req: v.StartRequest, engine: Engine, day: date) -> Plan:
        mode = req.mode
        if mode in DAILY_MODES:
            self._daily_run(engine)
            snap = gather(self._storage, engine)
            plan = build_plan(snap, mode=mode, lighter=mode == "lighter")
            self._log_day(snap, plan)
            return plan
        if mode == "extra":
            snap = gather(self._storage, engine, day=day + timedelta(days=1), for_mode="extra")
            plan = build_plan(
                snap,
                mode="extra",
                n=req.count or EXTRA_DEFAULT,
                include_new=False,
                flashcards=False,
            )
            return replace(plan, day=day.isoformat())
        if mode == "focused":
            return self._focused_plan(req, engine)
        if mode == "practice-test":
            return self._test_plan(req, engine, day)
        raise QueueError(f"unknown study mode {mode!r}")

    def _empty_turn(self, plan: Plan, engine: Engine) -> v.Turn:
        if plan.info.get("vacation"):
            message = "Vacation mode is on: nothing is scheduled today."
        elif plan.mode in DAILY_MODES:
            message = "Today's plan is done. Extra practice is there if you want it."
        else:
            message = "Nothing to practice here right now."
        return v.Turn(type="empty", message=message, mode=plan.mode)

    def _close(self, session: SessionState, engine: Engine) -> None:
        plan = Plan.from_json(session.plan)
        if session.current and session.current.get("pending"):
            session, plan, _ = self._finalize(session, plan, engine)
        if plan.mode == "practice-test":
            self._grade_test(session, plan, engine)
        self._storage.users.end_session(_id(session))

    def end(self) -> v.Summary:
        """End the session: grade a saved answer, then the summary with tomorrow's forecast."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            if session.current and session.current.get("pending"):
                session, plan, _ = self._finalize(session, plan, engine)
            test = None
            if plan.mode == "practice-test":
                session, plan, test = self._grade_test(session, plan, engine)
            ended = self._storage.users.end_session(_id(session))
            summary = self._summary(ended, plan, engine, test)
        self.start_auto_fit()
        return summary

    # ================================================================ automatic fitting (I7)

    def start_auto_fit(self) -> bool:
        """I7: refit the parameter sets that are due, in the background, after a session
        ends (never mid-answer). The fitting runs outside the service lock; writing an
        adopted set and the recompute that follows take it, so they fall between two calls
        and never interleave with a graded answer. False when a fit is still running."""
        if self._fitter is not None and self._fitter.is_alive():
            return False
        self._fitter = threading.Thread(target=self._auto_fit, name="auto-fit", daemon=True)
        self._fitter.start()
        return True

    def _auto_fit(self) -> None:
        try:
            self.last_auto_fit = Engine(self._storage).auto_fit(writing=self._locked)
        except Exception as error:
            self.last_auto_fit = error

    def wait_for_auto_fit(self, timeout: float | None = None) -> bool:
        """Block until a background fit is done (tests, closing the profile)."""
        fitter = self._fitter
        if fitter is not None:
            fitter.join(timeout)
        return fitter is None or not fitter.is_alive()

    def set_lighter(self, on: bool = True) -> v.Turn:
        """QUE-10: same due skills, tier 1-2 problems, no new skills; successes count Hard."""
        with self._locked():
            engine = self.engine()
            session, _ = self._require(engine)
            return self._set_lighter(session, on, engine)

    def _set_lighter(self, session: SessionState, on: bool, engine: Engine) -> v.Turn:
        plan = Plan.from_json(session.plan)
        if plan.mode not in DAILY_MODES:
            raise QueueError("A Lighter set applies to the daily plan.")
        plan = replace(plan, lighter=on, mode="lighter" if on else "daily")
        if on:
            started = {i.block for i in plan.done if i.block}
            drop = [i.key for i in plan.pending if i.order == NEW and i.block not in started]
            plan = rebalance(plan, drop=drop, confusable=self._confusable(engine))
        cur = session.current
        if cur is not None and plan.item(str(cur["key"])) is None:
            # QUE-10 adds no new skills: a block counts as started once one of its items is
            # done, so the worked example on screen leaves with its skill (nothing of it is
            # graded yet) and the session moves on to the next item, still resumable (QUE-16).
            session = self._advance(replace(session, current=None), plan, engine)
        else:
            session = self._storage.users.save_session(replace(session, plan=plan.to_json()))
        return self._turn(session, engine)

    # ================================================================ serving

    def _confusable(self, engine: Engine) -> dict[str, frozenset[str]]:
        if isinstance(engine, _CallEngine):
            return engine.confusable()
        return confusable_map(engine.catalog())

    def _advance(self, session: SessionState, plan: Plan, engine: Engine) -> SessionState:
        """Make the first pending item current (picking its problem) and save."""
        users = self._storage.users
        now = self._now()
        while True:
            item = plan.first_pending()
            if item is None:
                return users.save_session(
                    replace(session, plan=plan.to_json(), current=None, active_ms=0, draft=None)
                )
            if self._example_first(item, plan):
                plan, key = plan.next_key("exf")
                example = replace(
                    item,
                    key=key,
                    kind="example",
                    tag="relearn",
                    label=TAG_LABELS["relearn"],
                    why=why("relearn.example"),
                    card_id=None,
                    anchor=None,
                    gap=0,
                    check_id=None,
                    check_kind=None,
                    stretch=False,
                    block=None,
                    est_ms=EXAMPLE_MS,
                    inserted=True,
                )
                items = list(plan.items)
                items.insert(plan.index(item.key), example)
                plan = plan.with_items(items)
                continue
            picked = self._pick(item, plan, engine, now)
            if picked is None:
                plan = plan.updated(replace(item, status="skipped", result={"no_problem": True}))
                plan = rebalance(
                    plan, prefer_course=item.course_id, confusable=self._confusable(engine)
                )
                continue
            card_id, stretch = picked
            if item.stretch and not stretch:  # the engine declined the stretch tier
                item = replace(item, stretch=False, tag="review", label="Review", why=why("review"))
                plan = plan.updated(item)
            card = self._card(card_id)
            if card.kind == "find-error" and item.card_id is None and item.kind == "problem":
                item = replace(item, why=why("review.find-error"))
                plan = plan.updated(item)
            current = {
                "key": item.key,
                "card_id": card_id,
                "rev": card.rev,
                "presentation_id": _uid(),
                "shown_at": now,
                "tries": 0,
                "hints": 0,
                "last_hint": False,
                "example_opened": False,
                "stretch": stretch,
                "pending": None,
                "closed": False,
            }
            if card.kind == "find-error":  # early on: "Step 3 is wrong. Why?"
                history = users.attempts(skill_id=card.skill_id) if card.skill_id else []
                current["highlighted"] = find_error_highlighted(history)
            return users.save_session(
                replace(
                    session,
                    plan=plan.to_json(),
                    position=plan.index(item.key),
                    current=current,
                    active_ms=0,
                    draft=None,
                )
            )

    def _example_first(self, item: PlanItem, plan: Plan) -> bool:
        """The diagnosis flow asked for a worked example before this skill's next problem
        (an unsolved cued twin); the example is served first and clears the request."""
        return (
            self._diagnosis
            and item.kind == "problem"
            and item.skill_id is not None
            and plan.mode != "practice-test"
            and Diagnosis(self._storage).needs_example(item.skill_id)
        )

    def _pick(
        self, item: PlanItem, plan: Plan, engine: Engine, now: int
    ) -> tuple[str, bool] | None:
        users, packs = self._storage.users, self._storage.packs
        marks = users.card_marks()
        hidden = {k for k, m in marks.items() if m.hidden or m.suspended}
        if item.kind == "flashcard":
            return (item.card_id, False) if item.card_id and item.card_id not in hidden else None
        if item.kind == "example":
            refs = [
                r
                for r in packs.card_refs(skill_id=item.skill_id)
                if r.kind == "example" and r.id not in hidden
            ]
            if not refs:
                # ENG-2: no example card, so a tier 1 problem is shown solved instead (never
                # graded; it is not served again as a problem today).
                if item.skill_id is None:
                    return None
                shown = engine.pick_problem(
                    item.skill_id, at_ms=now, tiers=(1,), kinds=("problem",)
                )
                return None if shown is None else (shown.card.id, False)
            seen = users.card_users()
            best = min(refs, key=lambda r: (seen[r.id].last_seen_at or 0) if r.id in seen else -1)
            return best.id, False
        if item.card_id and item.card_id not in hidden:
            return item.card_id, item.stretch
        if item.skill_id is None:
            return None
        last = users.attempts(skill_id=item.skill_id, limit=1, newest_first=True)
        last_id = last[0].card_id if last else None
        if item.method:  # ENG-16: which-method items, only while the skill is active
            if not Diagnosis(self._storage).method_choice_active(item.skill_id):
                return None
            pick = engine.pick_problem(
                item.skill_id, last_card_id=last_id, at_ms=now, kinds=("method",)
            )
            return None if pick is None else (pick.card.id, False)
        found = self._find_error(item, plan, engine, now)
        if found is not None:
            return found, False
        pick = engine.pick_problem(
            item.skill_id,
            stretch=item.stretch,
            lighter_set=plan.lighter,
            last_card_id=last_id,
            at_ms=now,
            kinds=("problem",),
        )
        return None if pick is None else (pick.card.id, pick.stretch)

    def _find_error(self, item: PlanItem, plan: Plan, engine: Engine, now: int) -> str | None:
        """A find-the-error item in place of a skill's review problem (it counts as the
        review): once the skill has two successful uncued reviews, at most one in every
        `queue.find_error_one_in` problems served (setting, 1 in 10; None turns them off),
        and never a card seen in the last 90 days."""
        if (
            plan.mode == "practice-test"
            or item.skill_id is None
            or item.stretch
            or item.block is not None
            or item.check_id is not None
            or item.anchor is not None
            or item.purpose not in ("review", "booster", "checkup", "focused")
        ):
            return None
        users, packs = self._storage.users, self._storage.packs
        one_in = DiagnosisSettings.from_settings(users.settings()).find_error_one_in
        if one_in is None:
            return None
        seen = users.card_users()
        fresh = [
            r
            for r in packs.card_refs(skill_id=item.skill_id)
            if r.kind == "find-error"
            and r.status == "active"
            and (
                r.id not in seen
                or seen[r.id].last_seen_at is None
                or now - int(seen[r.id].last_seen_at or 0) >= SEEN_SKIP_DAYS * DAY_MS
            )
        ]
        if not fresh or memory_of(users.skill_state(item.skill_id)) is None:
            return None
        if not find_error_unlocked(users.attempts(skill_id=item.skill_id)):
            return None
        recent = [
            a.card_kind
            for a in users.attempts(limit=4 * one_in, newest_first=True)
            if a.final and a.card_kind in ("problem", "find-error", "method")
        ][: max(0, one_in - 1)]
        if not find_error_slot_open(list(reversed(recent)), one_in):
            return None
        pick = engine.pick_problem(item.skill_id, at_ms=now, kinds=("find-error",))
        if pick is None or pick.card.id not in {r.id for r in fresh}:
            return None
        return pick.card.id

    # ================================================================ turns and views

    def _turn(
        self,
        session: SessionState,
        engine: Engine,
        *,
        message: str = "",
        break_due: bool = False,
    ) -> v.Turn:
        plan = Plan.from_json(session.plan)
        cur = session.current
        if cur is None:
            if plan.mode == "practice-test" or not plan.pending:
                summary = self._end_after_last(session, plan, engine)
                return v.Turn(
                    type="summary",
                    session_id=session.id,
                    summary=summary,
                    message=message,
                    mode=plan.mode,
                )
            session = self._advance(session, plan, engine)
            return self._turn(session, engine, message=message, break_due=break_due)
        item = plan.item(str(cur["key"]))
        if item is None:
            raise StorageError("the session's current item is missing from its plan")
        result = None
        if cur.get("pending") or cur.get("closed"):
            result = self._result_view(session, plan, item, engine)
        return v.Turn(
            type="problem",
            session_id=session.id,
            problem=self._problem_view(session, plan, item, engine),
            progress=self._progress(plan, item),
            result=result,
            message=message,
            break_due=break_due,
            lighter=plan.lighter,
            mode=plan.mode,
        )

    def _end_after_last(self, session: SessionState, plan: Plan, engine: Engine) -> v.Summary:
        test = None
        if plan.mode == "practice-test":
            session, plan, test = self._grade_test(session, plan, engine)
        ended = self._storage.users.end_session(_id(session))
        return self._summary(ended, plan, engine, test)

    def _progress(self, plan: Plan, item: PlanItem) -> v.Progress:
        done = [i for i in plan.items if i.status == "done" and i.slots]
        on_screen = 1 if item.slots and item.pending else 0
        return v.Progress(
            position=len(done) + on_screen,
            total=sum(i.slots for i in plan.items if i.status != "skipped"),
            answered=len(done),
            correct=sum(1 for i in done if (i.result or {}).get("correct")),
        )

    def _attempts_allowed(
        self, plan: Plan, item: PlanItem, cur: Mapping[str, Any] | None = None
    ) -> int:
        """Tries per answer box. One for practice tests, which-method items (a choice among
        three or four) and find-the-error items (graded on the step, reason and value)."""
        if plan.mode == "practice-test" or item.kind != "problem" or item.method:
            return 1
        card_id = (cur or {}).get("card_id")
        if card_id is not None and self._card(str(card_id)).kind in ("method", "find-error"):
            return 1
        return max(1, self._settings(date.fromisoformat(plan.day)).attempts_per_problem)

    def _problem_view(
        self, session: SessionState, plan: Plan, item: PlanItem, engine: Engine
    ) -> v.ProblemView:
        cur = session.current or {}
        card = self._card(str(cur["card_id"]))
        hints = card.hints[: int(cur.get("hints", 0))]
        return v.ProblemView(
            item_key=item.key,
            kind=item.kind,
            card=self._card_view(
                card,
                cued=item.check_kind == "cued-twin",
                ord_=item.card_ord,
                highlighted=bool(cur.get("highlighted")),
                as_example=item.kind == "example",
            ),
            reason=v.Reason(tag=item.tag, label=item.label, why=item.why),
            attempts_allowed=self._attempts_allowed(plan, item, cur),
            tries_used=int(cur.get("tries", 0)),
            hints_shown=tuple(hints),
            draft=session.draft,
            active_ms=session.active_ms,
            target_ms=None,
            untimed=session.untimed,
            practice_test=plan.mode == "practice-test",
        )

    def _card_view(
        self,
        card: Card,
        *,
        cued: bool = False,
        ord_: int = 0,
        highlighted: bool = False,
        as_example: bool = False,
    ) -> v.CardView:
        prompt = card.question_md or card.front_md or card.text_md or ""
        if cued and card.cued_question_md:
            prompt = card.cued_question_md  # a cued twin names the method
        back = card.back_md if card.kind == "flashcard" else None
        if card.kind == "cloze":  # one blank number per item, like Anki
            prompt = cloze.front(card.text_md, ord_)
            back = cloze.back(card.text_md, ord_)
            if card.extra_md:
                back += "\n\n" + card.extra_md
        specs = specs_for(card)
        parts = tuple(
            v.PartView(
                label=p.label,
                prompt_md=p.prompt_md,
                answer_type=p.answer_type,
                choices=tuple(
                    v.ChoiceView(index=i, text_md=c.text_md) for i, c in enumerate(p.choices)
                ),
                multiple=sum(1 for c in p.choices if c.correct) > 1,
            )
            for p in card.parts
        ) or (
            v.PartView(
                label=None,
                prompt_md=None,
                answer_type=card.answer_type,
                choices=tuple(
                    v.ChoiceView(index=i, text_md=c.text_md) for i, c in enumerate(card.choices)
                ),
                multiple=sum(1 for c in card.choices if c.correct) > 1,
            ),
        )
        return v.CardView(
            id=card.id,
            rev=card.rev,
            kind=card.kind,
            prompt_md=prompt,
            parts=parts,
            hint_count=len(card.hints),
            calculator=card.calculator,
            angles=card.angles,
            plot=card.plot,
            self_graded=any(s.spec.answer_type == "self" for s in specs),
            back_md=back,
            solution_md=card.solution_md
            if card.kind == "example"
            else _worked_md(card)
            if as_example  # a problem shown solved in place of an example card (ENG-2)
            else None,
            shown_work=_work(card),
            reasons=tuple(
                v.ChoiceView(index=i, text_md=c.text_md) for i, c in enumerate(card.reasons)
            ),
            error_step=card.error_step if card.kind == "find-error" and highlighted else None,
            cloze=ord_ + 1 if card.kind == "cloze" else None,
            type_answer=card.kind == "flashcard" and card.answer is not None,
        )

    def _solution_view(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        engine: Engine,
        *,
        correct: bool,
        pending: Mapping[str, Any],
    ) -> v.SolutionView:
        card = self._card(str((session.current or {})["card_id"]))
        catalog = engine.catalog()
        skill_id = card.skill_id
        skill = catalog.skills.get(skill_id or "")

        def name(k: str | None) -> str | None:
            s = catalog.skills.get(k or "")
            return s.name if s is not None else None

        active = pending.get("timing", {}).get("active_ms")
        target = None
        level = engine.level(skill_id) if skill_id else None
        if skill_id and not session.untimed and level in ("learned", "exam", "mastered"):
            target = engine.target_time(skill_id, card.tier)
        time_text = None
        if active is not None and not session.untimed:
            time_text = _clock(int(active)) + (f" · target {_clock(target)}" if target else "")
        first_clean = (
            correct
            and int(pending.get("attempt_number", 1)) == 1
            and int(pending.get("hints_used", 0)) == 0
            and not pending.get("unsure")
        )
        easy_key = bool(self._storage.users.get_setting("rating.too_easy_key", True))
        return v.SolutionView(
            skill_id=skill_id,
            skill_name=skill.name if skill is not None else None,
            answer_md=card.answer_md or card.answer,
            solution_md=card.solution_md,
            steps=tuple(
                v.StepView(
                    number=s.number,
                    skill_id=s.skill_id,
                    skill_name=name(s.skill_id),
                    label=s.label,
                    body_md=s.body_md,
                )
                for s in card.solution
            ),
            alternative_md=card.alternative_solution_md,
            active_ms=None if active is None else int(active),
            target_ms=target,
            time_text=time_text,
            needs_diagnosis=not correct
            and plan.mode != "practice-test"
            and item.kind == "problem"
            and card.kind == "problem",  # the picker is about one's own worked solution
            # Only what the engine recorded for this answer (never recomputed here): an
            # answer not graded yet has no confident error to show.
            confident_error=not correct and bool((session.current or {}).get("confident_error")),
            can_mark_too_easy=first_clean and easy_key,
            textbook_ref=skill.textbook_ref if skill is not None and not correct else None,
            rubric=card.rubric,
            shown_work=_work(card),
            preselect_step=None
            if correct
            else next(
                (
                    int(p["wrong_step"])
                    for p in pending.get("verdicts", ())
                    if p.get("wrong_step") is not None
                ),
                None,
            ),
        )

    def _result_view(
        self, session: SessionState, plan: Plan, item: PlanItem, engine: Engine
    ) -> v.AttemptResult:
        cur = session.current or {}
        pending = cur.get("pending") or cur.get("answer") or {}
        correct = bool(pending.get("correct"))
        if item.kind != "problem":
            return v.AttemptResult(
                item_key=item.key, outcome="recorded", rating=(item.result or {}).get("rating")
            )
        return v.AttemptResult(
            item_key=item.key,
            outcome=_outcome_of(pending),
            verdicts=tuple(v.PartVerdictView(**p) for p in pending.get("verdicts", ())),
            solution=self._solution_view(
                session, plan, item, engine, correct=correct, pending=pending
            ),
            tries_used=int(cur.get("tries", 0)),
            attempts_allowed=self._attempts_allowed(plan, item, cur),
            find_error=_find_error_view(pending),
        )

    # ================================================================ answering

    def read_answer(self, raw: str, *, part: str | None = None, source: v.Source = "text") -> Any:
        """The live "We read your answer as ..." preview (never an attempt)."""
        with self._locked():
            engine = self.engine()
            session, _ = self._require(engine)
            card = self._card(str((session.current or {})["card_id"]))
            spec = next((p.spec for p in specs_for(card) if p.label == part), None)
            if spec is None:
                spec = specs_for(card)[0].spec
            return self._previewer(raw, spec, source)

    def tick(self, active_ms: int, draft: str | None = None) -> v.Tick:
        """Save the active time so far and the typed draft (QUE-16); break reminders."""
        with self._locked():
            engine = self.engine()
            session, _ = self._require(engine)
            cur = session.current or {}
            guarded = guard_timing(
                TimingReport(active_ms=active_ms),
                shown_at=cur.get("shown_at"),
                now_ms=self._now(),
                saved_active_ms=session.active_ms,
            ).timing
            active = guarded.active_ms or 0
            session, due = self._note_active(session, active)
            session = self._storage.users.save_session(
                replace(
                    session, active_ms=active, draft=draft if draft is not None else session.draft
                )
            )
            return v.Tick(saved=True, active_ms=active, break_due=due)

    def _note_active(self, session: SessionState, active_ms: int) -> tuple[SessionState, bool]:
        """Add the new active time to the session total; usage-based backups; a break
        reminder every `ui.break_reminder_minutes` (50) of active time."""
        delta = max(0, active_ms - session.active_ms)
        extra = dict(session.extra)
        total = int(extra.get("active_total_ms", 0)) + delta
        extra["active_total_ms"] = total
        due = False
        minutes = self._storage.users.get_setting("ui.break_reminder_minutes", 50)
        if minutes:
            reached = total // (int(minutes) * MINUTE_MS)
            if reached > int(extra.get("breaks", 0)):
                extra["breaks"] = int(reached)
                due = True
        if delta:
            self._storage.note_use(delta)
        return replace(session, extra=extra, active_ms=max(session.active_ms, active_ms)), due

    def _current_item(
        self, session: SessionState, plan: Plan, key: str | None = None
    ) -> tuple[dict[str, Any], PlanItem]:
        cur = dict(session.current or {})
        if not cur:
            raise QueueError("There is no problem on screen.")
        if key is not None and key != cur["key"]:
            raise QueueError("That problem is no longer on screen.")
        item = plan.item(str(cur["key"]))
        if item is None:
            raise StorageError("the session's current item is missing from its plan")
        return cur, item

    def submit(self, request: v.SubmitRequest | Mapping[str, Any]) -> v.AttemptResult:
        req = (
            request if isinstance(request, v.SubmitRequest) else v.SubmitRequest.from_dict(request)
        )
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan, req.item_key)
            if item.kind == "example":
                raise QueueError("A worked example has no answer to submit; continue.")
            if item.kind == "flashcard":
                raise QueueError("Rate the flashcard instead.")
            if cur.get("pending") or cur.get("closed"):
                raise QueueError("This problem is already answered; continue.")
            card = self._card(str(cur["card_id"]))
            now = self._now()
            specs = specs_for(card)
            guarded = guard_timing(
                req.timing,
                shown_at=cur.get("shown_at"),
                now_ms=now,
                saved_active_ms=session.active_ms,
                expected_chars=sum(s.expected_chars for s in specs),
            )
            session, break_due = self._note_active(session, guarded.timing.active_ms or 0)
            raw = " | ".join(a.value for a in req.answers) if req.answers else None
            base = {
                "at": now,
                "attempt_number": int(cur.get("tries", 0)) + 1,
                "hints_used": _hints_used(cur),
                "last_hint_used": bool(cur.get("last_hint")),
                "unsure": req.confidence == "unsure",
                "guessed": req.guessed,
                "timing": _timing_json(guarded.timing),
                "flags": list(guarded.flags),
                "raw_input": raw,
            }
            if plan.mode == "practice-test":
                return self._submit_test(session, plan, item, cur, card, req, base, engine)

            self_graded = any(s.spec.answer_type == "self" for s in specs)
            if req.self_grade is not None or req.rubric_ticked is not None:
                if not (self_graded or cur.get("self_grade")):
                    raise QueueError("This problem is graded automatically.")
                pending = {
                    **base,
                    **_self_graded(card, req),
                    "verdict": "undecided" if cur.get("undecided") else "self",
                    "verdicts": [],
                }
                return self._hold(session, plan, item, cur, pending, engine, break_due)
            if card.parts and not self_graded:
                return self._submit_parts(
                    session, plan, item, cur, card, req, base, engine, break_due, guarded.flags
                )

            checked = check_answers(
                card,
                [(a.part, a.value) for a in req.answers],
                req.answers[0].source if req.answers else "text",
                self._checker,
            )
            verdicts: list[dict[str, Any]] = [
                {
                    "part": p.part,
                    "status": p.status,
                    "read_as": p.read_as,
                    "message": p.message,
                    "feedback": p.feedback,
                    "wrong_step": p.wrong_step,
                }
                for p in checked.verdicts
            ]
            if checked.invalid:
                self._storage.users.save_session(replace(session, draft=raw))
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="invalid",
                    verdicts=tuple(v.PartVerdictView(**p) for p in verdicts),
                    message="Not counted: fix the answer's form and submit again.",
                    tries_used=int(cur.get("tries", 0)),
                    attempts_allowed=self._attempts_allowed(plan, item),
                    break_due=break_due,
                )
            if checked.undecided:
                cur.update(self_grade=True, undecided=not self_graded)
                session = self._storage.users.save_session(replace(session, current=cur, draft=raw))
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="self-grade",
                    verdicts=tuple(v.PartVerdictView(**p) for p in verdicts),
                    message="Compare your work with the solution and grade it yourself.",
                    solution=self._solution_view(
                        session, plan, item, engine, correct=False, pending=base
                    ),
                    tries_used=int(cur.get("tries", 0)),
                    attempts_allowed=self._attempts_allowed(plan, item),
                    break_due=break_due,
                )
            if card.kind == "find-error":
                return self._submit_find_error(
                    session, plan, item, cur, card, req, base, verdicts, checked, engine, break_due
                )
            tries = int(cur.get("tries", 0)) + 1
            allowed = self._attempts_allowed(plan, item, cur)
            if not checked.correct and tries < allowed:
                cur["tries"] = tries
                cur["last_verdicts"] = verdicts  # "Your answer" if the student then gives up
                extra = {k: val for k, val in session.extra.items() if k != "undo"}
                trying = replace(session, current=cur, draft=None, extra=extra)
                facts = AnswerFacts(
                    correct=False, attempt_number=tries, hints_used=_hints_used(cur)
                )
                outcome = self._outcome(
                    trying,
                    plan,
                    item,
                    cur,
                    facts=facts,
                    timing=guarded.timing,
                    at=now,
                    raw=raw,
                    parsed=_parsed(verdicts),
                    verdict="incorrect",
                    matched_wrong=checked.matched_index,
                    flags=guarded.flags,
                )
                engine.record_try(outcome)
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="retry",
                    verdicts=tuple(v.PartVerdictView(**p) for p in verdicts),
                    message="Not quite.",
                    tries_used=tries,
                    attempts_allowed=allowed,
                    break_due=break_due,
                )
            pending = {
                **base,
                "correct": checked.correct,
                "verdict": "correct" if checked.correct else "incorrect",
                "verdicts": verdicts,
                "parsed": _parsed(verdicts),
                "matched_wrong": checked.matched_index,
            }
            return self._hold(session, plan, item, cur, pending, engine, break_due)

    def _submit_parts(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        req: v.SubmitRequest,
        base: dict[str, Any],
        engine: Engine,
        break_due: bool,
        flags: Sequence[str],
    ) -> v.AttemptResult:
        """Multi-part problems: one box, verdict and attempt count per part. A part is final
        once right or out of tries; the problem is graded when every part is final (a part
        with its own skill reports to it; the card's skill takes the worst of the rest)."""
        allowed = self._attempts_allowed(plan, item, cur)
        state: dict[str, dict[str, Any]] = {
            str(k): dict(x) for k, x in dict(cur.get("parts") or {}).items()
        }
        given = {a.part: a for a in req.answers if a.part is not None}
        targets = [
            p.label
            for p in card.parts
            if p.label in given and not state.get(p.label, {}).get("final")
        ]
        if not targets:
            raise QueueError("Enter an answer for a part that is still open.")
        source = given[targets[0]].source
        checked = check_answers(
            card, [(k, given[k].value) for k in targets], source, self._checker, only=targets
        )
        raw = " | ".join(f"{k}: {given[k].value}" for k in targets)

        def view(p: Any, final: bool, tries: int) -> dict[str, Any]:
            return {
                "part": p.part,
                "status": p.status,
                "read_as": p.read_as,
                "message": p.message,
                "feedback": p.feedback,
                "wrong_step": p.wrong_step,
                "final": final,
                "tries_used": tries,
            }

        def shown() -> list[dict[str, Any]]:
            return [
                state[p.label]["verdict"] for p in card.parts if "verdict" in state.get(p.label, {})
            ]

        if checked.invalid:
            fresh = [
                view(p, False, state.get(p.part or "", {}).get("tries", 0))
                for p in checked.verdicts
            ]
            self._storage.users.save_session(replace(session, draft=raw))
            return v.AttemptResult(
                item_key=item.key,
                outcome="invalid",
                verdicts=tuple(v.PartVerdictView(**p) for p in fresh),
                message="Not counted: fix the answer's form and submit again.",
                tries_used=int(cur.get("tries", 0)),
                attempts_allowed=allowed,
                break_due=break_due,
            )
        if checked.undecided:  # the checker can't decide a part: the student grades it all
            cur.update(self_grade=True, undecided=True)
            session = self._storage.users.save_session(replace(session, current=cur, draft=raw))
            return v.AttemptResult(
                item_key=item.key,
                outcome="self-grade",
                verdicts=tuple(v.PartVerdictView(**p) for p in [*shown()]),
                message="Compare your work with the solution and grade it yourself.",
                solution=self._solution_view(
                    session, plan, item, engine, correct=False, pending=base
                ),
                tries_used=int(cur.get("tries", 0)),
                attempts_allowed=allowed,
                break_due=break_due,
            )
        retrying: list[str] = []
        for p in checked.verdicts:
            label = str(p.part)
            entry = state.setdefault(label, {"tries": 0})
            entry["tries"] = int(entry.get("tries", 0)) + 1
            entry["correct"] = p.status == Status.CORRECT
            entry["final"] = entry["correct"] or entry["tries"] >= allowed
            entry["verdict"] = view(p, entry["final"], entry["tries"])
            entry["raw"] = given[label].value
            entry["read_as"] = p.read_as
            if not entry["final"]:
                retrying.append(label)
        cur["parts"] = state
        cur["tries"] = max(int(x.get("tries", 0)) for x in state.values())
        now = int(base["at"])
        for label in retrying:  # each "Not quite" is logged at once, against its part
            entry = state[label]
            trying = replace(
                session,
                current=cur,
                extra={k: val for k, val in session.extra.items() if k != "undo"},
            )
            outcome = self._outcome(
                trying,
                plan,
                item,
                cur,
                facts=AnswerFacts(
                    correct=False,
                    attempt_number=int(entry["tries"]),
                    hints_used=_hints_used(cur),
                ),
                timing=TimingFacts(**base.get("timing", {})),
                at=now,
                raw=str(entry["raw"]),
                parsed=entry.get("read_as"),
                verdict="incorrect",
                flags=flags,
            )
            engine.record_try(replace(outcome, part=label))
        if not all(state.get(p.label, {}).get("final") for p in card.parts):
            extra = {k: val for k, val in session.extra.items() if k != "undo"}
            self._storage.users.save_session(replace(session, current=cur, draft=None, extra=extra))
            return v.AttemptResult(
                item_key=item.key,
                outcome="retry",
                verdicts=tuple(v.PartVerdictView(**p) for p in shown()),
                message="Not quite." if retrying else "Saved. Now the other parts.",
                tries_used=int(cur["tries"]),
                attempts_allowed=allowed,
                break_due=break_due,
            )
        outcomes = [
            PartOutcome(
                label=p.label,
                skill_id=p.skill_id,
                correct=bool(state[p.label].get("correct")),
                attempts=int(state[p.label].get("tries", 1)),
                gave_up=bool(state[p.label].get("gave_up")),
            )
            for p in card.parts
        ]
        facts = card_facts(AnswerFacts(correct=False), outcomes, card.skill_id or "")
        final = shown()
        pending = {
            **base,
            "raw_input": " | ".join(
                f"{p.label}: {state[p.label].get('raw', '')}" for p in card.parts
            ),
            "attempt_number": facts.attempt_number,
            "correct": facts.correct,
            "verdict": "correct" if facts.correct else "incorrect",
            "verdicts": final,
            "parsed": _parsed(final),
            "parts": [o.as_json() for o in outcomes],
        }
        return self._hold(session, plan, item, cur, pending, engine, break_due)

    def _submit_find_error(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        req: v.SubmitRequest,
        base: dict[str, Any],
        verdicts: list[dict[str, Any]],
        checked: Any,
        engine: Engine,
        break_due: bool,
    ) -> v.AttemptResult:
        """Find-the-error: graded on the step picked (given in the highlighted version), the
        reason chosen and the corrected value; then the correct solution appears beside the
        shown work. It counts as a review of the card's skill."""
        step = card.error_step if cur.get("highlighted") else req.error_step
        if step is None or req.reason is None:
            raise QueueError("Pick the wrong step and why it is wrong, then type the fix.")
        grade = grade_find_error(card, step=step, reason=req.reason, value_correct=checked.correct)
        pending = {
            **base,
            "correct": grade.correct,
            "verdict": "correct" if grade.correct else "incorrect",
            "verdicts": verdicts,
            "parsed": _parsed(verdicts),
            "find_error": {
                "error_step": card.error_step,
                "right_reason": next((i for i, r in enumerate(card.reasons) if r.correct), None),
                "step_ok": grade.step_ok,
                "reason_ok": grade.reason_ok,
                "value_ok": grade.value_ok,
            },
        }
        return self._hold(session, plan, item, cur, pending, engine, break_due)

    def show_solution(self) -> v.AttemptResult:
        """Self-graded problems: the Show solution button. The solution (and the rubric to
        tick, if the card has one) appears; then `submit` with `rubric_ticked` (all ticked
        Good, all but one Hard, fewer Again) or `self_grade` (Matched / Minor slip / Didn't
        get it). Nothing is graded yet."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            if item.kind != "problem" or plan.mode == "practice-test":
                raise QueueError("There is no solution to show here.")
            if cur.get("pending") or cur.get("closed"):
                raise QueueError("This problem is already answered; continue.")
            card = self._card(str(cur["card_id"]))
            if not (
                any(p.spec.answer_type == "self" for p in specs_for(card)) or cur.get("self_grade")
            ):
                raise QueueError("This problem is graded automatically.")
            if not cur.get("solution_shown"):
                cur["solution_shown"] = True
                cur["solution_shown_at"] = self._now()
                session = self._storage.users.save_session(replace(session, current=cur))
            return v.AttemptResult(
                item_key=item.key,
                outcome="self-grade",
                message=(
                    "Tick the steps your work matched."
                    if card.rubric
                    else "Matched the solution, a minor slip, or didn't get it?"
                ),
                solution=self._solution_view(
                    session, plan, item, engine, correct=False, pending={}
                ),
                tries_used=int(cur.get("tries", 0)),
                attempts_allowed=self._attempts_allowed(plan, item, cur),
            )

    def give_up(self, timing: TimingReport | Mapping[str, Any] | None = None) -> v.AttemptResult:
        report = timing if isinstance(timing, TimingReport) else TimingReport.from_dict(timing)
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            if item.kind != "problem":
                raise QueueError("Only a problem can be given up.")
            if cur.get("pending") or cur.get("closed"):
                raise QueueError("This problem is already answered; continue.")
            now = self._now()
            guarded = guard_timing(
                report, shown_at=cur.get("shown_at"), now_ms=now, saved_active_ms=session.active_ms
            )
            session, break_due = self._note_active(session, guarded.timing.active_ms or 0)
            pending = {
                "at": now,
                "correct": False,
                "gave_up": True,
                "attempt_number": int(cur.get("tries", 0)) + 1,
                "hints_used": _hints_used(cur),
                "last_hint_used": bool(cur.get("last_hint")),
                "verdict": "gave-up",
                # The last attempt stays "Your answer" beside the correct one (spec).
                "verdicts": list(cur.get("last_verdicts") or []),
                "timing": _timing_json(guarded.timing),
                "flags": list(guarded.flags),
            }
            card = self._card(str(cur["card_id"]))
            if plan.mode == "practice-test":
                return self._submit_test(
                    session, plan, item, cur, card, v.SubmitRequest(), pending, engine
                )
            auto = not cur.get("self_grade") and all(
                p.spec.answer_type != "self" for p in specs_for(card)
            )
            if card.parts and auto:  # the parts still open are given up
                state = {str(k): dict(x) for k, x in dict(cur.get("parts") or {}).items()}
                outcomes = []
                for p in card.parts:
                    entry = state.get(p.label, {})
                    done = bool(entry.get("final"))
                    outcomes.append(
                        PartOutcome(
                            label=p.label,
                            skill_id=p.skill_id,
                            correct=done and bool(entry.get("correct")),
                            attempts=int(entry.get("tries", 0)) + (0 if done else 1),
                            gave_up=not done,
                        )
                    )
                facts = card_facts(AnswerFacts(correct=False), outcomes, card.skill_id or "")
                pending.update(
                    correct=facts.correct,
                    gave_up=facts.gave_up,
                    attempt_number=max(1, facts.attempt_number),
                    verdict="gave-up"
                    if facts.gave_up
                    else "correct"
                    if facts.correct
                    else "incorrect",
                    verdicts=[e["verdict"] for e in state.values() if "verdict" in e],
                    parts=[o.as_json() for o in outcomes],
                )
            return self._hold(session, plan, item, cur, pending, engine, break_due)

    def _hold(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        pending: dict[str, Any],
        engine: Engine,
        break_due: bool,
    ) -> v.AttemptResult:
        """Save a final answer in the session row; it is graded on continue or diagnose."""
        cur["pending"] = pending
        cur["tries"] = int(pending.get("attempt_number", 1))
        extra = {k: val for k, val in session.extra.items() if k != "undo"}
        session = self._storage.users.save_session(
            replace(session, current=cur, draft=pending.get("raw_input"), extra=extra)
        )
        correct = bool(pending.get("correct"))
        outcome = _outcome_of(pending)
        return v.AttemptResult(
            item_key=item.key,
            outcome=outcome,
            verdicts=tuple(v.PartVerdictView(**p) for p in pending.get("verdicts", ())),
            message="" if outcome == "correct" else "Here is the full solution.",
            solution=self._solution_view(
                session, plan, item, engine, correct=correct, pending=pending
            ),
            tries_used=cur["tries"],
            attempts_allowed=self._attempts_allowed(plan, item, cur),
            break_due=break_due,
            find_error=_find_error_view(pending),
        )

    def hint(self) -> v.HintReveal:
        """The next hint of the card's ladder: any hint caps the rating at Hard, the last
        one (it gives the first step) counts as Again."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            if plan.mode == "practice-test":
                raise QueueError("No hints during a practice test.")
            if not self._settings(self._today(engine)).hints:
                raise QueueError("Hints are turned off in Settings.")
            if cur.get("pending") or cur.get("closed"):
                raise QueueError("This problem is already answered.")
            hints = self._card(str(cur["card_id"])).hints
            shown = int(cur.get("hints", 0))
            if shown >= len(hints):
                raise QueueError("No more hints for this problem.")
            cur["hints"] = shown + 1
            last = shown + 1 == len(hints)
            cur["last_hint"] = last
            self._storage.users.save_session(replace(session, current=cur))
            return v.HintReveal(
                item_key=item.key,
                index=shown + 1,
                total=len(hints),
                text=hints[shown],
                rating_effect="again" if last else "hard",
            )

    def open_example(self) -> None:
        """The student opened the skill's worked example mid-problem (TIME-5 exclusion)."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, _ = self._current_item(session, plan)
            cur["example_opened"] = True
            self._storage.users.save_session(replace(session, current=cur))

    def diagnose(self, choice: str, step: int | None = None) -> v.Diagnosis:
        """The "What went wrong?" pick after a miss. The answer is graded with it, so the
        diagnosis flow's hooks see it (error_choice, error_step, didnt_know_start and the
        slip cap) and their PendingCheck rows land in the re-plan."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            pending = dict(cur.get("pending") or {})
            if not pending or pending.get("correct"):
                raise QueueError("There is no missed answer to diagnose.")
            error, error_step, start, slip = _choice(choice, step)
            pending.update(  # the diagnosis hook decides the slip cap (ADR-0008)
                error_choice=error,
                error_step=error_step,
                didnt_know_start=start,
            )
            cur["pending"] = pending
            session = replace(session, current=cur)
            before = {i.key for i in plan.items}
            session, plan, recorded = self._finalize(session, plan, engine)
            new_checks = [
                i for i in plan.items if i.key not in before and i.order == CHECK and i.pending
            ]
            diag = recorded.attempt.extra.get("diagnosis") if recorded is not None else None
            accepted = isinstance(diag, dict) and diag.get("slip") == "accepted"
            skills = engine.catalog().skills
            names = tuple(
                skills[i.skill_id].name
                for i in new_checks
                if i.skill_id is not None and i.skill_id in skills
            )
            if accepted:
                follow = "Counted as a slip: the miss is recorded, but it doesn't lower your Level."
            elif new_checks:
                follow = "A quick check on " + ", ".join(names) + " comes in a few problems."
            elif recorded is not None and recorded.attempt.rating is None:
                follow = "Its rating waits for a quick check, which comes next session."
            elif slip:
                follow = "The slip allowance is used up for this skill, so it counts as a miss."
            elif error == "setup":
                follow = "A worked example comes before this skill's next problem."
            else:
                follow = "A fresh problem on this skill comes later."
            if recorded is not None and recorded.result.effects.confident_error:
                follow += " You submitted it as sure, so it comes back tomorrow for a second look."
            return v.Diagnosis(
                item_key=item.key,
                choice=choice,
                follow_up=follow,
                rating=recorded.attempt.rating if recorded is not None else None,
                slip_accepted=accepted,
                checks=names,
            )

    def next(self) -> v.Turn:
        """Continue: grade the answer on screen if it isn't yet, then the next item."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur = session.current
            if cur is not None and plan.mode == "practice-test":
                return self._turn(session, engine)
            if cur is not None:
                item = plan.item(str(cur["key"]))
                if cur.get("pending"):
                    session, plan, _ = self._finalize(session, plan, engine)
                elif not cur.get("closed"):
                    if item is not None and item.kind == "example":
                        cur = {
                            **cur,
                            "pending": {
                                "at": self._now(),
                                "correct": False,
                                "verdict": "shown",
                                "timing": {},
                            },
                        }
                        session, plan, _ = self._finalize(
                            replace(session, current=cur), plan, engine
                        )
                    elif item is not None and item.kind == "flashcard":
                        raise QueueError("Rate the flashcard first.")
                    else:
                        raise QueueError("Submit an answer or give up first.")
            session = self._advance(session, plan, engine)
            return self._turn(session, engine)

    # ================================================================ grading

    def _outcome(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: Mapping[str, Any],
        *,
        facts: AnswerFacts,
        timing: TimingFacts,
        at: int,
        raw: str | None = None,
        parsed: str | None = None,
        verdict: str | None = None,
        error_choice: str | None = None,
        error_step: int | None = None,
        matched_wrong: int | None = None,
        flags: Sequence[str] = (),
        parts: Sequence[Mapping[str, Any]] = (),
        find_error: Mapping[str, Any] | None = None,
    ) -> ProblemOutcome:
        card = self._card(str(cur["card_id"]))
        ref = self._ref(card)
        extra: dict[str, Any] = {"queue_mode": plan.mode, "item": item.key}
        if find_error:
            extra["find_error"] = dict(find_error)
        if cur.get("highlighted"):
            extra["highlighted"] = True
        if item.check_id is not None:
            extra["check_id"] = item.check_id
            if item.check_kind == "cued-twin":
                extra["cued"] = True  # shown with its cued stem (the method named)
        if flags:
            extra["timing_flags"] = list(flags)
        if cur.get("undecided"):
            extra["grader_review"] = True
        return ProblemOutcome(
            card=ref,
            facts=facts,
            at=at,
            timing=timing,
            shown_at=cur.get("shown_at"),
            purpose=cast(Purpose, item.purpose),
            # Only a problem served as a stretch is one (unrated, ADR-0014); a review whose
            # pick had to widen its tiers is still the skill's review. Practice tests keep
            # the band rule (exam-tier problems above it stay unrated).
            stretch=True
            if cur.get("stretch")
            else (None if plan.mode == "practice-test" else False),
            untimed=session.untimed,
            lighter_set=plan.lighter,
            example_opened=bool(cur.get("example_opened")),
            verdict=cast(Any, verdict),
            pack_id=None if ref.source == "user" else ref.source,
            session=session,
            presentation_id=str(cur["presentation_id"]),
            reason_tag=item.tag,
            triage_policy=plan.policy,
            raw_input=raw,
            parsed=parsed,
            error_choice=cast(ErrorChoice | None, error_choice),
            error_step=error_step,
            matched_wrong=matched_wrong,
            app_version=self._app_version,
            check_of=item.check_id,
            extra=extra,
            parts=tuple(PartOutcome.from_json(dict(p)) for p in parts),
        )

    def _finalize(
        self, session: SessionState, plan: Plan, engine: Engine
    ) -> tuple[SessionState, Plan, Any]:
        """Grade the saved answer on screen (one transaction with the session row), then
        plan its follow-ups. Returns the session, the plan and the engine's Recorded."""
        cur = dict(session.current or {})
        pending = dict(cur.get("pending") or {})
        item = plan.item(str(cur["key"]))
        if item is None or not pending:
            raise QueueError("Nothing to grade.")
        facts = AnswerFacts(
            correct=bool(pending.get("correct")),
            attempt_number=int(pending.get("attempt_number", 1)),
            hints_used=int(pending.get("hints_used", 0)),
            last_hint_used=bool(pending.get("last_hint_used")),
            gave_up=bool(pending.get("gave_up")),
            unsure=bool(pending.get("unsure")),
            guessed=bool(pending.get("guessed")),
            too_easy=bool(pending.get("too_easy")),
            didnt_know_start=bool(pending.get("didnt_know_start")),
            slip_within_cap=bool(pending.get("slip_within_cap")),
            self_grade=pending.get("self_grade"),
            rubric_total=pending.get("rubric_total"),
            rubric_ticked=pending.get("rubric_ticked"),
        )
        undo = {
            "presentation_id": cur["presentation_id"],
            "key": item.key,
            "card_id": cur["card_id"],
            "plan": session.plan,
            "position": session.position,
        }
        marked = plan.updated(replace(item, status="done", result={"answered_at": pending["at"]}))
        closed = {**cur, "pending": None, "closed": True, "answer": pending}
        extra = {**session.extra, "undo": undo, "replan": item.key}
        graded = replace(session, plan=marked.to_json(), current=closed, extra=extra)
        outcome = self._outcome(
            graded,
            plan,
            item,
            closed,
            facts=facts,
            timing=TimingFacts(**pending.get("timing", {})),
            at=int(pending["at"]),
            raw=pending.get("raw_input"),
            parsed=pending.get("parsed"),
            verdict=pending.get("verdict"),
            error_choice=pending.get("error_choice"),
            error_step=pending.get("error_step"),
            matched_wrong=pending.get("matched_wrong"),
            flags=pending.get("flags", ()),
            parts=pending.get("parts", ()),
            find_error=pending.get("find_error"),
        )
        recorded = engine.grade(outcome)
        new_plan, new_extra = self._after_answer(
            graded, marked, item.key, recorded.attempt, recorded.result, engine
        )
        new_extra.pop("replan", None)
        closed["attempt_id"] = recorded.attempt.id
        # The engine's decision (ENG miss flow): only a miss submitted sure is a confident
        # error with a guaranteed next-day redo. The solution view reads it from here.
        closed["confident_error"] = bool(recorded.result.effects.confident_error)
        saved = self._storage.users.save_session(
            replace(graded, plan=new_plan.to_json(), current=closed, extra=new_extra)
        )
        return saved, new_plan, recorded

    def _after_answer(
        self,
        session: SessionState,
        plan: Plan,
        key: str,
        attempt: Attempt,
        result: GradeResult | None,
        engine: Engine,
    ) -> tuple[Plan, dict[str, Any]]:
        """The re-plan after an answer (also run on resume after a crash, with result None:
        the follow-ups are then read from the stored attempt and skill row)."""
        users = self._storage.users
        extra = dict(session.extra)
        item = plan.item(key)
        if item is None or key in plan.replanned:
            return plan, extra
        effects: Effects | None = result.effects if result is not None else None
        stage = attempt.extra.get("stage")
        success = (
            result.decision.success
            if result is not None
            else attempt.verdict == "correct" or (attempt.rating or 0) >= 2
        )
        skill_id = attempt.skill_id or item.skill_id
        state = users.skill_state(skill_id) if skill_id else None
        learned = (
            effects.learned
            if effects is not None
            else state is not None and state.learned_at == attempt.at
        )
        if learned and skill_id:
            extra["learned"] = [*extra.get("learned", []), skill_id]
        res = {
            "attempt_id": attempt.id,
            "verdict": attempt.verdict,
            "rating": attempt.rating,
            "correct": bool(success) if item.kind == "problem" else None,
            "stage": stage,
            "card_id": attempt.card_id,
            "skill_id": skill_id,
            "active_ms": attempt.active_ms,
            "learned": bool(learned),
        }
        snap = gather_light(self, engine, date.fromisoformat(session.study_day), plan)
        inserted: list[PlanItem] = []
        drop: set[str] = set()
        if item.kind == "problem" and plan.mode != "practice-test" and skill_id:
            reinforce = (
                effects.reinforcement_due
                if effects is not None
                else attempt.rating == 1 and stage == "review" and not (state and state.leech)
            )
            if reinforce and item.purpose != "reinforcement":
                plan, k = plan.next_key("rf")
                inserted.append(
                    snap.make(
                        k,
                        skill_id,
                        order=RELEARN,
                        tag="relearn",
                        variant="relearn.reinforcement",
                        purpose="reinforcement",
                        anchor=key,
                        gap=5,
                    )
                )
            # A stretch problem is unrated (ADR-0014): the skill's core-band review is owed
            # and comes the next study day, never a few items after the stretch's worked
            # solution (the engine keeps the skill due from tomorrow).
            if not success:
                # QUE-2: a flashcard on the missed skill right after the solution: one
                # already planned for later moves up; otherwise one more if the limit allows.
                planned = next(
                    (i for i in plan.pending if i.kind == "flashcard" and i.skill_id == skill_id),
                    None,
                )
                if planned is not None:
                    drop.add(planned.key)
                    inserted.append(
                        flashcard_item(
                            snap.snap,
                            planned.card_id or "",
                            planned.card_ord,
                            skill_id,
                            refresher=True,
                        )
                    )
                elif plan.flashcards > 0:
                    refresher = self._refresher(skill_id, plan)
                    if refresher is not None:
                        inserted.append(
                            flashcard_item(snap.snap, refresher, 0, skill_id, refresher=True)
                        )
                        plan = replace(plan, flashcards=plan.flashcards - 1)
        if item.block is not None and skill_id:
            step = learning_step(state, date.fromisoformat(session.study_day))
            block_left = [i for i in plan.pending if i.block == item.block]
            if memory_of(state) is not None or step in ("waiting", "none"):
                drop |= {i.key for i in block_left}
            elif step == "problem" and not any(i.kind == "problem" for i in block_left):
                plan, k = plan.next_key("lp")
                inserted.append(
                    snap.make(
                        k,
                        skill_id,
                        order=LEARNING,
                        tag="new-skill",
                        variant="new-skill.continue",
                        tier=1.5,
                        block=item.block,
                    )
                )
        # Checks and diagnostic sets the diagnosis flow made (or resolved) meanwhile.
        if plan.mode not in ("practice-test",):
            ins, gone = self._sync_checks(plan, snap, attempt, key)
            inserted += ins
            drop |= gone
        res["inserted"] = [i.key for i in inserted]
        plan = plan.updated(replace(item, result=res))
        plan = self._rebalance(plan, inserted, drop, item.course_id, engine)
        plan = replace(plan, replanned=(*plan.replanned, key))
        return plan, extra

    def _rebalance(
        self,
        plan: Plan,
        inserted: Sequence[PlanItem],
        drop: set[str],
        course: str | None,
        engine: Engine,
    ) -> Plan:
        """rebalance, then drop anchored items that can't reach their distance (a check
        stays pending in storage for the next session; a reinforcement is not needed then:
        the relearning review comes tomorrow)."""
        confusable = self._confusable(engine)
        out = rebalance(
            plan, inserted=inserted, drop=drop, prefer_course=course, confusable=confusable
        )
        short = _short_anchors(out)
        if short:
            out = rebalance(out, drop=short, prefer_course=course, confusable=confusable)
        return out

    def _refresher(self, skill_id: str, plan: Plan) -> str | None:
        """QUE-2: a flashcard linked to the missed skill, right after the solution."""
        marks = self._storage.users.card_marks()
        in_plan = {i.card_id for i in plan.items if i.kind == "flashcard"}
        for ref in self._storage.packs.card_refs(skill_id=skill_id):
            mark = marks.get(ref.id)
            if (
                ref.kind == "flashcard"
                and ref.status == "active"
                and ref.id not in in_plan
                and not (mark and (mark.hidden or mark.suspended))
            ):
                return ref.id
        return None

    def _sync_checks(
        self, plan: Plan, snap: _Light, attempt: Attempt, key: str
    ) -> tuple[list[PlanItem], set[str]]:
        """Checks the diagnosis flow made (or resolved, or cancelled) since the last answer.
        A check whose miss is in this session waits `after_items` items after it; one from an
        earlier session has no anchor."""
        users = self._storage.users
        now = self._now()
        pending = {c.id: c for c in users.pending_checks("pending") if c.id is not None}
        planned = {i.check_id for i in plan.items if i.check_id is not None}
        by_attempt = {
            (i.result or {}).get("attempt_id"): i.key for i in plan.items if not i.pending
        }
        by_attempt[attempt.id] = key
        fresh = [
            c
            for c in queue_order(pending.values())
            if c.id not in planned and (c.not_before_at is None or c.not_before_at <= now)
        ]
        reason_of = Diagnosis(self._storage).reason if fresh else None
        inserted = []
        for n, check in enumerate(fresh):
            anchor = by_attempt.get(check.attempt_id)
            missed = attempt.skill_id if anchor == key else check.skill_id
            name = snap.snap.skill_name(missed)
            diagnostic = check.kind == "diagnostic"
            inserted.append(
                snap.make(
                    f"chk:{check.id}",
                    check.skill_id,
                    order=CHECK,
                    rank=-1.0 + n / 1000,
                    tag="check",
                    variant="check.diagnostic" if diagnostic else "check",
                    why_text=reason_of(check) if reason_of is not None else None,
                    label="Check" if diagnostic else f"Check (after a miss on {name})",
                    tier=2.0,
                    course=snap.snap.course_of(attempt.skill_id) if anchor else None,
                    anchor=anchor,
                    gap=max(check.after_items, CHECK_GAP) if anchor else 0,
                    check_id=check.id,
                    check_kind=check.kind,
                    card_id=check.card_id,
                )
            )
        gone = {i.key for i in plan.pending if i.check_id is not None and i.check_id not in pending}
        return inserted, gone

    def _bookkeeping_hook(
        self, ctx: SkillContext, outcome: ProblemOutcome, result: GradeResult
    ) -> GradeResult:
        """Without the diagnosis flow (diagnosis=False): resolve the check this answer was
        served for, so it isn't served again."""
        check_id = outcome.check_of
        if check_id is None or any(
            isinstance(c, PendingCheck) and c.id == check_id for c in result.answer.changes
        ):
            return result
        check = next(
            (c for c in self._storage.users.pending_checks("pending") if c.id == check_id), None
        )
        if check is None:
            return result
        resolved = replace(
            check,
            status="passed" if result.decision.success else "failed",
            resolved_at=outcome.at,
            resolved_by=THIS_ATTEMPT,
        )
        answer = replace(result.answer, changes=(*result.answer.changes, resolved))
        return replace(result, answer=answer)

    # ================================================================ flashcards

    def rate_flashcard(
        self,
        rating: int | None = None,
        *,
        answer: str | None = None,
        source: v.Source = "text",
        timing: TimingReport | Mapping[str, Any] | None = None,
    ) -> v.AttemptResult:
        """Again/Hard/Good/Easy (keys 1-4), or a typed answer graded by the checker."""
        report = timing if isinstance(timing, TimingReport) else TimingReport.from_dict(timing)
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            if item.kind != "flashcard":
                raise QueueError("The item on screen is not a flashcard.")
            if cur.get("closed"):
                raise QueueError("This flashcard is already rated.")
            card = self._card(str(cur["card_id"]))
            verdict = "self"
            if rating is None:
                if answer is None:
                    raise QueueError("Rate the flashcard or type its answer.")
                checked = check_answers(card, [(None, answer)], source, self._checker)
                if checked.invalid or checked.undecided:
                    raise QueueError("Rate this one yourself.")
                rating = 3 if checked.correct else 1
                verdict = "correct" if checked.correct else "incorrect"
            if rating not in (1, 2, 3, 4):
                raise QueueError("A rating is 1 (Again) to 4 (Easy).")
            now = self._now()
            guarded = guard_timing(
                report, shown_at=cur.get("shown_at"), now_ms=now, saved_active_ms=session.active_ms
            )
            session, _ = self._note_active(session, guarded.timing.active_ms or 0)
            users = self._storage.users
            state = users.flashcard_state(card.id, item.card_ord)
            adapter = engine.adapter_for_card(card.id)
            new_state, event, recall = grade_flashcard(
                state,
                card_id=card.id,
                card_ord=item.card_ord,
                rating=rating,
                at_ms=now,
                adapter=adapter,
                days=engine.days(),
                leech_lapses=int(users.get_setting("leech.flashcard_lapses", 8)),
            )
            undo = {
                "presentation_id": cur["presentation_id"],
                "key": item.key,
                "card_id": card.id,
                "plan": session.plan,
                "position": session.position,
            }
            res = {"rating": rating, "verdict": verdict, "correct": rating >= 2}
            marked = plan.updated(replace(item, status="done", result=res))
            rewrite = new_state.leech and not (state is not None and state.leech)
            if rating == 1 and not new_state.leech:
                # I5: shown again at least 5 items later, with FSRS's same-day update.
                marked, key = marked.next_key("fr")
                reshow = replace(
                    item,
                    key=key,
                    status="pending",
                    result=None,
                    anchor=item.key,
                    gap=FLASHCARD_RESHOW_GAP,
                    inserted=True,
                    purpose="relearn",
                    why=why("flashcard.reshow"),
                )
                marked = rebalance(marked, inserted=[reshow], refill=False)
            closed = {**cur, "closed": True, "answer": {"at": now, "rating": rating}}
            graded = replace(
                session,
                plan=marked.to_json(),
                current=closed,
                extra={**session.extra, "undo": undo},
            )
            ref = self._ref(card)
            attempt = Attempt(
                at=now,
                shown_at=cur.get("shown_at"),
                session_id=session.id,
                presentation_id=str(cur["presentation_id"]),
                card_id=card.id,
                card_rev=card.rev,
                pack_id=None if ref.source == "user" else ref.source,
                card_kind=card.kind,
                skill_id=card.skill_id,
                part=None if item.card_ord == 0 else str(item.card_ord),
                reason_tag="flashcard",
                raw_input=answer,
                verdict=cast(Any, verdict),
                active_ms=guarded.timing.active_ms,
                raw_ms=guarded.timing.active_ms,
                untimed=session.untimed,
                rating=rating,
                explicit_rating=answer is None,
                predicted_recall=None if recall is None else min(1.0, max(0.0, recall)),
                params_id=adapter.params_id,
                rules_version=event.rules_version,
                triage_policy=plan.policy,
                app_version=self._app_version,
                extra={
                    "queue_mode": plan.mode,
                    "item": item.key,
                    "stage": "flashcard",
                    "strict_ok": rating >= 2,
                },
            )
            stored = users.record_answer(
                GradedAnswer(
                    attempt=attempt, changes=(new_state,), reviews=(event,), session=graded
                )
            )
            closed["attempt_id"] = stored.id
            marked = marked.updated(
                replace(item, status="done", result={**res, "attempt_id": stored.id})
            )
            users.save_session(replace(graded, plan=marked.to_json(), current=closed))
            return v.AttemptResult(
                item_key=item.key,
                outcome="recorded",
                rating=rating,
                attempts_allowed=1,
                tries_used=1,
                message=FLASHCARD_REWRITE if rewrite else "",
            )

    # ================================================================ undo, dispute, report

    def undo(self) -> v.Turn:
        """QUE-15: roll back the last answer (attempt, rating, FSRS state, Elo) in one
        transaction and show the problem again. Refused, with a message, once a later
        answer was submitted or the rows changed since (storage refuses inexact undos)."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            users = self._storage.users
            cur = dict(session.current or {})
            if cur.get("pending"):  # on the verdict screen, not graded yet
                pending = cur["pending"]
                fresh = {
                    **cur,
                    "pending": None,
                    "tries": 0,
                    "parts": None,
                    "solution_shown": False,
                    "hints": 0,
                    "last_hint": False,
                    "presentation_id": _uid(),
                    "shown_at": self._now(),
                    # ADR-0019 item 7: the solution was on screen, so a re-answer is never
                    # a clean Good.
                    UNDO_AFTER_SOLUTION: bool(
                        cur.get(UNDO_AFTER_SOLUTION)
                        or cur.get("solution_shown")
                        or not (isinstance(pending, dict) and pending.get("correct"))
                    ),
                }
                restored = replace(session, current=fresh, draft=None)
                last = users.last_attempt()
                if last is not None and last.presentation_id == cur.get("presentation_id"):
                    users.undo_last_answer(session=restored)  # voids its "Not quite" tries
                else:
                    users.save_session(restored)
                return self._turn(
                    users.session(_id(session)) or restored,
                    engine,
                    message="Undone. The problem is back.",
                )
            snap = session.extra.get("undo")
            if not snap:
                answered = any(i.status == "done" for i in plan.items)
                message = (
                    "Undo is only available until the next answer is submitted."
                    if answered
                    else "There is no answer to undo."
                )
                return self._turn(session, engine, message=message)
            last = users.last_attempt()
            if last is None or last.presentation_id != snap["presentation_id"]:
                return self._turn(
                    session,
                    engine,
                    message="Undo is only available until the next answer is submitted.",
                )
            old = Plan.from_json(snap["plan"])
            item = old.item(str(snap["key"]))
            if item is None:
                return self._turn(session, engine, message="There is no answer to undo.")
            extra = {k: val for k, val in session.extra.items() if k not in ("undo", "replan")}
            undone = plan.item(item.key)
            if undone is not None and (undone.result or {}).get("learned"):
                extra["learned"] = [k for k in extra.get("learned", []) if k != item.skill_id]
            undone_card = self._card(str(snap["card_id"]))
            # ADR-0019 item 7: a graded miss showed its solution; so did a self-graded one.
            solution_seen = bool(
                cur.get(UNDO_AFTER_SOLUTION)
                or cur.get("solution_shown")
                or last.verdict != "correct"
            )
            current = {
                "key": item.key,
                "card_id": snap["card_id"],
                "rev": undone_card.rev,
                "presentation_id": _uid(),
                "shown_at": self._now(),
                "tries": 0,
                "hints": 0,
                "last_hint": False,
                "example_opened": False,
                "stretch": item.stretch,
                "pending": None,
                "closed": False,
                UNDO_AFTER_SOLUTION: solution_seen,
            }
            if undone_card.kind == "find-error" and undone_card.skill_id:
                current["highlighted"] = find_error_highlighted(
                    [
                        a
                        for a in users.attempts(skill_id=undone_card.skill_id)
                        if a.presentation_id != snap["presentation_id"]
                    ]
                )
            restored = replace(
                session,
                plan=old.to_json(),
                position=old.index(item.key),
                current=current,
                active_ms=0,
                draft=None,
                extra=extra,
            )
            try:
                users.undo_last_answer(session=restored)
            except NothingToUndoError, UndoConflictError:
                return self._turn(
                    session,
                    engine,
                    message="That answer can't be undone exactly any more, so it stays.",
                )
            return self._turn(
                users.session(_id(session)) or restored,
                engine,
                message="Undone. The problem is back.",
            )

    def flag(self, kind: str, note: str | None = None) -> v.FlagResult:
        """too_easy (before continuing), dispute ("I was right": the attempt doesn't count,
        logged), report (hide the card at once, the attempt leaves scheduling), flag (a note
        for later), suspend (never serve the card)."""
        with self._locked():
            engine = self.engine()
            session, plan = self._require(engine)
            cur, item = self._current_item(session, plan)
            users = self._storage.users
            card = self._card(str(cur["card_id"]))
            if kind == "too_easy":
                pending = cur.get("pending")
                if not pending or not pending.get("correct"):
                    return v.FlagResult(
                        ok=False,
                        message="Too easy applies to a correct answer before you continue.",
                    )
                pending["too_easy"] = True
                users.save_session(replace(session, current=cur))
                return v.FlagResult(ok=True, message="Marked too easy.")
            if kind in ("dispute", "report"):
                reason: VoidReason = "dispute" if kind == "dispute" else "report"
                return self._void_answer(session, plan, item, cur, card, reason, note, engine)
            if kind in ("flag", "suspend"):
                mark = users.card_mark(card.id) or CardMark(card_id=card.id)
                if kind == "flag":
                    users.set_card_mark(replace(mark, flagged=True, flag_note=note))
                    return v.FlagResult(ok=True, message="Flagged for later.")
                users.set_card_mark(replace(mark, suspended=True))
                if not cur.get("pending") and not cur.get("closed") and not cur.get("tries"):
                    self._repick(session, plan, item, engine)
                return v.FlagResult(ok=True, message="Suspended: this problem won't come back.")
            raise QueueError(f"unknown flag {kind!r}")

    def _repick(self, session: SessionState, plan: Plan, item: PlanItem, engine: Engine) -> None:
        """A different problem for the item on screen (its card was reported or suspended
        before it was answered)."""
        fresh = replace(item, card_id=None) if item.check_id is None else item
        plan = plan.updated(fresh)
        self._advance(replace(session, current=None), plan, engine)

    def _void_answer(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        reason: VoidReason,
        note: str | None,
        engine: Engine,
    ) -> v.FlagResult:
        users = self._storage.users
        message = (
            "Logged. This attempt won't count."
            if reason == "dispute"
            else "Reported and hidden. This attempt won't count."
        )
        pending = cur.get("pending")
        if pending:  # never graded: log it as an unrated attempt, voided, with the record
            outcome = self._outcome(
                session,
                plan,
                item,
                cur,
                facts=AnswerFacts(
                    correct=bool(pending.get("correct")),
                    attempt_number=int(pending.get("attempt_number", 1)),
                ),
                timing=TimingFacts(**pending.get("timing", {})),
                at=int(pending["at"]),
                raw=pending.get("raw_input"),
                verdict=pending.get("verdict"),
            )
            ctx = engine.context(card.skill_id or "", card_id=card.id, at_ms=int(pending["at"]))
            answer = record_try(ctx, outcome)
            res = {"correct": None, "voided": reason, "verdict": pending.get("verdict")}
            marked = plan.updated(replace(item, status="done", result=res))
            closed = {**cur, "pending": None, "closed": True, "answer": pending}
            after = replace(
                session,
                plan=marked.to_json(),
                current=closed,
                extra={k: x for k, x in session.extra.items() if k != "undo"},
            )
            tries = [
                a.id
                for a in users.attempts(session_id=session.id)
                if a.presentation_id == cur["presentation_id"] and a.id is not None
            ]

            def write(u: Any) -> int:
                stored = u.record_answer(replace(answer, session=None))
                u.void_attempts([*tries, stored.id], reason=reason, note=note, session=after)
                if reason == "dispute":
                    u.add_dispute(
                        Dispute(attempt_id=stored.id, raw_input=pending.get("raw_input"), note=note)
                    )
                else:
                    u.add_report(
                        Report(
                            card_id=card.id,
                            card_rev=card.rev,
                            attempt_id=stored.id,
                            reason=note or "",
                        )
                    )
                return int(stored.id)

            users.atomic(write)
            return v.FlagResult(ok=True, message=message, attempt_counts=False)
        snap = session.extra.get("undo")
        last = users.last_attempt()
        graded_here = (
            snap is not None
            and last is not None
            and last.presentation_id == snap["presentation_id"]
            and snap["key"] == item.key
        )
        if cur.get("closed") and graded_here and last is not None:
            res = dict(item.result or {})
            res.update(correct=None, voided=reason)
            drop = [i for i in res.get("inserted", ()) if (plan.item(i) or item).pending]
            marked = rebalance(
                plan.updated(replace(item, result=res)),
                drop=drop,
                confusable=self._confusable(engine),
            )
            extra = {k: x for k, x in session.extra.items() if k != "undo"}
            if item.skill_id in extra.get("learned", []):
                extra["learned"] = [k for k in extra["learned"] if k != item.skill_id]
            after = replace(session, plan=marked.to_json(), extra=extra)

            def void_and_log(u: Any) -> None:
                # One transaction: the void and the dispute (or report) record, both or
                # neither (spec, Buttons after grading).
                try:
                    u.undo_last_answer(reason=reason, note=note, session=after)
                except NothingToUndoError, UndoConflictError:
                    # Rows changed since, so no exact undo: void the answer and rebuild the
                    # memory of the cards it touched from the log (C3); Elo, tiers and Level
                    # keep their later values.
                    group = [
                        a.id
                        for a in u.attempts(session_id=session.id)
                        if a.presentation_id == last.presentation_id and a.id is not None
                    ]
                    engine.void_attempts(group, reason=reason, note=note, session=after)
                if reason == "dispute":
                    u.add_dispute(
                        Dispute(attempt_id=_int(last.id), raw_input=last.raw_input, note=note)
                    )
                else:
                    u.add_report(
                        Report(
                            card_id=card.id,
                            card_rev=card.rev,
                            attempt_id=last.id,
                            reason=note or "",
                        )
                    )

            users.atomic(void_and_log)
            return v.FlagResult(ok=True, message=message, attempt_counts=False)
        if reason == "report":  # before answering: hide it and serve another problem
            users.add_report(Report(card_id=card.id, card_rev=card.rev, reason=note or ""))
            if not cur.get("closed"):
                tries = [
                    a.id
                    for a in users.attempts(session_id=session.id)
                    if a.presentation_id == cur["presentation_id"] and a.id is not None
                ]
                if tries:
                    users.void_attempts(tries, reason="report", note=note)
                self._repick(session, plan, item, engine)
            return v.FlagResult(ok=True, message="Reported and hidden.", attempt_counts=False)
        return v.FlagResult(ok=False, message="There is no answer to dispute.")

    # ================================================================ other ways to study

    def _focused_plan(self, req: v.StartRequest, engine: Engine) -> Plan:
        """QUE-14: a section, a skill or the current weak spots, outside the plan. Results
        count as ordinary reviews; a new skill still goes through its learning phase."""
        snap = gather(self._storage, engine)
        catalog = snap.catalog
        if req.skill_id is not None:
            skills = [req.skill_id] if req.skill_id in catalog.skills else []
        elif req.section_id is not None:
            skills = [
                k for k, s in sorted(catalog.skills.items()) if s.section_id == req.section_id
            ]
        elif req.weak_spots:
            skills = sorted({w.skill_id for w in self._storage.users.weak_spots("open")})
            skills = skills or sorted(snap.recent_fails)
        else:
            raise QueueError("Pick a section, a skill or your weak spots.")
        if not skills:
            return Plan(day=snap.day.isoformat(), mode="focused")
        count = req.count or FOCUSED_DEFAULT
        builder = TriageBuilder(snap, lighter=False)
        units: list[Unit] = []
        slots = 0
        round_ = 0
        while slots < count and round_ < count:
            added = False
            for skill_id in skills:
                if slots >= count:
                    break
                state = snap.states.get(skill_id)
                if memory_of(state) is None:
                    if any(u[0].block == f"blk:{skill_id}" for u in units):
                        continue
                    block = learning_block(builder, skill_id, state, order=LEARNING, rank=slots)
                    unit = tuple(replace(i, purpose="focused") for i in block)
                else:
                    unit = (
                        builder.item(
                            f"foc:{skill_id}:{round_}",
                            skill_id,
                            order=REVIEW,
                            rank=slots,
                            tag="review",
                            variant="review.focused",
                            purpose="focused",
                        ),
                    )
                units.append(unit)
                slots += sum(i.slots for i in unit)
                added = True
            round_ += 1
            if not added:
                break
        items = order_items(
            [],
            [i for u in units for i in u],
            shares={"": 1.0},
            confusable=confusable_map(catalog),
            warmup=False,
        )
        items = [replace(i, course_id="") for i in items]
        return Plan(
            day=snap.day.isoformat(),
            mode="focused",
            policy=policy_for(None).name,
            n=slots,
            items=tuple(items),
            shares={"": 1.0},
            info={
                "target": {
                    "skill": req.skill_id,
                    "section": req.section_id,
                    "weak_spots": req.weak_spots,
                }
            },
        )

    def _test_plan(self, req: v.StartRequest, engine: Engine, day: date) -> Plan:
        """ENG-8: a set number (the request's, else the exam's problem count, else 10) of
        exam-tier problems across the exam's scope: every skill once before any twice, the
        rest weighted toward weaker recall (weight 1 - recall + TEST_RECALL_FLOOR; with fewer
        problems than skills, a weighted draw seeded by exam and day picks the skills).
        Optionally timed at exam pace; graded only at the end (_grade_test). Self-graded
        problems are left out: nothing is graded until the test ends."""
        users, packs = self._storage.users, self._storage.packs
        exam = next((e for e in users.exams() if e.id == req.exam_id), None)
        if exam is None:
            raise QueueError("Pick an exam for the practice test.")
        days = engine.days()
        if not practice_tests_open(days.day_of(exam.at), day):
            raise QueueError("Practice tests open in the final 21 days before an exam.")
        catalog = engine.catalog()
        scope = [
            k
            for k in (
                catalog.skills_in_sections(exam.sections)
                if exam.sections
                else catalog.skills_of_course(exam.course_id or "")
            )
            if k in catalog.skills and not catalog.skills[k].method_choice
        ]
        states = users.skill_states(scope)
        skills = [k for k in scope if memory_of(states.get(k)) is not None] or list(scope)
        count = max(1, req.count or exam.problems or PRACTICE_TEST_DEFAULT)
        hidden = {k for k, m in users.card_marks().items() if m.hidden or m.suspended}
        seen = users.card_users()
        now = self._now()
        adapter_of = engine.skill_adapters()
        pools: dict[str, list[str]] = {}
        for skill_id in skills:
            tier = catalog.exam_tier(skill_id)
            refs = [
                r
                for r in packs.card_refs(skill_id=skill_id)
                if r.kind == "problem"
                and r.status == "active"
                and r.id not in hidden
                and all(p.spec.answer_type != "self" for p in specs_for(self._card(r.id)))
            ]
            refs.sort(
                key=lambda r: (
                    abs(r.tier - tier),
                    (seen[r.id].last_seen_at or 0) if r.id in seen else -1,
                    r.id,
                )
            )
            if refs:
                pools[skill_id] = [r.id for r in refs]
        weights: dict[str, float] = {}
        for skill_id in pools:
            memory = memory_of(states.get(skill_id))
            recall = adapter_of(skill_id).retrievability(memory, now) if memory is not None else 0.0
            weights[skill_id] = max(0.0, 1.0 - recall) + TEST_RECALL_FLOOR
        allocation = practice_test_allocation(
            weights,
            {k: len(v) for k, v in pools.items()},
            count,
            seed=f"{exam.id}|{day.isoformat()}",
        )
        snap = gather(self._storage, engine)
        builder = TriageBuilder(snap, lighter=False)
        items: list[PlanItem] = []
        for skill_id in sorted(allocation, key=lambda k: (-weights[k], k)):
            for card_id in pools[skill_id][: allocation[skill_id]]:
                ref_tier = self._card(card_id).tier
                items.append(
                    builder.item(
                        f"pt:{len(items)}",
                        skill_id,
                        order=REVIEW,
                        rank=len(items),
                        tag="exam-prep",
                        variant="exam-prep.test",
                        purpose="practice-test",
                        tier=float(ref_tier),
                        card_id=card_id,
                    )
                )
        items = order_items([], items, shares={"": 1.0}, warmup=False)
        items = [replace(i, course_id="") for i in items]
        limit = None
        if req.timed:
            per = (
                exam.minutes / exam.problems
                if exam.minutes and exam.problems
                else DEFAULT_TEST_MINUTES_PER_PROBLEM
            )
            limit = math.ceil(per * len(items) * MINUTE_MS)
        unanswered = users.get_setting(TEST_UNANSWERED_KEY, TEST_UNANSWERED_DEFAULT)
        return Plan(
            day=day.isoformat(),
            mode="practice-test",
            n=len(items),
            items=tuple(items),
            shares={"": 1.0},
            info={
                "exam_id": exam.id,
                "timed": req.timed,
                "limit_ms": limit,
                "unanswered": "skip" if unanswered == "skip" else "again",
                "weights": {k: round(w, 4) for k, w in weights.items()},
            },
        )

    def _submit_test(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        req: v.SubmitRequest,
        base: dict[str, Any],
        engine: Engine,
    ) -> v.AttemptResult:
        """A practice-test answer is checked and saved, with no feedback until the end. One
        try per problem; a multi-part problem keeps each part's verdict."""
        if base.get("gave_up"):
            answer = {**base}
            if card.parts:
                answer["parts"] = [
                    PartOutcome(
                        label=p.label, skill_id=p.skill_id, correct=False, gave_up=True
                    ).as_json()
                    for p in card.parts
                ]
        else:
            checked = check_answers(
                card,
                [(a.part, a.value) for a in req.answers],
                req.answers[0].source if req.answers else "text",
                self._checker,
            )
            if checked.invalid:
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="invalid",
                    message="Not counted: fix the answer's form.",
                )
            answer = {
                **base,
                "correct": checked.correct,
                "verdict": "correct"
                if checked.correct
                else ("undecided" if checked.undecided else "incorrect"),
            }
            if card.parts and not checked.undecided:
                answer["parts"] = [
                    PartOutcome(
                        label=str(p.part),
                        skill_id=next((c.skill_id for c in card.parts if c.label == p.part), None),
                        correct=p.status == Status.CORRECT,
                    ).as_json()
                    for p in checked.verdicts
                ]
        res = {"answer": answer, "graded": False}
        plan = plan.updated(replace(item, status="done", result=res))
        session = replace(session, plan=plan.to_json(), current=None)
        limit = plan.info.get("limit_ms")
        used = int(session.extra.get("active_total_ms", 0))
        if limit and used >= int(limit):
            plan = replace(plan, info={**plan.info, "time_up": True})
            plan = plan.with_items(
                replace(i, status="skipped", result={"unanswered": True}) if i.pending else i
                for i in plan.items
            )
        session = self._advance(session, plan, engine)
        return v.AttemptResult(
            item_key=item.key, outcome="recorded", message="Saved. Results come at the end."
        )

    def _grade_test(
        self, session: SessionState, plan: Plan, engine: Engine
    ) -> tuple[SessionState, Plan, v.TestResult]:
        """Grade a practice test when it ends (each problem its own transaction, with the
        session row marking it graded); results count as reviews. A problem never answered
        when the test ends (stopped early or time up) scores zero in the test, but memory
        can't fail a question the student never saw (C5, ADR-0014): it is logged as an
        unrated attempt (no FSRS event, no lapse, no leech count). The setting
        `queue.test_unanswered` = "again" still counts it as Again."""
        catalog = engine.catalog()
        policy = str(plan.info.get("unanswered", "skip"))  # plans from before: not graded
        now = self._now()
        for item in list(plan.items):
            res = dict(item.result or {})
            if res.get("graded") or item.card_id is None:
                continue
            answer = res.get("answer")
            if answer is None and item.kind == "problem" and policy != "again":
                session = self._log_unanswered(session, plan, item, res, engine, now)
                plan = Plan.from_json(session.plan)
                continue
            if answer is None:
                if policy != "again" or item.kind != "problem":
                    continue
                answer = {
                    "at": now,
                    "correct": False,
                    "gave_up": True,
                    "unanswered": True,
                    "verdict": "gave-up",
                    "timing": {},
                }
                card = self._card(item.card_id)
                if card.parts:
                    answer["parts"] = [
                        PartOutcome(
                            label=p.label, skill_id=p.skill_id, correct=False, gave_up=True
                        ).as_json()
                        for p in card.parts
                    ]
                res["answer"] = answer
            facts = AnswerFacts(
                correct=bool(answer.get("correct")),
                gave_up=bool(answer.get("gave_up")),
                unsure=bool(answer.get("unsure")),
                guessed=bool(answer.get("guessed")),
            )
            res["graded"] = True
            marked = plan.updated(replace(item, status="done", result=res))
            cur = {
                "card_id": item.card_id,
                "presentation_id": _uid(),
                "shown_at": None,
                "key": item.key,
            }
            graded = replace(session, plan=marked.to_json(), current=None)
            outcome = self._outcome(
                graded,
                plan,
                item,
                cur,
                facts=facts,
                timing=TimingFacts(**answer.get("timing", {})),
                at=int(answer["at"]),
                raw=answer.get("raw_input"),
                verdict=answer.get("verdict"),
                parts=answer.get("parts", ()),
            )
            if answer.get("unanswered"):
                outcome = replace(outcome, extra={**outcome.extra, "unanswered": True})
            recorded = engine.grade(outcome)
            res.update(
                attempt_id=recorded.attempt.id,
                rating=recorded.attempt.rating,
                correct=bool(answer.get("correct")),
            )
            plan = marked.updated(replace(item, status="done", result=res))
            session = self._storage.users.save_session(replace(graded, plan=plan.to_json()))
        lines = []
        for item in plan.items:
            res = item.result or {}
            answer = res.get("answer")
            answered = answer is not None and not answer.get("unanswered")
            skill = catalog.skills.get(item.skill_id or "")
            lines.append(
                v.TestLine(
                    item_key=item.key,
                    card_id=item.card_id,
                    skill_name=skill.name if skill is not None else "",
                    answered=answered,
                    correct=bool(answered and answer and answer.get("correct")),
                    your_answer=answer.get("raw_input") if answered and answer else None,
                    rating=res.get("rating"),
                )
            )
        result = v.TestResult(
            exam_id=plan.info.get("exam_id"),
            answered=sum(1 for x in lines if x.answered),
            correct=sum(1 for x in lines if x.correct),
            total=len(lines),
            timed=bool(plan.info.get("timed")),
            time_up=bool(plan.info.get("time_up")),
            lines=tuple(lines),
            unanswered="again" if policy == "again" else "skip",
            limit_ms=plan.info.get("limit_ms"),
        )
        return session, plan, result

    def _log_unanswered(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        res: dict[str, Any],
        engine: Engine,
        now: int,
    ) -> SessionState:
        """C5: an unanswered practice-test problem as an unrated attempt (the test's zero),
        committed with the session row that marks it graded."""
        answer = {"at": now, "correct": False, "unanswered": True, "verdict": "gave-up"}
        res = {**res, "answer": answer, "graded": True}
        marked = plan.updated(replace(item, status="done", result=res))
        cur = {"card_id": item.card_id, "presentation_id": _uid(), "shown_at": None}
        graded = replace(session, plan=marked.to_json(), current=None)
        facts = AnswerFacts(correct=False, gave_up=True)
        outcome = self._outcome(
            graded, plan, item, cur, facts=facts, timing=TimingFacts(), at=now, verdict="gave-up"
        )
        outcome = replace(outcome, extra={**outcome.extra, "unanswered": True})
        skill_id = outcome.card.skill_id or item.skill_id or ""
        ctx = engine.context(skill_id, card_id=outcome.card.id, at_ms=now)
        stored = self._storage.users.record_answer(record_unrated(ctx, outcome))
        res.update(attempt_id=stored.id, rating=None, correct=False)
        done = marked.updated(replace(item, status="done", result=res))
        return self._storage.users.save_session(replace(graded, plan=done.to_json()))

    # ================================================================ summary

    def _summary(
        self, session: SessionState, plan: Plan, engine: Engine, test: v.TestResult | None
    ) -> v.Summary:
        catalog = engine.catalog()
        done = [i for i in plan.items if i.status == "done" and i.kind == "problem"]
        counted = [i for i in done if (i.result or {}).get("correct") is not None]
        misses = [i for i in counted if not (i.result or {}).get("correct")]

        def name(k: str | None) -> str:
            s = catalog.skills.get(k or "")
            return s.name if s is not None else (k or "")

        learned = tuple(dict.fromkeys(name(k) for k in session.extra.get("learned", [])))
        ready_today = self._learning_ready_today(engine) if plan.mode in DAILY_MODES else 0
        tomorrow = self._today(engine) + timedelta(days=1)
        snap = gather(self._storage, engine, day=tomorrow)
        forecast_plan = build_plan(snap)
        forecast = v.Forecast(
            day=tomorrow.isoformat(),
            problems=sum(i.slots for i in forecast_plan.pending),
            minutes=projected_minutes(forecast_plan.pending),
            courses=self._course_lines(snap, forecast_plan.pending),
        )
        return v.Summary(
            mode=plan.mode,
            problems=len(counted),
            correct=len(counted) - len(misses),
            missed=len(misses),
            active_ms=int(session.extra.get("active_total_ms", 0)),
            misses=tuple(
                v.MissLine(
                    item_key=i.key,
                    card_id=(i.result or {}).get("card_id"),
                    skill_id=i.skill_id,
                    skill_name=name(i.skill_id),
                    tag=i.tag,
                    label=i.label,
                )
                for i in misses
            ),
            learned=learned,
            flashcards=sum(1 for i in plan.items if i.kind == "flashcard" and i.status == "done"),
            forecast=forecast,
            extra_practice_available=bool(forecast_plan.pending),
            practice_tests=tuple(e for e in self._exam_lines(snap) if e.practice_test),
            test=test,
            ready_today=ready_today,
        )

    def _learning_ready_today(self, engine: Engine) -> int:
        """Learning-phase problems Home would offer now that can still be served today: each
        learning block's slots, capped by its skill's problems not yet seen today."""
        today_plan = build_plan(gather(self._storage, engine))
        blocks: dict[str, int] = {}
        for item in today_plan.pending:
            if item.block is not None and item.skill_id is not None and item.slots:
                blocks[item.skill_id] = blocks.get(item.skill_id, 0) + item.slots
        return sum(min(n, engine.unseen_today(k)) for k, n in blocks.items())


# ---------------------------------------------------------------- helpers


class _CallEngine(Engine):
    """The engine for one service call: the skill catalog is read once per call instead of
    on every engine method (packs and user content don't change inside a call)."""

    def __init__(
        self,
        storage: Storage,
        *,
        hooks: Sequence[GradeHook],
        adapter: FsrsAdapter | None = None,
    ) -> None:
        super().__init__(storage, hooks=hooks, adapter=adapter)
        self._catalog: Catalog | None = None
        self._confusable: dict[str, frozenset[str]] | None = None

    def catalog(self) -> Catalog:
        if self._catalog is None:
            self._catalog = super().catalog()
        return self._catalog

    def confusable(self) -> dict[str, frozenset[str]]:
        if self._confusable is None:
            self._confusable = confusable_map(self.catalog())
        return self._confusable


class _Light:
    """Builds inserted items with the same fields triage gives (course, section, minutes)."""

    def __init__(self, snap: Snapshot, lighter: bool) -> None:
        self.snap = snap
        self._builder = TriageBuilder(snap, lighter=lighter)

    def make(self, key: str, skill_id: str | None, **kw: Any) -> PlanItem:
        kw.setdefault("rank", -1.0)
        return replace(self._builder.item(key, skill_id, **kw), inserted=True)


def gather_light(service: StudyService, engine: Engine, day: date, plan: Plan) -> _Light:
    """A small snapshot for building re-plan items: no due lists, no boosters; minutes
    from the plan's own estimates per skill."""
    storage = service.storage
    users = storage.users
    catalog = engine.catalog()
    times = TimeTable(
        by_skill={i.skill_id: i.est_ms for i in plan.items if i.kind == "problem" and i.skill_id}
    )
    snap = Snapshot(
        day=day,
        now_ms=storage.db.clock.now_ms(),
        days=engine.days(),
        settings=QueueSettings.from_values(users.settings(), day),
        catalog=catalog,
        adapter=engine.adapter(),
        courses={},
        section_states={k: s.state for k, s in users.section_states().items()},
        goals=engine.goals(),
        states=users.skill_states(),
        times=times,
    )
    return _Light(snap, lighter=plan.lighter)


def _short_anchors(plan: Plan) -> list[str]:
    """Pending anchored items placed closer to their miss than their gap allows."""
    seq = [i for i in plan.items if i.kind != "flashcard" and i.status != "skipped"]
    pos = {i.key: n for n, i in enumerate(seq)}
    return [
        i.key
        for i in seq
        if i.pending
        and i.anchor is not None
        and i.anchor in pos
        and pos[i.key] - pos[i.anchor] < i.gap
    ]


def _choice(choice: str, step: int | None) -> tuple[str | None, int | None, bool, bool]:
    """(error_choice, error_step, didnt_know_start, slip) for a picker choice. Accepts the
    spec's names and the page prototype's (different_method, cant_tell, step 0)."""
    c = choice.replace("_", "-")
    if c == "step":
        if step is None:
            raise QueueError("Pick the step where your work went differently.")
        if step == 0:
            return "setup", 0, True, False
        return "step", step, False, False
    if c in ("setup", "start", "didnt-know-start"):
        return "setup", 0, True, False
    if c in ("slip", "misread"):
        return c, None, False, True
    if c in ("other-method", "different-method"):
        return "other-method", None, False, False
    if c in ("cant-tell", "skip"):
        return "cant-tell", None, False, False
    raise QueueError(f"unknown choice {choice!r}")


def practice_test_allocation(
    weights: Mapping[str, float], capacity: Mapping[str, int], count: int, *, seed: str
) -> dict[str, int]:
    """Problems per skill for a practice test (ENG-8): spread over the scope, weighted
    toward weaker recall. With at least as many problems as skills, every skill gets one and
    each further problem goes to the skill with the largest weight / (problems + 1) (a
    D'Hondt split); with fewer, a weighted draw without replacement (keys u^(1/w), u from a
    hash of seed and skill, so a test is stable) picks which skills appear. `capacity`:
    problems available per skill."""
    skills = sorted(k for k in weights if capacity.get(k, 0) > 0)
    if not skills or count <= 0:
        return {}
    if count < len(skills):

        def key(k: str) -> float:
            digest = hashlib.sha256(f"{seed}|{k}".encode()).digest()
            u = (int.from_bytes(digest[:8], "big") + 1) / (2**64 + 1)
            return float(u ** (1.0 / max(weights[k], 1e-9)))

        keyed = sorted(skills, key=lambda k: (-key(k), k))
        return {k: 1 for k in keyed[:count]}
    out = {k: 1 for k in skills}
    left = count - len(skills)
    while left > 0:
        open_ = [k for k in skills if out[k] < capacity[k]]
        if not open_:
            break
        best = max(open_, key=lambda k: (weights[k] / (out[k] + 1), -skills.index(k)))
        out[best] += 1
        left -= 1
    return out


def _self_graded(card: Card, req: v.SubmitRequest) -> dict[str, Any]:
    """A self-grade: rubric ticks when given (clamped to the rubric), else the three
    buttons; `correct` follows the rating map (Hard or better is a success)."""
    if req.rubric_ticked is not None:
        if not card.rubric:
            raise QueueError("This problem has no rubric: Matched, Minor slip or Didn't get it.")
        total = len(card.rubric)
        ticked = max(0, min(total, int(req.rubric_ticked)))
        return {
            "correct": ticked >= total - 1,
            "self_grade": None,
            "rubric_total": total,
            "rubric_ticked": ticked,
        }
    if req.self_grade not in ("matched", "minor-slip", "missed"):
        raise QueueError("A self-grade is matched, minor-slip or missed.")
    return {
        "correct": req.self_grade == "matched",  # a minor slip is a wrong final answer
        "self_grade": req.self_grade,
        "rubric_total": None,
        "rubric_ticked": None,
    }


def _outcome_of(pending: Mapping[str, Any]) -> Literal["correct", "incorrect"]:
    """A multi-part problem is "correct" only when every part is (its own skill may still
    count as a success when only parts with skills of their own were missed)."""
    parts = pending.get("parts")
    if parts:
        return "correct" if all(p.get("correct") for p in parts) else "incorrect"
    return "correct" if pending.get("correct") else "incorrect"


def _find_error_view(pending: Mapping[str, Any]) -> v.FindErrorView | None:
    data = pending.get("find_error")
    return None if not data else v.FindErrorView(**data)


def _work(card: Card) -> tuple[v.StepView, ...]:
    """A find-the-error card's shown work, without skill names (Study screen rule 7)."""
    return tuple(
        v.StepView(
            number=s.number, skill_id=None, skill_name=None, label=s.label, body_md=s.body_md
        )
        for s in card.shown_work
    )


def _worked_md(card: Card) -> str:
    """A problem's worked solution as one Markdown text: its steps (or its untagged
    solution), then the answer. Used when a problem is shown solved as a worked example."""
    blocks: list[str] = []
    for step in card.solution:
        blocks.append(f"**Step {step.number}.** {step.label}")
        if step.body_md:
            blocks.append(step.body_md)
    if not card.solution and card.solution_md:
        blocks.append(card.solution_md)
    if card.parts:
        answers = [f"({p.label}) {p.answer}" for p in card.parts if p.answer]
        if answers:
            blocks.append("**Answer:** " + "; ".join(answers))
    elif card.answer_md or card.answer:
        blocks.append(f"**Answer:** {card.answer_md or card.answer}")
    return "\n\n".join(blocks)


def _clock(ms: int | None) -> str:
    seconds = round((ms or 0) / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _timing_json(t: TimingFacts) -> dict[str, Any]:
    return {
        "solve_ms": t.solve_ms,
        "entry_ms": t.entry_ms,
        "active_ms": t.active_ms,
        "raw_ms": t.raw_ms,
        "pause_count": t.pause_count,
        "longest_pause_ms": t.longest_pause_ms,
        "after_wake": t.after_wake,
        "expected_chars": t.expected_chars,
    }


def _parsed(verdicts: Sequence[Mapping[str, Any]]) -> str | None:
    reads = [str(p["read_as"]) for p in verdicts if p.get("read_as")]
    return " | ".join(reads) if reads else None


def _id(session: SessionState) -> int:
    if session.id is None:
        raise StorageError("session without an id")
    return session.id


def _int(value: int | None) -> int:
    if value is None:
        raise StorageError("attempt without an id")
    return value


__all__ = ["QueueError", "StudyService"]


# A problem brought back by undo after its solution was on screen (ADR-0019 item 7).
UNDO_AFTER_SOLUTION = "undo_after_solution"


def _hints_used(cur: Mapping[str, Any]) -> int:
    """Hints used on the problem on screen. Undone after its solution was shown, it counts
    at least one, so a re-answer is at most Hard and never strict (ADR-0019 item 7)."""
    hints = int(cur.get("hints", 0))
    return max(hints, 1) if cur.get(UNDO_AFTER_SOLUTION) else hints
