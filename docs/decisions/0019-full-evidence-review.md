# ADR-0019: Decisions from the full evidence review

- Status: Accepted
- Date: 2026-11-01
- Amends: ADR-0006, ADR-0007, ADR-0013, ADR-0014 (sections named below)

## Context

On 2026-11-01 the owner asked for a review of everything built so far and for every decision to be
backed by research. Twelve read-only reviews and research notes, and one synthesis, are in
`docs/research/Toishi full evidence review.md` and
`docs/research/notes/Toishi full evidence review/`. The coordinator decided the resulting
spec changes, and the spec was updated (Claude Doc revision 261 and later, exported to
docs/spec.md). Several changes contradict older ADRs. Under the new precedence rule (item 1), an
older ADR would otherwise still win, so this record makes the changes binding.

## Decision

1. **Precedence (spec DEV-17).** A newer accepted ADR supersedes conflicting spec text until the
   spec is updated, which happens within the same milestone. Every ADR lists the spec IDs and ADR
   sections it amends, and an amended ADR gets an "Amended by" line at the top. Briefs name both
   the spec sections and the ADRs.
2. **No AI in the app, now or later** (owner decision). There are no model calls at runtime, local
   or remote, and no optional or bring-your-own-key AI. Evidence: unguarded AI tutoring lowered
   exam scores in randomized trials (Bastani et al., PNAS 2025; Maryland 2026), and closed-book
   exam scores fell in a 26,811-student panel in China. The benefits seen elsewhere came from
   verified solutions, one-step hints and structure after mistakes, which the app provides without
   AI. AI stays a development tool (writing code and content offline, with verification).
3. **Correctness before features** (owner decision). Defects in grading, scheduling and saved
   progress are fixed, each with a test that fails before the fix, before new features ship.
4. **Integration errors count** (amends ADR-0014, the passed-step-check case). When a step check
   passes, the tapped step's skill is fine, and the miss belongs to the problem's own skill: it is a
   plain Again that counts for Level and leeches. Only a careless slip or misread within its 30-day
   cap is excused.
5. **Below-band items never train the scheduler** (amends ADR-0014 and ADR-0006 on the Lighter set
   and prerequisite checks; spec ENG-4, ENG-6, QUE-10). Problems below a skill's core band never
   enter parameter fitting. In the live schedule a below-band miss is Again, and a below-band
   success changes nothing. A practice-test miss is Again at every tier, including exam tiers 4
   and 5 (QUE-19).
6. **Time never changes a rating** (amends ADR-0006 section 5; spec ENG-13, ENG-14). A slow answer
   is labelled and feeds Level's pace evidence only when an exam with a length is entered. Grading
   10% of passes Hard raised workload by about 19% with no recall gain in a researchers'
   simulation.
7. **Undo after a shown solution** keeps "solution shown", so a re-answer can never be a clean Good.
8. **Fitting is atomic** (amends ADR-0013). Adopting fitted parameters is one transaction, and
   startup repairs a half-applied fit. Fit failures are persisted. Calls into fsrs-rs-python catch
   its `PanicException`, which derives from `BaseException`, not `Exception`.
9. **Statistical rules** (amends ADR-0006):
   - Partial credit (ENG-7) stays in Shadow through 1.0. Switching it on needs a paired
     confidence interval with a margin over at least 800 held-out credited reviews.
   - The weak-spot finder (ENG-15) uses an exact binomial tail with sequential confirmation
     instead of z <= -2.
   - Placement (ADR-0006 section 9) asks a middle skill first and halves the remaining range. A
     fail prunes its dependents, and a single pass never marks a deep chain known without a
     confirming question.
   - The leech threshold is 8 lapses (Anki's default), marked provisional.
10. **Holes** (amends ADR-0007, "Holes are wrong"). An answer that differs from the key only at
    removable points is not marked wrong. It gets a message that costs no attempt and is logged as
    its own category. Domains a card declares strict are still enforced, and the policy is revisited
    from the logged data. Holes-as-wrong had no production precedent and rejected natural rewrites
    in our probes.
11. **Numbers.** E-notation is accepted. Tolerance comes from the requested rounding; when none is
    requested it is 1% relative with an absolute floor, and exact answers stay exact. Interval and
    inequality answers declare their variable, and other letters are invalid. "Simplified" names
    canonical forms instead of a node count.

## Consequences

- The code changes land in milestone M7, with the M7 gates: test protection, trace, trust report,
  kill loop, stateful property test, an independent scheduler review and mutation runs on the
  critical modules.
- ADR-0006, ADR-0007, ADR-0013 and ADR-0014 carry an "Amended by ADR-0019" line.
- Constants without a published source are listed as provisional in the spec's constants table and
  logged for evaluation (DEV-16).
