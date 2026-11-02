"""The queue on real content: the Test pack (packs/test, every card kind) imported as the
student's own cards, answered through the real answer checker, over several study days."""

from collections import Counter
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core import grader
from core.cards import apply_import, plan_import
from core.cards.load import skills_in, sources_in
from core.model import Card
from core.queue import Plan, StudyService, Turn
from core.storage import Storage
from core.storage.clock import FixedClock
from core.storage.profiles import ProfilePaths
from tests.queue.helpers import NY

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def storage(tmp_path: Path) -> Iterator[Storage]:
    clock = FixedClock(datetime(2026, 9, 1, 12, tzinfo=NY), tz=NY)
    opened = Storage.open(ProfilePaths(tmp_path / "p"), clock=clock, create=True)
    users = opened.users
    users.set_setting("study.timezone", "America/New_York")
    folder = ROOT / "packs" / "test"
    plan = plan_import(users, sources_in(folder), skills_in(folder))
    assert plan.rejected == []
    apply_import(users, plan)
    for section in opened.packs.sections():
        users.set_section_state(section.id, "learning")
    yield opened
    opened.close(backup=False)
    grader.shutdown()


def typed(card: Card) -> list[dict[str, str]]:
    """What a student who knows the answer types: the key (first alternative for text)."""

    def key(answer_type: str, answer: str | None) -> str:
        text = answer or ""
        return text.split(";")[0].strip() if answer_type == "text" else text

    if card.parts:
        return [{"part": p.label, "value": key(p.answer_type, p.answer)} for p in card.parts]
    return [{"value": key(card.answer_type, card.answer)}]


def study(svc: StudyService, storage: Storage, clock: FixedClock, kinds: Counter[str]) -> Turn:
    turn = svc.start()
    steps = 0
    while turn.type == "problem" and turn.problem is not None and steps < 80:
        steps += 1
        p = turn.problem
        kinds[p.card.kind] += 1
        clock.advance(seconds=45)
        if p.kind == "example":
            turn = svc.next()
            continue
        if p.kind == "flashcard":
            svc.rate_flashcard(3)
            turn = svc.next()
            continue
        card = storage.packs.card(p.card.id)
        assert card is not None
        timing = {"active_ms": 45_000, "solve_ms": 40_000, "entry_ms": 4_000}
        if p.card.self_graded:
            result = svc.submit({"self_grade": "matched", "timing": timing})
        else:
            result = svc.submit({"answers": typed(card), "timing": timing})
            if result.outcome == "self-grade":
                result = svc.submit({"self_grade": "matched", "timing": timing})
            elif result.outcome == "retry":
                result = svc.give_up(timing)
        assert result.outcome in ("correct", "incorrect"), (card.id, result)
        if result.outcome == "incorrect":
            svc.diagnose("cant_tell")
        turn = svc.next()
    return turn


def test_a_week_on_the_test_pack(storage: Storage) -> None:
    clock = storage.db.clock
    assert isinstance(clock, FixedClock)
    svc = StudyService(storage)
    kinds: Counter[str] = Counter()
    for day in range(5):
        turn = study(svc, storage, clock, kinds)
        assert turn.type in ("summary", "empty"), day
        clock.set(datetime(2026, 9, 2, 12, tzinfo=NY) + timedelta(days=day))
    attempts = [a for a in storage.users.attempts() if a.final]
    assert len(attempts) > 20
    assert "incorrect" not in {a.verdict for a in attempts}  # the real checker agreed
    assert kinds["flashcard"] >= 1
    assert kinds["cloze"] >= 1  # flashcards and cloze cards sit between problems
    assert kinds["example"] >= 2  # learning blocks open with their worked example
    assert {"problem"} <= set(kinds)
    states = storage.users.skill_states()
    assert sum(1 for s in states.values() if s.learned_at is not None) >= 3
    plan = svc.plan_preview()
    assert isinstance(plan, Plan)
    assert sum(plan.quotas.values()) + plan.info["free"] == plan.info["count"]
