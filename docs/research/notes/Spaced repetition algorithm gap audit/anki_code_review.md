# Anki 26.09 scheduler code review vs Toishi (2026-11-01)

Anki paths are under `rslib/src/` in /home/claude/reference/anki. Ours are under /home/claude/toishi. FSRS formulas, the training filter, the adoption rule, fuzz constants and the load balancer are already in `agent-efficiency/fsrs_in_anki.md`, so they are only cited here. Every claim below was read in code.

## 1. Day boundaries

**Anki.** `sched_timing_today_v2_new` (`scheduler/timing.rs:27-55`) works in a `FixedOffset`:
- `next_day_at` is today's rollover hour, plus 24 h once that hour has passed (L39-45).
- `days_elapsed` counts calendar days since the collection was created, minus one before the rollover (L69-81).
- The result is cached until `now >= next_day_at` (`scheduler/mod.rs:35-48`). The offset is re-read from the OS on each build (L90-107).
- Due dates are stored as day numbers: `due = days_elapsed + interval` (`answering/review.rs:20`).

The FSRS Δt is `floor((next_day_at - last_review_time)/86400)` (`answering/mod.rs:504-511`, `timestamp.rs:31-33`). It is a whole number, and 0 means same day.

DST is approximate. On the night of the change, the rollover fires once at 3 or 5 AM. A review made within about an hour of the rollover, across a 23 h or 25 h day, can get a Δt one day off.

**Ours.**
- `study_day` takes the local date in an IANA zone and subtracts one day before the rollover (`core/storage/clock.py:271-275`).
- `day_start_ms` handles DST gaps and folds exactly (L282-296).
- "Same day" means the same study day (`core/engine/lifecycle.py:42-47`), which matches Anki's Δt==0 and is better than py-fsrs's 24 h blocks.

Two differences remain:
- **Long-term updates use fractional days.** `FsrsAdapter.review` feeds R(t) with t = (at - last)/86 400 000 (`core/engine/fsrs_adapter.py:102-111`). Anki and the fitter (`calibration.py:203`) use whole days.
- **`replay()` still uses the 24 h rule** (`fsrs_adapter.py:103,125-130`). That path builds every learned skill's first card (`lifecycle.py:195`) and also drives projections.
- **Past reviews move with settings.** The current zone and rollover hour are applied to every past instant (`user_store.py:266-271`, `lifecycle.py:89`), so changing either setting moves old reviews to different study days.

## 2. Answering

**Anki.** `card_state_updater` (`answering/mod.rs:465-552`) reads the preset's parameters and the deck's DR (L484). If a non-new card has no memory state, it rebuilds it from the revlog (L490-503). It then calls `fsrs.next_states(memory, dr, days_elapsed)` (L512-516). Short-term scheduling needs w17>0 and w18>0 (L522-534).

The state machine:
- **Learning and relearning with empty steps** (`states/learning.rs:39-195`, `states/relearning.rs:37-203`):
  - If the FSRS interval is under 0.5 d, the card gets an intraday step of interval×86400 s. A new card answered Again has S=0.212, so it comes back after about 5 h.
  - Otherwise the card goes to Review with `fuzz(round(I).max(1))`.
  - Easy is at least the fuzzed Good + 1.
- **Review, Again** (`states/review.rs:95-136`): interval = round(I(S'))≥1 with no fuzz (L80-84), or intraday relearning if it is under 0.5 d. Lapses increase only here.
- **Review, Hard/Good/Easy** (`review.rs:179-218`): hard ≥ max(1, mfi), good ≥ hard+1, easy ≥ good+1. `minimum_review_fuzz_interval` stops fuzz from shrinking the previous interval (`states/fuzz.rs:81-98`). The fuzz seed is card_id+reps (`answering/mod.rs:672-697`).
- **Leeches** (`review.rs:292-302`): the threshold is checked again every half threshold. The card is suspended (`answering/mod.rs:194-196`) and tagged (L361-363).
- **One transaction per answer** (`answering/mod.rs:321-394`):
  - cap the answer time (L330);
  - refuse if the card changed since the states were shown (L335-339);
  - write the revlog (L342);
  - bury siblings (L345);
  - set `last_review_time` unless the card was answered in preview (L349-354);
  - update the load-balancer cache (L365-376).
- **Stored per answer:**
  - Revlog row (`answering/revlog.rs:35-54`): id = answer time in ms, button, interval, last interval, `ease_factor` (= D+0.1 under FSRS, `card/mod.rs:126`), time taken, kind.
  - Card fields: S/D, DR, decay (`answering/mod.rs:185,489`), and `last_review_time`.

**Ours.** `grade_answer` (`core/engine/grading.py:173-434`) picks a stage: example, learning, reinforcement, stretch or review (L208-219). Then:
- **Learning:** the phase's (rating, time) pairs are replayed into a card once `correct_in_a_row` clean answers are reached (`lifecycle.py:175-229`). Their review events are written at pass time (`grading.py:296-301`). A failed phase is discarded with no events (L212-225).
- **Review:** `review_on`, then Again sets fsrs_state 3, due the next study day, plus an unrated reinforcement problem the same day (`lifecycle.py:244-292`).
- **Due dates are recomputed live** from S and today's retention, with a hash fuzz on (skill, last_review_at) (`lifecycle.py:81-96`, `fsrs_adapter.py:139-156`). There is no hard<good<easy floor and no previous-interval floor. The student never sees interval previews (ratings come from `rating.py`), so the ordering rule matters only for flashcards.
- **Flashcards** (`core/queue/flashcards.py:27-77`):
  - Again sets due to tomorrow, with no re-show in the same session (L46-47).
  - `lapse` counts any Again on a card with memory, including relearning and same-day Agains (L45).
  - The `leech` flag (L64) is never read anywhere.
- **Stored per answer:** the attempt, the state rows, and ReviewEvents (rating, rules_version, params_id, retention, predicted_recall, before/after FSRS fields) in one transaction (`core/storage/user_store.py:390-446`).

## 3. Queue

**Anki gathering** (`scheduler/queue/builder/gathering.rs:14-21`) runs in this order:
1. intraday learning, which ignores limits;
2. interday learning, then reviews, both against the **review** limit (L35-61);
3. new cards.

Siblings are buried while gathering (L136-169) and unburied at rollover (`bury_and_suspend.rs:32-49`). Limits are the preset limits minus today's counts, and new cards come out of the review limit unless "new cards ignore review limit" is on (`decks/limits.rs:94-115`). Changing a limit mid-day therefore takes effect on the next queue build. The R sort uses elapsed seconds (`storage/card/mod.rs:831-835`, `storage/sqlite.rs:313-370`). Overdue cards get no special treatment beyond sort order and limits.

**Ours.**
- Triage classes run check → relearn/redo → learning → prerequisite or escalated (>7 days overdue) → exam → review → new (`core/queue/triage.py:142-163`). The "recommended" sort is descending R (L55-61).
- Course quotas fill N; the effective count is N minus today's problems, and new-skill room is reduced by skills already introduced today (`planner.py:96-147`).
- Easy days, the flashcard limit, overdue measured against the live due date, and redo grading are covered in table rows 14, 9, 13 and 12.

## 4. Leeches, suspend/bury, undo, manual actions, filtered decks

**Anki.**
- **Undo** is a 30-step stack (`undo/mod.rs:15`). It restores cards, notes and tags, revlog rows, queue state and config (`undo/changes.rs:17-41`).
- **Set due date**, under FSRS, sets interval = days since last review + new days and logs a Manual row (`scheduler/reviews.rs:28-67,128-178`).
- **Forget** clears the memory state and logs a Manual row with ease 0, which cuts the history used for training (`new.rs:40-62,153-190`; `revlog/mod.rs:103-105`).
- **Grade now** answers cards outside the queue (`reviews.rs:180-205`).
- **Filtered decks:** a rescheduling deck counts its answers as real reviews. A preview deck changes nothing and leaves `last_review_time` alone (`answering/mod.rs:144-177,349-354`). Cram rows are dropped from training (`revlog/mod.rs:115-131`).

**Ours.**
- Undo restores exact row snapshots and voids the attempt, its review events and its credits. It refuses if the rows changed since (`user_store.py:530-580`).
- An older disputed answer "can't be taken back" (`session.py:2370`); nothing recomputes the state.
- Leech skill: memory is cleared and a new learning phase starts, with prerequisite checks (`lifecycle.py:276-291`).
- Every study mode rates. **Unanswered practice-test problems are rated Again by default** (`queue/config.py:61`, `session.py:2650-2715`), which on a core-band tier is a lapse with a review event.

## 5. Memory-state recomputation and parameter changes

**Anki.** Saving options recomputes memory for every non-new card in the affected decks when any of these change: FSRS on/off, parameters, DR, or easy days with reschedule ticked (`deckconfig/update.rs:264-316`). The recompute (`fsrs/memory_state.rs:83-258`):
- replays the filtered revlog;
- for a history whose learning rows were trimmed, infers a starting state from the first graded row via SM-2 conversion with `historical_retention` (L517-580; and L409-430 when no usable rows exist);
- recomputes due dates only if "reschedule" is ticked, keeping the minimum-interval floor and logging a Rescheduled row.

Moving a card to another deck also clears and recomputes its memory (`card/mod.rs:194-203`). Parameters are adopted only if their log loss is lower (`fsrs/params.rs:148-180`).

**Ours.**
- `Engine.fit()` saves the new parameters directly (`core/engine/service.py:367-373`). It never compares log loss against the current parameters.
- Stored S/D, computed under the old parameters, are kept. Due dates then mix the old S with the new decay w20.
- There is no replay-from-log function. The VoidReason "recompute" exists but nothing uses it.
- Fitted values are not clamped. `stored_parameters` (`calibration.py:240-247`) passes them to py-fsrs, whose `Scheduler` raises ValueError on any value out of bounds, for example a float32 0.8000000119 (see `fsrs_in_anki.md` §6). The error would surface in **every** `adapter()` call.
- `review_histories` (`calibration.py:179-209`) starts a history at each event without stability. All of a learning phase's events have that, so a phase that spans two study days is split into two histories.
- A RULES_VERSION bump drops the history prefix of every existing skill.
- Changing retention needs no recompute: due dates are live, and stored S does not depend on DR.

## 6. Guards

Anki clamps deck options (DR 0.70-0.99, maximum interval 1-36500; `deckconfig/mod.rs:227-312`), validates parameters in `FSRS::new`, caps S at 36500, and Check Database rebuilds ivl, due and `last_review_time` from the revlog (`storage/card/mod.rs:374-423`). Ours checks setting ranges (`settings.py:54-90`) and ReviewEvent values (`model.py:788-793`). SkillState accepts NaN S, D outside 1-10 and a future `last_review_at` (`model.py:553-560`), and there is no repair pass.

## Comparison table

| # | Area | Anki behavior | Our behavior | Verdict | Recommended fix |
|---|---|---|---|---|---|
| 1 | Rollover and DST | Rollover at local hour in a fixed offset, cached to `next_day_at`; can be one day off near DST (timing.rs:39-81) | Exact study days in IANA zone (clock.py:271-296) | Justified (ours more exact) | Keep; add a DST test for `review_on` same-day detection |
| 2 | Δt for the S update | Whole days, 0 = same day (answering/mod.rs:504-516); fitter uses whole days | Same day by study day, but long-term R uses fractional days (fsrs_adapter.py:102-111); fit uses whole days | Gap (inference does not match training) | Pass `t = days.between(last, now)` into R for the stability update; keep fractional R for display and sort; log both recalls |
| 3 | `replay()` same-day rule | One rule everywhere | 24 h rule (fsrs_adapter.py:103,125-130), used for every first card (lifecycle.py:195) | Bug (minor) | Give `replay` a `StudyDays` and route it through `review_on`; delete the `same_day=None` fallback |
| 4 | Interval ordering and fuzz floor | hard≥1, good≥hard+1, easy≥good+1; fuzz never shrinks the previous interval (review.rs:179-218; fuzz.rs:81-98) | Each rating independent; no previous-interval floor (fsrs_adapter.py:139-147); banker's rounding | Justified for skills (no previews); gap for flashcards | Pass the last scheduled interval into `interval_days` and apply Anki's `mfi` floor; use floor(x+0.5) for Rust rounding |
| 5 | Lapse handling | Empty relearn steps: Again → round(I(S'))≥1 d, no fuzz, or intraday if <0.5 d (review.rs:76-136) | Always relearn the next study day, plus an unrated same-day problem (lifecycle.py:90-91,266-275) | Justified (checks the skill on a fresh problem) | Document in ADR-0006 |
| 6 | Flashcard Again | Intraday relearn (new card back in about 5 h) (learning.rs:39-84) | Due tomorrow only (flashcards.py:46-47) | Gap | Re-insert a failed flashcard ≥5 items later in the session; rate it with the same-day short-term update |
| 7 | Flashcard lapse count | Only Review → Again (review.rs:95-97) | Any Again with memory (flashcards.py:45) | Bug | `lapse = rating==1 and state.fsrs_state==REVIEW and not same` |
| 8 | Flashcard leech | Tag plus suspend, repeating every half threshold (review.rs:292-302) | Flag set, never read (flashcards.py:64) | Gap | Skip `leech` rows in `_flashcards` (snapshot.py:355-362); show "needs rewrite" |
| 9 | Flashcard daily limits | New and review limits minus today's counts (limits.rs:94-115) | M per plan, not reduced by today's done; no separate new limit (planner.py:210-213) | Bug | Subtract today's flashcard attempts from M; add a `daily.new_flashcards` limit |
| 10 | Flashcard parameters | Per-preset parameters | Uses skill-fitted "math" parameters (service.py:77-86) though the fit excludes flashcards (calibration.py:126) | Gap | Give flashcards their own adapter: defaults until a flashcard fit exists |
| 11 | Unanswered test problems | Unseen cards are never rated | Default "again" → lapse, leech count, review event (config.py:61; session.py:2650-2715) | Bug | Default to "skip", or log as an unrated attempt with no ReviewEvent; keep the zero only in the test score |
| 12 | Redo of a missed problem | n/a | Same problem graded as a full FSRS review even when not due (triage.py:198-218) | Bug (memory of one problem inflates the skill's S) | Grade `purpose="redo"` like reinforcement (unrated) unless the skill is due, and then rate a fresh problem |
| 13 | Retention change → overdue | Due fixed at answer; a DR change moves dates only with "reschedule" (update.rs:264-316) | Live due with today's retention; overdue and escalation (>7 d) measured against it (schedule.py:50-62) | Bug (false escalations in exam windows) | Measure overdue against `due_at` cached at review time, or escalate on an R deficit; clamp moved-earlier dues to today |
| 14 | Load balancing and easy days | Weighted day choice in the fuzz range, ≤90 d; per-weekday easy days (load_balancer.rs:21-120) | None for reviews; easy days cut N, which creates backlog (snapshot.py:74-76) | Gap | Choose the fuzz day by `scheduled_load` × easy-day %; persist the chosen offset in `level_evidence` keyed by `last_review_at` (like `due_adjust`) |
| 15 | Gather order, limits, sort | Intraday → interday → review → new; limits minus today; R sort optional (gathering.rs:14-61) | Triage classes + quotas; N − done_today; descending R (triage.py:55-163; planner.py:96-147) | Same / justified | None |
| 16 | Siblings | Bury at gather and after answer, unbury at rollover | One unit per skill per day; one new cloze blank a day | Same in spirit | None |
| 17 | Undo | 30-step stack restoring card, revlog, queue, tags | Exact snapshot restore plus void; refuses after later changes (user_store.py:530-580) | Same / justified | None |
| 18 | Memory recompute | Replays the revlog on parameter/DR/preset change, card move, missing state; trimmed history → SM-2 start (memory_state.rs:83-258,517-580) | None; `fit()` keeps old-parameter S/D (service.py:367-373); "recompute" void unused | Gap (high) | `Engine.recompute_memory()`: per skill, replay non-voided `review_log` through `review_on` from the last fresh event, starting placed skills from the seed S; run after `fit()` and after voiding old attempts; one transaction |
| 19 | Parameter adoption and validation | Kept only if log loss improves; `FSRS::new` validates (params.rs:148-180) | Always adopted; no clamp → ValueError in `adapter()` (calibration.py:212-247) | Bug | Clamp to py-fsrs bounds (round to 6 dp first); compare in-sample log loss with the current set; on failure fall back to defaults |
| 20 | Training histories | Start at the first learning row of the last block; a Reset row cuts (params.rs:401-470) | Multi-day learning phase splits in two (calibration.py:196-206); failed phases log nothing; a RULES_VERSION bump drops prefixes | Bug / gap | Mark block starts explicitly (an event flag); log failed-phase ratings; keep old-rules events as prefix, train only on new-rules targets |
| 21 | Leech repair (skills) | Suspend or tag; memory kept | Clear memory, relearn, checks (lifecycle.py:276-291) | Justified | Fit already treats it as a fresh start; keep |
| 22 | Manual tools and preview | Set due date, forget (logs Manual), preview decks (reviews.rs:28-67; new.rs:40-62) | None; every study mode rates | Gap (low) | A "practice, don't schedule" toggle (attempt only, no ReviewEvent); a forget that writes a marker event |
| 23 | Data guards | Clamped options, S≤36500, Check Database rebuilds `last_review_time` (deckconfig/mod.rs:227-312; storage/card/mod.rs:374-423) | No S/D/time validation (model.py:553-560); no repair pass | Gap | Validate finite S∈[0.001,36500], D∈[1,10], `last_review_at`≤now in SkillState/FlashcardState; add a check that rebuilds FSRS fields from `review_log` |
| 24 | Partial credit (On mode) | n/a | Several credits a day compound from the already-credited S (credit.py:115-170) | Risk (shadow mode is the default) | At most one credit per target per study day |
| 25 | Zone or rollover change | Only "today" moves | Past reviews move to other study days (user_store.py:266-271) | Minor | Use the stored `Attempt.study_day` for past events, or document it |

**Not verified:** fsrs-rs-python's default for `enable_short_term` and its epoch count (Anki trains with 8 epochs), and whether the session can build a second daily plan the same day (that decides row 9's practical impact).
