# ADR-0014: Honest grading paths and queue parity with Anki (wave 7, grading)

- Status: Accepted. Amends ADR-0006 (stretch, rating map), ADR-0008 (held verdicts, slips,
- Amended by: ADR-0019 (passed step checks count as plain Again; below-band items never train the scheduler; practice-test misses are Again at every tier)
  partial credit), ADR-0009 (follow-ups, redo, flashcards) and ADR-0010 (unanswered test
  problems).
- Date: 2026-11-01
- Source: docs/research/Spaced repetition algorithm gap audit.md ("Skill scheduling holds up
  only if a miss stays a miss", "Prioritized fix list", decisions 1, 3, 4 and 5).

## Decision

FSRS learns pass versus fail from rating > 1, and in this app the grading rules write every
rating. So no rule may turn a miss into a pass, an unseen problem into a miss, or a
reminder-aided answer into a measurement.

### A miss stays a miss (Decision 1)

- A wrong final answer is never Hard. A careless slip or misread within the cap is Again,
  flagged `slip` (`RatingDecision.slip`, `Effects.slip`, `Attempt.extra["slip"]`): FSRS and
  the lapse count see it; Level gets no evidence from it and the leech counter skips it
  (`review_answer(excused=True)` raises `leech_base` by one). No reinforcement problem and
  no ENG-6 pull-forward follow a slip.
- A held miss (ADR-0008) settles as Again whatever its check shows, at the miss's time. It
  is excused (Level and leeches ignore it, as they ignored the Hard it replaces) when the
  check passes (a slip or an integration error) or when a step check fails and the miss is
  traced to the checked skill (which takes its own lapse). A failed check on the problem's
  own skill (above-level, second slip) stays a plain Again. A held miss served again before
  its check is still settled as a plain Again first. A Step 0 miss is no longer released
  by its cued twin (supersedes ADR-0008 reading 2): it is Again at the miss's time, excused
  when the twin is solved (the method choice failed, and that skill gets its Again), plain
  when it is not; the twin's own rating follows the same day.
- A self-graded "Minor slip" is a wrong final answer: Again flagged `slip` (it was Hard).
  A rubric with all but one step ticked stays Hard.
- Stretch problems are unrated, right or wrong (Decision 5: harder problems only as unrated
  stretch). The skill's rated core-band review is owed and comes the next study day
  (a `due_adjust` "not before tomorrow"), never a few items after the stretch's worked
  solution; the queue no longer inserts a same-session follow-up, and only skills due
  exactly today get a stretch, so a review is never moved twice. A review whose problem
  pick had to widen its tiers is still a review (the session passes `stretch=False`).
- Every attempt logs `extra["strict_ok"]` (read as `Attempt.strict_ok`): the final answer
  correct on the first try with no hint, self-graded "matched" or a full rubric; False for
  non-final tries, examples and unanswered problems. The fitter (wave7-fit) reads it.
- `RULES_VERSION` is `2026.11-r2`.

### Unanswered practice-test problems (C5, Decision 4)

`queue.test_unanswered` defaults to "skip": a problem still unanswered when a test ends is
an unrated final attempt (`grading.record_unrated`: verdict gave-up, `extra.unanswered`, no
ReviewEvent, no state change). The zero stays in the test's score. "again" remains as an
opt-in.

### Goal changes (I2, Decision 3: due dates stay live)

- QUE-4 escalation reads the due date cached at review time (`SkillState.due_at`), never the
  live one; rows without one use an R deficit (recall below what the live interval plus the
  longest wait would leave). A live due date that moved earlier than the cached one counts
  from the cached day, clamped to today, so it is never "overdue" because of a goal.
  Example: S = 30 reviewed 45 days ago under Keep (interval 99.5 d) is due today after a
  switch to A (interval 30.0 d) and not escalated.
- `StudyService.preview_goal` returns "This makes N skills due" (N = skills whose live due
  day moves to today or earlier); `set_goal` saves the goal, spreads those skills over the
  next 7 days with the load balancer's weights (a `due_adjust` "not before" its day, keyed
  by the last review) and refreshes every course skill's cached due date.

### Load balancer (I3)

When a review is graded, an interval of 3 to 90 days takes its day inside the fuzz range
with Anki's weights, (1/n)^2.15 * (1/interval)^3 (1 for a day with nothing due), drawn
with a seed from the skill and its last review. The choice is stored in
`level_evidence["balance"]` keyed by `last_review_at` and by the live unfuzzed interval it
was chosen for; any other review or retention falls back to the hash fuzz.
`SkillContext.load` carries the other skills' due counts and `SkillContext.easy_days` the
Easy Days setting (Engine.grade fills both).

**Easy Days, as Anki 26.09.3 does them.** The audit's rule (Reduced multiplies a day's weight
by 0.5, so "all weekdays Reduced give the same load as all Normal") is not what Anki does,
and was not adopted. Anki (`rslib/src/scheduler/states/load_balancer.rs`) maps a weekday's
load share to Normal (1.0), Minimum (0.0) or Reduced (anything else) (:43-51), whose
modifiers are 1, 0.0001 and 0.5 (:54-62); `calculate_easy_days_modifiers` (:324-357) then
turns each Reduced day in the fuzz range into Minimum when its count / 0.5 exceeds the
other days' count per remaining load share, else Normal; and a day with nothing due weighs
1.0 whatever its setting (:425-426). `lifecycle.easy_days_modifiers` and `balance_weight`
reproduce this, with `queue.easy_days` (weekday -> load percent: 100 Normal, 0 Minimum,
else Reduced) feeding the balancer at grading and the goal-change spread. Easy Days no
longer lower the day's problem count: Anki has no such cut (its limits are untouched), and
the cut only built a backlog.

### Redo (I4)

A redo repeats one known problem, which measures item memory. `purpose="redo"` is graded
as unrated reinforcement unless the skill is due. When it is due, triage plans a fresh
problem as the rated review (`rel:`/`rev:`) and the redo after it (anchored, gap 2), so the
redo is graded once the skill is no longer due; a redo left alone while due is rated as
before (nothing fresher was served). The spec's timing conflict is settled as built: a
confident miss is redone the next study day, an unsure one 3 days later (ENG-3's "next
study day" for confident errors; "3 to 7 days" reads as the unsure case's lower end).

### Flashcards (I5)

- A lapse is an Again on a card in review on a new study day (Anki `review.rs`
  `answer_again`); Again while relearning or a second Again the same day is not one.
- Leech cards are not served; `TodayView.flashcards_to_rewrite` counts them and the rating
  that makes one says it needs a rewrite (`AttemptResult.message`). Anki suspends them.
- The plan offers M minus the flashcards done today, and new ones only up to
  `daily.new_flashcards` (default 20) minus today's (Anki `limits.rs`).
- A missed card is shown again at least 5 items later in the session (purpose relearn),
  with FSRS's same-day update.
- Flashcards are scheduled with `flashcard_adapter(engine)`: `Engine.adapter_for
  ("flashcards")` when the engine has it (wave7-fit), else the default parameters (shim).
- Flashcards whose skill's section or own deck section is Off are not planned.

### Partial credit (I9)

A target skill gets at most one ENG-7 credit per study day, at the largest weight: a later,
larger offer replaces the day's credit (computed from the stability the day's first credit
started from), smaller or equal ones are skipped. Credit On takes effect only when
`credit_switch` finds the credited recalls (logged at explicit reviews, STA-4) beat the
plain ones on log loss over at least 200 held-out reviews (those predicted with the
parameters in force); otherwise it runs as Shadow and the attempt logs why.

### Problem selection (Decision 5)

`pick_problem(target_p=)`; `Engine.pick_problem` aims rated reviews at the course's desired
retention for the day (0.90 under goal A) and keeps 0.80 for learning phases and stretch.

## Consequences

- API additions (backward compatible): `StudyService.preview_goal`, `set_goal`;
  `v.GoalPreview`; `TodayView.flashcards_to_rewrite`; `PartView.multiple`;
  `PartVerdictView.wrong_step`; `SolutionView.preselect_step`; `Effects.slip`;
  `RatingDecision.slip`; `SkillContext.load`; `CardRef.section_id`; `Attempt.strict_ok`
  (property over `extra`); `grading.record_unrated`; `schedule.goal_change`, `GoalChange`,
  `effective_due`, `escalated`; `lifecycle.balance`, `interval_of`, `easy_days_modifiers`,
  `easy_day`, `with_adjust` (moved
  from diagnosis.verdict, still importable there); `credit.credit_switch`;
  `World.credits_since`; setting `daily.new_flashcards`.
- Simulated slip-only learners now log every slip as Again (about 3 in 4 excused) and never
  become leeches; honest misses lower stability and with it the core band.
- `tests/grader/test_serialize.py`'s intermittent failure was its own sampling: a sample
  point that is exactly a pole (x = -2 for 1/(2*(x + 2))) makes `evalf(subs=)` return
  precision noise that differs between equal forms; such points are now skipped.
