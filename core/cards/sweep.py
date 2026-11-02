"""Runs template sweeps in their own process, with a hard time limit per instance.

SymPy stays out of the caller's process (as with the grader's worker), and a template
whose computation hangs is killed: the sweep process reports after every parameter
draw, and the caller kills it when a draw takes longer than the 2-second limit plus a
small margin. The process uses the "spawn" start method and is reused between sweeps.
"""

import contextlib
import multiprocessing
import multiprocessing.connection
import threading
from typing import Any

from core.cards.template import SweepResult, TemplateJob

STARTUP_SECONDS = 60.0
MARGIN_SECONDS = 0.5


def _serve(conn: multiprocessing.connection.Connection) -> None:
    from core.cards import cas  # SymPy loads here, in the sweep process only

    conn.send(("ready", None))
    while True:
        try:
            kind, job = conn.recv()
        except EOFError:
            return
        if kind == "stop":
            return

        def report(_kind: str, _payload: Any) -> None:
            conn.send(("tick", None))

        try:
            result = cas.run(job, report)
        except Exception as exc:  # a bug, not the template's fault: report it, stay alive
            result = SweepResult(error=f"template error: {type(exc).__name__}: {exc}")
        conn.send(("done", result))


class SweepRunner:
    """One reusable sweep process. Thread-safe: one sweep at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Any = None
        self._conn: multiprocessing.connection.Connection | None = None
        self.kills = 0

    def _ensure_started(self) -> multiprocessing.connection.Connection:
        if self._proc is not None and self._proc.is_alive() and self._conn is not None:
            return self._conn
        self._kill()
        ctx = multiprocessing.get_context("spawn")
        parent, child = ctx.Pipe()
        proc = ctx.Process(target=_serve, args=(child,), daemon=True, name="mastery-sweep")
        proc.start()
        child.close()
        try:
            if not parent.poll(STARTUP_SECONDS):
                raise RuntimeError("the template sweep process did not start")
            parent.recv()
        except (EOFError, OSError, RuntimeError) as exc:
            proc.kill()
            proc.join(5)
            parent.close()
            raise RuntimeError(f"the template sweep process did not start: {exc}") from None
        self._proc, self._conn = proc, parent
        return parent

    def _kill(self) -> None:
        if self._proc is not None:
            if self._proc.is_alive():
                self._proc.kill()
            self._proc.join(5)
        if self._conn is not None:
            self._conn.close()
        self._proc = None
        self._conn = None

    def start(self) -> None:
        with self._lock:
            self._ensure_started()

    def stop(self) -> None:
        with self._lock:
            if self._conn is not None and self._proc is not None and self._proc.is_alive():
                with contextlib.suppress(OSError):
                    self._conn.send(("stop", None))
            self._kill()

    def run(self, job: TemplateJob) -> SweepResult:
        with self._lock:
            for attempt in range(2):  # a process that died since the last sweep is replaced
                try:
                    conn = self._ensure_started()
                    conn.send(("job", job))
                    break
                except (OSError, RuntimeError) as exc:
                    self._kill()
                    if attempt:
                        return SweepResult(error=str(exc), line=job.first_line)
            limit = job.seconds + MARGIN_SECONDS
            while True:
                if not conn.poll(limit):
                    self._kill()
                    self.kills += 1
                    return SweepResult(
                        error=f"an instance took longer than {job.seconds:g} s",
                        line=job.first_line,
                        combinations=job.combinations(),
                    )
                try:
                    kind, payload = conn.recv()
                except EOFError, OSError:
                    self._kill()
                    return SweepResult(error="the template sweep process died", line=job.first_line)
                if kind == "done" and isinstance(payload, SweepResult):
                    return payload


_RUNNER = SweepRunner()


def runner() -> SweepRunner:
    return _RUNNER


def shutdown() -> None:
    _RUNNER.stop()
