-- Content tables, schema version 1 (frozen: a later change gets content_v2.sql).
-- Shared by pack files (prefix "") and by user.db for the student's own cards and
-- skills (prefix "user_"), so both have exactly the same shape. {p} is the prefix.
-- Fields follow docs/card-format.md. Times are UTC epoch milliseconds.
-- Skill references across content are not foreign keys: a card or edge may point at a
-- skill in another pack, so the pack builder validates them instead.

CREATE TABLE {p}course (
  id    TEXT PRIMARY KEY NOT NULL,
  title TEXT NOT NULL,
  ord   INTEGER NOT NULL DEFAULT 0
) STRICT;

CREATE TABLE {p}unit (
  id        TEXT PRIMARY KEY NOT NULL,
  course_id TEXT NOT NULL,
  title     TEXT NOT NULL,
  ord       INTEGER NOT NULL DEFAULT 0
) STRICT;

CREATE TABLE {p}section (
  id           TEXT PRIMARY KEY NOT NULL,
  unit_id      TEXT NOT NULL,
  title        TEXT NOT NULL,
  ord          INTEGER NOT NULL DEFAULT 0,
  textbook_ref TEXT
) STRICT;

CREATE TABLE {p}skill (
  id            TEXT PRIMARY KEY NOT NULL,
  name          TEXT NOT NULL,
  deck          TEXT,
  section_id    TEXT,
  textbook_ref  TEXT,
  method_choice INTEGER NOT NULL DEFAULT 0 CHECK (method_choice IN (0, 1)),
  core          INTEGER NOT NULL DEFAULT 0 CHECK (core IN (0, 1)),
  exam_tier     INTEGER CHECK (exam_tier IS NULL OR exam_tier BETWEEN 1 AND 5),
  notes_md      TEXT
) STRICT;
CREATE INDEX {p}skill_section ON {p}skill(section_id);

CREATE TABLE {p}skill_edge (
  skill_id TEXT NOT NULL REFERENCES {p}skill(id),
  kind     TEXT NOT NULL CHECK (kind IN ('requires', 'encompasses', 'confusable')),
  other_id TEXT NOT NULL,
  ord      INTEGER NOT NULL DEFAULT 0,
  weight   REAL CHECK ((kind = 'encompasses') = (weight IS NOT NULL)),
  PRIMARY KEY (skill_id, kind, other_id),
  CHECK (skill_id <> other_id)
) STRICT;
CREATE INDEX {p}skill_edge_other ON {p}skill_edge(other_id, kind);

CREATE TABLE {p}card (
  id                      TEXT PRIMARY KEY NOT NULL,
  rev                     INTEGER NOT NULL DEFAULT 1 CHECK (rev >= 1),
  kind                    TEXT NOT NULL DEFAULT 'problem' CHECK (kind IN
                            ('problem', 'example', 'flashcard', 'cloze', 'find-error', 'method')),
  skill_id                TEXT,
  tier                    INTEGER NOT NULL DEFAULT 2 CHECK (tier BETWEEN 1 AND 5),
  answer_type             TEXT NOT NULL DEFAULT 'self',
  answer                  TEXT,
  checker                 TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(checker)),
  plot                    TEXT,
  calculator              INTEGER NOT NULL DEFAULT 0 CHECK (calculator IN (0, 1)),
  angles                  TEXT NOT NULL DEFAULT 'radians' CHECK (angles IN ('radians', 'degrees')),
  cue_required            INTEGER NOT NULL DEFAULT 0 CHECK (cue_required IN (0, 1)),
  error_step              INTEGER CHECK (error_step IS NULL OR error_step >= 0),
  tagged                  TEXT,
  deck                    TEXT,
  section_id              TEXT,
  tags                    TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(tags)),
  question_md             TEXT,
  cued_question_md        TEXT,
  hints                   TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(hints)),
  answer_md               TEXT,
  solution_md             TEXT,
  rubric                  TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(rubric)),
  alternative_solution_md TEXT,
  front_md                TEXT,
  back_md                 TEXT,
  text_md                 TEXT,
  extra_md                TEXT,
  notes_md                TEXT,
  template_id             TEXT,
  seed                    INTEGER,
  source                  TEXT,
  source_url              TEXT,
  license                 TEXT,
  creators                TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(creators)),
  original_path           TEXT,
  original_commit         TEXT,
  modified                INTEGER NOT NULL DEFAULT 0 CHECK (modified IN (0, 1)),
  modification_note       TEXT,
  third_party             TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(third_party)),
  translation             TEXT,
  unofficial_solution     INTEGER NOT NULL DEFAULT 0 CHECK (unofficial_solution IN (0, 1)),
  verified                TEXT,
  status                  TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired'))
) STRICT;
CREATE INDEX {p}card_skill ON {p}card(skill_id, tier);
CREATE INDEX {p}card_template ON {p}card(template_id);
CREATE INDEX {p}card_section ON {p}card(section_id);

-- `uses:` tags (count at 0.4 in the weak-spot finder)
CREATE TABLE {p}card_use (
  card_id  TEXT NOT NULL REFERENCES {p}card(id),
  ord      INTEGER NOT NULL,
  skill_id TEXT NOT NULL,
  PRIMARY KEY (card_id, skill_id)
) STRICT;
CREATE INDEX {p}card_use_skill ON {p}card_use(skill_id);

-- Step-tagged solution, alternative solution and find-error shown work
CREATE TABLE {p}card_step (
  card_id  TEXT NOT NULL REFERENCES {p}card(id),
  section  TEXT NOT NULL CHECK (section IN ('solution', 'alternative', 'shown-work')),
  number   INTEGER NOT NULL CHECK (number >= 0),
  skill_id TEXT,
  label    TEXT NOT NULL,
  body_md  TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (card_id, section, number)
) STRICT;
CREATE INDEX {p}card_step_skill ON {p}card_step(skill_id);

-- ### Choices and ### Reasons (part '' is the card itself, else a part label)
CREATE TABLE {p}card_choice (
  card_id TEXT NOT NULL REFERENCES {p}card(id),
  part    TEXT NOT NULL DEFAULT '',
  role    TEXT NOT NULL CHECK (role IN ('choice', 'reason')),
  ord     INTEGER NOT NULL,
  text_md TEXT NOT NULL,
  correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
  PRIMARY KEY (card_id, part, role, ord)
) STRICT;

-- `wrong:` known wrong answers with feedback and the step behind them
CREATE TABLE {p}card_wrong (
  card_id  TEXT NOT NULL REFERENCES {p}card(id),
  part     TEXT NOT NULL DEFAULT '',
  ord      INTEGER NOT NULL,
  answer   TEXT NOT NULL,
  feedback TEXT,
  step     INTEGER CHECK (step IS NULL OR step >= 0),
  PRIMARY KEY (card_id, part, ord)
) STRICT;

CREATE TABLE {p}card_part (
  card_id     TEXT NOT NULL REFERENCES {p}card(id),
  ord         INTEGER NOT NULL,
  label       TEXT NOT NULL,
  prompt_md   TEXT NOT NULL,
  answer_type TEXT NOT NULL DEFAULT 'self',
  answer      TEXT,
  checker     TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(checker)),
  skill_id    TEXT,
  PRIMARY KEY (card_id, ord),
  UNIQUE (card_id, label)
) STRICT;

-- PACK-2 revision history (a changed answer key is noted)
CREATE TABLE {p}card_revision (
  card_id        TEXT NOT NULL REFERENCES {p}card(id),
  rev            INTEGER NOT NULL CHECK (rev >= 1),
  changed_at     INTEGER NOT NULL,
  note           TEXT NOT NULL DEFAULT '',
  answer_changed INTEGER NOT NULL DEFAULT 0 CHECK (answer_changed IN (0, 1)),
  PRIMARY KEY (card_id, rev)
) STRICT;
