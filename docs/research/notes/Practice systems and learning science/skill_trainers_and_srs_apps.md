# Practice trainers and spaced-repetition apps: mechanics, what users value, why people quit (as of Nov 2026)

Scope note: Anki and FSRS internals are skipped, per the brief. Research ran with a limited budget. Reddit, app-store review aggregates, AnkiWeb download counts, Brainscape, RemNote, Mochi, AlgoExpert, Exercism and Quizlet Learn could not be retrieved (see Gaps). Where a source is a competitor, a third-party mirror or a podcast summary, that is stated. Dates are given where known; "date unknown" means the page did not show one.

## 1. Chess trainers: Chessable MoveTrainer, Lichess and Chess.com puzzles, Aimchess

### Takeaway
Chess trainers split into three designs. Chessable uses move-level SRS with a learn-then-repeat loop and per-move levels. Lichess uses a rated-puzzle model (Glicko-2 for users and puzzles, themes, a dashboard, plus speed modes). Aimchess builds training from the user's own game mistakes. The most reusable ideas for a STEM practice engine are per-item difficulty ratings, theme-based weakness drilling, and puzzles generated from the user's own mistakes. Chessable gates its "difficult moves" tracking behind PRO, which suggests that feature is valued.

### Cited Findings
**Chessable / MoveTrainer**
- MoveTrainer is an SRS "designed specifically for learning chess moves". Lessons alternate commentary with quizzes at very fine granularity (one move at a time, then the whole sequence is repeated). Input is by moving pieces, so it can be auto-graded. Critique from the author: board-move prompts can't reinforce conceptual knowledge, a limitation shared with Execute Program. — [Andy Matuschak notes: Chessable MoveTrainer](https://notes.andymatuschak.org/zDr94hP6bG3jJYrdYy8B5hx)
- Review intervals per level are 4h, 1d, 3d, 1w, 2w, 1mo, 3mo, 6mo (Levels 1–8). Each move in a variation tracks its own level. A wrong answer on a late review resets the position to Level 1. Caveat: the page is on Chess.com's support site and the fetch described it as Chess.com's MoveTrainer. Chessable is owned by Chess.com, but I could not confirm the schedule is identical to Chessable's. — [Chess.com Support: how does the spaced repetition scheduling work](https://support.chess.com/en/articles/10319322-how-does-the-spaced-repetition-scheduling-work)
- Quiz loop: the trainer shows a move and asks you to repeat it. A miss shows the correct move and restarts the quiz. After a line is finished, all moves are repeated with emphasis on those missed (default 3 repetitions). Learn mode shows the line first, while Review mode hides it and reveals the move only after a failure. Options include "soft fail" for alternative moves, a think-time limit (default 60 s) and playback speed. — [Chessentials review](https://chessentials.com/chessable-honest-review/)
- The same reviewer praised short mobile sessions (about three sessions of roughly 15 minutes a day) and community comments on variations. He criticized streaks, badges and "rubies" as "social-media dopamine loops" that he finds less useful than MoveTrainer's scoring. Commenters raised cost ("course and video purchases add up") and difficulty navigating level tags. Single reviewer plus comments, not a survey. — [Chessentials review](https://chessentials.com/chessable-honest-review/)
- Chessable 3.0 added "Puzzle Connect" (link a Chess.com account and Chessable generates puzzles from your own mistakes; Basic gets 10 personalized puzzles, PRO up to 1,000) and "Priority Lines" (opening lines drawn from a database of millions of online games, so you study what opponents actually play). PRO also includes "tracking of difficult moves the user has trouble remembering" and a "customizable study schedule", plus offline mode. Article date unknown. — [Chess.com news: Announcing Chessable 3.0](https://www.chess.com/news/view/announcing-chessable-3)

**Lichess puzzles**
- Puzzles are mined from Lichess games and analyzed with Stockfish 12 NNUE at 40 meganodes. The design goal was a "single, crystal-clear solution", responding to user complaints. At launch there were about 650k puzzles. The set is free to download. — [Lichess blog: new puzzles are here](https://lichess.org/blog/X-S6gRUAAGjNX4ki/new-puzzles-are-here) (about 2020–21, from the Stockfish version; older)
- Each attempt is treated as a Glicko-2 "game" between user and puzzle (solve = win). Themed puzzles award fewer points because the theme acts as a hint. New puzzles are volatile until they settle, which takes "days, not weeks" at about 3M attempts per day. — [Lichess blog](https://lichess.org/blog/X-S6gRUAAGjNX4ki/new-puzzles-are-here)
- After each puzzle users give a thumbs up or down and vote on themes. Users are told not to vote on difficulty because the rating system handles it. Some themes are auto-detected and not votable. An "equality" category appears only on request. — [Lichess blog](https://lichess.org/blog/X-S6gRUAAGjNX4ki/new-puzzles-are-here)
- Third-party docs mirror of the lila source (secondary): "Angle Training" lets the user pick theme, opening, difficulty relative to rating (easier or harder), or mix. There are 100+ themes. Dashboard shows rating history and accuracy and solved counts by theme, strengths and weaknesses. Puzzle History allows re-attempting failed puzzles and data export. Puzzle Streak is unrated and continues until the first mistake, with rising difficulty. Puzzle Storm is 3 minutes with rising difficulty and daily, weekly and all-time leaderboards. Puzzle Racer is a race to 20 puzzles. — [Mintlify mirror of lila docs](https://mintlify.com/lichess-org/lila/features/puzzles)

**Chess.com Puzzle Rush**
- A coach's article says the clock runs, puzzles get harder, and the score is the number solved. He recommends 3–5 runs averaged and reviewing the positions for recurring mistakes. The evidence cited is entirely anecdotal (his own scores and students), with no studies. He never explicitly claims speed improves. — [Chess.com article: Improve Your Chess With Puzzle Rush](https://chess.com/article/view/improve-your-chess-with-puzzle-rush) (date unknown)

**Aimchess**
- Aimchess connects to Chess.com, Lichess or Chess24 and breaks games into Openings, Tactics, Endings, Advantage Capitalization, Resourcefulness and Time Management, compared with players at your level. "Adaptive Tactics" repeats puzzles you struggle with, and the Training Room has about nine exercise types (Retry Mistakes, Time Trainer, Intuition Trainer and others). Free tier: 15 lessons/day. Premium: $9.99/month or $71.99/year. App Store rating 3.9/5 from 196 ratings. — [App Store: Aimchess](https://apps.apple.com/us/app/aimchess-learn-chess-online/id1524941307)
- Reviews (praise): personalized to your own games, and "no ridiculous gamification or constant reminders about daily streaks". Reviews (complaints): no guidance on where to start ("a library rather than a classroom"); the opening trainer restarts the whole line after a mistake instead of stepping back one move; exercises don't always show a visible rating; an accidental tap on "next" instead of "retry" can skip a daily exercise; users want an infinite mixed-exercise mode. A handful of reviews quoted, not a systematic sample. — [App Store: Aimchess](https://apps.apple.com/us/app/aimchess-learn-chess-online/id1524941307)

### Inferences
- Lichess's design separates difficulty (rating learned from outcomes) from quality (votes) from selection (theme and relative-difficulty angle). A STEM problem bank can mirror this: per-problem and per-skill ratings learned from outcomes, plus a "flag this problem" signal that is not a difficulty vote.
- "Puzzles from your own mistakes" (Chessable 3.0, Aimchess Retry Mistakes) is the chess analogue of lapse-driven remediation. The equivalent here is that a lapse spawns a fresh variant of the same skill, not the identical item.
- The "difficult moves" feature being PRO-only, and Aimchess users asking for step-back retry and visible ratings, are signals that leech/difficulty handling and visible progress are valued. This is inference from product packaging and a few reviews, not usage data.

### Gaps
- Chessable's exact "difficult moves" algorithm (when a move is flagged, what drill it triggers) was not found in primary documentation. The only primary mention is the Chessable 3.0 PRO bullet.
- Chessable's drill/"Time Trial"-style modes and Smart Review could not be confirmed from an official source.
- r/chessable and Lichess forum sentiment, and Chess.com Puzzle Rush mode details (3 min / 5 min / Survival), were not retrieved.
- No independent study was found on whether Puzzle Storm or Rush improves over-the-board performance.

## 2. Coding practice: LeetCode, NeetCode, AlgoExpert, Exercism, Execute Program, Codewars

### Takeaway
Coding platforms are mostly "solve once, move on" lists. The visible demand for retention comes from users (LeetCode forgetting threads, third-party SRS tools), and NeetCode puts spaced-repetition reminders behind its Pro tier. Execute Program is the closest existing analogue to the Toishi, with typed answers, fresh machine-graded prompts and prerequisite-gated unlocking. Its lessons on false negatives from machine grading are directly relevant to math answer-checking.

### Cited Findings
**Execute Program**
- Prompts are machine-graded, and harmless typos were marking correct answers wrong. Because lessons unlock only after prerequisite lessons are successfully reviewed, these false negatives were frustrating. In early 2020 the policy changed: wrong attempts don't count as failures if the student eventually answers correctly, retries are unlimited, and the next review interval still grows on the normal schedule. A student can "give up" to see the answer, which shortens the item's interval like any forgotten item. — [Andy Matuschak notes: Execute Program missed answers](https://notes.andymatuschak.org/z4tavSGuFp6SDx5mrqeiseHEB7Q4G7H4KAdTV)
- The author notes that Execute Program has no non-executable prompts (every prompt is applied or executed), a contrast with Chessable-style recall of moves. Titles of related notes also say its prompts "act both as application prompts and recall prompts"; I read only the title. — [Andy Matuschak notes: Chessable MoveTrainer](https://notes.andymatuschak.org/zDr94hP6bG3jJYrdYy8B5hx)

**NeetCode / LeetCode**
- NeetCode 75 is a subset of NeetCode 150. The 150 spans 15 topics with 5–15 problems each, ordered easy to hard, with a video per problem. Suggested timelines are 3–4 weeks for the 75 and 6–8 weeks for the 150. Pro costs $119/year or $219 lifetime and includes an in-browser editor, progress tracking "with spaced repetition reminders", and extra courses. Spaced repetition is Pro-only. Criticisms: a curated list rather than a curriculum, friction between the NeetCode videos and LeetCode (no editor on free tier), and no mock-interview environment. Caveat: the review is published by a competing product (Lodely), so its criticisms are self-interested. — [Lodely: NeetCode review](https://www.lodely.com/blog/neetcode-review)
- A LeetCode forum poster with 400+ solved problems says they "often recognize that I've solved a problem before" yet struggle to recall "the key insight or pattern", and lack "a good system for retaining what we've learned long-term". Single post, with no replies retrievable. — [LeetCode Discuss](https://leetcode.com/discuss/post/8313816/am-i-the-only-one-who-forgets-leetcode-s-0or4/)
- A third-party developer's SRS-for-LeetCode tool uses intervals from about 1 day to about 1 month, scaled by difficulty, and highlights overdue problems. Its author claims mastering about 50 problems with 3–5 reviews each beats solving 200 once (author's claim, no evidence). — [Show HN post mirror](https://hn.svelte.dev/item/45436942)

**Codewars**
- Ranks run 8 kyu to 1 kyu, then 1 dan to 8 dan. Overall rank rises only the first time a kata is completed in any language, and per-language ranks rise separately. Completing the kata is the only way to rank up. Kata rank scores grow roughly 2.7x per rank (8 kyu = 2 points, 1 kyu = 1,097), and a kata two ranks above you yields about 30% progress versus about 5% for same-rank and about 0.3% two ranks below, so grinding easy kata earns little rank. A progress wheel shows percent to the next rank. — [Codewars docs: ranks](https://docs.codewars.com/gamification/ranks/)

### Inferences
- Execute Program's "eventual correct = pass, give up = lapse" is a tested answer to unreliable auto-grading. For math, CAS-based equivalence checking plus a retry policy would be the equivalent. Whether a retry should also downgrade the FSRS rating (Good vs Hard) is a design decision with no direct evidence.
- LeetCode users' "I recognize it but can't recall the insight" implies the schedulable unit should be the technique or pattern (skill), not the individual problem. That matches the plan for fresh problems per skill review, which also removes the "memorized the solution" failure mode.
- Codewars' rank-score weighting (easy problems earn almost nothing) is a way to discourage padding progress with easy work. It could inform how a "mastery level" is computed.

### Gaps
- AlgoExpert and Exercism (mentoring, concept vs practice exercises, track structure) were not researched; no sources retrieved.
- No data found on LeetCode quit rates. Search surfaced Blind and r/leetcode burnout threads, but I could not read them, so only the forgetting complaint is cited.
- Execute Program's exact interval schedule and its review volume were not found (its /spaced-repetition page returned metadata only).

## 3. Language and SRS apps: Duolingo, WaniKani, SuperMemo, RemNote, Mochi, Quizlet, Brainscape, Memrise, Orbit

### Takeaway
Duolingo has the richest published mechanics (Half-Life Regression for memory strength, Birdbrain for exercise difficulty) but its reported gains are engagement, not independently measured learning. WaniKani is the clearest example of stage-gated SRS with explicit penalty rules and is also the clearest documented case of backlog burnout. Orbit/Quantum Country provides the best published retention data on mnemonic-medium reviews. I could not retrieve Brainscape, RemNote, Mochi or Quizlet Learn details.

### Cited Findings
**Duolingo**
- HLR (Settles & Meeder, ACL 2016, pp. 1848–1858): recall probability p = 2^(−Δ/h) with half-life h = 2^(Θ·x). Θ is fit on large volumes of practice logs, and word features matter (cognates and short common words are easier). Duolingo reports the lowest error among tested methods (MAE 0.13, "nearly half" the Leitner error) and A/B-test daily retention gains of +9.5% (practice sessions), +1.7% (lessons) and +12% (overall activity). These are engagement metrics, not learning-outcome measures. — [Duolingo blog: how we learn how you learn](https://blog.duolingo.com/how-we-learn-how-you-learn); paper metadata: [ACL Anthology P16-1174](https://preview.aclanthology.org/landing_page/P16-1174) (2016; older)
- HLR drives skill-strength meters and the "weakest words" practice sessions. Stated principle: "the best time to practice is when you are on the verge of forgetting". — [Duolingo blog](https://blog.duolingo.com/how-we-learn-how-you-learn)
- Birdbrain estimates each learner's ability and each exercise's difficulty to predict correctness. The session generator uses it to choose exercises at the right difficulty. Duolingo claims A/B tests showed learners "learn more", are happier and return more, and that it personalized over 20% of lessons (up from near 0% in March 2020). No effect sizes given. — [Duolingo blog: Birdbrain](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain/) (2020; older)

**WaniKani**
- Nine SRS stages: Apprentice 1–4, Guru 1–2 (stages 5–6), Master (7), Enlightened (8), Burned (9, removed from reviews). Standard waits: 4h, 8h, 1d, 2d, 1w, 2w, 1mo, 4mo. Levels 1–2 use accelerated waits (2h, 4h, 8h, 1d). Review times are rounded down to the start of the hour. — [WaniKani Knowledge Base: SRS stages](https://knowledge.wanikani.com/wanikani/srs-stages/)
- A correct answer moves up one stage. Incorrect answers drop stages by ceil(incorrect count / 2) × a penalty factor (2 if the item is at stage 5 or higher, otherwise 1), with a floor of stage 1. Reaching Guru unlocks dependent items (kanji that use a radical, vocabulary that uses a kanji) into the lesson queue. — [WaniKani Knowledge Base](https://knowledge.wanikani.com/wanikani/srs-stages/)

**SuperMemo**
- Per Wikipedia: SM-2 (1987) through SM-17 (2016); SM-20 listed as 2026 (not verified elsewhere; SM-18 is not mentioned on that page). Self-graded recall on a 0–5 scale. Incremental reading since SuperMemo 10 (2000): import text, bookmark and schedule it, extract passages, turn extracts into questions. A priority system lets the user ensure the most important material is retained when they cannot review everything. — [Wikipedia: SuperMemo](https://en.wikipedia.org/wiki/SuperMemo) (secondary source)

**Memrise**
- Mechanics: leaderboard points for time and questions, SRS, user-made mnemonic "mems", user-generated courses with audio and pictures. The leaderboard was suspended in 2012 after "extensive cheating" with bots and non-learning tactics. The 2019 Decks split drew loud criticism and was reversed in 2020. Mems were removed in September 2022 with "overwhelmingly negative feedback". Community courses were sunset in 2023, and in 2024 moved to a separate site the app cannot access (no offline download). — [Wikipedia: Memrise](https://en.wikipedia.org/wiki/Memrise) (secondary; one "citation needed" claim about 2026 mem reintroduction not used)

**Quizlet**
- Freemium with ads and subscriptions: Quizlet Go (2017, later Plus); Q-Chat AI tutor launched 2023. The Wikipedia page did not describe Learn-mode adaptivity. — [Wikipedia: Quizlet](https://en.wikipedia.org/wiki/Quizlet)

**Orbit / Quantum Country (mnemonic medium)**
- Once a reader has demonstrated 5 days of retention on an item, the median reader's accuracy afterward is 95% (IQR 89–98%). The median by demonstrated interval is 95% at 2 weeks, 96% at 1 month, 97% at 2 months and 99% at 4 months. 82% of reader–item traces had zero lapses after the 5-day mark (97% after 4 months). Median reader had 8 lapses before reaching 5 days' retention, about as many as in the following half year. Caveats from the author: recall rates may overstate retention because cueing can mask forgetting. Sample sizes shrink with window length (N=129 for half-year traces, 53 for full year with every card), which implies attrition but the note does not quantify it. — [Andy Matuschak notes: Quantum Country five-day retention](https://notes.andymatuschak.org/z2Rv4RAjXUrwa3fMYn9Q1iR)

### Inferences
- WaniKani's penalty rule (drop deeper when a more mature item is missed, and by more when missed repeatedly) is a hand-built analogue of lapse handling. FSRS handles this natively, but the stage names (Apprentice → Burned) show that named mastery tiers are an effective user-facing layer on top of any scheduler.
- WaniKani's prerequisite unlocking (radical → kanji → vocab) matches Execute Program's prerequisite-reviewed unlocking and suggests a skill DAG for STEM, where a skill is introduced into the queue only after its prerequisites are stable.
- Quantum Country's data suggest items that survive the first few days rarely lapse. Most of the risk and effort is front-loaded, so the early short intervals deserve the polish (fast, low-friction first reviews), and long-run review burden can stay small.
- Memrise's history (cheating bots on leaderboards, backlash on removing a beloved feature, data stranded by an architecture split) is a cautionary tale for any leaderboard design and for data portability.

### Gaps
- Brainscape (confidence-based repetition), RemNote, Mochi, Quizlet Learn and SuperMemo's priority queue / SM-18 specifics were not retrieved (the Brainscape page failed to load, and RemNote/Mochi were not searched). Treat the brief's descriptions of these as unverified.
- Duolingo "practice mistakes" / Mistakes Review feature details were not retrieved.
- No independent test of Duolingo's learning outcomes was found (a search for a systematic review returned only low-quality repositories and theses).

## 4. What users value and hate, and Anki add-ons as a signal of missing features

### Takeaway
Primary user-voice sources (Reddit, app-store aggregates) could not be accessed, so this section rests on community forum threads, a few reviews and the contents of the most feature-rich Anki add-on. The consistent signals are demand for load smoothing, break handling, backlog recovery, transparent statistics, and personalized weakness targeting. The consistent complaints are guilt-inducing obligation, cost, and unclear starting points.

### Cited Findings
- FSRS4Anki Helper add-on feature list: Reschedule, Postpone, Advance, "Schedule a Break" (spreads cards due during an absence), Load Balance (small random interval changes to even out daily counts), Easy Days (fewer reviews on chosen days such as weekends), Disperse Siblings, Flatten (cap reviews per future day, postponing the excess), Remedy Hard Misuse, Steps Stats, plus display of memory state after answering, "true retention" statistics, a schedule visualizer, dataset export and a "Target R" browser column. — [GitHub: fsrs4anki-helper README](https://github.com/open-spaced-repetition/fsrs4anki-helper)
- Anki's deck options docs now describe Easy Days ("spend less time on Anki on some days of the week", works with FSRS and SM-2). They recommend sorting by relative overdueness (replaced by ascending retrievability under FSRS) for large backlogs, and advise stopping new cards "until you catch up with that backlog". — [Anki Manual: deck options](https://docs.ankiweb.net/deck-options.html)
- A Load Balancer PR (adapted from an older AnkiWeb add-on) picks a low-load day within the fuzz range, skips intervals over 90 days, and was explicitly proposed to start discussion of a native implementation. Reviewers worried that always choosing the least-loaded day biases cards toward the far end of their fuzz range, which could lower average retention. — [GitHub: ankitects/anki PR 3230](https://github.com/ankitects/anki/pull/3230). Exact release version in which Easy Days and Load Balancer shipped natively was not verified.
- Chessable's commenters: cost accumulates; level tags confusing; streak/badge/ruby gamification seen as dopamine loops. — [Chessentials review](https://chessentials.com/chessable-honest-review/)
- Aimchess reviewers: value personalization and specific weakness trainers; one explicitly values the absence of streak reminders; others want guidance on where to start, visible exercise ratings, and step-back retry. — [App Store: Aimchess](https://apps.apple.com/us/app/aimchess-learn-chess-online/id1524941307)
- Lichess's puzzle redesign was driven by user complaints about ambiguous solutions, leading to the "single, crystal-clear solution" rule. — [Lichess blog](https://lichess.org/blog/X-S6gRUAAGjNX4ki/new-puzzles-are-here)
- Execute Program users hit by false negatives from machine-graded typed answers drove a policy change. — [Andy Matuschak notes](https://notes.andymatuschak.org/z4tavSGuFp6SDx5mrqeiseHEB7Q4G7H4KAdTV)

### Inferences
- Add-on content is the best available proxy for "what the core scheduler lacked": breaks, load smoothing, easy days, postponing, backlog flattening, per-card diagnostic visibility, and true-retention stats. Several have since moved into core Anki (docs describe Easy Days and backlog sort orders), so a new app should ship these in v1 rather than leaving them to extensions.
- Review Heatmap, Image Occlusion and AnkiConnect were named in the brief as signals, but I could not retrieve download counts or pages for them. I cannot say anything about their relative popularity from evidence.

### Gaps
- AnkiWeb pages and listings returned no content (JavaScript-rendered or blocked); GitHub API access for star counts was denied. No add-on download numbers were obtained.
- r/Anki, r/chessable, r/leetcode, r/duolingo and app-store review aggregates were not accessed. Feature ratings by users in this section are therefore anecdotal.

## 5. Adherence: why people abandon SRS, what helps, and evidence on streaks and gamification

### Takeaway
The most-documented abandonment trigger is a review pile-up after a break, usually compounded by guilt and perfectionism. Documented countermeasures are mostly practitioner-level (caps, vacation modes, sort orders, stopping new items), while the strongest controlled evidence is thin: one large Peru RCT on streak highlighting (engagement up, learning effect only in a small tested subsample) and a meta-analysis showing small-to-moderate gamification effects that are least robust for motivation and behavior. Duolingo's own A/B results on streak freezes and goals are company-reported and engagement-focused.

### Cited Findings
**Drop-off causes (user and community voice)**
- WaniKani users report returning after 3–6 months to 600–1,600 reviews, and that "seeing the number killed motivation". Others describe guilt spreading to other tools (feeling they must clear WaniKani before returning to Anki or Bunpro), forgetting older items after a break, and going too fast (about 300 reviews/day). — [WaniKani community: tips for recovering from burnout](https://community.wanikani.com/t/tips-for-recovering-from-burnout/54043)
- An Anki forum proposal claims that students who miss 4–5 days return to hundreds of cards, and that "seeing a massive, unending wall of cards causes many users to give up on Anki entirely", attributed to mental fatigue. No data cited. The single reply notes young cards (not yet reviewed about 5–7 times) should be relearned from the start after a long break while mature cards tolerate gaps, and suggests fixed daily goals such as 10 new cards and at least 20 reviews. — [Anki forums: Backlog Recovery Planner proposal](https://forums.ankiweb.net/t/proposal-backlog-recovery-planner-to-prevent-user-churn-burnout/70487)
- A 12-year Japanese-learning Anki user quit citing duty and fear, old failed cards returning ("the ultimate fun killer"), perfectionism and anxiety, and diminishing returns of new cards (rare words rarely recurring in real immersion). One person's account, but detailed. — [Japanese Level Up](https://japaneselevelup.com/?p=26463)
- Duolingo's own blog says losing a streak after a single missed day can lower motivation and may lead some learners to avoid challenges to protect their streaks, and that long streaks give diminishing motivational returns (a 2→3 day streak is +50%, 200→201 is +0.5%). — [Duolingo blog: streak research](https://blog.duolingo.com/duolingo-streak-research/) (May 2024, modified Jun 2025)

**What helps (practitioner-level, mostly unvalidated)**
- WaniKani community remedies: vacation mode; reset a few levels; stop new lessons until reviews are zero; reorder reviews by SRS stage to work in small batches; set a cap you can hit "on your worst day, not your best" (suggested 25–100 per sitting); start with 5–10 lessons/day; rule of thumb that daily reviews settle near 10× daily lessons (one user's claim); mix in real-world use. — [WaniKani community](https://community.wanikani.com/t/tips-for-recovering-from-burnout/54043)
- Anki docs: relative-overdueness (or ascending-retrievability) ordering for large backlogs; hold new cards until caught up; Maximum reviews/day cap; Easy Days. — [Anki Manual](https://docs.ankiweb.net/deck-options.html)
- One blogger describes a fixed single-pomodoro daily Anki session to beat dread of a backlog. He rejected lowering the review limit as only hiding the problem and instead paused new material. Author concedes there is little data supporting pomodoro benefits. — [vslira blog via scour.ing](https://scour.ing/@tomasz/p/https://blog.vslira.net/2026/01/one-pomodoro-of-anki-day-is-enough-for.html) (Jan 2026; anecdote)

**Duolingo streak mechanics (company-reported; not independent)**
- Two Streak Freezes allowed at once raised daily active learners by +0.38% and did not increase skipping. A milestone animation raised 7-day continuation by +1.7%. Learners with a 7-day streak are 3.6× more likely to complete a course (survey data, causality not established). No sample sizes or methods given. — [Duolingo blog: streak research](https://blog.duolingo.com/duolingo-streak-research/)
- Podcast summary (third-party summary of a Duolingo retention PM interview; numbers unverified): tying the streak to one completed lesson instead of an XP goal drove a major engagement gain; two freezes beat one, three were no better than two; giving new users two freezes early raised retention; a free "earn back" of a lost streak by completing lessons in a window was a retention winner; too much flexibility on long streaks led users to take more time off; a goal that is too hard cost users streaks; pre-selecting a harder goal didn't help but user-chosen goals did; an eight-word explanation of how streaks and freezes work significantly increased retention; the team ran 600+ streak experiments over four years and shut down about half; streaks "should only be built once the core learning value works". — [Recall.it summary of Lenny's Podcast](https://www.recall.it/summary/lennys-podcast/behind-the-product-duolingo-streaks-or-jackson-shuttleworth-group-pm-retention-team)

**Independent evidence on streaks and gamification vs learning outcomes**
- RCT in Peru (Aulagnon, Cristia, Cueto, Malamud; NBER w34173, 2025): about 60,000 students in grades 4–6 on an online math platform randomized to streak highlighting, personalized reminders, generic reminders or control. Streak highlighting and personalized reminders raised platform use compared to generic reminders and control, with streaks stronger on intensive use and reminders stronger on extensive use (whether students used it at all). Streak highlighting improved math achievement versus control among students who took the endline test. Only about 1,500 took the endline test, and differences from the other treatment arms were not significant. — [NBER working paper 34173](https://www.nber.org/papers/w34173)
- Meta-analysis (Sailer & Homner 2020, Educational Psychology Review): gamification effects were cognitive g = .49 (k=19, N=1,686), motivational g = .36 (k=16), behavioral g = .25 (k=9). All were small but significant, and only the cognitive effect held in the high-rigor subsplit. Game fiction and combined competition + collaboration were moderators for behavioral outcomes. — [Springer: The Gamification of Learning: a Meta-analysis](https://link.springer.com/article/10.1007/s10648-019-09498-w)
- Leaderboards were gamed in practice: Memrise's was suspended after bots and non-learning tactics. — [Wikipedia: Memrise](https://en.wikipedia.org/wiki/Memrise)

### Inferences
- The key drop-off event is the return after a lapse in use, not the steady state. Designing the return experience (bounded workload, end-date forecast, relearning young items rather than grinding them) probably matters more than steady-state motivation features.
- The evidence supports "engagement and streak features increase time on platform and may improve learning where that raises practice volume". It does not support them as learning interventions in themselves. The Peru RCT's learning result is based on about 2.5% of randomized students taking the endline test, so selection could drive it.
- Streak freezes, user-chosen goals and earn-back are the mechanics with the strongest (company-reported) evidence of improving retention without raising skipping. They are cheap to implement in a local app.
- Perfectionism, anxiety and "obligation" in the Anki and Japanese Level Up accounts argue for a visible "done for today" state and soft, non-punitive language.

### Gaps
- No peer-reviewed study of SRS dropout or backlog effects was found. All "pile-up" evidence is forum and blog testimony.
- No independent quantification of Duolingo streak effects on learning (as opposed to engagement) was found.
- Streak "loss aversion" claims are asserted by Duolingo with no data.

## 6. Speed and fluency training: timed drills, Puzzle Storm/Rush, and real-performance transfer

### Takeaway
The best evidence concerns timed practice of basic math facts, not chess puzzles or STEM problem solving. It suggests timed practice can improve fluency when accuracy is established first and when combined with intervention. Evidence that timed drills cause anxiety is weak or absent in the experiments found, but the long-run evidence is incomplete. No evidence was found that Puzzle Storm/Rush improves real chess performance.

### Cited Findings
- Fuchs et al. (2013, as reported by Hechinger): struggling first graders tutored three times a week; one group did 60-second flashcard speed practice and another played untimed games. After 16 weeks the speed group had "much higher math achievement". Sample size and effect size not given in the article. The article says a What Works Clearinghouse expert panel rated evidence for timed activities within larger interventions as "strong" (27 studies), but also that Fuchs's is one of few direct timed-vs-untimed comparisons and replication is needed. — [Hechinger Report: do math drills help children learn?](https://hechingerreport.org/proof-points-do-math-drills-help-children-learn/)
- Same article: Baroody says timed tests can be effective if children first understand the concepts. Fuchs recommends students first show correct answers untimed and that teachers stop at errors for immediate correction. The Science of Math group says timed activities shouldn't start until a child calculates accurately and shouldn't count toward grades. It found only two experimental studies on timed tests and anxiety, neither concluding tests produce anxiety, while the article concludes the anxiety question "remains unknown". — [Hechinger Report](https://hechingerreport.org/proof-points-do-math-drills-help-children-learn/)
- Maki, Zaslofsky, Codding & Woods (Journal of School Psychology, reported by EdWeek Aug 2024): 113 grade 4–5 students did simple multiplication and harder 3-digit addition under overt versus covert two- or four-minute timing. No significant difference in self-reported anxiety. Harder problems produced more anxiety and fewer correct answers. Limitations: small sample, self-report, students may have assumed they were timed. — [EdWeek: Do timed tasks really worsen math anxiety?](https://www.edweek.org/teaching-learning/do-timed-tasks-really-worsen-math-anxiety/2024/08)
- NCTM position quoted in that article: "timed tests do not assess fluency and can negatively affect students". — [EdWeek](https://www.edweek.org/teaching-learning/do-timed-tasks-really-worsen-math-anxiety/2024/08)
- Puzzle Rush/Storm: coach's article recommends several runs and mistake review but cites no data. Lichess's Storm is 3 minutes with rising difficulty and leaderboards. — [Chess.com article](https://chess.com/article/view/improve-your-chess-with-puzzle-rush); [Mintlify mirror of lila docs](https://mintlify.com/lichess-org/lila/features/puzzles)

### Inferences
- Timed modes are justified only for already-accurate, automatable sub-skills (arithmetic, algebra manipulations, identities, unit conversions, derivative rules) and not for multi-step reasoning. The evidence base is K-5 arithmetic facts, so transfer to college STEM is an extrapolation.
- Safest design: an opt-in sprint mode per skill, with time recorded as a secondary signal that does not by itself reduce the schedule's grade. Accuracy-first gating is supported by Fuchs, Baroody and the Science of Math group.
- The immediate-correction recommendation is consistent with showing the worked answer right after an error.

### Gaps
- No controlled study on chess Storm/Rush, Codewars-style speed, or timed STEM problem solving beyond arithmetic was found.
- Effect sizes for Fuchs 2013 and the WWC panel's 27 studies were not retrieved.
- Boaler's specific claims were not retrieved (the sources found didn't quote her primary work).

## 7. Concrete recommendations for Toishi: adopt, adapt, avoid, and drop-off countermeasures

### Takeaway
Ship load control and a graceful return from a break in v1, make the answer checker forgiving, calibrate and show per-skill difficulty and accuracy, and keep gamification personal and soft (user-chosen goals, 2 freezes, earn-back). Keep timed modes opt-in and gated by accuracy. Avoid leaderboards, energy/paywall mechanics and any design that makes a missed day feel punitive.

### Cited Findings
(The findings supporting each recommendation are cited in sections 1–6. This section lists recommendations only, as inferences.)

### Inferences
**ADOPT (evidence-backed, low risk)**
1. Fresh problem per review via templates/generators, with the scheduler operating on the skill, not the item. Supports: Execute Program's applied prompts, LeetCode forgetting-of-insight posts, Matuschak's critique of recall-only prompts (sections 1–2).
2. Forgiving, CAS/equivalence-based typed answers with unlimited retries; "give up / show solution" counts as a lapse; correct-after-retry counts as a pass (consider a lower grade). Supports: Execute Program's early-2020 policy change (section 2).
3. Daily review cap, backlog-aware ordering (relative overdueness / lowest retrievability first), new-item gating tied to backlog size, Easy Days, and load balancing within the fuzz range. Supports: Anki docs, FSRS Helper feature list, Load Balancer PR, WaniKani remedies (sections 4–5).
4. "Schedule a break" / vacation mode and a return-from-break flow: show a workload forecast and projected clear date, allow a user-chosen recovery pace, relearn young items from the start while letting mature items resume. Supports: FSRS Helper "Schedule a Break", Anki forum proposal and reply, WaniKani burnout threads (section 5).
5. Per-skill accuracy dashboard (by tag/theme, with strengths and weaknesses) and a "drill my weak skills" session; "true retention" and per-card memory-state transparency. Supports: Lichess dashboard and Angle Training, Aimchess, FSRS Helper (sections 1, 4).
6. A "Retry Mistakes"-style remediation path: a lapse queues a fresh variant of the lapsed skill. Supports: Chessable Puzzle Connect, Aimchess (section 1).
7. Named mastery tiers per skill (e.g., Apprentice → Mastered) shown with progress toward the next tier. Supports: WaniKani stages, Codewars progress wheel (sections 2–3).
8. Prerequisite-based unlocking of new skills, with a "I already know this" override because the app is practice-only. Supports: WaniKani Guru unlocking, Execute Program (sections 2–3).
9. Users choose their own daily goal (minutes or items); default modest. Supports: Duolingo experiments (company-reported), Anki beginner advice (section 5).

**ADAPT (promising, needs care)**
10. Per-problem and per-user difficulty ratings (Glicko-2/Elo-style) used to select which variant to serve within a skill, separate from FSRS scheduling; hints reduce credit. Supports: Lichess, Birdbrain (sections 1, 3). Risk: needs enough local data; seed ratings from author-assigned difficulty. For one user the ratings will be noisy early on.
11. Streak/consistency feature: heatmap or weekly-goal consistency, 2 built-in freezes, earn-back, no loss-aversion language, no cross-user leaderboards. Supports: Duolingo freeze and earn-back (company-reported); Peru RCT (engagement ↑); gamification meta-analysis (small effects); Duolingo's admitted streak-protection avoidance (section 5). Keep it optional.
12. Timed sprint mode (opt-in per skill, only for fluent sub-skills, accuracy-gated, not counted in the main grade). Supports: Fuchs 2013, Science of Math/Baroody gating (section 6). Evidence is for arithmetic, not for college STEM.
13. Lichess-style problem flagging: a "bad problem / ambiguous answer" button that suspends or reports an item, distinct from difficulty feedback. Supports: Lichess votes (section 1).
14. "Retire" a skill after sustained mastery (WaniKani "Burned") but keep sparse maintenance checks, since Quantum Country data show lapses are rare after demonstrated retention but cueing may mask forgetting (section 3).
15. A guided default plan (the single daily queue already planned) plus an onboarding "where to start", to fix the "library, not classroom" complaint (Aimchess, NeetCode criticism).
16. Short-session framing: finish-line state and a suggested session length (3×15 min pattern in Chessable reports; pomodoro anecdote). Evidence is anecdotal.

**AVOID**
17. Leaderboards or any competitive social layer (Memrise cheating and suspension; irrelevant to an offline single-user app).
18. Paywalling or degrading core review features (Chessable PRO-only difficult-moves tracking and schedule, NeetCode Pro-only SRS, Aimchess 15-lessons/day cap). Free local app should avoid caps like this.
19. Restart-the-whole-sequence-on-one-error and easy accidental skips (Aimchess complaints). Provide step-back retry and undo for the last answer.
20. Strict single-day streak loss with guilt language; high streak counts with no flexibility (Duolingo's own admission of challenge-avoidance).
21. Removing or re-architecting user-visible features and stranding user data (Memrise mems and community courses). Keep a stable local data format and Anki import/export.
22. Pre-selecting aggressive goals for the user (Duolingo experiment: pre-selected harder goal did not improve retention).

**Main drop-off causes and countermeasures with the strongest evidence available**
| Cause | Countermeasures | Evidence level |
|---|---|---|
| Review pile-up after a break | Break scheduling, daily cap, overdue-first ordering, stop new items, recovery forecast | Community and docs; no controlled studies |
| Streak loss, guilt and perfectionism | Two freezes, earn-back, user-chosen goals, soft "done for today" state | Company-reported A/B tests; Duolingo's blog admits negative effects |
| Early dropout in week 1 | Low initial load, early freezes, a clear explanation of how streaks/freezes work, early wins | Company-reported (podcast summary, unverified) |
| Goals that are too hard | User-chosen goals with easier opt-outs | Company-reported |
| Boredom and obligation | Fresh problems, mixed queue, retiring mastered skills, using skills in real work | Anecdote (Japanese Level Up, WaniKani thread) |
| Old failed items irritating | Leech handling, relearning young items, a remediation path | Anecdote plus Chessable PRO feature |
| False negatives from machine grading | Equivalence checking, retries, give-up semantics | Execute Program policy change |
| Not knowing where to start | One daily queue and guided onboarding | A few reviews and a competitor critique |
| Cost and paywalls | Free local app | Comments only |

### Gaps
- None of the above has been tested on this app's population. All are inferences from other products' evidence, much of it company-reported or anecdotal.
