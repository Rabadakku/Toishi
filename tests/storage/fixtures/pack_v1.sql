-- Frozen sealed pack at pack schema v1 (packs/test), written by the v1 code
-- (tests/storage/v1_cards.py). Never edit.
BEGIN TRANSACTION;
CREATE TABLE card (
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
INSERT INTO "card" VALUES('test.linear.solve.001',1,'problem','test.alg.linear-solve',1,'number','5','{}',NULL,0,'radians',0,NULL,'hand test-pack 1.0','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','["equations","one-step"]','Solve \(3x + 5 = 20\).',NULL,'["Get the \\(x\\) term alone first.","Subtract \\(5\\) from both sides."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.line.001',1,'problem','test.alg.line-equation',2,'equation','y = 2x + 1','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Write the equation of the line with slope \(2\) and \(y\)-intercept \(1\).',NULL,'["Use slope-intercept form, \\(y = mx + b\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.simplify.001',1,'problem','test.alg.arithmetic',1,'expression','x + 6','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Simplify \(2(x + 3) - x\).',NULL,'["Distribute the \\(2\\) first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.check.001',1,'problem','test.alg.linear-solve',1,'truefalse','true','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','True or false: \(x = 2\) is a solution of \(3x + 1 = 7\).',NULL,'["Substitute \\(x = 2\\) into the left side."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.slope-name.001',1,'problem','test.alg.line-equation',1,'text','slope; the slope','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','In \(y = mx + b\), what is the number \(m\) called?',NULL,'["It measures how steep the line is."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.vector.001',1,'problem','test.alg.vectors',1,'vector','<3, 4>','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Write the vector from \((1, 2)\) to \((4, 6)\) in component form.',NULL,'["Subtract the coordinates of the start from the coordinates of the end."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.matrix.001',1,'problem','test.alg.matrices',2,'matrix','[[1, 2], [3, 4]]','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Write the coefficient matrix of the system \(x + 2y = 5\), \(3x + 4y = 6\).',NULL,'["One row per equation, one column per variable."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.degrees.001',1,'problem','test.alg.arithmetic',1,'number','2','{}',NULL,1,'degrees',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Evaluate \(2 \sin 30^\circ + 1\).',NULL,'["\\(\\sin 30^\\circ = \\frac{1}{2}\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original','https://example.org/test-pack','personal','[]',NULL,NULL,1,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.linear.explain.001',1,'problem','test.alg.linear-solve',2,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Explain why \(0x = 5\) has no solution.',NULL,'["What is \\(0\\) times any number?"]',NULL,NULL,'["Says that \\(0x = 0\\) for every \\(x\\)","Concludes that no number makes the equation true"]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
INSERT INTO "card" VALUES('test.linear.example.001',1,'example','test.alg.linear-solve',2,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2x - 7 = 3\).',NULL,'[]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
INSERT INTO "card" VALUES('test.linear.flash.001',1,'flashcard',NULL,2,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]',NULL,NULL,'[]',NULL,NULL,'[]',NULL,'What is the slope-intercept form of a line?','\(y = mx + b\), where \(m\) is the slope and \(b\) is the \(y\)-intercept.',NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
INSERT INTO "card" VALUES('test.linear.cloze.001',1,'cloze',NULL,2,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]',NULL,NULL,'[]',NULL,NULL,'[]',NULL,NULL,NULL,'To solve \(ax + b = c\), first {{c1::subtract \(b\) from both sides}}, then {{c2::divide both sides by \(a\)}}.','This works whenever \(a \ne 0\).',NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
INSERT INTO "card" VALUES('test.linear.solve.t01--cc2ed4ba',1,'problem','test.alg.linear-solve',1,'number','9/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 1 = 10\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 1; c = 10','test.linear.solve.t01',3425621178,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--d97e7279',1,'problem','test.alg.linear-solve',1,'number','19/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 1 = 20\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 1; c = 20','test.linear.solve.t01',3648942713,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--6f278589',1,'problem','test.alg.linear-solve',1,'number','4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 2 = 10\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 2; c = 10','test.linear.solve.t01',1864861065,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--26f719ef',1,'problem','test.alg.linear-solve',1,'number','9','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 2 = 20\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 2; c = 20','test.linear.solve.t01',653728239,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--0587c9e2',1,'problem','test.alg.linear-solve',1,'number','7/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 3 = 10\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 3; c = 10','test.linear.solve.t01',92785122,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--1ab13269',1,'problem','test.alg.linear-solve',1,'number','17/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 3 = 20\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 3; c = 20','test.linear.solve.t01',447820393,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--13560d01',1,'problem','test.alg.linear-solve',1,'number','3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 4 = 10\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 4; c = 10','test.linear.solve.t01',324406529,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--50634d10',1,'problem','test.alg.linear-solve',1,'number','8','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 4 = 20\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 4; c = 20','test.linear.solve.t01',1348685072,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--37400c93',1,'problem','test.alg.linear-solve',1,'number','5/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 5 = 10\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 5; c = 10','test.linear.solve.t01',926944403,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--9b0c38fc',1,'problem','test.alg.linear-solve',1,'number','15/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 5 = 20\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 5; c = 20','test.linear.solve.t01',2601269500,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--b9da0963',1,'problem','test.alg.linear-solve',1,'number','2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 6 = 10\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 6; c = 10','test.linear.solve.t01',3118074211,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--5f15055c',1,'problem','test.alg.linear-solve',1,'number','7','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(2 x + 6 = 20\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; b = 6; c = 20','test.linear.solve.t01',1595213148,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--4f9e0ebf',1,'problem','test.alg.linear-solve',1,'number','3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 1 = 10\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 1; c = 10','test.linear.solve.t01',1335758527,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--54249344',1,'problem','test.alg.linear-solve',1,'number','19/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 1 = 20\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 1; c = 20','test.linear.solve.t01',1411683140,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--554661df',1,'problem','test.alg.linear-solve',1,'number','8/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 2 = 10\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 2; c = 10','test.linear.solve.t01',1430675935,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--50739601',1,'problem','test.alg.linear-solve',1,'number','6','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 2 = 20\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 2; c = 20','test.linear.solve.t01',1349752321,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--39e7fcc6',1,'problem','test.alg.linear-solve',1,'number','7/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 3 = 10\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 3; c = 10','test.linear.solve.t01',971504838,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--e317d741',1,'problem','test.alg.linear-solve',1,'number','17/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 3 = 20\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 3; c = 20','test.linear.solve.t01',3809990465,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--e810f6eb',1,'problem','test.alg.linear-solve',1,'number','2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 4 = 10\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 4; c = 10','test.linear.solve.t01',3893425899,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--77333035',1,'problem','test.alg.linear-solve',1,'number','16/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 4 = 20\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 4; c = 20','test.linear.solve.t01',1999843381,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--37c8e675',1,'problem','test.alg.linear-solve',1,'number','5/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 5 = 10\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 5; c = 10','test.linear.solve.t01',935913077,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--b0a4fd9d',1,'problem','test.alg.linear-solve',1,'number','5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 5 = 20\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 5; c = 20','test.linear.solve.t01',2963602845,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--e13e7c59',1,'problem','test.alg.linear-solve',1,'number','4/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 6 = 10\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 6; c = 10','test.linear.solve.t01',3778968665,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--f71a42ce',1,'problem','test.alg.linear-solve',1,'number','14/3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(3 x + 6 = 20\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; b = 6; c = 20','test.linear.solve.t01',4145693390,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--92bd2908',1,'problem','test.alg.linear-solve',1,'number','9/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 1 = 10\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 1; c = 10','test.linear.solve.t01',2461870344,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--90e4c2c1',1,'problem','test.alg.linear-solve',1,'number','19/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 1 = 20\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 1; c = 20','test.linear.solve.t01',2430911169,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--b02ca601',1,'problem','test.alg.linear-solve',1,'number','2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 2 = 10\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 2; c = 10','test.linear.solve.t01',2955716097,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--4891c9ae',1,'problem','test.alg.linear-solve',1,'number','9/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 2 = 20\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 2; c = 20','test.linear.solve.t01',1217513902,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--98adbc27',1,'problem','test.alg.linear-solve',1,'number','7/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 3 = 10\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 3; c = 10','test.linear.solve.t01',2561522727,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--2c4aa87f',1,'problem','test.alg.linear-solve',1,'number','17/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 3 = 20\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 3; c = 20','test.linear.solve.t01',743090303,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--b51261b3',1,'problem','test.alg.linear-solve',1,'number','3/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 4 = 10\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 4; c = 10','test.linear.solve.t01',3037880755,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--04908abe',1,'problem','test.alg.linear-solve',1,'number','4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 4 = 20\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 4; c = 20','test.linear.solve.t01',76581566,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--1952c899',1,'problem','test.alg.linear-solve',1,'number','5/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 5 = 10\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 5; c = 10','test.linear.solve.t01',424855705,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--d0a12ae2',1,'problem','test.alg.linear-solve',1,'number','15/4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 5 = 20\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 5; c = 20','test.linear.solve.t01',3500223202,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--f396ddce',1,'problem','test.alg.linear-solve',1,'number','1','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 6 = 10\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 6; c = 10','test.linear.solve.t01',4086750670,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--2f2a7b6c',1,'problem','test.alg.linear-solve',1,'number','7/2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(4 x + 6 = 20\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; b = 6; c = 20','test.linear.solve.t01',791313260,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--be7dfaa1',1,'problem','test.alg.linear-solve',1,'number','9/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 1 = 10\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 1; c = 10','test.linear.solve.t01',3195927201,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--eb6df22e',1,'problem','test.alg.linear-solve',1,'number','19/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 1 = 20\).',NULL,'["Subtract \\(1\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 1; c = 20','test.linear.solve.t01',3949851182,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--8a986255',1,'problem','test.alg.linear-solve',1,'number','8/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 2 = 10\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 2; c = 10','test.linear.solve.t01',2325242453,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--6cda46b0',1,'problem','test.alg.linear-solve',1,'number','18/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 2 = 20\).',NULL,'["Subtract \\(2\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 2; c = 20','test.linear.solve.t01',1826244272,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--b70a4440',1,'problem','test.alg.linear-solve',1,'number','7/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 3 = 10\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 3; c = 10','test.linear.solve.t01',3070903360,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--c44412ae',1,'problem','test.alg.linear-solve',1,'number','17/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 3 = 20\).',NULL,'["Subtract \\(3\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 3; c = 20','test.linear.solve.t01',3292795566,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--9123e24b',1,'problem','test.alg.linear-solve',1,'number','6/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 4 = 10\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 4; c = 10','test.linear.solve.t01',2435048011,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--f5d4bda3',1,'problem','test.alg.linear-solve',1,'number','16/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 4 = 20\).',NULL,'["Subtract \\(4\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 4; c = 20','test.linear.solve.t01',4124360099,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--e45b948b',1,'problem','test.alg.linear-solve',1,'number','1','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 5 = 10\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 5; c = 10','test.linear.solve.t01',3831207051,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--9e4dba50',1,'problem','test.alg.linear-solve',1,'number','3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 5 = 20\).',NULL,'["Subtract \\(5\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 5; c = 20','test.linear.solve.t01',2655894096,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--978765ef',1,'problem','test.alg.linear-solve',1,'number','4/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 6 = 10\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 6; c = 10','test.linear.solve.t01',2542233071,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.linear.solve.t01--765b7d2d',1,'problem','test.alg.linear-solve',1,'number','14/5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','[]','Solve \(5 x + 6 = 20\).',NULL,'["Subtract \\(6\\) from both sides first."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; b = 6; c = 20','test.linear.solve.t01',1985707309,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.001',1,'problem','test.alg.quadratic-solve',2,'set','2, 3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^2 - 5x + 6 = 0\).',NULL,'["Find two numbers that multiply to \\(6\\) and add to \\(-5\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.coefficients.001',1,'problem','test.alg.quadratic-formula',1,'list','2, -3, 7','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','List the coefficients \(a\), \(b\), \(c\) of \(2x^2 - 3x + 7\), in that order.',NULL,'["Compare with \\(ax^2 + bx + c\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.inequality.001',1,'problem','test.alg.quadratic-solve',3,'interval','(-2, 2)','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^2 - 4 < 0\). Write the answer in interval notation.',NULL,'["Where is \\(x^2 - 4 = 0\\)?","Test a number between the zeros."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.vertex.001',1,'problem','test.alg.vertex',1,'point','(1, 3)','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Find the vertex of the parabola \(y = (x - 1)^2 + 3\).',NULL,'["Compare with \\(y = (x - h)^2 + k\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.parabola.001',1,'problem','test.alg.quadratic-solve',3,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Let \(f(x) = x^2 - 1\).

![The graph of y = x^2 - 1](media/parabola.svg)',NULL,'["Set \\(x^2 - 1 = 0\\).","The vertex of \\(y = x^2 + k\\) is \\((0, k)\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.factor-error.001',1,'find-error','test.alg.factor-quadratic',2,'expression','(x - 3)(x + 3)','{"form":"factored"}',NULL,0,'radians',0,2,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Factor \(x^2 - 9\).',NULL,'["Expand \\((x - 3)^2\\) and compare."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.method.001',1,'method','test.alg.choose-quadratic-method',2,'choice',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Which method fits best? \(x^2 + x - 1 = 0\)',NULL,'[]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--2df55cce',1,'problem','test.alg.quadratic-solve',2,'set','1, 2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 3 x + 2 = 0\).',NULL,'["Find two numbers that multiply to \\(2\\) and add to \\(-3\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 1; s = 2','test.quad.solve.t01',771054798,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--596e4ddd',1,'problem','test.alg.quadratic-solve',2,'set','1, 3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 4 x + 3 = 0\).',NULL,'["Find two numbers that multiply to \\(3\\) and add to \\(-4\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 1; s = 3','test.quad.solve.t01',1500401117,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--2cc9b5f4',1,'problem','test.alg.quadratic-solve',2,'set','1, 4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 5 x + 4 = 0\).',NULL,'["Find two numbers that multiply to \\(4\\) and add to \\(-5\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 1; s = 4','test.quad.solve.t01',751416820,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--c159b5f5',1,'problem','test.alg.quadratic-solve',2,'set','1, 5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 6 x + 5 = 0\).',NULL,'["Find two numbers that multiply to \\(5\\) and add to \\(-6\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 1; s = 5','test.quad.solve.t01',3243881973,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--1a75df75',1,'problem','test.alg.quadratic-solve',2,'set','2, 3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 5 x + 6 = 0\).',NULL,'["Find two numbers that multiply to \\(6\\) and add to \\(-5\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 2; s = 3','test.quad.solve.t01',443932533,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--c10ea89c',1,'problem','test.alg.quadratic-solve',2,'set','2, 4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 6 x + 8 = 0\).',NULL,'["Find two numbers that multiply to \\(8\\) and add to \\(-6\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 2; s = 4','test.quad.solve.t01',3238963356,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--c6c333ee',1,'problem','test.alg.quadratic-solve',2,'set','2, 5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 7 x + 10 = 0\).',NULL,'["Find two numbers that multiply to \\(10\\) and add to \\(-7\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 2; s = 5','test.quad.solve.t01',3334681582,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--ed9f7034',1,'problem','test.alg.quadratic-solve',2,'set','3, 4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 7 x + 12 = 0\).',NULL,'["Find two numbers that multiply to \\(12\\) and add to \\(-7\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 3; s = 4','test.quad.solve.t01',3986649140,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--bc4130a6',1,'problem','test.alg.quadratic-solve',2,'set','3, 5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 8 x + 15 = 0\).',NULL,'["Find two numbers that multiply to \\(15\\) and add to \\(-8\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 3; s = 5','test.quad.solve.t01',3158388902,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.quad.solve.t01--2b5330ff',1,'problem','test.alg.quadratic-solve',2,'set','4, 5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','[]','Solve \(x^{2} - 9 x + 20 = 0\).',NULL,'["Find two numbers that multiply to \\(20\\) and add to \\(-9\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: r = 4; s = 5','test.quad.solve.t01',726872319,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.001',1,'problem','test.calc.power-rule',1,'expression','3x^2 + 2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Find \(f''(x)\) for \(f(x) = x^3 + 2x\).','Use the power rule to find \(f''(x)\) for \(f(x) = x^3 + 2x\).','["Differentiate each term separately."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.deriv.antiderivative.001',1,'problem','test.calc.power-rule',2,'antiderivative','x^3 + C','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Find \(\displaystyle \int 3x^2 \, dx\).',NULL,'["Which function has derivative \\(3x^2\\)?"]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.deriv.limit-dne.001',1,'problem','test.calc.limits',2,'number','DNE','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Find \(\displaystyle \lim_{x \to 0} \frac{|x|}{x}\).',NULL,'["Compare \\(x\\) slightly above and slightly below \\(0\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.deriv.limit-inf.001',1,'problem','test.calc.limits',2,'number','inf','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Find \(\displaystyle \lim_{x \to 0} \frac{1}{x^2}\).',NULL,'["What happens to \\(x^2\\) as \\(x \\to 0\\)?"]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.deriv.critical-choice.001',1,'problem','test.calc.critical-points',2,'choice',NULL,'{}','x^3 - 3x, x = -2.5..2.5',0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Select all critical numbers of \(f(x) = x^3 - 3x\).',NULL,'["Solve \\(f''(x) = 0\\)."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'self-check','active');
INSERT INTO "card" VALUES('test.deriv.example.001',1,'example','test.calc.power-rule',2,'self',NULL,'{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 5x^4\).',NULL,'[]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,NULL,'active');
INSERT INTO "card" VALUES('test.deriv.power.t01--81b9036a',1,'problem','test.calc.power-rule',1,'expression','6*x^2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 2 x^{3}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; n = 3','test.deriv.power.t01',2176385898,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--3c194862',1,'problem','test.calc.power-rule',1,'expression','8*x^3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 2 x^{4}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; n = 4','test.deriv.power.t01',1008289890,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--47c7fdb3',1,'problem','test.calc.power-rule',1,'expression','10*x^4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 2 x^{5}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; n = 5','test.deriv.power.t01',1204288947,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--6e8e8334',1,'problem','test.calc.power-rule',1,'expression','12*x^5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 2 x^{6}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 2; n = 6','test.deriv.power.t01',1854833460,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--f4d53d2f',1,'problem','test.calc.power-rule',1,'expression','9*x^2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 3 x^{3}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; n = 3','test.deriv.power.t01',4107615535,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--e5616d60',1,'problem','test.calc.power-rule',1,'expression','12*x^3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 3 x^{4}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; n = 4','test.deriv.power.t01',3848367456,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--dc654051',1,'problem','test.calc.power-rule',1,'expression','15*x^4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 3 x^{5}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; n = 5','test.deriv.power.t01',3697623121,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--58410edd',1,'problem','test.calc.power-rule',1,'expression','18*x^5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 3 x^{6}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 3; n = 6','test.deriv.power.t01',1480658653,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--f0ebd192',1,'problem','test.calc.power-rule',1,'expression','12*x^2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 4 x^{3}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; n = 3','test.deriv.power.t01',4041986450,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--004a5723',1,'problem','test.calc.power-rule',1,'expression','16*x^3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 4 x^{4}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; n = 4','test.deriv.power.t01',4871971,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--5ab21fc7',1,'problem','test.calc.power-rule',1,'expression','20*x^4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 4 x^{5}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; n = 5','test.deriv.power.t01',1521622983,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--2b29a1e7',1,'problem','test.calc.power-rule',1,'expression','24*x^5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 4 x^{6}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 4; n = 6','test.deriv.power.t01',724148711,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--d4f94fc3',1,'problem','test.calc.power-rule',1,'expression','15*x^2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 5 x^{3}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; n = 3','test.deriv.power.t01',3573108675,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--cc198f9a',1,'problem','test.calc.power-rule',1,'expression','20*x^3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 5 x^{4}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; n = 4','test.deriv.power.t01',3424227226,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--ea43e0dd',1,'problem','test.calc.power-rule',1,'expression','25*x^4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 5 x^{5}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; n = 5','test.deriv.power.t01',3930317021,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--1eae4c84',1,'problem','test.calc.power-rule',1,'expression','30*x^5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 5 x^{6}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 5; n = 6','test.deriv.power.t01',514739332,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--482c054b',1,'problem','test.calc.power-rule',1,'expression','18*x^2','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 6 x^{3}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 6; n = 3','test.deriv.power.t01',1210844491,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--d7659828',1,'problem','test.calc.power-rule',1,'expression','24*x^3','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 6 x^{4}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 6; n = 4','test.deriv.power.t01',3613759528,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--23d78e95',1,'problem','test.calc.power-rule',1,'expression','30*x^4','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 6 x^{5}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 6; n = 5','test.deriv.power.t01',601329301,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
INSERT INTO "card" VALUES('test.deriv.power.t01--4bc36255',1,'problem','test.calc.power-rule',1,'expression','36*x^5','{}',NULL,0,'radians',0,NULL,NULL,'Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives','[]','Differentiate \(f(x) = 6 x^{6}\).',NULL,'["Bring the exponent down, then lower it by one."]',NULL,NULL,'[]',NULL,NULL,NULL,NULL,NULL,'template parameters: a = 6; n = 6','test.deriv.power.t01',1271095893,'original',NULL,'personal','[]',NULL,NULL,0,NULL,'[]',NULL,0,'template+cas','active');
CREATE TABLE card_choice (
  card_id TEXT NOT NULL REFERENCES card(id),
  part    TEXT NOT NULL DEFAULT '',
  role    TEXT NOT NULL CHECK (role IN ('choice', 'reason')),
  ord     INTEGER NOT NULL,
  text_md TEXT NOT NULL,
  correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
  PRIMARY KEY (card_id, part, role, ord)
) STRICT;
INSERT INTO "card_choice" VALUES('test.quad.parabola.001','c','choice',0,'Up',1);
INSERT INTO "card_choice" VALUES('test.quad.parabola.001','c','choice',1,'Down',0);
INSERT INTO "card_choice" VALUES('test.quad.factor-error.001','','reason',0,'\(9\) is not a perfect square',0);
INSERT INTO "card_choice" VALUES('test.quad.factor-error.001','','reason',1,'A difference of squares factors as \((a - b)(a + b)\), not \((a - b)^2\)',1);
INSERT INTO "card_choice" VALUES('test.quad.factor-error.001','','reason',2,'The \(x^2\) term should have been factored out first',0);
INSERT INTO "card_choice" VALUES('test.quad.method.001','','choice',0,'Factor over the integers',0);
INSERT INTO "card_choice" VALUES('test.quad.method.001','','choice',1,'The quadratic formula',1);
INSERT INTO "card_choice" VALUES('test.quad.method.001','','choice',2,'Take the square root of both sides',0);
INSERT INTO "card_choice" VALUES('test.deriv.critical-choice.001','','choice',0,'\(-1\)',1);
INSERT INTO "card_choice" VALUES('test.deriv.critical-choice.001','','choice',1,'\(0\)',0);
INSERT INTO "card_choice" VALUES('test.deriv.critical-choice.001','','choice',2,'\(1\)',1);
INSERT INTO "card_choice" VALUES('test.deriv.critical-choice.001','','choice',3,'\(3\)',0);
CREATE TABLE card_part (
  card_id     TEXT NOT NULL REFERENCES card(id),
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
INSERT INTO "card_part" VALUES('test.quad.parabola.001',0,'a','Find the zeros of \(f\).','set','-1, 1','{}',NULL);
INSERT INTO "card_part" VALUES('test.quad.parabola.001',1,'b','Find the vertex of the graph of \(f\).','point','(0, -1)','{}','test.alg.vertex');
INSERT INTO "card_part" VALUES('test.quad.parabola.001',2,'c','Which way does the graph open?','choice',NULL,'{}','test.alg.vertex');
CREATE TABLE card_revision (
  card_id        TEXT NOT NULL REFERENCES card(id),
  rev            INTEGER NOT NULL CHECK (rev >= 1),
  changed_at     INTEGER NOT NULL,
  note           TEXT NOT NULL DEFAULT '',
  answer_changed INTEGER NOT NULL DEFAULT 0 CHECK (answer_changed IN (0, 1)),
  PRIMARY KEY (card_id, rev)
) STRICT;
INSERT INTO "card_revision" VALUES('test.linear.solve.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.line.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.simplify.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.check.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.slope-name.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.vector.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.matrix.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.degrees.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.explain.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.example.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.flash.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.cloze.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--cc2ed4ba',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--d97e7279',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--6f278589',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--26f719ef',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--0587c9e2',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--1ab13269',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--13560d01',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--50634d10',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--37400c93',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--9b0c38fc',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--b9da0963',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--5f15055c',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--4f9e0ebf',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--54249344',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--554661df',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--50739601',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--39e7fcc6',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--e317d741',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--e810f6eb',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--77333035',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--37c8e675',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--b0a4fd9d',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--e13e7c59',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--f71a42ce',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--92bd2908',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--90e4c2c1',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--b02ca601',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--4891c9ae',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--98adbc27',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--2c4aa87f',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--b51261b3',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--04908abe',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--1952c899',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--d0a12ae2',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--f396ddce',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--2f2a7b6c',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--be7dfaa1',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--eb6df22e',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--8a986255',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--6cda46b0',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--b70a4440',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--c44412ae',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--9123e24b',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--f5d4bda3',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--e45b948b',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--9e4dba50',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--978765ef',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.linear.solve.t01--765b7d2d',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.coefficients.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.inequality.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.vertex.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.parabola.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.factor-error.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.method.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--2df55cce',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--596e4ddd',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--2cc9b5f4',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--c159b5f5',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--1a75df75',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--c10ea89c',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--c6c333ee',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--ed9f7034',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--bc4130a6',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.quad.solve.t01--2b5330ff',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.antiderivative.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.limit-dne.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.limit-inf.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.critical-choice.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.example.001',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--81b9036a',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--3c194862',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--47c7fdb3',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--6e8e8334',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--f4d53d2f',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--e5616d60',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--dc654051',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--58410edd',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--f0ebd192',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--004a5723',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--5ab21fc7',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--2b29a1e7',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--d4f94fc3',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--cc198f9a',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--ea43e0dd',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--1eae4c84',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--482c054b',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--d7659828',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--23d78e95',1,1,'added in 1.0.0',0);
INSERT INTO "card_revision" VALUES('test.deriv.power.t01--4bc36255',1,1,'added in 1.0.0',0);
CREATE TABLE card_step (
  card_id  TEXT NOT NULL REFERENCES card(id),
  section  TEXT NOT NULL CHECK (section IN ('solution', 'alternative', 'shown-work')),
  number   INTEGER NOT NULL CHECK (number >= 0),
  skill_id TEXT,
  label    TEXT NOT NULL,
  body_md  TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (card_id, section, number)
) STRICT;
INSERT INTO "card_step" VALUES('test.linear.solve.001','solution',0,'test.alg.linear-solve','Set up','undo the operations on \(x\) in reverse order.');
INSERT INTO "card_step" VALUES('test.linear.solve.001','solution',1,'test.alg.arithmetic','Subtract 5','\(3x = 15\).');
INSERT INTO "card_step" VALUES('test.linear.solve.001','solution',2,'test.alg.linear-solve','Divide by 3','\(x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.line.001','solution',0,'test.alg.line-equation','Set up','slope-intercept form is \(y = mx + b\).');
INSERT INTO "card_step" VALUES('test.linear.line.001','solution',1,'test.alg.line-equation','Substitute','\(m = 2\) and \(b = 1\) give \(y = 2x + 1\).');
INSERT INTO "card_step" VALUES('test.linear.simplify.001','solution',0,'test.alg.arithmetic','Set up','distribute, then combine like terms.');
INSERT INTO "card_step" VALUES('test.linear.simplify.001','solution',1,'test.alg.arithmetic','Distribute','\(2x + 6 - x\).');
INSERT INTO "card_step" VALUES('test.linear.simplify.001','solution',2,'test.alg.arithmetic','Combine like terms','\(x + 6\).');
INSERT INTO "card_step" VALUES('test.linear.check.001','solution',0,'test.alg.linear-solve','Set up','a solution makes both sides equal.');
INSERT INTO "card_step" VALUES('test.linear.check.001','solution',1,'test.alg.arithmetic','Substitute','\(3 \cdot 2 + 1 = 7\), so the statement is true.');
INSERT INTO "card_step" VALUES('test.linear.slope-name.001','solution',0,'test.alg.line-equation','Name it','\(m\) is the slope, the rise over the run.');
INSERT INTO "card_step" VALUES('test.linear.vector.001','solution',0,'test.alg.vectors','Set up','the components are end minus start.');
INSERT INTO "card_step" VALUES('test.linear.vector.001','solution',1,'test.alg.arithmetic','Subtract','\(\langle 4 - 1, 6 - 2 \rangle = \langle 3, 4 \rangle\).');
INSERT INTO "card_step" VALUES('test.linear.matrix.001','solution',0,'test.alg.matrices','Set up','row \(i\) holds the coefficients of equation \(i\), in the order \(x\), \(y\).');
INSERT INTO "card_step" VALUES('test.linear.matrix.001','solution',1,'test.alg.matrices','Fill in','\(\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}\).');
INSERT INTO "card_step" VALUES('test.linear.degrees.001','solution',0,'test.alg.arithmetic','Evaluate','\(2 \cdot \frac{1}{2} + 1 = 2\).');
INSERT INTO "card_step" VALUES('test.linear.explain.001','solution',0,'test.alg.linear-solve','Set up','a solution is a number that makes both sides equal.');
INSERT INTO "card_step" VALUES('test.linear.explain.001','solution',1,'test.alg.arithmetic','Reason','\(0x = 0\) for every \(x\), and \(0 \ne 5\), so no number works.');
INSERT INTO "card_step" VALUES('test.linear.example.001','solution',0,'test.alg.linear-solve','Set up','undo the subtraction, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.example.001','solution',1,'test.alg.arithmetic','Add 7','\(2x = 10\).');
INSERT INTO "card_step" VALUES('test.linear.example.001','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--cc2ed4ba','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--cc2ed4ba','solution',1,'test.alg.arithmetic','Subtract 1','\(2x = 9\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--cc2ed4ba','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{9}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d97e7279','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d97e7279','solution',1,'test.alg.arithmetic','Subtract 1','\(2x = 19\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d97e7279','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{19}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6f278589','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6f278589','solution',1,'test.alg.arithmetic','Subtract 2','\(2x = 8\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6f278589','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--26f719ef','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--26f719ef','solution',1,'test.alg.arithmetic','Subtract 2','\(2x = 18\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--26f719ef','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 9\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--0587c9e2','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--0587c9e2','solution',1,'test.alg.arithmetic','Subtract 3','\(2x = 7\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--0587c9e2','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{7}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1ab13269','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1ab13269','solution',1,'test.alg.arithmetic','Subtract 3','\(2x = 17\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1ab13269','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{17}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--13560d01','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--13560d01','solution',1,'test.alg.arithmetic','Subtract 4','\(2x = 6\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--13560d01','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 3\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50634d10','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50634d10','solution',1,'test.alg.arithmetic','Subtract 4','\(2x = 16\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50634d10','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 8\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37400c93','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37400c93','solution',1,'test.alg.arithmetic','Subtract 5','\(2x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37400c93','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{5}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9b0c38fc','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9b0c38fc','solution',1,'test.alg.arithmetic','Subtract 5','\(2x = 15\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9b0c38fc','solution',2,'test.alg.linear-solve','Divide by 2','\(x = \frac{15}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b9da0963','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b9da0963','solution',1,'test.alg.arithmetic','Subtract 6','\(2x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b9da0963','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 2\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--5f15055c','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--5f15055c','solution',1,'test.alg.arithmetic','Subtract 6','\(2x = 14\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--5f15055c','solution',2,'test.alg.linear-solve','Divide by 2','\(x = 7\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4f9e0ebf','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4f9e0ebf','solution',1,'test.alg.arithmetic','Subtract 1','\(3x = 9\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4f9e0ebf','solution',2,'test.alg.linear-solve','Divide by 3','\(x = 3\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--54249344','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--54249344','solution',1,'test.alg.arithmetic','Subtract 1','\(3x = 19\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--54249344','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{19}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--554661df','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--554661df','solution',1,'test.alg.arithmetic','Subtract 2','\(3x = 8\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--554661df','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{8}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50739601','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50739601','solution',1,'test.alg.arithmetic','Subtract 2','\(3x = 18\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--50739601','solution',2,'test.alg.linear-solve','Divide by 3','\(x = 6\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--39e7fcc6','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--39e7fcc6','solution',1,'test.alg.arithmetic','Subtract 3','\(3x = 7\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--39e7fcc6','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{7}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e317d741','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e317d741','solution',1,'test.alg.arithmetic','Subtract 3','\(3x = 17\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e317d741','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{17}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e810f6eb','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e810f6eb','solution',1,'test.alg.arithmetic','Subtract 4','\(3x = 6\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e810f6eb','solution',2,'test.alg.linear-solve','Divide by 3','\(x = 2\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--77333035','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--77333035','solution',1,'test.alg.arithmetic','Subtract 4','\(3x = 16\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--77333035','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{16}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37c8e675','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37c8e675','solution',1,'test.alg.arithmetic','Subtract 5','\(3x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--37c8e675','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{5}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b0a4fd9d','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b0a4fd9d','solution',1,'test.alg.arithmetic','Subtract 5','\(3x = 15\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b0a4fd9d','solution',2,'test.alg.linear-solve','Divide by 3','\(x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e13e7c59','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e13e7c59','solution',1,'test.alg.arithmetic','Subtract 6','\(3x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e13e7c59','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{4}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f71a42ce','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f71a42ce','solution',1,'test.alg.arithmetic','Subtract 6','\(3x = 14\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f71a42ce','solution',2,'test.alg.linear-solve','Divide by 3','\(x = \frac{14}{3}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--92bd2908','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--92bd2908','solution',1,'test.alg.arithmetic','Subtract 1','\(4x = 9\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--92bd2908','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{9}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--90e4c2c1','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--90e4c2c1','solution',1,'test.alg.arithmetic','Subtract 1','\(4x = 19\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--90e4c2c1','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{19}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b02ca601','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b02ca601','solution',1,'test.alg.arithmetic','Subtract 2','\(4x = 8\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b02ca601','solution',2,'test.alg.linear-solve','Divide by 4','\(x = 2\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4891c9ae','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4891c9ae','solution',1,'test.alg.arithmetic','Subtract 2','\(4x = 18\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--4891c9ae','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{9}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--98adbc27','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--98adbc27','solution',1,'test.alg.arithmetic','Subtract 3','\(4x = 7\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--98adbc27','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{7}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2c4aa87f','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2c4aa87f','solution',1,'test.alg.arithmetic','Subtract 3','\(4x = 17\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2c4aa87f','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{17}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b51261b3','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b51261b3','solution',1,'test.alg.arithmetic','Subtract 4','\(4x = 6\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b51261b3','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{3}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--04908abe','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--04908abe','solution',1,'test.alg.arithmetic','Subtract 4','\(4x = 16\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--04908abe','solution',2,'test.alg.linear-solve','Divide by 4','\(x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1952c899','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1952c899','solution',1,'test.alg.arithmetic','Subtract 5','\(4x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--1952c899','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{5}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d0a12ae2','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d0a12ae2','solution',1,'test.alg.arithmetic','Subtract 5','\(4x = 15\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--d0a12ae2','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{15}{4}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f396ddce','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f396ddce','solution',1,'test.alg.arithmetic','Subtract 6','\(4x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f396ddce','solution',2,'test.alg.linear-solve','Divide by 4','\(x = 1\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2f2a7b6c','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2f2a7b6c','solution',1,'test.alg.arithmetic','Subtract 6','\(4x = 14\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--2f2a7b6c','solution',2,'test.alg.linear-solve','Divide by 4','\(x = \frac{7}{2}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--be7dfaa1','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--be7dfaa1','solution',1,'test.alg.arithmetic','Subtract 1','\(5x = 9\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--be7dfaa1','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{9}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--eb6df22e','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--eb6df22e','solution',1,'test.alg.arithmetic','Subtract 1','\(5x = 19\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--eb6df22e','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{19}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--8a986255','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--8a986255','solution',1,'test.alg.arithmetic','Subtract 2','\(5x = 8\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--8a986255','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{8}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6cda46b0','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6cda46b0','solution',1,'test.alg.arithmetic','Subtract 2','\(5x = 18\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--6cda46b0','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{18}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b70a4440','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b70a4440','solution',1,'test.alg.arithmetic','Subtract 3','\(5x = 7\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--b70a4440','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{7}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--c44412ae','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--c44412ae','solution',1,'test.alg.arithmetic','Subtract 3','\(5x = 17\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--c44412ae','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{17}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9123e24b','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9123e24b','solution',1,'test.alg.arithmetic','Subtract 4','\(5x = 6\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9123e24b','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{6}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f5d4bda3','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f5d4bda3','solution',1,'test.alg.arithmetic','Subtract 4','\(5x = 16\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--f5d4bda3','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{16}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e45b948b','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e45b948b','solution',1,'test.alg.arithmetic','Subtract 5','\(5x = 5\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--e45b948b','solution',2,'test.alg.linear-solve','Divide by 5','\(x = 1\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9e4dba50','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9e4dba50','solution',1,'test.alg.arithmetic','Subtract 5','\(5x = 15\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--9e4dba50','solution',2,'test.alg.linear-solve','Divide by 5','\(x = 3\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--978765ef','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--978765ef','solution',1,'test.alg.arithmetic','Subtract 6','\(5x = 4\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--978765ef','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{4}{5}\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--765b7d2d','solution',0,'test.alg.linear-solve','Set up','undo the addition, then the multiplication.');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--765b7d2d','solution',1,'test.alg.arithmetic','Subtract 6','\(5x = 14\).');
INSERT INTO "card_step" VALUES('test.linear.solve.t01--765b7d2d','solution',2,'test.alg.linear-solve','Divide by 5','\(x = \frac{14}{5}\).');
INSERT INTO "card_step" VALUES('test.quad.solve.001','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.001','solution',1,'test.alg.factor-quadratic','Factor','\((x - 2)(x - 3) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.001','solution',2,'test.alg.linear-solve','Solve','\(x = 2\) or \(x = 3\).');
INSERT INTO "card_step" VALUES('test.quad.coefficients.001','solution',0,'test.alg.quadratic-formula','Set up','match the terms of \(ax^2 + bx + c\).');
INSERT INTO "card_step" VALUES('test.quad.coefficients.001','solution',1,'test.alg.quadratic-formula','Read off','\(a = 2\), \(b = -3\), \(c = 7\).');
INSERT INTO "card_step" VALUES('test.quad.inequality.001','solution',0,'test.alg.quadratic-solve','Set up','find the zeros, then test the sign between them.');
INSERT INTO "card_step" VALUES('test.quad.inequality.001','solution',1,'test.alg.factor-quadratic','Factor','\((x - 2)(x + 2) < 0\).');
INSERT INTO "card_step" VALUES('test.quad.inequality.001','solution',2,'test.alg.quadratic-solve','Sign','the product is negative between the zeros, so \(-2 < x < 2\), that is \((-2, 2)\).');
INSERT INTO "card_step" VALUES('test.quad.vertex.001','solution',0,'test.alg.vertex','Set up','the vertex of \(y = (x - h)^2 + k\) is \((h, k)\).');
INSERT INTO "card_step" VALUES('test.quad.vertex.001','solution',1,'test.alg.vertex','Read off','\(h = 1\), \(k = 3\).');
INSERT INTO "card_step" VALUES('test.quad.parabola.001','solution',0,'test.alg.quadratic-solve','Set up','the zeros solve \(f(x) = 0\); the vertex of \(x^2 + k\) is \((0, k)\).');
INSERT INTO "card_step" VALUES('test.quad.parabola.001','solution',1,'test.alg.factor-quadratic','Factor','\((x - 1)(x + 1) = 0\), so \(x = -1\) or \(x = 1\).');
INSERT INTO "card_step" VALUES('test.quad.parabola.001','solution',2,'test.alg.vertex','Vertex','\((0, -1)\). The coefficient of \(x^2\) is positive, so the graph opens up.');
INSERT INTO "card_step" VALUES('test.quad.factor-error.001','solution',1,'test.alg.factor-quadratic','Recognize','\(x^2 - 9 = x^2 - 3^2\).');
INSERT INTO "card_step" VALUES('test.quad.factor-error.001','solution',2,'test.alg.factor-quadratic','Factor','\(x^2 - 9 = (x - 3)(x + 3)\).');
INSERT INTO "card_step" VALUES('test.quad.factor-error.001','shown-work',1,'test.alg.factor-quadratic','Recognize','\(x^2 - 9 = x^2 - 3^2\) is a difference of squares.');
INSERT INTO "card_step" VALUES('test.quad.factor-error.001','shown-work',2,'test.alg.factor-quadratic','Factor','\(x^2 - 9 = (x - 3)^2\).');
INSERT INTO "card_step" VALUES('test.quad.method.001','solution',0,'test.alg.choose-quadratic-method','Set up','no two integers multiply to \(-1\) and add to \(1\), and there is an \(x\) term, so use the quadratic formula.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2df55cce','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2df55cce','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 2\right) \left(x - 1\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2df55cce','solution',2,'test.alg.linear-solve','Solve','\(x = 1\) or \(x = 2\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--596e4ddd','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--596e4ddd','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 3\right) \left(x - 1\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--596e4ddd','solution',2,'test.alg.linear-solve','Solve','\(x = 1\) or \(x = 3\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2cc9b5f4','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2cc9b5f4','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 4\right) \left(x - 1\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2cc9b5f4','solution',2,'test.alg.linear-solve','Solve','\(x = 1\) or \(x = 4\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c159b5f5','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c159b5f5','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 5\right) \left(x - 1\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c159b5f5','solution',2,'test.alg.linear-solve','Solve','\(x = 1\) or \(x = 5\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--1a75df75','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--1a75df75','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 3\right) \left(x - 2\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--1a75df75','solution',2,'test.alg.linear-solve','Solve','\(x = 2\) or \(x = 3\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c10ea89c','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c10ea89c','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 4\right) \left(x - 2\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c10ea89c','solution',2,'test.alg.linear-solve','Solve','\(x = 2\) or \(x = 4\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c6c333ee','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c6c333ee','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 5\right) \left(x - 2\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--c6c333ee','solution',2,'test.alg.linear-solve','Solve','\(x = 2\) or \(x = 5\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--ed9f7034','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--ed9f7034','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 4\right) \left(x - 3\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--ed9f7034','solution',2,'test.alg.linear-solve','Solve','\(x = 3\) or \(x = 4\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--bc4130a6','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--bc4130a6','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 5\right) \left(x - 3\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--bc4130a6','solution',2,'test.alg.linear-solve','Solve','\(x = 3\) or \(x = 5\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2b5330ff','solution',0,'test.alg.quadratic-solve','Set up','factor, then set each factor equal to zero.');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2b5330ff','solution',1,'test.alg.factor-quadratic','Factor','\(\left(x - 5\right) \left(x - 4\right) = 0\).');
INSERT INTO "card_step" VALUES('test.quad.solve.t01--2b5330ff','solution',2,'test.alg.linear-solve','Solve','\(x = 4\) or \(x = 5\).');
INSERT INTO "card_step" VALUES('test.deriv.power.001','solution',0,'test.calc.power-rule','Set up','differentiate term by term with the power rule.');
INSERT INTO "card_step" VALUES('test.deriv.power.001','solution',1,'test.calc.power-rule','First term','\((x^3)'' = 3x^2\).');
INSERT INTO "card_step" VALUES('test.deriv.power.001','solution',2,'test.calc.power-rule','Second term','\((2x)'' = 2\), so \(f''(x) = 3x^2 + 2\).');
INSERT INTO "card_step" VALUES('test.deriv.power.001','alternative',1,'test.calc.limits','Limit definition','\(\frac{f(x + h) - f(x)}{h} = 3x^2 + 3xh + h^2 + 2\), which tends to \(3x^2 + 2\) as \(h \to 0\).');
INSERT INTO "card_step" VALUES('test.deriv.antiderivative.001','solution',0,'test.calc.power-rule','Set up','run the power rule backwards.');
INSERT INTO "card_step" VALUES('test.deriv.antiderivative.001','solution',1,'test.calc.power-rule','Integrate','raise the exponent by one and divide by the new exponent: \(\frac{3x^3}{3} + C = x^3 + C\).');
INSERT INTO "card_step" VALUES('test.deriv.limit-dne.001','solution',0,'test.calc.limits','Set up','compare the one-sided limits.');
INSERT INTO "card_step" VALUES('test.deriv.limit-dne.001','solution',1,'test.calc.limits','One-sided limits','the quotient is \(1\) for \(x > 0\) and \(-1\) for \(x < 0\), so the limit does not exist.');
INSERT INTO "card_step" VALUES('test.deriv.limit-inf.001','solution',0,'test.calc.limits','Set up','look at the size of the quotient near \(0\).');
INSERT INTO "card_step" VALUES('test.deriv.limit-inf.001','solution',1,'test.calc.limits','Grow','\(x^2 > 0\) shrinks to \(0\), so \(\frac{1}{x^2}\) grows without bound from both sides.');
INSERT INTO "card_step" VALUES('test.deriv.critical-choice.001','solution',0,'test.calc.critical-points','Set up','critical numbers are where \(f''\) is zero or undefined.');
INSERT INTO "card_step" VALUES('test.deriv.critical-choice.001','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 3x^2 - 3\).');
INSERT INTO "card_step" VALUES('test.deriv.critical-choice.001','solution',2,'test.alg.quadratic-solve','Solve','\(3x^2 - 3 = 0\) gives \(x = -1\) or \(x = 1\).');
INSERT INTO "card_step" VALUES('test.deriv.example.001','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.example.001','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 5 \cdot 4x^3 = 20x^3\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--81b9036a','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--81b9036a','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 2 \cdot 3 x^{2} = 6 x^{2}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--3c194862','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--3c194862','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 2 \cdot 4 x^{3} = 8 x^{3}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--47c7fdb3','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--47c7fdb3','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 2 \cdot 5 x^{4} = 10 x^{4}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--6e8e8334','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--6e8e8334','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 2 \cdot 6 x^{5} = 12 x^{5}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--f4d53d2f','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--f4d53d2f','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 3 \cdot 3 x^{2} = 9 x^{2}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--e5616d60','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--e5616d60','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 3 \cdot 4 x^{3} = 12 x^{3}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--dc654051','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--dc654051','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 3 \cdot 5 x^{4} = 15 x^{4}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--58410edd','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--58410edd','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 3 \cdot 6 x^{5} = 18 x^{5}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--f0ebd192','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--f0ebd192','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 4 \cdot 3 x^{2} = 12 x^{2}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--004a5723','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--004a5723','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 4 \cdot 4 x^{3} = 16 x^{3}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--5ab21fc7','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--5ab21fc7','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 4 \cdot 5 x^{4} = 20 x^{4}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--2b29a1e7','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--2b29a1e7','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 4 \cdot 6 x^{5} = 24 x^{5}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--d4f94fc3','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--d4f94fc3','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 5 \cdot 3 x^{2} = 15 x^{2}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--cc198f9a','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--cc198f9a','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 5 \cdot 4 x^{3} = 20 x^{3}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--ea43e0dd','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--ea43e0dd','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 5 \cdot 5 x^{4} = 25 x^{4}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--1eae4c84','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--1eae4c84','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 5 \cdot 6 x^{5} = 30 x^{5}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--482c054b','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--482c054b','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 6 \cdot 3 x^{2} = 18 x^{2}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--d7659828','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--d7659828','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 6 \cdot 4 x^{3} = 24 x^{3}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--23d78e95','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--23d78e95','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 6 \cdot 5 x^{4} = 30 x^{4}\).');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--4bc36255','solution',0,'test.calc.power-rule','Set up','\((x^n)'' = n x^{n - 1}\), and constant factors stay.');
INSERT INTO "card_step" VALUES('test.deriv.power.t01--4bc36255','solution',1,'test.calc.power-rule','Differentiate','\(f''(x) = 6 \cdot 6 x^{5} = 36 x^{5}\).');
CREATE TABLE card_use (
  card_id  TEXT NOT NULL REFERENCES card(id),
  ord      INTEGER NOT NULL,
  skill_id TEXT NOT NULL,
  PRIMARY KEY (card_id, skill_id)
) STRICT;
INSERT INTO "card_use" VALUES('test.linear.solve.001',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.check.001',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.vector.001',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.explain.001',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.example.001',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--cc2ed4ba',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--d97e7279',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--6f278589',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--26f719ef',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--0587c9e2',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--1ab13269',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--13560d01',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--50634d10',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--37400c93',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--9b0c38fc',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--b9da0963',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--5f15055c',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--4f9e0ebf',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--54249344',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--554661df',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--50739601',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--39e7fcc6',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--e317d741',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--e810f6eb',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--77333035',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--37c8e675',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--b0a4fd9d',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--e13e7c59',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--f71a42ce',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--92bd2908',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--90e4c2c1',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--b02ca601',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--4891c9ae',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--98adbc27',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--2c4aa87f',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--b51261b3',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--04908abe',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--1952c899',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--d0a12ae2',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--f396ddce',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--2f2a7b6c',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--be7dfaa1',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--eb6df22e',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--8a986255',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--6cda46b0',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--b70a4440',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--c44412ae',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--9123e24b',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--f5d4bda3',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--e45b948b',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--9e4dba50',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--978765ef',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.linear.solve.t01--765b7d2d',0,'test.alg.arithmetic');
INSERT INTO "card_use" VALUES('test.quad.solve.001',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.001',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.inequality.001',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.parabola.001',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.parabola.001',1,'test.alg.vertex');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2df55cce',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2df55cce',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--596e4ddd',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--596e4ddd',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2cc9b5f4',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2cc9b5f4',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c159b5f5',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c159b5f5',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--1a75df75',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--1a75df75',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c10ea89c',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c10ea89c',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c6c333ee',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--c6c333ee',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--ed9f7034',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--ed9f7034',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--bc4130a6',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--bc4130a6',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2b5330ff',0,'test.alg.factor-quadratic');
INSERT INTO "card_use" VALUES('test.quad.solve.t01--2b5330ff',1,'test.alg.linear-solve');
INSERT INTO "card_use" VALUES('test.deriv.power.001',0,'test.calc.limits');
INSERT INTO "card_use" VALUES('test.deriv.critical-choice.001',0,'test.calc.power-rule');
INSERT INTO "card_use" VALUES('test.deriv.critical-choice.001',1,'test.alg.quadratic-solve');
CREATE TABLE card_wrong (
  card_id  TEXT NOT NULL REFERENCES card(id),
  part     TEXT NOT NULL DEFAULT '',
  ord      INTEGER NOT NULL,
  answer   TEXT NOT NULL,
  feedback TEXT,
  step     INTEGER CHECK (step IS NULL OR step >= 0),
  PRIMARY KEY (card_id, part, ord)
) STRICT;
INSERT INTO "card_wrong" VALUES('test.linear.solve.001','',0,'25/3','You added 5 to both sides instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.line.001','',0,'y = x + 2','The slope multiplies x, and the intercept is the constant.',1);
INSERT INTO "card_wrong" VALUES('test.linear.simplify.001','',0,'x + 3','Multiply both terms in the parentheses by 2.',1);
INSERT INTO "card_wrong" VALUES('test.linear.slope-name.001','',0,'intercept','The intercept is b, where the line crosses the y-axis.',NULL);
INSERT INTO "card_wrong" VALUES('test.linear.vector.001','',0,'<4, 3>','Write the x-component first.',1);
INSERT INTO "card_wrong" VALUES('test.linear.vector.001','',1,'<-3, -4>','Subtract the start from the end.',1);
INSERT INTO "card_wrong" VALUES('test.linear.matrix.001','',0,'[[1, 3], [2, 4]]','Each row holds the coefficients of one equation.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--cc2ed4ba','',0,'11/2','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--d97e7279','',0,'21/2','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--6f278589','',0,'6','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--26f719ef','',0,'11','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--0587c9e2','',0,'13/2','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--1ab13269','',0,'23/2','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--13560d01','',0,'7','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--50634d10','',0,'12','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--37400c93','',0,'15/2','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--9b0c38fc','',0,'25/2','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--b9da0963','',0,'8','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--5f15055c','',0,'13','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--4f9e0ebf','',0,'11/3','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--54249344','',0,'7','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--554661df','',0,'4','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--50739601','',0,'22/3','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--39e7fcc6','',0,'13/3','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--e317d741','',0,'23/3','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--e810f6eb','',0,'14/3','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--77333035','',0,'8','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--37c8e675','',0,'5','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--b0a4fd9d','',0,'25/3','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--e13e7c59','',0,'16/3','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--f71a42ce','',0,'26/3','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--92bd2908','',0,'11/4','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--90e4c2c1','',0,'21/4','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--b02ca601','',0,'3','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--4891c9ae','',0,'11/2','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--98adbc27','',0,'13/4','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--2c4aa87f','',0,'23/4','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--b51261b3','',0,'7/2','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--04908abe','',0,'6','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--1952c899','',0,'15/4','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--d0a12ae2','',0,'25/4','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--f396ddce','',0,'4','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--2f2a7b6c','',0,'13/2','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--be7dfaa1','',0,'11/5','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--eb6df22e','',0,'21/5','You added 1 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--8a986255','',0,'12/5','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--6cda46b0','',0,'22/5','You added 2 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--b70a4440','',0,'13/5','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--c44412ae','',0,'23/5','You added 3 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--9123e24b','',0,'14/5','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--f5d4bda3','',0,'24/5','You added 4 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--e45b948b','',0,'3','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--9e4dba50','',0,'5','You added 5 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--978765ef','',0,'16/5','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.linear.solve.t01--765b7d2d','',0,'26/5','You added 6 instead of subtracting it.',1);
INSERT INTO "card_wrong" VALUES('test.quad.solve.001','',0,'-2, -3','(x - 2)(x - 3) is zero at x = 2 and x = 3.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.001','',1,'2','There are two solutions.',2);
INSERT INTO "card_wrong" VALUES('test.quad.coefficients.001','',0,'2, 3, 7','Keep the sign: the middle term is -3x.',1);
INSERT INTO "card_wrong" VALUES('test.quad.coefficients.001','',1,'7, -3, 2','a goes with x^2, b with x, c is the constant.',1);
INSERT INTO "card_wrong" VALUES('test.quad.inequality.001','',0,'[-2, 2]','The inequality is strict, so the endpoints are not included.',2);
INSERT INTO "card_wrong" VALUES('test.quad.inequality.001','',1,'(-inf, -2) U (2, inf)','That is where x^2 - 4 is positive.',2);
INSERT INTO "card_wrong" VALUES('test.quad.vertex.001','',0,'(-1, 3)','In (x - h)^2 + k the vertex is (h, k), so h = 1.',1);
INSERT INTO "card_wrong" VALUES('test.quad.parabola.001','a',0,'1','There are two zeros.',1);
INSERT INTO "card_wrong" VALUES('test.quad.factor-error.001','',0,'x^2 - 9','Write it as a product of two factors.',2);
INSERT INTO "card_wrong" VALUES('test.quad.factor-error.001','',1,'(x - 3)^2','That is x^2 - 6x + 9.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--2df55cce','',0,'-1, -2','The zeros of (x - 1)(x - 2) are 1 and 2.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--596e4ddd','',0,'-1, -3','The zeros of (x - 1)(x - 3) are 1 and 3.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--2cc9b5f4','',0,'-1, -4','The zeros of (x - 1)(x - 4) are 1 and 4.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--c159b5f5','',0,'-1, -5','The zeros of (x - 1)(x - 5) are 1 and 5.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--1a75df75','',0,'-2, -3','The zeros of (x - 2)(x - 3) are 2 and 3.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--c10ea89c','',0,'-2, -4','The zeros of (x - 2)(x - 4) are 2 and 4.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--c6c333ee','',0,'-2, -5','The zeros of (x - 2)(x - 5) are 2 and 5.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--ed9f7034','',0,'-3, -4','The zeros of (x - 3)(x - 4) are 3 and 4.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--bc4130a6','',0,'-3, -5','The zeros of (x - 3)(x - 5) are 3 and 5.',2);
INSERT INTO "card_wrong" VALUES('test.quad.solve.t01--2b5330ff','',0,'-4, -5','The zeros of (x - 4)(x - 5) are 4 and 5.',2);
INSERT INTO "card_wrong" VALUES('test.deriv.power.001','',0,'3x^2','The derivative of 2x is 2, not 0.',2);
INSERT INTO "card_wrong" VALUES('test.deriv.power.001','',1,'x^2 + 2','Multiply by the old exponent.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.antiderivative.001','',0,'6x','That is the derivative, not an antiderivative.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.limit-dne.001','',0,'1','That is the limit from the right only.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.limit-dne.001','',1,'-1','That is the limit from the left only.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.limit-inf.001','',0,'DNE','The quotient grows without bound from both sides: write inf.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--81b9036a','',0,'2*x^2','Multiply by the exponent 3 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--81b9036a','',1,'6*x^3','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--3c194862','',0,'2*x^3','Multiply by the exponent 4 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--3c194862','',1,'8*x^4','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--47c7fdb3','',0,'2*x^4','Multiply by the exponent 5 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--47c7fdb3','',1,'10*x^5','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--6e8e8334','',0,'2*x^5','Multiply by the exponent 6 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--6e8e8334','',1,'12*x^6','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--f4d53d2f','',0,'3*x^2','Multiply by the exponent 3 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--f4d53d2f','',1,'9*x^3','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--e5616d60','',0,'3*x^3','Multiply by the exponent 4 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--e5616d60','',1,'12*x^4','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--dc654051','',0,'3*x^4','Multiply by the exponent 5 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--dc654051','',1,'15*x^5','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--58410edd','',0,'3*x^5','Multiply by the exponent 6 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--58410edd','',1,'18*x^6','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--f0ebd192','',0,'4*x^2','Multiply by the exponent 3 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--f0ebd192','',1,'12*x^3','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--004a5723','',0,'4*x^3','Multiply by the exponent 4 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--004a5723','',1,'16*x^4','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--5ab21fc7','',0,'4*x^4','Multiply by the exponent 5 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--5ab21fc7','',1,'20*x^5','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--2b29a1e7','',0,'4*x^5','Multiply by the exponent 6 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--2b29a1e7','',1,'24*x^6','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--d4f94fc3','',0,'5*x^2','Multiply by the exponent 3 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--d4f94fc3','',1,'15*x^3','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--cc198f9a','',0,'5*x^3','Multiply by the exponent 4 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--cc198f9a','',1,'20*x^4','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--ea43e0dd','',0,'5*x^4','Multiply by the exponent 5 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--ea43e0dd','',1,'25*x^5','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--1eae4c84','',0,'5*x^5','Multiply by the exponent 6 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--1eae4c84','',1,'30*x^6','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--482c054b','',0,'6*x^2','Multiply by the exponent 3 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--482c054b','',1,'18*x^3','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--d7659828','',0,'6*x^3','Multiply by the exponent 4 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--d7659828','',1,'24*x^4','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--23d78e95','',0,'6*x^4','Multiply by the exponent 5 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--23d78e95','',1,'30*x^5','Lower the exponent by one.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--4bc36255','',0,'6*x^5','Multiply by the exponent 6 too.',1);
INSERT INTO "card_wrong" VALUES('test.deriv.power.t01--4bc36255','',1,'36*x^6','Lower the exponent by one.',1);
CREATE TABLE course (
  id    TEXT PRIMARY KEY NOT NULL,
  title TEXT NOT NULL,
  ord   INTEGER NOT NULL DEFAULT 0
) STRICT;
INSERT INTO "course" VALUES('Test Course','Test Course',0);
CREATE TABLE media (
  name TEXT PRIMARY KEY NOT NULL,
  data BLOB NOT NULL
) STRICT;
INSERT INTO "media" VALUES('media/parabola.svg',X'3C73766720786D6C6E733D22687474703A2F2F7777772E77332E6F72672F323030302F737667222076696577426F783D222D33202D3320362036222077696474683D2232343022206865696768743D223234302220726F6C653D22696D672220617269612D6C6162656C3D225468652070617261626F6C612079203D20785E32202D2031223E0A20203C67207472616E73666F726D3D227363616C6528312C2D3129222066696C6C3D226E6F6E6522207374726F6B652D77696474683D22302E3034223E0A202020203C6C696E652078313D222D33222079313D2230222078323D2233222079323D223022207374726F6B653D2223383838222F3E0A202020203C6C696E652078313D2230222079313D222D33222078323D2230222079323D223322207374726F6B653D2223383838222F3E0A202020203C7061746820643D224D202D32203320512030202D352032203322207374726F6B653D2223323536336562222F3E0A20203C2F673E0A3C2F7376673E0A');
CREATE TABLE pack (
  singleton    INTEGER PRIMARY KEY NOT NULL CHECK (singleton = 1),
  id           TEXT NOT NULL,
  title        TEXT NOT NULL,
  version      TEXT NOT NULL,
  format       INTEGER NOT NULL,
  built_at     INTEGER NOT NULL,
  content_hash TEXT NOT NULL DEFAULT ''
) STRICT;
INSERT INTO "pack" VALUES(1,'test','Test pack','1.0.0',1,1,'sha256:47edd6bf695541b3f3e89e3d680e5e53803702e01576fb904a40164d3c437fac');
CREATE TABLE section (
  id           TEXT PRIMARY KEY NOT NULL,
  unit_id      TEXT NOT NULL,
  title        TEXT NOT NULL,
  ord          INTEGER NOT NULL DEFAULT 0,
  textbook_ref TEXT
) STRICT;
INSERT INTO "section" VALUES('Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra','1.1 Linear Equations',0,NULL);
INSERT INTO "section" VALUES('Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra','1.2 Quadratics',1,NULL);
INSERT INTO "section" VALUES('Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus','2.1 Derivatives',2,NULL);
CREATE TABLE skill (
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
INSERT INTO "skill" VALUES('test.alg.arithmetic','Simplify arithmetic and expressions','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','Test Book 1.1',0,1,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.linear-solve','Solve a linear equation','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','Test Book 1.1',0,1,2,NULL);
INSERT INTO "skill" VALUES('test.alg.line-equation','Write the equation of a line','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations','Test Book 1.2',0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.vectors','Write a vector in component form','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations',NULL,0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.matrices','Write the coefficient matrix of a system','Test Course::1 Algebra::1.1 Linear Equations','Test Course::1 Algebra::1.1 Linear Equations',NULL,0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.factor-quadratic','Factor a quadratic','Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','Test Book 2.1',0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.quadratic-formula','Use the quadratic formula','Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics','Test Book 2.2',0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.quadratic-solve','Solve a quadratic equation or inequality','Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics',NULL,0,0,3,NULL);
INSERT INTO "skill" VALUES('test.alg.vertex','Find the vertex of a parabola','Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics',NULL,0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.alg.choose-quadratic-method','Choose a method for a quadratic equation','Test Course::1 Algebra::1.2 Quadratics','Test Course::1 Algebra::1.2 Quadratics',NULL,1,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.calc.power-rule','Differentiate with the power rule','Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives',NULL,0,1,NULL,NULL);
INSERT INTO "skill" VALUES('test.calc.limits','Find a limit','Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives',NULL,0,0,NULL,NULL);
INSERT INTO "skill" VALUES('test.calc.critical-points','Find critical numbers','Test Course::2 Calculus::2.1 Derivatives','Test Course::2 Calculus::2.1 Derivatives',NULL,0,0,NULL,'Critical numbers are where \(f''\) is zero or undefined.');
CREATE TABLE skill_edge (
  skill_id TEXT NOT NULL REFERENCES skill(id),
  kind     TEXT NOT NULL CHECK (kind IN ('requires', 'encompasses', 'confusable')),
  other_id TEXT NOT NULL,
  ord      INTEGER NOT NULL DEFAULT 0,
  weight   REAL CHECK ((kind = 'encompasses') = (weight IS NOT NULL)),
  PRIMARY KEY (skill_id, kind, other_id),
  CHECK (skill_id <> other_id)
) STRICT;
INSERT INTO "skill_edge" VALUES('test.alg.linear-solve','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.linear-solve','confusable','test.alg.line-equation',1,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.line-equation','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.line-equation','confusable','test.alg.linear-solve',1,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.vectors','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.matrices','requires','test.alg.linear-solve',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.factor-quadratic','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.factor-quadratic','confusable','test.alg.quadratic-formula',1,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-formula','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-formula','confusable','test.alg.factor-quadratic',1,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-solve','requires','test.alg.factor-quadratic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-solve','requires','test.alg.linear-solve',1,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-solve','encompasses','test.alg.factor-quadratic',2,0.5);
INSERT INTO "skill_edge" VALUES('test.alg.quadratic-solve','encompasses','test.alg.linear-solve',3,0.25);
INSERT INTO "skill_edge" VALUES('test.alg.vertex','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.choose-quadratic-method','requires','test.alg.factor-quadratic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.alg.choose-quadratic-method','requires','test.alg.quadratic-formula',1,NULL);
INSERT INTO "skill_edge" VALUES('test.calc.power-rule','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.calc.limits','requires','test.alg.arithmetic',0,NULL);
INSERT INTO "skill_edge" VALUES('test.calc.critical-points','requires','test.calc.power-rule',0,NULL);
INSERT INTO "skill_edge" VALUES('test.calc.critical-points','requires','test.alg.quadratic-solve',1,NULL);
INSERT INTO "skill_edge" VALUES('test.calc.critical-points','encompasses','test.calc.power-rule',2,1.0);
CREATE TABLE unit (
  id        TEXT PRIMARY KEY NOT NULL,
  course_id TEXT NOT NULL,
  title     TEXT NOT NULL,
  ord       INTEGER NOT NULL DEFAULT 0
) STRICT;
INSERT INTO "unit" VALUES('Test Course::1 Algebra','Test Course','1 Algebra',0);
INSERT INTO "unit" VALUES('Test Course::2 Calculus','Test Course','2 Calculus',1);
CREATE INDEX skill_section ON skill(section_id);
CREATE INDEX skill_edge_other ON skill_edge(other_id, kind);
CREATE INDEX card_skill ON card(skill_id, tier);
CREATE INDEX card_template ON card(template_id);
CREATE INDEX card_section ON card(section_id);
CREATE INDEX card_use_skill ON card_use(skill_id);
CREATE INDEX card_step_skill ON card_step(skill_id);
COMMIT;
