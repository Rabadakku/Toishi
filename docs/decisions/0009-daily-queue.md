# ADR-0009: Daily queue and study sessions (M5)

- Status: Accepted (readings 9 and 10 superseded by ADR-0010)
- Date: 2026-11-01

## Decision

`core/queue/` decides what the student does each day and drives every study session. The
planning parts are pure functions over a `Snapshot` (`share`, `triage`, `order`,
`planner`, `guards`, `estimate`, `daylog`); `snapshot.gather` is the only storage read;
`StudyService` (`session.py`) is the storage-bound facade the bridge calls. It uses the
engine (ADR-0006), the diagnosis flow (ADR-0008, its hook grades every answer) and the
checker only through their public APIs, and needs no schema change.

### Grade on continue

A final answer (right, wrong after the last attempt, or Give up) is saved in the session
row and graded when the student continues, picks "What went wrong?" or the session ends:
"too easy" and the picker's choice are part of the rating, and grading once avoids voids.
The saved answer is committed state (QUE-16): a resume shows the same verdict screen, and
a session left open past the rollover is graded with its original time before a new plan
is built. Non-final tries ("Not quite") are logged at once. The engine's commit of the
attempt includes the session row (one transaction); the re-plan is saved right after, and
a crash between the two is finished on the next read from the stored attempt.

### Plans and re-plans

- A plan keeps N problem slots. Follow-ups (reinforcement 5 items after a lapse, a failed
  stretch's core problem 3 after, the diagnosis flow's checks `after_items` after their
  miss, a learning block's extra problem) take the slot of the lowest-priority pending
  item, the same course's first. Freed slots refill from the bench, never with a new skill
  (QUE-5 is decided once a day). A follow-up that can't reach its distance in this session
  is dropped (a check stays pending in storage for the next session).
- Flashcards sit outside N in groups of up to five; a miss moves a planned flashcard of the
  missed skill right after the solution, or adds one while the daily limit allows.
- The triage policy is a named sort key (`triage.POLICIES`, setting `queue.triage_policy`);
  every attempt records it in `triage_policy`.
- Day-to-day memory lives in profile settings (unknown keys are stored as JSON):
  `queue.day_log` (each day's count, need, backlog, quotas; carry-over, QUE-8, QUE-13),
  `queue.vacation`, `queue.diagnosis_day` (Diagnosis.daily() runs once a study day).

### Readings of the spec where it is open

1. Order 4 "being learned now": skills in their learning phase, new skills next in line in
   a Learning-now section, and skills with an Again in the last 7 days.
2. Order 5: boosters due today plus due skills in an exam's scope within 21 days.
3. Mixed check-ups (up to 4 skills) open order 6; vacation pull-forwards follow them.
4. QUE-13 "backlog under one day's quota": the course's due work is under its weight share
   of N (with unlimited demand).
5. Carry-over is reserved on top of the course's share (still inside N) and only after a
   day the student studied: a missed day carries nothing ("no pile").
6. A learning block starts at `correct_in_a_row` + 1 problems, may shrink to fit, grows by
   one while the phase goes on and ends when it passes or fails.
7. Warm-up: two or three plain reviews with an expected tier of 2.5 or lower.
8. Vacation: reviews due in the first half move to the days before it (up to 7 lead days,
   dealt evenly); the second half waits until after; vacation days are empty.
9. Practice tests: the exam's problem count (else 10) of exam-tier problems across its
   scope; timed at the exam's pace (minutes / problems, else 6 minutes each); unanswered
   problems are not graded; one try each, no hints, no picker.
10. Flashcards are scheduled here (FSRS per card, the student's rating; Again relearns the
    next day) because the engine schedules skills only. Cloze cards use blank 0 only.
11. Minutes come from the student's log-median active time per skill and tier, falling back
    to the skill, the tier, then 1.5/2.5/3.5/5/7 minutes for tiers 1-5.
12. Timing guards: active time is bounded by the wall clock since the problem was shown;
    solve plus entry time must fit inside it, else the solve time is dropped so the
    attempt stays out of speed baselines. The engine stores raw and capped times.

## Consequences

- A month with three courses and two exams (`tests/queue/test_simulation.py`, marked slow)
  keeps quotas summing to N every day, starves no course, and lands every check at least 3
  and every reinforcement at least 5 items after its miss.
- The web prototype's types (`web/src/lib/types.ts`) differ in places (reason kinds, ids,
  timing fields); the bridge step maps them.
