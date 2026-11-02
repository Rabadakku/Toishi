"""Every card kind through StudyService on the Test pack, built and compiled with the pack
CLI (content-tools/mepack.py build, then compile) and answered through the real checker:
multi-part problems (a verdict and tries per part), find-the-error and which-method items
(with the diagnosis flow's gating), cloze cards (one item per blank), self-graded problems
(Show solution, rubric ticks or the three buttons) and practice tests (ENG-8)."""

import os
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from core import grader
from core.engine import memory_of
from core.model import Attempt, Card, CardMark, Exam, GradedAnswer, PackInfo
from core.queue import Plan, StudyService, Turn
from core.queue.cloze import back, blank_numbers, front, ords
from core.queue.session import practice_test_allocation
from core.storage import Storage, build_pack
from core.storage.clock import FixedClock, to_ms
from core.storage.profiles import ProfilePaths
from tests.queue.helpers import DAY, NY, fake_checker, fake_preview, review_state, world_records

ROOT = Path(__file__).resolve().parents[2]
START = datetime(2026, 9, 1, 12, tzinfo=NY)

ARITH = "test.alg.arithmetic"
LINEAR = "test.alg.linear-solve"
FACTOR = "test.alg.factor-quadratic"
FORMULA = "test.alg.quadratic-formula"
QUAD = "test.alg.quadratic-solve"
VERTEX = "test.alg.vertex"
METHOD = "test.alg.choose-quadratic-method"
POWER = "test.calc.power-rule"
PARABOLA = "test.quad.parabola.001"
FIND = "test.quad.factor-error.001"
EXPLAIN = "test.linear.explain.001"
CLOZE = "test.linear.cloze.001"


@pytest.fixture(scope="module")
def pack_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """packs/test through the CLI: build (checks, .mepack), then compile the .mepack."""
    out = tmp_path_factory.mktemp("built")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    script = str(ROOT / "content-tools" / "mepack.py")
    for args in (
        ["build", str(ROOT / "packs" / "test"), "--no-render", "--out", str(out)],
        ["compile", str(out / "test-1.0.0.mepack"), "--out", str(out / "compiled.db")],
    ):
        run = subprocess.run(
            [sys.executable, script, *args],
            capture_output=True, text=True, check=False, env=env, cwd=ROOT, timeout=300,
        )  # fmt: skip
        assert run.returncode == 0, run.stdout + run.stderr
    return out / "compiled.db"


@pytest.fixture
def storage(tmp_path: Path, pack_db: Path) -> Iterator[Storage]:
    clock = FixedClock(START, tz=NY)
    opened = Storage.open(
        ProfilePaths(tmp_path / "p"), pack_paths=[pack_db], clock=clock, create=True
    )
    opened.users.set_setting("study.timezone", "America/New_York")
    for section in opened.packs.sections():
        opened.users.set_section_state(section.id, "learning")
    yield opened
    opened.close(backup=False)
    grader.shutdown()


def clock_of(storage: Storage) -> FixedClock:
    clock = storage.db.clock
    assert isinstance(clock, FixedClock)
    return clock


def in_review(storage: Storage, *skills: str, days_ago: float = 5, stability: float = 2.0) -> None:
    now = clock_of(storage).now_ms()
    storage.users.apply(
        [review_state(k, now, days_ago=days_ago, stability=stability) for k in skills]
    )


def only(storage: Storage, skill: str, keep: str) -> None:
    """Suspend the skill's other problems, so `keep` is the one served."""
    for ref in storage.packs.card_refs(skill_id=skill):
        if ref.kind == "problem" and ref.id != keep:
            storage.users.set_card_mark(CardMark(card_id=ref.id, suspended=True))


def uncued_successes(storage: Storage, skill: str, n: int = 2) -> None:
    """History: n successful uncued reviews of a skill (unlocks find-the-error items)."""
    now = clock_of(storage).now_ms()
    for i in range(n):
        storage.users.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    at=now - (i + 2) * DAY,
                    card_id=f"old.{skill}.{i}",
                    card_kind="problem",
                    skill_id=skill,
                    final=True,
                    verdict="correct",
                    rating=3,
                    extra={
                        "stage": "review",
                        "elo": {
                            "form": f"card:old.{skill}.{i}",
                            "p": 0.8,
                            "theta": 1.0,
                            "d": 0.0,
                            "d_after": 0.0,
                            "o": 1,
                        },
                    },
                )
            )
        )


def letters(choices: Any) -> str:
    return ", ".join("abcdefgh"[i] for i, c in enumerate(choices) if c.correct)


def typed(card: Card, *, wrong: dict[str, str] | None = None) -> list[dict[str, str]]:
    """What a student who knows the answer types (parts in `wrong` get that answer)."""

    def key(answer_type: str, answer: str | None, choices: Any) -> str:
        if answer_type == "choice":
            return letters(choices)
        text = answer or ""
        return text.split(";")[0].strip() if answer_type == "text" else text

    if card.parts:
        return [
            {
                "part": p.label,
                "value": (wrong or {}).get(p.label) or key(p.answer_type, p.answer, p.choices),
            }
            for p in card.parts
        ]
    return [{"value": key(card.answer_type, card.answer, card.choices)}]


TIMING = {"active_ms": 30_000, "solve_ms": 25_000, "entry_ms": 3_000}


def answer_right(svc: StudyService, storage: Storage, turn: Turn) -> Any:
    """Answer the problem on screen correctly, whatever its kind."""
    assert turn.problem is not None
    view = turn.problem.card
    card = storage.packs.card(view.id)
    assert card is not None
    if view.kind == "find-error":
        right = next(i for i, r in enumerate(card.reasons) if r.correct)
        return svc.submit(
            {
                "answers": typed(card),
                "error_step": card.error_step,
                "reason": right,
                "timing": TIMING,
            }
        )
    if view.self_graded:
        shown = svc.show_solution()
        assert shown.outcome == "self-grade"
        assert shown.solution is not None
        assert shown.solution.rubric == card.rubric
        if card.rubric:
            return svc.submit({"rubric_ticked": len(card.rubric), "timing": TIMING})
        return svc.submit({"self_grade": "matched", "timing": TIMING})
    return svc.submit({"answers": typed(card), "timing": TIMING})


def study_day(svc: StudyService, storage: Storage, seen: list[tuple[str, str, int | None]]) -> Turn:
    turn = svc.start()
    for _ in range(60):
        if turn.type != "problem" or turn.problem is None:
            return turn
        p = turn.problem
        seen.append((p.kind, p.card.kind, p.card.cloze))
        clock_of(storage).advance(seconds=40)
        if p.kind == "example":
            turn = svc.next()
            continue
        if p.kind == "flashcard":
            if p.card.kind == "cloze":
                assert "[...]" in p.card.prompt_md
                assert "{{c" not in p.card.prompt_md
            assert svc.rate_flashcard(3).outcome == "recorded"
            turn = svc.next()
            continue
        result = answer_right(svc, storage, turn)
        assert result.outcome == "correct", (p.card.id, result)
        turn = svc.next()
    raise AssertionError("the session did not end")


# ---------------------------------------------------------------- the mixed session


def test_a_session_mixes_every_card_kind(storage: Storage) -> None:
    users = storage.users
    reviewed = [k.id for k in storage.packs.skills() if k.id != POWER]
    in_review(storage, *reviewed)
    uncued_successes(storage, FACTOR)
    only(storage, QUAD, PARABOLA)
    only(storage, LINEAR, EXPLAIN)
    svc = StudyService(storage)
    seen: list[tuple[str, str, int | None]] = []
    end = study_day(svc, storage, seen)
    assert end.type == "summary"
    kinds = Counter(card_kind for _, card_kind, _ in seen)
    assert {"problem", "find-error", "method", "flashcard", "cloze", "example"} <= set(kinds)
    assert ("flashcard", "cloze", 1) in seen  # blank c1 today ...
    finals = {a.card_id: a for a in users.attempts() if a.final and a.card_kind != "flashcard"}
    # A multi-part problem: each part's verdict, the card's skill rated on its own part.
    parabola = finals[PARABOLA]
    assert [p["label"] for p in parabola.extra["parts"]] == ["a", "b", "c"]
    assert parabola.rating == 3
    assert parabola.extra["diagnosis"]["parts"] == {"b": "credit", "c": "credit"}
    # Find-the-error counts as a review of its skill; which-method as the method skill's.
    assert finals[FIND].rating == 3
    assert finals[FIND].skill_id == FACTOR
    assert finals[FIND].extra["find_error"]["reason_ok"]
    method = next(a for a in finals.values() if a.card_kind == "method")
    assert (method.skill_id, method.rating) == (METHOD, 3)
    # Self-graded with a rubric: every step ticked is Good.
    assert (finals[EXPLAIN].verdict, finals[EXPLAIN].rating) == ("self", 3)
    # The which-method item sat outside the problem count.
    assert end.session_id is not None
    row = users.session(end.session_id)
    assert row is not None
    plan = Plan.from_json(row.plan)
    assert [i.slots for i in plan.items if i.method] == [0]
    # ... and blank c2 the next study day (new siblings wait a day, like Anki).
    clock_of(storage).set(START + timedelta(days=1))
    seen2: list[tuple[str, str, int | None]] = []
    study_day(svc, storage, seen2)
    assert ("flashcard", "cloze", 2) in seen2
    assert {(f.card_id, f.ord) for f in users.flashcard_states() if f.card_id == CLOZE} == {
        (CLOZE, 0),
        (CLOZE, 1),
    }


# ---------------------------------------------------------------- multi-part problems


def focused(svc: StudyService, skill: str, count: int = 1) -> Turn:
    turn = svc.start({"mode": "focused", "skill_id": skill, "count": count})
    assert turn.problem is not None
    return turn


def test_multi_part_tries_and_verdicts_are_per_part(storage: Storage) -> None:
    in_review(storage, ARITH, LINEAR, FACTOR, QUAD, VERTEX)
    only(storage, QUAD, PARABOLA)
    svc = StudyService(storage)
    turn = focused(svc, QUAD)
    assert turn.problem is not None
    assert turn.problem.card.id == PARABOLA
    card = storage.packs.card(PARABOLA)
    assert card is not None
    assert [p.label for p in turn.problem.card.parts] == ["a", "b", "c"]
    first = svc.submit({"answers": typed(card, wrong={"a": "2, 3"}), "timing": TIMING})
    assert first.outcome == "retry"
    by_part = {p.part: p for p in first.verdicts}
    assert (by_part["a"].status, by_part["a"].final, by_part["a"].tries_used) == (
        "incorrect",
        False,
        1,
    )
    assert by_part["b"].final
    assert by_part["c"].final
    # Parts b and c are final: only part a is checked again.
    second = svc.submit({"answers": typed(card)[:1], "timing": TIMING})
    assert second.outcome == "correct"
    assert second.solution is not None
    assert not second.solution.needs_diagnosis
    assert {p.part: p.tries_used for p in second.verdicts} == {"a": 2, "b": 1, "c": 1}
    svc.next()
    users = storage.users
    tries = [a for a in users.attempts(card_id=PARABOLA) if not a.final]
    assert [a.part for a in tries] == ["a"]  # the "Not quite" is logged against its part
    (graded,) = [a for a in users.attempts(card_id=PARABOLA) if a.final]
    assert graded.rating == 2  # part a took two tries: Hard
    assert graded.attempt_number == 2
    assert users.pending_checks("pending") == []


def test_a_missed_part_with_its_own_skill_checks_that_skill(storage: Storage) -> None:
    in_review(storage, ARITH, LINEAR, FACTOR, QUAD, VERTEX)
    only(storage, QUAD, PARABOLA)
    svc = StudyService(storage)
    focused(svc, QUAD)
    card = storage.packs.card(PARABOLA)
    assert card is not None
    assert (
        svc.submit({"answers": typed(card, wrong={"b": "(1, 2)"}), "timing": TIMING}).outcome
        == "retry"
    )
    result = svc.submit({"answers": typed(card, wrong={"b": "(1, 2)"})[1:2], "timing": TIMING})
    assert result.outcome == "incorrect"  # not every part right ...
    assert result.solution is not None
    assert not result.solution.needs_diagnosis  # ... but the card's own parts were
    svc.next()
    (graded,) = [a for a in storage.users.attempts(card_id=PARABOLA) if a.final]
    assert graded.rating == 3
    assert graded.extra["diagnosis"]["parts"] == {"b": "check", "c": "credit"}
    (check,) = storage.users.pending_checks("pending")
    assert (check.skill_id, check.kind) == (VERTEX, "prerequisite")


def test_giving_up_a_multi_part_problem_gives_up_its_open_parts(storage: Storage) -> None:
    in_review(storage, ARITH, LINEAR, FACTOR, QUAD, VERTEX)
    only(storage, QUAD, PARABOLA)
    svc = StudyService(storage)
    focused(svc, QUAD)
    card = storage.packs.card(PARABOLA)
    assert card is not None
    answers = typed(card)
    svc.submit({"answers": [answers[0], answers[2]], "timing": TIMING})  # a and c right
    result = svc.give_up(TIMING)
    assert result.outcome == "incorrect"
    svc.next()
    (graded,) = [a for a in storage.users.attempts(card_id=PARABOLA) if a.final]
    assert graded.rating == 3  # part a, the card's own, was right
    parts = {p["label"]: p for p in graded.extra["parts"]}
    assert parts["b"]["gave_up"]
    assert not parts["a"]["gave_up"]


# ---------------------------------------------------------------- find-the-error items


def test_find_the_error_is_gated_and_graded_on_step_reason_and_value(storage: Storage) -> None:
    in_review(storage, ARITH, FACTOR)
    svc = StudyService(storage)
    # Locked: no uncued review successes yet (and no plain problem for the skill here).
    turn = svc.start({"mode": "focused", "skill_id": FACTOR, "count": 1})
    assert turn.type == "summary"  # its one item had nothing to serve
    uncued_successes(storage, FACTOR)
    turn = focused(svc, FACTOR)
    assert turn.problem is not None
    view = turn.problem.card
    assert view.kind == "find-error"
    assert turn.problem.attempts_allowed == 1
    assert [s.number for s in view.shown_work] == [1, 2]
    assert all(s.skill_name is None for s in view.shown_work)  # no skill names before
    assert len(view.reasons) == 3
    assert view.error_step == 2  # early on: the highlighted version
    assert "find the error" in turn.problem.reason.why.lower()
    card = storage.packs.card(FIND)
    assert card is not None
    result = svc.submit({"answers": typed(card), "reason": 0, "timing": TIMING})
    assert result.outcome == "incorrect"
    assert result.find_error is not None
    assert (result.find_error.step_ok, result.find_error.reason_ok, result.find_error.value_ok) == (
        True,
        False,
        True,
    )
    assert result.find_error.right_reason == 1
    assert result.solution is not None
    assert not result.solution.needs_diagnosis
    assert [s.number for s in result.solution.shown_work] == [1, 2]
    svc.next()
    (graded,) = [a for a in storage.users.attempts(card_id=FIND) if a.final]
    assert (graded.skill_id, graded.rating, graded.extra["highlighted"]) == (FACTOR, 1, True)


def test_find_the_error_comes_at_most_once_in_n_and_can_be_turned_off(storage: Storage) -> None:
    in_review(storage, ARITH, FACTOR)
    uncued_successes(storage, FACTOR)
    users = storage.users
    users.set_setting("queue.find_error_one_in", None)
    svc = StudyService(storage)
    turn = svc.start({"mode": "focused", "skill_id": FACTOR, "count": 1})
    assert turn.type == "summary"  # off: nothing to serve for this skill
    users.set_setting("queue.find_error_one_in", 10)
    users.record_answer(  # a find-the-error item among the last nine problems
        GradedAnswer(
            attempt=Attempt(
                at=clock_of(storage).now_ms() - 1000,
                card_id="old.find",
                card_kind="find-error",
                skill_id=ARITH,
                final=True,
                verdict="correct",
            )
        )
    )
    turn = svc.start({"mode": "focused", "skill_id": FACTOR, "count": 1})
    assert turn.type == "summary"  # its slot is taken until nine more problems
    users.set_setting("queue.find_error_one_in", 5)  # now outside the last four
    for i in range(4):
        users.record_answer(
            GradedAnswer(
                attempt=Attempt(
                    at=clock_of(storage).now_ms() - 900 + i,
                    card_id=f"old.p{i}",
                    card_kind="problem",
                    skill_id=ARITH,
                    final=True,
                    verdict="correct",
                )
            )
        )
    turn = svc.start({"mode": "focused", "skill_id": FACTOR, "count": 1})
    assert turn.problem is not None
    assert turn.problem.card.kind == "find-error"


# ---------------------------------------------------------------- which-method items


def test_which_method_items_only_for_an_active_skill_and_outside_n(storage: Storage) -> None:
    users = storage.users
    in_review(storage, ARITH, FACTOR, METHOD)  # the formula is not learned yet: inactive
    svc = StudyService(storage)
    plan = svc.plan_preview()
    items = [i for i in plan.items if i.skill_id == METHOD]
    assert items
    assert all(i.method and i.slots == 0 for i in items)
    turn = svc.start()
    served = []
    while turn.type == "problem" and turn.problem is not None:
        served.append(turn.problem.card.kind)
        if turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        elif turn.problem.kind == "problem":
            answer_right(svc, storage, turn)
        turn = svc.next()
    assert "method" not in served
    # Active once two of the methods it chooses among are learned.
    in_review(storage, FORMULA)
    clock_of(storage).set(START + timedelta(days=1))
    in_review(storage, METHOD)
    turn = svc.start()
    kinds = []
    while turn.type == "problem" and turn.problem is not None:
        kinds.append(turn.problem.card.kind)
        if turn.problem.card.kind == "method":
            assert turn.problem.attempts_allowed == 1
            assert "which-method" in turn.problem.reason.why
            assert turn.result is None
            assert turn.progress is not None
            total = turn.progress.total
            result = answer_right(svc, storage, turn)
            assert result.outcome == "correct"
            assert result.solution is not None
            assert not result.solution.needs_diagnosis
            assert total == turn.progress.total
        elif turn.problem.kind == "flashcard":
            svc.rate_flashcard(3)
        elif turn.problem.kind == "problem":
            answer_right(svc, storage, turn)
        turn = svc.next()
    assert "method" in kinds
    (graded,) = [a for a in users.attempts(skill_id=METHOD) if a.final]
    assert graded.card_kind == "method"
    assert graded.rating == 3
    assert memory_of(users.skill_state(METHOD)) is not None


# ---------------------------------------------------------------- cloze cards


def test_cloze_text_rendering() -> None:
    text = "A {{c1::one}}, {{c2::two::hint}} and {{c1::uno}}."
    assert blank_numbers(text) == [1, 2]
    assert ords(text) == [0, 1]
    assert front(text, 0) == "A [...], two and [...]."
    assert front(text, 1) == "A one, [hint] and uno."
    assert back(text, 1) == "A one, **two** and uno."
    assert ords(None) == []


def test_cloze_blanks_are_scheduled_one_by_one(storage: Storage) -> None:
    users = storage.users
    cloze_card = storage.packs.card(CLOZE)
    assert cloze_card is not None
    home = cloze_card.section_id
    for section in storage.packs.sections():  # no problems today: flashcards only
        users.set_section_state(section.id, "solid" if section.id == home else "off")
    users.set_setting("daily.new_skills", 0)
    svc = StudyService(storage)
    turn = svc.start()
    views = []
    while turn.type == "problem" and turn.problem is not None:
        if turn.problem.card.id == CLOZE:
            views.append(turn.problem.card)
        if turn.problem.kind == "flashcard":
            first = turn.problem.card.id == CLOZE and len(views) == 1
            svc.rate_flashcard(1 if first else 3)
            turn = svc.next()
        else:
            svc.end()
            break
    assert [v.cloze for v in views] == [1, 1]  # missed, then shown again later (I5)
    assert views[0].back_md is not None
    assert "**subtract" in views[0].back_md
    assert "This works whenever" in views[0].back_md  # the Extra section on the back
    (state,) = [f for f in users.flashcard_states() if f.card_id == CLOZE]
    assert (state.ord, state.lapses) == (0, 0)
    # Next day: c1 (rated Again) is due and c2 waits; the day after, c2 is new.
    clock_of(storage).set(START + timedelta(days=1))
    plan = svc.plan_preview()
    assert [(i.card_id, i.card_ord) for i in plan.items if i.card_id == CLOZE] == [(CLOZE, 0)]
    users.apply([replace(state, due_at=to_ms(START + timedelta(days=30)))])
    plan = svc.plan_preview()
    assert [(i.card_id, i.card_ord) for i in plan.items if i.card_id == CLOZE] == [(CLOZE, 1)]


# ---------------------------------------------------------------- self-graded problems


@pytest.mark.parametrize(("ticked", "rating"), [(2, 3), (1, 2), (0, 1)])
def test_rubric_ticks_rate_a_self_graded_problem(
    storage: Storage, ticked: int, rating: int
) -> None:
    in_review(storage, ARITH, LINEAR)
    only(storage, LINEAR, EXPLAIN)
    svc = StudyService(storage)
    turn = focused(svc, LINEAR)
    assert turn.problem is not None
    assert turn.problem.card.self_graded
    shown = svc.show_solution()
    assert shown.solution is not None
    assert len(shown.solution.rubric) == 2
    assert svc.current().result is None  # nothing graded yet; the problem is still open
    result = svc.submit({"rubric_ticked": ticked, "timing": TIMING})
    assert result.outcome == ("correct" if rating >= 2 else "incorrect")
    svc.next()
    (graded,) = [a for a in storage.users.attempts(card_id=EXPLAIN) if a.final]
    assert (graded.verdict, graded.rating) == ("self", rating)


def self_graded_world(tmp_path: Path) -> Storage:
    records, skills, sections = world_records(("sg",), sections=1, skills=1, seeds=1)
    records.append(
        Card(
            id="sg.proof",
            skill_id=skills[0],
            tier=1,
            answer_type="self",
            question_md="Prove it.",
            solution_md="A proof.",
        )
    )
    pack = tmp_path / "sg.db"
    build_pack(pack, PackInfo(id="sg", title="SG", version="1"), records)  # type: ignore[arg-type]
    storage = Storage.open(
        ProfilePaths(tmp_path / "sgp"),
        pack_paths=[pack],
        clock=FixedClock(START, tz=NY),
        create=True,
    )
    storage.users.set_setting("study.timezone", "America/New_York")
    for section in sections:
        storage.users.set_section_state(section, "solid")
    now = clock_of(storage).now_ms()
    storage.users.apply([review_state(skills[0], now, days_ago=5, stability=2.0)])
    only(storage, skills[0], "sg.proof")
    return storage


@pytest.mark.parametrize(("choice", "rating"), [("matched", 3), ("minor-slip", 1), ("missed", 1)])
def test_self_graded_without_a_rubric_uses_three_buttons(
    tmp_path: Path, choice: str, rating: int
) -> None:
    storage = self_graded_world(tmp_path)
    try:
        svc = StudyService(storage, checker=fake_checker, previewer=fake_preview)
        turn = svc.start({"mode": "focused", "skill_id": "sg.s1.k1", "count": 1})
        assert turn.problem is not None
        assert turn.problem.card.id == "sg.proof"
        shown = svc.show_solution()
        assert shown.solution is not None
        assert shown.solution.rubric == ()
        with pytest.raises(Exception, match="no rubric"):
            svc.submit({"rubric_ticked": 1})
        svc.submit({"self_grade": choice, "timing": TIMING})
        svc.next()
        (graded,) = [a for a in storage.users.attempts(card_id="sg.proof") if a.final]
        assert (graded.verdict, graded.rating) == ("self", rating)
    finally:
        storage.close(backup=False)


# ---------------------------------------------------------------- practice tests (ENG-8)


def test_practice_test_allocation_spreads_and_weights_weak_skills() -> None:
    weights = {"weak": 0.9, "mid": 0.5, "strong": 0.25}
    capacity = {"weak": 9, "mid": 9, "strong": 9}
    spread = practice_test_allocation(weights, capacity, 8, seed="x")
    assert set(spread) == set(weights)
    assert all(n >= 1 for n in spread.values())
    assert sum(spread.values()) == 8
    assert spread["weak"] > spread["mid"] > spread["strong"]
    assert (
        practice_test_allocation(weights, {"weak": 1, "mid": 9, "strong": 9}, 8, seed="x")["weak"]
        == 1
    )
    picks: Counter[str] = Counter()
    for i in range(300):
        picks.update(practice_test_allocation(weights, capacity, 1, seed=f"s{i}"))
    assert picks["weak"] > picks["mid"] > picks["strong"]
    assert practice_test_allocation(weights, capacity, 1, seed="a") == practice_test_allocation(
        weights, capacity, 1, seed="a"
    )


def test_practice_test_on_the_test_pack(storage: Storage) -> None:
    users = storage.users
    now = clock_of(storage).now_ms()
    skills = [k.id for k in storage.packs.skills() if not k.method_choice]
    in_review(storage, *skills, days_ago=1, stability=30.0)  # strong ...
    users.apply([review_state(QUAD, now, days_ago=20, stability=3.0)])  # ... but one
    exam = users.add_exam(
        Exam(
            name="Midterm",
            at=to_ms(START + timedelta(days=7)),
            sections=(storage.packs.sections()[1].id,),
            problems=6,
            minutes=60,
        )
    )
    svc = StudyService(storage)
    turn = svc.start({"mode": "practice-test", "exam_id": exam.id, "timed": True})
    session = users.latest_open_session()
    assert session is not None
    plan = Plan.from_json(session.plan)
    per_skill = Counter(i.skill_id for i in plan.items)
    assert sum(per_skill.values()) == 6
    in_scope = {k.id for k in storage.packs.skills() if k.section_id == exam.sections[0]}
    assert set(per_skill) <= in_scope
    assert METHOD not in per_skill
    assert per_skill[QUAD] == max(per_skill.values())  # weighted toward weaker recall
    assert all(storage.packs.card(i.card_id or "").kind == "problem" for i in plan.items)  # type: ignore[union-attr]
    assert plan.info["limit_ms"] == 60 * 60_000
    # Two answered (one multi-part if drawn), then stopped early: the rest score zero and
    # are logged unrated (C5).
    for _ in range(2):
        assert turn.problem is not None
        assert turn.problem.practice_test
        assert answer_right(svc, storage, turn).outcome == "recorded"
        turn = svc.current()
    summary = svc.end()
    test = summary.test
    assert test is not None
    assert (test.answered, test.correct, test.total, test.unanswered) == (2, 2, 6, "skip")
    assert [x.rating for x in test.lines if not x.answered] == [None, None, None, None]
    assert sum(1 for a in users.attempts() if a.final) == 6


# ---------------------------------------------------------------- backlog (wave 7)


def test_backlog_matched_wrong_answers_step_is_sent_for_the_picker(storage: Storage) -> None:
    in_review(storage, ARITH, LINEAR)
    only(storage, LINEAR, "test.linear.solve.001")  # wrong: 25/3 => ... @1
    svc = StudyService(storage)
    turn = focused(svc, LINEAR)
    assert turn.problem is not None
    assert turn.problem.card.id == "test.linear.solve.001"
    first = svc.submit({"answers": [{"value": "25/3"}], "timing": TIMING})
    assert first.outcome == "retry"
    assert [(p.feedback is not None, p.wrong_step) for p in first.verdicts] == [(True, 1)]
    final = svc.submit({"answers": [{"value": "25/3"}], "timing": TIMING})
    assert final.outcome == "incorrect"
    assert final.solution is not None
    assert final.solution.needs_diagnosis
    assert final.solution.preselect_step == 1  # the picker preselects the step behind it
    assert final.verdicts[0].wrong_step == 1


def test_backlog_a_choice_part_says_whether_several_answers_are_allowed(storage: Storage) -> None:
    critical = "test.calc.critical-points"
    in_review(storage, critical)
    only(storage, critical, "test.deriv.critical-choice.001")
    svc = StudyService(storage)
    turn = focused(svc, critical)
    assert turn.problem is not None
    assert turn.problem.card.id == "test.deriv.critical-choice.001"
    assert [p.multiple for p in turn.problem.card.parts] == [True]  # select all that apply
    single = storage.packs.card(PARABOLA)
    assert single is not None
    views = svc._card_view(single).parts
    choice = [p for p in views if p.answer_type == "choice"]
    assert choice
    assert not any(p.multiple for p in choice)
