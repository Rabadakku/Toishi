from collections.abc import Iterator

import pytest
from hypothesis import settings

from core.grader import shutdown, warm_up

# Property tests write nothing to disk (no .hypothesis/ database in the repo).
settings.register_profile("grader", database=None, deadline=None)
settings.load_profile("grader")


@pytest.fixture(scope="session", autouse=True)
def checker_worker() -> Iterator[None]:
    """One warm worker process for the whole run; stopped at the end."""
    warm_up()
    yield
    shutdown()
