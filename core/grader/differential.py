"""Differential check of a verdict (DEV-18): SymPy and our mpmath evaluator side by side.

The grader samples answers with its own mpmath evaluator (numeric.py) and confirms with
SymPy (symbolic.py); template keys come from SymPy (core/cards/cas.py). Here both engines
evaluate the answer and the key at the checker's own sample points, independently:
mpmath through our tree, SymPy through `evalf` of the translated expression at the exact
binary value of each point. Problems reported:

- the engines disagree on the value of the key or of the answer at a point (both real);
- the verdict is correct but SymPy finds the values different at a point (a false
  accept is the dangerous direction; an incorrect verdict often rests on a domain rule,
  which SymPy's real evaluation at these points does not see, so it is not second-guessed).

Runs inside the grader's worker process (pipeline.py, Job mode "cross"). Scalars only
(number and expression cards); other types report nothing.
"""

from collections.abc import Mapping

import mpmath
import sympy
from mpmath import mp

from core.grader import nodes as n
from core.grader import shapes as s
from core.grader.numeric import Number, Overflow, Undefined
from core.grader.serialize import to_text
from core.grader.spec import Card
from core.grader.symbolic import Deadline
from core.grader.translate import TranslateError, to_sympy

DPS = 30
MAX_POINTS = 8
ENGINES_CLOSE = mpmath.mpf("1e-20")  # both engines at 30 digits: rounding only


def cross(card: Card, answer: s.Value, status: str, deadline: Deadline) -> list[str]:
    """Disagreements between the engines, or with the verdict `status`, for one answer."""
    if card.answer_type not in {"number", "expression"} or not isinstance(answer, s.Scalar):
        return []
    with mp.workdps(DPS):
        return _cross(card, answer, status, deadline)


def _cross(card: Card, answer: s.Scalar, status: str, deadline: Deadline) -> list[str]:
    from core.grader.compare import Checker, _rational

    checker = Checker(card, deadline, symbolic=False)
    problems: list[str] = []
    a = answer.node
    for key in card.keys:
        if not isinstance(key, s.Scalar):
            continue
        k = key.node
        names = checker._names(a, k)
        envs: list[Mapping[str, Number]] = [{}]
        if names:
            envs = list((checker.points_for(k, names) or [])[:MAX_POINTS])
        try:
            sa, sk = to_sympy(a, checker.ctx), to_sympy(k, checker.ctx)
        except TranslateError:
            continue
        for env in envs:
            if deadline.left() < 0.2:
                return problems
            subs = {checker.ctx.symbols[v]: _rational(x) for v, x in env.items()}
            values: dict[str, tuple[Number | None, Number | None]] = {}
            for label, node, expr in (("answer", a, sa), ("key", k, sk)):
                mv = _mpmath(checker, node, env)
                sv = _sympy(expr, subs)
                values[label] = (mv, sv)
                if mv is not None and sv is not None and not _close(mv, sv, ENGINES_CLOSE):
                    problems.append(
                        f"the engines disagree on the {label} {to_text(node)} at {_where(env)}: "
                        f"mpmath {mpmath.nstr(mv, 12)}, SymPy {mpmath.nstr(sv, 12)}"
                    )
            sa_v, sk_v = values["answer"][1], values["key"][1]
            if sa_v is None or sk_v is None:
                continue
            exact = not (n.has_decimal(a) or n.has_decimal(k))
            if status == "correct" and exact and not _close(sa_v, sk_v, mpmath.mpf("1e-25")):
                problems.append(
                    f"graded correct, but SymPy evaluates {to_text(a)} and {to_text(k)} "
                    f"differently at {_where(env)}"
                )
    return list(dict.fromkeys(problems))


def _mpmath(checker: object, node: n.Node, env: Mapping[str, Number]) -> Number | None:
    try:
        v = checker._eval(node, env, DPS)  # type: ignore[attr-defined]
    except Undefined, Overflow:
        return None
    return v if isinstance(v, mpmath.mpf) and mpmath.isfinite(v) else None


def _sympy(expr: sympy.Expr, subs: Mapping[object, object]) -> Number | None:
    try:
        v = expr.evalf(DPS, subs=subs)
    except Exception:  # SymPy raises many internal errors: no value, no comparison
        return None
    if not (v.is_Number and v.is_real and v.is_finite):
        return None
    return mpmath.mpf(sympy.Float(v, DPS)._mpf_)


def _close(a: Number, b: Number, rel: Number) -> bool:
    """Relatively close, or both within rounding noise of 0 at 30 digits (sin(pi))."""
    return bool(abs(a - b) <= rel * max(abs(a), abs(b)) + mpmath.mpf("1e-25"))


def _where(env: Mapping[str, Number]) -> str:
    return ", ".join(f"{v} = {mpmath.nstr(x, 8)}" for v, x in env.items()) or "the value"
