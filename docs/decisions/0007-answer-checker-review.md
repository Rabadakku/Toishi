# ADR-0007: Answer checker review: holes, critical points, precision, forms

- Status: Accepted
- Amended by: ADR-0019 (holes are no longer marked wrong)
- Date: 2026-11-01

## Context

An independent review attacked the M3 checker (core/grader/) with 1514 cases written
before reading its golden suite (tests/grader/data/golden_review.toml, rows marked `FA`
or `FR`). The original checker accepted 74 of them wrongly. The causes were systematic:

1. **Sampling never left |x| <= 45** and treated each sample independently of the
   answer's structure, so `x + abs(x) - 45 + abs(abs(x) - 45)` (equal to x only for
   |x| <= 45), a difference inside `abs(x - 0.7) < 0.001`, `0*sqrt(1000 - x)` and, for
   integer n, `abs(n - 20) + n - 20` all passed as equal.
2. **Holes were accepted.** SymPy turns `x^2/x` into `x` in the exact step, and random
   points never land on x = 1 for `(x^2-1)/(x-1)`. docs/spec.md says "an answer undefined
   where the key is defined is wrong"; the old golden suite said the opposite.
3. **Absolute floors** in numeric closeness (1e-25 at 30 digits, 1e-50 at 60) made every
   tiny value equal: `e^(-1000)` graded correct for 0, `2e^(-200)` for `e^(-200)`, and
   `0.0` for `10^(-30)` (decimal slack). Interval endpoints were "exact" only to 1e-40.
4. **Form checks** could be gamed: `sqrt((x+1)^4)` passed `expanded`,
   `((x^2-4)^3)^(1/3)` passed `factored`, `0.3333` passed `lowest-terms` for 1/3,
   `2/sqrt(2)` passed `simplified` (SymPy had already simplified it). `require-constant`
   was syntactic: `x^2/2 + C - C` passed, `(x^2 + C)/2` failed.
5. **`endpoints: either` closed brackets before merging**, so `(-inf, 0) U (0, inf)`
   became the whole line and "where is 1/x decreasing?" accepted `(-inf, inf)`.
6. `0^0` evaluated to 1; a typed NUL character was read as a degree sign.

## Decision

- **Critical points** (core/grader/critical.py). The real zeros of every abs()/sign()
  argument, domain-restricting argument (sqrt, ln, log, even roots, fractional powers,
  arcsin-like at +-1) and divisor (including tan/sec/cot/csc) cut the line into regions
  where both expressions are analytic; the checker adds points in every region, just
  past every edge, far beyond the outermost ones, and at each exactly representable
  critical value. Zeros come from SymPy's solveset under a time limit (periodic families
  give their members for n = -3..3), else from a numeric scan. Arguments in several
  variables are cut along each variable with the others held at three sample points.
  If the analysis runs out of time, a match is **undecidable**, not correct.
- **Holes are wrong**, for expressions, antiderivatives and equations, as the spec says:
  `(x^2-1)/(x-1)` is not `x + 1`, `x/x` and `sec(x)^2 - tan(x)^2` are not `1`,
  `-arctan(1/x)` is not an antiderivative of 1/(1+x^2) on the reals, and `y/x^2 = 1`
  leaves (0, 0) out of `y = x^2`. A hole the key shares is fine (`sin(x)/cos(x)` for
  `tan(x)`, `x*y = 1` for `y = 1/x`); a card that means "for x != 1" says so in `domain`.
  The message names the point. Holes are found exactly: zeros of each divisor from
  solveset, the key's own divisors checked symbolically, the key checked continuous.
- **No absolute floors.** A mismatch is rechecked at 60, 120 and 240 digits: agreement
  to 1e-40 (relative) at any level settles it; otherwise the difference counts only if
  it is stable between two levels, because rounding noise shrinks as digits are added and
  a real difference does not. Constants use the same test. Decimal tolerance slack is
  relative. Interval endpoints are compared at 120 digits to 1e-100.
- **Tiny exact differences.** When symbolic confirmation can neither prove nor disprove
  a match, SymPy's difference (which cancels identical terms) is evaluated with strict
  `evalf` at sample points; a stable, nonzero value far below the sampled resolution
  (`x + exp(-1000x^2)` minus `x`) is a miss. A large value is ignored: it means SymPy
  reads a branch differently from our evaluator, and this step must never reject a match
  on that basis.
- **Forms.** factored/expanded/simplified/lowest-terms reject decimals that matched only
  within tolerance; lowest-terms takes no decimals and, for a rational value, only
  `p/q` as typed; expanded looks inside function calls and powers; factored checks every
  sum in the answer; simplified measures the answer as typed. `require-constant` asks
  that the answer change with C by an amount free of x.
- **`endpoints: either`** merges with the typed brackets, then opens the finite ends: a
  point inside the set is not an endpoint, so `[-1, 1) U (1, 3]` is not `[-1, 3]`.
- `0^0` is undefined (an indeterminate form). NUL is rejected before normalization.

## Known limits (accepted)

- **Equations use STACK's ratio test**: left minus right of the answer must be a nonzero
  constant times the key's, after clearing denominators. Equivalent equations that are
  not proportional are rejected: `sqrt(x) = 2` against `x = 4`, `(y - 2x - 1)^2 = 0`,
  `abs(y - 2x - 1) = 0`, `y^2 = x^2` style squarings. These are false rejects by
  design. The test does not accept a non-equivalent equation: proportional sides have
  the same zeros wherever both are defined; the answer must be defined wherever the
  key is at every sample and critical point; and clearing denominators is checked for
  points the answer leaves out of the key's solution set (polynomial divisors via
  `sympy.solve`; others, or a timeout, give undecidable).
- Holes of periodic divisors are found only for |n| <= 3 periods from the origin, and
  breakpoints of arguments in several variables only along each axis through three
  sample points. Differences below 1e-40 (relative) at every sample point are found only
  by the symbolic step, which the 2 s hard kill can cut short (the earlier, numeric
  verdict then stands).
- `tan(x)*cos(x)` for `sin(x)` and `arctan(x/sqrt(1-x^2))` for `arcsin(x)` without a
  domain are now incorrect (holes at pi/2 and +-1). Card authors who want them accepted
  add the domain.
