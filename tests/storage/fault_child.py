"""Child process for tests/storage/test_fault_injection.py. It writes through the real
storage code, reports each commit on stdout ("ok <attempt id>"), and dies abruptly where
the test asks: os._exit skips every exit handler, like Cmd+Q or a crash.

    python -m tests.storage.fault_child <mode> <profile dir> [extra]

The vN-* modes run the real migration step to vN (v2: v1 -> v2, v3: v2 -> v3) through
Storage.open (backup hook first) on a user.db the test put there. SQLite's progress handler,
set on the migration connection inside the step and called at every VM instruction (SQLite
restarts its own countdown at each statement, so the count is kept here), counts the step's
instructions (vN-count), kills the process at instruction n (vN-die n), or slows the step
down for a SIGKILL from outside (vN-slow).
"""

import os
import sqlite3
import sys
import time
from dataclasses import replace
from pathlib import Path

from core.model import Attempt, CardUser, GradedAnswer, ReviewEvent, SkillState
from core.storage import Database, Storage
from core.storage.profiles import ProfilePaths
from core.storage.schema import MIGRATIONS, Migration

SKILL = "calc1.s"


def answer(n: int) -> GradedAnswer:
    """The n-th answer: every row it writes carries n, so consistency is checkable."""
    return GradedAnswer(
        attempt=Attempt(card_id=f"card.{n}", skill_id=SKILL, verdict="correct", rating=3),
        changes=(
            SkillState(skill_id=SKILL, reps=n, stability=float(n), fsrs_state=2),
            CardUser(card_id="card", times_seen=n),
        ),
        reviews=(ReviewEvent(target_kind="skill", target_id=SKILL, rating=3, rules_version="r1"),),
    )


def say(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def commit_some(storage: Storage, count: int) -> int:
    done = storage.users.counts()["attempts"] or 0
    for n in range(done + 1, done + count + 1):
        stored = storage.users.record_answer(answer(n))
        say(f"ok {stored.id}")
    return done + count


def migrate_step(mode: str, paths: ProfilePaths, args: list[str]) -> None:
    version, _, how = mode.partition("-")
    real = MIGRATIONS[int(version.removeprefix("v")) - 1]
    die_at = int(args[0]) if how == "die" else 0
    ticks = [0]

    def tick() -> int:
        ticks[0] += 1
        if ticks[0] == die_at:
            os._exit(9)
        if how == "slow":
            time.sleep(0.0002)
        return 0

    def watched(conn: sqlite3.Connection) -> None:
        if how == "slow":
            say("migrating")
        conn.set_progress_handler(tick, 1)
        real.apply(conn)

    def unwatched(step: Migration) -> Migration:
        """The step after the watched one: the count ends where it begins, so it covers the
        watched step through its commit and nothing of the next step."""

        def apply(conn: sqlite3.Connection) -> None:
            conn.set_progress_handler(None, 1)
            step.apply(conn)

        return replace(step, apply=apply)

    index = real.version - 1
    later = [unwatched(m) if i == 0 else m for i, m in enumerate(MIGRATIONS[index + 1 :])]
    steps = (*MIGRATIONS[:index], replace(real, apply=watched), *later)
    real_open = Database.open

    def open_watched(path: Path, **kwargs: object) -> Database:
        return real_open(path, migrations=steps, **kwargs)  # type: ignore[arg-type]

    Database.open = open_watched  # type: ignore[method-assign]
    storage = Storage.open(paths)
    say(f"done {ticks[0]}")
    storage.close(backup=False)


def main() -> None:
    mode, root = sys.argv[1], Path(sys.argv[2])
    paths = ProfilePaths(root)
    if mode.startswith(("v2-", "v3-")):
        migrate_step(mode, paths, sys.argv[3:])
        return
    storage = Storage.open(paths, create=not paths.user_db.exists())
    say("ready")
    if mode == "loop":
        commit_some(storage, 10**9)
    elif mode == "mid-transaction":
        done = commit_some(storage, 5)

        def half_then_die(conn):
            storage.users._record(conn, answer(done + 1))  # the whole answer, uncommitted
            conn.execute("INSERT INTO setting VALUES ('half', '1', 0)")
            say("dying")
            os._exit(9)

        storage.db.write(half_then_die)
    elif mode == "after-commit":
        commit_some(storage, 3)
        os._exit(9)
    elif mode == "mid-backup":
        commit_some(storage, 2)
        real = Path.replace

        def die_on_rename(self: Path, target):
            if str(self).endswith(".db.tmp"):
                say("dying")
                os._exit(9)
            return real(self, target)

        Path.replace = die_on_rename  # type: ignore[method-assign]
        storage.backups.create("manual")
    elif mode == "mid-migration":
        commit_some(storage, 4)
        storage.close(backup=False)

        def step_then_die(conn):
            conn.execute("ALTER TABLE setting ADD COLUMN extra INTEGER")
            conn.execute("UPDATE skill_state SET reps = 999")
            say("dying")
            os._exit(9)

        steps = (*MIGRATIONS, Migration(len(MIGRATIONS) + 1, "dies", step_then_die))
        Database.open(
            paths.user_db,
            migrations=steps,
            target_version=len(steps),
            before_migration=lambda _a, _b: storage.backups.create("pre-migration"),
        )
    elif mode == "mid-restore":
        commit_some(storage, 2)
        backup = storage.backups.create("manual")
        commit_some(storage, 2)
        storage.close(backup=False)
        real = Path.replace

        def die_on_swap(self: Path, target):
            if Path(target).name == "user.db" and str(self).endswith(".incoming"):
                say("dying")
                os._exit(9)
            return real(self, target)

        Path.replace = die_on_swap  # type: ignore[method-assign]
        storage.backups.restore(backup)
    elif mode == "sleep":
        commit_some(storage, 1)
        time.sleep(60)
    else:
        raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    main()
