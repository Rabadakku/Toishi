"""Attempt rows -> the student model's observations (wave 2, docs/design/wave2-integration.md
section 3, `observations.py`; student-model design 3.4).

Rows that are not voided become `Observation`s in (at, id) order:

- **The first try of a presentation** (`attempt_number = 1`) is the observation. `correct` is its
  verdict, so a non-final first row (a "Not quite" the student then retried) is a wrong first
  try. A self-graded first try (verdict self, or undecided then self-graded) is correct when the
  self-grade says so: `extra.correct` on v3 rows, the strict label (`extra.strict_ok`, else a
  Good rating) on older ones.
- **Aided** (a failure whatever the verdict): a give-up before any answer, a worked example
  opened before answering, or (rows before v3) a hint before answering.
- `matched_wrong` is the column; `minutes` is `valid_minutes` on v3 rows. Older rows derive it
  from the speed time the old engine stored (`extra.speed_ms`: solve time plus the typing
  allowance, capped, TIME-4/5) when the first try is correct and its timing is valid under
  `core.engine.timing.excluded_from_baseline`; otherwise it is None.
- `role` is the column; rows before v3 count as growth.
- **Multi-part cards** give one observation per part, from the final row's `extra.parts`: correct
  when right on the part's first attempt and not given up, aided when given up before any
  answer. Parts are untimed. The per-part "Not quite" rows are not observations.
- Not observations: flashcards and clozes; worked examples and problems shown solved (verdict
  shown); find-the-error and which-method items; practice-test problems never answered (the
  student never saw them); rows whose card is no longer a loaded problem.

`observations_of` turns one row into its observations, so the engine reads only the rows a
log has gained since it last looked.
"""

import math
from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

from core.engine.config import BASELINE_LONG_PAUSE_MS
from core.learner.types import ROLES, Observation
from core.model import Attempt
from core.practice.catalog import Catalog

PRE_V3_ROLE = "growth"
SELF_VERDICTS = frozenset({"self", "undecided"})
MS_PER_MINUTE = 60_000.0


def is_first_try_row(attempt: Attempt) -> bool:
    """Rows that can carry an observation (the cheap test before the catalog is consulted)."""
    if attempt.card_kind != "problem" or attempt.voided_by is not None:
        return False
    if attempt.verdict == "shown" or attempt.extra.get("unanswered"):
        return False
    if attempt.extra.get("parts"):
        return attempt.final
    return attempt.part is None and attempt.attempt_number == 1


def observations_of(attempt: Attempt, catalog: Catalog) -> tuple[Observation, ...]:
    """The observations one row carries (none for most rows)."""
    if attempt.id is None or not is_first_try_row(attempt):
        return ()
    day = date.fromisoformat(attempt.study_day) if attempt.study_day else None
    if day is None:
        return ()
    role = attempt.role if attempt.role in ROLES else PRE_V3_ROLE
    parts = attempt.extra.get("parts")
    if parts:
        return tuple(_part_observations(attempt, attempt.id, catalog, parts, day, role))
    problem = catalog.problem(attempt.card_id)
    if problem is None:
        return ()
    aided = (
        (attempt.verdict == "gave-up")
        or attempt.example_opened
        or (attempt.role is None and attempt.hints_used > 0)
    )
    correct = _correct(attempt)
    return (
        Observation(
            attempt_id=attempt.id,
            at_ms=attempt.at,
            study_day=day,
            problem=problem,
            correct=correct,
            aided=aided,
            matched_wrong=attempt.matched_wrong,
            minutes=minutes_of(attempt) if correct and not aided else None,
            role=role,
        ),
    )


def minutes_of(attempt: Attempt) -> float | None:
    """A correct first try's valid solving minutes (see the module docstring)."""
    if attempt.role is not None or attempt.valid_minutes is not None:
        value = attempt.valid_minutes
        return value if value is not None and math.isfinite(value) and value > 0 else None
    speed = attempt.extra.get("speed_ms")
    if not isinstance(speed, int | float) or isinstance(speed, bool) or speed <= 0:
        return None
    if (
        attempt.untimed
        or attempt.solve_ms is None
        or (attempt.longest_pause_ms or 0) > BASELINE_LONG_PAUSE_MS
        or attempt.after_wake
        or attempt.hints_used > 0
        or attempt.example_opened
    ):
        return None
    return float(speed) / MS_PER_MINUTE


def _correct(attempt: Attempt) -> bool:
    if attempt.verdict in SELF_VERDICTS:
        own = attempt.extra.get("correct")
        if isinstance(own, bool):
            return own
        strict = attempt.extra.get("strict_ok")
        if isinstance(strict, bool):
            return strict
        return (attempt.rating or 0) >= 3
    return attempt.verdict == "correct"


def _part_observations(
    attempt: Attempt, attempt_id: int, catalog: Catalog, parts: Any, day: date, role: str
) -> Iterable[Observation]:
    for entry in parts if isinstance(parts, list) else ():
        if not isinstance(entry, Mapping):
            continue
        problem = catalog.problem(attempt.card_id, str(entry.get("label")))
        if problem is None:
            continue
        tries = int(entry.get("attempts", 1) or 1)
        gave_up = bool(entry.get("gave_up"))
        aided = (gave_up and tries <= 1) or attempt.example_opened
        correct = bool(entry.get("correct")) and tries == 1 and not gave_up
        yield Observation(
            attempt_id=attempt_id,
            at_ms=attempt.at,
            study_day=day,
            problem=problem,
            correct=correct,
            aided=aided,
            matched_wrong=None,
            minutes=None,  # parts are untimed
            role=role,
        )


def build_observations(attempts: Iterable[Attempt], catalog: Catalog) -> list[Observation]:
    """Every observation of `attempts` (voided rows are skipped), in (at, id) order."""
    out = [o for a in attempts for o in observations_of(a, catalog)]
    out.sort(key=order)
    return out


def order(obs: Observation) -> tuple[int, int]:
    """Replay order (C3): time, then attempt id."""
    return obs.at_ms, obs.attempt_id
