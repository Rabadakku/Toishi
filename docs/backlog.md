# Backlog: found during hands-on testing

Items found by testing the real app on the Mac. Each one goes into the next milestone that
touches its area; strike it through when fixed (with the commit).

## App shell (app/)

- ~~**Local Network prompt (macOS 26).** Launching Toishi.app showed macOS's "find devices
  on your local network" prompt.~~ Fixed in wave5-integration (ADR-0012): pywebview's server ran
  `socket.getfqdn()` at bind time and `uuid.uuid1()` can fall back to `uuid.getnode()`, which
  resolves the Mac's own `<name>.local`; app/shell.py now binds 127.0.0.1 by number with random
  ids, and tests/app/test_local_network.py fails on any non-loopback lookup. Confirm on the Mac.
- ~~**Edit menu has no Undo / Redo items.**~~ Fixed in wave5-integration: Edit has Undo, Redo
  (sent to the first responder) and Undo Last Answer (QUE-15). Check Cmd+Z in the math field on
  the Mac (the page should still get the key first).

## Integration (from wave5-integration, 2026-11-01)

- ~~Flashcards from sections that are Off are planned and served (a fresh profile with every
  section Off shows "0 problems · 2 flashcards"). Spec: Off keeps a section's skills out of
  the queue. Core question for the queue.~~ Fixed in wave7-grading (ADR-0014): a flashcard's
  own deck section counts too (`CardRef.section_id`).
- Home has no forgiving streak yet (STA-1): TodayView carries no streak.
- The page doesn't preselect the step of a matched known wrong answer: PartVerdictView has
  the feedback but not the wrong answer's step. Core side done in wave7-grading
  (`PartVerdictView.wrong_step`, `SolutionView.preselect_step`); the page still has to use it.
- Choice parts don't say whether several options may be picked; the page offers one. Core
  side done in wave7-grading (`PartView.multiple`); the page still has to use it.

## From the UI wiring (2026-11-01)

- ~~Flashcards from sections that are Off are still served (queue).~~ Fixed in wave7-grading.
- TodayView has no streak, so Home has none (STA-1).
- ~~The matched wrong answer's @step isn't sent to the page, so the picker can't preselect
  it.~~ Sent in wave7-grading (`SolutionView.preselect_step`).
- ~~Choice parts don't say whether several options may be picked.~~ `PartView.multiple`
  (wave7-grading).
- ~~Card images show as "[figure: ...]": serve pack and user media from the app's own origin (ADR-0012).~~
  Fixed in wave8-anki-ui (ADR-0017): `/media/...` on the loopback server, `library_card_media`.
- Local Network prompt: fixed in app/shell.py (numeric 127.0.0.1 bind, random ids); confirm on the Mac.

## Grader integration (from the grader build, 2026-11-01)

- ~~`app/main.py` must call `multiprocessing.freeze_support()` and `core.grader.warm_up()` at launch;
  `shutdown()` on exit. The bridge passes `source="mathlive"` or `"text"`.~~ Done in
  wave5-integration (freeze_support stays first in app/__main__.py).
- ~~MathLive's `log` shortcut inserts an empty base box, so typing log(x) is invalid: override the
  shortcut in the page.~~ Done in wave5-integration (web/src/lib/math-shortcuts.ts).
- Spec MATH-4 and MATH-8 still say MathJSON; ADR-0005 chose MathLive LaTeX lowered into the one
  grammar. Update the spec text.
- Equation answers use the ratio test, so `sqrt(x)=2` vs `x=4` is marked different. Authoring rule:
  use `equation` only for lines and curves in polynomial-like form; use `set` for solutions.

## Storage schema v2 (needed by cards and diagnosis, 2026-11-01)

- ~~A column for template parameter sets on card instances (now stuffed into notes_md).~~
  Fixed in schema v2 (ADR-0011): card.params.
- ~~A home for the template source text of the student's own cards (now in the import log).~~
  Fixed in schema v2: user_template.
- ~~A per-profile user media store, so imported/own images can be stored and exported.~~
  Fixed in schema v2: UserStore.media (user_media + the profile's media/ folder).
- ~~A reason column on pending_check (now in the attempt's extra JSON).~~
  Fixed in schema v2: pending_check.reason.
- ~~The app must call core.cards.shutdown() and core.grader.shutdown() at exit.~~ Done in
  wave5-integration (app/main.py shutdown()).
- The editor (EDT-1) should use UserStore.media / StoredMedia; own images of cards imported
  under v1 are stored on their file's next import. ~~Images in cards still show as
  "[figure: ...]".~~ The app's image serving is `app/media.py` (ADR-0017); the CSP did not change.
- Unreferenced media files are kept forever (content-addressed, so older backups still find
  theirs); a clean-up that knows which backups are kept may come later.

## Engine (from the M4a build, 2026-11-01)

- ENG-11's calibration notice (a bin of 30 reviews off by 0.10) fires by chance on a well-calibrated
  model. Replace it with a test that accounts for sample size (e.g. a binomial interval per bin,
  or require 100 reviews) before the stats screen shows it.
- Deviations accepted for now (see ADR-0006): same day = same study day; a correct stretch
  problem counts as a normal review; Learned returns after 3 clean answers.

## Storage (from the independent review, 2026-11-01)

- Measure the per-commit cost of F_FULLFSYNC on the Mac (only tested on Linux by monkeypatch);
  one answer per commit should stay well under the 150 ms next-problem budget.
- The CAS worker must not fork while holding the profile lock (use spawn).
- Backup setting changes apply only after reopening; fine for 1.0, note it in Settings.

## Anki import (M7 core, ADR-0015, 2026-11-01)

- ~~Page: draw `anki-card` HTML (`is_anki_html`) instead of Markdown, re-sanitize with a DOM
  allow-list, set `anki-night` in dark mode, load each card's `data-anki-css` file and media
  through the media route (ADR-0012).~~ Done in wave8-anki-ui (ADR-0017).
- Queue: cloze rendering doesn't know nested or multi-ordinal clozes; use
  `core.importers.anki.cloze` (exact port of Anki's). It also marks the answer on a card's back
  with Markdown `**x**`, which shows as asterisks inside imported HTML (ADR-0017): render the
  back with `reveal_cloze_text` (`<span class="cloze">`).
- Check on the Mac (WebKit): an imported card with `[sound:...]` plays (the media route answers
  byte ranges), and a note type's own font and background load.
- Engine: `recompute_memory()` (the importer's hook) and per-source parameter sets; the
  import log's `summary.anki` lists the param sets and the items to replay (with SM-2 seeds).
- App: an import screen over `plan_anki_import` / `apply_anki_import`, with a pre-import backup.

## Verified on the Mac (2026-11-01, macOS 26.6.2)

- pywebview build: 43.2 MB, median launch 478 ms; Qt spike: 545.7 MB, 592 ms. Both self-tests pass.
- Dark mode followed; title does not overlap the window buttons; typing, Cmd+Z and Shift+Cmd+Z
  work in the math field.
- Not yet checked by hand: paste, dead keys (Option+E e), alert sound while typing.

### Hand test of the full build (2026-11-01, main at ce3cf91)

check.sh app on the Mac: 4144 core tests, 79 WebKit page tests, build and .app self-test all pass.
By hand: first-run name, Library "Learning now", a 4-problem session with a flashcard pair,
correct/wrong/Not sure/Hint/Give up, the miss picker, Edit > Undo Last Answer, quit and relaunch
(progress kept, no first-run screen) all work. Found:

1. **Give up is shown as a confident error.** After Give up the solution says "You marked this
   one as sure". `session._solution_view` sets `confident_error = not correct and not unsure`
   without looking at `gave_up` or the stage, while `grading.py` uses `stage in (review, stretch)
   and AGAIN and not unsure` (also counting a give-up). Spec ENG/miss flow: only a miss *submitted*
   sure is a confident error. Fix both; the view should use the engine's effect, not recompute.
2. **Give up after a wrong try shows "Your answer: No answer"** although "3" was tried. Show the
   last attempt (spec: the student's answer beside the correct one).
3. **The same problem is served again minutes after its solution was shown.** With a 2-problem
   pool, `pick_problem` relaxes "recently seen" down to zero, so a new skill's learning set was
   the same two problems twice, and the miss's "fresh problem" was the missed one. Never serve a
   card already seen in the current study day; if nothing qualifies, skip that slot. The learning
   phase (ENG-2) then needs min(3, distinct problems available) correct in a row, so a tiny pool
   can still finish, and the Library flags the skill's pool as too small. Imported and user-made
   decks will often have small pools, so this matters beyond the test pack.
4. **No worked example before a new skill's first problem.** ENG-2 says an `example` card, or
   else a tier 1 problem shown solved; with no example card the session went straight to a problem.
5. **Summary says "Tomorrow: 4 problems" while Home offers 4 more today** (the learning phase
   continues today, up to 8 problems). The summary should say more are ready today. The "To
   revisit" list shows the same skill twice; group by skill.
6. **The "What went wrong?" picker is below the fold** at the default window size, Continue is
   disabled, and the "Pick one to continue" note is hidden: it looks stuck. Scroll the picker into
   view after a miss.
7. Small: "About Toishi" appears twice in the app menu; Pause shows on the summary screen;
   clicking Hint takes focus out of the answer box.

## Product requirements added by the student (2026-11-01, in the spec as PACK-7..10, STA-11)

- Distributable: shipped packs only openly licensed/permitted content (license allowlist in the
  pack builder); personal decks import into a profile only and never ship; packs CC BY-NC-SA 4.0;
  fsrs-rs-python must be replaced or licensed before any public release (it declares no license).
- First run: choose subjects, then a placement test as the default first session (skippable).
- Weak areas screen: specific concepts with why they're listed, the prerequisite underneath, and
  links to open textbook sections, free videos and websites (`learn:` key in the skills file).
- Learning links (PACK-10): per course, first research which sources students and teachers widely
  recommend (learning-center lists, course pages, community FAQs); then per skill pick the specific
  video/page from those sources, verify it covers the skill, store title/source/URL/why; a
  content-tools link check at every pack build. App: a bridge method that opens only pack-provided
  https links in the default browser; links also on the solution screen after a miss.
- Mistakes: a "My mistakes" list of missed problems (your answer vs the right one, the step you
  tapped) the student can redo any time as unrated practice; the scheduler still re-serves each
  missed problem once, unrated, and rates only fresh problems (I4).

## Product direction (from the student, 2026-11-01)

- The app must work for anyone, any class, any STEM field; nothing tailored to one school or exam.
- Exams need a "calculators allowed" field and problem count/length entered by the user; exam pace
  (ENG-13) comes from those, not from defaults tied to one course.
- Later: English (grammar, spelling, reading comprehension). Likely needs: a shared passage shown
  with several questions, sentence-correction items (the find-the-error kind applied to text),
  typed spelling recall graded exactly, and a text answer checker separate from the math one.

## Concept sections ("Learn"), end of the roadmap (student, 2026-11-01)

The student wants short textbook-like sections for each concept inside the app, after the practice
core is done. Accuracy is the overriding requirement ("even small errors could be very bad"):
- Research first what makes the best textbooks effective (structure, worked examples, visuals,
  misconceptions, length) and turn it into a written style guide.
- Original text (or adapted CC BY material with attribution), never copied from commercial books.
- Every definition, theorem and claim checked against at least two reputable sources; every
  formula, worked example and graph machine-checked (SymPy, the pack builder); an independent
  fresh-context reviewer hunts errors; a qualified human reviewer signs off before shipping.
- Versioned, with an in-app "report an error" button and a public errata list.
- Sections link to the skills they cover; practice stays the core, and learn links (PACK-10)
  keep pointing to outside sources too.

## Photos of handwritten work (student, 2026-11-01)

Students may want to photograph their notebook work as they go (like Chinese study tablets that
read handwritten steps). Plan:
- 1.1 (with the mistake lifecycle): attach photos to a problem attempt or mistake; Continuity
  Camera ("Take Photo" from an iPhone) or a file; stored in user_media, shown beside the solution
  and in My mistakes. No recognition needed.
- Spike before any recognition feature: run offline, open-source math OCR models (candidates such
  as Pix2Text or TexTeller; licenses and sizes to check) on 20-30 of the student's real notebook
  photos. Measure lines read correctly. Only if line accuracy is high (about 90%+) build
  automatic step diagnosis: compare each recognized line with the worked solution's steps using
  the grader's equivalence check, and preselect the first step that differs in "What went wrong?"
  (the student confirms; a wrong auto-diagnosis must never be applied silently). Needs an ADR
  (a local model is not runtime AI in the cloud, but it is a large new dependency).

## Owner decisions to fold into the spec (2026-11-01, evening, during the full review)

1. **No AI anywhere in the app**, not even optional or bring-your-own-key: no tutoring, no reading or
   grading photos, no explanations. ("We are not making an AI tutor software.") Remove the optional
   cloud-AI ideas from the backlog and spec.
2. **Paper mock exams (with the exam layer, 1.1):** the app prints an exam built from the blueprint
   plus an answer sheet (corner markers, QR code per page, bubbles for multiple choice, digit grids
   for numbers, a short list of answers to type later). The student takes it on paper, scans the
   answer sheet with Continuity Camera "Scan Documents" (iPhone, no app needed) or AirDrop or
   drag-in, or taps the bubbles in the app instead. Bubbles are read by deterministic image
   processing (OMR, no AI); anything uncertain is asked, never guessed. Expression answers are typed
   and graded by the normal checker; long answers are self-scored with the rubric. A confirmation
   screen shows every read answer beside its cropped image before anything counts. Results become
   reviews (a miss stays a miss) and feed the lost-points analysis, readiness range and mistakes.
   Scratch-work photos can be attached to mistakes (no AI). No iPhone app (no Apple developer fee).
   Before speccing: research OMR accuracy from phone scans and paper-vs-screen practice effects;
   spike Continuity Camera in the pywebview window on the Mac.
3. **"Walk me through it" guided redo: dropped** (Later, only if data shows the same misses
   repeating). Keep the tap with its check problem; add the automatic "likely cause" from the card's
   coded wrong answers plus shared mistake patterns per topic; add control probes so the app can
   measure whether taps carry information.
4. **Content cost rule:** no course is mass-produced until a pilot section has measured tokens per
   card and the error rate. Templates first, the right model per job, answers checked by computer
   algebra, sampled audits instead of reviewing everything twice, shared patterns reused.
5. **Worked solutions must be machine-checked** too (the cheapest form that works), not only final
   answers.
6. **Chart text descriptions (WCAG 1.1.1): end of the roadmap.**

## Content strategy (owner, 2026-11-02, 13:19)
- The owner will make **no private decks**. The coordinator makes all decks, and everything shipped must be shareable. The clean-room workflow for private banks (docs/prompts/clean-room-decks.md) is no longer needed; keep it archived for reference.
- Packs are built from openly licensed sources (CLP, OpenStax, WeBWorK OPL, APEX, MIT OCW, ...) plus original problems, with per-card source and license (Calc I: CC BY-NC-SA 4.0).
- **Open-source decks** from Anki or other programs may be included: history, medical and so on, or math/engineering flashcard decks to pull definitions from or to seed problem sets. Only decks with an explicit license that allows redistribution qualify (CC0, CC BY, CC BY-SA, or NC variants, since the app is free). Most AnkiWeb shared decks state no license, and medical decks often contain copyrighted images, so each deck needs a license check. Research this after Calc I ("everything else" phase), unless the owner reorders.
- Crowded-day smoothing (owner question 13:17): steady inflow of new skills across a section's days, early-only load balancing (≤10% of the interval, ≤7 days), compression via problems covering several due skills, and a future-due heat map in stats (polish). See docs/design/student-model-working-notes.md.

## Model controls and Anki parity (owner, 2026-11-02, 14:30–14:42)
- **Refit schedule: on evidence, not the calendar** (owner asked why "every 14 days"; there was no reason). First refit at 150 first tries (30 held out), then whenever the log has grown by half since the last refit or by 1,000 attempts, and at once when calibration in the large of the predictions since the last refit is off by more than 3 standard errors. Built in core/learner/refit.py (`refit_due`, `calibration_drift`); the adoption rule is unchanged, so extra refits can't make predictions worse.
- **Refit now** button (wave 2 UI): runs the refit at once and shows the report: held-out log loss before and after, calibration by tier and by gap, kept or not. Same adoption rule.
- **Anki deck-option parity**, from docs.ankiweb.net/deck-options.html (2026-11-02):
  - Already specified: desired retention (flashcards) / accuracy target and target tier (courses); maximum interval; Easy Days; load balancer; leeches; suspend; undo; browse.
  - Wave 2: Optimize and Evaluate buttons; which decks feed a fit; "ignore attempts before" a date; the parameter view with Reset to defaults; Reschedule cards on change for flashcards (courses re-plan from predictions every time, so a new target applies at once); the Simulator and "Help me decide" as a minutes-per-day forecast for the rest of the course at a chosen target and tier (the future-due heat map); historical retention for imported Anki history; bury siblings, display order, timers and auto advance for flashcards.
  - Not doing: custom scheduling JavaScript (no user code runs, AGENTS rule 15); SM-2 options (FSRS only); sort orders for problem courses (interleaving is the point; flashcards keep them).
- **Opt-in "Export my practice log"** (later): the only way to pool data without a sync server. Packs are public, so pooled logs line up problem by problem: per-problem difficulty and population priors, which Anki can't do. Card content is never needed in the export.
- **Distribution notes** (owner asked how people will get it): start small (one class or a tutoring center), then r/Anki, r/learnmath, r/calculus, r/EngineeringStudents, Show HN. Hosting without GitHub: Cloudflare Pages + R2 or Codeberg. Without the Apple Developer Program, macOS 15+ blocks the first launch (System Settings → Privacy & Security → Open Anyway); the download page needs a three-screenshot guide, and notarization is the first spend worth considering once there are users.

## Content: precalculus geometry first (owner, 2026-11-02, 16:02)
- The owner often forgets geometry definitions. A precalculus geometry section comes first in the content queue, alongside Calculus I Chapter 4, because related rates (4.1) and optimization (4.7) lean on it:
  - area and perimeter;
  - volume and surface area of prisms, cylinders, cones, spheres and pyramids;
  - similar triangles and proportional sides;
  - the Pythagorean theorem, special right triangles and the distance formula;
  - circle arcs, sectors, chords and inscribed angles;
  - angle facts.
- Each item is a free-recall definition or formula card plus short problems.
- The items become background components (`pre.geo.*`) that the Calculus I problems use.

## Learning design proposal (owner, 2026-11-02, 16:01; awaiting the owner's yes)
- The owner's view: learn the concept from a textbook, lecture or video; in practice, no tutoring, no help, no explanations; extreme difficulty is fine; long struggle is fine; open book.
- The proposal sent to the owner:
  - no hints or explanations in the app; each problem names its textbook section;
  - wrong means try again, any number of times, with no time cutoff; the solution shows only on give-up, which counts as a miss;
  - new skills start with a problem, with worked examples as optional reference;
  - after 3 misses in a row, point to the textbook section and the blamed prerequisite (no explanation);
  - open book while learning; closed-book timed sittings certify M2 and M3;
  - an optional harder growth band (50–75%).
- Evidence cited:
  - Cambridge example sheets followed by supervisions;
  - productive failure (the gain needs consolidation after the struggle);
  - wheel-spinning in tutoring-system logs (Beck & Gong 2013);
  - desirable difficulties require eventual success (Bjork & Bjork 2011).
