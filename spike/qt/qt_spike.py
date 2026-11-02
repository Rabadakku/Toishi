"""M0 shell spike: the same page in PySide6 6.12 + QtWebEngine (ADR-0001). Not shipped.

Mirrors app/main.py so the two shells can be compared like for like:
- the page is served from a loopback HTTP server (http://127.0.0.1:<port>), never file://;
- a QWebEngineUrlRequestInterceptor blocks every request that is not to that origin;
- window.pywebview.api is provided over QWebChannel, backed by the same app.api.Api;
- `--self-test` prints the same SELFTEST JSON line and exits 0/1.

Run: uv run --group spike-qt python spike/qt/qt_spike.py [--self-test]
"""

import argparse
import functools
import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root: core/, app/

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QFile, QIODevice, QObject, QTimer, QUrl, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
    qWebEngineChromiumVersion,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

import core
from app.api import Api, SelfTestInbox
from app.paths import WEB_DIST_DIR
from core.health import health_check

SHELL_NAME = f"PySide6 {PYSIDE_VERSION} + QtWebEngine (Chromium {qWebEngineChromiumVersion()})"
SELF_TEST_PREFIX = "SELFTEST "
LAUNCH_T0_ENV = "TOISHI_LAUNCH_T0"

# Builds window.pywebview.api on top of QWebChannel, then fires pywebviewready,
# so the page cannot tell this shell from pywebview.
SHIM = """
(function () {
  new QWebChannel(qt.webChannelTransport, function (channel) {
    var host = channel.objects.host;
    var api = {};
    METHODS.forEach(function (name) {
      api[name] = function () {
        var args = Array.prototype.slice.call(arguments);
        return new Promise(function (resolve, reject) {
          host.call(name, JSON.stringify(args), function (reply) {
            var r = JSON.parse(reply);
            if (r.ok) { resolve(r.value); } else { reject(new Error(r.error)); }
          });
        });
      };
    });
    window.pywebview = {api: api};
    window.dispatchEvent(new CustomEvent('pywebviewready'));
  });
})();
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


class LocalOnly(QWebEngineUrlRequestInterceptor):
    """Block everything except the loopback origin that serves the page."""

    def __init__(self, origin: QUrl) -> None:
        super().__init__()
        self.origin = origin
        self.blocked: list[str] = []

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        url = info.requestUrl()
        if url.scheme() in {"data", "blob", "about", "qrc"}:
            return
        if url.host() == self.origin.host() and url.port() == self.origin.port():
            return
        self.blocked.append(url.toString())
        info.block(True)


class Host(QObject):
    """QWebChannel object: forwards page calls to the public methods of app.api.Api."""

    def __init__(self, api: Api, on_report: Any) -> None:
        super().__init__()
        self._api = api
        self._on_report = on_report
        self.methods = sorted(n for n in dir(api) if not n.startswith("_"))

    @Slot(str, str, result=str)
    def call(self, name: str, args_json: str) -> str:
        if name not in self.methods:
            return json.dumps({"ok": False, "error": f"unknown method {name!r}"})
        try:
            value = getattr(self._api, name)(*json.loads(args_json))
        except Exception as error:
            return json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"})
        if name == "report_self_test":
            QTimer.singleShot(0, self._on_report)
        return json.dumps({"ok": True, "value": value})


def read_qt_resource(path: str) -> str:
    resource = QFile(path)
    if not resource.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"cannot read Qt resource {path}")
    return bytes(resource.readAll().data()).decode()


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(prog="qt-spike")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)

    if not (WEB_DIST_DIR / "index.html").is_file():
        print("error: app/web_dist missing; run npm --prefix web run build", file=sys.stderr)
        return 2

    httpd = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(WEB_DIST_DIR))
    )
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    origin = QUrl(f"http://127.0.0.1:{httpd.server_address[1]}/")

    app = QApplication([sys.argv[0]])
    app.setApplicationName(f"{core.APP_NAME} (Qt spike)")
    inbox = SelfTestInbox() if args.self_test else None
    result: dict[str, Any] = {}

    profile = QWebEngineProfile(app)  # off the record: nothing persisted
    interceptor = LocalOnly(origin)
    profile.setUrlRequestInterceptor(interceptor)

    view = QWebEngineView()
    page = QWebEnginePage(profile, view)
    view.setPage(page)

    def finish() -> None:
        if result:  # report and timeout can both fire
            return
        report = inbox.wait(0) if inbox else None
        page_ok = bool(report and report.get("ok") is True)
        core_report = health_check().as_dict()
        launch_t0 = os.environ.get(LAUNCH_T0_ENV)
        result.update(
            {
                "ok": page_ok and core_report["ok"] is True and not interceptor.blocked,
                "shell": SHELL_NAME,
                "page": report or {"ok": False, "error": "no report from the page"},
                "core": core_report,
                "blocked_requests": interceptor.blocked,
                "timings": {
                    "launch_to_report_ms": (
                        round((time.time() - float(launch_t0)) * 1000, 1) if launch_t0 else None
                    ),
                    "main_to_report_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            }
        )
        app.quit()

    api = Api(self_test=inbox)
    host = Host(api, finish)
    channel = QWebChannel(page)
    channel.registerObject("host", host)
    page.setWebChannel(channel)

    shim = QWebEngineScript()
    shim.setName("pywebview-shim")
    shim.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    shim.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    shim.setSourceCode(
        read_qt_resource(":/qtwebchannel/qwebchannel.js")
        + SHIM.replace("METHODS", json.dumps(host.methods))
    )
    page.scripts().insert(shim)

    view.setWindowTitle(f"{core.APP_NAME} (Qt spike)")
    view.resize(1100, 780)
    view.load(origin.resolved(QUrl("index.html")))
    view.show()

    if args.self_test:
        QTimer.singleShot(int(args.timeout * 1000), finish)
    app.exec()
    httpd.shutdown()

    if not args.self_test:
        return 0
    print(SELF_TEST_PREFIX + json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
