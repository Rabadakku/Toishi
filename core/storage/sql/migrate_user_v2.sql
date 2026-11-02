-- user.db schema v1 -> v2 (ADR-0011). Frozen: it runs once, inside the v2 migration's
-- transaction, after which core/storage/schema.py moves the v1 data into these homes.
-- New columns go last, so each table keeps the field order of its dataclass in
-- core/model.py, and user_card keeps the shape of a v2 pack's card table.

-- Template instances: the parameter set, out of notes_md (it was its first line).
ALTER TABLE user_card ADD COLUMN
  params TEXT CHECK (params IS NULL OR template_id IS NOT NULL);

-- The source text of the student's own templates, by template ID (the instances'
-- template_id), for export (EXP-1) and editing (EDT-1). Kept after its instances retire.
CREATE TABLE user_template (
  id         TEXT PRIMARY KEY NOT NULL,
  source_md  TEXT NOT NULL CHECK (source_md <> ''),
  updated_at INTEGER NOT NULL
) STRICT;

-- The student's own media: each image reference in an own card, as written in its text,
-- maps to a content-addressed file (<sha256 hex>[.ext]) in the profile's media/ folder.
-- Files are never deleted, so an older backup of user.db still finds its images.
CREATE TABLE user_media (
  card_id TEXT NOT NULL REFERENCES user_card(id),
  ref     TEXT NOT NULL CHECK (ref <> ''),
  file    TEXT NOT NULL CHECK (
            file GLOB '[0-9a-f][0-9a-f]*' AND file NOT GLOB '*[^0-9a-z.]*'
            AND file NOT GLOB '*..*' AND length(file) BETWEEN 64 AND 73),
  PRIMARY KEY (card_id, ref)
) STRICT;
CREATE INDEX user_media_file ON user_media(file);

-- Checks: the "Why is this here?" sentence, out of the asking attempt's extra JSON.
ALTER TABLE pending_check ADD COLUMN reason TEXT;
