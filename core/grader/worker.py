"""The checker's worker process: reused between answers, killed after the hard limit.

SymPy and mpmath work happens here, never in the caller's process, so no answer can
hang the app (MATH-15: hard limit 2 s, then the verdict is undecidable). The worker is
started with the "spawn" method (the macOS default, and safe inside a frozen .app,
where app/main.py must call multiprocessing.freeze_support()). A worker that misses the
deadline is killed and a fresh one starts in the background.
"""

import multiprocessing
import multiprocessing.connection
import os
import threading
import time
from typing import Any

from core.grader.pipeline import Job, JobResult, run_job

HARD_LIMIT_SECONDS = 2.0
STARTUP_SECONDS = 60.0


def _serve(conn: multiprocessing.connection.Connection) -> None:
    import sympy  # noqa: F401 - warm the imports before reporting ready

    conn.send(("ready", os.getpid()))
    while True:
        try:
            message = conn.recv()
        except EOFError:
            return
        kind, job_id, payload = message
        if kind == "stop":
            return
        if kind == "sleep":  # test hook: simulate a hang the soft limits can't stop
            time.sleep(payload)
            continue

        def report(result: JobResult, job_id: int = job_id) -> None:
            conn.send(("prelim", job_id, result))

        try:
            result = run_job(payload, report)
        except Exception as exc:  # report, don't die: the next answer still needs us
            result = JobResult("undecidable", f"checker error: {type(exc).__name__}: {exc}")
        conn.send(("final", job_id, result))


class Worker:
    """A single reusable worker process. Thread-safe: one job at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Any = None
        self._conn: multiprocessing.connection.Connection | None = None
        self._ready = False
        self._job_id = 0
        self.restarts = 0

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        with self._lock:
            self._ensure_started()

    def _ensure_started(self) -> None:
        if self._proc is not None and self._proc.is_alive():
            return
        ctx = multiprocessing.get_context("spawn")
        parent, child = ctx.Pipe()
        proc = ctx.Process(target=_serve, args=(child,), name="answer-checker", daemon=True)
        proc.start()
        child.close()
        self._proc, self._conn, self._ready = proc, parent, False

    def _wait_ready(self) -> bool:
        if self._conn is None:
            return False
        if self._ready:
            return True
        try:
            if not self._conn.poll(STARTUP_SECONDS):
                self._kill()
                return False
            message = self._conn.recv()
        except EOFError, OSError:
            self._kill()
            return False
        self._ready = message[0] == "ready"
        return self._ready

    def _kill(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc.join(5)
        if self._conn is not None:
            self._conn.close()
        self._proc, self._conn, self._ready = None, None, False

    def restart(self) -> None:
        self._kill()
        self.restarts += 1
        self._ensure_started()  # starts importing in the background right away

    def stop(self) -> None:
        with self._lock:
            if self._conn is not None and self._proc is not None and self._proc.is_alive():
                try:
                    self._conn.send(("stop", 0, None))
                    self._proc.join(2)
                except BrokenPipeError, OSError:
                    pass
            self._kill()

    @property
    def pid(self) -> int | None:
        return self._proc.pid if self._proc is not None else None

    # ------------------------------------------------------------------ jobs
    def run(
        self, job: Job | None, *, hard_limit: float = HARD_LIMIT_SECONDS, sleep: float = 0.0
    ) -> tuple[JobResult | None, bool]:
        """Run a job. Returns (result, timed_out); result may be preliminary or None."""
        with self._lock:
            for attempt in range(2):
                self._ensure_started()
                if self._wait_ready():
                    break
                if attempt:
                    return None, False
            if self._conn is None:
                return None, False
            self._job_id += 1
            job_id = self._job_id
            try:
                if job is None:
                    self._conn.send(("sleep", job_id, sleep))
                else:
                    self._conn.send(("job", job_id, job))
            except BrokenPipeError, OSError:
                self.restart()
                return None, False
            end = time.monotonic() + hard_limit
            prelim: JobResult | None = None
            while True:
                left = end - time.monotonic()
                try:
                    if left <= 0 or not self._conn.poll(left):
                        self.restart()
                        return prelim, True
                    kind, got_id, result = self._conn.recv()
                except EOFError, OSError:
                    self.restart()
                    return prelim, False
                if got_id != job_id:
                    continue
                if kind == "final":
                    return result, False
                prelim = result


_WORKER = Worker()


def worker() -> Worker:
    return _WORKER
