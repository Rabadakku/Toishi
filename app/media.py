"""Card media on the app's own origin: `GET /media/...` on the loopback server (ADR-0017).

The page may load images, audio, video, fonts and stylesheets from 'self' only (CSP,
ADR-0002), so the media of pack cards and of the student's own cards (imported Anki decks,
ADR-0015) are served here, read-only, under two fixed shapes:

    /media/user/<sha256 hex>[.ext]     the profile's media store (core.storage.media), by its
                                       content-addressed file name
    /media/pack/<pack id>/<name>       a pack's media table, by name (`media/graph.svg`)

Everything else under /media/ is 404, including the folders themselves: there is no listing.
Names are checked before anything is looked up (a user file must be exactly a content-addressed
name; a pack name must be a relative path without '.', '..', empty parts, backslashes, NULs or
control characters), and a pack name is only ever a key into the pack database, never a path.
Only GET and HEAD are answered, with one byte range at most (WKWebView will not play audio or
video from a server without ranges). Responses carry the content type of the extension,
`nosniff`, and a CSP that keeps an SVG opened as a document from running anything.

`respond` is the whole route as a function, so the app's server (`MediaMiddleware`, a WSGI
wrapper installed by app/shell.py) and the test harness share it. This module imports no GUI.
"""

import dataclasses
import posixpath
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Protocol
from urllib.parse import quote

from core.storage import Storage, StorageError
from core.storage.media import FILE_NAME, unsafe_name

PREFIX = "/media/"
USER_URL = PREFIX + "user/"
PACK_URL = PREFIX + "pack/"
PACK_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
CHUNK = 64 * 1024

CONTENT_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "avif": "image/avif",
    "bmp": "image/bmp",
    "ico": "image/x-icon",
    "svg": "image/svg+xml",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "oga": "audio/ogg",
    "opus": "audio/ogg",
    "mp4": "video/mp4",
    "m4v": "video/mp4",
    "mov": "video/quicktime",
    "webm": "video/webm",
    "ogv": "video/ogg",
    "woff": "font/woff",
    "woff2": "font/woff2",
    "ttf": "font/ttf",
    "otf": "font/otf",
    "css": "text/css; charset=utf-8",
}
FALLBACK_TYPE = "application/octet-stream"
# Opened as a document (nothing in the app does), an SVG may not run script or load anything.
DOCUMENT_CSP = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
_RANGE = re.compile(r"bytes=(\d*)-(\d*)")
_REASONS = {
    200: "OK",
    206: "Partial Content",
    404: "Not Found",
    405: "Method Not Allowed",
    416: "Range Not Satisfiable",
}

type Headers = list[tuple[str, str]]


class MediaSource(Protocol):
    """Where media come from. Both lookups answer None for anything they do not hold."""

    def user_file(self, name: str) -> Path | None:
        """The stored file of a content-addressed name, in the open profile."""
        ...

    def pack_file(self, pack_id: str, name: str) -> bytes | None:
        """A media file of an attached pack."""
        ...


@dataclass(slots=True)
class MediaResponse:
    status: int
    headers: Headers = field(default_factory=list)
    body: Iterable[bytes] = ()

    @property
    def status_line(self) -> str:
        return f"{self.status} {_REASONS[self.status]}"


def user_url(file: str) -> str:
    """The URL of a stored file (`file` is a content-addressed name)."""
    return USER_URL + file


def pack_url(pack_id: str, name: str) -> str:
    return PACK_URL + quote(pack_id, safe="") + "/" + quote(name, safe="/")


def pack_name_ok(name: str) -> bool:
    """A pack media name that can be looked up: relative, no '.'/'..'/empty parts."""
    return not unsafe_name(name) and not any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in name)


def parse(path: str) -> tuple[str, str, str] | None:
    """('user', '', file) or ('pack', pack id, name) for a servable path, else None."""
    if not path.startswith(PREFIX):
        return None
    kind, _, tail = path[len(PREFIX) :].partition("/")
    if kind == "user":
        return ("user", "", tail) if FILE_NAME.fullmatch(tail) else None
    if kind == "pack":
        pack_id, _, name = tail.partition("/")
        if PACK_ID.fullmatch(pack_id) and pack_name_ok(name):
            return "pack", pack_id, name
    return None


def content_type(name: str) -> str:
    suffix = PurePosixPath(name).suffix.lower().removeprefix(".")
    return CONTENT_TYPES.get(suffix, FALLBACK_TYPE)


def _plain(status: int, headers: Headers | None = None) -> MediaResponse:
    text = _REASONS[status].encode()
    head = [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(text)))]
    return MediaResponse(status, [*head, *(headers or [])], [text])


def _byte_range(header: str | None, size: int) -> tuple[int, int] | Literal["bad"] | None:
    """(first, last) of one satisfiable range; None for no (usable) Range header; "bad" when
    the range cannot be satisfied. Several ranges are not served: the whole file answers."""
    if header is None:
        return None
    match = _RANGE.fullmatch(header.strip())
    if match is None:
        return None
    first, last = match.groups()
    if not first and not last:
        return None
    if not first:  # the last N bytes
        count = int(last)
        return (max(0, size - count), size - 1) if count and size else "bad"
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    return (start, end) if start < size and start <= end else "bad"


def _file_chunks(path: Path, start: int, length: int) -> Iterator[bytes]:
    with path.open("rb") as handle:
        handle.seek(start)
        left = length
        while left > 0:
            chunk = handle.read(min(CHUNK, left))
            if not chunk:
                return
            left -= len(chunk)
            yield chunk


def _bytes_chunks(data: bytes, start: int, length: int) -> Iterator[bytes]:
    for at in range(start, start + length, CHUNK):
        yield data[at : min(at + CHUNK, start + length)]


def respond(
    method: str, path: str, source: MediaSource, range_header: str | None = None
) -> MediaResponse:
    """The answer to one request for `path` (decoded, no query)."""
    if method not in ("GET", "HEAD"):
        return _plain(405, [("Allow", "GET, HEAD")])
    target = parse(path)
    if target is None:
        return _plain(404)
    kind, pack_id, name = target
    file: Path | None = None
    data: bytes | None = None
    try:
        if kind == "user":
            file = source.user_file(name)
            size = file.stat().st_size if file is not None else 0
        else:
            data = source.pack_file(pack_id, name)
            size = len(data) if data is not None else 0
    except OSError:
        return _plain(404)
    if file is None and data is None:
        return _plain(404)
    headers: Headers = [
        ("Content-Type", content_type(name)),
        ("Accept-Ranges", "bytes"),
        ("X-Content-Type-Options", "nosniff"),
        ("Content-Security-Policy", DOCUMENT_CSP),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        # Content-addressed files never change; a pack's media change only with the pack.
        ("Cache-Control", "private, max-age=31536000, immutable" if kind == "user" else "no-cache"),
    ]
    chosen = _byte_range(range_header, size)
    if chosen == "bad":
        return _plain(416, [("Content-Range", f"bytes */{size}")])
    status, start, length = 200, 0, size
    if isinstance(chosen, tuple):
        status, start, length = 206, chosen[0], chosen[1] - chosen[0] + 1
        headers.append(("Content-Range", f"bytes {chosen[0]}-{chosen[1]}/{size}"))
    headers.append(("Content-Length", str(length)))
    if method == "HEAD":
        return MediaResponse(status, headers)
    if file is not None:
        body: Iterable[bytes] = _file_chunks(file, start, length)
    else:
        body = _bytes_chunks(data or b"", start, length)
    return MediaResponse(status, headers, body)


# ---------------------------------------------------------------- the open profile


class ProfileMedia:
    """MediaSource over whatever profile is open now (`storage` answers None when none is).

    Called from server threads, with no API lock: storage gives each thread its own read
    connection, and a profile that closes meanwhile just makes the file unavailable."""

    def __init__(self, storage: Callable[[], Storage | None]) -> None:
        self._storage = storage

    def user_file(self, name: str) -> Path | None:
        storage = self._storage()
        if storage is None:
            return None
        path = storage.users.media.path(name)
        return path if path.is_file() and not path.is_symlink() else None

    def pack_file(self, pack_id: str, name: str) -> bytes | None:
        storage = self._storage()
        if storage is None:
            return None
        try:
            return storage.packs.media(pack_id, name)
        except StorageError, sqlite3.Error, ValueError:
            return None


# ---------------------------------------------------------------- what a card shows

_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)")


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for item in dataclasses.fields(value):
            yield from _strings(getattr(value, item.name))
    elif isinstance(value, tuple | list):
        for item in value:
            yield from _strings(item)


def card_media(storage: Storage, card_id: str) -> dict[str, str]:
    """{reference as written in the card's text: URL on this origin} for the media a card has.

    An own card (imported Anki deck, editor): its user_media links, `pic.png` or
    `_anki-nt-....css` -> /media/user/<file>. A pack card: the images its Markdown names
    (`![..](media/graph.svg)`) that the pack holds -> /media/pack/<pack>/<name>."""
    source = storage.packs.card_source(card_id)
    if source is None:
        return {}
    if source == "user":
        return {ref: user_url(file) for ref, file in storage.users.media.links(card_id).items()}
    card = storage.packs.card(card_id)
    found: dict[str, str] = {}
    for text in _strings(card):
        for match in _IMAGE.finditer(text):
            ref = match.group(1)
            name = posixpath.normpath(ref)
            if ref not in found and pack_name_ok(name) and storage.packs.media(source, name):
                found[ref] = pack_url(source, name)
    return found


# ---------------------------------------------------------------- WSGI wrapper


class MediaMiddleware:
    """WSGI app: /media/... is answered here, everything else goes to `app` untouched."""

    def __init__(self, app: Callable[..., Any], source: MediaSource) -> None:
        self._app = app
        self._source = source

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Any:
        path = str(environ.get("PATH_INFO", ""))
        if path != PREFIX.rstrip("/") and not path.startswith(PREFIX):
            return self._app(environ, start_response)
        reply = respond(
            str(environ.get("REQUEST_METHOD", "GET")),
            path,
            self._source,
            environ.get("HTTP_RANGE"),
        )
        start_response(reply.status_line, reply.headers)
        return reply.body
