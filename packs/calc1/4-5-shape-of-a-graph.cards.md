---
format: mastery-cards 1
deck: Calculus I::4 Applications of Derivatives::4.5 Derivatives and the Shape of a Graph
source: original
license: CC BY-NC-SA 4.0
---

<!-- Section 4.5 Derivatives and the Shape of a Graph: seven skills, one worked example each, twelve problems each.
     Conventions: f is increasing on an interval when f' > 0 there, except possibly at isolated points;
     a critical number is an interior point of the domain where f' is zero or undefined;
     a local extremum is an interior point; an inflection point needs f defined there and f'' to change sign;
     the second derivative test says nothing when f'' = 0 at the critical number.
     Provenance: adapted cards name their source; every other card is original. -->


<!-- ===================================================================== -->
<!-- calc1.shape.increasing-decreasing                                     -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.incdec-example.001
kind: example
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart

### Question
On what intervals is \(f(x) = 2x^3 - 9x^2 + 12x + 1\) increasing, and on what intervals is it decreasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive and decreases where its derivative is negative. Find the derivative, mark the numbers where it is zero or undefined, and test its sign on each piece between them.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 6x^2 - 18x + 12\).
   check: diff(2*x^3 - 9*x^2 + 12*x + 1, x) = 6*x^2 - 18*x + 12
2. [alg.factor.polynomials] Factor: \(f'(x) = 6(x - 1)(x - 2)\).
   check: expand(6*(x - 1)*(x - 2)) = 6*x^2 - 18*x + 12
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = 1\) or \(x = 2\).
   check: solve(6*(x - 1)*(x - 2), x) = {1, 2}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = 1\) and \(x = 2\). They cut the number line into three pieces.
   check: {1, 2} = {1, 2}
5. [alg.inequality.sign-chart] Sign chart: test one point in each piece, \(f'(0) = 12\), \(f'\left(\frac{3}{2}\right) = -\frac{3}{2}\) and \(f'(3) = 12\). So \(f'\) is positive, negative, positive.
   check: subs(6*(x - 1)*(x - 2), x, 0) = 12
   check: subs(6*(x - 1)*(x - 2), x, 3/2) = -3/2
   check: subs(6*(x - 1)*(x - 2), x, 3) = 12
6. [calc1.shape.increasing-decreasing] Conclude: \(f\) is increasing on \((-\infty, 1)\) and on \((2, \infty)\), and decreasing on \((1, 2)\).
   check: solve(6*x^2 - 18*x + 12 < 0, x) = solve((x - 1)*(x - 2) < 0, x)
   check: solve(6*x^2 - 18*x + 12 > 0, x) = solve((x - 1)*(x - 2) > 0, x)

<!-- tier 1, template: f' is given in factored form -->
## Card calc1.4-5.incdec-factored.t01
skill: calc1.shape.increasing-decreasing
uses: alg.inequality.sign-chart
difficulty: 1
answer-type: interval
endpoints: either
vars: p = int(1, 5); q = int(1, 5); x
let: g = (x + p)*(x - q)
answer: solve(g > 0, x)
wrong: solve(g < 0, x) => That is where \(f'\) is negative, so \(f\) is decreasing there. @2

### Question
A function \(f\) is defined for all real numbers and \(f'(x) = (x + [[p]])(x - [[q]])\). On what intervals is \(f\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive, so find where the given derivative is positive.
1. [alg.inequality.sign-chart] Sign chart: \(f'\) is zero at \(x = -[[p]]\) and \(x = [[q]]\). Test one point in each piece: \(f'([[-p - 1]]) = [[p + q + 1]]\), \(f'(0) = [[-p*q]]\) and \(f'([[q + 1]]) = [[p + q + 1]]\). So \(f'\) is positive, negative, positive.
   check: subs(g, x, -p - 1) = p + q + 1
   check: subs(g, x, 0) = -p*q
   check: subs(g, x, q + 1) = p + q + 1
2. [calc1.shape.increasing-decreasing] Conclude: \(f' > 0\) on the two outer pieces, so \(f\) is increasing on \((-\infty, -[[p]])\) and on \(([[q]], \infty)\).
   check: solve(g > 0, x) = solve((x + p)*(x - q) > 0, x)

<!-- tier 1: the meaning of the sign of f' -->
## Card calc1.4-5.incdec-concept.001
skill: calc1.shape.increasing-decreasing
difficulty: 1
answer-type: choice

### Question
Suppose \(f'(x) < 0\) for every \(x\) in the interval \((2, 5)\). Which statement about \(f\) on \((2, 5)\) must be true?

### Choices
- [x] \(f\) is decreasing on \((2, 5)\)
- [ ] \(f\) is increasing on \((2, 5)\)
- [ ] \(f\) is concave down on \((2, 5)\)
- [ ] \(f(x) < 0\) for every \(x\) in \((2, 5)\)

### Solution
0. [calc1.shape.increasing-decreasing] Set up: the sign of the first derivative tells whether the function values rise or fall as the input grows. A negative derivative means they fall, so the function is decreasing. Concavity is decided by the second derivative, and the sign of the derivative says nothing about the sign of the function itself.

<!-- tier 1: one critical number, a parabola -->
## Card calc1.4-5.incdec-quad.001
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.power-rule, alg.solve.linear
difficulty: 1
answer-type: interval
endpoints: either
vars: x
answer: (-inf, 3)

### Question
On what interval is \(f(x) = x^2 - 6x + 4\) decreasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function decreases where its derivative is negative.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 2x - 6\).
   check: diff(x^2 - 6*x + 4, x) = 2*x - 6
2. [alg.solve.linear] Solve \(f'(x) < 0\): \(2x < 6\), so \(x < 3\).
   check: solve(2*x - 6 < 0, x) = solve(x - 3 < 0, x)
3. [calc1.shape.increasing-decreasing] Conclude: \(f\) is decreasing on \((-\infty, 3)\).
   check: solve(diff(x^2 - 6*x + 4, x) < 0, x) = solve(x - 3 < 0, x)

<!-- tier 2, template: cubic whose derivative factors -->
## Card calc1.4-5.incdec-cubic.t01
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: a = int(-3, 1); b = int(2, 5); x
require: a + b != 0
let: f = 2*x^3 - 3*(a + b)*x^2 + 6*a*b*x; g = 6*(x - a)*(x - b)
answer: solve(g > 0, x)
wrong: solve(g < 0, x) => That is where \(f'\) is negative, so \(f\) is decreasing there. @6; solve((x + a)*(x + b) > 0, x) => Check the signs of the zeros: a factor \(x - c\) is zero at \(x = c\), not at \(x = -c\). @3

### Question
On what intervals is \(f(x) = [[tex(f)]]\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive. Find the derivative, its zeros, and its sign on each piece.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(diff(f, x))]]\).
   check: diff(f, x) = 6*x^2 - 6*(a + b)*x + 6*a*b
2. [alg.factor.polynomials] Factor: \(f'(x) = [[tex(6*(x - a)*(x - b))]]\).
   check: expand(6*(x - a)*(x - b)) = 6*x^2 - 6*(a + b)*x + 6*a*b
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = [[a]]\) or \(x = [[b]]\).
   check: solve(g, x) = {a, b}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = [[a]]\) and \(x = [[b]]\).
   check: {a, b} = {a, b}
5. [alg.inequality.sign-chart] Sign chart: \(f'([[a - 1]]) = [[6*(b - a + 1)]]\), \(f'([[b + 1]]) = [[6*(b - a + 1)]]\), and \(f'\) is negative between the two zeros.
   check: subs(g, x, a - 1) = 6*(b - a + 1)
   check: subs(g, x, b + 1) = 6*(b - a + 1)
   check: subs(g, x, (a + b)/2) = -6*(b - a)^2/4
6. [calc1.shape.increasing-decreasing] Conclude: \(f' > 0\) on the two outer pieces, so \(f\) is increasing on \((-\infty, [[a]])\) and on \(([[b]], \infty)\).
   check: solve(diff(f, x) > 0, x) = solve(g > 0, x)

<!-- tier 2, template: the logarithm restricts the domain -->
## Card calc1.4-5.incdec-log.t01
skill: calc1.shape.increasing-decreasing
uses: pre.functions.domain, calc1.deriv.logarithm, alg.solve.rational-equation, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: k = int(2, 6); x
let: f = x^2 - 2*k^2*ln(x); g = 2*x - 2*k^2/x
answer: (0, k)
wrong: (-k, k) => A logarithm is defined only for \(x > 0\), so the interval cannot reach below \(0\). @1; (k, inf) => That is where \(f'\) is positive, so \(f\) is increasing there. @5

### Question
On what interval is \(f(x) = [[tex(f)]]\) decreasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function decreases where its derivative is negative. Work inside the domain of the function.
1. [pre.functions.domain] Domain: a logarithm needs a positive input, so \(f\) is defined only for \(x > 0\).
   check: solve(x > 0, x) = solve(x > 0, x)
2. [calc1.deriv.logarithm] Differentiate: \(f'(x) = 2x - \frac{[[2*k^2]]}{x}\).
   check: diff(f, x) = 2*x - 2*k^2/x
3. [alg.solve.rational-equation] Solve \(f'(x) = 0\): multiply by \(x\) (note \(x \ne 0\)) to get \(2x^2 = [[2*k^2]]\), so \(x = \pm [[k]]\).
   check: solve(g, x) = {-k, k}
4. [calc1.extrema.critical-numbers] Critical numbers: \(x = -[[k]]\) is not in the domain and \(f'\) does not exist at \(x = 0\), which is not in the domain either. So the only critical number is \(x = [[k]]\).
   check: {k} = {k}
5. [alg.inequality.sign-chart] Sign chart on \(x > 0\): \(f'\left([[tex(k/2)]]\right) = [[-3*k]]\) and \(f'([[2*k]]) = [[3*k]]\), so \(f'\) is negative on \((0, [[k]])\) and positive on \(([[k]], \infty)\).
   check: subs(g, x, k/2) = -3*k
   check: subs(g, x, 2*k) = 3*k
6. [calc1.shape.increasing-decreasing] Conclude: \(f' < 0\) only inside the domain piece \(0 < x < [[k]]\), so \(f\) is decreasing on \((0, [[k]])\).

<!-- tier 2: product with an exponential -->
## Card calc1.4-5.incdec-exp.001
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.product-rule, calc1.deriv.chain-linear-inside, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: x
answer: (0, 1)
wrong: (-inf, 0) U (1, inf) => That is where \(f'\) is negative, so \(f\) is decreasing there. @6; (0, inf) => The factor \(1 - x\) is negative for \(x > 1\), so \(f'\) changes sign again at \(x = 1\). @6

### Question
On what interval is \(f(x) = x^2 e^{-2x}\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive. Find the derivative, its zeros, and its sign on each piece.
1. [calc1.deriv.product-rule] Product rule: \(f'(x) = 2x\,e^{-2x} + x^2\left(e^{-2x}\right)'\).
   check: diff(x^2*e^(-2*x), x) = 2*x*e^(-2*x) + x^2*diff(e^(-2*x), x)
2. [calc1.deriv.chain-linear-inside] Chain rule with a linear inside: \(\left(e^{-2x}\right)' = -2e^{-2x}\), so \(f'(x) = 2x\,e^{-2x} - 2x^2 e^{-2x}\).
   check: diff(e^(-2*x), x) = -2*e^(-2*x)
   check: 2*x*e^(-2*x) - 2*x^2*e^(-2*x) = diff(x^2*e^(-2*x), x)
3. [alg.factor.polynomials] Factor out the common factor: \(f'(x) = 2x(1 - x)e^{-2x}\).
   check: 2*x*(1 - x)*e^(-2*x) = 2*x*e^(-2*x) - 2*x^2*e^(-2*x)
4. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(e^{-2x}\) is never zero, so \(x = 0\) or \(x = 1\).
   check: solve(2*x*(1 - x)*e^(-2*x), x) = {0, 1}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = 0\) and \(x = 1\).
   check: {0, 1} = {0, 1}
6. [alg.inequality.sign-chart] Sign chart: since \(e^{-2x} > 0\), the sign of \(f'\) is the sign of \(2x(1 - x)\). Test points: \(f'(-1) = -4e^{2}\), \(f'\left(\frac{1}{2}\right) = \frac{1}{2e}\) and \(f'(2) = -4e^{-4}\). So \(f'\) is negative, positive, negative.
   check: subs(2*x*(1 - x)*e^(-2*x), x, -1) = -4*e^2
   check: subs(2*x*(1 - x)*e^(-2*x), x, 1/2) = 1/(2*e)
   check: subs(2*x*(1 - x)*e^(-2*x), x, 2) = -4*e^(-4)
7. [calc1.shape.increasing-decreasing] Conclude: \(f\) is increasing on \((0, 1)\).
   check: solve(2*x*(1 - x) > 0, x) = solve(x*(x - 1) < 0, x)

<!-- tier 2: a flat spot where f' does not change sign -->
## Card calc1.4-5.incdec-flat.001
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
vars: x
answer: (-inf, inf)
wrong: (-inf, 2) U (2, inf) => The derivative is zero at \(x = 2\), but it does not change sign there, so \(f\) keeps increasing through \(x = 2\) and the two pieces join into one interval. @5; (2, inf) => The derivative is also positive for \(x < 2\). @5

### Question
On what intervals is \(f(x) = x^3 - 6x^2 + 12x + 1\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive. A single point where the derivative is zero does not stop the function from increasing, as long as the derivative does not change sign there.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 - 12x + 12\).
   check: diff(x^3 - 6*x^2 + 12*x + 1, x) = 3*x^2 - 12*x + 12
2. [alg.factor.polynomials] Factor: \(f'(x) = 3(x - 2)^2\).
   check: expand(3*(x - 2)^2) = 3*x^2 - 12*x + 12
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = 2\), a repeated zero.
   check: solve(3*(x - 2)^2, x) = {2}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the only critical number is \(x = 2\).
   check: {2} = {2}
5. [alg.inequality.sign-chart] Sign chart: \(f'(1) = 3\) and \(f'(3) = 3\), so \(f'\) is positive on both sides of \(x = 2\). It never changes sign.
   check: subs(3*(x - 2)^2, x, 1) = 3
   check: subs(3*(x - 2)^2, x, 3) = 3
6. [calc1.shape.increasing-decreasing] Conclude: \(f' \ge 0\) everywhere and is zero only at \(x = 2\), so \(f\) is increasing on \((-\infty, \infty)\).
   check: solve(3*(x - 2)^2 >= 0, x) = solve(3*x^2 - 12*x + 12 >= 0, x)

<!-- tier 3, template: a domain gap splits the answer -->
## Card calc1.4-5.incdec-rational.t01
skill: calc1.shape.increasing-decreasing
uses: pre.functions.domain, calc1.deriv.quotient-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: k = int(1, 9); x
let: f = x^2/(x - k); g = x*(x - 2*k)/(x - k)^2
answer: (0, k) U (k, 2*k)
wrong: (0, 2*k) => \(f\) is not defined at \(x = [[k]]\), so that point cannot be inside an interval where \(f\) is decreasing. @1; (-inf, 0) U (2*k, inf) => That is where \(f'\) is positive, so \(f\) is increasing there. @6

### Question
On what intervals is \(f(x) = [[tex(f)]]\) decreasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function decreases where its derivative is negative. Find the domain first, then the derivative, its zeros, and its sign on each piece.
1. [pre.functions.domain] Domain: the denominator is zero at \(x = [[k]]\), so \(f\) is defined for every \(x \ne [[k]]\).
   check: solve(x - k, x) = {k}
2. [calc1.deriv.quotient-rule] Quotient rule: \(f'(x) = \frac{2x(x - [[k]]) - x^2}{(x - [[k]])^2} = \frac{x^2 - [[2*k]]x}{(x - [[k]])^2}\).
   check: diff(f, x) = (x^2 - 2*k*x)/(x - k)^2
3. [alg.factor.polynomials] Factor the numerator: \(f'(x) = \frac{x(x - [[2*k]])}{(x - [[k]])^2}\).
   check: expand(x*(x - 2*k)) = x^2 - 2*k*x
4. [alg.solve.polynomial] Solve \(f'(x) = 0\): the numerator is zero at \(x = 0\) and \(x = [[2*k]]\).
   check: solve(x*(x - 2*k), x) = {0, 2*k}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) does not exist at \(x = [[k]]\), but \(f\) is not defined there, so it is not a critical number. The critical numbers are \(x = 0\) and \(x = [[2*k]]\).
   check: {0, 2*k} = {0, 2*k}
6. [alg.inequality.sign-chart] Sign chart: the zeros \(0\) and \([[2*k]]\) and the break at \([[k]]\) cut the line into four pieces. Test points give \(f'(-1) = \frac{[[2*k + 1]]}{[[(k + 1)^2]]}\), \(f'\left([[tex(k/2)]]\right) = -3\), \(f'\left([[tex(3*k/2)]]\right) = -3\) and \(f'([[3*k]]) = \frac{3}{4}\). So \(f'\) is positive, negative, negative, positive.
   check: subs(g, x, -1) = (2*k + 1)/(k + 1)^2
   check: subs(g, x, k/2) = -3
   check: subs(g, x, 3*k/2) = -3
   check: subs(g, x, 3*k) = 3/4
7. [calc1.shape.increasing-decreasing] Conclude: \(f' < 0\) on \((0, [[k]])\) and on \(([[k]], [[2*k]])\), so \(f\) is decreasing on both. The point \(x = [[k]]\) is not in the domain.
   check: solve(diff(f, x) < 0, x) = solve(g < 0, x)

<!-- tier 3: trig on an interval -->
## Card calc1.4-5.incdec-trig.001
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.trig-sin-cos, trig.equations.solve, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: x
answer: (pi/3, 5*pi/3)
wrong: (0, pi/3) U (5*pi/3, 2*pi) => That is where \(f'\) is negative, so \(f\) is decreasing there. @4; (pi/6, 11*pi/6) => \(\cos x = \frac{1}{2}\) at \(x = \frac{\pi}{3}\) and \(\frac{5\pi}{3}\). The angles \(\frac{\pi}{6}\) and \(\frac{11\pi}{6}\) belong to \(\sin x = \pm\frac{1}{2}\). @2

### Question
On what interval inside \((0, 2\pi)\) is \(f(x) = x - 2\sin x\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive. Find the derivative, its zeros in the interval, and its sign on each piece.
1. [calc1.deriv.trig-sin-cos] Differentiate: \(f'(x) = 1 - 2\cos x\).
   check: diff(x - 2*sin(x), x) = 1 - 2*cos(x)
2. [trig.equations.solve] Solve \(f'(x) = 0\): \(\cos x = \frac{1}{2}\), so \(x = \frac{\pi}{3}\) or \(x = \frac{5\pi}{3}\) in \((0, 2\pi)\).
   check: subs(1 - 2*cos(x), x, pi/3) = 0
   check: subs(1 - 2*cos(x), x, 5*pi/3) = 0
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers in the interval are \(x = \frac{\pi}{3}\) and \(x = \frac{5\pi}{3}\).
   check: {pi/3, 5*pi/3} = {pi/3, 5*pi/3}
4. [alg.inequality.sign-chart] Sign chart: \(f'(0) = -1\), \(f'(\pi) = 3\) and \(f'(2\pi) = -1\), so \(f'\) is negative, positive, negative on the three pieces.
   check: subs(1 - 2*cos(x), x, 0) = -1
   check: subs(1 - 2*cos(x), x, pi) = 3
   check: subs(1 - 2*cos(x), x, 2*pi) = -1
5. [calc1.shape.increasing-decreasing] Conclude: \(f' > 0\) between the two zeros, so \(f\) is increasing on \(\left(\frac{\pi}{3}, \frac{5\pi}{3}\right)\).

<!-- tier 3, adapted from CLP-1: the domain excludes the point where the derivative is undefined -->
## Card calc1.4-5.incdec-quotient-exp.001
skill: calc1.shape.increasing-decreasing
uses: pre.functions.domain, calc1.deriv.exponential, calc1.deriv.quotient-rule, alg.solve.linear, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: x
answer: (-inf, -3) U (-3, -2)
wrong: (-inf, -2) => The function is not defined at \(x = -3\), so that point cannot be inside an interval where \(f\) is decreasing. @1; (-2, inf) => That is where \(f'\) is positive, so \(f\) is increasing there. @6
source: CLP-1 Differential Calculus problem book (Feldman, Rechnitzer, Yeager), Section 3.6.2, question 2
source-url: https://github.com/arechnitzer/CLP1/blob/9f0295936d395bec68dab7915057135a2c7f0414/latex/problembook/problems/prob_s3.6.2.tex
license: CC BY-NC-SA 4.0
modified: yes

### Question
On what intervals is \(f(x) = \dfrac{e^x}{x + 3}\) decreasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function decreases where its derivative is negative. Find the domain first, then the derivative, its zeros, and its sign on each piece.
1. [pre.functions.domain] Domain: the denominator is zero at \(x = -3\), so \(f\) is defined for every \(x \ne -3\).
   check: solve(x + 3, x) = {-3}
2. [calc1.deriv.exponential] Differentiate the numerator: \((e^x)' = e^x\).
   check: diff(e^x, x) = e^x
3. [calc1.deriv.quotient-rule] Quotient rule: \(f'(x) = \frac{e^x(x + 3) - e^x}{(x + 3)^2} = \frac{e^x(x + 2)}{(x + 3)^2}\).
   check: diff(e^x/(x + 3), x) = e^x*(x + 2)/(x + 3)^2
4. [alg.solve.linear] Solve \(f'(x) = 0\): \(e^x\) is never zero, so \(x + 2 = 0\) and \(x = -2\).
   check: solve(x + 2, x) = {-2}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) does not exist at \(x = -3\), but \(f\) is not defined there, so the only critical number is \(x = -2\).
   check: {-2} = {-2}
6. [alg.inequality.sign-chart] Sign chart: since \(e^x > 0\) and \((x + 3)^2 > 0\), the sign of \(f'\) is the sign of \(x + 2\). Test points: \(f'(-4) = -2e^{-4}\), \(f'\left(-\frac{5}{2}\right) = -2e^{-5/2}\) and \(f'(0) = \frac{2}{9}\). So \(f'\) is negative on \((-\infty, -3)\) and on \((-3, -2)\), and positive on \((-2, \infty)\).
   check: subs(e^x*(x + 2)/(x + 3)^2, x, -4) = -2*e^(-4)
   check: subs(e^x*(x + 2)/(x + 3)^2, x, -5/2) = -2*e^(-5/2)
   check: subs(e^x*(x + 2)/(x + 3)^2, x, 0) = 2/9
7. [calc1.shape.increasing-decreasing] Conclude: \(f\) is decreasing on \((-\infty, -3)\) and on \((-3, -2)\).
   check: solve((x + 2)/(x + 3)^2 < 0, x) = solve((x + 2)/(x + 3)^2 < 0, x)

<!-- tier 4, template: for which values of a parameter is f increasing everywhere -->
## Card calc1.4-5.incdec-param.t01
skill: calc1.shape.increasing-decreasing
uses: calc1.deriv.power-rule, alg.solve.quadratic-formula, alg.inequality.sign-chart
difficulty: 4
answer-type: interval
vars: c = int(1, 9); k
let: f = x^3 + k*x^2 + c*k*x
answer: [0, 3*c]
wrong: (0, 3*c) => The endpoints work too: at \(k = 0\) the function is \(x^3\), and at \(k = [[3*c]]\) the derivative is \(3(x + [[c]])^2\), which is zero at only one point. @4; (-inf, 0] U [3*c, inf) => That is where the discriminant is positive or zero, so \(f'\) takes negative values. @3

### Question
Find all values of \(k\) for which \(f(x) = [[tex(f)]]\) is increasing on \((-\infty, \infty)\).

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function is increasing on the whole line when its derivative is never negative and is zero only at isolated points. Here the derivative is an upward-opening parabola, so this happens exactly when it does not have two distinct real zeros, which means its discriminant is at most zero.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 + 2kx + [[tex(c*k)]]\).
   check: diff(f, x) = 3*x^2 + 2*k*x + c*k
2. [alg.solve.quadratic-formula] Discriminant of \(3x^2 + 2kx + [[tex(c*k)]]\): \(b^2 - 4ac = (2k)^2 - 4(3)\left([[tex(c*k)]]\right) = 4k^2 - [[12*c]]k\).
   check: (2*k)^2 - 4*3*(c*k) = 4*k^2 - 12*c*k
3. [alg.inequality.sign-chart] Solve \(4k^2 - [[12*c]]k \le 0\): factor as \(4k(k - [[3*c]]) \le 0\). The product is positive for \(k < 0\), negative for \(0 < k < [[3*c]]\) and positive for \(k > [[3*c]]\).
   check: subs(4*k*(k - 3*c), k, -1) = 4*(1 + 3*c)
   check: subs(4*k*(k - 3*c), k, c) = -8*c^2
   check: subs(4*k*(k - 3*c), k, 3*c + 1) = 4*(3*c + 1)
4. [calc1.shape.increasing-decreasing] Conclude: the endpoints are allowed, because at \(k = 0\) we get \(f' = 3x^2\) and at \(k = [[3*c]]\) we get \(f' = 3(x + [[c]])^2\), each zero at a single point only. So \(f\) is increasing on \((-\infty, \infty)\) exactly when \(0 \le k \le [[3*c]]\).
   check: subs(3*x^2 + 2*k*x + c*k, k, 3*c) = 3*(x + c)^2
   check: solve(4*k^2 - 12*c*k <= 0, k) = solve(k*(k - 3*c) <= 0, k)

<!-- tier 4: the domain is a closed interval and f' has a square root in its denominator -->
## Card calc1.4-5.incdec-sqrt.001
skill: calc1.shape.increasing-decreasing
uses: pre.functions.domain, calc1.deriv.product-rule, calc1.deriv.chain-rule, alg.fraction.combine, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 4
answer-type: interval
endpoints: either
vars: x
answer: (-sqrt(2), sqrt(2))
wrong: (-2, 2) => The derivative is negative near both ends of the domain: for example \(f'\left(\frac{3}{2}\right) < 0\). @7; (-2, -sqrt(2)) U (sqrt(2), 2) => That is where \(f'\) is negative, so \(f\) is decreasing there. @7

### Question
On what interval is \(f(x) = x\sqrt{4 - x^2}\) increasing?

### Solution
0. [calc1.shape.increasing-decreasing] Set up: a function increases where its derivative is positive. Find the domain, the derivative, where it is zero or undefined, and its sign on each piece.
1. [pre.functions.domain] Domain: the square root needs \(4 - x^2 \ge 0\), so \(f\) is defined exactly on \([-2, 2]\).
   check: solve(4 - x^2 >= 0, x) = solve((2 - x)*(2 + x) >= 0, x)
2. [calc1.deriv.product-rule] Product rule: \(f'(x) = (1)\sqrt{4 - x^2} + x\left(\sqrt{4 - x^2}\right)'\).
   check: diff(x*sqrt(4 - x^2), x) = sqrt(4 - x^2) + x*diff(sqrt(4 - x^2), x)
3. [calc1.deriv.chain-rule] Chain rule: \(\left(\sqrt{4 - x^2}\right)' = \frac{-2x}{2\sqrt{4 - x^2}} = -\frac{x}{\sqrt{4 - x^2}}\), so \(f'(x) = \sqrt{4 - x^2} - \frac{x^2}{\sqrt{4 - x^2}}\).
   check: diff(sqrt(4 - x^2), x) = -x/sqrt(4 - x^2)
4. [alg.fraction.combine] Combine over \(\sqrt{4 - x^2}\): \(f'(x) = \frac{(4 - x^2) - x^2}{\sqrt{4 - x^2}} = \frac{4 - 2x^2}{\sqrt{4 - x^2}}\).
   check: sqrt(4 - x^2) - x^2/sqrt(4 - x^2) = (4 - 2*x^2)/sqrt(4 - x^2)
5. [alg.solve.polynomial] Solve \(f'(x) = 0\): the numerator \(4 - 2x^2 = 2(2 - x^2)\) is zero when \(x^2 = 2\), so \(x = \pm\sqrt{2}\).
   check: solve(4 - 2*x^2, x) = {-sqrt(2), sqrt(2)}
6. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) does not exist at \(x = \pm 2\), but these are the ends of the domain, not interior points. So the critical numbers are \(x = \pm\sqrt{2}\), and both are inside \((-2, 2)\).
   check: {-sqrt(2), sqrt(2)} = {-sqrt(2), sqrt(2)}
7. [alg.inequality.sign-chart] Sign chart on \((-2, 2)\): the denominator is positive there, so the sign of \(f'\) is the sign of \(4 - 2x^2\). The numerator is \(-\frac{1}{2}\) at \(x = -\frac{3}{2}\), \(4\) at \(x = 0\) and \(-\frac{1}{2}\) at \(x = \frac{3}{2}\). So \(f'\) is negative, positive, negative.
   check: subs(4 - 2*x^2, x, -3/2) = -1/2
   check: subs(4 - 2*x^2, x, 0) = 4
   check: subs(4 - 2*x^2, x, 3/2) = -1/2
8. [calc1.shape.increasing-decreasing] Conclude: \(f\) is increasing on \(\left(-\sqrt{2}, \sqrt{2}\right)\) and decreasing on \((-2, -\sqrt{2})\) and \((\sqrt{2}, 2)\).
   check: solve(4 - 2*x^2 > 0, x) = solve(x^2 - 2 < 0, x)



<!-- ===================================================================== -->
<!-- calc1.shape.first-derivative-test                                     -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.fdt-example.001
kind: example
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart

### Question
Find the critical numbers of \(f(x) = x^4 - 4x^3\) and classify each one as a local maximum, a local minimum or neither.

### Solution
0. [calc1.shape.first-derivative-test] Set up: at a critical number, look at the sign of the derivative just to the left and just to the right. If it changes from positive to negative there is a local maximum, if it changes from negative to positive there is a local minimum, and if it does not change sign there is no local extremum.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 4x^3 - 12x^2\).
   check: diff(x^4 - 4*x^3, x) = 4*x^3 - 12*x^2
2. [alg.factor.polynomials] Factor: \(f'(x) = 4x^2(x - 3)\).
   check: expand(4*x^2*(x - 3)) = 4*x^3 - 12*x^2
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = 0\) or \(x = 3\).
   check: solve(4*x^2*(x - 3), x) = {0, 3}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = 0\) and \(x = 3\).
   check: {0, 3} = {0, 3}
5. [alg.inequality.sign-chart] Sign chart: \(f'(-1) = -16\), \(f'(1) = -8\) and \(f'(4) = 64\). So \(f'\) is negative on \((-\infty, 0)\), negative on \((0, 3)\) and positive on \((3, \infty)\).
   check: subs(4*x^2*(x - 3), x, -1) = -16
   check: subs(4*x^2*(x - 3), x, 1) = -8
   check: subs(4*x^2*(x - 3), x, 4) = 64
6. [calc1.shape.first-derivative-test] Classify: at \(x = 0\) the derivative is negative on both sides, so it does not change sign and \(f\) has no local extremum there. At \(x = 3\) the derivative changes from negative to positive, so \(f\) has a local minimum, with value \(f(3) = -27\).
   check: subs(x^4 - 4*x^3, x, 3) = -27

<!-- tier 1, template: read the sign pattern of f' -->
## Card calc1.4-5.fdt-signs.t01
skill: calc1.shape.first-derivative-test
difficulty: 1
answer-type: number
vars: p = int(-3, 1); q = int(2, 6)
answer: p
wrong: q => At \(x = [[q]]\) the derivative changes from negative to positive, which is a local minimum, not a maximum. @1

### Question
A function \(f\) is continuous for all real numbers. Its derivative satisfies \(f'(x) > 0\) for \(x < [[p]]\), \(f'(x) < 0\) for \([[p]] < x < [[q]]\) and \(f'(x) > 0\) for \(x > [[q]]\). At what \(x\)-value does \(f\) have a local maximum?

### Solution
0. [calc1.shape.first-derivative-test] Set up: a local maximum is where the derivative changes from positive to negative, so the function rises and then falls.
1. [calc1.shape.first-derivative-test] Read the sign changes: the derivative changes from positive to negative at \(x = [[p]]\), a local maximum, and from negative to positive at \(x = [[q]]\), a local minimum.
   check: p = p

<!-- tier 1: a zero of f' is not enough -->
## Card calc1.4-5.fdt-zero-not-enough.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: truefalse
answer: false

### Question
True or false: if \(f\) is differentiable and \(f'(c) = 0\), then \(f\) has a local maximum or a local minimum at \(x = c\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: a zero of the derivative is only a candidate. For a local extremum the derivative must also change sign there.
1. [calc1.deriv.power-rule] Counterexample: take \(f(x) = x^3\), so \(f'(x) = 3x^2\).
   check: diff(x^3, x) = 3*x^2
2. [calc1.shape.first-derivative-test] Classify: \(f'(0) = 0\), but \(f'(-1) = 3\) and \(f'(1) = 3\) are both positive, so \(f'\) does not change sign at \(0\). The function \(x^3\) increases through \(x = 0\) and has no local extremum there, so the statement is false.
   check: subs(3*x^2, x, 0) = 0
   check: subs(3*x^2, x, -1) = 3
   check: subs(3*x^2, x, 1) = 3

<!-- tier 1, template: a parabola has one turning point -->
## Card calc1.4-5.fdt-quad.t01
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.solve.linear
difficulty: 1
answer-type: number
vars: a = int(1, 3); h = int(-4, 4, not 0); c = int(-5, 5)
require: c != h
let: f = a*x^2 - 2*a*h*x + c; g = 2*a*x - 2*a*h
answer: h
wrong: -h => Check the sign when you solve \(f'(x) = 0\) for \(x\). @2; c => That is the \(y\)-intercept. The question asks for an \(x\)-value. @3

### Question
The function \(f(x) = [[tex(f)]]\) has a local minimum at exactly one \(x\)-value. Find it.

### Solution
0. [calc1.shape.first-derivative-test] Set up: find where the derivative is zero, then check that it changes sign there.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(g)]]\).
   check: diff(f, x) = g
2. [alg.solve.linear] Solve \(f'(x) = 0\): \(x = [[h]]\).
   check: solve(g, x) = {h}
3. [calc1.shape.first-derivative-test] Classify: \(f'([[h - 1]]) = [[-2*a]]\) and \(f'([[h + 1]]) = [[2*a]]\), so the derivative changes from negative to positive at \(x = [[h]]\). That is a local minimum, at \(x = [[h]]\).
   check: subs(g, x, h - 1) = -2*a
   check: subs(g, x, h + 1) = 2*a
   check: h = h

<!-- tier 2, template: a cubic with one maximum and one minimum, found as points -->
## Card calc1.4-5.fdt-cubic.t01
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 2
answer-type: point
vars: m = int(1, 3); c = int(-5, 5, not 0)
let: f = x^3 - 3*m^2*x + c; g = 3*(x - m)*(x + m)
answer: (-m, c + 2*m^3), (m, c - 2*m^3)
wrong: (-m, c - 2*m^3), (m, c + 2*m^3) => Check the heights: \(f([[-m]]) = [[c + 2*m^3]]\) and \(f([[m]]) = [[c - 2*m^3]]\). @6; (m, c + 2*m^3), (-m, c - 2*m^3) => Check the signs of the zeros of \(f'\): \(x - [[m]]\) is zero at \(x = [[m]]\), and \(x + [[m]]\) at \(x = -[[m]]\). @3

### Question
Find the local maximum point and the local minimum point of \(f(x) = [[tex(f)]]\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers, check how the sign of the derivative changes at each, and then find the height of the graph there.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(diff(f, x))]]\).
   check: diff(f, x) = 3*x^2 - 3*m^2
2. [alg.factor.polynomials] Factor: \(f'(x) = 3(x - [[m]])(x + [[m]])\).
   check: expand(g) = 3*x^2 - 3*m^2
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = [[m]]\) or \(x = -[[m]]\).
   check: solve(g, x) = {-m, m}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = -[[m]]\) and \(x = [[m]]\).
   check: {-m, m} = {-m, m}
5. [alg.inequality.sign-chart] Sign chart: \(f'([[-m - 1]]) = [[3*(2*m + 1)]]\), \(f'(0) = [[-3*m^2]]\) and \(f'([[m + 1]]) = [[3*(2*m + 1)]]\). So \(f'\) is positive, negative, positive.
   check: subs(g, x, -m - 1) = 3*(2*m + 1)
   check: subs(g, x, 0) = -3*m^2
   check: subs(g, x, m + 1) = 3*(2*m + 1)
6. [alg.arith.exact-evaluation] Evaluate \(f\) at the critical numbers: \(f(-[[m]]) = [[c + 2*m^3]]\) and \(f([[m]]) = [[c - 2*m^3]]\).
   check: subs(f, x, -m) = c + 2*m^3
   check: subs(f, x, m) = c - 2*m^3
7. [calc1.shape.first-derivative-test] Classify: the derivative changes from positive to negative at \(x = -[[m]]\), a local maximum, and from negative to positive at \(x = [[m]]\), a local minimum. So the local maximum point and the local minimum point are \((-[[m]], [[c + 2*m^3]]), ([[m]], [[c - 2*m^3]])\).

<!-- tier 2: a critical number where f' does not change sign -->
## Card calc1.4-5.fdt-neither.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: set
answer: -1, 1
wrong: -1, 0, 1 => At \(x = 0\) the derivative is negative on both sides, so it does not change sign and there is no extremum there. @6; -1 => The derivative also changes sign at \(x = 1\), from negative to positive, so \(f\) has a local minimum there. @6

### Question
Find all \(x\)-values at which \(f(x) = 3x^5 - 5x^3\) has a local extremum.

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers, then check at each one whether the derivative changes sign.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 15x^4 - 15x^2\).
   check: diff(3*x^5 - 5*x^3, x) = 15*x^4 - 15*x^2
2. [alg.factor.polynomials] Factor: \(f'(x) = 15x^2(x - 1)(x + 1)\).
   check: expand(15*x^2*(x - 1)*(x + 1)) = 15*x^4 - 15*x^2
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = -1\), \(x = 0\) or \(x = 1\).
   check: solve(15*x^2*(x - 1)*(x + 1), x) = {-1, 0, 1}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(-1\), \(0\) and \(1\).
   check: {-1, 0, 1} = {-1, 0, 1}
5. [alg.inequality.sign-chart] Sign chart: \(f'(-2) = 180\), \(f'\left(-\frac{1}{2}\right) = -\frac{45}{16}\), \(f'\left(\frac{1}{2}\right) = -\frac{45}{16}\) and \(f'(2) = 180\). So \(f'\) is positive, negative, negative, positive.
   check: subs(15*x^2*(x - 1)*(x + 1), x, -2) = 180
   check: subs(15*x^2*(x - 1)*(x + 1), x, -1/2) = -45/16
   check: subs(15*x^2*(x - 1)*(x + 1), x, 1/2) = -45/16
   check: subs(15*x^2*(x - 1)*(x + 1), x, 2) = 180
6. [calc1.shape.first-derivative-test] Classify: at \(x = -1\) the derivative changes from positive to negative (local maximum). At \(x = 0\) it is negative on both sides (no extremum). At \(x = 1\) it changes from negative to positive (local minimum). So the local extrema are at \(x = -1\) and \(x = 1\).
   check: {-1, 1} = {-1, 1}

<!-- tier 2, template: f' is given, one factor is squared -->
## Card calc1.4-5.fdt-double-root.t01
skill: calc1.shape.first-derivative-test
uses: alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart
difficulty: 2
answer-type: set
vars: a = int(1, 4); b = int(1, 4)
let: g = x*(x - a)^2*(x + b)
answer: -b, 0
wrong: -b, 0, a => The factor \((x - [[a]])^2\) is never negative, so the derivative does not change sign at \(x = [[a]]\) and there is no extremum there. @3; 0, a => The factor \(x + [[b]]\) is zero at \(x = -[[b]]\), not at \(x = [[b]]\). @1

### Question
A function \(f\) is continuous for all real numbers and \(f'(x) = x(x - [[a]])^2(x + [[b]])\). Find all \(x\)-values at which \(f\) has a local extremum.

### Solution
0. [calc1.shape.first-derivative-test] Set up: the derivative is given in factored form, so find its zeros and check whether its sign changes at each one.
1. [alg.solve.polynomial] Zero-product rule: \(f'(x) = 0\) at \(x = -[[b]]\), \(x = 0\) and \(x = [[a]]\).
   check: solve(g, x) = {-b, 0, a}
2. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) is a polynomial, so it exists everywhere and the critical numbers are \(-[[b]]\), \(0\) and \([[a]]\).
   check: {-b, 0, a} = {-b, 0, a}
3. [alg.inequality.sign-chart] Sign chart: \(f'([[-b - 1]]) = [[(b + 1)*(a + b + 1)^2]]\), \(f'\left(-\frac{1}{2}\right) = [[tex(-(1/2)*(a + 1/2)^2*(b - 1/2))]]\), \(f'\left(\frac{1}{2}\right) = [[tex((1/2)*(a - 1/2)^2*(b + 1/2))]]\) and \(f'([[a + 1]]) = [[(a + 1)*(a + b + 1)]]\). So \(f'\) is positive, negative, positive, positive.
   check: subs(g, x, -b - 1) = (b + 1)*(a + b + 1)^2
   check: subs(g, x, -1/2) = -(1/2)*(a + 1/2)^2*(b - 1/2)
   check: subs(g, x, 1/2) = (1/2)*(a - 1/2)^2*(b + 1/2)
   check: subs(g, x, a + 1) = (a + 1)*(a + b + 1)
4. [calc1.shape.first-derivative-test] Classify: the derivative changes sign at \(x = -[[b]]\) (a local maximum) and at \(x = 0\) (a local minimum), but not at \(x = [[a]]\), where it is positive on both sides. So the local extrema are at \(x = -[[b]]\) and \(x = 0\).
   check: {-b, 0} = {-b, 0}

<!-- tier 2: product with an exponential, extrema as points -->
## Card calc1.4-5.fdt-exp.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.exponential, calc1.deriv.product-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 2
answer-type: point
answer: (0, 3), (1, e)
wrong: (3/2, 3*e^(3/2)/4) => Use the product rule: the factor \(e^x\) also has a derivative. Differentiating only the polynomial misses a term. @2; (0, 3) => The derivative also changes sign at \(x = 1\), from negative to positive, so \(f\) has a local minimum there. @8

### Question
Find all local extrema of \(f(x) = (x^2 - 3x + 3)e^x\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers, check how the sign of the derivative changes at each, and then find the height of the graph there.
1. [calc1.deriv.exponential] Differentiate the exponential: \((e^x)' = e^x\).
   check: diff(e^x, x) = e^x
2. [calc1.deriv.product-rule] Product rule: \(f'(x) = (2x - 3)e^x + (x^2 - 3x + 3)e^x\).
   check: diff((x^2 - 3*x + 3)*e^x, x) = (2*x - 3)*e^x + (x^2 - 3*x + 3)*e^x
3. [alg.factor.polynomials] Factor out \(e^x\): \(f'(x) = (x^2 - x)e^x = x(x - 1)e^x\).
   check: x*(x - 1)*e^x = (2*x - 3)*e^x + (x^2 - 3*x + 3)*e^x
4. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(e^x\) is never zero, so \(x = 0\) or \(x = 1\).
   check: solve(x*(x - 1)*e^x, x) = {0, 1}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(0\) and \(1\).
   check: {0, 1} = {0, 1}
6. [alg.inequality.sign-chart] Sign chart: \(f'(-1) = \frac{2}{e}\), \(f'\left(\frac{1}{2}\right) = -\frac{\sqrt{e}}{4}\) and \(f'(2) = 2e^2\). So \(f'\) is positive, negative, positive.
   check: subs(x*(x - 1)*e^x, x, -1) = 2/e
   check: subs(x*(x - 1)*e^x, x, 1/2) = -sqrt(e)/4
   check: subs(x*(x - 1)*e^x, x, 2) = 2*e^2
7. [alg.arith.exact-evaluation] Evaluate: \(f(0) = 3\) and \(f(1) = e\).
   check: subs((x^2 - 3*x + 3)*e^x, x, 0) = 3
   check: subs((x^2 - 3*x + 3)*e^x, x, 1) = e
8. [calc1.shape.first-derivative-test] Classify: the derivative changes from positive to negative at \(x = 0\), a local maximum, and from negative to positive at \(x = 1\), a local minimum. The local extrema are the points \((0, 3), (1, e)\).


<!-- tier 3: a vertical tangent where f' does not change sign -->
## Card calc1.4-5.fdt-vertical-tangent.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule-rational, alg.factor.lowest-power, calc1.extrema.critical-numbers, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
answer: (-1, -3)
wrong: (0, 0), (-1, -3) => The derivative does not exist at \(x = 0\), but it is positive on both sides of \(0\). The graph has a vertical tangent there and keeps rising, so \(x = 0\) is not an extremum. @4; (-1, 5) => The real cube root of \(-1\) is \(-1\), so \(f(-1) = 1 - 4 = -3\). @5

### Question
Find all local extrema of \(f(x) = x^{4/3} + 4x^{1/3}\), as points \((x, f(x))\). Here \(x^{1/3}\) is the real cube root, so \(f\) is defined for every real number.

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers, including any where the derivative does not exist, and check how the sign of the derivative changes at each.
1. [calc1.deriv.power-rule-rational] Differentiate: \(f'(x) = \frac{4}{3}x^{1/3} + \frac{4}{3}x^{-2/3}\).
   check: diff(u^4 + 4*u, u)/diff(u^3, u) = (4*u^3 + 4)/(3*u^2)
   check: 4/3*u + 4/3*u^(-2) = (4*u^3 + 4)/(3*u^2)
2. [alg.factor.lowest-power] Factor out the lowest power: \(f'(x) = \frac{4}{3}x^{-2/3}(x + 1) = \frac{4(x + 1)}{3x^{2/3}}\).
   check: 4/3*u^(-2)*(u^3 + 1) = 4/3*u + 4/3*u^(-2)
3. [calc1.extrema.critical-numbers] Critical numbers: the numerator is zero at \(x = -1\), and \(f'\) does not exist at \(x = 0\), which is in the domain. So the critical numbers are \(x = -1\) and \(x = 0\).
   check: solve(x + 1, x) = {-1}
4. [alg.inequality.sign-chart] Sign chart: \(x^{2/3} > 0\) for \(x \ne 0\), so the sign of \(f'\) is the sign of \(x + 1\). Test points: \(f'(-8) = -\frac{7}{3}\), \(f'\left(-\frac{1}{8}\right) = \frac{14}{3}\) and \(f'(8) = 3\). So \(f'\) is negative, positive, positive.
   check: subs(4*(u^3 + 1)/(3*u^2), u, -2) = -7/3
   check: subs(4*(u^3 + 1)/(3*u^2), u, -1/2) = 14/3
   check: subs(4*(u^3 + 1)/(3*u^2), u, 2) = 3
5. [alg.arith.exact-evaluation] Evaluate: \(f(-1) = (-1)^{4/3} + 4(-1)^{1/3} = 1 - 4 = -3\).
   check: subs(u^4 + 4*u, u, -1) = -3
6. [calc1.shape.first-derivative-test] Classify: at \(x = -1\) the derivative changes from negative to positive, a local minimum. At \(x = 0\) the derivative is positive on both sides, so there is no extremum. The only local extremum is the local minimum at the point \((-1, -3)\).

<!-- tier 3, template: corners of an absolute value -->
## Card calc1.4-5.fdt-abs-corners.t01
skill: calc1.shape.first-derivative-test
uses: alg.abs.piecewise, calc1.deriv.power-rule, calc1.extrema.critical-numbers, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
vars: a = int(2, 4); k = int(1, 4)
let: f = a*abs(x^2 - k^2)
answer: (-k, 0), (0, a*k^2), (k, 0)
wrong: (0, a*k^2) => The derivative does not exist at \(x = \pm [[k]]\), but \(f\) is defined there and the derivative changes sign, from negative to positive. Those corners are local minima. @3; (-k, 0), (k, 0) => The derivative also changes sign at \(x = 0\), from positive to negative, so \(f\) has a local maximum there. @6

### Question
Find all local extrema of \(f(x) = [[a]]\left|x^2 - [[k^2]]\right|\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: rewrite the function without the absolute value, then find the critical numbers, including any where the derivative does not exist, and check how its sign changes at each.
1. [alg.abs.piecewise] Piecewise form: \(x^2 - [[k^2]] < 0\) exactly for \(-[[k]] < x < [[k]]\), so \(f(x) = [[a]](x^2 - [[k^2]])\) for \(x \le -[[k]]\) or \(x \ge [[k]]\), and \(f(x) = [[a]]([[k^2]] - x^2)\) for \(-[[k]] < x < [[k]]\).
   check: solve(x^2 - k^2 < 0, x) = solve((x - k)*(x + k) < 0, x)
2. [calc1.deriv.power-rule] Differentiate each piece: \(f'(x) = [[2*a]]x\) for \(x < -[[k]]\) or \(x > [[k]]\), and \(f'(x) = -[[2*a]]x\) for \(-[[k]] < x < [[k]]\).
   check: diff(a*(x^2 - k^2), x) = 2*a*x
   check: diff(a*(k^2 - x^2), x) = -2*a*x
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) is zero at \(x = 0\). At \(x = \pm [[k]]\) the one-sided slopes are \(-[[2*a*k]]\) and \([[2*a*k]]\), so \(f'\) does not exist there, and \(f\) is defined at \(\pm [[k]]\). The critical numbers are \(-[[k]]\), \(0\) and \([[k]]\).
   check: subs(2*a*x, x, -k) = -2*a*k
   check: subs(-2*a*x, x, -k) = 2*a*k
   check: subs(-2*a*x, x, k) = -2*a*k
   check: subs(2*a*x, x, k) = 2*a*k
4. [alg.inequality.sign-chart] Sign chart: \(f'(-[[k + 1]]) = -[[2*a*(k + 1)]]\), \(f'\left(-[[tex(k/2)]]\right) = [[a*k]]\), \(f'\left([[tex(k/2)]]\right) = -[[a*k]]\) and \(f'([[k + 1]]) = [[2*a*(k + 1)]]\). So \(f'\) is negative, positive, negative, positive.
   check: subs(2*a*x, x, -k - 1) = -2*a*(k + 1)
   check: subs(-2*a*x, x, -k/2) = a*k
   check: subs(-2*a*x, x, k/2) = -a*k
   check: subs(2*a*x, x, k + 1) = 2*a*(k + 1)
5. [alg.arith.exact-evaluation] Evaluate: \(f(-[[k]]) = 0\), \(f(0) = [[a*k^2]]\) and \(f([[k]]) = 0\).
   check: subs(f, x, -k) = 0
   check: subs(f, x, 0) = a*k^2
   check: subs(f, x, k) = 0
6. [calc1.shape.first-derivative-test] Classify: the derivative changes from negative to positive at \(x = -[[k]]\) (local minimum), from positive to negative at \(x = 0\) (local maximum) and from negative to positive at \(x = [[k]]\) (local minimum). The local extrema are the points \((-[[k]], 0), (0, [[a*k^2]]), ([[k]], 0)\).

<!-- tier 3: trig on an interval -->
## Card calc1.4-5.fdt-trig.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.trig-sin-cos, trig.equations.solve, calc1.extrema.critical-numbers, alg.inequality.sign-chart, trig.values.exact
difficulty: 3
answer-type: point
answer: (pi/6, pi/6 + sqrt(3)), (5*pi/6, 5*pi/6 - sqrt(3))
wrong: (7*pi/6, 7*pi/6 - sqrt(3)), (11*pi/6, 11*pi/6 + sqrt(3)) => The derivative of \(\cos x\) is \(-\sin x\), so \(f'(x) = 1 - 2\sin x\), not \(1 + 2\sin x\). @1; (pi/6, pi/6 + sqrt(3)) => The derivative also changes sign at \(x = \frac{5\pi}{6}\), from negative to positive, so \(f\) has a local minimum there. @5

### Question
Find all local extrema of \(f(x) = x + 2\cos x\) on the interval \((0, 2\pi)\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers in the interval, check how the sign of the derivative changes at each, and then find the height of the graph there.
1. [calc1.deriv.trig-sin-cos] Differentiate: \(f'(x) = 1 - 2\sin x\).
   check: diff(x + 2*cos(x), x) = 1 - 2*sin(x)
2. [trig.equations.solve] Solve \(f'(x) = 0\): \(\sin x = \frac{1}{2}\), so \(x = \frac{\pi}{6}\) or \(x = \frac{5\pi}{6}\) in \((0, 2\pi)\).
   check: subs(1 - 2*sin(x), x, pi/6) = 0
   check: subs(1 - 2*sin(x), x, 5*pi/6) = 0
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers in the interval are \(\frac{\pi}{6}\) and \(\frac{5\pi}{6}\).
   check: {pi/6, 5*pi/6} = {pi/6, 5*pi/6}
4. [alg.inequality.sign-chart] Sign chart: \(f'(0) = 1\), \(f'\left(\frac{\pi}{2}\right) = -1\) and \(f'(\pi) = 1\). So \(f'\) is positive, negative, positive.
   check: subs(1 - 2*sin(x), x, 0) = 1
   check: subs(1 - 2*sin(x), x, pi/2) = -1
   check: subs(1 - 2*sin(x), x, pi) = 1
5. [trig.values.exact] Evaluate with exact values: \(f\left(\frac{\pi}{6}\right) = \frac{\pi}{6} + \sqrt{3}\) and \(f\left(\frac{5\pi}{6}\right) = \frac{5\pi}{6} - \sqrt{3}\).
   check: subs(x + 2*cos(x), x, pi/6) = pi/6 + sqrt(3)
   check: subs(x + 2*cos(x), x, 5*pi/6) = 5*pi/6 - sqrt(3)
6. [calc1.shape.first-derivative-test] Classify: the derivative changes from positive to negative at \(x = \frac{\pi}{6}\), a local maximum, and from negative to positive at \(x = \frac{5\pi}{6}\), a local minimum. The local extrema are the points \(\left(\frac{\pi}{6}, \frac{\pi}{6} + \sqrt{3}\right), \left(\frac{5\pi}{6}, \frac{5\pi}{6} - \sqrt{3}\right)\).

<!-- tier 4, template: work backwards from the extrema to the function -->
## Card calc1.4-5.fdt-inverse.t01
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.expand.products, alg.solve.linear
difficulty: 4
vars: s = int(-2, 2, not 0); t = int(1, 3)
require: s^2 != t^2
let: p = s - t; q = s + t

### Question
The function \(f(x) = x^3 + ax^2 + bx\) has a local maximum at \(x = [[p]]\) and a local minimum at \(x = [[q]]\). Find the constants \(a\) and \(b\).

### Part a
answer-type: number
answer: -3*s
wrong: 3*s => The coefficient of \(x\) in \(f'\) must equal \([[-6*s]]\), and it is \(2a\). Keep the sign when you solve for \(a\). @3
Find \(a\).

### Part b
answer-type: number
answer: 3*(s^2 - t^2)
wrong: s^2 - t^2 => The derivative has leading coefficient 3, so it is 3 times the product of two linear factors. Its constant term, which is \(b\), is 3 times the product of the zeros. @2
Find \(b\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: a local maximum and a local minimum at these two places mean the derivative is zero at both, and it changes sign from positive to negative at the first and from negative to positive at the second. The derivative of this cubic is a quadratic with leading coefficient 3, so it must be 3 times the product of the two linear factors.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 + 2ax + b\).
   check: diff(x^3 + a*x^2 + b*x, x) = 3*x^2 + 2*a*x + b
2. [alg.expand.products] Expand the factored form: \(f'(x) = [[tex(3*(x - p)*(x - q))]] = [[tex(3*x^2 - 6*s*x + 3*(s^2 - t^2))]]\).
   check: expand(3*(x - p)*(x - q)) = 3*x^2 - 6*s*x + 3*(s^2 - t^2)
3. [alg.solve.linear] Match coefficients: \(2a = [[-6*s]]\), so \(a = [[-3*s]]\), and \(b = [[3*(s^2 - t^2)]]\).
   check: solve(2*a + 6*s, a) = {-3*s}
   check: 3*(s - t)*(s + t) = 3*(s^2 - t^2)
4. [calc1.shape.first-derivative-test] Check: with these values \(f'(x) = [[tex(3*(x - p)*(x - q))]]\) is positive before the first zero, negative between the zeros and positive after the second, so the local maximum really is at \(x = [[p]]\) and the local minimum at \(x = [[q]]\).
   check: subs(3*(x - p)*(x - q), x, p - 1) = 3*(2*t + 1)
   check: subs(3*(x - p)*(x - q), x, s) = -3*t^2
   check: subs(3*(x - p)*(x - q), x, q + 1) = 3*(2*t + 1)

<!-- tier 4: four critical numbers, two of them not standard angles -->
## Card calc1.4-5.fdt-trig-double.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.trig-sin-cos, calc1.deriv.chain-linear-inside, trig.identities.pythagorean, alg.factor.polynomials, trig.equations.solve, calc1.extrema.critical-numbers, alg.inequality.sign-chart, trig.values.exact
difficulty: 4
answer-type: point
answer: (arcsin(1/4), 9/8), (pi/2, 0), (pi - arcsin(1/4), 9/8), (3*pi/2, -2)
wrong: (pi/2, 0), (3*pi/2, -2) => The factor \(1 - 4\sin x\) is also zero, at \(\sin x = \frac{1}{4}\), and the derivative changes sign at both of those angles too. Those are local maxima. @5; (pi/6, 1), (pi/2, 0), (5*pi/6, 1), (3*pi/2, -2) => By the chain rule \((\cos 2x)' = -2\sin 2x\). Keep the factor \(2\). @2

### Question
Find all local extrema of \(f(x) = \sin x + \cos 2x\) on the interval \((0, 2\pi)\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.first-derivative-test] Set up: find the critical numbers in the interval, check how the sign of the derivative changes at each, and then find the height of the graph there.
1. [calc1.deriv.trig-sin-cos] Differentiate the sine and the cosine: \((\sin x)' = \cos x\) and \((\cos u)' = -\sin u\).
   check: diff(sin(x), x) = cos(x)
   check: diff(cos(u), u) = -sin(u)
2. [calc1.deriv.chain-linear-inside] Chain rule with the linear inside \(u = 2x\): \(f'(x) = \cos x - 2\sin 2x\).
   check: diff(sin(x) + cos(2*x), x) = cos(x) - 2*sin(2*x)
3. [trig.identities.pythagorean] Double-angle identity \(\sin 2x = 2\sin x\cos x\): \(f'(x) = \cos x - 4\sin x\cos x\).
   check: cos(x) - 2*sin(2*x) = cos(x) - 4*sin(x)*cos(x)
4. [alg.factor.polynomials] Factor out \(\cos x\): \(f'(x) = \cos x\,(1 - 4\sin x)\).
   check: cos(x)*(1 - 4*sin(x)) = cos(x) - 4*sin(x)*cos(x)
5. [trig.equations.solve] Solve \(f'(x) = 0\): \(\cos x = 0\) gives \(x = \frac{\pi}{2}\) or \(\frac{3\pi}{2}\), and \(\sin x = \frac{1}{4}\) gives \(x = \arcsin\frac{1}{4}\) or \(x = \pi - \arcsin\frac{1}{4}\) in \((0, 2\pi)\).
   check: subs(cos(x)*(1 - 4*sin(x)), x, pi/2) = 0
   check: subs(cos(x)*(1 - 4*sin(x)), x, 3*pi/2) = 0
   check: subs(cos(x)*(1 - 4*sin(x)), x, arcsin(1/4)) = 0
   check: subs(cos(x)*(1 - 4*sin(x)), x, pi - arcsin(1/4)) = 0
6. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\). In increasing order the critical numbers are \(\arcsin\frac{1}{4} \approx 0.25\), \(\frac{\pi}{2}\), \(\pi - \arcsin\frac{1}{4} \approx 2.89\) and \(\frac{3\pi}{2}\).
   check: {arcsin(1/4), pi/2, pi - arcsin(1/4), 3*pi/2} = {arcsin(1/4), pi/2, pi - arcsin(1/4), 3*pi/2}
7. [alg.inequality.sign-chart] Sign chart: \(f'(0) = 1\), \(f'\left(\frac{\pi}{6}\right) = -\frac{\sqrt{3}}{2}\), \(f'\left(\frac{2\pi}{3}\right) = \frac{2\sqrt{3} - 1}{2}\), \(f'(\pi) = -1\) and \(f'(2\pi) = 1\). One test point lies in each of the five pieces, so \(f'\) is positive, negative, positive, negative, positive.
   check: subs(cos(x) - 2*sin(2*x), x, 0) = 1
   check: subs(cos(x) - 2*sin(2*x), x, pi/6) = -sqrt(3)/2
   check: subs(cos(x) - 2*sin(2*x), x, 2*pi/3) = (2*sqrt(3) - 1)/2
   check: subs(cos(x) - 2*sin(2*x), x, pi) = -1
   check: subs(cos(x) - 2*sin(2*x), x, 2*pi) = 1
8. [trig.values.exact] Evaluate at the standard angles: \(f\left(\frac{\pi}{2}\right) = 1 + \cos\pi = 0\) and \(f\left(\frac{3\pi}{2}\right) = -1 + \cos 3\pi = -2\).
   check: subs(sin(x) + cos(2*x), x, pi/2) = 0
   check: subs(sin(x) + cos(2*x), x, 3*pi/2) = -2
9. [trig.identities.pythagorean] Evaluate where \(\sin x = \frac{1}{4}\): the double-angle identity \(\cos 2x = 1 - 2\sin^2 x\) gives \(\cos 2x = \frac{7}{8}\), so \(f = \frac{1}{4} + \frac{7}{8} = \frac{9}{8}\) at both of those critical numbers.
   check: 1 - 2*(1/4)^2 = 7/8
   check: subs(sin(x) + cos(2*x), x, arcsin(1/4)) = 9/8
   check: subs(sin(x) + cos(2*x), x, pi - arcsin(1/4)) = 9/8
10. [calc1.shape.first-derivative-test] Classify: the derivative changes from positive to negative at the first and third critical numbers (local maxima) and from negative to positive at the second and fourth (local minima). The local extrema are the points \(\left(\arcsin\frac{1}{4}, \frac{9}{8}\right), \left(\frac{\pi}{2}, 0\right), \left(\pi - \arcsin\frac{1}{4}, \frac{9}{8}\right), \left(\frac{3\pi}{2}, -2\right)\).



<!-- ===================================================================== -->
<!-- calc1.shape.concavity                                                 -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.conc-example.001
kind: example
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart

### Question
On what intervals is the graph of \(f(x) = x^4 - 8x^3 + 18x^2\) concave up, and on what intervals is it concave down?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive and concave down where it is negative. Differentiate twice, find where the second derivative is zero, and test its sign on each piece.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = 4x^3 - 24x^2 + 36x\) and \(f''(x) = 12x^2 - 48x + 36\).
   check: diff(x^4 - 8*x^3 + 18*x^2, x) = 4*x^3 - 24*x^2 + 36*x
   check: diff(x^4 - 8*x^3 + 18*x^2, x, 2) = 12*x^2 - 48*x + 36
2. [alg.factor.polynomials] Factor: \(f''(x) = 12(x - 1)(x - 3)\).
   check: expand(12*(x - 1)*(x - 3)) = 12*x^2 - 48*x + 36
3. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(x = 1\) or \(x = 3\).
   check: solve(12*(x - 1)*(x - 3), x) = {1, 3}
4. [alg.inequality.sign-chart] Sign chart: \(f''(0) = 36\), \(f''(2) = -12\) and \(f''(4) = 36\). So \(f''\) is positive, negative, positive.
   check: subs(12*(x - 1)*(x - 3), x, 0) = 36
   check: subs(12*(x - 1)*(x - 3), x, 2) = -12
   check: subs(12*(x - 1)*(x - 3), x, 4) = 36
5. [calc1.shape.concavity] Conclude: the graph is concave up on \((-\infty, 1)\) and on \((3, \infty)\), and concave down on \((1, 3)\).
   check: solve(12*x^2 - 48*x + 36 > 0, x) = solve((x - 1)*(x - 3) > 0, x)
   check: solve(12*x^2 - 48*x + 36 < 0, x) = solve((x - 1)*(x - 3) < 0, x)

<!-- tier 1, template: the second derivative is linear -->
## Card calc1.4-5.conc-cubic.t01
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule, alg.solve.linear
difficulty: 1
answer-type: interval
endpoints: either
vars: p = int(-3, 4); q = int(-5, 5); x
let: f = x^3 - 3*p*x^2 + q*x
answer: (p, inf)
wrong: (-inf, p) => That is where \(f''\) is negative, so the graph is concave down there. @2

### Question
On what interval is the graph of \(f(x) = [[tex(f)]]\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = [[tex(diff(f, x))]]\) and \(f''(x) = [[tex(diff(f, x, 2))]]\).
   check: diff(f, x) = 3*x^2 - 6*p*x + q
   check: diff(f, x, 2) = 6*x - 6*p
2. [alg.solve.linear] Solve \(f''(x) > 0\): \(6x > [[6*p]]\), so \(x > [[p]]\).
   check: solve(6*x - 6*p > 0, x) = solve(x - p > 0, x)
3. [calc1.shape.concavity] Conclude: \(f'' > 0\) exactly when \(x > [[p]]\), so the graph is concave up on \(([[p]], \infty)\).
   check: solve(diff(f, x, 2) > 0, x) = solve(x - p > 0, x)

<!-- tier 1: the sign of f'' at a point -->
## Card calc1.4-5.conc-point.001
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: text
answer: concave up; up; concave upward

### Question
Is the graph of \(f(x) = x^4 - 4x^2\) concave up or concave down at \(x = 1\)? Answer "concave up" or "concave down".

### Solution
0. [calc1.shape.concavity] Set up: the graph is concave up at a point where the second derivative is positive and concave down where it is negative.
1. [calc1.deriv.power-rule] Differentiate twice: \(f''(x) = 12x^2 - 8\).
   check: diff(x^4 - 4*x^2, x, 2) = 12*x^2 - 8
2. [calc1.shape.concavity] Evaluate: \(f''(1) = 4 > 0\), so the graph is concave up at \(x = 1\).
   check: subs(12*x^2 - 8, x, 1) = 4

<!-- tier 1: increasing does not mean concave up -->
## Card calc1.4-5.conc-tf.001
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: truefalse
answer: false

### Question
True or false: if \(f\) is increasing on an interval, then the graph of \(f\) is concave up on that interval.

### Solution
0. [calc1.shape.concavity] Set up: increasing is decided by the sign of the first derivative, and concavity by the sign of the second derivative. They are different conditions, so look for a counterexample.
1. [calc1.deriv.power-rule] Counterexample: take \(f(x) = -x^2\) on \((-\infty, 0)\), so \(f'(x) = -2x\) and \(f''(x) = -2\).
   check: diff(-x^2, x) = -2*x
   check: diff(-x^2, x, 2) = -2
2. [calc1.shape.concavity] Conclude: \(f'(-1) = 2 > 0\), so \(f\) is increasing for \(x < 0\), but \(f'' = -2 < 0\), so the graph is concave down there. The statement is false.
   check: subs(-2*x, x, -1) = 2

<!-- tier 2, template: a quartic, concave down between two inflection candidates -->
## Card calc1.4-5.conc-quartic.t01
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: k = int(1, 5); c = int(-5, 5); x
let: f = x^4 - 6*k^2*x^2 + c*x; g = 12*(x - k)*(x + k)
answer: (-k, k)
wrong: (-inf, -k) U (k, inf) => That is where \(f''\) is positive, so the graph is concave up there. @5; (0, k) => The inequality \(x^2 < [[k^2]]\) holds for \(-[[k]] < x < [[k]]\), on both sides of \(0\). @5

### Question
On what interval is the graph of \(f(x) = [[tex(f)]]\) concave down?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave down where the second derivative is negative. Differentiate twice, find the zeros of the second derivative, and test its sign on each piece.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = [[tex(diff(f, x))]]\) and \(f''(x) = [[tex(diff(f, x, 2))]]\).
   check: diff(f, x) = 4*x^3 - 12*k^2*x + c
   check: diff(f, x, 2) = 12*x^2 - 12*k^2
2. [alg.factor.polynomials] Factor: \(f''(x) = 12(x - [[k]])(x + [[k]])\).
   check: expand(g) = 12*x^2 - 12*k^2
3. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(x = -[[k]]\) or \(x = [[k]]\).
   check: solve(g, x) = {-k, k}
4. [alg.inequality.sign-chart] Sign chart: \(f''([[-k - 1]]) = [[12*(2*k + 1)]]\), \(f''(0) = [[-12*k^2]]\) and \(f''([[k + 1]]) = [[12*(2*k + 1)]]\). So \(f''\) is positive, negative, positive.
   check: subs(g, x, -k - 1) = 12*(2*k + 1)
   check: subs(g, x, 0) = -12*k^2
   check: subs(g, x, k + 1) = 12*(2*k + 1)
5. [calc1.shape.concavity] Conclude: \(f'' < 0\) only between the two zeros, so the graph is concave down on \((-[[k]], [[k]])\).
   check: solve(diff(f, x, 2) < 0, x) = solve(x^2 - k^2 < 0, x)

<!-- tier 2: product with an exponential, differentiated twice -->
## Card calc1.4-5.conc-xexp.001
skill: calc1.shape.concavity
uses: calc1.deriv.product-rule, calc1.deriv.chain-linear-inside, alg.solve.linear, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: x
answer: (2, inf)
wrong: (-inf, 2) => That is where \(f''\) is negative, so the graph is concave down there. @5; (-inf, 1) => The number \(1\) is where \(f'\) is zero. Concavity comes from \(f''\), which is zero at \(x = 2\). @3

### Question
On what interval is the graph of \(f(x) = xe^{-x}\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive. Differentiate twice, find where the second derivative is zero, and test its sign.
1. [calc1.deriv.product-rule] Product rule: \(f'(x) = (1)e^{-x} + x\left(e^{-x}\right)'\).
   check: diff(x*e^(-x), x) = e^(-x) + x*diff(e^(-x), x)
2. [calc1.deriv.chain-linear-inside] Chain rule with a linear inside: \(\left(e^{-x}\right)' = -e^{-x}\), so \(f'(x) = (1 - x)e^{-x}\).
   check: diff(e^(-x), x) = -e^(-x)
   check: (1 - x)*e^(-x) = e^(-x) + x*(-e^(-x))
3. [calc1.deriv.product-rule] Differentiate again with the product rule: \(f''(x) = -e^{-x} + (1 - x)\left(-e^{-x}\right) = (x - 2)e^{-x}\).
   check: diff((1 - x)*e^(-x), x) = (x - 2)*e^(-x)
4. [alg.solve.linear] Solve \(f''(x) = 0\): \(e^{-x}\) is never zero, so \(x - 2 = 0\) and \(x = 2\).
   check: solve((x - 2)*e^(-x), x) = {2}
5. [alg.inequality.sign-chart] Sign chart: since \(e^{-x} > 0\), the sign of \(f''\) is the sign of \(x - 2\). Test points: \(f''(1) = -e^{-1}\) and \(f''(3) = e^{-3}\).
   check: subs((x - 2)*e^(-x), x, 1) = -1/e
   check: subs((x - 2)*e^(-x), x, 3) = e^(-3)
6. [calc1.shape.concavity] Conclude: \(f'' > 0\) exactly when \(x > 2\), so the graph is concave up on \((2, \infty)\).
   check: solve((x - 2)*e^(-x) > 0, x) = solve(x - 2 > 0, x)

<!-- tier 2: f'' is zero at isolated points but never negative -->
## Card calc1.4-5.conc-always-up.001
skill: calc1.shape.concavity
uses: calc1.deriv.trig-sin-cos, trig.equations.solve
difficulty: 2
answer-type: interval
vars: x
answer: (-inf, inf)
wrong: (-inf, -pi/2) U (-pi/2, 3*pi/2) U (3*pi/2, inf) => The second derivative is zero at \(x = -\frac{\pi}{2}\) and \(x = \frac{3\pi}{2}\), but it is never negative, so it does not change sign there and the intervals join up. @2; none => The second derivative is never negative, so the graph is never concave down. It is concave up everywhere. @2

### Question
On what intervals is the graph of \(f(x) = \frac{x^2}{2} - \sin x\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive. A point where the second derivative is zero does not end a concave-up interval unless the sign changes there.
1. [calc1.deriv.trig-sin-cos] Differentiate twice: \(f'(x) = x - \cos x\) and \(f''(x) = 1 + \sin x\).
   check: diff(x^2/2 - sin(x), x) = x - cos(x)
   check: diff(x^2/2 - sin(x), x, 2) = 1 + sin(x)
2. [trig.equations.solve] Solve \(f''(x) = 0\): \(\sin x = -1\), so \(x = -\frac{\pi}{2} + 2\pi n\) for whole numbers \(n\). For example, \(x = -\frac{\pi}{2}\) and \(x = \frac{3\pi}{2}\).
   check: subs(1 + sin(x), x, -pi/2) = 0
   check: subs(1 + sin(x), x, 3*pi/2) = 0
3. [calc1.shape.concavity] Conclude: \(\sin x \ge -1\) for every \(x\), so \(f'' \ge 0\) everywhere and it is zero only at isolated points. It never changes sign, so the graph is concave up on \((-\infty, \infty)\).

<!-- tier 2, template: f'' is given with a repeated factor -->
## Card calc1.4-5.conc-given.t01
skill: calc1.shape.concavity
uses: alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 2
answer-type: interval
endpoints: either
vars: p = int(-3, 1); q = int(2, 5); x
let: g = (x - p)*(x - q)^2
answer: (p, inf)
wrong: (p, q) => The factor \((x - [[q]])^2\) is never negative, so \(f''\) stays positive after \(x = [[q]]\) and the graph stays concave up. @2; (-inf, p) => That is where \(f''\) is negative, so the graph is concave down there. @2

### Question
A function \(f\) has \(f''(x) = [[tex(g)]]\) for all real \(x\), and \(f'\) exists everywhere. On what interval is the graph of \(f\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive, so find the sign of the given second derivative.
1. [alg.solve.polynomial] Zero-product rule: \(f''(x) = 0\) at \(x = [[p]]\) and \(x = [[q]]\).
   check: solve(g, x) = {p, q}
2. [alg.inequality.sign-chart] Sign chart: \(f''([[p - 1]]) = [[-(q - p + 1)^2]]\), \(f''\left([[tex(p + 1/2)]]\right) = [[tex((1/2)*(q - p - 1/2)^2)]]\) and \(f''([[q + 1]]) = [[q - p + 1]]\). So \(f''\) is negative, positive, positive.
   check: subs(g, x, p - 1) = -(q - p + 1)^2
   check: subs(g, x, p + 1/2) = (1/2)*(q - p - 1/2)^2
   check: subs(g, x, q + 1) = q - p + 1
3. [calc1.shape.concavity] Conclude: \(f''\) is positive on both sides of \(x = [[q]]\) and zero only at that point, so the concavity does not change there. The graph is concave up on \(([[p]], \infty)\).


<!-- tier 3, template: the logarithm of a quadratic -->
## Card calc1.4-5.conc-log.t01
skill: calc1.shape.concavity
uses: calc1.deriv.logarithm, calc1.deriv.chain-rule, calc1.deriv.quotient-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: k = int(1, 9); x
let: f = ln(x^2 + k^2); g = 2*(k - x)*(k + x)
answer: (-k, k)
wrong: (-inf, -k) U (k, inf) => That is where \(f''\) is negative, so the graph is concave down there. @7; (0, inf) => That is where \(f'\) is positive, so \(f\) is increasing there. Concavity comes from \(f''\). @0

### Question
On what interval is the graph of \(f(x) = \ln\left(x^2 + [[k^2]]\right)\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive. Differentiate twice, find the zeros of the second derivative, and test its sign on each piece.
1. [calc1.deriv.logarithm] Outer function: \(\left(\ln u\right)' = \frac{1}{u}\), here with \(u = x^2 + [[k^2]]\).
   check: diff(ln(u), u) = 1/u
2. [calc1.deriv.chain-rule] Chain rule: multiply by \(u' = 2x\), so \(f'(x) = \frac{2x}{x^2 + [[k^2]]}\).
   check: diff(f, x) = 2*x/(x^2 + k^2)
3. [calc1.deriv.quotient-rule] Quotient rule: \(f''(x) = \frac{2(x^2 + [[k^2]]) - 2x(2x)}{(x^2 + [[k^2]])^2} = \frac{[[2*k^2]] - 2x^2}{(x^2 + [[k^2]])^2}\).
   check: diff(f, x, 2) = (2*k^2 - 2*x^2)/(x^2 + k^2)^2
4. [alg.factor.polynomials] Factor the numerator: \([[2*k^2]] - 2x^2 = 2([[k]] - x)([[k]] + x)\).
   check: expand(g) = 2*k^2 - 2*x^2
5. [alg.solve.polynomial] Solve \(f''(x) = 0\): the numerator is zero at \(x = -[[k]]\) and \(x = [[k]]\).
   check: solve(g, x) = {-k, k}
6. [alg.inequality.sign-chart] Sign chart: the denominator is always positive, so the sign of \(f''\) is the sign of the numerator. It is \([[-2*(2*k + 1)]]\) at \(x = [[-k - 1]]\), \([[2*k^2]]\) at \(x = 0\) and \([[-2*(2*k + 1)]]\) at \(x = [[k + 1]]\). So \(f''\) is negative, positive, negative.
   check: subs(g, x, -k - 1) = -2*(2*k + 1)
   check: subs(g, x, 0) = 2*k^2
   check: subs(g, x, k + 1) = -2*(2*k + 1)
7. [calc1.shape.concavity] Conclude: \(f'' > 0\) only between the two zeros, so the graph is concave up on \((-[[k]], [[k]])\).
   check: solve(diff(f, x, 2) > 0, x) = solve(k^2 - x^2 > 0, x)

<!-- tier 3: the domain excludes the point where f'' is undefined -->
## Card calc1.4-5.conc-reciprocal.001
skill: calc1.shape.concavity
uses: pre.functions.domain, calc1.deriv.power-rule-rational, alg.fraction.combine, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: x
answer: (-inf, -2) U (0, inf)
wrong: (-2, 0) => That is where \(f''\) is negative, so the graph is concave down there. @7; (0, inf) => The second derivative is also positive for \(x < -2\). @6

### Question
On what intervals is the graph of \(f(x) = x^2 + \dfrac{8}{x}\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive. Find the domain first, then differentiate twice and test the sign of the second derivative on each piece.
1. [pre.functions.domain] Domain: the denominator is zero at \(x = 0\), so \(f\) is defined for every \(x \ne 0\).
   check: solve(x, x) = {0}
2. [calc1.deriv.power-rule-rational] Differentiate twice: \(f(x) = x^2 + 8x^{-1}\), so \(f'(x) = 2x - 8x^{-2}\) and \(f''(x) = 2 + 16x^{-3} = 2 + \frac{16}{x^3}\).
   check: diff(x^2 + 8/x, x) = 2*x - 8/x^2
   check: diff(x^2 + 8/x, x, 2) = 2 + 16/x^3
3. [alg.fraction.combine] Combine over \(x^3\): \(f''(x) = \frac{2x^3 + 16}{x^3} = \frac{2(x^3 + 8)}{x^3}\).
   check: 2 + 16/x^3 = (2*x^3 + 16)/x^3
4. [alg.factor.polynomials] Sum of cubes: \(x^3 + 8 = (x + 2)(x^2 - 2x + 4)\).
   check: expand((x + 2)*(x^2 - 2*x + 4)) = x^3 + 8
5. [alg.solve.polynomial] Solve \(f''(x) = 0\): the numerator is zero when \(x + 2 = 0\), since \(x^2 - 2x + 4\) has no real zeros. So \(x = -2\).
   check: solve(x^3 + 8, x) = {-2}
6. [alg.inequality.sign-chart] Sign chart: \(x^2 - 2x + 4 > 0\) always, so the sign of \(f''\) is the sign of \(\frac{x + 2}{x}\), with breaks at \(x = -2\) and \(x = 0\). Test points: \(f''(-3) = \frac{38}{27}\), \(f''(-1) = -14\) and \(f''(1) = 18\). So \(f''\) is positive, negative, positive.
   check: subs(2 + 16/x^3, x, -3) = 38/27
   check: subs(2 + 16/x^3, x, -1) = -14
   check: subs(2 + 16/x^3, x, 1) = 18
7. [calc1.shape.concavity] Conclude: the graph is concave up on \((-\infty, -2)\) and on \((0, \infty)\), and concave down on \((-2, 0)\).
   check: solve(2 + 16/x^3 > 0, x) = solve((x + 2)/x > 0, x)

<!-- tier 3: the bell curve -->
## Card calc1.4-5.conc-gauss.001
skill: calc1.shape.concavity
uses: calc1.deriv.chain-rule, calc1.deriv.product-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: x
answer: (-inf, -sqrt(2)/2) U (sqrt(2)/2, inf)
wrong: (-sqrt(2)/2, sqrt(2)/2) => That is where \(f''\) is negative, so the graph is concave down there. @6; (-inf, -1/2) U (1/2, inf) => From \(2x^2 = 1\) we get \(x^2 = \frac{1}{2}\), so \(x = \pm\frac{\sqrt{2}}{2}\), not \(\pm\frac{1}{2}\). @4

### Question
On what intervals is the graph of \(f(x) = e^{-x^2}\) concave up?

### Solution
0. [calc1.shape.concavity] Set up: a graph is concave up where the second derivative is positive. Differentiate twice, find the zeros of the second derivative, and test its sign on each piece.
1. [calc1.deriv.chain-rule] Chain rule: \(\left(e^{u}\right)' = e^{u}u'\) with \(u = -x^2\), so \(f'(x) = -2x\,e^{-x^2}\).
   check: diff(e^(-x^2), x) = -2*x*e^(-x^2)
2. [calc1.deriv.product-rule] Product rule on \(f'\): \(f''(x) = -2e^{-x^2} + (-2x)\left(-2x\,e^{-x^2}\right) = (4x^2 - 2)e^{-x^2}\).
   check: diff(-2*x*e^(-x^2), x) = (4*x^2 - 2)*e^(-x^2)
3. [alg.factor.polynomials] Factor out \(2\): \(f''(x) = 2(2x^2 - 1)e^{-x^2}\).
   check: expand(2*(2*x^2 - 1)) = 4*x^2 - 2
4. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(e^{-x^2}\) is never zero, so \(2x^2 = 1\) and \(x = \pm\frac{\sqrt{2}}{2}\).
   check: solve(2*x^2 - 1, x) = {-sqrt(2)/2, sqrt(2)/2}
5. [alg.inequality.sign-chart] Sign chart: since \(e^{-x^2} > 0\), the sign of \(f''\) is the sign of \(2x^2 - 1\). It is \(1\) at \(x = -1\), \(-1\) at \(x = 0\) and \(1\) at \(x = 1\). So \(f''\) is positive, negative, positive.
   check: subs(2*x^2 - 1, x, -1) = 1
   check: subs(2*x^2 - 1, x, 0) = -1
   check: subs(2*x^2 - 1, x, 1) = 1
6. [calc1.shape.concavity] Conclude: \(f'' > 0\) when \(2x^2 - 1 > 0\), so the graph is concave up on \(\left(-\infty, -\frac{\sqrt{2}}{2}\right)\) and on \(\left(\frac{\sqrt{2}}{2}, \infty\right)\).
   check: solve(2*x^2 - 1 > 0, x) = solve(4*x^2 - 2 > 0, x)

<!-- tier 4, template: for which values of a parameter is the graph concave up everywhere -->
## Card calc1.4-5.conc-param.t01
skill: calc1.shape.concavity
uses: calc1.deriv.power-rule, alg.solve.quadratic-formula, alg.inequality.sign-chart
difficulty: 4
answer-type: interval
vars: m = int(1, 5); k
let: f = x^4 + k*x^3 + 6*m^2*x^2
answer: [-4*m, 4*m]
wrong: (-4*m, 4*m) => The endpoints work too: at \(k = [[4*m]]\) the second derivative is \(12(x + [[m]])^2\), which is zero at one point only and never negative. @3; (-inf, -4*m] U [4*m, inf) => That is where the discriminant is positive or zero, so \(f''\) takes negative values. @2

### Question
Find all values of \(k\) for which the graph of \(f(x) = [[tex(f)]]\) is concave up on \((-\infty, \infty)\).

### Solution
0. [calc1.shape.concavity] Set up: the graph is concave up on the whole line when the second derivative is never negative and is zero only at isolated points. Here the second derivative is an upward-opening parabola, so this happens exactly when it does not have two distinct real zeros, which means its discriminant is at most zero.
1. [calc1.deriv.power-rule] Differentiate twice: \(f''(x) = 12x^2 + 6kx + [[12*m^2]]\).
   check: diff(f, x, 2) = 12*x^2 + 6*k*x + 12*m^2
2. [alg.solve.quadratic-formula] Discriminant of \(12x^2 + 6kx + [[12*m^2]]\): \((6k)^2 - 4(12)([[12*m^2]]) = 36k^2 - [[576*m^2]]\).
   check: (6*k)^2 - 4*12*(12*m^2) = 36*k^2 - 576*m^2
3. [alg.inequality.sign-chart] Solve \(36k^2 - [[576*m^2]] \le 0\): factor as \(36(k - [[4*m]])(k + [[4*m]]) \le 0\). The product is positive for \(k < -[[4*m]]\), negative between the zeros and positive for \(k > [[4*m]]\). At the endpoint \(k = [[4*m]]\) the second derivative is \(12(x + [[m]])^2\), which is never negative.
   check: subs(36*(k - 4*m)*(k + 4*m), k, 0) = -576*m^2
   check: subs(36*(k - 4*m)*(k + 4*m), k, 5*m) = 324*m^2
   check: subs(36*(k - 4*m)*(k + 4*m), k, -5*m) = 324*m^2
   check: subs(12*x^2 + 6*k*x + 12*m^2, k, 4*m) = 12*(x + m)^2
4. [calc1.shape.concavity] Conclude: the graph is concave up on \((-\infty, \infty)\) exactly when \(-[[4*m]] \le k \le [[4*m]]\).
   check: solve(36*k^2 - 576*m^2 <= 0, k) = solve((k - 4*m)*(k + 4*m) <= 0, k)

<!-- tier 4: increasing and concave down together -->
## Card calc1.4-5.conc-both.001
skill: calc1.shape.concavity
uses: calc1.deriv.product-rule, calc1.deriv.chain-rule, alg.factor.polynomials, calc1.shape.increasing-decreasing, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 4
answer-type: interval
endpoints: either
vars: x
answer: (0, sqrt(2)/2)
wrong: (0, sqrt(6)/2) => That is where the graph is concave down. The question also requires \(f\) to be increasing, and \(f\) is decreasing for \(x > \frac{\sqrt{2}}{2}\). @9; (-sqrt(2)/2, 0) => On this interval \(f\) is increasing, but \(f'' > 0\), so the graph is concave up there. @9

### Question
On what interval is \(f(x) = xe^{-x^2}\) both increasing and concave down?

### Solution
0. [calc1.shape.concavity] Set up: find where the first derivative is positive and where the second derivative is negative, separately, then keep the numbers that satisfy both conditions.
1. [calc1.deriv.product-rule] Product rule: \(f'(x) = (1)e^{-x^2} + x\left(e^{-x^2}\right)'\).
   check: diff(x*e^(-x^2), x) = e^(-x^2) + x*diff(e^(-x^2), x)
2. [calc1.deriv.chain-rule] Chain rule: \(\left(e^{-x^2}\right)' = -2x\,e^{-x^2}\), so \(f'(x) = e^{-x^2} - 2x^2e^{-x^2}\).
   check: diff(e^(-x^2), x) = -2*x*e^(-x^2)
   check: e^(-x^2) + x*(-2*x*e^(-x^2)) = e^(-x^2) - 2*x^2*e^(-x^2)
3. [alg.factor.polynomials] Factor out \(e^{-x^2}\): \(f'(x) = (1 - 2x^2)e^{-x^2}\).
   check: (1 - 2*x^2)*e^(-x^2) = e^(-x^2) - 2*x^2*e^(-x^2)
4. [calc1.shape.increasing-decreasing] Increasing: since \(e^{-x^2} > 0\), \(f' > 0\) exactly when \(1 - 2x^2 > 0\), that is for \(-\frac{\sqrt{2}}{2} < x < \frac{\sqrt{2}}{2}\).
   check: solve(1 - 2*x^2 > 0, x) = solve(2*x^2 - 1 < 0, x)
5. [calc1.deriv.product-rule] Differentiate again with the product rule: \(f''(x) = -4x\,e^{-x^2} + (1 - 2x^2)\left(-2x\,e^{-x^2}\right) = (4x^3 - 6x)e^{-x^2}\).
   check: diff((1 - 2*x^2)*e^(-x^2), x) = (4*x^3 - 6*x)*e^(-x^2)
6. [alg.factor.polynomials] Factor: \(f''(x) = 2x(2x^2 - 3)e^{-x^2}\).
   check: expand(2*x*(2*x^2 - 3)) = 4*x^3 - 6*x
7. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(x = 0\) or \(2x^2 = 3\), so \(x = 0\) or \(x = \pm\frac{\sqrt{6}}{2}\).
   check: solve(2*x*(2*x^2 - 3), x) = {-sqrt(6)/2, 0, sqrt(6)/2}
8. [alg.inequality.sign-chart] Sign chart: the sign of \(f''\) is the sign of \(2x(2x^2 - 3)\). It is \(-20\) at \(x = -2\), \(2\) at \(x = -1\), \(-2\) at \(x = 1\) and \(20\) at \(x = 2\). So \(f''\) is negative on \(\left(-\infty, -\frac{\sqrt{6}}{2}\right)\) and on \(\left(0, \frac{\sqrt{6}}{2}\right)\).
   check: subs(2*x*(2*x^2 - 3), x, -2) = -20
   check: subs(2*x*(2*x^2 - 3), x, -1) = 2
   check: subs(2*x*(2*x^2 - 3), x, 1) = -2
   check: subs(2*x*(2*x^2 - 3), x, 2) = 20
9. [calc1.shape.concavity] Combine: \(f\) is increasing on \(\left(-\frac{\sqrt{2}}{2}, \frac{\sqrt{2}}{2}\right)\) and concave down on \(\left(-\infty, -\frac{\sqrt{6}}{2}\right)\) and \(\left(0, \frac{\sqrt{6}}{2}\right)\). Since \(\frac{\sqrt{2}}{2} \approx 0.71\) is less than \(\frac{\sqrt{6}}{2} \approx 1.22\), the only overlap is \(\left(0, \frac{\sqrt{2}}{2}\right)\).



<!-- ===================================================================== -->
<!-- calc1.shape.inflection-points                                         -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.infl-example.001
kind: example
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart, alg.arith.exact-evaluation

### Question
Find the inflection points of the graph of \(f(x) = x^5 - 5x^4\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is a point of the graph where the concavity changes, so the second derivative must change sign there. A zero of the second derivative is only a candidate. Differentiate twice, find the candidates, and check the sign of the second derivative on each side of each one.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = 5x^4 - 20x^3\) and \(f''(x) = 20x^3 - 60x^2\).
   check: diff(x^5 - 5*x^4, x) = 5*x^4 - 20*x^3
   check: diff(x^5 - 5*x^4, x, 2) = 20*x^3 - 60*x^2
2. [alg.factor.polynomials] Factor: \(f''(x) = 20x^2(x - 3)\).
   check: expand(20*x^2*(x - 3)) = 20*x^3 - 60*x^2
3. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(x = 0\) or \(x = 3\). The second derivative exists everywhere, so these are the only candidates.
   check: solve(20*x^2*(x - 3), x) = {0, 3}
4. [alg.inequality.sign-chart] Sign chart: \(f''(-1) = -80\), \(f''(1) = -40\) and \(f''(4) = 320\). So \(f''\) is negative, negative, positive.
   check: subs(20*x^2*(x - 3), x, -1) = -80
   check: subs(20*x^2*(x - 3), x, 1) = -40
   check: subs(20*x^2*(x - 3), x, 4) = 320
5. [calc1.shape.inflection-points] Decide: at \(x = 0\) the second derivative is negative on both sides, so the concavity does not change and there is no inflection point. At \(x = 3\) it changes from negative to positive, so the concavity changes there.
   check: {3} = {3}
6. [alg.arith.exact-evaluation] Evaluate: \(f(3) = 243 - 405 = -162\).
   check: subs(x^5 - 5*x^4, x, 3) = -162
7. [calc1.shape.inflection-points] Conclude: the only inflection point is \((3, -162)\).
   check: subs(x^5 - 5*x^4, x, 3) = -162

<!-- tier 1, template: a cubic has one inflection point -->
## Card calc1.4-5.infl-cubic.t01
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule, alg.solve.linear, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 1
answer-type: point
vars: p = int(-3, 3, not 0); q = int(-4, 4); r = int(-5, 5)
let: f = x^3 - 3*p*x^2 + q*x + r
answer: (p, -2*p^3 + q*p + r)
wrong: (-p, -4*p^3 - q*p + r) => Check the sign when you solve \(f''(x) = 0\) for \(x\). @2

### Question
Find the inflection point of the graph of \(f(x) = [[tex(f)]]\), as a point \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the second derivative changes sign. Find the zero of the second derivative, check the sign change, and find the height of the graph there.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = [[tex(diff(f, x))]]\) and \(f''(x) = [[tex(diff(f, x, 2))]]\).
   check: diff(f, x) = 3*x^2 - 6*p*x + q
   check: diff(f, x, 2) = 6*x - 6*p
2. [alg.solve.linear] Solve \(f''(x) = 0\): \(x = [[p]]\).
   check: solve(6*x - 6*p, x) = {p}
3. [alg.inequality.sign-chart] Sign chart: \(f''([[p - 1]]) = -6\) and \(f''([[p + 1]]) = 6\), so \(f''\) changes from negative to positive at \(x = [[p]]\).
   check: subs(6*x - 6*p, x, p - 1) = -6
   check: subs(6*x - 6*p, x, p + 1) = 6
4. [alg.arith.exact-evaluation] Evaluate: \(f([[p]]) = [[-2*p^3 + q*p + r]]\).
   check: subs(f, x, p) = -2*p^3 + q*p + r
5. [calc1.shape.inflection-points] Conclude: the concavity changes at \(x = [[p]]\), so the inflection point is \(([[p]], [[-2*p^3 + q*p + r]])\).

<!-- tier 1: what an inflection point is -->
## Card calc1.4-5.infl-concept.001
skill: calc1.shape.inflection-points
difficulty: 1
answer-type: choice

### Question
Which statement describes an inflection point of the graph of a function \(f\)?

### Choices
- [x] A point on the graph, where \(f\) is defined, at which the concavity changes from up to down or from down to up
- [ ] A point where \(f'(x) = 0\)
- [ ] A point where \(f''(x) = 0\), whether or not the concavity changes
- [ ] A point where \(f\) has a local maximum or a local minimum

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is defined by a change of concavity at a point of the graph, which means the second derivative changes sign there. A zero of the first derivative is a candidate for a local extremum, not for an inflection point. A zero of the second derivative is only a candidate for an inflection point, since the sign must also change.

<!-- tier 1: f'' = 0 is not enough -->
## Card calc1.4-5.infl-tf.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: truefalse
answer: false

### Question
True or false: if \(f''(c) = 0\), then the graph of \(f\) has an inflection point at \(x = c\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point needs a change of concavity, so the second derivative must change sign. A zero of the second derivative alone is not enough, so look for a counterexample.
1. [calc1.deriv.power-rule] Counterexample: take \(f(x) = x^4\), so \(f''(x) = 12x^2\).
   check: diff(x^4, x, 2) = 12*x^2
2. [calc1.shape.inflection-points] Decide: \(f''(0) = 0\), but \(f''(-1) = 12\) and \(f''(1) = 12\) are both positive, so the second derivative does not change sign at \(0\). The graph is concave up on both sides and has no inflection point at \(x = 0\), so the statement is false.
   check: subs(12*x^2, x, 0) = 0
   check: subs(12*x^2, x, -1) = 12
   check: subs(12*x^2, x, 1) = 12

<!-- tier 2, template: a quartic with two inflection points -->
## Card calc1.4-5.infl-quartic.t01
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 2
answer-type: point
vars: a = int(1, 3)
let: f = x^4 - 4*a*x^3
answer: (0, 0), (2*a, -16*a^4)
wrong: (0, 0) => The second derivative also changes sign at \(x = [[2*a]]\), from negative to positive, so there is a second inflection point. @6; (0, 0), (2*a, 0) => The height of the graph at \(x = [[2*a]]\) is \(f([[2*a]])\), not \(f''([[2*a]])\). @5

### Question
Find all inflection points of the graph of \(f(x) = [[tex(f)]]\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the second derivative changes sign. Find the zeros of the second derivative, check the sign on each side, and find the height of the graph at each.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = [[tex(diff(f, x))]]\) and \(f''(x) = [[tex(diff(f, x, 2))]]\).
   check: diff(f, x) = 4*x^3 - 12*a*x^2
   check: diff(f, x, 2) = 12*x^2 - 24*a*x
2. [alg.factor.polynomials] Factor: \(f''(x) = 12x(x - [[2*a]])\).
   check: expand(12*x*(x - 2*a)) = 12*x^2 - 24*a*x
3. [alg.solve.polynomial] Solve \(f''(x) = 0\): \(x = 0\) or \(x = [[2*a]]\).
   check: solve(12*x*(x - 2*a), x) = {0, 2*a}
4. [alg.inequality.sign-chart] Sign chart: \(f''(-1) = [[12*(2*a + 1)]]\), \(f''([[a]]) = [[-12*a^2]]\) and \(f''([[2*a + 1]]) = [[12*(2*a + 1)]]\). So \(f''\) is positive, negative, positive, and it changes sign at both zeros.
   check: subs(12*x*(x - 2*a), x, -1) = 12*(2*a + 1)
   check: subs(12*x*(x - 2*a), x, a) = -12*a^2
   check: subs(12*x*(x - 2*a), x, 2*a + 1) = 12*(2*a + 1)
5. [alg.arith.exact-evaluation] Evaluate: \(f(0) = 0\) and \(f([[2*a]]) = [[-16*a^4]]\).
   check: subs(f, x, 0) = 0
   check: subs(f, x, 2*a) = -16*a^4
6. [calc1.shape.inflection-points] Conclude: the concavity changes at both \(x = 0\) and \(x = [[2*a]]\), so the inflection points are \((0, 0), ([[2*a]], [[-16*a^4]])\).

<!-- tier 2, template: f'' is given with a repeated factor -->
## Card calc1.4-5.infl-given.t01
skill: calc1.shape.inflection-points
uses: alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 2
answer-type: set
vars: a = int(-4, -1); b = int(0, 2); c = int(3, 6)
let: g = (x - a)*(x - b)^2*(x - c)
answer: a, c
wrong: a, b, c => The factor \([[tex((x - b)^2)]]\) is never negative, so the second derivative does not change sign at \(x = [[b]]\) and the concavity does not change there. @2; c => The second derivative also changes sign at \(x = [[a]]\), from positive to negative. @2

### Question
A function \(f\) has \(f''(x) = [[tex(g)]]\) for all real \(x\). Find all \(x\)-values at which the graph of \(f\) has an inflection point.

### Solution
0. [calc1.shape.inflection-points] Set up: the second derivative is given in factored form. Its zeros are the candidates, and an inflection point needs a sign change of the second derivative.
1. [alg.solve.polynomial] Zero-product rule: \(f''(x) = 0\) at \(x = [[a]]\), \(x = [[b]]\) and \(x = [[c]]\).
   check: solve(g, x) = {a, b, c}
2. [alg.inequality.sign-chart] Sign chart: \(f''([[a - 1]]) = [[(b - a + 1)^2*(c - a + 1)]]\), \(f''\left([[tex(b - 1/2)]]\right) = [[tex(-(1/4)*(b - a - 1/2)*(c - b + 1/2))]]\), \(f''\left([[tex(b + 1/2)]]\right) = [[tex(-(1/4)*(b - a + 1/2)*(c - b - 1/2))]]\) and \(f''([[c + 1]]) = [[(c - a + 1)*(c - b + 1)^2]]\). So \(f''\) is positive, negative, negative, positive.
   check: subs(g, x, a - 1) = (b - a + 1)^2*(c - a + 1)
   check: subs(g, x, b - 1/2) = -(1/4)*(b - a - 1/2)*(c - b + 1/2)
   check: subs(g, x, b + 1/2) = -(1/4)*(b - a + 1/2)*(c - b - 1/2)
   check: subs(g, x, c + 1) = (c - a + 1)*(c - b + 1)^2
3. [calc1.shape.inflection-points] Decide: the sign changes at \(x = [[a]]\) and at \(x = [[c]]\) but not at \(x = [[b]]\), where it is negative on both sides. So the inflection points are at \(x = [[a]]\) and \(x = [[c]]\).
   check: {a, c} = {a, c}

<!-- tier 2: product with an exponential -->
## Card calc1.4-5.infl-xexp.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.exponential, calc1.deriv.product-rule, alg.solve.linear, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 2
answer-type: point
answer: (-2, -2*e^(-2))
wrong: (-1, -1/e) => The number \(-1\) is where \(f'\) is zero. Inflection points come from the second derivative, which is zero at \(x = -2\). @4

### Question
Find the inflection point of the graph of \(f(x) = xe^{x}\), as a point \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the second derivative changes sign. Differentiate twice, find the zero of the second derivative, check the sign change, and find the height of the graph there.
1. [calc1.deriv.exponential] Differentiate the exponential: \((e^x)' = e^x\).
   check: diff(e^x, x) = e^x
2. [calc1.deriv.product-rule] Product rule, twice: \(f'(x) = e^x + xe^x = (x + 1)e^x\) and \(f''(x) = e^x + (x + 1)e^x = (x + 2)e^x\).
   check: diff(x*e^x, x) = (x + 1)*e^x
   check: diff(x*e^x, x, 2) = (x + 2)*e^x
3. [alg.solve.linear] Solve \(f''(x) = 0\): \(e^x\) is never zero, so \(x + 2 = 0\) and \(x = -2\).
   check: solve((x + 2)*e^x, x) = {-2}
4. [alg.inequality.sign-chart] Sign chart: \(f''(-3) = -e^{-3}\) and \(f''(0) = 2\), so \(f''\) changes from negative to positive at \(x = -2\).
   check: subs((x + 2)*e^x, x, -3) = -e^(-3)
   check: subs((x + 2)*e^x, x, 0) = 2
5. [alg.arith.exact-evaluation] Evaluate: \(f(-2) = -2e^{-2}\).
   check: subs(x*e^x, x, -2) = -2*e^(-2)
6. [calc1.shape.inflection-points] Conclude: the concavity changes at \(x = -2\), so the inflection point is \(\left(-2, -\frac{2}{e^{2}}\right)\).

<!-- tier 2: trig on an interval -->
## Card calc1.4-5.infl-trig.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.trig-sin-cos, trig.equations.solve, alg.inequality.sign-chart, trig.values.exact
difficulty: 2
answer-type: point
answer: (pi/2, 3*pi/2), (3*pi/2, 9*pi/2)
wrong: (pi/2, 3*pi/2) => The second derivative also changes sign at \(x = \frac{3\pi}{2}\), from positive to negative. @5; (pi, 3*pi - 4) => Check the derivatives: \((\cos x)' = -\sin x\) and \((-\sin x)' = -\cos x\), so \(f''(x) = -4\cos x\). @1

### Question
Find all inflection points of the graph of \(f(x) = 3x + 4\cos x\) on the interval \((0, 2\pi)\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the second derivative changes sign. Find the zeros of the second derivative in the interval, check the sign on each side, and find the height of the graph at each.
1. [calc1.deriv.trig-sin-cos] Differentiate twice: \(f'(x) = 3 - 4\sin x\) and \(f''(x) = -4\cos x\).
   check: diff(3*x + 4*cos(x), x) = 3 - 4*sin(x)
   check: diff(3*x + 4*cos(x), x, 2) = -4*cos(x)
2. [trig.equations.solve] Solve \(f''(x) = 0\): \(\cos x = 0\), so \(x = \frac{\pi}{2}\) or \(x = \frac{3\pi}{2}\) in \((0, 2\pi)\).
   check: subs(-4*cos(x), x, pi/2) = 0
   check: subs(-4*cos(x), x, 3*pi/2) = 0
3. [alg.inequality.sign-chart] Sign chart: \(f''\left(\frac{\pi}{3}\right) = -2\), \(f''(\pi) = 4\) and \(f''\left(\frac{5\pi}{3}\right) = -2\). So \(f''\) is negative, positive, negative, and it changes sign at both zeros.
   check: subs(-4*cos(x), x, pi/3) = -2
   check: subs(-4*cos(x), x, pi) = 4
   check: subs(-4*cos(x), x, 5*pi/3) = -2
4. [trig.values.exact] Evaluate with exact values: \(f\left(\frac{\pi}{2}\right) = \frac{3\pi}{2}\) and \(f\left(\frac{3\pi}{2}\right) = \frac{9\pi}{2}\).
   check: subs(3*x + 4*cos(x), x, pi/2) = 3*pi/2
   check: subs(3*x + 4*cos(x), x, 3*pi/2) = 9*pi/2
5. [calc1.shape.inflection-points] Conclude: the concavity changes at both zeros, so the inflection points are \(\left(\frac{\pi}{2}, \frac{3\pi}{2}\right), \left(\frac{3\pi}{2}, \frac{9\pi}{2}\right)\).


<!-- tier 3, template: a rational function with three inflection points -->
## Card calc1.4-5.infl-rational.t01
skill: calc1.shape.inflection-points
uses: calc1.deriv.quotient-rule, alg.factor.lowest-power, alg.solve.polynomial, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
vars: k = int(1, 8)
let: f = x/(x^2 + k^2)
answer: (-sqrt(3)*k, -sqrt(3)/(4*k)), (0, 0), (sqrt(3)*k, sqrt(3)/(4*k))
wrong: (-k, -1/(2*k)), (k, 1/(2*k)) => The values \(x = \pm [[k]]\) make the first derivative zero, so they are the critical numbers. Inflection points come from the zeros of the second derivative. @3; (-sqrt(3)*k, -sqrt(3)/(4*k)), (sqrt(3)*k, sqrt(3)/(4*k)) => The numerator \(2x(x^2 - [[3*k^2]])\) is also zero at \(x = 0\), and the second derivative changes sign there, from positive to negative. @4

### Question
Find all inflection points of the graph of \(f(x) = [[tex(f)]]\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the second derivative changes sign. Differentiate twice, find the zeros of the second derivative, check the sign on each side of each, and find the height of the graph at each.
1. [calc1.deriv.quotient-rule] Differentiate with the quotient rule, twice: \(f'(x) = \frac{[[k^2]] - x^2}{(x^2 + [[k^2]])^2}\) and \(f''(x) = \frac{-2x(x^2 + [[k^2]])^2 - ([[k^2]] - x^2) \cdot 2(x^2 + [[k^2]]) \cdot 2x}{(x^2 + [[k^2]])^4}\).
   check: diff(f, x) = (k^2 - x^2)/(x^2 + k^2)^2
   check: diff((k^2 - x^2)/(x^2 + k^2)^2, x) = (-2*x*(x^2 + k^2)^2 - (k^2 - x^2)*2*(x^2 + k^2)*2*x)/(x^2 + k^2)^4
2. [alg.factor.lowest-power] Factor out \(x^2 + [[k^2]]\) from the numerator and cancel it against the denominator: \(f''(x) = \frac{2x(x^2 - [[3*k^2]])}{(x^2 + [[k^2]])^3}\).
   check: (-2*x*(x^2 + k^2)^2 - (k^2 - x^2)*2*(x^2 + k^2)*2*x)/(x^2 + k^2)^4 = 2*x*(x^2 - 3*k^2)/(x^2 + k^2)^3
3. [alg.solve.polynomial] Solve \(f''(x) = 0\): the denominator is never zero, so \(2x(x^2 - [[3*k^2]]) = 0\). The zeros are \(x = 0\) and \(x = \pm [[tex(sqrt(3)*k)]]\).
   check: solve(2*x*(x^2 - 3*k^2), x) = {-sqrt(3)*k, 0, sqrt(3)*k}
4. [alg.inequality.sign-chart] Sign chart: the denominator is positive, so \(f''\) has the sign of the numerator \(N(x) = 2x(x^2 - [[3*k^2]])\). Test points: \(N([[-2*k]]) = [[-4*k^3]]\), \(N([[-k]]) = [[4*k^3]]\), \(N([[k]]) = [[-4*k^3]]\) and \(N([[2*k]]) = [[4*k^3]]\). So \(f''\) is negative, positive, negative, positive, and it changes sign at all three zeros.
   check: subs(2*x*(x^2 - 3*k^2), x, -2*k) = -4*k^3
   check: subs(2*x*(x^2 - 3*k^2), x, -k) = 4*k^3
   check: subs(2*x*(x^2 - 3*k^2), x, k) = -4*k^3
   check: subs(2*x*(x^2 - 3*k^2), x, 2*k) = 4*k^3
5. [alg.arith.exact-evaluation] Evaluate: at \(x = \pm [[tex(sqrt(3)*k)]]\) the denominator is \([[3*k^2]] + [[k^2]] = [[4*k^2]]\), so \(f\left(\pm [[tex(sqrt(3)*k)]]\right) = \pm [[tex(sqrt(3)/(4*k))]]\), and \(f(0) = 0\).
   check: subs(f, x, sqrt(3)*k) = sqrt(3)/(4*k)
   check: subs(f, x, -sqrt(3)*k) = -sqrt(3)/(4*k)
   check: subs(f, x, 0) = 0
6. [calc1.shape.inflection-points] Conclude: the sign of \(f''\) changes at each of its three zeros, so the inflection points are \(\left(-[[tex(sqrt(3)*k)]], -[[tex(sqrt(3)/(4*k))]]\right), (0, 0), \left([[tex(sqrt(3)*k)]], [[tex(sqrt(3)/(4*k))]]\right)\).

<!-- tier 3: f'' fails to exist at a point where f is defined -->
## Card calc1.4-5.infl-cbrt.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule-rational, alg.factor.lowest-power, alg.solve.linear, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
answer: (-1, -6)
wrong: (-1, -6), (0, 0) => The second derivative does not exist at \(x = 0\), but it is positive on both sides of \(0\). The concavity does not change there, so there is no inflection point at \(x = 0\). @5; (2, -3*2^(2/3)) => The value \(x = 2\) makes the first derivative zero. Inflection points come from the second derivative, which is zero at \(x = -1\). @3

### Question
Find all inflection points of the graph of \(f(x) = x^{5/3} - 5x^{2/3}\), as points \((x, f(x))\). Here \(x^{1/3}\) is the real cube root, so \(f\) is defined for every real number.

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point is where the concavity changes at a point where the function is defined. The second derivative may be zero or may fail to exist there, so look for both, and check the sign on each side.
1. [calc1.deriv.power-rule-rational] Differentiate twice: \(f'(x) = \frac{5}{3}x^{2/3} - \frac{10}{3}x^{-1/3}\) and \(f''(x) = \frac{10}{9}x^{-1/3} + \frac{10}{9}x^{-4/3}\).
   check: diff(u^5 - 5*u^2, u)/diff(u^3, u) = 5/3*u^2 - 10/3/u
   check: diff(5/3*u^2 - 10/3/u, u)/diff(u^3, u) = 10/9/u + 10/9/u^4
2. [alg.factor.lowest-power] Factor out the lowest power: \(f''(x) = \frac{10}{9}x^{-4/3}(x + 1) = \frac{10(x + 1)}{9x^{4/3}}\).
   check: 10/9*u^(-4)*(u^3 + 1) = 10/9/u + 10/9/u^4
3. [alg.solve.linear] Zero of \(f''\): the numerator is zero when \(x + 1 = 0\), so \(x = -1\).
   check: solve(x + 1, x) = {-1}
4. [calc1.shape.inflection-points] Candidates: \(f''\) is zero at \(x = -1\) and does not exist at \(x = 0\). Since \(f(0) = 0\) is defined, \(x = 0\) is a candidate too.
   check: subs(u^5 - 5*u^2, u, 0) = 0
5. [alg.inequality.sign-chart] Sign chart: \(x^{4/3} > 0\) for \(x \ne 0\), so \(f''\) has the sign of \(x + 1\). Test points: \(f''(-8) = -\frac{35}{72}\), \(f''\left(-\frac{1}{8}\right) = \frac{140}{9}\) and \(f''(8) = \frac{5}{8}\). So \(f''\) is negative, positive, positive.
   check: subs(10*(u^3 + 1)/(9*u^4), u, -2) = -35/72
   check: subs(10*(u^3 + 1)/(9*u^4), u, -1/2) = 140/9
   check: subs(10*(u^3 + 1)/(9*u^4), u, 2) = 5/8
6. [alg.arith.exact-evaluation] Evaluate: \(f(-1) = (-1)^{5/3} - 5(-1)^{2/3} = -1 - 5 = -6\).
   check: subs(u^5 - 5*u^2, u, -1) = -6
7. [calc1.shape.inflection-points] Conclude: at \(x = -1\) the second derivative changes from negative to positive, so there is an inflection point. At \(x = 0\) it is positive on both sides, so there is none. The only inflection point is \((-1, -6)\).

<!-- tier 3: logarithm on a restricted domain -->
## Card calc1.4-5.infl-log.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.logarithm, calc1.deriv.product-rule, alg.logs.solve-equations, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
answer: (e^(-3/2), -3/2*e^(-3))
wrong: (e^(-1/2), -1/(2*e)) => The value \(x = e^{-1/2}\) makes the first derivative zero. Inflection points come from the second derivative, \(f''(x) = 2\ln x + 3\). @3; (e^(3/2), 3/2*e^3) => Solving \(2\ln x + 3 = 0\) gives \(\ln x = -\frac{3}{2}\), with a minus sign. @3

### Question
Find the inflection point of the graph of \(f(x) = x^2 \ln x\), as a point \((x, f(x))\).

### Solution
0. [calc1.shape.inflection-points] Set up: the function is defined only for positive inputs. An inflection point is where the second derivative changes sign, so differentiate twice, solve for the zero of the second derivative, check the sign on each side, and find the height of the graph there.
1. [calc1.deriv.logarithm] Differentiate the logarithm: \((\ln x)' = \frac{1}{x}\) for \(x > 0\).
   check: diff(ln(x), x) = 1/x
2. [calc1.deriv.product-rule] Product rule, twice: \(f'(x) = 2x\ln x + x\) and \(f''(x) = 2\ln x + 2 + 1 = 2\ln x + 3\).
   check: diff(x^2*ln(x), x) = 2*x*ln(x) + x
   check: diff(x^2*ln(x), x, 2) = 2*ln(x) + 3
3. [alg.logs.solve-equations] Solve \(f''(x) = 0\): \(2\ln x = -3\), so \(\ln x = -\frac{3}{2}\) and \(x = e^{-3/2}\).
   check: solve(2*ln(x) + 3, x) = {exp(-3/2)}
4. [alg.inequality.sign-chart] Sign chart on \(x > 0\): \(f''\left(e^{-2}\right) = -1\) and \(f''(1) = 3\). So \(f''\) changes from negative to positive at \(x = e^{-3/2}\).
   check: subs(2*ln(x) + 3, x, exp(-2)) = -1
   check: subs(2*ln(x) + 3, x, 1) = 3
5. [alg.arith.exact-evaluation] Evaluate: \(f\left(e^{-3/2}\right) = e^{-3} \cdot \left(-\frac{3}{2}\right) = -\frac{3}{2}e^{-3}\).
   check: subs(x^2*ln(x), x, exp(-3/2)) = -3/2*exp(-3)
6. [calc1.shape.inflection-points] Conclude: the concavity changes at \(x = e^{-3/2}\), so the inflection point is \(\left(e^{-3/2}, -\frac{3}{2}e^{-3}\right)\).

<!-- tier 4, template: the logistic curve grows fastest at its inflection point -->
## Card calc1.4-5.infl-logistic.t01
skill: calc1.shape.inflection-points
uses: calc1.deriv.chain-linear-inside, calc1.deriv.quotient-rule, alg.logs.solve-equations, alg.inequality.sign-chart, alg.arith.exact-evaluation
difficulty: 4
vars: c = int(3, 12); A = int(3, 9); m = int(2, 4)
let: L = 100*c

### Question
The number of fish in a lake \(t\) years after it is stocked is \(P(t) = \frac{[[L]]}{1 + [[A]]e^{-t/[[m]]}}\). The population grows fastest at the moment when its growth rate \(P'(t)\) is largest.

### Part a
answer-type: number
answer: m*ln(A)
wrong: ln(A)/m => Solving \(-\frac{t}{[[m]]} = -\ln [[A]]\) for \(t\) means multiplying both sides by \([[m]]\), so \(t = [[m]]\ln [[A]]\), not \(\frac{\ln [[A]]}{[[m]]}\). @3
Find the time, in years, at which the population is growing fastest.

### Part b
answer-type: number
answer: L/2
wrong: L/(4*m) => That number is the largest growth rate \(P'\), in fish per year. The question asks for the population \(P\), the number of fish. @5; L => The number \([[L]]\) is the limit of \(P\) as \(t\) grows. At the inflection point the denominator is \(1 + 1 = 2\), so \(P\) is half of it. @6
Find the number of fish in the lake at that time.

### Solution
0. [calc1.shape.inflection-points] Set up: the growth rate is the derivative of the population. It is largest where the derivative stops increasing and starts decreasing, which is where the second derivative changes sign from positive to negative: an inflection point of the population curve. Differentiate twice, find that point, and evaluate the population there.
1. [calc1.deriv.chain-linear-inside] Differentiate the exponential: \(\frac{d}{dt}e^{-t/[[m]]} = -\frac{1}{[[m]]}e^{-t/[[m]]}\).
   check: diff(exp(-t/m), t) = -exp(-t/m)/m
2. [calc1.deriv.quotient-rule] Differentiate twice with the quotient rule: \(P'(t) = [[tex(L*A/m)]] \cdot \frac{e^{-t/[[m]]}}{\left(1 + [[A]]e^{-t/[[m]]}\right)^2}\) and \(P''(t) = [[tex(L*A/m^2)]] \cdot \frac{e^{-t/[[m]]}\left([[A]]e^{-t/[[m]]} - 1\right)}{\left(1 + [[A]]e^{-t/[[m]]}\right)^3}\).
   check: diff(L/(1 + A*exp(-t/m)), t) = (L*A/m)*exp(-t/m)/(1 + A*exp(-t/m))^2
   check: diff((L*A/m)*exp(-t/m)/(1 + A*exp(-t/m))^2, t) = (L*A/m^2)*exp(-t/m)*(A*exp(-t/m) - 1)/(1 + A*exp(-t/m))^3
3. [alg.logs.solve-equations] Solve \(P''(t) = 0\): the exponential and the denominator are positive, so \([[A]]e^{-t/[[m]]} = 1\). Then \(e^{-t/[[m]]} = \frac{1}{[[A]]}\), so \(-\frac{t}{[[m]]} = -\ln [[A]]\) and \(t = [[m]]\ln [[A]]\).
   check: solve(A*exp(-t/m) - 1, t) = {m*ln(A)}
4. [alg.inequality.sign-chart] Sign chart: \(P''\) has the sign of \([[A]]e^{-t/[[m]]} - 1\). At \(t = 0\) this is \([[A - 1]]\), which is positive. At \(t = [[2*m]]\ln [[A]]\) it is \([[tex(1/A - 1)]]\), which is negative. So \(P''\) changes from positive to negative at \(t = [[m]]\ln [[A]]\).
   check: subs(A*exp(-t/m) - 1, t, 0) = A - 1
   check: subs(A*exp(-t/m) - 1, t, 2*m*ln(A)) = 1/A - 1
5. [calc1.shape.inflection-points] Decide: \(P'\) increases while \(P'' > 0\) and decreases while \(P'' < 0\), so the growth rate is largest at the inflection point \(t = [[m]]\ln [[A]]\) years. The largest growth rate is \(P'\left([[m]]\ln [[A]]\right) = [[tex(L/(4*m))]]\) fish per year.
   check: subs((L*A/m)*exp(-t/m)/(1 + A*exp(-t/m))^2, t, m*ln(A)) = L/(4*m)
6. [alg.arith.exact-evaluation] Evaluate: at \(t = [[m]]\ln [[A]]\) we have \(e^{-t/[[m]]} = \frac{1}{[[A]]}\), so \(P = \frac{[[L]]}{1 + [[A]] \cdot \frac{1}{[[A]]}} = \frac{[[L]]}{2} = [[L/2]]\) fish.
   check: subs(L/(1 + A*exp(-t/m)), t, m*ln(A)) = L/2

<!-- tier 4: a family of curves, with a repeated zero and a degenerate member -->
## Card calc1.4-5.infl-param.001
skill: calc1.shape.inflection-points
uses: calc1.deriv.power-rule, alg.solve.quadratic-formula
difficulty: 4
answer-type: interval
vars: c
answer: (-inf, 0) U (0, 1)
wrong: (-inf, 1) => When \(c = 0\) the second derivative is linear, \(12(2x + 1)\), with only one zero, so the graph has just one inflection point. @4; (-inf, 0) U (0, 1] => When \(c = 1\) the second derivative is \(12(x + 1)^2\). It is zero at \(x = -1\) but never negative, so it does not change sign and there is no inflection point. @3; (1, inf) => The quadratic has two distinct zeros when its discriminant \(4 - 4c\) is positive, which means \(c < 1\). @2

### Question
For which values of the constant \(c\) does the graph of \(f(x) = cx^4 + 4x^3 + 6x^2\) have exactly two inflection points?

### Solution
0. [calc1.shape.inflection-points] Set up: an inflection point needs a sign change of the second derivative. The second derivative depends on the constant, so count its sign changes for each value of the constant, and look closely at the special values.
1. [calc1.deriv.power-rule] Differentiate twice: \(f''(x) = 12cx^2 + 24x + 12 = 12(cx^2 + 2x + 1)\).
   check: diff(c*x^4 + 4*x^3 + 6*x^2, x, 2) = 12*(c*x^2 + 2*x + 1)
2. [alg.solve.quadratic-formula] Discriminant: for \(c \ne 0\), the quadratic \(cx^2 + 2x + 1\) has discriminant \(2^2 - 4c = 4 - 4c\). It has two distinct real zeros exactly when \(4 - 4c > 0\), that is, when \(c < 1\).
   check: 2^2 - 4*c*1 = 4 - 4*c
   check: solve(4 - 4*c > 0, c) = solve(c < 1, c)
3. [calc1.shape.inflection-points] Repeated zero: at \(c = 1\) the second derivative is \(12(x + 1)^2\), which is zero at \(x = -1\) but never negative. It does not change sign, so there is no inflection point. For \(c > 1\) there are no zeros at all.
   check: subs(12*(c*x^2 + 2*x + 1), c, 1) = 12*(x + 1)^2
4. [calc1.shape.inflection-points] Degenerate case: at \(c = 0\) the second derivative is \(12(2x + 1)\), a linear function with one zero at \(x = -\frac{1}{2}\), where it changes sign. That gives one inflection point, not two.
   check: subs(12*(c*x^2 + 2*x + 1), c, 0) = 12*(2*x + 1)
   check: solve(12*(2*x + 1), x) = {-1/2}
5. [calc1.shape.inflection-points] Conclude: two inflection points need \(c < 1\) and \(c \ne 0\), so the values are \((-\infty, 0) \cup (0, 1)\).



<!-- ===================================================================== -->
<!-- calc1.shape.second-derivative-test                                    -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.sdt-example.001
kind: example
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.arith.exact-evaluation

### Question
Use the second derivative test to find and classify the local extrema of \(f(x) = 2x^3 - 3x^2 - 12x + 4\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers, where the derivative is zero. At each one the sign of the second derivative decides: positive means a local minimum, negative means a local maximum, and zero means the test gives no information.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = 6x^2 - 6x - 12\) and \(f''(x) = 12x - 6\).
   check: diff(2*x^3 - 3*x^2 - 12*x + 4, x) = 6*x^2 - 6*x - 12
   check: diff(2*x^3 - 3*x^2 - 12*x + 4, x, 2) = 12*x - 6
2. [alg.factor.polynomials] Factor: \(f'(x) = 6(x - 2)(x + 1)\).
   check: expand(6*(x - 2)*(x + 1)) = 6*x^2 - 6*x - 12
3. [alg.solve.polynomial] Critical numbers: \(f'(x) = 0\) at \(x = -1\) and \(x = 2\). The derivative exists everywhere, so there are no others.
   check: solve(6*(x - 2)*(x + 1), x) = {-1, 2}
4. [calc1.shape.second-derivative-test] Test: \(f''(-1) = -18 < 0\), so \(f\) has a local maximum at \(x = -1\). \(f''(2) = 18 > 0\), so \(f\) has a local minimum at \(x = 2\).
   check: subs(12*x - 6, x, -1) = -18
   check: subs(12*x - 6, x, 2) = 18
5. [alg.arith.exact-evaluation] Evaluate: \(f(-1) = -2 - 3 + 12 + 4 = 11\) and \(f(2) = 16 - 12 - 24 + 4 = -16\). So the local maximum point is \((-1, 11)\) and the local minimum point is \((2, -16)\).
   check: subs(2*x^3 - 3*x^2 - 12*x + 4, x, -1) = 11
   check: subs(2*x^3 - 3*x^2 - 12*x + 4, x, 2) = -16

<!-- tier 1: what the sign of f'' says -->
## Card calc1.4-5.sdt-concept.001
skill: calc1.shape.second-derivative-test
cue: required
difficulty: 1
answer-type: choice

### Question
A function \(f\) has \(f'(3) = 0\) and \(f''(3) = -4\). What does the second derivative test say about \(f\) at \(x = 3\)?

### Choices
- [x] \(f\) has a local maximum at \(x = 3\)
- [ ] \(f\) has a local minimum at \(x = 3\)
- [ ] \(f\) has an inflection point at \(x = 3\)
- [ ] The test is inconclusive

### Solution
0. [calc1.shape.second-derivative-test] Set up: at a number where the first derivative is zero, the sign of the second derivative decides. Positive means concave up, a local minimum. Negative means concave down, a local maximum. Zero means the test gives no information.
1. [calc1.shape.second-derivative-test] Decide: the second derivative at this number is negative, so the graph is concave down there and the function has a local maximum.

<!-- tier 1, template: read the signs from a table -->
## Card calc1.4-5.sdt-table.t01
skill: calc1.shape.second-derivative-test
cue: required
difficulty: 1
answer-type: number
vars: a = int(-4, 0); g = int(2, 4); h = int(2, 4); s = int(-1, 1, not 0); u = int(1, 5); v = int(1, 5)
let: b = a + g; c = b + h; w = (a + b)/2 + s*(b - a)/2
answer: w
wrong: (a + b)/2 - s*(b - a)/2 => A positive second derivative means the graph is concave up, which gives a local minimum, not a maximum. @1; c => The second derivative is zero at \(x = [[c]]\), so the test gives no information there. @1

### Question
A function \(f\) has \(f'(x) = 0\) at \(x = [[a]]\), \(x = [[b]]\) and \(x = [[c]]\). Its second derivative has \(f''([[a]]) = [[s*u]]\), \(f''([[b]]) = [[-s*v]]\) and \(f''([[c]]) = 0\). At which of these three values of \(x\) does the second derivative test show a local maximum?

### Solution
0. [calc1.shape.second-derivative-test] Set up: at a critical number, a negative second derivative means a local maximum, a positive one means a local minimum, and zero means the test gives no information.
1. [calc1.shape.second-derivative-test] Read the table: \(f''([[a]]) = [[s*u]]\), \(f''([[b]]) = [[-s*v]]\) and \(f''([[c]]) = 0\). The second derivative is negative only at \(x = [[w]]\), so the test shows a local maximum there. It is positive at the other number with a nonzero value, a local minimum, and the test says nothing at \(x = [[c]]\).
   check: w = (a + b)/2 + s*(b - a)/2

<!-- tier 1: f'' = 0 does not mean no extremum -->
## Card calc1.4-5.sdt-inconclusive.001
skill: calc1.shape.second-derivative-test
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: truefalse
answer: false

### Question
True or false: if \(f'(c) = 0\) and \(f''(c) = 0\), then \(f\) has neither a local maximum nor a local minimum at \(x = c\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: when the second derivative is zero at a critical number, the second derivative test gives no information. That is different from saying there is no extremum, so look for a counterexample.
1. [calc1.deriv.power-rule] Counterexample: take \(f(x) = x^4\), so \(f'(x) = 4x^3\) and \(f''(x) = 12x^2\). Both are zero at \(x = 0\).
   check: diff(x^4, x) = 4*x^3
   check: diff(x^4, x, 2) = 12*x^2
   check: subs(4*x^3, x, 0) = 0
   check: subs(12*x^2, x, 0) = 0
2. [calc1.shape.second-derivative-test] Decide: \(f(x) = x^4 \ge 0 = f(0)\) for every \(x\), so \(f\) has a local minimum at \(x = 0\) even though the test is silent. The statement is false.
   check: subs(x^4, x, 0) = 0

<!-- tier 2, template: a cubic with a maximum and a minimum -->
## Card calc1.4-5.sdt-cubic.t01
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, alg.arith.exact-evaluation
difficulty: 2
vars: p = int(1, 4); c = int(-5, 5)
let: f = x^3 + 3*p*x^2 + c

### Question
Use the second derivative test to classify the critical numbers of \(f(x) = [[tex(f)]]\).

### Part a
answer-type: point
answer: (-2*p, 4*p^3 + c)
wrong: (0, c) => At \(x = 0\) the second derivative is \([[6*p]]\), which is positive, so the graph is concave up and that point is the local minimum. @4
Find the local maximum point \((x, f(x))\).

### Part b
answer-type: point
answer: (0, c)
wrong: (-2*p, 4*p^3 + c) => At \(x = [[-2*p]]\) the second derivative is \([[-6*p]]\), which is negative, so the graph is concave down and that point is the local maximum. @4
Find the local minimum point \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers, where the derivative is zero. At each one the sign of the second derivative decides: negative means a local maximum and positive means a local minimum.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = [[tex(diff(f, x))]]\) and \(f''(x) = [[tex(diff(f, x, 2))]]\).
   check: diff(f, x) = 3*x^2 + 6*p*x
   check: diff(f, x, 2) = 6*x + 6*p
2. [alg.factor.polynomials] Factor: \(f'(x) = 3x(x + [[2*p]])\).
   check: expand(3*x*(x + 2*p)) = 3*x^2 + 6*p*x
3. [alg.solve.polynomial] Critical numbers: \(f'(x) = 0\) at \(x = 0\) and \(x = [[-2*p]]\).
   check: solve(3*x*(x + 2*p), x) = {-2*p, 0}
4. [calc1.shape.second-derivative-test] Test: \(f''(0) = [[6*p]] > 0\), so there is a local minimum at \(x = 0\). \(f''([[-2*p]]) = [[-6*p]] < 0\), so there is a local maximum at \(x = [[-2*p]]\).
   check: subs(6*x + 6*p, x, 0) = 6*p
   check: subs(6*x + 6*p, x, -2*p) = -6*p
5. [alg.arith.exact-evaluation] Evaluate: the local maximum value is \(f([[-2*p]]) = [[4*p^3 + c]]\) and the local minimum value is \(f(0) = [[c]]\).
   check: subs(f, x, -2*p) = 4*p^3 + c
   check: subs(f, x, 0) = c

<!-- tier 2: a reciprocal, with a maximum below the minimum -->
## Card calc1.4-5.sdt-reciprocal.001
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.power-rule-rational, alg.solve.rational-equation, alg.arith.exact-evaluation
difficulty: 2
answer-type: number
answer: -4
wrong: 4 => The value \(4\) is the local minimum value, at \(x = 2\), where the second derivative is positive. The local maximum is at \(x = -2\), where the second derivative is negative. @3

### Question
The function \(f(x) = x + \dfrac{4}{x}\) is defined for \(x \ne 0\). Use the second derivative test to find its local maximum value.

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers, where the derivative is zero or does not exist in the domain. At each one the sign of the second derivative decides: negative means a local maximum.
1. [calc1.deriv.power-rule-rational] Differentiate twice: \(f'(x) = 1 - 4x^{-2}\) and \(f''(x) = 8x^{-3}\).
   check: diff(x + 4/x, x) = 1 - 4/x^2
   check: diff(x + 4/x, x, 2) = 8/x^3
2. [alg.solve.rational-equation] Solve \(f'(x) = 0\): multiply by \(x^2\) (note \(x \ne 0\)) to get \(x^2 = 4\), so \(x = \pm 2\). The derivative fails to exist only at \(x = 0\), which is not in the domain.
   check: solve(1 - 4/x^2, x) = {-2, 2}
3. [calc1.shape.second-derivative-test] Test: \(f''(-2) = -1 < 0\), so there is a local maximum at \(x = -2\). \(f''(2) = 1 > 0\), so there is a local minimum at \(x = 2\).
   check: subs(8/x^3, x, -2) = -1
   check: subs(8/x^3, x, 2) = 1
4. [alg.arith.exact-evaluation] Evaluate: the local maximum value is \(f(-2) = -2 - 2 = -4\).
   check: subs(x + 4/x, x, -2) = -4

<!-- tier 2: product with an exponential -->
## Card calc1.4-5.sdt-exp.001
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.exponential, calc1.deriv.product-rule, alg.factor.polynomials, alg.solve.polynomial, alg.arith.exact-evaluation
difficulty: 2

### Question
Use the second derivative test to classify the critical numbers of \(f(x) = (x^2 - 3)e^{x}\).

### Part a
answer-type: point
answer: (-3, 6*e^(-3))
wrong: (1, -2*e) => At \(x = 1\) the second derivative is \(4e\), which is positive, so the graph is concave up and that point is the local minimum. @5
Find the local maximum point \((x, f(x))\).

### Part b
answer-type: point
answer: (1, -2*e)
wrong: (-3, 6*e^(-3)) => At \(x = -3\) the second derivative is \(-4e^{-3}\), which is negative, so the graph is concave down and that point is the local maximum. @5
Find the local minimum point \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers, where the derivative is zero. At each one the sign of the second derivative decides: negative means a local maximum and positive means a local minimum.
1. [calc1.deriv.exponential] Differentiate the exponential: \((e^x)' = e^x\).
   check: diff(e^x, x) = e^x
2. [calc1.deriv.product-rule] Product rule, twice: \(f'(x) = 2xe^x + (x^2 - 3)e^x = (x^2 + 2x - 3)e^x\) and \(f''(x) = (2x + 2)e^x + (x^2 + 2x - 3)e^x = (x^2 + 4x - 1)e^x\).
   check: diff((x^2 - 3)*e^x, x) = (x^2 + 2*x - 3)*e^x
   check: diff((x^2 + 2*x - 3)*e^x, x) = (x^2 + 4*x - 1)*e^x
3. [alg.factor.polynomials] Factor: \(f'(x) = (x + 3)(x - 1)e^x\).
   check: expand((x + 3)*(x - 1)) = x^2 + 2*x - 3
4. [alg.solve.polynomial] Critical numbers: \(e^x\) is never zero, so \(f'(x) = 0\) at \(x = -3\) and \(x = 1\).
   check: solve((x + 3)*(x - 1), x) = {-3, 1}
5. [calc1.shape.second-derivative-test] Test: \(f''(-3) = -4e^{-3} < 0\), so there is a local maximum at \(x = -3\). \(f''(1) = 4e > 0\), so there is a local minimum at \(x = 1\).
   check: subs((x^2 + 4*x - 1)*e^x, x, -3) = -4*e^(-3)
   check: subs((x^2 + 4*x - 1)*e^x, x, 1) = 4*e
6. [alg.arith.exact-evaluation] Evaluate: the local maximum point is \(\left(-3, f(-3)\right) = \left(-3, 6e^{-3}\right)\) and the local minimum point is \(\left(1, f(1)\right) = (1, -2e)\).
   check: subs((x^2 - 3)*e^x, x, -3) = 6*e^(-3)
   check: subs((x^2 - 3)*e^x, x, 1) = -2*e

<!-- tier 2: trigonometric function on an interval -->
## Card calc1.4-5.sdt-trig.001
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.trig-sin-cos, trig.equations.solve, trig.values.exact
difficulty: 2

### Question
Use the second derivative test to classify the critical numbers of \(f(x) = \sin x + \cos x\) on the interval \((0, 2\pi)\).

### Part a
answer-type: point
answer: (pi/4, sqrt(2))
wrong: (5*pi/4, -sqrt(2)) => At \(x = \frac{5\pi}{4}\) the second derivative is \(\sqrt{2}\), which is positive, so the graph is concave up and that point is the local minimum. @3
Find the local maximum point \((x, f(x))\).

### Part b
answer-type: point
answer: (5*pi/4, -sqrt(2))
wrong: (pi/4, sqrt(2)) => At \(x = \frac{\pi}{4}\) the second derivative is \(-\sqrt{2}\), which is negative, so the graph is concave down and that point is the local maximum. @3
Find the local minimum point \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers in the interval, where the derivative is zero. At each one the sign of the second derivative decides: negative means a local maximum and positive means a local minimum.
1. [calc1.deriv.trig-sin-cos] Differentiate twice: \(f'(x) = \cos x - \sin x\) and \(f''(x) = -\sin x - \cos x\).
   check: diff(sin(x) + cos(x), x) = cos(x) - sin(x)
   check: diff(sin(x) + cos(x), x, 2) = -sin(x) - cos(x)
2. [trig.equations.solve] Solve \(f'(x) = 0\): \(\cos x = \sin x\), so \(\tan x = 1\) and \(x = \frac{\pi}{4}\) or \(x = \frac{5\pi}{4}\) in \((0, 2\pi)\).
   check: subs(cos(x) - sin(x), x, pi/4) = 0
   check: subs(cos(x) - sin(x), x, 5*pi/4) = 0
3. [calc1.shape.second-derivative-test] Test: \(f''\left(\frac{\pi}{4}\right) = -\sqrt{2} < 0\), so there is a local maximum at \(x = \frac{\pi}{4}\). \(f''\left(\frac{5\pi}{4}\right) = \sqrt{2} > 0\), so there is a local minimum at \(x = \frac{5\pi}{4}\).
   check: subs(-sin(x) - cos(x), x, pi/4) = -sqrt(2)
   check: subs(-sin(x) - cos(x), x, 5*pi/4) = sqrt(2)
4. [trig.values.exact] Evaluate with exact values: the local maximum point is \(\left(\frac{\pi}{4}, \sqrt{2}\right)\) and the local minimum point is \(\left(\frac{5\pi}{4}, -\sqrt{2}\right)\).
   check: subs(sin(x) + cos(x), x, pi/4) = sqrt(2)
   check: subs(sin(x) + cos(x), x, 5*pi/4) = -sqrt(2)


<!-- tier 3, template: the second derivative test fails at one critical number -->
## Card calc1.4-5.sdt-two-tests.t01
skill: calc1.shape.second-derivative-test
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.shape.first-derivative-test, alg.arith.exact-evaluation
difficulty: 3
answer-type: point
vars: k = int(1, 3)
let: f = x^6 - 3*k*x^4
answer: (-sqrt(2*k), -4*k^3), (0, 0), (sqrt(2*k), -4*k^3)
wrong: (-sqrt(2*k), -4*k^3), (sqrt(2*k), -4*k^3) => The second derivative is zero at \(x = 0\), so the second derivative test says nothing there. That does not mean there is no extremum: check the sign of \(f'\) on each side. @5; (0, 0) => The factor \(x^2 - [[2*k]]\) of \(f'\) is also zero, at \(x = \pm [[tex(sqrt(2*k))]]\), so there are more critical numbers. @3

### Question
Find all local extrema of \(f(x) = [[tex(f)]]\), as points \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers, then use the second derivative test at each. Where the second derivative is zero the test fails, and the sign change of the first derivative has to decide.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = 6x^5 - [[12*k]]x^3\) and \(f''(x) = 30x^4 - [[36*k]]x^2\).
   check: diff(f, x) = 6*x^5 - 12*k*x^3
   check: diff(f, x, 2) = 30*x^4 - 36*k*x^2
2. [alg.factor.polynomials] Factor: \(f'(x) = 6x^3(x^2 - [[2*k]])\).
   check: expand(6*x^3*(x^2 - 2*k)) = 6*x^5 - 12*k*x^3
3. [alg.solve.polynomial] Critical numbers: \(f'(x) = 0\) at \(x = 0\) and \(x = \pm [[tex(sqrt(2*k))]]\).
   check: solve(6*x^3*(x^2 - 2*k), x) = {-sqrt(2*k), 0, sqrt(2*k)}
4. [calc1.shape.second-derivative-test] Test: \(f''\left(\pm [[tex(sqrt(2*k))]]\right) = [[48*k^2]] > 0\), so there is a local minimum at each of those two numbers. But \(f''(0) = 0\), so the test is inconclusive at \(x = 0\).
   check: subs(30*x^4 - 36*k*x^2, x, sqrt(2*k)) = 48*k^2
   check: subs(30*x^4 - 36*k*x^2, x, -sqrt(2*k)) = 48*k^2
   check: subs(30*x^4 - 36*k*x^2, x, 0) = 0
5. [calc1.shape.first-derivative-test] Fall back on the first derivative at \(x = 0\): \(f'(-1) = [[6*(2*k - 1)]]\) and \(f'(1) = [[-6*(2*k - 1)]]\), so \(f'\) changes from positive to negative and there is a local maximum at \(x = 0\).
   check: subs(6*x^3*(x^2 - 2*k), x, -1) = 6*(2*k - 1)
   check: subs(6*x^3*(x^2 - 2*k), x, 1) = -6*(2*k - 1)
6. [alg.arith.exact-evaluation] Evaluate: \(f(0) = 0\), and \(f\left(\pm [[tex(sqrt(2*k))]]\right) = [[8*k^3]] - [[12*k^3]] = [[-4*k^3]]\).
   check: subs(f, x, 0) = 0
   check: subs(f, x, sqrt(2*k)) = -4*k^3
   check: subs(f, x, -sqrt(2*k)) = -4*k^3
7. [calc1.shape.second-derivative-test] Conclude: there are local minima at the two outer critical numbers and a local maximum at \(x = 0\). The local extrema are the points \(\left(-[[tex(sqrt(2*k))]], [[-4*k^3]]\right), (0, 0), \left([[tex(sqrt(2*k))]], [[-4*k^3]]\right)\).

<!-- tier 3, template: classify from a given derivative -->
## Card calc1.4-5.sdt-fprime.t01
skill: calc1.shape.second-derivative-test
cue: required
uses: alg.solve.polynomial, calc1.deriv.product-rule
difficulty: 3
vars: p = int(1, 3); q = int(2, 5)
require: q > p
let: g = (x^2 - p^2)*(x^2 - q^2)

### Question
A function \(f\) has \(f'(x) = [[tex(g)]]\) for all \(x\). Use the second derivative test to classify the critical numbers of \(f\).

### Part a
answer-type: set
answer: -q, p
wrong: -p, q => At \(x = [[p]]\) the second derivative is \([[2*p*(p^2 - q^2)]]\), which is negative, so the graph is concave down there and \(x = [[p]]\) is a local maximum. @3
Find all \(x\)-values at which \(f\) has a local maximum.

### Part b
answer-type: set
answer: -p, q
wrong: -q, p => At \(x = [[q]]\) the second derivative is \([[2*q*(q^2 - p^2)]]\), which is positive, so the graph is concave up there and \(x = [[q]]\) is a local minimum. @3
Find all \(x\)-values at which \(f\) has a local minimum.

### Solution
0. [calc1.shape.second-derivative-test] Set up: the critical numbers are the zeros of the given derivative. Differentiate it to get the second derivative, then check the sign of the second derivative at each critical number.
1. [alg.solve.polynomial] Critical numbers: \(f'(x) = 0\) when \(x^2 = [[p^2]]\) or \(x^2 = [[q^2]]\), that is, at \(x = \pm [[p]]\) and \(x = \pm [[q]]\).
   check: solve(g, x) = {-q, -p, p, q}
2. [calc1.deriv.product-rule] Differentiate \(f'\) with the product rule: \(f''(x) = 2x(x^2 - [[q^2]]) + 2x(x^2 - [[p^2]]) = 2x(2x^2 - [[p^2 + q^2]])\).
   check: diff(g, x) = 2*x*(2*x^2 - p^2 - q^2)
3. [calc1.shape.second-derivative-test] Test: \(f''(-[[q]]) = [[-2*q*(q^2 - p^2)]]\), \(f''(-[[p]]) = [[2*p*(q^2 - p^2)]]\), \(f''([[p]]) = [[2*p*(p^2 - q^2)]]\) and \(f''([[q]]) = [[2*q*(q^2 - p^2)]]\). So \(f\) has local maxima at \(x = -[[q]]\) and \(x = [[p]]\), where the second derivative is negative, and local minima at \(x = -[[p]]\) and \(x = [[q]]\), where it is positive.
   check: subs(2*x*(2*x^2 - p^2 - q^2), x, -q) = -2*q*(q^2 - p^2)
   check: subs(2*x*(2*x^2 - p^2 - q^2), x, -p) = 2*p*(q^2 - p^2)
   check: subs(2*x*(2*x^2 - p^2 - q^2), x, p) = 2*p*(p^2 - q^2)
   check: subs(2*x*(2*x^2 - p^2 - q^2), x, q) = 2*q*(q^2 - p^2)

<!-- tier 3: a quotient with a logarithm -->
## Card calc1.4-5.sdt-lnx.001
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.logarithm, calc1.deriv.quotient-rule, alg.logs.solve-equations, alg.arith.exact-evaluation
difficulty: 3

### Question
The function \(f(x) = \dfrac{\ln x}{x}\) is defined for \(x > 0\). Use the second derivative test to classify its critical number.

### Part a
answer-type: point
answer: (e, 1/e)
wrong: (1, 0) => The number \(x = 1\) solves \(\ln x = 0\), which is where \(f\) is zero. Critical numbers solve \(f'(x) = 0\), that is, \(1 - \ln x = 0\). @3
Find the critical point \((x, f(x))\).

### Part b
answer-type: text
answer: maximum; local maximum; max; local max
wrong: minimum => At \(x = e\) the second derivative is negative, so the graph is concave down there and the point is a local maximum. @4
Is the critical point a local maximum or a local minimum? Answer with the word maximum or minimum.

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical number, where the derivative is zero, then use the sign of the second derivative there. Negative means a local maximum and positive means a local minimum.
1. [calc1.deriv.logarithm] Differentiate the logarithm: \((\ln x)' = \frac{1}{x}\) for \(x > 0\).
   check: diff(ln(x), x) = 1/x
2. [calc1.deriv.quotient-rule] Differentiate twice with the quotient rule: \(f'(x) = \frac{1 - \ln x}{x^2}\) and \(f''(x) = \frac{2\ln x - 3}{x^3}\).
   check: diff(ln(x)/x, x) = (1 - ln(x))/x^2
   check: diff((1 - ln(x))/x^2, x) = (2*ln(x) - 3)/x^3
3. [alg.logs.solve-equations] Solve \(f'(x) = 0\): the denominator \(x^2\) is positive, so \(1 - \ln x = 0\), \(\ln x = 1\) and \(x = e\). The derivative exists for every \(x > 0\), so this is the only critical number.
   check: solve(1 - ln(x), x) = {exp(1)}
4. [calc1.shape.second-derivative-test] Test: \(f''(e) = \frac{2 - 3}{e^3} = -\frac{1}{e^3} < 0\), so there is a local maximum at \(x = e\).
   check: subs((2*ln(x) - 3)/x^3, x, exp(1)) = -exp(-3)
5. [alg.arith.exact-evaluation] Evaluate: \(f(e) = \frac{\ln e}{e} = \frac{1}{e}\), so the local maximum point is \(\left(e, \frac{1}{e}\right)\).
   check: subs(ln(x)/x, x, exp(1)) = exp(-1)

<!-- tier 4, template: work backwards from the inflection point and the minimum -->
## Card calc1.4-5.sdt-backward.t01
skill: calc1.shape.second-derivative-test
uses: calc1.deriv.power-rule, calc1.shape.inflection-points, alg.solve.linear, alg.factor.polynomials, alg.arith.exact-evaluation
difficulty: 4
answer-type: point
vars: s = int(-1, 2); d = int(2, 4)
let: q = s + d; u = -3*s; w = 3*q*(2*s - q); r = 2*s - q
answer: (r, r^3 + u*r^2 + w*r)
wrong: (q, q^3 + u*q^2 + w*q) => The point at \(x = [[q]]\) is the local minimum that the question gives. The local maximum is at the other critical number. @5; (s, s^3 + u*s^2 + w*s) => The inflection point is where \(f''\) is zero. It is not a local extremum, because \(f'\) is not zero there. @5

### Question
The function \(f(x) = x^3 + ax^2 + bx\), where \(a\) and \(b\) are constants, has an inflection point at \(x = [[s]]\) and a local minimum at \(x = [[q]]\). Find the local maximum point of \(f\), as a point \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: use the two conditions to find the constants. The second derivative is zero at an inflection point, and the first derivative is zero at a local minimum. Then find the other critical number and use the sign of the second derivative to confirm that it is the local maximum.
1. [calc1.deriv.power-rule] Differentiate twice: \(f'(x) = 3x^2 + 2ax + b\) and \(f''(x) = 6x + 2a\).
   check: diff(x^3 + a*x^2 + b*x, x) = 3*x^2 + 2*a*x + b
   check: diff(x^3 + a*x^2 + b*x, x, 2) = 6*x + 2*a
2. [calc1.shape.inflection-points] Inflection point at \(x = [[s]]\): the second derivative is zero there, so \(f''([[s]]) = [[tex(6*s + 2*a)]] = 0\) and \(a = [[u]]\).
   check: solve(6*s + 2*a, a) = {-3*s}
3. [alg.solve.linear] Local minimum at \(x = [[q]]\): the first derivative is zero there, so \(f'([[q]]) = [[tex(3*q^2 + 2*a*q + b)]] = 0\). With \(a = [[u]]\) this gives \(b = [[w]]\).
   check: solve(3*q^2 + 2*u*q + b, b) = {w}
4. [alg.factor.polynomials] Factor with these constants: \(f'(x) = [[tex(3*x^2 + 2*u*x + w)]] = [[tex(3*(x - q)*(x - r))]]\), so the critical numbers are \(x = [[q]]\) and \(x = [[r]]\).
   check: expand(3*(x - q)*(x - r)) = 3*x^2 + 2*u*x + w
5. [calc1.shape.second-derivative-test] Test: \(f''(x) = [[tex(6*x + 2*u)]]\), so \(f''([[r]]) = [[-6*d]] < 0\) and \(f''([[q]]) = [[6*d]] > 0\). The other critical number \(x = [[r]]\) is the local maximum, and \(x = [[q]]\) is the local minimum, as given.
   check: subs(6*x + 2*u, x, r) = -6*d
   check: subs(6*x + 2*u, x, q) = 6*d
6. [alg.arith.exact-evaluation] Evaluate: \(f([[r]]) = [[r^3 + u*r^2 + w*r]]\).
   check: subs(x^3 + u*x^2 + w*x, x, r) = r^3 + u*r^2 + w*r
7. [calc1.shape.second-derivative-test] Conclude: the local maximum point is \(([[r]], [[r^3 + u*r^2 + w*r]])\).

<!-- tier 4: three critical numbers, exponential times a trigonometric function -->
## Card calc1.4-5.sdt-expsin.001
skill: calc1.shape.second-derivative-test
cue: required
uses: calc1.deriv.chain-linear-inside, calc1.deriv.trig-sin-cos, calc1.deriv.product-rule, trig.equations.solve, trig.values.exact
difficulty: 4

### Question
Use the second derivative test to classify the critical numbers of \(f(x) = e^{-x}\sin x\) on the interval \((0, 3\pi)\).

### Part a
answer-type: point
answer: (pi/4, sqrt(2)/2*e^(-pi/4)), (9*pi/4, sqrt(2)/2*e^(-9*pi/4))
wrong: (pi/4, sqrt(2)/2*e^(-pi/4)) => There is a third critical number in the interval, \(x = \frac{9\pi}{4}\). The second derivative is negative there too, so it is a local maximum as well. @5
Find the local maximum points \((x, f(x))\).

### Part b
answer-type: point
answer: (5*pi/4, -sqrt(2)/2*e^(-5*pi/4))
wrong: (3*pi/2, -e^(-3*pi/2)) => The critical numbers come from \(f'(x) = e^{-x}(\cos x - \sin x) = 0\), not from the minimum of \(\sin x\) alone: the factor \(e^{-x}\) changes where the graph turns. @4
Find the local minimum point \((x, f(x))\).

### Solution
0. [calc1.shape.second-derivative-test] Set up: find the critical numbers in the interval, where the derivative is zero. At each one the sign of the second derivative decides: negative means a local maximum and positive means a local minimum.
1. [calc1.deriv.chain-linear-inside] Differentiate the exponential: \(\left(e^{-x}\right)' = -e^{-x}\).
   check: diff(e^(-x), x) = -e^(-x)
2. [calc1.deriv.trig-sin-cos] Differentiate the sine and the cosine: \((\sin x)' = \cos x\) and \((\cos x)' = -\sin x\).
   check: diff(sin(x), x) = cos(x)
   check: diff(cos(x), x) = -sin(x)
3. [calc1.deriv.product-rule] Product rule, twice: \(f'(x) = e^{-x}(\cos x - \sin x)\) and \(f''(x) = -2e^{-x}\cos x\).
   check: diff(e^(-x)*sin(x), x) = e^(-x)*(cos(x) - sin(x))
   check: diff(e^(-x)*(cos(x) - sin(x)), x) = -2*e^(-x)*cos(x)
4. [trig.equations.solve] Solve \(f'(x) = 0\): \(e^{-x}\) is never zero, so \(\cos x = \sin x\) and \(\tan x = 1\). In \((0, 3\pi)\) this gives \(x = \frac{\pi}{4}\), \(x = \frac{5\pi}{4}\) and \(x = \frac{9\pi}{4}\).
   check: subs(cos(x) - sin(x), x, pi/4) = 0
   check: subs(cos(x) - sin(x), x, 5*pi/4) = 0
   check: subs(cos(x) - sin(x), x, 9*pi/4) = 0
5. [calc1.shape.second-derivative-test] Test: \(f''\left(\frac{\pi}{4}\right) = -\sqrt{2}\,e^{-\pi/4} < 0\), so there is a local maximum. \(f''\left(\frac{5\pi}{4}\right) = \sqrt{2}\,e^{-5\pi/4} > 0\), so there is a local minimum. \(f''\left(\frac{9\pi}{4}\right) = -\sqrt{2}\,e^{-9\pi/4} < 0\), so there is a local maximum.
   check: subs(-2*e^(-x)*cos(x), x, pi/4) = -sqrt(2)*e^(-pi/4)
   check: subs(-2*e^(-x)*cos(x), x, 5*pi/4) = sqrt(2)*e^(-5*pi/4)
   check: subs(-2*e^(-x)*cos(x), x, 9*pi/4) = -sqrt(2)*e^(-9*pi/4)
6. [trig.values.exact] Evaluate with exact values: \(f\left(\frac{\pi}{4}\right) = \frac{\sqrt{2}}{2}e^{-\pi/4}\), \(f\left(\frac{5\pi}{4}\right) = -\frac{\sqrt{2}}{2}e^{-5\pi/4}\) and \(f\left(\frac{9\pi}{4}\right) = \frac{\sqrt{2}}{2}e^{-9\pi/4}\).
   check: subs(e^(-x)*sin(x), x, pi/4) = sqrt(2)/2*e^(-pi/4)
   check: subs(e^(-x)*sin(x), x, 5*pi/4) = -sqrt(2)/2*e^(-5*pi/4)
   check: subs(e^(-x)*sin(x), x, 9*pi/4) = sqrt(2)/2*e^(-9*pi/4)



<!-- ===================================================================== -->
<!-- calc1.shape.from-derivative-graph                                     -->
<!-- The plot is always the graph of f', never of f.                        -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.fromgraph-example.001
kind: example
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test, calc1.shape.concavity, calc1.shape.inflection-points
plot: (x^2 - 4)/2, x = -4..4

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-4, 4]\). Use it to find where \(f\) is increasing, the \(x\)-values of the local extrema of \(f\), where \(f\) is concave up, and the \(x\)-values of the inflection points of \(f\).

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the height of the graph of the derivative is the slope of the function. Where the graph is above the axis the function increases, and where it is below the axis the function decreases. Where the graph rises the function is concave up, and where it falls the function is concave down.
1. [calc1.shape.from-derivative-graph] Read the zeros: the graph meets the axis at \(x = -2\) and \(x = 2\).
   check: solve((x^2 - 4)/2, x) = {-2, 2}
2. [calc1.shape.first-derivative-test] Classify: the graph is above the axis before \(x = -2\), below it between \(-2\) and \(2\), and above it after \(2\), with heights \(f'(-3) = \frac{5}{2}\), \(f'(0) = -2\) and \(f'(3) = \frac{5}{2}\). So \(f\) is increasing on \((-4, -2)\) and \((2, 4)\) and decreasing on \((-2, 2)\). It has a local maximum at \(x = -2\), where \(f'\) goes from positive to negative, and a local minimum at \(x = 2\).
   check: subs((x^2 - 4)/2, x, -3) = 5/2
   check: subs((x^2 - 4)/2, x, 0) = -2
   check: subs((x^2 - 4)/2, x, 3) = 5/2
3. [calc1.shape.concavity] Concavity: the graph is a parabola with its lowest point at \(x = 0\). It falls on \((-4, 0)\) and rises on \((0, 4)\), so \(f'' < 0\) on \((-4, 0)\) and \(f'' > 0\) on \((0, 4)\). The function is concave up on \((0, 4)\).
   check: diff((x^2 - 4)/2, x) = x
4. [calc1.shape.inflection-points] Inflection point: \(f''(x) = x\) changes sign from negative to positive at \(x = 0\), and \(f\) is defined there, so the inflection point is at \(x = 0\).
   check: solve(diff((x^2 - 4)/2, x), x) = {0}

<!-- tier 1, template: where f decreases, read from a parabola -->
## Card calc1.4-5.fromgraph-quad.t01
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.increasing-decreasing
difficulty: 1
answer-type: interval
endpoints: either
vars: a = int(-2, 2); b = int(1, 3); x
let: g = (x - a)^2 - b^2
answer: (a - b, a + b)
wrong: (a - b - 2, a - b) U (a + b, a + b + 2) => The graph of \(f'\) is above the axis outside these two numbers, so \(f\) is increasing there. A function decreases where its derivative is negative, below the axis. @1; (a - b - 2, a) => This is where the graph of \(f'\) is falling, not where \(f\) is decreasing. A function decreases where its derivative is below the axis. @1
plot: [[g]], x = [[a - b - 2]]..[[a + b + 2]]

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \(\left[ [[a - b - 2]], [[a + b + 2]] \right]\). On what interval is \(f\) decreasing?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: a function decreases where its derivative is negative, so look for the part of the graph of the derivative that lies below the horizontal axis.
1. [calc1.shape.from-derivative-graph] Read the zeros: the graph meets the axis at \(x = [[a - b]]\) and \(x = [[a + b]]\). At its lowest point, \(x = [[a]]\), the graph has height \([[-b^2]]\), which is below the axis.
   check: solve(g, x) = {a - b, a + b}
   check: subs(g, x, a) = -b^2
2. [calc1.shape.increasing-decreasing] Conclude: \(f' < 0\) for \([[a - b]] < x < [[a + b]]\), so \(f\) is decreasing on \(([[a - b]], [[a + b]])\).

<!-- tier 1: rising derivative -->
## Card calc1.4-5.fromgraph-concept.001
skill: calc1.shape.from-derivative-graph
difficulty: 1
answer-type: choice

### Question
On an interval, the graph of \(f'\), the derivative of \(f\), is rising from left to right. What does that say about \(f\) on that interval?

### Choices
- [x] \(f\) is concave up
- [ ] \(f\) is concave down
- [ ] \(f\) is increasing
- [ ] \(f\) is decreasing

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the second derivative is the slope of the graph of the first derivative, and the sign of the second derivative decides the concavity of the function.
1. [calc1.shape.from-derivative-graph] Decide: a rising graph of the derivative has positive slope, so the second derivative is positive and the function is concave up. Whether the function itself is increasing depends on whether the graph of the derivative is above the axis, and this information does not say that.

<!-- tier 1: a sign change from positive to negative -->
## Card calc1.4-5.fromgraph-cross.001
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test
difficulty: 1
answer-type: number
answer: 2
wrong: -1 => At this number the graph of \(f'\) goes from below the axis to above it, so \(f\) has a local minimum there, not a maximum. @2
plot: (2 - x)*(x + 1), x = -3..4

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-3, 4]\). At which \(x\)-value does \(f\) have a local maximum?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: a local maximum of the function is where its derivative changes from positive to negative, so the graph must go from above the axis to below it.
1. [calc1.shape.from-derivative-graph] Read the zeros: the graph meets the axis at \(x = -1\) and \(x = 2\).
   check: solve((2 - x)*(x + 1), x) = {-1, 2}
2. [calc1.shape.first-derivative-test] Classify: at \(x = -1\) the graph goes from below to above the axis, which gives a local minimum. At \(x = 2\) it goes from above to below, so the local maximum is at \(x = 2\).

<!-- tier 2, template: a sharp peak in the graph of f' -->
## Card calc1.4-5.fromgraph-tent.t01
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.inflection-points
difficulty: 2
answer-type: number
vars: h = int(-2, 2); t = int(2, 4)
let: g = t - abs(x - h)
answer: h
wrong: h - t => At this number the graph of \(f'\) meets the axis and goes from below to above it, so \(f\) has a local minimum there. An inflection point is where the graph of \(f'\) changes from rising to falling, or the reverse. @1; h + t => At this number the graph of \(f'\) meets the axis and goes from above to below it, so \(f\) has a local maximum there. An inflection point is where the graph of \(f'\) changes from rising to falling, or the reverse. @1
plot: [[g]], x = [[h - t - 1]]..[[h + t + 1]]

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \(\left[ [[h - t - 1]], [[h + t + 1]] \right]\). Find the \(x\)-value of the inflection point of \(f\).

### Solution
0. [calc1.shape.from-derivative-graph] Set up: an inflection point of the function is where the concavity changes, so the graph of its derivative must change from rising to falling, or from falling to rising. That happens at a peak or a valley of the graph.
1. [calc1.shape.from-derivative-graph] Read the graph: it rises to a sharp peak at \(x = [[h]]\), where its height is \([[t]]\), and it falls after that. Its zeros, at \(x = [[h - t]]\) and \(x = [[h + t]]\), are where \(f\) has a local minimum and a local maximum, not where the concavity changes.
   check: subs(g, x, h) = t
   check: subs(g, x, h - t) = 0
   check: subs(g, x, h + t) = 0
   check: subs(diff(g, x), x, h - 1) = 1
   check: subs(diff(g, x), x, h + 1) = -1
2. [calc1.shape.inflection-points] Conclude: \(f''\) is \(1\) to the left of the peak and \(-1\) to the right of it, so \(f''\) changes sign from positive to negative at \(x = [[h]]\), where \(f\) is defined. The inflection point is at \(x = [[h]]\).

<!-- tier 2: touching the axis is not a sign change -->
## Card calc1.4-5.fromgraph-touch.001
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test
difficulty: 2
answer-type: number
answer: 0
wrong: 2 => The graph of \(f'\) meets the axis at \(x = 0\) and \(x = 4\), so \(f'\) is zero there. But \(f'\) stays above the axis on both sides of each, so it does not change sign, and \(f\) has no local extremum at either. @2
plot: x^2*(x - 4)^2, x = -1..5

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-1, 5]\). How many local extrema does \(f\) have for \(x\) strictly between \(-1\) and \(5\)?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: a local extremum of the function needs its derivative to change sign. Touching the axis is not enough.
1. [calc1.shape.from-derivative-graph] Read the zeros: the graph meets the axis at \(x = 0\) and \(x = 4\).
   check: solve(x^2*(x - 4)^2, x) = {0, 4}
2. [calc1.shape.first-derivative-test] Check the sign on each side: \(f'(-1) = 25\), \(f'(1) = 9\), \(f'(3) = 9\) and \(f'(5) = 25\) are all positive. So \(f'\) is positive on both sides of \(x = 0\) and of \(x = 4\), and it never changes sign.
   check: subs(x^2*(x - 4)^2, x, -1) = 25
   check: subs(x^2*(x - 4)^2, x, 1) = 9
   check: subs(x^2*(x - 4)^2, x, 3) = 9
   check: subs(x^2*(x - 4)^2, x, 5) = 25
3. [calc1.shape.from-derivative-graph] Conclude: with no sign change, \(f\) has \(0\) local extrema.

<!-- tier 2: where the graph of f' is rising -->
## Card calc1.4-5.fromgraph-concavity.001
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.concavity
difficulty: 2
answer-type: interval
endpoints: either
vars: x
answer: (-2, -1) U (1, 2)
wrong: (-1, 1) => The graph of \(f'\) falls on this interval, so \(f''\) is negative and \(f\) is concave down there, not concave up. @1; (-sqrt(3), 0) U (sqrt(3), 2) => The graph is above the axis on these intervals, so \(f\) is increasing there. Concave up needs the graph of \(f'\) to be rising. @1
plot: x^3 - 3*x, x = -2..2

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-2, 2]\). On what intervals is \(f\) concave up?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the function is concave up where its second derivative is positive, that is, where the graph of the derivative is rising.
1. [calc1.shape.from-derivative-graph] Read the graph: it rises from the left end to a peak at \(x = -1\), falls to a valley at \(x = 1\), and rises again to the right end. The slope of the graph is \(f''(x) = 3x^2 - 3\), which is positive at \(x = -\frac{3}{2}\), negative at \(x = 0\) and positive at \(x = \frac{3}{2}\).
   check: diff(x^3 - 3*x, x) = 3*x^2 - 3
   check: solve(3*x^2 - 3, x) = {-1, 1}
   check: subs(3*x^2 - 3, x, -3/2) = 15/4
   check: subs(3*x^2 - 3, x, 0) = -3
   check: subs(3*x^2 - 3, x, 3/2) = 15/4
2. [calc1.shape.concavity] Conclude: \(f'' > 0\) on \((-2, -1)\) and on \((1, 2)\), so \(f\) is concave up on \((-2, -1) \cup (1, 2)\).

<!-- tier 2: the steepest rise is at the peak of f' -->
## Card calc1.4-5.fromgraph-steepest.001
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.inflection-points
difficulty: 2
answer-type: number
answer: 1
wrong: 3 => At this number the graph of \(f'\) meets the axis, so the slope of \(f\) is zero: the graph of \(f\) is flat there, with a local maximum, not rising steeply. @1; 4 => The number 4 is the height of the peak, which is the largest slope. The question asks for the \(x\)-value where it happens. @1
plot: 4 - (x - 1)^2, x = -2..4

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-2, 4]\). At which \(x\)-value is the graph of \(f\) rising most steeply?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the slope of the graph of the function is the height of the graph of its derivative, so the function rises most steeply where the derivative is largest.
1. [calc1.shape.from-derivative-graph] Read the peak: the graph of \(f'\) has its highest point at \(x = 1\), at height \(4\). It meets the axis at \(x = -1\) and \(x = 3\), where \(f\) is flat.
   check: subs(4 - (x - 1)^2, x, 1) = 4
   check: solve(diff(4 - (x - 1)^2, x), x) = {1}
   check: solve(4 - (x - 1)^2, x) = {-1, 3}
2. [calc1.shape.inflection-points] Conclude: \(f'\) is largest where \(f''\) changes from positive to negative, which is an inflection point of \(f\). The steepest rise is at \(x = 1\).


<!-- tier 3, template: a sine wave for f' -->
## Card calc1.4-5.fromgraph-sine.t01
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test, calc1.shape.inflection-points
difficulty: 3
vars: a = int(1, 3); h = int(0, 2)
let: g = a*sin(pi*(x - h)/2)
plot: [[g]], x = [[h]]..[[h + 8]]

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \(\left[ [[h]], [[h + 8]] \right]\). Consider only \(x\)-values strictly between \([[h]]\) and \([[h + 8]]\).

### Part a
answer-type: set
answer: h + 2, h + 6
wrong: h + 2, h + 4, h + 6 => The graph of \(f'\) goes from below to above the axis at \(x = [[h + 4]]\), so \(f\) has a local minimum there, not a maximum. @2
Find the \(x\)-values at which \(f\) has a local maximum.

### Part b
answer-type: set
answer: h + 4
wrong: h + 2, h + 6 => At these numbers the graph of \(f'\) goes from above to below the axis, so \(f\) has local maxima there. @2
Find the \(x\)-values at which \(f\) has a local minimum.

### Part c
answer-type: set
answer: h + 1, h + 3, h + 5, h + 7
wrong: h + 2, h + 4, h + 6 => The graph meets the axis at these numbers, so \(f'\) is zero and \(f\) has local extrema there. Inflection points are where the graph of \(f'\) has a peak or a valley. @3
Find the \(x\)-values at which \(f\) has an inflection point.

### Solution
0. [calc1.shape.from-derivative-graph] Set up: a local maximum of the function is where its derivative goes from positive to negative, and a local minimum is where it goes from negative to positive. An inflection point is where the concavity changes, which happens at a peak or a valley of the graph of the derivative.
1. [calc1.shape.from-derivative-graph] Read the zeros: inside the interval the graph meets the axis at \(x = [[h + 2]]\), \(x = [[h + 4]]\) and \(x = [[h + 6]]\).
   check: subs(g, x, h + 2) = 0
   check: subs(g, x, h + 4) = 0
   check: subs(g, x, h + 6) = 0
2. [calc1.shape.first-derivative-test] Classify: the heights of the graph are \(f'([[h + 1]]) = [[a]]\), \(f'([[h + 3]]) = [[-a]]\), \(f'([[h + 5]]) = [[a]]\) and \(f'([[h + 7]]) = [[-a]]\). So \(f'\) goes from positive to negative at \(x = [[h + 2]]\) and \(x = [[h + 6]]\), which gives local maxima, and from negative to positive at \(x = [[h + 4]]\), which gives a local minimum.
   check: subs(g, x, h + 1) = a
   check: subs(g, x, h + 3) = -a
   check: subs(g, x, h + 5) = a
   check: subs(g, x, h + 7) = -a
3. [calc1.shape.inflection-points] Inflection points: the graph has a peak or a valley, with a horizontal tangent, at \(x = [[h + 1]]\), \(x = [[h + 3]]\), \(x = [[h + 5]]\) and \(x = [[h + 7]]\). There the slope of the graph, \(f''\), changes sign, so these are the inflection points of \(f\).
   check: subs(diff(g, x), x, h + 1) = 0
   check: subs(diff(g, x), x, h + 3) = 0
   check: subs(diff(g, x), x, h + 5) = 0
   check: subs(diff(g, x), x, h + 7) = 0

<!-- tier 3, template: a crossing, a touch, a peak and a valley -->
## Card calc1.4-5.fromgraph-touch-cubic.t01
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test, calc1.shape.inflection-points, calc1.shape.concavity
difficulty: 3
vars: s = int(-2, 1); x
let: g = (x - s)*(x - s - 3)^2
plot: [[g]], x = [[s - 1]]..[[s + 5]]

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \(\left[ [[s - 1]], [[s + 5]] \right]\). Consider only \(x\)-values strictly between \([[s - 1]]\) and \([[s + 5]]\).

### Part a
answer-type: set
answer: s
wrong: s, s + 3 => The graph of \(f'\) also meets the axis at \(x = [[s + 3]]\), but it only touches the axis there and stays above it on both sides. So \(f'\) does not change sign, and \(f\) has no extremum there. @2
Find the \(x\)-values at which \(f\) has a local extremum.

### Part b
answer-type: set
answer: s + 1, s + 3
wrong: s + 1 => The graph of \(f'\) also has a valley at \(x = [[s + 3]]\), where it touches the axis. The graph changes from falling to rising there, so the concavity of \(f\) changes and this is an inflection point. @3; s, s + 3 => The number \([[s]]\) is where the graph meets the axis, so \(f'\) is zero there. Inflection points are where the graph has a peak or a valley. @3
Find the \(x\)-values at which \(f\) has an inflection point.

### Part c
answer-type: interval
endpoints: either
answer: (s + 1, s + 3)
wrong: (s - 1, s + 1) U (s + 3, s + 5) => The graph of \(f'\) is rising on these intervals, so \(f''\) is positive and \(f\) is concave up there, not concave down. @4
Find the interval on which \(f\) is concave down.

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the function has a local extremum where its derivative changes sign, an inflection point where the graph of the derivative has a peak or a valley, and it is concave down where the graph of the derivative is falling.
1. [calc1.shape.from-derivative-graph] Read the zeros: the graph meets the axis at \(x = [[s]]\), where it crosses, and at \(x = [[s + 3]]\), where it only touches the axis.
   check: solve(g, x) = {s, s + 3}
2. [calc1.shape.first-derivative-test] Classify: \(f'([[s - 1]]) = -16\) is negative, and \(f'([[s + 1]]) = 4\) and \(f'([[s + 4]]) = 4\) are positive. So \(f'\) changes sign only at \(x = [[s]]\), from negative to positive, which gives a local minimum. There is no sign change at \(x = [[s + 3]]\).
   check: subs(g, x, s - 1) = -16
   check: subs(g, x, s + 1) = 4
   check: subs(g, x, s + 4) = 4
3. [calc1.shape.inflection-points] Inflection points: the slope of the graph is zero at \(x = [[s + 1]]\), a peak, and at \(x = [[s + 3]]\), a valley. It changes sign at both, since \(f''([[s]]) = 9\), \(f''([[s + 2]]) = -3\) and \(f''([[s + 4]]) = 9\).
   check: solve(diff(g, x), x) = {s + 1, s + 3}
   check: subs(diff(g, x), x, s) = 9
   check: subs(diff(g, x), x, s + 2) = -3
   check: subs(diff(g, x), x, s + 4) = 9
4. [calc1.shape.concavity] Concavity: \(f''(x) = [[tex(3*(x - s - 1)*(x - s - 3))]]\) is negative exactly between its two zeros, where the graph of \(f'\) is falling, so \(f\) is concave down on \(([[s + 1]], [[s + 3]])\).
   check: diff(g, x) = 3*(x - s - 1)*(x - s - 3)

<!-- tier 3: a polygonal graph of f' -->
## Card calc1.4-5.fromgraph-zigzag.001
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test, calc1.shape.inflection-points
difficulty: 3
vars: x
plot: -2*x - 4, x = -3..-1; 2*x, x = -1..1; -2*x + 4, x = 1..3

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([-3, 3]\). It is made of three line segments. Consider only \(x\)-values strictly between \(-3\) and \(3\).

### Part a
answer-type: set
answer: -2, 2
wrong: -2, 0, 2 => At \(x = 0\) the graph of \(f'\) goes from below to above the axis, so \(f\) has a local minimum there, not a maximum. @2
Find the \(x\)-values at which \(f\) has a local maximum.

### Part b
answer-type: set
answer: -1, 1
wrong: -2, 0, 2 => The graph meets the axis at these numbers, so \(f'\) is zero and \(f\) has local extrema there. Inflection points are where the graph of \(f'\) has a corner that turns it from falling to rising, or the reverse. @3
Find the \(x\)-values at which \(f\) has an inflection point.

### Part c
answer-type: interval
endpoints: either
answer: (-1, 1)
wrong: (0, 2) => The graph of \(f'\) is above the axis on this interval, so \(f\) is increasing there. Concave up needs the graph to be rising, which it is on \((-1, 1)\). @3
Find the interval on which \(f\) is concave up.

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the function has a local extremum where its derivative changes sign. It has an inflection point where the graph of the derivative changes from falling to rising, or the reverse, and it is concave up where the graph is rising.
1. [calc1.shape.from-derivative-graph] Read the segments: the graph is \(f'(x) = -2x - 4\) on \([-3, -1]\), \(f'(x) = 2x\) on \([-1, 1]\) and \(f'(x) = -2x + 4\) on \([1, 3]\). The pieces meet at heights \(-2\) at \(x = -1\) and \(2\) at \(x = 1\), and the graph meets the axis at \(x = -2\), \(x = 0\) and \(x = 2\).
   check: subs(-2*x - 4, x, -1) = -2
   check: subs(2*x, x, -1) = -2
   check: subs(2*x, x, 1) = 2
   check: subs(-2*x + 4, x, 1) = 2
   check: solve(-2*x - 4, x) = {-2}
   check: solve(2*x, x) = {0}
   check: solve(-2*x + 4, x) = {2}
2. [calc1.shape.first-derivative-test] Classify: \(f'(-\frac{5}{2}) = 1\), \(f'(-\frac{1}{2}) = -1\), \(f'(\frac{1}{2}) = 1\) and \(f'(\frac{5}{2}) = -1\). So \(f'\) goes from positive to negative at \(x = -2\) and \(x = 2\), which gives local maxima, and from negative to positive at \(x = 0\), which gives a local minimum.
   check: subs(-2*x - 4, x, -5/2) = 1
   check: subs(2*x, x, -1/2) = -1
   check: subs(2*x, x, 1/2) = 1
   check: subs(-2*x + 4, x, 5/2) = -1
3. [calc1.shape.inflection-points] Inflection points: the slopes of the three segments are \(-2\), \(2\) and \(-2\), so \(f''\) is negative on \((-3, -1)\), positive on \((-1, 1)\) and negative on \((1, 3)\). It changes sign at \(x = -1\) and \(x = 1\), where \(f\) is defined, so these are the inflection points, and \(f\) is concave up on \((-1, 1)\).
   check: diff(-2*x - 4, x) = -2
   check: diff(2*x, x) = 2
   check: diff(-2*x + 4, x) = -2

<!-- tier 4: a composition, with a touch point -->
## Card calc1.4-5.fromgraph-compose.001
skill: calc1.shape.from-derivative-graph
uses: calc1.deriv.chain-rule, alg.solve.polynomial, alg.inequality.sign-chart
difficulty: 4
answer-type: number
answer: 3
wrong: 5 => The factor \((x^2 - 4)^2\) of \(g'\) is a square, so \(g'\) does not change sign at \(x = 2\) or \(x = -2\). Only the zeros where \(g'\) changes sign give local extrema. @4; 2 => The factor \(2x\) of \(g'\) is also zero, at \(x = 0\), and \(g'\) changes sign there, so \(g\) has a local extremum at \(x = 0\) as well. @3
plot: (x - 1)*(x - 4)^2, x = 0..5

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \([0, 5]\). Let \(g(x) = f(x^2)\), defined for \(-\sqrt{5} \le x \le \sqrt{5}\). How many local extrema does \(g\) have for \(x\) strictly between \(-\sqrt{5}\) and \(\sqrt{5}\)?

### Solution
0. [calc1.shape.from-derivative-graph] Set up: a local extremum of the new function needs its derivative to change sign. Use the chain rule to write that derivative in terms of the derivative of the original function, read the zeros from the graph, and then see where the sign really changes.
1. [calc1.deriv.chain-rule] Chain rule: \(g'(x) = 2x \cdot f'(x^2)\). The graph is that of \(f'(t) = (t - 1)(t - 4)^2\), so \(g'(x) = 2x(x^2 - 1)(x^2 - 4)^2\).
   check: 2*x*subs((x - 1)*(x - 4)^2, x, x^2) = 2*x*(x^2 - 1)*(x^2 - 4)^2
2. [calc1.shape.from-derivative-graph] Read the graph: it crosses the axis at \(1\), from below to above, and only touches it at \(4\), with heights \(f'(0) = -16\), \(f'(2) = 4\) and \(f'(5) = 4\).
   check: solve((x - 1)*(x - 4)^2, x) = {1, 4}
   check: subs((x - 1)*(x - 4)^2, x, 0) = -16
   check: subs((x - 1)*(x - 4)^2, x, 2) = 4
   check: subs((x - 1)*(x - 4)^2, x, 5) = 4
3. [alg.solve.polynomial] Zeros of \(g'\): \(x = 0\), or \(x^2 = 1\), or \(x^2 = 4\). So \(g'(x) = 0\) at \(x = -2, -1, 0, 1, 2\), all inside the interval because \(2 < \sqrt{5}\).
   check: solve(2*x*(x^2 - 1)*(x^2 - 4)^2, x) = {-2, -1, 0, 1, 2}
4. [alg.inequality.sign-chart] Sign changes: the factor \((x^2 - 4)^2\) is never negative, so \(g'\) has the same sign on both sides of \(x = -2\) and of \(x = 2\). The factors \(2x\) and \(x^2 - 1\) do change sign, at \(0\) and \(\pm 1\). Test points: \(g'(-\frac{3}{2}) = -\frac{735}{64}\), \(g'(-\frac{1}{2}) = \frac{675}{64}\), \(g'(\frac{1}{2}) = -\frac{675}{64}\) and \(g'(\frac{3}{2}) = \frac{735}{64}\).
   check: subs(2*x*(x^2 - 1)*(x^2 - 4)^2, x, -3/2) = -735/64
   check: subs(2*x*(x^2 - 1)*(x^2 - 4)^2, x, -1/2) = 675/64
   check: subs(2*x*(x^2 - 1)*(x^2 - 4)^2, x, 1/2) = -675/64
   check: subs(2*x*(x^2 - 1)*(x^2 - 4)^2, x, 3/2) = 735/64
5. [calc1.shape.from-derivative-graph] Conclude: \(g'\) changes sign at \(x = -1\), from negative to positive, at \(x = 0\), from positive to negative, and at \(x = 1\), from negative to positive, and nowhere else. So \(g\) has \(3\) local extrema.

<!-- tier 4, template: the derivative of f minus a line -->
## Card calc1.4-5.fromgraph-shift.t01
skill: calc1.shape.from-derivative-graph
uses: calc1.shape.first-derivative-test
difficulty: 4
vars: a = int(-1, 2); k = int(-2, 1); j = int(1, 3)
require: k + j^2 >= 1
let: g = (x - a)^2 + k; m = k + j^2
plot: [[g]], x = [[a - j - 1]]..[[a + j + 1]]

### Question
The graph of \(f'\), the derivative of a function \(f\), is shown on \(\left[ [[a - j - 1]], [[a + j + 1]] \right]\). Let \(h(x) = f(x) - [[tex(m*x)]]\). Consider only \(x\)-values strictly between \([[a - j - 1]]\) and \([[a + j + 1]]\).

### Part a
answer-type: number
answer: a - j
wrong: a => The lowest point of the graph of \(f'\) is not where \(h\) has an extremum. The derivative of \(h\) is \(f'\) minus a constant, so look for where the graph is at the height of that constant. @1; a + j => At this number \(h'\) goes from negative to positive, so \(h\) has a local minimum there, not a maximum. @2
Find the \(x\)-value at which \(h\) has a local maximum.

### Part b
answer-type: number
answer: a + j
wrong: a - j => At this number \(h'\) goes from positive to negative, so \(h\) has a local maximum there, not a minimum. @2
Find the \(x\)-value at which \(h\) has a local minimum.

### Solution
0. [calc1.shape.from-derivative-graph] Set up: the derivative of the new function is the derivative of the original function minus a constant. So its zeros are where the graph is at the height of that constant, and its sign is positive where the graph is above that height and negative where it is below.
1. [calc1.shape.from-derivative-graph] Read the graph: the lowest point is at \(x = [[a]]\), at height \([[k]]\), which is below \([[m]]\). The graph is at height \([[m]]\) at \(x = [[a - j]]\) and at \(x = [[a + j]]\).
   check: subs(g, x, a) = k
   check: subs(g, x, a - j) = m
   check: subs(g, x, a + j) = m
2. [calc1.shape.first-derivative-test] Classify: \(h'(x) = f'(x) - [[m]]\) equals \([[2*j + 1]]\) at \(x = [[a - j - 1]]\), equals \([[-j^2]]\) at \(x = [[a]]\) and equals \([[2*j + 1]]\) at \(x = [[a + j + 1]]\). So \(h'\) goes from positive to negative at \(x = [[a - j]]\), a local maximum, and from negative to positive at \(x = [[a + j]]\), a local minimum.
   check: subs(g - m, x, a - j - 1) = 2*j + 1
   check: subs(g - m, x, a) = -j^2
   check: subs(g - m, x, a + j + 1) = 2*j + 1



<!-- ===================================================================== -->
<!-- calc1.shape.interpret-derivative-signs                                -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-5.signs-example.001
kind: example
skill: calc1.shape.interpret-derivative-signs
uses: calc1.deriv.chain-linear-inside

### Question
A cup of coffee cools in a room. Its temperature, in degrees Celsius, is \(T(t) = 20 + 70e^{-t/10}\), where \(t\) is the time in minutes after it is poured. Find the signs of \(T'(t)\) and \(T''(t)\), and say in words how the temperature changes.

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the sign of the first derivative says whether the temperature rises or falls. The sign of the second derivative says whether the rate of change is increasing or decreasing, which tells whether the change speeds up or slows down.
1. [calc1.deriv.chain-linear-inside] Differentiate twice: \(T'(t) = -7e^{-t/10}\) in degrees per minute, and \(T''(t) = \frac{7}{10}e^{-t/10}\) in degrees per minute per minute.
   check: diff(20 + 70*e^(-t/10), t) = -7*e^(-t/10)
   check: diff(20 + 70*e^(-t/10), t, 2) = 7/10*e^(-t/10)
2. [calc1.shape.interpret-derivative-signs] Signs: the exponential is always positive, so \(T'(t) < 0\) and \(T''(t) > 0\) for every \(t\). For example, at \(t = 0\) the values are \(T'(0) = -7\) and \(T''(0) = \frac{7}{10}\).
   check: subs(-7*e^(-t/10), t, 0) = -7
   check: subs(7/10*e^(-t/10), t, 0) = 7/10
3. [calc1.shape.interpret-derivative-signs] Translate: \(T' < 0\) means the coffee is cooling. \(T'' > 0\) means \(T'\) is increasing toward zero, so the rate of cooling shrinks toward zero as \(t\) grows. The coffee keeps cooling, but more and more slowly.
   check: limit(-7*e^(-t/10), t, inf) = 0

<!-- tier 1: from words to signs -->
## Card calc1.4-5.signs-translate.001
skill: calc1.shape.interpret-derivative-signs
difficulty: 1
answer-type: choice

### Question
The population \(P(t)\) of a town, in thousands of people, is growing, but more and more slowly. Which pair of signs describes this?

### Choices
- [ ] \(P'(t) > 0\) and \(P''(t) > 0\)
- [x] \(P'(t) > 0\) and \(P''(t) < 0\)
- [ ] \(P'(t) < 0\) and \(P''(t) > 0\)
- [ ] \(P'(t) < 0\) and \(P''(t) < 0\)

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the first derivative is the rate of growth, so growing means it is positive. The second derivative is the rate of change of that rate.
1. [calc1.shape.interpret-derivative-signs] Decide: the growth is slowing, so the rate of growth is decreasing, which makes the second derivative negative. The signs are positive for the first derivative and negative for the second.

<!-- tier 1: from signs to words -->
## Card calc1.4-5.signs-reverse.001
skill: calc1.shape.interpret-derivative-signs
difficulty: 1
answer-type: choice

### Question
A company's profit \(P(t)\), in thousands of dollars, satisfies \(P'(t) < 0\) and \(P''(t) > 0\) over a period of months. Which statement describes the profit?

### Choices
- [ ] It is falling faster and faster
- [x] It is falling, but more and more slowly
- [ ] It is rising faster and faster
- [ ] It is rising, but more and more slowly

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: a negative first derivative means the profit is falling. A positive second derivative means the first derivative is increasing.
1. [calc1.shape.interpret-derivative-signs] Decide: the first derivative is negative and increasing toward zero, so the fall is getting smaller. The profit is falling, but more and more slowly.

<!-- tier 1, template: the rate of the rate -->
## Card calc1.4-5.signs-ratechange.t01
skill: calc1.shape.interpret-derivative-signs
difficulty: 1
answer-type: number
vars: u = int(4, 12); w = int(1, 3); n = int(2, 4)
require: u > w*n
answer: u - w*n
wrong: u + w*n => The second derivative is negative, so the rate of change is falling by \([[w]]\) thousand liters per day each day, so subtract that amount instead of adding it. @1; -w*n => This is only the change in the rate. The new rate is the old rate plus the change. @1

### Question
The volume of water in a tank is \(V(t)\) thousand liters, where \(t\) is the time in days. At \(t = 4\), the volume is increasing at a rate of \(V'(4) = [[u]]\) thousand liters per day, and \(V''(4) = -[[w]]\) thousand liters per day per day. Suppose \(V''\) stays equal to \(-[[w]]\) for the next [[n]] days. What is \(V'([[4 + n]])\), in thousand liters per day?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the second derivative is the rate of change of the first derivative. Here it is negative, so the rate of increase of the volume falls by a fixed amount each day.
1. [calc1.shape.interpret-derivative-signs] Compute: over \([[n]]\) days the rate changes by \([[n]] \cdot (-[[w]]) = [[-w*n]]\) thousand liters per day, so \(V'([[4 + n]]) = [[u]] - [[w*n]] = [[u - w*n]]\) thousand liters per day. The volume is still increasing, but more slowly.
   check: u + n*(-w) = u - w*n

<!-- tier 2, template: overlap of two sign intervals -->
## Card calc1.4-5.signs-intersect.t01
skill: calc1.shape.interpret-derivative-signs
difficulty: 2
answer-type: interval
endpoints: either
vars: a = int(0, 2); g = int(1, 3); k = int(1, 3); n = int(1, 3); t
let: b = a + g; c = b + k; d = c + n
answer: (b, c)
wrong: (a, c) => This is only where the revenue is increasing. It must also be increasing at a decreasing rate, which needs the second derivative to be negative as well. @2; (b, d) => This is only where the second derivative is negative. The revenue must also be increasing, which needs the first derivative to be positive. @2

### Question
A shop's monthly revenue \(R(t)\), in thousands of dollars, \(t\) months after it opens, satisfies \(R'(t) > 0\) for \([[a]] < t < [[c]]\) and \(R''(t) < 0\) for \([[b]] < t < [[d]]\). During which months is the revenue increasing at a decreasing rate?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: increasing means the first derivative is positive. Increasing at a decreasing rate means the rate of increase is itself falling, so the second derivative must be negative as well.
1. [calc1.shape.interpret-derivative-signs] Translate: both conditions must hold at once, so the answer is the overlap of the two intervals.
2. [calc1.shape.interpret-derivative-signs] Intersect: the first derivative is positive on \(([[a]], [[c]])\) and the second is negative on \(([[b]], [[d]])\). Both hold from month \([[b]]\) to month \([[c]]\), that is, on \(([[b]], [[c]])\).

<!-- tier 2: a table of signs -->
## Card calc1.4-5.signs-table.001
skill: calc1.shape.interpret-derivative-signs
difficulty: 2
answer-type: number
answer: 8
wrong: 11 => At this time the height is also falling, but the second derivative is positive, so the descent is slowing down, not speeding up. @1; 5 => At this time the height is still rising, because the first derivative is positive. @1

### Question
A drone's height is \(h(t)\) meters, \(t\) seconds after takeoff. The signs of its derivatives are: at \(t = 2\), \(h' > 0\) and \(h'' > 0\); at \(t = 5\), \(h' > 0\) and \(h'' < 0\); at \(t = 8\), \(h' < 0\) and \(h'' < 0\); at \(t = 11\), \(h' < 0\) and \(h'' > 0\). At which of these times, in seconds, is the drone descending faster and faster?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: descending means the first derivative is negative. Descending faster and faster means the first derivative is becoming more negative, so it is decreasing and the second derivative is negative.
1. [calc1.shape.interpret-derivative-signs] Match: both derivatives must be negative. That happens only at the third time listed, which is \(t = 8\).

<!-- tier 2: faster and faster means more negative -->
## Card calc1.4-5.signs-faster.001
skill: calc1.shape.interpret-derivative-signs
difficulty: 2
answer-type: truefalse
answer: false
wrong: true => Cooling faster and faster means the first derivative is becoming more negative, so it is decreasing and the second derivative is negative, not positive. @1

### Question
True or false: if a cup of coffee is cooling faster and faster, then \(T'(t) < 0\) and \(T''(t) > 0\), where \(T(t)\) is its temperature at time \(t\).

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: cooling means the first derivative is negative. Cooling faster and faster means the first derivative is becoming more negative, so it is decreasing.
1. [calc1.shape.interpret-derivative-signs] Decide: a decreasing first derivative has a negative derivative, so the second derivative is negative, not positive. The correct signs are negative and negative, so the statement is false.

<!-- tier 2: marginal cost -->
## Card calc1.4-5.signs-marginal.001
skill: calc1.shape.interpret-derivative-signs
difficulty: 2
answer-type: truefalse
answer: true
wrong: false => The marginal cost is the derivative of the cost. If it is increasing, its own derivative, the second derivative of the cost, is positive, and that means concave up. @1

### Question
True or false: if the marginal cost \(C'(x)\) of producing \(x\) items is increasing, then the cost function \(C(x)\), in dollars, is concave up.

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the marginal cost is the first derivative of the cost, and a function is concave up where its second derivative is positive.
1. [calc1.shape.interpret-derivative-signs] Decide: if the marginal cost is increasing, its derivative, the second derivative of the cost, is positive. So the cost function is concave up, and the statement is true.

<!-- tier 3, template: speeding up and slowing down -->
## Card calc1.4-5.signs-speed.t01
skill: calc1.shape.interpret-derivative-signs
difficulty: 3
answer-type: interval
endpoints: either
vars: p = int(1, 3); g = int(1, 3); k = int(1, 3); t
let: r = p + g; q = r + k
answer: (0, p) U (r, q)
wrong: (p, r) => On this interval the velocity and the acceleration are both negative, so the particle is speeding up, not slowing down. @2; (0, p) => The particle also slows down later, after the acceleration changes sign. The velocity and the acceleration have opposite signs on \(([[r]], [[q]])\) too. @2

### Question
A particle moves along a line for \(0 \le t \le [[q]]\), where \(t\) is in seconds. Its velocity \(v(t)\), in meters per second, is positive for \(0 < t < [[p]]\) and negative for \([[p]] < t < [[q]]\). Its acceleration \(a(t) = v'(t)\), in meters per second per second, is negative for \(0 < t < [[r]]\) and positive for \([[r]] < t < [[q]]\). During which time intervals is the particle slowing down?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the particle slows down when its speed is decreasing. That happens when the velocity and the acceleration have opposite signs, and it speeds up when they have the same sign.
1. [calc1.shape.interpret-derivative-signs] Compare the signs on each interval: from time 0 to time [[p]], the velocity is positive and the acceleration is negative, so the particle slows down. From time [[p]] to time [[r]], both are negative, so it speeds up. From time [[r]] to time [[q]], the velocity is negative and the acceleration is positive, so it slows down.
2. [calc1.shape.interpret-derivative-signs] Conclude: the particle is slowing down on \((0, [[p]]) \cup ([[r]], [[q]])\).

<!-- tier 3, template: a cubic model with units -->
## Card calc1.4-5.signs-cubic.t01
skill: calc1.shape.interpret-derivative-signs
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: q = int(1, 3); m = int(1, 3); t
let: r = q + 2*m; f = -t^3 + 3*m*t^2 + 3*q*r*t
answer: (m, r)
wrong: (0, r) => On this interval the number of users is increasing, but it is increasing at a decreasing rate only after the second derivative becomes negative, which is later. @3; (m, r + 2) => After \(t = [[r]]\) the number of users is decreasing, so it is not increasing on this part. @3

### Question
The number of people using an app each week, in thousands, is \(N(t) = [[tex(f)]]\) for \(0 \le t \le [[r + 2]]\), where \(t\) is the time in weeks after the release. During which weeks is the number of users increasing at a decreasing rate?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: increasing at a decreasing rate means the first derivative is positive and the second derivative is negative.
1. [calc1.deriv.power-rule] Differentiate twice: \(N'(t) = [[tex(diff(f, t))]]\) and \(N''(t) = [[tex(diff(f, t, 2))]]\).
   check: diff(f, t) = -3*t^2 + 6*m*t + 3*q*r
   check: diff(f, t, 2) = -6*t + 6*m
2. [alg.factor.polynomials] Factor: \(N'(t) = -3(t - [[r]])(t + [[q]])\).
   check: expand(-3*(t - r)*(t + q)) = -3*t^2 + 6*m*t + 3*q*r
3. [alg.inequality.sign-chart] Sign charts for \(t \ge 0\): the zeros of \(N'\) are \(t = [[r]]\) and \(t = [[-q]]\), and only the first lies in the domain. \(N'(0) = [[3*q*r]]\) is positive and \(N'([[r + 1]]) = [[-3*(r + 1 + q)]]\) is negative, so \(N' > 0\) for \(0 \le t < [[r]]\). \(N''(0) = [[6*m]]\) is positive and \(N''([[m + 1]]) = -6\) is negative, so \(N'' < 0\) for \(t > [[m]]\).
   check: subs(-3*(t - r)*(t + q), t, 0) = 3*q*r
   check: subs(-3*(t - r)*(t + q), t, r + 1) = -3*(r + 1 + q)
   check: subs(-6*t + 6*m, t, 0) = 6*m
   check: subs(-6*t + 6*m, t, m + 1) = -6
4. [calc1.shape.interpret-derivative-signs] Translate: both conditions hold when \([[m]] < t < [[r]]\), so the number of users is increasing at a decreasing rate on \(([[m]], [[r]])\).

<!-- tier 3: falling faster and faster, from a periodic model -->
## Card calc1.4-5.signs-temperature.001
skill: calc1.shape.interpret-derivative-signs
uses: calc1.deriv.trig-sin-cos, calc1.deriv.chain-linear-inside, trig.equations.solve, alg.inequality.sign-chart
difficulty: 3
answer-type: interval
endpoints: either
vars: t
answer: (12, 18)
wrong: (12, 24) => The temperature is falling on this whole interval, but falling faster and faster also needs the second derivative to be negative, which holds only until \(t = 18\). @4; (6, 18) => On \((6, 12)\) the temperature is still rising, because the first derivative is positive there. @4

### Question
The temperature outdoors, in degrees Celsius, is modeled by \(T(t) = 18 - 6\cos\left(\frac{\pi t}{12}\right)\) for \(0 \le t \le 24\), where \(t\) is the time in hours after midnight. During which hours is the temperature falling faster and faster?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: falling means the first derivative is negative. Falling faster and faster means the first derivative is becoming more negative, so it is decreasing and the second derivative is negative.
1. [calc1.deriv.trig-sin-cos] Differentiate the cosine: \((\cos u)' = -\sin u\) and \((\sin u)' = \cos u\).
   check: diff(cos(u), u) = -sin(u)
   check: diff(sin(u), u) = cos(u)
2. [calc1.deriv.chain-linear-inside] Chain rule with the linear inside \(u = \frac{\pi t}{12}\), twice: \(T'(t) = \frac{\pi}{2}\sin\left(\frac{\pi t}{12}\right)\) and \(T''(t) = \frac{\pi^2}{24}\cos\left(\frac{\pi t}{12}\right)\).
   check: diff(18 - 6*cos(pi*t/12), t) = pi/2*sin(pi*t/12)
   check: diff(18 - 6*cos(pi*t/12), t, 2) = pi^2/24*cos(pi*t/12)
3. [trig.equations.solve] Zeros in \([0, 24]\): \(T'(t) = 0\) when \(\sin\left(\frac{\pi t}{12}\right) = 0\), at \(t = 0, 12, 24\). \(T''(t) = 0\) when \(\cos\left(\frac{\pi t}{12}\right) = 0\), at \(t = 6, 18\).
   check: subs(sin(pi*t/12), t, 12) = 0
   check: subs(sin(pi*t/12), t, 24) = 0
   check: subs(cos(pi*t/12), t, 6) = 0
   check: subs(cos(pi*t/12), t, 18) = 0
4. [alg.inequality.sign-chart] Sign charts: \(T'(6) = \frac{\pi}{2}\) and \(T'(18) = -\frac{\pi}{2}\), so \(T' < 0\) on \((12, 24)\). \(T''(0) = \frac{\pi^2}{24}\), \(T''(12) = -\frac{\pi^2}{24}\) and \(T''(24) = \frac{\pi^2}{24}\), so \(T'' < 0\) on \((6, 18)\).
   check: subs(pi/2*sin(pi*t/12), t, 6) = pi/2
   check: subs(pi/2*sin(pi*t/12), t, 18) = -pi/2
   check: subs(pi^2/24*cos(pi*t/12), t, 0) = pi^2/24
   check: subs(pi^2/24*cos(pi*t/12), t, 12) = -pi^2/24
   check: subs(pi^2/24*cos(pi*t/12), t, 24) = pi^2/24
5. [calc1.shape.interpret-derivative-signs] Translate: both derivatives are negative where \((12, 24)\) and \((6, 18)\) overlap, so the temperature is falling faster and faster on \((12, 18)\).

<!-- tier 4, template: growth rate from a differential equation, with no formula for P -->
## Card calc1.4-5.signs-logistic.t01
skill: calc1.shape.interpret-derivative-signs
uses: calc1.implicit.differentiate, alg.inequality.sign-chart
difficulty: 4
answer-type: number
vars: c = int(2, 9); m = int(2, 5)
let: L = 100*c
answer: L/2
wrong: L => The growth rate \(P'\) is zero when the population reaches \([[L]]\) fish, so the growth has stopped there. The growth is fastest at a smaller population. @3; L/(4*m) => This is the largest growth rate, in fish per year. The question asks for the population size at which it happens, in fish. @3

### Question
The number of fish \(P(t)\) in a lake, \(t\) years after it is stocked, satisfies \(P'(t) = \frac{1}{[[m]]}P(t)\left(1 - \frac{P(t)}{[[L]]}\right)\), and \(0 < P(t) < [[L]]\) for all \(t\). At what population size, in fish, is the population growing fastest?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the population grows fastest where the growth rate is largest. The growth rate stops increasing and starts decreasing where the second derivative changes sign from positive to negative. There is no formula for the population, so differentiate the equation itself.
1. [calc1.implicit.differentiate] Differentiate both sides with respect to \(t\). Because \(P\) depends on \(t\), each term in \(P\) gets a factor \(P'(t)\) from the chain rule: \(P''(t) = \frac{1}{[[m]]}\left(1 - \frac{2P}{[[L]]}\right)P'(t)\).
   check: diff(P*(1 - P/L)/m, P) = (1 - 2*P/L)/m
2. [alg.inequality.sign-chart] Signs: since \(0 < P < [[L]]\), the growth rate \(P'\) is positive, so \(P''\) has the sign of \(1 - \frac{2P}{[[L]]}\). That is \(\frac{1}{2}\) at \(P = [[L/4]]\) and \(-\frac{1}{2}\) at \(P = [[3*L/4]]\), and it is zero at \(P = [[L/2]]\).
   check: subs(1 - 2*P/L, P, L/4) = 1/2
   check: subs(1 - 2*P/L, P, 3*L/4) = -1/2
   check: solve(1 - 2*P/L, P) = {L/2}
3. [calc1.shape.interpret-derivative-signs] Conclude: \(P'' > 0\) while the population is below \([[L/2]]\) fish, so the growth speeds up, and \(P'' < 0\) above it, so the growth slows down. The growth is fastest when the population is \(P = [[L/2]]\) fish.

<!-- tier 4: concentration of a drug, with units -->
## Card calc1.4-5.signs-drug.001
skill: calc1.shape.interpret-derivative-signs
uses: calc1.deriv.chain-linear-inside, calc1.deriv.product-rule, alg.solve.linear, alg.inequality.sign-chart
difficulty: 4

### Question
The concentration of a drug in the blood, in milligrams per liter, is \(C(t) = te^{-t/2}\), where \(t \ge 0\) is the time in hours after the injection.

### Part a
answer-type: number
answer: 2
wrong: 4 => At this time the concentration is already falling. The highest concentration is where the first derivative changes from positive to negative. @4
At what time, in hours, is the concentration the highest?

### Part b
answer-type: number
answer: 4
wrong: 2 => At this time the first derivative is zero, so the concentration has just stopped rising. It falls most rapidly later, where the second derivative changes sign. @4
At what time, in hours, is the concentration falling most rapidly?

### Part c
answer-type: number
answer: e^(-2)
wrong: -e^(-2) => The rate of change is negative because the concentration is falling. The question asks how fast it falls, which is the size of that rate. @5
How fast is the concentration falling at that time, in milligrams per liter per hour?

### Solution
0. [calc1.shape.interpret-derivative-signs] Set up: the concentration is highest where the first derivative changes from positive to negative. It falls most rapidly where the first derivative is most negative, which is where the second derivative changes sign from negative to positive.
1. [calc1.deriv.chain-linear-inside] Differentiate the exponential: \(\frac{d}{dt}e^{-t/2} = -\frac{1}{2}e^{-t/2}\).
   check: diff(e^(-t/2), t) = -1/2*e^(-t/2)
2. [calc1.deriv.product-rule] Differentiate twice with the product rule: \(C'(t) = \left(1 - \frac{t}{2}\right)e^{-t/2}\) and \(C''(t) = \left(\frac{t}{4} - 1\right)e^{-t/2}\).
   check: diff(t*e^(-t/2), t) = (1 - t/2)*e^(-t/2)
   check: diff((1 - t/2)*e^(-t/2), t) = (t/4 - 1)*e^(-t/2)
3. [alg.solve.linear] Zeros: the exponential is never zero, so \(C'(t) = 0\) when \(1 - \frac{t}{2} = 0\), at \(t = 2\), and \(C''(t) = 0\) when \(\frac{t}{4} - 1 = 0\), at \(t = 4\).
   check: solve(1 - t/2, t) = {2}
   check: solve(t/4 - 1, t) = {4}
4. [alg.inequality.sign-chart] Sign charts: \(C'(1) = \frac{1}{2}e^{-1/2}\) is positive and \(C'(3) = -\frac{1}{2}e^{-3/2}\) is negative, so \(C'\) changes from positive to negative at \(t = 2\). \(C''(3) = -\frac{1}{4}e^{-3/2}\) is negative and \(C''(5) = \frac{1}{4}e^{-5/2}\) is positive, so \(C''\) changes from negative to positive at \(t = 4\).
   check: subs((1 - t/2)*e^(-t/2), t, 1) = 1/2*e^(-1/2)
   check: subs((1 - t/2)*e^(-t/2), t, 3) = -1/2*e^(-3/2)
   check: subs((t/4 - 1)*e^(-t/2), t, 3) = -1/4*e^(-3/2)
   check: subs((t/4 - 1)*e^(-t/2), t, 5) = 1/4*e^(-5/2)
5. [calc1.shape.interpret-derivative-signs] Interpret: the concentration is highest at \(t = 2\) hours. After that it falls, with \(C'' < 0\) until \(t = 4\), so it falls faster and faster until then and more slowly afterwards. It falls most rapidly at \(t = 4\) hours, at the rate \(C'(4) = -e^{-2}\) milligrams per liter per hour, that is, \(e^{-2}\) milligrams per liter per hour.
   check: subs((1 - t/2)*e^(-t/2), t, 4) = -e^(-2)
