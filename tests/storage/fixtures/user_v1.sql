-- Frozen user.db at schema v1 with data (tests/storage/data.py). Never edit.
BEGIN TRANSACTION;
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
INSERT INTO "attempt" VALUES(1,1793545200000,'2026-11-01',1793545159000,1,'p0','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,'t01','due','0, 1','{0, 1}','incorrect',1,0,0,0,'sure',0,0,40000,35000,5000,41000,40000,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'0.1.0','{}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":null,"table":"card_user"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793545200000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":1,"updated_at":1793545200000},"table":"card_user"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(2,1793545230000,'2026-11-01',NULL,1,'p0','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,NULL,NULL,'-1, 0, 1',NULL,'correct',2,1,1,0,'unsure',0,0,70000,60000,10000,75000,70000,1,4000,0,0,2,0,0.91,'default-6','r1','recommended','slip',2,NULL,NULL,'0.1.0','{"part_results":{"a":"correct"}}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":null,"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":null,"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":null,"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793545200000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":1,"updated_at":1793545200000},"table":"card_user"},{"key":{"id":1},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":{"difficulty":5.5,"due_at":1793761230000,"elo_n":1,"elo_theta":0.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":null,"lapses":0,"last_review_at":1793545230000,"learned_at":null,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":1793545230000,"level_evidence":"{\"days\":1}","mastered_at":null,"reps":1,"shaky":0,"shaky_reviews":0,"skill_id":"calc1.extrema.critical-numbers","stability":2.5,"updated_at":1793545230000},"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":{"baseline_median_ms":65000,"baseline_n":1,"first_correct_ms":"[70000]","skill_id":"calc1.extrema.critical-numbers","target_at":null,"target_ms":90000,"tier":3,"updated_at":1793545230000},"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":{"credited_stability":1.25,"skill_id":"calc1.deriv.power-rule","updated_at":1793545230000},"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":1793545230000,"last_seen_at":1793545230000,"redo_due_at":1793890830000,"redo_guaranteed":0,"times_seen":2,"updated_at":1793545230000},"table":"card_user"},{"key":{"id":1},"row":{"after_items":3,"attempt_id":2,"card_id":null,"created_at":1793545230000,"depth":1,"id":1,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(3,1793545290000,'2026-11-01',NULL,1,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'self',1,1,0,0,'sure',0,0,8000,NULL,NULL,NULL,NULL,0,NULL,0,0,3,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":null,"table":"flashcard_state"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":{"card_id":"calc1.mvt.001","difficulty":4.0,"due_at":1793804490000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545290000,"leech":0,"ord":0,"reps":1,"stability":3.0,"updated_at":1793545290000},"table":"flashcard_state"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(4,1793545350000,'2026-11-01',NULL,1,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,'check',NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,2,NULL,'{}','{"rows":[{"key":{"id":1},"row":{"after_items":3,"attempt_id":2,"card_id":null,"created_at":1793545230000,"depth":1,"id":1,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}','{"rows":[{"key":{"id":1},"row":{"after_items":3,"attempt_id":2,"card_id":null,"created_at":1793545230000,"depth":1,"id":1,"kind":"step","not_before_at":null,"resolved_at":1793545350000,"resolved_by":4,"skill_id":"alg.factor.polynomials","status":"passed"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(5,1793631750000,'2026-11-02',1793631709000,2,'p1','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,'t01','due','0, 1','{0, 1}','incorrect',1,0,0,0,'sure',0,0,40000,35000,5000,41000,40000,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'0.1.0','{}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":1793545230000,"last_seen_at":1793545230000,"redo_due_at":1793890830000,"redo_guaranteed":0,"times_seen":2,"updated_at":1793545230000},"table":"card_user"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793631750000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":3,"updated_at":1793631750000},"table":"card_user"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(6,1793631780000,'2026-11-02',NULL,2,'p1','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,NULL,NULL,'-1, 0, 1',NULL,'correct',2,1,1,0,'unsure',0,0,70000,60000,10000,75000,70000,1,4000,0,1,2,0,0.91,'default-6','r1','recommended','slip',2,NULL,NULL,'0.1.0','{"part_results":{"a":"correct"}}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":{"difficulty":5.5,"due_at":1793761230000,"elo_n":1,"elo_theta":0.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":null,"lapses":0,"last_review_at":1793545230000,"learned_at":null,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":1793545230000,"level_evidence":"{\"days\":1}","mastered_at":null,"reps":1,"shaky":0,"shaky_reviews":0,"skill_id":"calc1.extrema.critical-numbers","stability":2.5,"updated_at":1793545230000},"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":{"baseline_median_ms":65000,"baseline_n":1,"first_correct_ms":"[70000]","skill_id":"calc1.extrema.critical-numbers","target_at":null,"target_ms":90000,"tier":3,"updated_at":1793545230000},"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":{"credited_stability":1.25,"skill_id":"calc1.deriv.power-rule","updated_at":1793545230000},"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793631750000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":3,"updated_at":1793631750000},"table":"card_user"},{"key":{"id":2},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":{"difficulty":5.5,"due_at":1794171780000,"elo_n":2,"elo_theta":0.1,"fsrs_state":2,"fsrs_step":null,"introduced_at":null,"lapses":0,"last_review_at":1793631780000,"learned_at":null,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":1793631780000,"level_evidence":"{\"days\":2}","mastered_at":null,"reps":2,"shaky":1,"shaky_reviews":1,"skill_id":"calc1.extrema.critical-numbers","stability":6.25,"updated_at":1793631780000},"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":{"baseline_median_ms":65000,"baseline_n":2,"first_correct_ms":"[70000,70000]","skill_id":"calc1.extrema.critical-numbers","target_at":null,"target_ms":90000,"tier":3,"updated_at":1793631780000},"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":{"credited_stability":3.125,"skill_id":"calc1.deriv.power-rule","updated_at":1793631780000},"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":1793631780000,"last_seen_at":1793631780000,"redo_due_at":1793977380000,"redo_guaranteed":0,"times_seen":4,"updated_at":1793631780000},"table":"card_user"},{"key":{"id":2},"row":{"after_items":3,"attempt_id":6,"card_id":null,"created_at":1793631780000,"depth":1,"id":2,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(7,1793631840000,'2026-11-02',NULL,2,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'self',1,1,0,0,'sure',0,0,8000,NULL,NULL,NULL,NULL,0,NULL,0,0,3,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":{"card_id":"calc1.mvt.001","difficulty":4.0,"due_at":1793804490000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545290000,"leech":0,"ord":0,"reps":1,"stability":3.0,"updated_at":1793545290000},"table":"flashcard_state"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":{"card_id":"calc1.mvt.001","difficulty":4.0,"due_at":1793891040000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631840000,"leech":0,"ord":0,"reps":2,"stability":4.0,"updated_at":1793631840000},"table":"flashcard_state"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(8,1793631900000,'2026-11-02',NULL,2,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,'check',NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,6,NULL,'{}','{"rows":[{"key":{"id":2},"row":{"after_items":3,"attempt_id":6,"card_id":null,"created_at":1793631780000,"depth":1,"id":2,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}','{"rows":[{"key":{"id":2},"row":{"after_items":3,"attempt_id":6,"card_id":null,"created_at":1793631780000,"depth":1,"id":2,"kind":"step","not_before_at":null,"resolved_at":1793631900000,"resolved_by":8,"skill_id":"alg.factor.polynomials","status":"passed"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(9,1793718300000,'2026-11-03',1793718259000,3,'p2','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,'t01','due','0, 1','{0, 1}','incorrect',1,0,0,0,'sure',0,0,40000,35000,5000,41000,40000,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'0.1.0','{}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":1793631780000,"last_seen_at":1793631780000,"redo_due_at":1793977380000,"redo_guaranteed":0,"times_seen":4,"updated_at":1793631780000},"table":"card_user"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793718300000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":5,"updated_at":1793718300000},"table":"card_user"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(10,1793718330000,'2026-11-03',NULL,3,'p2','calc1.4-1.crit-numbers.001',3,'calc1','problem','calc1.extrema.critical-numbers',NULL,3,42,NULL,NULL,'-1, 0, 1',NULL,'correct',2,1,1,0,'unsure',1,0,70000,60000,10000,75000,70000,1,4000,0,0,2,0,0.91,'default-6','r1','recommended','slip',2,NULL,NULL,'0.1.0','{"part_results":{"a":"correct"}}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":{"difficulty":5.5,"due_at":1794171780000,"elo_n":2,"elo_theta":0.1,"fsrs_state":2,"fsrs_step":null,"introduced_at":null,"lapses":0,"last_review_at":1793631780000,"learned_at":null,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":1793631780000,"level_evidence":"{\"days\":2}","mastered_at":null,"reps":2,"shaky":1,"shaky_reviews":1,"skill_id":"calc1.extrema.critical-numbers","stability":6.25,"updated_at":1793631780000},"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":{"baseline_median_ms":65000,"baseline_n":2,"first_correct_ms":"[70000,70000]","skill_id":"calc1.extrema.critical-numbers","target_at":null,"target_ms":90000,"tier":3,"updated_at":1793631780000},"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":{"credited_stability":3.125,"skill_id":"calc1.deriv.power-rule","updated_at":1793631780000},"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":null,"last_seen_at":1793718300000,"redo_due_at":null,"redo_guaranteed":0,"times_seen":5,"updated_at":1793718300000},"table":"card_user"},{"key":{"id":3},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"calc1.extrema.critical-numbers"},"row":{"difficulty":5.5,"due_at":1795068330000,"elo_n":3,"elo_theta":0.2,"fsrs_state":2,"fsrs_step":null,"introduced_at":null,"lapses":0,"last_review_at":1793718330000,"learned_at":null,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":1793718330000,"level_evidence":"{\"days\":3}","mastered_at":null,"reps":3,"shaky":0,"shaky_reviews":2,"skill_id":"calc1.extrema.critical-numbers","stability":15.625,"updated_at":1793718330000},"table":"skill_state"},{"key":{"skill_id":"calc1.extrema.critical-numbers","tier":3},"row":{"baseline_median_ms":65000,"baseline_n":3,"first_correct_ms":"[70000,70000,70000]","skill_id":"calc1.extrema.critical-numbers","target_at":null,"target_ms":90000,"tier":3,"updated_at":1793718330000},"table":"skill_tier"},{"key":{"skill_id":"calc1.deriv.power-rule"},"row":{"credited_stability":7.8125,"skill_id":"calc1.deriv.power-rule","updated_at":1793718330000},"table":"skill_shadow"},{"key":{"card_id":"calc1.4-1.crit-numbers.001"},"row":{"card_id":"calc1.4-1.crit-numbers.001","last_correct_at":1793718330000,"last_seen_at":1793718330000,"redo_due_at":1794063930000,"redo_guaranteed":0,"times_seen":6,"updated_at":1793718330000},"table":"card_user"},{"key":{"id":3},"row":{"after_items":3,"attempt_id":10,"card_id":null,"created_at":1793718330000,"depth":1,"id":3,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(11,1793718390000,'2026-11-03',NULL,3,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'self',1,1,0,0,'sure',0,0,8000,NULL,NULL,NULL,NULL,0,NULL,0,0,3,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":{"card_id":"calc1.mvt.001","difficulty":4.0,"due_at":1793891040000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631840000,"leech":0,"ord":0,"reps":2,"stability":4.0,"updated_at":1793631840000},"table":"flashcard_state"}],"v":1}','{"rows":[{"key":{"card_id":"calc1.mvt.001","ord":0},"row":{"card_id":"calc1.mvt.001","difficulty":4.0,"due_at":1793977590000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793718390000,"leech":0,"ord":0,"reps":3,"stability":5.0,"updated_at":1793718390000},"table":"flashcard_state"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(12,1793718450000,'2026-11-03',NULL,3,NULL,'calc1.mvt.001',1,NULL,'flashcard',NULL,NULL,NULL,NULL,NULL,'check',NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,10,NULL,'{}','{"rows":[{"key":{"id":3},"row":{"after_items":3,"attempt_id":10,"card_id":null,"created_at":1793718330000,"depth":1,"id":3,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"alg.factor.polynomials","status":"pending"},"table":"pending_check"}],"v":1}','{"rows":[{"key":{"id":3},"row":{"after_items":3,"attempt_id":10,"card_id":null,"created_at":1793718330000,"depth":1,"id":3,"kind":"step","not_before_at":null,"resolved_at":1793718450000,"resolved_by":12,"skill_id":"alg.factor.polynomials","status":"passed"},"table":"pending_check"}],"v":1}',NULL);
CREATE TABLE attempt_void (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  at           INTEGER NOT NULL,
  reason       TEXT NOT NULL CHECK (reason IN ('undo', 'dispute', 'report', 'recompute')),
  note         TEXT,
  state_before TEXT CHECK (state_before IS NULL OR json_valid(state_before)),
  state_after  TEXT CHECK (state_after IS NULL OR json_valid(state_after))
) STRICT;
CREATE TABLE card_mark (
  card_id    TEXT PRIMARY KEY NOT NULL,
  flagged    INTEGER NOT NULL DEFAULT 0 CHECK (flagged IN (0, 1)),
  flag_note  TEXT,
  suspended  INTEGER NOT NULL DEFAULT 0 CHECK (suspended IN (0, 1)),
  hidden     INTEGER NOT NULL DEFAULT 0 CHECK (hidden IN (0, 1)),
  updated_at INTEGER NOT NULL
) STRICT;
INSERT INTO "card_mark" VALUES('calc1.mvt.001',1,'typo?',0,0,1793545200000);
INSERT INTO "card_mark" VALUES('calc1.4-1.crit-numbers.001',0,NULL,0,1,1793804850000);
CREATE TABLE card_user (
  card_id         TEXT PRIMARY KEY NOT NULL,
  last_seen_at    INTEGER,
  times_seen      INTEGER NOT NULL DEFAULT 0 CHECK (times_seen >= 0),
  last_correct_at INTEGER,
  redo_due_at     INTEGER,
  redo_guaranteed INTEGER NOT NULL DEFAULT 0 CHECK (redo_guaranteed IN (0, 1)),
  updated_at      INTEGER NOT NULL
) STRICT;
INSERT INTO "card_user" VALUES('calc1.4-1.crit-numbers.001',1793718330000,6,1793718330000,1794063930000,0,1793718330000);
CREATE TABLE course_goal (
  course_id        TEXT PRIMARY KEY NOT NULL,
  goal             TEXT NOT NULL DEFAULT 'A' CHECK (goal IN ('A', 'B', 'Keep', 'custom')),
  custom_retention REAL CHECK (custom_retention IS NULL OR custom_retention BETWEEN 0.80 AND 0.95),
  goal_date        TEXT CHECK (goal_date IS NULL OR date(goal_date) IS goal_date),
  starts_on        TEXT CHECK (starts_on IS NULL OR date(starts_on) IS starts_on),
  updated_at       INTEGER NOT NULL,
  CHECK ((goal = 'custom') = (custom_retention IS NOT NULL))
) STRICT;
INSERT INTO "course_goal" VALUES('calc1','custom',0.85,'2026-12-15',NULL,1793545200000);
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
INSERT INTO "diagnostic_set" VALUES(1,'alg.factor.polynomials',1,1793804850000,'pending','["a.1","a.2","a.3"]',0,0,NULL);
CREATE TABLE dispute (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id  INTEGER NOT NULL REFERENCES attempt(id),
  at          INTEGER NOT NULL,
  raw_input   TEXT,
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'upheld', 'rejected')),
  resolved_at INTEGER,
  note        TEXT
) STRICT;
INSERT INTO "dispute" VALUES(1,1,1793804850000,'0, 1','open',NULL,'I was right');
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
INSERT INTO "exam" VALUES(1,'calc1','Test 3',1795273200000,75,12,'["calc1.4-1"]',NULL,1793545200000);
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
INSERT INTO "flashcard_state" VALUES('calc1.mvt.001',0,2,NULL,5.0,4.0,1793977590000,1793718390000,3,0,0,1793718390000);
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
INSERT INTO "implicit_credit" VALUES(1,1793545230000,2,'calc1.extrema.critical-numbers','calc1.deriv.power-rule',0.5,'shadow',1.0,1.4,NULL);
INSERT INTO "implicit_credit" VALUES(2,1793631780000,6,'calc1.extrema.critical-numbers','calc1.deriv.power-rule',0.5,'shadow',1.0,1.4,NULL);
INSERT INTO "implicit_credit" VALUES(3,1793718330000,10,'calc1.extrema.critical-numbers','calc1.deriv.power-rule',0.5,'shadow',1.0,1.4,NULL);
CREATE TABLE import_record (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      INTEGER NOT NULL,
  file    TEXT NOT NULL,
  kind    TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(summary)),
  backup  TEXT
) STRICT;
INSERT INTO "import_record" VALUES(1,1793545200000,'deck.apkg','apkg','{"added":3,"rejected":0}','b.db');
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
INSERT INTO "pending_check" VALUES(1,1793545230000,2,'alg.factor.polynomials','step',NULL,3,NULL,1,'passed',1793545350000,4);
INSERT INTO "pending_check" VALUES(2,1793631780000,6,'alg.factor.polynomials','step',NULL,3,NULL,1,'passed',1793631900000,8);
INSERT INTO "pending_check" VALUES(3,1793718330000,10,'alg.factor.polynomials','step',NULL,3,NULL,1,'passed',1793718450000,12);
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
INSERT INTO "report" VALUES(1,'calc1.4-1.crit-numbers.001',3,2,1793804850000,'typo in key','open',NULL);
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
INSERT INTO "review_log" VALUES(1,1793545230000,2,'skill','calc1.extrema.critical-numbers',0,2,'r1','default-6',0.85,0.91,NULL,'{"difficulty":5.5,"due_at":1793761230000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545230000,"reps":1,"stability":2.5}',NULL);
INSERT INTO "review_log" VALUES(2,1793545290000,3,'flashcard','calc1.mvt.001',0,3,'r1',NULL,NULL,NULL,NULL,'{"difficulty":4.0,"due_at":1793804490000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545290000,"reps":1,"stability":3.0}',NULL);
INSERT INTO "review_log" VALUES(3,1793631780000,6,'skill','calc1.extrema.critical-numbers',0,2,'r1','default-6',0.85,0.91,'{"difficulty":5.5,"due_at":1793761230000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545230000,"reps":1,"stability":2.5}','{"difficulty":5.5,"due_at":1794171780000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631780000,"reps":2,"stability":6.25}',NULL);
INSERT INTO "review_log" VALUES(4,1793631840000,7,'flashcard','calc1.mvt.001',0,3,'r1',NULL,NULL,NULL,'{"difficulty":4.0,"due_at":1793804490000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793545290000,"reps":1,"stability":3.0}','{"difficulty":4.0,"due_at":1793891040000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631840000,"reps":2,"stability":4.0}',NULL);
INSERT INTO "review_log" VALUES(5,1793718330000,10,'skill','calc1.extrema.critical-numbers',0,2,'r1','default-6',0.85,0.91,'{"difficulty":5.5,"due_at":1794171780000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631780000,"reps":2,"stability":6.25}','{"difficulty":5.5,"due_at":1795068330000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793718330000,"reps":3,"stability":15.625}',NULL);
INSERT INTO "review_log" VALUES(6,1793718390000,11,'flashcard','calc1.mvt.001',0,3,'r1',NULL,NULL,NULL,'{"difficulty":4.0,"due_at":1793891040000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793631840000,"reps":2,"stability":4.0}','{"difficulty":4.0,"due_at":1793977590000,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1793718390000,"reps":3,"stability":5.0}',NULL);
CREATE TABLE section_state (
  section_id TEXT PRIMARY KEY NOT NULL,
  state      TEXT NOT NULL CHECK (state IN ('off', 'learning', 'covered', 'solid')),
  changed_at INTEGER NOT NULL
) STRICT;
INSERT INTO "section_state" VALUES('calc1.4-1','learning',1793545200000);
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
INSERT INTO "session" VALUES(1,'2026-11-01',1793545200000,1793545350000,1793545350000,0,'{"day":0,"items":["calc1.4-1.crit-numbers.001","calc1.mvt.001"]}',4,'{"card_id":"calc1.4-1.crit-numbers.001","seed":42}',1234,'x^2','{}');
INSERT INTO "session" VALUES(2,'2026-11-02',1793631750000,1793631900000,1793631900000,1,'{"day":1,"items":["calc1.4-1.crit-numbers.001","calc1.mvt.001"]}',4,'{"card_id":"calc1.4-1.crit-numbers.001","seed":42}',1234,'x^2','{}');
INSERT INTO "session" VALUES(3,'2026-11-03',1793718300000,1793718450000,NULL,0,'{"day":2,"items":["calc1.4-1.crit-numbers.001","calc1.mvt.001"]}',4,'{"card_id":"calc1.4-1.crit-numbers.001","seed":42}',1234,'x^2','{}');
CREATE TABLE setting (
  key        TEXT PRIMARY KEY NOT NULL,
  value      TEXT NOT NULL CHECK (json_valid(value)),
  updated_at INTEGER NOT NULL
) STRICT;
INSERT INTO "setting" VALUES('daily.problems','25',1793545200000);
INSERT INTO "setting" VALUES('queue.easy_days','{"sat":50}',1793545200000);
INSERT INTO "setting" VALUES('custom.flag','[1,2]',1793545200000);
CREATE TABLE skill_shadow (
  skill_id           TEXT PRIMARY KEY NOT NULL,
  credited_stability REAL,
  updated_at         INTEGER NOT NULL
) STRICT;
INSERT INTO "skill_shadow" VALUES('calc1.deriv.power-rule',7.8125,1793718330000);
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
INSERT INTO "skill_state" VALUES('calc1.extrema.critical-numbers',2,NULL,15.625,5.5,1795068330000,1793718330000,3,0,0,NULL,NULL,0,0,'learned',1793718330000,'{"days":3}',0,2,NULL,NULL,0.2,3,1793718330000);
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
INSERT INTO "skill_tier" VALUES('calc1.extrema.critical-numbers',3,90000,NULL,65000,3,'[70000,70000,70000]',1793718330000);
CREATE TABLE user_card (
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
INSERT INTO "user_card" VALUES('mine.trig.001',1,'problem','mine.trig',2,'number','1','{}',NULL,0,'radians',0,NULL,NULL,NULL,NULL,'[]','sin^2 + cos^2?',NULL,'[]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
CREATE TABLE user_card_choice (
  card_id TEXT NOT NULL REFERENCES user_card(id),
  part    TEXT NOT NULL DEFAULT '',
  role    TEXT NOT NULL CHECK (role IN ('choice', 'reason')),
  ord     INTEGER NOT NULL,
  text_md TEXT NOT NULL,
  correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
  PRIMARY KEY (card_id, part, role, ord)
) STRICT;
CREATE TABLE user_card_part (
  card_id     TEXT NOT NULL REFERENCES user_card(id),
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
CREATE TABLE user_card_revision (
  card_id        TEXT NOT NULL REFERENCES user_card(id),
  rev            INTEGER NOT NULL CHECK (rev >= 1),
  changed_at     INTEGER NOT NULL,
  note           TEXT NOT NULL DEFAULT '',
  answer_changed INTEGER NOT NULL DEFAULT 0 CHECK (answer_changed IN (0, 1)),
  PRIMARY KEY (card_id, rev)
) STRICT;
CREATE TABLE user_card_step (
  card_id  TEXT NOT NULL REFERENCES user_card(id),
  section  TEXT NOT NULL CHECK (section IN ('solution', 'alternative', 'shown-work')),
  number   INTEGER NOT NULL CHECK (number >= 0),
  skill_id TEXT,
  label    TEXT NOT NULL,
  body_md  TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (card_id, section, number)
) STRICT;
CREATE TABLE user_card_use (
  card_id  TEXT NOT NULL REFERENCES user_card(id),
  ord      INTEGER NOT NULL,
  skill_id TEXT NOT NULL,
  PRIMARY KEY (card_id, skill_id)
) STRICT;
CREATE TABLE user_card_wrong (
  card_id  TEXT NOT NULL REFERENCES user_card(id),
  part     TEXT NOT NULL DEFAULT '',
  ord      INTEGER NOT NULL,
  answer   TEXT NOT NULL,
  feedback TEXT,
  step     INTEGER CHECK (step IS NULL OR step >= 0),
  PRIMARY KEY (card_id, part, ord)
) STRICT;
CREATE TABLE user_course (
  id    TEXT PRIMARY KEY NOT NULL,
  title TEXT NOT NULL,
  ord   INTEGER NOT NULL DEFAULT 0
) STRICT;
INSERT INTO "user_course" VALUES('mine','My deck',0);
CREATE TABLE user_section (
  id           TEXT PRIMARY KEY NOT NULL,
  unit_id      TEXT NOT NULL,
  title        TEXT NOT NULL,
  ord          INTEGER NOT NULL DEFAULT 0,
  textbook_ref TEXT
) STRICT;
CREATE TABLE user_skill (
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
INSERT INTO "user_skill" VALUES('mine.trig','Trig identities',NULL,NULL,NULL,0,0,NULL,NULL);
CREATE TABLE user_skill_edge (
  skill_id TEXT NOT NULL REFERENCES user_skill(id),
  kind     TEXT NOT NULL CHECK (kind IN ('requires', 'encompasses', 'confusable')),
  other_id TEXT NOT NULL,
  ord      INTEGER NOT NULL DEFAULT 0,
  weight   REAL CHECK ((kind = 'encompasses') = (weight IS NOT NULL)),
  PRIMARY KEY (skill_id, kind, other_id),
  CHECK (skill_id <> other_id)
) STRICT;
INSERT INTO "user_skill_edge" VALUES('mine.trig','requires','calc1.deriv.power-rule',0,NULL);
CREATE TABLE user_unit (
  id        TEXT PRIMARY KEY NOT NULL,
  course_id TEXT NOT NULL,
  title     TEXT NOT NULL,
  ord       INTEGER NOT NULL DEFAULT 0
) STRICT;
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
INSERT INTO "weak_spot" VALUES(1,'alg.factor.polynomials',1793804850000,'2026-11-04',-2.4,6.0,3,6,2,'open',NULL);
CREATE INDEX skill_state_due ON skill_state(due_at);
CREATE INDEX flashcard_state_due ON flashcard_state(due_at);
CREATE INDEX pending_check_open ON pending_check(status, skill_id);
CREATE INDEX session_open ON session(ended_at, updated_at);
CREATE INDEX attempt_skill ON attempt(skill_id, at);
CREATE INDEX attempt_card ON attempt(card_id, at);
CREATE INDEX attempt_day ON attempt(study_day);
CREATE INDEX attempt_session ON attempt(session_id);
CREATE INDEX attempt_presentation ON attempt(presentation_id);
CREATE INDEX review_log_target ON review_log(target_kind, target_id, at);
CREATE INDEX review_log_attempt ON review_log(attempt_id);
CREATE INDEX implicit_credit_attempt ON implicit_credit(attempt_id);
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
CREATE INDEX user_skill_section ON user_skill(section_id);
CREATE INDEX user_skill_edge_other ON user_skill_edge(other_id, kind);
CREATE INDEX user_card_skill ON user_card(skill_id, tier);
CREATE INDEX user_card_template ON user_card(template_id);
CREATE INDEX user_card_section ON user_card(section_id);
CREATE INDEX user_card_use_skill ON user_card_use(skill_id);
CREATE INDEX user_card_step_skill ON user_card_step(skill_id);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('exam',1);
INSERT INTO "sqlite_sequence" VALUES('import_record',1);
INSERT INTO "sqlite_sequence" VALUES('session',3);
INSERT INTO "sqlite_sequence" VALUES('attempt',12);
INSERT INTO "sqlite_sequence" VALUES('pending_check',3);
INSERT INTO "sqlite_sequence" VALUES('review_log',6);
INSERT INTO "sqlite_sequence" VALUES('implicit_credit',3);
INSERT INTO "sqlite_sequence" VALUES('weak_spot',1);
INSERT INTO "sqlite_sequence" VALUES('diagnostic_set',1);
INSERT INTO "sqlite_sequence" VALUES('dispute',1);
INSERT INTO "sqlite_sequence" VALUES('report',1);
COMMIT;
