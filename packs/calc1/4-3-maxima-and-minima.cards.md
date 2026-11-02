---
format: mastery-cards 1
deck: Calculus I::4 Applications of Derivatives::4.3 Maxima and Minima
source: original
license: CC BY-NC-SA 4.0
---

<!-- Section 4.3 Maxima and Minima: three skills, one worked example each, twelve problems each.
     Local extremum = a point that is highest (or lowest) among all nearby points on BOTH sides,
     so an endpoint is never a local extremum here (it can still be an absolute one).
     Critical number = a number in the domain of f where f' is zero or does not exist (OpenStax).
     Provenance: adapted cards name their source; every other card is original. -->


<!-- ===================================================================== -->
<!-- calc1.extrema.from-graph                                              -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-3.graph-example.001
kind: example
skill: calc1.extrema.from-graph
plot: x^4 - 8x^2, x = -3..3

### Question
The graph of \(f\) is shown on \([-3, 3]\). Find the absolute and the local extrema of \(f\) on this interval.

### Solution
0. [calc1.extrema.from-graph] Set up: an absolute extremum is the highest or lowest point of the whole graph, endpoints included. A local extremum is a point that is highest or lowest among all nearby points on both sides of it, so an endpoint is never a local extremum.
1. [calc1.extrema.from-graph] Highest points: the graph rises to height \(9\) at both ends, so the absolute maximum value is \(9\), reached at \(x = -3\) and at \(x = 3\).
   check: subs(x^4 - 8*x^2, x, 3) = 9
   check: subs(x^4 - 8*x^2, x, -3) = 9
2. [calc1.extrema.from-graph] Lowest points: the two valleys bottom out at height \(-16\), so the absolute minimum value is \(-16\), reached at \(x = -2\) and at \(x = 2\). These valleys are also local minima.
   check: subs(x^4 - 8*x^2, x, 2) = -16
   check: subs(x^4 - 8*x^2, x, -2) = -16
3. [calc1.extrema.from-graph] The hilltop between the valleys: \(f\) has a local maximum at \(x = 0\) with \(f(0) = 0\). It is not an absolute maximum, because the graph is higher near both ends.
   check: subs(x^4 - 8*x^2, x, 0) = 0

<!-- tier 1, template: read the peak of a downward parabola -->
## Card calc1.4-3.graph-peak.t01
skill: calc1.extrema.from-graph
difficulty: 1
answer-type: point
vars: h = int(-2, 2); c = int(1, 4)
require: c != h
let: f = c - (x - h)^2
answer: (h, c)
wrong: (c, h) => A point is written (x, y): give the x-coordinate first. @2; (h - 3, c - 9) => That is the left end of the graph, one of its lowest points. The question asks for the highest point. @1
plot: [[f]], x = [[h - 3]]..[[h + 3]]

### Question
The graph of \(f\) is shown on \(\left[ [[h - 3]], [[h + 3]] \right]\). Find the point where \(f\) has its absolute maximum.

### Hints
1. The absolute maximum is the highest point of the whole graph.
2. Read both the \(x\)-coordinate and the height of that point.

### Solution
0. [calc1.extrema.from-graph] Set up: the absolute maximum is the highest point of the whole graph.
1. [calc1.extrema.from-graph] Read: the graph peaks at \(x = [[h]]\), and the height there is \(f([[h]]) = [[c]]\).
   check: subs(f, x, h) = c
2. [calc1.extrema.from-graph] Answer: the highest point is \(P = ([[h]], [[c]])\).

<!-- tier 1: local minima of a W-shaped graph, endpoints excluded by the question -->
## Card calc1.4-3.graph-local-min.001
skill: calc1.extrema.from-graph
difficulty: 1
answer-type: set
answer: -1, 1
wrong: 0 => The point x = 0 is the top of the hill between the two valleys, a local maximum. @1; 1 => There are two valleys, so two local minima. @1; -2, -1, 1, 2 => The question asks only about x-values strictly between -2 and 2. @1
plot: x^4 - 2x^2, x = -2..2

### Question
The graph of \(f\) is shown on \([-2, 2]\). List every \(x\)-value strictly between \(-2\) and \(2\) at which \(f\) has a local minimum.

### Hints
1. A local minimum is the bottom of a valley: the graph is higher on both sides nearby.

### Solution
0. [calc1.extrema.from-graph] Set up: a local minimum is a point lower than all nearby points on both sides.
1. [calc1.extrema.from-graph] Read: the graph has two valleys, with bottoms at \(x = -1\) and \(x = 1\), both at height \(-1\). Between them, \(x = 0\) is the top of a hill.
   check: subs(x^4 - 2*x^2, x, 1) = -1
   check: subs(x^4 - 2*x^2, x, -1) = -1
   check: subs(x^4 - 2*x^2, x, 0) = 0
2. [calc1.extrema.from-graph] Answer: the local minima are at \(x = -1\) and \(x = 1\).
   check: {-1, 1} = {-1, 1}

<!-- tier 1: absolute minimum VALUE, reached at two places -->
## Card calc1.4-3.graph-min-value.001
skill: calc1.extrema.from-graph
difficulty: 1
answer-type: number
answer: -2
wrong: 1 => That is an x-value where the lowest height occurs. The absolute minimum value is the height, the y-value. @1; 2 => That is the greatest height of the graph, the absolute maximum value. The minimum value is the lowest height. @1
plot: x^3 - 3x, x = -2..2

### Question
The graph of \(f\) is shown on \([-2, 2]\). What is the absolute minimum value of \(f\) on this interval?

### Hints
1. Find the lowest point of the whole graph, endpoints included.
2. The value is the height of that point, not its \(x\)-coordinate.

### Solution
0. [calc1.extrema.from-graph] Set up: the absolute minimum value is the height of the lowest point of the whole graph.
1. [calc1.extrema.from-graph] Read: the lowest height is \(-2\). It is reached at the left end \(x = -2\) and again at the valley \(x = 1\), so the absolute minimum value is \(-2\).
   check: subs(x^3 - 3*x, x, -2) = -2
   check: subs(x^3 - 3*x, x, 1) = -2

<!-- tier 1, template: the maximum is at an endpoint, not at the flat spot -->
## Card calc1.4-3.graph-endpoint-max.t01
skill: calc1.extrema.from-graph
difficulty: 1
answer-type: number
vars: h = int(-2, 2); c = int(-3, 3)
let: f = (x - h)^3 + c
answer: h + 2
wrong: h => The graph flattens at this x-value but keeps rising through it, so it is not the highest point. @1; h - 2 => That is the lowest point, the left end. @1
plot: [[f]], x = [[h - 2]]..[[h + 2]]

### Question
The graph of \(f\) is shown on \(\left[ [[h - 2]], [[h + 2]] \right]\). At which \(x\)-value does \(f\) have its absolute maximum?

### Hints
1. The absolute maximum is the highest point of the whole graph, and it can be an endpoint.

### Solution
0. [calc1.extrema.from-graph] Set up: the absolute maximum is the highest point of the whole graph, and it can be an endpoint.
1. [calc1.extrema.from-graph] Read: the graph rises from left to right and only flattens for a moment at \(x = [[h]]\). Its highest point is the right end, \(x = [[h + 2]]\), where \(f = [[c + 8]]\).
   check: subs(f, x, h + 2) = c + 8
   check: subs(f, x, h) = c
2. [calc1.extrema.from-graph] Answer: the absolute maximum occurs at \(x = [[h + 2]]\).
   check: h + 2 = h + 2

<!-- tier 2: the valley is only local; the left end is lower -->
## Card calc1.4-3.graph-local-min-trap.001
skill: calc1.extrema.from-graph
difficulty: 2
answer-type: number
answer: -16
wrong: 0 => That is the bottom of the valley at x = 3, only a local minimum. The graph is lower at the left end. @1; -1 => That is the x-value where the lowest height occurs. The minimum value is the height. @1
plot: x*(x - 3)^2, x = -1..4

### Question
The graph of \(f\) is shown on \([-1, 4]\). Find the absolute minimum value of \(f\) on this interval.

### Hints
1. Compare the bottom of the valley with the heights at the two ends.

### Solution
0. [calc1.extrema.from-graph] Set up: the absolute minimum is the lowest point of the whole graph, so compare every valley bottom and both ends.
1. [calc1.extrema.from-graph] Read: the valley at \(x = 3\) has height \(0\), but the graph starts lower, at the left end \(x = -1\), with height \(-16\). The right end is at height \(4\).
   check: subs(x*(x - 3)^2, x, 3) = 0
   check: subs(x*(x - 3)^2, x, 4) = 4
   check: subs(x*(x - 3)^2, x, -1) = -16

<!-- tier 2: corners can be extrema -->
## Card calc1.4-3.graph-corner-count.001
skill: calc1.extrema.from-graph
difficulty: 2
answer-type: number
answer: 3
wrong: 0 => A corner has no horizontal tangent, but a corner can still be a local extremum. @1; 2 => The hilltop at x = 0 also counts. @1
plot: abs(abs(x) - 2), x = -4..4

### Question
The graph of \(f\) is shown on \([-4, 4]\). How many \(x\)-values strictly between \(-4\) and \(4\) give a local extremum of \(f\)?

### Hints
1. Look for the tops of hills and the bottoms of valleys, sharp or smooth.

### Solution
0. [calc1.extrema.from-graph] Set up: a local extremum is the top of a hill or the bottom of a valley among nearby points, even where the graph has a sharp corner.
1. [calc1.extrema.from-graph] Read: the graph has a valley bottom at \(x = -2\) (height \(0\)), a hilltop at \(x = 0\) (height \(2\)) and a valley bottom at \(x = 2\) (height \(0\)). All three are corners.
   check: subs(abs(abs(x) - 2), x, -2) = 0
   check: subs(abs(abs(x) - 2), x, 0) = 2
   check: subs(abs(abs(x) - 2), x, 2) = 0
2. [calc1.extrema.from-graph] Count: one hilltop and two valleys give three local extrema.
   check: 1 + 2 = 3

<!-- tier 2: an open interval -->
## Card calc1.4-3.graph-open-interval.001
skill: calc1.extrema.from-graph
difficulty: 2
answer-type: number
answer: DNE
wrong: 4 => The graph gets close to height 4 at both ends, but x = -1 and x = 3 are not in the open interval, so height 4 is never reached. @1; 0 => That is the absolute minimum value, reached at x = 1. The question asks for the maximum. @1
plot: (x - 1)^2, x = -1..3

### Question
The graph of \(f\) is shown over the open interval \((-1, 3)\). Find the absolute maximum value of \(f\) on \((-1, 3)\), or enter DNE if there is none.

### Hints
1. Are the endpoints of an open interval part of the interval?

### Solution
0. [calc1.extrema.from-graph] Set up: an absolute maximum is a highest point that the graph actually reaches inside the interval. Endpoints of an open interval are not in the interval.
1. [calc1.extrema.from-graph] Read: the graph gets close to height \(4\) near both ends, because \(f(-1) = 4\) and \(f(3) = 4\), but those points are not in \((-1, 3)\). Every height actually reached is below \(4\), and there is no highest one, so the absolute maximum does not exist.
   check: subs((x - 1)^2, x, -1) = 4
   check: subs((x - 1)^2, x, 3) = 4
   check: DNE = DNE

<!-- tier 2, template: the local maximum is not the highest point -->
## Card calc1.4-3.graph-cubic-range.t01
skill: calc1.extrema.from-graph
difficulty: 2
answer-type: list
vars: c = int(-4, 4)
let: f = x^3 - 3*x + c
answer: c - 2, c + 18
wrong: c - 2, c + 2 => The hill at x = -1 is only a local maximum. The graph keeps rising to a greater height at the right end. @2; c + 18, c - 2 => Give the minimum first, then the maximum. @3
plot: [[f]], x = -2..3

### Question
The graph of \(f\) is shown on \([-2, 3]\). Give the absolute minimum value and the absolute maximum value of \(f\) on this interval, in that order.

### Hints
1. Compare the heights at both ends with the hilltop and the valley bottom.

### Solution
0. [calc1.extrema.from-graph] Set up: read the lowest and the highest height of the whole graph, endpoints included.
1. [calc1.extrema.from-graph] Lowest point: the lowest height is \([[c - 2]]\). It is reached at the left end \(x = -2\) and again at the valley \(x = 1\).
   check: subs(f, x, -2) = c - 2
   check: subs(f, x, 1) = c - 2
2. [calc1.extrema.from-graph] Highest point: the hill at \(x = -1\) has height \([[c + 2]]\), but the graph keeps rising to height \([[c + 18]]\) at the right end \(x = 3\).
   check: subs(f, x, -1) = c + 2
   check: subs(f, x, 3) = c + 18
3. [calc1.extrema.from-graph] Answer: the absolute minimum value is \([[c - 2]]\) and the absolute maximum value is \([[c + 18]]\).
   check: {c - 2, c + 18} = {c - 2, c + 18}

<!-- tier 2: count the extrema of a periodic graph -->
## Card calc1.4-3.graph-sine-count.001
skill: calc1.extrema.from-graph
difficulty: 2
answer-type: number
answer: 6
wrong: 3 => That counts only the hilltops. Each valley bottom is a local minimum, so it is a local extremum too. @1; 8 => The question counts only x-values strictly between 0 and 6pi, so the two ends of the interval do not count. @1
plot: sin(x), x = 0..6*pi

### Question
The graph of \(f\) is shown on \([0, 6\pi]\) and shows three full waves. How many \(x\)-values strictly between \(0\) and \(6\pi\) give a local extremum of \(f\)?

### Hints
1. Count the hilltops and the valley bottoms separately, then add.

### Solution
0. [calc1.extrema.from-graph] Set up: count every hilltop (local maximum) and every valley bottom (local minimum) strictly inside the interval.
1. [calc1.extrema.from-graph] Read: each wave has one hilltop of height \(1\) and one valley of height \(-1\). The hilltops are at \(x = \frac{\pi}{2}, \frac{5\pi}{2}, \frac{9\pi}{2}\) and the valleys at \(x = \frac{3\pi}{2}, \frac{7\pi}{2}, \frac{11\pi}{2}\).
   check: subs(sin(x), x, 5*pi/2) = 1
   check: subs(sin(x), x, 9*pi/2) = 1
   check: subs(sin(x), x, 7*pi/2) = -1
   check: subs(sin(x), x, 11*pi/2) = -1
2. [calc1.extrema.from-graph] Count: three hilltops and three valleys give six local extrema.
   check: 3 + 3 = 6

<!-- tier 3, adapted from CLP-1: a flat spot that is not an extremum, and a sharp peak -->
## Card calc1.4-3.graph-flat-and-peak.001
skill: calc1.extrema.from-graph
difficulty: 3
answer-type: set
answer: 2
wrong: 0, 2 => At x = 0 the tangent is flat, but the graph keeps rising through that point, so x = 0 is not a local extremum. @1; 0 => At x = 0 the tangent is flat, but the graph keeps rising through it. The sharp peak at x = 2 is the local maximum. @1
plot: x^3/4 + 2, x = -2.5..2; 3*(x - 3)^2 + 1, x = 2..2.5; 3*e^(-4*(x - 5/2))/4 + 1, x = 2.5..3.1
source: CLP-1 Differential Calculus problem book (Feldman, Rechnitzer, Yeager), Section 3.5.1, question 1
source-url: https://github.com/arechnitzer/CLP1/blob/9f0295936d395bec68dab7915057135a2c7f0414/latex/problembook/problems/prob_s3.5.1.tex
license: CC BY-NC-SA 4.0
modified: yes

### Question
The graph of \(f\) is shown on \([-2.5, 3.1]\). List every \(x\)-value strictly between \(-2.5\) and \(3.1\) at which \(f\) has a local extremum.

### Hints
1. A flat tangent does not guarantee an extremum: check whether the graph turns around.
2. A sharp peak is a local maximum even though there is no tangent line.

### Solution
0. [calc1.extrema.from-graph] Set up: a local extremum is a point where the graph turns around, from rising to falling or the reverse. It does not matter whether the tangent is flat, sloped or missing.
1. [calc1.extrema.from-graph] The flat spot: near \(x = 0\) the graph follows \(f(x) = \frac{x^3}{4} + 2\), which has slope \(0\) at \(x = 0\) but is increasing on both sides. The graph does not turn around, so there is no extremum.
   check: subs(diff(x^3/4 + 2, x), x, 0) = 0
   check: diff(x^3/4 + 2, x) = 3*x^2/4
2. [calc1.extrema.from-graph] The sharp peak: at \(x = 2\) the slope is \(3\) from the left and \(-6\) from the right, and the height is \(f(2) = 4\). The graph rises to the peak and then falls, so \(f\) has a local maximum there.
   check: subs(diff(x^3/4 + 2, x), x, 2) = 3
   check: subs(diff(3*(x - 3)^2 + 1, x), x, 2) = -6
   check: subs(x^3/4 + 2, x, 2) = 4
   check: subs(3*(x - 3)^2 + 1, x, 2) = 4
3. [calc1.extrema.from-graph] Answer: the only local extremum inside the interval is at \(x = 2\).
   check: {2} = {2}

<!-- tier 3, template: corners at the bottom of the valleys -->
## Card calc1.4-3.graph-abs-valley.t01
skill: calc1.extrema.from-graph
difficulty: 3
answer-type: set
vars: k = int(1, 3); c = int(-2, 2)
let: f = abs(x^2 - k^2) + c
answer: -k, 0, k
wrong: 0 => The point x = 0 is the only place with a flat tangent, but the sharp corners at x = -[[k]] and x = [[k]] are valley bottoms, so they are local minima too. @1; -2*k, -k, 0, k, 2*k => The question asks only about x-values strictly between -[[2*k]] and [[2*k]]. @3
plot: [[f]], x = [[-2*k]]..[[2*k]]

### Question
The graph of \(f\) is shown on \(\left[ [[-2*k]], [[2*k]] \right]\). List every \(x\)-value strictly between \([[-2*k]]\) and \([[2*k]]\) at which \(f\) has a local extremum.

### Hints
1. Look at every hilltop and every valley bottom, including the sharp ones.

### Solution
0. [calc1.extrema.from-graph] Set up: a local extremum is the top of a hill or the bottom of a valley among nearby points, whether the graph is smooth or has a sharp corner there.
1. [calc1.extrema.from-graph] The corners: the graph comes down to height \([[c]]\) at \(x = -[[k]]\) and at \(x = [[k]]\) and is higher on both sides. The slopes on the two sides of \(x = [[k]]\) are \(-[[2*k]]\) and \([[2*k]]\), so each is a sharp corner and a valley bottom.
   check: subs(f, x, k) = c
   check: subs(f, x, -k) = c
   check: subs(diff(k^2 - x^2 + c, x), x, k) = -2*k
   check: subs(diff(x^2 - k^2 + c, x), x, k) = 2*k
2. [calc1.extrema.from-graph] The smooth hilltop: between the corners the graph rises to height \(f(0) = [[k^2 + c]]\) and then falls, so \(x = 0\) is a local maximum.
   check: subs(f, x, 0) = k^2 + c
3. [calc1.extrema.from-graph] Answer: the local extrema inside the interval are at \(x = -[[k]]\), \(x = 0\) and \(x = [[k]]\).
   check: {-k, 0, k} = {-k, 0, k}

<!-- tier 3: a cusp is the highest point -->
## Card calc1.4-3.graph-cusp.001
skill: calc1.extrema.from-graph
difficulty: 3
answer-type: list
answer: -1, 3
wrong: -1, -1 => The sharp point at x = 0 is the highest point of the graph. Extrema can occur where the graph has no tangent line. @2; 3, -1 => Give the minimum first, then the maximum. @3
plot: 3 - root(x, 3)^2, x = -8..8

### Question
The graph of \(f\) is shown on \([-8, 8]\). Give the absolute minimum value and the absolute maximum value of \(f\) on this interval, in that order.

### Hints
1. There is no horizontal tangent anywhere, but extrema do not need one.
2. Check the ends and the sharp point.

### Solution
0. [calc1.extrema.from-graph] Set up: read the lowest and the highest height of the whole graph. A sharp point can be an extremum, and so can an endpoint.
1. [calc1.extrema.from-graph] Lowest point: the graph falls away on both sides of the sharp point and reaches height \(-1\) at both ends, \(x = -8\) and \(x = 8\).
   check: subs(3 - root(x, 3)^2, x, -8) = -1
   check: subs(3 - root(x, 3)^2, x, 8) = -1
2. [calc1.extrema.from-graph] Highest point: the sharp point at \(x = 0\) is the top of the graph, at height \(f(0) = 3\). Nearby points, such as \(x = \pm 1\) at height \(2\), are lower.
   check: subs(3 - root(x, 3)^2, x, 0) = 3
   check: subs(3 - root(x, 3)^2, x, 1) = 2
3. [calc1.extrema.from-graph] Answer: the absolute minimum value is \(-1\) and the absolute maximum value is \(3\).
   check: {-1, 3} = {-1, 3}


<!-- ===================================================================== -->
<!-- calc1.extrema.critical-numbers                                        -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-3.crit-example.001
kind: example
skill: calc1.extrema.critical-numbers
uses: pre.functions.domain, calc1.deriv.power-rule-rational, alg.factor.lowest-power

### Question
Find all critical numbers of \(f(x) = x^{4/3} - 4x^{1/3}\).

### Solution
0. [calc1.extrema.critical-numbers] Set up: a critical number is a number in the domain of the function where its derivative is zero or does not exist. Find the derivative, then look for both kinds of points.
1. [pre.functions.domain] Domain: cube roots exist for every real number, so the function is defined everywhere, including at zero.
2. [calc1.deriv.power-rule-rational] Differentiate: \(f'(x) = \frac{4}{3}x^{1/3} - \frac{4}{3}x^{-2/3}\).
   check: diff(u^4 - 4*u, u)/diff(u^3, u) = (4*u^3 - 4)/(3*u^2)
   check: 4/3*u - 4/3*u^(-2) = (4*u^3 - 4)/(3*u^2)
3. [alg.factor.lowest-power] Factor out the lowest power: \(f'(x) = \frac{4}{3}x^{-2/3}(x - 1) = \frac{4(x - 1)}{3x^{2/3}}\).
   check: 4/3*u^(-2)*(u^3 - 1) = 4/3*u - 4/3*u^(-2)
4. [calc1.extrema.critical-numbers] Critical numbers: the numerator is zero at \(x = 1\), and \(f'\) does not exist at \(x = 0\), which is in the domain. So the critical numbers are \(x = 0\) and \(x = 1\).
   check: solve(u^3 - 1, u) = {1}

<!-- tier 1, template: quadratic, one linear equation -->
## Card calc1.4-3.crit-quad.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule, alg.solve.linear
difficulty: 1
answer-type: set
vars: a = choice(1, 2, 3, -1, -2, -3); h = int(-4, 4, not 0); k = int(-5, 5)
require: k != h; k != -h; k != 2*h
let: f = a*(x - h)^2 + k; g = expand(f)
answer: h
wrong: -h => Check the sign when you solve for x. @2; k => That is the height of the vertex, f at the critical number. A critical number is an x-value. @3; 2*h => The derivative of ax^2 is 2ax, not ax. @1

### Question
Find all critical numbers of \(f(x) = [[tex(g)]]\).

### Hints
1. Differentiate, then find where \(f'(x) = 0\).

### Solution
0. [calc1.extrema.critical-numbers] Set up: the function is a polynomial, so its derivative exists everywhere and the critical numbers are the zeros of the derivative.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(diff(g, x))]]\).
   check: diff(g, x) = 2*a*x - 2*a*h
2. [alg.solve.linear] Solve \(f'(x) = 0\): \(x = [[h]]\).
   check: solve(2*a*x - 2*a*h, x) = {h}
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the only critical number is \(x = [[h]]\).
   check: {h} = {h}

<!-- tier 1, template: f' is given in factored form -->
## Card calc1.4-3.crit-factored.t01
skill: calc1.extrema.critical-numbers
uses: alg.solve.polynomial
difficulty: 1
answer-type: set
vars: r = int(1, 5); s = int(1, 5)
answer: -r, s
wrong: -r => The factor (x - [[s]])^2 is also zero, at x = [[s]], so f' = 0 there too. @1; r, s => The factor x + [[r]] is zero at x = -[[r]], not at x = [[r]]. @1

### Question
A function \(f\) is defined for all real numbers and \(f'(x) = (x + [[r]])(x - [[s]])^2\). Find all critical numbers of \(f\).

### Hints
1. A product is zero when one of its factors is zero.

### Solution
0. [calc1.extrema.critical-numbers] Set up: the derivative exists for every number, so the critical numbers are exactly the zeros of the derivative.
1. [alg.solve.polynomial] Zero-product rule: \((x + [[r]])(x - [[s]])^2 = 0\) when \(x = -[[r]]\) or \(x = [[s]]\).
   check: solve((x + r)*(x - s)^2, x) = {-r, s}

<!-- tier 1: no critical numbers -->
## Card calc1.4-3.crit-none.001
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule
difficulty: 1
answer-type: set
answer: none
wrong: 0 => f'(0) = 3, not 0. Set f' equal to zero, not f. @2; 1, -1 => 3x^2 + 3 = 0 would need x^2 = -1, which has no real solution. @2

### Question
Find all critical numbers of \(f(x) = x^3 + 3x\). Enter none if there are no critical numbers.

### Hints
1. Differentiate and ask whether \(f'(x) = 0\) can happen.

### Solution
0. [calc1.extrema.critical-numbers] Set up: the function is a polynomial, so its derivative exists everywhere. Critical numbers are the zeros of the derivative, if there are any.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 + 3\).
   check: diff(x^3 + 3*x, x) = 3*x^2 + 3
2. [calc1.extrema.critical-numbers] Zeros of \(f'\): \(3x^2 + 3 \ge 3\) for every \(x\), so \(f'(x)\) is never \(0\). There are no critical numbers.
   check: solve(3*x^2 + 3, x) = none

<!-- tier 2, template: cubic whose derivative factors -->
## Card calc1.4-3.crit-poly.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial
difficulty: 2
answer-type: set
vars: a = int(1, 5); b = int(2, 6)
require: a < b
let: f = 2*x^3 - 3*(a + b)*x^2 + 6*a*b*x
answer: a, b
wrong: -a, -b => The factor x - [[a]] is zero at x = [[a]], not at x = -[[a]]. @3; a => Each factor of f' gives a critical number, so there are two. @3

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Hints
1. Differentiate, factor out the common factor of \(f'\), then factor the quadratic.

### Solution
0. [calc1.extrema.critical-numbers] Set up: the function is a polynomial, so its derivative exists everywhere. Find the zeros of the derivative.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(diff(f, x))]]\).
   check: diff(f, x) = 6*x^2 - 6*(a + b)*x + 6*a*b
2. [alg.factor.polynomials] Factor: \(f'(x) = 6(x - [[a]])(x - [[b]])\).
   check: expand(6*(x - a)*(x - b)) = 6*x^2 - 6*(a + b)*x + 6*a*b
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = [[a]]\) or \(x = [[b]]\).
   check: solve(6*(x - a)*(x - b), x) = {a, b}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers are \(x = [[a]]\) and \(x = [[b]]\).
   check: {a, b} = {a, b}

<!-- tier 2, template: simple rational function, quotient rule -->
## Card calc1.4-3.crit-rational.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.quotient-rule, alg.factor.polynomials, alg.solve.polynomial, pre.functions.domain
difficulty: 2
answer-type: set
vars: k = int(1, 6)
let: f = x/(x^2 + k^2)
answer: -k, k
wrong: k => The numerator [[k^2]] - x^2 is zero at both x = [[k]] and x = -[[k]]. @3; 0 => x = 0 is a zero of f, not of f'. Differentiate first, then set f' equal to zero. @1

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Hints
1. Use the quotient rule. A fraction is zero when its numerator is zero.

### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers are where the derivative is zero or does not exist, in the domain of the function. Differentiate first.
1. [calc1.deriv.quotient-rule] Quotient rule: \(f'(x) = \frac{(x^2 + [[k^2]])(1) - x(2x)}{(x^2 + [[k^2]])^2} = \frac{[[k^2]] - x^2}{(x^2 + [[k^2]])^2}\).
   check: diff(f, x) = (k^2 - x^2)/(x^2 + k^2)^2
2. [alg.factor.polynomials] Factor the numerator, a difference of squares: \([[k^2]] - x^2 = ([[k]] - x)([[k]] + x)\).
   check: expand((k - x)*(k + x)) = k^2 - x^2
3. [alg.solve.polynomial] Zeros of \(f'\): the numerator is zero at \(x = [[k]]\) and \(x = -[[k]]\).
   check: solve(k^2 - x^2, x) = {-k, k}
4. [pre.functions.domain] Where \(f'\) does not exist: the denominator \((x^2 + [[k^2]])^2\) is never zero, so \(f'\) exists for every real \(x\).
   check: solve(x^2 + k^2, x) = none
5. [calc1.extrema.critical-numbers] Critical numbers: \(x = -[[k]]\) and \(x = [[k]]\).
   check: {-k, k} = {-k, k}

<!-- tier 2, template: product of x and an exponential -->
## Card calc1.4-3.crit-exp.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.product-rule, calc1.deriv.chain-linear-inside, alg.factor.polynomials, alg.solve.linear
difficulty: 2
answer-type: set
vars: k = int(2, 9)
let: f = x*e^(-x/k)
answer: k
wrong: 0 => This forgets the product rule: x is not a constant factor, so the term (x)' e^(-x/[[k]]) is part of f' too. @1; -k => The chain rule gives (e^(-x/[[k]]))' = -(1/[[k]]) e^(-x/[[k]]): keep the minus sign. @2

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Hints
1. Use the product rule. The derivative of \(e^{-x/[[k]]}\) needs a chain-rule factor.

### Solution
0. [calc1.extrema.critical-numbers] Set up: the function is defined and differentiable for every number, so the critical numbers are the zeros of its derivative.
1. [calc1.deriv.product-rule] Product rule: \(f'(x) = (1)e^{-x/[[k]]} + x\left(e^{-x/[[k]]}\right)'\).
   check: diff(f, x) = e^(-x/k) + x*diff(e^(-x/k), x)
2. [calc1.deriv.chain-linear-inside] Chain rule with a linear inside: \(\left(e^{-x/[[k]]}\right)' = -\frac{1}{[[k]]}e^{-x/[[k]]}\).
   check: diff(e^(-x/k), x) = -1/k*e^(-x/k)
3. [alg.factor.polynomials] Factor out the common factor: \(f'(x) = e^{-x/[[k]]}\left(1 - \frac{x}{[[k]]}\right)\).
   check: e^(-x/k)*(1 - x/k) = e^(-x/k) + x*(-1/k)*e^(-x/k)
4. [alg.solve.linear] Solve \(f'(x) = 0\): \(e^{-x/[[k]]}\) is never zero, so \(1 - \frac{x}{[[k]]} = 0\) and \(x = [[k]]\).
   check: solve(1 - x/k, x) = {k}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the only critical number is \(x = [[k]]\).
   check: {k} = {k}

<!-- tier 2, template: the logarithm excludes x = 0 from the domain -->
## Card calc1.4-3.crit-log.t01
skill: calc1.extrema.critical-numbers
uses: pre.functions.domain, calc1.deriv.logarithm, alg.solve.rational-equation
difficulty: 2
answer-type: set
vars: k = int(2, 7)
let: f = x - k*ln(x)
answer: k
wrong: 0, k => f' does not exist at x = 0, but f is not defined there either, so 0 is not a critical number. @4; 1/k => Multiply 1 - [[k]]/x = 0 by x to get x - [[k]] = 0, so x = [[k]]. @3

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Hints
1. Find the domain of \(f\) first.
2. A critical number must be in the domain.

### Solution
0. [calc1.extrema.critical-numbers] Set up: a critical number must be in the domain of the function, with the derivative zero or undefined there.
1. [pre.functions.domain] Domain: a logarithm needs a positive input, so the domain of the function is all numbers greater than zero.
2. [calc1.deriv.logarithm] Differentiate: \(f'(x) = 1 - \frac{[[k]]}{x}\).
   check: diff(f, x) = 1 - k/x
3. [alg.solve.rational-equation] Solve \(f'(x) = 0\): multiply by \(x\) (note \(x \ne 0\)) to get \(x - [[k]] = 0\), so \(x = [[k]]\).
   check: solve(1 - k/x, x) = {k}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'(x) = 0\) at \(x = [[k]]\), which is in the domain. \(f'\) does not exist at \(x = 0\), but \(0\) is not in the domain of \(f\). So the only critical number is \(x = [[k]]\).
   check: {k} = {k}

<!-- tier 3, template: trig equation on an interval -->
## Card calc1.4-3.crit-trig.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.trig-sin-cos, trig.equations.solve
difficulty: 3
answer-type: set
vars: b = choice(2, -2); c = int(-4, 4)
let: f = x + b*sin(x) + c; p = arccos(-1/b); q = 2*pi - arccos(-1/b)
answer: p, q
wrong: p => Cosine takes each value between -1 and 1 twice in (0, 2pi). There are two critical numbers. @2; arccos(1/b), 2*pi - arccos(1/b) => Check the sign: f' = 0 gives cos x = [[-1/b]], not cos x = [[1/b]]. @2

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\) in the interval \((0, 2\pi)\).

### Hints
1. Differentiate and solve \(f'(x) = 0\) for \(\cos x\).
2. The cosine takes each value in \((-1, 1)\) twice between \(0\) and \(2\pi\).

### Solution
0. [calc1.extrema.critical-numbers] Set up: the function is differentiable for every number, so the critical numbers in the given interval are the zeros of its derivative there.
1. [calc1.deriv.trig-sin-cos] Differentiate: \(f'(x) = [[tex(diff(f, x))]]\).
   check: diff(f, x) = 1 + b*cos(x)
2. [trig.equations.solve] Solve \(f'(x) = 0\): \(\cos x = [[tex(-1/b)]]\), so \(x = [[tex(p)]]\) or \(x = [[tex(q)]]\) in \((0, 2\pi)\).
   check: subs(diff(f, x), x, p) = 0
   check: subs(diff(f, x), x, q) = 0
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x\), so the critical numbers in the interval are \(x = [[tex(p)]]\) and \(x = [[tex(q)]]\).
   check: {p, q} = {p, q}

<!-- tier 3: f' does not exist at a point of the domain -->
## Card calc1.4-3.crit-cusp.001
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule-rational, alg.factor.lowest-power, pre.functions.domain
difficulty: 3
answer-type: set
answer: 0, 2
wrong: 2 => f' also does not exist at x = 0, and f is defined there, so 0 is a critical number. @4; 0, 2, 5 => x = 5 is a zero of f, not of f'. Set f' equal to zero. @4

### Question
Find all critical numbers of \(f(x) = x^{2/3}(x - 5)\).

### Hints
1. Where is \(f'\) zero? Where is it undefined?
2. Rewrite \(f\) as a sum of powers of \(x\) before differentiating.

### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers include points where the derivative is zero and points in the domain where the derivative does not exist.
1. [pre.functions.domain] Domain: the cube root and the factor \(x - 5\) exist for every real \(x\), so \(f\) is defined everywhere, including at \(x = 0\), where \(f(0) = 0\).
   check: subs(root(x, 3)^2*(x - 5), x, 0) = 0
2. [calc1.deriv.power-rule-rational] Differentiate: \(f(x) = x^{5/3} - 5x^{2/3}\), so \(f'(x) = \frac{5}{3}x^{2/3} - \frac{10}{3}x^{-1/3}\).
   check: diff(u^5 - 5*u^2, u)/diff(u^3, u) = (5*u^4 - 10*u)/(3*u^2)
   check: 5/3*u^2 - 10/3*u^(-1) = (5*u^4 - 10*u)/(3*u^2)
3. [alg.factor.lowest-power] Factor out the lowest power: \(f'(x) = \frac{5}{3}x^{-1/3}(x - 2) = \frac{5(x - 2)}{3x^{1/3}}\).
   check: 5/3*u^(-1)*(u^3 - 2) = 5/3*u^2 - 10/3*u^(-1)
4. [calc1.extrema.critical-numbers] Critical numbers: the numerator is zero at \(x = 2\), and \(f'\) does not exist at \(x = 0\), which is in the domain. So \(x = 0\) and \(x = 2\).
   check: {0, 2} = {0, 2}

<!-- tier 3, adapted from OpenStax: f' is undefined only where f is undefined -->
## Card calc1.4-3.crit-holes.001
skill: calc1.extrema.critical-numbers
uses: pre.functions.domain, alg.fraction.cancel-factors, calc1.deriv.quotient-rule
difficulty: 3
answer-type: set
answer: none
wrong: -3, 1 => f is not defined at x = -3 or at x = 1, so neither can be a critical number. @4; -3 => f' does not exist at x = -3, but f is not defined there, so it is not a critical number. @4
source: OpenStax Calculus Volume 1 (Strang, Herman), Section 4.3 exercises, fs-id1165040750656
source-url: https://openstax.org/books/calculus-volume-1/pages/4-3-maxima-and-minima
license: CC BY-NC-SA 4.0
modified: yes

### Question
Find all critical numbers of \(f(x) = \dfrac{x^2 - 1}{x^2 + 2x - 3}\). Enter none if there are no critical numbers.

### Hints
1. Find the domain first. A critical number must be in the domain.
2. Simplify the fraction before you differentiate.

### Solution
0. [calc1.extrema.critical-numbers] Set up: a critical number must be in the domain of the function, with the derivative zero or undefined there.
1. [pre.functions.domain] Domain: the denominator factors as \((x + 3)(x - 1)\), which is zero at \(x = -3\) and \(x = 1\). So \(f\) is defined for every \(x\) except \(-3\) and \(1\).
   check: solve(x^2 + 2*x - 3, x) = {-3, 1}
2. [alg.fraction.cancel-factors] Simplify: for \(x\) in the domain, \(f(x) = \frac{(x - 1)(x + 1)}{(x + 3)(x - 1)} = \frac{x + 1}{x + 3}\).
   check: simplify((x^2 - 1)/(x^2 + 2*x - 3)) = (x + 1)/(x + 3)
3. [calc1.deriv.quotient-rule] Differentiate: \(f'(x) = \frac{(1)(x + 3) - (x + 1)(1)}{(x + 3)^2} = \frac{2}{(x + 3)^2}\).
   check: diff((x + 1)/(x + 3), x) = 2/(x + 3)^2
4. [calc1.extrema.critical-numbers] Critical numbers: \(\frac{2}{(x + 3)^2}\) is never zero. It does not exist at \(x = -3\), but \(f\) is not defined at \(-3\) or at \(1\), so neither is a critical number. There are none.
   check: solve(2/(x + 3)^2, x) = none

<!-- tier 4: the variable is in the exponent -->
## Card calc1.4-3.crit-xpowx.001
skill: calc1.extrema.critical-numbers
uses: pre.functions.domain, calc1.deriv.logarithmic-differentiation, calc1.deriv.product-rule, alg.logs.solve-equations
difficulty: 4
answer-type: set
answer: 1/e
wrong: none => The variable is in the exponent, so the power rule does not apply. Use logarithmic differentiation. @2; 1 => x^x is not a constant base raised to the power x, so (x^x)' is not x^x ln x. @2

### Question
Find all critical numbers of \(f(x) = x^x\) for \(x > 0\). Enter none if there are no critical numbers.

### Hints
1. The variable appears in both the base and the exponent.
2. Take the natural logarithm of both sides before differentiating.

### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers are where the derivative is zero or does not exist, inside the given domain of positive numbers.
1. [pre.functions.domain] Domain: \(x^x = e^{x \ln x}\), which is defined for \(x > 0\), the domain given.
   check: x^x = e^(x*ln(x))
2. [calc1.deriv.logarithmic-differentiation] Take logarithms: \(\ln f(x) = x\ln x\), so \(\frac{f'(x)}{f(x)} = (x\ln x)'\).
   check: ln(x^x) = x*ln(x)
3. [calc1.deriv.product-rule] Product rule: \((x\ln x)' = \ln x + 1\), so \(f'(x) = x^x(\ln x + 1)\).
   check: diff(x*ln(x), x) = ln(x) + 1
   check: diff(x^x, x) = x^x*(ln(x) + 1)
4. [alg.logs.solve-equations] Solve \(f'(x) = 0\): \(x^x > 0\), so \(\ln x + 1 = 0\), and \(x = e^{-1}\).
   check: solve(ln(x) + 1, x) = {1/e}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x > 0\), so the only critical number is \(x = \frac{1}{e}\).
   check: {1/e} = {1/e}

<!-- tier 4, adapted from CLP-1: absolute value inside a root -->
## Card calc1.4-3.crit-abs-sqrt.001
skill: calc1.extrema.critical-numbers
uses: alg.abs.piecewise, pre.functions.decompose, calc1.deriv.chain-rule
difficulty: 4
answer-type: set
answer: -7, -1, 5
wrong: -1 => f' also does not exist at x = -7 and x = 5, where the radicand is zero, and f is defined there. @4; -7, 5 => f' is also zero at x = -1. @4
source: CLP-1 Differential Calculus problem book (Feldman, Rechnitzer, Yeager), Section 3.5.1, question 7
source-url: https://github.com/arechnitzer/CLP1/blob/9f0295936d395bec68dab7915057135a2c7f0414/latex/problembook/problems/prob_s3.5.1.tex
license: CC BY-NC-SA 4.0
modified: yes

### Question
Find all critical numbers of \(f(x) = \sqrt{\left|(x - 5)(x + 7)\right|}\).

### Hints
1. Where is the quantity under the root equal to zero?
2. Rewrite the absolute value as a piecewise expression before you differentiate.

### Solution
0. [calc1.extrema.critical-numbers] Set up: the critical numbers are the zeros of the derivative and the points of the domain where the derivative does not exist. The root makes the derivative blow up where the radicand is zero.
1. [alg.abs.piecewise] Rewrite: \((x - 5)(x + 7) = x^2 + 2x - 35\) is negative for \(-7 < x < 5\) and positive otherwise, so \(|(x - 5)(x + 7)| = 35 - 2x - x^2\) for \(-7 < x < 5\) and \(x^2 + 2x - 35\) otherwise.
   check: expand((x - 5)*(x + 7)) = x^2 + 2*x - 35
2. [pre.functions.decompose] Decompose: \(f\) is the square root of an inner function, \(f = \sqrt{u}\) with \(u = |(x - 5)(x + 7)|\). Since \(u \ge 0\), \(f\) is defined for every \(x\).
   check: subs(sqrt(u), u, abs((x - 5)*(x + 7))) = sqrt(abs((x - 5)*(x + 7)))
3. [calc1.deriv.chain-rule] Chain rule: for \(-7 < x < 5\), \(f'(x) = \frac{-2 - 2x}{2\sqrt{35 - 2x - x^2}} = -\frac{x + 1}{\sqrt{35 - 2x - x^2}}\); for \(x < -7\) or \(x > 5\), \(f'(x) = \frac{x + 1}{\sqrt{x^2 + 2x - 35}}\).
   check: diff(sqrt(35 - 2*x - x^2), x) = -(x + 1)/sqrt(35 - 2*x - x^2)
   check: diff(sqrt(x^2 + 2*x - 35), x) = (x + 1)/sqrt(x^2 + 2*x - 35)
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) is zero only at \(x = -1\), which is in \((-7, 5)\). The denominator is zero at \(x = -7\) and \(x = 5\), so \(f'\) does not exist there, but \(f\) is defined there (\(f = 0\)). So the critical numbers are \(x = -7, -1, 5\).
   check: solve(x + 1, x) = {-1}
   check: solve(x^2 + 2*x - 35, x) = {-7, 5}
   check: {-7, -1, 5} = {-7, -1, 5}


<!-- ===================================================================== -->
<!-- calc1.extrema.closed-interval                                         -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-3.closed-example.001
kind: example
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.arith.exact-evaluation

### Question
Find the absolute maximum value and the absolute minimum value of \(f(x) = 2x^3 - 3x^2 - 12x + 5\) on \([-2, 3]\).

### Solution
0. [calc1.extrema.closed-interval] Set up: the function is continuous on the closed interval, so it has an absolute maximum and an absolute minimum there. Each occurs at an endpoint or at a critical number inside the interval, so compare the function at all of those.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 6x^2 - 6x - 12\).
   check: diff(2*x^3 - 3*x^2 - 12*x + 5, x) = 6*x^2 - 6*x - 12
2. [alg.factor.polynomials] Factor: \(f'(x) = 6(x - 2)(x + 1)\).
   check: expand(6*(x - 2)*(x + 1)) = 6*x^2 - 6*x - 12
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = 2\) or \(x = -1\).
   check: solve(6*(x - 2)*(x + 1), x) = {-1, 2}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere, so the critical numbers are \(-1\) and \(2\). Both lie in \([-2, 3]\), so both are candidates.
   check: {-1, 2} = {-1, 2}
5. [alg.arith.exact-evaluation] Evaluate \(f\) at the two endpoints and at the critical numbers: \(f(-2) = 1\), \(f(-1) = 12\), \(f(2) = -15\), \(f(3) = -4\).
   check: subs(2*x^3 - 3*x^2 - 12*x + 5, x, -2) = 1
   check: subs(2*x^3 - 3*x^2 - 12*x + 5, x, -1) = 12
   check: subs(2*x^3 - 3*x^2 - 12*x + 5, x, 2) = -15
   check: subs(2*x^3 - 3*x^2 - 12*x + 5, x, 3) = -4
6. [calc1.extrema.closed-interval] Compare: the largest value is \(12\), at \(x = -1\), and the smallest is \(-15\), at \(x = 2\). So the absolute maximum value is \(12\) and the absolute minimum value is \(-15\).
   check: {-15, 12} = {-15, 12}

<!-- tier 1, template: only the comparison is left -->
## Card calc1.4-3.closed-compare.t01
skill: calc1.extrema.closed-interval
difficulty: 1
answer-type: number
vars: p = int(1, 2); q = int(3, 5); a = int(-4, 3); b = int(-4, 3); c = int(2, 8); d = int(-3, 4)
require: c > a; c > b; c > d; d > a; c != q
answer: c
wrong: d => You compared only the two endpoint values. The value at the critical number x = [[q]] is larger. @1; q => That is the x-value where the maximum occurs. The maximum value is f([[q]]). @1

### Question
A continuous function \(f\) has exactly two critical numbers in \((0, 6)\), namely \(x = [[p]]\) and \(x = [[q]]\). Its values are \(f(0) = [[a]]\), \(f([[p]]) = [[b]]\), \(f([[q]]) = [[c]]\) and \(f(6) = [[d]]\). Find the absolute maximum value of \(f\) on \([0, 6]\).

### Hints
1. The absolute maximum is the largest of the values at the endpoints and at the critical numbers.

### Solution
0. [calc1.extrema.closed-interval] Set up: on a closed interval, the absolute maximum is the largest value of the function among the two endpoints and the critical numbers inside the interval.
1. [calc1.extrema.closed-interval] Compare: the four candidate values are \([[a]]\), \([[b]]\), \([[c]]\) and \([[d]]\). The largest is \([[c]]\), at \(x = [[q]]\), so the absolute maximum value is \([[c]]\).
   check: c = c

<!-- tier 1, adapted from CLP-1: a quadratic with its vertex inside the interval -->
## Card calc1.4-3.closed-quad.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule, alg.solve.linear, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 1
answer-type: list
answer: -19, 45
wrong: -15, 45 => Check the critical number x = -3 as well: f(-3) = -19 is lower than both endpoint values. @3; -19, 5 => 5 is the x-value where the maximum occurs. The maximum value is f(5) = 45. @5; 45, -19 => Give the minimum first, then the maximum. @5
source: CLP-1 Differential Calculus problem book (Feldman, Rechnitzer, Yeager), Section 3.5.2, question 4
source-url: https://github.com/arechnitzer/CLP1/blob/9f0295936d395bec68dab7915057135a2c7f0414/latex/problembook/problems/prob_s3.5.2.tex
license: CC BY-NC-SA 4.0
modified: yes

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = x^2 + 6x - 10\) on \([-5, 5]\), in that order.

### Hints
1. Find the critical numbers, then compare \(f\) at those and at both endpoints.

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 2x + 6\).
   check: diff(x^2 + 6*x - 10, x) = 2*x + 6
2. [alg.solve.linear] Solve \(f'(x) = 0\): \(2x + 6 = 0\) gives \(x = -3\).
   check: solve(2*x + 6, x) = {-3}
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere, so \(x = -3\) is the only critical number, and it lies in \([-5, 5]\).
   check: {-3} = {-3}
4. [alg.arith.exact-evaluation] Evaluate: \(f(-5) = -15\), \(f(-3) = -19\), \(f(5) = 45\).
   check: subs(x^2 + 6*x - 10, x, -5) = -15
   check: subs(x^2 + 6*x - 10, x, -3) = -19
   check: subs(x^2 + 6*x - 10, x, 5) = 45
5. [calc1.extrema.closed-interval] Compare: the smallest value is \(-19\) and the largest is \(45\).
   check: {-19, 45} = {-19, 45}

<!-- tier 1: f' is never zero -->
## Card calc1.4-3.closed-monotone.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 1
answer-type: list
answer: -14, 4
wrong: -2, 1 => Those are the x-values of the endpoints. Report the values of f there. @4; 4, -14 => Give the minimum first, then the maximum. @4

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = x^3 + 3x\) on \([-2, 1]\), in that order.

### Hints
1. Does \(f'\) ever equal zero?

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 + 3\).
   check: diff(x^3 + 3*x, x) = 3*x^2 + 3
2. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere and \(3x^2 + 3 \ge 3\) is never zero, so there are no critical numbers. Only the endpoints are candidates.
   check: solve(3*x^2 + 3, x) = none
3. [alg.arith.exact-evaluation] Evaluate: \(f(-2) = -14\) and \(f(1) = 4\).
   check: subs(x^3 + 3*x, x, -2) = -14
   check: subs(x^3 + 3*x, x, 1) = 4
4. [calc1.extrema.closed-interval] Compare: the smaller value is \(-14\) and the larger is \(4\).
   check: {-14, 4} = {-14, 4}

<!-- tier 2, template: a critical number outside the interval would give a wrong minimum -->
## Card calc1.4-3.closed-cubic.t01
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule, alg.factor.polynomials, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 2
answer-type: list
vars: m = int(1, 3); c = int(-6, 6)
let: f = x^3 - 12*m^2*x + c; p = c - 16*m^3; q = c; r = c - 9*m^3
answer: p, q
wrong: p, c + 16*m^3 => The critical number x = -[[2*m]] is outside the interval [0, [[3*m]]], so f(-[[2*m]]) is not a candidate. @3; r, q => Check the critical number x = [[2*m]] as well: it is inside the interval and f there is lower than both endpoint values. @3; q, p => Give the minimum first, then the maximum. @5

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = [[tex(f)]]\) on \(\left[ 0, [[3*m]] \right]\), in that order.

### Hints
1. Find the critical numbers, then keep only those inside the interval.

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = [[tex(diff(f, x))]]\).
   check: diff(f, x) = 3*x^2 - 12*m^2
2. [alg.factor.polynomials] Factor: \(f'(x) = 3(x - [[2*m]])(x + [[2*m]])\).
   check: expand(3*(x - 2*m)*(x + 2*m)) = 3*x^2 - 12*m^2
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere and is zero at \(x = \pm [[2*m]]\). Only \(x = [[2*m]]\) lies in \([0, [[3*m]]]\).
   check: solve(diff(f, x), x) = {-2*m, 2*m}
4. [alg.arith.exact-evaluation] Evaluate: \(f(0) = [[q]]\), \(f([[2*m]]) = [[p]]\), \(f([[3*m]]) = [[r]]\).
   check: subs(f, x, 0) = q
   check: subs(f, x, 2*m) = p
   check: subs(f, x, 3*m) = r
5. [calc1.extrema.closed-interval] Compare: the smallest value is \([[p]]\) and the largest is \([[q]]\).
   check: {p, q} = {p, q}

<!-- tier 2, adapted from CLP-1: one critical number is outside the interval -->
## Card calc1.4-3.closed-cubic-outside.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 2
answer-type: list
answer: 7, 61
wrong: -329/3, 61 => x = 5 is a critical number, but it is outside [-4, 0], so f(5) is not a candidate. @4; 7, 157/3 => The critical number x = -3 is inside the interval, and f(-3) = 61 is larger than f(-4). @4; 61, 7 => Give the minimum first, then the maximum. @6
source: CLP-1 Differential Calculus problem book (Feldman, Rechnitzer, Yeager), Section 3.5.2, question 5
source-url: https://github.com/arechnitzer/CLP1/blob/9f0295936d395bec68dab7915057135a2c7f0414/latex/problembook/problems/prob_s3.5.2.tex
license: CC BY-NC-SA 4.0
modified: yes

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = \frac{2}{3}x^3 - 2x^2 - 30x + 7\) on \([-4, 0]\), in that order.

### Hints
1. Find all critical numbers, then keep only those in \([-4, 0]\).

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 2x^2 - 4x - 30\).
   check: diff(2/3*x^3 - 2*x^2 - 30*x + 7, x) = 2*x^2 - 4*x - 30
2. [alg.factor.polynomials] Factor: \(f'(x) = 2(x - 5)(x + 3)\).
   check: expand(2*(x - 5)*(x + 3)) = 2*x^2 - 4*x - 30
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): \(x = 5\) or \(x = -3\).
   check: solve(2*(x - 5)*(x + 3), x) = {-3, 5}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere, so the critical numbers are \(-3\) and \(5\). Only \(x = -3\) lies in \([-4, 0]\); \(x = 5\) is outside.
   check: {-3} = {-3}
5. [alg.arith.exact-evaluation] Evaluate: \(f(-4) = \frac{157}{3}\), \(f(-3) = 61\), \(f(0) = 7\).
   check: subs(2/3*x^3 - 2*x^2 - 30*x + 7, x, -4) = 157/3
   check: subs(2/3*x^3 - 2*x^2 - 30*x + 7, x, -3) = 61
   check: subs(2/3*x^3 - 2*x^2 - 30*x + 7, x, 0) = 7
6. [calc1.extrema.closed-interval] Compare: \(\frac{157}{3} \approx 52.3\), so the smallest value is \(7\) and the largest is \(61\).
   check: {7, 61} = {7, 61}

<!-- tier 2, template: f' is undefined at 0, outside the interval; the critical number -k is outside too -->
## Card calc1.4-3.closed-rational.t01
skill: calc1.extrema.closed-interval
uses: alg.exponents.rewrite-as-power, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 2
answer-type: list
vars: a = int(2, 4); k = int(5, 8)
let: f = a*x + a*k^2/x; p = 2*a*k; q = a*(1 + k^2); r = 17*a*k/4
answer: p, q
wrong: r, q => Check the critical number x = [[k]] as well: it is inside the interval and f there is lower than both endpoint values. @4; -p, q => The critical number x = -[[k]] is outside the interval [1, [[4*k]]], so f(-[[k]]) is not a candidate. @4; q, p => Give the minimum first, then the maximum. @6

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = [[tex(f)]]\) on \(\left[ 1, [[4*k]] \right]\), in that order.

### Hints
1. Write \(f\) as a sum of powers of \(x\) before differentiating.
2. The critical numbers are the zeros of \(f'\). Where is \(f'\) undefined?

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [alg.exponents.rewrite-as-power] Rewrite: \(f(x) = [[a]]x + [[a*k^2]]x^{-1}\).
   check: a*x + a*k^2*x^(-1) = f
2. [calc1.deriv.power-rule-rational] Differentiate: \(f'(x) = [[a]] - [[a*k^2]]x^{-2} = [[a]] - \frac{[[a*k^2]]}{x^2}\).
   check: diff(a*x + a*k^2*x^(-1), x) = a - a*k^2*x^(-2)
3. [alg.solve.rational-equation] Solve \(f'(x) = 0\): multiply by \(x^2\) (note \(x \ne 0\)) to get \(x^2 = [[k^2]]\), so \(x = \pm [[k]]\).
   check: solve(a - a*k^2/x^2, x) = {-k, k}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) does not exist at \(x = 0\), but \(0\) is not in the domain of \(f\). The critical numbers are \(x = \pm [[k]]\), and only \(x = [[k]]\) lies in \([1, [[4*k]]]\).
   check: {k} = {k}
5. [alg.arith.exact-evaluation] Evaluate: \(f(1) = [[q]]\), \(f([[k]]) = [[p]]\), \(f([[4*k]]) = [[tex(r)]]\).
   check: subs(f, x, 1) = q
   check: subs(f, x, k) = p
   check: subs(f, x, 4*k) = r
6. [calc1.extrema.closed-interval] Compare: the smallest value is \([[p]]\) and the largest is \([[q]]\).
   check: {p, q} = {p, q}

<!-- tier 2: product rule with a logarithm; endpoints are powers of e -->
## Card calc1.4-3.closed-xlnx.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.product-rule, calc1.deriv.logarithm, alg.logs.solve-equations, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 2
answer-type: list
answer: -1/e, e
wrong: -2/e^2, e => Check the critical number x = 1/e as well: it is inside the interval and f there is lower than the endpoint values. @4; 1/e, e => 1/e is the x-value where the minimum occurs. The minimum value is f(1/e) = -1/e. @6; e, -1/e => Give the minimum first, then the maximum. @6

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = x\ln x\) on \(\left[ e^{-2}, e \right]\), in that order.

### Hints
1. The domain of \(f\) is \(x > 0\), which contains the whole interval.
2. Use the product rule to find \(f'\).

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.product-rule] Product rule: \(f'(x) = (1)(\ln x) + x\left(\ln x\right)'\).
   check: diff(x*ln(x), x) = ln(x) + x*diff(ln(x), x)
2. [calc1.deriv.logarithm] Differentiate the logarithm: \(\left(\ln x\right)' = \frac{1}{x}\), so \(f'(x) = \ln x + 1\).
   check: ln(x) + x*(1/x) = ln(x) + 1
3. [alg.logs.solve-equations] Solve \(f'(x) = 0\): \(\ln x = -1\), so \(x = e^{-1}\).
   check: solve(ln(x) + 1, x) = {1/e}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x > 0\), so the only critical number is \(x = \frac{1}{e}\). It lies in \([e^{-2}, e]\), since \(e^{-2} < e^{-1} < e\).
   check: {1/e} = {1/e}
5. [alg.arith.exact-evaluation] Evaluate: \(f(e^{-2}) = -2e^{-2}\), \(f(e^{-1}) = -e^{-1}\), \(f(e) = e\).
   check: subs(x*ln(x), x, e^(-2)) = -2/e^2
   check: subs(x*ln(x), x, 1/e) = -1/e
   check: subs(x*ln(x), x, e) = e
6. [calc1.extrema.closed-interval] Compare: since \(e > 2\), \(-\frac{1}{e} < -\frac{2}{e^2}\), so the smallest value is \(-\frac{1}{e}\) and the largest is \(e\).
   check: {-1/e, e} = {-1/e, e}

<!-- tier 3, template: trig, two critical numbers in [0, 2pi] -->
## Card calc1.4-3.closed-trig.t01
skill: calc1.extrema.closed-interval
uses: calc1.deriv.trig-sin-cos, trig.equations.solve, calc1.extrema.critical-numbers, trig.values.exact
difficulty: 3
answer-type: list
vars: a = int(2, 4); c = int(-3, 3)
let: f = a*(sin(x) + cos(x)) + c; p = c - a*sqrt(2); q = c + a*sqrt(2)
answer: p, q
wrong: a + c, q => Check both solutions of cos x = sin x in [0, 2pi]: x = 5pi/4 gives a lower value than the endpoints. @2; p, a + c => Check both solutions of cos x = sin x in [0, 2pi]: x = pi/4 gives a higher value than the endpoints. @2; q, p => Give the minimum first, then the maximum. @5

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = [[tex(f)]]\) on \([0, 2\pi]\), in that order.

### Hints
1. Solve \(f'(x) = 0\) for every solution in \([0, 2\pi]\).
2. At the solutions, \(\sin x\) and \(\cos x\) are \(\pm\frac{\sqrt{2}}{2}\).

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.trig-sin-cos] Differentiate: \(f'(x) = [[a]](\cos x - \sin x)\).
   check: diff(f, x) = a*(cos(x) - sin(x))
2. [trig.equations.solve] Solve \(f'(x) = 0\): \(\cos x = \sin x\), which has two solutions in \([0, 2\pi]\), \(x = \frac{\pi}{4}\) and \(x = \frac{5\pi}{4}\).
   check: subs(diff(f, x), x, pi/4) = 0
   check: subs(diff(f, x), x, 5*pi/4) = 0
3. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists everywhere, so the critical numbers in the interval are \(\frac{\pi}{4}\) and \(\frac{5\pi}{4}\).
   check: {pi/4, 5*pi/4} = {pi/4, 5*pi/4}
4. [trig.values.exact] Evaluate with exact values: \(f(0) = f(2\pi) = [[a + c]]\), \(f\left(\frac{\pi}{4}\right) = [[tex(q)]]\), \(f\left(\frac{5\pi}{4}\right) = [[tex(p)]]\).
   check: subs(f, x, 0) = a + c
   check: subs(f, x, 2*pi) = a + c
   check: subs(f, x, pi/4) = q
   check: subs(f, x, 5*pi/4) = p
5. [calc1.extrema.closed-interval] Compare: since \(\sqrt{2} > 1\), the smallest value is \([[tex(p)]]\) and the largest is \([[tex(q)]]\).
   check: {p, q} = {p, q}

<!-- tier 3: f' does not exist at an interior point, and that point gives the minimum -->
## Card calc1.4-3.closed-cusp.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.power-rule-rational, alg.factor.lowest-power, alg.solve.radical-equation, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 3
answer-type: list
answer: 0, 2
wrong: 3*root(2, 3)^2 - 4, 2 => The derivative does not exist at x = 0, which is in the domain and inside the interval, so 0 is a critical number. There f(0) = 0 is lower than both endpoint values. @4; 0, 3*root(2, 3)^2 - 4 => The derivative is also zero at x = -1 and x = 1, both inside the interval. There f = 2, which is higher than the endpoint values. @4; 2, 0 => Give the minimum first, then the maximum. @6

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = 3x^{2/3} - x^2\) on \([-2, 2]\), in that order.

### Hints
1. Find where \(f'\) is zero and where it does not exist. Both kinds of points count.
2. Write \(f'\) with the lowest power of \(x\) factored out.

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.power-rule-rational] Differentiate: \(f'(x) = 2x^{-1/3} - 2x\).
   check: diff(3*u^2 - u^6, u)/diff(u^3, u) = (6*u - 6*u^5)/(3*u^2)
   check: 2*u^(-1) - 2*u^3 = (6*u - 6*u^5)/(3*u^2)
2. [alg.factor.lowest-power] Factor out the lowest power: \(f'(x) = 2x^{-1/3}\left(1 - x^{4/3}\right) = \frac{2\left(1 - x^{4/3}\right)}{x^{1/3}}\).
   check: 2*u^(-1)*(1 - u^4) = 2*u^(-1) - 2*u^3
3. [alg.solve.radical-equation] Solve \(f'(x) = 0\): \(x^{4/3} = 1\), so \(x = \pm 1\).
   check: solve(u^4 - 1, u) = {-1, 1}
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) is zero at \(x = \pm 1\) and does not exist at \(x = 0\), which is in the domain. All three numbers lie in \([-2, 2]\).
   check: {-1, 0, 1} = {-1, 0, 1}
5. [alg.arith.exact-evaluation] Evaluate: \(f\) is even, so \(f(-2) = f(2) = 3\cdot 2^{2/3} - 4\) and \(f(-1) = f(1) = 2\). Also \(f(0) = 0\).
   check: subs(3*root(x, 3)^2 - x^2, x, 2) = 3*root(2, 3)^2 - 4
   check: subs(3*(x^2)^(1/3) - x^2, x, -2) = 3*root(2, 3)^2 - 4
   check: subs(3*root(x, 3)^2 - x^2, x, 1) = 2
   check: subs(3*(x^2)^(1/3) - x^2, x, -1) = 2
   check: subs(3*root(x, 3)^2 - x^2, x, 0) = 0
6. [calc1.extrema.closed-interval] Compare: \(2^{2/3}\) is between \(\frac{4}{3}\) and \(2\), so \(3\cdot 2^{2/3} - 4\) is between \(0\) and \(2\). The smallest value is \(0\), at the cusp \(x = 0\), and the largest is \(2\), at \(x = \pm 1\).
   check: {0, 2} = {0, 2}

<!-- tier 3, template: the minimum is at the critical number, the maximum at the right endpoint -->
## Card calc1.4-3.closed-radical.t01
skill: calc1.extrema.closed-interval
uses: alg.exponents.rewrite-as-power, calc1.deriv.power-rule-rational, alg.factor.lowest-power, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 3
answer-type: list
vars: w = int(1, 4); c = int(1, 9)
let: f = x*sqrt(x) - 3*w^2*sqrt(x) + c; p = c - 2*w^3; q = c + 2*w^3
answer: p, q
wrong: c, q => Check the critical number x = [[w^2]] as well: f there is lower than both endpoint values. @4; p, c => The right end has the larger value: f([[4*w^2]]) = [[q]] is greater than f(0) = [[c]]. @6; q, p => Give the minimum first, then the maximum. @6

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = [[tex(f)]]\) on \(\left[ 0, [[4*w^2]] \right]\), in that order.

### Hints
1. Write \(f\) with fractional powers of \(x\) before differentiating.
2. \(f'\) does not exist at \(x = 0\), an endpoint, which is a candidate anyway.

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [alg.exponents.rewrite-as-power] Rewrite: \(f(x) = x^{3/2} - [[3*w^2]]x^{1/2} + [[c]]\).
   check: x^(3/2) - 3*w^2*x^(1/2) + c = f
2. [calc1.deriv.power-rule-rational] Differentiate: \(f'(x) = \frac{3}{2}x^{1/2} - \frac{[[3*w^2]]}{2}x^{-1/2}\).
   check: diff(f, x) = 3/2*x^(1/2) - 3*w^2/2*x^(-1/2)
3. [alg.factor.lowest-power] Factor out the lowest power: \(f'(x) = \frac{3}{2}x^{-1/2}(x - [[w^2]])\).
   check: 3/2*x^(-1/2)*(x - w^2) = 3/2*x^(1/2) - 3*w^2/2*x^(-1/2)
4. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) is zero at \(x = [[w^2]]\), which is inside the interval. \(f'\) does not exist at \(x = 0\), the left endpoint, which is checked anyway.
   check: solve(x - w^2, x) = {w^2}
5. [alg.arith.exact-evaluation] Evaluate: \(f(0) = [[c]]\), \(f([[w^2]]) = [[p]]\), \(f([[4*w^2]]) = [[q]]\).
   check: subs(f, x, 0) = c
   check: subs(f, x, w^2) = p
   check: subs(f, x, 4*w^2) = q
6. [calc1.extrema.closed-interval] Compare: the smallest value is \([[p]]\) and the largest is \([[q]]\).
   check: {p, q} = {p, q}

<!-- tier 4: inverse trig; the comparison needs arctan 4 < pi/2 < 2 -->
## Card calc1.4-3.closed-arctan.001
skill: calc1.extrema.closed-interval
uses: calc1.deriv.inverse-trig, alg.fraction.combine, alg.solve.polynomial, calc1.extrema.critical-numbers, trig.inverse.values
difficulty: 4
answer-type: list
answer: arctan(4) - 2, pi/4 - 1/2
wrong: 0, pi/4 - 1/2 => Also compare f at the right end: f(4) = arctan 4 - 2 is below 0, because arctan 4 < pi/2 < 2. @6; arctan(4) - 2, 0 => Check the critical number x = 1 as well, where f' = 0: f(1) = pi/4 - 1/2 is greater than 0. @4; pi/4 - 1/2, arctan(4) - 2 => Give the minimum first, then the maximum. @6

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = \arctan x - \dfrac{x}{2}\) on \([0, 4]\), in that order.

### Hints
1. Differentiate, put \(f'\) over a common denominator, and find where it is zero.
2. To compare \(f(4)\) with \(0\), use \(\arctan 4 < \frac{\pi}{2}\).

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [calc1.deriv.inverse-trig] Differentiate: \(f'(x) = \frac{1}{1 + x^2} - \frac{1}{2}\).
   check: diff(arctan(x) - x/2, x) = 1/(1 + x^2) - 1/2
2. [alg.fraction.combine] Combine over a common denominator: \(f'(x) = \frac{1 - x^2}{2(1 + x^2)}\).
   check: 1/(1 + x^2) - 1/2 = (1 - x^2)/(2*(1 + x^2))
3. [alg.solve.polynomial] Solve \(f'(x) = 0\): the numerator \(1 - x^2 = (1 - x)(1 + x)\) is zero at \(x = \pm 1\).
   check: solve(1 - x^2, x) = {-1, 1}
4. [calc1.extrema.critical-numbers] Critical numbers: the denominator \(2(1 + x^2)\) is never zero, so \(f'\) exists everywhere. The critical numbers are \(\pm 1\), and only \(x = 1\) lies in \([0, 4]\).
   check: solve(2*(1 + x^2), x) = none
5. [trig.inverse.values] Evaluate with exact inverse trig values: \(f(0) = \arctan 0 = 0\), \(f(1) = \arctan 1 - \frac{1}{2} = \frac{\pi}{4} - \frac{1}{2}\), \(f(4) = \arctan 4 - 2\).
   check: subs(arctan(x) - x/2, x, 0) = 0
   check: subs(arctan(x) - x/2, x, 1) = pi/4 - 1/2
   check: subs(arctan(x) - x/2, x, 4) = arctan(4) - 2
6. [calc1.extrema.closed-interval] Compare: \(\frac{\pi}{4} - \frac{1}{2} > 0\) because \(\frac{\pi}{4} > \frac{1}{2}\), and \(\arctan 4 - 2 < \frac{\pi}{2} - 2 < 0\). So the smallest value is \(\arctan 4 - 2\) and the largest is \(\frac{\pi}{4} - \frac{1}{2}\).
   check: {arctan(4) - 2, pi/4 - 1/2} = {arctan(4) - 2, pi/4 - 1/2}

<!-- tier 4: logarithmic differentiation; the critical number e is outside the interval -->
## Card calc1.4-3.closed-xpow.001
skill: calc1.extrema.closed-interval
uses: pre.functions.domain, calc1.deriv.logarithmic-differentiation, calc1.deriv.quotient-rule, alg.logs.solve-equations, calc1.extrema.critical-numbers, alg.arith.exact-evaluation
difficulty: 4
answer-type: list
answer: 1/4, sqrt(2)
wrong: 1/4, e^(1/e) => x = e is a critical number, but e is about 2.72, outside [1/2, 2], so f(e) is not a candidate. @5; sqrt(2)/2, sqrt(2) => f(1/2) = (1/2)^(1/(1/2)) = (1/2)^2 = 1/4. @6; sqrt(2), 1/4 => Give the minimum first, then the maximum. @7

### Question
Find the absolute minimum value and the absolute maximum value of \(f(x) = x^{1/x}\) on \(\left[ \frac{1}{2}, 2 \right]\), in that order.

### Hints
1. The variable appears in the base and in the exponent.
2. Take the natural logarithm of both sides to differentiate.

### Solution
0. [calc1.extrema.closed-interval] Set up: compare the function at the critical numbers inside the interval and at both endpoints.
1. [pre.functions.domain] Domain: \(x^{1/x} = e^{(\ln x)/x}\), which needs \(x > 0\). The interval \(\left[\frac{1}{2}, 2\right]\) lies inside the domain.
   check: x^(1/x) = e^(ln(x)/x)
2. [calc1.deriv.logarithmic-differentiation] Take logarithms: \(\ln f(x) = \frac{\ln x}{x}\), so \(\frac{f'(x)}{f(x)} = \left(\frac{\ln x}{x}\right)'\).
   check: ln(x^(1/x)) = ln(x)/x
3. [calc1.deriv.quotient-rule] Quotient rule: \(\left(\frac{\ln x}{x}\right)' = \frac{1 - \ln x}{x^2}\), so \(f'(x) = x^{1/x}\cdot\frac{1 - \ln x}{x^2}\).
   check: diff(ln(x)/x, x) = (1 - ln(x))/x^2
   check: diff(x^(1/x), x) = x^(1/x)*(1 - ln(x))/x^2
4. [alg.logs.solve-equations] Solve \(f'(x) = 0\): \(x^{1/x} > 0\), so \(1 - \ln x = 0\) and \(x = e\).
   check: solve(1 - ln(x), x) = {e}
5. [calc1.extrema.critical-numbers] Critical numbers: \(f'\) exists for every \(x > 0\), so the only critical number is \(x = e \approx 2.72\), which is larger than \(2\). There is no critical number in \(\left[\frac{1}{2}, 2\right]\), so only the endpoints are candidates.
   check: {e} = {e}
6. [alg.arith.exact-evaluation] Evaluate: \(f\left(\frac{1}{2}\right) = \left(\frac{1}{2}\right)^{2} = \frac{1}{4}\) and \(f(2) = 2^{1/2} = \sqrt{2}\).
   check: subs(x^(1/x), x, 1/2) = 1/4
   check: subs(x^(1/x), x, 2) = sqrt(2)
7. [calc1.extrema.closed-interval] Compare: \(\frac{1}{4} < \sqrt{2}\), so the minimum value is \(\frac{1}{4}\) and the maximum value is \(\sqrt{2}\).
   check: {1/4, sqrt(2)} = {1/4, sqrt(2)}
