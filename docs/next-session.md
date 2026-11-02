# Where we stopped (2026-11-01, night)

Start the next session here. Owner's direction: correctness of grading, scheduling and saved
progress first; the base app great before problem sets are mass-produced; every decision backed by
research; no AI in the app.

## State

- main: everything merged. The last Mac run (all modes) passed: 4308 core and 94 WebKit page tests,
  build and self-test.
- The full evidence review is done: report `docs/research/Toishi full evidence review.md`,
  notes and scripts under `docs/research/notes/Toishi full evidence review/`. It lists 20
  ranked defects (section 2) and a verdict map.
- The spec was updated from the review: Claude Doc revision 261 and later, exported to
  docs/spec.md. ADR-0019 records the rule changes and amends ADR-0006, 0007, 0013 and 0014. New
  requirements carry release tags (1.0 / 1.1 / Later).
- The card-format Claude Doc is BEHIND the repo's docs/card-format.md (commit ab0044f plus the
  format 1.1 additions). Treat the repo file as current, and sync the doc from it before anyone
  edits the doc.
- The Mac runner works: write a mode to .runner/requests/<id>, then read .runner/status.

## Owner's roadmap order (2026-11-01, 20:08), overrides the spec's plan until the spec is updated

1. **Mac only.**
2. **Functional first version: all functionality complete and in full working order**, with no
   visual polish. Coordinator's reading, to confirm with the owner: everything functional in the
   1.0 and 1.1 scope (including the exam layer, paper mock exams and the mistake lifecycle), with
   correctness first (M7).
3. **Then the Calculus I problem sets.**
4. **Then polish** (looks, accessibility polish, stats charts).
5. **Then everything else** (the Later list: other platforms, Chinese, concept sections...).
Next session: update the spec's Implementation plan and Release timeline to this order (the Calc I
pack will take a few months; the app helps with imported Anki decks before
then).

## Next, in order (milestone M7, "correctness first")

1. Reset and recreate the two stopped M7 worktrees (/home/claude/wt/trace and
   /home/claude/wt/durability) from main, and restart them with their briefs (DEV-6, DEV-10..12;
   DEV-7..9).
2. Fix the review's defects, each with a test that fails before the fix. They are listed in the
   report's section 2 and in ADR-0019:
   - below-band items never train the scheduler;
   - practice-test misses are Again at every tier;
   - undo after a shown solution;
   - atomic fit adoption with startup repair, and catching PanicException;
   - credit stays in Shadow;
   - held misses settle after 7 days;
   - the study day is frozen at grading;
   - SQLite floor 3.51.3;
   - interval `vars`;
   - the hole message instead of a reject;
   - canonical "simplified";
   - placement half-split;
   - passed step checks count as plain Again;
   - check problems obey the same-day rule;
   - atomic disputes;
   - pack key fixes void old attempts;
   - in-app restore;
   - bridge hardening (an allow-list over pywebview's dispatcher, navigation and drop policy,
     ALLOW_FILE_URLS off, a Host-header check).
3. An independent fresh-context review of the scheduler, engine and queue against Anki's code and
   the reference vectors. Mutation runs on the five critical modules. An mpmath cross-check of
   SymPy.
4. Then M8: the reordered first run, goals and exams, the import screen with flashcard fidelity,
   minimal Settings, function plots, accessibility fixes.
5. A content pilot (one Calculus I section) in parallel once M7's gates are green. Measure tokens
   per card and the error rate before scaling (PACK rule).

## Owner decisions still open (spec "Risks and open decisions")

- Practice-test window: the coordinator chose 21 days to match boosters. The code says 14.
- Whether a Calculus I pilot section ships inside 1.0. The release candidate is now gated on
  criteria, not the date; the dates are marked at risk.
- Reach beyond the Mac (offline web app via Pyodide spike; Windows), signing and distribution,
  the fsrs-rs-python license, public source hosting versus "no GitHub", app and pack licenses,
  sustainability, and when to start the Chinese interface.
- Paper mock exams (1.1): first research OMR accuracy on phone scans and the paper-versus-screen
  evidence, and spike Continuity Camera in the pywebview window.

## Known

- A flaky test under load: tests/ui test_shortcuts_never_fire_while_typing_except_enter.
- fsrs-rs-python has no license; this blocks any public release.
