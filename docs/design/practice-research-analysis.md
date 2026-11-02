# Practice design research: the coordinator's analysis (2026-11-02)

The owner's learning design (backlog, "Learning design", 16:01–16:12) raised questions the earlier research did not settle. Researchers gathered the evidence into `docs/research/notes/Practice design questions/`, one note per question; the notes give facts and evidence strength only. This document is the coordinator's reading of them: what each note changes in the design, and what goes to the owner.

Grades as in `student-model.md`: **A** direct evidence in a similar setting, **B** indirect or analogous, **C** a design assumption with the check that tests it.

## 1. Feedback after a wrong answer (`feedback_after_errors.md`)

**What the evidence says:**
- **Correctness alone teaches little.** Knowledge of results (right/wrong only) averaged d = 0.05 in computer-based learning, against 0.32 for the correct answer and 0.49 for an explanation (van der Kleij et al. 2015, 40 studies). Errors later corrected: none .08, right/wrong .28, the answer .53 (Marsh et al. 2012, undergraduates, general knowledge).
- **Full information after a failure teaches most.** High-information feedback d = 0.99 against corrective 0.46 (Wisniewski et al. 2020, 435 studies). An explanation beat the bare answer only after an incorrect first response (Attali & van der Kleij 2017, N = 2,445, math practice items).
- **Order matters.** Answers available before the student's own attempt lower the gains (Shute 2008, citing Bangert-Drowns et al. 1991). Unrestricted AI help raised practice scores 48% and lowered the later exam 17%; a guardrailed tutor left the exam unchanged (Bastani et al. 2025, about 1,000 high-school students). Help after an attempt was neutral to modestly positive in the follow-ups.
- **Retries are thin evidence.**
  - Multiple tries were slightly better for higher-order outcomes (Clariana & Koul 2005, review).
  - Three tries without the answer beat one try plus the answer (Cubillos et al. 2023, grades 3–4, N = 73).
  - A hint after the first wrong answer helped a one-week test but not the exam (Schwerter et al. 2022, college statistics, N = 87).
  - The only look at very many tries is observational and confounded: give-ups rose from 1.6% at 10 allowed tries to 8.2% at 99 (physics homework).
  - No study tests unlimited retries with no hints and a solution only on give-up.
- **Prior knowledge can flip simple feedback.** Right/wrong feedback helped children with no strategy and hurt children taught one (Fyfe & Rittle-Johnson, grades 2–3).
- **A delayed review after an error** is what made immediate feedback pay (Attali & van der Kleij 2017). Feedback delayed a week helped transfer in an engineering course (Mullet et al. 2014).
- **Self-explanation** averaged g = .44 in math (Bisra et al. 2018, 16 studies), mostly on immediate tests. Comparing one's own flawed model with an expert's beat explaining the expert's alone (Gadgil et al. 2012, science, abstract only). A secondhand report of Barbieri et al. 2023 says self-explanation prompts added to worked examples did not help.
- **Setting a problem aside** helps a little on lab insight problems (d = 0.29; Sio & Ormerod 2009), more after longer work before the break. Sleep results are mixed, and nothing tests math.

**What this means for Toishi:**
1. **The design holds.** It is attempt first, then retry, the worked solution on give-up, and a later review. That matches the three best-supported rules: feedback after the student's own attempt; full information after a failure; a delayed review after an error. **B**.
2. **Unlimited retries stay** (owner: long struggle is fine). The physics data is about guessing for points. Here only the first try counts, so guessing gains nothing. **C**: log retries per item and give-ups, and look at the distribution after real use.
3. **Matched wrong-answer feedback only with the solution** (done in v1.3, `student-model.md` 4.6). Shown during retries, it would be a hint.
4. **Set aside until tomorrow** (ladder rung 3) stays. It is supported as a stop for wheel-spinning (Beck & Gong 2013), and only weakly by incubation. **C**.
5. **Proposal for the owner: a comparison line under the solution.**
   - After a give-up, show the student's last answer beside the solution, with one line: "Find the first line where your work and this solution part ways."
   - It adds no information and records nothing, so it keeps to "no help".
   - Basis: self-explanation (**B**, immediate tests) and own-versus-expert comparison (**C**).

## 2. Keeping students practicing (`adherence.md`)

**What the evidence says:**
- **Most users fall short of intended use.** About 9% of Khan Academy users reach the recommended 30+ minutes a week, and stated reasons for stopping are time and workload. No dropout analysis of Anki users exists.
- **Engagement features raise engagement more than learning.**
  - Gamification: g = .25–.49, and only the cognitive effect survives in rigorous studies (Sailer & Homner 2020).
  - Badges plus a leaderboard lowered intrinsic motivation and exam scores in one college course (Hanus & Fox, N = 80).
  - Streak evidence is company A/B tests on retention, with no learning outcome.
- **Nudges shrink at scale.** Planning prompts had no completion effect over about 250,000 students (Kizilcec et al. 2020) and no academic effect over about 25,000 college students (Oreopoulos & Petronijevic).
- **Plans and progress tracking work for goals in general.** Implementation intentions d = .65 (94 tests, adult goals). Monitoring progress d = .40 (138 studies). Neither is tested inside a self-directed practice app.
- **Backlogs.** No controlled study links backlog size to quitting. 82.1% of surveyed medical students found Anki overwhelming, and 75% never or rarely kept up with older reviews (cross-sectional). In habit research, one missed day did little and accumulated misses mattered.
- **Difficulty and persistence.** No study tests hard unassisted practice against easier practice on persistence. In one adaptive app, students rated difficulty "appropriate" near 65% success, and answer volume did not change with the target.
- **Performance predicts later self-efficacy** more than the reverse (β = 0.205 vs 0.071).

**What this means for Toishi:**
1. **No streaks, badges, points or leaderboards.** They have no learning evidence, and one college study found harm. This matches the spec's avoid list. **B**.
2. **The biggest adherence risk is our own planner.**
   - It reports the full load and never caps it (owner decision).
   - In the simulator's stand-in run, a typical student was planned 449 minutes a day against 60 served, and certified nothing by the deadlines (`sim2-report.md`). That run used the stand-in planner, so the real numbers are needed first.
   - An impossible daily list is the backlog problem the Anki surveys describe. **Owner decision** (section 8).
3. **Build the study plan the spec already has (LIB-12, not built yet).** One screen asks when and where the daily set happens, the likely obstacle, and an if-then plan. Basis: implementation intentions (**B** in general, **C** here). It is not a reminder or a nudge.
4. **Progress monitoring is built in**: the Skills page with milestones and deadlines. Keep it factual (**B**).
5. **A missed day costs little.** The return-from-break plan keeps new material first and caps catch-up at 40%, which fits the habit evidence. **B**.

## 3. Practicing above exam difficulty (`above_exam_difficulty.md`)

**What the evidence says:**
- **No direct comparison exists.** No study holds practice time constant and compares above-exam with at-exam practice on a delayed exam-level test, in math or any STEM field. The two math studies are olympiad training: self-selected students, or a test aligned with the training.
- **Extra practice at the same difficulty buys little later.**
  - 3 vs 9 problems made no difference at 1 and 4 weeks (Rohrer & Taylor 2006, 216 students).
  - A mastery threshold of 5 vs 3 correct changed retention by about 0.02 (ALEKS, 806,279 students).
- **What works is tested at practice difficulty.** Interleaving (classroom RCT d = 0.83), spacing and retrieval are all tested with the test at the practice's own difficulty. Difficulty ramps help when they adapt to the learner, and they ramp up to the test's difficulty (Wickens et al., 37 transfer studies).
- **Too much difficulty fails.** Unassisted discovery d = −0.38 against guided discovery 0.30 (Alfieri et al. 2011). The expertise-reversal effect also applies. Under extreme load, reducing the load helps.
- **Elite courses don't settle it.** Cambridge marks some example-sheet questions as extras for strong students, with no comparison to the Tripos. Landau's exam was hard, with about an hour per problem, but there is no record of practice above its level.

**What this means for Toishi:**
1. **Tier 4 as the target is the owner's choice, grade C.**
   - Its defensible part is what tier 4 means: varied surface form, no hint of the method, and components combined across sections. That overlaps with interleaving and transfer, which have support.
   - Its cost is real: at 0.90, a 5-component problem needs about 0.985 per component (`student-model.md` risk 4).
2. **The milestone ladder is the supported part.** Tier 2 by M1, tier 3 by M2 and the target by M3 is an adaptive ramp up to and past exam level. The growth band picks problems by predicted success, which is the adaptive part.
3. **Keep tier 3 selectable** on the course page, which already allows 3–5. Show the hours to keep pace at each tier, so the cost of tier 4 is visible.

## 4. The practice success rate (`success_rate_and_struggle.md`)

**What the evidence says:**
- **The "85% rule" is theory.** It comes from binary classification with gradient-descent learners and Gaussian noise (Wilson et al. 2019), and its optimum moves with the noise: about 82% under Laplace noise, 75% under Cauchy. The only human test is a motor-task preprint. There, about 70% success beat 85% (d = 0.65) and did not differ from 50%.
- **Studies that set the success rate disagree, and none uses multi-step math:**
  - **Paired associates:** recall was best when items were scheduled at 86–94% predicted recall (Eglington & Pavlik 2020, adults, 3-day test), because failures cost more time.
  - **Arithmetic:** in Math Garden, the highest preset success rate gave the most problems attempted and the largest improvement (children, 6 weeks; condition values secondhand).
  - **A number-line game** (tens of thousands of players): easier versions were more engaging, and the most engaging versions taught slowest.
  - **Geography:** students voted difficulty "appropriate" at about 65% success, and in school at about 75%.
  - **A vendor's design target:** 80–85% on quizzes, with no experiment.
- **Struggle pays only with instruction after it.**
  - Productive failure: g = 0.36 when explicit instruction follows (Sinha & Kapur 2021, 53 studies). It reverses for young children.
  - Unassisted discovery: d = −0.38; guided discovery: 0.50 (Alfieri et al. 2011).
- **Wheel-spinning is common, but its measured rate depends on the definition:** from 0.6% to 47% of student-skill pairs in tutoring logs. No randomized intervention exists, and no study varies how long students struggle before help.

**What this means for Toishi:**
1. **The standard band [0.70, 0.90] stays, grade C.** It sits inside the range the evidence points to (65–94%), centred on 0.80. Its best support is the time-cost argument: in a fixed time, failures cost more, which matches our measured minutes per certification.
2. **The hard band [0.50, 0.75] stays an owner option, not the default.**
   - Nothing tests repeated practice at 50–75% first-try success on multi-step problems. The productive-failure result is about trying a problem before being taught, which our students already have been.
   - Its cost is visible: hours to keep pace come from the student's own minutes, so a harder band shows its price.
   - Log outcomes by band, grade C.
3. **The ladder is our answer to wheel-spinning.** No study tests a stopping rule, so its rung points (1, 2 and 3 misses in a row) stay grade C, and they are logged.

## 5. Worked example or problem first, and open-book practice (`examples_and_open_book.md`)

**What the evidence says:**
- **Example first usually wins, but for novices.** Example-then-problem beat problem-then-example in 8 of 10 comparisons pooled by van Harsel et al. 2019 (d = 0.35). Almost every one used learners with no prior instruction and an immediate test.
- **The closest sample to ours shows no difference.** In van Harsel et al. 2019 Exp. 1, 124 first-year engineering students learning the trapezoidal rule did no better with example-first than with problem-first. Examples only did best.
- **Example advantages fade at a delay.** At a one-week test they often vanish (Yeo & Fazio 2019; four experiments in van Gog et al. 2015, about 430 learners). Learners who know more do better with problem solving at a delay (Chen et al. 2016).
- **Expertise reversal.** High support helps low prior knowledge (d = 0.51) and hurts high prior knowledge (d = −0.43), most strongly in higher education (Tetzlaff et al. 2025, 60 studies; secondhand).
- **Our situation is the comparison arm of productive failure.** Practice after a lecture is the "instruction first" condition in those studies. No study gives productive-failure problems after the lecture.
- **Examples on demand get copied.** Poor solvers looked back 6.6 times per problem against 2.7 and copied more (Chi et al. 1989, N = 8). A worked solution at hand helped on near-identical problems, not on ones that needed changing (Reed et al. 1985). Clicking hints through to the answer went with worse learning at every skill level (Roll et al., 38 students).
- **Open book.**
  - Open-book practice tests matched closed-book ones on delayed retention in the lab (Agarwal et al. 2008).
  - Reviews and classroom studies lean closed-book (Durning et al. 2016; Permzadian & Cho 2025).
  - Math evidence is thin.
- **Expectations shape study.** Expecting an open-book test cut study time and lowered delayed closed-book scores by about 10% (Agarwal & Roediger 2011). Learners adapt to the format they expect (Finley & Benjamin 2012).

**What this means for Toishi:**
1. **A new skill opens with a problem (decision, design v1.3).** Our students have read the section, with its examples, before the skill is introduced. For them, the closest evidence shows no gain from example-first, the advantage fades by a week, and support turns harmful as prior knowledge grows. This matches the owner's design: the textbook teaches and the app tests. **B**.
2. **The worked example stays as reference, during the new-skill block only.**
   - A "Worked example" button opens it.
   - Opening it before the first answer makes that try aided, a failure for the model (as a hint was), so the evidence stays honest.
   - Later problems show only the textbook pointer, and sittings show nothing.
   - The ladder catches a student who didn't read the section: a smaller problem, then a prerequisite, then the textbook pointer and a day off.
3. **Say up front that certification is closed book.** The course page and the first sitting state that M2 and M3 are certified in closed-book timed sittings. The expectancy evidence says students study more for a closed-book test. **B**.
4. **This changes the planner and the session (wave 2 follow-up).**
   - The New role serves a tier-1 problem first, and its WorkItem carries the example card as reference.
   - The session records an example opened before the first answer as aided.
   - The page shows the button.
   - It is built after the three wave 2 branches merge, by one builder, so it lands consistently.

## 6. Definitions, formulas and transfer (`definitions_and_transfer.md`)

**What the evidence says:**
- **Recalling facts does not by itself help application.**
  - Fact quizzes lifted a fact test from .54 to .78 (d = 1.23) but not higher-order questions: .46 against .44 for studying once (Agarwal 2019, college, full text).
  - Higher-order quizzes scored .85 on higher-order questions.
  - Transfer of testing averages d = 0.40 over 192 effects. It is weakest for worked-example problems, and it shrinks after a publication-bias correction (Pan & Rickard 2018).
  - Practicing term-to-definition did not transfer to the reverse question (Pan & Rickard 2017).
- **Successive relearning:** 3 correct recalls at first, then 1 per session over at least 3 spaced sessions. More relearning sessions wash out most of the gain from a higher first criterion.
- **Stopping after one correct recall is costly.** Students dropped 68% of flashcards after one correct recall. Those items were recalled at .62 later, against .88 after two (Kornell & Bjork 2008).
- **Self-scoring.** Students over-credit their own recall, low performers most. Checking against idea units cut overconfidence from 0.14 to 0.06 (Nederhand et al. 2018, N = 127).
- **Recall vs multiple choice.** With feedback the two formats perform about the same (Smith & Karpicke 2014). Short answer beat multiple choice only with feedback (Kang et al. 2007).
- **Prerequisites and calculus.**
  - Readiness tests predict calculus grades (r = .28–.51).
  - Spaced precalculus quiz problems raised a readiness test a month after the course (.54 to .59, N = 51).
  - In related rates, the weakest step is turning the words into a diagram and equations (Martin 2000).
- **Mixing facts with problems** gave the best overall average, while each pure quiz type won on its own test (Agarwal 2019).

**What this means for Toishi:**
1. **The geometry deck pairs every fact with problems that use it** (owner design, now supported). The flashcards keep formulas retrievable, and the problems are what carry over to calculus. **B**.
2. **Formula cards get typed answers that the app grades.** Definition cards that must be self-graded list their idea units, one per line, so each part is checked. Cards ask in the direction the problems use: the situation on the front, the formula on the back. **B**. (Sent to the geometry writer, and added to the content brief.)
3. **New flashcards need two correct recalls on their first day (wave 2 follow-up).**
   - Today a new card that is answered Good once graduates. Only a missed card comes back in the session.
   - Anki's default learning steps (1 and 10 minutes) also give two recalls on day one, so this is Anki parity too.
   - The second recall is a same-day FSRS event (the short-term formula). **B** (Kornell & Bjork 2008; the successive-relearning criterion).
4. **Related rates needs its setup step tagged as its own component** (the translation into a diagram and equations), which the 4.1 map already has. Its problems are checked for it in review.

## 7. Timed practice and exam pace (`timed_practice.md`)

**What the evidence says:**
- **No study tests what we need.** None randomizes timed against untimed practice and then measures a later timed exam, in high-school or college math, physics or engineering, or on the SAT, ACT, GRE or AP. Everything is indirect.
- **Speed drills help fact fluency in young children.**
  - Speeded against non-speeded practice: ES .51 in at-risk first graders (Fuchs et al. 2013, confounded).
  - Timed against identical untimed practice: g = 0.09–0.42 in the three clean K–6 contrasts (WWC 2021).
  - The gain transfers to procedural computation, not to algebra or word problems (Fuchs et al. 2009). It transfers only when strategy instruction comes with it (Woodward 2006; Tournaki 2003).
  - Automaticity came only after declarative training (Hasselbring et al. 1988).
- **In adults, timing did not raise accuracy** (Jazbutis 2023, n = 211, an artificial times table). It lowered immediate accuracy, raised transfer accuracy (.87 vs .80), and raised stress.
- **One small engineering pilot** (Miller 2011, n = 19, historical control): timed homework went with better midterms and the same final.
- **When to add speed.** No study compares accuracy first with speed from the start. Expert guidance says not to time the introduction of a concept (WWC panel). The usual entry criterion for fluency work is 80% accuracy.
- **Costs.**
  - Math anxiety correlates with performance at r = −.28 to −.34, more strongly on multistep tasks (Namkung et al. 2019; Barroso et al. 2021).
  - Time pressure raises state anxiety in the short term. Bell pacing against self pacing made no performance difference in undergraduates (n = 35).
  - Pressure harms people with high working memory on demanding math (Beilock & Carr 2005), and practice until answers are retrieved removed the choking (Beilock et al. 2004).
- **Exam pacing.** The share of time used did not predict grades over six engineering courses (R² = 0.023). Extra time did not raise online quiz scores. No study tests practicing against a pace target.

**What this means for Toishi:**
1. **The order stays: accuracy first, then pace.** M1 is untimed, and M2 and M3 add pace. No clock runs during practice; the time appears after submitting (TIME rules). This is what the guidance says. **B** for the order, **C** for pace as a requirement.
2. **The pace requirement itself is grade C, and the owner's choice.** Nothing shows that training to a standard time raises timed exam scores. What the sittings check is what an exam checks: a block of problems in its time (v1.3).
3. **Sittings show the block time and never cut off.** That keeps the rehearsal and limits the pressure. The Untimed switch (TIME-6) stays for practice sessions. A sitting is always timed.
4. **Maintenance at the target is the anti-choking part:** practice until retrieval is fluent removed choking under pressure (Beilock et al. 2004). **B**.
5. **Log it, don't tune it:** time per sitting, pass rate by predicted pass chance, and exam scores entered against readiness (6.5). Revisit after real use.

## 8. Decisions for the owner

1. **The accuracy target and the daily load.** The simulator's typical student has a 65% starting accuracy (Koedinger et al. 2023's median). Under the model, that student needs about 70 successes on a component to reach 0.90, so they can't certify M1 by its 5-day deadline, and their planned load grows without bound. Real logs also level off near 89% (audit #17).
   - Options:
     - **(a)** Keep 0.90 and the full reported load, and let Today show what fits in the student's chosen time, in priority order, beside the full cost.
     - **(b)** Set the targets by milestone: M1 0.80, M2 0.85, M3 the course target.
     - **(c)** Keep 0.90 and lower only the default tier to 3.
   - The numbers from the real planner come first (the simulator rerun after the merges).
2. **The comparison line under the solution** (§1, proposal 5).
3. **How a new skill opens**: decided as problem first, with the example as aided reference (§5). The owner can reverse it.

## 9. Pace training (owner, 2026-11-02, 17:52 and 18:02)

The owner asked for speed to be trained, not only measured: some students would score above 90% with twice the time. He left the design to the coordinator, on two conditions: decisions come from data and research, and each one is labelled with its evidence.

The current design:
- measures pace and requires it for M2 and M3;
- has a fixed speed-up of 3.5% per doubling of practice, against 2–2.5% measured in the logs;
- tracks speed as an all-time average;
- times only whole problems.

A student at twice the standard time therefore never reaches M2.

Inputs being gathered: a deeper research pass (`speed_training_deep.md`) and public math logs with solve times (`timing_datasets.md`). From them, the coordinator will measure speed-up rates per student, whether slow starters catch up, and which practice produces speed. The pace-training design (v1.4) follows from those results.
