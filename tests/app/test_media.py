"""The card media route (ADR-0017): read-only, content-addressed, no traversal, no listing.

`app.media.respond` is the whole route; the last tests run it behind the real pywebview server
(`shell.install_loopback_server`) to show nothing else answers /media and the page's own files
still come through.
"""

import http.client
import socket
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import media, shell
from app.api import Api
from app.media import ProfileMedia, card_media, respond
from app.paths import WEB_DIST_DIR
from core.importers.anki import apply_anki_import, plan_anki_import, read_package
from core.storage.media import media_file_name

DECKS = Path(__file__).parents[1] / "importers" / "fixtures"
PARABOLA_CARD = "test.quad.parabola.001"
PACK_IMAGE = "/media/pack/test/media/parabola.svg"


class Recorder:
    """A media source that remembers what it was asked for."""

    def __init__(self, inner: media.MediaSource) -> None:
        self.inner = inner
        self.asked: list[tuple[str, ...]] = []

    def user_file(self, name: str) -> Path | None:
        self.asked.append(("user", name))
        return self.inner.user_file(name)

    def pack_file(self, pack_id: str, name: str) -> bytes | None:
        self.asked.append(("pack", pack_id, name))
        return self.inner.pack_file(pack_id, name)


@pytest.fixture
def profile(api: Api) -> Api:
    """A profile with the Test pack and the Basic fixture deck imported (pic.png, café.png)."""
    api.profile_create({"name": "Sam"})
    users = api._store().users
    data = read_package(DECKS / "basic.apkg")
    apply_anki_import(users, plan_anki_import(users, data))
    return api


@pytest.fixture
def source(profile: Api) -> Recorder:
    return Recorder(ProfileMedia(profile._storage_or_none))


def hola_card(profile: Api) -> str:
    return next(c.id for c in profile._store().users.user_cards() if "Hola" in (c.front_md or ""))


def body(reply: media.MediaResponse) -> bytes:
    return b"".join(reply.body)


def test_serves_a_stored_image_with_its_content_type(profile: Api, source: Recorder) -> None:
    data = read_package(DECKS / "basic.apkg").media.read("pic.png")
    url = profile.library_card_media({"card_id": hola_card(profile)})["files"]["pic.png"]
    assert url == f"/media/user/{media_file_name(data, 'pic.png')}"
    reply = respond("GET", url, source)
    assert reply.status == 200
    headers = dict(reply.headers)
    assert headers["Content-Type"] == "image/png"
    assert headers["Content-Length"] == str(len(data))
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert "sandbox" in headers["Content-Security-Policy"]
    assert "immutable" in headers["Cache-Control"]
    served = body(reply)
    assert served == data
    assert served[:8] == b"\x89PNG\r\n\x1a\n"  # a real PNG, not a placeholder


def test_serves_pack_media_by_name(source: Recorder) -> None:
    reply = respond("GET", PACK_IMAGE, source)
    assert reply.status == 200
    assert dict(reply.headers)["Content-Type"] == "image/svg+xml"
    assert body(reply).lstrip().startswith((b"<?xml", b"<svg"))
    assert source.asked == [("pack", "test", "media/parabola.svg")]


def test_head_has_the_headers_and_no_body(profile: Api, source: Recorder) -> None:
    url = profile.library_card_media({"card_id": hola_card(profile)})["files"]["pic.png"]
    get, head = respond("GET", url, source), respond("HEAD", url, source)
    assert head.status == 200
    assert dict(head.headers)["Content-Length"] == dict(get.headers)["Content-Length"]
    assert body(head) == b""


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def test_nothing_but_get_and_head(method: str, source: Recorder) -> None:
    reply = respond(method, PACK_IMAGE, source)
    assert reply.status == 405
    assert dict(reply.headers)["Allow"] == "GET, HEAD"
    assert source.asked == []


DIGEST = "5f23bb350e313f30e8ac2bfa182496eeb15674171ecc0a2bc79cab880e942a70"


@pytest.mark.parametrize(
    "path",
    [
        # traversal, as the server hands it over (already percent-decoded)
        "/media/user/../../../etc/passwd",
        "/media/user/../user.db",
        f"/media/user/{DIGEST}.png/../../user.db",
        f"/media/user/../media/{DIGEST}.png",
        "/media/pack/test/../../../etc/passwd",
        "/media/pack/test/media/../../test.db",
        "/media/pack/test/./media/parabola.svg",
        "/media/pack/test//media/parabola.svg",
        "/media/pack/../test/media/parabola.svg",
        "/media/pack/test/media\\..\\parabola.svg",
        "/media/pack/test/media/parabola.svg\x00.png",
        "/media/pack/test/media/\x1fparabola.svg",
        "/media/pack/te st/media/parabola.svg",
        "/media/pack/TEST/media/parabola.svg",
        "/media/pack//media/parabola.svg",
        "/media/../index.html",
        "/media/./user/" + DIGEST,
        "//media/user/" + DIGEST,
        # not a content-addressed name
        "/media/user/pic.png",
        "/media/user/" + DIGEST.upper(),
        "/media/user/" + DIGEST[:-1],
        "/media/user/" + DIGEST + "0",
        f"/media/user/{DIGEST}.PNG",
        f"/media/user/{DIGEST}.png.png",
        f"/media/user/{DIGEST}.",
        f"/media/user/{DIGEST}.png/",
        f"/media/user/{DIGEST}.png/extra",
        "/media/user/.incoming-abc",
        # no listing
        "/media",
        "/media/",
        "/media/user",
        "/media/user/",
        "/media/pack",
        "/media/pack/",
        "/media/pack/test",
        "/media/pack/test/",
        "/media/pack/test/media/",
        "/media/other/x",
    ],
)
def test_refuses_traversal_bad_names_and_listings(path: str, source: Recorder) -> None:
    reply = respond("GET", path, source)
    assert reply.status == 404
    assert body(reply) == b"Not Found"
    assert source.asked == []  # refused by shape alone: nothing was looked up


def test_unknown_names_are_404(profile: Api, source: Recorder) -> None:
    assert respond("GET", f"/media/user/{'0' * 64}.png", source).status == 404
    assert respond("GET", "/media/pack/test/media/nope.svg", source).status == 404
    assert respond("GET", "/media/pack/nopack/media/parabola.svg", source).status == 404
    assert {a[0] for a in source.asked} == {"user", "pack"}  # well-formed, so looked up
    # With no profile open there is nothing to serve at all.
    closed = ProfileMedia(lambda: None)
    assert respond("GET", PACK_IMAGE, closed).status == 404
    assert respond("GET", f"/media/user/{DIGEST}.png", closed).status == 404


def test_a_symlink_in_the_store_is_not_followed(profile: Api, tmp_path: Path) -> None:
    folder = profile._store().users.media.folder
    secret = tmp_path / "secret.png"
    secret.write_bytes(b"not for the page")
    name = "0" * 63 + "1.png"
    (folder / name).symlink_to(secret)
    reply = respond("GET", f"/media/user/{name}", ProfileMedia(profile._storage_or_none))
    assert reply.status == 404


@pytest.mark.parametrize(
    ("header", "status", "slice_", "content_range"),
    [
        ("bytes=0-3", 206, slice(0, 4), "bytes 0-3/{n}"),
        ("bytes=2-", 206, slice(2, None), "bytes 2-{last}/{n}"),
        ("bytes=-5", 206, slice(-5, None), "bytes {first5}-{last}/{n}"),
        ("bytes=0-99999", 206, slice(0, None), "bytes 0-{last}/{n}"),
        ("bytes=9999-", 416, None, "bytes */{n}"),
        ("bytes=5-2", 416, None, "bytes */{n}"),
        ("bytes=0-1,4-5", 200, slice(0, None), None),  # several ranges: the whole file
        ("items=0-3", 200, slice(0, None), None),
        ("bytes=-", 200, slice(0, None), None),
    ],
)
def test_one_byte_range_for_audio_and_video(
    header: str, status: int, slice_: slice | None, content_range: str | None, source: Recorder
) -> None:
    whole = body(respond("GET", PACK_IMAGE, source))
    n = len(whole)
    reply = respond("GET", PACK_IMAGE, source, header)
    assert reply.status == status
    headers = dict(reply.headers)
    if content_range is not None:
        assert headers["Content-Range"] == content_range.format(n=n, last=n - 1, first5=n - 5)
    if slice_ is not None:
        assert body(reply) == whole[slice_]
        assert headers["Content-Length"] == str(len(whole[slice_]))
    if status != 416:
        assert headers["Accept-Ranges"] == "bytes"


def test_ranges_work_on_stored_files_too(profile: Api, source: Recorder) -> None:
    url = profile.library_card_media({"card_id": hola_card(profile)})["files"]["sound.mp3"]
    whole = body(respond("GET", url, source))
    assert dict(respond("GET", url, source).headers)["Content-Type"] == "audio/mpeg"
    reply = respond("GET", url, source, "bytes=3-6")
    assert (reply.status, body(reply)) == (206, whole[3:7])


def test_content_types_by_extension() -> None:
    assert media.content_type("a.PNG") == "image/png"
    assert media.content_type("media/graph.svg") == "image/svg+xml"
    assert media.content_type("x.woff2") == "font/woff2"
    assert media.content_type("_card.css") == "text/css; charset=utf-8"
    assert media.content_type("x.exe") == "application/octet-stream"
    assert media.content_type("noextension") == "application/octet-stream"


# ---------------------------------------------------------------- what a card shows


def test_card_media_of_an_own_card_is_its_links(profile: Api) -> None:
    files = profile.library_card_media({"card_id": hola_card(profile)})["files"]
    assert set(files) == {"pic.png", "sound.mp3"}
    assert all(url.startswith("/media/user/") for url in files.values())


def test_card_media_of_a_pack_card_is_the_images_the_pack_holds(profile: Api) -> None:
    files = profile.library_card_media({"card_id": PARABOLA_CARD})["files"]
    assert files == {"media/parabola.svg": PACK_IMAGE}
    other = profile.library_card_media({"card_id": "test.linear.flash.001"})
    assert other == {"files": {}}  # no images
    assert profile.library_card_media({"card_id": "no.such.card"}) == {"files": {}}


def test_card_media_leaves_out_what_the_pack_lacks(profile: Api) -> None:
    store = profile._store()
    card = store.packs.card(PARABOLA_CARD)
    assert card is not None
    hostile = replace(
        card,
        question_md="![a](media/nope.svg) ![b](../secret.png) ![c](https://x.example/y.png) "
        "![d](media/parabola.svg) ![e](media/../media/parabola.svg)",
    )
    packs = SimpleNamespace(
        card_source=lambda card_id: "test", card=lambda card_id: hostile, media=store.packs.media
    )
    found = card_media(SimpleNamespace(packs=packs), "x")  # type: ignore[arg-type]
    assert found == {"media/parabola.svg": PACK_IMAGE, "media/../media/parabola.svg": PACK_IMAGE}


def test_library_card_media_checks_its_argument(profile: Api) -> None:
    with pytest.raises(TypeError):
        profile.library_card_media({"card_id": 7})
    with pytest.raises(ValueError, match="longer"):
        profile.library_card_media({"card_id": "x" * 500})


# ---------------------------------------------------------------- behind the real server


@pytest.fixture
def live(profile: Api) -> Iterator[str]:
    if not (WEB_DIST_DIR / "index.html").is_file():
        pytest.skip("app/web_dist not built")
    shell.install_loopback_server(ProfileMedia(profile._storage_or_none))
    address, _root, _server = shell._http.BottleServer.start_server(
        [str(WEB_DIST_DIR / "index.html")], None
    )
    origin = address.rstrip("/")
    host, _, port = origin.removeprefix("http://").partition(":")
    for _attempt in range(100):  # the server thread binds a moment after start_server returns
        try:
            socket.create_connection((host, int(port)), timeout=1).close()
            break
        except OSError:
            time.sleep(0.05)
    yield origin
    shell.install_loopback_server()  # the next test gets the plain server again


def raw_get(origin: str, target: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    """The request line exactly as given (no client-side normalization of .. or %2e)."""
    host, _, port = origin.removeprefix("http://").partition(":")
    conn = http.client.HTTPConnection(host, int(port), timeout=10)
    try:
        conn.putrequest("GET", target, skip_host=False, skip_accept_encoding=True)
        for key, value in (headers or {}).items():
            conn.putheader(key, value)
        conn.endheaders()
        reply = conn.getresponse()
        return reply.status, reply.read()
    finally:
        conn.close()


def test_the_real_server_serves_media_and_still_the_page(profile: Api, live: str) -> None:
    url = profile.library_card_media({"card_id": hola_card(profile)})["files"]["pic.png"]
    status, data = raw_get(live, url)
    assert (status, data[:4]) == (200, b"\x89PNG")
    status, data = raw_get(live, PACK_IMAGE)
    assert status == 200
    assert data.lstrip().startswith((b"<?xml", b"<svg"))
    with urllib.request.urlopen(live + "/index.html", timeout=10) as reply:  # noqa: S310
        assert reply.status == 200
        assert b"Content-Security-Policy" in reply.read()
    status, data = raw_get(live, url, {"Range": "bytes=1-3"})
    assert (status, data) == (206, b"PNG")


@pytest.mark.parametrize(
    "target",
    [
        "/media/user/..%2f..%2f..%2fetc%2fpasswd",
        "/media/user/%2e%2e/%2e%2e/user.db",
        "/media/pack/test/%2e%2e/%2e%2e/%2e%2e/pyproject.toml",
        "/media/pack/test/media%2f..%2f..%2ftest.db",
        "/media/pack/test/media/..%5cparabola.svg",
        "/media/../index.html",
        "/media/pack/test/",
        "/media/",
        "/media",
    ],
)
def test_the_real_server_refuses_traversal_and_listings(live: str, target: str) -> None:
    status, data = raw_get(live, target)
    assert status == 404
    assert data == b"Not Found"
    for name in ("passwd", "user.db", "pyproject", "<!doctype"):
        assert name.encode() not in data
