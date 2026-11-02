"""Shape validation: does the parsed answer have the form the answer type expects?

A mismatch ("expected an interval") is an InputError of kind "shape": shown inline,
never counted as an attempt. The result is a typed Value the checker compares.
"""

from collections.abc import Collection
from dataclasses import dataclass

from core.grader import errors
from core.grader import nodes as n


@dataclass(frozen=True, slots=True)
class Scalar:
    node: n.Node


@dataclass(frozen=True, slots=True)
class Infinity:
    sign: int


@dataclass(frozen=True, slots=True)
class DneValue:
    pass


type Element = Scalar | Infinity | DneValue


@dataclass(frozen=True, slots=True)
class Equation:
    lhs: n.Node
    rhs: n.Node


@dataclass(frozen=True, slots=True)
class Elements:
    """A set (unordered) or a list (ordered) of values."""

    items: tuple[Element, ...]
    ordered: bool


@dataclass(frozen=True, slots=True)
class Points:
    points: tuple[tuple[n.Node, ...], ...]


@dataclass(frozen=True, slots=True)
class VectorValue:
    items: tuple[n.Node, ...]


@dataclass(frozen=True, slots=True)
class MatrixValue:
    rows: tuple[tuple[n.Node, ...], ...]


@dataclass(frozen=True, slots=True)
class Piece:
    """One interval; None means -inf (lo) or +inf (hi). lo == hi closed is a point."""

    lo: n.Node | None
    hi: n.Node | None
    lo_closed: bool
    hi_closed: bool


@dataclass(frozen=True, slots=True)
class SetOp:
    op: str  # "union" or "intersect"
    items: tuple[SetExpr, ...]


type SetExpr = Piece | SetOp


@dataclass(frozen=True, slots=True)
class Intervals:
    expr: SetExpr


type Value = (
    Scalar
    | Infinity
    | DneValue
    | Equation
    | Elements
    | Points
    | VectorValue
    | MatrixValue
    | Intervals
)

EMPTY = SetOp("union", ())

_NAMES = {
    "number": "a number",
    "expression": "an expression",
    "equation": "an equation",
    "antiderivative": "an expression",
    "set": "a list of values separated by commas",
    "list": "a list of values separated by commas",
    "interval": "an interval",
    "point": "a point such as (2, -4)",
    "vector": "a vector such as <1, -2, 3>",
    "matrix": "a matrix such as [[1, 2], [3, 4]]",
    "quantity": "a quantity",
}


def expected(kind: str) -> errors.InputError:
    return errors.shape(f"Expected {_NAMES.get(kind, 'an answer')}.")


def _is_inf(node: n.Node) -> int:
    """+1 / -1 if node is (-)inf, else 0."""
    node = n.unwrap(node)
    if isinstance(node, n.Const) and node.name == "inf":
        return 1
    if isinstance(node, n.Neg):
        return -_is_inf(node.arg)
    return 0


def _check_scalar(node: n.Node, what: str = "") -> n.Node:
    match n.unwrap(node):
        case n.Chain(_, ops) if "=" in ops:
            raise errors.shape(
                f"Expected {what or 'a value'}, not an equation.",
                "Leave out the 'x =' part and give just the value.",
            )
        case n.Chain() | n.Or() | n.And():
            raise errors.shape(f"Expected {what or 'a value'}, not an inequality.")
        case n.Tuple() | n.SetLit() | n.Union() | n.NoneSet() | n.Vector() | n.Matrix():
            raise errors.shape(f"Expected {what or 'a value'}.")
        case n.Dne():
            raise errors.shape(f"DNE doesn't fit here: expected {what or 'a value'}.")
    for sub in n.walk(node):
        if isinstance(sub, n.Const) and sub.name == "inf":
            raise errors.shape("inf can only stand on its own, as in inf or -inf.")
    return node


def _element(node: n.Node, allow_tokens: bool, what: str = "") -> Element:
    if isinstance(n.unwrap(node), n.Dne) and allow_tokens:
        return DneValue()
    sign = _is_inf(node)
    if sign and allow_tokens:
        return Infinity(sign)
    return Scalar(_check_scalar(node, what))


def shape_value(
    parsed: n.Parsed,
    kind: str,
    variables: Collection[str] = (),
    constants: Collection[str] = (),
) -> Value:
    """Turn a parsed answer into the Value its answer type expects (or raise a shape error)."""
    if len(parsed.alternatives) != 1:
        raise errors.shape("Give one answer (no ';').")
    items = parsed.alternatives[0]
    single = items[0] if len(items) == 1 else None
    if kind in {"number", "expression", "antiderivative", "quantity"}:
        if single is None:
            raise errors.shape(
                f"Expected {_NAMES[kind]}, not a list.",
                "Commas separate list items; don't use them inside numbers.",
            )
        if kind in {"expression", "antiderivative", "quantity"}:
            if isinstance(single, n.Dne):
                raise errors.shape(f"DNE doesn't fit here: expected {_NAMES[kind]}.")
            return Scalar(_check_scalar(single, _NAMES[kind]))
        value = _element(single, allow_tokens=True, what=_NAMES[kind])
        if isinstance(value, Scalar):
            names = n.free_vars(value.node)
            if names:
                raise errors.shape(f"Expected a number, not an expression in {min(names)}.")
        return value
    if kind == "equation":
        node = n.unwrap(single) if single is not None else None
        if not isinstance(node, n.Chain) or node.ops != ("=",):
            raise errors.shape("Expected an equation with one '=' sign, such as y = 2x + 1.")
        return Equation(_check_scalar(node.operands[0]), _check_scalar(node.operands[1]))
    if kind in {"set", "list"}:
        return _elements(items, ordered=kind == "list")
    if kind == "point":
        return _points(items)
    if kind == "vector":
        node = n.unwrap(single) if single is not None else None
        if isinstance(node, n.Vector) or (
            isinstance(node, n.Tuple) and (node.left, node.right) == ("(", ")")
        ):
            return VectorValue(tuple(_check_scalar(x) for x in node.items))
        raise expected(kind)
    if kind == "matrix":
        node = n.unwrap(single) if single is not None else None
        if not isinstance(node, n.Matrix):
            raise expected(kind)
        if len({len(r) for r in node.rows}) != 1:
            raise errors.shape("Every row of a matrix needs the same number of entries.")
        return MatrixValue(tuple(tuple(_check_scalar(x) for x in r) for r in node.rows))
    if kind == "interval":
        if single is None:
            raise errors.shape("Expected an interval.", "Join intervals with U, not commas.")
        used = sorted(n.free_vars(single))
        if len(used) > 1:  # x > 1 and y > 1 is not a set of numbers on one line
            raise errors.shape(
                f"Use one variable, not {' and '.join(used)}.",
                "Write the set with the problem's variable, such as -1 <= x < 3.",
            )
        return Intervals(_set_expr(single, variables))
    raise expected(kind)


def _elements(items: tuple[n.Node, ...], ordered: bool) -> Elements:
    if len(items) == 1:
        node = n.unwrap(items[0])
        if isinstance(node, n.NoneSet):
            return Elements((), ordered)
        if isinstance(node, n.SetLit) and not ordered:
            items = node.items
        if isinstance(node, n.Union | n.Tuple):
            raise errors.shape(
                "Expected values separated by commas.",
                "Write the values themselves, such as -1, 0, 1.",
            )
    return Elements(tuple(_element(x, allow_tokens=True) for x in items), ordered)


def _points(items: tuple[n.Node, ...]) -> Points:
    if len(items) == 1 and isinstance(n.unwrap(items[0]), n.NoneSet):
        return Points(())
    points: list[tuple[n.Node, ...]] = []
    for item in items:
        node = n.unwrap(item)
        if not isinstance(node, n.Tuple) or (node.left, node.right) != ("(", ")"):
            raise errors.shape("Expected a point such as (2, -4).")
        points.append(tuple(_check_scalar(x) for x in node.items))
    if len({len(p) for p in points}) > 1:
        raise errors.shape("All points need the same number of coordinates.")
    return Points(tuple(points))


def _endpoint(node: n.Node, low: bool, closed: bool) -> n.Node | None:
    sign = _is_inf(node)
    if sign:
        if (low and sign > 0) or (not low and sign < 0):
            raise errors.shape("An interval can't start at inf or end at -inf.")
        if closed:
            raise errors.shape("Infinity is never included: use ( or ) next to inf.")
        return None
    _check_scalar(node, "an endpoint")
    if n.free_vars(node):
        raise errors.shape("Interval endpoints must be numbers.")
    return node


def _set_expr(node: n.Node, variables: Collection[str]) -> SetExpr:
    node = n.unwrap(node)
    match node:
        case n.NoneSet():
            return EMPTY
        case n.Union(items):
            return SetOp("union", tuple(_set_expr(x, variables) for x in items))
        case n.Tuple(items, left, right):
            if len(items) != 2:
                raise errors.shape("An interval has two endpoints, such as (0, 2].")
            lo = _endpoint(items[0], True, left == "[")
            hi = _endpoint(items[1], False, right == "]")
            return Piece(lo, hi, left == "[", right == "]")
        case n.SetLit(items):
            pieces: list[SetExpr] = []
            for x in items:
                pt = _endpoint(x, True, True)
                pieces.append(Piece(pt, pt, True, True))
            return SetOp("union", tuple(pieces))
        case n.Or(items):
            return SetOp("union", tuple(_set_expr(x, variables) for x in items))
        case n.And(items):
            return SetOp("intersect", tuple(_set_expr(x, variables) for x in items))
        case n.Chain():
            return _inequality(node)
    raise errors.shape(
        "Expected an interval.",
        "Write it like (-inf, 0) U (2, inf), or as inequalities like x < 0 or x > 2.",
    )


_FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "=": "=", "!=": "!="}


def _inequality(chain: n.Chain) -> SetExpr:
    operands = [n.unwrap(x) for x in chain.operands]
    var_at = [k for k, x in enumerate(operands) if isinstance(x, n.Var)]
    if len(var_at) != 1 or any(n.free_vars(x) for k, x in enumerate(operands) if k != var_at[0]):
        raise errors.shape(
            "Write the inequality with the variable alone, such as -1 <= x < 3.",
        )
    k = var_at[0]
    if len(operands) == 2:
        op = chain.ops[0] if k == 0 else _FLIP[chain.ops[0]]
        other = chain.operands[1 - k]
        return _simple(op, other)
    if len(operands) == 3 and k == 1:
        left_op, right_op = _FLIP[chain.ops[0]], chain.ops[1]  # both now "x op c"
        a, b = chain.operands[0], chain.operands[2]
        if left_op in {">", ">="} and right_op in {"<", "<="}:
            return Piece(_endpoint(a, True, left_op == ">="), _endpoint(b, False, right_op == "<="),
                         left_op == ">=", right_op == "<=")  # fmt: skip
        if left_op in {"<", "<="} and right_op in {">", ">="}:
            return Piece(_endpoint(b, True, right_op == ">="), _endpoint(a, False, left_op == "<="),
                         right_op == ">=", left_op == "<=")  # fmt: skip
    raise errors.shape("Can't read this chain of inequalities.", "Write it like -1 <= x < 3.")


def _simple(op: str, other: n.Node) -> SetExpr:
    """x op c."""
    match op:
        case "<" | "<=":
            return Piece(None, _endpoint(other, False, op == "<="), False, op == "<=")
        case ">" | ">=":
            return Piece(_endpoint(other, True, op == ">="), None, op == ">=", False)
        case "=":
            pt = _endpoint(other, True, True)
            return Piece(pt, pt, True, True)
        case _:  # !=
            pt = _endpoint(other, True, False)
            return SetOp("union", (Piece(None, pt, False, False), Piece(pt, None, False, False)))
