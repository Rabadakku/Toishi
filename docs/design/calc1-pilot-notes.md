# Calculus I pilot: section 4.3 Maxima and Minima

2026-11-02 · pack `calc1` · branch `calc1-pilot` · file `packs/calc1/4-3-maxima-and-minima.cards.md`

## What this is

The pilot content section for the Calculus I pack: OpenStax Calculus Volume 1, section 4.3, for
the skills `calc1.extrema.from-graph`, `calc1.extrema.critical-numbers` and
`calc1.extrema.closed-interval`. The pilot measures the effort per card and the errors that get
through, so this file records what I did, what each check caught and what I am unsure about.

- **Size:** 3 worked examples and 36 problems (12 per skill). 20 problems are static and 16 are
  templates that expand to 663 instances, so the pack builds to 686 cards (3 + 20 + 663).
- **Final build:** `content-tools/mepack.py check packs/calc1 --katex <KaTeX 0.19.1>` reports `OK`.
  Differential checks (DEV-18): 720 answers graded by both engines, 1989 template operations agree
  with mpmath. 42 operations could not be recomputed (6 in `crit-log.t01`, 36 in
  `closed-radical.t01`), so those rest on SymPy alone; the builder does not count that as an
  error. Worked solutions (MATH-17): 2280 step checks hold, 683 final lines match the key,
  0 steps with math unverified. No pool lines for the three skills. The KaTeX strict render check
  ran (the worktree has no `web/node_modules/katex`, so I installed the pinned 0.19.1 elsewhere
  and passed `--katex`; the one pytest that needs it is skipped by `check.sh fast`).
- **`./scripts/check.sh fast`:** passed (4645 passed, 12 skipped, 112 deselected, 0 failed). I
  ran it twice, the second time on the final cards file, with the same result both times
  (about 7.5 and 6 minutes). A re-run of the real build just before the commit printed a report
  identical to round 10.
- **Not done:** nothing is merged, `app/packs.py` `SHIPPED` is unchanged, and no card carries a
  `tagged:` line (see the questions at the end).

## Cards by skill and tier

| Skill | Example | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Problems |
|---|---|---|---|---|---|---|
| `calc1.extrema.from-graph` | 1 | 4 | 5 | 3 | 0 | 12 |
| `calc1.extrema.critical-numbers` | 1 | 3 | 4 | 3 | 2 | 12 |
| `calc1.extrema.closed-interval` | 1 | 3 | 4 | 3 | 2 | 12 |

Tier 5 was not written. From-graph problems have a `plot:` and stay at tiers 1 to 3. Template
kinds: polynomial, simple rational, radical, trig, exponential and log, as asked, plus the
graph-reading and comparison drills. IDs are `calc1.4-3.<name>.<nnn>` (static) and
`calc1.4-3.<name>.t<nn>` (template).

| Card | Tier | Form | Answer type | Source |
|---|---|---|---|---|
| `graph-example.001` | example | static | self-graded | original |
| `graph-peak.t01` | 1 | template, 18 instances | point | original |
| `graph-local-min.001` | 1 | static | set | original |
| `graph-min-value.001` | 1 | static | number | original |
| `graph-endpoint-max.t01` | 1 | template, 35 | number | original |
| `graph-local-min-trap.001` | 2 | static | number | original |
| `graph-corner-count.001` | 2 | static | number | original |
| `graph-open-interval.001` | 2 | static | number (`DNE`) | original |
| `graph-cubic-range.t01` | 2 | template, 9 | list | original |
| `graph-sine-count.001` | 2 | static | number | original |
| `graph-flat-and-peak.001` | 3 | static | set | CLP-1 3.5.1 question 1, modified |
| `graph-abs-valley.t01` | 3 | template, 15 | set | original |
| `graph-cusp.001` | 3 | static | list | original |
| `crit-example.001` | example | static | self-graded | original |
| `crit-quad.t01` | 1 | template, 200 | set | original |
| `crit-factored.t01` | 1 | template, 25 | set | original |
| `crit-none.001` | 1 | static | set (`none`) | original |
| `crit-poly.t01` | 2 | template, 15 | set | original |
| `crit-rational.t01` | 2 | template, 6 | set | original |
| `crit-exp.t01` | 2 | template, 8 | set | original |
| `crit-log.t01` | 2 | template, 6 | set | original |
| `crit-trig.t01` | 3 | template, 18 | set | original |
| `crit-cusp.001` | 3 | static | set | original |
| `crit-holes.001` | 3 | static | set (`none`) | OpenStax 4.3 exercise fs-id1165040750656, modified |
| `crit-xpowx.001` | 4 | static | set | original |
| `crit-abs-sqrt.001` | 4 | static | set | CLP-1 3.5.1 question 7, modified |
| `closed-example.001` | example | static | self-graded | original |
| `closed-compare.t01` | 1 | template, 200 | number | original |
| `closed-quad.001` | 1 | static | list | CLP-1 3.5.2 question 4, modified |
| `closed-monotone.001` | 1 | static | list | original |
| `closed-cubic.t01` | 2 | template, 39 | list | original |
| `closed-cubic-outside.001` | 2 | static | list | CLP-1 3.5.2 question 5, modified |
| `closed-rational.t01` | 2 | template, 12 | list | original |
| `closed-xlnx.001` | 2 | static | list | original |
| `closed-trig.t01` | 3 | template, 21 | list | original |
| `closed-cusp.001` | 3 | static | list | original |
| `closed-radical.t01` | 3 | template, 36 | list | original |
| `closed-arctan.001` | 4 | static | list | original |
| `closed-xpow.001` | 4 | static | list | original |

Every problem has 2 or 3 `wrong:` lines with feedback and an `@step`, hints, and a numbered
solution whose every step has one tag. Wrong answers in templates are computed from the
parameters. The five adapted cards say `modified: yes` and name their source, `source-url`
and `license` on the card; the rest inherit `source: original` and the license from the file
header.

## How the time went

I started at 16:59 UTC and had the clean build at 17:43. The review and fix rounds ran to 18:15,
the first `check.sh fast` to 18:23, the last edit to the cards file was at 18:28, and this note
and the commit finished at 18:41. That is about 1 hour 40 minutes of wall clock for 39 card
definitions, or about 2.6 minutes per definition (0.15 minutes per built card). The split is
rough, because writing and thinking overlap, and so do the last two rows (the second
`check.sh fast` ran while I finished this note), so the rows add up to slightly more than the
102 minutes:

| Phase | Time | What it was |
|---|---|---|
| Reading | about 6 min | AGENTS.md, the card format, the test packs, the skill map, the two sources |
| Pipeline code and first experiments | about 20 min | Which rules the builder enforces (checks, templates, claims, plots, answer types), installing KaTeX, four early scratch builds |
| Design and scratch builds | about 14 min | A helper that searched for cubics with integer critical numbers and values, about eight more scratch builds to learn the claim idioms and the failure messages, and brute-force checks of every static key |
| Writing | about 3 min of tool time | The file went in as three appends. The drafting happened during the two phases above and cannot be separated from them |
| Builder-driven fixes | about 3 min | Rounds 1 to 3 |
| Independent review | about 31 min | Brute-force truth check of all 686 cards, my own lint, proofreading the rendered instances, and the fixes in the next sections |
| `check.sh fast` | about 14 min | Two runs (about 8 and 6 minutes); the second ran on the final file while I finished this note |
| This note and the commit | about 13 min | |

About 40 minutes of this was one-off (learning the toolchain and building the checks), so a
second section with the same tooling should cost much less per card. The largest single cost
was the independent review, because the builder can say `OK` while content is still wrong.

## Build log

A round is one run of the real build on the real file.

| Round | UTC | Result | What it showed | Fix |
|---|---|---|---|---|
| 1 | 17:41:30 | FAILED, 6 errors | 4 cards used the template names `lo`, `hi` and `mid` ("use one letter, a Greek letter or a_1"); `graph-open-interval.001`: final line does not match the key `DNE`; `crit-abs-sqrt.001`: final line `-7, 5` does not match the key `-7, -1, 5` | Renamed to `p`, `q`, `r`; added the missing final claims `DNE = DNE` and `{-7, -1, 5} = {-7, -1, 5}` |
| 2 | 17:41:59 | OK, 670 cards | Pool report: from-graph tier 3 had 3 problems and needs 10 (GRAPH-4) | none yet |
| 3 | 17:43:34 | OK, 684 | | Made `graph-abs-valley` a template (15 instances) |
| 4 | 17:55:09 | OK | Nothing from the builder; my own checks (below) | Plot join, spoiler sentence, feedback wording |
| 5 | 17:57:37 | OK, 686 | My proofreading of rendered instances | Parameter ranges that printed `e^{-x/1}`, `1x` and `+ -4` |
| 6 | 18:01:18 | OK, but 609 steps with math unverified | My typographic pass wrapped `f`, `f'`, `x` in math, which put math in steps that have no claim | See round 7 (this batch also fixed the `graph-peak` feedback) |
| 7 | 18:03:53 | OK, 0 unverified | | Step 0 and two domain steps written without math; two real claims added |
| 8 | 18:07:08 | OK | My proofreading | `closed-trig` coefficient, `closed-rational` display, `crit-trig` feedback |
| 9 | 18:14:16 | OK, 2280 step checks | My provenance check | Replaced `closed-cusp.001` (see Provenance) |
| 10 | 18:31:23 | OK, 686; this is the committed file | My proofreading | One feedback line reworded after the first `check.sh` (the `graph-sine-count` endpoint line) |

Of the 10 rounds, 1 failed with builder errors (6 errors of 2 kinds: the template-name rule, 4
errors, and a last claim that does not match the key, 2 errors). Two more produced a builder
report that I acted on (the pool gap in round 2, and the unverified math in round 6, which my own
typographic pass had caused), and the next round after each confirmed the fix (rounds 3 and 7).
The other 5 (rounds 4, 5, 8, 9 and 10) passed the builder untouched and changed the file only
because of my own checks, which the builder has no way to ask for.

**Caught before the first real build, in the scratch pack** (not counted as rounds): a `wrong`
step number past the last step; a point or list answer whose last claim does not match the key
(and a set claim `{2} = {2}` against the key `0, 2, 4`); `diff(x^(2/3), x)` producing a
DiracDelta template error; `\([[[h - 3]], ...]\)` not parsing; `require` that used `x`; an
unsatisfiable `require`; a step with math and no claim; `solve(x > 0, x) = (0, inf)` ("not a
single value"; interval claims are unsupported); a step without `Label:`; a semicolon inside
`wrong:` feedback splitting the entry; template names longer than one letter (`lo`); and a
find-and-replace of mine that turned `r = c - 9*m^3` into `r = r`. The template-name error came
back in the real file, even though the rule is in `docs/card-format.md` and I had already hit it:
what I learned in the scratch pack did not carry over to the names I chose later.

## What the builder cannot catch, and what I did about it

All of these passed the builder. I found them with my own checks, which live in the session
scratchpad and are not committed:

- `truth.py`: recomputes the answer of all 36 card families (every instance of the 16 templates)
  by brute force (dense numeric scans, SymPy, local-extremum detection), independently of the
  pipeline's CAS. Result: 686 cards, 0 mismatches. Its first run flagged two families: one was a
  sort-order bug in the checker itself, the other was the hidden plot jump described below.
- `lint.py`: step tags against `skill` and `uses` in both directions (the builder only warns on
  tags outside the set), `uses` duplicates, 2 or 3 wrong answers, tier bounds, template
  instance counts. No problems.
- A scan of every rendered question, hint, step and feedback line for `x - -2`, `+ -4`, `1x`,
  `x^{1}`, `e^{-x/1}`, unsubstituted names and stray `*` or raw function names.

What they found:

1. **A hidden jump in a plot.** `graph-flat-and-peak.001` copies the CLP-1 figure. Its pieces do
   not meet at x = 2.5 (heights 1.75 and 1.7558), so the curve has a small upward jump there
   and a numeric scan finds a spurious turning point. The builder checks only the plot syntax.
   The third piece is now `3*e^(-4*(x - 5/2))/4 + 1`, which joins exactly with matching slope.
2. **A spoiler.** The adapted question said "flattens out at x = 0 and has a sharp peak at
   x = 2". Removed; the student has to find the features.
3. **Edge-case rendering.** `k = 1` printed `e^{-x/1}` and `\frac{1}{1}`; `a = 1` printed `1x` and
   `1(\cos x - \sin x)`; a negative constant printed `+ -4` and `+ 0`. Ranges narrowed.
4. **A name that was never substituted:** "f' = 0 at x = k" in `crit-log.t01` and
   "cos x = -1/b" in a `crit-trig.t01` feedback line.
5. **Inaccurate feedback:** "the lowest point, the left end" when both ends of the parabola are
   equally low; "the greatest height of the valley-and-hill part"; a sine-count line that stated
   the endpoint convention instead of pointing at "strictly between".
6. **Math outside math delimiters:** 61 lines had bare `f`, `f'` and `x` in prose. Wrapped; the
   claim-free steps were then reworded without math (round 7).
7. **A provenance error:** see below.

## Provenance

Allowed sources were CLP-1 and the OpenStax Calculus Volume 1 section 4.3 exercises. Five cards
are adapted from them; the other 31 problems and the 3 examples are original and carry
`source: original` from the file header. No other book was used, and nothing from any private
folder. (The scratch sources folder also holds CLP-2 and College Algebra, which are not allowed
sources; I used nothing from them.)

- CLP-1 question numbers are the position in the section file, stage by stage; I believe that
  matches the problem book's numbering but did not have the PDF to confirm it:
  `prob_s3.5.1.tex` question 1 (the graph with a flat spot and a spike) and question 7
  (`sqrt(|(x - 5)(x + 7)|)`), `prob_s3.5.2.tex` question 4 (`x^2 + 6x - 10` on `[-5, 5]`) and
  question 5 (`2/3 x^3 - 2x^2 - 30x + 7` on `[-4, 0]`). The URLs are pinned to the commit I
  read.
- OpenStax gives its exercises no printed numbers in the CNXML, so `crit-holes.001` cites the
  exercise by its `fs-id1165040750656` (`y = (x^2 - 1)/(x^2 + 2x - 3)`, answer "None").
- `closed-cusp.001` first cited an OpenStax item (`fs-id1165042035519`, `x^2 - 3x^(2/3)` on
  `[0, 2]`). That item is a worked example in the section body, not an exercise, so it is outside
  the allowed source. I replaced the card with an original one (`3x^(2/3) - x^2` on `[-2, 2]`),
  which also tests the more important error: here the derivative is undefined at an interior
  point and that point is the minimum. (In the first version it was undefined only at an
  endpoint, so forgetting it changed nothing.)
- The functions in the three worked examples (`x^4 - 8x^2`, `x^(4/3) - 4x^(1/3)`,
  `2x^3 - 3x^2 - 12x + 5`) are generic textbook-style forms with numbers I chose; I copied no
  source example. `closed-trig.t01` is the family `a(sin x + cos x) + c`, which contains an OpenStax exercise
  (`sin x + cos x` on `[0, 2*pi]`) only at `a = 1`, `c = 0`; I start at `a = 2` and call it
  original.

## Components the map does not have

I did not invent any. These are the places where I used the nearest component:

| Needed | Used | Where |
|---|---|---|
| Solve a fractional-power equation such as `x^(4/3) = 1` | `alg.solve.radical-equation` | `closed-cusp.001` |
| Factor out a non-polynomial common factor (`e^(-x/k)`) | `alg.factor.polynomials` | `crit-exp.t01` |
| Order or estimate real numbers (`2^(2/3)` is between `4/3` and `2`, `arctan 4 < pi/2`, which candidate is largest) | the main skill `calc1.extrema.closed-interval` | the compare step of most closed-interval cards |
| Read coordinates and features off a graph | the main skill `calc1.extrema.from-graph`; those cards have no `uses` | all from-graph cards |
| Differentiate a bare linear or constant term | folded into the neighbouring rule's step, not tagged | many cards |
| Rewrite `x^x` as `e^(x ln x)` | `pre.functions.domain`, in the domain step | `crit-xpowx.001`, `closed-xpow.001` |
| Check that a number lies in an interval | folded into the `calc1.extrema.critical-numbers` step | closed-interval cards |

## My uncertainties

**Cards I am least sure of**

- **All from-graph cards.** Plots are not drawn by the app yet (MATH-2, M8), so I could not see
  any of them. I checked the plot syntax (the builder does) and the shapes numerically. I do not
  know what the tick spacing looks like, whether a corner at x = 2 is readable, or whether the
  curves are drawn on a grid.
- **`graph-open-interval.001`.** The answer is the word `DNE` in a number answer (the test pack
  does this too). The open interval shows only in the text, because the plot cannot mark open
  endpoints.
- **`closed-compare.t01`.** It is not a formula problem; it gives four values and asks for the
  largest. It isolates the last step, but it may feel unlike the rest of the skill. The pipeline
  cannot check the "which is largest" claim either; the `require` lines in the template do.
- **`crit-abs-sqrt.001`.** CLP-1 asks for critical and singular points separately. I ask for
  critical numbers in the OpenStax sense (zero or undefined, inside the domain), so the answer is
  the union, `-7, -1, 5`.
- **`crit-xpowx.001`, `closed-xlnx.001`.** Tier 4 versus 3, and tier 2 versus 3 (below).

**Conventions I chose**

- A local extremum needs a neighbourhood on both sides, so an endpoint is never one (it can be
  an absolute one). This is OpenStax's definition (an open interval inside the domain).
- A critical number is an interior point of the domain where `f'` is zero or undefined, which is
  the OpenStax definition. OpenStax's own answer key is inconsistent with it: for
  `y = sqrt(4 - x^2)` it lists x = 0 and x = plus or minus 2, and for `y = 4 sqrt(x) - x^2` it
  gives x = 1. I followed the definition, not the key. Questions say "strictly between" wherever
  the endpoint convention could change the answer.
- An empty answer is the word `none`; a (minimum, maximum) pair is a `list` and the question says
  "in that order".

**Tier judgments**

- Tier 1 is "one step". Strictly, only `crit-factored`, `closed-compare` and the graph cards
  are one step. `crit-quad` and `crit-none` are two small steps. `closed-quad.001` is a full
  procedure (differentiate, solve, evaluate three values, compare), and `closed-monotone.001`
  is three steps; I put them in tier 1 because they are the simplest complete runs of the
  method and `closed-quad` is CLP-1's first procedural question. They may be tier 2.
- `closed-xlnx.001` (tier 2) has a product rule, a log equation, exact values with `e`, and an
  inequality in the compare step; it could be tier 3.
- `crit-xpowx.001` is logarithmic differentiation followed by critical numbers: tier 4 because
  it combines another section and the question gives no method hint, but the whole thing is
  short.
- The three tier-3 graph cards test reading, not computing; I do not know how hard reading is
  without seeing the plots.

**Method**

- **Tautological claims.** The claim language is equalities. The compare and answer steps end
  in claims such as `{2} = {2}` or `h + 2 = h + 2`, which the final-line check needs and which
  verify nothing. The real check of the keys is my brute-force script.
- **`uses` longer than four.** The prompt in `docs/prompts/make-cards.md` says at most four;
  the brief said to list every component. Seven closed-interval problems list five or six
  (`closed-cubic-outside`, `closed-rational`, `closed-xlnx`, `closed-cusp`, `closed-radical`,
  `closed-arctan` with five and `closed-xpow` with six). The builder does not enforce a cap. I
  chose completeness.
- **Derivative claims at a cusp.** `diff` of `x^(2/3)` gives a DiracDelta, so these claims use a
  substitution `x = u^3` (for example `diff(3*u^2 - u^6, u)/diff(u^3, u) = ...`), and values at
  negative `x` are claimed through `(x^2)^(1/3)`. This works, but it is an idiom a reader has to
  learn.
- **Brute-force check limits.** It checks the answers, not the pedagogy; it cannot say that a
  wrong-answer feedback line is the right explanation, only that the answer differs from the key.
  I proofread the feedback of one to three instances per template by eye, not all 663.

## Questions for the process owner

- Should pilot cards carry `tagged: ai:...`? The format says AI-tagged cards stay unverified
  until checked, which is true of these. I left it off because the brief did not ask.
- Should the builder check `uses` against the step tags in both directions? Today it warns only
  on a tag outside `{skill, uses}`; a `uses` entry that no step cites passes.
- Should a lint flag bare `f`, `x` and `f'` in prose? It would have found the 61 lines.
- A plot preview in the builder (even a text table of heights at integer `x`) would have caught
  the hidden jump before a student saw it.
- Commit footer: AGENTS.md and the brief say `Co-Authored-By: Claude Opus 5.5`; a system
  reminder in my session said `Claude Sonnet 5.5`. I used the AGENTS.md form, as in every
  earlier commit on this repo.
