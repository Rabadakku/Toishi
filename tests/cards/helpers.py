"""Small builders for card-file tests."""

from core.cards import LoadResult, Source, load
from core.model import Card

HEADER = "---\nformat: mastery-cards 1\ndeck: Test::Unit::Section\n---\n"


def cards_file(body: str, header: str = HEADER) -> str:
    return header + "\n" + body.strip("\n") + "\n"


def load_text(text: str, name: str = "t.cards.md", **kwargs: object) -> LoadResult:
    return load([Source(name, text)], **kwargs)  # type: ignore[arg-type]


def only_card(result: LoadResult) -> Card:
    assert not result.errors(), result.errors()
    assert len(result.cards) == 1, [a.card.id for a in result.cards]
    return result.cards[0].card


def rejection(result: LoadResult) -> tuple[int, str]:
    """(line, first reason) of the only rejected card or file problem."""
    if result.file_problems:
        p = result.file_problems[0]
        return p.line, p.message
    assert len(result.rejected) == 1, result.rejected
    r = result.rejected[0]
    return r.line, r.reasons[0]
