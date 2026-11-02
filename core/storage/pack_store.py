"""PackStore: read access to all content: the attached packs, then the student's own.

Cards and skills are found by permanent id (DATA-4). Sources are searched in attach
order, and the student's own content (user.db, tables prefixed "user_") comes last.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from core.model import (
    Card,
    CardRef,
    CardRevision,
    Course,
    PackInfo,
    PackPace,
    Section,
    Skill,
    SkillEdge,
    Unit,
)
from core.storage.connection import Database
from core.storage.content import ContentReader
from core.storage.packs import has_model_tables, read_pace
from core.storage.schema import USER_CONTENT_PREFIX

USER_SOURCE = "user"


class PackStore:
    def __init__(self, db: Database, *, include_user: bool = True) -> None:
        self._db = db
        self._include_user = include_user

    @contextmanager
    def _sources(self) -> Iterator[list[ContentReader]]:
        with self._db.reading(packs=True) as conn:
            readers = [
                ContentReader(
                    conn,
                    p.alias,
                    "",
                    p.info.id,
                    version=p.info.schema_version,
                    card_times=has_model_tables(p.info.schema_version),
                )
                for p in self._db.packs
            ]
            if self._include_user:
                readers.append(ContentReader(conn, "main", USER_CONTENT_PREFIX, USER_SOURCE))
            yield readers

    def _first[T](self, fetch: Callable[[ContentReader], T | None]) -> T | None:
        with self._sources() as sources:
            for source in sources:
                found = fetch(source)
                if found is not None:
                    return found
        return None

    def _all[T](self, fetch: Callable[[ContentReader], list[T]]) -> list[T]:
        with self._sources() as sources:
            return [item for source in sources for item in fetch(source)]

    # ------------------------------------------------------------ packs

    def packs(self) -> list[PackInfo]:
        return [p.info for p in self._db.packs]

    def pace(self, pack_id: str) -> PackPace | None:
        """The pack's pace standard (student-model spec 4.1): minutes per solution step,
        weekly class hours, and the sections in course order with their standard hours.
        None when no such pack is attached."""
        for pack in self._db.packs:
            if pack.info.id == pack_id:
                with self._db.reading(packs=True) as conn:
                    return read_pace(conn, pack.alias, pack.info.schema_version)
        return None

    def media(self, pack_id: str, name: str) -> bytes | None:
        for pack in self._db.packs:
            if pack.info.id == pack_id:
                with self._db.reading(packs=True) as conn:
                    row = conn.execute(
                        f"SELECT data FROM {pack.alias}.media WHERE name = ?", (name,)
                    ).fetchone()
                return None if row is None else bytes(row[0])
        return None

    # ------------------------------------------------------------ course tree and skills

    def courses(self) -> list[Course]:
        return self._all(lambda s: s.courses())

    def course_sources(self) -> dict[str, str]:
        """Course id -> the pack id that holds it ("user" for the student's own); the first
        source in attach order wins, as for every other lookup."""
        out: dict[str, str] = {}
        with self._sources() as sources:
            for source in sources:
                for course in source.courses():
                    out.setdefault(course.id, source.source)
        return out

    def units(self) -> list[Unit]:
        return self._all(lambda s: s.units())

    def sections(self) -> list[Section]:
        return self._all(lambda s: s.sections())

    def skill(self, skill_id: str) -> Skill | None:
        return self._first(lambda s: s.skill(skill_id))

    def skills(self) -> list[Skill]:
        return self._all(lambda s: s.skills())

    def skills_in_section(self, section_id: str) -> list[Skill]:
        return self._all(lambda s: s.skills(where="section_id = ?", params=(section_id,)))

    def edges(self, kind: str | None = None) -> list[SkillEdge]:
        return self._all(lambda s: s.edges(kind))

    # ------------------------------------------------------------ cards

    def card(self, card_id: str) -> Card | None:
        return self._first(lambda s: s.card(card_id))

    def card_source(self, card_id: str) -> str | None:
        """The pack id holding the card, "user" for the student's own, or None."""
        return self._first(lambda s: s.source if s.has_card(card_id) else None)

    def card_refs(
        self, *, skill_id: str | None = None, include_retired: bool = False
    ) -> list[CardRef]:
        return self._all(lambda s: s.card_refs(skill_id=skill_id, include_retired=include_retired))

    def cards_for_skill(self, skill_id: str, *, include_retired: bool = False) -> list[Card]:
        return self._all(lambda s: s.cards(skill_id=skill_id, include_retired=include_retired))

    def revisions(self, card_id: str) -> list[CardRevision]:
        return self._all(lambda s: s.revisions(card_id))
