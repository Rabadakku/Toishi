"""Anki's stock note types (as Anki 26.09 creates them) and the Mastery Problem note type
(docs/card-format.md "Anki compatibility"). A plain-text export carries only a note type's
name, so its notes are built with these definitions."""

from core.importers.anki.model import (
    STOCK_BASIC,
    STOCK_CLOZE,
    STOCK_OPTIONAL_REVERSED,
    STOCK_REVERSED,
    STOCK_TYPING,
    Notetype,
    Template,
)

TOISHI_PROBLEM = "Mastery Problem"
TOISHI_FIELDS = (
    "ID",
    "Kind",
    "Skill",
    "Uses",
    "Difficulty",
    "AnswerType",
    "Answer",
    "Options",
    "Question",
    "Hints",
    "Solution",
    "CuedQuestion",
    "Wrong",
    "Calculator",
    "Source",
    "License",
)

STOCK_CSS = (
    ".card {\n    font-family: arial;\n    font-size: 20px;\n    line-height: 1.5;\n"
    "    text-align: center;\n    color: black;\n    background-color: white;\n}\n"
)
CLOZE_CSS = (
    STOCK_CSS + ".cloze {\n    font-weight: bold;\n    color: blue;\n}\n"
    ".nightMode .cloze {\n    color: lightblue;\n}\n"
)
# Older Anki versions' stock CSS (no line-height); compared without whitespace.
_OLDER_CSS = (
    ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n"
    " background-color: white;\n}\n"
)
_CLOZE_RULES = ".cloze {\n font-weight: bold;\n color: blue;\n}\n"
_NIGHT_CLOZE = ".nightMode .cloze {\n color: lightblue;\n}\n"

_ANSWER = "{{FrontSide}}\n\n<hr id=answer>\n\n"


def _squash(css: str) -> str:
    return "".join(css.split())


STOCK_CSS_VARIANTS = frozenset(
    _squash(css)
    for css in (
        "",
        STOCK_CSS,
        CLOZE_CSS,
        _OLDER_CSS,
        _OLDER_CSS + _CLOZE_RULES,
        _OLDER_CSS + _CLOZE_RULES + _NIGHT_CLOZE,
    )
)


def is_stock_css(css: str) -> bool:
    """Anki's default styling: dropped on import, so the app's own styling applies."""
    return _squash(css) in STOCK_CSS_VARIANTS


def _basic(ntid: int, name: str, kind: int, fields: tuple[str, ...], *cards: Template) -> Notetype:
    return Notetype(ntid, name, False, fields, cards, STOCK_CSS, kind)


STOCK_NOTETYPES: dict[str, Notetype] = {
    nt.name.casefold(): nt
    for nt in (
        _basic(
            -1,
            "Basic",
            STOCK_BASIC,
            ("Front", "Back"),
            Template("Card 1", 0, "{{Front}}", _ANSWER + "{{Back}}"),
        ),
        _basic(
            -2,
            "Basic (and reversed card)",
            STOCK_REVERSED,
            ("Front", "Back"),
            Template("Card 1", 0, "{{Front}}", _ANSWER + "{{Back}}"),
            Template("Card 2", 1, "{{Back}}", _ANSWER + "{{Front}}"),
        ),
        _basic(
            -3,
            "Basic (optional reversed card)",
            STOCK_OPTIONAL_REVERSED,
            ("Front", "Back", "Add Reverse"),
            Template("Card 1", 0, "{{Front}}", _ANSWER + "{{Back}}"),
            Template(
                "Card 2", 1, "{{#Add Reverse}}{{Back}}{{/Add Reverse}}", _ANSWER + "{{Front}}"
            ),
        ),
        _basic(
            -4,
            "Basic (type in the answer)",
            STOCK_TYPING,
            ("Front", "Back"),
            Template(
                "Card 1",
                0,
                "{{Front}}\n\n{{type:Back}}",
                "{{Front}}\n\n<hr id=answer>\n\n{{type:Back}}",
            ),
        ),
        Notetype(
            -5,
            "Cloze",
            True,
            ("Text", "Back Extra"),
            (Template("Cloze", 0, "{{cloze:Text}}", "{{cloze:Text}}<br>\n{{Back Extra}}"),),
            CLOZE_CSS,
            STOCK_CLOZE,
        ),
        Notetype(
            -6,
            TOISHI_PROBLEM,
            False,
            TOISHI_FIELDS,
            (Template("Card 1", 0, "{{Question}}", _ANSWER + "{{Solution}}"),),
            "",
        ),
    )
}


def stock_notetype(name: str) -> Notetype | None:
    return STOCK_NOTETYPES.get(name.strip().casefold())
