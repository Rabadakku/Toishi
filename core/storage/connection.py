"""Connections to one profile's user.db: a single writer thread and per-thread readers.

- Writes (ARC-6): every write is a job run on one dedicated writer thread that owns the
  only writable connection. Each job is one short `BEGIN IMMEDIATE ... COMMIT`
  transaction, so a graded answer submitted as one job is committed on its own (ARC-8).
  A write submitted from inside a running job joins that job's transaction as a
  savepoint: if it raises, its own changes are rolled back before the error propagates.
- Reads: each thread gets its own `query_only` connection (never shared), with the
  read-only packs ATTACHed (`mode=ro`). Connections of finished threads are closed.
  close() never closes a reader another thread is reading on: it waits for that read to
  end (closing a connection under a running query crashes the interpreter).
- The profile is locked with flock while open, so two writers can never meet.
- Pragmas: WAL, synchronous=FULL, foreign_keys=ON, busy_timeout, trusted_schema=OFF, and
  fullfsync + checkpoint_fullfsync: on macOS a plain fsync() stops at the drive's volatile
  cache, so without F_FULLFSYNC a committed answer can still vanish on power loss.
"""

import fcntl
import os
import queue
import sqlite3
import threading
import urllib.parse
import weakref
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.model import PackInfo
from core.storage import schema
from core.storage.clock import Clock, SystemClock
from core.storage.errors import (
    CorruptDatabaseError,
    MissingDatabaseError,
    PackError,
    ProfileInUseError,
    StorageError,
    UnsafeSQLiteError,
)
from core.storage.packs import read_pack_info

BUSY_TIMEOUT_MS = 10_000
CLOSE_WAIT_S = 30.0  # how long close() waits for another thread's read to finish
# DEV-7: SQLite 3.7.0 to 3.51.2 can corrupt a WAL database when two connections write or
# checkpoint at the same instant (the WAL-reset bug). Fixed in 3.51.3 and backported to
# 3.50.7 and 3.44.6; every safe version also has STRICT tables (3.37).
MIN_SQLITE = (3, 51, 3)
SQLITE_BACKPORTS: dict[tuple[int, int], int] = {(3, 50): 7, (3, 44): 6}  # line -> first fixed
RESTORE_SUFFIX = ".incoming"
SIDE_SUFFIXES = ("-wal", "-shm", "-journal")  # files SQLite keeps beside a database

type Job[T] = Callable[[sqlite3.Connection], T]


def file_uri(path: Path, **params: str) -> str:
    uri = "file:" + urllib.parse.quote(str(path.absolute()))
    return uri + ("?" + urllib.parse.urlencode(params) if params else "")


def sqlite_is_safe(version: tuple[int, int, int]) -> bool:
    """True when this SQLite version has the WAL-reset fix (3.51.3+, 3.50.7+, 3.44.6+)."""
    if version >= MIN_SQLITE:
        return True
    first_fixed = SQLITE_BACKPORTS.get(version[:2])
    return first_fixed is not None and version[2] >= first_fixed


def require_safe_sqlite() -> None:
    """Refuse to touch any database with a SQLite that has the WAL-reset bug (DEV-7)."""
    if not sqlite_is_safe(sqlite3.sqlite_version_info):
        raise UnsafeSQLiteError(
            f"SQLite {sqlite3.sqlite_version} has a bug that can corrupt saved progress; "
            "Toishi needs SQLite 3.51.3 or later (or 3.50.7+, 3.44.6+)"
        )


def connect(path: Path, *, mode: str = "rw", check_same_thread: bool = True) -> sqlite3.Connection:
    """Open with explicit transaction control (autocommit=True: no implicit BEGIN/COMMIT)."""
    require_safe_sqlite()
    conn = sqlite3.connect(
        file_uri(path, mode=mode),
        uri=True,
        autocommit=True,
        timeout=BUSY_TIMEOUT_MS / 1000,
        check_same_thread=check_same_thread,
    )
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA trusted_schema = OFF")
    # Any connection may commit, or checkpoint as the last one to close: flush for real.
    conn.execute("PRAGMA fullfsync = ON")
    conn.execute("PRAGMA checkpoint_fullfsync = ON")
    return conn


def configure_user(conn: sqlite3.Connection, *, writer: bool) -> None:
    if writer:
        mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        if str(mode).lower() != "wal":
            raise StorageError(f"could not switch user.db to WAL (got {mode!r})")
    conn.execute("PRAGMA synchronous = FULL")
    conn.execute("PRAGMA foreign_keys = ON")
    if not writer:
        conn.execute("PRAGMA query_only = ON")


def integrity_problems(path: Path, *, full: bool = False) -> list[str]:
    """[] when PRAGMA quick_check (or integrity_check) passes; otherwise what is wrong."""
    try:
        conn = connect(path, mode="rw")
    except sqlite3.Error as error:
        return [f"cannot open: {error}"]
    try:
        conn.execute("PRAGMA query_only = ON")
        pragma = "integrity_check" if full else "quick_check"
        rows = [str(r[0]) for r in conn.execute(f"PRAGMA {pragma}")]
        rows += [f"foreign key: {tuple(r)}" for r in conn.execute("PRAGMA foreign_key_check")]
    except sqlite3.Error as error:
        return [f"{type(error).__name__}: {error}"]
    finally:
        conn.close()
    return [] if rows == ["ok"] else [r for r in rows if r != "ok"]


@contextmanager
def profile_lock(db_path: Path) -> Iterator[int]:
    fd = acquire_lock(db_path)
    try:
        yield fd
    finally:
        release_lock(fd)


def acquire_lock(db_path: Path) -> int:
    lock_path = db_path.with_name(db_path.name + ".lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise ProfileInUseError(f"{db_path} is open elsewhere") from None
    return fd


def release_lock(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def full_fsync(fd: int) -> None:
    """Flush a file to stable storage. On macOS that takes F_FULLFSYNC: fsync() there only
    reaches the drive's cache, which a power loss can drop or write out of order."""
    op = getattr(fcntl, "F_FULLFSYNC", None)
    if op is not None:
        try:
            fcntl.fcntl(fd, op)
            return
        except OSError:
            pass  # not supported here (some file systems, some directories): plain fsync
    os.fsync(fd)


def fsync_path(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        full_fsync(fd)
    finally:
        os.close(fd)


def recover_interrupted_restore(db_path: Path) -> None:
    """Finish or undo a restore that a crash interrupted (see BackupManager.restore)."""
    incoming = db_path.with_name(db_path.name + RESTORE_SUFFIX)
    if not incoming.exists():
        return
    if db_path.exists():
        incoming.unlink()  # the swap never happened; the old database is intact
        return
    if integrity_problems(incoming):
        raise CorruptDatabaseError(incoming, ["interrupted restore left a damaged file"])
    # The crash may have come between moving user.db aside and moving its -wal/-journal:
    # SQLite would replay those onto the restored file. Set them aside, never delete.
    for suffix in SIDE_SUFFIXES:
        side = db_path.with_name(db_path.name + suffix)
        if side.exists():
            stale = side.with_name(side.name + ".stale")
            serial = 1
            while stale.exists():
                serial += 1
                stale = side.with_name(f"{side.name}.stale-{serial}")
            side.replace(stale)
    incoming.replace(db_path)
    fsync_path(db_path.parent)


def _attach_limit() -> int:
    probe = sqlite3.connect(":memory:")
    try:
        return probe.getlimit(sqlite3.SQLITE_LIMIT_ATTACHED)
    finally:
        probe.close()


# ---------------------------------------------------------------- the single writer


class _Writer:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._jobs: queue.SimpleQueue[tuple[Job[Any], Future[Any], bool] | None] = (
            queue.SimpleQueue()
        )
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None
        self._conn: sqlite3.Connection | None = None
        self._closed = False
        self._close_lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name="mastery-db-writer", daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._startup_error is not None:
            raise self._startup_error

    def on_writer_thread(self) -> bool:
        return threading.current_thread() is self._thread

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None or not self.on_writer_thread():
            raise StorageError("the write connection belongs to the writer thread")
        return self._conn

    def submit[T](self, job: Job[T], *, transaction: bool = True) -> T:
        if self.on_writer_thread():
            if not transaction:
                raise StorageError("a non-transactional job cannot run inside a write job")
            return self._nested(job)
        future: Future[T] = Future()
        with self._close_lock:
            if self._closed:
                raise StorageError("the database is closed")
            self._jobs.put((job, future, transaction))
        return future.result()

    def _nested[T](self, job: Job[T]) -> T:
        """A write inside a running job joins its transaction as a savepoint, so a nested
        call that fails part-way leaves none of its rows even if the caller carries on."""
        conn = self.conn
        conn.execute("SAVEPOINT nested_write")
        try:
            result = job(conn)
        except BaseException:
            if conn.in_transaction:  # some errors already rolled everything back
                conn.execute("ROLLBACK TO nested_write")
                conn.execute("RELEASE nested_write")
            raise
        conn.execute("RELEASE nested_write")
        return result

    def _run(self) -> None:
        try:
            conn = connect(self._path, mode="rw")
            configure_user(conn, writer=True)
        except BaseException as error:
            self._startup_error = error
            self._ready.set()
            return
        self._conn = conn
        self._ready.set()
        try:
            while (item := self._jobs.get()) is not None:
                job, future, transaction = item
                if future.set_running_or_notify_cancel():
                    self._execute(conn, job, future, transaction)
        finally:
            conn.close()

    @staticmethod
    def _execute(
        conn: sqlite3.Connection, job: Job[Any], future: Future[Any], transaction: bool
    ) -> None:
        try:
            if not transaction:
                result = job(conn)
            else:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    result = job(conn)
                    conn.execute("COMMIT")
                except BaseException:
                    if conn.in_transaction:
                        conn.execute("ROLLBACK")
                    raise
        except BaseException as error:
            future.set_exception(error)
        else:
            future.set_result(result)

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            self._jobs.put(None)  # queued jobs before it still run
        if not self.on_writer_thread():
            self._thread.join()


# ---------------------------------------------------------------- the database


@dataclass(frozen=True, slots=True)
class AttachedPack:
    alias: str
    path: Path
    info: PackInfo


class _ReaderState(threading.local):
    conn: sqlite3.Connection | None = None
    busy: threading.Lock | None = None  # held while this thread has a read open
    generation = -1
    depth = 0
    attached: tuple[str, ...] = ()


class Database:
    """One open user.db. Create with Database.open(); close() when done."""

    def __init__(self, path: Path, clock: Clock, lock_fd: int) -> None:
        self.path = path
        self.clock = clock
        self._lock_fd: int | None = lock_fd
        self._writer = _Writer(path)
        self._local = _ReaderState()
        self._registry: list[tuple[weakref.ref[threading.Thread], sqlite3.Connection]] = []
        self._busy: dict[sqlite3.Connection, threading.Lock] = {}  # see reading()
        self._registry_lock = threading.Lock()
        self._packs: tuple[AttachedPack, ...] = ()
        self._generation = 0
        self._next_alias = 0

    @classmethod
    def open(
        cls,
        path: Path,
        *,
        clock: Clock | None = None,
        pack_paths: Sequence[Path] = (),
        create: bool = False,
        before_migration: schema.BeforeStep | None = None,
        migrations: Sequence[schema.Migration] = schema.MIGRATIONS,
        target_version: int = schema.USER_SCHEMA_VERSION,
    ) -> Database:
        """Lock, integrity-check (BAK-4), migrate (backup hook first) and start the writer."""
        require_safe_sqlite()  # before any file is touched (DEV-7)
        path = path.absolute()
        if not create and not path.parent.is_dir():
            raise MissingDatabaseError(f"{path} does not exist")
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = acquire_lock(path)
        try:
            # Only under the lock: a restore in progress holds it, and its .incoming file
            # must not be finished or discarded by a second launch meanwhile.
            recover_interrupted_restore(path)
            exists = path.exists()
            if not exists and not create:
                raise MissingDatabaseError(f"{path} does not exist")
            if exists:
                problems = integrity_problems(path)
                if problems:
                    raise CorruptDatabaseError(path, problems)
            conn = connect(path, mode="rwc" if create else "rw")
            try:
                schema.check_user_db(conn, target=target_version)  # before anything writes
                configure_user(conn, writer=True)
                schema.migrate(
                    conn, target=target_version, migrations=migrations, before_step=before_migration
                )
            finally:
                conn.close()
            db = cls(path, clock or SystemClock(), lock_fd)
        except BaseException:
            release_lock(lock_fd)
            raise
        try:
            for pack_path in pack_paths:
                db.attach_pack(pack_path)
        except BaseException:
            db.close()
            raise
        return db

    # ------------------------------------------------------------ writes

    def write[T](self, job: Job[T]) -> T:
        """Run job(conn) on the writer thread in its own transaction; return its result."""
        self._check_open()
        return self._writer.submit(job)

    def write_outside_transaction[T](self, job: Job[T]) -> T:
        """For PRAGMAs that refuse to run in a transaction (wal_checkpoint)."""
        self._check_open()
        return self._writer.submit(job, transaction=False)

    @property
    def in_write_job(self) -> bool:
        return self._writer.on_writer_thread()

    # ------------------------------------------------------------ reads

    @contextmanager
    def reading(self, *, packs: bool = False) -> Iterator[sqlite3.Connection]:
        """A consistent read snapshot on this thread's own connection.

        Inside a write job this is the write connection (it sees the job's own changes);
        packs are not attached there, so pack reads must happen before writing.
        """
        self._check_open()
        if self._writer.on_writer_thread():
            if packs:
                raise StorageError("read pack content before submitting the write job")
            yield self._writer.conn
            return
        state = self._local
        conn = state.conn if state.conn is not None else self._new_reader()
        busy = self._local.busy
        if busy is None:  # pragma: no cover - set together with conn in _new_reader
            raise StorageError("a read connection without its lock")
        if state.depth == 0:
            busy.acquire()  # close() waits for it before closing this connection
            try:
                self._check_open()  # closed while this thread waited
                try:
                    self._sync_packs(conn)
                except sqlite3.Error:
                    if packs:
                        raise
                    # A pack file that vanished or broke must not block reading progress;
                    # the attach is retried on this thread's next read.
                conn.execute("BEGIN")
            except BaseException:
                busy.release()
                raise
        state.depth += 1
        try:
            yield conn
        finally:
            state.depth -= 1
            if state.depth == 0:
                try:
                    if conn.in_transaction:
                        conn.execute("COMMIT")
                finally:
                    busy.release()

    def _new_reader(self) -> sqlite3.Connection:
        # check_same_thread=False only so close() can close it from the closing thread;
        # it is only ever used by the thread that opened it (thread-local).
        conn = connect(self.path, mode="rw", check_same_thread=False)
        configure_user(conn, writer=False)
        busy = threading.Lock()
        with self._registry_lock:
            if self._lock_fd is None:  # closed meanwhile: close() will not see this one
                conn.close()
                raise StorageError("the database is closed")
            alive = []
            for thread_ref, other in self._registry:
                thread = thread_ref()
                if thread is None or not thread.is_alive():
                    other.close()
                    self._busy.pop(other, None)
                else:
                    alive.append((thread_ref, other))
            alive.append((weakref.ref(threading.current_thread()), conn))
            self._registry = alive
            self._busy[conn] = busy
        self._local.conn = conn
        self._local.busy = busy
        return conn

    # ------------------------------------------------------------ packs

    @property
    def packs(self) -> tuple[AttachedPack, ...]:
        return self._packs

    def attach_pack(self, path: Path) -> PackInfo:
        """Validate a sealed pack and attach it read-only to every reader."""
        info = read_pack_info(path)
        with self._registry_lock:
            if any(p.info.id == info.id for p in self._packs):
                raise PackError(f"pack {info.id} is already attached")
            if len(self._packs) + 1 > _attach_limit():
                raise PackError(f"at most {_attach_limit()} packs can be attached")
            alias = f"pack{self._next_alias}"
            self._next_alias += 1
            self._packs = (*self._packs, AttachedPack(alias, path.absolute(), info))
            self._generation += 1
        return info

    def detach_pack(self, pack_id: str) -> None:
        with self._registry_lock:
            self._packs = tuple(p for p in self._packs if p.info.id != pack_id)
            self._generation += 1

    def _sync_packs(self, conn: sqlite3.Connection) -> None:
        state = self._local
        if state.generation == self._generation:
            return
        packs = self._packs
        wanted = {p.alias: p for p in packs}
        for alias in state.attached:
            if alias not in wanted:
                conn.execute(f"DETACH DATABASE {alias}")
                state.attached = tuple(a for a in state.attached if a != alias)
        for alias, pack in wanted.items():
            if alias not in state.attached:
                conn.execute("ATTACH DATABASE ? AS " + alias, (file_uri(pack.path, mode="ro"),))
                state.attached = (*state.attached, alias)
        state.generation = self._generation

    # ------------------------------------------------------------ lifecycle

    def checkpoint(self) -> None:
        """Fold the WAL into the main file (before copying files around)."""
        self.write_outside_transaction(
            lambda conn: conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
        )

    @property
    def closed(self) -> bool:
        return self._lock_fd is None

    def _check_open(self) -> None:
        if self._lock_fd is None:
            raise StorageError("the database is closed")

    def close(self) -> None:
        if self._lock_fd is None:
            return
        self._writer.close()
        with self._registry_lock:
            readers, self._registry = self._registry, []
            busy, self._busy = self._busy, {}
            lock_fd, self._lock_fd = self._lock_fd, None  # new reads now refuse
        me = threading.current_thread()
        for thread_ref, conn in readers:
            lock = busy.get(conn)
            if thread_ref() is me or lock is None:
                conn.close()  # our own: nothing of ours can be running on it
                continue
            # Another thread's reader: wait for its read to end. Closing it under a running
            # query is a use-after-free in sqlite3 (a segfault). A read that never ends
            # leaves its connection to be freed with its thread rather than crash.
            if lock.acquire(timeout=CLOSE_WAIT_S):
                try:
                    conn.close()
                finally:
                    lock.release()
        self._local = _ReaderState()
        release_lock(lock_fd)

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
