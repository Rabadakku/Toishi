-- Pack file, schema version 3 (PRAGMA user_version = 3, application_id 'MEPK').
-- A pack is built once by content-tools, sealed, and then only ever opened read-only.
-- The content tables (content_v2.sql, prefix "") follow these. pack and media are unchanged
-- since v1. v3 adds what the student model reads from a pack (docs/card-format.md): the
-- standard times of the `time:` key and the pace standard of skills.md. Only packs have
-- these tables, so user.db's content tables keep exactly the shape of a pack's. The app
-- reads v1, v2 and v3 packs (ADR-0011); packs are never migrated.

CREATE TABLE pack (
  singleton    INTEGER PRIMARY KEY NOT NULL CHECK (singleton = 1),
  id           TEXT NOT NULL,
  title        TEXT NOT NULL,
  version      TEXT NOT NULL,
  format       INTEGER NOT NULL,
  built_at     INTEGER NOT NULL,
  content_hash TEXT NOT NULL DEFAULT ''
) STRICT;

CREATE TABLE media (
  name TEXT PRIMARY KEY NOT NULL,
  data BLOB NOT NULL
) STRICT;

-- `time:` standard times in minutes, of a card (part '') or of one of its parts. Only the
-- cards and parts that set `time:` have a row; the others take the default.
CREATE TABLE card_time (
  card_id TEXT NOT NULL REFERENCES card(id),
  part    TEXT NOT NULL DEFAULT '',
  minutes REAL NOT NULL CHECK (minutes > 0),
  PRIMARY KEY (card_id, part)
) STRICT;

-- The pace standard (skills.md): minutes per solution step for standard times and the
-- weekly class hours (one row), and each section's standard hours in course order.
CREATE TABLE pace (
  singleton        INTEGER PRIMARY KEY NOT NULL CHECK (singleton = 1),
  minutes_per_step REAL NOT NULL CHECK (minutes_per_step > 0),
  weekly_hours     REAL CHECK (weekly_hours IS NULL OR weekly_hours > 0)
) STRICT;

CREATE TABLE pace_section (
  ord        INTEGER PRIMARY KEY NOT NULL CHECK (ord >= 0),
  section_id TEXT NOT NULL UNIQUE REFERENCES section(id),
  hours      REAL NOT NULL CHECK (hours > 0)
) STRICT;
