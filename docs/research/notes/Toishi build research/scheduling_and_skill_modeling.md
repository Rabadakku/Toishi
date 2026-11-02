# Scheduling and Skill Modeling for a Skill-Level Spaced-Repetition Problem-Solving App (FSRS + FIRe-style credit + Elo + prerequisite graph)

Research date: 2026-11-01. Version numbers and dates are as of that day unless noted. Where I ran code, I installed `fsrs` 6.3.2 from PyPI in a scratch virtualenv and called its public and private methods directly. Those numbers are labeled "computed with fsrs 6.3.2" and come from the formulas in the cited source file.

Labeling convention: **Cited Findings** are things a source says. **Inferences** are my own reasoning or design proposals for this app. Anything in Inferences is NOT established practice unless a citation says so.

---

## 1. FSRS: current version, memory model, formulas, parameters, ratings, desired retention, same-day reviews, optimizer, py-fsrs API, Anki integration (load balancing, fuzz, Easy Days)

### Takeaway
FSRS-6 (21 parameters, w0–w20) is the current *released* model. py-fsrs has used it since v6.0.0 (21 May 2025), and the latest py-fsrs is 6.3.2 (9 Aug 2026, MIT, Python ≥3.10). Anki moved to it in 25.07. FSRS-7 exists in the benchmark and in parts of fsrs-rs: it handles fractional (sub-day) intervals and same-day reviews better. But as of June 2026 it had not been released by open-spaced-repetition or merged into Anki. The py-fsrs optimizer returns default parameters until it has ≥512 non-same-day reviews.

### Cited Findings

**Versions and status**
- PyPI `fsrs` latest = **6.3.2, released Aug 9, 2026**; MIT License; requires Python >=3.10. History includes 6.3.1 (Mar 10 2026), 6.3.0 (Oct 13 2025), 6.2.0 (Oct 5 2025), 6.1.0 (Jun 13 2025), 6.0.0 (May 21 2025), 5.0.0 (Jan 24 2025) — [PyPI fsrs](https://pypi.org/project/fsrs/)
- py-fsrs v6.0.0 notes: "This release upgrades Py-FSRS to use the new FSRS 6 model". FSRS 6 adds two parameters for same-day reviews and better forgetting modeling. Breaking changes: custom parameters need 21 values instead of 19, and `Card.get_retrievability()` became a `Scheduler` method. v6.2.0 added "Add method for rescheduling cards" and "Update default parameters". v6.3.0 added JSON serialization. v6.3.2 "Fixed the same-day Hard stability floor" — [py-fsrs releases](https://github.com/open-spaced-repetition/py-fsrs/releases)
- FSRS version history (Jarrett Ye, "The History of FSRS for Anki", LessWrong, 14 Jul 2025): v4 (Jul 2023) switched to a power-law forgetting curve and added hard_penalty/easy_bonus, giving 17 params. FSRS-4.5 (Dec 2023) used a flatter curve. FSRS-5 (Jul 2024) added short-term review effects and improved initial difficulty, with about 4% lower error. The optimizer later gained recency weighting, about 4.5% lower error. The post ends: "FSRS-6 is coming." — [LessWrong](https://www.lesswrong.com/posts/G7fpGCi8r7nCKXsQk)
- Anki **25.07**: "FSRS-6 brings further algorithm improvements". The Evaluate button was replaced by an optional health check during optimization. Anki moved to fsrs-rs v3.0.0 and then 4.1.1, and updated the default FSRS-6 decay — [Anki 25.07 notes](https://newreleases.io/project/github/ankitects/anki/release/25.07). The Anki manual says "Compute minimum recommended retention" (CMRR) was removed in Anki 25.07 — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html)
- Anki **26.05** (released "16 Jun", year from the tag) includes "Make descending retrievability a pure R sort" (#4400), "Improve sibling dispersal in the load balancer, including across presets" (#4640), "Expose card decay and desired retention to the custom scheduler" (#4880), and "Speed up FSRS memory state updates by batching" (#4335) — [Anki 26.05 release](https://github.com/ankitects/anki/releases/tag/26.05)
- **FSRS-7 status**: On a 5 Jun 2026 Anki forum thread, Danika_Dakika said FSRS-7 is "an in-process project" that "hasn't been merged into or released by open-spaced-repetition", with no Anki PR yet — [Anki forum: When will Anki integrate FSRS-7?](https://forums.ankiweb.net/t/when-will-anki-integrate-fsrs-7/69997)
- The srs-benchmark README calls FSRS-7 "the newest version". It is "designed for fractional (non-integer) interval lengths" and is "the only version that can give realistic predictions of probability of recall for same-day reviews". Its forgetting curve has 8 optimizable parameters — [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)
- The fsrs-rs README mentions "the FSRS-6 and FSRS-7 Cost ADR policy" and "FSRS-7 training with card IDs". The license is BSD-3-Clause. Bindings include fsrs-rs-python, C, Node.js, Dart, and PHP — [fsrs-rs](https://github.com/open-spaced-repetition/fsrs-rs). The latest fsrs-rs release is v6.6.0 ("06 Jun"; the page shows no year). v6.0.0 ("29 May") added per-card desired retention and parameters, and v6.3.0 added "initialize state from history" — [fsrs-rs releases](https://github.com/open-spaced-repetition/fsrs-rs/releases)

**Benchmark (srs-benchmark README, ~10k Anki collections)** — [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)
- Without same-day reviews (9,999 collections, 349.9M evaluation reviews), log loss / RMSE(bins) / AUC:
  - FSRS-7: 0.3401 / 0.0634 / 0.7167
  - FSRS-7 default params: 0.3620 / 0.0910 / 0.7029
  - FSRS-6: 0.3460 / 0.0653 / 0.7034
  - FSRS-5: 0.3561 / 0.0742 / 0.7010
  - GRU: 0.3328 / 0.0549 / 0.7324
  - RWKV-Instant: 0.2773 / 0.02502 / 0.8329
  - HLR: 0.4694 / 0.1275 / 0.6369
- With same-day reviews: FSRS-7 0.3206 / 0.0615 / 0.7475, FSRS-6 0.3842 / 0.0985 / 0.6830, FSRS-5 0.4565 / 0.1175 / 0.6761. FSRS-6 degrades much more than FSRS-7 when same-day reviews are included.
- The README is inconsistent about dataset size: it says both "20 thousand people" (~1.7B reviews) and "10 thousand users" (~727M reviews).

**Memory model (DSR: Difficulty D ∈ [1,10], Stability S in days, Retrievability R)**
- Forgetting curve (FSRS-6, trainable decay):
  `R(t,S) = (1 + factor · t/S)^(−w20)`, with `factor = 0.9^(−1/w20) − 1`, so that R(S,S) = 0.9 — [FSRS wiki: The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)
- py-fsrs code: `DECAY = −w20`, `FACTOR = 0.9^(1/DECAY) − 1`. Retrievability `R = (1 + FACTOR·t/S)^DECAY`, where **t = whole days** since last review (`max(0, (now − last_review).days)`). It returns 0 if the card has never been reviewed — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Initial stability: `S0(G) = w[G−1]` (G = 1..4 for Again..Easy), clamped ≥ 0.001 — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Initial difficulty: `D0(G) = w4 − e^(w5·(G−1)) + 1`, clamped to [1,10] — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py); this form was introduced in FSRS-5 — [FSRS wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)
- Difficulty update (linear damping plus mean reversion toward D0(Easy)):
  - `ΔD = −w6·(G−3)`
  - `D' = D + (10 − D)·ΔD/9`
  - `D'' = w7·D0(4) + (1 − w7)·D'`, clamped to [1,10]
  - Source: [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py). Mean reversion targets D0(4) since FSRS-5 — [FSRS wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)
- Stability after a successful review (Hard/Good/Easy):
  `S' = S·(1 + e^(w8)·(11 − D)·S^(−w9)·(e^((1−R)·w10) − 1)·hard_penalty·easy_bonus)`, where hard_penalty = w15 if Hard (else 1) and easy_bonus = w16 if Easy (else 1) — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Stability after a lapse (Again):
  `S'_f = min( w11·D^(−w12)·((S+1)^(w13) − 1)·e^((1−R)·w14) , S / e^(w17·w18) )` — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Same-day (short-term) stability, FSRS-6:
  `S' = S · e^(w17·(G − 3 + w18)) · S^(−w19)`. The wiki notes that SInc converges to 1 and that SInc ≥ 1 should hold when G ≥ 2 — [FSRS wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm). py-fsrs floors the increase at 1.0 for Hard/Good/Easy — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Interval from desired retention r:
  `I = (S/FACTOR)·(r^(1/DECAY) − 1)`, rounded to whole days and clamped to [1, maximum_interval] — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- Default FSRS-6 parameters w0..w20: 0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542 — [FSRS wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm); identical in [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py) and in the installed 6.3.2 `Scheduler.__init__` signature
- Parameter meanings, as they appear in the formulas above:
  - w0–w3: initial S per grade
  - w4, w5: initial D
  - w6: difficulty delta
  - w7: mean reversion
  - w8–w10: recall stability growth
  - w11–w14: post-lapse stability
  - w15: Hard penalty
  - w16: Easy bonus
  - w17–w19: same-day
  - w20: decay
  - Source: [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)

**How ratings move state: worked numbers (computed with fsrs 6.3.2, default params, fuzz off)** — formulas from [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- First review, default learning steps (1 min, 10 min):

  | Rating | State after | S | D | Next due |
  |---|---|---|---|---|
  | Again | Learning | 0.212 | 6.41 | 1 min |
  | Hard | Learning | 1.293 | 5.11 | 5.5 min |
  | Good | Learning | 2.307 | 2.12 | 10 min |
  | Easy | Review | 8.296 | 1.0 | 8 days |

- With `learning_steps=()`, a first Good goes straight to Review with S = 2.31 and is due in 2 days. A second review at day 2 (R = 0.90) gives:

  | Rating | S | D | Next |
  |---|---|---|---|
  | Again | 0.61 | 7.39 | relearn in 10 min |
  | Hard | 7.51 | 4.75 | 8 d |
  | Good | 10.96 | 2.11 | 11 d |
  | Easy | 18.52 | 1.0 | 19 d |

- Difficulty update starting from D = 5: Again → 8.34, Hard → 6.67, Good → 4.99, Easy → 3.31.
- Same-day review starting from S = 2.3065: Again → 0.775, Hard → 2.307, Good → 2.307 (no gain, because SInc is floored to 1), Easy → 3.946.
- Spacing effect built into the recall formula, S = 10 and D = 5, Good review after t days:

  | t (days) | R | S' after Good | Gain (S'/S) | S' after Hard | S' after Again |
  |---|---|---|---|---|---|
  | 1 | 0.986 | 13.05 | ×1.30 | | |
  | 5 | 0.940 | 22.9 | ×2.29 | | |
  | 10 | 0.900 | 32.0 | ×3.20 | 23.3 | 1.39 |
  | 20 | 0.846 | 44.7 | ×4.47 | | |
  | 30 | 0.809 | 53.6 | ×5.36 | | |

  In short, early reviews yield little stability gain.

**Desired retention and the shape of the FSRS-6 curve**
- Anki's default desired retention is 90%. "Above 90% the workload increases very quickly, and above 97% the workload can be overwhelming." Desired retention can now differ per deck within a preset — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html)
- Raising desired retention "will shorten all the intervals, not just the first intervals" — [Anki FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)
- Computed with fsrs 6.3.2 (default w20 = 0.1542, FACTOR ≈ 0.980), using the interval formula from [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py):
  - Intervals at S = 10 d: desired retention 0.80 → 33 d, 0.85 → 19 d, 0.90 → 10 d, 0.95 → 4 d.
  - R at S = 10: t = 1 → 0.986, 5 → 0.940, 10 → 0.900, 20 → 0.846, 40 → 0.782, 100 → 0.693.
- py-fsrs `Optimizer.compute_optimal_retention(parameters)` simulates desired retention from 0.70 to 0.95 (1,000 cards each) and picks the lowest-cost value. It needs ≥512 ReviewLogs, and every log must have a non-None `review_duration` — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py)

**Same-day reviews and learning steps**
- py-fsrs handles a review less than 1 day after the last one as follows — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py):
  - In Learning or Relearning: `_short_term_stability` and `_next_difficulty` are applied.
  - In Review: only `_short_term_stability` is applied, and difficulty is still updated.
  - Otherwise the long-term `_next_stability` is used with R at review time.
- Learning-step rules in py-fsrs:
  - Again resets to step 0.
  - Hard on step 0 with one step uses 1.5× that step. Hard on step 0 with two or more steps uses the average of the first two steps.
  - Good advances one step, or graduates on the last step.
  - Easy graduates immediately.
  - Review + Again goes to Relearning if relearning steps exist.
  - Defaults: `learning_steps=(1 min, 10 min)` and `relearning_steps=(10 min,)`. Both can be disabled with `()`.
  - Source: [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py), [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- The Anki manual says to keep learning and relearning steps under one day so they finish the same day (e.g., 10m or 30m), and that "23h is not recommended". Leaving steps empty lets FSRS handle short-term scheduling, which the manual labels experimental — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html)
- In optimization, same-day reviews update card state but add no loss term ("only compute step-loss on non-same-day reviews") — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py). In FSRS, short-term reviews are time-series features, not training labels, and their exact intervals are ignored — [LessWrong history](https://www.lesswrong.com/posts/G7fpGCi8r7nCKXsQk)

**Optimizer: how much data is needed**
- py-fsrs returns `DEFAULT_PARAMETERS` unless there are **≥512 countable (non-same-day) reviews** (`if num_reviews < mini_batch_size: return list(DEFAULT_PARAMETERS)`, mini_batch_size = 512) — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py)
- Other py-fsrs optimizer details — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py):
  - Uses only the first 64 reviews per card.
  - 5 epochs, Adam with lr = 4e-2 and cosine annealing.
  - Binary cross-entropy loss, where `recall = 0 if rating == Rating.Again else 1`, so **Hard counts as a success**.
  - Parameters are clamped to bounds, and the best epoch is kept.
- Anki: since 24.06.3, "the optimizer can be used with any number of reviews". Re-optimize about once a month, or each time reviews double (100, 200, 400…) — [Anki FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)
- Expertium on the Anki forum (flagged "IIRC"): "pretrain … starts at 8 reviews and full optimization starts at 64 reviews". "RMSE is strongly correlated with the number of reviews" — [Anki forum: how many reviews](https://forums.ankiweb.net/t/how-many-reviews-for-accurate-optimization/53320). This conflicts with py-fsrs's 512 threshold; the two are different implementations.
- "In some cases, FSRS may even be more accurate if you only use Again and Good." FSRS uses only interval lengths and grades. Review time was used only by CMRR — [Anki FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)
- Use separate presets (parameter sets) for materials that differ, such as Japanese vs geography — [Anki FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)

**py-fsrs API (fsrs 6.3.2)** — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs); signatures verified on the installed package
- `pip install fsrs`. Install `pip install "fsrs[optimizer]"` for the Optimizer, which needs torch. The library is **UTC-only**: `review_datetime` must be timezone-aware UTC, or it raises ValueError.
- `Scheduler(parameters=DEFAULT_PARAMETERS, desired_retention=0.9, learning_steps=(timedelta(minutes=1), timedelta(minutes=10)), relearning_steps=(timedelta(minutes=10),), maximum_interval=36500, enable_fuzzing=True)`
- `Scheduler.review_card(card, rating, review_datetime=None, review_duration=None) -> (Card, ReviewLog)`. `review_duration` is in ms — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- `Scheduler.get_card_retrievability(card, current_datetime=None) -> float`
- `Scheduler.reschedule_card(card, review_logs) -> Card`: replays history under new parameters.
- `Scheduler.to_dict/from_dict/to_json/from_json`
- `Card(card_id=None, state=State.Learning, step=None, stability=None, difficulty=None, due=None, last_review=None)`. All fields can be set directly. `card_id` defaults to epoch milliseconds.
- `State`: Learning = 1, Review = 2, Relearning = 3.
- `Rating`: Again = 1, Hard = 2, Good = 3, Easy = 4.
- `ReviewLog(card_id, rating, review_datetime, review_duration)`
- `Optimizer(review_logs)` with `.compute_optimal_parameters(verbose=False)` and `.compute_optimal_retention(parameters)`. The README notes results "may differ slightly from Anki's optimizer".

**Fuzz** — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- No fuzz below 2.5 days.
- Fuzz factors: 0.15 for [2.5, 7), 0.10 for [7, 20), 0.05 for ≥20 days.
- `delta = 1 + Σ factor·max(min(I, end) − start, 0)`, `min_ivl = max(2, round(I − delta))`, `max_ivl = min(round(I + delta), maximum_interval)`. The interval is drawn uniformly in [min_ivl, max_ivl], and only when the resulting state is Review.

**Anki load balancer and Easy Days**
- Anki 24.11: "within your fuzz range, Anki will now try to pick days that have fewer reviews waiting"; Easy Days: "you can now tell Anki to try avoid certain days of the week"; "Decks can now be sorted by descending retrievability" (simulations favor it with a backlog) — [Anki 24.11 notes](https://newreleases.io/project/github/ankitects/anki/release/24.11)
- Load balancer source — [Anki load_balancer.rs](https://raw.githubusercontent.com/ankitects/anki/main/rslib/src/scheduler/states/load_balancer.rs):
  - It only applies when interval ≤ 90 days (`MAX_LOAD_BALANCE_INTERVAL = 90`, cache 99 days).
  - Each candidate day in the fuzz range gets weight `(1/review_count)^2.15 × (1/target_interval)^3 × sibling_modifier × easy_days_modifier`, and an empty day gets 1.0. Note that the doc comment says `^2`, but the code uses 2.15.
  - Sibling modifiers across ±5 days: `[1.0, 0.8, 0.6, 0.4, 0.2, 0.000001, 0.2, 0.4, 0.6, 0.8, 1.0]`. Multiple siblings multiply.
  - Easy-day load modifiers: Minimum 0.0001, Normal 1.0. A "Reduced" day becomes Minimum if its load exceeds the average of the other days in the window, else Normal.
  - The day is sampled from a seeded `WeightedIndex`.
- The manual says that setting all days to Reduced or Minimum gives the same workload as all Normal, and that changes affect only future intervals — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html)

### Inferences
- **Use py-fsrs 6.3.2 (FSRS-6) and pin it.** Wrap it behind an interface, so that FSRS-7 can be swapped in if and when it ships in py-fsrs: fractional intervals and better same-day modeling would help an app with same-day reinforcement. As of this research, FSRS-7 should be treated as unreleased.
- **Pitfall: py-fsrs computes R using whole days** (`.days`). So R = 1.0 for any check within 24 h of the last review, and R jumps in steps. For sub-day triage or same-day reinforcement logic, compute R yourself from fractional days using the same formula.
- **Pitfall: same-day Good gives zero stability gain** under default parameters, because SInc is floored to 1 (computed above). The app's "immediate reinforcement with fresh problems" (design decision 6) will therefore not push the skill's next review later. That is arguably correct; see §8 on overlearning.
- **Pitfall: the optimizer treats Hard as a pass.** If the app maps "correct but needed a hint" to Hard, the optimizer will learn that as a successful recall. Decide deliberately (see §2).
- **Data volume (my arithmetic):** at roughly 15 graded skill reviews a day, 512 non-same-day reviews takes about 5 weeks, so the app will run on default parameters for its first month or more. Defaults were fit on Anki flashcards, not math skills.
- Persist Card/ReviewLog via `to_dict()` in SQLite JSON columns or explicit columns. Keep the raw review event table as the source of truth, so that `reschedule_card` / re-optimization can replay it.

### Gaps
- No primary source gave the exact FSRS-7 formulas or parameter count beyond "8 optimizable forgetting-curve parameters". fsrs-rs's FSRS-7 API is not documented in what I read.
- The exact Anki-native optimizer thresholds (8 reviews pretrain, 64 full) come only from a forum post marked "IIRC".
- Exact release years for fsrs-rs v6.x and Anki 26.05 are not shown on the pages I read; "June" is inferred to be 2026 from context.

---

## 2. Applying FSRS to SKILLS with variable problems (not fixed cards): validity, research/practitioner reports, and mapping difficulty/correctness/time/hints to a rating

### Takeaway
No source I found validates FSRS on skill-level scheduling with a fresh problem each review. FSRS was fit and benchmarked on Anki flashcard logs, and FSRS developers and forum volunteers are skeptical about using it for "practice". On the other side, the education literature shows that distributed practice of math problem types strongly improves 4-week retention. And skill-level memory models with multi-skill items (DAS3H) outperform item-only or skill-only models. So the skill-as-card design is plausible but unvalidated: treat FSRS's R as an approximation that must be re-fit on the app's own logs. The mapping from performance to rating has no standard; any mapping is the developer's choice.

### Cited Findings
- On an Anki forum thread about tuning FSRS for math and logical-reasoning problem cards (6 Sep 2026), volunteer Danika_Dakika wrote:
  - For memorizing, use FSRS. For practice, "There's no evidence that either of the algorithms, or even spaced-repetition scheduling in general" applies.
  - If a step was the failure point, "you'd probably benefit *more* from doing a completely separate problem."
  - "Practice problems work much better at getting the skill down."
  - "Do not tweak your parameters, or let an LLM tweak them for you."
  - The original poster grades "purely based on whether I can come up with a complete solving idea on my own."
  - This is a practitioner opinion, not research — [Anki forum: FSRS for math problem cards](https://forums.ankiweb.net/t/questions-about-tuning-fsrs-for-math-logical-reasoning-problem-cards/70949)
- Rohrer & Taylor ran two experiments with 216 college students learning one kind of math problem — [Rohrer & Taylor, USF digital commons](https://digitalcommons.usf.edu/psy_facpub/1770/):
  - Experiment 1: 10 problems in one session vs split across two sessions a week apart. The distributed-practice benefit was "nil" at 1 week but "extremely large" at 4 weeks.
  - Experiment 2: 3 vs 9 problems in one session. The extra six problems "had no effect on test scores 1 or 4 weeks later".
  - This is direct evidence that spacing works for math *problem types*, which supports scheduling at the skill level.
- DAS3H (Choffin et al.) models skill-level memory for items tagged with multiple skills — [DAS3H, arXiv 1905.06873](https://ar5iv.labs.arxiv.org/html/1905.06873):
  - Formula: `P = σ(α_s − δ_j + Σ_{k∈KC(j)} β_k + Σ_{k∈KC(j)} Σ_w [θ_{k,2w+1} log(1+c_{s,k,w}) − θ_{k,2w+2} log(1+a_{s,k,w})])`, with time windows {1/24, 1, 7, 30, +∞} days.
  - It beat DASH, AFM, PFA, and IRT on three math datasets (e.g., algebra05 AUC 0.826 vs best DASH 0.775).
  - The authors *propose*, but did not test, skill-review scheduling: pick the skill whose recall probability is closest to a threshold, then pick an item for it.
  - They warn that "an item involving only the target skill may not exist" and that very early skill reactivation can hurt long-term retention.
- FSRS treats cards independently. Asked about sibling-aware scheduling, Expertium said it "would require massive changes to Anki" (14 Sep 2025) — [Anki forum: reverse cards](https://forums.ankiweb.net/t/feature-request-fsrs-should-take-reverse-cards-into-account-when-scheduling/66404). Jarrett Ye notes some users had non-monotonic forgetting curves, likely from mixing different materials, and that siblings shown close together led to a "Disperse Siblings" add-on feature — [LessWrong history](https://www.lesswrong.com/posts/G7fpGCi8r7nCKXsQk)
- SuperMemo separates "topics" (read passively) from "items" (tested): "Unlike items, topics do not test knowledge" — [SuperMemo Guru: Topic](https://supermemo.guru/wiki/Topic). I found no SuperMemo guidance on scheduling procedural or problem-solving skills.
- Math Academy's spaced repetition "relies on the first-order signal: accuracy". Future versions will add "reference reliance (second-order) and timing (third-order)" — [Skycak, Spaced Repetition 2.0](https://justinmath.com/the-vision-for-version-2-of-math-academys-spaced-repetition-system/)
- Math Academy defines a repetition as "a successful review at the appropriate time". Raw credit is positive if passed and negative if failed, and its magnitude scales with the quality of work — [Skycak, FIRe article](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- The py-fsrs optimizer's label is binary (Again = 0; Hard/Good/Easy = 1) — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py). FSRS "may even be more accurate if you only use Again and Good" — [Anki FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)
- Response time carries signal. In Pelánek's geography practice data, after a correct answer the probability the next answer is correct fell from ~95% (very fast) to ~80% (slow) — [Pelánek et al., UMUAI adaptive practice](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf)
- Elo variants can use log response time (`E(t|s,p) = d_p − θ_s`) or a "high speed, high stakes" score `S = (2·correct − 1)(a_i·d_i − a_i·t_si)` for interfaces that show a time limit — [Pelánek, Elo in education (CAE)](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- Pelánek et al. found AFM a poor fit for programming because "response time carries information that binary correctness discards" — [Pelánek et al., AFM analysis](https://www.fi.muni.cz/~xpelanek/publications/afm-analysis.pdf)

### Inferences
- **The model is reasonable, but "recall" is redefined.** For a skill, "R" means P(solving a fresh, typical-difficulty problem of this skill unaided). Problem-to-problem variance in difficulty adds noise that flashcards don't have. FSRS will absorb this into lower apparent retention and noisier D. Mitigation: only count a review as an FSRS event when the problem's difficulty is near the skill's typical ("core") difficulty. See §7.
- **Proposed rating map (my proposal, not established).** Inputs are correctness, hints/reference use, and time relative to the user's running median for that skill, where t_med is a per-skill EMA of log-time on correct answers. Keep the label binary-compatible.
  - Again: wrong answer, OR needed a hint that revealed the method, OR looked at the worked solution.
  - Hard: correct, but with a minor nudge/hint, or time > 2× t_med. The optimizer will treat this as success.
  - Good: correct, unaided, time within normal range.
  - Easy: correct, unaided, time < 0.5× t_med, AND the user confirms it was effortless. Use sparingly. Optionally disable Easy entirely, per the FAQ's "Again/Good only" remark.
- **Gate FSRS updates by expected difficulty.** If the Elo model predicted P(correct) < ~0.5 for the chosen problem (a stretch problem) and the user failed, do not log Again on the skill. Log it to Elo only, and trigger the sub-skill tagging flow. If the problem was a "core" problem (P near the target), a failure is a genuine lapse. This implements design decision (2).
- **Consider separate parameter sets** per domain (math vs physics/chemistry vs C++), as the FAQ suggests separate presets for different material. Only do this once each domain has ≥512 reviews; before then, use one shared set.
- Rohrer & Taylor's overlearning result argues against long same-day reinforcement runs. Spacing, not same-session volume, drives 4-week retention.

### Gaps
- I found no published study or benchmark of FSRS (or SM-2) on skill-level scheduling with generated or varied problems, and no LeetCode-SRS tool with published retention data. Search results only surfaced hobby GitHub repos, which I did not evaluate.
- No source gives a validated mapping from hints and time to SRS grades for problem solving.

---

## 3. Math Academy's FIRe (Fractional Implicit Repetition) and repetition compression

### Takeaway
FIRe keeps a separate **encompassing graph** whose edges carry weights in [0,1]: the fraction of a simpler topic practiced inside an advanced one. Passing an advanced topic sends discounted credit *down* through multiple layers. Failing a simple topic sends discounted penalties *up* to topics that encompass it. Credit arriving early is discounted. Low-speed topics get no implicit credit. Due reviews are chosen to "knock out" as many other due reviews as possible, but a due review is never deferred to wait for a knock-out. The full propagation algorithm is proprietary. Only the per-topic update formulas are published.

### Cited Findings
- **Two graphs.** The encompassing graph is separate from the prerequisite graph. "Encompassed topics are usually prerequisites, but prerequisites are often not fully encompassed." The prerequisite graph is "forwards" (what to learn next). The encompassing graph is "backwards" (how later work credits earlier topics) — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Weights.** Each encompassing edge has weight 0–1, "the fraction of the simpler topic practiced". It can be read as the probability that a random advanced problem encompasses a random simpler problem. Weights are set explicitly only if they are:
  1. nontrivial,
  2. not inferable from repetition flow, and
  3. between topics close in the prerequisite graph.
  All others are treated as zero. Zero weights are common, for example when only conceptual familiarity is needed — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Credit flow.** Credit travels down "like lightning bolts" through second- and third-order encompassed topics. Full encompassings form a "trunk" along which credit travels unhindered. Partial ones let credit fade along branches. Penalties "travel upwards through the knowledge graph like growing trees". Example: a failure on adding a one-digit number to a two-digit number penalizes multiplying a two-digit number by a one-digit number — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/); [Hecker, Math Academy part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/)
- **Published per-topic update formulas** (Skycak's article; the current page calls the credit term `rawDelta`, while the archived version and Hecker's summary call it `netWork`):
  - `repNum → max(0, repNum + speed · decay^failed · rawDelta)`
  - `memory → max(0, memory + rawDelta) · 0.5^(days/interval)`
  - Variables:
    - `repNum`: accumulated successful spaced repetitions. Hecker notes this is not a literal count.
    - `memory`: expected current retention. The next rep is due when memory is sufficiently low.
    - `interval`: ideal days between rep n and n+1.
    - `speed`: student-topic learning speed, a ratio of student-ability speedup to topic-difficulty slowdown. At 2×, a review counts as 2 repetitions. At 0.5×, as 0.5.
    - `failed`: 1 or 0.
    - `rawDelta`: positive if passed, negative if failed, with magnitude scaled by quality of work.
    - `decay`: starts at 1 and grows as the rep becomes more overdue, so overdue failures move the student backward faster.
  - Sources: [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/), [archived version](https://gwern.net/doc/www/www.justinmath.com/9af2ce40376e836660c237a0e971d1896a163eee.html), [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/)
- **Early discounting:** "The magnitude of rawDelta is also discounted if the repetition was completed early relative to the desired interval". Earliness is judged by high `memory`. No formula is published — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Low-speed topics:** for a topic whose learning speed is below 1, "incoming implicit credit is discarded and explicit reviews are forced" — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **No deferral:** when a repetition is due, "we're not going to wait for an 'implicit knock-out' opportunity to open up". The system knocks it out with a more advanced topic if possible, otherwise gives an explicit review — [archived FIRe article](https://gwern.net/doc/www/www.justinmath.com/9af2ce40376e836660c237a0e971d1896a163eee.html)
- **Repetition compression:** the system picks a small set of tasks whose implicit repetitions knock out the other due reviews "like dominoes". It also fends off future reviews and climbs the graph evenly to keep options open. Raw spaced repetition in a densely encompassed subject would otherwise consume all study time — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/). The book claims that "on average most courses require only about one explicit review for each topic covered" — [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/). The selection algorithm (e.g., greedy set cover) is not named — [archived FIRe article](https://gwern.net/doc/www/www.justinmath.com/9af2ce40376e836660c237a0e971d1896a163eee.html)
- **Setting weights in practice** (Skycak's demo) — [Skycak, Setting encompassing weights](https://justinmath.com/setting-encompassing-weights):
  - Rows are (topic, prerequisite or "key prerequisite" several steps back), managed in a spreadsheet.
  - Questions asked include "if you only solved problems from this topic forever, would you forget [the prerequisite]?" and whether the topic practices the prerequisite "from first principles" or only a special case.
  - 0 = no credit, e.g., a special-case formula application. 0.5 for a "fuzzy" case, e.g., the geometric distribution under negative binomial, because "the solution is mostly encompassed, but the problem statement and priming are not". 1 = "the subskill is being fully leveraged, almost like direct practice".
  - Skycak has set "over 10,000" weights, and the total is "tens of thousands".
  - Warning: "You don't want to give students credit for something they aren't actually practicing, or they'll forget it."
- **Weights along chains** can be inferred by multiplying, e.g., 0.5 × 0.4 = 0.2. Distant topics are treated as zero. A course with n topics has n(n−1)/2 possible weights (499,500 for 1,000 topics). Non-ancestor encompassings, such as across courses, also exist — [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/)
- **Hecker's open questions:** the exact partial-credit algorithm is not given. Hecker presumes credit is low when a review is far ahead of schedule and high near the scheduled time. "Large distance" is undefined — [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/)
- **Other mechanics** — [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works), [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/):
  - Quizzes sample previously learned topics. A missed question triggers an immediate remedial review. Quiz difficulty is tuned so students average about 80%.
  - If a lesson is failed twice with no forward progress, remedial reviews on the relevant prerequisites are assigned.
  - After a long break, a new diagnostic moves the "knowledge frontier" back.

### Inferences
- The app's design (3) matches FIRe's credit flow down. Design (4) is a manual version of the penalty/remediation path. FIRe additionally flows penalties *up*: failing a sub-skill penalizes skills that encompass it. Consider adding that, since a broken sub-skill implies the advanced skill is weaker than its FSRS state says.
- For a single-user app with College Algebra → Calc 1 (likely hundreds of skills, not thousands), hand-setting weights only for close pairs and inferring the rest by max-product along paths (with a cutoff) follows MA's stated practice.
- Repetition compression is a weighted set-cover problem. A greedy pick (the problem whose skill set covers the most due-skill weight) is the standard approximation. This is my proposal; MA's method is unpublished.

### Gaps
- MA's exact discount function for early implicit credit, its interval schedule as a function of repNum and speed, how `decay` grows, and its compression algorithm are not public. The Math Academy Way book chapters were not directly accessible. Only Hecker's summary and Skycak's articles were.

---

## 4. Combining FSRS with implicit (fractional) credit in practice

### Takeaway
FSRS already discounts early reviews: the stability gain `e^((1−R)·w10) − 1` is small when R is high. So a clean way to give fractional implicit credit is to compute the full-Good FSRS update at the current R and apply only a fraction w of the stability increase. Keep these implicit events out of the FSRS optimizer's training log. No published system documents doing this with FSRS, so every formula below is my proposal.

### Cited Findings
- The FSRS recall-stability increment is proportional to `(e^((1−R)·w10) − 1)`. With S = 10 and D = 5, a Good at R = 0.986 gives ×1.30, at R = 0.90 gives ×3.20, and at R = 0.81 gives ×5.36 (computed with fsrs 6.3.2) — [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)
- FIRe discounts early implicit credit and forces explicit reviews for slow (speed < 1) topics — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- FIRe does not defer a due review while waiting for an implicit knock-out — [archived FIRe article](https://gwern.net/doc/www/www.justinmath.com/9af2ce40376e836660c237a0e971d1896a163eee.html)
- py-fsrs `Card` fields (stability, difficulty, last_review, due, state) can be set directly, so custom partial updates are possible without forking the library (verified by signature) — [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs)
- The py-fsrs Optimizer trains on whatever `ReviewLog`s it is given. Each log has only card_id, rating, datetime, and duration, so there is no field to mark a review as implicit — [py-fsrs optimizer.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/optimizer.py)
- fsrs-rs v6.0.0 added per-card desired retention and parameters — [fsrs-rs releases](https://github.com/open-spaced-repetition/fsrs-rs/releases)
- FSRS does not model related or sibling cards. That would "require massive changes to Anki" — [Anki forum: reverse cards](https://forums.ankiweb.net/t/feature-request-fsrs-should-take-reverse-cards-into-account-when-scheduling/66404)
- Skycak warns: "You don't want to give students credit for something they aren't actually practicing, or they'll forget it." — [Skycak, Setting encompassing weights](https://justinmath.com/setting-encompassing-weights)

### Inferences (all my proposals)
- **Option A: fractional stability, clock keeps running (recommended starting point).** On a passed explicit review of advanced skill A at time now, for each encompassed skill B with effective weight w_AB:
  1. `R_B = R(now − last_review_B, S_B)`, using fractional days.
  2. `S_full = next_recall_stability(D_B, S_B, R_B, Good)`
  3. `S_B ← S_B + w_AB · (S_full − S_B)`
  4. Do **not** change `last_review_B`. Leave D_B unchanged, or apply `w_AB · ΔD_Good`.
  5. Recompute `due_B = last_review_B + I(S_B)`. If that is earlier than now, B stays due.
  - Raising S while keeping the clock raises current R a bit and lengthens the interval. That means "push later, don't cancel". Early credit is automatically tiny because S_full ≈ S when R ≈ 1.
- **Option B: treat as a discounted virtual review.** Set `last_review = now` and `S ← S + w·(S_full − S)`. Pitfall: resetting the clock makes R jump to 1 even for w = 0.1, which overcredits heavily. Avoid it, or interpolate the due date instead: `due ← due + w·((now + I(S_full)) − due)`.
- **Guards:**
  - Skip implicit credit if B is in Learning or Relearning, or was failed within the last N days.
  - Cap cumulative implicit stability gain between explicit reviews, e.g., force an explicit review of B once S_B has grown by more than 2× through implicit credit alone. This mirrors MA's "explicit reviews forced" rule and Skycak's warning above.
  - Skip implicit credit for skills with poor history (high D, e.g., D > 8), the analogue of speed < 1.
- **Penalty up (design 4 extended):** when sub-skill B fails its direct check (Again on B), optionally shrink S for skills A that encompass B: `S_A ← S_A · (1 − w_AB·λ)`, with λ around 0.3. Or simply mark A for an earlier explicit review.
- **Optimizer hygiene:** store implicit events in a separate table. Feed only explicit reviews to `Optimizer`, as ReviewLogs. Pitfall: excluding implicit events means the optimizer sees long gaps with higher-than-expected success for well-covered sub-skills, which biases it toward faster stability growth. Including them as Good reviews biases it the other way. There is no clean answer. A possible middle path is to optimize only on skills with little implicit credit, or to treat it as an open question and monitor calibration (predicted R vs observed pass rate, binned).
- **Sibling spacing:** after an explicit review of A, avoid serving another problem heavily encompassing the same sub-skill B in the same session. That second success would mostly be short-term retrieval and would inflate B's credit. Pelánek's time-penalty idea and Anki's ±5-day sibling modifier are the closest precedents (§9).

### Gaps
- I found no published implementation, evaluation, or forum report of FIRe-style fractional credit layered on FSRS. The effect of implicit credit on FSRS calibration is untested.

---

## 5. Prerequisite / knowledge-graph modeling (KST/ALEKS, encompassing vs prerequisite edges and weights, graph sizes, semi-automatic construction)

### Takeaway
Use two edge types on one node set of skills: **prerequisite** edges (a DAG used for unlocking and diagnostics) and **encompassing** edges (weighted 0–1, used for implicit credit). Knowledge Space Theory gives the formal basis for "which skill sets are feasible" and the "outer fringe" of what is ready to learn. Math Academy runs thousands of topics, about 300 per course. LLMs and embedding methods can propose prerequisite edges, but expert review is still needed.

### Cited Findings
- **KST definitions** — [Emergent Mind: ALEKS/KST summary](https://www.emergentmind.com/topics/aleks) (a secondary aggregator summarizing Doignon/Falmagne and Falmagne et al.; see also [Knowledge Spaces and Learning Spaces, arXiv 1511.06757](https://arxiv.org/pdf/1511.06757), not fetched):
  - A knowledge structure (Q, K) is a domain Q of items plus a family K of feasible subsets, the knowledge states.
  - A knowledge space is closed under union.
  - A learning space adds "Learning Smoothness" and "Learning Consistency". Learning spaces are equivalent to antimatroids and well-graded knowledge spaces.
  - The inner fringe is the items removable from a state. The outer fringe is the items addable to it. In a learning space, a state is determined by its two fringes.
  - ALEKS offers outer-fringe items as "ready to learn".
- **ALEKS numbers** — [Emergent Mind: ALEKS](https://www.emergentmind.com/topics/aleks):
  - Beginning Algebra has about 650 items and a learning space of "many millions of states".
  - Elementary math has 416 items, with at most 35 items per assessment.
  - Over 1,940,473 learning occasions, the median probability of successfully learning an outer-fringe item was about 0.93.
- **Math Academy scale:** "multiple thousands of interlinked topics spanning 4th Grade through university-level math". A course is about 300 topics, and calculus has "several hundred topics" — [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works). Skycak alone has set over 10,000 encompassing weights — [Skycak, Setting encompassing weights](https://justinmath.com/setting-encompassing-weights)
- **Encompassing vs prerequisite:** two graphs, with weights in [0,1] only where nontrivial and topics are close. Composition by multiplication along chains. See §3 — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/), [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/)
- **ACE (AI-assisted construction of educational knowledge graphs, JEDM)** — [ACE paper](https://distantreader.org/stacks/journals-ojs/jedm/jedm-737.htm):
  - Concept pairs are ranked by a Prerequisite Rank Score, built from semantic and exact references between concept descriptions using all-MiniLM-L6-v2 embeddings.
  - An expert labels the top pairs as A→B, B→A, or neither. Pairs implied by transitivity are skipped, and redundant edges are removed.
  - On Metacademy (141 concepts), semantic references raised path recall from 0.485 to 0.684. At 50% expert-effort reduction, path recall was about 90%.
  - Baseline: GPT-4o-mini RAG prerequisite detection reached precision 87.23, recall 61.11, F1 71.92.
  - Ranking 141 concepts took 150 min with MiniLM and 9–12 min with FastText or Word2Vec.
- **LLMs predicting prerequisites zero-shot** — [arXiv 2507.18479](https://arxiv.org/html/2507.18479v1):
  - 13 models on the ESCO occupational-skills taxonomy (3,196 skills), not school math.
  - BERTScore F1 ranged 0.811–0.835. Semantic similarity was 0.60–0.71.
  - Conclusion: LLMs "can, to a significant extent, infer prerequisite skill relationships", with a single prompt and no significance testing.
- Pelánek's adaptive-practice paper says basic Elo is "probably not sufficient" for prerequisites, and suggests Bayesian networks for that case — [Pelánek et al., UMUAI](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf)

### Inferences
- **Schema (proposal):**
  - `skill(id, course, unit, section, enabled, …)`
  - `prereq_edge(src, dst)`: a DAG. Validate with topological sort on insert, and store its transitive reduction.
  - `encompass_edge(adv, sub, weight ∈ (0,1])`: set by hand for direct or close pairs.
  - Effective weight between distant skills = max over paths of the product of weights, cut off below about 0.1 or beyond 2–3 hops. This matches MA's "multiply along chains" and "distant = 0".
  - Precompute a sparse `credit_matrix[adv] = {sub: w_eff}` whenever the graph changes.
- Toggling courses, units, or sections off (design 8) should hide skills from the queue but **not** remove them from the credit graph. Disabled sub-skills can still receive implicit credit, or this can be made a setting. Open question.
- **Semi-automatic build (proposal):**
  1. An LLM drafts the skill list per section from the syllabus.
  2. The LLM proposes prerequisite and encompassing candidates with a suggested weight from the vocabulary {0, 0.25, 0.5, 1}, mirroring Skycak's examples.
  3. The human reviews the edges in a spreadsheet-like UI, ordered by confidence (ACE-style).
  4. Transitive edges are auto-skipped.
- **Size estimate (my inference):** College Algebra + Trig + Calc 1 at the granularity MA uses (about 300 topics/course) gives roughly 600–900 skills. A coarser "section-level" skill list would be 100–250.

### Gaps
- I did not retrieve primary ALEKS documentation or Doignon & Falmagne's text directly. The KST numbers come from a secondary summary.
- No source gives MA's per-topic count of encompassing edges, or how much effort the weights took per course.

---

## 6. Diagnosing which prerequisite caused an error (ITS approaches, Q-matrix/DINA/AFM/PFA, self-tagging reliability)

### Takeaway
Psychometric cognitive-diagnosis models (DINA) and logistic knowledge tracing (AFM, PFA, DAS3H) can apportion blame across the skills an item requires, given a Q-matrix. But they need much more data than one user generates, and additive models "explain away" across skills. Practical systems (Math Academy) use simpler rules: remediate the missed topic immediately, and after repeated failure assign remedial work on prerequisites. The app's plan (user tags a sub-skill, then a quick direct check confirms it) is a sound low-data design. I found no hard numbers on how accurate learners' self-diagnosis is.

### Cited Findings
- **DINA (conjunctive):**
  - `ξ_ij = Π_k α_jk^(q_ik)`, i.e., the student has every skill the item needs.
  - `P(Y_ij = 1) = (1 − s_i)^(ξ_ij) · g_i^(1 − ξ_ij)`, with slip `s_i = P(wrong | has all skills)` and guess `g_i = P(right | missing a skill)`.
  - Q-matrix `q_ik ∈ {0,1}`.
  - Posterior over attribute profiles by Bayes. Per-skill mastery = Σ_c P(profile c | y)·α_ck.
  - The Stan example uses Beta(5,25) priors on s and g.
  - Source: [Stan DINA case study](https://mc-stan.org/learn-stan/case-studies/dina_independent.html)
- **AFM:** `P = σ(α_i + Σ_k β_k q_jk + Σ_k γ_k q_jk t_ik)`, where t_ik = practice opportunities. Its assumptions include ignoring item difficulty and compensatory skills. Adding *random* made-up concepts improved RMSE in 60% of experiments, so Q-matrix fit can mislead. On a programming dataset, AFM "does not provide satisfactory fit and insights" — [Pelánek et al., AFM analysis](https://www.fi.muni.cz/~xpelanek/publications/afm-analysis.pdf)
- **PFA:** `m = β + Σ_k (γ_k·s_k + ρ_k·f_k)` over the item's skills, `P = 1/(1 + e^(−m))`. It "can handle multiple KCs for the same item". It is typically fit with EM and random restarts, and is degenerate if γ < ρ — [LASER KT module 2](https://laserkt.quarto.pub/module-2-logistic-knowledge-tracing-and-performance-factors-analysis); [Penn MOOT slides](https://learninganalytics.upenn.edu/MOOT/slides/W004V003.pdf). The explicit equations above are reconstructed from these sources' worked examples, as both pages note.
- **DAS3H** adds skill-specific time-window memory to multi-skill items. The authors note the additive form is compensatory ("explaining away") — [DAS3H](https://ar5iv.labs.arxiv.org/html/1905.06873)
- **Math Academy practice:**
  - A missed quiz question triggers an immediate remedial review on that topic.
  - If a lesson is halted twice with no progress, remedial reviews go to "the most relevant prerequisites".
  - Sources: [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works), [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Self-diagnosis evidence (physics):** about 200 algebra-based physics students. Self-diagnosis with a rubric, a worked solution, or answer-only ("struggle") reduced the gap between low and high prior-knowledge students on transfer — [Learning from mistakes, arXiv 1602.07253](https://arxiv.org/pdf/1602.07253):
  - Self-diagnosis score correlated with transfer only in the struggle group, on the typical problem (r = 0.54).
  - There was no correlation for any group on the challenging problem.
  - The paper reports **no accuracy percentage** for self-diagnosis.

### Inferences
- **Keep design (4) and make it Bayesian-lite (proposal):**
  - The user's tag is a strong prior on which sub-skill broke. The direct check is the observation.
  - If the check passes, the miss is attributed to "slip" or to integration of the skills, and the advanced skill takes the hit.
  - If it fails, the sub-skill gets Again in FSRS. The advanced skill is penalized less, or not at all, because the failure was explained by the sub-skill.
- **Offer a fixed error taxonomy** in the tagging UI: {sub-skill list from the encompassing edges, "careless/slip", "didn't know where to start (strategy/recognition)", "integration of steps"}. A "strategy" error is exactly what interleaving trains (§9) and belongs to the advanced skill itself.
- **Self-tag reliability:** since accuracy is unquantified, verify tags with the direct check (which the design already does). Log tag vs check outcome. Over time, the confirmation rate per sub-skill measures how reliable the user's tags are, e.g., if the user tags "algebra" and passes the check 90% of the time, those tags are mostly slips.
- **When enough data exists (hundreds of multi-skill attempts),** a per-user PFA or DAS3H fit over the Q-matrix (from encompassing edges) could auto-suggest the likely broken sub-skill before the user tags. This is not viable at launch.

### Gaps
- Web search budget ran out before I could retrieve primary sources on cognitive-tutor model tracing and bug libraries (BUGGY/DEBUGGY), and Corbett & Anderson (1995) directly. I have no citable specifics on bug-library effectiveness.
- I found no quantitative study of how accurately students identify which prerequisite caused their own math error.

---

## 7. Difficulty / ability modeling (Elo, IRT, Glicko), cold start, targeting a success probability, interaction with FSRS

### Takeaway
Elo with a decaying update size (`K = U(n) = a/(1 + b·n)`, a = 1, b ≈ 0.05) is the proven lightweight choice for adaptive practice. It matches joint-MLE Rasch estimates (r ≈ 0.97) in one online pass. Item difficulty normally needs about 100 learners to estimate well, which a single-user app will never have. So problem difficulty must start from author-assigned priors and be pooled at the skill level. Target success rates used in practice range from 65% to 80%.

### Cited Findings
- **Elo/Rasch:**
  - `P = 1/(1 + e^(−(θ_s − d_i)))`
  - `θ_s += K·(correct − P)`, `d_i += K·(P − correct)`, both starting at 0.
  - Earlier work used K = 0.4. A small K converges too slowly and a large K is unstable.
  - Recommended uncertainty function `U(n) = a/(1 + b·n)` with a = 1, b = 0.05, refit by grid search.
  - Source: [Pelánek, Elo in education](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- Pelánek's UMUAI paper uses α = 1, β = 0.06. Basic Elo matched JMLE (r = 0.97). Richer prior-knowledge models gave only small RMSE gains: basic Elo 0.4142, hierarchical 0.4115, networked 0.4118 — [Pelánek et al., UMUAI](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf)
- **Cold start** — [Pelánek, Elo in education](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf):
  - New items are set to difficulty 0.
  - "just 10 answers per student are sufficient to produce reasonable skill estimates" (r = 0.8 in simulation).
  - "the system needs at least 100 students to get good estimates of item difficulty".
  - The proportion-correct method "gives poor estimates" under adaptive selection.
  - A single global skill can be too coarse: skills estimated on different continents correlated only about 0.6.
- **Hierarchical / multivariate Elo** — [Pelánek et al., UMUAI](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf), [Pelánek, Elo in education](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf):
  - `P = σ((θ_l + θ_lc) − d_i)`, with global skill plus concept-level skill.
  - Multivariate update: `θ_sj += c_ij·K·(correct − P)` across correlated components.
- **PFAE (current knowledge):** `θ_li += γ(1 − P)` if correct, `θ_li += δ·P` if wrong. Fitted on geography facts, γ = 2.23, δ = −0.89 — [Pelánek et al., UMUAI](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf)
- **Choosing an item near a target success rate** (Papoušek, Pelánek & Stanislav, EDM 2014) — [EDM14 adaptive facts](https://www.fi.muni.cz/~xpelanek/publications/EDM14-adaptive-facts.pdf):
  - P_target = 0.75.
  - `S_prob = P_est/P_target` if P_est ≤ P_target, else `(1 − P_est)/(1 − P_target)`.
  - `S_time = −1/t`, with t = seconds since last asked.
  - `S_count = 1/√(1 + n)`.
  - `Total = 10·S_prob + 10·S_count + 120·S_time`. Pick the max.
- A follow-up difficulty experiment kept a 35% target error rate, i.e., 65% success. Letting learners pick the difficulty directly was "not beneficial" for engagement — [Pelánek, difficulty adjustment](https://www.fi.muni.cz/~xpelanek/publications/difficulty-adjustment.pdf). The UMUAI paper concludes "values around 65% may be a suitable target rate" — [Pelánek et al., UMUAI](https://www.fi.muni.cz/~xpelanek/publications/umuai-adaptive-practice.pdf)
- Math Academy tunes quiz difficulty so students average about 80% — [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works)
- **Glicko-1:**
  - `q = ln(10)/400`
  - `g(RD) = 1/√(1 + 3q²RD²/π²)`
  - `E = 1/(1 + 10^(−g(RD_j)(r − r_j)/400))`
  - `d² = [q² Σ g(RD_j)² E(1 − E)]⁻¹`
  - `r' = r + q/(1/RD² + 1/d²) · Σ g(RD_j)(s_j − E)`
  - `RD' = √(1/(1/RD² + 1/d²))`
  - Inflation over time: `RD = min(√(RD_old² + c²t), 350)`
  - Start at r = 1500, RD = 350. In Glickman's worked example, c ≈ 63.2.
  - Source: [Glickman, The Glicko System](http://www.glicko.net/glicko/glicko.pdf)
- Glicko-2 adds volatility σ (0.06 initially), with τ suggested between 0.3 and 1.2 — [Wikipedia: Glicko](https://en.wikipedia.org/wiki/Glicko_rating_system)

### Inferences (proposals)
- **Model:** `logit P(correct) = θ_user + θ_user,skill − (b_skill + δ_problem)`.
  - θ_user is global ability. θ_user,skill is a per-skill offset (hierarchical Elo).
  - b_skill is the skill's baseline difficulty. δ_problem is a per-problem offset from an author-assigned tier, e.g., tier 1–5 → δ = −1, −0.5, 0, +0.75, +1.5 logits.
  - Updates use U(n) per parameter. Problem offsets get a much smaller K, since one user gives few answers per problem.
  - Glicko-style RD gives per-parameter uncertainty in a principled way, and RD inflation over time is a natural "rustiness" signal. But it duplicates what FSRS models. Elo with U(n) is simpler and enough.
- **Selecting difficulty:** the target logit for p = 0.75 is +1.10 (p = 0.65 → +0.62, p = 0.80 → +1.39, p = 0.85 → +1.73). Choose the unseen problem whose predicted P is closest to the target, using Pelánek's S_prob, S_time, and S_count scoring to avoid repeats.
  - For **FSRS review events**, use a fixed "core" target (e.g., p ≈ 0.85 at the skill's baseline) so that pass/fail measures retention, not difficulty.
  - For **learning or stretch practice**, use 0.65–0.75.
- **Interaction with FSRS:**
  - FSRS decides *when* a skill is due. Elo decides *which problem*.
  - Do not let the Elo per-skill offset and FSRS both "punish" the same failure twice in a way that compounds. A failure on a stretch problem (predicted P < 0.5) updates Elo only. A failure on a core problem updates both.
  - Optionally lower problem difficulty when the skill's R is low (an overdue skill gets an easier core problem). Keep this a small adjustment, or pass/fail stops being comparable across reviews.
- **Cold start for problem difficulty:** with one user, δ_problem barely moves. Rely on author tiers. If a problem pool is shared with others later (the user wants it "built as if it had multiple users"), pooled data can calibrate δ_problem after about 100 answers per item, per Pelánek.

### Gaps
- No source addresses item calibration in a single-learner system. My tier-to-logit numbers are illustrative, not sourced.

---

## 8. Mastery detection (BKT, PFA, N-correct, EMA) and the threshold before a new skill enters normal spaced review

### Takeaway
Pelánek & Řihák found that the choice of threshold and data matters more than the choice of model, and they recommend a simple exponential moving average. BKT's classic threshold is P(L) ≥ 0.95; a 2025 EDM study found ≥ 0.98 associated with better next-lesson outcomes. Math Academy advances on 2 correct in a row within up to about 5 practice problems. Same-session overlearning does not improve 1- or 4-week retention, so mastery criteria should be short and rely on spaced follow-ups.

### Cited Findings
- **BKT equations** (Corbett & Anderson framework, as given in the pyBKT paper):
  - After a correct response: `P(L_t|1) = P(L_t)(1 − S) / [P(L_t)(1 − S) + (1 − P(L_t))G]`
  - After an incorrect response: `P(L_t|0) = P(L_t)S / [P(L_t)S + (1 − P(L_t))(1 − G)]`
  - Learning transition: `P(L_{t+1}) = P(L_t|obs) + (1 − P(L_t|obs))·T`
  - Standard BKT assumes forgetting = 0. pyBKT offers a `forgets` variant, and BKT+Forget reached DKT-level AUC (0.83) on ASSISTments.
  - pyBKT is MIT-licensed (`pip install pyBKT`; `from pyBKT.models import Model`; `.fit`, `.predict`, `.evaluate`, `.crossvalidate`).
  - Source: [pyBKT paper, arXiv 2105.00385](https://arxiv.org/pdf/2105.00385)
- **BKT thresholds** (EDM 2025 short paper by Baker's lab):
  - Prior thresholds: 0.95 (Corbett & Anderson 1995), 0.8, 0.9, and skill-specific about 0.9–0.97 (Pelánek & Řihák 2017).
  - Students with final P(L) ≥ 0.98 did significantly better in the next lesson than those below 0.3, and had the largest learning gains.
  - The authors suggest P(L_n) > 0.98 may be the better threshold.
  - The study is correlational and measured next-lesson performance, not retention.
  - Parameter bounds used: G, S ∈ [0.01, 0.3]; P(L0) ∈ [0.001, 0.5]; T ∈ [0.001, 0.1].
  - Source: [EDM 2025 BKT threshold paper](https://learninganalytics.upenn.edu/ryanbaker/edm25_short_bkt%20threshold_CR_final.pdf)
- **Mastery criteria analysis:** "the choice of data sources used for mastery decision and setting of thresholds are more important" than the learner-modeling technique. "a simple exponential moving average method is a suitable technique for mastery criterion". They propose an EMA extension for item "time intensity" — [Řihák & Pelánek, Analysis and design of mastery learning criteria](https://www.ics.muni.cz/en/research/publications/1448676); [Experimental Analysis of Mastery Learning Criteria](https://www.ics.muni.cz/en/research/publications/1392193)
- **Math Academy lessons:** a worked example, then "up to 5 practice problems". Two correct in a row advances to the next example; otherwise more problems are given — [Math Academy: How it works](https://mathacademy.com/how-it-works). Each incorrect answer adds required questions. Too many wrong halts the lesson, which is retried later after unrelated work — [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works)
- **Overlearning:** 9 vs 3 problems in one session made no difference at 1 or 4 weeks. Splitting the same 10 problems across two sessions a week apart had an "extremely large" benefit at 4 weeks — [Rohrer & Taylor](https://digitalcommons.usf.edu/psy_facpub/1770/)
- PFA predicts the probability of correctness rather than latent knowledge, so it has no built-in mastery threshold — [LASER KT module 2](https://laserkt.quarto.pub/module-2-logistic-knowledge-tracing-and-performance-factors-analysis)

### Inferences (proposals)
- **EMA mastery score per new skill:** `m ← λ·m + (1 − λ)·x`, with x = 1 for an unaided correct answer and 0 otherwise, starting at m = 0.
  - With λ = 0.6, consecutive corrects give m = 0.40, 0.64, 0.78, 0.87, 0.92, 0.95 (my arithmetic).
  - So "m ≥ 0.85" needs 4 straight correct from zero, and roughly 5–6 if one miss is mixed in.
  - Graduate the skill to FSRS Review state when m ≥ ~0.85 AND the last 2 were correct (MA's two-in-a-row) AND at least one correct was on a core-difficulty problem.
- **Partial mastery (design 6, e.g., 5 right / 2 wrong):** do 1–2 fresh reinforcement problems now (not a long run, given Rohrer & Taylor), then schedule a delayed redo next day. This is FSRS relearning with a ≥1-day gap, or a learning step under 1 day per the Anki manual. Under default FSRS-6 parameters, same-day Good adds no stability (§1), so the delayed redo is what moves the schedule.
- On graduation, initialize the FSRS card from the learning-phase history (replay the real attempts as ReviewLogs). Don't invent a stability.

### Gaps
- I could not retrieve the full text of Pelánek & Řihák for their exact EMA α and threshold values. The search budget was exhausted and one PDF link failed. The λ and threshold values above are mine.

---

## 9. Queue construction: interleaving, ordering, new vs review balance, overdue handling, triage when count < due, daily-limit behavior, sibling spacing

### Takeaway
Interleaving math problem types has a large effect: d = 0.83 in a preregistered cluster RCT. Anki's guidance is to pause new material when behind (matching design 5). But for which reviews to drop, FSRS-era Anki simulations favored **descending** retrievability: do the *most*-likely-remembered first and let the low-R ones slip. That is the opposite of design (5) as phrased. This conflict needs a deliberate decision.

### Cited Findings
- **Interleaving RCT:**
  - 54 seventh-grade classes, 787 students analyzed, test about a month after the review.
  - Interleaved 60.7% vs blocked 37.6% correct, d = 0.83 (95% CI 0.68–0.97). Positive for all 15 teachers.
  - Mechanisms: students must "choose a strategy and not merely execute" it; interleaving "guarantees spaced practice"; and it forces retrieval.
  - Source: [Rohrer et al., interleaved math RCT](https://Www.Gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **Anki sort-order guidance** — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html):
  - "Due date, then random" is the default and is recommended when up to date.
  - For a large backlog under SM-2, "Relative overdueness" ("cards that you're more likely to have forgotten first"). Its FSRS equivalent is listed as "Ascending retrievability".
- **Conflicting newer guidance:** Anki 24.11 added "descending retrievability" sorting and said simulations favor it when you have a backlog — [Anki 24.11 notes](https://newreleases.io/project/github/ankitects/anki/release/24.11). A 2026 forum thread calls descending R "the order which is usually recommended", with the rationale "you will be sacrificing some cards that already have lower R in order to rescue cards that still have higher R" (Danika_Dakika) — [Anki forum: descending R](https://forums.ankiweb.net/t/a-situation-in-which-descending-retrievability-may-not-be-the-most-efficient-review-sort-order/68947). Anki 26.05 made descending R "a pure R sort" — [Anki 26.05](https://github.com/ankitects/anki/releases/tag/26.05). Before that it was relative to each deck's desired retention — [Anki forum: pure R sort](https://forums.ankiweb.net/t/follow-up-make-descending-retrievability-a-pure-r-sort/67082)
- **Unvalidated proposal on the Anki forum** (user "nap", 7 Jun 2026): sort by `R_today − R_tomorrow` (the daily loss from postponing), so a card is not sacrificed needlessly. No developer response or simulation was posted — [Anki forum: R_today − R_tomorrow](https://forums.ankiweb.net/t/sorting-order-by-today-minus-tomorrow-retrievability-difference/70007)
- **Daily R loss by stability** (computed with fsrs 6.3.2, using the forgetting curve from [py-fsrs scheduler.py](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/fsrs/scheduler.py)): ΔR per day of postponement at R ≈ 0.90 is about 0.030 for S = 2 d, about 0.0067 for S = 10 d, and about 0.0014 for S = 50 d. Postponing a stable skill costs roughly 20× less retention per day than postponing a fragile one.
- **New vs review** — [Anki manual: deck options](https://docs.ankiweb.net/deck-options.html):
  - "Continuing to introduce new cards when you're already behind can make the backlog worse."
  - "If you are consistently learning 20 new cards a day, you can expect your daily reviews to be roughly about 200 cards/day."
  - Options: New Cards/Day, Maximum Reviews/Day, "New cards ignore review limit", and new/review mix order.
- **Math Academy** — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/), [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works), [Math Academy: How it works](https://mathacademy.com/how-it-works):
  - Due reviews are compressed into tasks that cover several due topics.
  - Reviews are interleaved, and new material is taught alongside dissimilar material ("non-interference").
  - After a long break, a new diagnostic resets the frontier instead of facing a huge backlog.
- **Sibling and recency spacing:**
  - Anki's load balancer down-weights days within ±5 of a sibling's due date (×0.2 at ±1 day, ×0.000001 on the same day) — [Anki load_balancer.rs](https://raw.githubusercontent.com/ankitects/anki/main/rslib/src/scheduler/states/load_balancer.rs)
  - Pelánek's item selection penalizes recency with `W_time·(−1/t)`, W_time = 120 with t in seconds — [EDM14 adaptive facts](https://www.fi.muni.cz/~xpelanek/publications/EDM14-adaptive-facts.pdf)
  - Load balancing in the add-on sometimes clustered related non-sibling cards on low-load days (one user report) — [Anki forum: load balance](https://forums.ankiweb.net/t/native-implementation-of-load-balance/46007/66)

### Inferences (proposed algorithm)
- **Daily build, given count N:**
  1. Candidates are all enabled skills that are due (`due ≤ end of today`), plus relearning redos and sub-skill checks. Checks and redos come first, since they are short and the design requires them.
  2. If the due set D fits within N: fill the rest with new skills whose prerequisites are mastered (outer fringe), capped by a new-per-day limit. Optionally add "pre-due" reviews with the highest ΔR per day.
  3. If D exceeds N: drop new skills first (design 5). Then choose which reviews to defer:
     - (a) **Design (5) as written:** defer the highest-R skills. Equivalent to ascending-R (most-forgotten first).
     - (b) **Anki-sim recommended:** defer the lowest-R skills (descending R).
     - (c) **Proposal:** defer the skills with the smallest ΔR per day from postponement. These are mostly high-S skills, which coincides largely with (a) when R is similar.
     - My suggestion: (c), with a cap so no skill is deferred more than k days or below R ≈ 0.7.
     - Also run a greedy compression pass first: pick advanced-skill problems whose encompassed due sub-skills give the most covered due weight. Each counts as one item but implicitly knocks out others (§3).
  4. Interleave: order the selected items so that consecutive items come from different sections or units, and no two items share a heavily-weighted sub-skill within the same short window. Use a greedy "pick next item maximizing distance from the last k items" over the skill graph, with random tie-breaking.
  5. Problem choice per item: Elo target (§7), excluding problems seen in the last X days for that skill.
- **Overdue without a visible backlog:** show only today's count N, never the total due. Track backlog internally. When backlog exceeds about 2×N for more than a week, prompt a short re-diagnostic or temporarily raise N, mirroring MA's "new diagnostic after a break". FSRS handles overdue skills naturally: low R means a successful review grants a big stability gain, and a failed one a lapse.
- **Load balancing future due dates** (optional): within the fuzz window, pick the day with the fewest due skills, using Anki's weight formula as a template, and add a sibling/encompassing-overlap modifier.

### Gaps
- I found no published simulation numbers comparing ascending vs descending R vs ΔR sorting. The claim that "simulations favor descending R" is only stated in release notes and forum posts. No source validates any of these orders for skill-level (problem) reviews.

---

## 10. Diagnostic placement tests to cold-start a user who already knows College Algebra

### Takeaway
Both ALEKS and Math Academy use adaptive diagnostics that exploit the prerequisite structure. Success on an advanced item implies success on its prerequisites, so ALEKS caps an assessment at about 35 items and MA uses 20–60 questions per course. ALEKS chooses each question to have about a 50% predicted success under the current posterior over knowledge states. MA keeps diagnostics conservative. Placed-out skills can be created in py-fsrs directly as Review-state cards with chosen stability.

### Cited Findings
- **Math Academy** — [Hecker part 7](https://frankhecker.com/2025/02/14/math-academy-part-7/), [Math Academy: How it works](https://mathacademy.com/how-it-works), [Math Academy: How our AI works](https://mathacademy.com/how-our-ai-works):
  - "Successful answers for a more advanced question indicate that the student should also be successful" on prerequisites.
  - The exam uses "relatively few questions (20-60 depending on the course level)" and is conservative.
  - Supplemental diagnostics are run when the graph changes.
  - It takes about 30–45 minutes and can be split across sittings.
  - The selection algorithm can "cut down the number of diagnostic questions by an order of magnitude" vs assessing about 500–1,000 topics.
- **ALEKS** — [Emergent Mind: ALEKS](https://www.emergentmind.com/topics/aleks):
  - Bayesian assessment over a probabilistic knowledge structure.
  - Questioning rule: ask the item whose predicted P(correct) is closest to 0.5 (a half-split of the posterior).
  - At most 35 items in an elementary domain.
  - Validation: 125,786 assessments, median tetrachoric correlation 0.68.
  - After assessment, it offers outer-fringe items.
- **Returning after a break:** MA recommends a new diagnostic to move the "knowledge frontier" back — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Initializing FSRS state:**
  - py-fsrs `Card(...)` accepts `state`, `stability`, `difficulty`, `due`, and `last_review` directly (verified on fsrs 6.3.2).
  - `reschedule_card(card, review_logs)` replays history.
  - fsrs-rs has `memory_state_from_sm2(...)` and "initialize state from history".
  - Sources: [py-fsrs README](https://github.com/open-spaced-repetition/py-fsrs), [fsrs-rs](https://github.com/open-spaced-repetition/fsrs-rs), [fsrs-rs releases](https://github.com/open-spaced-repetition/fsrs-rs/releases)

### Inferences (proposed procedure)
- **Graph-guided adaptive diagnostic (simplified ALEKS/MA):**
  1. Keep P(known) for each skill, starting at a course prior, e.g., 0.7 for College Algebra skills for this user.
  2. Repeatedly ask a core-difficulty problem from the skill whose answer would resolve the most uncertainty. A practical proxy: the not-yet-tested skill with the most descendants and ancestors still uncertain, and P(known) near 0.5.
  3. On a pass, set the skill and its fully-encompassed ancestors (weight ≥ ~0.8) to "known". Partially-encompassed ones get a smaller boost.
  4. On a fail, set the skill to "unknown" and propagate to its descendants. Then test its direct prerequisites.
  5. Stop after about 20–40 questions per course, or when all P are outside [0.2, 0.8].
- **FSRS init for placed-out skills:**
  - Create `Card(state=State.Review, stability=S_init, difficulty=D_init, last_review=now, due=now + I(S_init))`.
  - Use a conservative S_init: e.g., the FSRS-6 default S0 for Good (2.3 d) for skills inferred only from descendants, and something like S after two successful reviews (≈ 10 d, per §1) for skills directly passed.
  - The first real review then calibrates quickly.
  - This choice is the developer's; no source prescribes it.
- **Conservative bias:** follow MA. It is cheaper to re-show a known skill a few times (FSRS will rapidly lengthen intervals on Good/Easy) than to skip a shaky prerequisite.

### Gaps
- No primary ALEKS technical documentation was retrieved. The question-selection detail comes from a secondary summary.
- MA's diagnostic item-selection and stopping rules are not public.
- **Research-process note:** the shared web-search budget was exhausted near the end of this task. Several planned primary-source lookups were not done: Corbett & Anderson 1995, BUGGY/bug libraries, the full text of Pelánek & Řihák, ALEKS primary docs, and the Math Academy Way spaced-repetition chapter. A follow-up search pass could fill these.
