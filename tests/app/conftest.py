"""Fixtures for the bridge tests: a real profile with the Test pack, through app.api.Api."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from app.api import Api
from app.packs import shipped_packs
from core import cards, grader
from core.model import CourseSetup
from core.storage import ProfileManager


@pytest.fixture(scope="session")
def test_pack() -> list[Path]:
    """The Test pack's database (compiled into build/packs when stale)."""
    return [p for p in shipped_packs() if p.stem == "test"]


@pytest.fixture
def api(tmp_path: Path, test_pack: list[Path]) -> Iterator[Api]:
    """A first-run Api over a temporary data folder (no profile yet)."""
    bridge = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=lambda: test_pack)
    yield bridge
    bridge._close(backup=False)


@pytest.fixture
def studying(api: Api) -> Iterator[Api]:
    """A profile with the Test pack's first section Learning now and its course set up to
    start today (wave 2: the planner serves the courses that have a schedule)."""
    api.profile_create({"name": "Sam"})
    course = api.library_get()["courses"][0]
    first = course["units"][0]["sections"][0]
    api.library_set_state({"id": first["id"], "state": "learning"})
    users = api._store().users
    users.set_course_setup(
        CourseSetup(course_id=course["id"], start=date.fromisoformat(users.study_day()))
    )
    yield api
    grader.shutdown()
    cards.shutdown()
