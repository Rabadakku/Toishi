"""Form checks (step 5): run on the answer as typed, after its value is known to be right.

factored, expanded, simplified, lowest-terms, exact and decimal(n), as in
docs/card-format.md. They look at our own tree, because SymPy rewrites what it builds
(`2*(x+1)` becomes `2*x + 2`), and use SymPy only for algebra (irreducibility, gcd).
"""

from collections.abc import Iterator
from fractions import Fraction

import sympy

from core.grader import nodes as n
from core.grader import shapes as s
from core.grader.exact import exact_rational
from core.grader.spec import Form
from core.grader.symbolic import SymbolicTimeout, time_limit
from core.grader.translate import SympyContext, TranslateError, to_sympy

_NAMES = {
    "factored": "factored form",
    "expanded": "expanded form",
    "simplified": "simplified form",
    "lowest-terms": "lowest terms",
}


def scalars(value: s.Value) -> Iterator[n.Node]:
    match value:
        case s.Scalar(node):
            yield node
        case s.Equation(lhs, rhs):
            yield lhs
            yield rhs
        case s.Elements(items):
            for item in items:
                if isinstance(item, s.Scalar):
                    yield item.node
        case s.Points(points):
            for p in points:
                yield from p
        case s.VectorValue(items):
            yield from items
        case s.MatrixValue(rows):
            for r in rows:
                yield from r
        case s.Intervals():
            return


def form_problem(
    form: Form, answer: s.Value, key: s.Value, ctx: SympyContext, seconds: float
) -> str | None:
    """None if the answer has the form; otherwise a message for the student."""
    name, places = form
    nodes = list(scalars(answer))
    if name == "exact":
        if any(n.has_decimal(x) for x in nodes):
            return "Right value, but give an exact answer (no decimals)."
        return None
    if name == "decimal":
        for x in nodes:
            if not _decimal_places(x, places):
                return f"Right value, but give it as a decimal with {places} decimal places."
        return None
    keys = list(scalars(key))
    for i, x in enumerate(nodes):
        # The algebraic forms are about exact answers: 0.3333 matched 1/3 only within the
        # decimal tolerance, so it can't be "in lowest terms". Lowest terms means a
        # fraction, so it takes no decimals at all (0.75 is not 3/4 in lowest terms).
        if n.has_decimal(x) and (name == "lowest-terms" or not _exact_decimal(x, keys, i)):
            return f"Right value, but the card asks for {_NAMES[name]} (no decimals)."
    try:
        with time_limit(max(seconds, 0.05)):
            for i, x in enumerate(nodes):
                k = keys[i] if i < len(keys) else None
                if not _has_form(name, x, k, ctx):
                    return f"Right value, but the card asks for {_NAMES[name]}."
    except SymbolicTimeout, RecursionError:
        return None  # can't tell: don't fail a right answer on form
    return None


def _exact_decimal(node: n.Node, keys: list[n.Node], i: int) -> bool:
    """A decimal answer that equals its key exactly (as rationals), or one in x."""
    if n.free_vars(node):
        return True  # decimals in expressions are compared exactly, not within a tolerance
    qa = exact_rational(node)
    qk = exact_rational(keys[i]) if i < len(keys) else None
    return qa is not None and qa == qk


def _decimal_places(node: n.Node, places: int) -> bool:
    node = n.unwrap(node)
    if isinstance(node, n.Neg):
        node = n.unwrap(node.arg)
    if not isinstance(node, n.Num) or "E" in node.text:
        return False
    frac = node.text.partition(".")[2]
    return len(frac) == places


def _has_form(name: str, node: n.Node, key: n.Node | None, ctx: SympyContext) -> bool:
    if name == "expanded":
        return _expanded(node)
    if name == "factored":
        return _factored(node, ctx)
    if name == "lowest-terms":
        return _lowest_terms(node, ctx, key)
    if name == "simplified":
        return _simplified(node, key, ctx)
    return True


# ------------------------------------------------------------------ expanded


def _has_vars(node: n.Node) -> bool:
    return bool(n.free_vars(node))


def _expanded(node: n.Node) -> bool:
    node = n.unwrap(node)
    match node:
        case n.Sum(terms):
            return all(_expanded_term(t) for _, t in terms)
        case _:
            return _expanded_term(node)


def _expanded_term(node: n.Node) -> bool:
    node = n.unwrap(node)
    match node:
        case n.Neg(arg):
            inner = n.unwrap(arg)
            return not (isinstance(inner, n.Sum) and _has_vars(inner)) and _expanded_term(inner)
        case n.Sum():
            return _expanded(node)
        case n.Product(factors):
            numerators = [f for op, f in factors if op != "/"]
            if any(isinstance(n.unwrap(f), n.Sum) and _has_vars(f) for f in numerators):
                return False
            return all(_expanded_term(f) if op != "/" else _expanded(f) for op, f in factors)
        case n.Power(base, exp):
            inner = n.unwrap(base)
            if isinstance(inner, n.Sum) and _has_vars(inner):
                q = exact_rational(exp)
                return not (q is not None and q.denominator == 1 and q > 1)
            # sqrt((x+1)^4) and ((x+1)^4)^(1/2) hide an unexpanded power inside.
            return _expanded_term(inner) and _expanded(exp)
        case n.Call(_, args, base):
            return all(_expanded(a) for a in args) and (base is None or _expanded(base))
    return True


# ------------------------------------------------------------------ factored


def _factors(node: n.Node) -> list[n.Node]:
    node = n.unwrap(node)
    match node:
        case n.Neg(arg):
            return _factors(arg)
        case n.Product(factors):
            return [x for _, f in factors for x in _factors(f)]
        case n.Power(base, exp):
            q = exact_rational(exp)
            if q is not None and q.denominator == 1 and q > 0:
                return _factors(base)
            return [node]
    return [node]


def _factored(node: n.Node, ctx: SympyContext) -> bool:
    """Every polynomial factor is irreducible, and so is every sum inside the answer.

    Sums nested in a root or power count too: `((x^2-4)^3)^(1/3)` equals x^2 - 4 but
    is not factored.
    """
    gens = [ctx.symbols[v] for v in sorted(n.free_vars(node)) if v in ctx.symbols]
    if not gens:
        return True
    sums = [sub for sub in n.walk(node) if isinstance(sub, n.Sum) and _has_vars(sub)]
    for f in [*_factors(node), *sums]:
        if not _has_vars(f):
            continue
        try:
            expr = to_sympy(f, ctx)
        except TranslateError:
            continue
        if not expr.is_polynomial(*gens):
            continue
        poly = sympy.Poly(expr, *gens)
        if poly.total_degree() <= 1:
            continue
        _, parts = sympy.factor_list(expr, *gens)
        if len(parts) != 1 or parts[0][1] != 1:
            return False
    return True


# ------------------------------------------------------------------ lowest terms


def _simple_fraction(node: n.Node) -> bool:
    """p, -p, p/q, -p/q or (-p)/q with whole numbers p and q, as typed."""
    node = n.unwrap(node)
    if isinstance(node, n.Neg):
        node = n.unwrap(node.arg)
    if isinstance(node, n.Num):
        return True
    if isinstance(node, n.Product) and len(node.factors) == 2 and node.factors[1][0] == "/":
        top, bottom = (n.unwrap(f) for _, f in node.factors)
        if isinstance(top, n.Neg):
            top = n.unwrap(top.arg)
        return isinstance(top, n.Num) and isinstance(bottom, n.Num)
    return False


def _lowest_terms(node: n.Node, ctx: SympyContext, key: n.Node | None = None) -> bool:
    rational = exact_rational(node) is not None or (
        key is not None and not n.free_vars(key) and exact_rational(key) is not None
    )
    if not n.free_vars(node) and rational and not _simple_fraction(node):
        return False  # 1 - 1/4, 3/4 + 0, sqrt(9/16) are not "3/4 in lowest terms"
    for sub in n.walk(node):
        if not isinstance(sub, n.Product) or not any(op == "/" for op, _ in sub.factors):
            continue
        num = [f for op, f in sub.factors if op != "/"]
        den = [f for op, f in sub.factors if op == "/"]
        qn = [exact_rational(f) for f in num]
        qd = [exact_rational(f) for f in den]
        if all(q is not None for q in qn + qd):
            top = _prod(qn)
            bottom = _prod(qd)
            if bottom == 0:
                continue
            if bottom.denominator != 1 or top.denominator != 1:
                return False
            if abs(bottom.numerator) == 1 or _gcd(top.numerator, bottom.numerator) != 1:
                return False
            continue
        try:
            top_s = sympy.Mul(*[to_sympy(f, ctx) for f in num])
            bottom_s = sympy.Mul(*[to_sympy(f, ctx) for f in den])
        except TranslateError:
            continue
        try:
            common = sympy.gcd(top_s, bottom_s)
        except Exception:  # noqa: S112 - not polynomial-like: nothing to cancel
            continue
        if common.free_symbols or (common.is_Integer and abs(common) > 1):
            return False
    return True


def _prod(values: list[Fraction | None]) -> Fraction:
    out = Fraction(1)
    for v in values:
        if v is None:
            raise ValueError("not a rational")
        out *= v
    return out


def _gcd(a: int, b: int) -> int:
    import math

    return math.gcd(a, b)


# ------------------------------------------------------------------ simplified
#
# "Simplified" names canonical forms (ADR-0019 item 11, docs/spec.md step 5), each its own
# predicate, never a size measure: like terms combined, no number factors left to multiply,
# no ^0, ^1 or + 0, fractions in lowest terms, simplified radicals (no square factor under a
# square root, no fraction under a radical, no improper power of a number such as 2^(3/2)),
# rationalized denominators (no numeric radical below a fraction bar) and no fraction inside
# a fraction. The last four are waived for a card whose own key breaks them (a key written
# 1/(2sqrt(3)) on purpose accepts that form), so a key always has its own form.

_KEYED = ("radicand", "improper-power", "radical-denominator", "nested-fraction")


def _simplified(node: n.Node, key: n.Node | None, ctx: SympyContext) -> bool:
    try:
        expr = to_sympy(node, ctx)
    except TranslateError:
        return True
    # Like terms or numbers left to combine: SymPy's own bookkeeping already merges them.
    unwrapped = n.unwrap(node)
    if isinstance(unwrapped, n.Sum) and len(sympy.Add.make_args(expr)) < len(unwrapped.terms):
        return False
    for sub in n.walk(node):
        if isinstance(sub, n.Product):
            numbers = [f for op, f in sub.factors if op != "/" and isinstance(n.unwrap(f), n.Num)]
            if len(numbers) > 1:
                return False
        if isinstance(sub, n.Power) and exact_rational(sub.exp) in (Fraction(0), Fraction(1)):
            return False
        if isinstance(sub, n.Sum) and any(exact_rational(t) == 0 for _, t in sub.terms):
            return False
    if not _lowest_terms(node, ctx):
        return False
    broken = _canonical_problems(node, ctx)
    if broken and key is not None:
        broken -= _canonical_problems(key, ctx)
    return not broken


def simplification_problems(node: n.Node, ctx: SympyContext) -> frozenset[str]:
    """The named canonical forms `node` breaks (for messages and tests)."""
    return frozenset(_canonical_problems(node, ctx))


def _canonical_problems(node: n.Node, ctx: SympyContext) -> set[str]:
    out: set[str] = set()
    for radicand, index, power in _radicals(node):
        if power is not None and not n.free_vars(radicand) and not 0 < power < 1:
            out.add("improper-power")  # 2^(3/2) is 2sqrt(2); 2^(-1/2) is sqrt(2)/2
        if not _simple_radicand(radicand, index, ctx):
            out.add("radicand")
    for sub in n.walk(node):
        if isinstance(sub, n.Product) and any(op == "/" for op, _ in sub.factors):
            below = [f for op, f in sub.factors if op == "/"]
            above = [f for op, f in sub.factors if op != "/"]
            if any(_numeric_radical(f) for f in below):
                out.add("radical-denominator")
            if any(_has_fraction(f) for f in below) or any(_has_fraction(f) for f in above):
                out.add("nested-fraction")
        if isinstance(sub, n.Power):
            q = exact_rational(sub.exp)
            if q is not None and q < 0 and _numeric_radical(sub.base):
                out.add("radical-denominator")
    return out


def _radicals(node: n.Node) -> Iterator[tuple[n.Node, int, Fraction | None]]:
    """(radicand, index, exponent or None) for every sqrt, root and fractional power."""
    for sub in n.walk(node):
        if isinstance(sub, n.Call) and sub.func == "sqrt" and len(sub.args) == 1:
            yield sub.args[0], 2, None
        elif isinstance(sub, n.Call) and sub.func == "root" and len(sub.args) == 2:
            k = exact_rational(sub.args[1])
            if k is not None and k.denominator == 1 and k >= 2:
                yield sub.args[0], int(k), None
        elif isinstance(sub, n.Power):
            q = exact_rational(sub.exp)
            if q is not None and q.denominator > 1:
                yield sub.base, q.denominator, q


def _numeric_radical(node: n.Node) -> bool:
    """A radical of a number somewhere in node (sqrt(2), 3^(1/3), root(5, 3))."""
    return any(not n.free_vars(r) for r, _, _ in _radicals(node))


def _has_fraction(node: n.Node) -> bool:
    return any(
        isinstance(sub, n.Product) and any(op == "/" for op, _ in sub.factors)
        for sub in n.walk(node)
    )


def _simple_radicand(radicand: n.Node, index: int, ctx: SympyContext) -> bool:
    """No k-th power factor and no fraction under a k-th root: sqrt(8), sqrt(1/2),
    root(16, 3), sqrt(4) and sqrt(12x) are not simplified; sqrt(x^3) isn't either."""
    try:
        value = to_sympy(radicand, ctx)
    except TranslateError:
        return True
    if isinstance(value, sympy.Rational):
        if value.q != 1 or value.p in (0, 1):
            return False
        return _power_free(abs(int(value.p)), index)
    if not isinstance(value, sympy.Mul | sympy.Pow | sympy.Symbol):
        return True  # a sum under the radical: nothing to take out without factoring
    coeff, factors = value.as_coeff_mul()
    if coeff != 1:
        if not isinstance(coeff, sympy.Rational) or coeff.q != 1:
            return False
        if not _power_free(abs(int(coeff.p)), index):
            return False
    for f in factors:
        _, exp = f.as_base_exp()
        if exp.is_Integer and int(exp) >= index:
            return False
    return True


def _power_free(value: int, index: int) -> bool:
    if value > 10**12:
        return True  # too large to factor here; never fail a right answer on form
    return all(e < index for p, e in sympy.factorint(value).items() if p > 1)
