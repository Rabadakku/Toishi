# Anki scheduler and study features (Anki 26.x with FSRS): audit checklist

Source note: GitHub release pages show day and month but no year. The years below come from Anki's YY.MM version names. At fetch time the latest stable release was 26.08.1 (5 Aug). 26.09b1 (25 Aug) and 26.09b2 (4 Sep) were betas ([releases](https://github.com/ankitects/anki/releases)). The manual is partly outdated. For example, it omits the descending-retrievability sort ([forum thread title](https://forums.ankiweb.net/t/descending-retrievability-missing-in-manual/71447)).

## 1. Card states, (re)learning steps and same-day reviews under FSRS

### Takeaway
Anki keeps its new, learning, review and relearning states, with step-based short-term scheduling, even when FSRS is on. The guidance is to use one or two short steps that finish the same day, or no steps at all (experimental), which lets FSRS handle same-day scheduling.

### Cited Findings
- **How steps work:** Good advances one step and Again returns to step 1. Hard on the first step gives the average of steps 1 and 2. With a single step, Hard gives 1.5× that step, capped at the step plus 1 day. On later steps, Hard repeats the current step. Easy graduates the card from any step. A step that crosses the day boundary is converted to days. With no relearning steps, a lapsed card gets a 1-day interval by default — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Queue priority:** Steps shorter than a day are shown as soon as they are due, ahead of reviews and new cards. They can also be shown up to 20 minutes early ("learn ahead", set in Preferences) when nothing else is due — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **FSRS advice on steps:** Keep steps under one day so they can be finished the same day. "23h is not recommended." The manual suggests 10m or 30m. With steps of a day or more, "FSRS may schedule the first review sooner than the last step, making Hard longer than Good." — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Experimental option:** Leave the steps empty and FSRS controls short-term scheduling, so Again may give 1 day or more — [Deck options](https://docs.ankiweb.net/deck-options.html). This was added in 24.11: "Let FSRS control short term schedule when no (re)learning steps are set" — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
- **Tutorial advice on steps:** Use a single step of 10, 15, 20 or 30m. Avoid strings of short steps such as "5m 10m 15m 30m". Steps over 12–14h are not recommended. If young-card retention is low, add 2h or 4h steps — [fsrs4anki tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
- **Same-day review changes:**
  - 25.02 disables the FSRS short-term scheduler "if w[17] or w[18] is zero" and fixes memory state not updating during relearning — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
  - 25.07 adds "FSRS-6", "simplified relearning steps logic with updated FSRS training API" and a fix so "FSRS-6 doesn't give <1d intervals" — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - 26.05 will "Prioritize previously-attempted cards in the intraday learning queue" and adds "unit tests for learning and relearning state transitions" — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
- **Conflicting source:** The tutorial says that for optimization "FSRS only takes into account one review per day" (the first review that day) — [tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md). That page still says Anki uses FSRS-4.5, so this statement is likely outdated for FSRS-5/6. **Unverified.**

### Inferences
- An app that schedules skills should match these behaviors:
  - Same-day repeats update the memory state through the short-term stability terms.
  - The first long interval comes from FSRS, not from a fixed graduating interval. The manual says SM-2-only options are hidden when FSRS is on.
  - Hard must never yield a longer interval than Good.

### Gaps
- I did not read the rslib state-machine code (`rslib/src/scheduler/states/`). The exact handling of Hard/Good/Easy for learning cards under FSRS when steps are present was not checked against the code.

## 2. Daily limits, queue building, display order and backlogs

### Takeaway
Under the v3 queue, cards are gathered in this order: intraday learning, interday learning, review, new. Review and new limits apply per deck and per parent. Interday learning cards count against the review limit. New cards stop once the review limit is hit, unless "New cards ignore review limit" is on. The documented default review sort is "Due date, then random". Descending retrievability is the option recommended for a backlog.

### Cited Findings
- **Limits:**
  - Each subdeck's limits cap what is gathered from it. The selected deck's limits cap the total.
  - There are three scopes: Preset, This deck, and Today only.
  - "New cards ignore review limit" is advised against when you have an overdue backlog.
  - With "Limits start from top", a parent's limits also apply when a subdeck is selected.
  - Interday learning cards count toward the review cap.
  - Unused new-card allowance does not carry over to the next day.
  - — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Display order:**
  - The options come from the selected deck, not from the card's own deck.
  - New gather order: Deck; Deck then random notes; Ascending position; Descending position; Random notes; Random cards.
  - New sort order: five variants.
  - New/review order and interday-learning/review order: Mixed, Before, or After.
  - Review sort: "Due date, then random (default)"; Due date then deck; Deck then due date; Ascending or Descending intervals; Ascending or Descending ease; Relative overdueness (SM-2); Ascending retrievability.
  - — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Descending retrievability:**
  - Added in 24.11. "Simulations have shown this is a better choice when you have a backlog… likely to become the default in the future" — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
  - 25.02 adds "More accurate sorting by R" and "Fall back to SM2 relative order when memory state missing" — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
  - 25.07 adds "Update sorting by R for FSRS 6" — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - 26.05 says "Make descending retrievability a pure R sort" — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
- **Community trade-off (Aug 2025):**
  - Descending R "gives the highest average retention (94.9%)" in a backlog. Ascending R gives the best efficiency.
  - Without a backlog, sort order barely matters ("just set it to random").
  - Interday learning order "doesn't matter unless you have steps that can't be finished in a day."
  - — [Forum](https://forums.ankiweb.net/t/which-is-the-most-recommended-display-order-for-fsrs/65483) (community posters, not developers)
- **Backlog tools:**
  - You can split a backlog into two filtered decks: `is:due prop:due>-7` and `is:due prop:due<=-7` — [Filtered decks](https://docs.ankiweb.net/filtered-decks.html)
  - FSRS Helper "Postpone" adds days to cards due today, chosen to keep "the deviation from the original review schedule … minimal". "Flatten" caps future reviews per day — [FSRS Helper](https://github.com/open-spaced-repetition/fsrs4anki-helper)
- **Insertion order:** In recent versions you should use Sequential insertion and control order through display order instead — [Deck options](https://docs.ankiweb.net/deck-options.html)

### Inferences
- Checklist for the app:
  - A review-limit-gates-new rule.
  - A backlog-aware sort with an R-based option.
  - Learning cards that bypass the limits.
  - Per-container limits plus a temporary "today only" override.

### Gaps
- I found no evidence that descending R became the default as of 26.x. The manual still says "Due date, then random".

## 3. Load balancer, easy days, fuzz, maximum interval, rescheduling, Postpone/Advance, siblings

### Takeaway
The load balancer (24.11) picks the least-loaded day within the fuzz range. In 26.05 it also spreads siblings apart, across presets. Easy days lighten chosen weekdays by nudging future intervals. "Reschedule cards on change" is off by default. Without it, a change to desired retention or the parameters only affects future answers. Postpone and Advance exist only in the FSRS Helper add-on.

### Cited Findings
- **Load balancer and easy days (24.11):** "Load balancing: within your fuzz range, Anki will now try to pick days that have fewer reviews waiting." "Easy days: you can now tell Anki to try avoid certain days of the week." The fuzz is also applied to SM-2 lapse intervals, which respect the maximum interval — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
- **Later changes:**
  - 25.02 fixes easy days causing the load balancer to "disproportionately schedule graduates to the furthest day" — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
  - 25.07 adds "Support load balance and easy days when rescheduling", "Fine-tune load balancer", "Make Load Balancer Optional", and a "'max interval too low' warning" — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - 26.05 adds "Improve sibling dispersal in the load balancer, including across presets", "Apply deck-specific load balancer settings to filtered deck study", "Ensure fuzz doesn't go backward during rescheduling" and "Don't reschedule suspended cards" — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
  - 26.08 says it "Avoided interval FSRS regressions from fuzz" (wording from the fetch summary) — [releases](https://github.com/ankitects/anki/releases)
- **Easy days:** The adjustment affects only future intervals, so current due counts don't change. Setting every day to Reduced gives the same workload as all Normal, because the weighting is relative — [Deck options](https://docs.ankiweb.net/deck-options.html). The Helper's version skips intervals under 3 days — [Helper](https://github.com/open-spaced-repetition/fsrs4anki-helper)
- **Maximum interval:** Default 100 years. At the cap, Hard, Good and Easy give the same delay — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Reschedule cards on change:**
  - Off by default. When on, it changes due dates, adds review entries, and is "not recommended" right after switching from SM-2 — [Deck options](https://docs.ankiweb.net/deck-options.html)
  - "By default… Future reviews use the new scheduling, so workload doesn't change immediately." The parameters and desired retention are independent, so changing retention needs no re-optimization — [tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
- **FSRS Helper:**
  - Postpone increases the intervals of cards due today. Advance decreases the intervals of undue cards; the tutorial calls it "preferable because it doesn't skew the grading history" (for example before an exam) — [tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
  - Disperse siblings: the auto mode "could cause constant queue rebuilding… breaks Display Order".
  - Schedule a break "will reduce future memory retention rates".
  - Easy days became built into Anki "after 24.11".
  - — [Helper](https://github.com/open-spaced-repetition/fsrs4anki-helper)
- **Sibling burying:**
  - Separate toggles for new, review and interday-learning siblings. Buried siblings move to the next day.
  - Later card types cannot bury earlier ones; types are gathered in the order intraday learning, interday learning, review, new.
  - — [Deck options](https://docs.ankiweb.net/deck-options.html)

### Inferences
- An app that schedules skills needs these pieces:
  - A fuzz range.
  - Load-aware day picking within that range.
  - Weekday weighting.
  - A rule that siblings or related skills are not due on the same day.
  - An explicit, opt-in mass reschedule that logs entries.
- Fuzz must never push an interval below the previous one, or below a shorter rating's interval.

### Gaps
- **Unverified fuzz ranges:** From memory of rslib `fuzz.rs`, not read this session: no fuzz under 2.5 days; then ±15% (2.5–7d), ±10% (7–20d), ±5% (>20d), plus 1 day.
- I did not find where the load-balancer toggle sits in the UI (Preferences or deck options).
- Anki has no built-in Postpone or Advance as far as found.

## 4. Leeches, suspend, bury, undo, set due date, reset, filtered decks and custom study

### Takeaway
Reviews done in a filtered deck count fully for FSRS when "Reschedule cards based on my answers" is on (the default). With it off, the deck is a preview with no effect on scheduling. Manual actions such as set due date and reset write "Manual" log entries with rating 0.

### Cited Findings
- **Leeches:**
  - The default threshold is 8 lapses; Anki then tags the note and suspends the card. Lapses are failures of cards in review.
  - Warnings repeat every half-threshold (12, 16, …).
  - Suspending is a setting. The fix advised is editing or rewording the card, not grinding.
  - — [Leeches](https://docs.ankiweb.net/leeches.html)
  - The FSRS simulator now "Consider[s] leeches" — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
- **Set due date:**
  - A range such as `60-90`. Review cards keep their interval unless `!` is added. Answer time is not recorded — [Browsing](https://docs.ankiweb.net/browsing.html)
  - With FSRS, the interval is set to the actual elapsed days — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - Manually scheduled cards with no reps are no longer treated as new — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
  - Review history marks these entries "Manual", rating 0 — [Stats](https://docs.ankiweb.net/stats.html)
- **Reset (Forget):** Moves the card to the end of the new queue. "The existing review history is preserved." Options to restore the original position and reset the lapse and rep counters — [Browsing](https://docs.ankiweb.net/browsing.html)
- **"Grade now":** A new action added in 25.07 — [25.07](https://github.com/ankitects/anki/releases/tag/25.07). Its exact behavior is unverified; it is likely grading cards from the browser.
- **Filtered decks:**
  - Suspended, buried, or already-filtered cards are excluded. Each card keeps its home deck.
  - Learning cards use the home deck's steps.
  - Rescheduling on: answers affect scheduling.
  - Rescheduling off: a "preview mode". Cards return "exactly as they started"; Again, Hard and Good have configurable delays and Easy removes the card.
  - Reviewing ahead uses a sliding scale and "is not appropriate for repeated use".
  - Under FSRS, relative overdueness uses R and the preset's desired retention.
  - — [Filtered decks](https://docs.ankiweb.net/filtered-decks.html)
- **Filtered decks and FSRS fixes:**
  - "Fix inconsistent retrievability calculations between normal/filtered decks" — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
  - Per-deck retention is now used in filtered decks — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
  - FSRS-only sort orders are hidden when FSRS is off — [26.09b2](https://github.com/ankitects/anki/releases)
- **Custom study:** Increase today's new limit; increase today's review limit (both change the current deck); review forgotten cards (Again within N days); review ahead; preview new cards; study by card state or tag (cram) — [Filtered decks](https://docs.ankiweb.net/filtered-decks.html)

### Inferences
- An early review counts as a real review. FSRS takes it in through low elapsed time and high R, which gives little stability gain. A "preview" or "practice" mode that does not touch the schedule is a separate feature worth having for an exam cram.

### Gaps
- I did not verify multi-level undo of answers in the manual this session. The details of FSRS memory-state handling after a reset were not verified.

## 5. Presets: what lives where, and how many

### Takeaway
FSRS on/off is global. Parameters, limits, steps and the default desired retention are per preset. Since 25.09, desired retention can also be overridden per deck. The advice is separate presets only for material that differs a lot in difficulty, re-optimized about monthly.

### Cited Findings
- **Global vs preset:** FSRS is global. The parameters are per preset; don't edit them by hand or copy them from others. "Optimize All Presets" exists. Once a month is enough. "Use separate presets for decks with very different difficulty" — [Deck options](https://docs.ankiweb.net/deck-options.html)
- **Per-deck desired retention:**
  - Added in 25.09, along with "Desired retention info graphs" and expected-workload calculation; memory state is recomputed when the deck's DR changes — [25.09](https://github.com/ankitects/anki/releases/tag/25.09)
  - DR and decay are cleared when a card changes deck — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - FSRS data is recomputed after a deck change — [26.09b1](https://github.com/ankitects/anki/releases)
- **Subdecks:** A subdeck's preset overrides its parent's. The alternative to fixed monthly optimization is to optimize at 512, 1024, 2048 reviews — [tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
- **Other per-preset FSRS options:**
  - "Ignore cards reviewed before" (dates in the future are disallowed in 26.09b2).
  - Historical retention (default 90%) fills gaps in review history.
  - The optimizer can be limited to a search.
  - — [Deck options](https://docs.ankiweb.net/deck-options.html); [releases](https://github.com/ankitects/anki/releases)

### Inferences
- An app that schedules skills should keep parameters per course or domain and allow a desired retention per skill group. It should recompute memory state when a card or skill moves between groups.

### Gaps
- I found no official numeric guidance on the number of presets beyond "different difficulty".

## 6. Statistics that build trust in the scheduler

### Takeaway
Anki's main trust signals are a true-retention table and the R, S and D distributions. The true-retention table counts the first review per day, with Again as fail and Hard/Good/Easy as pass, split into young and mature cards. True retention should track desired retention.

### Cited Findings
- **Today:** Reviews, Again count, percent correct, and breakdowns by Learn, Review, Relearn and Filtered — [Stats](https://docs.ankiweb.net/stats.html)
- **Future due:** Assumes no new cards and no failures and excludes cards already overdue. "Daily load" is Σ1/interval — [Stats](https://docs.ankiweb.net/stats.html). From 24.11: true retention stats, estimated total knowledge and daily load added, new cards excluded from Future Due, and backlog counted in today — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
- **Other graphs:**
  - Calendar, Reviews (by mature, young, relearn, learn, filtered), Card Counts, Review Time, Intervals, Hourly breakdown, Answer buttons.
  - Stability, Difficulty and Retrievability distributions (FSRS only).
  - "Estimated total knowledge" is average R × the number of cards reviewed at least once.
  - Mature means an interval of 21 days or more.
  - If true retention differs from desired retention, the advice is to re-optimize, use separate presets, deal with leeches, and use the answer buttons properly.
  - — [Stats](https://docs.ankiweb.net/stats.html)
- **Card info:**
  - A forgetting curve was added in 24.11 — [24.11](https://github.com/ankitects/anki/releases/tag/24.11)
  - Its future projection was added in 25.02 — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
  - R is computed from elapsed seconds since 25.07 — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - Memory state is updated when Card Info opens since 26.09b1 — [releases](https://github.com/ankitects/anki/releases)
- **Stats display:** Medians replaced some means in 25.07. Quantiles are used for R ranges in 26.05 — [25.07](https://github.com/ankitects/anki/releases/tag/25.07); [26.05](https://github.com/ankitects/anki/releases/tag/26.05)

### Gaps
- The exact time periods in the true-retention table (today, yesterday, week, month, year) were not confirmed.

## 7. Common mistakes, and how Anki nudges users away from them

### Takeaway
The worst mistake for FSRS is pressing Hard when you forgot. Anki now catches this with an optional health check during optimization and adds friction against hand-editing parameters.

### Cited Findings
- **Mistakes listed in the tutorial:**
  - Hard used for forgotten cards. FSRS adapts to most habits "except for one habit: pressing 'Hard' instead of 'Again'".
  - Choosing a grade by the interval you want instead of how easy recall was.
  - Changing rating habits.
  - Using scheduling add-ons.
  - Reviewing on clients without FSRS.
  - Desired retention above 0.97.
  - — [tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md)
- **Health check:** "Check health when optimizing" flags low review counts, Hard misuse, and not using Again when a card was forgotten — [Deck options](https://docs.ankiweb.net/deck-options.html). It replaced the Evaluate button in 25.07 — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
- **Other nudges:**
  - 25.07: the "max interval too low" warning and better desired-retention warnings — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
  - 26.05: "Require three left-clicks to unlock FSRS parameter editing" and the reworked "Help Me Decide" efficiency graph — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
  - Compute Minimum Recommended Retention was removed in 25.07 and replaced by Help Me Decide and workload simulation — [Deck options](https://docs.ankiweb.net/deck-options.html); [25.09](https://github.com/ankitects/anki/releases/tag/25.09)
- **Repair tool:** FSRS Helper's "Remedy Hard misuse" rewrites Hard to Again within a date range — [Helper](https://github.com/open-spaced-repetition/fsrs4anki-helper)

### Inferences
- An app where users grade their own problem attempts should do three things:
  - Define each grade clearly, especially "wrong = Again".
  - Hide or de-emphasize interval previews.
  - Run a health check on how grades are distributed.

## 8. Newer releases (2025–2026) relevant to scheduling

### Takeaway
The changes run from FSRS-6 (25.07) to per-deck desired retention (25.09), then refinements of the load balancer, sorting and filtered decks (26.05), and fsrs-rs 6.6.x (26.08 and 26.09 betas).

### Cited Findings
- **25.02 (Feb 2025):** Easy days reworked; simulator respects "new cards ignore review limit"; filtered decks selectable in stats; true-retention table UI — [25.02](https://github.com/ankitects/anki/releases/tag/25.02)
- **25.07 (Jul 2025):**
  - FSRS-6.
  - Grade now.
  - Load balancing and easy days applied when rescheduling.
  - Health check.
  - Set-due-date change for FSRS.
  - Simulator with load balancing, easy days and leeches.
  - — [25.07](https://github.com/ankitects/anki/releases/tag/25.07)
- **25.09 (Sep 2025):** Per-deck desired retention; DR graphs; expected workload — [25.09](https://github.com/ankitects/anki/releases/tag/25.09)
- **26.05 (16 Jun 2026):**
  - Pure-R descending sort.
  - Sibling dispersal in the load balancer.
  - Load balancing and per-deck desired retention applied in filtered decks.
  - Intraday learning prioritizes cards already attempted.
  - The custom scheduler is given card decay and desired retention.
  - — [26.05](https://github.com/ankitects/anki/releases/tag/26.05)
- **26.08 / 26.08.1 (Aug 2026):**
  - fsrs-rs 6.6.1.
  - Fuzz no longer causes FSRS interval regressions.
  - Check Database fixes wrong last-review times.
  - Set due date uses the FSRS config.
  - Fix for broken custom study and unbury links.
  - — [releases](https://github.com/ankitects/anki/releases)
- **26.09b1–b2:** FSRS 6.6.2 and the fixes listed above — [releases](https://github.com/ankitects/anki/releases)

### Gaps
- I could not confirm whether 26.09 final has shipped as of November 2026. AnkiMobile and AnkiDroid parity was not checked.
