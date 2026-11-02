"""Symbolic confirmation with a soft time limit (step 4 of the checking pipeline).

Runs in the worker process. A SIGALRM timer interrupts slow SymPy calls so the worker
survives; the parent's hard kill at 2 s (worker.py) is the backstop for anything a
signal can't interrupt. Symbolic results can confirm a numeric match, or prove an exact
nonzero difference, but never overrule a numeric mismatch.
"""

import contextlib
import signal
import threading
import time
from collections.abc import Iterator

import sympy


class SymbolicTimeout(Exception):
    pass


@contextlib.contextmanager
def time_limit(seconds: float) -> Iterator[None]:
    """Raise SymbolicTimeout in the block after `seconds` (main thread on Unix only)."""
    usable = threading.current_thread() is threading.main_thread() and hasattr(signal, "setitimer")
    if seconds <= 0:
        raise SymbolicTimeout
    if not usable:
        yield
        return

    def on_alarm(signum: int, frame: object) -> None:
        raise SymbolicTimeout

    previous = signal.signal(signal.SIGALRM, on_alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class Deadline:
    def __init__(self, seconds: float) -> None:
        self.end = time.monotonic() + seconds

    def left(self) -> float:
        return self.end - time.monotonic()


def zero_status(diff: sympy.Expr, seconds: float) -> bool | None:
    """True: diff is provably 0. False: provably a nonzero number. None: unknown/timeout."""
    try:
        with time_limit(seconds):
            return _zero_status(diff)
    except SymbolicTimeout, RecursionError, TypeError, ValueError, ZeroDivisionError:
        return None
    except Exception:  # SymPy can raise many internal errors; unknown is the safe answer
        return None


def _nonzero_function(value: sympy.Expr) -> bool:
    """A nonzero rational function with exact coefficients differs from 0 almost everywhere."""
    symbols = sorted(value.free_symbols, key=str)
    if not symbols or not value.is_rational_function(*symbols):
        return False
    numer, _ = sympy.fraction(sympy.cancel(value))
    poly = sympy.Poly(numer, *symbols)
    return not poly.is_zero and all(c.is_Rational for c in poly.coeffs())


def _nonzero_number(value: sympy.Expr) -> bool:
    if value.is_Rational:
        return bool(value != 0)
    if value.is_number and not value.free_symbols:
        approx = value.evalf(100)
        return bool(approx.is_Number and abs(approx) > sympy.Float("1e-80", 100))
    return False


def _zero_status(diff: sympy.Expr) -> bool | None:
    if diff == 0:
        return True
    if _nonzero_number(diff):
        return False
    for step in (sympy.expand, sympy.cancel, sympy.simplify):
        value = step(diff)
        if value == 0:
            return True
        if _nonzero_number(value) or _nonzero_function(value):
            return False
    return None
