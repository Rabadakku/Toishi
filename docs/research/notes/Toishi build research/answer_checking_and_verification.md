# Answer Checking and a Zero-Wrong-Key Problem-Bank Pipeline (AI + Computer Algebra)

Scope note: research done 2026-11-01. Claims marked "local run" come from experiments the researcher ran in SymPy 1.14.0 (Python 3.13). The linked SymPy doc page covers the API used, not the specific result. Everything else is cited to the page it came from. "Inferences" are the researcher's engineering judgment, not published evidence.

---

## 1. How mature systems check math answers, and which answer types must be supported

### Takeaway
WeBWorK, STACK and Möbius all separate *value equivalence* from *form requirements*. WeBWorK compares formulas numerically at random test points inside a declared domain, with relative tolerance. STACK uses symbolic `simplify(a-b)=0` in Maxima plus about 40 specialised "answer tests" chained in potential response trees. Möbius uses author-written Maple predicates. A bank-serving app needs typed answers (number, expression, equation, interval/union, finite set or unordered list, ordered tuple/point/vector, matrix, DNE/none/infinity, quantity with units), each with its own comparator. A single generic "are these equal" function is not enough.

### Cited Findings
**WeBWorK MathObjects (Perl, numeric-first)**
- Default context flags: `tolerance = .001`, `tolType = "relative"`, `zeroLevel = 1E-14` (below this magnitude, comparison switches to absolute), `zeroLevelTol = 1E-12`, `num_points = 5` random test points (plus any `test_at` points), `limits = [-2,2]`, `checkUndefinedPoints = 0`, `granularity = 1000`, `reduceConstants = 1`, `reduceConstantFunctions = 1` — [WeBWorK wiki: Context flags](https://webwork.maa.org/wiki/Context_flags)
- Interval/set flags: `ignoreEndpointTypes = 0` (open/closed endpoints matter), `reduceSets = 1`, `reduceSetsForComparison = 1`, `reduceUnions = 1`, `reduceUnionsForComparison = 1`, `infiniteWord = "infinity"` — [WeBWorK wiki: Context flags](https://webwork.maa.org/wiki/Context_flags)
- Answer-checker options include `studentsMustReduceUnions` (default 1: overlapping or uncombined intervals are rejected), `showUnionReduceWarnings`, `ignoreStrings` (so "NONE" in a list-of-numbers checker doesn't raise a type error) and `showTypeWarnings` — [WeBWorK wiki: Answer Checker Options](https://webwork.maa.org/wiki/Answer_Checker_Options_(MathObjects))
- Test points "be chosen from an interval contained in the domain of the correct answer". For logs or non-integer powers the variable should stay positive, including odd roots like cube roots, "because floating-point arithmetic is unreliable for negative inputs". When no valid points can be found, WeBWorK errors with "Can't generate enough valid points for comparison". Limits and points can be set per formula (`$f->{limits}=[2,5]`, `$f->{test_points}=[[-3],[-2],[2]]`), and per-variable resolution is supported (`n => ['Real', limits=>[1,20], resolution=>1]`) — [WeBWorK wiki: FormulaTestPoints](https://webwork.maa.org/wiki/FormulaTestPoints)
- Test points can deliberately be placed outside the key's domain to catch a student who entered an equivalent-but-undefined expression — [WeBWorK wiki: FormulaTestPoints](https://webwork.maa.org/wiki/FormulaTestPoints)
- Examples show typed answers like `List('NONE')->cmp(typeMatch => 'Value::Point')`. The list checker "allows a wider range of answers" and individual checkers give more detailed feedback — [WeBWorK wiki: Answer Checkers (MathObjects)](https://webwork.maa.org/wiki/Answer_Checkers_(MathObjects))

**STACK (Moodle/ILIAS; Maxima CAS)**
- Answer-test families: Equivalence (AlgEquiv, AlgEquivNouns, SubstEquiv, CasEqual, SameType, SysEquiv); Syntactic form (FacForm, PartFrac, SingleFrac, CompSquare, Expanded, LowestTerms); Rules-based (EqualComAss, EqualComAssRules); Numerical (NumRelative, NumAbsolute, NumSigFigs, NumDecPlaces, SigFigsStrict, GT, GTE); Scientific units (Units, UnitsStrict, UnitsRelative, UnitsAbsolute, …); Calculus (Diff, Int, Antidiff, AddConst); String/regex (String, StringSloppy, Levenshtein, SRegExp); Other (Sets, Equiv, PropLogic) — [STACK docs: Answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/)
- AlgEquiv is roughly `simplify(ex1-ex2)=0`. It is symbolic, not numeric, and "always fully simplifies all its arguments". For equations, equivalence means the same roots with the same multiplicities. STACK checks this by taking the ratio of the simplified numerators of (lhs−rhs) and testing whether that ratio is a number, so it never solves anything. Inequalities are converted to the sets of reals they represent. Sets are compared through canonical string forms, because "we cannot subtract one list or set from another" — [STACK docs: Equivalence tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/)
- Documented AlgEquiv limitations: expansion can blow up and factoring can time out (authors can weaken the test with `algebraic_equivalence_factorp:false` and `algebraic_equivalence_trigexpandp:false`); floats are discouraged in favour of numerical tests; some true identities fail, e.g. the Cardano expression `(sqrt(108)+10)^(1/3)-(sqrt(108)-10)^(1/3)` (which equals 2); `radcan` is not applied automatically — [STACK docs: Equivalence tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/)
- SubstEquiv searches for a variable renaming. It is factorial in the number of variables, so it "only works for 4 or fewer variables". SysEquiv compares polynomial systems through Gröbner bases. CasEqual is purely structural (`simp:false`), and the docs warn "Explicit properties should be tested in preference to using this test!" — [STACK docs: Equivalence tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/)
- NumRelative tests `abs(sa-ta) <= opt*abs(ta)` and NumAbsolute tests `abs(sa-ta) < opt`, both with default tolerance 0.05. Both accept lists (order matters) and sets (order ignored). NumDecPlaces requires trailing zeros ("12.30" passes for 2 places, "12.3" fails) — [STACK docs: Numerical tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Numerical/)
- A potential response tree (PRT) is "the algorithm which establishes the mathematical properties of the student's answer and assigns outcomes". It is an acyclic graph where each node runs one answer test, and each true/false branch can set, add or subtract score, attach feedback, record a unique "answer note" and name the next node. The default per-attempt penalty is 0.1. Each input can have its own PRT, and a separate PRT can span several inputs for formative feedback only — [STACK docs: Potential response trees](https://docs.stack-assessment.org/en/Authoring/Potential_response_trees/)

**Möbius (formerly Maple T.A.; Maple CAS)**
- Example grading code: default `evalb(($ANSWER)-($RESPONSE)=0)`; `is(($ANSWER)-($RESPONSE)=0)`; `evalb(simplify(($ANSWER)-($RESPONSE),symbolic)=0)`; absolute tolerance `is(abs(($ANSWER)-($RESPONSE))<=0.01)`; percent tolerance `evalb(100*abs((($ANSWER)-($RESPONSE))/($ANSWER)) <= 1)`; antiderivative up to a constant `is(diff(($ANSWER)-($RESPONSE),x)=0)`; factored form, by checking that the product of the response's factors equals the answer and that each factor is irreducible; sets with partial credit `numelems(RESPONSE intersect ANSWER)/numelems(ANSWER)`, scoring 0 when the response has more elements than the answer; and a rule that blocks students from typing `factor(...)` — [DigitalEd: Example Maple grading code](https://www.digitaled.com/support/help/admin/Content/INST-AUTHORING/QUESTION-TYPES/MAPLE-GRADED/Example-Maple-grading-code.htm)
- Möbius accepts algebraic, equation, numeric (fraction/decimal/scientific) and unit equivalence (e.g., 10000 cm² = 1 m²) by default. Instructors can turn this off, and "if a question asks you to simplify… you must enter the simplified form" — [DigitalEd: Enter equivalent responses](https://digitaled.com/support/help/student/Content/STUD-ENTERING-RESPONSES/Enter-equivalent-responses.htm)

**LLM-evaluation graders (the modern "Lean-free" Python approach)**
- Hugging Face Math-Verify parses LaTeX and plain expressions with SymPy plus an ANTLR4 grammar. It supports sets, intervals, finite sets, set operations, matrices/vectors, equations and inequalities, percentages, units, and complex numbers. It compares in stages (normalised string → basic SymPy equality → numeric within precision → simplify the difference), has timeout protection, and handles relation flips like `a<2` vs `2>a`. Its `verify(gold, pred)` is asymmetric: an interval gold answer against an inequality prediction returns False unless `allow_set_relation_comp` is set — [GitHub: huggingface/Math-Verify](https://github.com/huggingface/Math-Verify)
- latex2sympy2_extended (the parser behind Math-Verify; MIT licence, maintainer Hynek Kydlíček) is at v1.11.0 (Jan 10 2026), with set-operation support and an option for complex numbers — [PyPI: latex2sympy2_extended](https://pypi.org/project/latex2sympy2_extended/)

### Inferences
- Answer types the bank schema must carry (each with its own comparator and input widget): `number` (exact or decimal with tolerance policy), `expression` (with variables and a domain), `equation` (curve or relation), `solution_set` (interval/union/finite set, including ∅), `unordered_list` (e.g., all roots), `ordered_tuple` (point, vector, (a,b,c) answers), `matrix`, `special` (DNE, ∞, −∞, "no solution", "all reals"), `quantity` (number plus unit, for physics and chemistry), `multiple_choice`, and `proof/show_that` (self-graded). Calc 1 limits need `{number, ∞, −∞, DNE}` as one union type.
- Copy STACK's design: each problem stores a *list of tests* (equivalence + optional form test + optional "common wrong answer" tests that trigger targeted feedback), not a single comparator.
- WeBWorK's default relative tolerance of 0.1% suits numeric sampling of formulas but is loose for "give the exact value" problems. Keep exact comparison for exact-answer problems and use tolerance only for decimal-answer problems.

### Gaps
- The WeBWorK List/Union checker option pages (`ordered`, `showLengthHints`, `partialCredit` and their defaults) could not be fetched (robots-disallowed). The defaults for list partial credit are unconfirmed.
- No primary documentation was found on how Möbius checks equivalence internally (symbolic vs random-value evaluation).

---

## 2. SymPy specifics: equivalence strategy, pitfalls, safe parsing

### Takeaway
No single SymPy call is reliable. `simplify(a-b)==0` has false negatives and can hang. `.equals()` often returns `None`. `==` is structural. Use a layered checker: (1) parse into a whitelisted AST with the problem's own symbol objects (real/positive assumptions), (2) cheap exact or structural checks, (3) time-boxed `simplify` or `.equals` in a subprocess, (4) multi-point numeric evaluation at points inside the key's domain, which decides most cases, (5) treat "can't decide" as a separate outcome. `parse_expr` calls `eval` and is exploitable even with a restricted `global_dict`: reject dunders and attribute access before parsing.

### Cited Findings
**Security of parsing**
- SymPy docs: `parse_expr` "uses `eval`, and thus shouldn't be used on unsanitized input" — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html)
- CVE-2026-55546 (qwed-mcp < 0.2.1, CVSS 3.1 9.8 Critical, CWE-94): user strings went to `parse_expr()` after only `^`→`**` conversion, with no restricted `global_dict`, no removal of built-ins and no AST check. "Because parse_expr() calls Python's eval() with built-ins available", an attacker could run OS commands — [NVD: CVE-2026-55546](https://nvd.nist.gov/vuln/detail/CVE-2026-55546)
- Local run (SymPy 1.14.0): even with `global_dict` restricted to `{Integer, Float, Rational, Symbol, Function}`, the input `x.__class__.__mro__[-1].__subclasses__()` was evaluated and returned Python's full list of object subclasses (the classic sandbox-escape primitive). `__import__('os')...` was blocked only incidentally. Restricting `global_dict` alone is not enough — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html) (behaviour verified by local run)

**Transformations (implicit multiplication etc.)**
- Available transformations: `standard_transformations`, `implicit_multiplication_application`, `implicit_multiplication`, `convert_xor` (`^`→power), `rationalize` (floats→Rational; run after `auto_number`), `split_symbols` ("xyz"→x*y*z), `auto_number`, `factorial_notation`, `function_exponentiation` (`cos**2(x)`). With `evaluate=False`, argument order is preserved and `'1 + x'` and `'x + 1'` parse to *unequal* trees — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html)
- Local run: with `implicit_multiplication_application`, `"sinx"` → `i*n*s*x` (four symbols) and `"f(x)"` → `f*x`. `"e^x"` → `e**x` with `e` a free Symbol, not Euler's number, unless `local_dict` maps `e→E`. With plain `implicit_multiplication` (no splitting), `"xy"` stays one symbol `xy`. `"1/2x"` parses as `x/2`, which is fine, but students may mean `1/(2x)`. `"sin x^2"` → `sin(x**2)` — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html) (verified by local run)

**LaTeX parsing**
- `parse_latex(s, strict=False, backend='antlr'|'lark')` is "experimental". The ANTLR backend "may fail to fully parse an expression, yet not throw a warning" (e.g., `parse_latex(r'x -')` returns `x`). The Lark backend rejects ill-formed input but lacks matrices, higher-order or partial derivatives, and multiple integrals. `strict` only applies to ANTLR — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html)
- Both LaTeX backends need extra packages (`antlr4-python3-runtime` or `lark`); a bare `pip install sympy` cannot parse LaTeX (local run: ImportError for both) — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html)

**Equivalence pitfalls (local runs, SymPy 1.14.0; API per [SymPy docs: core](https://docs.sympy.org/latest/modules/core.html))**
- Symbol assumptions matter: `simplify(sqrt(x**2) - Abs(x))` does *not* reduce to 0 for a plain `Symbol('x')` (complex by default), but gives 0 for `Symbol('x', real=True)`.
- `Symbol('x') != Symbol('x', real=True)`. In one test, a student expression parsed with a default `x` and a key built with a real `x` were treated as different variables, so `diff(G - H, x)` silently differentiated only half the expression. Always inject the problem's own symbol objects through `local_dict`.
- Log laws: `simplify(log(x*y) - log(x) - log(y))` stays unsimplified (it is not an identity over ℂ). `expand_log(..., force=True)` forces it, which is mathematically unsafe.
- Trig identities do work: `sin²+cos²−1`, `tan − sin/cos` and `sin3x − (3sin x − 4sin³x)` all simplify to 0 in ≤0.03 s.
- Removable singularities: `simplify((x**2-1)/(x-1) - (x+1)) == 0` and `.equals` → True. Symbolic simplification ignores the hole at x=1. Whether that matters is a per-problem domain decision.
- `.equals()` returns `None` (undecided) for `asin(sin(x))` vs `x` (0.26 s) and for `Piecewise((x,x>0),(-x,True))` vs `Abs(x)`. The docstring: "Return True if self == other, False if it does not, or None", and numeric evalf is used only when the expression is a number.
- Real odd roots: `(x**Rational(1,3)).subs(x,-8).evalf()` gives `1.0 + 1.732*I` (principal complex root), not −2. `real_root(-8,3)` gives −2. Students' `(-8)^(1/3)` must be mapped to `real_root` in real-variable contexts, or numeric sampling must stay on x>0 (WeBWorK's advice).
- `simplify` false negative: the Cardano expression stays unsimplified (`2**(1/3)*(...)`). `nsimplify(N(expr,50))` → 2, `minimal_polynomial(expr, z)` → `z - 2`, and `.equals(2)` → True. Algebraic-number constants should be compared with `.equals` / `minimal_polynomial`, not `simplify`.
- Branch-sensitive identities: `atan(x)+atan(1/x) - pi/2` is not simplified to 0, even with `x` positive. Numerically it is 0 at x=2 and −π at x=−2. Domain-aware sampling gives the right verdict only if the problem's domain is declared.
- `Rational(1,3) == Float(0.3333)` → False (`==` is structural/exact; per the core docs, "only numbers of the same type will compare equal, so S.Half != Float(0.5)" under `is_same`) — [SymPy docs: core](https://docs.sympy.org/latest/modules/core.html)
- Sets and intervals: `Interval(1,3,True,False) == Interval.Lopen(1,3)` → True; `FiniteSet(1,2) == FiniteSet(2,1)` → True; `FiniteSet(Tuple(1,2),Tuple(3,4))` is order-insensitive; `solveset(Abs(x-1)>=2, x, S.Reals)` → `Union(Interval(-oo,-1), Interval(3,oo))` and compares equal to a hand-built union. Canonical SymPy set objects make set and interval answers easy to compare *exactly* (no numeric sampling needed).
- Equations: the STACK numerator-ratio method in SymPy (`r = simplify(numer(together(L1-R1)) / numer(together(L2-R2)))`, then equivalent iff `r.is_number and r != 0`) correctly accepts `x+y=1 ≡ 2x+2y=2` (r=1/2) and `y=2x+1 ≡ y-1=2x` (r=1), and rejects `x²=1` vs `x=1` (r=x+1).
- Units: `sympy.physics.units.convert_to(10000*centimeter**2, meter)` minus `1*meter**2` simplifies to 0, and `convert_to(5*newton, [kilogram, meter, second])` → `5*kilogram*meter/second**2` — [SymPy docs: Physics units](https://docs.sympy.org/latest/modules/physics/units/index.html) (verified by local run)
- Antiderivatives: `simplify(diff(log(Abs(x)),x) - 1/x)` returns `Piecewise((zoo, Eq(x,0)), (0, True))`, not 0. A "derivative of the difference is 0" check (Möbius' approach) needs numeric evaluation or Piecewise handling.

**Prototype result (local run):** a 2-stage checker (subprocess-timeboxed `simplify(a-b)==0`, then 12 random real points in [−3,3] via `lambdify(..., 'mpmath')`, skipping points where the key is undefined or non-real, and failing if the student is undefined or non-real where the key is defined) gave:
| student vs key | symbolic | numeric (domain-aware) |
|---|---|---|
| sqrt(x^2) vs abs(x) | True | True |
| sqrt(x^2) vs x | False | False |
| ln(x^2) vs 2ln(x) | False | False (student-side ln(x²) is defined at x<0 where key 2ln x is not real → rejected, matching WeBWorK convention) |
| 2ln\|x\| vs ln(x^2) | **False (false negative)** | True |
| atan(x)+atan(1/x) vs π/2 | False | False (correct unless domain is x>0) |
| (x²−1)/(x−1) vs x+1 | True | True |
| asin(sin x) vs x | False | False |
Each case took ≤0.16 s. "Symbolic False" is not evidence of inequivalence; the numeric stage is the arbiter.

### Inferences (recommended design, code-level)
1. **Tokenise and validate before any `parse_expr`.** Allow only digits, decimal points *between digits*, `+-*/^()[]{},|=<>!`, whitespace, and identifiers from a per-problem whitelist (problem variables + `sin cos tan sec csc cot arcsin asin … ln log exp sqrt abs pi e oo inf DNE`). Reject `__`, any `.` not between digits, `lambda`, quotes, `[` indexing after identifiers, and input longer than about 200 characters. Better still, write a small Lark/pyparsing grammar that builds SymPy objects directly and never calls `eval`. Also cap exponent towers (e.g., parse with `evaluate=False` and reject `Pow` nodes whose exponent is a large integer), because evaluating something like `9^9^9` could hang. This last point is the researcher's inference and was not tested.
2. **Symbol handling.** Build `local_dict = {name: Symbol(name, real=True)}` (or `positive=True` when the problem's domain says so) and map `e→E`, `ln→log`, `arcsin→asin`, `abs→Abs`, `inf/infinity→oo`. Use `implicit_multiplication` plus `split_symbols_custom(predicate)` that splits only into *known* variable names, so `xy`→`x*y` when x and y are variables but `sinx` is rejected with "did you mean sin(x)?".
3. **Layered `is_equivalent(student, key, spec)`** where `spec` holds type, variables, domain (interval per variable or an excluded set), and tolerance:
   - a. Type gate (an expression vs a set is wrong; DNE vs a number is wrong).
   - b. Exact fast path: `sympy.nsimplify`/`Rational` for numbers; `(a-b).expand() == 0`; `a.equals(b)` for constants (it handles algebraic numbers via minimal polynomials).
   - c. Numeric sampling (the main decider for expressions): about 10–20 points per variable from the declared domain. Use rational or high-precision points with `lambdify(..., 'mpmath')` at mp.dps=30, skip points where the key is undefined or non-real, and fail if the student is undefined where the key is defined (WeBWorK's convention). Use relative tolerance 1e-9 at high precision, with an absolute floor (WeBWorK's `zeroLevel` idea) near zeros. Sample at least one point per connected piece of the domain (e.g., x<0 and x>0 for `1/x`).
   - d. Symbolic confirm (optional, for logging and disagreement triage): `simplify(a-b)` in a `multiprocessing.Process` killed after 1–2 s. Treat a timeout as "unknown".
   - e. Verdict ∈ {correct, incorrect, undecidable}. "Undecidable" must never become "correct" in the *bank pipeline*; in the student UI it can fall back to a self-grade.
4. **Equations:** STACK's numerator-ratio test (above). For "solve for y" answers, compare the solved forms instead.
5. **Sets and intervals:** parse interval notation and "x<3 or x≥5" into SymPy `Interval`/`Union`/`FiniteSet` and compare with `==` after `simplify` of endpoints. Numeric endpoints should be compared with `.equals`.
6. **Antiderivatives:** check `diff(student,x) - integrand` numerically at sample points (avoids the `log|x|` Piecewise issue), plus require that the student included `+C` if the course insists (a form test).
7. **Units:** `convert_to` both quantities to SI base units, compare the dimensionless magnitude with a relative tolerance (STACK's NumRelative default is 5%, which is loose; physics problems likely want 1–2% or a significant-figure test), and separately check dimensions match.

### Gaps
- No primary SymPy GitHub issue list was compiled for `simplify` hangs; the timeout recommendation rests on STACK's documented factoring/expansion timeouts and general experience.
- `parse_latex` robustness on real student LaTeX was not benchmarked. Math-Verify's README reports a comparison table on MATH but gives no methodology, so its numbers were not used.

---

## 3. Requiring a "simplified" or specific form

### Takeaway
Treat form as a separate *test* run after equivalence passes, using an unevaluated parse (`evaluate=False`) and structural predicates. STACK (FacForm, Expanded, LowestTerms, SingleFrac, PartFrac, CompSquare, NumDecPlaces, NumSigFigs) and Möbius (factor-irreducibility checks, blocking `factor(` in input) are the templates to copy.

### Cited Findings
- STACK separates "Equivalence" tests from "Syntactic form" tests (FacForm, PartFrac, SingleFrac, CompSquare, Expanded, LowestTerms) and numeric-format tests (NumSigFigs, NumDecPlaces) — [STACK docs: Answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/)
- Form checks need `simp:false`; many predicates only work unsimplified; use `EqualComAss(predicate(ex),true)` rather than `AlgEquiv(...)`. EqualComAss = equal up to commutativity/associativity of + and × (and − and ÷) — [STACK docs: Equivalence tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/)
- Möbius factored-form check: product of the response's factors equals the answer *and* each factor is irreducible; a separate pattern blocks the student typing `factor(...)` — [DigitalEd: Example Maple grading code](https://www.digitaled.com/support/help/admin/Content/INST-AUTHORING/QUESTION-TYPES/MAPLE-GRADED/Example-Maple-grading-code.htm)
- Möbius: equivalence does not override "simplify" instructions; instructors can disable equivalence — [DigitalEd: Enter equivalent responses](https://digitaled.com/support/help/student/Content/STUD-ENTERING-RESPONSES/Enter-equivalent-responses.htm)
- `parse_expr(..., evaluate=False)` keeps the expression as typed (`2**3` stays `2**3`; `srepr(parse_expr('2+3', evaluate=False))` = `Add(Integer(2), Integer(3))`) — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html) (verified by local run)
- WeBWorK's `reduceConstants`/`reduceConstantFunctions` default to 1 (so `2*3`→6, `sqrt(2)`→decimal), and `studentsMustReduceUnions=1` enforces a reduced form for unions — [WeBWorK wiki: Context flags](https://webwork.maa.org/wiki/Context_flags); [Answer Checker Options](https://webwork.maa.org/wiki/Answer_Checker_Options_(MathObjects))

### Inferences
- Suggested SymPy form predicates on the `evaluate=False` tree. All are inferences and untested beyond the basics:
  - *exact, not decimal:* `not tree.atoms(Float)`
  - *factored:* top node is `Mul`/`Pow`, and every non-constant factor `f` has `len(factor_list(f)[1]) == 1` with multiplicity 1 inside its own Pow (locally, `factor_list(expand((x+1)*(x-2)))` returns two linear factors)
  - *expanded:* `expand(e) == e` structurally on the evaluated form
  - *lowest-terms fraction:* `gcd(numer, denom) == 1` for Rationals typed as `a/b`
  - *rationalised denominator:* no `Pow(…, -1/2)` in the denominator
  - *simplified radical:* `sqrt(n)` with n square-free
  - *decimal places / sig figs:* inspect the raw string, not the parsed Float, since floats lose trailing zeros (STACK's NumDecPlaces requires them)
- Store per problem `form_requirements: [...]` and give feedback like "Correct value, but write it in factored form", ideally scored as "not yet correct" rather than wrong, for FSRS purposes.
- "Simplified" is ill-defined in general. Prefer concrete named forms per problem over a vague "simplify" flag.

### Gaps
- No published SymPy library implementing STACK-style form tests was found; these would need to be written and unit-tested.

---

## 4. Partial credit for multi-part problems, and proof / "show that" problems

### Takeaway
Multi-part problems should be split into parts, each with its own typed answer and test chain, like STACK's per-input PRTs. Follow-through (error-carried-forward) credit needs dependent tests evaluated against the *student's* earlier values. For proofs, published 2025–2026 evidence says LLM grading is usable only with a reference solution plus a marking scheme and a strong model; without them, LLMs over-score polished but wrong proofs. For a single-user app, self-grading against a rubric and model solution is the robust default.

### Cited Findings
- STACK: each input can have its own PRT, a separate PRT can depend on several inputs (formative only), and PRTs can add or subtract score per branch with a default penalty of 0.1 per wrong attempt. The PRT page does not describe follow-through marking — [STACK docs: Potential response trees](https://docs.stack-assessment.org/en/Authoring/Potential_response_trees/)
- Möbius set partial credit = |response ∩ answer| / |answer|, with 0 if the response has more elements than the answer — [DigitalEd: Example Maple grading code](https://www.digitaled.com/support/help/admin/Content/INST-AUTHORING/QUESTION-TYPES/MAPLE-GRADED/Example-Maple-grading-code.htm)
- ProofBench (145 olympiad problems, 435 expert-graded LLM proofs, 0–7 scale): o3 with reference solution plus marking scheme reached MAE 0.964, Kendall τ 0.502 and bias −0.008. With no context, MAE was 1.680 and bias +0.924, with only 49.5% of grades within one point. GPT-4o even with reference and scheme had MAE 2.197. The paper ranks effect sizes as "backbone ≫ context ≫ instruction". Without context, evaluators over-scored weak proofs (those graded 0–2) by an average of 1.7 points, and 80% of the 20 largest disagreements involved "sophisticated presentation but fundamental logical errors". Evaluators did worst on outputs from their own model family. Ensembling 5 runs (median) lowered MAE from 0.981 to 0.926 — [Reliable Fine-Grained Evaluation of Natural Language Math Proofs (arXiv 2510.13888)](https://arxiv.org/html/2510.13888v1)
- MathArena USAMO 2026: graded by an LLM jury (GPT-5.4, Gemini-3.1-Pro, Opus-4.6) using generated grading schemes, taking the minimum score when judges were within 2 points and reconciling otherwise, with *every* solution then human-reviewed. Human review changed only 3 solutions, by ≤2 points. Gemini-3.1-Pro and Opus-4.6 "substantially overestimate their own performance". Scheme quality was uneven, and "small phrasing issues in the schemes misled the judges". The pipeline also wrongly graded unfinished Opus-4.6 reasoning chains as complete (later set to 0) — [MathArena: USAMO 2026](https://matharena.ai/usamo/)
- BrokenMath (competition problems perturbed into *false* statements): the best model, GPT-5, gave sycophantic answers 29% of the time — [BrokenMath (arXiv 2510.04721)](https://arxiv.org/abs/2510.04721)

### Inferences
- Multi-part design: `parts: [{id, prompt, answer_spec, depends_on: [part_ids], key_fn}]`. For follow-through, `key_fn` is a SymPy function that recomputes the expected part-(b) answer from the student's part-(a) answer. This works only for template or programmatic problems where the dependence is computable. Score per part. For FSRS, either schedule at part or skill level, or grade the card "Again/Hard/Good" by fraction of parts correct.
- Proof/"show that": (1) show the model solution and a 3–6 item marking checklist (key steps), (2) the student self-grades each item, (3) optionally an LLM pass with the reference solution and checklist flags missing steps. Following ProofBench, never run an LLM grader without the reference and rubric. For an offline app, the LLM pass would need network access or must be skipped.
- "Show that X = Y" problems can often be auto-checked *partially*. Ask for a key intermediate quantity as a typed answer, then self-grade the argument.

### Gaps
- No primary documentation was found on STACK's or WeBWorK's follow-through/ECF mechanics (WeBWorK custom checkers presumably support it, but the page was not retrieved).
- No studies were found on the reliability of *student self-grading* of proofs against rubrics in self-study apps.

---

## 5. Published evidence (2023–2026) on LLM error rates in solving and in GENERATING problems and answer keys

### Takeaway
Final-answer solving of standard and competition problems is near-saturated for frontier models (AIME 2026 top scores ~95–99%). The dominant residual errors in a bank therefore come from **bad problems and bad keys**: ambiguous or ill-posed statements, wrong source keys, transcription and translation errors. LLMs are poor at *detecting* these. Model-generated answers to synthetic problems are wrong at substantial rates (~30% for mid-size models in MathClean), and even professionally curated benchmarks carry wrong keys at percent-level rates.

### Cited Findings
**Solving accuracy (frontier)**
- AIME 2026: BenchLM's leaderboard (updated Oct 29 2026, 33 models) lists GLM-5.2 at 99.2%, several models at 97–98%, and Kimi K2.6 at 96.4%. This is a secondary aggregator and the scoring method is not described — [BenchLM: AIME 2026](https://benchlm.ai/md/benchmarks/aime2026.md)
- MathArena now marks all its final-answer competitions (AIME 2025/2026, HMMT Feb 2026, etc.) and proof competitions as "Deprecated". Top "expected performance" on its remaining non-deprecated sets is GPT-6.1 Sol (max) at 84.0% ±2.1% — [MathArena](https://matharena.ai/)
- USAMO 2026 proofs: GPT-5.4 95.2%, Gemini-3.1-Pro 74.4%, Opus-4.6 47.0% — [MathArena: USAMO 2026](https://matharena.ai/usamo/)
- Platinum benchmarks (cleaned versions): o1 (high) has the best overall error, 0.75%. On 274 cleaned GSM8K items, the best models made about 1–3 errors (DeepSeek-R1 ~1, o1-high 2, Claude 3.5 Sonnet 3) — [Vendrow et al., Do LLM Benchmarks Test Reliability? (arXiv 2502.03461)](https://arxiv.org/pdf/2502.03461)

**Error rates in existing answer keys and problems (human-made)**
- Platinum benchmark cleaning found these flawed items. "Removed" means ambiguous or ill-posed; "mislabeled" means a wrong key. GSM8K: 26/300 removed (8.7%), 1 mislabeled (0.3%). SVAMP: 27/300 (9.0%) removed, 3 (1.0%) mislabeled. MultiArith: 3 (1.7%) removed, 3 (1.7%) mislabeled. SingleEq: 9/109 (8.3%) removed. MMLU HS Math: 2/270 (0.7%) removed. The method was to "manually inspect any example on which at least one LLM makes an error". The counts are a **lower bound**, because flawed items that all models answered consistently with the label are missed. 48% of the original GSM8K errors and 77% of the SVAMP errors were attributable to the benchmark, not the model — [arXiv 2502.03461](https://arxiv.org/pdf/2502.03461)
- Omni-MATH-2 (Jan 2026): a manual audit of Omni-MATH checked compilability, solvability and verifiability, producing a clean exact-answer subset (n=4181) and a tagged non-standard subset (n=247) needing proofs, estimates or images. Expert annotation found the original Omni-Judge wrong in 96.4% of its disagreements with GPT-5 mini — [Ballon et al., arXiv 2601.19532](https://arxiv.org/abs/2601.19532)
- Physics benchmark audit (arXiv 2609.13009, reported via a secondary blog that says it checked the paper): of 250 responses recorded as wrong across HLE-Physics, PHYBench, PRISM-Physics and UGPhysics, 143 were benchmark errors (defective item or key), 95 were grader errors, and only 12 were genuine model errors. CMT-Benchmark had defects in 30 of 50 items. The sampling covered only items every model got wrong, so these are not benchmark-wide rates — [Pebblous blog summary](https://blog.pebblous.ai/report/physics-benchmark-defect-floor-2026-09/en/) (primary: [arXiv 2609.13009](https://arxiv.org/abs/2609.13009), not fetched directly)
- Formal benchmarks: in ProofNet, 104/367 (28%) formal statements are mathematically false and 204/367 (56%) are unfaithful to the informal source. Across six other benchmarks, unfaithful rates ranged from 4.8% to 60.0% — [Ground False (ICML 2026)](https://icml.cc/virtual/2026/82611)

**Error rates in LLM-generated problems and answers**
- MathClean / MathDebugger: of 2,000 model-generated answers (Qwen2.5-Math-72B, Qwen2.5-72B, Llama-3.1-8B, Qwen2.5-Math-1.5B; CoT and PoT), **30.5% were wrong** (163/800 on GSM8K-level, 447/1,200 on MATH-level). Of the wrong answers, 52% were logic errors, 38% computation errors and 10% expression errors. Labels came from 30 STEM-graduate annotators plus reviewers with dual review (Fleiss κ 0.69–0.88) — [MathClean (arXiv 2502.19058)](https://arxiv.org/html/2502.19058v1); [MathDebugger, EMNLP 2026](https://aclanthology.org/2026.emnlp-main.608.pdf)
- The MathClean introduction cites a report that "approximately 50% of the generated QA pairs are incorrect" in OpenMathInstruct (a secondary citation inside the paper) — [arXiv 2502.19058](https://arxiv.org/html/2502.19058v1)
- OpenMathInstruct-2: synthetic questions have no ground truth, so the key was the **majority vote of 32 solutions** (Llama-3.1-405B, T=0.7). An LLM judge plus reward model flagged 6–12% of solutions, and a manual check of 20 flagged items found ~60% truly incorrect. Filters flagged 45–67% of solutions from a weaker 8B teacher. Training was robust to ≤20% bad solutions, which is fine for SFT data but irrelevant to a "zero wrong keys" bank — [OpenMathInstruct-2 (arXiv 2410.01560)](https://arxiv.org/abs/2410.01560)
- ValiMath (synthesised questions; the pool was deliberately enriched for errors, so this is *not* a prevalence rate): 848/2,147 annotated items were flawed. The taxonomy was contradiction 13.97%, minimal-domain error 7.96%, instruction error 6.66%, non-semantic or linguistic error 5.54%, and completeness (missing condition) 5.36% — [Let's Verify Math Questions Step by Step (arXiv 2505.13903)](https://arxiv.org/html/2505.13903v2)

**LLMs' ability to detect bad problems and keys (the weak link)**
- MathClean detection accuracy (GSM8K / MATH splits). Question-error detection: GPT-4o 72.4 / 72.5, o1-mini 74.9 / 77.0, o1-preview 72.1 / 74.0, DeepSeek-R1 71.3 / 74.5. Answer-error detection: GPT-4o 80.8 / 77.3, o1-preview 75.4 / 77.3, DeepSeek-R1 76.8 / 76.3. o1 judged a contradictory geometry question correct — [arXiv 2502.19058](https://arxiv.org/html/2502.19058v1)
- Faulty-problem study (363 faulty problems, 2024 models): with no hint, the best model flagged only 33.3% (Gemini-1.5-Pro), GPT-4 31.4% and Claude-3-Opus 27.8%; the 10-model average was 19.7%. With a hint that the problem *may* be faulty, detection rose to 79–96%. With a misleading hint ("the problem is valid"), detection fell back to about the no-hint level ("high confirmational bias") — [From Blind Solvers to Logical Thinkers (arXiv 2410.18921)](https://arxiv.org/pdf/2410.18921)
- MathQ-Verify (5-stage question validation) on ValiMath: GPT-o4-mini precision 80.88, F1 83.36. Multi-model voting: precision rises with the unanimity requirement, from 86.72% for 1 model to 91.42% for 3/3 and 92.44% for 5/5, while recall falls from 68.90% to 50.81% — [arXiv 2505.13903](https://arxiv.org/html/2505.13903v2)
- Agreement as a confidence signal (2026): on GPQA, gpt-4.1 answers with self-consistency ≥0.8 were still wrong 48% of the time. Across providers, models that both erred chose the *same* wrong option more often than chance (e.g., .71 vs .38 null for claude-sonnet-4.6, p=.005). The authors advise treating agreement as "a coarse, cost-saving signal, not as a trustworthy confidence threshold" and warn against treating cross-provider agreement as evidence of correctness. On AIME, confident errors were "often dispersed" (no single stable wrong integer) — [When LLMs Agree, Are They Right? (arXiv 2607.08065)](https://arxiv.org/pdf/2607.08065)

### Inferences
- For curated sources (OPL, OpenStax, exams), expect roughly 0.3–2% wrong keys and 1–9% ambiguous or ill-posed items (the Platinum lower bounds on well-used datasets). Harder or less-used material is likely worse; the physics and Omni-MATH audits suggest that.
- For AI-original problems, the dominant risk is *ill-posedness* (contradictions, missing conditions, multiple valid answers), not arithmetic. Blind re-solving does **not** catch this: the solver "blindly solves" a broken problem (≤33% detection without a prompt to look for flaws), and two models can agree on an answer to an ill-posed problem. A dedicated, explicitly adversarial well-posedness check is required.
- Errors on hard problems are less correlated than on multiple-choice items (AIME confident errors are dispersed), so two-solver agreement is *more* informative for numeric-answer problems than for MC. This supports keeping free-response numeric answers and converting MC sources to free response where possible.

### Gaps
- No published estimate was found of the residual wrong-key rate *after* a pipeline like "two independent solves agree + CAS check". The achievable floor is unmeasured.
- No published error rates were found specifically for OpenStax answer keys or WeBWorK OPL problems.
- The AIME 2026 figures come from a secondary aggregator (BenchLM), and MathArena's per-competition final-answer leaderboards did not load.

---

## 6. Techniques to drive answer-key errors toward zero

### Takeaway
The strongest guarantee comes from **making the key a computation**: a CAS or program computes the answer from structured parameters, and the model only writes prose around it. Next best is **multiple independent derivations that fail differently**: a source key plus a blind natural-language solve plus a program-of-thought solve, compared by the SymPy checker, plus back-substitution or property checks, plus an explicit well-posedness audit. Agreement between two LLM solves alone is a coarse signal. Rule-based checkers have near-perfect precision but miss ~5–40% of correct equivalents; LLM judges catch more but are exploitable. Use rules first, with LLM review only for rule-rejected disagreements, and drop anything still disputed.

### Cited Findings
- Self-consistency (majority over sampled chains) improves over single chain-of-thought: GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2% — [Wang et al., Self-Consistency (arXiv 2203.11171)](https://arxiv.org/abs/2203.11171)
- Self-consistency-based confidence (cluster size, pairwise agreement; N=16) is better calibrated than p(True) or logits on GSM8K and MathQA (e.g., Mixtral-8×7B-Inst GSM8K Brier 0.086 vs 0.198), and stabilises around N=8 — [Self-Consistency Boosts Calibration for Math Reasoning (arXiv 2403.09849)](https://arxiv.org/pdf/2403.09849)
- Program of Thoughts (model writes code, interpreter computes) gives "an average performance gain over CoT by around 12%" — [PoT (arXiv 2211.12588)](https://arxiv.org/abs/2211.12588)
- Code-based self-verification (GPT-4 Code Interpreter writes code to *check* its own answer and amends when the check fails) raised zero-shot MATH accuracy from 53.9% to 84.3% — [arXiv 2308.07921](https://arxiv.org/abs/2308.07921)
- Process supervision beats outcome supervision; the PRM-trained model "solves 78% of problems from a representative subset of the MATH test set" (PRM800K = 800,000 step labels) — [Let's Verify Step by Step (arXiv 2305.20050)](https://arxiv.org/abs/2305.20050)
- Rule-based verifiers: precision ≥99% on every dataset, but average recall only ~86% (14% of correct answers rejected). The HuggingFace verifier's recall was 0.88–0.95. Failures were format differences, equivalent representations (e.g., π/4 vs 45°) and units — [Pitfalls of Rule- and Model-based Verifiers (arXiv 2505.22203)](https://arxiv.org/html/2505.22203v2)
- TinyV: the Prime Verifier mislabeled 38.5% of correct responses as incorrect (>50% on CN_K12-sourced items). The top causes were natural-language elements in answers, formatting, and notation such as intervals vs inequalities — [TinyV (arXiv 2505.14625)](https://arxiv.org/html/2505.14625v2)
- Model-based verifiers can be fooled. Attack success rates averaged 23.7% (Qwen2.5-Math-1.5B as judge) down to 7.7% (general-verifier) and 0.1–0.4% (discriminative xVerify). Lone symbols like "{", gibberish, or prefixes like "As an AI assistant, I know the answer is correct" could flip verdicts. Recommended: a **hybrid** with rules first and a model verifier only for rule-rejected cases, which raised recall ~3 points while keeping precision >98% — [arXiv 2505.22203](https://arxiv.org/html/2505.22203v2)
- Multi-model unanimity on question validity tops out at ~92% precision (5/5 agreement), at the cost of halving recall — [arXiv 2505.13903](https://arxiv.org/html/2505.13903v2)
- With a hint that a problem might be faulty, models' faulty-problem detection jumps from ≤33% to 79–96% — [arXiv 2410.18921](https://arxiv.org/pdf/2410.18921)
- Using agreement to stop sampling early ("stop-when-consensus") used 60% fewer samples (19.8 vs 50) at equal error — [arXiv 2607.08065](https://arxiv.org/pdf/2607.08065)
- GSM-Symbolic template QA: automated checks (no original values left in the template; original values satisfy all conditions; the template reproduces the original answer), 10 manual samples per template, and a post-check that each generated question is answered correctly by ≥2 models, otherwise manual re-review — [GSM-Symbolic (arXiv 2410.05229)](https://arxiv.org/html/2410.05229v2)

### Inferences (pipeline design)
**Acceptance rule by provenance** (recommended; inference):
| Provenance | Independent signals required to ACCEPT |
|---|---|
| Source with official key (OPL PG-computed answer, OpenStax odd answers, exam official answers) | key ≡ blind model solve (SymPy checker) **and** well-posedness pass |
| Source without key (OpenStax evens, exams without official answers) | blind NL solve ≡ independent PoT/SymPy solve (different prompt, ideally a different model) **and** back-substitution/property check where applicable **and** well-posedness pass |
| Template (parameterised, answer computed by code) | template verified once (below) + per-instance constraint checks in code; no per-instance LLM call |
| AI-original, CAS-checkable answer | generator's intended answer ≡ blind NL solve ≡ PoT solve (3 signals) **and** adversarial well-posedness pass **and** uniqueness check |
| AI-original, olympiad/proof-style | do not auto-accept as auto-graded; ship as self-graded with rubric, or require a strong-model reference solution reviewed by a second strong model with an explicit "find the flaw" prompt; quarantine until the owner has solved it |

**Concrete checks that cost no tokens** (inference):
- *Back-substitution:* for "solve", substitute every claimed root into the original equation (exact or 50-digit numeric) and also run `solveset` over the stated domain to confirm the *set* of roots (catches missing or extraneous roots).
- *Derivative/integral:* differentiate the claimed antiderivative; check the claimed derivative numerically with a central difference; check a definite integral with `mpmath.quad`.
- *Limits:* evaluate `f` at x = a ± 1e-8 (mpmath high precision) as a sanity check against the CAS `limit`.
- *Inverse/composition:* `f(g(x)) == x` on samples.
- *Systems/linear algebra:* `A*x - b == 0`; eigenpairs `A*v - λ*v == 0`; inverses `A*Ainv == I`. All exact in SymPy rationals.
- *Statistics:* recompute from the data with `statistics`/`numpy` or `scipy.stats`.
- *Trig/exact values:* compare the claimed exact value with `N(..., 50)`.
- *Units:* dimensional analysis of the final quantity.

**Well-posedness audit (LLM, cheap model OK but prompted adversarially):** ask explicitly "This problem may be flawed. List missing conditions, contradictions, ambiguous wording, multiple valid answers, domain issues; answer VALID/FLAWED". Supported by the jump from ≤33% to 79–96% detection when hinted. Run *before* the solves, and drop on any FLAWED.

**Uniqueness:** require that the solver output the *complete* answer set (all solutions, or "DNE"), and compare sets, not single values. Many keys are wrong because a root, a case or a sign is missing.

**Disputes:** the owner's plan (drop disputed problems) matches the evidence. Never let an LLM judge *overrule* a SymPy "not equal". Use the LLM judge only to rescue rule-checker false negatives (format mismatch), and only when it outputs a canonical expression that SymPy then confirms.

**Post-release:** the "flag bad key" button plus automatic quarantine (hide on flag; re-verify with a stronger model and a different method), and log the student's answer so a SymPy re-check against alternative keys is possible.

### Gaps
- No study was found that measures the *joint* false-accept rate of "two different frontier models agree + CAS-checked + well-posedness audit". Zero errors cannot be proven; it can only be driven down and then monitored with the flag button.
- No published cost-per-verified-problem figures were found from adaptive-learning companies.

---

## 7. Verifying extracted problems from sources (errata, OCR/LaTeX errors, odd-only keys, transcription)

### Takeaway
Source keys are good but not perfect, and the commonly assumed open sources have licence and coverage caveats. OpenStax student keys cover only odd-numbered exercises, and several math titles are CC BY-NC-SA, not CC BY. The OPL is ~35,000 problems under CC BY-NC-SA 3.0. The most reliable extraction path is from *structured* sources: PG code from the OPL, where the answer is computed by the problem's own code, and CNXML/HTML from OpenStax rather than PDF OCR. Every extracted item then goes through the same blind-solve-and-compare gate.

### Cited Findings
- OpenStax Precalculus 2e: "Students can find odd-numbered answers to Review Exercises, Practice Test, and Section Exercises in the Answer Key… Answers to all odd and even-numbered questions are provided only to instructors." The licence is **CC BY-NC-SA 4.0** (not CC BY) — [OpenStax Precalculus 2e preface](https://openstax.org/books/precalculus-2e/pages/preface)
- OpenStax errata are reviewed by subject-matter experts. Online versions are updated twice a year at semester end, and PDF/print only "when substantial changes are present". Past errata suggestions are viewable via each book's Errata tool — [OpenStax: Errata correction process](https://help.openstax.org/s/article/Errata-correction-process)
- WeBWorK OPL: "approximately 35,000 problems". Licence CC BY-NC-SA 3.0 unless otherwise indicated. Hosted at GitHub `openwebwork/webwork-open-problem-library`. Submissions are reviewed by the OPL Editorial Board, and bug fixes ship via repository updates — [WeBWorK wiki: Open Problem Library](https://webwork.maa.org/wiki/NPL)
- Big-Math's source cleaning shows the practical issues: removed 625 problems (13%) with Asymptote figures (`[asy]`); removed problems whose solution lacked exactly one `\boxed` answer; regex-cleaned 2,535 aops_forum items; filtered multiple-choice (117,018), multi-part (87,984), proof (40,509), yes/no and true/false items with regex plus Llama-3.1-70B classifiers iterated to >98% recall — [Big-Math (arXiv 2502.17387)](https://arxiv.org/pdf/2502.17387)
- Omni-MATH-2's audit criteria were LaTeX compilability, solvability (missing figures or information added), verifiability, and tagging items needing proof, estimate or image — [arXiv 2601.19532](https://arxiv.org/abs/2601.19532)
- The ANTLR LaTeX parser can silently drop input (`x -` → `x`), so LaTeX→SymPy conversion of keys must use strict mode or the Lark backend, which rejects ill-formed input — [SymPy docs: Parsing](https://docs.sympy.org/latest/modules/parsing.html)

### Inferences
- **Licence** (owner's personal, non-distributed use is low-risk, but the plan says "built as if multi-user"): track `license` and `attribution` per item. NC-SA content cannot go into a commercial product, and SA requires derivatives (including translations and edited problems) under the same licence.
- **OpenStax evens** have no student key. Treat them as "source without key" (two independent derivations needed).
- **OPL extraction:** prefer executing or interpreting the PG file over scraping rendered HTML. The PG code *computes* the answer (MathObjects `Compute(...)`), and random seeds give variants. A simple route is rendering many seeds with the standalone WeBWorK renderer (PG is Perl, so this is a build-time dependency, not an app dependency) and storing (statement, answer, answer-type, seed). Problems depending on images, applets or custom checkers should be skipped or flagged.
- **Transcription checks (token-free):** LaTeX must compile (KaTeX/MathJax render without errors); every `$...$` key must parse in strict mode; numbers in the statement must appear in the source text (regex diff between OCR text and final statement); figure references ("see the graph") with no figure → drop.
- **Mismatch detection:** if the blind solve disagrees with the official key, do *not* auto-trust either. Send it to a stronger model with both answers plus the instruction "one may be wrong, or the problem may be ambiguous; decide or say AMBIGUOUS", then drop unless the SymPy check confirms the decision with back-substitution. Platinum-benchmark data suggests most such disagreements are ambiguity, not a wrong key.
- Check OpenStax errata pages for the specific books before extraction, and re-extract after the twice-yearly updates.

### Gaps
- No quantitative error rates were found for OpenStax answer keys or OPL problems.
- CLP Calculus (UBC) and MIT OCW exam licensing and key formats were not researched here (adjacent researchers may cover them).
- The reuse policies of Japanese university entrance exams were not covered in this scope.

---

## 8. Parameterised variants (templates): generating many fresh problems and verifying the template once

### Takeaway
Template problems, where code computes the answer from random parameters under explicit constraints, give the strongest correctness guarantee and near-zero marginal token cost. This is WeBWorK PG's model and GSM-Symbolic's. Verify the *template* once (code review, a property-based sweep over many seeds with SymPy checks, a few LLM blind solves of sampled instances), then enforce constraints per instance in code.

### Cited Findings
- GSM-Symbolic templates use typed placeholders with value domains (e.g., x, y, z ∈ [5,99], total ∈ [100,499]) and *conditions* (e.g., `x+y+z+ans == total`, divisibility so answers are whole numbers). The answer is computed in the template. QA: automated checks, 10 manual samples per template, and ≥2 models must answer each instance correctly or it is re-reviewed. Scale: 100 templates × 50 samples — [GSM-Symbolic (arXiv 2410.05229)](https://arxiv.org/html/2410.05229v2)
- Changing numbers (not just names) widened model accuracy variance (e.g., >12–15% worst-to-best gaps for some models), and adding irrelevant clauses (GSM-NoOp) caused drops "up to 65%". Parameter variation genuinely changes difficulty — [arXiv 2410.05229](https://arxiv.org/html/2410.05229v2)
- WeBWorK supports per-variable domains and resolution for test points, and problems get random parameters per student seed — [WeBWorK wiki: FormulaTestPoints](https://webwork.maa.org/wiki/FormulaTestPoints)

### Inferences
- Template spec (inference): `params: {a: randint(-9,9, exclude=[0]), b: …}`, `constraints: [discriminant(a,b,c) > 0, is_square(discriminant), gcd(...)==1, answer_is_nice(...)]`, `answer_fn(params) -> sympy object`, `answer_type`, `render(params) -> statement`, `distractor_fns` (common-error answers for feedback), `difficulty_features(params)`.
- One-time template verification (inference):
  1. Property-based sweep (e.g., `hypothesis` or 1,000–10,000 random seeds): for every instance, the constraints hold, `answer_fn` agrees with an *independent* SymPy route (e.g., `solveset` vs the quadratic-formula code; `integrate` vs a numeric quad), back-substitution passes, and no degenerate cases occur (division by zero, double roots when the template says "two solutions", answers that simplify to 0 or 1, and so on).
  2. LLM blind-solve of ~5–10 sampled instances, including extreme parameters. Any disagreement blocks the template.
  3. Freeze the template with a content hash. Re-verify only when the code changes.
- Per-instance cost is then zero tokens. Per-instance code checks (constraints + back-substitution) run in milliseconds and can even run in the app at serve time to make fresh instances on demand, which suits FSRS reviews since the same skill gets a new instance each time.
- For FSRS, a *skill* card can draw a fresh instance per review, so the student can't memorise the specific answer. Templates are the natural fit for algebra, trig and Calc 1 drill skills, with sourced and AI-original fixed problems for richer items.
- Templates suit LLM authoring well: the model writes the *code*, which is checked mechanically, instead of writing answers.

### Gaps
- No published error rates were found for LLM-written problem templates (as opposed to LLM-written problems).

---

## 9. Deduplication / near-duplicate detection, and difficulty estimation before user data

### Takeaway
Use the large-dataset recipe: normalise text, exact-hash dedup, MinHash-LSH on character or token shingles (threshold ~0.6–0.7), then embedding similarity (e.g., all-MiniLM-L6-v2) to catch paraphrases, with an LLM or human check only on candidate pairs. For math, also compare *answers plus structure*: same answer and similar statement means a likely duplicate. For cold-start difficulty, direct LLM ratings are poor. Simulated-student IRT correlates 0.75–0.82 with real item difficulty, but is costly. Cheap proxies (solve rate across sampled weak-model attempts, step count, source position) are reasonable priors that FSRS and user data then overwrite.

### Cited Findings
- Big-Math dedup: MinHashLSH (128 hash functions, similarity threshold 0.6 or 0.7) within NuminaMath subsets; exact-match dedup ignoring whitespace; then SemDeDup with all-MiniLM-L6-v2 removing pairs with cosine >0.5 (thresholds 0.95–0.2 were tested); decontamination against held-out test problems removed 4,229 items — [Big-Math (arXiv 2502.17387)](https://arxiv.org/pdf/2502.17387)
- Big-Math used a *solve-rate* filter (64 Llama-3.1-8B samples plus 5–8 Llama-3.1-405B samples per problem), keeping problems either model solved, and noted that this "does not guarantee that removed data has an incorrect answer" — [arXiv 2502.17387](https://arxiv.org/pdf/2502.17387)
- OpenMathInstruct-2 decontamination: embedding search plus LLM paraphrase detection, removing ~50K of 569K synthetic questions — [arXiv 2410.01560](https://arxiv.org/abs/2410.01560)
- Difficulty: simulated "classrooms" of LLM-role-played students answering NAEP items, fitted with IRT, gave correlations with real item correctness of 0.75 (grade 4), 0.76 (grade 8) and 0.82 (grade 12). A *weaker* model (Gemma) predicted difficulty better than stronger ones, and the authors call LLMs "poor direct judges of problem difficulty" — [Take Out Your Calculators (arXiv 2601.09953)](https://arxiv.org/abs/2601.09953v1)

### Inferences
- Math-specific normalisation before hashing: canonicalise LaTeX (strip `\left`/`\right`, spacing, `\dfrac`→`\frac`), replace numbers with a placeholder for a "structure hash", and store the SymPy canonical answer. Two problems with the same structure hash are *template siblings*, which is useful for "same skill, different numbers" rather than a duplicate to delete.
- Cosine 0.5 with MiniLM is aggressive (it removes related but distinct problems). For a learning bank, where variety within a skill is wanted, use a high threshold (~0.9) for auto-removal and 0.75–0.9 for review.
- Cheap difficulty prior: run a *small* model k times (e.g., k=4–8 attempts by Haiku-class or a local model) and use its failure rate, which matches the finding that weaker models are better difficulty proxies. Add features like source (exam level, exercise position in a section), step count from the reference solution, and number of skills tagged. Let FSRS difficulty and observed accuracy take over quickly.

### Gaps
- No math-specific near-duplicate benchmark with precision/recall numbers was found.
- No study was found that validates small-model solve rate as a difficulty proxy for college-level calculus items specifically.

---

## 10. Token and cost efficiency

### Takeaway
Most of the pipeline should be deterministic code: extraction, LaTeX validation, parsing, SymPy comparison, back-substitution, dedup hashing, template sweeps. LLM calls belong to tagging (cheapest model, batched, cached taxonomy), the well-posedness audit, and blind solves (mid-tier model by default, top model only for hard or disputed items). At current Claude API prices with the 50% Batch discount, routine problems cost on the order of a cent or two each to verify; hard problems with long reasoning cost about 5–20 cents each.

### Cited Findings
- Claude API base prices per MTok (input/output): Haiku 5.5 $0.10/$0.50 (prompts ≤100k tokens; $0.50/$2.50 above), Sonnet 5.5 $2/$10, Opus 5.5 $4/$20. The Batch API gives "a 50 percent discount on both input and output tokens" (Haiku 5.5 $0.05/$0.25, Sonnet 5.5 $1/$5, Opus 5.5 $2/$10). Prompt caching: 5-minute write 1.25×, 1-hour write 2×, cache read 0.1× base input (0.05× on Opus 5.5 and Sonnet 5.5). Prices may change — [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Agreement-based early stopping cut samples 60% at equal error — [arXiv 2607.08065](https://arxiv.org/pdf/2607.08065)
- A weaker teacher's outputs were flagged as wrong far more often (45–67%) than the 405B teacher's, so the solver tier matters for key quality — [arXiv 2410.01560](https://arxiv.org/abs/2410.01560)
- Hybrid verification (rules first, model verifier only for rule-rejected cases) keeps precision >98% while recovering recall — [arXiv 2505.22203](https://arxiv.org/html/2505.22203v2)

### Inferences (cost model; all numbers are the researcher's estimates)
- **Deterministic (0 tokens):** PDF/HTML/PG extraction, regex segmentation, LaTeX render and parse checks, SymPy equivalence, back-substitution, unit checks, MinHash/embedding dedup (a local embedding model), template sweeps, form checks, skill-tag *validation* (the tag must exist in the taxonomy).
- **Tagging:** Haiku 5.5 via Batch. Put the skill taxonomy (a few thousand tokens) in a cached system prefix and send problems in groups of about 10–20 per request with JSON output. Estimate per problem: ~300 input + ~60 output tokens → ≈ $0.00003. 10,000 problems ≈ $0.30–$1, which is negligible.
- **Well-posedness audit:** Haiku or Sonnet, ~400 in / ~200 out. Sonnet batch ≈ $0.0014 per problem.
- **Blind solve (routine college algebra, trig, Calc 1):** Sonnet 5.5 batch, ~400 in / ~1,500–3,000 out (assuming reasoning tokens bill as output) ≈ $0.008–$0.016 per solve. A second independent solve as PoT/SymPy code ≈ similar. **≈ $0.02–$0.03 per verified routine problem**, so 10,000 problems ≈ $200–$300.
- **Hard / olympiad / AI-original:** Opus 5.5 batch, ~10,000 output tokens ≈ $0.10 per solve; 2–3 solves plus audit ≈ $0.25–$0.35 per accepted problem. Many will be rejected, so the cost per *accepted* hard problem may be 2–3× that.
- **Templates:** ~$0.05–$0.20 one-time per template (authoring + 5–10 instance solves), then $0 per instance. For high-volume drill skills this is far cheaper than per-problem verification.
- **Escalation ladder:** cheap solve first. Escalate to a stronger model only on disagreement with the source key or between solves, then drop if still disputed. With early stopping, most items need just 1–2 calls.
- Batch results arrive asynchronously, which suits an offline build pipeline. Cache the stable prefix (taxonomy, instructions, few-shot examples).

### Gaps
- Whether the Batch discount stacks with prompt-cache read pricing, and exactly how thinking tokens are billed, were not confirmed on the pricing page fetched.
- No published per-problem verification costs from adaptive-learning companies were found. No engineering blogs from such companies on question-bank QA were located in this pass.

---

## 11. Translating Japanese exam problems into English while preserving mathematical meaning

### Takeaway
Raw LLM translation of math problems has meaningful *content* error rates. For Japanese, human experts disagreed with GPT-4o drafts on content in about 13–15% of problems in the PolyMath benchmark, and "a single mistake in a key term can distort the entire problem". Translation must be verified like extraction: a math-term glossary, number and formula preservation checks in code, and a blind solve of the English version that must reproduce the official Japanese answer.

### Cited Findings
- PolyMath translation pipeline: GPT-4o pre-translation → math experts extract key terms (~30 terms/hour) → language experts with math knowledge calibrate (~8 samples/hour), focusing on term accuracy and lossless formula transfer. For Japanese, experts disagreed with the GPT-4o draft on **content** in 12.8% (medium), 15.2% (high) and 12.8% (top) of samples, and on fluency in 5.6%, 9.6% and 14.4%. "Mathematical translation is far more challenging than general translation… A single mistake in a key term can distort the entire problem, rendering the sample completely invalid" — [PolyMath (arXiv 2504.18428)](https://arxiv.org/pdf/2504.18428)
- The widely used MGSM multilingual math benchmark contains "several translation errors" that, together with answer-extraction issues, distort cross-language results. A semi-automatic QA method found them, and a corrected MGSM-Rev2 was released. After fixes, the reported language gap "mostly disappears" — [Mind the Gap… or Not? (arXiv 2511.05162)](https://www.arxiv.org/abs/2511.05162)

### Inferences
- The PolyMath figures are for GPT-4o (2024–25). Current models are probably better, but no newer measurement was found. Assume a non-trivial error rate and verify.
- Translation verification steps (inference):
  1. Build a JA→EN glossary of exam terms that change meaning if mistranslated, e.g., 以上/以下 (≥/≤, inclusive) vs より大きい/未満 (>/<, strict); 整数 (integer) vs 自然数 (natural number, which in Japanese school convention starts at 1); 実数解 (real solutions) vs 解; 少なくとも (at least); ただし (provided that), conditions often placed at the end of the problem; 最大値・最小値 (max/min values) and whether attaining points are also asked for; 求めよ (find) vs 示せ/証明せよ (show/prove), which marks a proof item; Japanese log notation (log without a base often means natural log in university exams but base-10 in some contexts); 弧度法 (radians).
  2. Code checks: every number, variable and LaTeX formula in the source must appear unchanged in the translation (extract with regex and diff); inequality direction and inclusivity must match the glossary mapping.
  3. Blind solve the *English* version, and accept only if it matches the *official Japanese* answer (or the Japanese-version solve) under the SymPy checker. This catches meaning-changing translation errors because they change the answer.
  4. Optional back-translation EN→JA by a different model, with a model or diff comparison of conditions. This is cheaper than a human but weaker than step 3.
  5. Multi-part exam problems (小問 (1)(2)(3)) often build on each other. Keep them as linked parts (Section 4).
- Many Japanese entrance-exam answer sheets are short or proof-style (記述式). Problems whose official key is a proof should be routed to self-grading, not auto-checking.

### Gaps
- No study was found that measures translation error rates specifically for Japanese university entrance exam math, or for current-generation models.
- The rules for reusing Japanese exam problems (copyright, permission policies) were outside this researcher's scope and were not verified.
