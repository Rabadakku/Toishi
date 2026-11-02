# Speed (fluency), mastery vs retention, goal-based deadline targets, and multi-course daily budgets for an FSRS problem-solving app

Context: an offline Mac app for one learner. FSRS-6 (py-fsrs) schedules skills, each review draws a fresh problem, an Elo-style model picks tiers 1–5, and the student types final answers after working on paper. Each section below tests one of the design decisions already made.

Evidence labels used throughout: **[Strong]** = peer-reviewed experiment or large study; **[Moderate]** = peer-reviewed but small, indirect, or a different domain; **[Practitioner]** = product documentation, forum posts by experienced users or developers, or user simulations; **[Proposal]** = my own reasoning and numbers, not taken from a source.

---

## 1. Response time as a learning signal: should slow-but-correct count as FSRS "Hard"?

### Takeaway
There is solid evidence that response time on *correct* answers tells you something about how strong a memory is. Kellman's ARTS system, van Rijn/Sense's adaptive fact learning, and the Math Academy product all use it. The signal that research supports is **slowness relative to the learner's own expected time**, not slowness relative to an absolute exam pace. So the decision should be refined: a very slow correct answer, measured against the student's own baseline, can reasonably map to FSRS "Hard", which is only a mild penalty. Missing exam pace should feed the separate Level measure and should not touch the FSRS grade.

### Cited Findings
- **ARTS priority formula** (Mettler, Massey & Kellman 2016, JEP: General): Pᵢ = a(Nᵢ − D)[b(1 − αᵢ)·log(RTᵢ/r) + αᵢ·W]. Nᵢ is the number of trials since the item was last shown. D is an enforced delay (= 1). αᵢ = 0 if the previous answer was correct and 1 if incorrect. W is a priority boost for errors. r = 3.0 is reported. The extracted text did not include a, b or W; they are in the paper's Table A1. In the 2016 PDF the sign before D came out garbled as "+"; the CogSci 2020 paper prints "−". — [Mettler, Massey & Kellman 2016 PDF](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/mettler_massey_kellman_2016.pdf); [Mettler et al. CogSci 2020](https://cognitivesciencesociety.org/cogsci20/papers/0138/0138.pdf) [Strong]
- ARTS rationale: RT "is a useful indicator of retrieval difficulty," and RTs are "at least a reasonable proxy for learning strength," though they can also reflect attention lapses. RTs on **incorrect** answers are treated as uninformative, which is why accuracy acts as a switch in the formula. ARTS "attempt[s] to read [learning strength] directly through RT measures" and does not model it. log(RT) gives more weight to differences among short RTs. — [Mettler, Massey & Kellman 2016](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/mettler_massey_kellman_2016.pdf) [Strong]
- On a 1-week delayed test (24 African countries, geography), ARTS scored 0.42, against 0.31 for a fixed expanding schedule and 0.30 for a fixed equal schedule (d ≈ 0.56–0.57). Against a yoked-item control it scored 0.42 vs 0.326, which was not significant (p = .16). ARTS also "compared favorably with a classic adaptive learning system that did not utilize RT information (Atkinson, 1972)" in Mettler et al. 2011. — [Mettler, Massey & Kellman 2016](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/mettler_massey_kellman_2016.pdf) [Strong for spacing; the gain specifically from RT is cited secondhand]
- ARTS retirement criterion in CogSci 2020: "five out of the last five presentations of an item correct with all five response-times less than seven seconds." Adaptive scheduling reached criterion in 197 trials vs 429 for random. Efficiency was 102% higher immediately and 50% higher at the delayed test. However, in Experiment 1 the random group, which got roughly twice the trials, showed **larger raw delayed accuracy gains** (0.76 vs 0.52). With dropout in both conditions (Experiment 2), accuracy did not differ and delayed efficiency was 31% higher for adaptive. — [Mettler et al. CogSci 2020](https://cognitivesciencesociety.org/cogsci20/papers/0138/0138.pdf) [Strong]
- Kellman's math Perceptual Learning Modules (PLMs) used RT inside both retirement rules and sequencing. Fractions: a category retired at "10 of the last 12 items correctly" with RT < 90 s per item for word problems and < 20 s for others. Algebra Experiment 2: two blocks with ≥85% accuracy and mean correct RT ≤ 8 s (the Discussion says 8.5 s), trials timed out at 30 s. Algebra Experiment 3: "5 out of the last 6 problems from that category answered correctly" with mean correct RT ≤ 8 s, and "faster responses lengthened the retention interval." — [Kellman et al. 2008, Pragmatics & Cognition](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf) [Moderate: these are classification/recognition tasks, not full solving]
- Adaptive fact learning (van Rijn / Sense, ACT-R based): each item has its own decay ("rate of forgetting"), starting at 0.3. When a response is much slower than the model predicts, the decay is adjusted upward, meaning faster forgetting is assumed. In 66 university students, the rate of forgetting estimated in session explained 62.4% of the variance in 3-day delayed recall, compared with 1.2% for working-memory capacity. — [Sense et al. 2018, Frontiers in Education](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2018.00112/pdf) [Moderate: small, homogeneous sample; the estimate combines RT and accuracy]
- Adding a learner's running **median correct RT** per knowledge component to Performance Factors Analysis improved prediction, but only slightly. Cross-validated R² rose by +0.0123 (multiple choice, 5 s limit), +0.0084 (short answer), and +0.0008 (statistics cloze) over an accuracy model that already had a "before first correct" dummy. — [EDM 2023 short paper](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-short-papers.22/index.html) [Moderate]
- **Math Academy** puts speed directly into review decisions: "The system will immediately assign review tasks on topics the student has answered incorrectly **or exceeded the time limit**." It also says "If a student is unable to perform the skills in the time given, then they haven't quite mastered the material well enough," and that quizzes consider "not only whether a question was answered correctly, but the response time as well." — [Math Academy FAQ](https://WWW.MATHACADEMY.COM/faq) [Practitioner]
- Retrieval-effort hypothesis: harder but *successful* retrievals (for example after longer gaps) produced **better** final test performance. — [Pyc & Rawson 2009 via Matuschak notes](https://notes.andymatuschak.org/z5zckzyAM1DwEQqt94qMpsd) [Strong, original JML paper; secondary summary used here]
- FSRS uses only interval lengths and grades, not review time. Review time was used only by the "Compute minimum recommended retention" feature, which was removed with FSRS-6. — [Anki forum, quoting FSRS FAQ #5](https://forums.ankiweb.net/t/does-anki-take-into-account-average-and-total-time-for-each-card-for-scheduling/70714) [Practitioner]
- In FSRS's stability formula, Hard multiplies the stability *increase* by w15 (< 1) and Easy by w16. For same-day reviews in FSRS-6, SInc ≥ 1 should hold for G ≥ 2. So Hard still grows stability, just more slowly; it does not reset the item. — [awesome-fsrs wiki: The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm) [Practitioner/technical]
- The Anki add-on "Pass/Fail Review" grades automatically from answer time. Defaults: < 1 s → Easy, 1–7 s → Good, ≥ 7 s → Hard. Thresholds are global or per deck, never per card. The author no longer uses it and reads a linked thread as suggesting it is redundant with FSRS. No FSRS developer comment was found on the page. — [Anki forum thread](https://forums.ankiweb.net/t/pass-fail-review-automatic-difficulty-rating-based-on-answer-time-beta-ver-official-thread/53872.md) [Practitioner]

### Inferences
- **[Proposal] Split the speed signal into two uses.**
  1. *Memory signal → FSRS grade.* A correct answer whose active time is far above the student's **own** baseline for that skill and tier suggests a struggling retrieval. This matches the van Rijn decay update and ARTS's RT-as-strength idea. Map it to Hard.
  2. *Performance criterion → Level.* Missing exam pace is a fluency or proficiency shortfall, not evidence of forgetting. Record it against Level (§4), not the FSRS grade. Math Academy does attach a scheduling consequence to time-limit misses, so a mild one is defensible, but FSRS's optimizer assumes that grades reflect memory.
- **[Proposal] Change the user's rule from "> 2× median OR past exam pace" to:**
  `grade = Again` if wrong; otherwise `Hard` if `log(t_active) − median(log t_recent correct, same skill×tier) > ln 2` (that is, more than 2× the personal median) **and** `t_active > T_target`; otherwise `Good`. Optionally use `Easy` if `t_active < 0.5 × T_target` and the problem is tier ≥ the skill's current tier.
  The **AND** matters. Early in the semester the student will often be slower than exam pace on every problem. Under "OR", nearly every review would become Hard, w15 would shrink every stability gain, and the workload would balloon exactly when the student is weakest.
- **[Proposal] Guard rails:** apply the rule only once the baseline has ≥ 5 correct samples (otherwise use a tier prior). Use the **median of log-times**, since RT distributions are right-skewed. Compute the baseline from correct answers only, as ARTS and the EDM 2023 paper do. Freeze the baseline window, for example to the last 10–20 correct answers, so the threshold tightens slowly as the student speeds up.
- **[Proposal] Consistency for the optimizer:** FSRS fits w15 from what "Hard" means *in your data*. Whatever rule assigns Hard must stay stable over time. If it changes, re-run the optimizer only after enough reviews under the new rule. Store raw active time with each review so grades can be recomputed later.
- The retrieval-effort result (Pyc & Rawson) is a warning: a slow correct answer *after a long interval* may simply mean low retrievability at review time. FSRS already accounts for that through R in the stability increase (the e^{w10(1−R)} − 1 term). So the Hard threshold should probably be relative to the expected time **given** current R. A simple approximation is to raise the threshold factor (e.g., 2.5× instead of 2×) when R at review time was < 0.85. [Proposal]

### Gaps
- No published FSRS benchmark was found that tests response time as a feature, or that tests "slow-correct → Hard" against "accuracy-only" grading. Whether the mapping improves FSRS predictions is unverified. The only option is to test it on the student's own data later, comparing log-loss of the optimizer with and without time-assigned Hard.
- The exact ARTS constants a, b and W (Table A1) could not be extracted.
- All RT-in-scheduling studies use short items (seconds), such as facts, map locations, or recognition PLMs. No study was found that uses RT for multi-minute written solving like calculus problems.

---

## 2. Measuring time fairly: idle time, pauses, outliers, and typing time

### Takeaway
The research systems used simple, robust methods: time-outs, winsorizing at a high percentile, medians of correct RTs, and log-RT. Anki caps answer time at 60 s by default. For a paper-and-pencil problem app, the main danger is not outliers. It is wrongly pausing the clock during legitimate paper work, when there is no keyboard or mouse activity. So pause on loss of focus or switching away from the window, not on input inactivity alone. Then cap per attempt and summarize with log-medians.

### Cited Findings
- Anki: "Maximum answer seconds: The default limit is 60 seconds." Answers longer than this are recorded as the cap. — [Anki Manual, Deck Options](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- EDM 2023 RT preprocessing: correct RTs above the **95th percentile were winsorized** to that value. Missing RTs were imputed with the learner's overall median. Hint and instruction trials were excluded. The feature was the **running median** of a learner's prior correct RTs per knowledge component. — [EDM 2023](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-short-papers.22/index.html) [Moderate]
- ARTS uses log(RT/r), which compresses long RTs and weights differences among short RTs more heavily. RT on incorrect answers is ignored. — [Mettler, Massey & Kellman 2016](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/mettler_massey_kellman_2016.pdf) [Strong]
- Kellman's algebra PLM had a hard 30 s time-out per trial and used the *mean RT of correct responses over a window* (5 of last 6, ≤ 8 s) as its criterion. It did not require every single response to be under threshold. — [Kellman et al. 2008](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf) [Moderate]
- Math Academy lets "the timing … be adjusted for each student in the Accommodations settings." — [Math Academy: How It Works](https://mathacademy.com/how-it-works) [Practitioner]

### Inferences
- **[Proposal] Active-time state machine:**
  - The timer runs while the problem is displayed **and** the app window is key/frontmost.
  - It pauses immediately on window blur or app switch, screen lock or sleep, and when the visible pause button is pressed. While paused, the problem is hidden or blurred so the pause is not used to keep thinking.
  - It does **not** pause on keyboard or mouse inactivity alone, because working on paper produces no input. Instead, after a long stretch with no input (suggest `max(3 × T_target, 5 min)`), show a non-modal "Still working?" prompt. If it gets no response within 60 s, trim the recorded time back to the moment the prompt appeared and pause.
  - Per-attempt cap: `T_cap = max(4 × T_target(skill, tier), 3 min)`, with an absolute ceiling of about 20–30 min. Store both the raw and capped values. Statistics use the capped value.
- **[Proposal] Summaries:** all speed statistics use log-time, i.e., the median of ln t over correct answers. Winsorize at the per-skill 95th percentile when fitting any regression, such as tier time priors. Never average raw seconds.
- **[Proposal] Separate entry time from solve time.** Record `t_solve` = display → first keystroke in the answer field (or a "ready to enter" press), and `t_entry` = first keystroke → submit. Speed criteria use `t_solve + min(t_entry, E_allow)`, where `E_allow` is a small allowance based on answer length (for example 5 s + 0.3 s per character of the expected answer). Long math-syntax entry then does not count as slow thinking, and the student still cannot do work inside the entry phase indefinitely. Record exact entry times for later calibration.
- **[Proposal] Wrong-then-correct (retry) attempts:** grade the FSRS review from the first submission. Exclude retry time from speed baselines, consistent with ignoring RT on incorrect answers.
- **[Proposal] Exclude** from speed baselines: attempts with any pause longer than 2 min, the first attempt after the app resumes from sleep, and attempts where hints or worked examples were opened.

### Gaps
- No published data was found on the typing overhead for math answer entry (e.g., LaTeX-like syntax). `E_allow` has to be calibrated from the student's own logs.
- No study was found that compares idle-detection policies for self-paced written problem solving.

---

## 3. Speed targets for math: does timed or fluency practice help, what are the risks, and how should targets and feedback be set?

### Takeaway
Within cognitive science and the "fluency" tradition, speed criteria are standard: Kellman's PLMs, Math Academy's timed quizzes, and Skycak's argument from automaticity. The anxiety critique (Boaler, NCTM 2023) is aimed mainly at *timed tests of basic facts for young children*, and its evidence is largely correlational. Two parts of the user's plan are supported by both camps: speed is ignored until the skill is accurate untimed, and time is shown after answering rather than as a countdown. Targets should come from exam pacing with a personal-improvement cap. "Mastered" should be judged on a median over several attempts, not on any single attempt.

### Cited Findings
- NCTM (January 2023): "Procedural fluency is the ability to apply procedures **efficiently, flexibly, and accurately**," including choosing the more appropriate strategy. It also says: "Timed tests do not assess fluency and can negatively affect students, and thus should be avoided." The statement is mostly about K–8 basic facts. — [NCTM Position Statement](https://nctm.org/Standards-and-Positions/Position-Statements/Procedural-Fluency-in-Mathematics) [Practitioner/professional body]
- Boaler (2014, *Teaching Children Mathematics*, pre-K to grade 6) claims timed tests cause early-onset math anxiety. Her evidence: Beilock's work on anxiety blocking working memory, which hits high-working-memory students most; Ramirez et al. 2013 (150 first and second graders, anxiety present by grade 1); Young, Wu & Menon 2012 (46 children aged 7–9, fMRI). The causal claim goes beyond what the mostly correlational studies show, and the population is young children. — [Boaler, youcubed PDF](https://www.youcubed.org/wp-content/uploads/2017/03/nctm-timed-tests.pdf) [Moderate for anxiety–performance links; weak for "timed tests cause anxiety"]
- Skycak (Math Academy) proposes a sequence: understand the concept, practice **untimed until consistent**, then practice timed with the most efficient strategy. He warns that timing before the skill is reliable untimed "mainly causes stress." His argument is about automaticity and freeing mental capacity, and the post cites no studies. — [Justin Skycak, "Fast, Correct Answers Do Matter"](https://www.justinmath.com/fast-correct-answers-do-matter-in-mathematics/) [Practitioner]
- Math Academy assigns timed quizzes about every 150 XP. Exceeding the time limit triggers review, as an error would, and timing can be adjusted per student. — [Math Academy FAQ](https://WWW.MATHACADEMY.COM/faq); [How It Works](https://mathacademy.com/how-it-works) [Practitioner]
- Evidence that fluency gains last: in Kellman's algebra PLM (Experiment 3), recognition RTs fell about 29% from pre-test to post-test and about 36% from pre-test to a 3-week delayed post-test, and "solving-time gains were preserved." In the fractions PLM (about 9-week delay), the PLM group kept its gains in accuracy and showed a greater pre-to-delayed gain than controls (t(43) = 2.86, p < .01). — [Kellman et al. 2008](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf) [Moderate]
- Examples of absolute speed criteria in the research: 7 s per item for single-step identification ([CogSci 2020](https://cognitivesciencesociety.org/cogsci20/papers/0138/0138.pdf)); 8 s mean for algebra transformation recognition; 20 s for fraction items; 90 s for fraction word problems ([Kellman et al. 2008](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf)). [Moderate]

### Inferences
- **[Proposal] Target time per skill × tier**, computed once the skill reaches "Learned" (speed is ignored before that):
  - `T_exam(tier)` (exam-pace ceiling) = `(exam_minutes × 0.85) / Σ exam point-weight` × the expected point-weight of a typical problem of that tier. The 0.85 leaves time for checking. Practice items test a single skill while exam problems chain several, so start with tier 1–2 at about 0.25–0.4 of the per-exam-problem time, tiers 3–4 at about 0.5–0.8, and tier 5 at about 1.0.
  - `T_personal` = `0.7 × median(t_solve over the first 5 correct attempts after Learned)`. The 30% improvement is in the range of Kellman's observed 29–36% RT drops.
  - `T_target = max(T_floor, min(T_exam(tier), T_personal))`, where `T_floor(tier)` keeps the target from becoming unreachably small (for example 20 s, 40 s, 60 s, 90 s, 120 s for tiers 1–5). All these numbers are starting guesses to be recalibrated from the student's logs.
  - Update `T_personal` at most once a week and never make it stricter by more than 10% per update. A target that keeps moving would undercut the sense of progress.
- **[Proposal] Window criterion, not single attempts.** "At target speed" = the median t_solve of the last 3 correct attempts at the skill's exam tier, taken on ≥ 2 different days, is ≤ T_target. This mirrors Kellman's mean-over-window rule and resists the high variance of multi-minute problems.
- **[Proposal] Feedback without harm.**
  1. No visible countdown during the problem. Show an elapsed time *only after submission*, next to the target ("4:10 · target 5:00").
  2. Show a weekly trend line of median time per skill (fluency growth) rather than per-problem judgments.
  3. A slow correct answer is always displayed as **correct**. Any "Hard" effect is internal.
  4. Offer a per-session "untimed" switch, as Math Academy's accommodations do. In untimed sessions, speed is neither recorded for Level nor used for Hard.
  5. Keep the language about pace ("exam-ready pace") rather than about being fast or smart.
- For a self-directed adult learner who chose speed goals, the NCTM/Boaler cautions apply less directly. They still argue for keeping speed pressure out of the initial learning phase, which the plan already does. [Inference]

### Gaps
- No controlled study was found showing that timed *practice* for **college calculus** (or physics/chemistry) improves timed exam scores beyond untimed practice. Evidence for transfer of speed practice to exams is indirect: PLM fluency persistence and product claims.
- No research-based per-tier time targets for calculus exist. The numbers above must be calibrated from the student's own logs and real exam formats.
- Evidence on math anxiety from timed practice in adult or college learners was not found in this search.

---

## 4. Learning vs performance, "learned vs mastered", mastery criteria, and reporting Level separately from Recall

### Takeaway
How well someone does during practice is a poor indicator of durable learning (Soderstrom & Bjork 2015). Major math products reserve their top mastery level for success shown **later, in a separate, mixed assessment without prompts**: ALEKS Knowledge Checks and Khan Mastery Challenges. Within-session mastery criteria, even ARTS's 5/5 under 7 s, still leave substantial forgetting a week later. The user's Level ladder (Learning → Learned → Exam-level → Mastered, requiring ≥ 3 spaced sessions and ≥ 2 problem forms) fits this evidence. It needs explicit demotion rules and a defined "spaced" gap.

### Cited Findings
- Soderstrom & Bjork (2015): "The primary goal of instruction should be to facilitate long-term learning—that is, to create relatively permanent changes." Performance during training is often an unreliable index of whether learning occurred, and learners often mistake current performance for lasting learning. — [PubMed 25910388](https://pubmed.ncbi.nlm.nih.gov/25910388/); [full text](https://hwb.gov.wales/api/storage/1031b700-acaf-4eda-a4bc-758715e85ff2/Learning%20versus%20Performance%20An%20Integrative%20Review.pdf) [Strong]
- **ALEKS "learned"**: the student can "solve a few problems based on that material without making mistakes," possibly after an example or two. **"Mastered"**: the student can "recognize it without having it pointed out," "reliably solve problems without following examples," and retain it over "extended periods of time." Knowledge Checks assess mastery. — [UCSC Math Coach on ALEKS](https://mathcoach.sites-test.ucsc.edu/success/learned_and_mastered) [Practitioner]
- ALEKS: "Mastered refers to the number of topics a student has demonstrated mastery of in a Knowledge Check." A topic missed in a Knowledge Check (wrong answer or "I don't know") moves from Mastered or Learned back to Remaining and back into the Learning Path. Knowledge Checks occur after 20 topics learned plus 5 hours in learning mode, after 10 hours, or after 60 days without one. — [McGraw Hill ALEKS support](https://www.mheducation.com/support/aleks-support-center/knowledge/why-did-my-number-of-mastered-or-learned-topics-go-down-after-a-knowledge-check.html) [Practitioner]
- **Khan Academy Mastery Challenges**: unlocked after Familiar on ≥ 3 skills and Proficient on ≥ 1, with ≥ 12 hours since the last one. Each has 6 questions across 3 skills (2 per skill). Both correct → level up; both wrong → level down; one of each → unchanged. — [Khan Academy Help](https://support.khanacademy.org/hc/en-us/articles/360037494231) [Practitioner]
- Math Academy: a student advances within a lesson after "two practice problems correct in a row." Missed quiz topics become review topics immediately. Its diagnostic "measures both mastery and automaticity." — [Math Academy: How It Works](https://mathacademy.com/how-it-works); [FAQ](https://WWW.MATHACADEMY.COM/faq) [Practitioner]
- Within-session criteria do not guarantee retention. Even with ARTS's 5/5-correct, all-under-7 s retirement criterion, delayed-test accuracy gains were well below immediate gains (adaptive: 0.85 immediate vs 0.52 delayed accuracy change). — [Mettler et al. CogSci 2020](https://cognitivesciencesociety.org/cogsci20/papers/0138/0138.pdf) [Strong]
- RemNote's exam scheduler requires two successful recalls for new cards before normal spacing, and two in a row for "shaky" cards after an error. — [RemNote Help: Exam Scheduler](https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler) [Practitioner]

### Inferences
- **[Proposal] Level definitions** (evidence-based; never decays with time alone, only with failed evidence):
  - **Learning**: started, but the Learned criterion is not yet met.
  - **Learned**: 2 consecutive correct answers in a session (Math Academy / RemNote convention) at tier ≥ 2, with no solution viewed. Speed is ignored.
  - **Exam-level**: correct at the skill's exam tier (tier where the Elo-predicted exam difficulty sits, typically 3–4) on ≥ 2 different days, with median time ≤ T_target (§3).
  - **Mastered**: all of the following —
    - (a) ≥ 3 successful reviews on **different days**, with at least one success after an elapsed interval ≥ 7 days *and* at predicted R ≤ 0.90 at review time, so the success is genuinely delayed and not a "just reviewed" success;
    - (b) successes on ≥ 2 distinct problem forms or templates;
    - (c) at least one success at tier ≥ exam tier + 1 or in a mixed/cumulative review session (comparable to ALEKS's unprompted Knowledge Check);
    - (d) speed criterion met on the most recent 3 correct answers.
- **[Proposal] Demotion** (similar to Khan's two-question rule):
  - One miss on a Mastered or Exam-level skill sets a "shaky" flag and gives FSRS Again.
  - A second miss within the next 3 reviews demotes one Level.
  - A miss while still Learned returns the skill to Learning.
  - Recovering a level requires meeting that level's criterion again; earlier evidence does not carry over.
- **[Proposal] Reporting:** show **two independent numbers per skill**:
  - *Recall* = FSRS retrievability now, plus a projected "on exam day" value if no review happens before then. This is the "will I remember" measure.
  - *Level* = a 4-step badge. This is the "how well can I do it" measure.
  At course level, show the share of in-scope skills at Exam-level or above, and mean projected recall on the exam date. Do not merge them into one score; ALEKS likewise reports learned and mastered as separate wedges rather than one percentage.
- **[Proposal] Mixed "check-up" sessions:** every ~10 study hours or ~3 weeks, insert an ALEKS-style cumulative check containing a few skills that are not currently due. Successes can satisfy Mastered criterion (c). Failures trigger demotion and FSRS Again. These reviews still update FSRS normally, since they are reviews.

### Gaps
- Khan Academy's main mastery-levels article (Attempted/Familiar/Proficient/Mastered and points) failed to load. Only the Mastery Challenge rules were verified.
- No study was found that compares mastery criteria with spaced requirements to within-session criteria *for math problem solving* specifically. The recommendation extrapolates from verbal and perceptual learning studies.
- "Problem form" diversity (≥ 2 forms) as a transfer criterion is not directly validated in these sources. It is a reasonable reading of ALEKS's "without having it pointed out" and "without following examples" language.

---

## 5. Scheduling toward a deadline: exam planner, workload cost of higher retention, and after the exam

### Takeaway
Running 0.95 all semester roughly **doubles** workload compared with 0.90. One user's FSRS simulation gives about 2.1× by interpolation, and the FSRS-6 interval at R = 0.95 is about 0.40× the interval at 0.90. Spacing research also implies that, for a test months away, reviews should stay spaced throughout rather than be crammed (Cepeda 2008). So the user's plan holds: 0.90 day to day, a targeted pre-exam "booster" that brings each in-scope skill to R ≥ 0.95 on the exam date, then about 0.80 maintenance. FSRS-6 gives a closed-form rule for when the last pre-exam review must happen. Practitioners warn against capping intervals at the exam date. The booster should be selective and spread over a window, and any extra load should be shown to the student as an explicit "catch-up" proposal rather than applied silently (the RemNote pattern).

### Cited Findings
- **Cepeda et al. 2008** (> 1,350 participants; gaps up to 3.5 months; tests up to 1 year later): "the optimal gap declined from about 20 to 40% of a 1-week test delay to about 5 to 10% of a 1-year test delay." The optimal gap grows in absolute terms as the test delay grows. — [PubMed 19076480](https://pubmed.ncbi.nlm.nih.gov/19076480/) [Strong]
- FSRS-6 forgetting curve: R(t, S) = (1 + factor·t/S)^(−w20), with factor = 0.9^(−1/w20) − 1, so that R(S, S) = 0.90. The interval for a desired retention r is I(r, S) = (S/factor)·(r^(−1/w20) − 1). That interval formula is given for FSRS-4.5 and follows the same algebra for FSRS-6. — [awesome-fsrs wiki: The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm) [Technical]
- Anki manual: desired retention defaults to 90%, which "offers a good balance." "Above 90% the workload increases very quickly, and above 97% the workload can be overwhelming." Keep it "lower than 97%." Anki's FSRS simulator estimates reviews per day or minutes per day. — [Anki Manual](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- One user's simulator output (desired retention → minutes/day), posted in the Anki forum thread proposing a workload-vs-DR graph: 70% → 19.8; 79% → 31.1; 82% → 37.1; 85% → 45; 88% → 57.2; 91% → 76.2; 94% → 114.5; 97% → 230.3. Expertium proposed showing a workload-vs-DR curve with its "knee" in place of the "minimum recommended retention" feature, with the curve fit as time = a·DR^b/(1−DR)^c. — [Anki forum: Replace CMRR with workload-vs-DR graph](https://forums.ankiweb.net/t/replace-cmrr-with-workload-vs-dr-graph-more/63234) [Practitioner; single collection]
- In another user's simulator runs, going from 70% to 82% desired retention raised workload by about 30–50%. — [Anki forum: Approximate workload](https://forums.ankiweb.net/t/questions-about-approximate-workload-when-changing-desired-retention/63860) [Practitioner]
- Practitioner advice for exams: "You shouldn't try to control your intervals based on an exam deadline." A low maximum interval does not work, because cards will still be scheduled after the exam unless the cap keeps being lowered. Instead raise desired retention "by a point or two," and use filtered decks near the exam. In a 3-month exam thread the same expert says "90% desired retention is plenty high to start with," and that changing desired retention does not require re-optimizing parameters. — [Anki forum: max review date](https://forums.ankiweb.net/t/exam-specific-add-on-or-help-max-review-date/67433/2); [Anki forum: retention for exam](https://forums.ankiweb.net/t/need-advice-on-fsrs-retention-for-exam-3-month/43560) [Practitioner]
- **RemNote exam scheduler** works alongside the main scheduler (SM-2 or FSRS) and "adds extra reviews or alters the parameters of the main scheduler as necessary." Components: a learning period (2 successful recalls); extra practice for shaky cards; a **Catch Up Period** that "proposes a temporary increase to your daily goal rather than silently rearranging"; an Exam Daily Goal calculated from this week's upcoming practice and the total remaining; and a **Final Review Period** that adds one last review of every card just before the exam. It gives no specific exam-day retention target and describes no post-exam change. — [RemNote Help](https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler) [Practitioner]

### Inferences
- **Interval multipliers computed from the FSRS-6 formula** [Proposal/computation; the default w20 ≈ 0.1542 is recalled from py-fsrs defaults and should be checked against the fitted parameters]. I(r)/I(0.90): r = 0.80 → 3.32×; 0.85 → 1.91×; 0.95 → 0.40×; 0.97 → 0.22×. Across w20 = 0.15–0.5, the 0.95 ratio stays at 0.40–0.46 and the 0.80 ratio at 2.4–3.3×.
- **Workload ratio**, log-interpolated from the forum simulation above [Computation]: 0.80 ≈ 0.48×, 0.85 ≈ 0.65×, 0.95 ≈ **2.1×** the minutes/day at 0.90. This agrees with the interval math (0.40× intervals, partly offset by fixed new-learning cost). Running 0.95 all semester is therefore about twice the work, which supports the planner approach.
- **Exam booster rule (closed form)** [Proposal]. For a skill with post-review stability S′, R on the exam date stays ≥ R* only if the last successful review falls within `Δ* = I(R*, S′) = (S′/factor)·(R*^(−1/w20) − 1)` days before the exam. For R* = 0.95 that is about 0.40·S′: S′ = 10 d → within 4 days; 20 d → 8 days; 40 d → 16 days; 80 d → 32 days. Algorithm, run daily from about 21 days before the exam:
  1. For each in-scope skill, compute `R_exam = R(exam − last_review, S)` assuming no further review, and also the R at its currently scheduled due date.
  2. If its normal due date falls before the exam, do nothing yet; the next review will be re-evaluated.
  3. If its due date falls *after* the exam and `R_exam < R*`, schedule a booster on a day `d` with `exam − d ≤ I(R*, S_good(d))`. Here S_good(d) is the FSRS stability after a Good review on day d, from py-fsrs's preview of next states. Pick the latest feasible day, but spread booster load evenly over the window (load-balancing).
  4. If a booster review is failed (Again), FSRS relearning shortens the interval automatically. Re-run step 3 the next day.
  5. Days −1 and 0: no forced sweep of everything (RemNote-style) unless the student asks. Optionally offer a short "warm-up" set of the lowest-R_exam skills.
- **Implementation tip** [Proposal]: store S, D and last_review, and compute `due = last_review + I(DR_course(today), S)` *dynamically*. Changing a course's DR (0.90 → maintenance 0.80, or a temporary bump) then takes effect immediately with no batch rescheduling. FSRS parameters do not depend on DR, so no re-optimization is needed.
- **After the exam** [Proposal]: drop the course to 0.80 maintenance. Intervals grow about 2.4–3.3× and workload falls to roughly half. Exception: skills that are **prerequisites** for an upcoming course (Calc 1 → Calc 2, physics) should be held at 0.85. About 3–4 weeks before the next course starts, run the same booster with R* = 0.90 for those prerequisite skills only. This follows Cepeda's ridgeline idea: if the "test" is the next course's use of the skill, schedule a refresh rather than relying on a far-out interval.
- Booster vs midterms: treat each exam (midterm or final) as a target date with its own in-scope skill set. Cumulative finals reuse midterm skills, so a skill's booster for the final uses its stability after the midterm booster. Midterm boosters are not wasted.

### Gaps
- No peer-reviewed or official FSRS analysis of "maximize R on a target date" scheduling was found, nor a published FSRS "deadline" algorithm. The booster rule is derived from the FSRS formulas. The Anki community's view is negative on interval caps but does not cover targeted boosters.
- The workload-vs-DR numbers come from one user's simulated collection, not an official benchmark. The FSRS simulator in the app itself (py-fsrs has no built-in workload simulator, as far as is known) or a simple Monte Carlo would give numbers specific to the student.
- Cepeda's data are for verbal facts. Spacing in math problem solving is supported elsewhere (e.g., Rohrer's work), but this search did not cover it.

---

## 6. Goal settings: translating "aim for an A / B / keep it" into settings

### Takeaway
No product or study found maps a letter-grade goal onto spaced-repetition parameters. Products translate goals into **workload pace and completion dates**: Math Academy's daily XP with projected completion dates, and RemNote's exam daily goal plus catch-up proposals. Since an exam score depends on *both* remembering and performing at exam difficulty, "aim for an A" should raise the Level and tier targets as well as exam-day recall, and the app should show a projected score and the required daily load.

### Cited Findings
- Math Academy: "Students have a daily XP goal, with each XP being roughly equivalent to 1-minute of focused effort," which can be "adjusted depending on the student's schedule." The diagnostic report gives "estimated course completion dates with a variety of daily XP goals." The FAQ recommends 20–40 XP/day, 3–5 days/week. — [Math Academy: How It Works](https://mathacademy.com/how-it-works); [FAQ](https://WWW.MATHACADEMY.COM/faq) [Practitioner]
- Math Academy assigns midterms and finals automatically for credit courses and uses timed quizzes as a mastery gate. — [Math Academy FAQ](https://WWW.MATHACADEMY.COM/faq) [Practitioner]
- RemNote calculates an Exam Daily Goal from upcoming and remaining practice, and proposes a temporary goal increase when the student falls behind. — [RemNote Help](https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler) [Practitioner]
- Practitioner consensus: 0.90 is a reasonable default desired retention, and 0.97+ is overwhelming. — [Anki Manual](https://docs.ankiweb.net/deck-options.html) [Practitioner]

### Inferences
- **[Proposal] Goal presets** (starting values to calibrate):

| Goal | Daily DR | Exam-day recall target R* | Level target for in-scope skills | Tier ceiling | After the date |
|---|---|---|---|---|---|
| A | 0.90 | 0.95 | Exam-level for all; Mastered for skills tagged "core" | 5 | 0.80 (prereqs 0.85) |
| B | 0.88–0.90 | 0.92 | Exam-level for core; Learned for the rest | 4 | 0.80 |
| Keep it | 0.80–0.85 | none | none (just keep Level from decaying via failures) | current | same |

- **[Proposal] Projected exam score** as the bridge between grade and settings: `E[score] ≈ Σ_skills w_s · R_s(exam) · P_s(correct at exam tier | Elo ability θ_s)`, where w_s is the skill's share of exam points (equal weights by default). Show it next to the grade cutoff (90 for A, 80 for B). If projected score < cutoff, the planner says why: low recall means boosters are needed; low P at exam tier means more tier-4/5 practice is needed. It then proposes the extra daily questions needed, RemNote-style, never silently.
- **[Proposal] Feasibility check at goal creation**: estimate total reviews needed until the date (simulate FSRS with DR and the booster), divide by available days, and show "≈ N questions/day (~M min)" using the student's median time per question. If this exceeds the daily budget given the other courses (§7), warn and suggest lowering the goal or extending the budget. This mirrors Math Academy's "completion date for each XP pace."
- An "A" goal changing *only* retention would be misleading. Recall of a skill does not guarantee solving exam-tier problems at exam pace (Soderstrom & Bjork's learning-vs-performance gap, and the Level vs Recall split in §4).

### Gaps
- No evidence was found linking a target grade to a specific retention or mastery threshold. The presets are design proposals.
- How Math Academy computes projected completion dates, and whether it lets users set an exam date that drives the schedule, was not confirmed beyond "estimated completion dates" and auto-assigned exams.

---

## 7. Splitting a fixed daily question budget across several courses

### Takeaway
Anki's per-deck limits are static caps that interact badly. A parent deck's limit can be used up before all subdecks are visited when the gather order is "Deck", and review limits also block new cards, so starvation and backlogs are known problems. A better design is a **work-conserving, weighted fair share with per-course minimums**: weights from goal and exam proximity, quotas by the largest-remainder method, unused quota redistributed, a carried-over deficit so a course shortchanged today catches up tomorrow, and due reviews before new material inside each course's share.

### Cited Findings
- Anki: "The selected deck's limits control the total number of cards that will be shown," and subdeck limits "control the maximum number of cards drawn from that particular deck." By default a parent's limits do not apply when you select a subdeck, unless "Limits Start From Top" is on. — [Anki Manual, Deck Options](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- Anki, "Deck" gather order: "If the daily limit of the selected deck is reached, gathering may stop before all subdecks have been checked." This is a direct starvation mechanism for later decks. — [Anki Manual](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- Anki: "The review limit also applies to new cards, and no new cards will be shown" once it is reached, unless an option is set. With a review backlog, "stop introducing new cards until you catch up with that backlog." — [Anki Manual](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- Anki offers a review sort order of "Relative overdueness," which shows first the cards "you're more likely to have forgotten." — [Anki Manual](https://docs.ankiweb.net/deck-options.html) [Practitioner]
- RemNote uses a separate exam goal section inside the daily goal and proposes temporary increases when behind. — [RemNote Help](https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler) [Practitioner]

### Inferences
- **[Proposal] Daily allocation algorithm** (budget B questions/day; C active courses):
  1. **Weights**: `w_c = g_c × u_c × p_c`. Goal factor `g` = A 1.5, B 1.0, keep 0.5. Urgency `u = 1 + 14 / max(days_to_next_exam, 7)`, so u ranges 1 to 3 and rises in the final two weeks; use u = 1 with no upcoming exam. Pressure `p = clamp(due_c / median_due, 0.5, 2)` tracks backlog size.
  2. **Floors**: `min_c = max(3, ⌈0.1·B⌉)` for any course with due work (maintenance-only courses: min 2). Give floors first. If `Σ min_c > B`, scale floors down proportionally to weight.
  3. **Proportional share** of the remainder `B − Σ min_c` by `w_c / Σw`, rounded with the **largest-remainder** method so the quotas sum exactly to B.
  4. **Work-conserving redistribution**: if a course has fewer due-plus-eligible-new items than its quota, return the surplus to the pool and reallocate by weight. Repeat until stable.
  5. **Deficit carry-over** (deficit round robin): track `debt_c += quota_c − served_c` each day, for example when the student stops early. Add `debt_c`, capped at 50% of quota, to tomorrow's quota so stopping early does not always starve the course that comes last in the queue.
  6. **Inside each course's share**: overdue/due reviews and booster reviews first, sorted by lowest current R or largest relative overdueness. New skills only if the course's due backlog is ≤ 1 day's quota, following Anki's backlog guidance.
  7. **Interleave** courses in the session queue in proportion to quotas, e.g., a round-robin weighted by remaining quota, rather than all of course 1 then course 2. Stopping partway through a session then still leaves every course with a fair share served.
- **[Proposal] Budget in minutes as well as questions**: problems differ greatly in length (tier 1 vs 5, calculus vs chemistry stoichiometry). Allocate in *expected minutes* (`Σ median active time per drawn item`) and show both "questions" and "≈ minutes." Otherwise a course with long problems takes most of the student's time.
- **[Proposal] Overload signal**: if the summed *need* (due + booster items) across courses exceeds B for 3+ consecutive days, show a RemNote-style proposal: raise B temporarily, lower a goal, or move a course to "keep it." Never drop due reviews silently.

### Gaps
- No published research was found on fair-share allocation across spaced-repetition decks or courses. The weighted fair-share, floors and deficit carry-over approach comes from general scheduling practice (fair queueing, deficit round robin), not from learning-science studies, and was not sourced here.
- Interleaving benefits across *different courses*, as opposed to across problem types within a course, were not researched in this pass.
