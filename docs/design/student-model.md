# Student model and practice planner (design spec v1.2)

- Status: **Accepted for implementation**, 2026-11-02. The coordinator designed it (owner instruction: the coordinator makes the design decisions; agents gather sources, review and implement).
- History: v1 (f96e77e) went through an adversarial review (`student-model-critique.md`, 400a10a): 3 blockers, 11 majors, 7 minors. v1.1 accepts all of them, with the judgment calls noted where a fix was adapted. The disposition of each finding is in section 11.
- v1.2 (2026-11-02): constants checked against real logs (`model-assumption-audit.md`).
  - slip prior mean 0.02, ρ 0, φ 0.05 and α 0.05;
  - milestones at +5, +14 and +28 days, from top-30 course pacing;
  - refits on evidence rather than every 14 days.

  The conjunctive product is kept for now: it underpredicts multi-skill items in both datasets, whose skill tags overlap. The content rule now requires distinct components, and calibration by component count is checked on our own data (6.4).
- v1.3 (2026-11-02): certification counts accuracy only, and pace is checked by the M2 and M3 sittings against an exam-style block time (3.7).
  - v1.2 counted an M2 or M3 success only when its time was also at or under T*. With σ_T ≈ 0.45, a 0.90 posterior then needs a median near 0.5·T*, which contradicts the pace definition in 3.3.
  - It also revoked a passed sitting at once.
- Supersedes: where they conflict, the skill-level FSRS design in spec ENG-1 to ENG-19 and QUE-1 to QUE-24 (ADR-0020 records this, per DEV-17), and the earlier proposal on branch engine-design (`docs/design/learning-engine.md`), whose simulator stays as background.
- Research: `docs/research/notes/Student model design/` (six notes), plus the earlier notes they cite.
- Evidence grades:
  - **A**: direct evidence in a similar setting.
  - **B**: indirect or analogous evidence.
  - **C**: a design assumption, stated as one, with the check that tests it.

## 0. What the system is for

The owner's definition (2026-11-02): an algorithm-driven practice tool for STEM, later other subjects. It does not teach. It makes practice as effective as the evidence allows: retrieval practice (typed answers solved from scratch), spacing, mixed problem sets, and a few further techniques with good evidence.

For each skill it gets the student to three targets and keeps them there:

| Target | Meaning | Default |
|---|---|---|
| **Accuracy** | The chance of a correct first try, unaided, on an unseen problem. A miss is a miss, slips included | 90%, set per course |
| **Difficulty** | The tier at which that accuracy must hold: above a good university's standard exam, reached by working up | Tier 4 |
| **Pace** | The typical (median) solve time is at or under a standard time derived from top-university exam timing | Section 2.4 |

The course moves at the pace of a very good school. The app shows what keeping up costs this student and never lowers the targets to fit a daily cap. Exam dates are optional.

Two hard-won principles from the review shape v1.1:
1. **Certify from direct evidence, predict with the model.** Milestones are certified from the student's own first tries at the tier in question. The model chooses problems and times reviews. Pelánek & Řihák 2017: the data used and the threshold matter more for mastery decisions than the learner model.
2. **Don't extrapolate a learning curve far past data.** Practice allowances are fixed and evidence-informed. Workload estimates come from the student's own history (Rollinson & Brunskill 2015: models of similar accuracy prescribe very different practice amounts; Doroudi et al. 2017: model-predicted gains of d ≈ 3.7–4.1 were null with real students).

## 1. Architecture

1. **Content model:** components, problems, tiers, standard times and known wrong answers. Authored and checked at pack build.
2. **Student model:** predicts the first-try success and solve time of any problem now or later, and updates after each answer. It is a pure function of the attempt log: the stored state equals a replay (invariant C3).
3. **Certification:** a direct-evidence posterior per skill and tier. It decides milestones and level.
4. **Planner:** decides what to practice, when, and how hard, from the model, the certifications, the targets and the pace schedule.

Flashcards keep FSRS exactly as Anki does (3.9).

## 2. Content model

### 2.1 Components
A **component** is a procedure, rule, fact or setup move that a student can know or not know independently. It is a skill ID in the skills file.

A problem's component set is K_j = {skill} ∪ {uses} ∪ {each solution step's tag}. The pack build makes them agree (content-tools branch). A component is either:
- a **course component**, defined in a section of this course; or
- a **background component**, a prerequisite from earlier courses with an `alg.`, `trig.` or `pre.` prefix, or any skill outside the course's own sections.

Granularity: split a component where its variants fail independently.
- *Evidence:* knowledge-component refinement improved held-out fit on 11 of 11 datasets, with gains concentrated in a few splits (Koedinger, McLaughlin & Stamper 2012). **B** (multi-student data).
- Problems that isolate one component diagnose better (Madison & Bradshaw 2015, simulation). **B**.
- The Calc I map (packs/calc1/skills.md) has 123 course and 39 background components. It separates, for example, the chain rule with a linear inside, a non-linear inside, and nested.

### 2.2 Tiers (difficulty anchors)

| Tier | Anchor |
|---|---|
| 1 | One step, one component (a drill) |
| 2 | Routine homework on one section |
| 3 | A standard exam problem at a good university (MIT 18.01, Berkeley Math 1A, UIUC Math 221 level) |
| 4 | Above the standard exam: combines components across sections, no hint of the method, varied surface form. The default target |
| 5 | Advanced, in optional sections only |

### 2.3 Known wrong answers
`wrong: answer => feedback @step` lines (computed in templates) tie a common error to the component of its step.
- *Evidence:* specific wrong answers diagnosed bugs at 94–99% against 81–90% for right/wrong alone (Lee & Corter 2011: four subtraction bugs, simulated multiple choice, truth coded from the same answers). **B**.
- Bugs are unstable across days (VanLehn 1987; Payne & Squibb 1990), so a match changes probabilities, never a permanent label.
- Packs report tier ≥ 2 problems with no `wrong:` line.

### 2.4 Standard times
T*_j = `time:` if set, else 0.5 + m·steps_j + m·max(0, tier − 3), in minutes, with m = the course's minutes per step (1.5 for Calc I).

Basis: MIT 18.01 exams run 0.50 min per point and 7.1–10.0 min per numbered problem (parts included). A 4–6-step problem gets 6.5–9.5 min. **C**: the formula rests on two anchors for three constants. Steps 2 and 6.3 check m against the student's first timed sets.

Measured time is active solving time: shown to submit, minus pauses, minus a typing allowance of 5 s plus 0.3 s per character of the expected answer (TIME-4).

## 3. Student model

### 3.1 State
**Per course component k:**
- the execution easiness posterior β_k ~ N(μ_k, v_k);
- soft execution counts C_k (successes, discounted within a day) and F_k (failures);
- an FSRS-6 memory state (S_k, D_k, last memory event);
- a practice count n_k, used for speed.

**Per background component k:** β_k ~ N(μ_k, v_k) only. It has no memory term (R = 1) and no counts in the speed model. *Basis:* prior courses, used constantly; modelling them as new fragile memories made the model predict that students forget algebra within weeks (critique 6).

**Shared, per student and course domain:**
- slip s;
- tier offsets δ_4 and δ_5;
- the per-tier recalibration (a_ℓ, b);
- the memory time scale φ;
- time parameters τ, per-skill speed offsets τ_s, σ_T;
- the student offset θ̂ for new components' priors.

**Fixed in v1** (not identifiable from one student; critique 10): γ, ρ, α and δ_5 stay at their priors. After the 6.1 recovery test, δ_4 and φ are fixed too: φ was not recovered at 1,000 attempts and stayed at its prior, and the tier-4 recalibration a_4 absorbed δ_4.

### 3.2 Accuracy

```
η_k    = β_k + γ·ln(1 + C_k) + ρ·ln(1 + F_k)          course components
η_k    = β_k                                            background components
e_k(ℓ) = σ( (μ_η − δ_ℓ) / sqrt(1 + π·v_k/8) )           execution, uncertainty-adjusted
                                                          (μ_η = μ_k + the count terms)
R_k(t) = FSRS-6 retrievability of k at elapsed time φ·(t − last)   (1 for background components,
                                                          and 1 for a course component before
                                                          its first event)
q_k    = e_k(ℓ_j) · R_k(t)
P_raw  = (1 − s) · Π_{k ∈ K_j} q_k
P_j    = σ( a_{ℓ_j} + b · logit(P_raw) )                 per-tier recalibration
```

- **Conjunctive product.** A multi-step problem fails if any step fails, and the product gives exact credit on success and Bayesian blame on failure.
  - Evidence: the Conjunctive Factor Model matched or beat AFM on conjunctive data, and on one real dataset "AFM is essentially performing as a conjunctive model" (Cen et al. 2008, abstract). Conjunctive knowledge tracing, applied to Cognitive Tutor logs, suggested 441 of 1,370 assigned problems may have been unnecessary under the blame-everything rule (Koedinger, Pavlik, Stamper, Nixon & Ritter 2011, abstract read by the coordinator; a log re-analysis, not an outcome trial).
  - **C**: the additive Best-LR / DAS3H family is the better-supported predictor (skills_not_cards §3; Gervet 2020), so it is a baseline in 6.2 and 6.4.
- **Execution × memory.** Execution uses success and failure counts on a log scale (Best-LR and LKT logsuc + logfail, the strongest logistic forms on tutoring data: **A** on their home ground). Memory uses FSRS-6.
  - FSRS-6 on procedures is **C**. With default weights it under-predicts both the forgetting and the spacing benefit in the one math retention study (Rohrer & Taylor 2006; critique 8).
  - Hence the per-student time scale φ (3.6) and the calibration-by-gap check (6.4).
- **Recalibration.** (a_ℓ, b) is Platt scaling against the student's own first tries. It corrects the product's systematic underprediction of strong students (critique 1: 0.936 predicted vs 0.977 observed).
- **Tier offsets.** δ_1 = δ_2 = δ_3 = 0. δ_4 is fitted; δ_5 is fixed.

### 3.3 Time and pace

```
ln T_j = ln T*_j + τ + τ_{s(j)} − α·ln(1 + n̄_j) + ε,    ε ~ N(0, σ_T²)
n̄_j    = mean of n_k over j's COURSE components (background excluded)
median_j = T*_j · exp(τ + τ_s − α·ln(1 + n̄_j))
pace_ok  ⇔  median_j ≤ T*_j
```

- **Pace definition:** the median at or under standard (the owner's "at a pace about what an exam would be"). The v1 product-with-probability definition demanded medians of about 0.5·T*.
- **Alternatives** to offer the owner on the course page: P(T ≤ 1.3·T*) ≥ 0.9, or a 6-problem set finished within its summed T* with probability 0.9, which needs a median of about 0.72·T*. **C**.
- **Updates:**
  - τ_s are per-skill offsets (prior N(0, 0.3²), shrunk toward 0 with κ = 5).
  - α is fixed at 0.05 (audit #14: 0.036 in Statics and 0.030 in EdNet after item and student effects; Delaney et al. 1998's 0.25–0.54 is for repeating identical problems). **B**.
  - τ and σ_T are updated by conjugate normal regression on correct first tries with valid time.
- **No speed forgetting in v1.** Speed decays less than accuracy in skill-decay data (Arthur et al. 1998, by task type; **C**).

### 3.4 Updating from an attempt

**What counts:**
- The observation is the first try, unaided.
- A wrong answer, a hint before answering, a give-up, or the solution shown before answering is a failure.
- Later tries are practice and update nothing.
- An answer the checker marks invalid is not an attempt.

**Before updating,** log P_j, P_raw, each q_k, the blame vector, the role and the flags on the attempt.

**Failure blame.**
```
b_k = (1 − q_k) / (1 − P_raw)      exact under independence; b_k ≤ 1 always
```
- If the wrong answer matched a known error whose step names k*: b_{k*} = κ + (1 − κ)·b_{k*}, and every other k gets b_k = (1 − κ)·b_k (κ = 0.95, **C**).
- A success sets b_k = 0 for all k.

**Memory share** for a course component: m_k = (1 − R_k) / (1 − e_k R_k), the probability that memory failed given that k failed.

**Per course component k ∈ K_j:**
1. **Memory.** The probability the method was recalled is r = 1 − b_k·m_k.
   - Compute the FSRS-6 Good and Again post-states, using the same-day rules if the last event was today.
   - Set D' = r·D_good + (1 − r)·D_again.
   - Choose S' so that R(7 days; S') equals r·R(7 d; S_good) + (1 − r)·R(7 d; S_again). Matching at 7 days, the maintenance horizon, replaces v1's log mix, which was optimistic at short horizons (critique 16).
   - When r is 0 or 1 this is exactly FSRS.
2. **Counts.** C_k += (1 − b_k)·w_day, where w_day = 1 for the component's first success of the study day and 0.25 after that (critique 12; DASH-style short window). F_k += b_k·(1 − m_k).
3. **Execution posterior.** One step on the marginal likelihood at the posterior mean. Here σ means σ(μ_η − δ_ℓ) **without** the uncertainty adjustment, which is for predictions only:
   - **Success:** the likelihood factorizes, so the step is exact: g = 1 − σ, h = σ(1 − σ).
   - **Failure:** L(η) = 1 − A·σ(η), with A = (1 − s)·R_k·Π_{i≠k} q_i (the other components, k's memory, and no slip). The score is g = −A·σ(1 − σ)/(1 − Aσ). The observed information is h = max(0, [u''(1 − u) + u'²]/(1 − u)²), clipped at 0, with u = Aσ, u' = Aσ(1 − σ) and u'' = Aσ(1 − σ)(1 − 2σ) (critique 4: v1's complete-data information made variances up to 11× too small).
   - Update v_k ← 1/(1/v_k + h), then μ_k ← μ_k + v_k·g.
   - Between study days, v_k grows by q_drift·Δdays (0.01, **C**), so the model can follow learning outside the app.

**Per background component:** only the execution posterior (step 3), with its blame.

**Speed:** n_k += 1 for course components. A correct first try with a valid time feeds the time regression and the skill's τ_s.

### 3.5 Starting values

| Quantity | Value | Basis |
|---|---|---|
| β, new course component | mean logit(0.65) = 0.62 + θ̂, variance 2.0 | Koedinger 2023 median first-opportunity accuracy 65.4% (tutoring with hints; datasets above 80% excluded). Widened so experts aren't many SD out (critique 1). **B** |
| β, background component | mean logit(0.97) = 3.48 + θ̂, variance 1.0 | Prior courses passed; a strong default keeps K background terms from capping problems (critique 6). **C**, checked by matched errors |
| γ (success gain on ln(1 + C)) | 0.37, fixed | Fitted so the median learner goes from 65% to 80% in about 7 opportunities (Koedinger 2023). It is not used for long-range extrapolation (section 0). **B** in range, **C** beyond it |
| ρ (failure gain) | 0, fixed (v1.1: 0.10) | **B**: failures did not raise later success in Statics or XES3G5M; the app's model scores better at 0 in both (audit #3) |
| δ_4 | prior N(0.3, 0.3²), refit | **C** |
| δ_5 | 0.7, fixed | **C** |
| s | prior Beta(0.4, 19.6), mean 0.02, refit (v1.1: mean 0.05) | Weak prior (same strength as v1.1) so that a careless student's rate is learned (critique 7). **B**: 0.02 scores better than 0.05 in both datasets (audit #10) |
| a_ℓ, b | priors N(0, 0.5²), N(1, 0.2²), refit | Platt scaling. **B** |
| φ | 0.05, fixed in v1 (prior log φ ~ N(ln 0.05, 0.5²), bounded [0.01, 0.5]; v1.1: 1) | **B**: FSRS's flashcard forgetting is about 20× too fast for procedures; φ 0.001–0.05 is calibrated by gap out to 30+ days in XES3G5M and Statics (audit #8) |
| θ̂ | precision-weighted mean of (μ_k − prior mean) over components with 3 or more attempts, shrunk by n/(n + 20) | Hierarchical shrinkage. **B** |
| FSRS weights | FSRS-6 defaults (py-fsrs 6.3.2); not refit for components in v1 (critique 3) | **A** for flashcards, **C** for components |
| τ | prior N(ln 2, 0.5²), refit | **C** |
| α | 0.05, fixed (v1.1: 0.3) | **B**: practice speed-up after item and student effects is 0.036 (Statics) and 0.030 (EdNet); Delaney's 0.25–0.54 is for repeating identical problems (audit #14) |
| σ_T | prior 0.45, refit | **C** |

### 3.6 Refitting

Refit s, a_ℓ, b, τ and σ_T by MAP (δ_4 and φ are held fixed in v1; 3.1), re-running the filter over the log for each candidate. Score each candidate on the most recent 20% of attempts (a time-series split).

**When** (on evidence, not the calendar; changed 2026-11-02, the earlier "every 14 days or 300 attempts" had no basis): a fit of k parameters on n attempts has an expected excess log loss of about k/(2n) nats per attempt, so a refit pays when the log has grown by a fixed fraction since the last one.
- The first refit once the log holds 150 first tries (30 held out, the minimum to adopt).
- Then when the log has grown by half since the last refit (the stale fit then costs at most 0.25·k/n, under the 0.003 margin from n ≈ 750 with k = 9), or by 1,000 attempts (slow drift).
- At once when the predictions since the last refit fail calibration in the large: |Σ(y − p)| > 3·√Σp(1 − p), with at least 50 of them.
- Whenever the student presses Refit now (the report shows the held-out loss before and after, calibration by tier and gap, and whether the fit was kept).
This gives 7 refits in the first 2,000 attempts (at 150, 225, 338, 507, 761, 1,142 and 1,713), when the priors are most likely wrong for the student, and about one per 1,000 after that.

**Adopt a candidate only if** both hold:
- it improves held-out log loss by at least 0.003 nats per attempt;
- the paired per-attempt differences give a one-sided bootstrap p < 0.1 (as ADR-0019 did for partial credit).

Otherwise keep the current values. This stops noise-chasing (critique 10).

The refit uses plain-Python coordinate search; no numpy, matching the dependencies. It runs on the auto-fit thread with atomic adoption, startup repair and the PanicException catch (ADR-0019).

The component FSRS weights are **not** refit in v1. A refit needs a soft-label fitter: clean-label gating hid 99.99% of lapses in the review's simulation (critique 3). The required later test: a simulated student with known forgetting must not have that forgetting reduced by any refit.

### 3.7 Certification (direct evidence)

For skill s and tier ℓ, keep a Beta posterior over s's first-try success at tier ℓ:
- **Evidence:** first tries on problems whose main skill is s at tier ℓ, from any role, sittings included. A correct first try is a success at every tier; time does not enter the posterior (v1.3).
- **Weighting:** each attempt is weighted by 2^(−age/30 days), so evidence fades and a lapse shows.
- **Prior:** Beta(κ0·p̂, κ0·(1 − p̂)), where p̂ is the model's calibrated prediction for a representative problem and κ0 = 4.

**M1 and Keep are certified** when the posterior mean ≥ the accuracy target and the effective direct observations reach 3.
- *Basis:* mastery criteria based on 3–5 correct answers differ little in retention. In the ALEKS randomized threshold trial, 5 vs 3 changed retention by about 0.02 at 30% more time (Matayoshi et al. 2025, **A**). N-consecutive-correct and EMA thresholds perform close to model-based ones (Pelánek & Řihák 2017, **B**).

**M2 and M3 are certified only by a sitting**, a closed-book timed block of unseen problems (`wave2-planner.md` §2). The skill passes when:
- every one of its sitting problems is correct on the first try, unaided;
- the total active time of those problems is at or under the sum of their T*. This is an exam's rule: a block of problems in the block's time.

A sitting is planned only when the model gives the skill at least a 0.5 chance of passing it, on the chosen problems (product of their P_j, times the chance that the summed lognormal times fit the limit). A student whose median is 0.8·T* (σ_T 0.45) fits 3 problems in their time about 68% of the time; at a median of T*, about 36%.

**Revoked** when the posterior mean falls below target − 0.10 (hysteresis). The skill then returns to growth at that tier. Pace is not revoked: speed decays less than accuracy (3.3).

**Level** = the highest ℓ such that every tier ℓ′ ≤ ℓ that has problems is certified (critique 17).

### 3.8 Representative problems
A skill's representative problems at tier ℓ are its pool problems at ℓ. For display it averages over at most 10 of them, chosen deterministically (lowest IDs after excluding retired cards).

### 3.9 Flashcards, card-only problems, imports
- **Flashcards and cloze cards:** FSRS-6 per card, Anki parity. Desired retention = the course accuracy target, capped at 0.97.
- **A problem with no skill tag:** a single-component problem; its component is the card itself.
- **Imported Anki decks:** unchanged.

### 3.10 Replay
The state is a deterministic function of the attempt log, the pack content at each attempt's card revision, and the adopted parameter versions. Caches are only for speed. C3, the kill loop and the stateful property test (DEV-8, DEV-9) cover it. A pack key fix voids old attempts as now (PACK-14).

## 4. Planner

### 4.1 Pace schedule

**Pace standard.** Each pack's skills file carries one: section hours in course order, weekly class hours and minutes per step (content-tools branch). Calc I uses:
- Berkeley Math 51/1A department hours by chapter: 6, 8, 8, 8, 5 and 3 h for chapters 1–6, at 38 h over 15 weeks;
- divided among sections by their components, and cross-checked against UIUC Math 221 (24–25 lectures, chapters 2–6).

**Student settings:**
- a start date, or "my class is at section X today";
- optional exams;
- optional pace factor (0.75× to 1.5×);
- accuracy target;
- target tier;
- an end date (none for self-study).

**Introduction dates** come from cumulative section hours. A skill is introduced on its section's date once its **course** prerequisites have been introduced. Introduced is enough; they need not be certified. Background components never gate (the component map's blocking issue).

**Milestones per skill** (from top-school cadence):

| Milestone | Requirement | Deadline | Grade |
|---|---|---|---|
| M1 | certified at tier 2 | introduction + 5 days | **B**: the median homework due date, 5 days after a topic's first lecture (40 topics in 3 top-30 Calc I courses; range 2–14) |
| M2 | certified at tier 3 at pace | introduction + 14 days | **B**: the median first exam covering a topic, 16 days after its first lecture (n = 19, range 6–33), minus the 2-day exam lead |
| M3 | certified at the target tier at pace | introduction + 28 days | **C**: the median gap between midterms (28 days), so above-exam level by the next exam |

- An exam pulls M2 (not M3) for in-scope skills to the exam date minus 2 days (critique 18).
- After the course end date, a skill drops to Keep: accuracy target 0.80 at tier 3 (LIB-8 kept).

**Mid-course start** (critique 14): skills in sections before the aligned section start in **Keep maintenance**, assumed learned. Reference checks (4.3) test that assumption, and a failed certification moves the skill to growth. Placement is offered but optional (owner).

### 4.2 Statuses
Each skill is in one of these:
- not yet introduced;
- new (introduced today);
- growth at its current milestone tier;
- maintenance (its milestone certified);
- Keep;
- **limited by careless errors:** every course component's e ≥ 0.97 and the direct posterior still below target, with the shortfall explained by s. No component growth; shown as "check your work";
- **struggling:** 3 study days at the full growth allowance with no rise in the direct posterior. The app shows the textbook reference and adds growth for the prerequisites of its weakest component.

Separately, each skill is ahead, on track or behind against its milestone deadline.

### 4.3 Daily work

**New.** A skill whose introduction date has arrived gets its worked example (the `example` card, or a tier-1 problem shown solved). Then up to 3 tier 1–2 problems in a row (blocked) until the first first-try success. After that it joins the mixed set.
- *Basis:* worked examples g = 0.43–0.48 in math (Barbieri et al. 2023), **A**.
- Low initial criteria plus spaced relearning (Vaughn et al. 2016; Rawson et al. 2018 relearning d = 1.52–4.19; ALEKS 3 vs 5 above), **A**.
- Rohrer, Dedrick & Stershic 2015 blocked each new skill's first problems, **B**.

**Maintenance.** A certified skill whose calibrated readiness at its certified tier, forecast for the next study day, falls below target gets one problem at that tier. This is FSRS "due" generalized.
- With exams, in-scope skills also get the exam date as a forecast horizon.

**Growth.** An introduced, uncertified skill gets up to **3 problems a day** at its milestone tier or the rung below.
- The skill stops for the day after 2 consecutive first-try successes.
- *Basis:* overlearning gives little lasting gain (Rohrer & Taylor 2006, 9 vs 3 problems; ALEKS), and spacing beats massing (Rohrer & Taylor 2006, 2007; Cepeda et al.), **A** for the direction. The numbers 3 and 2 are **C**.

**Reference checks.** Every 10th item is a uniformly random unseen problem at the current milestone tier (or certified tier) of a uniformly random introduced skill. These feed calibration and certification without selection bias.
- *Basis:* Papoušek, Stanislav & Pelánek's every-10th random reference question (Pelánek, Řihák & Papoušek 2016: controlled randomization), **B**.
- Reference checks replace v1's exploration (critique 11).

**Caps and priority:**
- New material is served first in each session, up to its count.
- Missed-milestone growth takes at most 40% of a session's items, so new material is never crowded out (critique 1).
- Maintenance and the remaining growth are interleaved.
- A per-skill daily cap of 3 applies outside Focused Practice.

**Reported, never capped:**
- Today's items and minutes: the sum of each item's predicted median time.
- **Hours to keep pace per week:**
  - from the student's own history: minutes actually spent per certified milestone by tier, times the milestones the pace schedule brings next week, plus maintenance minutes from due forecasts;
  - until about 10 certifications exist, the course's standard outside-class hours stand in. For a 12-unit MIT subject this is about 7 h/week (5-0-7), and 34 CFR 600.2 gives 2 h per credit hour.

No simulated trajectories are used (critique 2).

**Feasibility check at course setup and after each refit:** the best attainable chance on a typical tier-ℓ* problem is (1 − s)·0.99^K̄. If it is below the target, the course page says so, with the numbers.

### 4.4 Choosing the problem

| Role | Choice |
|---|---|
| New | Tier 1–2 problems of the skill, the highest predicted chance first |
| Growth | Problems at the milestone tier or one below, with predicted P_j in the **band [0.70, 0.90]**, preferring problems that contain the skill's **bottleneck**: the course component with the lowest q_k over the milestone-tier pool. After a failure with spread blame (top suspect b < 0.7), prefer a problem containing the top suspect and not the runner-up. If the band is empty, take the problem closest to 0.80 |
| Maintenance | A problem at the certified tier with P_j closest to the target |
| Reference check | Uniform over eligible unseen problems (4.3) |

**Band basis:**
- retention per minute peaked at predicted recall 0.86–0.94 (Eglington & Pavlik 2020, facts);
- the testing effect needs more than 75% initial success without feedback (Rowland 2014);
- the 90% condition learned best in Math Garden (secondary source);
- harder targets learned better in geography, mostly when compared with 95% success (Papoušek et al. 2016);
- the 85% rule is simulation only.

Grade **C** within that range.

**Variety:** no card twice in a study day; no repeat within 90 days when the pool allows; template parameters not repeated within 180 days; a different surface form from the skill's previous problem when possible.

### 4.5 Order (mixed sets)
Items are interleaved across skills. There are no two consecutive items of one skill, except a new skill's example and first problems (4.3). Confusable pairs are placed adjacent with probability 0.5, randomized and logged.
- *Basis:* interleaved math beat blocked (Rohrer & Taylor 2007: 63% vs 20%; classroom RCT d = 0.83, Rohrer et al. 2020; meta-analysis g = 0.34 for math, Brunmair & Richter 2019). **A** for mixing.
- The discrimination mechanism is contested (Rowlandson & Simpson 2024 null). **B** for the adjacency rule.

### 4.6 After a miss (v1.3: the owner's unassisted design, `wave2-planner.md`)
- **Within the problem.** A wrong answer shows "Not quite" and the student may retry any number of times. Only the first try is evidence. There are no hints and no explanations.
- **Give up** shows the full worked solution and counts as a miss.
  - Basis: high-information feedback beats corrective feedback (d = 0.99 vs 0.46; Wisniewski et al. 2020, **B**).
  - Elaborated feedback helps after an incorrect first response and not after a correct one (Attali & van der Kleij 2017, N = 2,445, **B**).
  - Feedback that comes before the student's own attempt hurts later unassisted performance (Shute 2008; Bastani et al. 2025), **B**.
- **A matched wrong answer's** short feedback is shown only with the solution, never during retries. Error-specific remediation was not clearly better than reteaching (Sleeman et al. 1989), so it stays short.
- **Across problems,** the stuck ladder changes the problem rather than explaining (`wave2-planner.md` §1): a smaller problem, then a prerequisite, then the skill is set aside until the next study day.
- **The next-day review** follows from the forecast. A delayed review after an error is what made immediate feedback pay in Attali & van der Kleij 2017.

### 4.7 Placement (optional)
Placement asks problems that contain the most uncertain components in isolation (tier 1–2 first), up to 15 per chapter. Its answers are ordinary observations. Stopping on a variance threshold was dropped (critique 4). **C**.

## 5. Changes to the current app

**Removed (superseded):**
- the error picker (step tap) and the 30-day slip excuse (owner);
- diagnostic sets and the weak-spot finder (ENG-15);
- skill-level FSRS cards, stability core bands, Elo selection, unrated stretch problems;
- the leech count for skills;
- boosters as a separate mechanism (the exam horizon is part of maintenance);
- partial credit in Shadow;
- the fixed daily count and "new skills last" triage;
- the placement walk.

**Kept:**
- the answer checker;
- the card format, with the 2.1–2.4 additions;
- packs and Anki import;
- storage, crash safety, backups, restore and bridge hardening;
- the worked example first;
- flashcards on FSRS;
- practice tests as optional timed mixed sets (ordinary observations);
- calibration statistics, made owner-facing;
- ADR-0019 rules not tied to removed parts.

## 6. Evaluation

### 6.1 Parameter recovery (gate before shipping)
Simulate one student from the model at 300, 1,000 and 3,000 attempts with known values. Refit s, δ_4, (a_ℓ, b), φ, τ and σ_T. Any value not recovered within ±50% at 1,000 attempts is fixed at its prior in v1.

### 6.2 Robustness across truth models (gate before shipping)
Run the planner against simulated students whose truth comes from different models (robust evaluation matrix; Doroudi, Aleven & Brunskill 2017):
- (a) this model;
- (b) an additive Best-LR/DAS3H learner;
- (c) a PPE/ACT-R learner with spacing-dependent decay;
- (d) a learner tuned to Rohrer & Taylor 2006 forgetting;
- (e) slow learners at half rate, and slip 0.12;
- (f) a component map with 10% of tags missing and 10% wrong.

Compare against a baseline: skill-level FSRS with 3 correct in a row and random problems at the target tier.

**Gates:**
- a strong model-truth student certifies M1–M3 by their deadlines;
- new material is always served on its date;
- daily items never exceed the reported plan;
- no truth model makes the planner certify weak students more often than the baseline does.

Report:
- minutes to M3;
- readiness 30 and 90 days after M3;
- the planner's calibration.

### 6.3 Content checks
- Double-tag a 20% sample of the pilot content with an independent tagger and report agreement.
- After launch, test each template family's observed first-try rate against its predicted rate with an exact binomial. Families recur, so one student gives enough data (critique 13).

### 6.4 Live calibration (owner-facing)
- Predicted against observed first tries, by tier, by role, by days since last practice (1, 2–7, 8–30, over 30) and by the number of course components (1, 2, 3+). The days-since split checks the memory term on procedures.
- **The component-count split checks the conjunctive product.**
  - In Statics 2011 and XES3G5M, multi-skill items come out about 12 points below observed after recalibration, while single-skill items are calibrated.
  - In those datasets, P = (1 − s)·Π q_k^(1/K) (the geometric mean) fits best (audit #12). Their tags overlap, though, so the result may not carry over to our distinct components.
  - If our own data shows the same gap, switch to q′_k = q_k^(K^−c), which keeps per-component blame. The failure step generalizes to u = a·σ^w, u′ = w·u·(1 − σ), u″ = w·u·(1 − σ)·(w(1 − σ) − σ), and a success to g = w(1 − σ), h = w·σ(1 − σ).
- Time: predicted median against observed.
- Logged, but not used to tune anything in v1: confusable adjacency, band position, reference-check results (critique 11: one student can't settle them).

### 6.5 Real exams
The student can enter exam scores, and the app compares them with readiness for the exam's scope.

## 7. Constants

| Constant | Value | Grade |
|---|---|---|
| Accuracy target | 0.90, owner-settable | Owner |
| Target tier | 4 | Owner |
| Minutes per step, Calc I | 1.5 (+0.5 to read) | C |
| Milestones | +5 / +14 / +28 days (changed 2026-11-02 from +7 / +21 / +35, from syllabus data); exams pull M2 to exam − 2 | B, B, C |
| Keep after the course | 0.80 at tier 3 | Existing LIB-8 |
| Certification | κ0 = 4; n_eff ≥ 3 (M1, Keep); M2 and M3 by sitting (planned at a predicted pass chance ≥ 0.5; all correct, block time ≤ ΣT*); half-life 30 days; revoke at target − 0.10 | B (thresholds), C (values) |
| Growth allowance | 3 per skill per day; stop after 2 consecutive successes | C (direction A) |
| New skill block | worked example + up to 3 until a success | B |
| Reference checks | every 10th item | B |
| Missed-milestone share | ≤ 40% of session items | C |
| Growth band | [0.70, 0.90]; fallback closest to 0.80 | C |
| Same-day success weight | 1 for the first, 0.25 for later ones | C |
| κ (matched-error confidence) | 0.95 | C |
| Spread-blame trigger | top suspect b < 0.7 | C |
| q_drift | 0.01 per day | C |
| Refit | first at 150 attempts, then log growth ×1.5 or +1,000, calibration drift (z > 3, n ≥ 50) or Refit now; 20% tail; margin 0.003 nats and p < 0.1 | B |
| Pace | median ≤ T* | C, owner can choose another |

## 8. Implementation interfaces (the contract for parallel work)

`core/learner/types.py`, frozen and slotted dataclasses unless noted:

<!-- fmt: off -->
```python
ComponentId = str


@dataclass(frozen=True, slots=True)
class ComponentInfo:
    component_id: ComponentId
    background: bool  # prefix alg./trig./pre. or outside the course's sections
    course_id: str | None


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    problem_id: str  # card id, or "card_id#part"
    card_id: str
    part: str | None
    main_skill: ComponentId
    components: tuple[ComponentId, ...]  # K_j, main skill first, unique
    tier: int  # 1..5
    steps: int
    standard_minutes: float  # T*_j
    wrong_components: tuple[tuple[int, ComponentId], ...]  # (wrong-line index, component)
    family: str  # template id or card id (variety, family checks)


@dataclass(frozen=True, slots=True)
class Observation:
    attempt_id: int  # order key together with at_ms
    at_ms: int
    study_day: date
    problem: ProblemSpec
    correct: bool  # first try, unaided
    aided: bool  # hint / solution / give-up before the first answer
    matched_wrong: int | None  # index of the matched wrong: line
    minutes: float | None  # valid active time of a correct first try, else None
    role: str  # new | growth | maintenance | check | practice-test | focused


@dataclass(slots=True)  # mutable
class MemoryState:
    stability: float
    difficulty: float
    last_ms: int
    last_day: date


@dataclass(slots=True)  # mutable
class ComponentState:
    mu: float
    var: float
    c: float = 0.0
    f: float = 0.0
    memory: MemoryState | None = None
    n: float = 0.0
    attempts: int = 0
    successes_today: int = 0
    today: date | None = None


@dataclass(frozen=True, slots=True)
class SharedParams:
    version: str
    slip: float
    delta4: float
    delta5: float
    calib_a: tuple[float, float, float, float, float]
    calib_b: float
    phi: float
    tau: float
    sigma_t: float
    gamma: float = 0.37
    rho: float = 0.0  # v1.2 (audit #3)
    alpha: float = 0.05  # v1.2 (audit #14)
    q_drift: float = 0.01
    kappa: float = 0.95
    same_day_weight: float = 0.25
    fsrs_weights: tuple[float, ...] = ()  # () = FSRS-6 defaults


@dataclass(slots=True)  # mutable
class StudentState:
    params: SharedParams
    components: dict[ComponentId, ComponentState]
    skill_speed: dict[ComponentId, tuple[float, int]]  # (sum of residuals, count)
    time_stats: tuple[float, float, int]  # running residual mean, M2, count
    theta_hat: float
    last_at_ms: int | None


@dataclass(frozen=True, slots=True)
class Prediction:
    p: float
    p_raw: float
    q: tuple[tuple[ComponentId, float], ...]
    e: tuple[tuple[ComponentId, float], ...]
    r: tuple[tuple[ComponentId, float], ...]
    median_minutes: float
    pace_ok: bool


@dataclass(frozen=True, slots=True)
class UpdateRecord:
    prediction: Prediction
    blame: tuple[tuple[ComponentId, float], ...]
    memory_share: tuple[tuple[ComponentId, float], ...]
```
<!-- fmt: on -->

`core/learner/__init__.py` exposes `class StudentModel`, built from a component catalog (Mapping[ComponentId, ComponentInfo]):
- `new_state(params) -> StudentState`
- `predict(state, problem, at_ms) -> Prediction`: no mutation
- `update(state, obs) -> UpdateRecord`: mutates the state
- `copy(state) -> StudentState`: a deep copy, for what-if questions
- `replay(params, observations) -> tuple[StudentState, list[UpdateRecord]]`
- `refit(observations, current) -> RefitDecision`: candidate, held-out scores, adopted or not

`core/plan/` (pure) exposes:
- `intro_dates(course, settings) -> dict[skill, date]`
- `milestones(skill, intro, settings) -> tuple[Milestone, ...]`
- `Certifier`: Beta posteriors per (skill, tier) from observations and model priors, giving `certified(skill, tier, today)`, `posterior(...)` and `level(skill)`
- `status(...) -> SkillStatus`
- `plan_day(model, state, certifier, course, settings, today, now_ms, served_today) -> DayPlan`: items, minutes, hours to keep pace, behind list
- `next_item(...) -> WorkItem | None`
- `choose_problem(...) -> ProblemSpec`
- `order(...)`

The data types are `Course` (pace standard, skills with pools, requires, confusable, example card), `CourseSettings`, `ExamSpec`, `Milestone`, `SkillStatus`, `WorkItem` (skill, role, problem or example card, expected minutes, priority) and `DayPlan`. Implementations may add fields, but not rename or remove these.

## 9. Implementation plan

**Wave 1, in parallel.** These agents work against section 8:
- (A) **`core/learner`:** the model, the updates (3.4), replay, refit (3.6), and the 6.1 recovery test (slow-marked).
- (B) **`core/plan`:** the pace schedule, certification (3.7), statuses, daily work, problem choice, order and caps, against a fake model for unit tests.
- (C) **`tools/sim2`:** the truth models and the 6.2 gate harness, using the real `core/learner` and `core/plan` as they land (stubs first).

**Wave 2: integration.**
- The user.db schema: course settings, parameter versions, and predictions, blame and role on attempts.
- Grading calls `core.learner`, and the session takes its items from `core.plan`.
- Removals (section 5).
- The functional UI: course setup, today's items and minutes with hours to keep pace, skill status (accuracy, level, pace, milestones), the calibration screen, and a bridge API update.
- Mac run and hand test.

**Content, in parallel:** the pilot section (§4.3), a double-tag audit of a sample, then Chapters 4–5, then the rest.

## 10. Risks
1. **Component tagging decides prediction quality.** Mitigations: build checks, the double-tag audit and template-family residuals.
2. **The forms are untested on math procedures:** the conjunctive form, the composition and FSRS memory (all C). Mitigations: calibration by tier, role and gap; the 6.2 truth-model matrix; the baselines.
3. **One student cannot calibrate individual problems** (about 100 learners per item; Pelánek). Difficulty comes from components and tier.
4. **Maintenance cost at tier 4.** A 5-component problem at 0.90 needs per-component reliability of about 0.985. Keeping a component's next-day R at 0.985 takes about 3.5× the reviews of 0.90 (critique 1). The cost is shown in hours to keep pace, and the owner can lower the target or tier.
5. **Constants graded C** are logged and revisited after real use. None of them is tuned automatically in v1.

## 11. Disposition of the review's findings

| # | Finding | Disposition |
|---|---|---|
| 1 | Milestones unreachable; starvation | Accepted: direct certification (3.7), recalibration (3.2), wider priors (3.5), 40% share cap (4.3), 6.2 gate |
| 2 | Extrapolated quotas and hours | Accepted: fixed allowances, history-based hours, observational struggling rule |
| 3 | FSRS refit learns no forgetting | Accepted: no component FSRS refit in v1; forgetting-recovery test required later |
| 4 | Laplace variance | Accepted: observed information clipped at 0; placement stop changed |
| 5 | Pace too strict, n̄, per-skill speed, T* grade | Accepted: median rule (owner can choose an alternative), n̄ over course components, τ_s, grade C |
| 6 | Background components fragile | Accepted: R = 1, prior 0.97, excluded from n̄ and the bottleneck |
| 7 | Slips make targets infeasible | Accepted: Beta(1, 19), slip-limited status, feasibility check |
| 8 | FSRS on procedures overgraded | Accepted: graded C; φ time scale; calibration by gap; truth model (d) |
| 9 | Grades too high | Accepted: regraded throughout; Best-LR baseline added |
| 10 | Unidentifiable refits | Accepted: γ, ρ, α, δ_5 fixed; margin plus a paired test |
| 11 | Band, exploration, tuning | Accepted: band [0.70, 0.90], reference checks, log-only |
| 12 | Same-day overvalued | Accepted: same-day weight 0.25; cap 3; stop after 2 successes |
| 13 | Tagging checks for one student | Accepted: double-tag audit; family residuals |
| 14 | Mid-course backlog | Accepted: Keep maintenance for earlier sections, verified by reference checks |
| 15–21 | Minors | Accepted: statements corrected (3.4), 7-day matching (3.4), definitions (3.7, 3.8, 4.4), exams pull M2 only, blocked first problems allowed, notes committed |
