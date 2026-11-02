"""Damaged, hostile and oversized packages are refused with a clear message, never half-read."""

import json
import sqlite3
import zlib
from pathlib import Path

import pytest

from core.importers.anki import AnkiImportError, Limits, read_package
from core.importers.anki.package import open_sqlite
from tests.importers.conftest import fixture
from tests.importers.packages import (
    META_LATEST,
    entries,
    latest_media_map,
    legacy_media_map,
    repack,
    zipped,
    zstd_stream,
)


def read_all(package: bytes | Path, **kwargs: object) -> None:
    data = read_package(package, **kwargs)  # type: ignore[arg-type]
    for name in data.media.names():
        data.media.read(name)


def refused(package: bytes | Path, match: str, **kwargs: object) -> None:
    with pytest.raises(AnkiImportError, match=match):
        read_all(package, **kwargs)


def test_not_a_zip() -> None:
    refused(b"definitely not a zip", "not an Anki package")


@pytest.mark.parametrize("meta", [b"\x08\x00", b"\x08\x04", b"\x08\x7f"])
def test_packages_from_a_newer_anki(meta: bytes) -> None:
    refused(repack(fixture("basic.apkg"), replace={"meta": meta}), "newer version of Anki")


def test_damaged_meta() -> None:
    refused(repack(fixture("basic.apkg"), replace={"meta": b"\x08"}), "meta file is damaged")


def test_missing_collection() -> None:
    refused(repack(fixture("basic.apkg"), drop=("collection.anki21b",)), "no collection.anki21b")


def test_collection_that_is_not_sqlite() -> None:
    package = repack(fixture("basic.apkg"), replace={"collection.anki21b": zstd_stream(b"x" * 99)})
    refused(package, "not a SQLite database")


def test_damaged_zstd_stream() -> None:
    package = repack(fixture("basic.apkg"), replace={"collection.anki21b": b"\x28\xb5\x2f\xfd!!"})
    refused(package, "can't be read|not a SQLite database")


def test_placeholder_only_package() -> None:
    files = entries(fixture("basic.apkg"))
    only = zipped({"collection.anki2": files["collection.anki2"]})
    refused(only, "placeholder")


def test_unsupported_schema(tmp_path: Path) -> None:
    db = tmp_path / "c.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE col (ver, conf, models, decks, dconf)")
    conn.execute("INSERT INTO col VALUES (99, '', '', '', '')")
    conn.commit()
    conn.close()
    refused(zipped({"collection.anki21": db.read_bytes()}), "schema 99 is not supported")


def test_damaged_tables() -> None:
    conn = open_sqlite(_collection_bytes())
    conn.close()
    package = _with_collection(_collection_bytes(tamper="UPDATE notetypes SET config = x'ff'"))
    refused(package, "collection is damaged")


def _collection_bytes(tamper: str | None = None) -> bytes:
    import zstandard

    raw = entries(fixture("basic.apkg"))["collection.anki21b"]
    data = zstandard.ZstdDecompressor().stream_reader(raw, read_across_frames=True).read()
    if tamper is None:
        return data
    conn = sqlite3.connect(":memory:")
    conn.deserialize(data[:18] + b"\x01\x01" + data[20:])  # out of WAL mode
    conn.create_collation("unicase", lambda a, b: (a > b) - (a < b))
    conn.execute(tamper)
    conn.commit()
    return conn.serialize()


def _with_collection(db: bytes) -> bytes:
    return repack(fixture("basic.apkg"), replace={"collection.anki21b": zstd_stream(db)})


# ---------------------------------------------------------------- zip bombs and limits


def test_collection_over_the_size_limit() -> None:
    refused(fixture("basic.apkg"), "larger than an import allows",
            limits=Limits(max_collection_bytes=10_000))  # fmt: skip


def test_zstd_bomb_stops_at_the_cap() -> None:
    bomb = zstd_stream(b"\0" * (64 << 20))  # 64 MiB of zeros, a few KB compressed
    assert len(bomb) < 100_000
    package = repack(fixture("basic.apkg"), replace={"collection.anki21b": bomb})
    refused(package, "larger than an import allows", limits=Limits(max_collection_bytes=1 << 20))


def test_deflate_bomb_is_refused_by_its_ratio() -> None:
    zeros = b"\0" * (32 << 20)
    assert len(zlib.compress(zeros)) * 1000 < len(zeros)
    files = entries(fixture("basic-legacy.apkg"))
    import io
    import zipfile

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for name, data in files.items():
            method = zipfile.ZIP_DEFLATED if name == "collection.anki21" else zipfile.ZIP_STORED
            archive.writestr(name, zeros if name == "collection.anki21" else data, method)
    refused(out.getvalue(), "compressed suspiciously well")


def test_too_many_entries() -> None:
    files = {str(i): b"" for i in range(50)} | {"collection.anki21": b""}
    refused(zipped(files), "more files than an import allows", limits=Limits(max_entries=20))


def test_total_budget() -> None:
    refused(fixture("basic.apkg"), "more data than an import allows",
            limits=Limits(max_total_bytes=50_000))  # fmt: skip


def test_duplicate_zip_entries() -> None:
    import io
    import warnings
    import zipfile

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, data in entries(fixture("basic.apkg")).items():
            archive.writestr(name, data)
        archive.writestr("media", b"{}")
    refused(out.getvalue(), "lists a file twice")


# ---------------------------------------------------------------- media names (path traversal)


@pytest.mark.parametrize("name", ["../evil.png", "a/b.png", "/etc/passwd", "..", ".", ""])
def test_unsafe_legacy_media_names(name: str) -> None:
    package = repack(fixture("basic-legacy.apkg"),
                     replace={"media": legacy_media_map({"0": name})})  # fmt: skip
    refused(package, "unsafe file name|damaged")


def test_legacy_media_map_must_be_an_index_map() -> None:
    package = repack(fixture("basic-legacy.apkg"),
                     replace={"media": json.dumps({"x/../0": "a.png"}).encode()})  # fmt: skip
    refused(package, "damaged")
    package = repack(fixture("basic-legacy.apkg"), replace={"media": b"[1, 2]"})
    refused(package, "damaged")


def test_legacy_names_are_normalized_like_ankis() -> None:
    nfd = "café <x>.png"
    package = repack(fixture("basic-legacy.apkg"),
                     replace={"media": legacy_media_map({"0": nfd})})  # fmt: skip
    assert read_package(package).media.names() == {"café x.png"}


@pytest.mark.parametrize("name", ["../evil.png", "a/b.png", "café.png", "x:y.png"])
def test_latest_media_names_must_be_safe_and_normalized(name: str) -> None:
    files = entries(fixture("basic.apkg"))
    package = repack(fixture("basic.apkg"),
                     replace={"media": latest_media_map([(name, files["0"])])})  # fmt: skip
    refused(package, "unsafe file name")


def test_latest_media_checksum_is_checked() -> None:
    files = entries(fixture("basic.apkg"))
    media = latest_media_map([("pic.png", b"other bytes")])
    package = repack(fixture("basic.apkg"), replace={"media": media, "0": files["1"]})
    refused(package, "does not match its checksum")


def test_latest_media_map_damaged() -> None:
    package = repack(fixture("basic.apkg"), replace={"media": zstd_stream(b"\x0a\xff\xff")})
    refused(package, "media list is damaged")


def test_missing_media_member() -> None:
    package = repack(fixture("basic.apkg"), drop=("0",))
    refused(package, "missing from the package")


def test_meta_is_read_without_trusting_other_names() -> None:
    """Zip entry names are only ever looked up, never used as paths: a hostile entry name
    beside a valid package changes nothing."""
    files = entries(fixture("basic.apkg"))
    files["../../outside"] = b"x"
    files["meta"] = META_LATEST
    data = read_package(zipped(files))
    assert len(data.notes) == 6
