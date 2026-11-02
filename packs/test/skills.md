---
format: mastery-skills 1
---

<!-- A tiny skill graph across three sections. test.alg.quadratic-solve lists
     test.alg.arithmetic on purpose: it is implied through test.alg.linear-solve, so the
     pack builder drops it (GRAPH-1, stored without redundant edges). -->

## Skill test.alg.arithmetic
name: Simplify arithmetic and expressions
deck: Test Course::1 Algebra::1.1 Linear Equations
textbook: Test Book 1.1
core: yes

## Skill test.alg.linear-solve
name: Solve a linear equation
deck: Test Course::1 Algebra::1.1 Linear Equations
requires: test.alg.arithmetic
confusable: test.alg.line-equation
textbook: Test Book 1.1
core: yes
exam-tier: 2

## Skill test.alg.line-equation
name: Write the equation of a line
deck: Test Course::1 Algebra::1.1 Linear Equations
requires: test.alg.arithmetic
confusable: test.alg.linear-solve
textbook: Test Book 1.2

## Skill test.alg.vectors
name: Write a vector in component form
deck: Test Course::1 Algebra::1.1 Linear Equations
requires: test.alg.arithmetic

## Skill test.alg.matrices
name: Write the coefficient matrix of a system
deck: Test Course::1 Algebra::1.1 Linear Equations
requires: test.alg.linear-solve

## Skill test.alg.factor-quadratic
name: Factor a quadratic
deck: Test Course::1 Algebra::1.2 Quadratics
requires: test.alg.arithmetic
confusable: test.alg.quadratic-formula
textbook: Test Book 2.1

## Skill test.alg.quadratic-formula
name: Use the quadratic formula
deck: Test Course::1 Algebra::1.2 Quadratics
requires: test.alg.arithmetic
confusable: test.alg.factor-quadratic
textbook: Test Book 2.2

## Skill test.alg.quadratic-solve
name: Solve a quadratic equation or inequality
deck: Test Course::1 Algebra::1.2 Quadratics
requires: test.alg.factor-quadratic, test.alg.linear-solve, test.alg.arithmetic
encompasses: test.alg.factor-quadratic = 0.5; test.alg.linear-solve = 0.25
exam-tier: 3

## Skill test.alg.vertex
name: Find the vertex of a parabola
deck: Test Course::1 Algebra::1.2 Quadratics
requires: test.alg.arithmetic

## Skill test.alg.choose-quadratic-method
name: Choose a method for a quadratic equation
deck: Test Course::1 Algebra::1.2 Quadratics
chooses: test.alg.factor-quadratic, test.alg.quadratic-formula

## Skill test.calc.power-rule
name: Differentiate with the power rule
deck: Test Course::2 Calculus::2.1 Derivatives
requires: test.alg.arithmetic
core: yes

## Skill test.calc.limits
name: Find a limit
deck: Test Course::2 Calculus::2.1 Derivatives
requires: test.alg.arithmetic

## Skill test.calc.critical-points
name: Find critical numbers
deck: Test Course::2 Calculus::2.1 Derivatives
requires: test.calc.power-rule, test.alg.quadratic-solve
encompasses: test.calc.power-rule = 1

### Notes
Critical numbers are where \(f'\) is zero or undefined.
