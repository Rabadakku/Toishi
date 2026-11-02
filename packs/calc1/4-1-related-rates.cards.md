---
format: mastery-cards 1
deck: Calculus I::4 Applications of Derivatives::4.1 Related Rates
source: original
license: CC BY-NC-SA 4.0
---

<!-- Section 4.1 Related Rates: six skills, one worked example each, twelve problems each.
     Conventions: a rate is signed (increasing = positive, decreasing = negative). Answers are
     numbers without units because the grader has no quantity type yet: the question names the
     unit, and ### Answer shows the signed rate with its unit after grading. Each full solution
     ends with a translate step that states the sign and the unit. Quantities that stay constant
     (a ladder's length) are numbers; quantities that change are named and get a rate.
     Provenance: every card is original. -->


<!-- ===================================================================== -->
<!-- calc1.related-rates.translate                                         -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-1.translate-example.001
kind: example
skill: calc1.related-rates.translate
uses: pre.geometry.pythagorean, calc1.related-rates.relate, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear

### Question
A 13 ft ladder leans against a vertical wall. Its foot slides away from the wall at a steady 2 ft/s. How fast is the top of the ladder moving down the wall at the instant when the foot is 5 ft from the wall?

### Solution
0. [calc1.related-rates.translate] Set up: let \(x\) be the distance in feet from the wall to the foot of the ladder and \(y\) the height in feet of its top, both functions of the time \(t\) in seconds. The foot moves away from the wall, so \(x\) is increasing and \(\frac{dx}{dt} = +2\). The question asks for \(\frac{dy}{dt}\) at the instant \(x = 5\).
   check: diff(5 + 2*t, t) = 2
1. [pre.geometry.pythagorean] Geometry: the wall, the ground and the ladder form a right triangle whose hypotenuse is the ladder, \(13\) ft long.
   check: 13^2 = 169
2. [calc1.related-rates.relate] Relate: the ladder's length never changes, so for every time \(t\) the two legs satisfy \(x^2 + y^2 = 169\). Only \(x\) and \(y\) change; \(169\) is a constant.
   check: 5^2 + 12^2 = 169
3. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(2x\,\frac{dx}{dt} + 2y\,\frac{dy}{dt} = 0\).
   check: diff(u^2, u) = 2*u
4. [calc1.related-rates.values-at-instant] At the instant: \(x = 5\) gives \(y^2 = 169 - 25 = 144\), so \(y = 12\). Only now substitute \(x = 5\), \(y = 12\), \(\frac{dx}{dt} = 2\): \(2(5)(2) + 2(12)\frac{dy}{dt} = 0\).
   check: 169 - 5^2 = 12^2
   check: 2*5*2 + 2*12*(-5/6) = 0
5. [alg.solve.linear] Solve for the unknown rate: \(24\,\frac{dy}{dt} = -20\), so \(\frac{dy}{dt} = -\frac{5}{6}\).
   check: solve(2*5*2 + 2*12*v, v) = {-5/6}
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dy}{dt} = -\frac{5}{6}\) ft/s. The negative sign means the height is decreasing, so the top slides down the wall at \(\frac{5}{6}\) ft/s, about \(0.83\) ft/s. A direct check: with \(x = 5 + 2t\) and \(y = \sqrt{169 - x^2}\), the slope of \(y\) at \(t = 0\) is the same number.
   check: subs(diff(sqrt(169 - (5 + 2*t)^2), t), t, 0) = -5/6

<!-- tier 1, template: the sign of a given rate (a quantity that decreases) -->
## Card calc1.4-1.translate-drain.t01
skill: calc1.related-rates.translate
difficulty: 1
answer-type: number
vars: q = int(2, 45)
answer: -q

### Question
Water drains out of a reservoir at a steady [[q]] thousand liters per hour. Let \(V\) be the volume of water in the reservoir, in thousand liters, and \(t\) the time in hours. What is \(\dfrac{dV}{dt}\), in thousand liters per hour?

### Answer
\(\dfrac{dV}{dt} = -[[q]]\) thousand liters per hour

### Solution
0. [calc1.related-rates.translate] Set up: water leaves the reservoir, so the volume is decreasing, and a rate of change is negative when the quantity decreases.
1. [calc1.related-rates.translate] Signed rate: the volume falls by [[q]] thousand liters each hour, so \(\frac{dV}{dt} = -[[q]]\) thousand liters per hour.
   check: diff(300 - q*t, t) = -q

<!-- tier 1: an object approaching a point has a shrinking distance -->
## Card calc1.4-1.translate-approach.001
skill: calc1.related-rates.translate
difficulty: 1
answer-type: choice

### Question
A truck drives along a straight road toward a toll booth at a steady 45 mph. Let \(s\) be the truck's distance from the booth, in miles, and \(t\) the time in hours. Which statement about \(\dfrac{ds}{dt}\) is correct?

### Choices
- [ ] \(\dfrac{ds}{dt} = 45\) mph, because the truck's speed is 45 mph
- [x] \(\dfrac{ds}{dt} = -45\) mph, because the distance to the booth is decreasing
- [ ] \(\dfrac{ds}{dt} = 0\) mph, because the speed is steady
- [ ] \(\dfrac{ds}{dt}\) cannot be found without knowing how far the truck is from the booth

### Solution
0. [calc1.related-rates.translate] Set up: the truck is getting closer to the booth, so the distance is decreasing, and its rate is negative.
1. [calc1.related-rates.translate] Signed rate: the speed is 45 mph, but the distance shrinks, so \(\frac{ds}{dt} = -45\) miles per hour.
   check: diff(3 - 45*t, t) = -45

<!-- tier 1, template: a shrinking radius with a decimal rate -->
## Card calc1.4-1.translate-melt.t02
skill: calc1.related-rates.translate
difficulty: 1
answer-type: number
vars: k = decimal(0.2, 1.8, 1)
answer: -k

### Question
A spherical hailstone melts as it falls, and its radius \(r\), in millimeters, is shrinking at [[k]] mm per minute. What is \(\dfrac{dr}{dt}\), in millimeters per minute, where \(t\) is the time in minutes?

### Answer
\(\dfrac{dr}{dt} = -[[k]]\) mm per minute

### Solution
0. [calc1.related-rates.translate] Set up: the radius is shrinking, so it is decreasing and its rate is negative.
1. [calc1.related-rates.translate] Signed rate: \(\frac{dr}{dt} = -[[k]]\) millimeters per minute.
   check: diff(8 - k*t, t) = -k

<!-- tier 2, template: inflow and outflow combine into one signed net rate -->
## Card calc1.4-1.translate-net.t01
skill: calc1.related-rates.translate
difficulty: 2
answer-type: number
vars: a = int(10, 15); b = int(4, 22)
require: a != b
answer: a - b
wrong: a + b => The drain takes water out, so it contributes a negative rate. @1; b - a => Net rate is what flows in minus what flows out. @2

### Question
A pipe fills a tank at a steady [[a]] liters per minute while a drain removes water at a steady [[b]] liters per minute. Both are open. Let \(V\) be the volume of water in the tank, in liters, and \(t\) the time in minutes. What is \(\dfrac{dV}{dt}\), in liters per minute?

### Answer
\(\dfrac{dV}{dt} = [[a - b]]\) liters per minute

### Solution
0. [calc1.related-rates.translate] Set up: the volume changes because of two flows at once, one adding water and one removing it, so the rate of change of the volume is the sum of two signed rates.
1. [calc1.related-rates.translate] Signed rates: the pipe adds, \(+[[a]]\) L/min, and the drain removes, \(-[[b]]\) L/min.
   check: diff(a*t, t) = a
   check: diff(-b*t, t) = -b
2. [calc1.related-rates.translate] Net rate: \(\frac{dV}{dt} = [[a]] - [[b]] = [[a - b]]\) liters per minute.
   check: diff(200 + a*t - b*t, t) = a - b

<!-- tier 2, template: signs of two rates, approaching and receding -->
## Card calc1.4-1.translate-signs.t01
skill: calc1.related-rates.translate
difficulty: 2
answer-type: list
vars: u = int(30, 45); w = int(20, 29)
require: u != w
answer: -u, w
wrong: u, w => Car A is driving toward the intersection, so its distance is decreasing. @1; -u, -w => Car B has already passed the intersection and is driving away, so its distance is increasing. @1; w, -u => Give the rate for car A first, then for car B. @2

### Question
Two roads cross at an intersection. Car A drives toward the intersection at [[u]] mph. Car B has already passed through it and drives away from it along the other road at [[w]] mph. Let \(x\) and \(y\) be the distances of car A and car B from the intersection, in miles, and \(t\) the time in hours. Give \(\dfrac{dx}{dt}\) and \(\dfrac{dy}{dt}\), in miles per hour and in that order.

### Answer
\(\dfrac{dx}{dt} = -[[u]]\) mph and \(\dfrac{dy}{dt} = [[w]]\) mph

### Solution
0. [calc1.related-rates.translate] Set up: a distance from a fixed point decreases while a car approaches that point and increases while it moves away.
1. [calc1.related-rates.translate] Car A approaches, so \(x\) decreases: \(\frac{dx}{dt} = -[[u]]\). Car B recedes, so \(y\) increases: \(\frac{dy}{dt} = +[[w]]\).
   check: diff(3 - u*t, t) = -u
   check: diff(2 + w*t, t) = w
2. [calc1.related-rates.translate] Answer in order: \(\frac{dx}{dt} = -[[u]]\) mph, then \(\frac{dy}{dt} = [[w]]\) mph.
   check: {diff(3 - u*t, t), diff(2 + w*t, t)} = {-u, w}

<!-- tier 2, template: from a signed rate back to a speed -->
## Card calc1.4-1.translate-speed.t01
skill: calc1.related-rates.translate
difficulty: 2
answer-type: number
vars: k = int(2, 19)
answer: k/10
wrong: -k/10 => The sign only says the depth is decreasing. The question asks for a speed, which is positive. @1

### Question
A calculation for a draining cylindrical tank gives \(\dfrac{dh}{dt} = -[[tex(k/10)]]\), where \(h\) is the depth of the water in meters and \(t\) is the time in minutes. At what speed is the water level falling, in meters per minute?

### Answer
[[tex(k/10)]] meters per minute

### Solution
0. [calc1.related-rates.translate] Set up: the sign of a rate gives the direction of change and its size gives the speed. A negative rate for the depth means the level is falling.
1. [calc1.related-rates.translate] Interpret with a unit: the level falls at \(\left|-[[tex(k/10)]]\right| = [[tex(k/10)]]\) meters per minute.
   check: abs(-k/10) = k/10

<!-- tier 2: read the given and the wanted rate off a ladder story -->
## Card calc1.4-1.translate-wanted.001
skill: calc1.related-rates.translate
difficulty: 2
answer-type: choice

### Question
A 17 ft ladder leans against a vertical wall. Its foot is pulled away from the wall at a steady 3 ft/s. Let \(x\) be the distance in feet from the wall to the foot and \(y\) the height in feet of the top, and let \(t\) be the time in seconds. The question is: how fast is the top sliding down the wall at the instant when the foot is 8 ft from the wall? Which choice states the given rate and the wanted rate correctly?

### Choices
- [ ] Given \(\frac{dx}{dt} = -3\). Wanted \(\frac{dy}{dt}\) when \(x = 8\).
- [ ] Given \(\frac{dx}{dt} = 3\). Wanted \(\frac{dy}{dt}\) when \(y = 8\).
- [x] Given \(\frac{dx}{dt} = 3\), since \(x\) is increasing. Wanted \(\frac{dy}{dt}\) when \(x = 8\), which will be negative since \(y\) is decreasing.
- [ ] Given \(\frac{dy}{dt} = 3\). Wanted \(\frac{dx}{dt}\) when \(x = 8\).

### Solution
0. [calc1.related-rates.translate] Set up: the foot moves away from the wall, so its distance increases and the given rate is positive. The unknown is how fast the height changes, and the instant is described by the foot's distance.
1. [calc1.related-rates.translate] Read off: the given rate is that of the foot's distance from the wall, positive and equal to 3 ft/s, and the wanted rate is that of the top's height at the instant when the foot is 8 ft from the wall. Because the top moves down, the answer will be negative.

<!-- tier 3: the wanted rate is the tip of the shadow, not its length -->
## Card calc1.4-1.translate-shadow.001
skill: calc1.related-rates.translate
uses: pre.geometry.similar-triangles, alg.solve.linear, calc1.related-rates.eliminate-variable, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant
difficulty: 3
answer-type: number
answer: 7
wrong: 3 => That is the rate at which the length of the shadow grows. The question asks about the tip of the shadow, whose distance from the lamp post is her distance plus the length of her shadow. @0; 4 => 4 ft/s is the woman's own speed. The tip of her shadow is farther out and moves faster than she does. @3

### Question
A lamp is mounted at the top of a 14 ft post. A woman 6 ft tall walks away from the post along level ground at a steady 4 ft/s. How fast is the tip of her shadow moving away from the base of the post at the instant when she is 20 ft from the post? Give the rate in feet per second.

### Answer
\(\dfrac{dp}{dt} = 7\) ft/s

### Solution
0. [calc1.related-rates.translate] Set up: let \(x\) be the woman's distance from the post, \(s\) the length of her shadow, and \(p = x + s\) the distance from the post to the tip of the shadow, all in feet, with \(t\) in seconds. Given \(\frac{dx}{dt} = 4\). Wanted: the speed of the tip, which is \(\frac{dp}{dt}\), not \(\frac{ds}{dt}\).
   check: diff(20 + 4*t, t) = 4
1. [pre.geometry.similar-triangles] Similar triangles: the lamp, the post and the ground form a right triangle that is similar to the triangle made by the woman and her shadow. Heights over bases agree: \(\frac{14}{x + s} = \frac{6}{s}\), that is \(14s = 6(x + s)\).
   check: 14*(3*x/4) = 6*(x + 3*x/4)
2. [alg.solve.linear] Solve for the shadow: \(8s = 6x\), so \(s = \frac{3x}{4}\).
   check: solve(14*s - 6*(x + s), s) = {3*x/4}
3. [calc1.related-rates.eliminate-variable] Eliminate \(s\), whose rate is not given: \(p = x + \frac{3x}{4} = \frac{7x}{4}\).
   check: x + 3*x/4 = 7*x/4
4. [calc1.related-rates.differentiate-time] Differentiate in \(t\): \(\frac{dp}{dt} = \frac{7}{4}\frac{dx}{dt}\).
   check: diff(7*x/4, x) = 7/4
5. [calc1.related-rates.values-at-instant] At the instant: the relation is linear, so the rate does not depend on \(x = 20\). Substitute \(\frac{dx}{dt} = 4\): \(\frac{dp}{dt} = \frac{7}{4}\cdot 4 = 7\).
   check: 7/4*4 = 7
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dp}{dt} = 7\) ft/s, positive, so the tip moves away from the post at 7 ft/s, faster than the woman. A direct check: with \(x = 20 + 4t\) and \(p = \frac{7x}{4}\), the slope of \(p\) at \(t = 0\) is the same number.
   check: subs(diff(7*(20 + 4*t)/4, t), t, 0) = 7

<!-- tier 3, template: one ship approaches the harbor, the other leaves it -->
## Card calc1.4-1.translate-ships.t01
skill: calc1.related-rates.translate
uses: pre.geometry.pythagorean, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear
difficulty: 3
answer-type: number
vars: u = int(12, 20); w = int(6, 14)
answer: (24*u - 7*w)/25
wrong: (24*u + 7*w)/25 => Ship B is sailing toward the harbor, so its distance north of the harbor is decreasing and its rate is negative. @0; u - w => The ships are not on one line. Use the distance s between them: if x and y are the distances of the ships from the harbor, then s^2 = x^2 + y^2. @1; -(24*u - 7*w)/25 => The distance between the ships is increasing, so the rate is positive. @5

### Question
Ship A is 24 km east of a harbor and sails east at [[u]] km/h. Ship B is 7 km north of the same harbor and sails south, toward the harbor, at [[w]] km/h. How fast is the distance between the two ships changing at this instant? Give the rate in kilometers per hour.

### Answer
\(\dfrac{ds}{dt} = [[tex((24*u - 7*w)/25)]]\) km/h

### Solution
0. [calc1.related-rates.translate] Set up: let \(x\) be ship A's distance east of the harbor, \(y\) ship B's distance north of it, and \(s\) the distance between the ships, in kilometers, with \(t\) in hours. Ship A moves away, so \(\frac{dx}{dt} = +[[u]]\). Ship B moves toward the harbor, so \(y\) decreases and \(\frac{dy}{dt} = -[[w]]\). Wanted: \(\frac{ds}{dt}\) when \(x = 24\) and \(y = 7\).
   check: diff(24 + u*t, t) = u
   check: diff(7 - w*t, t) = -w
1. [pre.geometry.pythagorean] Geometry: the harbor and the two ships form a right triangle with legs \(x\) and \(y\) and hypotenuse \(s\), so \(s^2 = x^2 + y^2\). At this instant \(s = \sqrt{24^2 + 7^2} = 25\).
   check: sqrt(24^2 + 7^2) = 25
2. [calc1.related-rates.differentiate-time] Differentiate in \(t\): \(2s\,\frac{ds}{dt} = 2x\,\frac{dx}{dt} + 2y\,\frac{dy}{dt}\).
   check: diff(z^2, z) = 2*z
3. [calc1.related-rates.values-at-instant] At the instant, substitute \(s = 25\), \(x = 24\), \(y = 7\), \(\frac{dx}{dt} = [[u]]\), \(\frac{dy}{dt} = -[[w]]\): \(50\,\frac{ds}{dt} = 48([[u]]) + 14(-[[w]])\).
   check: 48*u + 14*(-w) = 48*u - 14*w
4. [alg.solve.linear] Solve for the rate: \(\frac{ds}{dt} = \frac{[[48*u - 14*w]]}{50} = \frac{[[24*u - 7*w]]}{25}\).
   check: solve(50*v - (48*u - 14*w), v) = {(24*u - 7*w)/25}
5. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{ds}{dt} = \frac{[[24*u - 7*w]]}{25}\) km/h, positive, so the ships are moving apart. A direct check: with \(x = 24 + [[u]]t\) and \(y = 7 - [[w]]t\), the slope of \(s = \sqrt{x^2 + y^2}\) at \(t = 0\) is the same number.
   check: subs(diff(sqrt((24 + u*t)^2 + (7 - w*t)^2), t), t, 0) = (24*u - 7*w)/25

<!-- tier 3: inflow and a leak make the net rate; a cone tank -->
## Card calc1.4-1.translate-tank-leak.001
skill: calc1.related-rates.translate
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles, calc1.related-rates.eliminate-variable, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear
difficulty: 3
answer-type: number
answer: 16/(9*pi)
wrong: 8/(3*pi) => The leak was ignored. The volume changes at the inflow rate minus the leak rate. @0; 32/(9*pi) => The leak removes water, so it is a negative rate. It is not added to the inflow. @0; 16/(3*pi) => Check the derivative of the volume formula: for the depth h, the derivative of pi h^3/12 is pi h^2/4. The factor 3 from the power is easy to drop. @4

### Question
A tank is a cone with its point at the bottom: it is 8 m tall and has a radius of 4 m at the top. Water runs in at a steady 6 cubic meters per minute, and the tank leaks at a steady 2 cubic meters per minute. How fast is the water level rising at the instant when the water is 3 m deep? Give the rate in meters per minute.

### Answer
\(\dfrac{dh}{dt} = \dfrac{16}{9\pi}\) m/min \(\approx 0.57\) m/min

### Solution
0. [calc1.related-rates.translate] Set up: let \(V\) be the volume of water in cubic meters, \(h\) its depth and \(r\) the radius of the water surface, in meters, with \(t\) in minutes. Water comes in, \(+6\), and leaks out, \(-2\), so \(\frac{dV}{dt} = 6 - 2 = 4\). Wanted: \(\frac{dh}{dt}\) when \(h = 3\).
   check: 6 - 2 = 4
1. [pre.geometry.area-volume-formulas] Formula: the water fills a cone, whose volume is \(V = \frac{1}{3}\pi r^2 h\). At the instant, \(r = 1.5\) and \(h = 3\) give \(V = \frac{9\pi}{4}\).
   check: 1/3*pi*(3/2)^2*3 = 9*pi/4
2. [pre.geometry.similar-triangles] Similar triangles: the water's cross-section is similar to the whole tank, so \(\frac{r}{h} = \frac{4}{8}\), that is \(r = \frac{h}{2}\).
   check: (h/2)/h = 4/8
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\), whose rate is not given: \(V = \frac{1}{3}\pi\left(\frac{h}{2}\right)^2 h = \frac{\pi h^3}{12}\).
   check: 1/3*pi*(h/2)^2*h = pi*h^3/12
4. [calc1.related-rates.differentiate-time] Differentiate in \(t\): \(\frac{dV}{dt} = \frac{\pi h^2}{4}\frac{dh}{dt}\).
   check: diff(pi*h^3/12, h) = pi*h^2/4
5. [calc1.related-rates.values-at-instant] At the instant \(h = 3\): \(\frac{\pi h^2}{4} = \frac{9\pi}{4}\), so \(4 = \frac{9\pi}{4}\frac{dh}{dt}\).
   check: pi*3^2/4 = 9*pi/4
6. [alg.solve.linear] Solve for the rate: \(\frac{dh}{dt} = \frac{16}{9\pi}\).
   check: solve(4 - 9*pi/4*v, v) = {16/(9*pi)}
7. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dh}{dt} = \frac{16}{9\pi}\) m/min, positive, so the level is rising at about \(0.57\) m/min. A direct check: with \(V = \frac{9\pi}{4} + 4t\) and \(h = \left(\frac{12V}{\pi}\right)^{1/3}\), the slope of \(h\) at \(t = 0\) is the same number.
   check: subs(diff((12*(9*pi/4 + 4*t)/pi)^(1/3), t), t, 0) = 16/(9*pi)

<!-- tier 4: the given rate belongs to the area, the instant to the circumference -->
## Card calc1.4-1.translate-slick.001
skill: calc1.related-rates.translate
uses: pre.geometry.area-volume-formulas, calc1.related-rates.eliminate-variable, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear
difficulty: 4
answer-type: number
answer: pi/4
wrong: 1/8 => That is the rate at which the radius grows. The question asks how fast the circumference grows, which is 2 pi times as fast. @0; 5 => 5 m^2/min is the given rate of the area. The question asks how fast the circumference grows. @0

### Question
An oil slick spreads over calm water in the shape of a circle, and its area grows at a steady 5 square meters per minute. How fast is the circumference of the slick growing at the instant when the circumference is 40 m? Give the rate in meters per minute.

### Answer
\(\dfrac{dC}{dt} = \dfrac{\pi}{4}\) m/min \(\approx 0.79\) m/min

### Solution
0. [calc1.related-rates.translate] Set up: let \(A\) be the area in square meters, \(C\) the circumference and \(r\) the radius in meters, with \(t\) in minutes. Given \(\frac{dA}{dt} = 5\), positive since the slick spreads. Wanted \(\frac{dC}{dt}\) at the instant \(C = 40\). The given rate and the instant belong to different quantities.
   check: diff(400/pi + 5*t, t) = 5
1. [pre.geometry.area-volume-formulas] Formulas: a circle of radius \(r\) has area \(A = \pi r^2\) and circumference \(C = 2\pi r\).
   check: pi*3^2 = 9*pi
2. [calc1.related-rates.eliminate-variable] Eliminate \(r\), whose rate is not given, to link \(C\) and \(A\) directly: \(r = \frac{C}{2\pi}\), so \(A = \pi\left(\frac{C}{2\pi}\right)^2 = \frac{C^2}{4\pi}\).
   check: pi*(C/(2*pi))^2 = C^2/(4*pi)
3. [calc1.related-rates.differentiate-time] Differentiate in \(t\): \(\frac{dA}{dt} = \frac{C}{2\pi}\frac{dC}{dt}\).
   check: diff(C^2/(4*pi), C) = C/(2*pi)
4. [calc1.related-rates.values-at-instant] At the instant: with \(C = 40\) the factor is \(\frac{C}{2\pi} = \frac{20}{\pi}\), so \(5 = \frac{20}{\pi}\frac{dC}{dt}\).
   check: 40/(2*pi) = 20/pi
5. [alg.solve.linear] Solve for the rate: \(\frac{dC}{dt} = \frac{5\pi}{20} = \frac{\pi}{4}\).
   check: solve(5 - 20/pi*v, v) = {pi/4}
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dC}{dt} = \frac{\pi}{4}\) m/min, positive, so the circumference grows at about \(0.79\) m/min. A direct check: with \(A = \frac{400}{\pi} + 5t\) and \(C = 2\sqrt{\pi A}\), the slope of \(C\) at \(t = 0\) is the same number.
   check: subs(diff(2*sqrt(pi*(400/pi + 5*t)), t), t, 0) = pi/4

<!-- tier 4: the leak depends on the changing surface, so the net rate depends on the instant -->
## Card calc1.4-1.translate-leaky-balloon.001
skill: calc1.related-rates.translate
uses: pre.geometry.area-volume-formulas, calc1.related-rates.relate, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear
difficulty: 4
answer-type: number
answer: 1/pi - 1/10
wrong: 1/pi => The leak was ignored. Air escapes through the surface, so the volume grows more slowly than the pump alone would make it. @2; 1/pi + 1/10 => The leak removes air, so it enters the balance with a minus sign. @2

### Question
A spherical balloon is inflated by a pump that delivers 100 cubic centimeters of air per second. The balloon is slightly porous: air escapes through its surface at 0.1 cubic centimeters per second for every square centimeter of surface area. How fast is the radius growing at the instant when the radius is 5 cm? Give the rate in centimeters per second.

### Answer
\(\dfrac{dr}{dt} = \dfrac{1}{\pi} - \dfrac{1}{10}\) cm/s \(\approx 0.22\) cm/s

### Solution
0. [calc1.related-rates.translate] Set up: let \(V\) be the volume in cubic centimeters, \(S\) the surface area in square centimeters and \(r\) the radius in centimeters, with \(t\) in seconds. Air enters at \(+100\) and escapes at \(-0.1\,S\), so the rate of the volume depends on the surface, which changes. Wanted: \(\frac{dr}{dt}\) when \(r = 5\).
   check: 100 - 1/10*4*pi*5^2 = 100 - 10*pi
1. [pre.geometry.area-volume-formulas] Formulas: a sphere has volume \(V = \frac{4}{3}\pi r^3\) and surface area \(S = 4\pi r^2\).
   check: 4/3*pi*3^3 = 36*pi
2. [calc1.related-rates.relate] Relate the flows to the volume: the volume grows by what comes in minus what escapes, \(\frac{dV}{dt} = 100 - 0.1\,S = 100 - 0.4\pi r^2\) at every time.
   check: 1/10*4*pi*r^2 = 2*pi*r^2/5
3. [calc1.related-rates.differentiate-time] Differentiate \(V = \frac{4}{3}\pi r^3\) in \(t\): \(\frac{dV}{dt} = 4\pi r^2\,\frac{dr}{dt}\).
   check: diff(4/3*pi*r^3, r) = 4*pi*r^2
4. [calc1.related-rates.values-at-instant] At the instant \(r = 5\): the leak is \(0.4\pi(25) = 10\pi\), so \(\frac{dV}{dt} = 100 - 10\pi\), and \(4\pi r^2 = 100\pi\). Then \(100\pi\,\frac{dr}{dt} = 100 - 10\pi\).
   check: 2*pi*5^2/5 = 10*pi
5. [alg.solve.linear] Solve for the rate: \(\frac{dr}{dt} = \frac{100 - 10\pi}{100\pi} = \frac{1}{\pi} - \frac{1}{10}\).
   check: solve(100*pi*v - (100 - 10*pi), v) = {1/pi - 1/10}
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dr}{dt} = \frac{1}{\pi} - \frac{1}{10}\) cm/s \(\approx 0.22\) cm/s, positive, so the balloon is still growing. A direct check: with \(V = \frac{500\pi}{3} + (100 - 10\pi)t\) and \(r = \left(\frac{3V}{4\pi}\right)^{1/3}\), the slope of \(r\) at \(t = 0\) is the same number.
   check: subs(diff((3*(500*pi/3 + (100 - 10*pi)*t)/(4*pi))^(1/3), t), t, 0) = 1/pi - 1/10


<!-- ===================================================================== -->
<!-- calc1.select.related-rates-relation                                   -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-1.select-example.001
kind: example
skill: calc1.select.related-rates-relation

### Question
Water is poured at a steady rate into a tank shaped like a cone with its point down. The wanted rate is how fast the depth of the water is rising. Which relations link the changing quantities, and why?

### Solution
0. [calc1.select.related-rates-relation] Set up: name the changing quantities before choosing anything. They are the volume of the water, the depth of the water and the radius of the water's surface. The given rate belongs to the volume and the wanted rate to the depth.
1. [calc1.select.related-rates-relation] Choose: the volume of a cone links the volume to the radius and the depth, so a volume formula is needed. The radius and the depth are tied together because the cone of water is similar to the whole tank, so similar triangles are needed to get rid of the radius. No hypotenuse that matters appears and no angle is involved, so the Pythagorean theorem and a trig ratio are not needed.

<!-- tier 1, template: two legs of a right triangle -->
## Card calc1.4-1.select-ladder.t01
kind: method
skill: calc1.select.related-rates-relation
difficulty: 1
answer-type: choice
vars: L = int(10, 30)

### Question
A [[L]] ft ladder leans against a vertical wall, and its foot slides away from the wall. The foot's distance from the wall and the height of the ladder's top are both changing. Which relation links these two quantities?

### Choices
- [ ] An area or volume formula
- [x] The Pythagorean theorem
- [ ] Similar triangles
- [ ] A trig ratio in a right triangle

### Solution
0. [calc1.select.related-rates-relation] Set up: the ladder, the wall and the ground form a right triangle. The ladder is the hypotenuse and has a constant length, and the two changing quantities are the legs, so the relation is the Pythagorean theorem.

<!-- tier 1: a volume formula links volume and radius -->
## Card calc1.4-1.select-sphere.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 1
answer-type: choice

### Question
Air is pumped into a spherical balloon, so its volume and its radius both grow. Which relation links the volume to the radius?

### Choices
- [ ] Similar triangles
- [ ] The Pythagorean theorem
- [x] An area or volume formula
- [ ] A trig ratio in a right triangle

### Solution
0. [calc1.select.related-rates-relation] Set up: the two changing quantities are a volume and a length of the same sphere, and there is no triangle in the picture. A volume formula, the volume of a sphere in terms of its radius, links them.

<!-- tier 1: similar triangles link a shadow to a distance -->
## Card calc1.4-1.select-shadow.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 1
answer-type: choice

### Question
A student walks away from a lamp post on level ground, and her shadow gets longer. Which relation links the length of her shadow to her distance from the post?

### Choices
- [ ] The Pythagorean theorem
- [ ] An area or volume formula
- [ ] A trig ratio in a right triangle
- [x] Similar triangles

### Solution
0. [calc1.select.related-rates-relation] Set up: the lamp with the post and the student with her shadow form two right triangles with the same angle at the tip of the shadow. They are similar, so the lengths are linked by equal ratios of corresponding sides.

<!-- tier 2, template: an angle is wanted, so a trig ratio -->
## Card calc1.4-1.select-kite.t01
kind: method
skill: calc1.select.related-rates-relation
difficulty: 2
answer-type: choice
vars: h = int(30, 60)

### Question
A kite flies at a constant height of [[h]] m while the wind carries it away from the person holding the string, who stands on level ground. The kite's horizontal distance from the person is growing. The wanted rate is how fast the angle between the string and the ground is changing. Which relation links that angle to the horizontal distance?

### Choices
- [x] A trig ratio in a right triangle
- [ ] The Pythagorean theorem
- [ ] An area or volume formula
- [ ] Similar triangles

### Solution
0. [calc1.select.related-rates-relation] Set up: the angle is an angle of a right triangle whose sides are the height, the horizontal distance and the string. The height is constant and the horizontal distance changes, so the tangent of the angle, the ratio of those two sides, is the relation. The Pythagorean theorem would link the lengths, not the angle.

<!-- tier 2: a plane over a station -->
## Card calc1.4-1.select-plane.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 2
answer-type: choice

### Question
A plane flies at a constant altitude of 4 km along a straight line that passes directly over a radar station. The wanted rate is how fast the distance from the station to the plane is changing at a moment when the plane is a given horizontal distance from the point directly above the station. Which relation links the changing quantities?

### Choices
- [ ] A trig ratio in a right triangle
- [x] The Pythagorean theorem
- [ ] Similar triangles
- [ ] An area or volume formula

### Solution
0. [calc1.select.related-rates-relation] Set up: the altitude, the horizontal distance and the distance to the station are the three sides of a right triangle. Two lengths change and one is constant, and no angle is asked for, so the relation is the Pythagorean theorem.

<!-- tier 2: the radius is given in terms of the height, so only a volume formula is needed -->
## Card calc1.4-1.select-pile.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 2
answer-type: choice

### Question
Grain pours from a chute onto a barn floor and forms a pile shaped like a cone whose height is always equal to the diameter of its base. The wanted rate is how fast the height of the pile is growing. Which relation links the volume of the pile to its dimensions?

### Choices
- [ ] The Pythagorean theorem
- [ ] A trig ratio in a right triangle
- [x] An area or volume formula
- [ ] Similar triangles

### Solution
0. [calc1.select.related-rates-relation] Set up: the given rate belongs to the volume and the wanted rate to the height, so the first relation must link a volume to lengths: the volume of a cone. The statement that the height equals the diameter already links the radius and the height, so no triangles are needed.

<!-- tier 2: radius and depth of a cone of water -->
## Card calc1.4-1.select-funnel.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 2
answer-type: choice

### Question
Water drains from a funnel shaped like a cone with its point at the bottom. As it drains, the depth of the water and the radius of its surface both shrink. Which relation links the radius of the water's surface to the depth of the water?

### Choices
- [ ] An area or volume formula
- [ ] A trig ratio in a right triangle
- [ ] The Pythagorean theorem
- [x] Similar triangles

### Solution
0. [calc1.select.related-rates-relation] Set up: a vertical slice through the funnel shows a large right triangle (the funnel) and a smaller right triangle (the water) with the same angle at the point. The triangles are similar, so the ratio of the surface radius to the depth equals the ratio of the funnel's rim radius to its height.

<!-- tier 3: two relations are needed together -->
## Card calc1.4-1.select-cone-tank.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 3
answer-type: choice

### Question
Water is pumped into a tank shaped like a cone with its point down. The given rate is how fast the volume of water grows, and the wanted rate is how fast the depth of the water rises. Which relations are needed to link the volume to the depth? Select all that apply.

### Choices
- [x] An area or volume formula
- [ ] The Pythagorean theorem
- [x] Similar triangles
- [ ] A trig ratio in a right triangle

### Solution
0. [calc1.select.related-rates-relation] Set up: the volume of a cone involves both the radius and the depth, so a volume formula is needed. The radius is not part of the question, and it is tied to the depth by the similar triangles of the tank and the water. The Pythagorean theorem and a trig ratio have nothing to link here.

<!-- tier 3, template: a triangular trough needs a volume formula and similar triangles -->
## Card calc1.4-1.select-trough.t01
kind: method
skill: calc1.select.related-rates-relation
difficulty: 3
answer-type: choice
vars: L = int(3, 6); w = int(2, 5); d = int(1, 3)

### Question
A horizontal trough is [[L]] m long. Its cross-section is an isosceles triangle with its point at the bottom, [[w]] m wide at the top and [[d]] m deep. Water is poured in at a steady rate, and the wanted rate is how fast the depth of the water is rising. Which relations are needed to link the volume of water to its depth? Select all that apply.

### Choices
- [ ] A trig ratio in a right triangle
- [x] An area or volume formula
- [ ] The Pythagorean theorem
- [x] Similar triangles

### Solution
0. [calc1.select.related-rates-relation] Set up: the water forms a triangular prism, so a volume formula, the area of the triangular end times the length, links the volume to the water's width and depth. The width of the water's surface is not part of the question, and it is tied to the depth by the similar triangles of the trough's cross-section and the water's cross-section.

<!-- tier 3: the rope is the hypotenuse -->
## Card calc1.4-1.select-boat.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 3
answer-type: choice

### Question
A boat is pulled toward a dock by a rope that runs from the dock's edge to a ring on the boat's bow, 2 m below the edge. The rope is hauled in at a steady rate. The wanted rate is how fast the boat moves toward the dock. Which relation links the length of the rope to the boat's horizontal distance from the dock?

### Choices
- [ ] Similar triangles
- [x] The Pythagorean theorem
- [ ] A trig ratio in a right triangle
- [ ] An area or volume formula

### Solution
0. [calc1.select.related-rates-relation] Set up: the rope is the hypotenuse of a right triangle whose legs are the horizontal distance to the dock and the constant vertical drop. The rope's length and the horizontal distance change together, and no angle is involved, so the relation is the Pythagorean theorem.

<!-- tier 4: an unfamiliar setup: the volume stays constant -->
## Card calc1.4-1.select-box.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 4
answer-type: choice

### Question
A closed box has a square base. A machine slowly squeezes it so that the side of the base grows while the height shrinks, and the volume of the box never changes. The wanted rate is how fast the height is shrinking at the moment when the base side has a given length. Which relation links the changing quantities?

### Choices
- [ ] The Pythagorean theorem
- [ ] Similar triangles
- [ ] A trig ratio in a right triangle
- [x] An area or volume formula

### Solution
0. [calc1.select.related-rates-relation] Set up: the changing quantities are the base side and the height of one box, and the one fact that ties them together is that the volume of a box, the base area times the height, has a fixed value. There is no triangle in the problem, so a volume formula is the relation. The volume is constant, so its rate is zero.

<!-- tier 4: the given rate is an angular rate -->
## Card calc1.4-1.select-laser.001
kind: method
skill: calc1.select.related-rates-relation
difficulty: 4
answer-type: choice

### Question
A laser pointer on a stand turns at a steady rate, and its dot sweeps along a straight wall 3 m from the stand. The wanted rate is how fast the dot is moving along the wall at the moment when the beam makes a given angle with the line from the stand perpendicular to the wall. Which relation links the dot's position along the wall to the angle of the beam?

### Choices
- [x] A trig ratio in a right triangle
- [ ] An area or volume formula
- [ ] Similar triangles
- [ ] The Pythagorean theorem

### Solution
0. [calc1.select.related-rates-relation] Set up: the stand, the foot of the perpendicular on the wall and the dot form a right triangle with a fixed side of 3 m. The dot's position is the side opposite the beam's angle, and the given rate belongs to that angle, so the relation is the tangent of the angle, the opposite side over the fixed adjacent side.


<!-- ===================================================================== -->
<!-- calc1.related-rates.relate                                            -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-1.relate-example.001
kind: example
skill: calc1.related-rates.relate
uses: pre.geometry.area-volume-formulas, calc1.related-rates.translate, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant

### Question
A pebble dropped into a pond makes a circular ripple whose radius grows at a steady 3 cm/s. How fast is the area inside the ripple growing at the instant when the radius is 10 cm?

### Solution
0. [calc1.related-rates.relate] Set up: the ripple has an area and a radius, and both change with time. To link them, look for a fact about the shape that stays true at every moment, not only at the instant in the question.
1. [pre.geometry.area-volume-formulas] Formula: the ripple stays a circle, and a circle of radius \(r\) has area \(\pi r^2\). For \(r = 3\) that is \(9\pi\).
   check: pi*3^2 = 9*pi
2. [calc1.related-rates.relate] Relate: let \(A\) be the area in square centimeters and \(r\) the radius in centimeters, both functions of the time \(t\) in seconds. Then \(A = \pi r^2\) at every time. Here \(\pi\) is a constant, while \(A\) and \(r\) change. At the instant \(r = 10\), the area is \(100\pi\).
   check: pi*10^2 = 100*pi
3. [calc1.related-rates.translate] Given and wanted: the radius is growing, so \(\frac{dr}{dt} = +3\) cm/s, and the wanted rate is \(\frac{dA}{dt}\) at the instant \(r = 10\).
   check: diff(10 + 3*t, t) = 3
4. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(\frac{dA}{dt} = 2\pi r\,\frac{dr}{dt}\).
   check: diff(pi*r^2, r) = 2*pi*r
5. [calc1.related-rates.values-at-instant] At the instant: substitute \(r = 10\) and \(\frac{dr}{dt} = 3\), giving \(\frac{dA}{dt} = 2\pi(10)(3) = 60\pi\).
   check: 2*pi*10*3 = 60*pi
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dA}{dt} = 60\pi\) cm\(^2\)/s, about \(188\) cm\(^2\)/s. It is positive, so the area is growing. A direct check: with \(r = 10 + 3t\), the slope of \(\pi r^2\) at \(t = 0\) is the same number.
   check: subs(diff(pi*(10 + 3*t)^2, t), t, 0) = 60*pi

<!-- tier 1: a volume formula is the whole relation -->
## Card calc1.4-1.relate-sphere.001
skill: calc1.related-rates.relate
uses: pre.geometry.area-volume-formulas
difficulty: 1
answer-type: expression
answer: 4/3*pi*r^3
wrong: 4*pi*r^2 => That is the surface area of a sphere. The volume is four thirds of pi times r cubed. @1

### Question
Air is pumped into a spherical balloon. At each moment it has radius \(r\) cm and volume \(V\) cm\(^3\), and both change with time. Write \(V\) in terms of \(r\).

### Answer
\(V = \dfrac{4}{3}\pi r^3\) cm\(^3\)

### Solution
0. [calc1.related-rates.relate] Set up: the problem has two changing quantities, so one equation must link them, and the balloon stays a sphere the whole time.
1. [pre.geometry.area-volume-formulas] Formula: the volume of a sphere of radius \(r\) is \(\frac{4}{3}\pi r^3\). For \(r = 3\) it is \(36\pi\).
   check: 4/3*pi*3^3 = 36*pi
2. [calc1.related-rates.relate] Relate: the formula holds at every time, so \(V = \frac{4}{3}\pi r^3\). Here \(V\) and \(r\) change, and \(\frac{4}{3}\pi\) is constant.
   check: 4*pi*r^3/3 = 4/3*pi*r^3

<!-- tier 1, template: which equation holds for a sliding ladder -->
## Card calc1.4-1.relate-ladder.t01
skill: calc1.related-rates.relate
uses: pre.geometry.pythagorean
difficulty: 1
answer-type: choice
vars: L = int(10, 30)

### Question
A [[L]] ft ladder leans against a vertical wall. Let \(x\) be the distance in feet from the wall to the foot of the ladder and \(y\) the height in feet of its top. Which equation holds at every moment as the ladder slides?

### Choices
- [ ] \(x + y = [[L]]\)
- [x] \(x^2 + y^2 = [[L^2]]\)
- [ ] \(x^2 + y^2 = [[L]]\)
- [ ] \(x^2 - y^2 = [[L^2]]\)

### Solution
0. [calc1.related-rates.relate] Set up: the ladder keeps its length while its foot and its top move, so the equation must link the two changing distances and use the fixed length.
1. [pre.geometry.pythagorean] Geometry: the wall, the ground and the ladder form a right triangle whose hypotenuse is the ladder. With the ladder lying flat on the ground, \(x = [[L]]\) and \(y = 0\).
   check: L^2 + 0^2 = L^2
2. [calc1.related-rates.relate] Relate: the squares of the two legs add up to the square of the ladder's length at every time, so \(x^2 + y^2 = [[L^2]]\). With the ladder upright, \(x = 0\) and \(y = [[L]]\), which also fits.
   check: 0^2 + L^2 = L^2

<!-- tier 1: the distance between two cars -->
## Card calc1.4-1.relate-cars.001
skill: calc1.related-rates.relate
uses: pre.geometry.pythagorean
difficulty: 1
answer-type: expression
answer: sqrt(x^2 + y^2)
wrong: x + y => The distance between the cars is the hypotenuse of a right triangle, so it is not the sum of the two legs. @1

### Question
Car A is \(x\) miles east of an intersection and car B is \(y\) miles north of it, and both distances are changing. Write the straight-line distance \(s\) between the cars in terms of \(x\) and \(y\).

### Answer
\(s = \sqrt{x^2 + y^2}\) miles

### Solution
0. [calc1.related-rates.relate] Set up: the straight-line distance between the cars must be linked to their two changing distances from the intersection by one equation.
1. [pre.geometry.pythagorean] Geometry: the intersection and the two cars form a right triangle with legs \(x\) and \(y\), so \(s^2 = x^2 + y^2\). For \(x = 3\) and \(y = 4\) it gives \(s = 5\).
   check: sqrt(3^2 + 4^2) = 5
2. [calc1.related-rates.relate] Relate: \(s\) is positive, so \(s = \sqrt{x^2 + y^2}\) at every time.
   check: (x^2 + y^2)^(1/2) = sqrt(x^2 + y^2)

<!-- tier 2, template: the tangent of the angle of a kite string -->
## Card calc1.4-1.relate-kite.t02
skill: calc1.related-rates.relate
uses: trig.right-triangle.ratios
difficulty: 2
answer-type: expression
vars: h = int(30, 60)
answer: h/x
wrong: x/h => The tangent of an angle is the opposite side over the adjacent side. The height is opposite the angle. @1; h/sqrt(x^2 + h^2) => That is the sine of the angle. The tangent is the opposite side over the adjacent side. @1

### Question
A kite flies at a constant height of [[h]] m above the hands of the person holding the string. Let \(x\) be the kite's horizontal distance from that person, in meters, and \(\theta\) the angle between the string and the ground. Write \(\tan\theta\) in terms of \(x\).

### Answer
\(\tan\theta = \dfrac{[[h]]}{x}\)

### Solution
0. [calc1.related-rates.relate] Set up: the angle must be linked to the changing horizontal distance by one equation, and the height is a constant.
1. [trig.right-triangle.ratios] Ratio: the height, the horizontal distance and the string form a right triangle, and the height is the side opposite \(\theta\), so \(\tan\theta = \frac{\text{opposite}}{\text{adjacent}}\). At \(x = [[h]]\) the angle is \(45^\circ\), so \(\tan\theta = 1\).
   check: h/h = 1
2. [calc1.related-rates.relate] Relate: at every time, \(\tan\theta = \frac{[[h]]}{x}\). Here \(\theta\) and \(x\) change and \([[h]]\) is constant.
   check: h*(1/x) = h/x

<!-- tier 2, template: the proportion for a shadow, as a choice -->
## Card calc1.4-1.relate-shadow.t01
skill: calc1.related-rates.relate
uses: pre.geometry.similar-triangles
difficulty: 2
answer-type: choice
vars: H = int(12, 20); b = int(5, 6)

### Question
A lamp is mounted at the top of a [[H]] ft post. A person [[b]] ft tall stands \(x\) ft from the base of the post, and her shadow on level ground has length \(s\) ft. Which equation holds at every moment as she walks?

### Choices
- [ ] \(\dfrac{[[H]]}{x} = \dfrac{[[b]]}{s}\)
- [x] \(\dfrac{[[H]]}{x + s} = \dfrac{[[b]]}{s}\)
- [ ] \(\dfrac{[[H]]}{s} = \dfrac{[[b]]}{x + s}\)
- [ ] \([[H]] + [[b]] = x + s\)

### Solution
0. [calc1.related-rates.relate] Set up: the shadow's length and the person's distance from the post both change, and the two heights are constants, so one equation must link the shadow's length to the person's distance.
1. [pre.geometry.similar-triangles] Similar triangles: the triangle made by the lamp and the post and the triangle made by the person and her shadow have the same angle at the tip of the shadow. The tip is \(x + s\) from the post, so height over base agrees: \(\frac{[[H]]}{x + s} = \frac{[[b]]}{s}\).
   check: H*(b*x/(H - b)) = b*(x + b*x/(H - b))
2. [calc1.related-rates.relate] Relate: cross-multiplying, \([[H]]s = [[b]](x + s)\) at every time. The base of the large triangle is \(x + s\), not \(x\).
   check: subs(H*s - b*(x + s), s, b*x/(H - b)) = 0

<!-- tier 2: the radius of the water in a cone tank -->
## Card calc1.4-1.relate-cone-water.001
skill: calc1.related-rates.relate
uses: pre.geometry.similar-triangles
difficulty: 2
answer-type: expression
answer: 5*h/16
wrong: 16*h/5 => The ratio is inverted. The radius of the water's surface over its depth equals the rim radius over the tank's height, 5 over 16. @1; 5*h => The ratio of radius to depth is 5 over 16, not 5. @1

### Question
A tank is a cone with its point at the bottom, 16 ft deep and 5 ft in radius at the top. At a certain time the water has depth \(h\) ft and its surface is a circle of radius \(r\) ft. Write \(r\) in terms of \(h\).

### Answer
\(r = \dfrac{5h}{16}\) ft

### Solution
0. [calc1.related-rates.relate] Set up: the radius of the water's surface and its depth both change with time, so one equation must link them.
1. [pre.geometry.similar-triangles] Similar triangles: a vertical slice shows the water's triangle inside the tank's triangle with the same point and the same angle, so \(\frac{r}{h} = \frac{5}{16}\). Check at the full tank: \(h = 16\) gives \(r = 5\).
   check: 5*16/16 = 5
2. [calc1.related-rates.relate] Relate: at every time, \(r = \frac{5h}{16}\).
   check: h*5/16 = 5*h/16

<!-- tier 2: the rope is the hypotenuse -->
## Card calc1.4-1.relate-boat.001
skill: calc1.related-rates.relate
uses: pre.geometry.pythagorean
difficulty: 2
answer-type: expression
answer: sqrt(x^2 + 4)
wrong: x + 2 => The rope is the hypotenuse of a right triangle, so its length is not the sum of the two legs. @1; sqrt(x^2 - 4) => The rope is the hypotenuse, so it is longer than either leg: add the squares. @1

### Question
A boat is pulled toward a dock by a rope that runs from the edge of the dock to a ring on the boat's bow, 2 m below the edge. Let \(x\) be the boat's horizontal distance from the dock in meters and \(s\) the length of the rope in meters. Write \(s\) in terms of \(x\).

### Answer
\(s = \sqrt{x^2 + 4}\) m

### Solution
0. [calc1.related-rates.relate] Set up: the rope's length and the boat's distance from the dock both change, and the 2 m drop is a constant, so one equation must link them.
1. [pre.geometry.pythagorean] Geometry: the rope is the hypotenuse of a right triangle whose legs are the horizontal distance \(x\) and the vertical drop of 2 m. For \(x = 3\) the rope is \(\sqrt{13}\) m.
   check: sqrt(3^2 + 2^2) = sqrt(13)
2. [calc1.related-rates.relate] Relate: \(s^2 = x^2 + 4\), and \(s > 0\), so \(s = \sqrt{x^2 + 4}\) at every time.
   check: sqrt(x^2 + 2^2) = sqrt(x^2 + 4)

<!-- tier 3, template: the water surface in a hemispherical bowl -->
## Card calc1.4-1.relate-bowl.t01
skill: calc1.related-rates.relate
uses: pre.geometry.pythagorean, alg.expand.products
difficulty: 3
answer-type: expression
vars: R = int(6, 15)
domain: 0 < h < 6
answer: sqrt(2*R*h - h^2)
wrong: sqrt(R^2 - h^2) => The vertical leg of the right triangle is the distance [[R]] - h from the water up to the center of the sphere, not the depth h. @1; sqrt(2*R*h + h^2) => Check the sign when you expand: the middle term of ([[R]] - h)^2 is -[[2*R]]h. @2

### Question
A bowl is a hemisphere of radius [[R]] cm with its rim at the top. Water in the bowl has depth \(h\) cm, measured up from the lowest point, and its surface is a circle of radius \(r\) cm, where \(0 < h < [[R]]\). Write \(r\) in terms of \(h\).

### Answer
\(r = \sqrt{[[2*R]]h - h^2}\) cm

### Solution
0. [calc1.related-rates.relate] Set up: the radius of the water's surface and the depth of the water both change, and the bowl's radius is a constant, so one equation must link the surface radius and the depth.
1. [pre.geometry.pythagorean] Geometry: the bowl is half of a sphere whose center lies in the plane of the rim, a distance \([[R]] - h\) above the water's surface. A radius of the sphere to the edge of the water is the hypotenuse of a right triangle with legs \(r\) and \([[R]] - h\), so \(r^2 + ([[R]] - h)^2 = [[R^2]]\).
   check: sqrt(R^2 - (R - h)^2)^2 + (R - h)^2 = R^2
2. [alg.expand.products] Expand: \([[R^2]] - ([[R]] - h)^2 = [[2*R]]h - h^2\).
   check: expand(R^2 - (R - h)^2) = 2*R*h - h^2
3. [calc1.related-rates.relate] Relate: \(r\) is positive, so \(r = \sqrt{[[2*R]]h - h^2}\) at every time.
   check: sqrt(R^2 - (R - h)^2) = sqrt(2*R*h - h^2)

<!-- tier 3, template: a rectangle inscribed in a circle -->
## Card calc1.4-1.relate-rectangle.t01
skill: calc1.related-rates.relate
uses: pre.geometry.pythagorean
difficulty: 3
answer-type: expression
vars: R = int(4, 13)
domain: 0 < x < 8
answer: sqrt(4*R^2 - x^2)
wrong: sqrt(R^2 - x^2) => The diagonal of the rectangle is a diameter of the circle, which is twice the radius, not the radius itself. @1; 2*R - x => The two sides do not add up to the diameter. The diagonal is the hypotenuse of a right triangle whose legs are the two sides. @1

### Question
A rectangle is inscribed in a circle of radius [[R]] cm, so all four of its corners lie on the circle. One side of the rectangle is \(x\) cm long and the adjacent side is \(y\) cm long, where \(0 < x < [[2*R]]\). Write \(y\) in terms of \(x\).

### Answer
\(y = \sqrt{[[4*R^2]] - x^2}\) cm

### Solution
0. [calc1.related-rates.relate] Set up: the two sides change together as the rectangle changes shape, and the circle is fixed, so one equation must link the two sides.
1. [pre.geometry.pythagorean] Geometry: the center of the circle is the center of the rectangle, so a diagonal passes through it and is a diameter, [[2*R]] cm long. The diagonal is the hypotenuse of a right triangle whose legs are the sides \(x\) and \(y\), so \(x^2 + y^2 = [[4*R^2]]\). A square inscribed in the circle has \(x = y = [[R]]\sqrt{2}\).
   check: (sqrt(2)*R)^2 + (sqrt(2)*R)^2 = 4*R^2
2. [calc1.related-rates.relate] Relate: \(y\) is positive, so \(y = \sqrt{[[4*R^2]] - x^2}\) at every time.
   check: sqrt((2*R)^2 - x^2) = sqrt(4*R^2 - x^2)

<!-- tier 3: a cylinder inside a cone -->
## Card calc1.4-1.relate-cylinder.001
skill: calc1.related-rates.relate
uses: pre.geometry.similar-triangles
difficulty: 3
answer-type: expression
domain: 0 < h < 12
answer: 6 - h/2
wrong: h/2 => That treats the cylinder like the water cone. The triangle that is similar to the whole cone is the small cone above the cylinder, whose height is 12 - h. @1; 2*(12 - h) => The ratio of radius to height is 6 over 12, which is one half, not 2. @1

### Question
A solid cone has base radius 6 cm and height 12 cm, with its base on a table. A cylinder of radius \(r\) cm and height \(h\) cm stands inside the cone with its base on the table and the rim of its top face touching the cone's slanted surface, where \(0 < h < 12\). Write \(r\) in terms of \(h\).

### Answer
\(r = 6 - \dfrac{h}{2}\) cm

### Solution
0. [calc1.related-rates.relate] Set up: the cylinder's radius and height change together as the cylinder changes shape, and the cone is fixed, so one equation must link them.
1. [pre.geometry.similar-triangles] Similar triangles: a vertical slice through the axis shows the small cone above the cylinder. It has height \(12 - h\) and base radius \(r\), and it has the same shape as the whole cone, whose height is \(12\) and base radius is \(6\). So \(\frac{r}{12 - h} = \frac{6}{12}\). When the cylinder is 6 cm tall, its radius is 3 cm.
   check: 3/(12 - 6) = 6/12
2. [calc1.related-rates.relate] Relate: multiplying by \(12 - h\), \(r = \frac{12 - h}{2} = 6 - \frac{h}{2}\) at every time.
   check: (12 - h)*6/12 = 6 - h/2

<!-- tier 4: a plank over a fence; similar triangles with a shifted base -->
## Card calc1.4-1.relate-plank.001
skill: calc1.related-rates.relate
uses: pre.geometry.similar-triangles, alg.solve.linear
difficulty: 4
answer-type: expression
domain: x > 3
answer: 3*x/(x - 3)
wrong: 3*x/(x + 3) => The base of the small triangle is x - 3, the part of the plank's foot distance that lies beyond the fence. @1; x*(x - 3)/3 => The proportion is inverted. The small triangle has height 3 and base x - 3, and the large triangle has height y and base x. @1

### Question
A fence 3 ft high stands 3 ft away from the wall of a shed on level ground. A plank rests on the top of the fence. Its lower end is on the ground \(x\) ft from the wall, where \(x > 3\), and its upper end touches the wall at height \(y\) ft. Write \(y\) in terms of \(x\).

### Answer
\(y = \dfrac{3x}{x - 3}\) ft

### Solution
0. [calc1.related-rates.relate] Set up: seen from the side, the plank is a straight line from the ground to the wall that passes through the top of the fence. So the plank's foot and its upper end move together, and the fence's numbers are constants.
1. [pre.geometry.similar-triangles] Similar triangles: the small triangle under the plank, between the fence and the plank's foot, has height 3 and base \(x - 3\). The large triangle under the whole plank has height \(y\) and base \(x\). They share the angle at the foot, so \(\frac{3}{x - 3} = \frac{y}{x}\). For \(x = 6\) the plank reaches height \(6\).
   check: 3/(6 - 3) = 6/6
2. [calc1.related-rates.relate] Relate: the plank always touches the top of the fence, so the proportion \(\frac{3}{x - 3} = \frac{y}{x}\) holds at every time, with both \(x\) and \(y\) changing.
   check: 3/(x - 3) = (3*x/(x - 3))/x
3. [alg.solve.linear] Solve for \(y\): multiply both sides by \(x\), so \(y = \frac{3x}{x - 3}\).
   check: x*(3/(x - 3)) = 3*x/(x - 3)

<!-- tier 4: a trough whose sides slope outward -->
## Card calc1.4-1.relate-trough.001
skill: calc1.related-rates.relate
uses: trig.right-triangle.ratios, pre.geometry.area-volume-formulas
difficulty: 4
answer-type: expression
domain: h > 0
answer: 4*h + 4*h^2
wrong: 4*h => The cross-section is not a rectangle: the surface of the water is wider than the bottom. @2; 4*h + 2*h^2 => The surface is wider than the bottom by h on each side, so its width is 1 + 2h, not 1 + h. @1

### Question
A horizontal trough is 4 m long. Its cross-section is an isosceles trapezoid that is 1 m wide at the bottom, and each sloping side makes an angle of \(45^\circ\) with the vertical. Water of depth \(h\) m is in the trough. Write the volume \(V\) of the water, in cubic meters, in terms of \(h\).

### Answer
\(V = 4h + 4h^2\) m\(^3\)

### Solution
0. [calc1.related-rates.relate] Set up: the volume of water depends on the depth only, because the trough's length and the bottom width are constants, so one equation must link the volume and the depth.
1. [trig.right-triangle.ratios] Ratio: on each side, the vertical depth, the water's surface and the sloping side form a right triangle with a \(45^\circ\) angle at the bottom, so the horizontal leg is \(h\tan 45^\circ = h\). The water's surface is therefore \(1 + 2h\) wide.
   check: subs(h*tan(x), x, pi/4) = h
   check: 1 + h + h = 1 + 2*h
2. [pre.geometry.area-volume-formulas] Formula: a trapezoid has area equal to the average of its parallel sides times the distance between them, so the water's cross-section is \(\frac{1 + (1 + 2h)}{2}\,h = h + h^2\). The volume is that area times the length, 4.
   check: (1 + (1 + 2*h))/2*h = h + h^2
3. [calc1.related-rates.relate] Relate: \(V = 4(h + h^2) = 4h + 4h^2\) at every time.
   check: 4*(h + h^2) = 4*h + 4*h^2

<!-- ===================================================================== -->
<!-- calc1.related-rates.eliminate-variable                                -->
<!-- ===================================================================== -->

<!-- worked example -->
## Card calc1.4-1.eliminate-example.001
kind: example
skill: calc1.related-rates.eliminate-variable
uses: calc1.related-rates.translate, pre.geometry.area-volume-formulas, calc1.related-rates.relate, pre.geometry.similar-triangles, calc1.related-rates.differentiate-time, calc1.related-rates.values-at-instant, alg.solve.linear

### Question
Water is pumped into a conical tank at a steady 10 ft\(^3\)/min. The tank has its point at the bottom, is 12 ft deep and is 4 ft in radius at the top. How fast is the water level rising at the instant when the water is 6 ft deep?

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume of the water depends on the radius of its surface and on its depth. The rate of the volume is given and the rate of the depth is wanted, but no rate is given for the radius. So before differentiating, remove the radius, so that the volume depends on the depth alone.
1. [calc1.related-rates.translate] Given and wanted: let \(V\) be the volume of water in ft\(^3\), \(r\) the radius of the water's surface in ft and \(h\) the depth in ft, all functions of the time \(t\) in minutes. Water is pumped in, so \(\frac{dV}{dt} = +10\), and the wanted rate is \(\frac{dh}{dt}\) at the instant \(h = 6\).
   check: diff(10*t, t) = 10
2. [pre.geometry.area-volume-formulas] Formula: a cone of radius \(r\) and height \(h\) holds \(\frac{1}{3}\pi r^2 h\). A cone of radius 3 and height 6 holds \(18\pi\).
   check: 1/3*pi*3^2*6 = 18*pi
3. [calc1.related-rates.relate] Relate: the water is a cone whose radius and depth both change, so \(V = \frac{1}{3}\pi r^2 h\) at every time. At the instant \(h = 6\) the radius is \(2\), and the volume is \(8\pi\).
   check: 1/3*pi*2^2*6 = 8*pi
4. [pre.geometry.similar-triangles] Similar triangles: in a vertical slice, the water's triangle has the same point and the same angle as the tank's triangle, so \(\frac{r}{h} = \frac{4}{12}\), that is \(r = \frac{h}{3}\). At the full tank, \(h = 12\) gives \(r = 4\).
   check: 4/12*12 = 4
5. [calc1.related-rates.eliminate-variable] Eliminate \(r\): substitute \(r = \frac{h}{3}\) into the volume, so \(V = \frac{1}{3}\pi\left(\frac{h}{3}\right)^2 h = \frac{\pi}{27}h^3\).
   check: 1/3*pi*(h/3)^2*h = pi*h^3/27
6. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\): \(\frac{dV}{dt} = \frac{\pi}{9}h^2\,\frac{dh}{dt}\).
   check: diff(pi*h^3/27, h) = pi*h^2/9
7. [calc1.related-rates.values-at-instant] At the instant: substitute \(h = 6\) and \(\frac{dV}{dt} = 10\) into the differentiated equation, giving \(10 = \frac{\pi}{9}(6)^2\,\frac{dh}{dt} = 4\pi\,\frac{dh}{dt}\).
   check: pi/9*6^2 = 4*pi
8. [alg.solve.linear] Solve for the unknown rate: \(\frac{dh}{dt} = \frac{10}{4\pi} = \frac{5}{2\pi}\).
   check: solve(10 - 4*pi*v, v) = {5/(2*pi)}
9. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dh}{dt} = \frac{5}{2\pi}\) ft/min, about \(0.80\) ft/min. It is positive, so the level is rising. A direct check: if \(V = 8\pi + 10t\), then \(h = \sqrt[3]{27V/\pi}\), and its slope at \(t = 0\) is the same number.
   check: subs(diff((27*(8*pi + 10*t)/pi)^(1/3), t), t, 0) = 5/(2*pi)

<!-- tier 1, template: replace a length by a multiple of another -->
## Card calc1.4-1.eliminate-garden.t01
skill: calc1.related-rates.eliminate-variable
difficulty: 1
answer-type: expression
vars: k = int(2, 8)
answer: k*w^2
wrong: k*w => Replace only the length. The width stays as a factor, so the area is (k w)(w). @1

### Question
A rectangular garden bed is always built with its length [[k]] times its width. Its area is \(A = \ell w\) square meters, where \(\ell\) is the length and \(w\) the width, both in meters. Write \(A\) in terms of \(w\) alone.

### Answer
\(A = [[k]]w^2\) m\(^2\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the area depends on the length and the width, but the answer must use the width alone, so replace the length with what the problem says it always equals.
1. [calc1.related-rates.eliminate-variable] Eliminate the length: \(\ell = [[k]]w\), so \(A = ([[k]]w)\,w = [[k]]w^2\).
   check: (k*w)*w = k*w^2

<!-- tier 1: the constant in front of h^3 -->
## Card calc1.4-1.eliminate-pile.001
skill: calc1.related-rates.eliminate-variable
difficulty: 1
answer-type: number
answer: pi/12
wrong: pi/6 => The radius is half the height, so r squared is h squared over 4, not h squared over 2. @1; pi/3 => The radius is h/2, not h, so r squared is h squared over 4. @1

### Question
Grain poured from a chute onto a barn floor forms a pile in the shape of a cone whose radius is always half its height. The volume of a cone is \(V = \frac{1}{3}\pi r^2 h\), with \(r\) and \(h\) in meters and \(V\) in cubic meters. Eliminating \(r\) gives \(V = c\,h^3\) for a constant \(c\). Find \(c\).

### Answer
\(c = \dfrac{\pi}{12}\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume is given in terms of the radius and the height, and the radius is tied to the height, so replace the radius before reading off the constant.
1. [calc1.related-rates.eliminate-variable] Eliminate the radius: since \(r = \frac{h}{2}\), \(V = \frac{1}{3}\pi\left(\frac{h}{2}\right)^2 h = \frac{\pi}{12}h^3\), so \(c = \frac{\pi}{12}\).
   check: 1/3*pi*(h/2)^2*h = pi*h^3/12
   check: subs(pi*h^3/12, h, 1) = pi/12

<!-- tier 1, template: which substitution comes before differentiating -->
## Card calc1.4-1.eliminate-which.t01
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.similar-triangles
difficulty: 1
answer-type: choice
vars: a = int(3, 6); b = int(8, 16)

### Question
Water is poured into a cone-shaped tank with its point at the bottom. The tank is [[b]] ft deep and [[a]] ft in radius at the top. At a certain moment the water has depth \(h\) ft and its surface has radius \(r\) ft, so its volume is \(V = \frac{1}{3}\pi r^2 h\). The rate \(\frac{dV}{dt}\) is given and \(\frac{dh}{dt}\) is wanted. What should you do before differentiating with respect to \(t\)?

### Choices
- [x] Replace \(r\) by \(\frac{[[a]]}{[[b]]}h\), so that \(V\) is written in terms of \(h\) alone
- [ ] Replace \(r\) by [[a]], the radius of the tank, since the radius does not change
- [ ] Replace \(h\) by [[b]], the depth of the tank, since the depth does not change
- [ ] Nothing: differentiate \(V = \frac{1}{3}\pi r^2 h\) as it stands, treating \(r\) as a constant

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume formula has two changing lengths, the radius of the water's surface and its depth. A rate is given for the volume and wanted for the depth, so the radius has to be removed before differentiating. Neither the radius nor the depth of the water is constant.
1. [pre.geometry.similar-triangles] Similar triangles: the water's triangle in a vertical slice matches the tank's triangle, so \(\frac{r}{h} = \frac{[[a]]}{[[b]]}\), that is \(r = \frac{[[a]]}{[[b]]}h\). At the full tank, \(h = [[b]]\) gives \(r = [[a]]\).
   check: a/b*b = a
2. [calc1.related-rates.eliminate-variable] Eliminate \(r\): substituting gives \(V = \frac{1}{3}\pi\left(\frac{[[a]]}{[[b]]}h\right)^2 h\), which contains \(h\) alone.
   check: 1/3*pi*(a/b*h)^2*h = pi*a^2*h^3/(3*b^2)

<!-- tier 2, template: the volume of water in a cone in terms of its depth -->
## Card calc1.4-1.eliminate-cone-tank.t02
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles
difficulty: 2
answer-type: expression
vars: a = int(3, 6); b = int(8, 16)
answer: pi*a^2*h^3/(3*b^2)
wrong: pi*a^2*h^3/(3*b) => Square the whole ratio: the radius is ([[a]]/[[b]])h, so its square has [[b^2]] in the denominator, not [[b]]. @3; pi*b^2*h^3/(3*a^2) => The ratio is inverted. The radius of the water's surface over its depth equals the tank's top radius over the tank's depth. @2; pi*a^2*h/3 => The radius of the water's surface is not the tank's radius. It depends on the depth, so it has to be replaced. @3

### Question
A tank is a cone with its point at the bottom, [[b]] ft deep and [[a]] ft in radius at the top. Water in the tank has depth \(h\) ft and its surface is a circle of radius \(r\) ft. Write the volume \(V\) of the water, in cubic feet, in terms of \(h\) alone.

### Answer
\(V = [[tex(pi*a^2*h^3/(3*b^2))]]\) ft\(^3\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume of the water depends on the radius of its surface and on its depth, but the answer must use the depth alone, so the radius has to be replaced.
1. [pre.geometry.area-volume-formulas] Formula: a cone of radius \(r\) and height \(h\) holds \(\frac{1}{3}\pi r^2 h\). A cone of radius 3 and height 6 holds \(18\pi\).
   check: 1/3*pi*3^2*6 = 18*pi
2. [pre.geometry.similar-triangles] Similar triangles: the water's triangle matches the tank's triangle, so \(\frac{r}{h} = \frac{[[a]]}{[[b]]}\), that is \(r = \frac{[[a]]}{[[b]]}h\). At the full tank, \(h = [[b]]\) gives \(r = [[a]]\).
   check: a/b*b = a
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\): \(V = \frac{1}{3}\pi\left(\frac{[[a]]}{[[b]]}h\right)^2 h = [[tex(pi*a^2*h^3/(3*b^2))]]\).
   check: 1/3*pi*(a*h/b)^2*h = pi*a^2*h^3/(3*b^2)

<!-- tier 2, template: the tip of a shadow, with the shadow's length eliminated -->
## Card calc1.4-1.eliminate-tip.t01
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.similar-triangles, alg.solve.linear
difficulty: 2
answer-type: expression
vars: H = int(12, 20); b = int(5, 6)
answer: H*x/(H - b)
wrong: x + b*x/H => The large triangle's base is z, the distance from the post to the tip of the shadow, not x. @1; b*x/(H - b) => That is the length of the shadow. The question asks for the distance z from the post to the tip, which is x plus the shadow's length. @3

### Question
A lamp is mounted at the top of a [[H]] ft post. A woman [[b]] ft tall stands \(x\) ft from the base of the post on level ground. Let \(z\) be the distance in feet from the base of the post to the tip of her shadow. Write \(z\) in terms of \(x\) alone.

### Answer
\(z = [[tex(H*x/(H - b))]]\) ft

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the tip of the shadow is farther from the post than the woman is. The shadow's own length is a third quantity, so write the relation first and then remove the shadow's length, leaving the distance to the tip in terms of her distance from the post.
1. [pre.geometry.similar-triangles] Similar triangles: the lamp's triangle has height [[H]] and base \(z\), and the woman's triangle has height [[b]] and base \(s\), the length of her shadow. They share the angle at the tip, so \(\frac{[[H]]}{z} = \frac{[[b]]}{s}\).
   check: H/(H*x/(H - b)) = b/(b*x/(H - b))
2. [calc1.related-rates.eliminate-variable] Eliminate \(s\): the shadow runs from her to the tip, so \(s = z - x\) and the proportion becomes \(\frac{[[H]]}{z} = \frac{[[b]]}{z - x}\).
   check: H*x/(H - b) - x = b*x/(H - b)
3. [alg.solve.linear] Solve for \(z\): cross-multiplying gives \([[H]](z - x) = [[b]]z\), so \(([[H]] - [[b]])z = [[H]]x\) and \(z = \frac{[[H]]x}{[[H - b]]}\).
   check: H*(H*x/(H - b) - x) = b*(H*x/(H - b))
   check: x*H/(H - b) = H*x/(H - b)

<!-- tier 2: a rectangle under a parabola -->
## Card calc1.4-1.eliminate-rectangle.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas
difficulty: 2
answer-type: expression
answer: 2*x*(9 - x^2)
wrong: x*(9 - x^2) => The rectangle's base runs from -x to x, so its width is 2x, not x. @1; 2*x*(9 - x) => The curve is y = 9 - x^2, so replace y by 9 - x^2, with the square. @2

### Question
A rectangle has its base on the \(x\)-axis and its two upper corners on the parabola \(y = 9 - x^2\), at \((x, y)\) and \((-x, y)\), where \(0 < x < 3\). Write the area \(A\) of the rectangle in terms of \(x\) alone.

### Answer
\(A = 2x(9 - x^2)\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the area depends on both coordinates of the corner, but the answer must use the horizontal one alone, so replace the vertical one using the curve.
1. [pre.geometry.area-volume-formulas] Formula: the rectangle runs from \(-x\) to \(x\), so its width is \(2x\), and its height is \(y\). Its area is \(A = 2xy\). For \(x = 2\) and \(y = 5\), the area is \(20\).
   check: 2*2*5 = 20
2. [calc1.related-rates.eliminate-variable] Eliminate \(y\): the corner is on the parabola, so \(y = 9 - x^2\) and \(A = 2x(9 - x^2) = 18x - 2x^3\).
   check: subs(2*x*y, y, 9 - x^2) = 18*x - 2*x^3

<!-- tier 2: the distance to a bead on a curve -->
## Card calc1.4-1.eliminate-curve.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.pythagorean
difficulty: 2
answer-type: expression
answer: sqrt(x^2 + (x^2 - 4)^2)
wrong: sqrt(x^2 + (x^2 + 4)^2) => The vertical difference is y - 4, and y = x^2, so it is x^2 - 4. @2; sqrt(x^2 + (x - 4)^2) => Replace y by x^2, not by x. @2

### Question
A bead slides along a wire bent into the parabola \(y = x^2\), with \(x\) and \(y\) in meters. Let \(s\) be the distance in meters from the bead to the point \((0, 4)\). Write \(s\) in terms of \(x\) alone.

### Answer
\(s = \sqrt{x^2 + (x^2 - 4)^2}\) m

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the distance depends on both coordinates of the bead, but the answer must use the horizontal one alone, so replace the vertical one using the wire's curve.
1. [pre.geometry.pythagorean] Distance formula: \(s^2 = (x - 0)^2 + (y - 4)^2\). For the bead at \((3, 9)\) it gives \(s = \sqrt{34}\).
   check: sqrt((3 - 0)^2 + (9 - 4)^2) = sqrt(34)
2. [calc1.related-rates.eliminate-variable] Eliminate \(y\): the bead is on the curve, so \(y = x^2\) and \(s = \sqrt{x^2 + (x^2 - 4)^2}\).
   check: subs(sqrt(x^2 + (y - 4)^2), y, x^2) = sqrt(x^2 + (x^2 - 4)^2)

<!-- tier 3: a trough with triangular ends -->
## Card calc1.4-1.eliminate-trough.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles
difficulty: 3
answer-type: expression
answer: 10*h^2/3
wrong: 5*h => The width of the water's surface changes with the depth. Only the full trough is 2 m wide. @3; 15*h^2/8 => The ratio is inverted. The width of the surface over the depth equals the trough's top width over its depth, 2 over 1.5. @2; 20*h^2/3 => The water's cross-section is a triangle, so its area is half of base times height. @1

### Question
A horizontal trough is 5 m long. Its cross-section is an isosceles triangle with its point at the bottom, 2 m wide at the top and 1.5 m deep. Water in the trough has depth \(h\) m, and the surface of the water is \(w\) m wide. Write the volume \(V\) of the water, in cubic meters, in terms of \(h\) alone.

### Answer
\(V = \dfrac{10h^2}{3}\) m\(^3\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume of the water depends on the depth and on the width of its surface, but the answer must use the depth alone, so the width has to be replaced.
1. [pre.geometry.area-volume-formulas] Formula: the water's cross-section is a triangle with base \(w\) and height \(h\), so its area is \(\frac{1}{2}wh\). The volume is that area times the length 5, so \(V = \frac{5}{2}wh\). For \(w = 4\) and \(h = 3\) it is \(30\).
   check: 5/2*4*3 = 30
2. [pre.geometry.similar-triangles] Similar triangles: the water's triangle matches the cross-section of the trough, so \(\frac{w}{h} = \frac{2}{1.5} = \frac{4}{3}\), that is \(w = \frac{4h}{3}\). At the full depth, \(h = 1.5\) gives \(w = 2\).
   check: 4/3*(3/2) = 2
3. [calc1.related-rates.eliminate-variable] Eliminate \(w\): \(V = \frac{5}{2}\left(\frac{4h}{3}\right)h = \frac{10}{3}h^2\).
   check: 5/2*(4*h/3)*h = 10*h^2/3

<!-- tier 3: a cylinder inscribed in a sphere -->
## Card calc1.4-1.eliminate-cylinder-sphere.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.pythagorean
difficulty: 3
answer-type: expression
answer: pi*h*(25 - h^2/4)
wrong: pi*h*(25 - h^2) => The vertical leg of the right triangle is half the height, h/2, so its square is h^2/4. @2; pi*h*(5 - h/2)^2 => The square of the radius is 25 - (h/2)^2, found by subtracting inside the Pythagorean equation, not (5 - h/2)^2. @3

### Question
A solid cylinder of radius \(r\) cm and height \(h\) cm is inscribed in a sphere of radius 5 cm: the center of the cylinder is the center of the sphere, and the rim of each circular face lies on the sphere. Write the volume \(V\) of the cylinder, in cubic centimeters, in terms of \(h\) alone, where \(0 < h < 10\).

### Answer
\(V = \pi h\left(25 - \dfrac{h^2}{4}\right)\) cm\(^3\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume of the cylinder depends on its radius and its height, but the answer must use the height alone, so the radius has to be replaced using the sphere.
1. [pre.geometry.area-volume-formulas] Formula: a cylinder of radius \(r\) and height \(h\) holds \(V = \pi r^2 h\). For \(r = 3\) and \(h = 4\) it holds \(36\pi\).
   check: pi*3^2*4 = 36*pi
2. [pre.geometry.pythagorean] Geometry: in a slice through the axis, the radius of the sphere to a point on the rim is the hypotenuse of a right triangle with legs \(r\) and \(\frac{h}{2}\), so \(r^2 + \left(\frac{h}{2}\right)^2 = 25\). For \(h = 6\) it gives \(r = 4\).
   check: 4^2 + (6/2)^2 = 25
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\): the formula contains \(r^2\), which equals \(25 - \frac{h^2}{4}\), so \(V = \pi\left(25 - \frac{h^2}{4}\right)h\).
   check: pi*(25 - (h/2)^2)*h = pi*h*(25 - h^2/4)

<!-- tier 3, template: a cylinder inscribed in a cone -->
## Card calc1.4-1.eliminate-cylinder-cone.t03
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles
difficulty: 3
answer-type: expression
vars: a = int(4, 8); b = int(8, 16)
answer: pi*a^2*h*(b - h)^2/b^2
wrong: pi*a^2*h^3/b^2 => The cylinder is not similar to the whole cone. The triangle that is similar to the cone is the small cone above the cylinder, whose height is [[b]] - h. @2; pi*a*h*(b - h)^2/b^2 => The radius is [[a]]([[b]] - h)/[[b]], and the whole radius is squared in the volume, including the factor [[a]]. @3

### Question
A solid cone has base radius [[a]] cm and height [[b]] cm, with its base on a table. A cylinder of radius \(r\) cm and height \(h\) cm stands inside the cone with its base on the table and the rim of its top face touching the cone's slanted surface, where \(0 < h < [[b]]\). Write the volume \(V\) of the cylinder, in cubic centimeters, in terms of \(h\) alone.

### Answer
\(V = [[tex(pi*a^2*h*(b - h)^2/b^2)]]\) cm\(^3\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the volume of the cylinder depends on its radius and its height, but the answer must use the height alone, so the radius has to be replaced using the cone.
1. [pre.geometry.area-volume-formulas] Formula: a cylinder of radius \(r\) and height \(h\) holds \(V = \pi r^2 h\). For \(r = 3\) and \(h = 4\) it holds \(36\pi\).
   check: pi*3^2*4 = 36*pi
2. [pre.geometry.similar-triangles] Similar triangles: a vertical slice through the axis shows the small cone above the cylinder. It has height \([[b]] - h\) and base radius \(r\), and it has the same shape as the whole cone, so \(\frac{r}{[[b]] - h} = \frac{[[a]]}{[[b]]}\), that is \(r = \frac{[[a]]([[b]] - h)}{[[b]]}\). When the cylinder is half as tall as the cone, its radius is half the cone's radius.
   check: a*(b - b/2)/b = a/2
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\): \(V = \pi\left(\frac{[[a]]([[b]] - h)}{[[b]]}\right)^2 h = [[tex(pi*a^2*h*(b - h)^2/b^2)]]\).
   check: pi*(a*(b - h)/b)^2*h = pi*a^2*h*(b - h)^2/b^2

<!-- tier 4: a bucket that is a truncated cone -->
## Card calc1.4-1.eliminate-bucket.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.similar-triangles, pre.geometry.area-volume-formulas, calc1.related-rates.relate
difficulty: 4
answer-type: expression
answer: pi*(18 + h)^3/27 - 216*pi
wrong: pi*(18 + h)^3/27 => This is the cone that reaches down to the point, not the water. The small cone below the bucket's bottom has to be taken away. @4; pi*(6 + h/3)^2*h/3 => The water is not a cone with its point at the bottom of the bucket. Extend the sides down to a point and subtract the cone that is missing. @2

### Question
A bucket is a truncated cone: its bottom is a circle of radius 6 in, its top is a circle of radius 10 in, and it is 12 in tall. Water of depth \(h\) in is in the bucket, where \(0 < h < 12\). Write the volume \(V\) of the water, in cubic inches, in terms of \(h\) alone.

### Answer
\(V = \dfrac{\pi(18 + h)^3}{27} - 216\pi\) in\(^3\)

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: the water fills a truncated cone. Instead of recalling a formula for it, extend the bucket's sides down to a point to make a full cone, write the volume of the cone up to the water's surface in terms of the depth alone, and subtract the small cone below the bottom.
1. [pre.geometry.similar-triangles] Similar triangles: the radius grows by 4 in over a height of 12 in, that is 1 in for every 3 in. So the sides meet at a point 18 in below the bottom, and the radius at height \(y\) above that point is \(\frac{y}{3}\). The water's surface is at height \(18 + h\), so its radius is \(r = \frac{18 + h}{3}\). At the top of the bucket, \(h = 12\) gives \(r = 10\).
   check: (18 + 12)/3 = 10
2. [pre.geometry.area-volume-formulas] Formula: a cone of radius \(r\) and height \(H\) holds \(\frac{1}{3}\pi r^2 H\). The small cone below the bucket has radius 6 and height 18, so it holds \(216\pi\).
   check: 1/3*pi*6^2*18 = 216*pi
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\): the cone up to the water's surface has height \(18 + h\) and radius \(\frac{18 + h}{3}\), so its volume is \(\frac{1}{3}\pi\left(\frac{18 + h}{3}\right)^2(18 + h) = \frac{\pi(18 + h)^3}{27}\).
   check: 1/3*pi*((18 + h)/3)^2*(18 + h) = pi*(18 + h)^3/27
4. [calc1.related-rates.relate] Relate: the water is the big cone minus the small cone, so \(V = \frac{\pi(18 + h)^3}{27} - 216\pi\) at every time. Check at the top of the bucket: \(h = 12\) gives \(784\pi\), the same as the volume formula for a truncated cone, \(\frac{\pi \cdot 12}{3}(6^2 + 6 \cdot 10 + 10^2)\).
   check: pi*12/3*(6^2 + 6*10 + 10^2) = pi*(18 + 12)^3/27 - 216*pi
   check: pi*((18 + h)^3 - 5832)/27 = pi*(18 + h)^3/27 - 216*pi

<!-- tier 4: water conserved between a funnel and a jar -->
## Card calc1.4-1.eliminate-funnel.001
skill: calc1.related-rates.eliminate-variable
uses: pre.geometry.area-volume-formulas, pre.geometry.similar-triangles, calc1.related-rates.relate, alg.solve.linear
difficulty: 4
answer-type: expression
answer: 9 - h^3/192
wrong: 144 - h^3/12 => The jar's cross-section is a circle of area 16 pi, so the volume has to be divided by 16 pi to get a depth. @5; 9 - h^3/48 => The radius of the water's surface in the funnel is h/2, not h. @3

### Question
A cone-shaped funnel, point down, is 12 cm deep and 12 cm across at the top, and water leaves it through a tiny hole at the point. It starts full and drains into a cylindrical jar of radius 4 cm placed directly below it, which starts empty. No water is lost. At a certain moment the water in the funnel has depth \(h\) cm and the water in the jar has depth \(y\) cm. Write \(y\) in terms of \(h\) alone.

### Answer
\(y = 9 - \dfrac{h^3}{192}\) cm

### Solution
0. [calc1.related-rates.eliminate-variable] Set up: no water is lost, so the water in the funnel and the water in the jar always add up to the volume that was in the full funnel. Write each volume in terms of one depth, with the radius of the water's surface in the funnel removed, then solve for the depth in the jar.
1. [pre.geometry.area-volume-formulas] Formula: a cone of radius \(r\) and height \(h\) holds \(\frac{1}{3}\pi r^2 h\), and a cylinder of radius 4 and depth \(y\) holds \(16\pi y\). The full funnel has radius 6 and height 12, so it holds \(144\pi\).
   check: 1/3*pi*6^2*12 = 144*pi
2. [pre.geometry.similar-triangles] Similar triangles: the water in the funnel has the same shape as the funnel, so \(\frac{r}{h} = \frac{6}{12}\), that is \(r = \frac{h}{2}\).
   check: 6/12*12 = 6
3. [calc1.related-rates.eliminate-variable] Eliminate \(r\): the water in the funnel has volume \(\frac{1}{3}\pi\left(\frac{h}{2}\right)^2 h = \frac{\pi}{12}h^3\).
   check: 1/3*pi*(h/2)^2*h = pi*h^3/12
4. [calc1.related-rates.relate] Relate: the two volumes add up to the starting volume at every time, so \(\frac{\pi}{12}h^3 + 16\pi y = 144\pi\). At the start \(h = 12\) and \(y = 0\), which fits.
   check: pi*12^3/12 + 16*pi*0 = 144*pi
5. [alg.solve.linear] Solve for \(y\): \(16\pi y = 144\pi - \frac{\pi}{12}h^3\), so \(y = 9 - \frac{h^3}{192}\).
   check: solve(pi*h^3/12 + 16*pi*y - 144*pi, y) = {9 - h^3/192}
   check: (144*pi - pi*h^3/12)/(16*pi) = 9 - h^3/192

<!-- ===================================================================== -->
<!-- calc1.related-rates.differentiate-time                                -->
<!-- ===================================================================== -->
<!-- Rates in answers: the question names a letter for each rate (for example u for dx/dt),
     because the answer syntax has no derivative symbol. ### Answer shows the usual notation. -->

<!-- worked example -->
## Card calc1.4-1.time-example.001
kind: example
skill: calc1.related-rates.differentiate-time
uses: calc1.related-rates.translate, calc1.related-rates.relate, calc1.deriv.product-rule, calc1.related-rates.values-at-instant

### Question
The length of a rectangle is increasing at a steady 3 cm/s while its width is decreasing at a steady 2 cm/s. Is the area increasing or decreasing at the instant when the length is 12 cm and the width is 5 cm, and how fast?

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the area depends on the length and the width, and both change with time. To find the rate of the area, differentiate the relation with respect to time, so that every changing quantity brings its own rate.
1. [calc1.related-rates.translate] Given and wanted: let \(x\) be the length, \(y\) the width and \(A\) the area, in cm and cm\(^2\), all functions of the time \(t\) in seconds. The length is increasing, so \(\frac{dx}{dt} = +3\), and the width is decreasing, so \(\frac{dy}{dt} = -2\). The wanted rate is \(\frac{dA}{dt}\) at \(x = 12\), \(y = 5\).
   check: diff(12 + 3*t, t) = 3
   check: diff(5 - 2*t, t) = -2
2. [calc1.related-rates.relate] Relate: the area of a rectangle is the product of its sides, so \(A = xy\) at every time. At the instant, \(A = 60\).
   check: 12*5 = 60
3. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), with \(A\), \(x\) and \(y\) all functions of \(t\): \(\frac{dA}{dt} = \frac{d}{dt}(xy)\), where both factors have a rate.
   check: diff(x*y, x)*3 + diff(x*y, y)*(-2) = 3*y - 2*x
4. [calc1.deriv.product-rule] Product rule: \(\frac{d}{dt}(xy) = \frac{dx}{dt}\,y + x\,\frac{dy}{dt}\).
   check: diff((12 + 3*t)*(5 - 2*t), t) = 3*(5 - 2*t) + (12 + 3*t)*(-2)
5. [calc1.related-rates.values-at-instant] At the instant: substitute \(x = 12\), \(y = 5\), \(\frac{dx}{dt} = 3\) and \(\frac{dy}{dt} = -2\), giving \(\frac{dA}{dt} = (3)(5) + (12)(-2) = -9\).
   check: 3*5 + 12*(-2) = -9
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dA}{dt} = -9\) cm\(^2\)/s. It is negative, so the area is decreasing, by 9 cm\(^2\) each second. A direct check: with \(x = 12 + 3t\) and \(y = 5 - 2t\), the slope of \(xy\) at \(t = 0\) is the same number.
   check: subs(diff((12 + 3*t)*(5 - 2*t), t), t, 0) = -9

<!-- tier 1, template: which equation do you get? -->
## Card calc1.4-1.time-ladder.t01
skill: calc1.related-rates.differentiate-time
difficulty: 1
answer-type: choice
vars: L = int(10, 30)

### Question
A [[L]] ft ladder leans against a wall, so the distance \(x\) ft from the wall to its foot and the height \(y\) ft of its top satisfy \(x^2 + y^2 = [[L^2]]\) at every time \(t\). Which equation results from differentiating both sides with respect to \(t\)?

### Choices
- [x] \(2x\,\dfrac{dx}{dt} + 2y\,\dfrac{dy}{dt} = 0\)
- [ ] \(2x + 2y = 0\)
- [ ] \(2x\,\dfrac{dx}{dt} + 2y\,\dfrac{dy}{dt} = [[2*L]]\)
- [ ] \(2x\,\dfrac{dx}{dt} + 2y = 0\)

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the relation holds at every time, so its two sides stay equal as time passes and their rates of change must be equal. Every changing quantity brings its own rate, and a constant has rate zero.
1. [calc1.related-rates.differentiate-time] Differentiate: \(\frac{d}{dt}x^2 = 2x\,\frac{dx}{dt}\), \(\frac{d}{dt}y^2 = 2y\,\frac{dy}{dt}\), and the constant \([[L^2]]\) has rate \(0\).
   check: diff(x^2, x) = 2*x
   check: diff(y^2, y) = 2*y
   check: diff(L^2, t) = 0

<!-- tier 1, template: a constant in the relation has no rate -->
## Card calc1.4-1.time-height.t02
skill: calc1.related-rates.differentiate-time
difficulty: 1
answer-type: expression
vars: H = int(2, 9)
answer: 2*pi*H*r*a
wrong: 2*pi*H*r => The radius changes with time, so the derivative of r squared is 2r times the rate of r. @1; pi*H*r^2*a => The power of r is differentiated too: the derivative of r squared is 2r, not r squared. @1

### Question
A round pool of syrup spreads across a flat plate while keeping a constant depth of [[H]] mm, so its radius \(r\) mm changes with the time \(t\) in seconds. Its volume is \(V = [[H]]\pi r^2\) mm\(^3\). Let \(a\) stand for \(\frac{dr}{dt}\). Write \(\frac{dV}{dt}\) in terms of \(r\) and \(a\).

### Answer
\(\dfrac{dV}{dt} = [[2*H]]\pi r\,a\) mm\(^3\)/s, with \(a\) in mm/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the depth is a constant and has no rate, while the radius changes with time, so only the radius brings a rate when both sides are differentiated.
1. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\): \(\frac{dV}{dt} = [[H]]\pi\cdot 2r\cdot\frac{dr}{dt} = [[2*H]]\pi r\,a\).
   check: diff(H*pi*r^2, r)*a = 2*pi*H*r*a

<!-- tier 1: every changing quantity brings a rate -->
## Card calc1.4-1.time-cube.001
skill: calc1.related-rates.differentiate-time
difficulty: 1
answer-type: expression
answer: 3*s^2*w
wrong: 3*s^2 => The edge changes with time, so the derivative of s cubed also has the factor ds/dt. @1

### Question
An ice cube melts, so the length \(s\) cm of its edge changes with the time \(t\) in minutes. Its volume is \(V = s^3\) cm\(^3\). Let \(w\) stand for \(\frac{ds}{dt}\). Write \(\frac{dV}{dt}\) in terms of \(s\) and \(w\).

### Answer
\(\dfrac{dV}{dt} = 3s^2\,w\) cm\(^3\)/min, with \(w\) in cm/min

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the volume depends on the edge, and the edge changes with time, so differentiating with respect to time brings in the rate of the edge.
1. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\): \(\frac{dV}{dt} = 3s^2\,\frac{ds}{dt} = 3s^2\,w\).
   check: diff(s^3, s)*w = 3*s^2*w

<!-- tier 2: a product with two changing factors -->
## Card calc1.4-1.time-cylinder.001
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.product-rule
difficulty: 2
answer-type: expression
answer: 2*pi*r*h*a + pi*r^2*b
wrong: 2*pi*r*h*a => The height changes too, so the product rule has a second term. @1; 2*pi*r*a*b => The product rule adds two terms, each with one factor differentiated, rather than multiplying the two rates. @1

### Question
A cylindrical balloon is being inflated so that both its radius \(r\) m and its height \(h\) m change with the time \(t\) in seconds. Its volume is \(V = \pi r^2 h\) cubic meters. Let \(a\) stand for \(\frac{dr}{dt}\) and \(b\) for \(\frac{dh}{dt}\). Write \(\frac{dV}{dt}\) in terms of \(r\), \(h\), \(a\) and \(b\).

### Answer
\(\dfrac{dV}{dt} = 2\pi r h\,a + \pi r^2\,b\) m\(^3\)/s, with \(a\) and \(b\) in m/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the volume depends on two quantities that both change with time, so differentiating with respect to time brings in both rates.
1. [calc1.deriv.product-rule] Product rule: the right side is \(\pi\) times the product of \(r^2\) and \(h\), so its rate is \(\pi\left[\frac{d(r^2)}{dt}\,h + r^2\,\frac{dh}{dt}\right]\).
   check: diff((3 + 2*t)^2*(6 - t), t) = 2*(3 + 2*t)*2*(6 - t) + (3 + 2*t)^2*(-1)
2. [calc1.related-rates.differentiate-time] Rates: \(\frac{d(r^2)}{dt} = 2r\,a\) and \(\frac{dh}{dt} = b\), so \(\frac{dV}{dt} = \pi\left(2r\,a\,h + r^2\,b\right) = 2\pi r h\,a + \pi r^2\,b\).
   check: diff(pi*r^2*h, r)*a + diff(pi*r^2*h, h)*b = 2*pi*r*h*a + pi*r^2*b

<!-- tier 2, template: differentiate an equation of an ellipse and solve for one rate -->
## Card calc1.4-1.time-ellipse.t01
skill: calc1.related-rates.differentiate-time
uses: alg.solve.linear
difficulty: 2
answer-type: expression
vars: k = int(2, 5); c = int(10, 40)
answer: -x*u/(k*y)
wrong: -x*u/y => The term with y squared has the coefficient [[k]], so its derivative is [[2*k]]y times the rate of y. @1; x*u/(k*y) => Check the sign: the two terms on the left add up to zero, so the rates have opposite signs. @2

### Question
A particle moves in the plane along the ellipse \(x^2 + [[k]]y^2 = [[c]]\), with \(x\) and \(y\) in meters. Both coordinates change with the time \(t\) in seconds. Let \(u\) stand for \(\frac{dx}{dt}\) and \(w\) for \(\frac{dy}{dt}\). Write \(w\) in terms of \(x\), \(y\) and \(u\).

### Answer
\(\dfrac{dy}{dt} = [[tex(-x*u/(k*y))]]\), with \(u\) in m/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: both coordinates change with time while the right side is a constant, so differentiating with respect to time gives a relation between the two rates.
1. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\): \(2x\,\frac{dx}{dt} + [[2*k]]y\,\frac{dy}{dt} = 0\), that is \(2x\,u + [[2*k]]y\,w = 0\).
   check: diff(x^2 + k*y^2, x)*u + diff(x^2 + k*y^2, y)*w = 2*x*u + 2*k*y*w
2. [alg.solve.linear] Solve for \(w\): \([[2*k]]y\,w = -2x\,u\), so \(w = [[tex(-x*u/(k*y))]]\).
   check: 2*x*u + 2*k*y*(-x*u/(k*y)) = 0
   check: -2*x*u/(2*k*y) = -x*u/(k*y)

<!-- tier 2: the rope and the boat -->
## Card calc1.4-1.time-boat.001
skill: calc1.related-rates.differentiate-time
uses: alg.solve.linear
difficulty: 2
answer-type: expression
answer: x*u/s
wrong: u/s => The term x squared has the derivative 2x times the rate of x, so the factor x stays. @1; s*u/x => Dividing both sides by 2s leaves s in the denominator and x in the numerator. @2

### Question
A boat is pulled toward a dock by a rope that runs from the edge of the dock to a ring on the boat's bow, 2 m below the edge. The boat's horizontal distance \(x\) m from the dock and the length \(s\) m of the rope satisfy \(s^2 = x^2 + 4\), and both change with the time \(t\) in seconds. Let \(u\) stand for \(\frac{dx}{dt}\) and \(v\) for \(\frac{ds}{dt}\). Write \(v\) in terms of \(x\), \(s\) and \(u\).

### Answer
\(\dfrac{ds}{dt} = \dfrac{x}{s}\,u\), with \(u\) in m/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the rope and the boat's distance both change with time, while the 2 m drop is a constant with no rate, so differentiating with respect to time gives a relation between the two rates.
1. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\): \(2s\,\frac{ds}{dt} = 2x\,\frac{dx}{dt} + 0\), that is \(2s\,v = 2x\,u\).
   check: diff(s^2, s) = 2*s
   check: diff(x^2 + 4, x) = 2*x
2. [alg.solve.linear] Solve for \(v\): divide both sides by \(2s\), so \(v = \frac{x}{s}\,u\).
   check: 2*x*u/(2*s) = x*u/s

<!-- tier 2, template: the angle of a kite string, as a choice -->
## Card calc1.4-1.time-kite.t02
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.power-rule-rational
difficulty: 2
answer-type: choice
vars: h = int(30, 60)

### Question
A kite flies at a constant height of [[h]] m above the hands of the person holding the string. Its horizontal distance \(x\) m from the person and the angle \(\theta\) between the string and the ground satisfy \(\tan\theta = \dfrac{[[h]]}{x}\) at every time \(t\). When both sides are differentiated with respect to \(t\), the left side becomes \(\sec^2\theta\,\dfrac{d\theta}{dt}\). What does the right side become?

### Choices
- [x] \(-\dfrac{[[h]]}{x^2}\,\dfrac{dx}{dt}\)
- [ ] \(\dfrac{[[h]]}{x^2}\,\dfrac{dx}{dt}\)
- [ ] \(-\dfrac{[[h]]}{x}\,\dfrac{dx}{dt}\)
- [ ] \(-\dfrac{1}{x^2}\,\dfrac{dx}{dt}\)

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the height is a constant, and only the horizontal distance changes on the right side, so the right side brings the rate of that distance and nothing else.
1. [calc1.deriv.power-rule-rational] Differentiate: \(\frac{[[h]]}{x} = [[h]]x^{-1}\), so \(\frac{d}{dx}\frac{[[h]]}{x} = -\frac{[[h]]}{x^2}\).
   check: diff(h/x, x) = -h/x^2
2. [calc1.related-rates.differentiate-time] Rate factor: \(x\) changes with time, so the derivative with respect to \(x\) is multiplied by \(\frac{dx}{dt}\). For example, if \(x = 3 + 2t\), then the rate of \(\frac{[[h]]}{x}\) is \(-\frac{[[h]]}{(3 + 2t)^2}\cdot 2\).
   check: diff(h/(3 + 2*t), t) = (-h/(3 + 2*t)^2)*2

<!-- tier 3: three changing quantities in a product with a sine -->
## Card calc1.4-1.time-triangle.001
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.product-rule, calc1.deriv.trig-sin-cos
difficulty: 3
answer-type: expression
answer: (p*b*sin(theta) + a*q*sin(theta) + a*b*cos(theta)*w)/2
wrong: (p*b*sin(theta) + a*q*sin(theta))/2 => The angle changes too, so the sine contributes a third term. @1; (p*b*sin(theta) + a*q*sin(theta) + a*b*sin(theta)*w)/2 => The derivative of sine is cosine, so the third term has cos(theta), not sin(theta). @2

### Question
A robot has two telescoping arms hinged at a common point. The arms have lengths \(a\) m and \(b\) m, and the angle between them is \(\theta\) radians. All three change with the time \(t\) in seconds. The triangle formed by the two arms and the line joining their tips has area \(A = \tfrac{1}{2}ab\sin\theta\) square meters. Let \(p\) stand for \(\frac{da}{dt}\), \(q\) for \(\frac{db}{dt}\) and \(w\) for \(\frac{d\theta}{dt}\). Write \(\frac{dA}{dt}\) in terms of \(a\), \(b\), \(\theta\), \(p\), \(q\) and \(w\).

### Answer
\(\dfrac{dA}{dt} = \dfrac{1}{2}\left(p\,b\sin\theta + a\,q\sin\theta + a\,b\,w\cos\theta\right)\) m\(^2\)/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the area depends on three quantities that all change with time, so differentiating with respect to time brings in all three rates.
1. [calc1.deriv.product-rule] Product rule for three factors: \(\frac{d}{dt}(ab\sin\theta) = \frac{da}{dt}\,b\sin\theta + a\,\frac{db}{dt}\sin\theta + ab\,\frac{d}{dt}\sin\theta\).
   check: diff((3 + 2*t)*(4 - t)*sin(1 + 3*t), t) = 2*(4 - t)*sin(1 + 3*t) + (3 + 2*t)*(-1)*sin(1 + 3*t) + (3 + 2*t)*(4 - t)*3*cos(1 + 3*t)
2. [calc1.deriv.trig-sin-cos] Differentiate the sine: \(\frac{d}{d\theta}\sin\theta = \cos\theta\).
   check: diff(sin(theta), theta) = cos(theta)
3. [calc1.related-rates.differentiate-time] Rates: the angle changes with time, so \(\frac{d}{dt}\sin\theta = \cos\theta\,w\). With \(\frac{da}{dt} = p\) and \(\frac{db}{dt} = q\), \(\frac{dA}{dt} = \frac{1}{2}\left(p\,b\sin\theta + a\,q\sin\theta + a\,b\,w\cos\theta\right)\).
   check: diff(a*b*sin(theta)/2, a)*p + diff(a*b*sin(theta)/2, b)*q + diff(a*b*sin(theta)/2, theta)*w = (p*b*sin(theta) + a*q*sin(theta) + a*b*cos(theta)*w)/2

<!-- tier 3: resistors in parallel, reciprocals on both sides -->
## Card calc1.4-1.time-resistors.001
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.power-rule-rational, alg.solve.linear
difficulty: 3
answer-type: expression
answer: R^2*(u/x^2 + w/y^2)
wrong: R^2*(u/x + w/y) => Every reciprocal is differentiated with a square: the derivative of 1 over x is minus 1 over x squared. @1; u/x^2 + w/y^2 => The left side is 1 over R, so its rate is minus the rate of R over R squared. Multiply by R squared to solve for the rate of R. @3

### Question
Two resistors of \(x\) ohms and \(y\) ohms are connected in parallel, giving a total resistance of \(R\) ohms with \(\dfrac{1}{R} = \dfrac{1}{x} + \dfrac{1}{y}\). The resistances \(x\) and \(y\) change with the time \(t\) in seconds as the resistors heat up. Let \(u\) stand for \(\frac{dx}{dt}\) and \(w\) for \(\frac{dy}{dt}\) (ohms per second). Write \(\frac{dR}{dt}\) in terms of \(R\), \(x\), \(y\), \(u\) and \(w\).

### Answer
\(\dfrac{dR}{dt} = R^2\left(\dfrac{u}{x^2} + \dfrac{w}{y^2}\right)\) ohms per second

### Solution
0. [calc1.related-rates.differentiate-time] Set up: all three resistances change with time, so differentiating both sides with respect to time brings in all three rates. The reciprocal of a changing quantity needs the power rule for a negative power.
1. [calc1.deriv.power-rule-rational] Differentiate: \(\frac{1}{z} = z^{-1}\), so \(\frac{d}{dz}\frac{1}{z} = -\frac{1}{z^2}\).
   check: diff(1/z, z) = -1/z^2
2. [calc1.related-rates.differentiate-time] Rates: differentiate both sides with respect to \(t\), giving each resistance its rate: \(-\frac{1}{R^2}\frac{dR}{dt} = -\frac{1}{x^2}u - \frac{1}{y^2}w\).
   check: diff(1/x, x)*u + diff(1/y, y)*w = -u/x^2 - w/y^2
3. [alg.solve.linear] Solve for \(\frac{dR}{dt}\): multiply both sides by \(-R^2\), so \(\frac{dR}{dt} = R^2\left(\frac{u}{x^2} + \frac{w}{y^2}\right)\). As a check, write \(R = \frac{1}{1/x + 1/y}\) and differentiate it directly.
   check: diff(1/(1/x + 1/y), x)*u + diff(1/(1/x + 1/y), y)*w = (1/(1/x + 1/y))^2*(u/x^2 + w/y^2)
   check: R^2*(u/x^2 + w/y^2) = R^2*u/x^2 + R^2*w/y^2

<!-- tier 3, template: an implicit curve with a product -->
## Card calc1.4-1.time-implicit.t03
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.product-rule, alg.solve.linear
difficulty: 3
answer-type: expression
vars: k = int(2, 4); c = int(2, 9)
answer: (c - 2*x*y)*u/(x^2 + 3*k*y^2)
wrong: -2*x*y*u/(x^2 + 3*k*y^2) => The right side also changes with time: its rate is [[c]] times the rate of x. @2; (c - 2*x*y)*u/(3*k*y^2) => The product x squared times y gives two terms, and the term with the rate of y belongs with the other rate-of-y terms. @1

### Question
A particle moves in the plane along the curve \(x^2y + [[k]]y^3 = [[c]]x\), with \(x\) and \(y\) in meters. Both coordinates change with the time \(t\) in seconds. Let \(u\) stand for \(\frac{dx}{dt}\) and \(w\) for \(\frac{dy}{dt}\). Write \(w\) in terms of \(x\), \(y\) and \(u\).

### Answer
\(\dfrac{dy}{dt} = \dfrac{([[c]] - 2xy)\,u}{x^2 + [[3*k]]y^2}\), with \(u\) in m/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: both coordinates change with time, so differentiating both sides with respect to time gives a relation between the two rates. The first term on the left is a product of two changing quantities.
1. [calc1.deriv.product-rule] Product rule: \(\frac{d}{dt}(x^2y) = \frac{d(x^2)}{dt}\,y + x^2\,\frac{dy}{dt} = 2x\,u\,y + x^2\,w\).
   check: diff(x^2*y, x)*u + diff(x^2*y, y)*w = 2*x*y*u + x^2*w
2. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(2xy\,u + x^2\,w + [[3*k]]y^2\,w = [[c]]\,u\).
   check: diff(x^2*y + k*y^3, x)*u + diff(x^2*y + k*y^3, y)*w = 2*x*y*u + x^2*w + 3*k*y^2*w
3. [alg.solve.linear] Solve for \(w\): collect the terms with \(w\), so \((x^2 + [[3*k]]y^2)\,w = ([[c]] - 2xy)\,u\) and \(w = \frac{([[c]] - 2xy)\,u}{x^2 + [[3*k]]y^2}\).
   check: 2*x*y*u + x^2*((c - 2*x*y)*u/(x^2 + 3*k*y^2)) + 3*k*y^2*((c - 2*x*y)*u/(x^2 + 3*k*y^2)) = c*u
   check: (c - 2*x*y)*u/(x^2 + 3*k*y^2) = (c*u - 2*x*y*u)/(x^2 + 3*k*y^2)

<!-- tier 4: an angle of elevation with both coordinates changing -->
## Card calc1.4-1.time-elevation.001
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.trig-other, calc1.deriv.quotient-rule, trig.identities.pythagorean, alg.solve.linear
difficulty: 4
answer-type: expression
answer: (x*p - h*q)/(x^2 + h^2)
wrong: (p*x - h*q)/x^2 => That is the rate of tan(theta). The question asks for the rate of theta, so divide by sec squared of theta. @5; (x*p + h*q)/(x^2 + h^2) => The quotient rule has a minus sign between its two terms. @2; (x*p - h*q)/(x^2 + h^2)^2 => Dividing by sec squared of theta, which is (x squared plus h squared) over x squared, leaves the denominator to the first power. @5

### Question
A camera on the ground tracks a drone. At a certain time the drone is \(x\) m horizontally from the camera and \(h\) m above the ground, and the angle of elevation \(\theta\) of the camera satisfies \(\tan\theta = \dfrac{h}{x}\). The height \(h\), the distance \(x\) and the angle \(\theta\) all change with the time \(t\) in seconds. Let \(p\) stand for \(\frac{dh}{dt}\) and \(q\) for \(\frac{dx}{dt}\). Write \(\frac{d\theta}{dt}\) in terms of \(x\), \(h\), \(p\) and \(q\).

### Answer
\(\dfrac{d\theta}{dt} = \dfrac{x\,p - h\,q}{x^2 + h^2}\) radians per second

### Solution
0. [calc1.related-rates.differentiate-time] Set up: both sides of the relation change with time. The left side is a function of the angle, so it brings the rate of the angle, and the right side is a quotient of two changing quantities, so it brings two rates.
1. [calc1.deriv.trig-other] Differentiate the tangent: \(\frac{d}{d\theta}\tan\theta = \sec^2\theta\).
   check: diff(tan(theta), theta) = 1/cos(theta)^2
2. [calc1.deriv.quotient-rule] Quotient rule: the rate of \(\frac{h}{x}\) has numerator \(\frac{dh}{dt}x - h\frac{dx}{dt}\) and denominator \(x^2\).
   check: diff(h/x, h)*p + diff(h/x, x)*q = (p*x - h*q)/x^2
3. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(\sec^2\theta\,\frac{d\theta}{dt} = \frac{p\,x - h\,q}{x^2}\). As a check, \(\theta = \arctan\frac{h}{x}\) has the rate found at the end.
   check: diff(arctan(h/x), h)*p + diff(arctan(h/x), x)*q = (x*p - h*q)/(x^2 + h^2)
4. [trig.identities.pythagorean] Identity: \(\sec^2\theta = 1 + \tan^2\theta = 1 + \frac{h^2}{x^2} = \frac{x^2 + h^2}{x^2}\).
   check: 1 + (h/x)^2 = (x^2 + h^2)/x^2
5. [alg.solve.linear] Solve for \(\frac{d\theta}{dt}\): divide both sides by \(\sec^2\theta\), so \(\frac{d\theta}{dt} = \frac{p\,x - h\,q}{x^2}\cdot\frac{x^2}{x^2 + h^2} = \frac{x\,p - h\,q}{x^2 + h^2}\).
   check: (p*x - h*q)/x^2/((x^2 + h^2)/x^2) = (x*p - h*q)/(x^2 + h^2)

<!-- tier 4: a surface area that stays constant -->
## Card calc1.4-1.time-box.001
skill: calc1.related-rates.differentiate-time
uses: calc1.deriv.product-rule, alg.solve.linear
difficulty: 4
answer-type: expression
answer: -(x + h)*u/x
wrong: -h*u/x => The side of the base changes too, so the term 2x squared contributes 4x times the rate of x. @2; -u => The term 4xh is a product of two changing quantities, so it gives two terms. Use the product rule. @1; (x + h)*u/x => Check the sign: the surface area does not change, so the terms add up to zero and the rates have opposite signs. @3

### Question
A closed metal box with a square base is reshaped without adding or removing any metal, so its surface area stays equal to 600 cm\(^2\). The side of the base is \(x\) cm and the height is \(h\) cm, so the surface area is \(S = 2x^2 + 4xh\). Both \(x\) and \(h\) change with the time \(t\) in seconds. Let \(u\) stand for \(\frac{dx}{dt}\) and \(w\) for \(\frac{dh}{dt}\). Write \(w\) in terms of \(x\), \(h\) and \(u\).

### Answer
\(\dfrac{dh}{dt} = -\dfrac{(x + h)\,u}{x}\), with \(u\) in cm/s

### Solution
0. [calc1.related-rates.differentiate-time] Set up: the surface area is constant, so its rate is zero. The two dimensions change with time, so differentiating both sides with respect to time gives a relation between their rates.
1. [calc1.deriv.product-rule] Product rule: \(\frac{d}{dt}(xh) = \frac{dx}{dt}\,h + x\,\frac{dh}{dt} = u\,h + x\,w\).
   check: diff(x*h, x)*u + diff(x*h, h)*w = u*h + x*w
2. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(4x\,u + 4\left(u\,h + x\,w\right) = 0\), since the right side is a constant.
   check: diff(2*x^2 + 4*x*h, x)*u + diff(2*x^2 + 4*x*h, h)*w = 4*x*u + 4*u*h + 4*x*w
3. [alg.solve.linear] Solve for \(w\): \(4x\,w = -4u(x + h)\), so \(w = -\frac{(x + h)\,u}{x}\).
   check: 4*x*u + 4*u*h + 4*x*(-(x + h)*u/x) = 0
   check: -4*u*(x + h)/(4*x) = -(x + h)*u/x

<!-- ===================================================================== -->
<!-- calc1.related-rates.values-at-instant                                 -->
<!-- ===================================================================== -->
<!-- In this block the differentiated equation is usually printed in the question, so the
     practice is on finding the values at the instant, substituting after differentiating,
     and solving for the wanted rate. -->

<!-- worked example -->
## Card calc1.4-1.instant-example.001
kind: example
skill: calc1.related-rates.values-at-instant
uses: calc1.related-rates.translate, pre.geometry.pythagorean, calc1.related-rates.relate, calc1.related-rates.differentiate-time, alg.solve.linear

### Question
A kite flies at a constant height of 40 m above the hands of the person holding the string. The wind carries it horizontally away from the person at a steady 3 m/s. How fast is the string being let out at the instant when 50 m of string is out? Assume the string stays straight.

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the rate of the string depends on how far the kite is from the person at that instant, and the problem gives the length of the string, not that distance. So differentiate the relation first, then find every quantity's value at the instant from the relation, and only then substitute.
1. [calc1.related-rates.translate] Given and wanted: let \(x\) be the horizontal distance and \(s\) the length of the string, in meters, both functions of the time \(t\) in seconds. The kite moves away, so \(\frac{dx}{dt} = +3\), and the wanted rate is \(\frac{ds}{dt}\) at \(s = 50\).
   check: diff(30 + 3*t, t) = 3
2. [pre.geometry.pythagorean] Geometry: the height, the horizontal distance and the straight string form a right triangle with hypotenuse \(s\) and legs \(x\) and \(40\).
   check: sqrt(30^2 + 40^2) = 50
3. [calc1.related-rates.relate] Relate: the height never changes, so for every time \(t\), \(s^2 = x^2 + 1600\). Only \(s\) and \(x\) change.
   check: 50^2 = 30^2 + 1600
4. [calc1.related-rates.differentiate-time] Differentiate both sides with respect to \(t\), giving every changing quantity its rate: \(2s\,\frac{ds}{dt} = 2x\,\frac{dx}{dt}\).
   check: diff(s^2, s) = 2*s
   check: diff(x^2 + 1600, x) = 2*x
5. [calc1.related-rates.values-at-instant] At the instant: \(s = 50\) gives \(x^2 = 2500 - 1600 = 900\), so \(x = 30\), because a distance is positive. Only now substitute \(s = 50\), \(x = 30\) and \(\frac{dx}{dt} = 3\): \(2(50)\,\frac{ds}{dt} = 2(30)(3)\).
   check: sqrt(50^2 - 40^2) = 30
6. [alg.solve.linear] Solve for the unknown rate: \(100\,\frac{ds}{dt} = 180\), so \(\frac{ds}{dt} = \frac{9}{5}\).
   check: solve(2*50*v - 2*30*3, v) = {9/5}
7. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{ds}{dt} = \frac{9}{5}\) m/s, that is 1.8 m/s. It is positive, so the string is being let out, more slowly than the kite moves. A direct check: with \(x = 30 + 3t\) and \(s = \sqrt{1600 + x^2}\), the slope of \(s\) at \(t = 0\) is the same number.
   check: subs(diff(sqrt(1600 + (30 + 3*t)^2), t), t, 0) = 9/5

<!-- tier 1, template: the other quantity's value at the instant -->
## Card calc1.4-1.instant-ladder.t01
skill: calc1.related-rates.values-at-instant
difficulty: 1
answer-type: number
vars: k = int(2, 4); m = int(2, 4); n = int(1, 3)
require: n < m; k*(m^2 + n^2) <= 40
let: a = k*(m^2 - n^2); b = 2*k*m*n; c = k*(m^2 + n^2)
answer: b
wrong: c - a => The legs and the hypotenuse of a right triangle are linked through their squares, not through a difference of lengths. @1

### Question
A [[c]] ft ladder leans against a vertical wall. The distance \(x\) ft from the wall to its foot and the height \(y\) ft of its top satisfy \(x^2 + y^2 = [[c^2]]\). At a certain instant the foot is [[a]] ft from the wall. How high up the wall, in feet, is the top of the ladder at that instant?

### Answer
\(y = [[b]]\) ft

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the distance of the foot from the wall is the value of one changing quantity at the instant, and the relation gives the value of the other quantity at the same instant.
1. [calc1.related-rates.values-at-instant] At the instant: \(x = [[a]]\) gives \(y^2 = [[c^2]] - [[a^2]] = [[b^2]]\), so \(y = [[b]]\), because a height is positive.
   check: sqrt(c^2 - a^2) = b

<!-- tier 1: substitute into a differentiated equation -->
## Card calc1.4-1.instant-cone-sub.001
skill: calc1.related-rates.values-at-instant
difficulty: 1
answer-type: number
answer: 2*pi
wrong: pi/3 => The depth enters squared. The factor is h squared, which is 36 at the instant, not 6. @1

### Question
The water in a cone-shaped tank has depth \(h\) ft and volume \(V\) ft\(^3\), with \(V = \frac{\pi}{27}h^3\). Differentiating with respect to the time \(t\) in minutes gives \(\frac{dV}{dt} = \frac{\pi}{9}h^2\,\frac{dh}{dt}\). At the instant when the depth is 6 ft, the level is rising at 0.5 ft/min. At what rate, in cubic feet per minute, is the volume of water increasing at that instant?

### Answer
\(\dfrac{dV}{dt} = 2\pi\) ft\(^3\)/min, about 6.3 ft\(^3\)/min

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the differentiated equation holds at every time, so the values at the instant can be substituted into it, and the unknown rate is then the only thing left.
1. [calc1.related-rates.values-at-instant] At the instant: substitute \(h = 6\) and \(\frac{dh}{dt} = \frac{1}{2}\), giving \(\frac{dV}{dt} = \frac{\pi}{9}(6)^2\left(\frac{1}{2}\right) = 2\pi\).
   check: pi/9*6^2*(1/2) = 2*pi

<!-- tier 1, template: substitute, then solve for the unknown rate -->
## Card calc1.4-1.instant-solve.t03
skill: calc1.related-rates.values-at-instant
uses: alg.solve.linear
difficulty: 1
answer-type: number
vars: k = int(2, 5); m = int(2, 4); n = int(1, 3); u = int(1, 4)
require: n < m; k*(m^2 + n^2) >= 20; k*(m^2 + n^2) <= 100
let: a = k*(m^2 - n^2); b = 2*k*m*n; c = k*(m^2 + n^2)
answer: -a*u/b
wrong: a*u/b => The two terms of the equation add up to zero, so the two rates have opposite signs. @2; -b*u/a => The coefficient of the rate of y is 2y, so divide by 2y, not by 2x. @2

### Question
A cyclist rides on a circular track of radius [[c]] m centered at the origin, so her coordinates \(x\) and \(y\), in meters, satisfy \(x^2 + y^2 = [[c^2]]\). Differentiating with respect to the time \(t\) in seconds gives \(2x\,\frac{dx}{dt} + 2y\,\frac{dy}{dt} = 0\). At the instant when she is at the point \(([[a]], [[b]])\), her \(x\)-coordinate is increasing at [[u]] m/s. How fast is her \(y\)-coordinate changing at that instant, in meters per second?

### Answer
\(\dfrac{dy}{dt} = [[tex(-a*u/b)]]\) m/s, negative because \(y\) is decreasing

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the point is given, so the values of both coordinates at the instant are known and can be substituted into the differentiated equation. The only unknown left is the rate of the vertical coordinate.
1. [calc1.related-rates.values-at-instant] At the instant: the point is on the track, since \([[a^2]] + [[b^2]] = [[c^2]]\). Substitute \(x = [[a]]\), \(y = [[b]]\) and \(\frac{dx}{dt} = [[u]]\), giving \(2([[a]])([[u]]) + 2([[b]])\,\frac{dy}{dt} = 0\).
   check: a^2 + b^2 = c^2
2. [alg.solve.linear] Solve for \(\frac{dy}{dt}\): \([[2*b]]\,\frac{dy}{dt} = -[[2*a*u]]\), so \(\frac{dy}{dt} = [[tex(-a*u/b)]]\).
   check: 2*a*u + 2*b*(-a*u/b) = 0
   check: -2*a*u/(2*b) = -a*u/b

<!-- tier 2: the order of substituting and differentiating -->
## Card calc1.4-1.instant-order.001
skill: calc1.related-rates.values-at-instant
difficulty: 2
answer-type: choice

### Question
A 13 ft ladder leans against a wall, so the distance \(x\) ft from the wall to its foot and the height \(y\) ft of its top satisfy \(x^2 + y^2 = 169\) at every time. The foot slides away from the wall at \(\frac{dx}{dt} = 2\) ft/s, and the question asks for \(\frac{dy}{dt}\) at the instant when \(x = 5\). In which order should the work be done?

### Choices
- [ ] Substitute \(x = 5\) into the relation first, then differentiate \(25 + y^2 = 169\) with respect to \(t\)
- [ ] Find \(y = 12\), substitute both \(x = 5\) and \(y = 12\) into the relation, then differentiate \(25 + 144 = 169\)
- [x] Differentiate both sides with respect to \(t\) first, then find \(y = 12\) from the relation and substitute \(x = 5\), \(y = 12\) and \(\frac{dx}{dt} = 2\)
- [ ] Differentiate first, then substitute only \(x = 5\) and leave \(y\) as a letter in the answer

### Solution
0. [calc1.related-rates.values-at-instant] Set up: both distances change with time, so the order of substituting and differentiating matters. A value may be substituted only after the relation has been differentiated.
1. [calc1.related-rates.values-at-instant] Why not before: if \(x = 5\) and \(y = 12\) are substituted first, the relation becomes \(25 + 144 = 169\), a statement about numbers whose rate of change is \(0\) and which says nothing about \(\frac{dy}{dt}\). Substituting only \(x = 5\) first freezes \(x\) and loses \(\frac{dx}{dt}\) as well.
   check: diff(5^2 + 12^2, t) = 0
2. [calc1.related-rates.values-at-instant] The right order: differentiate to get \(2x\,\frac{dx}{dt} + 2y\,\frac{dy}{dt} = 0\). At the instant, \(x = 5\) gives \(y = 12\) from the relation, and only then substitute \(x = 5\), \(y = 12\) and \(\frac{dx}{dt} = 2\). The unknown \(y\) cannot stay a letter, because the answer must be a number.
   check: sqrt(13^2 - 5^2) = 12

<!-- tier 2, template: a kite string, the length found from the distance -->
## Card calc1.4-1.instant-kite.t01
skill: calc1.related-rates.values-at-instant
uses: alg.solve.linear, calc1.related-rates.translate
difficulty: 2
answer-type: number
vars: k = int(2, 4); m = int(2, 4); n = int(1, 3); w = int(2, 6)
require: n < m; 2*k*m*n >= 20; 2*k*m*n <= 100
let: H = 2*k*m*n; X = k*(m^2 - n^2); S = k*(m^2 + n^2)
answer: X*w/S
wrong: S*w/X => The equation gives the rate of the string as x over s times the rate of x, so the string is let out more slowly than the kite moves. @2; X*w/H => The letter s stands for the length of the string, not for the height. At the instant it comes from the relation. @1

### Question
A kite flies at a constant height of [[H]] m above the hands of the person holding the string. The wind carries it horizontally away from the person at a steady [[w]] m/s. The string stays straight, with length \(s\) m, and the kite is \(x\) m horizontally from the person, so \(s^2 = x^2 + [[H^2]]\). Differentiating with respect to the time \(t\) in seconds gives \(s\,\frac{ds}{dt} = x\,\frac{dx}{dt}\). At the instant when the kite is [[X]] m horizontally from the person, how fast, in meters per second, is the string being let out?

### Answer
\(\dfrac{ds}{dt} = [[tex(X*w/S)]]\) m/s

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the horizontal distance is known at the instant, but the length of the string is not, so the relation has to give the length before the values can be substituted.
1. [calc1.related-rates.values-at-instant] At the instant: \(x = [[X]]\) gives \(s^2 = [[X^2]] + [[H^2]] = [[S^2]]\), so \(s = [[S]]\), because a length is positive.
   check: sqrt(X^2 + H^2) = S
2. [alg.solve.linear] Solve: substitute \(s = [[S]]\), \(x = [[X]]\) and \(\frac{dx}{dt} = [[w]]\) into the differentiated equation, so \([[S]]\,\frac{ds}{dt} = [[X*w]]\) and \(\frac{ds}{dt} = [[tex(X*w/S)]]\).
   check: solve(S*v - X*w, v) = {X*w/S}
3. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{ds}{dt} = [[tex(X*w/S)]]\) m/s. It is positive, so the string is being let out, and more slowly than the kite moves. A direct check: with \(x = [[X]] + [[w]]t\), the slope of \(\sqrt{[[H^2]] + x^2}\) at \(t = 0\) is the same number.
   check: subs(diff(sqrt(H^2 + (X + w*t)^2), t), t, 0) = X*w/S

<!-- tier 2, template: find every quantity's value at the instant -->
## Card calc1.4-1.instant-values.t02
skill: calc1.related-rates.values-at-instant
difficulty: 2
answer-type: list
vars: a = int(4, 8); j = int(1, 5)
require: j < a
answer: j, 3*j
wrong: 3*j, j => Give the radius of the water's surface first and then the depth, as the question asks. @1; j/3, j => The volume formula is pi/27 times h cubed, so h cubed is 27 times the number in front of pi. @1

### Question
A tank is a cone with its point at the bottom, [[3*a]] ft deep and [[a]] ft in radius at the top. When the water has depth \(h\) ft and surface radius \(r\) ft, its volume \(V\) ft\(^3\) satisfies \(r = \frac{h}{3}\) and \(V = \frac{\pi}{27}h^3\). At the instant when the tank holds \([[tex(j^3*pi)]]\) ft\(^3\) of water, what are \(r\) and \(h\)? Give \(r\) first and then \(h\), both in feet.

### Answer
\(r = [[j]]\) ft and \(h = [[3*j]]\) ft

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the volume at the instant is known, so the volume formula gives the depth, and then the first relation gives the radius.
1. [calc1.related-rates.values-at-instant] At the instant: \(\frac{\pi}{27}h^3 = [[tex(j^3*pi)]]\) gives \(h^3 = [[27*j^3]]\), so \(h = [[3*j]]\) ft. Then \(r = \frac{h}{3} = [[j]]\) ft.
   check: (3*j)^3/27 = j^3
   check: {3*j/3, 3*j} = {j, 3*j}

<!-- tier 2: the instant is given by the volume, not by the depth -->
## Card calc1.4-1.instant-cone.001
skill: calc1.related-rates.values-at-instant
uses: alg.solve.linear, calc1.related-rates.translate
difficulty: 2
answer-type: number
answer: 4/(3*pi)
wrong: 4/(27*pi) => The number 27 pi is the volume, not the depth. The formula for the volume has to give the depth first. @1; 12/pi => Solving (pi/27) h cubed = 27 pi gives h cubed = 729, not 27. @1; 3/(4*pi) => The depth in the equation is the depth of the water at the instant, 9 ft, not the full depth of the tank, 12 ft. @1

### Question
Water is pumped at a steady 12 ft\(^3\)/min into a tank that is a cone with its point at the bottom, 12 ft deep and 4 ft in radius at the top. The depth \(h\) ft and the volume \(V\) ft\(^3\) of the water satisfy \(V = \frac{\pi}{27}h^3\), and differentiating with respect to the time \(t\) in minutes gives \(\frac{dV}{dt} = \frac{\pi}{9}h^2\,\frac{dh}{dt}\). How fast is the water level rising at the instant when the tank holds \(27\pi\) ft\(^3\) of water? Give the rate in feet per minute.

### Answer
\(\dfrac{dh}{dt} = \dfrac{4}{3\pi}\) ft/min, about 0.42 ft/min

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the instant is described by the volume, not by the depth, so the volume formula has to give the depth before the values can be substituted into the differentiated equation.
1. [calc1.related-rates.values-at-instant] At the instant: \(\frac{\pi}{27}h^3 = 27\pi\) gives \(h^3 = 729\), so \(h = 9\) ft. Substitute \(h = 9\) and \(\frac{dV}{dt} = 12\): \(12 = \frac{\pi}{9}(9)^2\,\frac{dh}{dt} = 9\pi\,\frac{dh}{dt}\).
   check: 9^3/27 = 27
   check: pi/9*9^2 = 9*pi
2. [alg.solve.linear] Solve for the unknown rate: \(\frac{dh}{dt} = \frac{12}{9\pi} = \frac{4}{3\pi}\).
   check: solve(12 - 9*pi*v, v) = {4/(3*pi)}
3. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dh}{dt} = \frac{4}{3\pi}\) ft/min, about 0.42 ft/min. It is positive, so the level is rising. A direct check: if \(V = 27\pi + 12t\), then \(h = \sqrt[3]{27V/\pi}\), and its slope at \(t = 0\) is the same number.
   check: subs(diff((27*(27*pi + 12*t)/pi)^(1/3), t), t, 0) = 4/(3*pi)

<!-- tier 3: exact trigonometric values at the instant -->
## Card calc1.4-1.instant-triangle.001
skill: calc1.related-rates.values-at-instant
uses: trig.values.exact, calc1.related-rates.translate
difficulty: 3
answer-type: number
answer: 5/4 + 6*sqrt(3)/5
wrong: 5/4 => The angle changes too, so the third term, with the rate of the angle, has to be included. @2; 5/2 + 12*sqrt(3)/5 => The area is one half of the product, so the whole expression in brackets is multiplied by one half. @2

### Question
A robot has two telescoping arms hinged at a common point. The arms have lengths \(a\) m and \(b\) m, and the angle between them is \(\theta\) radians, all functions of the time \(t\) in seconds. The triangle formed by the arms and the line joining their tips has area \(A = \frac{1}{2}ab\sin\theta\), and differentiating with respect to \(t\) gives
\[\frac{dA}{dt} = \frac{1}{2}\left(\frac{da}{dt}\,b\sin\theta + a\,\frac{db}{dt}\sin\theta + ab\cos\theta\,\frac{d\theta}{dt}\right).\]
At the instant when \(a = 6\), \(b = 8\) and \(\theta = \frac{\pi}{6}\), the arm \(a\) is lengthening at 1 m/s, the arm \(b\) is shortening at 0.5 m/s, and the angle is increasing at 0.1 rad/s. At what rate is the area changing at that instant, in square meters per second?

### Answer
\(\dfrac{dA}{dt} = \dfrac{5}{4} + \dfrac{6\sqrt{3}}{5}\) m\(^2\)/s, about 3.33 m\(^2\)/s

### Solution
0. [calc1.related-rates.values-at-instant] Set up: every quantity in the differentiated equation has a value at the instant, and the sine and cosine of the angle are needed exactly. A shortening arm has a negative rate.
1. [trig.values.exact] Exact values: \(\sin\frac{\pi}{6} = \frac{1}{2}\) and \(\cos\frac{\pi}{6} = \frac{\sqrt{3}}{2}\).
   check: sin(pi/6) = 1/2
   check: cos(pi/6) = sqrt(3)/2
2. [calc1.related-rates.values-at-instant] At the instant: substitute \(a = 6\), \(b = 8\), \(\frac{da}{dt} = 1\), \(\frac{db}{dt} = -\frac{1}{2}\) and \(\frac{d\theta}{dt} = \frac{1}{10}\): \(\frac{dA}{dt} = \frac{1}{2}\left[(1)(8)\cdot\frac{1}{2} + (6)\left(-\frac{1}{2}\right)\cdot\frac{1}{2} + (6)(8)\cdot\frac{\sqrt{3}}{2}\cdot\frac{1}{10}\right] = \frac{5}{4} + \frac{6\sqrt{3}}{5}\).
   check: (1*8*(1/2) + 6*(-1/2)*(1/2) + 6*8*(sqrt(3)/2)*(1/10))/2 = 5/4 + 6*sqrt(3)/5
3. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dA}{dt} = \frac{5}{4} + \frac{6\sqrt{3}}{5}\) m\(^2\)/s, about 3.33 m\(^2\)/s. It is positive, so the area is increasing. A direct check: with \(a = 6 + t\), \(b = 8 - \frac{t}{2}\) and \(\theta = \frac{\pi}{6} + \frac{t}{10}\), the slope of \(\frac{1}{2}ab\sin\theta\) at \(t = 0\) is the same number.
   check: subs(diff((6 + t)*(8 - t/2)*sin(pi/6 + t/10)/2, t), t, 0) = 5/4 + 6*sqrt(3)/5

<!-- tier 3: the instant is described by the volume, and the trough has triangular ends -->
## Card calc1.4-1.instant-trough.001
skill: calc1.related-rates.values-at-instant
uses: alg.solve.linear, calc1.related-rates.translate
difficulty: 3
answer-type: number
answer: 1/40
wrong: 1/48 => Solving (10/3) h squared = 4.8 gives h squared = 1.44, so the depth is 1.2, not 1.44. @1; 1/50 => The depth in the equation is the depth of the water at the instant, 1.2 m, not the full depth of the trough, 1.5 m. @1

### Question
A horizontal trough is 5 m long. Its cross-section is an isosceles triangle with its point at the bottom, 2 m wide at the top and 1.5 m deep. When the water has depth \(h\) m, its volume is \(V = \frac{10}{3}h^2\) cubic meters, and differentiating with respect to the time \(t\) in minutes gives \(\frac{dV}{dt} = \frac{20}{3}h\,\frac{dh}{dt}\). Water is poured in at a steady 0.2 m\(^3\)/min. How fast is the water level rising at the instant when the trough holds 4.8 m\(^3\) of water? Give the rate in meters per minute.

### Answer
\(\dfrac{dh}{dt} = \dfrac{1}{40}\) m/min, that is 2.5 cm/min

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the instant is described by the volume, not by the depth, so the volume formula has to give the depth before the values can be substituted into the differentiated equation.
1. [calc1.related-rates.values-at-instant] At the instant: \(\frac{10}{3}h^2 = 4.8\) gives \(h^2 = 1.44\), so \(h = 1.2\) m, because a depth is positive. Substitute \(h = 1.2\) and \(\frac{dV}{dt} = 0.2\): \(0.2 = \frac{20}{3}(1.2)\,\frac{dh}{dt} = 8\,\frac{dh}{dt}\).
   check: 10/3*(6/5)^2 = 24/5
   check: 20/3*(6/5) = 8
2. [alg.solve.linear] Solve for the unknown rate: \(\frac{dh}{dt} = \frac{0.2}{8} = \frac{1}{40}\).
   check: solve(1/5 - 8*v, v) = {1/40}
3. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dh}{dt} = \frac{1}{40}\) m/min, that is 2.5 cm/min. It is positive, so the level is rising. A direct check: if \(V = 4.8 + 0.2t\), then \(h = \sqrt{0.3V}\), and its slope at \(t = 0\) is the same number.
   check: subs(diff(sqrt(3*(24/5 + t/5)/10), t), t, 0) = 1/40

<!-- tier 3, template: a bead on a curve, a sign choice and a second rate -->
## Card calc1.4-1.instant-curve.t03
skill: calc1.related-rates.values-at-instant
uses: calc1.related-rates.differentiate-time, alg.solve.linear, calc1.related-rates.translate
difficulty: 3
answer-type: number
vars: q = int(2, 5); c = int(2, 5)
answer: c*(1 + 2*q^2)/sqrt(1 + q^2)
wrong: c/sqrt(1 + q^2) => The height changes too. The curve y = x squared gives its rate as 2x times the rate of x. @2; c*sqrt(1 + 4*q^2) => That is the speed of the bead along the wire. The question asks for the rate at which its distance from the origin changes. @3

### Question
A bead slides along a wire bent into the part of the parabola \(y = x^2\) with \(x > 0\), where \(x\) and \(y\) are in centimeters. Let \(s\) cm be the distance from the bead to the origin, so \(s^2 = x^2 + y^2\), and differentiating with respect to the time \(t\) in seconds gives \(s\,\frac{ds}{dt} = x\,\frac{dx}{dt} + y\,\frac{dy}{dt}\). At the instant when the bead is [[q^2]] cm high, its \(x\)-coordinate is increasing at [[c]] cm/s. How fast is the distance from the bead to the origin changing at that instant, in centimeters per second?

### Answer
\(\dfrac{ds}{dt} = [[tex(c*(1 + 2*q^2)/sqrt(1 + q^2))]]\) cm/s

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the bead's height gives its position on the curve, and the curve also links the two rates. So the position, the rate of the height and the distance to the origin are all needed before anything can be substituted.
1. [calc1.related-rates.values-at-instant] At the instant: \(y = [[q^2]]\) on the part of the curve with \(x > 0\) gives \(x = [[q]]\). Then \(s^2 = [[q^2]] + [[q^4]] = [[q^2 + q^4]]\), so \(s = \sqrt{[[q^2 + q^4]]}\).
   check: sqrt(q^2 + (q^2)^2) = q*sqrt(1 + q^2)
2. [calc1.related-rates.differentiate-time] The curve gives the rate of the height: differentiating \(y = x^2\) with respect to \(t\) gives \(\frac{dy}{dt} = 2x\,\frac{dx}{dt} = 2([[q]])([[c]]) = [[2*q*c]]\).
   check: diff(x^2, x)*c = 2*x*c
3. [calc1.related-rates.values-at-instant] Substitute into the differentiated equation: \(\sqrt{[[q^2 + q^4]]}\,\frac{ds}{dt} = ([[q]])([[c]]) + ([[q^2]])([[2*q*c]]) = [[q*c + 2*q^3*c]]\).
   check: q*c + q^2*(2*q*c) = q*c*(1 + 2*q^2)
4. [alg.solve.linear] Solve for the unknown rate: \(\frac{ds}{dt} = \dfrac{[[q*c + 2*q^3*c]]}{\sqrt{[[q^2 + q^4]]}} = [[tex(c*(1 + 2*q^2)/sqrt(1 + q^2))]]\).
   check: (q*c + 2*q^3*c)/sqrt(q^2 + q^4) = c*(1 + 2*q^2)/sqrt(1 + q^2)
5. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{ds}{dt} = [[tex(c*(1 + 2*q^2)/sqrt(1 + q^2))]]\) cm/s. It is positive, so the bead is moving away from the origin. A direct check: with \(x = [[q]] + [[c]]t\) and \(y = x^2\), the slope of \(\sqrt{x^2 + y^2}\) at \(t = 0\) is the same number.
   check: subs(diff(sqrt((q + c*t)^2 + ((q + c*t)^2)^2), t), t, 0) = c*(1 + 2*q^2)/sqrt(1 + q^2)

<!-- tier 4: the given rate is a net rate that depends on the instant -->
## Card calc1.4-1.instant-leak.001
skill: calc1.related-rates.values-at-instant
uses: calc1.related-rates.translate, alg.solve.linear
difficulty: 4
answer-type: number
answer: 9/(4*pi)
wrong: 12/(4*pi) => The leak removes water, so the rate of the volume is the inflow minus the outflow, not the inflow alone. @1; 15/(4*pi) => The leak removes water, so it is subtracted from the inflow, not added. @1

### Question
Water flows into a conical tank at a steady 12 ft\(^3\)/min and leaks out through a hole at the bottom at \(\frac{h}{2}\) ft\(^3\)/min, where \(h\) ft is the depth of the water. The tank has its point at the bottom, is 12 ft deep and is 4 ft in radius at the top, so the volume of water is \(V = \frac{\pi}{27}h^3\), and differentiating with respect to the time \(t\) in minutes gives \(\frac{dV}{dt} = \frac{\pi}{9}h^2\,\frac{dh}{dt}\). At what rate is the water level changing at the instant when the depth is 6 ft? Give the rate in feet per minute.

### Answer
\(\dfrac{dh}{dt} = \dfrac{9}{4\pi}\) ft/min, about 0.72 ft/min

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the rate of the volume is not one number given in the problem. It is the inflow minus the outflow, and the outflow depends on the depth, so it has to be found at the instant before the differentiated equation can be used.
1. [calc1.related-rates.translate] Net rate: water enters at \(+12\) and leaves at \(\frac{h}{2}\), so \(\frac{dV}{dt} = 12 - \frac{h}{2}\) ft\(^3\)/min. At \(h = 6\) the leak is \(3\), so \(\frac{dV}{dt} = 9\).
   check: 12 - 6/2 = 9
2. [calc1.related-rates.values-at-instant] At the instant: substitute \(h = 6\) and \(\frac{dV}{dt} = 9\) into the differentiated equation: \(9 = \frac{\pi}{9}(6)^2\,\frac{dh}{dt} = 4\pi\,\frac{dh}{dt}\).
   check: pi/9*6^2 = 4*pi
3. [alg.solve.linear] Solve for the unknown rate: \(\frac{dh}{dt} = \frac{9}{4\pi}\).
   check: solve(9 - 4*pi*v, v) = {9/(4*pi)}
4. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dh}{dt} = \frac{9}{4\pi}\) ft/min, about 0.72 ft/min. It is positive, so the level is still rising at this depth. A direct check: at this instant the volume is \(8\pi\) and grows at 9 ft\(^3\)/min, so \(h = \sqrt[3]{27V/\pi}\) has the same slope.
   check: subs(diff((27*(8*pi + 9*t)/pi)^(1/3), t), t, 0) = 9/(4*pi)

<!-- tier 4: two candidate pairs of sides, and two rates to find -->
## Card calc1.4-1.instant-rect.001
skill: calc1.related-rates.values-at-instant
uses: alg.solve.polynomial, alg.solve.linear, calc1.related-rates.translate
difficulty: 4
answer-type: number
answer: 21/20
wrong: 12/5 => The other side changes too, so the term with the rate of y has to be included. @5; -7/5 => The width is the shorter side, so x = 6 and y = 8. Swapping them changes the sign of the answer. @2

### Question
A rectangle with sides \(x\) cm and \(y\) cm is inscribed in a circle of radius 5 cm, so \(x^2 + y^2 = 100\), and its area is \(A = xy\). With \(t\) the time in seconds, differentiating gives \(x\,\frac{dx}{dt} + y\,\frac{dy}{dt} = 0\) and \(\frac{dA}{dt} = \frac{dx}{dt}\,y + x\,\frac{dy}{dt}\). At the instant when the area is 48 cm\(^2\) and \(x < y\), the side \(x\) is increasing at 0.3 cm/s. At what rate is the area changing at that instant, in square centimeters per second?

### Answer
\(\dfrac{dA}{dt} = \dfrac{21}{20}\) cm\(^2\)/s, that is 1.05 cm\(^2\)/s

### Solution
0. [calc1.related-rates.values-at-instant] Set up: the instant is described by the area, not by the sides, so the two sides at the instant must be found first. Then the first differentiated equation gives the rate of the second side, and the second one gives the rate of the area.
1. [calc1.related-rates.values-at-instant] At the instant: \(x^2 + y^2 = 100\) and \(xy = 48\), so \((x + y)^2 = 100 + 2(48) = 196\) and \(x + y = 14\), because the sides are positive.
   check: sqrt(100 + 2*48) = 14
2. [alg.solve.polynomial] Solve: \(x\) and \(y\) are the roots of \(z^2 - 14z + 48 = 0\), that is \(z = 6\) or \(z = 8\). Since \(x < y\), \(x = 6\) and \(y = 8\).
   check: solve(z^2 - 14*z + 48, z) = {6, 8}
3. [calc1.related-rates.values-at-instant] Substitute into the first differentiated equation: \(6(0.3) + 8\,\frac{dy}{dt} = 0\).
   check: 6*(3/10) = 9/5
4. [alg.solve.linear] Solve for the rate of \(y\): \(8\,\frac{dy}{dt} = -1.8\), so \(\frac{dy}{dt} = -0.225\).
   check: solve(6*(3/10) + 8*v, v) = {-9/40}
5. [calc1.related-rates.values-at-instant] Substitute into the second differentiated equation: \(\frac{dA}{dt} = (0.3)(8) + (6)(-0.225) = 2.4 - 1.35 = 1.05\).
   check: 3/10*8 + 6*(-9/40) = 21/20
6. [calc1.related-rates.translate] Answer with sign and unit: \(\frac{dA}{dt} = \frac{21}{20}\) cm\(^2\)/s, that is 1.05 cm\(^2\)/s. It is positive, so the area is increasing even though the side \(y\) is shrinking. A direct check: with \(x = 6 + 0.3t\) and \(y = \sqrt{100 - x^2}\), the slope of \(xy\) at \(t = 0\) is the same number.
   check: subs(diff((6 + 3*t/10)*sqrt(100 - (6 + 3*t/10)^2), t), t, 0) = 21/20
