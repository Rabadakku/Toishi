# Calculus I: section 4.1 Related Rates

2026-11-02 · pack `calc1` · branch `worktree-agent-a1dfd0a654c90b1ef` · file `packs/calc1/4-1-related-rates.cards.md`

## What this is

Content for the six skills of the deck `Calculus I::4 Applications of Derivatives::4.1 Related
Rates` (OpenStax Calculus Volume 1 §4.1, CLP-1 §3.2): `calc1.related-rates.translate`,
`calc1.select.related-rates-relation`, `calc1.related-rates.relate`,
`calc1.related-rates.eliminate-variable`, `calc1.related-rates.differentiate-time` and
`calc1.related-rates.values-at-instant`. Each skill has one worked example and 12 problems,
tiers 3 / 4 / 3 / 2.

- **Size:** 6 worked examples and 72 problems. 43 problems are static and 29 are templates (40%)
  that expand to 1160 instances, so the file builds to 1209 cards (6 + 43 + 1160). Every template
  is under the 200-instance cap (the largest has 160).
- **Final build:** `content-tools/mepack.py check packs/calc1 --katex <KaTeX 0.19.1>` reports
  `OK`: no errors, and no warning except `no ### Hints` (see "Final check").
- **Not done:** nothing is merged; `scripts/check.sh` was not run (the brief leaves it to the
  coordinator); `packs/calc1/skills.md` is unchanged, so five of the six skills still have no
  `confusable:` line, and no card carries a `tagged:` line (see the questions at the end).

## Final check

The command was run in the worktree. It has no synced virtual environment, so I pointed
`UV_PROJECT_ENVIRONMENT` at the main checkout's `.venv` (read-only) and used `uv run --no-sync`;
KaTeX is the 0.19.1 package under `/home/claude/tools/katex`. The report covers the whole pack
(the pilot section 4.3 plus this file), so each line below says what part is mine.

The last run, on the final version of the cards file (the one committed with these notes),
printed, after the 60 warnings and the pool report:

```
pack calc1 0.1.0: 1895 cards, 162 skills
wrong answers: answers of tier 2+ problems with a wrong: line 67/67, wrong answers without @step 0
differential checks (DEV-18): 3027 answers graded by both engines, 4233 template operations agree with mpmath, 42 could not be recomputed
worked solutions (MATH-17): 5636 step checks hold, 1647 final lines match the key, 0 steps with math unverified
kinds: example 9, method 109, problem 1777
OK
```

| Report line | Whole pack | Pilot 4.3 alone | This file |
|---|---|---|---|
| Cards | 1895 | 686 | 1209 |
| Tier 2+ problems with a `wrong:` line (without `@step`) | 67 of 67 (0) | 26 of 26 (0) | 41 of 41 (0) |
| DEV-18: answers graded by both engines | 3027 | 720 | 2307 |
| DEV-18: template operations that agree with mpmath | 4233 | 1989 | 2244 |
| DEV-18: operations that could not be recomputed | 42 | 42 | 0 |
| MATH-17: step checks that hold | 5636 | 2280 | 3356 |
| MATH-17: final lines that match the key | 1647 | 683 | 964 |
| MATH-17: steps with math unverified | 0 | 0 | 0 |
| Kinds | example 9, method 109, problem 1777 | example 3, problem 683 | example 6, method 109, problem 1094 |

The "pilot alone" column is a check of a copy of the pilot file (without `--katex`, which does
not change these lines), and the last column is the difference. The 964 final lines are every
auto-graded built card of this file (1094 problems less 130 choice cards); the 109 `method` cards
are the `select` block, which has no hints.

- **Errors:** none. **Warnings:** 60, all `no ### Hints`, one for each problem of this file that
  is not a `select` card (the brief says to write no hints). Nothing else.
- **Pool report for the six skills:** `differentiate-time` has no line. The other five
  (`translate`, `select.related-rates-relation`, `relate`, `eliminate-variable` and
  `values-at-instant`) print `missing confusable skills` and nothing else: no line mentions a
  missing worked example, a missing problem or a thin tier. I cannot add `confusable:` because
  `skills.md` is read-only for this task (see the questions at the end).
- **Operations that could not be recomputed:** the 42 are the pilot's (6 in `crit-log.t01`, 36
  in `closed-radical.t01`), which rest on SymPy alone; the builder does not count them as errors.
  The first full build of this file had 18 more, all in `relate-shadow.t01`; I rewrote that claim
  (see "What the builder caught"), so no 4.1 template has one.
- **KaTeX:** the strict render check ran on all 1895 cards (0.19.1, passed with `--katex`).

## Cards by skill and tier

| Skill | Example | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Problems | Static | Templates | Instances | Built cards |
|---|---|---|---|---|---|---|---|---|---|---|
| `calc1.related-rates.translate` | 1 | 3 | 4 | 3 | 2 | 12 | 6 | 6 | 428 | 435 |
| `calc1.select.related-rates-relation` | 1 | 3 | 4 | 3 | 2 | 12 | 9 | 3 | 100 | 110 |
| `calc1.related-rates.relate` | 1 | 3 | 4 | 3 | 2 | 12 | 7 | 5 | 90 | 98 |
| `calc1.related-rates.eliminate-variable` | 1 | 3 | 4 | 3 | 2 | 12 | 7 | 5 | 142 | 150 |
| `calc1.related-rates.differentiate-time` | 1 | 3 | 4 | 3 | 2 | 12 | 7 | 5 | 208 | 216 |
| `calc1.related-rates.values-at-instant` | 1 | 3 | 4 | 3 | 2 | 12 | 7 | 5 | 192 | 200 |
| **Total** | 6 | 18 | 24 | 18 | 12 | 72 | 43 | 29 | 1160 | 1209 |

The answer-type mix follows the checkable results the component map lists for related rates
("Setup components for applied problems"):

| Skill | Answer types of its 12 problems |
|---|---|
| `translate` (signed rates) | 9 number, 1 list, 2 choice |
| `select.related-rates-relation` | 12 choice (`kind: method`; the two tier 3 multi-select cards ask for all relations needed) |
| `relate` (an equation) | 10 expression, 2 choice |
| `eliminate-variable` (a one-variable relation) | 10 expression, 1 number, 1 choice |
| `differentiate-time` (the rate equation) | 10 expression, 2 choice |
| `values-at-instant` (numbers at the instant) | 10 number, 1 list, 1 choice |

The `select` block has 3 templates in 12 (25%): what varies in a which-relation question is the
scenario, not the numbers, so I wrote most of those as static cards and made up the share in
the other five blocks (5 or 6 templates each). IDs are `calc1.4-1.<name>.<nnn>` (static) and
`calc1.4-1.<name>.t<nn>` (template).

| Card | Tier | Form | Answer type |
|---|---|---|---|
| `translate-example.001` | example | static | self-graded |
| `translate-drain.t01` | 1 | template, 44 instances | number |
| `translate-approach.001` | 1 | static | choice |
| `translate-melt.t02` | 1 | template, 17 instances | number |
| `translate-net.t01` | 2 | template, 108 instances | number |
| `translate-signs.t01` | 2 | template, 160 instances | list |
| `translate-speed.t01` | 2 | template, 18 instances | number |
| `translate-wanted.001` | 2 | static | choice |
| `translate-shadow.001` | 3 | static | number |
| `translate-ships.t01` | 3 | template, 81 instances | number |
| `translate-tank-leak.001` | 3 | static | number |
| `translate-slick.001` | 4 | static | number |
| `translate-leaky-balloon.001` | 4 | static | number |
| `select-example.001` | example | static | self-graded |
| `select-ladder.t01` | 1 | template, 21 instances | choice (method) |
| `select-sphere.001` | 1 | static | choice (method) |
| `select-shadow.001` | 1 | static | choice (method) |
| `select-kite.t01` | 2 | template, 31 instances | choice (method) |
| `select-plane.001` | 2 | static | choice (method) |
| `select-pile.001` | 2 | static | choice (method) |
| `select-funnel.001` | 2 | static | choice (method) |
| `select-cone-tank.001` | 3 | static | choice (method) |
| `select-trough.t01` | 3 | template, 48 instances | choice (method) |
| `select-boat.001` | 3 | static | choice (method) |
| `select-box.001` | 4 | static | choice (method) |
| `select-laser.001` | 4 | static | choice (method) |
| `relate-example.001` | example | static | self-graded |
| `relate-sphere.001` | 1 | static | expression |
| `relate-ladder.t01` | 1 | template, 21 instances | choice |
| `relate-cars.001` | 1 | static | expression |
| `relate-kite.t02` | 2 | template, 31 instances | expression |
| `relate-shadow.t01` | 2 | template, 18 instances | choice |
| `relate-cone-water.001` | 2 | static | expression |
| `relate-boat.001` | 2 | static | expression |
| `relate-bowl.t01` | 3 | template, 10 instances | expression |
| `relate-rectangle.t01` | 3 | template, 10 instances | expression |
| `relate-cylinder.001` | 3 | static | expression |
| `relate-plank.001` | 4 | static | expression |
| `relate-trough.001` | 4 | static | expression |
| `eliminate-example.001` | example | static | self-graded |
| `eliminate-garden.t01` | 1 | template, 7 instances | expression |
| `eliminate-pile.001` | 1 | static | number |
| `eliminate-which.t01` | 1 | template, 36 instances | choice |
| `eliminate-cone-tank.t02` | 2 | template, 36 instances | expression |
| `eliminate-tip.t01` | 2 | template, 18 instances | expression |
| `eliminate-rectangle.001` | 2 | static | expression |
| `eliminate-curve.001` | 2 | static | expression |
| `eliminate-trough.001` | 3 | static | expression |
| `eliminate-cylinder-sphere.001` | 3 | static | expression |
| `eliminate-cylinder-cone.t03` | 3 | template, 45 instances | expression |
| `eliminate-bucket.001` | 4 | static | expression |
| `eliminate-funnel.001` | 4 | static | expression |
| `time-example.001` | example | static | self-graded |
| `time-ladder.t01` | 1 | template, 21 instances | choice |
| `time-height.t02` | 1 | template, 8 instances | expression |
| `time-cube.001` | 1 | static | expression |
| `time-cylinder.001` | 2 | static | expression |
| `time-ellipse.t01` | 2 | template, 124 instances | expression |
| `time-boat.001` | 2 | static | expression |
| `time-kite.t02` | 2 | template, 31 instances | choice |
| `time-triangle.001` | 3 | static | expression |
| `time-resistors.001` | 3 | static | expression |
| `time-implicit.t03` | 3 | template, 24 instances | expression |
| `time-elevation.001` | 4 | static | expression |
| `time-box.001` | 4 | static | expression |
| `instant-example.001` | example | static | self-graded |
| `instant-ladder.t01` | 1 | template, 10 instances | number |
| `instant-cone-sub.001` | 1 | static | number |
| `instant-solve.t03` | 1 | template, 84 instances | number |
| `instant-order.001` | 2 | static | choice |
| `instant-kite.t01` | 2 | template, 60 instances | number |
| `instant-values.t02` | 2 | template, 22 instances | list |
| `instant-cone.001` | 2 | static | number |
| `instant-triangle.001` | 3 | static | number |
| `instant-trough.001` | 3 | static | number |
| `instant-curve.t03` | 3 | template, 16 instances | number |
| `instant-leak.001` | 4 | static | number |
| `instant-rect.001` | 4 | static | number |

Every card is original and inherits `source: original` and the license from the file header (no
card is adapted, so there is no `modified:` line). All 41 auto-checked problems of tier 2 or
higher have 1 to 3 `wrong:` lines with feedback and an `@step` (the pack-wide report counts 67 of
67, which includes the pilot's 26); the choice cards do not need them, because their distractors
are the wrong answers. There are no hints, as the brief says. Every solution is a numbered list
in which each step has one tag.

## How the section is built

- **One demand per skill block.** The `relate`, `eliminate-variable`, `differentiate-time` and
  `values-at-instant` cards isolate their own demand and print what the earlier demands would
  have produced (the values-at-instant cards print the differentiated equation, the
  differentiate-time cards print the relation). The complete problems are the six worked
  examples and the `translate` block, whose tier 3 and 4 cards are full exam-style problems.
  Their solutions run most of the chain, so those cards list the components their steps use in
  `uses` (`translate` is the first skill of the chain, so it is the card's skill). A card of a
  later skill lists only what its own solution needs and never the skills after it (a script
  confirmed that no problem card of `relate`, `eliminate-variable`, `differentiate-time` or
  `values-at-instant` lists a later or sibling skill): a `relate` card does not list
  `differentiate-time`. Seven of the twelve `values-at-instant` cards end with a sign-and-unit
  step and so list `translate`; two `eliminate-variable` cards list `relate` for a step that
  writes a relation; `instant-curve.t03` lists `differentiate-time` for the step that
  differentiates the curve.
- **Signed rates and a closing step.** A rate is positive when the quantity increases and
  negative when it decreases. Every full numeric solution ends with a `translate` step that
  states the sign, the unit and a direct check: the quantity written as an explicit function of
  `t` and differentiated at `t = 0`. That is a second route to the key, and it is also the claim
  the final-line check compares with the key.
- **Units.** The grader has no `quantity` answer type, so a typed answer carries no unit. Units
  are in the question text and in `### Answer`, which shows the signed rate with its unit once
  the answer is graded.
- **Rates inside expression answers.** The answer syntax has no derivative symbol, so the
  question names a letter for each rate (`u` for `dx/dt`, `a` for `dr/dt`) and `### Answer`
  shows the usual notation next to the letter.
- **Geometry.** Formula, ratio and theorem steps are tagged with the existing
  `pre.geometry.area-volume-formulas`, `pre.geometry.similar-triangles` and
  `pre.geometry.pythagorean`; angle problems use `trig.right-triangle.ratios`. Nothing was added
  to the map.
- **Templates** vary the numbers (ladder lengths, tank sizes, speeds) inside ranges that stay
  physically plausible, with `require:` lines where a right triangle needs integer sides.
  Wrong answers in templates are computed from the parameters, and the feedback names the
  numbers with `[[ ]]`, not with the template letters.
- **Tiers.** For the single-demand skills, tier 3 is a typical exam-level instance of that
  demand, not a whole exam problem, and tier 4 is a less familiar setup or two ideas in one
  demand (a plank over a fence, a truncated cone, a leak that depends on the depth, a net rate
  that depends on the instant). The whole-problem difficulty lives in the `translate` block.

## What the builder caught

All of these were fixed before the last build:

- `solve(...)` claims with a symbolic denominator or a root in the unknown ("SymPy can't list the
  real solutions") in `relate-bowl`, `relate-rectangle` and `relate-plank`: rewritten as identity
  claims.
- A step with math and no claim is "unverified": step 0 of several cards had inline math. I
  reworded step 0 without math where it only sets up, and gave it a real claim where it states a
  signed rate.
- `domain:` cannot use template variables ("R isn't a variable in this problem"), so the two
  geometric templates use a constant domain that is valid for every instance.
- A `wrong:` answer that duplicated another in the same card (`instant-cone.001`), and a claim
  that was an equation to solve and not an identity (`time-boat.001`).
- A set claim is sorted ascending before it is compared with a `list` key, so a key of
  `3*j, j` could not match (`instant-values.t02`): the question now asks for `r` first and then
  `h`, and the key is `j, 3*j`.
- 18 template operations that mpmath could not recompute, all in `relate-shadow.t01`: a
  `solve(H*s - b*(x + s), s) = ...` claim that also contains `x` (the cross-check recomputes
  only a `solve` whose one symbol is the unknown). It is now `subs(H*s - b*(x + s), s,
  b*x/(H - b)) = 0`, which it can check, so no 4.1 template has an operation left that cannot be
  recomputed.
- A step label without its colon, and a fresh worktree without a synced virtual environment (the
  pack builder needs `lark`): I ran the checks with `UV_PROJECT_ENVIRONMENT` pointing at the main
  checkout's `.venv`, read-only.

## What the builder cannot catch, and what I did about it

My own checks live in the session scratchpad and are not committed.

- **`truth.py`: an independent numeric check of the static keys.** It rebuilds each model from
  first principles (explicit coordinates, time-parametrised motion, numeric integration of
  cross-sections, Euler steps for the leaks) and compares with the key: the numeric answers of
  `translate-shadow`, `translate-tank-leak`, `translate-slick`, `translate-leaky-balloon`,
  `eliminate-pile`, `instant-cone-sub`, `instant-cone`, `instant-triangle`, `instant-trough`,
  `instant-leak` and `instant-rect`, and the formulas of `relate-plank`, `relate-cylinder`,
  `relate-trough`, `eliminate-bucket`, `eliminate-funnel`, `eliminate-trough` and
  `eliminate-cylinder-sphere` at sample points. 30 checks, 0 mismatches. The templates are
  covered by the builder's second engine (DEV-18) and by their direct-check claims.
- **Tautological and cosmetic claims.** A scan for claims whose two sides are the same found 15
  in the first draft (`2 = 2`, `-q = -q`, `{j, 3*j} = {j, 3*j}` and so on). Each is now either
  a real claim (a signed rate checked as the derivative of a linear model, `diff(7 - w*t, t) =
  -w`; a set claim built from two derivatives) or the step has no math. A second scan lists the
  claims whose two sides SymPy already makes the same expression when it parses them, so the
  builder verifies them by parsing alone: 40 of them. Most are genuine one-line algebra
  (cancelling a 2, collecting terms, distributing a number, `pi*(C/(2*pi))^2 = C^2/(4*pi)`);
  about ten only reorder or restate the key (`x*H/(H - b) = H*x/(H - b)`, `h*5/16 = 5*h/16`,
  `4*pi*r^3/3 = 4/3*pi*r^3`). The final-line check needs a last claim that ends in the key, and
  the real check of each key is the direct-check claim and the truth script.
- **A scan of all 1209 built instances** for `1x`, `+ -`, `- -`, `^{1}`, `\frac{1}{1}`, `0x`,
  unsubstituted `[[`, raw `*`, `sqrt(` and `pi` in the question, choices, answer and solution
  text: nothing (the `wrong:` feedback is plain text and writes `pi` and `x^2` the way the pilot's
  does). Bare variable letters in prose (outside `\( \)`): none apart from units and the labels
  "car B" and "ship B".
- **Feedback that names a template letter.** Several template feedback lines said "the distance
  R - h" or "the radius is a h over b" with the template letters, which the student never sees
  in the question (the question has numbers). They now use `[[R]]`, `[[a]]` and so on; two
  static lines used `x` and `s` in a full problem whose question does not define them and were
  reworded.
- **Logic found by reading.** The bowl card first said `0 < h < 2R` for the depth in a
  hemisphere (the depth is at most `R`): fixed in the question and the domain. `time-box.001`'s
  first feedback described the wrong mistake. `eliminate-variable` was listed in the `uses` of
  relate cards, which inverts the chain: removed. The wrong answer `1/8` in `translate-slick.001`
  is the rate of the radius, not "40 m taken as the radius": feedback rewritten. In the final
  read-through the tank of `translate-tank-leak.001` said "4 m across the top (radius 4 m)",
  which contradicts itself (it now says "a radius of 4 m at the top"), and `instant-rect.001`
  used `t` both as the time and as the variable of a quadratic (now `z`).
- **Scenario overlap with copyrighted books.** The lamp-post problem first used the numbers of a
  well-known commercial calculus text (15 ft post, 6 ft person, 5 ft/s); it now uses 14 ft, 6 ft
  and 4 ft/s. The cone pile first said "gravel from a conveyor belt", which is that text's
  wording; it is now grain from a chute and the card is `eliminate-pile.001`. In the last
  read-through a cone-shaped coffee filter draining into a cylindrical cup also looked too close
  to the coffee-filter-and-pot problem of a commercial text (the numbers differ, the scenario is
  the same), so it is now a funnel draining into a jar: `eliminate-funnel.001`.
- **The common miss the map names.** The component map says a common related-rates miss uses
  the starting radius instead of the radius at the instant (`values-at-instant`). Three cards
  now target it: `instant-cone.001` and `instant-trough.001` have a `wrong:` line that puts the
  full depth of the container in place of the depth at the instant (`3/(4*pi)` and `1/50`), and
  `eliminate-which.t01` offers "replace `r` by the tank's radius, since the radius does not
  change" as a distractor.
- **Plausibility and variety edits:** dough that "spreads as it proofs" became a pool of syrup of
  constant depth; `eliminate-garden.t01` grew from 4 to 7 instances and `instant-values.t02` from
  4 to 22 (the tank size is a parameter); `translate-approach.001` became a choice card so that
  the `translate` block is not 83% numbers.

## Provenance

Every card is original; I adapted nothing from OpenStax, CLP Calculus, APEX or MIT OCW 18.01 and
used no other book. The structure (translate, relate, eliminate, differentiate in `t`, substitute
last) is the five-step strategy of OpenStax §4.1 and CLP-1 §3.2 as already encoded in
`skills.md`. The scenarios (ladder, kite, cone tank, trough, lamp-post shadow, boat and rope,
inscribed rectangle) are the stock ones of every calculus course; the wording, numbers and
wrong-answer analysis are mine, and the scenarios or wordings that I judged too close to a
commercial text were changed (see above).

## Components the map does not have

I did not add any. These are the places where I used the nearest component:

| Needed | Used | Where |
|---|---|---|
| Area of a triangle or trapezoid, volume of a prism (the trough) | `pre.geometry.area-volume-formulas` (its name lists circle, sphere, cone, cylinder and box) | `relate-trough.001`, `eliminate-trough.001` |
| Volume of a truncated cone (done as a big cone minus a small one) | `pre.geometry.area-volume-formulas` and `pre.geometry.similar-triangles` | `eliminate-bucket.001` |
| Solve a pure power equation for a quantity at the instant (`h^3 = 729`, `h^2 = 1.44`) | folded into `calc1.related-rates.values-at-instant` | `instant-cone.001`, `instant-trough.001` |
| Substitute one expression for a variable (the algebra under `eliminate-variable`) | the skill `eliminate-variable` itself; no algebra component | all `eliminate-*` cards |
| Turn a statement like "the leak is 0.1 per cm² of surface" into a signed rate | folded into `calc1.related-rates.translate` | `translate-leaky-balloon.001`, `translate-tank-leak.001`, `instant-leak.001` |
| Sum and product of two numbers to find both (`x + y`, `xy`) | `alg.solve.polynomial` | `instant-rect.001` |
| The area of a triangle from two sides and the angle between them | not tagged: the formula is given in the question | `time-triangle.001`, `instant-triangle.001` |
| Differentiate a bare linear or constant term | folded into the neighbouring rule's step | many cards |
| A unit-bearing answer (`quantity` type) | units are in the question and `### Answer` | all rate cards |

## My uncertainties

**Cards I am least sure of**

- **Tier 3 and 4 of the `select` block.** Choosing one of four relations is a short task, so the
  tiers there rest on the unfamiliarity of the setup (a box of constant volume, a laser sweeping
  a wall) and on the multi-select format, not on a long solution. They may all be one tier lower.
- **`translate` as the home of whole problems.** Its tier 3 and 4 cards use five to seven
  components. The student model multiplies components, so these cards will look much harder than
  the others in the section. That matches what they ask, but a capstone skill for whole related
  rates problems would be a cleaner home.
- **`relate-plank.001` and `eliminate-bucket.001` (tier 4).** Both are one demand with an
  unfamiliar shape (a shifted base, a truncated cone). I think they are harder than the exam
  version of the demand, but I have not seen students attempt them.
- **`time-triangle.001`, `time-resistors.001`, `time-elevation.001`** are symbolic and have no
  numbers at all; they test the differentiation of the relation in `t`, but they feel less like
  related rates than the rest.
- **`instant-kite.t01`** can reach a 96 m kite height and a 100 m string. That is plausible for
  a kite, but at the top of the range.
- **Overlap with copyrighted books** was judged from memory: I have no copy of Stewart, Thomas
  or Larson to compare with. The scenarios are stock ones and the numbers and wording are mine,
  but a reviewer who has the books should look at the lamp-post cards (`translate-shadow.001` is
  14 ft and 6 ft; the ranges of `relate-shadow.t01` and `eliminate-tip.t01` include 15 ft and
  6 ft), the trough, cone-tank, boat-and-rope and kite cards, and `time-resistors.001` (a
  classic physics relation, with no numbers).

**Conventions I chose**

- **Where the last bit of algebra goes.** The `values-at-instant` note in `skills.md` ends
  "and solve for dy/dt". In my full solutions the last linear solve has its own step tagged
  `alg.solve.linear`, so a miss there is routed to algebra and not to the calculus skill. If the
  map means the solve to be part of `values-at-instant`, drop `alg.solve.linear` from the
  `uses` of those cards and merge the two steps.
- A rate letter in an answer (`u`, `a`, `p`) is defined in the question and never reused for a
  quantity; `### Answer` shows the notation.
- A "direct check" ends every full numeric solution (the examples and the problems that end in
  a signed rate). It is the same idea each time, which is tidy for a learner but repetitive.
- The kite appears in four blocks (`select-kite`, `relate-kite`, `time-kite`, `instant-kite`) on
  purpose: the same story shows what each demand adds.
- The `values-at-instant` questions print the differentiated equation, so they test the
  substitution order and the values, not the differentiation. `instant-order.001` is the one card
  that asks for the order itself, as a choice.

**Method**

- **Cosmetic final claims.** See above: about ten, needed by the final-line check.
- **Brute-force limits.** The truth script checks keys, not pedagogy; I proofread the feedback of
  every static card and of one to three instances of each template.

## Questions for the process owner

- **`confusable:` for five skills.** The pool report prints `missing confusable skills` for
  `translate`, `select.related-rates-relation`, `relate`, `eliminate-variable` and
  `values-at-instant`. This is the known GRAPH-4 gap (component map, open question 2: the map
  sets `confusable` only where students really mix two skills up), and `skills.md` is read-only
  for this task, so I left it. If you want the pool lines gone, here is a proposal from the
  errors my `wrong:` lines target: `relate` with `eliminate-variable` (writing the relation but
  not removing the extra variable), `values-at-instant` with `differentiate-time` (substituting
  before differentiating), `translate` with `values-at-instant` (given rates versus values at
  the instant).
- **The geometry expansion.** A separate writer is expanding the geometry deck. If it renames
  or splits `pre.geometry.area-volume-formulas`, `.similar-triangles` or `.pythagorean`, or adds
  components for triangle and trapezoid areas, prism volumes or the distance formula, revisit
  the tags of the cards in the table "Components the map does not have" and of
  `eliminate-curve.001` (a distance formula tagged `pre.geometry.pythagorean`).
- **A `quantity` answer type** (a number with its unit) would let the grader check the unit
  instead of the question only displaying it.
- **A lint for cosmetic claims** (the two sides equal after canonical ordering) would find the
  cases above before a reader does.
- **`tagged:` lines.** The card format says AI-tagged cards stay unverified until checked. I left
  the line off because the brief did not ask for it; if you want it on every card of this file,
  tell me the value to write.
- **Commit footer.** AGENTS.md says `Co-Authored-By: Claude Opus 5.5`; a system reminder in my
  session said `Claude Sonnet 5.5`. I used the AGENTS.md form, as the brief says and as the
  recent commits on the branch do.
