"""Plain-text answer syntax -> answer AST (nodes.py), via our tokenizer and a Lark grammar.

Nothing here evaluates anything (ADR-0003): the tree is built from whitelisted tokens.
"""

import functools
from collections.abc import Iterator
from typing import Any

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedInput, VisitError
from lark.lexer import Lexer

from core.grader import errors
from core.grader import nodes as n
from core.grader.exact import exact_rational
from core.grader.grammar import GRAMMAR
from core.grader.tokens import MAX_CHARS, Tokens, Vocabulary, tokenize

MAX_EXPONENT = 1000

_DESCRIBE = {
    "RPAREN": "')'",
    "RBRACK": "']'",
    "RBRACE": "'}'",
    "ABS_CLOSE": "a closing '|'",
    "RANGLE": "'>'",
    "COMMA": "','",
    "$END": "the end",
}


class _TokenListLexer(Lexer):
    """Feeds our pre-built tokens to Lark (the 'text' passed to parse() is a Tokens)."""

    def __init__(self, lexer_conf: Any) -> None:
        pass

    def lex(self, data: Tokens) -> Iterator[Token]:  # type: ignore[override]
        # Lark calls custom lexers with the object given to parse().
        tokens = data
        for i, tok in enumerate(tokens.toks):
            yield Token(tok.type, tok.value, start_pos=i, line=1, column=i + 1)


@functools.cache
def _lark() -> Lark:
    return Lark(GRAMMAR, parser="lalr", lexer=_TokenListLexer)


def _ops(items: list[Any]) -> list[Any]:
    return [x.children[0].value if hasattr(x, "children") else x for x in items]


@v_args(inline=True)
class _ToAst(Transformer[Token, Any]):
    def start(self, *alts: Any) -> n.Parsed:
        return n.Parsed(tuple(a for a in alts if not isinstance(a, Token)))

    def alternative(self, *items: Any) -> tuple[n.Node, ...]:
        return tuple(x for x in items if not isinstance(x, Token))

    def dne(self, _tok: Token) -> n.Dne:
        return n.Dne()

    def none(self, _tok: Token) -> n.NoneSet:
        return n.NoneSet()

    def disj(self, *items: Any) -> n.Or:
        return n.Or(tuple(x for x in items if not isinstance(x, Token)))

    def conj(self, *items: Any) -> n.And:
        return n.And(tuple(x for x in items if not isinstance(x, Token)))

    def relop(self, tok: Token) -> str:
        return {"EQ": "=", "LT": "<", "LE": "<=", "GT": ">", "GE": ">=", "NE": "!="}[tok.type]

    def chain(self, *items: Any) -> n.Chain:
        return n.Chain(tuple(items[0::2]), tuple(items[1::2]))

    def setexpr(self, *items: Any) -> n.Union:
        return n.Union(tuple(x for x in items if not isinstance(x, Token)))

    def close(self, tok: Token) -> str:
        return str(tok.value)

    def bracketed(self, left: Token, *rest: Any) -> n.Tuple:
        right = rest[-1]
        items = tuple(x for x in rest[:-1] if not isinstance(x, Token))
        return n.Tuple(items, str(left.value), right)

    def setlit(self, *items: Any) -> n.SetLit:
        return n.SetLit(tuple(x for x in items if x is not None and not isinstance(x, Token)))

    def vector(self, *items: Any) -> n.Vector:
        return n.Vector(tuple(x for x in items if not isinstance(x, Token)))

    def matrix(self, *items: Any) -> n.Matrix:
        return n.Matrix(tuple(x for x in items if not isinstance(x, Token)))

    def row(self, *items: Any) -> tuple[n.Node, ...]:
        return tuple(x for x in items if not isinstance(x, Token))

    def addop(self, tok: Token) -> str:
        return "+" if tok.type == "PLUS" else "-"

    def sum(self, first: n.Node, *rest: Any) -> n.Node:
        if not rest:
            return first
        terms = [("+", first)]
        terms += [(rest[i], rest[i + 1]) for i in range(0, len(rest), 2)]
        return n.Sum(tuple(terms))

    def mulop(self, tok: Token) -> str:
        return "*" if tok.type == "STAR" else "/"

    def product(self, first: n.Node, *rest: Any) -> n.Node:
        if not rest:
            return first
        factors: list[tuple[str, n.Node]] = [("*", first)]
        i = 0
        while i < len(rest):
            if isinstance(rest[i], str):
                factors.append((rest[i], rest[i + 1]))
                i += 2
            else:
                factors.append(("", rest[i]))
                i += 1
        return n.Product(tuple(factors))

    def neg(self, _tok: Token, arg: n.Node) -> n.Node:
        return n.Neg(arg)

    def pos(self, _tok: Token, arg: n.Node) -> n.Node:
        return arg

    def pow(self, base: n.Node, _tok: Token, exp: n.Node) -> n.Power:
        return n.Power(base, exp)

    def degree(self, arg: n.Node, _tok: Token) -> n.Degree:
        return n.Degree(arg)

    def number(self, tok: Token) -> n.Num:
        return n.Num(str(tok.value))

    def var(self, tok: Token) -> n.Var:
        return n.Var(str(tok.value))

    def const(self, tok: Token) -> n.Const:
        return n.Const(str(tok.value))

    def group(self, _l: Token, arg: n.Node, _r: Token) -> n.Group:
        return n.Group(arg)

    def abs(self, _l: Token, arg: n.Node, _r: Token) -> n.Call:
        return n.Call("abs", (arg,))

    def call_abs(self, func: Token, _l: Token, arg: n.Node, _r: Token) -> n.Call:
        return self.call(func, n.Call("abs", (arg,)))

    def call(self, func: Token, *rest: Any) -> n.Call:
        args = tuple(x for x in rest if not isinstance(x, Token))
        name = str(func.value)
        base: n.Node | None = None
        if name.startswith("log_"):
            sub = name[4:]
            base = n.Num(sub) if sub.isdigit() else n.Var(sub)
            name = "log"
        arity = 2 if name == "root" else 1
        if len(args) != arity:
            want = "root(x, n)" if name == "root" else f"{name}(x)"
            raise errors.syntax(f"{name} takes {arity} argument{'s' * (arity > 1)}: {want}.")
        return n.Call(name, args, base)


def parse(raw: str, vocab: Vocabulary, max_chars: int = MAX_CHARS) -> n.Parsed:
    """Parse answer text. Raises InputError (syntax or limit) with hints."""
    tokens = tokenize(raw, vocab, max_chars)
    try:
        tree = _lark().parse(tokens)
        result = _ToAst().transform(tree)
    except UnexpectedInput as exc:
        raise _syntax_error(tokens, exc) from None
    except VisitError as exc:
        if isinstance(exc.orig_exc, errors.InputError):
            raise exc.orig_exc from None
        raise
    if not isinstance(result, n.Parsed):
        raise errors.syntax("Can't read this answer.")
    _check_exponents(result)
    return result


def _check_exponents(parsed: n.Parsed) -> None:
    """MATH-10: caps on exponent size, so no input can hang the checker."""
    for alt in parsed.alternatives:
        for item in alt:
            for sub in n.walk(item):
                if isinstance(sub, n.Power):
                    q = exact_rational(sub.exp)
                    big = q is not None and abs(q) > MAX_EXPONENT
                    if big or (q is None and _too_big(sub.exp)):
                        raise errors.limit(f"Exponents are limited to {MAX_EXPONENT}.")


def _too_big(node: n.Node) -> bool:
    """A constant exponent that exact_rational gave up on because it is huge."""
    return any(
        isinstance(sub, n.Power)
        and not n.free_vars(sub)
        and exact_rational(sub) is None
        and exact_rational(sub.base) is not None
        and exact_rational(sub.exp) is not None
        for sub in n.walk(node)
    )


def _syntax_error(tokens: Tokens, exc: UnexpectedInput) -> errors.InputError:
    toks = tokens.toks
    token = getattr(exc, "token", None)
    index = getattr(token, "start_pos", None)
    if getattr(token, "type", None) == "$END":
        index = None
    expected = sorted(getattr(exc, "expected", None) or getattr(exc, "allowed", None) or ())
    if not isinstance(index, int) or index >= len(toks):
        wanted = [_DESCRIBE[e] for e in expected if e in _DESCRIBE and e != "$END"]
        hint = (f"Expected {' or '.join(wanted)}.",) if wanted else ()
        return errors.InputError("syntax", "The answer ends too early.", hint)
    tok = toks[index]
    where = tokens.text[: tok.pos].rstrip()
    near = f" after {where[-12:]!r}" if where else " at the start"
    wanted = [_DESCRIBE[e] for e in expected if e in _DESCRIBE]
    hints: tuple[str, ...] = (f"Expected {' or '.join(wanted)}.",) if wanted else ()
    if tok.type == "EQ" and index == 0:
        hints = ("Nothing comes before '='.",)
    return errors.InputError("syntax", f"Unexpected {tok.value!r}{near}.", hints)
