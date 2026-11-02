"""Content rows (course tree, skills, cards) for packs and for the student's own content.

Both use the content tables (content_v2.sql); packs with no prefix in their own file,
user.db with the prefix "user_". The same functions write and read either, so the
student's cards have exactly the shape of pack cards. Writing is always at the current
version; reading also takes v1 packs, whose instances kept their parameter set in
notes_md (ADR-0011): they read back exactly as a v2 pack built from the same source.

`time:` standard times live in a pack-only table (card_time, pack schema v3): packs write
them with write_card_times, and readers of v3 packs read them (`card_times=True`).
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

from core.model import (
    Card,
    CardPart,
    CardRef,
    CardRevision,
    CheckerOptions,
    Choice,
    Course,
    Provenance,
    Section,
    Skill,
    SkillEdge,
    SolutionStep,
    Unit,
    WrongAnswer,
)
from core.storage.rows import dumps
from core.storage.schema import CONTENT_SCHEMA_VERSION, split_v1_notes

CONTENT_VERSION = CONTENT_SCHEMA_VERSION  # the content tables' version in user.db (and packs)
CARD_CHILDREN = ("card_use", "card_step", "card_choice", "card_wrong", "card_part")
CONTENT_TABLES = (
    "course",
    "unit",
    "section",
    "skill",
    "skill_edge",
    "card",
    *CARD_CHILDREN,
    "card_revision",
)


def _upsert(conn: sqlite3.Connection, table: str, row: dict[str, Any], pk: str = "id") -> None:
    columns = ", ".join(row)
    marks = ", ".join(f":{c}" for c in row)
    updates = ", ".join(f"{c} = excluded.{c}" for c in row if c != pk)
    conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({marks}) "
        f"ON CONFLICT ({pk}) DO UPDATE SET {updates}",
        row,
    )


def _insert(conn: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    columns = ", ".join(row)
    marks = ", ".join(f":{c}" for c in row)
    conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({marks})", row)


# ---------------------------------------------------------------- writing


def write_course(conn: sqlite3.Connection, prefix: str, course: Course) -> None:
    _upsert(conn, f"{prefix}course", asdict(course))


def write_unit(conn: sqlite3.Connection, prefix: str, unit: Unit) -> None:
    _upsert(conn, f"{prefix}unit", asdict(unit))


def write_section(conn: sqlite3.Connection, prefix: str, section: Section) -> None:
    _upsert(conn, f"{prefix}section", asdict(section))


def write_skill(conn: sqlite3.Connection, prefix: str, skill: Skill) -> None:
    row = {
        "id": skill.id,
        "name": skill.name,
        "deck": skill.deck,
        "section_id": skill.section_id,
        "textbook_ref": skill.textbook_ref,
        "method_choice": int(skill.method_choice),
        "core": int(skill.core),
        "exam_tier": skill.exam_tier,
        "notes_md": skill.notes_md,
    }
    _upsert(conn, f"{prefix}skill", row)
    conn.execute(f"DELETE FROM {prefix}skill_edge WHERE skill_id = ?", (skill.id,))
    for ord_, edge in enumerate(skill.edges()):
        _insert(
            conn,
            f"{prefix}skill_edge",
            {
                "skill_id": edge.skill_id,
                "kind": edge.kind,
                "other_id": edge.other_id,
                "ord": ord_,
                "weight": edge.weight,
            },
        )


def _checker_json(checker: CheckerOptions) -> str:
    return dumps({k: v for k, v in asdict(checker).items() if v is not None})


def card_row(card: Card) -> dict[str, Any]:
    p = card.provenance
    return {
        "id": card.id,
        "rev": card.rev,
        "kind": card.kind,
        "skill_id": card.skill_id,
        "tier": card.tier,
        "answer_type": card.answer_type,
        "answer": card.answer,
        "checker": _checker_json(card.checker),
        "plot": card.plot,
        "calculator": int(card.calculator),
        "angles": card.angles,
        "cue_required": int(card.cue_required),
        "error_step": card.error_step,
        "tagged": card.tagged,
        "deck": card.deck,
        "section_id": card.section_id,
        "tags": dumps(list(card.tags)),
        "question_md": card.question_md,
        "cued_question_md": card.cued_question_md,
        "hints": dumps(list(card.hints)),
        "answer_md": card.answer_md,
        "solution_md": card.solution_md,
        "rubric": dumps(list(card.rubric)),
        "alternative_solution_md": card.alternative_solution_md,
        "front_md": card.front_md,
        "back_md": card.back_md,
        "text_md": card.text_md,
        "extra_md": card.extra_md,
        "notes_md": card.notes_md,
        "template_id": card.template_id,
        "seed": card.seed,
        "source": p.source,
        "source_url": p.source_url,
        "license": p.license,
        "creators": dumps(list(p.creators)),
        "original_path": p.original_path,
        "original_commit": p.original_commit,
        "modified": int(p.modified),
        "modification_note": p.modification_note,
        "third_party": dumps(list(p.third_party)),
        "translation": p.translation,
        "unofficial_solution": int(p.unofficial_solution),
        "verified": card.verified,
        "status": card.status,
        "params": card.params,
    }


def write_card(conn: sqlite3.Connection, prefix: str, card: Card) -> None:
    """Insert or replace one card with all its child rows."""
    _upsert(conn, f"{prefix}card", card_row(card))
    for child in CARD_CHILDREN:
        conn.execute(f"DELETE FROM {prefix}{child} WHERE card_id = ?", (card.id,))
    cid = card.id
    for ord_, skill_id in enumerate(card.uses):
        _insert(conn, f"{prefix}card_use", {"card_id": cid, "ord": ord_, "skill_id": skill_id})
    for section, steps in (
        ("solution", card.solution),
        ("alternative", card.alternative_solution),
        ("shown-work", card.shown_work),
    ):
        for step in steps:
            _insert(
                conn, f"{prefix}card_step", {"card_id": cid, "section": section, **asdict(step)}
            )
    _write_choices(conn, prefix, cid, "", "choice", card.choices)
    _write_choices(conn, prefix, cid, "", "reason", card.reasons)
    _write_wrong(conn, prefix, cid, "", card.wrong)
    for ord_, part in enumerate(card.parts):
        _insert(
            conn,
            f"{prefix}card_part",
            {
                "card_id": cid,
                "ord": ord_,
                "label": part.label,
                "prompt_md": part.prompt_md,
                "answer_type": part.answer_type,
                "answer": part.answer,
                "checker": _checker_json(part.checker),
                "skill_id": part.skill_id,
            },
        )
        _write_choices(conn, prefix, cid, part.label, "choice", part.choices)
        _write_wrong(conn, prefix, cid, part.label, part.wrong)


def write_card_times(conn: sqlite3.Connection, card: Card) -> None:
    """A pack's `time:` rows for one card: the card's own (part '') and its parts'. Packs
    only (pack schema v3): user.db has no card_time table."""
    conn.execute("DELETE FROM card_time WHERE card_id = ?", (card.id,))
    timed = [("", card.time_minutes), *((p.label, p.time_minutes) for p in card.parts)]
    for part, minutes in timed:
        if minutes is not None:
            _insert(conn, "card_time", {"card_id": card.id, "part": part, "minutes": minutes})


def _write_choices(
    conn: sqlite3.Connection,
    prefix: str,
    card_id: str,
    part: str,
    role: str,
    choices: tuple[Choice, ...],
) -> None:
    for ord_, choice in enumerate(choices):
        _insert(
            conn,
            f"{prefix}card_choice",
            {
                "card_id": card_id,
                "part": part,
                "role": role,
                "ord": ord_,
                "text_md": choice.text_md,
                "correct": int(choice.correct),
            },
        )


def _write_wrong(
    conn: sqlite3.Connection, prefix: str, card_id: str, part: str, wrong: tuple[WrongAnswer, ...]
) -> None:
    for ord_, item in enumerate(wrong):
        _insert(
            conn,
            f"{prefix}card_wrong",
            {"card_id": card_id, "part": part, "ord": ord_, **asdict(item)},
        )


def write_revision(conn: sqlite3.Connection, prefix: str, revision: CardRevision) -> None:
    row = asdict(revision)
    row["answer_changed"] = int(revision.answer_changed)
    _insert(conn, f"{prefix}card_revision", row)


# ---------------------------------------------------------------- reading


class ContentReader:
    """Reads content tables from one source: an attached pack or user.db's own tables.
    `version` is the source's schema version (a pack's; user.db's own tables are always
    the current content version). `card_times`: the source has card_time (a v3 pack)."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        schema: str,
        prefix: str,
        source: str,
        *,
        version: int = CONTENT_VERSION,
        card_times: bool = False,
    ) -> None:
        self._conn = conn
        self._t = f"{schema}.{prefix}"
        self.source = source
        self.version = version
        self.card_times = card_times

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return self._conn.execute(sql.replace("~", self._t), params).fetchall()

    def courses(self) -> list[Course]:
        return [Course(**dict(r)) for r in self._rows("SELECT * FROM ~course ORDER BY ord, id")]

    def units(self) -> list[Unit]:
        return [Unit(**dict(r)) for r in self._rows("SELECT * FROM ~unit ORDER BY ord, id")]

    def sections(self) -> list[Section]:
        rows = self._rows("SELECT * FROM ~section ORDER BY ord, id")
        return [Section(**dict(r)) for r in rows]

    def skill_ids(self) -> list[str]:
        return [str(r[0]) for r in self._rows("SELECT id FROM ~skill ORDER BY id")]

    def skill(self, skill_id: str) -> Skill | None:
        found = self.skills(where="id = ?", params=(skill_id,))
        return found[0] if found else None

    def skills(self, *, where: str = "", params: tuple[Any, ...] = ()) -> list[Skill]:
        sql = "SELECT * FROM ~skill" + (f" WHERE {where}" if where else "") + " ORDER BY id"
        out = []
        for row in self._rows(sql, params):
            edges = self._rows(
                "SELECT * FROM ~skill_edge WHERE skill_id = ? ORDER BY ord", (row["id"],)
            )
            out.append(
                Skill(
                    id=row["id"],
                    name=row["name"],
                    deck=row["deck"],
                    section_id=row["section_id"],
                    textbook_ref=row["textbook_ref"],
                    method_choice=bool(row["method_choice"]),
                    core=bool(row["core"]),
                    exam_tier=row["exam_tier"],
                    notes_md=row["notes_md"],
                    requires=tuple(e["other_id"] for e in edges if e["kind"] == "requires"),
                    encompasses=tuple(
                        (e["other_id"], e["weight"]) for e in edges if e["kind"] == "encompasses"
                    ),
                    confusable=tuple(e["other_id"] for e in edges if e["kind"] == "confusable"),
                )
            )
        return out

    def edges(self, kind: str | None = None) -> list[SkillEdge]:
        sql = "SELECT * FROM ~skill_edge" + (" WHERE kind = ?" if kind else "")
        rows = self._rows(sql + " ORDER BY skill_id, ord", (kind,) if kind else ())
        return [
            SkillEdge(
                kind=r["kind"], skill_id=r["skill_id"], other_id=r["other_id"], weight=r["weight"]
            )
            for r in rows
        ]

    def card_ids(self) -> list[str]:
        return [str(r[0]) for r in self._rows("SELECT id FROM ~card ORDER BY id")]

    def has_card(self, card_id: str) -> bool:
        return bool(self._rows("SELECT 1 FROM ~card WHERE id = ?", (card_id,)))

    def card(self, card_id: str) -> Card | None:
        rows = self._rows("SELECT * FROM ~card WHERE id = ?", (card_id,))
        return self._card(rows[0]) if rows else None

    def cards(self, *, skill_id: str | None = None, include_retired: bool = True) -> list[Card]:
        where, params = self._card_filter(skill_id, include_retired)
        return [
            self._card(r) for r in self._rows(f"SELECT * FROM ~card{where} ORDER BY id", params)
        ]

    def card_refs(
        self, *, skill_id: str | None = None, include_retired: bool = False
    ) -> list[CardRef]:
        where, params = self._card_filter(skill_id, include_retired)
        sql = (
            "SELECT id, rev, kind, skill_id, tier, template_id, seed, status, cue_required, "
            f"cued_question_md IS NOT NULL AS has_cued, section_id FROM ~card{where} ORDER BY id"
        )
        return [
            CardRef(
                id=r["id"],
                rev=r["rev"],
                kind=r["kind"],
                skill_id=r["skill_id"],
                tier=r["tier"],
                template_id=r["template_id"],
                seed=r["seed"],
                status=r["status"],
                cue_required=bool(r["cue_required"]),
                has_cued_question=bool(r["has_cued"]),
                source=self.source,
                section_id=r["section_id"],
            )
            for r in self._rows(sql, params)
        ]

    @staticmethod
    def _card_filter(skill_id: str | None, include_retired: bool) -> tuple[str, tuple[Any, ...]]:
        clauses: list[str] = []
        params: tuple[Any, ...] = ()
        if skill_id is not None:
            clauses.append("skill_id = ?")
            params = (skill_id,)
        if not include_retired:
            clauses.append("status = 'active'")
        return (" WHERE " + " AND ".join(clauses) if clauses else ""), params

    def revisions(self, card_id: str) -> list[CardRevision]:
        rows = self._rows("SELECT * FROM ~card_revision WHERE card_id = ? ORDER BY rev", (card_id,))
        return [
            CardRevision(
                card_id=r["card_id"],
                rev=r["rev"],
                changed_at=r["changed_at"],
                note=r["note"],
                answer_changed=bool(r["answer_changed"]),
            )
            for r in rows
        ]

    def _card(self, row: sqlite3.Row) -> Card:
        cid = row["id"]
        steps = self._rows(
            "SELECT * FROM ~card_step WHERE card_id = ? ORDER BY section, number", (cid,)
        )
        choices = self._rows(
            "SELECT * FROM ~card_choice WHERE card_id = ? ORDER BY part, role, ord", (cid,)
        )
        wrong = self._rows("SELECT * FROM ~card_wrong WHERE card_id = ? ORDER BY part, ord", (cid,))
        uses = self._rows("SELECT skill_id FROM ~card_use WHERE card_id = ? ORDER BY ord", (cid,))
        parts = self._rows("SELECT * FROM ~card_part WHERE card_id = ? ORDER BY ord", (cid,))
        times: dict[str, float] = {}
        if self.card_times:
            found = self._rows("SELECT part, minutes FROM ~card_time WHERE card_id = ?", (cid,))
            times = {t["part"]: t["minutes"] for t in found}

        def step_list(section: str) -> tuple[SolutionStep, ...]:
            return tuple(
                SolutionStep(
                    number=s["number"],
                    skill_id=s["skill_id"],
                    label=s["label"],
                    body_md=s["body_md"],
                )
                for s in steps
                if s["section"] == section
            )

        def choice_list(part: str, role: str) -> tuple[Choice, ...]:
            return tuple(
                Choice(text_md=c["text_md"], correct=bool(c["correct"]))
                for c in choices
                if c["part"] == part and c["role"] == role
            )

        def wrong_list(part: str) -> tuple[WrongAnswer, ...]:
            return tuple(
                WrongAnswer(answer=w["answer"], feedback=w["feedback"], step=w["step"])
                for w in wrong
                if w["part"] == part
            )

        provenance = Provenance(
            source=row["source"],
            source_url=row["source_url"],
            license=row["license"],
            creators=tuple(json.loads(row["creators"])),
            original_path=row["original_path"],
            original_commit=row["original_commit"],
            modified=bool(row["modified"]),
            modification_note=row["modification_note"],
            third_party=tuple(json.loads(row["third_party"])),
            translation=row["translation"],
            unofficial_solution=bool(row["unofficial_solution"]),
        )
        if self.version >= 2:
            params, notes = row["params"], row["notes_md"]
        else:
            params, notes = split_v1_notes(row["template_id"], row["notes_md"])
        return Card(
            id=cid,
            rev=row["rev"],
            kind=row["kind"],
            skill_id=row["skill_id"],
            uses=tuple(u["skill_id"] for u in uses),
            tier=row["tier"],
            time_minutes=times.get(""),
            answer_type=row["answer_type"],
            answer=row["answer"],
            checker=CheckerOptions(**json.loads(row["checker"])),
            wrong=wrong_list(""),
            plot=row["plot"],
            calculator=bool(row["calculator"]),
            angles=row["angles"],
            cue_required=bool(row["cue_required"]),
            error_step=row["error_step"],
            tagged=row["tagged"],
            deck=row["deck"],
            section_id=row["section_id"],
            tags=tuple(json.loads(row["tags"])),
            question_md=row["question_md"],
            cued_question_md=row["cued_question_md"],
            choices=choice_list("", "choice"),
            shown_work=step_list("shown-work"),
            reasons=choice_list("", "reason"),
            parts=tuple(
                CardPart(
                    label=p["label"],
                    prompt_md=p["prompt_md"],
                    answer_type=p["answer_type"],
                    answer=p["answer"],
                    checker=CheckerOptions(**json.loads(p["checker"])),
                    skill_id=p["skill_id"],
                    choices=choice_list(p["label"], "choice"),
                    wrong=wrong_list(p["label"]),
                    time_minutes=times.get(p["label"]),
                )
                for p in parts
            ),
            hints=tuple(json.loads(row["hints"])),
            answer_md=row["answer_md"],
            solution=step_list("solution"),
            solution_md=row["solution_md"],
            rubric=tuple(json.loads(row["rubric"])),
            alternative_solution=step_list("alternative"),
            alternative_solution_md=row["alternative_solution_md"],
            front_md=row["front_md"],
            back_md=row["back_md"],
            text_md=row["text_md"],
            extra_md=row["extra_md"],
            notes_md=notes,
            template_id=row["template_id"],
            seed=row["seed"],
            params=params,
            provenance=provenance,
            verified=row["verified"],
            status=row["status"],
        )


# ---------------------------------------------------------------- hashing


def _ordered_rows(conn: sqlite3.Connection, table: str) -> Iterator[tuple[Any, ...]]:
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    keys = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]] or ["rowid"]
    yield tuple(r["name"] for r in info)
    yield from (tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY {', '.join(keys)}"))


def content_hash(conn: sqlite3.Connection, tables: tuple[str, ...]) -> str:
    """sha256 over every row of the given tables in primary-key order."""
    digest = hashlib.sha256()
    for table in tables:
        digest.update(f"\x00table {table}\n".encode())
        for row in _ordered_rows(conn, table):
            values = [v.hex() if isinstance(v, bytes) else v for v in row]
            digest.update(dumps(values).encode())
            digest.update(b"\n")
    return "sha256:" + digest.hexdigest()
