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
| 1 | user.db v3 migration and storage helpers | done |
| 2 | `core/practice` (catalog, observations, engine) with tests | next |
| 3 | the session switch (`core/queue/session.py`) | |
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
