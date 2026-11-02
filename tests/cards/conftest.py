from collections.abc import Iterator
from pathlib import Path

import pytest

from core.cards import shutdown as sweep_shutdown
from core.cards.sweep import runner
from core.grader import shutdown as grader_shutdown
from core.grader import warm_up
from core.storage import FixedClock, Storage
from core.storage.profiles import ProfilePaths

START = 1_793_577_600_000  # 2026-11-01T00:00:00Z


@pytest.fixture(scope="session", autouse=True)
def workers() -> Iterator[None]:
    """One warm checker worker and one warm template sweep process for the whole run."""
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
