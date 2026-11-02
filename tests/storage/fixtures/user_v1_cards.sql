-- Frozen user.db at schema v1, written by the v1 code (tests/storage/v1_cards.py).
-- Never edit.
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
INSERT INTO "attempt" VALUES(1,1788280200000,'2026-09-01',NULL,NULL,NULL,'crit.t2.0',1,NULL,'problem','c.crit',NULL,2,0,'crit.t2',NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,40000,40000,NULL,40000,40000,0,NULL,0,0,NULL,0,0.88395198802734454,'fsrs6-default','2026.11-r1',NULL,'step',1,NULL,NULL,NULL,'{"baseline_ok":true,"diagnosis":{"blame":{"c.alg":0.20571020393938538,"c.crit":0.19428979606061467,"c.pow":0.6},"checks":[{"card":"c.pow.t2.0","depth":0,"kind":"step","reason":"Check after a miss on Critical numbers: did Power rule at the step \u201cDifferentiate\u201d break?","skill":"c.pow"}],"choice":"step","cued":false,"held":{"check":"c.pow","kind":"step"},"p":0.817574,"step":1,"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4},"tap_factor":1.0,"tapped":"c.pow"},"elo":{"d":-0.5,"d_after":-0.45,"form":"template:crit.t2","o":0,"p":0.817574,"theta":1.0},"purpose":"review","reasons":["wrong"],"slow":false,"speed_ms":46500,"stage":"review"}','{"rows":[{"key":{"skill_id":"c.crit"},"row":{"difficulty":5.0,"due_at":null,"elo_n":10,"elo_theta":1.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.crit","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"crit.t2.0"},"row":null,"table":"card_user"},{"key":{"skill_id":"c.crit","tier":2},"row":null,"table":"skill_tier"},{"key":{"id":1},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"c.crit"},"row":{"difficulty":5.0,"due_at":1788336000000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-02\",\"not_before\":\"2026-09-02\",\"reason\":\"Waiting for its check after the miss on 2026-09-01\"},\"hold\":{\"at\":1788280200000,\"check_skill\":\"c.pow\",\"day\":\"2026-09-01\",\"entry\":{\"c\":false,\"d\":\"2026-09-01\",\"e\":25.0,\"f\":\"template:crit.t2\",\"ms\":46500,\"ok\":false,\"p\":0.884,\"r\":null,\"t\":2,\"x\":false},\"kind\":\"step\",\"last_review_at\":1786120200000,\"pass_rating\":2},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.crit","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"crit.t2.0"},"row":{"card_id":"crit.t2.0","last_correct_at":null,"last_seen_at":1788280200000,"redo_due_at":1788336000000,"redo_guaranteed":1,"times_seen":1,"updated_at":1788280200000},"table":"card_user"},{"key":{"skill_id":"c.crit","tier":2},"row":{"baseline_median_ms":null,"baseline_n":0,"first_correct_ms":"[]","skill_id":"c.crit","target_at":null,"target_ms":null,"tier":2,"updated_at":1788280200000},"table":"skill_tier"},{"key":{"id":1},"row":{"after_items":3,"attempt_id":1,"card_id":"c.pow.t2.0","created_at":1788280200000,"depth":0,"id":1,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.pow","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(2,1788280500000,'2026-09-01',NULL,NULL,NULL,'c.pow.t2.0',1,NULL,'problem','c.pow',NULL,2,0,'c.pow.t2',NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,40000,40000,NULL,40000,40000,0,NULL,0,0,1,0,0.98566670351158614,'fsrs6-default','2026.11-r1',NULL,NULL,NULL,NULL,1,NULL,'{"baseline_ok":true,"diagnosis":{"blame":{"c.pow":1.0},"check":{"id":1,"kind":"step"},"checks":[{"card":"c.alg.t1.0","depth":1,"kind":"prerequisite","reason":"Check: Factor polynomials is a prerequisite of Power rule, which was just missed","skill":"c.alg"}],"choice":null,"cued":false,"p":0.924142,"resolved":{"check":1,"choice":"step","confirmed":true,"kind":"step","skill":"c.pow","trigger":1},"tags":{"c.pow":1.0}},"elo":{"d":-0.5,"d_after":-0.45,"form":"template:c.pow.t2","o":0,"p":0.924142,"theta":2.0},"purpose":"review","reasons":["wrong"],"slow":false,"speed_ms":46500,"stage":"review"}','{"rows":[{"key":{"skill_id":"c.pow"},"row":{"difficulty":5.0,"due_at":null,"elo_n":10,"elo_theta":2.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":1786293000000,"lapses":0,"last_review_at":1788021000000,"learned_at":1786725000000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.pow","stability":30.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.pow.t2.0"},"row":null,"table":"card_user"},{"key":{"skill_id":"c.pow","tier":2},"row":null,"table":"skill_tier"},{"key":{"skill_id":"c.crit"},"row":{"difficulty":5.0,"due_at":1788336000000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-02\",\"not_before\":\"2026-09-02\",\"reason\":\"Waiting for its check after the miss on 2026-09-01\"},\"hold\":{\"at\":1788280200000,\"check_skill\":\"c.pow\",\"day\":\"2026-09-01\",\"entry\":{\"c\":false,\"d\":\"2026-09-01\",\"e\":25.0,\"f\":\"template:crit.t2\",\"ms\":46500,\"ok\":false,\"p\":0.884,\"r\":null,\"t\":2,\"x\":false},\"kind\":\"step\",\"last_review_at\":1786120200000,\"pass_rating\":2},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.crit","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"id":1},"row":{"after_items":3,"attempt_id":1,"card_id":"c.pow.t2.0","created_at":1788280200000,"depth":0,"id":1,"kind":"step","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.pow","status":"pending"},"table":"pending_check"},{"key":{"id":2},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"c.pow"},"row":{"difficulty":8.341762369296838,"due_at":1788336000000,"elo_n":11,"elo_theta":1.3839054533474957,"fsrs_state":3,"fsrs_step":null,"introduced_at":1786293000000,"lapses":1,"last_review_at":1788280500000,"learned_at":1786725000000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learning","level_at":1788280500000,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":5,"shaky":0,"shaky_reviews":0,"skill_id":"c.pow","stability":2.017946891489868,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.pow.t2.0"},"row":{"card_id":"c.pow.t2.0","last_correct_at":null,"last_seen_at":1788280500000,"redo_due_at":1788336000000,"redo_guaranteed":1,"times_seen":1,"updated_at":1788280500000},"table":"card_user"},{"key":{"skill_id":"c.pow","tier":2},"row":{"baseline_median_ms":null,"baseline_n":0,"first_correct_ms":"[]","skill_id":"c.pow","target_at":null,"target_ms":null,"tier":2,"updated_at":1788280500000},"table":"skill_tier"},{"key":{"skill_id":"c.crit"},"row":{"difficulty":5.0,"due_at":1787558400000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-03\",\"not_before\":\"2026-09-02\",\"reason\":\"Earlier review: Power rule, which it builds on, just lapsed\"},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.crit","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"id":1},"row":{"after_items":3,"attempt_id":1,"card_id":"c.pow.t2.0","created_at":1788280200000,"depth":0,"id":1,"kind":"step","not_before_at":null,"resolved_at":1788280500000,"resolved_by":2,"skill_id":"c.pow","status":"failed"},"table":"pending_check"},{"key":{"id":2},"row":{"after_items":3,"attempt_id":2,"card_id":"c.alg.t1.0","created_at":1788280500000,"depth":1,"id":2,"kind":"prerequisite","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.alg","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
INSERT INTO "attempt" VALUES(3,1788280800000,'2026-09-01',NULL,NULL,NULL,'c.prod.t2.1',1,NULL,'problem','c.prod',NULL,2,1,'c.prod.t2',NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,40000,40000,NULL,40000,40000,0,NULL,0,0,NULL,0,0.88393114084895386,'fsrs6-default','2026.11-r1',NULL,'setup',NULL,NULL,NULL,NULL,'{"baseline_ok":true,"diagnosis":{"blame":{"c.mc":0.6,"c.pow":0.00035789431155596943,"c.prod":0.39964210568844405},"checks":[{"card":"c.prod.t2.0","depth":0,"kind":"cued-twin","reason":"The same kind of Product rule problem with the method named: was it the method, or choosing it?","skill":"c.prod"}],"choice":"setup","cued":false,"held":{"check":"c.prod","kind":"cued-twin"},"p":0.817574,"tags":{"c.mc":0.4,"c.pow":0.4,"c.prod":1.0}},"elo":{"d":-0.5,"d_after":-0.45,"form":"template:c.prod.t2","o":0,"p":0.817574,"theta":1.0},"purpose":"review","reasons":["wrong"],"slow":false,"speed_ms":46500,"stage":"review"}','{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":null,"elo_n":10,"elo_theta":1.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.1"},"row":null,"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":null,"table":"skill_tier"},{"key":{"id":3},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":1788336000000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-02\",\"not_before\":\"2026-09-02\",\"reason\":\"Waiting for its check after the miss on 2026-09-01\"},\"hold\":{\"at\":1788280800000,\"check_skill\":\"c.prod\",\"day\":\"2026-09-01\",\"entry\":{\"c\":false,\"d\":\"2026-09-01\",\"e\":25.007,\"f\":\"template:c.prod.t2\",\"ms\":46500,\"ok\":false,\"p\":0.8839,\"r\":null,\"t\":2,\"x\":false},\"kind\":\"cued-twin\",\"last_review_at\":1786120200000,\"pass_rating\":null},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.1"},"row":{"card_id":"c.prod.t2.1","last_correct_at":null,"last_seen_at":1788280800000,"redo_due_at":1788336000000,"redo_guaranteed":1,"times_seen":1,"updated_at":1788280800000},"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":{"baseline_median_ms":null,"baseline_n":0,"first_correct_ms":"[]","skill_id":"c.prod","target_at":null,"target_ms":null,"tier":2,"updated_at":1788280800000},"table":"skill_tier"},{"key":{"id":3},"row":{"after_items":3,"attempt_id":3,"card_id":"c.prod.t2.0","created_at":1788280800000,"depth":0,"id":3,"kind":"cued-twin","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.prod","status":"pending"},"table":"pending_check"}],"v":1}',1);
INSERT INTO "attempt" VALUES(4,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.0',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:0","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(5,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.1',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:1","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(6,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.2',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:2","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(7,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.3',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:3","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(8,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.4',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:4","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(9,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.5',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:5","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(10,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.0',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:6","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(11,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.1',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"blame":{"c.alg":0.6,"c.crit":0.3,"c.pow":0.1},"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:7","o":0,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(12,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.4',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,3,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:100","o":1,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(13,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.5',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,3,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:101","o":1,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(14,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.0',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,3,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:102","o":1,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(15,1788363600000,'2026-09-02',NULL,NULL,NULL,'crit.t2.1',1,NULL,'problem','c.crit',NULL,2,NULL,NULL,NULL,NULL,NULL,'correct',1,1,0,0,'sure',0,0,NULL,NULL,NULL,NULL,NULL,0,NULL,0,0,3,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'{"diagnosis":{"tags":{"c.alg":0.4,"c.crit":1.0,"c.pow":0.4}},"elo":{"d":0,"d_after":0,"form":"card:103","o":1,"p":0.8175744761936437,"theta":1.0},"stage":"review"}','{"rows":[],"v":1}','{"rows":[],"v":1}',NULL);
INSERT INTO "attempt" VALUES(16,1788367500000,'2026-09-02',NULL,NULL,NULL,'c.prod.t2.2',1,NULL,'problem','c.prod',NULL,2,2,'c.prod.t2',NULL,NULL,NULL,'incorrect',1,1,0,0,'sure',0,0,40000,40000,NULL,40000,40000,0,NULL,0,0,NULL,0,0.88095680537715193,'fsrs6-default','2026.11-r1',NULL,'setup',NULL,NULL,NULL,NULL,'{"baseline_ok":true,"diagnosis":{"blame":{"c.mc":0.6,"c.pow":0.06670228217018032,"c.prod":0.3332977178298197},"checks":[{"card":"c.prod.t2.0","depth":0,"kind":"cued-twin","reason":"The same kind of Product rule problem with the method named: was it the method, or choosing it?","skill":"c.prod"}],"choice":"setup","cued":false,"held":{"check":"c.prod","kind":"cued-twin"},"p":0.817574,"tags":{"c.mc":0.4,"c.pow":0.4,"c.prod":1.0}},"elo":{"d":-0.5,"d_after":-0.45,"form":"template:c.prod.t2","o":0,"p":0.817574,"theta":1.0},"purpose":"review","reasons":["wrong"],"slow":false,"speed_ms":46500,"stage":"review"}','{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":null,"elo_n":10,"elo_theta":1.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.2"},"row":null,"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":null,"table":"skill_tier"},{"key":{"id":12},"row":null,"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":1788422400000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-03\",\"not_before\":\"2026-09-03\",\"reason\":\"Waiting for its check after the miss on 2026-09-02\"},\"hold\":{\"at\":1788367500000,\"check_skill\":\"c.prod\",\"day\":\"2026-09-02\",\"entry\":{\"c\":false,\"d\":\"2026-09-02\",\"e\":26.01,\"f\":\"template:c.prod.t2\",\"ms\":46500,\"ok\":false,\"p\":0.881,\"r\":null,\"t\":2,\"x\":false},\"kind\":\"cued-twin\",\"last_review_at\":1786120200000,\"pass_rating\":null},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.2"},"row":{"card_id":"c.prod.t2.2","last_correct_at":null,"last_seen_at":1788367500000,"redo_due_at":1788422400000,"redo_guaranteed":1,"times_seen":1,"updated_at":1788367500000},"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":{"baseline_median_ms":null,"baseline_n":0,"first_correct_ms":"[]","skill_id":"c.prod","target_at":null,"target_ms":null,"tier":2,"updated_at":1788367500000},"table":"skill_tier"},{"key":{"id":12},"row":{"after_items":3,"attempt_id":16,"card_id":"c.prod.t2.0","created_at":1788367500000,"depth":0,"id":12,"kind":"cued-twin","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.prod","status":"pending"},"table":"pending_check"}],"v":1}',NULL);
CREATE TABLE attempt_void (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  at           INTEGER NOT NULL,
  reason       TEXT NOT NULL CHECK (reason IN ('undo', 'dispute', 'report', 'recompute')),
  note         TEXT,
  state_before TEXT CHECK (state_before IS NULL OR json_valid(state_before)),
  state_after  TEXT CHECK (state_after IS NULL OR json_valid(state_after))
) STRICT;
INSERT INTO "attempt_void" VALUES(1,1788280800000,'undo',NULL,'{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":1788336000000,"elo_n":11,"elo_theta":0.4549503492042376,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"due_adjust\":{\"last_review_at\":1786120200000,\"not_after\":\"2026-09-02\",\"not_before\":\"2026-09-02\",\"reason\":\"Waiting for its check after the miss on 2026-09-01\"},\"hold\":{\"at\":1788280800000,\"check_skill\":\"c.prod\",\"day\":\"2026-09-01\",\"entry\":{\"c\":false,\"d\":\"2026-09-01\",\"e\":25.007,\"f\":\"template:c.prod.t2\",\"ms\":46500,\"ok\":false,\"p\":0.8839,\"r\":null,\"t\":2,\"x\":false},\"kind\":\"cued-twin\",\"last_review_at\":1786120200000,\"pass_rating\":null},\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.1"},"row":{"card_id":"c.prod.t2.1","last_correct_at":null,"last_seen_at":1788280800000,"redo_due_at":1788336000000,"redo_guaranteed":1,"times_seen":1,"updated_at":1788280800000},"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":{"baseline_median_ms":null,"baseline_n":0,"first_correct_ms":"[]","skill_id":"c.prod","target_at":null,"target_ms":null,"tier":2,"updated_at":1788280800000},"table":"skill_tier"},{"key":{"id":3},"row":{"after_items":3,"attempt_id":3,"card_id":"c.prod.t2.0","created_at":1788280800000,"depth":0,"id":3,"kind":"cued-twin","not_before_at":null,"resolved_at":null,"resolved_by":null,"skill_id":"c.prod","status":"pending"},"table":"pending_check"}],"v":1}','{"rows":[{"key":{"skill_id":"c.prod"},"row":{"difficulty":5.0,"due_at":null,"elo_n":10,"elo_theta":1.0,"fsrs_state":2,"fsrs_step":null,"introduced_at":1784392200000,"lapses":0,"last_review_at":1786120200000,"learned_at":1784824200000,"learning_count":0,"learning_streak":0,"leech":0,"leech_at":null,"level":"learned","level_at":null,"level_evidence":"{\"log\":[]}","mastered_at":null,"reps":4,"shaky":0,"shaky_reviews":0,"skill_id":"c.prod","stability":20.0,"updated_at":1788280200000},"table":"skill_state"},{"key":{"card_id":"c.prod.t2.1"},"row":null,"table":"card_user"},{"key":{"skill_id":"c.prod","tier":2},"row":null,"table":"skill_tier"},{"key":{"id":3},"row":null,"table":"pending_check"}],"v":1}');
CREATE TABLE card_mark (
  card_id    TEXT PRIMARY KEY NOT NULL,
  flagged    INTEGER NOT NULL DEFAULT 0 CHECK (flagged IN (0, 1)),
  flag_note  TEXT,
  suspended  INTEGER NOT NULL DEFAULT 0 CHECK (suspended IN (0, 1)),
  hidden     INTEGER NOT NULL DEFAULT 0 CHECK (hidden IN (0, 1)),
  updated_at INTEGER NOT NULL
) STRICT;
CREATE TABLE card_user (
  card_id         TEXT PRIMARY KEY NOT NULL,
  last_seen_at    INTEGER,
  times_seen      INTEGER NOT NULL DEFAULT 0 CHECK (times_seen >= 0),
  last_correct_at INTEGER,
  redo_due_at     INTEGER,
  redo_guaranteed INTEGER NOT NULL DEFAULT 0 CHECK (redo_guaranteed IN (0, 1)),
  updated_at      INTEGER NOT NULL
) STRICT;
INSERT INTO "card_user" VALUES('crit.t2.0',1788280200000,1,NULL,1788336000000,1,1788280200000);
INSERT INTO "card_user" VALUES('c.pow.t2.0',1788280500000,1,NULL,1788336000000,1,1788280500000);
INSERT INTO "card_user" VALUES('c.prod.t2.2',1788367500000,1,NULL,1788422400000,1,1788367500000);
CREATE TABLE course_goal (
  course_id        TEXT PRIMARY KEY NOT NULL,
  goal             TEXT NOT NULL DEFAULT 'A' CHECK (goal IN ('A', 'B', 'Keep', 'custom')),
  custom_retention REAL CHECK (custom_retention IS NULL OR custom_retention BETWEEN 0.80 AND 0.95),
  goal_date        TEXT CHECK (goal_date IS NULL OR date(goal_date) IS goal_date),
  starts_on        TEXT CHECK (starts_on IS NULL OR date(starts_on) IS starts_on),
  updated_at       INTEGER NOT NULL,
  CHECK ((goal = 'custom') = (custom_retention IS NOT NULL))
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
INSERT INTO "diagnostic_set" VALUES(1,'c.alg',1,1788367200000,'pending','["c.alg.t1.0","c.alg.t2.0","c.alg.t1.1","c.alg.t1.2"]',0,0,NULL);
INSERT INTO "diagnostic_set" VALUES(2,'c.pow',2,1788367200000,'pending','["c.pow.t2.1","c.pow.t1.0","c.pow.t2.2","c.pow.t2.3"]',0,0,NULL);
CREATE TABLE dispute (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id  INTEGER NOT NULL REFERENCES attempt(id),
  at          INTEGER NOT NULL,
  raw_input   TEXT,
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'upheld', 'rejected')),
  resolved_at INTEGER,
  note        TEXT
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
CREATE TABLE import_record (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      INTEGER NOT NULL,
  file    TEXT NOT NULL,
  kind    TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(summary)),
  backup  TEXT
) STRICT;
INSERT INTO "import_record" VALUES(1,1788278400000,'algebra.cards.md, geometry.cards.md','cards','{"added":["mine.alg.fixed.001","mine.alg.double.t01--57028f63","mine.alg.double.t01--474f709d","mine.alg.double.t01--a66c78da","mine.alg.const.t01--e3b0c442","mine.alg.mul.t01--2f3a978c","mine.alg.mul.t01--0b275f42","mine.alg.mul.t01--58b48d9f","mine.alg.mul.t01--95a57e89","mine.geo.tri.001"],"files":{"algebra.cards.md":{"ids":["mine.alg.fixed.001","mine.alg.double.t01","mine.alg.const.t01","mine.alg.mul.t01"],"templates":{"mine.alg.const.t01":"## Card mine.alg.const.t01\ndeck: Mine::Algebra\nskill: mine.alg.double\ndifficulty: 1\nanswer-type: number\nanswer: 2 + 3\n\n### Question\nWhat is [[2 + 3]]?\n\n### Hints\n1. Add.\n\n### Solution\n0. [mine.alg.double] Add: [[2 + 3]].","mine.alg.double.t01":"## Card mine.alg.double.t01\ndeck: Mine::Algebra\nskill: mine.alg.double\ndifficulty: 1\nanswer-type: number\nvars: k = int(1, 3)\nanswer: 2*k\n\n### Question\nDouble [[k]].\n\n### Hints\n1. Add it to itself.\n\n### Solution\n0. [mine.alg.double] Double: [[2*k]].\n\n### Notes\nWatch the sign.\n\nA second paragraph of notes.","mine.alg.mul.t01":"## Card mine.alg.mul.t01\ndeck: Mine::Algebra\nskill: mine.alg.multiply\ndifficulty: 2\nanswer-type: number\nvars: a = int(2, 3); b = choice(1/2, 3)\nanswer: a*b\n\n### Question\nMultiply [[a]] by [[b]].\n\n### Hints\n1. Multiply.\n\n### Solution\n0. [mine.alg.multiply] Multiply: [[a*b]]."}},"geometry.cards.md":{"ids":["mine.geo.tri.001"],"templates":{}}},"key_updated":[],"missing":[],"rejected":[],"retired":[],"retired_instances":[],"skills":{"added":[],"created":["mine.alg.double","mine.alg.multiply","mine.geo.area"],"updated":[]},"unchanged":0,"updated":[]}',NULL);
INSERT INTO "import_record" VALUES(2,1788279000000,'deck.apkg','apkg','{"added":3,"files":{"x":{}}}',NULL);
INSERT INTO "import_record" VALUES(3,1788279600000,'algebra.cards.md','cards','{"added":["mine.alg.double.t01--6142fb40"],"files":{"algebra.cards.md":{"ids":["mine.alg.fixed.001","mine.alg.double.t01","mine.alg.const.t01"],"templates":{"mine.alg.const.t01":"## Card mine.alg.const.t01\ndeck: Mine::Algebra\nskill: mine.alg.double\ndifficulty: 1\nanswer-type: number\nanswer: 2 + 3\n\n### Question\nWhat is [[2 + 3]]?\n\n### Hints\n1. Add.\n\n### Solution\n0. [mine.alg.double] Add: [[2 + 3]].","mine.alg.double.t01":"## Card mine.alg.double.t01\ndeck: Mine::Algebra\nskill: mine.alg.double\ndifficulty: 1\nanswer-type: number\nvars: k = int(2, 4)\nanswer: 2*k\n\n### Question\nDouble [[k]].\n\n### Hints\n1. Add it to itself.\n\n### Solution\n0. [mine.alg.double] Double: [[2*k]].\n\n### Notes\nWatch the sign.\n\nA second paragraph of notes."}}},"key_updated":[],"missing":["mine.alg.mul.t01"],"rejected":[],"retired":["mine.alg.double.t01--57028f63","mine.alg.mul.t01--0b275f42","mine.alg.mul.t01--2f3a978c","mine.alg.mul.t01--58b48d9f","mine.alg.mul.t01--95a57e89"],"retired_instances":["mine.alg.double.t01--57028f63"],"skills":{"added":[],"created":[],"updated":[]},"unchanged":4,"updated":[]}',NULL);
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
INSERT INTO "pending_check" VALUES(1,1788280200000,1,'c.pow','step','c.pow.t2.0',3,NULL,0,'failed',1788280500000,2);
INSERT INTO "pending_check" VALUES(2,1788280500000,2,'c.alg','prerequisite','c.alg.t1.0',3,NULL,1,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(4,1788367200000,NULL,'c.alg','diagnostic','c.alg.t1.0',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(5,1788367200000,NULL,'c.alg','diagnostic','c.alg.t2.0',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(6,1788367200000,NULL,'c.alg','diagnostic','c.alg.t1.1',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(7,1788367200000,NULL,'c.alg','diagnostic','c.alg.t1.2',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(8,1788367200000,NULL,'c.pow','diagnostic','c.pow.t2.1',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(9,1788367200000,NULL,'c.pow','diagnostic','c.pow.t1.0',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(10,1788367200000,NULL,'c.pow','diagnostic','c.pow.t2.2',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(11,1788367200000,NULL,'c.pow','diagnostic','c.pow.t2.3',0,1788367200000,0,'pending',NULL,NULL);
INSERT INTO "pending_check" VALUES(12,1788367500000,16,'c.prod','cued-twin','c.prod.t2.0',3,NULL,0,'pending',NULL,NULL);
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
INSERT INTO "review_log" VALUES(1,1788280500000,2,'skill','c.pow',0,1,'2026.11-r1','fsrs6-default',0.9,0.98566670351158614,'{"difficulty":5.0,"due_at":null,"fsrs_state":2,"fsrs_step":null,"lapses":0,"last_review_at":1788021000000,"reps":4,"stability":30.0}','{"difficulty":8.341762369296838,"due_at":1788336000000,"fsrs_state":3,"fsrs_step":null,"lapses":1,"last_review_at":1788280500000,"reps":5,"stability":2.017946891489868}',NULL);
CREATE TABLE section_state (
  section_id TEXT PRIMARY KEY NOT NULL,
  state      TEXT NOT NULL CHECK (state IN ('off', 'learning', 'covered', 'solid')),
  changed_at INTEGER NOT NULL
) STRICT;
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
CREATE TABLE setting (
  key        TEXT PRIMARY KEY NOT NULL,
  value      TEXT NOT NULL CHECK (json_valid(value)),
  updated_at INTEGER NOT NULL
) STRICT;
INSERT INTO "setting" VALUES('study.timezone','"America/New_York"',1788278400000);
CREATE TABLE skill_shadow (
  skill_id           TEXT PRIMARY KEY NOT NULL,
  credited_stability REAL,
  updated_at         INTEGER NOT NULL
) STRICT;
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
INSERT INTO "skill_state" VALUES('c.alg',2,NULL,2.0,5.0,NULL,1786552200000,4,0,0,NULL,1784824200000,0,0,'learned',NULL,'{"log":[]}',0,0,1785256200000,NULL,0.0,10,1788280200000);
INSERT INTO "skill_state" VALUES('c.pow',3,NULL,2.0179468914898679,8.3417623692968377,1788336000000,1788280500000,5,1,0,NULL,1786293000000,0,0,'learning',1788280500000,'{"log":[]}',0,0,1786725000000,NULL,1.3839054533474957,11,1788280200000);
INSERT INTO "skill_state" VALUES('c.crit',2,NULL,20.0,5.0,1787558400000,1786120200000,4,0,0,NULL,1784392200000,0,0,'learned',NULL,'{"due_adjust":{"last_review_at":1786120200000,"not_after":"2026-09-03","not_before":"2026-09-02","reason":"Earlier review: Power rule, which it builds on, just lapsed"},"log":[]}',0,0,1784824200000,NULL,0.4549503492042376,11,1788280200000);
INSERT INTO "skill_state" VALUES('c.prod',2,NULL,20.0,5.0,1788422400000,1786120200000,4,0,0,NULL,1784392200000,0,0,'learned',NULL,'{"due_adjust":{"last_review_at":1786120200000,"not_after":"2026-09-03","not_before":"2026-09-03","reason":"Waiting for its check after the miss on 2026-09-02"},"hold":{"at":1788367500000,"check_skill":"c.prod","day":"2026-09-02","entry":{"c":false,"d":"2026-09-02","e":26.01,"f":"template:c.prod.t2","ms":46500,"ok":false,"p":0.881,"r":null,"t":2,"x":false},"kind":"cued-twin","last_review_at":1786120200000,"pass_rating":null},"log":[]}',0,0,1784824200000,NULL,0.4549503492042376,11,1788280200000);
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
INSERT INTO "skill_tier" VALUES('c.crit',2,NULL,NULL,NULL,0,'[]',1788280200000);
INSERT INTO "skill_tier" VALUES('c.pow',2,NULL,NULL,NULL,0,'[]',1788280500000);
INSERT INTO "skill_tier" VALUES('c.prod',2,NULL,NULL,NULL,0,'[]',1788367500000);
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
INSERT INTO "user_card" VALUES('mine.alg.fixed.001',1,'problem','mine.alg.double',1,'number','2','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','What is \(1 + 1\)?',NULL,'["Count."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: not a template, so these notes stay as written',NULL,NULL,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
INSERT INTO "user_card" VALUES('mine.alg.double.t01--57028f63',1,'problem','mine.alg.double',1,'number','2','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Double 1.',NULL,'["Add it to itself."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: k = 1

Watch the sign.

A second paragraph of notes.','mine.alg.double.t01',1459785571,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','retired');
INSERT INTO "user_card" VALUES('mine.alg.double.t01--474f709d',1,'problem','mine.alg.double',1,'number','4','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Double 2.',NULL,'["Add it to itself."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: k = 2

Watch the sign.

A second paragraph of notes.','mine.alg.double.t01',1196388509,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
INSERT INTO "user_card" VALUES('mine.alg.double.t01--a66c78da',1,'problem','mine.alg.double',1,'number','6','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Double 3.',NULL,'["Add it to itself."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: k = 3

Watch the sign.

A second paragraph of notes.','mine.alg.double.t01',2792126682,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
INSERT INTO "user_card" VALUES('mine.alg.const.t01--e3b0c442',1,'problem','mine.alg.double',1,'number','2 + 3','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','What is 5?',NULL,'["Add."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: ','mine.alg.const.t01',3820012610,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
INSERT INTO "user_card" VALUES('mine.alg.mul.t01--2f3a978c',1,'problem','mine.alg.multiply',2,'number','1','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Multiply 2 by 1/2.',NULL,'["Multiply."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 1/2','mine.alg.mul.t01',792369036,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','retired');
INSERT INTO "user_card" VALUES('mine.alg.mul.t01--0b275f42',1,'problem','mine.alg.multiply',2,'number','6','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Multiply 2 by 3.',NULL,'["Multiply."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 3','mine.alg.mul.t01',187129666,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','retired');
INSERT INTO "user_card" VALUES('mine.alg.mul.t01--58b48d9f',1,'problem','mine.alg.multiply',2,'number','3/2','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Multiply 3 by 1/2.',NULL,'["Multiply."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 1/2','mine.alg.mul.t01',1488227743,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','retired');
INSERT INTO "user_card" VALUES('mine.alg.mul.t01--95a57e89',1,'problem','mine.alg.multiply',2,'number','9','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Multiply 3 by 3.',NULL,'["Multiply."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 3','mine.alg.mul.t01',2510651017,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','retired');
INSERT INTO "user_card" VALUES('mine.geo.tri.001',1,'problem','mine.geo.area',2,'number','6','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Geometry','Mine::Geometry','[]','![a right triangle with legs 3 and 4](media/tri.svg)
What is the area of the triangle?',NULL,'["Half the base times the height."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
INSERT INTO "user_card" VALUES('mine.alg.double.t01--6142fb40',1,'problem','mine.alg.double',1,'number','8','{}',NULL,0,'radians',0,NULL,NULL,'Mine::Algebra','Mine::Algebra','[]','Double 4.',NULL,'["Add it to itself."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: k = 4

Watch the sign.

A second paragraph of notes.','mine.alg.double.t01',1631779648,NULL,NULL,NULL,'[]',NULL,NULL,0,NULL,'[]',NULL,0,'unverified','active');
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
INSERT INTO "user_card_revision" VALUES('mine.alg.fixed.001',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.double.t01--57028f63',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.double.t01--474f709d',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.double.t01--a66c78da',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.const.t01--e3b0c442',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.mul.t01--2f3a978c',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.mul.t01--0b275f42',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.mul.t01--58b48d9f',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.mul.t01--95a57e89',1,1788278400000,'added from algebra.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.geo.tri.001',1,1788278400000,'added from geometry.cards.md',0);
INSERT INTO "user_card_revision" VALUES('mine.alg.double.t01--6142fb40',1,1788279600000,'added from algebra.cards.md',0);
CREATE TABLE user_card_step (
  card_id  TEXT NOT NULL REFERENCES user_card(id),
  section  TEXT NOT NULL CHECK (section IN ('solution', 'alternative', 'shown-work')),
  number   INTEGER NOT NULL CHECK (number >= 0),
  skill_id TEXT,
  label    TEXT NOT NULL,
  body_md  TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (card_id, section, number)
) STRICT;
INSERT INTO "user_card_step" VALUES('mine.alg.fixed.001','solution',0,'mine.alg.double','Add','\(1 + 1 = 2\).');
INSERT INTO "user_card_step" VALUES('mine.alg.double.t01--57028f63','solution',0,'mine.alg.double','Double','2.');
INSERT INTO "user_card_step" VALUES('mine.alg.double.t01--474f709d','solution',0,'mine.alg.double','Double','4.');
INSERT INTO "user_card_step" VALUES('mine.alg.double.t01--a66c78da','solution',0,'mine.alg.double','Double','6.');
INSERT INTO "user_card_step" VALUES('mine.alg.const.t01--e3b0c442','solution',0,'mine.alg.double','Add','5.');
INSERT INTO "user_card_step" VALUES('mine.alg.mul.t01--2f3a978c','solution',0,'mine.alg.multiply','Multiply','1.');
INSERT INTO "user_card_step" VALUES('mine.alg.mul.t01--0b275f42','solution',0,'mine.alg.multiply','Multiply','6.');
INSERT INTO "user_card_step" VALUES('mine.alg.mul.t01--58b48d9f','solution',0,'mine.alg.multiply','Multiply','3/2.');
INSERT INTO "user_card_step" VALUES('mine.alg.mul.t01--95a57e89','solution',0,'mine.alg.multiply','Multiply','9.');
INSERT INTO "user_card_step" VALUES('mine.geo.tri.001','solution',0,'mine.geo.area','Area','\(\tfrac12 \cdot 3 \cdot 4 = 6\).');
INSERT INTO "user_card_step" VALUES('mine.alg.double.t01--6142fb40','solution',0,'mine.alg.double','Double','8.');
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
INSERT INTO "user_course" VALUES('Mine','Mine',0);
CREATE TABLE user_section (
  id           TEXT PRIMARY KEY NOT NULL,
  unit_id      TEXT NOT NULL,
  title        TEXT NOT NULL,
  ord          INTEGER NOT NULL DEFAULT 0,
  textbook_ref TEXT
) STRICT;
INSERT INTO "user_section" VALUES('Mine::Algebra','Mine::Algebra','Algebra',0,NULL);
INSERT INTO "user_section" VALUES('Mine::Geometry','Mine::Geometry','Geometry',1,NULL);
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
INSERT INTO "user_skill" VALUES('mine.alg.double','mine.alg.double','Mine::Algebra','Mine::Algebra',NULL,0,0,NULL,NULL);
INSERT INTO "user_skill" VALUES('mine.alg.multiply','mine.alg.multiply','Mine::Algebra','Mine::Algebra',NULL,0,0,NULL,NULL);
INSERT INTO "user_skill" VALUES('mine.geo.area','mine.geo.area','Mine::Geometry','Mine::Geometry',NULL,0,0,NULL,NULL);
CREATE TABLE user_skill_edge (
  skill_id TEXT NOT NULL REFERENCES user_skill(id),
  kind     TEXT NOT NULL CHECK (kind IN ('requires', 'encompasses', 'confusable')),
  other_id TEXT NOT NULL,
  ord      INTEGER NOT NULL DEFAULT 0,
  weight   REAL CHECK ((kind = 'encompasses') = (weight IS NOT NULL)),
  PRIMARY KEY (skill_id, kind, other_id),
  CHECK (skill_id <> other_id)
) STRICT;
CREATE TABLE user_unit (
  id        TEXT PRIMARY KEY NOT NULL,
  course_id TEXT NOT NULL,
  title     TEXT NOT NULL,
  ord       INTEGER NOT NULL DEFAULT 0
) STRICT;
INSERT INTO "user_unit" VALUES('Mine::Algebra','Mine','Algebra',0);
INSERT INTO "user_unit" VALUES('Mine::Geometry','Mine','Geometry',1);
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
INSERT INTO "weak_spot" VALUES(1,'c.alg',1788367200000,'2026-09-02',-4.7085,9.9703,6,13,2,'open',NULL);
INSERT INTO "weak_spot" VALUES(2,'c.pow',1788367200000,'2026-09-02',-2.535,5.04,7,14,2,'open',NULL);
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
INSERT INTO "sqlite_sequence" VALUES('import_record',3);
INSERT INTO "sqlite_sequence" VALUES('pending_check',12);
INSERT INTO "sqlite_sequence" VALUES('attempt',16);
INSERT INTO "sqlite_sequence" VALUES('review_log',1);
INSERT INTO "sqlite_sequence" VALUES('attempt_void',1);
INSERT INTO "sqlite_sequence" VALUES('weak_spot',2);
INSERT INTO "sqlite_sequence" VALUES('diagnostic_set',2);
COMMIT;
