"""The Python API the page sees as window.pywebview.api (typed in web/src/lib/bridge.ts).

Every public method is callable from JavaScript, and the public methods here and the
`BridgeApi` interface in bridge.ts must match name for name (tests/test_app.py). Payloads
are JSON: the study methods return `core.queue.to_dict` of the StudyService views as they
are (types.ts mirrors core/queue/views.py), so fields the core adds reach the page.

Threading (AGENTS.md rule 6): pywebview runs each call on a fresh worker thread. One
re-entrant lock serializes every call that touches the profile, so two calls never
interleave a session change; storage gives each thread its own read connection and does
all writes on its single writer thread, so no sqlite3 connection is ever shared.

Arguments are untrusted JSON values: their types are checked here, never evaluated
(ADR-0003). A request the session can't act on now raises `UserMessage`; the page shows
its text (pywebview rejects the call with an Error whose name is "UserMessage").
"""

import functools
import platform
import sqlite3
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, Concatenate, get_args

import core
from app.media import card_media
from core.model import SectionStateName
from core.queue import QueueError, StudyService, to_dict
from core.storage import (
    BackupError,
    Clock,
    CorruptDatabaseError,
    ProfileError,
    ProfileInUseError,
    ProfileManager,
    SchemaTooNewError,
    Storage,
    StorageError,
    SystemClock,
    UnsafeSQLiteError,
)
from core.storage.backups import BackupInfo, BackupManager
from core.storage.profiles import ProfileInfo

MAX_PING_CHARS = 10_000
MAX_ANSWER_CHARS = 2_000
MAX_DRAFT_CHARS = 20_000
MAX_NOTE_CHARS = 2_000
MAX_ID_CHARS = 400

MODES = ("daily", "extra", "practice-test")
FLAGS = ("too_easy", "dispute", "report", "flag", "suspend")
SELF_GRADES = ("matched", "minor-slip", "missed")
SOURCES = ("text", "mathlive")
SECTION_STATES: tuple[str, ...] = get_args(SectionStateName)
THEMES = {"auto": "automatic", "day": "day", "night": "night"}  # page name -> setting value
TEXT_SIZE = (14, 28, 18)  # min, max, default (px)

type Json = dict[str, Any]
type PackPaths = Callable[[], Sequence[Path]]


class UserMessage(Exception):
    """A request the page can't act on now. The text is shown to the student."""


class SelfTestInbox:
    """Receives the page's self-test report (app --self-test); thread-safe."""

    def __init__(self) -> None:
        self._report: dict[str, Any] | None = None
        self._received = threading.Event()
        self._lock = threading.Lock()

    def put(self, report: dict[str, Any]) -> None:
        with self._lock:
            self._report = report
        self._received.set()

    def wait(self, timeout: float) -> dict[str, Any] | None:
        if not self._received.wait(timeout):
            return None
        with self._lock:
            return self._report


# ---------------------------------------------------------------- argument checks


def _obj(value: object, what: str = "request") -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{what} must be an object")
    return value


def _str(value: object, what: str, limit: int = MAX_ID_CHARS) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a string")
    if len(value) > limit:
        raise ValueError(f"{what} is longer than {limit} characters")
    return value


def _opt_str(value: object, what: str, limit: int = MAX_ID_CHARS) -> str | None:
    return None if value is None else _str(value, what, limit)


def _int(value: object, what: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float) or value != int(value):
        raise TypeError(f"{what} must be a whole number")
    number = int(value)
    if not low <= number <= high:
        raise ValueError(f"{what} must be between {low} and {high}")
    return number


def _opt_int(value: object, what: str, low: int, high: int) -> int | None:
    return None if value is None else _int(value, what, low, high)


def _bool(value: object, what: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{what} must be true or false")
    return value


def _one_of(value: object, what: str, options: Sequence[str]) -> str:
    if value not in options:
        raise ValueError(f"{what} must be one of {', '.join(options)}")
    return str(value)


def _timing(value: object) -> Json:
    """A TimingReport as the page sends it: ms counts and flags; unknown keys are dropped."""
    data = _obj(value, "timing")
    out: Json = {}
    for key in ("active_ms", "solve_ms", "entry_ms", "paused_ms", "longest_pause_ms"):
        if data.get(key) is not None:
            out[key] = _int(data[key], f"timing.{key}", -(10**12), 10**12)
    if data.get("pause_count") is not None:
        out["pause_count"] = _int(data["pause_count"], "timing.pause_count", 0, 100_000)
    for key in ("after_wake", "idle_trimmed"):
        if data.get(key) is not None:
            out[key] = _bool(data[key], f"timing.{key}")
    return out


def _answers(value: object) -> list[Json]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 50:
        raise TypeError("answers must be a list of at most 50 parts")
    out = []
    for item in value:
        data = _obj(item, "answer")
        out.append(
            {
                "part": _opt_str(data.get("part"), "answer.part"),
                "value": _str(data.get("value", ""), "answer.value", MAX_ANSWER_CHARS),
                "source": _one_of(data.get("source", "text"), "answer.source", SOURCES),
            }
        )
    return out


# ---------------------------------------------------------------- the bridge


def _serial[**P, R](method: Callable[Concatenate[Api, P], R]) -> Callable[Concatenate[Api, P], R]:
    """Run a bridge call under the API lock; a QueueError becomes a UserMessage."""

    @functools.wraps(method)
    def call(self: Api, /, *args: P.args, **kwargs: P.kwargs) -> R:
        with self._lock:
            try:
                return method(self, *args, **kwargs)
            except QueueError as error:
                raise UserMessage(str(error)) from error

    return call


class Api:
    def __init__(
        self,
        *,
        self_test: SelfTestInbox | None = None,
        profiles: ProfileManager | None = None,
        pack_paths: PackPaths | Sequence[Path] = (),
        clock: Clock | None = None,
    ) -> None:
        self._self_test = self_test
        self._profiles = profiles
        self._pack_paths = pack_paths
        self._clock = clock
        self._lock = threading.RLock()
        self._profile: ProfileInfo | None = None
        self._storage: Storage | None = None
        self._service: StudyService | None = None
        self._error: str | None = None
        self._recovery: ProfileInfo | None = None  # a profile that failed to open (BAK-4)
        self._warnings: list[str] = []
        self._prefs: Json = {"theme": "auto", "text_size": TEXT_SIZE[2]}

    # ------------------------------------------------------------ lifecycle (app/main.py)

    def _open_last(self) -> None:
        """Open the profile used last (or the only one). First run: none, the page asks."""
        with self._lock:
            if self._profiles is None or self._storage is not None:
                return
            try:
                chosen = self._profiles.last_chosen()
                if chosen is None:
                    listed = self._profiles.list()
                    chosen = listed[0] if len(listed) == 1 else None
            except (StorageError, OSError) as error:
                self._error = f"The profile list could not be read: {error}"
                return
            if chosen is not None:
                self._open(chosen)

    def _open(self, info: ProfileInfo) -> None:
        """Open a profile. One that exists but can't be opened (a failed integrity check, a
        missing or unreadable user.db) is kept for the restore screen (BAK-4): no new
        profile is created over it."""
        packs = self._pack_paths() if callable(self._pack_paths) else self._pack_paths
        try:
            storage = Storage.open(info.paths, pack_paths=list(packs), clock=self._clock)
        except ProfileInUseError:
            self._error = f"{info.name}'s profile is open in another Toishi window."
            return
        except SchemaTooNewError:
            self._error = f"{info.name}'s profile was saved by a newer Toishi."
            return
        except UnsafeSQLiteError as error:  # DEV-7: no backup would help
            self._error = f"{error}."
            return
        except CorruptDatabaseError as error:
            self._recovery = info
            self._error = f"{info.name}'s profile failed its integrity check: {error}"
            return
        except (StorageError, sqlite3.Error) as error:
            self._recovery = info
            self._error = f"{info.name}'s profile could not be opened: {error}"
            return
        if self._profiles is not None:
            info = self._profiles.choose(info.id)
        self._profile = info
        self._storage = storage
        self._service = StudyService(storage, app_version=core.version())
        self._warnings = storage.warnings()
        self._error = None
        self._recovery = None
        theme = storage.users.get_setting("ui.theme", "automatic")
        size = storage.users.get_setting("ui.text_size_px", TEXT_SIZE[2])
        page_theme = next((k for k, v in THEMES.items() if v == theme), "auto")
        self._prefs = {"theme": page_theme, "text_size": size}

    def _close(self, *, backup: bool = True) -> None:
        """Close the profile (on-close backup, best effort; every answer is already committed)."""
        with self._lock:
            storage, self._storage, self._service = self._storage, None, None
            if storage is not None:
                storage.close(backup=backup)

    def _study(self) -> StudyService:
        if self._service is None:
            raise UserMessage("Create or open a profile first.")
        return self._service

    def _store(self) -> Storage:
        if self._storage is None:
            raise UserMessage("Create or open a profile first.")
        return self._storage

    def _storage_or_none(self) -> Storage | None:
        """The open profile's storage, for the media route (server threads; no lock, no raise)."""
        return self._storage

    def _guard(self, item_key: object) -> None:
        """A stale page (a double key press, a second window) must not act on another item."""
        key = _opt_str(item_key, "item_key")
        if key is None:
            return
        session = self._store().users.latest_open_session()
        current = (session.current or {}).get("key") if session is not None else None
        if current is not None and current != key:
            raise UserMessage("That problem is no longer on screen.")

    # ------------------------------------------------------------ app

    def ping(self, message: str) -> str:
        """Echo, to prove the round trip page -> Python -> page."""
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        if len(message) > MAX_PING_CHARS:
            raise ValueError(f"message longer than {MAX_PING_CHARS} characters")
        return f"pong: {message}"

    def version(self) -> str:
        return core.version()

    def app_info(self) -> dict[str, object]:
        return {
            "name": core.APP_NAME,
            "version": core.version(),
            "python": platform.python_version(),
            "self_test": self._self_test is not None,
        }

    def report_self_test(self, report: object) -> None:
        """Called by the page when it finishes its self-test (only in --self-test runs)."""
        if not isinstance(report, dict):
            raise TypeError("report must be an object")
        if self._self_test is not None:
            self._self_test.put(dict(report))

    # ------------------------------------------------------------ profile and preferences

    @_serial
    def profile_get(self) -> Json:
        """The open profile, or none (first run: the page asks for a name; a profile that
        could not be opened: restore_list names it and the page shows the restore screen)."""
        profile = self._profile if self._storage is not None else None
        return {
            "profile": None if profile is None else {"id": profile.id, "name": profile.name},
            "error": self._error,
            "warnings": list(self._warnings),
        }

    @_serial
    def profile_create(self, request: object) -> Json:
        """First run: a profile needs only a name (spec: Library, First run 1)."""
        name = _str(_obj(request).get("name"), "name", 200)
        if self._profiles is None:
            raise UserMessage("Profiles are not available in this run.")
        if self._storage is not None:
            raise UserMessage("A profile is already open.")
        if self._recovery is not None:  # never a new default profile over one (BAK-4, HAZ-6)
            raise UserMessage(f"Restore {self._recovery.name}'s profile from a backup first.")
        try:
            info = self._profiles.create(name)
        except ProfileError as error:
            raise UserMessage(str(error).capitalize() + ".") from error
        self._open(info)
        return self.profile_get()

    @_serial
    def prefs_get(self) -> Json:
        return dict(self._prefs)

    @_serial
    def prefs_set(self, preferences: object) -> None:
        data = _obj(preferences, "preferences")
        theme = _one_of(data.get("theme", "auto"), "theme", tuple(THEMES))
        size = _int(data.get("text_size", TEXT_SIZE[2]), "text_size", TEXT_SIZE[0], TEXT_SIZE[1])
        self._prefs = {"theme": theme, "text_size": size}
        if self._storage is not None:
            self._storage.users.set_settings({"ui.theme": THEMES[theme], "ui.text_size_px": size})

    # ------------------------------------------------------------ restore (BAK-3, BAK-4)

    def _restore_target(self) -> ProfileInfo | None:
        """The profile that failed to open (BAK-4), else the open one (BAK-3)."""
        return self._recovery or (self._profile if self._storage is not None else None)

    def _backups(self, info: ProfileInfo) -> BackupManager:
        paths = info.paths
        return BackupManager(paths.user_db, paths.backups_dir, clock=self._clock or SystemClock())

    @_serial
    def restore_list(self) -> Json:
        """The profile to restore and its verified backups, newest first, each with its date
        and counts (the preview); backups that fail their check are left out. While no
        profile is open, `profile` is the one that could not be opened (the page then shows
        the restore screen), or null."""
        info = self._restore_target()
        if info is None:
            return {"profile": None, "backups": []}
        manager = self._backups(info)
        backups = []
        for backup in manager.all():
            preview = manager.preview(backup)
            if preview.ok:
                backups.append(_backup_entry(backup, preview.counts))
        return {"profile": {"id": info.id, "name": info.name}, "backups": backups}

    @_serial
    def restore_backup(self, request: object) -> Json:
        """Replace the profile's user.db with a verified backup, then open it. The swap is a
        rename; the file it replaces is kept (a pre-restore backup when it can still be
        read, and the raw files under backups/replaced-<time>/ either way)."""
        name = _str(_obj(request).get("id"), "id")
        info = self._restore_target()
        if info is None:
            raise UserMessage("There is no profile to restore.")
        manager = self._backups(info)
        backup = next((b for b in manager.all() if b.path.name == name), None)
        if backup is None:
            raise UserMessage("That backup is no longer there.")
        self._close(backup=False)  # the restore takes its own pre-restore backup
        try:
            manager.restore(backup)
        except BackupError as error:
            self._open(info)  # the profile as it was, or the restore screen again
            raise UserMessage(f"That backup could not be restored: {error}") from error
        self._open(info)
        return self.profile_get()

    @_serial
    def restore_recheck(self) -> Json:
        """Check the profile that failed to open again, and open it if it now passes."""
        if self._recovery is not None and self._storage is None:
            self._open(self._recovery)
        return self.profile_get()

    # ------------------------------------------------------------ library

    @_serial
    def library_get(self) -> Json:
        """The course tree with each section's state (Off, Learning now, Covered, Solid)."""
        store = self._store()
        states = {k: v.state for k, v in store.users.section_states().items()}
        skills: dict[str, int] = {}
        # ENG-2: skills with fewer distinct learning problems than the run of correct
        # answers; they are learned after all of them in a row ("pool too small").
        small = self._study().engine().small_learning_pools()
        few: dict[str, list[str]] = {}
        for skill in store.packs.skills():
            if skill.section_id:
                skills[skill.section_id] = skills.get(skill.section_id, 0) + 1
                if skill.id in small:
                    few.setdefault(skill.section_id, []).append(skill.name)
        sections: dict[str, list[Json]] = {}
        for s in sorted(store.packs.sections(), key=lambda s: (s.ord, s.id)):
            sections.setdefault(s.unit_id, []).append(
                {
                    "id": s.id,
                    "title": s.title,
                    "state": states.get(s.id, "off"),
                    "skills": skills.get(s.id, 0),
                    "textbook_ref": s.textbook_ref,
                    "small_pool_skills": few.get(s.id, []),
                }
            )
        units: dict[str, list[Json]] = {}
        for u in sorted(store.packs.units(), key=lambda u: (u.ord, u.id)):
            children = sections.get(u.id, [])
            units.setdefault(u.course_id, []).append(
                {"id": u.id, "title": u.title, "state": _merged(children), "sections": children}
            )
        courses = []
        for c in sorted(store.packs.courses(), key=lambda c: (c.ord, c.title, c.id)):
            children = units.get(c.id, [])
            courses.append(
                {"id": c.id, "title": c.title, "state": _merged(children), "units": children}
            )
        return {"courses": courses}

    @_serial
    def library_set_state(self, request: object) -> Json:
        """Set a section's state; a course or unit sets all its sections (LIB-1). Switching a
        section off never deletes progress (LIB-6)."""
        data = _obj(request)
        target = _str(data.get("id"), "id")
        state = _one_of(data.get("state"), "state", SECTION_STATES)
        store = self._store()
        units = {u.id for u in store.packs.units() if u.id == target or u.course_id == target}
        chosen = [s.id for s in store.packs.sections() if s.id == target or s.unit_id in units]
        if not chosen:
            raise UserMessage("That part of the library is no longer there.")
        for section_id in chosen:
            store.users.set_section_state(section_id, state)  # type: ignore[arg-type]
        return self.library_get()

    @_serial
    def library_card_media(self, request: object) -> Json:
        """The media a card's text refers to, as URLs on the page's own origin (ADR-0017):
        {"files": {reference as written: "/media/user/<file>" or "/media/pack/<id>/<name>"}}.
        References the card has no stored file for are left out."""
        card_id = _str(_obj(request).get("card_id"), "card_id")
        return {"files": card_media(self._store(), card_id)}

    # ------------------------------------------------------------ home and sessions

    @_serial
    def study_today(self) -> Json:
        """Home: today's items and minutes by course and role, hours to keep pace, skills
        behind or set aside, sittings and the planner's notes. Never an overdue count."""
        return to_dict(self._study().today())

    @_serial
    def study_forecast(self) -> Json:
        return to_dict(self._study().forecast())

    @_serial
    def study_start(self, request: object = None) -> Json:
        """Start a session (daily, extra, practice-test) or resume today's."""
        data = _obj(request)
        clean: Json = {"mode": _one_of(data.get("mode", "daily"), "mode", MODES)}
        if data.get("untimed") is not None:
            clean["untimed"] = _bool(data["untimed"], "untimed")
        clean["count"] = _opt_int(data.get("count"), "count", 1, 200)
        clean["exam_id"] = _opt_int(data.get("exam_id"), "exam_id", 0, 2**53)
        clean["timed"] = _bool(data.get("timed", False), "timed")
        return to_dict(self._study().start(clean))

    @_serial
    def study_resume(self) -> Json | None:
        """Today's open session at the same problem (QUE-16), or null."""
        turn = self._study().resume()
        return None if turn is None else to_dict(turn)

    @_serial
    def study_current(self) -> Json:
        return to_dict(self._study().current())

    @_serial
    def study_read_answer(self, request: object) -> Json:
        """The live "We read your answer as ..." preview. Never an attempt."""
        data = _obj(request)
        self._guard(data.get("item_key"))
        preview = self._study().read_answer(
            _str(data.get("value", ""), "value", MAX_ANSWER_CHARS),
            part=_opt_str(data.get("part"), "part"),
            source=_one_of(data.get("source", "text"), "source", SOURCES),  # type: ignore[arg-type]
        )
        out: Json = asdict(preview)
        return out

    @_serial
    def study_submit(self, request: object) -> Json:
        """Grade the answer on screen. A wrong try is committed at once and answered with the
        verdict alone (retry); a final answer is saved in the session and committed on
        continue (ADR-0009)."""
        data = _obj(request)
        clean: Json = {
            "item_key": _opt_str(data.get("item_key"), "item_key"),
            "answers": _answers(data.get("answers")),
            "confidence": _one_of(data.get("confidence", "sure"), "confidence", ("sure", "unsure")),
            "guessed": _bool(data.get("guessed", False), "guessed"),
            "timing": _timing(data.get("timing")),
        }
        if data.get("self_grade") is not None:
            clean["self_grade"] = _one_of(data["self_grade"], "self_grade", SELF_GRADES)
        clean["rubric_ticked"] = _opt_int(data.get("rubric_ticked"), "rubric_ticked", 0, 100)
        clean["error_step"] = _opt_int(data.get("error_step"), "error_step", 0, 1000)
        clean["reason"] = _opt_int(data.get("reason"), "reason", 0, 100)
        return to_dict(self._study().submit(clean))

    @_serial
    def study_show_solution(self, request: object = None) -> Json:
        """Self-graded problems: show the solution (and rubric) before grading. Any other
        problem: after a wrong first try, the solution, ending the problem like Give up."""
        self._guard(_obj(request).get("item_key"))
        return to_dict(self._study().show_solution())

    @_serial
    def study_give_up(self, request: object = None) -> Json:
        data = _obj(request)
        self._guard(data.get("item_key"))
        return to_dict(self._study().give_up(_timing(data.get("timing"))))

    @_serial
    def study_tick(self, request: object) -> Json:
        """Save the active time so far and the typed draft (QUE-16); break reminder."""
        data = _obj(request)
        self._guard(data.get("item_key"))
        return to_dict(
            self._study().tick(
                _int(data.get("active_ms"), "active_ms", 0, 10**10),
                _opt_str(data.get("draft"), "draft", MAX_DRAFT_CHARS),
            )
        )

    @_serial
    def study_next(self, request: object = None) -> Json:
        """Continue: commit the answer on screen if it isn't yet, then the next item."""
        self._guard(_obj(request).get("item_key"))
        return to_dict(self._study().next())

    @_serial
    def study_flag(self, request: object) -> Json:
        """Too easy (E), I was right (D), Report problem (R), Flag, Suspend."""
        data = _obj(request)
        self._guard(data.get("item_key"))
        kind = _one_of(data.get("kind"), "kind", FLAGS)
        return to_dict(self._study().flag(kind, _opt_str(data.get("note"), "note", MAX_NOTE_CHARS)))

    @_serial
    def study_undo(self) -> Json:
        """QUE-15: undo the last answer; the same problem comes back unanswered."""
        return to_dict(self._study().undo())

    @_serial
    def study_rate_flashcard(self, request: object) -> Json:
        """Again/Hard/Good/Easy (1-4), or a typed answer the checker grades."""
        data = _obj(request)
        self._guard(data.get("item_key"))
        return to_dict(
            self._study().rate_flashcard(
                _opt_int(data.get("rating"), "rating", 1, 4),
                answer=_opt_str(data.get("answer"), "answer", MAX_ANSWER_CHARS),
                source=_one_of(data.get("source", "text"), "source", SOURCES),  # type: ignore[arg-type]
                timing=_timing(data.get("timing")),
            )
        )

    @_serial
    def study_end(self) -> Json:
        """End the session now: the summary and tomorrow's forecast."""
        return to_dict(self._study().end())


def _backup_entry(backup: BackupInfo, counts: Mapping[str, int | None]) -> Json:
    return {
        "id": backup.path.name,
        "created_at": backup.created_at,
        "reason": backup.reason,
        "attempts": counts.get("attempts") or 0,
        "last_attempt_at": counts.get("last_attempt_at"),
    }


def _merged(children: Sequence[Mapping[str, Any]]) -> str:
    """A parent's state: its children's common state, or "mixed" (LIB-1 partial mark)."""
    states = {c["state"] for c in children}
    if not states:
        return "off"
    return states.pop() if len(states) == 1 else "mixed"


def public_methods() -> list[str]:
    """The bridge methods, as pywebview exposes them (and the test harness serves them)."""
    return sorted(n for n in dir(Api) if not n.startswith("_") and callable(getattr(Api, n)))
