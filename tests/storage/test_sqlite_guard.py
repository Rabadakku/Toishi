"""DEV-7: no database is opened with a SQLite that has the WAL-reset corruption bug.

The bug (3.7.0 to 3.51.2) was fixed in 3.51.3 and backported to 3.50.7 and 3.44.6.
"""

import sqlite3
from pathlib import Path

import pytest

from core.health import health_check
from core.storage import Storage, UnsafeSQLiteError
from core.storage.connection import sqlite_is_safe
from core.storage.profiles import ProfilePaths


@pytest.mark.parametrize(
    ("version", "safe"),
    [
        ((3, 51, 3), True),  # the fix
        ((3, 51, 4), True),
        ((3, 52, 0), True),
        ((3, 53, 1), True),
        ((4, 0, 0), True),
        ((3, 51, 2), False),  # the last affected release
        ((3, 51, 0), False),
        ((3, 50, 7), True),  # backport
        ((3, 50, 9), True),
        ((3, 50, 6), False),
        ((3, 44, 6), True),  # backport
        ((3, 44, 10), True),
        ((3, 44, 5), False),
        ((3, 45, 3), False),  # between the backported lines: not fixed
        ((3, 49, 9), False),
        ((3, 43, 99), False),
        ((3, 37, 0), False),  # the old floor
    ],
)
def test_version_comparison_knows_the_fix_and_its_backports(
    version: tuple[int, int, int], safe: bool
) -> None:
    assert sqlite_is_safe(version) is safe


def fake_sqlite(monkeypatch: pytest.MonkeyPatch, version: tuple[int, int, int]) -> str:
    text = ".".join(map(str, version))
    monkeypatch.setattr(sqlite3, "sqlite_version_info", version)
    monkeypatch.setattr(sqlite3, "sqlite_version", text)
    return text


def test_storage_refuses_an_unsafe_sqlite_and_names_its_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = ProfilePaths(tmp_path / "p")
    Storage.open(paths, create=True).close(backup=False)
    before = paths.user_db.read_bytes()
    text = fake_sqlite(monkeypatch, (3, 51, 2))
    with pytest.raises(UnsafeSQLiteError, match=rf"SQLite {text} .*3\.51\.3"):
        Storage.open(paths)
    with pytest.raises(UnsafeSQLiteError):
        Storage.open(ProfilePaths(tmp_path / "new"), create=True)
    assert paths.user_db.read_bytes() == before  # untouched
    assert not (tmp_path / "new" / "user.db").exists()  # nothing created


@pytest.mark.parametrize("version", [(3, 50, 7), (3, 44, 6), (3, 51, 3)])
def test_storage_opens_with_a_fixed_or_backported_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: tuple[int, int, int]
) -> None:
    fake_sqlite(monkeypatch, version)
    with Storage.open(ProfilePaths(tmp_path / "p"), create=True) as storage:
        assert storage.users.counts()["attempts"] == 0


def test_self_test_reports_the_version_and_fails_on_an_unsafe_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = sqlite3.sqlite_version
    check = next(c for c in health_check().checks if c.name == "sqlite")
    assert check.ok
    assert f"SQLite {real}" in check.detail
    text = fake_sqlite(monkeypatch, (3, 50, 6))
    check = next(c for c in health_check().checks if c.name == "sqlite")
    assert not check.ok
    assert f"SQLite {text}" in check.detail
