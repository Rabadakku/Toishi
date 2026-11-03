# Calculus I: section 4.5 Derivatives and the Shape of a Graph

2026-11-02 · pack `calc1` · branch `worktree-agent-a66cdc891eee8cd3e` · file `packs/calc1/4-5-shape-of-a-graph.cards.md`

## What this is

The content for OpenStax Calculus Volume 1, section 4.5, in the deck `Calculus I::4 Applications of
Derivatives::4.5 Derivatives and the Shape of a Graph`. It covers seven skills: `calc1.shape.increasing-decreasing`,
`first-derivative-test`, `concavity`, `inflection-points`, `second-derivative-test`, `from-derivative-graph`
and `interpret-derivative-signs`. I followed `docs/prompts/write-calc1-section.md` and used the pilot file
`packs/calc1/4-3-maxima-and-minima.cards.md` as the model.

- **Size:** 7 worked examples and 84 problems (12 per skill). 48 problems are static and 36 are templates
  (43%) that expand to 1546 instances, so the file builds to 1601 cards (7 + 48 + 1546). Four templates reach
  the 200-instance cap: `fdt-quad.t01`, `infl-cubic.t01`, `infl-logistic.t01` and `sdt-table.t01`.
- **Final check:** `content-tools/mepack.py check packs/calc1 --katex <KaTeX 0.19.1>` reports `OK` on the whole
  pack, which is now 2287 cards (the pilot's 686 and these 1601). Details below.
- **Not done:** nothing is merged. `scripts/check.sh` was not run, as the brief says. No card
  carries a `tagged:` line, as in the pilot. Tier 5 was not written (the brief asks for tiers 1 to 4).
  `skills.md`, `pack.json` and the component map are untouched. The commit holds the cards file and this note
  and nothing else.

## Cards by skill and tier

| Skill | Example | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Problems | Templates | Instances |
|---|---|---|---|---|---|---|---|---|
| `calc1.shape.increasing-decreasing` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 66 |
| `calc1.shape.first-derivative-test` | 1 | 3 | 4 | 3 | 2 | 12 | 6 | 291 |
| `calc1.shape.concavity` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 177 |
| `calc1.shape.inflection-points` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 459 |
| `calc1.shape.second-derivative-test` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 268 |
| `calc1.shape.from-derivative-graph` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 83 |
| `calc1.shape.interpret-derivative-signs` | 1 | 3 | 4 | 3 | 2 | 12 | 5 | 202 |
| **Total** | 7 | 21 | 28 | 21 | 14 | 84 | 36 | 1546 |

Every skill has the same shape: one worked example and 12 problems, split 3 / 4 / 3 / 2 over tiers 1 to 4. IDs are
`calc1.4-5.<name>.<nnn>` for static cards and `.t<nn>` for templates. Counting each card or part once, the answer
types are interval 30, point 24, number 21, set 12, choice 6, true/false 6 and text 2; 13 problems have two or
three parts. No card uses `expression`, `equation`, `list` or `quantity`. The template families are polynomials
(quadratic, cubic, quartic), a rational function, logarithms, an absolute value, a logistic curve, tables of
signs, given-derivative forms (a factored `f'` or `f''`), parameter families and graph-reading drills. The
trigonometric and exponential functions are static cards.

Tiers 3 and 4 put several of the section's tools into one question, the way an exam does:

- **Where the function or its derivative is not defined.** `incdec-rational.t01`, `incdec-quotient-exp.001` and
  `conc-reciprocal.001` have a gap in the domain that splits the answer into two intervals, and `incdec-sqrt.001`
  has a closed-interval domain. In `fdt-vertical-tangent.001` and `infl-cbrt.001` (real cube roots) the
  derivative, or the second derivative, does not exist at 0 but does not change sign there, so 0 is neither an
  extremum nor an inflection point. In `fdt-abs-corners.t01` the corners of an absolute value are local minima.
- **Two conditions at once.** `conc-both.001` asks where `f` is both increasing and concave down. In
  `sdt-two-tests.t01` the second derivative test fails at 0, so the first derivative test has to decide there.
- **Trigonometric and exponential functions.** `incdec-trig.001` and `fdt-trig.001` at tier 3; at tier 4,
  `fdt-trig-double.001` (`sin x + cos 2x` on `(0, 2π)`: four critical numbers, two of them at `arcsin(1/4)` and
  its mirror image) and `sdt-expsin.001` (`e^(-x) sin x` on `(0, 3π)`: three critical numbers).
- **Applications.** `infl-logistic.t01` and `signs-logistic.t01` (a logistic population grows fastest at its
  inflection point, once from a formula and once from the differential equation alone), `signs-drug.001`,
  `signs-cubic.t01`, `signs-temperature.001` (a cosine model) and `signs-speed.t01`.
- **Working backwards.** `fdt-inverse.t01` finds the constants of a cubic from where its extrema are, and
  `sdt-backward.t01` finds the local maximum point from an inflection point and a local minimum.
- **Parameter families.** `incdec-param.t01`, `conc-param.t01` and `infl-param.001` ask for which values of a
  constant the function is increasing everywhere, concave up everywhere, or has exactly two inflection points.
  The end cases (a repeated zero, a degenerate member of the family) are in the solutions and the wrong
  answers.
- **One plot, several questions.** `fromgraph-sine.t01` asks for the sets of local maxima, local minima and
  inflection points; `fromgraph-touch-cubic.t01` asks for the local extrema, the inflection points and the
  interval where `f` is concave down (the plot touches the axis without crossing it); `fromgraph-zigzag.001`
  asks for the local maxima, the inflection points and the interval where `f` is concave up (three line
  segments). The tier 4 pair is `fromgraph-compose.001` (how many local extrema `g(x) = f(x^2)` has) and
  `fromgraph-shift.t01` (`h = f - mx`: the zeros of `h'` are where the plot is at height `m`).

| Card | Tier | Form | Answer type | Source |
|---|---|---|---|---|
| `incdec-example.001` | example | static | self-graded | original |
| `incdec-concept.001` | 1 | static | choice | original |
| `incdec-factored.t01` | 1 | template, 25 instances | interval | original |
| `incdec-quad.001` | 1 | static | interval | original |
| `incdec-cubic.t01` | 2 | template, 18 instances | interval | original |
| `incdec-exp.001` | 2 | static | interval | original |
| `incdec-flat.001` | 2 | static | interval | original |
| `incdec-log.t01` | 2 | template, 5 instances | interval | original |
| `incdec-quotient-exp.001` | 3 | static | interval | CLP-1 section 3.6.2, question 2, modified |
| `incdec-rational.t01` | 3 | template, 9 instances | interval | original |
| `incdec-trig.001` | 3 | static | interval | original |
| `incdec-param.t01` | 4 | template, 9 instances | interval | original |
| `incdec-sqrt.001` | 4 | static | interval | original |
| `fdt-example.001` | example | static | self-graded | original |
| `fdt-quad.t01` | 1 | template, 200 instances | number | original |
| `fdt-signs.t01` | 1 | template, 25 instances | number | original |
| `fdt-zero-not-enough.001` | 1 | static | truefalse | original |
| `fdt-cubic.t01` | 2 | template, 30 instances | point | original |
| `fdt-double-root.t01` | 2 | template, 16 instances | set | original |
| `fdt-exp.001` | 2 | static | point | original |
| `fdt-neither.001` | 2 | static | set | original |
| `fdt-abs-corners.t01` | 3 | template, 12 instances | point | original |
| `fdt-trig.001` | 3 | static | point | original |
| `fdt-vertical-tangent.001` | 3 | static | point | original |
| `fdt-inverse.t01` | 4 | template, 8 instances | 2 parts: number, number | original |
| `fdt-trig-double.001` | 4 | static | point | original |
| `conc-example.001` | example | static | self-graded | original |
| `conc-cubic.t01` | 1 | template, 88 instances | interval | original |
| `conc-point.001` | 1 | static | text | original |
| `conc-tf.001` | 1 | static | truefalse | original |
| `conc-always-up.001` | 2 | static | interval | original |
| `conc-given.t01` | 2 | template, 20 instances | interval | original |
| `conc-quartic.t01` | 2 | template, 55 instances | interval | original |
| `conc-xexp.001` | 2 | static | interval | original |
| `conc-gauss.001` | 3 | static | interval | original |
| `conc-log.t01` | 3 | template, 9 instances | interval | original |
| `conc-reciprocal.001` | 3 | static | interval | original |
| `conc-both.001` | 4 | static | interval | original |
| `conc-param.t01` | 4 | template, 5 instances | interval | original |
| `infl-example.001` | example | static | self-graded | original |
| `infl-concept.001` | 1 | static | choice | original |
| `infl-cubic.t01` | 1 | template, 200 instances | point | original |
| `infl-tf.001` | 1 | static | truefalse | original |
| `infl-given.t01` | 2 | template, 48 instances | set | original |
| `infl-quartic.t01` | 2 | template, 3 instances | point | original |
| `infl-trig.001` | 2 | static | point | original |
| `infl-xexp.001` | 2 | static | point | original |
| `infl-cbrt.001` | 3 | static | point | original |
| `infl-log.001` | 3 | static | point | original |
| `infl-rational.t01` | 3 | template, 8 instances | point | original |
| `infl-logistic.t01` | 4 | template, 200 instances | 2 parts: number, number | original |
| `infl-param.001` | 4 | static | interval | original |
| `sdt-example.001` | example | static | self-graded | original |
| `sdt-concept.001` | 1 | static | choice | original |
| `sdt-inconclusive.001` | 1 | static | truefalse | original |
| `sdt-table.t01` | 1 | template, 200 instances | number | original |
| `sdt-cubic.t01` | 2 | template, 44 instances | 2 parts: point, point | original |
| `sdt-exp.001` | 2 | static | 2 parts: point, point | original |
| `sdt-reciprocal.001` | 2 | static | number | original |
| `sdt-trig.001` | 2 | static | 2 parts: point, point | original |
| `sdt-fprime.t01` | 3 | template, 9 instances | 2 parts: set, set | original |
| `sdt-lnx.001` | 3 | static | 2 parts: point, text | original |
| `sdt-two-tests.t01` | 3 | template, 3 instances | point | original |
| `sdt-backward.t01` | 4 | template, 12 instances | point | original |
| `sdt-expsin.001` | 4 | static | 2 parts: point, point | original |
| `fromgraph-example.001` | example | static | self-graded (plot) | original |
| `fromgraph-concept.001` | 1 | static | choice | original |
| `fromgraph-cross.001` | 1 | static | number (plot) | original |
| `fromgraph-quad.t01` | 1 | template, 15 instances | interval (plot) | original |
| `fromgraph-concavity.001` | 2 | static | interval (plot) | original |
| `fromgraph-steepest.001` | 2 | static | number (plot) | original |
| `fromgraph-tent.t01` | 2 | template, 15 instances | number (plot) | original |
| `fromgraph-touch.001` | 2 | static | number (plot) | original |
| `fromgraph-sine.t01` | 3 | template, 9 instances | 3 parts: set, set, set (plot) | original |
| `fromgraph-touch-cubic.t01` | 3 | template, 4 instances | 3 parts: set, set, interval (plot) | original |
| `fromgraph-zigzag.001` | 3 | static | 3 parts: set, set, interval (plot) | original |
| `fromgraph-compose.001` | 4 | static | number (plot) | original |
| `fromgraph-shift.t01` | 4 | template, 40 instances | 2 parts: number, number (plot) | original |
| `signs-example.001` | example | static | self-graded | original |
| `signs-ratechange.t01` | 1 | template, 53 instances | number | original |
| `signs-reverse.001` | 1 | static | choice | original |
| `signs-translate.001` | 1 | static | choice | original |
| `signs-faster.001` | 2 | static | truefalse | original |
| `signs-intersect.t01` | 2 | template, 81 instances | interval | original |
| `signs-marginal.001` | 2 | static | truefalse | original |
| `signs-table.001` | 2 | static | number | original |
| `signs-cubic.t01` | 3 | template, 9 instances | interval | original |
| `signs-speed.t01` | 3 | template, 27 instances | interval | original |
| `signs-temperature.001` | 3 | static | interval | original |
| `signs-drug.001` | 4 | static | 3 parts: number, number, number | original |
| `signs-logistic.t01` | 4 | template, 32 instances | number | original |

Every tier 2+ problem has one to three `wrong:` entries per answer, each with feedback and an `@step`
(`fromgraph-touch-cubic.t01` has four over its three parts). The templates compute their wrong answers from the
parameters. There are no hints, as the brief says, so the builder prints one `no ### Hints` warning per problem.
Every solution is a numbered list of steps with one tag each, taken from the card's `skill` or its `uses`. Units
appear wherever a problem has them (thousand liters per day per day, meters per second per second, milligrams
per liter per hour, degrees Celsius).

## Final check

The real check ran three times on the whole pack: on the assembled file, after the late audit of the step tags
described below, and once more after I removed a blank line at the end of the file (the pilot file has none). All
three printed `OK`, and the last ran on the file as committed. From the worktree root:

```
uv run --no-sync python content-tools/mepack.py check packs/calc1 --katex <KaTeX 0.19.1 folder>
```

Its output, with the 84 `no ### Hints` warning lines and the 152 `pool` lines for other
skills left out:

```
pack calc1 0.1.0: 2287 cards, 162 skills
pool calc1.shape.interpret-derivative-signs: missing confusable skills
wrong answers: answers of tier 2+ problems with a wrong: line 106/106, wrong answers without @step 0
differential checks (DEV-18): 3523 answers graded by both engines, 10788 template operations agree with mpmath, 56 could not be recomputed
worked solutions (MATH-17): 10350 step checks hold, 1944 final lines match the key, 0 steps with math unverified
kinds: example 10, problem 2277
OK
```

- **Warnings:** the 84 `no ### Hints` warnings are the only ones from the check, one per problem. There is no
  other warning and no error (the log has one more `warning:` line, a deprecation notice that `uv` prints about
  an environment variable). The KaTeX strict render check ran too (`--katex`, version 0.19.1).
- **Pool report (GRAPH-4):** the only line for the seven skills is `calc1.shape.interpret-derivative-signs:
  missing confusable skills`, because `skills.md` gives that skill no `confusable:` line (the brief says not to
  edit it). The other 152 lines are for skills of other sections and for the prerequisite skills
  (algebra, trigonometry, earlier derivative rules) that have no cards in the pack yet; none is for the
  pilot's skills. By my own count every skill of this section has a worked example and a template at each of
  tiers 1 to 4, and tier 3 has 11, 14, 11, 10, 13, 14 and 37 problem cards (templates counted by instance,
  skills in the order of the table above). The target is 10.
- **Numbers for this file alone,** as the pack's figures minus the pilot's (720, 1989, 42, 2280 and 683 in
  `docs/design/calc1-pilot-notes.md`): 2803 answers graded by both engines, 8799 template
  operations agree with mpmath, 14 could not be recomputed, 8070 step checks hold,
  1261 final lines match the key, 0 steps with math unverified. A scratch build of this file alone, on the
  final file, prints exactly these figures (and 1601 cards, 7 examples, 1594 problems, and `wrong:` lines for 80
  of 80 answers of tier 2+ problems), so the subtraction is right. The 1261 is not 1594: the final-line check
  applies to single-part cards with a math answer type, and 333 of the 1594 problem cards have parts or are
  choice, true/false or text cards.
- **Operations not recomputed (14):** one per instance of the two logarithm templates, `conc-log.t01` (9) and
  `incdec-log.t01` (5). The builder does not count that as an error; those results rest on SymPy alone (the pilot
  had the same for its log and radical templates). I traced them with a script that loads the pack and prints the
  per-template tallies.
- **What the late audit changed in the numbers.** The scratch build before the audit printed 8599 operations and
  7857 step checks. The audit added 200 operations and 213 step checks: the one new claim of `infl-logistic.t01`
  in each of its 200 instances, and 13 claims in static cards.

## What my own checks found

The builder says `OK` while content can still be wrong, so I ran my own checks. They are scripts kept
outside the repository and are not committed.

**What the builder stopped me on**

- A `;` inside `wrong:` feedback splits the entry and then fails with "Can't read 'this': two letters never
  multiply" (`fromgraph-touch-cubic.t01` part b and `signs-ratechange.t01`). I reworded both and scanned every
  `wrong:` line of the file for the same slip.
- A step 0 with math and no `check:` (`fromgraph-quad.t01`, and earlier `infl-cbrt.001` and `infl-log.001`). Step 0
  is now written without math.
- A limit claim written with `oo` (`signs-example.001`), which the claim grammar does not read; the spelling is
  `inf`.

**What only my own checks found**

- **GRAPH-4 pool targets, found late.** My scratch build script filtered out the `pool` lines, so I did not see
  that tier 3 needs 10 problem cards per skill (templates count by instance) and that tiers 1 and 2 need a
  template. Several tier 3 families were too small, and skill 7 had no tier 1 template. Fixes: wider parameter
  ranges in `incdec-rational.t01` (`k` up to 9), `conc-log.t01` (up to 9) and `infl-rational.t01` (up to 8);
  `fdt-abs-corners` rewritten as a template; skill 7 re-tiered so that tiers 1 and 2 each have a template. So
  part of the tiering of skill 7 was driven by the target (see the uncertainties).
- **Rendering.** The lint reads the database built from this file alone, so it sees every instance of every
  template. It scans each question, step, feedback line and part prompt for `- -`, `+ -`, a lone `1` before a
  letter, `^{1}`, `/1`, a fraction over 1, `+ 0`, `- 0`, `0x`, a stray `*`, a raw function name, empty parentheses,
  a dangling plus, an unsubstituted `[[ ]]`, and bare `f`, `f'`, `x`, `k` or `t` in prose outside math. It found a
  double minus and a `- 0` in `fromgraph-touch-cubic.t01` step 4 (the factored `f''` is now typeset with `tex()`)
  and bare math in the feedback of skills 6 and 7 (now inside `\( \)`, as in skills 1 to 5). On the final build its
  only report is the four instances of `fromgraph-touch-cubic.t01`, which has four wrong answers over three parts
  (it counts per card and allows three).
- **Structure.** A second script on the cards file checks each step's tag against `skill` and `uses` in both
  directions, duplicate `uses`, consecutive step numbers and every `@n` in range. The builder only warns about a
  tag outside the set; a `uses` entry that no step cites passes it. On the final file: 91 cards, 0 problems.
- **Brute-force keys.** Seven scripts, one per skill, recompute the answer of every card family that has a
  computed key, over the parameter ranges of its template. They use finite differences and dense numeric scans,
  never the CAS. For the plot cards they use the plotted function itself: the joins of the three segments in
  `fromgraph-zigzag.001`, a numerical antiderivative for `fromgraph-compose.001`, and all 40 instances of
  `fromgraph-shift.t01`. All seven print `ALL OK` on the final file. The expected answers are typed into the
  scripts from the cards, not read from the file, so a card whose key differs from my copy would not show; the
  builder's final-line check (the key must equal the solution's last claim) is the mechanical link between a
  key and its card. The scripts check answers only, not the steps.
- **Reading as a student.** I read the whole file once end to end, and the rendered instances of the templates. It
  caught a modelling flaw (`signs-cubic.t01` first modelled total downloads, which cannot decrease; it now models
  the number of weekly users), an awkward `V'(4 + 4)` in `signs-ratechange.t01` (now `V'(8)` and the like, from
  `[[4 + n]]`), and the tag gaps in the next item.
- **A late audit of `uses` against the steps.** Reading the file against the component map, I found cards whose
  solution used a derivative fact or an identity that no step tagged, which the brief forbids (`uses:` lists
  every other component the solution needs). The pilot tags these separately (`closed-xlnx.001` tags `(ln x)'`
  with `calc1.deriv.logarithm`; `crit-exp.t01` tags `e^(-x/k)` with `calc1.deriv.chain-linear-inside`), so I did the
  same. Ten cards got a step of their own: `(e^x)' = e^x` (`calc1.deriv.exponential`) in
  `incdec-quotient-exp.001`, `fdt-exp.001`, `infl-xexp.001` and `sdt-exp.001`; `(ln x)' = 1/x`
  (`calc1.deriv.logarithm`) in `infl-log.001` and `sdt-lnx.001`; the derivative of `e^(kx)`
  (`calc1.deriv.chain-linear-inside`) in `infl-logistic.t01`, `signs-drug.001` and `sdt-expsin.001`; and the
  derivatives of sine and cosine (`calc1.deriv.trig-sin-cos`) in `sdt-expsin.001` and `signs-temperature.001`.
  In `fdt-trig-double.001` the values at the standard angles and the double-angle evaluation at `sin x = 1/4`
  are now separate steps (`trig.values.exact` and `trig.identities.pythagorean`). `sdt-reciprocal.001`
  differentiates `4/x`, so it is tagged `calc1.deriv.power-rule-rational`, not `calc1.deriv.power-rule`. Two
  concept cards that name the second derivative test (`sdt-concept.001` and `sdt-table.t01`) now carry
  `cue: required`, like the other cards of that skill that name it. That is 14 cards. Where a step was inserted, the
  `@n` of the `wrong:` lines moved with the steps.

## Provenance

Allowed sources were OpenStax Calculus Volume 1, CLP Calculus (UBC), APEX Calculus and MIT OpenCourseWare 18.01.
One card is adapted, from CLP-1. The other 83 problems and the 7 examples are original and carry
`source: original` from the file header. No other book was used.

- `incdec-quotient-exp.001` is adapted from the CLP-1 problem book (Feldman, Rechnitzer, Yeager), section 3.6.2,
  question 2, which asks for the largest open interval on which `e^x/(x + 3)` is increasing. The question number is
  its position in `prob_s3.6.2.tex`; I believe that matches the book's numbering but did not have the PDF to
  confirm it (the pilot has the same caveat). I kept the function, asked where it is *decreasing* and for all such
  intervals (so the excluded point `x = -3` matters), and wrote the solution, its steps and the wrong-answer
  lines myself. The URL is pinned to commit `9f0295936d395bec68dab7915057135a2c7f0414`; the card has
  `modified: yes` and license CC BY-NC-SA 4.0.
- The functions in the examples and templates are generic textbook-style forms with numbers I chose (cubics and
  quartics with integer critical numbers, `x^2 e^(-2x)`, `x^2 ln x`, `x e^(-x^2)`, `x/(x^2 + k^2)`,
  `ln(x^2 + k^2)`, `|x^2 - k^2|`, `x^(4/3) + 4x^(1/3)`, `x^(5/3) - 5x^(2/3)`, a logistic curve, `sin x + cos x`).
  I copied no wording, figure, scenario or answer from any source beyond the one card above.

## Components the map does not have

I did not add any. These are the places where I used the nearest component or folded a demand into another step:

| Needed | Used | Where |
|---|---|---|
| The one-sign criterion for a quadratic in a parameter (never negative exactly when the discriminant is at most 0), with the check of the two end values | `alg.solve.quadratic-formula` for the discriminant; the inequality in the parameter inside `alg.inequality.sign-chart`; the end values inside the card's main skill | `incdec-param.t01`, `conc-param.t01`, `infl-param.001` |
| Sign analysis restricted to a domain (`x > 0`, `x != k`, `t >= 0`, an interval) | inside `alg.inequality.sign-chart`; `pre.functions.domain` for the step that finds the domain | with a domain step: `incdec-log.t01`, `incdec-rational.t01`, `incdec-quotient-exp.001`, `incdec-sqrt.001`, `conc-reciprocal.001`; without one: `infl-log.001`, `signs-cubic.t01` |
| A squared factor does not change sign | folded into `alg.inequality.sign-chart` | `incdec-flat.001`, `fdt-double-root.t01`, `conc-given.t01`, `infl-given.t01`, `fromgraph-compose.001` |
| Read zeros, sign changes, peaks and valleys off a plotted graph | the card's main skill, `calc1.shape.from-derivative-graph`; those cards have little or no `uses` for this | all `fromgraph-*` cards |
| Solutions of a trigonometric equation that are not standard angles (`sin x = 1/4`) | `trig.equations.solve`, with `arcsin` in the answer | `fdt-trig-double.001` |
| Find constants from where the extrema or the inflection point are | `alg.solve.linear` (with `alg.expand.products` in `fdt-inverse.t01`) | `fdt-inverse.t01`, `sdt-backward.t01` |
| Differentiate an equation that defines `P'` to get `P''` (there is no formula for `P`) | `calc1.implicit.differentiate`, the nearest | `signs-logistic.t01` |
| The chain rule when `f'` is known only by its graph (`g(x) = f(x^2)`) | `calc1.deriv.chain-rule` | `fromgraph-compose.001` |
| Speeding up and slowing down from the signs of `v` and `a` | the card's own skill, `calc1.shape.interpret-derivative-signs`; `calc1.motion.speeding-up` (section 3.4) names the same rule | `signs-speed.t01` |
| Differentiate a bare linear or constant term | folded into the neighbouring rule's step, not tagged | many cards |

## My uncertainties

**Cards I am least sure of**

- **The 12 plot cards** (the example and 11 problems: every `fromgraph-*` card except `fromgraph-concept.001`).
  Plots are not drawn by the app yet (MATH-2), so I never saw one. I kept every feature the questions ask about
  at an integer `x`, made the joins continuous, and ask only for `x`-values, intervals and counts, never a
  height. I cannot judge tick marks or readability. `fromgraph-touch-cubic.t01` runs from -16 to 20 on a window 6
  units wide, so its peak (height 4) may look small; `fromgraph-compose.001` runs from -16 to 4 and
  `fromgraph-shift.t01` up to 17.
- **Tier judgments.** I tiered by the number of independent ideas: one idea is tier 1, one idea with a trap or
  two steps is tier 2, a typical exam question with several ideas is tier 3, and tier 4 adds a less familiar
  setup. The ones I doubt: `signs-speed.t01` (tier 3, but it only compares signs on three intervals with no
  computation, and 27 of skill 7's 37 tier 3 cards are its instances; without them the skill would still have 10),
  `signs-faster.001` (tier 2: a true/false whose point is that falling "faster and faster" needs `T'' < 0`),
  `fromgraph-touch.001` (tier 2, but the touching-the-axis trap may catch strong students) and
  `fromgraph-compose.001` (tier 4 because it combines three ideas, though the arithmetic is easy).
- **`interpret-derivative-signs` is a thin skill.** It requires only `concavity`, and its tier 1 and 2 cards and
  `signs-speed.t01` list no other component. Its other tier 3 and 4 cards need a computation first (power rule,
  factoring, a sign chart, trigonometric equations, implicit differentiation), so they list those in `uses`.
  `signs-speed.t01` is section 3.4 material (`calc1.motion.speeding-up`); I kept it here because the translation
  from words to signs is the same skill. If the coordinator would rather keep sections apart, its steps can be
  re-tagged with `calc1.motion.speeding-up`, which must then be added to `uses`.

**Conventions I chose**

- "Increasing on an interval" follows the definition (`f(a) < f(b)` for `a < b`), so a function whose derivative is
  zero only at isolated points is increasing across them: `incdec-flat.001` answers `(-inf, inf)`, and the
  parameter families include their end values. A student taught "`f' > 0`, strictly" may type two intervals;
  that wrong answer has its own feedback.
- A critical number is an interior point of the domain where `f'` is zero or undefined; a local extremum is an
  interior point; an inflection point needs `f` defined there and `f''` to change sign (`f''` may fail to exist,
  as in `infl-cbrt.001`). The graph cards say "consider only `x`-values strictly between ...", so end points never
  count. Two questions say that `x^(1/3)` is the real cube root.

**What the builder cannot see**

- **Final lines without a claim.** In 42 cards the last step has no `check:`. In 34 of them
  the last step has math and the builder grades its last math against the key, so that final line is verified
  only by equalling the key, not by a computed claim. The other 8 are choice and true/false cards with no math in
  the last step.
- **Tautological claims.** 24 claims in 20 cards have identical sides (`{1, 2} = {1, 2}`, `p = p`,
  `h = h`, `solve(...) = solve(...)`). They satisfy "every step with math has a claim" for steps that only
  restate an earlier result, and verify nothing by themselves; the neighbouring claims and the final line do the
  work.
- **Long `uses` lists.** `docs/prompts/make-cards.md` says at most four; the brief says to list every component, and
  I chose completeness, as the pilot did. 28 problems list more than four (`fdt-trig-double.001` lists 8;
  `incdec-sqrt.001` and `fdt-exp.001` list 7). Each is a distinct step with its own tag, so the component rule
  holds, but the diagnosis from the `wrong:` lines gets coarse.
- **`cue: required`** is on 10 second-derivative-test cards: the example, the 7 problems whose question says "Use the second
  derivative test", and the 2 concept cards (`sdt-concept.001`, `sdt-table.t01`) whose question asks what the
  test says. The three problems that do not name it (`sdt-inconclusive.001`, `sdt-two-tests.t01`,
  `sdt-backward.t01`) are uncued. I am not sure the key is meant for concept cards.
- **Text answers.** `conc-point.001` and `sdt-lnx.001` part b take a word ("concave up", "maximum") against a fixed
  list of accepted forms. A student who types something else is marked wrong, with no partial match.
- **Wrong answers per card.** `fromgraph-touch-cubic.t01` has 4 `wrong:` entries over its 3 parts (1, 2 and 1):
  within three for each part, over three for the card. `docs/prompts/make-cards.md` says up to three.
- **Small template families,** kept small because larger ranges break the numbers: `infl-quartic.t01` (3
  instances), `sdt-two-tests.t01` (3), `fromgraph-touch-cubic.t01` (4), `conc-param.t01` (5) and `incdec-log.t01` (5). A
  student can meet all of them in a few reviews. The three families I widened for the pool target vary the
  numbers, not the structure, and so does `signs-speed.t01`.
- **No `equation`, `expression`, `list` or `quantity` answer types.** The questions ask for intervals, points,
  numbers and sets; units are in the question text, not graded.
- **Idiom for cube roots.** The derivative claims for `x^(4/3)` and `x^(5/3)` substitute `x = u^3` (for example
  `diff(u^5 - 5*u^2, u)/diff(u^3, u)`), as the pilot did for its cusp. It works, but a reader has to learn it.
- **Tagging judgments.** Shape skills appear as `uses` on cards of other skills of this section: on the graph
  cards (`first-derivative-test` on seven, `inflection-points` on six, `concavity` on three, `increasing-decreasing`
  on `fromgraph-quad.t01`), and on `sdt-two-tests.t01` (`first-derivative-test`), `sdt-backward.t01`
  (`inflection-points`) and `conc-both.001` (`increasing-decreasing`). I read them as separate demands (relating
  the sign of `f'` to extrema is not the same as reading a graph), but another writer might fold them into the main
  skill. `fdt-trig-double.001` uses two double-angle identities, `sin 2x = 2 sin x cos x` in step 3 and
  `cos 2x = 1 - 2 sin^2 x` in step 9, both under `trig.identities.pythagorean`, which the map says covers the
  double-angle identities.
- **What no check can say.** Whether a wrong-answer feedback line is the best explanation, or whether a
  question reads well to a student. I proofread a sample of instances of each template, not all 1546.

## For the coordinator

- **`calc1.shape.interpret-derivative-signs` has no `confusable:` line in `skills.md`.** GRAPH-4 lists it as
  missing, and it is the only pool line for this section. I did not edit `skills.md`.
- **A lint for untagged derivative facts** (a `diff` of `e^x`, `e^(kx)`, `ln x`, `sin` or `cos` in a claim of a card
  whose `uses` lacks the component) would have caught the 10 cards of the late audit that needed a step of their
  own for such a fact. The builder cannot know what a step needs.
- **Commit footer.** `AGENTS.md` asks for `Co-Authored-By: Claude Opus 5.5` plus a `Claude-Session` line; the
  reminder in my session said `Claude Sonnet 5.5` with the same `Claude-Session` line. I used the `AGENTS.md`
  text, as the brief says and as the pilot did.
