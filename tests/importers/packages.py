"""Builders for hand-made and damaged packages (zip archives in memory)."""

import io
import json
import zipfile
from collections.abc import Mapping
from pathlib import Path

import zstandard


def entries(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {info.filename: archive.read(info) for info in archive.infolist()}


def zipped(files: Mapping[str, bytes], *, compress: bool = False) -> bytes:
    out = io.BytesIO()
    method = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    with zipfile.ZipFile(out, "w", method) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return out.getvalue()


def repack(
    path: Path,
    replace: Mapping[str, bytes] | None = None,
    drop: tuple[str, ...] = (),
    rename: Mapping[str, str] | None = None,
) -> bytes:
    files = entries(path)
    for name in drop:
        files.pop(name, None)
    for old, new in (rename or {}).items():
        files[new] = files.pop(old)
    files.update(replace or {})
    return zipped(files)


def zstd_stream(data: bytes) -> bytes:
    """A streaming zstd frame without a content size, as Anki writes them."""
    out = io.BytesIO()
    with zstandard.ZstdCompressor().stream_writer(out, closefd=False) as writer:
        writer.write(data)
    return out.getvalue()


def legacy_media_map(mapping: Mapping[str, str]) -> bytes:
    return json.dumps(mapping).encode()


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _field(number: int, payload: bytes) -> bytes:
    return _varint(number << 3 | 2) + _varint(len(payload)) + payload


def latest_media_map(items: list[tuple[str, bytes]]) -> bytes:
    """protobuf MediaEntries {repeated MediaEntry{name=1, size=2, sha1=3}}, zstd-compressed."""
    import hashlib

    body = b""
    for name, data in items:
        entry = _field(1, name.encode()) + _varint(2 << 3) + _varint(len(data))
        entry += _field(3, hashlib.sha1(data, usedforsecurity=False).digest())
        body += _field(1, entry)
    return zstd_stream(body)


META_LEGACY = b"\x08\x02"
META_LATEST = b"\x08\x03"
