# Wave 2 UI notes (W2)

2026-11-02 · the choices the page side made where `docs/design/wave2-integration.md` (v1.2) and the coordinator's v1.3 changes left room. W2 owns `web/` and the page tests in `tests/ui/`.

## The contract (section 6), as the page declares it

**Agreed with W1 through the coordinator:**
- `ProblemView.reason` stays the tag object (tag, label, why). The planner's reason code is `plan_reason` (section 6 had called it `reason`, a name already taken).
- `TodayView` keeps day, problems, minutes, flashcards, courses, exams, session_open, done_today, extra_practice_available and flashcards_to_rewrite. It adds the section 6 fields and drops proposals and vacation.
- Removed: `ProblemView.hints_shown`, `CardView.hint_count`, `SolutionView.needs_diagnosis` and `preselect_step`, and the `HintReveal`, `Diagnosis`, `DiagnoseRequest`, `WentWrongChoice` and `Proposal` types.
- A retry result carries no matched-wrong-answer feedback and no `wrong_step`.
- `SittingView.time_limit_ms` is the limit of the item's skill block: the sum of that skill's standard times in the sitting. `block_elapsed_ms` is the active time already spent on the block.

**Left as they were, because section 6 says nothing about them:**
- `Turn.lighter`: the page ignores it.
- `StartRequest`'s fields: only the `mode` union lost lighter and focused.
- `Summary`, including `ready_today`.
- `PartVerdictView.wrong_step`.
- `SolutionView`'s confident_error, can_mark_too_easy and textbook_ref.

**Layout:**
- The payload types stay in `web/src/lib/types.ts` with the existing ones; `bridge.ts` declares the methods.
- Section 6's inline shapes got names (`SkillsView`, `RefitBlock`, `Calibration`, `PlannedSitting`, `HoursBasis`, `Textbook`, `SittingView`). The JSON is the same.
- `course_settings_set` keeps the contract's `Omit<...>` signature on one line, so the method regex in `tests/test_app.py` finds it.

**How the page reads the open fields:**
- `first_try_counted` means "this answer was the item's first try". It is true for the first submission, and for a give-up before any answer; false for retries and invalid answers. The page uses it on one screen only: a verdict that is right on a later try says "Right on a later try. Only the first try counts."
- `can_retry`: Retry shows when the outcome is `retry` and `can_retry` isn't false. An older bridge sends no field and gets Retry. A `retry` with `can_retry: false` offers only Give up.
- `attempts_allowed`: the page no longer shows "Attempt N of M". The mock sends 0 for "no limit".
- **The set-aside notice** has no field of its own in section 6, so it travels in `Turn.message`. The page shows `Turn.message` as a note at the top of the card, kept until the next item; it used to vanish at the first keystroke. The mock's text is "Power rule is set aside for today. See OpenStax Calculus Volume 1 §3.3."
- **Planner notes and calibration labels** are shown as sent. The planner writes notes with skill ids and formulas ("(1 - 0.020) x 0.99^3.0 = ..."), so the bridge should turn them into plain words with skill names. Calibration labels should be words too ("Under 1 day", "1 to 7 days").

## Study screen

**After a wrong try** (coordinator v1.3): "Not quite", Retry and Give up, and nothing else.
- Submit and Not sure are hidden until Retry.
- Retry has the keyboard: Enter retries and G gives up.
- Any edit also counts as Retry: typing, picking a choice, the mode key, or clicking into a box.
- Retry gives the focus to the box that was active; on a multi-part problem the right parts stay settled.
- The page never renders a verdict's feedback or message on a retry, even if the bridge sends one.

**Give up and the solution:**
- Give up after a wrong try calls `study_give_up`. The page has no separate Show solution after a wrong try.
- The solution shows the matched wrong answer's feedback, the worked steps, and the card's other method in a closed "Another method" disclosure. The other method used to need the picker's "a different method" choice.

**MathLive sends Enter as an `input` event**, from a `setTimeout` after the answer is graded. That late event ended "Not quite" at once, and it started the next try's solve time at the Enter. `StudySession.setValue` now ignores a value that hasn't changed.

**The textbook line:**
- It sits under the problem text, in the problem's serif face, italic, with a book icon: `{book} §{section}`. A section that already starts with § isn't doubled.
- A closed-book sitting hides it: naming the section points at the method.

**Sittings:**
- A banner at the top of the card shows "Closed-book sitting", "Problem i of n", "Notes and textbook away. Nothing stops at the time limit." and "Time on this block: m:ss of m:ss".
- The block time is `block_elapsed_ms` plus the item's own active time, from the same clock that leaves pauses out. It updates every second. This is the one clock shown during a problem, per v1.3.
- Past the limit it says "Over the limit" with an icon and the warning color. Nothing is cut off.

**The stuck ladder** puts one line at the top of the card from `plan_reason`: "A smaller step first" or "A prerequisite first". It gives no explanation.

**Kept, though the new learner may not use them:**
- "Not sure" (Shift+Enter): the bridge still takes `confidence`.
- "Too easy": shown when the bridge sets `can_mark_too_easy`.

These are open questions for the owner.

**Removed:** `HintLadder.svelte`, `WhatWentWrong.svelte`, the H key, the Lighter set toggle, and StepSolution's "Likely" step, which only the picker used.

## Home

- **Roles:** small count-and-word marks: New, Building (growth), Review (maintenance), Check, Sitting. Each has a hint in its title.
- **Pace:** "About 6.5 hours a week keeps you on pace." The next line says where the figure comes from: your own practice, with the standard beside it; the course standard, which switches after about 10 certified milestones; or no pace data. Hours are rounded to the half hour.
- **Behind** links to Skills filtered to behind skills. Behind, set aside and sittings show the names the bridge sends.

## Course setup (`#/course?course=ID`, from the Library)

**Schedule:** three cards.
- From a start date.
- "My class is at a section today": a section select. `aligned.day` is the local calendar day, which can differ from the study day between midnight and the day rollover.
- Not set yet.

The anchor not chosen is sent as null.

**Without pace data** (`has_pace` false), the start, the alignment and the pace factor are hidden, and a note says why. The targets, the end date and the exams stay.

**Ranges:** accuracy 80 to 95% in steps of 1, tier 3 to 5 (named Exam, Challenge, Elite), pace factor 0.75 to 1.5 in steps of 0.05.

**Not on the page:**
- `keep_target` and `keep_tier` are sent back unchanged. The end-date hint quotes them.
- An exam's `target` isn't on the form; editing an exam keeps it.

**Exams:**
- The form asks for the name, the day and the sections it covers.
- Length in minutes and the number of problems are optional (rule 12: exam details come from the user, and a practice test uses the problem count).
- Sections are saved in course order.
- Delete removes an exam at once.

**Checks before saving:**
- A start date in date mode.
- A section in alignment mode.
- The end not before the start.

Bridge refusals show their message.

## Skills (`#/skills?course=ID&filter=behind`)

- **Data:** section titles and course order come from `course_settings_get().sections`, since `skills_get` gives only decks. A deck not listed comes last, titled by its last `::` segment. The course picker uses `library_get`.
- **Filter:** "Only behind (n)" works on the page; the URL parameter only sets where it starts.
- **Words:**
  - States: Not started, New today, Building, Reviewing, Keeping, Careless errors, Struggling.
  - Tracks: Ahead, On track, Behind, each with an icon.
  - Milestones: Homework level (M1), Exam level (M2), Target level (M3), Keep, always with the tier, the deadline when there is one, and a check plus "certified" for screen readers.
  - Level: "Tier 3".
  - First-try chance: the readiness as a percentage.
  - Speed: At pace, Slower than the standard time, or No timed first try yet.

## Student model (`#/model`, from Settings)

- **Parameters:** read-only, in plain words, with the values. Unknown keys appear by name. Two have a gloss: slip as a percentage, and τ as "about N times the standard time" (e^τ).
- **Refit report:** each block's held-out log loss before and after, its p value, and whether it was kept. The explanation doesn't quote the adoption thresholds, so it can't drift from core.
- **Reset:** an inline confirmation where Cancel has the focus.

## Routes and mocks

**Routes:** `course`, `skills` and `model` aren't in the sidebar, whose six entries are the spec's. The sidebar marks Library for course and skills, and Settings for the model.

**Mock switches** (only with `?bridge=mock`): `scenario=ladder|sitting` and `hours=history|standard|none`.

**The mock's ladder:**
- It counts first-try misses in a row over the skill's planned slots, and the ladder items in those slots count too.
- It rewrites the next slot (a smaller problem, then a prerequisite) and sets the skill aside at three.
- This is simpler than W3's planner and only exercises the page.

**Mock data:**
- Two courses: Sample Calculus has pace data; Sample Statistics doesn't.
- One exam and six skills.
- The model's priors are core.learner's `SharedParams`.
- A refit adopts the first time and keeps the current values after that.
