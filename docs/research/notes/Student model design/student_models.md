# Student model sources: what the literature says

Gathered 2026-11-02 for Toishi. Reporting only; no design recommendation. Tags: [FT] full text read; [IMG] equations read from page images; [SRC] package source read; [OCR] scanned patent, OCR plus image check; [AB] abstract or metadata only; [EX] existing note, cited not re-gathered. Existing notes: SK = `Spaced repetition algorithm gap audit/skills_not_cards.md`; PA = `Spaced repetition algorithm gap audit/papers_annotated.md`; SM = `Toishi build research/scheduling_and_skill_modeling.md`. Notation: σ(x) = 1/(1+e^−x).

## 1. AFM, Learning Factors Analysis (LFA), automated KC-model improvement

**Citation and link.** Cen, Koedinger & Junker (2006), "Learning Factors Analysis", ITS 2006, LNCS 4053:164-175 [not retrieved]. Read instead the 2005 workshop version, "Automating Cognitive Model Improvement by A*Search and Logistic Regression", https://learnlab.org/wp-content/uploads/2025/07/CenKoedinger-Junker-05pdf.pdf [FT]. Koedinger, McLaughlin & Stamper (2012), "Automated Student Model Improvement", EDM 2012, pp. 17-24, ERIC ED537074 [FT]. Effenberger, Pelánek & Čechák (2020), LAK '20, doi 10.1145/3375462.3375491 [FT]. Lee et al. (2026), L@S '26, arXiv 2605.01690 [FT].

**What it models.** P(correct) on a problem step from student proficiency, KC easiness, and KC learning rate times prior opportunities. Multi-KC steps sum KC terms (compensatory). LFA searches Q-matrices (step-to-KC maps), scoring each with AFM.

**Equations.** Effenberger et al.: P(Y_ij=1) = σ(α_i + Σ_k β_k q_jk + Σ_k γ_k q_jk t_ik); q_jk = 1 if step j uses KC k; t_ik = student i's prior opportunities on k. 2005 paper: ln[p/(1−p)] = β0 + α_j + Σβ_j x_ij + Σγ_j x_ij t_ij. LFA operators: split, merge, add, driven by a P matrix of candidate factors; best-first search ranked by AIC or BIC.

**Parameters.** α_i per student (regularized); β_k and γ_k per KC; total N_students + 2K. No item term, no success/failure split, no time or forgetting.

**Fitting.** Penalized logistic regression, regularization on α [Effenberger]. 2012 LFA: split operator only; start with one KC for all steps; P matrix = union of all KC models already in DataShop; stop after 5 iterations without gain; runs with AIC and with BIC; the 4 best models compared with existing models by 10-fold CV (student-, item-, and non-stratified; item-stratified primary because it matches choosing the next problem).

**Data and results.** 2005: Geometry area, R² 0.149 to 0.174 for the best-found model. 2012: 11 DataShop datasets, 41-318 students, 1-48 KCs per model. Item-stratified RMSE, original-in-use / best-hand / best-LFA: Geometry9697 0.4129 / 0.4033 / 0.4011; fractions game 0.4442 / 0.4396 / 0.4346; Statistics-Fall09 0.3648 / 0.3527 / 0.3353. LFA best in 11 of 11 (item-stratified) and 10 of 11 (other folds). Gains concentrate in few KCs: Geometry9697 TRIANGLE-SIDE −11.1% RMSE, CIRCLE-RADIUS −9.5%, other 12 KCs −0.2% to 3.1%. Lee et al. 2026: the "astonishing regularity" of learning rates (iAFM, 27 datasets, ~7,000 learners) depends on which observations are fit; learning-rate variation inflates by a median 118% under one rule, several-fold under another.

**Code and license.** AFM runs inside PSLC DataShop (code license UNVERIFIED). AFM terms are reproduced in LKT (GPL-3, `lineafm`) and KTM (MIT, "skills, attempts", d=0). No LFA code found.

**Stated limitations.** Effenberger et al.: one-dimensional student skill and equal learning rates for all; all practice equal regardless of outcome; linear learning on the logit scale; binary outcomes and item-skill links; compensatory skills; item difficulty ignored; no handling of bias such as mastery attrition. Koedinger 2012: add operator dropped because LFA "ran for multiple days", so multi-KC steps cannot be produced; P matrix needs human-coded factors; CV too slow inside the search; overall RMSE gains small. R-PFA authors: prior successes alone beat AFM, which "casts doubt" on AFM for model search.

## 2. Conjunctive Factor Model (CFM) vs AFM

**Citation and link.** Cen, Koedinger & Junker (2008), "Comparing Two IRT Models for Conjunctive Skills", ITS 2008, LNCS 5091:796-798, doi 10.1007/978-3-540-69132-7_111, https://link.springer.com/chapter/10.1007/978-3-540-69132-7_111 [AB; the PDF link returned a paywall page].

**What it models.** Abstract: "a step requiring a conjunction of skills is harder than steps that require requiring [sic] each individual skill only"; AFM and CFM are the two item-response models compared.

**Equations, parameters, fitting.** UNVERIFIED (full text not retrievable). Context from other papers [FT]: the PFA paper says LFA "models conjunction by summing the contributions from all KCs" and KT handled multi-KC steps "by multiplying the probabilities".

**Data and results.** Abstract only: compared on simulated data and one real assessment dataset. "CFM was as good as or better than AFM in the mean cross validation errors on the simulated data. In the real data set CFM is not clearly better. However, AFM is essentially performing as a conjunctive model."

**Code and license.** None found.

**Stated limitations.** None beyond the abstract (3-page paper).

## 3. PFA and recent-performance variants

### 3a. PFA (Pavlik, Cen & Koedinger 2009)

**Citation and link.** AIED 2009 (Brighton), pp. 531-538, ERIC ED506305 [FT].

**What it models.** AFM without the student term, with separate success and failure counts, so predictions adapt to each student's own responses. Multi-KC steps sum KC terms.

**Equations.** m(i, j∈KCs, s, f) = Σ_{j∈KCs} (β_j + γ_j s_ij + ρ_j f_ij) (Eq. 3); p(m) = 1/(1+e^−m).

**Parameters.** β_j, γ_j, ρ_j per KC (3 per KC); no student or item parameter; s and f are prior success and failure counts.

**Fitting.** Maximum log-likelihood (ordinary logistic regression), γ ≥ 0. KT comparison split multi-KC steps into single-KC rows. KT1: Beck and Leszczenski code adapted by Cen; KT2: Baker's exhaustive search minimizing SSE. KT bounds: slip ≤0.1, guess ≤0.3; predictions clipped to [0.01, 0.99] for LL.

**Data and results.** Physics (Andes), Geometry, Algebra, Fractions (Carnegie Learning tutors). Table 2 (PFA vs LFA, which has a student term; "LFA ns" lacks it): PFA ties or beats LFA only on Fractions (BIC 7.287E+4 vs 7.377E+4; 7-fold MAD 0.207 vs 0.208); elsewhere LFA is better by BIC (Physics 4.627E+4 vs 4.797E+4) with MAD close (0.340 vs 0.346; LFA ns 0.349). Authors: PFA picks up individual differences "nearly as effectively as a subject parameter". Table 3 (held-out status not stated, UNVERIFIED):

| Data | Par KT / PFA | A' KT1 / KT2 / PFA |
|---|---|---|
| Physics | 752 / 564 | .708 / .705 / .719 |
| Geometry | 480 / 360 | .660 / .667 / .685 |
| Algebra | 552 / 414 | .687 / .692 / .711 |
| Fractions | 256 / 192 | .706 / .692 / .723 |

PFA also had the highest correlation r and better LL and BIC in all four. Explanation offered: KT reacts too sharply to one failure.

**Code and license.** None released with the paper (UNVERIFIED). Reproduced in LKT (GPL-3, `linesuc`/`linefail`) and KTM (MIT, "skills, wins, fails").

**Stated limitations.** No student parameter (LFA's captures slightly more student variability; adaptive estimation suggested as future work); BIC values "suggest overfitting" yet 7-fold MAD "shows the model generalizes well"; PFA uses counts only, whereas KT "results in different predictions depending on the order of practice"; no forgetting or time term (structural, not stated).

### 3b. R-PFA (Galyardt & Goldin 2015) and decay variants

**Citation and link.** Galyardt & Goldin, "Move your lamp post: Recent data reflects learner knowledge better than older data", JEDM 7(2):83-108. Text read: arXiv 1501.02732v1, "Predicting Performance During Tutoring with Models of Recent Performance" [FT]; published-version differences UNVERIFIED. PFA-decay: Gong, Beck & Heffernan (2011), IJAIED 21:27-46 [not read; fixed d=0.9 per R-PFA paper].

**What it models.** Whether recent history predicts better than full history. Adds a decay-weighted proportion of successes R with "ghost" initial failures.

**Equations.** PFA: logit(p_ijt) = θ_i + β_j + α_j S_ijt + ρ_j F_ijt. S_ijt = Σ_{p=1}^{t−1} d^{t−1−p} X_ijp; F_ijt = Σ d^{t−1−p}(X_ijp − 1) (as printed; the text calls F the decayed failure count). R_ijt = Σ_{p=−2}^{t−1} d^{t−p} X_ijp / Σ_{p=−2}^{t−1} d^{t−p}, with ghosts X_{ij,−2} = X_{ij,−1} = X_{ij,0} = 0. R-only: θ_i + β_j + δ_j R; R-PFA: θ_i + β_j + ρ_j F_ijt + δ_j R_ijt. d is a tuned constant per predictor.

**Parameters.** Best model: β_j, ρ_j, δ_j per KC (3 per KC), student θ_i as random effect, plus two decay constants ("only two tuning weights beyond the parameter structure of PFA").

**Fitting.** lme4 `glmer`, random effects for students and for KC intercepts and slopes; 111 models fit; decay grid 0.1-1.0. AIC used because data too sparse for CV.

**Data and results.** Assistments "moment of learning" data: 4,138 students, 54 KCs (one per item), 187,309 first attempts; 410 students per KC, median 4 attempts per student-KC. AIC only; no AUC, RMSE or log loss on real data. AIC order: PFA beats AFM; S-only with d=1 beats AFM; decayed S-only and R-only beat PFA; R equals S for d<0.3 and pulls ahead as d grows (d=0.9: R-only AIC 1,200 lower); best equal-decay PFA d=0.6; best overall R decay 0.7 with F decay 0.1. Best model: δ_j significantly positive for 49 of 54 KCs. Simulations (100 each from BKT, 3-state BKT, BKT with forgetting and slipping): R-PFA beat PFA and AFM in 100% of runs by AIC and L1-loss CV; best success decay 0.6-0.8.

**Code and license.** Authors link code and data (https://sites.google.com/site/aprilgalyardt/research; license UNVERIFIED). Features reappear in LKT as `propdec`, `propdec2`, `expdecfail` (GPL-3).

**Stated limitations.** Not compared with BKT; single-KC items only (multi-skill Q-matrices left for later); sparse student data forced AIC over CV; early attempts noisy.

## 4. Logistic Knowledge Tracing (LKT)

**Citation and link.** Pavlik, Eglington & Harrell-Williams, "Logistic Knowledge Tracing: A Constrained Framework for Learner Modeling", arXiv 2005.00869 [FT] (published venue UNVERIFIED). Package: https://cran.r-project.org/package=LKT, version 1.7.0 [SRC].

**What it models.** A notation for logistic regressions: terms are features of a component's history (KC, item, or student), each with one coefficient overall or per level (`$`). Student ability can be an intercept or an adaptive feature (`propdec`, `logitdec`) so new students need no fitted parameter. 25 features in Table I.

**Equations (LKT 1.7.0 source; `cor`/`icor` = prior correct/incorrect counts; p1..p4 nonlinear parameters).**
- `lineafm` = cor + icor; `logafm` = log(1 + cor + icor); `powafm` = (cor + icor)^p1; `recency` = rec^−p1 (rec = time since previous trial of the component; 0 if none)
- `expdec` = Σ v_i d^(w−i) over prior outcomes
- `propdec` = corv/(corv + incorv), each a d-decayed sum, plus 1 ghost success and 1 ghost failure (starts at .5); `propdec2` = Σ v d^(w−i) / Σ d^(w+2−i) (3 ghost failures; starts at 0)
- `logitdec` = log(corv/incorv), window capped at last 60 trials
- `base` = log(1 + cor + icor) × age^−p1 (age since first trial); `base2` scales between-session time by p2; `base4` multiplies by mean spacing^p3
- `ppe` = (cor + icor)^p1 × Tw^−(p2 + p3 × space); Tw = Σ w_i t_i, w_i = t_i^−p4 / Σ_j t_j^−p4, t_i = time since prior practice i; space = running mean over prior gaps of 1/ln(lag + e) (0 on first trial).

**Parameters.** One logistic coefficient per feature (per level with `$`) plus nonlinear parameters: 1 for `propdec`, `expdec`, `logitdec`, `recency`, `powafm`; 4 for `base4` and `ppe`. The 12 main models each use `propdecStudent` + `intercept$KC` + KC-level features (Table II).

**Fitting.** Coefficients by LiblineaR logistic regression (cost 512); nonlinear parameters by L-BFGS-B, bounds [1e-5, 0.99999], seeds 0.5, maxit 100 [SRC]. Evaluation: 100 student-stratified split-half holdouts, paired t-tests on per-subject RMSE. First attempts on first problem steps only; students ≥25 observations, KCs ≥600.

**Data and results.** Six datasets: statistics cloze (58,316 obs, 478 adults, 144 item-level KCs), Chinese tones (48,443 obs, 97 students, 5 KCs), Assistments (580,785 obs, 912 students), KDD Cup (120 of 574 students per run, ~39 KCs), Andes (66 students, 345,536 obs, 45 KCs), McGraw-Hill (124,387 obs, 1,047 adults, 111 KCs; unreleased). Held-out AUC:

| Model | Cloze | Tone | Assist | KDD | Andes | McGraw |
|---|---|---|---|---|---|---|
| 1 lineafmKC (AFM) | .818 | .698 | .715 | .731 | .732 | .717 |
| 5 logsuc+logfail+recency | .855 | .724 | .726 | .761 | .753 | .820 |
| 9 propdec+expdecfail (R-PFA-like) | .842 | .725 | .725 | .753 | .746 | .821 |
| 10 propdec+ppe | .857 | .724 | .726 | .768 | .762 | .823 |
| 12 propdec+base4 | .854 | .722 | .725 | .756 | .748 | .794 |

Authors: memory-feature models (10-12) beat decay-insensitive ones on cloze and McGraw-Hill (fact learning); for tones "simpler models that were insensitive to memory decay" sufficed; Assistments models 9-12 not significantly different; PPE best on Andes. Student-only McFadden R² (Table IV): intercept 0.035-0.080, `propdecStudent` 0.057-0.076; combining both added little ("highly colinear").

**Code and license.** GPL-3 (CRAN DESCRIPTION, 2024-07-01) [SRC]; GitHub Optimal-Learning-Lab/LKT; LearnSphere.

**Stated limitations.** Fits models given fixed KC and student groupings; random effects for intercepts only; student-level parameters avoided; no latency model, so "more suitable for mastery determination"; `base`, `base4`, `ppe` are hard-coded; transfer between KCs unmodeled (tones fit poorly); first attempts only because hints change what "correct" means.

## 5. Predictive Performance Equation (PPE)

**Citation and link.** Walsh, Gluck, Gunzelmann, Jastrzembski et al. (2018), "Mechanisms underlying the spacing effect in learning: A comparison of three computational models", J Exp Psychol Gen 147:1325-1348, doi 10.1037/xge0000416 [AB via Europe PMC; no full text found]. Earlier form: US Patent 8,568,145 B2, Jastrzembski et al., 29 Oct 2013 (US Air Force) [OCR + image]. Abstracts: https://mathpsych.org/presentation/1233 and /1223 [AB].

**What it models.** Performance as a power law of learning (N^c), a power law of forgetting (T^−d), and a practice-spacing term.

**Equations.** Patent: Performance = S · St · N^c · T^−d; St = ⌊(Σlag / P) · (P_i / T_i) · (Σ_i^j (lag_max_{i,j} − lag_min_{i,j}) / N_i)⌋. S scalar, c learning rate, d decay rate (free); T true time since training began, N number of training events, lag true time between events, P practice time accumulated. LKT `ppe`: section 4 (p1..p4 = c, b, m, x in the vignette). Whether either equals the Walsh 2018 specification is UNVERIFIED.

**Parameters.** Patent: S, c, d free. LKT: c, b, m, x (nonlinear) plus a regression coefficient, per KC with `$`. One fit in the LKT vignette (dataset not stated): c = 0.3491901, b = 0.2045801, m = 1e-05 (at the lower bound), x = 0.9734477.

**Fitting.** LKT as in section 4. Walsh 2018: UNVERIFIED.

**Data and results.** Walsh 2018 abstract: Japanese-English paired associates, massed vs spaced acquisition, retention intervals 1 to 21 days; spacing slowed acquisition, raised retention at test start and sped relearning; "Of the 3 models, only 1, the predictive performance equation (PPE), was consistent with the finding of spacing-accelerated relearning." LKT results: section 4. Sense et al. (ICCM 2023 abstract): "the full PPE performs best in experimental data but ... not much predictive accuracy is lost if the terms are omitted from the model when naturalistic data are concerned." Collins et al.: a "Change PPE" fit a naturalistic dataset better than standard PPE.

**Code and license.** In LKT (GPL-3). The patent covers an earlier "predictive performance optimizer"; US 8,777,628 (same title) not read; legal scope not assessed.

**Stated limitations.** Only what the abstracts say; full papers not read.

## 6. DASH and DAS3H

### 6a. DASH (Lindsey, Shroyer, Pashler & Mozer 2014)

**Citation and link.** Psychological Science 25(3):639-647, doi 10.1177/0956797613504302 [FT of author-hosted copy; online supplement with inference details not retrieved].

**What it models.** Student ability, item difficulty, and windowed counts of past correct and total attempts, as an additive-factors logistic model.

**Equations.** Pr(R_si=1 | D_s, G_i, φ, ψ) = σ[D_s − G_i + Σ_w φ_w log(1 + c_siw) − ψ_w log(1 + n_siw)] (Eq. 1; symbols as garbled in extraction); c_siw = correct recalls of KC i by student s in window w, n_siw = attempts in w; add-one smoothing. Windows (days) {1/24, 1, 7, 30, ∞}.

**Parameters.** D_s per student; G_i per item or KC; φ_w, ψ_w per window, shared (10).

**Fitting.** Bayesian inference of ability and difficulty; retrained periodically ("cycle time of retraining"); details in the supplement (not read).

**Data and results.** 179 middle-school Spanish students, one semester, 597,990 retrieval trials. Comparison on 100 temporally contiguous blocks by accumulative prediction error against proportion-correct, Bayesian IRT, the Pavlik & Anderson (2005) ACT-R model and DASH variants (numbers only in a figure). Field result on cumulative exams at semester end and 28 days later: personalized review +12.4% and +16.5% over massed, +8.3% and +10.0% over generic spaced (time-matched).

**Code and license.** DASH code not found.

**Stated limitations.** Time scales under one hour not encoded; few windows chosen to limit parameters; optimal scheduling intractable, so a threshold heuristic (T = .33 best in Khajah et al. 2013 simulations).

### 6b. DAS3H (Choffin, Popineau, Bourda & Vie 2019)

**Citation and link.** EDM 2019, arXiv 1905.06873 [FT, local copy `/home/claude/reference/papers/choffin2019_DAS3H_1905.06873.pdf`]. Best-d AUC table also in SK lines 70-75.

**Equations.** P(Y_{s,j,t}=1) = σ(α_s − δ_j + Σ_{k∈KC(j)} β_k + Σ_{k∈KC(j)} Σ_{w=0}^{W−1} [θ_{k,2w+1} log(1 + c_{s,k,w}) − θ_{k,2w+2} log(1 + a_{s,k,w})]); W=5 windows {1/24, 1, 7, 30, ∞} days; c = correct, a = attempts in window.

**Parameters.** α_s per student, δ_j per item, β_k per skill, 2W = 10 θ per skill. Stated count: (d+1)(K + 2W(K−1)) more feature parameters than DASH, d = embedding size.

**Fitting.** KTM framework: d=0 scikit-learn L2 logistic regression; d>0 libFM MCMC (Gibbs, 300 iterations) via pywFM with N(μ, 1/λ) priors, μ ~ N(0,1), λ ~ Γ(1,1). 5-fold student-level CV.

**Data and results.** assist12 (24,750 users, 52,976 items, 265 skills, 2,692,889 interactions), bridge06 (1,135; 129,263; 493; 1,817,427), algebra05 (569; 173,113; 112; 607,000). AUC at d=0, DAS3H / DASH / IRT / PFA / AFM: algebra05 .826 / .773 / .771 / .744 / .707 (NLL .414 vs .454 DASH); assist12 .739 / .703 / .702 / .668 / .608; bridge06 .790 / .749 / .747 / .739 / .692. Authors: time-window features beat plain wins and attempts counts; skill-specific θ beats one shared set by +0.03 to +0.04 AUC (bridge06 .790 vs .757, algebra05 .826 vs .789, assist12 .739 vs .701); d=20 vs d=0: bridge06 .776 vs .790, algebra05 .817 vs .826, assist12 .740 vs .739 (section 12: Gervet finds windows add nothing to Best-LR).

**Code and license.** https://github.com/BenoitChoffin/das3h; no LICENSE, LICENSE.md or LICENSE.txt on raw master; license UNVERIFIED.

**Stated limitations.** Few public datasets combine timestamps and multi-KC tags; additive form is compensatory ("explaining away"); window set fixed; not compared with R-PFA, PFA-decay, ACT-R, MCM; latency unused. SK: no ablation of the item term; student-level CV leaves unseen items untested.

## 7. Knowledge Tracing Machines (KTM)

**Citation and link.** Vie & Kashima (2019), AAAI-19, arXiv 1811.03388 [FT].

**What it models.** One factorization machine over a sparse vector of student, item, skill, success-count, failure-count and side-information features; generalizes IRT, AFM, PFA (and DAS3H).

**Equations.** ψ(p(x)) = μ + Σ_k w_k x_k + Σ_{k<l} x_k x_l ⟨v_k, v_l⟩ (Eq. 1), ψ a link (logit), v_k ∈ R^d. d=0 is logistic regression: IRT = "users, items"; AFM = "skills, attempts"; PFA = "skills, wins, fails". Loss: negative log-likelihood.

**Parameters.** Global bias μ; weight w_k per feature; embedding v_k (d numbers) per feature. Counters (wins, fails, attempts) are per skill.

**Fitting.** libFM MCMC (Gibbs) via pywFM; 1000 epochs (non-temporal sets), 500 (Assistments), 300 (Berkeley); 5-fold CV over entries (student-level split not stated; DAS3H says KTM used student-level folds).

**Data and results.** Six datasets: Fraction (536 users), TIMSS (757), ECPE (2,922), Assistments 2009-10 (4,217 users, 26,688 items, 123 skills, 346,860 entries), Berkeley (1,730 users, 234 items, 29 skills, 562,201 entries), Castor (58,939). ACC / AUC / NLL on Assistments: items+skills+wins+fails+extra d=20 .774 / .819 / .465 (d=0 .774 / .815 / .463); without extra, d=10 .727 / .767 / .539; IRT .675 / .691 / .599; PFA .68 / .685 / .604; AFM .653 / .616 / .631. Berkeley: items+skills+wins+fails d=20 .706 / .778 / .563; IRT .688 / .753 / .586; PFA .631 / .684 / .635; AFM .621 / .675 / .639. Findings: wins and fails over attempts +0.07 AUC (Assistments), +0.01 (Berkeley); item bias +0.07 and +0.09 over PFA; higher d adds under +0.01 AUC on temporal sets. "Extra" = first action, school id, teacher id, tutor mode. The d=0 model beat reported vanilla DKT (0.815 > 0.743) and trained in 4 min 30 s on CPU for 5 folds vs 1 hour for DKT.

**Code and license.** https://github.com/jilljenn/ktm, MIT (Vie, 2022) [verified]. libFM license UNVERIFIED.

**Stated limitations.** Few; the conclusion leaves open whether counters should be at item or skill level and defers response time and ordinal outcomes.

## 8. Bayesian Knowledge Tracing and variants with forgetting

**Citation and link.** Corbett & Anderson (1995), "Knowledge tracing: Modeling the acquisition of procedural knowledge", User Modeling and User-Adapted Interaction 4(4):253-278, doi 10.1007/BF01099821 [text not retrieved; bibliographic data from OpenAlex]. Khajah, Lindsey & Mozer (2016), "How Deep is Knowledge Tracing?", EDM 2016, arXiv 1604.02416 [FT].

**What it models.** Per KC, a hidden two-state learner. Parameters (PFA paper [FT]): L0 initial learning, T learning transition, G guess, S slip; no forgetting; one KC per step. Equations: see SM (pyBKT, arXiv 2105.00385, MIT; BKT+Forget AUC 0.83 on ASSISTments).

**Variants (Khajah).** Forgetting F = P(K_{s,i+1}=0 | K_{si}=1) (0 in classic BKT). BKT+A: slip and guess modulated by a latent student ability (stronger students: lower slip, higher guess). BKT+S: skill discovery via a weighted Chinese restaurant process prior on exercise-to-skill assignment. BKT+FSA: all three.

**Parameters and fitting.** 4 per KC (L0, T, G, S); +1 for F; one ability per student for A. BKT+ is C++ (WCRP); KT fitting in the PFA paper: section 3a.

**Data and results.** Khajah, test AUC: Assistments 2009-10 (Piech split) BKT .73 (Piech reported .67), BKT+F .83, DKT .86 (Piech); exercise-indexed labels give BKT+S and BKT+FSA .90. Statics (333 students, 189,297 trials) BKT+FSA .75, DKT .76. Spanish (182 students, 578,726 trials) BKT+FSA .846, DKT .836. "31.6% of difference ... due to the use of a biased procedure for computing the AUC for BKT. Another 50.6% ... vanishes if BKT is augmented to allow for forgetting." Gervet 2020: BKT .621 (algebra05), .631 (assist09), .732 (statics), .832 (spanish) from earlier papers; BKT+ .759 (assist09), .710 (assist17), .811 (statics), .851 (spanish), too slow on large sets ("orders of magnitude slower to train").

**Code and license.** BKT+ https://github.com/robert-lindsey/WCRP (branch `forgetting`), MIT (Lindsey, 2015) [verified]; pyBKT MIT [EX]; Khajah's DKT code https://github.com/mmkhajah/dkt (license not found).

**Stated limitations.** Khajah: classic BKT assumes a binary state, known skill labels, no forgetting over short spans; different extensions help different datasets; skill discovery adds cost. PFA paper: unbounded slip becomes implausibly high; one KC per step. R-PFA paper: BKT "notoriously can fail to return interpretable or accurate estimates of parameters".

## 9. Elo and IRT-based learner models

**Citation and link.** Pelánek, "Applications of the Elo rating system in adaptive educational systems" (Computers & Education; https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf) and PFAE (EDM 2015, https://www.educationaldatamining.org/EDM2015/proceedings/short480-483.pdf) [EX: SK lines 78-87]. IRT form from Lindsey 2014 [FT].

**What it models.** Online ability and difficulty estimates (Elo); P(correct) from ability minus difficulty (Rasch/IRT).

**Equations.** Elo (SK): θ += K(correct − P), d −= K(correct − P), K = a/(1+bn), a=1, b=0.05. Rasch (Lindsey): Pr(R_si=1 | D_s, G_i) = logistic(D_s − G_i); additive-factors extension logistic(D_s − G_i + Σ_j J_j m_sij).

**Parameters.** One ability per student, one difficulty per item; Elo adds global a, b.

**Fitting.** Elo: one online update per answer; approximates joint maximum likelihood for Rasch (SK). IRT in Gervet 2020: logistic regression.

**Data and results.** Per SK: about 100 students per item difficulty; about 10 answers per skill estimate (simulation r ~0.8); PFAE AUC 0.719 to 0.761; raw proportion correct fails under adaptive item selection. Gervet 2020 IRT AUC (student-level CV): assist09 .692, assist12 .713, assist15 .638, assist17 .681, algebra05 .768, bridge06 .749, spanish .679, statics .789, squirrel .733.

**Code and license.** Not checked.

**Stated limitations.** Gervet: student-level CV "does not do justice to IRT, as the student ability parameter is never fit"; Wilson et al. (2016) refit ability after every question, "which makes IRT significantly more competitive". SK: evaluations by student leave new items untested.

## 10. Half-life regression (HLR)

**Citation and link.** Settles & Meeder (2016), ACL 2016, pp. 1848-1858, P16-1174 [FT, local `/home/claude/reference/papers/settles2016_HLR_P16-1174.pdf`]. SK/PA #6 also cover results.

**What it models.** Recall probability decays as 2^(−lag/half-life); the half-life grows exponentially with practice features.

**Equations.** p = 2^(−Δ/h) (1); ĥ_Θ = 2^(Θ·x) (2); p̂_Θ = 2^(−Δ/ĥ_Θ); h = −Δ/log2(p); loss ℓ = (p − p̂_Θ)² + α(h − ĥ_Θ)² + λ‖Θ‖²₂.

**Parameters.** One weight vector Θ: counts of times seen, correct, incorrect (square roots worked better), bias, plus a sparse indicator per lexeme tag (word form); no per-student parameter.

**Fitting.** Gradient descent; λ = 0.1, α = 0.01, learning rate η = 0.001, tuned on the first 1 million instances.

**Data and results.** 12.9 million student-word traces from two weeks of Duolingo logs, first 90% train, last 10% test. MAE / AUC: HLR .128 / .538; HLR without lexeme tags .128 / .537; without half-life term .350 / .528; Leitner .235 / .542; Pimsleur .445 / .510; logistic regression .211 / .513; constant (p̄ = .859) .175. Live tests, change in daily retention (any activity / lesson / practice; * p < 0.001): I. HLR vs Leitner control, six weeks, just under 1 million students: +0.3 / +0.3 / −7.3*; II. HLR without lexeme tags vs HLR control, two weeks, 3.3 million students: +12.0* / +1.7* / +9.5*.

**Code and license.** https://github.com/duolingo/halflife-regression, MIT (Duolingo, 2016) [verified]; data and code from the offline evaluation released.

**Stated limitations.** AUC low partly from a noisy task and range restriction (p̄ = .859). Lexeme-tag indicators over-fit (words with large negative weights decayed fast regardless of practice) and have no data for new courses, hence HLR without tags; authors unaware of MCM and unsure its cost would scale; target is recall between sessions over long time scales, not within-session learning.

## 11. ACT-R declarative memory and the Pavlik & Anderson spacing extension

**Citation and link.** Pavlik & Anderson, "An ACT-R Model of the Spacing Effect", conference paper (gwern.net copy; venue and year not printed) [FT, equations from page images]. Pavlik & Anderson (2005), Cognitive Science 29:559-586, and (2008), J Exp Psychol Applied 14(2):101-117, doi 10.1037/1076-898X.14.2.101 [not retrieved; 2008 [AB] in PA #13]. Eglington & Pavlik (2020), npj Science of Learning 5:15 [EX: PA #13].

**What it models.** Each practice leaves a trace whose strength decays as a power of age; the decay rate for each trace depends on the activation when it was laid down, which yields the spacing effect.

**Equations.** (1) m_n = ln(Σ_{j=1}^{n} t_j^−d); (2) recall probability = e^{m/s} / (e^{m/s} + e^{τ/s}); (3) d_j = c·e^{m_j} + a; (4) m_n = ln(Σ_{j=1}^{n} t_j^{−d_j}). Time between sessions is multiplied by h ("psychological time"). Every trial counts as one encoding whether correct or not.

**Parameters.** Five shared: a (decay intercept), c (decay scale), s (noise), τ (threshold), h (between-session scaling). Fitted values: a 0.167, c 0.232, s 0.252, τ −0.669, h .031 (Japanese-English pairs, 162 aggregate points, RMSD .046, r² .971). Glenberg (1976) exp. 3, τ fixed at −0.669: a .104, c .374, s .4, r² .980, RMSD .009.

**Fitting.** χ²-type minimization on aggregate condition means (not per student).

**Data and results.** Two sessions 1 or 7 days apart; items repeated 1, 2, 4, 8 times at spacings of 2, 14, or 98 trials; human data matched the model closely overall.

**Code and license.** None found.

**Stated limitations.** The 8-repetition, spacing-14 condition on session 2 was not captured and the authors could not explain it; Lindsey 2014 notes that such models need many parameters to fit individuals.

## 12. Logistic vs deep knowledge tracing (Gervet et al. 2020)

**Citation and link.** Gervet, Koedinger, Schneider & Mitchell, "When is Deep Learning the Best Approach to Knowledge Tracing?", JEDM 12(3), starts p. 31 [FT]. Code: https://github.com/theophilee/learner-performance-prediction.

**What it models.** Compares IRT, PFA, DAS3H, a new Best-LR, BKT, BKT+, DKT, SAKT and a feedforward network (Best-FFW) on nine datasets.

**Equations.** Best-LR: σ(α_s − δ_q + φ(c_s) + φ(f_s) + Σ_{k∈KC(q)} (β_k + γ_k φ(c_{s,k}) + ρ_k φ(f_{s,k}))), φ(x) = log(1+x); c_s, f_s total correct and wrong counts. "DAS3H without time-window features but augmented with total count features."

**Parameters.** Per student, per item, per KC (3), plus two global total-count weights.

**Fitting.** scikit-learn L-BFGS, L2, C in {0.1, 1, 10} (insensitive). DKT: one layer, dropout 0.5, size 200 on most sets. 5-fold nested CV by learner; AUC and RMSE.

**Data and results.** Learners per item (median) order the sets: algebra05 1, bridge06 4, assist09 10, assist12 22, assist17 90, statics 136, squirrel 137, spanish 178. Test AUC (RMSE) Best-LR vs DKT: algebra05 .831 (.329) vs .821 (.334); bridge06 .803 (.366) vs .790 (.368); assist09 .772 (.423) vs .757 (.428); spanish .863 (.334) vs .832 (.364); assist12 .751 (.416) vs .771 (.414); assist17 .714 (.450) vs .770 (.434); statics .819 (.368) vs .829 (.367); squirrel .765 (.423) vs .772 (.421); assist15 .702 (.419) vs .731 (.416). Best-LR leads on 4 sets, DKT on 5. On squirrel subsampling, Best-LR dominates below about one million interactions; DKT plateaus after about 1,000 interactions per student (spanish) and reaches near-peak with 10 interactions vs 60 for Best-LR. Time windows add nothing to Best-LR but lift a feedforward net (+.048 AUC assist17, +.014 assist12). Expert KC model adds ≤0.01 AUC on 7 of 9 sets (+0.03 on algebra05, bridge06).

**Code and license.** Paper says code is "freely available"; license file not found, UNVERIFIED.

**Stated limitations.** No cross-validation over items, so generalization to new items is untested; IRT ability never fit; DKT's temporal advantage is unexplained.

## 13. FSRS or flashcard memory models on skills and items of varying difficulty

**Search status.** No published application of FSRS to procedural or problem-solving skills found. PA (line 131) records the same: "no peer-reviewed FSRS-6/7 paper, no published study scheduling varied-problem math skills with an FSRS-type model". SK lines 105-120 hold forum positions, not papers. Web search quota ran out before further checks.

**Adjacent published evidence.**
- LKT (section 4): memory features on procedural or mixed datasets: Andes physics PPE .762 vs AFM .732 AUC; KDD PPE .768 vs .731; Assistments .726 vs .715; large gains only on fact-like sets. The authors: "learning and memory theories make distinct predictions for learning and remembering facts versus procedural information".
- Maier, Slavin, Baker & Stalzer (2023), ICCE 2023, "Studying Memory Decay and Spacing within Knowledge Tracing" [FT]: McGraw-Hill Reveal Math Course 1 (489,359 points, 4,363 items, 71 skills; 647 test students, 98,604 points). PFA baseline AUC .6975 / RMSE .4443; MemDec (decayed PFA, practice order, b_s = .6, b_f = .7) .7679 / .4076; time windows 1 d .756, 2 d .754, 7 d .749, 14 d .747; spacing gave no gain; authors call the data "relatively massed". No license found.

## Could not find or verify

- CFM equation, parameters, fitting and numbers beyond the abstract (paywalled); Cen et al. 2006 LFA paper (only the 2005 workshop version read).
- Corbett & Anderson 1995 text; BKT equations here come from SM, not the primary paper.
- Walsh et al. 2018 full text: exact PPE equations, fitting, typical parameter values. The Wright State thesis (Collins 2024) was blocked by a bot check and not pursued.
- Pavlik & Anderson 2005 and 2008 full texts (only the conference paper was read).
- Gong et al. 2011 PFA-decay; R-PFA published JEDM version; DASH online supplement and Figure 4 values; Qiu et al. 2011 and other BKT-with-time models.
- Licenses: DAS3H repo, Gervet repo, DASH, LFA, DataShop AFM, R-PFA code, libFM, Khajah DKT; patent 8,777,628 unread.
- Pelánek 2016 and Eglington & Pavlik 2020 only through existing notes.
- Any FSRS or flashcard-model study on problem-solving skills; none found, search quota exhausted.
