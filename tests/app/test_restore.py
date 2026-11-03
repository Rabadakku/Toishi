"""In-app restore (BAK-3, BAK-4, BAK-7; HAZ-6) through app.api.Api over a real profile.

A profile that fails its integrity check, or can't be opened at all, is offered its verified
backups (newest first) and never replaced by a new default profile; a restore gives back
exactly the progress the backup holds.
"""

import shutil
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.api import Api, UserMessage
from app.main import _key_answers
from core.storage import ProfileManager
from core.storage.backups import backup_name
from core.storage.connection import connect
from tests.app.test_bridge_contract import ts_fields
from tests.storage.data import dump_state


def study_some(api: Api, answers: int = 4) -> None:
    """Answer problems through the bridge, right and wrong, and leave the session open."""
    turn = api.study_start({"mode": "daily"})
    done = 0
    for _ in range(60):
        if turn["type"] != "problem" or done >= answers:
            return
        problem = turn["problem"]
        key = problem["item_key"]
        if problem["kind"] == "flashcard":
            api.study_rate_flashcard({"item_key": key, "rating": 3})
        elif problem["kind"] != "example":
            card = api._store().packs.card(problem["card"]["id"])
            assert card is not None
            if problem["card"]["self_graded"]:
                api.study_give_up({"item_key": key, "timing": {"active_ms": 1000}})
            else:
                typed = _key_answers(card)
                if done % 2:
                    typed = [{**a, "value": "987654321"} for a in typed]
                result = api.study_submit({"item_key": key, "answers": typed})
                if result["outcome"] in ("retry", "invalid", "self-grade"):  # wrong: give up
                    api.study_give_up({"item_key": key, "timing": {"active_ms": 1000}})
            done += 1
        turn = api.study_next({"item_key": key})


def snapshot(db: Path) -> dict[str, list[tuple[object, ...]]]:
    conn = connect(db, mode="ro")
    try:
        return dump_state(conn)
    finally:
        conn.close()


def smash(db: Path) -> None:
    for side in ("-wal", "-shm"):
        db.with_name(db.name + side).unlink(missing_ok=True)
    with db.open("r+b") as handle:
        handle.seek(4096)
        handle.write(b"\xff" * 8192)


def relaunch(api: Api, data: Path) -> Api:
    again = Api(profiles=ProfileManager(data), pack_paths=api._pack_paths)
    again._open_last()
    return again


@pytest.fixture
def saved(studying: Api, tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Sam's profile with answers, closed with its on-close backup; its exact contents."""
    study_some(studying)
    db = studying._store().paths.user_db
    studying._close(backup=True)
    return db, snapshot(db)


def test_a_corrupted_profile_restores_to_identical_progress(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    db, before = saved
    assert len(before["attempt"]) >= 4
    smash(db)
    api = relaunch(studying, tmp_path / "data")
    try:
        state = api.profile_get()
        assert state["profile"] is None
        assert "integrity check" in str(state["error"])
        listed = api.restore_list()
        assert listed["profile"]["name"] == "Sam"
        assert [b["reason"] for b in listed["backups"]] == ["close"]
        latest = listed["backups"][0]
        assert latest["attempts"] == len([a for a in before["attempt"] if a[-1] is None])

        # HAZ-6: never a new default profile over the damaged one.
        with pytest.raises(UserMessage, match="Restore Sam"):
            api.profile_create({"name": "Sam 2"})
        assert [p.name for p in ProfileManager(tmp_path / "data").list()] == ["Sam"]

        restored = api.restore_backup({"id": latest["id"]})
        assert restored["profile"]["name"] == "Sam"
        assert restored["error"] is None
        assert api.restore_list()["profile"]["name"] == "Sam"  # now the open profile
        assert snapshot(db) == before  # identical progress
        resumed = api.study_resume()  # the open session comes back
        assert resumed is not None
        assert resumed["type"] == "problem"
    finally:
        api._close(backup=False)
    kept = list((db.parent / "backups").glob("replaced-*/user.db"))
    assert len(kept) == 1  # the damaged file is kept, never deleted


def test_newest_verified_backup_comes_first_and_bad_ones_are_not_offered(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    db, before = saved
    backups = db.parent / "backups"
    older = next(backups.glob("user-*-close.db"))
    shutil.copyfile(older, backups / backup_name(1, "manual"))  # an older good copy
    bad = backups / backup_name(4_102_444_800_000, "periodic")  # newest, but damaged
    bad.write_bytes(b"\0" * 8192)
    smash(db)
    api = relaunch(studying, tmp_path / "data")
    try:
        listed = api.restore_list()["backups"]
        assert [b["id"] for b in listed] == [older.name, backup_name(1, "manual")]
        assert [b["created_at"] for b in listed] == sorted(
            (b["created_at"] for b in listed), reverse=True
        )
        for name in (bad.name, "../user.db", "nope.db"):
            with pytest.raises(UserMessage):
                api.restore_backup({"id": name})
        assert api.profile_get()["profile"] is None  # still on the restore screen
        api.restore_backup({"id": listed[0]["id"]})
        assert snapshot(db) == before
    finally:
        api._close(backup=False)


def test_a_missing_user_db_on_a_new_mac_restores_from_its_backups(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    # BAK-7: the data folder copied to a new Mac without a usable user.db.
    _db, before = saved
    new_mac = tmp_path / "new-mac"
    shutil.copytree(tmp_path / "data", new_mac)
    profile_dir = next((new_mac / "profiles").iterdir())
    for name in ("user.db", "user.db-wal", "user.db-shm"):
        (profile_dir / name).unlink(missing_ok=True)
    api = relaunch(studying, new_mac)
    try:
        assert api.profile_get()["profile"] is None
        assert "could not be opened" in str(api.profile_get()["error"])
        listed = api.restore_list()
        assert listed["profile"]["name"] == "Sam"
        state = api.restore_backup({"id": listed["backups"][0]["id"]})
        assert state["profile"]["name"] == "Sam"
        assert snapshot(profile_dir / "user.db") == before
    finally:
        api._close(backup=False)


def test_recheck_opens_a_profile_that_passes_again(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    db, before = saved
    aside = db.with_name("elsewhere.db")
    db.replace(aside)
    api = relaunch(studying, tmp_path / "data")
    try:
        assert api.restore_recheck()["profile"] is None
        aside.replace(db)
        state = api.restore_recheck()
        assert state["profile"]["name"] == "Sam"
        assert state["error"] is None
        assert snapshot(db) == before
    finally:
        api._close(backup=False)


def test_restoring_while_open_keeps_a_pre_restore_backup(studying: Api) -> None:
    # BAK-3: any backup, any time; the state it replaces is backed up first.
    study_some(studying, 2)
    store = studying._store()
    taken = store.backups.create("manual")
    db = store.paths.user_db
    expected = snapshot(taken.path)
    study_some(studying, 2)
    later = snapshot(db)
    assert later != expected
    state = studying.restore_backup({"id": taken.path.name})
    assert state["profile"]["name"] == "Sam"
    assert snapshot(db) == expected
    reasons = [b["reason"] for b in studying.restore_list()["backups"]]
    assert "pre-restore" in reasons
    pre = next(p for p in (db.parent / "backups").glob("user-*-pre-restore.db"))
    assert snapshot(pre) == later


def test_nothing_to_restore_on_first_run(api: Api) -> None:
    assert api.restore_list() == {"profile": None, "backups": []}
    with pytest.raises(UserMessage):
        api.restore_backup({"id": "user-x.db"})
    assert api.restore_recheck()["profile"] is None


def test_an_unsafe_sqlite_is_an_error_not_a_restore(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 51, 2))
    monkeypatch.setattr(sqlite3, "sqlite_version", "3.51.2")
    api = relaunch(studying, tmp_path / "data")
    state = api.profile_get()
    assert state["profile"] is None
    assert "3.51.2" in str(state["error"])
    assert api.restore_list()["profile"] is None  # no backup would help


def test_restore_payloads_match_bridge_types(
    studying: Api, saved: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    api = relaunch(studying, tmp_path / "data")
    try:
        listed = api.restore_list()
        assert set(listed) == ts_fields("BackupList")
        assert listed["backups"]
        for entry in listed["backups"]:
            assert set(entry) == ts_fields("BackupEntry")
        assert set(api.restore_recheck()) == ts_fields("ProfileState")
    finally:
        api._close(backup=False)
