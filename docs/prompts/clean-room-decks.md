# Clean-room decks: original problems inspired by copyrighted problem banks

Version 1 (2026-11-01). Turns problem banks you own (books you bought, school materials) into
**new, original** problems that can ship in the free app. Ideas, topics, problem types, methods
and difficulty are not owned by anyone; the wording, distinctive scenarios, specific numbers,
solutions and diagrams of a source are. So the work is split in two sessions that never share
source text:

| Step | Who | Sees the sources? | Produces |
|---|---|---|---|
| A. Blueprint | Session A | Yes | A blueprint (topics, problem types, steps, difficulty, traps, coverage) with no wording, numbers or diagrams from the source; plus one plain-text file per source problem for the checker |
| B. Write | Session B (a different conversation) | **Never** | Original card files, templates and diagrams in the Toishi format, written from the blueprint only |
| C. Check | Session A again (or you) | Only through the checker | `content-tools/similarity_check.py` flags any card too close to a source; flagged cards go back to B with the reason only |

This is not legal advice. Before the app is shared publicly, have someone qualified look over
this process (law school IP clinics sometimes do this for free).

## Folders

Create this once, outside the project folder (it must never be inside `<project folder>`):

```
~/Toishi Private/
  sources/        the problem banks (PDFs, scans, files) - legally obtained, never shared
  source-text/    Session A's plain-text copy, one problem (+ its solution) per file, for the checker
  blueprints/     Session A's blueprints
  drafts/         Session B's card files, one folder per course
```

Give each session only the folders it needs: Session A gets `~/Toishi Private`; Session
B gets `blueprints/`, `drafts/` and the project folder `<project folder>` (for the card format),
and **not** `sources/` or `source-text/`.

When a course's drafts pass the check, copy its folder to `<project folder>/packs/<course-id>/`
and tell Claude in the main session; it builds the pack, which re-checks every answer with
computer algebra.

---

## Prompt for Session A (blueprint)

Paste everything between the lines into a new conversation that has access to
`~/Toishi Private`. Fill in the brackets.

---

You are preparing a BLUEPRINT for a free study app, Toishi, from problem banks in
`~/Toishi Private/sources/[folder or file]`. The sources are copyrighted. Your blueprint
will be given to a different writer who must never see them, so it may describe only IDEAS:
topics, problem types, the steps a solution takes, difficulty, common mistakes and how often each
type appears. It must NOT contain any sentence, phrase, specific number, specific function,
distinctive scenario, name, solution text or diagram from the sources.

Course: [e.g. Calculus I (single-variable, early transcendentals)]
Course ID prefix: [e.g. calc1]
Scope: [e.g. chapters 2-4, or "all"]

Do this:

1. Read the sources in scope.
2. Write `~/Toishi Private/source-text/[course]/[source]-[problem number].txt` for EVERY
   problem in scope: the problem and, if the source has one, its solution, as plain text (math
   in plain notation). One problem per file. These files are only for an automatic similarity
   check and are never shared.
3. Propose the course's skills: one skill per distinct thing a student must be able to do (not
   per chapter). For each: an ID `[prefix].[area].[skill]` in lowercase with dashes, a name, a
   one-line definition in your own words, its prerequisite skills, and its "near-miss neighbor"
   (the skill it is most often confused with).
4. For each skill, list its PROBLEM TYPES. For each type give:
   - `type`: a generic description, e.g. "find where a cubic polynomial is increasing" or
     "related rates for a container filling or draining". Generic scenarios that appear in every
     textbook are fine; anything distinctive to one source is not (no named people, brands,
     unusual objects or stories).
   - `steps`: the solution steps in abstract terms (Step 0 = choose the method).
   - `difficulty`: 1-5 (1 = one routine step, 3 = several steps with one decision, 5 = hardest
     exam problems).
   - `answer form`: number, expression, interval, set of points, equation, proof...
   - `traps`: the mistakes students commonly make on this type.
   - `variation`: what can vary (kind of function, which quantity is unknown, sign cases...),
     without giving the source's actual values.
   - `diagram`: "none", or what a diagram must show in general terms (e.g. "graph of f with its
     local extrema marked", "right triangle with one angle and the hypotenuse labeled"). Never
     describe how a source drew it.
   - `weight`: how many problems of this type are in scope, and how many appear on past exams if
     the source includes exams.
5. Save the blueprint as `~/Toishi Private/blueprints/[course].md`: first the skills
   list, then the problem types grouped by skill, then a short coverage summary (counts per skill
   and per difficulty).
6. Self-check before saving: search your blueprint for any number, quoted phrase, proper name or
   formula taken from a source and replace it with a general description. A blueprint line like
   "differentiate f(x) = 3x^2 sin(4x)" is NOT allowed; "differentiate a product of a polynomial
   and a trig function with an inner linear argument" is.

Report: the number of problems read, skills proposed, problem types, and anything you were
unsure how to describe without copying.

---

## Prompt for Session B (write)

Paste everything between the lines into a NEW conversation that can see
`~/Toishi Private/blueprints/`, `~/Toishi Private/drafts/` and
`<project folder>`, but NOT `sources/` or `source-text/`.

---

You are writing ORIGINAL practice problems for Toishi, a free study app that schedules
skills and shows a fresh problem at every review. You work only from a blueprint. Do not open,
search for or ask about any textbook, problem bank, website or file other than the ones named
here; if you recognize a problem type, still write your own problem from scratch.

Inputs:
- Blueprint: `~/Toishi Private/blueprints/[course].md`
- Card format (follow it exactly): `<project folder>/docs/card-format.md`
- Card-writing rules (follow them): `<project folder>/docs/prompts/make-cards.md`, the rules
  after the line
- Example pack folders: `<project folder>/packs/test/`

Output: a pack folder `~/Toishi Private/drafts/[course-id]/` with
- `pack.json`: `{"id": "[course-id]", "title": "[Course title]", "version": "0.1.0",
  "license": "CC BY 4.0 (original problems written for Toishi)"}`
- `skills.md`: the blueprint's skills in the card-format "Skills and decks" format
- one card file per skill or section, header `source: original (clean-room, blueprint
  [course])` and `license: CC BY 4.0`
- `media/` with any diagrams

How to write:
1. Cover every problem type in the blueprint, in proportion to its weight, at its difficulty.
   Aim for at least 20 problems per skill per difficulty tier it uses, OR a template.
2. Prefer TEMPLATES (card-format "Variants"): one template card generates endless fresh
   problems with answers computed from the parameters. Use them wherever the type allows; that
   is what keeps students from memorizing answers.
3. Every problem is new: your own scenario, your own numbers and functions, your own wording.
   Do not try to recreate any problem you may have seen.
4. Follow every rule in make-cards.md: one main skill from the skills list, step-tagged
   solutions starting with Step 0, machine-checkable answers, `wrong:` answers from the
   blueprint's traps, two or three hints, no method cues in the question.
5. Diagrams: for graphs of functions use the card's `plot:` key (the app draws it). For other
   figures (triangles, containers, regions, vectors), write a small script that draws an SVG from
   the problem's own numbers and save it in `media/`; reference it as `![description](media/name.svg)`.
   Label everything the question refers to; keep it clean, black and white, readable at small size.
6. Solve every problem yourself and check each answer by substituting it back or by computer
   algebra. If unsure, leave the problem out and list it in `drafts/[course-id]/UNSURE.md`.
7. Finish with `drafts/[course-id]/REPORT.md`: problems and templates per skill and tier, and
   anything in the blueprint you could not cover.

---

## Step C: the similarity check

Session A (it already has access to the private folder) or you in Terminal runs:

```
cd <project folder>
python3 content-tools/similarity_check.py \
  --sources "$HOME/Toishi Private/source-text/[course]" \
  --drafts "$HOME/Toishi Private/drafts/[course-id]"
```

It prints only card IDs, source file names and scores, never source text. A flagged card is too
close to a source: 30% or more shared 5-word runs, a 12-word run in common, or all of its
question's numbers taken from one source problem. Send Session B only the flagged card IDs and
the reasons the checker gave (never the source), ask for a completely new problem for each, and
run the check again until nothing is flagged.

Then copy `drafts/[course-id]/` to `<project folder>/packs/[course-id]/` and tell Claude.

## Which model and effort for each session

| Session | Model | Effort | Why |
|---|---|---|---|
| A: blueprint and skills list | Opus 5.5 | medium | The skills list and problem types shape everything after them, and keeping the blueprint free of source details takes judgment |
| A: plain-text copies for the checker (`source-text/`) | Haiku 5.5 (as a helper agent, if the session can start them) | low | Mechanical copying |
| B: writing cards | Opus 5.5 | medium; high for templates and difficulty 4-5 | Solutions, hints and wrong-answer feedback must be right, and only the final answers are machine-checked later |
| C: similarity check | none (a script) | - | Run the command |

Fable 5.1 is stronger than Opus but costs much more; it isn't needed here, because the pack
builder re-checks every answer with computer algebra and you spot-check the rest.

## Efficiency add-on (paste after either prompt)

---

Work efficiently; tokens are limited:

1. Work in batches of one skill (or one textbook section) at a time. Read only the pages in that
   batch. Never load a whole book at once.
2. Keep `PROGRESS.md` next to your output: one line per finished batch (what, how many problems
   or cards, open issues). If this conversation gets long (roughly after 3-4 batches), stop, make
   sure PROGRESS.md is current, and tell me to start a new conversation; the new one resumes from
   PROGRESS.md without re-reading finished work.
3. Never re-read a file you already read in this conversation. Extract PDF text with a tool
   (e.g. pdftotext) instead of reading page images; look at a page image only when it has a
   diagram or math the text extraction garbled.
4. If you can start helper agents, give mechanical work (plain-text copies, file
   reorganizing, format checks) to a cheaper model (Haiku 5.5) with a short, exact instruction.
   Do the judgment work (skills, problem types, writing problems) yourself. At most 3 helpers at
   once.
5. Check answers by computation (a short Python/SymPy script over the whole batch), not by
   re-reading and re-reasoning each one.
6. Prefer one template that generates many problems over many hand-written fixed problems.
7. Stop rules: if you can't confirm an answer after two tries, put it in `UNSURE.md` and move on.
   If an instruction is unclear, write the question in PROGRESS.md and continue with the rest;
   never guess on content.
8. Keep chat messages short: a one-line status per batch with counts. Everything else goes in the
   files.

---
