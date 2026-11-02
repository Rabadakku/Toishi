"""Reading an Anki collection (SQLite) into AnkiData, for schema 11 and schema 15-18.

- Schema 11 keeps note types, decks, deck options and config as JSON in the `col` row.
- Schema 15+ (packages from Anki 2.1.50+ are 18) has `notetypes`, `fields`, `templates`,
  `decks`, `deck_config` and `config` tables with protobuf blobs; names use the `unicase`
  collation (registered by the caller), and deck names separate levels with \\x1f.
  `fields` and `templates` are always joined to `notetypes`: exports keep leftover rows for
  stock note types that aren't in the package.
- A card in a filtered deck belongs to its original deck (`odid`).
"""

import json
import sqlite3
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from core.importers.anki import protobuf as pb
from core.importers.anki.errors import AnkiImportError
from core.importers.anki.model import (
    AnkiData,
    AnkiFormat,
    Card,
    DeckConfig,
    Note,
    Notetype,
    Revlog,
    Template,
)

SUPPORTED_SCHEMAS = (11, 15, 16, 17, 18)


def read_collection(conn: sqlite3.Connection, *, name: str, format: AnkiFormat) -> AnkiData:
    try:
        return _read(conn, name, format)
    except AnkiImportError:
        raise
    except (sqlite3.Error, pb.ProtoError, ValueError, TypeError, KeyError) as exc:
        raise AnkiImportError(f"the collection is damaged: {exc}") from None


def _read(conn: sqlite3.Connection, name: str, format: AnkiFormat) -> AnkiData:
    row = conn.execute("SELECT ver, conf, models, decks, dconf FROM col").fetchone()
    if row is None:
        raise AnkiImportError("the collection has no col row")
    ver = int(row[0])
    if ver not in SUPPORTED_SCHEMAS:
        raise AnkiImportError(f"collection schema {ver} is not supported (11 or 15-18 are)")
    if ver == 11:
        config = _json_object(row[1])
        notetypes = _notetypes_v11(_json_object(row[2]))
        decks, deck_config_ids = _decks_v11(_json_object(row[3]))
        deck_configs = _deck_configs_v11(_json_object(row[4]))
    else:
        config = _config_table(conn)
        notetypes = _notetypes_v18(conn)
        decks, deck_config_ids = _decks_v18(conn)
        deck_configs = _deck_configs_v18(conn)
    notes = _notes(conn)
    cards = _cards(conn, decks, deck_config_ids)
    revlog = [
        Revlog(*(int(v) for v in r))
        for r in conn.execute(
            "SELECT id, cid, ease, ivl, lastIvl, factor, time, type FROM revlog ORDER BY id"
        )
    ]
    rollover = config.get("rollover")
    west = config.get("localOffset")
    return AnkiData(
        name=name,
        format=format,
        notetypes=notetypes,
        notes=notes,
        cards=cards,
        deck_configs=deck_configs,
        revlog=revlog,
        rollover_hour=int(rollover) % 24 if isinstance(rollover, int) else None,
        minutes_west=max(-23 * 60, min(23 * 60, west)) if isinstance(west, int) else None,
        schema=ver,
    )


def _json_object(raw: Any) -> dict[str, Any]:
    if raw in (None, "", b""):
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise AnkiImportError("the collection's settings are damaged")
    return value


def _sorted_by_ord(items: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(items, key=lambda i: int(i.get("ord") or 0))


def _notetypes_v11(models: Mapping[str, Any]) -> dict[int, Notetype]:
    out: dict[int, Notetype] = {}
    for key, m in models.items():
        if not isinstance(m, dict):
            continue
        ntid = int(m.get("id") or key)
        fields = tuple(str(f["name"]) for f in _sorted_by_ord(m.get("flds") or []))
        templates = tuple(
            Template(str(t.get("name", "")), i, str(t.get("qfmt", "")), str(t.get("afmt", "")))
            for i, t in enumerate(_sorted_by_ord(m.get("tmpls") or []))
        )
        out[ntid] = Notetype(
            id=ntid,
            name=str(m.get("name", "")),
            is_cloze=int(m.get("type") or 0) == 1,
            fields=fields,
            templates=templates,
            css=str(m.get("css") or ""),
            stock_kind=int(m.get("originalStockKind") or 0),
        )
    return out


def _notetypes_v18(conn: sqlite3.Connection) -> dict[int, Notetype]:
    fields: dict[int, list[str]] = {}
    for ntid, _ord, fname in conn.execute(
        "SELECT f.ntid, f.ord, f.name FROM fields f JOIN notetypes n ON n.id = f.ntid "
        "ORDER BY f.ntid, f.ord"
    ):
        fields.setdefault(int(ntid), []).append(str(fname))
    templates: dict[int, list[Template]] = {}
    for ntid, _ord, tname, config in conn.execute(
        "SELECT t.ntid, t.ord, t.name, t.config FROM templates t JOIN notetypes n "
        "ON n.id = t.ntid ORDER BY t.ntid, t.ord"
    ):
        tc = pb.decode(bytes(config or b""))
        found = templates.setdefault(int(ntid), [])
        found.append(Template(str(tname), len(found), pb.text(tc, 1), pb.text(tc, 2)))
    out: dict[int, Notetype] = {}
    for ntid, ntname, config in conn.execute("SELECT id, name, config FROM notetypes"):
        nc = pb.decode(bytes(config or b""))
        out[int(ntid)] = Notetype(
            id=int(ntid),
            name=str(ntname),
            is_cloze=pb.integer(nc, 1) == 1,
            fields=tuple(fields.get(int(ntid), [])),
            templates=tuple(templates.get(int(ntid), [])),
            css=pb.text(nc, 3),
            stock_kind=pb.integer(nc, 9),
        )
    return out


def _decks_v11(decks: Mapping[str, Any]) -> tuple[dict[int, str], dict[int, int | None]]:
    names: dict[int, str] = {}
    configs: dict[int, int | None] = {}
    for key, d in decks.items():
        if not isinstance(d, dict):
            continue
        did = int(d.get("id") or key)
        names[did] = _deck_name(str(d.get("name", "")))
        conf = d.get("conf")
        configs[did] = None if d.get("dyn") else int(conf) if conf is not None else None
    return names, configs


def _decks_v18(conn: sqlite3.Connection) -> tuple[dict[int, str], dict[int, int | None]]:
    names: dict[int, str] = {}
    configs: dict[int, int | None] = {}
    for did, dname, kind in conn.execute("SELECT id, name, kind FROM decks"):
        names[int(did)] = _deck_name(str(dname).replace("\x1f", "::"))
        container = pb.decode(bytes(kind or b""))
        normal = pb.message(container, 1)
        configs[int(did)] = pb.signed(normal, 1) if normal is not None else None
    return names, configs


def _deck_name(name: str) -> str:
    parts = [p.strip() for p in name.split("::")]
    return "::".join(p for p in parts if p) or "Default"


def _fsrs_params(*candidates: Iterable[float]) -> tuple[float, ...]:
    for params in candidates:
        values = tuple(float(v) for v in params)
        if values:
            return values
    return ()


def _deck_configs_v11(dconf: Mapping[str, Any]) -> dict[int, DeckConfig]:
    out: dict[int, DeckConfig] = {}
    for key, c in dconf.items():
        if not isinstance(c, dict):
            continue
        cid = int(c.get("id") or key)
        retention = c.get("desiredRetention")
        if not isinstance(retention, int | float) or retention <= 0:
            retention = None
        out[cid] = DeckConfig(
            id=cid,
            name=str(c.get("name", "")),
            fsrs_params=_fsrs_params(
                c.get("fsrsParams6") or (), c.get("fsrsParams5") or (), c.get("fsrsWeights") or ()
            ),
            desired_retention=None if retention is None else float(retention),
            ignore_before_ms=_date_ms(str(c.get("ignoreRevlogsBeforeDate") or "")),
        )
    return out


def _deck_configs_v18(conn: sqlite3.Connection) -> dict[int, DeckConfig]:
    out: dict[int, DeckConfig] = {}
    for cid, cname, config in conn.execute("SELECT id, name, config FROM deck_config"):
        fields = pb.decode(bytes(config or b""))
        retention = pb.float32(fields, 37)
        out[int(cid)] = DeckConfig(
            id=int(cid),
            name=str(cname),
            fsrs_params=_fsrs_params(
                pb.floats(fields, 6), pb.floats(fields, 5), pb.floats(fields, 3)
            ),
            desired_retention=retention if retention else None,
            ignore_before_ms=_date_ms(pb.text(fields, 46)),
        )
    return out


def _date_ms(text: str) -> int:
    """Anki's ignore_revlogs_before_date: YYYY-MM-DD at UTC midnight."""
    if not text:
        return 0
    try:
        return int(datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000)
    except ValueError:
        return 0


def _config_table(conn: sqlite3.Connection) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in conn.execute("SELECT KEY, val FROM config"):
        try:
            out[str(key)] = json.loads(val)
        except ValueError, TypeError, UnicodeDecodeError:
            continue
    return out


def _notes(conn: sqlite3.Connection) -> list[Note]:
    out: list[Note] = []
    for number, (nid, guid, mid, tags, flds) in enumerate(
        conn.execute("SELECT id, guid, mid, tags, flds FROM notes ORDER BY id"), start=1
    ):
        out.append(
            Note(
                id=int(nid),
                guid=str(guid),
                notetype_id=int(mid),
                fields=tuple(str(flds).split("\x1f")),
                tags=tuple(str(tags or "").split()),
                line=number,
            )
        )
    return out


def _cards(
    conn: sqlite3.Connection, decks: Mapping[int, str], configs: Mapping[int, int | None]
) -> list[Card]:
    out: list[Card] = []
    for row in conn.execute(
        "SELECT id, nid, did, odid, ord, type, queue, ivl, factor, reps, lapses, flags, data "
        "FROM cards ORDER BY nid, ord"
    ):
        cid, nid, did, odid, ord_, type_, queue, ivl, factor, reps, lapses, flags, data = row
        home = int(odid) if odid else int(did)
        try:
            parsed = json.loads(data) if data else {}
        except ValueError, TypeError:
            parsed = {}
        out.append(
            Card(
                id=int(cid),
                note_id=int(nid),
                ord=int(ord_),
                deck=decks.get(home, "Default"),
                config_id=configs.get(home),
                type=int(type_),
                queue=int(queue),
                ivl=int(ivl),
                factor=int(factor),
                reps=int(reps),
                lapses=int(lapses),
                flags=int(flags) & 0b111,
                data=parsed if isinstance(parsed, dict) else {},
            )
        )
    return out
