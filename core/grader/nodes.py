"""The answer AST: what the student typed, before any math happens.

The parser builds these nodes; nothing here touches SymPy. Keeping our own tree lets the
checker see the answer exactly as written (for `form` checks and the "read as" preview)
and evaluate it numerically with strict real semantics, which SymPy's automatic
simplification would lose (`sqrt(x)^2` becomes `x`, `e^(ln(x))` becomes `x`).
All nodes are frozen and picklable, so they can be sent to the worker process.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Num:
    """A decimal literal as typed: "2", "0.333", or e-notation stored as "6.02E23"."""

    text: str

    @property
    def is_decimal(self) -> bool:
        return "." in self.text or "E" in self.text


@dataclass(frozen=True, slots=True)
class Var:
    name: str


@dataclass(frozen=True, slots=True)
class Const:
    """pi, e (Euler's number), inf, or i (only when the card enables it)."""

    name: str


@dataclass(frozen=True, slots=True)
class Neg:
    arg: Node


@dataclass(frozen=True, slots=True)
class Sum:
    """terms[0] has op "+"; the rest "+" or "-"."""

    terms: tuple[tuple[str, Node], ...]


@dataclass(frozen=True, slots=True)
class Product:
    """factors[0] has op "*"; the rest "*", "/" or "" (implicit multiplication)."""

    factors: tuple[tuple[str, Node], ...]


@dataclass(frozen=True, slots=True)
class Power:
    base: Node
    exp: Node


@dataclass(frozen=True, slots=True)
class Call:
    """A whitelisted function. `log` with a base keeps it in `base`."""

    func: str
    args: tuple[Node, ...]
    base: Node | None = None


@dataclass(frozen=True, slots=True)
class Group:
    """Parentheses the student typed (kept for previews and form checks)."""

    arg: Node


@dataclass(frozen=True, slots=True)
class Degree:
    """A postfix degree mark: 30°."""

    arg: Node


@dataclass(frozen=True, slots=True)
class Chain:
    """Relations: a = b, a < b <= c. ops[i] sits between operands[i] and operands[i+1]."""

    operands: tuple[Node, ...]
    ops: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Or:
    items: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class And:
    items: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Tuple:
    """(a, b), [a, b), ... : a point or an interval, decided by the answer type."""

    items: tuple[Node, ...]
    left: str
    right: str


@dataclass(frozen=True, slots=True)
class SetLit:
    items: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Vector:
    items: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Matrix:
    rows: tuple[tuple[Node, ...], ...]


@dataclass(frozen=True, slots=True)
class Union:
    items: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class Dne:
    pass


@dataclass(frozen=True, slots=True)
class NoneSet:
    pass


type Node = (
    Num
    | Var
    | Const
    | Neg
    | Sum
    | Product
    | Power
    | Call
    | Group
    | Degree
    | Chain
    | Or
    | And
    | Tuple
    | SetLit
    | Vector
    | Matrix
    | Union
    | Dne
    | NoneSet
)

SCALAR_NODES = (Num, Var, Const, Neg, Sum, Product, Power, Call, Group, Degree)


@dataclass(frozen=True, slots=True)
class Parsed:
    """A whole answer: `;`-separated alternatives, each a `,`-separated list of items."""

    alternatives: tuple[tuple[Node, ...], ...]


def unwrap(node: Node) -> Node:
    while isinstance(node, Group):
        node = node.arg
    return node


def walk(node: Node) -> list[Node]:
    """Every node in the tree, parents first (iterative: trees can be deep)."""
    out: list[Node] = []
    stack: list[Node] = [node]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(reversed(children(n)))
    return out


def children(node: Node) -> tuple[Node, ...]:
    match node:
        case Neg(arg) | Group(arg) | Degree(arg):
            return (arg,)
        case Sum(terms):
            return tuple(t for _, t in terms)
        case Product(factors):
            return tuple(f for _, f in factors)
        case Power(base, exp):
            return (base, exp)
        case Call(_, args, base):
            return (*args, base) if base is not None else args
        case Chain(operands, _):
            return operands
        case Or(items) | And(items) | Tuple(items) | SetLit(items) | Vector(items):
            return items
        case Union(items):
            return items
        case Matrix(rows):
            return tuple(x for row in rows for x in row)
        case _:
            return ()


def free_vars(node: Node) -> set[str]:
    return {n.name for n in walk(node) if isinstance(n, Var)}


def has_decimal(node: Node) -> bool:
    return any(isinstance(n, Num) and n.is_decimal for n in walk(node))
