# Model assumption audit (2026-11-02)

Every assumption of the student model (`core/learner`) and the planner (`core/plan`), checked against the research notes and against real learning logs. Each check ends in a verdict and an action. The analysis code is in `docs/research/analysis/`; the numbers below are its output.

## How it was checked

**Data:**

| Dataset | What it is | Used for |
|---|---|---|
| Statics 2011 (CMU OLI) | 331 college students in an engineering statics course; 114k first attempts at problem steps; 85 skills; 13% of steps tagged with 2–3 skills | Learning, forgetting, combination rule, step times |
| XES3G5M (TAL Education, MIT license) | Primary-school math practice; 3,000 of 18,066 students sampled, 924k first attempts, 822 skills, gaps from minutes to months; 12% multi-skill questions | Learning, forgetting at long gaps, combination rule |
| EdNet KT1 (Riiid) | 3,000 TOEIC learners, 491k timed first answers to single questions | Response times |
| Calculus I syllabi | 14 top-30 US courses (`docs/research/notes/Student model design/syllabus_pacing.md`) | Milestone deadlines |

**Two kinds of test:**
1. *Pooled models.* Logistic models with student and skill effects, scored on each student's last 20% of attempts. They show what the data supports in general.
2. *The app's own model.* `core.learner` is run over each student's log from the priors, predicting every first try before seeing it (prequential). Constants are varied one at a time. Each run is scored by log loss, AUC, and log loss after one global recalibration (the app's refit recalibrates per student, so this is the fairer comparison). Calibration is also checked by component count and by the gap since the skill was last practiced.

## Verdicts: student model

| # | Assumption (design section) | Evidence | Verdict | Action |
|---|---|---|---|---|
| 1 | Learning grows with ln(1 + successes) (3.2) | Log form beats linear-per-opportunity in both datasets (Statics 0.481 vs 0.493; XES 0.4546 vs 0.4585 held-out log loss) | Supported | Keep |
| 2 | γ = 0.37 (3.2) | Pooled γ 0.40 (Statics), 0.33–0.46 (XES); the app's model is flat from 0.2 to 0.6 | Supported | Keep |
| 3 | ρ = 0.10: a failure with feedback teaches (3.2) | The app's model is better at ρ = 0 in both datasets; pooled failure coefficients are negative (−0.14, −0.39), which means failures signal a deficit rather than learning | Not supported | ρ → 0 |
| 4 | One learning rate for every student (3.1) | A per-student learning rate makes held-out predictions worse in both datasets (Koedinger 2023: student slope SD 0.015 across 27 datasets) | Supported | Keep |
| 5 | One learning rate for every skill (3.1) | Per-skill learning rates are the largest gain found: Statics 0.481 → 0.468, XES 0.4546 → 0.4524; skill slope SD 0.44 and 0.23 | Wrong | Needs pooled data: per-component learning rate and difficulty in packs (opt-in log export, later) |
| 6 | New skill starts at 65% (3.1) | First-try accuracy 68.6% (Statics, college), 76.4% (XES, primary school); Koedinger 65.4% | Supported | Keep; the refit recalibrates per student |
| 7 | Prior spread, variance 2.0 (3.1) | Skill SD 1.19 (Statics), 0.87 (XES); student SD 0.68–0.85 | Supported | Keep |
| 8 | FSRS-6 flashcard forgetting with φ = 1 (3.3) | Too strong in both datasets: every φ from 4 down to 0.25 predicts worse than smaller ones. With φ = 1 the app's model underpredicts success after 30+ day gaps by 10 points (after recalibration) in XES. φ = 0.001–0.05 is calibrated by gap | Wrong | φ → 0.05 (forgetting 20× slower than flashcards); measured accuracy drops about 4–5 points between short and multi-week gaps, then plateaus |
| 9 | Same-day successes after the first count 0.25 (3.4) | Next-day accuracy is predicted best by weights 0–0.25 (pooled, both datasets); the app's model is flat | Supported | Keep |
| 10 | Slip 5% (3.2) | The app's model is better at 2%; pooled fits put slip near 0 | Too high | Slip prior 0.05 → 0.02 (refit per student) |
| 11 | Variance drift 0.01/day (3.4) | Statics: 0.05 slightly better; XES: see below | Weak evidence | Keep |
| 12 | A problem is the product of its components (conjunctive, 3.2) | After recalibration, multi-skill items are underpredicted by 12 points in both datasets while single-skill items are calibrated. The geometric mean (Π q)^(1/K) fits best in both: recalibrated log loss Statics 0.514 → 0.506, XES 0.490 → 0.481. The weakest-link min is nearly as good. Both datasets tag overlapping skills (a parent and its sub-concept), which a product double-counts | Wrong for overlapping tags; untested for distinct ones | Keep the product: our content rule now requires distinct components. Check calibration by component count on our own data (6.4) and switch to (Π q_k)^(K^−c) if the gap appears |
| 13 | Log time is normal with σ_T 0.45 (3.5) | Residual σ after item and student effects: 0.51 (EdNet single questions); Statics single steps 0.95 (steps of a few seconds); near-normal tails (0.5–0.6% beyond 3 SD) | Supported for whole problems | Keep |
| 14 | Practice speeds students up, α = 0.3 (3.5) | After item and student effects, α = 0.036 (Statics) and 0.030 (EdNet): about 10× smaller. Delaney's 0.25–0.54 is for repeating identical problems | Wrong | α → 0.05 |
| 15 | Students differ in speed (τ, 3.5) | Split-half reliability of a student's speed 0.94 in both datasets; SD 0.32–0.46 log units | Supported | Keep |
| 16 | Learning speeds up as experience accumulates (owner's hypothesis) | No faster learning per practice with more experience once skill slopes are modeled (interaction −0.03 XES, +0.03 Statics). New skills do start a little easier for experienced students (XES +0.11 logits per ln(1 + attempts so far)). No longitudinal study found | Not supported as a rate; small effect on starting accuracy | Don't model now; recheck on our own data |
| 17 | Practiced skills reach the 90% target | Accuracy after 10+ successes with few failures plateaus at 88.6% (Statics) and 88.9% (XES), on the platforms' own mixed items | At the edge | Owner decision: keep 0.90, or 0.85 at tier 4 |

### Speed, added 2026-11-02 (evening, for pace training)

| # | Assumption | Evidence | Verdict | Action |
|---|---|---|---|---|
| 14a | α measured in time order | The Statics loader for #14 read rows in file order, which is not time order for 202 of 333 students. Recomputed in time order: α = 0.035 (was 0.036) | Confirmed | None |
| 27 | One speed-up rate for every student | EdNet, 1,475 students with 40+ timed correct answers: per-student slopes average 0.027 (median 0.020), estimated true SD 0.08 | Students differ | On held-out times (1,300 students, last 20% held out), shrunk per-student rates beat the shared rate only slightly (MSE 0.2892 vs 0.2930) |
| 28 | Speed is a stable all-time average (τ_s as a plain mean) | Held-out times are predicted best by recency-weighted speed (half-life about 50 answers) plus the shared speed-up: MSE 0.2839, against 0.2930 for the shared speed-up alone and 0.2950 for no speed-up (EdNet). Statics agrees: half-life 50 is best (1.652 vs 1.702) | Wrong | Track current speed with recency weighting (v1.4, pace training) |
| 29 | Slow students catch up with practice | EdNet: the slowest third at the start (2.1× the fastest third's time) got 12% faster over their answers, and the fastest third 1%; the gap went from 2.1× to about 1.9× | Not by ordinary practice | Speed has to be trained, not only measured (v1.4) |

Code: `docs/research/analysis/speed_slopes.py` and `speed_heldout.py`.

### Update rule and memory, added 2026-11-02 (night, for the external audit)

The app's model on both datasets, one rule changed at a time (`external-audit-response.md` has the full table and method).

| # | Assumption | Evidence | Verdict | Action |
|---|---|---|---|---|
| 30 | One Newton step with observed information clipped at 0 (3.4) | The information is 0 on 27% of failures in both datasets. Assumed-density filtering (moment matching under the probit approximation) lowers log loss by 0.0077 (Statics) and 0.0121 (XES3G5M) nats per attempt, and by 0.0014 and 0.0015 after recalibration. AUC rises, 84% and 90% of students are better predicted, and the gain holds at every constant tried. Expected Fisher information does not help | Wrong | ADF (design v1.5) |
| 31 | A failed first try starts the memory at Good (3.4) | Starting it at Again is worse in both datasets (0.5344 vs 0.5339; 0.5420 vs 0.5403) | Supported | Keep |
| 32 | A failed try adds soft successes to the components not blamed (3.4) | Removing them changes log loss by under 0.0004 in both datasets | Neutral | Keep (the expected-count form) |
| 33 | A failure attributed to execution still strengthens memory (3.4) | A rule where failures never raise stability scores the same to four decimals | Neutral | Keep |
| 34 | Combination rule (3.2), post hoc | Geometric mean 0.5061, weakest link 0.5064, soft minimum 0.5059–0.5064, product 0.5138 (Statics, recalibrated) | As #12 | Unchanged: check on our own data |

## Verdicts: planner

| # | Assumption | Evidence | Verdict | Action |
|---|---|---|---|---|
| 18 | M1 at +7 days | Homework due a median 5 days after a topic's first lecture (40 topics, range 2–14) | Too late | +5 (done) |
| 19 | M2 at +21 days | First exam covering a topic a median 16 days after its first lecture (n = 19, range 6–33) | Too late | +14, the exam minus the 2-day lead (done) |
| 20 | M3 at +35 days | No direct data; the median gap between midterms is 28 days | Choice | +28 (done) |
| 21 | Growth band 70–90% | Flashcards: retention per minute peaks at 86–94% success (Eglington & Pavlik 2020); nothing for multi-step problems | Untested | Research round |
| 22 | Target above exam level (tier 4) | Desirable difficulties in general; no direct study of training above test difficulty | Untested | Research round |
| 23 | Practice at exam pace | No direct study | Untested | Research round |
| 24 | Interleaving; confusable skills adjacent half the time | Rohrer & Taylor; Brunmair & Richter 2019 meta-analysis | Supported | Keep |
| 25 | A worked example, then blocked first problems | Worked-example and expertise-reversal research | Supported | Keep |
| 26 | The day's items never exceed its plan (6.2 gate) | Simulator: 2 study days in 6 runs exceeded the plan with the real planner | Bug | Fix in the wave 2 planner work (test marked xfail) |

## What the app's model does with all changes

Statics, the app's model end to end:
- **Default constants:** log loss 0.543, AUC 0.659, underpredicting success by 9.4 points before any refit.
- **With φ 0.05, ρ 0 and slip 0.02:** log loss 0.534, AUC 0.664. After recalibration, every gap bin out to 30 days is calibrated within 2 points.
- **With the geometric-mean combination as well:** recalibrated log loss falls further, 0.514 → 0.506. In XES3G5M it falls 0.490 → 0.481.
- **The remaining gap** to the pooled model with per-skill parameters (0.468) is per-skill information that one student's log can't supply.

## What is missing

1. **Per-skill parameters.** Learning rate and difficulty per component are the largest gain in both datasets. Packs can carry them once pooled data exists (the opt-in export), or as authored estimates.
2. **A forgetting model fitted for procedures.** The φ change makes FSRS's curve far gentler. The logs show a drop of a few points over weeks that then plateaus, which is a power-law shape. A fitted procedural curve, for example the PPE family (Walsh et al. 2018), is a v2 candidate. The logs are dominated by short gaps, and exam-relevant gaps are 2–8 weeks, so this needs our own data too.
3. **A starting point that rises with experience.** New skills start a little easier as a student accumulates practice.
4. **Research on the three planner questions** (21–23) and on keeping students practicing.
