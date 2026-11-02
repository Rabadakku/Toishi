"""Runtime self-check of the pure-Python stack.

Proves the interpreter and every core dependency import and work, which matters
most inside the frozen .app (a missing PyInstaller hook shows up here).
Used by the tests and by `app --self-test`.
"""

import sqlite3
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

type Probe = Callable[[], str]


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    ok: bool
    detail: str
    ms: float


@dataclass(frozen=True, slots=True)
class HealthReport:
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checks": [
                {"name": c.name, "ok": c.ok, "detail": c.detail, "ms": round(c.ms, 1)}
                for c in self.checks
            ],
        }


def _dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unknown"


def _python() -> str:
    found = sys.version.split()[0]
    if sys.version_info[:2] != (3, 14):
        raise RuntimeError(f"expected Python 3.14, running {found}")
    if not sys._is_gil_enabled():
        raise RuntimeError("free-threaded Python is not supported (pywebview #1739)")
    return found


def _sqlite() -> str:
    from core.storage.connection import require_safe_sqlite

    require_safe_sqlite()  # DEV-7: the WAL-reset fix (3.51.3, or the 3.50.7 / 3.44.6 backports)
    with tempfile.TemporaryDirectory() as tmp:
        con = sqlite3.connect(Path(tmp) / "probe.db")
        try:
            mode = con.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if mode != "wal":
                raise RuntimeError(f"journal_mode=WAL gave {mode!r}")
            with con:
                con.execute("CREATE TABLE probe (x INTEGER)")
                con.execute("INSERT INTO probe VALUES (1)")
            (count,) = con.execute("SELECT count(*) FROM probe").fetchone()
            if count != 1:
                raise RuntimeError("write/read round trip failed")
        finally:
            con.close()
    return f"SQLite {sqlite3.sqlite_version}, WAL-reset fix ok, WAL ok"


def _fsrs() -> str:
    from fsrs import Card, Rating, Scheduler

    card, log = Scheduler().review_card(Card(), Rating.Good)
    if card.due <= log.review_datetime:
        raise RuntimeError("a Good review did not schedule the card in the future")
    return f"fsrs {_dist_version('fsrs')}, review ok"


def _sympy() -> str:
    import sympy

    # Objects are built explicitly; strings never go through sympify (ADR-0003).
    x = sympy.Symbol("x")
    if sympy.expand((x + 1) ** 2 - (x**2 + 2 * x + 1)) != 0:
        raise RuntimeError("expand() gave a wrong result")
    return f"SymPy {sympy.__version__}"


def _mpmath() -> str:
    import mpmath

    with mpmath.workdps(30):
        digits = mpmath.nstr(mpmath.pi, 25)
    if not digits.startswith("3.14159265358979323846"):
        raise RuntimeError(f"pi came out as {digits}")
    return f"mpmath {mpmath.__version__}"


def _lark() -> str:
    import lark

    parser = lark.Lark("start: INT\n%import common.INT", parser="lalr")
    tree = parser.parse("42")
    if str(tree.children[0]) != "42":
        raise RuntimeError("tiny grammar did not parse")
    return f"Lark {lark.__version__}"


def _zstandard() -> str:
    import zstandard

    data = b"mastery engine " * 200
    packed = zstandard.ZstdCompressor(level=3).compress(data)
    if zstandard.ZstdDecompressor().decompress(packed) != data:
        raise RuntimeError("round trip changed the data")
    return f"zstandard {zstandard.__version__}, {len(data)} -> {len(packed)} bytes"


def _platformdirs() -> str:
    from core.paths import app_data_dir

    return f"platformdirs {_dist_version('platformdirs')}, data dir {app_data_dir()}"


DEFAULT_PROBES: Mapping[str, Probe] = {
    "python": _python,
    "sqlite": _sqlite,
    "fsrs": _fsrs,
    "sympy": _sympy,
    "mpmath": _mpmath,
    "lark": _lark,
    "zstandard": _zstandard,
    "platformdirs": _platformdirs,
}


def health_check(probes: Mapping[str, Probe] = DEFAULT_PROBES) -> HealthReport:
    """Run every probe; a failing probe is reported, never raised."""
    checks: list[Check] = []
    for name, probe in probes.items():
        start = time.perf_counter()
        try:
            checks.append(Check(name, True, probe(), _ms_since(start)))
        except Exception as error:
            detail = f"{type(error).__name__}: {error}"
            checks.append(Check(name, False, detail, _ms_since(start)))
    return HealthReport(tuple(checks))


def _ms_since(start: float) -> float:
    return (time.perf_counter() - start) * 1000
