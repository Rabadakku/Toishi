-- user.db schema v2 -> v3 (wave 2: the student model and planner in the app,
-- docs/design/wave2-integration.md section 2). Frozen: it runs once, inside the v3
-- migration's transaction, after which core/storage/schema.py seeds course_settings from
-- course_goal. New columns go last, so attempt keeps the field order of its dataclass in
-- core/model.py.

-- What the planner chose and the learner used, logged with each problem attempt (design
-- 3.4: log P_j, the role and the flags before updating). NULL for flashcards and for rows
-- from before v3.
ALTER TABLE attempt ADD COLUMN role TEXT CHECK (role IS NULL OR role IN
  ('new', 'growth', 'maintenance', 'check', 'practice-test', 'focused', 'sitting',
   'placement'));
ALTER TABLE attempt ADD COLUMN milestone TEXT
  CHECK (milestone IS NULL OR milestone IN ('M1', 'M2', 'M3', 'keep'));
ALTER TABLE attempt ADD COLUMN missed INTEGER CHECK (missed IS NULL OR missed IN (0, 1));
ALTER TABLE attempt ADD COLUMN plan_p REAL CHECK (plan_p IS NULL OR plan_p BETWEEN 0 AND 1);
ALTER TABLE attempt ADD COLUMN ladder INTEGER CHECK (ladder IS NULL OR ladder BETWEEN 0 AND 2);
ALTER TABLE attempt ADD COLUMN sitting TEXT;
ALTER TABLE attempt ADD COLUMN learner_version TEXT;
ALTER TABLE attempt ADD COLUMN valid_minutes REAL
  CHECK (valid_minutes IS NULL OR valid_minutes > 0);

-- The log stays append-only (DATA-5): the trigger now lists the new columns too.
DROP TRIGGER attempt_no_update;
CREATE TRIGGER attempt_no_update BEFORE UPDATE OF
  id, at, study_day, shown_at, session_id, presentation_id, card_id, card_rev, pack_id,
  card_kind, skill_id, part, tier, seed, template_id, reason_tag, raw_input, parsed, verdict,
  attempt_number, final, hints_used, example_opened, confidence, guessed, too_easy, active_ms,
  solve_ms, entry_ms, raw_ms, capped_ms, pause_count, longest_pause_ms, after_wake, untimed,
  rating, explicit_rating, predicted_recall, params_id, rules_version, triage_policy,
  error_choice, error_step, matched_wrong, check_of, app_version, extra, state_before,
  state_after, role, milestone, missed, plan_p, ladder, sitting, learner_version,
  valid_minutes ON attempt
BEGIN SELECT RAISE(ABORT, 'attempt is append-only'); END;

-- One row per course the student has set up (design 4.1): the pace anchor (a start date,
-- or "my class is at section X today"), the targets and the end date. Courses live in
-- read-only pack files or in user_course, and SQLite cannot reference a table in an
-- attached database, so the app checks course_id against the loaded courses on write.
CREATE TABLE course_settings (
  course_id       TEXT PRIMARY KEY NOT NULL CHECK (course_id <> ''),
  start           TEXT CHECK (start IS NULL OR date(start) IS start),
  aligned_deck    TEXT CHECK (aligned_deck IS NULL OR aligned_deck <> ''),
  aligned_day     TEXT CHECK (aligned_day IS NULL OR date(aligned_day) IS aligned_day),
  pace_factor     REAL NOT NULL DEFAULT 1 CHECK (pace_factor BETWEEN 0.75 AND 1.5),
  accuracy_target REAL NOT NULL DEFAULT 0.9
                    CHECK (accuracy_target > 0 AND accuracy_target < 1),
  target_tier     INTEGER NOT NULL DEFAULT 4 CHECK (target_tier BETWEEN 1 AND 5),
  end_day         TEXT CHECK (end_day IS NULL OR date(end_day) IS end_day),
  keep_target     REAL NOT NULL DEFAULT 0.8 CHECK (keep_target > 0 AND keep_target < 1),
  keep_tier       INTEGER NOT NULL DEFAULT 3 CHECK (keep_tier BETWEEN 1 AND 5),
  growth_band     TEXT NOT NULL DEFAULT 'standard' CHECK (growth_band IN ('standard', 'hard')),
  updated_at      INTEGER NOT NULL,
  CHECK ((aligned_deck IS NULL) = (aligned_day IS NULL))
) STRICT;

-- The learner's shared parameter versions (design 3.6): the prior, each refit (adopted or
-- not, with its report) and each reset. Exactly one row is current.
CREATE TABLE learner_params (
  version    TEXT PRIMARY KEY NOT NULL CHECK (version <> ''),
  created_at INTEGER NOT NULL,
  params     TEXT NOT NULL CHECK (json_valid(params)),
  source     TEXT NOT NULL CHECK (source IN ('prior', 'refit', 'reset')),
  report     TEXT CHECK (report IS NULL OR json_valid(report)),
  current    INTEGER NOT NULL DEFAULT 0 CHECK (current IN (0, 1))
) STRICT;
CREATE UNIQUE INDEX learner_params_current ON learner_params(current) WHERE current = 1;

-- A version's values never change once written; only which version is current does.
CREATE TRIGGER learner_params_no_delete BEFORE DELETE ON learner_params
BEGIN SELECT RAISE(ABORT, 'learner_params is append-only'); END;
CREATE TRIGGER learner_params_no_update BEFORE UPDATE OF
  version, created_at, params, source, report ON learner_params
BEGIN SELECT RAISE(ABORT, 'learner_params is append-only'); END;
