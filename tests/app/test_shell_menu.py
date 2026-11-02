"""The macOS app menu: "About <app>" appears once (pywebview adds it, we must not add another)."""

from pathlib import Path
from typing import Any

import pytest

from app import main, shell
from core import grader


def test_pywebview_app_menu_already_has_the_standard_about_item() -> None:
    cocoa = Path(str(shell._http.__file__)).parent / "platforms" / "cocoa.py"
    source = cocoa.read_text()
    # Pinned 6.2.1: _add_app_menu always starts with About, then our app_menu items, then
    # Services. So anything we pass in app_menu comes after a standard About item.
    assert "def _add_app_menu(self, mainMenu, custom_items=None):" in source
    assert "self.localization['cocoa.menu.about']" in source
    assert "'orderFrontStandardAboutPanel:'" in source


def test_the_app_adds_no_second_about_item(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entry = tmp_path / "index.html"
    entry.write_text("")
    seen: dict[str, shell.WindowSpec] = {}

    class FakeApi:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def _open_last(self) -> None:
            pass

        def _storage_or_none(self) -> None:
            return None

    def fake_run(spec: shell.WindowSpec, api: object, *args: Any, **kwargs: Any) -> None:
        seen["spec"] = spec

    monkeypatch.setattr(main, "index_html", lambda: entry)
    monkeypatch.setattr(main, "Api", FakeApi)
    monkeypatch.setattr(main, "ProfileManager", lambda: None)
    monkeypatch.setattr(grader, "warm_up", lambda: None)
    monkeypatch.setattr(main, "shutdown", lambda api: None)
    monkeypatch.setattr(shell, "run", fake_run)

    assert main.main([]) == 0
    spec = seen["spec"]
    titles = [item.title for item in (*spec.app_menu, *spec.edit_menu)]
    assert [t for t in titles if t.lower().startswith("about")] == []
    assert titles == ["Undo Last Answer"]  # the Edit menu item still comes from us
