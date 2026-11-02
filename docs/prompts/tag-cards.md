# Prompt: tag existing problems with skills

Version 1 (2026-11-01). For problems that are already cards (for example an imported Anki deck) but
have no skills. It follows the procedure in the spec's "Tagging with AI" section: the model solves
each problem, tags each step, then confirms each tag with a yes/no question. Run it 3–5 times on
the same batch (a fresh conversation each time) and keep a main tag only if it appears in at
least 80% of the runs; send 40–80% to your review list and drop the rest. Spot-check 30–50 problems
per chapter before trusting the tags.

Attach the course skill list (`skills.md`, each skill with its definition, examples and near-miss
neighbor) and the problems. Paste everything below the line as the prompt.

---

You are tagging math problems with skills from the attached skill list for a study app. For EACH
problem, in order:

1. SOLVE: write a short numbered solution. Step 0 is setting up or choosing the method. If the
   problem has an answer key, your final answer must match it; if it doesn't, say so and stop on
   that problem.
2. CANDIDATES: list the 10–15 skills from the attached list (same course and chapter first) that
   could plausibly apply, plus NONE.
3. STEP-TAG: give each step exactly one skill ID from the candidates, or NONE.
4. VERIFY: for each distinct skill you used, answer YES or NO: "Does solving this problem REQUIRE
   <skill> as defined, as opposed to its near-miss neighbor?" Drop every NO.
5. RESULT: main skills = the skills of the key steps (at most 2); uses = the skills of routine steps
   (at most 4); a proposed difficulty tier 1–5 with a one-line reason; and any method cue in the
   question (words that name the method).

Output one JSON object per problem, one per line, and nothing else:

{"id": "<card id>", "main": ["skill-id"], "uses": ["skill-id"], "tier": 3,
 "tier_reason": "...", "cue": "Use L'Hôpital's rule" or null, "answer_matches_key": true,
 "steps": [{"n": 0, "skill": "skill-id", "label": "Set up"}]}

Rules: use only skill IDs that appear in the attached list, exactly as written; prefer fewer tags
over more (over-tagging is the most common mistake); never change the problem or its answer.
