"""Native window shell: the only module that imports pywebview (ADR-0001).

Everything toolkit-specific lives here, so moving to another shell (the PySide6
fallback in spike/qt) means rewriting this file and nothing else.
"""

import importlib
import json
import logging
import platform
import re
import socket
import socketserver
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import webview
import webview.util
from webview._version import __version__ as PYWEBVIEW_FOUND
from webview.menu import Menu, MenuAction

from app import csp_compat
from app.media import MediaMiddleware, MediaSource

SHELL_NAME = f"pywebview {PYWEBVIEW_FOUND}"
# pywebview's server and window modules, patched below (typed loosely: bottle has no types).
_http: Any = importlib.import_module("webview.http")
_window: Any = importlib.import_module("webview.window")
LOOPBACK = "127.0.0.1"
PAGE_EVENT = "toishi:menu"  # the page listens for this CustomEvent (web/src/lib/menu.ts)
_EVENT_NAME = re.compile(r"^[a-z][a-z-]{0,40}$")
_log = logging.getLogger(__name__)
# Native Edit menu items sent to the first responder (WKWebView, then MathLive's field).
EDIT_ITEMS: tuple[tuple[str, str, str], ...] = (("Undo", "undo:", "z"), ("Redo", "redo:", "Z"))


class ShellWindow(Protocol):
    """What callers may do with the window. Kept small on purpose."""

    def destroy(self) -> None: ...

    def create_confirmation_dialog(self, title: str, message: str) -> bool: ...

    def send_page_event(self, name: str) -> None: ...


@dataclass(frozen=True, slots=True)
class MenuItem:
    title: str
    action: Callable[[ShellWindow], None]


@dataclass(frozen=True, slots=True)
class WindowSpec:
    title: str
    entry: Path  # index.html of the built web UI; served over http://127.0.0.1, never file://
    width: int = 1100
    height: int = 780
    min_size: tuple[int, int] = (720, 520)
    hidden: bool = False
    focus: bool = True
    debug: bool = False  # Web Inspector; must stay False in release builds (pywebview #1866)
    app_menu: Sequence[MenuItem] = ()
    edit_menu: Sequence[MenuItem] = ()  # added below Undo / Redo in the native Edit menu


def page_event_script(name: str) -> str:
    """The script that tells the page a menu item was chosen (no eval: run_js runs it raw)."""
    if not _EVENT_NAME.match(name):
        raise ValueError(f"bad page event name {name!r}")
    detail = json.dumps(name)
    return f"window.dispatchEvent(new CustomEvent({json.dumps(PAGE_EVENT)}, {{detail: {detail}}}))"


class _Window:
    """ShellWindow over a pywebview window."""

    def __init__(self, window: Any) -> None:
        self._window = window

    def destroy(self) -> None:
        self._window.destroy()

    def create_confirmation_dialog(self, title: str, message: str) -> bool:
        return bool(self._window.create_confirmation_dialog(title, message))

    def send_page_event(self, name: str) -> None:
        self._window.run_js(page_event_script(name))


# ---------------------------------------------------------------- loopback-only HTTP server
#
# macOS asks "find devices on your local network?" when an app resolves a name on the local
# network. pywebview's stdlib-based server did two such lookups at launch:
# - http.server.HTTPServer.server_bind() calls socket.getfqdn(host);
# - uuid.uuid1() (the server's and every evaluate_js call's id) falls back to
#   uuid.getnode(), whose _arp_getnode() runs gethostbyname(gethostname()): the Mac's
#   "<name>.local", a multicast DNS query, when the stdlib's _uuid helper is unavailable.
# The server below binds 127.0.0.1 by number and names itself by that number; ids are random.


class LoopbackWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)  # bind only: no HTTPServer.getfqdn() lookup
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)
        self.setup_environ()


class _QuietHandler(WSGIRequestHandler):
    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        pass


def free_loopback_port() -> int:
    """A free port on 127.0.0.1, without resolving "localhost"."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((LOOPBACK, 0))
        port: int = sock.getsockname()[1]
        return port


_server_port: int | None = None  # the page's port, picked when pywebview starts its server


def _pick_server_port() -> int:
    global _server_port
    _server_port = free_loopback_port()
    return _server_port


def app_origin(port: int | None = None) -> str | None:
    """The page's own origin, http://127.0.0.1:<port> (None before the server started)."""
    port = _server_port if port is None else port
    return None if port is None else f"http://{LOOPBACK}:{port}"


class HostCheck:
    """WSGI app: answers 403 to a request whose Host is not exactly 127.0.0.1:<port>, so a
    page on another name that resolves to this machine (DNS rebinding) reads nothing."""

    def __init__(self, app: Callable[..., Any], port: int) -> None:
        self._app = app
        self._host = f"{LOOPBACK}:{port}"

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Any:
        if environ.get("HTTP_HOST") != self._host:
            body = b"Forbidden"
            start_response(
                "403 Forbidden",
                [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))],
            )
            return [body]
        return self._app(environ, start_response)


_media_source: MediaSource | None = None  # what /media/... serves (ADR-0017); None = nothing


class _LoopbackAdapter(_http.ThreadedAdapter):  # type: ignore[misc]
    """pywebview's server adapter (a bottle ServerAdapter) on LoopbackWSGIServer, with the
    card media route (app/media.py) in front of pywebview's own routes."""

    def run(self, handler: Any) -> None:
        handler_class = _QuietHandler if self.quiet else WSGIRequestHandler
        app = handler if _media_source is None else MediaMiddleware(handler, _media_source)
        port = int(self.port)
        server = make_server(
            LOOPBACK, port, HostCheck(app, port), LoopbackWSGIServer, handler_class=handler_class
        )
        server.serve_forever()


class _RandomIds:
    """Stands in for the uuid module inside pywebview: uuid1() without the MAC address."""

    uuid1 = staticmethod(uuid.uuid4)

    def __getattr__(self, name: str) -> Any:
        return getattr(uuid, name)


def install_loopback_server(media: MediaSource | None = None) -> None:
    """Make pywebview's HTTP server loopback-only with no hostname lookups (idempotent), and
    have it answer /media/... from `media` (read when the server starts)."""
    global _media_source
    _media_source = media
    _http.ThreadedAdapter = _LoopbackAdapter
    _http._get_random_port = _pick_server_port
    _http.uuid = _RandomIds()
    _window.uuid1 = uuid.uuid4


# ---------------------------------------------------------------- CSP compatibility

_patched = False


def _install_csp_compat() -> None:
    """Swap pywebview's `new Function` API stubs for closures (see app/csp_compat.py)."""
    global _patched
    if _patched:
        return
    csp_compat.check_version(PYWEBVIEW_FOUND)
    # Annotated `-> str` in pywebview, but it returns (js_code, finish_script).
    original: Callable[..., Any] = webview.util.load_js_files

    def load_js_files(window: Any, platform: str) -> tuple[str, str]:
        js_code, finish_script = original(window, platform)
        return csp_compat.patch_bridge_js(js_code), finish_script

    webview.util.load_js_files = load_js_files  # type: ignore[assignment]
    _patched = True


def _return_results_without_eval(window: Any) -> None:
    """Deliver bridge results with run_js (raw) instead of evaluate_js (eval-wrapped)."""
    evaluate_js = window.evaluate_js

    def csp_safe_evaluate_js(script: str, callback: Callable[..., Any] | None = None) -> Any:
        if callback is None and csp_compat.is_bridge_return(script):
            return window.run_js(script)
        return evaluate_js(script, callback)

    window.evaluate_js = csp_safe_evaluate_js


# ---------------------------------------------------------------- bridge hardening (ARC-12)
#
# HAZ-4: pywebview 6.2.1 dispatches any attribute name the page sends (`_close`,
# `__setattr__`, `__init__`, dotted paths), never checks which frame or origin sent it, and
# re-injects the bridge into whatever page the window navigates to. So:
# - the dispatcher runs only the api's public methods (and none of pywebview's own control
#   messages: the app uses no window.state, DOM events, drag-move or async callbacks);
# - on macOS the message must come from the main frame of the app's own origin;
# - the window never navigates away from the app's origin, file URLs are off, and
#   target=_blank links are not handed to the browser (they go through the same policy);
# - the page itself ignores dropped files (web/src/main.ts).

_CALL_ID = re.compile(r"^[0-9A-Za-z.+-]{1,64}$")  # pywebview's ids: (Math.random() + "").slice(2)
_original_js_bridge_call: Callable[..., Any] | None = None


_public_names: dict[type, frozenset[str]] = {}


def bridge_methods(api: object) -> frozenset[str]:
    """What the page may call: the api's public methods (app.api.public_methods for Api)."""
    cls = type(api)
    names = _public_names.get(cls)
    if names is None:
        names = frozenset(
            n for n in dir(cls) if not n.startswith("_") and callable(getattr(cls, n))
        )
        _public_names[cls] = names
    return names


def bridge_call_allowed(api: object, func_name: object, call_id: object) -> bool:
    return (
        isinstance(func_name, str)
        and func_name in bridge_methods(api)
        and isinstance(call_id, str)
        and _CALL_ID.match(call_id) is not None
    )


def guarded_js_bridge_call(window: Any, func_name: Any, param: Any, value_id: Any) -> None:
    """pywebview's js_bridge_call, but only for an allowed method and a well-formed call id
    (the id is pasted into the script that returns the result). Anything else is dropped."""
    if not bridge_call_allowed(getattr(window, "_js_api", None), func_name, value_id):
        _log.warning("bridge: dropped a call to %r", str(func_name)[:80])
        return
    if _original_js_bridge_call is None:
        raise RuntimeError("the bridge guard is not installed")
    _original_js_bridge_call(window, func_name, param, value_id)


def install_bridge_guard() -> None:
    """Put guarded_js_bridge_call in place of pywebview's dispatcher, also where a platform
    module imported it by name (webview.platforms.cocoa). Idempotent."""
    global _original_js_bridge_call
    util: Any = webview.util
    if _original_js_bridge_call is None and util.js_bridge_call is not guarded_js_bridge_call:
        _original_js_bridge_call = util.js_bridge_call
    util.js_bridge_call = guarded_js_bridge_call
    if platform.system() == "Darwin":
        importlib.import_module("webview.platforms.cocoa")
    for name, module in list(sys.modules.items()):
        if name.startswith("webview.platforms.") and hasattr(module, "js_bridge_call"):
            loaded: Any = module
            loaded.js_bridge_call = guarded_js_bridge_call


def navigation_allowed(url: str, origin: str | None) -> bool:
    """Only the app's own page may load in the window: http://127.0.0.1:<port>/..."""
    if origin is None:
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    return (
        parts.scheme == "http"
        and parts.hostname == LOOPBACK
        and f"http://{LOOPBACK}:{port}" == origin
        and not parts.username
        and not parts.password
    )


def bridge_sender_allowed(
    is_main_frame: bool, scheme: str, host: str, port: int, origin: str | None
) -> bool:
    """A bridge message must come from the main frame of the app's own origin."""
    return is_main_frame and origin is not None and f"{scheme}://{host}:{port}" == origin


def harden_settings() -> None:
    """pywebview settings for the app's window (read when the window is created)."""
    webview.settings["ALLOW_FILE_URLS"] = False
    webview.settings["ALLOW_DOWNLOADS"] = False
    # target=_blank: load in the window (and so through the navigation policy, which
    # refuses it) instead of opening the student's browser.
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False


_cocoa_guards: tuple[Any, Any] | None = None


def _install_cocoa_guards() -> None:
    """macOS: subclass pywebview's script message handler and navigation delegate (plain
    Python attributes of cocoa.BrowserView, read when a window is created) to check the
    sender's frame and origin and to cancel navigations off the app's origin."""
    global _cocoa_guards
    if platform.system() != "Darwin" or _cocoa_guards is not None:
        return
    cocoa: Any = importlib.import_module("webview.platforms.cocoa")
    objc: Any = importlib.import_module("objc")
    webkit: Any = importlib.import_module("WebKit")
    cancel = getattr(webkit, "WKNavigationActionPolicyCancel", 0)

    class MasteryJSBridge(cocoa.BrowserView.JSBridge):  # type: ignore[misc]
        def userContentController_didReceiveScriptMessage_(
            self: Any, controller: Any, message: Any
        ) -> None:
            frame = message.frameInfo()
            sender = frame.securityOrigin()
            if not bridge_sender_allowed(
                bool(frame.isMainFrame()),
                str(sender.protocol()),
                str(sender.host()),
                int(sender.port()),
                app_origin(),
            ):
                _log.warning("bridge: dropped a message from another frame or origin")
                return
            objc.super(MasteryJSBridge, self).userContentController_didReceiveScriptMessage_(
                controller, message
            )

    class MasteryBrowserDelegate(cocoa.BrowserView.BrowserDelegate):  # type: ignore[misc]
        def webView_decidePolicyForNavigationAction_decisionHandler_(
            self: Any, webview_: Any, action: Any, handler: Any
        ) -> None:
            url = action.request().URL()
            if url is None or not navigation_allowed(str(url.absoluteString()), app_origin()):
                _log.warning("navigation off the app's origin cancelled")
                handler(cancel)
                return
            objc.super(
                MasteryBrowserDelegate, self
            ).webView_decidePolicyForNavigationAction_decisionHandler_(webview_, action, handler)

    cocoa.BrowserView.JSBridge = MasteryJSBridge
    cocoa.BrowserView.BrowserDelegate = MasteryBrowserDelegate
    _cocoa_guards = (MasteryJSBridge, MasteryBrowserDelegate)


# ---------------------------------------------------------------- native Edit menu


def _install_edit_menu(items: Sequence[MenuAction]) -> None:
    """macOS: pywebview's default Edit menu has no Undo / Redo. Add them (sent to the first
    responder, so Cmd+Z reaches the focused field) and our own items below a separator."""
    if platform.system() != "Darwin":
        return
    cocoa: Any = importlib.import_module("webview.platforms.cocoa")

    view = cocoa.BrowserView
    original = getattr(view, "_mastery_add_edit_menu", None) or view._add_edit_menu
    view._mastery_add_edit_menu = original

    def add_edit_menu(self: Any, main_menu: Any) -> None:
        original(self, main_menu)
        edit = main_menu.itemAtIndex_(1).submenu()
        for index, (title, action, key) in enumerate(EDIT_ITEMS):
            edit.insertItemWithTitle_action_keyEquivalent_atIndex_(title, action, key, index)
        edit.insertItem_atIndex_(cocoa.AppKit.NSMenuItem.separatorItem(), len(EDIT_ITEMS))
        if items:
            edit.addItem_(cocoa.AppKit.NSMenuItem.separatorItem())
            self._process_menu_items(list(items), edit)

    view._add_edit_menu = add_edit_menu


def run(
    spec: WindowSpec,
    api: object,
    on_started: Callable[[ShellWindow], None] | None = None,
    *,
    media: MediaSource | None = None,
) -> None:
    """Open the window and run the GUI loop until it closes. Main thread only.

    `on_started` runs on a background thread once the loop is up. `media` is where the page's
    card images, sounds and fonts come from (served at /media/..., ADR-0017).
    """
    _install_csp_compat()
    install_loopback_server(media)
    install_bridge_guard()
    harden_settings()
    _install_cocoa_guards()
    window = webview.create_window(
        spec.title,
        url=str(spec.entry),
        js_api=api,
        width=spec.width,
        height=spec.height,
        min_size=spec.min_size,
        hidden=spec.hidden,
        focus=spec.focus,
        text_select=True,
    )
    if window is None:
        raise RuntimeError("pywebview did not create a window")
    _return_results_without_eval(window)
    shell_window = _Window(window)

    def wrap(item: MenuItem) -> MenuAction:
        return MenuAction(item.title, lambda: item.action(shell_window))

    _install_edit_menu([wrap(item) for item in spec.edit_menu])
    menu = [Menu("__app__", [wrap(item) for item in spec.app_menu])] if spec.app_menu else []
    started = (lambda: on_started(shell_window)) if on_started else None
    webview.start(
        started,
        debug=spec.debug,
        http_server=True,
        private_mode=True,
        menu=menu,
    )
