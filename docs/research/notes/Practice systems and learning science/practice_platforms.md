# How leading problem-practice and exam-question-bank platforms drive practice to mastery (teardown as of November 2026)

Research date: 2026-11-01. Scope: PRACTICE mechanics (mastery criterion, review/retention, wrong-answer handling, adaptivity, timing, analytics, motivation) plus the evidence and user sentiment around them. Math Academy and ALEKS basics, Khan mastery levels, WeBWorK/STACK guessing data, Brilliant reviews and Execute Program are already in `Toishi build research/prior_art_and_ux.md`. This file adds new primary material and does not repeat that ground except where a conflict or update matters.

Source-type labels: **[Doc]** vendor documentation/help center; **[Vendor]** vendor-authored research or marketing (treat as unverified); **[Research]** peer-reviewed, government or independent evaluation; **[Observational]** non-causal association study; **[User]** individual user/forum report; **[Competitor]** a rival vendor's blog (biased); **[Carried]** taken from the earlier notes' cited URL and not re-fetched this session.

Method note: the Math Academy Way working-draft PDF (justinmath.com, ~19k lines of text) was downloaded and read directly for the chapters on remediation, timed testing, gamification, diagnostics and the FAQ. Page numbers below are the printed footers of that draft. Reddit mirrors mostly failed or returned binary data, so Reddit sentiment is thin and flagged. PMC pages were blocked by a captcha, so several journal abstracts were pulled via the Europe PMC API instead.

---

## 1. Math Academy: remediation, quizzes, automaticity, XP penalties and the diagnostic (new detail beyond the prior notes)

### Takeaway
The Math Academy Way (working draft) shows a system whose guiding rule is "never lower the bar": help comes as more questions, a rest period, targeted prerequisite reviews, and a retake with different questions, never as answer-revealing hints. Its quizzes are deliberately harder than typical classroom quizzes (timed, interleaved, no advance warning of content) and are used as the instrument for pace-setting and automaticity, with every missed quiz question triggering an immediate remedial review. No independent controlled study of Math Academy exists (all pass-rate figures are internal), and an explicit "rapid-fire" fluency trainer was still only planned as of October 2025.

### Cited Findings
**Mistake handling and remediation (Ch. 21, pp. 300-306)**
- [Doc] The stated principle is that remediation "keeps the bar where it's at." The book contrasts this with adaptive hints in intelligent tutoring systems, which it says "effectively lower the bar for success." Support instead takes the form of actions that help the student "clear the bar fully and independently on their next attempt." — [The Math Academy Way (working draft PDF), p. 300](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] Four remediation modes are defined:
  - **Corrective:** more questions if the student struggles during a task; if they fail a lesson, a break while they progress on unrelated topics, then a re-attempt; if they get stuck again at the same place without forward progress, remedial reviews on the relevant prerequisites; and for every missed quiz question, an immediate remedial review of that topic. — [Math Academy Way, p. 301](https://justinmath.com/files/the-math-academy-way.pdf)
  - **Preventative:** the initial per-student, per-topic "learning speed" is predicted from speeds on related topics; slowing and forcing explicit reviews on those weak related topics is itself "pre-remediation" for later ones. — [Math Academy Way, p. 303](https://justinmath.com/files/the-math-academy-way.pdf)
  - **Foundational:** diagnostics test lower-grade prerequisites; students first do course topics that don't depend on the gaps ("build up some momentum"), and gaps are filled when they begin to block progress. — [Math Academy Way, pp. 304-305](https://justinmath.com/files/the-math-academy-way.pdf)
  - **Content:** per-knowledge-point and per-question analytics identify where students get stuck; when pass rates are low MA adds scaffolding rather than lowering standards. Reported pass rates are 95% first try and 99% within two (internal figures). — [Math Academy Way, pp. 305-306](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] Step-to-prerequisite linking is explicit: MA tracks "the key prerequisites that are used in each part of each lesson." The worked example is the lesson Exponents with Rational Bases, Part 2 (evaluating (-4)^3), whose key prerequisite is Multiplying Negative Numbers, several steps back in the hierarchy. A student stuck at Part 2 gets a targeted review of that prerequisite automatically. — [Math Academy Way, p. 302](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc, FAQ] A failed lesson is halted so initial learning can consolidate; MA claims this "produces an 80% chance of passing the lesson the second time around without any additional" help. After failing twice at the same worked example, reviews on the key prerequisites are assigned. — [Math Academy Way, FAQ section](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc, FAQ] Students are told to submit a best guess after about 5 minutes stuck and "not move forward to the next question until they have worked out the original question themselves, on paper, following along with the solution." — [Math Academy Way, p. 428](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc, FAQ] Students are told not to use reference material during a quiz, "as it will cause the system to make decisions as if you got the question right without relying on any reference material," and to take a best guess even when unsure, then study the solution whether right or wrong. — [Math Academy Way, FAQ](https://justinmath.com/files/the-math-academy-way.pdf)

**Reviews and interleaving trade-off (Ch. 19 and FAQ)**
- [Doc, FAQ] Reviews hold several questions because they must (1) interleave across knowledge points of the topic, (2) assess mastery, defined as "consistently solving problems correctly - not just once," and (3) be robust against guessing. — [Math Academy Way, p. 414](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] MA states the trade-off openly: fully micro-interleaving every topic before it appears on a quiz would need an explicit review of every topic, which "pretty soon... your progress is going to grind to a halt." So MA "give[s] up a little bit of micro-interleaving to enable spaced repetition optimizations" (i.e., FIRe compression). — [Math Academy Way, Ch. 19](https://justinmath.com/files/the-math-academy-way.pdf)

**Quizzes, timing, automaticity (Ch. 20 and FAQ)**
- [Doc] Timed tests are introduced only after the skill is performed "successfully in an untimed setting"; accuracy must precede fluency. MA cites Codding et al. and the US Dept. of Education practice guide (Fuchs et al. 2021): use timed activities to build fluency but "Do not use timed activities to introduce and teach mathematics concepts." — [Math Academy Way, pp. 289-292](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] Quizzes are described as low-stakes and frequent; a student who does less than "well" can retake with different questions after the follow-up reviews. The book cites meta-analyses (as secondary citations, not verified here): Yang et al. 2021, 222 classroom studies, >48,000 students, Hedges' g = 0.50 for class quizzes on achievement; Yang et al. 2023, 24 studies, g = -0.52 on test anxiety. — [Math Academy Way, pp. 292-293](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc, FAQ] MA's quizzes differ from typical classroom ones on purpose: classroom quizzes are "less frequent, students are told what's going to be on it," cover only very recent topics, and allow ample time, which makes them "artificially easy, a biased signal for adapting the pace of learning, a poor measurement of retention & automaticity." MA quizzes are "timed, fully interleaved, and some forgetting has set in," and difficulty is calibrated "tougher if you've been doing well... because the 80-85% accuracy range is the sweet spot for learning." Their purpose is to "pinpoint areas where you are not yet fully automatic (even if you could solve those problems in an untimed open-book setting)." — [Math Academy Way, FAQ, pp. 403-405](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] A passed lesson means "mastered the topic well enough to continue layering," but "probably haven't reached the point of automaticity." Placement diagnostics measure a **conservative** edge of mastery, while learning operates on an **aggressive** edge; so a student who finished a course can be placed lower on a later placement exam. — [Math Academy Way, Ch. 30, p. 380](https://justinmath.com/files/the-math-academy-way.pdf)
- [Founder/Staff] A "rapid-fire" flashcard-style trainer for multiplication tables, trig values/identities and derivative/integral rules is "pretty high on my and Jason's to-do list" (essay dated 2025-10-28). The post gives no design, thresholds or measurement method. — [Skycak, Yes, You Need to be Automatic on Math Facts](https://justinmath.com/yes-you-need-to-be-automatic-on-math-facts/)
- A search for a launch of this feature (Nov 2026) returned nothing relevant, so treat it as not shipped or at least unverified.

**XP, penalties and retries (Ch. 22, pp. 308-316)**
- [Doc] 1 XP = 1 minute of fully focused work for an "average serious (but imperfect) student." Awards: bonus for perfect, full for nearly perfect, most for passable, a little for nearly passable, zero for poor, negative for "blowing off a task." Weekly leagues are optional. — [Math Academy Way, pp. 310-312](https://justinmath.com/files/the-math-academy-way.pdf)
- [Vendor] Without penalties, "XP hackers" complete easy tasks and "submit random guesses to intentionally fail out of tasks that require more effort," which tanks their adaptive schedule. After penalties, MA reports those students' pass rates "jumped from under 50% to over 90%" (internal, unverified). Penalties are calibrated to "how frustrated a teacher, tutor, or guardian sitting next to the student would become." — [Math Academy Way, pp. 313-314](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] On re-attempt MA changes the questions and imposes a delay period, and meanwhile the student continues on other paths. Quizzes are individually randomized. — [Math Academy Way, p. 314](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] Progress (% topics complete) rises only on lesson completion and is deliberately separate from XP, because total XP changes as the spaced-repetition load changes. There is a "hard rule" that, on average, a student has the opportunity to do a lesson at least ~25% of the time. Late in a course progress slows because fewer frontier lessons remain to "knock out" due reviews. — [Math Academy Way, pp. 314-316](https://justinmath.com/files/the-math-academy-way.pdf)

**Diagnostic (Ch. 30, pp. 376-381)**
- [Doc] Diagnostics take 20-40 questions for lower-grade courses (e.g., Prealgebra) and 40-60 for higher-grade (e.g., Calculus), against 500+ without the graph inference. (The website figure in the prior notes is "30-45 minutes"; the two are consistent in scale but not identical metrics.) — [Math Academy Way, p. 376](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] Evidence is a per-topic "plus-minus balance." A correct answer adds to the topic and its prerequisites; an incorrect answer subtracts from the topic and its post-requisites. A correct but excessively slow answer gets a reduced weight. Conflicts (advanced right/simple wrong; right but slow) produce low confidence and "conditional completion," meaning the student starts as though they know it and the system "falls backwards" at the first struggle. — [Math Academy Way, pp. 377-380](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc, FAQ] Student instructions for the diagnostic: click "I don't know" if not solvable in about 3 minutes; do not guess ("a successful guess may cause you to be placed too far"); no external resources; do not spread over many days; do not take when tired. — [Math Academy Way, FAQ](https://justinmath.com/files/the-math-academy-way.pdf)
- [Doc] "Supplemental diagnostics" of at most a handful of questions patch the knowledge profile when the knowledge graph changes. — [Math Academy Way, p. 381](https://justinmath.com/files/the-math-academy-way.pdf)

**Evidence and critique**
- [Critic] A reviewer of the book notes it "has lots of citations" but is "a sales pitch" in part; she names almost none of the sources, and the review does not describe the software's actual schedule. — [Book Review: The Math Academy Way](https://ijfen.substack.com/p/book-review-the-math-academy-way)
- No independent controlled study of MA outcomes was found in this pass either (consistent with the prior notes' gap). MA's pass-rate and penalty effects are all internal.

### Inferences
- The book's most transferable single idea for our app is the **step-to-key-prerequisite link**: each part/step of a problem declares which earlier skills it depends on, so a diagnosed step error can route to a targeted repair review. This is what makes "What went wrong?" actionable.
- MA's reliance on penalties exists because its XP is an extrinsic reward; a free single-user tool has no such adversary, but MA's observation that students dodge hard tasks by guessing is a reminder to treat very fast wrong answers as "rushing" and not as knowledge evidence.
- MA's accuracy-before-fluency rule (no timed work until untimed success) and its use of timed interleaved quizzes as a measurement tool are the clean template for gaokao-style speed training: timing as a later layer, not a default.

### Gaps
- Exact FIRe/XP/speed parameters remain proprietary; the book's chapters on spaced repetition and learning efficiency were not read in full this pass.
- r/mathacademy and Discord threads were inaccessible, so community sentiment on quizzes and reviews comes only from the prior notes' blog sources.
- No evidence on whether MA's quiz difficulty calibration (80-85%) actually yields better transfer than fixed-difficulty quizzes.

---

## 2. ALEKS (Knowledge Space Theory): assessment engine, learning rule, retention checks, accuracy and evidence

### Takeaway
ALEKS's own technical papers show a Bayesian knowledge-state assessment capped at about 30 questions, a simple additive learning rule (target 5 points, with +2 for a second consecutive correct), and a retention model in which newly learned items decay to roughly 60-80% retained depending on how deep they sit in the prerequisite structure. Its retention checks have since been made shorter and targeted by a neural-network forgetting model. Vendor-reported accuracy is good (AUROC ~0.86-0.89), but independent evidence of learning benefit remains the prior notes' meta-analysis finding (equal to traditional teaching).

### Cited Findings
- [Vendor/Research] Initial assessments are capped at 30 questions, one of which is a random "extra problem" that doesn't affect the result. The ideal stop is when every item is in-state (>80% likelihood) or out-of-state (<20%), but most assessments end at the cap with some items uncertain. — [ALEKS: A Practical Perspective on KST (ESSA Tier 4 doc)](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-practical-perspective-knowledge-space-theory.pdf)
- [Vendor/Research] Method: Bayesian update over a distribution of knowledge states; items count as known when summed probability of states containing them exceeds 0.5; each item has a careless-error probability and lucky guesses are assumed zero. — [ALEKS: Assessing Mathematical Knowledge in a Learning Space](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-assessing-learning-space.pdf)
- [Vendor] Reported accuracy on ~3.1 million initial assessments (2012-early 2020): AUROC 0.875 (Sixth-Grade Math), 0.863 (College Algebra), 0.889 (College Placement); accuracy 0.801-0.814. In-state items were answered correctly 74-84% of the time versus ~10-11% for out-of-state items. Authors include ALEKS Corporation staff. — [ALEKS: A Practical Perspective on KST](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-practical-perspective-knowledge-space-theory.pdf)
- [Vendor] Earlier study of 125,786 elementary assessments: predicting a held-out extra item gave a point-biserial that levels near 0.46 (median) at the end of the assessment, with a "learning success" probability of 0.93 (median) for items taken from the outer fringe. — [ALEKS: Assessing Mathematical Knowledge in a Learning Space](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-assessing-learning-space.pdf)
- [Vendor] Learning-mode rule: an item is provisionally learned at a score of 5 (or 3 for "fast-tracked" uncertain items after the initial assessment and for items removed after a progress assessment). Correct +1, second correct in a row +2, incorrect -1 (floor 0); reading an explanation leaves the score unchanged but breaks the streak. Five consecutive incorrect answers count as a failed attempt and the learner is gently prompted to try a different item. Observed success rate 0.81 (Sixth-Grade Math), 0.84 (Algebra I), 0.94 (College Algebra); failure rate 1.5-4.1%. — [ALEKS: A Practical Perspective on KST](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-practical-perspective-knowledge-space-theory.pdf)
- [Vendor] Retention depends on the item's depth in the structure: layer-1 items drop steeply in the first days and level off near 0.6; layer-2 near 0.67; layers 5 and above stay near 0.8 (8,352,006 retention events, 2016-2019). — [ALEKS: A Practical Perspective on KST](https://www.mheducation.com/content/dam/mhe/research/prek-12/essa-tier-4/aleks-practical-perspective-knowledge-space-theory.pdf)
- [Vendor, undated] Knowledge checks were shortened ("shorter, smarter"): the Initial Knowledge Check is now at most 25 questions (down from 30); a neural-network model picks the problems students are most likely to forget; a "strategic delay" precedes revisiting certain problem types; and content at the edge of a student's knowledge decays faster. ALEKS claims students learn "9% more on average" with the new checks (internal, unverified). **Conflict:** the prior notes (and older help pages) say 20-30 or up to 30 questions. — [ALEKS: Shorter, Smarter Knowledge Checks](https://www.mheducation.com/content/dam/mhe/highered/documents/aleks/innovation-shorter-smarter-knowledge-checks.pdf)
- [Research] A randomized A/B experiment on mastery-learning thresholds found students who learned under the higher threshold were less likely to forget, but the advantage shrinks over time and varies with how much students struggle and with subject. The abstract-level page does not give effect sizes. — [JEDM: Using a Randomized Experiment to Compare Mastery Learning Thresholds](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/900)
- [Carried] The EDM 2022 regression-discontinuity study found a 5-vs-3 threshold raised first-week retention by about 0.03, an effect that "has largely disappeared" after several weeks; and the Fang et al. (2019) meta-analysis found ALEKS "as good, but not better than" traditional teaching (15 studies). — [EDM 2022 paper](https://educationaldatamining.org/EDM2022/proceedings/2022.EDM-short-papers.27/2022.EDM-short-papers.27.pdf); [Fang et al. 2019](https://digitalcommons.memphis.edu/facpubs/7254)

### Inferences
- The retention table is the best published evidence we found that "fresh learning" is a fragile state (60-80% retained) and that raising the in-session threshold buys only a short-lived retention bump. It supports a short initial practice gate plus early spaced confirmation rather than long massed overlearning.
- Per-item "depth in the prerequisite structure" predicts retention. An FSRS-by-skill app can capture this cheaply by letting initial stability or difficulty priors depend on graph depth or on the number of dependents.
- ALEKS's move to a forgetting-model-targeted check (not a random sample of all learned items) supports checking only the items most at risk, which is exactly what FSRS retrievability ordering does.

### Gaps
- Exact trigger numbers in the current ALEKS (the 20-topics/5-hours/60-days rules in the prior notes) were not re-verified against the newer "shorter, smarter" release; date of that release is not shown.
- No independent, post-2019 study of ALEKS learning outcomes was found.

---

## 3. Khan Academy: Mastery Challenges, efficacy data, Khanmigo practice, and Official SAT Practice

### Takeaway
Khan's mastery levels now do get spaced "Mastery Challenges" (6 randomized questions over 3 skills, 12-hour windows, level up/down/hold), partly answering the prior notes' "mastery never decays" complaint, but they are optional. Khan's own efficacy studies are observational and vendor-run; the one randomized trial found (NBER, Aug 2026, Khanmigo plus Khan practice) shows small gains (~0.06-0.08 SD per school year) equal to Khan practice without AI, with the AI tutor barely used when students made mistakes. The College Board's SAT practice data are also observational and show diminishing returns per extra practice test.

### Cited Findings
**Mastery Challenges (fills the prior notes' gap)**
- [Doc] Mastery Challenges are optional practice sets in math courses that review skills already worked on. Unlock rule: Familiar on at least 3 skills, Proficient on at least 1, and more than 12 hours since the last one was started. Format: 6 randomized questions over 3 skills (2 per skill), skills from across the course and personalized. Per skill: both correct = level up; both incorrect = level down; one each = same level. Once started you have 12 hours to finish or it resets; only one per 12-hour period. The page does not say whether skill selection uses recency or decay. — [Khan Academy Help: What are Mastery Challenges?](https://support.khanacademy.org/hc/en-us/articles/360037494231)

**Efficacy**
- [Vendor/Observational] Annual study (2022-23): ~350K students in grades 3-8; 30+ minutes/week (18+ hours/year) associated with ~20% greater-than-expected MAP Growth gains (about 9% of students reached this); 9-18 hours/year associated with ~7%. A longitudinal study of ~221K students compared with their own prior years; each additional skill practiced to proficient/mastered is associated with ~0.5 percentage points of gain. Reported effect size 0.36 (comparison unclear). Usage not randomized; Khan authored the studies and the outcome test is from a partner (NWEA). — [Khan Academy Efficacy Results, November 2024](https://blog.khanacademy.org/?p=18194)
- [Research] Two-year cluster RCT (Hamilton County, TN; 18 middle schools; authors Oreopoulos and Low; NBER w35620, Aug 2026) of Khan Academy with the Khanmigo AI tutor in daily remedial math sessions: +1.3 national percentile ranks per term (~0.06-0.08 SD per school year; ~0.14 SD implied for a full year of active participation), similar to Khan practice without AI. 96% tried Khanmigo, but students messaged the tutor in only 17% of exercise sessions where they made a mistake, and most messages were bare answers or suggested-prompt clicks. The authors conclude low engagement is the binding constraint. — [NBER w35620](https://www.nber.org/papers/w35620)
- [Vendor] Khan's May 2026 engineering post on the AI tutor tracks "next-item correctness" (solving the next problem on the same skill without help) as the success metric. Giving the tutor a summary of the student's recent right/wrong attempts raised it by 3.4%, and surfacing unmastered prerequisites with a brief review before harder problems raised it by 2.7% (A/B tests across 0.6-1.4M threads). Showing example problems of other types had no measurable effect. — [Khan Academy blog: Building a Better AI Tutor](https://blog.khanacademy.org/?p=21314)

**SAT practice (College Board / Khan / Bluebook)**
- [Vendor/Observational] 2017 College Board-Khan release: nearly 250,000 test takers; 20 hours of Official SAT Practice on Khan associated with a 115-point average gain ("nearly double" non-users), 6-8 hours with ~90 points. The comparison group is not described, the release uses "associated with," and motivation is flagged as unexplored. — [College Board newsroom, May 2017](https://newsroom.collegeboard.org/new-data-links-20-hours-personalized-official-sat-practice-khan-academy-115-point-average-score)
- [Vendor/Observational] 2025 College Board research report (class of 2025, March 2024 school-day SAT, matched on background and prior achievement): completing 1, 2 or 3+ full-length Bluebook practice tests is associated with SAT scores ~25.7, 45.5 and 61.4 points higher than matched non-practicers, with bigger gains for lower PSAT scorers (e.g., 3+ tests: +79 at PSAT 900 vs +57 at PSAT 1300). Authors state "Estimates are not causal." Raw (unmatched) means rise 61 / 78 / 89 for 1 / 2 / 3+ tests. — [College Board research: Digital SAT Practice Tests (May 2025)](https://research.collegeboard.org/media/pdf/DigitalSATPracticeTests_052025.pdf)
- [Doc] Bluebook mechanics: a short untimed Test Preview with no scoring; full-length tests timed like the real one (you may advance past a section early), automatically scored; "My Practice" for review and analysis; "Get Tailored Practice" generating questions aimed at weak skills; a Student Question Bank of thousands of official questions filterable by section, domain, skill and difficulty; Khan Official SAT Prep; Schoolhouse.world peer tutoring. — [College Board: Bluebook](https://satsuite.collegeboard.org/practice/practice-tests/bluebook)
- [Doc] Tailored practice is based on real-test and full-length Bluebook performance across eight content domains; the Question Bank lets students build quizzes of up to 80 questions per knowledge/skill domain; each quiz returns a score and answer explanations; a printable practice score report is available. — [College Board: Official SAT Practice](https://satsuite.collegeboard.org/sat/practice-preparation/official-sat-practice)

### Inferences
- Khan's Mastery Challenge rule (2 questions per skill; both right/both wrong/mixed) is an economical "noisy-evidence" rule: one fresh-problem miss does not demote, two do. It is a useful alternative to demoting on a single miss, but it also shows how little signal 2 items carry.
- The NBER result is a caution about any optional "ask the AI" help: the intervention was ignored in 83% of mistake moments. Help must be in the flow (e.g., the diagnosis step shown automatically after a miss) to matter.
- College Board's data show diminishing marginal gains per extra full practice test and larger gains for lower scorers; all are non-causal. For a gaokao-style target, full mock exams are a measurement and rehearsal tool, not a learning engine on their own.

### Gaps
- Khan's primary "How do Khan Academy's Mastery levels work?" page failed to load again (client error), so current level-demotion rules beyond the prior notes' 2018 post are unconfirmed.
- No independent (non-Khan, non-College Board) evaluation of the SAT-practice gains was found.
- Khanmigo's in-practice hint mechanics beyond the NBER description and the May 2026 blog are not documented in what was retrieved.

---

## 4. IXL: SmartScore, challenge zone and the diagnostic

### Takeaway
IXL's SmartScore is a 0-100 skill score with asymmetric stakes at the top: large gains and small penalties at low scores, but in the 90-100 "challenge zone" gains drop to 1-2 points while misses cost 3-8. Mastery needs at least 28 questions and up to ten correct in a row near the end. IXL's own research shows small associations with growth; independent reviewers and users describe the system as drill-heavy and the penalty structure as punitive. The IXL diagnostic could not be examined in detail.

### Cited Findings
- [Doc] Score bands: 0-70 learning/practicing ("large SmartScore increases for correct answers and low penalties for incorrect"), 70-90 refining (rising rigor; 90 recommended as "excellence"), 90-100 challenge zone (correct answers add "small (1-2 points)"; penalties larger at 3-8 points). "Students will need to answer as many as 10 questions correctly in a row to achieve mastery"; "a minimum of 28 questions" for most skills to reach 100. SmartScore accounts for correctness, difficulty, recent answers and consistency. A miss never blocks eventual mastery. — [IXL SmartScore Guide (PDF, undated)](https://www.ixl.com/analytics/smart-score-guide.pdf)
- [Vendor] IXL's research page states a SmartScore of 80 indicates proficiency and 100 mastery, and that it is "not a percent correct score." — [IXL research: SmartScore](https://www.ixl.com/research/smartscore)
- [Vendor/Observational] Schonberg (IXL, Aug 2023; 6,290 students grades 2-6 math and 8,736 grades 1-8 ELA, one district, 2021-22): students who reached proficiency via a "fluctuating" path (50-80% correct before proficiency) gained more on IXL's own Real-Time Diagnostic than those whose scores rose steadily (>80% correct): math b = 60.55 per week of that practice (β = .14, p < .001) vs b = 3.44 (β = .04). Not peer-reviewed, authored by IXL staff, observational. — [IXL research: SmartScore](https://www.ixl.com/research/smartscore)
- [Reviewer] Common Sense Education: pros are confidence building, progress tracking and teacher stats; cons are drilling that limits application, questions that "repeat too often," and "point deductions for wrong answers can feel punitive"; "repetition won't encourage critical thinking." No controlled studies are cited. Scheduled diagnostic tests track performance across the year and a recommendations wall lists future skills. — [Common Sense Education: IXL](https://www.commonsense.org/education/reviews/ixl)
- [Competitor, biased] Boddle's article reports user complaints and a petition: a miss at 99 dropping to 89 and needing ten more correct answers. The article's claim of "28 questions in a row" misstates IXL's own wording (minimum of 28 questions). — [Boddle: Does IXL Punish Wrong Answers?](https://www.boddlelearning.com/article/ixl-punishes-wrong-answers)

### Inferences
- The "80 = proficiency, 100 = mastery" split is another instance of a two-tier mastery label, like ALEKS Learned vs Mastered. IXL's top-band asymmetry intentionally forces consistency but is exactly what users call punitive.
- IXL's finding that a middling success rate (50-80%) predicted more diagnostic growth than a high one is a weak, correlational echo of the "desirable difficulty" literature in the prior learning-science notes. It does not support an exact target by itself.

### Gaps
- IXL Real-Time Diagnostic mechanics (levels, item selection, frequency) were not retrieved; the Common Sense page does not describe them.
- Independent IXL efficacy evidence (e.g., Bashkov 2021, Empirical Education 2013, listed on IXL's page) was not evaluated.
- IXL help-center pages on exactly how many points a correct answer is worth below 90, and any time-based rules, were not found.

---

## 5. Carnegie Learning MATHia (and Cognitive Tutor): step-level tutoring, BKT mastery and RCT evidence

### Takeaway
MATHia estimates mastery of each knowledge component with Bayesian Knowledge Tracing, tracks every step, gives three levels of hints, and moves students on when all components in a workspace are estimated mastered (or promotes them without mastery after a problem cap). It is the closest published model of the "step-level diagnosis" feature. The large RAND RCT of its predecessor found no first-year gain and about a 0.20 SD gain in year two for high schools, but the WWC page shows mixed ratings, and Carnegie's own evidence summary has several flagged weaknesses.

### Cited Findings
- [Doc] Each workspace skill value is "an estimate of how likely you know that skill," not percent correct. Correct entries raise it; incorrect entries usually lower it, except for steps with designated "freebie JIT" wrong answers (used when the answer isn't truly wrong or the interface doesn't communicate the expected input). The first two hint levels do not lower the skill; requesting the bottom-out hint (the answer) does; a mistake followed by a bottom-out hint on the same step is not penalized twice; viewing Step-by-Step does not affect skill levels. — [MATHia Help: When and why do skills move?](https://support.carnegielearning.com/help-center/math/mathia/mathia-faqs/article/when-and-why-do-skills-move/)
- [Doc] Students see a Progress Meter and, in mastery workspaces, a "Skillometer" of rings that go from blue to green, reflecting "how likely you are to demonstrate the skill again later." — [MATHia Help: Monitoring My MATHia Progress](https://support.carnegielearning.com/help-center/math/home-connection/mathia-support22/article/monitoring-my-progress-with-the-progress-meter/)
- [Doc] DataShop documentation (2019-2020): "KC mastery is estimated using Bayesian Knowledge Tracing (BKT; Corbett & Anderson, 1994)." Hints have three levels (restate goal; deeper guidance without the answer; the answer). Errors with "JIT" feedback give just-in-time context-sensitive messages. A student moves on when MATHia estimates all workspace KCs mastered; if a fixed maximum number of problems is reached without mastery, the student is promoted without mastery (status values GRADUATED, PROMOTED, NOT_COMPLETED). BKT parameters and the mastery threshold are not given. — [Carnegie Learning MATHia 2019-2020 DataShop Documentation](<https://www.stat.cmu.edu/~brian/nynke/726-2021/project%20HCI%20Prereqs%20%28Elaine,%20Smeet%20&%20Zhou%29/2021-03-09/Carnegie%20Learning%20MATHia%202019-2020%20DataShop%20Documentation.pdf>)
- [Vendor] Carnegie's ESSA report describes MATHia as based on ACT-R with knowledge components, immediate feedback on common errors, hints following the student's own strategy, and problem selection that "maximize[s] time on unmastered components." It does not mention BKT (conflict with the DataShop doc above is one of emphasis, not substance). — [Carnegie Learning 2023 ESSA Math Research Report](https://www.carnegielearning.com/hubfs/PDFs/Marketing%20Collateral%20PDFs/2023-ESSA-Math-Research-Report.pdf?hsLang=en)
- [Research] Pane, Griffin, McCaffrey & Karam (2014), RAND: randomized trial of Cognitive Tutor Algebra I (2 days/week software, 3 days teacher-led) across 147 middle and high schools in seven states, >17,000 students. No significant gains in year one; high schools in year two had about twice the control group's pre-post gains; middle school results were inconclusive. — [EdSurge: The Nature of Big Edtech Research (2013)](https://www.edsurge.com/news/2013-08-27-the-nature-of-big-edtech-research)
- [Research, ratings conflict] The WWC page for the same study (51 districts, high school 5,328 students 1-year and 5,738 2-year; middle school 74 schools) shows findings not statistically significant (1-year HS: intervention -0.02 vs comparison 0.03; 2-year: 0.08 vs -0.08), with a high-school intervention report (reviewed May 2026) and middle-school review that "meet WWC standards without reservations," but also a Dec 2025 single-study review that does not meet group design standards, and an internal inconsistency (a "statistically significant positive effect" line next to "no statistically significant positive findings"). — [IES WWC Study 82101](https://ies.ed.gov/ncee/WWC/study/82101)
- [Vendor] Carnegie summarizes Pane 2014 as +0.20 SD over control (vs 0.22 SD typical annual growth) and a "nearly doubled" claim; the review of that document flagged that 0.20 SD is additive, not a doubling, that the mastery-learning d = 0.5 figure is generic (Kulik et al., 1990) and not MATHia-specific, and that the MATHia "Tier 2" support rests on correlational and small quasi-experimental studies. — [Carnegie Learning 2023 ESSA Math Research Report](https://www.carnegielearning.com/hubfs/PDFs/Marketing%20Collateral%20PDFs/2023-ESSA-Math-Research-Report.pdf?hsLang=en)
- [Critic] Justin Reich warned that educators should be wary of vendor interpretations like "doubles math learning in one year," given incentives throughout the research ecosystem. — [EdSurge](https://www.edsurge.com/news/2013-08-27-the-nature-of-big-edtech-research)

### Inferences
- MATHia's treatment of hints is a ready-made, evidence-informed answer to "do hints break mastery?": free for the first levels, penalized only when the answer is revealed, not double-penalized after a mistake, and "freebie" handling for input-format failures. This maps directly onto an FSRS rating policy.
- The "promoted without mastery" status after a problem cap is a wheel-spinning guard; ALEKS (5 consecutive misses) and ASSISTments (10-question cap) have equivalents. The app needs one too, with a clear "parked, come back later" state.
- The ambiguity of the RAND result (no year-1 effect; decent year-2 effect) is a reminder that tool adoption costs show up early; a "calibration" period in which the app collects data before trusting its own estimates is justified.

### Gaps
- BKT mastery threshold and parameter values are not published in the sources found; Wikipedia-level folklore of a 0.95 threshold was not verified (the search for it returned only generic knowledge-tracing pages).
- WWC rating contradictions on the Pane study could not be resolved from the retrieved page.
- No evidence was found on whether MATHia schedules spaced review across workspaces (the sources describe within-workspace mastery only).

---

## 6. DeltaMath, WeBWorK/MyOpenMath, ASSISTments, Brilliant, and Chinese practice platforms

### Takeaway
DeltaMath is a teacher-assigned randomized-practice and test-correction tool with essentially no published efficacy evidence. WeBWorK-style systems randomize numbers per student with immediate correctness feedback. ASSISTments is the strongest-evidence homework-practice platform found (two RCTs, effects 0.10-0.18 SD) and the only one with a published, concrete spaced-reassessment ladder (7/14/28/56 days). Brilliant has no efficacy evidence found; its streak rule is minimal. For the gaokao context, public documentation of Chinese platforms' practice mechanics is mostly marketing.

### Cited Findings
**DeltaMath**
- [Reviewer] Assignment types include digital question sets (multiple choice, fill-in-the-blank, timed challenges, interactive modeling), test corrections, warmups and guided lessons. Teachers can require a set number of questions or a run of correct answers such as two or three in a row. Each submitted answer shows a detailed solution. A problem log gives a time-stamped record per completed question, filterable by student, assignment or skill. No research is cited. — [Common Sense Education: DeltaMath](https://www.commonsense.org/education/reviews/deltamath)
- [Doc] Test corrections assign targeted practice for the skills tied to missed questions: missing one question assigns practice for only that skill and subtype; missing two on the same skill assigns one skill's practice with more problems; a student with no misses is told no problems are assigned. Linked corrections (PLUS/INTEGRAL plans) pull scores from DeltaMath tests, and teachers can adjust counts via "required" and "add" settings. — [DeltaMath Help: Introduction to Test Corrections](https://help.deltamath.com/introduction-to-test-corrections)

**WeBWorK / MyOpenMath**
- [Doc] WeBWorK gives each student an individualized version of each problem set (numeric values differ), allows repeated attempts and shows immediate correct/incorrect feedback after each attempt. — [Rutgers: What is WeBWorK?](https://sites.math.rutgers.edu/courses/135/135-f14/whatiswebwork.html)
- [Carried] UBC (2013): 47.4% of students with unlimited attempts showed guessing vs 9.7% with a 7-attempt limit, with similar full-mark rates; 29% often used tools like Wolfram Alpha. — [Lo, Merchant & Piccolo, CWSEI](https://cwsei.ubc.ca/files/outcomes/EOY/Lo-Merchant-Piccolo_WebWork-Math_CWSEI-EOY2013.pdf)
- A search for MyOpenMath-specific randomization documentation returned only generic LMS pages; no MyOpenMath primary doc was retrieved.

**ASSISTments (added because it has the best RCT evidence)**
- [Doc/Blog] A Skill Builder is complete after 3 consecutive correct answers on a topic ("temporary mastery"); using a hint resets the streak; if a student cannot finish within 10 questions the program stops and says "try again tomorrow." Reports show time per question, hint use and every submitted answer. ARRS (Automated Reassessment and Relearning System): after completion, a reassessment of one random question from the same bank arrives 7 days later; a correct answer schedules the next check at 14, then 28, then 56 days; an error triggers remediation, i.e., redoing the Skill Builder under the original rule. The post notes ARRS is still in development for wide release and its retention claim is anecdotal. — [ASSISTments: How Skill Builders Work](https://www.assistments.org/blog-posts/how-assistments-skillbuilders-works-in-my-class-and-why-it-will-work-for-you-too)
- [Vendor] ARRS research summary: RCT with 97 8th graders (one suburban Massachusetts school, two teachers, 32 skills); students did better on skills that were reassessed and relearned, especially low pretest students; no effect sizes or intervals reported on the page. — [ASSISTments: Reassessing and Relearning](https://www.assistments.org/blog-posts/our-research-reassessing-and-relearning)
- [Research] Replication RCT in North Carolina (WestEd): 63 schools, 9,073 seventh graders (2019-20), outcome the end-of-8th-grade state math test one year after the program: +0.10 SD (p = 0.01). The original Maine RCT found 0.18 SD. Mechanism: homework answers are checked immediately, with hints/scaffolds, and teachers get real-time reports to focus class review. — [Arnold Ventures summary of the replication RCT](https://www.arnoldventures.org/stories/a-replication-randomized-controlled-trial-rct-of-assistments-an-online-study-tool-to-improve-student-math-outcomes-in-seventh-grade)

**Brilliant**
- [Doc] Streak: complete 3 problems or one full concept per day; missed days are covered by an available Streak Charge, otherwise the streak resets to 0. The help page says nothing on spaced review or on how mistakes are handled. — [Brilliant Help: What is a streak?](https://brilliant.org/help/features/what-is-a-streak/)
- [Carried] A six-month user review noted wrong or ambiguous answers and "streaks are the only motivator"; a 2026 reviewer says Brilliant resurfaces struggled concepts at spaced intervals and launched the Koji AI tutor on 2026-05-29. — [Cedar Sanderson review](https://cedarlila.substack.com/p/a-review-brilliant); [SkillScouter review](https://skillscouter.com/brilliant-review-math-science-coding/)
- No efficacy study of Brilliant was found.

**Chinese platforms / adaptive learning evidence**
- [Research abstract] Two randomized efficacy studies of Squirrel AI Learning with Chinese eighth-graders from two provinces found greater gains on a math test than whole-class teaching and than small-group teaching by expert teachers; sample sizes and effect sizes are not on the retrieved page (full text via DOI 10.1080/10494820.2020.1808794). — [SRI publication page](https://sri.com/publication/education-learning-pubs/when-adaptive-learning-is-effective-learning-comparison-of-an-adaptive-learning-system-to-teacher-led-instruction)
- [Marketing] The Yuantiku (猿题库) store listing offers practice by province and knowledge point, an automatic 错题本 (mistake book) sorted by knowledge point, and a practice report that "intelligently assesses mastery"; it does not describe how problems are selected, and the "400 million users" claim is unverified. — [App Store listing](https://apps.apple.com/cz/app/%E7%8C%BF%E9%A2%98%E5%BA%93-%E4%B8%AD%E5%B0%8F%E5%AD%A6%E7%94%9F%E5%88%B7%E9%A2%98%E5%88%A9%E5%99%A8/id852188634?l=cs)
- [Carried] A 2026 NetEase article warns a 错题本 becomes a "regret notebook" if errors are copied but not analyzed, recommending: where it went wrong, why, how to fix, a similar problem, one reminder line. — [163.com](https://www.163.com/dy/article/L45VFT0V0556FBHS.html)

### Inferences
- ASSISTments' ladder (7, 14, 28, 56 days, with a single random question and failure triggering a re-do of the mastery gate) is a useful sanity baseline against which to compare FSRS intervals for skills, and its 10-question cap is a simple wheel-spinning guard.
- ASSISTments' evidence is for teacher-linked homework with immediate feedback, not for a solo learner; but it shows that instant correctness feedback plus hints is enough to produce measurable (small) gains at scale.
- The gaokao ecosystem's public tools center on 错题本 by knowledge point and mock-exam practice; nothing found documents spaced scheduling of mistakes. That is the gap Toishi fills.

### Gaps
- DeltaMath: no primary documentation of randomization, retry limits or mastery rules found (the help-center home and the Common Sense page do not state them); no efficacy evidence found.
- MyOpenMath: no primary source retrieved.
- Chinese gaokao platforms: no primary documentation of adaptive or spaced mechanics (e.g., Zuoyebang, Yuanfudao/Xiaoyuan, Squirrel AI internals) was retrieved; the Squirrel AI result is an abstract only.
- Brilliant: no spaced-review documentation or efficacy data.

---

## 7. UWorld and Kaplan (USMLE/NCLEX question banks): modes, test builder, filters, analytics, percentiles, self-assessments

### Takeaway
UWorld's design is a tutor-mode/timed-mode split, a "create test" builder with unused/incorrect/marked/all filters, per-question peer answer percentages, subject/system/topic reports, an overall percentile and time-per-question benchmark, and separate self-assessment exams that return an estimated score. UWorld's own advice is tutor mode for the first pass, then timed random 40-question blocks for the second, with triage of explanation review. Kaplan's public product page is thin. A key caveat from users and the literature: raw Qbank percent correct is a weak score predictor, while full-length self-assessments are better.

### Cited Findings
**UWorld**
- [Doc, NCLEX/nursing product blog] Tutor mode (default on) shows answer and rationale after each question; timed mode (default off) is for practice days to simulate pressure; turning tutor mode off shows results only at the end. The Create Test page offers unused, incorrect, marked, all and custom modes; "Marked" is for questions flagged for further study "including ones answered correctly but guessed"; "Incorrect" is for self-remediation. Rationales are presented as "the most important part." Example schedule: ~2 hours daily in tutor mode and one exam-simulation day. — [UWorld Nursing Blog: 7 Tips for Using the UWorld NCLEX Qbank](https://nursing.uworld.com/blog/7-tips-for-using-the-uworld-nclex-qbank/)
- [Doc, USMLE product page] Tutor and timed modes; custom tests built by subject and system; a Performance section with Overall, Reports (by subject, system, topic) and Graphs (by date and by test); after answering, the percentage of students choosing each option; an overall percentile rank and average time per question versus other users; Previous Tests & Quizzes with resume and question-by-question review; up to three self-assessments per exam (Step 1 and Step 2 CK), each four 60-minute blocks of 40 questions, returning explanations, ranking and an estimated USMLE score; spaced-repetition flashcards (ReadyDecks, SmartCards); a Notebook; and a Study Planner that builds a daily schedule from your availability. — [UWorld USMLE features](https://medical.uworld.com/usmle/features/)
- [Vendor guidance] UWorld's blog on a second pass: reset the bank to clear first-pass statistics; tutor mode for the first pass (learning, no concern for timing), timed random 40-question blocks (90 seconds/question, ~1 hour per block) for the second; 60-120 questions per day over 4-8 weeks; review triage rule "(100 - your average score on UWorld question blocks) = cutoff for review," meaning review missed questions that at least that percentage of other students answered correctly (e.g., at a 70% average, review misses that 30%+ of peers got right). No absolute percent-correct target is given. If time is short, redo only incorrect questions. — [UWorld blog: A Complete Guide To Getting Through the UWorld Step 1 QBank Twice](https://medical.uworld.com/?p=5264)
- [User, 2016 thread] Posters on Student Doctor Network mostly say UWorld percentages are a weak predictor ("Use it to learn. Ignore the percentages"), with some reporting their first-pass percentage matched their score; first-pass averages of 60-80% were reported; posters noted peer averages (about 50-65%) are inflated by second passes and block-by-subject study. These are 2016 posts; exam and bank have changed. — [Student Doctor Network thread](https://forums.studentdoctor.net/threads/uworld-average.1186593/post-17536393)
- [Competitor, flagged] The iatroX blog (which sells a rival bank) lists five factors that distort percent correct (reset/second pass, tutor vs timed, question age, block composition, review habits) and says raw percentage "correlates only loosely" with the real score; no data or sources given. Treat as opinion. — [iatroX: What Is a Good UWorld Percentage?](https://www.iatrox.com/blog/what-is-a-good-uworld-percentage)

**Kaplan**
- [Doc] Kaplan's Step 1 Qbank page lists "3,200+" questions in one place and "2,600+" in another (internally inconsistent); test building by organ system or discipline; two full-length practice tests; succinct and in-depth explanations; an AI Tutor; "detailed progress reports." Tutor/timed modes, peer comparison, score predictors and a study planner are not described on the page. — [Kaplan USMLE Step 1 Qbank](https://www.kaptest.com/usmle/practice/usmle-step-1-qbank)

### Inferences
- The UWorld mode split is really a **learning phase vs performance phase** split, with a reset of statistics between phases so the analytics measure the right thing. An app tracking FSRS state needs the same separation: "practice/learn" sessions (instant feedback, count for scheduling) vs "exam sim" sessions (feedback deferred, reported as a measurement).
- "Marked" doubles as a lightweight confidence flag (correct but guessed). That is a one-tap, zero-modeling way to record low-confidence successes.
- The peer-answer-percentage display is a cheap difficulty signal; a single-user app has no peers, but could show its own item difficulty and personal historical success.
- Percentiles require a population. An offline free app cannot honestly show them without norm data; it can show score estimates relative to a target (see section 10).

### Gaps
- UWorld's omitted-question filter, exact percentile calculation and self-assessment score model are not documented in what was retrieved; the NCLEX blog is for a different UWorld product than USMLE.
- Kaplan: no features such as modes, filters or analytics beyond a marketing page; no user reviews retrieved.
- Reddit r/Step1 and r/Step2 threads were not retrievable (search returned mirror links but fetches failed); sentiment comes from a 2016 SDN thread plus vendor blogs.

---

## 8. AMBOSS: difficulty ratings, adaptive sessions, knowledge profile, readiness metrics

### Takeaway
AMBOSS is the most transparent qbank about its modeling: question difficulty is a data-derived five-level "hammer" percentile, a Rasch/IRT knowledge profile per topic drives adaptive sessions that deliberately target the learner's weakest areas while recycling older misses (spaced-repetition-like), and a separate score predictor uses practice-exam results rather than Qbank activity. The headline accuracy numbers are the vendor's own.

### Cited Findings
- [Doc] Difficulty is "automatically determined by how often it is answered correctly or incorrectly in AMBOSS": 1 hammer = easiest 20%, 2 = between bottom 20% and upper 50%, 3 = between lower 50% and upper 20%, 4 = harder than lower 80% but easier than top 5%, 5 = hardest 5%. Shown in study mode and review; filterable when building a session. — [AMBOSS Help: Question difficulty](https://support.amboss.com/hc/en-us/articles/360035679652)
- [Doc] Session builder: Study mode or Exam mode ("set up exactly like the USMLE testing environment"); filters by discipline, system, difficulty, topics (via a Study Objective), saved question folders, marked questions only, and images-only; a toggle for adaptive question selection; unanswered/incorrect filters were not listed on that page. — [AMBOSS Help: Creating a Qbank session](https://support.amboss.com/hc/en-us/articles/360032477132)
- [Doc] Review: per-question peer statistics, "Show All Explanations" for incorrect answers, hyperlinked terms and linked library articles, a sidebar of results with per-question difficulty, and Study Summary and Performance Analysis views. — [AMBOSS Help: Reviewing a Qbank session](https://support.amboss.com/hc/en-us/articles/360035979311)
- [Doc] Adaptive question sessions: filter by study objective; prefer unanswered questions, and if too few, recycle answered ones "with older incorrect questions returning first, similar to spaced repetition"; for each candidate estimate the chance of a correct answer and pick the one where the learner appears weakest, then simulate the profile as if answered correctly to shift the next pick (an approach "similar to Computerized Adaptive Testing"); only user control is session size (3-10 recommended). — [AMBOSS Help: Adaptive Question Sessions](https://support.amboss.com/hc/en-us/articles/45511273700369)
- [Vendor] Knowledge profile: a Rasch model per topic/competency updated after each answer, weighting surprising answers more, with older activity discounted ("Ebbinghaus forgetting curve" inspiration). Readiness outputs: Equated Percent Correct (expected success across the whole objective's pool, difficulty- and relevance-adjusted, shown after 40 questions), Exam Score Estimate with a confidence range (Step 2), Probability of Passing (Step 1). A separate Score Predictor (Step 1, Step 2, COMLEX) uses NBME, UWorld and AMBOSS self-assessments and dates, not Qbank activity. Validation against 7,244 self-reported Step 2 CK scores: mean absolute error 8.52 points, ~23% below a naive baseline; AMBOSS estimates theoretical limit near 6 points. Full white paper not reviewed; self-reported outcomes. — [AMBOSS blog: How does AMBOSS personalize your prep?](https://blog.amboss.com/us/knowledge-profile)
- [Doc] AMBOSS feature page: 13,000+ questions; hammer ratings; study plans; High-Yield Mode; AI-powered Study Summary with peer comparison; Score Predictor with pass likelihood; learning cards; Anki integration (AnKing). — [AMBOSS Product Features](https://www.amboss.com/us/features?tab=learn)
- [User, undated] In a support-forum thread on AMBOSS vs UWorld for shelf exams, commenters say AMBOSS questions represent shelf material well and help with Step 2, one reported similar scores to UWorld users for similar effort, and one relayed a secondhand claim that AMBOSS questions can be "nitpicky" with red herrings. — [AMBOSS support community post](https://support.amboss.com/hc/de/community/posts/4403408421012/comments/4403711021716)

### Inferences
- AMBOSS's two-tier design (a Qbank-activity-based competence estimate, and a separate practice-exam-based score predictor) is a good model for the app: use the fine-grained model for choosing what to practice, and full mock exams for estimating performance.
- The "pick the item you're weakest on, simulate it as correct, repeat" loop is a cheap greedy selection that avoids serving ten items on one weak skill; it is portable to FSRS retrievability or to a per-skill P(correct).
- "Wrong answers the model expected you to get right are especially informative" mirrors Math Academy's accuracy-time conflict handling and the hypercorrection logic in the prior notes.

### Gaps
- The AMBOSS white paper and independent validation of the score predictor/EPC were not reviewed; all accuracy numbers are vendor-reported.
- Learning-card spaced-repetition scheduling is not described in the sources retrieved.

---

## 9. Magoosh, College Board Bluebook (test-day structure) and UCAT (Medify)

### Takeaway
Magoosh and Medify document a generic bank-plus-mocks-plus-estimate product with strong marketing claims and little disclosed methodology. The one detailed look at mock construction is Medify: each mock is built as a fixed, ordered unit and calibrated on a pilot student group before release, and anecdotal user reports suggest Medify scores run low relative to official UCAT mocks and the real test for some users. Bluebook is fully official and free, its practice tests are timed and scored, with weak-skill "Tailored Practice."

### Cited Findings
**Magoosh (GRE)**
- [Vendor] Over 1,600 practice questions; a video explanation for every question; custom study schedules from 1 week to 6 months; a score predictor that compares performance with past students' data; up to six timed full-length tests; a +5 total score guarantee and a 7-day money-back guarantee on premium plans. No adaptivity or analytics detail on the page. — [Magoosh GRE plans](https://gre.magoosh.com/plans)

**Medify (UCAT)**
- [Vendor] 20,000+ questions, 25 full mocks, 34 mini-mocks; scores receive a percentile defined as the proportion of test takers outperformed, though the page also says "other students in your year" (an internal inconsistency); a "review function" collects performance data; unsourced claims include "students who answered more UCAT practice questions performed better," "160 million" questions answered last year and "2 in 3 UCAT takers use Medify." — [Medify: UCAT question bank](https://medify.co/resources/ucat-question-bank)
- [Vendor] Mock construction: each mock is built as a complete unit from specific sub-topics in a fixed order to replicate pacing, difficulty progression and question types; the questions are trialed with a student group and those scores are used to map raw marks to standardized scores on a 300-900 scale. No prediction-accuracy data are given. — [Medify Help: How our mocks are built](https://help.medify.co/en/articles/10206866-how-our-mocks-are-built)
- [User, anecdotal] In a Reddit thread (r/UCAT), commenters report official mocks track the real score better than Medify, which one said "definitely downscales scores"; others saw Medify and official mocks agree. Small sample, individual reports. — [r/UCAT thread via redlib](https://redlib.ssps.io/r/UCAT/comments/1lcj661/do_official_mocks_inflate_ones_scores)
- Searches surfaced no UWorld UCAT product, so the "UWorld/Medify for UCAT" pairing in the brief is treated as Medify only.

**Bluebook**
- See section 3 for Bluebook features and the College Board matched-practice report.

### Inferences
- A mock exam's value depends on calibration against the real score scale; the best a free offline app can do is use the exam's official score-conversion or marking scheme for its own mock papers and display scores as a range, not a percentile.
- Anecdotal "mock harsher/easier than real" noise argues for showing score estimates with a visible error band and for letting the user enter real past-paper scores to self-calibrate.

### Gaps
- Kaplan, Magoosh and Medify analytics, filters and mode details were not retrievable; no independent data on their predictive validity were found.
- No gaokao mock-exam platform documentation was retrieved.

---

## 10. Published evidence on question-bank use, self-assessment predictiveness and what it implies

### Takeaway
All evidence on qbank use is observational: more questions completed and more full-length practice exams are associated with higher exam scores after controlling for prior ability, with modest per-question effects. Full-length self-assessments predict real scores better than raw Qbank percentages, but typical errors remain several points. No study compared tutor vs timed mode or incorrect-only vs all-question reruns.

### Cited Findings
- [Observational] Deng, Gluckstein & Larsen (2015): 72 medical students; all used practice MCQs (mean 3,870); MCQs completed was an independent predictor of Step 1 score (unstandardized B = 2.2 x 10^-3, i.e., about 2 points per 1,000 questions by my arithmetic), alongside MCAT, honours grades, and test anxiety (negative). Anki use 31%, Firecracker 49%. — [PMC4673073](https://pmc.ncbi.nlm.nih.gov/articles/PMC4673073)
- [Observational] Burk-Rafel et al. (2017): 274 students (82.5% response); average 3,597 practice MCQs; starting earlier, more review-book use and more practice questions were each associated with higher Step 1 scores controlling for MCAT, preclinical performance and score goal (adjusted R reported as 0.56 in the abstract). — [Academic Medicine, doi:10.1097/acm.0000000000001916](https://doi.org/10.1097/acm.0000000000001916)
- [Observational] Cureus (2020): 399 responses; UWorld practice test scores were the most predictive of Step 1 among the resources studied, NBME forms next; taking six or more practice tests was associated with higher scores with an optimum of six to nine; the authors' updated predictor was within 3.8 points (1.6%) of actual. — [PMC7198101](https://pmc.ncbi.nlm.nih.gov/articles/PMC7198101)
- [Observational] A single-CBSSA projection model: predicted Step 1 = 292 - (292 - CBSSA score) x 0.9875^(days out); mean absolute prediction error 7.7-7.8 points; 72.1% and 96.7% of true scores fell within one and two SD of prediction (2017 data); one school, ~40 respondents per year. — [PMC8368818](https://pmc.ncbi.nlm.nih.gov/articles/PMC8368818)
- [Observational] ScholarRx Qmax (BMC Med Educ, 2026; two cohorts n = 97 and n = 103): voluntary use of practice questions was associated with higher CBSE scores and with taking and passing Step 1 on schedule in both curricula. — [PMC13560434](https://pmc.ncbi.nlm.nih.gov/articles/PMC13560434)
- [Observational] Anesthesiology residents (2026): in-training exam scores were higher for residents completing >500 Qbank questions, and those above the 90th percentile completed >1,000 on average. — [doi:10.46374/volxxviii_issue2_walsh](https://doi.org/10.46374/volxxviii_issue2_walsh)
- [Research, systematic review] A 2026 review of 11 studies on Anki in medical education found three showing a consistent positive association with Step 1 (high-frequency users +4-13 points, one dose-response), more mixed results for course exams, one Step 2 CK study with no benefit, and mostly observational evidence. — [PMC13197492](https://pmc.ncbi.nlm.nih.gov/articles/PMC13197492)
- [Competitor, unsourced] iatroX asserts r about 0.85-0.88 for UWSA 2 vs the real Step 2 CK score, NBME forms running 5-12 points low, and r about 0.6-0.7 for Qbank percentage; no sources are given. — [iatroX: Score Predictors Compared](https://www.iatrox.com/blog/score-predictors-compared-how-accurate-are-they)
- No study was found comparing tutor mode with timed mode, or incorrect-only with full re-passes, for learning outcomes.

### Inferences
- The per-question effect (~2 points per 1,000 questions after adjustment) and the diminishing returns per extra practice test (College Board) together argue for quality of review (explanations, error analysis, spacing) over raw volume, but the evidence cannot separate these.
- Qbank percent correct depends on mode, repetition and selection, so a fair readiness measure needs a fixed, comparable instrument: full-length untouched mocks or a per-skill model that adjusts for item difficulty (AMBOSS EPC).

### Gaps
- Pre-registered or randomized comparisons of qbank features (tutor vs timed; spaced re-serving) are absent from what was found.
- Evidence for non-medical banks (UCAT, GRE, Chinese 题库) is absent apart from College Board data.

---

## 11. Cross-platform comparison and the adopt / adapt / avoid feature list for Toishi

### Takeaway
The platforms converge on a few mechanics: a provisional-vs-confirmed mastery distinction, a separate timed cumulative check, mistake-driven remediation that routes to prerequisites without lowering the bar, one-tap review sets (incorrect/marked), and exam-readiness estimates from full mocks rather than from drill percentages. They diverge on penalties and gamification, which are mostly unnecessary or counterproductive in a free single-user tool. Below is the concrete list; items are tagged by the evidence strength behind them.

### Cited Findings
Summary matrix (derived from the sourced sections above; evidence column reflects the weakest link):

| Platform | Mastery criterion | Review / retention | Wrong-answer handling | Adaptivity | Timing | Analytics | Evidence |
|---|---|---|---|---|---|---|---|
| Math Academy | Consistent correctness on multi-question tasks; lesson pass = 2 correct in a row per knowledge point (prior notes) | FIRe spaced reviews + timed interleaved quizzes (Sec. 1) | Pause, other topics, targeted prerequisite review, retake with new questions | Knowledge frontier + diagnostic | Quizzes timed; accuracy before speed | XP, progress separate from XP | Internal only |
| ALEKS | Score 5 in learning mode, then confirmed in a knowledge check (Sec. 2) | Targeted checks; forgetting model | -1 per miss, 5 straight misses = try different item | Knowledge-state frontier | None in learning | Pie of mastered/learned/remaining | Vendor + meta-analysis (null vs traditional) |
| Khan | Level points; mastery challenges 2 Qs per skill (Sec. 3) | Optional Mastery Challenge | Level down on 2 misses | Course/unit based | 12-hour windows | Levels | Observational + one small RCT |
| IXL | SmartScore 100 (80 = proficient) | None found | Larger penalties near 100 | Difficulty rises with score | None | SmartScore, diagnostic | Vendor observational |
| MATHia | BKT estimate for all KCs in workspace | Within-workspace only (found) | 3-level hints, step-level errors | Picks unmastered KCs | Problem cap | Skillometer | Mixed RCT (WWC) |
| ASSISTments | 3 correct in a row, no hints | ARRS 7/14/28/56 days | Hint resets streak; 10-question cap | Skill builder sets | None | Teacher reports | Two RCTs (0.10-0.18 SD) |
| UWorld | None (bank) | Reset / second pass, flashcards | Incorrect and marked filters | None (manual) | Tutor vs timed | Percentile, subject/system reports | Observational |
| AMBOSS | Rasch profile per topic | Older misses recycled first | Peer stats, linked articles | CAT-like sessions | Study vs exam mode | EPC, score estimate | Vendor + one validation |
| Bluebook | Official scores | Not scheduled | Review + Tailored Practice | Tailored sets | Timed full tests | Score reports | Observational |

### Inferences
These are my recommendations, not findings; each cites the sourced evidence in sections above.

**ADOPT (strong support and cheap to build)**
1. **Two-stage mastery status: "Learned (provisional)" -> "Confirmed" on first success at a spaced interval with a fresh problem.** Basis: ALEKS Learned/Mastered and retention decay to 60-80% (Sec. 2); MA conditional completion; IXL 80/100 split. Keep ALEKS-style safe practice that doesn't change scheduling.
2. **Step-to-key-prerequisite links on every problem step**, so a diagnosed wrong step ("What went wrong?") triggers a targeted repair review on the exact prerequisite and a retake with a fresh problem after a delay. Basis: MA Ch. 21 (Sec. 1).
3. **Separate timed cumulative "checkpoint" mode**, interleaved, closed-book, not announced by topic, only on skills already correct untimed; each miss queues an immediate repair review; allow a retake with different questions. Calibrate difficulty toward ~80-85% accuracy. Basis: MA Ch. 20 and FAQ (Sec. 1). Report speed on the skill page but do not make speed a default requirement.
4. **Learning-phase vs exam-phase session modes with a stats reset between them.** Tutor (instant feedback, counts for scheduling) vs Exam (feedback deferred to the end, reported as a measurement, scored with the exam's real marking scheme). Basis: UWorld/AMBOSS modes and UWorld's reset guidance (Sec. 7-8).
5. **Session builder with filters:** due, new, incorrect-only, marked, by skill/domain, by difficulty, by exam section, saved sets. Basis: UWorld Create Test, AMBOSS filters, Bluebook Question Bank (Sec. 3, 7, 8). Let "marked" also mean "correct but guessed" (UWorld) and feed a shorter next interval.
6. **Hint policy:** first hints free, bottom-out hint counts as a miss for the step, no double penalty after a mistake, and "freebie" handling for answers that fail only on input format (show "interpreted as" before submit). Basis: MATHia (Sec. 5).
7. **Wheel-spinning guard:** after N consecutive misses or a per-session cap (ALEKS 5 straight misses; ASSISTments 10 questions; MATHia promotion without mastery), park the skill, work elsewhere, and return in a few days (MA reports an 80% second-attempt pass after a break). Basis: Sec. 1, 2, 5, 6.
8. **Exam-readiness estimate from full mocks plus a per-skill model**, displayed as a range with an error band, kept separate from drill percent correct. Basis: AMBOSS (EPC vs Score Predictor), UWorld self-assessments, College Board report (Sec. 3, 8, 10). Make the per-skill expected-score view a weighted sum of current retrievability over the exam blueprint.
9. **Honest decay display:** skill strength derived from current retrievability, never a sticky high-water mark. Basis: Khan complaint in prior notes plus Mastery Challenge level-down rule.
10. **Fresh problem on retry + short delay before re-attempt.** Basis: MA (Sec. 1), consistent with the app's design.

**ADAPT (good idea, needs modification for a solo offline learner)**
11. **Khan-style micro-check:** 2 fresh questions per skill (both right = up, both wrong = down, split = hold) as an optional "noise-resistant" confirmation, instead of demoting on one miss.
12. **AMBOSS-style greedy weak-spot selection** (pick the item with lowest predicted P(correct), simulate success, repeat; recycle older misses first) as a "Targeted drill" mode beside the FSRS queue.
13. **Difficulty tiers (AMBOSS hammers):** author-estimated difficulty first, then personal calibration from the user's own results; avoid peer percentiles.
14. **ASSISTments ARRS ladder (7/14/28/56 days)** as the initial-interval prior and as a transparent "why is this due?" reference alongside FSRS.
15. **ALEKS-style periodic cumulative check** (e.g., after N new skills or ~60 days), but non-blocking and with demotions explained and dampened.
16. **UWorld review triage:** an optional rule to skim explanations for hard items the user is unlikely to retain and spend effort on misses that other (or earlier-self) attempts show are learnable. Vendor-recommended, unvalidated; make it a suggestion.
17. **MA-style effort units** (minutes, not points) for a daily goal and a configurable floor on new-skill time (~25%) so reviews don't crowd out progress; keep "progress" (skills confirmed) separate from effort.
18. **Placement:** adaptive, with an explicit "I don't know" after a time threshold, graph inference up/down, reduced credit for slow correct answers, conservative placement edge with conditional completion, resumable and re-runnable. Basis: MA Ch. 30, ALEKS.

**AVOID**
19. **Blocking knowledge checks and cascading demotions** (ALEKS complaints in prior notes) and **steep top-band penalties** (IXL 1-2 point gains vs 3-8 point losses).
20. **Sticky mastery** that never decays (Khan complaint) and **streak-centric motivation** (prior notes' streak research; Brilliant's streak is the only motivator).
21. **Leaderboards/leagues and negative XP;** MA needs them to police adversarial students, a single-user tool does not.
22. **Percentile claims without a norm population** (Medify's ambiguous "students in your year"; UWorld/AMBOSS peer data). Use score ranges and the user's own history.
23. **Treating raw question-bank percent as readiness** (modes, repeats and block selection distort it).
24. **Optional "ask the AI" help as the main remediation channel** (NBER: used in 17% of mistake sessions). If AI help is added, show the diagnosis automatically after a miss.
25. **Topic-labeled reviews and pre-announced quizzes** (MA critiques in prior notes; MA's own rationale for unannounced quizzes).

**Gaokao-specific notes (inference, not researched in depth)**
- Gaokao papers are heavy on multi-step written solutions with step-wise marking; this makes step-level error diagnosis (MATHia-style) and step-linked prerequisite repair more valuable than multiple-choice-centric designs such as USMLE banks.
- The widely used 错题本 practice only works if analyzed (NetEase article, Sec. 6); the app's mistake bank should require a short cause tag plus a scheduled similar-problem retry, not just storage.
- Timed full mocks should use the real paper structure and marking scheme, with visible error bands; the app should let the user enter real mock-exam results to calibrate its estimates.

### Gaps
- Most mechanics are vendor-described; very few have causal evidence (ASSISTments, Cognitive Tutor and the Khanmigo RCT are the exceptions).
- Whether a Learned-then-Confirmed split, MA-style calibrated quizzes, or greedy weak-spot selection actually improve outcomes vs plain FSRS on fresh problems has not been tested in any source found.
- Reddit and Discord sentiment (r/mathacademy, r/Step1, r/Step2, r/UCAT, r/Sat) is thin because mirrors failed; user-complaint coverage leans on blogs, forum threads and review sites.
- The call count for this task far exceeded the usual guideline because the brief spanned about 20 platforms; some platforms (DeltaMath, Kaplan, Magoosh, MyOpenMath, IXL diagnostic) remain lightly sourced.
