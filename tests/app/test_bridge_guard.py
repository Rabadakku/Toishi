"""Bridge hardening (ARC-12, HAZ-4) for what runs off the Mac: the allow-list over pywebview
6.2.1's real dispatcher, the navigation and sender checks, the settings, and the loopback
server's Host check. The Cocoa subclasses themselves need the Mac (scripts/check.sh app).
"""

import http.client
import json
import queue
import socket
import sys
import threading
import time
import types
from collections.abc import Iterator
from typing import Any

import pytest
import webview
import webview.util

from app import shell
from app.api import Api, public_methods


class FakeWindow:
    """The parts of webview.Window that js_bridge_call touches."""

    def __init__(self, api: object) -> None:
        self._js_api = api
        self._functions: dict[str, Any] = {}
        self._callbacks: dict[str, Any] = {}
        self.returned: queue.Queue[str] = queue.Queue()

    def evaluate_js(self, script: str, callback: Any = None) -> None:
        self.returned.put(script)


@pytest.fixture
def dispatch() -> Iterator[Any]:
    """Whatever pywebview's dispatcher is right now, restored afterwards."""
    util: Any = webview.util
    saved = util.js_bridge_call, shell._original_js_bridge_call
    yield lambda *args: util.js_bridge_call(*args)
    util.js_bridge_call, shell._original_js_bridge_call = saved
    sys.modules.pop("webview.platforms.fakeplatform", None)


def call(dispatch: Any, window: FakeWindow, name: str, params: Any, call_id: str = "123") -> None:
    dispatch(window, name, params, call_id)
    time.sleep(0.2)  # pywebview runs the method on a new thread


ATTACKS: list[tuple[str, Any]] = [
    ("_close", []),
    ("__setattr__", ["_error", "set from the page"]),
    ("__init__", []),
]


def test_unguarded_pywebview_runs_private_and_dunder_members(dispatch: Any) -> None:
    # Why the guard exists: pywebview 6.2.1 dispatches any attribute the page names.
    original = shell._original_js_bridge_call or webview.util.js_bridge_call
    if original is shell.guarded_js_bridge_call:
        pytest.skip("guard already installed in this process")
    api = Api()
    lock = api._lock
    closed: list[bool] = []
    api._close = lambda **_: closed.append(True)  # type: ignore[method-assign]
    window = FakeWindow(api)
    call(original, window, "_close", [])
    assert closed == [True]
    call(original, window, "__setattr__", ["_error", "set from the page"])
    assert api._error == "set from the page"
    call(original, window, "__init__", [])
    assert api._lock is not lock  # the constructor ran again


def test_guard_runs_only_public_api_methods(dispatch: Any) -> None:
    shell.install_bridge_guard()
    api = Api()
    lock = api._lock
    closed: list[bool] = []
    api._close = lambda **_: closed.append(True)  # type: ignore[method-assign]
    window = FakeWindow(api)
    for name, params in ATTACKS:
        call(dispatch, window, name, params)
    odd: list[Any] = ["_open_last", "study_today.__globals__", "ping.__call__", "nope", "", 7]
    for name in odd:
        call(dispatch, window, name, [])
    for control in ("pywebviewStateUpdate", "pywebviewMoveWindow", "pywebviewAsyncCallback"):
        call(dispatch, window, control, {"key": "x", "value": 1})
    assert closed == []
    assert api._error is None
    assert api._lock is lock
    assert window.returned.empty()  # dropped calls send nothing back

    call(dispatch, window, "ping", ["hi"])
    assert '"pong: hi"' in window.returned.get(timeout=5)


def test_guard_rejects_call_ids_that_could_inject_script(dispatch: Any) -> None:
    shell.install_bridge_guard()
    window = FakeWindow(Api())
    for bad in ('1"]);alert(1);//', "", "x" * 65, "1 2", "<"):
        call(dispatch, window, "ping", ["hi"], bad)
    assert window.returned.empty()
    for good in ("123456789", "8e-7", "0.5"):
        call(dispatch, window, "ping", ["hi"], good)
        assert good in window.returned.get(timeout=5)


def test_allow_list_is_the_bridge_contract() -> None:
    assert shell.bridge_methods(Api()) == set(public_methods())
    assert not any(n.startswith("_") for n in shell.bridge_methods(Api()))


def test_guard_is_rebound_where_a_platform_module_imported_the_dispatcher(
    dispatch: Any,
) -> None:
    # webview.platforms.cocoa does `from webview.util import js_bridge_call`.
    fake = types.ModuleType("webview.platforms.fakeplatform")
    fake.js_bridge_call = webview.util.js_bridge_call  # type: ignore[attr-defined]
    sys.modules[fake.__name__] = fake
    shell.install_bridge_guard()
    shell.install_bridge_guard()  # idempotent: the original is kept, not the guard
    assert fake.js_bridge_call is shell.guarded_js_bridge_call
    util: Any = webview.util
    assert util.js_bridge_call is shell.guarded_js_bridge_call
    assert shell._original_js_bridge_call is not shell.guarded_js_bridge_call


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("http://127.0.0.1:5123/index.html", True),
        ("http://127.0.0.1:5123/index.html#/library", True),
        ("http://127.0.0.1:5123/", True),
        ("http://127.0.0.1:5124/index.html", False),  # another local server
        ("http://localhost:5123/index.html", False),
        ("https://127.0.0.1:5123/index.html", False),
        ("http://user@127.0.0.1:5123/", False),
        ("http://127.0.0.1.evil.example:5123/", False),
        ("file:///Users/sam/Library/Application%20Support/user.db", False),
        ("https://example.com/", False),
        ("about:blank", False),
        ("data:text/html,<script>1</script>", False),
        ("javascript:alert(1)", False),
        ("http://127.0.0.1:99999/", False),
    ],
)
def test_navigation_stays_on_the_apps_own_page(url: str, allowed: bool) -> None:
    assert shell.navigation_allowed(url, "http://127.0.0.1:5123") is allowed


def test_no_navigation_before_the_server_has_a_port() -> None:
    assert shell.navigation_allowed("http://127.0.0.1:5123/", None) is False


@pytest.mark.parametrize(
    ("main", "scheme", "host", "port", "allowed"),
    [
        (True, "http", "127.0.0.1", 5123, True),
        (False, "http", "127.0.0.1", 5123, False),  # a subframe
        (True, "http", "127.0.0.1", 5124, False),
        (True, "file", "", 0, False),
        (True, "https", "example.com", 443, False),
    ],
)
def test_bridge_messages_only_from_the_main_frame_of_the_app(
    main: bool, scheme: str, host: str, port: int, allowed: bool
) -> None:
    origin = shell.app_origin(5123)
    assert shell.bridge_sender_allowed(main, scheme, host, port, origin) is allowed


def test_file_urls_downloads_and_external_links_are_off() -> None:
    saved = dict(webview.settings)
    try:
        shell.harden_settings()
        assert webview.settings["ALLOW_FILE_URLS"] is False
        assert webview.settings["ALLOW_DOWNLOADS"] is False
        assert webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] is False
    finally:
        webview.settings.update(saved)


# ---------------------------------------------------------------- Host header on the server


@pytest.fixture
def server() -> int:
    """pywebview's real server with our loopback adapter (as webview.start starts it)."""
    shell.install_loopback_server()
    _address, _root, _server = shell._http.BottleServer.start_server([str(__file__)], None)
    port = shell._server_port
    assert port is not None
    for _attempt in range(100):
        try:
            socket.create_connection((shell.LOOPBACK, port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.05)
    return port


def get(port: int, host: str | None) -> int:
    conn = http.client.HTTPConnection(shell.LOOPBACK, port, timeout=10)
    try:
        conn.putrequest("GET", "/" + __file__.rsplit("/", 1)[1], skip_host=True)
        if host is not None:
            conn.putheader("Host", host)
        conn.endheaders()
        return conn.getresponse().status
    finally:
        conn.close()


def test_server_answers_only_its_own_host(server: int) -> None:
    assert shell.app_origin() == f"http://127.0.0.1:{server}"
    assert get(server, f"127.0.0.1:{server}") == 200
    for host in (
        f"localhost:{server}",
        "evil.example",
        "127.0.0.1",
        f"127.0.0.1:{server + 1}",
        None,
    ):
        assert get(server, host) == 403, host


def test_host_check_alone() -> None:
    seen: list[str] = []

    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        seen.append(environ["PATH_INFO"])
        start_response("200 OK", [])
        return [b"ok"]

    checked = shell.HostCheck(app, 5123)
    status: list[str] = []
    body = checked(
        {"HTTP_HOST": "127.0.0.1:5123", "PATH_INFO": "/a"}, lambda s, h: status.append(s)
    )
    assert body == [b"ok"]
    body = checked({"HTTP_HOST": "attacker:5123", "PATH_INFO": "/b"}, lambda s, h: status.append(s))
    assert body == [b"Forbidden"]
    assert status == ["200 OK", "403 Forbidden"]
    assert seen == ["/a"]


def test_guarded_dispatch_is_thread_safe_under_load(dispatch: Any) -> None:
    # Bridge methods run on worker threads (AGENTS.md rule 6): many at once stay correct.
    shell.install_bridge_guard()
    window = FakeWindow(Api())
    threads = [
        threading.Thread(target=dispatch, args=(window, "ping", [str(n)], str(n)))
        for n in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    replies = [window.returned.get(timeout=5) for _ in range(20)]
    assert sorted(r for r in replies if "pong" in r) == sorted(replies)
    assert {json.dumps(f"pong: {n}") in "".join(replies) for n in range(20)} == {True}
