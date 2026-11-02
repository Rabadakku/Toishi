"""Anki decks for the page tests, built with the official `anki` package (a dev-only test
oracle, ADR-0015): a custom note type with its own CSS and a picture, a stock Cloze note, and a
Basic note with math. One collection and one .apkg each, so a test imports only what it studies."""

import struct
import zlib
from pathlib import Path
from typing import Any

from anki.collection import Collection
from anki.import_export_pb2 import ExportAnkiPackageOptions, ExportLimit

PICTURE_SIZE = (48, 32)
BG_SIZE = (8, 8)

# Rules the page test looks for. The bare `div` rule must stay inside the card.
PICTURE_CSS = """
.card { font-family: Georgia, serif; background: url(_bg.png) repeat; }
.prompt { color: rgb(1, 2, 3); border: 2px solid rgb(4, 5, 6); }
.answer { color: rgb(7, 8, 9); }
div { margin-left: 13px; }
.nightMode .prompt { color: rgb(250, 250, 250); }
"""


def png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """A real, decodable PNG of one colour."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    row = b"\x00" + bytes(rgb) * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )


def _add(col: Any, notetype: str, deck: str, fields: dict[str, str]) -> None:
    note = col.new_note(col.models.by_name(notetype))
    for name, value in fields.items():
        note[name] = value
    col.add_note(note, col.decks.id(deck))


def _collection(folder: Path) -> Any:
    folder.mkdir(parents=True, exist_ok=True)
    col: Any = Collection(str(folder / "collection.anki2"))
    col.media.write_data("paris.png", png(*PICTURE_SIZE, (200, 40, 40)))
    col.media.write_data("_bg.png", png(*BG_SIZE, (230, 230, 200)))
    return col


def _export(col: Any, out: Path, deck: str) -> None:
    options = ExportAnkiPackageOptions(
        with_scheduling=False, with_deck_configs=False, with_media=True, legacy=False
    )
    col.export_anki_package(
        out_path=str(out),
        options=options,
        limit=ExportLimit(deck_id=col.decks.id(deck, create=False)),
    )
    col.close()


def picture_deck(folder: Path) -> Path:
    """A custom note type (own CSS, scoped at import) with a picture on the front."""
    col = _collection(folder)
    picture = col.models.copy(col.models.by_name("Basic"))
    picture["name"] = "Picture card"
    picture["css"] = PICTURE_CSS
    picture["tmpls"][0]["qfmt"] = '<div class="prompt">{{Front}}</div>'
    picture["tmpls"][0]["afmt"] = '{{FrontSide}}<hr id=answer><div class="answer">{{Back}}</div>'
    col.models.update_dict(picture)
    _add(
        col,
        "Picture card",
        "Pictures",
        {
            "Front": 'Which city? <img src="paris.png" alt="a red square">',
            "Back": "Paris, the <b>capital</b>",
        },
    )
    _export(col, folder / "pictures.apkg", "Pictures")
    return folder / "pictures.apkg"


def cloze_deck(folder: Path) -> Path:
    col = _collection(folder)
    fields = {
        "Text": "{{c1::Paris::city}} is the capital of {{c2::France}}.",
        "Back Extra": "<i>Europe</i>",
    }
    _add(col, "Cloze", "Clozes", fields)
    _export(col, folder / "cloze.apkg", "Clozes")
    return folder / "cloze.apkg"


def math_deck(folder: Path) -> Path:
    col = _collection(folder)
    fields = {
        "Front": "Solve \\(x^2 = 4\\) for \\(x\\)",
        "Back": "\\[ x = \\pm 2 \\] since \\(\\frac{4}{2} = 2\\)",
    }
    _add(col, "Basic", "Maths", fields)
    _export(col, folder / "math.apkg", "Maths")
    return folder / "math.apkg"
