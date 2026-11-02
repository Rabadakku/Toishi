# Split Recall From Level, Build on WebKit

This round keeps most of the engine's design. It changes how five signals are read, and it replaces the desktop shell. **Speed should change an FSRS grade only when a correct answer is both more than twice the learner's own median time and slower than the target.** The design's "OR" rule would turn nearly every early-semester review into Hard and shrink every stability gain. Exam pace belongs instead to a separate four-step **Level**, shown next to FSRS **Recall** and never merged with it. The clock should pause on window blur, screen lock and sleep, never on keyboard inactivity, because the work happens on paper. With one learner, three more rules follow. Item difficulty must be fixed from tier priors, because Elo needs about 100 students to calibrate an item. A wrong answer's cause is only a hypothesis until a one-problem probe confirms it. And AI skill tags must be tied to individual solution steps and verified one at a time, because GPT-4 choosing freely from a standards list matched the gold tag set only **4.8%** of the time. On the build side, the recommended stack changes in four ways:

- The shell moves from PySide6/QtWebEngine to **pywebview 6.2.1 on the system WKWebView**, with a Svelte UI.
- Python moves from 3.12/3.13 to **3.14**.
- GitHub CI gives way to one `make check` run on the Mac.
- Backups become a nightly launchd job that writes a verified git bundle and a `VACUUM INTO` snapshot to iCloud Drive.

The FSRS optimizer no longer needs PyTorch. **fsrs-rs-python 0.9.3**, a 1.3 MB wheel, fits FSRS-6 parameters, rebuilds Anki's exact memory states and computes optimal retention. Anki imports hide three silent traps. Every modern package contains a dummy `collection.anki2`. Its zstd frames must be decoded as a stream. And py-fsrs replays of Anki history disagree with Anki on stability (9.30 versus 12.65 in one test) unless Anki day numbers are mapped first. On content, five more Japanese universities permit reuse without prior approval. The Common Test and Science Tokyo require an application first. The WeBWorK renderer is confirmed to return answer keys. CLP-1's starred UBC exam problems and MIT OCW exams cover Calc I well. Calculus-based physics is adequate, and general chemistry remains thin.

## Fifteen earlier positions move, and one conflict stays open

The table lists every place where this round reverses, refines or corrects the earlier report. Later sections give the evidence. "Researcher's proposal" marks designs the notes put forward without a source testing them.

| Topic | Earlier report | This round | Change |
|---|---|---|---|
| Desktop shell | PySide6 6.12 + QtWebEngine (249.8 MB wheel), QWebChannel bridge, custom URL scheme | pywebview 6.2.1 on system WKWebView; Svelte 5 UI served by pywebview's loopback server under a strict CSP; PySide6 kept as a fallback behind a one-module shell adapter | Reversed |
| Python | 3.12 or 3.13 | 3.14, managed by uv | Reversed |
| Build and test | GitHub Actions on Windows and macOS runners; OS undecided | Mac-only; `make check` plus a git hook on the Mac; a Linux sandbox runs everything except the Cocoa shell | Reversed |
| Data folder and backups | `platformdirs.user_data_dir`; Anki-style rolling backups | `~/Library/Application Support/<bundle-id>/`; daily `VACUUM INTO` snapshot; nightly verified git bundle to iCloud Drive via launchd; never the live DB or repo in iCloud | Refined |
| FSRS optimizer | py-fsrs optimizer needs PyTorch; keep it out of the build; re-fit after 512 reviews | fsrs-rs-python 0.9.3 (no Python dependencies) in the default build; fits w0–w3 from 8 items, all 21 parameters from 64 | Reversed |
| Optimal retention | Compute a time-aware optimum later | `optimal_retention` exists, but returns 0.70 with flashcard costs; feed it the app's own durations | Refined |
| Slow correct answers | Design rule: Hard if > 2× median OR past exam pace | Hard only if > 2× personal median AND past target; exam pace feeds Level, not FSRS | Refined |
| Timing | Log duration per attempt | Pause on blur, lock and sleep, never on input idle; "Still working?" prompt; per-attempt cap; log-medians; solve time separated from entry time | Refined |
| Problem difficulty | Elo picks problems; tiers carry difficulty; misses at P < 0.5 produce no FSRS event | Item difficulty fixed per tier; Elo updates only the learner; misses at P < 0.35 are "above level" and get at most Hard if a probe passes | Refined |
| Mastery display | One mastery figure from today's R; Mastered = ~3 spaced successes plus a stability threshold | Two numbers: Recall (R now and on exam day) and Level (four evidence-based steps that never decay with time alone) | Refined |
| Exam dates | Pull exam skills forward; review 5–10 days before a test a month away | Desired retention 0.90 day to day; a booster brings each in-scope skill to R ≥ 0.95 on exam day within a window of about 0.40·S′; 0.80 afterward; no interval caps | Refined |
| Sub-skill diagnosis | The user tags the broken sub-skill; a quick check confirms it | Tap the first differing step on a step-labeled solution; split blame 0.6/0.4; a probe confirms; a "cued twin" probe separates method choice from execution | Refined |
| AI tagging | Haiku batch-tags against a cached taxonomy (~$0.00003 per problem) | Solve → narrow candidates → tag each step → verify each tag yes/no → 3–5 runs for confidence → per-chapter spot checks | Reversed |
| WeBWorK tolerance | 0.001 relative (wiki) | MathObjects source default is 1E-4 relative | Corrected |
| Japanese exams | Tokyo, Kyoto, Kyushu, Shinshu (plus Meiji, Chuo); Common Test not cleared | Adds Osaka, Tohoku, Nagoya, Hiroshima and Hitotsubashi; Common Test and Science Tokyo need an application; Waseda requires your own permission clearance | Expanded |
| Backlog order | Descending retrievability with guards | Unchanged. This round's per-course allocation proposal sorts lowest-R first, with no new evidence | Conflict |

The conflict needs a ruling. The earlier report's descending-retrievability default rested on specific evidence: Anki 24.11 added the sort because simulations favored it under a backlog ([Anki 24.11 notes](https://newreleases.io/project/github/ankitects/anki/release/24.11)), and a simulation by FSRS's author ranked it second only to ascending difficulty when the daily count was limited ([Anki forum](https://forums.ankiweb.net/t/ordering-request-reverse-relative-overdueness/50051)). This round's multi-course proposal cites only the manual's description of "relative overdueness," which shows first the cards "you're more likely to have forgotten" ([Anki manual](https://docs.ankiweb.net/deck-options.html)). That is a description of the option, not a recommendation. So the pluggable triage policy should keep descending R as its default inside each course's share. Lowest-R-first is a logged alternative to compare against the user's own data.

## Speed changes a grade only when it is slow for you

### Response time is a real but small memory signal

Research systems do use response time on correct answers as a measure of memory strength. Kellman's ARTS scheduler builds log(RT) into each item's priority. Its authors call RT "at least a reasonable proxy for learning strength" and treat RT on wrong answers as uninformative. On a one-week delayed test, ARTS scored 0.42 versus 0.31 for a fixed expanding schedule ([Mettler, Massey & Kellman 2016](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/mettler_massey_kellman_2016.pdf)). In van Rijn and Sense's adaptive fact learner, a response much slower than predicted raises the item's estimated forgetting rate. The rate estimated within a session explained **62.4%** of the variance in 3-day recall ([Sense et al. 2018](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2018.00112/pdf)). Math Academy goes furthest: it "will immediately assign review tasks on topics the student has answered incorrectly **or exceeded the time limit**" ([Math Academy FAQ](https://WWW.MATHACADEMY.COM/faq)). The size of the signal is the caution. Adding a learner's running median correct RT to an accuracy model raised cross-validated R² by only **0.001–0.012** ([EDM 2023](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-short-papers.22/index.html)). Every study used items lasting seconds, not multi-minute calculus problems. FSRS itself ignores review time ([Anki forum](https://forums.ankiweb.net/t/does-anki-take-into-account-average-and-total-time-for-each-card-for-scheduling/70714)). No benchmark has tested whether time-assigned Hard improves its predictions.

The useful signal is slowness relative to the learner's **own** baseline, not slowness against exam pace. Missing exam pace measures a fluency shortfall, not forgetting, and FSRS's optimizer assumes grades reflect memory. Hard is mild: it multiplies the stability *increase* by w15 < 1, so the skill still grows rather than resets ([awesome-fsrs wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)). That makes it the right grade for a struggling but successful retrieval. The rule below is the researcher's proposal:

```text
wrong on first submission                                     → Again
correct, ln(t) − median(ln t over last 10–20 correct, same skill × tier) > ln 2
         AND t > T_target                                     → Hard
correct, t < 0.5 × T_target, tier ≥ skill's current tier      → Easy (optional)
otherwise                                                     → Good
```

The **AND** is the important change. Early in a semester the student is slower than exam pace on almost everything. Under the OR rule, nearly every review would become Hard. A smaller w15 would then cut every stability gain, and workload would balloon exactly when the student is weakest. The researcher adds several guard rails:

- Apply the rule only after at least 5 correct samples exist for that skill and tier; use a tier prior until then.
- Use medians of log-times, because response times are right-skewed.
- Build the baseline from correct answers only, over a frozen window of 10–20, so it tightens slowly.
- Raise the factor to about 2.5× when R at review time was below 0.85.

The last guard matters because harder *successful* retrievals after long gaps produce better learning ([Pyc & Rawson via Matuschak](https://notes.andymatuschak.org/z5zckzyAM1DwEQqt94qMpsd)). A slow answer at low R is expected, not alarming. Whatever rule assigns Hard must stay fixed over time, since the optimizer fits w15 from what Hard means in the data. Store raw active time with every review so grades can be recomputed if the rule changes. Later, compare optimizer log-loss with and without time-assigned Hard on the user's own logs.

### The clock must survive paper work

Research systems handle timing with blunt tools. Anki caps answer time at 60 seconds by default ([Anki manual](https://docs.ankiweb.net/deck-options.html)). The EDM 2023 study winsorized correct RTs at the 95th percentile and used running medians ([EDM 2023](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-short-papers.22/index.html)). Kellman's algebra module used a 30-second timeout and a mean over a window of correct answers ([Kellman et al. 2008](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf)). For a paper-and-pencil app, the main danger is pausing the clock during legitimate work, when there is no keyboard or mouse input at all. Outliers are a smaller problem.

The researcher's proposed state machine works as follows:

- The timer runs while the problem is displayed and the window is frontmost.
- It pauses on window blur, app switch, screen lock, sleep or the pause button. While paused, the problem is blurred so the pause can't be used as extra thinking time.
- It never pauses on input inactivity alone. After `max(3 × T_target, 5 min)` without input, a non-modal "Still working?" prompt appears. If nobody answers within 60 seconds, the recorded time is trimmed back to when the prompt appeared, and the clock pauses.
- Each attempt is capped at `max(4 × T_target, 3 min)`, with an absolute ceiling of 20–30 minutes. Both the raw and capped times are stored.

The researcher's proposal also separates two kinds of time:

- **Solve time** runs from display to the first keystroke in the answer field.
- **Entry time** runs from that keystroke to submit.

Speed criteria then use solve time plus `min(entry time, 5 s + 0.3 s per expected answer character)`, so slow math-syntax typing never counts as slow thinking. No data on math-entry overhead exists, so that allowance must be calibrated from the user's own logs. The FSRS grade comes from the first submission. Three kinds of attempt stay out of speed baselines: those with a pause longer than 2 minutes, the first attempt after waking from sleep, and attempts where hints were opened. One implementation detail matters here. pywebview documents `loaded`, `closing`, `closed`, `resized`, `moved` and `request_sent` window events but no focus event ([pywebview API](https://pywebview.flowrl.com/api/)). Blur and sleep detection therefore has to come from the page's own focus events or a small PyObjC hook, and it needs a smoke test.

### Targets come from exam pacing, and time appears only after the answer

The anti-timing critique is narrower than it sounds. NCTM's 2023 position statement says "timed tests do not assess fluency" and should be avoided, but it is aimed mainly at K–8 basic facts ([NCTM](https://nctm.org/Standards-and-Positions/Position-Statements/Procedural-Fluency-in-Mathematics)). Boaler's claim that timed tests cause math anxiety rests largely on correlational studies of children aged 6–9 ([Boaler](https://www.youcubed.org/wp-content/uploads/2017/03/nctm-timed-tests.pdf)). Math Academy's Skycak proposes the sequence the design already follows: understand the concept, practice **untimed until consistent**, then practice timed. He warns that timing too early "mainly causes stress" ([Skycak](https://www.justinmath.com/fast-correct-answers-do-matter-in-mathematics/)). Fluency gains do last. In Kellman's algebra module, response times fell about 29% by the post-test and 36% by a 3-week delayed test, and "solving-time gains were preserved" ([Kellman et al. 2008](https://kellmanlab.psych.ucla.edu/wp-content/uploads/sites/357/2025/09/kellman_et_al_2008.pdf)). No controlled study shows that timed practice improves timed *college calculus* exam scores beyond untimed practice. Speed goals rest on indirect evidence.

The researcher proposes this target, computed once a skill is Learned:

```text
T_target = max(T_floor(tier), min(T_exam(tier), T_personal))
```

The three terms are:

- `T_exam` is 85% of the exam's minutes divided by its total point weight, times the typical problem's share. Single-skill practice items get a fraction of a full exam problem: tiers 1–2 about 0.25–0.4, tiers 3–4 about 0.5–0.8, tier 5 about 1.0.
- `T_personal` is 0.7 × the median solve time of the first 5 correct attempts after Learned. That 30% improvement matches Kellman's observed drops.
- `T_floor` is 20, 40, 60, 90 and 120 seconds for tiers 1–5.

`T_personal` updates at most weekly and tightens by no more than 10% per update. "At target speed" means the median of the last 3 correct attempts at exam tier, spread over at least 2 days, is at or under `T_target`. No single attempt decides it. Five feedback rules follow:

- No countdown is visible during a problem. Elapsed time appears only after submission, as "4:10 · target 5:00."
- A weekly trend line shows median time per skill.
- A slow correct answer always displays as **correct**; any Hard is internal.
- A per-session "untimed" switch, like Math Academy's accommodations ([How It Works](https://mathacademy.com/how-it-works)), turns off both the Hard rule and Level timing for that session.
- The wording stays about "exam-ready pace," never about being fast or smart.

## Recall and Level answer different questions, and goals set both

### A four-step Level that only evidence can lower

Performance during practice is an unreliable index of durable learning ([Soderstrom & Bjork 2015](https://pubmed.ncbi.nlm.nih.gov/25910388/)). Major products reserve their top level for success shown later, in an unprompted mixed check. ALEKS defines "Mastered" through Knowledge Checks and demotes topics missed there ([McGraw Hill](https://www.mheducation.com/support/aleks-support-center/knowledge/why-did-my-number-of-mastered-or-learned-topics-go-down-after-a-knowledge-check.html)). Its "mastered" means the student can "recognize it without having it pointed out" ([UCSC on ALEKS](https://mathcoach.sites-test.ucsc.edu/success/learned_and_mastered)). Khan Academy's Mastery Challenges ask two questions per skill: two correct raise the level, two wrong lower it ([Khan Academy](https://support.khanacademy.org/hc/en-us/articles/360037494231)). Within-session criteria don't guarantee retention. Even with ARTS's strict rule (5 of 5 correct, all under 7 seconds), accuracy gains fell from 0.85 immediately to 0.52 a week later ([Mettler et al. 2020](https://cognitivesciencesociety.org/cogsci20/papers/0138/0138.pdf)).

That evidence supports the design's ladder and gives it explicit rules. The table is the researcher's proposal.

| Level | Reached when | Lost when |
|---|---|---|
| Learning | Started, Learned not yet met | — |
| Learned | 2 consecutive correct in a session at tier ≥ 2, no solution viewed; speed ignored | Any miss returns the skill to Learning |
| Exam-level | Correct at the skill's exam tier on ≥ 2 different days, median time ≤ T_target | A miss sets a "shaky" flag and FSRS Again; a second miss within the next 3 reviews drops one level |
| Mastered | ≥ 3 successes on different days, one of them after an interval ≥ 7 days at predicted R ≤ 0.90; ≥ 2 problem forms; ≥ 1 success above exam tier or in a mixed check-up; speed met on the last 3 correct | Same two-miss rule; recovering a level means meeting its criteria again |

This replaces the earlier report's "about three spaced successes plus a stability threshold." A Mastered skill now needs proof of delayed retrieval at genuinely uncertain R, transfer across problem forms and unprompted recognition. The ≥ 2-forms rule is a reading of ALEKS's language; it has not been validated as a transfer test. Every ~10 study hours or ~3 weeks, an ALEKS-style check-up mixes in a few skills that aren't due. Successes there satisfy the mixed-check criterion. Failures demote the skill and count as normal FSRS reviews. The display then shows **two numbers per skill**. **Recall** is FSRS retrievability now, plus its projected value on exam day if no review happens before then. That one fades with time. **Level** is a badge that drops only on failed evidence. At course level, show the share of in-scope skills at Exam-level or above, and mean projected Recall on the exam date. ALEKS likewise reports learned and mastered separately and never blends them into one percentage.

### A 0.95 semester costs about twice the work; a booster costs far less

The FSRS-6 forgetting curve gives a closed form for exam targeting ([awesome-fsrs wiki](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)):

```text
R(t, S) = (1 + f·t/S)^(−w20),   f = 0.9^(−1/w20) − 1
I(r, S) = (S / f) · (r^(−1/w20) − 1)        interval that lands at retention r
```

With the default w20 ≈ 0.154, the interval at a desired retention of 0.95 is **0.40×** the interval at 0.90. At 0.80 it is 3.3×, and at 0.85 it is 1.9× (the researcher's computation; the 0.95 ratio stays at 0.40–0.46 for w20 between 0.15 and 0.5). One user's posted simulator output (desired retention → minutes per day) was 85% → 45, 88% → 57.2, 91% → 76.2, 94% → 114.5 and 97% → 230.3 ([Anki forum](https://forums.ankiweb.net/t/replace-cmrr-with-workload-vs-dr-graph-more/63234)). Interpolated, running 0.95 all semester costs about **2.1×** the minutes of 0.90, 0.85 costs about 0.65×, and 0.80 about 0.48×. That comes from one collection, but it agrees with the interval math. Practitioners advise against capping intervals at the exam date. Cards still get scheduled past the exam unless the cap keeps shrinking. The advice instead is to raise desired retention "by a point or two" ([Anki forum](https://forums.ankiweb.net/t/exam-specific-add-on-or-help-max-review-date/67433/2)), and "90% desired retention is plenty high to start with" for an exam three months out ([Anki forum](https://forums.ankiweb.net/t/need-advice-on-fsrs-retention-for-exam-3-month/43560)). Cepeda's large study found that the optimal gap shrinks from about 20–40% of a one-week test delay to 5–10% of a one-year delay ([Cepeda et al. 2008](https://pubmed.ncbi.nlm.nih.gov/19076480/)). For a test months away, reviews should stay spaced rather than crammed.

The booster rule is the researcher's proposal; no published FSRS deadline algorithm exists. A skill whose post-review stability is S′ keeps R ≥ R\* on exam day only if its last successful review falls within **Δ\* = I(R\*, S′) ≈ 0.40·S′ days** of the exam, for R\* = 0.95. That is 4 days for S′ = 10, 8 days for 20, 16 for 40 and 32 for 80. The procedure runs daily from about 21 days before the exam:

1. For each in-scope skill, compute R on the exam date assuming no further review.
2. If the skill's normal due date falls before the exam, leave it; the next review gets re-evaluated.
3. If its due date falls after the exam and projected R is below R\*, schedule a booster on the latest feasible day d with `exam − d ≤ I(R*, S_good(d))`. S_good(d) comes from py-fsrs's preview of the state after a Good. Spread booster load evenly across the window.
4. If a booster fails, FSRS relearning shortens the interval, and step 3 runs again the next day.
5. Make no forced sweep on days −1 and 0. Offer an optional warm-up of the lowest-projected skills instead.

Each midterm and final is its own target with its own skill set. A cumulative final's booster starts from the stability left after the midterm booster, so midterm boosters aren't wasted. Store S, D and last-review time, and compute `due = last_review + I(DR_course(today), S)` on the fly. A course's desired-retention change then takes effect at once, with no batch rescheduling, and needs no re-optimization, because FSRS parameters don't depend on desired retention. After the exam, the course drops to **0.80**, about half the workload. Prerequisites for the next course, such as Calc 1 skills before Calc 2 or physics, stay at **0.85**. About 3–4 weeks before that course starts, a booster with R\* = 0.90 runs on those prerequisites alone. RemNote's exam scheduler adds one useful pattern: it "proposes a temporary increase to your daily goal rather than silently rearranging" ([RemNote](https://help.remnote.com/en/articles/9102040-understanding-the-exam-scheduler)). Any extra booster load should be offered that way.

### Goals become settings plus a projected score

No study or product maps a letter-grade goal onto spaced-repetition parameters. Products translate goals into pace instead. Math Academy shows "estimated course completion dates with a variety of daily XP goals," with one XP equal to about a minute of focused work ([Math Academy](https://mathacademy.com/how-it-works)). An exam score depends on both remembering a skill and performing it at exam difficulty and pace. So "aim for an A" has to raise Level and tier targets as well as exam-day recall. A goal that changed retention alone would mislead. The presets below are the researcher's proposal and starting values to calibrate.

| Goal | Daily retention | Exam-day R\* | Level target, in-scope skills | Tier ceiling | After the date |
|---|---|---|---|---|---|
| A | 0.90 | 0.95 | Exam-level for all; Mastered for skills tagged "core" | 5 | 0.80 (prerequisites 0.85) |
| B | 0.88–0.90 | 0.92 | Exam-level for core; Learned for the rest | 4 | 0.80 |
| Keep it | 0.80–0.85 | none | Keep Level from falling | current | same |

The goal shows up as a **projected exam score**: `E[score] ≈ Σ w_s · R_s(exam) · P_s(correct at exam tier)`, where w_s is the skill's share of exam points (equal by default) and P_s comes from the learner-side Elo ability (researcher's proposal). The planner shows that projection next to the cutoff (90 for an A). It says which factor is short: low recall calls for boosters, low P at exam tier calls for tier-4 and tier-5 practice. It proposes the extra daily questions, never adding them silently. When the goal is created, a feasibility check simulates FSRS with the booster through the exam date. It shows "≈ N questions/day (~M min)" from the student's median times, and warns when that exceeds the budget left after other courses.

### Several courses share the budget by weighted fair share

Anki's per-deck limits are static caps that interact badly. In "Deck" gather order, "gathering may stop before all subdecks have been checked," and the review limit "also applies to new cards" ([Anki manual](https://docs.ankiweb.net/deck-options.html)). Later decks starve. No research addresses fair allocation across spaced-repetition courses, so the algorithm below is the researcher's proposal, borrowed from fair-queueing practice:

1. **Weight** each course by `w = g × u × p`. Goal g is 1.5 for an A, 1.0 for a B and 0.5 for keep-it. Urgency is `u = 1 + 14 / max(days to next exam, 7)`, which runs from 1 to 3. Backlog pressure is `p = clamp(due / median due, 0.5, 2)`.
2. **Give floors first.** Each course with due work gets `max(3, ⌈0.1·B⌉)` questions; maintenance-only courses get 2.
3. **Split the rest** in proportion to weight, rounded by the largest-remainder method so the quotas sum exactly to the budget B.
4. **Return surplus.** Quota a course can't use goes back to the pool.
5. **Carry the deficit.** Up to 50% of a course's unserved quota rolls into tomorrow, so stopping early never always starves the same course.
6. **Order within each course.** Due and booster reviews come first, under the triage policy above. New skills enter only when the course's due backlog is at most one day's quota.
7. **Interleave the session.** Weave courses in proportion to remaining quota, so a session stopped halfway still served everyone.

Allocate in expected minutes as well as questions. Tier-5 calculus and a stoichiometry problem differ greatly in length, and a question count alone lets long-problem courses take most of the time. If the combined need exceeds the budget for 3 or more days running, the app should propose one of three fixes: raise the budget, lower a goal, or move a course to keep-it. This tightens the earlier report's trigger of a backlog above twice the daily count for a week. Interleaving *across* courses, as opposed to across problem types within one, was not researched.

## Every wrong answer is a hypothesis until a probe confirms it

### The first-error tap is noisy evidence, not a verdict

A paper-then-type app is an **answer-based** tutor in VanLehn's taxonomy. Answer-based tutors averaged an effect of 0.31. Step-based tutors averaged 0.76, roughly human tutoring's 0.79 ([VanLehn](https://quality.mit.edu/files/2012/01/Quality-Symposium-Kurt-VanLehn.pdf)). The step benefit comes from feedback *during* each step, so an after-the-fact tap is a diagnostic tool, not a substitute for step tutoring. The app's learning power rests on retrieval, spacing and explanatory feedback. Students' self-diagnosis depends heavily on support. On a hard physics quiz, diagnosis scores were **0.73** with an outline plus rubric, 0.57 with a worked example, and **0.24** with only the final answer. On an easier quiz, all three groups scored 0.56–0.62. About 60% of students could not diagnose misapplication of a principle they had invoked ([Mason et al.](https://arxiv.org/pdf/1603.03070)). Self-diagnosed bugs are also unstable: specific algebra bugs often failed to recur across items ([Birenbaum, Kelly & Tatsuoka 1992](https://www.ets.org/research/policy_research_reports/publications/report/1992/hxjo.html)).

That justifies the design's "tap the first step where your work differed," with four refinements (researcher's proposal):

- **Show the solution in the best-performing format.** Number the steps and give each a one-line purpose label and its skill tag. Add an explicit Step 0, "set up or choose the method."
- **Offer escape options:** "I used a different valid method," "my steps matched but my answer didn't" and "can't tell."
- **Treat the tap as a likelihood.** Give 0.6 of the blame to the tapped step's skill. Spread 0.4 over the other step skills in proportion to their weakness. With no tap, blame each required skill in proportion to (1 − R), in line with DINA-style conjunctive models, where the weakest skill most likely broke.
- **Confirm with one probe:** a single-skill problem at or below the learner's tier on the blamed skill. A failed probe confirms the gap. A passed probe makes the miss a slip or integration error, worth at most Hard on the original skill.

The researcher also proposes a self-calibration loop. Log every (self-label, tapped skill, probe result) triple. If probes confirm taps less than half the time, weight taps less. No study has measured first-error identification accuracy in a learner's own math work.

### Five causes, five signals

The table below is the researcher's proposal and turns the design's diagnosis goals into rules.

| Cause | Distinguishing signal | Scheduling action |
|---|---|---|
| Prerequisite gap | Tapped step uses a prerequisite skill; the probe on it fails | Again on the prerequisite; probe its own low-R prerequisites, deepest first |
| Concept gap in the target skill | Tapped step uses the target skill; probe fails; misses cluster on that skill across different items | Again on the target skill |
| Method-selection gap | Tap at Step 0 **and** a "cued twin" (same family, method named) succeeds; if the cued twin also fails, it is an execution gap | Lapse on the matching `select:*` skill |
| Slip | Learner reports a slip; accepted only when R ≥ 0.9, the last 2–3 attempts were correct, and slips stay under ~20% of 30-day misses | At most Hard; a second "slip" on the same sub-skill within 30 days triggers a probe |
| Hard problem | Elo-predicted P < 0.35, tapped skill recently passed at lower tiers, probe passes | No lapse; record an "above level" miss, at most Hard |

The ~20% slip budget is loosely anchored on an older estimate that about 20% of errors are careless. Carelessness correlated *positively* with engaged concentration (r ≈ 0.55), which makes it a risk for confident, fast students ([San Pedro, Baker & Rodrigo](https://learninganalytics.upenn.edu/ryanbaker/AIED-D-13-00017_Revised%20v2.pdf)). The "above level" row replaces the earlier rule that misses below P ≈ 0.5 produce no FSRS event. Misses at P ≥ 0.6 now count as strong evidence and always go to a probe. For the band in between, the default probe path applies.

### One learner cannot calibrate items, so tiers stay fixed

Elo item difficulty needs **at least ~100 students** ([Pelánek 2016](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)). Population models are fragile even at scale. Fitted additive factor models (AFM) shrink parameters toward zero, so "flagging concepts for revision from AFM parameters is risky" ([Čechák & Pelánek](https://www.fi.muni.cz/~xpelanek/publications/aied21afm.pdf)). AFM also often accepted wrong skill-model refinements across 90 simulated scenarios, while performance factors analysis (PFA) did better ([Goldin & Galyardt 2018](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/316)). The design's idea of comparing the Elo difficulty of missed and solved problems therefore needs a change. Item difficulty should be **anchored to the tier**. The researcher suggests logits of −1.5, −0.75, 0, 0.75 and 1.5 for tiers 1–5. At most, an item seen repeatedly can drift with K ≤ 0.05. Elo updates only the learner's ability. Otherwise the app concludes "that item was hard" exactly when the learner is weak. Repeated success on a tier-5 family goes to the content pipeline as "possible tier mislabel," never as an automatic edit.

The 30-day weak-spot finder has the same problem. Raw "appears in misses versus correct" lift is confounded by difficulty: skills tagged on tier-5 items look weak. It is also confounded by co-occurrence: simplification appears in most misses because it appears in most items. The replacement is a difficulty-adjusted, blame-weighted residual screen, followed by a confirmatory diagnostic set (both the researcher's proposal):

```text
p_i = σ(θ_i − d(tier_i))                          expected success, tier-fixed difficulty
e_ik = tap/probe blame on misses, else tag weight (primary 1.0, secondary 0.4, normalized)
R_k = Σ e_ik (y_i − p_i);   V_k = Σ e_ik² p_i (1 − p_i)
z_k = R_k / √(V_k + τ),  τ ≈ 0.5–1
flag k if z_k ≤ −2.0, effective n ≥ 5, misses on ≥ 3 items and ≥ 2 days
```

With about 100 active skills, a z ≤ −2.0 screen flags roughly two skills a week by chance. That is acceptable only because the next stage is the real test. That stage draws 3–4 fresh items where the flagged skill is the only primary tag, with other tags limited to high-R skills and tiers at or below the learner's level. Two or more misses confirm the gap, triggering a lapse and prerequisite probes. Zero or one miss resets the screen and turns attention to co-tagged skills. Run at most 1–2 diagnostic sets a week. If even that feels too frequent, tighten the screen to z ≤ −2.5.

### Find-the-error items, method-selection skills and malrules each earn a narrow role

Erroneous examples help reliably only in one format. A 2025 systematic review covered 40 studies, 26 of them in math. Erroneous examples beat correct ones in only 9 of 21 comparisons. **Contrasting** an erroneous example with a correct one beat correct examples in 9 of 12, and beat problem solving in 6 of 8. Some benefits appeared only on delayed tests ([Dieterich, Rumann & Rodemer 2025](https://link.springer.com/article/10.1007/s10648-025-10071-x)). In a decimals tutor, erroneous examples won only at one week, and students liked them less ([Learning Scientists on Adams et al.](https://www.learningscientists.org/blog/2023/7/27)). At field scale, AlgebraByExample mixed misconception-targeted examples with problems 50/50 across more than 6,000 students. Struggling students gained about **10 points** in conceptual knowledge while solving half as many problems ([SERP](https://serpinstitute.org/algebra-by-example/research)). The researcher's format has four steps, presented as "another student's work": pick the wrong step, choose why it is wrong, give the corrected value, then see the correct solution side by side. Introduce these items only after a skill has at least two uncued successes. Earlier, use a highlighted-error variant, because low-prior-knowledge learners transfer better from correct examples. The frequency is an assumption with no evidence behind it: at most 1 in 8–10 reviews, or after a confirmed diagnosis.

Method selection is a separate, trainable demand. Interleaving improved a delayed test from **37.6% to 60.7% (d = 0.83)** in a preregistered trial of 787 students. The authors' mechanism is that interleaved practice "requires students to choose a strategy and not merely execute a strategy" ([Rohrer et al.](https://www.gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)). Schema-based word-problem instruction improved results at a 9-week delay in 806 students ([Jitendra et al. 2017](https://experts.umn.edu/en/publications/a-randomized-trial-of-the-effects-of-schema-based-instruction-on-/)). An integral-calculus error study classed "technique determination" errors as their own conceptual type ([Voon et al. 2017](https://files.eric.ed.gov/fulltext/EJ1207815.pdf)). So the graph should hold **one selection skill per family of confusable methods**, such as `select:limit-technique`, `select:integration-technique`, `setup:related-rates` and `setup:optimization`. Each activates once at least two of its methods are introduced. "Which method fits?" items take 5–15 seconds and give many reps per minute. Generic skills such as "checking answers" lack evidence as trackable units, so they become habit prompts rather than scheduled skills (researcher's proposal).

Method cues in a problem statement remove that choice. In the integral study, u-substitution items with a hint had a 25.4% error rate versus 36.5% without one ([Voon et al. 2017](https://files.eric.ed.gov/fulltext/EJ1207815.pdf)). LLM-generated problems sometimes "embedded the solution" ([MathFish](https://aclanthology.org/2024.findings-emnlp.323.pdf)). The pipeline should detect cues with a regex for named rules plus an LLM pass for implicit ones ("let u = …", "hypotenuse"). It should rewrite review stems to drop the method, and store both versions. `stem_uncued` is the review default. `stem_cued` serves first exposure, the cued-twin probe and highlighted-error items. Keep `cue_required: true` where the method *is* the answer specification, as in "left Riemann sum with n = 4." Tag forms that give the method away, like ∫xeˣdx, with `selection_evidence: low` (researcher's proposal). No experiment has compared cued and uncued wording of the same item directly.

Executable misconception libraries now exist for the prerequisite layer. MalruleLib encodes **101 misconceptions across 498 parameterized templates**, each as code (generator, correct solver, buggy solver and tests). Every misconception traces to published research, but the library stops before calculus ([MalruleLib](https://arxiv.org/pdf/2601.03217)). Its tests also show why a predicted wrong answer is only evidence. LLMs predicted a student's next wrong answer from one worked mistake only about 40% of the time on a new template. The researcher proposes a small hand-built calculus table, with 3–8 wrong transformations per skill written as functions. Examples include dropping the inner derivative, (fg)′ = f′g′, and ∫1/x² dx → ln(x²); these examples need verification against the literature. Every malrule runs on every generated problem at build time. A typed answer that matches a malrule output earns targeted feedback, pre-selects the likely step in the tap UI and carries blame of about 0.8, but it still triggers the probe. The same buggy solvers can generate find-the-error items automatically.

## AI tags hold up only when each one is verified against a step

LLMs are good at **verifying** whether one skill fits one problem and poor at **picking** from a large list. In MathFish (9,923 problems, 385 standards), GPT-4's free, self-guided tagging exactly matched the gold set **4.8%** of the time. It predicted **3.05 standards per problem versus 1.66 gold**, usually landing next to the right one. Assisted hierarchical tagging, one level at a time, reached 0.85 mean per-level accuracy. LLM verifiers were lenient, judging 96% of generated problems aligned where teachers judged 52% ([MathFish](https://aclanthology.org/2024.findings-emnlp.323.pdf)). On binary concept matching, GPT-4o scored about 88% accuracy against a human expert's 92%, with **recall 96.8% but precision 76.5%** ([arXiv 2409.08406](https://arxiv.org/pdf/2409.08406)). Over-tagging is therefore the dominant error. Zero-shot Q-matrix coding agreement ranged from κ = 0.12 to 0.63 and **did not improve with newer models** ([Fan, Bialo & Li](https://arxiv.org/pdf/2602.08796)). Generated knowledge components can match or beat human ones. In one programming study, instructors judged their precision at 93.2% versus 92.5% for human tags, but removing few-shot examples made them too abstract ([KCGen-KT](https://aclanthology.org/2026.findings-acl.1670.pdf)). LLM-proposed misconception tags agreed only modestly with experts but fit student responses better (AUC 0.780 versus 0.717). Keyword-driven over-tagging was a systematic error ([Zhang et al. 2026](https://arxiv.org/pdf/2604.16398)). No published accuracy exists for LLM tagging of college calculus.

The procedure therefore changes from "choose from the list" to **solve → step-tag → verify**. The researcher's eight steps:

1. **Write a versioned taxonomy.** Each skill gets a definition, two positive examples and one or two near-miss negatives drawn from its confusable neighbor. Near-misses target MathFish's main failure, confusing neighboring standards.
2. **Solve.** The model writes a numbered worked solution and checks its final answer against the key with SymPy. A mismatch means reject or re-run.
3. **Narrow candidates.** Use chapter context or embedding top-k (10–15), and always include "NONE / NEW SKILL."
4. **Step-tag.** Each step gets exactly one candidate skill. Key steps give at most 2 primary tags; routine steps give at most 4 secondary "uses" tags.
5. **Verify.** Ask a yes/no question per tag ("Does solving this REQUIRE skill X as defined?"), with the near-miss neighbor's definition in the prompt.
6. **Measure confidence.** Repeat steps 4–5 three to five times at temperature above zero with shuffled candidates. Accept primaries kept in ≥ 0.8 of runs, send 0.4–0.8 to review, and drop the rest.
7. **Detect cues and propose a tier** in the same pass.
8. **Record provenance and pin versions.** Store the model, prompt version and taxonomy version, and pin all three, since results drift across model versions.

The step-tagged solution serves twice. It is also the scaffolded, skill-labeled worked solution that the diagnosis tap needs, so the solve step costs nothing extra. The earlier report estimated about $0.00003 per problem for a single tagging call. The new procedure needs a solution plus three to five tag-and-verify runs, which multiplies that figure several times. At Haiku 5.5's $0.10/$0.50 per million tokens ([Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing)), it still stays cheap.

Validation runs on one learner's scale (researcher's proposal). Before using a chapter, hand-check a stratified sample of 30–50 items, oversampling low-confidence and multi-tag items. Wherever a skill's primary-tag precision falls below 0.85, rewrite its definition and near-misses, then re-run. Tags that flip between runs or models go to review automatically. Once the learner's data accumulates, four detectors raise review flags, never automatic edits:

- **Surprising success:** fast and correct while the primary skill is confirmed weak.
- **Repeated taps on an untagged skill:** suggests a missing tag.
- **Probe disagreement:** probes pass, but misses on the family keep recurring.
- **Persistent residual outliers:** an item's results keep deviating from what its tagged skills predict.

Automated refinement is error-prone even with many students. When "NONE / NEW SKILL" keeps firing on similar steps, cluster those steps and propose a new skill for review.

## pywebview on WKWebView replaces Qt, and the Mac replaces CI

### Why the shell changed and what it costs

The earlier recommendation assumed an undecided OS and GitHub CI. With a Mac-only, no-GitHub, free-tools-only project, the researcher recommends **pywebview 6.2.1** (BSD-3-Clause, released 2026-04-15) ([PyPI pywebview](https://pypi.org/project/pywebview/)). It is a thin PyObjC wrapper around the system WKWebView. The JS bridge travels over WKScriptMessageHandler, not HTTP ([cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)). Exposed Python methods return Promises to JavaScript ([pywebview bridge guide](https://pywebview.flowrl.com/guide/interdomain.html)). It provides native menus and file dialogs. PySide6 6.12 still works, but its QtWebEngine wheel alone is **249.8 MB** ([PyPI PySide6-WebEngine](https://pypi.org/project/PySide6-WebEngine/)). Qt's real advantages are a pinned Chromium and an interceptor that sees every subresource request ([Qt docs](https://doc-snapshots.qt.io/qtwebengine/qwebengineurlrequestinterceptor.html)). Those matter less for one user on one Mac. Both stacks need macOS 14 or later in practice. Tauri 2 would use the same WKWebView while adding Rust and a PyInstaller-frozen Python sidecar ([Tauri sidecars](https://v2.tauri.app/develop/sidecar/)). Briefcase/Toga is a credible plan B with a weaker bridge story ([PyPI briefcase](https://pypi.org/project/briefcase/)). A native Swift host is the most native option and far too much work for now.

| Dimension | pywebview 6.2.1 | PySide6 6.12 + QtWebEngine |
|---|---|---|
| Bundle | No engine bundled; size not yet measured | 249.8 MB WebEngine wheel; expect a few hundred MB app |
| Engine | Follows the installed Safari/WebKit; Safari 26 also ships for macOS 14 and 15 ([Apple](https://support.apple.com/en-mide/125113)) | Pinned Chromium, deterministic until upgraded |
| Offline enforcement | CSP meta tag; `request_sent` sees only the main document on macOS | Interceptor blocks any subresource |
| Native feel | Native WebKit text input, IME, spellcheck | Chromium inside a Qt window |
| Maintenance | Small project; no release in 6.5 months; open macOS 26 bug | Qt Company; 6.12.0 and 6.11.3 both shipped in Oct 2026 |

The costs are concrete, and each has a mitigation:

- **No custom scheme.** A relative entry path starts a built-in Bottle server on `http://127.0.0.1:<random port>` that cannot be disabled ([pywebview architecture](https://pywebview.flowrl.com/guide/architecture.html)). The page origin changes every launch. Private mode (the default) wipes website data, and `storage_path` is a no-op on Cocoa ([#1714](https://github.com/r0x0r/pywebview/issues/1714)). All state, including window geometry, therefore lives in SQLite, never in localStorage.
- **Offline enforcement falls to the CSP.** The Cocoa backend sets `NSAllowsArbitraryLoads`, and `request_sent` fires only for the main document on macOS ([pywebview API](https://pywebview.flowrl.com/api/)). Offline is enforced by a CSP meta tag (`default-src 'self'; connect-src 'self'; img-src 'self' data: blob:; font-src 'self' data:; style-src 'self' 'unsafe-inline'`). The `'unsafe-inline'` is there because MathLive inserts styles dynamically.
- **Thread safety.** "Exposed functions are executed in separate threads and are not thread-safe" ([pywebview bridge guide](https://pywebview.flowrl.com/guide/interdomain.html)). Route every database write through one owner thread.
- **Native key handling.** The native view intercepts Cmd+Z (sent to the native undo manager), Cmd+A, Cmd+V, Cmd+Q and Cmd+W before the page sees them ([cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)). MathLive's own undo stack may never run. Test this in week one. The fix is a small override of `WebKitHost.keyDown_`.
- **Debug mode.** Issue #1866 (open) reports overlapping, unclickable traffic-light buttons on macOS 26 when `debug=True` ([#1866](https://github.com/r0x0r/pywebview/issues/1866)). Gate debug behind an environment variable and never ship it.
- **Shutdown.** atexit may not run on some shutdown paths ([issues](https://github.com/r0x0r/pywebview/issues)). Commit each review immediately.
- **Python build.** The FAQ warns of focus and Cmd+Tab problems with a venv built from the system Python ([FAQ](https://pywebview.flowrl.com/guide/faq)). Use uv-managed or python.org Python, never `/usr/bin/python3`. Use the standard GIL build, given the no-GIL error report.

Keep pywebview behind one `shell/` module so a swap back to PySide6 stays contained.

MathLive must be **0.111.0 or later**. That release fixed Safari's loss of the last edit when a focused math field leaves the DOM, which is exactly what happens when a review card advances. 0.111.2 tightened same-origin checks so two opaque `"null"` origins no longer match ([MathLive changelog](https://github.com/arnog/mathlive/blob/master/CHANGELOG.md)). That rules out `file://`. Read the answer explicitly with `mf.getValue()` on submit. Import `mathlive/fonts.css` and KaTeX's CSS through Vite, so fonts are emitted locally ([MathLive integration](https://mathlive.io/mathfield/guides/integration/); [KaTeX](https://katex.org/docs/browser)). Set `base: './'`. Add a build test that greps `dist/` for stray `http(s)://` URLs. The earlier safety rules all carry over unchanged: the whitelisted MathJSON-to-SymPy translator, no `parse_expr`, and a SymPy worker process with a timeout. The bridge is now pywebview's `js_api` instead of QWebChannel. On macOS, `multiprocessing` uses spawn, so the frozen app must call `freeze_support()` first.

### Pinned versions as of 2026-11-01

| Component | Version (date) | Note |
|---|---|---|
| Python | 3.14 (3.14.10, 2026-10-25) | Bugfix until 2030-10; 3.15 too new; 3.13 security-only ([python.org](https://www.python.org/downloads/)) |
| uv | 0.13.6 (2026-10-27) | Python install, universal lockfile ([PyPI](https://pypi.org/project/uv/)) |
| pywebview | 6.2.1 (2026-04-15) | Classifiers stop at 3.13; pure Python over PyObjC ([PyPI](https://pypi.org/project/pywebview/)) |
| pyobjc-core | 13.0 (2026-10-30) | cp314 universal2 wheels ([PyPI](https://pypi.org/project/pyobjc-core/)) |
| PyInstaller | 6.22.3 (2026-09-12) | Supports 3.8–3.15; onedir `.app` ([PyPI](https://pypi.org/project/pyinstaller/)) |
| SymPy / mpmath | 1.14.0 / 1.4.1 | SymPy's classifiers stop at 3.13, but its main CI runs 3.14 ([sympy CI](https://github.com/sympy/sympy/blob/master/.github/workflows/runtests.yml)) |
| py-fsrs / fsrs-rs-python | 6.3.2 / 0.9.3 | See the Anki section |
| Svelte / Vite | 5.57.3 / 8.3.5 | npm, Oct 2026 ([svelte](https://www.npmjs.com/package/svelte); [vite](https://www.npmjs.com/package/vite)) |
| KaTeX / MathLive | 0.19.1 / 0.111.4 | Self-hosted from npm ([katex](https://www.npmjs.com/package/katex); [mathlive](https://www.npmjs.com/package/mathlive)) |
| ruff / mypy / pytest / Hypothesis / import-linter | 0.17.3 / 2.4.1 / 9.2.0 / 6.170.14 / 2.15 | Local checks ([ruff](https://pypi.org/project/ruff/); [mypy](https://pypi.org/project/mypy/); [pytest](https://pypi.org/project/pytest/); [hypothesis](https://pypi.org/project/hypothesis/); [import-linter](https://pypi.org/project/import-linter/)) |
| Playwright / pytest-playwright | 1.64.1 (WebKit 27.2) / 0.10.0 | UI tests in WebKit ([PyPI](https://pypi.org/project/playwright/)) |

### One command checks everything the sandbox can't

Without CI, one script is the quality gate. The layout separates `app/core` (scheduling, SQLite), `app/checker` (the SymPy worker) and `app/bridge` (the plain-Python API object exposed to JS) from `app/shell`, the only package that imports `webview` or `objc`. An import-linter contract enforces that split, so everything but the shell tests on Linux too. UI tests serve `ui/dist` and inject a fake `window.pywebview.api` that forwards calls to the real bridge. Then they run in Playwright's WebKit. That build is "derived from the latest WebKit main branch sources" and is not branded Safari ([Playwright browsers](https://playwright.dev/python/docs/browsers)), so it catches DOM and JavaScript bugs but not every WKWebView quirk. A `page.route` handler fails the test on any request outside 127.0.0.1. The only test of the real WKWebView + PyObjC + PyInstaller combination is a `--self-test` flag on the frozen app. It starts hidden, renders one KaTeX formula and one MathLive field, calls one bridge method, gets an answer from the SymPy worker, and exits 0 or 1. The researcher's script, condensed:

```bash
uv sync --locked && uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run lint-imports
[[ $MODE == fast ]] && { HYPOTHESIS_PROFILE=dev uv run pytest -q -x -m "not ui and not slow"; exit 0; }
( cd ui && npm ci --prefer-offline && npx svelte-check && npx vitest run && npm run build )
HYPOTHESIS_PROFILE=thorough uv run pytest -q -n auto -m "not ui"
uv run pytest -q -m ui --browser webkit
if [[ $(uname) == Darwin ]]; then
  uv run pyinstaller packaging/Toishi.spec --noconfirm --clean
  codesign --verify --deep --strict dist/Toishi.app
  dist/Toishi.app/Contents/MacOS/Toishi --self-test
fi
```

The pre-commit framework normally clones its hook repositories, typically from GitHub. A plain tracked hook works offline instead: `scripts/git-hooks/pre-commit` runs `check.sh fast`, installed with `git config core.hooksPath scripts/git-hooks`. Two packaging items are unverified and belong in week one. pywebview's own freezing guide says "use py2app" for macOS and mentions PyInstaller only for other platforms ([pywebview freezing](https://pywebview.flowrl.com/guide/freezing.html)). Whether PyInstaller collects pywebview's injected JS without `--collect-data webview` is untested. Build a hello-world `.app` first, and keep py2app 0.28.10 as the fallback ([PyPI py2app](https://pypi.org/project/py2app/)). Also test uv's standalone Python builds with PyInstaller early; the python.org installer is the safe fallback.

### Locally built apps skip Gatekeeper; data and backups stay out of iCloud's way

The earlier report's open Gatekeeper question is settled for this workflow. Apple's DTS engineer states that "all code on Apple silicon must be at least ad hoc signed" and that "Gatekeeper typically only kicks in if the app is quarantined" ([Apple Developer Forums](https://developer.apple.com/forums/thread/740680)). Build tools sign ad hoc, but their output is never quarantined ([Eclectic Light](https://eclecticlight.co/2024/10/01/living-without-notarization/)). PyInstaller ad-hoc signs every binary by default ([PyInstaller](https://pyinstaller.org/en/stable/feature-notes.html)). A `.app` built on the Mac and copied to /Applications with `ditto` launches without a prompt. No paid developer account or notarization is needed. Never edit files inside the built `.app`: that breaks the signature, and Apple Silicon refuses to run it. Rebuild instead. Use a fixed bundle ID such as `com.<name>.toishi`. Store data in `~/Library/Application Support/<bundle-id>/`, Apple's location for app-specific user data ([Apple](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/MacOSXDirectories/MacOSXDirectories.html)). Don't call platformdirs with a version argument: its macOS path appends the version ([platformdirs](https://github.com/tox-dev/platformdirs/blob/main/src/platformdirs/macos.py)), which would split data across releases.

Backups need two different mechanisms. **The source repo** gets a daily `git bundle create --all`, a full, self-contained backup of all refs that `git bundle verify` can check ([git-bundle](https://git-scm.com/docs/git-bundle)). The bundle is written to a temp file, verified, and only then moved into iCloud Drive. The live repo itself must never sit in iCloud. iCloud creates numbered duplicates such as `refs/heads/main 2` inside `.git` and breaks the repository ([dev.to](https://dev.to/architchandra/a-side-effect-of-storing-a-git-repository-in-icloud-drive-7ed)). So keep it in `~/Developer`, outside the Desktop and Documents folders that iCloud may sync. **The study database** needs care because of WAL. The WAL file "is part of the persistent state of the database" ([SQLite WAL](https://www.sqlite.org/wal.html)), and background tools copying mid-transaction can produce a corrupt copy. `VACUUM INTO` and the backup API "will work even on a live database" ([SQLite](https://www.sqlite.org/howtocorrupt.html)). Forum participants agree that a Time Machine copy of a live WAL database restores like a crash at best ([SQLite forum](https://sqlite.org/forum/forumpost/796a192a95)). Only `user.db` needs snapshots: `content.db` is a build artifact regenerable from the repo (an inference from the earlier two-database design). The app writes a `VACUUM INTO` snapshot on first launch each day and before every migration. The nightly job copies the newest one into iCloud as a single closed file and keeps 30 of each kind. Time Machine runs on top of both.

Schedule the job with a per-user launchd agent, not cron. Apple says cron "has been deprecated in favor of launchd." A `StartCalendarInterval` job that misses its time during sleep runs on wake ([Apple](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)). Load the agent with `launchctl bootstrap gui/$(id -u) <plist>` and test it with `launchctl kickstart -k` ([ss64](https://ss64.com/mac/launchctl.html)). The core of the script:

```zsh
git -C "$REPO" bundle create "$TMP/repo.bundle" --all
git -C "$REPO" bundle verify "$TMP/repo.bundle" >/dev/null
mv "$TMP/repo.bundle" "$DEST/repo-$(date +%F).bundle"
/usr/bin/sqlite3 "$DATA/user.db" "VACUUM INTO '$TMP/user.db'" && mv "$TMP/user.db" "$DEST/user-$(date +%F).db"
```

It is unverified whether a launchd agent can write to iCloud Drive without a privacy prompt. The first `kickstart` run will show "Operation not permitted" in the log if it can't. Once a month, run a restore drill: `git clone` the bundle and `git fsck --full` it.

## Anki packages hide three traps, and fsrs-rs-python removes PyTorch

### Detecting the format: never read `collection.anki2` first

.apkg and .colpkg files are ZIP archives built by the same code. The format is decided by a two-byte protobuf `meta` entry ([meta.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/meta.rs); [import_export.proto](https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto)):

| Package | `meta` | Collection file | Compression | Media map |
|---|---|---|---|---|
| Latest (2.1.50+ default) | `08 03` | `collection.anki21b` (schema 18) | zstd for the DB, every media file and the map | Protobuf `MediaEntries` (name, size, SHA-1) |
| Legacy 2 ("support older versions") | `08 02` | `collection.anki21` (schema 11), deflated | None beyond zip | JSON `{"0":"pic.png"}` |
| Legacy 1 (old Anki, old AnkiDroid) | absent | `collection.anki21` if present, else `collection.anki2` | None | JSON, or missing (treated as `{}`) |

The first trap: every modern export also writes a **dummy `collection.anki2`** containing one note that says "Please update to the latest Anki version" ([colpkg/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/colpkg/export.rs)). An importer that reads it first imports garbage. A `meta` value of 0 or above 3 means "too new." The second trap: Anki's streaming zstd encoder leaves the content size out of the frame header. In a local test with packages built by `anki` 26.9.3, one-shot decompression raised "could not determine content size," while `ZstdDecompressor().stream_reader()` worked ([PyPI anki](https://pypi.org/project/anki/), verified locally). Python 3.14's standard library includes `compression.zstd` ([PEP 784](https://peps.python.org/pep-0784/)). Media files sit in the zip as `"0"`, `"1"`, … and are mapped back to names. Names are NFC-normalized and limited to 120 bytes, and unsafe names are rejected ([media.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/media.rs)).

### Reading schema 11 and schema 18

After decompressing to a temp file, read `col.ver`. Schema 11 keeps notetypes, decks and deck options as JSON strings in the single `col` row. Schema 18 moves them into `notetypes`, `fields`, `templates`, `decks`, `deck_config` and `config` tables, whose `config` columns are protobuf blobs ([schema upgrades](https://github.com/ankitects/anki/tree/main/rslib/src/storage/upgrades)). Two more traps were verified locally:

- Querying those tables from Python's `sqlite3` fails with "no such collation sequence: unicase" until a casefold collation is registered ([schema15_upgrade.sql](https://github.com/ankitects/anki/blob/main/rslib/src/storage/upgrades/schema15_upgrade.sql)).
- The apkg exporter starts from a default collection and runs only `DELETE FROM notetypes`. `fields` and `templates` therefore keep orphan rows for every stock notetype, so always join them to `notetypes.id` ([apkg/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/apkg/export.rs)).

Only a few protobuf fields matter: template question and answer (fields 1 and 2), notetype kind and CSS (1 and 3), deck `config_id`, and deck-config `fsrs_params_6` (field 6, packed floats) plus `desired_retention` (field 37) ([deck_config.proto](https://github.com/ankitects/anki/blob/main/proto/anki/deck_config.proto); [notetypes.proto](https://github.com/ankitects/anki/blob/main/proto/anki/notetypes.proto)). The researcher estimates a hand-written decoder for them at about 50 lines, which avoids the protobuf runtime. The data columns follow fixed conventions:

- **Notes.** `notes.flds` joins fields with `\x1f`. Tags are stored as `" t1 t2 "`.
- **Card state.** `cards.data` is JSON. A memory state exists only if both `s` and `d` are present ([data.rs](https://github.com/ankitects/anki/blob/main/rslib/src/storage/card/data.rs)). A local sample after two Goods read `{"pos":1,"s":2.3065,"d":2.111,"dr":0.9,"decay":0.154,"lrt":1793547859}`.
- **Revlog fields.** `ease` 1–4 is the button pressed, and 0 marks a manual action. `ivl` counts days when positive and seconds when negative. `type` is 0 learn, 1 review, 2 relearn, 3 filtered, 4 manual or 5 rescheduled. A Reset is type 4 with factor 0; cramming is type 3 with factor 0.
- **Difficulty in revlog.** With FSRS on, `factor` stores difficulty normalized to 100–1100, recoverable as `D = (factor/1000 − 0.1)·9 + 1` ([revlog/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/revlog/mod.rs); [memory_state.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/memory_state.rs)).
- **Old scheduler.** In v1-scheduler learning entries, ease 3 meant Easy.

An exported apkg carried neither the global `fsrs` switch nor `rollover` in a local test. Assume Anki's 4 a.m. rollover unless the user says otherwise; a .colpkg carries the real values. Since Anki 26.08, exporting without scheduling also strips FSRS parameters ([commit 8a99c47](https://github.com/ankitects/anki/commit/8a99c47)).

### Rendering cards and handling media safely

Anki's template language only resembles Mustache, and it differs in six ways ([template.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs); [cloze.rs](https://github.com/ankitects/anki/blob/main/rslib/src/cloze.rs)):

- `{{Field}}` inserts raw HTML.
- "Empty" means only whitespace and `<br>`/`<div>` tags.
- Filters apply right to left, so `{{text:cloze:Text}}` runs `cloze` first.
- `{{FrontSide}}` inserts the rendered question.
- An unknown field is an error.
- Clozes allow multiple ordinals and nesting, and `}}` inside MathJax closes only a cloze opened within it.

genanki uses the generic `chevron` Mustache library, so it gets these rules wrong ([genanki](https://pypi.org/project/genanki/)). The other PyPI readers predate the 2.1.50 format. There are two workable routes. The first is a pure-Python renderer, which the researcher estimates at 200–300 lines porting the rules above. The second is the official `anki` 26.9.3 pylib, an AGPL wheel of about 9.2 MB. In a local test it imported a latest-format apkg into a throwaway collection and rendered `card.question()` headlessly. It returned the scheduling memory state and both revlog rows ([PyPI anki](https://pypi.org/project/anki/), verified locally). For a private app that is never conveyed, the AGPL triggers nothing. That is a general reading, not legal advice. Porting avoids both the license and the API churn: 26.09b1 removed the legacy importers ([commit d4fdbef](https://github.com/ankitects/anki/commit/d4fdbef)), and compatibility shims were added afterward.

Shared decks can carry arbitrary JavaScript, and Anki's own `hint:` filter emits an inline `onclick` ([template_filters.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template_filters.rs)). Imported cards should therefore follow five rules:

- Render under a CSP with `script-src 'none'`.
- Strip `<script>` tags, `on*=` attributes and `javascript:` URLs.
- Replace `hint:` with a `<details>` element and `[[type:…]]` with the app's own input.
- Copy media into the app's folder under normalized names. Rename on collision and rewrite the references found by Anki's patterns: `src`/`data` on media tags, `[sound:…]`, and underscore-prefixed files in CSS ([text.rs](https://github.com/ankitects/anki/blob/main/rslib/src/text.rs)).
- MathJax delimiters stay in the HTML for KaTeX to render.

For a student's own question/solution cards, the plain-text format is the simplest authoring route. Since Anki 2.1.54 it carries `#separator:tab`, `#html:true` and column headers for guid, notetype, deck and tags. The body is tab-separated with RFC 4180 quoting, and `#` lines count as comments ([csv metadata.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/metadata.rs); [Anki manual](https://docs.ankiweb.net/importing/text-files.html)). Python's `csv` module has no comment option, so filter `#` lines only at record starts. That way a quoted multi-line field is never cut. Plain text carries no media, templates or scheduling.

### Rebuilding memory state and fitting parameters

Anki computes memory state with fsrs-rs 6.6.2 in six steps ([params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)):

1. Order each card's revlog by time.
2. Drop cram entries.
3. Cut everything before the last Reset.
4. Keep history from the start of the last learning block.
5. Drop ease-0 entries.
6. Convert each entry to (rating, delta_t), counting delta_t in rollover-aware **Anki days**.

Incomplete histories are seeded with `memory_state_from_sm2`. py-fsrs 6.3.2's `reschedule_card` instead replays reviews with `timedelta.days`, which counts 24-hour blocks ([py-fsrs scheduler](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)). That is the third trap. On one seven-review history, replaying raw timestamps gave **S = 9.30**. Anki's method gave **S = 12.65**. Difficulty matched at 8.24 (verified locally). The fix is to compute each review's Anki day number with a 4 a.m. rollover and the local time zone. Then build synthetic UTC datetimes as epoch + day + k seconds, where k is the review's index within its day, before calling `reschedule_card`. A shortcut skips replay entirely. If the source had FSRS on, copy `s`, `d` and `lrt` from `cards.data` straight into py-fsrs's stability, difficulty and last-review fields, and import `fsrs_params_6` with them.

**fsrs-rs-python 0.9.3** (2026-08-31) wraps that same Rust crate. Its macOS arm64 wheel holds a 1.3 MB native library with no Python dependencies, built for CPython 3.9–3.14 ([PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/)). It exposes `compute_parameters`, `memory_state`, `memory_state_from_sm2`, `next_states`, `evaluate`, `simulate` and `optimal_retention` ([fsrs_rs_python.pyi](https://github.com/open-spaced-repetition/fsrs-rs-python/blob/main/fsrs_rs_python.pyi)). All of them worked locally. Its default parameters are identical to py-fsrs's 21. That reverses the earlier advice to leave the optimizer out of the build. The training thresholds come from fsrs-rs ([training.rs v6.6.2](https://github.com/open-spaced-repetition/fsrs-rs/blob/v6.6.2/src/training.rs)):

- Fewer than 8 training items returns the defaults unchanged.
- Fewer than 64 fits only the four initial-stability parameters.
- 64 or more fits all 21. Locally, 1,041 synthetic items fitted in well under a second.

Those thresholds are mechanical. Parameters fitted from 64 items will be noisy, so the binned calibration check stays. Two cautions apply:

- `optimal_retention` returned **0.70** under the default simulator configuration, which encodes flashcard costs. For multi-minute problems, its `state_rating_costs` must come from the app's own logged durations.
- Imported Anki history raises the data volume on day one, but it describes flashcards. The earlier per-domain preset rule still applies (an inference): Anki history fits parameters for imported decks, not for problem skills.

The library has two risks. Neither its PyPI metadata nor its repository declares a license, although the underlying crate is BSD-3-Clause ([fsrs-rs LICENSE](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/LICENSE)). That is irrelevant privately and a question to settle before any sharing. And FSRS-7 work is active on fsrs-rs `main`, including a commit titled "default empty parameters to FSRS-7" (#455). It has not been released: crates.io's latest is 6.6.2 ([crates.io](https://crates.io/crates/fsrs)), py-fsrs has no FSRS-7 code, and Anki 26.09's deck config holds only FSRS-4, -5 and -6 parameters ([fsrs-rs commits](https://github.com/open-spaced-repetition/fsrs-rs/commits/main)). Pin `fsrs-rs-python==0.9.3` and always pass explicit 21-value parameters, so a future upgrade can't silently switch models.

## Nine national universities clear reuse; open sources cover Calc I but not chemistry

### Japanese exam policies

| Source | Reuse without prior approval? | Key conditions | Official math answers |
|---|---|---|---|
| Tokyo, Kyoto, Kyushu, Shinshu (earlier report; private Meiji and Chuo also allow it) | Yes (Kyoto: granted on conditions; Kyushu can revoke) | Cite source, mark changes, label unofficial answers, report within one month of publication | Kyoto yes; Tokyo no |
| Osaka | Yes, since 2024-03-06; terms of 2025-03-28 | Form 様式1 plus the deliverable within one month; cite like 「大阪大学 令和７年度 前期 数学」; mark 改題; label unpublished answers; no answer sheets online; no sublicensing ([notice](https://www.osaka-u.ac.jp/ja/admissions/faculty/general/files/s9dfgq/@@download/file); [policy](https://www.nyusi.icho.osaka-u.ac.jp/uploads/2025/03/nyushi_mondai_riyou20250328.pdf)) | Unverified |
| Tohoku | Yes, since 2025-07-01 | Google Form report within one month; revised versions re-reported ([policy](https://admissions.tohoku.ac.jp/ja/adcms/wp-content/uploads/2025/10/secondaryuse-1.pdf)) | In 出題意図 "where a unique answer can be shown"; R8 前期/後期 posted ([page](https://admissions.tohoku.ac.jp/ja/materials/ito/)) |
| Nagoya | Permission granted on conditions (2022-10-04) | Report plus a copy within one month; stop if revoked ([policy](https://www.nagoya-u.ac.jp/admissions/exam/data/answer/copyright_policy/post_208.html)) | 正解・解答例 for R6–R8 ([index](https://www.nagoya-u.ac.jp/admissions/exam/data/answer/index.html)) |
| Hiroshima | Yes, since 2021-08-19 | Microsoft Form report within one month plus a mailed copy ([page](https://www.hiroshima-u.ac.jp/nyushi/gakubu/riyou)) | Label as unofficial unless published |
| Hitotsubashi | Yes (undated) | Email report 「遅滞なく」 ([policy](https://juken.hit-u.ac.jp/admission/info/files/R5_nijiriyo.pdf)) | Not stated; as a social-science university its math is likely humanities-track (文系) only, so limited calculus value (inference) |
| Hokkaido, Kobe | No policy found: permission required | — | Hokkaido 数学β with answers for ~3 years ([R8](https://www.hokudai.ac.jp/admission/faculty/general/R8examanswer.html)); Kobe 解答例 R4–R8 ([index](https://www.office.kobe-u.ac.jp/stdnt-examinavi/juken/past_exam/index.html)) |
| Institute of Science Tokyo | Application form (申請) | Conditions unreadable ([page](https://admissions.isct.ac.jp/ja/013/undergraduate/examination-questions)) | Medical/dental track (医歯学系) only |
| Waseda | No: clear permission yourself ([page](https://www.waseda.jp/inst/admission/undergraduate/past-test/)) | — | Where available |
| Common Test (DNC) | No: apply before use, decision normally within 8 business days ([policy](https://www.dnc.ac.jp/about_site.html)) | Send a copy after use | Answer keys R6–R8 |
| Tsukuba, Keio | 前期 not posted ([Tsukuba](https://ac.tsukuba.ac.jp/examination/exam_questions/)); no undergraduate archive found for Keio | — | — |

Every one-month reporting duty runs from publication of the deliverable (「成果物の公表」). Nagoya defines secondary use as publishing or posting online. A private app that is never shared therefore arguably owes no reports. That is the researcher's reading, not a ruling from any university. One caveat cuts the other way. The self-study exemptions at Tohoku, Hiroshima and Nagoya name 受験予定者 (prospective examinees), which the user is not. No policy mentions translation. Since every one requires marking changes, each English card should carry "Source: [University] [year] [前期/後期] 数学 第n問, translated and adapted (改題); solution unofficial unless marked." A provenance table should record the source URL, retrieval date and policy URL, in case a report is ever needed. For calculus, the useful papers are the science-track (理系) ones: Tohoku 数学（理系）, Nagoya 数学（理科系）, Osaka 前期 理系 and Hiroshima 前期. They are hand-downloaded PDFs, a handful per year, from archives that hold about three years.

### The WeBWorK renderer returns keys, with exclusions

The earlier claim is now confirmed in source code. `POST /render-api` with `_format=json` and `isInstructor=1` adds the full PG answer hash to the JSON response. Without `isInstructor`, the answers are missing ([FormatRenderedProblem.pm](https://github.com/openwebwork/renderer/blob/main/lib/WeBWorK/FormatRenderedProblem.pm)). Each answer entry carries `correct_ans`, `correct_ans_latex_string` and `correct_value` ([AnswerChecker.pm](https://github.com/openwebwork/pg/blob/main/lib/Value/AnswerChecker.pm)). Solutions come back only inside `renderedHTML`, so they must be scraped or tried through the untested PreTeXt output. The renderer is quiet but alive. `main` was last committed 2025-06-18 and `develop` 2025-08-05, while PG itself is at version 2.21 and was last committed 2026-10-27 ([renderer](https://github.com/openwebwork/renderer); [pg](https://github.com/openwebwork/pg)). It runs as a locally built Docker image on port 3000 with the OPL mounted. No JWT is required by default. The build is the main risk: the Dockerfile starts `FROM ubuntu:20.04` and installs Node 16 from nodesource, and whether that still builds on Apple Silicon is unverified ([Dockerfile](https://github.com/openwebwork/renderer/blob/main/Dockerfile)). The fallback is PreTeXt's static processing with a local copy of PG, which its guide calls the fastest route ([PreTeXt guide](https://pretextbook.org/doc/guide/html/publication-file-webwork.html)). Throughput is undocumented.

A blobless clone counted **77,134** `.pg` files ([OPL](https://github.com/openwebwork/webwork-open-problem-library)). The exclusion list grows. Skip `Pending/` (6,969 files), `WHFreeman` (1,264), `Wiley` (413) and the newly identified `UVA-Stew5e` (773). Also skip any file whose `TitleText` or `AuthorText` names a commercial textbook, and any file that loads applet, LiveGraphics, graph-tool or plotly macros. Drop any render with a non-empty `pg_warn`/`perl_warn` or an empty answer hash. Problems with custom checkers or multi-part answers can report a `correct_ans` that is only one acceptable form. So grade by equivalence, at the MathObjects default of **1E-4 relative tolerance** ([Value.pm](https://github.com/openwebwork/pg/blob/main/lib/Value.pm)), which corrects the earlier report's 0.001. Under the researcher's reading, the renderer's GPL-3.0 governs distributing the program. Running it privately at build time and keeping only its output creates no obligation. The rendered text remains CC BY-NC-SA 3.0. The first pilot is `Library/Rochester/setMAAtutorial/hello.pg` at seed 1234, checking that `answers.AnSwEr0001.correct_ans` comes back.

### Calc I, physics and chemistry sources

The **CLP-1 problem book** is the best verified Calc I match. It is CC BY-NC-SA 4.0, 550 pages, with hints, answers and full solutions for every problem. Its starred problems come from real UBC Math 100, 180 and 120 quizzes and exams; a glyph count found about 237 stars. Problems are graded Stage 1–3. A blue-outlined set is "usually highly typical of what you'd see on an exam" ([CLP-1 problem book](https://personal.math.ubc.ca/~CLP/CLP1/clp_1_dc_problems.pdf)). **MIT OCW 18.01** adds review sheets, practice exams and real exams, all with solutions ([18.01 exams](https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/pages/exams/)). It is CC BY-NC-SA 4.0, judged by "the use, not the user" ([OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/)). APEX is CC BY-NC 4.0 ([colophon](https://runestone.academy/ns/books/published/APEXPROTEUS/colophon.html)), and Active Calculus is CC BY-SA ([AIM](https://textbooks.aimath.org/textbooks/approved-textbooks/boelkins/)). UBC's Math Exam Resources wiki is not recommended. Its FAQ and About pages contradict each other on the license, and the exam questions themselves are not clearly covered ([FAQ](https://wiki.ubc.ca/Science:Math_Exam_Resources/FAQ); [About](https://wiki.ubc.ca/Science:Math_Exam_Resources/About)). CLP already includes many UBC exam problems under a clear license. The researcher's priority order for exam-level content:

1. CLP-1's starred and Stage 3 problems
2. MIT 18.01 exams
3. Japanese 数学III problems
4. OPL randomized drill
5. APEX, Active Calculus and OpenStax for coverage

The CLP LaTeX environment names were not inspected.

For **calculus-based physics**, three sources stand out:

- **MIT 8.01L** practice exams 1–3 and a final, all with solutions. "A typical 1 hour exam would contain 3-4 problems similar to those in the practice exams" ([8.01L](https://ocw.mit.edu/courses/8-01l-physics-i-classical-mechanics-fall-2005/pages/exams/)).
- **Crowell's** calculus-based *Simple Nature* ([Light and Matter](https://www.lightandmatter.com/area1sn.html)) and the Crowell–Shotwell *Problems in Introductory Physics*, which has solutions, an answer checker and LaTeX source ([Problems](https://lightandmatter.com/problems/)). Both say to check the PDF copyright page for licensing, which has not been opened.
- **OPL Douglas College** Particle Dynamics (929 files) and Statics (818).

OPL's BrockPhysics set (2,336 files) comes mostly from the *algebra-based* OpenStax College Physics. It uses legacy checkers and the now-deprecated `BrockPhysicsMacros.pl`, so it suits concept drill, not calculus mechanics ([OPL](https://github.com/openwebwork/webwork-open-problem-library)). No 8.02 exam source was verified. **Chemistry** remains thinnest. MIT 5.111 offers exams with solutions ([5.111](https://ocw.mit.edu/courses/5-111-principles-of-chemical-science-fall-2008/pages/exams/)). LibreTexts pages carry machine-readable license tags that must be filtered page by page ([LibreTexts](https://chem.libretexts.org/Courses/Remixer_University/LibreTexts_Construction_Guide_1e/03%3A_Basic_Editing/3.09%3A_Selecting_Copyright_for_Page_(Meta-Tags))). The OPL has essentially no chemistry. OpenStax Chemistry 2e stays the backbone, supplemented by science-track (理系) chemistry papers from the no-approval universities.

### Calculator and unit conventions differ by source

Several sources follow different conventions:

- **OpenStax** marks technology exercises with "[T]" ([OpenStax preface](https://courses.lumenlearning.com/suny-openstax-calculus1/front-matter/preface/)).
- **CLP-1** states calculator rules per problem, and in its notes "log x" means ln x ([CLP-1](https://personal.math.ubc.ca/~CLP/CLP1/clp_1_dc_problems.pdf)).
- **WeBWorK** evaluates trig in radians unless a problem loads `contextTrigDegrees.pl` ([pg](https://github.com/openwebwork/pg/blob/main/macros/contexts/contextTrigDegrees.pl)).
- **The Common Test** allowed-items list includes no calculator ([R8 notice](https://www.nifs-k.ac.jp/wp-content/uploads/2026/01/03_R8_%E5%85%B1%E9%80%9A%E3%83%86%E3%82%B9%E3%83%88_%E5%8F%97%E9%A8%93%E4%B8%8A%E3%81%AE%E6%B3%A8%E6%84%8F.pdf)).

The researcher's tagging rule follows from these. `calculator = required` applies to OpenStax [T] items, and `allowed-limited` wherever CLP says so. Everything else defaults to `no-calculator`, including CLP's starred problems, MIT exams and all Japanese problems. Angles default to radians, and degree problems get a flag. CLP cards carry a "log means ln" note. OPL problems built on `NumberWithUnits` or `FormulaWithUnits` route to the unit-aware checker.

## Sixteen items still need a test on the Mac or in the logs

| Item | Why it matters | How to settle |
|---|---|---|
| Does time-assigned Hard improve FSRS predictions? | Changes the fitted w15 | Compare optimizer log-loss with and without it on the user's own logs |
| Math-entry typing allowance | Speed fairness | Calibrate from logged entry times |
| Booster rule and allocation weights | No published deadline or multi-course algorithm | Simulate with `fsrs_rs_python.simulate` before trusting them |
| First-error tap accuracy | Sets blame weights | Track the probe confirmation rate; down-weight taps below 50% |
| LLM tagging accuracy on calculus | No published figure | 30–50-item stratified spot check per chapter |
| Cmd+Z, IME and clipboard in MathLive under pywebview | Input usability | Test in week one; override `keyDown_` if needed |
| PyInstaller collecting pywebview, uv Python plus PyInstaller | Packaging | Build a hello-world `.app` first; py2app and python.org Python are fallbacks |
| Bundle size and cold start | Confirms the stack choice | `du -sh` and time-to-first-paint on the first build |
| Blur and sleep detection in pywebview | Clock correctness | Page focus events or a PyObjC hook, plus a smoke test |
| launchd writing to iCloud Drive | Backups | First `kickstart` run; check the log |
| Renderer Docker build on arm64; throughput; legacy vs MathObjects share | OPL pipeline | Pilot `hello.pg`, then 100 files × 3 seeds |
| Anki `next_day_at` formula | Exact day numbers for replay | Compare replayed states against `cards.data` on a real export |
| fsrs-rs-python license | Only if ever shared | Ask maintainers or self-build the binding |
| FSRS-7 release | Better same-day modeling | Adapter interface; pin 0.9.3 meanwhile |
| Hokkaido and Kobe policies, Science Tokyo form, Osaka answers | Source coverage | Treat as permission-required until found |
| *Simple Nature* and Crowell–Shotwell copyright pages | Physics content license | Open the PDFs' copyright pages |

## Conclusion

The thread running through this round is that every signal a one-learner app reads is weaker than it looks. A response time, a self-diagnosis tap, an AI tag and a difficulty residual each carry real information. Each also mixes in noise that a large platform would average away across thousands of users. The design answer is the same in every case. Treat the signal as a screen, confirm it with a cheap, targeted check (a probe, a cued twin, a diagnostic set, a spot-check sample), and log how often the check agrees. The app then calibrates its own instruments: how reliable the user's taps are, how precise each skill's tags are, and whether time-assigned Hard helps FSRS. Those are numbers no published study can supply for this learner. The same logic explains the split between Recall and Level. Remembering a skill and performing it at exam pace and difficulty are different claims, they decay differently, and a grade goal needs both.

The engineering findings shift where the effort goes. Dropping QtWebEngine and CI removes the hardest packaging and signing work. The remaining risk sits in one small dependency, pywebview, that can be fenced behind an adapter and tested with a self-test. fsrs-rs-python makes parameter fitting, evaluation and retention optimization available from the first week, without PyTorch. That turns the earlier report's "wait about five weeks for 512 reviews, then re-fit elsewhere" into a routine weekly check, provided the cost model uses real problem durations rather than flashcard defaults. On content, Calc I is no longer constrained by supply. The binding constraints are physics and chemistry coverage and the per-problem cost of verifying and translating Japanese exam items. Those, not the scheduler, will set the pace of each later course's rollout.
