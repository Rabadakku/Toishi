# ADR-0008: Error diagnosis (M4b)

- Status: Accepted
- Date: 2026-11-01

## Decision

`core/engine/diagnosis/` plugs into the scheduling core (ADR-0006) as one `GradeHook`
(`DiagnosisHook`) plus a daily run (`Diagnosis.daily`). Everything an answer changes goes
into its own `GradedAnswer`, so one transaction commits it and undo removes it.

### Held verdicts

When a miss is routed to a check (a step tap, Step 0, a second slip, an above-level miss),
the problem's own rating depends on the check, so it is **held**: the skill keeps its
pre-miss FSRS memory and Level, the attempt gets no rating, and the skill is due the next
study day. The check settles it at the miss's own time (Hard on pass; no event when the
blame went to another skill; Again by default). A held skill graded again before its check
is settled with Again first, so FSRS events stay in time order. Settled events carry no
predicted recall (kept out of ENG-11's bins, like stretch problems). This avoids writing an
Again into `review_log` (the optimizer's data) that a passed check would contradict.

### Storage (no schema change)

- Holds, due-date adjustments (ENG-6 pull-forward, forced reviews, "waiting for its check")
  and "worked example first" live in `SkillState.level_evidence`; an adjustment is valid
  only while `last_review_at` is unchanged (`lifecycle.adjusted_due`).
- `PendingCheck` had no text column: each check's reason sentence was stored in the linked
  attempt's `extra["diagnosis"]["checks"]` (`check_reason`, `Diagnosis.reason`); diagnostic
  checks composed theirs from the weak spot. Superseded by ADR-0009: schema v2 stores it in
  `pending_check.reason` (diagnostic checks too); the old location is still read for rows
  the migration could not match.
- Every graded problem logs `extra["diagnosis"]`: tags, Elo prediction, choice, blame,
  check resolution (the tap log), slip decision. ENG-15 reads these.

### Readings of the spec where it is open

1. A step check passing gives the problem's skill Hard; failing gives the checked skill
   Again (the check is its review) and the problem's skill **no event** (ENG-6 spirit:
   never cut an encompassing skill), due no earlier than the next day.
2. Step 0's cued twin is a problem of the same skill shown cued: solved, the method-choice
   skill gets Again and the twin's own rating is the skill's review; unsolved, the twin's
   Again is the lapse and a worked example comes first.
3. Above-level misses (predicted success < 0.35) with "can't tell" or no choice get a check
   on the problem's skill instead of an immediate lapse: pass Hard, fail Again.
4. A rejected slip (skill not strong) is a plain Again without a check.
5. Uncued problems count toward a due method-choice skill as one Good review per day when
   the method was chosen right; Step 0 is left to the cued twin.
6. ENG-15 weights: a success uses tag weights; a miss its blame shares scaled to the same
   total, so a student the model describes has mean-zero residuals. Diagnostic-set
   problems are logged unrated; a confirmed set adds one Again. Sets aim at predicted
   success near 0.85 so a chance dip rarely confirms.
7. "Low-recall" prerequisites: recall < 0.85 or no FSRS card; at most four checks.
8. Unserved checks are cancelled after a week (diagnostic ones stay with their set).

### Engine changes (backward compatible)

`ProblemOutcome.check_of` (stored as `Attempt.check_of`); `lifecycle.adjusted_due` and
`due_note`, applied in `due_day`; `DueSkill.note`.

## Consequences

Simulated learners (tests/engine/diagnosis/sim.py): a hidden prerequisite gap and a
method-choice gap are found within a median of 4-5 problems; a student who only slips
keeps his skills; a student the model describes is flagged in under 5% of skill-months.
