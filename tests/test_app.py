import inspect
import json
import re
from pathlib import Path

import pytest
import webview.util
from webview._version import __version__ as pywebview_version

import core
from app import csp_compat, main
from app.api import MAX_PING_CHARS, Api, SelfTestInbox
from tests.pywebview_support import load_pywebview_js


def test_ping_echoes_and_validates() -> None:
    api = Api()
    assert api.ping(r"\frac{1}{2}") == r"pong: \frac{1}{2}"
    with pytest.raises(TypeError):
        api.ping(42)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="longer"):
        api.ping("x" * (MAX_PING_CHARS + 1))


def test_app_info_is_json_serializable() -> None:
    info = Api(self_test=SelfTestInbox()).app_info()
    assert json.loads(json.dumps(info)) == info
    assert info["version"] == core.version() == Api().version()
    assert info["self_test"] is True
    assert Api().app_info()["self_test"] is False


def test_self_test_report_reaches_inbox() -> None:
    inbox = SelfTestInbox()
    assert inbox.wait(0.01) is None
    Api(self_test=inbox).report_self_test({"ok": True, "checks": []})
    assert inbox.wait(0.01) == {"ok": True, "checks": []}
    with pytest.raises(TypeError):
        Api(self_test=inbox).report_self_test("ok")


BRIDGE_TS = (Path(__file__).parents[1] / "web/src/lib/bridge.ts").read_text()


@pytest.mark.xfail(
    "course_settings_get" not in BRIDGE_TS,
    reason="wave 2: the bridge methods changed on the Python side; web/src/lib/bridge.ts "
    "(W2) is merged on its own, and then the names must match again",
    strict=True,
)
def test_public_api_matches_typescript_bridge() -> None:
    public = sorted(n for n, _ in inspect.getmembers(Api, inspect.isfunction) if n[0] != "_")
    declared = sorted(set(re.findall(r"^\s+(\w+)\(.*\): Promise<", BRIDGE_TS, re.MULTILINE)))
    assert public == declared


@pytest.mark.parametrize(
    ("env", "frozen", "expected"),
    [
        ({}, False, False),
        ({main.DEBUG_ENV: "1"}, False, True),
        ({main.DEBUG_ENV: "1"}, True, False),  # never in a built .app (pywebview #1866)
    ],
)
def test_debug_only_in_dev_runs(env: dict[str, str], frozen: bool, expected: bool) -> None:
    assert main.debug_enabled(env, frozen) is expected


def test_self_test_result_needs_page_and_core() -> None:
    good_page = {"ok": True, "checks": []}
    assert main.self_test_result(good_page, {"ok": True}, {})["ok"] is True
    assert main.self_test_result(good_page, {"ok": False}, {})["ok"] is False
    missing = main.self_test_result(None, {"ok": True}, {})
    assert missing["ok"] is False
    assert missing["page"]["error"] == "no report from the page"


def test_main_reports_missing_web_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(main, "index_html", lambda: tmp_path / "index.html")
    assert main.main(["--self-test"]) == 2
    assert "npm --prefix web run build" in capsys.readouterr().err


# --- CSP compatibility patches against the real, pinned pywebview -----------------


def test_pinned_pywebview_is_the_patched_version() -> None:
    assert pywebview_version == csp_compat.PYWEBVIEW_VERSION
    csp_compat.check_version(pywebview_version)
    with pytest.raises(csp_compat.PywebviewCompatError):
        csp_compat.check_version("6.3.0")


def test_patch_removes_the_only_dynamic_code_in_pywebview_js() -> None:
    js_code, finish = load_pywebview_js()
    assert "new Function" in js_code
    patched = csp_compat.patch_bridge_js(js_code)
    assert "new Function" not in patched
    assert "eval(" not in patched + finish
    with pytest.raises(csp_compat.PywebviewCompatError):
        csp_compat.patch_bridge_js(patched)


def test_return_prefix_matches_pywebview_bridge_call() -> None:
    source = inspect.getsource(webview.util.js_bridge_call)
    assert "window.evaluate_js(" in source
    assert "f'" + csp_compat.BRIDGE_RETURN_PREFIX in source
    assert csp_compat.is_bridge_return('window.pywebview._returnValuesCallbacks["ping"]["1"]({})')
    assert not csp_compat.is_bridge_return("document.title")


def test_health_flag_checks_core_without_a_window(capsys: pytest.CaptureFixture[str]) -> None:
    assert main.main(["--health"]) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("HEALTH ")
    assert json.loads(line.removeprefix("HEALTH "))["ok"] is True
