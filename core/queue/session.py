"""The study session service (wave 2): start or resume, serve, grade, re-plan, undo, summarize.

`StudyService(storage)` is what the bridge calls. It keeps no state of its own: every call
reads the open session row (QUE-16), acts, and saves the row again, so a quit, crash or
restart resumes at the same problem with its active time, typed draft, tries and any answer
not yet continued from. A lock serializes calls (bridge methods run on worker threads,
AGENTS rule 6).

Problems are planned by core.practice: the student model and the planner (design v1.2,
docs/design/wave2-integration.md section 4).

1. **Planning.** A daily session takes its problems from `PracticeEngine.plan_day` over the
   set-up courses; flashcards and cloze blanks go between them in groups of up to five (FSRS
   per card, unchanged). After every answer the rest of the day is planned again from the
   items served today, which the engine reads back from the log, so a second session of the
   day goes on where the first stopped.
2. **Answering.** A problem can be retried any number of times; only its first try counts.
   A wrong try is logged at once (a non-final attempt) and answered with "Not quite" alone:
   no checker message, no known-wrong-answer feedback, no step. The problem ends when the
   answer is right or the student gives up (or, after a wrong first try, asks for the
   solution); the full solution then shows, with the matched feedback. There are no hints and
   no "What went wrong?".
3. **Committing.** A final answer is held in the session row and committed on continue (or
   at the end, or, at its own time, when the study day rolls over) in one transaction with the
   session row (rule 5): the attempt row with what the planner chose (role, milestone,
   prediction, ladder rung, sitting, parameter version) and its valid solving minutes.
   Problems write no state rows; the learner state is a function of the log, and the engine
   picks up each committed row (`PracticeEngine.record`).
4. **Undo** voids the last answer's attempt rows and restores the plan as it was before it;
   the learner replays the shorter log.

Other modes: a practice test (exam-tier problems over an exam's scope, graded at the end)
and extra practice (tomorrow's planned problems, done now). Card kinds (ADR-0010): multi-part
problems keep a verdict and tries per part and are final when every part is; self-graded
problems show their solution (and rubric) before the student grades them; cloze cards come
one blank number at a time.
"""

import math
import threading
import uuid
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, timedelta
from typing import Any, Literal, cast

from core.engine import Engine, PartOutcome, TimingFacts, speed_time_ms
from core.engine.config import BASELINE_LONG_PAUSE_MS
from core.engine.service import FitReport
from core.engine.timing import cap_ms, excluded_from_baseline
from core.grader import Status
from core.learner.types import ProblemSpec
from core.model import (
    Attempt,
    Card,
    CardMark,
    Dispute,
    Exam,
    GradedAnswer,
    Report,
    SessionState,
    VoidReason,
)
from core.practice import Catalog, PlannedItem, PracticeEngine, PracticePlan
from core.practice.words import plain_note, set_aside_line
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
    DAY_MS,
    EXTRA_DEFAULT,
    FLASHCARD,
    FLASHCARD_MS,
    FLASHCARD_RESHOW_GAP,
    LEARNING,
    MINUTE_MS,
    PRACTICE_TEST_DEFAULT,
    REVIEW,
)
from core.queue.deck import flashcards as day_flashcards
from core.queue.flashcards import FLASHCARD_REWRITE, grade_flashcard
from core.queue.guards import TimingReport, guard_timing
from core.queue.items import LADDER_REASONS, ROLE_REASONS, TAG_LABELS, Mode, Plan, PlanItem, why
from core.queue.planner import place_flashcards
from core.storage import NothingToUndoError, Storage, StorageError, UndoConflictError

ENGINE = 2  # plan.info["engine"]: planned by core.practice (wave 2)
DAILY: Mode = "daily"
MODES: tuple[Mode, ...] = ("daily", "extra", "practice-test")
PRACTICE_TEST_WINDOW_DAYS = 21  # practice tests open 21 days before an exam (ENG-8)
PRACTICE_TEST_TIER = 3  # a standard exam problem (design 2.2)
PRACTICE_TEST_FRESH_DAYS = 7  # problems not served in the last 7 days
NO_LIMIT = 0  # attempts_allowed: problems are retried freely
UNDO_AFTER_SOLUTION = "undo_after_solution"  # ADR-0019 item 7: brought back after its solution


class QueueError(Exception):
    """A request the session can't act on now (shown to the student as a message)."""


def _uid() -> str:
    return uuid.uuid4().hex


class StudyService:
    def __init__(
        self,
        storage: Storage,
        *,
        checker: Checker | None = None,
        previewer: Previewer | None = None,
        app_version: str | None = None,
    ) -> None:
        self._storage = storage
        self._checker = checker or default_checker
        self._previewer = previewer or default_previewer
        self._app_version = app_version
        self._lock = threading.RLock()
        self._cards: dict[str, Card] = {}
        self._practice = PracticeEngine(storage)
        self._fitter: threading.Thread | None = None
        self._launched = False  # the launch repair ran (ADR-0019 item 8)
        self._resumed = False  # the open session was looked at since this launch
        # The last background fit's reports (flashcard sets), or the error that stopped it.
        self.last_auto_fit: list[FitReport] | Exception | None = None
        self.last_refit: object | Exception | None = None  # the last learner refit's outcome

    # ================================================================ wiring

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def practice(self) -> PracticeEngine:
        return self._practice

    def engine(self) -> Engine:
        """The FSRS engine, for flashcards: their parameter sets, fits and the log repairs."""
        return Engine(self._storage)

    def _launch(self) -> None:
        """Once per launch: attempts graded under a since-changed answer key are voided
        (PACK-14), and flashcard memory is rebuilt for a fit an older build left half-applied."""
        if self._launched:
            return
        self._launched = True
        engine = self.engine()
        engine.void_changed_keys()
        engine.repair_fit()

    def _now(self) -> int:
        return self._storage.db.clock.now_ms()

    def _today(self) -> date:
        return self._practice.days().day_of(self._now())

    def _setting(self, key: str, default: Any) -> Any:
        return self._storage.users.get_setting(key, default)

    def _card(self, card_id: str) -> Card:
        """Cards are read-only while a pack is open (a pack update reopens storage)."""
        card = self._cards.get(card_id)
        if card is None:
            card = self._storage.packs.card(card_id)
            if card is None:
                raise QueueError(f"card {card_id} is no longer available")
            self._cards[card_id] = card
        return card

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._lock:
            yield

    # ================================================================ home and plans

    def today(self) -> v.TodayView:
        """Home: today's items and minutes, by course and by role; what keeping pace costs;
        skills behind or set aside; sittings; the planner's notes. Never an overdue count."""
        with self._locked():
            self._launch()
            open_session = self._open_session()
            day = self._today()
            plan = Plan.from_json(open_session.plan) if open_session is not None else None
            if plan is None or plan.mode != DAILY:
                plan = self._daily_plan(day)
            pending = [i for i in plan.items if i.pending]
            summary: Mapping[str, Any] = plan.info.get("summary") or {}
            problems = [i for i in pending if i.kind == "problem"]
            done_today = (
                open_session is None
                and not problems
                and bool(self._storage.users.attempts(since=self._practice.days().start(day)))
            )
            extra = not problems and bool(self._extra_items(day, EXTRA_DEFAULT))
            deck = self._deck(day)
            return v.TodayView(
                day=day.isoformat(),
                problems=len(problems),
                minutes=_minutes(pending),
                flashcards=sum(1 for i in pending if i.kind == "flashcard"),
                courses=self._course_lines(pending),
                exams=self._exam_lines(day),
                session_open=open_session is not None,
                done_today=done_today,
                extra_practice_available=extra,
                flashcards_to_rewrite=deck.leeches,
                by_role=dict(Counter(i.purpose for i in problems)),
                hours_to_keep_pace=summary.get("hours_to_keep_pace"),
                hours_basis=summary.get("hours_basis", "none"),
                standard_hours=summary.get("standard_hours"),
                behind=tuple(summary.get("behind", ())),
                set_aside=tuple(summary.get("set_aside", ())),
                sittings=tuple(
                    v.SittingLine(id=str(s["id"]), skills=tuple(s["skills"]))
                    for s in summary.get("sittings", ())
                ),
                notes=tuple(summary.get("notes", ())),
            )

    def forecast(self, day: date | None = None) -> v.Forecast:
        """A later day's plan (tomorrow by default): problems and minutes, per course."""
        with self._locked():
            day = day or self._today() + timedelta(days=1)
            items = self._problem_items(
                self._practice.plan_day(day, self._practice.days().moment(day)),
                Plan(day=day.isoformat()),
            )[1]
            return v.Forecast(
                day=day.isoformat(),
                problems=len(items),
                minutes=_minutes(items),
                courses=self._course_lines(items),
            )

    def plan_preview(self, day: date | None = None) -> Plan:
        """The plan a daily start would build (tests, stats, debugging)."""
        with self._locked():
            return self._daily_plan(day or self._today())

    def _course_lines(self, items: Sequence[PlanItem]) -> tuple[v.CourseLine, ...]:
        lines: dict[str, list[PlanItem]] = {}
        for item in items:
            lines.setdefault(item.course_id or "", []).append(item)
        titles = {c.id: c.title for c in self._storage.packs.courses()}
        return tuple(
            v.CourseLine(
                course_id=c,
                title=titles.get(c, c),
                problems=sum(1 for i in group if i.kind == "problem"),
                minutes=_minutes(group),
            )
            for c, group in sorted(lines.items())
        )

    def _exam_lines(self, day: date) -> tuple[v.ExamLine, ...]:
        days = self._practice.days()
        out = []
        for exam in sorted(self._storage.users.exams(), key=lambda e: e.at):
            left = (days.day_of(exam.at) - day).days
            if left < 0:
                continue
            out.append(
                v.ExamLine(
                    exam_id=exam.id,
                    name=exam.name,
                    course_id=exam.course_id,
                    days_left=left,
                    practice_test=left <= PRACTICE_TEST_WINDOW_DAYS,
                )
            )
        return tuple(out)

    # ================================================================ building plans

    def _daily_plan(self, day: date) -> Plan:
        """Today's plan: everything the planner has left for today (the items served so far
        today come from the log), with the day's flashcards placed between the problems."""
        practice = self._practice
        planned = practice.plan_day(day, self._now(), practice.served(day))
        plan, problems = self._problem_items(planned, Plan(day=day.isoformat(), mode=DAILY))
        flash, left = self._flashcard_items(day)
        items = place_flashcards(problems, flash)
        return replace(
            plan,
            n=len(problems),
            items=tuple(items),
            flashcards=left,
            info={"engine": ENGINE, "summary": self._summary_info(planned)},
        )

    def _problem_items(self, planned: PracticePlan, plan: Plan) -> tuple[Plan, list[PlanItem]]:
        """The planner's items as plan items, with fresh keys."""
        catalog = self._practice.catalog()
        version = self._practice.params().version
        out = []
        for p in planned.items:
            plan, key = plan.next_key("pp")
            out.append(_plan_item(key, p, catalog, version))
        return plan, out

    def _summary_info(self, planned: PracticePlan) -> dict[str, Any]:
        """What Home shows about the plan (kept in plan.info, so an open session's Home needs
        no re-plan): hours to keep pace, skills behind and set aside, sittings, notes. Lists
        and notes are in plain words (skill names, never ids or formulas); `set_aside_ids`
        keeps the ids, for the study screen's set-aside notice."""
        catalog = self._practice.catalog()
        names = catalog.name
        behind: list[str] = []
        aside_ids: list[str] = []
        sittings: list[dict[str, Any]] = []
        notes: list[str] = []
        for day_plan in planned.plans.values():
            behind += [names(k) for k in day_plan.behind]
            aside = [str(k) for k in getattr(day_plan, "set_aside", ())]
            aside_ids += aside
            for sid, skills in tuple(getattr(day_plan, "sittings", ())):
                sittings.append({"id": str(sid), "skills": [names(k) for k in skills]})
            notes += [plain_note(note, catalog, set_aside=aside) for note in day_plan.notes]
        return {
            "hours_to_keep_pace": planned.hours_to_keep_pace,
            "hours_basis": planned.hours_basis,
            "standard_hours": planned.standard_hours,
            "behind": list(dict.fromkeys(behind)),
            "set_aside": list(dict.fromkeys(names(k) for k in aside_ids)),
            "set_aside_ids": list(dict.fromkeys(aside_ids)),
            "sittings": sittings,
            "notes": list(dict.fromkeys(notes)),
        }

    def _deck(self, day: date) -> Any:
        days = self._practice.days()
        users = self._storage.users
        legacy = {k for k, s in users.skill_states().items() if s.introduced_at is not None}
        return day_flashcards(
            self._storage,
            hidden=self._practice.unavailable(),
            skill_sections={
                s.id: s.section_id for s in self._storage.packs.skills() if s.section_id
            },
            section_states={k: s.state for k, s in users.section_states().items()},
            scheduled=self._practice.scheduled_skills(),
            introduced=self._practice.introduced(day) | legacy,
            tomorrow_start=days.start(day + timedelta(days=1)),
            today_start=days.start(day),
        )

    def _flashcard_items(self, day: date) -> tuple[list[PlanItem], int]:
        """The day's flashcards (I5, like Anki's limits): the daily limit less those done
        today, new ones only up to `daily.new_flashcards` less today's new ones. Returns the
        items and the limit left (refreshers draw on it)."""
        days = self._practice.days()
        start, end = days.bounds(day)
        done = [
            a
            for a in self._storage.users.attempts(since=start, until=end)
            if a.final and a.card_kind in ("flashcard", "cloze")
        ]
        limit = max(0, int(self._setting("daily.flashcards", 50)) - len(done))
        new_left = int(self._setting("daily.new_flashcards", 20)) - sum(
            1 for a in done if a.predicted_recall is None
        )
        deck = self._deck(day)
        catalog = self._practice.catalog()
        out: list[PlanItem] = []
        for card_id, ord_, skill in deck.due:
            if len(out) >= limit:
                break
            if (card_id, ord_) in deck.new:
                if new_left <= 0:
                    continue
                new_left -= 1
            out.append(_flashcard_item(card_id, ord_, skill, catalog))
        return out, max(0, limit - len(out))

    def _tomorrow(self, day: date) -> PracticePlan:
        tomorrow = day + timedelta(days=1)
        return self._practice.plan_day(tomorrow, self._practice.days().moment(tomorrow))

    def _extra_items(
        self, day: date, count: int, planned: PracticePlan | None = None
    ) -> list[PlannedItem]:
        """Extra practice: the growth and maintenance problems tomorrow's plan holds
        (`planned`: that plan, when the caller has it)."""
        planned = planned or self._tomorrow(day)
        chosen = [
            p
            for p in planned.items
            if p.item.problem is not None and p.item.role in ("growth", "maintenance")
        ]
        return chosen[:count]

    def _extra_plan(self, req: v.StartRequest, day: date) -> Plan:
        catalog = self._practice.catalog()
        version = self._practice.params().version
        plan = Plan(day=day.isoformat(), mode="extra")
        items = []
        for p in self._extra_items(day, req.count or EXTRA_DEFAULT):
            plan, key = plan.next_key("ex")
            item = _plan_item(key, p, catalog, version)
            items.append(replace(item, why=why("review.extra-plan")))
        return replace(plan, n=len(items), items=tuple(items), info={"engine": ENGINE})

    # ================================================================ sessions

    def _open_session(self) -> SessionState | None:
        """Today's open session. One from an earlier study day, or one an older build
        planned, is closed first: its held answer is graded (at its own time), a practice
        test is graded, and the row is ended (QUE-16: a plan from before the rollover is
        rebuilt)."""
        users = self._storage.users
        session = users.latest_open_session()
        if session is None:
            return None
        plan = Plan.from_json(session.plan)
        ours = plan.info.get("engine") == ENGINE
        if ours:
            session = self._recover(session)
            if not self._resumed:
                session = self._interrupted(session, plan)
        self._resumed = True
        if ours and session.study_day == self._today().isoformat():
            return session
        plan = Plan.from_json(session.plan)
        if session.current and session.current.get("pending"):
            session, plan, _ = self._finalize(session, plan, replan=False)
        if plan.mode == "practice-test":
            self._grade_test(session, plan)
        users.end_session(_id(session))
        return None

    def _interrupted(self, session: SessionState, plan: Plan) -> SessionState:
        """At the first look after a launch: a sitting problem left on screen unanswered was
        interrupted (the app was quit or crashed), so its time is unknown and the sitting is
        void rather than failed on a clock that ran while the app was closed."""
        cur = session.current
        if not cur or cur.get("pending") or cur.get("closed") or cur.get("interrupted"):
            return session
        item = plan.item(str(cur.get("key")))
        if item is None or item.purpose != "sitting" or item.meta is None:
            return session
        return self._storage.users.save_session(
            replace(session, current={**cur, "interrupted": True})
        )

    def _recover(self, session: SessionState) -> SessionState:
        """Finish a re-plan a crash interrupted (the answer committed, its follow-up not)."""
        key = session.extra.get("replan")
        if not key:
            return session
        plan = Plan.from_json(session.plan)
        current = dict(session.current or {})
        presentation = current.get("presentation_id")
        attempt = next(
            (
                a
                for a in self._storage.users.attempts(session_id=session.id, newest_first=True)
                if a.final and a.presentation_id == presentation
            ),
            None,
        )
        if attempt is not None:
            current["attempt_id"] = attempt.id
            plan = self._replan(session, plan, str(key))
        extra = {k: val for k, val in session.extra.items() if k != "replan"}
        return self._storage.users.save_session(
            replace(session, plan=plan.to_json(), current=current or None, extra=extra)
        )

    def _require(self) -> tuple[SessionState, Plan]:
        session = self._open_session()
        if session is None:
            raise QueueError("No study session is open. Press Start.")
        return session, Plan.from_json(session.plan)

    def resume(self) -> v.Turn | None:
        """QUE-16: the open session at the same problem, or None."""
        with self._locked():
            session = self._open_session()
            return None if session is None else self._turn(session)

    def current(self) -> v.Turn:
        with self._locked():
            session, _ = self._require()
            return self._turn(session)

    def start(self, request: v.StartRequest | Mapping[str, Any] | None = None) -> v.Turn:
        """Start a session, or resume today's open one of the same mode."""
        req = request if isinstance(request, v.StartRequest) else v.StartRequest.from_dict(request)
        with self._locked():
            self._launch()
            users = self._storage.users
            if req.mode not in MODES:
                raise QueueError(f"Unknown study mode {req.mode!r}.")
            day = self._today()
            if req.mode == "practice-test":
                self._test_exam(req, day)  # refused before the open session is closed
            open_session = self._open_session()
            if open_session is not None:
                if Plan.from_json(open_session.plan).mode == req.mode:
                    return self._turn(open_session)
                self._close(open_session)  # its held answer and test are graded first
            plan = self._new_plan(req, day)
            if not plan.items:
                return self._empty_turn(plan)
            untimed = bool(self._setting("session.untimed_default", False))
            session = users.start_session(
                SessionState(
                    study_day=day.isoformat(),
                    started_at=self._now(),
                    untimed=untimed if req.untimed is None else req.untimed,
                    plan=plan.to_json(),
                    extra={"active_total_ms": 0, "breaks": 0, "learned": []},
                )
            )
            session = self._advance(session, plan)
            return self._turn(session)

    def _new_plan(self, req: v.StartRequest, day: date) -> Plan:
        if req.mode == DAILY:
            return self._daily_plan(day)
        if req.mode == "extra":
            return self._extra_plan(req, day)
        if req.mode == "practice-test":
            return self._test_plan(req, day)
        raise QueueError(f"unknown study mode {req.mode!r}")

    def _empty_turn(self, plan: Plan) -> v.Turn:
        if plan.mode == DAILY:
            if not self._practice.active_courses():
                message = "Set up a course first: its start date, or the section your class is at."
            else:
                message = "Today's plan is done."
        else:
            message = "Nothing to practice here right now."
        return v.Turn(type="empty", message=message, mode=plan.mode)

    def _close(self, session: SessionState) -> None:
        plan = Plan.from_json(session.plan)
        if session.current and session.current.get("pending"):
            session, plan, _ = self._finalize(session, plan, replan=False)
        if plan.mode == "practice-test":
            self._grade_test(session, plan)
        self._storage.users.end_session(_id(session))

    def end(self) -> v.Summary:
        """End the session: grade a held answer, then the summary with tomorrow's forecast."""
        with self._locked():
            session, plan = self._require()
            if session.current and session.current.get("pending"):
                session, plan, _ = self._finalize(session, plan, replan=False)
            test = None
            if plan.mode == "practice-test":
                session, plan, test = self._grade_test(session, plan)
            ended = self._storage.users.end_session(_id(session))
            summary = self._summary(ended, plan, test)
        self.start_auto_fit()
        return summary

    # ================================================================ background fits

    def start_auto_fit(self) -> bool:
        """After a session (never mid-answer), in the background, one at a time: the flashcard
        parameter sets that are due (I7), then the learner's refit when it is due (design
        3.6). Fitting runs outside the service lock; recording an outcome takes it, so it falls
        between two calls and never interleaves with a graded answer. False when a fit is
        still running."""
        if self._fitter is not None and self._fitter.is_alive():
            return False
        self._fitter = threading.Thread(target=self._auto_fit, name="auto-fit", daemon=True)
        self._fitter.start()
        return True

    def _auto_fit(self) -> None:
        try:
            self.last_auto_fit = self.engine().auto_fit(writing=self._locked, kinds=("flashcard",))
        except Exception as error:
            self.last_auto_fit = error
        try:
            self.last_refit = self._practice.refit(writing=self._locked)
        except Exception as error:
            self.last_refit = error

    def wait_for_auto_fit(self, timeout: float | None = None) -> bool:
        """Block until a background fit is done (tests, closing the profile)."""
        fitter = self._fitter
        if fitter is not None:
            fitter.join(timeout)
        return fitter is None or not fitter.is_alive()

    # ================================================================ serving

    def _advance(self, session: SessionState, plan: Plan) -> SessionState:
        """Make the first pending item current and save. An item whose card is no longer
        available (suspended, reported or gone) is skipped; in a daily plan the planner is
        asked once more first, so another problem takes its place."""
        users = self._storage.users
        now = self._now()
        unavailable = self._practice.unavailable()
        replanned = False
        while True:
            item = plan.first_pending()
            if item is None:
                return users.save_session(
                    replace(session, plan=plan.to_json(), current=None, active_ms=0, draft=None)
                )
            card = self._available(item, unavailable)
            if card is None:
                if plan.mode == DAILY and item.kind != "flashcard" and not replanned:
                    replanned = True
                    plan = self._with_plan(plan, self._fresh_plan(plan))
                    continue
                plan = plan.updated(replace(item, status="skipped", result={"no_problem": True}))
                continue
            current = {
                "key": item.key,
                "card_id": card.id,
                "rev": card.rev,
                "presentation_id": _uid(),
                "shown_at": now,
                "tries": 0,
                "example_opened": False,
                "pending": None,
                "closed": False,
            }
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

    def _available(self, item: PlanItem, unavailable: frozenset[str]) -> Card | None:
        if item.card_id is None or item.card_id in unavailable:
            return None
        try:
            return self._card(item.card_id)
        except QueueError:
            return None

    # ================================================================ turns and views

    def _turn(self, session: SessionState, *, message: str = "", break_due: bool = False) -> v.Turn:
        plan = Plan.from_json(session.plan)
        cur = session.current
        if cur is None:
            if plan.mode == "practice-test" or not plan.pending:
                summary = self._end_after_last(session, plan)
                return v.Turn(
                    type="summary",
                    session_id=session.id,
                    summary=summary,
                    message=message,
                    mode=plan.mode,
                )
            session = self._advance(session, plan)
            return self._turn(session, message=message, break_due=break_due)
        item = plan.item(str(cur["key"]))
        if item is None:
            raise StorageError("the session's current item is missing from its plan")
        result = None
        if cur.get("pending") or cur.get("closed"):
            result = self._result_view(session, plan, item)
        return v.Turn(
            type="problem",
            session_id=session.id,
            problem=self._problem_view(session, plan, item),
            progress=self._progress(plan, item),
            result=result,
            message=message,
            break_due=break_due,
            mode=plan.mode,
        )

    def _end_after_last(self, session: SessionState, plan: Plan) -> v.Summary:
        test = None
        if plan.mode == "practice-test":
            session, plan, test = self._grade_test(session, plan)
        ended = self._storage.users.end_session(_id(session))
        summary = self._summary(ended, plan, test)
        self.start_auto_fit()  # a session that finished through Continue
        return summary

    def _progress(self, plan: Plan, item: PlanItem) -> v.Progress:
        done = [i for i in plan.items if i.status == "done" and i.slots]
        on_screen = 1 if item.slots and item.pending else 0
        return v.Progress(
            position=len(done) + on_screen,
            total=sum(i.slots for i in plan.items if i.status != "skipped"),
            answered=len(done),
            correct=sum(1 for i in done if (i.result or {}).get("correct")),
        )

    def _attempts_allowed(self, plan: Plan, item: PlanItem) -> int:
        """Tries per answer box: one in a practice test and for flashcards; no limit for a
        problem (only its first try counts)."""
        if plan.mode == "practice-test" or item.kind != "problem":
            return 1
        return NO_LIMIT

    def _problem_view(self, session: SessionState, plan: Plan, item: PlanItem) -> v.ProblemView:
        cur = session.current or {}
        card = self._card(str(cur["card_id"]))
        meta = item.meta or {}
        textbook = self._practice.catalog().textbooks.get(item.skill_id or "")
        if meta.get("sitting") or item.kind != "problem":
            textbook = None  # a sitting is closed book; examples and flashcards carry none
        return v.ProblemView(
            item_key=item.key,
            kind=item.kind,
            card=self._card_view(card, ord_=item.card_ord, as_example=item.kind == "example"),
            reason=v.Reason(tag=item.tag, label=item.label, why=item.why),
            attempts_allowed=self._attempts_allowed(plan, item),
            tries_used=int(cur.get("tries", 0)),
            draft=session.draft,
            active_ms=session.active_ms,
            target_ms=None,
            untimed=session.untimed,
            practice_test=plan.mode == "practice-test",
            role=item.purpose if item.meta is not None and item.kind == "problem" else None,
            plan_reason=str(meta["reason"]) if meta.get("reason") else None,
            textbook=None
            if textbook is None
            else v.TextbookView(book=textbook.book, section=textbook.section),
            sitting=self._sitting_view(plan, item),
        )

    def _sitting_view(self, plan: Plan, item: PlanItem) -> v.SittingView | None:
        """A sitting item: its place in the sitting, and its skill block's time limit (the
        planner's `time_limit`: the sum of that skill's sitting problems' standard times)
        against the sitting clock the block's earlier problems used (wall clock, pauses
        included; the page adds the running time of the problem on screen). Nothing is cut
        off at the limit."""
        meta = item.meta or {}
        sitting = meta.get("sitting")
        if not sitting:
            return None
        members = [
            i
            for i in plan.items
            if (i.meta or {}).get("sitting") == sitting and i.status != "skipped"
        ]
        keys = [i.key for i in members]
        block = [i for i in members if i.skill_id == item.skill_id]
        limit = meta.get("time_limit")
        if limit is None:
            limit = sum(float((i.meta or {}).get("standard") or 0.0) for i in block)
        elapsed = sum(
            int((i.result or {}).get("sitting_ms", (i.result or {}).get("active_ms")) or 0)
            for i in block
            if i.key != item.key and not i.pending
        )
        return v.SittingView(
            id=str(sitting),
            index=keys.index(item.key) + 1 if item.key in keys else 1,
            total=len(members),
            time_limit_ms=round(limit * MINUTE_MS),
            block_elapsed_ms=elapsed,
        )

    def _card_view(self, card: Card, *, ord_: int = 0, as_example: bool = False) -> v.CardView:
        prompt = card.question_md or card.front_md or card.text_md or ""
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
            calculator=card.calculator,
            angles=card.angles,
            plot=card.plot,
            self_graded=any(s.spec.answer_type == "self" for s in specs),
            back_md=back,
            solution_md=card.solution_md
            if card.kind == "example"
            else _worked_md(card)
            if as_example  # a problem shown solved in place of an example card
            else None,
            shown_work=_work(card),
            reasons=tuple(
                v.ChoiceView(index=i, text_md=c.text_md) for i, c in enumerate(card.reasons)
            ),
            error_step=None,
            cloze=ord_ + 1 if card.kind == "cloze" else None,
            type_answer=card.kind == "flashcard" and card.answer is not None,
        )

    def _solution_view(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        *,
        correct: bool,
        pending: Mapping[str, Any],
    ) -> v.SolutionView:
        card = self._card(str((session.current or {})["card_id"]))
        catalog = self._practice.catalog()
        skill_id = card.skill_id

        def name(k: str | None) -> str | None:
            return catalog.skill_names.get(k or "")

        active = pending.get("timing", {}).get("active_ms")
        standard = (item.meta or {}).get("standard")
        target = None if standard is None or session.untimed else round(float(standard) * MINUTE_MS)
        time_text = None
        if active is not None and not session.untimed:
            time_text = _clock(int(active)) + (f" · standard {_clock(target)}" if target else "")
        first_clean = correct and int(pending.get("attempt_number", 1)) == 1
        easy_key = bool(self._setting("rating.too_easy_key", True))
        textbook = catalog.textbooks.get(skill_id or "")
        return v.SolutionView(
            skill_id=skill_id,
            skill_name=name(skill_id),
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
            confident_error=False,
            can_mark_too_easy=first_clean and easy_key and plan.mode != "practice-test",
            textbook_ref=None
            if textbook is None or correct
            else f"{textbook.book} {textbook.section}".strip(),
            rubric=card.rubric,
            shown_work=_work(card),
        )

    def _result_view(self, session: SessionState, plan: Plan, item: PlanItem) -> v.AttemptResult:
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
            solution=self._solution_view(session, plan, item, correct=correct, pending=pending),
            tries_used=int(cur.get("tries", 0)),
            attempts_allowed=self._attempts_allowed(plan, item),
            first_try_counted=bool(
                pending.get("first_submission", int(pending.get("attempt_number", 1)) == 1)
            ),
        )

    # ================================================================ answering

    def read_answer(self, raw: str, *, part: str | None = None, source: v.Source = "text") -> Any:
        """The live "We read your answer as ..." preview (never an attempt)."""
        with self._locked():
            session, _ = self._require()
            card = self._card(str((session.current or {})["card_id"]))
            spec = next((p.spec for p in specs_for(card) if p.label == part), None)
            if spec is None:
                spec = specs_for(card)[0].spec
            return self._previewer(raw, spec, source)

    def tick(self, active_ms: int, draft: str | None = None) -> v.Tick:
        """Save the active time so far and the typed draft (QUE-16); break reminders."""
        with self._locked():
            session, _ = self._require()
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
        minutes = self._setting("ui.break_reminder_minutes", 50)
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
            session, plan = self._require()
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
                "unsure": req.confidence == "unsure",
                "guessed": req.guessed,
                "timing": _timing_json(guarded.timing),
                "flags": list(guarded.flags),
                "raw_input": raw,
            }
            if plan.mode == "practice-test":
                return self._submit_test(session, plan, item, cur, card, req, base)

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
                return self._hold(session, plan, item, cur, pending, break_due)
            if card.parts and not self_graded:
                return self._submit_parts(
                    session, plan, item, cur, card, req, base, break_due, guarded.flags
                )

            checked = check_answers(
                card,
                [(a.part, a.value) for a in req.answers],
                req.answers[0].source if req.answers else "text",
                self._checker,
            )
            verdicts = [_verdict_json(p) for p in checked.verdicts]
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
                    can_retry=True,
                )
            if checked.undecided:
                cur.update(self_grade=True, undecided=not self_graded)
                session = self._storage.users.save_session(replace(session, current=cur, draft=raw))
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="self-grade",
                    verdicts=tuple(v.PartVerdictView(**p) for p in verdicts),
                    message="Compare your work with the solution and grade it yourself.",
                    solution=self._solution_view(session, plan, item, correct=False, pending=base),
                    tries_used=int(cur.get("tries", 0)),
                    attempts_allowed=self._attempts_allowed(plan, item),
                    break_due=break_due,
                )
            tries = int(cur.get("tries", 0)) + 1
            if not checked.correct:
                cur["tries"] = tries
                cur["last_verdicts"] = verdicts  # "Your answer" beside the solution, later
                wrong = {
                    **base,
                    "correct": False,
                    "verdict": "incorrect",
                    "parsed": _parsed(verdicts),
                    "matched_wrong": checked.matched_index,
                }
                self._record_try(session, plan, item, cur, card, wrong)
                return v.AttemptResult(
                    item_key=item.key,
                    outcome="retry",
                    verdicts=tuple(v.PartVerdictView(**_quiet(p)) for p in verdicts),
                    message="Not quite.",
                    tries_used=tries,
                    attempts_allowed=self._attempts_allowed(plan, item),
                    break_due=break_due,
                    can_retry=True,
                    first_try_counted=tries == 1,
                )
            pending = {
                **base,
                "correct": True,
                "verdict": "correct",
                "verdicts": verdicts,
                "parsed": _parsed(verdicts),
                "matched_wrong": None,
            }
            return self._hold(session, plan, item, cur, pending, break_due)

    def _submit_parts(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        req: v.SubmitRequest,
        base: dict[str, Any],
        break_due: bool,
        flags: Sequence[str],
    ) -> v.AttemptResult:
        """Multi-part problems: one box, verdict and try count per part. A part is final once
        right; each "Not quite" is logged at once against its part. The problem is final when
        every part is (or when the student gives up on the rest)."""
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
            return {**_verdict_json(p), "final": final, "tries_used": tries}

        def shown(*, quiet: bool) -> list[dict[str, Any]]:
            out = []
            for p in card.parts:
                entry = state.get(p.label, {})
                if "verdict" in entry:
                    verdict = entry["verdict"]
                    out.append(_quiet(verdict) if quiet and not entry.get("final") else verdict)
            return out

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
                attempts_allowed=NO_LIMIT,
                break_due=break_due,
                can_retry=True,
            )
        if checked.undecided:  # the checker can't decide a part: the student grades it all
            cur.update(self_grade=True, undecided=True)
            session = self._storage.users.save_session(replace(session, current=cur, draft=raw))
            return v.AttemptResult(
                item_key=item.key,
                outcome="self-grade",
                verdicts=tuple(v.PartVerdictView(**p) for p in shown(quiet=True)),
                message="Compare your work with the solution and grade it yourself.",
                solution=self._solution_view(session, plan, item, correct=False, pending=base),
                tries_used=int(cur.get("tries", 0)),
                attempts_allowed=NO_LIMIT,
                break_due=break_due,
            )
        retrying: list[str] = []
        firsts = False
        for p in checked.verdicts:
            label = str(p.part)
            entry = state.setdefault(label, {"tries": 0})
            entry["tries"] = int(entry.get("tries", 0)) + 1
            firsts = firsts or entry["tries"] == 1
            entry["correct"] = p.status == Status.CORRECT
            entry["final"] = entry["correct"]
            entry["verdict"] = view(p, entry["final"], entry["tries"])
            entry["raw"] = given[label].value
            entry["read_as"] = p.read_as
            entry["matched_wrong"] = p.wrong_index
            if not entry["final"]:
                retrying.append(label)
        cur["parts"] = state
        cur["tries"] = max(int(x.get("tries", 0)) for x in state.values())
        for label in retrying:  # each "Not quite" is logged at once, against its part
            entry = state[label]
            wrong = {
                **base,
                "attempt_number": int(entry["tries"]),
                "correct": False,
                "verdict": "incorrect",
                "raw_input": str(entry["raw"]),
                "parsed": entry.get("read_as"),
                "matched_wrong": entry.get("matched_wrong"),
                "flags": list(flags),
            }
            self._record_try(session, plan, item, cur, card, wrong, part=label)
        if not all(state.get(p.label, {}).get("final") for p in card.parts):
            extra = {k: val for k, val in session.extra.items() if k != "undo"}
            self._storage.users.save_session(replace(session, current=cur, draft=None, extra=extra))
            return v.AttemptResult(
                item_key=item.key,
                outcome="retry",
                verdicts=tuple(v.PartVerdictView(**p) for p in shown(quiet=True)),
                message="Not quite." if retrying else "Saved. Now the other parts.",
                tries_used=int(cur["tries"]),
                attempts_allowed=NO_LIMIT,
                break_due=break_due,
                can_retry=True,
                first_try_counted=firsts,
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
        correct, number, _ = _parts_facts(outcomes)
        final = shown(quiet=False)
        pending = {
            **base,
            "raw_input": " | ".join(
                f"{p.label}: {state[p.label].get('raw', '')}" for p in card.parts
            ),
            "attempt_number": number,
            "correct": correct,
            "verdict": "correct" if correct else "incorrect",
            "verdicts": final,
            "parsed": _parsed(final),
            "parts": [o.as_json() for o in outcomes],
        }
        return self._hold(session, plan, item, cur, pending, break_due, first=firsts)

    def show_solution(self) -> v.AttemptResult:
        """Self-graded problems: the solution (and the rubric to tick) before the student
        grades it (`submit` with `rubric_ticked` or `self_grade`). Any other problem: only after
        a wrong first try, and it ends the problem like Give up (the solution is help)."""
        with self._locked():
            session, plan = self._require()
            cur, item = self._current_item(session, plan)
            if item.kind != "problem" or plan.mode == "practice-test":
                raise QueueError("There is no solution to show here.")
            if cur.get("pending") or cur.get("closed"):
                raise QueueError("This problem is already answered; continue.")
            card = self._card(str(cur["card_id"]))
            if not (
                any(p.spec.answer_type == "self" for p in specs_for(card)) or cur.get("self_grade")
            ):
                if int(cur.get("tries", 0)) < 1:
                    raise QueueError("Try it first. Give up shows the solution.")
                return self._give_up(session, plan, cur, item, TimingReport())
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
                solution=self._solution_view(session, plan, item, correct=False, pending={}),
                tries_used=int(cur.get("tries", 0)),
                attempts_allowed=self._attempts_allowed(plan, item),
            )

    def give_up(self, timing: TimingReport | Mapping[str, Any] | None = None) -> v.AttemptResult:
        """Give up: the full solution, and the problem ends (before any answer, its first try
        counts as a miss)."""
        report = timing if isinstance(timing, TimingReport) else TimingReport.from_dict(timing)
        with self._locked():
            session, plan = self._require()
            cur, item = self._current_item(session, plan)
            return self._give_up(session, plan, cur, item, report)

    def _give_up(
        self,
        session: SessionState,
        plan: Plan,
        cur: dict[str, Any],
        item: PlanItem,
        report: TimingReport,
    ) -> v.AttemptResult:
        if item.kind != "problem":
            raise QueueError("Only a problem can be given up.")
        if cur.get("pending") or cur.get("closed"):
            raise QueueError("This problem is already answered; continue.")
        now = self._now()
        guarded = guard_timing(
            report, shown_at=cur.get("shown_at"), now_ms=now, saved_active_ms=session.active_ms
        )
        session, break_due = self._note_active(session, guarded.timing.active_ms or 0)
        pending: dict[str, Any] = {
            "at": now,
            "correct": False,
            "gave_up": True,
            "attempt_number": int(cur.get("tries", 0)) + 1,
            "verdict": "gave-up",
            # The last try stays "Your answer" beside the solution, with its feedback.
            "verdicts": list(cur.get("last_verdicts") or []),
            "timing": _timing_json(guarded.timing),
            "flags": list(guarded.flags),
        }
        card = self._card(str(cur["card_id"]))
        if plan.mode == "practice-test":
            return self._submit_test(session, plan, item, cur, card, v.SubmitRequest(), pending)
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
            correct, number, gave_up = _parts_facts(outcomes)
            pending.update(
                correct=correct,
                gave_up=gave_up,
                attempt_number=max(1, number),
                verdict="gave-up" if gave_up else "correct" if correct else "incorrect",
                verdicts=[e["verdict"] for e in state.values() if "verdict" in e],
                parts=[o.as_json() for o in outcomes],
            )
        return self._hold(
            session, plan, item, cur, pending, break_due, first=int(cur.get("tries", 0)) == 0
        )

    def _hold(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        pending: dict[str, Any],
        break_due: bool,
        *,
        first: bool | None = None,
    ) -> v.AttemptResult:
        """Save a final answer in the session row; it is committed on continue. `first`:
        whether this submission was the item's first try (default: the answer's attempt
        number is 1; a multi-part problem says it itself)."""
        if first is None:
            first = int(pending.get("attempt_number", 1)) == 1
        pending["first_submission"] = first
        cur["pending"] = pending
        cur["tries"] = max(int(cur.get("tries", 0)), int(pending.get("attempt_number", 1)))
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
            solution=self._solution_view(session, plan, item, correct=correct, pending=pending),
            tries_used=cur["tries"],
            attempts_allowed=self._attempts_allowed(plan, item),
            break_due=break_due,
            first_try_counted=first,
        )

    def open_example(self) -> None:
        """The student opened the skill's worked example mid-problem: help, so the problem's
        first try counts as aided (and its time is not a valid solving time, TIME-5)."""
        with self._locked():
            session, plan = self._require()
            cur, item = self._current_item(session, plan)
            if (item.meta or {}).get("sitting"):
                raise QueueError("A sitting is closed book.")
            cur["example_opened"] = True
            self._storage.users.save_session(replace(session, current=cur))

    def next(self) -> v.Turn:
        """Continue: commit the answer on screen if it isn't yet, then the next item."""
        with self._locked():
            session, plan = self._require()
            cur = session.current
            if cur is not None and plan.mode == "practice-test":
                return self._turn(session)
            message = ""
            if cur is not None:
                item = plan.item(str(cur["key"]))
                if cur.get("pending"):
                    before = set(_aside(plan))
                    session, plan, _ = self._finalize(session, plan)
                    message = self._set_aside_message(plan, before)
                elif not cur.get("closed"):
                    if item is not None and item.kind == "example":
                        shown = {
                            "at": self._now(),
                            "correct": False,
                            "verdict": "shown",
                            "timing": {},
                        }
                        session, plan, _ = self._finalize(
                            replace(session, current={**cur, "pending": shown}), plan
                        )
                    elif item is not None and item.kind == "flashcard":
                        raise QueueError("Rate the flashcard first.")
                    else:
                        raise QueueError("Submit an answer or give up first.")
            session = self._advance(session, plan)
            return self._turn(session, message=message)

    def _set_aside_message(self, plan: Plan, before: set[str]) -> str:
        """A skill the re-plan set aside for today (the stuck ladder's third rung): "{name} is
        set aside for today. See {book} §{section}." (Turn.message on the next turn)."""
        catalog = self._practice.catalog()
        return " ".join(
            set_aside_line(catalog.name(k), catalog.textbooks.get(k))
            for k in _aside(plan)
            if k not in before
        )

    # ================================================================ committing

    def _attempt_row(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: Mapping[str, Any],
        pending: Mapping[str, Any],
        card: Card,
        *,
        final: bool,
        part: str | None = None,
    ) -> Attempt:
        """The attempt row of one try (final or not), with what the planner chose."""
        timing = TimingFacts(**pending.get("timing", {}))
        meta = item.meta or {}
        verdict = str(
            pending.get("verdict") or ("correct" if pending.get("correct") else "incorrect")
        )
        number = int(pending.get("attempt_number", 1))
        correct = bool(pending.get("correct"))
        source = self._storage.packs.card_source(card.id) or "user"
        extra: dict[str, Any] = {"queue_mode": plan.mode, "item": item.key}
        if item.meta is not None:
            extra["plan"] = {
                "course": item.course_id,
                "skill": item.skill_id,
                "problem": meta.get("problem"),
                "block": bool(meta.get("block")),
                "priority": meta.get("priority"),
                "reason": meta.get("reason"),
                "minutes": meta.get("minutes"),
                "tier": meta.get("tier"),
                "time_limit": meta.get("time_limit"),
            }
        if pending.get("parts"):
            extra["parts"] = list(pending["parts"])
        if verdict in ("self", "undecided"):
            extra["correct"] = correct
        if cur.get(UNDO_AFTER_SOLUTION):
            extra["solution_seen"] = True  # ADR-0019 item 7: aided
        if pending.get("flags"):
            extra["timing_flags"] = list(pending["flags"])
        if cur.get("undecided"):
            extra["grader_review"] = True
        if pending.get("unanswered"):
            extra["unanswered"] = True
        solution_seen = bool(cur.get(UNDO_AFTER_SOLUTION))
        standard = meta.get("standard")
        target = None if standard is None else round(float(standard) * MINUTE_MS)
        valid = None
        if (
            number == 1
            and correct
            and part is None
            and not pending.get("parts")
            and verdict == "correct"
            and not solution_seen
        ):
            if item.purpose == "sitting" and item.meta is not None:
                valid = sitting_minutes(
                    timing,
                    shown_at=cur.get("shown_at"),
                    submitted_at=int(pending["at"]),
                    untimed=session.untimed,
                    interrupted=bool(cur.get("interrupted") or cur.get("example_opened")),
                    tier=card.tier,
                    target_ms=target,
                )
            else:
                valid = valid_minutes(
                    timing,
                    untimed=session.untimed,
                    example_opened=bool(cur.get("example_opened")),
                    tier=card.tier,
                    target_ms=target,
                )
        capped = None
        if timing.active_ms is not None:
            capped = min(timing.active_ms, cap_ms(target, card.tier))
        # Problems and the new skill's worked example carry the planner's role (the planner
        # reads a served example back as its block's); flashcards and older plans' items none.
        role = item.purpose if item.meta is not None and item.kind != "flashcard" else None
        return Attempt(
            at=int(pending["at"]),
            shown_at=cur.get("shown_at"),
            session_id=session.id,
            presentation_id=str(cur["presentation_id"]),
            card_id=card.id,
            card_rev=card.rev,
            pack_id=None if source == "user" else source,
            card_kind=card.kind,
            skill_id=card.skill_id,
            part=part,
            tier=card.tier,
            seed=card.seed,
            template_id=card.template_id,
            reason_tag=item.tag,
            raw_input=pending.get("raw_input"),
            parsed=pending.get("parsed"),
            verdict=cast(Any, verdict),
            attempt_number=number,
            final=final,
            example_opened=bool(cur.get("example_opened")),
            confidence="unsure" if pending.get("unsure") else "sure",
            guessed=bool(pending.get("guessed")),
            too_easy=bool(pending.get("too_easy")),
            active_ms=timing.active_ms,
            solve_ms=timing.solve_ms,
            entry_ms=timing.entry_ms,
            raw_ms=timing.raw_ms,
            capped_ms=capped,
            pause_count=timing.pause_count,
            longest_pause_ms=timing.longest_pause_ms,
            after_wake=timing.after_wake,
            untimed=session.untimed,
            matched_wrong=pending.get("matched_wrong"),
            app_version=self._app_version,
            extra=extra,
            role=cast(Any, role),
            milestone=meta.get("milestone") if role else None,
            missed=bool(meta.get("missed")) if role else None,
            plan_p=meta.get("p") if role else None,
            ladder=int(meta.get("ladder") or 0) if role else None,
            sitting=meta.get("sitting") if role else None,
            learner_version=meta.get("version") if role else None,
            valid_minutes=valid,
        )

    def _record_try(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        wrong: Mapping[str, Any],
        *,
        part: str | None = None,
    ) -> Attempt:
        """A wrong try that leaves the problem open: committed at once with the session row
        (rule 5). A first try is the problem's observation: the learner takes it now."""
        trying = replace(
            session,
            current=cur,
            draft=None,
            extra={k: val for k, val in session.extra.items() if k != "undo"},
        )
        row = self._attempt_row(trying, plan, item, cur, wrong, card, final=False, part=part)
        stored = self._storage.users.record_answer(GradedAnswer(attempt=row, session=trying))
        if stored.id is not None:
            self._practice.record(stored.id)
        return stored

    def _finalize(
        self, session: SessionState, plan: Plan, *, replan: bool = True
    ) -> tuple[SessionState, Plan, Attempt]:
        """Commit the answer held on screen: the final attempt row and the session row in one
        transaction; then the learner takes it, and (in a daily session of today) the rest of
        the day is planned again. A crash between the two writes is finished on resume."""
        users = self._storage.users
        cur = dict(session.current or {})
        pending = dict(cur.get("pending") or {})
        item = plan.item(str(cur["key"]))
        if item is None or not pending:
            raise QueueError("Nothing to grade.")
        card = self._card(str(cur["card_id"]))
        # Final: the presentation is complete. A worked example (or a problem shown solved in
        # its place) is a final "shown" row, never an observation.
        row = self._attempt_row(session, plan, item, cur, pending, card, final=True)
        undo = {
            "presentation_id": cur["presentation_id"],
            "key": item.key,
            "card_id": cur["card_id"],
            "plan": session.plan,
            "position": session.position,
        }
        result = {
            "answered_at": pending["at"],
            "verdict": pending.get("verdict"),
            "correct": None if item.kind != "problem" else _first_try_success(cur, pending, item),
            "card_id": card.id,
            "skill_id": item.skill_id,
            "active_ms": _presentation_ms(users.attempts(session_id=session.id), cur, pending),
        }
        if item.purpose == "sitting":
            # The sitting clock this problem used up: its counted time (the wall clock plus
            # the typing allowance), or the bare wall clock when that time is unknown.
            counted = row.valid_minutes
            wall = sitting_ms(cur.get("shown_at"), int(pending["at"])) or 0
            result["sitting_ms"] = round(counted * MINUTE_MS) if counted is not None else wall
        marked = plan.updated(replace(item, status="done", result=result))
        closed = {**cur, "pending": None, "closed": True, "answer": pending}
        extra = {**session.extra, "undo": undo}
        if replan:
            extra["replan"] = item.key
        graded = replace(session, plan=marked.to_json(), current=closed, extra=extra)
        stored = users.record_answer(GradedAnswer(attempt=row, session=graded))
        if stored.id is not None:
            self._practice.record(stored.id)
        closed["attempt_id"] = stored.id
        new_plan = self._replan(graded, marked, item.key) if replan else marked
        extra.pop("replan", None)
        if item.kind == "problem" and item.purpose == "new" and result["correct"] and item.skill_id:
            extra["learned"] = [*extra.get("learned", []), item.skill_id]
        saved = users.save_session(
            replace(graded, plan=new_plan.to_json(), current=closed, extra=extra)
        )
        return saved, new_plan, stored

    def _replan(self, session: SessionState, plan: Plan, key: str) -> Plan:
        """After an answer in today's daily session: the rest of the day, planned again from
        the items served today (the planner's ladder, blocks that end at a success, growth
        that stops after two in a row)."""
        if key in plan.replanned:
            return plan
        plan = replace(plan, replanned=(*plan.replanned, key))
        if plan.mode != DAILY or plan.day != self._today().isoformat():
            return plan
        return self._with_plan(plan, self._fresh_plan(plan))

    def _fresh_plan(self, plan: Plan) -> PracticePlan:
        day = date.fromisoformat(plan.day)
        return self._practice.plan_day(day, self._now(), self._practice.served(day))

    def _with_plan(self, plan: Plan, planned: PracticePlan) -> Plan:
        """The plan's pending problems replaced by the planner's; flashcards placed between
        them again (a missed flashcard still at least five items after its miss)."""
        done = [i for i in plan.items if not i.pending]
        pending = [i for i in plan.items if i.pending]
        flash = [i for i in pending if i.kind == "flashcard" and i.anchor is None]
        reshows = [i for i in pending if i.kind == "flashcard" and i.anchor is not None]
        plan, problems = self._problem_items(planned, plan)
        tail = place_flashcards(problems, flash)
        for item in reshows:
            tail = _insert_reshow(done, tail, item)
        info = {**plan.info, "summary": self._summary_info(planned)}
        return replace(plan, items=(*done, *tail), n=len(done) + len(problems), info=info)

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
            session, plan = self._require()
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
            engine = self.engine()
            state = users.flashcard_state(card.id, item.card_ord)
            adapter = engine.adapter_for_card(card.id)
            new_state, event, recall = grade_flashcard(
                state,
                card_id=card.id,
                card_ord=item.card_ord,
                rating=rating,
                at_ms=now,
                adapter=adapter,
                days=self._practice.days(),
                leech_lapses=int(self._setting("leech.flashcard_lapses", 8)),
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
                done = [i for i in marked.items if not i.pending]
                tail = _insert_reshow(done, [i for i in marked.items if i.pending], reshow)
                marked = replace(marked, items=(*done, *tail))
            closed = {**cur, "closed": True, "answer": {"at": now, "rating": rating}}
            graded = replace(
                session,
                plan=marked.to_json(),
                current=closed,
                extra={**session.extra, "undo": undo},
            )
            source_pack = self._storage.packs.card_source(card.id) or "user"
            attempt = Attempt(
                at=now,
                shown_at=cur.get("shown_at"),
                session_id=session.id,
                presentation_id=str(cur["presentation_id"]),
                card_id=card.id,
                card_rev=card.rev,
                pack_id=None if source_pack == "user" else source_pack,
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
        """QUE-15: roll back the last answer (its attempt rows; a flashcard's FSRS state) in
        one transaction and show the problem again. Refused, with a message, once a later
        answer was submitted or the rows changed since. The learner replays the shorter log."""
        with self._locked():
            session, plan = self._require()
            users = self._storage.users
            cur = dict(session.current or {})
            if cur.get("pending"):  # on the verdict screen, not committed yet
                pending = cur["pending"]
                fresh = {
                    **cur,
                    "pending": None,
                    "tries": 0,
                    "parts": None,
                    "last_verdicts": None,
                    "solution_shown": False,
                    "self_grade": False,
                    "undecided": False,
                    "presentation_id": _uid(),
                    "shown_at": self._now(),
                    # ADR-0019 item 7: the solution was on screen after a first try that was
                    # not a clean success, so the re-answer is aided (undo never erases a miss).
                    UNDO_AFTER_SOLUTION: bool(
                        cur.get(UNDO_AFTER_SOLUTION)
                        or cur.get("solution_shown")
                        or cur.get("example_opened")
                        or _missed_first(pending)
                    ),
                }
                restored = replace(session, current=fresh, draft=None)
                last = users.last_attempt()
                if last is not None and last.presentation_id == cur.get("presentation_id"):
                    users.undo_last_answer(session=restored)  # voids its "Not quite" tries
                else:
                    users.save_session(restored)
                return self._turn(
                    users.session(_id(session)) or restored, message="Undone. The problem is back."
                )
            snap = session.extra.get("undo")
            if not snap:
                answered = any(i.status == "done" for i in plan.items)
                message = (
                    "Undo is only available until the next answer is submitted."
                    if answered
                    else "There is no answer to undo."
                )
                return self._turn(session, message=message)
            last = users.last_attempt()
            if last is None or last.presentation_id != snap["presentation_id"]:
                return self._turn(
                    session, message="Undo is only available until the next answer is submitted."
                )
            old = Plan.from_json(snap["plan"])
            item = old.item(str(snap["key"]))
            if item is None:
                return self._turn(session, message="There is no answer to undo.")
            extra = {k: val for k, val in session.extra.items() if k not in ("undo", "replan")}
            undone = plan.item(item.key)
            if undone is not None and item.skill_id in extra.get("learned", []):
                extra["learned"] = [k for k in extra.get("learned", []) if k != item.skill_id]
            undone_card = self._card(str(snap["card_id"]))
            # ADR-0019 item 7, from the presentation's rows (the session has moved on to the
            # next item): a first try that was not a clean success brings the problem back
            # aided, so undo never turns a miss into a fresh first try.
            group = [
                a
                for a in users.attempts(session_id=session.id)
                if a.presentation_id == snap["presentation_id"]
            ]
            solution_seen = any(_row_missed(a) for a in group)
            current = {
                "key": item.key,
                "card_id": snap["card_id"],
                "rev": undone_card.rev,
                "presentation_id": _uid(),
                "shown_at": self._now(),
                "tries": 0,
                "example_opened": False,
                "pending": None,
                "closed": False,
                UNDO_AFTER_SOLUTION: solution_seen and item.kind == "problem",
            }
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
                    session, message="That answer can't be undone exactly any more, so it stays."
                )
            return self._turn(
                users.session(_id(session)) or restored, message="Undone. The problem is back."
            )

    def flag(self, kind: str, note: str | None = None) -> v.FlagResult:
        """too_easy (logged with the answer), dispute ("I was right": the attempt doesn't
        count, logged), report (hide the card at once, the attempt doesn't count), flag (a note
        for later), suspend (never serve the card)."""
        with self._locked():
            session, plan = self._require()
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
                return self._void_answer(session, plan, item, cur, card, reason, note)
            if kind in ("flag", "suspend"):
                mark = users.card_mark(card.id) or CardMark(card_id=card.id)
                if kind == "flag":
                    users.set_card_mark(replace(mark, flagged=True, flag_note=note))
                    return v.FlagResult(ok=True, message="Flagged for later.")
                users.set_card_mark(replace(mark, suspended=True))
                if not cur.get("pending") and not cur.get("closed") and not cur.get("tries"):
                    self._repick(session, plan)
                return v.FlagResult(ok=True, message="Suspended: this problem won't come back.")
            raise QueueError(f"unknown flag {kind!r}")

    def _repick(self, session: SessionState, plan: Plan) -> None:
        """Another item in place of the one on screen (its card was reported or suspended
        before it was answered): the planner leaves that card out now."""
        self._advance(replace(session, current=None), plan)

    def _void_answer(
        self,
        session: SessionState,
        plan: Plan,
        item: PlanItem,
        cur: dict[str, Any],
        card: Card,
        reason: VoidReason,
        note: str | None,
    ) -> v.FlagResult:
        users = self._storage.users
        message = (
            "Logged. This attempt won't count."
            if reason == "dispute"
            else "Reported and hidden. This attempt won't count."
        )
        pending = cur.get("pending")
        if pending:  # never committed: log it with its tries, voided, with the record
            row = self._attempt_row(session, plan, item, cur, pending, card, final=True)
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

            def write(u: Any) -> None:
                stored = u.record_answer(GradedAnswer(attempt=row))
                u.void_attempts([*tries, stored.id], reason=reason, note=note, session=after)
                self._log_flag(u, reason, card, stored.id, pending.get("raw_input"), note)

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
            marked = plan.updated(replace(item, result=res))
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
                    group = [
                        a.id
                        for a in u.attempts(session_id=session.id)
                        if a.presentation_id == last.presentation_id and a.id is not None
                    ]
                    u.void_attempts(group, reason=reason, note=note, session=after)
                self._log_flag(u, reason, card, last.id, last.raw_input, note)

            users.atomic(void_and_log)
            return v.FlagResult(ok=True, message=message, attempt_counts=False)
        if reason == "report":  # before answering: hide it and serve another item
            users.add_report(Report(card_id=card.id, card_rev=card.rev, reason=note or ""))
            if not cur.get("closed"):
                tries = [
                    a.id
                    for a in users.attempts(session_id=session.id)
                    if a.presentation_id == cur["presentation_id"] and a.id is not None
                ]
                if tries:
                    users.void_attempts(tries, reason="report", note=note)
                self._repick(session, plan)
            return v.FlagResult(ok=True, message="Reported and hidden.", attempt_counts=False)
        return v.FlagResult(ok=False, message="There is no answer to dispute.")

    def _log_flag(
        self,
        users: Any,
        reason: VoidReason,
        card: Card,
        attempt_id: int | None,
        raw: str | None,
        note: str | None,
    ) -> None:
        if reason == "dispute":
            users.add_dispute(Dispute(attempt_id=_int(attempt_id), raw_input=raw, note=note))
        else:
            users.add_report(
                Report(card_id=card.id, card_rev=card.rev, attempt_id=attempt_id, reason=note or "")
            )

    # ================================================================ practice tests

    def _test_exam(self, req: v.StartRequest, day: date) -> Exam:
        """The exam a practice test is for; refused outside its final 21 days."""
        exam = next((e for e in self._storage.users.exams() if e.id == req.exam_id), None)
        if exam is None:
            raise QueueError("Pick an exam for the practice test.")
        left = (self._practice.days().day_of(exam.at) - day).days
        if not 0 <= left <= PRACTICE_TEST_WINDOW_DAYS:
            raise QueueError("Practice tests open in the final 21 days before an exam.")
        return exam

    def _test_plan(self, req: v.StartRequest, day: date) -> Plan:
        """A practice test (ENG-8, wave 2 without triage): N problems at tier 3 (the
        request's count, else the exam's problem count, else 10) from the exam's scope
        sections, none served in the last 7 days, spread over the scope's skills (every skill
        once before any twice); optionally timed at the sum of their standard times; graded at
        the end. Self-graded problems are left out: nothing is graded until the test ends."""
        users = self._storage.users
        exam = self._test_exam(req, day)
        catalog = self._practice.catalog()
        unavailable = self._practice.unavailable()
        fresh_since = self._now() - PRACTICE_TEST_FRESH_DAYS * DAY_MS
        recent = {a.card_id for a in users.attempts(since=fresh_since)}
        pools: list[tuple[str, str, list[ProblemSpec]]] = []  # (course, skill, problems)
        for course_id, entry in catalog.courses.items():
            if exam.course_id is not None and exam.course_id != course_id:
                continue
            for skill in entry.course.skills:
                if skill.background or not _in_scope(skill.deck, exam.sections):
                    continue
                problems = [
                    p
                    for p in skill.pool
                    if p.tier == PRACTICE_TEST_TIER
                    and p.part is None
                    and p.card_id not in unavailable
                    and p.card_id not in recent
                    and all(s.spec.answer_type != "self" for s in specs_for(self._card(p.card_id)))
                ]
                if problems:
                    pools.append(
                        (course_id, skill.skill_id, sorted(problems, key=lambda p: p.problem_id))
                    )
        count = max(1, req.count or exam.problems or PRACTICE_TEST_DEFAULT)
        chosen: list[tuple[str, ProblemSpec]] = []
        taken: set[str] = set()
        while len(chosen) < count:
            added = False
            for course_id, _, problems in pools:
                if len(chosen) >= count:
                    break
                found = next((p for p in problems if p.card_id not in taken), None)
                if found is not None:
                    chosen.append((course_id, found))
                    taken.add(found.card_id)
                    added = True
            if not added:
                break
        version = self._practice.params().version
        plan = Plan(day=day.isoformat(), mode="practice-test")
        items: list[PlanItem] = []
        for course_id, problem in chosen:
            plan, key = plan.next_key("pt")
            tag, label, variant = ROLE_REASONS["practice-test"]
            items.append(
                PlanItem(
                    key=key,
                    kind="problem",
                    skill_id=problem.main_skill,
                    course_id=course_id,
                    section_id=catalog.skill_decks.get(problem.main_skill),
                    order=REVIEW,
                    rank=float(len(items)),
                    tag=tag,
                    label=label,
                    why=why(variant),
                    purpose="practice-test",
                    tier_hint=float(problem.tier),
                    est_ms=round(problem.standard_minutes * MINUTE_MS),
                    card_id=problem.card_id,
                    meta={
                        "problem": problem.problem_id,
                        "tier": problem.tier,
                        "standard": problem.standard_minutes,
                        "minutes": problem.standard_minutes,
                        "priority": 1,
                        "reason": "practice-test",
                        "version": version,
                    },
                )
            )
        limit = None
        if req.timed:
            limit = math.ceil(sum(p.standard_minutes for _, p in chosen) * MINUTE_MS)
        return replace(
            plan,
            n=len(items),
            items=tuple(items),
            info={
                "engine": ENGINE,
                "exam_id": exam.id,
                "timed": req.timed,
                "limit_ms": limit,
                "unanswered": "skip",
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
                "matched_wrong": checked.matched_index,
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
        res = {"answer": answer, "graded": False, "presentation_id": cur.get("presentation_id")}
        res["shown_at"] = cur.get("shown_at")
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
        self._advance(session, plan)
        return v.AttemptResult(
            item_key=item.key,
            outcome="recorded",
            message="Saved. Results come at the end.",
            first_try_counted=True,
        )

    def _grade_test(
        self, session: SessionState, plan: Plan
    ) -> tuple[SessionState, Plan, v.TestResult]:
        """Grade a practice test when it ends: each answered problem through the commit path
        (its own transaction, with the session row marking it graded), role practice-test. A
        problem never answered scores zero in the test but is no evidence about the student
        (C5): it is logged as unanswered, which the learner skips."""
        catalog = self._practice.catalog()
        now = self._now()
        users = self._storage.users
        for item in list(plan.items):
            res = dict(item.result or {})
            if res.get("graded") or item.card_id is None or item.kind != "problem":
                continue
            given = res.get("answer")
            unanswered = given is None
            answer: dict[str, Any] = (
                {"at": now, "correct": False, "unanswered": True, "verdict": "gave-up"}
                if given is None
                else dict(given)
            )
            card = self._card(item.card_id)
            cur = {
                "card_id": item.card_id,
                "presentation_id": res.get("presentation_id") or _uid(),
                "shown_at": res.get("shown_at"),
                "key": item.key,
            }
            res.update(answer=answer, graded=True)
            marked = plan.updated(replace(item, status="done", result=res))
            graded = replace(session, plan=marked.to_json(), current=None)
            row = self._attempt_row(graded, plan, item, cur, answer, card, final=True)
            stored = users.record_answer(GradedAnswer(attempt=row, session=graded))
            if stored.id is not None:
                self._practice.record(stored.id)
            res.update(
                attempt_id=stored.id,
                correct=None if unanswered else bool(answer.get("correct")),
            )
            plan = marked.updated(replace(item, status="done", result=res))
            session = users.save_session(replace(graded, plan=plan.to_json()))
        lines = []
        for item in plan.items:
            res = item.result or {}
            shown = res.get("answer")
            answered = shown is not None and not shown.get("unanswered")
            lines.append(
                v.TestLine(
                    item_key=item.key,
                    card_id=item.card_id,
                    skill_name=catalog.name(item.skill_id or ""),
                    answered=answered,
                    correct=bool(answered and shown and shown.get("correct")),
                    your_answer=shown.get("raw_input") if answered and shown else None,
                    rating=None,
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
            unanswered="skip",
            limit_ms=plan.info.get("limit_ms"),
        )
        return session, plan, result

    # ================================================================ summary

    def _summary(self, session: SessionState, plan: Plan, test: v.TestResult | None) -> v.Summary:
        catalog = self._practice.catalog()
        done = [i for i in plan.items if i.status == "done" and i.kind == "problem"]
        counted = [i for i in done if (i.result or {}).get("correct") is not None]
        misses = [i for i in counted if not (i.result or {}).get("correct")]
        learned = tuple(dict.fromkeys(catalog.name(k) for k in session.extra.get("learned", [])))
        today = self._today()
        tomorrow = today + timedelta(days=1)
        planned = self._tomorrow(today)
        forecast_items = self._problem_items(planned, Plan(day=tomorrow.isoformat()))[1]
        forecast = v.Forecast(
            day=tomorrow.isoformat(),
            problems=len(forecast_items),
            minutes=_minutes(forecast_items),
            courses=self._course_lines(forecast_items),
        )
        rest = self._practice.plan_day(today, self._now(), self._practice.served(today))
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
                    skill_name=catalog.name(i.skill_id or ""),
                    tag=i.tag,
                    label=i.label,
                )
                for i in misses
            ),
            learned=learned,
            flashcards=sum(1 for i in plan.items if i.kind == "flashcard" and i.status == "done"),
            forecast=forecast,
            extra_practice_available=bool(self._extra_items(today, 1, planned)),
            practice_tests=tuple(e for e in self._exam_lines(today) if e.practice_test),
            test=test,
            # Problems today's plan still holds (the session ended before the plan did).
            ready_today=sum(1 for p in rest.items if p.item.problem is not None),
        )


# ---------------------------------------------------------------- helpers


def valid_minutes(
    timing: TimingFacts,
    *,
    untimed: bool,
    example_opened: bool,
    tier: int,
    target_ms: int | None = None,
) -> float | None:
    """A correct first try's valid solving time (TIME-4/5): solve time plus the typing
    allowance, capped at four times the target (the problem's standard time T*; the tier
    floor without one), 3 to 30 minutes; None when the timing is not valid (untimed, a pause
    over 2 minutes, the first answer after a wake, an example opened, no solve time)."""
    if excluded_from_baseline(timing, untimed=untimed, hints_used=0, example_opened=example_opened):
        return None
    speed = speed_time_ms(timing.solve_ms, timing.expected_chars, target_ms=target_ms, tier=tier)
    return None if not speed else speed / MINUTE_MS


def sitting_ms(shown_at: int | None, submitted_at: int) -> int | None:
    """A sitting problem's clock: wall-clock time from the problem shown to the submit."""
    return None if shown_at is None else max(0, submitted_at - shown_at)


def sitting_minutes(
    timing: TimingFacts,
    *,
    shown_at: int | None,
    submitted_at: int,
    untimed: bool,
    interrupted: bool,
    tier: int,
    target_ms: int | None = None,
) -> float | None:
    """A certification sitting's valid solving time (coordinator rule, wave2-impl-notes.md):
    the clock never stops, as in an exam, so a defocus or a pause counts. It is the wall-clock
    time from the problem shown to the submit plus the typing allowance (TIME-4's
    `speed_time_ms`), with the usual cap (TIME-5). The time is unknown (None, which makes the
    sitting void) after a pause over 2 minutes, for the first answer after the Mac wakes, in an
    untimed session (TIME-6), or when the app was closed and opened again on the problem
    (`interrupted`)."""
    wall = sitting_ms(shown_at, submitted_at)
    if wall is None or untimed or interrupted or timing.after_wake:
        return None
    if (timing.longest_pause_ms or 0) > BASELINE_LONG_PAUSE_MS:
        return None
    speed = speed_time_ms(wall, timing.expected_chars, target_ms=target_ms, tier=tier)
    return None if speed is None else speed / MINUTE_MS


def _plan_item(key: str, planned: PlannedItem, catalog: Catalog, version: str) -> PlanItem:
    """A planner item as a session plan item (wave2-integration.md section 4)."""
    it = planned.item
    problem = it.problem
    role = it.role
    reason = it.reason or ""
    tag, label, variant = LADDER_REASONS.get(reason) or ROLE_REASONS.get(
        role, ("review", TAG_LABELS["review"], "review")
    )
    if problem is None:  # the new skill's worked example
        tag, label, variant = "new-skill", "Worked example", "new-skill"
    order = CHECK if role == "check" else LEARNING if role == "new" else REVIEW
    return PlanItem(
        key=key,
        kind="problem" if problem is not None else "example",
        skill_id=it.skill_id,
        course_id=planned.course_id,
        section_id=catalog.skill_decks.get(it.skill_id),
        order=order,
        rank=float(it.priority),
        tag=tag,
        label=label,
        why=why(variant),
        purpose=role,
        tier_hint=float(it.tier or (problem.tier if problem else 1)),
        est_ms=round(it.expected_minutes * MINUTE_MS),
        block=f"blk:{it.skill_id}" if it.block else None,
        card_id=problem.card_id if problem is not None else it.example_card,
        meta={
            "problem": None if problem is None else problem.problem_id,
            "standard": None if problem is None else problem.standard_minutes,
            "milestone": it.milestone,
            "missed": it.missed,
            "p": it.p,
            "ladder": int(getattr(it, "ladder", 0) or 0),
            "sitting": getattr(it, "sitting", None),
            "time_limit": getattr(it, "time_limit", None),
            "priority": it.priority,
            "reason": reason,
            "tier": it.tier,
            "block": it.block,
            "minutes": it.expected_minutes,
            "version": version,
        },
    )


def _flashcard_item(card_id: str, card_ord: int, skill: str | None, catalog: Catalog) -> PlanItem:
    return PlanItem(
        key=f"fc:{card_id}:{card_ord}",
        kind="flashcard",
        skill_id=skill,
        course_id=catalog.course_of(skill or "") or "",
        section_id=catalog.skill_decks.get(skill or ""),
        order=FLASHCARD,
        tag="review",
        label="Flashcard",
        why=why("flashcard"),
        purpose="review",
        tier_hint=1.0,
        est_ms=FLASHCARD_MS,
        card_id=card_id,
        card_ord=card_ord,
    )


def _insert_reshow(
    done: Sequence[PlanItem], tail: Sequence[PlanItem], item: PlanItem
) -> list[PlanItem]:
    """I5: a missed flashcard at least `gap` items after its miss."""
    keys = [i.key for i in done if i.status != "skipped"]
    after = len(keys) - 1 - keys.index(item.anchor) if item.anchor in keys else 0
    out = list(tail)
    out.insert(min(max(0, item.gap - after), len(out)), item)
    return out


def _aside(plan: Plan) -> list[str]:
    """The skill ids today's plan has set aside."""
    return [str(k) for k in (plan.info.get("summary") or {}).get("set_aside_ids", ())]


def _parts_facts(outcomes: Sequence[PartOutcome]) -> tuple[bool, int, bool]:
    """A multi-part problem's final answer: (right when every part is, the most tries any
    part took, given up when a part was and not every part is right)."""
    correct = bool(outcomes) and all(o.correct for o in outcomes)
    number = max((o.attempts for o in outcomes), default=1)
    return correct, number, any(o.gave_up for o in outcomes) and not correct


def _missed_first(answer: Mapping[str, Any] | None) -> bool:
    """Whether an answer's first try was not a clean success: wrong, given up, right only on
    a later try, or a part so. Its solution has been on screen, so undo brings the problem
    back aided (ADR-0019 item 7); otherwise undo would erase a miss."""
    if not isinstance(answer, Mapping):
        return False
    if not answer.get("correct") or answer.get("gave_up"):
        return True
    if int(answer.get("attempt_number", 1)) > 1:
        return True
    return any(
        not p.get("correct") or p.get("gave_up") or int(p.get("attempts", 1)) > 1
        for p in answer.get("parts") or ()
    )


def _row_missed(attempt: Attempt) -> bool:
    """A problem row of an answer whose first try was not a clean success (see
    `_missed_first`): a "Not quite" try, a final answer not right on its first try (self-graded
    ones included: their solution came first), aided, or a part so."""
    if attempt.card_kind != "problem":
        return False
    if not attempt.final or attempt.verdict != "correct" or attempt.attempt_number > 1:
        return True
    if attempt.example_opened or attempt.extra.get("solution_seen"):
        return True
    return _missed_first({"correct": True, "parts": attempt.extra.get("parts") or ()})


def _first_try_success(cur: Mapping[str, Any], pending: Mapping[str, Any], item: PlanItem) -> bool:
    """Whether the item's problem was right on its first try, unaided (what counts)."""
    if cur.get(UNDO_AFTER_SOLUTION) or cur.get("example_opened"):
        return False
    parts = pending.get("parts")
    problem = (item.meta or {}).get("problem")
    if parts:
        label = str(problem).split("#", 1)[1] if problem and "#" in str(problem) else None
        chosen = [p for p in parts if label is None or p.get("label") == label]
        return bool(chosen) and all(
            p.get("correct") and int(p.get("attempts", 1)) == 1 and not p.get("gave_up")
            for p in chosen
        )
    return (
        int(pending.get("attempt_number", 1)) == 1
        and bool(pending.get("correct"))
        and not pending.get("gave_up")
    )


def _presentation_ms(
    attempts: Sequence[Attempt], cur: Mapping[str, Any], pending: Mapping[str, Any]
) -> int:
    """Active time on the presentation: its tries so far and the final answer."""
    presentation = cur.get("presentation_id")
    tries = sum(a.active_ms or 0 for a in attempts if a.presentation_id == presentation)
    final = int((pending.get("timing") or {}).get("active_ms") or 0)
    return max(tries, final)


def _in_scope(deck: str, sections: Sequence[str]) -> bool:
    return not sections or any(deck == s or deck.startswith(s + "::") for s in sections)


def _verdict_json(p: Any) -> dict[str, Any]:
    return {
        "part": p.part,
        "status": p.status,
        "read_as": p.read_as,
        "message": p.message,
        "feedback": p.feedback,
        "wrong_step": p.wrong_step,
    }


def _quiet(verdict: Mapping[str, Any]) -> dict[str, Any]:
    """A wrong try's verdict as the student sees it while the problem is open: the verdict
    and the answer as read, no checker message, no known-wrong-answer feedback, no step
    (coordinator rule, design v1.3 4.6: they come with the solution)."""
    out = dict(verdict)
    if out.get("status") != Status.CORRECT:
        out.update(message="", feedback=None, wrong_step=None)
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
    """A multi-part problem is "correct" only when every part is."""
    parts = pending.get("parts")
    if parts:
        return "correct" if all(p.get("correct") for p in parts) else "incorrect"
    return "correct" if pending.get("correct") else "incorrect"


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


def _minutes(items: Sequence[PlanItem]) -> int:
    return math.ceil(sum(i.est_ms for i in items if i.pending) / MINUTE_MS)


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


__all__ = ["QueueError", "StudyService", "valid_minutes"]
