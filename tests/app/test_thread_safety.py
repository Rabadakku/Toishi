"""Bridge calls arrive on many threads at once (pywebview: one thread per call)."""

import threading
from collections.abc import Callable
from typing import Any

from app.api import Api, UserMessage


def test_concurrent_calls_never_interleave_or_share_a_connection(studying: Api) -> None:
    turn = studying.study_start({})
    while turn["problem"]["kind"] != "problem":
        key = turn["problem"]["item_key"]
        if turn["problem"]["kind"] == "flashcard":
            studying.study_rate_flashcard({"item_key": key, "rating": 3})
        turn = studying.study_next({"item_key": key})
    key = turn["problem"]["item_key"]
    part = turn["problem"]["card"]["parts"][0]["label"]
    errors: list[str] = []
    results: dict[str, int] = {}
    lock = threading.Lock()
    start = threading.Barrier(24)

    def run(name: str, call: Callable[[], Any], times: int = 8) -> None:
        start.wait()
        for _ in range(times):
            try:
                call()
                with lock:
                    results[name] = results.get(name, 0) + 1
            except UserMessage:
                pass  # e.g. the item moved on: a message, never a crash
            except Exception as error:
                with lock:
                    errors.append(f"{name}: {type(error).__name__}: {error}")

    calls: list[tuple[str, Callable[[], Any]]] = [
        ("today", studying.study_today),
        ("library", studying.library_get),
        ("current", studying.study_current),
        ("resume", studying.study_resume),
        ("prefs", studying.prefs_get),
        ("forecast", studying.study_forecast),
        (
            "preview",
            lambda: studying.study_read_answer({"item_key": key, "part": part, "value": "x+1"}),
        ),
        ("tick", lambda: studying.study_tick({"item_key": key, "active_ms": 1000, "draft": None})),
    ]
    threads = [threading.Thread(target=run, args=(name, call)) for name, call in calls * 3]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)
    assert errors == []
    assert all(results.get(name, 0) > 0 for name, _ in calls)

    # The session is intact: the same item, and its answer still grades.
    assert studying.study_current()["problem"]["item_key"] == key
    result = studying.study_give_up({"item_key": key, "timing": {"active_ms": 2000}})
    assert result["outcome"] == "incorrect"
    attempts = [a for a in studying._store().users.attempts() if a.final]
    assert len(attempts) == 1  # held on the verdict screen until Continue (ADR-0009)
    studying.study_next({"item_key": key})
    assert len([a for a in studying._store().users.attempts() if a.final]) == 2


def test_two_submits_racing_grade_the_item_once(studying: Api) -> None:
    turn = studying.study_start({})
    while turn["problem"]["kind"] != "problem":
        key = turn["problem"]["item_key"]
        if turn["problem"]["kind"] == "flashcard":
            studying.study_rate_flashcard({"item_key": key, "rating": 3})
        turn = studying.study_next({"item_key": key})
    key = turn["problem"]["item_key"]
    outcomes: list[str] = []
    barrier = threading.Barrier(6)

    def give_up() -> None:
        barrier.wait()
        try:
            outcomes.append(
                studying.study_give_up({"item_key": key, "timing": {"active_ms": 900}})["outcome"]
            )
        except UserMessage as message:
            outcomes.append(str(message))

    threads = [threading.Thread(target=give_up) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert outcomes.count("incorrect") == 1
    assert all("already answered" in o for o in outcomes if o != "incorrect")
