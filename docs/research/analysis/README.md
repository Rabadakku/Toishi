# Analysis code for the model audits

The scripts behind `docs/design/model-assumption-audit.md` and `docs/design/external-audit-response.md`. They are analysis code, not part of the app: they need numpy, pandas, pyarrow, scipy and fsrs (py-fsrs 6.3.2), which the app does not depend on. They import `core.learner` from this repository, so they test the model exactly as built.

The datasets are not in the repository (their licenses don't allow redistribution). Get them from:
- **CMU OLI Engineering Statics, Fall 2011:** PSLC DataShop, dataset 507, the student-step export (`student_step.csv`).
- **XES3G5M:** github.com/ai4ed/XES3G5M, the `kc_level` files `seq_train.parquet` and `seq_test.parquet`.
- **EdNet KT1:** github.com/riiid/ednet (`KT1.zip` and the question contents).

| Script | What it does | Run |
|---|---|---|
| `fit.py` | Loaders and the pooled logistic models (student and skill effects, held-out last 20%) | `fit.py statics|xes DATA OUT_JSON` |
| `filter_eval.py` | The app's model run prequentially over each student's log, with constants varied one at a time | `filter_eval.py statics|xes DATA OUT_JSON [n] [grid]` |
| `lam.py` | The combination rule's exponent, post hoc on a dumped run | `lam.py DUMP.pkl` |
| `times.py` | Response-time residuals and the speed-up α | `times.py statics DATA OUT` or `times.py ednet KT1 CONTENTS OUT [n]` |
| `speed_slopes.py` | Per-student speed-up slopes and slow starters | as `times.py` |
| `speed_heldout.py` | Held-out comparison of speed models (shared, per-student, recency) | as `times.py` |
| `audit_variants.py` | External audit: structural variants of the update (Fisher information, assumed-density filtering, memory start, failure credit) | `audit_variants.py statics|xes DATA OUT_JSON [n]` |
| `audit_paired.py` | Assumed-density filtering against the Newton step: student-clustered bootstrap and a robustness grid | as above |
| `audit_extra.py` | External audit: no stability gain on failures, and combination rules (product, geometric mean, weakest link, soft minimum) | as above |
| `pace_checks.py` | Sitting and exam-finishing probabilities (Fenton-Wilkinson and Monte Carlo), and the refit trigger's false-alarm rate | `pace_checks.py` |

Datasets: pass `0` for all students (Statics: 331) or a sample size (XES3G5M: 1,000 in the audits, seed 0).
