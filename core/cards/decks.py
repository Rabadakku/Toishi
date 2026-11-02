"""Deck paths (`Course::Unit::Section`) -> the course tree records.

IDs are the deck path prefixes themselves, so a card's section_id is its deck:
course "Calculus I", unit "Calculus I::4 Applications", section the full path. A
one-level deck is its own course, unit and section; deeper levels stay in the section.
"""

from collections.abc import Iterable

from core.model import Course, Section, Unit

SEPARATOR = "::"


def split(deck: str) -> list[str]:
    return [seg.strip() for seg in deck.split(SEPARATOR)]


def normalize(deck: str) -> str:
    return SEPARATOR.join(split(deck))


def tree(decks: Iterable[str | None]) -> list[Course | Unit | Section]:
    out: list[Course | Unit | Section] = []
    courses: dict[str, int] = {}
    units: dict[str, int] = {}
    sections: set[str] = set()
    for deck in decks:
        if not deck:
            continue
        segs = split(deck)
        course_id = segs[0]
        unit_id = SEPARATOR.join(segs[:2])
        section_id = SEPARATOR.join(segs)
        if course_id not in courses:
            courses[course_id] = len(courses)
            out.append(Course(id=course_id, title=segs[0], ord=courses[course_id]))
        if unit_id not in units:
            units[unit_id] = len(units)
            out.append(
                Unit(
                    id=unit_id,
                    course_id=course_id,
                    title=segs[min(1, len(segs) - 1)],
                    ord=units[unit_id],
                )
            )
        if section_id not in sections:
            sections.add(section_id)
            out.append(
                Section(id=section_id, unit_id=unit_id, title=segs[-1], ord=len(sections) - 1)
            )
    return out
