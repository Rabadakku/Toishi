"""Study-flow fixes from the full evidence review (ADR-0019), each failing before its fix.
Items are numbered as in the M7 engine brief."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from core.storage.user_store import UserStore
from tests.queue.helpers import World, answer, make_world, review_state

SKILLS = [f"ca.s{s}.k{k}" for s in (1, 2) for k in (1, 2, 3)]


@pytest.fixture
def world(tmp_path: Path) -> Iterator[World]:
    """One course, all sections Solid, every skill in review and due today."""
    w = make_world(
        tmp_path,
        ("ca",),
        sections=2,
        skills=3,
        flashcards=True,
        state="solid",
        settings={"daily.flashcards": 0},
    )
    now = w.clock.now_ms()
    w.storage.users.apply([review_state(k, now, days_ago=5, stability=2.0) for k in SKILLS])
    yield w
    w.storage.close(backup=False)


# ---------------------------------------------------------------- 15. disputes are atomic


def test_15_a_dispute_writes_the_void_and_its_record_together(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    users = world.storage.users
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    answer(svc, world.clock, correct=False)
    svc.diagnose("cant-tell")  # graded now, still on screen
    assert [a for a in users.attempts() if a.final]

    def killed(self: UserStore, dispute: object) -> object:
        raise RuntimeError("the process ended between the two writes")

    monkeypatch.setattr(UserStore, "add_dispute", killed)
    with pytest.raises(RuntimeError):
        svc.flag("dispute", "I was right")
    assert users.voids() == []  # neither row: the void rolled back with the dispute
    assert all(a.voided_by is None for a in users.attempts(include_voided=True))
    monkeypatch.undo()
    assert svc.flag("dispute", "I was right").ok
    assert len(users.disputes()) == 1
    assert users.voids()[-1].reason == "dispute"


# ---------------------------------------------------------------- 4. undo after the solution


@pytest.mark.parametrize("graded", [False, True])
def test_4_undo_after_the_solution_was_shown_never_gives_a_clean_good(
    world: World, graded: bool
) -> None:
    users = world.storage.users
    svc = world.service()
    svc.start()
    answer(svc, world.clock, correct=False)
    miss = answer(svc, world.clock, correct=False)  # the last attempt: the solution shows
    assert miss.solution
    if graded:
        svc.diagnose("cant-tell")  # graded, still on screen
    undone = svc.undo()
    assert undone.problem is not None
    first_card = undone.problem.card.id
    assert answer(svc, world.clock, correct=True).outcome == "correct"
    svc.next()  # commits it
    final = [a for a in users.attempts() if a.final][-1]
    assert final.card_id == first_card  # the same problem back ...
    assert final.rating is not None
    assert final.rating <= 2  # ... capped: never a clean Good (ADR-0019 item 7)
    assert final.extra.get("strict_ok") is False
    assert final.hints_used >= 1
