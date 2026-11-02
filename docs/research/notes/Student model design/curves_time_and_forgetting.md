# Curves, time and forgetting: gathered findings (no recommendations)

Compiled 2026-11-02. Reports what sources say, no recommendations. **UNVERIFIED** = not seen in a primary text, or read from a figure; **SECONDARY** = described by another source. Already covered, so cited not re-gathered (under `/docs/research/notes/`): `Toishi build research/learning_science.md` (Cepeda 2008, Brunmair & Richter 2019, Rohrer 2015/2020, Donovan & Radosevich 1999, Kalyuga/Renkl secondary), `Practice systems and learning science/science_of_practice.md` (successive relearning, worked examples), `Toishi gaps research/speed_mastery_goals.md` (RT as signal).

## A. Accuracy learning curves

### A1. Koedinger, Carvalho, Liu & McLaughlin 2023, PNAS
- **Citation and link:** "An astonishing regularity in student learning rate", PNAS 120, e2221311120. https://doi.org/10.1073/pnas.2221311120 (full text via PMC10068755; SI Table S1 not accessible).
- **Population, task and N:** 27 PSLC DataShop datasets (language, math, science; upper elementary to college; mostly tutoring systems); about 7,000 students and 1.3 million attempts in total, about 40 to nearly 4,000 students per dataset (counts from A2). Datasets with initial success above 80% excluded.
- **Method:** individual Additive Factors Model (iAFM), mixed-effects logistic regression on first-attempt correctness: logit p = (θ + θi + βk) + (δ + δi + γk)·opportunities; linear in log odds, no asymptote or slip term. KC model per dataset chosen by 3-fold item-blocked CV. Opportunities to 80% = (logit 0.80 − θ)/δ.
- **Key numbers:** median population intercept θ = 0.638 log odds = 65.42% correct. Median learning rate δ = 0.09 log odds per opportunity (M = 0.15, CI [0.08, 0.22]) = 2.5 percentage points from 65%. Median opportunities to 80%: 7.24 (M = 12.27, CI [7.09, 17.45]). Students' initial knowledge: median SD 0.651, median IQR 0.830 log odds; lower half of students 55% vs upper half 75% correct; opportunities to 80%: 13.13 vs 3.66. Student learning rate: median SD 0.015, median IQR 0.018 (about 1% per opportunity, 2.56% to 1.70%); KC learning rate: median SD 0.102, IQR 0.132. Slower-half learners need 7.89 opportunities, faster-half 6.94. Student learning-rate IQR by domain: language (6 datasets) 0.045, math (16) 0.017, science (5) 0.008. iAFM beat AFM by AIC in 21 of 27 datasets (BIC: 15).
- **Stated limitations:** favorable conditions only (interactive technology with hints and feedback); peer interaction and classroom dialogue not represented. Student learning-rate variation is "either not present or too small to be detectable" in some datasets.

### A2. Lee, Lichand, Barnard, Klotz, Thille, Kim & Domingue 2026 (ACM L@S '26)
- **Citation and link:** "Revisiting the Regularity of Student Learning Rate: Sensitivity to Which Observations Are Included", arXiv:2605.01690v2 (18 May 2026). https://arxiv.org/pdf/2605.01690
- **Population, task and N:** 26 of the 27 Koedinger datasets (ds4555 restricted); about 1.3 million attempts, about 7,000 students; per dataset 41 to 3,819 students, 4 to 194 KCs. Share of observations in (student, KC) pairs longer than 10 attempts ranges 0.8% to 97.0%.
- **Method:** iAFM refit in R lme4; (a) truncation to the first 10 attempts per (student, KC) pair (20 datasets); (b) pattern mixture, separate fits on short (10 or fewer) and long pairs (9 datasets).
- **Key numbers:** replication median IQR of student slopes 0.020 (original 0.018). Truncation: SD of student intercepts −1.5% (IQR −5.7% to +2.1%); SD of student slopes +118% (IQR +44% to +297%; up in 18 of 20); population slope +18% (median 0.088 to 0.126); Spearman ρ = 0.68 between slope-SD change and fraction of data dropped. Pattern mixture: slope SD higher in short pairs in all 9 datasets (median +233%); population slope higher in short pairs in all 9 (median difference 0.12 log odds per opportunity), by a factor of 2 or more in 7; intercept SD about unchanged.
- **Stated limitations:** single truncation threshold; linear opportunity term approximate; pattern mixture on 9 datasets chosen for data adequacy; calendar time not modeled; does not resolve whether learning rates truly differ.

### A3. Simpson, Norberg & Fancsali 2024 (EDM)
- **Citation and link:** "Replication of Koedinger et al. (2023)", Proc. 17th EDM, pp. 420-425. https://educationaldatamining.org/EDM2024/proceedings/2024.EDM-short-papers.40/index.html
- **Population, task and N:** Study 1: five Koedinger datasets (41 to 123 students). Study 2: MATHia geometry/area workspaces, 2022-23, first attempts only; 570 students (W1) plus 3,000 per workspace W2-W6 (15,570 total), 5 to 57 skills per workspace.
- **Method:** iAFM as GLMM, shrunken random effects, bootstrapped 95% intervals.
- **Key numbers:** Study 1 student-slope IQRs reproduced (0.012 to 0.047; original largest 0.102, Chinese vocabulary). Study 2 fixed learning rates per opportunity (log odds): W1 0.48, W2 0.16, W3 0.45, W4 0.30, W5 0.39, W6 0.45; fixed intercepts −0.31 to 1.69 (wide CIs). Student-slope IQR 0.0056 to 0.1182 (W6, above the original largest); student-intercept IQR 0.7474 to 1.3238; slope variance under 0.0001 to 0.0087 vs intercept variance 0.321 to 0.8102; skill-level slope variances much larger than student-level.
- **Stated limitations:** iAFM "a very new model"; fixed-intercept CIs very wide (text says maximum range 1.04, table about 2.08); few math topics. Initial-accuracy distributions and opportunities to 80% not reported.

### A4. Beauchesne, Maroti, Bratman, Pesenti, Holt, Tambellini, McGrath, Guo & Peterson (Campus AI)
- **Citation and link:** "Personalized AI Practice Replicates Learning Rate Regularity at Scale", arXiv:2604.03246 (year not stated in fetched text). https://arxiv.org/pdf/2604.03246
- **Population, task and N:** mobile test-prep platform; 7,161 students, 366,127 opportunities, 51,437 LLM-generated KCs (after filtering: KCs under 5 interactions and opportunities beyond the 30th dropped).
- **Method:** iAFM variant without KC-specific terms, with fixed effects for exercise type and simplification.
- **Key numbers:** population intercept 0.686 (student SD 0.461); population rate 0.0657 (student SD 0.0121; prior work 0.015). Percentiles 25/50/75: initial accuracy 64.24 / 71.34 / 76.92%; opportunities to 80% by initial knowledge 12.18 / 7.22 / 2.78, by learning rate 8.25 / 7.52 / 7.01. Median 7.22 vs 6.54 for expert-designed curricula (as cited). Error floors not reported.
- **Stated limitations:** self-selected high-intent users; attrition filters; skipped exercises may bias correctness; unsupervised LLM generation; most KCs practiced by one student; short-term mastery only.

### A5. Liu & Koedinger 2015 (EDM)
- **Citation and link:** "Variations in learning rate: Student classification based on systematic residual error patterns across practice opportunities", Proc. 8th EDM. https://www.educationaldatamining.org/EDM2015/proceedings/short420-423.pdf
- **Population, task and N:** 8 DataShop datasets (geometry, equation solving, story problems, grammar, statistics); 907 students.
- **Method:** AFM residual-by-opportunity correlation per student (steep r > 0.1, flat r < −0.1, else regular); AFM+StudRate vs AFM+GroupRate (three group rates); AIC, BIC, 10-fold CV.
- **Key numbers:** AFM+StudRate failed to beat AFM RMSE in 14 of 16 cases; AFM+GroupRate best on all 8 datasets (AIC, BIC, item-CV); GroupRate item-CV RMSE .3085 to .4166 across datasets. Group membership predicted post-test after pre-test in several datasets (IWT 1 marginal, p = .077).
- **Stated limitations:** no evidence of a fixed learning-speed trait; authors suggest groups reflect position on the curve. No slope distributions or group sizes reported.

### A6. Yudelson, Koedinger & Gordon 2013 (AIED)
- **Citation and link:** "Individualized Bayesian Knowledge Tracing Models". https://www.academia.edu/25841291/Individualized_Bayesian_Knowledge_Tracing_Models (mirror of paper text).
- **Population, task and N:** Cognitive Tutor Algebra I (3,310 students, 8.9 million rows, 515/541 skills) and Bridge to Algebra (6,043 students, 20.0 million rows, 807/933 skills).
- **Method:** standard BKT vs student-specific P(L0), P(T), or both; guess and slip constrained, not individualized; 10-fold user-stratified CV.
- **Key numbers:** RMSE standard / indiv. P(L0) / indiv. P(T) / both: Algebra I 0.362734 / 0.362653 / 0.361161 / 0.361192; Bridge 0.362944 / 0.362553 / 0.358511 / 0.358542. Authors: individualizing learning rate helps more than initial knowledge. No fitted-parameter distributions printed.
- **Stated limitations:** RMSE and accuracy only, no AUC.

### A7. BKT and PFA papers fetched (bounds, start values, fit; no fitted-value tables)
- **Citation and link:** Pavlik, Cen & Koedinger 2009 (PFA) https://files.eric.ed.gov/fulltext/ED506305.pdf; Hawkins, Heffernan & Baker 2011 https://learninganalytics.upenn.edu/ryanbaker/paper_143.pdf; Pardos & Heffernan 2011 (KT-IDEM) https://web.cs.wpi.edu/~nth/pubs_and_grants/papers/2011/UMAP/Pardos%20Introducing%20Item%20Difficulty.pdf; Falakmasir et al. 2015 https://www.educationaldatamining.org/EDM2015/proceedings/short360-363.pdf; Slater & Baker https://learninganalytics.upenn.edu/ryanbaker/behaviormetrika_vfinal.pdf; Baker, Corbett & Aleven 2008 (abstract only) https://www.springerprofessional.de/doi/10.1007/978-3-540-69132-7_44; Penn slide https://learninganalytics.upenn.edu/MOOT/slides/W004V002.pdf.
- **Population, task and N:** PFA: Andes Physics, Geometry, Bridge to Algebra (algebra, fractions), 4.1E+4 to 1.0E+5 observations. Hawkins 2011: ASSISTments, 1,579 students, 67 skill builders. KT-IDEM: 10 ASSISTments sets (637 to 1,285 students), 12 Bridge skills (116 to 159 students). Falakmasir: KDD Cup 2010, over 6,000 students, about 1,650 skills.
- **Method:** BKT by EM or gradient descent, PFA, cross-validation; Slater & Baker simulate 51,030 datasets.
- **Key numbers:** PFA bounds: gamma at least 0; KT slip maximum 0.1, guess maximum 0.3 (KT2: initial learning maximum 0.85, transition maximum 0.3). PFA vs KT1 (A′): Physics .719 vs .708; Geometry .685 vs .660; Algebra .711 vs .687; Fractions .723 vs .706. EM start values: Hawkins 2011 L0 0.5, others 0.1. KT-IDEM mean AUC: ASSISTments 0.669 vs 0.699; Cognitive Tutor 0.6457 vs 0.6441. Falakmasir standard BKT: accuracy 0.8609 (item CV) and 0.8659 (student CV), RMSE 0.3293 and 0.3153, majority class 0.8569. Slater & Baker (simulated): SD of fitted P(T) across 30 trials 0.080 to 0.146 at 25 students vs 0.015 to 0.035 at 500 (P(L0) 0.105 to 0.159 vs 0.033 to 0.043); up to 42% of guess estimates at bounds; 5 and 10 students did not recover seeds. Bounds cited by others (SECONDARY): guess < 0.3 and slip < 0.1 (Corbett & Anderson 1995); both < 0.5 (Baker et al. 2008).
- **Stated limitations:** none of these printed fitted P(L0), P(T), guess, slip, gamma or rho values or their spread across KCs or students.

## B. Speed-up with practice

### B1. Newell & Rosenbloom 1981 (not obtained)
- **Citation and link:** "Mechanisms of skill acquisition and the law of practice", in Anderson (ed.), Cognitive Skills and Their Acquisition, pp. 1-55. Primary not retrieved; secondary excerpts: https://cdn.aaai.org/AAAI/1982/AAAI82-061.pdf, Heathcote et al. 2000, Anglim 2011.
- **Population, task and N / Method:** SECONDARY: survey of existing datasets incl. Seibel's 1,023-choice task (76,725 trials); T = B·N^−α, linear in log-log; power beat exponential "in every case" (Heathcote); four-parameter power beat three-parameter exponential (Anglim).
- **Key numbers:** no fitted exponents or typical α recovered. UNVERIFIED.
- **Stated limitations:** Heathcote et al. refit a subset by least squares: power still won for averaged data, exponential won for the two unaveraged series.

### B2. Heathcote, Brown & Mewhort 2000
- **Citation and link:** "The power law repealed: The case for an exponential law of practice", Psychonomic Bulletin & Review 7(2), 185-207. https://doi.org/10.3758/BF03212979
- **Population, task and N:** 40 data sets, 7,910 learning series, 475 subjects, 24 experiments; memory search, counting, mental arithmetic, visual search, key-press and other tasks.
- **Method:** power, exponential, general power (pre-experimental practice term) and APEX functions fit to individual series and averaged data.
- **Key numbers:** exponential beat power in 82.2% of series (ties 2.5% excluded), 64% (MS2) to 93% (Count3); mean R² .498 vs .426 (17% improvement); exponential won in every unaveraged data set; averaging biased toward power. APEX beat general power in 84.1% of series (70% to 94%). Asymptote below 150 ms: power 87.7% of series, exponential 16.1%, general power 35.3%, APEX 27.4%. Pre-experimental practice estimates averaged 90.4% of series length.
- **Stated limitations:** exponentials may overpredict asymptote when learning slows early; short, noisy individual series.

### B3. Evans, Brown, Mewhort & Heathcote 2018
- **Citation and link:** "Refining the law of practice", Psychological Review. https://doi.org/10.1037/rev0000105 (read: accepted manuscript, https://figshare.utas.edu.au/articles/journal_contribution/Refining_the_Law_of_Practice/22964183/1/files/40706153.pdf).
- **Population, task and N:** the 17 data sets of Heathcote et al. 2000 (memory search, counting, mental and alphabetic arithmetic, visual search, motor) plus Rickard 2004; 4 to 36 participants per set (sum 309, my calculation).
- **Method:** standard and delayed power and exponential laws, general power, lognormal RT distribution, hierarchical Bayes, WAIC; correct trials only.
- **Key numbers:** an exponential law preferred in 15 of 17 data sets, power in 2, standard power never; delay needed in 13 of 17; delayed exponential chosen in 11; delayed power in 2 of 5 mental-arithmetic sets. Rickard data WAIC: delayed exponential 13359 vs exponential 13965; delayed power 14422 vs power 15818; sharp transitions in 71% of series. Example delayed-exponential medians: S3 τ 2.1, r 0.00065, t0 0.13; K1 τ 0.5, r 0.0097, t0 0.52.
- **Stated limitations:** Discussion says delay in 15 of 18 sets vs 13 of 17 in Results (unreconciled); delayed exponential poor for sharp transitions; worse for low-trial sets (M3, M4, M5).

### B4. Rickard 1997
- **Citation and link:** "Bending the power law: A CMPL theory of strategy shifts and the automatization of cognitive skills", JEP: General 126(3), 288-311. https://rickardlab.ucsd.edu/pdf/Rickard1997.pdf
- **Population, task and N:** Exp 1 pound arithmetic (21 recruited, 18 analyzed, six sessions); Exp 2 alphabet arithmetic verification (21 participants, four sessions); reanalysis of Logan 1988.
- **Method:** strategy probed on one third of trials, remainder classified by logistic fits; CMPL vs instance theory.
- **Key numbers:** retrieval on nearly all trials by about block 60; step-function transitions for 90 of 216 items (41%); Exp 1 error .109 (session 1) to .019 (session 5); r² .94 both models (Exp 1), .95 vs .97 (Exp 2); 16 of 18 participants had steeper RT slopes (M −.505) than SD slopes (M −.435). Power law failed overall but held within strategy; algorithm RT fell from about 13,000 to 3,600 ms (new problems about 8,000 ms).
- **Stated limitations:** small samples; strategy inferred on two thirds of trials; CMPL has more free parameters (9 vs 5, Exp 1).

### B5. Delaney, Reder, Staszewski & Ritter 1998
- **Citation and link:** "The strategy-specific nature of improvement: The power law applies by strategy within task", Psychological Science 9(1). https://www.cmu.edu/dietrich/psychology/memorylab/publications/98_pd_lmr_js_fr.pdf
- **Population, task and N:** three mental-arithmetic experiments with feeling-of-knowing reports (Reder & Ritter 1992 Exp 1 and 2; Schunn et al. 1997 Exp 1; two-digit × two-digit "multiply" and invented "sharp") plus expert calculator G.G. (multi-digit multiplication, new strategy from session 501). Individual analysis: 46 participant-by-operator cases (28 multiply, 18 sharp) using each strategy on at least 30% of trials.
- **Method:** power functions on aggregated data vs by participant and strategy (retrieval vs calculation by button press); stepwise regression of trial times.
- **Key numbers:** aggregate fits all R² of at least .95 (no discrimination); strategy-specific estimate superior in all 46 cases. Mean power-function slope α (SD): multiply retrieval 0.54 (0.53), calculation 0.37 (0.18); sharp retrieval 0.11 (1.15), calculation 0.25 (0.88); slopes did not differ by strategy; retrieval intercepts lower (p < .001). G.G. reached the 10% error criterion in 20 sessions, then averaged 5.2% errors.
- **Stated limitations:** error trials excluded; strategy shifts not stepwise (region between first and last switch 42% to 52% of trials); Rickard found no R² gain from strategy-specific fits.

### B6. Industrial learning curves (SECONDARY only)
- **Citation and link:** Wright 1936, J. Aeronautical Sciences (not retrieved); Yelle 1979, Decision Sciences 10(2) (blocked). Read: Tamás & Koltai 2020 https://pp.bme.hu/so/article/download/14136/8566; Mishina 1999 https://www.nber.org/chapters/c10232.pdf; textbook chapter https://highered.mheducation.com/sites/dl/free/8838695636/1130587/learning_curves.pdf; Anglim 2011 thesis https://web-archive.southampton.ac.uk/cogprints.org/8035/1/anglim-2011-skill-acquisition-phd-thesis.pdf; Uzumeri & Nembhard 1998 https://iro.uiowa.edu/esploro/outputs/journalArticle/A-population-of-learners-A-new/9984187070402771; Nembhard & Uzumeri 2000 https://iro.uiowa.edu/esploro/outputs/journalArticle/Experiential-learning-and-forgetting-for-manual/9984187070102771.
- **Population, task and N:** aircraft assembly (Wright); B-17 production (Mishina); workers: 3,874 learning episodes in one US manufacturer (Uzumeri & Nembhard), a manual and a procedural task (Nembhard & Uzumeri; N not seen).
- **Method:** Wright cumulative average Y(Q) = aQ^b; Crawford unit-time version; rate L with b = log L / log 2 (L = 80% gives b = −0.322).
- **Key numbers:** Wright: each doubling of cumulative output cut labor time 20% (80% curve). "Typical industrial" b −0.415 to −0.074, i.e. 75 to 95% (Tamás & Koltai). Textbook (attributed to NASA): aerospace 85%; shipbuilding 80-85%; complex machine tools 75-85%; repetitive electronics 90-95%; machining 90-95%; welding 90%; raw materials 93-96%. Mishina: b = −0.472, 27.9% fall per doubling. Faster learners tend to forget faster (Nembhard & Uzumeri). Anglim: industrial models use group data, confound learning with technology, "little relevance to understanding psychological mechanisms".
- **Stated limitations:** Mishina: the curve "was not able to predict labor hours reliably" at Boeing (as extracted). Primary Wright, Yelle, Dutton & Thomas numbers UNVERIFIED.

## C. Response-time models

### C1. van der Linden 2006
- **Citation and link:** "A lognormal model for response times on test items", J. Educational and Behavioral Statistics 31(2), 181-204. https://doi.org/10.3102/10769986031002181 (abstract and record only).
- **Population, task and N:** adaptive ASVAB test; the 2007 report cites 48 items and 2,000 test takers.
- **Method:** ln Tij ~ N(βi − τj, αi^−2): person speed τ, item time intensity β and discrimination α; Gibbs sampler; posterior predictive checks vs a normal model.
- **Key numbers:** "excellent fit"; normal model could not reproduce skewness; an equality constraint on α caused only a slight loss of fit.
- **Stated limitations:** full text not read; parameter values UNVERIFIED.

### C2. van der Linden 2007 (report version)
- **Citation and link:** "A hierarchical framework for modeling speed and accuracy on test items", Psychometrika 72, 287-308; read LSAC Research Report 05-02. https://ris.utwente.nl/ws/files/5129699/Linden05hierarchical.pdf
- **Population, task and N:** framework paper; ASVAB CAT fit example (48 items, 2,000 test takers).
- **Method:** 3PNO response model plus lognormal time model; person (θ, τ) and item (a, b, c, α, β) parameters multivariate normal with correlations; response and time conditionally independent given (θ, τ).
- **Key numbers:** speed-accuracy tradeoff is a within-person relation; a population can show a positive speed-accuracy correlation. In an earlier CAT study θ and τ were uncorrelated, yet ability correlated positively with total time because difficulty and time intensity correlated ρ = .65 and adaptive selection gave harder items to abler examinees.
- **Stated limitations:** conditional independence is an assumption; observed score-time correlations depend on item sampling.

### C3. Klein Entink, Fox & van der Linden 2009
- **Citation and link:** "A multivariate multilevel approach to the modeling of accuracy and speed of test takers", Psychometrika 74(1), 21-48 (Cambridge Core PDF).
- **Population, task and N:** Example 2: 388 test takers, 65 items, Natural World Assessment Test; Example 1: 286 undergraduates, 22 personality items.
- **Method:** joint IRT and lognormal RT model with covariates; Gibbs sampler, Bayes factor, DIC.
- **Key numbers:** Example 2 person-level correlation of ability and speed parameters −0.76 (covariance −0.38; sign convention UNVERIFIED); difficulty and time-intensity correlation 0.21; effort → ability 0.25, effort → speed −0.22.
- **Stated limitations:** conditional-independence structure does not capture a speed-accuracy tradeoff; Bayes factor prior-sensitive; DIC ignores unknown variances.

### C4. Domingue et al. 2022
- **Citation and link:** "Speed-accuracy trade-off? Not so fast: Marginal changes in speed have inconsistent relationships with accuracy in real-world settings", JEBS 47(5), 576-602. https://doi.org/10.3102/10769986221099906
- **Population, task and N:** 29 cognitive-task data sets (not named in the record).
- **Method:** flexible conditional-accuracy method tested by simulation.
- **Key numbers:** small within-person increases in time use did not reliably predict higher accuracy; relation may depend on item difficulty; respondents with more within-person speed variation tended to have lower ability; response time a weak predictor of accuracy.
- **Stated limitations:** abstract only; numbers UNVERIFIED.

## D. Forgetting and retention

### D1. Arthur, Bennett, Stanush & McNelly 1998
- **Citation and link:** "Factors that influence skill decay and retention: A quantitative review and analysis", Human Performance 11(1), 57-101. https://Www.Gwern.net/doc/psychology/spaced-repetition/1998-arthur.pdf
- **Population, task and N:** 53 articles, 189 data points; 178 points, N = 8,719 in the interval analysis.
- **Method:** Hunter-Schmidt meta-analysis; d = retention vs end-of-training score; eight retention-interval bins.
- **Key numbers:** overall mean d −0.97 (corrected −0.95, SD 0.72). Mean d (k) by bin: under 1 day +0.02 (3); 1-7 days −1.03 (89); over 7-14 −1.54 (13); over 14-28 −0.95 (19); over 28-90 −0.65 (33); over 90-180 −1.42 (7); over 180-365 −1.04 (11); over 365 −1.28 (3). Interval-d correlation across the 8 bins −0.51. Moderators (mean d): cognitive −1.18 vs physical −0.76; speed tasks −0.33 (k = 33) vs accuracy −1.02 (k = 145); closed-loop −0.73 vs open-loop −1.06; natural −0.94 vs artificial −1.00; recognition −0.85 vs recall −0.96 (corrected). Degree of overlearning vs skill loss: 0.08 in Table 6 (a correlation converted to d; k = 30; 83% of points had no overlearning information). Largest moderator in Table 6: retrieval conditions, 1.13.
- **Stated limitations:** abstract says d = −1.4 after more than 365 days, Table 3 shows −1.28 (k = 3); large SDs imply moderators; moderators collapsed across intervals and confounded (open-loop tasks over-represent cognitive tasks).

### D2. Tatel & Ackerman 2025
- **Citation and link:** "Procedural skill retention and decay: A meta-analytic review", Psychological Bulletin 151(6), 696-736. https://doi.org/10.1037/bul0000481 (abstract only).
- **Population, task and N:** motor-based procedural skills; 457 reports, 1,344 effect sizes.
- **Method:** random-effects metaregression, retention interval continuous.
- **Key numbers:** gap between acquisition and retention grew 0.08 SD per month (accuracy measures) and 0.06 SD per month (speed and mixed). Half of initial gains lost after about 6.5 months (accuracy), 13 (speed), 11 (mixed).
- **Stated limitations:** retention must be separated from relearning; speed-accuracy tradeoffs complicate interpretation. Moderator estimates UNVERIFIED.

### D3. Bahrick & Hall 1991 (SECONDARY only)
- **Citation and link:** "Lifetime maintenance of high school mathematics content", JEP: General (1991), PsycNet 1991-19106-001 (blocked). Secondary: https://www.edweek.org/education/psychologist-examines-retention-of-mathematical-knowledge/1991/01; https://files.eric.ed.gov/fulltext/EJ1076383.pdf (Willingham 2015); Karsenty 2002 (Weizmann PDF).
- **Population, task and N / Method:** algebra and geometry tests, cross-sectional by years since course (up to 74) and highest course; 1,726 people (EdWeek), "about 1700" (Karsenty), "more than 1,000" (Willingham).
- **Key numbers:** none first-hand. Secondary: those with courses beyond calculus "showed no loss of their algebra knowledge, even 50 years after"; single-year learners performed near chance; grades had minor influence on loss; amount and distribution of practice mattered most.
- **Stated limitations:** percent-correct curves not found. UNVERIFIED.

### D4. Rohrer & Taylor 2006
- **Citation and link:** "The effects of overlearning and distributed practice on the retention of mathematics knowledge", Applied Cognitive Psychology 20, 1209-1224. https://files.eric.ed.gov/fulltext/ED505642.pdf
- **Population, task and N:** 216 undergraduates (Exp 1: 116, 6 excluded for 0 or 1 of 5 correct after tutorial; Exp 2: 100). Task: number of distinct orderings of letter strings with repeats.
- **Method:** Exp 1: Spacers 5 problems in each of two sessions 1 week apart vs Massers 10 in one session; test 1 or 4 weeks after last practice. Exp 2: 9 vs 3 problems in one session; test 1 or 4 weeks later.
- **Key numbers:** Exp 1 (read from Figure 1B, UNVERIFIED exact): 1 week Massers 75%, Spacers 70% (n.s.); 4 weeks Spacers 64%, Massers 32% ("virtually doubled"); spacing × interval F(1,106) = 7.21, ηp² = .06; strategy F(1,106) = 3.67, p = .06. Exp 2 (Figure 1D): 1 week 69% and 67%, 4 weeks 28% and 27% (group order not recorded); practice amount F < 1; interval ηp² = .28. Describes Driskell et al. 1992 as 51 comparisons, d = .75, only 7 with interval over 1 week (longest 28 days), largest effects under 1 hour (SECONDARY).
- **Stated limitations:** one procedure, college students; some Spacers forgot across the 1-week gap; small overlearning not ruled out.

### D5. Rohrer & Taylor 2007; Rohrer et al. 2005
- **Citation and link:** Rohrer & Taylor, "The shuffling of mathematics problems improves learning", Instructional Science 35, 481-498, https://www.Gwern.net/doc/psychology/spaced-repetition/2007-rohrer.pdf (also in `learning_science.md`); Rohrer, Taylor, Pashler, Wixted & Cepeda, "The effect of overlearning on long-term retention", Applied Cognitive Psychology 19, 361-374, https://files.eric.ed.gov/fulltext/ED505637.pdf.
- **Population, task and N:** 2007: Exp 1 66 undergraduates (6 excluded), permutations; Exp 2 volume of solids (t(14)). 2005: 130 (10 city-country pairs) and 88 (20 word-definition pairs) undergraduates.
- **Method:** 2007 Exp 1: Spacers (2+2 problems, 1 week apart) vs Massers (4) vs Light Massers (2), tested 1 week later; Exp 2 blocked vs mixed. 2005: 5 vs 20 test-feedback trials, tests at 1, 3, 9 weeks.
- **Key numbers:** 2007 Exp 1: Spacers 74%, Massers 49%, Light Massers 46%, F(2,57) = 3.59, ηp² = 0.11 (Massers vs Light p = 0.8). Exp 2 test: Mixers 63% vs Blockers 20%, d = 1.34 (practice: Blockers 89% vs Mixers 60%). 2005 Exp 1: 1 week 70% vs 31%; 9 weeks 24% vs 17% (n.s.).
- **Stated limitations:** small samples; single sessions; fact materials in 2005; 2005 Exp 2 results not captured.

### D6. Cepeda, Pashler, Vul, Wixted & Rohrer 2006
- **Citation and link:** "Distributed practice in verbal recall tasks: A review and quantitative synthesis", Psychological Bulletin 132(3), 354-380. https://www.yorku.ca/ncepeda/publications/CPVWR2006.pdf
- **Population, task and N:** 839 assessments, 317 experiments, 184 articles; verbal recall only.
- **Method:** meta-analysis of spacing and lag (ISI) effects plus optimal-ISI analysis.
- **Key numbers:** 80% of differences used retention intervals under 1 day, 4% over 1 month. At 1-day retention, recall rose as ISI difference went from 1-15 min to 1 day; at 2-28 days a 1-day difference beat 1-15 min, with a marginally significant drop beyond; over 1 month only qualitative evidence of an optimum above 1 day. Optimal ISI rises with retention interval.
- **Stated limitations:** sparse long-interval data; not math.

### D7. Existing-note evidence (not re-verified here)
- **Citation and link:** `learning_science.md` lines 56-62 and 89-92 (Cepeda 2008; Rohrer, Dedrick & Stershic 2015; Rohrer et al. 2020; Brunmair & Richter 2019; Donovan & Radosevich 1999).
- **Population, task and N / Method:** see those notes (Cepeda 2008: 1,354 participants; Rohrer 2020: 787 students; Brunmair & Richter: 59 papers, N = 8,466).
- **Key numbers (as stated there, not re-verified):** Cepeda 2008 optimal gaps about 3, 8, 12, 27 days for intervals of 7, 35, 70, 350 days. Rohrer 2015 d = 0.42 at 1 day, 0.79 at 30 days. Rohrer 2020 d = 0.83. Brunmair & Richter math g = 0.34 [0.11, 0.57]. Donovan & Radosevich d = 0.46 overall, 0.07-0.11 for high complexity.
- **Stated limitations:** not re-checked.

## E. Within-session vs across-session practice, overlearning, successive relearning

### E1. Driskell, Willis & Copper 1992 (SECONDARY only)
- **Citation and link:** "Effect of overlearning on retention", J. Applied Psychology 77(5), 615-622. https://doi.org/10.1037/0021-9010.77.5.615 (abstract only).
- **Population, task and N / Method:** meta-analysis of overlearning vs learning to criterion. Abstract gives no counts; Rohrer & Taylor 2006 cite 51 comparisons, cognitive tasks; `science_of_practice.md` says "15 studies" and benefits disappear "around 38 days" (SECONDARY, conflicting).
- **Key numbers:** "moderate overall magnitude" (d = .75 per Rohrer & Taylor); moderated by degree of overlearning, task type, retention length. Moderator values UNVERIFIED.
- **Stated limitations:** not available.

### E2. Rawson & Dunlosky 2013
- **Citation and link:** "Relearning attenuates the benefits and costs of spacing", JEP: General 142, 1113-1129. https://doi.org/10.1037/a0030498 (abstract).
- **Population, task and N:** 3 experiments, 567 students; key-term definitions, about 40,000 scored responses.
- **Method:** test-restudy to 1 or 3 correct recalls, massed vs spaced initial practice, then 2-3 relearning sessions; final test days or weeks later.
- **Key numbers:** initial-spacing benefits substantial before relearning, significantly attenuated after; spacing's time costs also attenuated by faster relearning. No d values in abstract.
- **Stated limitations:** verbal materials.

### E3. Vaughn, Dunlosky & Rawson 2016
- **Citation and link:** "Effects of successive relearning on recall: Does relearning override the effects of initial learning criterion?", Memory & Cognition 44, 897-909. https://doi.org/10.3758/s13421-016-0606-y (abstract).
- **Population, task and N:** Swahili-English pairs; N not in abstract.
- **Method:** initial criterion 1 to 7 recalls, then relearning to one recall at one-week intervals over 4-5 sessions; Exp 2 adds a one-month test.
- **Key numbers:** benefits of a higher initial criterion did not persist across relearning sessions ("relearning override"), including at one month.
- **Stated limitations:** effect sizes UNVERIFIED.

### E4. Rawson, Vaughn, Walsh & Dunlosky 2018
- **Citation and link:** "Investigating and explaining the effects of successive relearning on long-term retention", JEP: Applied 24, 57-71. https://doi.org/10.1037/xap0000146 (abstract).
- **Population, task and N:** two experiments; N not in abstract.
- **Method:** successive relearning vs single-session learning; initial lag varied; RAD model.
- **Key numbers:** relearning potency ds = 1.52 to 4.19; initial-lag effects before relearning ds = 1.07 to 1.87, after relearning ds = −.20 to .38.
- **Stated limitations:** verbal materials.

### E5. Higham, Zengel, Bartlett & Hadwin 2022
- **Citation and link:** "The benefits of successive relearning on multiple learning outcomes", JEP 114(5), 928-944. https://doi.org/10.1037/edu0000693
- **Population, task and N:** introductory psychology; N and effect sizes absent from the fetched record (existing note: preprint 212 students, d = 0.705, .55 vs .41 on repeated items).
- **Method:** three sessions per weekly lecture, two days apart; 20 fill-in-the-blank items, correct items dropped, incorrect re-presented up to 2 more times; vs restudy; weekly alternation.
- **Key numbers:** end-of-semester recall better after relearning; individual differences not associated with the benefit.
- **Stated limitations:** not retrieved.

### E6. Bego et al. 2024
- **Citation and link:** "Single-paper meta-analyses of the effects of spaced retrieval practice in nine introductory STEM courses", Int. J. STEM Education 11. https://doi.org/10.1186/s40594-024-00468-5
- **Population, task and N:** 578 analyzed of 910 undergraduates in eight courses (30 to 112 each: chemistry, physics, biology, statistics, research methods) plus Calculus I (N = 180, Lyle et al. 2022).
- **Method:** within-subject; 24 objectives per course, half massed (quiz right after introduction), half spaced (three consecutive biweekly quizzes); criterial test 30 or 34 days after the fifth quiz window.
- **Key numbers:** pooled mean improvement, eight courses 1.50% (95% CI −0.18 to 3.26%, I² = 87.7); filtered 2.00% (−0.77 to 4.76); nine courses with calculus 2.06% (0.16 to 3.97, I² = 89.2); filtered 2.74% (0.08 to 5.40). Significant courses: Calculus I; Chemistry for Health Professionals (filtered).
- **Stated limitations:** unproctored quizzes; ceiling or low-reliability items removed in filtered analyses; calculus on a different system; some statistics content conceptual.

## F. Worked examples and fading (effect sizes only)

### F1. Barbieri, Clerjuste, Chawla & Miller-Cotto (poster)
- **Citation and link:** meta-analysis poster, University of Delaware (published 2023, Educational Psychology Review, https://doi.org/10.1007/s10648-023-09745-1, not read). https://www.cehd.udel.edu/wp-content/uploads/2022/02/Worked-Examples-Meta-Poster_022722_SC.pdf
- **Population, task and N:** math performance; 40 articles, 49 studies, 185 effect sizes (41 negative, 144 positive; −1.80 to 4.66); participant N not reported.
- **Method:** worked-example vs no-worked-example learners; moderators: example type, format, grade, content.
- **Key numbers:** Hedges g = 0.43, 95% CI 0.31 to 0.55; I² = 94.46%; no moderator significant; 4 articles on faded examples, 7 on incorrect examples (no results). A UDel follow-up cites the published figure as g = .48 (`science_of_practice.md` line 177).
- **Stated limitations:** none stated; most outcomes percent accuracy.

### F2. Reisslein, Atkinson, Seeling & Reisslein 2006
- **Citation and link:** "Encountering the expertise reversal effect with a computer-based environment on electrical circuit analysis", Learning and Instruction 16, 92-103. https://faculty.engineering.asu.edu/mre/wp-content/uploads/sites/31/2020/02/Exp_Rev_LI06.pdf
- **Population, task and N:** 185 engineering undergraduates; series and parallel resistance, 8 items of 3 steps.
- **Method:** 3 (example-problem, problem-example, backward fading) × 2 (pretest split at 7 of 12: high N = 93, low N = 92); near- and far-transfer posttests (max 12).
- **Key numbers:** near transfer low prior knowledge 11.52 / 10.76 / 10.93, high 11.25 / 11.84 / 11.67; interaction F(2,179) = 3.24, p < .05. Far transfer low 5.64 / 5.10 / 3.70, high 9.21 / 8.63 / 7.97; prior knowledge f = .46; no procedure or interaction effect.
- **Stated limitations:** low-knowledge fading learners scored below example-problem learners (unexpected); interaction only on near transfer.

## Could not find or verify
- Newell & Rosenbloom 1981 primary and typical exponents; Wright 1936, Yelle 1979, Dutton & Thomas 1984 primaries.
- Typical fitted BKT/PFA values (P(L0), P(T), guess, slip, gamma, rho) and their spread across KCs and students: not printed in the A7 papers; Corbett & Anderson 1995, Baker et al. 2008 full text, Pavlik 2009 tables, Pelánek 2017 not retrieved.
- Any per-KC accuracy floor (asymptote) in tutoring data; iAFM has none. Koedinger 2023 SI Table S1 (per-dataset θ, δ).
- Cognitive Tutor step-time or RT learning-curve exponents; algebra strategy-shift studies (Siegler, Lemaire); any model joining the lognormal RT model with practice speed-up.
- Anderson, Fincham & Douglass 1999 (not attempted; web search budget exhausted).
- van der Linden 2006 full text; Klein Entink sign convention; Domingue 2022 per-dataset results.
- Bahrick & Hall 1991 and Driskell 1992 primaries (51 comparisons vs "15 studies"; "38 days").
- Rawson & Dunlosky 2011 and 2022 (blocked); Rawson, Dunlosky & Sciartelli 2013 (doi 10.1007/s10648-013-9240-4; abstract only, two experiments in a real course, no numbers); Janes et al.; Higham 2022 N and effect sizes.
- Kalyuga et al. 2003 and Renkl/Atkinson fading effect sizes; Crissman 2006 (d = 0.57 seen only as cited by Wesenberg et al. 2022, Frontiers in Psychology 13:1032003); Barbieri 2023 published moderators (0.43 vs 0.48).
- Nembhard & Uzumeri 2000 N and models; Tatel & Ackerman per-moderator estimates.
- Discrepancies: Arthur abstract −1.4 vs Table 3 −1.28; Evans 15 of 18 vs 13 of 17; Simpson text vs table CI range.
