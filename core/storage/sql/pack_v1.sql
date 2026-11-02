-- Pack file, schema version 1 (PRAGMA user_version = 1, application_id 'MEPK').
-- A pack is built once by content-tools, sealed, and then only ever opened read-only.
-- The content tables (content_v1.sql, prefix "") follow these two.

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
