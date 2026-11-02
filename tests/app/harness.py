"""Test-only harness: the built page with the REAL core behind its bridge, no pywebview.

`BridgeHarness` serves app/web_dist on 127.0.0.1 and answers `POST /__bridge/<method>`
(a JSON list of arguments) by calling that public method of app.api.Api, each request on
its own thread as pywebview does. `shim_script()` is the init script a Playwright test
injects to define `window.pywebview.api` over that endpoint. It exists only in tests:
the shipped page never contains it (tests/ui/test_real_session.py checks).

A refused call answers {"error": {"name", "message"}}; the shim rejects with an Error of
that name, exactly like pywebview's bridge, so `userMessage()` in bridge.ts works the same.

GET /media/... is answered by the app's own route (app.media.respond over the open profile), so
the page's images, sounds and card CSS come through the code the app ships (ADR-0017).
"""

import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from app.api import Api, public_methods
from app.media import PREFIX as MEDIA_PREFIX
from app.media import ProfileMedia, respond

BRIDGE_PREFIX = "/__bridge/"
MAX_BODY = 1_000_000

SHIM = """
(() => {
  const methods = %(methods)s;
  const call = async (name, args) => {
    const reply = await fetch('%(prefix)s' + name, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(args),
    });
    const body = await reply.json();
    if (body.error) {
      const error = new Error(body.error.message);
      error.name = body.error.name;
      throw error;
    }
    return body.value;
  };
  const api = {};
  for (const name of methods) api[name] = (...args) => call(name, args);
  window.pywebview = {api};
  const ready = () => window.dispatchEvent(new CustomEvent('pywebviewready'));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
"""


def shim_script() -> str:
    return SHIM % {"methods": json.dumps(public_methods()), "prefix": BRIDGE_PREFIX}


class BridgeHarness:
    """http://127.0.0.1:<port>/ serving `root`, with the bridge endpoint over `api`."""

    def __init__(self, root: Path, api: Api) -> None:
        self.api = api
        self.calls: list[str] = []
        self.errors: list[str] = []
        allowed = set(public_methods())
        harness = self
        media = ProfileMedia(api._storage_or_none)
        self.media_requests: list[tuple[str, int]] = []  # (path, status)

        class Handler(SimpleHTTPRequestHandler):
            def serve_media(self, method: str) -> None:
                path = unquote(urlsplit(self.path).path)  # as the real server hands it over
                reply = respond(method, path, media, self.headers.get("Range"))
                harness.media_requests.append((path, reply.status))
                self.send_response(reply.status)
                for name, value in reply.headers:
                    self.send_header(name, value)
                self.end_headers()
                for chunk in reply.body:
                    self.wfile.write(chunk)

            def do_GET(self) -> None:
                if urlsplit(self.path).path.startswith(MEDIA_PREFIX):
                    self.serve_media("GET")
                else:
                    super().do_GET()

            def do_HEAD(self) -> None:
                if urlsplit(self.path).path.startswith(MEDIA_PREFIX):
                    self.serve_media("HEAD")
                else:
                    super().do_HEAD()

            def do_POST(self) -> None:
                path = urlsplit(self.path).path
                name = path.removeprefix(BRIDGE_PREFIX)
                if not path.startswith(BRIDGE_PREFIX) or name not in allowed:
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if length > MAX_BODY:
                    self.send_error(413)
                    return
                args = json.loads(self.rfile.read(length) or b"[]")
                harness.calls.append(name)
                try:
                    reply: dict[str, Any] = {"value": getattr(harness.api, name)(*args)}
                except Exception as error:
                    harness.errors.append(f"{name}: {type(error).__name__}: {error}")
                    reply = {"error": {"name": type(error).__name__, "message": str(error)}}
                body = json.dumps(reply).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self._httpd = ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(Handler, directory=str(root))
        )
        self._httpd.daemon_threads = True
        self.origin = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
