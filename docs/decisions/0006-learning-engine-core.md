# ADR-0006: Learning engine scheduling core (M4a)

- Status: Accepted
- Amended by: ADR-0019 (slow rule (section 5), placement (section 9), leech threshold, partial-credit switch, weak-spot finder, Lighter set and checks below the core band)
- Date: 2026-11-01

## Decision

`core/engine/` computes; `core/storage/` persists. Everything is a pure function over the
records in `core/model.py`, except `Engine` (`service.py`), which loads rows, calls them and
commits each graded answer through `UserStore.record_answer` in one transaction.

### FSRS adapter (`fsrs_adapter.py`, the only py-fsrs importer)

- py-fsrs 6.3.2 with `learning_steps=()`, `relearning_steps=()`, fuzz on, maximum interval
  from the setting (365 days). The app runs learning and relearning itself.
- The adapter calls py-fsrs's formula methods (`_initial_stability`, `_next_stability`,
  `_short_term_stability`, `_next_difficulty`) so it can feed them **fractional-day**
  retrievability (ENG-1). Those are private; the pin and a conformance test (whole-day
  reviews match `Scheduler.review_card` exactly) guard them. FSRS-7 replaces this module.
- **Same day means the same study day.** py-fsrs uses its short-term formula when under 24
  hours have passed, so a skill learned at noon and reviewed the next study day at 11:58
  got almost no stability, and weak skills looped at 1-day intervals in the simulation.
  `lifecycle.review_on` passes "same study day" (4 AM rollover) instead.
- Due dates are computed live: last review's study day + interval(stability, retention in
  force), with py-fsrs's fuzz ranges and a fuzz position hashed from (skill, last review),
  so recomputing gives the same day and a goal change reschedules nothing.
  `SkillState.due_at` is only a cache of that value at review time.
- `fsrs_state` 3 marks relearning after a lapse: due the next study day (ENG-3).

### Dependencies

- `hypothesis==6.170.1` (dev): property tests.
- `fsrs-rs-python==0.9.3` in the optional group `fit` (`uv sync --group fit`), imported
  lazily for ENG-12. Its package declares no license (the Rust library is BSD-3-Clause):
  fine for this personal app, **to be settled before any sharing**. `check.sh`'s
  `uv sync --locked` leaves it out; its test skips then, and `fit_parameters` raises
  `FitUnavailable`. The fsrs-rs simulator is not used: load projections use a seeded
  Monte Carlo in `projection.py`.

### Storage (no schema change)

- Elo: theta in `SkillState.elo_theta/elo_n`; each answer's Elo numbers in
  `Attempt.extra["elo"]`, and a problem form's difficulty is its latest non-voided value,
  so undo also undoes difficulty drift.
- Learning phase (`level_evidence["phase"]`, `example_due`, `restart_on`) and Level evidence
  (`level_evidence["log"]`, last 30 answers) live in `SkillState.level_evidence`.
- Speed: `Attempt.extra["speed_ms"]` (solve time + typing allowance, capped) and
  `extra["baseline_ok"]`; baselines are recomputed from attempts, cached in `SkillTierState`.
- Fitted parameters: the setting `fsrs.params.math` (`{"w": [...], "id": ...}`); events
  carry `params_id` and `rules_version` (`config.RULES_VERSION`).

### Readings of the spec where it is open

1. **Stretch problems.** The rating map's row is about a stretch "answered wrong" (no FSRS
   event, Elo only, core-band follow-up). A stretch answered right is rated normally and
   settles the review; otherwise the skill would stay due and be served again tomorrow.
   Stretch events carry no predicted recall, so ENG-11 bins are not biased by logging
   successes but not misses.
2. **Boosters.** A booster's window runs from the first day a Good review keeps exam-day
   recall at the target (the spec's ~0.4 x new stability before the exam) to the day
   before. Boosters are load-balanced over their windows; ties go to the earlier day,
   leaving room to re-plan after a failed booster. The plan is recomputed daily.
3. **Level.** "Correct" means right on the first attempt with no hints; a miss is a rated
   Again (a slip within the cap is Hard and is not a miss). A miss while Learned shows
   Learning; Learned comes back after `correct_in_a_row` clean answers in a row (no new
   learning block: ENG-3 already schedules the relearning). Promotion waits while shaky.
4. **Learning phase.** Guessed answers don't extend the streak; the phase fails as soon as
   the streak can no longer be reached within the problem limit.
5. **Slow and too easy.** A slow answer marked too easy stays Hard.
6. **Custom goal.** Exam-day target min(0.95, r + 0.05), none at 0.80; hardest tier 5 from
   r = 0.90, else 4. An exam after the goal date falls under Keep (no target).
7. **Exam window** (tier 3 for in-scope skills, no stretch) = the 21-day booster window.
8. **Forms.** A template's variants are one form; any other card is its own form.
   Difficulty drifts at most 0.05 per answer and 0.5 from the tier anchor in total.
9. **Placement.** Inference follows `requires` transitively. Covered/Solid sections seed
   like inferred (2.3 d) / direct (10 d). Seeds never mark an existing card provisional; a
   provisional seed missed at its first review starts as new, with no lapse and no event.
   Next-course prerequisites (LIB-8) are the transitive `requires` closure.
10. **Speed.** No target until five correct answers after Learned or a known exam length;
    tier shares of an exam problem 0.25/0.40/0.50/0.80/1.0 (tiers 1-5); a tighter target
    waits a week since the last change. Baselines use the last 20 eligible successes after
    Learned (reinforcement problems excluded).
11. **QUE-5 room** assumes the same number of new skills each day of the week (each costs
    its learning block plus about one early review).
12. **Projections (LIB-9).** Exam score = mean of recall x level factor (Learning 0.4,
    Learned 0.75, Exam-level 0.95, Mastered 1.0), starting guesses; the shortfall
    1 - r f splits exactly into level (1 - f) and recall f (1 - r).

### Extension points for the diagnosis milestone

`GradeHook` callables (passed to `Engine` or `grade_answer`) run after base grading and
return a changed `GradeResult`. `Effects` reports `lapse`, `reinforcement_due`,
`core_followup_due`, `prerequisite_checks` (ENG-2 failure, ENG-9 leech), `leech`,
`textbook_ref`, `confident_error`, `tier_flag`. `AnswerFacts` already takes
`slip_within_cap`, `didnt_know_start` and self-grades. Not implemented here: the "What went
wrong?" flow, checks, cued twins, ENG-6, ENG-7, ENG-15, ENG-16, the queue builder.

## Consequences

- The simulation harness (`tests/engine/sim.py`) drives the pure API with simulated
  students and is the place to test future rule changes before bumping `RULES_VERSION`.
- ENG-11's notice (30 reviews, 0.10) is noisy: one standard error of a 30-review bin at
  p = 0.65 is 0.087, so a well-calibrated model can raise it by chance. Worth revisiting
  with a significance test once real logs exist.
