"""ARC-6: many threads write through the one writer; readers each have their own connection."""

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from core.model import Attempt, GradedAnswer, ReviewEvent, SkillState
from core.storage import Storage, StorageError, UserStore
from tests.storage.data import some

THREADS = 12
PER_THREAD = 40


def test_many_threads_write_through_one_writer(storage: Storage) -> None:
    users = storage.users
    writer_threads: set[str] = set()
    seen_counts: list[list[int]] = [[], [], []]
    stop = threading.Event()

    def reader(seen: list[int]) -> None:
        while not stop.is_set():
            with storage.db.reading() as conn:
                attempts = conn.execute("SELECT count(*) FROM attempt").fetchone()[0]
                reviews = conn.execute("SELECT count(*) FROM review_log").fetchone()[0]
            assert attempts == reviews  # never a half-written answer
            seen.append(attempts)

    def work(worker: int) -> list[int]:
        ids = []
        for n in range(PER_THREAD):
            skill = f"s{worker}"
            stored = users.record_answer(
                GradedAnswer(
                    attempt=Attempt(
                        card_id=f"c{worker}", skill_id=skill, verdict="correct", rating=3
                    ),
                    changes=(SkillState(skill_id=skill, reps=n + 1, stability=float(n + 1)),),
                    reviews=(
                        ReviewEvent(
                            target_kind="skill", target_id=skill, rating=3, rules_version="r1"
                        ),
                    ),
                )
            )
            ids.append(some(stored.id))
            writer_threads.add(storage.db.write(lambda _c: threading.current_thread().name))
        return ids

    readers = [threading.Thread(target=reader, args=(seen,)) for seen in seen_counts]
    for t in readers:
        t.start()
    with ThreadPoolExecutor(THREADS) as pool:
        results = list(pool.map(work, range(THREADS)))
    stop.set()
    for t in readers:
        t.join()

    all_ids = [i for ids in results for i in ids]
    assert sorted(all_ids) == list(range(1, THREADS * PER_THREAD + 1))
    assert all(ids == sorted(ids) for ids in results)  # each thread's writes are ordered
    assert writer_threads == {"mastery-db-writer"}
    states = users.skill_states()
    assert {s: states[s].reps for s in states} == {f"s{w}": PER_THREAD for w in range(THREADS)}
    for seen in seen_counts:  # each reader only ever sees the count grow
        assert seen
        assert seen == sorted(seen)
    assert users.counts()["reviews"] == THREADS * PER_THREAD


def test_each_thread_reads_on_its_own_connection(storage: Storage) -> None:
    # Keep the connection objects alive (not just their ids, which Python reuses after
    # garbage collection) and hold all five threads inside reading() at once.
    connections: dict[str, object] = {}
    lock = threading.Lock()
    together = threading.Barrier(5)

    def grab(name: str, wait: bool = True) -> None:
        with storage.db.reading() as first, storage.db.reading() as nested:
            assert first is nested
            with lock:
                connections[name] = first
            if wait:
                together.wait(timeout=10)

    threads = [threading.Thread(target=grab, args=(f"t{i}",)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(c) for c in connections.values()}) == 5
    # connections of finished threads are closed when the next thread opens a reader
    late = threading.Thread(target=grab, args=("late", False))
    late.start()
    late.join()
    owners = [ref() for ref, _ in storage.db._registry]
    assert owners == [threading.main_thread(), late]  # main opened one in Storage.open


def test_write_job_errors_roll_back_and_the_writer_keeps_going(storage: Storage) -> None:
    def failing(conn):
        conn.execute("INSERT INTO setting VALUES ('a', '1', 0)")
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        storage.db.write(failing)
    assert storage.users.get_setting("a", default=None) is None
    storage.users.set_setting("daily.problems", 33)
    assert storage.users.get_setting("daily.problems") == 33


def test_a_failed_nested_write_leaves_nothing_behind(storage: Storage) -> None:
    # No session 7: the answer fails on the attempt row, after its state rows were written.
    bad = GradedAnswer(
        attempt=Attempt(card_id="c", skill_id="s", verdict="correct", session_id=7),
        changes=(SkillState(skill_id="s", reps=5, stability=3.0, fsrs_state=2),),
    )

    def work(users: UserStore) -> None:
        with pytest.raises(sqlite3.IntegrityError):
            users.record_answer(bad)
        users.set_setting("daily.problems", 30)  # the caller carries on with other writes

    storage.users.atomic(work)
    assert storage.users.skill_state("s") is None  # no FSRS change without its attempt
    assert storage.users.counts()["attempts"] == 0
    assert storage.users.get_setting("daily.problems") == 30


def test_closed_database_refuses_work(storage: Storage) -> None:
    storage.close(backup=False)
    with pytest.raises(StorageError, match="closed"):
        storage.users.set_setting("daily.problems", 3)
    with pytest.raises(StorageError, match="closed"):
        storage.users.counts()
    assert storage.close() is None  # closing twice is harmless
