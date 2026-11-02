# ADR-0020: Component student model, direct certification and a pace-based planner

- Status: Accepted
- Date: 2026-11-02
- Amends:
  - spec ENG-1 to ENG-19 and QUE-1 to QUE-24 where they conflict;
  - LIB-4, LIB-9 and STA-12 (targets, projection);
  - ADR-0006 (learning design);
  - ADR-0013 (what is fitted);
  - ADR-0014 (rating rules for problems);
  - ADR-0019 items 4, 5 and 9 (integration errors, below-band items, statistical rules).
- Design: `docs/design/student-model.md` v1.1. Review: `docs/design/student-model-critique.md`.
  Research: `docs/research/notes/Student model design/`.

## Context

On 2026-11-02 the owner judged the skill-level FSRS engine "vibes based" and asked for a model designed from research by the coordinator, with these requirements:
- targets for accuracy, difficulty (above a good university's exam) and pace (top-school standard times);
- course pace from very good schools;
- no self-reported error diagnosis;
- mixed sets;
- new material never last;
- daily load as an output, not a cap;
- an optional placement quiz.

A first spec went through an adversarial review: 3 blockers and 11 majors, all accepted in v1.1.

## Decision

1. **Components.** Problems are tagged with every component their solution uses; the pack build enforces it. Background (earlier-course) components have no memory term and a strong prior.
2. **Student model.**
   - Per course component: execution (log-count PFA/Best-LR form with a Bayesian easiness posterior) times memory (FSRS-6 defaults, scaled by a per-student time factor φ).
   - Problem success is the conjunctive product with a slip term and per-tier recalibration.
   - Blame is Bayesian, pinned to a component when the wrong answer matches a known error.
   - Time is lognormal with power-law speed-up and per-skill offsets. Pace means a median at or under the standard time.
3. **Certification from direct evidence.** Milestones and level come from recency-weighted Beta posteriors of first tries at each tier, with the model's prediction as a weak prior (κ0 = 4). They are never certified from model extrapolation.
4. **Planner.**
   - A pace schedule from top-school section hours, with milestones at +7, +21 and +35 days. Exams pull M2.
   - New material first in each session. Missed-milestone work capped at 40% of a session.
   - Growth allowance of 3 a day per skill, stopping after 2 consecutive successes, in a band of [0.70, 0.90].
   - Maintenance by forecast. A reference check every 10th item. Mixed order.
   - Hours to keep pace come from the student's own history.
5. **Refits.**
   - Only s, δ4, the per-tier recalibration, φ, τ and σ_T are refit. Adoption needs a margin and a paired test.
   - Component FSRS weights are not refit in v1.
   - Flashcards keep FSRS and its existing fitting.
6. **Removed:** the error picker, the slip excuse, diagnostic sets, the weak-spot finder, stability core bands, Elo selection, unrated stretch problems, the skill leech count, separate boosters, partial credit and the fixed daily count.

## Consequences

- The engine and the daily plan are rebuilt (wave 1: core/learner, core/plan, sim2; wave 2: integration and UI). The answer checker, card format, storage, crash safety, import and flashcards carry over.
- Shipping is gated on the parameter-recovery test and the truth-model matrix (design 6.1, 6.2).
- Constants graded C are listed in the design's constants table. They are logged and none are auto-tuned in v1.
- The spec (Claude Doc) is updated from the design within this milestone (DEV-17).
