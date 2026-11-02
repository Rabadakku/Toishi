"""Queue loose ends between the fitting and grading branches (ADR-0016)."""

import threading
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.engine import Engine
from tests.queue.helpers import World, answer, make_world, review_state

SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]
FSRS = ("fsrs_state", "stability", "difficulty", "last_review_at", "reps", "lapses")


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path, ("ca",), sections=2, skills=3, state="solid")
    now = w.clock.now_ms()
    w.storage.users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in SKILLS])
    yield w
    w.storage.close(backup=False)


def _fsrs(state: object) -> tuple[object, ...]:
    return tuple(getattr(state, k) for k in FSRS)


def test_C3_a_dispute_after_later_changes_voids_the_answer_and_rebuilds_memory(
    world: World,
) -> None:
    users = world.storage.users
    before = {k: _fsrs(s) for k, s in users.skill_states().items()}
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("slip")  # graded now (an excused Again), still on screen
    (graded,) = [a for a in users.attempts() if a.final]
    skill = graded.skill_id
    assert skill is not None
    moved = users.skill_state(skill)
    assert moved is not None
    assert _fsrs(moved) != before[skill]  # the review moved its memory
    users.apply([replace(moved, elo_theta=moved.elo_theta + 1)])  # a later change
    result = svc.flag("dispute", "I was right")
    assert result.ok
    assert not result.attempt_counts
    assert all(a.voided_by is not None for a in users.attempts(include_voided=True) if a.final)
    assert users.voids()[-1].reason == "dispute"
    assert users.disputes()[-1].note == "I was right"
    after = users.skill_state(skill)
    assert after is not None
    assert _fsrs(after) == before[skill]  # memory as the log says without the answer (C3)
    assert after.elo_theta == moved.elo_theta + 1  # rows outside memory keep later values
    assert Engine(world.storage).recompute_memory().changed == ()


def test_I7_a_due_fit_runs_in_the_background_after_the_session_ends(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    release = threading.Event()
    wrote = threading.Event()

    def fake_auto_fit(self: Engine, *, writing: Any = None) -> list[Any]:
        calls.append(threading.current_thread().name)
        assert release.wait(5)  # a slow fit
        with writing():  # the write half holds the service lock
            wrote.set()
        return []

    monkeypatch.setattr(Engine, "auto_fit", fake_auto_fit)
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=True)
    svc.next()
    assert calls == []  # never while answering
    svc.end()  # returns while the fit is still running: the student doesn't wait
    assert not wrote.is_set()
    assert svc.start_auto_fit() is False  # one fit at a time
    with svc._locked():  # the student's next call holds the lock: the write waits for it
        release.set()
        assert not wrote.wait(0.2)
    assert svc.wait_for_auto_fit(5)
    assert wrote.is_set()
    assert calls == ["auto-fit"]
    assert svc.last_auto_fit == []


def test_I7_a_failed_background_fit_is_kept_not_raised(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(self: Engine, *, writing: Any = None) -> list[Any]:
        raise RuntimeError("no fit today")

    monkeypatch.setattr(Engine, "auto_fit", broken)
    svc = world.service()
    svc.start()
    svc.end()
    assert svc.wait_for_auto_fit(5)
    assert isinstance(svc.last_auto_fit, RuntimeError)


def test_cloze_items_parse_like_anki() -> None:
    from core.queue.cloze import back, blank_numbers, front, ords

    text = "{{c1,2::shared}} and {{c3::outer {{c4::inner::h}} end}}"
    assert blank_numbers(text) == [1, 2, 3, 4]
    assert ords(text) == [0, 1, 2, 3]
    assert front(text, 0) == "[...] and outer inner end"
    assert front(text, 1) == "[...] and outer inner end"  # c1,2: one blank, two items
    assert front(text, 3) == "shared and outer [h] end"  # nested: only c4 hidden
    assert front(text, 2) == "shared and [...]"
    assert back(text, 2) == "shared and **outer inner end**"
    # Inside MathJax, }} closes only a blank opened inside it (Anki's cloze.rs).
    math = r"{{c1::\(x^{2^{a}}\)}} and {{c2::y}}"
    assert front(math, 0) == "[...] and y"
    assert back(math, 0) == r"**\(x^{2^{a}}\)** and y"
