"""ADR-0003: nothing typed by the user is ever evaluated as code.

Static guard over our own sources (ruff's S102/S307/TID251 rules say the same):
- Python in core/, app/, scripts/, spike/: no eval/exec/compile/__import__, no
  SymPy string evaluators (sympify, S(...), parse_expr, sympy.parsing, lambdify).
- TypeScript/Svelte in web/src: no eval, new Function, or string timers.
SymPy itself parses some of its own constant strings internally (simplify,
nsimplify, definite integrals), so the rule is about what *we* pass to it:
user text goes through our own parser, never into SymPy as a string.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY_DIRS = ("core", "app", "scripts", "spike")
WEB_SRC = ROOT / "web" / "src"

BANNED_NAMES = {"eval", "exec", "compile", "__import__", "sympify", "parse_expr", "S", "lambdify"}
BANNED_ATTRS = {"sympify", "parse_expr", "lambdify"}
BANNED_MODULES = ("sympy.parsing", "sympy.utilities.lambdify", "sympy.core.sympify")
BUILTINS_ATTRS = {"eval", "exec", "compile", "__import__"}

JS_BANNED = re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(|\bset(?:Timeout|Interval)\s*\(\s*['\"`]")


def python_violations(source: str, filename: str = "<string>") -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(source, filename)):
        where = f"{filename}:{getattr(node, 'lineno', '?')}"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BANNED_NAMES:
                found.append(f"{where} call to {func.id}()")
            elif isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else ""
                if func.attr in BANNED_ATTRS or (owner == "sympy" and func.attr == "S"):
                    found.append(f"{where} call to .{func.attr}()")
                elif owner == "builtins" and func.attr in BUILTINS_ATTRS:
                    found.append(f"{where} call to builtins.{func.attr}()")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(BANNED_MODULES):
                found.append(f"{where} import from {node.module}")
            names = {alias.name for alias in node.names}
            if node.module.startswith("sympy") and names & BANNED_ATTRS:
                found.append(f"{where} imports {sorted(names & BANNED_ATTRS)} from {node.module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(BANNED_MODULES):
                    found.append(f"{where} import {alias.name}")
    return found


def our_python_files() -> list[Path]:
    files = [p for d in PY_DIRS for p in (ROOT / d).rglob("*.py")]
    files += (ROOT / "packaging").rglob("*.spec")
    return sorted(p for p in files if "web_dist" not in p.parts and "build" not in p.parts)


def test_our_python_never_evaluates_strings() -> None:
    files = our_python_files()
    assert any(p.parts[-2:] == ("core", "health.py") for p in files)  # the scan really ran
    problems = [
        v for p in files for v in python_violations(p.read_text(), str(p.relative_to(ROOT)))
    ]
    assert problems == []


def test_our_web_code_never_evaluates_strings() -> None:
    files = [p for p in WEB_SRC.rglob("*") if p.suffix in {".ts", ".svelte", ".js"}]
    assert files
    problems = [
        f"{p.relative_to(ROOT)}: {m.group(0)}"
        for p in files
        for m in JS_BANNED.finditer(p.read_text())
    ]
    assert problems == []


@pytest.mark.parametrize(
    "snippet",
    [
        "eval(user_text)",
        "exec(code)",
        "compile(src, 'x', 'exec')",
        "__import__('os')",
        "import builtins\nbuiltins.eval('1')",
        "import sympy\nsympy.sympify(answer)",
        "import sympy\nsympy.S(answer)",
        "from sympy import S\nS(answer)",
        "from sympy import sympify",
        "from sympy import parse_expr",
        "from sympy.parsing.sympy_parser import parse_expr",
        "from sympy.parsing.latex import parse_latex",
        "import sympy.parsing.mathematica",
        "from sympy import lambdify",
        "import sympy\nsympy.lambdify(x, e)",
    ],
)
def test_guard_catches_python_violations(snippet: str) -> None:
    assert python_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "import re\nre.compile('x')",
        "import sympy\nx = sympy.Symbol('x')\nsympy.expand((x + 1) ** 2)",
        "from sympy import S\nhalf = S.Half",
        "import sympy\nsympy.Rational(1, 2)",
    ],
)
def test_guard_allows_safe_code(snippet: str) -> None:
    assert python_violations(snippet) == []


@pytest.mark.parametrize(
    ("snippet", "banned"),
    [
        ("eval(x)", True),
        ("const f = new Function('a', 'return a')", True),
        ("setTimeout('go()', 10)", True),
        ("setTimeout(() => go(), 10)", False),
        ("retrieval(x)", False),
    ],
)
def test_guard_catches_js_violations(snippet: str, banned: bool) -> None:
    assert bool(JS_BANNED.search(snippet)) is banned
