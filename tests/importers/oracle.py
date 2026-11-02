"""The official `anki` package as a test oracle (dev only, AGPL; ADR-0015). Tests that use it
skip when it isn't installed."""

import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

anki = pytest.importorskip("anki")

from anki.collection import (  # noqa: E402
    Collection,
    ImportAnkiPackageOptions,
    ImportAnkiPackageRequest,
)

HINT_ID = re.compile(r"hint[0-9a-f]{16}")
SOUND = re.compile(r"\[sound:[^]]+\]|\[anki:tts[^\]]*\].*?\[/anki:tts\]", re.S)


@contextmanager
def collection() -> Iterator[Any]:
    folder = tempfile.mkdtemp()
    col = Collection(str(Path(folder) / "collection.anki2"))
    try:
        yield col
    finally:
        col.close()


def import_package(col: Any, path: Path) -> None:
    options = ImportAnkiPackageOptions(with_scheduling=True, with_deck_configs=True)
    col.import_anki_package(ImportAnkiPackageRequest(package_path=str(path), options=options))


def full_render(col: Any, card_id: int) -> tuple[str, str, bool]:
    """Anki's own full render of a card (rslib render_card, no CSS, no av-tag rewrite)."""
    out = col._backend.render_existing_card(card_id=card_id, browser=False, partial_render=False)
    return out.question_nodes[0].text, out.answer_nodes[0].text, out.is_empty


def av_tags(text: str, side: str) -> str:
    """What pylib's card.question()/answer() do to [sound:] and TTS tags."""
    count = iter(range(1000))
    return SOUND.sub(lambda _m: f"[anki:play:{side}:{next(count)}]", text)


def same_hint(text: str) -> str:
    """Anki's hint ids use BLAKE3; ours BLAKE2b. Everything else must match."""
    return HINT_ID.sub("hintID", text)
