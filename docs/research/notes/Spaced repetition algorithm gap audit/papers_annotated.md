# Annotated library: spaced-repetition scheduling and memory models

Compiled 2026-11-01 for an FSRS-6 app that schedules math skills (fresh problem per review) plus flashcards. Complements `skills_not_cards.md` (DAS3H, KAR3L, LECTOR, Math Academy, Birdbrain, Pelánek) and `verifying_srs.md` (metrics, golden tests); those are cross-referenced, not repeated.

Evidence tags: **[FT]** full text read. **[FT*]** page read through a summarizing fetch, so numbers were not checked against raw text. **[AB]** abstract or landing page only. **[DOC]** project docs/code on disk, no paper. **[TR]** full text via translation. PDFs are in `/home/claude/reference/papers/`. Design tags: SKILL = skill-level scheduling, RATE = rating map, DIFF = problem difficulty, DR = desired retention, VERIFY = verifying the scheduler.

## A. FSRS and SuperMemo lineage

**1. Ye, Su, Cao (2022). A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling. KDD '22, 4381–4390.** [doi](https://doi.org/10.1145/3534678.3539081) (ACM blocked; read MaiMemo's [Chinese translation](https://memodocs.maimemo.com/docs/2022_KDD)) [TR]
- *Method.* DHP model on 220M MaiMemo logs: state = half-life h and difficulty d. After recall h' = h(e^{θ·x}+1) with x = [log d, log h, log(1−p)]. After a lapse h' is reset by a log-linear fit and d rises by θ3. SSP-MMC runs value iteration over discretized (h,d) to minimize expected review cost (3 s per recall, 9 s per lapse) to a 360-day half-life.
- *Results.* DHP predicts half-life better than HLR, mainly after lapses. In simulation on its own fitted model (600 s/day, 1000 days), days to master 6000 items: SSP-MMC 466, 80%-threshold 533, SM-2 variant 569, MEMORIZE 793 (12.6% cost saving vs threshold).
- *Design (DR, VERIFY).* The optimal recall probability at review rises with half-life and falls with difficulty: reviewing at lower R early is "desirable difficulty". Gains are simulated on the authors' own model, so they need an online test.

**2. Su, Ye, Nie, Cao, Chen (2023). Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory. IEEE TKDE 35(10), 10085ff.** [doi](https://doi.org/10.1109/TKDE.2023.3251721) [FT] (copy linked from the awesome-fsrs wiki)
- *Method.* Adds GRU-HLR (hidden size 2) next to DHP-HLR; sMAPE loss on half-life; 71,697 grouped samples; ablations of Δt-history and past-p features. Scheduler is SSP-MMC; baselines are Random, SM-2 variant, Half-life, 90% Threshold, MEMORIZE.
- *Results.* Every GRU-HLR variant cuts MAE(p) by at least 64% vs HLR. Past recall probabilities are the most useful feature, because HLR cannot tell outcome order (1,0) from (0,1). In simulation (target 2000 items), SSP-MMC saves about 12.5% review cost vs MEMORIZE (DHP environment) and 16.8% vs Threshold (GRU environment). The authors warn that data degrades above ~141-day half-lives because learners review off-platform.
- *Design (SKILL, VERIFY).* Log the ordered (Δt, outcome) sequence per skill, not counts. Treat long-interval data as noisy.

**3. FSRS-6 specification (no standalone paper).** [awesome-fsrs wiki: The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm) plus `py-fsrs` 6.3.2 code [DOC]
- *Method.* 21 parameters, state (S, D). R(t,S) = (1 + F·t/S)^(−w20), F = 0.9^(−1/w20) − 1, so R(S) = 0.9. Decay w20 is trainable (default 0.1542). Recall: S' = S·(1 + e^{w8}(11−D)S^{−w9}(e^{w10(1−R)}−1)·H·E), with H = w15 (0.6014) for Hard and E = w16 (1.8729) for Easy. Lapse: S' = min(w11·D^{−w12}((S+1)^{w13}−1)e^{w14(1−R)}, S/e^{w17·w18}). Difficulty step ΔD = −w6(G−3), damped by (10−D)/9, with mean reversion to D0(4). Same-day: S' = S·e^{w17(G−3+w18)}·S^{−w19}.
- *Results.* See #17 (benchmark LL 0.3460).
- *Design (RATE).* Ratings act only through pass/fail (Again vs rest), the D drift, and the Hard/Easy growth factors. "Hint" or "second try" mapped to Hard stays a pass, with 0.6× growth, so it inflates R. Handle those outcomes outside FSRS, or map them to Again.

**4. FSRS-7 technical notes (no paper).** [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark), `models/fsrs_v7.py`, `fsrs-rs/docs/` (`FSRS7_PENALTY.MD`, `COST_ADR.MD`) [DOC]
- *Method.* 34 parameters; state = long-term S, short-term S, D. It takes fractional (seconds-level) intervals. The curve is a weighted mixture of a short-term and a long-term power curve, with D rescaling the long-term time axis. Lapse stability is D-independent. Optional recency weighting and scheduling penalties (huge interval jumps at low DR; <10-minute intervals at 99% DR). Experimental "Cost ADR" picks a per-card DR from (S, D, cost weight) after each update, without changing memory updates.
- *Results.* LL 0.3370 (recency) vs 0.3460 for FSRS-6. With same-day reviews scored, 0.3206 vs 0.3842. Cost ADR docs report 2.4–16.4% simulated "relative time saved" across four partitions of one user's collection (the 16.4% partition has 213 cards). That is developer-reported, single-user, and unreviewed.
- *Design (SKILL, DR).* Dual stability matters if a session shows several fresh problems of one skill on the same day. Day-level FSRS-6 is enough otherwise. Pin versions, because this code path is still moving.

**5. SuperMemo.** Woźniak & Gorzelańczyk (1994), *Acta Neurobiol Exp* 54(1):59–62 [PubMed](https://pubmed.ncbi.nlm.nih.gov/8023714/). Woźniak, Gorzelańczyk & Murakowski (1995), *Two components of long-term memory*, 55(4):301–5, [doi](https://doi.org/10.55782/ane-1995-1090) [AB]. [Algorithm SM-17](https://supermemo.guru/wiki/Algorithm_SM-17) and [SM-18](https://supermemo.guru/wiki/Algorithm_SM-18) [FT]. SM-2: spec page blocked by robots.txt; summarized via Schill 2026 (#18).
- *Method.* 1995 abstract: two independent components explain optimum spacing and the spacing effect. SM-2 multiplies interval by an easiness factor d, with d' = d + f(grade), and never predicts recall. SM-17 is the DSR model: Int[n] = Int[n−1]·SInc[D,S,R]. S is the interval giving 0.9 recall. D is the maximum possible stability increase mapped to 0..1. Matrices are fit from the full repetition history, and a target forgetting index of 10% is the default. SM-18 changes only difficulty: it can jump when "anchoring" converts a hard item to an easy one.
- *Results.* Self-reported: SInc matrix deviation of 18% on large collections. It is proprietary, with no external validation.
- *Design (DIFF).* SM-17's notes say that in earlier versions heterogeneous item streams "polluted" matrix entries, which supports a fixed core difficulty band for FSRS events. SM-18 says difficulty is not constant, so allow D to move.

## B. Language-learning regressions

**6. Settles & Meeder (2016). A Trainable Spaced Repetition Model for Language Learning. ACL 2016, 1848–1858.** [ACL](https://aclanthology.org/P16-1174/) [FT]
- *Method.* p = 2^(−Δ/h) and ĥ = 2^(Θ·x), with x = counts of correct, incorrect and total plus lexeme tags. The loss fits both recall and a half-life term. Data: 12.9M Duolingo student-word traces (2 weeks), last 10% held out.
- *Results.* MAE: HLR 0.128, Leitner 0.235, Pimsleur 0.445, constant 0.175, logistic regression 0.211. Without the half-life loss term, MAE is 0.350. AUC is weak (HLR 0.538 vs Leitner 0.542). A/B tests measured engagement only: HLR vs Leitner changed daily "any activity" return by +0.3% and practice by −7.3% (~1M students, 6 weeks). HLR without lexeme features vs HLR with them: +12.0% (3.3M students, 2 weeks). Lexeme weights overfit, and some words decayed quickly.
- *Design (SKILL, VERIFY).* Start from interaction features, not per-skill identity (cold start, overfit). Engagement is not learning. Calibration can improve while discrimination stays near the old heuristic.

**7. Ilídio et al. (2026). Revisiting Half-Life Regression for Explainable and Personalized Spaced Repetition in Duolingo. PMLR 339:217–227.** [PMLR](https://proceedings.mlr.press/v339/ilidio26a.html) [FT]
- *Method.* HLR with crossed random effects for learner and lexeme (HLR+LMM), extended features (EF), then BLUPs into a Random Forest. Same 12.9M traces (~115k learners, 19k lexemes).
- *Results.* AUC: HLR 0.508, +LMM 0.558, +LMM+EF 0.603, RF+EF 0.631 (Leitner 0.510). MAE 0.1153 → 0.1044. Spearman for ĥ: 0.03 → 0.61. No learning outcomes tested.
- *Design (DIFF, SKILL).* Learner and item random effects give the biggest single gain, which supports an additive ability/difficulty layer beside the memory curve (`skills_not_cards.md` §5). Earlier Duolingo follow-ups (Birdbrain) are in the same file §2. Zaidi et al. 2020 (neural HLR) was not fetched.

## C. Optimal scheduling and teaching

**8. Reddy, Labutov, Banerjee, Joachims (2016). Unbounded Human Learning: Optimal Scheduling for Spaced Repetition. KDD '16, 1815–1824.** [doi](https://doi.org/10.1145/2939672.2939850), [arXiv](https://arxiv.org/abs/1602.07032) [FT]
- *Method.* Mnemosyne logs (2,742 users, 88,892 items) set the forgetting model. Leitner decks become a queueing network (M/M/1 queues, mean-recall approximation), and review rates are optimized under a review budget.
- *Results.* Predicts a sharp phase transition. Mastered-item throughput rises linearly with the new-item rate, then collapses once reviews saturate. Confirmed on MTurk (331 workers, 446 items).
- *Design (DR, SKILL).* Gate new-skill introduction on due-review load. Overload cuts the learning rate itself, not just comfort.

**9. Tabibian, Upadhyay, De, Zarezade, Schölkopf, Gomez-Rodriguez (2019). Enhancing human learning via spaced repetition optimization. PNAS 116(10):3988–93.** [doi](https://doi.org/10.1073/pnas.1815156116) (PNAS blocked; read [arXiv v2](https://arxiv.org/abs/1712.01856)) [FT of preprint]
- *Method.* Reviews as a marked point process. Forgetting rate n(t) falls ×(1−α) on recall and rises ×(1+β) on lapse; m(t) = exp(−n(t)(t−t_r)). Quadratic loss (1−m)² + q·u² gives the optimal review intensity u*(t) = q^{−1/2}(1 − m(t)).
- *Results.* On ~5.2M Duolingo (user, word) pairs, grouped by recall pattern, the top-25% pairs by likelihood under MEMORIZE had effort ratios of 0.00–0.07 and forgetting-rate ratios of 0.10–0.22 vs uniform/threshold fits (<1 favors MEMORIZE). That is a natural experiment, selected by schedule likelihood, with no intervention. In #1 it was the slowest baseline.
- *Design (DR).* A single effort parameter q replaces a fixed target R. Review rate is proportional to forgetting probability. Useful for ranking when capacity is limited.

**10. Upadhyay, Lancashire, Moser, Gomez-Rodriguez (2021). Large-scale randomized experiments reveals that machine learning-based instruction helps people memorize more effectively. npj Sci Learn 6:26.** [doi](https://doi.org/10.1038/s41539-021-00105-8) [FT]
- *Method.* RCT in a German driver's-permit question app (questions, not cards). Arms: 'select' (model picks which questions each session shows, n=10,151), 'difficulty' (easier first, n=34,029), 'random' (n=13,600). Learners choose when to study. ~16.75M answers, ~1,900 questions.
- *Results.* The select group had lower empirical forgetting rate in 83.5% of strata. Median reduction was ~48% vs random and ~40% vs difficulty. Half-life was ~69% longer. The outcome is in-app forgetting rate, not a separate post-test.
- *Design (SKILL, VERIFY).* The best RCT precedent for question-based practice. Randomize at learner level and keep logging identical across arms.

**11. Hunziker, Chen, Mac Aodha, Gomez Rodriguez, Krause, Perona, Yue, Singla (2019). Teaching Multiple Concepts to a Forgetful Learner. NeurIPS 32, 4050–4060.** [NeurIPS](https://proceedings.neurips.cc/paper/2019/hash/2952351097998ac1240cb2ab7333a3d2-Abstract.html), [arXiv](https://arxiv.org/abs/1805.08322) [FT]
- *Method.* An adaptive greedy teacher picks the concept maximizing expected recall at the end, under an HLR-type memory model. A data-dependent bound uses stepwise submodularity and curvature. It allows interdependent concepts, for example Apfelsaft/Apfel.
- *Results.* In simulation it beats random, round-robin and lowest-recall-first, most under tight time or many concepts. MTurk, one ~25-minute session, 15 concepts, 40 steps. German (80 people): gain 0.572 vs 0.487 (lowest-recall-first, p=0.065), 0.462, 0.467. Biodiversity (320): 0.475 vs 0.411, 0.390, 0.251; rare species 0.766 vs 0.668.
- *Design (SKILL).* Under limited session time, pick by expected gain, not lowest R. Dependencies are modelled as shared recall, which is the same idea as FIRe credit.

**12. Ebisu v2 (Fasih, 2017–).** [docs](https://fasiha.github.io/ebisu/) [DOC]
- *Method.* Per-fact Beta(α,β) prior on recall at a reference time. Exponential decay is propagated exactly. Updates take Bernoulli, binomial (k of n) or soft-binary quizzes, with ease rescaling.
- *Results.* In the benchmark (untrained, α=β=0.2, t=512): LL 0.4989, RMSE(bins) 0.1627, AUC 0.6051. That is worse than the constant-average predictor (LL 0.3945).
- *Design (RATE, SKILL).* The binomial update is the natural way to record "k of n fresh problems solved" on one skill. Its fixed priors are not calibrated, so use it only for uncertainty.

**13. Pavlik & Anderson (2008), *J Exp Psychol: Applied* 14(2):101–117** [doi](https://doi.org/10.1037/1076-898X.14.2.101) [AB]; **Eglington & Pavlik (2020), *npj Sci Learn* 5:15** [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7567101/) [FT*]
- *Method.* An activation model schedules each item for the best learning gain per unit time. The 2020 experiment practices the item whose predicted recall is just below a threshold of 0.40, 0.70, 0.86, 0.94 or 0.98, vs a fixed-repeat control.
- *Results.* 2008: "large effect sizes", with the optimal interval growing as practice accumulates. 2020: N=291 (Japanese–English pairs, test after 3 days). Mean recall was ~0.47 (0.94) and ~0.48 (0.86), about 40% above control. Thresholds 0.40 and 0.98 were worse (post hoc p<.01–.023; Kruskal–Wallis H(4)=16.5, p<.01).
- *Design (DR).* Direct evidence for a default DR of ~0.85–0.90 rather than 0.95+. It is paired associates in one session, not skills.

## D. Models with ability, difficulty and history

**14. Lindsey, Shroyer, Pashler, Mozer (2014). Improving Students' Long-Term Knowledge Retention Through Personalized Review. *Psychol Sci* 25(3):639–647.** [doi](https://doi.org/10.1177/0956797613504302) [AB]; Mozer et al. (2009), *Multiscale Context Model*, NeurIPS 22 [PDF](https://proceedings.neurips.cc/paper/2009/file/6bc24fc1ab650b25b4114e93a98f1eba-Paper.pdf) [AB read]
- *Method.* DASH = student ability − item difficulty + windowed study-history terms in a logistic model, with hierarchical Bayesian estimation. MCM is a cascade of leaky integrators that predicts the best spacing from one-session forgetting data.
- *Results.* A semester of middle-school Spanish: personalized review gave +16.5% over massed study and +10.0% over generic spacing on a cumulative exam a month later (time-matched). MCM abstract: good spacing "can double retention". DASH without its difficulty term scores LL 0.3682 vs FSRS-6 0.3460 in the benchmark.
- *Design (DIFF, SKILL).* The additive-logit form maps onto skill ability plus tier difficulty plus history (`skills_not_cards.md` §3).

**15. DAS3H, KAR³L, LECTOR (summarized in `skills_not_cards.md` §3).** Choffin et al. 2019 [arXiv:1905.06873](https://arxiv.org/abs/1905.06873) [FT]; Shu et al. EMNLP 2024 [arXiv:2402.12291](https://arxiv.org/abs/2402.12291) [FT]; LECTOR [arXiv:2508.03275](https://arxiv.org/abs/2508.03275) [FT skim]
- *Added here.* DAS3H explicitly separates skills from cards: specific items are "the only way to practice" a skill, and students who master it "should be able to generalize to unseen items", which is our fresh-problem setting. KAR³L's data: 123,143 logs from 543 users on trivia cards; online test of 27 users. It also uses a delta-based policy that picks cards predicted to gain most from review, not lowest R. LECTOR is simulation-only (100 simulated learners).
- *Design (DIFF, VERIFY).* Treat KAR³L and LECTOR as ideas, not evidence.

**16. Randazzo (2022). Memory Models for Spaced Repetition Systems. MSc thesis, Politecnico di Milano.** [handle](https://hdl.handle.net/10589/186407) [FT]
- *Method.* Compares 1PL-IRT, HLR, DASH, DASH[MCM], DASH[ACT-R] and two new models: DASH[RNN], and R-17, a neural approximation of SM-17. Swift question data (same app as #10): ~80k train and ~40k test reviews per sample.
- *Results.* AUC DASH[RNN] 0.853–0.861; R-17 0.839–0.844; DASH 0.822–0.835; IRT (no history) 0.772–0.785; HLR ~0.61, ICI 0.145. On a tiny set (3,700 histories, 97% success) R-17 falls to 0.665.
- *Design (DIFF, VERIFY).* On question data, history adds about +0.06–0.08 AUC over item/learner terms alone, and HLR is badly miscalibrated. Expect the difficulty term to carry much of the signal for fresh problems.

## E. 2024–2026 evaluations on large datasets

**17. SRS Benchmark and anki-revlogs-10k (Open Spaced Repetition).** [repo](https://github.com/open-spaced-repetition/srs-benchmark); [dataset](https://huggingface.co/datasets/open-spaced-repetition/anki-revlogs-10k) (no paper) [DOC]
- *Method.* 9,999 users, 349.9M scored reviews, 5-fold time-series split, log loss / RMSE(bins) / AUC (see `verifying_srs.md` §1).
- *Results (no same-day).* RWKV-Instant 0.2773 / AUC 0.8329 (2.76M parameters, trained across users, uses duration, siblings, deck). GRU 0.3328. FSRS-7 recency 0.3370. FSRS-6 0.3460 / 0.0653 / 0.7034. FSRS-5 0.3561. FSRS-4.5 0.3625. DASH 0.3682. AVG 0.3945. HLR 0.4694. Ebisu 0.4989. README says ~727M reviews; the dataset card says 938M rows.
- *Design (VERIFY, RATE).* A 21-parameter per-user curve beats HLR, DASH and Ebisu clearly. The large gap to RWKV shows context features carry signal, so log them. RMSE(bins) uses interval, count and lapse bins that do not exist for varied-problem skills, so rebuild the metric around skill and tier.

**18. Schill (2026). Interpretable Memory Models for Spaced Repetition. arXiv:2610.10548.** [arXiv](https://arxiv.org/abs/2610.10548) [FT] (single-author preprint)
- *Method.* SBD has 7 weights and states stability, brittleness and difficulty, with a Gamma-frailty curve. It trains on anki-revlogs-10k with the benchmark's fine-tuning. Planning by value iteration maximizes the discounted area under the recall curve at review cost λ. With a daily budget B it uses a Whittle index: review the B highest-index cards.
- *Results.* Fine-tuned, FSRS-7 scores BCE 0.3237 / RMSE(bins) 0.0577 / AUC 0.7517; SBD scores 0.3279 / 0.0593 / 0.7441 (≈1% worse BCE and AUC) with 80% fewer weights. Core argument: test-set accuracy is not enough because logs come from existing schedulers (Lucas critique). The paper also notes that A/B tests between state-of-the-art schedulers are absent from the literature.
- *Design (VERIFY, DR).* Backtests only cover intervals the old scheduler chose, so keep a small randomized interval-jitter slice to check calibration off-policy. Review cost λ or a daily budget is a principled alternative to a fixed DR.

**19. MaiMemo (2025). Memory Algorithm Experiment 2025, Preliminary Report (Exp.01).** [report](https://memodocs.maimemo.com/docs/2025_experiment) [FT*] (not peer reviewed; charts unreadable)
- *Method.* Live A/B on MaiMemo Flashcards, default parameters, 30 days. MMX-5 (internal FSRS-3-like, 12 parameters; 4,570 users) vs MMX-6 (FSRS-6 variant with changed success threshold, no Hard penalty and a Forgot penalty; 4,412 users). Run after an AA test.
- *Results.* Offline (12,370 users, 50/50 split) MMX-6 was best on LL, RMSE and AUC. Online, "Completed" retention was ~10% lower relative at day 30 (p=0.11, not significant). Paid rate was similar. Review retention was ~75% in both arms against an 85% target.
- *Design (VERIFY, DR).* Offline gains did not carry over to product outcomes. Report realized vs target retention and test changes with outcome metrics, not only log loss.

**20. Shen et al. (2026). Evolvable Psychology Informed Neural Network for Memory Behavior Modeling. *Inf. Process. Manag.* 63(1):104312.** [arXiv:2408.14492](https://arxiv.org/abs/2408.14492) [AB]
- *Method.* PsyINN evolves symbolic memory equations jointly with a neural network. It claims better accuracy on four large real memory-behavior datasets, but the landing page gives no numbers.
- *Not fetched.* Sun et al., KDD 2025 (doi 10.1145/3711896.3736886); Shen et al., AAAI 2026 (doi 10.1609/aaai.v40i3.37186, access denied); ROKAN; Xiao & Wang 2024 (DRL-SRS). All are cited in #18.
- *Design (VERIFY).* Skip for now. The interpretability trade-off in #18 matters more.

## F. Optimal retention and workload

**21. Cepeda, Vul, Rohrer, Wixted, Pashler (2008). Spacing effects in learning: a temporal ridgeline of optimal retention. *Psychol Sci* 19(11):1095–1102.** [PubMed](https://pubmed.ncbi.nlm.nih.gov/19076480/) [AB]
- *Results.* More than 1,350 people, gaps up to 3.5 months, tests up to a year later. The best gap fell from ~20–40% of a 1-week test delay to ~5–10% of a 1-year delay.
- *Design (DR).* Gap should depend on time to the exam, so consider raising DR as a known test date approaches.

**Synthesis for choosing DR.**
- The [Optimal Retention wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Optimal-Retention) says workload per remembered card has an interior minimum. Anki's "compute minimum recommended retention" button was later removed (`verifying_srs.md` §3).
- #13 puts the best within-session threshold at ~0.86–0.94.
- #1 and #2 say the best R depends on memory stage and difficulty.
- #8 says capacity limits matter as much as DR.
- #18 and #4 offer cost-weighted per-card DR, with weak evidence so far.
- #19 reports realized retention of 75% against an 85% target.
- Reasonable default: 0.85–0.90, then measure realized retention.

**Gaps.** I found no peer-reviewed FSRS-6/7 paper, no published study scheduling varied-problem math skills with an FSRS-type model, and no RCT of FSRS vs SM-2 (searched, not exhaustive). Not fetched: KDD ACM page (403), IEEE page (empty), PNAS (403), Zaidi 2020, TADS, Nioche 2021, SM-2 and SM-20 pages, Lindsey's thesis.
