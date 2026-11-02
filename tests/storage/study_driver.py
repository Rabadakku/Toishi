"""A student driving the real StudyService on the Test pack (DEV-8 kill loop, DEV-9 state
machine): right answers type the key, wrong ones a value no key has.

`key_checker` grades plain kinds (choice, true/false, text) with the real checker in this
process and math kinds by comparing with the key as typed. These tests are about saved
progress, not answer equivalence, and it keeps SymPy's worker process out of every child
the kill loop starts (core/grader is tested on its own).
"""

import sqlite3
from collections.abc import Mapping
from typing import Any, Literal

from core import grader
from core.grader import AnswerSpec, GradeResult, Status
from core.model import Card
from core.queue import AttemptResult, StudyService, Turn
from core.storage import Storage

WRONG = "987654321"
IN_PROCESS = {"choice", "truefalse", "text", "self", "quantity"}
STATE_TABLES = (  # what an answer changes and undo restores (core/storage/rows.py)
    "skill_state",
    "skill_tier",
    "skill_shadow",
    "flashcard_state",
    "card_user",
    "pending_check",
    "weak_spot",
    "diagnostic_set",
)
LOG_TABLES = ("attempt", "review_log", "implicit_credit")

type How = Literal["right", "wrong", "unsure", "give-up", "hint"]


def key_checker(raw: str, spec: AnswerSpec, source: Any) -> GradeResult:
    if spec.answer_type in IN_PROCESS:
        return grader.grade(raw, spec, source)
    ok = raw.strip() == (spec.answer or "").strip()
    return GradeResult(Status.CORRECT if ok else Status.INCORRECT, message="")


def typed(card: Card, right: bool) -> list[dict[str, Any]]:
    def key(answer_type: str, answer: str | None, choices: tuple[Any, ...]) -> str:
        text = answer or ""
        value = text.split(";")[0].strip() if answer_type == "text" else text
        if right:
            return value
        if answer_type == "choice":  # a wrong choice: the first one that is not correct
            return str(next((i + 1 for i, c in enumerate(choices) if not c.correct), 1))
        if answer_type == "truefalse":
            return "false" if value.strip().lower() == "true" else "true"
        return WRONG

    if card.parts:
        return [
            {"part": p.label, "value": key(p.answer_type, p.answer, p.choices)} for p in card.parts
        ]
    return [{"value": key(card.answer_type, card.answer, card.choices)}]


def answer(svc: StudyService, storage: Storage, turn: Turn, how: How) -> AttemptResult | None:
    """Answer the item on screen until its answer is final (saved, graded on continue).
    Returns the final result, or None for a worked example (nothing to answer)."""
    p = turn.problem
    assert p is not None
    timing = {"active_ms": 30_000, "solve_ms": 25_000, "entry_ms": 3_000}
    if p.kind == "example":
        return None
    if p.kind == "flashcard":
        rating = {"right": 3, "unsure": 2, "hint": 3}.get(how, 1)
        return svc.rate_flashcard(rating, timing=timing)
    card = storage.packs.card(p.card.id)
    assert card is not None
    if how == "give-up":
        return svc.give_up(timing)
    if how == "hint" and card.hints:
        svc.hint()
    right = how != "wrong"
    confidence = "unsure" if how == "unsure" else "sure"
    grade = "matched" if right else "missed"
    if p.card.self_graded:
        svc.show_solution()
        return svc.submit({"self_grade": grade, "timing": timing})
    result = svc.submit({"answers": typed(card, right), "confidence": confidence, "timing": timing})
    for _ in range(p.attempts_allowed + 1):
        if result.outcome == "retry":
            result = svc.submit({"answers": typed(card, right), "timing": timing})
        elif result.outcome == "self-grade":
            result = svc.submit({"self_grade": grade, "timing": timing})
        elif result.outcome == "invalid":
            result = svc.give_up(timing)
        else:
            break
    assert result.outcome in ("correct", "incorrect", "recorded"), (card.id, result)
    return result


def table_rows(conn: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]  # noqa: S608


def progress(storage: Storage) -> dict[str, Any]:
    """What undo must restore: the state rows and the non-voided log."""
    with storage.db.reading() as conn:
        out: dict[str, Any] = {t: table_rows(conn, t) for t in STATE_TABLES}
        for t in LOG_TABLES:
            out[t] = [r[0] for r in conn.execute(f"SELECT id FROM {t} WHERE voided_by IS NULL")]  # noqa: S608
    return out


def attempt_ids(storage: Storage) -> set[int]:
    with storage.db.reading() as conn:
        return {int(r[0]) for r in conn.execute("SELECT id FROM attempt")}


def current_key(storage: Storage) -> str | None:
    session = storage.users.latest_open_session()
    current: Mapping[str, Any] = (session.current or {}) if session is not None else {}
    key = current.get("key")
    return None if key is None else str(key)
