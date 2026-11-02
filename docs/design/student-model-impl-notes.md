# Student model: implementation notes (wave 1, `core/learner`)

- Implements `student-model.md` v1.1 sections 3.1–3.6 and 3.10, with the constants of 3.5 and 7, the contract of section 8 and the recovery test of 6.1.
- Code: `core/learner/model.py` (StudentModel), `refit.py` (MAP refit and adoption), `simulate.py` (students sampled from the model), plus `FsrsAdapter.step_fractional` in `core/engine/fsrs_adapter.py`.
- Tests: `tests/learner/`. Golden numbers worked by hand are in `test_golden.py`; the recovery test (slow) is in `test_recovery.py`.
- The design is unchanged. Where it was ambiguous or silent, the reading closest to its stated intent was chosen. Each choice is listed below.

## Readings chosen

### Accuracy and updates (3.2, 3.4)
1. **Matched wrong answers in the execution step.**
   - 3.4 defines the κ rule only for the blame b_k, but says background components get "the execution posterior (step 3), with its blame". Its failure step L = 1 − Aσ has no blame in it, so as written a match would never reach a background component's posterior, or more than a plain miss would reach k*'s.
   - Reading: the κ rule is a mixture. With probability κ the match is diagnostic: k* failed (L = 1 − R·σ) and every other component succeeded (the exact success step). With probability 1 − κ it is an ordinary miss.
   - The score and the observed information mix the same way: g = κ·g_match + (1 − κ)·g_fail, h likewise. By Fisher's identity, the score is exactly the one implied by the κ-adjusted blame of 3.4.
   - Without a match, the step is the spec's formula unchanged. The mixing of h is a linear approximation.
2. **What the Newton step sees.** σ, A, the counts and R are the ones in force when the problem was answered, the same as the logged prediction. All of a problem's components update from that one prediction. A uses the other components' uncertainty-adjusted q_i, k's R_k and 1 − s, as 3.4 says; σ for k is unadjusted.
3. **Same-day weight.** "The component's first success of the study day" counts correct first tries that contain the component; the contract's integer `successes_today` holds them. A miss uses w = 1 until such a success, and is not itself a success.
4. **FSRS elapsed time.**
   - The memory update uses the same recall R_k(t) as the prediction: fractional days × φ, through `FsrsAdapter.step_fractional`.
   - "Same day" is decided on study days (`last_day == study_day`).
   - The flashcard path keeps whole study days (C4). Its reason, matching what the fitter is trained on, does not apply, because component FSRS weights are not refit in v1 (3.6).
5. **First event.** R = 1 before a course component's first event, so m_k = 0 and r = 1. The first event is always FSRS's initial Good state, even after a miss. The miss still moves the counts and the execution posterior.
6. **The 7-day horizon** is 7 real days, so 7·φ in FSRS time, because R_k(t) is FSRS recall after φ·(t − last). At r = 0 or 1, `mix_memory` returns the plain Again or Good state exactly.
7. **Drift.**
   - v_k grows by q_drift per whole study day since the component's last update, applied lazily: stored on update, computed but not stored on predict.
   - `predict` takes an optional `study_day`. Otherwise the model's calendar decides: UTC with the 4 AM rollover, as FsrsAdapter does, and injectable as `day_of`.
   - Background components drift too (step 3 applies to them).
8. **θ̂.**
   - n is the number of components with 3 or more attempts. The prior mean subtracted is the population one (0.62 or 3.48, without θ̂). Background components count.
   - θ̂ is recomputed after every update. It sets the prior of components first seen after that, both course and background (3.5 adds θ̂ to both).

### Time (3.3)
9. **τ and σ_T.**
   - 3.3 says they are "updated by conjugate normal regression"; 3.6 refits them by MAP; the contract keeps them in `SharedParams` with the other refit parameters. Reading: in the filter they are fixed between refits, like s and δ4.
   - The online part of the time regression is:
     - the per-skill offsets τ_s = Σ residual / (count + 5), where a residual is ln T − ln T* + α ln(1 + n̄) − τ (`skill_speed`);
     - the running Welford statistics of the prediction residuals ln T − ln median (`time_stats`), for the calibration screen.
   - The refit's MAP for τ is then a conjugate normal regression: τ enters each residual linearly. The search computes it exactly and cheaply with the time part of the filter alone (`time_nll`), and a test checks it against full replays.
   - The κ = 5 shrinkage is the operative rule for τ_s. 3.3's "prior N(0, 0.3²)" is not applied separately.
10. **Problems without a positive standard time** get no time prediction: median 0, and they do not feed the time model. A tier outside 1–5 raises ValueError.

### Refit (3.6)
11. **Split.** MAP is fit on the first 80% of the attempts in (at_ms, attempt_id) order. The current and the candidate parameters are scored by full replays over the whole log, on the last 20%. The adopted values are the ones fit on the 80%.
12. **The held-out log loss includes time.** An attempt's loss is the binary log loss of its first try plus, for a timed success, −log N(ln T; ln median, σ_T²). Without the time term, τ and σ_T could never be scored or adopted.
13. **Adoption per block.**
    - The accuracy parameters (s, δ4, a_ℓ, b, φ) move only the first-try predictions; τ and σ_T move only the time predictions. The two losses are separable.
    - Each block is adopted on its own loss, with 3.6's rule: at least 0.003 nats per attempt and a one-sided paired bootstrap p < 0.1.
    - A joint test would let a large time gain carry an accuracy change that is worse on its own held-out data, which is the noise-chasing 3.6 exists to stop.
    - `RefitDecision` reports the whole MAP candidate, the joint scores and p, the per-block decisions, and `params`: the current values with each adopted block swapped in.
14. **Bootstrap.** p = (#{resampled mean difference ≤ 0} + 1) / (B + 1), with B = 2000, a fixed seed (20261102), and the same resampled indices for both blocks.
15. **Minimum tail.** Fewer than 30 held-out attempts adopt nothing; the candidate is still reported. This is our constant; the spec is silent on tiny logs, where a bootstrap on a handful of attempts would pass by chance.
16. **Search scales and priors.**
    - Bounded coordinate (pattern) search in plain Python:
      - s on the logit scale, bounds [0.001, 0.5];
      - δ4 in [−1.5, 2.1];
      - ln φ in [ln 0.5, ln 4], the design's bounds;
      - a_ℓ in [−2, 2] and b in [0.2, 2];
      - τ in ln 2 ± 2.5;
      - ln σ_T in [ln 0.05, ln 2].
    - MAP depends on the scale. On the logit scale, Beta(1, 19) peaks at its stated mean 0.05 (Jacobian included), the default value of s. On s itself it peaks at 0.
    - Every other prior's mode is its stated centre (δ4 0.3, a 0, b 1, φ 1, τ ln 2, σ_T 0.45), so the logit scale keeps s consistent with them.
    - On the probability scale, s collapsed to its 0.001 bound in 2 of 6 recovery seeds, because the recalibration b < 1 does part of slip's job and the prior's mode at 0 decides (see the results below).
17. **The prior on σ_T.** 3.5 gives only the value 0.45. We use ln σ_T ~ N(ln 0.45, 0.5²), the same form as φ's prior.
18. **The recalibration is cached.** (a_ℓ, b) map P_raw to P and nothing else: blame and the Newton steps use P_raw. A replay therefore depends only on (s, δ4, φ), and (a_ℓ, b) are scored on cached logit(P_raw) values. A test checks that this is exactly a full replay.
19. **Trigger.** `refit_due(since, today, new_attempts)` returns True after 300 new attempts, or 14 days after `since`. `since` is the last refit, or the first attempt when there was none. It returns False when there are no new attempts.

### Contract and catalog
20. **Unknown components.** Components missing from the catalog are course components: 3.9 makes an untagged problem its own component.
21. **Added fields.**
    - `UpdateRecord.attempt_id` (default None) was added.
    - `memory_share` lists every component; background components get 0.
    - Duplicate ids in `ProblemSpec.components` count once.
22. **`StudentModel.time_attempts(alpha, observations)`** gives the time model's inputs for the refit.
23. **The spec file.** The section 8 code block of `student-model.md` is wrapped in `<!-- fmt: off -->`. ruff 0.17 formats Python blocks inside Markdown, and without the markers `scripts/check.sh` failed on main.

## Recovery (6.1)

The test truth is s = 0.12, δ4 = 0.8, φ = 2.0, τ = 0.3, σ_T = 0.3, with the identity recalibration. The course is synthetic, with seed 11: 48 course and 12 background components. The schedule is mixed, with 12 attempts per study day. The refit starts from the priors.

| Parameter | True | Prior | Refit, 1,000 attempts (test seed 7) | Range over 6 seeds at 1,000 | Seed 7 at 3,000 |
|---|---|---|---|---|---|
| s | 0.12 | 0.05 | 0.078 | 0.047–0.145 (within ±50% in 5 of 6) | 0.138 |
| δ4 | 0.8 | 0.3 | 0.494 | 0.27–0.60 (within ±50% in 3 of 6) | 0.738 |
| φ | 2.0 | 1.0 | 1.016 | 0.88–1.12: not recovered | 0.918 |
| τ | 0.3 | 0.693 | 0.323 | 0.285–0.323 (all within 8%) | 0.309 |
| σ_T | 0.3 | 0.45 | 0.357 | 0.34–0.41 (biased high) | 0.332 |

- **φ is not identifiable here.**
  - The training log-likelihood is nearly flat in φ: 0.07 nats over [0.5, 4] at 1,000 attempts, with its minimum at the true value. The prior then decides.
  - A mixed schedule keeps every component's recall high (mean R ≈ 0.99), so memory barely affects outcomes.
  - φ passes the ±50% band only because the prior 1.0 lies on the band's edge. Per 6.1, it should stay fixed at its prior unless a schedule with long gaps shows otherwise.
- **δ4 is confounded with a_4.** The tier-4 recalibration takes part of the tier-4 effect (a_4 < 0 whenever δ4 is short), so δ4 is shrunk toward its prior at 1,000 attempts.
- **s is confounded with (a_ℓ, b).** b < 1 compresses predictions much as slip caps them. With the recalibration fixed at the identity, the slip profile bottoms out at 0.10–0.12. Recovery is seed-dependent at 1,000 attempts and good at 3,000.
- **σ_T is biased upward** at 1,000 attempts by the error of the early online τ_s estimates. That is the right predictive spread, but it is a biased estimate of the noise.
- **Adoption.** The accuracy block was never adopted in these runs: held-out gains were at most 0.005 nats, with p > 0.2. The time block always was.

## Performance

A replay of 5,000 observations with 4 components each takes about 0.4–0.55 s in CPython 3.14 on the Linux workspace. `test_performance.py` bounds it at 3 s.

A refit of 1,000 attempts takes about 3 s, with 40–70 filter replays. A refit of 3,000 attempts takes about 10 s.
