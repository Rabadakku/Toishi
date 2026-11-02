# ADR-0016: Integrating fitting, honest grading and the Anki import (wave 8)

- Status: Accepted. Completes the hooks ADR-0013 left to the grading paths, settles where
  automatic fitting runs, and connects ADR-0015's import to the engine.
- Date: 2026-11-01

## Decision

### Rules version

`RULES_VERSION` is `2026.11-r3`, later than both branches' values (r1 fitting, r2 grading).
Only events graded under the merged rules are fit targets; r1/r2 events stay as prefixes
(C6).

### One clock (C4)

`lifecycle.review_on` passes `elapsed_days = days.between(last, now)` on the calendar it is
given; flashcards go through it too. Live updates, `replay` and recompute count the same
whole study days. Fractional days remain only in recall for display and Level's spacing.

### Disputes and reports (C3)

The exact undo (ADR-0012) stays first: it restores Elo, tiers and Level too. When it is
refused because rows changed since, the session voids the answer with
`Engine.void_attempts`, which rebuilds the touched cards' memory from the log in the same
transaction (a card with no event left since its seed returns to the memory its first
voided event started from). Other rows keep their later values.

### Automatic fitting (I7)

`StudyService.end()` starts `Engine.auto_fit` on a background thread. `Engine.fit` is split
into `fit_decision` (slow, read-only) and `apply_fit` (writes the set, recomputes);
`auto_fit(writing=)` holds the service lock only around `apply_fit`, so a recompute never
interleaves with a graded answer and the student never waits for a fit. One fit at a time;
a failure is kept in `last_auto_fit` and the sets in force stay.

### Parameter sets everywhere (decision 6)

Code that schedules many skills at once takes `adapter_of` (`scheduled_load`,
`goal_change`, `plan_boosters`, `apply_seeds`, `DiagnosisHook`, `partial_credit`); the
engine and queue pass `Engine.skill_adapters()`. The session no longer builds its Engine
with one fixed adapter (that overrode every set, flashcards included). Flashcards are
graded with `Engine.adapter_for_card` (the "flashcards" set or the card's Anki deck
group's); the queue's shim is gone.

### Anki import -> engine

`core.importers.anki.recompute_memory(storage, record=None)`: for each Anki import (the
given one, or all, oldest first) every deck options preset with FSRS parameters becomes
the group `<preset id>` (`Engine.register_deck_group`: its decks join `fsrs.deck_groups`,
its parameters become "anki.<group>" unless that set was written since). Items stored
without FSRS state are replayed from their reviews with their group's parameters
(`Engine.replay_flashcards`, due at 0.90 like a flashcard graded now), then
`Engine.recompute_memory()` runs. Histories cut before Anki's last learning block (an
`sm2_seed`) are not replayed.

### Cloze

The queue's cloze items use the port's parser (`core.importers.anki.cloze.parse`): several
numbers per blank, nesting and MathJax-aware closing, still rendered as Markdown.

## Not done

- `lifecycle.learning_answer` replaying a failed learning phase before the passing one
  (so a recompute after a failed-then-passed phase changes nothing): it changes the
  interval of a clean phase that follows a failed one from 2 days to 1, which
  `tests/engine/test_simulation.py::test_intervals_are_sensible` forbids. Until decided, a
  recompute moves such cards to the Anki value (ADR-0013).
- SM-2 seeds for incomplete imported histories; recompute also replays cards whose FSRS
  state was imported as it is, when their last review matches their last logged event.
