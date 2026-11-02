"""UserStore: the repository over one profile's user.db that the engine and queue call.

Storage stores and retrieves; it never computes FSRS, Elo or Levels. Every write is
one transaction on the single writer thread. A graded answer (record_answer) writes the
attempt, every state row it changes, its review events, partial credits and the
session's resume state together. The attempt keeps exact snapshots of each changed row
before and after, so undo (QUE-15) restores state exactly, or refuses if the rows were
changed again since. Logs are append-only (DATA-5); voiding sets voided_by once.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import json
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, tzinfo
from typing import Any, cast
from zoneinfo import ZoneInfo

from core.model import (
    THIS_ATTEMPT,
    Attempt,
    AttemptVoid,
    Card,
    CardMark,
    CardRevision,
    CardUser,
    Course,
    CourseGoal,
    CourseSetup,
    DiagnosticSet,
    Dispute,
    DisputeStatus,
    Exam,
    FlashcardState,
    GradedAnswer,
    ImplicitCredit,
    ImportRecord,
    LearnerParams,
    PendingCheck,
    Report,
    ReportStatus,
    ReviewEvent,
    Section,
    SectionState,
    SectionStateName,
    SessionState,
    Skill,
    SkillShadow,
    SkillState,
    SkillTierState,
    StateRecord,
    TemplateSource,
    Unit,
    VoidReason,
    WeakSpot,
)
from core.storage import clock as clock_mod
from core.storage import content, rows, settings
from core.storage.connection import Database
from core.storage.errors import NothingToUndoError, StorageError, UndoConflictError
from core.storage.media import UserMedia
from core.storage.rows import STATE_TABLES, STATE_TABLES_BY_NAME, Row, Table
from core.storage.schema import USER_CONTENT_PREFIX

SNAPSHOT_VERSION = 1
FSRS_FIELDS = (
    "fsrs_state",
    "fsrs_step",
    "stability",
    "difficulty",
    "due_at",
    "last_review_at",
    "reps",
    "lapses",
)
_MISSING = object()

type UserContent = Course | Unit | Section | Skill | Card | CardRevision | TemplateSource


@dataclass(frozen=True, slots=True)
class UndoResult:
    void: AttemptVoid
    attempts: tuple[Attempt, ...]  # the voided attempts, newest first


class _Snapshot:
    """Before/after images of every row a write touches, keyed by (table, primary key)."""

    def __init__(self) -> None:
        self._order: list[tuple[str, str]] = []
        self._key: dict[tuple[str, str], Row] = {}
        self._before: dict[tuple[str, str], Row | None] = {}
        self._after: dict[tuple[str, str], Row | None] = {}

    @staticmethod
    def _id(table: Table, key: Mapping[str, Any]) -> tuple[str, str]:
        return table.name, rows.dumps([key[name] for name in table.pk])

    def touch(self, table: Table, key: Row, before: Row | None) -> None:
        ident = self._id(table, key)
        if ident not in self._key:  # the first image wins: it is the true "before"
            self._order.append(ident)
            self._key[ident] = key
            self._before[ident] = before

    def set_after(self, table: Table, key: Row, after: Row | None) -> None:
        self._after[self._id(table, key)] = after

    def before_of(self, table: Table, key: Row) -> tuple[bool, Row | None]:
        ident = self._id(table, key)
        return (ident in self._key), self._before.get(ident)

    def as_json(self, which: str) -> dict[str, Any]:
        images = self._before if which == "before" else self._after
        return {
            "v": SNAPSHOT_VERSION,
            "rows": [
                {"table": ident[0], "key": self._key[ident], "row": images[ident]}
                for ident in self._order
            ],
        }


def _same_row(current: Row | None, image: Row | None) -> bool:
    """Whether a row still is what a snapshot recorded. A snapshot written before a column
    was added (say pending_check.reason, v2) does not have it: that column is not compared,
    and restoring the image leaves it as it is."""
    if current is None or image is None:
        return current is image
    return all(name in current and current[name] == value for name, value in image.items())


def _snapshot_rows(snapshot: Mapping[str, Any] | None) -> list[tuple[Table, Row, Row | None]]:
    if not snapshot:
        return []
    if snapshot.get("v") != SNAPSHOT_VERSION:
        raise StorageError(f"unknown snapshot version {snapshot.get('v')!r}")
    out = []
    for entry in snapshot["rows"]:
        table = STATE_TABLES_BY_NAME[entry["table"]]
        out.append((table, dict(entry["key"]), entry["row"]))
    return out


def _next_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(
        "SELECT max(coalesce((SELECT seq FROM sqlite_sequence WHERE name = ?), 0), "
        f"coalesce((SELECT max(id) FROM {table}), 0)) + 1",
        (table,),
    ).fetchone()
    return int(row[0])


def count_rows(conn: sqlite3.Connection) -> dict[str, int | None]:
    """Headline counts of a user.db (for backup previews and export manifests)."""

    def one(sql: str) -> int | None:
        value = conn.execute(sql).fetchone()[0]
        return None if value is None else int(value)

    return {
        "attempts": one("SELECT count(*) FROM attempt WHERE voided_by IS NULL"),
        "reviews": one("SELECT count(*) FROM review_log WHERE voided_by IS NULL"),
        "skills": one("SELECT count(*) FROM skill_state"),
        "flashcards": one("SELECT count(*) FROM flashcard_state"),
        "sessions": one("SELECT count(*) FROM session"),
        "own_cards": one(f"SELECT count(*) FROM {USER_CONTENT_PREFIX}card"),
        "last_attempt_at": one("SELECT max(at) FROM attempt WHERE voided_by IS NULL"),
    }


class UserStore:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._media = UserMedia(db)

    @property
    def db(self) -> Database:
        return self._db

    @property
    def media(self) -> UserMedia:
        """The student's own media: files in the profile's media folder (ADR-0011)."""
        return self._media

    def _now(self) -> int:
        return self._db.clock.now_ms()

    def atomic[T](self, work: Callable[[UserStore], T]) -> T:
        """Run several store calls as one transaction: writes inside join it, reads see it.
        A call inside that raises leaves none of its own writes behind."""
        return self._db.write(lambda _conn: work(self))

    # ------------------------------------------------------------ generic helpers

    def _stamp[R](self, record: R, now: int) -> R:
        table = rows.table_for(type(record))
        updates = {name: now for name in table.stamp if getattr(record, name) == 0}
        return cast(R, replace(cast(Any, record), **updates)) if updates else record

    def _put_in[R](self, conn: sqlite3.Connection, record: R, now: int) -> R:
        table = rows.table_for(type(record))
        row = rows.to_row(self._stamp(record, now))
        if table.autoinc and row["id"] is None:
            key: Row = {"id": rows.insert_row(conn, table, row)}
        else:
            rows.upsert_row(conn, table, row)
            key = rows.key_of(table, row)
        stored = rows.read_row(conn, table, key)
        if stored is None:
            raise StorageError(f"{table.name} {key} vanished after writing")
        return rows.from_row(type(record), stored)

    def _put[R](self, record: R) -> R:
        return self._db.write(lambda conn: self._put_in(conn, record, self._now()))

    def _list[R](
        self,
        record_type: type[R],
        where: str = "",
        params: Mapping[str, Any] | tuple[Any, ...] = (),
        order: str = "",
    ) -> list[R]:
        with self._db.reading() as conn:
            return rows.select(conn, record_type, where, params, order)

    def _get[R](self, record_type: type[R], **key: Any) -> R | None:
        with self._db.reading() as conn:
            return rows.select_one(conn, record_type, **key)

    # ------------------------------------------------------------ settings and time

    def get_setting(self, key: str, default: Any = _MISSING) -> Any:
        with self._db.reading() as conn:
            row = conn.execute("SELECT value FROM setting WHERE key = ?", (key,)).fetchone()
        if row is not None:
            return json.loads(row[0])
        return settings.default(key) if default is _MISSING else default

    def settings(self) -> dict[str, Any]:
        with self._db.reading() as conn:
            stored = {
                r[0]: json.loads(r[1]) for r in conn.execute("SELECT key, value FROM setting")
            }
        return settings.defaults() | stored

    def set_setting(self, key: str, value: Any) -> None:
        self.set_settings({key: value})

    def set_settings(self, values: Mapping[str, Any]) -> None:
        for key, value in values.items():
            settings.validate(key, value)

        def write(conn: sqlite3.Connection) -> None:
            now = self._now()
            for key, value in values.items():
                conn.execute(
                    "INSERT INTO setting (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT "
                    "(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                    (key, rows.dumps(value), now),
                )

        self._db.write(write)

    def timezone(self) -> tzinfo:
        name = self.get_setting("study.timezone")
        return ZoneInfo(name) if name else self._db.clock.tz

    def rollover_hour(self) -> int:
        return int(self.get_setting("study.day_start_hour"))

    def study_day(self, at_ms: int | None = None) -> str:
        at = self._now() if at_ms is None else at_ms
        return clock_mod.study_day_iso(at, self.timezone(), self.rollover_hour())

    def day_bounds(self, day: str) -> tuple[int, int]:
        """[start, end) of a study day in UTC ms."""
        return clock_mod.day_bounds_ms(
            date.fromisoformat(day), self.timezone(), self.rollover_hour()
        )

    # ------------------------------------------------------------ goals, exams, sections

    def set_course_goal(self, goal: CourseGoal) -> CourseGoal:
        return self._put(replace(goal, updated_at=self._now()))

    def course_goal(self, course_id: str) -> CourseGoal | None:
        return self._get(CourseGoal, course_id=course_id)

    def course_goals(self) -> list[CourseGoal]:
        return self._list(CourseGoal)

    def add_exam(self, exam: Exam) -> Exam:
        if exam.id is not None:
            raise ValueError("a new exam has no id")
        return self._put(exam)

    def update_exam(self, exam: Exam) -> Exam:
        if exam.id is None or self._get(Exam, id=exam.id) is None:
            raise StorageError(f"no exam {exam.id}")
        return self._put(exam)

    def delete_exam(self, exam_id: int) -> None:
        self._db.write(lambda conn: conn.execute("DELETE FROM exam WHERE id = ?", (exam_id,)))

    def exams(self) -> list[Exam]:
        return self._list(Exam, order="at, id")

    def set_section_state(self, section_id: str, state: SectionStateName) -> SectionState:
        return self._put(SectionState(section_id=section_id, state=state, changed_at=self._now()))

    def section_states(self) -> dict[str, SectionState]:
        return {s.section_id: s for s in self._list(SectionState)}

    # ------------------------------------------------------------ planner and learner (v3)

    def set_course_setup(self, setup: CourseSetup) -> CourseSetup:
        """Add or replace a course's setup (the caller checks the course exists: courses
        live in packs, which the table cannot reference)."""
        return self._put(replace(setup, updated_at=self._now()))

    def course_setup(self, course_id: str) -> CourseSetup | None:
        return self._get(CourseSetup, course_id=course_id)

    def course_setups(self) -> list[CourseSetup]:
        return self._list(CourseSetup)

    def learner_params(self, version: str | None = None) -> LearnerParams | None:
        """The current parameter version, or the named one; None when there is none."""
        if version is not None:
            return self._get(LearnerParams, version=version)
        found = self._list(LearnerParams, "current = 1")
        return found[0] if found else None

    def learner_param_history(self) -> list[LearnerParams]:
        """Every parameter version, oldest first."""
        return self._list(LearnerParams, order="created_at, version")

    def add_learner_params(self, record: LearnerParams) -> LearnerParams:
        """Write a new parameter version. When it is current, the version current before
        stops being current in the same transaction. A version is never rewritten."""

        def write(conn: sqlite3.Connection) -> LearnerParams:
            if rows.select_one(conn, LearnerParams, version=record.version) is not None:
                raise StorageError(f"parameter version {record.version} already exists")
            if record.current:
                conn.execute("UPDATE learner_params SET current = 0 WHERE current = 1")
            return self._put_in(conn, record, self._now())

        return self._db.write(write)

    # ------------------------------------------------------------ memory state

    def skill_state(self, skill_id: str) -> SkillState | None:
        return self._get(SkillState, skill_id=skill_id)

    def skill_states(self, skill_ids: Iterable[str] | None = None) -> dict[str, SkillState]:
        found = self._list(SkillState)
        if skill_ids is not None:
            wanted = set(skill_ids)
            found = [s for s in found if s.skill_id in wanted]
        return {s.skill_id: s for s in found}

    def skill_tiers(self, skill_id: str | None = None) -> list[SkillTierState]:
        if skill_id is None:
            return self._list(SkillTierState)
        return self._list(SkillTierState, "skill_id = ?", (skill_id,))

    def skill_shadows(self) -> dict[str, SkillShadow]:
        return {s.skill_id: s for s in self._list(SkillShadow)}

    def flashcard_state(self, card_id: str, ord: int = 0) -> FlashcardState | None:
        return self._get(FlashcardState, card_id=card_id, ord=ord)

    def flashcard_states(self) -> list[FlashcardState]:
        return self._list(FlashcardState)

    def card_user(self, card_id: str) -> CardUser | None:
        return self._get(CardUser, card_id=card_id)

    def card_users(self) -> dict[str, CardUser]:
        return {c.card_id: c for c in self._list(CardUser)}

    def pending_checks(self, status: str | None = "pending") -> list[PendingCheck]:
        if status is None:
            return self._list(PendingCheck)
        return self._list(PendingCheck, "status = ?", (status,))

    def weak_spots(self, status: str | None = None) -> list[WeakSpot]:
        if status is None:
            return self._list(WeakSpot)
        return self._list(WeakSpot, "status = ?", (status,))

    def diagnostic_sets(self, status: str | None = None) -> list[DiagnosticSet]:
        if status is None:
            return self._list(DiagnosticSet)
        return self._list(DiagnosticSet, "status = ?", (status,))

    def apply(self, changes: Sequence[StateRecord]) -> tuple[StateRecord, ...]:
        """Write state rows outside any attempt (daily runs, section switches). Not undoable."""

        def write(conn: sqlite3.Connection) -> tuple[StateRecord, ...]:
            now = self._now()
            out = []
            for record in changes:
                if type(record) not in STATE_TABLES:
                    raise TypeError(f"{type(record).__name__} is not a state record")
                out.append(self._put_in(conn, record, now))
            return tuple(out)

        return self._db.write(write)

    # ------------------------------------------------------------ card marks

    def card_mark(self, card_id: str) -> CardMark | None:
        return self._get(CardMark, card_id=card_id)

    def card_marks(self) -> dict[str, CardMark]:
        return {m.card_id: m for m in self._list(CardMark)}

    def set_card_mark(self, mark: CardMark) -> CardMark:
        return self._put(replace(mark, updated_at=self._now()))

    # ------------------------------------------------------------ graded answers

    def record_answer(self, answer: GradedAnswer) -> Attempt:
        """Commit one graded answer and everything it changes in a single transaction."""
        attempt = answer.attempt
        if attempt.id is not None or attempt.voided_by is not None:
            raise ValueError("a new attempt has no id and is not voided")
        if attempt.state_before is not None or attempt.state_after is not None:
            raise ValueError("snapshots are taken by storage")
        if answer.session is not None and answer.session.id is None:
            raise ValueError("start the session before recording answers in it")
        for record in answer.changes:
            if type(record) not in STATE_TABLES:
                raise TypeError(f"{type(record).__name__} cannot change with an attempt")
        return self._db.write(lambda conn: self._record(conn, answer))

    def _record(self, conn: sqlite3.Connection, answer: GradedAnswer) -> Attempt:
        now = self._now()
        attempt = answer.attempt
        at = attempt.at or now
        day = attempt.study_day or self.study_day(at)
        attempt_id = _next_id(conn, "attempt")
        snap = _Snapshot()
        for record in answer.changes:
            self._snap_put(conn, snap, _bind_attempt(record, attempt_id), at)
        stored = replace(
            attempt,
            id=attempt_id,
            at=at,
            study_day=day,
            state_before=snap.as_json("before"),
            state_after=snap.as_json("after"),
        )
        rows.insert_row(conn, rows.table_for(Attempt), rows.to_row(stored))
        for review in answer.reviews:
            _insert_event(conn, snap, review, attempt_id, at)
        for credit in answer.credits:
            credit = replace(credit, id=None, at=credit.at or at, attempt_id=attempt_id)
            rows.insert_row(conn, rows.table_for(ImplicitCredit), rows.to_row(credit))
        if answer.session is not None:
            self._save_session_in(conn, answer.session, now)
        result = rows.select_one(conn, Attempt, id=attempt_id)
        if result is None:
            raise StorageError(f"attempt {attempt_id} vanished after writing")
        return result

    def _snap_put(self, conn: sqlite3.Connection, snap: _Snapshot, record: Any, now: int) -> None:
        table = STATE_TABLES[type(record)]
        row = rows.to_row(self._stamp(record, now))
        if table.autoinc and row["id"] is None:
            key: Row = {"id": rows.insert_row(conn, table, row)}
            snap.touch(table, key, None)
        else:
            key = rows.key_of(table, row)
            snap.touch(table, key, rows.read_row(conn, table, key))
            rows.upsert_row(conn, table, row)
        snap.set_after(table, key, rows.read_row(conn, table, key))

    def settle_attempt(
        self,
        attempt_id: int,
        reviews: Sequence[ReviewEvent],
        changes: Sequence[StateRecord],
    ) -> list[ReviewEvent]:
        """Settle an older attempt's held verdict (ENG-6: its check never answered): its
        review events, bound to that attempt so voiding it voids them, and the state they
        change, in one transaction."""

        def write(conn: sqlite3.Connection) -> list[ReviewEvent]:
            if rows.select_one(conn, Attempt, id=attempt_id) is None:
                raise StorageError(f"no attempt {attempt_id}")
            snap = _Snapshot()
            now = self._now()
            for record in changes:
                if type(record) not in STATE_TABLES:
                    raise TypeError(f"{type(record).__name__} is not a state record")
                self._snap_put(conn, snap, record, now)
            ids = [_insert_event(conn, snap, r, attempt_id, now) for r in reviews]
            return [e for e in rows.select(conn, ReviewEvent) if e.id in ids]

        return self._db.write(write)

    def attempt(self, attempt_id: int) -> Attempt | None:
        return self._get(Attempt, id=attempt_id)

    def attempts(
        self,
        *,
        skill_id: str | None = None,
        card_id: str | None = None,
        session_id: int | None = None,
        since: int | None = None,
        until: int | None = None,
        include_voided: bool = False,
        limit: int | None = None,
        newest_first: bool = False,
        after_id: int | None = None,
    ) -> list[Attempt]:
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (("skill_id", skill_id), ("card_id", card_id)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        if after_id is not None:
            clauses.append("id > ?")
            params.append(after_id)
        if since is not None:
            clauses.append("at >= ?")
            params.append(since)
        if until is not None:
            clauses.append("at < ?")
            params.append(until)
        if not include_voided:
            clauses.append("voided_by IS NULL")
        order = "id DESC" if newest_first else "id"
        if limit is not None:
            order += f" LIMIT {int(limit)}"
        return self._list(Attempt, " AND ".join(clauses), tuple(params), order)

    def last_attempt(self, *, include_voided: bool = False) -> Attempt | None:
        found = self.attempts(include_voided=include_voided, limit=1, newest_first=True)
        return found[0] if found else None

    def attempt_log_key(self) -> tuple[int, int]:
        """(the newest non-voided attempt id or 0, the number of voided attempts): what a
        state derived from the log depends on. New answers raise the first; undo, disputes
        and reports change both."""
        with self._db.reading() as conn:
            row = conn.execute(
                "SELECT coalesce((SELECT max(id) FROM attempt WHERE voided_by IS NULL), 0), "
                "(SELECT count(*) FROM attempt WHERE voided_by IS NOT NULL)"
            ).fetchone()
        return int(row[0]), int(row[1])

    def review_events(
        self,
        *,
        target_kind: str | None = None,
        target_id: str | None = None,
        since: int | None = None,
        include_voided: bool = False,
    ) -> list[ReviewEvent]:
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (("target_kind", target_kind), ("target_id", target_id)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if since is not None:
            clauses.append("at >= ?")
            params.append(since)
        if not include_voided:
            clauses.append("voided_by IS NULL")
        return self._list(ReviewEvent, " AND ".join(clauses), tuple(params))

    def credits(self, *, include_voided: bool = False) -> list[ImplicitCredit]:
        return self._list(ImplicitCredit, "" if include_voided else "voided_by IS NULL")

    def voids(self) -> list[AttemptVoid]:
        return self._list(AttemptVoid)

    # ------------------------------------------------------------ undo and voiding

    def undo_last_answer(
        self,
        *,
        reason: VoidReason = "undo",
        note: str | None = None,
        session: SessionState | None = None,
    ) -> UndoResult:
        """QUE-15: void the latest answer (all tries of its presentation) and restore the
        exact state before it, in one transaction. Refuses if those rows changed since."""
        return self._db.write(lambda conn: self._undo(conn, reason, note, session))

    def _undo(
        self,
        conn: sqlite3.Connection,
        reason: VoidReason,
        note: str | None,
        session: SessionState | None,
    ) -> UndoResult:
        tail = rows.select(conn, Attempt, "voided_by IS NULL", (), "id DESC LIMIT 100")
        if not tail:
            raise NothingToUndoError("no answer to undo")
        group = [tail[0]]
        if tail[0].presentation_id is not None:
            for attempt in tail[1:]:
                if attempt.presentation_id != tail[0].presentation_id:
                    break
                group.append(attempt)
        snap = _Snapshot()
        for attempt in group:  # newest first
            for table, key, after in _snapshot_rows(attempt.state_after):
                current = rows.read_row(conn, table, key)
                if not _same_row(current, after):
                    raise UndoConflictError(
                        f"attempt {attempt.id}: {table.name} {key} changed after it; "
                        "undo would not be exact"
                    )
            for table, key, before in _snapshot_rows(attempt.state_before):
                snap.touch(table, key, rows.read_row(conn, table, key))
                if before is None:
                    rows.delete_row(conn, table, key)
                else:
                    rows.upsert_row(conn, table, before)
                snap.set_after(table, key, rows.read_row(conn, table, key))
        for table in STATE_TABLES.values():  # small tables; the FKs among them are deferred
            dangling = conn.execute(f"PRAGMA foreign_key_check({table.name})").fetchall()
            if dangling:
                raise UndoConflictError(
                    f"{table.name} row {dangling[0][1]} now points at a row this undo would "
                    "remove; undo would not be exact"
                )
        return self._finish_void(conn, group, reason, note, snap, session)

    def void_attempts(
        self,
        attempt_ids: Sequence[int],
        *,
        reason: VoidReason,
        changes: Sequence[StateRecord] = (),
        note: str | None = None,
        session: SessionState | None = None,
    ) -> UndoResult:
        """Void older attempts (report, dispute, recompute) and write the state the engine
        recomputed without them. Nothing is restored automatically here."""

        def write(conn: sqlite3.Connection) -> UndoResult:
            group = []
            for attempt_id in sorted(set(attempt_ids), reverse=True):
                attempt = rows.select_one(conn, Attempt, id=attempt_id)
                if attempt is None:
                    raise StorageError(f"no attempt {attempt_id}")
                if attempt.voided_by is not None:
                    raise StorageError(f"attempt {attempt_id} is already voided")
                group.append(attempt)
            if not group:
                raise ValueError("no attempts given")
            snap = _Snapshot()
            now = self._now()
            for record in changes:
                if type(record) not in STATE_TABLES:
                    raise TypeError(f"{type(record).__name__} is not a state record")
                self._snap_put(conn, snap, record, now)
            return self._finish_void(conn, group, reason, note, snap, session)

        return self._db.write(write)

    def rewrite_states(
        self,
        changes: Sequence[StateRecord],
        *,
        reason: VoidReason = "recompute",
        note: str | None = None,
    ) -> AttemptVoid | None:
        """Write state rows the engine rebuilt from the log (a recompute, a repair) in one
        transaction, logged as an attempt_void row that voids no attempt and keeps the
        before/after snapshot. Nothing to write: None."""
        if not changes:
            return None

        def write(conn: sqlite3.Connection) -> AttemptVoid:
            snap = _Snapshot()
            now = self._now()
            for record in changes:
                if type(record) not in STATE_TABLES:
                    raise TypeError(f"{type(record).__name__} is not a state record")
                self._snap_put(conn, snap, record, now)
            return self._finish_void(conn, [], reason, note, snap, None).void

        return self._db.write(write)

    def raw_state_rows(self, record_type: type[Any]) -> list[dict[str, Any]]:
        """A state table's rows as stored, without building records (a corrupted row would
        not build): for the "Check database" repair."""
        table = STATE_TABLES[record_type]
        with self._db.reading() as conn:
            found = conn.execute(f"SELECT * FROM {table.name}").fetchall()
        return [dict(r) for r in found]

    def _finish_void(
        self,
        conn: sqlite3.Connection,
        group: list[Attempt],
        reason: VoidReason,
        note: str | None,
        snap: _Snapshot,
        session: SessionState | None,
    ) -> UndoResult:
        now = self._now()
        void = self._put_in(
            conn,
            AttemptVoid(
                at=now,
                reason=reason,
                note=note,
                state_before=snap.as_json("before"),
                state_after=snap.as_json("after"),
            ),
            now,
        )
        ids = [a.id for a in group]
        marks = ", ".join("?" for _ in ids)
        for table in ("attempt", "review_log", "implicit_credit"):
            column = "id" if table == "attempt" else "attempt_id"
            conn.execute(
                f"UPDATE {table} SET voided_by = ? WHERE {column} IN ({marks}) "
                "AND voided_by IS NULL",
                (void.id, *ids),
            )
        if session is not None:
            self._save_session_in(conn, session, now)
        voided = tuple(rows.select(conn, Attempt, f"id IN ({marks})", tuple(ids), "id DESC"))
        return UndoResult(void, voided)

    # ------------------------------------------------------------ sessions (QUE-16)

    def start_session(self, session: SessionState) -> SessionState:
        if session.id is not None:
            raise ValueError("a new session has no id")
        return self._put(session)

    def save_session(self, session: SessionState) -> SessionState:
        if session.id is None:
            raise ValueError("start the session first")
        return self._db.write(lambda conn: self._save_session_in(conn, session, self._now()))

    def _save_session_in(
        self, conn: sqlite3.Connection, session: SessionState, now: int
    ) -> SessionState:
        if session.id is not None and rows.select_one(conn, SessionState, id=session.id) is None:
            raise StorageError(f"no session {session.id}")
        return self._put_in(conn, replace(session, updated_at=now), now)

    def session(self, session_id: int) -> SessionState | None:
        return self._get(SessionState, id=session_id)

    def latest_open_session(self) -> SessionState | None:
        found = self._list(SessionState, "ended_at IS NULL", (), "updated_at DESC, id DESC LIMIT 1")
        return found[0] if found else None

    def resumable_session(self, study_day: str | None = None) -> SessionState | None:
        """The open session to resume, only if it belongs to this study day (QUE-16)."""
        session = self.latest_open_session()
        today = study_day or self.study_day()
        return session if session is not None and session.study_day == today else None

    def end_session(self, session_id: int) -> SessionState:
        def write(conn: sqlite3.Connection) -> SessionState:
            session = rows.select_one(conn, SessionState, id=session_id)
            if session is None:
                raise StorageError(f"no session {session_id}")
            now = self._now()
            return self._put_in(conn, replace(session, ended_at=now, updated_at=now), now)

        return self._db.write(write)

    # ------------------------------------------------------------ disputes and reports

    def add_dispute(self, dispute: Dispute) -> Dispute:
        return self._put(replace(dispute, id=None))

    def disputes(self, status: DisputeStatus | None = None) -> list[Dispute]:
        if status is None:
            return self._list(Dispute)
        return self._list(Dispute, "status = ?", (status,))

    def resolve_dispute(
        self, dispute_id: int, status: DisputeStatus, note: str | None = None
    ) -> Dispute:
        return self._resolve(Dispute, dispute_id, status=status, note=note)

    def add_report(self, report: Report, *, hide: bool = True) -> Report:
        """Log a report; by default also hide the card from every queue at once."""

        def write(conn: sqlite3.Connection) -> Report:
            now = self._now()
            stored = self._put_in(conn, replace(report, id=None), now)
            if hide:
                mark = rows.select_one(conn, CardMark, card_id=report.card_id)
                mark = mark or CardMark(card_id=report.card_id)
                self._put_in(conn, replace(mark, hidden=True, updated_at=now), now)
            return stored

        return self._db.write(write)

    def reports(self, status: ReportStatus | None = None) -> list[Report]:
        if status is None:
            return self._list(Report)
        return self._list(Report, "status = ?", (status,))

    def resolve_report(self, report_id: int, status: ReportStatus) -> Report:
        return self._resolve(Report, report_id, status=status)

    def _resolve[R](self, record_type: type[R], record_id: int, **changes: Any) -> R:
        def write(conn: sqlite3.Connection) -> R:
            record = rows.select_one(conn, record_type, id=record_id)
            if record is None:
                raise StorageError(f"no {record_type.__name__.lower()} {record_id}")
            now = self._now()
            updated = replace(cast(Any, record), resolved_at=now, **changes)
            return self._put_in(conn, cast(R, updated), now)

        return self._db.write(write)

    # ------------------------------------------------------------ the student's own content

    def put_user_content(self, *records: UserContent) -> None:
        """Add or replace own courses, skills and cards (same shape as pack content), and
        own templates' source text."""

        def write(conn: sqlite3.Connection) -> None:
            p = USER_CONTENT_PREFIX
            for record in records:
                match record:
                    case Course():
                        content.write_course(conn, p, record)
                    case Unit():
                        content.write_unit(conn, p, record)
                    case Section():
                        content.write_section(conn, p, record)
                    case Skill():
                        content.write_skill(conn, p, record)
                    case Card():
                        row = conn.execute(
                            f"SELECT rev FROM {p}card WHERE id = ?", (record.id,)
                        ).fetchone()
                        if row is not None and row[0] > record.rev:
                            raise StorageError(
                                f"card {record.id} is at rev {row[0]}; revisions only go up"
                            )
                        timed = [record.time_minutes, *(q.time_minutes for q in record.parts)]
                        if any(t is not None for t in timed):  # user.db has no card_time
                            raise StorageError(
                                f"card {record.id}: standard times (time:) are kept in packs only"
                            )
                        content.write_card(conn, p, record)
                    case CardRevision():
                        content.write_revision(conn, p, record)
                    case TemplateSource():
                        self._put_in(conn, record, self._now())
                    case _:
                        raise TypeError(f"{type(record).__name__} is not user content")

        self._db.write(write)

    def retire_user_card(self, card_id: str) -> None:
        """PACK-2: cards are retired, never deleted, so their history stays valid."""

        def write(conn: sqlite3.Connection) -> None:
            cursor = conn.execute(
                f"UPDATE {USER_CONTENT_PREFIX}card SET status = 'retired' WHERE id = ?", (card_id,)
            )
            if cursor.rowcount != 1:
                raise StorageError(f"no own card {card_id}")

        self._db.write(write)

    def user_card(self, card_id: str) -> Card | None:
        with self._db.reading() as conn:
            return content.ContentReader(conn, "main", USER_CONTENT_PREFIX, "user").card(card_id)

    def user_cards(self) -> list[Card]:
        with self._db.reading() as conn:
            return content.ContentReader(conn, "main", USER_CONTENT_PREFIX, "user").cards()

    def user_skills(self) -> list[Skill]:
        with self._db.reading() as conn:
            return content.ContentReader(conn, "main", USER_CONTENT_PREFIX, "user").skills()

    def user_template(self, template_id: str) -> TemplateSource | None:
        """An own template's source text (EDT-1 opens it; its instances are cards whose
        template_id is this id)."""
        return self._get(TemplateSource, id=template_id)

    def user_templates(self) -> list[TemplateSource]:
        return self._list(TemplateSource)

    def template_sources(self) -> dict[str, str]:
        """{template id: source text} of every own template, for export (EXP-1)."""
        return {t.id: t.source_md for t in self.user_templates()}

    # ------------------------------------------------------------ imports and counts

    def log_import(self, record: ImportRecord) -> ImportRecord:
        return self._put(replace(record, id=None))

    def imports(self) -> list[ImportRecord]:
        return self._list(ImportRecord)

    def counts(self) -> dict[str, int | None]:
        with self._db.reading() as conn:
            return count_rows(conn)


def _bind_attempt(record: Any, attempt_id: int) -> Any:
    if isinstance(record, PendingCheck):
        if record.attempt_id == THIS_ATTEMPT:
            record = replace(record, attempt_id=attempt_id)
        if record.resolved_by == THIS_ATTEMPT:
            record = replace(record, resolved_by=attempt_id)
    return record


def _target(review: ReviewEvent) -> tuple[Table, Row]:
    if review.target_kind == "skill":
        return STATE_TABLES[SkillState], {"skill_id": review.target_id}
    return STATE_TABLES[FlashcardState], {"card_id": review.target_id, "ord": review.target_ord}


def _insert_event(
    conn: sqlite3.Connection, snap: _Snapshot, review: ReviewEvent, attempt_id: int, at: int
) -> int:
    """Insert one review event of an attempt, with its card's state before and after."""
    table, key = _target(review)
    touched, before = snap.before_of(table, key)
    after = rows.read_row(conn, table, key)
    if not touched:
        before = after
    event = replace(
        review,
        id=None,
        at=review.at or at,
        attempt_id=attempt_id,
        state_before=_fsrs_subset(before),
        state_after=_fsrs_subset(after),
        voided_by=None,
    )
    return rows.insert_row(conn, rows.table_for(ReviewEvent), rows.to_row(event))


def _fsrs_subset(row: Row | None) -> dict[str, Any] | None:
    return None if row is None else {name: row[name] for name in FSRS_FIELDS}
