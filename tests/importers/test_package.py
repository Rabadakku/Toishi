"""IMP-2: reading .apkg and .colpkg, old and new formats, schema 11 and 18."""

import unicodedata
import zipfile
from pathlib import Path

import zstandard

from core.importers.anki import read_anki_file, read_package
from core.importers.anki.package import PLACEHOLDER_TEXT
from tests.importers.conftest import fixture
from tests.importers.packages import entries, repack


def _content(name: str) -> set[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    data = read_package(fixture(name))
    return {(n.guid, n.fields, n.tags) for n in data.notes}


def test_latest_format_reads_the_zstd_collection_never_the_placeholder() -> None:
    files = entries(fixture("basic.apkg"))
    assert files["meta"] == b"\x08\x03"
    assert {"collection.anki21b", "collection.anki2"} <= set(files)
    frame = zstandard.get_frame_parameters(files["collection.anki21b"])
    assert frame.content_size == zstandard.CONTENTSIZE_UNKNOWN  # must be streamed
    data = read_package(fixture("basic.apkg"))
    assert (data.package_version, data.schema, data.format) == (3, 18, "apkg")
    assert len(data.notes) == 6
    assert data.cards is not None
    assert len(data.cards) == 8
    assert not any(PLACEHOLDER_TEXT in f for n in data.notes for f in n.fields)


def test_legacy_format_has_the_same_deck() -> None:
    data = read_package(fixture("basic-legacy.apkg"))
    assert (data.package_version, data.schema) == (2, 11)
    assert _content("basic-legacy.apkg") == _content("basic.apkg")
    latest = read_package(fixture("basic.apkg"))
    assert sorted((c.ord, c.deck) for c in data.cards or ()) == sorted(
        (c.ord, c.deck) for c in latest.cards or ()
    )
    assert sorted(nt.name for nt in data.notetypes.values()) == sorted(
        nt.name for nt in latest.notetypes.values()
    )


def test_schema_18_reads_only_note_types_in_the_package() -> None:
    """The exporter leaves fields/templates rows of stock note types it didn't export."""
    data = read_package(fixture("basic.apkg"))
    names = {nt.name for nt in data.notetypes.values()}
    assert names == {
        "Basic", "Basic (and reversed card)", "Basic (optional reversed card)",
        "Basic (type in the answer)",
    }  # fmt: skip
    reversed_ = next(nt for nt in data.notetypes.values() if nt.name.endswith("reversed card)"))
    assert [t.qfmt for t in reversed_.templates] == ["{{Front}}", "{{Back}}"]


def test_without_meta_the_newest_collection_file_is_read() -> None:
    no_meta = repack(fixture("basic-legacy.apkg"), drop=("meta",))
    data = read_package(no_meta, name="old.apkg")
    assert data.package_version == 2
    assert len(data.notes) == 6
    # Anki 2.0: only collection.anki2 (here: the real collection under the old name).
    oldest = repack(
        fixture("basic-legacy.apkg"),
        drop=("meta", "collection.anki2"),
        rename={"collection.anki21": "collection.anki2"},
    )
    data = read_package(oldest, name="oldest.apkg")
    assert data.package_version == 1
    assert len(data.notes) == 6


def test_meta_saying_legacy_1_still_never_reads_the_placeholder() -> None:
    package = repack(fixture("basic-legacy.apkg"), replace={"meta": b"\x08\x01"})
    assert len(read_package(package).notes) == 6


def test_media_map_names_and_bytes() -> None:
    for name in ("basic.apkg", "basic-legacy.apkg"):
        data = read_package(fixture(name))
        assert data.media.names() == {"pic.png", "sound.mp3", "café.png"}
        assert unicodedata.is_normalized("NFC", next(n for n in data.media.names() if "caf" in n))
        assert data.media.read("pic.png").startswith(b"\x89PNG")
        assert data.media.read("café.png").endswith(b"cafe")


def test_a_package_without_a_media_map_has_no_media() -> None:
    data = read_package(repack(fixture("basic.apkg"), drop=("media",)))
    assert data.media.names() == frozenset()
    assert len(data.notes) == 6


def test_colpkg_carries_rollover_offset_and_deck_options() -> None:
    data = read_package(fixture("history.colpkg"))
    assert data.format == "colpkg"
    assert (data.rollover_hour, data.minutes_west) == (6, -300)
    presets = {c.name: c for c in data.deck_configs.values()}
    assert len(presets["FSRS preset"].fsrs_params) == 21
    assert presets["FSRS preset"].fsrs_params[0] == 0.2172
    assert presets["FSRS preset"].desired_retention == 0.85
    assert presets["Default"].fsrs_params == ()
    apkg = read_package(fixture("history.apkg"))
    assert (apkg.rollover_hour, apkg.minutes_west) == (None, None)  # .apkg: Anki's 4 AM


def test_cards_carry_home_deck_scheduling_and_fsrs_data() -> None:
    data = read_package(fixture("history.apkg"))
    by_deck = {c.deck for c in data.cards or ()}
    assert by_deck == {"Hist::FSRS", "Hist::SM2"}
    with_memory = [c for c in data.cards or () if "s" in c.data]
    assert len(with_memory) == 1
    assert with_memory[0].data["s"] == 12.5
    assert len(data.revlog) == 22


def test_read_anki_file_picks_the_reader() -> None:
    assert read_anki_file(fixture("basic.apkg")).format == "apkg"
    assert read_anki_file(fixture("history.colpkg")).format == "colpkg"
    assert read_anki_file(fixture("notes.txt")).format == "anki-text"


def test_reader_never_writes_to_the_archive(tmp_path: Path) -> None:
    copy = tmp_path / "deck.apkg"
    copy.write_bytes(fixture("basic.apkg").read_bytes())
    before = copy.read_bytes()
    read_package(copy)
    assert copy.read_bytes() == before
    assert zipfile.is_zipfile(copy)
