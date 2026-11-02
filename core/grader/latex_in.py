"""MathLive input: lower the math field's LaTeX to the plain answer syntax.

ADR-0005: the page sends `mf.getValue("latex-unstyled")`; this module rewrites its
structure (groups, \\frac, \\sqrt, \\left...\\right, matrices) into plain syntax with
explicit parentheses, and the one Lark grammar then parses it. It decides no math
itself beyond typeset conventions that are unambiguous on screen:
`\\sin x` and `\\sin 2x` take the following run of atoms as the argument, `\\sin^2 x` is
sin(x)^2, `\\sin^{-1}` is arcsin, and a symbol such as `\\pi` next to a letter multiplies.
Unknown commands are errors (a whitelist), never passed through.
"""

import re
from dataclasses import dataclass

from core.grader import errors

MAX_LATEX_CHARS = 2000
MAX_BRACE_DEPTH = 40

_TOKEN = re.compile(r"\\([A-Za-z]+)|\\(.)|(\s+)|(.)", re.DOTALL)

_FUNCS = {
    "sin", "cos", "tan", "sec", "csc", "cot", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "ln", "log", "exp",
}  # fmt: skip
_OPERATOR_NAMES = {"arcsec", "arccsc", "arccot", "sign", "abs", "sgn"}
_GREEK = (
    *("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota"),
    *("kappa", "lambda", "mu", "nu", "xi", "rho", "sigma", "tau", "upsilon", "phi"),
    *("chi", "psi", "omega"),
)
_SYMBOLS = {
    "pi": "pi",
    "exponentialE": "e",
    "imaginaryI": "i",
    "infty": "inf",
    **{g: g for g in _GREEK},
    "varepsilon": "epsilon",
    "vartheta": "theta",
    "varphi": "phi",
}
_PLAIN = {
    "cdot": "*",
    "times": "*",
    "ast": "*",
    "div": "/",
    "cup": " U ",
    "le": "<=",
    "leq": "<=",
    "leqslant": "<=",
    "ge": ">=",
    "geq": ">=",
    "geqslant": ">=",
    "ne": "!=",
    "neq": "!=",
    "lt": "<",
    "gt": ">",
    "lor": " or ",
    "land": " and ",
    "emptyset": " none ",
    "varnothing": " none ",
    "lbrack": "[",
    "rbrack": "]",
    "lbrace": "{",
    "rbrace": "}",
    "langle": "<",
    "rangle": ">",
    "vert": "|",
    "mid": "|",
    "circ": "°",
    "degree": "°",
    "quad": " ",
    "qquad": " ",
}
_IGNORED = {"displaystyle", "textstyle", "scriptstyle", "limits", "nolimits"}
_SPACES = {",", ";", ":", "!", " ", ">"}
_TEXT_CMDS = {"text", "mathrm", "operatorname", "mathit", "textrm", "textit", "mathbf", "textbf"}
_LEFT_RIGHT = {"left", "right", "mleft", "mright", "bigl", "bigr", "Bigl", "Bigr"}
_DELIMS = {
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "lbrack": "[",
    "rbrack": "]",
    "{": "{",
    "}": "}",
    "lbrace": "{",
    "rbrace": "}",
    "langle": "<",
    "rangle": ">",
    ".": "",
}
_BARS = {"|", "vert", "lvert", "rvert"}
_STOP = set("+-=<>,;)]|&") | {"*", "/"}


@dataclass(frozen=True, slots=True)
class _Tok:
    kind: str  # cmd, char
    value: str


def _scan(latex: str) -> list[_Tok]:
    toks: list[_Tok] = []
    for m in _TOKEN.finditer(latex):
        if m.group(1):
            toks.append(_Tok("cmd", m.group(1)))
        elif m.group(2):
            toks.append(_Tok("cmd", m.group(2)))
        elif m.group(4):
            toks.append(_Tok("char", m.group(4)))
    return toks


class _Lowering:
    def __init__(self, toks: list[_Tok]) -> None:
        self.toks = toks
        self.i = 0
        self.depth = 0

    # ------------------------------------------------------------ primitives
    def peek(self, k: int = 0) -> _Tok | None:
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def next(self) -> _Tok:
        tok = self.peek()
        if tok is None:
            raise errors.syntax("The answer ends too early.")
        self.i += 1
        return tok

    def group_tokens(self) -> list[_Tok]:
        """The tokens of a {...} group or of a single token (TeX argument rules)."""
        tok = self.next()
        if tok.kind == "char" and tok.value == "{":
            depth = 1
            start = self.i
            while True:
                t = self.next()
                if t.kind == "char" and t.value == "{":
                    depth += 1
                elif t.kind == "char" and t.value == "}":
                    depth -= 1
                    if depth == 0:
                        return self.toks[start : self.i - 1]
        return [tok]

    def optional_bracket(self) -> list[_Tok] | None:
        tok = self.peek()
        if not (tok and tok.kind == "char" and tok.value == "["):
            return None
        self.i += 1
        start = self.i
        depth = 0
        while True:
            t = self.next()
            if t.kind == "char" and t.value in "{[":
                depth += 1
            elif t.kind == "char" and t.value in "}]":
                if depth == 0 and t.value == "]":
                    return self.toks[start : self.i - 1]
                depth -= 1

    def sub(self, toks: list[_Tok]) -> str:
        self.depth += 1
        if self.depth > MAX_BRACE_DEPTH:
            raise errors.limit(f"Answers can nest at most {MAX_BRACE_DEPTH} levels deep.")
        out = _Lowering(toks)
        out.depth = self.depth
        text = out.run()
        self.depth -= 1
        return text

    # ------------------------------------------------------------ main loop
    def run(self) -> str:
        parts: list[str] = []
        prev = ""  # kind of the last piece: "letters", "symbol", or ""
        while self.peek() is not None:
            piece, kind = self.item()
            if piece is None:
                continue
            # A typeset symbol next to a letter or function multiplies (2πx, x sin x);
            # letter next to letter stays one word, so `xy` gets the usual error.
            if (prev == "symbol" and kind in {"symbol", "letters", "func"}) or (
                prev == "letters" and kind in {"symbol", "func"}
            ):
                parts.append("*")
            parts.append(piece)
            prev = kind
        return "".join(parts)

    def item(self) -> tuple[str | None, str]:
        tok = self.next()
        if tok.kind == "char":
            return self.char(tok.value)
        return self.command(tok.value)

    def char(self, ch: str) -> tuple[str | None, str]:
        if ch == "{":
            self.i -= 1
            return f"({self.sub(self.group_tokens())})", "close"
        if ch == "}":
            raise errors.syntax("Unbalanced braces.")
        if ch == "^":
            return self.superscript(), "close"
        if ch == "_":
            sub = self.sub(self.group_tokens()).strip()
            if not re.fullmatch(r"[A-Za-z0-9]+", sub):
                raise errors.syntax("Subscripts can only be letters or digits, as in x_1.")
            return f"_{sub}", "letters"
        if ch == "~":
            return " ", ""
        if ch == "&":
            raise errors.syntax("Unexpected '&'.")
        if ch.isalpha():
            return ch, "letters"
        if ch.isdigit() or ch == ".":
            return ch, "number"
        return ch, "close" if ch in ")]" else ""

    def superscript(self) -> str:
        arg = self.group_tokens()
        if len(arg) == 1 and arg[0].kind == "cmd" and arg[0].value in {"circ", "degree"}:
            return "°"
        return f"^({self.sub(arg)})"

    def command(self, name: str) -> tuple[str | None, str]:
        if name in _SPACES or name in _IGNORED:
            return None, ""
        if name in {"frac", "dfrac", "tfrac", "cfrac"}:
            before = self.toks[self.i - 2] if self.i >= 2 else None
            if before is not None and before.kind == "char" and before.value.isdigit():
                raise errors.syntax(
                    "Mixed numbers aren't allowed.", "Write 3 + 1/2 or 7/2 instead of 3 1/2."
                )
            num = self.sub(self.group_tokens())
            den = self.sub(self.group_tokens())
            return f"(({num})/({den}))", "close"
        if name == "sqrt":
            index = self.optional_bracket()
            body = self.sub(self.group_tokens())
            if index is not None:
                return f"root({body}, {self.sub(index)})", "close"
            return f"sqrt({body})", "close"
        if name in _LEFT_RIGHT:
            return self.delimiter(name)
        if name in _BARS and name != "|":
            return "|", ""
        if name == "|":
            raise errors.syntax("Use single bars for absolute values.")
        if name in {"{", "}"}:
            return name, ""
        if name in _FUNCS:
            return self.function(name), "func"
        if name in _TEXT_CMDS:
            return self.text(name)
        if name in _SYMBOLS:
            return f" {_SYMBOLS[name]} ", "symbol"
        if name in _PLAIN:
            return _PLAIN[name], ""
        if name == "begin":
            return self.matrix(), "close"
        if name == "placeholder":
            raise errors.syntax("Fill in the empty box.")
        if name in {"pm", "mp"}:
            raise errors.syntax("Write both values separated by a comma instead of ±.")
        raise errors.syntax(f"The symbol \\{name} isn't supported in answers.")

    def text(self, name: str) -> tuple[str | None, str]:
        content = "".join(t.value if t.kind == "char" else " " for t in self.group_tokens())
        word = content.strip()
        if name == "operatorname" and word in _OPERATOR_NAMES | _FUNCS:
            fname = {"sgn": "sign"}.get(word, word)
            return self.function(fname), "func"
        if not word:
            return None, ""
        if not re.fullmatch(r"[A-Za-z ]+", word):
            raise errors.syntax(f"Can't read the text {content!r}.")
        if word in {"or", "and", "U"}:
            return f" {word} ", ""
        return word, "letters"

    def delimiter(self, name: str) -> tuple[str | None, str]:
        tok = self.next()
        value = tok.value
        if tok.kind == "cmd" and value == "|":
            raise errors.syntax("Use single bars for absolute values.")
        if name in {"left", "mleft", "bigl", "Bigl"} and value in _BARS | {"|"}:
            inner = self.until_right()
            return f"abs({inner})", "close"
        if value in _BARS | {"|"}:
            return "|", ""
        if value not in _DELIMS:
            raise errors.syntax(f"Unsupported bracket {value!r}.")
        return _DELIMS[value], "close" if value in {")", "]", "rbrack", "rbrace", "rangle"} else ""

    def until_right(self) -> str:
        """Tokens up to the matching \\right| (for \\left| ... \\right|)."""
        start = self.i
        depth = 0
        while True:
            t = self.next()
            if t.kind == "cmd" and t.value in {"left", "mleft"}:
                depth += 1
            elif t.kind == "cmd" and t.value in {"right", "mright"}:
                if depth == 0:
                    self.next()  # the closing bar
                    return self.sub(self.toks[start : self.i - 2])
                depth -= 1

    def function(self, name: str) -> str:
        power: str | None = None
        base: str | None = None
        while True:
            tok = self.peek()
            if tok and tok.kind == "char" and tok.value == "^" and power is None:
                self.i += 1
                power = self.sub(self.group_tokens()).strip()
            elif tok and tok.kind == "char" and tok.value == "_" and name == "log" and base is None:
                self.i += 1
                base = self.sub(self.group_tokens()).strip()
            else:
                break
        if power is not None and power.replace(" ", "") in {"-1", "(-1)"}:
            if name not in {"sin", "cos", "tan", "sec", "csc", "cot"}:
                raise errors.syntax(f"Can't read {name}^-1.", "Use parentheses.")
            name, power = "arc" + name, None
        arg = self.argument(name)
        fname = f"log_{base}" if base else name
        call = f"{fname}({arg})"
        return f"{call}^({power})" if power is not None else call

    def argument(self, name: str) -> str:
        tok = self.peek()
        if tok is None:
            raise errors.syntax(f"{name} needs an argument.", f"Did you mean {name}(x)?")
        if tok.kind == "cmd" and tok.value in {"left", "mleft", "bigl", "Bigl"}:
            nxt = self.peek(1)
            if nxt is not None and (nxt.value in _BARS or nxt.value == "|"):
                self.i += 2
                return f"abs({self.until_right()})"
            if nxt is not None and nxt.value == "(":
                self.i += 2
                return self.sub(self._until_close("right"))
        if tok.kind == "char" and tok.value == "(":
            self.i += 1
            return self.sub(self._until_close(None))
        if tok.kind == "char" and tok.value == "|":
            # \ln|x| (bars without \left...\right): the bars delimit the argument.
            depth, j = 0, self.i + 1
            while j < len(self.toks):
                bar = self.toks[j]
                if bar.kind == "char" and bar.value == "{":
                    depth += 1
                elif bar.kind == "char" and bar.value == "}":
                    depth -= 1
                elif bar.kind == "char" and bar.value == "|" and depth == 0:
                    break
                j += 1
            if j < len(self.toks) and j > self.i + 1:
                inner = self.toks[self.i + 1 : j]
                self.i = j + 1
                return f"abs({self.sub(inner)})"
        # Typeset convention: \sin x, \sin 2x, \ln x^2 take the following run of atoms.
        start = self.i
        while (t := self.peek()) is not None:
            if t.kind == "char" and (t.value in _STOP or t.value == "("):
                break
            if t.kind == "cmd" and (
                t.value in _FUNCS
                or t.value in _PLAIN
                or t.value in _LEFT_RIGHT
                or t.value in _TEXT_CMDS
                or t.value in {"pm", "mp"}
            ):
                break
            if t.kind == "char" and t.value in "^_":
                self.i += 1
                self.group_tokens()
                continue
            if t.kind == "cmd" and t.value in {"frac", "dfrac", "tfrac", "sqrt"}:
                self.i += 1
                if t.value == "sqrt":
                    self.optional_bracket()
                    self.group_tokens()
                else:
                    self.group_tokens()
                    self.group_tokens()
                continue
            if t.kind == "char" and t.value == "{":
                self.group_tokens()
                continue
            self.i += 1
        run = self.toks[start : self.i]
        if not any((t.kind == "char" and not t.value.isspace()) or t.kind == "cmd" for t in run):
            raise errors.syntax(f"{name} needs parentheses.", f"Did you mean {name}(x)?")
        return self.sub(run)

    def _until_close(self, right: str | None) -> list[_Tok]:
        start = self.i
        depth = 0
        while True:
            t = self.next()
            if right is None:
                if t.kind == "char" and t.value == "(":
                    depth += 1
                elif t.kind == "char" and t.value == ")":
                    if depth == 0:
                        return self.toks[start : self.i - 1]
                    depth -= 1
            elif t.kind == "cmd" and t.value in {"left", "mleft"}:
                depth += 1
            elif t.kind == "cmd" and t.value in {"right", "mright"}:
                if depth == 0:
                    self.next()
                    return self.toks[start : self.i - 2]
                depth -= 1

    def matrix(self) -> str:
        env = "".join(t.value for t in self.group_tokens())
        if env not in {"bmatrix", "pmatrix", "matrix", "Bmatrix", "vmatrix"} or env == "vmatrix":
            raise errors.syntax(f"Unsupported layout {env!r}.")
        start = self.i
        depth = 0
        while True:
            t = self.next()
            if t.kind == "cmd" and t.value == "begin":
                depth += 1
            elif t.kind == "cmd" and t.value == "end":
                if depth == 0:
                    body = self.toks[start : self.i - 1]
                    self.group_tokens()
                    break
                depth -= 1
        rows: list[list[list[_Tok]]] = [[[]]]
        for t in body:
            if t.kind == "cmd" and t.value == "\\":
                rows.append([[]])
            elif t.kind == "char" and t.value == "&":
                rows[-1].append([])
            else:
                rows[-1][-1].append(t)
        if rows and all(not cell for cell in rows[-1]):
            rows.pop()
        texts = [[self.sub(cell) for cell in row] for row in rows]
        return "[" + ", ".join("[" + ", ".join(r) + "]" for r in texts) + "]"


def lower(latex: str) -> str:
    """MathLive LaTeX -> plain answer syntax. Raises InputError (syntax/limit)."""
    if len(latex) > MAX_LATEX_CHARS:
        raise errors.limit("The answer is too long.")
    if not latex.strip():
        raise errors.syntax("Type an answer.")
    return _Lowering(_scan(latex)).run().strip()
