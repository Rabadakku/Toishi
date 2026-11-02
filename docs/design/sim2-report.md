# Simulator report: robust evaluation of the student model and planner (design 6.2)

Generated 2026-11-02 by `python -m tools.sim2.run --out docs/design/sim2-report.md`: 108 runs in 1.5 minutes on 2 processes. Code: `tools/sim2/`; tests: `tests/sim2/`.

> **P1 is a stand-in.** `core.learner` and `core.plan` have not merged, so P1 ran on `tools/sim2/standin.py`, a simplified version of the design written for this simulator. Every P1 number and every P1 gate below is provisional and labelled "stand-in". P0 (the baseline) and the truth models are final for this simulator.

## Gates (design 6.2)

| Gate | Policy | Result | Detail |
|---|---|---|---|
| Strong model-truth student certifies M1-M3 on time | P1 | **PASS (stand-in)** | M1 1.00, M2 1.00, M3 1.00 of skills by deadline (threshold 0.95; 3 seeds) |
| New material is always served on its date | P1 | **PASS (stand-in)** | 0 skill introductions not served on their first study day by the policy's choice; 467 more only because new material alone filled the budget (54 runs) |
| Daily items never exceed the plan | P1 | **PASS (stand-in)** | 0 study days served more items than planned (54 runs) |
| Weak students are not certified more often than under the baseline | P1 vs P0 | **PASS (stand-in)** | false certifications of weak students per 100 skill-milestones (tolerance +0.5): a-model: P1 0.0 vs P0 32.6 ok; b-additive: P1 0.0 vs P0 34.3 ok; d-rohrer-taylor: P1 0.0 vs P0 33.2 ok; e-careless: P1 0.0 vs P0 33.2 ok; e-slow: P1 0.0 vs P0 17.9 ok; f-tags: P1 0.0 vs P0 33.3 ok |
| Strong model-truth student certifies M1-M3 on time | P0 | **FAIL** | M1 1.00, M2 0.01, M3 0.03 of skills by deadline (threshold 0.95; 3 seeds) |
| New material is always served on its date | P0 | **PASS** | 0 skill introductions not served on their first study day by the policy's choice; 2262 more only because new material alone filled the budget (54 runs) |
| Daily items never exceed the plan | P0 | **PASS** | 0 study days served more items than planned (54 runs) |

P1's rows are the gates. P0's rows apply the same checks to the baseline for reference. A strong student passes gate 1 when at least 95% of its skills reach each milestone by the deadline (mean over seeds). Gate 2 counts a skill when its new material did not start on its first study day on or after its introduction date although the policy served other work that day or stopped before the budget; days where new material alone filled the budget are reported, not counted. Gate 4 compares false certifications (truth readiness below the target − 0.10 at the moment of certification) of the weak profile, with a tolerance of 0.5 per 100 skill-milestones.

## Overview across truth models

Means over truth models of each model's mean over seeds. Certified / ready: the share of skills certified by the deadline against the share the truth says was at the target then (with pace for M2 and M3). False: certifications while the truth was below the target − 0.10, per 100 skill-milestones. Ready +90: truth readiness at the target tier 90 days after the M3 deadline (accuracy / at pace).

| Profile | Policy | M1 certified / ready | M2 certified / ready | M3 certified / ready | False | Ready +90 | Minutes a day |
|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 1.0 | 0.42 / 0.37 | 61 |
| typical | P0 | 0.56 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 37.5 | 0.39 / 0.33 | 59 |
| strong | P1 (stand-in) | 0.92 / 0.83 | 0.91 / 0.83 | 0.89 / 0.83 | 0.0 | 0.95 / 0.95 | 23 |
| strong | P0 | 1.00 / 0.83 | 0.04 / 0.83 | 0.06 / 0.83 | 0.0 | 0.95 / 0.95 | 8 |
| weak | P1 (stand-in) | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.0 | 0.19 / 0.09 | 63 |
| weak | P0 | 0.06 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 30.7 | 0.15 / 0.07 | 64 |

## Setup

- **Course:** `calc1-ch4`, 72 course skills and 23 background components from the component map, 22 sections, 25.0 class hours at 2.5 a week (70 days). 2736 generated problems: tier 1 576, tier 2 720, tier 3 720, tier 4 720. Components: tier 1 the skill; tier 2 plus 0–1 prerequisite or section component; tier 3 three or four; tier 4 four to six with one from another section. T* = 0.5 + 1.5·steps + 1.5·max(0, tier − 3) minutes.
- **Runs:** start 2027-01-11, through each skill's M3 deadline + 90 days (self-study, no course end). Budget 60 minutes a study day; 15% of days skipped (the same days for both policies); a worked example takes 3 minutes and a miss 1 more minute to read the solution. Target 0.90 at tier 4. Seeds 1, 2, 3; each seed is one student per truth model and profile, met by both policies.
- **P1** (design): `core.learner` + `core.plan` through `tools/sim2/adapters.py` (stand-in until the merge). **P0** (baseline): one FSRS-6 card per skill (defaults of `core/engine/fsrs_adapter.py`), introduced on its pace date with a worked example, random tier 1–2 problems (at most 8 a day) until 3 in a row are right, then one random target-tier problem per due review. P0 certifies M1 when learning ends and M2 and M3 after 3 correct first tries in a row at tier 3+ within T*; it never revokes.

| Truth model | What it is |
|---|---|
| a-model | The design's own model (3.2): conjunctive, execution × FSRS-6 memory, hidden values drawn around the design's priors. |
| b-additive | Additive Best-LR / DAS3H learner: logit = ability − difficulty + Σ over components of [β + Σ_w (g_w ln(1 + successes_w) − t_w ln(1 + attempts_w))], windows 1 h, 1 d, 7 d, 30 d, ∞. |
| d-rohrer-taylor | (a) with exponential forgetting, S₀ = 24.9 d and spaced-review gain 11, fitted to Rohrer & Taylor 2006 Exp 1. |
| e-slow | (a) learning at half rate: γ, ρ and the speed-up exponent halved. |
| e-careless | (a) with slip 0.12 (the target of 0.90 is out of reach by construction). |
| f-tags | (a) on the real tags while the planner sees 10% of non-main tags dropped and 10% swapped. |

Profiles: **typical** (drawn per seed: ability offset ~ N(0, 0.65²), component offsets ~ N(0, 0.7²), slip 0.02–0.05, median time ≈ 2·T* before practice); **strong** (above the targets from the start: component execution ≈ 0.997, memories from before the course, slip 0.01, median time ≈ 0.5·T*); **weak** (ability offset −1.3, slip 0.06, faster forgetting (φ 1.3), median time ≈ 2.8·T*).

## Results by truth model

Mean ± standard deviation over seeds. M1–M3: share of skills certified by the deadline (cumulative). Min to M3: median minutes on the skill until M3, over skills that reached it (count in brackets). Ready: truth readiness at the target tier 30 and 90 days after the M3 deadline, and the share of skills at or above the target at +90. Calibration: expected calibration error and bias (predicted − observed). Minutes: per study day served (mean / max). False: false certifications per 100 skill-milestones.

### a-model

The design's own model (3.2): conjunctive, execution × FSRS-6 memory, hidden values drawn around the design's priors.

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.01 ± 0.01 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.28 ± 0.02 | 0.36 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.00 | -0.03 ± 0.00 | 61 / 68 | 1.2 ± 1.0 |
| typical | P0 | 0.69 ± 0.31 | 0.00 ± 0.00 | 0.00 ± 0.00 | 180 ± 33 (6) | 0.22 ± 0.03 | 0.33 ± 0.03 | 0.00 ± 0.00 | 0.35 ± 0.01 | 0.35 ± 0.01 | 64 / 99 | 38.1 ± 1.0 |
| strong | P1 (stand-in) | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 30 ± 1 (72) | 0.97 ± 0.00 | 0.96 ± 0.01 | 0.98 ± 0.04 | 0.06 ± 0.00 | -0.06 ± 0.00 | 14 / 61 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.01 ± 0.01 | 0.03 ± 0.01 | 15 ± 0 (72) | 0.97 ± 0.00 | 0.96 ± 0.00 | 0.99 ± 0.01 | 0.08 ± 0.01 | -0.08 ± 0.01 | 7 / 59 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.09 ± 0.02 | 0.13 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.00 | -0.02 ± 0.01 | 62 / 83 | 0.0 ± 0.0 |
| weak | P0 | 0.05 ± 0.05 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.06 ± 0.00 | 0.06 ± 0.01 | 0.00 ± 0.00 | 0.50 ± 0.01 | 0.50 ± 0.01 | 65 / 98 | 32.6 ± 1.3 |

### b-additive

Additive Best-LR / DAS3H learner: logit = ability − difficulty + Σ over components of [β + Σ_w (g_w ln(1 + successes_w) − t_w ln(1 + attempts_w))], windows 1 h, 1 d, 7 d, 30 d, ∞.

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.82 ± 0.08 | 0.93 ± 0.04 | 0.77 ± 0.22 | 0.04 ± 0.01 | -0.03 ± 0.01 | 61 / 71 | 0.2 ± 0.3 |
| typical | P0 | 0.62 ± 0.48 | 0.00 ± 0.00 | 0.02 ± 0.04 | 78 ± 18 (20) | 0.85 ± 0.09 | 0.92 ± 0.02 | 0.69 ± 0.17 | 0.06 ± 0.01 | -0.06 ± 0.01 | 36 / 80 | 39.2 ± 1.2 |
| strong | P1 (stand-in) | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 29 ± 1 (72) | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.07 ± 0.00 | -0.07 ± 0.00 | 14 / 63 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 15 ± 0 (72) | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 0.10 ± 0.00 | -0.10 ± 0.00 | 7 / 59 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.38 ± 0.05 | 0.57 ± 0.03 | 0.00 ± 0.00 | 0.05 ± 0.01 | -0.04 ± 0.00 | 63 / 91 | 0.0 ± 0.0 |
| weak | P0 | 0.04 ± 0.01 | 0.00 ± 0.00 | 0.00 ± 0.00 | 204 ± 15 (1) | 0.50 ± 0.02 | 0.67 ± 0.07 | 0.02 ± 0.03 | 0.11 ± 0.06 | -0.08 ± 0.06 | 62 / 110 | 34.3 ± 0.9 |

### d-rohrer-taylor

(a) with exponential forgetting, S₀ = 24.9 d and spaced-review gain 11, fitted to Rohrer & Taylor 2006 Exp 1.

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.00 ± 0.01 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.29 ± 0.01 | 0.36 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.03 ± 0.01 | 61 / 76 | 1.9 ± 0.5 |
| typical | P0 | 0.69 ± 0.18 | 0.00 ± 0.00 | 0.00 ± 0.00 | 167 ± 55 (4) | 0.18 ± 0.05 | 0.32 ± 0.02 | 0.00 ± 0.00 | 0.36 ± 0.01 | 0.36 ± 0.01 | 64 / 86 | 36.9 ± 2.2 |
| strong | P1 (stand-in) | 0.99 ± 0.01 | 1.00 ± 0.00 | 1.00 ± 0.00 | 30 ± 1 (72) | 0.97 ± 0.00 | 0.95 ± 0.00 | 0.98 ± 0.02 | 0.07 ± 0.01 | -0.07 ± 0.01 | 16 / 63 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.01 ± 0.00 | 0.02 ± 0.01 | 16 ± 1 (72) | 0.97 ± 0.00 | 0.96 ± 0.00 | 0.99 ± 0.01 | 0.07 ± 0.00 | -0.07 ± 0.00 | 7 / 62 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.09 ± 0.01 | 0.13 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.03 ± 0.01 | 62 / 74 | 0.0 ± 0.0 |
| weak | P0 | 0.06 ± 0.03 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.03 ± 0.01 | 0.03 ± 0.00 | 0.00 ± 0.00 | 0.53 ± 0.03 | 0.53 ± 0.03 | 65 / 99 | 33.2 ± 0.3 |

### e-slow

(a) learning at half rate: γ, ρ and the speed-up exponent halved.

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.14 ± 0.02 | 0.16 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.00 ± 0.01 | 62 / 76 | 0.3 ± 0.5 |
| typical | P0 | 0.13 ± 0.05 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.09 ± 0.01 | 0.12 ± 0.04 | 0.00 ± 0.00 | 0.45 ± 0.05 | 0.45 ± 0.05 | 65 / 114 | 32.9 ± 0.8 |
| strong | P1 (stand-in) | 0.96 ± 0.06 | 1.00 ± 0.00 | 1.00 ± 0.00 | 42 ± 1 (72) | 0.97 ± 0.00 | 0.96 ± 0.00 | 1.00 ± 0.01 | 0.06 ± 0.00 | -0.06 ± 0.00 | 23 / 67 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.03 ± 0.04 | 0.06 ± 0.02 | 19 ± 0 (72) | 0.97 ± 0.00 | 0.96 ± 0.00 | 0.99 ± 0.02 | 0.07 ± 0.01 | -0.07 ± 0.01 | 10 / 64 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.04 ± 0.01 | 0.05 ± 0.01 | 0.00 ± 0.00 | 0.03 ± 0.01 | 0.00 ± 0.01 | 64 / 90 | 0.0 ± 0.0 |
| weak | P0 | 0.04 ± 0.02 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.03 ± 0.01 | 0.04 ± 0.01 | 0.00 ± 0.00 | n/a | n/a | 65 / 89 | 17.9 ± 1.5 |

### e-careless

(a) with slip 0.12 (the target of 0.90 is out of reach by construction).

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.26 ± 0.01 | 0.33 ± 0.01 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.02 ± 0.01 | 61 / 70 | 0.8 ± 0.3 |
| typical | P0 | 0.46 ± 0.32 | 0.00 ± 0.00 | 0.00 ± 0.00 | 130 ± 25 (6) | 0.19 ± 0.03 | 0.30 ± 0.01 | 0.00 ± 0.00 | 0.36 ± 0.02 | 0.36 ± 0.02 | 63 / 89 | 38.7 ± 3.1 |
| strong | P1 (stand-in) | 0.56 ± 0.03 | 0.43 ± 0.06 | 0.36 ± 0.09 | 50 ± 2 (57) | 0.87 ± 0.00 | 0.87 ± 0.00 | 0.00 ± 0.00 | 0.02 ± 0.01 | 0.01 ± 0.01 | 57 / 65 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.13 ± 0.03 | 0.18 ± 0.04 | 18 ± 0 (72) | 0.87 ± 0.00 | 0.86 ± 0.00 | 0.00 ± 0.00 | 0.03 ± 0.00 | 0.02 ± 0.01 | 10 / 65 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.08 ± 0.01 | 0.12 ± 0.02 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.00 ± 0.02 | 63 / 91 | 0.0 ± 0.0 |
| weak | P0 | 0.06 ± 0.02 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.06 ± 0.01 | 0.06 ± 0.01 | 0.00 ± 0.00 | 0.49 ± 0.04 | 0.49 ± 0.04 | 65 / 96 | 33.2 ± 0.3 |

### f-tags

(a) on the real tags while the planner sees 10% of non-main tags dropped and 10% swapped.

| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target +90 | ECE | Bias | Minutes | False |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| typical | P1 (stand-in) | 0.01 ± 0.01 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.29 ± 0.02 | 0.36 ± 0.02 | 0.00 ± 0.00 | 0.02 ± 0.00 | -0.02 ± 0.01 | 61 / 72 | 1.5 ± 1.4 |
| typical | P0 | 0.79 ± 0.18 | 0.00 ± 0.00 | 0.00 ± 0.00 | 166 ± 19 (7) | 0.23 ± 0.03 | 0.33 ± 0.02 | 0.00 ± 0.00 | 0.35 ± 0.01 | 0.35 ± 0.01 | 64 / 82 | 39.2 ± 1.8 |
| strong | P1 (stand-in) | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 29 ± 0 (72) | 0.97 ± 0.01 | 0.96 ± 0.00 | 0.99 ± 0.01 | 0.06 ± 0.00 | -0.06 ± 0.00 | 15 / 63 | 0.0 ± 0.0 |
| strong | P0 | 1.00 ± 0.00 | 0.04 ± 0.02 | 0.05 ± 0.02 | 15 ± 0 (72) | 0.97 ± 0.00 | 0.96 ± 0.00 | 1.00 ± 0.01 | 0.07 ± 0.01 | -0.07 ± 0.01 | 7 / 63 | 0.0 ± 0.0 |
| weak | P1 (stand-in) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.09 ± 0.02 | 0.12 ± 0.03 | 0.00 ± 0.00 | 0.03 ± 0.01 | -0.03 ± 0.01 | 62 / 83 | 0.0 ± 0.0 |
| weak | P0 | 0.09 ± 0.04 | 0.00 ± 0.00 | 0.00 ± 0.00 | n/a (0) | 0.06 ± 0.01 | 0.07 ± 0.01 | 0.00 ± 0.00 | 0.46 ± 0.07 | 0.46 ± 0.07 | 64 / 102 | 33.3 ± 0.0 |

## Diagnostics

### Workload and pace

Planned items and minutes are what the policy reported for the day (the design never caps them); served is what fit in the budget. Fast: the share of correct tier 3+ first tries within T*. M2 and M3 certification needs P(correct and within T*) at or above the target, so with a 0.90 target a student who is always right still needs about 90% of solves within T*.

| Truth | Profile | Policy | Planned items | Served items | Planned min | Accuracy | Fast | Ready +90 at pace | Ever M3 |
|---|---|---|---|---|---|---|---|---|---|
| a-model | strong | P0 | 5 | 3.1 | 23 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.00 |
| a-model | strong | P1 (stand-in) | 13 | 8.3 | 20 | 98% | 100% | 0.96 ± 0.01 | 1.00 ± 0.00 |
| a-model | typical | P0 | 79 | 12.4 | 634 | 36% | 89% | 0.30 ± 0.02 | 0.08 ± 0.02 |
| a-model | typical | P1 (stand-in) | 201 | 29.1 | 449 | 68% | 88% | 0.33 ± 0.02 | 0.00 ± 0.00 |
| a-model | weak | P0 | 226 | 13.3 | 810 | 34% | 70% | 0.03 ± 0.00 | 0.00 ± 0.00 |
| a-model | weak | P1 (stand-in) | 199 | 16.4 | 821 | 50% | nan% | 0.06 ± 0.01 | 0.00 ± 0.00 |
| b-additive | strong | P0 | 5 | 3.0 | 22 | 100% | 100% | 1.00 ± 0.00 | 1.00 ± 0.00 |
| b-additive | strong | P1 (stand-in) | 13 | 8.0 | 21 | 100% | 100% | 1.00 ± 0.00 | 1.00 ± 0.00 |
| b-additive | typical | P0 | 44 | 8.7 | 217 | 55% | 82% | 0.78 ± 0.06 | 0.28 ± 0.22 |
| b-additive | typical | P1 (stand-in) | 201 | 29.8 | 447 | 66% | 97% | 0.85 ± 0.07 | 0.00 ± 0.00 |
| b-additive | weak | P0 | 200 | 11.6 | 702 | 38% | 50% | 0.33 ± 0.03 | 0.01 ± 0.01 |
| b-additive | weak | P1 (stand-in) | 200 | 15.4 | 855 | 40% | nan% | 0.28 ± 0.02 | 0.00 ± 0.00 |
| d-rohrer-taylor | strong | P0 | 6 | 3.3 | 25 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.00 |
| d-rohrer-taylor | strong | P1 (stand-in) | 14 | 9.0 | 22 | 98% | 100% | 0.95 ± 0.00 | 1.00 ± 0.00 |
| d-rohrer-taylor | typical | P0 | 76 | 12.5 | 632 | 36% | 88% | 0.29 ± 0.03 | 0.06 ± 0.04 |
| d-rohrer-taylor | typical | P1 (stand-in) | 199 | 29.4 | 438 | 68% | 97% | 0.33 ± 0.02 | 0.00 ± 0.00 |
| d-rohrer-taylor | weak | P0 | 202 | 12.6 | 787 | 34% | 55% | 0.02 ± 0.00 | 0.00 ± 0.00 |
| d-rohrer-taylor | weak | P1 (stand-in) | 201 | 16.8 | 836 | 50% | nan% | 0.07 ± 0.01 | 0.00 ± 0.00 |
| e-careless | strong | P0 | 7 | 4.6 | 36 | 87% | 100% | 0.86 ± 0.00 | 1.00 ± 0.00 |
| e-careless | strong | P1 (stand-in) | 133 | 47.1 | 142 | 87% | 100% | 0.87 ± 0.00 | 0.79 ± 0.15 |
| e-careless | typical | P0 | 92 | 13.7 | 639 | 35% | 87% | 0.27 ± 0.02 | 0.08 ± 0.05 |
| e-careless | typical | P1 (stand-in) | 198 | 30.0 | 428 | 63% | 100% | 0.30 ± 0.02 | 0.00 ± 0.00 |
| e-careless | weak | P0 | 220 | 13.0 | 805 | 33% | 72% | 0.03 ± 0.01 | 0.00 ± 0.00 |
| e-careless | weak | P1 (stand-in) | 200 | 16.5 | 858 | 48% | nan% | 0.06 ± 0.01 | 0.00 ± 0.00 |
| e-slow | strong | P0 | 6 | 3.5 | 26 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.01 |
| e-slow | strong | P1 (stand-in) | 20 | 8.7 | 44 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.00 |
| e-slow | typical | P0 | 153 | 12.2 | 727 | 34% | 38% | 0.06 ± 0.03 | 0.00 ± 0.00 |
| e-slow | typical | P1 (stand-in) | 200 | 18.3 | 688 | 55% | 64% | 0.08 ± 0.02 | 0.00 ± 0.00 |
| e-slow | weak | P0 | 393 | 10.5 | 984 | 29% | nan% | 0.01 ± 0.00 | 0.00 ± 0.00 |
| e-slow | weak | P1 (stand-in) | 200 | 10.3 | 1228 | 37% | nan% | 0.01 ± 0.00 | 0.00 ± 0.00 |
| f-tags | strong | P0 | 5 | 3.3 | 24 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.00 |
| f-tags | strong | P1 (stand-in) | 13 | 8.6 | 21 | 98% | 100% | 0.96 ± 0.00 | 1.00 ± 0.00 |
| f-tags | typical | P0 | 71 | 12.1 | 616 | 36% | 88% | 0.30 ± 0.02 | 0.10 ± 0.03 |
| f-tags | typical | P1 (stand-in) | 197 | 29.5 | 450 | 68% | 83% | 0.33 ± 0.01 | 0.00 ± 0.00 |
| f-tags | weak | P0 | 222 | 13.0 | 805 | 34% | 45% | 0.03 ± 0.00 | 0.00 ± 0.00 |
| f-tags | weak | P1 (stand-in) | 199 | 16.0 | 862 | 48% | nan% | 0.06 ± 0.01 | 0.00 ± 0.00 |

### Certified against truly ready, at each deadline

Certified: the share of skills the policy certified by the deadline. Ready: the share whose truth readiness at the milestone tier (with pace for M2 and M3) was at or above the target at the end of the deadline day, under that policy's practice. A planner that certifies far less than is ready wastes practice; one that certifies more is certifying students who are not there. Mean truth readiness in brackets.

| Truth | Profile | Policy | M1 certified / ready | M2 certified / ready | M3 certified / ready |
|---|---|---|---|---|---|
| a-model | strong | P0 | 1.00 / 1.00 (0.99) | 0.01 / 1.00 (0.98) | 0.03 / 1.00 (0.97) |
| a-model | strong | P1 (stand-in) | 1.00 / 1.00 (0.99) | 1.00 / 1.00 (0.98) | 1.00 / 1.00 (0.98) |
| a-model | typical | P0 | 0.69 / 0.00 (0.50) | 0.00 / 0.00 (0.23) | 0.00 / 0.00 (0.12) |
| a-model | typical | P1 (stand-in) | 0.01 / 0.00 (0.58) | 0.00 / 0.00 (0.31) | 0.00 / 0.00 (0.20) |
| a-model | weak | P0 | 0.05 / 0.00 (0.29) | 0.00 / 0.00 (0.05) | 0.00 / 0.00 (0.02) |
| a-model | weak | P1 (stand-in) | 0.00 / 0.00 (0.38) | 0.00 / 0.00 (0.06) | 0.00 / 0.00 (0.02) |
| b-additive | strong | P0 | 1.00 / 1.00 (1.00) | 0.00 / 1.00 (1.00) | 0.00 / 1.00 (1.00) |
| b-additive | strong | P1 (stand-in) | 1.00 / 1.00 (1.00) | 1.00 / 1.00 (1.00) | 1.00 / 1.00 (1.00) |
| b-additive | typical | P0 | 0.62 / 0.00 (0.54) | 0.00 / 0.00 (0.55) | 0.02 / 0.02 (0.61) |
| b-additive | typical | P1 (stand-in) | 0.00 / 0.00 (0.55) | 0.00 / 0.00 (0.51) | 0.00 / 0.01 (0.59) |
| b-additive | weak | P0 | 0.04 / 0.00 (0.27) | 0.00 / 0.00 (0.10) | 0.00 / 0.00 (0.16) |
| b-additive | weak | P1 (stand-in) | 0.00 / 0.00 (0.30) | 0.00 / 0.00 (0.08) | 0.00 / 0.00 (0.09) |
| d-rohrer-taylor | strong | P0 | 1.00 / 1.00 (0.99) | 0.01 / 1.00 (0.98) | 0.02 / 1.00 (0.97) |
| d-rohrer-taylor | strong | P1 (stand-in) | 0.99 / 1.00 (0.99) | 1.00 / 1.00 (0.98) | 1.00 / 1.00 (0.98) |
| d-rohrer-taylor | typical | P0 | 0.69 / 0.00 (0.50) | 0.00 / 0.00 (0.17) | 0.00 / 0.00 (0.08) |
| d-rohrer-taylor | typical | P1 (stand-in) | 0.00 / 0.00 (0.57) | 0.00 / 0.00 (0.32) | 0.00 / 0.00 (0.20) |
| d-rohrer-taylor | weak | P0 | 0.06 / 0.00 (0.29) | 0.00 / 0.00 (0.05) | 0.00 / 0.00 (0.02) |
| d-rohrer-taylor | weak | P1 (stand-in) | 0.00 / 0.00 (0.38) | 0.00 / 0.00 (0.05) | 0.00 / 0.00 (0.02) |
| e-careless | strong | P0 | 1.00 / 0.00 (0.88) | 0.13 / 0.00 (0.87) | 0.18 / 0.00 (0.87) |
| e-careless | strong | P1 (stand-in) | 0.56 / 0.00 (0.88) | 0.43 / 0.00 (0.88) | 0.36 / 0.00 (0.87) |
| e-careless | typical | P0 | 0.46 / 0.00 (0.45) | 0.00 / 0.00 (0.22) | 0.00 / 0.00 (0.12) |
| e-careless | typical | P1 (stand-in) | 0.00 / 0.00 (0.53) | 0.00 / 0.00 (0.29) | 0.00 / 0.00 (0.18) |
| e-careless | weak | P0 | 0.06 / 0.00 (0.28) | 0.00 / 0.00 (0.05) | 0.00 / 0.00 (0.02) |
| e-careless | weak | P1 (stand-in) | 0.00 / 0.00 (0.36) | 0.00 / 0.00 (0.06) | 0.00 / 0.00 (0.02) |
| e-slow | strong | P0 | 1.00 / 1.00 (0.99) | 0.03 / 1.00 (0.98) | 0.06 / 1.00 (0.97) |
| e-slow | strong | P1 (stand-in) | 0.96 / 1.00 (0.99) | 1.00 / 1.00 (0.98) | 1.00 / 1.00 (0.98) |
| e-slow | typical | P0 | 0.13 / 0.00 (0.41) | 0.00 / 0.00 (0.09) | 0.00 / 0.00 (0.04) |
| e-slow | typical | P1 (stand-in) | 0.00 / 0.00 (0.47) | 0.00 / 0.00 (0.11) | 0.00 / 0.00 (0.06) |
| e-slow | weak | P0 | 0.04 / 0.00 (0.28) | 0.00 / 0.00 (0.01) | 0.00 / 0.00 (0.00) |
| e-slow | weak | P1 (stand-in) | 0.00 / 0.00 (0.31) | 0.00 / 0.00 (0.01) | 0.00 / 0.00 (0.00) |
| f-tags | strong | P0 | 1.00 / 1.00 (0.99) | 0.04 / 1.00 (0.98) | 0.05 / 1.00 (0.97) |
| f-tags | strong | P1 (stand-in) | 1.00 / 1.00 (0.99) | 1.00 / 1.00 (0.98) | 1.00 / 1.00 (0.98) |
| f-tags | typical | P0 | 0.79 / 0.00 (0.51) | 0.00 / 0.00 (0.23) | 0.00 / 0.00 (0.13) |
| f-tags | typical | P1 (stand-in) | 0.01 / 0.00 (0.58) | 0.00 / 0.00 (0.32) | 0.00 / 0.00 (0.21) |
| f-tags | weak | P0 | 0.09 / 0.00 (0.30) | 0.00 / 0.00 (0.05) | 0.00 / 0.00 (0.02) |
| f-tags | weak | P1 (stand-in) | 0.00 / 0.00 (0.38) | 0.00 / 0.00 (0.06) | 0.00 / 0.00 (0.02) |

### Calibration, pooled over seeds and profiles

| Truth | Policy | Attempts | Predicted | Observed | ECE | Brier | Log loss |
|---|---|---|---|---|---|---|---|
| a-model | P1 | 25710 | 0.645 | 0.676 | 0.031 | 0.181 | 0.534 |
| a-model | P0 | 3622 | 0.660 | 0.384 | 0.296 | 0.260 | 0.699 |
| b-additive | P1 | 25085 | 0.595 | 0.636 | 0.041 | 0.187 | 0.544 |
| b-additive | P0 | 1849 | 0.827 | 0.901 | 0.074 | 0.089 | 0.313 |
| d-rohrer-taylor | P1 | 26318 | 0.641 | 0.673 | 0.032 | 0.182 | 0.538 |
| d-rohrer-taylor | P0 | 3689 | 0.659 | 0.364 | 0.319 | 0.264 | 0.708 |
| e-careless | P1 | 46153 | 0.725 | 0.729 | 0.018 | 0.168 | 0.512 |
| e-careless | P0 | 3944 | 0.696 | 0.439 | 0.257 | 0.249 | 0.685 |
| e-slow | P1 | 17355 | 0.581 | 0.595 | 0.020 | 0.182 | 0.531 |
| e-slow | P0 | 1611 | 0.720 | 0.515 | 0.271 | 0.187 | 0.529 |
| f-tags | P1 | 25941 | 0.643 | 0.671 | 0.028 | 0.180 | 0.532 |
| f-tags | P0 | 3704 | 0.661 | 0.384 | 0.295 | 0.261 | 0.702 |

### Truth-model checks

Rohrer & Taylor 2006 Exp 1 on a median student (one-component problems):

| Memory | Massed 4w/1w | Spaced/massed 4w | Spaced/massed 1w |
|---|---|---|---|
| Observed (D4) | 0.43 | 2.0 | 0.93 |
| Truth (d) | 0.43 | 1.99 | 1.19 |
| FSRS-6 defaults (truth a, φ = 1) | 0.83 | 1.24 | 1.15 |

Truth (f) view: of 5023 non-main tags, 506 (10.1%) were dropped and 516 (10.3%) swapped; main skills are never changed (7759 tags in all).

## Where the stand-in had to choose

The spec leaves these open, and the stand-in's choices shape the provisional P1 numbers; the real planner may choose differently:

- Order among skills when the plan is longer than the session (4.3 says only that maintenance and growth are interleaved): maintenance by lowest forecast readiness, alternating with on-time growth by nearest deadline, and missed-milestone skills least recently practised first. In development runs (a-model, typical, seeds 3 and 4), serving growth in course order starved later skills: M1 at any time for 13-15% of skills instead of 28%.
- Empty growth band: 4.4 says to take the problem closest to 0.80 from the milestone tier or the rung below. For a strong student that picks rung-below problems, which never count toward the milestone (in development, a-model strong seed 1: M1 by its deadline for 72% of skills instead of 100%). The stand-in keeps to the milestone tier unless all its problems are below the band, and applies the 90-day no-repeat preference within each tier for the same reason.
- The 40% cap on missed-milestone work holds for every prefix of the session while other work remains; after that, missed-milestone items continue. Read literally, the cap would end sessions early once most skills are past a deadline.
- A reference check that falls due while new material is pending waits until the new material is served (new material first).
- Certifier priors and maintenance forecasts average the first 3 representative problems (the design allows up to 10); M2 and M3 priors multiply by the model's chance of finishing within T*.
- Not in the stand-in: refits other than the per-tier recalibration, the struggling and slip-limited statuses, exams, mid-course starts, confusable adjacency and the extra problem after an execution miss.

## Running P1 for real

1. Merge model-core and plan-core into this branch. `adapters.load_backend("auto")` switches to `core` once `core.learner.StudentModel` and `core.plan.plan_day`, `next_item`, `intro_dates` and `Certifier` exist.
2. Run `python -c "from tools.sim2.adapters import core_backend_problems as p; print(p())"` and fix `_CorePlanner` in `tools/sim2/adapters.py` until it prints `[]`: the contract leaves the Certifier's constructor and how it takes observations, the arguments of `next_item` and how a refit is adopted to the implementations.
3. Rerun `python -m tools.sim2.run --backend core --out docs/design/sim2-report.md` and the slow tests (`pytest -m slow tests/sim2`).

