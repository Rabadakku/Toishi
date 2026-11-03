"""Plain words for what the planner says (wave 2): Home and the study screen show these lines
as they are sent, so they name skills and textbook sections, never ids or formulas
(docs/design/wave2-integration.md section 5, "the planner's notes in plain words").

The planner (core.plan) writes its notes for the log: skill ids, deck ids and the numbers
behind a decision. `plain_note` rewrites one for the student:

- the feasibility note's formula becomes a sentence with percentages;
- a parenthesis of numbers ("(predicted pass 0.41: accuracy 0.62, ...)") is dropped;
- a set-aside note becomes the set-aside line with its textbook pointer;
- "See the textbook section." names the section when the skill has a pointer;
- skill ids become skill names and deck ids section titles.
"""

import re
from collections.abc import Collection, Mapping

from core.practice.catalog import Catalog, Textbook

_FEASIBILITY = re.compile(
    r"^At tier (?P<tier>\d+) the best attainable first-try chance is .*= (?P<best>[0-9.]+), "
    r"below the accuracy target (?P<target>[0-9.]+)\.$"
)
_NUMBERS = re.compile(r"\s*\([^()]*\d\.\d[^()]*\)")
_LEADING = re.compile(r"^(?P<skill>[\w.-]+): (?P<rest>.*)$")
_TOKEN = re.compile(r"(?<![\w.:-])[\w.-]+(?:::[\w.-]+)*")
_SEE_TEXTBOOK = "See the textbook section."


def pointer(book: Textbook | None) -> str:
    """ "OpenStax Calculus Vol 1 §4.1" (the book, then its section), or "" without one."""
    if book is None:
        return ""
    return f"{book.book} {book.section}".strip()


def set_aside_line(name: str, book: Textbook | None) -> str:
    """The study screen's notice when the planner sets a skill aside for the day."""
    where = pointer(book)
    return f"{name} is set aside for today." + (f" See {where}." if where else "")


def section_titles(catalog: Catalog) -> dict[str, str]:
    """Deck id -> section title, over every course."""
    return {s.deck: s.title for entry in catalog.courses.values() for s in entry.sections}


def plain_note(note: str, catalog: Catalog, *, set_aside: Collection[str] = ()) -> str:
    """One planner note in plain words (see the module docstring)."""
    found = _FEASIBILITY.match(note)
    if found is not None:
        tier = found["tier"]
        best = float(found["best"])
        target = float(found["target"])
        return (
            f"Your accuracy target of {target:.0%} is above what tier {tier} allows: even with "
            f"every skill in place, first tries top out near {best:.0%}."
        )
    text = _NUMBERS.sub("", note)
    leading = _LEADING.match(text)
    if leading is not None and leading["skill"] in catalog.skill_names:
        skill = leading["skill"]
        book = catalog.textbooks.get(skill)
        if skill in set_aside and "set aside" in leading["rest"]:
            return set_aside_line(catalog.name(skill), book)
        if book is not None:
            text = text.replace(_SEE_TEXTBOOK, f"See {pointer(book)}.")
    return names_in(text, catalog.skill_names, section_titles(catalog))


def names_in(text: str, names: Mapping[str, str], titles: Mapping[str, str]) -> str:
    """Skill ids and deck ids in `text` replaced by skill names and section titles."""

    def swap(match: re.Match[str]) -> str:
        token = match.group(0)
        bare = token.rstrip(".")
        tail = token[len(bare) :]
        if bare in names:
            return names[bare] + tail
        if bare in titles:
            return titles[bare] + tail
        return token

    return _TOKEN.sub(swap, text)


__all__ = ["names_in", "plain_note", "pointer", "section_titles", "set_aside_line"]
