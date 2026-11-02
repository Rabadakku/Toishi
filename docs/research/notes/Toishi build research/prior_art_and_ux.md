# Prior Art and UX Lessons for an FSRS-Scheduled Problem-Solving App ("Anki for problem solving")

Research date: 2026-11-01. Labels used below: **[Doc]** = vendor documentation or official release notes; **[Founder/Staff]** = claims by the product's own people (promotional, unverified); **[User]** = an individual user's report or opinion; **[Critic]** = an outside expert's critique; **[Research]** = peer-reviewed or institutional study. Dates are given for user reports wherever the source showed them.

Coverage caveat: the session's shared web-search budget ran out partway through, so a few planned sub-topics (Mathigon, RemNote/Mochi, Exercism, Japanese/Korean study apps, more Reddit threads) could not be researched. These are listed under Gaps.

---

## 1. Math Academy: how the system works and what adult/college users report

### Takeaway
Math Academy is the closest existing analogue to the planned app. It uses a dense prerequisite/"encompassing" knowledge graph, an adaptive diagnostic, short lessons that open with worked examples, and spaced reviews in which credit from advanced problems trickles down to component skills (FIRe). Timed, interleaved quizzes come every ~150 XP. Adults consistently praise the structure and the manageable review load. Recurring complaints are a "brutal" diagnostic, an opaque task queue, untrustworthy pace estimates, quiz stress, multiple-choice shortcuts, a procedural/shallow bias, and no easy way to tell the system "I don't know this topic."

### Cited Findings

**Mechanics (documented)**
- [Doc] The diagnostic is adaptive and takes about 30–45 minutes, and it can be split across sessions. It places the student at their "knowledge frontier," measures both mastery and automaticity, and flags missing foundations from lower courses. The report includes a placement recommendation, estimated completion dates for several daily-XP options, and per-topic mastery. — [Math Academy: How It Works](https://www.mathacademy.com/how-it-works)
- [Doc] Diagnostic algorithm: it compresses the graph into a minimal covering set, then repeatedly asks the most informative question. A correct answer counts as positive evidence for the topic, its prerequisites and related topics. A wrong answer counts as negative evidence for the topic and its postrequisites. Topics with mixed evidence are marked "conditionally completed," and a slow correct answer can carry less weight. The course-relevant 500–1,000 topics are reduced "by an order of magnitude" in questions asked. — [Math Academy: How Our AI Works](https://mathacademy.com/how-our-ai-works)
- [Doc] If a student later struggles with a "conditionally completed" topic, the system starts "falling backwards" along the relevant learning paths. — [How Our AI Works](https://mathacademy.com/how-our-ai-works)
- [Doc] Missing foundations are handled lazily: students first work on course topics that don't depend on the gaps, and the gaps are filled once they block progress. — [How Our AI Works](https://mathacademy.com/how-our-ai-works)
- [Doc] Lessons are split into small "knowledge points," and each opens with a fully worked example. There are up to 5 practice problems per example, and two correct in a row advances to the next knowledge point. Every question has an explanation. — [How It Works](https://www.mathacademy.com/how-it-works)
- [Doc] The scaffolding is roughly 10x finer than a textbook's. A typical calculus textbook has ~100 sections, while the MA calculus course has ~300 topics × ~3 knowledge points ≈ 1,000 steps. Problem solving starts "within minutes" of a new lesson, after a "minimum necessary dose" of explanation. — [Math Academy Pedagogy](https://mathacademy.com/pedagogy)
- [Doc] Non-interference: new concepts are taught alongside or after *dissimilar* material to avoid confusion. — [Pedagogy](https://mathacademy.com/pedagogy)
- [Doc] XP is "roughly equivalent to 1-minute of focused effort." Full XP goes to a mostly-correct lesson, partial XP for partial correctness, and bonus XP for a perfect score. Negative XP is "rare" and assigned when the system detects rushing or guessing. A struggling lesson can be cut short with no XP. — [How It Works](https://www.mathacademy.com/how-it-works); [Math Academy FAQ](https://www.mathacademy.com/faq)
- [Doc, via Hecker's paraphrase of *The Math Academy Way*] Students "earn little or no XP for nearly passable or poor performance" and "get penalized with negative XP if they are perceived to be blowing off tasks." Students are offered "a choice of unrelated next topics." — [Frank Hecker, part 5 (2025-02-12)](https://frankhecker.com/2025/02/12/math-academy-part-5/)
- [Doc] Recommended pace is 20–40 XP/day, 3–5 days/week. Adults doing ~1 hour/day, 5 days/week, can reach upper-level university courses within a year. AP Calculus BC is ≈6,000 XP. — [FAQ](https://www.mathacademy.com/faq)
- [Founder/Staff] The highest *sustainable* rate is about 50–60 XP/day ("50-60 minutes of serious practice per day"). The all-time monthly record is ~200 XP/day, #10 is ~125/day, and the in-school program averages ~30–35 XP/day. "Consistency is key." (Justin Skycak, 2024-07-26) — [justinmath.com](https://www.justinmath.com/what-is-the-highest-sustainable-daily-xp-on-math-academy/)
- [Doc] A timed quiz becomes available every ~150 XP and covers recent topics, with no access to lessons during it. Missed topics are "scheduled for immediate review," and the quiz can be retaken with different questions after the reviews. Timing can be relaxed in Accommodations. Quiz difficulty is tuned so students average ~80%. — [How It Works](https://www.mathacademy.com/how-it-works); [FAQ](https://www.mathacademy.com/faq); [How Our AI Works](https://mathacademy.com/how-our-ai-works)
- [Doc] Failing a lesson: the lesson halts and the student works on unrelated topics, and the topic returns "within a few days." Prerequisites that may have caused the confusion are prioritized for review. After a *second* halt without progress, the system slows down and assigns remedial reviews, which can reach several steps back in the graph. First-attempt pass rate is 93%, and 98% by the second attempt. — [FAQ](https://www.mathacademy.com/faq); [How Our AI Works](https://mathacademy.com/how-our-ai-works)

**FIRe spaced repetition model (Skycak)**
- [Founder/Staff] Credit from a passed advanced review flows *down* "encompassings" to component skills, recursively and "many layers deep." Each encompassing has a weight (a fraction, which can be zero even for key prerequisites). Credit travels fully along full encompassings and "fades off along partial encompassings." — [Skycak, Individualized SR in Hierarchical Knowledge Structures](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- [Founder/Staff] Failures propagate *up* to the advanced topics that depend on the failed skill ("penalties travel upwards... like growing trees"). — [same](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- [Founder/Staff] "Repetition compression": the selector picks a small set of tasks whose implicit repetitions knock out many due reviews "like dominoes." However, when a repetition is actually due, the system gives an explicit review instead of waiting for an implicit knock-out. — [same](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- [Founder/Staff] Each student-topic pair has a "speed" = student-ability speedup / topic-difficulty slowdown. A pass at 2x speed counts as two repetitions and at 0.5x as half. **When speed < 1, implicit credit is discarded and explicit reviews are forced.** — [same](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- [Founder/Staff] The memory model halves per interval (0.5^(days/interval)). Early reviews get discounted credit, and a decay multiplier grows as a review becomes more overdue (modeling the "summer slide"). Lesson tasks are ~10 questions and review tasks ~3–5 questions. The exact parameters are proprietary. — [same](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/)
- [Founder/Staff] Interleaving: use a *small block* of one problem type at first exposure, then interleaved review. Cited studies: Taylor & Rohrer (2010), where interleaving "doubled test scores," and Rohrer, Dedrick & Stershic (2015), where 7th graders were 25% better at 1 day and 76% better at 1 month. MA uses both micro-interleaving (mixed review and quiz items) and macro-interleaving (breadth-first through small lessons). — [Skycak, Interleaving](https://justinmath.com/cognitive-science-of-learning-interleaving/)
- [Founder/Staff] Unproductive behaviors MA wants to coach against include over-reading instructional material before trying problems, over-relying on reference material instead of retrieval, and solving *alongside* a worked example rather than peeking briefly and finishing unassisted. The planned approach is "just-in-time" behavior detection. (2024-08-27) — [Skycak, Behavior Coaching](https://www.justinmath.com/my-next-big-modeling-project-behavior-coaching/)

**Adult-learner reports: Frank Hecker (retired, multi-year blog series, Jan 2025–Sep 2026)**
- [User] Pedagogy is mostly positive. Lessons are short, review load averaged "under three topics a day" early on and felt "quite reasonable," and quizzes are "useful and reasonable." His routine is to read the first worked example, attempt the second himself, then check. (2025-02-17) — [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/)
- [User] Pain points (2025-02-17):
  - The diagnostic was "a brutal and dispiriting experience" with no obvious exit.
  - Course descriptions lacked prerequisite info.
  - With multiple-choice questions he sometimes used the options to find his mistake ("a bit of a cheat").
  - Quiz time pressure forced him to retake 5 of 15 quizzes.
  - Reviews didn't reinforce *sets of related facts* (e.g., unit-circle values).
  - Leagues encouraged XP for its own sake, so he turned them off.
  - Pace estimates conflicted ("limited trust in the numbers").
  - Finishing a course gave no acknowledgment ("as exciting as watching your car's odometer roll over").
  - He wanted a way to flag correct answers he had guessed.
  - Most of his errors were careless (sign errors, misreading). He thought *not* offering a "silly mistake" retry in lessons was the right call.

  — [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/)
- [User] Final verdict (2025-02-18): worth it for him (>$1,000 total planned spend). Scaffolding often teaches only the simplest case, e.g., synthetic division by a linear factor only. He worries about the emphasis on speed/XP and deliberately slowed to ~50 XP/day "so he won't tire." He proposed a cheaper reviews-only tier for retaining finished courses. — [Hecker part 11](https://frankhecker.com/2025/02/18/math-academy-part-11/)
- [User] Tablet UX: answer boxes are too small, Prev/Next placement is awkward, and there's no tab-equivalent for moving between subfields. He switched back to a laptop. — [Hecker part 9](https://frankhecker.com/2025/02/16/math-academy-part-9/)
- [User] Longitudinal numbers:

  | Course (post date) | XP/day | Days off | Lessons : reviews | Quizzes retaken |
  |---|---|---|---|---|
  | Calc I (2025-11-03) | ~42 | 1 of 28 | n/a | 6 of 7 |
  | Calc II (2026-02-08) | ~35, SD >25 | 18 (+4 days under 10 XP) | 87 : 234 (~2.7:1) | 12 of 22 |
  | Multivariable (2026-07-23) | ~30 | 41 of 166 | 118 : 310 | 17 of 32 |
  | Prob & Stats (2026-09-29) | ~33 | 8 of 67 | 72 : 144 (2:1) | 9 of 14 |

  A one-year retrospective (2026-01-10) reports ~325 hours and ~53 XP/day. — [Hecker update 5](https://frankhecker.com/2026/02/08/math-academy-update-5/); [Hecker update 6](https://frankhecker.com/2026/07/23/math-academy-update-6/); [Hecker RSS feed with updates 4, 7 and the anniversary post](https://frankhecker.com/tags/math-academy/index.xml)
- [User] Others on the MA Discord call the late-course review load "review hell." Hecker himself accepts it because reviews protect knowledge he paid for. He acknowledges the frustration of "review after review and only one new lesson." — [Hecker update 5](https://frankhecker.com/2026/02/08/math-academy-update-5/); [RSS feed](https://frankhecker.com/tags/math-academy/index.xml)
- [User] His side Anki deck for trig/hyperbolic identities, derivatives and integrals "was not as successful as I'd hoped." He couldn't make reviews daily, found the card count "daunting," and said the practice felt "disconnected from my Math Academy activity." It helped for volume/surface-area formulas but not identities. (2025-11 and 2026-02) — [Hecker update 5](https://frankhecker.com/2026/02/08/math-academy-update-5/); [RSS feed](https://frankhecker.com/tags/math-academy/index.xml)

**Other user and critic reports**
- [User] This first-month report (Apr 30–May 31, 2025) is a reader submission published by Jarrett Ye (FSRS author) on his Substack. Praise:
  - adaptive difficulty;
  - "Math should not be painful… Pain is different from difficulty";
  - a sustainable 30–50 XP/day or 350 XP/week;
  - "MA is more fun to do, and I naturally try to avoid boring vocabulary cards" (in Anki).

  Complaints:
  - Choosing too high a course goal led to mismatched content.
  - Correcting placement by deliberately failing was slow and cost XP; lowering the goal and re-running the diagnostic worked better.
  - Never-learned "small links" were labeled "review" and gave no XP.
  - Early timed quizzes were too short at 2–3 minutes/question.
  - Multiple-choice selection on complex formulas was error-prone and couldn't be undone.
  - The leaderboard drove a 4.5-hour session yielding 76 XP.
  - Suggestion: an explicit "I don't know this topic" option (MA declined, fearing misuse).

  — [My First Month with Math Academy (2025-06-01)](https://lmsherlock.substack.com/p/my-first-month-with-math-academy); [LessWrong cross-post](https://www.lesswrong.com/posts/HxtYuHpa3jzrWsrdm/my-first-month-with-math-academy-an-experience-report-from-a)
- [Critic/User] Andy Matuschak (Methods of Proof, Jun–Aug 2024).

  Praise:
  - prerequisite interleaving and hierarchical SRS;
  - diagnostics give "empowering clarity";
  - XP as an effort/pace measure;
  - review tasks don't repeat lesson content verbatim.

  Criticisms:
  - The "algorithmic lesson queue" is a black box that creates "a feeling of passivity."
  - Exposition lacks motivation.
  - Concepts, names and definitions go unreinforced, so he duplicated them into his own SRS.
  - Proofs are fill-in-the-template, so learners never choose a proof strategy, "which is the skill I really need!"
  - Reviews are grouped by topic, so the learner knows the topic in advance, which he predicts will "significantly harm transfer."
  - The hierarchical SRS may be "too conservative" (he forgot earlier material faster than with his own system).
  - He questions whether it is really mastery learning ("can miss several problems and still continue").
  - The UI feels like "living inside a database table."
  - Long worked examples make his eyes "glaze over." He suggests progressive step reveal or having learners fill in trivial steps.
  - Holistic mode's ~80-question diagnostic projected "an extra ~8 months… at 30XP/day."

  — [Matuschak, Math Academy notes](https://notes.andymatuschak.org/Math_Academy)
- [Critic] Michael Pershan (Prob & Stats, ~1 month; post dated 2025-02-06):
  - MA is "unabashedly procedural."
  - Practice problems mirrored worked examples with only numbers changed, so explanations were effectively skippable.
  - "the rapid gains are somewhat illusory." He passed via "accumulated ability to answer multiple-choice questions I didn't understand."
  - "Math Academy never let me forget my shallow learning." He "still [doesn't] know what a geometric distribution is."
  - XP rewards speed over depth.
  - "direct instruction for procedures, discovery learning for concepts."
  - Verdict: "fundamentally broken."
  - He does see value as a supplement for basic university-math practice.

  — [Pershan, Math Academy Wants to Supercharge Your Learning](https://pershmail.substack.com/p/math-academy-wants-to-supercharge?open=false)
- [Founder/Staff] MA curriculum director Alex Smith's reply in the comments: new concepts should start with short motivation and worked examples, not probing questions, and small topics keep cognitive load low. He cites a 93% completion rate for the 4th-grade course and 99% of lessons passed within two attempts. He proposes in-task coaching as a fix. — [same page, comments](https://pershmail.substack.com/p/math-academy-wants-to-supercharge?open=false)
- [User] Hacker News (2025-03-06/07): uniformly positive in this thread. Users credited spaced repetition and interleaving "the way a dedicated tutor would," and one wrote "I really liked the assessment portion which levels you." No negative MA experiences were reported there. — [HN item 43281460](https://news.ycombinator.com/item?id=43281460)
- [User] Homeschool parent log (2024):
  - Actual time was ~2–4 minutes per XP for kids, not 1.
  - Extra problems after mistakes with no XP until lesson completion upset a child ("30 minutes without earning XP").
  - One child "figured out some pattern in the answers" to guess multiple-choice items and couldn't solve them on paper.
  - Changing course settings triggered a long diagnostic that couldn't be undone.
  - Progress sometimes appeared to reset.
  - Another parent's child "loves Mathacademy."

  — [Well-Trained Mind forum](https://forums.welltrainedmind.com/topic/733445-my-ongoing-review-of-mathacademycom-updated-62824)

### Inferences
- **Copy:**
  - Worked-example-first micro-lessons with "2 correct in a row" advancement.
  - Prerequisite-aware remediation, with a halt-and-return-in-a-few-days rule instead of grinding.
  - Immediate review of missed quiz topics.
  - Interleaved mixed quizzes as a separate, higher-stakes retrieval event.
  - XP-like *effort* units for daily goals (they let a "user-chosen question count" convert to expected minutes).
  - Forced explicit review when a skill is weak (MA discards implicit credit when speed < 1). This matters for the planned "partial review credit" feature: partial credit from encompassing problems should be suppressed for skills the user is shaky on.
- **Avoid or fix:**
  - an opaque queue (show *why* each item is in today's queue: due, prerequisite repair, new, quiz);
  - pace/ETA numbers that disagree across screens;
  - no "I don't know this" path during placement;
  - labeling never-learned material as "review";
  - multiple-choice formats that leak answers;
  - no milestone acknowledgment.
- The review:lesson ratio rises late in a course (2–2.7 reviews per lesson in Hecker's data) and users call it "review hell." A single-user app should forecast this, and let the user cap reviews or trade desired retention for new-skill throughput, rather than surprise them.
- Even a heavily optimized commercial system averages ~30–50 XP/day for a committed adult with many zero days. Default workload settings and streak logic should assume irregular days.
- The Pershan/Matuschak critique, that procedural fluency plus SRS can entrench shallow understanding, applies directly to "fresh problems per skill" if the problem generators only vary numbers. Variation in *problem form*, plus some "why" or concept prompts and mixed-topic items where the method must be chosen, is the mitigation.

### Gaps
- Direct Reddit r/MathAcademy and r/learnmath threads couldn't be read (the mirror returned binary data, and the search budget ran out), so community sentiment comes mainly from blogs, HN and one forum.
- MA's exact FIRe parameters, the speed-estimation method and the XP formula are proprietary and undocumented.
- No independent controlled study of MA learning outcomes was found.

---

## 2. ALEKS (Knowledge Space Theory): initial check, "ready to learn," knowledge-check cadence, complaints

### Takeaway
ALEKS pioneered the adaptive "knowledge state" diagnostic and the "ready to learn" frontier. It separates *Learned* (practiced) from *Mastered* (confirmed later in a knowledge check), and periodic Progress Knowledge Checks can push topics back into the path. Students resent those checks as progress-blocking and punitive, especially when one wrong answer removes many related topics. A meta-analysis found ALEKS only as good as traditional instruction.

### Cited Findings
- [Doc] A Knowledge Check uses "approximately 20-30 questions" to find the student's knowledge state, with no right/wrong feedback during the check. Students can choose "I Don't Know," and the check can be resumed after logout. The initial check is taken at first login and can't be bypassed. — [McGraw Hill: What is an ALEKS Knowledge Check?](https://www.mheducation.com/support/aleks-support-center/knowledge/what-is-a-knowledge-check.html)
- [Doc] Progress Knowledge Checks trigger after "20 topics learned w/ min of 5 hours worked," or after 10 hours in learning mode, or after 60 days without one. A topic not retained "is put back in their learning path to re-learn." — [What is a Knowledge Check](https://www.mheducation.com/support/aleks-support-center/knowledge/what-is-a-knowledge-check.html); [ALEKS: Why must I review a topic I have already mastered?](https://www.mheducation.com/prek-12/support/knowledge/aleks-why-must-i-review-a-topic-i-have-already-mastered.html)
- [Doc] *Mastered* means confirmed in a Knowledge Check, and *Learned* means practiced successfully in Learning Mode but not yet confirmed. Choosing "I Don't Know" or missing a related question can move a topic from Mastered/Learned back to Remaining. Review mode is "a safe environment" that does *not* change counts. — [Why must I review…](https://www.mheducation.com/prek-12/support/knowledge/aleks-why-must-i-review-a-topic-i-have-already-mastered.html)
- [Doc] Learning Mode scoring: +1 per correct answer, +2 for two correct in a row *without* opening the Explanation, and −1 per wrong answer (floor 0). A topic is learned at 5 points. Opening the Explanation breaks the streak. Topics are shown in a "Topic Carousel" ordered "from most to least accessible," with locked topics showing prerequisites. Topics lost in a check reappear under "Needs More Practice." The ALEKS pie shows mastered (dark), learned (light) and remaining slices. — [ALEKS K-12 Student Guide (PDF)](https://mheducation.com/unitas/school/explore/sites/aleks/aleks-k-12-student-guide.pdf)
- [Doc] McGraw Hill tells instructors to make sure students take the initial check "without any outside resources," since it "will set the tone for their learning experience." (2026-09-02) — [Ask an ALEKS Implementation Manager](https://www.mheducation.com/highered/blog/2026/08/ask-an-aleks-implementation-manager-jo-ciavarella-on-setting-student-expectations-in-the-first-month)
- [Doc/Institutional] Initial checks are "adaptive, open-response, and no more than 30 questions," and results should guide "support, resources, and differentiation… importantly, not remediation." — [Every Learner Everywhere: Initial Knowledge Checks](https://transformlearning.everylearnereverywhere.org/?p=336)
- [User] College pre-algebra student (Common Sense review, ~2025): "any mistake" on a 25-question check sends you back, and they once had to redo 55 topics. They believe it flags related topics they had no trouble with. Worked examples often don't match the following problem, videos are "rarely helpful," and using an explanation breaks the streak. They prefer DeltaMath. — [Common Sense Education review](https://www.commonsense.org/education/reviews/aleks/teacher-reviews/5118207)
- [User] High-school newspaper (2018-03-12): ALEKS "occasionally bombards the user with 'Knowledge Checks,' blocking all progress," especially bad before a deadline. A 2021 commenter: it "would count x as wrong if it wanted X," and struggling on a topic requires "a whole lot of questions answered correctly in a row." — [Huntley Voice](https://huntleyvoice.com/21455/thevoice/math-program-aleks-is-frustrating-and-stressful/)
- [Research] Meta-analysis of 15 studies / 24 samples (2005–2015): ALEKS was "as good, but not better than, traditional classroom teaching." There was no significant difference between ALEKS as principal and as supplementary instruction. Effects were larger for *shorter* durations of use. — [Fang, Ren, Hu & Graesser (2019), *Educational Psychology* 39(10)](https://digitalcommons.memphis.edu/facpubs/7254)

### Inferences
- **Copy:**
  - The "ready to learn" frontier list ordered by accessibility.
  - An explicit "I don't know" button in placement, so users don't guess and pollute the model.
  - A *Learned vs Mastered* distinction, i.e., provisional status until a later spaced success confirms it. This maps naturally onto FSRS: a skill isn't "mastered" until it survives a review at a meaningful interval.
  - A safe practice mode that doesn't affect scheduling.
- **Avoid:**
  - Blocking checks that halt all progress.
  - A single wrong answer cascading into the loss of many related topics, a visible "progress taken away" event. For partial-credit/penalty propagation in a prerequisite graph, dampen upward penalties and show the user *why* something was demoted.
  - Case/format-strict auto-grading.
  - Breaking a streak for consulting an explanation, which discourages learning from feedback.
- ALEKS's weak meta-analytic result is a reminder that adaptivity alone doesn't guarantee better learning. Content quality and practice design matter at least as much.

### Gaps
- No primary academic study of student *affect* toward progress knowledge checks was retrieved.
- Reddit threads weren't accessible.
- The degreeforum adult-learner thread failed to load.

---

## 3. Khan Academy mastery system and Duolingo practice/streak design

### Takeaway
Khan Academy's mastery levels are driven by quizzes, unit tests and course challenges, and users report that course-level mastery effectively never decays, so it reflects cramming rather than retention. Learners have asked for spaced review for years. Duolingo shows that streaks and XP drive engagement but can displace the learning goal, encourage rushing, and cause quitting after a streak breaks. Its 2022 forced linear "path" (with built-in timed review) traded user agency for simplicity and drew strong backlash.

### Cited Findings
- [Doc] Each Khan skill is worth 100 Mastery Points: Familiar = 50, Proficient = 80, Mastered = 100. Quizzes, unit tests and course challenges move levels up, or down on missed questions. — [Khan Academy Help: Course and Unit Mastery](https://support.khanacademy.org/hc/en-us/articles/115002552631)
- [Doc] September 2018 mechanics change:
  - Practice exercises can demote skills: Mastered falls to Proficient on 70–99%, or to Familiar below 70%.
  - Familiar is no longer a "permanent floor."
  - The Course Challenge no longer counts as 20% of course mastery; 100% is reachable from unit mastery alone.

  — [Khan Academy: Mastery Mechanics Changes Sept 2018](https://support.khanacademy.org/hc/tr/community/posts/360023249611/comments/360004074292)
- [Doc] "Course challenges cover a sampling of skills from the entire course." (blog, 2024-03-12) — [Khan Academy Blog](https://blog.khanacademy.org/?p=16136)
- [User] "Mastery never seems to go down" (undated, no staff reply): the user does well the same day but fails within two days. Course mastery reached 84% and stayed there even after failing the course challenge, so the system "reflects short-term cramming rather than retention." — [Khan Academy community](https://support.khanacademy.org/hc/vi/community/posts/17266266115469/comments/17689505634829)
- [User] Feature request for opt-in site-wide spaced repetition (undated, no staff reply). "when content is completed on Khan Academy, it appears to stay completed indefinitely." Course challenges lower mastery for typos. The user proposes difficulty self-ratings and an "already know" reveal option. — [Khan Academy community](https://support.khanacademy.org/hc/fr/community/posts/39811850715021/comments/39864110417165)
- [User/Teacher] (2023-05-23) Students "approach the app just like their other computer games and try to rush to the end." One student finished a course challenge in 15 minutes at 50% accuracy. Proposed fixes: minimum time per question, a "random guess"/"best guess" checkbox, hints revealed one at a time with ~10 s locks, and per-question time reports. — [Guessing on Khan Academy](https://support.khanacademy.org/hc/es/community/posts/16042819700749-Guessing-on-Khan-Academy-and-improving-the-course-challenges)
- [Research, via secondary source] Silverman et al. (2023, *J. Consumer Research*):
  - Users can come to "view extending their streak as more important than engaging in the underlying activity."
  - Users who break streaks are more likely to quit entirely.
  - Users are less motivated to keep streaks when they know they can repair them.

  Etkin (2016) found tracking can drain enjoyment. The author (566-day streak) admits doing lessons just to extend the streak. (2026-03-02) — [The Decision Lab, Streak Creep](https://thedecisionlab.com/insights/consumer-insights/streak-creep-the-perils-of-too-much-gamification)
- [User] Duolingo XP Boosts must be used immediately. The author admits to "rush through the lesson to score XP and climb the leaderboard rather than taking my time to learn." Another user avoids the app when they don't have a 20-minute block. — [Android Authority opinion](https://androidauthority.com/duolingo-xp-boost-ux-trap-3674572)
- [Doc/Founder] 2022 path redesign: CEO Luis von Ahn said the goals were "decreasing confusion and increasing learning outcomes." The path builds in timed reviews "optimized for memory" that users previously controlled. Internal engagement was "about the same." Users called it the "worst update ever." One user disengaged because he "can no longer pick easier lessons when tired." — [NBC News](https://www.nbcnews.com/tech/tech-news/duolingos-update-redesign-luis-von-ahn-interview-rcna44655)
- [Critic] (2022-11-27) The path is ~200 units for French, the colors "a colourful mess with no meaning," and the big-picture progress view is gone. A single forced linear path limits users who want to revisit or focus on a skill. — [UX Collective, Down the wrong path](https://uxdesign.cc/down-the-wrong-path-the-disaster-of-the-latest-duolingo-ui-update-a4cdd1e6ea1c)

### Inferences
- A skill's displayed "mastery" should be *derived from FSRS retrievability at today's date*, not a sticky high-water mark. That avoids Khan's "never goes down" credibility problem. Pair it with a gentle presentation (e.g., "fading" rather than "lost").
- Streaks: if used at all, make them forgiving and low-salience, e.g., a weekly target or "days practiced this month" rather than a breakable consecutive-day counter. Evidence suggests that broken streaks precede quitting and that streaks displace the real goal. No social/league features are needed for a single user.
- Avoid XP mechanics that reward rushing. Credit should depend on correctness and honest grading, not speed. Optional "I guessed" / "best guess" flags are a cheap anti-gaming tool that also yields better scheduling data.
- Keep user agency: one recommended queue, but let the user pick an easier item set when tired or focus on one course before an exam. Duolingo's path backlash shows the cost of removing choice.

### Gaps
- Khan's "Mastery Challenges" help article failed to load, so their exact spaced-review mechanics are unconfirmed.
- No primary Duolingo data on streak-freeze effects was retrieved, only the secondary summary of Silverman et al.

---

## 4. Anki and FSRS: what works, what users hate, scheduling features, and Anki-for-math/problems

### Takeaway
Anki's strengths are being offline, free, extensible, and having an algorithm users trust. Its weaknesses are a dated, intimidating UI, settings jargon, and review backlogs that trigger a "death spiral." FSRS largely ended "ease hell" through difficulty mean reversion and added desired-retention control, a simulator, a load balancer, easy days, and backlog-friendly sort orders. For math, experienced users find SRS works well for facts, definitions and atomic insights, and poorly for full problem *practice*. That is exactly the gap the planned app targets, and a warning that FSRS's memory model may not transfer cleanly to procedural skills.

### Cited Findings

**Deck options and scheduling features (documented)**
- [Doc] Desired retention defaults to 90%, described as "the most important setting in FSRS"; higher retention means more reviews, and the docs suggest staying below 97%. Optimizing about monthly is enough. "Compute minimum recommended retention" was removed in 25.07. Learning steps of a day or more are discouraged with FSRS. Maximum interval defaults to 100 years. — [Anki Manual: Deck Options](https://docs.ankiweb.net/deck-options.html)
- [Doc] Review sort orders include "Due date, then random," deck, interval, ease, and relative overdueness. With FSRS, the last becomes "Ascending retrievability." Bury toggles exist for new, review and interday-learning siblings. With a review backlog, the docs advise you "stop introducing new cards until you catch up." "New cards ignore review limit" is off by default. — [Deck Options](https://docs.ankiweb.net/deck-options.html)
- [Doc] Easy Days shift due dates away from chosen weekdays and don't retroactively change intervals. — [Deck Options](https://docs.ankiweb.net/deck-options.html)
- [Doc] Anki 24.11 added several scheduling features. The load balancer picks, within the fuzz range, "days that have fewer reviews waiting." It also added:
  - Easy Days;
  - a **descending retrievability** sort, "works well with backlogs";
  - the FSRS simulator;
  - a forgetting curve in card info;
  - True Retention stats;
  - estimated total knowledge and daily load.

  — [Anki 24.11 release notes](https://github.com/ankitects/anki/releases/tag/24.11)
- [Doc] Anki 25.07 brought FSRS-6, an optional "health check" during optimization (replacing Evaluate), better workload estimates with a disclaimer, a "max interval too low" warning, a "grade now" action, and leeches considered in the simulator. Load balancing and easy days now apply when rescheduling. — [Anki 25.07 changelog](https://newreleases.io/project/github/ankitects/anki/release/25.07)
- [User] "The load balancer is great!" Daily Load and True Retention stats are valued for checking whether FSRS behaves sensibly. (2024-12-31) — [Anki forum: 24.11 appreciation](https://forums.ankiweb.net/t/anki-24-11-appreciation/53769)
- [Doc] Leeches: at 8 lapses Anki tags the note and suspends the card, with repeat warnings every 4 lapses after that. The suggested fixes are to restructure the card (it may hold too much or be memorized before being understood), delete it, or suspend interfering siblings and "concentrate on one idea at a time." — [Anki Manual: Leeches](https://docs.ankiweb.net/leeches.html)
- [Doc] Custom Study offers: increase today's new/review limit; review forgotten cards (answered Again within N days); review ahead ("not appropriate for repeated use"); preview new cards; study by state or tag. Filtered decks can reschedule based on answers or run in preview mode. — [Anki Manual: Filtered Decks](https://docs.ankiweb.net/filtered-decks.html)
- [Doc] The FSRS Helper add-on provides:
  - Postpone (lengthen intervals of due cards after a break);
  - Advance (review early, e.g., before a test);
  - Schedule a Break (spread cards due during a planned absence);
  - Flatten (push cards beyond the daily limit to future days);
  - Disperse Siblings;
  - Remedy Hard Misuse (convert past Hard to Again);
  - Steps Stats;
  - True Retention.

  Easy Days and FSRS itself are now native. — [fsrs4anki-helper (GitHub)](https://github.com/open-spaced-repetition/fsrs4anki-helper)

**FSRS vs SM-2 ("ease hell")**
- [Doc, FSRS FAQ quoted on forum] Ease hell under SM-2 "is solved by mean reversion of difficulty… If you press good continuously, the difficulty will converge to D0(3)." (2023-12-11) — [Anki forum: Does FSRS solve ease hell?](https://forums.ankiweb.net/t/does-fsrs-solve-ease-hell/38275/2)
- [User/Community] "7 misconceptions about FSRS" (2024-09-15):
  - Hard counts as a pass; only Again means forgotten.
  - Use separate presets for very different material.
  - Desired retention can range from 70% to 99%.
  - Enabling FSRS creates a backlog only if "Reschedule cards on change" is used.

  — [r/Anki via mirror](https://redlib.belloworld.it/r/Anki/comments/1fhe1nd/7_misconceptions_about_fsrs)
- [User] Some users still experience "ease-hell-like" high difficulty under FSRS (2025-11/12 thread). Replies: difficulty "is just one of the values," and "the proof is in the pudding" if measured retention matches the target. One user cites the FSRS FAQ that FSRS "may even be more accurate if you only use **Again** and **Good**." — [Anki forum: FSRS very uneven difficulty](https://forums.ankiweb.net/t/fsrs-very-uneven-difficulty/67482)
- [User] (2026-06-03) A user hid the interval times above the answer buttons to avoid "fight[ing] the algorithm," and reported "Ease Hell++++" with cards stuck at hours-long intervals after removing relearning steps. — [Anki forum: Struggles adjusting to FSRS](https://forums.ankiweb.net/t/struggles-adjusting-to-fsrs/69849/34)

**Backlog / "avalanche" handling**
- [User/Expert] Expertium cites LMSherlock's simulation (April 2024): with an unlimited review count, order doesn't matter. With a *limited* count, "Difficulty Ascending performed best, with Retrievability Descending second." (thread 2024-09-28) — [Anki forum: Reverse relative overdueness](https://forums.ankiweb.net/t/ordering-request-reverse-relative-overdueness/50051)
- [User] Advice for resuming after a 2-month break (2025-07):
  - Don't shift all due dates ("spreads the backlog problem to every card").
  - Use a catch-up filtered deck with a manageable daily cap and descending-retrievability order.
  - Pause new cards ("If I have a backlog of e.g. 2000 cards it makes no sense… to learn new cards at all").
  - Exhaustion is often the real limit, more than minutes spent.
  - "your workload is not magically going to go away once you're done with the backlog."

  — [Anki forum: Resume learning after two-month break](https://forums.ankiweb.net/t/resume-learning-after-two-month-break-best-practices/64522)
- [User] An opinionated guide (Luise Woehlke, 2025-07-08) recommends a daily review cap of 10–20 with proportionate new cards to prevent "procrastination spirals" and the "Anki death spiral." Too many cards and too-long cards are why "no one ever sticks with Anki." Commenter: "If a card causes you to avoid reviewing, gouge it out and throw it away." Another sustains ~60 reviews/day, down from a peak near 400. — [LessWrong](https://www.lesswrong.com/posts/7Q7DPSk4iGFJd8DRk/an-opinionated-guide-to-using-anki-correctly)

**UI and settings complaints**
- [User] Capterra reviews (2022–2025): the UI "looks a bit old"; Anki "can be very intimidating and not very user friendly"; "The settings are not super easy to understand" (changing one deck's settings affected a whole group); missing a few days builds a large backlog and there's no vacation/pause mode. Praise: works fully offline, the desktop app is more capable than mobile, and the add-on ecosystem is valued. — [Capterra Anki reviews](https://www.capterra.com/p/229584/Anki/reviews/)
- [Staff/User] Users have requested beginner/advanced settings tiers since 2021, and in 2023 someone suggested plain-language questions (e.g., "daily study time") instead of jargon like "leech" and "siblings." The developer (dae, 2024-02-26): "I just don't think a global beginner/advanced switch is the best way to tackle the complexity issue." A community survey on two layouts was split. — [Anki forum: tiered settings](https://forums.ankiweb.net/t/suggestion-tiered-settings-levels-and-actions-based-on-experience/8702)

**Anki for math, proofs and problems**
- [Critic/Practitioner] Michael Nielsen (2019):
  - He makes questions and answers "as atomic as possible."
  - He restates each idea several ways (algebraic, geometric, verbal) and rejects memorizing proofs as "linear lists of statements."
  - Each theorem took a few hours and dozens of cards.
  - The card-writing process drives much of the benefit, and Anki mainly adds retention.
  - Problem solving and creativity are limitations: he notes he "rarely problem-solves these days" and hasn't verified that the method matches obsessive problem-solving.

  — [Nielsen, Using spaced repetition to see through a piece of mathematics](https://cognitivemedium.com/srs-mathematics)
- [User] Ben Pomeranz (2025-07-24): "This is not about using spaced repetition to learn math." He learns from textbooks and paper, then uses cards for definitions, examples/counterexamples, short proof heuristics and nearly trivial quiz items. "I could just memorize the specific answers, and if I notice myself doing this I reassess those cards." He is unsure whether to spaced-repeat full exercises, which are strenuous. — [Anki for Math (Substack)](https://benpomeranz.substack.com/p/anki-for-math)
- [User/Community] Anki forum (2026-09-06) on FSRS for math/logic problem cards. Respondent Danika_Dakika: for *memorization* FSRS is better ("Memory is memory"), but for *practice* neither SM-2 nor FSRS is suited, and there's no evidence spaced-repetition scheduling is what practice needs. Multi-step problems are better practiced with fresh problems, while a card asking for steps is "the most boring, most difficult, and least effective way to study." The thread also advises against hand-tweaking parameters. — [Anki forum: tuning FSRS for math problem cards](https://forums.ankiweb.net/t/questions-about-tuning-fsrs-for-math-logical-reasoning-problem-cards/70949)
- [User] Community randomized-value card templates exist (2026-07-08) so math cards change numbers on reload; no evaluation was reported. LessWrong commenters also suggest randomizing prompt wording/format to prevent cue memorization. — [Anki forum: random values template](https://forums.ankiweb.net/t/an-anki-card-template-for-random-values-inside-cards/70345.md); [LessWrong guide](https://www.lesswrong.com/posts/7Q7DPSk4iGFJd8DRk/an-opinionated-guide-to-using-anki-correctly)
- [Critic] Andy Matuschak: problem solving yields insights that reading-based prompts don't capture ("You really do need to work through the examples and the problems"). How to reinforce that with SRS is an open question. — [Matuschak: How to reinforce insights from problem solving?](https://notes.andymatuschak.org/z4PwWLrxyDFyUgvigpn3nQi)

### Inferences
- **Copy from Anki/FSRS:**
  - desired retention as the main knob, with a workload simulator/forecast next to it;
  - a load balancer and easy days;
  - backlog-safe ordering (descending retrievability or ascending difficulty when capped);
  - "pause new skills when backlogged" as a default rule;
  - Postpone, Advance and Schedule-a-Break actions;
  - leech detection that *prompts a fix* (in this app, route to prerequisite repair or a worked example) rather than silently suspending;
  - sibling dispersal (don't serve two problems from the same skill or template on the same day);
  - Again/Good as the minimal honest grade set.
- **Avoid:**
  - jargon-heavy settings: expose a few plain-language controls (daily question count, target retention, easy days) and hide the rest;
  - a red overdue counter that grows unbounded: show "today's plan" capped to the chosen count and quietly re-plan the backlog;
  - unbounded daily load after missed days;
  - settings changes that silently apply to other courses.
- **FSRS fit caveat:** FSRS is fitted to flashcard recall data. Using it for *skills* with *fresh problem instances* is an extrapolation. Practitioners (Danika_Dakika) explicitly doubt SRS scheduling suits procedural practice, while MA uses a custom model with per-topic speed and implicit credit. Implications:
  - Per-course or per-skill-family presets, since difficulty varies widely.
  - Re-optimizing only after enough data.
  - Tracking *true retention per skill* to validate that the model's predicted recall matches observed success on fresh problems.
- Hecker's failed side-Anki and Pomeranz's experience both show that a *separate* flashcard deck for formulas and identities tends to be abandoned when it feels disconnected. Integrating fact-cards *inside* the same daily queue and linking them to the skills that use them (as the user plans) addresses this directly.

### Gaps
- The FSRS FAQ wiki page didn't render, so official guidance on minimum review counts for optimization and on non-memory use couldn't be quoted directly.
- No 2025–2026 Anki changelog beyond 25.07 was retrieved (25.09 is mentioned only in passing as having a descending-retrievability item).

---

## 5. Other relevant tools: Brilliant, WeBWorK/STACK, coding SRS (LeetCode), SuperMemo, mistake notebooks (错题本)

### Takeaway
Homework systems (WeBWorK, STACK) show the importance of separating input syntax from mathematical correctness, giving partial credit and specific feedback, and limiting attempts to curb guessing. Coding-SRS practitioners converge on the same idea: re-solve, don't recite. Treat the model solution as a living document, judge understanding only at long intervals, and prioritize by importance. Mistake notebooks work only if each error is *analyzed* (cause, fix, similar problem), not just copied.

### Cited Findings
- [Doc] STACK's philosophy:
  - "Separating validity from assessment is a key design feature." Students see how their typed answer was interpreted and can fix syntax before it is marked.
  - Unlimited inputs and potential-response trees allow "follow-through marking" on multi-part questions.
  - Partial credit applies when an expression "only satisfies some of the required properties."
  - With multiple choice it "is impossible to give feedback on student errors outside the given examples."
  - Questions can be randomized.

  — [STACK documentation: Philosophy](https://docs.stack-assessment.org/en/About/The_philosophy_of_STACK/)
- [Research] UBC WeBWorK study (2013):
  - On multi-part true/false items, 47.4% of students with *unlimited* attempts showed guessing (4+ submissions within 30 s) versus 9.7% with a 7-attempt limit, with similar full-mark rates (75.3% vs 79.5%).
  - 19% self-reported guessing often or very often.
  - 66% often reworked problems to correct errors.
  - 29% often used tools like Wolfram Alpha to get answers.
  - 85% of 618 respondents preferred an option including WeBWorK.
  - Answer-format syntax was a frequent frustration.

  — [Lo, Merchant & Piccolo, CWSEI 2013 (PDF)](https://cwsei.ubc.ca/files/outcomes/EOY/Lo-Merchant-Piccolo_WebWork-Math_CWSEI-EOY2013.pdf)
- [Research] WeBWorK in electric circuits (2008): students valued immediate correctness feedback. They were frustrated by the lack of *specific* feedback on wrong answers, overly precise value entry, and errors in problem solutions. Requested fixes were textbook-section references, hints, and intermediate steps. — [Brauer, ASEE PSW 2008 (PDF)](https://peer.asee.org/52258.pdf)
- [User] Brilliant review (2024-11-25, six months daily): some questions have wrong or multiple defensible answers, so you must guess the intended one. The app is "severely limited in educational content," suits refreshing rather than first learning, and streaks are the only motivator. — [Cedar Sanderson, A Review: Brilliant](https://cedarlila.substack.com/p/a-review-brilliant)
- [Reviewer] (updated 2026-09-29) Brilliant "leads with interactive problems" and gives hints rather than answers on mistakes. It resurfaces struggled concepts at spaced intervals, and the Koji AI tutor launched 2026-05-29. The problem-first style frustrates learners who want long explanations, and coding depth is weaker. — [SkillScouter Brilliant review](https://skillscouter.com/brilliant-review-math-science-coding/)
- [User/Practitioner] Red-Green-Code (Duncan Smith), "LeetCode Tip 11" (2023-03-22):
  - The model solution is "a living document" revised each repetition.
  - Use spacing to tune difficulty.
  - If you forget a detail at a long interval, *keep* the interval rather than shortening it, because shortening "promotes a memorization approach." Analyze the detail in a notebook instead.
  - By an interval of a week or two, aim to retain structure, not lines of code.

  — [LeetCode Tip 11](https://www.redgreencode.com/leetcode-tip-11-how-to-use-spaced-repetition-part-1/)
- [User/Practitioner] "LeetCode Tip 12" (2023-03-29):
  - Short intervals mislead, because success may be short-term recall. "once you get to a 15- or 30-day interval, you can be confident that you know how the solution works."
  - If you keep failing to reproduce a solution, "it may be best to leave that problem for later" or switch to a sibling problem.
  - SR strengthens existing understanding; it isn't for learning from scratch.

  — [LeetCode Tip 12](https://www.redgreencode.com/leetcode-tip-12-how-to-use-spaced-repetition-part-2/)
- [Doc] LeetSolv (Go CLI):
  - An SM-2 variant "designed for DSA practice, not flashcard memorization."
  - Inputs are familiarity (5 levels), importance (4) and reasoning (3).
  - Backlog is ranked by a priority score: (1.5×Importance) + (0.5×Overdue Days) + (3.0×Familiarity) − (1.5×Review Count) − (1.0×Ease).
  - FAQ: "Anki is great for memorizing facts, but DSA requires deeper practice." Add only problems you want to revisit, and avoid bulk-adding.

  — [LeetSolv GitHub](https://github.com/eannchen/leetsolv)
- [User] Blind thread (undated): spaced repetition "won't teach you how to solve problems" and can lead you to recall a similar but wrong solution. The consensus favors reviewing *patterns* over specific answers. — [Blind: Does spaced repetition work for LeetCode?](https://www.teamblind.com/post/does-spaced-repetition-work-for-leetcode-1izuzfpe)
- [Founder] The dsaprep.dev Show HN uses fixed ladder intervals (1d→3d→1w→2w→1m) and claims "It's better to master 50 problems through 3-5 reviews each than solve 200 problems once." The thread had no comments. — [Show HN: Spaced Repetition for LeetCode](https://hn.svelte.dev/item/45436942)
- [Research, small] SuperMemo in a special-ed math class (n=10, ~375 items/student): teacher-marked oral retention was 80%, while SuperMemo's self-graded estimate was ~90%. The author attributes the gap to lenient self-grading. — [Mols, SuperMemo as a study aid in mathematics](https://www-v1.supermemo.com/archives1990-2015/articles/school)
- [Commentary] 错题本 practice (NetEase, 2026-08-12):
  - A mistake notebook becomes a "后悔本" ("regret notebook") if errors are copied but never analyzed. "不要只是把错题抄得整整齐齐" (don't just copy mistakes neatly).
  - The recommended loop: 错在哪里，为什么错，怎样改，再做一道相似题，最后留一句提醒 (where it went wrong, why, how to fix it, do a similar problem, write one reminder line).
  - Start with 5 mistakes, not 50.
  - No research evidence is cited.

  — [163.com article](https://www.163.com/dy/article/L45VFT0V0556FBHS.html)
- [Doc] Typical 错题本 apps offer photo capture of wrong problems, tagging by category and knowledge point, guidance on summarizing the error cause, an auto-generated review plan, and charts of review progress. No user reviews were displayed for the sampled app. — [App Store: 错题本 app listing](https://apps.apple.com/us/app/id6448768023)

### Inferences
- **For typed answers:**
  - A STACK-style "interpreted as…" preview before grading eliminates the syntax-error false negatives that plague WeBWorK and ALEKS (x vs X).
  - Use equivalence checking, not string match.
  - For multi-part problems, use follow-through marking so one early slip doesn't zero later parts.
- Limit or slow re-attempts (e.g., a small fixed number, or a forced pause) to curb guessing, and record "solved after k attempts" as a weaker success for scheduling. This combines the WeBWorK evidence with Execute Program's approach in Section 6.
- For coding (C++) problems:
  - Treat the scheduled unit as the *pattern/skill*, not the specific problem.
  - Serve a *different* problem from the pattern when possible.
  - Keep a per-problem "model solution / insight note" the user revises.
  - Don't count very short-interval successes as strong evidence.
- Build a native "mistake review" loop modeled on 错题本: on a miss, ask for a one-tap error category (concept gap / wrong method chosen / algebra-arithmetic slip / misread / ran out of time). Optionally take a one-line "reminder to self," then schedule a *similar* fresh problem soon. Keep it small (a few per day), since copying without analysis is the known failure.

### Gaps
- Mathigon, RemNote, Mochi, Exercism, and Japanese/Korean exam-prep apps could not be researched (search budget exhausted).
- No rigorous study of 错题本 effectiveness was found.

---

## 6. UX for a problem-solving SRS: presentation, grading, hints, solutions, confidence, slips, dashboards, overdue counts

### Takeaway
Evidence and practitioner experience favor:
- paper-and-pencil work with typed or self-checked final answers;
- syntax-safe auto-grading where possible;
- grading that separates "made mistakes but got there" from "gave up/forgot";
- explicit, cheap metacognitive flags (guessed, careless slip, confident);
- immediate access to full worked solutions after an attempt;
- hints that cost something but don't punish learning;
- dashboards that show calibrated retention and a workload forecast rather than an unbounded overdue count.

### Cited Findings
- [Doc] MA encourages working on paper. XP is designed to reward working on paper and checking wrong answers against worked solutions. Every question has an explanation. — [How It Works](https://www.mathacademy.com/how-it-works); [FAQ](https://www.mathacademy.com/faq)
- [Doc] Execute Program (early 2020): wrong attempts no longer count as failure "so long as the student eventually produces a correct answer." The interval grows normally, and only "giving up" (revealing the answer) shrinks the interval, as with forgetting. This avoids false negatives from typos in machine grading. — [Matuschak note on Execute Program](https://notes.andymatuschak.org/zX7RdiHGbHYnkFznUr9VZx7)
- [Critic] Self-graded systems "outperform machine-graded systems in most respects": they're more efficient, avoid false negatives, and allow a wider variety of prompts. Machine grading enables "more advanced knowledge modeling." All commercially successful SRS are machine-graded. — [Matuschak: Self-grading vs machine-grading](https://notes.andymatuschak.org/zScaVuH9r2pwo24iD3f39bU)
- [Critic/Data] Self-grading leniency: in Quantum Country data, "Half of all long-term Quantum Country lapses come from just 12% of its questions." A reported 100% recall at the 75th percentile is doubted, with ~95% more plausible. Secretly inserted never-seen questions were marked forgotten much more often, so the signal survives partial "lying." Leniency may grow over time. — [Matuschak: Do people lie when self-grading?](https://notes.andymatuschak.org/z3W7SG6BkSYyZD4cCqN6znd); also see the SuperMemo 80% vs 90% gap — [Mols](https://www-v1.supermemo.com/archives1990-2015/articles/school)
- [User] Hecker wanted a way to flag correct-but-guessed answers for extra review. He judged that most of his errors were careless slips but agreed with *not* offering a "silly mistake" retry in lessons. — [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/)
- [User/Teacher] Proposed "random guess" / "best guess" checkbox, staged hints locked ~10 s each, and an "I've tried but I still don't get it" option. — [Khan guessing post](https://support.khanacademy.org/hc/es/community/posts/16042819700749-Guessing-on-Khan-Academy-and-improving-the-course-challenges)
- [Research] Hypercorrection effect: errors made with *high confidence* are more likely to be corrected after feedback (gamma .14 between error confidence and later correct retrieval, same-session retest), linked to "metacognitive mismatch" or surprise. — [Metcalfe et al. (2012), J. Cogn. Neurosci.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3970786). A related paper is titled "The hypercorrection effect persists over a week, but high-confidence errors return" (Butler, Fazio & Marsh), cited in the same article. Only the title was seen.
- [Doc] ALEKS breaks the "two in a row" bonus when the Explanation is opened. Students experience this as being punished for seeking help. — [ALEKS Student Guide](https://mheducation.com/unitas/school/explore/sites/aleks/aleks-k-12-student-guide.pdf); [Common Sense review](https://www.commonsense.org/education/reviews/aleks/teacher-reviews/5118207)
- [Critic] Matuschak suggests revealing worked-example steps progressively, or asking the learner to fill in trivial steps, to prevent "glazing over." — [Matuschak MA notes](https://notes.andymatuschak.org/Math_Academy)
- [User] Timed quizzes stress adults. Hecker retook ~half of his quizzes across courses, and the Jarrett-Ye-published reader found early quiz timers too short. MA lets accommodations relax timing. — [Hecker RSS](https://frankhecker.com/tags/math-academy/index.xml); [First Month](https://lmsherlock.substack.com/p/my-first-month-with-math-academy); [How It Works](https://www.mathacademy.com/how-it-works)
- [User] A UI where a misclicked multiple-choice answer can't be undone was called error-prone. — [First Month](https://lmsherlock.substack.com/p/my-first-month-with-math-academy)
- [Doc] Anki surfaces True Retention, daily load, an estimated-knowledge count, a forgetting curve per card, a workload estimate tied to desired retention, and a timebox that periodically reports progress. — [Anki 24.11 notes](https://github.com/ankitects/anki/releases/tag/24.11); [Anki 25.07](https://newreleases.io/project/github/ankitects/anki/release/25.07); [Anki Preferences](https://docs.ankiweb.net/preferences.html)
- [User] Pace/ETA numbers that disagree across screens erode trust ("limited trust in the numbers"). — [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/)
- [User] Anki users cite review pile-ups after missed days and the lack of a vacation mode as major pain points. — [Capterra](https://www.capterra.com/p/229584/Anki/reviews/)

### Inferences (concrete UX recommendations)
- **Presentation:**
  - Show one problem at a time, with an encouraged scratch-paper workflow.
  - Optional per-item timer that records time spent for analytics rather than enforcing a limit, with timed mode reserved for opt-in "quiz" sessions.
  - Final-answer entry with a rendered "interpreted as…" preview, equivalence checking, and undo before submit.
- **Grading model:**
  - Auto-grade the final answer where possible, then map to FSRS ratings.
  - Correct on first attempt, unaided = Good (Easy is optional and rare).
  - Correct after a hint, or after a second attempt = Hard (still a pass).
  - Gave up, viewed the solution, or wrong after the attempt limit = Again.
  - This mirrors Execute Program's "only giving up counts as failure" and keeps grades honest without self-report bias.
- **Self-grade for proofs and open-ended items:** require the user to compare against the full solution and pick Again or Good. Minimize choices (Again/Good) and add an occasional calibration check, e.g., a re-serve of a self-graded item as auto-graded where possible.
- **Metacognitive flags (one tap, optional):**
  - "Guessed" downgrades a correct answer to Hard, or schedules a near-term recheck.
  - "Careless slip" on a wrong answer: log it separately, apply a softer penalty (e.g., Hard instead of Again), and don't propagate the penalty to prerequisites. Cap how often it can be used, or require a corrected re-entry, so it doesn't become an escape hatch. Hecker's preference for *no* slip-retry in lessons argues for keeping it modest.
  - "Confident" (pre-answer): enables hypercorrection-style emphasis. Show the solution prominently when a high-confidence answer is wrong, and schedule a near-term recheck, since high-confidence errors may return.
- **Hints and solutions:** staged hints, each step revealed progressively. Using a hint lowers the grade one step but never blocks progress or "breaks a streak." Always show the full worked solution after any attempt.
- **Multi-part problems:**
  - Grade each part.
  - Credit the skills each part exercises.
  - Use follow-through marking (STACK) so an early slip doesn't fail downstream skills.
  - The skill rating comes from the parts that exercise it.
- **Dashboards that help:**
  - A forecast of the next 7–30 days' load.
  - True retention vs target per course.
  - A skill map colored by *current* retrievability (honest decay, unlike Khan).
  - A "ready to learn" frontier (ALEKS).
  - Weak-skill and leech lists with suggested prerequisite repair.
  - A single consistent ETA computed in one place.
- **Avoid demotivating counts:**
  - Never show a raw overdue number.
  - Show "Today: N questions" (the user's chosen count).
  - Silently spread the excess using descending-retrievability/difficulty ordering and a load balancer.
  - Offer Postpone and Schedule-a-Break actions.
  - Suspend new skills automatically while a backlog exists, and tell the user.

### Gaps
- No controlled evidence was found on the effect of an "I made a careless slip" button on learning or scheduling accuracy.
- No evidence was found comparing typed versus self-checked paper answers for math SRS specifically.

---

## 7. Onboarding: placement/diagnostics so advanced users don't redo basics; joining mid-course

### Takeaway
Adaptive diagnostics (ALEKS, MA) save advanced users time but are long and draining, and they are hard to correct when wrong. Users most want: a clear "I don't know" option; the ability to skip, exit or redo placement; prerequisite info up front; and a cheap way to say "I've covered units 1–4 of my class." Lazy, frontier-based gap repair beats front-loading every foundation.

### Cited Findings
- [Doc] The MA diagnostic is ~30–45 min, splittable, places at the knowledge frontier, and also tests lower-grade foundations. — [How It Works](https://www.mathacademy.com/how-it-works); [How Our AI Works](https://mathacademy.com/how-our-ai-works)
- [Doc] After the diagnostic, MA students can switch courses per the report's recommendation, or stay and have prerequisite gaps reviewed as they go. — [FAQ](https://www.mathacademy.com/faq)
- [User] The diagnostic was "a brutal and dispiriting experience" with no obvious exit. Course pages lacked the prerequisite info needed for "an initial assessment of course appropriateness." (2025-02-17) — [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/)
- [User] Holistic Mode: an 80-question diagnostic added an estimated ~8 months at 30 XP/day (Matuschak, 2024-07-24). Another user saw a goal date move from July to October. — [Matuschak](https://notes.andymatuschak.org/Math_Academy); [First Month](https://lmsherlock.substack.com/p/my-first-month-with-math-academy)
- [User] Placement correction: deliberately failing questions to lower the placement was slow and cost XP, because the system "responds slowly to deliberate errors to prevent cheating." Lowering the goal and re-taking the diagnostic worked best. Request: let users mark known-unknown topics. — [First Month](https://lmsherlock.substack.com/p/my-first-month-with-math-academy)
- [User] Changing course settings triggered a long diagnostic that couldn't be undone. — [Well-Trained Mind](https://forums.welltrainedmind.com/topic/733445-my-ongoing-review-of-mathacademycom-updated-62824)
- [Doc] The ALEKS initial check is ≤30 adaptive open-response questions with an "I Don't Know" button. It can't be skipped except for carry-over students, and must be taken without outside resources. — [What is a Knowledge Check](https://www.mheducation.com/support/aleks-support-center/knowledge/what-is-a-knowledge-check.html); [ALEKS blog 2026](https://www.mheducation.com/highered/blog/2026/08/ask-an-aleks-implementation-manager-jo-ciavarella-on-setting-student-expectations-in-the-first-month)
- [User] HN commenter (2025-03): "I really liked the assessment portion which levels you," and it showed gaps in an engineering graduate's knowledge. — [HN](https://news.ycombinator.com/item?id=43281460)
- [Doc] The Khan course challenge samples skills from the whole course and can level many skills at once. It is optional, and since 2018 no longer required for 100% mastery. — [Khan blog](https://blog.khanacademy.org/?p=16136); [Khan 2018 changes](https://support.khanacademy.org/hc/tr/community/posts/360023249611/comments/360004074292)
- [User] A Khan course-challenge typo lowered mastery, and retaking was tedious. — [Khan SRS request](https://support.khanacademy.org/hc/fr/community/posts/39811850715021/comments/39864110417165)

### Inferences
- A **layered onboarding** suits a single user who already knows the syllabus:
  1. Toggle courses, units and sections to match the class (the user's plan).
  2. For each enabled section, choose "haven't covered / covered in class / solid."
  3. An *optional*, short, skippable, resumable placement check for "covered/solid" sections, using graph inference (MA/ALEKS style: a correct answer on an advanced skill implies its prerequisites) and an "I don't know" button.
- Seed FSRS state from placement results as *provisional*. ALEKS's "Learned vs Mastered" maps well here: placement-passed skills get a moderate initial stability, are tagged unconfirmed, and are confirmed or demoted by their first scheduled review on a fresh problem. Don't ask the user to grind basics.
- Make placement *reversible*: a per-section "reset/re-place" action and a per-skill "I actually don't know this" override. MA declined this out of anti-cheating concern, which is irrelevant for a single-user tool.
- Repair gaps lazily, MA style: only route back to foundations when an error pattern implicates them, rather than front-loading a long holistic diagnostic.
- Show prerequisite chains and estimated hours before enabling a course, so the user can judge fit, which Hecker asked for.

### Gaps
- No data was found on how much time diagnostics actually save versus starting at the beginning.
- No sources were found on onboarding for users who are partway through a *specific external class syllabus*, beyond MA/ALEKS course-switch guidance.

---

## 8. Common failure modes of adaptive learning products and mitigations

### Takeaway
The recurring failure modes are:
- black-box sequencing that makes learners passive;
- procedural or shallow learning, where SRS preserves a shallow understanding;
- guessing and gaming of reward systems;
- over-review late in a course ("review hell") or under-challenge;
- punitive checks that remove progress;
- strict auto-graders that create false negatives;
- content errors that destroy trust.

Most have known mitigations: transparency, form-varied problems and concept prompts, honest effort-based rewards, forgiving grading, capped workloads, and rigorous content verification.

### Cited Findings
- [Critic] Black box: MA's "algorithmic lesson queue" creates "a feeling of passivity," and the same problem appears in Khan's mastery system. — [Matuschak](https://notes.andymatuschak.org/Math_Academy)
- [Critic] Shallow understanding: "Math Academy never let me forget my shallow learning." Practice problems differ from worked examples only in numbers. — [Pershan](https://pershmail.substack.com/p/math-academy-wants-to-supercharge?open=false). Matuschak's summary of Pershan: "It reinforces his memory of a shallow understanding." Topic-grouped reviews "significantly harm transfer." — [Matuschak](https://notes.andymatuschak.org/Math_Academy)
- [Founder/Staff] The rebuttal: worked examples plus small steps minimize cognitive load, and interleaved quizzes and layering build transfer. Behavior coaching is planned for unproductive habits. — [Pershan comments (Alex Smith)](https://pershmail.substack.com/p/math-academy-wants-to-supercharge?open=false); [Skycak interleaving](https://justinmath.com/cognitive-science-of-learning-interleaving/); [Skycak behavior coaching](https://www.justinmath.com/my-next-big-modeling-project-behavior-coaching/)
- [User] Gaming and guessing: a child pattern-guessed MA multiple choice; a Khan student did a course challenge in 15 min at 50%; WeBWorK guessing was 47% with unlimited attempts; the Duolingo XP boost led to rushing. — [WTM](https://forums.welltrainedmind.com/topic/733445-my-ongoing-review-of-mathacademycom-updated-62824); [Khan guessing](https://support.khanacademy.org/hc/es/community/posts/16042819700749-Guessing-on-Khan-Academy-and-improving-the-course-challenges); [UBC CWSEI](https://cwsei.ubc.ca/files/outcomes/EOY/Lo-Merchant-Piccolo_WebWork-Math_CWSEI-EOY2013.pdf); [Android Authority](https://androidauthority.com/duolingo-xp-boost-ux-trap-3674572)
- [User] Over-review: "review hell" late in MA courses, with 2–2.7 reviews per lesson. — [Hecker update 5](https://frankhecker.com/2026/02/08/math-academy-update-5/). Anki "death spiral" or backlog. — [LessWrong](https://www.lesswrong.com/posts/7Q7DPSk4iGFJd8DRk/an-opinionated-guide-to-using-anki-correctly)
- [Critic] Possible *under*-review: MA's hierarchical SRS may be "too conservative," i.e., it lets earlier material be forgotten. — [Matuschak](https://notes.andymatuschak.org/Math_Academy)
- [User] Under-challenge or narrow scaffolding: Hecker often learns "only the simplest case." Templated proofs never require choosing a strategy. — [Hecker part 11](https://frankhecker.com/2025/02/18/math-academy-part-11/); [Matuschak](https://notes.andymatuschak.org/Math_Academy)
- [User] Punitive checks: ALEKS knowledge checks block progress and can send a student back 55 topics. — [Huntley Voice](https://huntleyvoice.com/21455/thevoice/math-program-aleks-is-frustrating-and-stressful/); [Common Sense](https://www.commonsense.org/education/reviews/aleks/teacher-reviews/5118207)
- [User] Strict grading false negatives: ALEKS case sensitivity; Khan typos lowering mastery; WeBWorK syntax frustration; Execute Program's typo problem, solved by not penalizing until "give up." — [Huntley Voice](https://huntleyvoice.com/21455/thevoice/math-program-aleks-is-frustrating-and-stressful/); [Khan SRS request](https://support.khanacademy.org/hc/fr/community/posts/39811850715021/comments/39864110417165); [UBC CWSEI](https://cwsei.ubc.ca/files/outcomes/EOY/Lo-Merchant-Piccolo_WebWork-Math_CWSEI-EOY2013.pdf); [Matuschak/Execute Program](https://notes.andymatuschak.org/zX7RdiHGbHYnkFznUr9VZx7)
- [User] Content errors and trust: Brilliant answers that are wrong or ambiguous; WeBWorK "errors in problem solutions"; MA progress resets and missing topics; a typo in MA's course overview. Separately, an HN commenter on an e-learning platform said "It's a frustrating feeling when you can't really trust what you're studying is factually correct." — [Cedar Sanderson](https://cedarlila.substack.com/p/a-review-brilliant); [ASEE 2008](https://peer.asee.org/52258.pdf); [WTM](https://forums.welltrainedmind.com/topic/733445-my-ongoing-review-of-mathacademycom-updated-62824); [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/); [HN](https://news.ycombinator.com/item?id=43281460)
- [User] Motivational design that backfires: broken streaks precede quitting; leagues encourage XP for its own sake; a 4.5-hour leaderboard binge yielded little; no milestone celebration. — [Decision Lab](https://thedecisionlab.com/insights/consumer-insights/streak-creep-the-perils-of-too-much-gamification); [Hecker part 10](https://frankhecker.com/2025/02/17/math-academy-part-10/); [First Month](https://lmsherlock.substack.com/p/my-first-month-with-math-academy)
- [Research] Adaptive systems are not automatically better: ALEKS matched but didn't beat traditional teaching. — [Fang et al. 2019](https://digitalcommons.memphis.edu/facpubs/7254)

### Inferences

#### Mitigations mapped to the planned app
- **Transparency:** every queue item shows a reason tag (Due review · Prerequisite repair for X · New skill · Mixed quiz · Leech fix). A per-skill page shows FSRS state (stability, retrievability, next due), recent attempts, and which problems credited it, including partial credit from encompassing skills. The user can override: "do this course only today," "easier set," "skip this item."
- **Depth versus shallowness:**
  - Problem generators should vary *form* (representation, wording, which quantity is unknown, embedded contexts), not just numbers.
  - Include "which method applies?" mixed items and short concept/why prompts (fact or concept cards in the same queue).
  - Reserve some slots for multi-skill synthesis problems and the "ultra-hard" ladder.
  - Avoid topic-labeled reviews: don't show the skill name before the attempt, only after.
- **Partial credit and penalty propagation:**
  - Follow MA's safeguards: discount partial credit by edge weight and suppress it for skills currently weak (MA forces explicit reviews when speed < 1).
  - Never let implicit credit indefinitely postpone an explicit review of a due skill.
  - Dampen upward penalties and explain them, so the app avoids ALEKS-style "lost 55 topics."
- **Anti-gaming without punishment:** attempt limits or brief pauses between retries; "guessed" flag; no speed-based rewards. A single-user tool needs no negative XP, because the main "adversary" is self-deception, so prefer honest-grading defaults over penalties.
- **Workload:**
  - The user-chosen daily question count is a hard cap.
  - Show a forecast and a desired-retention ↔ workload simulator.
  - Auto-pause new skills under backlog.
  - Load balancer, easy days, break scheduling.
  - Optionally let reviews of retired courses run at lower desired retention, since Hecker wanted reviews-only maintenance of finished courses.
- **Content trust:**
  - Every problem needs a verified answer key: ideally CAS- or test-checked for generated problems, and compiled and test-cased for C++.
  - Add a one-click "report/flag problem" that suspends the item, routes it to a fix list, and doesn't count the attempt.
  - Use STACK-style input validation.
- **Motivation:**
  - Milestones on section and course completion (Hecker's "odometer" complaint).
  - Forgiving weekly targets instead of fragile streaks.
  - No leaderboards.
  - Effort units (questions or minutes) as the daily goal, matching the user's chosen question count.

#### Validation the app itself should do
- Because FSRS was built for declarative memory, log predicted retrievability versus actual success on *fresh* problems per skill, and surface the calibration. If skills behave differently from flashcards (e.g., procedural skills decay more slowly), per-preset optimization will capture it only if the logs are clean. That depends on honest grading and on separating hint-assisted, slip and guess outcomes in the review log.

### Gaps
- No quantitative evidence was found on how often content errors cause users to abandon adaptive math products.
- No head-to-head study was found of implicit-credit (FIRe-style) versus independent per-skill FSRS scheduling.
