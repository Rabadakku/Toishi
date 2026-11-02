"""core/practice/observations.py: attempt rows -> the student model's observations."""

from collections import Counter
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from app.packs import shipped_packs
from core import cards, grader
from core.learner.types import Observation
from core.model import Attempt
from core.practice import build_catalog, build_observations, observations_of
from core.storage import Storage
from core.storage.profiles import ProfilePaths
from tests.practice.helpers import World, answer, make_world
from tests.storage.v1_cards import load_fixture
from tests.storage.v2_user import USER_V2


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    w = make_world(tmp_path)
    yield w
    w.storage.close(backup=False)


def obs_of(world: World, attempt: Attempt) -> tuple[Observation, ...]:
    return observations_of(attempt, build_catalog(world.storage))


def test_a_first_try_is_the_observation(world: World) -> None:
    right = answer(world, "c.limit.t2.v0", minutes=3.5)
    (obs,) = obs_of(world, right)
    assert (obs.correct, obs.aided, obs.minutes, obs.role) == (True, False, 3.5, "growth")
    assert obs.problem.problem_id == "c.limit.t2.v0"
    assert obs.study_day == date(2026, 9, 7)


def test_a_retried_wrong_first_try_is_a_miss_and_later_tries_are_not_observations(
    world: World,
) -> None:
    first = answer(
        world,
        "c.limit.t2.v1",
        correct=False,
        final=False,
        presentation="p1",
        matched_wrong=0,
        role="maintenance",
    )
    second = answer(world, "c.limit.t2.v1", attempt_number=2, presentation="p1")
    (obs,) = obs_of(world, first)
    assert (obs.correct, obs.minutes, obs.matched_wrong, obs.role) == (
        False,
        None,
        0,
        "maintenance",
    )
    assert obs_of(world, second) == ()


def test_a_give_up_before_any_answer_is_aided(world: World) -> None:
    gave_up = answer(world, "c.limit.t2.v2", correct=False, verdict="gave-up")
    (obs,) = obs_of(world, gave_up)
    assert (obs.correct, obs.aided) == (False, True)
    opened = answer(world, "c.limit.t3.v0", example_opened=True)
    (obs,) = obs_of(world, opened)
    assert (obs.correct, obs.aided, obs.minutes) == (True, True, None)


def test_self_grades_and_parts(world: World) -> None:
    graded = answer(world, "c.limit.t1.v0", verdict="self", extra={"correct": False})
    (obs,) = obs_of(world, graded)
    assert not obs.correct
    parts = [
        {"label": "a", "skill": None, "correct": True, "attempts": 1, "gave_up": False},
        {"label": "b", "skill": "c.squeeze", "correct": True, "attempts": 2, "gave_up": False},
    ]
    final = answer(world, "c.multi", extra={"parts": parts})
    a, b = obs_of(world, final)
    assert (a.problem.problem_id, a.correct, a.minutes) == ("c.multi#a", True, None)
    assert (b.problem.problem_id, b.correct) == ("c.multi#b", False)
    given_up = [{"label": "a", "correct": False, "attempts": 1, "gave_up": True}]
    (c,) = obs_of(world, answer(world, "c.multi", correct=False, extra={"parts": given_up}))
    assert (c.correct, c.aided) == (False, True)
    part_try = answer(world, "c.multi", correct=False, final=False, part="a")
    assert obs_of(world, part_try) == ()  # a part's "Not quite" is not an observation


def test_rows_that_are_not_observations(world: World) -> None:
    shown = answer(world, "c.limit.t1.v1", verdict="shown", final=False)
    example = answer(world, "c.limit.ex", verdict="shown")
    unknown = answer(world, "o.thing.t2", correct=True)
    unanswered = answer(
        world, "c.limit.t4.v0", correct=False, verdict="gave-up", extra={"unanswered": True}
    )
    assert obs_of(world, shown) == ()
    assert obs_of(world, example) == ()
    assert obs_of(world, unanswered) == ()
    assert len(obs_of(world, unknown)) == 1  # another course's problem is still evidence


def test_the_v2_history_reads_back_as_observations(tmp_path: Path) -> None:
    """The frozen v2 profile (old engine) with the Test pack: every first try of a problem,
    from the rows alone, by an independent reading of the log."""
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(USER_V2, paths.user_db, version=2)
    packs = [p for p in shipped_packs() if p.stem in ("test", "tutorial")]
    try:
        with Storage.open(paths, pack_paths=packs) as storage:
            catalog = build_catalog(storage)
            rows = storage.users.attempts(include_voided=True)
            found = build_observations(rows, catalog)
    finally:
        grader.shutdown()
        cards.shutdown()
    expected: list[tuple[int, str, bool]] = []
    for a in rows:
        if a.voided_by is not None or a.card_kind != "problem" or a.verdict == "shown":
            continue
        if a.extra.get("unanswered"):
            continue
        parts = a.extra.get("parts")
        if parts:
            for p in parts:
                ok = p["correct"] and p.get("attempts", 1) == 1 and not p.get("gave_up")
                expected.append((a.id or 0, f"{a.card_id}#{p['label']}", bool(ok)))
        elif a.part is None and a.attempt_number == 1:
            ok = a.verdict == "correct" and a.hints_used == 0
            if a.verdict in ("self", "undecided"):
                ok = bool(a.extra.get("strict_ok"))
            expected.append((a.id or 0, a.card_id, ok))
    got = [(o.attempt_id, o.problem.problem_id, o.correct and not o.aided) for o in found]
    assert sorted(got) == sorted(expected)
    assert len(found) > 30
    kinds = Counter((o.correct, o.aided) for o in found)
    assert kinds[(True, False)]
    assert kinds[(False, False)]
    assert kinds[(False, True)]
    assert kinds[(True, True)]  # a hint before the right answer: aided
    assert {o.role for o in found} == {"growth"}  # rows before v3
    timed = [o for o in found if o.minutes is not None]
    assert timed
    assert all(o.correct and not o.aided for o in timed)
    by_id = {a.id: a for a in rows}
    for o in timed:
        assert o.minutes == pytest.approx(by_id[o.attempt_id].extra["speed_ms"] / 60_000)
    assert [(o.at_ms, o.attempt_id) for o in found] == sorted(
        (o.at_ms, o.attempt_id) for o in found
    )
