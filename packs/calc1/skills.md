---
format: mastery-skills 1
---

<!-- Calculus I component map (pack calc1). One skill = one component: a procedure, rule,
     fact or setup move a student can know or not know on its own. Every solution step names
     exactly one of these IDs. IDs are permanent: never rename or reuse one.
     Structure and section numbering follow OpenStax Calculus Volume 1 (CC BY-NC-SA 4.0);
     the map itself is original. Design notes: docs/design/calc1-component-map.md. -->

<!-- ==================== 0 Precalculus Skills ==================== -->

<!-- 0.1 Algebraic Expressions -->

## Skill alg.arith.exact-evaluation
name: Evaluate an expression exactly at a number
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
textbook: OpenStax College Algebra 2e §1.1

### Notes
Step: [alg.arith.exact-evaluation] Evaluate: \(f(-2) = (-2)^3 - 3(-2) = -8 + 6 = -2\).

## Skill alg.expand.products
name: Expand a product of polynomials and distribute signs, including (x + h)ⁿ
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
textbook: OpenStax College Algebra 2e §1.4

### Notes
Step: [alg.expand.products] Expand: \((x + h)^2 - x^2 = 2xh + h^2\); a minus sign in front of a bracket changes every sign inside it.

## Skill alg.factor.polynomials
name: Factor a polynomial (common factor, trinomial, difference of squares or cubes, grouping)
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
confusable: alg.solve.quadratic-formula
textbook: OpenStax College Algebra 2e §1.5; OpenStax Calculus Vol 1 §1.2

### Notes
Step: [alg.factor.polynomials] Factor: \(4x^3 - 4x = 4x(x - 1)(x + 1)\).

## Skill alg.factor.lowest-power
name: Factor out the lowest power of a common factor (negative or fractional exponents)
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.factor.polynomials, alg.exponents.rules
textbook: OpenStax College Algebra 2e §1.5

### Notes
Step: [alg.factor.lowest-power] Factor: \(x^{2/3} - 2x^{-1/3} = x^{-1/3}(x - 2)\).

## Skill alg.fraction.cancel-factors
name: Cancel a common factor of a rational expression (factors, never terms)
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.factor.polynomials
confusable: alg.fraction.split-terms
textbook: OpenStax College Algebra 2e §1.6

### Notes
Step: [alg.fraction.cancel-factors] Cancel: \(\frac{(x - 2)(x + 2)}{x - 2} = x + 2\) for \(x \neq 2\).

## Skill alg.fraction.combine
name: Combine rational expressions over a common denominator
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.factor.polynomials
textbook: OpenStax College Algebra 2e §1.6

### Notes
Step: [alg.fraction.combine] Combine: \(\frac{1}{x} - \frac{1}{2} = \frac{2 - x}{2x}\).

## Skill alg.fraction.complex
name: Simplify a complex fraction
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.fraction.combine
textbook: OpenStax College Algebra 2e §1.6; OpenStax Calculus Vol 1 §2.3

### Notes
Step: [alg.fraction.complex] Simplify: \(\frac{\frac{1}{x+h} - \frac{1}{x}}{h} = \frac{-h}{h\,x(x+h)} = \frac{-1}{x(x+h)}\).

## Skill alg.fraction.split-terms
name: Split a fraction with a one-term denominator into separate terms
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.exponents.rules
confusable: alg.fraction.cancel-factors
textbook: OpenStax College Algebra 2e §1.6; OpenStax Calculus Vol 1 §4.10

### Notes
Step: [alg.fraction.split-terms] Split: \(\frac{x^2 + 3}{x} = x + 3x^{-1}\).

## Skill alg.polynomials.long-division
name: Divide polynomials by long division
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.expand.products
textbook: OpenStax College Algebra 2e §5.4; OpenStax Calculus Vol 1 §4.6

### Notes
Step: [alg.polynomials.long-division] Divide: \(\frac{x^2 + 1}{x - 1} = x + 1 + \frac{2}{x - 1}\).

## Skill alg.quadratics.complete-square
name: Complete the square in a quadratic
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
requires: alg.expand.products
textbook: OpenStax College Algebra 2e §2.5; OpenStax Calculus Vol 1 §5.7

### Notes
Step: [alg.quadratics.complete-square] Complete the square: \(x^2 + 2x + 5 = (x + 1)^2 + 4\).

## Skill alg.abs.piecewise
name: Rewrite an absolute value as a piecewise expression by sign
deck: Calculus I::0 Precalculus Skills::0.1 Algebraic Expressions
textbook: OpenStax Calculus Vol 1 §1.1; OpenStax College Algebra 2e §3.6

### Notes
Step: [alg.abs.piecewise] Rewrite: \(|x - 3| = 3 - x\) for \(x < 3\) and \(x - 3\) for \(x \ge 3\).

<!-- 0.2 Equations and Inequalities -->

## Skill alg.solve.linear
name: Solve a linear or literal equation for one unknown (such as dy/dx)
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
textbook: OpenStax College Algebra 2e §2.2

### Notes
Step: [alg.solve.linear] Solve for \(y'\): \(y'(2y - x) = y - 2x\), so \(y' = \frac{y - 2x}{2y - x}\).

## Skill alg.solve.polynomial
name: Solve a polynomial equation by factoring (zero-product property)
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
requires: alg.factor.polynomials
textbook: OpenStax College Algebra 2e §2.5; OpenStax Calculus Vol 1 §1.2

### Notes
Step: [alg.solve.polynomial] Solve: \(4x(x - 1)(x + 1) = 0\) gives \(x = -1, 0, 1\).

## Skill alg.solve.quadratic-formula
name: Solve a quadratic equation with the quadratic formula
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
confusable: alg.factor.polynomials
textbook: OpenStax College Algebra 2e §2.5; OpenStax Calculus Vol 1 §1.2

### Notes
Step: [alg.solve.quadratic-formula] Quadratic formula: \(3x^2 - 6x + 1 = 0\) gives \(x = \frac{6 \pm \sqrt{24}}{6} = 1 \pm \frac{\sqrt{6}}{3}\).

## Skill alg.solve.rational-equation
name: Solve an equation with fractions (clear denominators, exclude their zeros)
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
requires: alg.fraction.combine, alg.solve.polynomial
textbook: OpenStax College Algebra 2e §2.2

### Notes
Step: [alg.solve.rational-equation] Solve \(1 - \frac{4}{x^2} = 0\): multiply by \(x^2\) (\(x \neq 0\)) to get \(x^2 = 4\), so \(x = \pm 2\).

## Skill alg.solve.radical-equation
name: Solve an equation with a square root (isolate, square, check for extraneous roots)
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
requires: alg.solve.polynomial
textbook: OpenStax College Algebra 2e §2.6

### Notes
Step: [alg.solve.radical-equation] Solve \(\frac{x}{\sqrt{x^2 + 9}} = \frac{1}{2}\): square to get \(4x^2 = x^2 + 9\), so \(x = \sqrt{3}\) (the negative root fails the sign check).

## Skill alg.inequality.sign-chart
name: Find where an expression is positive or negative with a sign chart
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
requires: alg.solve.polynomial
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6.2

### Notes
Step: [alg.inequality.sign-chart] Sign chart: \(3x(x - 2)\) is positive on \((-\infty, 0)\) and \((2, \infty)\) and negative on \((0, 2)\).

## Skill alg.abs.inequality
name: Rewrite an absolute-value inequality as a double inequality
deck: Calculus I::0 Precalculus Skills::0.2 Equations and Inequalities
requires: alg.abs.piecewise
textbook: OpenStax College Algebra 2e §2.7; OpenStax Calculus Vol 1 §2.5

### Notes
Step: [alg.abs.inequality] Rewrite: \(|x - 2| < \delta\) means \(2 - \delta < x < 2 + \delta\).

<!-- 0.3 Functions and Graphs -->

## Skill pre.functions.domain
name: Find the domain of a function (denominators, even roots, logarithms)
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
requires: alg.inequality.sign-chart
textbook: OpenStax Calculus Vol 1 §1.1; CLP-1 §0.4

### Notes
Step: [pre.functions.domain] Domain: \(\sqrt{x}\) needs \(x \ge 0\) and \(\frac{1}{x - 4}\) needs \(x \neq 4\), so \([0, 4) \cup (4, \infty)\).

## Skill pre.functions.intercepts
name: Find the x- and y-intercepts of a graph
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
requires: alg.solve.polynomial
textbook: OpenStax Calculus Vol 1 §1.1; CLP-1 §3.6.1

### Notes
Step: [pre.functions.intercepts] Intercepts: \(f(0) = 0\), and \(x^2(x - 3) = 0\) gives x-intercepts 0 and 3.

## Skill pre.functions.even-odd
name: Decide whether a function is even, odd or neither
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
textbook: OpenStax Calculus Vol 1 §1.1; CLP-1 §3.6.4

### Notes
Step: [pre.functions.even-odd] Symmetry: \(f(-x) = (-x)^3 \cos(-x) = -f(x)\), so f is odd.

## Skill pre.functions.decompose
name: Split a composite function into its outer and inner functions
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
textbook: OpenStax Calculus Vol 1 §1.1; CLP-1 §0.5

### Notes
Step: [pre.functions.decompose] Decompose: \(e^{a/x}\) is \(e^u\) with inner function \(u = a/x\).

## Skill pre.functions.evaluate-composite
name: Evaluate a composite function from formulas, a table or a graph
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
requires: alg.arith.exact-evaluation
textbook: OpenStax Calculus Vol 1 §1.1

### Notes
Step: [pre.functions.evaluate-composite] Look up: \(g(1) = 3\), then \(f'(g(1)) = f'(3) = -2\) from the table.

## Skill pre.functions.inverse-value
name: Find a value of an inverse function by solving f(x) = a
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
requires: alg.solve.linear
textbook: OpenStax Calculus Vol 1 §1.4; CLP-1 §0.6

### Notes
Step: [pre.functions.inverse-value] Inverse value: \(x^3 + x = 2\) at \(x = 1\), so \(f^{-1}(2) = 1\).

## Skill alg.lines.point-slope
name: Write the equation of a line from a point and a slope
deck: Calculus I::0 Precalculus Skills::0.3 Functions and Graphs
textbook: OpenStax Calculus Vol 1 §1.2

### Notes
Step: [alg.lines.point-slope] Line: slope 12 through \((2, 8)\) is \(y = 8 + 12(x - 2)\).

<!-- 0.4 Trigonometry -->

## Skill trig.values.exact
name: Find exact trig values at standard angles
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
confusable: trig.inverse.values
textbook: OpenStax Calculus Vol 1 §1.3; CLP-1 §A.6

### Notes
Step: [trig.values.exact] Exact value: \(\cos\frac{2\pi}{3} = -\frac{1}{2}\).

## Skill trig.angles.radians
name: Convert between degrees and radians
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
textbook: OpenStax Calculus Vol 1 §1.3; CLP-1 §A.4

### Notes
Step: [trig.angles.radians] Convert: \(2^\circ = \frac{2\pi}{180} = \frac{\pi}{90}\) rad, as calculus formulas need radians.

## Skill trig.right-triangle.ratios
name: Write a trig ratio from the sides of a right triangle
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
textbook: OpenStax Calculus Vol 1 §1.3; CLP-1 §A.3

### Notes
Step: [trig.right-triangle.ratios] Ratio: the angle of elevation satisfies \(\tan\theta = \frac{h}{500}\).

## Skill trig.identities.reciprocal-quotient
name: Rewrite with the reciprocal and quotient identities (tan = sin/cos, sec = 1/cos)
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
confusable: trig.identities.pythagorean
textbook: OpenStax Calculus Vol 1 §1.3; CLP-1 §A.7

### Notes
Step: [trig.identities.reciprocal-quotient] Rewrite: \(\frac{\tan x}{x} = \frac{\sin x}{x} \cdot \frac{1}{\cos x}\).

## Skill trig.identities.pythagorean
name: Rewrite with a Pythagorean or double-angle identity
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
requires: trig.identities.reciprocal-quotient
confusable: trig.identities.reciprocal-quotient
textbook: OpenStax Calculus Vol 1 §1.3; CLP-1 §A.7, §A.8

### Notes
Step: [trig.identities.pythagorean] Rewrite: \(\tan^2 x = \sec^2 x - 1\), or \(2\sin x \cos x = \sin 2x\).

## Skill trig.equations.solve
name: Solve a trig equation for every solution in an interval
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
requires: trig.values.exact
textbook: OpenStax Calculus Vol 1 §1.3; OpenStax Precalculus 2e §7.5

### Notes
Step: [trig.equations.solve] Solve \(\cos x = \sin x\) on \([0, 2\pi]\): \(x = \frac{\pi}{4}\) and \(x = \frac{5\pi}{4}\).

## Skill trig.inverse.values
name: Evaluate an inverse trig function exactly (principal range)
deck: Calculus I::0 Precalculus Skills::0.4 Trigonometry
requires: trig.values.exact
confusable: trig.values.exact
textbook: OpenStax Calculus Vol 1 §1.4; CLP-1 §A.9

### Notes
Step: [trig.inverse.values] Exact value: \(\arctan 1 - \arctan 0 = \frac{\pi}{4}\).

<!-- 0.5 Exponents and Logarithms -->

## Skill alg.exponents.rules
name: Simplify with the laws of exponents (products, quotients, powers, negative and zero exponents)
deck: Calculus I::0 Precalculus Skills::0.5 Exponents and Logarithms
confusable: alg.logs.properties
textbook: OpenStax College Algebra 2e §1.2; CLP-1 §A.12

### Notes
Step: [alg.exponents.rules] Simplify: \(\frac{x^{1/2} \cdot x^2}{x^{-1}} = x^{7/2}\).

## Skill alg.exponents.rewrite-as-power
name: Rewrite roots and reciprocals as powers, and back
deck: Calculus I::0 Precalculus Skills::0.5 Exponents and Logarithms
requires: alg.exponents.rules
textbook: OpenStax College Algebra 2e §1.3; CLP-1 §A.12

### Notes
Step: [alg.exponents.rewrite-as-power] Rewrite: \(\frac{3}{\sqrt{x}} = 3x^{-1/2}\) and \(\frac{a}{x} = ax^{-1}\).

## Skill alg.logs.properties
name: Expand or combine logarithms with the log laws (including ln eˣ = x)
deck: Calculus I::0 Precalculus Skills::0.5 Exponents and Logarithms
requires: alg.exponents.rules
confusable: alg.exponents.rules
textbook: OpenStax Calculus Vol 1 §1.5; CLP-1 §A.13

### Notes
Step: [alg.logs.properties] Expand: \(\ln\frac{x^2\sqrt{x + 1}}{x - 3} = 2\ln x + \frac{1}{2}\ln(x + 1) - \ln(x - 3)\).

## Skill alg.logs.solve-equations
name: Solve an exponential or logarithmic equation (take ln or exponentiate)
deck: Calculus I::0 Precalculus Skills::0.5 Exponents and Logarithms
requires: alg.logs.properties
textbook: OpenStax Calculus Vol 1 §1.5; OpenStax College Algebra 2e §6.6

### Notes
Step: [alg.logs.solve-equations] Solve \(e^{2x} = 5\): \(2x = \ln 5\), so \(x = \frac{\ln 5}{2}\).

<!-- 0.6 Geometry -->

## Skill pre.geometry.area-volume-formulas
name: Recall an area, volume or surface-area formula (circle, sphere, cone, cylinder, box)
deck: Calculus I::0 Precalculus Skills::0.6 Geometry
textbook: CLP-1 §A.10, §A.11

### Notes
Step: [pre.geometry.area-volume-formulas] Formula: a cone holds \(V = \frac{1}{3}\pi r^2 h\).

## Skill pre.geometry.similar-triangles
name: Relate lengths with similar triangles
deck: Calculus I::0 Precalculus Skills::0.6 Geometry
confusable: pre.geometry.pythagorean
textbook: CLP-1 §A.1

### Notes
Step: [pre.geometry.similar-triangles] Similar triangles: the water cone matches the tank, so \(\frac{r}{h} = \frac{5}{16}\).

## Skill pre.geometry.pythagorean
name: Relate lengths with the Pythagorean theorem or the distance formula
deck: Calculus I::0 Precalculus Skills::0.6 Geometry
confusable: pre.geometry.similar-triangles
textbook: CLP-1 §A.2

### Notes
Step: [pre.geometry.pythagorean] Pythagoras: the plane is \(s = \sqrt{x^2 + 4000^2}\) ft from the station.

<!-- ==================== 2 Limits ==================== -->

<!-- 2.1 A Preview of Calculus -->

## Skill calc1.rates.average-rate
name: Compute an average rate of change (secant slope or average velocity)
deck: Calculus I::2 Limits::2.1 A Preview of Calculus
requires: alg.arith.exact-evaluation
confusable: calc1.rates.estimate-instantaneous, calc1.deriv.definition, calc1.defint.average-value
textbook: OpenStax Calculus Vol 1 §2.1, §3.4; CLP-1 §1.1, §1.2

### Notes
Step: [calc1.rates.average-rate] Average velocity: \(\frac{s(3) - s(1)}{3 - 1} = \frac{40 - 16}{2} = 12\) m/s.

## Skill calc1.rates.estimate-instantaneous
name: Estimate an instantaneous rate from secant slopes or a table of values
deck: Calculus I::2 Limits::2.1 A Preview of Calculus
requires: calc1.rates.average-rate
confusable: calc1.rates.average-rate
textbook: OpenStax Calculus Vol 1 §2.1, §3.1; CLP-1 §1.2

### Notes
Step: [calc1.rates.estimate-instantaneous] Estimate: the secant slopes over \([1, 1.1]\), \([1, 1.01]\) and \([1, 1.001]\) are 2.1, 2.01 and 2.001, so the tangent slope at 1 is about 2.

<!-- 2.2 The Limit of a Function -->

## Skill calc1.limits.from-table
name: Estimate a limit from a table of values on both sides
deck: Calculus I::2 Limits::2.2 The Limit of a Function
requires: alg.arith.exact-evaluation
textbook: OpenStax Calculus Vol 1 §2.2; CLP-1 §1.3

### Notes
Step: [calc1.limits.from-table] Estimate: the values at 0.1, 0.01, 0.001 and at -0.1, -0.01, -0.001 all approach 0.5, so the limit is about 0.5.

## Skill calc1.limits.from-graph
name: Read one-sided and two-sided limits from a graph
deck: Calculus I::2 Limits::2.2 The Limit of a Function
textbook: OpenStax Calculus Vol 1 §2.2; CLP-1 §1.3

### Notes
Step: [calc1.limits.from-graph] Read: the graph approaches 2 from the left and 3 from the right, so \(\lim_{x \to 1} f(x)\) does not exist, whatever \(f(1)\) is.

## Skill calc1.asymptotes.vertical
name: Find vertical asymptotes (zeros of the denominator that do not cancel)
deck: Calculus I::2 Limits::2.2 The Limit of a Function
requires: calc1.limits.from-graph, alg.fraction.cancel-factors
confusable: calc1.continuity.classify
textbook: OpenStax Calculus Vol 1 §2.2, §4.6; CLP-1 §1.3, §3.6.1

### Notes
Step: [calc1.asymptotes.vertical] Asymptotes: \(\frac{x - 2}{(x - 2)(x + 1)}\) has a hole at \(x = 2\), where the factor cancels, and a vertical asymptote at \(x = -1\).

<!-- 2.3 The Limit Laws -->

## Skill calc1.limits.limit-laws
name: Combine known limits with the limit laws (sum, product, quotient, power)
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: alg.arith.exact-evaluation
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step: [calc1.limits.limit-laws] Limit laws: \(\lim_{x \to 6}\left(2f(x) - g(x)^2\right) = 2(4) - 3^2 = -1\).

## Skill calc1.limits.direct-substitution
name: Evaluate a limit by direct substitution where the function is continuous
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.limit-laws
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step: [calc1.limits.direct-substitution] Substitute: the function is continuous at 2, so \(\lim_{x \to 2}\frac{x^2 + 1}{x + 3} = \frac{5}{5} = 1\).

## Skill calc1.limits.factor-cancel
name: Evaluate a 0/0 limit by simplifying and cancelling the factor that is zero
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.direct-substitution, alg.fraction.cancel-factors
confusable: calc1.limits.conjugate, calc1.limits.infinite
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step 0: [calc1.limits.factor-cancel] Set up: substitution gives 0/0, which is not an answer; the limit never uses \(x = 2\) itself, so cancel the zero factor \(x - 2\) and substitute again.

## Skill calc1.limits.conjugate
name: Evaluate a 0/0 limit with a root difference by multiplying by the conjugate
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.factor-cancel, alg.expand.products
confusable: calc1.limits.factor-cancel
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step: [calc1.limits.conjugate] Conjugate: \(\frac{\sqrt{x + 4} - 2}{x}\cdot\frac{\sqrt{x + 4} + 2}{\sqrt{x + 4} + 2} = \frac{x}{x\left(\sqrt{x + 4} + 2\right)}\).

## Skill calc1.limits.piecewise
name: Find one-sided and two-sided limits of a piecewise function at a break point
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.direct-substitution, calc1.limits.from-graph, alg.abs.piecewise
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.3, §1.4

### Notes
Step: [calc1.limits.piecewise] One-sided: the left formula gives \(\lim_{x \to 1^-} f(x) = 1\) and the right formula gives 2; they differ, so the two-sided limit does not exist.

## Skill calc1.limits.infinite
name: Find an infinite one-sided limit of the form K/0 from the sign of the denominator
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.direct-substitution, alg.inequality.sign-chart
confusable: calc1.limits.factor-cancel
textbook: OpenStax Calculus Vol 1 §2.2, §2.3; CLP-1 §1.3

### Notes
Step: [calc1.limits.infinite] Sign: as \(x \to 3^+\) the top tends to 2 and \(x - 3\) is small and positive, so \(\frac{x - 1}{x - 3} \to +\infty\).

## Skill calc1.limits.squeeze
name: Evaluate a limit with the squeeze theorem (bound an oscillating factor)
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.direct-substitution
confusable: calc1.limits.special-trig
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step: [calc1.limits.squeeze] Squeeze: \(-x^2 \le x^2\sin\frac{1}{x} \le x^2\) and both bounds tend to 0, so the limit is 0.

## Skill calc1.limits.special-trig
name: Evaluate a trig limit with sin(θ)/θ → 1 and (1 − cos θ)/θ → 0, rescaling the argument
deck: Calculus I::2 Limits::2.3 The Limit Laws
requires: calc1.limits.direct-substitution, trig.identities.reciprocal-quotient
confusable: calc1.limits.squeeze
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §2.8

### Notes
Step: [calc1.limits.special-trig] Rescale: \(\frac{\sin 3x}{x} = 3\cdot\frac{\sin 3x}{3x} \to 3 \cdot 1 = 3\).

## Skill calc1.select.limit-algebraic
name: Choose a limit technique without L'Hôpital's rule (substitution, cancelling, conjugate, squeeze, a trig limit or a sign analysis)
deck: Calculus I::2 Limits::2.3 The Limit Laws
chooses: calc1.limits.direct-substitution, calc1.limits.factor-cancel, calc1.limits.conjugate, calc1.limits.squeeze, calc1.limits.special-trig, calc1.limits.infinite
textbook: OpenStax Calculus Vol 1 §2.3; CLP-1 §1.4

### Notes
Step 0: [calc1.select.limit-algebraic] Set up: substitution gives 0/0 and the top is \(\sqrt{x + 4} - 2\), so multiply by the conjugate.

<!-- 2.4 Continuity -->

## Skill calc1.continuity.at-a-point
name: Check continuity at a point (f(a) is defined, the limit exists, and the two are equal)
deck: Calculus I::2 Limits::2.4 Continuity
requires: calc1.limits.piecewise
textbook: OpenStax Calculus Vol 1 §2.4; CLP-1 §1.6

### Notes
Step: [calc1.continuity.at-a-point] Check: \(f(2) = 5\) but \(\lim_{x \to 2} f(x) = 4\), so f is not continuous at 2.

## Skill calc1.continuity.intervals
name: Find where a function is continuous (the domain of each formula, then the break points)
deck: Calculus I::2 Limits::2.4 Continuity
requires: calc1.continuity.at-a-point, pre.functions.domain
textbook: OpenStax Calculus Vol 1 §2.4; CLP-1 §1.6

### Notes
Step: [calc1.continuity.intervals] Continuity: \(\frac{\ln x}{x - 2}\) is continuous on its domain, \((0, 2) \cup (2, \infty)\).

## Skill calc1.continuity.classify
name: Classify a discontinuity as removable, jump or infinite
deck: Calculus I::2 Limits::2.4 Continuity
requires: calc1.continuity.at-a-point, calc1.limits.infinite
confusable: calc1.asymptotes.vertical
textbook: OpenStax Calculus Vol 1 §2.4; CLP-1 §1.6

### Notes
Step: [calc1.continuity.classify] Classify: both one-sided limits at 2 equal 4 but \(f(2)\) is undefined, so the discontinuity is removable.

## Skill calc1.continuity.make-continuous
name: Find the parameter value that makes a piecewise function continuous
deck: Calculus I::2 Limits::2.4 Continuity
requires: calc1.continuity.at-a-point, alg.solve.linear
textbook: OpenStax Calculus Vol 1 §2.4; CLP-1 §1.6

### Notes
Step: [calc1.continuity.make-continuous] Match the pieces at 1: \(k + 2 = 1^2 + 3\), so \(k = 2\).

## Skill calc1.continuity.ivt
name: Show that a root exists with the Intermediate Value Theorem (continuity and a sign change)
deck: Calculus I::2 Limits::2.4 Continuity
requires: calc1.continuity.intervals
confusable: calc1.mvt.hypotheses
textbook: OpenStax Calculus Vol 1 §2.4; CLP-1 §1.6

### Notes
Step: [calc1.continuity.ivt] IVT: f is continuous on \([1, 2]\), \(f(1) = -1 < 0\) and \(f(2) = 5 > 0\), so f has a root in \((1, 2)\).

<!-- 2.5 The Precise Definition of a Limit -->

## Skill calc1.epsilon-delta.find-delta
name: Find a δ that works for a given ε (from a linear formula or a graph)
deck: Calculus I::2 Limits::2.5 The Precise Definition of a Limit
requires: calc1.limits.from-graph, alg.abs.inequality
textbook: OpenStax Calculus Vol 1 §2.5; CLP-1 §1.7

### Notes
Step: [calc1.epsilon-delta.find-delta] Find delta: \(|(3x - 1) - 5| = 3|x - 2| < \varepsilon\) when \(|x - 2| < \frac{\varepsilon}{3}\), so \(\delta = \frac{\varepsilon}{3}\).

## Skill calc1.epsilon-delta.proof
name: Write an ε–δ proof that a limit holds
deck: Calculus I::2 Limits::2.5 The Precise Definition of a Limit
requires: calc1.epsilon-delta.find-delta
textbook: OpenStax Calculus Vol 1 §2.5; CLP-1 §1.7

### Notes
Step: [calc1.epsilon-delta.proof] Prove: let \(\varepsilon > 0\) and choose \(\delta = \frac{\varepsilon}{3}\); if \(0 < |x - 2| < \delta\) then \(|(3x - 1) - 5| = 3|x - 2| < \varepsilon\) (self-graded with a rubric).

<!-- ==================== 3 Derivatives ==================== -->

<!-- 3.1 Defining the Derivative -->

## Skill calc1.deriv.definition
name: Differentiate from the limit definition (difference quotient)
deck: Calculus I::3 Derivatives::3.1 Defining the Derivative
requires: calc1.limits.factor-cancel, alg.expand.products
confusable: calc1.rates.average-rate
textbook: OpenStax Calculus Vol 1 §3.1, §3.2; CLP-1 §2.2

### Notes
Step 0: [calc1.deriv.definition] Set up: \(f'(x) = \lim_{h \to 0}\frac{f(x + h) - f(x)}{h}\) with \(f(x + h) = (x + h)^2\); after the algebra, \(f'(x) = \lim_{h \to 0}(2x + h) = 2x\).

## Skill calc1.deriv.tangent-line
name: Write the tangent line (linearization) at a point: slope f′(a) through (a, f(a))
deck: Calculus I::3 Derivatives::3.1 Defining the Derivative
requires: calc1.deriv.definition, alg.lines.point-slope
confusable: calc1.deriv.tangent-given-slope
textbook: OpenStax Calculus Vol 1 §3.1, §4.2; CLP-1 §2.1, §3.4.2

### Notes
Step: [calc1.deriv.tangent-line] Tangent line: \(f'(2) = 12\) (a number, not \(f'(x)\)) and \(f(2) = 8\), so \(y = 8 + 12(x - 2)\); the same step estimates \(f(2.1) \approx 8 + 12(0.1)\). A normal line uses the slope \(-\frac{1}{12}\).

<!-- 3.2 The Derivative as a Function -->

## Skill calc1.deriv.recognize-limit
name: Recognize a limit as a derivative and name f and a
deck: Calculus I::3 Derivatives::3.2 The Derivative as a Function
requires: calc1.deriv.definition
textbook: OpenStax Calculus Vol 1 §3.2; CLP-1 §2.2

### Notes
Step: [calc1.deriv.recognize-limit] Recognize: \(\lim_{h \to 0}\frac{\sqrt{9 + h} - 3}{h}\) is \(f'(9)\) for \(f(x) = \sqrt{x}\), so it equals \(\frac{1}{6}\).

## Skill calc1.deriv.sketch-derivative
name: Sketch the graph of f′ from the graph of f
deck: Calculus I::3 Derivatives::3.2 The Derivative as a Function
requires: calc1.deriv.definition
confusable: calc1.shape.from-derivative-graph
textbook: OpenStax Calculus Vol 1 §3.2; CLP-1 §2.2

### Notes
Step: [calc1.deriv.sketch-derivative] Sketch: f has horizontal tangents at -1 and 2, so the graph of f' crosses zero there; f rises steeply near 3, so f' is large and positive there.

## Skill calc1.deriv.differentiability
name: Find where f is not differentiable (a corner, cusp, vertical tangent or discontinuity)
deck: Calculus I::3 Derivatives::3.2 The Derivative as a Function
requires: calc1.deriv.definition, calc1.continuity.at-a-point
textbook: OpenStax Calculus Vol 1 §3.2; CLP-1 §2.2

### Notes
Step: [calc1.deriv.differentiability] Check: \(|x - 1|\) has one-sided slopes -1 and 1 at \(x = 1\), a corner, so it is not differentiable there. Matching the values and the slopes of two pieces makes a piecewise function differentiable.

<!-- 3.3 Differentiation Rules -->

## Skill calc1.deriv.power-rule
name: Differentiate powers of x, sums and constant multiples (power rule)
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.definition
confusable: calc1.deriv.exponential, calc1.deriv.logarithmic-differentiation, calc1.antideriv.power-rule
textbook: OpenStax Calculus Vol 1 §3.3; CLP-1 §2.4, §2.6

### Notes
Step: [calc1.deriv.power-rule] Differentiate: \(\frac{d}{dx}\left(5x^4 - 3x^2 + 7\right) = 20x^3 - 6x\).

## Skill calc1.deriv.power-rule-rational
name: Differentiate a negative or fractional power of x
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.power-rule, alg.exponents.rewrite-as-power
textbook: OpenStax Calculus Vol 1 §3.3, §3.7; CLP-1 §2.6, §2.10

### Notes
Step: [calc1.deriv.power-rule-rational] Differentiate: \(\frac{d}{dx}4x^{-1/2} = -2x^{-3/2}\) and \(\frac{d}{dx}ax^{-1} = -ax^{-2}\).

## Skill calc1.deriv.product-rule
name: Differentiate a product (product rule)
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.power-rule
confusable: calc1.deriv.quotient-rule, calc1.deriv.chain-rule
textbook: OpenStax Calculus Vol 1 §3.3; CLP-1 §2.4

### Notes
Step: [calc1.deriv.product-rule] Product rule: \(\left(x^2\sin x\right)' = 2x\sin x + x^2\cos x\).

## Skill calc1.deriv.quotient-rule
name: Differentiate a quotient (quotient rule)
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.power-rule
confusable: calc1.deriv.product-rule, calc1.lhopital.quotient
textbook: OpenStax Calculus Vol 1 §3.3; CLP-1 §2.4

### Notes
Step: [calc1.deriv.quotient-rule] Quotient rule: \(\left(\frac{x}{x^2 + 1}\right)' = \frac{(1)(x^2 + 1) - x(2x)}{(x^2 + 1)^2} = \frac{1 - x^2}{(x^2 + 1)^2}\).

## Skill calc1.deriv.rules-at-point
name: Evaluate a product or quotient derivative from tables or graphs of f and g
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.product-rule, calc1.deriv.quotient-rule
confusable: calc1.deriv.chain-at-point
textbook: OpenStax Calculus Vol 1 §3.3; CLP-1 §2.4

### Notes
Step: [calc1.deriv.rules-at-point] From the table: \((fg)'(1) = f'(1)g(1) + f(1)g'(1) = (2)(3) + (5)(-1) = 1\).

## Skill calc1.deriv.tangent-given-slope
name: Find the points where the tangent line has a given slope (horizontal, or parallel to a line)
deck: Calculus I::3 Derivatives::3.3 Differentiation Rules
requires: calc1.deriv.power-rule, alg.solve.polynomial
confusable: calc1.deriv.tangent-line
textbook: OpenStax Calculus Vol 1 §3.3

### Notes
Step: [calc1.deriv.tangent-given-slope] Horizontal tangents: \(f'(x) = 3x^2 - 12 = 0\) at \(x = \pm 2\), so at the points \((2, -16)\) and \((-2, 16)\).

<!-- 3.4 Derivatives as Rates of Change -->

## Skill calc1.rates.interpret-derivative
name: Interpret a derivative value in context, with units
deck: Calculus I::3 Derivatives::3.4 Derivatives as Rates of Change
requires: calc1.deriv.definition
confusable: calc1.net-change.interpret
textbook: OpenStax Calculus Vol 1 §3.4; CLP-1 §2.3

### Notes
Step: [calc1.rates.interpret-derivative] Interpret: \(C'(100) = 12\) means the cost rises by about 12 dollars per extra unit at 100 units, so the 101st unit costs about 12 dollars.

## Skill calc1.motion.velocity-acceleration
name: Find velocity and acceleration from a position function
deck: Calculus I::3 Derivatives::3.4 Derivatives as Rates of Change
requires: calc1.deriv.power-rule
textbook: OpenStax Calculus Vol 1 §3.4; CLP-1 §3.1

### Notes
Step: [calc1.motion.velocity-acceleration] Differentiate: \(s(t) = t^3 - 6t^2 + 9t\) gives \(v(t) = 3t^2 - 12t + 9\) and \(a(t) = 6t - 12\).

## Skill calc1.motion.at-rest-direction
name: Find when a particle is at rest or moving in a given direction (solve v = 0, sign of v)
deck: Calculus I::3 Derivatives::3.4 Derivatives as Rates of Change
requires: calc1.motion.velocity-acceleration, alg.inequality.sign-chart
confusable: calc1.motion.speeding-up
textbook: OpenStax Calculus Vol 1 §3.4; CLP-1 §3.1

### Notes
Step: [calc1.motion.at-rest-direction] Solve: \(v(t) = 3(t - 1)(t - 3)\) is 0 at \(t = 1\) and \(t = 3\) (at rest) and negative for \(1 < t < 3\) (moving backward); answer with the times, not the definition.

## Skill calc1.motion.speeding-up
name: Decide when a particle speeds up or slows down (v and a with the same or opposite signs)
deck: Calculus I::3 Derivatives::3.4 Derivatives as Rates of Change
requires: calc1.motion.at-rest-direction
confusable: calc1.motion.at-rest-direction
textbook: OpenStax Calculus Vol 1 §3.4; CLP-1 §3.1

### Notes
Step: [calc1.motion.speeding-up] Compare signs: on \((2, 3)\), \(v < 0\) and \(a > 0\), so the particle slows down; on \((3, \infty)\) both are positive, so it speeds up.

<!-- 3.5 Derivatives of Trigonometric Functions -->

## Skill calc1.deriv.trig-sin-cos
name: Differentiate sine and cosine
deck: Calculus I::3 Derivatives::3.5 Derivatives of Trigonometric Functions
requires: calc1.deriv.power-rule
confusable: calc1.antideriv.trig
textbook: OpenStax Calculus Vol 1 §3.5; CLP-1 §2.8

### Notes
Step: [calc1.deriv.trig-sin-cos] Differentiate: \(\frac{d}{dx}(3\sin x - \cos x) = 3\cos x + \sin x\).

## Skill calc1.deriv.trig-other
name: Differentiate tan, cot, sec and csc
deck: Calculus I::3 Derivatives::3.5 Derivatives of Trigonometric Functions
requires: calc1.deriv.trig-sin-cos
textbook: OpenStax Calculus Vol 1 §3.5; CLP-1 §2.8

### Notes
Step: [calc1.deriv.trig-other] Differentiate: \(\frac{d}{dx}\csc x = -\csc x\cot x\) and \(\frac{d}{dx}\tan x = \sec^2 x\); the co-functions carry the minus sign.

## Skill calc1.deriv.nth-derivative
name: Find an nth derivative by spotting the pattern
deck: Calculus I::3 Derivatives::3.5 Derivatives of Trigonometric Functions
requires: calc1.deriv.trig-sin-cos
textbook: OpenStax Calculus Vol 1 §3.5; CLP-1 §2.14

### Notes
Step: [calc1.deriv.nth-derivative] Pattern: the derivatives of \(\sin x\) repeat every 4 steps and \(99 = 4 \cdot 24 + 3\), so \(\frac{d^{99}}{dx^{99}}\sin x = -\cos x\).

<!-- 3.6 The Chain Rule -->

## Skill calc1.deriv.chain-linear-inside
name: Differentiate f(ax + b): multiply the outer derivative by a (chain rule, linear inside)
deck: Calculus I::3 Derivatives::3.6 The Chain Rule
requires: calc1.deriv.power-rule
confusable: calc1.deriv.chain-rule, calc1.substitution.linear-inside
textbook: OpenStax Calculus Vol 1 §3.6; CLP-1 §2.9

### Notes
Step: [calc1.deriv.chain-linear-inside] Chain (linear inside): \(\frac{d}{dx}(2x + 1)^7 = 7(2x + 1)^6 \cdot 2\) and \(\frac{d}{dx}e^{5x} = 5e^{5x}\).

## Skill calc1.deriv.chain-rule
name: Differentiate a composite with a non-linear inside: f′(g(x))·g′(x) (chain rule)
deck: Calculus I::3 Derivatives::3.6 The Chain Rule
requires: calc1.deriv.chain-linear-inside, pre.functions.decompose
confusable: calc1.deriv.product-rule, calc1.deriv.chain-linear-inside, calc1.deriv.chain-nested
textbook: OpenStax Calculus Vol 1 §3.6; CLP-1 §2.9

### Notes
Step: [calc1.deriv.chain-rule] Chain: \(\frac{d}{dx}e^{a/x} = e^{a/x}\cdot\left(-\frac{a}{x^2}\right)\); the outer derivative stays evaluated at the inside, times the derivative of the inside.

## Skill calc1.deriv.chain-nested
name: Differentiate a composite of three or more functions (chain rule repeated from the outside in)
deck: Calculus I::3 Derivatives::3.6 The Chain Rule
requires: calc1.deriv.chain-rule
confusable: calc1.deriv.chain-rule
textbook: OpenStax Calculus Vol 1 §3.6; CLP-1 §2.9

### Notes
Step: [calc1.deriv.chain-nested] Chain twice: \(\frac{d}{dx}\sin^3(4x^2) = 3\sin^2(4x^2)\cdot\cos(4x^2)\cdot 8x\).

## Skill calc1.deriv.chain-at-point
name: Evaluate a chain-rule derivative from tables or graphs: f′(g(a))·g′(a)
deck: Calculus I::3 Derivatives::3.6 The Chain Rule
requires: calc1.deriv.chain-rule, pre.functions.evaluate-composite
confusable: calc1.deriv.rules-at-point
textbook: OpenStax Calculus Vol 1 §3.6; CLP-1 §2.9

### Notes
Step: [calc1.deriv.chain-at-point] From the table: \(h'(1) = f'(g(1))\,g'(1) = f'(3)\,g'(1) = (-2)(4) = -8\); f' is read at \(g(1) = 3\), not at 1.

## Skill calc1.select.differentiation-rule
name: Choose the differentiation rule from the outermost operation (power, product, quotient or chain)
deck: Calculus I::3 Derivatives::3.6 The Chain Rule
chooses: calc1.deriv.power-rule, calc1.deriv.power-rule-rational, calc1.deriv.product-rule, calc1.deriv.quotient-rule, calc1.deriv.chain-linear-inside, calc1.deriv.chain-rule, calc1.deriv.chain-nested
textbook: OpenStax Calculus Vol 1 §3.6; CLP-1 §2.9

### Notes
Step 0: [calc1.select.differentiation-rule] Set up: \(x^2e^{3x}\) is a product whose second factor is a composite, so the product rule goes outside and the chain rule inside; \(\frac{3}{x^2}\) is a power, not a quotient.

<!-- 3.7 Derivatives of Inverse Functions -->

## Skill calc1.deriv.inverse-function
name: Find the derivative of an inverse function at a point: (f⁻¹)′(a) = 1/f′(f⁻¹(a))
deck: Calculus I::3 Derivatives::3.7 Derivatives of Inverse Functions
requires: calc1.deriv.power-rule, pre.functions.inverse-value
textbook: OpenStax Calculus Vol 1 §3.7

### Notes
Step: [calc1.deriv.inverse-function] Inverse derivative: \(f(1) = 2\), so \(f^{-1}(2) = 1\) and \((f^{-1})'(2) = \frac{1}{f'(1)} = \frac{1}{4}\); the derivative of f is taken at \(f^{-1}(2)\), not at 2.

## Skill calc1.deriv.inverse-trig
name: Differentiate arcsin, arccos and arctan
deck: Calculus I::3 Derivatives::3.7 Derivatives of Inverse Functions
requires: calc1.deriv.power-rule
confusable: calc1.antideriv.inverse-trig
textbook: OpenStax Calculus Vol 1 §3.7; CLP-1 §2.12

### Notes
Step: [calc1.deriv.inverse-trig] Differentiate: \(\frac{d}{dx}\arctan x = \frac{1}{1 + x^2}\) and \(\frac{d}{dx}\arcsin x = \frac{1}{\sqrt{1 - x^2}}\).

<!-- 3.8 Implicit Differentiation -->

## Skill calc1.implicit.differentiate
name: Differentiate an equation implicitly (each y term gets a factor dy/dx)
deck: Calculus I::3 Derivatives::3.8 Implicit Differentiation
requires: calc1.deriv.chain-rule, alg.solve.linear
confusable: calc1.related-rates.differentiate-time
textbook: OpenStax Calculus Vol 1 §3.8; CLP-1 §2.11

### Notes
Step: [calc1.implicit.differentiate] Differentiate both sides: \(x^2 + y^3 = 7\) gives \(2x + 3y^2\frac{dy}{dx} = 0\); solving for \(\frac{dy}{dx}\) is the next step (alg.solve.linear). A second derivative repeats this and substitutes \(y'\).

<!-- 3.9 Derivatives of Exponential and Logarithmic Functions -->

## Skill calc1.deriv.exponential
name: Differentiate eˣ and aˣ (aˣ ln a)
deck: Calculus I::3 Derivatives::3.9 Derivatives of Exponential and Logarithmic Functions
requires: calc1.deriv.power-rule
confusable: calc1.deriv.power-rule, calc1.deriv.logarithmic-differentiation
textbook: OpenStax Calculus Vol 1 §3.9; CLP-1 §2.7

### Notes
Step: [calc1.deriv.exponential] Differentiate: \(\frac{d}{dx}2^x = 2^x\ln 2\) (not \(x\,2^{x - 1}\)) and \(\frac{d}{dx}e^x = e^x\).

## Skill calc1.deriv.logarithm
name: Differentiate ln x, ln|x| and logarithms to other bases
deck: Calculus I::3 Derivatives::3.9 Derivatives of Exponential and Logarithmic Functions
requires: calc1.deriv.power-rule
confusable: calc1.antideriv.exp-log
textbook: OpenStax Calculus Vol 1 §3.9; CLP-1 §2.10

### Notes
Step: [calc1.deriv.logarithm] Differentiate: \(\frac{d}{dx}\ln|x| = \frac{1}{x}\) and \(\frac{d}{dx}\log_2 x = \frac{1}{x\ln 2}\).

## Skill calc1.deriv.logarithmic-differentiation
name: Differentiate by taking logarithms first (a variable power, or a messy product or quotient)
deck: Calculus I::3 Derivatives::3.9 Derivatives of Exponential and Logarithmic Functions
requires: calc1.deriv.logarithm, calc1.implicit.differentiate, alg.logs.properties
confusable: calc1.deriv.power-rule, calc1.deriv.exponential
textbook: OpenStax Calculus Vol 1 §3.9; CLP-1 §2.10

### Notes
Step: [calc1.deriv.logarithmic-differentiation] Take logs: \(\ln y = \arctan(x)\,\ln(x^3 + 1)\); differentiate both sides, then multiply by \(y = (x^3 + 1)^{\arctan x}\).

<!-- ==================== 4 Applications of Derivatives ==================== -->

<!-- 4.1 Related Rates -->

## Skill calc1.related-rates.translate
name: Translate a related-rates problem into signed rates: the given rates, the wanted rate, the instant
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
requires: calc1.rates.interpret-derivative
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step: [calc1.related-rates.translate] Given and wanted: \(\frac{dV}{dt} = -3\) (draining, so negative); find \(\frac{dh}{dt}\) when \(h = 4\). The same component states the answer's sign and units at the end.

## Skill calc1.select.related-rates-relation
name: Choose the relation that links the changing quantities (a formula, Pythagoras, a trig ratio or similar triangles)
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
chooses: pre.geometry.area-volume-formulas, pre.geometry.pythagorean, pre.geometry.similar-triangles, trig.right-triangle.ratios
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step 0: [calc1.select.related-rates-relation] Set up: the quantities are two legs and the hypotenuse of a right triangle, so the relation is the Pythagorean theorem.

## Skill calc1.related-rates.relate
name: Write the equation that relates the changing quantities
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
requires: calc1.related-rates.translate
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step: [calc1.related-rates.relate] Relate: the ladder, the wall and the ground form a right triangle, so \(x^2 + y^2 = 13^2\) at every time t.

## Skill calc1.related-rates.eliminate-variable
name: Eliminate the quantity whose rate is not given before differentiating
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
requires: calc1.related-rates.relate, pre.geometry.similar-triangles
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step: [calc1.related-rates.eliminate-variable] Eliminate r: \(r = \frac{5h}{16}\), so \(V = \frac{1}{3}\pi\left(\frac{5h}{16}\right)^2 h = \frac{25\pi}{768}h^3\).

## Skill calc1.related-rates.differentiate-time
name: Differentiate the relation with respect to time (every changing quantity gets its rate)
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
requires: calc1.related-rates.relate, calc1.implicit.differentiate
confusable: calc1.implicit.differentiate
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step: [calc1.related-rates.differentiate-time] Differentiate in t: \(2x\frac{dx}{dt} + 2y\frac{dy}{dt} = 0\).

## Skill calc1.related-rates.values-at-instant
name: Find every quantity's value at the instant, then substitute after differentiating
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
requires: calc1.related-rates.differentiate-time
textbook: OpenStax Calculus Vol 1 §4.1; CLP-1 §3.2

### Notes
Step: [calc1.related-rates.values-at-instant] At the instant: \(x = 5\) gives \(y = 12\) from \(x^2 + y^2 = 169\); substitute both into the differentiated equation (never before differentiating) and solve for \(\frac{dy}{dt}\).

<!-- 4.2 Linear Approximations and Differentials -->

## Skill calc1.linearization.approximate-value
name: Approximate a number by choosing a function and a nearby base point (linear approximation)
deck: Calculus I::4 Applications of Derivatives::4.2 Linear Approximations and Differentials
requires: calc1.deriv.tangent-line
confusable: calc1.linearization.estimate-change
textbook: OpenStax Calculus Vol 1 §4.2; CLP-1 §3.4.2

### Notes
Step 0: [calc1.linearization.approximate-value] Set up: \(\sqrt{9.1}\) is \(f(x) = \sqrt{x}\) near \(a = 9\), so \(\sqrt{9.1} \approx f(9) + f'(9)(0.1) = 3 + \frac{0.1}{6}\).

## Skill calc1.linearization.estimate-change
name: Estimate a change with the differential dy = f′(x) dx
deck: Calculus I::4 Applications of Derivatives::4.2 Linear Approximations and Differentials
requires: calc1.linearization.approximate-value
confusable: calc1.linearization.approximate-value, calc1.linearization.actual-change
textbook: OpenStax Calculus Vol 1 §4.2; CLP-1 §3.4.6

### Notes
Step: [calc1.linearization.estimate-change] Differential: \(dV = 4\pi r^2\,dr = 4\pi(10)^2(0.1) = 40\pi\) cubic cm.

## Skill calc1.linearization.actual-change
name: Compute the actual change Δy = f(x + Δx) − f(x) and compare it with the differential
deck: Calculus I::4 Applications of Derivatives::4.2 Linear Approximations and Differentials
requires: calc1.linearization.estimate-change
confusable: calc1.linearization.estimate-change
textbook: OpenStax Calculus Vol 1 §4.2; CLP-1 §3.4.6

### Notes
Step: [calc1.linearization.actual-change] Actual change: \(\Delta V = \frac{4}{3}\pi\left(10.1^3 - 10^3\right) \approx 40.4\pi\), slightly more than \(dV = 40\pi\).

## Skill calc1.linearization.relative-error
name: Compute a relative or percentage error from a differential
deck: Calculus I::4 Applications of Derivatives::4.2 Linear Approximations and Differentials
requires: calc1.linearization.estimate-change
textbook: OpenStax Calculus Vol 1 §4.2; CLP-1 §3.4.6

### Notes
Step: [calc1.linearization.relative-error] Relative error: \(\frac{dV}{V} = 3\frac{dr}{r} = 3(0.01) = 0.03\), so about 3%.

<!-- 4.3 Maxima and Minima -->

## Skill calc1.extrema.from-graph
name: Identify absolute and local extrema on a graph
deck: Calculus I::4 Applications of Derivatives::4.3 Maxima and Minima
confusable: calc1.shape.from-derivative-graph
textbook: OpenStax Calculus Vol 1 §4.3; CLP-1 §3.5.1

### Notes
Step: [calc1.extrema.from-graph] Read: the highest point on \([-2, 3]\) is the endpoint \((3, 5)\), an absolute maximum; the hilltop at \((0, 2)\) is only a local maximum.

## Skill calc1.extrema.critical-numbers
name: Find critical numbers (f′ is zero or undefined, inside the domain)
deck: Calculus I::4 Applications of Derivatives::4.3 Maxima and Minima
requires: calc1.deriv.power-rule, pre.functions.domain
confusable: calc1.shape.inflection-points
textbook: OpenStax Calculus Vol 1 §4.3; CLP-1 §3.5.1

### Notes
Step: [calc1.extrema.critical-numbers] Critical numbers: \(f'(x) = \frac{2(x - 1)}{3x^{1/3}}\) is 0 at \(x = 1\) and undefined at \(x = 0\); both are in the domain of f.

## Skill calc1.extrema.closed-interval
name: Find absolute extrema on a closed interval (compare f at the critical numbers and the endpoints)
deck: Calculus I::4 Applications of Derivatives::4.3 Maxima and Minima
requires: calc1.extrema.critical-numbers
confusable: calc1.optimize.open-interval-absolute
textbook: OpenStax Calculus Vol 1 §4.3; CLP-1 §3.5.2

### Notes
Step: [calc1.extrema.closed-interval] Compare: \(f(-1) = 3\), \(f(0) = 1\), \(f(2) = 7\), so the absolute maximum is 7 at \(x = 2\) and the absolute minimum is 1 at \(x = 0\).

<!-- 4.4 The Mean Value Theorem -->

## Skill calc1.mvt.hypotheses
name: Check the hypotheses of Rolle's theorem or the Mean Value Theorem
deck: Calculus I::4 Applications of Derivatives::4.4 The Mean Value Theorem
requires: calc1.continuity.intervals, calc1.deriv.differentiability
confusable: calc1.continuity.ivt
textbook: OpenStax Calculus Vol 1 §4.4; CLP-1 §2.13

### Notes
Step: [calc1.mvt.hypotheses] Hypotheses: \(f(x) = x^{2/3}\) is continuous on \([-1, 1]\) but not differentiable at 0, so the MVT does not apply.

## Skill calc1.mvt.find-c
name: Find the numbers c that the Mean Value Theorem or Rolle's theorem guarantees
deck: Calculus I::4 Applications of Derivatives::4.4 The Mean Value Theorem
requires: calc1.mvt.hypotheses, calc1.rates.average-rate
confusable: calc1.defint.average-value
textbook: OpenStax Calculus Vol 1 §4.4; CLP-1 §2.13

### Notes
Step: [calc1.mvt.find-c] Solve \(f'(c) = \frac{f(2) - f(0)}{2 - 0} = 2\): \(3c^2 = 2\), so \(c = \sqrt{2/3}\), the root inside \((0, 2)\).

## Skill calc1.mvt.use-conclusion
name: Use f(b) − f(a) = f′(c)(b − a) to conclude something (a rate was reached, a bound, at most one root)
deck: Calculus I::4 Applications of Derivatives::4.4 The Mean Value Theorem
requires: calc1.mvt.hypotheses
textbook: OpenStax Calculus Vol 1 §4.4; CLP-1 §2.13

### Notes
Step: [calc1.mvt.use-conclusion] Conclude: 150 miles in 2 hours is an average of 75 mph, so by the MVT the speed was exactly 75 mph at some instant.

<!-- 4.5 Derivatives and the Shape of a Graph -->

## Skill calc1.shape.increasing-decreasing
name: Find where f increases or decreases from the sign of f′
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.extrema.critical-numbers
confusable: calc1.shape.concavity
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6.2

### Notes
Step: [calc1.shape.increasing-decreasing] Conclude: \(f' > 0\) on \((-\infty, 0)\) and \((2, \infty)\), so f increases there, and decreases on \((0, 2)\).

## Skill calc1.shape.first-derivative-test
name: Classify critical points by the sign change of f′ (first derivative test)
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.increasing-decreasing
confusable: calc1.shape.second-derivative-test
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6.2

### Notes
Step: [calc1.shape.first-derivative-test] Classify: f' changes from + to - at \(x = 0\), so \(f(0) = 0\) is a local maximum; no sign change means no extremum.

## Skill calc1.shape.concavity
name: Find where f is concave up or down from the sign of f″
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.increasing-decreasing
confusable: calc1.shape.increasing-decreasing
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6.3

### Notes
Step: [calc1.shape.concavity] Conclude: \(f''(x) = 6x - 6 > 0\) for \(x > 1\), so f is concave up on \((1, \infty)\) and concave down on \((-\infty, 1)\).

## Skill calc1.shape.inflection-points
name: Find inflection points (f″ changes sign where f is defined)
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.concavity
confusable: calc1.extrema.critical-numbers
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6.3

### Notes
Step: [calc1.shape.inflection-points] Inflection: f'' changes sign at \(x = 1\) and \(f(1) = -2\), so \((1, -2)\) is an inflection point; a zero of f'' without a sign change is not one.

## Skill calc1.shape.second-derivative-test
name: Classify a critical point by the sign of f″ there (second derivative test)
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.concavity
confusable: calc1.shape.first-derivative-test
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.5

### Notes
Step: [calc1.shape.second-derivative-test] Test: \(f'(2) = 0\) and \(f''(2) = 6 > 0\), so \(f(2)\) is a local minimum; \(f''(2) = 0\) would make the test inconclusive.

## Skill calc1.shape.from-derivative-graph
name: Read where f increases, has extrema or changes concavity from the graph of f′
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.first-derivative-test, calc1.shape.inflection-points
confusable: calc1.extrema.from-graph, calc1.deriv.sketch-derivative
textbook: OpenStax Calculus Vol 1 §4.5; CLP-1 §3.6

### Notes
Step: [calc1.shape.from-derivative-graph] Read the graph of f': it crosses from below to above the axis at \(x = 3\), so f has a local minimum there; f' peaks at \(x = 5\), so f has an inflection point there.

## Skill calc1.shape.interpret-derivative-signs
name: Translate statements about change into signs of f′ and f″ (and back)
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
requires: calc1.shape.concavity
textbook: OpenStax Calculus Vol 1 §4.5

### Notes
Step: [calc1.shape.interpret-derivative-signs] Translate: “the population grows, but more slowly” means \(P' > 0\) and \(P'' < 0\).

<!-- 4.6 Limits at Infinity and Asymptotes -->

## Skill calc1.infinity.polynomial-rational
name: Find a limit at infinity of a polynomial or rational function from its dominant terms
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
requires: calc1.limits.limit-laws, alg.fraction.split-terms
confusable: calc1.asymptotes.oblique
textbook: OpenStax Calculus Vol 1 §4.6; CLP-1 §1.5

### Notes
Step: [calc1.infinity.polynomial-rational] Divide by \(x^2\): \(\frac{3x^2 - x}{2x^2 + 5} = \frac{3 - 1/x}{2 + 5/x^2} \to \frac{3}{2}\), so \(y = \frac{3}{2}\) is a horizontal asymptote.

## Skill calc1.infinity.radical
name: Find a limit at infinity of an expression with a square root (√(x²) = |x|, so signs flip at −∞)
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
requires: calc1.infinity.polynomial-rational, alg.abs.piecewise, calc1.limits.conjugate
textbook: OpenStax Calculus Vol 1 §4.6; CLP-1 §1.5

### Notes
Step: [calc1.infinity.radical] For \(x < 0\), \(\sqrt{x^2} = -x\), so \(\frac{\sqrt{4x^2 + 1}}{x} \to -2\) as \(x \to -\infty\) but \(\to 2\) as \(x \to \infty\).

## Skill calc1.infinity.transcendental
name: Find a limit at infinity of an exponential, logarithmic or inverse trig expression
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
requires: calc1.infinity.polynomial-rational
confusable: calc1.lhopital.growth-rates
textbook: OpenStax Calculus Vol 1 §4.6; CLP-1 §1.5

### Notes
Step: [calc1.infinity.transcendental] End behavior: \(e^{-x} \to 0\) as \(x \to \infty\), so \(\frac{2 + e^{-x}}{1 + e^{-x}} \to 2\); and \(\arctan x \to \frac{\pi}{2}\).

## Skill calc1.asymptotes.oblique
name: Find an oblique asymptote by long division
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
requires: calc1.infinity.polynomial-rational, alg.polynomials.long-division
confusable: calc1.infinity.polynomial-rational
textbook: OpenStax Calculus Vol 1 §4.6

### Notes
Step: [calc1.asymptotes.oblique] Divide: \(\frac{x^2 + 1}{x - 1} = x + 1 + \frac{2}{x - 1}\), and the remainder term goes to 0, so \(y = x + 1\) is an oblique asymptote.

## Skill calc1.sketch.assemble
name: Assemble a sketch from the domain, intercepts, asymptotes and the sign charts of f′ and f″
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
requires: calc1.shape.first-derivative-test, calc1.shape.inflection-points, calc1.infinity.polynomial-rational, calc1.asymptotes.vertical, pre.functions.intercepts
textbook: OpenStax Calculus Vol 1 §4.6; CLP-1 §3.6.5

### Notes
Step: [calc1.sketch.assemble] Sketch: decreasing and concave up on \((0, 1)\), local minimum at \((1, 2)\), vertical asymptote \(x = 0\), approaching \(y = 0\) as \(x \to \infty\) (self-graded with a rubric).

## Skill calc1.select.curve-analysis
name: Choose the analysis that answers a graph question (sign of f′, sign of f″, or a derivative test)
deck: Calculus I::4 Applications of Derivatives::4.6 Limits at Infinity and Asymptotes
chooses: calc1.shape.increasing-decreasing, calc1.shape.concavity, calc1.shape.first-derivative-test, calc1.shape.second-derivative-test, calc1.shape.inflection-points
textbook: OpenStax Calculus Vol 1 §4.6; CLP-1 §3.6.5

### Notes
Step 0: [calc1.select.curve-analysis] Set up: “where is the graph concave down” is a question about the sign of f'', not of f'.

<!-- 4.7 Applied Optimization Problems -->

## Skill calc1.optimize.objective
name: Write the quantity to maximize or minimize in the problem's variables
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
requires: pre.geometry.area-volume-formulas
confusable: calc1.optimize.one-variable
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.3

### Notes
Step: [calc1.optimize.objective] Objective: the enclosed area to maximize is \(A = xy\).

## Skill calc1.optimize.one-variable
name: Use the constraint to write the objective in one variable
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
requires: calc1.optimize.objective, alg.solve.linear
confusable: calc1.optimize.objective
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.3

### Notes
Step: [calc1.optimize.one-variable] Constraint: \(2x + y = 100\) gives \(y = 100 - 2x\), so \(A(x) = x(100 - 2x)\).

## Skill calc1.optimize.domain
name: State the interval of feasible values for the one-variable objective
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
requires: calc1.optimize.one-variable
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.3

### Notes
Step: [calc1.optimize.domain] Domain: lengths are nonnegative and \(y = 100 - 2x \ge 0\), so \(0 \le x \le 50\).

## Skill calc1.optimize.open-interval-absolute
name: Justify an absolute extremum on an open or unbounded interval (one critical number, or end behavior)
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
requires: calc1.shape.first-derivative-test
confusable: calc1.extrema.closed-interval
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.2

### Notes
Step: [calc1.optimize.open-interval-absolute] Justify: \(S' < 0\) on \((0, 4)\) and \(S' > 0\) on \((4, \infty)\), so the only critical number \(x = 4\) gives the absolute minimum.

## Skill calc1.optimize.answer
name: Report what the question asks for: the optimal input, the dimensions or the extreme value, with units
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
requires: calc1.optimize.domain
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.3

### Notes
Step: [calc1.optimize.answer] Answer: the pen is 25 m by 50 m (the question asks for the dimensions, not the area 1250 square meters).

## Skill calc1.select.optimization-method
name: Choose how to locate and justify the optimum (closed-interval method, one-critical-number argument or a derivative test)
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
chooses: calc1.extrema.closed-interval, calc1.optimize.open-interval-absolute, calc1.shape.first-derivative-test, calc1.shape.second-derivative-test
textbook: OpenStax Calculus Vol 1 §4.7; CLP-1 §3.5.2

### Notes
Step 0: [calc1.select.optimization-method] Set up: the domain \((0, \infty)\) is open and unbounded, so justify the one critical number with the first derivative test instead of comparing endpoints.

<!-- 4.8 L'Hôpital's Rule -->

## Skill calc1.lhopital.identify-form
name: Identify the form of a limit by substitution (0/0, ∞/∞, 0·∞, ∞ − ∞, 1^∞, 0⁰, ∞⁰, or not indeterminate)
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.limits.direct-substitution
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7

### Notes
Step: [calc1.lhopital.identify-form] Form: substitution gives \(1^\infty\), which is indeterminate (it is not 1).

## Skill calc1.lhopital.quotient
name: Apply L'Hôpital's rule to a 0/0 or ∞/∞ quotient (differentiate top and bottom separately)
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.lhopital.identify-form, calc1.deriv.power-rule
confusable: calc1.deriv.quotient-rule
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7.1

### Notes
Step: [calc1.lhopital.quotient] L'Hôpital: \(\lim_{x \to 0}\frac{e^x - 1}{x} = \lim_{x \to 0}\frac{e^x}{1} = 1\).

## Skill calc1.lhopital.product-form
name: Rewrite a 0·∞ product as a quotient for L'Hôpital's rule
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.lhopital.quotient
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7.2

### Notes
Step: [calc1.lhopital.product-form] Rewrite: \(x\ln x = \frac{\ln x}{1/x}\), which is \(\frac{-\infty}{\infty}\) as \(x \to 0^+\).

## Skill calc1.lhopital.difference-form
name: Rewrite an ∞ − ∞ difference as one quotient
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.lhopital.quotient, alg.fraction.combine
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7.2

### Notes
Step: [calc1.lhopital.difference-form] Combine: \(\frac{1}{x} - \frac{1}{\sin x} = \frac{\sin x - x}{x\sin x}\), which is 0/0 at 0.

## Skill calc1.lhopital.power-form
name: Evaluate a 1^∞, 0⁰ or ∞⁰ limit by taking ln, then exponentiating back
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.lhopital.product-form, alg.logs.properties
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7.2

### Notes
Step: [calc1.lhopital.power-form] Exponentiate back: \(\ln y = x\ln\left(1 + \frac{2}{x}\right) \to 2\), so \(y \to e^2\).

## Skill calc1.lhopital.growth-rates
name: Compare growth rates (ln x ≪ xᵖ ≪ eˣ) to evaluate a limit at infinity
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
requires: calc1.lhopital.quotient
confusable: calc1.infinity.transcendental
textbook: OpenStax Calculus Vol 1 §4.8

### Notes
Step: [calc1.lhopital.growth-rates] Growth: \(e^x\) outgrows every power of x, so \(\frac{x^{50}}{e^x} \to 0\).

## Skill calc1.select.limit-technique
name: Choose a limit technique, L'Hôpital's rule included
deck: Calculus I::4 Applications of Derivatives::4.8 L'Hôpital's Rule
chooses: calc1.limits.direct-substitution, calc1.limits.factor-cancel, calc1.limits.conjugate, calc1.limits.squeeze, calc1.limits.special-trig, calc1.infinity.polynomial-rational, calc1.lhopital.quotient
textbook: OpenStax Calculus Vol 1 §4.8; CLP-1 §3.7

### Notes
Step 0: [calc1.select.limit-technique] Set up: substitution gives 0/0, there is nothing to factor or rationalize, and the top is a sine, so use L'Hôpital's rule or rewrite as \(3 \cdot \frac{\sin 3x}{3x}\).

<!-- 4.9 Newton's Method -->

## Skill calc1.newton.setup
name: Set up f(x) = 0 for Newton's method (a root, a radical, an intersection, or f′ = 0 for an extremum)
deck: Calculus I::4 Applications of Derivatives::4.9 Newton's Method
textbook: OpenStax Calculus Vol 1 §4.9; CLP-1 §C.1

### Notes
Step: [calc1.newton.setup] Set up: \(\sqrt[3]{5}\) is the positive root of \(f(x) = x^3 - 5\).

## Skill calc1.newton.iterate
name: Compute Newton's method iterates xₙ₊₁ = xₙ − f(xₙ)/f′(xₙ)
deck: Calculus I::4 Applications of Derivatives::4.9 Newton's Method
requires: calc1.newton.setup, calc1.deriv.power-rule
textbook: OpenStax Calculus Vol 1 §4.9; CLP-1 §C.1

### Notes
Step: [calc1.newton.iterate] Iterate: \(x_1 = 2 - \frac{f(2)}{f'(2)} = 2 - \frac{3}{12} = 1.75\). A zero of \(f'(x_n)\) or cycling iterates means the method fails.

<!-- 4.10 Antiderivatives -->

## Skill calc1.antideriv.power-rule
name: Antidifferentiate powers of x, sums and constant multiples (power rule for antiderivatives)
deck: Calculus I::4 Applications of Derivatives::4.10 Antiderivatives
requires: calc1.deriv.power-rule, alg.exponents.rewrite-as-power
confusable: calc1.antideriv.exp-log, calc1.deriv.power-rule, calc1.substitution.log-form
textbook: OpenStax Calculus Vol 1 §4.10; CLP-1 §4.1

### Notes
Step: [calc1.antideriv.power-rule] Antidifferentiate: \(\int \left(3x^2 + x^{-1/2}\right)dx = x^3 + 2x^{1/2} + C\).

## Skill calc1.antideriv.trig
name: Antidifferentiate sin, cos, sec², csc², sec·tan and csc·cot
deck: Calculus I::4 Applications of Derivatives::4.10 Antiderivatives
requires: calc1.deriv.trig-other
confusable: calc1.deriv.trig-sin-cos
textbook: OpenStax Calculus Vol 1 §4.10; CLP-1 §4.1

### Notes
Step: [calc1.antideriv.trig] Antidifferentiate: \(\int (\sin x + \sec^2 x)\,dx = -\cos x + \tan x + C\).

## Skill calc1.antideriv.exp-log
name: Antidifferentiate eˣ, aˣ and 1/x (ln|x|)
deck: Calculus I::4 Applications of Derivatives::4.10 Antiderivatives
requires: calc1.deriv.exponential, calc1.deriv.logarithm
confusable: calc1.antideriv.power-rule, calc1.deriv.logarithm
textbook: OpenStax Calculus Vol 1 §4.10, §5.6; CLP-1 §4.1

### Notes
Step: [calc1.antideriv.exp-log] Antidifferentiate: \(\int \left(e^x + \frac{2}{x}\right)dx = e^x + 2\ln|x| + C\).

## Skill calc1.antideriv.initial-value
name: Solve an initial-value problem: find C from a known value (twice when f″ is given)
deck: Calculus I::4 Applications of Derivatives::4.10 Antiderivatives
requires: calc1.antideriv.power-rule, alg.solve.linear
textbook: OpenStax Calculus Vol 1 §4.10; CLP-1 §4.1

### Notes
Step: [calc1.antideriv.initial-value] Find C: \(F(x) = x^3 + C\) and \(F(1) = 4\) give \(C = 3\). For motion, \(v(0)\) fixes the first constant and \(s(0)\) the second.

<!-- ==================== 5 Integration ==================== -->

<!-- 5.1 Approximating Areas -->

## Skill calc1.sums.sigma-notation
name: Write a sum in sigma notation, or expand one (index, bounds, terms)
deck: Calculus I::5 Integration::5.1 Approximating Areas
textbook: OpenStax Calculus Vol 1 §5.1; CLP-2 §1.1.2

### Notes
Step: [calc1.sums.sigma-notation] Write: \(1 + 4 + 9 + \cdots + 100 = \sum_{i=1}^{10} i^2\).

## Skill calc1.sums.formulas
name: Evaluate a sum with sum properties and the formulas for the sums of i, i² and i³
deck: Calculus I::5 Integration::5.1 Approximating Areas
requires: calc1.sums.sigma-notation, alg.expand.products
textbook: OpenStax Calculus Vol 1 §5.1; CLP-2 §1.1.2

### Notes
Step: [calc1.sums.formulas] Sum: \(\sum_{i=1}^{n}(2i + 1) = 2\cdot\frac{n(n + 1)}{2} + n = n^2 + 2n\).

## Skill calc1.riemann.endpoint-sum
name: Compute a left, right or midpoint Riemann sum (width, sample points, sum)
deck: Calculus I::5 Integration::5.1 Approximating Areas
requires: calc1.sums.sigma-notation, alg.arith.exact-evaluation
textbook: OpenStax Calculus Vol 1 §5.1; CLP-2 §1.1.3

### Notes
Step: [calc1.riemann.endpoint-sum] Right sum: \(\Delta x = 0.5\), so \(R_4 = 0.5\left[f(0.5) + f(1) + f(1.5) + f(2)\right]\).

## Skill calc1.riemann.over-under
name: Decide whether a Riemann sum overestimates or underestimates (monotone f; upper and lower sums)
deck: Calculus I::5 Integration::5.1 Approximating Areas
requires: calc1.riemann.endpoint-sum
textbook: OpenStax Calculus Vol 1 §5.1; CLP-2 §1.1

### Notes
Step: [calc1.riemann.over-under] Compare: f is increasing on \([0, 2]\), so the left sum underestimates and the right sum overestimates.

<!-- 5.2 The Definite Integral -->

## Skill calc1.defint.riemann-definition
name: Translate between a limit of Riemann sums and a definite integral (width, sample points, f, a, b)
deck: Calculus I::5 Integration::5.2 The Definite Integral
requires: calc1.riemann.endpoint-sum, calc1.sums.formulas
textbook: OpenStax Calculus Vol 1 §5.2; CLP-2 §1.1.3

### Notes
Step: [calc1.defint.riemann-definition] Recognize: \(\lim_{n \to \infty}\sum_{i=1}^{n}\left(1 + \frac{2i}{n}\right)^2\frac{2}{n} = \int_1^3 x^2\,dx\), with \(\Delta x = \frac{2}{n}\) and \(x_i = 1 + \frac{2i}{n}\).

## Skill calc1.defint.geometry
name: Evaluate a definite integral from areas of triangles, rectangles and circles (area below the axis counts as negative)
deck: Calculus I::5 Integration::5.2 The Definite Integral
requires: calc1.riemann.endpoint-sum, pre.geometry.area-volume-formulas
confusable: calc1.defint.total-area
textbook: OpenStax Calculus Vol 1 §5.2; CLP-2 §1.1.4

### Notes
Step: [calc1.defint.geometry] Net area: a triangle of area 4 above the axis and one of area 1 below it give \(\int_0^5 f(x)\,dx = 4 - 1 = 3\).

## Skill calc1.defint.total-area
name: Find a total area or total distance: split where the integrand changes sign and add absolute values
deck: Calculus I::5 Integration::5.2 The Definite Integral
requires: calc1.defint.geometry, alg.inequality.sign-chart
confusable: calc1.defint.geometry, calc1.net-change.integrate-rate
textbook: OpenStax Calculus Vol 1 §5.2, §5.4; CLP-2 §1.1.5

### Notes
Step: [calc1.defint.total-area] Split at \(t = 2\), where v changes sign: distance \(= -\int_0^2 v\,dt + \int_2^5 v\,dt\).

## Skill calc1.defint.properties
name: Use the properties of definite integrals (linearity, splitting the interval, reversed limits, comparison bounds)
deck: Calculus I::5 Integration::5.2 The Definite Integral
requires: calc1.defint.geometry
textbook: OpenStax Calculus Vol 1 §5.2; CLP-2 §1.2

### Notes
Step: [calc1.defint.properties] Split: \(\int_2^4 f\,dx = \int_0^4 f\,dx - \int_0^2 f\,dx = 5 - (-3) = 8\).

## Skill calc1.defint.average-value
name: Find the average value of f on [a, b], and where f takes it
deck: Calculus I::5 Integration::5.2 The Definite Integral
requires: calc1.defint.geometry
confusable: calc1.mvt.find-c, calc1.rates.average-rate
textbook: OpenStax Calculus Vol 1 §5.2, §5.3; CLP-2 §2.2

### Notes
Step: [calc1.defint.average-value] Average value: \(\frac{1}{3 - 0}\int_0^3 x^2\,dx = 3\); then \(c^2 = 3\) gives \(c = \sqrt{3}\) in \([0, 3]\).

<!-- 5.3 The Fundamental Theorem of Calculus -->

## Skill calc1.ftc.part1
name: Differentiate an integral whose upper limit is x (Fundamental Theorem, Part 1)
deck: Calculus I::5 Integration::5.3 The Fundamental Theorem of Calculus
requires: calc1.defint.properties
confusable: calc1.ftc.evaluate, calc1.ftc.part1-chain
textbook: OpenStax Calculus Vol 1 §5.3; CLP-2 §1.3

### Notes
Step: [calc1.ftc.part1] FTC 1: \(\frac{d}{dx}\int_1^x \sqrt{t^3 + 1}\,dt = \sqrt{x^3 + 1}\).

## Skill calc1.ftc.part1-chain
name: Differentiate an integral whose limits are functions of x (Part 1 with the chain rule)
deck: Calculus I::5 Integration::5.3 The Fundamental Theorem of Calculus
requires: calc1.ftc.part1, calc1.deriv.chain-rule
confusable: calc1.ftc.part1
textbook: OpenStax Calculus Vol 1 §5.3; CLP-2 §1.3

### Notes
Step: [calc1.ftc.part1-chain] FTC 1 with the chain rule: \(\frac{d}{dx}\int_0^{x^2}\cos t\,dt = \cos(x^2)\cdot 2x\); a lower limit \(g(x)\) contributes \(-f(g(x))\,g'(x)\).

## Skill calc1.ftc.evaluate
name: Evaluate a definite integral with an antiderivative, F(b) − F(a) (Fundamental Theorem, Part 2)
deck: Calculus I::5 Integration::5.3 The Fundamental Theorem of Calculus
requires: calc1.antideriv.power-rule, calc1.defint.geometry
confusable: calc1.ftc.part1
textbook: OpenStax Calculus Vol 1 §5.3; CLP-2 §1.3

### Notes
Step: [calc1.ftc.evaluate] Evaluate: \(\left[\frac{x^3}{3}\right]_1^2 = \frac{8}{3} - \frac{1}{3} = \frac{7}{3}\).

## Skill calc1.ftc.accumulation-graph
name: Analyze an accumulation function g(x) = ∫ f(t) dt from a to x, given the graph of f
deck: Calculus I::5 Integration::5.3 The Fundamental Theorem of Calculus
requires: calc1.ftc.part1, calc1.shape.first-derivative-test
textbook: OpenStax Calculus Vol 1 §5.3; CLP-2 §1.3

### Notes
Step: [calc1.ftc.accumulation-graph] Read: \(g' = f\) changes from + to - at \(x = 3\), so g has a local maximum there, and \(g(3)\) is the net area under f from a to 3.

<!-- 5.4 Integration Formulas and the Net Change Theorem -->

## Skill calc1.net-change.integrate-rate
name: Find a net change or a new amount by integrating a rate: Q(b) = Q(a) + ∫ Q′(t) dt from a to b
deck: Calculus I::5 Integration::5.4 Integration Formulas and the Net Change Theorem
requires: calc1.ftc.evaluate
confusable: calc1.defint.total-area
textbook: OpenStax Calculus Vol 1 §5.4; CLP-2 §1.1.5, §1.3

### Notes
Step: [calc1.net-change.integrate-rate] Net change: \(V(5) = V(0) + \int_0^5 r(t)\,dt = 200 + 75 = 275\) liters.

## Skill calc1.net-change.interpret
name: Interpret a definite integral of a rate in context, with units
deck: Calculus I::5 Integration::5.4 Integration Formulas and the Net Change Theorem
requires: calc1.net-change.integrate-rate
confusable: calc1.rates.interpret-derivative
textbook: OpenStax Calculus Vol 1 §5.4; CLP-2 §1.1.5

### Notes
Step: [calc1.net-change.interpret] Interpret: \(\int_0^{10} r(t)\,dt\) is the number of gallons used in the first 10 minutes (r in gallons per minute).

## Skill calc1.defint.even-odd
name: Use symmetry to integrate an even or odd function over [−a, a]
deck: Calculus I::5 Integration::5.4 Integration Formulas and the Net Change Theorem
requires: calc1.defint.properties, pre.functions.even-odd
textbook: OpenStax Calculus Vol 1 §5.4; CLP-2 §1.2.1

### Notes
Step: [calc1.defint.even-odd] Symmetry: \(x^3\cos x\) is odd, so \(\int_{-2}^{2} x^3\cos x\,dx = 0\).

<!-- 5.5 Substitution -->

## Skill calc1.substitution.choose-u
name: Choose u = g(x) so that g′(x) dx appears in the integrand, up to a constant
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.deriv.chain-rule
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step 0: [calc1.substitution.choose-u] Set up: the inner function \(x^2 + 1\) has derivative \(2x\), which appears, so let \(u = x^2 + 1\).

## Skill calc1.substitution.indefinite
name: Rewrite the integral in u with du, integrate, and substitute back
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.substitution.choose-u, calc1.antideriv.power-rule
confusable: calc1.substitution.definite
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step: [calc1.substitution.indefinite] Substitute: \(\int 2x(x^2 + 1)^5\,dx = \int u^5\,du = \frac{u^6}{6} + C = \frac{(x^2 + 1)^6}{6} + C\).

## Skill calc1.substitution.adjust-constant
name: Adjust for a missing constant factor in du (multiply by 1/k)
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.substitution.indefinite
confusable: calc1.substitution.linear-inside
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step: [calc1.substitution.adjust-constant] Adjust: \(du = 3x^2\,dx\), so \(x^2\,dx = \frac{1}{3}\,du\).

## Skill calc1.substitution.express-x-in-u
name: Write the leftover x in terms of u after substituting
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.substitution.indefinite, alg.solve.linear
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step: [calc1.substitution.express-x-in-u] Leftover x: with \(u = x - 1\), \(x = u + 1\), so \(\int x\sqrt{x - 1}\,dx = \int (u + 1)u^{1/2}\,du\).

## Skill calc1.substitution.definite
name: Change the limits of integration when substituting in a definite integral
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.substitution.indefinite, calc1.ftc.evaluate
confusable: calc1.substitution.indefinite
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step: [calc1.substitution.definite] New limits: \(x = 0\) gives \(u = 1\) and \(x = 2\) gives \(u = 5\), so the integral becomes \(\int_1^5 \frac{1}{2}u^{1/2}\,du\).

## Skill calc1.substitution.linear-inside
name: Antidifferentiate f(ax + b) by dividing by a
deck: Calculus I::5 Integration::5.5 Substitution
requires: calc1.antideriv.power-rule, calc1.antideriv.trig, calc1.antideriv.exp-log
confusable: calc1.substitution.adjust-constant, calc1.deriv.chain-linear-inside
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step: [calc1.substitution.linear-inside] Linear inside: \(\int e^{3x}\,dx = \frac{1}{3}e^{3x} + C\) (divide by 3, never multiply).

## Skill calc1.select.integration-technique
name: Choose an integration method: a basic rule (after rewriting) or substitution
deck: Calculus I::5 Integration::5.5 Substitution
chooses: calc1.antideriv.power-rule, calc1.antideriv.trig, calc1.antideriv.exp-log, calc1.substitution.linear-inside, calc1.substitution.indefinite
textbook: OpenStax Calculus Vol 1 §5.5; CLP-2 §1.4

### Notes
Step 0: [calc1.select.integration-technique] Set up: \(\int \frac{x^2 + 1}{x}\,dx\) needs no substitution; split the fraction and use the power and log rules.

<!-- 5.6 Integrals Involving Exponential and Logarithmic Functions -->

## Skill calc1.substitution.log-form
name: Integrate g′(x)/g(x) as ln|g(x)|
deck: Calculus I::5 Integration::5.6 Integrals Involving Exponential and Logarithmic Functions
requires: calc1.substitution.adjust-constant, calc1.antideriv.exp-log
confusable: calc1.antideriv.power-rule, calc1.antideriv.inverse-trig
textbook: OpenStax Calculus Vol 1 §5.6; CLP-2 §1.4

### Notes
Step: [calc1.substitution.log-form] Log form: \(\int \frac{x}{x^2 + 1}\,dx = \frac{1}{2}\ln(x^2 + 1) + C\).

<!-- 5.7 Integrals Resulting in Inverse Trigonometric Functions -->

## Skill calc1.antideriv.inverse-trig
name: Antidifferentiate 1/√(a² − x²) and 1/(a² + x²) as arcsin and arctan forms
deck: Calculus I::5 Integration::5.7 Integrals Resulting in Inverse Trigonometric Functions
requires: calc1.substitution.adjust-constant, calc1.deriv.inverse-trig
confusable: calc1.substitution.log-form, calc1.deriv.inverse-trig
textbook: OpenStax Calculus Vol 1 §5.7; CLP-2 §1.3

### Notes
Step: [calc1.antideriv.inverse-trig] Inverse tangent form: \(\int \frac{dx}{4 + x^2} = \frac{1}{2}\arctan\frac{x}{2} + C\).
