# Verifying an FSRS-6 scheduler (py-fsrs 6.3.2 + fsrs-rs-python 0.9.3): tests, metrics, pitfalls

Versions as checked on 2026-11-01: py-fsrs main = 6.3.2; fsrs-rs-python 0.9.3 pins fsrs-rs 6.6.2 (fsrs-rs main commit of 2026-10-28). fsrs-rs 6.6.2 now also ships an FSRS-7 path, and FSRS-7 appears in srs-benchmark. FSRS-6 code paths are kept separately. — [fsrs-rs repo](https://github.com/open-spaced-repetition/fsrs-rs); [fsrs-rs-python](https://github.com/open-spaced-repetition/fsrs-rs-python); [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)

## 1. Evaluation metrics: definitions, typical FSRS-6 values, data needed

### Takeaway
Use log loss and RMSE(bins) for calibration and AUC for discrimination. FSRS-6 averages about LL 0.346, RMSE(bins) 0.065 and AUC 0.70 across 10k users. For one user, RMSE(bins) depends heavily on review count, so compare against a count-adjusted baseline (Anki's health-check formula), never against benchmark averages.

### Cited Findings
- Log loss = −(1/N)Σ[y log p + (1−y) log(1−p)], where y=0 for Again and 1 for Hard/Good/Easy. AUC is ROC area (0.5 = random). RMSE(bins) = sqrt(Σ wᵢ(R̄predᵢ − R̄measᵢ)² / Σ wᵢ), with each bin weighted by its review count. — [awesome-fsrs wiki: The Metric](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Metric)
- How fsrs-rs forms bins: delta_t bin = round(2.48·3.62^floor(log₃.₆₂ Δt)·100). The length bin applies 1.99·1.89^floor(log₁.₈₉(n)) to n = long-term review count + 1. The lapse bin applies 1.65·1.73^floor(log₁.₇₃ L), where L counts only Again ratings with Δt ≥ 1, and L=0 gets its own bin. — [fsrs-rs dataset.rs `r_matrix_index`](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/dataset.rs). The fsrs-optimizer `rmse_matrix` uses the same constants. — [fsrs_optimizer.py](https://github.com/open-spaced-repetition/fsrs-optimizer/blob/main/src/fsrs_optimizer/fsrs_optimizer.py)
- **Conflict:** the wiki page prints different constants (2.48/2.57, 1.52/1.58, 1.4/1.48). The code (3.62/1.89/1.73) should be treated as authoritative. — [The Metric](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Metric) vs [dataset.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/dataset.rs)
- The bins use features that do not depend on the predictions. The older prediction-based binning could be gamed by sending every prediction to one bin. The current binning can still be gamed by a model that memorizes bin means. — [The Metric](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Metric)
- The srs-benchmark uses sklearn TimeSeriesSplit with 5 splits and drops the first split, which is training-only. It excludes manual due-date changes and non-rescheduling filtered-deck reviews and applies an outlier filter. Its dataset is 9,999 collections with 349,923,850 evaluated reviews (excluding same-day reviews). — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- Results without same-day reviews (mean ± 99% CI): FSRS-6 LL 0.3460±0.0042, RMSE(bins) 0.0653±0.0011, AUC 0.7034±0.0023. FSRS-rs (FSRS-6 with recency weighting): 0.3443 / 0.0635 / 0.7074. FSRS-5: 0.3561 / 0.0742 / 0.7010. When same-day reviews are evaluated, FSRS-6 scores 0.3842 / 0.0985 / 0.6830. — [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)
- The averages are weighted by each user's review count. Absolute RMSE values depend on the binning, weighting and outlier filter, so the author advises against focusing on them. Optimized FSRS-6 beats default parameters for 84.3% of users, and default parameters win more often when data is scarce. — [Expertium, Benchmark](https://expertium.github.io/Benchmark.html)
- "RMSE is strongly correlated with the number of reviews, logloss is strongly correlated with retention." — Expertium in [Anki forum](https://forums.ankiweb.net/t/how-many-reviews-for-accurate-optimization/53320)
- Anki's health check runs only when there are more than 300 training items. It uses a 5-split time-series evaluation and passes if adjusted LL ≤ 1.11 or adjusted RMSE ≤ 1.53. The baselines are `0.623·(4r(1−r))^0.738` for LL and `0.0135/(r^0.504−1.14) + 0.176/((c/1000)^0.825+2.22) + 0.101` for RMSE, where r is retention and c is item count. — [Anki params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- Anki 25.06 removed the "Evaluate" button. — [Expertium, Benchmark](https://expertium.github.io/Benchmark.html)
- fsrs-rs `evaluate()` is in-sample on whatever parameters it is given and recency-weights items by 0.25+0.75·(idx/len)³. The out-of-sample variant is `evaluate_with_time_series_splits` with 5 splits. — [fsrs-rs inference.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/inference.rs), [dataset.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/dataset.rs)
- The calibration tooling in fsrs-optimizer uses 20 predicted-R bins that are log-spaced, so bins are finer near R=1. Per-bin intervals come from a likelihood-ratio method that the source comment says covers better than Clopper-Pearson. It reports ICI, E50, E90 and Emax from LOWESS, plus a weighted linear fit (intercept and slope). — [fsrs_optimizer.py `plot_brier`/`load_brier`](https://github.com/open-spaced-repetition/fsrs-optimizer/blob/main/src/fsrs_optimizer/fsrs_optimizer.py); bin function in [inference.rs `get_bin`](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/inference.rs)

### Inferences
- Plugging into Anki's formula (derived): at 90% retention the RMSE baseline is about 0.099 at c=300, 0.085 at c=1,000 and 0.050 at c=10,000. The pass thresholds are about 0.151, 0.130 and 0.077, and the LL threshold is about 0.325. At 85% retention the LL threshold is about 0.421. Use the same formula to label a single user's metrics as "normal for your data size".
- Below a few hundred long-term reviews, per-user metrics are mostly noise. Treat about 300 items (Anki's gate) as the minimum before showing any verdict.

### Gaps
- No primary source gives the distribution of per-user FSRS-6 metrics by review count. The plots exist only as forum images.

## 2. Testing against reference implementations

### Takeaway
Golden tests should replay fixed rating/time sequences with fuzz off. py-fsrs ships exact expected values to reuse. The biggest cross-implementation risk is how "elapsed days" is computed, and py-fsrs and fsrs-rs/Anki compute it differently.

### Cited Findings
- py-fsrs golden values come from `Scheduler(enable_fuzzing=False)`, start time 2022-11-29 12:30 UTC, each review at `card.due`. Expected intervals are `[0, 2, 11, 46, 163, 498, 0, 0, 2, 4, 7, 12, 21]`. After Again, Good×5 at day offsets [0,0,1,3,8,21], S = 53.62691 and D = 6.3574867 (abs tol 1e-4). Ten Easy ratings give D == 1.0. Fuzz tests seed `random` and expect intervals of 12 (seed 42) and 11 (seed 12345). — [py-fsrs test_basic.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_basic.py)
- Other invariant tests in py-fsrs: stability ≥ STABILITY_MIN (0.001) after 1000 Agains; a same-day Hard does not lower stability; `maximum_interval` is respected; `reschedule_card` reproduces the state from the logs. — [test_basic.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_basic.py), [scheduler.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)
- fsrs-rs tests itself for determinism (`evaluate_is_deterministic`, bit-exact `to_bits()` comparisons) and documents example next states in doctests. — [inference.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/inference.rs)
- **Day counting differs:**
  - py-fsrs: `days_since_last_review = (review_datetime - card.last_review).days`, which floors 24-hour UTC periods. Retrievability uses the same `.days`. Datetimes must be tz-aware UTC, or a ValueError is raised. — [scheduler.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)
  - Anki: revlog Δt = difference of `floor((next_day_at − review_time)/86400)`, measured from the local rollover hour (default 4am). — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), [timing.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/timing.rs)
  - fsrs-rs reference converter: calendar-date difference in the user's tz after subtracting `next_day_starts_at` hours. — [convertor_tests.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/convertor_tests.rs)
- **Rounding:** fsrs-rs FSRS-6 `next_interval` returns an unrounded float clamped to [0, S_MAX] (in [model_v6.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/model_v6.rs)). py-fsrs rounds it, enforces at least 1 day and caps at `maximum_interval`. Its fuzz range never goes below 2 days. — [scheduler.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)
- py-fsrs warns that its optimizer results "may be slightly different" from Anki's for the same logs. — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- **Converting a review log into training items** (fsrs-rs and Anki):
  - A card's history must start at its last first-learn entry. Entries before a Reset are dropped, and cramming and manual entries are removed (`has_rating_and_affects_scheduling`).
  - Each review after the first becomes one item containing its full prefix history, but only if Δt > 0. Same-day reviews stay inside the history with Δt=0 but are never targets.
  - When training, Anki drops cards with no learning entry, which means histories are incomplete.
  - Sources: [params.rs `reviews_for_fsrs`](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), [convertor_tests.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/convertor_tests.rs)
- **Data thresholds:**
  - fsrs-rs FSRS-6: fewer than 8 items returns defaults; fewer than 64, or only first reviews, returns pretrained initial stabilities only. An outlier filter drops the rarest Δt groups per first rating (up to 5%, at least 20 items) and groups with fewer than 6 items or Δt above 100 days (365 for Easy). — [training.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/training.rs), [dataset.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/dataset.rs)
  - py-fsrs Optimizer: with fewer than 512 logs it returns the unchanged defaults, and optimal retention needs at least 512. — [test_optimizer.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_optimizer.py), [optimizer.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/optimizer.py)
  - An Anki code comment mentions 400 items. Forum answers conflict (8/64 vs 100/400). — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), [forum](https://forums.ankiweb.net/t/how-many-reviews-for-accurate-optimization/53320)

### Inferences
- The app schedules with py-fsrs (24-hour UTC floors) but fits with fsrs-rs-python on FSRSItems it builds itself. The Δt in those items must be computed exactly the way py-fsrs computes elapsed days when scheduling. If it isn't, the fitted parameters describe a different clock. For example, a review at 23:00 followed by one at 08:00 is 0 days in py-fsrs and 1 day in Anki.
- The core test is a cross-check: replay each card's log through the py-fsrs Scheduler, replay it through fsrs-rs-python's memory-state function with the fitted parameters, and assert that S and D agree within about 1e-3 relative. A mismatch exposes conversion bugs.

### Gaps
- No published cross-implementation golden fixtures with fixed tolerances were found. The 1e-4 tolerance is py-fsrs's own. The exact S_MIN/S_MAX values in fsrs-rs were not captured.

## 3. Simulation-based testing

### Takeaway
The fsrs-rs simulator gives per-day series (reviews, learns, memorized, cost, correct) to check workload against desired retention and recall against prediction. No primary source documents a parameter-recovery test, so the app has to build one.

### Cited Findings
- fsrs-rs `simulate()` returns `memorized_cnt_per_day`, `review_cnt_per_day`, `learn_cnt_per_day`, `cost_per_day`, `correct_cnt_per_day` and `introduced_cnt_per_day`. `SimulatorConfig` covers deck_size, learn_span, max_cost_perday, max_ivl, rating probabilities, learn/review limits, step transitions and costs, and hooks for review priority and post-scheduling. Workload helpers are `expected_workload` and `expected_workload_with_existing_cards`. — [simulation.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/simulation.rs)
- py-fsrs tests simulated cost: `round(simulation_cost_0_75) == 239312`. — [test_optimizer.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_optimizer.py)
- Anki's simulator estimates reviews or minutes per day from real memory states. Above 90% desired retention the workload "increases very quickly", and above 97% it "can be overwhelming". "Compute minimum recommended retention" was removed in 25.07. — [Anki manual](https://docs.ankiweb.net/deck-options.html)

### Inferences
- Property tests to run:
  - Workload rises monotonically and convexly with desired retention.
  - In simulation, correct/reviewed on due reviews ≈ desired retention.
  - A review cap creates a backlog, and recall on overdue cards drops to roughly the predicted R(t).
  - No interval exceeds max_ivl, and no due date lands in the past.
- Parameter-recovery test: generate synthetic users with known parameters (Bernoulli outcomes from R), feed the logs through the app's own converter, fit with fsrs-rs-python, and check:
  - log loss on held-out data is near that of the true parameters;
  - predicted intervals agree. Individual parameters can be weakly identifiable, so compare predictions rather than the raw parameters.

### Gaps
- No published synthetic parameter-recovery study for FSRS was found. The FSRS4Anki simulator notebook was not reviewed.

## 4. Pitfalls in the wild and how mature systems guard against them

### Takeaway
Most failures are data-pipeline failures: the wrong day boundary, polluted logs, or incomplete histories. Anki guards against them by filtering the review log, using a rollover hour and a cutoff date, and setting conservative defaults.

### Cited Findings
- **Day boundary and DST:** Anki computes "today" with a rollover hour and the local UTC offset for each timestamp, "includ[ing] the daylight savings offset". — [timing.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/timing.rs). py-fsrs is "UTC only". — [README](https://github.com/open-spaced-repetition/py-fsrs)
- **Polluted logs:** both Anki and the benchmark exclude manual reschedules, resets and cramming (filtered decks without rescheduling). — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)
- **Imported or incomplete histories:**
  - Anki offers "Ignore cards reviewed before" for imported scheduling data.
  - When history is missing, it assumes 90% historical retention, which is adjustable.
  - It tracks a `revlogs_complete` flag.
  - Sources: [Anki manual](https://docs.ankiweb.net/deck-options.html), [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- **Retraining:** "once every month is sufficient". Don't hand-edit parameters or copy someone else's. A few hundred reviews counts as low data. — [Anki manual](https://docs.ankiweb.net/deck-options.html)
- **Regressions:** after optimizing, Anki can revert to the current parameters if the new ones look worse on a check. Only part of this logic was seen (`params = current_params` when a short-term stability check fails), so this is partly unverified. — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- **Changing retention or parameters:** by default Anki does not reschedule existing cards. Rescheduling can make many cards due at once. — [Anki manual](https://docs.ankiweb.net/deck-options.html)
- Learning steps of 1 day or more, including 23h, are "not recommended" with FSRS. The default max interval is 100 years. — [Anki manual](https://docs.ankiweb.net/deck-options.html)
- Parameters are fitted per preset, from all decks that share it. — [Anki manual](https://docs.ankiweb.net/deck-options.html)

### Inferences
- Mixed review types: problem-solving "skills" and flashcards produce different rating semantics and retention, so give them separate parameter sets.
- Duplicate or lost reviews: make the review ID an idempotency key, apply an undo as a log deletion followed by a replay from the log, and recompute card state from the log rather than mutating it.
- Rating inconsistency on problems: define the rubric up front, for example fail = could not finish without the solution.
- Anki's revlog Δt uses fixed 86,400-second steps back from the next rollover. Near a DST change this can shift by one day for reviews within an hour of rollover. This is unverified.

### Gaps
- No primary documentation was found on how undo or duplicate reviews are handled in FSRS logs.

## 5. Showing the student it works without misleading

### Takeaway
Show true retention against desired retention (with Wilson CIs), a calibration plot with per-bin intervals, out-of-sample LL and RMSE against the count-adjusted baseline, and a parameter history. Hide verdicts below minimum counts.

### Cited Findings
- Anki's true retention counts only reviews with an interval of at least 1 day and only the first review of each day. Again = fail, everything else = pass. It splits young/mature at 21 days and reports today, yesterday, week, month, year and all time. — [Anki stats](https://docs.ankiweb.net/stats.html), [retention.rs](https://github.com/ankitects/anki/blob/main/rslib/src/stats/graphs/retention.rs)
- "Estimated total knowledge" = average R × cards reviewed at least once. — [Anki stats](https://docs.ankiweb.net/stats.html)
- Benchmark-style calibration displays: log-spaced bins with likelihood CIs, ICI/E50/E90, and a regression slope/intercept. — [fsrs_optimizer.py](https://github.com/open-spaced-repetition/fsrs-optimizer/blob/main/src/fsrs_optimizer/fsrs_optimizer.py)

### Inferences
- Derived 95% Wilson intervals at an observed retention of 0.90: n=30 → [0.744, 0.965]; n=100 → [0.826, 0.945]; n=400 → [0.867, 0.926]; n=1000 → [0.880, 0.917].
- So a "true retention vs 90%" claim needs about 400 or more interday reviews to resolve ±3 percentage points. Show the intervals, grey out bins under about 30 reviews, and use out-of-sample metrics only (not fsrs-rs `evaluate` on the training data).
- Compare the expected retention, mean predicted R at review time, with observed retention. That is a direct calibration check that stays valid when reviews are overdue.
