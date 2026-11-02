"""Fixtures for page tests: serve app/web_dist on 127.0.0.1 and watch every request.

Browser: TOISHI_BROWSER=webkit|chromium|firefox (default: webkit on macOS, the
closest thing to WKWebView; chromium on Linux, which has it preinstalled).
"""

import functools
import os
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import (
    Browser,
    ConsoleMessage,
    Error,
    Page,
    Playwright,
    Request,
    Route,
    WebSocket,
    sync_playwright,
)

from app.paths import WEB_DIST_DIR

BROWSER_ENV = "TOISHI_BROWSER"
REQUIRE_UI_ENV = "TOISHI_REQUIRE_UI"  # set by scripts/check.sh: a missing build fails, not skips
LOCAL_SCHEMES = {"data", "blob", "about"}

CSP_RECORDER = """
window.__cspViolations = [];
document.addEventListener('securitypolicyviolation', (e) => {
  window.__cspViolations.push({directive: e.violatedDirective, blocked: e.blockedURI});
});
"""


HERE = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if HERE in item.path.parents:
            item.add_marker(pytest.mark.ui)


@pytest.fixture(scope="session")
def web_dist() -> Path:
    if not (WEB_DIST_DIR / "index.html").is_file():
        message = "app/web_dist not built: run npm --prefix web ci && npm --prefix web run build"
        if os.environ.get(REQUIRE_UI_ENV) == "1":
            pytest.fail(message)
        pytest.skip(message)
    return WEB_DIST_DIR


class LocalServer:
    """http://127.0.0.1:<port>/ serving web_dist, plus in-memory extra routes."""

    def __init__(self, root: Path) -> None:
        self.extra: dict[str, tuple[str, bytes]] = {}
        extra = self.extra

        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self) -> None:
                path = urlsplit(self.path).path
                if path in extra:
                    content_type, body = extra[path]
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                super().do_GET()

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self._httpd = ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(Handler, directory=str(root))
        )
        self.origin = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def add(self, path: str, body: str, content_type: str = "text/javascript") -> str:
        self.extra[path] = (content_type, body.encode())
        return self.origin + path

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


@pytest.fixture(scope="session")
def server(web_dist: Path) -> Iterator[LocalServer]:
    srv = LocalServer(web_dist)
    yield srv
    srv.close()


def browser_name() -> str:
    default = "webkit" if sys.platform == "darwin" else "chromium"
    name = os.environ.get(BROWSER_ENV, default)
    if name not in {"webkit", "chromium", "firefox"}:
        raise pytest.UsageError(f"{BROWSER_ENV}={name!r}: use webkit, chromium or firefox")
    return name


@pytest.fixture(scope="session")
def playwright() -> Iterator[Playwright]:
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Iterator[Browser]:
    b = getattr(playwright, browser_name()).launch()
    yield b
    b.close()


@dataclass
class Guarded:
    """A page plus everything it tried to do that it should not."""

    page: Page
    requests: list[str] = field(default_factory=list)
    outbound: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)

    def csp_violations(self) -> list[dict[str, str]]:
        result: list[dict[str, str]] = self.page.evaluate("window.__cspViolations || []")
        return result

    def assert_clean(self) -> None:
        assert self.outbound == [], f"requests left 127.0.0.1: {self.outbound}"
        assert self.csp_violations() == []
        assert self.console_errors == []


def is_local(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme in LOCAL_SCHEMES or parts.hostname == "127.0.0.1"


@pytest.fixture
def guarded(browser: Browser) -> Iterator[Guarded]:
    context = browser.new_context()
    page = context.new_page()
    g = Guarded(page)

    def route(r: Route) -> None:
        if is_local(r.request.url):
            r.continue_()
        else:
            g.outbound.append(r.request.url)
            r.abort()

    def on_request(request: Request) -> None:
        g.requests.append(request.url)

    def on_websocket(ws: WebSocket) -> None:
        g.outbound.append(ws.url)

    def on_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            g.console_errors.append(message.text)

    def on_page_error(error: Error) -> None:
        g.console_errors.append(str(error))

    context.route("**/*", route)
    page.on("request", on_request)
    page.on("websocket", on_websocket)
    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    context.add_init_script(CSP_RECORDER)
    yield g
    context.close()
