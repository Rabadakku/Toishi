"""Tokenizer for the plain-text answer syntax (docs/card-format.md, "Answer types").

Our own scanner, not Lark's, because the meaning of a word depends on the card (its
variables) and because the friendly errors live here: `sinx` ("Did you mean sin(x)?"),
`xy` ("two letters never multiply"), `x2`, `3 1/2`. It also decides which `|` opens
or closes an absolute value and which `<` `>` are vector brackets, so the grammar
stays LALR(1). The Lark parser (parser.py) consumes the token list.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from core.grader import errors

MAX_CHARS = 400  # MATH-10
MAX_DEPTH = 40  # MATH-10: nesting of brackets, bars and function calls
MAX_CARETS = 12  # power towers
MAX_SIGNS_IN_A_ROW = 3

FUNCTIONS: dict[str, str] = {
    **{f: f for f in ("sin", "cos", "tan", "sec", "csc", "cot", "sinh", "cosh", "tanh")},
    **{f: f for f in ("ln", "log", "exp", "sqrt", "root", "abs", "sign")},
    **{f"arc{f}": f"arc{f}" for f in ("sin", "cos", "tan", "sec", "csc", "cot")},
    **{f"a{f}": f"arc{f}" for f in ("sin", "cos", "tan", "sec", "csc", "cot")},
}
CONSTANT_WORDS = {"pi": "pi", "e": "e", "inf": "inf", "infinity": "inf", "oo": "inf"}
GREEK = frozenset(
    [
        *("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota"),
        *("kappa", "lambda", "mu", "nu", "xi", "omicron", "rho", "sigma", "tau"),
        *("upsilon", "phi", "chi", "psi", "omega"),
    ]
)
RESERVED = frozenset({"e", "U"})

# Unicode the student may paste or the math keyboard may produce.
_CHAR_MAP = {
    "\u2212": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u00d7": "*",
    "\u00b7": "*",
    "\u22c5": "*",
    "\u2219": "*",
    "\u00f7": "/",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u221e": " inf ",
    "\u03c0": " pi ",
    "\u222a": " U ",
    "\u2205": " none ",
    "\u27e8": "<",
    "\u2329": "<",
    "\u27e9": ">",
    "\u232a": ">",
    "\u2223": "|",
    "\u221a": "sqrt",
    "\t": " ",
    "\n": " ",
    "\r": " ",
}
_GREEK_CHARS = {
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b3": "gamma",
    "\u03b4": "delta",
    "\u03b5": "epsilon",
    "\u03b8": "theta",
    "\u03bb": "lambda",
    "\u03bc": "mu",
    "\u03c1": "rho",
    "\u03c3": "sigma",
    "\u03c4": "tau",
    "\u03c6": "phi",
    "\u03c9": "omega",
}
_SUPERSCRIPTS = dict(
    zip(
        "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b",
        "0123456789-",
        strict=True,
    )
)
_ALLOWED = re.compile(r"[A-Za-z0-9 .+\-*/^()\[\]{},;|<>=!_°]*")

# E-notation (ADR-0019 item 11): `6.02e23`, `1.2e4`, `1.6e-19`, `3E-5`. A lowercase e with
# a whole-number mantissa and a signed exponent keeps its old reading, because e is Euler's
# number: `2e-1` is 2e - 1 (write 2E-1 for 0.2). Every other form was a syntax error before.
_E_NOTATION = r"(?:\d+(?:\.\d+)?|\.\d+)[eE]\d+|(?:\d*\.\d+)[eE][-+]\d+|\d+E[-+]\d+"
_PLAIN_NUMBER = re.compile(r"\d+(?:\.\d+)?|\.\d+")
MAX_E_EXPONENT = 1000  # as for powers (parser.MAX_EXPONENT)
_SCAN = re.compile(
    r"(?P<space>\s+)"
    rf"|(?P<number>(?:{_E_NOTATION})(?![A-Za-z0-9_.])|\d+(?:\.\d+)?|\.\d+)"
    r"|(?P<word>[A-Za-z]+(?:_[A-Za-z0-9]+)?)"
    r"|(?P<op>\*\*|<=|>=|!=|[-+*/^()\[\]{},;|<>=°])"
)
_OPS = {
    "**": "CARET",
    "<=": "LE",
    ">=": "GE",
    "!=": "NE",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "^": "CARET",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACK",
    "]": "RBRACK",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ";": "SEMI",
    "=": "EQ",
    "<": "LT",
    ">": "GT",
    "°": "DEGREE",
}
# Tokens that end an operand / start one: implicit multiplication happens between them.
_ENDS = {"NUMBER", "VAR", "CONST", "RPAREN", "ABS_CLOSE", "DEGREE"}
_STARTS = {"NUMBER", "VAR", "CONST", "FUNC", "LPAREN", "ABS_OPEN"}
_OPENERS = {"LPAREN", "LBRACK", "LBRACE", "ABS_OPEN", "LANGLE"}
_CLOSERS = {"RPAREN", "RBRACK", "RBRACE", "ABS_CLOSE", "RANGLE"}
_ARG_STOP = {"PLUS", "MINUS", "EQ", "LT", "LE", "GT", "GE", "NE", "COMMA", "SEMI", "FUNC"}


@dataclass(frozen=True, slots=True)
class Vocabulary:
    """What words mean for one card.

    `variables`: the card's symbols. `open_vars`: key mode, where any single letter,
    Greek name or subscripted letter is a variable (used to discover the key's symbols).
    `imaginary`: `i` is the imaginary unit (only when the card says so, MATH-9).
    """

    variables: frozenset[str] = frozenset()
    open_vars: bool = False
    imaginary: bool = False


@dataclass(frozen=True, slots=True)
class Tok:
    type: str
    value: str
    pos: int  # character offset in the normalized text
    end: int


@dataclass(slots=True)
class Tokens:
    text: str  # normalized text the positions refer to
    toks: list[Tok] = field(default_factory=list)

    def source(self, start: int, end: int) -> str:
        """The text of toks[start:end]."""
        if start >= end:
            return ""
        return self.text[self.toks[start].pos : self.toks[end - 1].end].strip()


def is_variable_name(word: str) -> bool:
    base, _, sub = word.partition("_")
    if sub and not re.fullmatch(r"[A-Za-z0-9]+", sub):
        return False
    return (len(base) == 1 and base.isalpha()) or base in GREEK


def normalize(raw: str, max_chars: int = MAX_CHARS) -> str:
    if len(raw) > max_chars:
        raise errors.limit(f"Answers are limited to {MAX_CHARS} characters.")
    if "\x00" in raw:  # NUL is the placeholder that carries ° through NFKC below
        raise errors.syntax("The character '\\x00' isn't part of the answer syntax.")
    out: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch in _SUPERSCRIPTS:
            j = i
            while j < len(raw) and raw[j] in _SUPERSCRIPTS:
                j += 1
            out.append("^(" + "".join(_SUPERSCRIPTS[c] for c in raw[i:j]) + ")")
            i = j
            continue
        out.append(_CHAR_MAP.get(ch) or (f" {_GREEK_CHARS[ch]} " if ch in _GREEK_CHARS else ch))
        i += 1
    text = unicodedata.normalize("NFKC", "".join(out).replace("°", "\x00")).replace("\x00", "°")
    if len(text) > 2 * max_chars:
        raise errors.limit(f"Answers are limited to {MAX_CHARS} characters.")
    if not _ALLOWED.fullmatch(text):
        bad = next(c for c in text if not _ALLOWED.fullmatch(c))
        raise errors.syntax(f"The character {bad!r} isn't part of the answer syntax.")
    return text


def tokenize(raw: str, vocab: Vocabulary, max_chars: int = MAX_CHARS) -> Tokens:
    text = normalize(raw, max_chars)
    result = Tokens(text)
    toks = result.toks
    pos = 0
    while pos < len(text):
        m = _SCAN.match(text, pos)
        if m is None:
            raise errors.syntax(f"Unexpected {text[pos]!r} at position {pos + 1}.")
        kind = m.lastgroup
        value = m.group()
        if kind == "number":
            if "E" in value and "E" in vocab.variables:  # a card variable E: 2E-3 is 2E - 3
                m = _PLAIN_NUMBER.match(text, pos) or m
                value = m.group()
            _check_number(value, text, m.end())
            toks.append(Tok("NUMBER", _canonical_number(value), m.start(), m.end()))
        elif kind == "word":
            toks.append(_word(value, m.start(), m.end(), text, vocab))
        elif kind == "op":
            toks.append(Tok(_OPS.get(value, "BAR"), value, m.start(), m.end()))
        pos = m.end()
    if not toks:
        raise errors.syntax("Type an answer.")
    _assign_bars_and_angles(toks)
    _check_structure(result)
    return result


def _canonical_number(value: str) -> str:
    """`1.2e4` -> `1.2E4`: e-notation is stored with a capital E, which reads back the same."""
    mantissa, e, exponent = value.lower().partition("e")
    return f"{mantissa}E{int(exponent)}" if e else value


def _check_number(value: str, text: str, end: int) -> None:
    mantissa, _, exponent = value.lower().partition("e")
    if exponent and abs(int(exponent)) > MAX_E_EXPONENT:
        raise errors.limit(f"Exponents are limited to {MAX_E_EXPONENT}.")
    whole = mantissa.split(".")[0]
    if len(whole) > 1 and whole.startswith("0"):
        raise errors.syntax(
            f"Write {value} without leading zeros.",
            "Don't use commas inside numbers: 1,000 reads as two numbers.",
        )
    if end < len(text) and text[end] == ".":
        raise errors.syntax(f"Unexpected '.' after {value}.", "Write decimals like 2.5 or 0.5.")


def _word(word: str, start: int, end: int, text: str, vocab: Vocabulary) -> Tok:
    base, _, sub = word.partition("_")
    lower = word.lower()
    if sub and base == "log":
        if sub == "e":
            return Tok("FUNC", "ln", start, end)
        if sub.isdigit() or sub in vocab.variables or (vocab.open_vars and len(sub) == 1):
            if sub.isdigit() and (sub.startswith("0") or int(sub) < 2):
                raise errors.syntax(f"log_{sub} isn't a valid logarithm base.")
            return Tok("FUNC", word, start, end)
        raise errors.syntax(
            f"Can't read {word!r}.", f"Did you mean log_{sub[:1]}({sub[1:] or 'x'})?"
        )
    if word in FUNCTIONS:
        return Tok("FUNC", FUNCTIONS[word], start, end)
    if word in CONSTANT_WORDS:
        return Tok("CONST", CONSTANT_WORDS[word], start, end)
    if lower == "dne":
        return Tok("DNE", "DNE", start, end)
    if lower in {"none", "empty"}:
        return Tok("NONE", "none", start, end)
    if word in {"or", "and"}:
        return Tok(word.upper(), word, start, end)
    if word == "U":
        return Tok("UNION", "U", start, end)
    if word == "i" and vocab.imaginary:
        return Tok("CONST", "i", start, end)
    if word in vocab.variables:
        return Tok("VAR", word, start, end)
    if vocab.open_vars and word not in RESERVED and is_variable_name(word):
        return Tok("VAR", word, start, end)
    raise _unknown_word(word, text, end, vocab)


def _known_piece(piece: str, vocab: Vocabulary) -> bool:
    return (
        piece in vocab.variables
        or piece in CONSTANT_WORDS
        or (vocab.open_vars and is_variable_name(piece) and piece not in RESERVED)
        or (piece == "i" and vocab.imaginary)
    )


def _split_letters(word: str, vocab: Vocabulary) -> list[str] | None:
    """Split a run of letters into known names (variables, constants), longest first."""
    if not word:
        return []
    for size in range(len(word), 0, -1):
        piece = word[:size]
        if _known_piece(piece, vocab):
            rest = _split_letters(word[size:], vocab)
            if rest is not None:
                return [piece, *rest]
    return None


def _unknown_word(word: str, text: str, end: int, vocab: Vocabulary) -> errors.InputError:
    followed_by_paren = text[end:].lstrip().startswith("(")
    base = word.split("_")[0]
    for fname in sorted(FUNCTIONS, key=len, reverse=True):
        if base.startswith(fname) and len(base) > len(fname):
            rest = base[len(fname) :]
            pieces = _split_letters(rest, vocab)
            arg = "*".join(pieces) if pieces else rest
            return errors.syntax(
                f"Can't read {word!r}.",
                f"Did you mean {FUNCTIONS[fname]}({arg})?",
            )
        if base.endswith(fname) and len(base) > len(fname) and followed_by_paren:
            pieces = _split_letters(base[: -len(fname)], vocab)
            if pieces:
                return errors.syntax(
                    f"Can't read {word!r}.",
                    f"Did you mean {'*'.join(pieces)}*{FUNCTIONS[fname]}(...)?",
                )
    loose = Vocabulary(vocab.variables, open_vars=True, imaginary=vocab.imaginary)
    pieces = _split_letters(base, loose) if base.isalpha() else None
    if pieces and len(pieces) > 1:
        return errors.syntax(
            f"Can't read {word!r}: two letters never multiply.",
            f"Write {'*'.join(pieces)}.",
        )
    if vocab.variables and not vocab.open_vars and is_variable_name(word):
        names = ", ".join(sorted(vocab.variables))
        hint = f"This answer uses {names}." if names else "This answer has no variables."
        if word == "i":
            hint = "i isn't the imaginary unit on this card. " + hint
        return errors.syntax(f"{word} isn't a variable in this problem.", hint)
    if not vocab.variables and not vocab.open_vars and is_variable_name(word):
        return errors.syntax(f"{word} isn't a variable in this problem.", "Give a number.")
    return errors.syntax(f"Unknown name {word!r}.")


def _assign_bars_and_angles(toks: list[Tok]) -> None:
    """Decide which `|` open/close an absolute value and which `<` `>` are vector brackets."""
    bars = 0
    angles = 0
    for k, tok in enumerate(toks):
        prev = toks[k - 1].type if k else None
        if tok.type == "BAR":
            closes = bars > 0 and prev in _ENDS
            toks[k] = Tok("ABS_CLOSE" if closes else "ABS_OPEN", "|", tok.pos, tok.end)
            bars += -1 if closes else 1
        elif tok.type == "LT" and prev in {None, "COMMA", "SEMI"}:
            toks[k] = Tok("LANGLE", "<", tok.pos, tok.end)
            angles += 1
        elif tok.type == "GT" and angles > 0:
            toks[k] = Tok("RANGLE", ">", tok.pos, tok.end)
            angles -= 1


def _check_structure(result: Tokens) -> None:
    toks = result.toks
    depth = 0
    carets = 0
    signs = 0
    for k, tok in enumerate(toks):
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if tok.type in _OPENERS:
            depth += 1
            if depth > MAX_DEPTH:
                raise errors.limit(f"Answers can nest at most {MAX_DEPTH} levels deep.")
        elif tok.type in _CLOSERS:
            depth -= 1
        elif tok.type == "CARET":
            carets += 1
            if carets > MAX_CARETS:
                raise errors.limit(f"Answers can have at most {MAX_CARETS} powers.")
        signs = signs + 1 if tok.type in {"PLUS", "MINUS"} else 0
        if signs > MAX_SIGNS_IN_A_ROW:
            raise errors.syntax("Too many + and - signs in a row.")
        if tok.type == "FUNC":
            _check_call(result, k)
        if nxt is not None and tok.type in _ENDS and nxt.type in _STARTS:
            _check_implicit(result, k)


def _following_arg(result: Tokens, start: int) -> str:
    """The text a student probably meant as a function argument (for hints)."""
    toks = result.toks
    end = start
    depth = 0
    while end < len(toks):
        t = toks[end].type
        if depth == 0 and (t in _ARG_STOP or t in _CLOSERS):
            break
        depth += t in _OPENERS
        depth -= t in _CLOSERS
        end += 1
    return result.source(start, end) or "x"


def _check_call(result: Tokens, k: int) -> None:
    toks = result.toks
    name = toks[k].value
    nxt = toks[k + 1] if k + 1 < len(toks) else None
    if nxt is not None and nxt.type == "LPAREN":
        return
    if nxt is not None and nxt.type == "ABS_OPEN" and name not in {"root", "sqrt"}:
        # ln|x| is standard; ln|x|^2 is ambiguous, so ask for parentheses.
        depth = 0
        for j in range(k + 1, len(toks)):
            depth += toks[j].type in _OPENERS
            depth -= toks[j].type in _CLOSERS
            if depth == 0:
                if j + 1 < len(toks) and toks[j + 1].type == "CARET":
                    inner = result.source(k + 2, j)
                    raise errors.syntax(
                        f"Can't tell what {name}|{inner}|^... means.",
                        f"Write {name}(|{inner}|^2) or {name}(|{inner}|)^2.",
                    )
                break
        return
    if nxt is not None and nxt.type == "CARET":
        exp_tok = toks[k + 2] if k + 2 < len(toks) else None
        after = toks[k + 3] if k + 3 < len(toks) else None
        if exp_tok is not None and exp_tok.type == "MINUS" and after and after.value == "1":
            inverse = "arc" + name if name in {"sin", "cos", "tan", "sec", "csc", "cot"} else None
            hint = f"Write {inverse}(x) for the inverse." if inverse else "Use parentheses."
            raise errors.syntax(f"Can't read {name}^-1.", hint)
        power = exp_tok.value if exp_tok is not None else "2"
        raise errors.syntax(
            f"Can't read {name}^{power}(...).",
            f"Write {name}(x)^{power} for the power of {name}.",
        )
    arg = _following_arg(result, k + 1) if nxt is not None else "x"
    raise errors.syntax(f"{name} needs parentheses.", f"Did you mean {name}({arg})?")


def _check_implicit(result: Tokens, k: int) -> None:
    """Implicit multiplication only after a number or next to parentheses."""
    left, right = result.toks[k], result.toks[k + 1]
    if right.type == "NUMBER":
        if left.type == "NUMBER":
            raise errors.syntax(
                f"Two numbers in a row: {left.value} {right.value}.",
                "Mixed numbers aren't allowed: write 3 + 1/2 or 7/2.",
            )
        if left.type == "VAR":
            raise errors.syntax(
                f"A number can't follow {left.value} without an operator.",
                f"Write {right.value}{left.value}, {left.value}*{right.value}"
                f" or {left.value}^{right.value}.",
            )
        raise errors.syntax(
            f"A number can't follow {left.value!r} without an operator.",
            f"Put * before {right.value}.",
        )
    if left.type in {"NUMBER", "RPAREN", "ABS_CLOSE"} or right.type in {"LPAREN", "ABS_OPEN"}:
        return
    if left.type == "DEGREE":
        raise errors.syntax("Put * after the degree mark.")
    raise errors.syntax(
        f"Can't read {left.value} {right.value}: two letters never multiply.",
        f"Write {left.value}*{right.value}" + ("(...)." if right.type == "FUNC" else "."),
    )
