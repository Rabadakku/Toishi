import pytest

from tests import offline


def pytest_configure(config: pytest.Config) -> None:
    offline.install()


def pytest_unconfigure(config: pytest.Config) -> None:
    offline.uninstall()
