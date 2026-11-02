import sys
import tomllib
from pathlib import Path

import platformdirs
import pytest
from platformdirs.macos import MacOS

import core
from core.health import DEFAULT_PROBES, health_check
from core.paths import DATA_DIR_ENV, LEGACY_BUNDLE_IDS, app_data_dir

ROOT = Path(__file__).resolve().parents[1]


def test_version_matches_pyproject() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert core.version() == core.__version__ == project["version"]


def test_health_check_passes_on_this_machine() -> None:
    report = health_check()
    failed = [c for c in report.checks if not c.ok]
    assert report.ok, failed
    assert [c.name for c in report.checks] == list(DEFAULT_PROBES)


def test_failing_probe_is_reported_not_raised() -> None:
    def broken() -> str:
        raise ValueError("boom")

    report = health_check({"fine": lambda: "ok", "broken": broken})
    assert not report.ok
    assert report.as_dict()["checks"] == [
        {"name": "fine", "ok": True, "detail": "ok", "ms": pytest.approx(0, abs=50)},
        {
            "name": "broken",
            "ok": False,
            "detail": "ValueError: boom",
            "ms": pytest.approx(0, abs=50),
        },
    ]


def test_runtime_is_gil_python_314_not_system_python() -> None:
    assert sys.version_info[:2] == (3, 14)
    assert sys._is_gil_enabled(), "free-threaded builds are not supported (pywebview #1739)"
    if sys.platform == "darwin":
        assert not sys.executable.startswith("/usr/bin/"), "use uv's Python, not /usr/bin/python3"


def test_data_dir_follows_macos_convention() -> None:
    mac = MacOS(core.BUNDLE_ID, appauthor=False)
    expected = Path("~/Library/Application Support").expanduser() / core.BUNDLE_ID
    assert Path(mac.user_data_dir) == expected


def _fake_user_data_dir(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    """Point platformdirs at `root`, so no test touches the real data folder."""
    monkeypatch.setattr(platformdirs, "user_data_dir", lambda name, **_: str(root / name))


def test_data_dir_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    assert app_data_dir() == tmp_path
    monkeypatch.delenv(DATA_DIR_ENV)
    _fake_user_data_dir(monkeypatch, tmp_path / "support")
    assert app_data_dir().name == core.BUNDLE_ID


def test_data_dir_adopts_the_earlier_names_folder_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The app was renamed: the first run moves the old data folder to the new name."""
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    _fake_user_data_dir(monkeypatch, tmp_path)
    legacy = tmp_path / LEGACY_BUNDLE_IDS[0]
    (legacy / "profiles").mkdir(parents=True)
    (legacy / "profiles" / "user.db").write_text("data")
    path = app_data_dir()
    assert path == tmp_path / core.BUNDLE_ID
    assert (path / "profiles" / "user.db").read_text() == "data"
    assert not legacy.exists()
    legacy.mkdir()  # an old folder that appears later is left alone
    assert app_data_dir() == path
    assert legacy.exists()
