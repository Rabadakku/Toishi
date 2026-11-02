# ADR-0005: MathLive answers reach the checker as LaTeX, lowered to the plain syntax

- Status: Accepted
- Date: 2026-11-01

## Context

The study screen takes answers two ways: plain text in the card's answer syntax (MATH-5)
and the MathLive math field (MATH-4). The spec assumed MathLive "outputs MathJSON" that a
second whitelist translator turns into SymPy (MATH-8). M3 had to choose between:

- **(a) MathJSON**: bundle `@cortex-js/compute-engine`, read `mf.expression`, translate the
  MathJSON tree with a whitelist; or
- **(b) a MathLive serialization** (ascii-math or LaTeX) fed through the same grammar as
  plain text.

## Evidence

All readings below come from the installed `mathlive` 0.111.4, typed with real keystrokes
into a fresh `<math-field>` in Chromium by `tests/grader/make_mathlive_fixtures.py`
(output: `tests/grader/data/mathlive_fixtures.json`, 57 cases).

1. **MathLive alone cannot produce MathJSON.** Its `OutputFormat` type
   (`types/core-types.d.ts`) has no `math-json`; `MathfieldElement.computeEngine` builds one
   only from a `ComputeEngine` constructor on `globalThis`. Option (a) means bundling
   `@cortex-js/compute-engine` (0.175.0: 26.3 MB unpacked, per `npm view`), which parses
   LaTeX with its own reading rules and canonicalizes what it builds. That is a second
   parser: the same answer could read differently in the two input modes, and the
   unsimplified tree that `form` checks need (lowest terms, factored) would be gone.
2. **ascii-math is lossy.** From the fixtures:

   | Typed | `latex-unstyled` | `ascii-math` |
   | --- | --- | --- |
   | DNE | `DNE` | `D N E` |
   | none | `none` | `n o n e` |
   | 3 1/2 (mixed number) | `3\frac12` | `3(1)/(2)` (same as 3·(1/2)) |
   | sin² x | `\sin^2x` | `sin ^2x` |
   | ∅ | `\emptyset` | `O/` |
   | √x/2 · sin x | `\frac{\sqrt{x}}{2}\sin\left(x\right)` | `(sqrt(x))/(2)sin (x)` |

3. **LaTeX is the field's own model and keeps every distinction above.** A short,
   structure-only rewrite (groups, `\frac`, `\sqrt[n]`, `\left…\right`, matrices, a
   whitelist of commands) turns it into plain syntax with explicit parentheses; the 57
   fixtures and 30 more cases in `tests/grader/test_mathlive.py` pin each reading.

## Decision

Option (b) with LaTeX. The page sends `mf.getValue("latex-unstyled")` with
`source="mathlive"`; `core/grader/latex_in.py` lowers it to the plain answer syntax, and
the one Lark grammar, shape checks and whitelist translator do the rest. There is one
math parser and one set of reading rules, and the "read as" preview is identical in both
modes. MathJSON and the Compute Engine are not used.

Lowering rules (all on the typeset form, which the student sees):

- `\sin x`, `\sin 2x`, `\ln x^2` take the following run of atoms as the argument;
  `\sin^2 x` is sin(x)², `\sin^{-1}` is arcsin. Plain text still requires `sin(x)`.
- A symbol next to a letter multiplies (`2\pi x`), but letter next to letter stays one
  word, so `xy` gets the same "two letters never multiply" error as in plain text.
- `3\frac{1}{2}` is rejected as a mixed number; `\placeholder{}` asks to fill the box;
  any command outside the whitelist (`\int`, `\pm`, …) is a syntax error.
- text, truefalse and choice answers use plain text: the math field drops spaces
  (`concave up` comes back as `concaveup`).

## Consequences

- MATH-4's "outputs MathJSON" and MATH-8's "MathJSON goes to SymPy through a hand-written
  whitelist translator" are replaced by this path; the spec text should say so.
- Nothing extra is bundled in the page and the CSP is unchanged.
- MathLive's `log` inline shortcut inserts `\log_{\placeholder{}}`, so typing `log(x)`
  gives an empty base box ("Fill in the empty box"). The page may want to override that
  shortcut to plain `\log`.
- After a MathLive upgrade, rerun
  `uv run python -m tests.grader.make_mathlive_fixtures`; `test_mathlive.py` checks the
  fixtures match the pinned version and shows which readings moved.
