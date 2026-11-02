# Student model and planner: adversarial review of spec v1

- Reviewed: `docs/design/student-model.md` (commit f96e77e; 4ec1a4e adds working notes only),
  2026-11-02, by an independent reviewer.
- Read: the six notes in `docs/research/notes/Student model design/` (including the now-complete
  `evaluation_and_policies.md`), `skills_not_cards.md`, `learning_science.md`,
  `science_of_practice.md`, ADR-0019 and `core/engine/fsrs_adapter.py`.
- Method: enumeration, numerical integration and simulation in Python with py-fsrs 6.3.2 (FSRS-6
  defaults). Simulations implement 3.4 as written (soft counts, Laplace step, drift 0.01 a day,
  probit adjustment, 3.5 priors, s = 0.03, δ₄ = 0.3), with R = 1 and no time unless stated, which
  favours the spec. The scripts stayed outside the repo.

**Summary.** The core probability is right. The blame formula, the memory share and the gradient
of the Laplace step are exact; the probit adjustment is within 0.004 of exact; P(T ≤ T*) is
algebraically correct. The trouble is what is built on them. Under the spec's own priors
and product, no student can be certified at any milestone by its deadline, not even one who
already beats the target. The planner's workload forecasts extrapolate a learning curve far past
any data. The planned FSRS refit would learn that nothing is forgotten. Together these make the
planner starve new material. Three blockers and eleven majors follow. Most fixes make v1 smaller.

## Blockers

### 1. Milestones cannot be reached in time, even by a student who already meets the target, and missed milestones starve new material
**Evidence.**
- **M1** (tier 2, deadline +7 days, cap 5 a day, so 35 problems at most). Each problem has one of
  the skill's two components and one background component. A student whose true first-try rate is
  0.988 is certified after 65 problems (13 days at the cap). One at 0.922 needs 80 to 120.
- **M3** (5-component tier-4 problems, deadline +35 days, so 175 problems at most). A student
  truly at 0.956 needs 363 to 432 tier-4 attempts at 3 a day. With a course-component prior of
  logit 0.9 it is still 228 to 294. A student at 0.985 waits about 110 days.
- **Direct test.** An exact binomial test of "p > 0.9" on the same first tries certifies at a
  median of 29 attempts when the true p is 0.985, and 61 when it is 0.956. The model needs 4 to 11
  times more evidence than the raw data.
- **Bias.** The model also underpredicts strong students: 0.936 predicted against 0.977 observed.

**Causes.**
- With s = 0.03, P_j ≥ 0.9 needs every component at 0.975 (K = 3), 0.985 (K = 5) or 0.991
  (K = 8).
- Course components start at logit 0.62 with SD 0.82, which puts an expert 4 to 8 SD out.
- Background components start at 0.866 after the adjustment, so two of them alone hold a problem to
  0.73 (0.786 at zero variance) until successes raise them. A tier-4 problem with three new and
  three background components starts at a predicted 0.10.
- The probit shrinkage compounds over K.
- Memory adds cost but does not bind. Keeping next-day R ≥ 0.985 takes 14 reviews per component in
  105 days (3.5 times the load at 0.90). R ≥ 0.995, which a component needs when execution is 0.99,
  takes 34 (8.5 times), above the working notes' estimate.

**Consequence.** Every skill misses M1. Missed milestones are priority 1 (spec 4.3), up to 5 problems a
day each, with no limit on the class as a whole. New material (priority 2) is served only after
all of that, which inverts the owner's rule that new material is not last.

**Fix.**
1. Certify milestones from direct evidence. Use a Beta-binomial or exact test on first tries at the
   milestone tier, taken from reference checks (finding 11). Pool tier 4 across a unit, like an
   exam. Keep the model for choosing problems.
2. Recalibrate predictions per tier, P′ = σ(a_ℓ + b·logit P), fitted on the student's own first
   tries with priors a = 0 and b = 1.
3. Widen the β priors (variance of at least 2).
4. Cap missed-milestone work at a share of each session (for example 40%) so new material is
   always served.
5. Gate shipping on 6.2 showing that a model-truth strong student reaches M1 to M3 by their
   deadlines.

### 2. Quotas, weekly hours, the stopping value and the struggling rule run on an extrapolated curve
**Evidence.**
- **What drives the forecast.** In the model's own predictive process, which 4.3 has the planner
  simulate, μ_k is a martingale. Only the count terms, the shrinking v and FSRS move
  forecasts.
- **The count term.** With γ = 0.37, lifting a component from 0.65 takes 70 successes to reach
  0.90, 534 to reach 0.95 and 6,923 to reach 0.98. Koedinger et al. 2023's linear rate (median
  0.09 logit per opportunity) reaches 0.985 in about 40 opportunities.
- **Where the curves were matched.** The log and linear forms were matched only between 65% and
  80% (spec 3.5). No note reports data above about 90%, yet the targets need 98.5% per component.
- **Forecast numbers.** Over 40 Monte Carlo paths of the model's own process (one fixed problem
  composition, execution only), the median N_s is 218 problems for M1, 816 for M2 and 2,140 for
  M3. Sixteen paths never reach M3 within 3,000 problems.
- **Effects.** Every skill in growth sits at the cap of 5, and weekly hours read in the hundreds.
  The struggling-skill rule ("twice its forecast count") never fires.
- **The notes already warn against this.**
  - Rollinson & Brunskill 2015: models of similar accuracy prescribe very different practice
    amounts (AFM stopped at once on 59% of skills, BKT on 6%).
  - Doroudi et al. 2017: a model-predicted d of 3.7 to 4.1 became a null result with students.

**Fix.** v1 derives no quota or hours figure from simulated trajectories.
- Growth gets a fixed allowance (3 a day). Maintenance uses due dates.
- Weekly hours come from the student's history: minutes spent per milestone actually certified,
  by tier.
- The struggling rule uses observations: for example, three study days at the allowance with no
  rise in the direct-evidence posterior.
- The simulator stays offline (6.2).

### 3. The component FSRS refit would learn that nothing is forgotten
**Evidence.**
- **The gate.** Section 3.6 keeps every success as a clean Good, but a failure only when
  b_k·m_k ≥ 0.9. Enumeration confirms that b_k·m_k = (1 − R_k)/(1 − P_j).
- **When a failure passes.** On a single-component problem with perfect execution and s = 0.03,
  only when R_k ≤ 0.79. At e = 0.95 it needs R_k ≤ 0.59. With more components it is rarer still,
  and the planner keeps R near 0.99.
- **Simulated mix** (K from 1 to 5, e from 0.7 to 0.995, R from 0.75 to 1). Of 390,728 component
  events from failed problems, 3 passed the gate. About 75,000 true memory lapses were hidden in
  those events. The fitter would see a lapse rate of 0.001% against a true 12.5%.
- **Result.** The fit predicts almost no forgetting, an adopt-if-better test scored on such events
  would favour it, and R enters every prediction.

**Fix.**
- Do not refit component FSRS weights in v1.
- Later, refit only on events that are unambiguous in both directions, such as single-component
  tier-1 items, or write the soft-label fitter.
- Add a test: a simulated student with known forgetting must not have that forgetting reduced by
  the refit.

## Majors

### 4. The Laplace step overstates what a failure tells
**Evidence.**
- **The mean step is exact.** g = −P(1 − e)/(1 − P) equals the marginal-likelihood score (Fisher's
  identity, checked numerically).
- **The variance step is not.** h = (w_s + w_f)·e(1 − e) is the complete-data information. The
  observed information of a failure, −d²/dη² ln(1 − Aσ(η)) with A = P_j/e_k, is near zero or
  negative whenever slip or other components can explain the miss:
  - at e = 0.65 with two companions at 0.85, the exact value is −0.002 against h = 0.228;
  - at e = 0.9 in a 5-component problem, it is −0.089 against 0.090.
- **Successes factorise and are exact.**
- **Test case.** Two components that always appear together, seen 150 times, compared with an exact
  2-D grid posterior. The filter's variance is 0.029; the exact marginal is 0.32, 11 times larger.
  Even clipped exact information gives 0.060, because the mean-field filter drops the negative
  correlation between the two components.

**Consequences.**
- The uncertainty adjustment is weakest exactly where uncertainty is largest.
- Placement stops (v_k < 0.25) after about 12 co-occurring items, while the exact variance is still
  about 0.4.
- θ̂'s weights and the diagnostic choice inherit the error.

**Fix.**
- On failures, use the observed information clipped at 0, or a 1-D Gauss–Hermite moment match.
- Stop placement only when each component has appeared in problems that separate it from its
  companions.

### 5. The pace target is stricter than any exam, and the time model counts practice wrongly
**Evidence.**
1. **Definition.** Readiness needs P_j·P(T ≤ T*) ≥ 0.9 with P_j ≤ 0.97, so P(T ≤ T*) ≥ 0.93 to 0.95.
   At σ_T = 0.45 that is a median time of about half of T* (0.48 to 0.52·T*). The working notes
   reach the same conclusion.
   - If T* is what a well-prepared top student needs (spec 2.4), that student passes with probability
     0.5 and fails by construction.
   - Exams pool time. With six problems and a budget of 6T*, a median of 0.72·T* finishes with
     probability 0.9.
   - Errors in the three-constant T* formula go into σ_T. At σ_T = 0.6 the bar drops to 0.38·T*.
2. **Practice count.** n̄_j is a mean over K_j, so well-practised background components dominate.
   - A never-practised component inside three background components with n = 200 gets n̄ = 150 and
     a predicted P(T ≤ T*) of 0.96.
   - Its slow first times then raise the one global τ and slow every other skill's forecast, a
     sawtooth with each new skill.
   - Under the priors, P(T ≤ T*) ≥ 0.947 needs n̄ ≥ 113.
3. **No per-skill speed.** A student who is slow on one skill is predicted at the global average.
4. **The T* derivation.**
   - AP multiple-choice items are not 1-step drills.
   - Tier 3's anchor is an exam problem part, but 7.1 to 10.0 minutes is per numbered problem,
     parts included.
   - "Both match" is two data points for three constants.
   - No note joins lognormal times with practice speed-up, and Delaney's slopes are mental
     arithmetic, so the combined model is C, not A or B.

**Fix.**
- Give the owner these numbers and let the owner choose the pace definition. Candidates: median time ≤ T*;
  P(T ≤ 1.3·T*) ≥ 0.9; or a timed mixed set finished within its summed T*.
- Compute n̄ over the problem's own course components only (or as their minimum).
- Add per-skill speed offsets, shrunk toward τ.
- Grade T* C and check m_course against the first timed practice test.

### 6. Background components are modelled as new, fragile skills
**Evidence.**
- Their prior of 0.90 caps products (finding 1).
- Their first event creates a new FSRS card (S₀ = 2.31 days), with R = 0.81 after a week and 0.67
  after a month. The model predicts that the student forgets algebra in weeks, and maintenance
  chases it.
- They appear in almost every problem. That inflates n̄ (finding 5) and makes them a bottleneck that
  no problem isolates.

**Fix.**
- Background components get no memory term (R = 1) and either a high prior (at least logit 0.98) or
  a shared per-problem intercept.
- They take blame mainly from matched wrong answers.
- Exclude them from n̄ and from the bottleneck rule.

### 7. Careless errors make the target infeasible, and the planner cannot tell
**Evidence.**
- With s ≥ 0.10, every P_j stays below 0.9 whatever the practice. ALEKS's median careless rate is
  19% (diagnosis note F7). The spec sets that aside without evidence. Its Beta(1.5, 48.5) prior
  carries 50 pseudo-observations, so refits barely move s.
- Simulated student: components truly at 0.995, slip 0.12. The predicted 0.851 matches the observed
  0.851, because the filter lowers the components. The planner then assigns growth to components
  already at 0.995, and the struggling rule adds their prerequisites. The loop has no exit.

**Fix.**
- Use a weak prior on s (for example Beta(1, 9)), learnt mostly from failures on problems whose
  components are all strong.
- Show the student s and the ceiling it implies.
- When the residual looks like slips, stop component growth and mark the skill "limited by careless
  errors". This is inferred by the model, not self-reported.
- Check target feasibility at course setup.

### 8. The FSRS-6 defaults for procedures are graded A but conflict with the one math retention dataset
**Evidence.**
- No study applies FSRS to procedures (student_models §13).
- Rohrer & Taylor 2006 Exp 1 (permutation problems), with every problem a Good under FSRS-6
  defaults:

  | Quantity | Model | Observed |
  |---|---|---|
  | Massers, 4-week / 1-week ratio | 0.83 | 0.43 |
  | Spacers / Massers at 4 weeks | 1.31 | 2.0 |
  | Spacers / Massers at 1 week | 1.19 | 0.93 |

- The notes hold forgetting models fitted on math and physics tutoring data, and the spec uses
  none of them for this term:
  - decayed PFA on McGraw-Hill math: AUC 0.768 against 0.698 for PFA;
  - DAS3H time windows: 0.826 against 0.744 for PFA on algebra05;
  - PPE: best on Andes and KDD, and the only model consistent with spacing-accelerated relearning.
- Donovan & Radosevich found spacing effects of only d = 0.07 to 0.11 for complex tasks.

**Fix.**
- Grade the component memory term C.
- Keep FSRS if it ships faster, but compare it with a decayed-success or time-window term in 6.2
  and on held-out data in 6.3.
- Quantify the "reproduces the key findings" claims, or drop them.

### 9. Several A and B grades are higher than their sources support
| Spec claim | Problem | Grade |
|---|---|---|
| Conjunctive product, "A for selection" | Koedinger et al. 2011's numbers appear in no research note, only the pre-research working notes, and are a model-based re-analysis of logs, not an outcome. CFM is an abstract ("not clearly better" on real data). skills_not_cards §3 names additive DAS3H or Best-LR as best supported. | C. Retrieve the paper; add Best-LR as a baseline in 6.3 |
| Lee & Corter 2011 (A) | Four subtraction bugs, simulated multiple choice, truth coded from the same answers | B |
| β prior (A) | Tutoring steps with hints; datasets above 80% initial success were excluded | B |
| ρ prior (B) | Between-group feedback effect sizes cannot become a per-failure logit gain | C |
| γ per student, no component rates | Variance is in components (SD 0.102), not students (0.015): that supports a fixed population γ and argues for the component rates v1 omits | Reword |
| Placement (B) | Kaplan's 0.89 is for 5 attributes, known items, every q-vector in the pool; here about 150 components and 15 problems a chapter | C |
| Time does not decay (B) | Arthur's "speed" and "accuracy" are task types; Tatel & Ackerman is motor skills, abstract only | C |

### 10. One student cannot fit the shared parameters, and adopt-if-better chases noise
**Evidence.** I profiled held-out log loss on the last 20% of 1,000 simulated attempts, with 150
components, true γ = 0.37, true δ₄ = 0.6 and four seeds.
- **γ.** The best value was 0.2 or 0.0 in every seed, never 0.37. The gap between 0.2 and 0.37 was
  about 0.003 nats per attempt, below seed-to-seed variation. The filter's μ updates and drift
  already track learning, so γ is confounded with β drift and pushed toward 0, which deepens
  finding 2.
- **δ₄.** The best was 0.6 in three seeds and 1.0 in one, within 0.001 of each other.
- **s and τ/α.** s is pinned by its prior. τ and α are nearly collinear, because x = ln(1 + n̄)
  varies little.
- **Refit rule.** Adopting any set with a lower tail loss, with no margin, makes the parameters
  random-walk and the displayed statuses jump at each refit.

**Fix.**
- In v1, fix γ, ρ, α and δ₅ at their priors. Refit only s, δ₄, τ and σ_T, and adopt only on a
  paired test with a margin, as ADR-0019 did for partial credit.
- Run 6.1 before shipping.

### 11. The stretch band, exploration and in-app tuning go against the evidence now gathered
**Evidence.**
- **Where the evidence points.**
  - Retention per minute peaked at a predicted recall of 0.86 to 0.94; practice at 0.40 was clearly
    worse (Eglington & Pavlik 2020).
  - Without feedback, the testing effect is g = 0.03 at or below 50% initial success and 0.56 above
    75% (Rowland).
  - Math Garden's 90% condition learned best (secondary source).
  - The 85% rule comes from simulation only.
  - The band [0.60, 0.85] and the exploration floor of 0.40 sit below all of this.
- **Exploration is still adaptive.** Conditioned on the model's predictions, it is not Pelánek's
  random reference question and leaves selection bias at the milestone tier.
- **6.4 cannot work.** It asks one student to settle three questions, one with three arms, but
  telling 0.85 from 0.90 takes about 1,370 rated reviews (evidence review): one question a semester.

**Fix.**
- Use a growth band of [0.70, 0.90], graded C, for 6.2 to revisit.
- Replace exploration with reference checks: one item in ten is a uniformly random unseen problem at
  the milestone tier, for skills within one tier of it. These checks feed calibration and finding
  1's certification.
- 6.4 only logs.

### 12. Same-day practice is over-valued, and the stopping rule reduces to the cap
**Evidence.**
- Execution counts carry no time, so a fourth problem today adds as much execution as one next week,
  and execution never decays.
- For Rohrer & Taylor 2006 Exp 2 (9 against 3 problems in one session), the model gives
  +4.6 points at 1 week and +3.8 at 4 weeks, permanently. The groups scored 69% and 67% at 1 week
  and 28% and 27% at 4 weeks (order not recorded; not significant).
- The ALEKS threshold RCT found about 0.02, narrowing over time (just over 0.04 at most for students
  who started wrong).
- For weak skills the value ratio stays above 1/4, so the rule gives them 5 a day. Those studies
  found little lasting gain from extra same-day practice, novices included.

**Fix.**
- Count only the first success per component per study day fully in C, and later ones at 0.25 (a
  same-day window, as in DASH).
- Lower the cap to 3.

### 13. The tagging-error safeguards do not work for one student
**Evidence.**
- Risk 1 says tagging decides everything, and its check after launch is the LFA curve test.
- LFA used 41 to 318 students per dataset, and Pelánek et al. 2016 found a merged Q-matrix "hard
  to detect".
- Here a component gets a few dozen binary points a semester, and each problem is seen once per 90
  days, so a mis-tagged problem leaves no detectable residual.
- A missing tag sends its failures to the tagged components, which get growth they do not need,
  while the missing component goes unpractised.

**Fix.**
- Double-tag a sample of the pilot content and report agreement.
- Test observed against predicted first-try rates per template family. Families recur, so this is
  testable with an exact binomial.

### 14. A mid-course start or a student far behind creates an unbounded backlog
**Evidence.** "My class is at section X today" dates every earlier skill in the past with its
milestones already missed, and placement is optional. With finding 1, all of that becomes
priority-1 work at up to 5 problems a day per skill.

**Fix.**
- A mid-course start runs placement.
- Earlier skills start in maintenance at the Keep target until the evidence says otherwise.
- Finding 1's session cap applies.

## Minors

15. **Statements to correct.**
    - "Exactly FSRS when b_k is 0 or 1" holds only when b_k·m_k is 0 or 1. At b_k = 1 the weight is
      r = 1 − m_k, which is 0.47 at e = R = 0.9.
    - The "clip to ≤ 1" never binds, because (1 − s)Πq ≤ q_k.
    - Define which e the Laplace step uses, σ_pred, and R for a course component before its first
      event.
16. **Log-mixed S is optimistic at short horizons.** After a gap of 30 days, S = 20 and r = 0.5, the
    collapsed state predicts R = 0.933 at 7 days, against 0.891 for the branch mixture; by 90 days
    they agree. Maintenance decides at 1 to 7 days. Choose S′ to match the mixture's R at the
    planning horizon.
17. **Definitions.**
    - M1 is accuracy-only, but readiness is defined with P_pace.
    - Level can skip a failed lower tier, since a tier-4 pool with fewer tags can outscore tier 3.
      Make Level the highest ℓ with every ℓ′ ≤ ℓ passing.
    - "Representative problems" is undefined.
    - An empty stretch band has no fallback.
18. **Exam entry pulls M3 to the exam.** A skill introduced in exam week gets a same-day tier-4
    deadline. Let exams pull M2 only.
19. **The interleaving rule departs from the cited studies.** Rohrer, Dedrick & Stershic 2015
    blocked each new skill's first four problems. The discrimination benefit is contested
    (Rowlandson & Simpson 2024 null; the IES replication runs to 2027). Allow 2 to 4 blocked first
    problems and grade "never two in a row" B.
20. **Homework elsewhere and breaks.**
    - Homework done outside the app refreshes memory while the model's R decays, so maintenance is
      over-assigned; q_drift adds only 0.14 of variance in two weeks.
    - After a break every maintained skill is due at once, which is acceptable once finding 1's
      session cap exists.
21. **Process.** The cited `Student model design` notes are untracked files in the main checkout
    and are absent from this branch. Commit them before the ADR.

## Simplicity

**v1 can drop** trajectory simulation (finding 2), the component FSRS refit (3), in-app tuning (11),
weekly six-parameter refits (10) and information-maximizing diagnosis. A problem with the top
suspect and not the runner-up does that job, and Doroudi et al. 2017 record a max-information-gain
policy failing with real learners.

**v1 is missing** a feasibility check at setup, direct certification, a session cap on
missed-milestone work, a slip-limited status, an empty-band fallback and a mid-course start policy
(findings 1, 7, 14 and 17).

## Ranked changes

1. Certify milestones from reference checks with an exact or Beta-binomial test, pooled per unit
   for tier 4, and cap missed-milestone work per session so new material is always served
   (findings 1, 11, 14).
2. Remove simulated quotas, hours and forecast-based struggle counts. Use fixed allowances and
   hours from the student's own history (finding 2).
3. Do not refit component FSRS weights in v1, and add the forgetting-recovery test (finding 3).
4. Put the pace definition to the owner with the numbers in finding 5. Fix n̄ and add per-skill
   speed.
5. Remove the memory term from background components, give them a high prior or an intercept, and
   keep them out of n̄ and the bottleneck rule (finding 6).
6. Recalibrate predictions per tier, widen the β priors, and weaken the slip prior, with a
   slip-limited status (findings 1 and 7).
7. Fix the Laplace variance and placement's stop rule (finding 4).
8. Fix γ, ρ and δ₅ at their priors, adopt refits only with a margin, and run 6.1 and 6.2 before
   shipping (findings 1 and 10).
9. Add the same-day discount and a cap of 3, move the band to [0.70, 0.90], and make 6.4 log-only
   (findings 11 and 12).
10. Regrade the evidence, retrieve Koedinger et al. 2011, add Best-LR and a decay-term alternative
    to 6.2 and 6.3, and commit the notes (findings 8, 9 and 21).
11. Double-tag sample content and add template-family residual checks (finding 13).
12. The minors (findings 15 to 20).
