# Borrow Anki's Guard Rails, Keep Misses Honest

The Toishi computes FSRS-6 correctly and beats Anki on exact study days and exact undo, but it lacks most of what Anki builds *around* the formulas, and that is where its real risks sit. **Parameter fitting is a manual, optional offer at 512 reviews that saves whatever fsrs-rs returns**: nothing clamps the values (one float32 0.8 at a bound makes py-fsrs raise `ValueError` on every scheduler build, reproduced locally), nothing compares the new set with the current one, nothing recomputes stored stability, and there is no health check or cadence, although the earlier research expected Anki's adoption rule and a routine check. The engine also fits on whole days but updates stability on fractional days, so the clock times of a lesson and its review alone can turn one due-day review into a 9-day or a 13-day interval, and a single `RULES_VERSION` bump permanently removes every existing skill from the training data. The second risk is what the ratings mean: five grading paths turn a miss into a pass (Hard) or into no event, unanswered practice-test problems are written as Agains, and the ENG-11 calibration check leaves out exactly the settled and stretch events that carry this bias, while FSRS counts Hard as recall and Anki names Hard-for-forgotten as the one habit FSRS cannot absorb. Third, live due dates make every goal change a silent mass reschedule that trips false "escalations", reviews have no load balancer, and flashcards miscount lapses, ignore their leech flag, overrun daily limits and borrow the skills' fitted parameters. Every fix maps onto an Anki 26.09.3 code path or a published FSRS test vector, and six belong before the first fit. Golden vectors and a parameter-recovery test can run today, but verdicts about this one learner need about 300 long-term items, and pinning true retention to ±3 points needs about 400 interday reviews.

## Anki runs FSRS-6 on whole days and wraps it in guard rails

### Twenty-one parameters drive two state variables through three update paths

FSRS-6 keeps two numbers per card. **Stability S** is the number of days until predicted recall falls to 0.9. **Difficulty D** sits on a 1–10 scale. Recall decays along a power curve whose shape parameter w20 is trainable. Every rating moves D, then updates S on one of three paths: a successful long-term review, a lapse, or a same-day review ([awesome-fsrs wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm); [fsrs-rs v6.6.2](https://github.com/open-spaced-repetition/fsrs-rs/tree/v6.6.2)). These are the formulas Anki 26.09.3 runs through fsrs-rs 6.6.2. S is clamped to [0.001, 36500], D to [1, 10], and t is whole days since the last review.

```text
R(t,S)  = (1 + F·t/S)^(−w20),   F = 0.9^(−1/w20) − 1              R = 0.9 when t = S
I(r,S)  = (S/F)·(r^(−1/w20) − 1)                                  interval for desired retention r
first:    S0 = w[G−1];   D0(G) = w4 − e^(w5·(G−1)) + 1
D:        D' = D − w6·(G−3)·(10−D)/9;   D'' = w7·D0(4) + (1−w7)·D'      runs on every review
pass:     S' = S·(1 + e^w8·(11−D)·S^(−w9)·(e^(w10·(1−R)) − 1)·h·e)       h = w15 if Hard, e = w16 if Easy
lapse:    S' = min(w11·D^(−w12)·((S+1)^w13 − 1)·e^(w14·(1−R)),  S/e^(w17·w18))
same day: S' = S·e^(w17·(G−3+w18))·S^(−w19)                       multiplier floored at 1 when G ≥ 2
```

Three properties explain most of FSRS's behavior. The growth term e^(w10·(1−R)) − 1 approaches zero as R approaches 1, so a review at high R, or partial credit that arrives early, is automatically cheap. Ratings act only through pass versus fail, the drift in D, and the Hard and Easy multipliers (w15 = 0.6014 and w16 = 1.8729 by default), so **Hard is a pass whose stability gain is about 0.6 times Good's**, and the optimizer's label is simply rating > 1 ([wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)). Same-day reviews still update S and D, through w17–w19.

The clipper bounds are w0–3 [0.001, 100], w4 [1, 10], w5–6 [0.001, 4], w7 [0.001, 0.75], w8 [0, 4.5], w9 [0, 0.8], w10 [0.001, 3.5], w11 [0.001, 5], w12 [0.001, 0.25], w13 [0.001, 0.9], w14 [0, 4], w15 [0, 1], w16 [1, 6], w17–18 [0, 2], w19 [0.01, 0.8] and w20 [0.1, 0.8] ([fsrs-rs v6.6.2](https://github.com/open-spaced-repetition/fsrs-rs/tree/v6.6.2), `parameter_clipper.rs`). Any implementation should reproduce the values below with the default parameters, to a tolerance of 1e-4 (fsrs-rs computes in float32).

| Case | Input | Expected (S, D) |
|---|---|---|
| First review | Again / Hard / Good / Easy | (0.212, 6.4133) / (1.2931, 5.11217) / (2.3065, 2.11810) / (8.2956, 1.0) |
| Long-term review | S = 10, D = 5, t = 10 | Again (1.39199, 8.34176); Hard (23.2469, 6.66600); Good (32.0267, 4.99023); Easy (51.2539, 3.31446) |
| Same-day review | S = 10, D = 5, t = 0 | Again (3.05125, 8.34176); Hard (10.0, 6.66600); Good (10.0, 4.99023); Easy (15.5343, 3.31446) |
| Replay | (G, t) = (1,0), (3,0), (3,1), (3,3), (3,8), (3,21) | S 53.62691, D 6.357487 |
| Curve | R(20, 10); F; I(r, S = 10) at r = 0.8 / 0.95 / 0.7 | 0.845885; 0.980346; 33.1596 / 4.02559 / 92.879 |
| py-fsrs intervals | `test_basic.py` rating sequence, fuzz off, each review at its due time | [0, 2, 11, 46, 163, 498, 0, 0, 2, 4, 7, 12, 21] |

Sources: [fsrs-rs v6.6.2](https://github.com/open-spaced-repetition/fsrs-rs/tree/v6.6.2) (`model.rs`, and an upstream test in `inference.rs` for the replay row); [py-fsrs test_basic.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_basic.py). I recomputed the Good value of the long-term row (32.0267) with py-fsrs 6.3.2 in the project's environment.

### Anki's scheduler adds whole-day clocks, interval floors, fuzz and load balancing

**Elapsed time.** Anki counts the elapsed time FSRS sees in **whole days from a local rollover hour**, so 0 means "same day" ([timing.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/timing.rs)).

**Intervals.** Intervals come from I(DR, S) and then pass through ordering floors: Hard ≥ 1 day, Good ≥ Hard + 1 and Easy ≥ Good + 1. A minimum-fuzz rule also keeps fuzz from pushing an interval below the previous one ([Anki 26.09.3](https://github.com/ankitects/anki/tree/26.09.3), `scheduler/states/review.rs`, `fuzz.rs`).

**Fuzz.** There is no fuzz under 2.5 days. Above that, the spread is ±(1 + 15% of the part between 2.5 and 7 days + 10% of the part from 7 to 20 + 5% beyond 20). The draw comes from a random generator seeded with the card id plus its review count ([Anki 26.09.3](https://github.com/ankitects/anki/tree/26.09.3), `scheduler/states/fuzz.rs`).

**Load balancer.** It has been on by default since 24.11. For intervals up to 90 days it picks a day inside the fuzz range, weighted by (1/n_due)^2.15·(1/day)^3. Modifiers then spread siblings and apply Easy Days, which lighten chosen weekdays to Reduced (0.5) or Minimum ([Anki 24.11](https://github.com/ankitects/anki/releases/tag/24.11); [Anki 26.05](https://github.com/ankitects/anki/releases/tag/26.05)).

**Learning steps.** These still exist under FSRS. With empty steps, FSRS controls short-term scheduling, and an interval under half a day becomes an intraday step. So a new card answered Again (S = 0.212) comes back in about five hours ([Deck options](https://docs.ankiweb.net/deck-options.html)).

**Lapses and leeches.** A lapse counts only when a card in Review is answered Again. At 8 lapses Anki tags and suspends the card, and it repeats the warning every half threshold ([Leeches](https://docs.ankiweb.net/leeches.html)).

**One transaction per answer.** Each answer is a single transaction. It caps the answer time, refuses to commit if the card changed since its choices were shown, writes the review log and updates the load-balancer cache ([Anki 26.09.3](https://github.com/ankitects/anki/tree/26.09.3), `scheduler/answering/mod.rs`).

### Training is filtered, thresholded, and adopted only when it wins

**Building the training data.** Anki builds training data per card from the review log, scanning newest to oldest. It skips cram rows, lets a Reset row cut off older history, starts the history at the first graded row of the last learning block, and removes manual rows (set due date, rescheduled). Every later review with Δt > 0 becomes one training item that carries its whole prefix. Same-day reviews shape S through w17–w19 but are **never prediction targets** ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)).

**Fitting.** fsrs-rs returns the defaults below 8 items and fits only the four initial stabilities below 64. Above that it trains 8 epochs in Anki on a log loss that weights recent reviews more, with an L2 pull toward the starting parameters and clipping at every step ([training.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/training.rs)).

**Adoption.** Next comes the step the engine skipped. Anki scores the current and the new parameters on the same items and **keeps the current ones unless the new set's log loss is lower** ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), L148–180).

**Health check.** This optional check needs more than 300 items. It trains and tests five times in time order: each fold trains on everything before a segment and tests on that segment. It passes if adjusted log loss ≤ 1.11 or adjusted RMSE(bins) ≤ 1.53, where both baselines depend on retention and item count ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs), L66–77, L182–198).

**Cadence.** Anki never optimizes on its own. It nudges with "It's been a while" after 30 days, and its FAQ suggests optimizing monthly or whenever the review count doubles ([FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)).

**After a change.** When parameters or desired retention change, saving **recomputes the memory state of every reviewed card by replaying its log**. Due dates stay put unless "Reschedule cards on change" is ticked. That option is off by default because it "can make many cards due at once" ([Deck options](https://docs.ankiweb.net/deck-options.html)).

The data-volume evidence explains these guard rails. Optimized FSRS-6 beats the default parameters for **84.3% of users**, and the defaults win more often when data is scarce ([Expertium benchmark](https://expertium.github.io/Benchmark.html)). In this audit's synthetic fits through fsrs-rs-python 0.9.3, 40 items changed no parameter, 200 changed all 21, and 5,700 cut held-out log loss from 0.3631 to 0.3590, against 0.3594 for the true parameters ([fsrs-rs-python](https://github.com/open-spaced-repetition/fsrs-rs-python)). Small fits move every parameter while proving little. That is exactly when an adoption test earns its keep.

### py-fsrs is not Anki, and the difference is mostly the clock

py-fsrs 6.3.2, which the engine schedules with, differs from Anki in five ways: it measures elapsed time in 24-hour UTC blocks, rounds half to even, applies random fuzz with a 2-day floor and no Hard < Good < Easy guarantee, does not cap S at 36,500, and raises `ValueError` for any parameter outside its bounds ([py-fsrs scheduler](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)). The clock matters most: in the earlier research round, one seven-review history replayed through py-fsrs gave S = 9.30, against 12.65 when replayed with Anki's rollover-based day numbers ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)).

The bound check bites when combined with fsrs-rs, which works in float32. A parameter clipped to 0.8 comes back as 0.800000011920929, and py-fsrs 6.3.2 rejects it: "parameters[20] = 0.800000011920929 is out of bounds: (0.1, 0.8)" (reproduced in the project's own environment).

FSRS-7 uses fractional intervals and separate short- and long-term stability. It reaches log loss 0.3370 against FSRS-6's 0.3460 in the benchmark, but no release of py-fsrs or Anki ships it ([srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)).

## The engine matches or beats Anki on the daily loop but not at the edges

Read line by line against Anki 26.09.3, the engine's daily loop holds up. ADR-0006 found that py-fsrs's 24-hour rule made weak skills loop at 1-day intervals in simulation. It replaced that rule with "same study day" (`core/engine/lifecycle.py:42-47`), which matches Anki's Δt = 0. The study-day code also handles daylight-saving gaps exactly (`core/storage/clock.py:271-296`), while Anki's cached rollover can be a day off for reviews within about an hour of a daylight-saving change ([timing.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/timing.rs)). Undo restores exact row snapshots and refuses if rows changed since (`core/storage/user_store.py:530-580`), which is stricter than Anki's 30-step stack.

The backlog order defaults to descending retrievability. Anki introduced that option because simulations favored it under a backlog, and in 26.05 made it a pure R sort ([24.11](https://github.com/ankitects/anki/releases/tag/24.11); [26.05](https://github.com/ankitects/anki/releases/tag/26.05)). Repairing a skill leech beats Anki's suspend for problem skills. The lapse rule also suits fresh problems: relearn the next study day, plus an unrated same-day problem.

| Area | Anki 26.09.3 | Engine | Verdict |
|---|---|---|---|
| Day boundary, daylight saving | Rollover hour, fixed offset; can be off by a day near a change | Exact study days in an IANA time zone | Engine better |
| Same-day rule | Δt = 0 by Anki day | Same study day | Match (py-fsrs's 24 h rule fixed) |
| Δt in the stability update | Whole days, the same as training | Fractional days; the fitter uses whole days | **Gap** |
| Undo | 30-step stack | Exact snapshot plus void; older disputes "can't be taken back" | Better, but no recompute |
| Lapse | Again → round(I(S′)) ≥ 1 d, or intraday | Next study day, plus an unrated reinforcement problem | Justified |
| Leech | Tag and suspend at 8 | Repair at 6: worked example, prerequisite checks, relearn | Justified |
| Backlog sort | Descending R available | Descending R default inside triage classes | Match |
| Siblings | Buried at gathering, unburied at rollover | One unit per skill per day; one new cloze blank a day | Match in spirit |
| Hard < Good < Easy floors | Enforced; fuzz never shortens the previous interval | None | Fine for skills (no previews); gap for flashcards |
| Load balancing, Easy Days | Weighted day choice ≤ 90 d; per-weekday weights | None; Easy Days cut the daily count N, building backlog | **Gap** |
| Parameter or retention change | Recompute memory; dues move only if opted in | No recompute; dues always move (live) | **Gap / risk** |
| Adopting fitted parameters | Kept only if log loss improves | Always adopted, unclamped | **Bug** |
| Preview / cram | Preview decks change nothing; cram rows dropped from training | Every study mode rates | Gap |
| Data repair | Check Database rebuilds from the review log | None; NaN S accepted | Gap |
| Flashcards | Intraday relearn; lapses only from Review; leech suspends; limits minus today | Tomorrow only; any Again is a lapse; leech flag unread; limits not reduced | **Bugs** |

Sources for the Anki column: [Anki 26.09.3](https://github.com/ankitects/anki/tree/26.09.3), [Deck options](https://docs.ankiweb.net/deck-options.html), [Leeches](https://docs.ankiweb.net/leeches.html), [Filtered decks](https://docs.ankiweb.net/filtered-decks.html). Engine paths are in `/home/claude/toishi`.

The flashcard path reads like code written on the side, and its bugs show it. In `core/queue/flashcards.py:45`, `lapse = rating == 1 and memory is not None`, which I confirmed in the code. So an Again during relearning, or a second Again the same day, both add a lapse, while Anki counts only Review → Again. The `leech` flag (line 64) is set but never read, so a leech is served forever; Anki suspends it and tags it for rewriting. The daily flashcard allowance is not reduced by cards already done today, and there is no separate limit for new cards (`core/queue/planner.py:210-213`). A failed card comes back only tomorrow, where Anki brings a new card back within hours. And flashcards are scheduled with the skills' fitted "math" parameters (`core/engine/service.py:77-86`), even though the fit excludes flashcard events. Anki's own advice is separate presets for material that differs a lot ([Deck options](https://docs.ankiweb.net/deck-options.html)). This matters more because flashcards will include imported Anki decks.

Reviews have no load balancer, and Easy Days lower the daily count rather than shifting future intervals, so they build a backlog. No study mode skips scheduling. Anki counts reviews in rescheduling filtered decks as real reviews too, and FSRS absorbs early reviews through high R, but a preview mode is still the safe way to cram for an exam. Nothing checks `SkillState` for a NaN stability, a difficulty outside 1–10 or a last review in the future (`core/model.py:553-560`). It is unverified whether a session can build a second daily plan on the same day, and that decides how much the flashcard-limit bug matters in practice.

## The fitting path can brick the scheduler and never asks whether new parameters are better

The original plan treated fitting as an afterthought, and the build carried that through. ENG-12 says that after 512 qualifying reviews the app "offers 'Fit my memory model'". `Engine.fit()` (`core/engine/service.py:367-373`, confirmed) computes parameters and writes them straight to the `fsrs.params.math` setting.

The 512 gate comes from py-fsrs's own optimizer, which returns the defaults below 512 logs ([py-fsrs tests](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_optimizer.py)). The fitter actually used is fsrs-rs, which has its own thresholds of 8 and 64 items, so the gate is a leftover.

The earlier gaps round said fsrs-rs-python would make fitting "a routine weekly check". What shipped is a manual button with none of Anki's guard rails: no clamp, no comparison with the current parameters, no recompute of stored memory, no health check and no cadence.

**The missing clamp can stop all grading.** fsrs-rs clips w9, w19 and w20 to an upper bound of 0.8, but in float32. `fit_parameters` converts each value with `float(w)`, which keeps 0.800000011920929. `stored_parameters` passes that value back unchanged (`core/engine/calibration.py:240-247`), and `FsrsAdapter` hands it to `Scheduler(parameters=...)`. That raises `ValueError`, reproduced locally with py-fsrs 6.3.2. `Engine.adapter()` builds that object for every grade, every due computation and every projection. So **one fit that lands on any of those three bounds stops the app from grading anything** until someone edits the setting by hand.

**Nothing asks whether the new parameters are better.** `fit()` adopts every result. Anki would keep the current set unless log loss improved, and once there are more than 300 items it would also run the health check ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)). In-sample comparison mostly guards against optimizer failures, because a fit nearly always wins on its own training data. With one learner, the real protection against overfitting is the out-of-sample split.

**Nothing recomputes stored memory after a fit.** Stored S and D were computed under the old parameters, while live due dates use the new w20. Every skill then sits on a curve its parameters never produced. There is no replay-from-log function: a `VoidReason` "recompute" exists but nothing uses it. That same missing function is why an older disputed answer "can't be taken back" (`session.py:2370`).

**The training histories lose data in three ways** (`core/engine/calibration.py:179-209`, confirmed). A history starts only at an event with no prior stability, and only events under the current `RULES_VERSION` are kept, so after a rules bump an already-learned skill never produces a fresh-start event again: **every existing skill drops out of training for good** unless it later leeches and relearns, which is far harsher than ENG-12's "only reviews graded under the current rating rules are used" intended. A learning phase that spans two study days becomes two histories. And failed learning phases write no events at all, where Anki keeps every learning row.

**Training and updating use different clocks.** The fit counts Δt in whole study days. Anki does the same, and so did the data the default parameters were trained on. But `FsrsAdapter.review` feeds the stability update an R computed from fractional days (`core/engine/fsrs_adapter.py:102-111`, confirmed). This traces back to the first report, which recommended computing R from fractional days because py-fsrs's R reads 1.0 for a full day after a review. That advice was about display and triage. ENG-1 carried it into the memory update.

The effect is large where schedules are densest. With the default parameters, take a skill whose learning phase ends with S = 2.31 and is reviewed Good on its due study day two days later (computed with py-fsrs 6.3.2):

| Learned at | Reviewed at | Fractional t | New S (≈ interval) |
|---|---|---|---|
| 23:00 | 08:00 | 1.375 | **8.80** (9 days) |
| any (whole-day count) | | 2 | 10.96 (11 days) |
| 08:00 | 23:00 | 2.625 | **12.83** (13 days) |

For a mature skill the gap shrinks to about 3%: at S = 10, reviews at t = 9.4 and t = 10 give 31.07 and 32.03. So the time of day the student studies moves early intervals by ±20% in a way the fitted model cannot represent.

`replay()` has the opposite problem. It still uses py-fsrs's 24-hour rule (`fsrs_adapter.py:125-130`, confirmed: it calls `review` without `same_day`). It builds every learned skill's first card (`lifecycle.py:195`) and drives the load projections. So a learning phase that crosses the 04:00 rollover takes the same-day path in replay and the long-term path in live grading.

## Skill scheduling holds up only if a miss stays a miss

### The evidence supports skills with fresh problems, as an approximation that must be measured

This audit found no published study that schedules varied-problem math skills with an FSRS-type model. Several lines of evidence still show how to do it responsibly.

**What FSRS can and can't see.** FSRS's maintainers model one card's own history: "FSRS and SM-2 cannot access the review history of any other card." Handling effects across items "would need to build an app with this kind of stuff in mind from the very beginning" ([AnkiWeb forum](https://forums.ankiweb.net/t/interval-determination-of-siblings/49267)). A forum volunteer (not a maintainer) calls spaced repetition "the wrong tool" for practice but grants that "a completely separate problem" each time helps ([AnkiWeb forum](https://forums.ankiweb.net/t/questions-about-tuning-fsrs-for-math-logical-reasoning-problem-cards/70949)).

**Models that separate ability, difficulty and forgetting.** The strongest structural evidence is DAS3H. Its logistic model adds student ability, item difficulty, skill terms and time-windowed practice history, and it reached AUC 0.826 on Algebra 2005 against 0.771 for IRT. Fitting history parameters per skill added about 0.03–0.04 AUC ([Choffin et al. 2019](https://arxiv.org/pdf/1905.06873v1)). Its cross-validation was split by student, though, so prediction on brand-new items is untested. On question data, history adds about 0.06–0.08 AUC over item and learner terms alone ([Randazzo 2022](https://hdl.handle.net/10589/186407)). FSRS cannot predict unseen cards at all, where a content-aware model reached AUC 0.786 ([KAR³L](https://arxiv.org/html/2402.12291v3)).

**Bias from adaptive selection.** Proportion correct is a valid measure under random item selection but fails under adaptive selection. Item difficulty needs about 100 learners to calibrate ([Pelánek](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)). SuperMemo's notes say mixed item streams "polluted" its matrices, which supports a fixed core difficulty band ([SM-17](https://supermemo.guru/wiki/Algorithm_SM-17)).

**Math Academy.** It runs no memory model per topic at all. It uses a pass/fail repetition counter with half-life decay, and it switches off implicit credit for topics the learner finds slow ([Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)).

Read together, these sources leave a coherent target. A skill's R can mean **P(first-try success on a typical core-band problem, now)**, and that is calibratable. It holds only if two conditions hold: the outcome label is honest, and "typical" stays fixed. The engine currently bends both.

### Five grading paths turn a miss into a pass or into silence

FSRS learns pass versus fail from rating > 1. Anki's tutorial says FSRS adapts to most habits "except for one habit: pressing 'Hard' instead of 'Again'" ([fsrs4anki tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)). Its FAQ says Again and Good alone are fine ([FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs)). In this engine the student never presses a button; the app's own grading rules write every rating. Here is how those rules handle a miss.

| Path | Defined in | What FSRS records | In ENG-11 bins? |
|---|---|---|---|
| Careless slip within the cap (wrong final answer) | Rating map | Hard: a pass | Yes |
| Step-check passes after a miss | ADR-0008 reading 1 | Hard on the missed problem's skill | No: settled events carry no predicted recall |
| Step-check fails after a miss | ADR-0008 reading 1 | No event for the missed problem's skill | No |
| Above-level miss, its check passes | ADR-0008 reading 3 | Hard | No |
| Stretch problem answered wrong | Rating map; ADR-0006 reading 1 | No event; a core-band follow-up three items later, served after the stretch's worked solution, becomes the rated review | No: stretch events carry no predicted recall |
| Correct after a second attempt, a non-final hint, "unsure" or "guessed" | Rating map | Hard | Yes |
| Unanswered practice-test problem (opposite direction) | ADR-0010 | Again, a lapse, a leech count, with no attempt at all | Not documented |
| Redo of the same missed problem, even when the skill is not due | Spec "Redo"; `triage.py:198-218` | A full rated review based on memory of one item | Not documented |

The first five rows push the training data toward success. The step-check rule even departs from the first report's own recommendation, which said that when a check passes, "the advanced skill takes the hit". The stretch path gives the skill a second chance right after a reminder. A stretch success counts as Good; a stretch failure counts nothing until a core problem served just after the worked solution.

ADR-0006 and ADR-0008 deliberately keep settled and stretch events out of ENG-11's calibration bins, so the bins aren't skewed. But `qualifying_reviews` and `review_histories` still include them (confirmed in `calibration.py`). **The fitter learns the bias, and the calibration screen cannot show it.**

The last two rows run the other way. ADR-0010 reversed ADR-0009's correct "unanswered problems are not graded", because "a real exam scores them zero". A zero belongs in the test score. Memory can't fail a question the student never saw. The redo rule repeats one specific problem, which measures item memory instead of skill, and the spec contradicts itself on timing: "3 to 7 days later" in the study-screen section, "the next study day" in ENG-3.

### The problem selector and the scheduler aim at different success rates

ENG-5's Elo selector picks the core-band problem whose predicted success is closest to **0.80**, while ENG-1 schedules goal-A skills at R = **0.90**. The spec says "Elo never changes the FSRS schedule". It does change the outcomes the schedule is fitted on.

My inference, untested: if the selector is accurate, core-band success at due time runs below the course's desired retention by design. A fit will read that gap as faster forgetting, shorten intervals and add work. Meanwhile Elo, by picking harder problems after successes, holds success near its own target. That flattens the link between elapsed time and outcome, which is exactly the signal FSRS learns from. This is Pelánek's adaptive-selection bias in a new form.

The core band that rises with stability (ENG-4) does the same over a longer timescale. And one failure is counted twice: Elo serves an easier problem next, while FSRS brings the review sooner, which muddies any later evaluation.

The fix keeps FSRS untouched. Log the tier and Elo's P on every event. Then compare FSRS R alone with a DAS3H-style combined prediction, p = σ(logit R + (θ − d_tier) − (θ − d_core)), with Elo alone and with a constant baseline, all on held-out time slices. Never bend ratings by tier, because that makes the optimizer fit a mixture of meanings.

### Live due dates turn every goal change into a mass reschedule

Due dates are recomputed live from S and the course's current retention. So "changing a goal reschedules nothing" is true for storage and false for the queue. At S = 30, the interval is **99.5 days at 0.80 but 30.0 days at 0.90**. At S = 10 it is 33.2 against 10.0 (computed with the default w20).

Move a course from Keep to A, and every skill whose elapsed time falls between those two intervals becomes due at once. `due_skills` measures overdue against the live due date and flags anything more than 7 days late (`core/engine/schedule.py:50-62`, confirmed). So a skill at S = 30 reviewed 45 days ago is instantly 15 days overdue and "escalated".

Anki's equivalent, "Reschedule cards on change", is opt-in. It logs its changes and has applied load balancing since 25.07 ([25.07](https://github.com/ankitects/anki/releases/tag/25.07)).

Partial credit has a hidden version of the same trap. In On mode, several credits a day compound from an already-credited S (`credit.py:115-170`). Shadow mode is the default, so the risk is dormant. ENG-7's other exclusions already mirror Math Academy's rule against crediting slow skills.

## Proving the scheduler works takes golden vectors, held-out metrics and about 400 reviews

Verification comes in layers, and the cheap ones can run today.

**Golden values.** The first layer is the table above, plus Anki's 15-row fuzz unit test (this audit's port reproduces all 15 rows) and the health-check formulas. The engine's existing conformance test checks that whole-day reviews match `Scheduler.review_card` (ADR-0006). That guards the private-method calls but not the clock or the fit.

**Cross-implementation replay.** The engine schedules with py-fsrs but fits with fsrs-rs-python, on training items it builds itself. So the Δt inside those items must equal the Δt the update uses. Replaying each skill's log through both and asserting that S and D agree within 1e-3 relative catches any conversion bug. This audit's reference port matched fsrs-rs-python on 2,000 random histories to a maximum relative error of 7e-6, and matched py-fsrs to 1e-14 when gaps were whole days ([fsrs-rs-python](https://github.com/open-spaced-repetition/fsrs-rs-python); [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)).

**Parameter recovery.** This audit found no published parameter-recovery study for FSRS, so the engine must build its own: simulate learners with known parameters, draw each outcome from R, pass the logs through the app's own converter, fit, and compare held-out log loss and predicted intervals rather than raw parameters, which are only weakly identifiable. That is the only test that proves the converter and the fitter agree on what a review is.

**Simulation properties.** The simulation harness (`tests/engine/sim.py`) should also assert that workload rises steadily, and ever faster, with desired retention; that success on due reviews roughly equals desired retention; that a review cap creates a backlog whose recall falls to about the predicted R; and that no interval exceeds the maximum and no due date lands in the past. fsrs-rs's simulator returns the per-day series needed to cross-check these ([fsrs-rs simulation.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/simulation.rs)).

**Live metrics** need baselines adjusted for data size. Log loss and RMSE(bins) measure calibration; AUC measures discrimination. FSRS-6 averages 0.3460 / 0.0653 / 0.7034 across about 10,000 users, against 0.3945 / 0.1034 / 0.4997 for predicting the average ([srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)). One learner's numbers should never be compared with those averages. "RMSE is strongly correlated with the number of reviews, logloss is strongly correlated with retention" ([Expertium, Anki forum](https://forums.ankiweb.net/t/how-many-reviews-for-accurate-optimization/53320)). Anki's health-check baselines correct for both ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)), and plugging in gives these pass thresholds:

| Long-term items | RMSE baseline at retention 0.90 | Pass if RMSE(bins) ≤ | Pass if log loss ≤ |
|---|---|---|---|
| 300 | 0.099 | 0.151 | 0.325 |
| 1,000 | 0.085 | 0.130 | 0.325 |
| 10,000 | 0.050 | 0.077 | 0.325 |

At retention 0.85 the log-loss threshold is 0.421. That limit sits within 0.5% of the entropy of r, so it means "no worse than predicting the average". RMSE(bins) must use the bin constants in the fsrs-rs code (3.62, 1.89, 1.73), not the stale ones on the wiki ([dataset.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/dataset.rs); [The Metric](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Metric)). For skills, adding course and tier as bin keys is a sensible extension; it is untested.

**True retention and ENG-11.** Anki's true-retention table counts only the first review of each day with an interval of at least a day. Again is a fail and anything else a pass, split into young and mature cards at 21 days ([Stats](https://docs.ankiweb.net/stats.html)). The statistics here are unforgiving. At an observed 0.90, the 95% Wilson interval is [0.744, 0.965] for 30 reviews, [0.826, 0.945] for 100, [0.867, 0.926] for 400 and [0.880, 0.917] for 1,000. So a claim of "on target ±3 points" needs about **400 interday reviews**.

ENG-11's notice fires when a bin of 30 or more reviews is off by more than 0.10. ADR-0006 already flagged it as noisy, and the size of the problem is concrete. For a perfectly calibrated model, a 30-review bin at p = 0.65 trips the alarm **25%** of the time. Across ten such bins, at least one alarm appears **94%** of the time. At p = 0.90 the rates are 2.6% per bin and 23% across ten (exact binomial calculation). Comparing mean predicted R at review time with observed retention is a direct check that stays valid even when reviews are overdue.

**Off-policy limits.** Offline metrics can only judge the intervals the current scheduler actually chose. A 2026 preprint argues that test-set accuracy alone is insufficient for that reason, and notes that no A/B test between state-of-the-art schedulers has been published ([Schill 2026](https://arxiv.org/abs/2610.10548)). MaiMemo's live A/B test makes the same point. An FSRS-6 variant that won every offline metric showed no significant gain online, and realized retention ran about 75% against an 85% target in both arms ([MaiMemo 2025](https://memodocs.maimemo.com/docs/2025_experiment)).

One learner cannot run an A/B test. The substitutes are held-out evaluation in time order, realized-versus-target retention, and a randomized slice of intervals. The engine's hashed fuzz already provides that slice, provided the unfuzzed interval and the chosen offset are logged.

## Conclusion

In Anki, the user's button press is the measurement and the optimizer only listens. In this engine, the app's own grading rules write every rating. So each rule — slip as Hard, check-pass as Hard, stretch-miss as silence, unanswered as Again — puts a thumb on the scale. The fitter will learn every one of them faithfully, and as currently built the calibration screen sees none of them. The most valuable single addition is therefore not a new model. It is a **strict outcome label**, logged beside every rating: correct on the first try, unaided, on the problem actually served. That turns each rating-map choice from an article of faith into a hypothesis the student's own data can reject.

The second lesson concerns defaults. Anki's guard rails are mostly conservative: don't move due dates unless asked, don't adopt parameters unless they win, rebuild memory from the log. The engine chose the opposite default in all three places — live dues, always adopt, never recompute. Each is cheap to reverse now and expensive to unpick once months of reviews sit on top of it. For a single learner the review log is the one asset that cannot be regenerated. That is why the fixes that protect it rank above the ones that tune it.

## Prioritized fix list

Engine paths are relative to `/home/claude/toishi`. "Vectors" means the golden-value table in the first section.

### Critical: before the first fit or any trusted schedule

| # | Fix | What to change | Acceptance test | Checked against |
|---|---|---|---|---|
| C1 | Clamp and validate fitted parameters | In `fit_parameters`/`stored_parameters` (`core/engine/calibration.py`): round each value to 6 dp, clamp into the intersection of py-fsrs's bounds and the fsrs-rs clipper (w9 ≤ 0.8, 0.01 ≤ w19 ≤ 0.8, 0.1 ≤ w20 ≤ 0.8, etc.), and reject non-finite or wrong-length vectors. `Engine.adapter()` falls back to defaults with a visible notice instead of raising | A fit result with w20 = 0.800000011920929 stores 0.8 and `adapter()` builds. A hypothesis test over arbitrary 21-float vectors never makes `adapter()` raise | fsrs-rs `parameter_clipper.rs` bounds; py-fsrs `Scheduler` bound check (ValueError reproduced locally) |
| C2 | Adopt only parameters that win | `Engine.fit()` scores current and candidate on the same items with fsrs-rs-python `evaluate` (recency-weighted log loss) and keeps the current set unless the candidate is lower. Above 300 items, also require lower held-out log loss on a 5-fold time-ordered split (each fold trains on all earlier segments; segment = N/6) and run the health check (adjLL ≤ 1.11 or adjRMSE ≤ 1.53) | A corrupted candidate (ratings flipped) is rejected and `params_id` is unchanged. The app's log loss and RMSE(bins) match `evaluate` to 1e-7. Thresholds reproduce 0.325 (LL, r = 0.9) and 0.151 / 0.130 / 0.077 (RMSE at 300 / 1,000 / 10,000 items) | Anki `params.rs` L66–77, L148–198; [fsrs-rs inference.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/inference.rs) |
| C3 | Recompute memory from the log | Add `Engine.recompute_memory()`. For each skill, in one transaction, replay non-voided `review_log` events through `review_on` from the last fresh start (placed skills start from their seed S). Run it after every adopted fit, after voiding older attempts (disputes) and from a repair command; wire the unused `VoidReason` "recompute" | After a fit, every stored (S, D) equals a fresh replay under the new parameters. With defaults, the replay vector gives S 53.62691, D 6.357487 (1e-4) | Anki `fsrs/memory_state.rs`; vectors |
| C4 | One clock for training and updates | Feed whole study days t into R for the stability update. Keep fractional R for display, sorting and triage, and log both. Give `replay()` a `StudyDays` and route it through `review_on`; delete the `same_day=None` 24-hour fallback (`core/engine/fsrs_adapter.py:102-130`) | Defaults: a skill whose first review is a single Good at 23:00 (S = 2.3065, D = 2.1181), then Good at 08:00 two study days later, gives S′ = 10.964 (t = 2), not 8.802 (t = 1.375). The long-term vector passes at 1e-4. A hypothesis test shows `replay(h)` equals sequential `review_on` for histories that cross 04:00 and daylight-saving changes | Anki `answering/mod.rs` Δt rule; vectors; py-fsrs 6.3.2 |
| C5 | Stop writing Agains without evidence | Set `TEST_UNANSWERED_DEFAULT = "skip"` (`core/queue/config.py:61`). Log unanswered problems as unrated attempts: no ReviewEvent, no lapse, no leech count. Keep the zero only in the test score | A test stopped with three unanswered problems writes three unrated attempts, zero ReviewEvents and unchanged lapse counts; the score shows the three as 0 | Anki trains only on graded rows (`params.rs`) |
| C6 | Keep the training data whole | Mark history starts explicitly with a block-start flag on the first event of a learning block, a leech relearn or a forget, instead of inferring them from missing stability. After a `RULES_VERSION` bump, keep older-rules events as prefix inputs and train only on current-rules targets. Log failed learning-phase ratings as prefix-only events | In a fixture with 50 learned skills, bumping `RULES_VERSION` keeps every prefix and new reviews become targets. A learning phase crossing the 04:00 rollover stays one history | Anki `reviews_for_fsrs` (history starts at the last learning block; a Reset row cuts; `params.rs` L401–535) |

### Important: before relying on the app for a full semester

| # | Fix | What to change | Acceptance test | Checked against |
|---|---|---|---|---|
| I1 | Clean targets and a strict label | Add `strict_ok` (final answer correct on the first try with no hint) to every attempt. Build fit items so stretch-derived, check-settled and post-stretch follow-up events appear only in prefixes, never as targets. Compute ENG-11 over all rated events, with settled and stretch events as their own series | No fit item ends on a settled, stretch or post-stretch event. In `tests/engine/sim.py`, a simulated learner who slips on 10% of answers shows strict-label success below mean predicted R by roughly the slip rate, a gap the current ENG-11 bins cannot show | Anki keeps same-day reviews in the history but never as targets (`params.rs`); the [benchmark](https://github.com/open-spaced-repetition/srs-benchmark) excludes reviews that don't affect scheduling |
| I2 | Goal changes without false escalations | Escalate on `due_at` cached at review time (or on an R deficit), never on the live due date. When a goal raises retention, preview "this makes N skills due", spread newly past-due skills over the following days with the load balancer, and clamp any due date that moved into the past to today | A skill at S = 30 reviewed 45 days ago under Keep (interval 99.5 d) is not escalated after a switch to A (interval 30.0 d). The preview count equals the number of skills whose live due moves to today or earlier | Anki "Reschedule cards on change" (opt-in, warns of mass dues); I(r, S) from the vectors |
| I3 | Load balancer and Easy Days | For intervals ≤ 90 days, pick a day inside the fuzz range with weight (1/n_due)^2.15·(1/day)^3 × the easy-day factor (Normal 1, Reduced 0.5, Minimum ≈ 0). Store the chosen offset keyed by `last_review_at`, as `due_adjust` is | In a seeded 90-day simulation, mean load is unchanged and day-to-day variance is lower than with hash fuzz. No due date falls outside its fuzz range. All weekdays set to Reduced gives the same load as all Normal | Anki `load_balancer.rs`; [Deck options](https://docs.ankiweb.net/deck-options.html) |
| I4 | Redo without item memory | Grade `purpose="redo"` as unrated reinforcement unless the skill is due. When it is due, rate a fresh problem and serve the redo unrated. Settle the spec's "3 to 7 days" against ENG-3's "next study day" in an ADR | A redo of a skill that isn't due leaves S and D unchanged and writes no ReviewEvent | Spec: "Every other review draws a fresh problem"; DAS3H definition of a skill |
| I5 | Flashcards to Anki parity | Count a lapse only on Again for a REVIEW-state card on a new day. Skip `leech` rows in `_flashcards` (`snapshot.py:355-362`) and show "needs rewrite". Subtract today's flashcard attempts from M and add `daily.new_flashcards`. Give flashcards their own adapter (defaults until a flashcard fit). Re-show a failed card at least 5 items later with the same-day update | An Again on a relearning card, or a second Again the same day, leaves `lapses` unchanged. A card at 8 lapses is not served. A second plan the same day offers M − done. After a math fit, the flashcard adapter's `params_id` still matches the defaults | Anki `review.rs` L95–97; [Leeches](https://docs.ankiweb.net/leeches.html); `limits.rs`; separate-presets advice |
| I6 | Data guards and repair | Validate `SkillState`/`FlashcardState`: S finite and in [0.001, 36500], D in [1, 10], `last_review_at` ≤ now. Add a "Check database" that rebuilds FSRS fields through C3 | Hypothesis: invalid states raise. A corrupted fixture is restored to its replay values | Anki option clamps and Check Database (`storage/card/mod.rs`) |
| I7 | Automatic, guarded fitting | Replace the manual 512 offer with an automatic fit monthly or whenever long-term items double, first at 300 items, adopted only through C2, followed by C3. Show a parameter history with one-click revert | A clock test fires at 30 days and at a doubling. A candidate that loses on held-out data leaves parameters unchanged | [FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs) cadence; 300-item health-check gate; fsrs-rs 8/64 thresholds |
| I8 | A calibration screen that doesn't cry wolf | Replace "≥ 30 reviews off by > 0.10" with Wilson intervals per bin and a Bonferroni-adjusted alarm; grey out bins under 30. Add a true-retention table (first interday review per day; young/mature at 21 d) with Wilson intervals, and expected-versus-observed retention. Above 300 items, show held-out log loss and RMSE(bins) against the size-adjusted baseline | For a simulated, perfectly calibrated learner with ten 30-review bins, at most 5% of runs raise an alarm (current rule: 25% per bin at p = 0.65, 94% across ten) | Exact binomial calculation; [Stats](https://docs.ankiweb.net/stats.html); [fsrs-optimizer calibration](https://github.com/open-spaced-repetition/fsrs-optimizer/blob/main/src/fsrs_optimizer/fsrs_optimizer.py) |
| I9 | Partial credit that can't compound | Allow at most one credit per target skill per study day, at the largest weight. Turn credit on only if credited predictions beat plain ones on held-out log loss for those skills' next core-band outcomes (about 200 reviews) | Two encompassing passes on one day credit skill B once. The switch-on check refuses when the credited log loss is worse | [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/); ENG-7 |
| I10 | A verification harness | Add three tests: a cross-implementation replay test, a parameter-recovery test through the app's own converter, and simulation property tests | py-fsrs adapter vs fsrs-rs-python `memory_state` on 2,000 random whole-day histories: max relative S error ≤ 1e-3. Recovery at about 5k items: held-out log loss within 0.001 of the true parameters' (audit run: 0.3590 vs 0.3594). Workload rises with desired retention, due-review success ≈ desired retention, no due date in the past, no interval above the maximum | [py-fsrs tests](https://github.com/open-spaced-repetition/py-fsrs/blob/main/tests/test_basic.py); [fsrs-rs simulation.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/src/simulation.rs) |

### Later

| # | Fix | What to change | Acceptance test | Checked against |
|---|---|---|---|---|
| L1 | Interval ordering for flashcards | Enforce hard ≥ 1, good ≥ hard + 1, easy ≥ good + 1, and the minimum-fuzz floor; round half away from zero, as Rust does | All 15 rows of Anki's fuzz unit test reproduce; Hard ≤ Good ≤ Easy across a hypothesis sweep | Anki `review.rs` L179–218, `fuzz.rs` |
| L2 | Practice without scheduling, and Forget | Add a "practice, don't schedule" toggle for exam cramming (attempt only, no ReviewEvent), and a Forget that writes a marker event cutting the training history | A practice session leaves every FSRS field unchanged; histories start after the marker | [Filtered decks](https://docs.ankiweb.net/filtered-decks.html) preview; Forget logs a Manual row |
| L3 | Stable past study days | Use the stored `Attempt.study_day` for past events when the time zone or rollover hour changes; add a daylight-saving test for `review_on` | Moving the rollover from 4 to 5 AM leaves every past event's study day unchanged | Anki moves only "today" |
| L4 | Logging for off-policy checks | Log the unfuzzed interval, chosen fuzz or balancer offset, tier, Elo P, and R on both clocks with every event | Schema test | [Schill 2026](https://arxiv.org/abs/2610.10548) |
| L5 | Combined prediction | Evaluate σ(logit R + (θ − d_tier) − (θ − d_core)) against FSRS R alone, Elo alone and a constant, on held-out time slices | After 300 items, report log loss, a calibration curve and RMSE(bins) for each | [DAS3H](https://arxiv.org/pdf/1905.06873v1); [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark) |
| L6 | Workload tool with real costs | Feed the app's own durations per (state, rating) into fsrs-rs `simulate` and show workload against desired retention, as Anki's Help Me Decide does | Simulated workload rises steadily, and ever faster, with desired retention | Anki simulator; [Optimal Retention wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Optimal-Retention) |
| L7 | FSRS-7 watch | Keep the adapter; revisit when py-fsrs ships FSRS-7 (it would help most when a session serves several fresh problems of one skill) | n/a | [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark) |

## Decisions the student must make

| Decision | Options | Recommendation |
|---|---|---|
| Can a wrong final answer ever count as a pass? | (a) Keep slips and passed step checks as Hard; (b) record Again with a flag that Level and the leech counter ignore; (c) record no event | **(b).** FSRS reads Hard as recall and fits w15 from it, and Anki names Hard-for-forgotten as the habit FSRS can't absorb. A flagged Again keeps R meaning "P(solve a fresh problem)", which is what an exam scores, while slips still don't drop Level or create leeches. Keep hints and second tries as Hard for now, and test them against the strict label once there are 300 items. |
| Who decides when to refit? | Manual offer at 512 (current) or automatic with guard rails | **Automatic**, monthly or on doubling, starting at 300 items, behind C1–C3, with a revert. For one learner, a manual button leaves parameters either stale or unguarded. |
| Should due dates follow the current goal? | Live (current) or fixed at answer time with an opt-in reschedule (Anki) | **Keep live** so goals stay simple, but add I2's preview, spreading and escalation from the cached due date, so a goal change behaves like Anki's opt-in reschedule with load balancing. |
| What does an unanswered practice-test problem mean? | Again (current default) or skip | **Skip.** The zero belongs in the test score; FSRS should learn only from attempts. |
| Should Elo aim rated reviews at 0.80? | 0.80 everywhere (current), or the course's desired retention (or the band's anchor difficulty) for rated core-band reviews | **Aim rated core-band reviews at the course's desired retention or the band anchor**, and keep 0.80 for learning phases, stretch problems and practice tests. Confirm with L5. Otherwise the selector holds success below the target and the fitter reads that as faster forgetting (my inference, untested). |
| One parameter set or several? | One "math" set for everything (current), or one per domain plus a flashcard set | **One per domain, plus separate sets for flashcards and imported Anki decks**, as Anki advises for very different material. Group skills into a few presets; never fit one per skill. |
