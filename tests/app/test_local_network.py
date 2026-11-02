"""macOS asked for Local Network access at launch (backlog). Startup must resolve no name
beyond loopback: no socket.getfqdn() in the HTTP server, no MAC-address lookup for ids."""

import socket
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import pytest

from app import shell
from app.api import Api
from app.paths import WEB_DIST_DIR
from core.storage import ProfileManager

LOOPBACK = {"127.0.0.1", "localhost", "::1", ""}


@pytest.fixture
def lookups(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every name the process tries to resolve; fail on the Mac's own name."""
    seen: list[str] = []
    own = socket.gethostname()

    def recorder(name: str, real: Any) -> Any:
        def wrapped(host: Any, *args: Any, **kwargs: Any) -> Any:
            text = host.decode() if isinstance(host, bytes) else str(host)
            seen.append(text)
            if text == own and own not in LOOPBACK:
                raise AssertionError(f"{name}({text!r}) resolves this machine's own name")
            return real(host, *args, **kwargs)

        return wrapped

    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getfqdn"):
        monkeypatch.setattr(socket, name, recorder(name, getattr(socket, name)))
    monkeypatch.setattr(socket, "getnameinfo", recorder("getnameinfo", socket.getnameinfo))

    def no_mac() -> int:
        raise AssertionError("uuid.getnode(): looks up the MAC address (and the host name)")

    # As on a Mac without the stdlib's _uuid helper: uuid1() would fall back to getnode().
    monkeypatch.setattr(uuid, "_generate_time_safe", None)
    monkeypatch.setattr(uuid, "getnode", no_mac)
    return seen


def test_the_unpatched_server_would_look_up_names(lookups: list[str]) -> None:
    # Guards the guard: the stdlib server's bind and uuid1() both trip the recorder.
    from http.server import HTTPServer, SimpleHTTPRequestHandler

    server = HTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
    server.server_close()
    assert "127.0.0.1" in lookups  # getfqdn(host) at bind time
    with pytest.raises(AssertionError, match="getnode"):
        uuid.uuid1()


def test_startup_resolves_no_non_loopback_name(lookups: list[str], tmp_path: Path) -> None:
    if not (WEB_DIST_DIR / "index.html").is_file():
        pytest.skip("app/web_dist not built")
    shell.install_loopback_server()
    # What webview.start(http_server=True) does with our entry page.
    address, _root, _server = shell._http.BottleServer.start_server(
        [str(WEB_DIST_DIR / "index.html")], None
    )
    assert address.startswith("http://127.0.0.1:")
    shell._window.uuid1()  # evaluate_js's ids
    # The app's own startup: profiles, the shipped packs, the bridge.
    api = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=())
    api._open_last()
    api.profile_create({"name": "Sam"})
    api._close(backup=False)
    with urllib.request.urlopen(address + "index.html", timeout=10) as reply:  # noqa: S310
        assert reply.status == 200
    assert {name for name in lookups} <= LOOPBACK, lookups
    assert "localhost" not in lookups  # bound and named by number


def test_free_port_is_a_loopback_number() -> None:
    port = shell.free_loopback_port()
    assert 0 < port < 65536


def test_page_events_are_plain_scripts_with_a_checked_name() -> None:
    script = shell.page_event_script("undo-answer")
    assert script == (
        'window.dispatchEvent(new CustomEvent("toishi:menu", {detail: "undo-answer"}))'
    )
    for bad in ("x'); alert(1); ('", "Undo", ""):
        with pytest.raises(ValueError, match="page event"):
            shell.page_event_script(bad)


def test_edit_menu_has_undo_and_redo_for_the_first_responder() -> None:
    assert shell.EDIT_ITEMS == (("Undo", "undo:", "z"), ("Redo", "redo:", "Z"))
    cocoa = Path(str(shell._http.__file__)).parent / "platforms" / "cocoa.py"
    source = cocoa.read_text()
    # The pywebview internals the Edit menu patch relies on (pinned 6.2.1).
    assert "def _add_edit_menu(self, mainMenu):" in source
    assert "def _process_menu_items(self, menu_items, parent_menu):" in source
    assert "mainMenu.insertItem_atIndex_(editMenuItem, 1)" in source
