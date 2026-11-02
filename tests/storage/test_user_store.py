import sqlite3
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest

from core.model import (
    Attempt,
    Card,
    CardMark,
    CardRevision,
    Dispute,
    Exam,
    GradedAnswer,
    PendingCheck,
    Report,
    SessionState,
    ShapeError,
    SkillState,
    TemplateSource,
)
from core.storage import Storage, StorageError
from core.storage.clock import FixedClock, to_ms
from core.storage.rows import ALL_TABLES
from tests.storage import data
from tests.storage.data import some


def snapshot_everything(storage: Storage) -> dict[str, Any]:
    users = storage.users
    return {
        "settings": users.settings(),
        "goals": users.course_goals(),
        "exams": users.exams(),
        "sections": users.section_states(),
        "skills": users.skill_states(),
        "tiers": users.skill_tiers(),
        "shadows": users.skill_shadows(),
        "flashcards": users.flashcard_states(),
        "card_users": users.card_users(),
        "marks": users.card_marks(),
        "checks": users.pending_checks(None),
        "weak": users.weak_spots(),
        "diag": users.diagnostic_sets(),
        "attempts": users.attempts(include_voided=True),
        "reviews": users.review_events(include_voided=True),
        "credits": users.credits(include_voided=True),
        "voids": users.voids(),
        "disputes": users.disputes(),
        "reports": users.reports(),
        "imports": users.imports(),
        "own_cards": users.user_cards(),
        "own_skills": users.user_skills(),
        "session": users.latest_open_session(),
        "counts": users.counts(),
    }


def test_full_history_reads_back_exactly_after_reopen(paths, clock: FixedClock, pack_path) -> None:
    storage = Storage.open(paths, pack_paths=[pack_path], clock=clock, create=True)
    written = data.populate(storage.users, clock)
    before = snapshot_everything(storage)
    storage.close(backup=False)

    reopened = Storage.open(paths, pack_paths=[pack_path], clock=clock)
    try:
        after = snapshot_everything(reopened)
        assert after == before
        assert after["attempts"] == written
        # fixed clock: times and study days are exactly what the clock said
        start = to_ms(data.START)
        first = written[0]
        assert (first.id, first.at, first.study_day) == (1, start, "2026-11-01")
        assert written[1].at == start + 30_000
        assert [a.study_day for a in written[::4]] == ["2026-11-01", "2026-11-02", "2026-11-03"]
        assert first.state_before == {
            "v": 1,
            "rows": [{"table": "card_user", "key": {"card_id": data.CARD}, "row": None}],
        }
        # reviews carry the FSRS state before and after, taken from the attempt's snapshot
        skill_reviews = [r for r in after["reviews"] if r.target_kind == "skill"]
        assert [r.state_before and r.state_before["stability"] for r in skill_reviews] == [
            None,
            2.5,
            6.25,
        ]
        assert [r.state_after["stability"] for r in skill_reviews] == [2.5, 6.25, 15.625]
        assert all(r.rules_version == "r1" for r in after["reviews"])
        # checks created by an attempt point at it; resolving checks point at theirs
        checks = after["checks"]
        assert [c.attempt_id for c in checks] == [written[1].id, written[5].id, written[9].id]
        assert [c.resolved_by for c in checks] == [written[3].id, written[7].id, written[11].id]
        assert after["settings"]["daily.problems"] == 25
        assert after["settings"]["daily.flashcards"] == 50  # default
        assert after["settings"]["custom.flag"] == [1, 2]
        assert after["session"].plan == {"items": [data.CARD, "calc1.mvt.001"], "day": 2}
        assert after["session"].current == {"card_id": data.CARD, "seed": 42}
        assert after["marks"][data.CARD].hidden  # the report hid it
        assert after["counts"]["attempts"] == 12
        assert reopened.packs.card("mine.trig.001") is not None
    finally:
        reopened.close(backup=False)


def test_every_table_matches_its_dataclass(storage: Storage) -> None:
    with storage.db.reading() as conn:
        for record_type, table in ALL_TABLES.items():
            columns = [r["name"] for r in conn.execute(f"PRAGMA table_info({table.name})")]
            assert columns == [f.name for f in fields(record_type)], table.name


def test_append_only_triggers_cover_every_column(storage: Storage) -> None:
    with storage.db.reading() as conn:
        for table in ("attempt", "review_log", "implicit_credit"):
            trigger = conn.execute(
                "SELECT sql FROM sqlite_schema WHERE name = ?", (f"{table}_no_update",)
            ).fetchone()[0]
            listed = trigger.split("UPDATE OF", 1)[1].split(" ON ", 1)[0]
            listed_columns = {c.strip() for c in listed.split(",")}
            columns = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            assert listed_columns == columns - {"voided_by"}, table


def test_logs_are_append_only(storage: Storage, clock: FixedClock) -> None:
    attempts = data.populate(storage.users, clock, days=1)

    def tamper(sql: str) -> None:
        storage.db.write(lambda conn: conn.execute(sql))

    for sql in (
        "UPDATE attempt SET rating = 4 WHERE id = 1",
        "DELETE FROM attempt WHERE id = 1",
        "UPDATE review_log SET rating = 1",
        "DELETE FROM review_log",
        "DELETE FROM implicit_credit",
        "UPDATE import_record SET kind = 'x'",
        "DELETE FROM import_record",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            tamper(sql)
    storage.users.undo_last_answer()
    with pytest.raises(sqlite3.IntegrityError, match="voided once"):
        tamper("UPDATE attempt SET voided_by = NULL WHERE voided_by IS NOT NULL")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        tamper("DELETE FROM attempt_void")
    assert storage.users.attempts(include_voided=True)[:3] == attempts[:3]


def test_readers_cannot_write_and_foreign_keys_hold(storage: Storage) -> None:
    with storage.db.reading() as conn, pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("INSERT INTO setting VALUES ('x', '1', 0)")
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        storage.users.add_dispute(Dispute(attempt_id=999))
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        storage.db.write(
            lambda conn: conn.execute("INSERT INTO setting VALUES ('x', 'not json', 0)")
        )
    with storage.db.reading() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_settings_defaults_and_validation(storage: Storage) -> None:
    users = storage.users
    assert users.get_setting("daily.problems") == 20
    assert users.get_setting("study.day_start_hour") == 4
    assert users.get_setting("not.a.setting", default="d") == "d"
    with pytest.raises(KeyError):
        users.get_setting("not.a.setting")
    for key, bad in [
        ("daily.problems", 0),
        ("daily.problems", 201),
        ("daily.problems", "20"),
        ("study.hints", 1),
        ("credit.partial", "maybe"),
        ("daily.minutes_cap", 5),
        ("queue.easy_days", {"funday": 50}),
        ("queue.stretch_fraction", 0.5),
        ("study.timezone", "Mars/Olympus_Mons"),
        ("study.timezone", "../../etc/passwd"),
    ]:
        with pytest.raises(ShapeError):
            users.set_setting(key, bad)
    users.set_settings(
        {"daily.minutes_cap": None, "queue.stretch_fraction": 0, "ui.theme": "night"}
    )
    assert users.get_setting("daily.minutes_cap") is None
    assert users.get_setting("ui.theme") == "night"


def test_study_day_follows_settings(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    clock.set(to_ms(data.START.replace(hour=8, minute=30)))  # 03:30 EST on Nov 1
    assert users.study_day() == "2026-10-31"
    users.set_setting("study.day_start_hour", 3)
    assert users.study_day() == "2026-11-01"
    users.set_setting("study.timezone", "Asia/Tokyo")
    assert users.study_day() == "2026-11-01"
    start, end = users.day_bounds("2026-11-01")
    assert end - start == 86_400_000


def test_goals_exams_sections_and_marks(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    exam = users.add_exam(Exam(name="Final", at=clock.now_ms() + 1000, sections=("a", "b")))
    assert exam.id == 1
    assert exam.created_at == clock.now_ms()
    assert exam.sections == ("a", "b")
    moved = users.update_exam(replace(exam, at=exam.at + 5))
    assert users.exams() == [moved]
    with pytest.raises(StorageError):
        users.update_exam(replace(exam, id=77))
    users.delete_exam(exam.id)
    assert users.exams() == []
    users.set_section_state("s1", "covered")
    clock.advance(seconds=1)
    state = users.set_section_state("s1", "solid")
    assert users.section_states() == {"s1": state}
    assert state.changed_at == clock.now_ms()
    mark = users.set_card_mark(CardMark(card_id="c1", suspended=True))
    assert users.card_mark("c1") == mark
    assert mark.suspended
    with pytest.raises(ValueError, match="new exam"):
        users.add_exam(replace(exam, id=5))


def test_record_answer_validates_its_input(storage: Storage) -> None:
    users = storage.users
    plain = Attempt(card_id="c", verdict="correct")
    with pytest.raises(ValueError, match="no id"):
        users.record_answer(GradedAnswer(attempt=replace(plain, id=5)))
    with pytest.raises(ValueError, match="snapshots"):
        users.record_answer(GradedAnswer(attempt=replace(plain, state_before={})))
    with pytest.raises(ValueError, match="start the session"):
        users.record_answer(
            GradedAnswer(attempt=plain, session=SessionState(study_day="2026-11-01"))
        )
    with pytest.raises(TypeError):
        users.record_answer(GradedAnswer(attempt=plain, changes=(CardMark(card_id="c"),)))  # type: ignore[arg-type]
    assert users.attempts() == []  # nothing was half-written


def test_a_failing_answer_writes_nothing(storage: Storage) -> None:
    users = storage.users
    bad_check = PendingCheck(skill_id="s", attempt_id=4242)  # dangling: deferred FK fails at commit
    with pytest.raises(sqlite3.IntegrityError):
        users.record_answer(
            GradedAnswer(
                attempt=Attempt(card_id="c", verdict="incorrect"),
                changes=(SkillState(skill_id="s", lapses=1), bad_check),
            )
        )
    assert users.attempts(include_voided=True) == []
    assert users.skill_states() == {}
    assert users.pending_checks(None) == []


def test_atomic_groups_calls_into_one_transaction(storage: Storage) -> None:
    users = storage.users

    def work(store):
        store.set_setting("daily.problems", 30)
        assert store.get_setting("daily.problems") == 30  # reads see the open transaction
        store.apply([SkillState(skill_id="s", reps=1)])
        raise RuntimeError("abort the whole batch")

    with pytest.raises(RuntimeError):
        users.atomic(work)
    assert users.get_setting("daily.problems") == 20
    assert users.skill_states() == {}
    users.atomic(lambda store: store.apply([SkillState(skill_id="s", reps=2)]))
    assert some(users.skill_state("s")).reps == 2


def test_sessions_resume_only_on_their_study_day(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    session = users.start_session(SessionState(study_day=users.study_day(), plan={"q": [1, 2]}))
    assert session.started_at == session.updated_at == clock.now_ms()
    clock.advance(minutes=3)
    saved = users.save_session(replace(session, position=1, active_ms=4000, draft="x+1"))
    assert saved.updated_at == clock.now_ms()
    assert saved.started_at == session.started_at
    assert users.resumable_session() == saved
    clock.advance(days=1)  # past the 4 AM rollover
    assert users.resumable_session() is None
    assert users.latest_open_session() == saved  # still there for the queue to rebuild from
    ended = users.end_session(some(session.id))
    assert ended.ended_at == clock.now_ms()
    assert users.latest_open_session() is None
    with pytest.raises(ValueError, match="start the session"):
        users.save_session(replace(session, id=None))
    with pytest.raises(StorageError):
        users.save_session(replace(session, id=99))
    with pytest.raises(StorageError):
        users.end_session(99)


def test_disputes_reports_and_imports(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    attempt = users.record_answer(GradedAnswer(attempt=Attempt(card_id="c", verdict="incorrect")))
    dispute = users.add_dispute(Dispute(attempt_id=some(attempt.id), raw_input="2/4"))
    assert users.disputes("open") == [dispute]
    clock.advance(seconds=5)
    upheld = users.resolve_dispute(some(dispute.id), "upheld", note="equivalent")
    assert upheld.resolved_at == clock.now_ms()
    assert users.disputes("open") == []
    report = users.add_report(Report(card_id="c", reason="bad key"), hide=False)
    assert users.card_mark("c") is None
    assert users.resolve_report(some(report.id), "fixed").status == "fixed"
    with pytest.raises(StorageError):
        users.resolve_report(99, "fixed")


def test_own_cards_are_versioned_and_retired_never_deleted(storage: Storage) -> None:
    users = storage.users
    card = Card(id="mine.1", question_md="Q", rev=2)
    users.put_user_content(card, CardRevision(card_id="mine.1", rev=2, changed_at=5))
    with pytest.raises(StorageError, match="only go up"):
        users.put_user_content(replace(card, rev=1))
    users.put_user_content(replace(card, rev=3, question_md="Q2"))
    users.retire_user_card("mine.1")
    assert users.user_card("mine.1") == replace(card, rev=3, question_md="Q2", status="retired")
    assert "mine.1" not in {r.id for r in storage.packs.card_refs()}
    with pytest.raises(StorageError):
        users.retire_user_card("nope")
    with pytest.raises(TypeError):
        users.put_user_content(CardMark(card_id="x"))  # type: ignore[arg-type]


def test_database_files_live_in_the_profile(storage: Storage, paths) -> None:
    names = sorted(p.name for p in Path(paths.root).iterdir())
    assert {"user.db", "user.db-wal", "user.db-shm", "user.db.lock", "media", "backups"} <= set(
        names
    )


def test_own_template_sources(storage: Storage, clock: FixedClock) -> None:
    users = storage.users
    assert users.user_template("t.001") is None
    users.put_user_content(TemplateSource(id="t.001", source_md="## Card t.001\nv1"))
    first = some(users.user_template("t.001"))
    assert first.updated_at == clock.now_ms()  # stamped
    clock.advance(seconds=1)
    users.put_user_content(TemplateSource(id="t.001", source_md="## Card t.001\nv2"))
    users.put_user_content(TemplateSource(id="a.001", source_md="## Card a.001"))
    assert [t.id for t in users.user_templates()] == ["a.001", "t.001"]
    assert users.template_sources() == {"a.001": "## Card a.001", "t.001": "## Card t.001\nv2"}
    assert some(users.user_template("t.001")).updated_at == clock.now_ms()


def test_check_reasons_are_stored_and_undone_with_their_answer(storage: Storage) -> None:
    users = storage.users
    asked = users.record_answer(
        GradedAnswer(
            attempt=Attempt(card_id="c", verdict="incorrect"),
            changes=(PendingCheck(skill_id="s", attempt_id=-1, reason="Why: a miss on s"),),
        )
    )
    (check,) = users.pending_checks()
    assert (check.attempt_id, check.reason) == (asked.id, "Why: a miss on s")
    assert some(asked.state_after)["rows"][0]["row"]["reason"] == "Why: a miss on s"
    users.undo_last_answer()
    assert users.pending_checks(None) == []
