# Student model: coordinator's working notes (pre-research draft, 2026-11-02)

Scratch notes so the reasoning survives a context reset. The spec (student-model.md) supersedes
this file once written.

## Owner's framing (2026-11-02)
- The product: an algorithm-driven practice tool for STEM (later other subjects). It doesn't
  teach; it makes practice as effective as possible: retrieval (typed, from scratch), spacing,
  mixed sets, plus evidence-backed extras.
- Targets per skill: accuracy (chance of a first-try unaided correct answer, settable), difficulty
  (above a good university's standard exam, worked up to), pace (standard time based on data,
  "what a top student needs"). No "mastery" wording. A miss is a miss: slips count.
- Pace of the course comes from very good schools; exam dates are optional. Daily load is an
  output ("keeping pace needs X hours"), not a constraint that lowers standards.
- No step tap and no separate diagnostic sets: diagnosis comes from the model and the answer.
  New material is not last. Sessions are mixed sets. Placement is optional.
- Time matters. Ship the core app and Calc I content; no big ML training now.

## Leaning decisions (to confirm against the gathered research)
1. **Components** = skills in the skills file. A problem's components = skill + uses + step
   tags (union; the pack build enforces that they match). The model is component-level; the
   student sees skills/sections.
2. **Conjunctive across components:** P(problem correct) = c * product over components of p_k.
   Success is clean evidence for every component; failure blame is Bayesian:
   b_k = (1 - p_k) / (1 - c * prod p_i). A wrong answer matching a known error at step s pins
   the blame on that step's component, and counts as success evidence for the others (the
   known wrong answers are computed by applying one error and doing everything else right).
   Evidence: conjunctive knowledge tracing (Koedinger, Pavlik, Stamper, Nixon & Ritter 2011:
   blaming every component after an error caused thrashing; about 1/3 of the problems assigned,
   441 of 1,370, may have been unnecessary); CFM (Cen et al. 2008); bug libraries.
3. **Component strength:** p_k(t) = sigma(theta_k - delta_level) * R_k(t).
   - theta_k = execution (acquisition), with uncertainty. It drifts up with practice
     (state-space learning: a learning gain per opportunity, Koedinger 2023 prior of about
     0.09-0.1 logit per opportunity), with diminishing same-day gains (log(1+n) per day;
     overlearning evidence: Rohrer & Taylor 2006, ALEKS 5-vs-3 correct gave +0.03 that faded).
   - R_k = FSRS-6 retrievability of the component's method (default parameters, fitted on
     about 10k users), updated by component events (soft mixture by blame).
   - Memory vs execution split on a failure: P(memory failed | k failed) =
     (1 - R)/(1 - sigma*R).
4. **Time:** lognormal: log T = log T*_j + speed_student + novice offset - alpha*log(1+n_eff)
   (power law of practice = Wright's law). Pace target: P(correct within T*) =
   P_j * Phi((log T* - mu)/sigma). Time never relabels right/wrong.
5. **Levels:** tiers 1-5 anchored to a good university's standard exam (3 = standard exam
   problem, 4 = above-exam target, 5 = optional advanced). delta_level is a shared per-course
   offset learned from data (prior small).
6. **Policy (scheduler)**, derived from predictions:
   - **Pace schedule:** section intro dates from top-school calendars. Milestones: standard
     level by about +1 week (pset cadence), target level by about +4 weeks (unit-exam cadence),
     or the entered exam date. Then maintenance.
   - **Daily work** = maintenance (forecast below target before next study day) + growth (to
     hit milestones; problems needed from the learning curve, spread over days) + new (intro
     date reached). Output: today's problems and minutes, and the weekly hours to stay on pace.
   - **Problem choice:** maintenance at target level; growth in a stretch band (about 0.6-0.85,
     research pending) on the ladder, aimed at the bottleneck component; diagnosis by
     information gain when the blame is uncertain; exploration epsilon about 0.1 (avoids
     adaptive-selection bias and allows in-app tuning).
   - **Mixed sets:** interleave across skills. A new skill's first problems come right after
     its worked example.
   - **Stopping:** marginal durable value per minute vs the next best item. Emerges from the
     diminishing same-day gains and FSRS's small same-day stability gains (successive
     relearning shape: criterion in session 1, then spaced relearning).
   - **After a miss:** the worked solution, specific feedback when the wrong answer matched, a
     retry later in the session targeting the suspected component, and the real relearning on
     a later day.
7. **Flashcards:** FSRS per card, Anki parity, unchanged.
8. **Evaluation:** calibration (predicted vs actual), held-out next-attempt prediction vs simple
   baselines (FSRS on the skill alone, Elo alone, constant), robust simulation across several
   truth models (Doroudi et al. 2017), small randomized variation for the band and the stopping
   rule, and real exams.

## Implementation decomposition (draft)
- T1 model core: component state, prediction, updates with blame, replay from the attempt log,
  priors.
- T2 time model and standard times.
- T3 planner: pace schedule, daily work, required hours, problem choice, ordering, stopping.
- T4 storage/migration.
- T5 integration and removal of superseded features (error picker, diagnostic sets, leech
  counts, boosters folded into maintenance, stability bands).
- T6 functional UI: pace setup, today's plan in minutes and hours, skill targets, calibration
  view.
- T7 content tools: component and wrong-answer checks, standard times.
- T8 robust simulator.

## Content decision (taken while the owner is away)
Calc I content comes from open-licensed sources (CLP-1, OpenStax Calculus Vol 1, WeBWorK OPL,
APEX; all NC-compatible with a CC BY-NC-SA 4.0 pack), adapted into our format with machine-
checked keys. Original problems fill the gaps. Owner rule respected: shipped content is
open-source/permitted only; private banks stay out.

## Self-found issues in spec v1 (before the critique returns)
1. **The pace target as written is far too strict.** P_pace = P_j * P(T <= T*) held at the same
   accuracy target p* (say 0.90) forces P(T <= T*) >= about 0.95. With sigma_T = 0.45 that means
   a median time <= 0.48 T*: twice as fast as the standard. Fix: the pace target is on the
   **median** predicted time (median <= T*, i.e. tau - alpha*ln(1+n) <= 0), checked separately from
   accuracy. "On target" = accuracy readiness >= p* AND median time <= T*.
2. **Maintenance cost at tier 4.** With 5 components, a 0.90 target and s = 0.03, each component
   needs q >= 0.985, i.e. per-component FSRS retention about 0.985 for the rare components, which
   costs about 3-4x the reviews of 0.90 (earlier FSRS-6 workload simulation: 0.95 1.57x, 0.97 2.18x,
   0.99 5.04x). Components shared by many problems stay stable through use; components unique to
   one skill carry the cost. Keep the owner's target as the default, make the cost visible
   (weekly hours), and have the 6.2 simulation report the cost by target and tier. Option for
   later: maintain at tier 3 with periodic tier-4 refresh before exams.

## Owner question 2026-11-02 13:17: crowded days (planner follow-up for wave 2)
Decision (coordinator):
1. **Steady inflow.** Spread a section's new skills evenly across the section's scheduled days
   instead of introducing them all on its first day. This is the main cause of later clumps,
   and the reason Anki feels smooth (new cards per day).
2. **Early-only load balancing.** A maintenance review may move up to 10% of its interval earlier
   (at least 0 days, at most 7), onto the lightest day of the forecast. Never later, because the
   target is a floor. The existing ENG-19 balancer weights are reused. The step repeats at every
   review, so it creates no later clump: the next due date is recomputed from the real review.
   Cost under FSRS-6 defaults (S = 30, D = 5): a review 10% early gives S' = 81 vs 85, so the
   next interval is about 5% shorter. At 39% early (R = 0.93 vs 0.90) the next interval is about
   20% shorter.
3. **Compression.** When several skills are due on the same day, prefer maintenance problems that
   contain several due components. Each success refreshes all of them, and re-planning after each
   answer drops skills that are no longer due.
4. **A future-due heat map** in stats (polish phase).
