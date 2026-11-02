"""The checking pipeline (docs/spec.md, "Math system"): exact -> numeric -> symbolic -> form.

Runs inside the worker process (worker.py) but is plain code, so tests can also call it
directly. Numeric sampling decides most cases; symbolic work can confirm a match (or
prove an exact nonzero difference) but never overrules a numeric mismatch.
"""

import random
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Literal

import mpmath
from mpmath import mp

from core.grader import critical, forms, intervals
from core.grader import nodes as n
from core.grader import shapes as s
from core.grader.exact import exact_rational
from core.grader.numeric import Evaluator, Number, Overflow, Undefined
from core.grader.serialize import to_answer_syntax, to_text
from core.grader.spec import Card, Tolerance
from core.grader.symbolic import Deadline, SymbolicTimeout, time_limit, zero_status
from core.grader.translate import SympyContext, TranslateError, make_symbols, to_sympy

# "hole": the answer matches the key except at removable points (ADR-0019 item 10). It is
# not wrong: grade() reports it as invalid input (no attempt) in its own category.
type Status = Literal["correct", "incorrect", "undecidable", "hole"]
type Fixed = tuple[tuple[str, Number], ...]  # variables held at sample values

DPS = 30  # MATH: numeric sampling at 30 digits
RECHECK_DPS = 60
CONST_DPS = 50
# A mismatch is rechecked at growing precision. Agreement to 1e-40 (relative) at any level
# settles it; otherwise the difference must stay put between two levels to count, since
# rounding noise shrinks as digits are added and a real difference does not. There is no
# absolute floor: 2e^(-200) is not e^(-200), and e^(-1000) is not 0.
AGREE_LEVELS = (RECHECK_DPS, 120, 240)
AGREE_RELATIVE = mpmath.mpf("1e-40")
POINTS_PER_VAR = 12
MIN_POINTS = 4
CANDIDATES_PER_VAR = 40
MAX_CANDIDATES = 400
NEAR_MISS_RECHECKS = 3
SYMBOLIC_SOFT_SECONDS = 0.6
CRITICAL_SOLVE_SECONDS = 0.25  # per solveset call (critical.py)
CRITICAL_RESERVE = 0.7  # seconds kept back for the rest of the job
MAX_EXTRA_POINTS = 200
SEED = 20261101

_RESTRICTING_FUNCS = {"sqrt", "ln", "log", "arcsin", "arccos", "arcsec", "arccsc"}


@dataclass(frozen=True, slots=True)
class Verdict:
    status: Status
    message: str = ""
    step: str = ""  # exact, numeric, symbolic, form, token
    confirmed: bool = False  # a symbolic step agreed with the numeric match


CORRECT = Verdict("correct", step="numeric")


def _incorrect(message: str = "", step: str = "numeric") -> Verdict:
    return Verdict("incorrect", message, step)


def _undecidable(message: str) -> Verdict:
    return Verdict("undecidable", message, "numeric")


HOLE_MESSAGE = (
    "Your answer is undefined at {where} where the expected answer isn't; check its form."
)
REMOVABLE_STEP = mpmath.mpf("1e-20")  # how far from a hole the answer is evaluated
REMOVABLE_CLOSE = mpmath.mpf("1e-8")  # how close it must come to the key there (relative)


def _hole_verdict(where: str) -> Verdict:
    return Verdict("hole", HOLE_MESSAGE.format(where=where), "numeric")


def matches(verdict: Verdict) -> bool:
    """Equal to the key, possibly except at removable points."""
    return verdict.status in {"correct", "hole"}


@dataclass(slots=True)
class Checker:
    """Compares answer Values against one card's keys."""

    card: Card
    deadline: Deadline = field(default_factory=lambda: Deadline(1.8))
    symbolic: bool = True
    ev: Evaluator = field(init=False)
    ctx: SympyContext = field(init=False)
    # Keyed by id(key); the key node is stored too, so a reused id can't hit.
    _points: dict[tuple[int, tuple[str, ...]], tuple[n.Node, list[dict[str, Number]] | None]] = (
        field(init=False, default_factory=dict)
    )
    _pieces: dict[str, list[intervals.Iv]] = field(init=False, default_factory=dict)
    _zeros_cache: dict[tuple[n.Node, int, str, Fixed], tuple[list[object], list[Number]]] = field(
        init=False, default_factory=dict
    )
    _incomplete: bool = field(init=False, default=False)  # critical analysis cut short

    def __post_init__(self) -> None:
        card = self.card
        complex_mode = card.imaginary or any(a == "complex" for _, a in card.variables)
        self.ev = Evaluator(degrees=card.degrees, complex_mode=complex_mode)
        symbols = make_symbols(card.variables, card.constants)
        self.ctx = SympyContext(symbols, degrees=card.degrees, complex_mode=complex_mode)

    # ================================================================== dispatch
    def compare(self, answer: s.Value, key: s.Value, *, top: bool = True) -> Verdict:
        kind = self.card.answer_type
        match answer, key:
            case (s.Infinity(a), s.Infinity(b)):
                return Verdict("correct" if a == b else "incorrect", step="token")
            case (s.DneValue(), s.DneValue()):
                return Verdict("correct", step="token")
            case (s.Scalar(a), s.Scalar(b)) if kind == "antiderivative":
                return self.antiderivative(a, b)
            case (s.Scalar(a), s.Scalar(b)):
                return self.scalar(a, b, symbolic=top)
            case (s.Equation(), s.Equation()):
                return self.equation(answer, key)
            case (s.Elements(), s.Elements()):
                return self.elements(answer.items, key.items, answer.ordered)
            case (s.Points(a), s.Points(b)):
                return self.points(a, b)
            case (s.VectorValue(a), s.VectorValue(b)):
                return self.sequence(a, b)
            case (s.MatrixValue(a), s.MatrixValue(b)):
                if len(a) != len(b) or len(a[0]) != len(b[0]):
                    return _incorrect("The matrix has the wrong size.", "shape")
                return self.sequence(tuple(x for r in a for x in r), tuple(x for r in b for x in r))
            case (s.Intervals(a), s.Intervals(b)):
                return self.interval_sets(a, b)
        if isinstance(key, s.DneValue | s.Infinity) or isinstance(answer, s.DneValue | s.Infinity):
            return Verdict("incorrect", step="token")
        return _incorrect("", "shape")

    # ================================================================== key checks
    def key_problem(self, key: s.Value) -> str | None:
        """Why a key can't be used (no real value, undefined on the domain), or None."""
        nodes: list[n.Node] = []
        match key:
            case s.Scalar(node):
                nodes = [node]
            case s.Equation(lhs, rhs):
                nodes = [_difference(lhs, rhs)]
            case s.Elements(items):
                nodes = [i.node for i in items if isinstance(i, s.Scalar)]
            case s.Points(points):
                nodes = [x for p in points for x in p]
            case s.VectorValue(items):
                nodes = list(items)
            case s.MatrixValue(rows):
                nodes = [x for r in rows for x in r]
            case s.Intervals(expr):
                try:
                    intervals.canonical(expr, self.ev)
                except intervals.BadEndpoint:
                    return "an endpoint of the key has no real value"
        for node in nodes:
            names = self._names(node)
            if self.card.answer_type == "antiderivative":
                names = tuple(sorted(set(names) | {_integration_var(self.card)}))
            if not names:
                try:
                    self._eval(node, {}, CONST_DPS)
                except Undefined, Overflow:
                    return f"the key {to_text(node)} has no real value"
            elif not self.points_for(node, names):
                return f"the key {to_text(node)} isn't defined at enough points in its domain"
        return None

    # ================================================================== scalars
    def scalar(self, a: n.Node, k: n.Node, *, symbolic: bool = True) -> Verdict:
        tolerance = self._tolerance_for(a, k)
        exact = self._exact_step(a, k)
        if exact is not None:
            return exact
        names = self._names(a, k)
        if not names:
            verdict = self._constant(a, k, tolerance)
        else:
            self._incomplete = False
            verdict = self._sampled(a, k, names, tolerance)
            if verdict.status == "correct":
                verdict = self._hole(a, k, names) or verdict
            verdict = self._unless_incomplete(verdict)
        if symbolic and self.symbolic and verdict.status != "incorrect" and tolerance is None:
            verdict = self._confirm(a, k, verdict)
        return verdict

    def _removable(
        self,
        answer: Callable[[Mapping[str, Number], int], Number],
        key: Callable[[Mapping[str, Number], int], Number],
        env: Mapping[str, Number],
        *,
        offset: bool = False,
    ) -> bool:
        """Is env, where the answer is undefined and the key defined, a removable point?

        Just beside it, along some variable, the answer is defined on both sides and comes
        back to the key's value (`offset`: for antiderivatives, differs from the key by the
        same constant on both sides, so `-arctan(1/x)` with its jump at 0 is not removable).
        A region where the answer is undefined (2ln(x) for x < 0) is not a point.
        """
        if self.card.domain_strict:
            return False
        try:
            k0 = key(env, CONST_DPS)
        except Undefined, Overflow:
            return False
        for name in env:
            v = env[name]
            sides: list[Number] = []
            try:
                for sign in (1, -1):
                    with mp.workdps(CONST_DPS):  # 1 + 1e-20 must not round back to 1
                        shifted = {**env, name: v + sign * REMOVABLE_STEP * (1 + abs(v))}
                    av = answer(shifted, CONST_DPS)
                    sides.append(av - key(shifted, CONST_DPS) if offset else av)
            except Undefined, Overflow:
                continue
            if offset:
                close = abs(sides[0] - sides[1]) <= REMOVABLE_CLOSE * (1 + abs(sides[0]))
            else:
                close = all(abs(x - k0) <= REMOVABLE_CLOSE * (1 + abs(k0)) for x in sides)
            if close:
                return True
        return False

    def _tolerance_for(self, a: n.Node, k: n.Node) -> Tolerance | None:
        """Decimals are compared within the tolerance; exact forms exactly.

        The default (1% relative, with a floor) applies to numbers (constants) only; an
        expression in x with a decimal (`0.5x`) is compared exactly unless the card sets
        `tolerance` or asks for a rounding.
        """
        form = self.card.form
        if form is not None and form[0] == "decimal":
            return Tolerance("absolute", Fraction(1, 2 * 10 ** form[1]), explicit=True)
        if not (n.has_decimal(a) or n.has_decimal(k)):
            return None
        if self._names(a, k) and not self.card.tolerance.explicit:
            return None
        return self.card.tolerance

    def _names(self, *nodes: n.Node) -> tuple[str, ...]:
        names: set[str] = set()
        for node in nodes:
            names |= n.free_vars(node)
        return tuple(sorted(names))

    def _restricted(self, node: n.Node) -> bool:
        """Does the tree restrict its own domain in a way SymPy's auto-simplification hides?

        Divisors count: SymPy turns `x^2/x` into `x` and `x^(-1)*x^2` into `x`, losing
        the hole at 0 (an answer undefined where the key is defined is wrong).
        """
        for sub in n.walk(node):
            if isinstance(sub, n.Call) and sub.func in _RESTRICTING_FUNCS:
                return True
            if isinstance(sub, n.Call) and sub.func == "root":
                return True
            if isinstance(sub, n.Power) and not _integer_literal(sub.exp):
                return True
            if isinstance(sub, n.Power) and n.free_vars(sub.base):
                q = exact_rational(sub.exp)
                if q is None or q < 0:
                    return True
            if isinstance(sub, n.Product) and any(
                op == "/" and n.free_vars(f) for op, f in sub.factors
            ):
                return True
        return False

    def _exact_step(self, a: n.Node, k: n.Node) -> Verdict | None:
        """Step 2: identical canonical forms are correct at once."""
        if self._restricted(a):
            return None
        try:
            sa, sk = to_sympy(a, self.ctx), to_sympy(k, self.ctx)
        except TranslateError:
            return None
        if sa == sk:
            return Verdict("correct", step="exact", confirmed=True)
        return None

    def _close(self, a: Number, k: Number) -> bool:
        """Relatively equal at 30 digits (no absolute floor: tiny values still count)."""
        return bool(abs(a - k) <= mpmath.mpf("1e-12") * max(abs(a), abs(k)))

    def _agree(
        self,
        env: Mapping[str, Number],
        answer: Callable[[Mapping[str, Number], int], Number],
        key: Callable[[Mapping[str, Number], int], Number],
    ) -> bool | None:
        """Do answer and key agree at env, beyond rounding? None: undefined at some precision.

        Agreement to 1e-40 relative at any of AGREE_LEVELS settles it. A larger difference
        is real only if it stays put from one level to the next: rounding noise shrinks by
        many orders of magnitude as digits are added (sin(pi) at 60 digits vs 120), while a
        true difference (e^(-1000) - 0, or 2e^(-200) - e^(-200)) does not move.
        """
        previous: Number | None = None
        for dps in AGREE_LEVELS:
            try:
                kv, av = key(env, dps), answer(env, dps)
            except Undefined, Overflow:
                return None
            d = abs(av - kv)
            if d <= AGREE_RELATIVE * max(abs(av), abs(kv)):
                return True
            if previous is not None and abs(d - previous) <= mpmath.mpf("1e-6") * d:
                return False
            previous = d
        return True  # the difference kept collapsing as digits were added: rounding noise

    def _within(self, a: Number, k: Number, tol: Tolerance) -> bool:
        d = abs(a - k)
        value = mpmath.mpf(tol.value.numerator) / tol.value.denominator
        slack = mpmath.mpf("1e-25") * max(abs(a), abs(k))  # relative: 0.0 is not 10^(-30)
        if tol.kind == "absolute":
            return bool(d <= value + slack)
        if tol.kind == "sig-figs":
            return bool(d <= _half_unit(k, int(tol.value)) + slack)
        floor = mpmath.mpf(tol.floor.numerator) / tol.floor.denominator
        return bool(d <= max(value * abs(k), floor) + slack)

    def _eval(self, node: n.Node, env: Mapping[str, Number], dps: int) -> Number:
        with mp.workdps(dps):
            return self.ev(node, env)

    def _constant(self, a: n.Node, k: n.Node, tol: Tolerance | None) -> Verdict:
        try:
            kv = self._eval(k, {}, CONST_DPS)
        except Undefined, Overflow:
            return _undecidable("The key has no value.")
        try:
            av = self._eval(a, {}, CONST_DPS)
        except Undefined:
            return _incorrect("Your answer has no real value.")
        except Overflow:
            return _undecidable("The answer is too large to compare.")
        qa, qk = exact_rational(a), exact_rational(k)
        if tol is not None and qa is not None and qk is not None:
            return CORRECT if _within_exactly(qa, qk, tol) else _incorrect()
        if tol is not None:
            return CORRECT if self._within(av, kv, tol) else _incorrect()
        if qa is not None and qk is not None:
            return Verdict("correct", step="exact", confirmed=True) if qa == qk else _incorrect()
        same = self._agree(
            {}, lambda env, dps: self._eval(a, env, dps), lambda env, dps: self._eval(k, env, dps)
        )
        if same is None:
            return _undecidable("The value is too close to an edge of its domain to compare.")
        return CORRECT if same else _incorrect()

    # ------------------------------------------------------------------ sampling
    def _var_pieces(self, name: str) -> list[intervals.Iv]:
        if name in self._pieces:
            return self._pieces[name]
        assumption = dict(self.card.variables).get(name, "real")
        zero = mpmath.mpf(0)
        base = {
            "positive": [intervals.Iv(zero, None, False, False)],
            "nonnegative": [intervals.Iv(zero, None, True, False)],
            "negative": [intervals.Iv(None, zero, False, False)],
            "nonpositive": [intervals.Iv(None, zero, False, True)],
        }.get(assumption, [intervals.Iv(None, None, False, False)])
        for cond in self.card.domain:
            got = intervals.condition_set(cond, name, self.ev)
            if got is not None:
                base = intervals.intersect(base, got)
        self._pieces[name] = base
        return base

    def _pool(self, name: str, rng: random.Random, count: int) -> list[Number]:
        assumption = dict(self.card.variables).get(name, "real")
        if assumption == "complex":
            return [mpmath.mpc(rng.uniform(-3, 3), rng.uniform(-3, 3)) for _ in range(count)]
        pieces = self._var_pieces(name)
        if not pieces:
            return []
        values: list[float] = []
        per_piece = max(2, count // len(pieces))
        for iv in pieces:
            lo = float(iv.lo) if iv.lo is not None else None
            hi = float(iv.hi) if iv.hi is not None else None
            for j in range(per_piece):
                values.append(_draw(lo, hi, rng, wide=j % 6 == 5))
        if assumption == "integer":
            ints = sorted({round(v) for v in values} | set(range(-15, 16)))
            ints = [v for v in ints if any(_contains(iv, v) for iv in pieces)]
            rng.shuffle(ints)
            return [mpmath.mpf(v) for v in ints[: max(count, POINTS_PER_VAR)]]
        return [mpmath.mpf(v) for v in values]

    def _domain_ok(self, env: Mapping[str, Number]) -> bool:
        for cond in self.card.domain:
            if len(n.free_vars(cond)) <= 1:
                continue  # one-variable conditions already shaped the pools
            if not self._holds(cond, env):
                return False
        return True

    def _holds(self, cond: n.Node, env: Mapping[str, Number]) -> bool:
        try:
            match cond:
                case n.Or(items):
                    return any(self._holds(c, env) for c in items)
                case n.And(items):
                    return all(self._holds(c, env) for c in items)
                case n.Chain(operands, ops):
                    vals = [self._eval(o, env, DPS) for o in operands]
                    return all(_rel(op, vals[i], vals[i + 1]) for i, op in enumerate(ops))
        except Undefined, Overflow, TypeError:
            return False
        return False

    def points_for(self, key: n.Node, names: tuple[str, ...]) -> list[dict[str, Number]] | None:
        """Up to 12 points per variable where the key is defined (one per connected piece)."""
        cache_key = (id(key), names)
        hit = self._points.get(cache_key)
        if hit is not None and hit[0] is key:
            return hit[1]
        # Deterministic sampling (not security related): same points every run.
        rng = random.Random(SEED + len(names))  # noqa: S311
        count = min(CANDIDATES_PER_VAR * len(names), MAX_CANDIDATES)
        pools = {name: self._pool(name, rng, CANDIDATES_PER_VAR) for name in names}
        if any(not pool for pool in pools.values()):
            self._points[cache_key] = (key, None)
            return None
        if len(names) == 1:
            (name,) = names
            raw = sorted(
                pools[name], key=lambda v: (v.real, v.imag) if isinstance(v, mpmath.mpc) else (v, 0)
            )
            envs = [{name: v} for v in raw]
        else:
            envs = [{nm: rng.choice(pools[nm]) for nm in names} for _ in range(count)]
        defined: list[bool] = []
        for env in envs:
            ok = self._domain_ok(env)
            if ok:
                try:
                    self._eval(key, env, DPS)
                except Undefined, Overflow:
                    ok = False
            defined.append(ok)
        chosen = _spread(envs, defined, POINTS_PER_VAR * len(names), ordered=len(names) == 1)
        result = chosen if len(chosen) >= min(MIN_POINTS, len(envs)) else None
        self._points[cache_key] = (key, result)
        return result

    def _sampled(
        self, a: n.Node, k: n.Node, names: tuple[str, ...], tol: Tolerance | None
    ) -> Verdict:
        points = self.points_for(k, names)
        if not points:
            return _undecidable("The key isn't defined at enough points in the domain.")
        return self._compare_values(
            points,
            lambda env, dps: self._eval(a, env, dps),
            lambda env, dps: self._eval(k, env, dps),
            tol,
            extra=self._extra_points((a, k), names, points),
        )

    def _compare_values(
        self,
        points: Sequence[Mapping[str, Number]],
        answer: Callable[[Mapping[str, Number], int], Number],
        key: Callable[[Mapping[str, Number], int], Number],
        tol: Tolerance | None,
        *,
        extra: Sequence[Mapping[str, Number]] = (),
        offset: bool = False,
    ) -> Verdict:
        """Compare at the sample points, then at the critical-region points (`extra`).

        Only the sample points count toward the minimum: extra points may well fall where
        the key is undefined. A point where only the answer is undefined is a hole if it is
        removable (`_removable`); the answer is then compared everywhere else.
        """
        compared = 0
        rechecks = 0
        hole: str | None = None
        for i, env in enumerate([*points, *extra]):
            if self.deadline.left() < 0.2:
                return _undecidable("Out of time.")
            try:
                kv = key(env, DPS)
            except Undefined, Overflow:
                continue
            try:
                av = answer(env, DPS)
            except Undefined:
                where = _where(env)
                if self._removable(answer, key, env, offset=offset):
                    hole = hole or where
                    continue
                return _incorrect(
                    f"Your answer is undefined at {where}, where the correct answer is defined."
                )
            except Overflow:
                continue
            compared += i < len(points)
            if tol is not None:
                if not self._within(av, kv, tol):
                    return _incorrect()
                continue
            close = self._close(av, kv)
            if close and rechecks >= NEAR_MISS_RECHECKS:
                continue
            # Recheck at higher precision: rule out cancellation on a mismatch, catch near
            # misses (a difference smaller than 1e-12 but real).
            rechecks += close
            same = self._agree(env, answer, key)
            if same is None and close:
                continue
            if not same:
                return _incorrect()
        if compared < MIN_POINTS and compared < len(points):
            return _undecidable("Too few points to compare.")
        if compared == 0:
            return _undecidable("No points to compare.")
        return _hole_verdict(hole) if hole is not None else CORRECT

    # ------------------------------------------------------------------ critical points
    def _unless_incomplete(self, verdict: Verdict) -> Verdict:
        """A match found before every piece of the line was checked is not a verdict."""
        if matches(verdict) and self._incomplete:
            return _undecidable("Ran out of time checking every piece of the answer.")
        return verdict

    def _subs(self, fixed: Fixed) -> dict[object, object]:
        return {self.ctx.symbols[v]: _rational(x) for v, x in fixed}

    def _zeros(
        self, node: n.Node, level: int, name: str, fixed: Fixed = ()
    ) -> tuple[list[object], list[Number]]:
        """Where node = level as a function of `name` (other variables held at `fixed`):
        (exact SymPy zeros, approximate zeros).

        Exact zeros come from solveset; if it gives up, a numeric scan finds approximate
        ones (good enough to place sample points, not to test a hole).
        """
        cache_key = (node, level, name, fixed)
        hit = self._zeros_cache.get(cache_key)
        if hit is not None:
            return hit
        exact: list[object] = []
        approx: list[Number] = []
        got = None
        budget = min(CRITICAL_SOLVE_SECONDS, self.deadline.left() - CRITICAL_RESERVE)
        try:
            expr = (to_sympy(node, self.ctx) - level).subs(self._subs(fixed))
            got = critical.solve_zeros(expr, self.ctx.symbols[name], budget)
        except TranslateError, KeyError, TypeError:
            pass
        if got is not None:
            exact = list(got)
        elif self.deadline.left() > CRITICAL_RESERVE + 0.3:
            held = dict(fixed)

            def f(v: mpmath.mpf) -> mpmath.mpf | None:
                try:
                    value = self._eval(node, {**held, name: v}, DPS)
                except Undefined, Overflow:
                    return None
                return None if isinstance(value, mpmath.mpc) else value - level

            approx = list(critical.scan_zeros(f))
        else:
            self._incomplete = True
            return exact, approx  # out of time: not cached, so a later call can retry
        self._zeros_cache[cache_key] = (exact, approx)
        return exact, approx

    def _held(
        self, part: critical.Part, name: str, env: Mapping[str, Number] | None
    ) -> Fixed | None:
        """The other variables of a part, held at their values in env (None: can't)."""
        others = n.free_vars(part.node) - {name}
        if name not in n.free_vars(part.node):
            return None
        if not others:
            return ()
        if env is None or not others <= env.keys():
            return None
        return tuple(sorted((o, env[o]) for o in others))

    def _critical_values(
        self, nodes: Iterable[n.Node], name: str, env: Mapping[str, Number] | None = None
    ) -> tuple[list[Number], list[Number]]:
        """(every critical value of `name`, the ones binary floating point holds exactly).

        Arguments in several variables are cut along `name` with the others held at env.
        """
        values: list[Number] = []
        exact_points: list[Number] = []
        for node in nodes:
            for part in critical.parts(node):
                fixed = self._held(part, name, env)
                if fixed is None:
                    continue
                for level in part.levels:
                    if self.deadline.left() < CRITICAL_RESERVE:
                        self._incomplete = True
                        return values, exact_points
                    zeros, approx = self._zeros(part.node, level, name, fixed)
                    for z in zeros:
                        v = critical.real_value(z, DPS)
                        if v is None:
                            continue
                        values.append(v)
                        q = critical.dyadic(z)
                        if q is not None:
                            exact_points.append(mpmath.mpf(q.numerator) / q.denominator)
                    values += approx
        return values, exact_points

    def _fit(self, name: str, values: Iterable[Number]) -> list[Number]:
        """Keep the values inside the variable's domain (rounded for integer variables)."""
        assumption = dict(self.card.variables).get(name, "real")
        pieces = self._var_pieces(name)
        out: list[Number] = []
        for v in values:
            if assumption == "integer":
                cands = [mp.floor(v) - 1, mp.floor(v), mp.ceil(v), mp.ceil(v) + 1]
            else:
                cands = [v]
            out += [c for c in cands if any(_contains(iv, c) for iv in pieces) and c not in out]
        return out

    def _admissible(self, name: str, v: Number) -> bool:
        if dict(self.card.variables).get(name, "real") == "integer" and v != mp.nint(v):
            return False
        return any(_contains(iv, v) for iv in self._var_pieces(name))

    def _extra_points(
        self,
        nodes: Sequence[n.Node],
        names: tuple[str, ...],
        base: Sequence[Mapping[str, Number]],
    ) -> list[dict[str, Number]]:
        """Points in every region cut out by the critical values of each variable.

        With several variables, each is cut in turn with the others held at a few of the
        sample points, so `abs(x - y) - 100` gets points with |x - y| > 100.
        """
        if self.ev.complex_mode:
            return []
        out: list[dict[str, Number]] = []
        bases: list[Mapping[str, Number] | None] = [None] if len(names) == 1 else list(base[:3])
        for b in bases:
            for name in names:
                if dict(self.card.variables).get(name, "real") == "complex":
                    continue
                values, exact_points = self._critical_values(nodes, name, b)
                if not values:
                    continue
                chosen = self._fit(name, [*exact_points, *critical.region_values(values)])
                envs = [{name: v} if b is None else {**b, name: v} for v in chosen]
                out += [e for e in envs if self._domain_ok(e)]
        return out[: MAX_EXTRA_POINTS * len(bases)]

    def _hole(self, a: n.Node, k: n.Node, names: tuple[str, ...]) -> Verdict | None:
        """The answer divides by zero somewhere the key is defined (a removable hole).

        `(x^2-1)/(x-1)` is not `x + 1`: it is undefined at 1 (docs/spec.md, numeric step:
        an answer undefined where the key is defined is wrong). Zeros of each divisor are
        found exactly along one variable (others held at a few sample points); divisors
        whose zeros solveset can't list (periodic ones such as cos x) are left to sampling.
        """
        if self.ev.complex_mode:
            return None
        base = self.points_for(k, names) or []
        bases: list[Mapping[str, Number] | None] = [None] if len(names) == 1 else list(base[:3])
        for part in critical.parts(a):
            if not part.singular:
                continue
            for b in bases:
                for name in sorted(n.free_vars(part.node)):
                    fixed = self._held(part, name, b)
                    if fixed is None or name not in names:
                        continue
                    if self.deadline.left() < CRITICAL_RESERVE:
                        self._incomplete = True
                        return None
                    zeros, _ = self._zeros(part.node, 0, name, fixed)
                    for z in zeros:
                        found = self._hole_at(a, k, part.node, name, z, b, fixed)
                        if found is not None:
                            return found
        return None

    def _hole_at(
        self,
        a: n.Node,
        k: n.Node,
        divisor: n.Node,
        name: str,
        z: object,
        b: Mapping[str, Number] | None,
        fixed: Fixed,
    ) -> Verdict | None:
        subs = {**self._subs(fixed), self.ctx.symbols[name]: z}
        if not self._exactly_zero(divisor, subs):
            return None
        v = critical.real_value(z, CONST_DPS)
        if v is None or not self._admissible(name, v):
            return None
        env = {name: v} if b is None else {**b, name: v}
        if not (self._domain_ok(env) and self._defined_at(k, env, name, subs)):
            return None
        try:
            where = to_answer_syntax(z)
        except Exception:  # only for the message: any failure falls back to digits
            where = mpmath.nstr(v, 8)
        antiderivative = self.card.answer_type == "antiderivative"

        def at(node: n.Node) -> Callable[[Mapping[str, Number], int], Number]:
            return lambda e, dps: self._eval(node, e, dps)

        if self._removable(at(a), at(k), env, offset=antiderivative):
            return _hole_verdict(f"{name} = {where}")
        return _incorrect(
            f"Your answer is undefined at {name} = {where}, where the correct answer is defined."
        )

    def _exactly_zero(self, node: n.Node, subs: Mapping[object, object]) -> bool:
        """Is node exactly 0 after subs? (False when unknown.)"""
        try:
            value = to_sympy(node, self.ctx).subs(subs)
        except TranslateError, KeyError, TypeError:
            return False
        budget = min(0.2, self.deadline.left() - CRITICAL_RESERVE)
        return budget > 0.02 and zero_status(value, budget) is True

    def _defined_at(
        self, k: n.Node, env: Mapping[str, Number], name: str, subs: Mapping[object, object]
    ) -> bool:
        """Is the key defined (and continuous in `name`) at env? `subs` holds exact values."""
        known = {str(sym) for sym in subs}
        for part in critical.parts(k):
            if part.singular and n.free_vars(part.node) <= known:
                try:
                    value = to_sympy(part.node, self.ctx).subs(subs)
                except TranslateError, KeyError, TypeError:
                    return False
                budget = min(0.2, self.deadline.left() - CRITICAL_RESERVE)
                if budget <= 0.02 or zero_status(value, budget) is not False:
                    return False  # the key may divide by zero here too
        v = env[name]
        values: list[Number] = []
        for offset in (0, 1, -1):
            shifted = {**env, name: v + offset * mpmath.mpf("1e-20") * (1 + abs(v))}
            try:
                values.append(self._eval(k, shifted, CONST_DPS))
            except Undefined, Overflow:
                return False
        ref = values[0]
        return all(abs(x - ref) <= mpmath.mpf("1e-8") * (1 + abs(ref)) for x in values)

    # ------------------------------------------------------------------ symbolic
    def _confirm(self, a: n.Node, k: n.Node, verdict: Verdict) -> Verdict:
        budget = min(SYMBOLIC_SOFT_SECONDS, self.deadline.left() - 0.3)
        if verdict.status == "correct" and verdict.step == "exact":
            return verdict
        if budget <= 0.05:
            return verdict
        try:
            diff = to_sympy(a, self.ctx) - to_sympy(k, self.ctx)
        except TranslateError:
            return verdict
        status = zero_status(diff, budget)
        if status is True and verdict.status == "hole":
            return replace(verdict, confirmed=True)  # equal as SymPy simplifies: holes vanish
        if status is True:
            step = "symbolic" if verdict.status != "correct" else verdict.step
            return Verdict("correct", step=step, confirmed=True)
        if status is False and matches(verdict):
            return _incorrect("", "symbolic")
        if status is None and matches(verdict):
            names = self._names(a, k)
            envs = (self.points_for(k, names) or [])[:3] if names else [{}]

            def scale(env: Mapping[str, Number]) -> Number:
                with mp.workdps(RECHECK_DPS):
                    return max(abs(self.ev(a, env)), abs(self.ev(k, env)))

            if self._tiny_difference(diff, envs, scale):
                return _incorrect("", "symbolic")
        return verdict

    def _tiny_difference(
        self,
        diff: object,
        envs: Sequence[Mapping[str, Number]],
        scale: Callable[[Mapping[str, Number]], Number],
    ) -> bool:
        """Is SymPy's exact difference a stable, tiny, nonzero number at a sample point?

        SymPy cancels identical terms when it builds a - k, so `x + exp(-1000x^2)` minus
        `x` is exactly `exp(-1000x^2)`: far below what sampling at 60 digits resolves, but
        strict evalf certifies it nonzero (a true zero that SymPy didn't simplify raises
        PrecisionExhausted instead). A value much larger than the sampled difference means
        SymPy reads the expression differently from our evaluator (a branch), so it is
        ignored: this step can only turn a match into a miss on a tiny difference.
        """
        import sympy
        from sympy.core.evalf import PrecisionExhausted

        budget = min(0.4, self.deadline.left() - 0.3)
        if budget <= 0.05 or not isinstance(diff, sympy.Expr):
            return False
        try:
            with time_limit(budget):
                for env in envs:
                    subs = {self.ctx.symbols[v]: _rational(x) for v, x in env.items()}
                    try:
                        d30 = diff.evalf(30, subs=subs, strict=True)
                        d60 = diff.evalf(60, subs=subs, strict=True)
                    except PrecisionExhausted:
                        continue
                    if not (d30.is_Float and d60.is_Float) or d60 == 0:
                        continue
                    v30 = mpmath.mpf(sympy.Float(d30, 30)._mpf_)
                    v60 = mpmath.mpf(sympy.Float(d60, 60)._mpf_)
                    if abs(v60 - v30) > mpmath.mpf("1e-20") * abs(v60):
                        continue
                    try:
                        size = scale(env)
                    except Undefined, Overflow:
                        continue
                    if abs(v60) <= mpmath.mpf("1e-30") * max(size, 1):
                        return True
        except SymbolicTimeout, RecursionError, KeyError:
            return False
        except Exception:  # SymPy can raise many internal errors; no proof is the safe answer
            return False
        return False

    # ================================================================== antiderivative
    def antiderivative(self, a: n.Node, k: n.Node) -> Verdict:
        card = self.card
        if card.require_constant and not self._has_constant(a):
            return _incorrect("Add the constant of integration (+ C).", "form")
        if self._exact_step(a, k) is not None:
            return Verdict("correct", step="exact", confirmed=True)
        var = _integration_var(card)
        names = tuple(sorted(set(self._names(a, k)) | {var}))
        points = self.points_for(k, names)
        if not points:
            return _undecidable("The key isn't defined at enough points in the domain.")
        self._incomplete = False
        extra = self._extra_points((a, k), names, points)
        # The answer must exist wherever the key does (except at removable points, where
        # it differs from the key by the same constant on both sides), then the
        # derivatives must agree.
        hole: str | None = None
        for env in [*points, *extra]:
            try:
                self._eval(k, env, DPS)
            except Undefined, Overflow:
                continue
            try:
                self._eval(a, env, DPS)
            except Undefined:
                if self._removable(
                    lambda e, dps: self._eval(a, e, dps),
                    lambda e, dps: self._eval(k, e, dps),
                    env,
                    offset=True,
                ):
                    hole = hole or _where({v: x for v, x in env.items() if v == var})
                    continue
                return _incorrect("Your answer is undefined where the correct answer is defined.")
            except Overflow:
                continue

        def derivative(node: n.Node) -> Callable[[Mapping[str, Number], int], Number]:
            def f(env: Mapping[str, Number], dps: int) -> Number:
                with mp.workdps(dps):
                    try:
                        return mp.diff(lambda t: self.ev(node, {**env, var: t}), env[var])
                    except ZeroDivisionError:
                        raise Undefined from None

            return f

        verdict = self._compare_values(points, derivative(a), derivative(k), None, extra=extra)
        if verdict.status == "correct" and hole is not None:
            verdict = _hole_verdict(hole)
        if verdict.status == "correct":
            verdict = self._unless_incomplete(self._hole(a, k, names) or verdict)
        verdict = self._unless_incomplete(verdict)
        if verdict.status == "undecidable" or not (self.symbolic and matches(verdict)):
            return verdict
        try:
            sym = self.ctx.symbols[var]
            diff = (to_sympy(a, self.ctx) - to_sympy(k, self.ctx)).diff(sym)
        except TranslateError, KeyError:
            return verdict
        budget = min(SYMBOLIC_SOFT_SECONDS, self.deadline.left() - 0.3)
        status = zero_status(diff, budget) if budget > 0.05 else None
        if status is True:
            return replace(verdict, confirmed=True)
        if status is False:
            return _incorrect("", "symbolic")
        dk = derivative(k)

        def scale(env: Mapping[str, Number]) -> Number:
            return abs(dk(env, RECHECK_DPS))

        if self._tiny_difference(diff, points[:3], scale):
            return _incorrect("", "symbolic")
        return verdict

    def _has_constant(self, a: n.Node) -> bool:
        """`+ C` is really there: the answer changes with C, by an amount free of x.

        `(x^2 + C)/2` has one; `x^2/2 + C - C`, `x^2/2 + 0*C` and `x^2/2 + C/C` don't
        (SymPy's own bookkeeping cancels those), and `x^2/2 + C*x` isn't a constant.
        """
        present = [c for c in self.card.constants if c in n.free_vars(a)]
        if not present:
            return False
        var = self.ctx.symbols.get(_integration_var(self.card))
        try:
            expr = to_sympy(a, self.ctx)
        except TranslateError:
            return _has_constant_term(a, self.card.constants)
        for c in present:
            dc = expr.diff(self.ctx.symbols[c])
            budget = min(0.3, self.deadline.left() - 0.5)
            if dc == 0 or budget <= 0.05 or zero_status(dc, budget) is True:
                continue
            if var is None or var not in dc.free_symbols:
                return True
            if zero_status(dc.diff(var), budget) is True:
                return True
        return False

    # ================================================================== equations
    def equation(self, answer: s.Equation, key: s.Equation) -> Verdict:
        g = _difference(answer.lhs, answer.rhs)
        f = _difference(key.lhs, key.rhs)
        verdict = self._ratio(g, f)
        if verdict.status != "correct":
            cleared = self._cleared(g), self._cleared(f)
            if cleared[0] is not None and cleared[1] is not None and cleared != (g, f):
                second = self._ratio(cleared[0], cleared[1])
                if second.status == "correct":
                    verdict, g, f = second, cleared[0], cleared[1]
        if verdict.status == "correct":
            verdict = self._equation_hole(answer, key) or verdict
        if matches(verdict) and self.symbolic:
            return self._confirm_ratio(g, f, verdict)
        return verdict

    def _equation_hole(self, answer: s.Equation, key: s.Equation) -> Verdict | None:
        """The answer divides by zero at a point of the key's solution set.

        Clearing denominators makes `y/x^2 = 1` pass the ratio test against `y = x^2`, but
        its graph leaves out (0, 0); `(y - 1)/x = 2` leaves (0, 1) out of y = 2x + 1. Such
        an answer is wrong, as an expression with a hole is. `xy = 1` against `y = 1/x`
        is fine: the key's own denominator is zero there too. Divisors that aren't
        polynomials, or systems SymPy can't solve in time, give undecidable.
        """
        import sympy

        divisors = [
            p.node for side in (answer.lhs, answer.rhs) for p in critical.parts(side) if p.singular
        ]
        if not divisors or self.ev.complex_mode:
            return None
        names = self._names(_difference(answer.lhs, answer.rhs), _difference(key.lhs, key.rhs))
        unsure = _undecidable("Couldn't check where your equation is undefined.")
        try:
            syms = [self.ctx.symbols[v] for v in names]
            numer, _ = sympy.fraction(
                sympy.together(to_sympy(_difference(key.lhs, key.rhs), self.ctx))
            )
            key_divisors = [
                to_sympy(p.node, self.ctx)
                for side in (key.lhs, key.rhs)
                for p in critical.parts(side)
                if p.singular
            ]
        except TranslateError, KeyError:
            return unsure
        for d in divisors:
            budget = min(0.5, self.deadline.left() - 0.4)
            if budget <= 0.05:
                return unsure
            try:
                ds = to_sympy(d, self.ctx)
                if not ds.is_polynomial(*syms) or not numer.is_polynomial(*syms):
                    return unsure
                with time_limit(budget):
                    solutions = sympy.solve([numer, ds], syms, dict=True)
            except SymbolicTimeout, TranslateError, NotImplementedError, RecursionError:
                return unsure
            except Exception:  # SymPy raises many internal errors; unknown is the safe answer
                return unsure
            for sol in solutions[:20]:
                point = self._solution_point(sol, syms)
                if point is None:
                    continue
                exact, env = point
                if any(zero_status(kd.subs(exact), 0.1) is not False for kd in key_divisors):
                    continue  # the key's own equation is undefined there too
                try:
                    lv = self._eval(key.lhs, env, CONST_DPS)
                    rv = self._eval(key.rhs, env, CONST_DPS)
                except Undefined, Overflow:
                    continue
                if abs(lv - rv) <= mpmath.mpf("1e-20") * (1 + abs(lv) + abs(rv)):
                    where = ", ".join(f"{v} = {mpmath.nstr(env[v], 6)}" for v in names)
                    if not self.card.domain_strict:  # one point left out: a hole
                        return _hole_verdict(where)
                    return _incorrect(
                        f"Your equation is undefined at {where}, which is on the correct graph."
                    )
        return None

    def _solution_point(
        self, sol: Mapping[object, object], syms: Sequence[object]
    ) -> tuple[dict[object, object], dict[str, Number]] | None:
        """One real point of a (possibly parametric) solution: (exact subs, numeric env)."""
        import sympy

        filler = {s: sympy.Rational(37, 100) * (i + 1) for i, s in enumerate(syms)}
        exact: dict[object, object] = {}
        env: dict[str, Number] = {}
        for s_ in syms:
            value = sol.get(s_, s_)
            if isinstance(value, sympy.Expr):
                value = value.subs({f: filler[f] for f in value.free_symbols if f in filler})
            v = critical.real_value(value, CONST_DPS)
            if v is None:
                return None
            exact[s_] = value
            env[str(s_)] = v
        return exact, env

    def _confirm_ratio(self, g: n.Node, f: n.Node, verdict: Verdict) -> Verdict:
        """Symbolic check that g/f is constant: every partial derivative is 0."""
        import sympy

        try:
            ratio = sympy.together(to_sympy(g, self.ctx) / to_sympy(f, self.ctx))
        except TranslateError:
            return verdict
        statuses = []
        for name in self._names(g, f):
            budget = min(SYMBOLIC_SOFT_SECONDS, self.deadline.left() - 0.3) / 2
            if budget <= 0.05:
                return verdict
            statuses.append(zero_status(ratio.diff(self.ctx.symbols[name]), budget))
        if False in statuses:
            return _incorrect("", "symbolic")
        if statuses and all(st is True for st in statuses):
            return replace(verdict, confirmed=True)
        return verdict

    def _cleared(self, node: n.Node) -> n.Node | None:
        """The numerator of left - right over a common denominator (via SymPy)."""
        import sympy

        from core.grader.translate import from_sympy

        try:
            expr = to_sympy(node, self.ctx)
            numer, _ = sympy.fraction(sympy.together(expr))
            return from_sympy(sympy.expand(numer))
        except TranslateError, TypeError, ValueError:
            return None

    def _ratio(self, g: n.Node, f: n.Node) -> Verdict:
        """STACK's ratio test: g = c*f for one nonzero constant c, checked by sampling."""
        names = self._names(g, f)
        if not names:
            return self.scalar(g, f)
        points = self.points_for(f, names)
        if not points:
            return _undecidable("The key equation isn't defined at enough points.")
        ratios: list[tuple[Mapping[str, Number], Number]] = []
        for env in points:
            try:
                fv = self._eval(f, env, DPS)
            except Undefined, Overflow:
                continue
            if abs(fv) < mpmath.mpf("1e-20"):
                continue
            try:
                gv = self._eval(g, env, DPS)
            except Undefined:
                return _incorrect("Your equation is undefined where the correct one is defined.")
            except Overflow:
                continue
            ratios.append((env, gv / fv))
        if len(ratios) < MIN_POINTS:
            return _undecidable("Too few points to compare.")
        env0, r0 = ratios[0]
        if abs(r0) < mpmath.mpf("1e-20"):
            return _incorrect()

        def ratio(env: Mapping[str, Number], dps: int) -> Number:
            with mp.workdps(dps):
                return self.ev(g, env) / self.ev(f, env)

        def first(env: Mapping[str, Number], dps: int) -> Number:
            return r0 if dps <= DPS else ratio(env0, dps)

        self._incomplete = False
        extra = [
            e
            for e in self._extra_points((g, f), names, [e for e, _ in ratios])
            if _nonzero_at(self, f, e)
        ]
        verdict = self._compare_values([e for e, _ in ratios], ratio, first, None, extra=extra)
        return self._unless_incomplete(verdict)

    # ================================================================== collections
    def sequence(self, a: Sequence[n.Node], k: Sequence[n.Node]) -> Verdict:
        if len(a) != len(k):
            return _incorrect("Wrong number of entries.", "shape")
        undecided = None
        for x, y in zip(a, k, strict=True):
            v = self.scalar(x, y, symbolic=self.symbolic)
            if v.status == "incorrect":
                return v
            if v.status == "undecidable":
                undecided = v
        return undecided or Verdict("correct", step="numeric")

    def _element(self, a: s.Element, k: s.Element) -> Verdict:
        if isinstance(a, s.Scalar) and isinstance(k, s.Scalar):
            return self.scalar(a.node, k.node, symbolic=self.symbolic)
        return self.compare(a, k, top=False)

    def elements(self, a: Sequence[s.Element], k: Sequence[s.Element], ordered: bool) -> Verdict:
        if ordered:
            if len(a) != len(k):
                return _incorrect("Wrong number of entries.", "shape")
            pairs = [self._element(x, y) for x, y in zip(a, k, strict=True)]
            return _combine(pairs)
        return self._set_equal(a, k, self._element)

    def points(self, a: Sequence[tuple[n.Node, ...]], k: Sequence[tuple[n.Node, ...]]) -> Verdict:
        if a and k and len(a[0]) != len(k[0]):
            return _incorrect("Wrong number of coordinates.", "shape")
        return self._set_equal(a, k, lambda x, y: self.sequence(x, y))

    def _set_equal[T](
        self, a: Sequence[T], k: Sequence[T], same: Callable[[T, T], Verdict]
    ) -> Verdict:
        if not a or not k:
            return Verdict("correct" if not a and not k else "incorrect", step="numeric")
        undecided = False
        matrix: dict[tuple[int, int], Verdict] = {}

        def eq(i: int, j: int) -> Verdict:
            if (i, j) not in matrix:
                matrix[(i, j)] = same(a[i], k[j])
            return matrix[(i, j)]

        hole: Verdict | None = None
        for i in range(len(a)):
            results = [eq(i, j) for j in range(len(k))]
            if not any(r.status == "correct" for r in results):
                holes = [r for r in results if r.status == "hole"]
                if holes:
                    hole = hole or holes[0]
                    continue
                if any(r.status == "undecidable" for r in results):
                    undecided = True
                    continue
                return _incorrect("An answer isn't in the solution set.")
        for j in range(len(k)):
            results = [eq(i, j) for i in range(len(a))]
            if not any(matches(r) for r in results):
                if any(r.status == "undecidable" for r in results):
                    undecided = True
                    continue
                return _incorrect("A solution is missing.")
        if undecided:
            return _undecidable("Some elements couldn't be compared.")
        return hole or Verdict("correct", step="numeric")

    # ================================================================== intervals
    def interval_sets(self, a: s.SetExpr, k: s.SetExpr) -> Verdict:
        either = self.card.endpoints_either
        try:
            kv = intervals.canonical(k, self.ev, either=either)
        except intervals.BadEndpoint:
            return _undecidable("The key has an endpoint with no value.")
        try:
            av = intervals.canonical(a, self.ev, either=either)
        except intervals.BadEndpoint:
            return _incorrect("An endpoint has no real value.")
        if intervals.equal(av, kv):
            return Verdict("correct", step="exact")
        return _incorrect()


# ====================================================================== helpers


def _within_exactly(a: Fraction, k: Fraction, tol: Tolerance) -> bool:
    """`_within` for two rational values, decided exactly (no rounding at the boundary)."""
    d = abs(a - k)
    if tol.kind == "absolute":
        return d <= tol.value
    if tol.kind == "sig-figs":
        if k == 0:
            return d == 0
        place = len(str(abs(k.numerator) // abs(k.denominator))) - 1
        while Fraction(10) ** place > abs(k):
            place -= 1
        return d <= Fraction(10) ** (place - int(tol.value) + 1) / 2
    return d <= max(tol.value * abs(k), tol.floor)


def _half_unit(k: Number, figures: int) -> Number:
    """Half a unit in the last of `figures` significant figures of k (0 for k = 0).

    The place comes from comparing with exact powers of ten, not from rounding a float
    logarithm (STACK #107: floor(0.1667*10^4) gave 1666).
    """
    size = abs(k)
    if size == 0:
        return mpmath.mpf(0)
    with mp.workdps(CONST_DPS):
        place = int(mpmath.floor(mpmath.log10(size)))
        while mpmath.mpf(10) ** place > size:
            place -= 1
        while mpmath.mpf(10) ** (place + 1) <= size:
            place += 1
        return mpmath.mpf(10) ** (place - figures + 1) / 2


def _where(env: Mapping[str, Number]) -> str:
    return ", ".join(f"{name} = {mpmath.nstr(v, 6)}" for name, v in sorted(env.items()))


def _nonzero_at(checker: Checker, node: n.Node, env: Mapping[str, Number]) -> bool:
    try:
        return bool(abs(checker._eval(node, env, DPS)) >= mpmath.mpf("1e-20"))
    except Undefined, Overflow:
        return False


def _rational(value: Number) -> object:
    """The exact binary value of an mpmath number, as a SymPy Rational."""
    import sympy

    sign, man, exp, _ = mpmath.mpf(value)._mpf_  # man_exp drops the sign
    return (-1 if sign else 1) * sympy.Integer(man) * sympy.Rational(2) ** int(exp)


def _integer_literal(node: n.Node) -> bool:
    node = n.unwrap(node)
    if isinstance(node, n.Neg):
        node = n.unwrap(node.arg)
    return isinstance(node, n.Num) and not node.is_decimal


def _draw(lo: float | None, hi: float | None, rng: random.Random, wide: bool) -> float:
    def spread() -> float:
        if wide:
            return rng.uniform(10.0, 45.0)
        return 10 ** rng.uniform(-1.3, 1.0)

    if lo is not None and hi is not None:
        return lo + (hi - lo) * rng.uniform(0.03, 0.97)
    if lo is not None:
        return lo + spread()
    if hi is not None:
        return hi - spread()
    if wide:
        return rng.choice((-1.0, 1.0)) * rng.uniform(10.0, 45.0)
    return rng.uniform(-9.0, 9.0)


def _contains(iv: intervals.Iv, v: float) -> bool:
    if iv.lo is not None and (v < iv.lo or (v == iv.lo and not iv.lo_closed)):
        return False
    return not (iv.hi is not None and (v > iv.hi or (v == iv.hi and not iv.hi_closed)))


def _spread(
    envs: list[dict[str, Number]], defined: list[bool], want: int, *, ordered: bool
) -> list[dict[str, Number]]:
    """Pick `want` defined points, at least one from each run of consecutive defined ones."""
    good = [i for i, ok in enumerate(defined) if ok]
    if len(good) <= want:
        return [envs[i] for i in good]
    picked: list[int] = []
    if ordered:
        runs: list[list[int]] = []
        for i in good:
            if runs and runs[-1][-1] == i - 1:
                runs[-1].append(i)
            else:
                runs.append([i])
        picked = [run[len(run) // 2] for run in runs][:want]
    rest = [i for i in good if i not in picked]
    step = len(rest) / max(1, want - len(picked))
    picked += [rest[int(j * step)] for j in range(want - len(picked)) if int(j * step) < len(rest)]
    return [envs[i] for i in sorted(set(picked))]


def _rel(op: str, a: Number, b: Number) -> bool:
    if isinstance(a, mpmath.mpc) or isinstance(b, mpmath.mpc):
        return False
    result = {
        "<": a < b,
        "<=": a <= b,
        ">": a > b,
        ">=": a >= b,
        "!=": a != b,
        "=": a == b,
    }[op]
    return bool(result)


def _difference(lhs: n.Node, rhs: n.Node) -> n.Node:
    return n.Sum((("+", n.Group(lhs)), ("-", n.Group(rhs))))


def _combine(verdicts: Iterable[Verdict]) -> Verdict:
    undecided = None
    hole = None
    for v in verdicts:
        if v.status == "incorrect":
            return v
        if v.status == "undecidable":
            undecided = v
        if v.status == "hole":
            hole = hole or v
    return undecided or hole or Verdict("correct", step="numeric")


def _integration_var(card: Card) -> str:
    names = [name for name, _ in card.variables]
    for preferred in ("x", "t"):
        if preferred in names:
            return preferred
    return names[0] if names else "x"


def _has_constant_term(node: n.Node, constants: Sequence[str]) -> bool:
    node = n.unwrap(node)
    terms = node.terms if isinstance(node, n.Sum) else (("+", node),)
    return any(isinstance(n.unwrap(t), n.Var) and n.unwrap(t).name in constants for _, t in terms)  # type: ignore[union-attr]


__all__ = ["Checker", "Verdict", "forms"]
