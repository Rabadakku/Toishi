---
format: mastery-cards 1
deck: Test Course::1 Algebra::1.1 Linear Equations
source: original
license: personal
---

<!-- number, with known wrong answers and the step they come from -->
## Card test.linear.solve.001
skill: test.alg.linear-solve
uses: test.alg.arithmetic
difficulty: 1
answer-type: number
answer: 5
wrong: 25/3 => You added 5 to both sides instead of subtracting it. @1
tags: equations, one-step
tagged: hand test-pack 1.0

### Question
Solve \(3x + 5 = 20\).

### Hints
1. Get the \(x\) term alone first.
2. Subtract \(5\) from both sides.

### Solution
0. [test.alg.linear-solve] Set up: undo the operations on \(x\) in reverse order.
1. [test.alg.arithmetic] Subtract 5: \(3x = 15\).
2. [test.alg.linear-solve] Divide by 3: \(x = 5\).

<!-- equation -->
## Card test.linear.line.001
skill: test.alg.line-equation
difficulty: 2
answer-type: equation
answer: y = 2x + 1
wrong: y = x + 2 => The slope multiplies x, and the intercept is the constant. @1

### Question
Write the equation of the line with slope \(2\) and \(y\)-intercept \(1\).

### Hints
1. Use slope-intercept form, \(y = mx + b\).

### Solution
0. [test.alg.line-equation] Set up: slope-intercept form is \(y = mx + b\).
1. [test.alg.line-equation] Substitute: \(m = 2\) and \(b = 1\) give \(y = 2x + 1\).

<!-- expression -->
## Card test.linear.simplify.001
skill: test.alg.arithmetic
difficulty: 1
answer-type: expression
answer: x + 6
wrong: x + 3 => Multiply both terms in the parentheses by 2. @1

### Question
Simplify \(2(x + 3) - x\).

### Hints
1. Distribute the \(2\) first.

### Solution
0. [test.alg.arithmetic] Set up: distribute, then combine like terms.
1. [test.alg.arithmetic] Distribute: \(2x + 6 - x\).
2. [test.alg.arithmetic] Combine like terms: \(x + 6\).

<!-- truefalse -->
## Card test.linear.check.001
skill: test.alg.linear-solve
uses: test.alg.arithmetic
difficulty: 1
answer-type: truefalse
answer: true

### Question
True or false: \(x = 2\) is a solution of \(3x + 1 = 7\).

### Hints
1. Substitute \(x = 2\) into the left side.

### Solution
0. [test.alg.linear-solve] Set up: a solution makes both sides equal.
1. [test.alg.arithmetic] Substitute: \(3 \cdot 2 + 1 = 7\), so the statement is true.

<!-- text -->
## Card test.linear.slope-name.001
skill: test.alg.line-equation
difficulty: 1
answer-type: text
answer: slope; the slope
wrong: intercept => The intercept is b, where the line crosses the y-axis.

### Question
In \(y = mx + b\), what is the number \(m\) called?

### Hints
1. It measures how steep the line is.

### Solution
0. [test.alg.line-equation] Name it: \(m\) is the slope, the rise over the run.

<!-- vector -->
## Card test.linear.vector.001
skill: test.alg.vectors
uses: test.alg.arithmetic
difficulty: 1
answer-type: vector
answer: <3, 4>
wrong: <4, 3> => Write the x-component first. @1; <-3, -4> => Subtract the start from the end. @1

### Question
Write the vector from \((1, 2)\) to \((4, 6)\) in component form.

### Hints
1. Subtract the coordinates of the start from the coordinates of the end.

### Solution
0. [test.alg.vectors] Set up: the components are end minus start.
1. [test.alg.arithmetic] Subtract: \(\langle 4 - 1, 6 - 2 \rangle = \langle 3, 4 \rangle\).

<!-- matrix -->
## Card test.linear.matrix.001
skill: test.alg.matrices
difficulty: 2
answer-type: matrix
answer: [[1, 2], [3, 4]]
wrong: [[1, 3], [2, 4]] => Each row holds the coefficients of one equation. @1

### Question
Write the coefficient matrix of the system \(x + 2y = 5\), \(3x + 4y = 6\).

### Hints
1. One row per equation, one column per variable.

### Solution
0. [test.alg.matrices] Set up: row \(i\) holds the coefficients of equation \(i\), in the order \(x\), \(y\).
1. [test.alg.matrices] Fill in: \(\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}\).

<!-- number, with a calculator allowed and angles in degrees -->
## Card test.linear.degrees.001
skill: test.alg.arithmetic
difficulty: 1
answer-type: number
answer: 2
calculator: yes
angles: degrees
source-url: https://example.org/test-pack
modified: yes

### Question
Evaluate \(2 \sin 30^\circ + 1\).

### Hints
1. \(\sin 30^\circ = \frac{1}{2}\).

### Solution
0. [test.alg.arithmetic] Evaluate: \(2 \cdot \frac{1}{2} + 1 = 2\).

<!-- self-graded, with a rubric -->
## Card test.linear.explain.001
skill: test.alg.linear-solve
uses: test.alg.arithmetic
difficulty: 2

### Question
Explain why \(0x = 5\) has no solution.

### Hints
1. What is \(0\) times any number?

### Solution
0. [test.alg.linear-solve] Set up: a solution is a number that makes both sides equal.
1. [test.alg.arithmetic] Reason: \(0x = 0\) for every \(x\), and \(0 \ne 5\), so no number works.

### Rubric
- [ ] Says that \(0x = 0\) for every \(x\)
- [ ] Concludes that no number makes the equation true

<!-- example -->
## Card test.linear.example.001
kind: example
skill: test.alg.linear-solve
uses: test.alg.arithmetic

### Question
Solve \(2x - 7 = 3\).

### Solution
0. [test.alg.linear-solve] Set up: undo the subtraction, then the multiplication.
1. [test.alg.arithmetic] Add 7: \(2x = 10\).
2. [test.alg.linear-solve] Divide by 2: \(x = 5\).

<!-- flashcard -->
## Card test.linear.flash.001
kind: flashcard

### Front
What is the slope-intercept form of a line?

### Back
\(y = mx + b\), where \(m\) is the slope and \(b\) is the \(y\)-intercept.

<!-- cloze -->
## Card test.linear.cloze.001
kind: cloze

### Text
To solve \(ax + b = c\), first {{c1::subtract \(b\) from both sides}}, then {{c2::divide both sides by \(a\)}}.

### Extra
This works whenever \(a \ne 0\).

<!-- template: a choice() parameter, a let, solve() of an equation, and [[...]] in a wrong answer's feedback -->
## Card test.linear.solve.t01
skill: test.alg.linear-solve
uses: test.alg.arithmetic
difficulty: 1
answer-type: number
vars: a = int(2, 5); b = int(1, 6); c = choice(10, 20)
let: r = (c - b)/a
answer: solve(a*x + b = c, x)
wrong: (c + b)/a => You added [[b]] instead of subtracting it. @1

### Question
Solve \([[tex(a*x + b)]] = [[c]]\).

### Hints
1. Subtract \([[b]]\) from both sides first.

### Solution
0. [test.alg.linear-solve] Set up: undo the addition, then the multiplication.
1. [test.alg.arithmetic] Subtract [[b]]: \([[a]]x = [[c - b]]\).
2. [test.alg.linear-solve] Divide by [[a]]: \(x = [[tex(r)]]\).

<!-- arithmetic: a worked example and enough problems for its learning phase to finish
     without serving a card twice in a study day (ADR-0018) -->
## Card test.linear.arith-example.001
kind: example
skill: test.alg.arithmetic

### Question
Simplify \(3(x - 2) + 4\).

### Solution
0. [test.alg.arithmetic] Set up: distribute, then combine the constants.
1. [test.alg.arithmetic] Distribute: \(3x - 6 + 4\).
2. [test.alg.arithmetic] Combine the constants: \(3x - 2\).

## Card test.linear.arith.001
skill: test.alg.arithmetic
difficulty: 1
answer-type: number
answer: 14
wrong: 20 => Multiply before you add. @1

### Question
Evaluate \(2 + 3 \cdot 4\).

### Hints
1. Multiplication comes before addition.

### Solution
0. [test.alg.arithmetic] Set up: multiply first, then add.
1. [test.alg.arithmetic] Multiply and add: \(2 + 12 = 14\).

## Card test.linear.arith.002
skill: test.alg.arithmetic
difficulty: 1
answer-type: number
answer: 3/4
wrong: 2/6 => Use a common denominator instead of adding the denominators. @1

### Question
Evaluate \(\frac{1}{2} + \frac{1}{4}\).

### Hints
1. Write \(\frac{1}{2}\) as quarters.

### Solution
0. [test.alg.arithmetic] Set up: use the common denominator \(4\).
1. [test.alg.arithmetic] Add: \(\frac{2}{4} + \frac{1}{4} = \frac{3}{4}\).

## Card test.linear.arith.003
skill: test.alg.arithmetic
difficulty: 1
answer-type: expression
answer: 5x - 2
wrong: 5x + 2 => Keep the sign of each constant. @1

### Question
Simplify \(2x + 3x - 7 + 5\).

### Hints
1. Combine the \(x\) terms, then the constants.

### Solution
0. [test.alg.arithmetic] Set up: collect like terms.
1. [test.alg.arithmetic] Combine: \(5x - 2\).

## Card test.linear.arith.004
skill: test.alg.arithmetic
difficulty: 2
answer-type: expression
answer: x - 3
wrong: x + 9 => The minus sign multiplies both terms in the parentheses. @1

### Question
Simplify \(4x - 3(x + 1)\).

### Hints
1. Distribute \(-3\) to both terms.

### Solution
0. [test.alg.arithmetic] Set up: distribute, then combine like terms.
1. [test.alg.arithmetic] Distribute: \(4x - 3x - 3\).
2. [test.alg.arithmetic] Combine like terms: \(x - 3\).

## Card test.linear.arith.005
skill: test.alg.arithmetic
difficulty: 2
answer-type: number
answer: -5
wrong: 5 => Two negatives make a positive only when you multiply. @1

### Question
Evaluate \(-2 - 3\).

### Hints
1. Subtracting \(3\) moves \(3\) further left on the number line.

### Solution
0. [test.alg.arithmetic] Set up: start at \(-2\) and move \(3\) to the left.
1. [test.alg.arithmetic] Subtract: \(-2 - 3 = -5\).
