# ADR-0013: FSRS fitting, one clock and memory rebuilt from the log

- Status: Accepted
- Amended by: ADR-0019 (fit adoption is atomic with startup repair; PanicException is caught)
- Date: 2026-11-01
- Supersedes parts of ADR-0006 (fractional-day stability updates, the manual 512-review fit,
  `fsrs-rs-python` as an optional group) and the matching readings of ENG-1, ENG-11, ENG-12.
- Source: `docs/research/Spaced repetition algorithm gap audit.md`, fixes C1-C4, C6, I1, I6-I8,
  I10 and decision 6 (approved by the student).

## Decision

The FSRS-6 formulas stay as they are; the engine adopts the guard rails Anki builds around
them (Anki 26.09.3, fsrs-rs 6.6.2).

### One clock (C4)

- The stability update sees **whole study days** t since the last review (0 = the same
  study day: the short-term formula), the clock the fitter trains on. Fractional-day recall
  stays for display, sorting and triage. `Engine.grade` logs both: `predicted_recall`
  (fractional, as before) and `Attempt.extra["recall_days"]`.
- `FsrsAdapter` carries a `StudyDays` (Engine passes the profile's). The py-fsrs 24-hour
  fallback is gone; `replay()` counts study days like `lifecycle.review_on`. Stability is
  capped at 36,500 days as in fsrs-rs.
- Golden vectors (audit table) are tests; the 23:00 -> 08:00 example now gives S' = 10.964.

### Parameters: cleaned, adopted only when they win, refitted automatically

- **C1.** Every vector is rounded to 6 decimals and clamped into the intersection of
  py-fsrs's bounds and fsrs-rs's clipper (`fsrs_adapter.clean_parameters`); a vector of the
  wrong length or with a non-finite value falls back to the defaults with a notice
  (`ParameterSet.notice`). `Engine.adapter()` never raises for a stored vector.
- **C2.** `fitting.adoption`: keep the current set unless the candidate's recency-weighted
  log loss on the same items is lower (fsrs-rs `evaluate`). Above 300 items the candidate
  must also win held-out on 5 time-ordered folds (segment = N/6, each fold fitted on every
  earlier segment) and pass Anki's health check (adjusted log loss <= 1.11 or adjusted
  RMSE(bins) <= 1.53). The app's own `log_loss`/`rmse_bins` accumulate in float32 like
  fsrs-rs, so they match `evaluate` to 1e-7.
- **I7.** `Engine.auto_fit()` fits each parameter set that is due: first at 300 long-term
  items, then every 30 days or when the items double. Every attempt is logged in
  `fsrs.fit_log.<set>`; adopted sets go to `fsrs.params.<set>` and their history
  `fsrs.params_history.<set>` (50 kept). `revert_parameters(set, params_id)` is the
  one-click revert. The 512-review manual offer is gone (`fit_offer` counts items, needs 300).
  The caller (session end or launch) decides when to call `auto_fit`.

### Parameter sets (decision 6)

One set per skill domain (`fsrs.domains`: course -> domain; others share "skills"), one for
flashcards ("flashcards", defaults until its own fit) and one per imported Anki deck group
("anki.<group>", `fsrs.deck_groups`: deck prefix -> group). `Engine.adapter_for(kind,
group)`, `adapter_for_skill`, `adapter_for_card`. The legacy `fsrs.params.math` still feeds
"skills" until that set is written. Domain names are the student's (rule 12).

### Training data kept whole (C6, I1)

`core/engine/histories.py` builds one history per card from its last fresh start:
- A **block start** flag is written explicitly in `Attempt.extra["fsrs_events"]` (one entry
  per event: kind, role, block_start) by `Engine.grade`; older rows are inferred (no
  stability before, previous event not a learning event). A learning phase that crosses
  04:00 stays one history.
- Failed learning phases are logged as **prefix-only** events (kind `learning-failed`),
  part of the same learning block, as Anki keeps every learning row.
- Events under an older `RULES_VERSION` stay as prefixes; only current-rules events are
  targets. Stretch, check-settled and post-stretch follow-up events are prefix-only.
- `Attempt.extra["strict_ok"]` is the strict label (first try, no hint, final answer
  correct). Grading may write it; `Engine.grade` fills the derived value when absent.

### Memory rebuilt from the log (C3, I6)

- `Engine.recompute_memory()` replays each card's non-voided events from its last fresh
  start (a placement seed starts from its seed) and writes the changed rows in one
  transaction, logged as an `attempt_void` row with reason "recompute" that voids no
  attempt (`UserStore.rewrite_states`). It runs after every adopted fit and revert.
  Due-date caches are left alone (Anki: no reschedule unless asked).
- `Engine.void_attempts(ids, reason=...)` voids older attempts and rebuilds the touched
  cards in the same transaction.
- `SkillState`/`FlashcardState` reject non-finite stability or stability outside
  [0.001, 36500] and difficulty outside [1, 10]. `Engine.check_database()` reads raw rows
  (`UserStore.raw_state_rows`), repairs impossible ones (and a review in the future) from
  the log and then recomputes everything.

### Calibration that doesn't cry wolf (I8)

Bins show a 95% Wilson interval and are greyed under 30 reviews; the alarm uses a
continuity-corrected Wilson interval at alpha = 0.05 / (bins shown). `calibration_stats()`
returns per-course and per-series reports (core, strict, settled, stretch, post-stretch),
Anki's true-retention table (first interday review per day, young/mature at 21 days) and,
when asked above 300 items, held-out log loss and RMSE(bins) with the size-adjusted
thresholds. Data only; the stats screen comes later.

### Dependencies

`fsrs-rs-python==0.9.3` moves from the optional group `fit` into the main dependencies and
ships in the app (imported statically by `core/engine/fitting.py`, so PyInstaller bundles
it). Its package declares no license (the Rust library is BSD-3-Clause): acceptable for this
private, personal app; settle it before any sharing.

### Storage (no schema change)

Additive only: `UserStore.rewrite_states` and `raw_state_rows`; new keys in `Attempt.extra`
(`fsrs_events`, `strict_ok`, `recall_days`) and new settings keys. Old rows still work:
every flag has an inferred default.

## Hooks for the grading paths (owned elsewhere)

- `grading.py` may set `extra["strict_ok"]` itself and mark events `role: "prefix"` in
  `extra["fsrs_events"]` (`histories.annotation`).
- `lifecycle.learning_answer` builds a learned card from the passing phase only; to match
  the log exactly after a failed phase it should replay the block's prefix too
  (`histories.build_histories` gives it). Until then a recompute moves such cards to the
  Anki value.
- `lifecycle.review_on` may pass `elapsed_days=days.between(...)` instead of `same_day`.
- Disputes in `core/queue/session.py` should call `Engine.void_attempts`.
- Flashcard code should take its adapter from `Engine.adapter_for("flashcard", group)`;
  schedule/booster code that takes one adapter for all skills uses the default domain's.

## Consequences

- The first recompute after this change moves stored stability to the whole-day clock.
- A learner far from the defaults recovers to within ~0.002 held-out log loss at 5k items
  (the optimizer's pull toward its start); near the defaults, within 0.001 (I10 test).
- The strict-label series shows a slip habit as a gap the rated bins cannot show (I1 test).
