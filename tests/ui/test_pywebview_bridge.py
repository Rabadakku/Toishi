"""pywebview's Cocoa bridge, emulated in a browser under the shipped CSP.

Runs pywebview 6.2.1's real injected JS and its real Python dispatcher
(webview.util.js_bridge_call) against the real built page and app.api.Api.
Only the two native entry points are stubbed:
- WKScriptMessageHandler (`window.webkit.messageHandlers.jsBridge`) -> an outbox
  array that this test drains and feeds to js_bridge_call;
- `evaluateJavaScript` -> a <script src> served from 127.0.0.1, so the code runs
  in the page world under the page's CSP, as it does in WKWebView. (page.evaluate
  is not used for this: Chromium's DevTools evaluation lets eval past the CSP.)

This proves both halves of app/csp_compat.py: without them the bridge is dead
under our CSP; with them the page's full self-test passes over the bridge.
"""

import contextlib
import itertools
import json
import queue
import time
from collections.abc import Callable
from typing import Any

import webview.util

from app import csp_compat, shell
from app.api import Api, SelfTestInbox
from tests.pywebview_support import finish_script, load_pywebview_js
from tests.ui.conftest import Guarded, LocalServer

TRANSPORT_STUB = """
window.__bridgeOutbox = [];
window.webkit = {messageHandlers: {jsBridge: {postMessage: (m) => window.__bridgeOutbox.push(m)}}};
"""


class FakeCocoaWindow:
    """The parts of webview.Window that js_bridge_call touches."""

    def __init__(self, api: object) -> None:
        self._js_api = api
        self._functions: dict[str, Any] = {}
        self._callbacks: dict[str, Any] = {}
        self.outgoing: queue.Queue[str] = queue.Queue()

    def evaluate_js(self, script: str, callback: Any = None) -> None:
        # Window.evaluate_js wraps the script in eval(...) before evaluateJavaScript.
        self.outgoing.put(f"eval({json.dumps(script)});")

    def run_js(self, script: str) -> None:
        self.outgoing.put(script)


class EmulatedBridge:
    _ids = itertools.count()

    def __init__(self, server: LocalServer, guarded: Guarded, window: FakeCocoaWindow) -> None:
        self.server, self.page, self.window = server, guarded.page, window

    def run_js(self, script: str) -> None:
        """What WKWebView.evaluateJavaScript does: run raw code in the page world."""
        url = self.server.add(f"/__test__/run/{next(self._ids)}.js", script)
        self.page.add_script_tag(url=url)

    def inject_pywebview(self, api: object, *, patched: bool) -> None:
        js_code, finish = load_pywebview_js()
        self.run_js(TRANSPORT_STUB)
        self.run_js(csp_compat.patch_bridge_js(js_code) if patched else js_code)
        self.run_js(finish_script(finish, api))

    def pump(self, done: Callable[[], bool], timeout_s: float = 15) -> bool:
        """Carry messages both ways until done() or the timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            for raw in self.page.evaluate("window.__bridgeOutbox.splice(0)"):
                body = json.loads(raw)
                window: Any = self.window  # duck-types webview.Window
                webview.util.js_bridge_call(window, body["funcName"], body["params"], body["id"])
            with contextlib.suppress(queue.Empty):
                self.run_js(self.window.outgoing.get(timeout=0.05))
            if done():
                return True
        return False


def script_src_violations(guarded: Guarded) -> list[dict[str, str]]:
    return [v for v in guarded.csp_violations() if v["directive"].startswith("script-src")]


def test_unpatched_pywebview_api_is_blocked_by_our_csp(
    server: LocalServer, guarded: Guarded
) -> None:
    bridge = EmulatedBridge(server, guarded, FakeCocoaWindow(Api()))
    guarded.page.goto(f"{server.origin}/index.html")
    bridge.inject_pywebview(Api(), patched=False)
    assert guarded.page.evaluate("typeof window.pywebview.api.ping") == "undefined"
    assert script_src_violations(guarded), "expected CSP to block pywebview's new Function"


def test_eval_wrapped_return_values_are_blocked_and_rerouting_fixes_it(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    window = FakeCocoaWindow(Api())
    bridge = EmulatedBridge(server, guarded, window)
    page.goto(f"{server.origin}/index.html")
    bridge.inject_pywebview(Api(), patched=True)
    # Fire and forget: page.evaluate would otherwise wait on the (possibly never settling) promise.
    call = "() => { window.pywebview.api.ping('a').then((v) => { window.__reply = v; }); }"

    page.evaluate(call)
    arrived = bridge.pump(lambda: page.evaluate("window.__reply !== undefined"), timeout_s=2)
    assert not arrived, "eval-wrapped result should be blocked by the CSP"
    assert script_src_violations(guarded)

    shell._return_results_without_eval(window)  # what app.shell does to the real window
    page.evaluate(call)
    assert bridge.pump(lambda: page.evaluate("window.__reply !== undefined"))
    assert page.evaluate("window.__reply") == "pong: a"


def test_page_self_test_passes_over_emulated_pywebview_bridge(
    server: LocalServer, guarded: Guarded
) -> None:
    inbox = SelfTestInbox()
    api = Api(self_test=inbox)
    window = FakeCocoaWindow(api)
    shell._return_results_without_eval(window)
    bridge = EmulatedBridge(server, guarded, window)

    guarded.page.goto(f"{server.origin}/index.html")
    bridge.inject_pywebview(api, patched=True)
    assert bridge.pump(lambda: inbox.wait(0) is not None), "page never reported its self-test"

    report = inbox.wait(0)
    assert report is not None
    assert report["ok"] is True, report["checks"]
    assert {c["name"] for c in report["checks"]} == {
        "csp",
        "katex",
        "katex-fonts",
        "mathlive",
        "bridge",
    }
    guarded.assert_clean()
