# Evaluation and policies for learner models and practice schedulers: source notes

Compiled 2026-11-02 for the Toishi student-model and scheduler design. Gather-only: these notes report what sources say. They contain no recommendations.

**Length:** this file runs over the ~5,000-word target: about 7,050 words in total (front matter and Sections 1-6 about 5,380; Section 7, added mid-task, about 1,450; closing list about 230). Entries keep key numbers only.

**Evidence tags:** FT = full text read. WF = read through WebFetch (tool-summarised page; numbers not cross-checked against a PDF). AB = abstract or landing page only. OCR = OCR of a scanned PDF. NOTE = relayed from an existing repo note, not re-verified here. UNVERIFIED = secondhand or not seen.

**Fields:** Cite = citation and link. Studied = population, task, N. Method. Results. Limits = limitations the authors state; "(gatherer)" marks my own observation.

**Existing notes (cited by path, not re-gathered).** Root = /docs/research/notes/
- SRS = `Spaced repetition algorithm gap audit/` (`papers_annotated.md`, `verifying_srs.md`, `skills_not_cards.md`)
- EVID = `Toishi full evidence review/engine_decisions_evidence.md`
- PRAC = `Practice systems and learning science/` (`practice_platforms.md`, `skill_trainers_and_srs_apps.md`, `science_of_practice.md`)
- FSRS = `Toishi build research/learning_science.md`

**Contents:** 1 learner-model evaluation; 2 identifiability and degeneracy; 3 policy evaluation; 4 mastery and stopping; 5 model-based spaced review; 6 randomized and large-scale adaptive-math evaluations; 7 problem difficulty and adaptive-selection bias; Could not find or verify.

---

## 1. Learner-model evaluation: metrics, data splits, data collection

### 1.1 Pelánek 2017, survey (evaluation section)
- **Cite:** Pelánek, R. (2017). Bayesian knowledge tracing, logistic models, and beyond: an overview of learner modeling techniques. User Modeling and User-Adapted Interaction. https://www.fi.muni.cz/~xpelanek/publications/umuai-overview.pdf [FT, §6]
- **Studied:** survey of learner-model families and evaluation practice; no new data.
- **Method:** literature review.
- **Results:** Metrics covered: RMSE, log-likelihood (LL), R², accuracy, F1, AUC. Metric choice can change a model comparison: Khajah et al. 2016 (cited) found AUC over all predictions vs AUC averaged per skill inflated differences between models. If a policy uses absolute predicted probabilities, AUC (a ranking measure) is not meaningful. Small metric differences can matter in practice (Yudelson & Koedinger 2013; Liu 2014; both cited). A mixture model can predict mastery for an always-wrong learner (Streeter 2015, cited). Random train/test splits are "incorrect" for sequential data; the preferred setup for predictions is "online, generalization to new learners". Data-collection biases named: mastery attrition, self-selection, item-order confound. Adaptive item selection creates a feedback loop, and with adaptive data a baseline can look good (Pelánek 2016, cited). Counters named: controlled randomization; filtering historical data (e.g. capping answers per learner). Ideal evaluation: an RCT with the real system.
- **Limits:** the survey "does not provide crystal clear guidance" on evaluation.

### 1.2 Pelánek 2015, metrics (simulation)
- **Cite:** Pelánek, R. (2015). Metrics for evaluation of student models. Journal of Educational Data Mining 7(2). https://www.fi.muni.cz/~xpelanek/publications/metrics.pdf [FT]
- **Studied:** 20 simulated datasets (BKT and AFM generators), 10,000 attempts each; 15 models (BKT, PFA, Elo variants); 300 model-dataset combinations.
- **Method:** compare MAE, RMSE, LL, AUC on which model each ranks best; worked examples; reliability diagrams.
- **Results:** Agreement on the best model across the 20 cases: RMSE-LL 17, AUC-RMSE 7, AUC-LL 5, MAE-RMSE 3, MAE-AUC 2, MAE-LL 2. Worked example, true p=0.7 vs an always-0.9 model: MAE 0.42 vs 0.34, so MAE prefers the wrong model; the squared-error row is 0.21 vs 0.25 (printed before the square root) and picks the right one. Reliability-diagram example: RMSE 0.344 vs 0.345 for two models that behave differently (model 2 predicts mostly around 0.93). Conclusions: do not use MAE; use AUC with caution; LL or RMSE are reasonable. §6.3: a wrongly merged-skill model collects data that hides its deficiency. Cites Yudelson & Koedinger 2013: small predictive differences give 7-20% over- and under-practice (secondary).
- **Limits:** none recorded; (gatherer) simulated data only.

### 1.3 Pelánek 2018, "The details matter"
- **Cite:** Pelánek, R. (2018). The details matter: methodological nuances in the evaluation of student models. UMUAI 28(3), doi 10.1007/s11257-018-9204-y. https://www.fi.muni.cz/~xpelanek/publications/methodological.pdf [FT]
- **Studied:** simulated learners (Fig. 1: 10,000 students) and stylised scenarios.
- **Method:** controlled examples showing how evaluation choices change conclusions.
- **Results:** Trace length: RMSE at 10 vs 50 answers is 0.48 / 0.39 for model B and 0.53 / 0.31 for model C (ranking flips). Fitted BKT at 10 vs 50 answers: Pinit 0.52 / 0.16, Plearn 0.41 / 0.37, Pslip 0.28 / 0.07, Pguess 0.21 / 0.21. Mastery attrition (curve 0.7e^(-0.06x), stop at "4 correct in a row") flattens and flips the learning curve; the PFA vs BKT ranking depends on fixed-length vs mastery-collected data. Self-selection: two flat subpopulations at 50% and 80% produce an illusory learning curve. Adaptive 75% target: a constant-0.75 baseline ties a good model. Same-student last-20% test sets plus "3 correct in a row" mastery: a model predicting 0.7 beats the true 0.5 model. Averaging, with 70% of students at 5 attempts and 30% at 60: RMSE globally vs per student is 0.40 / 0.46 (B) and 0.35 / 0.48 (C). AUC globally vs per KC: correct model 0.73 / 0.63; speed-mismatch model 0.60 / 0.63; negative-learning model 0.68 / 0.45. Per-student AUC is undefined when all answers are the same. Also covers student-level vs item-level cross-validation and static vs dynamic prediction.
- **Limits:** none recorded; (gatherer) simulated examples.

### 1.4 Effenberger & Pelánek 2020
- **Cite:** Effenberger, T., Pelánek, R. (2020). Impact of methodological choices on the evaluation of student models. AIED 2020, LNCS 12163, doi 10.1007/978-3-030-52237-7_13 [FT]
- **Studied:** prediction of log problem-solving time in four programming exercises. Arrows: 94 items, 13,000 students, 182,000 successful attempts. Robot: 85, 10,800, 146,000. Turtle: 77, 10,100, 87,000. Python: 73, 1,400, 17,000.
- **Method:** six models, 10-fold student-level CV; vary attempt filtering, metric, averaging, per-level disaggregation, time-series vs student-level CV.
- **Results:** Keeping learners with at least 10, 20, 30, 40 attempts keeps 86%, 47%, 22%, 13% of the original attempts; absolute RMSE changes more than model differences, but rankings barely change. RMSE vs MAE changes the order of I-Avg and SI-Avg. Global vs per-student vs per-item averaging changes values and some ranks. Complex models do not win in the advanced levels. Under time-series CV Elo wins on Turtle (consecutive students' item performance is correlated), unlike under student-level CV. Conclusion: differences between metric settings exceed differences between models, so comparing with published numbers is "very dangerous".
- **Limits:** none recorded; (gatherer) outcome is time, not correctness.

### 1.5 Pelánek, Řihák & Papoušek 2016, data collection
- **Cite:** Pelánek, R., Řihák, J., Papoušek, J. (2016). Impact of data collection on interpretation and evaluation of student models. LAK 2016. https://www.fi.muni.cz/~xpelanek/publications/lak16-data-collection.pdf [FT]
- **Studied:** simulated data, plus real slepemapy.cz geography answers from the four conditions of item 1.6 (200,000-250,000 answers per group; 20% train / 80% test split by student).
- **Method:** compare Elo and naive predictors (constant, student average, item average) across conditions; simulate mastery attrition and adaptive selection.
- **Results:** More adaptivity gives higher RMSE and a smaller spread between models. Naive predictors come close to Elo, and the item-average vs student-average order swaps. In simulation the model that picks items for the system produces the largest RMSE and the smallest differences; a constant model looks comparable. A merged Q-matrix (10 KCs vs 2 merged) is hard to detect. Item-difficulty estimates (Elo vs percent-correct, European countries): the data set mattered more than the model. BKT fits depend on trace length: data from logistic σ(θ+0.4k), θ~N(-1,1) give Pinit/Plearn/Pslip/Pguess of 0.25/0.25/0.29/0.19 at trace length 5 and 0.08/0.24/0.03/0.21 at length 25. Data from BKT (0.25/0.08/0.12/0.3): fixed length 20 recovers 0.27/0.08/0.10/0.27; "3 correct in a row" collection fits 0.72/0.23/0.52/0.15. With logistic data σ(θ+0.1k), θ~N(-0.4,2), PFA beats BKT under constant trace length and BKT beats PFA under "k correct in a row". Stated recommendations: document the collection mechanism; probe stability (e.g. shorter traces); use controlled randomization, which "would enable easier evaluation without hampering" learning.
- **Limits:** none recorded; (gatherer) one platform and domain.

### 1.6 Papoušek, Stanislav & Pelánek 2016, adaptive geography RCT
- **Cite:** Papoušek, J., Stanislav, V., Pelánek, R. (2016). Evaluation of an adaptive practice system for learning geography facts. LAK 2016. https://www.fi.muni.cz/~xpelanek/publications/lak16-evaluation.pdf [FT]
- **Studied:** slepemapy.cz, Aug-Oct 2015, more than 1,300,000 answers, roughly 20,000 learners, random assignment on entry to four conditions. Letters are (question stem, options): adaptive-adaptive A-A, A-R, R-A, R-R.
- **Method:** target error rate 20% in adaptive parts; every 1st, 11th, 21st... question is an open reference question about a random item (the first comes before the algorithm can influence practice); analyses of return probability, attrition and learning curves (Weibull survival fits).
- **Results:** Return probability (95% CI ±0.9%): A-A 15.1%, A-R 13.9%, R-A 14.3%, R-R 13.1%. Attrition differs across conditions and is not only mastery attrition. Different learning-curve filtering approaches give different curves. Adaptive beats random in all analyses; adaptivity matters mainly for choosing the number of options and distractors, not the stem. Adaptive stem choice relates to initial mortality, adaptive options to the overall length of stay; for learning the main factor is adaptive choice of options.
- **Limits:** learning curves ignore time between attempts; 80% of answers came in the first session.

### 1.7 Pelánek & Řihák 2017, mastery criteria
- **Cite:** Pelánek, R., Řihák, J. (2017). Experimental analysis of mastery learning criteria. UMAP 2017, doi 10.1145/3079628.3079667. https://www.fi.muni.cz/~xpelanek/publications/mastery-detection.pdf [FT]
- **Studied:** simulated learners (BKT scenarios B1-B6, logistic L1-L6; 50 answers; 10,000 train + 10,000 test). Real: Czech grammar (over 40,000 answer sequences); MatMat arithmetic (330,000 answers, more than 8,000 learners).
- **Method:** compare BKT threshold, N-consecutive-correct (NCC) and exponential moving average (EMA) by weighted mean absolute deviation (wMAD); effort-score graphs (effort = average attempts to mastery; score = correct answers in the next k=5).
- **Results:** With true BKT parameters (thresholds 0.9-0.97; NCC N 2-8) BKT is "typically better, but the difference is not large", decision correlation is typically very high, and the largest difference is at high slip and low guess. Table 2 (scenario: NCC N / BKT T / wMAD NCC / wMAD BKT / correlation): B1 2/0.92/2.56/2.42/0.88; B2 4/0.97/6.2/5.76/0.97; B4 1/0.9/2.72/2.13/0.74; B6 8/0.97/11.48/10.33/0.94. EMA is slightly better than NCC (Table 3, wMAD NCC / EMA95 / full EMA): L3 7.39/6.21/5.04; L1 3.92/3.34/2.63; B4 2.82/3.47/2.31; L4 10.28/10.7/10.3. In L6 the optimal alpha varies from 0.52 to 0.73 with the weight w. N >= log_alpha(1-T): at T=0.95, alpha 0.7, 0.75, 0.8, 0.85, 0.9, 0.95 gives N = 9, 11, 14, 19, 29, 59. Response times have a larger effect than the learner model. Conclusion: data source and threshold matter more than model technique.
- **Limits:** single, well-specified KCs; no forgetting; no wheel spinning; no biases in real data. Related work cited (secondary): Fancsali et al. threshold simulations; Pardos & Yudelson (RMSE good, AUC poor for moment of learning).

### 1.8 Pelánek & Řihák 2018, mastery criteria (journal extension)
- **Cite:** Pelánek, R., Řihák, J. (2018). Analysis and design of mastery learning criteria. New Review of Hypermedia and Multimedia 24(3):133-159. https://www.fi.muni.cz/~xpelanek/publications/nrhm-mastery.pdf [FT]
- **Studied / Method:** extends 1.7 with a time-intensity extension of EMA and a deployment in Umíme (Czech grammar, English vocabulary, math calculation, matching).
- **Results:** Tables 3 and 4 repeat the 1.7 experiments with the same numbers. Time-to-mastery distributions are similar across 5 exercises while attempts differ.
- **Limits:** no forgetting, no wheel spinning, no real-data bias handling.

### 1.9 Pelánek 2018, conceptual issues in mastery criteria
- **Cite:** Pelánek, R. (2018). Conceptual issues in mastery criteria: differentiating uncertainty and degrees of knowledge. AIED 2018. Saved as mastery-modeling.pdf; likely https://www.fi.muni.cz/~xpelanek/publications/mastery-modeling.pdf (exact URL not recorded; UNVERIFIED) [FT, brief]
- **Studied / Method:** proposes LogisticHMM and a two-threshold criterion, P(theta >= Tm) >= Tu; compared with common criteria on simulated data.
- **Results / Limits:** not extracted beyond the proposal.

---

## 2. Identifiability and degeneracy

### 2.1 Beck & Chang 2007 (not retrieved)
- **Cite:** Beck, J.E., Chang, K. (2007). Identifiability: a fundamental problem of student modeling. UM 2007, doi 10.1007/978-3-540-73078-1_44. Springer landing page only [UNVERIFIED].
- **As described by Doroudi & Brunskill 2017 and van de Sande 2013:** Table 1 shows three BKT parameter sets with identical P(correct) at each step but different P(learned); "statistically there is no justification for preferring one model over another" (quoted via Doroudi); Dirichlet priors proposed.

### 2.2 Doroudi & Brunskill 2017
- **Cite:** Doroudi, S., Brunskill, E. (2017). The misidentified identifiability problem of Bayesian Knowledge Tracing. EDM 2017. https://www.cs.cmu.edu/~shayand/papers/EDM2017.pdf [FT]
- **Studied:** theory plus simulation: BKT fitted to data from a 10-state HMM and from AFM.
- **Method:** re-analysis of Beck & Chang's example conditioning on data; identifiability via the Anandkumar et al. HMM result; taxonomy of semantic degeneracy; grid-search fits (0.01 steps), 500 sequences × 20 practices vs 100 × 200.
- **Results:** Beck & Chang compared marginal predictions P(C_i) without conditioning on data; conditioning on the sequence (1,0,0,0,0,0,0,1,1) their three models differ. BKT is identifiable from joint distributions of up to 3 observations if P(L0) is not in {0,1}, P(T) != 1 and P(G) != 1-P(S). Semantic degeneracy is separate. Taxonomy: forgetting (G+S>1), low-performance mastery (S>0.5), high-performance guessing (G>t), high performance without learning (P(mastery) < 0.95 after m=10 correct). Table 3 fitted P(G)/P(S): 0.27/0.44 at length 20, 0.49/0.13 at length 200. AFM-generated data: G 0.14, S 0.46 at 20; G 0.28, S 0.03 at 200. A fitted model gives P(K11=1 | 10 correct) of about .89, below 0.95. For the first model in Table 3, BKT assumes 56% correct at "mastery" where a truly mastered student has 90%, so a tutor using it "will likely give far fewer problems" than needed. Suggestions: domain knowledge in fitting, or alternative models; a degenerate fit is informative.
- **Limits:** none recorded; (gatherer) conclusions rest on simulation.

### 2.3 van de Sande 2013
- **Cite:** van de Sande, B. (2013). Properties of the Bayesian Knowledge Tracing model. JEDM 5(2). https://jedm.educationaldatamining.org/index.php/JEDM/article/download/35/pdf_27 [FT]
- **Studied / Method:** analytical; no data.
- **Results:** The student-averaged chain gives P(C_j) = 1-P(S) - A·e^(-beta·j), with A=(1-P(S)-P(G))(1-P(L0)) and beta = -log(1-P(T)). It depends on three parameters, which explains the Beck & Chang "identifiability"; the form is exponential, not a power law. The HMM has no identifiability problem given both correct and incorrect steps. Constraints: P(G)+P(S)<1 and 0<P(T)<1-P(S)/(1-P(G)); otherwise P(L|O) falls after correct answers, matching Baker's "empirically degenerate". Maximum likelihood is preferred over RSS.
- **Limits:** analytical only.

### 2.4 Baker, Corbett & Aleven 2008
- **Cite:** Baker, R.S.J.d., Corbett, A.T., Aleven, V. (2008). More accurate student modeling through contextual estimation of slip and guess probabilities in Bayesian Knowledge Tracing. ITS 2008. https://learninganalytics.upenn.edu/ryanbaker/BCA2008W.pdf [FT]
- **Studied:** Middle School Tutor (Cognitive Tutor), 2002-2003: 232 students (grades 6-8), 581,785 transactions on 171,987 problem steps, 253 skills, 37 lessons; 290,698 further transactions were excluded because they were not labeled with skills.
- **Method:** compare baseline BKT, Dirichlet priors, bounded guess/slip (G<=0.3, S<=0.1) and a contextual guess-and-slip model; theoretical degeneracy (G or S > 0.5) and empirical tests N=3 and M=10.
- **Results:** Theoretically degenerate skills: baseline 75%, Dirichlet 76%, bounded 0%. First empirical test failed on 2% / 2% / 0% of skills (baseline / Dirichlet / bounded); second (10 correct but P(L)<0.95) failed on 23% / 23% / 5%. Contextual model (trained on 64 skills): second test failed 13 of 758 (1.7%). A' across 171,989 first actions: baseline 0.66, bounded 0.61, Dirichlet 0.65, contextual 0.75 (r = 0.29, 0.25, 0.26, 0.43).
- **Limits:** one Cognitive Tutor; needs replication.

### 2.5 Slater & Baker, sample size and BKT error
- **Cite:** Slater, S., Baker, R.S. Degree of error in Bayesian Knowledge Tracing estimates from differences in sample sizes. Behaviormetrika (year not in the preprint text I read). https://learninganalytics.upenn.edu/ryanbaker/behaviormetrika_vfinal.pdf [FT]
- **Studied:** 51,030 simulated datasets; students 5/10/25/50/100/250/500; problems per set 3/6/10; 30 trials per cell.
- **Results:** 5 and 10 students do not converge to the seed. Parameter SD falls with more students. About 4x as much error at 25 vs 500 students, about 2x at 3 vs 10 problems. Extreme parameters occur "up to 42%" of the time. Mastery-prediction error stays within 2-3 problems from 25 students and at least 3 opportunities. To avoid extremes the authors say at least 250 students and 6 problems per skill per student.
- **Limits:** simulation only (gatherer).

---

## 3. Policy evaluation

### 3.1 Doroudi, Aleven & Brunskill 2017, Robust Evaluation Matrix
- **Cite:** Doroudi, S., Aleven, V., Brunskill, E. (2017). Robust evaluation matrices: towards a more principled offline exploration of instructional policies. L@S 2017, doi 10.1145/3051457.3051463. https://www.cs.cmu.edu/~shayand/papers/L@S2017.pdf [FT]
- **Studied:** Case 1: fractions tutor, more than 1,000 students for model fitting, 4-6 days, 20-100 problems, 16-item pre/post-test; policies AP-1 and AP-2 (from a G-SCOPE-based model) vs spiral non-adaptive baselines 1 and 2 and BKT-MP; 40 problems and 1,000 simulated students per policy. Case 2: Rafferty et al. concept-learning experiment (POMDP policies).
- **Method:** REM = simulate each policy under several plausible student models and compare. Importance sampling is unbiased but high variance: if logged data come from a policy choosing each of 20 binary decisions at random, only one in 2^20 (over one million) students matches a deterministic policy; 50 decisions need over 10^15 students.
- **Results:** Predicted (G-SCOPE model) vs actual posttest out of 16 (± as printed): Baseline 1 5.87±0.90 vs 5.52±2.61; Baseline 2 6.10±0.97 vs 5.14±3.22; BKT-MP 7.03±1.00 vs 5.46±3.0; AP-1 7.85±0.98 vs 5.57±3.27; AP-2 9.10±0.80 vs 4.93±1.8. Predicted Cohen's d 3.66 (AP-2 vs Baseline 2) and 4.14 (vs Baseline 1); actual: no significant difference. Under a BKT model AP-2 7.04 and Baseline 1 6.46; under a DKT model Baseline 1 9.89 beats AP-1 8.31 and AP-2 8.58. The three student models had RMSE 0.41-0.44. Trajectory lengths depend on the policy: Baseline 1 students did about 48 problems on average, the others 28 or fewer. Case 2 (as recorded): model agreement predicted the POMDP policies would beat random (confirmed) and flagged the max-information-gain policy, which failed in the real experiment.
- **Limits:** REM can be over-conservative and depends on the models chosen.

### 3.2 Doroudi, Aleven & Brunskill 2019, "Where's the reward?"
- **Cite:** Doroudi, S., Aleven, V., Brunskill, E. (2019). Where's the reward? A review of reinforcement learning for instructional sequencing. IJAIED 29(4), doi 10.1007/s40593-019-00187-x. https://link.springer.com/content/pdf/10.1007/s40593-019-00187-x.pdf [WF]
- **Studied:** review of RL-induced instructional policies tested with students: "34 papers containing 41 studies that matched our criteria".
- **Method:** each study coded Sig / ATI / Mixed / Not Sig / Sig Worse (labels as printed in Table 2) and grouped into clusters.
- **Results:** Table 2 "All Studies" (Sig/ATI/Mixed/Not Sig/Sig Worse): 21/4/4/11/1 (sum 41). Clusters: paired-associate 11/0/0/2/1; concept learning 4/0/2/1/0; sequencing interdependent content 0/0/2/6/0; sequencing activity types 4/4/0/2/0; maximizing other objectives 2/0/0/0/0. Abstract: "over half of the studies found that RL-induced policies significantly outperform baselines"; RL "most successful in cases where it has been constrained"; a theory-informed model "might be more useful". Baselines: "17 of them (71%) compared ... to a random baseline"; "RL-induced policies were compared to relatively weak baselines". A Results sentence reads "Twenty-one of the 36 studies found that at least one RL-induced policy was..." (36 vs 41 in Table 2: UNVERIFIED which is intended).
- **Limits:** "even robust evaluations are limited by the models considered"; "it does not seem like RL-based instructional policies have significantly impacted educational practice to date"; the review may have missed studies.

### 3.3 Rollinson & Brunskill 2015
- **Cite:** Rollinson, J., Brunskill, E. (2015). From predictive models to instructional policies. EDM 2015. https://www.educationaldatamining.org/EDM2015/proceedings/full179-186.pdf [WF]
- **Studied:** KDD Cup 2010 Algebra I 2008-2009: 8,918,054 rows cut to 3,292 students, 505 skills, 421,991 sequences.
- **Method:** 5-fold CV of BKT, PFM, AFM; predictive-similarity stopping (epsilon=0.01, delta=0.95) vs mastery threshold 0.95, scored by ExpOps (simulated expected problems; path threshold 1e-7; max length 100).
- **Results:** RMSE: BKT 0.353-0.366, PFM 0.364-0.369, AFM 0.368-0.374. ExpOps correlation 0.95 on 218 skills with meaningful BKT parameters and 0.55 on the other 283 (between the two stopping rules, as I read it). Immediate stopping: AFM 295 skills (59%), PFM 130 (26%), BKT 31 (6%). ExpOps correlations across models, all skills: AFM-PFM 0.32, AFM-BKT -0.06, PFM-BKT 0.16 (0.72 / 0.44 / 0.46 excluding immediate stops). Conclusion: models with similar accuracy recommend very different practice amounts.
- **Limits:** (gatherer) one dataset; simulated ExpOps metric; no learning outcomes; myopic, one-skill-at-a-time policy.

---

## 4. Mastery and stopping

Pelánek & Řihák (items 1.7-1.9) and Rollinson & Brunskill (3.3) also belong here.

### 4.1 Kelly, Wang, Thompson & Heffernan 2015
- **Cite:** Kelly, K., Wang, Y., Thompson, T., Heffernan, N. (2015). Defining mastery: knowledge tracing versus N-consecutive correct responses. EDM 2015 poster, pp. 630-631. https://www.educationaldatamining.org/EDM2015/proceedings/poster630-631.pdf [WF; poster]
- **Studied:** ASSISTments. Study I: next-problem correctness from large datasets (about 285-287 students per table). Study II: RCT on a transfer question (about 37-74 students per table).
- **Method:** 3-CCR, 5-CCR and knowledge tracing at 0.95 compared on false positives and false negatives.
- **Results:** Study II false positives / false negatives: 3-CCR 43% / 0%; 5-CCR 19% / 8%; KT 39% / 7%. The fetch also reports over 90% of students reaching the higher threshold after 3-CCR (wording unclear). Study I: KT (95%) 80.5% "met & correct". PRAC `science_of_practice.md` (line 209) cites it as "only 56 students"; the poster's own N is not stated and table sizes are inconsistent.
- **Limits:** none; no tests reported.

### 4.2 Cen, Koedinger & Junker 2007 (secondary only)
- **Cite:** Cen, H., Koedinger, K., Junker, B. (2007). Is over practice necessary? AIED 2007. Primary NOT retrieved. Read: LearnLab wiki "Using learning curves to optimize problem assignment" https://learnlab.org/research/wiki/index.php/Using_learning_curves_to_optimize_problem_assignment [WF; no authors or sample size on the page]
- **Studied:** 1997 Geometry Cognitive Tutor, Area unit; the control group used the original parameters.
- **Method:** Learning Factors Analysis identified over- and under-practiced KCs; problem assignment was adjusted.
- **Results:** Over-practiced example: rectangle-area error about 12% falling to 8% after 18 practices (mean 10). Under-practiced: trapezoid-area error 76%, still about 40% at the 6th practice. About 22 minutes saved (12%): Unit 2 5 minutes (p=.01), Unit 1 14 minutes (p=.19). Both groups gained about 5 points; condition p=0.772, interaction p=0.56; retention test two weeks later p=0.602.
- **Limits:** none on the page; it is internally inconsistent about the circle unit and Unit 6 (gatherer).

### 4.3 Matayoshi, Cosyn, Uzun & Kurd-Misto, ALEKS mastery-threshold experiment
- **Cite:** Matayoshi, Cosyn, Uzun, Kurd-Misto. Using a randomized experiment to compare mastery learning thresholds (title as recorded). JEDM (2025 per EVID/SRS notes). https://jedm.educationaldatamining.org/index.php/JEDM/article/download/900/254 [FT]
- **Studied:** ALEKS topics, data April 2023 to November 2024. From April 2023 each topic start was randomly assigned the high threshold (score 5) 5% of the time and the low threshold (score 3) 5% of the time.
- **Method:** compare outcomes by threshold: Learn / Fail (five consecutive wrong) / Incomplete / No response, duration, and retention on later extra problems.
- **Results:** Table 2 (about 33M data points; Learn / Fail / Inc. / No resp.; duration mean/median minutes): High (16,441,259) 0.789 / 0.024 / 0.073 / 0.115; 6.6 / 3.2. Low (16,474,845) 0.809 / 0.022 / 0.059 / 0.110; 5.1 / 2.4. Learning-ratio gap about 0.02 against an overall 0.80. Retention analysis: 1,404,725 extra-problem data points from 806,279 students; differences mostly 0.02 or less and narrowing with time; retention about 0.6 after several weeks. Starting with a wrong answer: difference over 0.04 at its maximum; starting correct: consistently under 0.02. Multilevel model: topic-level mean and median difference 0.021 (5th/95th percentiles 0.011 and 0.032); correlation with the topic's retention under the low threshold r = -0.86. Agrees with the earlier regression-discontinuity study (Matayoshi 2022: about 0.03 at first week, "has largely disappeared").
- **Limits:** vendor-run (gatherer). The paper cites Kelly et al. and Cen et al.

### 4.4 Zhang, Vanacore, Baker, Ch, Mills & Henkel 2025
- **Cite:** Zhang et al. (2025). How much mastery is enough mastery? EDM 2025 short papers. https://educationaldatamining.org/edm2025/proceedings/2025.EDM.short-papers.4/2025.EDM.short-papers.4.pdf [FT]
- **Studied:** Rori WhatsApp math tutor, logs September 2023 to May 2024: 5,039 micro-lessons from 543 students, 49,612 problems.
- **Method:** BKT fitted per micro-lesson (brute force, constrained against degeneracy); next-lesson accuracy by mastery level at the end of the previous lesson.
- **Results:** Next-lesson (N+1) accuracy / early-knowledge estimate / final-knowledge estimate, by mastery level P(Ln) at the end of lesson N: 0.9-0.95 (129 micro-lessons) 0.66 / 0.50 / 0.75; 0.95-0.98 (229) 0.69 / 0.56 / 0.77; 0.98 or above (4,140) 0.83 (sd 0.22) / 0.66 / 0.91. The paper reports the 0.98-or-above group as significantly higher on next-lesson accuracy.
- **Limits:** correlational; selection plausible; "over-practice identified by [8] may not be over-practice at all".

### 4.5 Xia, Schmucker, Borchers & Aleven 2025
- **Cite:** Xia, Schmucker, Borchers, Aleven (2025). Optimizing mastery learning by fast-forwarding over-practice steps. arXiv 2506.17577 [FT, brief]
- **Studied / Method:** APTA equation-solving DataShop data; simulated fast-forwarding of over-practice steps.
- **Results:** reduces over-practice by up to one-third; effect larger for algorithms that choose difficult problems.
- **Limits:** simulation, not an experiment (gatherer).

### 4.6 Käser, Yudelson, Fancsali (not retrieved)
Only secondary mentions seen (in 1.2, 1.7, 1.1): Yudelson & Koedinger 2013 (small predictive differences give 7-20% over- and under-practice); Fancsali et al. 2013 (BKT threshold simulations of premature mastery and over-practice); Käser et al. 2016 ("when to stop" criteria by practice opportunities). UNVERIFIED.

---

## 5. Model-based spaced review with experimental tests

Existing coverage: SRS `papers_annotated.md` (#1, #2, #6, #8-#11, #13, #18, #19) and `verifying_srs.md`. Items below that say NOTE are relayed from there or from EVID.

### 5.1 Lindsey, Shroyer, Pashler & Mozer 2014
- **Cite:** Lindsey, R.V., Shroyer, J.D., Pashler, H., Mozer, M.C. (2014). Improving students' long-term knowledge retention through personalized review. Psychological Science 25(3):639-647, doi 10.1177/0956797613504302. https://scottbarrykaufman.com///wp-content/uploads/2014/01/Lindsey-et-al.-2014.pdf [FT]
- **Studied:** 179 8th-grade Spanish students (third semester), COLT software for a semester, about 30 minutes a week (about 10% of course time).
- **Method:** within-student: one third of each chapter's items to massed, generic spaced and personalized spaced (DASH, hierarchical Bayesian) review, with equal review trials. Cumulative proctored exams (half the items each) at semester end and 28 days later.
- **Results:** Exam 1: personalized beats massed by +12.4% (d=1.38) and generic by +8.3% (d=1.05). Exam 2: +16.5% over massed (d=1.42) and +10.0% over generic (d=0.88). Forgetting over the 28-day break: 18.1% massed, 17.1% generic, 15.7% personalized.
- **Limits:** personalization is confounded with the coarse temporal distribution of review; uncontrolled outside exposure; declarative Spanish items. The paper describes Pavlik & Anderson 2008 as "three study sessions in 1 week and a test the following week".

### 5.2 Pavlik & Anderson 2008 (not retrieved)
Pavlik, P.I., Anderson, J.R. (2008). Using a model to compute the optimal schedule of practice. J Exp Psychol: Applied 14(2):101-117. Fetch failed. [NOTE] SRS `papers_annotated.md` #13 records "large effect sizes" (abstract level); same file records Eglington & Pavlik 2020 (N=291; thresholds .40/.70/.86/.94/.98; mean recall about .47-.48; test after 3 days; d=0.64 over conventional spacing).

### 5.3 Khajah, Lindsey & Mozer 2014 (not retrieved)
Khajah, M.M., Lindsey, R.V., Mozer, M.C. (2014). Maximizing students' retention via spaced review: practical guidance from computational models of memory (title from memory; UNVERIFIED). Fetch refused (robots.txt). Content UNVERIFIED.

### 5.4 Tabibian et al. 2019 (MEMORIZE) and Upadhyay et al. 2021 [NOTE]
SRS `papers_annotated.md` #9: PNAS 116(10):3988-93; about 5.2M Duolingo pairs; natural experiment; top 25% by likelihood; effort ratios 0.00-0.07 and forgetting-rate ratios 0.10-0.22 vs uniform and threshold schedules; no intervention. #10: Upadhyay et al. 2021, npj Science of Learning 6:26; RCT in a German driver's-permit app; select n=10,151, difficulty n=34,029, random n=13,600; about 16.75M answers; lower empirical forgetting rate in 83.5% of strata; median reduction about 48% vs random and about 40% vs difficulty; outcome is in-app forgetting.

### 5.5 Reddy et al. 2016 (KDD) [NOTE]
SRS `papers_annotated.md` #8: Mnemosyne logs, 2,742 users and 88,892 items; Leitner system as a queueing network with a phase transition; MTurk 331 workers and 446 items.

### 5.6 Ye, Su & Cao 2022 (SSP-MMC) and Su et al. 2023 [NOTE]
SRS `papers_annotated.md` #1, #2: 220M MaiMemo logs. Simulation (6000 items, 600 s/day, 1000 days), days to master: SSP-MMC 466, 80%-threshold 533, SM-2 variant 569, MEMORIZE 793. TKDE paper: saves about 12.5% vs MEMORIZE and 16.8% vs threshold. Simulated on the authors' own model.

### 5.7 Hunziker et al. 2019 (NeurIPS) [NOTE]
SRS `papers_annotated.md` #11: adaptive greedy teacher; MTurk, one 25-minute session, 15 concepts, 40 steps. German (80 people) gain 0.572 vs 0.487 (lowest-recall-first; p=0.065); Biodiversity (320) 0.475 vs 0.411.

### 5.8 Settles & Meeder 2016 (HLR) [NOTE]
SRS `papers_annotated.md` #6: MAE 0.128 vs Leitner 0.235; AUC weak (0.538 vs 0.542); A/B tests measured engagement only.

### 5.9 FSRS-author minimum recommended retention (CMRR) and related [NOTE]
SRS `verifying_srs.md` (line 71): above 90% desired retention workload "increases very quickly"; above 97% "can be overwhelming"; "Compute minimum recommended retention" removed in Anki 25.07. EVID: one user's minutes/day by desired retention: 19.8 (70%), 31.1 (79%), 45 (85%), 57.2 (88%), 76.2 (91%), 114.5 (94%), 230.3 (97%). SRS `papers_annotated.md` #18, #19 (Schill 2026; MaiMemo A/B): realized retention about 75% vs 85% target.

---

## 6. Randomized and large-scale adaptive-math evaluations

### 6.1 Pane, Griffin, McCaffrey & Karam 2014 (Cognitive Tutor Algebra I)
- **Cite:** Pane, J.F., Griffin, B.A., McCaffrey, D.F., Karam, R. (2014). Effectiveness of Cognitive Tutor Algebra I at scale. Educational Evaluation and Policy Analysis 36(2):127-144, doi 10.3102/0162373713507480. WWC page https://ies.ed.gov/ncee/WWC/Study/82101 [WF]
- **Studied:** matched-pair school randomization, 2 years. Per Sales & Pane (arXiv 1707.09308, FT): blocked cluster randomized design, 74 middle schools and 73 high schools, 52 districts, 7 states, nearly 18,700 high school students.
- **Results:** High school effect (95% CI half-width): -0.10±0.2 SD in year 1 and 0.22±0.2 in year 2. Middle school: -0.03±0.2 and 0.19±0.3. Abstract: no first-year effect; positive second-year effect, about 8 percentile points for the median student; significant for high schools only. WWC page: high school N 5,328 (year 1) and 5,738 (year 2); means -0.02 vs 0.03 and 0.08 vs -0.08, not significant. Israni, Sales & Pane (arXiv 1802.08616): about 85% of worked sections mastered (except Connecticut); 13-15% of sections ended in promotion (except Texas about 3% and Connecticut 5%); 18 treatment schools, 4,460 students; reassignment out of sections appears to lower post-test. Sales & Pane: the tutor may be more effective for frequently promoted students; causal attribution unclear.
- **Limits:** WWC ratings and the state lists conflict across the RAND, WWC and Sales & Pane pages (gatherer).

### 6.2 Roschelle, Feng, Murphy & Mason 2016 (ASSISTments)
- **Cite:** Roschelle, J., Feng, M., Murphy, R.F., Mason, C.A. (2016). Online mathematics homework increases student achievement. AERA Open, doi 10.1177/2332858416673968. https://journals.sagepub.com/doi/10.1177/2332858416673968 [WF]
- **Studied:** Maine 7th grade; 43 analyzed schools (46 recruited); 2,850 students (1,621 treatment, 1,229 control).
- **Results:** TerraNova Common Core math, adjusted difference 8.84 points, Hedges' g = 0.18, t(20)=2.992, p=.007. Low prior achievers 13.35 points (g=0.29 in text, 0.10 in Table 4: inconsistent); high prior achievers 5.84 (g=0.12 in text); interaction p=.015. Average use 967 problems and 14 hours a year; attrition 10.1% (5.6% differential). North Carolina replication (Arnold Ventures page, WF): 63 schools, 9,073 students, 2019-20; 0.10 SD (p=0.01) on the 8th-grade state test a year after the program; suggestive (p<0.10) larger impact for higher performers.
- **Limits:** Maine laptops, rural, one warm-up year, components not separable.

### 6.3 Fang, Ren, Hu & Graesser 2019 (ALEKS meta-analysis)
- **Cite:** Fang, Y., Ren, Z., Hu, X., Graesser, A.C. (2019). A meta-analysis of the effectiveness of ALEKS on learning. Educational Psychology 39(10):1278-1292, doi 10.1080/01443410.2018.1495829. https://digitalcommons.memphis.edu/facpubs/7254 [WF, abstract]
- **Results:** 15 studies (2005-2015), 24 independent samples; ALEKS "as good, but not better than" traditional teaching; no moderator differences by school level, implementation or outcome type; shorter use gave larger effects. Overall g not on the page. Vendor figures [NOTE] PRAC `practice_platforms.md` §2: in-state items answered correctly 74-84% vs about 10-11% out-of-state; AUROC 0.863-0.889.

### 6.4 Khan Academy
- **Cite:** Khan Academy efficacy blog https://blog.khanacademy.org/?p=18194 [WF]
- **Studied:** vendor-run, observational; about 350K students in grades 3-8, MAP Growth, 2022-23.
- **Results:** 30+ min/week (18+ hours) "associated with ~20% greater-than-expected learning gains", effect size .36; about 9% (~33K) reached it; 9-18 hours about 7%. A longitudinal sub-sample of about 221K is called "quasi-experimental". [NOTE] PRAC `practice_platforms.md` and `Toishi full evidence review/ai_tutors_and_study_tools.md`: NBER w35620 RCT, Hamilton County, 18 middle schools, about 0.06-0.08 SD per year; Khanmigo used in 17% of mistake sessions (UNVERIFIED here).

### 6.5 Math Academy
Hecker blog (https://frankhecker.com/2025/02/09/math-academy-part-2/ [WF]) cites no studies and notes a selection effect. justinmath.com success stories [WF]: anecdotes, n=1 to 4, a "4x as efficient" internal claim with no data. No independent evaluation found.

---

## 7. Problem difficulty and adaptive-selection measurement

Selection-bias material is in 1.1, 1.2 (§6.3), 1.3, 1.5 and 1.6; item 7.9 points to it.

### 7.1 Wilson, Shenhav, Straccia & Cohen 2019, "Eighty Five Percent Rule"
- **Cite:** Wilson, R.C., Shenhav, A., Straccia, M., Cohen, J.D. (2019). The Eighty Five Percent Rule for optimal learning. Nature Communications 10:4646, doi 10.1038/s41467-019-12552-4. https://www.nature.com/articles/s41467-019-12552-4 [FT]
- **Studied:** simulated learners, not humans: binary classification by stochastic-gradient-descent learners with Gaussian noise.
- **Method:** derive the training error that maximizes the learning rate; validate by simulation: a Perceptron (1000 simulations × 1000 trials per error rate 0.01-0.5); a two-layer network on MNIST parity and magnitude tasks (5000 trials, error clamped 5-30%, 1000 repeats, about 10% test-accuracy range); the Law & Gold model of monkey perceptual learning.
- **Results:** optimal training error 15.87% (accuracy about 85%). The optimum is constant over precision, so clamping the error rate is optimal. Noise sensitivity: optimal accuracy 85% (Gaussian), 82% (Laplacian), 75% (Cauchy). No human experiment. Staircasing procedures are "commonly designed to produce about 80-85% accuracy".
- **Limits:** not all models show a sweet spot (a Bayesian learner with perfect memory learns equally regardless of order); extension to multi-category tasks, batch training and other algorithms needed. Notes: FSRS (Q7) says untested on humans; EVID cites the bioRxiv preprint.

### 7.2 Papoušek & Pelánek 2015, adaptive behaviour and motivation
- **Cite:** Papoušek, J., Pelánek, R. (2015). Impact of adaptive educational system behaviour on student motivation. AIED 2015, LNCS 9112:348-357. https://www.fi.muni.cz/~xpelanek/publications/aied15.pdf [FT]
- **Studied:** slepemapy.cz randomized multivariate tests; in-school users (about 20% of data) separated.
- **Results:** Experiment 1: adaptive-both median 33.0 answers vs 20.0, 20.0, 19.5 (p<0.01; p=0.06 vs fully random, which had 26 students). Experiment 2 (target success probability 50-95%): no significant trend in answers; actual success only 65-90%; self-reported appropriateness peaks at 65% real success (in-school about 75%; more than 1,700,000 answers, 12,000 feedback records); satisfaction highest for target 60-65% (about 70% real). Dynamic adjustment: median answers 28 vs 21 (p=0.02); "Appropriate" votes 68% vs 63%. The paper states that in computerized adaptive testing the optimal success rate is 50%; its default target was 75%. Cites Lomas (monotone) and Jansen et al. (7.5).
- **Limits:** no learning outcomes measured.

### 7.3 Papoušek, Stanislav & Pelánek 2016, question difficulty RCT
- **Cite:** Papoušek, J., Stanislav, V., Pelánek, R. (2016). Impact of question difficulty on engagement and learning. Short paper; venue not stated in the PDF (ITS 2016 by recollection; UNVERIFIED). https://www.fi.muni.cz/~xpelanek/publications/its-target-difficulty.pdf [FT]
- **Studied:** slepemapy.cz RCT, Nov 2015-Jan 2016, almost 3,300,000 answers, about 37,000 learners; target error rates 5%, 20%, 35%, 50% (C5/C20/C35/C50); every 10th question is a random reference question.
- **Results:** Survival after 10 answers: 89.2 / 87.0 / 84.0 / 81.2% (±0.77%); after 100 answers 26.0-26.5%. Return rate after more than 10 hours: C5 15.2%, C20 16.0%, C35 16.6%, C50 16.8% (±0.75%). Learning-curve rate k (power law a·x^-k): harder is better, mostly C5 vs the rest. C35 and C50 stop reaching their targets after about 30 questions. Authors: short-term engagement favors easy; long-term engagement and learning favor hard; this differs from Lomas and Jansen (math); domain is declarative geography.
- **Limits:** none beyond the authors' domain caveat above.

### 7.4 Lomas, Patel, Forlizzi & Koedinger 2013
- **Cite:** Lomas, D., Patel, K., Forlizzi, J.L., Koedinger, K.R. (2013). Optimizing challenge in an educational game using large-scale design experiments. CHI 2013, pp. 89-98. https://www.stat.cmu.edu/~brian/463-663/project-part-one/Optimizing%20Challenge.pdf [FT]
- **Studied:** Battleship Numberline (number-line estimation game); two multi-factor experiments (about 10K and about 70K subjects; 10,478 and 69,642 play sessions).
- **Results:** Easier is more engaging: largest target 63% success vs smallest 29%; 34% more estimates and 18% more time; no quadratic fit (p=0.8). Learning: 1,392 players, first 30 trials, larger targets slower learning (p=0.02).
- **Limits:** authors suggest that perhaps they "never made the game easy enough" (easiest conditions below 70% success).

### 7.5 Jansen et al. (Math Garden) [NOTE / secondary]
Cited by Papoušek & Pelánek 2015 and 7.3: target success rates 60%, 75%, 90%; the easiest condition gave the best learning, mediated by number of problems. EVID records 207 children, 6 weeks. Primary NOT retrieved.

### 7.6 Published target rates of platforms
- ALEKS: initial-assessment questions target an item with likelihood near 0.5 of being in the student's knowledge state (EVID line 437). The 5 and 3 scores in 4.3 are mastery thresholds, not difficulty targets.
- Math Academy: PRAC `practice_platforms.md` (line 36, from a Math Academy FAQ per the note) records quiz difficulty "tougher if you've been doing well... because the 80-85% accuracy range is the sweet spot for learning", and says no evidence tests it (line 65); FSRS (line 225) says "Math Academy publishes no success-rate target" on its pedagogy page. The notes may refer to different things (quizzes vs practice). Math Academy's own pages not re-read.
- Duolingo / Birdbrain: exercises chosen "at the right difficulty"; Duolingo claims A/B gains with no effect sizes or target rate in the note (PRAC `skill_trainers_and_srs_apps.md`, line 79; see also SRS `skills_not_cards.md`).
- Khan Academy: no target rate found.
- Slepemapy.cz (research system): 75% default target (7.2); 20% error in the 7.3 RCT.

### 7.7 Metcalfe & Kornell, region of proximal learning
- **Cite:** Metcalfe, J., Kornell, N. (2003). The dynamics of learning and allocation of study time to a region of proximal learning. J Exp Psychol: General 132(4):530-542. https://psychology.columbia.edu/sites/psychology.columbia.edu/files/2016-11/530.pdf [FT]
- **Studied:** Experiment 2: N=12 Columbia students; English-Spanish pairs rated easy/medium/difficult; 10 s emphasized vs 1 s unemphasized per pair.
- **Results:** Proportion recalled: emphasize-medium 0.32, emphasize-easy 0.27, emphasize-difficult 0.25; F(2,22)=4.39, ES=.29; only medium vs difficult significant (Tukey). Experiment 1: free choice favored medium and easy items. Related (not re-summarised): Metcalfe 2002, JEP:General 131(3):349-363, five experiments (experts including Grade 6 children studied harder items than novices) https://psychology.columbia.edu/sites/default/files/2016-11/349.pdf; Metcalfe & Kornell 2005, JML 52:463-477, eight experiments (judgments of rate of learning to decide when to stop) https://psychology.columbia.edu/sites/default/files/2016-11/Metcalfe.Kornell.2005_0.pdf [FT].
- **Limits:** (gatherer) declarative vocabulary; small N.

### 7.8 Desirable difficulties (Bjork) [NOTE only]
Bjork's own papers NOT retrieved. Effect sizes seen only via notes: Soderstrom & Bjork 2015, performance during training is an unreliable index of learning (EVID; `Toishi gaps research/speed_mastery_goals.md`). Rohrer & Taylor 2007: blocked practice 89% in practice vs 60% mixed, but 20% vs 63% at test (d=1.34) (PRAC `science_of_practice.md`; EVID). Donoghue & Hattie 2021: 242 studies, 1,619 effects; overall 0.56, distributed 0.85, practice testing 0.74, interleaved 0.47 (same two notes). Eglington & Pavlik 2020: d=0.64 over conventional spacing (SRS `papers_annotated.md`; EVID; FSRS).

### 7.9 Cognitive load and too-hard practice for novices
- **Cite:** Alfieri, L., Brooks, P.J., Aldrich, N.J., Tenenbaum, H.R. (2011). Does discovery-based instruction enhance learning? J Educ Psychol 103(1):1-18, doi 10.1037/a0021017. https://www.fisme.science.uu.nl/publicaties/literatuur/2011_alfieri_discovery_learning.pdf [FT]
- **Studied:** meta-analysis, 164 studies.
- **Results:** unassisted discovery vs explicit instruction: 580 comparisons from 108 studies, d = -0.38 (95% CI -0.44 to -0.31). Enhanced/assisted discovery vs other instruction: 360 comparisons from 56 studies, d = 0.30 (0.23 to 0.36). Feedback, worked examples, scaffolding and elicited explanations helped.
- **Limits:** (gatherer) an indirect proxy for cognitive load; it does not test problem success rate.
- **Notes only [NOTE]:** worked-examples meta-analysis g about 0.43-0.48 (Barbieri et al.: 43 articles, 55 studies, 181 effects); AlgebraByExample RCT (more than 6,000 students, 130 teachers); productive failure g = 0.36 (53 studies, 166 comparisons); Rowland 2014 testing effect g = 0.03 at 50% or lower initial success and 0.56 above 75% (no feedback), 0.73 with feedback (PRAC `science_of_practice.md`; EVID; FSRS). Sweller, Kalyuga and Kirschner primaries NOT retrieved; no direct test of "too-hard problems reduce novice learning" found.

### 7.10 IRT item information and adaptive-testing targets
- **Cite:** Baker, F.B. (2001). The Basics of Item Response Theory, ch. 6. ERIC ED458219, https://files.eric.ed.gov/fulltext/ED458219.pdf [OCR of a scanned PDF, pp. 117-125]; Newsom, IRT handout, https://web.pdx.edu/~newsomj/cdaclass/ho_irt.pdf [FT, 2025].
- **Results:** 2PL item information I = a²PQ, symmetric about b; with a=1.5, b=1.0 the maximum is 0.56 at theta=1.0 (P=Q=0.5). Rasch: I = PQ (a=1), maximum 0.25. 3PL with c=0.2 (same a, b) gives less information: at theta=0 it is .142 vs .34 under 2PL, and the maximum occurs "slightly higher than the value of b" (P=0.60 at theta=1.0, I=.375). Test information is the sum of item informations.
- **Limits:** (gatherer) information concerns measuring ability, not learning gain. No primary CAT target-probability source retrieved; the 50% statement is secondary (7.2).

### 7.11 Adaptive selection and parameter bias: where covered
Adaptive item choice shrinks model differences and makes naive baselines competitive (1.5; 1.3 adaptive 75% example). Mastery attrition and trace length shift fitted BKT parameters (1.3; 1.5; 2.2; 2.5). Counters reported: controlled randomization (1.5), random reference questions every 10th question (1.6; 7.3), filtering or capping answers per learner (1.1), random-order or random-condition RCT assignment (1.6). Not retrieved: Nižnan et al. 2015; Mandel et al. 2014.

---

## Could not find or verify

- Primaries not retrieved: Beck & Chang 2007; Cen et al. 2007 (only the LearnLab wiki, no authors or N); Pavlik & Anderson 2008; Khajah et al. 2014; Käser, Yudelson and Fancsali papers; Nižnan et al. 2015; Jansen et al. 2013 (specific rates); Bjork's own papers; Sweller / Kalyuga cognitive-load primaries; Mandel et al. 2014; any primary CAT target-probability source.
- Items 5.4-5.9 and the Khan RCT rest on existing notes, not re-verified.
- "Where's the reward?": 36 vs 41 denominator mismatch inside the paper; which is intended is UNVERIFIED.
- No independent Math Academy evaluation; no published target success rates found for Duolingo, Khan or ALEKS (ALEKS only the 0.5 assessment target). Two repo notes differ on whether Math Academy states a number.
- Khan Academy and ALEKS threshold evidence is vendor-run; Fang et al. overall g is not on the page read.
- Pane 2014: state lists and WWC ratings conflict across pages.
- Roschelle 2016: subgroup effect sizes inconsistent (0.29 vs 0.10).
- Kelly 2015: N not stated; sample sizes inconsistent.
- Papoušek et al. 2016 short paper: venue not stated in the PDF.
- Baker 2001 text is OCR of a scanned PDF.
- No human experiment of the 85% rule found; no direct cognitive-load test of success rate found.
- Search budget was exhausted, so sources not already fetched were not pursued.
