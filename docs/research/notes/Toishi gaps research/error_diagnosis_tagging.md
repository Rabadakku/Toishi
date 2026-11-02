# Error Diagnosis and AI Skill Tagging for a Single-Learner Math Practice App

Scope: how an offline, single-learner "Anki for problem solving" (FSRS per skill, fresh problem per review, Elo tiers 1-5, prerequisite graph, final-answer entry only) can tell a concept gap from a prerequisite gap, a problem-solving gap, a slip or a hard problem, and how to tag problems with skills reliably using an LLM in an offline pipeline.

Evidence labels used below: **[Strong]** = randomized/meta-analytic or large replicated evidence; **[Moderate]** = a few controlled studies or a systematic review with mixed results; **[Weak]** = single small study, abstract-only, or practitioner opinion; **[Own proposal]** = my design synthesis, not tested in the literature.

---

## 1. Step-level error localization: first-error identification, self-diagnosis accuracy, how tutors localize errors

### Takeaway
Step-level interaction is the main thing that makes computer tutors work (step-based ITS d≈0.76 vs answer-based d≈0.31 in VanLehn's review), so having the learner find the first wrong step after a miss is a sound idea, **but** students' self-diagnosis is unreliable without scaffolding (on a hard physics problem, diagnosis scores ran from 0.24 with minimal support to 0.73 with an outline and rubric), so the tap should count as noisy evidence that a probe problem then confirms. It should not be treated as ground truth.

### Cited Findings
- **[Strong]** VanLehn's review of tutoring effects compared with no tutoring: answer-based systems (hints and feedback on short answers; "student solves on paper and enters an answer") mean effect 0.31 (40% of 165 effects reliable); step-based systems (feedback on each step) 0.76 (68% of 28 effects reliable); substep-based (discuss the reasoning behind steps) 0.40; human tutoring 0.79. He calls this the "Interaction Plateau": human = substep = step > answer > none. — [VanLehn, MIT Quality Symposium slides summarizing VanLehn 2011](https://quality.mit.edu/files/2012/01/Quality-Symposium-Kurt-VanLehn.pdf)
- **[Strong, but note]** The app's design (paper work, final answer typed) is by definition an *answer-based* system in VanLehn's taxonomy. The step-based benefit comes from feedback **during** each step, not from looking back at the steps afterward. The same slides define step-based as "hints and feedback on steps normally taken when using tool." — [VanLehn slides](https://quality.mit.edu/files/2012/01/Quality-Symposium-Kurt-VanLehn.pdf)
- **[Moderate]** Self-diagnosis accuracy depends on scaffolding and problem difficulty. In an algebra-based physics course, self-diagnosis (SD) scores on a hard quiz were 0.73 with a TA outline plus rubric (N=31), 0.57 with a detailed worked example (N=28), and 0.24 with only the final answer, notes and textbook (N=25) (p<0.05). On an easier quiz, all groups scored about the same (0.56-0.62). — [Mason, Cohen, Singh & Yerushalmi, "Self-Diagnosis, Scaffolding and Transfer"](https://arxiv.org/pdf/1603.03070)
- **[Moderate]** Students had more trouble diagnosing some kinds of errors than others. Most students who failed to *invoke* the needed principle on the hard problem could self-diagnose that, but about 60% could not correctly *apply* principles they had invoked. On the easier problem, many could not diagnose their failure to invoke momentum conservation. The authors warn "the SD grade does not necessarily imply meaningful SD": heavy support may lead to shallow matching against the sample solution. — [Mason et al.](https://arxiv.org/pdf/1603.03070)
- **[Weak]** In a companion study (~200 students), the group given an outline and rubric scored 0.526 on a later midterm problem vs 0.424 for controls (p=0.112, not significant at .05). Self-diagnosis scores did not significantly predict midterm scores. Students often did not see the midterm problem as similar to the quiz problem (far transfer). — [Yerushalmi, Mason, Cohen & Singh, "Effect of Self Diagnosis on Subsequent Problem Solving Performance"](https://arxiv.org/pdf/1603.06647)
- **[Moderate]** Weaker learners struggle to explain errors unless the wrong step is clearly highlighted (Große & Renkl). Highlighting errors lowered task demands and helped lower-prior-knowledge learners. — [LearnLab wiki, Corrective self-explanation](https://learnlab.org/research/wiki/index.php/Corrective_self-explanation); [Dieterich, Rumann & Rodemer 2025 systematic review, Educ Psychol Rev 37:94](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate]** "Careless" errors (slips): in BKT-based tutor research, a slip is by definition an error made when the student *knows* the skill, so the label depends on the knowledge estimate. A cited older estimate (Clements 1982) put about 20% of errors as careless. Carelessness correlated *positively* with engaged concentration (r=0.58/0.54) and negatively with boredom and confusion. The authors suggest it is a risk for successful, engaged students (overconfidence, fast work). Slip labels estimated from future performance were noisy and extreme. — [San Pedro, Baker & Rodrigo, "Carelessness and Affect in an Intelligent Tutoring System for Mathematics," IJAIED](https://learninganalytics.upenn.edu/ryanbaker/AIED-D-13-00017_Revised%20v2.pdf)
- **[Moderate]** Self-diagnosed "bugs" are unstable in general. In algebra, many bugs found by bug analysis did not recur consistently across items, and stable bugs were infrequent. The authors conclude that diagnoses need stability before they can drive remediation. — [Birenbaum, Kelly & Tatsuoka 1992, ETS RR-92-58](https://www.ets.org/research/policy_research_reports/publications/report/1992/hxjo.html)

### Inferences
- **Verdict on "tap the first step where your work differed" [Own proposal, grounded in above]: CONFIRM with refinements.** It is the closest an answer-only app can get to step-level data. Because self-diagnosis is unreliable (0.24-0.73 depending on support), the design should:
  1. Present the worked solution in a **scaffolded, rubric-like format**: numbered steps, each with a one-line "what this step does" label and its skill tag. This mirrors the best-performing self-diagnosis condition (outline + rubric).
  2. Make **Step 0 = "Set up / choose the method"** explicit, so a miss on the method is tappable.
  3. Offer escape options: **"I used a different valid method"** (the tap does not apply; record only "end result wrong"), **"My steps matched but my answer didn't"** (a slip, misread or entry error) and **"Can't tell."**
  4. Treat the tap as a **likelihood, not a verdict**. Example: give 0.6 of the blame to the tapped step's skill and spread 0.4 across the other step skills in proportion to their current weakness (lower FSRS retrievability or Elo).
  5. **Confirm with a probe** (already in the design, and strongly justified by bug instability): 1 single-skill problem at or below the learner's current tier on the blamed skill. A failed probe confirms the gap (FSRS lapse on that skill, plus a check on its prerequisites). A passed probe rejects it (mark the event as slip or integration error; at most a "Hard" on the original skill). Add a 2nd probe only if the first is ambiguous (e.g., skipped).
- **Distinguishing the five causes. A decision table [Own proposal]:**
  - *Prerequisite gap*: the tapped step's skill is a **prerequisite** (e.g., algebra simplification inside a derivative problem). The probe on that prerequisite fails.
  - *Concept gap (target skill)*: the tapped step uses the item's **target** skill. The probe on it fails, and the misses cluster on that skill across different items (see Q4).
  - *Problem-solving / method-selection gap*: the tap is at Step 0, **and** a "cued twin" probe succeeds. A cued twin is a same-family problem with the method named ("Use the chain rule..."). Solving it when cued but not uncued is the operational definition of a selection gap. If the cued twin also fails, it is a concept/execution gap in that method. (This follows Rohrer's choose-vs-execute distinction in Q3.)
  - *Slip*: the learner reports a slip or "steps matched." Accept it only when the skill is currently strong (e.g., FSRS retrievability ≥0.9 and the last 2-3 attempts on the skill were correct), and keep a budget (e.g., slips ≤ ~20% of 30-day misses, anchored loosely on the Clements estimate). A second "slip" on the same sub-skill within 30 days becomes a step error and triggers a probe.
  - *Hard problem*: the item's tier is clearly above the learner's level (Elo P(correct) < ~0.35), the tapped step is a skill the learner has recently passed at lower tiers, and the probe passes. Then do not lapse the skill; record it as an "above level" miss (see Q4).
- **Self-calibration loop [Own proposal]:** log every (self-label, tapped skill, probe outcome) triple. Over time, compute how often the probe confirms the learner's tap and how often "slip" labels are followed by failed probes. If confirmation is low (<50%), weight the tap less and lean more on residual statistics. This uses the single learner's own data to estimate how reliable his self-diagnosis is.

### Gaps
- I found no study measuring how accurately learners identify their **first erroneous step** in their own math work by comparing it with a step-numbered worked solution, which is the exact mechanism proposed. The physics self-diagnosis studies are the closest analog and use rubric scores, not first-error accuracy.
- I did not retrieve primary sources on how Cognitive Tutors (model tracing), Andes or ASSISTments localize errors internally. Model tracing (matching each student step against correct and buggy production rules) is background knowledge that was not verified this session. ASSISTments "scaffolding questions" (breaking a missed problem into steps) were also not verified.
- No evidence was found on whether the act of tapping the first error is itself a learning activity (a self-explanation benefit) apart from its diagnostic value.

---

## 2. Incorrect / erroneous worked examples ("find the error" items)

### Takeaway
Erroneous examples help reliably only under certain conditions. The most consistent benefit is from **contrasting an erroneous example with a correct one**. Benefits often show up only on **delayed** tests, and learners with low prior knowledge need the error **highlighted** (or need correct examples first). So "find-the-error" items fit the app best for skills that are already partly learned, with a correct contrast and a prompt to explain and fix the error after the learner picks a step.

### Cited Findings
- **[Moderate]** A 2025 systematic review (40 studies, 33 articles; 26 in mathematics) found method variation too large for a meta-analysis. Vote counts: erroneous examples (ErrEx) vs correct examples: 9 of 21 comparisons favored ErrEx, 11 showed no difference, 1 favored correct. **Contrasted** erroneous + correct (Con-ErrEx) vs correct: 9 of 12 favored Con-ErrEx. ErrEx vs plain problem solving: 7 of 14 favored ErrEx, 6 no difference, 1 favored problem solving. Con-ErrEx vs problem solving: 6 of 8 favored Con-ErrEx. — [Dieterich, Rumann & Rodemer 2025, Educ Psychol Rev](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate]** In the same review, prior knowledge as a moderator was **mixed** (no universal advantage for high or low prior knowledge). Error highlighting helped low-prior-knowledge learners. Prompts to identify, correct, explain or reflect often deepened learning but could overload learners on complex material. Some ErrEx benefits over problem solving appeared **only at delayed posttests**. — [Dieterich et al. 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate] Große & Renkl (2007)** as summarized in the review: for far transfer, high-prior-knowledge learners benefited more from mixed correct + erroneous examples, while low-prior-knowledge learners benefited more from correct examples only. For near transfer, low-prior-knowledge learners benefited when errors were highlighted and they were only prompted to explain. — [Dieterich et al. 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate] Adams et al. (2014)**, decimals, middle school, web tutor: the ErrEx condition (24 erroneous examples + 12 problems) vs problem solving (36 problems). Students explained (chose explanations for) and **fixed** another student's error. There was no difference on the immediate posttest; ErrEx was better on the **1-week delayed** test, controlling for prior knowledge. The benefit held for both lower- and higher-prior-knowledge students, and ErrEx students judged their own test performance more accurately. Students **liked** ErrEx less. — [Learning Scientists blog summary](https://www.learningscientists.org/blog/2023/7/27); [Dieterich et al. 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate] Durkin & Rittle-Johnson (2012)**, decimal magnitude: Con-ErrEx reduced misconceptions more than correct examples. Outcomes were better when correct-answer feedback came only after later problem solving instead of with each prompt. No prior-knowledge effects were found. — [Dieterich et al. 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Moderate] Booth et al. (2013)**, algebra: Con-ErrEx vs correct examples showed no significant difference (Exp. 1). ErrEx vs Con-ErrEx showed no significant difference (Exps. 1-2). Con-ErrEx vs problem solving with identical feedback favored Con-ErrEx. — [Dieterich et al. 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)
- **[Strong, field scale] AlgebraByExample** (Booth et al. 2015; >6,000 students, >130 teachers, randomized): assignments mixed worked examples (targeting common misconceptions) with problems at about a **50/50 ratio**. Struggling students scored about **10 percentage points** higher in conceptual knowledge, and all students gained about 4 points in procedural knowledge, **despite solving half as many problems**. Students also scored 7 points higher on released state-test items. — [SERP Institute, AlgebraByExample research](https://serpinstitute.org/algebra-by-example/research)
- **[Strong]** A meta-analysis of worked examples in math (40 articles, 49 studies, 185 effect sizes) found g = 0.43 overall (95% CI 0.31-0.55). Example type (correct, incorrect, comparison, faded) was **not** a significant moderator, though only 7 articles used incorrect examples. — [Clerjuste, Chawla, Barbieri & Miller-Cotto, meta-analysis poster, U. Delaware](https://www.cehd.udel.edu/wp-content/uploads/2022/02/Worked-Examples-Meta-Poster_022722_SC.pdf)
- **[Moderate]** Corrective self-explanation (Siegler 2002; Siegler & Chen 2008): explaining why wrong answers are wrong *and* why correct answers are right beat explaining correct answers only. It works best when paired with building the correct knowledge. Without a replacement strategy, students may reject the wrong strategy and have nothing to use, or fall back on it. — [LearnLab wiki](https://learnlab.org/research/wiki/index.php/Corrective_self-explanation)
- **[Weak]** The AdaptErrEx ITS project design asked students to "find the error" in a fictitious student's work, with optional help. — [IES award page](https://ies.ed.gov/use-work/awards/adapterrex-exploring-learning-benefits-erroneous-examples-and-their-dynamic-adaptations-within)

### Inferences
- **Verdict on "find-the-error" items: CONFIRM, with format and timing changes [Own proposal grounded in the review]:**
  - **Format:** (1) pick the wrong step (localize), (2) choose or type why it is wrong (explain; a multiple-choice list of 3-4 explanations is fine, as in Adams et al.), (3) give the corrected value at that step (fix), (4) then show the **correct solution side by side** (contrast). The contrast step matters because Con-ErrEx was the most consistent winner.
  - **Present it as "another student's work"** (Adams et al. did this). It also keeps the item from being confused with the learner's own diagnosis flow.
  - **Gate by mastery:** introduce find-the-error items for a skill only after it has some stability (e.g., ≥2 successful uncued reviews), because low-prior-knowledge learners benefited more from correct examples for far transfer (Große & Renkl). For early-stage skills, use a highlighted-error variant ("Step 3 is wrong. Why?").
  - **Choose errors from known misconceptions, not random typos.** Errors drawn from a bug library (Q5) target the misconceptions that the Durkin & Rittle-Johnson and AlgebraByExample work aimed at.
  - **Frequency:** AlgebraByExample's 50/50 ratio is for initial instruction. For an FSRS review queue, a much lower rate (e.g., ≤1 in 8-10 reviews, or triggered after a confirmed diagnosis on that skill) is a reasonable starting point. This number is my assumption and is not evidence-based.
  - **Scheduling:** since benefits appear on delayed tests, judge find-the-error items by later uncued performance on the skill, not by in-session accuracy. They can feed FSRS for a separate "error-detection" card type, or simply count as a review of the skill with a lower weight.
- **Expect low enjoyment** (Adams et al.). For a self-directed single learner, keeping these items short and infrequent may matter for sticking with the app.

### Gaps
- There is no pooled effect size specifically for erroneous examples. The 2025 review declined to meta-analyze, and the Clerjuste et al. poster did not break effects down by example type.
- I found no erroneous-example studies in **calculus** specifically. Most are on decimals, fractions and algebra.
- No evidence on the best ratio or frequency of erroneous examples inside a spaced-retrieval schedule.

---

## 3. Problem-solving skills vs content knowledge: is method selection a separable, trainable skill? Should it be a node in the graph?

### Takeaway
There is strong evidence that **choosing** a strategy is a demand separate from **executing** it. Interleaved practice, which forces the choice, improved a delayed test from 38% to 61% (d=0.83) in a large preregistered RCT. Schema-based instruction for word problems also improves performance and retention. This supports modeling **domain-specific discrimination skills** (e.g., "choose an integration technique," "recognize a related-rates setup") as tracked skills. Generic skills like "multi-step planning" or "checking answers" have much weaker evidence as trackable units.

### Cited Findings
- **[Strong]** Rohrer, Dedrick, Hartwig & Cheung (2019/2020, J. Educ. Psych.): a preregistered cluster RCT with 54 seventh-grade classes and 787 students. On an unannounced test about one month later, interleaved practice scored **60.7%** vs blocked **37.6%**, d = 0.83 (95% CI 0.68-0.97). All 15 teachers showed a positive effect (d 0.23-1.48). — [Rohrer et al. PDF](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **[Strong]** The authors' mechanism: "interleaved practice requires students to choose a strategy and not merely execute a strategy." Choosing is hard because many problems lack clear cues, so students must "make fiendishly difficult discriminations." Superficially similar problems may need different strategies (e.g., Law of Sines vs Law of Cosines). — [Rohrer et al.](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **[Strong]** The authors caution that interleaving may be less effective or too hard if students get no blocked practice when first meeting a new skill. They do not recommend eliminating blocked practice. — [Rohrer et al.](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **[Strong]** Schema-based instruction (SBI): a randomized trial with 806 seventh graders with math problem-solving difficulties found that SBI students outscored controls on proportional word problems at posttest and on a **9-week delayed** test. — [Jitendra, Harwell, Dupuis & Karl 2017, J. Learning Disabilities](https://experts.umn.edu/en/publications/a-randomized-trial-of-the-effects-of-schema-based-instruction-on-/)
- **[Moderate]** In an integral-calculus error analysis (147 students), "technique determination" errors, such as choosing integration by parts where u-substitution fit, were classed as a *conceptual* error type, separate from procedural and technical errors. — [Voon, Julaihi & Tang 2017, Asian J. Univ. Education](https://files.eric.ed.gov/fulltext/EJ1207815.pdf)
- **[Weak, bibliographic only]** Dufresne, Gerace, Hardiman & Mestre (1987) studied guiding novices through a hierarchical, principle-first analysis of mechanics problems ("hierarchically structured problem solving"). I could only retrieve the citation, not the results. — [SRRI record](https://srri.umass.edu/publications/dufresne-1987hsp)

### Inferences
- **Verdict on tracking "problem-solving skills" as their own skills: CONFIRM for domain-specific selection skills; REFINE for generic ones [Own proposal].**
  - Model **one method-selection skill per family of confusable methods**: e.g., `select:differentiation-rule` (product/quotient/chain/implicit), `select:limit-technique` (direct substitution / factor / conjugate / L'Hôpital / squeeze), `select:integration-technique` (u-sub / parts / partial fractions / trig sub), `setup:related-rates`, `setup:optimization`. The evidence is about discriminating among specific, superficially similar strategies, not about a general "problem-solving ability."
  - In the graph, a selection skill's prerequisites are the methods it chooses among (you cannot choose u-sub well before you can do u-sub). It should become active only once ≥2 of those methods are introduced, matching Rohrer's caution about a blocked first exposure.
  - **"Which method fits?" items** are well justified: show an uncued problem and ask the learner to pick a method (multiple choice) without solving it. They are fast (5-15 s), so they give many discrimination reps per minute. Mix them with full problems, not instead of them.
  - **Generic skills** ("multi-step planning," "checking answers") are hard to diagnose from a final answer and have no direct evidence here. Treat "checking" as a **habit prompt** (e.g., after a slip, a "did you check units/sign?" note), not as a FSRS-scheduled skill. "Setting up word problems" is better split by schema type (rate, optimization, related rates, accumulation), following SBI.
  - **Diagnosing a selection gap:** see Q1. A Step-0 tap plus success on a cued twin is the cleanest single-learner signal.

### Gaps
- I did not retrieve evidence on Pólya-style **general** heuristics training, or meta-analytic effect sizes for problem-categorization training (e.g., Dufresne et al. 1992, Chi et al. categorization work). Their effectiveness for calculus is unverified here.
- No study was found that models method selection as a separate knowledge component in a KC/Q-matrix model and tests whether that improves prediction.

---

## 4. Diagnosing with little data: single-learner weak-spot detection, AFM/PFA/DINA lessons, separating item difficulty from skill weakness

### Takeaway
Population methods (AFM, PFA, Elo item calibration, Q-matrix refinement) need many students. Elo item difficulty needs about 100 students, and even with thousands, AFM parameters can be biased and Q-matrix refinement by learning-curve fit is error-prone. With one learner, the app should **fix item difficulty from tier priors** and treat the 30-day weak-spot finder as a **screening test followed by a confirmatory diagnostic set** (two-stage). Raw miss-vs-correct "lift" should be replaced with **difficulty-adjusted residuals** plus minimum-evidence thresholds.

### Cited Findings
- **[Strong]** Elo in educational systems: P(correct) = logistic(skill − difficulty). Both values update after each answer in opposite directions. Elo shares the Rasch predictive function. An uncertainty function U(n) = a/(1 + b·n) replaces a fixed K (suggested starting values a=1, b=0.05; K=0.4 was used in earlier work). Multi-skill variants update every skill scaled by its correlation with the item's component. — [Pelánek 2016, "Applications of the Elo Rating System in Adaptive Educational Systems," Computers & Education](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- **[Strong]** The same paper says a system needs **at least ~100 students** to estimate item difficulty well. It does not address the single-student case. Elo is designed so skill changes over time while item difficulty stays roughly constant. — [Pelánek 2016](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- **[Strong]** AFM structure: student ability (α), concept easiness (β) and learning rate (γ) in a logistic model. With simulated ground truth (2,000 students), "the best performing model is not necessarily the correct one." Fitted AFMs shrink β and γ toward zero, and a misspecified Q-matrix could beat the true one under ordering/attrition biases, so **flagging concepts for revision from AFM parameters is risky**. — [Čechák & Pelánek, "Better Model, Worse Predictions: The Dangers…", AIED](https://www.fi.muni.cz/~xpelanek/publications/aied21afm.pdf)
- **[Strong]** In 90 simulated scenarios, AFM (as used in DataShop) had consistent accuracy problems when accepting proposed domain-model (KC) refinements. PFA and Recent-PFA were much more accurate but still struggled in some cases. One such case was telling apart two skills when error rates stayed high after much practice. — [Goldin & Galyardt 2018, JEDM 10(2)](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/316)
- **[Moderate]** Slip estimates from future performance are noisy and tend toward extremes. Cases with prior knowledge near 1 were removed because they overestimate slips. — [San Pedro, Baker & Rodrigo](https://learninganalytics.upenn.edu/ryanbaker/AIED-D-13-00017_Revised%20v2.pdf)
- **[Moderate]** Bug-level diagnoses were unstable, while rule-space (latent-attribute) diagnoses were relatively more stable. This argues for diagnosing **skills/attributes** over specific bugs. — [Birenbaum, Kelly & Tatsuoka 1992](https://www.ets.org/research/policy_research_reports/publications/report/1992/hxjo.html)

### Inferences
- **Verdict on the weak-spot finder ("compare how often each sub-skill appears in misses vs correct answers over 30 days"): REFINE.** Raw lift is confounded in two ways: (a) by difficulty, since skills tagged on hard tier-5 items look weak; (b) by co-occurrence, since a ubiquitous secondary skill like algebraic simplification shows up in most misses simply because it appears in most items. The fix is a difficulty-adjusted, blame-weighted residual test. **[Own proposal]**

#### Algorithm A: Difficulty-adjusted, blame-weighted weak-spot screen [Own proposal]
```
Inputs (last 30 days): attempts i with outcome y_i ∈ {0,1}, item tier t_i,
  tags with weights q_ik (primary = 1.0, secondary "uses" = 0.4),
  blame weights b_ik from the diagnosis flow (Q1) for misses (sum to 1 over k), else none.
Difficulty prior: d(tier) fixed, e.g. tier1..5 = -1.5, -0.75, 0, 0.75, 1.5 (logit scale).
Global/domain ability θ from Elo (learner side only; K via U(n)=a/(1+bn)).
For each attempt: p_i = σ(θ_at_time_i − d(t_i))        # expected P(correct)
For each skill k:
   if miss and b_ik exists:  e_ik = b_ik            # use the tap/probe blame
   else:                     e_ik = q_ik / Σ_k q_ik # spread by tag weight
   R_k = Σ_i e_ik · (y_i − p_i)                     # negative = worse than expected
   V_k = Σ_i e_ik² · p_i(1 − p_i)
   z_k = R_k / sqrt(V_k + τ)                        # τ≈0.5-1 shrinks tiny samples to 0
   n_eff_k = (Σ e_ik)² / Σ e_ik²
Flag k when ALL hold:
   z_k ≤ −2.0 (screen) ;  n_eff_k ≥ 5 ;  misses on ≥ 3 distinct items ;
   misses on ≥ 2 distinct days ;  k not already in an active diagnostic/relearn state.
Rank flagged skills by z_k; schedule at most 1-2 diagnostic sets per week.
```
- **Why these thresholds:** with ~100 active skills, a one-sided z ≤ −2.0 screen would flag about 2 skills a week by chance alone (2.3% each). That is acceptable **only** because the next stage, a 3-4 item diagnostic set, is the actual test. If diagnostic sets feel too frequent, tighten to z ≤ −2.5 (≈0.6% per skill) or apply Benjamini-Hochberg across skills. These numbers are my calibration suggestions, not published values.

#### Algorithm B: Diagnostic set as the confirmatory stage [Own proposal]
```
For flagged skill k: draw 3-4 fresh items where k is the ONLY primary tag,
  secondary tags limited to skills with high FSRS retrievability, tiers at or
  below the learner's level (p_i ≥ 0.6).
Score: if ≥ 2 misses → confirmed gap: FSRS lapse on k, check prerequisites
  (run one probe per prerequisite with low retrievability, deepest first).
  if 0-1 misses → reject: reset k's screen statistic (exclude these 30 days
  of residuals from future flags) and look at co-tagged skills instead.
```
- **Prerequisite tracing [Own proposal]:** when k is confirmed weak, walk the prerequisite graph *downward* and probe only prerequisites that are both (a) tagged on the steps the learner blamed and (b) below a retrievability threshold. This keeps probes few. It resembles the "find the deepest failing node" idea in knowledge-space and rule-space methods (rule space mentioned in Birenbaum et al.), applied here heuristically.

#### Separating "hard problem" from "concept gap" with one learner [Own proposal]
- **Verdict on "compare Elo difficulty of missed vs solved problems": REFINE.** With one learner, Elo cannot calibrate item difficulty (it needs ~100 students per Pelánek), and each fresh item is seen about once. So:
  1. **Anchor item difficulty to the tier** (assigned in the pipeline by the author or AI). Optionally let it drift with a very small K (e.g., ≤0.05) for items seen repeatedly. Do not let a single learner's misses push item difficulty up, or the app will conclude "the item was hard" exactly when the learner is weak.
  2. Classify each miss by its expected probability: if p_i < 0.35, call it an **above-level miss** and down-weight it in FSRS (e.g., grade "Hard" instead of "Again" when the probe passes). If p_i ≥ 0.6, call it a **below-level miss**: strong evidence of a gap or slip, so send it to the probe.
  3. Concept gap = a skill whose residual is negative on **at-or-below-level** items across ≥3 distinct items. Hard problem = misses concentrated on above-level items with no consistent skill in the blame weights.
  4. If the learner later succeeds repeatedly on a tier-5 item family, that is evidence the tier label may be too high. Surface it to the content pipeline as "possible tier mislabel" instead of auto-adjusting.
- **What to borrow from AFM/PFA/DINA (lightweight) [Own proposal]:**
  - *From PFA:* keep separate success and failure counts per skill (recent window). This already sits inside FSRS plus the residual statistic. PFA did better than AFM at judging KC-model refinements (Goldin & Galyardt).
  - *From AFM:* the additive logit (ability + skill easiness + practice) underlies the residual idea, but **do not interpret fitted parameters** for one learner (Čechák & Pelánek).
  - *From DINA-style conjunctive models:* a multi-skill item is answered correctly only if all required skills work. Blame for a miss should therefore go mostly to the **weakest** required skill. Use the current retrievability: blame_k ∝ (1 − R_k) when no tap is available.

### Gaps
- I did not retrieve primary sources with the PFA or DINA equations, or any published single-learner (N=1) diagnostic method. The DINA slip/guess conjunctive formulation and the PFA success/failure-count logit are standard background but were not verified in this session.
- No published thresholds for minimum evidence in single-learner weak-spot detection were found. The thresholds above are my proposals and should be tuned on the learner's own logs (e.g., the rate at which diagnostic sets confirm flags).
- No source was found on combining FSRS memory states with diagnostic residuals.

---

## 5. Bug libraries and common misconceptions in algebra and calculus

### Takeaway
Executable bug/misconception libraries exist and are recent (MalruleLib, Jan 2026: 101 misconceptions, all pre-calculus). Calculus error research mostly offers **taxonomies** (conceptual / procedural / technical; structural / executive / arbitrary) and topic lists, not a ready catalog. Specific bugs are often unstable within a student, so wrong-answer feedback should name a *likely* misconception and route to a probe. It should not assert a diagnosis.

### Cited Findings
- **[Moderate]** MalruleLib (Chen, Liu & Sonkar, arXiv Jan 2026): **101 documented misconceptions ("malrules") across 498 parameterized problem templates**, in 22 categories and 10 NCTM strands, from arithmetic through early high school (fractions, decimals, signed numbers, exponents and radicals, expressions and equations, functions, geometry, coordinate geometry). **Calculus is not included.** Each malrule is code: a problem generator, a correct solver, a malrule solver producing a step trace that ends in the wrong answer, and unit tests. Every malrule traces to published research (67 sources, including Brown & Burton's BUGGY). — [MalruleLib](https://arxiv.org/pdf/2601.03217)
- **[Moderate]** In MalruleLib's tests, nine LLMs (4B-120B) predicted a student's next answer from one worked mistake with only ~40% accuracy when the new problem used a different template (~46.5% when given the student's steps), 10-21 points below same-template accuracy. — [MalruleLib](https://arxiv.org/pdf/2601.03217)
- **[Moderate]** Bugs found by bug analysis were often unstable within students, and stable bugs were infrequent. — [Birenbaum, Kelly & Tatsuoka 1992](https://www.ets.org/research/policy_research_reports/publications/report/1992/hxjo.html)
- **[Weak-Moderate]** Integral calculus error study (147 students over six semesters, plus qualitative work with 70): used Seah's (2005) **conceptual / procedural / technical** classification. It also notes Donaldson's (1963) **structural / arbitrary / executive** errors and Avital & Libeskind's (1978) conceptual / mathematical / technical difficulties. Listed errors include: misusing or ignoring dx and dθ; wrong inverse-function antiderivatives; using the log rule where the power rule applies; choosing parts where u-sub fit; one-sided limit notation and "division by zero" errors in improper integrals; confusing differentiation with integration for trig and inverse-trig functions; and arithmetic, cancellation and binomial-expansion errors. Error rates by type: improper integrals of standard functions 63.1%; parts / trig-sub / partial fractions 42.8%; u-sub **without** hint 36.5% vs **with** hint 25.4%; completing the square 18.7%. — [Voon, Julaihi & Tang 2017](https://files.eric.ed.gov/fulltext/EJ1207815.pdf)

### Inferences
- **Proposal: a small, curated calculus "malrule" table in the content pipeline [Own proposal].** For each skill, list 3-8 known wrong transformations and implement each as a function that maps a problem to the wrong answer it produces. Examples (common, but not sourced above, so verify against the literature or the textbook's "common errors" boxes before use): d/dx f(g(x)) → f′(g′(x)) or forgetting the inner derivative; (fg)′ = f′g′; (f/g)′ with the sign of the numerator terms swapped; ∫1/x² dx → ln(x²); L'Hôpital applied to a non-indeterminate form; √(a²+b²) = a + b; dropping the constant of integration; sign errors when distributing a negative. At import, run every malrule on every generated problem. If the learner's typed answer matches a malrule output (and not the correct answer), show targeted feedback ("This is the answer you'd get if you differentiate only the outer function...").
- **Use malrule matches as evidence, not a verdict.** Given bug instability, a match should (a) pre-select the likely wrong step in the tap UI, (b) add blame to that skill, and (c) trigger the same confirmation probe. A malrule match is far stronger evidence than a bare miss, though, because a random error rarely produces exactly a predicted wrong answer. Blame weight could be ~0.8 instead of 0.6. **[Own proposal]**
- **Reuse:** MalruleLib's algebra/fractions/exponents malrules apply directly to the **prerequisite** layer (algebra inside calculus). Its code-per-malrule design (generator, correct solver, buggy solver, tests) is a good template for writing calculus malrules in the offline pipeline. The same buggy solvers can **generate find-the-error items** automatically (Q2).
- **Error-type labels in the UI:** the conceptual / procedural / technical taxonomy maps onto the app's self-labels: "didn't know where to start" ≈ conceptual or selection; "a step went wrong" ≈ procedural; "careless slip" ≈ technical. This gives a literature-backed vocabulary.

### Gaps
- I could not retrieve a comprehensive, published catalog of **differential calculus / limits** misconceptions (e.g., Orton 1983 on differentiation and integration; Tall & Vinner on limit concept images). These are known classics but their contents were not verified this session.
- No executable calculus malrule library was found as of Nov 2026.
- The u-sub hint vs no-hint numbers come from different exam items across semesters (observational), not a controlled comparison.

---

## 6. Method cues in problem statements ("Use L'Hôpital's rule")

### Takeaway
The best evidence (Rohrer's interleaving work) shows that knowing the strategy in advance removes the choice, the very demand that produced the d=0.83 benefit. Problem statements that name the method act like blocking at the item level. Strip or flag cues for review items, but keep cued versions for first exposure and for the "cued twin" diagnostic probe.

### Cited Findings
- **[Strong]** Under blocked practice, "students know the strategy for each problem before they read the problem." This fluency may be illusory and lead students and teachers to overrate blocked practice. In blocked sets, the needed formula is often visible on the previous problem's solution, so retrieval is skipped. — [Rohrer et al. 2019/2020](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **[Strong]** Rohrer et al.'s example of a hard discrimination: a word problem solvable with the Pythagorean theorem that **omits words like "hypotenuse,"** so the strategy cannot be read off the wording. — [Rohrer et al.](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- **[Weak, observational]** In integral calculus exams, u-substitution items **with a hint** had a 25.4% error rate vs 36.5% **without** a hint. — [Voon et al. 2017](https://files.eric.ed.gov/fulltext/EJ1207815.pdf)
- **[Moderate]** In MathFish, some LLM-generated problems "embedded the solution" or targeted a skill other than the requested standard. Content generated by LLMs needs checking for giveaways too. — [Lucy et al. 2024, MathFish, Findings of EMNLP](https://aclanthology.org/2024.findings-emnlp.323.pdf)

### Inferences
- **Verdict on stripping or flagging method cues: CONFIRM [Own proposal grounded in Rohrer].** Pipeline:
  1. **Detect** cues: regex for method names and imperatives ("use," "by," "apply," "using," "with the aid of," named rules and theorems: L'Hôpital, chain rule, product rule, integration by parts, u-substitution, partial fractions, squeeze theorem, MVT, IVT, implicit differentiation, logarithmic differentiation), plus an LLM pass for implicit cues ("let u = …", "Hint: …", a section heading carried into the stem, keywords like "hypotenuse").
  2. **Rewrite** to remove the method while keeping the math target the same: "Use L'Hôpital's rule to evaluate lim…" → "Evaluate lim…". "Use the substitution u = x² + 1 to find ∫…" → "Find ∫…". Keep any constraint that changes the answer (e.g., "use a left Riemann sum with n=4" stays, because the method *is* the answer specification). Mark such cases `cue_required: true` so they are not stripped.
  3. **Store both versions**: `stem_uncued` (default for reviews) and `stem_cued` (used for first exposure of a new skill per Rohrer's caveat, for highlighted-error find-the-error items, and for the "cued twin" probe that separates a selection gap from an execution gap, Q1).
  4. **Watch for cues that the rewrite cannot remove**: problems whose surface form uniquely identifies the method (e.g., every ∫xeˣdx item screams "parts"). These still benefit from interleaving because the learner must notice the form, but they give weaker evidence for the `select:*` skill. Tag `selection_evidence: low` so they count less toward method-selection skills.
- **Uncued items carry the method-selection tag** (`select:limit-technique` etc.). Cued items do not, since no selection happened.

### Gaps
- I found no controlled experiment that compares **cued vs uncued wording of the same item** and measures later uncued performance in calculus or algebra. The recommendation rests on the interleaving mechanism and the "know the strategy before reading" argument, not on a direct test of item wording.
- No published method or tool for automatically rewriting problems to remove method cues was found.

---

## 7. LLM skill / knowledge-component tagging of math problems: accuracy, prompting, human baselines, validation

### Takeaway
LLMs are good at **verifying** whether one skill fits one problem (GPT-4o about 88% accuracy vs a human expert's about 92% in a K-3 study). They are poor at **free selection from a large flat taxonomy**: in MathFish, GPT-4 exactly matched the gold standard set only 4.8% of the time, over-predicted (3.05 vs 1.66 tags) and usually landed on a neighboring standard. Zero-shot Q-matrix coding agreement varies widely (κ 0.12-0.63) and did not improve with newer models. The reliable recipe: **fixed taxonomy with descriptions and examples → retrieve or hierarchically narrow candidates → per-candidate yes/no verification grounded in solution steps → self-consistency confidence → human spot checks → learner-data checks.**

### Cited Findings
- **[Moderate] MathFish** (Lucy et al., Findings of EMNLP 2024; 9,923 problems, 385 Common Core standards): *verification* (does problem X fully align with standard Y?) got harder as distractor standards became more similar. In *assisted* hierarchical tagging (one level at a time), 3-shot GPT-4 reached mean per-level accuracy 0.850, falling at finer levels. In *self-guided* full-tree tagging, GPT-4 exact-match accuracy was **0.048** and overlap accuracy 0.502. It predicted **3.05 standards per problem vs 1.66 gold**, typically ~1.9 graph edges from a correct standard (vs 5.5 for random). The paper recommends hierarchical traversal over one flat list (to avoid context-length and "lost in the middle" effects), shuffling options, and a "none" option at each level. LLM verifiers were **lenient**: 96% of generated problems were judged aligned vs 52% by teachers. — [MathFish](https://aclanthology.org/2024.findings-emnlp.323.pdf)
- **[Moderate]** Binary knowledge-concept matching on 24 K-3 concepts (MathKnowCT, expert-labeled, ~1:4 match ratio): the **human expert** scored accuracy 91.75 / F1 88.51. A single GPT-4o (2-shot CoT) scored accuracy 88.38 / F1 85.46, with **recall 96.77 but precision 76.51** (over-tagging). A multi-agent decomposition (planner → sub-constraint judges → numeric checks in Python → AND) raised GPT-4o precision to 80.47 but lowered recall (accuracy 86.91). Gains were larger for small models. The authors prefer false negatives over false positives in education. (The fetched table was garbled, so the cell values should be checked against the paper.) — [Knowledge Tagging with LLM-based Multi-Agent System, arXiv 2409.08406](https://arxiv.org/pdf/2409.08406)
- **[Moderate]** GPT-4 **generating** KCs for MCQs matched human-assigned KCs for 56% of chemistry and 35% of e-learning questions (higher when top-5 were considered). Where they disagreed, domain experts preferred the LLM's KC about two-thirds of the time. — [Moore, Schmucker, Mitchell & Stamper 2024, ACM L@S, arXiv 2405.20526](https://arxiv.org/abs/2405.20526v1)
- **[Moderate]** KCGen-KT (Findings of ACL 2026), programming problems: GPT-4o generated KCs (few-shot + CoT, clustered with Sentence-BERT) gave knowledge-tracing AUC 0.816 vs 0.797 for human KCs (CodeWorkout). Instructor-judged tag precision was 93.2% (generated) vs 92.5% (human), with **89.3% inter-annotator agreement**. Generated KCs had better learning curves (weighted R² 0.21 vs 0.18 under PFA). **Removing few-shot examples produced overly abstract KCs.** Including correct solutions helped and including incorrect ones hurt. — [Duan et al. 2026](https://aclanthology.org/2026.findings-acl.1670.pdf)
- **[Moderate]** Zero-shot Q-matrix coding (20 reading items, 5 skills) vs a validated Q-matrix, Cohen's κ. May 2025: Gemini 2.5 Pro 0.63, Claude 4 Sonnet 0.33, DeepSeek V3 0.26, GPT-4.5 0.24, GPT-4o 0.12. Jan 2026: Gemini 3 Pro 0.42, Claude 4.5 Sonnet 0.26, DeepSeek V3.2 0.21, GPT-5.2 0.16. **Newer models did not improve.** One model reinterpreted the task and coded an entire skill category as absent. Four human raters were generally slightly better than most models. The authors recommend AI as supplementary evidence, empirical validation against response data, and repeated runs. — [Fan, Bialo & Li 2025/2026, arXiv 2602.08796](https://arxiv.org/pdf/2602.08796)
- **[Moderate]** "Generate-and-Validate" Q-matrix refinement (Zhang et al., arXiv Mar 2026; 26 items, ~614 students): LLM-proposed item-misconception tags had modest agreement with the expert Q-matrix (GPT-5, **high-confidence tags only**: recall 0.54, micro-F1 0.49). But they fit student responses *better* than the expert matrix (NeuralCDM AUC 0.780 vs 0.717). Prompt revisions guided by expert feedback on a small item set raised AUC from 0.715 to 0.780. They note **keyword-driven over-tagging** as a systematic error and say better fit does not prove cognitive validity. — [Zhang et al. 2026](https://arxiv.org/pdf/2604.16398)
- **[Weak, abstract only]** For KC tagging of math word problems (Common Core), LLM tagging had consistency problems, SBERT similarity alone underperformed, and combining the two improved results. — [Tan, Wei & Kim, ICCE 2025](https://library.apsce.net/index.php/ICCE/article/view/5574)

### Inferences
- **Human-agreement baseline to aim for:** among the sources, expert-level performance is about 88-92% on binary tag decisions (91.75% expert accuracy in the K-3 study; 89.3% inter-annotator agreement in KCGen-KT). A realistic target for the pipeline is **≥85-90% precision on primary tags**, judged by the learner's own spot checks. Disagreement on *granularity* is common and not always an error (experts preferred the LLM's KC about two-thirds of the time in Moore et al.).
- **Verdict on "AI tags untagged imports against a published skill list, including secondary 'uses' tags": CONFIRM, but change the procedure from "choose from list" to "solve → step-tag → verify" [Own proposal grounded in the findings].**

#### Algorithm C: Offline tagging pipeline [Own proposal]
```
0. Taxonomy file (versioned): per skill → id, name, 1-2 sentence definition,
   2 positive examples, 1-2 NEAR-MISS negatives (the confusable neighbor skill),
   parent/chapter, prerequisites. (Near-miss negatives target MathFish's
   main failure: confusing neighboring standards.)
1. SOLVE: the LLM writes a numbered worked solution (it is needed anyway for the
   tap-to-diagnose UI). If the item has an answer key, check the LLM's
   final answer against it (sympy where possible); reject or re-run on mismatch.
2. CANDIDATES: narrow hierarchically (course → chapter → section) or by
   embedding top-k (k≈10-15) + chapter context. Always include "NONE / NEW SKILL".
3. STEP-TAG: for each step, choose exactly ONE skill from the candidates
   (or NONE). The item's PRIMARY tags = skills of the key steps (≤2);
   SECONDARY "uses" tags = skills of routine steps (≤4). Grounding every tag in
   a step limits over-tagging (MathFish 3.05 vs 1.66; keyword over-tagging).
4. VERIFY: per (item, candidate tag) yes/no question: "Does solving this
   problem REQUIRE skill X as defined? Answer about the solution shown."
   Include the near-miss neighbor's definition in the prompt.
5. CONFIDENCE: repeat steps 3-4 N=3-5 times (temperature > 0, shuffled
   candidate order). Confidence = fraction of runs that keep the tag.
   Accept primary if ≥0.8; 0.4-0.8 → review queue; <0.4 → drop.
   Optional: a second model as a tiebreaker.
6. CUES & TIER: in the same pass, detect method cues (Q6) and propose
   difficulty tier 1-5 with a one-line reason; low-confidence tiers → review.
7. PROVENANCE: store model id, prompt version, taxonomy version, date,
   confidence per tag. Pin model and prompt versions (results drift across
   versions, Fan et al.). Re-tag only when the taxonomy changes.
```
- **Few-shot examples:** use 2-3 in-domain examples per chapter, drawn from items the learner has hand-verified. Duan et al. found removing examples made KCs too abstract, but MathFish found few-shot examples did not consistently help verification, so validate on the spot-check set before adopting them.
- **Calibration note:** LLM verifiers are lenient (96% vs 52% in MathFish) and favor recall over precision (recall 96.8 vs precision 76.5). Expect **over-tagging** to be the dominant error. Set acceptance thresholds to favor precision on *primary* tags, which drive FSRS lapses. Secondary tags can be more permissive because they carry less weight in blame (Algorithm A).

#### Algorithm D: Validation with one learner's data [Own proposal]
1. **Spot checks before use:** for each new chapter, hand-check a stratified sample (≥30-50 items, oversampling low-confidence and multi-tag items). Compute primary-tag precision and recall per skill. If a skill's precision is <0.85, rewrite its definition and near-miss negatives and re-run the chapter. This is the "calibrate on a small item set" loop from Zhang et al., on a personal scale.
2. **Consistency check:** tags that flip across reruns or between two models go to review automatically. Disagreement is a cheap proxy for low reliability.
3. **Learner-data mis-tag detectors (ongoing):**
   - *Surprising success:* item solved quickly and correctly while its primary skill is in a confirmed-weak state → the tag may be wrong, or the item doesn't really require the skill.
   - *Surprising failure with blame elsewhere:* the learner repeatedly taps a step whose skill is **not** among the item's tags → a missing tag. Add it to the review queue.
   - *Probe disagreement:* a tapped-skill probe passes but misses on the same item family keep recurring → the family's primary tag may be wrong.
   - *Residual outliers:* items with |y − p| consistently large relative to tagged-skill states across ≥2 attempts → re-tag or re-tier.
   These follow the "Generate-and-Validate" idea of using response fit as a guardrail, scaled down to single-learner heuristics. With one learner, treat them as **review flags**, never automatic edits (Goldin & Galyardt show automated refinement acceptance is error-prone even with many students).
4. **Taxonomy evolution:** when "NONE / NEW SKILL" fires repeatedly for similar steps, cluster those steps (embedding similarity) and propose a new skill for review. This is the generate-then-cluster approach used in KCGen-KT and Moore et al.

### Gaps
- I found **no published accuracy for LLM tagging of calculus (or college-level math) problems** against a fixed skill list. All math results found are K-12 (MathFish, MathKnowCT, ASDiv/GSM8K). The KCGen-KT and Moore et al. results are programming, chemistry and e-learning.
- No published human inter-rater agreement for **calculus KC tagging** was found. The 88-92% figures come from K-3 math concept matching and from programming-tag precision judgments.
- I found no study that evaluates **step-level** skill tagging of worked solutions (tagging each step rather than the item). The step-tag design is my proposal.
- No study evaluated LLM **confidence** (verbalized or self-consistency) as a predictor of tag correctness for math KC tagging. Zhang et al.'s "high-confidence only" filtering is the nearest evidence, but no calibration curve was reported.
- The Tan et al. (ICCE 2025) numbers and the BJET 2024 multilingual skill-tagging paper (Kwak et al.) could not be retrieved (paywall or fetch failure).
