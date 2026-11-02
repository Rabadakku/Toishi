# Prompt: turn problems into a Toishi card file

Version 1 (2026-11-01). Use with any capable AI model. Attach three things to the conversation:

1. `docs/card-format.md` (the format; the model must follow it exactly),
2. the course's skill list (`skills.md`), so every tag comes from it,
3. the source problems, with where they came from and their license.

Paste everything below the line as the prompt, filling in the brackets. Afterwards, import the file
in the app: the importer re-checks every answer key with computer algebra and rejects anything
that doesn't parse or grade itself correct, and AI-made cards stay marked unverified until you
spot-check them.

---

You are writing practice cards for Toishi, a study app that schedules SKILLS and shows a
fresh problem for each review. Write ONE card file in the exact format of the attached
card-format.md. Output only the file, nothing before or after it.

Course and deck: [e.g. Calculus I::4 Applications of Differentiation::4.3 Shape of a Graph]
Source: [citation and URL, or "original"] — License: [e.g. CC BY-NC-SA 4.0]
Card ID prefix: [e.g. calc1.4-3.] — continue numbering from [e.g. 001]

Rules:

1. Header: `format: mastery-cards 1`, the deck, source and license above. Set `modified: yes` on
   any card you reword.
2. One card per problem. Every card has exactly one main `skill:` taken from the attached skill
   list, and `uses:` for other listed skills the solution needs (at most four). Never invent a
   skill ID; if none fits, write `skill: NONE` and explain in `### Notes`.
3. Difficulty: set `difficulty:` 1–5 from the tier table in card-format.md, judged by the steps the
   problem needs, not by feel.
4. Answers must be machine-checkable: pick the right `answer-type` and write the key in the plain
   answer syntax of card-format.md (exact values like `sqrt(2)/2`, `pi/3`; `^` for powers; `*`
   between letters; intervals with `U`; `DNE`, `inf`). Add `domain:` whenever an expression answer
   has logs, roots or absolute values. Use `self` only for proofs, sketches and explanations, and
   then give a `### Rubric`.
5. Only use a source's answer key if the source gives one; otherwise solve the problem yourself
   carefully and check the answer by substituting it back. If you are not sure of an answer,
   leave the card out and list it at the end inside an HTML comment `<!-- UNSURE: ... -->`.
6. `### Solution` is a numbered, step-tagged list: `0. [skill-id] Set up: ...`, then
   `1. [skill-id] Label: ...` for every step. Each step names exactly the one listed skill it uses.
   Step 0 is setting up or choosing the method.
7. Remove method cues from `### Question` ("Use the chain rule to…" → "Differentiate…"). Put the
   original cued wording in `### Cued Question`. If the method is part of what is asked (for
   example "use a left Riemann sum with n = 4"), keep it and set `cue: required`.
8. Add `wrong:` with up to three common wrong answers students really give, each with one short
   line of feedback and the step it comes from, e.g.
   `wrong: 3(x^2+1)^2 => The inner derivative 2x is missing @2`. Feedback can't contain `;`.
9. Add a `### Hints` list of two or three hints, mildest first; the last may give the first step.
10. Multi-part problems use `### Part a`, `### Part b`, … each with its own answer type and answer
    (and its own `skill:` if that part tests a different listed skill).
11. Set `calculator: yes` only when the problem truly needs one, and `angles: degrees` only when it
    uses degrees.
12. Math is LaTeX between `\(` `\)` (inline) and `\[` `\]` (display). Never use `$`.
13. Write every question in your own words unless the license allows copying; never copy exercises
    from commercial textbooks.
14. Where a skill would benefit, you may add a variant template card exactly as card-format.md's
    Variants section shows; its answer must be computed from the parameters, never typed.
