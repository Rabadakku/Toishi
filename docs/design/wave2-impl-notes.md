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
| 1 | user.db v3 migration and storage helpers | done (8d61631, was d31ba65 before the rebase) |
| 2 | `core/practice` (catalog, observations, engine) with tests | done (4f85961, was 1b00693) |
| 3 | the session switch (`core/queue/session.py`) | done |
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
    (the commit before the v3 migration) through the real StudyService on the Test pack. Its builder is
    `tests/storage/v2_user.py`. It holds right and wrong first tries, wrong-then-right, give-ups, a
    hint, shown examples (including a tier-1 problem shown solved), flashcards and clozes, an undo
    (voided rows), a practice test with a multi-part problem, focused practice, two course goals and
    two exams.
  - `tests/storage/test_migration_v3.py`: every row and value kept (`expected_v3`), migrating again
    does nothing, the new columns are append-only, the course start carries over, old attempts
    read back, the last v2 answer can still be undone, v3 attempts store the planner's columns,
    parameter versions keep one current row and never change, setups are range-checked; crashes at
    every instruction of the step leave v2 or a complete v3; SIGKILLs at random moments; the v2 code
    path, and the released v2 code (git archive of the commit before the v3 migration, found
    from the history), refuse a v3 file untouched.
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

## Phase 3: the session switch

**Rebase first.** The planner (W3) reached `main` by cherry-pick, on a history that was rewritten
(docs only: 18fd93b on this branch is 59748e2 there, with no common ancestor). The branch was moved
with `git rebase --onto main 18fd93b`, so it now sits on main's history and carries none of the old
one; phases 1 and 2 are 8d61631 and 4f85961. The `getattr` fallbacks for W3's fields became direct
reads.

**Delivered**
- `core/queue/session.py`, rewritten on `PracticeEngine` (section 4). Same public methods, less
  `hint`, `diagnose`, `set_lighter` and the vacation calls.
  - *Plans.* A daily session takes the problems `PracticeEngine.plan_day` leaves for today over the
    set-up courses (the items served so far come from the log, `served(day)`), with the day's
    flashcards placed between them; after every answer the rest of the day is planned again. A
    course with no setup has nothing planned ("Set up a course first").
  - *Answering.* Problems are retried freely (`attempts_allowed` 0). A wrong try is committed at
    once, as a non-final row, in one transaction with the session row, and the learner takes it if
    it was the first try. Its result is the verdict alone (status and the answer as read), "Not
    quite.", `can_retry`, `first_try_counted`; no checker message, known-wrong-answer feedback or
    step (coordinator rule). The matched feedback comes with the solution (Give up, or Show solution
    after a wrong first try); `matched_wrong` is logged on the row.
  - *Committing.* A final answer is held in the session row and committed on Continue, at the end,
    or (at its own time) when the study day rolls over, with the session row: the v3 columns, the
    planner's item whole in `extra.plan.work`, and `valid_minutes`. Then `PracticeEngine.record`,
    then the re-plan; `extra.replan` marks a re-plan a crash cut off, finished on resume.
  - *Undo* voids the presentation's rows (storage's exact undo) and restores the plan; the learner
    replays. *Dispute* and *report* void in one transaction with their record.
  - *Practice tests* (section 4): tier 3, the exam's scope, not served in 7 days, every scope skill
    once before any twice, timed optionally at the sum of T*, graded at the end through the same
    commit path; an unanswered problem is logged `unanswered` and is not evidence (C5).
  - *Extra practice*: tomorrow's planned growth and maintenance problems.
  - *Home* (`today()`): items by role, hours to keep pace and their basis, standard hours, behind
    and set-aside skills, sittings, the planner's notes, all in plain words.
  - *Sittings*: the sitting view (place, the block's limit, the block's clock so far), closed book.
- `core/queue/deck.py`: the day's flashcards (FSRS per card as before). A card on a skill of a
  set-up course is in play once the pace schedule introduces the skill; any other card follows the
  Library as before.
- `core/queue/items.py`: `Mode` is daily, extra, practice-test; the planner's roles and ladder rungs
  as tags, labels and "Why is this here?" sentences; `PlanItem.meta` (what the planner said).
- `core/queue/views.py`: the section 6 contract as agreed with the coordinator (below).
- `core/practice`: `words.py` (plain words); the engine gains `served`, `scheduled_skills`,
  `introduced`, `work_json` and `work_from_json`; calibration labels in plain words;
  `observations.py` counts `extra.solution_seen` as aided.
- `core/engine/service.py`: `auto_fit(kinds=...)`; the session fits only flashcard sets, then runs
  the learner's refit when due, on the same background thread, after `end()` and after a session
  that finished through Continue.
- `app/api.py`: `study_hint`, `study_diagnose`, `study_set_lighter` removed; `study_start` takes
  daily, extra or practice-test. `app/main.py`'s self-test sets the Test course up and gives up after
  a wrong try.
- Tests:
  - `tests/queue/test_session.py` (34) and `tests/queue/test_card_kinds.py` (12), most through
    `Script` (`tests/queue/helpers.py`), a stand-in for the planner that serves chosen problems;
    others through the real planner. They cover the commit path (one row per try, the held
    answer, the session row together, the planner's columns), undo on the verdict screen and after
    Continue with the learner replayed (C3), the day rolling over with a held answer, a crash
    between the commit and the re-plan, resume after a reopen, the exact round trip of served items,
    a wrong try's result carrying no feedback text, the sitting view and clock, the set-aside
    notice, plain-word notes, practice tests, extra practice, multi-part and self-graded problems,
    cloze blanks a day apart, flashcards (I5: leeches, both daily limits, the re-show with the
    same-day update, the flashcard parameters), find-the-error and which-method never served.
  - `tests/storage`: the study driver (no hints; wrong then right; wrong then give up), the kill
    loop (the Test course set up; the learner replays after every kill) and the DEV-9 state
    machine (a new invariant: the cached learner state equals a replay of the log, after every
    step; a C3 test with every answer in the same millisecond).
  - `tests/app`: the `studying` profile sets its course up; requests and refusals of the new
    flow; `test_restore`'s helper gives up after a wrong try (it retried forever otherwise).
  - Removed: the old engine's session tests (`tests/queue/test_session.py`,
    `test_hand_test_fixes.py`, `test_review_fixes.py`, `test_audit_queue.py`,
    `test_integration_wave8.py`, `test_simulation.py` with `sim.py`, `test_test_pack.py`, the old
    `test_card_kinds.py`). They asserted ratings, FSRS skill state, hints, lighter sets, the
    diagnosis flow, triage and vacations. What still holds is re-tested above. The pure pieces of
    the old planner (`share`, `triage`, `order`, `planner.build_plan`, `daylog`) keep their tests
    until phase 5 removes them.

**Choices the spec left open**
- *First try counted* (coordinator): true on the item's first submission and on a give-up before
  any answer. A multi-part submission counts when it held some part's first try.
- *Show solution*: a self-graded problem shows it before grading (that is how it is graded); any
  other problem only after a wrong first try, and then it ends the problem like Give up (the
  solution is help). Before any try: "Try it first. Give up shows the solution."
- *Undo never erases a miss.* A problem brought back by undo is aided (`extra.solution_seen`) when
  the undone answer's first try was not a clean success: wrong, given up, right only on a later
  try, a part so, or a worked example opened. After a clean first-try success it comes back clean,
  as before (the solution showed nothing the student lacked).
- *Worked examples* (and a problem the planner shows solved in their place) commit a final
  `shown` row carrying the planner's role, which the planner reads back as its block's; never an
  observation.
- *`valid_minutes`* (practice): TIME-4's speed time (solve time plus the typing allowance) capped
  at four times the problem's T* (3 to 30 minutes), for a correct, unaided, single-part, auto-graded
  first try outside an untimed session and not excluded by TIME-5. A self-graded or multi-part first
  try has none.
- **The sitting clock** (coordinator rule, after an external review: exams don't pause). For items
  with role `sitting` only:
  - the time is the wall clock from the problem shown to the submit, plus the typing allowance
    (`speed_time_ms`), with the usual cap: pauses and defocus count;
  - it is unknown (`valid_minutes` None, so the certifier calls the sitting void, with no 2-day
    wait) after a pause over 2 minutes or for the first answer after the Mac wakes; and, my
    choices, in an untimed session (TIME-6: nothing from it counts for pace) and when the app was
    closed and opened again with the problem on screen (`interrupted`, set at the first look after
    a launch: the clock ran while nobody could see it, so the sitting is void rather than failed);
  - practice items keep the rule above unchanged.
  - The banner's `block_elapsed_ms` is the sitting clock the block's earlier problems used (their
    counted time, else the bare wall clock), and `time_limit_ms` is the planner's `time_limit` (the
    block's sum of T*). types.ts says the page adds the running time of the problem on screen; for
    a sitting that running clock should not pause either (W2).
- *Closed book*: a sitting item shows no textbook line and refuses the worked example.
- *Practice tests reach the planner as served items* (W3's notes: they count toward a skill's
  streak, and the planner keeps them out of the day's cap by role). The session logs each with a
  planner item it builds (role practice-test).
- *Extra practice* items are logged without tomorrow's `day_items` stamp: the planner caps the day
  at the smallest stamp it is given, so tomorrow's would bind today's plan.
- *Served items come back whole* (W3: "pass each served WorkItem back exactly as returned"). Every
  attempt row of a planned item logs `work_json(item)`, every field with the problem by id, and
  `served()` rebuilds it with `work_from_json`; a test checks equality with the planner's first
  plan, also after a restart. Rows from before this build fall back to the field-by-field
  rebuild.
- **Plain words** (coordinator): the planner writes its notes for the log, so
  `core/practice/words.py` rewrites each: the feasibility formula becomes a sentence with
  percentages; a parenthesis of numbers is dropped ("not yet at pace for its sitting (predicted
  pass 0.41: ...)" becomes "not yet at pace for its sitting."); the set-aside note becomes the
  set-aside line; "See the textbook section." names the section; skill ids become names and deck
  ids section titles. Behind, set-aside and sitting lists hold names. Calibration bins: "Tier 1",
  "First practice", "1 to 7 days", "2 skills", ...
- *The set-aside notice* (coordinator): on the turn after the answer whose re-plan set a skill
  aside, `Turn.message` is "{name} is set aside for today. See {book} {section}." (the section
  carries its "§" from the pack).
- *The contract*, as agreed (coordinator):
  - dropped: `CardView.hint_count`, `ProblemView.hints_shown`, `SolutionView.needs_diagnosis` and
    `preselect_step`, `HintReveal`, `Diagnosis`, `TodayView.proposals` and `vacation`, `Proposal`,
    `GoalPreview`; and, now, `Turn.lighter` and `StartRequest.section_id`, `skill_id`,
    `weak_spots` (their modes are gone; a request naming them is read without them);
  - added: `ProblemView.role`, `plan_reason`, `textbook` (`TextbookView`, types.ts `Textbook`),
    `sitting` (`SittingView`, with `block_elapsed_ms`); `AttemptResult.can_retry`,
    `first_try_counted`; the `TodayView` fields of section 6 (`sittings` as `SittingLine`,
    types.ts `PlannedSitting`);
  - kept with a new meaning: `Summary.ready_today` is the problems today's plan still holds after
    the session (it ended before the plan did); `PartVerdictView.wrong_step` is filled only in a
    result that carries the solution.
- *Modes* are checked before anything else: an unknown mode, or a practice test for an exam not in
  its final 21 days, is refused without closing the open session.
- *A session an older build saved* (no `plan.info.engine == 2`) is closed, not resumed: its held
  answer is committed (a row without a role, read as a pre-v3 growth observation), its practice
  test graded.

**Expected failures until W2's page side is merged** (strict xfails keyed on web/ itself, so they
turn back into plain checks on merge):
- `tests/test_app.py::test_public_api_matches_typescript_bridge`, until bridge.ts declares
  `course_settings_get`;
- `tests/app/test_bridge_contract.py`: the mirrors of the payloads wave 2 changed and the live
  session check, until types.ts declares `SittingView`. After the merge, `Turn` and
  `StartRequest` still differ until types.ts drops `lighter` and the three start fields.

**Spec problems and questions found**
- *The sitting formula counts typing twice.* The wall clock to the submit already includes the
  typing, and the allowance is added on top; TIME-4 meant the allowance to replace the measured
  typing ("typing math slowly never counts as slow thinking"). Built as given. If the allowance
  should replace the typing, the sound version (no loophole of one early keystroke, then leaving)
  is the wall clock to the submit less the measured active entry time, plus the allowance: one line
  in `sitting_minutes`.
- *Untimed and sittings.* With the untimed rule above, a student who always studies untimed can
  never certify M2 or M3, and the planner keeps offering sittings (a void has no wait).
- *`tests/ui/test_session_summary.py`* called `study_diagnose`, which mypy (in `check.sh fast`)
  rejects now. It carries W2's own change to the file, applied unchanged from W2's branch, so the
  merge has nothing to resolve there. Its "ready today" check reads `Summary.ready_today`, whose
  meaning changed (above); the coordinator checks it at merge.
- *Time.* The DEV-9 fast state machine now takes 45-100 s here (the docstring said well under
  30 s): the planner runs on every answer and every start, and the new learner invariant replays
  the log after every step (with the cached catalog; rebuilding the catalog each step doubled it).
