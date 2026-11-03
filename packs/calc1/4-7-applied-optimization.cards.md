---
format: mastery-cards 1
deck: Calculus I::4 Applications of Derivatives::4.7 Applied Optimization Problems
source: original
license: CC BY-NC-SA 4.0
---

<!-- Section 4.7 Applied Optimization Problems: six skills, one worked example each, twelve problems each.
     Tiers 1 and 2 train one move at a time (write the objective, eliminate a variable, state the
     domain, justify an extremum, report the answer), so they stop where that move ends. Tiers 3
     and 4 are whole optimization problems: every one ends with an explicit justification that the
     critical number is the maximum or minimum (compare values on a closed interval, or the sign of
     the first derivative, or the second derivative, on an open one).
     Units are written in the question text and in the displayed answer; the keys are plain numbers
     because the quantity answer type is not available yet. The geometry facts a setup needs are
     tagged pre.geometry.*. Provenance: every card is original unless it names a source. -->


<!-- ===================================================================== -->
<!-- calc1.optimize.objective                                              -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-7.objective-example.001
kind: example
skill: calc1.optimize.objective
uses: pre.geometry.area-volume-formulas, calc1.optimize.one-variable, calc1.optimize.domain, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.open-interval-absolute, calc1.optimize.answer

### Question
An open-top storage box has a square base and must hold exactly 32 liters (\(32\,000\) cm³). What base and height use the least material?

### Solution
0. [calc1.optimize.objective] Set up: the material is the surface area of the box without a top, and it depends on two lengths, the side of the base and the height. Name them, write the area in those two lengths, and only then use the volume to remove one of them.
1. [pre.geometry.area-volume-formulas] Formulas: with a square base of side \(x\) cm and height \(h\) cm, the volume is \(V = x^2 h\), the base has area \(x^2\), and each of the four sides has area \(xh\).
   check: x*x*h = x^2*h
2. [calc1.optimize.objective] Objective: the quantity to minimize is the material, the base plus four sides and no lid, so \(S = x^2 + 4xh\).
   check: x^2 + 4*(x*h) = x^2 + 4*x*h
3. [calc1.optimize.one-variable] Constraint: \(x^2 h = 32000\) gives \(h = \frac{32000}{x^2}\), so \(S(x) = x^2 + 4x \cdot \frac{32000}{x^2} = x^2 + \frac{128000}{x}\).
   check: subs(x^2*h, h, 32000/x^2) = 32000
   check: subs(x^2 + 4*x*h, h, 32000/x^2) = x^2 + 128000/x
4. [calc1.optimize.domain] Domain: the base side is positive, and every \(x > 0\) gives a positive height, since \(\frac{32000}{x^2}\) is never \(0\). So \(x\) can be any positive number, the interval \((0, \infty)\).
   check: solve(32000/x^2, x) = none
5. [calc1.deriv.power-rule-rational] Differentiate: \(S'(x) = 2x - \frac{128000}{x^2}\).
   check: diff(x^2 + 128000/x, x) = 2*x - 128000/x^2
6. [alg.solve.rational-equation] Solve \(S'(x) = 0\): multiply by \(x^2\) (note \(x \ne 0\)) to get \(2x^3 = 128000\), so \(x^3 = 64000\) and \(x = 40\).
   check: solve(2*x - 128000/x^2, x) = {40}
7. [calc1.optimize.open-interval-absolute] Justify: the domain is open, so there are no endpoints to compare. \(S'(20) = -280 < 0\) and \(S'(80) = 140 > 0\), and \(S'\) changes sign only at \(x = 40\), so \(S\) decreases on \((0, 40)\) and increases on \((40, \infty)\). The only critical number gives the absolute minimum.
   check: subs(2*x - 128000/x^2, x, 20) = -280
   check: subs(2*x - 128000/x^2, x, 80) = 140
8. [calc1.optimize.answer] Answer: the base is \(40\) cm by \(40\) cm and the height is \(h = \frac{32000}{40^2} = 20\) cm. The box then uses \(S(40) = 4800\) square centimeters of material.
   check: 32000/40^2 = 20
   check: subs(x^2 + 128000/x, x, 40) = 4800

<!-- tier 1: separate the quantity to optimize from the constraint -->
## Card calc1.4-7.obj-choose.001
skill: calc1.optimize.objective
difficulty: 1
answer-type: choice

### Question
A farmer has \(120\) m of fence for a rectangular pen. One side of the pen is a barn wall that needs no fence, so the fence covers the two sides of length \(x\) that meet the wall and the side of length \(y\) parallel to it. She wants the pen with the greatest area. Which equation gives the quantity to maximize?

### Choices
- [ ] \(2x + y = 120\)
- [x] \(A = xy\)
- [ ] \(A = 2x + y\)
- [ ] \(y = 120 - 2x\)

### Solution
0. [calc1.optimize.objective] Objective: the greatest area is wanted, and the area of a rectangle with sides \(x\) and \(y\) is \(A = xy\). The equation \(2x + y = 120\) is the constraint on the fence, not the quantity to maximize.
   check: x*y = y*x

<!-- tier 1, template: add up the cost of two kinds of fence -->
## Card calc1.4-7.obj-fence-cost.t01
skill: calc1.optimize.objective
difficulty: 1
answer-type: expression
vars: a = choice(36, 40, 45, 48, 50, 54); b = choice(16, 18, 20, 24, 25)
answer: a*x + b*(x + 2*y)
wrong: b*(2*x + 2*y) => The fence along the road, of length x, costs $[[a]] per meter. Only the other three sides cost $[[b]] per meter. @0; a*x + 2*b*y => The three cheaper sides are the back, of length x, and the two sides of length y. @0

### Question
A rectangular storage yard is \(x\) meters wide along a road and \(y\) meters deep. The fence along the road (the side of length \(x\)) costs $[[a]] per meter. The fence on the other three sides costs $[[b]] per meter. Write the total cost \(C\) of the fence, in dollars, in terms of \(x\) and \(y\).

### Answer
\(C = [[a]]x + [[b]](x + 2y)\) dollars

### Solution
0. [calc1.optimize.objective] Objective: the front costs \([[a]]x\) dollars, and the other three sides have total length \(x + 2y\) and cost \([[b]](x + 2y)\) dollars, so \(C = [[a]]x + [[b]](x + 2y)\).
   check: a*x + b*(x + 2*y) = (a + b)*x + 2*b*y
   check: (a + b)*x + 2*b*y = a*x + b*(x + 2*y)

<!-- tier 1: the width of a rectangle under a parabola is 2x -->
## Card calc1.4-7.obj-parabola-rect.001
skill: calc1.optimize.objective
difficulty: 1
answer-type: expression
answer: 2*x*y
wrong: x*y => The base runs from \(-x\) to \(x\), so its length is \(2x\), not \(x\). @0

### Question
A rectangle has its base on the \(x\)-axis and its two upper corners on the parabola \(y = 12 - x^2\), with the upper right corner at \((x, y)\) and the figure symmetric about the \(y\)-axis. Write the area \(A\) of the rectangle in terms of \(x\) and \(y\).

### Solution
0. [calc1.optimize.objective] Objective: the base runs from \(-x\) to \(x\), so its length is \(x - (-x) = 2x\), and the height is \(y\). The area is \(A = 2xy\).
   check: x - (-x) = 2*x
   check: 2*x*y = 2*x*y

<!-- tier 2, template: material cost of a closed cylinder -->
## Card calc1.4-7.obj-drum-cost.t01
skill: calc1.optimize.objective
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
vars: a = choice(45, 50, 56, 60); b = choice(24, 30, 36, 40)
answer: 2*pi*a*r^2 + 2*pi*b*r*h
wrong: pi*a*r^2 + 2*pi*b*r*h => A closed drum has two circular ends, a top and a bottom, so the ends together have area \(2\pi r^2\). @0; 2*pi*a*r^2 + pi*b*r*h => The side unrolls to a rectangle that is \(2\pi r\) long and \(h\) tall, so its area is \(2\pi r h\). @0; 2*pi*b*r^2 + 2*pi*a*r*h => The ends cost $[[a]] per square meter and the side costs $[[b]], not the other way round. @1

### Question
A closed cylindrical drum has radius \(r\) meters and height \(h\) meters. The metal for its top and bottom costs $[[a]] per square meter, and the metal for its side costs $[[b]] per square meter. Write the total cost \(C\) of the metal, in dollars, in terms of \(r\) and \(h\).

### Answer
\(C = [[a]]\cdot 2\pi r^2 + [[b]]\cdot 2\pi r h\) dollars

### Solution
0. [pre.geometry.area-volume-formulas] Areas: each circular end has area \(\pi r^2\), so the two ends together have area \(2\pi r^2\), and the side unrolls to a rectangle \(2\pi r\) by \(h\), with area \(2\pi r h\).
   check: pi*r^2 + pi*r^2 = 2*pi*r^2
1. [calc1.optimize.objective] Objective: cost is price times area for each part, so \(C = [[a]] \cdot 2\pi r^2 + [[b]] \cdot 2\pi r h\).
   check: a*(2*pi*r^2) + b*(2*pi*r*h) = 2*pi*a*r^2 + 2*pi*b*r*h

<!-- tier 2: area of a rectangle topped by a semicircle -->
## Card calc1.4-7.obj-arch-door.001
skill: calc1.optimize.objective
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
answer: w*h + pi*w^2/8
wrong: w*h + pi*w^2/4 => That is the area of a whole circle of diameter \(w\). The opening has only a semicircle. @0; w*h + pi*w^2/2 => The radius of the semicircle is half the width, \(\frac{w}{2}\), not \(w\). @0

### Question
A doorway is a rectangle \(w\) meters wide and \(h\) meters tall (to the top of its straight sides), topped by a semicircle whose diameter is the full width \(w\). Write the area \(A\) of the opening, in square meters, in terms of \(w\) and \(h\).

### Answer
\(A = wh + \frac{\pi w^2}{8}\) square meters

### Solution
0. [pre.geometry.area-volume-formulas] Areas: the rectangle has area \(wh\). The semicircle has radius \(\frac{w}{2}\), so its area is \(\frac{1}{2}\pi \left(\frac{w}{2}\right)^2 = \frac{\pi w^2}{8}\).
   check: 1/2*pi*(w/2)^2 = pi*w^2/8
1. [calc1.optimize.objective] Objective: the area of the opening is the rectangle plus the semicircle, \(A = wh + \frac{\pi w^2}{8}\).
   check: w*h + pi*w^2/8 = w*h + pi*w^2/8

<!-- tier 2, template: cost of a cable, with the underwater length from the Pythagorean theorem -->
## Card calc1.4-7.obj-river-cable.t01
skill: calc1.optimize.objective
uses: pre.geometry.pythagorean
difficulty: 2
answer-type: expression
vars: w = choice(300, 400, 500); d = choice(1000, 1200, 1500); a = choice(120, 150, 180); b = choice(60, 80, 90)
answer: a*sqrt(w^2 + x^2) + b*(d - x)
wrong: a*sqrt(w^2 + x^2) + b*x => The cable on land runs from the point \(P\) to the substation. The substation is \([[d]]\) m downstream, so that part has length \([[d]] - x\). @1; a*(w + x) + b*(d - x) => The underwater cable goes straight from the plant to \(P\). It is the hypotenuse of a right triangle, not the sum of its legs. @0; a*sqrt(w + x^2) + b*(d - x) => The first leg is \([[w]]\) m, so its square is \([[w]]^2 = [[w^2]]\). @0

### Question
A power plant on the north bank of a straight river \([[w]]\) m wide must be connected to a substation on the south bank, \([[d]]\) m downstream from the point directly across from the plant. The cable runs under water in a straight line from the plant to a point \(P\) on the south bank, \(x\) meters downstream from the point directly across, and then along the south bank to the substation. Underwater cable costs $[[a]] per meter and cable on land costs $[[b]] per meter. Write the total cost \(C\) of the cable, in dollars, in terms of \(x\).

### Answer
\(C = [[a]]\sqrt{[[w^2]] + x^2} + [[b]]([[d]] - x)\) dollars

### Solution
0. [pre.geometry.pythagorean] Underwater length: the cable is the hypotenuse of a right triangle with legs \([[w]]\) and \(x\), so it has length \(\sqrt{[[w]]^2 + x^2} = \sqrt{[[w^2]] + x^2}\).
   check: sqrt(w^2 + x^2)^2 = w^2 + x^2
1. [calc1.optimize.objective] Objective: the part on land has length \([[d]] - x\). The cost is price times length for each part, \(C = [[a]]\sqrt{[[w^2]] + x^2} + [[b]]([[d]] - x)\).
   check: a*sqrt(w^2 + x^2) + b*(d - x) = a*sqrt(w^2 + x^2) + b*d - b*x

<!-- tier 2: total yield is the number of plants times the yield per plant -->
## Card calc1.4-7.obj-greenhouse-yield.001
skill: calc1.optimize.objective
difficulty: 2
answer-type: expression
answer: (80 + x)*(12 - x/10)
wrong: 80*(12 - x/10) => The bed now holds \(80 + x\) plants, not \(80\). @0; (80 + x)*12 - x/10 => The yield falls by \(0.1\) kg for every plant in the bed, so the yield per plant is \(12 - 0.1x\) and it multiplies all \(80 + x\) plants. @0

### Question
A greenhouse bed holds \(80\) tomato plants, and each plant yields \(12\) kg per season. For each extra plant added to the bed, the yield of every plant in the bed falls by \(0.1\) kg. Let \(x\) be the number of extra plants. Write the total yield \(Y\) of the bed, in kilograms per season, in terms of \(x\).

### Answer
\(Y = (80 + x)(12 - 0.1x)\) kilograms per season

### Solution
0. [calc1.optimize.objective] Objective: total yield is the number of plants times the yield per plant. The bed holds \(80 + x\) plants, and each yields \(12 - 0.1x\) kg, so \(Y = (80 + x)(12 - 0.1x)\). For example, \(x = 20\) gives \(100\) plants at \(10\) kg each, \(1000\) kg in all.
   check: subs((80 + x)*(12 - x/10), x, 20) = 1000
   check: (80 + x)*(12 - x/10) = (80 + x)*(12 - x/10)

<!-- tier 3, template: a tank whose ends are made of dearer plate than its side -->
## Card calc1.4-7.obj-tank-cost.t01
skill: calc1.optimize.objective
uses: pre.geometry.area-volume-formulas, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.open-interval-absolute, calc1.optimize.answer
difficulty: 3
answer-type: list
vars: k = choice(2, 3); s = int(2, 4); a = choice(80, 100, 120, 140)
require: k*s <= 8
answer: s, 2*k*s
wrong: k^(1/3)*s, 2*k^(1/3)*s => That treats the ends as costing the same as the side. The ends cost [[k]] times as much per square meter, which changes the cost function. @1; 2*k*s, s => Give the radius first, then the height. @8

### Question
A chemical plant needs a closed cylindrical storage tank that holds exactly \([[2*k*s^3]]\pi\) cubic meters of liquid. The top and bottom are cut from steel plate that costs $[[k*a]] per square meter, and the side is made of thinner plate that costs $[[a]] per square meter. Find the radius and the height of the tank, in meters and in that order, that minimize the cost of the plate.

### Answer
radius \([[s]]\) m, height \([[2*k*s]]\) m

### Solution
0. [pre.geometry.area-volume-formulas] Formulas: the volume of a cylinder is \(\pi r^2 h\). Each end has area \(\pi r^2\), and the side unrolls to a rectangle of area \(2\pi r h\).
   check: pi*r^2 + pi*r^2 = 2*pi*r^2
1. [calc1.optimize.objective] Objective: the quantity to minimize is the cost, not the surface area, because the plates are priced differently. The two ends cost \([[k*a]] \cdot 2\pi r^2\) and the side costs \([[a]] \cdot 2\pi r h\), so \(C = [[k*a]] \cdot 2\pi r^2 + [[a]] \cdot 2\pi r h\).
   check: k*a*(2*pi*r^2) + a*(2*pi*r*h) = 2*pi*k*a*r^2 + 2*pi*a*r*h
2. [calc1.optimize.one-variable] Constraint: \(\pi r^2 h = [[2*k*s^3]]\pi\) gives \(h = \frac{[[2*k*s^3]]}{r^2}\), so \(C(r) = [[tex(2*pi*k*a*r^2 + 4*pi*k*a*s^3/r)]]\).
   check: subs(pi*r^2*h, h, 2*k*s^3/r^2) = 2*pi*k*s^3
   check: subs(2*pi*k*a*r^2 + 2*pi*a*r*h, h, 2*k*s^3/r^2) = 2*pi*k*a*r^2 + 4*pi*k*a*s^3/r
3. [calc1.optimize.domain] Domain: the radius is positive, and every \(r > 0\) gives a positive height, since \(\frac{[[2*k*s^3]]}{r^2}\) is never \(0\). So the domain is \((0, \infty)\).
   check: solve(2*k*s^3/r^2, r) = none
4. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints whose values could be compared. Find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.power-rule-rational] Differentiate: \(C'(r) = [[tex(4*pi*k*a*r - 4*pi*k*a*s^3/r^2)]]\).
   check: diff(2*pi*k*a*r^2 + 4*pi*k*a*s^3/r, r) = 4*pi*k*a*r - 4*pi*k*a*s^3/r^2
6. [alg.solve.rational-equation] Solve \(C'(r) = 0\): multiplying by \(r^2\) (note \(r \ne 0\)) gives \(r^3 = [[s^3]]\), so \(r = [[s]]\).
   check: solve(4*pi*k*a*r - 4*pi*k*a*s^3/r^2, r) = {s}
7. [calc1.optimize.open-interval-absolute] Justify: \(C'(r) = \frac{[[tex(4*pi*k*a)]] (r^3 - [[s^3]])}{r^2}\) is negative for \(0 < r < [[s]]\) and positive for \(r > [[s]]\). So \(C\) decreases and then increases, and the only critical number gives the absolute minimum.
   check: 4*pi*k*a*(r^3 - s^3)/r^2 = 4*pi*k*a*r - 4*pi*k*a*s^3/r^2
8. [calc1.optimize.answer] Answer: the radius is \([[s]]\) m and the height is \(h = \frac{[[2*k*s^3]]}{[[s^2]]} = [[2*k*s]]\) m.
   check: 2*k*s^3/s^2 = 2*k*s
   check: {s, 2*k*s} = {s, 2*k*s}

<!-- tier 3: the objective is profit, not revenue -->
## Card calc1.4-7.obj-ferry-profit.001
skill: calc1.optimize.objective
uses: alg.expand.products, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: number
answer: 14
wrong: 12 => That fare maximizes the revenue. The profit also subtracts the \$4 cost of each passenger, so the profit per passenger is the fare minus \$4. @0; 4 => That is the number of \$1 increases, not the fare. @8; 2000 => That is the greatest daily profit, not the fare that gives it. @8

### Question
A small ferry carries passengers across a bay. At a fare of $10 it carries \(280\) passengers per day, and for every $1 the fare is raised, \(20\) fewer passengers ride each day. Each passenger costs the operator $4 (fuel, ticketing and insurance), and the other costs do not depend on the fare. The operator will not lower the fare below $10. What fare gives the greatest daily profit, in dollars?

### Answer
a fare of $14

### Solution
0. [calc1.optimize.objective] Objective: let \(x\) be the number of $1 increases. The fare is \(10 + x\) dollars, each passenger brings a profit of \((10 + x) - 4 = 6 + x\) dollars, and \(280 - 20x\) passengers ride. So the daily profit is \(P(x) = (6 + x)(280 - 20x)\).
   check: (10 + x) - 4 = 6 + x
   check: subs(280 - 20*x, x, 1) = 260
1. [alg.expand.products] Expand: \(P(x) = 1680 + 160x - 20x^2\).
   check: expand((6 + x)*(280 - 20*x)) = 1680 + 160*x - 20*x^2
2. [calc1.optimize.domain] Domain: the fare is not lowered, so \(x \ge 0\), and the number of passengers cannot be negative, so \(280 - 20x \ge 0\), which gives \(x \le 14\). The domain is \([0, 14]\).
   check: solve(280 - 20*x, x) = {14}
3. [calc1.select.optimization-method] Method: the domain is a closed interval and the profit function is continuous, so the absolute maximum is found by comparing the profit at the critical number and at both endpoints.
4. [calc1.deriv.power-rule] Differentiate: \(P'(x) = 160 - 40x\).
   check: diff(1680 + 160*x - 20*x^2, x) = 160 - 40*x
5. [alg.solve.linear] Solve \(P'(x) = 0\): \(x = 4\), which lies in \([0, 14]\).
   check: solve(160 - 40*x, x) = {4}
6. [alg.arith.exact-evaluation] Evaluate: \(P(0) = 1680\), \(P(4) = 2000\) and \(P(14) = 0\).
   check: subs(1680 + 160*x - 20*x^2, x, 0) = 1680
   check: subs(1680 + 160*x - 20*x^2, x, 4) = 2000
   check: subs(1680 + 160*x - 20*x^2, x, 14) = 0
7. [calc1.extrema.closed-interval] Compare: the largest of the three values is \(2000\), at \(x = 4\), so the absolute maximum of the profit occurs at \(x = 4\).
   check: {1680, 2000, 0} = {1680, 2000, 0}
8. [calc1.optimize.answer] Answer: the question asks for the fare, not for \(x\) or for the profit. The fare is \(10 + 4 = 14\) dollars.
   check: 10 + 4 = 14

<!-- tier 3: a divider fence is priced differently; the second derivative decides -->
## Card calc1.4-7.obj-paddock-divider.001
skill: calc1.optimize.objective
uses: calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.shape.second-derivative-test, calc1.optimize.answer
difficulty: 3
answer-type: list
answer: 12, 15
wrong: 15, 12 => Give the length of the divider \(x\) first, then the other side \(y\). @7; sqrt(120), 180/sqrt(120) => That prices the divider at $24 per meter. Only the fence around the paddock costs $24 per meter, and the divider costs $12. @0; 12, 1440 => The second number is the other side \(y\) in meters, not the cost. @7

### Question
A rancher will fence a rectangular paddock of area \(180\) square meters and divide it into two equal parts with a fence parallel to one pair of its sides. The fence around the paddock costs $24 per meter, and the lighter dividing fence costs $12 per meter. Let \(x\) be the length of the dividing fence and \(y\) the length of the other side of the paddock. Find \(x\) and \(y\), in meters and in that order, that minimize the cost of the fencing.

### Answer
the divider is \(12\) m long and the other side is \(15\) m

### Solution
0. [calc1.optimize.objective] Objective: the fence around the paddock has length \(2x + 2y\) and costs $24 per meter, and the divider has length \(x\) and costs $12 per meter. So \(C = 24(2x + 2y) + 12x = 60x + 48y\).
   check: 24*(2*x + 2*y) + 12*x = 60*x + 48*y
1. [calc1.optimize.one-variable] Constraint: the area is \(xy = 180\), so \(y = \frac{180}{x}\) and \(C(x) = 60x + \frac{8640}{x}\).
   check: subs(x*y, y, 180/x) = 180
   check: subs(60*x + 48*y, y, 180/x) = 60*x + 8640/x
2. [calc1.optimize.domain] Domain: both lengths are positive, and every \(x > 0\) gives a positive \(y = \frac{180}{x}\), so the domain is \((0, \infty)\).
   check: solve(180/x, x) = none
3. [calc1.select.optimization-method] Method: the domain is open, so there are no endpoint values to compare. Find the critical number, and decide whether it is a minimum from the sign of the second derivative.
4. [calc1.deriv.power-rule-rational] Differentiate: \(C'(x) = 60 - \frac{8640}{x^2}\).
   check: diff(60*x + 8640/x, x) = 60 - 8640/x^2
5. [alg.solve.rational-equation] Solve \(C'(x) = 0\): multiplying by \(x^2\) gives \(60x^2 = 8640\), so \(x^2 = 144\) and \(x = 12\) (the root \(x = -12\) is outside the domain).
   check: solve(60 - 8640/x^2, x) = {-12, 12}
6. [calc1.shape.second-derivative-test] Test: \(C''(x) = \frac{17280}{x^3}\), which is positive for every \(x > 0\). So \(C\) is concave up on the whole domain, and its only critical number \(x = 12\) gives the absolute minimum. At that point \(C''(12) = 10 > 0\).
   check: diff(60 - 8640/x^2, x) = 17280/x^3
   check: subs(17280/x^3, x, 12) = 10
7. [calc1.optimize.answer] Answer: the divider is \(x = 12\) m long and the other side is \(y = \frac{180}{12} = 15\) m. The question asks for the two lengths, not for the cost.
   check: 180/12 = 15
   check: {12, 15} = {12, 15}

<!-- tier 4: ordering cost plus holding cost; the domain is half open -->
## Card calc1.4-7.obj-reorder.001
skill: calc1.optimize.objective
uses: calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.open-interval-absolute, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 4
answer-type: list
answer: 300, 1200
wrong: 1200, 300 => Give the order size \(Q\) first, then the yearly cost. @7; 150*sqrt(2), 1200*sqrt(2) => The holding cost is charged on the average stock \(\frac{Q}{2}\), not on \(Q\). With \(4Q\) the cost function is wrong from the start. @0

### Question
A bookstore sells \(3600\) copies of a title per year at a steady rate. It restocks by ordering \(Q\) copies at a time, each order arriving just as the shelf runs empty, so the stock falls steadily from \(Q\) to \(0\) between orders. Each order costs $50 to place, whatever its size. Holding stock costs $4 per copy per year, charged on the average number of copies in stock, which is \(\frac{Q}{2}\). An order can be at most the year's \(3600\) copies. Find the order size \(Q\) that minimizes the total yearly cost of ordering and holding, and that minimum cost. Give \(Q\) in copies and the cost in dollars, in that order.

### Answer
orders of \(300\) copies, with a minimum yearly cost of $1200

### Solution
0. [calc1.optimize.objective] Objective: the number of orders per year is \(\frac{3600}{Q}\), at $50 each, so ordering costs \(50 \cdot \frac{3600}{Q} = \frac{180000}{Q}\) dollars. Holding costs \(4 \cdot \frac{Q}{2} = 2Q\) dollars. The total is \(C(Q) = \frac{180000}{Q} + 2Q\).
   check: 50*(3600/Q) = 180000/Q
   check: 4*(Q/2) = 2*Q
1. [calc1.optimize.domain] Domain: an order is a positive number of copies and at most the yearly demand, so \(0 < Q \le 3600\). The interval has a right endpoint, \(3600\), but no left endpoint.
   check: solve(3600 - Q, Q) = {3600}
2. [calc1.select.optimization-method] Method: the domain has no left endpoint, so the closed-interval method does not apply. Find the critical number and use the sign of the derivative on each side of it, up to the right end of the domain.
3. [calc1.deriv.power-rule-rational] Differentiate: \(C'(Q) = 2 - \frac{180000}{Q^2}\).
   check: diff(180000/Q + 2*Q, Q) = 2 - 180000/Q^2
4. [alg.solve.rational-equation] Solve \(C'(Q) = 0\): \(2Q^2 = 180000\), so \(Q^2 = 90000\) and \(Q = 300\) (the root \(Q = -300\) is outside the domain).
   check: solve(2 - 180000/Q^2, Q) = {-300, 300}
5. [calc1.optimize.open-interval-absolute] Justify: \(C'(100) = -16 < 0\) and \(C'(600) = 1.5 > 0\), and \(C'\) changes sign only at \(Q = 300\). So \(C\) decreases on \((0, 300)\) and increases on \((300, 3600]\), and the only critical number gives the absolute minimum on the whole domain.
   check: subs(2 - 180000/Q^2, Q, 100) = -16
   check: subs(2 - 180000/Q^2, Q, 600) = 3/2
6. [alg.arith.exact-evaluation] Evaluate: \(C(300) = \frac{180000}{300} + 2 \cdot 300 = 600 + 600 = 1200\).
   check: subs(180000/Q + 2*Q, Q, 300) = 1200
7. [calc1.optimize.answer] Answer: order \(300\) copies at a time, for a minimum yearly cost of $1200.
   check: {300, 1200} = {300, 1200}

<!-- tier 4: illuminance from a lamp, with the objective built from an inverse-square law -->
## Card calc1.4-7.obj-lamp-height.001
skill: calc1.optimize.objective
uses: pre.geometry.pythagorean, trig.right-triangle.ratios, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.chain-rule, calc1.deriv.product-rule, alg.factor.lowest-power, alg.solve.polynomial, calc1.optimize.open-interval-absolute, calc1.optimize.answer
difficulty: 4
answer-type: number
answer: 3*sqrt(2)
wrong: 6 => That comes from \(E = \frac{kh}{d^2}\). Since \(\cos\theta = \frac{h}{d}\) also has \(d\) in its denominator, \(E = \frac{kh}{d^3}\). @2; 18 => That is \(h^2\) at the critical number. The height is its square root. @8

### Question
A street lamp hangs at height \(h\) meters directly above a point of a flat road. A point \(P\) on the road is \(6\) m from that point. The illuminance at \(P\) is \(E = \dfrac{k \cos\theta}{d^2}\), where \(k\) is a positive constant (the lamp's strength), \(d\) is the distance from the lamp to \(P\), and \(\theta\) is the angle between the vertical line down from the lamp and the line from the lamp to \(P\). At what height \(h\) is the illuminance at \(P\) greatest? Give \(h\) in meters.

### Answer
\(3\sqrt{2} \approx 4.24\) m

### Solution
0. [pre.geometry.pythagorean] Distance: the lamp, the point below it and \(P\) form a right triangle with legs \(h\) and \(6\), so \(d^2 = h^2 + 36\).
   check: h^2 + 6^2 = h^2 + 36
1. [trig.right-triangle.ratios] Angle: \(\cos\theta\) is the side next to \(\theta\) over the hypotenuse, so \(\cos\theta = \frac{h}{d} = \frac{h}{\sqrt{h^2 + 36}}\). For example, \(h = 8\) gives \(d = 10\) and \(\cos\theta = \frac{4}{5}\).
   check: subs(h/sqrt(h^2 + 36), h, 8) = 4/5
2. [calc1.optimize.objective] Objective: \(E = \frac{k \cos\theta}{d^2} = \frac{k h}{d^3}\), so \(E(h) = \frac{kh}{(h^2 + 36)^{3/2}} = kh(h^2 + 36)^{-3/2}\).
   check: k*(h/sqrt(h^2 + 36))/(h^2 + 36) = k*h*(h^2 + 36)^(-3/2)
3. [calc1.optimize.domain] Domain: the lamp is above the road and no upper limit on its height is given, so the domain is \((0, \infty)\).
   check: solve(h, h) = {0}
4. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints to compare. Find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.chain-rule] Chain rule: \(\frac{d}{dh}(h^2 + 36)^{-3/2} = -\frac{3}{2}(h^2 + 36)^{-5/2} \cdot 2h = -3h(h^2 + 36)^{-5/2}\).
   check: diff((h^2 + 36)^(-3/2), h) = -3*h*(h^2 + 36)^(-5/2)
6. [calc1.deriv.product-rule] Product rule: \(E'(h) = k\left[(h^2 + 36)^{-3/2} - 3h^2(h^2 + 36)^{-5/2}\right]\).
   check: diff(k*h*(h^2 + 36)^(-3/2), h) = k*((h^2 + 36)^(-3/2) - 3*h^2*(h^2 + 36)^(-5/2))
7. [alg.factor.lowest-power] Factor out the lowest power \((h^2 + 36)^{-5/2}\): \(E'(h) = k(h^2 + 36)^{-5/2}\left[(h^2 + 36) - 3h^2\right] = \frac{k(36 - 2h^2)}{(h^2 + 36)^{5/2}}\).
   check: k*(36 - 2*h^2)/(h^2 + 36)^(5/2) = k*((h^2 + 36)^(-3/2) - 3*h^2*(h^2 + 36)^(-5/2))
8. [alg.solve.polynomial] Solve \(E'(h) = 0\): \(36 - 2h^2 = 0\) gives \(h^2 = 18\), so \(h = 3\sqrt{2}\) (the root \(-3\sqrt{2}\) is outside the domain).
   check: solve(36 - 2*h^2, h) = {-3*sqrt(2), 3*sqrt(2)}
9. [calc1.optimize.open-interval-absolute] Justify: \(k\) and \((h^2 + 36)^{5/2}\) are positive, so \(E'\) has the sign of \(36 - 2h^2\). That is positive at \(h = 1\) (value \(34\)) and negative at \(h = 6\) (value \(-72 + 36 = -36\)), and it changes sign only at \(h = 3\sqrt{2}\). So \(E\) increases on \((0, 3\sqrt{2})\) and decreases after it, and the only critical number gives the absolute maximum.
   check: subs(36 - 2*h^2, h, 1) = 34
   check: subs(36 - 2*h^2, h, 6) = -36
10. [calc1.optimize.answer] Answer: the illuminance at \(P\) is greatest when the lamp is \(3\sqrt{2} \approx 4.24\) m above the road.
   check: sqrt(18) = 3*sqrt(2)


<!-- ===================================================================== -->
<!-- calc1.optimize.one-variable                                           -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-7.onevar-example.001
kind: example
skill: calc1.optimize.one-variable
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.open-interval-absolute, calc1.optimize.answer

### Question
A farmer wants a rectangular grazing field of area \(3200\) square meters along a straight river. No fence is needed along the river. What dimensions use the least fence?

### Solution
0. [calc1.optimize.one-variable] Set up: the length of fence depends on two lengths, but the fixed area ties them together. Solve that relation for one length and substitute it into the fence length, so that everything depends on a single variable.
1. [calc1.optimize.objective] Objective: let \(x\) be the length of each of the two sides that run away from the river and \(y\) the side parallel to the river, in meters. The fence needed is \(L = 2x + y\).
   check: 2*x + y = 2*x + y
2. [calc1.optimize.one-variable] Constraint: the area is \(xy = 3200\), so \(y = \frac{3200}{x}\). Substituting gives \(L(x) = 2x + \frac{3200}{x}\).
   check: subs(x*y, y, 3200/x) = 3200
   check: subs(2*x + y, y, 3200/x) = 2*x + 3200/x
3. [calc1.optimize.domain] Domain: both lengths are positive, and every \(x > 0\) gives a positive \(y = \frac{3200}{x}\), so \(x\) can be any number in \((0, \infty)\).
   check: solve(3200/x, x) = none
4. [calc1.deriv.power-rule-rational] Differentiate: \(L'(x) = 2 - \frac{3200}{x^2}\).
   check: diff(2*x + 3200/x, x) = 2 - 3200/x^2
5. [alg.solve.rational-equation] Solve \(L'(x) = 0\): \(2x^2 = 3200\), so \(x^2 = 1600\) and \(x = 40\).
   check: solve(2 - 3200/x^2, x) = {-40, 40}
6. [calc1.optimize.open-interval-absolute] Justify: the domain is open, so there are no endpoints to compare. \(L'(20) = -6 < 0\) and \(L'(80) = 1.5 > 0\), and \(L'\) changes sign only at \(x = 40\). So \(L\) decreases and then increases, and the only critical number gives the absolute minimum.
   check: subs(2 - 3200/x^2, x, 20) = -6
   check: subs(2 - 3200/x^2, x, 80) = 3/2
7. [calc1.optimize.answer] Answer: \(x = 40\) m and \(y = \frac{3200}{40} = 80\) m, so the field is \(40\) m by \(80\) m, with the long side along the river. It uses \(L = 160\) m of fence.
   check: 3200/40 = 80
   check: subs(2*x + 3200/x, x, 40) = 160

<!-- tier 1, template: solve a fence constraint for y -->
## Card calc1.4-7.onevar-solve-y.t01
skill: calc1.optimize.one-variable
difficulty: 1
answer-type: expression
vars: c = choice(2, 3, 4); d = choice(2, 3, 4, 5); n = choice(120, 150, 180, 240)
answer: (n - c*x)/d
wrong: (n - c*x)*d => The coefficient of \(y\) divides the whole right side. Divide by [[d]], do not multiply. @0; n - c*x/d => Divide the whole right side, \([[n]] - [[c]]x\), by [[d]]. @0

### Question
A pen is fenced with exactly \([[n]]\) meters of fence in total. The fence is made of [[c]] sections of length \(x\) meters each and [[d]] sections of length \(y\) meters each. Write \(y\) in terms of \(x\).

### Answer
\(y = \frac{[[n]] - [[c]]x}{[[d]]}\) meters

### Solution
0. [calc1.optimize.one-variable] Constraint: the total length of fence is \([[c]]x + [[d]]y = [[n]]\), so \(y = \frac{[[n]] - [[c]]x}{[[d]]}\).
   check: solve(c*x + d*y - n, y) = {(n - c*x)/d}

<!-- tier 1, template: substitute a sum constraint into a product -->
## Card calc1.4-7.onevar-product.t01
skill: calc1.optimize.one-variable
difficulty: 1
answer-type: expression
vars: s = choice(20, 24, 30, 36, 40, 50)
answer: x*(s - x)
wrong: x*(s + x) => From \(x + y = [[s]]\) we get \(y = [[s]] - x\). @0

### Question
Two positive numbers \(x\) and \(y\) have sum \([[s]]\). Write their product \(P = xy\) as a function of \(x\) alone.

### Solution
0. [calc1.optimize.one-variable] Constraint: \(x + y = [[s]]\) gives \(y = [[s]] - x\), so \(P(x) = x([[s]] - x)\).
   check: solve(x + y - s, y) = {s - x}
   check: subs(x*y, y, s - x) = x*(s - x)

<!-- tier 1, template: the constraint is a product -->
## Card calc1.4-7.onevar-sumsq.t01
skill: calc1.optimize.one-variable
difficulty: 1
answer-type: expression
vars: q = choice(9, 16, 25, 36, 49)
answer: x^2 + q^2/x^2
domain: x > 0
wrong: x^2 + q/x^2 => From \(xy = [[q]]\) we get \(y = \frac{[[q]]}{x}\), and \(y^2 = \frac{[[q^2]]}{x^2}\), not \(\frac{[[q]]}{x^2}\). @0

### Question
Two positive numbers \(x\) and \(y\) have product \([[q]]\). Write the sum of their squares, \(S = x^2 + y^2\), as a function of \(x\) alone.

### Solution
0. [calc1.optimize.one-variable] Constraint: \(xy = [[q]]\) gives \(y = \frac{[[q]]}{x}\), so \(S(x) = x^2 + \left(\frac{[[q]]}{x}\right)^2 = x^2 + \frac{[[q^2]]}{x^2}\).
   check: subs(x*y, y, q/x) = q
   check: subs(x^2 + y^2, y, q/x) = x^2 + q^2/x^2

<!-- tier 2, template: volume of a box folded from a sheet -->
## Card calc1.4-7.onevar-box-sheet.t01
skill: calc1.optimize.one-variable
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
vars: a = choice(30, 36, 40, 48); b = choice(50, 60, 72, 80)
answer: x*(a - 2*x)*(b - 2*x)
wrong: x*(a - x)*(b - x) => Cutting a square from both ends of a side removes \(x\) twice, so each side of the base shrinks by \(2x\). @1; (a - 2*x)*(b - 2*x) => The volume is the area of the base times the height, and the height is \(x\). @0

### Question
An open box is made from a rectangular sheet of cardboard [[a]] cm by [[b]] cm. A square of side \(x\) cm is cut from each corner, and the sides are folded up. Write the volume \(V\) of the box, in cubic centimeters, as a function of \(x\).

### Answer
\(V = x([[a]] - 2x)([[b]] - 2x)\) cubic centimeters

### Solution
0. [pre.geometry.area-volume-formulas] Formula: the volume of a box is its length times its width times its height.
1. [calc1.optimize.one-variable] Dimensions: cutting \(x\) from both ends of a side removes \(2x\), so the base is \([[a]] - 2x\) by \([[b]] - 2x\), and the height is \(x\). So \(V(x) = x([[a]] - 2x)([[b]] - 2x)\). For example, \(x = 5\) gives a box \([[a - 10]]\) by \([[b - 10]]\) by \(5\).
   check: subs(x*(a - 2*x)*(b - 2*x), x, 5) = 5*(a - 10)*(b - 10)
   check: x*(a - 2*x)*(b - 2*x) = x*(a - 2*x)*(b - 2*x)

<!-- tier 2, template: the volume constraint of a can -->
## Card calc1.4-7.onevar-can-surface.t01
skill: calc1.optimize.one-variable
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
vars: k = choice(54, 128, 250, 432)
answer: 2*pi*r^2 + 2*k*pi/r
domain: r > 0
wrong: 2*pi*r^2 + 2*k*pi*r^3 => From \(\pi r^2 h = [[k]]\pi\) we get \(h = \frac{[[k]]}{r^2}\). Divide by \(r^2\), do not multiply. @1; 2*pi*r^2 + 2*k*pi/r^2 => In \(2\pi r h\), one factor \(r\) cancels against \(r^2\) in \(h = \frac{[[k]]}{r^2}\), leaving \(\frac{[[2*k]]\pi}{r}\). @1

### Question
A closed can has radius \(r\) cm and height \(h\) cm, so its surface area is \(S = 2\pi r^2 + 2\pi r h\) square centimeters. The can must hold exactly \([[k]]\pi\) cm³. Write \(S\) as a function of \(r\) alone.

### Answer
\(S = 2\pi r^2 + \frac{[[2*k]]\pi}{r}\) square centimeters

### Solution
0. [pre.geometry.area-volume-formulas] Formula: the volume of a cylinder is \(V = \pi r^2 h\), so the condition is \(\pi r^2 h = [[k]]\pi\).
   check: subs(pi*r^2*h, h, k/r^2) = k*pi
1. [calc1.optimize.one-variable] Constraint: \(\pi r^2 h = [[k]]\pi\) gives \(h = \frac{[[k]]}{r^2}\). Then \(S(r) = 2\pi r^2 + 2\pi r \cdot \frac{[[k]]}{r^2} = 2\pi r^2 + \frac{[[2*k]]\pi}{r}\).
   check: subs(2*pi*r^2 + 2*pi*r*h, h, k/r^2) = 2*pi*r^2 + 2*k*pi/r

<!-- tier 2: one piece of wire becomes a square and the other a circle -->
## Card calc1.4-7.onevar-wire-pieces.001
skill: calc1.optimize.one-variable
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
answer: x^2/16 + (12 - x)^2/(4*pi)
wrong: x^2 + (12 - x)^2/(4*pi) => The piece of length \(x\) is the perimeter of the square, so its side is \(\frac{x}{4}\) and its area is \(\frac{x^2}{16}\). @0; x^2/16 + (12 - x)^2/pi => The circumference is \(2\pi r\), so the radius is \(\frac{12 - x}{2\pi}\), and the area \(\pi r^2\) is \(\frac{(12 - x)^2}{4\pi}\). @0

### Question
A wire \(12\) m long is cut into two pieces. The piece of length \(x\) m is bent into a square, and the rest is bent into a circle. Write the total area \(A\) enclosed by the two shapes, in square meters, as a function of \(x\).

### Answer
\(A = \frac{x^2}{16} + \frac{(12 - x)^2}{4\pi}\) square meters

### Solution
0. [pre.geometry.area-volume-formulas] Areas: the square has perimeter \(x\), so its side is \(\frac{x}{4}\) and its area is \(\frac{x^2}{16}\). The circle has circumference \(12 - x = 2\pi r\), so its radius is \(r = \frac{12 - x}{2\pi}\) and its area is \(\pi r^2 = \frac{(12 - x)^2}{4\pi}\).
   check: (x/4)^2 = x^2/16
   check: pi*((12 - x)/(2*pi))^2 = (12 - x)^2/(4*pi)
1. [calc1.optimize.one-variable] One variable: the two pieces use all \(12\) m of wire, so the circle's piece is \(12 - x\) and both areas depend only on \(x\). The total is \(A(x) = \frac{x^2}{16} + \frac{(12 - x)^2}{4\pi}\).
   check: x^2/16 + (12 - x)^2/(4*pi) = x^2/16 + (12 - x)^2/(4*pi)

<!-- tier 2: the Pythagorean theorem removes the second variable -->
## Card calc1.4-7.onevar-ladder-triangle.001
skill: calc1.optimize.one-variable
uses: pre.geometry.pythagorean
difficulty: 2
answer-type: expression
answer: x*sqrt(25 - x^2)/2
domain: 0 < x < 5
wrong: x*(5 - x)/2 => The ladder is the hypotenuse, so the height \(y\) satisfies \(x^2 + y^2 = 25\), which gives \(y = \sqrt{25 - x^2}\). @0; x*sqrt(5 - x^2)/2 => The hypotenuse is \(5\), so the equation is \(x^2 + y^2 = 5^2 = 25\). @0

### Question
A \(5\) m ladder leans against a vertical wall on level ground, with its foot \(x\) meters from the wall. The ladder, the wall and the ground form a right triangle. Write the area \(A\) of this triangle, in square meters, as a function of \(x\).

### Answer
\(A = \frac{1}{2}x\sqrt{25 - x^2}\) square meters

### Solution
0. [pre.geometry.pythagorean] Height: the ladder is the hypotenuse, so the top of the ladder is at height \(y = \sqrt{5^2 - x^2} = \sqrt{25 - x^2}\).
   check: sqrt(5^2 - x^2) = sqrt(25 - x^2)
1. [calc1.optimize.one-variable] One variable: the legs of the triangle are \(x\) and \(y\), so its area is \(\frac{1}{2}xy\). Substituting gives \(A(x) = \frac{1}{2}x\sqrt{25 - x^2}\).
   check: subs(x*y/2, y, sqrt(25 - x^2)) = x*sqrt(25 - x^2)/2

<!-- tier 3, template: the best garden in the corner of a triangular plot -->
## Card calc1.4-7.onevar-corner-rect.t01
skill: calc1.optimize.one-variable
uses: calc1.optimize.objective, pre.geometry.similar-triangles, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: list
vars: a = choice(12, 16, 18, 20); b = choice(24, 30, 36, 40)
answer: a/2, b/2
wrong: b/2, a/2 => Give the side along the [[a]] m leg first, then the side along the [[b]] m leg. @9; a, b => The corner of the garden must lie on the hypotenuse. When \(x\) is the whole leg, there is no room left for the other side. @1

### Question
A triangular plot of land is a right triangle with legs of [[a]] m and [[b]] m. A rectangular garden is laid out inside the plot with one corner at the right-angle vertex, two sides along the legs, and the opposite corner on the hypotenuse. Find the dimensions of the garden of greatest area: the side along the [[a]] m leg and the side along the [[b]] m leg, in meters and in that order.

### Answer
[[a/2]] m along the [[a]] m leg and [[b/2]] m along the [[b]] m leg

### Solution
0. [calc1.optimize.objective] Objective: let \(x\) be the side of the garden along the [[a]] m leg and \(y\) the side along the [[b]] m leg, in meters. The area to maximize is \(A = xy\).
   check: x*y = x*y
1. [pre.geometry.similar-triangles] Similar triangles: the small triangle above the garden, with legs \(x\) and \([[b]] - y\), is similar to the whole plot, with legs [[a]] and [[b]]. So \(\frac{[[b]] - y}{x} = \frac{[[b]]}{[[a]]}\).
   check: solve(a*(b - y) - b*x, y) = {b - b*x/a}
2. [calc1.optimize.one-variable] Eliminate \(y\): \(y = [[b]] - \frac{[[b]]}{[[a]]}x\), so \(A(x) = x\left([[b]] - \frac{[[b]]}{[[a]]}x\right) = [[tex(b*x - b*x^2/a)]]\).
   check: subs(x*y, y, b - b*x/a) = b*x - b*x^2/a
3. [calc1.optimize.domain] Domain: the side along the [[a]] m leg satisfies \(0 \le x \le [[a]]\), and \(y\) reaches \(0\) at \(x = [[a]]\). The domain is the closed interval \([0, [[a]]]\).
   check: solve(b - b*x/a, x) = {a}
4. [calc1.select.optimization-method] Method: the domain is a closed interval and the area function is continuous, so compare the area at the critical number with the area at both endpoints.
5. [calc1.deriv.power-rule] Differentiate: \(A'(x) = [[tex(diff(b*x - b*x^2/a, x))]]\).
   check: diff(b*x - b*x^2/a, x) = b - 2*b*x/a
6. [alg.solve.linear] Solve \(A'(x) = 0\): \(x = \frac{[[a]]}{2} = [[a/2]]\), which lies in \([0, [[a]]]\).
   check: solve(b - 2*b*x/a, x) = {a/2}
7. [alg.arith.exact-evaluation] Evaluate: \(A(0) = 0\), \(A([[a/2]]) = [[a*b/4]]\) and \(A([[a]]) = 0\).
   check: subs(b*x - b*x^2/a, x, 0) = 0
   check: subs(b*x - b*x^2/a, x, a/2) = a*b/4
   check: subs(b*x - b*x^2/a, x, a) = 0
8. [calc1.extrema.closed-interval] Compare: the largest of the three values is \([[a*b/4]]\), at \(x = [[a/2]]\), so the absolute maximum of the area occurs there.
   check: a*b/4 = a*b/4
9. [calc1.optimize.answer] Answer: at \(x = [[a/2]]\) the other side is \(y = [[b]] - \frac{[[b]]}{[[a]]} \cdot [[a/2]] = [[b/2]]\). The garden is \([[a/2]]\) m along the [[a]] m leg and \([[b/2]]\) m along the [[b]] m leg.
   check: subs(b - b*x/a, x, a/2) = b/2
   check: {a/2, b/2} = {a/2, b/2}

<!-- tier 3: a cylinder cut from a cone, with similar triangles -->
## Card calc1.4-7.onevar-candle-cone.001
skill: calc1.optimize.one-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.polynomial, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: list
answer: 4, 5
wrong: 5, 4 => Give the radius first, then the height. @9; 6, 15 => That cylinder would stick out of the cone. The top rim of the candle must lie on the slanted side of the cone, which ties its height to its radius. @1

### Question
A craftsman cuts a cylindrical candle from a cone-shaped block of wax. The block has base radius \(6\) cm and height \(15\) cm. The candle has the same axis as the block, and its base lies on the base of the block. Find the radius and the height of the candle of greatest volume, in centimeters and in that order.

### Answer
radius \(4\) cm and height \(5\) cm

### Solution
0. [pre.geometry.area-volume-formulas] Formula: the quantity to maximize is the volume of the candle, a cylinder of radius \(r\) and height \(h\) centimeters, so \(V = \pi r^2 h\).
   check: pi*r^2*h = pi*h*r^2
1. [pre.geometry.similar-triangles] Similar triangles: in a cross-section through the axis, the small triangle above the candle has height \(15 - h\) and base \(r\). It is similar to the whole cross-section, with height \(15\) and base \(6\), so \(\frac{15 - h}{r} = \frac{15}{6}\).
   check: solve(6*(15 - h) - 15*r, h) = {15 - 5*r/2}
2. [calc1.optimize.one-variable] Eliminate \(h\): \(h = 15 - \frac{5}{2}r\), so \(V(r) = \pi r^2\left(15 - \frac{5}{2}r\right) = \pi\left(15r^2 - \frac{5}{2}r^3\right)\).
   check: subs(pi*r^2*h, h, 15 - 5*r/2) = pi*(15*r^2 - 5*r^3/2)
3. [calc1.optimize.domain] Domain: the candle cannot be wider than the block, and its height must not be negative, so \(0 \le r \le 6\). At \(r = 6\) the height is \(15 - 15 = 0\). The domain is the closed interval \([0, 6]\).
   check: solve(15 - 5*r/2, r) = {6}
4. [calc1.select.optimization-method] Method: the domain is a closed interval and the volume function is continuous, so compare the volume at the critical number with the volume at both endpoints.
5. [calc1.deriv.power-rule] Differentiate: \(V'(r) = \pi\left(30r - \frac{15}{2}r^2\right)\).
   check: diff(pi*(15*r^2 - 5*r^3/2), r) = pi*(30*r - 15*r^2/2)
6. [alg.solve.polynomial] Solve \(V'(r) = 0\) by factoring: \(V'(r) = \frac{15\pi}{2}\,r(4 - r)\), so \(r = 0\) or \(r = 4\). Both lie in \([0, 6]\).
   check: factor(pi*(30*r - 15*r^2/2)) = -15*pi*r*(r - 4)/2
   check: solve(pi*(30*r - 15*r^2/2), r) = {0, 4}
7. [alg.arith.exact-evaluation] Evaluate: \(V(0) = 0\), \(V(4) = 80\pi\) and \(V(6) = 0\).
   check: subs(pi*(15*r^2 - 5*r^3/2), r, 0) = 0
   check: subs(pi*(15*r^2 - 5*r^3/2), r, 4) = 80*pi
   check: subs(pi*(15*r^2 - 5*r^3/2), r, 6) = 0
8. [calc1.extrema.closed-interval] Compare: the largest value is \(80\pi\), at \(r = 4\), so the absolute maximum of the volume occurs at \(r = 4\).
   check: 80*pi = 80*pi
9. [calc1.optimize.answer] Answer: the radius is \(4\) cm and the height is \(h = 15 - \frac{5}{2} \cdot 4 = 5\) cm. The candle has volume \(80\pi \approx 251\) cm³.
   check: subs(15 - 5*r/2, r, 4) = 5
   check: {4, 5} = {4, 5}

<!-- tier 3: the nearest point of a parabola to a point off the curve -->
## Card calc1.4-7.onevar-closest-point.001
skill: calc1.optimize.one-variable
uses: pre.geometry.pythagorean, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial, calc1.optimize.open-interval-absolute, calc1.optimize.answer
difficulty: 3
answer-type: point
answer: (1, 1)
wrong: (3, 9) => The point of the parabola with the same \(x\)-coordinate as \((3, 0)\) is not the nearest one. Minimize the distance. @0; (0, 0) => The derivative of the squared distance at \(x = 0\) is \(-6\), not \(0\), so the vertex is not the critical number. @6

### Question
Find the point on the parabola \(y = x^2\) that is closest to the point \((3, 0)\).

### Solution
0. [pre.geometry.pythagorean] Distance: the quantity to minimize is the distance from the point \((x, y)\) of the parabola to \((3, 0)\), which is \(d = \sqrt{(x - 3)^2 + y^2}\). It is smallest where its square \(D = d^2 = (x - 3)^2 + y^2\) is smallest, and \(D\) is easier to differentiate.
   check: sqrt((x - 3)^2 + y^2)^2 = (x - 3)^2 + y^2
1. [calc1.optimize.one-variable] Constraint: the point is on the parabola, so \(y = x^2\) and \(D(x) = (x - 3)^2 + x^4 = x^4 + x^2 - 6x + 9\).
   check: subs((x - 3)^2 + y^2, y, x^2) = x^4 + x^2 - 6*x + 9
2. [calc1.optimize.domain] Domain: every real number is the first coordinate of a point of the parabola, so the domain is all real numbers, an interval with no endpoints.
3. [calc1.select.optimization-method] Method: the domain has no endpoints, so find the critical numbers and use the sign of the derivative on each side of them.
4. [calc1.deriv.power-rule] Differentiate: \(D'(x) = 4x^3 + 2x - 6\).
   check: diff(x^4 + x^2 - 6*x + 9, x) = 4*x^3 + 2*x - 6
5. [alg.factor.polynomials] Factor: \(x = 1\) is a root, since \(4 + 2 - 6 = 0\), and dividing out \(x - 1\) gives \(D'(x) = 2(x - 1)(2x^2 + 2x + 3)\).
   check: expand(2*(x - 1)*(2*x^2 + 2*x + 3)) = 4*x^3 + 2*x - 6
6. [alg.solve.polynomial] Solve \(D'(x) = 0\): the factor \(2x^2 + 2x + 3 = 2\left(x + \frac{1}{2}\right)^2 + \frac{5}{2}\) is always positive, so the only critical number is \(x = 1\).
   check: expand(2*(x + 1/2)^2 + 5/2) = 2*x^2 + 2*x + 3
   check: solve(4*x^3 + 2*x - 6, x) = {1}
7. [calc1.optimize.open-interval-absolute] Justify: since \(2x^2 + 2x + 3 > 0\), \(D'\) has the sign of \(x - 1\). It is negative on \((-\infty, 1)\) and positive on \((1, \infty)\), so \(D\) decreases and then increases. The only critical number gives the absolute minimum.
   check: subs(4*x^3 + 2*x - 6, x, 0) = -6
   check: subs(4*x^3 + 2*x - 6, x, 2) = 30
8. [calc1.optimize.answer] Answer: at \(x = 1\) the point of the parabola has \(y = 1^2 = 1\), and its distance from \((3, 0)\) is \(\sqrt{5}\). The closest point is \((x, y) = (1, 1)\).

<!-- tier 4: the largest cone inside a ball, with the Pythagorean theorem -->
## Card calc1.4-7.onevar-cone-in-ball.001
skill: calc1.optimize.one-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.pythagorean, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.polynomial, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 4
answer-type: list
answer: 6*sqrt(2), 12
wrong: 72, 12 => The first number is the radius of the base, not its square. @9; 12, 6*sqrt(2) => Give the radius first, then the height. @9

### Question
A craftsman carves a cone from a solid wooden ball of radius \(9\) cm, so that the apex of the cone and the whole rim of its base lie on the surface of the ball. Find the base radius and the height of the cone of greatest volume, in centimeters and in that order.

### Answer
base radius \(6\sqrt{2} \approx 8.49\) cm and height \(12\) cm

### Solution
0. [pre.geometry.area-volume-formulas] Formula: the quantity to maximize is the volume of the cone, with base radius \(r\) and height \(h\) centimeters, so \(V = \frac{1}{3}\pi r^2 h\).
   check: pi*r^2*h/3 = pi*h*r^2/3
1. [pre.geometry.pythagorean] Relation: cut the ball through its center and the axis of the cone. The center of the ball is on the axis, at distance \(|h - 9|\) from the center of the base, and a point of the base rim is \(9\) from the center of the ball. By the Pythagorean theorem, \(r^2 + (h - 9)^2 = 81\), so \(r^2 = 18h - h^2\).
   check: expand(81 - (h - 9)^2) = 18*h - h^2
2. [calc1.optimize.one-variable] Eliminate \(r\): the volume involves \(r\) only through \(r^2\), so \(V(h) = \frac{1}{3}\pi(18h - h^2)h = \frac{\pi}{3}\left(18h^2 - h^3\right)\).
   check: subs(pi*s*h/3, s, 18*h - h^2) = pi*(18*h^2 - h^3)/3
3. [calc1.optimize.domain] Domain: the base plane must cut the ball, so \(0 \le h \le 18\), the diameter of the ball. At both ends \(r^2 = 18h - h^2\) is \(0\). The domain is the closed interval \([0, 18]\).
   check: solve(18*h - h^2, h) = {0, 18}
4. [calc1.select.optimization-method] Method: the domain is a closed interval and the volume function is continuous, so compare the volume at the critical numbers with the volume at both endpoints.
5. [calc1.deriv.power-rule] Differentiate: \(V'(h) = \frac{\pi}{3}\left(36h - 3h^2\right) = \pi\left(12h - h^2\right)\).
   check: diff(pi*(18*h^2 - h^3)/3, h) = pi*(12*h - h^2)
6. [alg.solve.polynomial] Solve \(V'(h) = 0\) by factoring: \(\pi h(12 - h) = 0\), so \(h = 0\) or \(h = 12\). Both lie in \([0, 18]\).
   check: solve(pi*(12*h - h^2), h) = {0, 12}
7. [alg.arith.exact-evaluation] Evaluate: \(V(0) = 0\), \(V(12) = 288\pi\) and \(V(18) = 0\).
   check: subs(pi*(18*h^2 - h^3)/3, h, 0) = 0
   check: subs(pi*(18*h^2 - h^3)/3, h, 12) = 288*pi
   check: subs(pi*(18*h^2 - h^3)/3, h, 18) = 0
8. [calc1.extrema.closed-interval] Compare: the largest value is \(288\pi\), at \(h = 12\), so the absolute maximum of the volume occurs at \(h = 12\).
   check: 288*pi = 288*pi
9. [calc1.optimize.answer] Answer: the base radius is \(r = \sqrt{18 \cdot 12 - 12^2} = \sqrt{72} = 6\sqrt{2} \approx 8.49\) cm and the height is \(12\) cm. The cone has volume \(288\pi \approx 905\) cm³.
   check: sqrt(18*12 - 12^2) = 6*sqrt(2)
   check: {6*sqrt(2), 12} = {6*sqrt(2), 12}

<!-- tier 4: the shortest ladder over a fence, with the length written through an angle -->
## Card calc1.4-7.onevar-fence-ladder.001
skill: calc1.optimize.one-variable
uses: calc1.optimize.objective, trig.right-triangle.ratios, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.trig-other, trig.equations.solve, calc1.optimize.open-interval-absolute, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 4
answer-type: number
answer: 25/2
wrong: atan(3/4) => That is the angle, in radians, that gives the shortest ladder. The question asks for the length of the ladder. @10; 6.4 + 2.7 => That adds the horizontal and the vertical distances. The ladder is longer than either and it is not the sum of the two. @1

### Question
A builder must reach the top of a wall with a straight ladder that rests on level ground and passes over a fence \(2.7\) m high. The fence is parallel to the wall and \(6.4\) m from it, and the foot of the ladder is on the other side of the fence. The ladder touches the top of the fence. What is the length of the shortest ladder that can do this? Give the length in meters.

### Answer
\(12.5\) m

### Solution
0. [calc1.optimize.objective] Objective: the quantity to minimize is the length of the ladder. The ladder is a straight line through the top of the fence, so it splits into the part before the top of the fence and the part after it.
1. [trig.right-triangle.ratios] Lengths: let \(\theta\) be the angle between the ladder and the ground. The part before the fence is the hypotenuse of a right triangle with vertical side \(2.7\), so its length is \(\frac{2.7}{\sin\theta}\). The part after the fence has horizontal run \(6.4\) at the same angle, so its length is \(\frac{6.4}{\cos\theta}\). For example, at \(\theta = 30^\circ\) the first part is \(5.4\) m long.
   check: subs(27/10/sin(t), t, pi/6) = 27/5
   check: subs(32/5/cos(t), t, pi/3) = 64/5
2. [calc1.optimize.one-variable] One variable: both lengths depend only on the angle, so \(L(\theta) = \frac{2.7}{\sin\theta} + \frac{6.4}{\cos\theta}\).
   check: subs(27/10/sin(t) + 32/5/cos(t), t, pi/4) = 27*sqrt(2)/10 + 32*sqrt(2)/5
3. [calc1.optimize.domain] Domain: the ladder is neither flat nor vertical, so the angle is strictly between zero and a right angle. The interval is open.
4. [calc1.select.optimization-method] Method: the domain is an open interval with no endpoints to compare, so find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.trig-other] Differentiate: since \(\frac{d}{d\theta}\csc\theta = -\csc\theta\cot\theta\) and \(\frac{d}{d\theta}\sec\theta = \sec\theta\tan\theta\), \(L'(\theta) = -\frac{2.7\cos\theta}{\sin^2\theta} + \frac{6.4\sin\theta}{\cos^2\theta}\).
   check: diff(27/10/sin(t) + 32/5/cos(t), t) = -27/10*cos(t)/sin(t)^2 + 32/5*sin(t)/cos(t)^2
6. [trig.equations.solve] Solve \(L'(\theta) = 0\): over a common denominator, \(L'(\theta) = \frac{6.4\sin^3\theta - 2.7\cos^3\theta}{\sin^2\theta\cos^2\theta}\). It is zero when \(\tan^3\theta = \frac{2.7}{6.4} = \frac{27}{64}\), that is, \(\tan\theta = \frac{3}{4}\).
   check: -27/10*cos(t)/sin(t)^2 + 32/5*sin(t)/cos(t)^2 = (32/5*sin(t)^3 - 27/10*cos(t)^3)/(sin(t)^2*cos(t)^2)
   check: (27/64)^(1/3) = 3/4
7. [calc1.optimize.open-interval-absolute] Justify: the denominator is positive on the domain, and dividing the numerator by \(\cos^3\theta > 0\) shows that \(L'\) has the sign of \(6.4\tan^3\theta - 2.7 = 6.4\left(\tan^3\theta - \frac{27}{64}\right)\). Since \(\tan\theta\) increases, \(L'\) is negative for \(\tan\theta < \frac{3}{4}\) and positive for \(\tan\theta > \frac{3}{4}\). So \(L\) decreases and then increases, and the only critical number gives the absolute minimum.
   check: 32/5*u^3 - 27/10 = 32/5*(u^3 - 27/64)
8. [trig.right-triangle.ratios] Ratios at the critical angle: \(\tan\theta = \frac{3}{4}\) is the ratio of the sides of a \(3\)-\(4\)-\(5\) right triangle, so \(\sin\theta = \frac{3}{5}\) and \(\cos\theta = \frac{4}{5}\).
   check: sin(atan(3/4)) = 3/5
   check: cos(atan(3/4)) = 4/5
9. [alg.arith.exact-evaluation] Evaluate: \(L = \frac{2.7}{3/5} + \frac{6.4}{4/5} = 4.5 + 8 = 12.5\) m.
   check: subs(27/10/sin(t) + 32/5/cos(t), t, atan(3/4)) = 25/2
10. [calc1.optimize.answer] Answer: the shortest ladder that clears the fence is \(12.5\) m long (the question asks for the length, not for the angle).
   check: 25/2 = 25/2


<!-- ===================================================================== -->
<!-- calc1.optimize.domain                                                 -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-7.domain-example.001
kind: example
skill: calc1.optimize.domain
uses: pre.geometry.area-volume-formulas, calc1.optimize.one-variable, calc1.select.optimization-method, alg.expand.products, calc1.deriv.power-rule, alg.solve.polynomial, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer

### Question
An open box is made from a rectangular sheet of cardboard \(30\) cm by \(48\) cm. A square of side \(x\) cm is cut from each corner, and the sides are folded up. What value of \(x\) gives the box of greatest volume, and what are the dimensions of that box?

### Solution
0. [calc1.optimize.domain] Set up: the volume depends on the side of the cut squares. Before looking for a maximum, say which values of that side are possible: they form the interval on which the maximum is sought, and the size of the sheet limits them.
1. [pre.geometry.area-volume-formulas] Formula: the volume of a box is its length times its width times its height. Cutting \(x\) from both ends of a side removes \(2x\), so the base is \(30 - 2x\) by \(48 - 2x\), and the height is \(x\). For example, \(x = 5\) leaves a base of \(20\) by \(38\).
   check: subs(30 - 2*x, x, 5) = 20
   check: subs(48 - 2*x, x, 5) = 38
2. [calc1.optimize.one-variable] One variable: everything depends on \(x\), so \(V(x) = x(30 - 2x)(48 - 2x)\). For example, \(V(5) = 5 \cdot 20 \cdot 38 = 3800\).
   check: subs(x*(30 - 2*x)*(48 - 2*x), x, 5) = 3800
3. [calc1.optimize.domain] Domain: a cut cannot have negative size, so \(x \ge 0\). The sides of the base must not be negative: \(30 - 2x \ge 0\) gives \(x \le 15\), and \(48 - 2x \ge 0\) gives \(x \le 24\). Both hold only when \(x \le 15\), so the domain is the closed interval \([0, 15]\). The shorter side of the sheet sets the limit.
   check: solve(30 - 2*x, x) = {15}
   check: solve(48 - 2*x, x) = {24}
4. [calc1.select.optimization-method] Method: the domain is a closed interval and the volume is continuous, so compare the volume at the critical numbers inside the interval with the volume at both endpoints.
5. [alg.expand.products] Expand: \(V(x) = 4x^3 - 156x^2 + 1440x\).
   check: expand(x*(30 - 2*x)*(48 - 2*x)) = 4*x^3 - 156*x^2 + 1440*x
6. [calc1.deriv.power-rule] Differentiate: \(V'(x) = 12x^2 - 312x + 1440\).
   check: diff(4*x^3 - 156*x^2 + 1440*x, x) = 12*x^2 - 312*x + 1440
7. [alg.solve.polynomial] Solve \(V'(x) = 0\) by factoring: \(V'(x) = 12(x - 6)(x - 20)\), so \(x = 6\) or \(x = 20\). Only \(x = 6\) lies in \([0, 15]\). The root \(x = 20\) is outside the domain, because it would make \(30 - 2x\) negative, so it is discarded.
   check: factor(12*x^2 - 312*x + 1440) = 12*(x - 6)*(x - 20)
   check: solve(12*x^2 - 312*x + 1440, x) = {6, 20}
8. [alg.arith.exact-evaluation] Evaluate: \(V(0) = 0\), \(V(6) = 3888\) and \(V(15) = 0\).
   check: subs(4*x^3 - 156*x^2 + 1440*x, x, 0) = 0
   check: subs(4*x^3 - 156*x^2 + 1440*x, x, 6) = 3888
   check: subs(4*x^3 - 156*x^2 + 1440*x, x, 15) = 0
9. [calc1.extrema.closed-interval] Compare: the largest of the three values is \(3888\), at \(x = 6\), so the absolute maximum of the volume occurs at \(x = 6\).
   check: 3888 = 3888
10. [calc1.optimize.answer] Answer: cut squares of side \(x = 6\) cm. The base is \(30 - 12 = 18\) cm by \(48 - 12 = 36\) cm and the height is \(6\) cm, so the box is \(18\) cm by \(36\) cm by \(6\) cm, with volume \(3888\) cm³.
   check: 30 - 2*6 = 18
   check: 48 - 2*6 = 36

<!-- tier 1, template: the domain of a pen built against a wall -->
## Card calc1.4-7.domain-fence.t01
skill: calc1.optimize.domain
difficulty: 1
answer-type: interval
vars: L = choice(60, 80, 100, 120, 160, 200, 240); x
answer: [0, L/2]
wrong: [0, L] => The two sides of length \(x\) use \(2x\) meters of fence, and \(2x\) cannot be more than [[L]]. So \(x \le [[L/2]]\). @0; (0, L/2) => A side of length 0 is allowed here, so both endpoints belong to the domain. @0

### Question
A rectangular pen is built against a long barn wall, so fence is needed only on the other three sides: two sides of length \(x\) meters that meet the wall and one side of length \(y\) meters parallel to the wall. All [[L]] m of fence are used, so \(y = [[L]] - 2x\), and the area is \(A(x) = x([[L]] - 2x)\) square meters. Lengths cannot be negative, but a length of \(0\) is allowed. State the domain of \(A\) as an interval.

### Answer
\([0, [[L/2]]]\)

### Solution
0. [calc1.optimize.domain] Domain: \(x \ge 0\), and \(y = [[L]] - 2x \ge 0\) gives \(x \le [[L/2]]\). Both endpoints are allowed, so the domain is \([0, [[L/2]]]\).

<!-- tier 1: the radius of a can with fixed volume is positive -->
## Card calc1.4-7.domain-can.001
skill: calc1.optimize.domain
difficulty: 1
answer-type: interval
answer: (0, inf)
vars: r
wrong: [0, inf) => If \(r = 0\) the can has no base, and \(h = \frac{128}{r^2}\) is undefined, so \(r = 0\) is not allowed. @0; (0, 128) => Nothing limits the radius to 128 cm. Every positive radius works, with height \(\frac{128}{r^2}\). @0

### Question
A closed can must hold exactly \(128\pi\) cm³. With radius \(r\) cm, its height is \(h = \frac{128}{r^2}\) cm, and its surface area is \(S(r) = 2\pi r^2 + \frac{256\pi}{r}\) square centimeters. State the domain of \(S\) as an interval.

### Answer
\((0, \infty)\)

### Solution
0. [calc1.optimize.domain] Domain: the radius must be positive, because \(h = \frac{128}{r^2}\) is undefined at \(r = 0\). Every \(r > 0\) gives a positive height, and nothing else limits \(r\), so the domain is \((0, \infty)\).

<!-- tier 1: two nonnegative numbers with a fixed sum -->
## Card calc1.4-7.domain-sum.001
skill: calc1.optimize.domain
difficulty: 1
answer-type: choice

### Question
Two numbers \(x\) and \(y\) are both at least \(0\), and \(x + y = 18\). Their product is \(P(x) = x(18 - x)\). Which interval is the domain of \(P\)?

### Choices
- [ ] \((0, 18)\)
- [ ] \([0, 9]\)
- [x] \([0, 18]\)
- [ ] \([0, \infty)\)

### Solution
0. [calc1.optimize.domain] Domain: \(x \ge 0\), and \(y = 18 - x \ge 0\) gives \(x \le 18\). A number may equal \(0\), so both endpoints belong to the domain \([0, 18]\).
   check: solve(18 - x, x) = {18}

<!-- tier 2, template: price and attendance -->
## Card calc1.4-7.domain-price.t01
skill: calc1.optimize.domain
difficulty: 2
answer-type: interval
vars: a = choice(600, 800, 1000, 1200); b = choice(20, 25, 40, 50); p
answer: [0, a/b]
wrong: [0, a] => The attendance [[a]] - [[b]]p is not negative only when \(p \le \frac{[[a]]}{[[b]]}\), not when \(p \le [[a]]\). @0; (-inf, a/b] => A price cannot be negative, so the domain starts at 0. @0

### Question
A concert hall sells tickets at \(p\) dollars each. At that price, the number of tickets sold is \(q = [[a]] - [[b]]p\), so the revenue in dollars is \(R(p) = p([[a]] - [[b]]p)\). The price cannot be negative, and the number of tickets sold cannot be negative. State the domain of \(R\) as an interval.

### Answer
\([0, [[a/b]]]\)

### Solution
0. [calc1.optimize.domain] Domain: the price cannot be negative, so \(p \ge 0\). The number of tickets sold cannot be negative, so \([[a]] - [[b]]p \ge 0\), which gives \(p \le [[a/b]]\). The domain is \([0, [[a/b]]]\).

<!-- tier 2, template: a closed box with a fixed surface area -->
## Card calc1.4-7.domain-box-surface.t01
skill: calc1.optimize.domain
difficulty: 2
answer-type: number
vars: S = choice(150, 216, 294, 384, 486, 600)
answer: sqrt(S/2)
wrong: sqrt(S) => The top and the base each have area \(x^2\), so together they use \(2x^2\) of the [[S]] cm². With \(h = 0\), \(2x^2 = [[S]]\). @0; S/2 => The condition is \(2x^2 \le [[S]]\), so \(x^2 \le [[S/2]]\) and \(x \le \sqrt{[[S/2]]}\). @0

### Question
A closed box has a square base of side \(x\) cm and height \(h\) cm. Its total surface area (base, top and four sides) is exactly [[S]] square centimeters, so \(h = \frac{[[S]] - 2x^2}{4x}\), and the volume is \(V(x) = \frac{x([[S]] - 2x^2)}{4}\) cubic centimeters. The height cannot be negative. What is the largest value of \(x\) for which the box can exist? Give \(x\) in centimeters.

### Answer
\(x = \sqrt{[[S/2]]}\) cm

### Solution
0. [calc1.optimize.domain] Domain: the side \(x\) is positive, and the height \(h = \frac{[[S]] - 2x^2}{4x}\) is not negative only if \([[S]] - 2x^2 \ge 0\). So \(x^2 \le [[S/2]]\), and the largest value is \(x = \sqrt{[[S/2]]}\) cm. At that value \(h = 0\).
   check: solve(S - 2*x^2, x) = {-sqrt(S/2), sqrt(S/2)}
   check: sqrt(S/2) = sqrt(S/2)

<!-- tier 2: the angle of a nozzle -->
## Card calc1.4-7.domain-hose.001
skill: calc1.optimize.domain
difficulty: 2
answer-type: interval
answer: [0, pi/2]
vars: t
wrong: [0, pi] => Pointing the nozzle past the vertical would send the water backward. The angle above the horizontal goes from 0 to \(\frac{\pi}{2}\) radians. @0; (0, pi/2) => The nozzle may point exactly horizontally or exactly vertically, so both endpoints are allowed. @0

### Question
A garden hose nozzle at ground level can be tilted from pointing horizontally to pointing straight up. Water leaves it at \(8\) m/s at an angle \(\theta\) above the horizontal, and lands at a horizontal distance of \(R(\theta) \approx 6.53\sin 2\theta\) meters. State the domain of \(R\) as an interval of angles in radians.

### Answer
\([0, \frac{\pi}{2}]\)

### Solution
0. [calc1.optimize.domain] Domain: the nozzle points horizontally at \(\theta = 0\) and straight up at \(\theta = \frac{\pi}{2}\) radians (\(90^\circ\)), and both positions are allowed. So the domain is \([0, \frac{\pi}{2}]\).

<!-- tier 2: which side of the sheet limits the cut -->
## Card calc1.4-7.domain-sheet-limit.001
skill: calc1.optimize.domain
difficulty: 2
answer-type: truefalse
answer: false
wrong: true => Cutting a square of side \(x\) from both ends of the \(24\) cm side leaves \(24 - 2x\), and that cannot be negative. @0

### Question
An open box is made from a rectangular sheet of cardboard \(24\) cm by \(60\) cm, by cutting a square of side \(x\) cm from each corner and folding up the sides. True or false: the value \(x = 20\) is in the domain of the volume function \(V(x) = x(24 - 2x)(60 - 2x)\).

### Solution
0. [calc1.optimize.domain] Domain: the sides of the base must not be negative, so \(24 - 2x \ge 0\) and \(60 - 2x \ge 0\). These give \(x \le 12\) and \(x \le 30\). Both must hold, so \(x \le 12\), and the domain is \([0, 12]\). The value \(x = 20\) is not in it, because the base would have a width of \(24 - 2 \cdot 20 = -16\) cm.
   check: solve(24 - 2*x, x) = {12}
   check: solve(60 - 2*x, x) = {30}
   check: subs(24 - 2*x, x, 20) = -16


<!-- tier 3, template: a short wall moves the maximum to the end of the domain -->
## Card calc1.4-7.domain-barn-wall.t01
skill: calc1.optimize.domain
uses: calc1.optimize.objective, calc1.optimize.one-variable, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: list
vars: L = choice(160, 200, 240, 300); W = choice(40, 50, 60)
require: 3*W < L
answer: W, (L - W)/2
wrong: L/2, L/4 => That pen has the greatest area of all, but its side along the wall would be [[L/2]] m long, and the wall is only [[W]] m long. The length of the wall must limit the domain. @2; (L - W)/2, W => Give the side along the wall first, then the side perpendicular to it. @8

### Question
A rancher has [[L]] m of fence to build a rectangular pen against one straight side of a barn, so the barn wall is one side of the pen and needs no fence. The wall is only [[W]] m long, so the side of the pen along the wall cannot be longer than [[W]] m. Find the dimensions of the pen of greatest area: the side along the wall and then the side perpendicular to it, in meters and in that order.

### Answer
[[W]] m along the wall and [[(L - W)/2]] m perpendicular to it

### Solution
0. [calc1.optimize.objective] Objective: let \(x\) be the length of each of the two sides perpendicular to the wall and \(y\) the length of the side along the wall, in meters. The area to maximize is \(A = xy\).
   check: x*y = x*y
1. [calc1.optimize.one-variable] Constraint: the fence covers two sides of length \(x\) and one of length \(y\), so \(2x + y = [[L]]\) and \(y = [[L]] - 2x\). Then \(A(x) = x([[L]] - 2x) = [[L]]x - 2x^2\).
   check: solve(2*x + y - L, y) = {L - 2*x}
   check: subs(x*y, y, L - 2*x) = L*x - 2*x^2
2. [calc1.optimize.domain] Domain: the sides cannot be negative, so \(x \ge 0\), and \(y = [[L]] - 2x \ge 0\) gives \(x \le [[L/2]]\). The side along the wall must also fit along the wall: \(y \le [[W]]\), so \([[L]] - 2x \le [[W]]\) and \(x \ge [[(L - W)/2]]\). The domain is the closed interval of values of \(x\) from \([[(L - W)/2]]\) to \([[L/2]]\).
   check: solve(L - 2*x - W, x) = {(L - W)/2}
   check: solve(L - 2*x, x) = {L/2}
3. [calc1.select.optimization-method] Method: the domain is a closed interval and the area is continuous, so compare the area at the critical number, if one lies in the interval, with the area at both endpoints.
4. [calc1.deriv.power-rule] Differentiate: \(A'(x) = [[L]] - 4x\).
   check: diff(L*x - 2*x^2, x) = L - 4*x
5. [alg.solve.linear] Solve \(A'(x) = 0\): \(x = [[L/4]]\). The domain starts at \([[(L - W)/2]]\), which is larger, so this critical number is not in the domain and it is discarded.
   check: solve(L - 4*x, x) = {L/4}
6. [alg.arith.exact-evaluation] Evaluate at the endpoints: \(A([[(L - W)/2]]) = [[W*(L - W)/2]]\) and \(A([[L/2]]) = 0\).
   check: subs(x*(L - 2*x), x, (L - W)/2) = W*(L - W)/2
   check: subs(x*(L - 2*x), x, L/2) = 0
7. [calc1.extrema.closed-interval] Compare: no critical number lies in the domain, and \([[W*(L - W)/2]] > 0\), so the absolute maximum of the area occurs at the left endpoint, \(x = [[(L - W)/2]]\). The area decreases as \(x\) grows through the whole domain.
   check: W*(L - W)/2 = W*(L - W)/2
8. [calc1.optimize.answer] Answer: at \(x = [[(L - W)/2]]\) the side along the wall is \(y = [[L]] - 2 \cdot [[(L - W)/2]] = [[W]]\) m. The pen is [[W]] m along the wall and [[(L - W)/2]] m deep, with area [[W*(L - W)/2]] square meters.
   check: subs(L - 2*x, x, (L - W)/2) = W
   check: {W, (L - W)/2} = {W, (L - W)/2}

<!-- tier 3: more people want tickets than there are seats -->
## Card calc1.4-7.domain-venue.001
skill: calc1.optimize.domain
uses: calc1.optimize.objective, calc1.optimize.one-variable, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: number
answer: 30
wrong: 25 => That price maximizes \(p(1000 - 20p)\) on its own, but at $25 about 500 people want tickets and the theater has only 400 seats. The seat limit must be part of the domain. @2; 12000 => That is the greatest revenue, not the ticket price that gives it. @8; 400 => That is the number of tickets sold at the best price, not the price. @8

### Question
A community theater has \(400\) seats. Surveys suggest that at a ticket price of \(p\) dollars, \(1000 - 20p\) people want to buy a ticket, and all of them do. The manager will not set a price at which more people want tickets than there are seats, so that nobody is turned away. What ticket price gives the greatest revenue? Give the price in dollars.

### Answer
a ticket price of $30

### Solution
0. [calc1.optimize.objective] Objective: the revenue is the ticket price times the number of tickets sold, and the revenue is the quantity to maximize.
1. [calc1.optimize.one-variable] One variable: the number of tickets sold is \(1000 - 20p\), so \(R(p) = p(1000 - 20p) = 1000p - 20p^2\).
   check: expand(p*(1000 - 20*p)) = 1000*p - 20*p^2
2. [calc1.optimize.domain] Domain: at most \(400\) people may want tickets, so \(1000 - 20p \le 400\), which gives \(p \ge 30\). The number of buyers cannot be negative, so \(1000 - 20p \ge 0\) and \(p \le 50\). The domain is the closed interval \([30, 50]\).
   check: solve(1000 - 20*p - 400, p) = {30}
   check: solve(1000 - 20*p, p) = {50}
3. [calc1.select.optimization-method] Method: the domain is a closed interval and the revenue is continuous, so compare the revenue at the critical number, if one lies in the interval, with the revenue at both endpoints.
4. [calc1.deriv.power-rule] Differentiate: \(R'(p) = 1000 - 40p\).
   check: diff(1000*p - 20*p^2, p) = 1000 - 40*p
5. [alg.solve.linear] Solve \(R'(p) = 0\): \(p = 25\). This is not in \([30, 50]\), so it is discarded.
   check: solve(1000 - 40*p, p) = {25}
6. [alg.arith.exact-evaluation] Evaluate at the endpoints: \(R(30) = 12000\) and \(R(50) = 0\).
   check: subs(1000*p - 20*p^2, p, 30) = 12000
   check: subs(1000*p - 20*p^2, p, 50) = 0
7. [calc1.extrema.closed-interval] Compare: no critical number lies in the domain, and \(12000 > 0\), so the absolute maximum of the revenue occurs at the left endpoint, \(p = 30\).
   check: 12000 = 12000
8. [calc1.optimize.answer] Answer: the price is $30. At that price \(1000 - 20 \cdot 30 = 400\) people buy tickets, which fills the theater, and the revenue is $12000. The question asks for the price.
   check: 1000 - 20*30 = 400
   check: 30 = 30

<!-- tier 3: the stage in a semicircular plaza -->
## Card calc1.4-7.domain-stage.001
skill: calc1.optimize.domain
uses: calc1.optimize.objective, pre.geometry.pythagorean, calc1.optimize.one-variable, calc1.select.optimization-method, calc1.deriv.chain-rule, calc1.deriv.product-rule, alg.solve.polynomial, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 3
answer-type: list
answer: 5*sqrt(2), 10*sqrt(2)
wrong: 10*sqrt(2), 5*sqrt(2) => Give the depth first, then the width. @9; 5*sqrt(2), 5*sqrt(2) => The two far corners are at \(x\) and \(-x\), so the width of the stage is \(2x = 10\sqrt{2}\), not \(x\). @9

### Question
A plaza is a half-disc of radius \(10\) m, bounded by a straight edge and a curved edge. A rectangular stage is built on the plaza with one side along the straight edge, centered on it, and its two far corners on the curved edge. Find the dimensions of the stage of greatest area: its depth (the side perpendicular to the straight edge) and then its width (the side along the straight edge), in meters and in that order.

### Answer
depth \(5\sqrt{2} \approx 7.07\) m and width \(10\sqrt{2} \approx 14.14\) m

### Solution
0. [calc1.optimize.objective] Objective: put the origin at the middle of the straight edge. The far corners of the stage are \((x, y)\) and \((-x, y)\), so the width is \(2x\) and the depth is \(y\), in meters. The area to maximize is \(A = 2xy\).
   check: 2*x*y = 2*x*y
1. [pre.geometry.pythagorean] Relation: the corner \((x, y)\) is on the curved edge, \(10\) m from the origin, so \(x^2 + y^2 = 10^2\), and \(y = \sqrt{100 - x^2}\).
   check: subs(x^2 + y^2, y, sqrt(100 - x^2)) = 100
2. [calc1.optimize.one-variable] One variable: \(A(x) = 2x\sqrt{100 - x^2}\).
   check: subs(2*x*y, y, sqrt(100 - x^2)) = 2*x*sqrt(100 - x^2)
3. [calc1.optimize.domain] Domain: \(x \ge 0\), and \(100 - x^2 \ge 0\) gives \(x \le 10\). At \(x = 0\) and \(x = 10\) the stage has area zero, and both are allowed. The domain is the closed interval \([0, 10]\).
   check: solve(100 - x^2, x) = {-10, 10}
4. [calc1.select.optimization-method] Method: the domain is a closed interval and the area is continuous, so compare the area at the critical numbers inside the interval with the area at both endpoints.
5. [calc1.deriv.chain-rule] Chain rule: \(\frac{d}{dx}\sqrt{100 - x^2} = \frac{-2x}{2\sqrt{100 - x^2}} = -\frac{x}{\sqrt{100 - x^2}}\).
   check: diff(sqrt(100 - x^2), x) = -x/sqrt(100 - x^2)
6. [calc1.deriv.product-rule] Product rule: \(A'(x) = 2\sqrt{100 - x^2} + 2x\left(-\frac{x}{\sqrt{100 - x^2}}\right) = \frac{200 - 4x^2}{\sqrt{100 - x^2}}\).
   check: diff(2*x*sqrt(100 - x^2), x) = (200 - 4*x^2)/sqrt(100 - x^2)
7. [alg.solve.polynomial] Solve \(A'(x) = 0\): the denominator is positive for \(0 \le x < 10\), so we need \(200 - 4x^2 = 0\), that is \(x^2 = 50\) and \(x = 5\sqrt{2} \approx 7.07\), which lies in \([0, 10]\). (The root \(-5\sqrt{2}\) is outside the domain, and \(A'\) is undefined only at the endpoint \(x = 10\).)
   check: solve(200 - 4*x^2, x) = {-5*sqrt(2), 5*sqrt(2)}
8. [alg.arith.exact-evaluation] Evaluate: \(A(0) = 0\), \(A(5\sqrt{2}) = 100\) and \(A(10) = 0\).
   check: subs(2*x*sqrt(100 - x^2), x, 0) = 0
   check: subs(2*x*sqrt(100 - x^2), x, 5*sqrt(2)) = 100
   check: subs(2*x*sqrt(100 - x^2), x, 10) = 0
9. [calc1.extrema.closed-interval] Compare: the largest value is \(100\), at \(x = 5\sqrt{2}\), so the absolute maximum of the area occurs there.
   check: 100 = 100
10. [calc1.optimize.answer] Answer: the depth is \(y = \sqrt{100 - 50} = 5\sqrt{2} \approx 7.07\) m, and the width is \(2x = 10\sqrt{2} \approx 14.14\) m. The stage has area \(100\) square meters. The question asks for the depth first and then the width.
   check: sqrt(100 - 50) = 5*sqrt(2)
   check: {5*sqrt(2), 10*sqrt(2)} = {5*sqrt(2), 10*sqrt(2)}

<!-- tier 4: a tank with hemispherical caps; the length cannot be negative, so the domain is half open -->
## Card calc1.4-7.domain-capsule.001
skill: calc1.optimize.domain
uses: pre.geometry.area-volume-formulas, calc1.optimize.objective, calc1.optimize.one-variable, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.open-interval-absolute, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 4
answer-type: list
answer: 1, 4
wrong: 2^(2/3), 0 => That treats the caps and the side as costing the same per square meter. The caps cost twice as much, which changes the cost function. @1; 4, 1 => Give the radius first, then the length of the cylindrical part. @9; 1, 6 => The length \(h\) is that of the cylinder only. The two caps add \(2r = 2\) m more, so \(6\) m is the length of the whole tank. @9

### Question
A storage tank for liquefied gas is a cylinder of radius \(r\) meters and length \(h\) meters, with a hemispherical cap on each end. It must hold exactly \(\frac{16\pi}{3}\) cubic meters (about \(16.8\) m³). The plate for the cylindrical side costs $90 per square meter, and the plate for the two caps costs $180 per square meter. Find the radius \(r\) and the length \(h\) of the cylindrical part that minimize the cost of the plate, in meters and in that order.

### Answer
radius \(1\) m and cylinder length \(4\) m

### Solution
0. [pre.geometry.area-volume-formulas] Formulas: the two caps together make a sphere of radius \(r\), with volume \(\frac{4}{3}\pi r^3\) and area \(4\pi r^2\). The cylinder has volume \(\pi r^2 h\) and side area \(2\pi r h\). So the tank holds \(V = \pi r^2 h + \frac{4}{3}\pi r^3\).
   check: subs(pi*r^2*h + 4*pi*r^3/3, r, 1) = pi*h + 4*pi/3
1. [calc1.optimize.objective] Objective: the cost is price times area for each part. The side costs \(90 \cdot 2\pi r h\) and the caps cost \(180 \cdot 4\pi r^2\), so \(C = 180\pi r h + 720\pi r^2\).
   check: 90*(2*pi*r*h) + 180*(4*pi*r^2) = 180*pi*r*h + 720*pi*r^2
2. [calc1.optimize.one-variable] Constraint: \(\pi r^2 h + \frac{4}{3}\pi r^3 = \frac{16\pi}{3}\) gives \(h = \frac{16 - 4r^3}{3r^2}\). Then \(C(r) = 180\pi r \cdot \frac{16 - 4r^3}{3r^2} + 720\pi r^2 = \frac{960\pi}{r} + 480\pi r^2\).
   check: subs(pi*r^2*h + 4*pi*r^3/3, h, (16 - 4*r^3)/(3*r^2)) = 16*pi/3
   check: subs(180*pi*r*h + 720*pi*r^2, h, (16 - 4*r^3)/(3*r^2)) = 960*pi/r + 480*pi*r^2
3. [calc1.optimize.domain] Domain: the radius is positive, and the length of the cylinder cannot be negative, so \(16 - 4r^3 \ge 0\), that is \(r^3 \le 4\) and \(r \le \sqrt[3]{4} \approx 1.59\). At \(r = \sqrt[3]{4}\) the cylinder has length \(0\) and the tank is a sphere. So the domain is the half-open interval \((0, \sqrt[3]{4}]\), with no left endpoint.
   check: solve(16 - 4*r^3, r) = {2^(2/3)}
4. [calc1.select.optimization-method] Method: the domain has no left endpoint, so the closed-interval method does not apply. Find the critical number and use the sign of the derivative on each side of it, up to the right end of the domain.
5. [calc1.deriv.power-rule-rational] Differentiate: \(C'(r) = -\frac{960\pi}{r^2} + 960\pi r\).
   check: diff(960*pi/r + 480*pi*r^2, r) = -960*pi/r^2 + 960*pi*r
6. [alg.solve.rational-equation] Solve \(C'(r) = 0\): multiplying by \(r^2\) (note \(r \ne 0\)) gives \(960\pi r^3 = 960\pi\), so \(r^3 = 1\) and \(r = 1\), which lies in the domain.
   check: solve(-960*pi/r^2 + 960*pi*r, r) = {1}
7. [calc1.optimize.open-interval-absolute] Justify: \(C'(r) = \frac{960\pi(r^3 - 1)}{r^2}\) is negative for \(0 < r < 1\) and positive for \(1 < r \le \sqrt[3]{4}\). So \(C\) decreases and then increases, and the only critical number gives the absolute minimum on the whole domain.
   check: 960*pi*(r^3 - 1)/r^2 = -960*pi/r^2 + 960*pi*r
8. [alg.arith.exact-evaluation] Evaluate the length: \(h = \frac{16 - 4 \cdot 1^3}{3 \cdot 1^2} = 4\).
   check: subs((16 - 4*r^3)/(3*r^2), r, 1) = 4
9. [calc1.optimize.answer] Answer: the radius is \(1\) m and the cylindrical part is \(4\) m long, so the whole tank is \(4 + 2 = 6\) m long. The question asks for \(r\) and then \(h\).
   check: {1, 4} = {1, 4}

<!-- tier 4: a flower bed shaped like a sector; the angle limit decides the domain -->
## Card calc1.4-7.domain-sector.001
skill: calc1.optimize.domain
uses: pre.geometry.area-volume-formulas, calc1.optimize.one-variable, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval, calc1.optimize.answer
difficulty: 4
answer-type: number
answer: 80/(4 + pi)
wrong: 10 => That is the critical number of the area function, but at \(r = 10\) the angle is \(2\) radians, about \(115^\circ\), which is more than \(90^\circ\). The angle limit must be part of the domain. @2; 1600*pi/(4 + pi)^2 => That is the greatest area, not the radius that gives it. @8

### Question
A landscaper edges a flower bed shaped like a sector of a circle (a slice of pie) with exactly \(40\) m of edging, which runs along the two straight sides and the curved side. The bed sits in the corner of a courtyard, so the angle \(\theta\) at its center cannot be more than \(90^\circ\), which is \(\frac{\pi}{2}\) radians. What radius \(r\) gives the bed of greatest area? Give \(r\) in meters.

### Answer
\(r = \dfrac{80}{4 + \pi} \approx 11.2\) m

### Solution
0. [pre.geometry.area-volume-formulas] Formulas: the area to maximize is that of a sector of radius \(r\) meters and central angle \(\theta\) radians, \(A = \frac{1}{2}r^2\theta\), and its arc has length \(r\theta\).
   check: r^2*t/2 = t*r^2/2
1. [calc1.optimize.one-variable] Constraint: the edging is \(2r + r\theta = 40\), so \(\theta = \frac{40 - 2r}{r}\) and \(A(r) = \frac{1}{2}r^2 \cdot \frac{40 - 2r}{r} = 20r - r^2\).
   check: subs(2*r + r*t, t, (40 - 2*r)/r) = 40
   check: subs(r^2*t/2, t, (40 - 2*r)/r) = 20*r - r^2
2. [calc1.optimize.domain] Domain: the angle is not negative, so \(\frac{40 - 2r}{r} \ge 0\) and \(r \le 20\). The angle is at most \(\frac{\pi}{2}\), so \(\frac{40 - 2r}{r} \le \frac{\pi}{2}\), which gives \(40 \le \left(2 + \frac{\pi}{2}\right)r\) and \(r \ge \frac{80}{4 + \pi} \approx 11.2\). The domain is the closed interval of values of \(r\) from \(\frac{80}{4 + \pi}\) to \(20\).
   check: solve(40 - 2*r, r) = {20}
   check: solve((40 - 2*r)/r - pi/2, r) = {80/(pi + 4)}
3. [calc1.select.optimization-method] Method: the domain is a closed interval and the area is continuous, so compare the area at the critical number, if one lies in the interval, with the area at both endpoints.
4. [calc1.deriv.power-rule] Differentiate: \(A'(r) = 20 - 2r\).
   check: diff(20*r - r^2, r) = 20 - 2*r
5. [alg.solve.linear] Solve \(A'(r) = 0\): \(r = 10\). Since \(10 < \frac{80}{4 + \pi} \approx 11.2\), this critical number is not in the domain, and it is discarded.
   check: solve(20 - 2*r, r) = {10}
6. [alg.arith.exact-evaluation] Evaluate at the endpoints: \(A\left(\frac{80}{4 + \pi}\right) = \frac{1600\pi}{(4 + \pi)^2} \approx 98.6\) and \(A(20) = 0\).
   check: subs(20*r - r^2, r, 80/(4 + pi)) = 1600*pi/(4 + pi)^2
   check: subs(20*r - r^2, r, 20) = 0
7. [calc1.extrema.closed-interval] Compare: no critical number lies in the domain, and \(98.6 > 0\), so the absolute maximum of the area occurs at the left endpoint, \(r = \frac{80}{4 + \pi}\).
   check: 1600*pi/(4 + pi)^2 = 1600*pi/(4 + pi)^2
8. [calc1.optimize.answer] Answer: the radius is \(r = \frac{80}{4 + \pi} \approx 11.2\) m. At this radius the angle is exactly \(90^\circ\) and the area is about \(98.6\) square meters. The question asks for the radius.
   check: 80/(pi + 4) = 80/(4 + pi)


<!-- ===================================================================== -->
<!-- calc1.optimize.open-interval-absolute                                 -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-7.open-example.001
kind: example
skill: calc1.optimize.open-interval-absolute
uses: calc1.optimize.objective, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.optimize.answer

### Question
A rectangular storage yard of area \(1200\) m² is to be fenced. The fence along the road costs $50 per meter, and the fence on the other three sides costs $30 per meter. What dimensions give the yard of least cost, and what is that cost?

### Solution
0. [calc1.optimize.open-interval-absolute] Set up: the cost will be a function on an open interval, which has no endpoints whose values could be compared. After finding the critical numbers, the sign of the derivative on each side of a critical number shows whether it gives the absolute minimum.
1. [calc1.optimize.objective] Objective: let \(x\) be the width of the yard along the road and \(y\) its depth, in meters. The front costs \(50x\) dollars, and the other three sides, of total length \(x + 2y\), cost \(30(x + 2y)\) dollars. So \(C = 50x + 30(x + 2y) = 80x + 60y\).
   check: 50*x + 30*(x + 2*y) = 80*x + 60*y
2. [calc1.optimize.one-variable] Constraint: \(xy = 1200\) gives \(y = \frac{1200}{x}\), so \(C(x) = 80x + \frac{72000}{x}\).
   check: subs(x*y, y, 1200/x) = 1200
   check: subs(80*x + 60*y, y, 1200/x) = 80*x + 72000/x
3. [calc1.optimize.domain] Domain: both lengths are positive, and every \(x > 0\) gives a positive \(y = \frac{1200}{x}\), so the domain is \((0, \infty)\).
   check: solve(1200/x, x) = none
4. [calc1.select.optimization-method] Method: the domain is open and unbounded, so find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.power-rule-rational] Differentiate: \(C'(x) = 80 - \frac{72000}{x^2}\).
   check: diff(80*x + 72000/x, x) = 80 - 72000/x^2
6. [alg.solve.rational-equation] Solve \(C'(x) = 0\): \(80x^2 = 72000\), so \(x^2 = 900\) and \(x = 30\) (the root \(x = -30\) is outside the domain).
   check: solve(80 - 72000/x^2, x) = {-30, 30}
7. [calc1.optimize.open-interval-absolute] Justify: the domain has no endpoints, so there is nothing to compare. \(C'(10) = -640 < 0\) and \(C'(60) = 60 > 0\), and \(C'\) changes sign only at \(x = 30\). So \(C\) decreases on \((0, 30)\) and increases on \((30, \infty)\), and the only critical number gives the absolute minimum. (The cost also grows without bound as \(x\) approaches \(0\) and as \(x\) grows, which gives the same conclusion.)
   check: subs(80 - 72000/x^2, x, 10) = -640
   check: subs(80 - 72000/x^2, x, 60) = 60
8. [calc1.optimize.answer] Answer: the yard is \(30\) m wide along the road and \(y = \frac{1200}{30} = 40\) m deep. The least cost is \(C(30) = 4800\) dollars.
   check: 1200/30 = 40
   check: subs(80*x + 72000/x, x, 30) = 4800

<!-- tier 1: the direction of the sign change -->
## Card calc1.4-7.open-direction.001
skill: calc1.optimize.open-interval-absolute
difficulty: 1
answer-type: truefalse
answer: false
wrong: true => The derivative changes from positive to negative at the critical number, so the function rises and then falls. That is a maximum, not a minimum. @0

### Question
The profit \(P(x)\), in thousands of dollars, from selling \(x\) hundred units of a product is a continuous function on \((0, \infty)\). Its derivative is positive on \((0, 5)\) and negative on \((5, \infty)\). True or false: \(P\) has its absolute minimum at \(x = 5\).

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: the derivative is positive to the left of the critical number and negative to the right, so the profit rises and then falls. The value at the critical number is the absolute maximum, not the minimum, so the statement is false.

<!-- tier 1: what a complete justification says -->
## Card calc1.4-7.open-justify.001
skill: calc1.optimize.open-interval-absolute
difficulty: 1
answer-type: choice

### Question
The cost of running a pump for \(x\) hours is \(C(x) = 3x + \frac{48}{x}\) dollars, for \(x > 0\). Its derivative is \(C'(x) = 3 - \frac{48}{x^2}\), and \(x = 4\) is the only critical number. Which statement shows that \(C(4)\) is the absolute minimum cost?

### Choices
- [ ] \(C'(4) = 0\), so \(x = 4\) is a critical number and gives the minimum.
- [ ] \(C(4) = 24\) is smaller than \(C(3) = 25\) and \(C(5) = 24.6\), so \(C(4)\) is the least value.
- [ ] \(C\) has only one critical number, so that number gives the minimum.
- [x] \(C'(x) < 0\) for \(0 < x < 4\) and \(C'(x) > 0\) for \(x > 4\), so \(C\) decreases and then increases.

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: on an open interval with no endpoints, the sign of the derivative on each side of the only critical number decides. \(C'(3) = -\frac{7}{3} < 0\) and \(C'(5) = \frac{27}{25} > 0\), so \(C\) decreases and then increases, and \(C(4)\) is the absolute minimum. A zero derivative at \(x = 4\), a comparison with two nearby values, or the existence of a single critical number does not show this.
   check: subs(3 - 48/x^2, x, 4) = 0
   check: subs(3 - 48/x^2, x, 3) = -7/3
   check: subs(3 - 48/x^2, x, 5) = 27/25

<!-- tier 1, template: test points on each side of the critical number -->
## Card calc1.4-7.open-sign.t01
skill: calc1.optimize.open-interval-absolute
difficulty: 1
answer-type: list
vars: c = choice(2, 4, 6, 8, 10); p = choice(20, 30, 40)
answer: -7*p*c, 7*p*c/2
wrong: 7*p*c/2, -7*p*c => Give the value at \(x = [[c/2]]\) first, then the value at \(x = [[2*c]]\). @0

### Question
An open-top tank with a square base of side \(x\) meters has a fixed volume. Its plate costs $[[p]] per square meter, so the cost of the plate is \(C(x) = [[p]]\left(x^2 + \frac{[[2*c^3]]}{x}\right)\) dollars, for \(x > 0\). The derivative is \(C'(x) = [[p]]\left(2x - \frac{[[2*c^3]]}{x^2}\right)\), and \(C\) has the single critical number \(x = [[c]]\). Find \(C'([[c/2]])\) and \(C'([[2*c]])\), the derivative at one test point on each side of the critical number, in dollars per meter and in that order.

### Answer
\(C'([[c/2]]) = -[[7*p*c]]\) and \(C'([[2*c]]) = [[7*p*c/2]]\), in dollars per meter

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: \(C'([[c/2]]) = [[p]]\left([[c]] - [[8*c]]\right) = -[[7*p*c]] < 0\) and \(C'([[2*c]]) = [[p]]\left([[4*c]] - \frac{[[c]]}{2}\right) = [[7*p*c/2]] > 0\). So \(C\) decreases to the left of the critical number and increases to the right, which shows the absolute minimum.
   check: subs(p*(2*x - 2*c^3/x^2), x, c/2) = -7*p*c
   check: subs(p*(2*x - 2*c^3/x^2), x, 2*c) = 7*p*c/2
   check: {-7*p*c, 7*p*c/2} = {-7*p*c, 7*p*c/2}

<!-- tier 2, template: the smallest value of x + k^2/x -->
## Card calc1.4-7.open-min-value.t01
skill: calc1.optimize.open-interval-absolute
uses: alg.arith.exact-evaluation
difficulty: 2
answer-type: number
vars: k = choice(3, 4, 5, 6, 7, 8, 9, 10, 12)
answer: 2*k
wrong: k => That is the value of \(x\) where the minimum occurs, not the minimum value of \(f\). @1; 1 + k^2 => That is \(f(1)\), the value at a test point. The minimum is the value at the critical number \(x = [[k]]\). @1

### Question
A positive number \(x\) is added to \([[k^2]]\) divided by \(x\), which gives \(f(x) = x + \frac{[[k^2]]}{x}\) for \(x > 0\). The derivative is \(f'(x) = 1 - \frac{[[k^2]]}{x^2}\), and the only critical number is \(x = [[k]]\). What is the smallest possible value of this sum?

### Answer
\([[2*k]]\)

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: the domain \((0, \infty)\) has no endpoints. \(f'(1) = 1 - [[k^2]] < 0\) and \(f'([[2*k]]) = \frac{3}{4} > 0\), and \(f'\) changes sign only at \(x = [[k]]\). So \(f\) decreases and then increases, and the only critical number gives the absolute minimum.
   check: subs(1 - k^2/x^2, x, 1) = 1 - k^2
   check: subs(1 - k^2/x^2, x, 2*k) = 3/4
1. [alg.arith.exact-evaluation] Evaluate: \(f([[k]]) = [[k]] + \frac{[[k^2]]}{[[k]]} = [[2*k]]\).
   check: subs(x + k^2/x, x, k) = 2*k

<!-- tier 2: there is no absolute maximum -->
## Card calc1.4-7.open-no-max.001
skill: calc1.optimize.open-interval-absolute
difficulty: 2
answer-type: number
answer: DNE
wrong: 24 => The critical number gives the least perimeter, \(P(6) = 24\) m, not the largest. As \(x\) approaches \(0\), \(P\) grows without bound. @0

### Question
A rectangle has area \(36\) m². If one side has length \(x\) meters, its perimeter is \(P(x) = 2x + \frac{72}{x}\) meters, for \(x > 0\). What is the largest possible perimeter? Write DNE if there is none.

### Answer
there is none (DNE)

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: as \(x\) approaches \(0\) from the right, \(\frac{72}{x}\) grows without bound, so \(P(x) \to \infty\). A function that is not bounded above has no absolute maximum on \((0, \infty)\). The critical number \(x = 6\) gives the least perimeter, not the largest.
   check: limit(2*x + 72/x, x, 0, right) = inf
   check: DNE = DNE

<!-- tier 2: end behavior on the whole real line -->
## Card calc1.4-7.open-end-behavior.001
skill: calc1.optimize.open-interval-absolute
uses: alg.arith.exact-evaluation
difficulty: 2
answer-type: set
answer: -2, 2
wrong: 0 => \(f(0) = 0\) is larger than \(f(\pm 2) = -16\), so the critical number \(x = 0\) gives a local maximum. @1; -16 => That is the smallest value of \(f\), not the values of \(x\) where it occurs. @1

### Question
The function \(f(x) = x^4 - 8x^2\) is defined for all real numbers, and its critical numbers are \(x = -2\), \(x = 0\) and \(x = 2\). At which values of \(x\) does \(f\) have its absolute minimum?

### Solution
0. [calc1.optimize.open-interval-absolute] Justify: \(f(x) = x^2(x^2 - 8)\) is large and positive when \(|x|\) is large (for example \(f(\pm 10) = 9200\)), and \(f(x) \to \infty\) as \(x \to \infty\) and as \(x \to -\infty\). So the graph rises at both ends. A continuous function with that end behavior has an absolute minimum, and it occurs at a critical number.
   check: x^4 - 8*x^2 = x^2*(x^2 - 8)
   check: subs(x^4 - 8*x^2, x, 10) = 9200
   check: subs(x^4 - 8*x^2, x, -10) = 9200
1. [alg.arith.exact-evaluation] Compare the values at the critical numbers: \(f(-2) = -16\), \(f(0) = 0\) and \(f(2) = -16\). The smallest value is \(-16\), reached at \(x = -2\) and at \(x = 2\).
   check: subs(x^4 - 8*x^2, x, -2) = -16
   check: subs(x^4 - 8*x^2, x, 0) = 0
   check: subs(x^4 - 8*x^2, x, 2) = -16
   check: {-2, 2} = {-2, 2}

<!-- tier 2, template: a half line that includes its left end -->
## Card calc1.4-7.open-halfline.t01
skill: calc1.optimize.open-interval-absolute
uses: alg.solve.polynomial, alg.arith.exact-evaluation
difficulty: 2
answer-type: number
vars: k = choice(3, 6); c = choice(40, 50, 60)
answer: c - 2*k^2/3
wrong: k => That is the time of the lowest temperature, not the temperature itself. @2; c => That is the starting temperature at \(t = 0\), which is higher than the temperature at \(t = [[k]]\). @1

### Question
The temperature of a chemical mixture, in degrees Celsius, \(t\) minutes after the start of a reaction is \(T(t) = \frac{t^3}{[[3*k]]} - [[k]]t + [[c]]\) for \(t \ge 0\). Its derivative is \(T'(t) = \frac{t^2 - [[k^2]]}{[[k]]}\). What is the lowest temperature the mixture reaches? Give the temperature in degrees Celsius.

### Answer
[[c - 2*k^2/3]] degrees Celsius

### Solution
0. [alg.solve.polynomial] Solve \(T'(t) = 0\): the numerator must be zero, \(t^2 - [[k^2]] = (t - [[k]])(t + [[k]]) = 0\), so \(t = [[k]]\) (the root \(t = -[[k]]\) is outside the domain).
   check: solve(t^2 - k^2, t) = {-k, k}
1. [calc1.optimize.open-interval-absolute] Justify: the domain \([0, \infty)\) is unbounded. \(T'(0) = -[[k]] < 0\) and \(T'([[2*k]]) = [[3*k]] > 0\), and \(T'\) changes sign only at \(t = [[k]]\). So \(T\) decreases for \(0 \le t \le [[k]]\) and increases for \(t \ge [[k]]\), and the only critical number gives the absolute minimum. The starting value \(T(0) = [[c]]\) is larger.
   check: subs((t^2 - k^2)/k, t, 0) = -k
   check: subs((t^2 - k^2)/k, t, 2*k) = 3*k
   check: subs(t^3/(3*k) - k*t + c, t, 0) = c
2. [alg.arith.exact-evaluation] Evaluate: \(T([[k]]) = \frac{[[k^3]]}{[[3*k]]} - [[k^2]] + [[c]] = [[k^2/3]] - [[k^2]] + [[c]] = [[c - 2*k^2/3]]\).
   check: subs(t^3/(3*k) - k*t + c, t, k) = c - 2*k^2/3


<!-- tier 3, template: revenue from a subscription whose demand decays exponentially -->
## Card calc1.4-7.open-revenue-exp.t01
skill: calc1.optimize.open-interval-absolute
uses: calc1.optimize.objective, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.chain-linear-inside, calc1.deriv.product-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 3
answer-type: list
vars: A = choice(1000, 2000, 4000); c = choice(2, 3, 4, 5, 6)
answer: c, A*c/e
wrong: A*c/e, c => Give the price first, then the revenue. @9; c, A/e => The second number is the number of subscribers at the best price. The revenue is the price times the number of subscribers. @9

### Question
A software company sells a monthly subscription. When the price is \(p\) dollars per month, about \(q = [[A]]e^{-p/[[c]]}\) people subscribe. Find the monthly price that maximizes the revenue, and that maximum monthly revenue, in dollars and in that order.

### Answer
a price of $[[c]] per month, with a revenue of \(\frac{[[A*c]]}{e}\) dollars per month

### Solution
0. [calc1.optimize.objective] Objective: the revenue is the price times the number of subscribers, and the revenue is the quantity to maximize.
1. [calc1.optimize.one-variable] One variable: the number of subscribers depends on the price, so \(R(p) = p \cdot [[A]]e^{-p/[[c]]} = [[A]]\,p\,e^{-p/[[c]]}\).
   check: p*(A*e^(-p/c)) = A*p*e^(-p/c)
2. [calc1.optimize.domain] Domain: the price is positive and nothing limits it above, so the domain is \((0, \infty)\).
   check: solve(p, p) = {0}
3. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints to compare. Find the critical number and use the sign of the derivative on each side of it.
4. [calc1.deriv.chain-linear-inside] Exponential factor: \(\frac{d}{dp}e^{-p/[[c]]} = -\frac{1}{[[c]]}e^{-p/[[c]]}\).
   check: diff(e^(-p/c), p) = -e^(-p/c)/c
5. [calc1.deriv.product-rule] Product rule: \(R'(p) = [[A]]e^{-p/[[c]]} + [[A]]\,p\left(-\frac{1}{[[c]]}\right)e^{-p/[[c]]} = [[A]]e^{-p/[[c]]}\left(1 - \frac{p}{[[c]]}\right)\).
   check: diff(A*p*e^(-p/c), p) = A*e^(-p/c)*(1 - p/c)
6. [alg.solve.linear] Solve \(R'(p) = 0\): the factor \([[A]]e^{-p/[[c]]}\) is never \(0\), so \(1 - \frac{p}{[[c]]} = 0\) and \(p = [[c]]\).
   check: solve(1 - p/c, p) = {c}
7. [calc1.optimize.open-interval-absolute] Justify: \(R'\) has the sign of \(1 - \frac{p}{[[c]]}\), because \([[A]]e^{-p/[[c]]} > 0\). At \(p = \frac{[[c]]}{2}\) that factor is \(\frac{1}{2} > 0\), and at \(p = [[2*c]]\) it is \(-1 < 0\), and it changes sign only at \(p = [[c]]\). So \(R\) increases and then decreases, and the only critical number gives the absolute maximum.
   check: subs(1 - p/c, p, c/2) = 1/2
   check: subs(1 - p/c, p, 2*c) = -1
8. [alg.arith.exact-evaluation] Evaluate: \(R([[c]]) = [[A]] \cdot [[c]]\,e^{-1} = \frac{[[A*c]]}{e}\).
   check: subs(A*p*e^(-p/c), p, c) = A*c/e
9. [calc1.optimize.answer] Answer: the best price is $[[c]] per month, and the maximum revenue is \(\frac{[[A*c]]}{e}\) dollars per month. The question asks for the price and then the revenue.
   check: {c, A*c/e} = {c, A*c/e}

<!-- tier 3: a funnel rolled from a sector of fixed radius -->
## Card calc1.4-7.open-cone-slant.001
skill: calc1.optimize.open-interval-absolute
uses: pre.geometry.area-volume-formulas, pre.geometry.pythagorean, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule, alg.solve.polynomial, calc1.optimize.answer
difficulty: 3
answer-type: list
answer: 40*sqrt(3)/3, 40*sqrt(6)/3
wrong: 40*sqrt(6)/3, 40*sqrt(3)/3 => Give the height first, then the radius. @8; 40, 0 => The derivative of \(h^3\) is \(3h^2\), so \(V'(h) = \frac{\pi}{3}(1600 - 3h^2)\), not \(\frac{\pi}{3}(1600 - h^2)\). @5

### Question
A funnel is made by rolling a sector cut from a circular sheet of metal of radius \(40\) cm into a cone, so the slant height of the funnel is \(40\) cm. Find the height and the base radius of the funnel of greatest volume, in centimeters and in that order.

### Answer
height \(\frac{40\sqrt{3}}{3} \approx 23.1\) cm and radius \(\frac{40\sqrt{6}}{3} \approx 32.7\) cm

### Solution
0. [pre.geometry.area-volume-formulas] Formula: the quantity to maximize is the volume of the cone, with base radius \(r\) and height \(h\) in centimeters, \(V = \frac{1}{3}\pi r^2 h\).
   check: pi*r^2*h/3 = pi*h*r^2/3
1. [pre.geometry.pythagorean] Relation: the slant height is the hypotenuse of a right triangle with legs \(h\) and \(r\), so \(r^2 + h^2 = 40^2 = 1600\) and \(r^2 = 1600 - h^2\).
   check: subs(r^2 + h^2, r, sqrt(1600 - h^2)) = 1600
2. [calc1.optimize.one-variable] Eliminate \(r\): \(V(h) = \frac{\pi}{3}(1600 - h^2)h = \frac{\pi}{3}\left(1600h - h^3\right)\).
   check: subs(pi*r^2*h/3, r, sqrt(1600 - h^2)) = pi*(1600*h - h^3)/3
3. [calc1.optimize.domain] Domain: the height and the radius are both positive, and \(r\) shrinks to \(0\) as \(h\) grows to \(40\), so \(0 < h < 40\). The domain is the open interval \((0, 40)\).
   check: solve(1600 - h^2, h) = {-40, 40}
4. [calc1.select.optimization-method] Method: the domain is open, so there are no endpoint values to compare. Find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.power-rule] Differentiate: \(V'(h) = \frac{\pi}{3}\left(1600 - 3h^2\right)\).
   check: diff(pi*(1600*h - h^3)/3, h) = pi*(1600 - 3*h^2)/3
6. [alg.solve.polynomial] Solve \(V'(h) = 0\): \(3h^2 = 1600\), so \(h^2 = \frac{1600}{3}\) and \(h = \frac{40\sqrt{3}}{3} \approx 23.1\) (the negative root is outside the domain).
   check: solve(1600 - 3*h^2, h) = {-40*sqrt(3)/3, 40*sqrt(3)/3}
7. [calc1.optimize.open-interval-absolute] Justify: \(V'(10) = \frac{\pi}{3} \cdot 1300 > 0\) and \(V'(30) = \frac{\pi}{3} \cdot (-1100) < 0\), and \(V'\) changes sign only at \(h = \frac{40\sqrt{3}}{3}\). So \(V\) increases and then decreases, and the only critical number gives the absolute maximum. (The volume also tends to \(0\) at both ends of the interval.)
   check: subs(1600 - 3*h^2, h, 10) = 1300
   check: subs(1600 - 3*h^2, h, 30) = -1100
8. [calc1.optimize.answer] Answer: the height is \(\frac{40\sqrt{3}}{3} \approx 23.1\) cm, and the radius is \(r = \sqrt{1600 - \frac{1600}{3}} = \frac{40\sqrt{6}}{3} \approx 32.7\) cm. The funnel holds about \(25.8\) liters. The question asks for the height first.
   check: sqrt(1600 - (40*sqrt(3)/3)^2) = 40*sqrt(6)/3
   check: {40*sqrt(3)/3, 40*sqrt(6)/3} = {40*sqrt(3)/3, 40*sqrt(6)/3}

<!-- tier 3: the cheapest speed for a trip, with a speed limit -->
## Card calc1.4-7.open-truck.001
skill: calc1.optimize.open-interval-absolute
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 3
answer-type: list
answer: 100, 240
wrong: 240, 100 => Give the speed first, then the cost. @7; 120, 244 => The speed limit is the greatest speed allowed, not the cheapest one. At \(120\) km/h the trip costs $244, which is more than at \(100\) km/h. @5

### Question
A truck makes a \(400\) km trip at a constant speed of \(v\) km/h. The driver is paid $30 per hour, and the fuel costs \(0.003v^2\) dollars per hour. The speed limit is \(120\) km/h. Find the speed that minimizes the total cost of the trip, and that minimum cost, in km/h and in dollars, in that order.

### Answer
a speed of \(100\) km/h, with a total cost of $240

### Solution
0. [calc1.optimize.objective] Objective: the trip takes \(\frac{400}{v}\) hours, and each hour costs \(30 + 0.003v^2\) dollars, so the total cost is \(C = \left(30 + 0.003v^2\right)\frac{400}{v} = \frac{12000}{v} + 1.2v\).
   check: (30 + 3*v^2/1000)*(400/v) = 12000/v + 6*v/5
1. [calc1.optimize.domain] Domain: the speed is positive and at most the limit, so \(0 < v \le 120\). The interval has a right endpoint, \(120\), but no left endpoint.
   check: solve(120 - v, v) = {120}
2. [calc1.select.optimization-method] Method: the domain has no left endpoint, so the closed-interval method does not apply. Find the critical number and use the sign of the derivative on each side of it, up to the right end of the domain.
3. [calc1.deriv.power-rule-rational] Differentiate: \(C'(v) = -\frac{12000}{v^2} + 1.2\).
   check: diff(12000/v + 6*v/5, v) = -12000/v^2 + 6/5
4. [alg.solve.rational-equation] Solve \(C'(v) = 0\): \(1.2v^2 = 12000\), so \(v^2 = 10000\) and \(v = 100\) (the root \(v = -100\) is outside the domain).
   check: solve(-12000/v^2 + 6/5, v) = {-100, 100}
5. [calc1.optimize.open-interval-absolute] Justify: \(C'(50) = -3.6 < 0\) and \(C'(120) = \frac{11}{30} > 0\), and \(C'\) changes sign only at \(v = 100\). So \(C\) decreases on \((0, 100)\) and increases on \((100, 120]\), and the only critical number gives the absolute minimum on the whole domain.
   check: subs(-12000/v^2 + 6/5, v, 50) = -18/5
   check: subs(-12000/v^2 + 6/5, v, 120) = 11/30
6. [alg.arith.exact-evaluation] Evaluate: \(C(100) = 120 + 120 = 240\). For comparison, at the speed limit \(C(120) = 100 + 144 = 244\).
   check: subs(12000/v + 6*v/5, v, 100) = 240
   check: subs(12000/v + 6*v/5, v, 120) = 244
7. [calc1.optimize.answer] Answer: the cheapest speed is \(100\) km/h, and the trip then costs $240. The question asks for the speed and then the cost.
   check: {100, 240} = {100, 240}


<!-- tier 4: the shortest piece of a tangent line between the axes -->
## Card calc1.4-7.open-tangent-segment.001
skill: calc1.optimize.open-interval-absolute
uses: calc1.deriv.tangent-line, alg.solve.linear, pre.geometry.pythagorean, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 4
answer-type: list
answer: 1, 2*sqrt(2)
wrong: 2*sqrt(2), 1 => Give the value of \(a\) first, then the length. @9; 1, 8 => The number \(8\) is \(PQ^2\), the square of the length. The length is its square root. @8

### Question
The tangent line to the curve \(y = \frac{1}{x}\) at the point \(\left(a, \frac{1}{a}\right)\), where \(a > 0\), crosses the \(x\)-axis at a point \(P\) and the \(y\)-axis at a point \(Q\). Find the value of \(a\) for which the segment \(PQ\) is shortest, and that shortest length. Give \(a\) first and then the length.

### Answer
\(a = 1\) and a shortest length of \(2\sqrt{2} \approx 2.83\)

### Solution
0. [calc1.deriv.tangent-line] Tangent: for \(f(x) = \frac{1}{x}\) we have \(f'(x) = -\frac{1}{x^2}\), so the slope at \(x = a\) is \(-\frac{1}{a^2}\). The tangent line is \(y = \frac{1}{a} - \frac{x - a}{a^2}\).
   check: diff(1/x, x) = -1/x^2
   check: subs(1/a - (x - a)/a^2, x, a) = 1/a
1. [alg.solve.linear] Intercepts: the line meets the \(x\)-axis where \(y = 0\), at \(x = 2a\), so \(P = (2a, 0)\). It meets the \(y\)-axis where \(x = 0\), at \(y = \frac{2}{a}\), so \(Q = \left(0, \frac{2}{a}\right)\).
   check: subs(1/a - (x - a)/a^2, x, 2*a) = 0
   check: subs(1/a - (x - a)/a^2, x, 0) = 2/a
2. [pre.geometry.pythagorean] Distance: \(PQ^2 = (2a)^2 + \left(\frac{2}{a}\right)^2 = 4a^2 + \frac{4}{a^2}\). The segment is shortest where its square \(D(a) = PQ^2\) is smallest, and \(D\) is easier to differentiate.
   check: (2*a)^2 + (2/a)^2 = 4*a^2 + 4/a^2
3. [calc1.optimize.domain] Domain: the problem requires \(a > 0\), and every \(a > 0\) gives positive intercepts, since \(\frac{2}{a}\) is never \(0\). So the domain is \((0, \infty)\).
   check: solve(2/a, a) = none
4. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints to compare. Find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.power-rule-rational] Differentiate: \(D'(a) = 8a - \frac{8}{a^3}\).
   check: diff(4*a^2 + 4/a^2, a) = 8*a - 8/a^3
6. [alg.solve.rational-equation] Solve \(D'(a) = 0\): multiplying by \(a^3\) (note \(a \ne 0\)) gives \(8a^4 = 8\), so \(a^4 = 1\) and \(a = 1\) (the root \(a = -1\) is outside the domain).
   check: solve(8*a - 8/a^3, a) = {-1, 1}
7. [calc1.optimize.open-interval-absolute] Justify: \(D'(a) = \frac{8(a^4 - 1)}{a^3}\), and \(a^3 > 0\), so \(D'\) is negative for \(0 < a < 1\) and positive for \(a > 1\). So \(D\) decreases and then increases, and the only critical number gives the absolute minimum of \(D\), and therefore of the length \(PQ\).
   check: 8*(a^4 - 1)/a^3 = 8*a - 8/a^3
8. [alg.arith.exact-evaluation] Evaluate: \(D(1) = 4 + 4 = 8\), so the shortest length is \(PQ = \sqrt{8} = 2\sqrt{2} \approx 2.83\).
   check: subs(4*a^2 + 4/a^2, a, 1) = 8
   check: sqrt(8) = 2*sqrt(2)
9. [calc1.optimize.answer] Answer: \(a = 1\), so the tangent point is \((1, 1)\), \(P = (2, 0)\) and \(Q = (0, 2)\). The shortest segment has length \(2\sqrt{2}\). The question asks for \(a\) and then the length.
   check: {1, 2*sqrt(2)} = {1, 2*sqrt(2)}

<!-- tier 4: average cost with a capacity limit; the critical number is outside the domain -->
## Card calc1.4-7.open-avg-cost.001
skill: calc1.optimize.open-interval-absolute
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, alg.arith.exact-evaluation, calc1.optimize.answer
difficulty: 4
answer-type: list
answer: 18.2, 250
wrong: 18, 300 => The critical number \(q = 300\) is beyond the capacity of the factory. The domain stops at \(250\) units. @4; 250, 18.2 => Give the average cost first, then the number of units. @7

### Question
A factory's total weekly cost of making \(q\) units of a product is \(C(q) = 1800 + 6q + 0.02q^2\) dollars: a fixed cost, a cost of $6 per unit, and a cost that grows with the square of the output as machines and staff get crowded. The average cost per unit is \(\frac{C(q)}{q}\). The factory can make at most \(250\) units a week. How many units per week give the least average cost per unit, and what is that average cost? Give the average cost in dollars per unit and then the number of units.

### Answer
an average cost of $18.20 per unit, at \(250\) units per week

### Solution
0. [calc1.optimize.objective] Objective: the quantity to minimize is the average cost per unit, \(c(q) = \frac{C(q)}{q} = \frac{1800}{q} + 6 + 0.02q\) dollars per unit.
   check: (1800 + 6*q + q^2/50)/q = 1800/q + 6 + q/50
1. [calc1.optimize.domain] Domain: the output is positive (the average is not defined at \(q = 0\)) and at most \(250\), so \(0 < q \le 250\). The interval has a right endpoint, \(250\), but no left endpoint.
   check: solve(250 - q, q) = {250}
2. [calc1.select.optimization-method] Method: the domain has no left endpoint, so the closed-interval method does not apply. Use the sign of the derivative on the whole domain.
3. [calc1.deriv.power-rule-rational] Differentiate: \(c'(q) = -\frac{1800}{q^2} + 0.02\).
   check: diff(1800/q + 6 + q/50, q) = -1800/q^2 + 1/50
4. [alg.solve.rational-equation] Solve \(c'(q) = 0\): \(0.02q^2 = 1800\), so \(q^2 = 90000\) and \(q = 300\) (the root \(q = -300\) is outside the domain). But \(300 > 250\), so there is no critical number in the domain.
   check: solve(-1800/q^2 + 1/50, q) = {-300, 300}
5. [calc1.optimize.open-interval-absolute] Justify: \(c'(q) = \frac{q^2 - 90000}{50q^2}\). On the domain \(0 < q \le 250\) we have \(q^2 \le 62500 < 90000\), so \(c'(q) < 0\) at every point of the domain. For example \(c'(250) = -\frac{11}{1250}\). So \(c\) is decreasing on the whole domain, and its absolute minimum is at the right endpoint, \(q = 250\).
   check: (q^2 - 90000)/(50*q^2) = -1800/q^2 + 1/50
   check: subs(-1800/q^2 + 1/50, q, 250) = -11/1250
6. [alg.arith.exact-evaluation] Evaluate: \(c(250) = 7.2 + 6 + 5 = 18.2\).
   check: subs(1800/q + 6 + q/50, q, 250) = 91/5
7. [calc1.optimize.answer] Answer: the least average cost is $18.20 per unit, at the full capacity of \(250\) units per week. (Without the capacity limit the best output would be \(300\) units, at $18 per unit.) The question asks for the average cost and then the number of units.
   check: {91/5, 250} = {91/5, 250}


<!-- ===================================================================== -->
<!-- calc1.optimize.answer                                                 -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-7.answer-example.001
kind: example
skill: calc1.optimize.answer
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.select.optimization-method, alg.expand.products, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval

### Question
A pottery studio sells \(60\) mugs per week at $25 each. A survey suggests that for every $1 the price is reduced, the studio sells \(4\) more mugs per week. What price maximizes the weekly revenue, how many mugs does the studio sell per week at that price, and what is the revenue?

### Solution
0. [calc1.optimize.answer] Set up: the unknown in the equations will be the number of price reductions, but the question asks for a price, a number of mugs and a revenue. Keep track of what each symbol means, and reread the question at the end to report the quantities it asks for, with their units.
1. [calc1.optimize.objective] Objective: let \(x\) be the number of $1 reductions. The price is \(25 - x\) dollars and the weekly sales are \(60 + 4x\) mugs, so the weekly revenue is \(R = (25 - x)(60 + 4x)\) dollars.
   check: subs((25 - x)*(60 + 4*x), x, 5) = 1600
2. [calc1.optimize.domain] Domain: the studio only considers reductions, so \(x \ge 0\), and the price \(25 - x\) cannot be negative, which gives \(x \le 25\). The domain is the closed interval \([0, 25]\).
   check: solve(25 - x, x) = {25}
3. [calc1.select.optimization-method] Method: the domain is a closed interval and the revenue is continuous, so compare the revenue at the critical number with the revenue at both endpoints.
4. [alg.expand.products] Expand: \(R(x) = 1500 + 40x - 4x^2\).
   check: expand((25 - x)*(60 + 4*x)) = 1500 + 40*x - 4*x^2
5. [calc1.deriv.power-rule] Differentiate: \(R'(x) = 40 - 8x\).
   check: diff(1500 + 40*x - 4*x^2, x) = 40 - 8*x
6. [alg.solve.linear] Solve \(R'(x) = 0\): \(x = 5\), which lies in \([0, 25]\).
   check: solve(40 - 8*x, x) = {5}
7. [alg.arith.exact-evaluation] Evaluate: \(R(0) = 1500\), \(R(5) = 1600\) and \(R(25) = 0\).
   check: subs(1500 + 40*x - 4*x^2, x, 0) = 1500
   check: subs(1500 + 40*x - 4*x^2, x, 5) = 1600
   check: subs(1500 + 40*x - 4*x^2, x, 25) = 0
8. [calc1.extrema.closed-interval] Compare: the largest of the three values is \(1600\), at \(x = 5\), so the absolute maximum of the revenue occurs at \(x = 5\).
   check: 1600 = 1600
9. [calc1.optimize.answer] Answer: \(x = 5\) counts the $1 reductions, so the best price is \(25 - 5 = 20\) dollars. At that price the studio sells \(60 + 4 \cdot 5 = 80\) mugs per week, and the weekly revenue is \(20 \cdot 80 = 1600\) dollars. The question asks for the price, the number of mugs and the revenue, not for \(x\).
   check: 25 - 5 = 20
   check: 60 + 4*5 = 80
   check: 20*80 = 1600

<!-- tier 1, template: the variable counts price reductions, the question asks for the price -->
## Card calc1.4-7.answer-price-cut.t01
skill: calc1.optimize.answer
difficulty: 1
answer-type: number
vars: p = choice(12, 14, 16); m = choice(1, 2, 3); k = choice(10, 15)
let: s = k*(p - 2*m)
answer: p - m
wrong: m => That counts the $1 reductions. The question asks for the price itself. @0; p => That is the price before any reduction. @0

### Question
A food truck sells [[s]] lunches per day at $[[p]] each. For every $1 the price is reduced, it sells [[k]] more lunches per day. With \(x\) reductions of $1, the daily revenue is \(R(x) = ([[p]] - x)([[s]] + [[k]]x)\) dollars, and it is greatest when \(x = [[m]]\). What price should the truck charge to get the greatest revenue? Give it in dollars.

### Answer
$[[p - m]]

### Solution
0. [calc1.optimize.answer] Answer: the number \(x = [[m]]\) counts the $1 reductions, not the price. The price after \(x\) reductions is \([[p]] - x\) dollars, which at \(x = [[m]]\) is \([[p]] - [[m]] = [[p - m]]\) dollars.
   check: subs(p - x, x, m) = p - m

<!-- tier 1: which of several true statements answers the question -->
## Card calc1.4-7.answer-which.001
skill: calc1.optimize.answer
difficulty: 1
answer-type: choice

### Question
Squares of side \(x\) cm are cut from the corners of a square sheet of cardboard \(36\) cm on a side, and the sides are folded up to make an open box. The volume \(V(x) = x(36 - 2x)^2\) is greatest when \(x = 6\) cm. The question asks: "What are the dimensions of the box of greatest volume?" Which answer responds to the question?

### Choices
- [x] The box is \(24\) cm by \(24\) cm by \(6\) cm.
- [ ] The cut squares have side \(x = 6\) cm.
- [ ] The greatest volume is \(3456\) cm³.
- [ ] The box is \(36\) cm by \(36\) cm by \(6\) cm.

### Solution
0. [calc1.optimize.answer] Answer: the question asks for the dimensions of the box, which are not the same as the cut \(x\). The height is \(x = 6\) cm, and the base is a square of side \(36 - 2 \cdot 6 = 24\) cm. The volume \(24 \cdot 24 \cdot 6 = 3456\) cm³ is a different quantity, and the sheet is \(36\) cm wide before it is cut.
   check: 36 - 2*6 = 24
   check: 24*24*6 = 3456

<!-- tier 1: the question asks for the value, not for where it occurs -->
## Card calc1.4-7.answer-profit.001
skill: calc1.optimize.answer
difficulty: 1
answer-type: number
answer: 500
wrong: 4 => That is the number of $5 increases, not the profit. @0; 60 => That is the daily rental price that gives the greatest profit, not the profit itself. @0

### Question
A kayak rental shop's daily profit is \(P(x) = 420 + 40x - 5x^2\) dollars, where \(x\) is the number of $5 increases in the daily rental price above $40. The profit is greatest when \(x = 4\). What is the greatest daily profit? Give it in dollars.

### Answer
$500

### Solution
0. [calc1.optimize.answer] Answer: the question asks for the greatest profit, not for where it occurs. Evaluate the profit at \(x = 4\): \(P(4) = 420 + 160 - 80 = 500\) dollars.
   check: subs(420 + 40*x - 5*x^2, x, 4) = 500

<!-- tier 2, template: the greatest height, not the time -->
## Card calc1.4-7.answer-height.t01
skill: calc1.optimize.answer
difficulty: 2
answer-type: number
vars: H = choice(3, 5, 8); v = choice(10, 20, 30)
answer: H + v^2/20
wrong: v/10 => That is the time at which the ball is highest, in seconds, not its height. @0; v^2/20 => That is how far the ball rises above the platform. Add the platform height of [[H]] m. @0

### Question
A small ball is launched straight up from a platform [[H]] m above the ground with an initial speed of [[v]] m/s. Taking \(g = 10\) m/s², its height above the ground after \(t\) seconds is \(h(t) = [[H]] + [[v]]t - 5t^2\) meters, and the ball is highest at \(t = [[v/10]]\) seconds. What is the greatest height of the ball above the ground? Give it in meters.

### Answer
[[H + v^2/20]] m

### Solution
0. [calc1.optimize.answer] Answer: the question asks for the greatest height, not for the time at which it occurs. Evaluate the height at \(t = [[v/10]]\): \(h([[v/10]]) = [[H]] + [[v]] \cdot [[v/10]] - 5 \cdot [[(v/10)^2]] = [[H + v^2/20]]\) meters above the ground.
   check: subs(H + v*t - 5*t^2, t, v/10) = H + v^2/20

<!-- tier 2, template: all the dimensions, in the order asked -->
## Card calc1.4-7.answer-box-dims.t01
skill: calc1.optimize.answer
difficulty: 2
answer-type: list
vars: m = choice(5, 8, 10, 15)
answer: m, 2*m
wrong: 2*m, m => Give the height first, then the base side. @0; 2*m, 2*m => The height is \(h = \frac{[[4*m^3]]}{x^2}\), not \(x\). @0

### Question
An open-top box with a square base must hold exactly \([[4*m^3]]\) cm³. With base side \(x\) cm and height \(h = \frac{[[4*m^3]]}{x^2}\) cm, the material used is least when \(x = [[2*m]]\). Give the dimensions of the box: the height and then the base side, in centimeters.

### Answer
height \([[m]]\) cm and base side \([[2*m]]\) cm

### Solution
0. [calc1.optimize.answer] Answer: the base side is \(x = [[2*m]]\) cm, and the height is \(h = \frac{[[4*m^3]]}{[[2*m]]^2} = [[m]]\) cm. The question asks for the height first and then the base side.
   check: 4*m^3/(2*m)^2 = m
   check: {m, 2*m} = {m, 2*m}

<!-- tier 2: the best whole number is next to the best real number -->
## Card calc1.4-7.answer-whole-number.001
skill: calc1.optimize.answer
difficulty: 2
answer-type: number
answer: 14
wrong: 43/3 => The company can only run a whole number of buses, so the answer cannot be \(\frac{43}{3}\). @0; 15 => Compare the profits: \(P(14) = 3160\) is more than \(P(15) = 3150\). The whole number nearest to \(\frac{43}{3} \approx 14.33\) is \(14\). @0

### Question
A bus company's weekly profit from running \(x\) extra evening buses is \(P(x) = -30x^2 + 860x - 3000\) dollars. If \(x\) could be any real number, the profit would be greatest at \(x = \frac{43}{3} \approx 14.33\). The company can only run a whole number of buses. How many extra buses give the greatest profit?

### Answer
\(14\) extra buses

### Solution
0. [calc1.optimize.answer] Answer: the number of buses must be a whole number, and the profit is a downward parabola, so the best whole number is next to \(\frac{43}{3} \approx 14.33\). Compare the two neighbors: \(P(14) = 3160\) and \(P(15) = 3150\). The greatest profit is at \(x = 14\).
   check: subs(-30*x^2 + 860*x - 3000, x, 14) = 3160
   check: subs(-30*x^2 + 860*x - 3000, x, 15) = 3150
   check: 14 = 14

<!-- tier 2, template: convert the time from hours to minutes -->
## Card calc1.4-7.answer-minutes.t01
skill: calc1.optimize.answer
difficulty: 2
answer-type: number
vars: v = choice(60, 80, 100); d = choice(240, 300, 360, 480)
answer: 60*d/v
wrong: d/v => That is the time in hours. The question asks for minutes, and one hour is \(60\) minutes. @0

### Question
A calculus model shows that a delivery van uses the least fuel per kilometer at a steady speed of [[v]] km/h. How many minutes does a [[d]] km route take at that speed?

### Answer
[[60*d/v]] minutes

### Solution
0. [calc1.optimize.answer] Answer: the time in hours is the distance divided by the speed, \(\frac{[[d]]}{[[v]]} = [[d/v]]\) hours. The question asks for minutes, so multiply by \(60\): \([[d/v]] \cdot 60 = [[60*d/v]]\) minutes.
   check: d/v*60 = 60*d/v


<!-- tier 3, template: crowding lowers the yield of every hive; report three quantities in the order asked -->
## Card calc1.4-7.answer-hives.t01
skill: calc1.optimize.answer
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.select.optimization-method, alg.expand.products, calc1.deriv.power-rule, alg.solve.linear, alg.arith.exact-evaluation, calc1.extrema.closed-interval
difficulty: 3
answer-type: list
vars: n = choice(20, 40, 60); p = choice(30, 34, 36, 40)
require: p > n/2
answer: (p + n/2)/2, p + n/2, (p + n/2)^2/2
wrong: (p + n/2)/2, p - n/2, (p + n/2)^2/2 => The second number is the count of additional hives, \(x = [[p - n/2]]\). The question asks for the total number of hives. @8; p + n/2, (p + n/2)/2, (p + n/2)^2/2 => Give the yield per hive first, then the number of hives. @8

### Question
A beekeeper keeps [[n]] hives in a meadow, and each hive produces [[p]] kg of honey per season. Every additional hive placed in the meadow lowers the yield of every hive by \(0.5\) kg, because the bees compete for the same flowers. Find the number of hives that gives the greatest total harvest, the yield of each hive at that number, and the greatest total harvest. Give the yield per hive in kilograms, then the number of hives, then the total harvest in kilograms.

### Answer
[[(p + n/2)/2]] kg per hive, [[p + n/2]] hives, and a total harvest of [[(p + n/2)^2/2]] kg

### Solution
0. [calc1.optimize.objective] Objective: let \(x\) be the number of additional hives. There are then \([[n]] + x\) hives, each producing \([[p]] - 0.5x\) kg, so the total harvest is \(H(x) = ([[n]] + x)([[p]] - 0.5x)\) kilograms per season.
   check: subs((n + x)*(p - x/2), x, 0) = n*p
1. [calc1.optimize.domain] Domain: \(x \ge 0\), and the yield per hive cannot be negative, \([[p]] - 0.5x \ge 0\), which gives \(x \le [[2*p]]\). The domain is the closed interval \([0, [[2*p]]]\).
   check: solve(p - x/2, x) = {2*p}
2. [calc1.select.optimization-method] Method: the domain is a closed interval and the harvest is continuous, so compare the harvest at the critical number with the harvest at both endpoints.
3. [alg.expand.products] Expand: \(H(x) = [[n*p]] + [[p - n/2]]x - 0.5x^2\).
   check: expand((n + x)*(p - x/2)) = n*p + (p - n/2)*x - x^2/2
4. [calc1.deriv.power-rule] Differentiate: \(H'(x) = [[p - n/2]] - x\).
   check: diff(n*p + (p - n/2)*x - x^2/2, x) = p - n/2 - x
5. [alg.solve.linear] Solve \(H'(x) = 0\): \(x = [[p - n/2]]\), which lies in \([0, [[2*p]]]\).
   check: solve(p - n/2 - x, x) = {p - n/2}
6. [alg.arith.exact-evaluation] Evaluate: \(H(0) = [[n*p]]\), \(H([[p - n/2]]) = [[(p + n/2)^2/2]]\) and \(H([[2*p]]) = 0\).
   check: subs(n*p + (p - n/2)*x - x^2/2, x, 0) = n*p
   check: subs(n*p + (p - n/2)*x - x^2/2, x, p - n/2) = (p + n/2)^2/2
   check: subs(n*p + (p - n/2)*x - x^2/2, x, 2*p) = 0
7. [calc1.extrema.closed-interval] Compare: the largest of the three values is \([[(p + n/2)^2/2]]\), at \(x = [[p - n/2]]\), because it exceeds \(H(0)\) by \(\frac{1}{2}([[p - n/2]])^2 > 0\). So the absolute maximum of the harvest occurs at \(x = [[p - n/2]]\).
   check: (p + n/2)^2/2 - n*p = (p - n/2)^2/2
8. [calc1.optimize.answer] Answer: \(x = [[p - n/2]]\) counts additional hives, so the meadow should hold \([[n]] + [[p - n/2]] = [[p + n/2]]\) hives. Each hive then produces \([[p]] - 0.5 \cdot [[p - n/2]] = [[(p + n/2)/2]]\) kg, and the total harvest is \([[p + n/2]] \cdot [[(p + n/2)/2]] = [[(p + n/2)^2/2]]\) kg per season. The question asks for the yield per hive, the number of hives and the total harvest, in that order.
   check: n + (p - n/2) = p + n/2
   check: p - (p - n/2)/2 = (p + n/2)/2
   check: {(p + n/2)/2, p + n/2, (p + n/2)^2/2} = {(p + n/2)/2, p + n/2, (p + n/2)^2/2}

<!-- tier 3: a crate whose base is twice as long as it is wide; the second derivative decides, and the area is asked in square meters -->
## Card calc1.4-7.answer-crate.001
skill: calc1.optimize.answer
uses: pre.geometry.area-volume-formulas, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.shape.second-derivative-test, alg.arith.exact-evaluation
difficulty: 3
answer-type: list
answer: 1.08, 30, 40, 60
wrong: 10800, 30, 40, 60 => The area \(10800\) is in square centimeters. The question asks for square meters, and \(1\ \text{m}^2 = 10000\ \text{cm}^2\). @8; 1.08, 30, 60, 40 => Give the width, then the height, then the length. @8

### Question
A closed storage crate with a rectangular base must hold exactly \(72\) liters, which is \(72000\) cm³. The length of the base is twice its width. Find the dimensions of the crate that uses the least material, and the surface area of that crate. Give the surface area in square meters first, and then the width, the height and the length in centimeters, in that order.

### Answer
a surface area of \(1.08\) m², with width \(30\) cm, height \(40\) cm and length \(60\) cm

### Solution
0. [pre.geometry.area-volume-formulas] Formulas: let the width be \(x\) cm, so the length is \(2x\) cm, and let the height be \(h\) cm. The volume is \(2x \cdot x \cdot h = 2x^2h = 72000\), so \(h = \frac{36000}{x^2}\). The material is the surface area of the six faces, \(S = 2(2x \cdot x) + 2(2x \cdot h) + 2(x \cdot h) = 4x^2 + 6xh\).
   check: subs(2*x^2*h, h, 36000/x^2) = 72000
   check: 2*(2*x*x) + 2*(2*x*h) + 2*(x*h) = 4*x^2 + 6*x*h
1. [calc1.optimize.one-variable] Eliminate \(h\): \(S(x) = 4x^2 + 6x \cdot \frac{36000}{x^2} = 4x^2 + \frac{216000}{x}\).
   check: subs(4*x^2 + 6*x*h, h, 36000/x^2) = 4*x^2 + 216000/x
2. [calc1.optimize.domain] Domain: the width is positive and nothing else limits it, so the domain is \((0, \infty)\).
   check: solve(x, x) = {0}
3. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints to compare. Find the critical number, and decide whether it gives a minimum from the sign of the second derivative on the whole domain.
4. [calc1.deriv.power-rule-rational] Differentiate: \(S'(x) = 8x - \frac{216000}{x^2}\).
   check: diff(4*x^2 + 216000/x, x) = 8*x - 216000/x^2
5. [alg.solve.rational-equation] Solve \(S'(x) = 0\): multiplying by \(x^2\) (note \(x \ne 0\)) gives \(8x^3 = 216000\), so \(x^3 = 27000\) and \(x = 30\).
   check: solve(8*x - 216000/x^2, x) = {30}
6. [calc1.shape.second-derivative-test] Justify: \(S''(x) = 8 + \frac{432000}{x^3}\), which is positive for every \(x > 0\). So \(S\) is concave up on the whole domain, and the only critical number gives the absolute minimum. (At the critical number \(S''(30) = 24 > 0\).)
   check: diff(8*x - 216000/x^2, x) = 8 + 432000/x^3
   check: subs(8 + 432000/x^3, x, 30) = 24
7. [alg.arith.exact-evaluation] Evaluate: \(h = \frac{36000}{30^2} = 40\), and \(S(30) = 3600 + 7200 = 10800\) cm².
   check: 36000/30^2 = 40
   check: subs(4*x^2 + 216000/x, x, 30) = 10800
8. [calc1.optimize.answer] Answer: the width is \(30\) cm, the height is \(40\) cm and the length is \(2 \cdot 30 = 60\) cm. The least surface area is \(10800\) cm², and since \(1\ \text{m}^2 = 10000\ \text{cm}^2\), it is \(1.08\) m². The question asks for the area in square meters first, and then the width, the height and the length in centimeters.
   check: 2*30 = 60
   check: 10800/10000 = 27/25
   check: {27/25, 30, 40, 60} = {27/25, 30, 40, 60}

<!-- tier 3: the time of the peak is asked in minutes, but the model uses hours -->
## Card calc1.4-7.answer-drug.001
skill: calc1.optimize.answer
uses: calc1.select.optimization-method, calc1.deriv.quotient-rule, alg.solve.polynomial, alg.arith.exact-evaluation, calc1.extrema.closed-interval
difficulty: 3
answer-type: list
answer: 2, 90
wrong: 2, 3/2 => The time \(t = \frac{3}{2}\) is in hours. The question asks for minutes, so multiply by \(60\). @5; 90, 2 => Give the concentration first, then the time. @5

### Question
A drug is given by injection. For the first \(12\) hours, the concentration of the drug in a patient's blood is \(C(t) = \dfrac{24t}{4t^2 + 9}\) milligrams per liter, where \(t\) is the number of hours after the injection. Find the greatest concentration during these \(12\) hours and the time at which it occurs. Give the concentration in mg/L and then the time in minutes after the injection.

### Answer
a greatest concentration of \(2\) mg/L, \(90\) minutes after the injection

### Solution
0. [calc1.select.optimization-method] Method: the concentration is continuous on the closed interval from 0 to 12 hours, because its denominator is never zero. So compare its values at the critical numbers inside the interval with its values at both endpoints.
1. [calc1.deriv.quotient-rule] Differentiate: \(C'(t) = \dfrac{24(4t^2 + 9) - 24t \cdot 8t}{(4t^2 + 9)^2} = \dfrac{24(9 - 4t^2)}{(4t^2 + 9)^2}\).
   check: diff(24*t/(4*t^2 + 9), t) = 24*(9 - 4*t^2)/(4*t^2 + 9)^2
2. [alg.solve.polynomial] Solve \(C'(t) = 0\): the denominator is never zero, so \(9 - 4t^2 = 0\), which gives \(t = \pm\frac{3}{2}\). Only \(t = \frac{3}{2}\) lies in the interval.
   check: solve(24*(9 - 4*t^2)/(4*t^2 + 9)^2, t) = {-3/2, 3/2}
3. [alg.arith.exact-evaluation] Evaluate: \(C(0) = 0\), \(C\left(\frac{3}{2}\right) = \frac{36}{18} = 2\) and \(C(12) = \frac{288}{585} = \frac{32}{65} \approx 0.49\).
   check: subs(24*t/(4*t^2 + 9), t, 0) = 0
   check: subs(24*t/(4*t^2 + 9), t, 3/2) = 2
   check: subs(24*t/(4*t^2 + 9), t, 12) = 32/65
4. [calc1.extrema.closed-interval] Compare: the largest of the three values is \(2\), at \(t = \frac{3}{2}\), so the absolute maximum of the concentration on the interval occurs at \(t = \frac{3}{2}\).
   check: 2 = 2
5. [calc1.optimize.answer] Answer: the greatest concentration is \(2\) mg/L. It occurs at \(t = \frac{3}{2}\) hours, and the question asks for minutes, so the time is \(\frac{3}{2} \cdot 60 = 90\) minutes after the injection. The question asks for the concentration first and then the time.
   check: 3/2*60 = 90
   check: {2, 90} = {2, 90}


<!-- tier 4: maximum power transfer; four quantities are asked, and one of them is a percentage -->
## Card calc1.4-7.answer-power.001
skill: calc1.optimize.answer
uses: calc1.optimize.objective, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.quotient-rule, alg.solve.linear, calc1.optimize.open-interval-absolute, alg.arith.exact-evaluation
difficulty: 4
answer-type: list
answer: 2, 3, 12, 50
wrong: 3, 2, 12, 50 => Give the current first, then the resistance. @7; 2, 3, 24, 50 => The battery supplies \(EI = 24\) W in total, but the load receives only \(I^2R = 12\) W. The question asks for the power delivered to the load. @7; 2, 3, 12, 0.5 => The question asks for a percentage, so write \(50\), not the fraction \(0.5\). @7

### Question
A battery with voltage \(E = 12\) V and internal resistance \(r = 3\ \Omega\) is connected to a load whose resistance \(R\) ohms can be adjusted. The current is \(I = \dfrac{E}{R + r}\) amperes, the power delivered to the load is \(P = I^2R\) watts, and the battery supplies a total power of \(EI\) watts. Find the load resistance that delivers the greatest power to the load. At that setting, find the current, the power delivered to the load, and the percentage of the battery's total power that reaches the load. Give the current in amperes, the resistance in ohms, the power in watts, and the percentage, in that order.

### Answer
a current of \(2\) A with a load of \(3\ \Omega\), delivering \(12\) W, which is \(50\%\) of the battery's total power

### Solution
0. [calc1.optimize.objective] Objective: the quantity to maximize is the power delivered to the load. With \(I = \frac{12}{R + 3}\), the power is \(P = I^2R = \frac{144R}{(R + 3)^2}\) watts.
   check: (12/(R + 3))^2*R = 144*R/(R + 3)^2
1. [calc1.optimize.domain] Domain: a resistance is positive, and nothing limits it above, so the domain is \((0, \infty)\).
   check: solve(R, R) = {0}
2. [calc1.select.optimization-method] Method: the domain is open and unbounded, so there are no endpoints to compare. Find the critical number and use the sign of the derivative on each side of it.
3. [calc1.deriv.quotient-rule] Differentiate: \(P'(R) = \dfrac{144(R + 3)^2 - 144R \cdot 2(R + 3)}{(R + 3)^4}\). Cancelling a factor \(R + 3\) gives \(P'(R) = \dfrac{144(3 - R)}{(R + 3)^3}\).
   check: diff(144*R/(R + 3)^2, R) = 144*(3 - R)/(R + 3)^3
4. [alg.solve.linear] Solve \(P'(R) = 0\): the denominator is positive, so the numerator must be zero, \(3 - R = 0\), and \(R = 3\).
   check: solve(144*(3 - R)/(R + 3)^3, R) = {3}
5. [calc1.optimize.open-interval-absolute] Justify: for \(R > 0\) the factor \((R + 3)^3\) is positive, so \(P'\) has the sign of \(3 - R\). It is positive for \(R < 3\), for example \(P'(1) = \frac{9}{2}\), and negative for \(R > 3\), for example \(P'(9) = -\frac{1}{2}\). So \(P\) increases and then decreases, and the only critical number gives the absolute maximum.
   check: subs(144*(3 - R)/(R + 3)^3, R, 1) = 9/2
   check: subs(144*(3 - R)/(R + 3)^3, R, 9) = -1/2
6. [alg.arith.exact-evaluation] Evaluate at \(R = 3\): the current is \(I = \frac{12}{3 + 3} = 2\) A, the power in the load is \(P = I^2R = 4 \cdot 3 = 12\) W, the battery supplies \(EI = 12 \cdot 2 = 24\) W, and the share that reaches the load is \(\frac{12}{24} \cdot 100 = 50\) percent.
   check: 12/(3 + 3) = 2
   check: 2^2*3 = 12
   check: 12*2 = 24
   check: 12/24*100 = 50
7. [calc1.optimize.answer] Answer: the load delivers the greatest power when \(R = 3\ \Omega\). At that setting the current is \(2\) A, the power in the load is \(12\) W, and \(50\%\) of the battery's power reaches the load (the other half is lost in the internal resistance). The question asks for the current, the resistance, the power and the percentage, in that order.
   check: {2, 3, 12, 50} = {2, 3, 12, 50}

<!-- tier 4: a trapezoid in a semicircle; the variable is half of the base that the question asks for -->
## Card calc1.4-7.answer-trapezoid.001
skill: calc1.optimize.answer
uses: pre.geometry.area-volume-formulas, pre.geometry.pythagorean, calc1.optimize.one-variable, calc1.optimize.domain, calc1.select.optimization-method, calc1.deriv.chain-rule, calc1.deriv.product-rule, alg.factor.polynomials, calc1.optimize.open-interval-absolute, alg.arith.exact-evaluation
difficulty: 4
answer-type: list
answer: 5*sqrt(3), 10, 75*sqrt(3)
wrong: 5*sqrt(3), 5, 75*sqrt(3) => The number \(x = 5\) is half of the shorter base. The shorter base is \(2x = 10\) m long. @10; 10, 5*sqrt(3), 75*sqrt(3) => Give the depth first, then the length of the shorter base. @10

### Question
A trapezoidal flower bed is to be laid out inside a semicircular lawn of radius \(10\) m. The longer base of the bed lies along the straight edge of the lawn, and the two ends of the shorter base touch the curved edge. Find the dimensions of the bed of greatest area, and that area. Give the depth of the bed (the distance between its two bases) in meters, the length of the shorter base in meters, and the area in square meters, in that order.

### Answer
depth \(5\sqrt{3} \approx 8.66\) m, shorter base \(10\) m, and area \(75\sqrt{3} \approx 129.9\) m²

### Solution
0. [pre.geometry.area-volume-formulas] Formula: put the center of the straight edge at the origin, so the longer base is the diameter, \(20\) m long, and the ends of the shorter base are \((-x, y)\) and \((x, y)\) with \(0 < x < 10\). The shorter base is \(2x\) m long and the depth of the bed is \(y\) m. The area of a trapezoid is half the sum of the bases times the depth, so \(A = \frac{1}{2}(20 + 2x)y = (10 + x)y\).
   check: (20 + 2*x)*y/2 = (10 + x)*y
1. [pre.geometry.pythagorean] Relation: the point \((x, y)\) lies on the circle of radius \(10\) about the origin, so \(x^2 + y^2 = 100\) and \(y = \sqrt{100 - x^2}\).
   check: subs(x^2 + y^2, y, sqrt(100 - x^2)) = 100
2. [calc1.optimize.one-variable] Eliminate \(y\): \(A(x) = (10 + x)\sqrt{100 - x^2}\).
   check: subs((10 + x)*y, y, sqrt(100 - x^2)) = (10 + x)*sqrt(100 - x^2)
3. [calc1.optimize.domain] Domain: the shorter base has positive length and the bed has positive depth, so \(0 < x < 10\). The domain is the open interval \((0, 10)\).
   check: solve(100 - x^2, x) = {-10, 10}
4. [calc1.select.optimization-method] Method: the domain is open, so there are no endpoint values to compare. Find the critical number and use the sign of the derivative on each side of it.
5. [calc1.deriv.chain-rule] Chain rule: \(\dfrac{d}{dx}\sqrt{100 - x^2} = -\dfrac{x}{\sqrt{100 - x^2}}\).
   check: diff(sqrt(100 - x^2), x) = -x/sqrt(100 - x^2)
6. [calc1.deriv.product-rule] Product rule: \(A'(x) = \sqrt{100 - x^2} + (10 + x)\left(-\dfrac{x}{\sqrt{100 - x^2}}\right) = \dfrac{100 - 10x - 2x^2}{\sqrt{100 - x^2}}\).
   check: diff((10 + x)*sqrt(100 - x^2), x) = (100 - 10*x - 2*x^2)/sqrt(100 - x^2)
7. [alg.factor.polynomials] Factor and solve: \(100 - 10x - 2x^2 = -2(x + 10)(x - 5)\), so \(A'(x) = 0\) at \(x = 5\) or \(x = -10\). Only \(x = 5\) lies in \((0, 10)\).
   check: -2*(x + 10)*(x - 5) = 100 - 10*x - 2*x^2
   check: solve(100 - 10*x - 2*x^2, x) = {-10, 5}
8. [calc1.optimize.open-interval-absolute] Justify: on \((0, 10)\) the denominator \(\sqrt{100 - x^2}\) and the factor \(x + 10\) are positive, so \(A'\) has the sign of \(5 - x\). For example, the numerator \(100 - 10x - 2x^2\) is \(88 > 0\) at \(x = 1\) and \(-152 < 0\) at \(x = 9\). So \(A\) increases and then decreases, and the only critical number gives the absolute maximum.
   check: subs(100 - 10*x - 2*x^2, x, 1) = 88
   check: subs(100 - 10*x - 2*x^2, x, 9) = -152
9. [alg.arith.exact-evaluation] Evaluate: \(y = \sqrt{100 - 5^2} = \sqrt{75} = 5\sqrt{3} \approx 8.66\), and \(A(5) = 15 \cdot 5\sqrt{3} = 75\sqrt{3} \approx 129.9\).
   check: sqrt(100 - 5^2) = 5*sqrt(3)
   check: subs((10 + x)*sqrt(100 - x^2), x, 5) = 75*sqrt(3)
10. [calc1.optimize.answer] Answer: \(x = 5\) is half of the shorter base, so the shorter base is \(2x = 10\) m long. The depth of the bed is \(5\sqrt{3} \approx 8.66\) m, and the greatest area is \(75\sqrt{3} \approx 129.9\) m². The question asks for the depth, the shorter base and the area, in that order.
   check: 2*5 = 10
   check: {5*sqrt(3), 10, 75*sqrt(3)} = {5*sqrt(3), 10, 75*sqrt(3)}


<!-- ===================================================================== -->
<!-- calc1.select.optimization-method                                      -->
<!-- ===================================================================== -->

<!-- worked example: the same function, two domains, two methods -->
## Card calc1.4-7.method-example.001
kind: example
skill: calc1.select.optimization-method
uses: calc1.deriv.power-rule-rational, alg.solve.rational-equation, calc1.shape.second-derivative-test, alg.arith.exact-evaluation, calc1.extrema.closed-interval

### Question
A rectangular plot of area \(900\) m² is fenced on all four sides. If the plot has width \(x\) meters, the length of fence is \(P(x) = 2x + \dfrac{1800}{x}\) meters. Find the least length of fence (a) if the width can be any positive number, and (b) if the plot lies between two buildings, so the width must be between \(40\) m and \(60\) m.

### Solution
0. [calc1.select.optimization-method] Set up (a): the width can be any positive number, so the domain is open and unbounded. There are no endpoints, so the closed-interval method is not available. The second derivative of this fence function is easy to sign on the whole domain, so use concavity.
1. [calc1.deriv.power-rule-rational] Differentiate: \(P'(x) = 2 - \dfrac{1800}{x^2}\).
   check: diff(2*x + 1800/x, x) = 2 - 1800/x^2
2. [alg.solve.rational-equation] Solve \(P'(x) = 0\): \(2x^2 = 1800\), so \(x^2 = 900\) and \(x = 30\) (the root \(x = -30\) is outside the domain).
   check: solve(2 - 1800/x^2, x) = {-30, 30}
3. [calc1.shape.second-derivative-test] Justify: \(P''(x) = \dfrac{3600}{x^3}\) is positive for every \(x > 0\), so \(P\) is concave up on the whole domain, and the only critical number gives the absolute minimum.
   check: diff(2 - 1800/x^2, x) = 3600/x^3
4. [alg.arith.exact-evaluation] Evaluate: \(P(30) = 60 + 60 = 120\). So in part (a) the least length of fence is \(120\) m, for a square plot \(30\) m by \(30\) m.
   check: subs(2*x + 1800/x, x, 30) = 120
5. [calc1.select.optimization-method] Set up (b): now the domain is the interval from 40 to 60, which is closed and bounded, and P is continuous on it, so use the closed-interval method. The critical number found above, 30, is outside the interval, so it is not a candidate, and only the two ends compete.
6. [alg.arith.exact-evaluation] Evaluate: \(P(40) = 80 + 45 = 125\) and \(P(60) = 120 + 30 = 150\).
   check: subs(2*x + 1800/x, x, 40) = 125
   check: subs(2*x + 1800/x, x, 60) = 150
7. [calc1.extrema.closed-interval] Compare: \(125 < 150\), so in part (b) the least length of fence is \(125\) m, at \(x = 40\), for a plot \(40\) m wide and \(22.5\) m long.
   check: 900/40 = 45/2

<!-- tier 1: a closed and bounded domain -->
## Card calc1.4-7.method-closed.001
kind: method
skill: calc1.select.optimization-method
difficulty: 1
answer-type: choice

### Question
A bakery's daily profit from baking \(x\) loaves is \(P(x) = -0.02x^2 + 8x - 100\) dollars, where \(0 \le x \le 250\) because the ovens hold at most \(250\) loaves. Which approach finds the greatest daily profit and shows that it is the greatest?

### Choices
- [x] Compare the profit at the critical number with the profit at both ends, \(x = 0\) and \(x = 250\)
- [ ] Solve \(P'(x) = 0\) and report the solution, with no further check
- [ ] Compare the profit at the two ends only, because the greatest value of a continuous function is always at an end
- [ ] Find where \(P''(x) = 0\) and test those points

### Solution
0. [calc1.select.optimization-method] Set up: the domain \([0, 250]\) is closed and bounded and \(P\) is continuous on it, so use the closed-interval method. The derivative \(P'(x) = -0.04x + 8\) is zero at \(x = 200\), which is inside the interval, so compare \(P(0) = -100\), \(P(200) = 700\) and \(P(250) = 650\). The greatest daily profit is $700, at \(x = 200\).
   check: solve(diff(-x^2/50 + 8*x - 100, x), x) = {200}
   check: subs(-x^2/50 + 8*x - 100, x, 0) = -100
   check: subs(-x^2/50 + 8*x - 100, x, 200) = 700
   check: subs(-x^2/50 + 8*x - 100, x, 250) = 650

<!-- tier 1, template: an open and unbounded domain with one critical number -->
## Card calc1.4-7.method-open.t01
kind: method
skill: calc1.select.optimization-method
difficulty: 1
answer-type: choice
vars: a = choice(2, 3, 5); k = choice(3, 4, 5, 6)

### Question
A print shop's average cost per poster, in cents, when it prints \(x\) hundred posters in one run is \(A(x) = [[a]]x + \dfrac{[[a*k^2]]}{x}\), where \(x > 0\) and there is no upper limit on the size of a run. Which approach finds the run size with the least average cost and shows that it is the least?

### Choices
- [ ] Compare the average cost at the two ends of the domain
- [x] Find the one critical number and show that \(A'\) changes sign there, from negative to positive
- [ ] Find where \(A''(x) = 0\) and test those points
- [ ] Solve \(A'(x) = 0\) and report the solution, since a critical number is always the minimum

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(x > 0\) is open and unbounded, so there are no endpoints to compare and the closed-interval method does not apply. The derivative \(A'(x) = [[a]] - \dfrac{[[a*k^2]]}{x^2}\) is zero only at \(x = [[k]]\) in the domain, so use the sign of \(A'\) on each side of \([[k]]\): negative before it and positive after it.
   check: solve(diff(a*x + a*k^2/x, x), x) = {-k, k}

<!-- tier 1: the second derivative has one sign on the whole domain -->
## Card calc1.4-7.method-concave.001
kind: method
skill: calc1.select.optimization-method
difficulty: 1
answer-type: choice

### Question
A food stand's daily revenue from selling a drink at a price of \(p\) dollars is \(R(p) = 160p - 8p^2\) dollars, where \(p \ge 0\) and there is no upper limit on the price. Which fact about \(R\), checked on the whole domain, shows that the critical number gives the greatest revenue?

### Choices
- [ ] Compare \(R\) at the two ends of the domain
- [x] \(R''(p)\) is negative for every \(p\), so the graph is concave down everywhere
- [ ] \(R''(p) = 0\) at the critical number
- [ ] \(R\) is continuous on the domain

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(p \ge 0\) has no right endpoint, so the closed-interval method does not apply. The derivative \(R'(p) = 160 - 16p\) is zero at \(p = 10\), and \(R''(p) = -16\) is negative for every \(p\). So the graph is concave down everywhere, and the critical number gives the absolute maximum, a revenue of $800.
   check: diff(160*p - 8*p^2, p) = 160 - 16*p
   check: solve(160 - 16*p, p) = {10}
   check: diff(160 - 16*p, p) = -16
   check: subs(160*p - 8*p^2, p, 10) = 800

<!-- tier 2, template: a half-open domain whose critical number is inside it -->
## Card calc1.4-7.method-halfopen.t01
kind: method
skill: calc1.select.optimization-method
difficulty: 2
answer-type: choice
vars: b = choice(2, 3); k = choice(10, 20, 30); L = choice(50, 60)

### Question
A ship's operating cost per kilometer, in dollars, at a speed of \(v\) km/h is \(C(v) = \dfrac{[[b*k^2]]}{v} + [[b]]v\), where \(0 < v \le [[L]]\) because [[L]] km/h is the ship's top speed. Which approach finds the speed with the least cost per kilometer and shows that it is the least?

### Choices
- [ ] Solve \(C'(v) = 0\) and report the solution, with no further check
- [x] Find the one critical number and show that \(C'\) is negative to its left and positive to its right on the domain
- [ ] Compare \(C\) at the two ends of the domain, \(v = 0\) and \(v = [[L]]\)
- [ ] Show that \(C''(v) = 0\) at the critical number

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(0 < v \le [[L]]\) does not include \(v = 0\), where \(C\) is not even defined, so the closed-interval method does not apply. The derivative \(C'(v) = [[b]] - \dfrac{[[b*k^2]]}{v^2}\) is zero only at \(v = [[k]]\), which lies in the domain because \([[k]] < [[L]]\). So use the sign of \(C'\) on each side of \([[k]]\): negative before it and positive after it, up to the top speed.
   check: solve(diff(b*k^2/v + b*v, v), v) = {-k, k}

<!-- tier 2: the only critical number is outside a closed interval -->
## Card calc1.4-7.method-outside.001
kind: method
skill: calc1.select.optimization-method
difficulty: 2
answer-type: choice

### Question
A ferry's operating cost per hour at a speed of \(v\) km/h is \(C(v) = 0.5v^2 - 30v + 600\) dollars. The ferry must run between \(40\) and \(80\) km/h, so \(40 \le v \le 80\). Solving \(C'(v) = 0\) gives \(v = 30\). Which approach finds the speed with the least cost per hour and shows that it is the least?

### Choices
- [x] Compare \(C\) at the two ends of the interval only, because the critical number is not in the domain
- [ ] Use \(v = 30\), because \(C''(v) = 1 > 0\) shows that it gives an absolute minimum
- [ ] Compare \(C(30)\), \(C(40)\) and \(C(80)\)
- [ ] Show that \(C'\) changes sign at \(v = 30\)

### Solution
0. [calc1.select.optimization-method] Set up: the domain \([40, 80]\) is closed and bounded and \(C\) is continuous on it, so use the closed-interval method. The only critical number, \(v = 30\), is outside the interval, so it is not a candidate, and only the two ends compete: \(C(40) = 200\) and \(C(80) = 1400\). The least cost is $200 per hour, at \(v = 40\).
   check: solve(diff(v^2/2 - 30*v + 600, v), v) = {30}
   check: subs(v^2/2 - 30*v + 600, v, 40) = 200
   check: subs(v^2/2 - 30*v + 600, v, 80) = 1400

<!-- tier 2: the second derivative test is inconclusive -->
## Card calc1.4-7.method-flat.001
kind: method
skill: calc1.select.optimization-method
difficulty: 2
answer-type: choice

### Question
The error in a sensor's reading, in units, at calibration setting \(x\) is \(E(x) = 0.1(x - 6)^4 + 2\), where \(x > 0\). The only critical number is \(x = 6\), and \(E''(6) = 0\). Which approach shows that \(x = 6\) gives the least error?

### Choices
- [ ] Apply the second derivative test at \(x = 6\) and read off the result
- [ ] Conclude that \(E\) has no minimum, because \(E''(6) = 0\)
- [ ] Compare \(E\) at the two ends of the domain
- [x] Show that \(E'\) is negative just to the left of \(6\) and positive just to the right, and use the fact that \(6\) is the only critical number

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(x > 0\) is open, so there are no endpoints to compare. The derivative \(E'(x) = \dfrac{2}{5}(x - 6)^3\) is zero only at \(x = 6\), and \(E''(x) = \dfrac{6}{5}(x - 6)^2\) is \(0\) there, so the second derivative test says nothing. Use the sign of \(E'\) instead: negative for \(x < 6\) and positive for \(x > 6\).
   check: diff((x - 6)^4/10 + 2, x) = 2*(x - 6)^3/5
   check: solve(2*(x - 6)^3/5, x) = {6}
   check: diff(2*(x - 6)^3/5, x) = 6*(x - 6)^2/5
   check: subs(6*(x - 6)^2/5, x, 6) = 0

<!-- tier 2, template: a downward parabola on a half line -->
## Card calc1.4-7.method-parabola.t01
kind: method
skill: calc1.select.optimization-method
difficulty: 2
answer-type: choice
vars: a = choice(2, 3, 5); h = choice(5, 10, 20); c = choice(10, 20)

### Question
A workshop's weekly profit from making \(x\) chairs is \(P(x) = -[[a]]x^2 + [[2*a*h]]x - [[c]]\) dollars, where \(x \ge 0\) and the workshop has no limit on how many chairs it can make. Which fact about \(P\), checked on the whole domain, shows that the critical number gives the greatest profit?

### Choices
- [x] \(P''(x) = -[[2*a]]\) is negative for every \(x\), so the graph is concave down everywhere
- [ ] \(P''(x) = 0\) at the critical number
- [ ] \(P\) is greater at the critical number than at \(x = 0\)
- [ ] Compare \(P\) at the two ends of the domain

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(x \ge 0\) has no right endpoint, so the closed-interval method does not apply. The derivative \(P'(x) = -[[2*a]]x + [[2*a*h]]\) is zero at \(x = [[h]]\), and \(P''(x) = -[[2*a]]\) is negative for every \(x\). So the graph is concave down everywhere, and the critical number gives the absolute maximum.
   check: solve(diff(-a*x^2 + 2*a*h*x - c, x), x) = {h}
   check: diff(diff(-a*x^2 + 2*a*h*x - c, x), x) = -2*a


<!-- tier 3, template: a cubic profit on a closed interval; the first derivative test finds only a local maximum -->
## Card calc1.4-7.method-cubic-cap.t01
kind: method
skill: calc1.select.optimization-method
difficulty: 3
answer-type: choice
vars: s = choice(1, 2, 3); L = choice(10, 11, 12, 13, 14, 15)

### Question
A company's profit from producing \(x\) thousand units is \(P(x) = [[s]](x^3 - 15x^2 + 63x)\) thousand dollars, where \(0 \le x \le [[L]]\) because the plant can make at most [[L]] thousand units. The derivative \(P'(x) = [[3*s]](x - 3)(x - 7)\) is zero at \(x = 3\) and at \(x = 7\). Which approach finds the production level with the greatest profit and shows that it is the greatest?

### Choices
- [ ] Use the first derivative test: \(P'\) changes from positive to negative at \(x = 3\), so \(x = 3\) gives the absolute maximum
- [ ] Use the second derivative test: \(P''(3) < 0\), so \(x = 3\) gives the absolute maximum
- [x] Compare \(P\) at \(x = 3\) and \(x = 7\) and at both ends, \(x = 0\) and \(x = [[L]]\)
- [ ] Show that \(P''(x)\) is negative on the whole domain

### Solution
0. [calc1.select.optimization-method] Set up: the domain \([0, [[L]]]\) is closed and bounded and \(P\) is continuous on it, so use the closed-interval method. The first and second derivative tests at \(x = 3\) show only a local maximum there, with \(P(3) = [[81*s]]\). The graph is not concave down on the whole domain, because \(P''(x) = [[6*s]](x - 5)\) changes sign at \(x = 5\). And the value at the right end, \(P([[L]]) = [[s*(L^3 - 15*L^2 + 63*L)]]\), is larger than \(P(3)\), so the greatest profit is at an end of the interval.
   check: solve(diff(s*(x^3 - 15*x^2 + 63*x), x), x) = {3, 7}
   check: diff(diff(s*(x^3 - 15*x^2 + 63*x), x), x) = 6*s*(x - 5)
   check: subs(s*(x^3 - 15*x^2 + 63*x), x, 3) = 81*s
   check: subs(s*(x^3 - 15*x^2 + 63*x), x, L) = s*(L^3 - 15*L^2 + 63*L)

<!-- tier 3: two critical numbers on an open domain; neither the one-critical-number argument nor concavity applies -->
## Card calc1.4-7.method-two-critical.001
kind: method
skill: calc1.select.optimization-method
difficulty: 3
answer-type: choice

### Question
A pump's energy use, in kilowatt-hours per day, at flow setting \(x\) is \(E(x) = \dfrac{x^3}{3} - 5x^2 + 16x + 40\), where \(x > 0\) and there is no upper limit on the setting. The derivative \(E'(x) = (x - 2)(x - 8)\) has two zeros. Which approach finds the setting with the least energy use and shows that it is the least?

### Choices
- [ ] Find the one critical number and show that \(E'\) changes sign there, so it gives the absolute minimum
- [ ] Show that \(E''(x) > 0\) for every \(x\), so the graph is concave up everywhere
- [ ] Compare \(E\) at the two ends of the domain and report the smaller value
- [x] Make a sign chart for \(E'\), classify both critical numbers, and compare the local minimum with the values of \(E\) near \(x = 0\) and for large \(x\)

### Solution
0. [calc1.select.optimization-method] Set up: the domain is open, so the closed-interval method does not apply. There are two critical numbers, so the one-critical-number argument is not available, and \(E''(x) = 2x - 10\) changes sign at \(x = 5\), so the graph is not concave up everywhere. Make a sign chart of \(E'\): positive on \((0, 2)\), negative on \((2, 8)\) and positive on \((8, \infty)\). So \(x = 8\) is a local minimum with \(E(8) = \dfrac{56}{3} \approx 18.7\). This is smaller than the value that \(E\) approaches as \(x \to 0^+\), which is \(40\), and \(E\) grows without bound for large \(x\), so the local minimum is the absolute minimum.
   check: solve(diff(x^3/3 - 5*x^2 + 16*x + 40, x), x) = {2, 8}
   check: diff(diff(x^3/3 - 5*x^2 + 16*x + 40, x), x) = 2*x - 10
   check: subs(x^3/3 - 5*x^2 + 16*x + 40, x, 8) = 56/3
   check: subs(x^3/3 - 5*x^2 + 16*x + 40, x, 0) = 40

<!-- tier 3, template: a speed limit below the critical number; the derivative has one sign on the whole domain -->
## Card calc1.4-7.method-cap.t01
kind: method
skill: calc1.select.optimization-method
difficulty: 3
answer-type: choice
vars: b = choice(2, 3); k = choice(30, 40, 50); L = choice(15, 20, 25)

### Question
A river barge's operating cost per kilometer, in dollars, at a speed of \(v\) km/h is \(C(v) = \dfrac{[[b*k^2]]}{v} + [[b]]v\), where \(0 < v \le [[L]]\) because of a speed limit on the canal. Solving \(C'(v) = 0\) gives \(v = [[k]]\). Which approach finds the speed with the least cost per kilometer and shows that it is the least?

### Choices
- [ ] Use \(v = [[k]]\), because \(C'\) changes sign there from negative to positive
- [ ] Compare \(C\) at both ends of the domain, \(v = 0\) and \(v = [[L]]\)
- [ ] Use the second derivative test: \(C''([[k]]) > 0\), so \(v = [[k]]\) gives the absolute minimum
- [x] Show that \(C'(v) < 0\) on the whole domain, so the least cost is at the right end, \(v = [[L]]\)

### Solution
0. [calc1.select.optimization-method] Set up: the domain \(0 < v \le [[L]]\) has no left endpoint, so the closed-interval method does not apply. The critical number \(v = [[k]]\) is larger than \([[L]]\), so it is outside the domain and cannot be used. On the domain \(v^2 \le [[L^2]] < [[k^2]]\), so \(\dfrac{[[b*k^2]]}{v^2} > [[b]]\) and \(C'(v) = [[b]] - \dfrac{[[b*k^2]]}{v^2} < 0\). So \(C\) is decreasing on the whole domain, and the least cost is at \(v = [[L]]\).
   check: solve(diff(b*k^2/v + b*v, v), v) = {-k, k}
   check: subs(b - b*k^2/v^2, v, L) = b*(L^2 - k^2)/L^2

<!-- tier 4: a sum of two terms that are each concave up, so the concavity of the whole function is clear before the critical number is known -->
## Card calc1.4-7.method-pump.001
kind: method
skill: calc1.select.optimization-method
difficulty: 4
answer-type: choice

### Question
Two farms lie \(3\) km and \(4\) km from a long straight canal, on the same side of it, and the points of the canal nearest to them are \(24\) km apart. A pumping station is placed on the canal at a point \(x\) km from the point nearest the first farm, where \(x\) can be any real number, and each farm is joined to it by a straight pipe. The total length of pipe is \(L(x) = \sqrt{x^2 + 9} + \sqrt{(24 - x)^2 + 16}\) kilometers. Which approach shows that a critical number of \(L\) gives the absolute minimum, without first solving the messy equation \(L'(x) = 0\)?

### Choices
- [ ] Compare \(L\) at the two ends of the domain
- [ ] Show that \(L'(x)\) changes sign at the critical number
- [x] Show that \(L''(x) > 0\) for every \(x\), because each square-root term is concave up everywhere
- [ ] Show that \(L''(x) = 0\) at the critical number

### Solution
0. [calc1.select.optimization-method] Set up: the domain is the whole real line, so there are no endpoints to compare. The sign of \(L'\) would need the critical number first, and \(L'(x)\) is a difference of square-root quotients. But each term is concave up everywhere: \(\dfrac{d^2}{dx^2}\sqrt{x^2 + 9} = \dfrac{9}{(x^2 + 9)^{3/2}} > 0\) and \(\dfrac{d^2}{dx^2}\sqrt{(24 - x)^2 + 16} = \dfrac{16}{((24 - x)^2 + 16)^{3/2}} > 0\). So \(L'' > 0\) everywhere, and any critical number gives the absolute minimum. Solving afterwards gives \(x = \dfrac{72}{7}\), with \(L\left(\dfrac{72}{7}\right) = 25\) km.
   check: diff(diff(sqrt(x^2 + 9), x), x) = 9/(x^2 + 9)^(3/2)
   check: diff(diff(sqrt((24 - x)^2 + 16), x), x) = 16/((24 - x)^2 + 16)^(3/2)
   check: subs(diff(sqrt(x^2 + 9) + sqrt((24 - x)^2 + 16), x), x, 72/7) = 0
   check: subs(sqrt(x^2 + 9) + sqrt((24 - x)^2 + 16), x, 72/7) = 25

<!-- tier 4: the question asks for the largest and the smallest value, so concavity alone is not enough -->
## Card calc1.4-7.method-two-squares.001
kind: method
skill: calc1.select.optimization-method
difficulty: 4
answer-type: choice

### Question
A \(24\) m length of edging is cut into two pieces, and each piece is bent into a square to border a vegetable bed. If the first piece has length \(x\) meters, where \(0 \le x \le 24\), the total area enclosed is \(A(x) = \dfrac{x^2}{16} + \dfrac{(24 - x)^2}{16}\) square meters. Which approach finds both the smallest and the largest total area, and shows that they are the smallest and the largest?

### Choices
- [ ] Show that \(A''(x) > 0\) everywhere, so the critical number gives both the smallest and the largest area
- [ ] Show that \(A'\) changes sign at the critical number, so it gives both the smallest and the largest area
- [x] Compare \(A\) at the critical number and at both ends of the interval
- [ ] Evaluate \(A\) at the critical number only, because a critical number is always an extreme value

### Solution
0. [calc1.select.optimization-method] Set up: the domain \([0, 24]\) is closed and bounded and \(A\) is continuous on it, so use the closed-interval method. The critical number is \(x = 12\), and \(A''(x) = \dfrac{1}{4} > 0\) shows only that the graph is concave up, which gives the smallest area but never a largest area inside the interval. The largest area is at an end of the interval: \(A(12) = 18\), the smallest, and \(A(0) = A(24) = 36\), the largest.
   check: solve(diff(x^2/16 + (24 - x)^2/16, x), x) = {12}
   check: diff(diff(x^2/16 + (24 - x)^2/16, x), x) = 1/4
   check: subs(x^2/16 + (24 - x)^2/16, x, 12) = 18
   check: subs(x^2/16 + (24 - x)^2/16, x, 0) = 36
   check: subs(x^2/16 + (24 - x)^2/16, x, 24) = 36

