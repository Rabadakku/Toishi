"""app.api.Api over a real profile: first run, library, preferences, guards, messages."""

from pathlib import Path

import pytest

from app.api import Api, UserMessage, public_methods
from core.storage import ProfileManager


def test_first_run_asks_for_a_name_then_opens_the_profile(api: Api, tmp_path: Path) -> None:
    assert api.profile_get() == {"profile": None, "error": None, "warnings": []}
    with pytest.raises(UserMessage, match="profile first"):
        api.study_today()
    state = api.profile_create({"name": "  Sam  "})
    assert state["profile"]["name"] == "Sam"
    with pytest.raises(UserMessage, match="already open"):
        api.profile_create({"name": "Other"})
    api._close(backup=False)

    # Next launch opens the profile used last, with the shipped pack attached.
    again = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=api._pack_paths)
    again._open_last()
    try:
        assert again.profile_get()["profile"]["name"] == "Sam"
        assert again.library_get()["courses"]
    finally:
        again._close(backup=False)


def test_a_profile_open_elsewhere_is_reported_not_raised(api: Api, tmp_path: Path) -> None:
    api.profile_create({"name": "Sam"})
    second = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=api._pack_paths)
    second._open_last()
    state = second.profile_get()
    assert state["profile"] is None
    assert "open in another" in str(state["error"])


def test_library_states_and_parents_set_their_sections(api: Api) -> None:
    api.profile_create({"name": "Sam"})
    course = api.library_get()["courses"][0]
    sections = [s for u in course["units"] for s in u["sections"]]
    assert course["state"] == "off"
    assert {s["state"] for s in sections} == {"off"}
    assert all(s["skills"] > 0 for s in sections)

    after = api.library_set_state({"id": sections[0]["id"], "state": "learning"})
    course = after["courses"][0]
    assert course["state"] == "mixed"  # LIB-1: mixed children show a partial mark
    after = api.library_set_state({"id": course["id"], "state": "covered"})
    assert {s["state"] for u in after["courses"][0]["units"] for s in u["sections"]} == {"covered"}
    with pytest.raises(ValueError, match="state"):
        api.library_set_state({"id": course["id"], "state": "maybe"})
    with pytest.raises(UserMessage):
        api.library_set_state({"id": "no such section", "state": "off"})


def test_preferences_live_in_the_profile(api: Api, tmp_path: Path) -> None:
    api.prefs_set({"theme": "night", "text_size": 22})  # before a profile: memory only
    assert api.prefs_get() == {"theme": "night", "text_size": 22}
    api.profile_create({"name": "Sam"})
    assert api.prefs_get() == {"theme": "auto", "text_size": 18}
    api.prefs_set({"theme": "day", "text_size": 20})
    api._close(backup=False)
    again = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=api._pack_paths)
    again._open_last()
    try:
        assert again.prefs_get() == {"theme": "day", "text_size": 20}
    finally:
        again._close(backup=False)
    with pytest.raises(ValueError, match="theme"):
        api.prefs_set({"theme": "pink", "text_size": 20})


def test_requests_are_checked_never_trusted(studying: Api) -> None:
    with pytest.raises(TypeError):
        studying.study_start("daily")
    with pytest.raises(ValueError, match="mode"):
        studying.study_start({"mode": "cram"})
    with pytest.raises(TypeError):
        studying.study_start({"count": "20"})
    turn = studying.study_start({"mode": "daily"})
    key = turn["problem"]["item_key"]
    with pytest.raises(TypeError):
        studying.study_submit({"item_key": key, "answers": "x"})
    with pytest.raises(ValueError, match="longer"):
        studying.study_submit({"item_key": key, "answers": [{"value": "1" * 5000}]})
    with pytest.raises(ValueError, match="choice"):
        studying.study_diagnose({"item_key": key, "choice": "blame the teacher"})
    with pytest.raises(TypeError):
        studying.study_tick({"item_key": key, "active_ms": True})


def test_a_stale_page_cannot_act_on_another_item(studying: Api) -> None:
    turn = studying.study_start({})
    key = turn["problem"]["item_key"]
    with pytest.raises(UserMessage, match="no longer on screen"):
        studying.study_next({"item_key": key + "-old"})
    with pytest.raises(UserMessage, match="no longer on screen"):
        studying.study_hint({"item_key": "nope"})
    assert studying.study_current()["problem"]["item_key"] == key


def test_queue_refusals_become_user_messages(studying: Api) -> None:
    with pytest.raises(UserMessage, match="Press Start"):
        studying.study_current()
    turn = studying.study_start({})
    while turn["problem"]["kind"] != "problem":
        key = turn["problem"]["item_key"]
        if turn["problem"]["kind"] == "flashcard":
            studying.study_rate_flashcard({"item_key": key, "rating": 3})
        turn = studying.study_next({"item_key": key})
    with pytest.raises(UserMessage):
        studying.study_diagnose({"choice": "cant-tell"})  # nothing missed yet
    resumed = studying.study_resume()
    assert resumed is not None
    assert resumed["problem"]["item_key"] == turn["problem"]["item_key"]


def test_bridge_methods_are_the_api_public_methods() -> None:
    names = public_methods()
    assert "study_submit" in names
    assert "profile_create" in names
    assert not any(n.startswith("_") for n in names)
