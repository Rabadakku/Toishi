# FSRS inside Anki 26.09.3: test-ready notes (2026-11-01)

Sources: Anki [26.09.3](https://github.com/ankitects/anki/tree/26.09.3) (pins fsrs-rs 6.6.2), [fsrs-rs v6.6.2](https://github.com/open-spaced-repetition/fsrs-rs/tree/v6.6.2) (`M`=src/model.rs), [py-fsrs 6.3.2](https://github.com/open-spaced-repetition/py-fsrs), [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark), [wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm), manual `deck-options.md`, [FSRS FAQ](https://docs.ankiweb.net/faqs/frequently-asked-questions-about-fsrs). "(V)" = verified by running code (fsrs 6.3.2, fsrs-rs-python 0.9.3, my Python reference). Anki paths are under `rslib/src/scheduler/`. Revlog rebuild: anki_import_fsrs_tooling.md sections 6-7.

## 1. FSRS-6 (M L218-310)
t = whole Anki days since last review; G in 1..4; S clamp [0.001,36500]; D clamp [1,10].
- factor=0.9^(-1/w20)-1; R(t,S)=(1+factor*t/S)^(-w20); I(r,S)=S/factor*(r^(-1/w20)-1), unrounded.
- First review: S=w[G-1]; D=clamp(w4-e^(w5(G-1))+1). Unclamped D0(4)=-4.7716 is the mean-reversion target.
- D'=D-w6(G-3)*(10-D)/9 (old D); D''=clamp(w7*D0(4)+(1-w7)*D'). Runs on every review, same-day included.
- t>0, G>=2: S'=S*(1+e^w8*(11-D)*S^-w9*(e^(w10(1-R))-1)*h*e); h=w15 if G=2, e=w16 if G=4.
- t>0, G=1: S'=min(w11*D^-w12*((S+1)^w13-1)*e^(w14(1-R)), S/e^(w17*w18)).
- t==0 (any G, overrides the two above): S'=S*e^(w17(G-3+w18))*S^-w19, with the multiplier floored at 1 only if G>=2.
- Defaults `[0.212,1.2931,2.3065,8.2956,6.4133,0.8334,3.0194,0.001,1.8722,0.1666,0.796,1.4835,0.0614,0.2629,1.6483,0.6014,1.8729,0.5425,0.0912,0.0658,0.1542]`.
- Clip bounds (`parameter_clipper.rs` L57-93): w0-3 [.001,100]; w4 [1,10]; w5,w6 [.001,4]; w7 [.001,.75]; w8 [0,4.5]; w9 [0,.8]; w10 [.001,3.5]; w11 [.001,5]; w12 [.001,.25]; w13 [.001,.9]; w14 [0,4]; w15 [0,1]; w16 [1,6]; w17,w18 [0,2]; w19 [.01,.8]; w20 [.1,.8].

Vectors (defaults; tolerance 1e-4, fsrs-rs is f32):
1. First review (S,D): G1 (0.212, 6.4133); G2 (1.2931, 5.11217); G3 (2.3065, 2.11810); G4 (8.2956, 1.0).
2. S=10, D=5, t=10: Again (1.39199, 8.34176); Hard (23.2469, 6.66600); Good (32.0267, 4.99023); Easy (51.2539, 3.31446).
3. Same state, t=0: Again (3.05125, 8.34176); Hard (10.0, 6.66600); Good (10.0, 4.99023); Easy (15.5343, 3.31446).
4. Replay (G,t) (1,0),(3,0),(3,1),(3,3),(3,8),(3,21): S 53.62691, D 6.357487; with w17-19=0, S 53.33511 (upstream test, `inference.rs` L1033).
5. R(20,10)=0.845885; factor=0.980346; I(S=10): r=.8 33.1596, r=.95 4.02559, r=.7 92.879.

(V) My reference matches fsrs-rs-python on 2000 random histories (max relative S error 7e-6) and py-fsrs to 1e-14 when gaps are multiples of 24 h with empty learning steps.

## 2. How Anki trains
- **Search**: `preset:"<name>" -is:suspended` (`deckconfig/update.rs` L373-380), or the preset's `param_search`. Suspended and leech cards are excluded.
- **Revlog filter** (`fsrs/params.rs` `reviews_for_fsrs` L401-535), per card, scanning newest to oldest:
  - cram rows (type Filtered, factor 0) are skipped;
  - a Reset row (Manual, factor 0) cuts older history;
  - history starts at the first graded Learning row of the last learning block;
  - training drops cards with no Learning row, or whose learning block precedes "ignore revlogs before";
  - ease=0 rows (set-due, rescheduled) are removed;
  - delta_t = calendar-day difference using the rollover (first = 0, same-day = 0).
- **Items**: one per review with index>=1 and delta_t>0 (L505), holding the whole prefix, sorted by revlog id. Same-day reviews shape S through w17-19 but are never prediction targets.
- **fsrs-rs** (`training.rs` L281-380):
  - ratings must be 1..4;
  - an outlier filter (`dataset.rs` L222-290) groups one-long-term-review items by (first rating, gap) and drops the smallest groups (up to 5%, at least 20 items) plus groups with <6 items or a gap >100 d (365 d for Easy);
  - <8 items returns defaults;
  - <64 items, or only one-long-term-review items, fits w0-3 only;
  - otherwise Adam, lr .04 cosine-annealed, batch 512, seed 2023, **8 epochs in Anki** (library default 5), items over 256 reviews dropped;
  - loss = recency-weighted BCE, weight 0.25+0.75*(i/(n-1))^3, with an L2 pull toward the initial parameters, clipped every step.
- **Adoption** (`params.rs` L148-180): current and new parameters are scored in-sample on all items (recency-weighted log loss). If current <= new, **keep current**; RMSE(bins) is not used. Code-only exception: with >=2 same-day relearning steps, a not-better result is still adopted unless the current parameters make S shrink after Again plus n Good answers from S=D=1. The UI reports "optimal" when the 4-dp values are unchanged.
- **Minimum data**: none enforced. FAQ A6 says any number since 24.06.3, though an old 400-review string remains. The health check needs >300 items. (V, synthetic): 40 items changed nothing; 200 changed all 21; 5.7k items cut hold-out log loss 0.3631 to 0.3590 (true-parameter model 0.3594).
- **Cadence**: manual "once every month is sufficient"; FAQ A4 monthly or whenever the review count doubles. The UI shows "It's been a while" after >30 days (`FsrsOptions.svelte` L59-63), and only Optimize All Presets resets that clock (`update.rs` L410). **No automatic optimization**: `aqt/main.py` `maybeOptimize` just vacuums the database.
- **Optimize All Presets** (`update.rs` L363-412): saves, then runs the same routine per preset (own search, ignore date, relearning-step count; no health check) and writes `fsrs_params_6`. Parameters, DR, ignore date and search belong to the preset; the FSRS switch is global. Empty parameters fall back to v5/v4 vectors, then defaults. FAQ A3: separate presets for different material are "usually better".

## 3. Answering and existing cards
- On display: `fsrs.next_states(memory, dr, days_elapsed)` (`answering/mod.rs` L485-520). DR is the deck override, else the preset value (valid .70-.99). The chosen state is stored in `cards.data` (S 4 dp, D 3 dp, plus dr, decay, lrt).
- Learning steps still run in minutes and update S/D on the t=0 path. With empty steps (or the experimental flag) and w17,w18>0, an FSRS interval <0.5 d becomes an intraday step. Lapse intervals use round().max(1); fuzz applies when leaving relearning.
- **Interval** = I(dr,S). Minimums (`states/review.rs` L179-230): hard=max(1,mfi(I_h)), good=max(hard+1,mfi(I_g)), easy=max(good+1,mfi(I_e)); mfi(I,prev) = prev+1 if round(I)>prev, prev if prev<=upper fuzz bound, else 0. Then fuzz and the maximum interval (default 36500).
- **Fuzz** (`states/fuzz.rs`): none if I<2.5 (round half up). Otherwise delta=1+.15*max(0,min(I,7)-2.5)+.1*max(0,min(I,20)-7)+.05*max(0,I-20); bounds [round(I-delta), round(I+delta)] clamped to [min,max], with hi=lo+1 if equal, >2 and <max; result=floor(lo+f*(1+hi-lo)), f from an RNG seeded with card_id+reps. (V) My port reproduces all 15 rows of Anki's unit test. Rust rounds half away from zero; Python `round()` is banker's.
- **Load balancer** (default on, `load_balancer.rs`): for I<=90 it picks a day in the fuzz range with weight (1/n_due)^2.15*(1/day)^3 (empty day = 1) times sibling and easy-day modifiers, per preset. Easy Days are per weekday: Normal, Reduced (.5), Minimum (~0).
- **Changing DR or parameters** (`update.rs` L221-300): when the FSRS switch, the preset's parameters or DR (preset or deck) change, saving **recomputes memory state for all non-new cards in the affected decks** by replaying each revlog with the new parameters. **Stored due dates do not move** unless "Reschedule cards on change" is ticked (per save, not persisted). If ticked, non-suspended Review cards with a last review get interval I(dr,S), fuzzed or balanced with the same mfi floor, due = today - days_since_review + interval, and a Rescheduled row (type 5) that training ignores. Stored `dr` is informational; the scheduler reads the preset's DR at answer time.

## 4. Desired-retention tools
- Default .90. UI warns <.80 or >.95 and shows red <.70 or >.97. The manual says workload climbs fast above 90% and to stay under 97%.
- The "Approximate workload Nx" box and the simulator ("Help Me Decide") sweep DR 70..99 on existing cards, returning memorized, time and review counts (`deckconfig/service.rs` L106-155, `fsrs/simulator.rs` L285). Costs are mean answer seconds per (state, rating) for 0<time<20 min; rating probabilities come from button usage; defaults otherwise (`simulation.rs` L257, L1688+).
- CMRR left the main options in 25.07 (manual L513). Backend code and a `display:none` block (`SimulatorModal.svelte` L496) remain. It runs Brent search over r in [.70,.95] (tol .01), minimizing total cost / final memorized count (`simulation.rs` L62, L220, L1445), then clamps to [.7,.95] (`retention.rs` L36). Wiki: "The Optimal Retention".

## 5. Metrics Anki uses
- Log loss = -sum w(y ln p+(1-y)ln(1-p))/sum w, with y=(rating>1) and p=R(target delta_t, S replayed from the prefix). `evaluate()` is in-sample with recency weights; the CV path uses weight 1.
- RMSE(bins) = sqrt(sum_b w_b(mean p - mean y)^2/sum_b w_b). Bin keys (`dataset.rs` L99-113):
  - delta_t: round(2.48*3.62^floor(log_3.62 dt)*100);
  - length: round(1.99*1.89^floor(log_1.89(n_longterm+1))), with n_longterm = reviews having delta_t>0 in the item, target included;
  - lapses: 0, or round(1.65*1.73^floor(log_1.73 L)), counting Again rows with delta_t>0 in the history.

  Wiki "The Metric" constants are stale; srs-benchmark `utils.py` agrees with fsrs-rs. (V) Both metrics match fsrs-rs-python `evaluate` to 1e-7.
- **Health check** (`params.rs` L66-77, L182-198; Optimize Current Preset only; checkbox default on; needs >300 items):
  - 5-fold expanding-window CV: segment=N/6, fold i tests segment i+1 and trains on everything earlier, retraining each fold;
  - r = share of items with last rating>1;
  - adjLL = LL/(0.623*(4r(1-r))^0.738); adjRMSE = RMSE/(0.0135/(r^0.504-1.14)+0.176/((N/1000)^0.825+2.22)+0.101);
  - pass if adjLL<=1.11 **or** adjRMSE<=1.53. By my calculation the LL arm is within 0.5% of the entropy of r for r .7-.9, so it means "no worse than predicting the average". The rationale is undocumented.
  - UI text: "FSRS can adapt to your memory well", or "difficult for FSRS to predict ... Hard is a passing grade ... Understand before you memorize". No numbers by default; a hidden legacy Evaluate prints in-sample "Log loss, RMSE(bins)".
- Benchmark (9,999 users, no same-day): FSRS-6 LL .3460 / RMSE .0653 / AUC .7034; AVG baseline .3945 / .1034 / .4997.

## 6. Pitfalls and skills
- **Ratings**: FSRS counts Hard as a pass; the manual warns that Hard-for-forgot inflates intervals. y=(rating>1), so derive ratings from graded outcomes. FAQ A2: Again/Good only is fine.
- **Same-day reviews**: they enter history (t==0 path) but not evaluation. py-fsrs measures t in 24 h blocks, not calendar days; one history gave S 9.30 vs 12.65 (anki_import_fsrs_tooling.md section 6). Feed app-defined day numbers.
- **Mixed review types**: Anki drops cram, set-due and reset rows but keeps early reviews in rescheduling filtered decks. Problem variants or practice-versus-quiz are not modelled; keep one trace per (learner, skill).
- **Sparse data**: <8 items gives defaults, <64 gives w0-3 only, >300 enables the health check. One vector per preset, so group skills into a few presets (course or family), not one per skill.
- **py-fsrs vs Anki**: no S cap at 36500; banker's rounding; random fuzz with min 2 and no hard<good<easy guarantee; `Scheduler` raises ValueError out of bounds. (V) A float32 0.8 (0.800000011920929), which fsrs-rs emits when w9, w19 or w20 hit the clip, is rejected as >0.8. Clamp or round fitted vectors before building `Scheduler`.
- **Skills versus cards**: I found no FSRS-author statement on skills. The nearest primary text is the wiki "Three-Day Journey" (L436-470) on composite memories: R=Ra*Rb, S=SaSb/(Sa+Sb), interference, "complexity approaches zero". That favours atomic skills. A community (non-developer) forum reply calls FSRS "the wrong tool" for practice problems ([thread](https://forums.ankiweb.net/t/questions-about-tuning-fsrs-for-math-logical-reasoning-problem-cards/70949)). There is no prerequisite graph; skill-model pointers are DAS3H and Hunziker et al. (wiki "Research-resources"). Inference: varying problem instances add noise to "recall", so watch the fit metrics.
- FSRS-7 (fractional intervals) exists in the benchmark and fsrs-rs main, not in any release, py-fsrs or Anki 26.09.

**Unverified**: rationale for the relearning-step exception and health-check constants; AnkiDroid/AnkiMobile parity; the exact `next_day_at` formula.
