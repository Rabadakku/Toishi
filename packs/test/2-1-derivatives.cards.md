---
format: mastery-cards 1
deck: Test Course::2 Calculus::2.1 Derivatives
source: original
license: personal
---

<!-- expression, with a cued twin and an alternative solution -->
## Card test.deriv.power.001
skill: test.calc.power-rule
difficulty: 1
answer-type: expression
answer: 3x^2 + 2
wrong: 3x^2 => The derivative of 2x is 2, not 0. @2; x^2 + 2 => Multiply by the old exponent. @1

### Question
Find \(f'(x)\) for \(f(x) = x^3 + 2x\).

### Cued Question
Use the power rule to find \(f'(x)\) for \(f(x) = x^3 + 2x\).

### Hints
1. Differentiate each term separately.

### Solution
0. [test.calc.power-rule] Set up: differentiate term by term with the power rule.
1. [test.calc.power-rule] First term: \((x^3)' = 3x^2\).
2. [test.calc.power-rule] Second term: \((2x)' = 2\), so \(f'(x) = 3x^2 + 2\).

### Alternative Solution
1. [test.calc.limits] Limit definition: \(\frac{f(x + h) - f(x)}{h} = 3x^2 + 3xh + h^2 + 2\), which tends to \(3x^2 + 2\) as \(h \to 0\).

<!-- antiderivative -->
## Card test.deriv.antiderivative.001
skill: test.calc.power-rule
difficulty: 2
answer-type: antiderivative
answer: x^3 + C
wrong: 6x => That is the derivative, not an antiderivative. @1

### Question
Find \(\displaystyle \int 3x^2 \, dx\).

### Hints
1. Which function has derivative \(3x^2\)?

### Solution
0. [test.calc.power-rule] Set up: run the power rule backwards.
1. [test.calc.power-rule] Integrate: raise the exponent by one and divide by the new exponent: \(\frac{3x^3}{3} + C = x^3 + C\).

<!-- number: DNE -->
## Card test.deriv.limit-dne.001
skill: test.calc.limits
difficulty: 2
answer-type: number
answer: DNE
wrong: 1 => That is the limit from the right only. @1; -1 => That is the limit from the left only. @1

### Question
Find \(\displaystyle \lim_{x \to 0} \frac{|x|}{x}\).

### Hints
1. Compare \(x\) slightly above and slightly below \(0\).

### Solution
0. [test.calc.limits] Set up: compare the one-sided limits.
1. [test.calc.limits] One-sided limits: the quotient is \(1\) for \(x > 0\) and \(-1\) for \(x < 0\), so the limit does not exist.

<!-- number: infinity -->
## Card test.deriv.limit-inf.001
skill: test.calc.limits
difficulty: 2
answer-type: number
answer: inf
wrong: DNE => The quotient grows without bound from both sides: write inf. @1

### Question
Find \(\displaystyle \lim_{x \to 0} \frac{1}{x^2}\).

### Hints
1. What happens to \(x^2\) as \(x \to 0\)?

### Solution
0. [test.calc.limits] Set up: look at the size of the quotient near \(0\).
1. [test.calc.limits] Grow: \(x^2 > 0\) shrinks to \(0\), so \(\frac{1}{x^2}\) grows without bound from both sides.

<!-- choice, select all that apply, with a plot -->
## Card test.deriv.critical-choice.001
skill: test.calc.critical-points
uses: test.calc.power-rule, test.alg.quadratic-solve
difficulty: 2
answer-type: choice
plot: x^3 - 3x, x = -2.5..2.5

### Question
Select all critical numbers of \(f(x) = x^3 - 3x\).

### Choices
- [x] \(-1\)
- [ ] \(0\)
- [x] \(1\)
- [ ] \(3\)

### Hints
1. Solve \(f'(x) = 0\).

### Solution
0. [test.calc.critical-points] Set up: critical numbers are where \(f'\) is zero or undefined.
1. [test.calc.power-rule] Differentiate: \(f'(x) = 3x^2 - 3\).
2. [test.alg.quadratic-solve] Solve: \(3x^2 - 3 = 0\) gives \(x = -1\) or \(x = 1\).

<!-- example -->
## Card test.deriv.example.001
kind: example
skill: test.calc.power-rule

### Question
Differentiate \(f(x) = 5x^4\).

### Solution
0. [test.calc.power-rule] Set up: \((x^n)' = n x^{n - 1}\), and constant factors stay.
1. [test.calc.power-rule] Differentiate: \(f'(x) = 5 \cdot 4x^3 = 20x^3\).

<!-- template: diff(), tex() and computed wrong answers -->
## Card test.deriv.power.t01
skill: test.calc.power-rule
difficulty: 1
answer-type: expression
vars: a = int(2, 6); n = int(3, 6)
let: f = a*x^n
answer: diff(f, x)
wrong: a*x^(n - 1) => Multiply by the exponent [[n]] too. @1; a*n*x^n => Lower the exponent by one. @1

### Question
Differentiate \(f(x) = [[tex(f)]]\).

### Hints
1. Bring the exponent down, then lower it by one.

### Solution
0. [test.calc.power-rule] Set up: \((x^n)' = n x^{n - 1}\), and constant factors stay.
1. [test.calc.power-rule] Differentiate: \(f'(x) = [[a]] \cdot [[n]] x^{[[n - 1]]} = [[tex(diff(f, x))]]\).
