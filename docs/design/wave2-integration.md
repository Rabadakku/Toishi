# Wave 2: wiring the student model and planner into the app

2026-11-02 · design v1.2 · implements ADR-0020 in the app.
- W1 (core) and W2 (bridge types and UI) are built in parallel against the contract in section 6.
- W3 (planner changes) is `docs/design/wave2-planner.md`.
- The survey of the old engine's connections is summarized in section 8.

## 1. What changes and what stays

**Problems move to the new engine:**
- Practice problems are planned by `core.plan` and modeled by `core.learner`.
- The skill-level FSRS scheduling of problems stops: no SkillState memory, SkillTierState, review_log events or implicit credit for problems.
- The diagnosis flow stops: pending checks, weak spots, diagnostic sets, the error picker.
- So do hints, boosters, triage, the lighter set, Level, goals and placement.

**What stays:**
- grading (`core.grader`), card loading and packs;
- the session row and its crash safety;
- tries and timing;
- the `attempt` log and attempt voiding;
- flashcards and clozes, with card-level FSRS unchanged (`grade_flashcard`, `rate_flashcard`, flashcard_state);
- the Anki import, profiles, backups, library and media.

**The learning design:**
- **No help during practice:** no hints and no explanations.
- **Retries:** a wrong answer can be retried any number of times. Only the first try counts.
- **Give up** shows the solution and ends the item.
- **The textbook pointer:** each problem names its textbook section.
- **When stuck,** the planner's ladder changes the problem (W3).
- **Certification sittings:** M2 and M3 certify in closed-book, timed sittings.

## 2. Data: user.db v3

One migration, `sql/migrate_user_v3.sql`, added the way `schema.py` adds v2: frozen SQL, a `_v3` step, `USER_SCHEMA_VERSION = 3`, dataclass fields in column order, append-only trigger lists, and fixtures and tests as for v2.

**`attempt` gains these columns, appended in order:**

| Column | Type | Meaning |
|---|---|---|
| `role` | TEXT NULL | The planner role of the item: new, growth, maintenance, check, practice-test, focused, sitting, placement. NULL for flashcards and rows from before v3 |
| `milestone` | TEXT NULL | M1, M2, M3 or keep: what the item worked toward |
| `missed` | INTEGER NULL | 1 if the item was missed-milestone catch-up work |
| `plan_p` | REAL NULL | The calibrated prediction when the item was chosen |
| `ladder` | INTEGER NULL | The stuck-ladder rung (0–2) |
| `sitting` | TEXT NULL | The sitting id, for certification sittings |
| `learner_version` | TEXT NULL | The learner parameter version that made `plan_p` |
| `valid_minutes` | REAL NULL | The minutes the learner uses for a correct first try: NULL if untimed or invalid under `core/engine/timing.py` (`excluded_from_baseline`) |

**New tables:**
- `course_settings` (one row per course):
  - `course_id` TEXT PK REFERENCES the course;
  - `start` TEXT NULL, `aligned_deck` TEXT NULL, `aligned_day` TEXT NULL;
  - `pace_factor` REAL NOT NULL DEFAULT 1;
  - `accuracy_target` REAL NOT NULL DEFAULT 0.9, `target_tier` INTEGER NOT NULL DEFAULT 4;
  - `end_day` TEXT NULL;
  - `keep_target` REAL NOT NULL DEFAULT 0.8, `keep_tier` INTEGER NOT NULL DEFAULT 3;
  - `growth_band` TEXT NOT NULL DEFAULT 'standard' (standard = 0.70–0.90, hard = 0.50–0.75);
  - `updated_at` INTEGER NOT NULL.

  An existing `course_goal.starts_on` seeds `start` in the migration.
- `learner_params`:
  - `version` TEXT PK, `created_at` INTEGER NOT NULL;
  - `params` TEXT NOT NULL (JSON of SharedParams);
  - `source` TEXT NOT NULL (prior, refit or reset);
  - `report` TEXT NULL (JSON of the RefitDecision);
  - `current` INTEGER NOT NULL DEFAULT 0, with exactly one current row (a partial unique index).

**The `exam` table is reused** for `ExamSpec`:
- `day` is the study day of `at`;
- `scope_decks` comes from `sections`;
- `target` comes from `target_recall`, where NULL means the course accuracy target.

## 3. Core: `core/practice/` (new package, W1)

Pure Python with no GUI imports. It is the only place that joins storage, packs, `core.learner` and `core.plan`.

### `catalog.py`
- Builds the `ComponentInfo` catalog and a `core.plan.Course` per course from the loaded packs:
  - skills, decks and their order;
  - `requires` and `confusable`;
  - the example card;
  - the pool of `ProblemSpec` per skill;
  - background components (alg./trig./pre. prefixes, or outside the course's sections);
  - the pace standard (pack v3 `pace`; none for older packs).
- A `ProblemSpec` per gradable problem: a card, or one part of a multi-part card (`problem_id = card#part`). Its fields:
  - `components`: the skill first, then `uses` and step tags, de-duplicated;
  - `tier` and `steps` (the number of solution steps);
  - `standard_minutes` (`core/cards/standard_time.py`, or the card's `time:`);
  - `wrong_components` (`core/cards/components.py`);
  - `family` (the template id, else the card id).
- Template instances share the template's family. Suspended and retired cards are left out of pools.

### `observations.py`
- Attempt rows, not voided, become `Observation`s in (at, id) order.
- The first try of a presentation (`attempt_number = 1`) is the observation:
  - `correct` is its verdict, so a final=0 first row means a wrong first try;
  - `aided` is a give-up or "show solution" before any submitted answer, or an example opened before answering;
  - `matched_wrong` is the column;
  - `minutes` is `valid_minutes` (rows before v3 derive it from `active_ms` and the timing validity rules, or leave it NULL);
  - `role` is the column (rows before v3: `growth`).
- **Multi-part cards** give one observation per part, from `extra.parts`: correct on the first attempt and not given up. Parts are untimed.
- **Flashcards and clozes** give no observations.

### `engine.py`: `PracticeEngine`
- **`state(profile)`.** The learner `StudentState`, cached in memory.
  - The key is the newest non-voided attempt id, the voided count and the current params version.
  - New attempts update the cache incrementally with `StudentModel.update`. Any other change replays from the log (C3: the state is a pure function of the log).
  - The cache is thread-safe: one lock, held briefly.
- **`params()`.** The current `SharedParams` from `learner_params`. Without a row it writes the prior (`source = prior`).
- **`settings(course_id)`.** A `CourseSettings` from `course_settings` plus `exam`. Pacing anchors on `start`, or on `aligned` for a mid-course start; with neither, the course has no schedule.
- **`plan_day(day, now_ms, served)` and `next_item(...)`.**
  - They wrap `core.plan.plan_day` and `next_item` for each active course (a course with settings and a pack loaded).
  - The certifier comes from `Certifier.from_model` once per study day. Each graded first try goes in with `Certifier.add`.
  - **Several courses:** each is planned separately. Their regular items are interleaved round-robin in each plan's own order, after all new-skill blocks. Overflow and checks keep each course's rule. Skills differ across courses, so no same-skill adjacency can arise.
- **`record(observation)`.**
  - Called after the session's transaction commits.
  - It updates the cached state and the certifier, and returns the `UpdateRecord`.
  - The storage write is the session's (section 4), never `record`'s.
- **`statuses(course_id, day)`.** The day plan's `SkillStatus` list, for the Skills screen.
- **`calibration()`.** It replays the log with the current parameters and bins prediction against outcome, after the per-tier recalibration:
  - by tier;
  - by days since the main skill was last practiced: first, under 1, 1–7, 8–30, over 30;
  - by number of course components: 1, 2, 3+.

  Each bin carries n, mean predicted and observed.
- **`refit_due()` and `refit(force=False)`.**
  - `refit_due` uses `core.learner.refit_due` with `calibration_drift` over the predictions since the last refit.
  - `refit` runs `StudentModel.refit` on the log and records a `learner_params` row (source `refit`, the report, `current` only if adopted).
  - Adoption invalidates the cache.
  - A manual refit (`force=True`, the student's Refit now) runs whatever `refit_due` says, and the adoption rule is unchanged.
- **`reset_params()`.** Writes the prior as a new current version (`source = reset`).

## 4. Session (`core/queue/session.py`, W1)

The session keeps its row-per-call structure, lock, crash recovery, timing and flashcard paths.

**Planning:**
- `_new_plan` builds problem items from `PracticeEngine.plan_day`. Flashcards stay as today (`snapshot._flashcards` and `place_flashcards`).
- Each `WorkItem` maps to a `PlanItem`. Keep the existing fields and put the new ones in a small `meta` dict on the item:
  - `kind` (`problem`, or `example` for a worked example);
  - `skill_id`, `course_id`, `section_id` (the skill's deck), `card_id`;
  - `purpose = role`, `tier_hint = tier`, `est_ms` from `expected_minutes`;
  - `block` for a new-skill block, `why` and `tag` from `reason`;
  - `meta`: milestone, missed, p, ladder, sitting, time_limit.
- The plan's notes, behind skills, sittings, set-aside skills and hours go in `Plan.info`.
- W3 adds `ladder`, `sitting`, `time_limit`, `set_aside` and `sittings`. Read them with `getattr(..., default)` until W3 merges, so either order of merging works.

**After an answer:**
- `next` re-plans with `PracticeEngine.next_item` from the items served today.
- The old re-plans go: reinforcement items, PendingCheck items, learning-block growth, the flashcard refresher after a miss, and `_rebalance` for problems. Keep `_rebalance`'s flashcard part.

**Tries, give-up and timing:**
- **Unlimited retries for problems.** A wrong try records a non-final attempt as now (`record_try`) and returns "Not quite" with `can_retry`. The item ends when the student is correct or gives up. Only the first try is the observation.
- **Give up** returns the full solution and ends the item. A give-up before any answer is an aided first try, so a failure.
- **No hints:**
  - `hint` and `HintReveal` are removed;
  - `hints_used` stays a column (always 0 for new rows);
  - `show_solution` is allowed only after a wrong first try or a give-up.
- **Sittings:** a sitting item shows its time limit, its index and total, and a closed-book notice. Nothing is cut off at the limit. The `valid_minutes` and the verdict decide the pass.

**Committing an answer:**
- `_finalize` stops calling `Engine.grade` for problems. In one transaction it writes:
  - the final attempt row with the v3 columns (`valid_minutes` from the timing rules);
  - for a first try, nothing else: the learner has no state rows;
  - the session row.
- After the commit, it calls `PracticeEngine.record` for a first try.
- Practice-test items commit the same way, at the end as now.

**Undo:** voids the attempt rows of the last presentation (the existing void machinery: `attempt_void`, `voided_by`). It restores the plan from `extra.undo.plan` as now. The learner cache replays. Problem attempts have no state images to restore any more, so `_undo` handles that case without `state_before`.

**Practice tests:** keep the mode, reimplemented without triage:
- N problems at tier 3 (an exam's problem count, or 10) from the exam's scope sections;
- problems not served in the last 7 days;
- spread over the scope's skills;
- timed at the sum of their standard times.

Each first try is an observation with `role = practice-test`.

**Removed modes:** focused, weak-spot and lighter. They have no new-engine meaning; the ladder and the planner replace them.

**Day rollover and crash recovery:** unchanged. A held answer is graded through the new commit path.

**Refit:**
- After `end()`, and after a session that finishes through `next()` (which today never starts it), run `PracticeEngine.refit_due`.
- If a refit is due, run it on the existing auto-fit daemon thread pattern, one at a time.
- The old skill-parameter fit stops. Flashcard parameter fits keep running (they are FSRS card fits).

**Removals:**
- `core/engine/boosters.py`, `core/engine/diagnosis/`, `core/engine/placement.py`, `core/engine/goals.py` (its flashcard retention becomes the fixed 0.90 that flashcards already use), and `core/engine/level.py`;
- `core/queue/triage.py` and `share.py`;
- the problem parts of `planner.py`, `snapshot.py` and `selection`;
- the hint, diagnose, lighter and focused paths;
- their tests.

Keep what flashcards, recompute for flashcards, fits for flashcard parameter sets and the Anki import use. Delete in steps: switch the session first, then remove modules that nothing imports. `lint-imports` and the tests must stay green.

## 5. Bridge (`app/api.py`, W1) and pages (`web/`, W2)

**Removed:** `study_hint`, `study_diagnose`, `study_set_lighter`.

**Changed** (same names): `study_today`, `study_start`, `study_submit`, `study_give_up`, `study_show_solution`, `study_next`, `study_end`.

**Added:**
- `course_settings_get`, `course_settings_set`;
- `exam_save`, `exam_delete`;
- `skills_get`;
- `model_get`, `model_refit`, `model_reset`.

Section 6 has the shapes. `tests/test_app.py` checks that `Api` and `BridgeApi` have the same names: W1 adds the Python side and W2 the TypeScript side, and the check passes once both merge.

**Pages (W2):**
- **Home (Today):**
  - the day's minutes, and items by role (new, growth, maintenance, check, sitting);
  - hours per week to keep pace, from the student's history, or the standard hours when there is none (say which);
  - behind skills, sittings planned today, set-aside skills;
  - the planner's notes in plain words.
- **Study:**
  - no Hint button or HintLadder, and no "What went wrong" picker;
  - after a wrong try: "Not quite", Retry (focus back in the answer) and Give up;
  - Give up shows the solution;
  - a textbook line under the problem ("OpenStax Calculus Volume 1 §4.1"), from the section's deck;
  - a sitting banner (closed book, the time limit, "problem 2 of 5");
  - ladder items carry a short reason ("a smaller step first", "a prerequisite first");
  - when a skill is set aside, a one-line notice with the textbook pointer.
- **Course setup** (from Library, per course):
  - start date, or "my class is at section X today" (a section picker);
  - end date and exams (date, name, scope sections);
  - accuracy target (0.80–0.95), target tier (3–5);
  - practice difficulty: standard or hard;
  - the pace factor;
  - "no pace data" when the pack has none.
- **Skills** (per course): one row per skill with:
  - its state and track (ahead, on track or behind);
  - its milestones with deadlines and certified marks;
  - its level, readiness and pace.

  Grouped by section, filterable to behind skills.
- **Model** (in Settings):
  - the current parameters, read-only, with their source and date;
  - Refit now, showing the report: held-out log loss before and after per block, the p value, kept or not;
  - Reset to defaults, with a confirmation;
  - calibration tables by tier, gap and component count.

  Plain language with the numbers alongside, and no "mastery" wording anywhere.
- **Removed:** `HintLadder.svelte` and `WhatWentWrong.svelte`, with their tests.
- **Mocks:** `mock-bridge.ts` and `mock-study.ts` serve the new shapes, so every page works with `?bridge=mock`.
- **Page tests:** Playwright `ui` tests for each new page and for the retry, give-up and sitting flows.

## 6. The contract (exact names and shapes)

TypeScript, as `web/src/lib/bridge.ts` declares it. Python returns the same JSON: snake_case keys, ISO dates (`YYYY-MM-DD`), times in ms.

```ts
type Role = 'new' | 'growth' | 'maintenance' | 'check' | 'practice-test' | 'focused' | 'sitting';
type MilestoneName = 'M1' | 'M2' | 'M3' | 'keep';

interface ExamIn { exam_id?: number; course_id: string; name: string; day: string;
                   scope_decks: string[]; target?: number | null; minutes?: number | null; problems?: number | null }
interface Exam extends ExamIn { exam_id: number }
interface SectionRef { deck: string; title: string; hours: number | null }
interface CourseSettings {
  course_id: string; course_title: string;
  start: string | null; aligned: { deck: string; day: string } | null;
  pace_factor: number; accuracy_target: number; target_tier: number;
  end: string | null; keep_target: number; keep_tier: number;
  growth_band: 'standard' | 'hard'; exams: Exam[];
  sections: SectionRef[]; has_pace: boolean;
}
course_settings_get(course_id: string): Promise<CourseSettings>
course_settings_set(settings: Omit<CourseSettings, 'course_title' | 'exams' | 'sections' | 'has_pace'>): Promise<CourseSettings>
exam_save(exam: ExamIn): Promise<Exam>
exam_delete(exam_id: number): Promise<void>

interface MilestoneView { name: MilestoneName; tier: number; deadline: string | null; certified: boolean }
interface SkillRow {
  skill_id: string; name: string; deck: string; state: string; track: 'ahead' | 'on-track' | 'behind';
  intro: string | null; milestones: MilestoneView[]; level: number | null;
  readiness: number | null; pace_ok: boolean | null; set_aside: boolean;
}
skills_get(course_id: string): Promise<{ course_id: string; day: string; skills: SkillRow[] }>

interface Bin { label: string; n: number; predicted: number; observed: number }
interface RefitReport {
  at: number; attempts: number; adopted: boolean; p_value: number;
  blocks: { name: string; current: number; candidate: number; p_value: number; adopted: boolean }[];
}
interface ModelView {
  version: string; source: 'prior' | 'refit' | 'reset'; created_at: number;
  params: Record<string, number | number[]>; last_refit: RefitReport | null;
  calibration: { by_tier: Bin[]; by_gap: Bin[]; by_components: Bin[] };
  attempts: number;
}
model_get(): Promise<ModelView>
model_refit(): Promise<RefitReport>
model_reset(): Promise<ModelView>
```

**`study_today` returns `TodayView` with these new fields:**

```ts
{ minutes: number; by_role: Partial<Record<Role, number>>;
  hours_to_keep_pace: number | null; hours_basis: 'history' | 'standard' | 'none';
  standard_hours: number | null; behind: string[]; set_aside: string[];
  sittings: { id: string; skills: string[] }[]; notes: string[] }
```

`behind`, `set_aside` and `sittings` hold skill names, not ids. Fields that only the old engine filled are dropped.

**The turn's problem view gains:**

```ts
{ role: Role | null; reason: string | null;           // e.g. 'ladder:smaller'
  textbook: { book: string; section: string } | null;  // from the deck and pack.json source
  sitting: { id: string; index: number; total: number; time_limit_ms: number } | null }
```

**The attempt result gains** `can_retry: boolean` and `first_try_counted: boolean`. It loses the hint fields and `needs_diagnosis`.

## 7. Order of work and checks

- **W1:**
  1. migration v3 and storage helpers;
  2. `core/practice` with tests;
  3. the session switch;
  4. the bridge;
  5. removals.

  Keep `check.sh fast` green at every commit.
- **W2:** pages and components against the mocks, with page tests (`pytest -m ui`, Chromium in the workspace).
- **W3:** the planner (`wave2-planner.md`).
- **Merge order:** W3, then W1, then W2.
- **After merging,** the coordinator runs:
  - `check.sh full`;
  - `check.sh gates`;
  - the Mac `all` run (WebKit page tests and the app build);
  - a hand test of the flows in section 5.

## 8. Survey summary (facts the design relies on)

- **Problem planning:** `snapshot.gather` → `planner.build_plan` (triage classes, shares, new-skill room, stretch, order, flashcards placed in groups of up to 5). Re-plans happen in `_after_answer`.
- **Problem grading:** `Engine.grade` → `UserStore.record_answer` writes the state rows, the attempt, review_log, implicit credit and the session row in one transaction.
- **The attempt table** already holds what an observation needs, except `role`: first-try detection, `matched_wrong`, timing and `extra.parts`.
- **Undo** voids attempts and restores `state_before` images. The planner and learner need no images, because their state is derived.
- **Auto-fit** runs on a daemon thread after `end()` only.
- **Nothing in `core/queue`, `core/engine` or `app` imports `core.learner` or `core.plan` yet.**
