# Response to the external design audit (2026-11-02)

An outside audit of the review document (`Toishi: technical design for review`) listed 44 defects with proposed fixes and answers to the reviewer questions. This note records the coordinator's verdict on each claim. Every claim was checked against the code on `main`, after the wave 2 planner merge. Claims that real data can settle were tested on it.

**Summary.**
- About a dozen claims are real problems. Seven of them change the design (v1.5 in `student-model.md`). The audit's proposed fix was usually not the one adopted.
- About ten are fair complaints about the review document, which was silent or wrong where the code is right. The document is corrected.
- About eighteen are wrong about what the code does.
- Six describe deliberate design choices.
- Five proposals were tested on real logs and not supported: Fisher scoring, starting a failed first try's memory at Again, no success credit on failures, no stability gain on failures, and the soft-minimum combination.

## How the claims were tested

- **The app's own model on real logs.** `core.learner` was run prequentially (every first try predicted before its update) over two datasets: CMU OLI Statics 2011 (331 students, 113,992 first tries) and XES3G5M (1,000 students sampled, 308,501). Structural variants replace one rule each. Scores:
  - log loss, raw and after one global recalibration (Platt);
  - AUC;
  - a student-clustered paired bootstrap (2,000 resamples) for the differences.
- **Pace numbers.** Fenton-Wilkinson, the formula `core.plan.sitting.pace_chance` uses, checked by Monte Carlo (400,000 draws) at σ_T = 0.45. The two agree within 0.002.
- **The refit trigger's false-alarm rate.** A perfectly calibrated model's predictions, looked at after every attempt from the 50th on, 20,000 runs.
- **M1 counts.** The real model and the certification rule on a simulated run of straight successes, 2 a study day.
- **Code.** `docs/research/analysis/` (scripts, and where to get the data).

## Results of the data tests

| Variant (audit item) | Statics: log loss, recalibrated, AUC | XES3G5M: log loss, recalibrated, AUC | Verdict |
|---|---|---|---|
| Current model | 0.5339, 0.5138, 0.664 | 0.5403, 0.4897, 0.644 | (baseline) |
| Fisher information on failures (1.7) | 0.5327, 0.5142, 0.663 | 0.5392, 0.4901, 0.643 | Not adopted: no gain after recalibration, lower AUC |
| Assumed-density filtering (1.7, Q3) | 0.5261, 0.5124, 0.667 | 0.5282, 0.4882, 0.646 | **Adopted (v1.5)** |
| First failure starts memory at Again (1.3) | 0.5344, 0.5140, 0.664 | 0.5420, 0.4899, 0.644 | Not adopted: worse |
| No success credit on failed tries (1.4) | 0.5342, 0.5137, 0.664 | 0.5406, 0.4897, 0.644 | Not adopted: no difference |
| A failure never raises stability (1.1, Q2) | 0.5339, 0.5138, 0.664 | 0.5404, 0.4897, 0.644 | Not adopted: no difference |

- **The assumed-density update.** It is better than the clipped Newton step in both datasets:
  - **Raw log loss:** 0.0077 nats per attempt in Statics (95% CI 0.0071 to 0.0084) and 0.0121 in XES3G5M (0.0116 to 0.0127).
  - **After recalibration:** 0.0014 (0.0012 to 0.0016) and 0.0015 (0.0013 to 0.0016).
  - **Share of students better predicted:** 84% and 90% raw.
  - **Robustness:** the gain holds at every constant tried, in both datasets: prior variance 1 and 3, γ 0.2 and 0.6, drift 0 and 0.05, and slip 0.05.
    - Raw: 0.005 to 0.016 nats per attempt.
    - After recalibration: 0.0010 to 0.0018.
    - AUC is higher at every setting, and every interval is above zero.
- **The clipping the audit pointed at is common.** The clipped observed information was 0 on 27% of failures in both datasets (8,410 of 30,728; 20,133 of 73,103).
- **Combination rules (Q1), post hoc on the base run's q_k, recalibrated log loss in Statics:**

  | Rule | Log loss |
  |---|---|
  | product | 0.5138 |
  | geometric mean | 0.5061 |
  | weakest link | 0.5064 |
  | the audit's soft minimum (β = 2, λ = 0.25) | 0.5064 |
  | the best soft minimum on a grid (β = 2, λ = 0) | 0.5059 |

  Every alternative beats the product equally on these logs, whose tags overlap. Nothing favours the soft minimum over the geometric mean, which keeps the existing derivative formulas (6.4).

## Pace and sittings

| Median solve time / standard time | 3-problem block within its summed time | 6-problem exam finished in time | Share of a 6-problem exam completed |
|---|---|---|---|
| 0.72 | 0.84 | 0.90 | 0.98 |
| 0.78 | 0.75 | 0.81 | 0.96 |
| 0.80 | 0.72 | 0.77 | 0.95 |
| 0.90 | 0.56 | 0.55 | 0.89 |
| 1.00 | 0.40 | 0.33 | 0.82 |
| 1.25 | 0.14 | 0.05 | 0.66 |

- At the v1.3 pace rule (median = T*), a student makes a 3-problem sitting's time 40% of the time. The predicted pass chance can then never reach the 0.5 needed to sit. The audit is right that the stated pace standard and the sitting contradict each other.
- The audit's fix, a limit of 1.25·ΣT*, would make the sitting as lax as the rule. A student at that pace finishes a 6-problem exam in time a third of the time and completes 82% of it. With 1.25·ΣT*, the time part at a median of T* is 0.72, not the 0.80 the audit states.
- Adopted (v1.5): define pace from the exam, as finishing an exam-length set in its time with probability at least 0.8. That is a median of about 0.78·T* for 6 problems (0.75 for 3, 0.81 for 10). The sitting stays as it is.
  - A student exactly at the accuracy target and this pace passes a 3-problem sitting with probability 0.73 × 0.75 ≈ 0.55. That is what a pass/fail test should give a student exactly at its threshold.
- The review document's own numbers for the block were wrong: 72% and 40%, not 68% and 36%.

## Verdict on each claim

| # | Claim | Verdict | Evidence | Action |
|---|---|---|---|---|
| 1.1 | The memory share treats a failure at high R as ~97% recall and raises stability | Accurate, by design | r = 1 − b·m is the probability the method was recalled; the failure is put on execution. Making failures never raise stability changed nothing (table above) | Document the semantics |
| 1.2 | The 7-day horizon conflicts with φ (140 days vs 0.35) | Wrong | `horizon = 7 × φ`: 7 calendar days, 0.35 FSRS days (model.py) | Document |
| 1.3 | A first failure starts memory at S0(Good) | Accurate | Starting it at Again instead was worse in both datasets | Keep |
| 1.4 | C_k grows on failed tries | Accurate, by design | Expected successful executions, an EM soft count. Removing it changed nothing | Keep; document |
| 1.5 | The Newton step ignores the κ pin | Wrong | The step mixes the matched and ordinary failure steps by κ (model.py, update) | Document the matched-answer update |
| 1.6 | Pinning mixes a marginal vector with a one-hot vector | Wrong | Blame values are marginal probabilities. The marginals of a mixture are the mixture of the marginals, so the mix is exact | None |
| 1.7 | The failure log-likelihood is not concave, so h is clipped to 0 and v freezes | **Right diagnosis** | 27% of failures had h = 0. The proposed Fisher scoring didn't help; assumed-density filtering did | **ADF (v1.5, 3.4)** |
| 1.8 | The gradient lacks a (1 − m_k) factor | Wrong | R_k is inside A, so the exact gradient is already the expected latent execution outcome minus σ | None |
| 1.9 | Learning is double-counted between the μ step and γ ln(1 + C) | Wrong | The filter estimates the student's offset given the learning curve, the standard state-space form. "70 successes" is the prior path of an average student, not what certification needs | Clarify the 70 in the document |
| 1.10 | The loop over components is order-dependent | Wrong | Every term, the blame and the others' product are computed before the loop | None |
| 1.11 | The outer a_4 can't absorb the inner δ_4 across K and R | True, an approximation | δ_4 is fixed; calibration by component count per tier checks the residual | Document |
| 1.12 | The fallback q_k^(K^−c) changes the derivatives | True for when it is adopted | 6.4 already gives the generalized failure step | None |
| 2.1 | The sitting gate blocks on-target students | **True at the stated pace** | Above | **Pace redefined from the exam (v1.5, 3.3)**; the audit's 1.25·ΣT* not adopted |
| 2.2 | The τ prior and shrinkage block early sittings until the first refit | **True** | Before the first refit, an exam-ready student (true 0.70–0.75·T*) needs about 30–50 timed successes on a skill before the gate opens | **τ updated after every timed success (v1.5, 3.3)** |
| 2.3 | α = 0.05 needs about a million problems to close a 2× gap | Arithmetic right, not a defect | That is the data (α 0.030–0.036 measured). Speed is estimated, not assumed to come from practice | 2.2's fix; pace training (v1.4) |
| 2.4 | M1 needs 8–17 successes at p̂ = 0.70 | Wrong | p̂ is the current forecast and rises with each success. A new single-component skill certifies after 4 straight successes (2 study days); with 2 or 3 new components, 6 or 8 | None. A related problem the audit missed is below |
| 2.5 | Recency decay pulls the posterior to p̂ and revokes passed sittings without errors | **True** | The model under-predicts success after 30+ day gaps by 4–6 points even after recalibration, so time-driven revocation mostly hits students who are fine | **Certification changes only on days with new evidence (v1.5, 3.7)**; event-index discounting not adopted |
| 2.6 | Tier 1 has no milestone, so level stays 0 | Wrong | An untested lower tier neither counts nor blocks (certify.py, level) | Fix the document's level rule |
| 3.1 | Fitting on the whole log leaks the held-out part | Wrong | The candidate is fit on the first 80% only (refit.py) | Document |
| 3.2 | Re-running the filter for (a, b), τ, σ_T is redundant | Already done | Replays are cached by (s, δ_4, φ); (a, b) are scored on cached logits; time needs no replay | Document |
| 3.3 | No adoption metric for τ, σ_T | Wrong | The time block is scored by the negative log density of log time, with the same margin and bootstrap | Document |
| 3.4 | The sequential 3σ check gives false alarms, 10-sample bootstrap noise, and loops | Partly | False alarms are about 3% per refit interval (2.0% by 200 attempts, 3.7% by 1,000), not 0.3%. They are harmless, since a refit adopts only on a held-out gain. The bootstrap uses 2,000 samples. Every refit, adopted or not, restarts the drift window (≥ 50 new predictions), so nothing loops | Document; no LIL boundary needed |
| 3.5 | Speed fitted on correct first tries only is biased | Not a defect | A sitting passes only when every answer is right, so time given correct is what P_pass needs | None |
| 3.6 | The feasibility check uses the uncalibrated ceiling | **True** | daily.py compares (1 − s)·0.99^K̄ with a calibrated target | **Recalibrate the ceiling (v1.5, 4.3)** |
| 4.1 | Background components have no learning curve | Partly | By design for skills used constantly. Since the precalculus review serves weak background skills as practice, such a skill is tracked only by evidence | Backlog: a background skill served as practice gets the course learning law |
| 4.2 | The ladder can't replace items that don't exist, failing gates | Wrong | The ladder never adds items by design. Maintenance holds a retry slot. The gates pass | Document |
| 4.3 | Rung 3 duplicates the cap and misuses the wheel-spinning citation | Partly | Rung 3 also stops checks and retries and starts the next-day return, so it isn't redundant. The citation motivates a stop rule, not the number 3 | Grade the rung points C in the document |
| 4.4 | Sittings break the no-two-in-a-row rule | Wrong | The sitting is placed as one block, exempt (order.py) | Document |
| 4.5 | A mid-course start revokes everything on day 1 | Wrong | Assumed skills start certified at Keep, their prior raised to the Keep target (certify.py) | Document |
| 4.6 | Skills are introduced before their prerequisites are certified | By design | The course calendar can't wait. Prerequisites are introduced first, and blame routes practice to a weak one through the bottleneck and ladder rules | None |
| 5.1 | Subtracting the typing allowance can make T ≤ 0 | Wrong | The allowance is added to the solve time (timing.py). The document said "minus" | Fix the document's time definition |
| 5.2 | Pausing on defocus freezes the clock in closed-book sittings | **True** | Practice subtracts pauses | **In a sitting the clock runs; a pause over 2 minutes voids it (v1.5)** |
| 5.3–5.6 | θ̂, δ_1..3, "representative problem" and n_k undefined | True for the document | Defined in the design and code | Define them in the document |
| 6.1–6.3 | Standard-time constants, EdNet domain, notation clashes, raw LaTeX | True for the document | EdNet is TOEIC; s, m, κ, σ and k were overloaded | Fixed in the document |
| 7.1 | Background prerequisites flood day 1 | Wrong | Background skills are never introduced, checked or kept | None |
| 7.2 | Reference checks can pick unintroduced skills | Wrong | Only introduced skills past their new block (daily.py, checks) | None |
| 7.3 | b > 1 saturates P_j | Not a defect | b is fit with a prior and adopted only on a held-out gain | None |
| 7.4 | Day boundaries reset the ladder, allowing endless bypass | Partly | The struggling rule spans days, but a skill stuck every day never reached it, because its rung-2 item was counted for the prerequisite | **A ladder item counts toward its stuck skill's allowance (v1.5, 4.2)** |
| 7.5 | FSRS receives probability q_k instead of retrievability | Wrong | FSRS receives a rating and an elapsed time; q_k never enters it | None |

## Proposed solutions

| Proposal | Decision |
|---|---|
| Ordered sequential credit, censoring steps after the failed one | Not adopted. For a matched wrong answer, the steps after the error were carried out on the wrong value, since the final answer matches. Removing failure credit, the testable part, changed nothing |
| ADF / expected Fisher scoring | ADF adopted; Fisher scoring tested and not adopted |
| Prior variance 0.5 and no drift once C_k > 0 | Not adopted. Prior variance 1–3 and drift 0–0.05 were all tested; ADF's gain holds across them |
| PPE power-law memory with a 0.70 floor | Already a candidate for the next version (needs procedural data). The floor value has no basis |
| Soft-minimum combination | No better than the geometric mean on the logs; switching waits for our own data (6.4) |
| Sitting limit at the 80th percentile, 1.25·ΣT* | Not adopted; pace redefined instead |
| Online filter for τ | Adopted, as the exact posterior with the per-skill offsets |
| Typing-allowance floor | Not needed: the allowance is added |
| Event-index discounting, staged targets, κ_0 = 2 | Event indexing not adopted (evidence-only state changes instead). Staged targets are the owner's pending decision (b). κ_0 = 2 would certify faster while the prior already reuses the evidence: not adopted without simulator numbers |
| Fixed-slot session envelope; sittings exempt from interleaving | Already built |
| LIL boundary and a 50-attempt cooldown | Not needed: the drift window already restarts at every refit |
| Mid-course priors at 0.85 | Not needed: assumed skills start certified |
| Truth models (g) step-abandonment and (h) bursty pauses | **Adopted** for the robustness matrix (6.2) |

## A problem the audit missed

The certification prior is the model's current forecast for the skill, and that forecast has already seen the same attempts. So direct evidence counts twice. At the M1 threshold, after 4 straight successes, the prior supplies 4 of 8 observations' weight at a forecast of 0.84. Common mastery rules (3–5 correct in a row) certify at about the same point, and the simulator's gate compares false certification against a baseline. It stays, stated plainly, with the false-certification rate as its check.
