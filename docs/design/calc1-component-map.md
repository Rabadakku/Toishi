# Calculus I component map

2026-11-02 · pack `calc1` · branch `calc1-map`

## What this is

`packs/calc1/skills.md` is the Calculus I component map for the new student model. A component
is one procedure, rule, fact or setup move that a student can know or not know independently.
A problem's components are its `skill`, its `uses` and its step tags, and every solution step
names exactly one component. The model predicts a student's chance on a problem from those
components, so two procedures that fail independently must be two components.

- **Size:** 172 components. 123 are calculus components (`calc1.`) and 49 are precalculus
  components (`alg.`, `trig.`, `pre.`) that calculus solution steps use. There are 7
  method-choice components and 60 confusable pairs. (The 0.6 Geometry block grew from 3
  components to 13 when its cards were written; see "The 0.6 Geometry block".)
- **Checks:** the file loads with `core/cards/skillfile.py` and passes `core/cards/graph.py`
  with no unknown IDs, no cycles and no redundant prerequisite edges. Every skill has a name,
  deck, textbook reference and Notes line. All 340 math fragments in the Notes render with KaTeX
  0.19.1 (the web UI's pinned version) in strict mode. `mepack.py check --no-render` passes.
- **Not shipped yet:** there are no problems, and the pack is not in `app/packs.py` `SHIPPED`.
- **Structure:** decks follow OpenStax Calculus Volume 1 (CC BY-NC-SA 4.0), Chapters 2 to 5,
  using its section numbers and titles, for example
  `Calculus I::4 Applications of Derivatives::4.3 Maxima and Minima`. Chapter 1 appears only as
  precalculus components, under `Calculus I::0 Precalculus Skills` in six topical decks (my own
  grouping: OpenStax Chapter 1 doesn't cover algebra).
- **Textbook references:**
  - OpenStax Calculus Volume 1 everywhere;
  - CLP-1 (UBC, CC BY-NC-SA 4.0) for Chapters 2 to 4;
  - CLP-2 for Chapter 5, because CLP-1 stops at antiderivatives;
  - OpenStax College Algebra 2e and Precalculus 2e for algebra and trigonometry that the calculus
    books don't teach.
- **How the sources were used:** I read the OpenStax CNXML (section outlines, examples,
  problem-solving strategy boxes and exercise groups), the CLP tables of contents, and CLP-1's
  chain-rule section. No text was copied except section titles. The structure is original.
- **IDs** are `calc1.<topic>.<step>` and `alg|trig|pre.<topic>.<step>`, lowercase with dashes.
  They are permanent: never rename or reuse one. They reuse the IDs that `docs/card-format.md`
  already shows where those fit:
  - `calc1.extrema.critical-numbers`;
  - `calc1.deriv.power-rule`;
  - `calc1.deriv.chain-rule`;
  - `calc1.shape.first-derivative-test`;
  - `calc1.shape.inflection-points`;
  - `calc1.select.limit-technique`;
  - `alg.factor.polynomials`;
  - `alg.solve.polynomial`.

## Components per section

| Section | Components | Section | Components |
|---|---|---|---|
| 0.1 Algebraic Expressions | 11 | 3.7 Derivatives of Inverse Functions | 2 |
| 0.2 Equations and Inequalities | 7 | 3.8 Implicit Differentiation | 1 |
| 0.3 Functions and Graphs | 7 | 3.9 Derivatives of Exponential and Logarithmic Functions | 3 |
| 0.4 Trigonometry | 7 | 4.1 Related Rates | 6 |
| 0.5 Exponents and Logarithms | 4 | 4.2 Linear Approximations and Differentials | 4 |
| 0.6 Geometry | 13 | 4.3 Maxima and Minima | 3 |
| 2.1 A Preview of Calculus | 2 | 4.4 The Mean Value Theorem | 3 |
| 2.2 The Limit of a Function | 3 | 4.5 Derivatives and the Shape of a Graph | 7 |
| 2.3 The Limit Laws | 9 | 4.6 Limits at Infinity and Asymptotes | 6 |
| 2.4 Continuity | 5 | 4.7 Applied Optimization Problems | 6 |
| 2.5 The Precise Definition of a Limit | 2 | 4.8 L'Hôpital's Rule | 7 |
| 3.1 Defining the Derivative | 2 | 4.9 Newton's Method | 2 |
| 3.2 The Derivative as a Function | 3 | 4.10 Antiderivatives | 4 |
| 3.3 Differentiation Rules | 6 | 5.1 Approximating Areas | 4 |
| 3.4 Derivatives as Rates of Change | 4 | 5.2 The Definite Integral | 5 |
| 3.5 Derivatives of Trigonometric Functions | 3 | 5.3 The Fundamental Theorem of Calculus | 4 |
| 3.6 The Chain Rule | 5 | 5.4 Integration Formulas and the Net Change Theorem | 3 |
| | | 5.5 Substitution | 7 |
| | | 5.6 Integrals Involving Exponential and Logarithmic Functions | 1 |
| | | 5.7 Integrals Resulting in Inverse Trigonometric Functions | 1 |

By chapter:

| Chapter | Components |
|---|---|
| 2 Limits | 21 |
| 3 Derivatives | 29 |
| 4 Applications of Derivatives | 48 |
| 5 Integration | 25 |
| 0 Precalculus Skills | 49 |

The skill's deck is the section that first teaches the procedure. A component used later lives
where it was taught. For example, `calc1.deriv.tangent-line` sits in 3.1, and 4.2's
linearization problems are tagged with it.

## Tagging conventions

These rules keep the tags consistent across authors and AI taggers. Each skill's Notes line shows
a sample step.

1. **One move per step.** If a step uses two components, split it. For example, write
   "inner derivative: \(-ax^{-2}\)" `[calc1.deriv.power-rule-rational]` and "chain:
   \(e^{a/x}\cdot(-ax^{-2})\)" `[calc1.deriv.chain-rule]` as two steps.
2. **Algebra gets its own component.** Factoring, solving, simplifying, exact values and sign
   charts go to `alg.`, `trig.` or `pre.` components. The calculus component tags only the
   calculus move.
3. **Step 0** is the card's skill, or a `calc1.select.*` component when choosing the method is the
   hard part (card-format.md, "Step-tagged solutions").
4. **Name the inner function in its own step** for every non-linear composite, tagged
   `[pre.functions.decompose]`. For a linear inside \(ax + b\),
   `calc1.deriv.chain-linear-inside` (or `calc1.substitution.linear-inside`) covers spotting it.
   card-format.md's example tags its decomposition step with `calc1.deriv.chain-rule`; this map
   separates the two (see the chain-rule split below).
5. **Applied problems end with an answer step:**
   - related rates use `calc1.related-rates.translate` (the signed rate with units);
   - optimization uses `calc1.optimize.answer`;
   - motion uses `calc1.motion.at-rest-direction` or `calc1.motion.speeding-up` (times or
     intervals, never a definition).

## Splits and why

**Status labels:**

- *cited* means an error study supports the split.
- *textbook* means OpenStax or CLP treats the variants as separate moves (their own subsection,
  strategy step, example or exercise group).
- *provisional* means: check with learning-curve data. A split should stay only if the two
  components' error curves separate once problems exist. If their misses always come together,
  merge them.

### Chapter 2

- **Limit techniques:** direct substitution; cancel a zero factor (factoring and complex
  fractions); conjugate; squeeze theorem; the special trig limits; K/0 sign analysis; one-sided
  limits of piecewise functions.
  - *Textbook:* OpenStax §2.3's strategy for 0/0 lists factoring, conjugates and complex
    fractions as separate moves, and the squeeze theorem and \(\sin\theta/\theta\) get their own
    subsection and example; CLP-1 §1.4, §2.8.
  - Factoring and complex fractions are one component (`calc1.limits.factor-cancel`) because the
    calculus move is the same (0/0 is not an answer; simplify, then substitute). The algebra
    difference lives in `alg.fraction.*`. *Provisional.*
- **0/0 vs K/0** (`calc1.limits.factor-cancel` vs `calc1.limits.infinite`), marked confusable.
  - *Textbook:* OpenStax §2.3 has a separate K/0 example.
  - Students treat both as "undefined", so the queue should interleave them.
- **Vertical asymptote vs removable discontinuity** (`calc1.asymptotes.vertical` vs
  `calc1.continuity.classify`), marked confusable.
  - *Textbook:* OpenStax §2.2 and §2.4.
  - A cancelling factor gives a hole, not an asymptote.
- **Limits from a table, from a graph, and from a formula.**
  - *Textbook:* OpenStax §2.2 has a strategy box for tables and separate graph exercise groups.
  - Different representations; *provisional*.
- **Continuity:** at a point, on intervals, classify, find a parameter, IVT.
  - *Textbook:* OpenStax §2.4 has a three-condition strategy box, plus separate subsections for
    discontinuity types, intervals and the IVT, and a "find k" exercise group.
  - Find a parameter is *provisional*.
- **ε–δ: find δ vs write the proof.**
  - *Textbook:* OpenStax §2.5 has separate exercise groups and a five-line proof strategy.
  - *Provisional.*

### Chapter 3

- **Power rule: integer powers vs negative or fractional powers**, plus a separate rewrite step
  (`alg.exponents.rewrite-as-power`).
  - *Textbook:* OpenStax §3.3 extends the power rule to negative exponents with its own learning
    objective and examples, and §3.7 does rational powers.
  - The owner's miss on \(e^{a/x}\) needed \(\frac{d}{dx}x^{-1}\), while \(e^{ax}\) did not.
  - Rewriting \(a/x\) as \(ax^{-1}\) is a separate step that fails on its own. *Provisional* for
    the rule split itself.
- **Chain rule, three components:** linear inside (`calc1.deriv.chain-linear-inside`),
  non-linear inside (`calc1.deriv.chain-rule`), and three or more layers
  (`calc1.deriv.chain-nested`).
  - *Textbook:* CLP-1 §2.9 states the \(f(ax + b)\) case as its own corollary (Corollary 2.9.9)
    and works the three cases as separate examples: Example 2.9.11 \((1 + 3x)^{75}\), 2.9.12
    \(\sin(x^2)\), 2.9.13 \(\sqrt[3]{\sin(x^2)}\). OpenStax §3.6 has a separate subsection and
    learning objective for composites of three or more functions.
  - *Cited:* Siyepu (2015) found 8 of 30 students failed \(\cot^3 x^4\) and 4 applied the
    product rule to \(\tan^3\sqrt{\cot 7x}\).
  - A typical miss pattern fits the same line: \(e^{ax}\) right, \(e^{a/x}\) wrong.
  - With a linear inside, the inner derivative is a constant. With a non-linear inside, it is an
    expression that needs another rule and is evaluated at the inside.
  - The linear vs non-linear split is *provisional*. No study found compares the two directly.
- **Decomposing a composite vs applying the chain rule** (`pre.functions.decompose`).
  - *Cited:* Jojo, Maharaj and Brijlall (2013): students with a weak understanding of composition
    still applied the chain rule well, so the two come apart. Siyepu (2015): composites were
    treated as products.
- **Derivative rules from tables or graphs vs from formulas** (`calc1.deriv.rules-at-point`,
  `calc1.deriv.chain-at-point`).
  - *Textbook:* OpenStax §3.3 and §3.6 have table exercise groups and the example "Using the Chain
    Rule with Functional Values".
  - Exams ask for the chain and quotient rules from a table.
  - The chain version is separate because its typical error (reading \(f'\) at \(a\) instead of
    at \(g(a)\)) does not exist for products. *Provisional.*
- **Trig derivatives: sine and cosine vs tan, cot, sec, csc.**
  - *Cited:* Siyepu (2015) found two students dropped the minus sign of
    \(\frac{d}{dx}\csc x\). The owner made the same miss (course doc, Test 2 1c).
  - *Provisional*, including whether cot and csc fail apart from tan and sec.
- **Tangent line at a point vs points with a given slope.**
  - *Textbook:* OpenStax §3.3 has the example "Determining Where a Function Has a Horizontal
    Tangent".
  - The reverse problem (solve \(f'(x) = m\)) is a different procedure. *Provisional.*
- **Motion: velocity and acceleration; at rest and direction; speeding up.**
  - *Textbook:* OpenStax §3.4.
  - Exams test each part separately, and a common miss answers parts b and c with
    definitions instead of solving. Speeding up is confusable with direction.
- **Exponential, logarithm, logarithmic differentiation.**
  - *Textbook:* OpenStax §3.9 has separate subsections, and log differentiation has its own
    strategy box.
  - Exams include a variable power.
  - \(a^x\) vs \(x^a\) is marked confusable.
- **Interpreting a derivative value with units** (3.4) **vs translating words into signs of
  \(f'\) and \(f''\)** (4.5).
  - A common miss is the sign meaning of \(V''\).
  - *Provisional.*
- **The nth-derivative pattern** and **recognizing a limit as a derivative.**
  - *Textbook:* OpenStax §3.5's pattern example and §3.2's exercise group.
  - *Provisional:* both are near the 10-problem floor.

### Chapter 4

- **Related rates, five setup steps and a chooser:**
  - translate the words into signed rates (`translate`);
  - write the relation (`relate`);
  - eliminate the quantity whose rate isn't given (`eliminate-variable`);
  - differentiate with respect to t (`differentiate-time`);
  - find the values at the instant, then substitute after differentiating (`values-at-instant`);
  - choose the relation type (`calc1.select.related-rates-relation`).

  Evidence:
  - *Textbook:* OpenStax §4.1's five-step strategy, which explicitly warns against substituting
    changing values before differentiating. The funnel example eliminates r with similar
    triangles.
  - *Cited:* Martin (2000): students did worst on the conceptual steps, translating prose into
    geometric and symbolic form, while overall success tracked the procedural steps.
  - A common miss uses the starting radius instead of the radius at the instant,
    which is `values-at-instant`.
  - Differentiating in t is kept apart from implicit differentiation in x and marked confusable.
    *Provisional.*
- **Linear approximation:**
  - choose f and a to approximate a number (`approximate-value`);
  - estimate a change with \(dy\) (`estimate-change`);
  - compute the actual change \(\Delta y\) (`actual-change`);
  - compute a relative or percentage error (`relative-error`).

  Evidence:
  - *Textbook:* OpenStax §4.2's three subsections and exercise groups.
  - Exams ask for the estimate, then the actual difference.
  - \(dy\) vs \(\Delta y\) is marked confusable.
  - The linearization formula itself is not a new component (see below).
- **Extrema:** read extrema from a graph; critical numbers; the closed-interval method.
  - *Textbook:* OpenStax §4.3's strategy box.
  - The absolute extremum on an open or unbounded interval is separate
    (`calc1.optimize.open-interval-absolute`, in 4.7), following OpenStax §4.7's own subsection.
- **Mean Value Theorem:** check the hypotheses; find c; use the conclusion.
  - *Textbook:* OpenStax §4.4 exercise groups.
  - The applications (rate reached, bounds, uniqueness of a root) are one component because they
    all use the same equation. *Provisional.*
  - The hypotheses check is confusable with the IVT.
- **Shape of a graph:**
  - increasing or decreasing;
  - the first derivative test;
  - concavity;
  - inflection points;
  - the second derivative test;
  - reading the graph of \(f'\);
  - translating words into signs.

  Evidence:
  - *Textbook:* OpenStax §4.5 subsections and its first-derivative-test strategy.
  - *Cited:* Baker, Cooley and Trigueros (2000): graphing from properties needs the properties
    coordinated over intervals, which is why `calc1.sketch.assemble` is its own component.
  - The sign chart itself is algebra (`alg.inequality.sign-chart`), so an error in finding signs
    doesn't count against the calculus.
  - Increasing or decreasing vs the first derivative test is *provisional*.
- **Limits at infinity:** polynomial or rational; radical (the sign flips at \(-\infty\) because
  \(\sqrt{x^2} = |x|\)); transcendental; and the oblique asymptote.
  - *Textbook:* OpenStax §4.6 subsections for polynomial, algebraic (with a radical example) and
    transcendental end behavior; CLP-1 §1.5.
- **Optimization, five setup steps and a chooser:**
  - write the objective (`objective`);
  - reduce it to one variable with the constraint (`one-variable`);
  - state the feasible domain (`domain`);
  - justify an absolute extremum on an open interval (`open-interval-absolute`);
  - report what was asked (`answer`);
  - choose the method (`calc1.select.optimization-method`).

  Evidence:
  - *Textbook:* OpenStax §4.7's six-step strategy.
  - *Cited:* Mkhatshwa's (2025) review found that building the objective function is the
    most-cited difficulty (Klymchuk et al. 2010; Swanagan 2012; Villegas et al. 2009; White and
    Mitchelmore 1996; LaRue and Infante 2015). Next come finding the extrema (Brijlall and Ndlovu
    2013) and justifying the extremum (Borgen and Manu 2002; Mkhatshwa 2019).
  - `answer` is *provisional*. It comes from the course doc's "answer the question asked" misses,
    and the wrong answer (the optimal x instead of the optimal value) shows clearly which step
    failed.
- **L'Hôpital's rule:**
  - identify the form;
  - apply the rule to a 0/0 or ∞/∞ quotient;
  - rewrite a 0·∞ product;
  - rewrite an ∞ − ∞ difference;
  - take the log of a 1^∞, 0⁰ or ∞⁰ power;
  - compare growth rates.

  Evidence:
  - *Textbook:* OpenStax §4.8 has a subsection per indeterminate type and the example "When
    L'Hôpital's Rule Does Not Apply"; CLP-1 §3.7.1 standard examples and §3.7.2 variations.
  - Forgetting to exponentiate back shows in the answer (it equals the log of the right one).
  - L'Hôpital vs the quotient rule is marked confusable.
  - Growth rates are *provisional*.
- **Newton's method: set up f(x) = 0 vs iterate.**
  - *Textbook:* OpenStax §4.9 exercise groups on writing the iteration, fixed points, and using
    \(f'\) to find extrema.
  - *Provisional.*
- **Antiderivatives:** power rule; trig; exponential and log; initial-value problems.
  - *Textbook:* OpenStax §4.10 table and initial-value subsection.
  - *Cited:* Voon, Julaihi and Tang (2017) list differentiation and integration confused for trig
    functions, and the log rule used where the power rule applies. Those pairs are marked
    confusable.

### Chapter 5

- **Sums and Riemann sums:** sigma notation; sum formulas; computing a Riemann sum; over- or
  underestimate.
  - *Textbook:* OpenStax §5.1.
  - Over- or underestimate is *provisional*.
- **The definite integral:**
  - translate a Riemann limit into an integral and back;
  - net signed area from geometry;
  - total area or distance;
  - properties;
  - average value.

  Evidence:
  - *Textbook:* OpenStax §5.2 subsections, which give net signed area and total area separately.
  - Net vs total area, and net change vs total distance, are marked confusable.
  - The average value of f vs the average rate of change, and vs the MVT's c, are marked
    confusable.
- **Fundamental Theorem:**
  - Part 1 with x as the upper limit (`part1`);
  - Part 1 with function limits (`part1-chain`);
  - Part 2 evaluation (`evaluate`);
  - reading an accumulation function from a graph (`accumulation-graph`).

  Evidence:
  - *Textbook:* OpenStax §5.3 has separate examples for the chain-rule and two-variable-limit
    cases.
  - Forgetting \(g'(x)\) mirrors the chain-rule omission. *Provisional.*
  - *Cited:* Thompson (1994) traces FTC difficulties to weak concepts of rate, which separates
    accumulation reasoning from the evaluation procedure.
- **Net change:** integrate a rate; interpret the integral with units; even and odd symmetry.
  - *Textbook:* OpenStax §5.4.
  - Interpreting an integral is confusable with interpreting a derivative.
- **Substitution:**
  - choose u (`choose-u`);
  - substitute and back-substitute (`indefinite`);
  - adjust a constant factor (`adjust-constant`);
  - write the leftover x in terms of u (`express-x-in-u`);
  - change the limits (`definite`);
  - divide by a for a linear inside (`linear-inside`);
  - choose a method (`calc1.select.integration-technique`).

  Evidence:
  - *Cited:* Voon, Julaihi and Tang (2017) report a 36.51% error rate on u-substitution without a
    hint vs 25.45% with one, so choosing u is its own hurdle. They also found substitution
    overlooked where it was the right method.
  - *Textbook:* OpenStax §5.5 has separate examples for "substitution with alteration" and for
    leftover x, and a subsection for definite integrals.
  - The linear-inside case mirrors the chain-rule split, and its classic error (multiplying by a)
    shows in the answer. It is *provisional*, marked confusable with
    `calc1.deriv.chain-linear-inside`.
- **The ln form \(g'/g\) and the inverse trig forms** are their own components.
  - *Cited:* Voon et al. (2017) report the log rule confused with the power rule.
  - \(\int \frac{dx}{1 + x^2}\), \(\int \frac{x\,dx}{1 + x^2}\) and
    \(\int \frac{x\,dx}{(1 + x^2)^2}\) are mutually confusable.

## Deliberately not split

- **Tangent line and linearization:** one procedure, so one component
  (`calc1.deriv.tangent-line`, 3.1). It also covers the amount-of-change estimate
  \(f(a + h) \approx f(a) + f'(a)h\) and normal lines.
- **Left, right and midpoint Riemann sums:** one procedure with a parameter.
- **The product rule and the quotient rule** are one component each. Their failures (order and
  sign in the numerator) are within one procedure, and the algebra afterwards is
  `alg.expand.products`.
- **Implicit differentiation** is one component, including second derivatives, which number
  under 10 a semester across OpenStax and CLP. Solving for \(dy/dx\) is `alg.solve.linear`, and
  implicit tangent lines use `calc1.deriv.tangent-line`.
- **Horizontal asymptotes** are the conclusion of a limit at infinity, so they are tagged with
  the limit component used.
- **eˣ and aˣ** share one derivative component; the \(\ln a\) factor is its typical error.
- **arcsin, arctan and arcsec integrals** share one component. Completing the square first is
  `alg.quadratics.complete-square`.
- **Repeated differentiation** (second derivatives, acceleration) uses the rule components.
  Only the nth-derivative pattern is separate.
- **Total distance from a position function** (turning points) is a note under
  `calc1.motion.at-rest-direction`. The integral version is `calc1.defint.total-area`.

## Method-choice components

One method-choice component per family of methods a student must pick between without a cue.
This follows the gaps research (`docs/research/notes/Toishi gaps research/error_diagnosis_tagging.md`,
section 3: one selection skill per family of confusable methods).

| Component | Deck | Chooses among |
|---|---|---|
| `calc1.select.limit-algebraic` | 2.3 | direct substitution, cancel the zero factor, conjugate, squeeze, special trig limits, K/0 sign analysis |
| `calc1.select.differentiation-rule` | 3.6 | power, negative or fractional power, product, quotient, chain (linear inside), chain, nested chain |
| `calc1.select.related-rates-relation` | 4.1 | area or volume formula, Pythagorean theorem, similar triangles, right-triangle trig ratio |
| `calc1.select.curve-analysis` | 4.6 | increasing or decreasing, concavity, first derivative test, second derivative test, inflection points |
| `calc1.select.optimization-method` | 4.7 | closed-interval method, one-critical-number argument, first or second derivative test |
| `calc1.select.limit-technique` | 4.8 | the 2.3 techniques, dominant terms at infinity, L'Hôpital's rule |
| `calc1.select.integration-technique` | 5.5 | power, trig, or exponential and log rule after rewriting; linear inside; substitution |

The limit family has two choosers. 2.3 students can then practise method choice months before
L'Hôpital's rule, and 4.8 adds the decision students get wrong once L'Hôpital is available: they
use it when substitution or algebra is enough. See the open questions.

## Setup components for applied problems

Each is a step whose result can be checked:

| Family | Components (checkable result) |
|---|---|
| Related rates | `translate` (signed given rates and the target), `relate` (an equation), `eliminate-variable` (a one-variable relation), `differentiate-time` (the rate equation), `values-at-instant` (numbers at the instant) |
| Optimization | `objective` (a formula), `one-variable` (a function of one variable), `domain` (an interval), `open-interval-absolute` (a justification, as a choice), `answer` (the quantity asked, with units) |
| Linear approximation | `approximate-value` (f and a, as an expression and a number), `estimate-change` (a number with units) |
| Motion | `at-rest-direction` (times and intervals), `speeding-up` (intervals) |
| Newton's method | `newton.setup` (the equation f(x) = 0) |
| Net change | `integrate-rate` (an amount), `interpret` (a meaning with units, as a choice) |
| Substitution | `choose-u` (the expression u) |

## Precalculus components (49)

They have no problems yet (as briefed), except the 0.6 Geometry components, whose cards are in
`packs/calc1/0-6-geometry.cards.md`. They exist so that steps can be tagged and a miss can be
routed to algebra instead of calculus.

- **0.1 Algebraic Expressions:**
  - `alg.arith.exact-evaluation`;
  - `alg.expand.products` (including signs and \((x + h)^n\));
  - `alg.factor.polynomials`;
  - `alg.factor.lowest-power` (negative or fractional exponents);
  - `alg.fraction.cancel-factors`, `.combine`, `.complex` and `.split-terms`;
  - `alg.polynomials.long-division`;
  - `alg.quadratics.complete-square`;
  - `alg.abs.piecewise`.
- **0.2 Equations and Inequalities:**
  - `alg.solve.linear` (including literal equations such as solving for dy/dx);
  - `alg.solve.polynomial`, `.quadratic-formula`, `.rational-equation` and `.radical-equation`;
  - `alg.inequality.sign-chart`;
  - `alg.abs.inequality`.
- **0.3 Functions and Graphs:**
  - `pre.functions.domain`, `.intercepts`, `.even-odd`, `.decompose`, `.evaluate-composite` and
    `.inverse-value`;
  - `alg.lines.point-slope`.
- **0.4 Trigonometry:**
  - `trig.values.exact`;
  - `trig.angles.radians`;
  - `trig.right-triangle.ratios`;
  - `trig.identities.reciprocal-quotient` and `.pythagorean` (Pythagorean and double-angle);
  - `trig.equations.solve`;
  - `trig.inverse.values`.
- **0.5 Exponents and Logarithms:**
  - `alg.exponents.rules` and `.rewrite-as-power`;
  - `alg.logs.properties` and `.solve-equations`.
- **0.6 Geometry** (13, listed in "The 0.6 Geometry block" below):
  - the original `pre.geometry.area-volume-formulas`, `.similar-triangles` and `.pythagorean`;
  - ten more, `.area-plane-figures`, `.perimeter-circumference`, `.volume-solids`,
    `.surface-area-solids`, `.arc-sector`, `.angle-relationships`, `.special-right-triangles`,
    `.distance-formula`, `.law-of-cosines` and `.composite-figures`.

The separate rewrite step (`alg.exponents.rewrite-as-power`) and the separate sign chart are the
two precalculus components the calculus splits above rely on most.

## The 0.6 Geometry block

The block grew from 3 components to 13 when its cards were written
(`packs/calc1/0-6-geometry.cards.md`; the card counts, sources and uncertainties are in
`docs/design/calc1-0-6-notes.md`). Students forget geometry definitions and formulas, and related
rates and optimization depend on them, so each fact that a solution step recalls had to be one
component of its own: a student who knows \(\pi r^2\) but not \(\frac{1}{3}\pi r^2 h\) fails
different steps. The original `pre.geometry.area-volume-formulas` bundled at least eight such
facts under one tag. The three original components keep their IDs and fields; ten were added.
Every `pre.geometry.` ID is below, with the prefix left off.

| Component | The one thing | Requires | Confusable with |
|---|---|---|---|
| `area-volume-formulas` (original) | umbrella for the formulas below; no 0.6 card tags it | | |
| `similar-triangles` (original) | set up a proportion between corresponding sides | | `pythagorean` |
| `pythagorean` (original) | the square of the hypotenuse is the sum of the squares of the legs | | `similar-triangles` |
| `area-plane-figures` | area of a triangle, parallelogram, trapezoid, circle or ellipse | | `perimeter-circumference` |
| `perimeter-circumference` | perimeter of a polygon, circumference of a circle | | `area-plane-figures` |
| `volume-solids` | volume of a box or prism, cylinder, cone, pyramid, sphere | `area-plane-figures` | `surface-area-solids` |
| `surface-area-solids` | surface area of a box, cylinder, cone, sphere | `area-plane-figures`, `perimeter-circumference` | `volume-solids` |
| `arc-sector` | arc length \(r\theta\) and sector area \(\frac{1}{2}r^2\theta\), with \(\theta\) in radians | `area-plane-figures`, `perimeter-circumference` | `perimeter-circumference` |
| `angle-relationships` | an unknown angle from complementary, supplementary, vertical, parallel-line and triangle-sum facts | | |
| `special-right-triangles` | the sides of a 45-45-90 or 30-60-90 triangle from one side | `pythagorean` | `pythagorean` |
| `distance-formula` | the distance between two points, and the equation of a circle | `pythagorean` | `pythagorean` |
| `law-of-cosines` | the third side from two sides and the angle between them | `pythagorean` | `pythagorean` |
| `composite-figures` | build an area, perimeter, volume or surface area from pieces: add, subtract, drop a shared edge | `volume-solids`, `surface-area-solids` | `perimeter-circumference` |

How the block is tagged:

- A step that recalls an area, perimeter, volume or surface-area formula carries the specific
  component. `area-volume-formulas` keeps its ID and its three dependents but is not tagged by
  any 0.6 card.
- Putting a figure together from pieces (including which edges count) is `composite-figures`; the
  formulas for the pieces are the other components.
- Finding a missing side with the Pythagorean theorem stays `pythagorean`. The 45-45-90 and
  30-60-90 ratios, the distance between two points and the law of cosines are separate
  components, because a student can know the theorem and still not recall them.
- The radian arc and sector formulas are separate from the circle's \(\pi r^2\) and \(2\pi r\):
  they fail separately, and the radian measure comes from `trig.angles.radians`.
- Status of the splits, in the map's terms: *textbook* for all ten (each has its own section in
  OpenStax Prealgebra 2e, Precalculus 2e or CLP-1 Appendix A), except `composite-figures`, which
  is *provisional*: if its misses always coincide with the misses on the pieces' formulas, merge it.

Follow-ups outside the 0.6 block (not made here):

1. Three skills still point at the umbrella, which has no cards:
   `calc1.optimize.objective` and `calc1.defint.geometry` (`requires`) and
   `calc1.select.related-rates-relation` (`chooses`). Retarget them, for example
   `calc1.optimize.objective` to `area-plane-figures`, `volume-solids` and
   `surface-area-solids`; `calc1.defint.geometry` to `area-plane-figures`; and the chooser to
   the specific volume and area components. Until then they inherit open question 1 below.
2. The original `pythagorean` name still says "or the distance formula", which
   `distance-formula` now owns. IDs are permanent but names are not, so the name can be trimmed.
3. `angle-relationships` has no genuine confusable, so the pool report lists it as missing one.
4. Not components yet: the midpoint formula, law of sines, and circle theorems (tangent and
   radius, angle in a semicircle). None is needed by the section 4.1 and 4.7 problems the block
   supports.

## Open questions

1. **Problem-less prerequisites block the queue today.** The queue introduces a skill only once
   every prerequisite is learned or placed (`core/queue/triage.py` `new_skill_ready`, LIB-3).
   Every calculus component reaches a precalculus component, and none of those has problems, so
   in today's engine nothing could be introduced.
   - Method-choice skills activate once two chosen methods are learned, so
     `calc1.select.related-rates-relation`, which chooses only precalculus components, could
     never activate either.
   - Diagnosis already treats a prerequisite with no pool as unverified (ENG-6).
   - Before this pack ships, decide one of these:
     - the queue does the same as diagnosis;
     - precalculus gets problems or placement items;
     - the precalculus edges move to `uses`.
2. **GRAPH-4 asks for a confusable skill on every skill** (`core/cards/graph.py` `pool_report`).
   I set `confusable` only where students really mix two up, 53 pairs, as briefed (60 now, with
   the 7 added in the 0.6 Geometry block). The pool report will list the rest until that target
   or the map changes.
3. **Two limit choosers or one?** If the data shows `limit-algebraic` and `limit-technique` move
   together, retire one. They can't be merged without retiring an ID.
4. **Provisional splits to check with learning-curve data:**
   - chain rule, linear vs non-linear inside;
   - power rule, integer vs negative and fractional powers;
   - tan and sec vs cot and csc;
   - rules from tables;
   - tangent with a given slope;
   - increasing or decreasing vs the first derivative test;
   - related rates, differentiating in t vs in x;
   - `optimize.answer`;
   - L'Hôpital growth rates;
   - Newton setup vs iterate;
   - MVT use;
   - FTC Part 1 with the chain rule;
   - substitution, linear inside and leftover x;
   - Riemann sums, over or under;
   - the nth-derivative pattern;
   - recognizing a limit as a derivative;
   - ε–δ, find δ vs write the proof.

   Each has a test: if the two components' misses always coincide, merge them. If one keeps
   failing while the other is learned, keep the split.
5. **`core`, `exam-tier` and `encompasses` are unset.** Exam tier defaults to 3, as briefed.
   Whether "core" should mark, say, the components on a typical final exam is the owner's call.
   With every component tagged on every problem, `encompasses` may no longer be needed.
6. **card-format.md's examples don't fully match this map:**
   - they use `calc1.mvt.statement` and `alg.simplify`, which this map doesn't define (the
     nearest are `calc1.mvt.hypotheses`, `alg.expand.products` and `alg.fraction.*`);
   - their decks use Stewart titles;
   - they tag a decomposition step with the chain rule.

   Update the examples, or keep them as generic illustrations.
7. **Deck titles use straight apostrophes** ("4.8 L'Hôpital's Rule", "4.9 Newton's Method")
   where OpenStax prints curly ones, so card authors can type them. Card decks must match
   exactly.
8. **Many classes use Stewart's numbering.** Check it against the edition:
   - Stewart 3.9 and 3.10 are OpenStax 4.1 and 4.2;
   - Stewart 4.1 to 4.4 are OpenStax 4.3, 4.4, 4.5 and 4.8;
   - Stewart 4.5 is the sketching part of OpenStax 4.6;
   - Stewart 4.7 to 4.9 are OpenStax 4.7, 4.9 and 4.10;
   - Stewart 2.6 is the limits part of OpenStax 4.6.
9. **Out of scope:** exponential growth and decay (OpenStax §6.8, CLP-1 §3.3), Taylor polynomials
   beyond the linear one (CLP-1 §3.4), and Chapter 6. A Calculus I course that includes them
   would need a few more components.
10. **The full KaTeX render check of a built pack needs `npm --prefix web ci`.** It isn't
    installed in this environment; the Notes math was checked separately (see the top).

## References

- OpenStax, *Calculus Volume 1*, Strang and Herman (CC BY-NC-SA 4.0).
  <https://openstax.org/details/books/calculus-volume-1>; source
  <https://github.com/openstax/osbooks-calculus-bundle>.
- Feldman, Rechnitzer and Yeager, *CLP-1 Differential Calculus* and *CLP-2 Integral Calculus*,
  UBC (CC BY-NC-SA 4.0). <https://github.com/arechnitzer/CLP1>,
  <https://github.com/arechnitzer/CLP2>.
- OpenStax, *College Algebra 2e* and *Precalculus 2e*.
  <https://github.com/openstax/osbooks-college-algebra-bundle>.
- Siyepu, S. W. (2015). Analysis of errors in derivatives of trigonometric functions.
  *International Journal of STEM Education* 2, 16. <https://doi.org/10.1186/s40594-015-0029-5>.
- Jojo, Z. M. M., Maharaj, A. and Brijlall, D. (2013). Schema development for the chain rule.
  *South African Journal of Higher Education* 27(3). <https://doi.org/10.20853/27-3-269>.
- Martin, T. (2000). Calculus students' ability to solve geometric related-rates problems.
  *Mathematics Education Research Journal* 12(2), 74–91. <https://doi.org/10.1007/BF03217077>.
- Mkhatshwa, T. (2025). Review of research on teaching optimization problems, *AURCO Journal*.
  <https://aurco.org/journals/AURCO_Journal_2025/Mkhatshwa_Teaching_Optimization_2025_PDF.pdf>
  (the source for the optimization studies cited above).
- Swanagan, B. (2012). The impact of students' understanding of derivatives on their
  performance while solving optimization problems. PhD thesis, University of Georgia.
  <https://openscholar.uga.edu/record/13859>.
- Baker, B., Cooley, L. and Trigueros, M. (2000). A calculus graphing schema. *Journal for
  Research in Mathematics Education* 31(5), 557–578.
- Thompson, P. W. (1994). Images of rate and operational understanding of the fundamental
  theorem of calculus. *Educational Studies in Mathematics* 26, 229–274.
  <https://doi.org/10.1007/BF01273664>.
- Voon, L. L., Julaihi, N. H. and Tang, H. E. (2017). Misconceptions and errors in learning
  integral calculus. *Asian Journal of University Education* 13(1).
  <https://files.eric.ed.gov/fulltext/EJ1207815.pdf>.
