"""Generic mapping between the user-side dataclasses in core.model and user.db rows.

Each table's columns are exactly the dataclass's fields, in order (a test checks).
bool <-> INTEGER 0/1, date <-> ISO text, dict/tuple <-> JSON text; the rest is as is.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import json
import sqlite3
import types
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import date
from typing import Any, TypeAliasType, Union, cast, get_args, get_origin, get_type_hints

from core import model

type Row = dict[str, Any]


def dumps(value: Any) -> str:
    """Canonical JSON: sorted keys, no NaN (SQLite's json_valid rejects it anyway)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class Table:
    name: str
    record: type[Any]
    pk: tuple[str, ...]
    autoinc: bool = False
    stamp: tuple[str, ...] = ()  # *_at fields set to "now" when left at 0

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(f.name for f in fields(self.record))


def _table(name: str, record: type[Any], pk: tuple[str, ...], *stamp: str) -> Table:
    return Table(name, record, pk, autoinc=pk == ("id",), stamp=stamp)


# Rows an attempt may change; each one is snapshotted for exact undo.
STATE_TABLES: dict[type[Any], Table] = {
    t.record: t
    for t in (
        _table("skill_state", model.SkillState, ("skill_id",), "updated_at"),
        _table("skill_tier", model.SkillTierState, ("skill_id", "tier"), "updated_at"),
        _table("skill_shadow", model.SkillShadow, ("skill_id",), "updated_at"),
        _table("flashcard_state", model.FlashcardState, ("card_id", "ord"), "updated_at"),
        _table("card_user", model.CardUser, ("card_id",), "updated_at"),
        _table("pending_check", model.PendingCheck, ("id",), "created_at"),
        _table("weak_spot", model.WeakSpot, ("id",), "flagged_at"),
        _table("diagnostic_set", model.DiagnosticSet, ("id",), "created_at"),
    )
}
STATE_TABLES_BY_NAME: dict[str, Table] = {t.name: t for t in STATE_TABLES.values()}

OTHER_TABLES: dict[type[Any], Table] = {
    t.record: t
    for t in (
        _table("course_goal", model.CourseGoal, ("course_id",), "updated_at"),
        _table("exam", model.Exam, ("id",), "created_at"),
        _table("section_state", model.SectionState, ("section_id",), "changed_at"),
        _table("card_mark", model.CardMark, ("card_id",), "updated_at"),
        _table("session", model.SessionState, ("id",), "started_at", "updated_at"),
        _table("attempt", model.Attempt, ("id",), "at"),
        _table("review_log", model.ReviewEvent, ("id",), "at"),
        _table("implicit_credit", model.ImplicitCredit, ("id",), "at"),
        _table("attempt_void", model.AttemptVoid, ("id",), "at"),
        _table("dispute", model.Dispute, ("id",), "at"),
        _table("report", model.Report, ("id",), "at"),
        _table("import_record", model.ImportRecord, ("id",), "at"),
        # the student's own content that packs don't have (v2, ADR-0011)
        Table("user_template", model.TemplateSource, ("id",), stamp=("updated_at",)),
        Table("user_media", model.CardMedia, ("card_id", "ref")),
        # the student model and planner (v3, wave 2)
        Table("course_settings", model.CourseSetup, ("course_id",), stamp=("updated_at",)),
        Table("learner_params", model.LearnerParams, ("version",), stamp=("created_at",)),
    )
}
ALL_TABLES: dict[type[Any], Table] = {**STATE_TABLES, **OTHER_TABLES}


def table_for(record_type: type[Any]) -> Table:
    try:
        return ALL_TABLES[record_type]
    except KeyError:
        raise TypeError(f"{record_type.__name__} is not stored in a user.db table") from None


# ---------------------------------------------------------------- conversion

_PLAIN, _BOOL, _DATE, _JSON, _TUPLE = "plain", "bool", "date", "json", "tuple"


def _unwrap(tp: Any) -> Any:
    while isinstance(tp, TypeAliasType):
        tp = tp.__value__
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        options = [a for a in get_args(tp) if a is not type(None)]
        if len(options) == 1:
            return _unwrap(options[0])
    return tp


def _kind(tp: Any) -> str:
    tp = _unwrap(tp)
    if tp is bool:
        return _BOOL
    if tp is date:
        return _DATE
    origin = get_origin(tp)
    if origin is tuple:
        return _TUPLE
    if origin in (dict, Mapping) or tp is dict:
        return _JSON
    return _PLAIN


_KINDS: dict[type[Any], dict[str, str]] = {}


def _kinds(record_type: type[Any]) -> dict[str, str]:
    kinds = _KINDS.get(record_type)
    if kinds is None:
        hints = get_type_hints(record_type)
        kinds = {f.name: _kind(hints[f.name]) for f in fields(record_type)}
        _KINDS[record_type] = kinds
    return kinds


def to_row(record: Any) -> Row:
    out: Row = {}
    for name, kind in _kinds(type(record)).items():
        value = getattr(record, name)
        if value is None or kind == _PLAIN:
            out[name] = value
        elif kind == _BOOL:
            out[name] = int(value)
        elif kind == _DATE:
            out[name] = cast(date, value).isoformat()
        else:
            out[name] = dumps(list(value) if kind == _TUPLE else value)
    return out


def from_row[R](record_type: type[R], row: Mapping[str, Any]) -> R:
    values: dict[str, Any] = {}
    for name, kind in _kinds(record_type).items():
        value = row[name]
        if value is None or kind == _PLAIN:
            values[name] = value
        elif kind == _BOOL:
            values[name] = bool(value)
        elif kind == _DATE:
            values[name] = date.fromisoformat(value)
        elif kind == _TUPLE:
            values[name] = tuple(json.loads(value))
        else:
            values[name] = json.loads(value)
    return record_type(**values)


def as_dict(row: sqlite3.Row | None) -> Row | None:
    return None if row is None else dict(row)


# ---------------------------------------------------------------- raw row access


def key_of(table: Table, row: Mapping[str, Any]) -> Row:
    return {name: row[name] for name in table.pk}


def _where(table: Table) -> str:
    return " AND ".join(f"{name} = :{name}" for name in table.pk)


def read_row(conn: sqlite3.Connection, table: Table, key: Mapping[str, Any]) -> Row | None:
    cursor = conn.execute(f"SELECT * FROM {table.name} WHERE {_where(table)}", dict(key))
    return as_dict(cursor.fetchone())


def insert_row(conn: sqlite3.Connection, table: Table, row: Mapping[str, Any]) -> int:
    """Insert; an autoincrement id given as None is assigned. Returns the rowid."""
    data = {k: v for k, v in row.items() if not (table.autoinc and k == "id" and v is None)}
    columns = ", ".join(data)
    marks = ", ".join(f":{name}" for name in data)
    cursor = conn.execute(f"INSERT INTO {table.name} ({columns}) VALUES ({marks})", data)
    rowid = cursor.lastrowid
    if rowid is None:
        raise RuntimeError(f"insert into {table.name} returned no rowid")
    return rowid


def upsert_row(conn: sqlite3.Connection, table: Table, row: Mapping[str, Any]) -> None:
    columns = ", ".join(row)
    marks = ", ".join(f":{name}" for name in row)
    updates = ", ".join(f"{name} = excluded.{name}" for name in row if name not in table.pk)
    conflict = ", ".join(table.pk)
    action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
    conn.execute(
        f"INSERT INTO {table.name} ({columns}) VALUES ({marks}) ON CONFLICT ({conflict}) {action}",
        dict(row),
    )


def delete_row(conn: sqlite3.Connection, table: Table, key: Mapping[str, Any]) -> None:
    conn.execute(f"DELETE FROM {table.name} WHERE {_where(table)}", dict(key))


def select[R](
    conn: sqlite3.Connection,
    record_type: type[R],
    where: str = "",
    params: Mapping[str, Any] | tuple[Any, ...] = (),
    order: str = "",
) -> list[R]:
    table = table_for(record_type)
    sql = f"SELECT * FROM {table.name}"
    if where:
        sql += f" WHERE {where}"
    sql += f" ORDER BY {order or ', '.join(table.pk)}"
    return [from_row(record_type, row) for row in conn.execute(sql, params)]


def select_one[R](conn: sqlite3.Connection, record_type: type[R], **key: Any) -> R | None:
    table = table_for(record_type)
    row = read_row(conn, table, key)
    return None if row is None else from_row(record_type, row)
