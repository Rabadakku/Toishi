-- user.db, schema version 1 (PRAGMA user_version = 1, application_id 'MEUS').
-- Frozen: a change is a new migration in core/storage/schema.py, never an edit here.
-- One user.db per profile, WAL mode. Times are UTC epoch milliseconds (`at`, `*_at`),
-- durations milliseconds (`*_ms`), study days ISO dates. JSON columns are checked.
-- Column order matches the dataclasses in core/model.py (a test checks).
-- The student's own cards and skills follow as content_v1.sql with prefix "user_".

CREATE TABLE setting (
  key        TEXT PRIMARY KEY NOT NULL,
  value      TEXT NOT NULL CHECK (json_valid(value)),
  updated_at INTEGER NOT NULL
) STRICT;

-- ---------------------------------------------------------------- goals and exams

CREATE TABLE course_goal (
  course_id        TEXT PRIMARY KEY NOT NULL,
  goal             TEXT NOT NULL DEFAULT 'A' CHECK (goal IN ('A', 'B', 'Keep', 'custom')),
  custom_retention REAL CHECK (custom_retention IS NULL OR custom_retention BETWEEN 0.80 AND 0.95),
  goal_date        TEXT CHECK (goal_date IS NULL OR date(goal_date) IS goal_date),
  starts_on        TEXT CHECK (starts_on IS NULL OR date(starts_on) IS starts_on),
  updated_at       INTEGER NOT NULL,
  CHECK ((goal = 'custom') = (custom_retention IS NOT NULL))
) STRICT;

CREATE TABLE exam (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id     TEXT,
  name          TEXT NOT NULL,
  at            INTEGER NOT NULL,
  minutes       INTEGER CHECK (minutes IS NULL OR minutes >= 0),
  problems      INTEGER CHECK (problems IS NULL OR problems >= 0),
  sections      TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(sections)),
  target_recall REAL CHECK (target_recall IS NULL OR target_recall BETWEEN 0 AND 1),
  created_at    INTEGER NOT NULL
) STRICT;

CREATE TABLE section_state (
  section_id TEXT PRIMARY KEY NOT NULL,
  state      TEXT NOT NULL CHECK (state IN ('off', 'learning', 'covered', 'solid')),
  changed_at INTEGER NOT NULL
) STRICT;

-- ---------------------------------------------------------------- memory state
-- Rows an attempt may change are snapshotted into attempt.state_before/state_after.

CREATE TABLE skill_state (
  skill_id        TEXT PRIMARY KEY NOT NULL,
  fsrs_state      INTEGER CHECK (fsrs_state IS NULL OR fsrs_state IN (1, 2, 3)),
  fsrs_step       INTEGER,
  stability       REAL CHECK (stability IS NULL OR stability > 0),
  difficulty      REAL,
  due_at          INTEGER,
  last_review_at  INTEGER,
  reps            INTEGER NOT NULL DEFAULT 0 CHECK (reps >= 0),
  lapses          INTEGER NOT NULL DEFAULT 0 CHECK (lapses >= 0),
  leech           INTEGER NOT NULL DEFAULT 0 CHECK (leech IN (0, 1)),
  leech_at        INTEGER,
  introduced_at   INTEGER,
  learning_streak INTEGER NOT NULL DEFAULT 0 CHECK (learning_streak >= 0),
  learning_count  INTEGER NOT NULL DEFAULT 0 CHECK (learning_count >= 0),
  level           TEXT CHECK (level IS NULL OR level IN ('learning', 'learned', 'exam', 'mastered')),
  level_at        INTEGER,
  level_evidence  TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(level_evidence)),
  shaky           INTEGER NOT NULL DEFAULT 0 CHECK (shaky IN (0, 1)),
  shaky_reviews   INTEGER NOT NULL DEFAULT 0 CHECK (shaky_reviews >= 0),
  learned_at      INTEGER,
  mastered_at     INTEGER,
  elo_theta       REAL NOT NULL DEFAULT 0,
  elo_n           INTEGER NOT NULL DEFAULT 0 CHECK (elo_n >= 0),
  updated_at      INTEGER NOT NULL
) STRICT;
CREATE INDEX skill_state_due ON skill_state(due_at);

CREATE TABLE skill_tier (
  skill_id           TEXT NOT NULL,
  tier               INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 5),
  target_ms          INTEGER CHECK (target_ms IS NULL OR target_ms >= 0),
  target_at          INTEGER,
  baseline_median_ms INTEGER,
  baseline_n         INTEGER NOT NULL DEFAULT 0,
  first_correct_ms   TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(first_correct_ms)),
  updated_at         INTEGER NOT NULL,
  PRIMARY KEY (skill_id, tier)
) STRICT;

CREATE TABLE skill_shadow (
  skill_id           TEXT PRIMARY KEY NOT NULL,
  credited_stability REAL,
  updated_at         INTEGER NOT NULL
) STRICT;

CREATE TABLE flashcard_state (
  card_id        TEXT NOT NULL,
  ord            INTEGER NOT NULL DEFAULT 0,
  fsrs_state     INTEGER CHECK (fsrs_state IS NULL OR fsrs_state IN (1, 2, 3)),
  fsrs_step      INTEGER,
  stability      REAL CHECK (stability IS NULL OR stability > 0),
  difficulty     REAL,
  due_at         INTEGER,
  last_review_at INTEGER,
  reps           INTEGER NOT NULL DEFAULT 0 CHECK (reps >= 0),
  lapses         INTEGER NOT NULL DEFAULT 0 CHECK (lapses >= 0),
  leech          INTEGER NOT NULL DEFAULT 0 CHECK (leech IN (0, 1)),
  updated_at     INTEGER NOT NULL,
  PRIMARY KEY (card_id, ord)
) STRICT;
CREATE INDEX flashcard_state_due ON flashcard_state(due_at);

CREATE TABLE card_user (
  card_id         TEXT PRIMARY KEY NOT NULL,
  last_seen_at    INTEGER,
  times_seen      INTEGER NOT NULL DEFAULT 0 CHECK (times_seen >= 0),
  last_correct_at INTEGER,
  redo_due_at     INTEGER,
  redo_guaranteed INTEGER NOT NULL DEFAULT 0 CHECK (redo_guaranteed IN (0, 1)),
  updated_at      INTEGER NOT NULL
) STRICT;

CREATE TABLE card_mark (
  card_id    TEXT PRIMARY KEY NOT NULL,
  flagged    INTEGER NOT NULL DEFAULT 0 CHECK (flagged IN (0, 1)),
  flag_note  TEXT,
  suspended  INTEGER NOT NULL DEFAULT 0 CHECK (suspended IN (0, 1)),
  hidden     INTEGER NOT NULL DEFAULT 0 CHECK (hidden IN (0, 1)),
  updated_at INTEGER NOT NULL
) STRICT;

-- ---------------------------------------------------------------- checks and weak spots

CREATE TABLE pending_check (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at    INTEGER NOT NULL,
  attempt_id    INTEGER REFERENCES attempt(id) DEFERRABLE INITIALLY DEFERRED,
  skill_id      TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('step', 'prerequisite', 'cued-twin', 'diagnostic')),
  card_id       TEXT,
  after_items   INTEGER NOT NULL DEFAULT 3 CHECK (after_items >= 0),
  not_before_at INTEGER,
  depth         INTEGER NOT NULL DEFAULT 0 CHECK (depth >= 0),
  status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'passed', 'failed', 'cancelled')),
  resolved_at   INTEGER,
  resolved_by   INTEGER REFERENCES attempt(id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE INDEX pending_check_open ON pending_check(status, skill_id);

CREATE TABLE weak_spot (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  skill_id    TEXT NOT NULL,
  flagged_at  INTEGER NOT NULL,
  study_day   TEXT NOT NULL CHECK (date(study_day) IS study_day),
  z           REAL NOT NULL,
  evidence    REAL NOT NULL,
  misses      INTEGER NOT NULL,
  problems    INTEGER NOT NULL,
  days        INTEGER NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'confirmed', 'cleared')),
  resolved_at INTEGER
) STRICT;

CREATE TABLE diagnostic_set (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  skill_id     TEXT NOT NULL,
  weak_spot_id INTEGER REFERENCES weak_spot(id) DEFERRABLE INITIALLY DEFERRED,
  created_at   INTEGER NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'active', 'confirmed', 'cleared', 'cancelled')),
  card_ids     TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(card_ids)),
  done         INTEGER NOT NULL DEFAULT 0 CHECK (done >= 0),
  misses       INTEGER NOT NULL DEFAULT 0 CHECK (misses >= 0),
  resolved_at  INTEGER
) STRICT;

-- ---------------------------------------------------------------- sessions (QUE-16)

CREATE TABLE session (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  study_day  TEXT NOT NULL CHECK (date(study_day) IS study_day),
  started_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  ended_at   INTEGER,
  untimed    INTEGER NOT NULL DEFAULT 0 CHECK (untimed IN (0, 1)),
  plan       TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(plan)),
  position   INTEGER NOT NULL DEFAULT 0 CHECK (position >= 0),
  current    TEXT CHECK (current IS NULL OR json_valid(current)),
  active_ms  INTEGER NOT NULL DEFAULT 0 CHECK (active_ms >= 0),
  draft      TEXT,
  extra      TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(extra))
) STRICT;
CREATE INDEX session_open ON session(ended_at, updated_at);

-- ---------------------------------------------------------------- append-only logs (DATA-5)

CREATE TABLE attempt_void (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  at           INTEGER NOT NULL,
  reason       TEXT NOT NULL CHECK (reason IN ('undo', 'dispute', 'report', 'recompute')),
  note         TEXT,
  state_before TEXT CHECK (state_before IS NULL OR json_valid(state_before)),
  state_after  TEXT CHECK (state_after IS NULL OR json_valid(state_after))
) STRICT;

CREATE TABLE attempt (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  at               INTEGER NOT NULL,
  study_day        TEXT NOT NULL CHECK (date(study_day) IS study_day),
  shown_at         INTEGER,
  session_id       INTEGER REFERENCES session(id),
  presentation_id  TEXT,
  card_id          TEXT NOT NULL,
  card_rev         INTEGER NOT NULL CHECK (card_rev >= 1),
  pack_id          TEXT,
  card_kind        TEXT NOT NULL CHECK (card_kind IN
                     ('problem', 'example', 'flashcard', 'cloze', 'find-error', 'method')),
  skill_id         TEXT,
  part             TEXT,
  tier             INTEGER CHECK (tier IS NULL OR tier BETWEEN 1 AND 5),
  seed             INTEGER,
  template_id      TEXT,
  reason_tag       TEXT,
  raw_input        TEXT,
  parsed           TEXT,
  verdict          TEXT NOT NULL CHECK (verdict IN
                     ('correct', 'incorrect', 'gave-up', 'self', 'undecided', 'shown')),
  attempt_number   INTEGER NOT NULL CHECK (attempt_number >= 1),
  final            INTEGER NOT NULL CHECK (final IN (0, 1)),
  hints_used       INTEGER NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
  example_opened   INTEGER NOT NULL DEFAULT 0 CHECK (example_opened IN (0, 1)),
  confidence       TEXT NOT NULL DEFAULT 'sure' CHECK (confidence IN ('sure', 'unsure')),
  guessed          INTEGER NOT NULL DEFAULT 0 CHECK (guessed IN (0, 1)),
  too_easy         INTEGER NOT NULL DEFAULT 0 CHECK (too_easy IN (0, 1)),
  active_ms        INTEGER CHECK (active_ms IS NULL OR active_ms >= 0),
  solve_ms         INTEGER CHECK (solve_ms IS NULL OR solve_ms >= 0),
  entry_ms         INTEGER CHECK (entry_ms IS NULL OR entry_ms >= 0),
  raw_ms           INTEGER CHECK (raw_ms IS NULL OR raw_ms >= 0),
  capped_ms        INTEGER CHECK (capped_ms IS NULL OR capped_ms >= 0),
  pause_count      INTEGER NOT NULL DEFAULT 0 CHECK (pause_count >= 0),
  longest_pause_ms INTEGER,
  after_wake       INTEGER NOT NULL DEFAULT 0 CHECK (after_wake IN (0, 1)),
  untimed          INTEGER NOT NULL DEFAULT 0 CHECK (untimed IN (0, 1)),
  rating           INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 4),
  explicit_rating  INTEGER NOT NULL DEFAULT 0 CHECK (explicit_rating IN (0, 1)),
  predicted_recall REAL CHECK (predicted_recall IS NULL OR predicted_recall BETWEEN 0 AND 1),
  params_id        TEXT,
  rules_version    TEXT,
  triage_policy    TEXT,
  error_choice     TEXT CHECK (error_choice IS NULL OR error_choice IN
                     ('step', 'setup', 'slip', 'misread', 'other-method', 'cant-tell')),
  error_step       INTEGER,
  matched_wrong    INTEGER,
  check_of         INTEGER REFERENCES attempt(id),
  app_version      TEXT,
  extra            TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(extra)),
  state_before     TEXT NOT NULL CHECK (json_valid(state_before)),
  state_after      TEXT NOT NULL CHECK (json_valid(state_after)),
  voided_by        INTEGER REFERENCES attempt_void(id)
) STRICT;
CREATE INDEX attempt_skill ON attempt(skill_id, at);
CREATE INDEX attempt_card ON attempt(card_id, at);
CREATE INDEX attempt_day ON attempt(study_day);
CREATE INDEX attempt_session ON attempt(session_id);
CREATE INDEX attempt_presentation ON attempt(presentation_id);

CREATE TABLE review_log (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  at               INTEGER NOT NULL,
  attempt_id       INTEGER NOT NULL REFERENCES attempt(id),
  target_kind      TEXT NOT NULL CHECK (target_kind IN ('skill', 'flashcard')),
  target_id        TEXT NOT NULL,
  target_ord       INTEGER NOT NULL DEFAULT 0,
  rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 4),
  rules_version    TEXT NOT NULL,
  params_id        TEXT,
  retention        REAL CHECK (retention IS NULL OR retention BETWEEN 0 AND 1),
  predicted_recall REAL CHECK (predicted_recall IS NULL OR predicted_recall BETWEEN 0 AND 1),
  state_before     TEXT CHECK (state_before IS NULL OR json_valid(state_before)),
  state_after      TEXT CHECK (state_after IS NULL OR json_valid(state_after)),
  voided_by        INTEGER REFERENCES attempt_void(id)
) STRICT;
CREATE INDEX review_log_target ON review_log(target_kind, target_id, at);
CREATE INDEX review_log_attempt ON review_log(attempt_id);

CREATE TABLE implicit_credit (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  at               INTEGER NOT NULL,
  attempt_id       INTEGER NOT NULL REFERENCES attempt(id),
  from_skill       TEXT NOT NULL,
  to_skill         TEXT NOT NULL,
  weight           REAL NOT NULL CHECK (weight > 0 AND weight <= 1),
  mode             TEXT NOT NULL CHECK (mode IN ('shadow', 'on')),
  stability_before REAL,
  stability_after  REAL,
  voided_by        INTEGER REFERENCES attempt_void(id)
) STRICT;
CREATE INDEX implicit_credit_attempt ON implicit_credit(attempt_id);

CREATE TABLE import_record (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      INTEGER NOT NULL,
  file    TEXT NOT NULL,
  kind    TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(summary)),
  backup  TEXT
) STRICT;

-- The logs are append-only. The only permitted update sets voided_by once.
CREATE TRIGGER attempt_no_delete BEFORE DELETE ON attempt
BEGIN SELECT RAISE(ABORT, 'attempt is append-only'); END;
CREATE TRIGGER attempt_no_update BEFORE UPDATE OF
  id, at, study_day, shown_at, session_id, presentation_id, card_id, card_rev, pack_id,
  card_kind, skill_id, part, tier, seed, template_id, reason_tag, raw_input, parsed, verdict,
  attempt_number, final, hints_used, example_opened, confidence, guessed, too_easy, active_ms,
  solve_ms, entry_ms, raw_ms, capped_ms, pause_count, longest_pause_ms, after_wake, untimed,
  rating, explicit_rating, predicted_recall, params_id, rules_version, triage_policy,
  error_choice, error_step, matched_wrong, check_of, app_version, extra, state_before,
  state_after ON attempt
BEGIN SELECT RAISE(ABORT, 'attempt is append-only'); END;
CREATE TRIGGER attempt_void_once BEFORE UPDATE OF voided_by ON attempt
WHEN OLD.voided_by IS NOT NULL OR NEW.voided_by IS NULL
BEGIN SELECT RAISE(ABORT, 'an attempt is voided once and stays voided'); END;

CREATE TRIGGER review_log_no_delete BEFORE DELETE ON review_log
BEGIN SELECT RAISE(ABORT, 'review_log is append-only'); END;
CREATE TRIGGER review_log_no_update BEFORE UPDATE OF
  id, at, attempt_id, target_kind, target_id, target_ord, rating, rules_version, params_id,
  retention, predicted_recall, state_before, state_after ON review_log
BEGIN SELECT RAISE(ABORT, 'review_log is append-only'); END;
CREATE TRIGGER review_log_void_once BEFORE UPDATE OF voided_by ON review_log
WHEN OLD.voided_by IS NOT NULL OR NEW.voided_by IS NULL
BEGIN SELECT RAISE(ABORT, 'a review is voided once and stays voided'); END;

CREATE TRIGGER implicit_credit_no_delete BEFORE DELETE ON implicit_credit
BEGIN SELECT RAISE(ABORT, 'implicit_credit is append-only'); END;
CREATE TRIGGER implicit_credit_no_update BEFORE UPDATE OF
  id, at, attempt_id, from_skill, to_skill, weight, mode, stability_before, stability_after
  ON implicit_credit
BEGIN SELECT RAISE(ABORT, 'implicit_credit is append-only'); END;
CREATE TRIGGER implicit_credit_void_once BEFORE UPDATE OF voided_by ON implicit_credit
WHEN OLD.voided_by IS NOT NULL OR NEW.voided_by IS NULL
BEGIN SELECT RAISE(ABORT, 'a credit is voided once and stays voided'); END;

CREATE TRIGGER attempt_void_no_delete BEFORE DELETE ON attempt_void
BEGIN SELECT RAISE(ABORT, 'attempt_void is append-only'); END;
CREATE TRIGGER attempt_void_no_update BEFORE UPDATE ON attempt_void
BEGIN SELECT RAISE(ABORT, 'attempt_void is append-only'); END;

CREATE TRIGGER import_record_no_delete BEFORE DELETE ON import_record
BEGIN SELECT RAISE(ABORT, 'import_record is append-only'); END;
CREATE TRIGGER import_record_no_update BEFORE UPDATE ON import_record
BEGIN SELECT RAISE(ABORT, 'import_record is append-only'); END;

-- ---------------------------------------------------------------- disputes and reports

CREATE TABLE dispute (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id  INTEGER NOT NULL REFERENCES attempt(id),
  at          INTEGER NOT NULL,
  raw_input   TEXT,
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'upheld', 'rejected')),
  resolved_at INTEGER,
  note        TEXT
) STRICT;

CREATE TABLE report (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id     TEXT NOT NULL,
  card_rev    INTEGER NOT NULL DEFAULT 1,
  attempt_id  INTEGER REFERENCES attempt(id),
  at          INTEGER NOT NULL,
  reason      TEXT NOT NULL DEFAULT '',
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'fixed', 'dismissed')),
  resolved_at INTEGER
) STRICT;
