"""Everything one plan reads, gathered from storage and the engine in one place.

`gather` is the only storage-bound part of planning: triage and the planner are pure
functions over a Snapshot, so tests and simulations can build one by hand.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from core.engine import (
    Booster,
    Catalog,
    DueSkill,
    Engine,
    EngineSettings,
    FsrsAdapter,
    StudyDays,
    due_day,
    scheduled_load,
    skill_retention,
)
from core.engine.diagnosis import Diagnosis, queue_order
from core.model import (
    CardRef,
    CourseGoal,
    FlashcardState,
    PendingCheck,
    SectionStateName,
    SkillState,
)
from core.queue.cloze import ords as cloze_ords
from core.queue.config import DAY_MS, RECENT_FAIL_DAYS, TIME_HISTORY_DAYS
from core.queue.daylog import DayEntry, Vacation, read_log, read_vacation
from core.queue.estimate import TimeTable
from core.queue.share import carry_over
from core.storage import Storage

DAILY_MODES = ("daily", "lighter")
PROBLEM_KINDS = ("problem", "find-error", "method")


@dataclass(frozen=True, slots=True, kw_only=True)
class QueueSettings:
    n: int = 20  # today's count
    base_n: int = 20
    flashcards: int = 50
    new_flashcards: int = 20  # I5: new flashcards a day (inside the flashcard limit)
    minutes_cap: int | None = None
    new_per_day: int = 4
    policy: str = "recommended"
    stretch_fraction: float = 0.10
    elite: bool = True
    checkup_every_weeks: int | None = 3
    min_per_course: int = 3
    min_fraction: float = 0.10
    correct_in_a_row: int = 3
    max_learning_problems: int = 8
    attempts_per_problem: int = 2
    hints: bool = True
    break_minutes: int | None = 50
    untimed_default: bool = False

    @classmethod
    def from_values(cls, values: Mapping[str, Any], day: date) -> QueueSettings:
        engine = EngineSettings.from_settings(values)

        def get(key: str, default: Any) -> Any:
            return values.get(key, default)

        # Easy Days shape future load through the load balancer, as in Anki (ADR-0014);
        # they no longer cut the day's count, which only built a backlog.
        base = engine.daily_problems
        n = base
        return cls(
            n=n,
            base_n=base,
            flashcards=int(get("daily.flashcards", 50)),
            new_flashcards=int(get("daily.new_flashcards", 20)),
            minutes_cap=get("daily.minutes_cap", None),
            new_per_day=engine.new_skills_per_day,
            policy=str(get("queue.triage_policy", "recommended")),
            stretch_fraction=engine.stretch_fraction,
            elite=engine.elite,
            checkup_every_weeks=engine.checkup_every_weeks,
            min_per_course=int(get("queue.min_per_course_problems", 3)),
            min_fraction=float(get("queue.min_per_course_fraction", 0.10)),
            correct_in_a_row=engine.correct_in_a_row,
            max_learning_problems=engine.max_learning_problems,
            attempts_per_problem=int(get("study.attempts_per_problem", 2)),
            hints=bool(get("study.hints", True)),
            break_minutes=get("ui.break_reminder_minutes", 50),
            untimed_default=bool(get("session.untimed_default", False)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExamWindow:
    exam_id: int | None
    name: str
    day: date
    days_left: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Snapshot:
    day: date
    now_ms: int
    days: StudyDays
    settings: QueueSettings
    catalog: Catalog
    adapter: FsrsAdapter
    courses: Mapping[str, str]  # active courses (any section not Off): id -> title
    section_states: Mapping[str, SectionStateName]
    goals: Mapping[str, CourseGoal]
    states: Mapping[str, SkillState]
    due: Sequence[DueSkill] = ()
    boosters: Sequence[Booster] = ()
    exam_scope: Mapping[str, ExamWindow] = field(default_factory=dict)  # skill -> nearest
    next_exam_days: Mapping[str, int] = field(default_factory=dict)  # course -> days left
    checks: Sequence[PendingCheck] = ()
    check_course: Mapping[int, str] = field(default_factory=dict)
    check_missed: Mapping[int, str] = field(default_factory=dict)  # check id -> missed skill
    check_reasons: Mapping[int, str] = field(default_factory=dict)  # "Why is this here?"
    redo: Mapping[str, tuple[str, bool]] = field(default_factory=dict)  # card -> (skill, sure)
    hidden_cards: frozenset[str] = frozenset()
    recent_fails: frozenset[str] = frozenset()
    due_days: Mapping[str, date | None] = field(default_factory=dict)
    last_checkup: date | None = None
    times: TimeTable = field(default_factory=TimeTable)
    projected_load: Mapping[date, int] = field(default_factory=dict)
    introduced_today: int = 0
    done_today: Mapping[str, int] = field(default_factory=dict)  # course -> daily problems
    carry: Mapping[str, int] = field(default_factory=dict)
    flashcards_due: Sequence[tuple[str, int, str | None]] = ()  # (card, ord, skill)
    flashcards_new: frozenset[tuple[str, int]] = frozenset()  # those never reviewed
    flashcards_done_today: int = 0  # I5: flashcard reviews already done today ...
    new_flashcards_done_today: int = 0  # ... and new flashcards among them
    flashcard_leeches: int = 0  # I5: leech flashcards, not served until rewritten
    vacation: Vacation | None = None
    log: Mapping[date, DayEntry] = field(default_factory=dict)

    def course_of(self, skill_id: str | None) -> str | None:
        return None if skill_id is None else self.catalog.course_of(skill_id)

    def section_of(self, skill_id: str | None) -> str | None:
        skill = None if skill_id is None else self.catalog.skills.get(skill_id)
        return None if skill is None else skill.section_id

    def active_skill(self, skill_id: str) -> bool:
        section = self.section_of(skill_id)
        if section is None:
            return skill_id in self.catalog.skills
        return self.section_states.get(section, "off") != "off"

    def skill_name(self, skill_id: str | None) -> str:
        skill = None if skill_id is None else self.catalog.skills.get(skill_id)
        return skill.name if skill is not None else (skill_id or "")


def gather(
    storage: Storage,
    engine: Engine,
    *,
    day: date | None = None,
    for_mode: str = "daily",
) -> Snapshot:
    """Read everything a plan for `day` (default today) needs."""
    users, packs = storage.users, storage.packs
    days = engine.days()
    now = storage.db.clock.now_ms()
    today = days.day_of(now)
    day = day or today
    values = users.settings()
    settings = QueueSettings.from_values(values, day)
    catalog = engine.catalog()
    adapter = engine.adapter()
    goals = engine.goals()
    sections = users.section_states()
    section_states: dict[str, SectionStateName] = {k: v.state for k, v in sections.items()}
    course_titles = {c.id: c.title for c in packs.courses()}
    active_courses: dict[str, str] = {}
    for section_id, state in section_states.items():
        course = catalog.course_of_section.get(section_id)
        if state != "off" and course is not None:
            active_courses[course] = course_titles.get(course, course)
    states = users.skill_states()

    def retention(skill_id: str) -> float:
        return skill_retention(skill_id, day, catalog, goals)

    due = engine.due_skills(day)
    boosters = engine.booster_plan(day).due_on(day)

    # Exams: in-scope skills inside the 21-day window, and each course's next exam.
    scope: dict[str, ExamWindow] = {}
    next_exam: dict[str, int] = {}
    for exam in sorted(users.exams(), key=lambda e: e.at):
        exam_day = days.day_of(exam.at)
        left = (exam_day - day).days
        if left < 0:
            continue
        skills = (
            catalog.skills_in_sections(exam.sections)
            if exam.sections
            else catalog.skills_of_course(exam.course_id or "")
        )
        courses = {exam.course_id} if exam.course_id else {catalog.course_of(k) for k in skills}
        for course in courses:
            if course is not None and course not in next_exam:
                next_exam[course] = left
        if left <= 21:
            window = ExamWindow(exam_id=exam.id, name=exam.name, day=exam_day, days_left=left)
            for k in skills:
                scope.setdefault(k, window)

    # Checks made by the diagnosis flow (ADR-0008), in its serving order, with the course
    # of the miss that asked for them; diagnostic sets arrive as "diagnostic" checks.
    checks = queue_order(
        c
        for c in users.pending_checks("pending")
        if c.not_before_at is None or c.not_before_at <= now
    )
    reason_of = Diagnosis(storage).reason
    check_reasons = {c.id: reason_of(c) for c in checks if c.id is not None}
    check_course: dict[int, str] = {}
    check_missed: dict[int, str] = {}
    for check in checks:
        if check.id is None:
            continue
        missed = users.attempt(check.attempt_id) if check.attempt_id is not None else None
        source = missed.skill_id if missed is not None and missed.skill_id else check.skill_id
        check_missed[check.id] = source
        course = catalog.course_of(source) or catalog.course_of(check.skill_id)
        if course is not None:
            check_course[check.id] = course

    marks = users.card_marks()
    hidden = frozenset(k for k, m in marks.items() if m.hidden or m.suspended)
    tomorrow_start = days.start(day + timedelta(days=1))
    redo: dict[str, tuple[str, bool]] = {}
    for card_id, cu in users.card_users().items():
        if cu.redo_due_at is None or cu.redo_due_at >= tomorrow_start or card_id in hidden:
            continue
        card = packs.card(card_id)
        if card is not None and card.skill_id is not None and not card.retired:
            redo[card_id] = (card.skill_id, cu.redo_guaranteed)

    history = users.attempts(since=now - TIME_HISTORY_DAYS * DAY_MS)
    fails = frozenset(
        a.skill_id
        for a in history
        if a.final and a.rating == 1 and a.skill_id and a.at >= now - RECENT_FAIL_DAYS * DAY_MS
    )
    checkups = [
        days.day_of(a.at) for a in history if a.final and a.extra.get("purpose") == "checkup"
    ]
    adapter_of = engine.skill_adapters()  # each skill's own parameter set (decision 6)
    due_days = {k: due_day(s, retention(k), adapter_of(k), days) for k, s in states.items()}
    load = scheduled_load(
        [s for k, s in states.items() if catalog.course_of(k) in active_courses],
        day,
        7,
        retention_of=retention,
        adapter=adapter,
        days=days,
        adapter_of=adapter_of,
    )
    start, end = days.bounds(day)
    introduced_today = sum(
        1 for s in states.values() if s.introduced_at is not None and start <= s.introduced_at < end
    )

    def daily_done(lo: int, hi: int) -> Counter[str]:
        out: Counter[str] = Counter()
        for a in history:
            if (
                lo <= a.at < hi
                and a.final
                and a.card_kind in PROBLEM_KINDS
                and a.extra.get("queue_mode") in DAILY_MODES
            ):
                out[catalog.course_of(a.skill_id or "") or ""] += 1
        return out

    done_today = daily_done(start, end)
    log = read_log(users)
    carry: dict[str, int] = {}
    yesterday = day - timedelta(days=1)
    if for_mode in DAILY_MODES and yesterday in log:
        y_start, y_end = days.bounds(yesterday)
        done_yesterday = daily_done(y_start, y_end)
        if sum(done_yesterday.values()) > 0:  # stopped early (a missed day carries nothing)
            for course, quota in log[yesterday].quotas.items():
                carry[course] = carry_over(quota, done_yesterday.get(course, 0))

    flashcards, new_cards, leeches = _flashcards(
        storage, states, hidden, catalog, section_states, tomorrow_start, days.start(day)
    )
    flash_today = [
        a
        for a in history
        if start <= a.at < end and a.final and a.card_kind in ("flashcard", "cloze")
    ]
    return Snapshot(
        day=day,
        now_ms=now,
        days=days,
        settings=settings,
        catalog=catalog,
        adapter=adapter,
        courses=active_courses,
        section_states=section_states,
        goals=goals,
        states=states,
        due=due,
        boosters=boosters,
        exam_scope=scope,
        next_exam_days=next_exam,
        checks=checks,
        check_course=check_course,
        check_missed=check_missed,
        check_reasons=check_reasons,
        redo=redo,
        hidden_cards=hidden,
        recent_fails=fails,
        due_days=due_days,
        last_checkup=max(checkups) if checkups else None,
        times=TimeTable.from_attempts(history),
        projected_load=load,
        introduced_today=introduced_today,
        done_today=dict(done_today),
        carry=carry,
        flashcards_due=flashcards,
        flashcards_new=new_cards,
        flashcards_done_today=len(flash_today),
        new_flashcards_done_today=sum(1 for a in flash_today if a.predicted_recall is None),
        flashcard_leeches=leeches,
        vacation=read_vacation(users),
        log=log,
    )


def _flashcards(
    storage: Storage,
    states: Mapping[str, SkillState],
    hidden: frozenset[str],
    catalog: Catalog,
    section_states: Mapping[str, SectionStateName],
    tomorrow_start: int,
    today_start: int,
) -> tuple[list[tuple[str, int, str | None]], frozenset[tuple[str, int]], int]:
    """Due flashcards, then new ones whose skill has been introduced (QUE-2); also which of
    them are new and how many leeches wait for a rewrite. A cloze card is one item per blank
    number, like Anki (ord = number - 1). Like Anki's "bury new siblings", a cloze card
    brings at most one new blank a day, and none on a day another of its blanks is due or
    was reviewed, so one blank's answer never gives away the next. Cards in an Off section
    (their skill's or their own deck's) and leeches (I5, Anki suspends them) are not served."""
    refs: dict[str, CardRef] = {
        r.id: r for r in storage.packs.card_refs() if r.kind in ("flashcard", "cloze")
    }

    def active(ref: CardRef) -> bool:
        if ref.id in hidden or ref.status != "active":
            return False
        skill = catalog.skills.get(ref.skill_id or "")
        sections = {ref.section_id, skill.section_id if skill is not None else None} - {None}
        return all(section_states.get(str(k), "off") != "off" for k in sections)

    rows = storage.users.flashcard_states()
    seen: dict[tuple[str, int], FlashcardState] = {(f.card_id, f.ord): f for f in rows}
    leeches = sum(1 for f in seen.values() if f.leech and f.card_id in refs)
    due = sorted(
        (f.due_at or 0, f.card_id, f.ord)
        for f in seen.values()
        if f.card_id in refs
        and not f.leech
        and active(refs[f.card_id])
        and (f.due_at or 0) < tomorrow_start
    )
    out = [(card, ord_, refs[card].skill_id) for _, card, ord_ in due]
    new: set[tuple[str, int]] = set()
    busy = {card for _, card, _ in due} | {
        f.card_id for f in rows if (f.last_review_at or 0) >= today_start
    }
    for ref in refs.values():
        if not active(ref):
            continue
        state = states.get(ref.skill_id or "")
        if not (ref.skill_id is None or (state is not None and state.introduced_at is not None)):
            continue
        if ref.kind == "cloze":
            if ref.id in busy:
                continue
            card = storage.packs.card(ref.id)
            blanks = [
                o for o in cloze_ords(card.text_md if card else None) if (ref.id, o) not in seen
            ]
            if blanks:
                out.append((ref.id, blanks[0], ref.skill_id))
                new.add((ref.id, blanks[0]))
        elif (ref.id, 0) not in seen:
            out.append((ref.id, 0, ref.skill_id))
            new.add((ref.id, 0))
    return out, frozenset(new), leeches
