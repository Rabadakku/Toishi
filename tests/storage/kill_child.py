"""The child side of the acknowledged-write kill loop (DEV-8, tests/storage/test_kill_loop.py).

`python -m tests.storage.kill_child` imports the app's core once, then reads one JSON job
per line on stdin and forks a worker for it, so each of the hundreds of rounds starts in
milliseconds. The worker runs in its own process group (the test kills the group, with any
process it started) and writes, with single atomic writes to stdout:

    begin {"step": ..., "now": ...}     before each step
    ack {"step": ..., ...}              after the step returned: it is acknowledged
    error <traceback>                   an unexpected exception (the worker then exits)

and this process writes `forked <pid>` and, once the worker is dead, `exit <pid> <status>`.

Jobs: {"job": "study", "root", "pack", "seed", "start_ms"} answers problems through the
real StudyService (right, wrong, unsure, after a hint, give up, continue, undo, end);
{"job": "import", "root", "seed", "start_ms", "decks"} backs up and imports Anki fixture
decks (read, plan, apply, the engine hook) one after another; {"job": "migrate", "root",
"start_ms"} opens a schema-v1 profile, which backs it up and migrates it.
"""

import json
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from core.importers.anki import (
    apply_anki_import,
    plan_anki_import,
    read_anki_file,
    recompute_memory,
)
from core.queue import QueueError, StudyService
from core.storage import Storage
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths
from tests.storage.study_driver import How, answer, key_checker

NY = ZoneInfo("America/New_York")
HOWS: list[How] = ["right", "right", "right", "wrong", "wrong", "unsure", "hint", "give-up"]


def say(kind: str, payload: dict[str, Any]) -> None:
    os.write(1, f"{kind} {json.dumps(payload, sort_keys=True)}\n".encode())


def attempts(storage: Storage) -> dict[int, bool]:
    """Every attempt id, and whether it is voided."""
    with storage.db.reading() as conn:
        return {
            int(r[0]): r[1] is not None for r in conn.execute("SELECT id, voided_by FROM attempt")
        }


def screen(storage: Storage) -> tuple[int | None, str | None, str | None, str | None]:
    """The open session, the item on screen, its presentation id and, when its answer is
    saved but not graded yet, that presentation id again (pending)."""
    session = storage.users.latest_open_session()
    if session is None or session.current is None:
        return (None if session is None else session.id), None, None, None
    cur = session.current
    shown = cur.get("presentation_id")
    shown = None if shown is None else str(shown)
    return session.id, str(cur.get("key")), shown, shown if cur.get("pending") else None


# ---------------------------------------------------------------- study


def study(job: dict[str, Any]) -> None:
    rng = random.Random(job["seed"])  # noqa: S311 -- reproducible, not crypto
    clock = FixedClock(int(job["start_ms"]), tz=NY)
    paths = ProfilePaths(Path(job["root"]))
    say("begin", {"step": "open", "now": clock.now_ms()})
    storage = Storage.open(paths, pack_paths=[Path(job["pack"])], clock=clock)
    svc = StudyService(storage, checker=key_checker)
    say("ack", {"step": "open", "now": clock.now_ms()})
    while True:
        clock.advance(seconds=rng.randint(5, 90))
        session_id, key, shown, pending = screen(storage)
        turn = None
        if session_id is not None and key is not None:
            turn = _quiet(svc.current)
        problem = turn.problem if turn is not None else None
        closed = turn is not None and turn.result is not None and pending is None  # rated
        roll = rng.random()
        if session_id is None:
            step = "start"
        elif problem is None:
            step = "end"
        elif pending is not None or closed or problem.kind == "example":
            step = "undo" if roll < 0.15 else "end" if roll < 0.2 else "next"
        else:
            step = "undo" if roll < 0.08 else "end" if roll < 0.1 else "answer"
        how = rng.choice(HOWS)
        before = attempts(storage)
        say("begin", {"step": step, "how": how, "now": clock.now_ms()})
        result: Any = None
        if step == "start":
            result = _quiet(lambda: svc.start({"mode": "daily"}))
            if result is None or result.type != "problem":
                clock.advance(days=1)  # nothing left today: come back tomorrow
        elif step == "answer":
            assert turn is not None
            result = _quiet(lambda t=turn, h=how: answer(svc, storage, t, h))
        elif step == "next":
            result = _quiet(svc.next)
        elif step == "undo":
            result = _quiet(svc.undo)
        else:
            result = _quiet(svc.end)
        # What the student was told: this answer was taken (the verdict on screen), or
        # undone. Known from the service's replies, not from reading the file back.
        answered = shown if step == "answer" and result is not None else None
        undid = (
            pending
            if step == "undo" and (getattr(result, "message", "") or "").startswith("Undone")
            else None
        )
        after = attempts(storage)
        session_id, key, _shown, pending = screen(storage)
        say(
            "ack",
            {
                "step": step,
                "now": clock.now_ms(),
                "new": sorted(set(after) - set(before)),
                "voided": sorted(i for i, v in after.items() if v and not before.get(i, False)),
                "answered": answered,
                "undid": undid,
                "session": session_id,
                "key": key,
                "pending": pending,
                "refused": result is None,
            },
        )


def _quiet(action: Any) -> Any:
    try:
        return action()
    except QueueError:
        return None


# ---------------------------------------------------------------- import


def anki_import(job: dict[str, Any]) -> None:
    rng = random.Random(job["seed"])  # noqa: S311
    clock = FixedClock(int(job["start_ms"]), tz=NY)
    paths = ProfilePaths(Path(job["root"]))
    decks = [Path(d) for d in job["decks"]]
    rng.shuffle(decks)
    say("begin", {"step": "open", "now": clock.now_ms()})
    storage = Storage.open(paths, clock=clock)
    say("ack", {"step": "open", "now": clock.now_ms()})
    for deck in decks:
        clock.advance(minutes=1)
        say("begin", {"step": "backup", "deck": deck.name, "now": clock.now_ms()})
        backup = storage.backup_before("pre-import")
        say("ack", {"step": "backup", "deck": deck.name, "backup": backup.path.name})
        data = read_anki_file(deck)
        plan = plan_anki_import(storage.users, data)
        say("begin", {"step": "apply", "deck": deck.name, "now": clock.now_ms()})
        result = apply_anki_import(storage.users, plan)
        record = result.record
        say("ack", {"step": "apply", "deck": deck.name, "record": record.id if record else None})
        say("begin", {"step": "hook", "deck": deck.name, "now": clock.now_ms()})
        recompute_memory(storage, record)
        say("ack", {"step": "hook", "deck": deck.name})
    say("ack", {"step": "done"})
    storage.close(backup=False)
    linger(job)


# ---------------------------------------------------------------- migration


def migrate(job: dict[str, Any]) -> None:
    clock = FixedClock(int(job["start_ms"]), tz=NY)
    say("begin", {"step": "migrate", "now": clock.now_ms(), "t": time.monotonic()})
    storage = Storage.open(ProfilePaths(Path(job["root"])), clock=clock)
    say("ack", {"step": "migrate", "t": time.monotonic()})
    storage.close(backup=False)
    linger(job)


def linger(job: dict[str, Any]) -> None:
    """A job that will be killed waits for it, so the kill always finds it."""
    while job.get("linger"):
        time.sleep(1)


JOBS = {"study": study, "import": anki_import, "migrate": migrate}


def worker(job: dict[str, Any], go: int) -> None:
    os.setsid()  # its own process group: the test kills it with everything it started
    os.read(go, 1)  # wait until "forked <pid>" is out, so it comes first
    try:
        JOBS[job["job"]](job)
        code = 0
    except BaseException:
        os.write(1, ("error " + traceback.format_exc().replace("\n", " | ") + "\n").encode())
        code = 70
    os._exit(code)


def serve() -> None:
    for line in sys.stdin:
        job = json.loads(line)
        sys.stdout.flush()
        go, ready = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(ready)
            worker(job, go)
        os.close(go)
        os.write(1, f"forked {pid}\n".encode())
        os.write(ready, b"!")
        os.close(ready)
        _, status = os.waitpid(pid, 0)
        os.write(1, f"exit {pid} {status}\n".encode())


if __name__ == "__main__":
    serve()
