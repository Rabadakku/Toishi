"""What the readers hand the planner: one neutral shape for .apkg, .colpkg and plain text.

Packages give note types, notes, cards, deck options and the review log as Anki stored
them; a plain-text export gives notes of stock note types and no cards (the planner
generates them as Anki would). Deck names use "::" between levels.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

type AnkiFormat = Literal["apkg", "colpkg", "anki-text"]

# Note type config `original_stock_kind` (Anki 2.1.62+), schema 11 `originalStockKind`.
STOCK_BASIC, STOCK_REVERSED, STOCK_OPTIONAL_REVERSED, STOCK_TYPING, STOCK_CLOZE = 1, 2, 3, 4, 5
STOCK_IMAGE_OCCLUSION = 6


@dataclass(frozen=True, slots=True)
class Template:
    name: str
    ord: int
    qfmt: str
    afmt: str


@dataclass(frozen=True, slots=True)
class Notetype:
    id: int
    name: str
    is_cloze: bool
    fields: tuple[str, ...]
    templates: tuple[Template, ...]
    css: str = ""
    stock_kind: int = 0  # original_stock_kind; 0 when unknown


@dataclass(frozen=True, slots=True)
class Note:
    id: int
    guid: str
    notetype_id: int
    fields: tuple[str, ...]
    tags: tuple[str, ...]
    line: int  # where it is: the note's number in a package, the row's line in a text file
    deck: str | None = None  # plain text only: packages give each card its deck


@dataclass(frozen=True, slots=True)
class Card:
    id: int
    note_id: int
    ord: int
    deck: str  # home deck (a card in a filtered deck counts in its original deck)
    config_id: int | None  # the home deck's options preset
    type: int = 0  # 0 new, 1 learning, 2 review, 3 relearning
    queue: int = 0
    ivl: int = 0
    factor: int = 0
    reps: int = 0
    lapses: int = 0
    flags: int = 0
    data: Mapping[str, Any] = field(default_factory=dict)  # FSRS memory: s, d, dr, lrt


@dataclass(frozen=True, slots=True)
class DeckConfig:
    id: int
    name: str
    fsrs_params: tuple[float, ...] = ()  # fsrs_params_6, else _5, else _4 (as Anki picks)
    desired_retention: float | None = None
    ignore_before_ms: int = 0


@dataclass(frozen=True, slots=True)
class Revlog:
    id: int  # review time, epoch ms
    card_id: int
    ease: int  # 1-4 = Again..Easy; 0 = manual
    ivl: int  # days if > 0, seconds if < 0
    last_ivl: int
    factor: int
    time: int  # answer time, ms
    type: int  # 0 learn, 1 review, 2 relearn, 3 filtered, 4 manual, 5 rescheduled


class MediaSource(Protocol):
    def names(self) -> frozenset[str]: ...
    def read(self, name: str) -> bytes: ...


class NoMedia:
    def names(self) -> frozenset[str]:
        return frozenset()

    def read(self, name: str) -> bytes:
        raise KeyError(name)


@dataclass(slots=True)
class AnkiData:
    name: str  # the file name shown in reports
    format: AnkiFormat
    notetypes: dict[int, Notetype]
    notes: list[Note]
    cards: list[Card] | None  # None: generate them (plain text)
    deck_configs: dict[int, DeckConfig] = field(default_factory=dict)
    revlog: list[Revlog] = field(default_factory=list)
    rollover_hour: int | None = None  # None: Anki's default, 4 AM
    minutes_west: int | None = None  # the collection's last UTC offset (colpkg only)
    media: MediaSource = field(default_factory=NoMedia)
    schema: int | None = None
    package_version: int | None = None  # 1, 2 (legacy) or 3 (latest)
    warnings: list[str] = field(default_factory=list)
