---
format: mastery-cards 1
deck: Calculus I::0 Precalculus Skills::0.6 Geometry
source: original
license: CC BY-NC-SA 4.0
---

<!-- Section 0.6 Geometry: twelve skills, one worked example each, eight or nine problems each
     (tiers 1 to 3), and flashcards for the definitions and formulas that related rates and
     optimization use. Lengths are in the units named in each question, and angles are in
     degrees only where a question writes the degree sign.
     Provenance: every card is original.
     pre.geometry.area-volume-formulas (the original umbrella skill) has no cards here: the
     area, volume and surface-area steps are tagged with the specific components instead. -->


<!-- ===================================================================== -->
<!-- pre.geometry.area-plane-figures                                       -->
<!-- ===================================================================== -->

<!-- worked example: choose the right lengths for a trapezoid -->
## Card calc1.0-6.area-example.001
kind: example
skill: pre.geometry.area-plane-figures

### Question
A flower bed is a trapezoid. Its two parallel sides are 6 m and 10 m long, the side perpendicular to them is 3 m long, and the slanted side is 5 m long. Find the area of the bed.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of a trapezoid is half the sum of its two parallel sides times its height. The height is the distance between the parallel sides measured at right angles, so a slanted side is not the height.
1. [pre.geometry.area-plane-figures] Choose the lengths: the parallel sides are 6 m and 10 m, and the height is the perpendicular side, 3 m. The slanted side of 5 m is not needed.
2. [pre.geometry.area-plane-figures] Area: \(A = \frac{1}{2}(a + b)h = \frac{1}{2}(6 + 10)(3) = 24\) square meters.
   check: 1/2*(6 + 10)*3 = 24

<!-- tier 1, template: triangle from base and height -->
## Card calc1.0-6.area.t01
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: number
vars: b = int(5, 24); h = int(3, 16)
answer: b*h/2
wrong: b*h => A triangle is half of the rectangle with the same base and height, so its area has a factor of 1/2. @1

### Question
A triangular sail has a base of [[b]] ft and a height of [[h]] ft. Find its area in square feet.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of a triangle is one half of its base times its height.
1. [pre.geometry.area-plane-figures] Area: \(A = \frac{1}{2}bh = \frac{1}{2}([[b]])([[h]]) = [[tex(b*h/2)]]\) square feet.
   check: (b*h)/2 = b*h/2

<!-- tier 1: the height of a trapezoid is not a slanted side -->
## Card calc1.0-6.area.001
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: number
answer: 48
wrong: 60 => The height is the distance between the parallel sides, measured at right angles, which is 4 ft. It is not the length of a slanted side. @1; 96 => The area of a trapezoid is half of (a + b) times h, so the product needs a factor of 1/2. @1

### Question
A plot of land is a trapezoid. Its parallel sides are 9 ft and 15 ft long, the distance between them is 4 ft, and each slanted side is 5 ft long. Find the area of the plot in square feet.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of a trapezoid is half the sum of the parallel sides times the height, and the height is measured at right angles to the parallel sides.
1. [pre.geometry.area-plane-figures] Area: with parallel sides 9 and 15 and height 4, \(A = \frac{1}{2}(9 + 15)(4) = 48\) square feet. The slanted sides are not used.
   check: 1/2*(9 + 15)*4 = 48

<!-- tier 1: area of a circle from its diameter -->
## Card calc1.0-6.area.002
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: number
answer: 49*pi
wrong: 196*pi => The area formula uses the radius, which is half of the diameter. @1; 14*pi => That is the circumference of the pond, not its area. @1

### Question
A circular pond has a diameter of 14 m. Find its area in square meters. Give an exact answer.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of a circle is pi times the square of the radius, and the radius is half of the diameter.
1. [pre.geometry.area-plane-figures] Area: the radius is \(r = \frac{14}{2} = 7\), so \(A = \pi r^2 = \pi(7)^2 = 49\pi\) square meters.
   check: pi*(14/2)^2 = 49*pi

<!-- tier 2, template: solve the triangle area formula for the height -->
## Card calc1.0-6.area.t02
skill: pre.geometry.area-plane-figures
uses: alg.solve.linear
difficulty: 2
answer-type: number
vars: k = int(2, 12); h = int(3, 14)
let: a = k*h; b = 2*k
answer: h
wrong: a/b => The area of a triangle is half the base times the height, so the height is 2A divided by the base. The factor 1/2 was left out. @1; 2*a*b => To isolate the height, divide by the base. Do not multiply. @2

### Question
A triangular piece of sheet metal has an area of [[a]] square inches and a base of [[b]] inches. Find its height in inches.

### Solution
0. [pre.geometry.area-plane-figures] Set up: write the triangle area formula with the area and the base that are given, then solve it for the height.
1. [pre.geometry.area-plane-figures] Formula: \(A = \frac{1}{2}bh\), so \([[a]] = \frac{1}{2}([[b]])h\).
   check: a = 1/2*b*h
2. [alg.solve.linear] Solve for \(h\): \(h = \frac{2([[a]])}{[[b]]} = [[h]]\) inches.
   check: 2*a/b = h

<!-- tier 2: a parallelogram's height is not its slanted side -->
## Card calc1.0-6.area.003
skill: pre.geometry.area-plane-figures
difficulty: 2
answer-type: number
answer: 60
wrong: 84 => The height is the distance between the two long sides, 5 cm. The slanted side of 7 cm is not the height. @1; 30 => A parallelogram is not half of a rectangle. Its area is base times height with no factor of 1/2. @1

### Question
A parallelogram has two sides of length 12 cm and two sides of length 7 cm. The distance between the two longer sides is 5 cm. Find the area of the parallelogram in square centimeters.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of a parallelogram is a base times the height measured at right angles to that base.
1. [pre.geometry.area-plane-figures] Area: the base is the long side, 12 cm, and the height is the distance 5 cm between the long sides, so \(A = bh = (12)(5) = 60\) square centimeters. The 7 cm sides are slanted and are not the height.
   check: 12*5 = 60

<!-- tier 2: the ellipse formula uses the semi-axes -->
## Card calc1.0-6.area.004
skill: pre.geometry.area-plane-figures
difficulty: 2
answer-type: number
answer: 60*pi
wrong: 240*pi => The formula uses the semi-axes, which are half the length and half the width. @1; 120*pi => Both the length and the width must be halved before multiplying. @1

### Question
An elliptical flower bed is 20 m long and 12 m wide. Find its area in square meters. Give an exact answer.

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area of an ellipse is pi times its two semi-axes, which are half the length and half the width.
1. [pre.geometry.area-plane-figures] Area: the semi-axes are 10 and 6, so \(A = \pi ab = \pi(10)(6) = 60\pi\) square meters.
   check: pi*10*6 = 60*pi

<!-- tier 3, template: the height of an isosceles triangle, in one variable -->
## Card calc1.0-6.area.t03
skill: pre.geometry.area-plane-figures
uses: pre.geometry.pythagorean
difficulty: 3
answer-type: expression
vars: L = int(5, 16); x
domain: 0 < x < [[L]]
answer: x*sqrt(L^2 - x^2)
wrong: 2*x*sqrt(L^2 - x^2) => The area of a triangle is half of the base times the height. Here the 1/2 and the 2 in the base 2x cancel, leaving x. @2; x*sqrt(L^2 - 4*x^2) => The altitude splits the base of length 2x into two pieces of length x, so use x as the leg in the Pythagorean theorem, not 2x. @1

### Question
An isosceles triangle has two equal sides of length [[L]] cm. Its base has length \(2x\) cm, where \(0 < x < [[L]]\). Write the area \(A\) of the triangle, in square centimeters, as a function of \(x\).

### Solution
0. [pre.geometry.area-plane-figures] Set up: the area is half the base times the height, so first write the height in terms of x.
1. [pre.geometry.pythagorean] Height: the altitude to the base splits the triangle into two right triangles, each with hypotenuse [[L]] and a leg \(x\), so \(h = \sqrt{[[L^2]] - x^2}\).
   check: sqrt(L^2 - x^2)^2 + x^2 = L^2
2. [pre.geometry.area-plane-figures] Area: \(A = \frac{1}{2}(2x)h = x\sqrt{[[L^2]] - x^2}\).
   check: 1/2*(2*x)*sqrt(L^2 - x^2) = x*sqrt(L^2 - x^2)

<!-- tier 3: area of a triangle from two sides and the angle between them -->
## Card calc1.0-6.area.005
skill: pre.geometry.area-plane-figures
uses: trig.values.exact
difficulty: 3
answer-type: number
answer: 24
wrong: 48 => The triangle's area is half of ab sin C, so the product (8)(12) sin 150 degrees needs a factor of 1/2. @1; 24*sqrt(3) => The sine of 150 degrees is 1/2, not the square root of 3 over 2. Use the reference angle of 30 degrees. @2

### Question
Two sides of a triangular lot are 8 ft and 12 ft long, and the angle between them is \(150^\circ\). Find the area of the lot in square feet.

### Solution
0. [pre.geometry.area-plane-figures] Set up: when two sides and the angle between them are known, the area is one half of the product of the two sides times the sine of that angle.
1. [pre.geometry.area-plane-figures] Formula: \(A = \frac{1}{2}ab\sin C = \frac{1}{2}(8)(12)\sin 150^\circ\).
   check: 1/2*8*12*sin(5*pi/6) = 24
2. [trig.values.exact] Exact value: \(\sin 150^\circ = \sin 30^\circ = \frac{1}{2}\).
   check: sin(5*pi/6) = 1/2
3. [pre.geometry.area-plane-figures] Area: \(A = 48 \cdot \frac{1}{2} = 24\) square feet.
   check: 48*(1/2) = 24

<!-- ===================================================================== -->
<!-- pre.geometry.perimeter-circumference                                  -->
<!-- ===================================================================== -->

<!-- worked example: a fixed perimeter gives one side in terms of the other -->
## Card calc1.0-6.perim-example.001
kind: example
skill: pre.geometry.perimeter-circumference
uses: alg.solve.linear

### Question
A rectangle is \(x\) meters wide and has a perimeter of 40 m. Write its length \(y\), in meters, in terms of \(x\).

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the perimeter is the distance around the outside, so for a rectangle it is two widths plus two lengths.
1. [pre.geometry.perimeter-circumference] Perimeter: \(2x + 2y = 40\).
   check: 2*x + 2*(20 - x) = 40
2. [alg.solve.linear] Solve for \(y\): \(2y = 40 - 2x\), so \(y = 20 - x\).
   check: solve(2*x + 2*y - 40, y) = {20 - x}

<!-- tier 1, template: perimeter of a rectangle -->
## Card calc1.0-6.perim.t01
skill: pre.geometry.perimeter-circumference
difficulty: 1
answer-type: number
vars: l = int(6, 40); w = int(3, 25)
require: l > w; l*w != 2*l + 2*w
answer: 2*l + 2*w
wrong: l*w => That is the area of the garden. The fencing goes around the outside, so it is the perimeter. @1; l + w => The distance around a rectangle includes two lengths and two widths. @1

### Question
A rectangular garden is [[l]] m long and [[w]] m wide. How many meters of fencing are needed to go all the way around it?

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the fence goes around the outside of the garden, so its length is the perimeter: two lengths plus two widths.
1. [pre.geometry.perimeter-circumference] Perimeter: \(P = 2l + 2w = 2([[l]]) + 2([[w]]) = [[2*l + 2*w]]\) meters.
   check: 2*(l + w) = 2*l + 2*w

<!-- tier 1: circumference from the diameter -->
## Card calc1.0-6.perim.001
skill: pre.geometry.perimeter-circumference
difficulty: 1
answer-type: number
answer: 10*pi
wrong: 25*pi => That is the area of the fountain. The distance around its edge is the circumference. @1; 5*pi => The circumference is pi times the diameter, or two pi times the radius. @1

### Question
A circular fountain has a diameter of 10 ft. Find the distance around its edge, in feet. Give an exact answer.

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the distance around a circle is its circumference, which is pi times the diameter (or 2 pi times the radius).
1. [pre.geometry.perimeter-circumference] Circumference: \(C = \pi d = \pi(10) = 10\pi\) feet.
   check: pi*10 = 10*pi

<!-- tier 1: radius from the circumference -->
## Card calc1.0-6.perim.002
skill: pre.geometry.perimeter-circumference
difficulty: 1
answer-type: number
answer: 9
wrong: 18 => Dividing the circumference 18pi by pi gives the diameter. The radius is half of the diameter. @1; 9*pi => Divide by 2pi, not by 2, so that the pi cancels. @1

### Question
A circle has a circumference of \(18\pi\) cm. Find its radius in centimeters.

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the circumference of a circle is 2 pi times the radius, so the radius is the circumference divided by 2 pi.
1. [pre.geometry.perimeter-circumference] Radius: \(r = \frac{C}{2\pi} = \frac{18\pi}{2\pi} = 9\) centimeters.
   check: 18*pi/(2*pi) = 9

<!-- tier 2, template: the outer edge of a circular walkway -->
## Card calc1.0-6.perim.t02
skill: pre.geometry.perimeter-circumference
difficulty: 2
answer-type: number
vars: r = int(3, 15); w = int(1, 4)
answer: 2*pi*(r + w)
wrong: 2*pi*r => That is the inner edge, the edge of the flower bed itself. The outer edge is a larger circle. @1; 2*pi*r + w => The outer edge is a circle of radius r + w, so add the width to the radius before using the circumference formula. @1; pi*(r + w)^2 => That is the area inside the outer edge. The length of the edge is the circumference. @2

### Question
A circular flower bed has a radius of [[r]] m. A walkway [[w]] m wide goes all the way around the bed. Find the length of the outer edge of the walkway in meters. Give an exact answer.

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the outer edge of the walkway is a circle, so its length is a circumference. Find its radius first.
1. [pre.geometry.perimeter-circumference] Outer radius: the walkway adds its width to the radius of the bed, so the outer circle has radius [[r + w]] m.
2. [pre.geometry.perimeter-circumference] Circumference: \(C = 2\pi R = 2\pi([[r + w]]) = [[tex(2*pi*(r + w))]]\) meters.
   check: 2*pi*(r + w) = 2*pi*r + 2*pi*w

<!-- tier 2: the area gives the missing side, then the perimeter -->
## Card calc1.0-6.perim.003
skill: pre.geometry.perimeter-circumference
uses: pre.geometry.area-plane-figures, alg.solve.linear
difficulty: 2
answer-type: number
answer: 110
wrong: 55 => The perimeter includes two lengths and two widths, so double the sum 40 + 15. @3; 15 => That is the width of the field. The fence goes around all four sides. @3

### Question
A rectangular field has an area of 600 square meters and is 40 m long. How many meters of fencing are needed to enclose it?

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the fence goes around the field, so its length is the perimeter. The width is not given, so find it from the area first.
1. [pre.geometry.area-plane-figures] Area: the area of a rectangle is length times width, so \(600 = 40w\).
   check: 600 = 40*15
2. [alg.solve.linear] Solve for \(w\): \(w = \frac{600}{40} = 15\) meters.
   check: 600/40 = 15
3. [pre.geometry.perimeter-circumference] Perimeter: \(P = 2l + 2w = 2(40) + 2(15) = 110\) meters.
   check: 2*40 + 2*15 = 110

<!-- tier 2: one side of a rectangle with a fixed perimeter -->
## Card calc1.0-6.perim.004
skill: pre.geometry.perimeter-circumference
uses: alg.solve.linear
difficulty: 2
answer-type: expression
vars: x
answer: 18 - x
wrong: 36 - x => After subtracting 2x from both sides of 2x + 2y = 36, divide by 2 to get y. @2; 36 - 2*x => Divide both sides of 2y = 36 - 2x by 2. @2

### Question
A rectangle has a perimeter of 36 ft. One of its sides has length \(x\) ft. Write the length \(y\), in feet, of an adjacent side in terms of \(x\).

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the perimeter of a rectangle is two of each of its two side lengths.
1. [pre.geometry.perimeter-circumference] Perimeter: \(2x + 2y = 36\).
   check: 2*x + 2*(18 - x) = 36
2. [alg.solve.linear] Solve for \(y\): \(2y = 36 - 2x\), so \(y = 18 - x\).
   check: solve(2*x + 2*y - 36, y) = {18 - x}

<!-- tier 3, template: the area of a rectangle with a fixed perimeter, in one variable -->
## Card calc1.0-6.perim.t03
skill: pre.geometry.perimeter-circumference
uses: alg.solve.linear, pre.geometry.area-plane-figures
difficulty: 3
answer-type: expression
vars: p = int(8, 40); x
answer: x*(p - x)
wrong: x*(2*p - x) => The fencing is the perimeter, 2x + 2y = 2p, so y = p - x. The length is not 2p - x. @2; x*(2*p - 2*x) => Dividing 2y = 2p - 2x by 2 gives y = p - x. @2

### Question
A farmer has [[2*p]] ft of fencing and uses all of it to enclose a rectangular pen. Let \(x\) be the width of the pen in feet. Write the area \(A\) of the pen, in square feet, as a function of \(x\).

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the fencing goes all the way around the pen, so its length is the perimeter. Use it to write the length in terms of the width, then find the area.
1. [pre.geometry.perimeter-circumference] Perimeter: with width \(x\) and length \(y\), \(2x + 2y = [[2*p]]\).
   check: 2*x + 2*(p - x) = 2*p
2. [alg.solve.linear] Solve for \(y\): \(y = [[p]] - x\).
   check: (2*p - 2*x)/2 = p - x
3. [pre.geometry.area-plane-figures] Area: \(A = xy = x([[p]] - x)\).
   check: x*(p - x) = x*(p - x)

<!-- tier 3: a piece of wire shared between a circle and a square -->
## Card calc1.0-6.perim.005
skill: pre.geometry.perimeter-circumference
uses: alg.solve.linear
difficulty: 3
answer-type: expression
vars: r
answer: 25 - pi*r/2
wrong: (100 - pi*r)/4 => The circumference of a circle is 2 pi r, so the circle uses 2 pi r cm of wire, not pi r. @1; 100 - 2*pi*r => That is the wire left for the square. The square has four equal sides, so each side is one fourth of it. @2; (100 - 2*pi*r)/2 => The perimeter of a square is 4s, not 2s. @1

### Question
A piece of wire 100 cm long is cut into two pieces. One piece is bent into a circle of radius \(r\) cm and the other into a square with sides of length \(s\) cm, and all of the wire is used. Write \(s\) in terms of \(r\).

### Solution
0. [pre.geometry.perimeter-circumference] Set up: the circle and the square together use all 100 cm of wire, so the circumference of the circle plus the perimeter of the square is 100.
1. [pre.geometry.perimeter-circumference] Lengths: the circumference of the circle is \(2\pi r\) and the perimeter of the square is \(4s\), so \(2\pi r + 4s = 100\).
   check: 2*pi*r + 4*(25 - pi*r/2) = 100
2. [alg.solve.linear] Solve for \(s\): \(4s = 100 - 2\pi r\), so \(s = 25 - \frac{\pi r}{2}\).
   check: solve(2*pi*r + 4*s - 100, s) = {25 - pi*r/2}

<!-- ===================================================================== -->
<!-- pre.geometry.volume-solids                                            -->
<!-- ===================================================================== -->

<!-- worked example: the volume of a cone -->
## Card calc1.0-6.vol-example.001
kind: example
skill: pre.geometry.volume-solids

### Question
A conical tank (point down) has a top radius of 4 ft and a height of 9 ft. How many cubic feet of water does it hold when it is full? Give an exact answer.

### Solution
0. [pre.geometry.volume-solids] Set up: a cone holds one third of the cylinder with the same base and the same height, and the height is measured straight up from the base to the point.
1. [pre.geometry.volume-solids] Volume: \(V = \frac{1}{3}\pi r^2 h = \frac{1}{3}\pi(4)^2(9) = 48\pi\) cubic feet.
   check: 1/3*pi*4^2*9 = 48*pi

<!-- tier 1, template: volume of a cone -->
## Card calc1.0-6.vol.t01
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: number
vars: r = int(2, 6); h = int(5, 14)
answer: 1/3*pi*r^2*h
wrong: pi*r^2*h => A cone holds one third of the cylinder with the same base and height, so the volume has a factor of 1/3. @1; 1/3*pi*r*h => The radius is squared, because the base is a circle of area pi r squared. @1

### Question
A cone-shaped paper cup has a rim radius of [[r]] cm and a height of [[h]] cm. Find the volume of the cup in cubic centimeters. Give an exact answer.

### Solution
0. [pre.geometry.volume-solids] Set up: a cone holds one third of the cylinder with the same base and height.
1. [pre.geometry.volume-solids] Volume: \(V = \frac{1}{3}\pi r^2 h = \frac{1}{3}\pi([[r]])^2([[h]]) = [[tex(1/3*pi*r^2*h)]]\) cubic centimeters.
   check: 1/3*pi*r^2*h = pi*r^2*h/3

<!-- tier 1: volume of a sphere from its diameter -->
## Card calc1.0-6.vol.001
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: number
answer: 288*pi
wrong: 2304*pi => The volume formula uses the radius, which is half of the diameter. @1; 144*pi => That is the surface area, 4 pi r squared. The volume is (4/3) pi r cubed. @1

### Question
A spherical balloon has a diameter of 12 cm. Find its volume in cubic centimeters. Give an exact answer.

### Solution
0. [pre.geometry.volume-solids] Set up: the volume of a sphere is four thirds of pi times the cube of the radius, and the radius is half of the diameter.
1. [pre.geometry.volume-solids] Volume: with \(r = 6\), \(V = \frac{4}{3}\pi r^3 = \frac{4}{3}\pi(6)^3 = 288\pi\) cubic centimeters.
   check: 4/3*pi*6^3 = 288*pi

<!-- tier 1: volume of a pyramid -->
## Card calc1.0-6.vol.002
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: number
answer: 120
wrong: 360 => A pyramid holds one third of the prism with the same base and height, so the volume has a factor of 1/3. @1; 180 => The factor in the volume of a pyramid is 1/3, not 1/2. @1

### Question
A pyramid has a square base that is 6 m on each side and a height of 10 m. Find its volume in cubic meters.

### Solution
0. [pre.geometry.volume-solids] Set up: a pyramid holds one third of the prism with the same base and height, so its volume is one third of the base area times the height.
1. [pre.geometry.volume-solids] Volume: the base area is \(6^2 = 36\), so \(V = \frac{1}{3}(36)(10) = 120\) cubic meters.
   check: 1/3*6^2*10 = 120

<!-- tier 2, template: volume of a cylinder from its diameter -->
## Card calc1.0-6.vol.t02
skill: pre.geometry.volume-solids
difficulty: 2
answer-type: number
vars: r = int(3, 9); h = int(3, 12)
answer: pi*r^2*h
wrong: pi*(2*r)^2*h => The volume formula uses the radius, which is half of the diameter. @1; 2*pi*r*h => That is the area of the curved side. The volume is the area of the base times the height. @1

### Question
A cylindrical water tank has a diameter of [[2*r]] m and a height of [[h]] m. Find the volume of the tank in cubic meters. Give an exact answer.

### Solution
0. [pre.geometry.volume-solids] Set up: the volume of a cylinder is the area of its base times its height, and the radius is half of the diameter.
1. [pre.geometry.volume-solids] Radius: the diameter is [[2*r]] m, so the radius is [[r]] m.
2. [pre.geometry.volume-solids] Volume: \(V = \pi r^2 h = \pi([[r]])^2([[h]]) = [[tex(pi*r^2*h)]]\) cubic meters.
   check: pi*r^2*h = pi*(2*r/2)^2*h

<!-- tier 2: the radius from the volume of a cylinder -->
## Card calc1.0-6.vol.003
skill: pre.geometry.volume-solids
uses: alg.solve.polynomial
difficulty: 2
answer-type: number
answer: 4
wrong: 16 => The equation gives r squared equal to 16, so take the square root. @2; 8 => To undo r squared, take a square root. Dividing by 2 does not undo a square. @2

### Question
A cylindrical can is 5 cm tall and holds \(80\pi\) cubic centimeters. Find the radius of its base in centimeters.

### Solution
0. [pre.geometry.volume-solids] Set up: write the cylinder volume formula with the volume and the height that are given, then solve it for the radius.
1. [pre.geometry.volume-solids] Equation: \(V = \pi r^2 h\), so \(80\pi = \pi r^2(5)\), which gives \(r^2 = 16\).
   check: 80*pi = pi*4^2*5
2. [alg.solve.polynomial] Solve: \(r^2 - 16 = (r - 4)(r + 4) = 0\), and a radius is positive, so \(r = 4\) centimeters.
   check: solve(r^2 - 16, r) = {-4, 4}
   check: sqrt(16) = 4

<!-- tier 2: the height of a box with a square base and a fixed volume -->
## Card calc1.0-6.vol.004
skill: pre.geometry.volume-solids
uses: alg.solve.linear
difficulty: 2
answer-type: expression
vars: x
domain: x > 0
answer: 32/x^2
wrong: 32/x => The base is a square with side x, so its area is x squared and the height is 32 divided by x squared. @1; 32 - x^2 => To isolate h in x^2 h = 32, divide by x^2. Do not subtract. @2

### Question
A box with a square base has a volume of 32 cubic feet. The sides of its base are \(x\) ft long and its height is \(h\) ft. Write \(h\) in terms of \(x\).

### Solution
0. [pre.geometry.volume-solids] Set up: the volume of a box is the area of its base times its height.
1. [pre.geometry.volume-solids] Volume: the base is a square with side \(x\), so \(V = x^2 h = 32\).
   check: x^2*(32/x^2) = 32
2. [alg.solve.linear] Solve for \(h\): \(h = \frac{32}{x^2}\).
   check: 32/x^2 = 32*x^(-2)

<!-- tier 3, template: a cylinder inscribed in a sphere, in one variable -->
## Card calc1.0-6.vol.t03
skill: pre.geometry.volume-solids
uses: pre.geometry.pythagorean
difficulty: 3
answer-type: expression
vars: R = int(3, 15); x
domain: 0 < x < [[R]]
answer: 2*pi*x^2*sqrt(R^2 - x^2)
wrong: pi*x^2*sqrt(R^2 - x^2) => The height of the cylinder is twice the distance from the center of the sphere to the top face, so the height is 2 times the square root. @1; 2*pi*x*sqrt(R^2 - x^2) => The area of the base is pi x squared, not pi x. @2

### Question
A right circular cylinder is inscribed in a sphere of radius [[R]] cm, so that the rim of each end of the cylinder lies on the sphere. Let \(x\) be the radius of the cylinder, where \(0 < x < [[R]]\). Write the volume \(V\) of the cylinder, in cubic centimeters, as a function of \(x\).

### Solution
0. [pre.geometry.volume-solids] Set up: the volume of a cylinder is the area of its base times its height, so first write the height in terms of x.
1. [pre.geometry.pythagorean] Height: the axis of the cylinder passes through the center of the sphere, and a point on the rim of the top face is [[R]] cm from the center. So half the height, b, satisfies \(x^2 + b^2 = [[R^2]]\), and the full height is \(h = 2b = 2\sqrt{[[R^2]] - x^2}\).
   check: x^2 + sqrt(R^2 - x^2)^2 = R^2
2. [pre.geometry.volume-solids] Volume: \(V = \pi x^2 h = 2\pi x^2\sqrt{[[R^2]] - x^2}\).
   check: pi*x^2*(2*sqrt(R^2 - x^2)) = 2*pi*x^2*sqrt(R^2 - x^2)

<!-- tier 3: a conical pile whose height is twice its radius -->
## Card calc1.0-6.vol.005
skill: pre.geometry.volume-solids
uses: alg.solve.linear
difficulty: 3
answer-type: expression
vars: h
domain: h > 0
answer: pi*h^3/12
wrong: 4*pi*h^3/3 => The height is twice the radius, so the radius is h/2, not 2h. @1; pi*h^2/6 => The radius is squared in the volume formula, and (h/2) squared is h squared over 4. @2

### Question
Sand falls from a conveyor belt and forms a pile in the shape of a cone whose height is always twice its radius. Let \(h\) be the height of the pile in meters. Write the volume \(V\) of the pile, in cubic meters, as a function of \(h\).

### Solution
0. [pre.geometry.volume-solids] Set up: use the volume formula for a cone, and replace the radius by an expression in h.
1. [alg.solve.linear] Radius: the height is twice the radius, \(h = 2r\), so \(r = \frac{h}{2}\).
   check: 2*(h/2) = h
2. [pre.geometry.volume-solids] Volume: \(V = \frac{1}{3}\pi r^2 h = \frac{1}{3}\pi\left(\frac{h}{2}\right)^2 h = \frac{\pi h^3}{12}\).
   check: 1/3*pi*(h/2)^2*h = pi*h^3/12

<!-- ===================================================================== -->
<!-- pre.geometry.surface-area-solids                                      -->
<!-- ===================================================================== -->

<!-- worked example: the total surface area of a closed can -->
## Card calc1.0-6.surf-example.001
kind: example
skill: pre.geometry.surface-area-solids

### Question
A closed cylindrical can has a radius of 3 cm and a height of 10 cm. Find the total area of its surface. Give an exact answer.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the surface of a closed can is two circular ends and a curved side. The curved side unrolls into a rectangle as wide as the circumference of an end, so its area is the circumference times the height.
1. [pre.geometry.surface-area-solids] Ends: the two circles have area \(2\pi r^2 = 2\pi(3)^2 = 18\pi\).
   check: 2*pi*3^2 = 18*pi
2. [pre.geometry.surface-area-solids] Side: the curved side has area \(2\pi r h = 2\pi(3)(10) = 60\pi\).
   check: 2*pi*3*10 = 60*pi
3. [pre.geometry.surface-area-solids] Total: \(S = 18\pi + 60\pi = 78\pi\) square centimeters.
   check: 18*pi + 60*pi = 78*pi

<!-- tier 1, template: surface area of a sphere -->
## Card calc1.0-6.surf.t01
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: number
vars: r = int(2, 15)
require: r != 3
answer: 4*pi*r^2
wrong: 4/3*pi*r^3 => That is the volume of the sphere. The surface area is 4 pi r squared. @1; pi*r^2 => That is the area of a flat circle with the same radius. The surface of a sphere has four times that area. @1

### Question
A spherical storage tank has a radius of [[r]] m. Find the area of its outer surface in square meters. Give an exact answer.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the surface area of a sphere is 4 pi times the square of its radius.
1. [pre.geometry.surface-area-solids] Surface area: \(S = 4\pi r^2 = 4\pi([[r]])^2 = [[tex(4*pi*r^2)]]\) square meters.
   check: 4*pi*r^2 = pi*(2*r)^2

<!-- tier 1: total surface area of a box -->
## Card calc1.0-6.surf.001
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: number
answer: 62
wrong: 30 => That is the volume of the box. The surface area adds up the areas of its six faces. @1; 31 => The box has three pairs of equal faces, so the sum lw + lh + wh must be doubled. @1

### Question
A closed box measures 5 cm by 3 cm by 2 cm. Find its total surface area in square centimeters.

### Solution
0. [pre.geometry.surface-area-solids] Set up: a box has six rectangular faces, in three pairs of equal faces.
1. [pre.geometry.surface-area-solids] Surface area: \(S = 2(lw + lh + wh) = 2(15 + 10 + 6) = 62\) square centimeters.
   check: 2*(5*3 + 5*2 + 3*2) = 62

<!-- tier 1: the curved wall of an open pipe -->
## Card calc1.0-6.surf.002
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: number
answer: 36*pi
wrong: 44*pi => The ends of the pipe are open, so only the curved wall counts. @1; 18*pi => Unrolled, the wall is a rectangle as wide as the circumference 2 pi r, so its area is 2 pi r h. @1

### Question
A pipe is a cylinder with a radius of 2 ft and a length of 9 ft, and both of its ends are open. Find the area of its curved wall in square feet. Give an exact answer.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the curved wall unrolls into a rectangle whose width is the circumference of the pipe and whose height is its length. The open ends are not part of the wall.
1. [pre.geometry.surface-area-solids] Area: \(A = 2\pi r h = 2\pi(2)(9) = 36\pi\) square feet.
   check: 2*pi*2*9 = 36*pi

<!-- tier 2, template: total surface area of a closed can -->
## Card calc1.0-6.surf.t02
skill: pre.geometry.surface-area-solids
difficulty: 2
answer-type: number
vars: r = int(2, 8); h = int(4, 15)
answer: 2*pi*r^2 + 2*pi*r*h
wrong: 2*pi*r*h => A closed can also has a top and a bottom, two circles of area pi r squared each. @1; pi*r^2 + 2*pi*r*h => A closed can has two circular ends, not one. @1

### Question
A closed cylindrical can has a radius of [[r]] cm and a height of [[h]] cm. Find the area of the metal needed to make the can, in square centimeters. Give an exact answer.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the can has two circular ends and a curved side, so its surface area is the area of two circles plus the area of the side.
1. [pre.geometry.surface-area-solids] Surface area: \(S = 2\pi r^2 + 2\pi r h = 2\pi([[r]])^2 + 2\pi([[r]])([[h]]) = [[tex(2*pi*r^2 + 2*pi*r*h)]]\) square centimeters.
   check: 2*pi*r^2 + 2*pi*r*h = 2*pi*r*(r + h)

<!-- tier 2: the curved surface of a cone needs the slant height -->
## Card calc1.0-6.surf.003
skill: pre.geometry.surface-area-solids
uses: pre.geometry.pythagorean
difficulty: 2
answer-type: number
answer: 15*pi
wrong: 12*pi => The curved surface uses the slant height, measured along the surface from the rim to the point, not the vertical height. @2; 24*pi => The question asks for the curved surface only, so the circular base is not included. @2

### Question
A cone has a base radius of 3 cm and a vertical height of 4 cm. Find the area of its curved surface, not counting the base, in square centimeters. Give an exact answer.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the curved surface of a cone has area pi times the radius times the slant height, where the slant height is the distance from the rim to the point measured along the surface.
1. [pre.geometry.pythagorean] Slant height: the radius, the vertical height and the slant height form a right triangle, so \(s = \sqrt{3^2 + 4^2} = 5\) cm.
   check: sqrt(3^2 + 4^2) = 5
2. [pre.geometry.surface-area-solids] Lateral area: \(A = \pi r s = \pi(3)(5) = 15\pi\) square centimeters.
   check: pi*3*5 = 15*pi

<!-- tier 2: a box with no lid -->
## Card calc1.0-6.surf.004
skill: pre.geometry.surface-area-solids
difficulty: 2
answer-type: expression
vars: x
domain: x > 0
answer: x^2 + 12*x
wrong: 2*x^2 + 12*x => A box with no lid has only one square face, the base. @1; x^2 + 4*x => Each of the four sides is a rectangle x by 3, so its area is 3x, not x. @1

### Question
A box with no lid has a square base with sides of length \(x\) m and a height of 3 m. Write the total area \(S\) of its base and four sides, in square meters, as a function of \(x\).

### Solution
0. [pre.geometry.surface-area-solids] Set up: with no lid, the surface is one square base and four rectangular sides.
1. [pre.geometry.surface-area-solids] Faces: the base has area \(x^2\) and each side is a rectangle \(x\) by \(3\) with area \(3x\), so \(S = x^2 + 4(3x) = x^2 + 12x\).
   check: x^2 + 4*(3*x) = x^2 + 12*x

<!-- tier 3, template: a closed can with a fixed volume, in one variable -->
## Card calc1.0-6.surf.t03
skill: pre.geometry.surface-area-solids
uses: pre.geometry.volume-solids, alg.solve.linear
difficulty: 3
answer-type: expression
vars: n = int(2, 12); r
domain: r > 0
answer: 2*pi*r^2 + 200*n/r
wrong: 200*n/r => A closed can also has a top and a bottom, so add the area 2 pi r squared of the two ends. @3; 2*pi*r^2 + 100*n/r => The side has area 2 pi r h, and 2 pi r times the height gives twice the term 100n/r. @3; 2*pi*r^2 + 200*n => The base has area pi r squared, so h = V/(pi r squared), and the side is 2 pi r h = 200n/r. @2

### Question
A closed cylindrical can must hold [[100*n]] cubic centimeters. Let \(r\) be its radius and \(h\) its height, both in centimeters. Write the total surface area \(S\) of the can, in square centimeters, as a function of \(r\) alone.

### Solution
0. [pre.geometry.surface-area-solids] Set up: the surface area depends on both r and h, so use the fixed volume to write h in terms of r.
1. [pre.geometry.volume-solids] Volume: \(V = \pi r^2 h = [[100*n]]\).
   check: pi*r^2*(100*n/(pi*r^2)) = 100*n
2. [alg.solve.linear] Solve for \(h\): \(h = \frac{[[100*n]]}{\pi r^2}\).
   check: 100*n/(pi*r^2)*(pi*r^2) = 100*n
3. [pre.geometry.surface-area-solids] Surface area: \(S = 2\pi r^2 + 2\pi r h = 2\pi r^2 + 2\pi r \cdot \frac{[[100*n]]}{\pi r^2} = 2\pi r^2 + \frac{[[200*n]]}{r}\).
   check: 2*pi*r^2 + 2*pi*r*(100*n/(pi*r^2)) = 2*pi*r^2 + 200*n/r

<!-- tier 3: an open-top box with a fixed volume, in one variable -->
## Card calc1.0-6.surf.005
skill: pre.geometry.surface-area-solids
uses: pre.geometry.volume-solids, alg.solve.linear
difficulty: 3
answer-type: expression
vars: x
domain: x > 0
answer: x^2 + 128/x
wrong: 2*x^2 + 128/x => A box with an open top has only one square face, the base. @3; x^2 + 32/x => There are four sides, each with area xh = 32/x, so together they are 128/x. @3; x^2 + 128/x^2 => Each side is a rectangle x by h, so the area of a side is xh, not h. @3

### Question
A box with an open top and a square base is to have a volume of 32 cubic feet. Let \(x\) be the length of a side of the base in feet. Write the total area \(S\) of the base and four sides, in square feet, as a function of \(x\).

### Solution
0. [pre.geometry.surface-area-solids] Set up: the surface is the base plus four sides, and the height h depends on x because the volume is fixed.
1. [pre.geometry.volume-solids] Volume: the base is a square with side \(x\), so \(V = x^2 h = 32\).
   check: x^2*(32/x^2) = 32
2. [alg.solve.linear] Solve for \(h\): \(h = \frac{32}{x^2}\).
   check: 32/x^2*x^2 = 32
3. [pre.geometry.surface-area-solids] Surface area: the base is \(x^2\) and each of the four sides is \(xh\), so \(S = x^2 + 4xh = x^2 + 4x \cdot \frac{32}{x^2} = x^2 + \frac{128}{x}\).
   check: x^2 + 4*x*(32/x^2) = x^2 + 128/x

<!-- ===================================================================== -->
<!-- pre.geometry.arc-sector                                               -->
<!-- ===================================================================== -->

<!-- worked example: arc length and sector area from a central angle in radians -->
## Card calc1.0-6.arc-example.001
kind: example
skill: pre.geometry.arc-sector

### Question
A sector of a circle has a radius of 6 cm and a central angle of \(\frac{2\pi}{3}\) radians. Find the length of its arc and its area. Give exact answers.

### Solution
0. [pre.geometry.arc-sector] Set up: with the central angle measured in radians, the sector is the fraction (angle divided by 2 pi) of the whole circle. Taking that fraction of the circumference gives the arc length r times the angle, and taking it of the circle's area gives one half of r squared times the angle.
1. [pre.geometry.arc-sector] Arc length: \(s = r\theta = 6 \cdot \frac{2\pi}{3} = 4\pi\) centimeters.
   check: 6*(2*pi/3) = 4*pi
2. [pre.geometry.arc-sector] Area: \(A = \frac{1}{2}r^2\theta = \frac{1}{2}(6)^2\left(\frac{2\pi}{3}\right) = 12\pi\) square centimeters.
   check: 1/2*6^2*(2*pi/3) = 12*pi

<!-- tier 1, template: arc length with the angle a fraction of pi -->
## Card calc1.0-6.arc.t01
skill: pre.geometry.arc-sector
difficulty: 1
answer-type: number
vars: r = int(3, 12); d = choice(2, 3, 4, 6)
answer: r*pi/d
wrong: r^2*pi/(2*d) => That is the area of the sector. The arc length is the radius times the angle. @1; pi/d => The arc length is the radius times the angle, so multiply by the radius. @1

### Question
A circle has a radius of [[r]] cm. An arc of the circle has a central angle of \([[tex(pi/d)]]\) radians. Find the length of the arc in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.arc-sector] Set up: when the central angle is measured in radians, the arc length is the radius times the angle.
1. [pre.geometry.arc-sector] Arc length: \(s = r\theta = ([[r]])\left([[tex(pi/d)]]\right) = [[tex(r*pi/d)]]\) centimeters.
   check: r*(pi/d) = r*pi/d

<!-- tier 1: area of a sector -->
## Card calc1.0-6.arc.001
skill: pre.geometry.arc-sector
difficulty: 1
answer-type: number
answer: 40
wrong: 4 => The radius is squared in the area of a sector, which is one half of r squared times the angle. @1; 80 => The area of a sector is one half of r squared times the angle. The factor 1/2 was left out. @1; 8 => That is the arc length, r times the angle. The question asks for the area. @1

### Question
A sector of a circle has a radius of 10 cm and a central angle of 0.8 radians. Find the area of the sector in square centimeters.

### Solution
0. [pre.geometry.arc-sector] Set up: with the central angle in radians, the area of a sector is one half of the square of the radius times the angle.
1. [pre.geometry.arc-sector] Area: \(A = \frac{1}{2}r^2\theta = \frac{1}{2}(10)^2(0.8) = 40\) square centimeters.
   check: 1/2*10^2*0.8 = 40

<!-- tier 1: the central angle from the arc length -->
## Card calc1.0-6.arc.002
skill: pre.geometry.arc-sector
difficulty: 1
answer-type: number
answer: 5/2
wrong: 2/5 => The central angle is the arc length divided by the radius, not the radius divided by the arc length. @1; 90 => To find the angle in radians, divide the arc length by the radius. Do not multiply. @1

### Question
An arc of length 15 cm lies on a circle of radius 6 cm. Find the central angle of the arc in radians.

### Solution
0. [pre.geometry.arc-sector] Set up: the arc length is the radius times the central angle in radians, so the angle is the arc length divided by the radius.
1. [pre.geometry.arc-sector] Angle: \(\theta = \frac{s}{r} = \frac{15}{6} = \frac{5}{2}\) radians.
   check: 15/6 = 5/2

<!-- tier 2, template: arc length with the angle in degrees -->
## Card calc1.0-6.arc.t02
skill: pre.geometry.arc-sector
uses: trig.angles.radians
difficulty: 2
answer-type: number
vars: r = int(3, 12); a = choice(30, 45, 60, 90, 120, 135, 150, 180)
answer: r*a*pi/180
wrong: r*a => The arc length formula s = r theta needs the angle in radians. Convert the degrees to radians first. @1; r*a*180/pi => To change degrees to radians, multiply by pi over 180, not 180 over pi. @1

### Question
A circle has a radius of [[r]] cm. An arc of the circle has a central angle of \([[a]]^\circ\). Find the length of the arc in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.arc-sector] Set up: the arc length formula needs the central angle in radians, so convert the angle first.
1. [trig.angles.radians] Convert: \([[a]]^\circ = [[a]] \cdot \frac{\pi}{180} = [[tex(a*pi/180)]]\) radians.
   check: a*pi/180 = a*(pi/180)
2. [pre.geometry.arc-sector] Arc length: \(s = r\theta = ([[r]])\left([[tex(a*pi/180)]]\right) = [[tex(r*a*pi/180)]]\) centimeters.
   check: r*(a*pi/180) = r*a*pi/180

<!-- tier 2: the area of a sector from the arc length -->
## Card calc1.0-6.arc.003
skill: pre.geometry.arc-sector
difficulty: 2
answer-type: number
answer: 48
wrong: 96 => The area of a sector is one half of r squared times the angle. The factor 1/2 was left out. @2; 64/3 => The central angle is the arc length divided by the radius, 12/8, not the radius divided by the arc length. @1

### Question
A sector of a circle has a radius of 8 cm and an arc length of 12 cm. Find the area of the sector in square centimeters.

### Solution
0. [pre.geometry.arc-sector] Set up: the area of a sector needs the central angle, which is the arc length divided by the radius.
1. [pre.geometry.arc-sector] Angle: \(\theta = \frac{s}{r} = \frac{12}{8} = \frac{3}{2}\) radians.
   check: 12/8 = 3/2
2. [pre.geometry.arc-sector] Area: \(A = \frac{1}{2}r^2\theta = \frac{1}{2}(8)^2\left(\frac{3}{2}\right) = 48\) square centimeters.
   check: 1/2*8^2*(3/2) = 48

<!-- tier 2: the edge of one slice of a pizza -->
## Card calc1.0-6.arc.004
skill: pre.geometry.arc-sector
uses: pre.geometry.perimeter-circumference
difficulty: 2
answer-type: number
answer: 16 + 2*pi
wrong: 2*pi => The edge of a slice also includes the two straight cuts, each as long as the radius. @3; 16 + pi/4 => The arc length is the radius times the angle, so multiply the angle by the radius 8. @2

### Question
A circular pizza with a radius of 8 in is cut into 8 equal slices. Find the length of the whole edge of one slice, the curved crust plus the two straight cuts, in inches. Give an exact answer.

### Solution
0. [pre.geometry.arc-sector] Set up: each slice is a sector. Its edge is the curved arc plus two straight sides, each one radius long.
1. [pre.geometry.arc-sector] Angle: the 8 slices share the full angle of \(2\pi\) radians, so each central angle is \(\theta = \frac{2\pi}{8} = \frac{\pi}{4}\).
   check: 2*pi/8 = pi/4
2. [pre.geometry.arc-sector] Arc: \(s = r\theta = 8 \cdot \frac{\pi}{4} = 2\pi\) inches.
   check: 8*(pi/4) = 2*pi
3. [pre.geometry.perimeter-circumference] Edge: the perimeter of the slice is the arc plus the two radii, \(2\pi + 8 + 8 = 16 + 2\pi\) inches.
   check: 2*pi + 8 + 8 = 16 + 2*pi

<!-- tier 3, template: a sector rolled into a cone -->
## Card calc1.0-6.arc.t03
skill: pre.geometry.arc-sector
uses: pre.geometry.perimeter-circumference
difficulty: 3
answer-type: number
vars: R = choice(12, 24, 36); f = choice(1/2, 2/3, 3/4, 5/6)
answer: R*f
wrong: 2*R*f => The base of the cone is a circle with circumference 2 pi r, so divide the arc length by 2 pi, not by pi. @2; 2*pi*R*f => That is the circumference of the base of the cone. Divide by 2 pi to get its radius. @2; R => The radius of the sheet becomes the slant height of the cone, and the radius of the base is smaller. @1

### Question
A sector with a central angle of \([[tex(2*pi*f)]]\) radians is cut from a circular sheet of paper of radius [[R]] cm. The two straight edges of the sector are joined to form a cone, so that the curved edge of the sector becomes the circle around the base of the cone. Find the radius of the base of the cone in centimeters.

### Solution
0. [pre.geometry.arc-sector] Set up: the curved edge of the sector becomes the circle around the base of the cone. Find the length of that arc, then find the radius of a circle with that circumference.
1. [pre.geometry.arc-sector] Arc length: \(s = R\theta = ([[R]])\left([[tex(2*pi*f)]]\right) = [[tex(2*pi*R*f)]]\) centimeters.
   check: R*(2*pi*f) = 2*pi*R*f
2. [pre.geometry.perimeter-circumference] Base circle: its circumference is \(2\pi r = [[tex(2*pi*R*f)]]\), so \(r = [[tex(R*f)]]\) centimeters.
   check: 2*pi*(R*f) = 2*pi*R*f
   check: 2*pi*R*f/(2*pi) = R*f

<!-- tier 3: a sector with a fixed perimeter, area in one variable -->
## Card calc1.0-6.arc.005
skill: pre.geometry.arc-sector
uses: pre.geometry.perimeter-circumference
difficulty: 3
answer-type: expression
vars: r
answer: 20*r - r^2
wrong: r*(40 - r)/2 => The straight edges are two radii, so the arc is 40 - 2r, not 40 - r. @1; r*(40 - 2*r) => The area of a sector is one half of the radius times the arc length. The factor 1/2 was left out. @2

### Question
A sector of a circle has radius \(r\) cm. The perimeter of the sector, the arc plus the two straight edges, is 40 cm. Write the area \(A\) of the sector, in square centimeters, as a function of \(r\).

### Solution
0. [pre.geometry.arc-sector] Set up: the area of a sector is one half of the radius times the arc length, so find the arc length from the perimeter first.
1. [pre.geometry.perimeter-circumference] Perimeter: the boundary is two radii plus the arc \(s\), so \(2r + s = 40\) and \(s = 40 - 2r\).
   check: 2*r + (40 - 2*r) = 40
2. [pre.geometry.arc-sector] Area: \(A = \frac{1}{2}rs = \frac{1}{2}r(40 - 2r) = 20r - r^2\).
   check: 1/2*r*(40 - 2*r) = 20*r - r^2

<!-- ===================================================================== -->
<!-- pre.geometry.angle-relationships                                      -->
<!-- ===================================================================== -->

<!-- worked example: base angles, then a straight line -->
## Card calc1.0-6.angle-example.001
kind: example
skill: pre.geometry.angle-relationships

### Question
In triangle ABC, sides AB and AC are equal and angle A measures \(40^\circ\). Side BC is extended past C to a point D. Find the measure of angle ACD.

### Solution
0. [pre.geometry.angle-relationships] Set up: angles opposite equal sides are equal, the three angles of a triangle add up to 180 degrees, and two angles that together make a straight line add up to 180 degrees.
1. [pre.geometry.angle-relationships] Base angles: since AB = AC, angles B and C are equal, and together they measure \(180^\circ - 40^\circ = 140^\circ\), so each measures \(70^\circ\).
   check: (180 - 40)/2 = 70
2. [pre.geometry.angle-relationships] Straight line: angles ACB and ACD make a straight line, so \(\angle ACD = 180^\circ - 70^\circ = 110^\circ\).
   check: 180 - 70 = 110

<!-- tier 1, template: the third angle of a triangle -->
## Card calc1.0-6.angle.t01
skill: pre.geometry.angle-relationships
difficulty: 1
answer-type: number
vars: a = int(25, 80); b = int(30, 85)
require: a + b >= 80; a + b <= 160; a + b != 90
answer: 180 - a - b
wrong: 360 - a - b => The angles of a triangle add up to 180 degrees, not 360 degrees. @1; a + b => That is the sum of two of the angles. The third angle is what is left of 180 degrees. @1

### Question
Two angles of a triangle measure \([[a]]^\circ\) and \([[b]]^\circ\). Find the measure of the third angle in degrees.

### Solution
0. [pre.geometry.angle-relationships] Set up: the three angles of a triangle add up to 180 degrees.
1. [pre.geometry.angle-relationships] Third angle: \(180^\circ - [[a]]^\circ - [[b]]^\circ = [[180 - a - b]]^\circ\).
   check: (180 - a) - b = 180 - a - b

<!-- tier 1: opposite angles and angles on a straight line, select all that apply -->
## Card calc1.0-6.angle.001
skill: pre.geometry.angle-relationships
difficulty: 1
answer-type: choice

### Question
Two straight lines cross, and one of the four angles formed measures \(65^\circ\). Which of these angle measures also appear among the four angles? Select all that apply.

### Choices
- [ ] \(25^\circ\)
- [x] \(65^\circ\)
- [ ] \(90^\circ\)
- [x] \(115^\circ\)
- [ ] \(130^\circ\)

### Solution
0. [pre.geometry.angle-relationships] Set up: where two lines cross, opposite angles are equal, and two neighboring angles together make a straight line, so they add up to 180 degrees.
1. [pre.geometry.angle-relationships] Opposite angle: the angle opposite the \(65^\circ\) angle is also \(65^\circ\).
   check: 65 = 65
2. [pre.geometry.angle-relationships] Neighboring angles: each neighbor measures \(180^\circ - 65^\circ = 115^\circ\), and the angle opposite a neighbor is \(115^\circ\) too. The four angles are \(65^\circ, 115^\circ, 65^\circ, 115^\circ\).
   check: 180 - 65 = 115

<!-- tier 1: the base angle of an isosceles triangle -->
## Card calc1.0-6.angle.002
skill: pre.geometry.angle-relationships
difficulty: 1
answer-type: number
answer: 70
wrong: 140 => The two base angles together measure 140 degrees, so each one is half of that. @1; 50 => The three angles of a triangle add up to 180 degrees, not 90 degrees. @1

### Question
An isosceles triangle has a \(40^\circ\) angle between its two equal sides. Find the measure, in degrees, of each of the other two angles.

### Solution
0. [pre.geometry.angle-relationships] Set up: the angles opposite the equal sides are equal, and the three angles of a triangle add up to 180 degrees.
1. [pre.geometry.angle-relationships] Base angles: the other two angles are equal and together measure \(180^\circ - 40^\circ = 140^\circ\), so each measures \(70^\circ\).
   check: (180 - 40)/2 = 70

<!-- tier 2, template: same-side interior angles between parallel lines -->
## Card calc1.0-6.angle.t02
skill: pre.geometry.angle-relationships
difficulty: 2
answer-type: number
vars: a = int(35, 85)
answer: 180 - a
wrong: a => Alternate interior angles are equal, but angles between the parallel lines and on the same side of the crossing line are supplementary. @1; 90 - a => These angles are supplementary, adding up to 180 degrees, not complementary. @1

### Question
Lines \(m\) and \(n\) are parallel, and a third line crosses both of them. Two of the angles formed lie between \(m\) and \(n\) and on the same side of the third line. One of these angles measures \([[a]]^\circ\). Find the measure of the other one in degrees.

### Solution
0. [pre.geometry.angle-relationships] Set up: when a line crosses two parallel lines, two angles that lie between the parallel lines and on the same side of the crossing line are supplementary, so they add up to 180 degrees.
1. [pre.geometry.angle-relationships] Other angle: \(180^\circ - [[a]]^\circ = [[180 - a]]^\circ\).
   check: 180 - a = 90 + (90 - a)

<!-- tier 2: three angles of a triangle written with a variable -->
## Card calc1.0-6.angle.003
skill: pre.geometry.angle-relationships
uses: alg.solve.linear
difficulty: 2
answer-type: number
answer: 24
wrong: 60 => The angles of a triangle add up to 180 degrees, not 360 degrees. @1; 6 => The angles of a triangle add up to 180 degrees, not 90 degrees. @1

### Question
The three angles of a triangle measure \((2x + 10)^\circ\), \((3x - 5)^\circ\) and \(55^\circ\). Find \(x\).

### Solution
0. [pre.geometry.angle-relationships] Set up: the three angles of a triangle add up to 180 degrees, so write that sum as an equation in x.
1. [pre.geometry.angle-relationships] Equation: \((2x + 10) + (3x - 5) + 55 = 180\), which simplifies to \(5x + 60 = 180\).
   check: (2*24 + 10) + (3*24 - 5) + 55 = 180
2. [alg.solve.linear] Solve: \(5x = 120\), so \(x = 24\).
   check: solve(5*x + 60 - 180, x) = {24}
   check: 120/5 = 24

<!-- tier 2: an angle outside the triangle -->
## Card calc1.0-6.angle.004
skill: pre.geometry.angle-relationships
difficulty: 2
answer-type: number
answer: 85
wrong: 5 => Angle ACD is outside the triangle. The interior angle at C is 180 minus 130, which is 50 degrees. @1; 50 => That is the interior angle at C. The question asks for angle B. @2

### Question
In triangle ABC, side BC is extended past C to a point D. Angle ACD measures \(130^\circ\) and angle A measures \(45^\circ\). Find the measure of angle B in degrees.

### Solution
0. [pre.geometry.angle-relationships] Set up: angle ACD is outside the triangle. It makes a straight line with the interior angle at C, and the three interior angles of the triangle add up to 180 degrees.
1. [pre.geometry.angle-relationships] Interior angle at C: \(\angle ACB = 180^\circ - 130^\circ = 50^\circ\).
   check: 180 - 130 = 50
2. [pre.geometry.angle-relationships] Angle B: \(\angle B = 180^\circ - 45^\circ - 50^\circ = 85^\circ\).
   check: 180 - 45 - 50 = 85

<!-- tier 3, template: an angle bisector and a triangle sum -->
## Card calc1.0-6.angle.t03
skill: pre.geometry.angle-relationships
difficulty: 3
answer-type: number
vars: p = int(20, 40); q = int(15, 40)
require: p != q
let: b = 2*p; c = 2*q
answer: 90 + p - q
wrong: 90 + q - p => That is angle ADB. Angle ADC is the angle at D on the side of C, between DA and DC. @3; 2*p => That uses all of angle A in triangle ADC. The bisector splits angle A into two equal halves, so use half of it. @3

### Question
In triangle ABC, angle B measures \([[b]]^\circ\) and angle C measures \([[c]]^\circ\). The bisector of angle A meets side BC at the point D. Find the measure of angle ADC in degrees.

### Solution
0. [pre.geometry.angle-relationships] Set up: find angle A from the triangle sum, split it in half with the bisector, then use the triangle sum again in triangle ADC.
1. [pre.geometry.angle-relationships] Angle A: \(\angle A = 180^\circ - [[b]]^\circ - [[c]]^\circ = [[180 - b - c]]^\circ\).
   check: 180 - b - c = 180 - 2*p - 2*q
2. [pre.geometry.angle-relationships] Bisector: it splits angle A into two equal angles, so \(\angle DAC = \frac{1}{2}([[180 - b - c]]^\circ) = [[90 - p - q]]^\circ\).
   check: (180 - b - c)/2 = 90 - p - q
3. [pre.geometry.angle-relationships] Triangle ADC: \(\angle ADC = 180^\circ - \angle DAC - \angle C = 180^\circ - [[90 - p - q]]^\circ - [[c]]^\circ = [[90 + p - q]]^\circ\).
   check: 180 - (90 - p - q) - 2*q = 90 + p - q

<!-- tier 3: how many sides does a regular polygon have? -->
## Card calc1.0-6.angle.005
skill: pre.geometry.angle-relationships
uses: alg.solve.linear
difficulty: 3
answer-type: number
answer: 15
wrong: 24 => That is the exterior angle at each vertex. The number of sides is not 24. @2; 15/2 => A polygon with n sides splits into n - 2 triangles, not n - 1. @1

### Question
Each interior angle of a regular polygon measures \(156^\circ\). How many sides does the polygon have?

### Solution
0. [pre.geometry.angle-relationships] Set up: a polygon with n sides can be cut into n - 2 triangles, so its interior angles add up to (n - 2) times 180 degrees. In a regular polygon the n angles are all equal.
1. [pre.geometry.angle-relationships] Equation: each interior angle is \(\frac{(n - 2)180^\circ}{n} = 156^\circ\).
   check: (15 - 2)*180/15 = 156
2. [alg.solve.linear] Solve: \(180n - 360 = 156n\), so \(24n = 360\) and \(n = 15\).
   check: solve(180*n - 360 - 156*n, n) = {15}
   check: 360/24 = 15

<!-- ===================================================================== -->
<!-- pre.geometry.special-right-triangles                                  -->
<!-- ===================================================================== -->

<!-- worked example: the height of an equilateral triangle -->
## Card calc1.0-6.special-example.001
kind: example
skill: pre.geometry.special-right-triangles

### Question
An equilateral triangle has sides of length 10 cm. Find its height. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: the altitude of an equilateral triangle cuts it into two 30-60-90 right triangles. In a 30-60-90 triangle the sides are in the ratio 1 to the square root of 3 to 2: the short leg is opposite the 30 degree angle, the long leg is opposite the 60 degree angle, and the hypotenuse is twice the short leg.
1. [pre.geometry.special-right-triangles] Sides: the hypotenuse is a side of the triangle, 10 cm, so the short leg, half of the base, is 5 cm.
2. [pre.geometry.special-right-triangles] Height: the height is the long leg, the short leg times the square root of 3, so \(h = 5\sqrt{3}\) centimeters.
   check: sqrt(10^2 - 5^2) = 5*sqrt(3)

<!-- tier 1, template: the hypotenuse of a 45-45-90 triangle -->
## Card calc1.0-6.special.t01
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: number
vars: a = int(2, 12)
answer: a*sqrt(2)
wrong: 2*a => In a 45-45-90 triangle the hypotenuse is the leg times the square root of 2, not 2. @1; a*sqrt(3) => The square root of 3 belongs to the 30-60-90 triangle. In a 45-45-90 triangle the hypotenuse is the leg times the square root of 2. @1

### Question
A right triangle has two equal legs, each [[a]] cm long. Find the length of its hypotenuse in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: a right triangle with two equal legs is a 45-45-90 triangle, and its sides are in the ratio 1 to 1 to the square root of 2.
1. [pre.geometry.special-right-triangles] Hypotenuse: \(c = a\sqrt{2} = [[a]]\sqrt{2}\) centimeters.
   check: sqrt(a^2 + a^2) = a*sqrt(2)

<!-- tier 1: a leg of a 45-45-90 triangle from the hypotenuse -->
## Card calc1.0-6.special.001
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: number
answer: 5*sqrt(2)
wrong: 10*sqrt(2) => The hypotenuse is the longest side, the leg times the square root of 2, so the leg is the hypotenuse divided by the square root of 2. @1; 5 => Half of the hypotenuse is the short leg of a 30-60-90 triangle. In a 45-45-90 triangle each leg is the hypotenuse divided by the square root of 2. @1

### Question
The hypotenuse of a 45-45-90 triangle is 10 in. Find the length of each leg in inches. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: in a 45-45-90 triangle the hypotenuse is the leg times the square root of 2, so each leg is the hypotenuse divided by the square root of 2.
1. [pre.geometry.special-right-triangles] Leg: \(a = \frac{10}{\sqrt{2}} = \frac{10\sqrt{2}}{2} = 5\sqrt{2}\) inches.
   check: 10/sqrt(2) = 5*sqrt(2)

<!-- tier 1: the other two sides of a 30-60-90 triangle -->
## Card calc1.0-6.special.002
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: list
answer: 4*sqrt(3), 8
wrong: 8, 4*sqrt(3) => Give the longer leg first and then the hypotenuse. @1; 4*sqrt(2), 8 => In a 30-60-90 triangle the long leg is the short leg times the square root of 3. The square root of 2 belongs to the 45-45-90 triangle. @1

### Question
In a 30-60-90 triangle the shorter leg is 4 cm long. Find the longer leg and the hypotenuse, in that order. Give exact answers.

### Solution
0. [pre.geometry.special-right-triangles] Set up: in a 30-60-90 triangle the sides are in the ratio 1 to the square root of 3 to 2. The long leg is the short leg times the square root of 3, and the hypotenuse is twice the short leg.
1. [pre.geometry.special-right-triangles] Sides: the longer leg is \(4\sqrt{3}\) cm and the hypotenuse is \(2(4) = 8\) cm.
   check: 2*4 = 8
   check: sqrt(8^2 - 4^2) = 4*sqrt(3)
   check: {4*sqrt(3), 8} = {4*sqrt(3), 8}

<!-- tier 2, template: the short leg from the long leg -->
## Card calc1.0-6.special.t02
skill: pre.geometry.special-right-triangles
difficulty: 2
answer-type: number
vars: L = int(2, 12)
answer: L*sqrt(3)/3
wrong: L*sqrt(3) => The long leg is the short leg times the square root of 3, so the short leg is the long leg divided by the square root of 3. @1; L/2 => The short leg is half of the hypotenuse, not half of the long leg. @1

### Question
The longer leg of a 30-60-90 triangle is [[L]] cm long. Find the length of the shorter leg in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: in a 30-60-90 triangle the long leg is the short leg times the square root of 3, so the short leg is the long leg divided by the square root of 3.
1. [pre.geometry.special-right-triangles] Short leg: divide the long leg by the square root of 3 and rationalize the denominator, \(a = \frac{[[L]]}{\sqrt{3}} = [[tex(L*sqrt(3)/3)]]\) centimeters.
   check: L/sqrt(3) = L*sqrt(3)/3

<!-- tier 2: a ladder leaning at 60 degrees -->
## Card calc1.0-6.special.003
skill: pre.geometry.special-right-triangles
difficulty: 2
answer-type: number
answer: 6*sqrt(3)
wrong: 6 => The foot of the ladder is 6 ft from the wall. That is the short leg. The ladder reaches higher, along the long leg. @1; 12*sqrt(3) => The long leg is the short leg times the square root of 3, and the short leg is half of the ladder, 6 ft, not 12 ft. @1

### Question
A 12-ft ladder leans against a vertical wall and makes a \(60^\circ\) angle with the level ground. How high up the wall does the ladder reach? Give an exact answer in feet.

### Solution
0. [pre.geometry.special-right-triangles] Set up: the ladder, the wall and the ground form a right triangle with angles of 30, 60 and 90 degrees. The ladder is the hypotenuse, and the height reached is the side opposite the 60 degree angle, the long leg.
1. [pre.geometry.special-right-triangles] Short leg: it is opposite the 30 degree angle, so it is half of the hypotenuse, \(\frac{12}{2} = 6\) ft.
   check: 12/2 = 6
2. [pre.geometry.special-right-triangles] Long leg: the height is the short leg times the square root of 3, \(6\sqrt{3}\) feet, which is about 10.4 ft.
   check: 6*sqrt(3) = sqrt(12^2 - 6^2)

<!-- tier 2: the area of an isosceles right triangle from its hypotenuse -->
## Card calc1.0-6.special.004
skill: pre.geometry.special-right-triangles
uses: pre.geometry.area-plane-figures
difficulty: 2
answer-type: expression
vars: h
answer: h^2/4
wrong: h^2/2 => The legs are not equal to the hypotenuse. Each leg is the hypotenuse divided by the square root of 2. @1; h^2/8 => In a 45-45-90 triangle the leg is h divided by the square root of 2, not h divided by 2. @1

### Question
An isosceles right triangle has hypotenuse \(h\). Write its area \(A\) in terms of \(h\).

### Solution
0. [pre.geometry.special-right-triangles] Set up: the two equal legs come from the hypotenuse by the 45-45-90 ratios, and then the area is half of one leg times the other.
1. [pre.geometry.special-right-triangles] Legs: each leg is \(a = \frac{h}{\sqrt{2}}\).
   check: (h/sqrt(2))^2 + (h/sqrt(2))^2 = h^2
2. [pre.geometry.area-plane-figures] Area: \(A = \frac{1}{2}a^2 = \frac{1}{2}\cdot\frac{h^2}{2} = \frac{h^2}{4}\).
   check: 1/2*(h/sqrt(2))^2 = h^2/4

<!-- tier 3, template: the perimeter of an equilateral triangle from its altitude -->
## Card calc1.0-6.special.t03
skill: pre.geometry.special-right-triangles
uses: pre.geometry.perimeter-circumference
difficulty: 3
answer-type: number
vars: k = int(1, 12)
answer: 6*sqrt(3)*k
wrong: 9*k => The altitude is not a side of the triangle. Each side is longer than the altitude. @1; 18*sqrt(3)*k => The long leg is the short leg times the square root of 3, so half of a side is the altitude divided by the square root of 3, not multiplied. @1

### Question
An equilateral triangle has an altitude of [[3*k]] cm. Find its perimeter in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: the altitude cuts the equilateral triangle into two 30-60-90 right triangles. The altitude is the long leg, half of a side is the short leg, and a side is the hypotenuse.
1. [pre.geometry.special-right-triangles] Side: half of a side is the long leg divided by the square root of 3, which is \(\frac{[[3*k]]}{\sqrt{3}} = [[tex(k*sqrt(3))]]\) cm, so a whole side is \([[tex(2*k*sqrt(3))]]\) cm.
   check: 3*k/sqrt(3) = k*sqrt(3)
2. [pre.geometry.perimeter-circumference] Perimeter: the three sides are equal, so \(P = 3\left([[tex(2*k*sqrt(3))]]\right) = [[tex(6*k*sqrt(3))]]\) centimeters.
   check: 3*(2*k*sqrt(3)) = 6*sqrt(3)*k

<!-- tier 3: the altitude to the hypotenuse of a 30-60-90 triangle -->
## Card calc1.0-6.special.005
skill: pre.geometry.special-right-triangles
uses: pre.geometry.area-plane-figures, alg.solve.linear
difficulty: 3
answer-type: number
answer: 3*sqrt(3)
wrong: 6 => That is the length of the leg BC. The altitude from C to the hypotenuse is shorter than either leg. @3; 18*sqrt(3) => That is the area of the triangle. The altitude comes from setting the area equal to one half of the hypotenuse times the altitude. @3

### Question
In right triangle ABC the right angle is at C, angle A measures \(30^\circ\), and the hypotenuse AB is 12 cm long. Find the length of the altitude from C to AB in centimeters. Give an exact answer.

### Solution
0. [pre.geometry.special-right-triangles] Set up: first find the legs from the 30-60-90 ratios. The altitude to the hypotenuse then follows by finding the area of the triangle in two ways.
1. [pre.geometry.special-right-triangles] Legs: BC is opposite the 30 degree angle, so it is half of the hypotenuse, 6 cm, and AC is the long leg, \(6\sqrt{3}\) cm.
   check: sqrt(12^2 - 6^2) = 6*sqrt(3)
2. [pre.geometry.area-plane-figures] Area two ways: with the legs as base and height, \(A = \frac{1}{2}(6)(6\sqrt{3}) = 18\sqrt{3}\), and with AB as the base, \(A = \frac{1}{2}(12)h = 6h\).
   check: 1/2*6*6*sqrt(3) = 18*sqrt(3)
3. [alg.solve.linear] Solve: \(6h = 18\sqrt{3}\), so \(h = 3\sqrt{3}\) centimeters.
   check: 18*sqrt(3)/6 = 3*sqrt(3)

<!-- ===================================================================== -->
<!-- pre.geometry.distance-formula                                         -->
<!-- ===================================================================== -->

<!-- worked example: a distance, then the circle with that radius -->
## Card calc1.0-6.dist-example.001
kind: example
skill: pre.geometry.distance-formula

### Question
On a map, 1 unit is 1 km. A hiker is at the point \((-2, 3)\) and a cabin is at the point \((4, -5)\). Find the straight-line distance from the hiker to the cabin. Then write the equation of the circle that is centered at the hiker and passes through the cabin.

### Solution
0. [pre.geometry.distance-formula] Set up: the distance between two points is the square root of the sum of the squares of the horizontal and vertical differences, the hypotenuse of the right triangle that has those differences as its legs. A circle is all of the points at one distance, the radius, from its center, so its equation says that the squared distance from the center is the radius squared.
1. [pre.geometry.distance-formula] Distance: \(d = \sqrt{(4 - (-2))^2 + (-5 - 3)^2} = \sqrt{36 + 64} = 10\) kilometers.
   check: sqrt((4 - (-2))^2 + (-5 - 3)^2) = 10
2. [pre.geometry.distance-formula] Circle: the center is \((-2, 3)\) and the radius is \(10\), so \((x + 2)^2 + (y - 3)^2 = 100\). The cabin is on the circle, because \((4 + 2)^2 + (-5 - 3)^2 = 36 + 64 = 100\).
   check: (4 + 2)^2 + (-5 - 3)^2 = 100

<!-- tier 1, template: the distance between two points, a Pythagorean triple -->
## Card calc1.0-6.dist.t01
skill: pre.geometry.distance-formula
difficulty: 1
answer-type: number
vars: m = int(2, 4); n = int(1, 3); s = choice(1, -1); a = int(-6, 6); b = int(-6, 6)
require: m > n
let: u = m^2 - n^2; v = 2*m*n; w = m^2 + n^2; c = a + s*u; d = b + v
answer: w
wrong: u + v => That adds the horizontal and vertical differences. The distance is the square root of the sum of their squares. @1; w^2 => That is the square of the distance. Take the square root. @1

### Question
On a map, 1 unit is 1 km. A trailhead is at the point \(([[a]], [[b]])\) and a lake is at the point \(([[c]], [[d]])\). Find the straight-line distance from the trailhead to the lake in kilometers.

### Solution
0. [pre.geometry.distance-formula] Set up: the distance between two points is the square root of the sum of the squares of the horizontal and vertical differences.
1. [pre.geometry.distance-formula] Distance: \(d = \sqrt{([[c - a]])^2 + ([[d - b]])^2} = \sqrt{[[u^2]] + [[v^2]]} = [[w]]\) kilometers.
   check: sqrt((c - a)^2 + (d - b)^2) = w

<!-- tier 1: the distance between two points with negative coordinates -->
## Card calc1.0-6.dist.001
skill: pre.geometry.distance-formula
difficulty: 1
answer-type: number
answer: 10
wrong: 2*sqrt(10) => Subtract the x-coordinates with care: 5 - (-3) = 8, not 2. @1; 14 => That adds the differences 8 and 6. Square each difference, add them, and then take the square root. @1

### Question
On a field map, 1 unit is 1 m. A sprinkler is at the point \((-3, 1)\) and a tree is at the point \((5, -5)\). Find the distance from the sprinkler to the tree in meters.

### Solution
0. [pre.geometry.distance-formula] Set up: the distance between two points is the square root of the sum of the squares of the horizontal and vertical differences.
1. [pre.geometry.distance-formula] Distance: \(d = \sqrt{(5 - (-3))^2 + (-5 - 1)^2} = \sqrt{64 + 36} = 10\) meters.
   check: sqrt((5 - (-3))^2 + (-5 - 1)^2) = 10

<!-- tier 1: which points lie on a circle centered at the origin, select all that apply -->
## Card calc1.0-6.dist.002
skill: pre.geometry.distance-formula
difficulty: 1
answer-type: choice

### Question
Which of these points lie on the circle \(x^2 + y^2 = 25\)? Select all that apply.

### Choices
- [x] \((3, 4)\)
- [ ] \((5, 5)\)
- [x] \((-4, 3)\)
- [ ] \((2, 4)\)
- [x] \((0, -5)\)

### Solution
0. [pre.geometry.distance-formula] Set up: this circle is centered at the origin with radius 5. The squared distance from the origin to a point is the sum of the squares of its coordinates, so a point is on the circle exactly when that sum is 25.
1. [pre.geometry.distance-formula] On the circle: \(3^2 + 4^2 = 25\), \((-4)^2 + 3^2 = 25\) and \(0^2 + (-5)^2 = 25\).
   check: 3^2 + 4^2 = 25
   check: (-4)^2 + 3^2 = 25
   check: 0^2 + (-5)^2 = 25
2. [pre.geometry.distance-formula] Off the circle: \(5^2 + 5^2 = 50\) and \(2^2 + 4^2 = 20\), and neither is 25.
   check: 5^2 + 5^2 = 50
   check: 2^2 + 4^2 = 20

<!-- tier 2, template: the distance from a fixed point to a point on a line -->
## Card calc1.0-6.dist.t02
skill: pre.geometry.distance-formula
difficulty: 2
answer-type: expression
vars: m = int(2, 5); c = int(1, 6); p = int(1, 6); x
domain: -10 < x < 10
answer: sqrt((x - p)^2 + (m*x + c)^2)
wrong: (x - p)^2 + (m*x + c)^2 => That is the square of the distance. Take the square root. @1; sqrt((x + p)^2 + (m*x + c)^2) => The horizontal difference is x minus [[p]], not x plus [[p]]. @1; sqrt((x - p)^2 + (m*x)^2) => The y-coordinate of the point is the whole expression for y on the line, including the constant term. @1

### Question
The point \(P = (x, y)\) lies on the line \(y = [[tex(m*x + c)]]\). Write the distance \(D\) from \(P\) to the point \(([[p]], 0)\) as a function of \(x\).

### Solution
0. [pre.geometry.distance-formula] Set up: the distance is the square root of the squared horizontal difference plus the squared vertical difference, and the y-coordinate of P comes from the equation of the line.
1. [pre.geometry.distance-formula] Distance: \(D = \sqrt{(x - [[p]])^2 + (y - 0)^2} = \sqrt{(x - [[p]])^2 + ([[tex(m*x + c)]])^2}\).
   check: sqrt((x - p)^2 + (m*x + c - 0)^2) = sqrt((x - p)^2 + (m*x + c)^2)

<!-- tier 2: the cable between three towers -->
## Card calc1.0-6.dist.003
skill: pre.geometry.distance-formula
uses: pre.geometry.perimeter-circumference
difficulty: 2
answer-type: number
answer: 26 + 7*sqrt(2)
wrong: 26 + 7 => The towers at (5, 12) and (12, 5) are 7 apart across and 7 apart up, so the distance between them is the square root of 49 + 49, not 7. @3; 26 + sqrt(14) => Square each difference before adding them: the square root of 7^2 + 7^2, not of 7 + 7. @3

### Question
Three radio towers stand at the points \((0, 0)\), \((5, 12)\) and \((12, 5)\) on a map where 1 unit is 1 km. A cable will run straight between each pair of towers. Find the total length of cable in kilometers. Give an exact answer.

### Solution
0. [pre.geometry.distance-formula] Set up: there are three cables, one for each pair of towers. Find each length with the distance formula, and then add them.
1. [pre.geometry.distance-formula] First cable: from \((0, 0)\) to \((5, 12)\), \(\sqrt{5^2 + 12^2} = \sqrt{169} = 13\) km.
   check: sqrt((5 - 0)^2 + (12 - 0)^2) = 13
2. [pre.geometry.distance-formula] Second cable: from \((0, 0)\) to \((12, 5)\), \(\sqrt{12^2 + 5^2} = 13\) km.
   check: sqrt((12 - 0)^2 + (5 - 0)^2) = 13
3. [pre.geometry.distance-formula] Third cable: from \((5, 12)\) to \((12, 5)\), \(\sqrt{7^2 + (-7)^2} = \sqrt{98} = 7\sqrt{2}\) km.
   check: sqrt((12 - 5)^2 + (5 - 12)^2) = 7*sqrt(2)
4. [pre.geometry.perimeter-circumference] Total: the cable length is the perimeter of the triangle, \(13 + 13 + 7\sqrt{2} = 26 + 7\sqrt{2}\) km, which is about 35.9 km.
   check: 13 + 13 + 7*sqrt(2) = 26 + 7*sqrt(2)

<!-- tier 2: a point on a circle with a given x-coordinate -->
## Card calc1.0-6.dist.004
skill: pre.geometry.distance-formula
uses: alg.solve.polynomial
difficulty: 2
answer-type: set
answer: -6, 2
wrong: 2 => Taking a square root gives two values: y + 2 can be 4 or -4. @2; -4, 4 => The equation is (y + 2)^2 = 16, so y + 2 = 4 or y + 2 = -4. Subtract 2 to find y. @2

### Question
A circle has its center at \((1, -2)\) and a radius of 5. Find all values of \(y\) for which the point \((4, y)\) lies on the circle.

### Solution
0. [pre.geometry.distance-formula] Set up: a point is on the circle when its distance from the center equals the radius, so the squared distance from the center to the point with x-coordinate 4 is the radius squared, 25.
1. [pre.geometry.distance-formula] Equation: \((4 - 1)^2 + (y + 2)^2 = 25\), so \((y + 2)^2 = 16\).
   check: 25 - (4 - 1)^2 = 16
2. [alg.solve.polynomial] Solve: \(y + 2 = 4\) or \(y + 2 = -4\), so \(y = 2\) or \(y = -6\).
   check: solve((y + 2)^2 - 16, y) = {-6, 2}

<!-- tier 3, template: the squared distance from a fixed point to a point on a parabola -->
## Card calc1.0-6.dist.t03
skill: pre.geometry.distance-formula
uses: alg.expand.products
difficulty: 3
answer-type: expression
form: expanded
vars: k = int(2, 4); p = int(1, 8); x
let: A = k^2; B = 1 - 2*k*p; C = p^2
answer: A*x^4 + B*x^2 + C
wrong: A*x^4 + x^2 + C => Squaring a difference gives a middle term as well: (a - b)^2 = a^2 - 2ab + b^2. @2; A*x^4 + (1 + 2*k*p)*x^2 + C => The middle term of a squared difference is negative: (a - b)^2 = a^2 - 2ab + b^2. @2; k*x^4 + B*x^2 + C => The coefficient [[k]] is squared too, so the leading coefficient is [[k^2]]. @2

### Question
The point \(P = (x, y)\) lies on the parabola \(y = [[tex(k*x^2)]]\). Let \(S\) be the square of the distance from \(P\) to the point \((0, [[p]])\). Write \(S\) as a polynomial in \(x\), multiplied out.

### Solution
0. [pre.geometry.distance-formula] Set up: the squared distance is the sum of the squared horizontal and vertical differences, and the y-coordinate of P comes from the equation of the parabola.
1. [pre.geometry.distance-formula] Squared distance: \(S = (x - 0)^2 + (y - [[p]])^2 = x^2 + ([[tex(k*x^2)]] - [[p]])^2\).
   check: (x - 0)^2 + (k*x^2 - p)^2 = x^2 + (k*x^2 - p)^2
2. [alg.expand.products] Multiply out: \(([[tex(k*x^2)]] - [[p]])^2 = [[tex(k^2*x^4)]] - [[2*k*p]]x^2 + [[C]]\), so \(S = [[tex(A*x^4 + B*x^2 + C)]]\).
   check: expand(x^2 + (k*x^2 - p)^2) = A*x^4 + B*x^2 + C

<!-- tier 3: the point on the highway that is equally far from two towns -->
## Card calc1.0-6.dist.005
skill: pre.geometry.distance-formula
uses: alg.expand.products, alg.solve.linear
difficulty: 3
answer-type: number
answer: 7
wrong: 3 => The y-coordinate 3 is halfway between the y-coordinates of the two towns, but the distances also depend on how far each town is from the highway, 2 km and 6 km. Set the two squared distances equal. @1

### Question
A cell tower is to be built on a straight highway, which is the y-axis of a map where 1 unit is 1 km. Two towns are at \(A = (2, 1)\) and \(B = (6, 5)\). The tower will stand at the point \((0, y)\) on the highway, the same distance from both towns. Find \(y\) in kilometers.

### Solution
0. [pre.geometry.distance-formula] Set up: the tower is equally far from A and B when the two distances are equal, and that happens when the two squared distances are equal, which avoids the square roots.
1. [pre.geometry.distance-formula] Squared distances: from \((0, y)\) to \(A\) it is \((2 - 0)^2 + (1 - y)^2 = 4 + (y - 1)^2\), and to \(B\) it is \((6 - 0)^2 + (5 - y)^2 = 36 + (y - 5)^2\). Setting them equal gives \(4 + (y - 1)^2 = 36 + (y - 5)^2\).
   check: (2 - 0)^2 + (1 - y)^2 = 4 + (y - 1)^2
   check: (6 - 0)^2 + (5 - y)^2 = 36 + (y - 5)^2
2. [alg.expand.products] Multiply out: \(4 + (y - 1)^2 = y^2 - 2y + 5\) and \(36 + (y - 5)^2 = y^2 - 10y + 61\).
   check: expand(4 + (y - 1)^2) = y^2 - 2*y + 5
   check: expand(36 + (y - 5)^2) = y^2 - 10*y + 61
3. [alg.solve.linear] Solve: the \(y^2\) terms cancel, leaving \(-2y + 5 = -10y + 61\), so \(8y = 56\) and \(y = 7\).
   check: solve(y^2 - 2*y + 5 - (y^2 - 10*y + 61), y) = {7}
   check: 56/8 = 7

<!-- ===================================================================== -->
<!-- pre.geometry.law-of-cosines                                           -->
<!-- ===================================================================== -->

<!-- worked example: two hikers on trails that meet at 60 degrees -->
## Card calc1.0-6.lawcos-example.001
kind: example
skill: pre.geometry.law-of-cosines

### Question
Two straight trails meet at a campsite at an angle of \(60^\circ\). One hiker is 5 km from the campsite along one trail, and another hiker is 8 km from the campsite along the other trail. How far apart are the hikers?

### Solution
0. [pre.geometry.law-of-cosines] Set up: the campsite and the two hikers are the corners of a triangle in which two sides and the angle between them are known. The law of cosines gives the third side: its square is the sum of the squares of the two known sides, minus twice their product times the cosine of the angle between them.
1. [pre.geometry.law-of-cosines] Law of cosines: \(c^2 = 5^2 + 8^2 - 2(5)(8)\cos 60^\circ = 25 + 64 - 40 = 49\), so \(c = 7\) km.
   check: 5^2 + 8^2 - 2*5*8*cos(pi/3) = 49
   check: sqrt(49) = 7

<!-- tier 1, template: the third side when the angle between two sides is 60 degrees -->
## Card calc1.0-6.lawcos.t01
skill: pre.geometry.law-of-cosines
difficulty: 1
answer-type: number
vars: a = int(3, 12); b = int(3, 12)
let: k = a^2 + b^2 - a*b
answer: sqrt(k)
wrong: sqrt(a^2 + b^2) => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @1; sqrt(a^2 + b^2 + a*b) => The law of cosines subtracts 2ab cos C, so a minus sign comes before that term. @1

### Question
Two straight trails meet at a campsite at an angle of \(60^\circ\). One hiker is [[a]] km from the campsite along one trail, and a second hiker is [[b]] km from the campsite along the other trail. Find the straight-line distance between the hikers in kilometers. Give an exact answer.

### Solution
0. [pre.geometry.law-of-cosines] Set up: the campsite and the two hikers are the corners of a triangle in which two sides and the angle between them are known, so use the law of cosines: the square of the third side is the sum of the squares of the two known sides, minus twice their product times the cosine of the angle between them.
1. [pre.geometry.law-of-cosines] Law of cosines: \(c^2 = [[a]]^2 + [[b]]^2 - 2([[a]])([[b]])\cos 60^\circ = [[a^2 + b^2]] - [[a*b]] = [[k]]\), so \(c = [[tex(sqrt(k))]]\) kilometers.
   check: a^2 + b^2 - 2*a*b*cos(pi/3) = k
   check: sqrt(k) = sqrt(a^2 + b^2 - 2*a*b*cos(pi/3))

<!-- tier 1: the third side, integer result -->
## Card calc1.0-6.lawcos.001
skill: pre.geometry.law-of-cosines
difficulty: 1
answer-type: number
answer: 7
wrong: sqrt(73) => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @1; sqrt(97) => The law of cosines subtracts 2ab cos C, so a minus sign comes before that term. @1

### Question
Two sides of a triangle are 3 cm and 8 cm long, and the angle between them is \(60^\circ\). Find the length of the third side in centimeters.

### Solution
0. [pre.geometry.law-of-cosines] Set up: two sides and the angle between them are known, so the law of cosines gives the third side: its square is the sum of the squares of the two known sides, minus twice their product times the cosine of the angle between them.
1. [pre.geometry.law-of-cosines] Law of cosines: \(c^2 = 3^2 + 8^2 - 2(3)(8)\cos 60^\circ = 9 + 64 - 24 = 49\), so \(c = 7\) cm.
   check: 3^2 + 8^2 - 2*3*8*cos(pi/3) = 49
   check: sqrt(49) = 7

<!-- tier 1: recognize the law of cosines among near misses, tested on a known triangle -->
## Card calc1.0-6.lawcos.002
skill: pre.geometry.law-of-cosines
difficulty: 1
answer-type: choice

### Question
In a triangle, two sides of lengths 3 cm and 8 cm meet at an angle of \(60^\circ\), and the third side has length 7 cm. Which equation correctly relates these lengths?

### Choices
- [ ] \(7^2 = 3^2 + 8^2 + 2(3)(8)\cos 60^\circ\)
- [x] \(7^2 = 3^2 + 8^2 - 2(3)(8)\cos 60^\circ\)
- [ ] \(7^2 = 3^2 + 8^2\)
- [ ] \(7^2 = 3^2 + 8^2 - 2(3)(8)\sin 60^\circ\)

### Solution
0. [pre.geometry.law-of-cosines] Set up: the law of cosines says that the square of the side opposite the angle equals the sum of the squares of the other two sides, minus twice their product times the cosine of the angle between them. To test each equation, work out its right side and compare it with the square of 7, which is 49.
1. [pre.geometry.law-of-cosines] With the minus sign and the cosine: \(3^2 + 8^2 - 2(3)(8)\cos 60^\circ = 9 + 64 - 24 = 49\), which equals \(7^2\).
   check: 3^2 + 8^2 - 2*3*8*cos(pi/3) = 7^2
2. [pre.geometry.law-of-cosines] With a plus sign: \(3^2 + 8^2 + 2(3)(8)\cos 60^\circ = 97\), which is not 49.
   check: 3^2 + 8^2 + 2*3*8*cos(pi/3) = 97
3. [pre.geometry.law-of-cosines] Without the last term: \(3^2 + 8^2 = 73\), which is not 49, because that equation holds only for a right angle.
   check: 3^2 + 8^2 = 73
4. [pre.geometry.law-of-cosines] With the sine: \(3^2 + 8^2 - 2(3)(8)\sin 60^\circ = 73 - 24\sqrt{3}\), which is about 31.4, not 49.
   check: 3^2 + 8^2 - 2*3*8*sin(pi/3) = 73 - 24*sqrt(3)

<!-- tier 2, template: the distance between two ships as a function of time -->
## Card calc1.0-6.lawcos.t02
skill: pre.geometry.law-of-cosines
uses: trig.values.exact
difficulty: 2
answer-type: expression
vars: a = int(3, 9); b = int(3, 9); g = choice(60, 120); t
domain: t > 0
let: q = cos(g*pi/180)
answer: sqrt((a*t)^2 + (b*t)^2 - 2*(a*t)*(b*t)*q)
wrong: sqrt((a*t)^2 + (b*t)^2) => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @2; sqrt((a*t)^2 + (b*t)^2 + 2*(a*t)*(b*t)*q) => The law of cosines subtracts 2ab cos C, so a minus sign comes before that term. @2; sqrt((a*t)^2 + (b*t)^2 - 2*a*b*q) => After t hours the ships are [[a]]t and [[b]]t km from the port, so the product of the two sides has a factor of t squared. @2

### Question
Two ships leave the same port at noon. Ship A sails at [[a]] km/h and ship B sails at [[b]] km/h, on straight courses that make an angle of \([[g]]^\circ\) with each other. Write the distance \(D\) between the ships, in kilometers, as a function of the time \(t\) in hours after noon.

### Solution
0. [pre.geometry.law-of-cosines] Set up: after t hours the ships are [[a]]t km and [[b]]t km from the port, along two sides of a triangle, and the angle between those sides is the angle between the courses. The distance between the ships is the third side, so use the law of cosines.
1. [trig.values.exact] Cosine: \(\cos [[g]]^\circ = [[tex(q)]]\).
   check: cos(g*pi/180) = q
2. [pre.geometry.law-of-cosines] Law of cosines: \(D^2 = ([[a]]t)^2 + ([[b]]t)^2 - 2([[a]]t)([[b]]t)\left([[tex(q)]]\right)\), so \(D = \sqrt{([[a]]t)^2 + ([[b]]t)^2 - 2([[a]]t)([[b]]t)\left([[tex(q)]]\right)}\).
   check: sqrt((a*t)^2 + (b*t)^2 - 2*(a*t)*(b*t)*q) = sqrt((a*t)^2 + (b*t)^2 - 2*a*b*q*t^2)

<!-- tier 2: the cosine of an angle from three sides -->
## Card calc1.0-6.lawcos.003
skill: pre.geometry.law-of-cosines
uses: alg.solve.linear
difficulty: 2
answer-type: number
answer: 1/5
wrong: 5/7 => The angle is opposite the 7 cm side, and the side opposite the angle is the one alone on the left: 7^2 = 5^2 + 6^2 - 2(5)(6)cos(theta). @1; 12 => That is 60 cos(theta). Divide by 60 to find cos(theta). @2; -1/5 => From 49 = 61 - 60 cos(theta), the term 60 cos(theta) equals 61 - 49 = 12, which is positive. @2

### Question
A triangle has sides of lengths 5 cm, 6 cm and 7 cm. Let \(\theta\) be the angle between the 5 cm side and the 6 cm side. Find \(\cos\theta\).

### Solution
0. [pre.geometry.law-of-cosines] Set up: the angle is opposite the 7 cm side. Write the law of cosines for that side, which gives an equation in which cos of the angle is the only unknown.
1. [pre.geometry.law-of-cosines] Law of cosines: \(7^2 = 5^2 + 6^2 - 2(5)(6)\cos\theta\), which simplifies to \(49 = 61 - 60\cos\theta\).
   check: 5^2 + 6^2 - 2*5*6*(1/5) = 7^2
2. [alg.solve.linear] Solve: \(60\cos\theta = 61 - 49 = 12\), so \(\cos\theta = \frac{12}{60} = \frac{1}{5}\).
   check: solve(49 - 61 + 60*C, C) = {1/5}
   check: 12/60 = 1/5

<!-- tier 2: the fence around a triangular garden bed -->
## Card calc1.0-6.lawcos.004
skill: pre.geometry.law-of-cosines
uses: pre.geometry.perimeter-circumference
difficulty: 2
answer-type: number
answer: 35
wrong: 22 => The fence goes around all three sides of the bed, including the side opposite the 60 degree angle. @2; 22 + sqrt(274) => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @1; 22 + sqrt(379) => The law of cosines subtracts 2ab cos C, so a minus sign comes before that term. @1

### Question
A triangular garden bed has two sides of lengths 7 m and 15 m that meet at an angle of \(60^\circ\). Find the length of fencing needed to go all the way around the bed, in meters.

### Solution
0. [pre.geometry.law-of-cosines] Set up: find the third side with the law of cosines, because two sides and the angle between them are known. The fencing is the perimeter of the triangle.
1. [pre.geometry.law-of-cosines] Third side: \(c^2 = 7^2 + 15^2 - 2(7)(15)\cos 60^\circ = 49 + 225 - 105 = 169\), so \(c = 13\) m.
   check: 7^2 + 15^2 - 2*7*15*cos(pi/3) = 169
   check: sqrt(169) = 13
2. [pre.geometry.perimeter-circumference] Perimeter: the fencing is \(7 + 15 + 13 = 35\) meters.
   check: 7 + 15 + 13 = 35

<!-- tier 3, template: the squared distance between two moving points, multiplied out -->
## Card calc1.0-6.lawcos.t03
skill: pre.geometry.law-of-cosines
uses: trig.values.exact, alg.expand.products
difficulty: 3
answer-type: expression
form: expanded
vars: L = int(6, 20); g = choice(60, 120); x
let: q = cos(g*pi/180); A = 2 + 2*q; B = -2*L*(1 + q); C = L^2
answer: A*x^2 + B*x + C
wrong: 2*x^2 - 2*L*x + C => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @2; (2 - 2*q)*x^2 - (2 - 2*q)*L*x + C => The law of cosines subtracts 2ab cos C, so a minus sign comes before that term. @2; A*x^2 - 2*q*L*x + C => Multiplying out the square (L - x)^2 gives L^2 - 2Lx + x^2, three terms. @3

### Question
Two straight roads meet at a junction at an angle of \([[g]]^\circ\). A hiker is \(x\) km from the junction along the first road, and a cyclist is \([[L]] - x\) km from the junction along the second road. Let \(S\) be the square of the distance between them. Write \(S\) as a polynomial in \(x\), multiplied out.

### Solution
0. [pre.geometry.law-of-cosines] Set up: the junction, the hiker and the cyclist are the corners of a triangle in which two sides and the angle between them are known. The law of cosines gives the square of the distance between the hiker and the cyclist.
1. [trig.values.exact] Cosine: \(\cos [[g]]^\circ = [[tex(q)]]\).
   check: cos(g*pi/180) = q
2. [pre.geometry.law-of-cosines] Law of cosines: \(S = x^2 + ([[L]] - x)^2 - 2x([[L]] - x)\left([[tex(q)]]\right)\).
   check: x^2 + (L - x)^2 - 2*x*(L - x)*cos(g*pi/180) = x^2 + (L - x)^2 - 2*x*(L - x)*q
3. [alg.expand.products] Multiply out: collecting the terms in \(x^2\), \(x\) and the constant gives \(S = [[tex(A*x^2 + B*x + C)]]\).
   check: expand(x^2 + (L - x)^2 - 2*x*(L - x)*q) = A*x^2 + B*x + C

<!-- tier 3: two kayaks on courses described by compass directions -->
## Card calc1.0-6.lawcos.005
skill: pre.geometry.law-of-cosines
uses: pre.geometry.angle-relationships, trig.values.exact
difficulty: 3
answer-type: number
answer: 14
wrong: sqrt(76) => Check the angle between the courses and the sign of cos 120 degrees. The angle is 120 degrees and its cosine is negative, so the last term adds to the sum. @1; sqrt(136) => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos C as well. @3; 7 => The kayaks have been paddling for 2 hours, so they are 6 km and 10 km from the dock, not 3 km and 5 km. @3

### Question
Two kayakers leave a dock at the same time. One paddles due north at 3 km/h. The other paddles on a course \(60^\circ\) east of due south at 5 km/h. How far apart are the kayakers after 2 hours, in kilometers?

### Solution
0. [pre.geometry.law-of-cosines] Set up: the dock and the two kayakers are the corners of a triangle. The two sides from the dock are the distances paddled, and the angle between them is the angle between the two courses. The distance between the kayakers is the third side.
1. [pre.geometry.angle-relationships] Angle between the courses: due south points the opposite way from due north, so a course \(60^\circ\) east of due south makes an angle of \(180^\circ - 60^\circ = 120^\circ\) with due north.
   check: 180 - 60 = 120
2. [trig.values.exact] Cosine: \(\cos 120^\circ = -\frac{1}{2}\).
   check: cos(2*pi/3) = -1/2
3. [pre.geometry.law-of-cosines] Law of cosines: after 2 hours the sides are \(3(2) = 6\) km and \(5(2) = 10\) km, so \(c^2 = 6^2 + 10^2 - 2(6)(10)\left(-\frac{1}{2}\right) = 36 + 100 + 60 = 196\) and \(c = 14\) km.
   check: 6^2 + 10^2 - 2*6*10*(-1/2) = 196
   check: sqrt(196) = 14

<!-- ===================================================================== -->
<!-- pre.geometry.composite-figures                                        -->
<!-- ===================================================================== -->

<!-- worked example: a window made of a rectangle and a semicircle -->
## Card calc1.0-6.comp-example.001
kind: example
skill: pre.geometry.composite-figures

### Question
A window is a rectangle 4 ft wide and 6 ft tall, topped by a semicircle whose diameter is the top edge of the rectangle. Find the area of the window and the length of the frame around its outside edge. Give exact answers.

### Solution
0. [pre.geometry.composite-figures] Set up: split the window into a rectangle and a semicircle. The area of the window is the sum of the areas of the two pieces. The frame runs around the outside edge only, and the top edge of the rectangle lies inside the window, so that shared edge is not part of the frame.
1. [pre.geometry.composite-figures] Area: the rectangle has area \(4 \cdot 6 = 24\), and the semicircle has radius 2 and area \(\frac{1}{2}\pi(2)^2 = 2\pi\), so \(A = 24 + 2\pi\) square feet.
   check: 4*6 + 1/2*pi*2^2 = 24 + 2*pi
2. [pre.geometry.composite-figures] Frame: two sides of 6 ft, the bottom of 4 ft and the semicircular arc of length \(\frac{1}{2}(2\pi)(2) = 2\pi\) ft, so \(P = 6 + 6 + 4 + 2\pi = 16 + 2\pi\) feet.
   check: 6 + 6 + 4 + 1/2*(2*pi*2) = 16 + 2*pi

<!-- tier 1, template: a lawn with a pond cut out of it -->
## Card calc1.0-6.comp.t01
skill: pre.geometry.composite-figures
difficulty: 1
answer-type: number
vars: a = int(10, 30); b = int(8, 20); c = int(2, 6); d = int(2, 6)
answer: a*b - c*d
wrong: a*b + c*d => The pond is not grass, so its area is subtracted from the area of the whole lawn. @1; a*b => The pond lies inside the lawn but is not grass, so its area is subtracted. @1

### Question
A rectangular lawn measures [[a]] m by [[b]] m. A rectangular pond that measures [[c]] m by [[d]] m lies entirely inside the lawn. Find the area of the grass in square meters.

### Solution
0. [pre.geometry.composite-figures] Set up: the grass is the whole rectangle with the pond removed, so subtract the area of the pond from the area of the lawn.
1. [pre.geometry.composite-figures] Subtract: \(A = [[a]] \cdot [[b]] - [[c]] \cdot [[d]] = [[a*b]] - [[c*d]] = [[a*b - c*d]]\) square meters.
   check: a*b - c*d = (a*b) - (c*d)

<!-- tier 1: the outline of a house-shaped sign -->
## Card calc1.0-6.comp.001
skill: pre.geometry.composite-figures
difficulty: 1
answer-type: number
answer: 26
wrong: 32 => The top edge of the rectangle is inside the sign, where the triangle is attached, so it is not part of the outline. @1; 20 => The two slanted sides of the triangle are part of the outline of the sign. @1

### Question
A sign is shaped like a house: a rectangle 6 ft wide and 4 ft tall, with an equilateral triangle on top whose base is the top edge of the rectangle. Find the perimeter of the sign in feet.

### Solution
0. [pre.geometry.composite-figures] Set up: the perimeter is the length of the outside edge. The top edge of the rectangle is shared with the triangle and lies inside the sign, so it is left out, and the two slanted sides of the triangle take its place.
1. [pre.geometry.composite-figures] Perimeter: the bottom is 6 ft, the vertical sides are 4 ft each, and each slanted side is 6 ft, an equilateral triangle having equal sides, so \(P = 6 + 4 + 4 + 6 + 6 = 26\) feet.
   check: 6 + 4 + 4 + 6 + 6 = 26

<!-- tier 1: which expression gives the frame of a window, select the single correct one -->
## Card calc1.0-6.comp.002
skill: pre.geometry.composite-figures
difficulty: 1
answer-type: choice

### Question
A window is a rectangle \(w\) wide and \(h\) tall, topped by a semicircle whose diameter is the top edge of the rectangle. Which expression gives the length of the frame around the outside edge of the window?

### Choices
- [ ] \(2h + 2w + \frac{\pi w}{2}\)
- [ ] \(2h + w + \pi w\)
- [x] \(2h + w + \frac{\pi w}{2}\)
- [ ] \(2h + 2w + \pi w\)

### Solution
0. [pre.geometry.composite-figures] Set up: the frame is the outside edge only. It has two vertical sides, the bottom, and the curved arc, which is half of the circumference of a circle with diameter w. The top edge of the rectangle lies inside the window, so it is left out. To compare the options, try a window 4 ft wide and 6 ft tall.
1. [pre.geometry.composite-figures] Outside edge: the two sides are \(6 + 6\), the bottom is \(4\), and the arc is \(\frac{1}{2}\pi(4) = 2\pi\), so the frame has length \(16 + 2\pi\), which matches \(2h + w + \frac{\pi w}{2}\).
   check: 2*6 + 4 + pi*4/2 = 16 + 2*pi
2. [pre.geometry.composite-figures] Shared edge counted: an option with \(2w\) counts the top edge of the rectangle as well, giving \(2(6) + 2(4) + 2\pi = 20 + 2\pi\), which is too long.
   check: 2*6 + 2*4 + pi*4/2 = 20 + 2*pi
3. [pre.geometry.composite-figures] Whole circle used: an option with \(\pi w\) uses the circumference of a whole circle, giving \(12 + 4 + 4\pi = 16 + 4\pi\), which is too long.
   check: 2*6 + 4 + pi*4 = 16 + 4*pi
4. [pre.geometry.composite-figures] Both mistakes: the last option gives \(12 + 8 + 4\pi = 20 + 4\pi\), which is too long.
   check: 2*6 + 2*4 + pi*4 = 20 + 4*pi

<!-- tier 2, template: a silo made of a cylinder and a hemisphere -->
## Card calc1.0-6.comp.t02
skill: pre.geometry.composite-figures
uses: pre.geometry.volume-solids
difficulty: 2
answer-type: number
vars: r = int(2, 6); h = int(3, 12)
answer: pi*r^2*h + 2/3*pi*r^3
wrong: pi*r^2*h + 4/3*pi*r^3 => A hemisphere is half of a sphere, so its volume is half of 4/3 pi r^3. @2; pi*r^2*h => The hemispherical roof adds volume, so add its volume to the volume of the cylinder. @3; 1/3*pi*r^2*h + 2/3*pi*r^3 => The cylinder holds pi r^2 h. The factor 1/3 belongs to a cone. @1

### Question
A grain silo is a cylinder with a hemispherical roof. The cylinder has a radius of [[r]] m and a height of [[h]] m, and the hemisphere has the same radius as the cylinder. Find the volume of the silo in cubic meters. Give an exact answer.

### Solution
0. [pre.geometry.composite-figures] Set up: the silo is a cylinder with half of a sphere on top, and the two pieces do not overlap, so the volume of the silo is the sum of the volumes of the two pieces.
1. [pre.geometry.volume-solids] Cylinder: \(V_1 = \pi r^2 h = \pi([[r]])^2([[h]]) = [[tex(pi*r^2*h)]]\).
   check: pi*r^2*h = (pi*r^2)*h
2. [pre.geometry.volume-solids] Hemisphere: half of a sphere, \(V_2 = \frac{1}{2}\left(\frac{4}{3}\pi r^3\right) = \frac{2}{3}\pi([[r]])^3 = [[tex(2/3*pi*r^3)]]\).
   check: 1/2*(4/3*pi*r^3) = 2/3*pi*r^3
3. [pre.geometry.composite-figures] Total: \(V = V_1 + V_2 = [[tex(pi*r^2*h + 2/3*pi*r^3)]]\) cubic meters.
   check: pi*r^2*h + 2*pi*r^3/3 = pi*r^2*h + 2/3*pi*r^3

<!-- tier 2: one lap of a running track -->
## Card calc1.0-6.comp.003
skill: pre.geometry.composite-figures
uses: pre.geometry.perimeter-circumference
difficulty: 2
answer-type: number
answer: 200 + 60*pi
wrong: 200 + 30*pi => The two semicircular ends together make one full circle, so both arcs are in the lap. @2; 320 + 60*pi => The ends of the rectangle are shared with the semicircles and lie inside the track, so they are not part of the lap. @1

### Question
A running track has the shape of a rectangle 100 m long and 60 m wide with a semicircle attached at each of the two 60 m ends. One lap runs along the outer edge of the track. Find the length of one lap in meters. Give an exact answer.

### Solution
0. [pre.geometry.composite-figures] Set up: a lap is the outer edge of the whole figure. It consists of the two long straight sides of the rectangle and the two semicircular arcs. The two ends of the rectangle are shared with the semicircles and lie inside the track, so they are not part of the lap.
1. [pre.geometry.perimeter-circumference] Curved part: the two semicircles together make one full circle with diameter 60 m, and its circumference is \(\pi d = 60\pi\) meters.
   check: 2*pi*30 = 60*pi
2. [pre.geometry.composite-figures] Lap: the straight sides are \(2(100) = 200\) m, so one lap is \(200 + 60\pi\) meters, which is about 388.5 m.
   check: 2*100 + 60*pi = 200 + 60*pi

<!-- tier 2: two cubes glued together, drop the hidden faces -->
## Card calc1.0-6.comp.004
skill: pre.geometry.composite-figures
uses: pre.geometry.surface-area-solids
difficulty: 2
answer-type: number
answer: 112
wrong: 120 => The face where the cubes touch is hidden on both cubes, so subtract it twice. @3; 116 => A patch of the top face of the large cube is covered as well as the bottom face of the small cube, so subtract both. @3

### Question
A cube with edges of 4 cm has a smaller cube with edges of 2 cm glued to the middle of its top face. Find the total exposed surface area of the solid in square centimeters.

### Solution
0. [pre.geometry.composite-figures] Set up: the exposed surface is all of the faces of both cubes except where they touch. The bottom face of the small cube is hidden, and an equal square patch of the top face of the large cube is covered.
1. [pre.geometry.surface-area-solids] Large cube: six faces of area \(4^2\), so \(S_1 = 6(4^2) = 96\) cm\(^2\).
   check: 6*4^2 = 96
2. [pre.geometry.surface-area-solids] Small cube: six faces of area \(2^2\), so \(S_2 = 6(2^2) = 24\) cm\(^2\).
   check: 6*2^2 = 24
3. [pre.geometry.composite-figures] Total: add the two surface areas and subtract the hidden patch twice, once from each cube, so \(S = 96 + 24 - 2(2^2) = 112\) square centimeters.
   check: 96 + 24 - 2*2^2 = 112

<!-- tier 3, template: the Norman window, area in terms of the width when the perimeter is fixed -->
## Card calc1.0-6.comp.t03
skill: pre.geometry.composite-figures
uses: pre.geometry.perimeter-circumference, alg.solve.linear, pre.geometry.area-plane-figures
difficulty: 3
answer-type: expression
vars: P = int(10, 40); x
domain: 0 < x < [[P/3]]
answer: P*x/2 - (1/2 + pi/8)*x^2
wrong: P*x/2 - (1 + pi/8)*x^2 => The top edge of the rectangle is shared with the semicircle, so it is not part of the perimeter. @2; P*x/2 - x^2/2 => That treats the window as a plain rectangle. The semicircle adds its arc to the perimeter and its area to the window. @1; P*x/2 - x^2/2 - 3*pi*x^2/8 => The arc of the semicircle is half of the circumference of the circle, not all of it. @1

### Question
A Norman window is a rectangle topped by a semicircle whose diameter is the top edge of the rectangle. The rectangle has width \(x\) ft and height \(h\) ft. The distance around the outside edge of the window is [[P]] ft. Write the area \(A\) of the window, in square feet, as a function of \(x\).

### Solution
0. [pre.geometry.composite-figures] Set up: the window is a rectangle plus a semicircle, so its area is the sum of the two areas. The height h of the rectangle depends on x through the perimeter, so find h in terms of x first.
1. [pre.geometry.perimeter-circumference] Arc: the semicircle has diameter x, so its arc is half of the circumference \(\pi x\), which is \(\frac{\pi x}{2}\).
   check: 1/2*(pi*x) = pi*x/2
2. [pre.geometry.composite-figures] Perimeter: the outside edge is the two vertical sides, the bottom and the arc. The top edge of the rectangle lies inside the window, so it is not counted. The perimeter equation says that twice the height, plus the width, plus the arc is [[P]].
3. [alg.solve.linear] Solve for \(h\): from \(2h + x + \frac{\pi x}{2} = [[P]]\), \(h = \frac{[[P]] - x - \pi x/2}{2}\).
   check: 2*((P - x - pi*x/2)/2) + x + pi*x/2 = P
4. [pre.geometry.area-plane-figures] Semicircle: the radius is \(\frac{x}{2}\), so its area is \(\frac{1}{2}\pi\left(\frac{x}{2}\right)^2 = \frac{\pi x^2}{8}\).
   check: 1/2*pi*(x/2)^2 = pi*x^2/8
5. [pre.geometry.composite-figures] Area: \(A = xh + \frac{\pi x^2}{8} = \frac{[[P]]x}{2} - \frac{x^2}{2} - \frac{\pi x^2}{4} + \frac{\pi x^2}{8} = \frac{[[P]]x}{2} - \left(\frac{1}{2} + \frac{\pi}{8}\right)x^2\).
   check: x*((P - x - pi*x/2)/2) + pi*x^2/8 = P*x/2 - (1/2 + pi/8)*x^2

<!-- tier 3: the surface area of a block with a hole drilled through it -->
## Card calc1.0-6.comp.005
skill: pre.geometry.composite-figures
uses: pre.geometry.surface-area-solids, pre.geometry.area-plane-figures
difficulty: 3
answer-type: number
answer: 392 + 12*pi
wrong: 392 + 28*pi => The two circular openings are cut out of the top and bottom faces, so their area is subtracted. @4; 392 - 8*pi => The inside wall of the hole is new surface, so it is added. @4; 392 + 20*pi => The two circular openings are cut out of the top and bottom faces, so their area is subtracted. @4

### Question
A metal block measures 12 cm by 8 cm by 5 cm. A cylindrical hole with a radius of 2 cm is drilled straight through the block, from the 12 cm by 8 cm top face to the bottom face, so the hole is 5 cm long. Find the total surface area of the block, including the inside wall of the hole, in square centimeters. Give an exact answer.

### Solution
0. [pre.geometry.composite-figures] Set up: drilling the hole takes a circle out of the top face and a circle out of the bottom face, and adds the curved inside wall of the hole. The new surface area is the surface area of the block, minus the two circles, plus the wall.
1. [pre.geometry.surface-area-solids] Block: \(S = 2(lw + lh + wh) = 2(12 \cdot 8 + 12 \cdot 5 + 8 \cdot 5) = 392\) cm\(^2\).
   check: 2*(12*8 + 12*5 + 8*5) = 392
2. [pre.geometry.surface-area-solids] Wall of the hole: a cylinder side with radius 2 and height 5, so \(2\pi r h = 2\pi(2)(5) = 20\pi\) cm\(^2\).
   check: 2*pi*2*5 = 20*pi
3. [pre.geometry.area-plane-figures] Circles removed: each opening has area \(\pi(2)^2 = 4\pi\), so the two openings remove \(8\pi\) cm\(^2\).
   check: 2*(pi*2^2) = 8*pi
4. [pre.geometry.composite-figures] Total: \(S = 392 - 8\pi + 20\pi = 392 + 12\pi\) square centimeters, which is about 429.7 cm\(^2\).
   check: 392 - 8*pi + 20*pi = 392 + 12*pi

<!-- ===================================================================== -->
<!-- pre.geometry.similar-triangles                                        -->
<!-- ===================================================================== -->

<!-- worked example: the height of a lamp from a shadow -->
## Card calc1.0-6.sim-example.001
kind: example
skill: pre.geometry.similar-triangles

### Question
A person 1.8 m tall stands 4.8 m from the base of a vertical lamp post. The lamp casts a shadow of the person on the level ground, and the shadow is 2.4 m long. How tall is the lamp post?

### Solution
0. [pre.geometry.similar-triangles] Set up: the lamp post and the person both stand straight up, and the light ray that just grazes the top of the person's head reaches the ground at the tip of the shadow. The large right triangle (post, ground, light ray) and the small right triangle (person, shadow, light ray) share the angle at the tip of the shadow, and each has a right angle, so they are similar. Corresponding sides of similar triangles are proportional.
1. [pre.geometry.similar-triangles] Bases: the base of the large triangle runs from the post to the tip of the shadow, \(4.8 + 2.4 = 7.2\) m, and the base of the small triangle is the shadow, 2.4 m.
   check: 4.8 + 2.4 = 7.2
2. [pre.geometry.similar-triangles] Proportion: height over base is the same in both triangles, so \(\frac{H}{7.2} = \frac{1.8}{2.4}\) and \(H = 7.2\cdot\frac{1.8}{2.4} = 5.4\) meters.
   check: 7.2*1.8/2.4 = 5.4

<!-- tier 1, template: the height of a tree from its shadow -->
## Card calc1.0-6.sim.t01
skill: pre.geometry.similar-triangles
difficulty: 1
answer-type: number
vars: p = int(2, 4); s = int(5, 8); m = int(3, 8)
let: S = s*m
answer: p*m
wrong: p + S - s => Similar triangles have proportional sides, not sides that differ by the same amount. @1; s*S/p => The ratio of height to shadow is the same for the pole and the tree, so the tree's height is its shadow times the pole's height divided by the pole's shadow. @1

### Question
A vertical pole [[p]] m tall casts a shadow [[s]] m long on level ground. At the same time of day, a tree casts a shadow [[S]] m long. Find the height of the tree in meters.

### Solution
0. [pre.geometry.similar-triangles] Set up: the sun's rays meet the ground at the same angle for the pole and for the tree, so the pole with its shadow and the tree with its shadow make similar right triangles, and corresponding sides are proportional.
1. [pre.geometry.similar-triangles] Proportion: height over shadow is the same for both, so \(\frac{h}{[[S]]} = \frac{[[p]]}{[[s]]}\) and \(h = [[S]]\cdot\frac{[[p]]}{[[s]]} = [[p*m]]\) meters.
   check: S*p/s = p*m

<!-- tier 1: the longest side of a similar triangle -->
## Card calc1.0-6.sim.001
skill: pre.geometry.similar-triangles
difficulty: 1
answer-type: number
answer: 20
wrong: 16 => Similar triangles have proportional sides, not sides that differ by the same amount. @1; 15 => The longest side of the second triangle corresponds to the longest side of the first, which is 12 cm. @1

### Question
A triangle has sides of 6 cm, 9 cm and 12 cm. A similar triangle has a shortest side of 10 cm. Find the length of its longest side in centimeters.

### Solution
0. [pre.geometry.similar-triangles] Set up: in similar triangles the shortest sides correspond, the longest sides correspond, and every pair of corresponding sides has the same ratio.
1. [pre.geometry.similar-triangles] Ratio and longest side: the ratio of corresponding sides is \(\frac{10}{6} = \frac{5}{3}\), so the longest side is \(12\cdot\frac{5}{3} = 20\) centimeters.
   check: 10/6 = 5/3
   check: 12*5/3 = 20

<!-- tier 1: which proportion fits the lamp post, select the single correct one -->
## Card calc1.0-6.sim.002
skill: pre.geometry.similar-triangles
difficulty: 1
answer-type: choice

### Question
A person 1.5 m tall stands 4 m from the base of a vertical lamp post and casts a shadow 2 m long on level ground. The lamp post has height \(H\). Which equation relates \(H\) to the other lengths by similar triangles?

### Choices
- [ ] \(\dfrac{H}{4} = \dfrac{1.5}{2}\)
- [ ] \(\dfrac{H}{2} = \dfrac{1.5}{4 + 2}\)
- [x] \(\dfrac{H}{4 + 2} = \dfrac{1.5}{2}\)
- [ ] \(\dfrac{H}{1.5} = \dfrac{4}{2}\)

### Solution
0. [pre.geometry.similar-triangles] Set up: the large triangle (post, ground, light ray) and the small triangle (person, shadow, light ray) are similar. The large triangle's base runs from the post to the tip of the shadow, so it is the distance to the person plus the shadow, and the small triangle's base is the shadow alone. Matching height over base in both triangles gives the equation.
1. [pre.geometry.similar-triangles] Correct equation: the large base is \(4 + 2 = 6\) m, so \(\frac{H}{6} = \frac{1.5}{2}\), which gives \(H = 4.5\) m.
   check: 6*1.5/2 = 4.5
2. [pre.geometry.similar-triangles] Wrong base: using \(\frac{H}{4}\) leaves out the shadow, and gives \(H = 3\), which is shorter than the lamp must be to reach the tip of the shadow.
   check: 4*1.5/2 = 3
3. [pre.geometry.similar-triangles] Heights and bases swapped: \(\frac{H}{2} = \frac{1.5}{4 + 2}\) pairs the height of the large triangle with the base of the small one, and gives \(H = 0.5\).
   check: 2*1.5/6 = 1/2
4. [pre.geometry.similar-triangles] Wrong base again: the ratio of the heights equals the ratio of the bases, \(\frac{4 + 2}{2}\), but \(\frac{H}{1.5} = \frac{4}{2}\) uses 4, which is not the base of either triangle, and gives \(H = 3\).
   check: 1.5*4/2 = 3

<!-- tier 2, template: the radius of the water surface in a conical tank -->
## Card calc1.0-6.sim.t02
skill: pre.geometry.similar-triangles
difficulty: 2
answer-type: expression
vars: R = int(2, 6); H = int(7, 14); h
domain: 0 < h < [[H]]
answer: R*h/H
wrong: H*h/R => The ratio of radius to depth is the same for the water and the tank, so the radius is the depth times the tank's radius divided by the tank's height. @1; R*h => The radius is the depth times the ratio R/H of the tank's radius to its height, so divide by the height as well. @1

### Question
A conical tank with its point down has a top radius of [[R]] m and a height of [[H]] m. Water in the tank has depth \(h\) m, and the water surface is a circle of radius \(r\) m. Write \(r\) as a function of \(h\).

### Solution
0. [pre.geometry.similar-triangles] Set up: a vertical slice through the axis of the tank shows the tank as a triangle and the water as a smaller triangle with the same point at the bottom. The two triangles are similar, so the ratio of radius to depth is the same for the water and for the tank.
1. [pre.geometry.similar-triangles] Proportion: \(\frac{r}{h} = \frac{[[R]]}{[[H]]}\), so \(r = [[tex(R*h/H)]]\).
   check: R/H*h = R*h/H

<!-- tier 2: the shadow of a person walking away from a lamp -->
## Card calc1.0-6.sim.003
skill: pre.geometry.similar-triangles
uses: alg.solve.linear
difficulty: 2
answer-type: expression
vars: x
domain: x > 0
answer: x/3
wrong: x/4 => The large triangle's base runs from the post to the tip of the shadow, so it is x + s, not x. @1; x/5 => Moving 1.5s to the left side means subtracting it, so 6s - 1.5s = 4.5s. @2

### Question
A lamp is on top of a vertical post 6 m high. A person 1.5 m tall walks away from the base of the post along level ground. When the person is \(x\) m from the base of the post, the person's shadow is \(s\) m long. Write \(s\) as a function of \(x\).

### Solution
0. [pre.geometry.similar-triangles] Set up: the large right triangle (post, ground, light ray) and the small right triangle (person, shadow, light ray) are similar. The large triangle's base runs from the post to the tip of the shadow, so it is the distance to the person plus the shadow, and the small triangle's base is the shadow alone.
1. [pre.geometry.similar-triangles] Proportion: height over base is the same in both triangles, so \(\frac{6}{x + s} = \frac{1.5}{s}\).
   check: 6/(x + x/3) = 1.5/(x/3)
2. [alg.solve.linear] Solve for \(s\): cross-multiplying gives \(6s = 1.5(x + s)\), so \(4.5s = 1.5x\) and \(s = \frac{x}{3}\).
   check: 1.5*(x + x/3) = 6*(x/3)
   check: 1.5*x/4.5 = x/3

<!-- tier 2: a line parallel to one side of a triangle -->
## Card calc1.0-6.sim.004
skill: pre.geometry.similar-triangles
difficulty: 2
answer-type: number
answer: 25/2
wrong: 15/2 => The side AB of the large triangle is AD + DB = 10 cm, and it corresponds to AD, not to DB. @1; 11 => Similar triangles have proportional sides, not sides that differ by the same amount. @1

### Question
In triangle ABC, point D is on side AB and point E is on side AC, and segment DE is parallel to side BC. AD = 4 cm, DB = 6 cm and DE = 5 cm. Find the length of BC in centimeters.

### Solution
0. [pre.geometry.similar-triangles] Set up: because DE is parallel to BC, the angles at D and B are equal and the angles at E and C are equal, and the triangles share the angle at A. So triangle ADE is similar to triangle ABC, with AD matching AB and DE matching BC.
1. [pre.geometry.similar-triangles] Whole side: \(AB = AD + DB = 4 + 6 = 10\) cm.
   check: 4 + 6 = 10
2. [pre.geometry.similar-triangles] Proportion: \(\frac{BC}{DE} = \frac{AB}{AD}\), so \(BC = 5\cdot\frac{10}{4} = \frac{25}{2}\) centimeters.
   check: 5*10/4 = 25/2

<!-- tier 3, template: the volume of water in a conical tank as a function of its depth -->
## Card calc1.0-6.sim.t03
skill: pre.geometry.similar-triangles
uses: pre.geometry.volume-solids
difficulty: 3
answer-type: expression
vars: R = int(2, 6); H = int(7, 14); h
domain: 0 < h < [[H]]
answer: pi*R^2*h^3/(3*H^2)
wrong: pi*R^2*h/3 => The radius of the water surface is not the radius of the tank. It grows with the depth, and similar triangles give r = [[R]]h/[[H]]. @1; pi*H^2*h^3/(3*R^2) => The ratio of radius to depth is the same for the water and the tank, so the radius is the depth times the tank's radius divided by the tank's height. @1; pi*R^2*h^3/H^2 => A cone holds one third of the cylinder with the same base and height, so the volume has a factor of 1/3. @2

### Question
A conical tank with its point down has a top radius of [[R]] m and a height of [[H]] m. Water in the tank has depth \(h\) m. Write the volume \(V\) of the water, in cubic meters, as a function of \(h\) alone.

### Solution
0. [pre.geometry.similar-triangles] Set up: the water forms a cone that is similar to the tank, because a vertical slice through the axis shows two triangles with the same point at the bottom. The volume formula needs the radius r of the water surface, so write r in terms of h first.
1. [pre.geometry.similar-triangles] Proportion: \(\frac{r}{h} = \frac{[[R]]}{[[H]]}\), so \(r = [[tex(R*h/H)]]\).
   check: R/H*h = R*h/H
2. [pre.geometry.volume-solids] Volume: \(V = \frac{1}{3}\pi r^2 h = \frac{1}{3}\pi\left([[tex(R*h/H)]]\right)^2 h = [[tex(pi*R^2*h^3/(3*H^2))]]\) cubic meters.
   check: 1/3*pi*(R*h/H)^2*h = pi*R^2*h^3/(3*H^2)

<!-- tier 3: a rectangle inside a right triangle -->
## Card calc1.0-6.sim.005
skill: pre.geometry.similar-triangles
uses: alg.solve.linear, pre.geometry.area-plane-figures
difficulty: 3
answer-type: expression
vars: x
domain: 0 < x < 12
answer: 8*x - 2*x^2/3
wrong: 18*x - 3*x^2/2 => Compare the same parts in both triangles: the short leg over the long leg, 8 over 12, not 12 over 8. @1; 8*x - x^2 => Similar triangles have proportional sides, not sides that differ by the same amount. @1; 8 - 2*x/3 => That is the height y. The area of the rectangle is x times y. @3

### Question
A right triangle has legs of 12 cm and 8 cm. A rectangle is placed inside the triangle so that one corner of the rectangle is at the right angle, two sides of the rectangle lie along the legs, and the opposite corner touches the hypotenuse. Let \(x\) cm be the length of the rectangle along the 12 cm leg and \(y\) cm its length along the 8 cm leg. Write the area \(A\) of the rectangle as a function of \(x\).

### Solution
0. [pre.geometry.similar-triangles] Set up: the part of the large triangle to the right of the rectangle is a smaller right triangle. It shares the angle at the end of the 12 cm leg with the large triangle, so the two are similar. Its horizontal leg is 12 minus x and its vertical leg is y.
1. [pre.geometry.similar-triangles] Proportion: vertical leg over horizontal leg is the same in both triangles, so \(\frac{y}{12 - x} = \frac{8}{12}\).
   check: (8 - 2*x/3)/(12 - x) = 8/12
2. [alg.solve.linear] Solve for \(y\): \(y = \frac{2}{3}(12 - x) = 8 - \frac{2x}{3}\).
   check: 2/3*(12 - x) = 8 - 2*x/3
3. [pre.geometry.area-plane-figures] Area: the rectangle has area base times height, so \(A = xy = x\left(8 - \frac{2x}{3}\right) = 8x - \frac{2x^2}{3}\).
   check: x*(8 - 2*x/3) = 8*x - 2*x^2/3

<!-- tier 3: the volume of water in a triangular trough -->
## Card calc1.0-6.sim.006
skill: pre.geometry.similar-triangles
uses: pre.geometry.area-plane-figures, pre.geometry.volume-solids
difficulty: 3
answer-type: expression
vars: h
domain: 0 < h < 0.8
answer: 3*h^2
wrong: 2.4*h => The width of the water surface depends on the depth. It is not the full top width of 1.2 m unless the trough is full. @1; 6*h^2 => The area of a triangle is one half of the base times the height. @2; 3*h^2/4 => The volume is the area of the cross-section times the length of the trough, 4 m. @3

### Question
A trough is 4 m long. Each end is an isosceles triangle with a top width of 1.2 m and a depth of 0.8 m, with its point at the bottom. Water in the trough has depth \(h\) m. Write the volume \(V\) of the water, in cubic meters, as a function of \(h\).

### Solution
0. [pre.geometry.similar-triangles] Set up: a cross-section of the water is a triangle with the same point at the bottom as the end of the trough, and it is similar to the end. So the width w of the water surface can be found from the depth h. The volume of water is then the area of this triangle times the length of the trough.
1. [pre.geometry.similar-triangles] Width: width over depth is the same for the water and for the end of the trough, so \(\frac{w}{h} = \frac{1.2}{0.8}\) and \(w = 1.5h\).
   check: 1.2/0.8*h = 1.5*h
2. [pre.geometry.area-plane-figures] Cross-section: the triangle has base w and height h, so its area is \(\frac{1}{2}wh = \frac{1}{2}(1.5h)(h) = 0.75h^2\).
   check: 1/2*(1.5*h)*h = 0.75*h^2
3. [pre.geometry.volume-solids] Volume: area of the cross-section times the length, \(V = 0.75h^2 \cdot 4 = 3h^2\) cubic meters.
   check: 0.75*h^2*4 = 3*h^2

<!-- ===================================================================== -->
<!-- pre.geometry.pythagorean                                              -->
<!-- ===================================================================== -->

<!-- worked example: the distance from a radar station to a plane -->
## Card calc1.0-6.pyth-example.001
kind: example
skill: pre.geometry.pythagorean

### Question
A small plane flies at a constant altitude of 4000 ft. At one moment the point on the ground directly below the plane is 3000 ft from a radar station. How far is the plane from the radar station at that moment?

### Solution
0. [pre.geometry.pythagorean] Set up: the radar station, the point on the ground directly below the plane and the plane are the corners of a right triangle. The altitude and the ground distance are the two legs, and the distance from the station to the plane is the hypotenuse, the side opposite the right angle.
1. [pre.geometry.pythagorean] Pythagoras: the square of the hypotenuse is the sum of the squares of the legs, so \(s^2 = 3000^2 + 4000^2 = 25{,}000{,}000\) and \(s = 5000\) feet.
   check: 3000^2 + 4000^2 = 25000000
   check: sqrt(25000000) = 5000

<!-- tier 1, template: the diagonal of a rectangular lot, a Pythagorean triple -->
## Card calc1.0-6.pyth.t01
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: number
vars: m = int(2, 4); n = int(1, 3)
require: m > n
let: u = m^2 - n^2; v = 2*m*n; w = m^2 + n^2
answer: w
wrong: u + v => That adds the two sides. The diagonal is the hypotenuse, so add the squares of the sides and take the square root. @1; w^2 => That is the square of the diagonal. Take the square root. @1

### Question
A rectangular lot is [[u]] m wide and [[v]] m long. A straight path runs along a diagonal of the lot, from one corner to the opposite corner. Find the length of the path in meters.

### Solution
0. [pre.geometry.pythagorean] Set up: the diagonal and the two sides form a right triangle, with the diagonal as the hypotenuse. The square of the hypotenuse is the sum of the squares of the legs.
1. [pre.geometry.pythagorean] Pythagoras: \(d = \sqrt{[[u]]^2 + [[v]]^2} = \sqrt{[[u^2]] + [[v^2]]} = [[w]]\) meters.
   check: sqrt(u^2 + v^2) = w

<!-- tier 1: is it a right triangle? -->
## Card calc1.0-6.pyth.001
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: truefalse
answer: true

### Question
True or false: a triangle with sides of 9 cm, 12 cm and 15 cm is a right triangle.

### Solution
0. [pre.geometry.pythagorean] Set up: if the square of the longest side equals the sum of the squares of the other two sides, then the triangle has a right angle opposite the longest side. This is the converse of the Pythagorean theorem.
1. [pre.geometry.pythagorean] Check: \(9^2 + 12^2 = 81 + 144 = 225\), and \(15^2 = 225\), so the squares match and the triangle is a right triangle.
   check: 9^2 + 12^2 = 15^2

<!-- tier 1: how high does a ladder reach -->
## Card calc1.0-6.pyth.002
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: number
answer: 8
wrong: 4 => The ladder is the hypotenuse of a right triangle, so the other two sides are not found by subtracting lengths. Subtract the squares. @1; sqrt(136) => The ladder is the longest side. Subtract the square of the known leg from the square of the ladder. @1

### Question
A 10-ft ladder leans against a vertical wall, and its foot is on level ground 6 ft from the wall. How high up the wall does the top of the ladder reach, in feet?

### Solution
0. [pre.geometry.pythagorean] Set up: the ladder, the wall and the ground form a right triangle with the ladder as the hypotenuse. The square of the hypotenuse is the sum of the squares of the legs, so a leg is found by subtracting the square of the other leg from the square of the hypotenuse.
1. [pre.geometry.pythagorean] Pythagoras: \(h = \sqrt{10^2 - 6^2} = \sqrt{64} = 8\) feet.
   check: sqrt(10^2 - 6^2) = 8

<!-- tier 2, template: the height of a ladder as a function of the distance of its foot from the wall -->
## Card calc1.0-6.pyth.t02
skill: pre.geometry.pythagorean
difficulty: 2
answer-type: expression
vars: L = int(8, 30); x
domain: 0 < x < [[L]]
answer: sqrt(L^2 - x^2)
wrong: L - x => The ladder, the wall and the ground form a right triangle, so the height is not found by subtracting lengths. Subtract the squares. @1; sqrt(L^2 + x^2) => The ladder is the hypotenuse, so the square of the height is the square of the ladder minus the square of x. @1; L^2 - x^2 => That is the square of the height. Take the square root. @1

### Question
A ladder [[L]] ft long leans against a vertical wall on level ground. The foot of the ladder is \(x\) ft from the wall, and the top of the ladder is \(y\) ft above the ground. Write \(y\) as a function of \(x\).

### Solution
0. [pre.geometry.pythagorean] Set up: the ladder, the wall and the ground form a right triangle with the ladder as the hypotenuse, so the squares of the two legs add up to the square of the ladder.
1. [pre.geometry.pythagorean] Pythagoras: \(x^2 + y^2 = [[L^2]]\), so \(y^2 = [[L^2]] - x^2\) and, since \(y > 0\), \(y = \sqrt{[[L^2]] - x^2}\).
   check: sqrt(L^2 - x^2)^2 + x^2 = L^2
   check: (L^2 - x^2)^(1/2) = sqrt(L^2 - x^2)

<!-- tier 2: the longest rod that fits in a box -->
## Card calc1.0-6.pyth.003
skill: pre.geometry.pythagorean
difficulty: 2
answer-type: number
answer: 13
wrong: 5 => That is the diagonal of the floor only. The rod also rises 12 ft, so use the floor diagonal and the height as the legs of a second right triangle. @2; 19 => The rod is a diagonal, not a path along the edges. Use the Pythagorean theorem. @1

### Question
A closed box is 3 ft wide, 4 ft long and 12 ft tall. Find the length of the longest straight rod that fits inside the box, in feet.

### Solution
0. [pre.geometry.pythagorean] Set up: the longest rod runs from a bottom corner to the opposite top corner. First find the diagonal of the floor, a right triangle with legs 3 and 4. Then use that diagonal and the height as the legs of a second right triangle, whose hypotenuse is the rod.
1. [pre.geometry.pythagorean] Floor diagonal: \(\sqrt{3^2 + 4^2} = 5\) feet.
   check: sqrt(3^2 + 4^2) = 5
2. [pre.geometry.pythagorean] Rod: \(\sqrt{5^2 + 12^2} = \sqrt{169} = 13\) feet.
   check: sqrt(5^2 + 12^2) = 13

<!-- tier 2: the area of an isosceles triangle from its sides -->
## Card calc1.0-6.pyth.004
skill: pre.geometry.pythagorean
uses: pre.geometry.area-plane-figures
difficulty: 2
answer-type: number
answer: 60
wrong: 65 => The height is the perpendicular distance from the apex to the base, not the slanted side of 13 cm. @1; 120 => The area of a triangle is one half of the base times the height. @2

### Question
An isosceles triangle has two equal sides of 13 cm and a base of 10 cm. Find its area in square centimeters.

### Solution
0. [pre.geometry.pythagorean] Set up: the height from the apex to the base splits the isosceles triangle into two congruent right triangles, and it meets the base at its midpoint. Each right triangle has the 13 cm side as its hypotenuse and half of the base as one leg.
1. [pre.geometry.pythagorean] Height: \(h = \sqrt{13^2 - 5^2} = \sqrt{144} = 12\) cm.
   check: sqrt(13^2 - 5^2) = 12
2. [pre.geometry.area-plane-figures] Area: \(A = \frac{1}{2}bh = \frac{1}{2}(10)(12) = 60\) square centimeters.
   check: 1/2*10*12 = 60

<!-- tier 3, template: the time for a lifeguard to run along the beach and then swim -->
## Card calc1.0-6.pyth.t03
skill: pre.geometry.pythagorean
difficulty: 3
answer-type: expression
vars: L = int(60, 200); d = int(20, 60); r = int(4, 7); s = int(1, 3); x
domain: 0 < x < [[L]]
answer: x/r + sqrt((L - x)^2 + d^2)/s
wrong: x/r + sqrt(x^2 + d^2)/s => The horizontal leg of the swimming triangle is the distance still left along the beach, which is [[L]] - x, not x. @1; x/r + ((L - x)^2 + d^2)/s => The swimming distance is the hypotenuse, the square root of the sum of the squares of the legs. @1; x*r + sqrt((L - x)^2 + d^2)*s => Time is distance divided by speed, not distance times speed. @2

### Question
A lifeguard stands on a straight beach. A swimmer in trouble is in the water [[d]] m from the shore, and the point on the shore nearest the swimmer is [[L]] m along the beach from the lifeguard. The lifeguard runs along the beach at [[r]] m/s for \(x\) meters, then swims straight to the swimmer at [[s]] m/s. Write the total time \(T\), in seconds, as a function of \(x\).

### Solution
0. [pre.geometry.pythagorean] Set up: after running x meters along the beach, the lifeguard swims along the hypotenuse of a right triangle. Its legs are the distance still left along the beach and the distance of the swimmer from the shore. For each part of the trip, time is distance divided by speed.
1. [pre.geometry.pythagorean] Swimming distance: the legs are \([[L]] - x\) and \([[d]]\), so the swimming distance is \(\sqrt{([[L]] - x)^2 + [[d^2]]}\) meters.
   check: sqrt((L - x)^2 + d^2)^2 = (L - x)^2 + d^2
2. [pre.geometry.pythagorean] Total time: running takes \(\frac{x}{[[r]]}\) seconds, and swimming takes the swimming distance divided by [[s]] m/s, so \(T = [[tex(x/r + sqrt((L - x)^2 + d^2)/s)]]\).
   check: x/r + sqrt((L - x)^2 + d^2)/s = x/r + sqrt(d^2 + (L - x)^2)/s

<!-- tier 3: how far the foot of a ladder moves when its top slips -->
## Card calc1.0-6.pyth.005
skill: pre.geometry.pythagorean
difficulty: 3
answer-type: number
answer: 2*sqrt(26) - 9
wrong: 1 => The foot of the ladder does not move the same distance as the top. Find the distance of the foot from the wall before and after the slip. @3; 2*sqrt(26) => That is the new distance of the foot from the wall. The question asks how far the foot moved, so subtract the old distance. @3

### Question
A 15-ft ladder leans against a vertical wall with its top 12 ft above the level ground. The top of the ladder slips down 1 ft along the wall, and the foot slides away from the wall. How far does the foot of the ladder move, in feet? Give an exact answer.

### Solution
0. [pre.geometry.pythagorean] Set up: the ladder is the hypotenuse of a right triangle both before and after it slips. Find the distance of the foot from the wall in each position, and then subtract.
1. [pre.geometry.pythagorean] Before: the top is 12 ft up, so the foot is \(\sqrt{15^2 - 12^2} = 9\) ft from the wall.
   check: sqrt(15^2 - 12^2) = 9
2. [pre.geometry.pythagorean] After: the top is 11 ft up, so the foot is \(\sqrt{15^2 - 11^2} = \sqrt{104} = 2\sqrt{26}\) ft from the wall.
   check: sqrt(15^2 - 11^2) = 2*sqrt(26)
3. [pre.geometry.pythagorean] Move: the foot moves \(2\sqrt{26} - 9\) feet, which is about 1.2 ft.
   check: sqrt(15^2 - 11^2) - sqrt(15^2 - 12^2) = 2*sqrt(26) - 9

<!-- ===================================================================== -->
<!-- Flashcards: one definition or formula per card, situation on the front -->
<!-- ===================================================================== -->

<!-- ---------- area of plane figures ---------- -->

## Card calc1.0-6.fc-area.001
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of a triangle with base \(b\) and height \(h\)

### Back
\[ A = \frac{1}{2}\,b\,h \]

\(b\) is the length of the side chosen as the base. \(h\) is the perpendicular distance from the opposite corner to the line that contains the base, so it is not the length of a slanted side.

In calculus: a triangle whose base or height changes is a common area function to differentiate in related-rates and optimization problems.

## Card calc1.0-6.fc-area.002
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of a parallelogram with base \(b\) and height \(h\)

### Back
\[ A = b\,h \]

\(b\) is the length of one side chosen as the base. \(h\) is the perpendicular distance between that side and the parallel side opposite it, not the length of the slanted side. For a rectangle with length \(l\) and width \(w\), the height is the other side, so \(A = lw\).

In calculus: the rectangle is the area you maximize in fence and inscribed-rectangle problems, and the piece that a Riemann sum adds up.

## Card calc1.0-6.fc-area.003
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of a trapezoid with parallel sides \(a\) and \(b\) and height \(h\)

### Back
\[ A = \frac{1}{2}\,(a + b)\,h \]

\(a\) and \(b\) are the lengths of the two parallel sides, and \(h\) is the perpendicular distance between them. This is the average of the parallel sides times the height.

In calculus: the trapezoid rule adds up trapezoid areas, and trapezoids appear as the cross-section of a trough or a canal.

## Card calc1.0-6.fc-area.004
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of a circle with radius \(r\)

### Back
\[ A = \pi r^2 \]

\(r\) is the radius, the distance from the center to any point on the circle. In terms of the diameter \(d = 2r\), this is \(A = \frac{\pi d^2}{4}\).

In calculus: a circle that grows, such as a ripple or a spreading spill, is a basic related-rates setup, with \(\frac{dA}{dt} = 2\pi r\,\frac{dr}{dt}\).

## Card calc1.0-6.fc-area.005
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of an ellipse with semi-axes \(a\) and \(b\)

### Back
\[ A = \pi a b \]

\(a\) and \(b\) are the semi-axes: half of the longest width and half of the shortest width of the ellipse. When \(a = b = r\) the ellipse is a circle and the formula gives \(\pi r^2\).

In calculus: the region inside \(\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1\) has area \(\pi a b\), which is a standard check for an area integral.

## Card calc1.0-6.fc-area.006
kind: flashcard
skill: pre.geometry.area-plane-figures

### Front
Area of a triangle with two sides \(a\) and \(b\) and the angle \(\theta\) between them

### Back
\[ A = \frac{1}{2}\,a\,b\,\sin\theta \]

\(a\) and \(b\) are the lengths of the two sides, and \(\theta\) is the angle between those two sides, not an angle opposite one of them. When \(\theta = 90^\circ\) this is \(\frac{1}{2}ab\).

In calculus: the area of a triangle with a moving angle, such as a triangle with two fixed sides, is maximized or differentiated in optimization and related-rates problems.

<!-- ---------- perimeter and circumference ---------- -->

## Card calc1.0-6.fc-perim.001
kind: flashcard
skill: pre.geometry.perimeter-circumference

### Front
Circumference of a circle with radius \(r\)

### Back
\[ C = 2\pi r \]

\(r\) is the radius. In terms of the diameter \(d = 2r\), this is \(C = \pi d\).

In calculus: the circumference is the rate at which the area of a circle grows with its radius, \(\frac{d}{dr}(\pi r^2) = 2\pi r\), and a circular arc is part of the perimeter constraint in a Norman-window problem.

## Card calc1.0-6.fc-perim.002
kind: flashcard
skill: pre.geometry.perimeter-circumference

### Front
Perimeter of a rectangle with length \(l\) and width \(w\)

### Back
\[ P = 2l + 2w \]

\(l\) and \(w\) are the lengths of two neighboring sides. The perimeter is the distance all the way around: two lengths and two widths.

In calculus: a fixed amount of fencing gives the constraint \(2l + 2w = P\), which is how an optimization problem ties the two sides together.

<!-- ---------- volume of solids ---------- -->

## Card calc1.0-6.fc-vol.001
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a rectangular box with length \(l\), width \(w\) and height \(h\)

### Back
\[ V = l\,w\,h \]

\(l\), \(w\) and \(h\) are the lengths of the three edges that meet at a corner.

In calculus: box problems, such as a box with a square base or an open box cut from a sheet, write \(V\) in terms of one variable before differentiating.

## Card calc1.0-6.fc-vol.002
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a right circular cylinder with radius \(r\) and height \(h\)

### Back
\[ V = \pi r^2 h \]

\(r\) is the radius of the circular base and \(h\) is the height, so this is the area of the base times the height.

In calculus: for a can or a tank with a fixed volume, \(h = \frac{V}{\pi r^2}\) lets you write the surface area in terms of \(r\) alone.

## Card calc1.0-6.fc-vol.003
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a right circular cone with base radius \(r\) and vertical height \(h\)

### Back
\[ V = \frac{1}{3}\,\pi r^2 h \]

\(r\) is the radius of the circular base. \(h\) is the vertical height from the base straight up to the point, not the slant height. A cone holds one third of the cylinder with the same base and height.

In calculus: conical tanks and sand piles are the standard related-rates volumes, where \(r\) is first rewritten in terms of \(h\).

## Card calc1.0-6.fc-vol.004
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a sphere with radius \(r\)

### Back
\[ V = \frac{4}{3}\,\pi r^3 \]

\(r\) is the radius, the distance from the center to the surface. A hemisphere has half of this volume, \(\frac{2}{3}\pi r^3\).

In calculus: an inflating balloon or a melting snowball gives \(\frac{dV}{dt} = 4\pi r^2\,\frac{dr}{dt}\).

## Card calc1.0-6.fc-vol.005
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a pyramid with base area \(B\) and height \(h\)

### Back
\[ V = \frac{1}{3}\,B\,h \]

\(B\) is the area of the base, which can be any polygon, and \(h\) is the perpendicular distance from the base to the top point. A pyramid holds one third of the prism with the same base and height.

In calculus: a square pyramid with base side \(x\) has \(V = \frac{1}{3}x^2 h\), which appears in related-rates and slicing problems.

## Card calc1.0-6.fc-vol.006
kind: flashcard
skill: pre.geometry.volume-solids

### Front
Volume of a solid with the same cross-section of area \(B\) along its whole length \(h\), such as a prism or a cylinder

### Back
\[ V = B\,h \]

\(B\) is the area of the cross-section, perpendicular to the length, and \(h\) is the length along which the cross-section stays the same.

In calculus: a trough, a tunnel or a thin slab of thickness \(dx\) has volume equal to its cross-sectional area times its length, which is the idea behind volume by slicing.

<!-- ---------- surface area of solids ---------- -->

## Card calc1.0-6.fc-surf.001
kind: flashcard
skill: pre.geometry.surface-area-solids

### Front
Surface area of a sphere with radius \(r\)

### Back
\[ S = 4\pi r^2 \]

\(r\) is the radius. This is four times the area of a flat circle with the same radius.

In calculus: it is the derivative of the volume of a sphere with respect to the radius, \(\frac{d}{dr}\left(\frac{4}{3}\pi r^3\right) = 4\pi r^2\), and it appears in rate problems for an inflating balloon.

## Card calc1.0-6.fc-surf.002
kind: flashcard
skill: pre.geometry.surface-area-solids

### Front
Total surface area of a closed cylinder with radius \(r\) and height \(h\)

### Back
\[ S = 2\pi r^2 + 2\pi r h \]

\(r\) is the radius and \(h\) is the height. The term \(2\pi r^2\) is the area of the two circular ends, and \(2\pi r h\) is the area of the curved side.

In calculus: minimizing the metal in a can with a fixed volume starts from this formula, after \(h\) is written in terms of \(r\).

## Card calc1.0-6.fc-surf.003
kind: flashcard
skill: pre.geometry.surface-area-solids

### Front
Area of the curved side of a cylinder with radius \(r\) and height \(h\)

### Back
\[ S = 2\pi r h \]

\(r\) is the radius and \(h\) is the height. Unrolled, the curved side is a rectangle as wide as the circumference \(2\pi r\) and as tall as \(h\).

In calculus: open-top tanks, pipes and tubes use the curved side alone, without the circular ends.

## Card calc1.0-6.fc-surf.004
kind: flashcard
skill: pre.geometry.surface-area-solids

### Front
Area of the curved surface of a right circular cone with base radius \(r\) and slant height \(s\)

### Back
\[ S = \pi r s \]

\(r\) is the radius of the base. \(s\) is the slant height, the distance along the surface from the rim to the point, and it equals \(\sqrt{r^2 + h^2}\) when \(h\) is the vertical height. The base is not included.

In calculus: paper cones, funnels and cones of minimum surface area need this formula and the slant height.

## Card calc1.0-6.fc-surf.005
kind: flashcard
skill: pre.geometry.surface-area-solids

### Front
Total surface area of a closed rectangular box with length \(l\), width \(w\) and height \(h\)

### Back
\[ S = 2(lw + lh + wh) \]

\(l\), \(w\) and \(h\) are the lengths of the three edges at a corner. The box has three pairs of equal faces, and each pair adds \(2\) times the area of one face.

In calculus: boxes with a fixed volume and the least surface area (or the least material) are standard optimization problems.

<!-- ---------- arc length and sector area ---------- -->

## Card calc1.0-6.fc-arc.001
kind: flashcard
skill: pre.geometry.arc-sector

### Front
Length of an arc of a circle with radius \(r\) and central angle \(\theta\) in radians

### Back
\[ s = r\,\theta \]

\(r\) is the radius and \(\theta\) is the central angle in radians. One radian is the angle whose arc is as long as the radius, so a full turn of \(2\pi\) radians gives the whole circumference \(2\pi r\).

In calculus: the speed of a point moving around a circle is \(\frac{ds}{dt} = r\,\frac{d\theta}{dt}\), which links a changing angle to a changing distance in related-rates problems.

## Card calc1.0-6.fc-arc.002
kind: flashcard
skill: pre.geometry.arc-sector

### Front
Area of a sector of a circle with radius \(r\) and central angle \(\theta\) in radians

### Back
\[ A = \frac{1}{2}\,r^2\,\theta \]

\(r\) is the radius and \(\theta\) is the central angle in radians. The sector is the fraction \(\frac{\theta}{2\pi}\) of the whole circle, so its area is that fraction of \(\pi r^2\).

In calculus: the area of a fan, a slice or a sector with a fixed perimeter is written in terms of \(r\) or \(\theta\) in optimization problems, and a changing \(\theta\) gives a related-rates problem.

<!-- ---------- angle relationships ---------- -->

## Card calc1.0-6.fc-angle.001
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Sum of the angles of a triangle

### Back
- The three interior angles of any triangle
- add up to \(180^\circ\), which is \(\pi\) radians
- In calculus: it gives the third angle in a figure, so a trig ratio or the law of cosines can be used in a related-rates problem

## Card calc1.0-6.fc-angle.002
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Complementary angles

### Back
- Two angles whose measures add up to \(90^\circ\), which is \(\frac{\pi}{2}\) radians
- Each angle is the complement of the other
- In calculus: the angle a ladder makes with the wall and the angle it makes with the ground are complementary, so one is \(\frac{\pi}{2}\) minus the other

## Card calc1.0-6.fc-angle.003
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Supplementary angles

### Back
- Two angles whose measures add up to \(180^\circ\), which is \(\pi\) radians
- Two angles that together make a straight line are supplementary
- In calculus: supplementary angles have the same sine, \(\sin(\pi - \theta) = \sin\theta\), so \(A = \frac{1}{2}ab\sin\theta\) gives the same area for an angle and for its supplement

## Card calc1.0-6.fc-angle.004
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Two straight lines cross and form four angles: how are the angles related?

### Back
- Opposite angles (vertical angles) are equal
- Neighboring angles add up to \(180^\circ\)
- In calculus: when two roads, rods or sight lines cross in a diagram, one known angle gives all four, so the angle in a trig ratio or in the law of cosines can be found

## Card calc1.0-6.fc-angle.005
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
A line crosses two parallel lines: how are the angles formed related?

### Back
- Alternate interior angles are equal, and so are corresponding angles
- Same-side interior angles add up to \(180^\circ\)
- In calculus: this is why an angle of elevation seen from one point equals the angle of depression seen from the other

## Card calc1.0-6.fc-angle.006
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Angles of an isosceles triangle

### Back
- In a triangle, the angles opposite equal sides are equal
- These are the base angles of an isosceles triangle
- Conversely, equal angles lie opposite equal sides, so an equilateral triangle has three angles of \(60^\circ\)
- In calculus: an isosceles triangle with equal sides \(L\) and base angle \(\theta\) has height \(L\sin\theta\) and base \(2L\cos\theta\), a standard setup for maximizing an area

## Card calc1.0-6.fc-angle.007
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Sum of the interior angles of a polygon with \(n\) sides

### Back
\[ S = (n - 2)\cdot 180^\circ \]

\(n\) is the number of sides of a polygon that does not cross itself. The diagonals from one corner cut a convex polygon into \(n - 2\) triangles, and each triangle has angles that add up to \(180^\circ\). Each angle of a regular polygon is \(\frac{(n - 2)\cdot 180^\circ}{n}\).

In calculus: regular polygons with more and more sides are used to approximate a circle, which is the first example of a limit of areas.

## Card calc1.0-6.fc-angle.008
kind: flashcard
skill: pre.geometry.angle-relationships

### Front
Angle of elevation of a point, seen from an observer

### Back
- The angle between the horizontal line through the observer's eye and the line of sight up to the point
- It is measured upward from the horizontal, not from the vertical
- The angle of depression is the same angle measured downward, and the two are equal for the two ends of one line of sight, because they are alternate interior angles
- In calculus: for a camera that follows a rising rocket or a kite, \(\tan\theta\) is the height divided by the horizontal distance, which links \(\frac{d\theta}{dt}\) to the rate at which the height changes

<!-- ---------- special right triangles ---------- -->

## Card calc1.0-6.fc-special.001
kind: flashcard
skill: pre.geometry.special-right-triangles

### Front
Sides of a right triangle with two equal legs of length \(a\)

### Back
- Angles: \(45^\circ\), \(45^\circ\), \(90^\circ\)
- Legs: \(a\) and \(a\)
- Hypotenuse: \(a\sqrt{2}\), so the sides are in the ratio \(1 : 1 : \sqrt{2}\)

In calculus: this gives the exact values \(\sin\frac{\pi}{4} = \cos\frac{\pi}{4} = \frac{1}{\sqrt{2}}\) and the diagonal \(s\sqrt{2}\) of a square with side \(s\).

## Card calc1.0-6.fc-special.002
kind: flashcard
skill: pre.geometry.special-right-triangles

### Front
Sides of a 30-60-90 triangle whose shortest side has length \(a\)

### Back
- The shortest side \(a\) is opposite the \(30^\circ\) angle
- The longer leg is \(a\sqrt{3}\), opposite the \(60^\circ\) angle
- The hypotenuse is \(2a\), so the sides are in the ratio \(1 : \sqrt{3} : 2\)

In calculus: this gives the exact values of sine, cosine and tangent at \(\frac{\pi}{6}\) and \(\frac{\pi}{3}\).

## Card calc1.0-6.fc-special.003
kind: flashcard
skill: pre.geometry.special-right-triangles

### Front
Height of an equilateral triangle with side \(s\)

### Back
\[ h = \frac{\sqrt{3}}{2}\,s \]

\(s\) is the length of each side. The height splits the triangle into two 30-60-90 triangles with hypotenuse \(s\) and shortest side \(\frac{s}{2}\), so the height is the longer leg, \(\frac{s}{2}\sqrt{3}\).

In calculus: equilateral triangles appear as cross-sections of solids and as shapes to optimize, and the height is needed for their area.

## Card calc1.0-6.fc-special.004
kind: flashcard
skill: pre.geometry.special-right-triangles

### Front
Area of an equilateral triangle with side \(s\)

### Back
\[ A = \frac{\sqrt{3}}{4}\,s^2 \]

\(s\) is the length of each side. This is half of the base \(s\) times the height \(\frac{\sqrt{3}}{2}s\).

In calculus: a solid whose cross-sections are equilateral triangles has cross-sectional area \(\frac{\sqrt{3}}{4}s^2\), where \(s\) may depend on \(x\).

<!-- ---------- distance formula and the circle ---------- -->

## Card calc1.0-6.fc-dist.001
kind: flashcard
skill: pre.geometry.distance-formula

### Front
Distance between the points \((x_1, y_1)\) and \((x_2, y_2)\)

### Back
\[ d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2} \]

The horizontal difference \(x_2 - x_1\) and the vertical difference \(y_2 - y_1\) are the legs of a right triangle, and \(d\) is its hypotenuse. The order of the points does not matter, because the differences are squared.

In calculus: the distance from a fixed point to a point \((x, f(x))\) on a curve is the function to minimize in closest-point problems.

## Card calc1.0-6.fc-dist.002
kind: flashcard
skill: pre.geometry.distance-formula

### Front
Equation of the circle with center \((h, k)\) and radius \(r\)

### Back
\[ (x - h)^2 + (y - k)^2 = r^2 \]

A point \((x, y)\) is on the circle when its distance from the center \((h, k)\) is \(r\), and the equation says that the squared distance equals \(r^2\). With the center at the origin it is \(x^2 + y^2 = r^2\).

In calculus: implicit differentiation and related rates often start from \(x^2 + y^2 = r^2\), and solving for \(y\) gives the upper half \(y = \sqrt{r^2 - x^2}\).

<!-- ---------- law of cosines ---------- -->

## Card calc1.0-6.fc-cos.001
kind: flashcard
skill: pre.geometry.law-of-cosines

### Front
Law of cosines: the square of the side \(c\) opposite the angle \(C\), in a triangle whose other two sides are \(a\) and \(b\)

### Back
\[ c^2 = a^2 + b^2 - 2ab\cos C \]

\(a\) and \(b\) are the two sides that meet at the angle \(C\), and \(c\) is the side opposite \(C\).

In calculus: the distance between two objects that move along two lines at a fixed angle, or at a changing angle \(\theta(t)\), is found with the law of cosines in related-rates problems.

## Card calc1.0-6.fc-cos.002
kind: flashcard
skill: pre.geometry.law-of-cosines

### Front
When does the law of cosines reduce to the Pythagorean theorem?

### Back
- When the angle \(C\) between the sides \(a\) and \(b\) is \(90^\circ\)
- Then \(\cos C = 0\)
- So \(c^2 = a^2 + b^2\)
- In calculus: it is a quick check on a distance formula built from the law of cosines, which must reduce to \(\sqrt{a^2 + b^2}\) at a right angle

<!-- ---------- composite figures ---------- -->

## Card calc1.0-6.fc-comp.001
kind: flashcard
skill: pre.geometry.composite-figures

### Front
Area or volume of a figure made of several simple pieces

### Back
- Split the figure into pieces whose formulas you know
- Add the areas (or volumes) of the pieces
- If a piece is cut out, such as a hole, subtract it
- In calculus: a window, a silo or a track is split into a rectangle and a half circle, or a cylinder and a half sphere, before its area or volume is written in one variable

## Card calc1.0-6.fc-comp.002
kind: flashcard
skill: pre.geometry.composite-figures

### Front
Perimeter of a figure made of several pieces: which edges count?

### Back
- Only the outside edge counts
- An edge shared by two joined pieces is inside the figure, so leave it out
- A curved edge counts by its arc length, and a semicircle is half of a circumference
- In calculus: the perimeter of a window or a track is the constraint in an optimization problem, so a counted shared edge changes the answer

## Card calc1.0-6.fc-comp.003
kind: flashcard
skill: pre.geometry.composite-figures

### Front
Surface area of a solid made of two solids joined at a face

### Back
- Only the exposed surface counts
- Add the surface areas of the two solids
- Subtract the area of the joined region twice, once from each solid
- In calculus: the paint or metal needed for a capsule, a silo or a tank with a cap is an exposed-surface area, which is what a minimization problem asks for

## Card calc1.0-6.fc-comp.004
kind: flashcard
skill: pre.geometry.composite-figures

### Front
Perimeter of a Norman window, the distance around its outside edge: a rectangle of width \(w\) and height \(h\) with a semicircle on its top edge

### Back
\[ P = 2h + w + \frac{\pi w}{2} \]

The outside edge has two vertical sides \(2h\), the bottom \(w\), and the semicircular arc, which is half of the circumference \(\pi w\) of a circle with diameter \(w\). The top edge of the rectangle is inside the window, so it is left out.

In calculus: with the perimeter fixed, maximizing the area of the window is a classic optimization problem.

## Card calc1.0-6.fc-comp.005
kind: flashcard
skill: pre.geometry.composite-figures

### Front
Area of a Norman window: a rectangle of width \(w\) and height \(h\) with a semicircle on its top edge

### Back
\[ A = w\,h + \frac{\pi w^2}{8} \]

The rectangle has area \(wh\). The semicircle has radius \(\frac{w}{2}\), so its area is \(\frac{1}{2}\pi\left(\frac{w}{2}\right)^2 = \frac{\pi w^2}{8}\).

In calculus: this is the quantity maximized in the Norman-window problem, after \(h\) is found from the perimeter.

<!-- ---------- Pythagorean theorem ---------- -->

## Card calc1.0-6.fc-pyth.001
kind: flashcard
skill: pre.geometry.pythagorean

### Front
Pythagorean theorem: the hypotenuse \(c\) of a right triangle with legs \(a\) and \(b\)

### Back
\[ a^2 + b^2 = c^2, \qquad c = \sqrt{a^2 + b^2} \]

\(a\) and \(b\) are the legs, the two sides next to the right angle. \(c\) is the hypotenuse, the side opposite the right angle and the longest side. To find a leg, use \(a = \sqrt{c^2 - b^2}\).

In calculus: the distance \(s = \sqrt{x^2 + y^2}\) between two moving objects, and ladder and kite problems, are the starting point of many related-rates problems.

## Card calc1.0-6.fc-pyth.002
kind: flashcard
skill: pre.geometry.pythagorean

### Front
Converse of the Pythagorean theorem

### Back
- Suppose the three sides of a triangle satisfy \(a^2 + b^2 = c^2\)
- Then the triangle is a right triangle
- The right angle is opposite the side \(c\)
- In calculus: it shows that a triangle with sides such as \(5, 12, 13\) has a right angle, so the Pythagorean theorem and the trig ratios can be used in a related-rates diagram

## Card calc1.0-6.fc-pyth.003
kind: flashcard
skill: pre.geometry.pythagorean

### Front
Common Pythagorean triples

### Back
- \(3, 4, 5\) and \(5, 12, 13\)
- \(8, 15, 17\) and \(7, 24, 25\)
- Multiples of a triple also work, such as \(6, 8, 10\)

In calculus: choosing a triple makes the lengths in a related-rates setup whole numbers.

## Card calc1.0-6.fc-pyth.004
kind: flashcard
skill: pre.geometry.pythagorean

### Front
Length of the diagonal of a rectangle with length \(l\) and width \(w\)

### Back
\[ d = \sqrt{l^2 + w^2} \]

The diagonal is the hypotenuse of a right triangle whose legs are the two sides. For a square with side \(s\) this is \(s\sqrt{2}\).

In calculus: the diagonal of a rectangle whose sides change with time is a typical related-rates distance.

## Card calc1.0-6.fc-pyth.005
kind: flashcard
skill: pre.geometry.pythagorean

### Front
Length of the longest diagonal of a rectangular box with edges \(l\), \(w\) and \(h\)

### Back
\[ d = \sqrt{l^2 + w^2 + h^2} \]

Use the theorem twice: the diagonal of the floor is \(\sqrt{l^2 + w^2}\), and it is a leg of a right triangle whose other leg is the vertical edge \(h\).

In calculus: the longest rod that fits in a box, or a cable across a room, is a three-dimensional distance of this kind.

## Card calc1.0-6.fc-pyth.006
kind: flashcard
skill: pre.geometry.pythagorean

### Front
A polygon is inscribed in a circle: what does that say about its corners?

### Back
- Every corner (vertex) of the polygon lies on the circle
- A rectangle inscribed in a circle of radius \(R\) has its diagonal equal to a diameter, \(2R\), so its sides satisfy \(x^2 + y^2 = (2R)^2\)
- In calculus: an inscribed rectangle, triangle or box is the shape whose area or volume is maximized, and the Pythagorean theorem ties its sides to the radius of the circle or sphere

<!-- ---------- similar triangles ---------- -->

## Card calc1.0-6.fc-sim.001
kind: flashcard
skill: pre.geometry.similar-triangles

### Front
Two angles of one triangle equal two angles of another triangle: what follows?

### Back
- The triangles are similar, because the third angles are equal too
- Corresponding sides are proportional: \(\frac{a}{a'} = \frac{b}{b'} = \frac{c}{c'}\)
- Corresponding sides are the ones opposite equal angles
- In calculus: similar triangles tie one changing length to another, such as the radius and the depth of water in a cone, or a shadow and a distance

## Card calc1.0-6.fc-sim.002
kind: flashcard
skill: pre.geometry.similar-triangles

### Front
Two similar figures have lengths in the ratio \(k\): how are their areas and their volumes related?

### Back
- Areas are in the ratio \(k^2\)
- Volumes are in the ratio \(k^3\)
- In calculus: the water in a cone has volume \(V = ch^3\) for a constant \(c\), because every length of the water cone is proportional to the depth \(h\)

## Card calc1.0-6.fc-sim.003
kind: flashcard
skill: pre.geometry.similar-triangles

### Front
A cone-shaped tank with its point down has top radius \(R\) and height \(H\). The water has depth \(h\): the radius \(r\) of the water surface

### Back
\[ \frac{r}{h} = \frac{R}{H}, \qquad r = \frac{R}{H}\,h \]

A vertical slice through the axis shows the water and the tank as similar triangles with the same point at the bottom, so radius over depth is the same for both.

In calculus: this lets the volume \(V = \frac{1}{3}\pi r^2 h\) of the water be written in terms of \(h\) alone, the standard first step of a conical-tank related-rates problem.

## Card calc1.0-6.fc-sim.004
kind: flashcard
skill: pre.geometry.similar-triangles

### Front
A lamp is at the top of a post of height \(H\). A person of height \(h\) stands a distance \(x\) from the post and has a shadow of length \(s\): the equation from similar triangles

### Back
\[ \frac{H}{x + s} = \frac{h}{s}, \qquad s = \frac{h\,x}{H - h} \]

The large triangle (post, ground out to the tip of the shadow, light ray) and the small triangle (person, shadow, light ray) are similar. The large base is \(x + s\), the distance to the person plus the shadow, and the small base is \(s\).

In calculus: the shadow problem relates \(\frac{ds}{dt}\) to \(\frac{dx}{dt}\), and the tip of the shadow moves at \(\frac{dx}{dt} + \frac{ds}{dt}\).

<!-- ===================================================================== -->
<!-- Typed-answer recall problems: the formula as an expression the app    -->
<!-- grades itself, one for each formula flashcard whose answer is an      -->
<!-- expression. A flashcard is never graded, so these carry the check.    -->
<!-- ===================================================================== -->

## Card calc1.0-6.recall-area.001
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: b, h
answer: 1/2*b*h
wrong: b*h => A triangle is half of a parallelogram with the same base and height, so the area has a factor of 1/2. @1; 1/2*(b + h) => The area multiplies the base and the height. It does not add them. @1

### Question
Write the area \(A\) of a triangle with base \(b\) and height \(h\) as an expression in \(b\) and \(h\).

### Solution
1. [pre.geometry.area-plane-figures] Formula: a triangle is half of a parallelogram with the same base and height, so \(A = \frac{1}{2}bh\).
   check: 1/2*b*h = b*h/2

## Card calc1.0-6.recall-area.002
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: b, h
answer: b*h
wrong: 1/2*b*h => The factor 1/2 belongs to a triangle. The area of a parallelogram is the base times the height. @1; 2*b + 2*h => That adds lengths, like a perimeter. The area is the base times the height. @1

### Question
Write the area \(A\) of a parallelogram with base \(b\) and height \(h\), where the height is the perpendicular distance between the two sides of length \(b\).

### Solution
1. [pre.geometry.area-plane-figures] Formula: the parallelogram can be cut and rearranged into a rectangle with the same base and height, so \(A = bh\).
   check: b*h = h*b

## Card calc1.0-6.recall-area.003
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: a, b, h
answer: 1/2*(a + b)*h
wrong: (a + b)*h => The area is the average of the parallel sides times the height, so there is a factor of 1/2. @1; a*b*h/2 => The parallel sides are added, not multiplied: their average is (a + b)/2. @1

### Question
Write the area \(A\) of a trapezoid with parallel sides \(a\) and \(b\) and height \(h\).

### Solution
1. [pre.geometry.area-plane-figures] Formula: the area is the average of the two parallel sides times the height, so \(A = \frac{1}{2}(a + b)h\).
   check: 1/2*(a + b)*h = (a + b)/2*h

## Card calc1.0-6.recall-area.004
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: r
answer: pi*r^2
wrong: 2*pi*r => That is the circumference. The area is pi times the square of the radius. @1; pi*r => The radius is squared in the area of a circle. @1

### Question
Write the area \(A\) of a circle with radius \(r\).

### Solution
1. [pre.geometry.area-plane-figures] Formula: the area of a circle is pi times the square of the radius, \(A = \pi r^2\), which is \(\frac{\pi d^2}{4}\) in terms of the diameter \(d = 2r\).
   check: pi*r^2 = pi*(2*r)^2/4

## Card calc1.0-6.recall-area.005
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: a, b
answer: pi*a*b
wrong: pi*(a + b) => The area is pi times the product of the semi-axes. For a circle, a = b = r, the product gives pi r squared. @1; 2*pi*a*b => For a circle, a = b = r, the area must be pi r squared, so the formula has no factor of 2. @1

### Question
Write the area \(A\) of an ellipse with semi-axes \(a\) and \(b\), which are half of its longest width and half of its shortest width.

### Solution
1. [pre.geometry.area-plane-figures] Formula: the area is pi times the product of the semi-axes, \(A = \pi a b\), which is \(\pi r^2\) when \(a = b = r\).
   check: pi*a*b = pi*b*a

## Card calc1.0-6.recall-area.006
skill: pre.geometry.area-plane-figures
difficulty: 1
answer-type: expression
vars: a, b, theta
answer: 1/2*a*b*sin(theta)
wrong: 1/2*a*b*cos(theta) => The area uses the sine of the angle between the sides. When the angle is 90 degrees the area is ab/2, and sin 90 degrees is 1. @1; a*b*sin(theta) => A triangle is half of the parallelogram with the same two sides, so the area has a factor of 1/2. @1

### Question
A triangle has two sides of lengths \(a\) and \(b\), and the angle between those two sides is \(\theta\). Write the area \(A\) of the triangle.

### Solution
1. [pre.geometry.area-plane-figures] Formula: take side \(a\) as the base. The height is \(b\sin\theta\), so \(A = \frac{1}{2}a(b\sin\theta) = \frac{1}{2}ab\sin\theta\).
   check: 1/2*a*(b*sin(theta)) = 1/2*a*b*sin(theta)

## Card calc1.0-6.recall-perim.001
skill: pre.geometry.perimeter-circumference
difficulty: 1
answer-type: expression
vars: r
answer: 2*pi*r
wrong: pi*r^2 => That is the area. The circumference is the distance around the circle. @1; pi*r => The circumference is pi times the diameter, and the diameter is 2r. @1

### Question
Write the circumference \(C\) of a circle with radius \(r\).

### Solution
1. [pre.geometry.perimeter-circumference] Formula: the circumference is pi times the diameter, \(C = \pi d = 2\pi r\).
   check: pi*(2*r) = 2*pi*r

## Card calc1.0-6.recall-perim.002
skill: pre.geometry.perimeter-circumference
difficulty: 1
answer-type: expression
vars: l, w
answer: 2*l + 2*w
wrong: l*w => That is the area. The perimeter is the distance all the way around. @1; l + w => The distance around the rectangle has two lengths and two widths. @1

### Question
Write the perimeter \(P\) of a rectangle with length \(l\) and width \(w\).

### Solution
1. [pre.geometry.perimeter-circumference] Formula: going all the way around takes two lengths and two widths, \(P = 2l + 2w\).
   check: 2*l + 2*w = 2*(l + w)

## Card calc1.0-6.recall-vol.001
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: l, w, h
answer: l*w*h
wrong: 2*(l*w + l*h + w*h) => That is the surface area. The volume is the product of the three edges. @1; l + w + h => The volume is the product of the three edges, not their sum. @1

### Question
Write the volume \(V\) of a rectangular box with length \(l\), width \(w\) and height \(h\).

### Solution
1. [pre.geometry.volume-solids] Formula: the volume is the area of the base times the height, \(V = lwh\).
   check: l*w*h = (l*w)*h

## Card calc1.0-6.recall-vol.002
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: r, h
answer: pi*r^2*h
wrong: 2*pi*r*h => That is the area of the curved side. The volume is the area of the base times the height. @1; 1/3*pi*r^2*h => The factor 1/3 belongs to a cone, not to a cylinder. @1

### Question
Write the volume \(V\) of a right circular cylinder with radius \(r\) and height \(h\).

### Solution
1. [pre.geometry.volume-solids] Formula: the volume is the area of the circular base times the height, \(V = \pi r^2 h\).
   check: pi*r^2*h = (pi*r^2)*h

## Card calc1.0-6.recall-vol.003
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: r, h
answer: 1/3*pi*r^2*h
wrong: pi*r^2*h => A cone holds one third of the cylinder with the same base and height, so the volume has a factor of 1/3. @1; 1/2*pi*r^2*h => A cone holds one third, not one half, of the cylinder with the same base and height. @1

### Question
Write the volume \(V\) of a right circular cone with base radius \(r\) and height \(h\), where \(h\) is the vertical height from the base to the point.

### Solution
1. [pre.geometry.volume-solids] Formula: a cone holds one third of the cylinder with the same base and height, so \(V = \frac{1}{3}\pi r^2 h\).
   check: 1/3*pi*r^2*h = pi*r^2*h/3

## Card calc1.0-6.recall-vol.004
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: r
answer: 4/3*pi*r^3
wrong: 4*pi*r^2 => That is the surface area. A volume has the radius cubed. @1; 4/3*pi*r^2 => A volume has the radius cubed, not squared. @1

### Question
Write the volume \(V\) of a sphere with radius \(r\).

### Solution
1. [pre.geometry.volume-solids] Formula: the volume of a sphere is four thirds of pi times the cube of the radius, \(V = \frac{4}{3}\pi r^3\).
   check: 4/3*pi*r^3 = 4*pi*r^3/3

## Card calc1.0-6.recall-vol.005
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: B, h
answer: 1/3*B*h
wrong: B*h => A pyramid holds one third of the prism with the same base and height, so the volume has a factor of 1/3. @1; 1/2*B*h => The factor for a pyramid is 1/3, not 1/2. @1

### Question
Write the volume \(V\) of a pyramid with base area \(B\) and height \(h\), where \(h\) is the perpendicular distance from the base to the top point.

### Solution
1. [pre.geometry.volume-solids] Formula: a pyramid holds one third of the prism with the same base and height, so \(V = \frac{1}{3}Bh\).
   check: 1/3*B*h = B*h/3

## Card calc1.0-6.recall-vol.006
skill: pre.geometry.volume-solids
difficulty: 1
answer-type: expression
vars: B, h
answer: B*h
wrong: 1/3*B*h => The factor 1/3 belongs to solids that come to a point, such as cones and pyramids. A solid with a constant cross-section has volume B times h. @1; B + h => The volume is the cross-sectional area times the length. It is not their sum. @1

### Question
A solid has the same cross-section, with area \(B\), along its whole length \(h\), as a prism or a cylinder does. Write its volume \(V\).

### Solution
1. [pre.geometry.volume-solids] Formula: stacking the cross-section along the length gives \(V = Bh\).
   check: B*h = h*B

## Card calc1.0-6.recall-surf.001
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: expression
vars: r
answer: 4*pi*r^2
wrong: 4/3*pi*r^3 => That is the volume. The surface area is 4 pi r squared. @1; pi*r^2 => That is the area of a flat circle with the same radius. The surface of a sphere has four times that area. @1

### Question
Write the surface area \(S\) of a sphere with radius \(r\).

### Solution
1. [pre.geometry.surface-area-solids] Formula: the surface area of a sphere is four times the area of a circle with the same radius, \(S = 4\pi r^2\).
   check: 4*pi*r^2 = 4*(pi*r^2)

## Card calc1.0-6.recall-surf.002
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: expression
vars: r, h
answer: 2*pi*r^2 + 2*pi*r*h
wrong: 2*pi*r*h => A closed cylinder also has a top and a bottom, two circles of area pi r squared each. @1; pi*r^2 + 2*pi*r*h => A closed cylinder has two circular ends, not one. @1

### Question
Write the total surface area \(S\) of a closed cylinder with radius \(r\) and height \(h\), including both circular ends.

### Solution
1. [pre.geometry.surface-area-solids] Formula: the two circular ends have area \(2\pi r^2\) and the curved side has area \(2\pi r h\), so \(S = 2\pi r^2 + 2\pi r h\).
   check: 2*pi*r^2 + 2*pi*r*h = 2*pi*r*(r + h)

## Card calc1.0-6.recall-surf.003
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: expression
vars: r, h
answer: 2*pi*r*h
wrong: pi*r^2*h => That is the volume. The curved side unrolls into a rectangle, and its area is the circumference times the height. @1; pi*r*h => The curved side unrolls into a rectangle as wide as the circumference, 2 pi r. @1

### Question
Write the area \(A\) of the curved side of a cylinder with radius \(r\) and height \(h\), not counting the circular ends.

### Solution
1. [pre.geometry.surface-area-solids] Formula: the curved side unrolls into a rectangle as wide as the circumference and as tall as the cylinder, \(A = 2\pi r h\).
   check: 2*pi*r*h = (2*pi*r)*h

## Card calc1.0-6.recall-surf.004
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: expression
vars: r, s
answer: pi*r*s
wrong: 2*pi*r*s => Unrolled, the curved surface of a cone is a sector, and its area is half of the circumference times the slant height. @1; 1/3*pi*r^2*s => That has the form of a volume. The curved surface of a cone has area pi r s. @1

### Question
Write the area \(A\) of the curved surface of a right circular cone with base radius \(r\) and slant height \(s\), not counting the base.

### Solution
1. [pre.geometry.surface-area-solids] Formula: unrolled, the curved surface is a sector of radius \(s\) whose arc is the circumference \(2\pi r\), so \(A = \frac{1}{2}s(2\pi r) = \pi r s\).
   check: 1/2*s*(2*pi*r) = pi*r*s

## Card calc1.0-6.recall-surf.005
skill: pre.geometry.surface-area-solids
difficulty: 1
answer-type: expression
vars: l, w, h
answer: 2*(l*w + l*h + w*h)
wrong: l*w + l*h + w*h => The box has three pairs of equal faces, so the sum lw + lh + wh must be doubled. @1; l*w*h => That is the volume. The surface area adds up the areas of the six faces. @1

### Question
Write the total surface area \(S\) of a closed rectangular box with length \(l\), width \(w\) and height \(h\).

### Solution
1. [pre.geometry.surface-area-solids] Formula: the six faces come in three equal pairs, so \(S = 2(lw + lh + wh)\).
   check: 2*(l*w + l*h + w*h) = 2*l*w + 2*l*h + 2*w*h

## Card calc1.0-6.recall-arc.001
skill: pre.geometry.arc-sector
difficulty: 1
answer-type: expression
vars: r, theta
answer: r*theta
wrong: 1/2*r^2*theta => That is the area of the sector. The arc length is the radius times the angle. @1; 2*pi*r*theta => The arc is the fraction theta over 2 pi of the circumference 2 pi r, which simplifies to r theta. @1

### Question
A circle has radius \(r\). Write the length \(s\) of an arc of the circle whose central angle is \(\theta\) radians.

### Solution
1. [pre.geometry.arc-sector] Formula: the arc is the fraction \(\frac{\theta}{2\pi}\) of the circumference, \(s = \frac{\theta}{2\pi}(2\pi r) = r\theta\).
   check: theta/(2*pi)*(2*pi*r) = r*theta

## Card calc1.0-6.recall-arc.002
skill: pre.geometry.arc-sector
difficulty: 1
answer-type: expression
vars: r, theta
answer: 1/2*r^2*theta
wrong: r*theta => That is the arc length. The area of a sector has the radius squared. @1; r^2*theta => The sector is the fraction theta over 2 pi of the area pi r squared, which gives one half of r squared times theta. @1

### Question
A circle has radius \(r\). Write the area \(A\) of a sector of the circle whose central angle is \(\theta\) radians.

### Solution
1. [pre.geometry.arc-sector] Formula: the sector is the fraction \(\frac{\theta}{2\pi}\) of the circle, \(A = \frac{\theta}{2\pi}(\pi r^2) = \frac{1}{2}r^2\theta\).
   check: theta/(2*pi)*(pi*r^2) = 1/2*r^2*theta

## Card calc1.0-6.recall-angle.001
skill: pre.geometry.angle-relationships
difficulty: 1
answer-type: expression
vars: n
answer: (n - 2)*180
wrong: n*180 => A convex polygon with n sides can be cut into n - 2 triangles, not n. @1; (n - 1)*180 => The diagonals from one corner cut a convex polygon with n sides into n - 2 triangles, not n - 1. @1

### Question
Write the sum \(S\), in degrees, of the interior angles of a polygon with \(n\) sides.

### Solution
1. [pre.geometry.angle-relationships] Formula: the diagonals from one corner cut a convex polygon into \(n - 2\) triangles, each with angle sum \(180^\circ\), so \(S = (n - 2)\cdot 180\).
   check: (n - 2)*180 = 180*n - 360

## Card calc1.0-6.recall-special.001
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: expression
vars: a
answer: a*sqrt(2)
wrong: 2*a => The hypotenuse is the leg times the square root of 2, not 2. @1; a*sqrt(3) => The square root of 3 belongs to the 30-60-90 triangle. In a 45-45-90 triangle the hypotenuse is the leg times the square root of 2. @1

### Question
A right triangle has two equal legs of length \(a\). Write the length \(c\) of its hypotenuse.

### Solution
1. [pre.geometry.special-right-triangles] Formula: the squares of the legs add up to the square of the hypotenuse, \(c^2 = a^2 + a^2 = 2a^2\), so \(c = a\sqrt{2}\).
   check: (a*sqrt(2))^2 = a^2 + a^2
   check: sqrt(2)*a = a*sqrt(2)

## Card calc1.0-6.recall-special.002
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: expression
vars: a
answer: a*sqrt(3)
wrong: a*sqrt(2) => The square root of 2 belongs to the 45-45-90 triangle. In a 30-60-90 triangle the longer leg is the shortest side times the square root of 3. @1; 2*a => That is the hypotenuse. The longer leg is the shortest side times the square root of 3. @1

### Question
In a 30-60-90 triangle the shortest side has length \(a\). Write the length of the longer leg.

### Solution
1. [pre.geometry.special-right-triangles] Formula: the hypotenuse is \(2a\), so the longer leg satisfies \(\ell^2 = (2a)^2 - a^2 = 3a^2\) and \(\ell = a\sqrt{3}\).
   check: (a*sqrt(3))^2 = (2*a)^2 - a^2
   check: sqrt(3)*a = a*sqrt(3)

## Card calc1.0-6.recall-special.003
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: expression
vars: s
answer: sqrt(3)/2*s
wrong: s*sqrt(3) => The height is the longer leg of a 30-60-90 triangle whose shortest side is s/2, so it is half of s times the square root of 3. @1; s/2 => That is half of the base. The height is the longer leg, s/2 times the square root of 3. @1

### Question
Write the height \(h\) of an equilateral triangle with side \(s\).

### Solution
1. [pre.geometry.special-right-triangles] Formula: the height splits the triangle into two 30-60-90 triangles with shortest side \(\frac{s}{2}\), so the height is \(\frac{s}{2}\sqrt{3} = \frac{\sqrt{3}}{2}s\).
   check: (sqrt(3)/2*s)^2 = s^2 - (s/2)^2
   check: s/2*sqrt(3) = sqrt(3)/2*s

## Card calc1.0-6.recall-special.004
skill: pre.geometry.special-right-triangles
difficulty: 1
answer-type: expression
vars: s
answer: sqrt(3)/4*s^2
wrong: sqrt(3)/2*s^2 => The area is one half of the base times the height, and the height is already the square root of 3 over 2 times s, so the area is the square root of 3 over 4 times s squared. @1; sqrt(3)/4*s => An area has the side squared. It is half of the base, s, times the height, which also contains an s. @1

### Question
Write the area \(A\) of an equilateral triangle with side \(s\).

### Solution
1. [pre.geometry.special-right-triangles] Formula: the area is half of the base times the height, \(A = \frac{1}{2}s\cdot\frac{\sqrt{3}}{2}s = \frac{\sqrt{3}}{4}s^2\).
   check: 1/2*s*(sqrt(3)/2*s) = sqrt(3)/4*s^2

## Card calc1.0-6.recall-dist.001
skill: pre.geometry.distance-formula
difficulty: 1
answer-type: expression
vars: p, q, u, v
answer: sqrt((u - p)^2 + (v - q)^2)
wrong: (u - p)^2 + (v - q)^2 => That is the square of the distance. Take the square root. @1; (u - p) + (v - q) => The distance is the hypotenuse of a right triangle whose legs are the horizontal and vertical differences, so square them, add, and take the square root. @1

### Question
Write the distance \(d\) between the points \((p, q)\) and \((u, v)\).

### Solution
1. [pre.geometry.distance-formula] Formula: the horizontal difference \(u - p\) and the vertical difference \(v - q\) are the legs of a right triangle, and the distance is its hypotenuse, \(d = \sqrt{(u - p)^2 + (v - q)^2}\).
   check: sqrt((u - p)^2 + (v - q)^2) = sqrt((p - u)^2 + (q - v)^2)

## Card calc1.0-6.recall-cos.001
skill: pre.geometry.law-of-cosines
difficulty: 1
answer-type: expression
vars: a, b, theta
answer: a^2 + b^2 - 2*a*b*cos(theta)
wrong: a^2 + b^2 => That is the Pythagorean theorem, which holds only when the angle is 90 degrees. The law of cosines subtracts 2ab cos(theta) as well. @1; a^2 + b^2 + 2*a*b*cos(theta) => The law of cosines subtracts 2ab cos(theta), so a minus sign comes before that term. @1; a^2 + b^2 - 2*a*b*sin(theta) => The law of cosines uses the cosine of the angle between the sides. For a right angle the cosine is 0, which gives back the Pythagorean theorem. @1

### Question
In a triangle, the sides \(a\) and \(b\) meet at the angle \(\theta\), and \(c\) is the side opposite \(\theta\). Write \(c^2\) in terms of \(a\), \(b\) and \(\theta\).

### Solution
1. [pre.geometry.law-of-cosines] Formula: the law of cosines gives \(c^2 = a^2 + b^2 - 2ab\cos\theta\), which becomes \(a^2 + b^2\) when \(\theta = 90^\circ\).
   check: a^2 + b^2 - 2*a*b*cos(pi/2) = a^2 + b^2
   check: a^2 + b^2 - 2*a*b*cos(theta) = a^2 + b^2 - 2*b*a*cos(theta)

## Card calc1.0-6.recall-comp.001
skill: pre.geometry.composite-figures
difficulty: 1
answer-type: expression
vars: w, h
answer: 2*h + w + pi*w/2
wrong: 2*h + 2*w + pi*w/2 => The top edge of the rectangle is inside the window, where the semicircle is attached, so it is not part of the outside edge. @1; 2*h + w + pi*w => The curved edge is a semicircle, which is half of the circumference pi w of a circle with diameter w. @1

### Question
A window is a rectangle of width \(w\) and height \(h\), with a semicircle on its top edge, so the diameter of the semicircle is \(w\). Write the length \(P\) of the outside edge of the window.

### Solution
1. [pre.geometry.composite-figures] Formula: the outside edge is two vertical sides, the bottom, and a semicircular arc of length \(\frac{1}{2}\pi w\), and the top edge of the rectangle is left out, so \(P = 2h + w + \frac{\pi w}{2}\).
   check: 2*h + w + 1/2*(pi*w) = 2*h + w + pi*w/2

## Card calc1.0-6.recall-comp.002
skill: pre.geometry.composite-figures
difficulty: 1
answer-type: expression
vars: w, h
answer: w*h + pi*w^2/8
wrong: w*h + pi*w^2/4 => The semicircle is half of a circle with radius w/2, and pi w squared over 4 is the area of the whole circle. @1; w*h + pi*w^2/2 => The semicircle has radius w/2, half of the width, not radius w. @1

### Question
A window is a rectangle of width \(w\) and height \(h\), with a semicircle on its top edge, so the diameter of the semicircle is \(w\). Write the area \(A\) of the window.

### Solution
1. [pre.geometry.composite-figures] Formula: the rectangle has area \(wh\), and the semicircle has radius \(\frac{w}{2}\) and area \(\frac{1}{2}\pi\left(\frac{w}{2}\right)^2 = \frac{\pi w^2}{8}\), so \(A = wh + \frac{\pi w^2}{8}\).
   check: w*h + 1/2*pi*(w/2)^2 = w*h + pi*w^2/8

## Card calc1.0-6.recall-pyth.001
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: expression
vars: a, b
answer: sqrt(a^2 + b^2)
wrong: a + b => The hypotenuse is shorter than the sum of the legs. Square the legs, add them, and take the square root. @1; a^2 + b^2 => That is the square of the hypotenuse. Take the square root. @1

### Question
A right triangle has legs \(a\) and \(b\). Write the length \(c\) of the hypotenuse.

### Solution
1. [pre.geometry.pythagorean] Formula: the square of the hypotenuse is the sum of the squares of the legs, so \(c = \sqrt{a^2 + b^2}\).
   check: sqrt(a^2 + b^2)^2 = a^2 + b^2
   check: (a^2 + b^2)^(1/2) = sqrt(a^2 + b^2)

## Card calc1.0-6.recall-pyth.002
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: expression
vars: l, w
answer: sqrt(l^2 + w^2)
wrong: l + w => The diagonal is the hypotenuse of a right triangle with legs l and w, so it is shorter than l + w. @1; l^2 + w^2 => That is the square of the diagonal. Take the square root. @1

### Question
Write the length \(d\) of the diagonal of a rectangle with length \(l\) and width \(w\).

### Solution
1. [pre.geometry.pythagorean] Formula: the diagonal and the two sides form a right triangle, so \(d = \sqrt{l^2 + w^2}\).
   check: sqrt(l^2 + w^2)^2 = l^2 + w^2
   check: (l^2 + w^2)^(1/2) = sqrt(l^2 + w^2)

## Card calc1.0-6.recall-pyth.003
skill: pre.geometry.pythagorean
difficulty: 1
answer-type: expression
vars: l, w, h
answer: sqrt(l^2 + w^2 + h^2)
wrong: sqrt(l^2 + w^2) + h => Use the theorem twice: the floor diagonal and the height are the legs of a second right triangle, so square the height and add it under the square root. @1; l + w + h => The diagonal cuts across the box, so it is shorter than l + w + h. @1

### Question
Write the length \(d\) of the longest diagonal of a rectangular box with edges \(l\), \(w\) and \(h\).

### Solution
1. [pre.geometry.pythagorean] Formula: the floor diagonal is \(\sqrt{l^2 + w^2}\) and it is a leg of a right triangle whose other leg is \(h\), so \(d = \sqrt{l^2 + w^2 + h^2}\).
   check: sqrt(sqrt(l^2 + w^2)^2 + h^2) = sqrt(l^2 + w^2 + h^2)

## Card calc1.0-6.recall-sim.001
skill: pre.geometry.similar-triangles
difficulty: 1
answer-type: expression
vars: R, H, h
answer: R*h/H
wrong: H*h/R => The radius and the depth of the water make a triangle similar to the tank, so radius over depth is R over H. @1; R*H/h => Radius over depth is the same for the water and the tank: r over h equals R over H. @1

### Question
A cone-shaped tank with its point down has top radius \(R\) and height \(H\). Water in the tank has depth \(h\). Write the radius \(r\) of the water surface in terms of \(R\), \(H\) and \(h\).

### Solution
1. [pre.geometry.similar-triangles] Formula: the water and the tank give similar triangles with the same point at the bottom, so \(\frac{r}{h} = \frac{R}{H}\) and \(r = \frac{R}{H}h\).
   check: R/H*h = R*h/H

## Card calc1.0-6.recall-sim.002
skill: pre.geometry.similar-triangles
difficulty: 1
answer-type: expression
vars: H, h, x
answer: h*x/(H - h)
wrong: h*x/H => The large triangle runs from the post to the tip of the shadow, so its base is x + s, not x. @1; h*x/(H + h) => Writing H s = h (x + s) and moving h s to the left side gives H s - h s, a difference. @1

### Question
A lamp is at the top of a vertical post of height \(H\). A person of height \(h\), where \(h < H\), stands a distance \(x\) from the post, and the person's shadow on the level ground has length \(s\). Write \(s\) in terms of \(H\), \(h\) and \(x\).

### Solution
1. [pre.geometry.similar-triangles] Formula: the large triangle (post, ground, light ray) and the small triangle (person, shadow, light ray) are similar, so \(\frac{H}{x + s} = \frac{h}{s}\), which gives \(Hs = h(x + s)\) and \(s = \frac{hx}{H - h}\).
   check: H*(h*x/(H - h)) = h*(x + h*x/(H - h))
   check: h*x/(H - h) = h*x/(H - h)
