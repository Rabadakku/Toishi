# ADR-0010: Every card kind in the queue, and practice tests (M5 gaps)

- Status: Accepted. Supersedes ADR-0009 readings 9 (practice tests) and 10 (cloze).
- Date: 2026-11-01

## Decision

The queue (ADR-0009) served plain problems only, graded multi-part problems as one box,
scheduled cloze blank 0 only and left unanswered practice-test problems ungraded. It now
serves every kind in docs/card-format.md through the engine (ADR-0006) and the diagnosis
flow's gating (ADR-0008). No schema change; StudyService only gained fields and methods.

### Multi-part problems (spec "Multi-part problems")

- Each part has its own box, verdict and tries, kept in the session row (`current.parts`).
  A part is final once right or out of tries and is not checked again; the problem is
  graded when every part is final. Each "Not quite" is logged at once with `Attempt.part`.
  Give up gives up the parts still open.
- `ProblemOutcome.parts` (`PartOutcome`: label, own skill, correct, tries, gave up) goes to
  the engine. `grade_answer` rates the card's own skill on the worst of its remaining parts
  (`parts.card_facts`: correct = all remaining parts right, attempt number = the most tries;
  equal to `rating.worst_rating` over parts rated one by one, which a test checks). If every
  part has a skill of its own, the card's skill is rated on all of them.
- The diagnosis hook reports parts with their own skill: answered right, that skill gets
  ENG-7 partial credit at weight 1 (same Off/Shadow/On setting and exclusions; merged with
  the card's own ENG-7 credit, one credit per skill at the larger weight); missed, it gets a
  prerequisite check (depth 1). The "What went wrong?" picker follows the card's own skill;
  `AttemptResult.outcome` is "correct" only when every part is right.
- An undecidable part, or a self-graded part, makes the whole card self-graded (as before).

### Find-the-error items

- Served in place of a skill's review problem (purposes review, booster, check-up,
  focused; never learning blocks, stretch, checks, reinforcement, redo or practice tests),
  counting as that review, when: the skill has two successful uncued reviews
  (`find_error_unlocked`); none of the last `queue.find_error_one_in` − 1 graded problems
  was a find-the-error item (`find_error_slot_open`; setting None turns them off); and the
  card was not seen in 90 days. Highlighted ("Step N is wrong") until two are solved.
- One try. Graded by `grade_find_error` on the step (given when highlighted), the reason
  and the corrected value (the checker); the solution view shows the shown work beside the
  correct solution. No "What went wrong?" picker (it is about one's own work).

### Which-method items (ENG-16)

- Items of a method-choice skill are which-method items (`PlanItem.method`): mixed in with
  full problems but outside the problem count (0 slots, about 15 s), so they never replace
  one. Served only while the skill is active (two of its methods learned); a method-choice
  skill is ready as a new skill once active. One try, no picker. Graded by base grading as
  the method-choice skill's reviews; uncued problems still count toward it (ADR-0008 #5).

### Cloze cards

- One item per blank number, Anki's card ord (ord = number − 1, so existing blank-0 rows
  are c1). The front hides every c<n> blank ("[...]" or its hint); the back shows the text
  with the c<n> answers in bold, then ### Extra. Like Anki's "bury new siblings", a cloze
  card brings at most one new blank a day, and none on a day another blank is due or was
  reviewed, so one blank's answer never gives the next away.

### Practice tests (ENG-8)

- The request's count, else the exam's problem count, else 10 exam-tier problems (kind
  problem, not self-graded: nothing is graded until the end) from the scope's learned
  skills (method-choice skills excluded). Every skill once before any twice; further
  problems go to the skill with the largest weight / (problems + 1), weight = 1 − recall +
  0.2; with fewer problems than skills, a weighted draw without replacement keyed by a hash
  of exam, day and skill. Optionally timed at exam pace; one try; graded at the end.
- **Unanswered problems count as Again** when the test ends (stopped early, time up, or
  closed by another session): a real exam scores them zero. Setting `queue.test_unanswered`
  = "skip" leaves them ungraded instead; the value in force at the start is kept in the
  plan. They are logged as verdict "gave-up" with `extra.unanswered`.

### Self-graded problems

- `show_solution()` shows the solution and rubric before grading (nothing is graded). Then
  `submit` with `rubric_ticked` (clamped; refused without a rubric) or `self_grade`
  (Matched / Minor slip / Didn't get it, also accepted on rubric cards). The rating map
  does the rest (all ticked Good, all but one Hard, fewer Again).

### Also fixed

- `ProblemOutcome.matched_wrong` got the matched wrong answer's step number, while the
  diagnosis flow reads it as an index into the card's `wrong` list. It is now the index
  (single-box cards; a part's wrong answers are the part's own).

## Consequences

- API additions: `StudyService.show_solution`; `SubmitRequest.error_step/reason`;
  `CardView.shown_work/reasons/error_step/cloze/type_answer`; `PartVerdictView.final/
  tries_used`; `SolutionView.rubric/shown_work`; `AttemptResult.find_error`
  (`FindErrorView`); `TestLine.rating`; `TestResult.unanswered/limit_ms`;
  `PlanItem.method`; engine `PartOutcome`, `ProblemOutcome.parts`, `pick_problem(kinds=)`,
  `partial_credit(targets=)`.
- Left open: a flashcard with an `answer` can still be rated by hand (the spec says typed
  and graded automatically); `CardView.type_answer` lets the page ask for typing first.
