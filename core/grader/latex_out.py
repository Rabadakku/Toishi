"""The "read as" preview (MATH-6): LaTeX of the parsed answer, multiplication explicit.

It shows the tree exactly as the checker reads it: `1/2x` renders as 1/2 · x and
`e^2x` as e^2 · x, with a note for each so the student can fix it before submitting.
"""

import itertools

from core.grader import nodes as n
from core.grader.serialize import to_text
from core.grader.tokens import GREEK

_FUNC = {
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "sec": r"\sec",
    "csc": r"\csc",
    "cot": r"\cot",
    "arcsin": r"\arcsin",
    "arccos": r"\arccos",
    "arctan": r"\arctan",
    "arcsec": r"\operatorname{arcsec}",
    "arccsc": r"\operatorname{arccsc}",
    "arccot": r"\operatorname{arccot}",
    "sinh": r"\sinh",
    "cosh": r"\cosh",
    "tanh": r"\tanh",
    "ln": r"\ln",
    "exp": r"\exp",
    "sign": r"\operatorname{sign}",
}
_REL = {"=": "=", "<": "<", "<=": r"\le", ">": ">", ">=": r"\ge", "!=": r"\ne"}


def _name(name: str) -> str:
    base, _, sub = name.partition("_")
    out = f"\\{base}" if base in GREEK else base
    return f"{out}_{{{sub}}}" if sub else out


def _paren(tex: str) -> str:
    return rf"\left({tex}\right)"


def latex(node: n.Node) -> str:
    match node:
        case n.Num(text):
            mantissa, e, exponent = text.partition("E")
            return rf"{mantissa} \times 10^{{{exponent}}}" if e else text
        case n.Var(name):
            return _name(name)
        case n.Const("pi"):
            return r"\pi"
        case n.Const("inf"):
            return r"\infty"
        case n.Const(name):
            return name
        case n.Group(arg):
            return _paren(latex(arg))
        case n.Neg(arg):
            inner = latex(arg)
            return f"-{_paren(inner) if isinstance(arg, n.Sum) else inner}"
        case n.Sum(terms):
            out = ""
            for i, (op, t) in enumerate(terms):
                tex = latex(t)
                if isinstance(t, n.Neg) and i:
                    tex = _paren(tex)
                out = tex if i == 0 else f"{out} {op} {tex}"
            return out
        case n.Product(factors):
            out = ""
            for i, (op, f) in enumerate(factors):
                tex = latex(f)
                if op != "/" and (isinstance(f, n.Sum) or (i and isinstance(f, n.Neg))):
                    tex = _paren(tex)
                if i == 0:
                    out = tex
                elif op == "/":
                    out = rf"\frac{{{out}}}{{{tex}}}"
                else:
                    out = rf"{out} \cdot {tex}"
            return out
        case n.Power(base, exp):
            b = latex(base)
            if not isinstance(base, n.Num | n.Var | n.Const | n.Group) and not (
                isinstance(base, n.Call) and base.func in {"abs", "sqrt", "root"}
            ):
                b = _paren(b)
            if isinstance(base, n.Call) and base.func not in {"abs", "sqrt", "root"}:
                b = _paren(latex(base))
            return f"{{{b}}}^{{{latex(exp)}}}"
        case n.Degree(arg):
            return f"{latex(arg)}^{{\\circ}}"
        case n.Call("abs", args):
            return rf"\left|{latex(args[0])}\right|"
        case n.Call("sqrt", args):
            return rf"\sqrt{{{latex(args[0])}}}"
        case n.Call("root", args):
            return rf"\sqrt[{latex(args[1])}]{{{latex(args[0])}}}"
        case n.Call("log", args, base):
            sub = latex(base) if base is not None else "10"
            return rf"\log_{{{sub}}}{_paren(latex(args[0]))}"
        case n.Call(func, args):
            return f"{_FUNC[func]}{_paren(', '.join(latex(a) for a in args))}"
        case n.Chain(operands, ops):
            out = latex(operands[0])
            for op, o in zip(ops, operands[1:], strict=True):
                out += f" {_REL[op]} {latex(o)}"
            return out
        case n.Or(items):
            return r" \text{ or } ".join(latex(i) for i in items)
        case n.And(items):
            return r" \text{ and } ".join(latex(i) for i in items)
        case n.Tuple(items, left, right):
            return rf"\left{left}{', '.join(latex(i) for i in items)}\right{right}"
        case n.SetLit(items):
            return rf"\left\{{{', '.join(latex(i) for i in items)}\right\}}"
        case n.Vector(items):
            return rf"\left\langle {', '.join(latex(i) for i in items)}\right\rangle"
        case n.Matrix(rows):
            body = r" \\ ".join(" & ".join(latex(x) for x in r) for r in rows)
            return rf"\begin{{bmatrix}}{body}\end{{bmatrix}}"
        case n.Union(items):
            return r" \cup ".join(latex(i) for i in items)
        case n.Dne():
            return r"\text{DNE}"
        case n.NoneSet():
            return r"\varnothing"
    raise TypeError(f"no LaTeX for {node!r}")


def parsed_latex(parsed: n.Parsed) -> str:
    return "; ".join(", ".join(latex(i) for i in alt) for alt in parsed.alternatives)


def reading_notes(parsed: n.Parsed) -> tuple[str, ...]:
    """Notes on readings a student may not expect: e^2x and 1/2x."""
    notes: list[str] = []
    for alt in parsed.alternatives:
        for item in alt:
            for sub in n.walk(item):
                if not isinstance(sub, n.Product):
                    continue
                factors = sub.factors
                for (_, left), (op, right) in itertools.pairwise(factors):
                    if op != "":
                        continue
                    if isinstance(left, n.Power) and isinstance(left.exp, n.Num):
                        base, power, nxt = to_text(left.base), left.exp.text, to_text(right)
                        notes.append(
                            f"{base}^{power}{nxt} is read as {base}^{power} times {nxt}. "
                            f"For {base}^({power}{nxt}), add parentheses."
                        )
                for i in range(1, len(factors) - 1):
                    if factors[i][0] == "/" and factors[i + 1][0] == "":
                        head = to_text(n.Product(factors[:i])) if i > 1 else to_text(factors[0][1])
                        den, nxt = to_text(factors[i][1]), to_text(factors[i + 1][1])
                        notes.append(
                            f"{head}/{den}{nxt} is read as ({head}/{den})*{nxt}. "
                            f"Write {head}/({den}{nxt}) if {nxt} belongs in the denominator."
                        )
    return tuple(dict.fromkeys(notes))
