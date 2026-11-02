from collections.abc import Iterator
from pathlib import Path

import pytest

from core.cards import shutdown as sweep_shutdown
from core.cards.sweep import runner
from core.grader import shutdown as grader_shutdown
from core.grader import warm_up
from core.storage import FixedClock, Storage, UserStore
from core.storage.profiles import ProfilePaths

FIXTURES = Path(__file__).parent / "fixtures"
START = 1_793_577_600_000  # 2026-11-01T00:00:00Z


@pytest.fixture(scope="session", autouse=True)
def workers() -> Iterator[None]:
    """Mastery Problem notes are self-checked by the grader; keep one warm worker."""
    warm_up()
    runner().start()
    yield
    sweep_shutdown()
    grader_shutdown()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(START)


@pytest.fixture
def storage(tmp_path: Path, clock: FixedClock) -> Iterator[Storage]:
    opened = Storage.open(ProfilePaths(tmp_path / "profile"), clock=clock, create=True)
    yield opened
    opened.close(backup=False)


@pytest.fixture
def store(storage: Storage) -> UserStore:
    return storage.users


def fixture(name: str) -> Path:
    return FIXTURES / name
