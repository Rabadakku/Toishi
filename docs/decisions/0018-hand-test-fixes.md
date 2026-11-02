# ADR-0018: Fixes from the hand test of the full build

- Status: Accepted
- Date: 2026-11-01

## Context

Merging wave 8 crashed the full suite (a segfault in the background auto-fit thread), and
hand-testing the built app on the Mac found five study-flow bugs (docs/backlog.md, "Hand test of
the full build", items 1-5) and literal asterisks on imported Anki cloze cards. This records the
choices made in fixing them.

## Decision

1. **Closing storage never pulls a connection from under a read.** Each thread's read
   connection (AGENTS rule 6) carries a lock held while that thread has a read open.
   `Database.close()` closes its own reader at once and waits (at most 30 s) for each other
   thread's open read before closing that reader; once closed, new reads raise
   `StorageError`. Closing a reader under a running query was a use-after-free in sqlite3: the
   auto-fit thread (I7) segfaulted when a profile closed while it read the catalog. A fit that
   outlives its profile now stops with `StorageError` (kept in `last_auto_fit`).
2. **Only a miss submitted sure is a confident error.** `grading.is_confident_error` decides
   (review or stretch, rated Again, and `AnswerFacts.submitted_sure_miss`: not unsure, not a
   give-up, not the last hint, not "didn't know where to start"); it sets
   `Effects.confident_error` and the guaranteed next-day redo. The solution view never
   recomputes it: it shows the note only from the effect recorded for the graded answer
   (stored on the session's current item), so an answer still waiting for "What went wrong?"
   shows none; the diagnosis follow-up sentence says it once the answer is graded.
3. **A card is never served twice in a study day.** `pick_problem(today_start_ms=...)` drops
   cards (and template parameter sets) served since the study day began, whatever else it
   relaxes; when nothing is left the slot is skipped. The learning phase (ENG-2) then needs
   `min(correct_in_a_row, pool)` clean answers in a row, where the pool is the skill's distinct
   active tier 1-2 problems (every active problem when it has none at those tiers). The pool is
   the whole pool, not what is left today, so a two-problem skill whose example used one of
   them finishes the next day rather than after one answer. The Library lists such skills per
   section (`small_pool_skills`).
4. **No example card: a tier 1 problem shown solved.** The example slot picks a tier 1 problem
   (never one seen today) and shows its steps and answer as the worked example. It is logged as
   a non-final "shown" attempt: it counts as seen (not served again today) and clears the
   example step, but answered-problem statistics (weak spots, timing baselines, find-the-error
   spacing) skip it.
5. **The summary says what is still ready today**: `Summary.ready_today`, the learning-phase
   problems Home would offer now, capped by each skill's problems not yet seen today. "To
   revisit" lists each skill once.
6. **Imported Anki cloze cards stay HTML.** `core.queue.cloze` reveals an Anki-HTML text with
   `reveal_cloze_text` (`<span class="cloze">`, styled by the note type's CSS); pack cards keep
   Markdown `**x**`.

## Consequences

- With a tiny pool a session can be shorter than Home's count suggested; the planner still
  sizes a learning block by the settings, and skipped slots are not refilled with new skills
  (QUE-5).
- The Test pack's arithmetic skill had two problems and no example card, so a first-day
  session held one problem. It now has a worked example and seven problems (tiers 1-2), enough
  for its learning phase to finish without repeats.
