# Prompt: write one Calculus I section for the calc1 pack

Version 1 (2026-11-02). The standing brief for content writers. The task message names the
section, its deck and any special instructions.

## Read first, in this order

1. `docs/card-format.md`: the format. Follow it exactly.
2. `packs/calc1/skills.md`: the component map. Use only its IDs. Do not edit it unless your task says so.
3. `docs/design/calc1-component-map.md`: what each component means, and the notes for your section.
4. `docs/design/calc1-pilot-notes.md`: how the pilot section was built and checked, what the builder cannot catch, and the fixes for it. Avoid every pitfall listed there.
5. `packs/calc1/4-3-maxima-and-minima.cards.md`: the model file. Follow its structure, IDs, step tags, `wrong:` lines and templates.
6. The rule "Components must be distinct requirements" in `docs/card-format.md`, and #12 in `docs/design/model-assumption-audit.md` for why it matters.

## Write

One file, `packs/calc1/<section number with dashes>-<short title>.cards.md`, with the section's deck from `skills.md`. For each skill of the section:

- **One worked example** (`kind: example`).
- **Twelve problems,** across tiers 1 to 4, about 3 / 4 / 3 / 2:
  - Tier 3 is a typical exam question at a strong university.
  - Tier 4 is harder than the exam: multi-step, a less familiar setup, more than one idea. It is never olympiad material.
- **Variety:**
  - Mix the answer types.
  - Use templates where they give real variety, about 40% of problems.
  - Use static problems for setups that need careful wording.
- **Solutions:** numbered steps, each tagged with exactly one skill (the card's `skill` or one of its `uses`). `uses:` lists every other component the solution needs. Tag each demand once.
- **Wrong answers:** every tier 2+ problem has at least one `wrong:` line for a common error, pointing at the step where it happens (`@n`). These lines are the app's diagnosis.
- **No hints.** The app shows none: students learn from the textbook and from their own retries.
- **Units** wherever the problem has them (rates, optimization, physics settings). The numbers must be plausible for the setting.
- **Sources.** Each card is original, or adapted from one of these with the per-card source line and `modified: yes`:
  - OpenStax Calculus Volume 1 (CC BY-NC-SA 4.0);
  - CLP Calculus, UBC (CC BY-NC-SA 4.0);
  - APEX Calculus (CC BY-NC 4.0);
  - MIT OpenCourseWare 18.01 (CC BY-NC-SA 4.0).

  Never use any other textbook's problems, wording, figures or distinctive scenarios: Stewart, Thomas, Larson and the like are copyrighted.
- **IDs:** `calc1.<section, e.g. 4-1>.<name>.<nnn>` for static cards and `.t<nn>` for templates. They are permanent.
- **Flashcards, when a deck has definition or formula cards** (`docs/design/practice-research-analysis.md` §6):
  - a formula that is an expression gets a typed math `answer:`, so the app grades the recall;
  - a definition or theorem that must be self-graded lists its idea units on the back, one per line;
  - the front gives the situation or name and the back the formula or fact, which is the direction problems use;
  - every fact is paired with short problems that use it.

## Check until clean

- Run `uv run --no-sync python content-tools/mepack.py check packs/calc1 --katex /home/claude/tools/katex/node_modules/katex` until it reports OK. It checks the whole pack, so the other sections are included.
- Fix every error, and every warning except "no hints".
- Then read your file once end to end as a student would. Check the wording, the units, that the numbers make sense, and that each tier 3 problem looks like a real exam problem.
- Do not run `scripts/check.sh`: the machine is shared. The coordinator runs the full checks after merging.

## Deliver

- The cards file.
- `docs/design/calc1-<section>-notes.md`, with:
  - counts by skill and tier, and template instance counts;
  - a summary of the final check output;
  - the sources used;
  - components the map lacks (report them; don't add them);
  - your uncertainties.
- Commit both on your branch with the footer in AGENTS.md. Do not merge.
