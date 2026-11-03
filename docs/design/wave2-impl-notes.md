# Wave 2 implementation notes (W1: data, core/practice, session, bridge, removals)

- Engineer W1, 2026-11-02. Spec: `docs/design/wave2-integration.md` v1.2, sections 2, 3, 4 and the
  Python side of 5 and 6. Background: `docs/design/student-model.md` (3, 4, 8), `docs/design/wave2-planner.md`
  (W3, in parallel), `docs/spec.md`.
- Work goes in the spec's section 7 order, one commit per phase, each with `scripts/check.sh fast` green.
- This file is the running log: what each phase did, each choice the spec left open and why, and
  each place where the spec proved wrong in the code (with the closest sound version taken). A
  successor resumes from the **Status** list.

## Status

| Phase | What | State |
|---|---|---|
| 1 | user.db v3 migration and storage helpers | done (d31ba65) |
| 2 | `core/practice` (catalog, observations, engine) with tests | done |
| 3 | the session switch (`core/queue/session.py`) | next |
| 4 | the bridge (`app/api.py`) | |
| 5 | removals | |

## Phase 1: user.db v3 and storage helpers

**Delivered**
- `core/storage/sql/migrate_user_v3.sql` (frozen) and the `_v3_practice` step in `schema.py`;
  `USER_SCHEMA_VERSION = 3`.
  - `attempt` gains `role, milestone, missed, plan_p, ladder, sitting, learner_version, valid_minutes`,
    appended in that order, each with a CHECK (role and milestone enums, `missed` 0/1, `plan_p` in
    [0, 1], `ladder` 0-2, `valid_minutes` > 0).
  - The `attempt_no_update` trigger is dropped and re-created with the new columns, so the log stays
    append-only (the existing test that every column is listed covers it).
  - `course_settings` and `learner_params` as section 2 lists them.
- `core/model.py`: the `Attempt` fields in column order; new records `CourseSetup` (table
  `course_settings`) and `LearnerParams` (table `learner_params`), registered in `core/storage/rows.py`.
- `UserStore`: `set_course_setup`, `course_setup`, `course_setups`, `learner_params(version=None)`
  (the current one by default), `learner_param_history`, `add_learner_params` (a current version
  clears the old current flag in the same transaction; an existing version is refused). For the
  learner cache: `attempts(after_id=...)` (the rows a log has gained) and `attempt_log_key()`
  (the newest non-voided id and the voided count). `PackStore.course_sources()`: the pack each
  course comes from, for its pace standard.
- Tests:
  - `tests/storage/fixtures/user_v2.sql`, a frozen v2 database written once by the v2 code
    (commit 18fd93b) through the real StudyService on the Test pack. Its builder is
    `tests/storage/v2_user.py`. It holds right and wrong first tries, wrong-then-right, give-ups, a
    hint, shown examples (including a tier-1 problem shown solved), flashcards and clozes, an undo
    (voided rows), a practice test with a multi-part problem, focused practice, two course goals and
    two exams.
  - `tests/storage/test_migration_v3.py`: every row and value kept (`expected_v3`), migrating again
    does nothing, the new columns are append-only, the course start carries over, old attempts
    read back, the last v2 answer can still be undone, v3 attempts store the planner's columns,
    parameter versions keep one current row and never change, setups are range-checked; crashes at
    every instruction of the step leave v2 or a complete v3; SIGKILLs at random moments; the v2 code
    path, and the released v2 code (git archive of 18fd93b), refuse a v3 file untouched.
  - `tests/storage/test_migration_v2.py` and `test_migrations.py` now follow a v1 profile through both
    steps: a v1 file opened by today's app is v3, so the v2 expectations pass through `expected_v3`,
    and each pre-migration backup must be exactly the state before its step (v1 before v2, a complete
    v2 before v3).

**Choices the spec left open**
- *Record names.* `CourseSetup` for `course_settings` (the page is "Course setup"), so it never
  shadows `core.plan.types.CourseSettings`, which `core/practice` builds from it. `LearnerParams` for
  `learner_params`.
- *The goal date carries over too.* The spec says `course_goal.starts_on` seeds `start`. The old
  `goal_date` meant "after this day the course drops to Keep" (LIB-8), which is exactly the new
  `end_day` (design 4.1, "LIB-8 kept"), so it seeds `end_day`. A row is written for each goal with
  either date, stamped with the goal's own `updated_at`, so the step is deterministic. Goals A, B
  and custom retention are not carried: they were FSRS desired retention, not first-try accuracy.
- *`learner_params` is append-only* except its `current` flag (triggers like the other logs), with a
  partial unique index for "exactly one current row".
- *The new columns are checked* (enums, ranges) like every v1 column.

**Spec problems found**
- `course_settings.course_id ... REFERENCES the course`: pack courses live in attached read-only
  pack databases, and SQLite foreign keys cannot reference a table in another database (and own
  courses are in `user_course`). No FK is declared; the bridge checks the id against the loaded
  courses when it writes a setup.

**Crash tests (coordinator request: make the kill aiming robust, keep the safety assertions)**
- `tests/storage/test_kill_loop.py::test_migrations_survive_sigkill` failed on the Mac (9 of 40 kills
  inside an open, 13 needed): the kills were aimed from the median of 3 probe opens, measured from when
  the parent read the child's first line, and warm opens are much faster than the probes (here 0.17 s
  probes, 0.05 s warm).
- Now:
  - kills are aimed from the child's own start stamp (`after_begin`, its monotonic clock, which is
    the machine's on Linux and macOS, with a fallback to a plain delay if it ever is not);
  - every round whose open finished first measures the span again, and the aim is the median of the
    last five measurements;
  - rounds continue, up to three times the planned 40, until a third land inside, and every round is
    checked in full whatever happened.
  - The checks are stronger than before, as v3 makes a v1 open two steps: after a kill the file is
    exactly the state of one version (v1, v2 or v3, each computed once from the fixture), every
    finished backup is exactly the state before its step, and the next open ends at exactly the v3
    state. Here: 38 of 40 inside, versions found v1 27, v2 9, v3 4.
- `tests/storage/fault_child.py`: the v2-only modes became `vN-count`, `vN-die`, `vN-slow` for any
  step. The progress handler is now cleared when the next step starts. Before, it stayed on the
  connection and counted the v3 step too, so "kills inside v2" landed in v3. The v3 sweep includes
  the instructions just before and after the commit, since the step is about 136,000 instructions and
  a 1/40 stride skipped them.

## Phase 2: `core/practice`

**Delivered**
- `catalog.py`: `build_catalog(storage)` gives the `ComponentInfo` catalog, a `ProblemSpec` per
  gradable problem (`card` or `card#part`), each course's `core.plan.Course` (skills in course
  order with requires, confusable pairs, example cards, pools, the background skills it needs and
  its pack's pace standard), skill names, decks and textbook pointers. `catalog_key` (pack content
  hashes and the own-content counts) decides when to rebuild.
- `observations.py`: `observations_of(attempt, catalog)`, one row's observations, per section 3.
- `engine.py`: `PracticeEngine` with `state`, `observations`, `record`, `params`, `reset_params`,
  `settings`, `certifier`, `plan_day`, `next_item`, `statuses`, `certified`, `calibration`,
  `refit_due`, `refit`, `last_refit`; `PlannerModel` (the `core.plan.Predictor` view of
  `StudentModel`), `merge` (several courses), `plan_settings`, `params_json`/`params_from_json`,
  `work_item` (builds a `WorkItem` with whatever fields this `core.plan` has).
- Tests in `tests/practice/` (32): the catalog on a pack with a pace standard and without one;
  observations from synthetic v3 rows and from the frozen v2 history read through the real Test
  pack (checked against an independent reading of the log); C3 after incremental updates and after
  an undo; `record`; the prior written once; resets; refits recorded and adopted only on evidence;
  a refit never overriding a reset made meanwhile; plans, statuses and the course merge; settings
  and exams; calibration bins; concurrent readers.

**Choices the spec left open**
- *Background components* follow the spec: an `alg.`, `trig.` or `pre.` id, or a skill in no
  course's sections (Calc I keeps its precalculus skills in its own "0 Precalculus" sections, so the
  prefix is what marks them). The prefixes are one named constant, `BACKGROUND_PREFIXES`, the
  skills files' convention. AGENTS rule 12 asks for no subject-specific code, so a `background: yes`
  key in the skills file format would be the general form (the coordinator may want that later).
  A component has one flag for the whole profile; a Calc I skill used by Calc II is a course
  component of Calc I, and the planner, which checks `course_id`, treats it as background there.
- *Pools hold `problem` cards only.* Find-the-error and which-method cards were served by the
  diagnosis flow (ENG-16, ADR-0010), which is removed.
- *Multi-part cards.* A part with its own `skill` is a one-component problem of that skill (the
  solution's steps belong to the card, and such a part reports to its own skill, as
  `PartOutcome` did). A part without one keeps the card's components less the other parts' own
  skills. Each part's T* is `standard_minutes(part, card=...)`; its `steps` is its share of the
  card's.
- *Course order* inside a section: prerequisites first, then id. Packs keep no file order.
- *A course's background skills*: those its skills require and those in its own sections, each with
  its pool (the planner grows a struggling skill's background prerequisites).
- **(owner)** *A pack without pace data* (the Test and Tutorial packs, older packs, own courses)
  gets a flat standard: every section at zero hours, so the whole course is introduced on its
  anchor day (with an alignment, the sections before it are assumed learned, as usual). Such a
  course contributes no standard hours, so `hours_basis` is `none` until there is history.
- *`record(attempt_id)` instead of `record(observation)`.* The state is a pure function of the log
  (C3), so after the session's transaction commits, the engine reads the committed row back from the
  log and returns the updates of that row's first tries. Nothing can be recorded that the log does
  not hold, and the session, undo and every other writer go through the same path.
- *The cache key* is the spec's (newest non-voided id, voided count, parameter version) plus the
  catalog key and the study-day clock (time zone, rollover hour). New rows whose order falls before
  the last observation, which a clock set back could give, replay instead of updating.
- *Suspended and reported cards* are passed to the planner as `retired` on each call, so marking a
  card never rebuilds the catalog.
- *Certifier priors* are taken at the first use of the study day; the certifier is rebuilt after a
  replay, a settings change or a change of the unavailable cards, and gains each new first try
  through `Certifier.add`.
- *Old rows* (before v3): a verdict `shown` row is a worked example or a tier-1 problem shown solved
  (a non-final row with `attempt_number` 1), never a try; practice-test problems never answered are
  not observations; a hint before answering makes a first try aided (design 3.4); a self-graded first
  try is correct by its strict label (`extra.strict_ok`, else a Good rating); `minutes` comes from
  `extra.speed_ms` (TIME-4's speed time, solve time plus the typing allowance, capped), which the old
  engine stored on every timed problem, under the same validity rules, rather than raw `active_ms`.
  New rows store the same quantity in `valid_minutes`.
- *Parameter versions.* Each row has its own version: the prior is `prior`, a reset is
  `reset-<time>`, a refit uses its fitted version (`map-<hash>`), suffixed `.2`, `.3` if that name
  exists. A refit that is not adopted records the candidate (not current) with its report, so Model
  shows what was tried. A version made current while a refit ran (a reset) wins: the refit is
  recorded but not adopted. The report keeps the log's size and last attempt id, which `refit_due`
  reads for "grown by half" and the drift check over the predictions since.
- *Calibration* bins the cached update records, which are the replay under the current parameters
  (every new version replays). Gap bins: first, under 1 day, 1-7, 8-30, over 30 days since the main
  skill's previous first try. Component count: course components only, at least 1. (Phase 3: the
  labels became plain words, which the Model page shows as sent: "Tier 1", "First practice",
  "1 to 7 days", "2 skills", ...)
- *Several courses.* A course's "blocks" are its plan's items up to its last new-block item (checks
  placed inside that run stay there); the rest go round-robin. Hours to keep pace add up over the
  courses.

**Spec problems found**
- *"textbook ... from the deck and pack.json source"*: pack.json has no source field (id, title,
  version, license, description). The pointer comes from the skill's `textbook:` line, else its
  section's textbook reference, split at its last space into book and section
  ("OpenStax Calculus Vol 1 §4.3"), first reference of a list.
