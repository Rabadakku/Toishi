"""core/plan is pure: no storage, no clock reads, no I/O, randomness only through a passed-in
random.Random (the brief for design 4; wave 2 passes storage values in)."""

import ast
from pathlib import Path

PLAN = Path(__file__).resolve().parents[2] / "core" / "plan"
FORBIDDEN_MODULES = {
    "sqlite3",
    "time",
    "os",
    "pathlib",
    "socket",
    "subprocess",
    "threading",
    "core.storage",
    "core.engine",
    "core.queue",
    "app",
}
FORBIDDEN_CALLS = {
    ("date", "today"),
    ("datetime", "now"),
    ("datetime", "today"),
    ("datetime", "utcnow"),
    ("random", "random"),
    ("random", "choice"),
    ("random", "shuffle"),
    ("random", "seed"),
}


def _modules(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_plan_modules_import_no_storage_clock_or_io() -> None:
    files = sorted(PLAN.glob("*.py"))
    assert files
    for f in files:
        tree = ast.parse(f.read_text())
        for mod in _modules(tree):
            banned = {m for m in FORBIDDEN_MODULES if mod == m or mod.startswith(m + ".")}
            assert not banned, f"{f.name} imports {mod}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                if isinstance(owner, ast.Name):
                    assert (owner.id, node.func.attr) not in FORBIDDEN_CALLS, (
                        f"{f.name}:{node.lineno} calls {owner.id}.{node.func.attr}"
                    )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in ("open", "print", "input"), f"{f.name}:{node.lineno}"
