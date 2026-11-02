from collections.abc import Iterator
from pathlib import Path

import pytest

from core.storage import Storage, build_pack
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths
from tests.storage import data


@pytest.fixture
def clock() -> FixedClock:
    return data.new_clock()


@pytest.fixture
def paths(tmp_path: Path) -> ProfilePaths:
    return ProfilePaths(tmp_path / "profile")


@pytest.fixture
def pack_path(tmp_path: Path) -> Path:
    path = tmp_path / "packs" / "calc1.db"
    build_pack(path, data.PACK_INFO, data.pack_records())
    return path


@pytest.fixture
def storage(paths: ProfilePaths, clock: FixedClock, pack_path: Path) -> Iterator[Storage]:
    opened = Storage.open(paths, pack_paths=[pack_path], clock=clock, create=True)
    yield opened
    opened.close(backup=False)
