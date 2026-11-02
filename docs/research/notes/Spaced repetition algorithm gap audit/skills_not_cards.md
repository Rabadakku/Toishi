# Skills, not cards: scheduling varied-problem practice with FSRS

## 1. Math Academy (Skycak): FIRe, compression, speed, failure handling

### Takeaway
Math Academy does not use a flashcard memory model on topics. It uses a simpler pass/fail repetition counter with a half-life decay. Credit and penalties move through a hand-built *encompassing* graph that is kept separate from the prerequisite graph. A per-student, per-topic "speed" scales how much each review counts. The weights, intervals and decay functions are proprietary, and no accuracy or retention results are published.

### Cited Findings
- **Two graphs.** Prerequisite links are "forwards": they decide what to learn next. Encompassing links are "backwards": they decide where credit flows. Prerequisites are often *not* encompassed. A domain expert maintains the encompassing graph. — [Skycak, FIRe](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Implicit repetition.** Passing an advanced topic sends credit down to the topics it encompasses, including second- and third-order ones. Failing a simple topic sends a penalty *up* to the advanced topics that encompass it. — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Weights.** A weight is roughly "P(a random advanced problem covers a random simpler problem)". Only pairs that are nontrivial, not already implied by the flow, and close in the prerequisite graph get explicit weights; all others are 0. A weight can be 0 when a topic needs only conceptual familiarity with its prerequisite. — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Update rules (published form, parameters not given).**
  - `repNum ← max(0, repNum + speed·decay^failed·rawDelta)`
  - `memory ← max(0, memory + rawDelta)·0.5^(days/interval)`
  - rawDelta is larger for stronger passes or weaker failures, and is discounted when memory is still high (early review).
  - `decay` grows with how overdue the review is (it models the "summer slide").
  - — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Speed.** Speed = (speedup from student ability) / (slowdown from topic difficulty). At speed 2x a review counts as 2 repetitions; at 0.5x it counts as 0.5. When speed < 1, the topic "discard[s] all incoming implicit repetition credit and instead force[s] explicit reviews." Curves are calibrated from observed performance alone. — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Compression.** A due review is "knocked out" by choosing an advanced task whose implicit credit covers it. Selection also prefers tasks that head off future reviews. — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Failure and remediation.** Two failed lessons in a row without progress trigger remedial tasks on the prerequisites where the learner got stuck. New topics open only after their prerequisites are mastered. — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- **Load numbers.**
  - About 10 questions per lesson and 3–5 per review.
  - At 3 new topics a day, reviews grow to about 60 questions a day within months; this is the case made for compression.
  - AP Calculus BC: more than 300 topics in about 6000 minutes.
  - — [same](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)

### Inferences
- Math Academy folds difficulty into **how much a review counts** (speed, pass strength), not into the review's label. That is a "magnitude" approach, not a "rating" approach.
- The speed < 1 gate is directly relevant to the app's FIRe shadow mode. Implicit credit to skills the learner finds hard is the riskiest part of compression, and Math Academy turns it off for them.

### Gaps
- No published intervals, weight values, decay function, speed formula, or validation metrics. The Math Academy Way PDF was not checked for outcome numbers.

## 2. Other systems: ALEKS, Duolingo, DASH/personalized review, Khan, SuperMemo, RemNote

### Takeaway
The production systems that work with varied items model **ability × item difficulty** through Elo or IRT. Retention is handled either with coarse rule-triggered rechecks (ALEKS) or with a forgetting term added to an ability/difficulty model (DASH, Pelánek's PFAE). None of them that I found runs a flashcard memory model per skill.

### Cited Findings
- **ALEKS rechecks.** Mastered topics are re-tested in Knowledge Checks. These are triggered after 20 topics learned plus 5 hours, after 10 hours of learning, or after 60 days. A failed or "I don't know" topic moves back to Remaining and the Learning Path, and linked topics may return too. Review mode does not change the knowledge state. — [McGraw Hill ALEKS support](https://www.mheducation.com/support/aleks-support-center/knowledge/aleks-why-must-i-review-a-topic-i-have-already-mastered.html)
- **ALEKS overlearning study.** Requiring 5 correct instead of 3 to master a topic raised first-week retention by about 0.03 (95% CI 0.025–0.036). The difference "has largely disappeared" after several weeks. The study is observational (regression discontinuity). — [Matayoshi et al., EDM 2022](https://educationaldatamining.org/EDM2022/proceedings/2022.EDM-short-papers.27/2022.EDM-short-papers.27.pdf)
- **Duolingo Birdbrain v1 (2020).**
  - An IRT-style logistic model: P(correct) depends on learner ability and exercise difficulty.
  - Exercise difficulty is the sum of feature difficulties.
  - One SGD step per exercise, described as a generalized Elo.
  - Run in shadow mode first, then A/B tested.
  - v2 (May 2022) replaced the single ability number with a 40-dimensional LSTM state.
  - Reported only "engagement and learning increased"; no accuracy figures.
  - — [IEEE Spectrum](https://spectrum.ieee.org/duolingo)
- **Duolingo HLR revisited (2026).** Adding mixed-effects random effects, which the authors read as lexeme difficulty and learner ability, improved on the original HLR. No numbers appear in the abstract. — [Ilídio et al., PMLR 339](https://proceedings.mlr.press/v339/ilidio26a.html)
- **DASH-driven personalized review.** 179 eighth-graders studied Spanish over a semester. Personalized review beat massed review by 16.5% and generic spaced review by 10% on an exam one month later. It is unclear whether these are relative or absolute differences. — [ScienceDaily on Lindsey et al. 2014](https://www.sciencedaily.com/releases/2014/01/140121093046.htm)

### Inferences
- The ALEKS result is weak evidence that extra *massed* initial practice buys little lasting retention, and that spaced rechecks matter more. This supports a short initial lesson followed by spaced reviews.

### Gaps
- Khan Academy mastery and decay rules, SuperMemo's handling of problem-like items, and RemNote's concept scheduling were not researched in this pass. No sourced claims are available.

## 3. Knowledge-tracing families and models that combine forgetting with item difficulty

### Takeaway
The best-supported structure for "a skill practiced with varied items" is an **additive logistic model**:

`P(correct) = σ(ability − item difficulty + skill easiness + time-windowed history term)`

This is DASH/DAS3H, and Elo/PFAE is its online cousin. It beats models that capture only difficulty or only forgetting. However, the published evaluations split data **by student**, so prediction on *brand-new items* is mostly untested. The exception is KAR³L, which uses item text.

### Cited Findings
- **DAS3H structure.** `σ(α_s − δ_j + Σβ_k + Σ_k Σ_w [θ·log(1+correct_{k,w}) − θ'·log(1+attempts_{k,w})])`. The windows are {1h, 1d, 7d, 30d, ∞}, and the θ parameters are fit separately for each skill. — [Choffin et al. 2019](https://arxiv.org/pdf/1905.06873v1)
- **DAS3H results (AUC).**
  | Dataset | DAS3H | DASH | IRT | PFA | AFM |
  |---|---|---|---|---|---|
  | algebra05 | 0.826 | 0.775 | 0.771 | 0.744 | 0.707 |
  | assist12 | 0.744 | 0.703 | 0.702 | 0.669 | 0.610 |
  | bridge06 | 0.791 | 0.749 | 0.747 | 0.746 | 0.706 |

  Time windows beat plain counts. Skill-specific parameters beat shared ones by about 0.03–0.04 AUC. The paper has no ablation for the item-difficulty term, and its cross-validation is split by student, so unseen items are not tested. — [Choffin et al. 2019](https://arxiv.org/pdf/1905.06873v1)
- **Elo basics (Pelánek).**
  - `θ += K(correct − P)`, `d −= K(correct − P)`, with uncertainty `K = a/(1+bn)` (a=1, b=0.05).
  - Elo estimates come close to joint maximum likelihood for the Rasch model.
  - **Proportion correct is valid under random item selection but fails under adaptive selection.**
  - About 10 answers give a skill estimate correlated about 0.8 with the truth (simulation).
  - About 100 students are needed for good item-difficulty estimates.
  - Outline Maps targets a 75% success rate.
  - Response time can be modeled as an expected log-time of d − θ.
  - — [Pelánek, Elo in adaptive educational systems](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- **PFAE with forgetting.** Elo-style asymmetric updates plus a learned staircase f(time since last attempt) raised AUC from 0.719 (PFA) to 0.761. Memory activation drops fast within about 10 minutes, stays roughly flat for about a day, then declines. — [Pelánek, EDM 2015](https://www.educationaldatamining.org/EDM2015/proceedings/short480-483.pdf)
- **KAR³L (content-aware: BERT + retrieval + DKT).**
  - Seen cards: AUC 0.864 vs FSRS 0.752; ECE 0.091 vs 0.111.
  - Unseen cards: AUC 0.786. FSRS cannot predict unseen cards at all.
  - Removing BERT drops unseen-card AUC from 0.740 to 0.612.
  - Its tables report inconsistent full-model numbers.
  - Online study (27 users): post-test accuracy 0.86 vs FSRS 0.88, so no clear retention gain.
  - — [Shu et al., EMNLP 2024](https://arxiv.org/html/2402.12291v3)
- **LECTOR (LLM semantic similarity).** 90.2% vs 88.4% success, measured **only in simulation** with 100 simulated learners. Weak evidence. — [arXiv 2508.03275](https://arxiv.org/abs/2508.03275)

### Inferences
- DAS3H separates three things that the app currently mixes inside FSRS's view of a review: **ability (α), item difficulty (δ), and history/forgetting (h)**. The app's Elo + tiers + FSRS design is roughly this decomposition, run online. The missing piece is combining the parts in one prediction.

### Gaps
- BKT (Corbett & Anderson), Yudelson's individualized BKT, DKT/attention models, and "knowledge tracing with forgetting" (e.g., Nagatani 2019) were not fetched.
- I found no study that tests delayed performance on unseen items of the same skill with a DASH-family model.

## 4. What the FSRS community says

### Takeaway
The FSRS maintainers model **one card's own history** under a Markov assumption. They say cross-item effects need an app designed for them from the start. A widely cited community answer calls spaced repetition the "wrong tool" for practicing problems, while noting that a *different* problem each time may help. I found no official FSRS guidance on skill-level FSRS or on difficulty-adjusted ratings.

### Cited Findings
- **Expertium on FSRS's limits.** "FSRS and SM-2 cannot access the review history of any other card." Working out how one card's review should change another's difficulty and stability is hard. Handling this "would need to build an app with this kind of stuff in mind from the very beginning," and he linked Skycak's FIRe. — [AnkiWeb forum](https://forums.ankiweb.net/t/interval-determination-of-siblings/49267)
- **Expertium's sibling experiment.** sorata reports that Expertium tried raising a card's stability when a sibling was reviewed, as a "partial review." — [same](https://forums.ankiweb.net/t/interval-determination-of-siblings/49267)
- **Danika_Dakika (forum volunteer, not a maintainer).**
  - Spaced repetition is "the wrong tool" for *practice*.
  - "doing a completely separate problem" helps more than repeating one problem.
  - Practice may need "a lot fewer repetitions, spaced further apart."
  - "Do not tweak your parameters" by hand.
  - — [AnkiWeb forum, Sept 2026](https://forums.ankiweb.net/t/questions-about-tuning-fsrs-for-math-logical-reasoning-problem-cards/70949)
- **Advice for mixed difficulty.** Put easy and hard decks in separate presets. — [AnkiWeb forum](https://forums.ankiweb.net/t/fsrs-and-different-level-of-difficulty/48511)
- **srs-benchmark (no same-day reviews; log loss / RMSE(bins) / AUC).**
  | Model | Log loss | RMSE(bins) | AUC |
  |---|---|---|---|
  | FSRS-6 | 0.3460 | 0.0653 | 0.7034 |
  | DASH | 0.3682 | 0.0838 | 0.6311 |
  | HLR | 0.4694 | 0.1275 | 0.6369 |
  | RWKV-Instant | 0.2773 | 0.0250 | 0.8329 |

  RWKV-Instant uses sibling information, review duration and the deck hierarchy, and is not optimized per user. DASH's item-difficulty term was dropped as "not applicable." RMSE(bins) bins predictions by interval, review count and lapse count. Evaluation uses a time-series split. The page is inconsistent on dataset size (10k vs 20k users). — [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)

### Inferences
- FSRS's per-card difficulty D is learned only from ratings. When problems vary, problem-difficulty variance shows up as **rating noise**: D drifts and stability updates get noisier.
- Restricting FSRS events to a fixed core band of tiers turns R into "P(first-try success on a typical core problem of this skill)." That is a coherent, calibratable quantity. This is my reasoning, not a published claim.
- Cross-item information clearly improves prediction (RWKV, KAR³L). This supports keeping FIRe-style credit, but behind validation.

### Gaps
- I found no L-M-Sherlock statement or GitHub issue on whether item difficulty should change the rating or the memory update. The Challenging Tasks Notion page did not render.

## 5. Recommendations (my proposals unless cited)

### Takeaway
Keep FSRS as the **memory/timing** model for a skill. Keep Elo/tiers as the **ability × difficulty** model. Combine the two only at prediction time, in logit space, as DAS3H does, rather than bending FSRS ratings by problem difficulty. Log raw outcomes so every mapping can be re-fit and checked against held-out data.

### Cited Findings
- Additive ability − difficulty + history beats any single factor. — [Choffin et al.](https://arxiv.org/pdf/1905.06873v1)
- Shadow mode, then comparison, is how Birdbrain was rolled out. — [IEEE Spectrum](https://spectrum.ieee.org/duolingo)
- Raw success rates are biased under adaptive selection. — [Pelánek](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- When skill speed is low, Math Academy turns off implicit credit. — [Skycak](https://www.justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- Evaluation: log loss, RMSE(bins), AUC with a time-series split. — [srs-benchmark](https://github.com/open-spaced-repetition/srs-benchmark)

### Inferences
**Well supported**
- **Core band only.** It controls the adaptive-selection bias that Pelánek describes.
- **Fixed tier difficulties.** These solve cold start for one learner; Elo needs about 100 students to learn item difficulty.
- **Elo for choosing difficulty.** This is standard practice (Pelánek; Duolingo).
- **FIRe kept in shadow mode.**
- **A fresh problem each review.** This counters memorizing specific answers.

**Risky**
1. **Hard covers too many outcomes.** "Second try", "hint", "unsure" and "slow" all map to Hard, and FSRS counts Hard as *recall*. Predicted R will then overstate first-try success, and hints in particular may hide failures. Consider mapping "hint" and "second try" to Again, or store them as their own outcome.
2. **Double penalty after a failure.** One failure updates both Elo (the next problem gets easier) and FSRS (the review comes sooner). That compounds, and it confounds evaluation.
3. **Ability growth read as stability.** Elo ability rising inside the core band may be absorbed as stability growth. This is mostly harmless, but it means S is not pure "memory."
4. **Implicit credit to low-ability skills.** Gate it the way Math Academy does.
5. **Changing rating semantics.** Upgrading or downgrading ratings by tier, for example Good on tier 5 → Easy, changes what the ratings mean, and the optimizer then fits a mixture. Avoid it.

**Missing**
- **Raw event log.** Record tier, attempts, hint, time, confidence, and the predicted R and Elo P at the moment of review. Without this, nothing can be re-fit.
- **Combined prediction.** `p = σ(logit(R_FSRS) + (θ_skill − d_tier) − (θ_skill − d_core))` for any tier. Use it to pick tiers and to log stretch results for evaluation. FSRS state stays untouched.
- **Per-learner evaluation.** Do a rolling time-series split and compare:
  - (a) FSRS R alone
  - (b) FSRS R + tier offset
  - (c) Elo alone
  - (d) a constant baseline

  Report log loss, a calibration curve, and RMSE(bins). Expect noisy AUC with only a few hundred events.
- **Gate FIRe credit on measured gain.** Turn it on only if, in shadow mode, it improves held-out log loss on the encompassed skills' next core-band outcomes.
- **Remediation rule.** Repeated failure should route to prerequisites, as Math Academy does with two failures.

### Gaps
- No published data on how many reviews a skill-level FSRS needs before its fit can be trusted for one learner.
- No study compares rating-adjustment against prediction-adjustment for varied-difficulty items. The recommendation above rests on the DAS3H-style decomposition, not on a direct test.
