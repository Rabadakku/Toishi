# Toishi Software Spec

Nov 1, 2026

## Goal

Toishi (working name) is where a student turns what they understood in class into skill they keep. Outside the app, the student only reads the textbook, attends class and takes notes to understand the ideas. Everything else happens in one daily queue here: practice, learning by doing, fixing weak spots, long-term review and exam prep.

It is an Anki-style Mac app that runs fully offline. It ships with a verified problem bank and imports card files and Anki decks. Each day it serves a set number of problems from every section the student has switched on, mixed together, and checks typed math answers with computer algebra.

Seven design choices carry the effectiveness, each grounded in the Toishi research report:

- **Skills are scheduled, not cards.** FSRS times each skill, and every review draws a fresh problem, so nothing gets memorized.
- **A skill is learned before it is tested.** A worked example comes first, then fresh problems until two or three in a row are right.
- **Remembering and doing are measured separately.** Recall says whether a skill will come back when needed; Level says whether exam-tier problems get solved, at exam pace when the exam is timed.
- **Practice is mixed.** Problems from all active sections arrive without labels, so the student must recognize which method applies.
- **Feedback teaches.** Every problem ends with a full worked solution, and errors are routed back to the prerequisite that broke.
- **Answer keys are trusted.** Code computes them wherever possible; independent checks verify the rest.
- **The app checks itself.** It logs every attempt, so its predictions can be tested against the student's real results.

Success means the student does the day's queue, walks into every exam having practiced each skill at exam level, and still has Calculus I when Calculus III needs it.

**Charter.** Correctness of grading, scheduling and saved progress comes before new features (owner decision, 2026-11-01).

## How a student uses it

The student opens the app once a day, presses Start, works each problem on paper and types the answer. A pause button is always on screen for a meal or a break, and only active time ever counts. Every feature serves that loop.

**A normal day** (20 problems, about an hour):

1. Home shows "Today: 20 problems, about 55 minutes" split across the active courses, with minutes from his own active pace, plus any exam countdowns. It never shows an overdue count.
2. Problems arrive mixed: reviews from every switched-on section, a short learning block for one or two new skills, and checks triggered by recent mistakes. No section labels appear until after answering.
3. For each problem the student types an answer, sees "We read your answer as ...", submits, and gets a verdict plus the full worked solution.
4. After a miss, the worked solution appears as numbered steps. One tap marks the first step where his work went differently, or says "didn't know where to start", "careless slip" or "I used a different method". The app then schedules a quick check problem on that step's skill and a fresh problem later.
5. The session ends with a short summary and tomorrow's forecast. Extra practice is offered, never pushed.
6. On a tired day, "Lighter set" keeps the same due skills but serves easier problems.

**A new section is taught in class.** The student marks it "Learning now" in the Library. Its skills are introduced a few per day, each through a worked example and a short block of problems, then mixed into review. The Library shows when the whole section will be introduced at the current pace.

**Goals and exams.** Each course has a goal (A, B or Keep) and a goal date, usually the final. Setting a goal shows what it costs per day before it is saved. The student enters each exam's date and sections. Everyday review keeps recall around 90%, and in the last three weeks before an exam the app adds booster reviews, so each in-scope skill is predicted at 95% on exam day for an A goal, and serves exam-level problems. An exam can carry a blueprint of its sections, points and minutes. Practice tests, from an untimed section up to a full paper at 90% of the time, are offered from three weeks out, with feedback at the end like a real exam and a report of where the points were lost. After the goal date the course drops to Keep.

**Speed comes after understanding.** While a skill is being learned, time is ignored. Once it is learned, it gets a target time from exam pace and his own improving times. Time shows only after he submits ("3:40 · target 4:00"), never as a countdown. Exam-level and Mastered require target pace only when an exam with a length is entered; otherwise the target time is information only.

**Several courses at once.** The daily count is shared across active courses by goal and exam urgency, with a minimum for each course, and problems from all of them are mixed through the session.

**A missed week.** The daily count stays the same. The app does the most valuable reviews first and quietly spreads the rest; there is no pile to face. If the backlog stays above twice the daily count for a week, it suggests raising the count or taking a short re-check. Vacation mode pauses the schedule ahead of time. After three or more missed days, the first open shows a plan to get back on track and holds new skills until then.

**Bringing in cards.** The student imports a card file or an Anki deck, approves the preview, and the new cards join the same queue. Untagged problems can be tagged outside the app with an AI tool, using the published skill list and tagging prompt; they stay marked unverified until checked.

## Release 1.0 scope and non-goals

Release 1.0 is the core app plus whatever Calculus I content passes the pilot rule (PACK-11), shipped before the end of the fall 2026 semester: every 1.0 feature below works, is tested, and is built into a Mac app on the student's own Mac. Release 1.1 follows right after the semester with the full exam layer and the rest of stats and settings. Later course packs follow as separate releases. The owner chose this order on 2026-11-01.

| Area | In 1.0 (before the final) | In 1.1 (right after the semester) |
| --- | --- | --- |
| Study | Daily queue shared across courses, course goals with goal dates, learning phase for new skills, mixed reviews, exam boosters, simple practice tests (an exam date, N exam-tier problems, graded at the end), flashcards and cloze cards, pause and active timing, undo, session resume, Focused Practice | The staged practice-test ladder with attempt labels and a lost-points report, a mistakes list that retires closed mistakes and drilling from it, the return-from-break plan, paper mock exams and retest papers, Pass/Fail flashcards |
| Math | Typed math input (math keyboard and plain text), a "read as" preview, a checker for every math answer type in the card format, KaTeX rendering, function plots | Units and significant figures, with the Physics I pack |
| Scheduling | FSRS-6 per skill and per flashcard, the rating map, Elo problem selection, prerequisite checks after errors, step-tagged error diagnosis, the weak-spot finder, target times, Recall and Level, partial credit in shadow mode, the adaptive learning gate and parking of stuck skills, leech repair, vacation mode | Exam-weight priority, the readiness range, mixing and form logging |
| Content | Pack loader, skill graph, provenance, a credits screen; the Test pack, the Answer Input Tutorial deck and Calculus I content that passes the pilot rule | The Physics I pack |
| Import and export | Card files and packs; Anki `.apkg`, `.colpkg` and plain text with optional review history, through the import screen; backups and restore; open-format export (EXP-5) | Anki export of own flashcards; real exam results and paper mock exams |
| Library | Course, unit and section toggles, section states, exams with dates, lengths, problem counts, calculator policy and optional blueprints, a placement check, a study plan |  |
| Tools | Profiles; a minimal Weak areas screen with learn links; a minimal Settings screen | Card browser and editor with bulk tools, the stats dashboard, the full settings |
| Platform | macOS only (Apple silicon), built and self-tested on the student's own Mac |  |
| Look | Complete keyboard control; the theme follows the system, with an override in Settings | The break reminder |

Not in 1.0:

- **Course content.** Every course after Calculus I ships as packs after 1.0.
- **Units and significant figures.** The card format defines them now; grading support lands with the Physics I pack (1.1).
- **Anything online.** No sync, accounts, cloud, telemetry or update checks. The app never opens a network connection.
- **AI in the app, now or later.** No model calls of any kind, not even optional or bring-your-own-key, because randomized trials found unguarded AI tutoring lowered exam scores (docs/research).
- **Add-ons, mobile apps, drawing input.** Curve sketching is answered with typed features such as intervals and points.
- **Windows and Linux.** The app is Mac-only (Apple silicon).
- **The C++ coding environment** and **a planner-app connector**, both scheduled later.

"Production ready" has a fixed meaning here, spelled out under Quality bar: no known crash or data-loss bugs, the grader test suite passing, a built app that runs offline in a fresh macOS user account, verified backup and restore, and two weeks of daily use without a blocking issue.

## Core concepts

The app schedules skills, and cards are just the problems it serves for them. Shipped content and the student's progress live in separate files, linked by permanent IDs, so a content update never touches progress.

&#91;embedded content: concept model · what ships vs. what is the student's\]

Each skill's state and every attempt are recorded against shipped IDs; section states, settings and backups belong to the student's profile.

| Term | Meaning |
| --- | --- |
| Course, unit, section | The course tree. Sections are what the student switches on and off |
| Skill | One thing a student can do, tested by one kind of problem. The unit FSRS schedules |
| Card | Anything shown: a problem, a variant instance, a worked example, a flashcard or a cloze card |
| Pool | All the cards for one skill; each review draws a fresh one |
| Tier | Difficulty from 1 (Drill) to 5 (Elite) |
| Core band | The tiers whose results count as FSRS reviews for a skill at its current stability |
| Stability | FSRS's estimate of memory strength: the days until predicted recall falls to 90% |
| Recall | The predicted chance of solving a fresh, typical problem unaided right now (FSRS calls it retrievability) |
| Desired retention | The recall level at which a skill comes due; default 0.90 |
| Learning phase | A worked example, then fresh problems until two to four in a row are right (ENG-2) |
| Lapse | A failed review; the skill goes to relearning |
| Prerequisite | A skill that must be learned first, and where errors get routed |
| Encompassing edge | A weighted link saying skill A practices skill B, used for partial credit |
| Partial credit | The fractional review credit B receives when A is passed |
| Check | A quick problem on the sub-skill the student blamed for a miss |
| Leech | A skill that keeps lapsing, which triggers a repair |
| Pack | A versioned bundle of skills, cards and media |
| Profile | One student's progress, settings and media |
| Goal and goal date | A course's target (A, B or Keep) and the date it must be met by, usually the final; sets retention, exam-day recall and Level targets |
| Booster | An extra review timed so a skill's recall reaches the exam-day target |
| Level | How well a skill can be done: Learning, Learned, Exam-level or Mastered. Changes only with evidence, never with time alone |
| Active time | Time a problem is on screen with the app in front and not paused; the only time that counts |
| Target time | The solve time a learned skill aims for at a tier, from exam pace and the student's own improving times |
| Method-choice skill | Choosing the right method from a family of easily confused ones, such as which limit technique fits |
| Step-tagged solution | A worked solution split into numbered steps, each labeled with its skill, used to find where a miss went wrong |

## Library, scope and onboarding

The Library is the course tree (course, unit, section, skills) where the student decides what is in play. Each section has one of four states, and the state tells the scheduler how to treat its skills.

| State | Meaning | What the scheduler does |
| --- | --- | --- |
| Off | Not being studied (yet, or anymore) | Skills stay out of the queue but stay in the skill graph, so errors can still be traced to them |
| Learning now | Being taught in class | New skills are introduced at the daily rate, ahead of other new skills |
| Covered | Taught before; partly known | Skills start in review with a short provisional interval; the first review confirms or demotes them |
| Solid | Known well | Skills start in review with a longer provisional interval |

**Library requirements**

- **LIB-1** Toggle any level: course, unit or section. A parent sets all its children; mixed children show a partial mark.
- **LIB-2** Each section shows its skill count, how many are learned and mastered, current recall ("fading" when low), and its pace ("all skills introduced by Thursday").
- **LIB-3** New skills follow the prerequisite graph, then section order. A skill is introduced only after its prerequisites are learned or placed.
- **LIB-4** Goals and exams. Each course has a goal (A, B or Keep; default A) and a goal date, usually the final. Each exam has a name, date and time, the sections in scope, and optionally its length in minutes, problem count and calculator policy; its exam-day recall target comes from the goal. Several exams can be active, and a final can cover a whole course. Setting or changing a goal shows its projected daily load ("about 14 problems, 40 minutes a day") and warns when all goals together exceed the daily count.
- **LIB-5** Each section can show the student's textbook reference, such as "Stewart 4.3". The app never shows textbook text.
- **LIB-6** Switching a section off never deletes progress, and switching it back on resumes where it stopped.
- **LIB-7** Milestones: one quiet banner when a section's skills are all learned and when a course is fully mastered.
- **LIB-8** After the goal date a course drops to Keep. Skills that are prerequisites of a course he is taking next are held at 0.85 instead of 0.80, and about three weeks before that course starts they get boosters to 0.90.
- **LIB-9** Each course page shows its goal, days left, the share of exam skills at Exam-level or above, and a projected exam score range (STA-12) with what is holding it back (recall or level). When the projection falls short, the app proposes extra daily problems; it never adds them silently.
- **LIB-10** Exam blueprint (optional). An exam can carry a blueprint: sections with item count, item kind, points and minutes, plus a weight of 1 to 3 per skill (a skill without one counts 1). Exam details come only from what the student enters or imports, never from code. Blueprints save and load as plain files, so a class can share one. A test built to the exam's real shape is the closest rehearsal.
- **LIB-11** Real results. After a real exam or a school mock, the student can enter a grid: question, points, points earned, optional minutes, and the skills it tested. Results are stored as exam results, never as FSRS reviews. They feed the lost-points report (STA-13), the weak-spot finder (ENG-15) at half weight, and the readiness check (STA-12).
- **LIB-12** Study plan. After the first session, one screen asks when and where the daily set happens, the likely obstacle, and an if-then plan ("If I get home late, I do the set before dinner"). Home shows the plan again after two missed days, and Settings can edit it. Evidence on planning prompts is mixed, so the prompt stays short.
- **LIB-13** (1.1) Rubric items. A blueprint item kind "rubric" gives points per step, adding up as the steps are reached. The student marks them at the end of the test; the score counts partial points, and FSRS follows the existing rubric map.

**Goal presets.** Running 0.95 retention all semester would cost about twice the daily work, so a goal keeps everyday retention moderate and uses boosters to reach a higher recall on exam day. The numbers are starting values, tuned from his own data after a semester.

| Goal | Everyday retention | Exam-day recall | Level target for exam skills | Hardest tier served | After the goal date |
| --- | --- | --- | --- | --- | --- |
| A | 0.90 | 0.95 | Exam-level for all; Mastered for core skills | 5 | Keep (prerequisites of the next course at 0.85) |
| B | 0.88 | 0.92 | Exam-level for core skills; Learned for the rest | 4 | Keep |
| Keep | 0.80 | None | None | Unchanged | Keep |

**First run**

1. Create a profile; only a name is needed.
2. Pick a daily problem count (default 20), with projected minutes shown beside it. The theme follows the system; Settings can override it.
3. Choose the subjects to cover (courses from the shipped packs and any imported decks), give each a goal and a goal date, enter known exams (date, and optionally length, problem count, calculator policy and a blueprint), and set each section's state. Everything starts Off.
4. Do the Answer Input Tutorial deck, or skip it: a few minutes practicing how to type fractions, roots, intervals and points.
5. Take the placement test for the chosen subjects. It is the default first session, can be skipped or paused, and its results seed each skill and fill the first Weak areas list (STA-11).
6. After that first session, write the study plan (LIB-12).

**Placement check**

- It uses the graph: one standard-tier problem per skill. It asks a skill in the middle of the remaining range first, then halves the range: a pass marks that skill's prerequisites provisionally known, and a fail prunes the skills that depend on it. A single pass never marks a deep chain known without a confirming question. This is the ALEKS and Math Academy principle; in simulation the old deepest-first walk seeded 10-15% of known skills against 60-80%.
- Every question has an "I don't know" button. The check can be skipped, paused, resumed and re-run.
- It stops after 25 questions per course.
- A skill passed directly starts in review with a provisional stability of about 10 days; one inferred from a passed descendant gets about 2.3 days. Failed and "I don't know" skills start as new. The first real review on a fresh problem confirms or demotes each one.
- Placement only ever adds knowledge. It never takes progress away.

## The daily queue

Each day the app plans one session of N problems, the student's count, plus up to M flashcards, then mixes them. It re-plans after every answer, so reinforcement and checks take slots from the lowest-priority items, which move to tomorrow.

**What counts**

- **QUE-1** One graded problem is one question, single or multi-part. Worked examples don't count. A new skill's learning block uses its problems' slots, usually three to five.
- **QUE-2** Flashcards have their own daily limit (default 50). They appear between problems in groups of up to five. A flashcard linked to a skill the student just missed appears right after that miss's solution, as a refresher.
- **QUE-3** Every attempt is timed silently, counting only active time (TIME-1 to TIME-6). Home shows projected minutes from the student's own median active time per skill and tier, taken over log times so one long problem doesn't skew it. An optional minutes cap ends the plan early.

**What gets picked when more is due than N**

| Order | Item | Reason |
| --- | --- | --- |
| 1 | Prerequisite checks triggered by recent errors | Quick, and they decide where the next repair goes |
| 2 | Relearning reviews: the next-day redo after a lapse | A lapse that isn't followed up is wasted |
| 3 | Learning blocks already in progress | Half-learned skills fade fastest |
| 4 | Reviews of prerequisites of anything being learned now or recently failed | Forgotten foundations block new learning |
| 5 | Exam-window reviews: skills whose recall on exam day would miss the target | Exam dates don't move |
| 6 | Other due reviews, highest current recall first | Saves the skills that are still saveable |
| 7 | New skills | Cut first when the day is full |

- **QUE-4** No due skill waits more than 7 days past due (a setting). After that it moves up to order 4. With this rule, the default triage behaves like oldest-due-first.
- **QUE-5** New skills are introduced only while the projected 7-day average load stays at or under N. Default: up to 4 new skills a day, "Learning now" sections first.
- **QUE-6** Order 6 reverses what was suggested earlier in chat. FSRS-era Anki guidance does the most-recallable reviews first, but that evidence comes from flashcards. The triage policy is therefore pluggable, every session records which policy ran, and stats compare policies on the student's own data.

**Sharing the day across courses**

- **QUE-11** With several courses active, the daily count is split by weight: goal (A 1.5, B 1.0, Keep 0.5) times exam urgency (1, rising to 3 over the two weeks before an exam) times backlog (due work against the other courses, between 0.5 and 2). Each course with due work first gets a floor of 3 problems or 10% of the count, whichever is larger. The rest is shared by weight and rounded so the quotas add up exactly to the count. A course with less due work than its quota hands the surplus back. Inside each course's share the triage order above applies.
- **QUE-12** Courses are mixed through the session in proportion to their quotas, never run one after another, so stopping partway still serves each fairly. If the student stops early, each course's shortfall carries into tomorrow, capped at half a quota. Quotas also show in minutes, since a chemistry problem can take three times as long as a drill.
- **QUE-13** A course adds new skills only while its own backlog is under one day's quota. If total need across courses exceeds the count for 3 days running, the app proposes raising the count for a while, lowering a goal or moving a course to Keep. It never drops due reviews silently.

**How the session is ordered**

1. Two or three quick reviews come first as a warm-up.
2. Two problems from the same skill never come back to back. Problems from the same section sit at least two apart where possible.
3. Confusable skills are placed next to each other, so the student practices telling them apart; immediate succession worked best in the Brunmair and Richter meta-analysis. For each confusable pair, adjacent or separated placement is randomized so the effect can be measured (QUE-23).
4. A new skill's learning block runs as one unit: worked example, then its problems. It never opens the session.
5. A reinforcement problem comes at least five items after the miss that triggered it; a prerequisite check, at least three.
6. Harder and easier problems alternate.
7. Skill names stay hidden until after the answer.

**Reason tags.** Every item carries one tag: Review, Relearn, New skill, Check (after a miss on X), Exam prep, Redo (a problem missed days ago), or Stretch. A small "Why is this here?" link explains it in a sentence.

**End of session.** A summary lists problems done, time, misses with their tags, and skills learned, plus tomorrow's forecast. "Extra practice" offers tomorrow's most useful items. "Practice test" appears when an exam is within 21 days (QUE-18).

**Backlogs, breaks and tired days**

- **QUE-7** No screen ever shows an overdue count.
- **QUE-8** If the backlog stays above 2N for 7 days, the app suggests raising the count, a short re-check, or spreading the load over the next week.
- **QUE-9** Vacation mode takes a date range and moves reviews slightly earlier before it and later after it, so the surrounding days carry an even load.
- **QUE-10** "Lighter set" keeps today's due skills but serves tier 1 and 2 problems and adds no new skills. Its problems sit below the core band (ENG-4): a miss is Again and a success changes nothing, so an easy day can't overstate recall.
- **QUE-17** Back from a break. On the first open after 3 or more missed study days, Home shows "Back on track by \<date> at N a day" with three paces to choose from (N, 1.5N or 2N). New skills wait until that date. Young skills (stability under 7 days) restart with a worked example. The return, not the routine, is where people quit.
- **QUE-23** (1.0) Confusable placement. Confusable pairs are placed next to each other by default. For each pair, the app randomizes adjacent or separated placement and logs which, so ENG-18 compares like with like.
- **QUE-24** (1.0) Booster cap. Boosters take at most half of the day's problems (a provisional default); the rest move to other days inside their windows. Without a cap, the last 21 days before an exam carry about six times the usual reviews.
- **QUE-25** (1.0) Out of fresh problems. When a skill has no fresh problem left for the day, its slot is skipped, never filled with a repeat, and the Library flags the pool as too small (ENG-2, ENG-5).

**Other ways to study**

- **QUE-14** Focused Practice: the student picks a section, a skill or the current weak spots and practices outside the plan. Problems come from the same pools, results count as ordinary reviews (FSRS gives little extra stability to a skill reviewed early), and new skills still go through their learning phase.
- **QUE-15** Undo last answer: the U key or Edit > Undo Last Answer, available until the next answer is submitted, rolls back the attempt, its rating, the FSRS state and the Elo change in one transaction and shows the problem again. An undo after the solution was shown keeps "solution shown", so the re-answer can never be a clean Good.
- **QUE-16** Resume: the session plan, the current problem, its active time so far and any typed answer are saved after every action, so a quit, crash or restart resumes at the same problem. A plan from before the study-day rollover is rebuilt.
- **QUE-18** Practice-test ladder. An exam's practice tests come in four types, unlocked in order: an untimed section, a timed section, a full timed test, and a full test at 90% of the time. They are offered from 21 days before the exam (the booster window) or on request, and the app suggests at most about 6 to 9 full tests per exam cycle. With a blueprint (LIB-10), a test follows its sections and is assembled greedily: the uncovered skill with the highest priority (ENG-17) first, no skill repeated before every skill is covered, fresh problems only. Without one, a test draws exam-tier problems from the scope weighted by 1 − R + 0.2. One try per problem, graded at the end; unanswered problems stay unrated.
- **QUE-19** Attempt labels. Every practice-test attempt gets one label: Perfect (correct within the target time), Overtime (over the target time), Rushed (wrong in under half the target time), Skipped (unanswered), or Wrong (any other miss). The test report shows the mix and first-pass accuracy. Labels never change a rating: a wrong answer on a practice test is Again for its skill at every tier, exam tiers 4 and 5 included, because a real exam scores it zero, and time pressure never excuses a miss from FSRS (ADR-0014). Overtime counts as pace evidence for Level.
- **QUE-20** Drill from mistakes. Focused Practice (QUE-14) adds three sources: open mistakes (STA-14), answers marked guessed or unsure, and the top 5 weak skills. Each serves fresh problems on those skills, optionally timed, and counts like other Focused Practice.
- **QUE-21** (1.1) Paper mock exams. The app prints an exam from its blueprint (LIB-10) with an answer sheet: corner markers, a QR code per page, bubbles for choice items, digit grids for numbers (sign, decimal point, fraction bar), and a list of answers to type in later.
  - Input: scan with the iPhone's Continuity Camera "Scan Documents", AirDrop a photo, drag in a file, or tap the bubbles in the app. There is no iPhone app.
  - Bubbles are read by deterministic optical mark recognition, with no AI. Any uncertain mark is asked about, never guessed.
  - Expression answers are typed and graded by the normal checker; long answers are self-scored on their rubric (LIB-13).
  - A confirmation screen shows every read answer beside its cropped image before anything counts.
  - Results are reviews, and a miss is Again (ADR-0014). They feed the lost-points report (STA-13), the readiness range (STA-12) and the mistakes list (STA-14). Scratch-work photos can be attached to mistakes.
  - Before building: spike Continuity Camera in the pywebview window, measure OMR accuracy on phone scans, and check the evidence on paper versus screen practice.
- **QUE-22** (1.1) Retest papers. Open mistakes and weak skills print as a PDF paper with a separate answer-key page, through the same printing as QUE-21.
- **QUE-26** (1.1) Pass/Fail flashcards. An option to answer flashcards with two buttons: Pass is Good, Fail is Again.
- **QUE-27** (1.1) Not now, and practice only. An ungraded "Not now" sets a card aside for the session, and a "practice only, don't schedule" switch records a session's attempts without any FSRS event.
- **QUE-28** (1.1) Outside help. An "I used outside help" flag on an attempt downgrades its rating, as a hint does, because the answer no longer measures unaided recall.

## Study screen

The study screen shows one problem in a calm, centered column with nothing else competing for attention. The student works on paper and types only the final answer.

At the top sit the reason tag and progress ("7 of 20"). Below them are the problem, any figure or plot, and one answer box per part. The buttons are Submit, Hint and Give up, and a pause button sits at the top right. No clock runs on screen during a problem; the active time appears only after submitting, beside the skill's target time once it has one.

**Pause and active time**

- **TIME-1** The pause button (or Esc, or P) stops the clock and blurs the problem, so a break isn't extra thinking time. Resume unblurs it.
- **TIME-2** The clock also pauses by itself when the window loses focus, the student switches apps, the screen locks or the Mac sleeps.
- **TIME-3** It never pauses for keyboard or mouse inactivity, because the work happens on paper. After a long stretch with no input (three times the target time, at least 5 minutes), a quiet "Still working?" note appears. With no answer within 60 seconds, the clock pauses and trims the time back to when the note appeared.
- **TIME-4** Solve time (problem shown to first keystroke in the answer box) and entry time (first keystroke to submit) are stored separately. Speed rules use solve time plus a typing allowance of 5 seconds and 0.3 seconds per character of the expected answer, so typing math slowly never counts as slow thinking.
- **TIME-5** An attempt is capped at four times its target time (at least 3 minutes, at most 30). Raw and capped times are both stored. Attempts with a pause over 2 minutes, the first attempt after the Mac wakes, and attempts where a hint or worked example was opened are left out of speed baselines.
- **TIME-6** An Untimed switch for a session: nothing from it counts toward speed or Level's pace requirement.

**Answering**

1. The student types in the math field, using the math keyboard or plain-text mode (one key switches). A live preview reads "We read your answer as ..." with multiplication made explicit.
2. A syntax error or a wrong answer shape ("expected an interval") shows inline and never counts as an attempt.
3. Enter submits; Shift+Enter submits marked "unsure". A correct answer shows the verdict, the full worked solution and the skill's name. Space continues; E marks it "too easy".
4. A wrong first attempt shows "Not quite" and nothing else. Two attempts are allowed by default.
5. A wrong final attempt, or Give up, shows the full solution with the student's answer beside the correct one, then the "What went wrong?" picker, scrolled into view with its "Pick one to continue" note visible, so the screen never looks stuck.
6. If the checker can't decide, the app shows the solution, the student self-grades, and the case is logged for grader review.

**Hints** come from the card's hint ladder, one per press. Any hint caps the rating at Hard; the last hint, which gives the first step, counts as Again.

**Multi-part problems** have one box, verdict and attempt count per part. A part with its own `skill` reports to that skill: success gives it partial credit, and a miss starts a prerequisite check. The card's own skill takes the worst rating among its remaining parts.

**Self-graded problems** show a Show solution button. With a rubric, the student ticks the steps they matched: all ticked is Good, all but one is Hard, fewer is Again. Without one, three buttons: Matched the solution, Minor slip, Didn't get it. A Minor slip is a wrong final answer: Again, flagged slip, like a careless slip.

**Flashcards** work like Anki: front, Space to show the back, then Again, Hard, Good or Easy on keys 1 to 4. A flashcard with an `answer` asks the student to type it and grades automatically, because typed recall beats recognition.

**Find-the-error problems** show another student's worked solution with one wrong step, drawn from a known common mistake. The student picks the wrong step, chooses why it is wrong from three or four reasons, and types the corrected value; then the correct solution appears beside it. They unlock for a skill after two successful uncued reviews, come at most once in every eight to ten reviews, and count as a review of that skill. Early on, a highlighted version ("Step 3 is wrong. Why?") is used instead.

**Which-method problems** show an uncued problem and ask only which method fits, in about 5 to 15 seconds. They train the section's method-choice skill and are mixed in with full problems, never replacing them.

**What went wrong?** After every miss the worked solution shows as numbered steps, starting with Step 0, "Set up and choose the method". Each step has a one-line label and its skill. One tap marks the first step where the student's work went differently, or picks another option. When the typed answer matches one of the card's known wrong answers, its feedback shows and the step behind that mistake is preselected, labelled "likely" (ENG-21).

| Choice | Effect |
| --- | --- |
| A step (tap it) | A quick check problem on that step's skill, at least three items later or next session. Check fails: that skill gets Again, and its low-recall prerequisites get checks, deepest first. Check passes: an integration error on the problem's own skill, which gets a plain Again that counts for Level and leeches. Only slips and misreads within their 30-day cap are excused |
| Step 0: didn't know where to start or which method | A cued twin: the same kind of problem with the method named. Solved: a method-choice gap, so the section's method-choice skill gets Again. Not solved: a gap in the method itself, so the problem's skill lapses and a worked example comes before its next problem |
| Careless slip, my steps matched | Again, flagged slip: FSRS sees it, Level and the leech counter ignore it, and no reinforcement problem follows (ADR-0014). Accepted only when the skill is strong (recall at least 0.90 and its last two attempts correct), at most once per skill per 30 days. A second slip on the same skill within 30 days becomes a step error with a check |
| Misread the question | Same as a careless slip, sharing its limit |
| I used a different valid method | No step blame; the problem's skill takes the lapse, and the solution shows the alternative method if the card has one |
| Can't tell | Lapse on the problem's skill; no check |

A tap is evidence, not a verdict, because people diagnose their own errors poorly without support. It puts 0.6 of the blame on the tapped step's skill (0.8 only when the answer matched one of the card's own coded wrong answers) and spreads the rest over the other steps' skills by how weak they are. The app logs each tap with whether its check confirmed it and how long the tap took. Control probes (ENG-22) measure whether taps beat chance; if they don't, taps count for less. A miss submitted "sure" is a confident error: the solution says so, and the next-day redo is guaranteed. Give up, the last hint and "didn't know where to start" are never confident errors; the screen shows the engine's verdict and never works it out again. "Check your answer" is a habit prompt after slips, not a scheduled skill.

**Rating map** (how each outcome becomes an FSRS rating)

| Outcome | Rating |
| --- | --- |
| Correct on the first attempt, no hints, submitted sure | Good |
| Correct and sure, however slow | Good: time never changes a rating (ENG-14) |
| Correct, sure and marked too easy | Easy (can be disabled) |
| Correct on the second attempt, after a non-final hint, submitted unsure, or marked guessed | Hard (provisional) |
| Careless slip or misread within the cap, or a self-graded Minor slip | Again, flagged slip (Level and the leech counter ignore it) |
| Wrong after the last attempt, gave up, used the last hint, or didn't know where to start | Again |
| A stretch problem (above the skill's core band), right or wrong | No FSRS event; only the difficulty model updates |
| Below the core band (the Lighter set, below-band checks) | A miss is Again; a success has no FSRS event (ENG-4) |

**Provisional ratings.** The Hard ratings for a second-attempt success, any hint and "unsure" are untested hypotheses: a researchers' simulation found that grading 10% of passes Hard raises workload about 19% with no recall gain. They stay provisional and are evaluated against the strict label at about 300 rated items (DEV-16).

**Buttons after grading**

- **I was right:** disputes the grading. The case is logged with the exact input, the attempt doesn't count, and the student self-grades. Disputes collect in a review list. The void and the dispute record are written in one transaction.
- **Report problem:** hides the card from every future queue at once, removes the attempt from scheduling, and logs it for re-verification.
- **Guessed** (on correct answers), **Flag**, **Suspend**, and **Edit** (the student's own cards only).

**Redo.** A missed problem comes back once: the next study day after a confident miss, 3 days later after an unsure one. A redo repeats a known problem, so it is unrated practice; when the skill is due, a fresh problem is the rated review and the redo follows it (ADR-0014). Every rated review draws a fresh problem.

**Keys:** Enter submit, Shift+Enter submit unsure, H hint, G give up, Space continue, E too easy, 1 to 5 in the picker, D dispute, R report, Esc or P pause, U undo the last answer.

## Learning engine

FSRS decides when each skill is due; a separate difficulty model decides which problem to serve; the skill graph spreads credit and routes errors. FSRS has never been validated for skills with fresh problems, so the engine logs enough to check its own predictions.

**ENG-1 Scheduler.** FSRS-6 through py-fsrs 6.3.2 (MIT), pinned behind an adapter so FSRS-7 can replace it. One FSRS card per skill and one per flashcard. Settings: `learning_steps=()` and `relearning_steps=()`, because the app runs learning and relearning itself; fuzz on; maximum interval 365 days; desired retention from the course goal (A 0.90, B 0.88, Keep 0.80). Due dates are computed live from stability and the course's current retention, so changing a goal reschedules nothing and needs no refit. FSRS-7 is still unreleased as of November 2026. Retrievability is computed from fractional days, because py-fsrs counts whole days:

```latex
R(t, S) = \left(1 + F\,\frac{t}{S}\right)^{-w_{20}}, \qquad F = 0.9^{-1/w_{20}} - 1
```

All times are stored in UTC. The study day rolls over at 4 AM local time (a setting).

**ENG-2 Learning phase.** A new skill always starts with a worked example: an `example` card, or, when the skill has none, a tier 1 problem shown solved before any problem is asked. Then come fresh tier 1 and 2 problems, at most eight, until enough in a row are correct without hints. The gate adapts, because a higher in-session bar buys little retention for its time:

- **2 in a row** when the phase's first attempt is clean.
- **3 in a row** after any miss in the phase.
- **4 in a row** for skills whose lapse rate after Learned is in the course's top quarter, once 30 or more of the course's skills are learned.
- Never more than the pool allows: the gate is min(N, distinct eligible problems), so a tiny pool can still finish, and the Library flags that pool as too small.

The app logs which rule fired and compares strict success at the next review. On success the skill is Learned, and its FSRS card is created by replaying those attempts, which gives a first interval of about two days. On failure the phase stops, the skill's prerequisites get quick checks, and it restarts the next day with the worked example again. After a second failed phase the skill is parked for 3 study days: it is listed under Weak areas (STA-11) with its textbook reference and learn links, and new skills that require it wait. Time is never judged during the learning phase.

**ENG-3 After a lapse.** One fresh reinforcement problem comes later in the same session; it is logged but not rated, since a same-day success adds no FSRS stability. The real relearning review is the next study day, on a fresh problem, with the redo of the missed problem after it, unrated (ADR-0014). Then FSRS takes over.

**ENG-4 Core band and the difficulty ladder.** Only problems in a skill's core band produce FSRS events. The band rises with stability, so a well-known skill gets harder problems. Items below the band (the Lighter set, prerequisite checks under the band) never enter parameter fitting; in the live schedule a below-band miss is Again and a below-band success changes nothing.

| Skill stability | Core band | Occasional stretch problem |
| --- | --- | --- |
| Under 7 days | Tiers 1 and 2 | Tier 3 |
| 7 to 30 days | Tiers 2 and 3 | Tier 4 |
| 30 to 90 days | Tier 3 | Tier 4 |
| Over 90 days | Tiers 3 and 4 | Tier 5, if Elite problems are on |

Stretch problems make up at most 10% of reviews and at most one Elite problem per session. Inside an exam window, in-scope skills use tier 3. Stretch problems are unrated, right or wrong, and only a skill due exactly today gets one; its rated core-band review comes the next study day, never later in the same session (ADR-0014).

**ENG-5 Problem selection.** Within the band, an Elo model picks the problem whose predicted success is closest to the course's desired retention for rated reviews, and to 0.80 for learning phases and stretch problems (ADR-0014). It skips problems seen in the last 90 days and prefers a different source or form from the skill's last problem. Template parameter sets don't repeat within 180 days. No card is served twice in one study day, even after its solution was shown: a small pool may relax the 90-day rule but never past today, and if nothing qualifies the slot is skipped. After a skill is Learned, a pool with fewer than 2 problem forms is flagged. Each rated attempt logs whether its form was first seen or repeated, and stats raise a notice when repeated forms beat first-seen ones by 15 points or more over 30 or more pairs (a starting threshold), a sign the pool teaches patterns instead of the skill.

```latex
P(\text{correct}) = \frac{1}{1 + e^{-(\theta_s - d_p)}}, \qquad \theta_s \leftarrow \theta_s + \frac{a}{1 + b\,n}\,(o - P), \quad a = 1,\ b = 0.05
```

Here theta is the student's ability on skill s, d is the problem's difficulty, o is 1 or 0, and n is the number of answers so far. Difficulty starts from the tier (tier 1 to 5 map to -1.5, -0.5, 0.5, 1.5, 2.5) and is anchored there: one student's results move it at most 0.05 per answer, because a single learner can't calibrate a problem (Elo needs about 100 learners for that). A run of surprising results flags a possible wrong tier for review instead. Elo never changes the FSRS schedule.

**ENG-6 Prerequisite checks.** A check is a tier 1 or 2 problem of the tagged skill and counts as a real review of it: within the skill's core band a pass is Good, below it a pass changes nothing (ENG-4), and a fail is Again. Checks obey the no-card-twice-a-day rule (ENG-5). A held miss whose check is never answered settles as plain Again after 7 days. When a prerequisite skill has no problem pool yet (for example algebra or trig before those packs exist), no check is scheduled: the prerequisite is listed as "unverified" under Weak areas (STA-11) with its textbook reference and learn links. Once a pool exists, the check runs as specified. When a foundational skill lapses, the skills that encompass it with weight 0.5 or more get their next review pulled earlier, never their stability cut, and their reason tag says why.

**ENG-7 Partial credit (shadow mode in 1.0).** When skill A passes an explicit core-band review, each skill B that A encompasses with weight w gets this update:

```latex
S_B' = S_B + w\,\left(S_B^{\text{Good}} - S_B\right)
```

S\_B^Good is the stability B would get from a Good review right now, at its fractional-day recall. B's last-review time is not reset, so credit arriving early is automatically tiny. No credit goes to skills that are learning, relearning, failed in the last 7 days, or rated very difficult, and a skill whose stability has doubled from credit alone gets a forced explicit review. Weights along a chain multiply, and products under 0.25 are ignored. In shadow mode the credited stability is stored beside the plain one while the schedule uses the plain one. Credit stays in Shadow through 1.0. It is switched on (setting: Off, Shadow, On) only when a paired confidence interval, with a margin, over at least 800 held-out credited reviews shows credited predictions beat plain ones; a point estimate at 200 reviews passes about half the time when credit is no better. Credit events never enter the optimizer's training data.

**ENG-8 Goals and exam boosters.** Every day from 21 days before an exam, the app predicts each in-scope skill's recall at exam time if it isn't reviewed again. A skill already due before the exam is left alone. For one due after the exam whose exam-day recall would miss the goal's target, the app schedules a booster inside its window, which runs from the first day a Good review keeps exam-day recall at the target to the day before the exam; boosters are load-balanced over their windows, ties going to the earlier day (ADR-0006), and capped per day (QUE-24). For a 0.95 target the window opens about 0.4 times the skill's new stability before the exam: 4 days for a 10-day stability, 16 days for 40. A failed booster relearns as usual and is re-planned the next day, and a final's boosters build on the midterm's. From 21 days before an exam, or on request, the app offers practice tests as a staged ladder (QUE-18), graded at the end; their results count as reviews, and every miss is Again (QUE-19). Boosters are ordered by exam-weight priority (ENG-17). Until the ladder and the priority ship in 1.1, a practice test, offered from the same 21-day window, is a set number of exam-tier problems from the scope, optionally timed at exam pace, graded at the end. After the goal date the course drops to Keep (LIB-8).

**ENG-9 Leeches.** A skill with 8 lapses (a setting; Anki's default, provisional) becomes a leech. It is repaired, not suspended: a worked example, checks on every prerequisite, the textbook reference ("Re-read Stewart 4.3"), then a fresh learning phase. A flashcard leeches at 8 lapses and is flagged for rewriting.

**ENG-10 Recall and Level.** Each skill has two separate measures. Recall is FSRS's predicted chance of solving a fresh problem now, plus its projected value on the next exam day; it fades with time. Level says how well the skill can be done and changes only with evidence:

- **Learning:** started; the learning phase isn't passed yet.
- **Learned:** the learning phase passed. Time is ignored.
- **Exam-level:** correct at the skill's exam tier on at least two different days, with, when pace applies (ENG-13), the median of the last three solve times at or under the target time.
- **Mastered:** at least three successful reviews on different days, at least one after 7 or more days at a predicted recall of 0.90 or lower; successes on at least two problem forms; at least one success above the exam tier or in a mixed check-up; and, when pace applies, the last three correct answers at target pace.

One miss on an Exam-level or Mastered skill marks it shaky, and a second miss within its next three reviews drops it one Level; a miss while Learned returns it to Learning. Getting a Level back means meeting its rule again. Fading (recall under 0.80 now) is a Recall warning, not a Level. Every three weeks or so a short mixed check-up includes a few skills that aren't due; its successes can satisfy Mastered, and its misses count as normal lapses.

**ENG-11 Calibration.** Every review logs its predicted recall and its outcome. Stats group them into bins per course and compare predicted with observed. Bins show a 95% Wilson interval and are greyed under 30 reviews; a notice fires only when a bin's continuity-corrected Wilson interval, adjusted for the number of bins shown, excludes its predicted recall (ADR-0013).

**ENG-12 Fitting the model.** After 300 qualifying items in a domain (math, sciences, coding), and then monthly or whenever long-term items double, the app fits its memory model automatically. New parameters are adopted only when they win on held-out data (ADR-0013), in one transaction; startup repairs a half-applied fit, and fit failures are persisted. Fitting catches fsrs-rs-python's PanicException, which is a BaseException, not an Exception. The fitter is fsrs-rs-python 0.9.3: Rust bindings, about 1.3 MB, no PyTorch, with the same default parameters as py-fsrs, so its output plugs straight in. It also simulates workload for the goal cost estimates. Its package declares no license (the underlying Rust library is BSD-3-Clause), which is fine for personal use and must be settled before any sharing. Review logs can also be exported as CSV and fitted elsewhere. Only reviews graded under the current rating rules are used.

**ENG-13 Target times.** Once a skill is Learned it gets a target solve time per tier: the larger of a floor (20, 40, 60, 90 and 120 seconds for tiers 1 to 5) and the smaller of exam pace and 70% of his median over his first five correct answers after Learned. Exam pace comes from the course's exam length: 85% of the exam's minutes spread over its problems, with single-skill tier 1 and 2 problems taking about a quarter to two fifths of an exam problem's time, and tier 3 and 4 problems a half to four fifths. The target tightens at most 10% a week. These numbers start as guesses and are recalibrated from his logs. Pace applies only to a course with an exam whose length is entered. Without one, Level's pace conditions are off and the target time shows as information only, because nothing supports speed gates outside a timed exam.

**ENG-14 Slow answers.** Time never changes an FSRS rating: a correct answer is Good however long it took, because FSRS grades should describe memory. Time goes only into attempt labels (QUE-19) and Level's pace evidence, and only when an exam with a length is entered (ENG-13). Raw times are stored so grades can be recomputed if the rule changes.

**ENG-15 Weak-spot finder.** Once a day the app compares each skill's results over the last 30 days with what their tiers predicted. Each miss's blame is spread by the step taps or, without a tap, toward the weakest tagged skill; main tags count fully and uses tags at 0.4. A skill is flagged when an exact binomial tail test shows it clearly worse than expected, confirmed sequentially over later answers, with at least five problems' worth of evidence, misses on three different problems and on two different days. A flag schedules a diagnostic set: three or four fresh problems where that skill is the only main skill, at or below his level. Two or more misses confirm the gap (a lapse, then checks on its low-recall prerequisites, deepest first); otherwise the flag is cleared. At most two diagnostic sets a week. The old z ≤ −2 rule falsely flagged about 10% of skills a semester.

**ENG-16 Method-choice skills.** Each family of easily confused methods gets its own skill: choose a limit technique, choose a differentiation rule, choose an integration technique, set up an optimization problem, set up a related-rates problem. Its prerequisites are the methods it chooses among, and it becomes active once two of them are learned. Uncued problems count toward it; cued ones don't.

**ENG-17 Exam-weight priority.** Booster order and practice-test assembly rank in-scope skills by priority = w × (1 − projected exam-day R) × (1 + 30-day lapse rate), where w is the skill's blueprint weight (1 to 3; 1 without a blueprint). A heavily weighted, fading, error-prone skill comes first.

**ENG-18 Measuring mixing.** Adjacency is randomized per confusable pair (QUE-23), and after 1,000 rated reviews stats compare strict success between adjacent and separated placements; a flag on whatever happened to come before would be confounded. Classroom evidence for mixing is now contested, so the app measures it on the student's own data, and authoring effort goes to confusable tables and which-method items rather than wider mixing.

**ENG-19 Load balancer (1.0, built).** When a review is graded, an interval of 3 to 90 days takes its day inside the fuzz range with Anki's weights, (1/n)^2.15 × (1/interval)^3, drawn with a seed from the skill and its last review (ADR-0014).

**ENG-20 Easy Days (1.0, built).** Easy Days follow Anki 26.09.3: each weekday's load share maps to Normal, Reduced or Minimum, which weights that day in the load balancer. They never lower the day's problem count (ADR-0014).

**ENG-21 Likely cause (1.0; shared patterns 1.1).** After a miss the app proposes a likely cause from the card's own coded wrong answers and, from 1.1, the shared mistake patterns of its topic (GRAPH-8). It preselects that step, labelled "likely"; the student's tap still decides, and its check problem stays. The 0.8 blame weight applies only to card-coded matches. A guided step-by-step redo is not built (see Later).

**ENG-22 Control probes (1.0).** On about 10 to 20% of picks, the check also tests one weak step the student did not tap, so the app can measure whether taps beat chance. Every tap logs its time to tap. This replaces the old "fewer than half confirmed" rule, which can't tell chance from signal.

**ENG-23 Time zones and travel (1.0).** The study day follows the Mac's local time and its 4 AM rollover. Each attempt stores its study day when it is graded, so a later time-zone, daylight-saving or rollover change never moves past reviews; DEV-9's clock and DST rules cover this.

**ENG-24 Engine constants (1.0).** Every constant the engine uses is listed with its source. One without a source is a provisional default, logged for evaluation.

| Constant | Value | Source |
| --- | --- | --- |
| Desired retention by goal | A 0.90, B 0.88, Keep 0.80 | 0.90 is FSRS's default; B and Keep: none — provisional default, logged for evaluation |
| Exam-day recall target | A 0.95, B 0.92 | None — provisional default, logged for evaluation |
| Booster window and cap | 21 days; half the daily count | None — provisional default, logged for evaluation |
| Learning gate | 2, or 3 after a miss, 4 for hard skills; at most 8 problems | ALEKS threshold trial, Math Academy, ASSISTments (practice-systems report) |
| Parking | 3 study days after a second failed phase | ASSISTments and Math Academy stop rules; the 3 days: none — provisional |
| Core band breaks | 7, 30 and 90 days of stability | None — provisional default, logged for evaluation |
| Stretch share | 10% of reviews | None — provisional default, logged for evaluation |
| Elo | a = 1, b = 0.05, tier anchors −1.5 to 2.5, 0.05 cap per answer | None — provisional default, logged for evaluation |
| Partial-credit weights | 0.25, 0.5, 1; chains under 0.25 ignored | Math Academy's encompassing idea; the numbers: none — provisional |
| Credit switch | 800 held-out credited reviews, paired interval | Code review simulation |
| Leech threshold | 8 lapses | Anki's default |
| Calibration alarm | Bins of 30; continuity-corrected Wilson | ADR-0013 |
| First fit | 300 items, then monthly or on doubling | ADR-0013 (fsrs-rs health-check gate) |
| Target times (ENG-13) | Floors 20 to 120 s; 70% of the early median; 85% of exam minutes; at most 10% tighter a week | None — provisional default, logged for evaluation |
| Weak-spot finder (ENG-15) | 5 problems, 3 problems, 2 days; 2 sets a week | None — provisional default, logged for evaluation |
| Placement | 25 questions; seeds of 10 and 2.3 days | 2.3 days is FSRS-6's first Good stability; the rest: none — provisional |
| Fair share (QUE-11 to QUE-13) | Weights 1.5, 1.0, 0.5; urgency up to 3; floor 3 problems or 10% | None — provisional default, logged for evaluation |
| Longest wait (QUE-4) | 7 days | None — provisional default, logged for evaluation |
| New skills per day | 4 | None — provisional default, logged for evaluation |
| Slip cap | Recall 0.90, last two correct, once per 30 days | None — provisional default, logged for evaluation |
| Tap blame | 0.6; 0.8 for card-coded matches | None — provisional default, logged for evaluation |
| Control probes | 10 to 20% of picks | Code review |
| Held-miss expiry | 7 days | None — provisional default, logged for evaluation |
| Readiness range | 80% | Practice-systems report |
| Mistake retirement | Two more clean passes on different days | Practice-systems report (convergent practice) |

## Math system

The checker must never accept a wrong answer and must almost never reject a right one, because a false "wrong" corrupts the schedule as badly as a wrong key. It works in layers and keeps "can we read this?" separate from "is it correct?".

**Rendering**

- **MATH-1** KaTeX 0.19.1, bundled with its fonts. Content builds render in strict mode, so any LaTeX that fails fails the build. A MathJax fallback for imported decks with macros KaTeX lacks is not built and moves to Later, because the build-time KaTeX check already rejects unsupported LaTeX in packs.
- **MATH-2** Function plots for cards with a `plot` line, drawn offline by a bundled plotting library (function-plot or JSXGraph). Not built yet; plots ship in 1.0 (M8), because calculus needs graphs.
- **MATH-3** Problem text is Markdown with LaTeX, images and tables.

**Input**

- **MATH-4** A MathLive math field (MIT, bundled): typing `/` makes a fraction, `^` a superscript, `sqrt` a root, with an optional on-screen math keyboard. Its LaTeX is lowered into the app's one plain-text grammar (ADR-0005).
- **MATH-5** Plain-text mode accepts the card format's answer syntax, parsed by the app's own grammar.
- **MATH-6** The "read as" preview re-renders the parsed answer with explicit multiplication. `sinx` gets "Did you mean sin(x)?" and `e^2x` displays as e² times x.
- **MATH-7** Answer-shape helpers: for intervals, sets and points the field offers union, infinity, DNE, none and bracket buttons.

**Parsing**

- **MATH-8** Nothing the student types is ever evaluated as code. MathLive's LaTeX is lowered to the plain syntax, and all input goes through the app's Lark grammar into a hand-written whitelist translator to SymPy (ADR-0005). SymPy's `parse_expr` and `sympify` are banned on user input, because they call `eval` (a 2026 High-severity remote-code flaw, CVE-2026-55585, in a third-party math-verifier package that called parse\_expr). A lint rule and a test enforce the ban.
- **MATH-9** The card defines its symbols and their assumptions (real by default), so the student's x and the key's x are the same symbol. `e` is Euler's number; `i` is the imaginary unit only when the card says so. Interval and inequality answers must declare their variable in vars, and any undeclared letter makes the answer invalid, so "x > 1 and y > 1" can't pass for x > 1.
- **MATH-10** Input limits: 400 characters, nesting depth 40, and caps on exponent size, so no input can hang the checker.

**Checking pipeline**

1. **Shape:** the answer must match the expected type. A mismatch ("expected an interval") uses no attempt.
2. **Exact:** identical canonical forms are correct at once.
3. **Numeric:** both sides are evaluated at 12 points per variable inside the domain, at 30-digit precision, with at least one point in each connected piece. An answer undefined where the key is defined is wrong, except for a hole-only mismatch. When the answer differs from the key only at removable points, it is not marked wrong: a message that costs no attempt says "Your answer is undefined at … where the expected answer isn't; check its form", and the case is logged as its own category. A domain the card declares strict is still enforced, the authoring preview shows hole differences, and the policy is revisited from data. Holes-as-wrong has no production precedent and rejected natural rewrites in probes. This step decides most cases.
4. **Symbolic confirmation:** `simplify(a - b) == 0` runs in a separate worker process that is killed after 2 seconds. It can confirm a match but never overrule a numeric mismatch.
5. **Form** (only when the card sets `form`): factored, expanded, simplified, lowest terms, exact, or decimal places, checked on the unsimplified answer. Simplified means named canonical forms (simplified radicals, rationalized denominators), never a node count, so √8 no longer passes for 2√2.
6. **Verdict:** correct, incorrect, or undecidable. Undecidable falls back to a self-grade and is logged.

| Type | How it is compared |
| --- | --- |
| number | Exact answers stay exact. Decimals accept e-notation and pass within half a unit in the last requested place, or, when the card asks for no rounding, within 1% relative with an absolute floor; `inf`, `-inf` and `DNE` are tokens |
| expression | Numeric sampling on the domain, then symbolic confirmation |
| equation | Left minus right of each must be proportional by a nonzero constant (STACK's ratio test), checked by sampling |
| antiderivative | Derivatives compared by sampling; `+ C` per the card |
| set, list, point, vector, matrix | Element by element with the expression rules; sets ignore order, lists don't |
| interval | Converted to canonical sets with unions merged; endpoints compared exactly; `endpoints: either` relaxes brackets; inequalities accepted when the card declares the variable (MATH-9) |
| choice, truefalse, text | Exact match on the options, or normalized text |
| quantity (1.1) | Converted to SI units; tolerance from `sig-figs` or `tolerance` |

**Grader quality**

- **MATH-11** A golden suite of at least 600 (input, key, verdict) cases at 1.0, covering every type and the known traps: `sinx`, `e^x`, 2ln|x| against ln(x²), the square root of x² against x, cube roots of negatives, interval endpoints, DNE against infinity, equivalent equations and antiderivative constants.
- **MATH-12** Property tests: equivalent rewrites of each key (expanded, factored, rationalized, trig identities) must pass; small perturbations (a coefficient off by one, a flipped sign) must fail; random junk input must never crash the parser.
- **MATH-13** Every key must grade itself correct, and every stored `wrong` answer must grade incorrect: in CI for packs, and at import for user cards.
- **MATH-14** Every "I was right" dispute is reviewed. A confirmed grader miss becomes a golden test before its fix ships.
- **MATH-15** 95% of answers are graded in under 300 ms, with a hard limit of 2 seconds before the verdict becomes undecidable.
- **MATH-16** Calculator and angles. Each card says whether a calculator is allowed (default no; problems from exams are no-calculator), and the study screen shows a small calculator mark when it is. Angles are radians unless the card says degrees; a degrees card shows a "degrees" note and compares its answers in degrees. The calculator flag is one entry of a tools list (MATH-19).
- **MATH-17** (1.0) Worked solutions are checked. The pipeline checks every structured intermediate result in a worked solution, and its final line, against the key, in the cheapest form that works, not only the final answer.
- **MATH-18** (1.0) Answer-type registry. Answer types live in an open registry. An unknown type falls back to self-graded, and each pack lists the types it requires in its manifest, so an older app can say what it can't check.
- **MATH-19** (1.0) Tools. A card's `tools` list generalizes the calculator flag (calculator now; others, such as a graphing tool, later). `calculator: yes` reads as `tools: calculator`.

## Content packs and the skill graph

Course content ships as packs: versioned bundles of skills, cards and media, built from card files by the content pipeline and loaded read-only. Release 1.0 ships the Test pack, the Answer Input Tutorial deck and whatever Calculus I content passes the pilot rule (PACK-11); each later course arrives as its own pack.

**A pack** (`.mepack`, a zip) holds `manifest.json` (ID, title, semantic version, format version, courses, license summary, build date, pipeline version, content hash), `skills.md`, card files, `media/` and `credits.json`. The build compiles each pack into its own read-only database file shipped with the app, and more packs can be imported later.

- **PACK-1** Packs are read-only. The student can suspend, flag or report pack cards, and edits only their own cards.
- **PACK-2** IDs are permanent. A fix adds a revision; a removed card is retired, never deleted, so its history stays valid. A changed answer key is noted in the card's history.
- **PACK-3** Templates are expanded at build time into 50 to 200 verified instances each and shipped as data. Packs never contain executable code.
- **PACK-4** Every card records its provenance: source, creators, license and URL, original path and commit, whether and how it was modified, third-party parts, and any translation or unofficial-solution label. The Credits screen is generated from this.
- **PACK-5** Every card records which verification path it passed.
- **PACK-6** A pack update arrives with a new app version or as an imported `.mepack`. Progress lives in a separate file and is never touched.
- **PACK-7** Distributable by design. The app and its shipped packs must be free to share. The pack builder refuses any card whose license isn't on an allowlist (CC0 and public domain, CC BY, CC BY-SA, CC BY-NC, CC BY-NC-SA, and sources with a written reuse policy that permits it), and refuses cards without provenance.
- **PACK-8** Personal content never ships. Decks the student imports for personal use (for example a private folder of decks) live only in that profile's data folder, are marked personal, and are excluded from every build and from pack export. The build fails if anything from a profile folder is in the bundle.
- **PACK-9** Shipped packs carry their licenses: each pack carries its source's license, one pack per license family, with a compatibility table in the pack builder (Active Calculus is CC BY-SA 4.0, so it can't go into a BY-NC-SA pack); the Credits screen lists every source, and a release checklist covers per-source duties (attribution, modification notes, and the reporting some Japanese universities ask for within a month of publication). AI-written originals are labelled AI-generated and released under CC0 to the extent any rights exist, since purely AI-generated output isn't copyrightable (USCO). The clean-room process gets a qualified review before any public release. Every shipped dependency must allow redistribution; fsrs-rs-python declares no license, so it is replaced or licensed before any public release.
- **PACK-10** Skills list where to learn them: a `learn:` key in the skills file gives open textbook sections, free videos and free websites (title, source, URL, and why it was chosen) for STA-11 and the solution screen. Sources are picked from what students and teachers widely recommend for that subject, using university learning-center resource lists, course pages and community FAQs, never a single search result. Each link is checked to cover that exact skill, and every pack build re-checks that links still resolve. The app never fetches them itself: a link opens in the default browser, and only links that come from pack data can be opened.
- **PACK-11** (1.0) Pilot first. No course is mass-produced until a pilot section has measured tokens per card and the error rate. Templates come first.
- **PACK-12** (1.0) Sampled audit. A pack ships only after an independent audit of a random sample of its cards: 0 errors in 150 bounds the error rate under 2%, and 0 in 300 under 1%. This replaces the three-day study check.
- **PACK-13** (1.0) Seeded-error test. The acceptance pipeline is tested by injecting about 100 plausible wrong keys and reporting the fraction it rejects.
- **PACK-14** (1.0) Updates to studied cards. A pack update that changes a card someone has studied keeps its history: a changed problem becomes a new revision, a removed one is retired, and a card moved to another skill is remapped with its attempts (PACK-2). When a revision changes an answer key, attempts graded under the old key are voided and memory is recomputed from the log (ADR-0013).
- **PACK-15** (1.0) Personal decks beside packs. When a personal deck covers the same skills as a pack, both join that skill's pool. An imported card that duplicates a pack card is flagged in the import preview, never merged silently.
- **PACK-16** (1.0) Reserved card keys (format: mastery-cards 1.1). Per-part `tolerance`, `alternates` (other accepted answers) and a sig-figs mode (off, advise or strict) are reserved now, so later subjects need no format break. Two attempts per instance stays.
- **PACK-17** (1.0) Per-instance attachments. A template instance can carry its own attachments, such as a figure or a data file drawn with its numbers.
- **PACK-18** (1.0) Template checks. The build sweeps each template's instances for isomorphs (the same problem in disguise) and drops them, and the app tracks first-try success per template, so a template whose instances differ in difficulty shows up.

**The skill graph**

- **GRAPH-1** One set of skill nodes with two edge types: prerequisites, which must form a DAG (checked by topological sort and stored without redundant edges), and encompassing edges weighted 0.25, 0.5 or 1.
- **GRAPH-2** Edges can cross courses; Calculus skills require Algebra and Trig skills. A prerequisite whose course has no pack yet has no pool; ENG-6 says how it is handled.
- **GRAPH-3** One skill is one thing a single kind of problem tests: roughly 100 to 300 per course. Math Academy runs about 300 topics per course.
- **GRAPH-4** Every skill has a name, a section, textbook references, its confusable skills, at least one worked example, and a full pool: tier 1 and 2 skills need a template or 20 or more fixed problems; tier 3 needs at least 10; tiers 4 and 5 take what's available. This applies to skills a pack teaches; prerequisites from courses without a pack may have no pool yet (ENG-6).
- **GRAPH-5** The pipeline drafts skills and candidate edges with a model. The student reviews them in order of confidence, and the validator rejects cycles and missing prerequisites.
- **GRAPH-6** Skills in Off sections stay in the graph for error routing and checks.
- **GRAPH-7** Every skill on the published skill list has a one- or two-sentence definition, two example problems, and one or two near-miss examples from its confusable neighbor, so people and AI tools tag consistently. The list and a ready tagging prompt are published with each course.
- **GRAPH-8** (1.1) Shared mistake patterns. Each skill family carries about 20 to 40 shared mistake patterns, coded like known wrong answers, so a miss on a card without its own coded wrong answer can still get a likely cause (ENG-21).

**The content pipeline** lives in the repo's `content-tools/` and never ships. It extracts from structured sources (OpenStax XML, CLP PreTeXt, LaTeX, and Open Problem Library problems rendered seed by seed at build time by a local WeBWorK renderer, which returns every answer in instructor mode), using OCR only for Japanese exams and PDFs. It excludes material the content policy rules out, tags skills and tiers with the procedure below, verifies, deduplicates, and builds the pack. Every key must pass the acceptance rule for its provenance:

| Provenance | Accepted only when |
| --- | --- |
| Template, answer computed in code | A sweep of 1,000 or more seeds passes an independent SymPy route, back-substitution and degenerate-case checks, plus 5 to 10 blind model solves. Then it is frozen |
| Source with an official key | The key matches a blind model solve under the checker, and the problem passes a well-posedness audit |
| Source without a key | A blind solve and an independent code or CAS solve agree, back-substitution passes, and the audit passes |
| AI-original with a checkable answer, including Gaokao- and CSAT-style | The intended answer, a blind solve and a code solve all agree; an adversarial audit passes; a check confirms the full answer set was found |
| AI-original proof or olympiad style | Ships self-graded with a rubric, held back until the student has solved it |
| Translated Japanese exam problem | A blind solve of the English version reproduces the official answer; marked translated, with solutions labeled unofficial |

A disputed problem is dropped, never patched into the pack.

**Tagging with AI.** Pack content and the student's own AI tagging of imported decks follow one procedure, because models pick well from yes/no questions but poorly from a long list (they over-tag):

1. The model solves the problem in numbered steps. If there is a key, its answer must match under the checker. These steps become the step-tagged solution.
2. Candidates are narrowed to the course and chapter: 10 to 15 skills plus "none / new skill".
3. Each step gets exactly one skill. The key steps' skills (at most two) are the main tags; routine steps' skills (at most four) are uses tags.
4. Each tag is confirmed by a yes/no question that includes the near-miss neighbor's definition.
5. Steps 3 and 4 run three to five times. A main tag kept in at least 80% of runs is accepted, 40 to 80% goes to review, and under 40% is dropped.
6. The same pass flags method cues and proposes a tier with a one-line reason.
7. The model, prompt and skill-list versions are stored with every tag.

Before a chapter's tags are trusted, the student spot-checks 30 to 50 problems, weighted toward low-confidence ones; a skill with under 85% precision on main tags gets its definition rewritten and the chapter re-run. Later the app flags likely mis-tags from his results, such as a fast success on a skill confirmed weak or repeated taps on a step whose skill isn't tagged, for review. It never changes tags itself. Routine tagging and yes/no checks can run on a smaller, cheaper model; blind solves that verify answer keys use the strongest one.

**Method cues.** The pipeline finds problems that name their method ("Use L'Hôpital's rule to evaluate...") and stores both versions: the uncued one for reviews, and the cued original for first exposure, cued-twin checks and highlighted find-the-error items. A cue that is part of the answer ("a left Riemann sum with n = 4") is kept and marked required. Problems whose look gives the method away count less toward method-choice skills.

**Known wrong answers.** For each skill the pipeline keeps a short list of common wrong moves, such as dropping the inner derivative or writing (fg)' = f'g', as code that produces the wrong answer for each problem. They become the card's wrong answers with targeted feedback, and the base for find-the-error items.

**First sources for Calculus I.** The CLP-1 problem book (CC BY-NC-SA 4.0, with hints, answers and full solutions; about 237 starred problems come from real UBC exams), MIT OCW 18.01 exams with solutions, APEX Calculus, Active Calculus, OpenStax, and the Open Problem Library without its Pending folder, its textbook-linked folders (WHFreeman, Wiley, UVA-Stew5e) and any problem naming a commercial textbook. Japanese exams from universities that allow reuse without asking: Tokyo, Kyoto, Kyushu, Shinshu, Osaka, Tohoku, Nagoya and Hiroshima. Hokkaido, Kobe, Science Tokyo, Waseda and the Common Test need permission and are skipped. Exam problems are marked no-calculator.

**Original problems from owned problem banks.** Problem banks the student owns, such as bought books and school materials, can inspire original cards that ship, through a clean-room workflow (`docs/prompts/clean-room-decks.md`). One session reads the sources and writes a blueprint of ideas only: topics, problem types, solution steps, difficulty and traps, with no wording, numbers or diagrams. A second session that never sees the sources writes the cards from that blueprint. `content-tools/similarity_check.py` then compares every draft with plain-text copies of the sources and flags any card with 30% or more shared 5-word runs, a 12-word run in common, or all its numbers from one source problem; flagged cards are rewritten from the reason alone until nothing is flagged. The cards then pass the acceptance rule for AI-original problems, and the sources never enter the repo.

## Import, export, profiles and backups

Nothing the student brings in or takes out can damage existing progress: every import is previewed, every risky step is preceded by a backup, and progress lives in its own file.

**Import**

- **IMP-1** Card files, skills files and `.mepack` packs, as defined in the Math Card Import Format.
- **IMP-2** Anki .apkg and .colpkg. The `meta` file names the format: bytes 08 03 mean the newer collection (`collection.anki21b`, zstd-compressed, with a protobuf media map and compressed media files) and 08 02 the older one (`collection.anki21`, JSON media map). Without `meta`, the importer reads `collection.anki21`, then `collection.anki2`. The placeholder `collection.anki2` that modern Anki adds is never read when a newer file is present. zstd data is decompressed as a stream, because Anki's frames don't record their size. Schema 18 note types, fields and templates come from their own tables, read after registering Anki's `unicase` collation and always joined to `notetypes`, since exports carry leftover rows for stock note types. Note types map as the format doc describes.
- **IMP-3** Anki's plain-text export, reading its header lines (#separator, #html, #tags, #columns, #notetype, #deck, and the column headers for note type, deck, tags and GUID). A headerless two-column file becomes Basic flashcards.
- **IMP-4** Optional review history. When cards already carry FSRS memory state (stability and difficulty in the card's data) and the deck has FSRS parameters, those are imported as they are. Otherwise the review log is replayed: cram entries, entries before a reset and manual entries are dropped, and each review is converted to its Anki study day, using the collection's rollover hour (4 AM when an .apkg doesn't carry it), before replay. Without that conversion py-fsrs counts 24-hour periods and gets different stability (9.3 against Anki's 12.65 days in a test).
- **IMP-5** Every import starts as a dry run. The report lists added, updated, unchanged and rejected cards, with file, line and reason, before Import or Cancel. The import itself is one transaction.
- **IMP-6** Imported HTML is sanitized and scripts never run: Anki templates can carry JavaScript, so it is stripped and the page's content security policy blocks the rest. Hint fields are rendered natively. Media file names are normalized (NFC, at most 120 bytes) and kept in a separate folder per import.
- **IMP-7** Imported cards carry an "unverified" mark in the browser, since they did not pass the content pipeline. Study screens don't show it. Keys converted by AI must grade themselves correct at import like any other card, and the student should spot-check a sample before relying on a deck.
- **IMP-8** Anki templates are rendered at import by the app's own renderer, a port of Anki's rules: a field counts as empty when it holds only whitespace, `<br>` or `<div>`; filters chain right to left; `{{FrontSide}}`, special fields and cloze numbering behave as in Anki. Generic Mustache libraries get these wrong. The official `anki` package (AGPL) is used only in development tests, as the reference the renderer must match.
- **IMP-9** (1.0, built) Import limits. Every package is untrusted input (ADR-0015): at most 200,000 entries, a 2 GiB collection, 512 MiB per media file, 8 GiB read in all, and a 1,000-to-1 compression ratio for entries over 1 MiB. Duplicate entries, unsafe media names and bad SHA-1s are refused, no archive name is used as a path, and the collection is opened in memory, read-only, with `trusted_schema` off.
- **IMP-10** (1.0) Imported-deck fidelity. Nested and multi-ordinal clozes render as in Anki, `[latex]` blocks render, and reversed sibling pairs are spaced apart like Anki's siblings.

**Export**

- **EXP-1** The student's own cards and skills export as card files, and re-import unchanged.
- **EXP-2** A whole profile exports as one `.meprofile` file: progress, settings and media.
- **EXP-3** The review log and attempts export as CSV, for fitting FSRS elsewhere or for analysis.
- **EXP-4** An optional daily summary file (date, problems, minutes, retention, forecast), written locally and off by default, is reserved for a future planner-app connector.
- **EXP-5** (1.0) No trapped data. Everything exports in documented open formats (card files for content; CSV and JSON for progress and logs).
- **EXP-6** (1.1) The student's own flashcards export as an Anki `.apkg`.

**Profiles**

- **PRO-1** Anki-style local profiles: each has its own progress file, media and settings, chosen at startup. Content is shared.
- **PRO-2** There are no passwords or accounts.
- **PRO-3** (1.0) A profile can be renamed or deleted. Deleting takes a final backup first and asks for the profile's name to confirm.

**Backups**

- **BAK-1** The progress file is backed up every 30 minutes of use and on close, keeping the last 10, plus 7 daily, 4 weekly and 6 monthly copies.
- **BAK-2** An extra backup is taken before every schema migration, import and pack update.
- **BAK-3** Restoring any backup takes two clicks in the app, after a preview of its date and counts (1.0).
- **BAK-4** Every launch runs an integrity check. If it fails, the app opens a restore screen offering the latest verified backup, and never silently creates a new default profile (1.0).
- **BAK-5** The app warns when the data folder is inside Dropbox, OneDrive, iCloud or a network drive, where SQLite is unsafe. The folder can be moved in Settings.
- **BAK-6** Backups use SQLite's online backup API, so they are consistent even while the app is running. The data folder is \~/Library/Application Support/com.toishi.app, outside iCloud. Time Machine copies of a live database are only crash-consistent, so these backups are the ones to restore from.
- **BAK-7** (1.0) Moving to a new Mac. A backup or profile export restored on the new Mac shows identical progress; the restore drill covers it.

## Browse, edit, stats and settings

These screens let the student inspect and adjust everything the scheduler does, without ever needing to.

**Browser**

- **BRW-1** Search and filter every card by course, section, skill, kind, answer type, tier, source, license, tags, status (new, learning, review, suspended, retired, reported, leech) and verified or not, with full-text search over questions and solutions.
- **BRW-2** Preview any card exactly as studied, including a random variant instance.
- **BRW-3** History for any card or skill: attempts, ratings, FSRS state, due date and current predicted recall.
- **BRW-4** Actions: suspend, flag with a color, report, reset a skill's progress (after confirmation), and move the student's own cards between decks.
- **BRW-5** (1.1) Bulk tools: select many cards to suspend, flag, tag, move or reset at once.

**Editor**

- **EDT-1** Create and edit the student's own cards in a form view or as raw card-file text, both with a live preview.
- **EDT-2** The import validator runs while typing, including the self-grade check and the template test.
- **EDT-3** A searchable skill picker, with an inline "new personal skill" option.
- **EDT-4** Every edit can be undone until the app closes.

**Stats**

- **STA-1** Home: today's problems with projected minutes, exam countdowns, and a forgiving streak (any study keeps it; it holds at most 2 freezes, earning 1 for every 7 days with the daily set done, and a freeze covers a missed day automatically; with no freeze left, the streak survives a missed day if the sets of the next 2 days are both done).
- **STA-2** Forecast: problems and minutes per day for the next 7 and 30 days.
- **STA-3** Retention: success on delayed reviews per course, against desired retention. This, not practice accuracy, is the measure of learning. One line contrasts the two on his own data, such as "92% during learning blocks, 81% on the same skills a week later", because seeing one's own delayed results keeps retrieval practice going.
- **STA-4** Calibration, in a separate Diagnostics view so Stats stays small: predicted against observed recall by bin (ENG-11), plus the shadow partial-credit comparison (ENG-7) and the triage-policy comparison (QUE-6).
- **STA-5** Skill map: one row per section, one cell per skill, showing each skill's Level (Learning, Learned, Exam-level or Mastered) and its Recall, with fading skills marked.
- **STA-6** Exam readiness: the share of in-scope skills predicted at or above target on exam day, the share at Exam-level or above, and the projected exam score range (STA-12).
- **STA-7** Time per day and per course, and a calendar heatmap of study days.
- **STA-8** Mistakes: counts by error type, slip rate, how often tagged sub-skills were confirmed by their checks, current leeches, and weak-spot flags with how often their diagnostic sets confirmed them.
- **STA-9** Speed: each skill's median solve time against its target as a weekly trend line. Never a judgment on a single problem, and worded as "exam-ready pace", not "fast".
- **STA-10** Goals: for each course, the goal, days to the goal date, projected daily load, and whether the goal is on track.
- **STA-11** Weak areas: a plain list of the specific skills holding the student back, gathered from the placement test, confirmed weak spots (ENG-15), leeches, failed prerequisite checks and fading skills. Each entry names the concept in words ("Choosing a limit technique", not a skill ID), says why it is listed ("missed 4 of the last 6, all at the setup step"), shows the prerequisite underneath if that is the real gap, and links where to learn it: the open-textbook section and free videos from the skill's `learn:` list, opened in the browser. Practicing an entry is one click (Focused Practice on that skill).
- **STA-12** Readiness range. The projected exam score shows as an 80% range, never a single number. Practice-test scores sit beside it and are never merged into it. After each real exam the app asks for the score and logs predicted against actual; after two exams in a course it applies a per-course offset. Predictions from a single practice test miss real scores by a few percent of the score scale, so a point estimate overstates what is known.
- **STA-13** Lost-points report. After each practice test, and after each real result entered (LIB-11), a report shows points lost by skill, by cause and by attempt label (QUE-19); "solvable but skipped" items (unanswered with R of 0.8 or more); and the slowest correct items. The "What went wrong?" picker runs on every miss before the report closes, or can be deferred to the next session.
- **STA-14** Mistakes. Every miss becomes a mistake whose state is derived from logged events, never kept as a second schedule; FSRS still writes every due date.
  - Open: missed.
  - Diagnosed: a cause was chosen and its check settled.
  - Retested: a fresh problem on the skill passed on a later day.
  - Retired: two more clean passes on different days, or the skill regains its earlier Level.

  A failed retest flags the mistake "needs reinforcement". The list shows only Open and Diagnosed mistakes by default, so it stays short. Each entry shows the student's answer beside the right one and the step tapped, and can be redone any time as unrated practice; drilling from the list is QUE-20.
- **STA-15** (1.0) Minimal Settings. Settings in 1.0 holds the daily count, vacation mode, Untimed, single-key shortcuts on or off (WCAG 2.1.4), text size up to 200% (WCAG 1.4.4) and the theme override. The rest of the settings table arrives in 1.1.
- **STA-16** (1.0) One count. Home, the session summary and Stats take every count from one computation, so they can never disagree.
- **STA-17** (1.0) Workload preview. The projected daily load for the coming weeks includes the booster load before each exam, so a goal's cost is never understated.
- **STA-18** (1.1) Knowledge over time: a chart of skills at each Level, and their recall, week by week.

**Settings and defaults**

| Setting | Default | Range or options |
| --- | --- | --- |
| Daily problems | 20 | 1 to 200 |
| Daily flashcards | 50 | 0 to 500 |
| New flashcards per day | 20 | 0 to 500 (daily.new\_flashcards) |
| Single-key shortcuts | On | On, Off (WCAG 2.1.4) |
| Minutes cap | Off | 10 to 480 |
| New skills per day | 4 | 0 to 20 |
| Learning phase: correct in a row | Adaptive: 2, or 3 after a miss, 4 for hard skills (ENG-2) | Adaptive, or a fixed 2 to 5 |
| Learning phase: most problems | 8 | 4 to 15 |
| Attempts per problem | 2 | 1 to 3 |
| Hints | On | On, Off |
| Course goal | A, per course | A, B, Keep, or a custom retention from 0.80 to 0.95 |
| Maximum interval | 365 days | 30 to 3,650 days |
| Study day starts | 4:00 AM | any hour |
| Longest wait for a due skill | 7 days | 1 to 30 days |
| Stretch problems | 10% of reviews | 0 to 25% |
| Elite problems | On | On, Off |
| "Too easy" key (Easy rating) | On | On, Off |
| Partial credit | Shadow | Off, Shadow, On |
| Triage policy | Recommended | Recommended, Lowest recall first |
| Leech threshold | 8 lapses (skills, provisional), 8 (flashcards) | 3 to 20 |
| Easy days | None | A load percentage per weekday |
| Time shown after each answer | On | On, Off |
| Break reminder | Every 50 minutes | Off, 25 to 90 minutes |
| Theme | Automatic | Automatic, Day, Night |
| Text size | 18 px | 14 to 36 px (up to 200%) |
| Data folder | \~/Library/Application Support/com.toishi.app | Any local folder |
| Backups | Every 30 minutes and on close | Interval and retention |
| Daily summary file | Off | On, Off |
| Untimed session | Off | On, Off, per session |
| "Still working?" note | After 3 times the target time, at least 5 minutes | 2 to 30 minutes |
| Diagnostic sets | At most 2 a week | 0 to 5 a week |
| Find-the-error problems | 1 in 10 reviews | Off, or 1 in 5 to 1 in 20 |
| Minimum per course | 3 problems or 10% of the count | 0 to 10 problems |
| Mixed check-up | Every 3 weeks | Off, or every 1 to 6 weeks |

## Design and theme

The app follows the light around the student: a warm Day theme in a lit room, a soft Night theme in the dark, and Automatic (the default) switching with the operating system's light or dark setting. Dark text on a light background reads better in a lit room, with better proofreading and smaller pupils in studies by Piepenbrock and colleagues (2013 and 2014; the 2014 Ergonomics study measured the pupils). A dark screen in a dark room avoids glare.

Three rules shape both themes:

- **No pure white and no pure black.** Contrast stays high but not maximal, about 13 to 15 to 1, which avoids the halo some readers see around bright text on black.
- **One accent color.** Everything else is neutral, so the eye goes to the problem.
- **Color is never the only signal.** Correct and incorrect use teal and orange plus a check or cross and a word. The two colours are nearly equal in luminance (about 1.03 to 1), so the symbol and the word carry the meaning.

| Token | Day | Night | Used for |
| --- | --- | --- | --- |
| background | `#F6F4EF` | `#17191C` | Page |
| surface | `#FCFBF8` | `#1F2226` | Problem column and panels |
| border | `#E2DED5` | `#30343A` | Dividers |
| input-border | `#8E8B86` | `#696D73` | Input outlines, at least 3 to 1 |
| text | `#1E2226` | `#E4E1DA` | Main text and math |
| text-muted | `#5C6269` | `#A2A6AD` | Labels, tags, hints |
| accent | `#2F6DB0` | `#7FA8DB` | Focus rings, links, the primary button |
| correct | `#2B7A6F` | `#5DB5A8` | Correct verdicts |
| incorrect | `#B4531B` | `#E08A52` | Incorrect verdicts |
| warning | `#936611` | `#D4A64A` | Notices |
| selection | `#DCE8F6` | `#2A3B52` | Selected text and highlights |

Every text pair must meet WCAG AA (4.5 to 1) and input outlines 3 to 1 against both backgrounds, checked by an automated test (DEV-19).

**Type.** Problem text uses Source Serif 4, which sits naturally beside KaTeX's math; the interface uses Inter. Both are open-licensed and bundled. Problem text is 18 px with 1.6 line height, in a column of at most about 70 characters, with math at 1.05 times the text size. Stats use tabular numbers.

**Layout.** The study screen is one centered column: progress, reason tag and pause button small at the top, the problem in the middle, buttons at the bottom, nothing else. Other screens share a left sidebar: Home, Study, Library, Browse, Stats, Settings. Spacing follows an 8 px grid. Focus mode puts the study screen full screen.

**Long sessions**

- A gentle break reminder every 50 minutes (a setting) suggests standing up and looking at something far away for 20 seconds. It never interrupts a problem.
- The Night theme draws plots in theme colors and dims images slightly.
- For warmer color at night, the app suggests the operating system's own night-light setting once, instead of tinting itself.
- No sounds by default, fades of 150 ms or less, and the OS's reduce-motion setting is respected.

**Accessibility**

- Every action has a key, with visible focus rings.
- Text size runs from 14 to 36 px (200%, WCAG 1.4.4), and math scales with it.
- KaTeX's MathML output lets screen readers read the math; every button has a label.
- macOS's Increase Contrast setting is respected.
- Focus is never hidden: whatever has focus, such as the miss picker, is scrolled into view (WCAG 2.2 Focus Not Obscured). Targets are at least 24 by 24 px, and verdicts are announced through a live region.

## Architecture and data

The app is a thin pywebview shell around one WKWebView, the Safari engine built into macOS, over a Python core that holds all the logic. This is Anki's proven layout without the parts Anki needs only at its scale: Rust, sync and add-ons.

&#91;embedded content: architecture · 4 layers\]

Only the core touches data, and it runs under plain pytest; the interface never calls SQLite or SymPy directly.

| Component | Choice | Why |
| --- | --- | --- |
| Language | Python 3.14, managed with uv | Current bugfix release, supported to 2030; never the system Python or a free-threaded build |
| Interface shell | `pywebview 6.2.1 (BSD-3) over macOS's WKWebView, behind a thin adapter` | No bundled Chromium, so a much smaller app. PySide6 6.12 with QtWebEngine (macOS 14 or later) stays the fallback if the M0 spike finds a blocker |
| Web layer | Svelte 5 and TypeScript, built with Vite at development time and bundled | Small and fast; Anki uses Svelte |
| Math display | KaTeX 0.19.1 (a MathJax fallback is Later) | Fast and fully offline |
| Math input | MathLive 0.111 or later (MIT) | Structured input; its LaTeX is lowered into the app's grammar (ADR-0005); 0.111 fixes WebKit losing the last edit when a card advances |
| Plots | function-plot or JSXGraph, chosen in M8 | Offline function graphs |
| Computer algebra | SymPy 1.14.0 with mpmath | Checking and verification |
| Parsing | Lark | A safe grammar for plain-text answers and card files |
| Scheduler | py-fsrs 6.3.2 (MIT) | FSRS-6 |
| Storage | SQLite from the standard library | Reliable single-file databases |
| Data folders | platformdirs 4.14.2 | \~/Library/Application Support on macOS |
| Anki import | zstandard (streaming) and a small protobuf reader | Reads Anki's newer collection format and media map |
| Units (1.1) | Pint | Unit-aware grading of quantities |
| Packaging | PyInstaller 6.22.3, onedir .app for arm64, ad-hoc signed | Built on the developer's own Mac, so no quarantine and no Gatekeeper prompt; no paid Apple account |
| Quality | pytest, Hypothesis, Playwright (WebKit), import-linter, ruff, mypy | Tests and enforced layer rules, all run locally by one script |
| Memory-model fitting | fsrs-rs-python 0.9.3 | Fits FSRS parameters and simulates workload without PyTorch |

**Storage**

- **DATA-1** Each pack is its own read-only SQLite file (opened read-only, no write journal). Shipped packs sit in the app bundle; imported packs sit in the data folder. All are attached at startup.
- **DATA-2** Each profile has one `user.db` in WAL mode, and every write goes there. Transactions spanning attached databases are not atomic in WAL mode, which is why packs are never written.
- **DATA-3** The schema version lives in `PRAGMA user_version`. Migrations run forward only, after a backup.
- **DATA-4** Problems are referenced by permanent string IDs plus a revision number.
- **DATA-5** The attempt log and review log are append-only.

```sql
-- Pack file (read-only)
pack(id, title, version, format, built_at, content_hash)
course(id, title, ord)
unit(id, course_id, title, ord)
section(id, unit_id, title, ord, textbook_ref)
skill(id, section_id, name, confusable, textbook_ref)
skill_prereq(skill_id, requires_id)
skill_encompass(skill_id, encompassed_id, weight)
card(id, rev, skill_id, kind, tier, answer_type, answer, options, wrong,
     question_md, parts, hints, solution_md, rubric, plot,
     template_id, seed, source, source_url, license, modified, verified, status)
media(name, data)

-- user.db (one per profile)
setting(key, value)
section_state(section_id, state, changed_at)
exam(id, name, at_utc, target_recall, scope)
skill_state(skill_id, fsrs_card, status, lapses, learned_at, mastered_at,
            leech, elo_theta, elo_n)
skill_shadow(skill_id, credited_stability, updated_at)
flashcard_state(card_id, fsrs_card, lapses, suspended)
card_user(card_id, last_seen_utc, times_seen, flag, suspended, reported, redo_due)
attempt(id, at_utc, session_id, card_id, card_rev, skill_id, tier, seed,
        raw_input, parsed, verdict, attempt_count, hints_used, duration_ms,
        confidence, flags, error_tag, check_of, rating, explicit,
        predicted_recall, params_id, triage_policy, app_version)
review_log(id, attempt_id, target_id, rating, at_utc, state_before, state_after)
implicit_credit(id, at_utc, from_skill, to_skill, weight, s_before, s_after, mode)
dispute(id, attempt_id, raw_input, at_utc, resolution)
report(id, card_id, at_utc, reason)
user_card(...same columns as card...)
user_skill(...same columns as skill...)
import_log(id, at_utc, file, summary)
```

**Repository layout**

```text
toishi/
  AGENTS.md        rules every AI agent working here must follow
  docs/            this spec, the card format, decision records
  core/            pure Python: model, storage, scheduler, queue, grader, importers
  app/             pywebview shell, JS bridge, local server, menus
  web/             Svelte and TypeScript interface, built into app/web_dist
  content-tools/   the content pipeline; never shipped
  packs/           sources for the Test pack and the tutorial deck
  tests/           unit, property, golden, simulation, interface, packaging
  scripts/         check.sh, build.sh, spike.sh, backup.sh
  packaging/       PyInstaller spec, icons, the launchd backup job
  spike/qt/        the PySide6 comparison app, M0 only
```

**Engineering rules**

- **ARC-1** `core/` never imports pywebview, PySide6 or any interface code; all of it lives in `app/`. An import-linter contract enforces this.
- **ARC-2** No network: the page is served from a loopback server on 127.0.0.1 with a strict content security policy (its own origin only; no remote scripts, fonts or connections), and a test fails on any outbound request. WKWebView has no request interceptor, so the policy and the test are the guard.
- **ARC-3** Nothing evaluates user input as code (MATH-8).
- **ARC-4** Every dependency is pinned; web assets are vendored with their license files; a third-party license file is generated at build.
- **ARC-5** Each major choice gets a decision record, and AGENTS.md lists the rules, so a later session won't quietly switch to PyQt or a CDN.
- **ARC-6** Grading, imports and queue building run off the interface thread. Bridge calls arrive on their own threads, so the core funnels database writes through one writer. The CAS worker is a separate process, restarted if it hangs.
- **ARC-7** Logs and crash reports stay in local rotating files and are never sent anywhere.
- **ARC-8** Every answer is committed as soon as it is graded, because Cmd+Q can end the process without running exit handlers.
- **ARC-9** All state lives in SQLite. The web view keeps nothing in browser storage, which pywebview on macOS doesn't keep anyway.
- **ARC-10** Release builds run pywebview with debug off (on macOS 26, debug mode pushes the window title over the traffic-light buttons). Cmd-key shortcuts are handled by the native menu, so app actions use plain keys or menu items.
- **ARC-11** (1.0) macOS conventions. Settings… on Cmd-comma; a View menu with Enter Full Screen; Undo Last Answer on its own Cmd-key shortcut that works from the answer box. No Dock badge, and notifications are off by default.
- **ARC-12** (1.0) Bridge hardening (HAZ-4). pywebview 6.2.1 runs underscore methods the page names, so the bridge exposes only an allow-list of methods. Calls are checked for frame and origin; a navigation policy keeps the window on the app's origin, and drop handlers stop dropped files from navigating; `ALLOW_FILE_URLS` is off; the loopback server checks the Host header.
- **ARC-13** (1.0) No student-supplied code ever runs in the core or the web process. Imported content is data only.

**Building, testing and backing up**

- **DEV-1** One command, `./scripts/check.sh`, runs ruff, mypy, import-linter, pytest with Hypothesis and the grader golden suite (fast mode); adds the web build and Playwright interface tests (full mode); and builds the app and runs its `--self-test` (app mode). Playwright's WebKit isn't identical to the Mac's own, so the self-test on the real app is the final gate.
- **DEV-2** Core tests also run in the Linux workspace where the agents work. The Mac build and interface tests run on the Mac. There is no paid CI, and a plain git pre-commit hook runs the fast checks.
- **DEV-3** The code lives in a public GitHub repository (ADR-0022) and a local clone on the Mac, never inside iCloud (iCloud's duplicate files break git). A launchd job writes `git bundle create --all` each night, verifies it, and copies it to iCloud Drive with a dated name, keeping the newest 30; Time Machine covers the rest. A bundle holds only committed work, so agents commit after every task.
- **DEV-4** Agents work from short briefs that point to the relevant spec sections and to any newer ADR that amends them (DEV-17). Critical code (grader, scheduler, storage, importers, queue) is written by the strongest model and checked by a separate agent that didn't write it; routine code and bulk content work use smaller models.

## Quality bar for 1.0

Release 1.0 ships when every criterion below passes, not on a date.

| Test layer | What it proves | Tool |
| --- | --- | --- |
| Unit tests on `core/` | Scheduler adapter, queue, grader, importers and storage each behave as specified | pytest |
| Grader golden suite and property tests | Right answers pass, wrong ones fail, junk input never crashes | pytest, Hypothesis |
| Scheduler simulation | Simulated students with known forgetting curves get sensible due dates, calibration and workload; a simulated month never exceeds the daily count; boosters reach the exam-day target; three courses share a month without one starving; target times and Level behave as specified | pytest |
| Pack checks | Every card renders in KaTeX strict mode, every key grades itself correct, every `wrong` answer fails, every template instance is valid | content build CI |
| Import round trips | Card files export and re-import unchanged; sample Anki decks (old and new formats; Basic, Cloze and custom types; media; history) import correctly | pytest with fixture decks |
| Data safety | Killing the app mid-write never corrupts progress; migrations run forward on copies of real data; backups restore | pytest with fault injection |
| Interface smoke tests | Every screen opens; a full session completes by keyboard alone | Playwright with WebKit, plus the built app's self-test |
| Offline tripwire | Any network request fails the test run | Content security policy, plus a socket guard in tests |
| Packaged-app self-test | The built app opens its data, renders a problem and grades an answer | `--self-test` on every build |
| Performance | Home within 4 s of launch; next problem within 150 ms; grading per MATH-15; queue built within 500 ms at 5,000 skills and 100,000 problems | benchmark tests |
| Accessibility | Every text pair meets 4.5 to 1; every control is reachable by keyboard | automated checks |

**Release criteria for 1.0**

- [ ] Every requirement in this spec is built, or explicitly moved to a later release.
- [ ] Every test layer passes in ./scripts/check.sh on the Mac.
- [ ] No open bug crashes the app, loses data or misgrades an answer.
- [ ] The built app runs offline in a fresh macOS user account.
- [ ] A backup restored into a fresh user account shows identical progress.
- [ ] The release candidate starts only when every Critical requirement is green in the trust report, every listed defect is fixed with its test, and the Mac hand checklist is done.
- [ ] Two weeks of daily use of the release candidate pass without a blocking issue.
- [ ] The user guide covers getting started, the answer syntax, the card format and backups.
- [ ] The Credits screen and third-party license file are generated.
- [ ] The trust report (DEV-11) is green for every Critical requirement, and every hazard at severity 4 or 5 has a named, passing test.

**A content pack ships when**

- [ ] The student has reviewed its skill graph.
- [ ] Every skill meets its pool targets (GRAPH-4).
- [ ] Every card passed the acceptance rule for its provenance.
- [ ] Every pack check passes in the content build.
- [ ] A sample of its AI tags passed the spot check, with main-tag precision of at least 85%.
- [ ] A random sample of its cards passed an independent audit with no errors: 0 in 150 bounds the error rate under 2%, 0 in 300 under 1% (PACK-12).

## Engineering process

Two questions are kept apart. Verification asks whether the app was built right: progress is never lost, a wrong answer is never accepted, and schedules match a reference. Tests can drive these close to zero defects, so their gates are enforced by scripts agents cannot edit. Validation asks whether the student retains more and scores better; one learner's data answers that slowly, about one question per semester.

**Phases.** Each release runs these phases in order. Phase 5 runs continuously from the first day of real use.

| Phase | Done means |
| --- | --- |
| 0 Charter | One page sets verification goals (zero acknowledged answers lost, zero known false accepts, schedules equal to reference vectors) and validation goals (realized retention inside its Wilson interval of target; predicted and actual exam scores logged). Constraints and non-goals are signed off by the owner |
| 1 Specify | Every requirement has an ID; each Critical one also has EARS wording, a risk class, a verification method and a passing test or owner demonstration (DEV-10). Acceptance examples exist before code: grader verdict tables, scheduler golden vectors, 1 to 3-step owner scripts. The hazard table and threat model (DEV-14) are current; key choices have ADRs and stated budgets |
| 2 Foundation | check.sh fast, full and app modes pass on the Mac. A test asserts the database settings. The SQLite version guard (DEV-7), verified backups with a restore drill, migrations from every released schema, and the kill loop (DEV-8) pass |
| 3 Build | Each change follows its class (DEV-5). Acceptance tests come from another session before the builder starts, test protection is enforced (DEV-6), a fresh-context reviewer's findings each ship with a failing test, and each milestone gets a hand test on the real Mac |
| 4 Harden | The stateful property test (DEV-9), the multi-year simulation, mutation runs (DEV-13), security negatives (DEV-14), and the accessibility and usability rounds (DEV-15) pass |
| 5 Validate | Strict-label retention, the exam prediction check, diagnosis quality and one preregistered experiment per semester run as DEV-16 says |
| 6 Release candidate | The built app installs and self-tests in a fresh macOS account; two weeks of daily use pass; the evidence bundle (trace, test, mutation and performance reports, hazard and threat changes, licenses) and a green trust report are ready |
| 7 Operate | Every escaped bug adds a hazard row and a regression test before its fix. Each release reviews dependencies (hash-pinned, pip-audit clean, SBOM stored) and the SQLite version. Crash diagnostics stay local |

**Requirements**

- **DEV-5** Change classes. C0 is docs only. C1 is features and interface, under the usual rules (tests with every change, check.sh). C2 is critical code (grader, rating map, scheduler adapter, queue, storage, importers): C1 plus a review of the hazard rows it touches, a mutation run on the touched code (DEV-13) and an ADR for any design change.
- **DEV-6** Test protection by script. check.sh and the pre-commit hook reject any diff that touches `tests/`, fixtures or golden files unless the commit carries a `Test-Change:` trailer from a verifier session, and they scan `core/` for branches that detect a test run. Agents do edit tests when blocked, and a hook is enforced where an instruction is only advice.
- **DEV-7** SQLite version guard. Startup and tests fail when the bundled SQLite is older than 3.51.3, or than the 3.50.7 and 3.44.6 backports, which fix a WAL-reset corruption bug. The build manifest records the version.
- **DEV-8** Acknowledged-write kill loop. Hundreds of SIGKILLs land during answers, imports and migrations. After each, every acknowledged answer is present, `integrity_check` passes, and stored state equals a replay of the log.
- **DEV-9** Stateful property test. A Hypothesis state machine over answer, undo, import, reopen, crash and clock changes, daylight saving included, holds its invariants over long runs. It is the strongest single test of "no lost progress".
- **DEV-10** Trace. Requirements on grading, scheduling and persistence are Critical. Each Critical requirement is worded in EARS form ("When ..., the app shall ...") and names its verification method: test, simulation, inspection or owner demonstration. Tests name their requirements with a `pytest.mark.req` marker, and a script fails check.sh when a Critical requirement has no passing test.
- **DEV-11** Trust report. check.sh writes a one-page, plain-language report for the owner: green or red for each Critical requirement, open hazards at severity 4 or 5, and any waivers. It lets someone who doesn't read code see what is proven.
- **DEV-12** Audit fixes stay closed. The earlier scheduler audit's six critical fixes are built (ADR-0013, ADR-0014): fitted parameters clamped, new parameters adopted only when they win, memory rebuilt from the log, one clock for training and updates, no Again without evidence, and whole training data. Their acceptance tests are Critical requirements in the trace, so a regression turns the trust report red.
- **DEV-13** Mutation testing (1.0, in M7). mutmut runs on touched code in the grader, rating map, scheduler adapter, storage and importers. Each surviving mutant is killed by a new test or reviewed and recorded as harmless: a test goal, not a score.
- **DEV-14** Threat model. A written threat model with a data-flow diagram and its trust boundaries: imported files and HTML, pack data, the loopback server and the bridge. Each threat has a mitigation and a negative test, including that card content cannot reach `window.pywebview`, that an XSS corpus on imported HTML is neutralized, and that parser payloads and oversized inputs are rejected within limits.
- **DEV-15** Usability and accessibility rounds. Three think-aloud rounds of about five users each; three classmates plus the owner is enough. A round is done when no severe problem recurs for two users, and SUS is reported as a range. A keyboard-only script has no pointer-only step; the app meets WCAG 2.2 AA (with the one waiver recorded in DEV-19), including Focus Not Obscured (2.4.11), 24-px targets (2.5.8) and verdicts in a live region; a VoiceOver pass covers sample math.
- **DEV-16** Validation plan. From the first day of real use: strict-label true retention with Wilson intervals and alarms that account for sample size; predicted against actual score for every real exam (STA-12); and diagnosis quality (check confirmation rate, parked skills, retired mistakes). One preregistered experiment per semester: written down before the semester starts, randomized at the skill level. About 1,100 rated reviews detect only differences of about 6 points, so only large effects can be settled. Two comparisons are added: a held-out scheduler comparison (FSRS against a fixed ladder of intervals) and a crossover against Anki with matched study time. The adaptive learning gate (ENG-2) is the first question. Holding items back from practice stays optional, since it costs a student whose grades matter.
- **DEV-17** (1.0) Precedence. A newer accepted ADR supersedes conflicting spec text until the spec catches up. Each ADR lists the spec IDs it amends, the spec is updated within the same milestone, and briefs name both.
- **DEV-18** (1.0) Differential checks. An independent numeric engine (mpmath) cross-checks SymPy on template keys and grader verdicts, and the FSRS golden vectors come from more than one implementation.
- **DEV-19** (1.0) Accessibility for 1.0. The Day warning and incorrect colours and the input outlines meet contrast (4.5 to 1 and 3 to 1), checked automatically; a real VoiceOver pass runs in the built app; math input is hand-tested with paste, dead keys, a non-US layout and an input method (IME). Chart text alternatives (WCAG 1.1.1, Level A) are deferred to the end of the roadmap by owner decision, so the WCAG 2.2 AA claim for 1.0 carries this one recorded waiver.
- **DEV-20** (1.0) Validation logging from day one: the invalid-input rate by answer type, first-run time and where people drop off, tap lift over chance (ENG-22), and strict outcomes on every attempt. DEV-16 also evaluates the provisional Hard ratings at about 300 rated items.

**Hazard table.** Hazards are ranked by severity (1 to 5) first, never by a multiplied score. Every hazard at severity 4 or 5 needs a named mitigation and a named automated test, whatever its likelihood. Every escaped bug adds a row.

| ID | Hazard | Severity | Likelihood | Mitigation | Detecting test |
| --- | --- | --- | --- | --- | --- |
| HAZ-1 | Lost progress: an acknowledged answer is missing after a crash, quit or power loss | 5 | Low | Each graded answer committed in its own transaction (ARC-8); WAL with full sync; backups (BAK-1 to BAK-6) | Kill loop (DEV-8); stateful property test (DEV-9) |
| HAZ-2 | A wrong answer is accepted as right | 5 | Low | Numeric-first checking that symbolic steps can't overrule; every key and stored wrong answer graded at build and import (MATH-13) | Golden suite and property tests (MATH-11, MATH-12); mutation runs on the grader (DEV-13) |
| HAZ-3 | A schedule is silently wrong: a rating rule, clock or parameter set misstates memory | 5 | Medium | A miss stays a miss (ADR-0014); one clock and guarded fitting (ADR-0013); exam labels never change ratings (QUE-19) | Golden vectors and the cross-implementation replay; rating-map tests; simulation; mutation runs on rating and scheduler code |
| HAZ-4 | Imported content reaches the bridge and triggers app actions | 5 | Low | Sanitized HTML, no scripts, the content security policy (IMP-6, ADR-0017); the bridge allow-list, frame and origin checks (ARC-12) | Negative tests that card content cannot reach `window.pywebview`; the XSS corpus (DEV-14) |
| HAZ-5 | An old SQLite's WAL-reset bug corrupts the database | 5 | Low | A single writer; the version guard (DEV-7) | Version check at startup and in tests; kill loop (DEV-8) |
| HAZ-6 | A failed integrity check silently starts a new, empty profile, so progress looks lost | 5 | Low | The restore screen (BAK-4); verified backups (BAK-1 to BAK-6) | A corrupted-database fixture opens the restore screen and creates no profile |

## Implementation plan

The base app is built in fourteen milestones that front-load the riskiest parts: packaging in M0, the grader in M3, the engine in M4. M0 to M6 are built. On 2026-11-01 the owner chose Calculus I first: 1.0 ships before the end of the fall 2026 semester with M7, M8, the hardening the release criteria need (M11) and the release with the Calculus I pack(s) (M12). The mistakes and exam layer (M9) and the rest of stats and settings (M10) ship in 1.1 right after the semester, and the remaining hardening (M13) follows them. Rows are in build order. Each milestone ends with a short hands-on check by the student, and none starts until the previous one's exit criteria pass.

| Milestone | Status | Builds | Done when |
| --- | --- | --- | --- |
| M0 Foundations | Built | `Local git repo with core/ (no GUI imports), app/, web/, content-tools/, scripts/ and tests/; AGENTS.md rules; decision records; dependencies pinned with uv; check.sh; the nightly backup job. A packaging spike: the same small page (KaTeX, MathLive, a plot) in pywebview and in PySide6 with QtWebEngine, each packaged with PyInstaller, comparing app size, launch time, MathLive typing, Cmd-key handling and offline loading` | pywebview is chosen unless the spike finds a blocker; the chosen build runs offline on the Mac; check.sh runs lint, type checks and tests; a backup bundle restores |
| M1 Data layer | Built | Pack database and `user.db` schemas, ATTACH, migrations, profiles, append-only logs, UTC storage with study-day rollover, backups, restore, integrity check | Migration, backup, restore and fault-injection tests pass; a fixed-clock test replays a full history exactly |
| M2 Card format and import | Built | Card-file and skills-file parser, validator, template expander with the safe evaluator, pack builder, including step-tagged solutions, cued and uncued stems, calculator and angle settings, and the find-the-error and which-method kinds; the Test pack and the Answer Input Tutorial deck. The card format is frozen at the end | Every example in the format doc imports; bad files give exact file-and-line errors; export and re-import round-trip |
| M3 Math system | Built, except plots (M8) and the MathJax fallback (Later) | KaTeX with MathJax fallback, MathLive input, plain-text grammar, whitelist translator, the checking pipeline, the CAS worker process, plots | The golden suite (600 or more cases) and property tests pass; a lint rule and a test prove nothing evaluates user input |
| M4 Learning engine | Built | FSRS adapter, rating map, learning phase, relearning, core band, Elo selection, prerequisite checks, shadow partial credit, goals and exam boosters, target times and the slow-answer rule, Recall and Level, the weak-spot finder, method-choice skills, leeches, calibration logging | Simulated students get sensible intervals and calibration, and no simulated month exceeds the daily count |
| M5 Queue and study screen | Built | Queue builder with triage, fair share across courses and interleaving; study screen with pause and active time, feedback, hints, the step-tagged error picker and flags; find-the-error and which-method items; flashcards and cloze; session summary; Focused Practice, undo and session resume | A full session runs offline by keyboard alone, and every reason tag matches the planner |
| M6 Anki import core | Built; screen in M8 | Anki `.apkg`, `.colpkg` and text import with history, through the app's own template renderer checked against Anki's (ADR-0015) | Fixture decks import correctly; the renderer matches Anki's |
| M7 Verification gates | Next · 1.0 | The hand-test fixes (backlog 1, 3, 4 and 6): no card twice in a study day, the min(N, distinct problems) learning gate, the worked example first, honest confident errors, the picker in view. Test protection (DEV-6); the SQLite version guard, kill loop and stateful property test (DEV-7 to DEV-9); the trace, hazard table and trust report (DEV-10 to DEV-12). Algorithm correctness first: the engine, grader and queue fixes this spec states (test misses at every tier, the 21-day test window, undo after a shown solution, checks under the no-repeat rule, below-band items, passed step checks, time out of ratings, guarded fitting, placement by halving, credit kept in Shadow, the binomial weak-spot test, held-miss expiry, declared variables, canonical simplified forms, removable holes, e-notation and tolerance, the leech threshold), each with a test that fails before its fix; an independent fresh-context review of the scheduler, engine and queue against Anki's code and the reference vectors; mutation testing (DEV-13); differential checks (DEV-18) | The fixes pass core and page tests and a hand test on the Mac; the hook rejects an unmarked test edit; the trace script exits 0 and the trust report is green for every Critical requirement; every listed fix has a test that failed before it; no unreviewed surviving mutant in critical code |
| M8 Onboarding and goals | Planned · 1.0 | Course tree, section states, goals with goal dates, exams with their dates, lengths, problem counts, calculator policy and optional blueprints (LIB-10), projected load, textbook references, the first-run flow with the study plan (LIB-12), placement check, milestones; the Anki import screen with a pre-import backup; the adaptive learning gate and parking (ENG-2) and pace only with an entered exam length (ENG-13); a minimal Weak areas screen with learn links (STA-11), pulled forward from M10; function plots (MATH-2); the minimal Settings screen (STA-15) and macOS menus (ARC-11); in-app restore (BAK-4); open-format export (EXP-5); bridge hardening (ARC-12); imported-deck fidelity (IMP-10); the STEM seams (MATH-18, MATH-19, PACK-16 to PACK-18); the workload preview with boosters (STA-17); validation logging (DEV-20) | A new profile goes from first launch to first session in under 5 minutes; placement stays within 25 questions; a fixture deck imports through the screen; each Weak areas entry opens its learn links and one-click Focused Practice |
| M11 Hardening for 1.0 | Planned · 1.0 | What the 1.0 release criteria need: performance, crash handling, the bridge and XSS negative tests behind HAZ-4 (DEV-14, ARC-12), the accessibility work for 1.0 (DEV-19), the user guide, credits and licenses | Every test layer passes in check.sh on the Mac; every hazard at severity 4 or 5 has a passing test; the user guide and Credits screen exist |
| M12 Release 1.0 | Planned · 1.0 | The app bundle and self-test; whatever Calculus I content passes the pilot rule (PACK-11; content has not started); the existing simple practice tests (an exam date, N exam-tier problems, graded at the end); the release candidate, gated on criteria (aiming for around November 23); two weeks of daily use; the evidence bundle and trust report; 1.0 around December 7 | Every 1.0 release criterion passes, and every Calculus I pack passes the content-pack checklist |
| M9 Mistakes and exams | Planned · 1.1 | The mistakes list and its lifecycle (STA-14) and drilling from it (QUE-20); the practice-test ladder (QUE-18), attempt labels (QUE-19), the lost-points report (STA-13), real results (LIB-11), the readiness range (STA-12) and exam-weight priority (ENG-17); paper mock exams (QUE-21), retest papers (QUE-22) and rubric items (LIB-13); shared mistake patterns (GRAPH-8) | A simulated exam cycle builds blueprint tests that cover every skill before repeating one, labels every attempt, rates every test miss Again, retires mistakes only by the logged rule, and logs predicted against actual scores |
| M10 Stats and settings | Planned · 1.1 | Browser and editor with live validation; dashboard with Recall, Level, speed, goal and calibration views; the return-from-break flow (QUE-17); the forgiving streak and own-data contrast (STA-1, STA-3); mixing and form logging (ENG-18, ENG-5); the rest of the settings with their defaults; break reminder; Pass/Fail and Not now flashcards (QUE-26, QUE-27); \`.apkg\` export (EXP-6); browser bulk tools (BRW-5); the outside-help flag (QUE-28); knowledge over time (STA-18). Weak areas and the minimal Settings moved to M8 | Every setting changes behavior as specified; edits validate live and exports round-trip; contrast and keyboard checks pass |
| M13 Hardening for 1.x | Planned · after 1.1 | The rest of the threat model (DEV-14), usability and accessibility rounds (DEV-15), the validation plan (DEV-16) | Every threat has a passing negative test; three usability rounds are done |

Because the card format freezes at the end of M2, Calculus I content can be built from then on, in parallel. It has not started; the pilot rule (PACK-11) comes first, and 1.0 carries what passes it (M12).

## Release timeline

1.0 ships before the end of the fall 2026 semester with whatever Calculus I content passes the pilot rule, and 1.1 follows right after the semester with the full exam layer and the rest of stats and settings. Then come further courses in a typical engineering order, with the earlier courses alongside, and a planner-app connector last.

&#91;embedded content: release roadmap · 8 phases, 3 gates\]


The Calculus I timing is tight. Shipping 1.0 around December 7 needs a release candidate by about November 23, because 1.0 requires two weeks of daily use. Content work could start once the card format froze at the end of M2, but it has not started, and the base app comes first. If 1.0 lands after December 9, the chapters 2 and 3 pack may go first (see Risks and open decisions). The app keeps improving through 1.x releases throughout, and every pack must pass the content-pack checklist under Quality bar.

**Decided 2026-11-01: Calculus I first.** 1.0 ships before the semester ends with the verification gates (M7), onboarding and goals with the Anki import screen (M8), a minimal Weak areas screen, the Calculus I content that passes the pilot rule, the existing simple practice tests, and the hardening the release criteria need (M11, M12). The dates above stay but are AT RISK: content has not started, the base app comes first, and the pilot rule (PACK-11) applies before any course is mass-produced. For the end of the fall 2026 semester, the realistic support is imported Anki decks plus pilot sections. The dates are to be re-planned with the owner. The release candidate is gated on criteria, not the date: every Critical requirement green in the trust report, every listed defect fixed with its test, and the Mac hand checklist done. The Calculus I Chapter 4 pilot pack may ship as its own release. The full exam layer (M9) and the rest of stats and settings (M10) ship in 1.1 right after the semester, so they help from the next exam cycle on.

## Later

These come after the must and should items. Each needs its own go-ahead before it is built.

- **Lighter feedback on sure answers.** On stable skills, a sure, on-target answer gets a one-line confirmation with the full solution one key away. Full solutions stay after misses, unsure answers and on skills with stability under 30 days. "Find your own error first" only as an in-app experiment.
- **Fluency sprints.** Opt-in 2 to 4 minute typed sprints on decks marked "fact": at most 18 cards, only cards answered right untimed twice. A deck stops being offered once its median time stops falling over 3 sprints. Sprints never change FSRS ratings.
- **Prerequisite pre-check.** Before a stretch or exam-tier problem, any of its step skills with recall under 0.80 gets its review at least 3 items earlier.
- **Personal traps.** When the same coded wrong answer fires on 2 or more problems of a skill within 30 days, the app flags a trap, shows a one-line contrast on the next solution, and prefers find-the-error items built from that misconception.
- **"Ran out of time" and a note to self.** A picker cause in timed tests only, feeding Level's pace evidence and never FSRS, and an optional one-line note shown above the next problem on that skill.
- **Worry writing.** An opt-in 10-minute writing prompt before a timed full test and on the evening before a real exam, plus one reappraisal line on the countdown. The app never claims stress inoculation.
- **Chinese interface and content for gaokao users.** A Chinese interface and packs for gaokao candidates. It needs translation and a check of which past papers may be redistributed.
- **Distribution.** Signing, notarization, licenses, REUSE/SPDX labels and an SBOM, settled by the distribution decision under Risks and open decisions, before anyone else installs the app.
- **Concept sections ("Learn"), at the end of the roadmap.** Short textbook-like sections for each concept, after the practice core is done. Accuracy is the overriding requirement, because even small errors could do real harm:
  - Research first what makes the best textbooks effective (structure, worked examples, visuals, misconceptions, length) and turn it into a written style guide.
  - Original text, or adapted CC BY material with attribution; never copied from commercial books.
  - Every definition, theorem and claim is checked against at least two reputable sources; every formula, worked example and graph is machine-checked (SymPy, the pack builder); an independent fresh-context reviewer hunts errors; a qualified human reviewer signs off before shipping.
  - Versioned, with an in-app "report an error" button and a public errata list.
  - Sections link to the skills they cover; practice stays the core, and learn links (PACK-10) keep pointing to outside sources too.
- **Guided step-by-step redo** after a miss, only if data shows the same misses repeating.
- **MathJax fallback** for imported decks with macros KaTeX lacks.
- **Chart text alternatives** (WCAG 1.1.1), at the very end of the roadmap.
- **Contribution tiers.** Packs marked Official, Reviewed, Unreviewed or Personal, with a pack linter.
- **Order-block (Parsons) items**: put the given steps of a solution in order.

## Risks and open decisions

The biggest risks are an unproven scheduling model and a grader that rejects right answers; both are handled by measuring rather than assuming. Risks are ranked by severity, from 1 (an annoyance) to 5 (lost progress or a wrong result the student can't see); product hazards at severity 4 or 5 also sit in the hazard table under Engineering process.

| Risk | Severity | Effect | Mitigation | Detecting test |
| --- | --- | --- | --- | --- |
| A wrong key slips through | 5 | The student learns something false | Acceptance by provenance, the report button that hides a card at once, a sampled audit before each pack ships (PACK-12) | Pack checks: every key grades itself correct and every `wrong` answer fails (MATH-13) |
| Code lost before it reaches the Mac | 4 | Lost work | A git bundle sent after every milestone, the repo on the Mac once a folder is linked, then a nightly bundle to iCloud Drive and Time Machine | The nightly job verifies each bundle |
| FSRS fits skills poorly | 4 | Reviews come too early or too late | Calibration logging, core-band gating, guarded refits (ADR-0013), an adapter to swap models | Calibration and held-out log loss (DEV-16); scheduler simulation |
| The grader rejects right answers | 4 | Lost trust and a corrupted schedule | Numeric-first checking, the "read as" preview, the dispute button, a growing golden suite | Golden suite and property tests; each confirmed dispute becomes a golden test (MATH-14) |
| The exam layer bends grading | 4 | Mock results turn misses into passes and skew every later fit | Labels never change ratings; a test miss is Again (QUE-19, ADR-0014) | A practice-test miss writes Again whatever its label |
| Small pools re-serve problems | 4 | Retrieval turns into recognition, mostly in imported and personal decks | No card twice in a study day; the min(N, distinct problems) gate; small pools flagged (ENG-2, ENG-5) | Queue tests over 1- and 2-problem pools |
| Partial credit lets skills fade unseen | 4 | Forgetting without reviews | Shadow mode until calibration supports it | The held-out comparison that must pass before credit turns on (ENG-7) |
| AI-written code drifts or weakens tests | 4 | Inconsistent architecture; checks that no longer check | AGENTS.md rules, an import-linter contract, decision records, test protection by hook (DEV-6) | The hook and import-linter in check.sh; mutation runs (DEV-13) |
| AI tags are wrong | 4 | Misses are routed to the wrong skill | Solve, step-tag and verify; repeated runs; spot checks per chapter; mis-tag flags from his results | The per-chapter spot check (85% main-tag precision) |
| The web view or packaging breaks | 4 | A broken app, or MathLive misbehaving in WebKit | M0 spike comparing pywebview and QtWebEngine; pinned versions behind an adapter (pywebview has had no release since April 2026); a self-test on every build | The built app's `--self-test`; Playwright WebKit tests |
| Time before the end of the fall 2026 semester | 3 | Calculus I packs land too late to help | Calculus I first (decided 2026-11-01): 1.0 holds only M7, M8, Weak areas, the packs, simple practice tests and the release hardening, and the exam layer waits for 1.1; content work runs in parallel since M2; the release candidate is tested with Chapter 4 to 6 content | None automated: the release candidate date (about November 23) |
| Scope keeps growing | 3 | 1.0 never ships | Fixed 1.0 scope; every new idea goes to a backlog or the Later list | None automated: the milestone gates |
| Courses compete for one day | 3 | One course starves | Fair share with floors, carry-over and an overload proposal (QUE-11 to QUE-13) | Simulation: three courses share a month without one starving |
| Self-diagnosis is unreliable | 3 | The wrong skill gets blamed | Taps count as evidence, a check confirms each, the confirmation rate is tracked, and taps count for less if it stays low | Diagnosis tests; the confirmation rate in stats (STA-8) |
| Speed rules feel punishing | 3 | Studying feels like a timed test | Speed ignored while learning, no countdown, time shown only after answering, time never changes a rating, pace only with an entered exam length, an Untimed switch | Level tests with and without an exam length; usability rounds (DEV-15) |
| Anki decks vary widely | 3 | Some import imperfectly | Fixture decks for common types; templates rendered at import; plain front and back as a fallback | Fixture-deck import tests; renderer parity with Anki |
| The app is shared someday | 3 | License duties: attribution, NonCommercial, ShareAlike, Japanese reports | Store provenance per card now; the license allowlist (PACK-7); decide before any public release | The pack builder's license check |
| Security prompts on a self-built app | 2 | An alarming first launch | Built on the developer's own Mac, the ad-hoc-signed app has no quarantine flag and opens without a prompt; never edit files inside the built app; sign and notarize only if ever published | Clean-account install in the release candidate |

| Open decision | Options | Recommendation | Needed by |
| --- | --- | --- | --- |
| Release dates | Keep a release candidate around November 23 and 1.0 around December 7, or move them | AT RISK: content has not started and the base app comes first; to re-plan with the owner (Release timeline) | Now |
| Release timeline | Exam layer in 1.0, likely after the end of the fall 2026 semester; or Calculus I first, with the exam layer in 1.1 | Decided 2026-11-01: Calculus I first; 1.0 before the semester ends, 1.1 right after it (Release timeline) | Done |
| Reach beyond the Mac | Mac only; an offline web app through Pyodide; Windows through pywebview and WebView2 | Owner's choice; spike Pyodide before deciding | Before 1.1 |
| Signing and distribution | The ad-hoc-signed build for the developer's own Mac; a $99-a-year Developer ID with notarization; an unsigned build opened with "Open Anyway"; the Microsoft Store, which is free, for a Windows build | Keep ad-hoc while only he uses it; one ADR before anyone else installs it, with pip-audit and an SBOM | Before anyone else installs it |
| fsrs-rs-python license | Get a license from upstream, replace the package, or keep the app personal | Settle before any public release (ENG-12, PACK-9) | Before any public release |
| Source hosting | Public source hosting, or "no GitHub" as before | Decided 2026-11-02: open source on GitHub as Toishi, GPL-3.0-or-later, fresh public history (ADR-0022) | Done |
| App and pack licenses | A license for the app; pack licenses per source family (PACK-9) | Owner's choice, with the builder's compatibility table | Before any public release |
| Sustainability and succession | Who keeps the app and packs going if the owner stops | Owner's choice | Before any public release |
| Chinese interface and notation layer | When to start; requirements R1 to R14 are in the docs/research notes | Owner's choice | Owner |
| Operating system | Mac only | Decided | Done |
| Where the code lives and builds | A home computer, this chat's workspace, or GitHub | Decided: a public GitHub repository (ADR-0022), a local clone on the Mac that builds it, a nightly bundle to iCloud Drive, Time Machine | Done |
| App name | "Toishi" is a working name | Owner's choice | Before 1.0 |
| Learning-phase threshold | 2 or 3 correct in a row, or adaptive | Decided: adaptive (ENG-2), tested by the first semester experiment (DEV-16) | Done |
| Partial credit for Off sections | Yes or no | Yes, in shadow mode | M4 |
| The "too easy" key | Keep it, or rate only Again, Hard and Good | Keep it; it is rarely used | M4 |
| Publishing the app someday | No, or later | Store provenance now; decide before sharing | Before any release to others |
| Calculus I pack order if 1.0 slips | Chapters 4 to 6 first, or 2 and 3 first | Chapters 4 to 6 first as planned; swap if 1.0 lands after December 9 | At 1.0 |
| The macOS version | 14 or later, or older | Needed to confirm the toolchain: PySide6 6.12 and Playwright's WebKit need macOS 14 or later | Start of M0 |
| Interface shell | pywebview, or PySide6 with QtWebEngine | pywebview, unless the M0 spike finds a blocker | End of M0 |
| Speed and goal constants | The starting guesses in ENG-13, QUE-11 and the goal presets (ENG-24) | Recalibrate from his own logs after four weeks of use | After 1.0 |
| Practice-test window | 14 or 21 days before an exam | 21, chosen by the coordinator to match the booster window (ENG-8); the owner's choice | Before 1.0 |
| Calculus I pilot in 1.0 | Ship a pilot section inside 1.0, or the Chapter 4 pilot pack as its own release | Owner's choice | Before the release candidate |
