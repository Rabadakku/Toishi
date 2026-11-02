"""ENG-1: the one module that talks to py-fsrs 6.3.2, so FSRS-7 can replace it.

The app runs learning and relearning itself (learning_steps=() and relearning_steps=()),
so every card is a plain FSRS-6 Review card. Differences from calling py-fsrs directly:

- One clock, as in Anki (ADR-0013, C4): the stability update sees whole study days t since
  the last review (0 = the same study day, short-term formula), exactly what the fitter is
  trained on. Fractional-day recall, R(t, S) = (1 + F t/S)^(-w20) with
  F = 0.9^(-1/w20) - 1, is kept for display, sorting and triage only (`retrievability`).
- Stability is capped at 36,500 days, as fsrs-rs does (py-fsrs has no cap).
- Parameters are cleaned before py-fsrs sees them (`clean_parameters`, C1): rounded to 6
  decimals and clamped into the intersection of py-fsrs's bounds and fsrs-rs's clipper,
  because fsrs-rs returns float32 values (0.800000011920929) that py-fsrs rejects.
- Intervals are computed live from stability and the desired retention in force, so a goal
  change reschedules nothing. Fuzz uses py-fsrs's own fuzz ranges but draws its position
  from a hash of (key, last review), so a live recomputation lands on the same day.
- Nothing here reads a clock: every call takes the review instant in UTC ms.
"""

import hashlib
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC
from typing import Final

from fsrs import Rating, Scheduler
from fsrs.scheduler import (
    DEFAULT_PARAMETERS,
    FUZZ_RANGES,
    LOWER_BOUNDS_PARAMETERS,
    UPPER_BOUNDS_PARAMETERS,
)

from core.engine.config import AGAIN, DAY_MS, EASY, PARAM_DECIMALS
from core.engine.days import StudyDays

DEFAULT_PARAMS_ID: Final = "fsrs6-default"
FSRS_VERSION: Final = "py-fsrs 6.3.2"
STABILITY_MAX: Final = 36_500.0

# fsrs-rs 6.6.2 parameter_clipper_v6.rs (short-term on, at most one relearning step).
_CLIPPER: Final = (
    *[(0.001, 100.0)] * 4,
    (1.0, 10.0),
    (0.001, 4.0),
    (0.001, 4.0),
    (0.001, 0.75),
    (0.0, 4.5),
    (0.0, 0.8),
    (0.001, 3.5),
    (0.001, 5.0),
    (0.001, 0.25),
    (0.001, 0.9),
    (0.0, 4.0),
    (0.0, 1.0),
    (1.0, 6.0),
    (0.0, 2.0),
    (0.0, 2.0),
    (0.01, 0.8),
    (0.1, 0.8),
)
# What both py-fsrs and the fsrs-rs clipper accept.
PARAMETER_BOUNDS: Final[tuple[tuple[float, float], ...]] = tuple(
    (max(lo, plo), min(hi, phi))
    for (lo, hi), plo, phi in zip(
        _CLIPPER, LOWER_BOUNDS_PARAMETERS, UPPER_BOUNDS_PARAMETERS, strict=True
    )
)


class ParameterError(ValueError):
    """A parameter vector that cannot be cleaned: wrong length or a non-finite value."""


def clean_parameters(values: Iterable[float]) -> tuple[float, ...]:
    """C1: round to 6 decimals and clamp into PARAMETER_BOUNDS. Raises ParameterError for
    a vector of the wrong length or with a non-finite (or non-numeric) value."""
    try:
        raw = [float(v) for v in values]
    except (TypeError, ValueError) as error:
        raise ParameterError(f"parameters must be numbers: {error}") from error
    if len(raw) != len(PARAMETER_BOUNDS):
        raise ParameterError(f"FSRS-6 needs {len(PARAMETER_BOUNDS)} parameters, got {len(raw)}")
    if not all(math.isfinite(v) for v in raw):
        raise ParameterError("parameters must be finite")
    return tuple(
        min(max(round(v, PARAM_DECIMALS), lo), hi)
        for v, (lo, hi) in zip(raw, PARAMETER_BOUNDS, strict=True)
    )


@dataclass(frozen=True, slots=True)
class Memory:
    """One FSRS card: stability (days), difficulty (1..10), last review (UTC ms)."""

    stability: float
    difficulty: float
    last_review_at: int


def params_id_for(parameters: Sequence[float]) -> str:
    if tuple(parameters) == tuple(DEFAULT_PARAMETERS):
        return DEFAULT_PARAMS_ID
    digest = hashlib.sha256(",".join(f"{w:.6f}" for w in parameters).encode()).hexdigest()
    return f"fit-{digest[:12]}"


class FsrsAdapter:
    """FSRS-6 with the spec's settings. Pure: the same inputs always give the same outputs.

    `days` is the study-day calendar whole-day elapsed time is counted on; Engine passes the
    profile's. Without it, UTC days with the default 4 AM rollover are used."""

    def __init__(
        self,
        parameters: Sequence[float] | None = None,
        *,
        maximum_interval_days: int = 365,
        fuzz: bool = True,
        params_id: str | None = None,
        days: StudyDays | None = None,
    ) -> None:
        params = tuple(DEFAULT_PARAMETERS if parameters is None else parameters)
        self._scheduler = Scheduler(
            parameters=params,
            desired_retention=0.9,
            learning_steps=(),
            relearning_steps=(),
            maximum_interval=maximum_interval_days,
            enable_fuzzing=fuzz,
        )
        self.parameters: tuple[float, ...] = params
        self.maximum_interval_days = maximum_interval_days
        self.fuzz = fuzz
        self.params_id = params_id or params_id_for(params)
        self.decay = params[20]
        self.factor = 0.9 ** (-1.0 / self.decay) - 1.0
        self.days = days or StudyDays(UTC)

    def with_days(self, days: StudyDays) -> FsrsAdapter:
        """The same model counting whole days on another calendar."""
        if days == self.days and days.pinned == self.days.pinned:
            return self
        return FsrsAdapter(
            self.parameters,
            maximum_interval_days=self.maximum_interval_days,
            fuzz=self.fuzz,
            params_id=self.params_id,
            days=days,
        )

    # ------------------------------------------------------------ memory model

    def retrievability_after(self, elapsed_days: float, stability: float) -> float:
        t = max(0.0, elapsed_days)
        return float((1.0 + self.factor * t / stability) ** (-self.decay))

    def retrievability(self, memory: Memory, at_ms: int) -> float:
        """Predicted recall at an instant, from fractional days since the last review. For
        display, sorting and triage; the stability update uses `recall_days` (C4)."""
        return self.retrievability_after((at_ms - memory.last_review_at) / DAY_MS, memory.stability)

    def elapsed_days(self, memory: Memory, at_ms: int) -> int:
        """Whole study days since the last review (0 = the same study day)."""
        return max(0, self.days.between(memory.last_review_at, at_ms))

    def recall_days(self, memory: Memory, at_ms: int) -> float:
        """Predicted recall on whole study days: what the stability update and the fitter see."""
        return self.retrievability_after(self.elapsed_days(memory, at_ms), memory.stability)

    def elapsed_for(self, recall: float, stability: float) -> float:
        """Fractional days until recall falls to the given value (inverse of R)."""
        return float(stability / self.factor * (recall ** (-1.0 / self.decay) - 1.0))

    def step(
        self, state: tuple[float, float] | None, rating: int, elapsed_days: int
    ) -> tuple[float, float]:
        """(stability, difficulty) after one review `elapsed_days` whole days after the
        previous one (0: the same day, short-term formula). state None: the first review."""
        return self.step_fractional(state, rating, elapsed_days, same_day=elapsed_days <= 0)

    def step_fractional(
        self,
        state: tuple[float, float] | None,
        rating: int,
        elapsed_days: float,
        *,
        same_day: bool,
    ) -> tuple[float, float]:
        """`step` with fractional elapsed days and an explicit same-day flag.

        `same_day` selects the short-term formula whatever the elapsed time; otherwise the
        long-term update sees recall after `elapsed_days` (fractional) days. The student
        model's component memory uses it (design 3.4): it decides "same day" on the study
        day and scales elapsed time by the student's time factor. `step(state, rating, t)`
        is `step_fractional(state, rating, t, same_day=t <= 0)`."""
        if rating not in (1, 2, 3, 4):
            raise ValueError(f"rating must be 1..4, got {rating}")
        grade = Rating(rating)
        s = self._scheduler
        if state is None:
            stability = s._initial_stability(rating=grade)
            difficulty = s._initial_difficulty(rating=grade, clamp=True)
            return min(float(stability), STABILITY_MAX), float(difficulty)
        old_s, old_d = state
        if same_day:
            stability = s._short_term_stability(stability=old_s, rating=grade)
        else:
            stability = s._next_stability(
                difficulty=old_d,
                stability=old_s,
                retrievability=self.retrievability_after(elapsed_days, old_s),
                rating=grade,
            )
        difficulty = s._next_difficulty(difficulty=old_d, rating=grade)
        return min(float(stability), STABILITY_MAX), float(difficulty)

    def review(
        self,
        memory: Memory | None,
        rating: int,
        at_ms: int,
        *,
        same_day: bool | None = None,
        elapsed_days: int | None = None,
    ) -> Memory:
        """The card after one review. Also the next-state preview (it changes nothing).

        The update sees whole study days t on `self.days` (C4). `same_day` (what
        lifecycle.review_on passes) forces t = 0, or t >= 1 when False; `elapsed_days`
        gives t directly. Without either, t is counted on `self.days`."""
        if memory is None:
            return Memory(*self.step(None, rating, 0), at_ms)
        if elapsed_days is not None:
            t = max(0, elapsed_days)
        elif same_day:
            t = 0
        else:
            t = self.elapsed_days(memory, at_ms)
            if same_day is not None:
                t = max(t, 1)
        stability, difficulty = self.step((memory.stability, memory.difficulty), rating, t)
        return Memory(stability, difficulty, at_ms)

    def next_states(
        self, memory: Memory | None, at_ms: int, *, same_day: bool | None = None
    ) -> dict[int, Memory]:
        """Preview all four ratings at an instant."""
        return {
            rating: self.review(memory, rating, at_ms, same_day=same_day)
            for rating in range(AGAIN, EASY + 1)
        }

    def replay(
        self, reviews: Iterable[tuple[int, int]], days: StudyDays | None = None
    ) -> Memory | None:
        """Create a card from (rating, at_ms) pairs in time order (ENG-2). Same as
        sequential lifecycle.review_on on `days` (default: the adapter's own)."""
        cal = days or self.days
        memory: Memory | None = None
        for rating, at_ms in reviews:
            t = 0 if memory is None else max(0, cal.between(memory.last_review_at, at_ms))
            memory = self.review(memory, rating, at_ms, elapsed_days=t)
        return memory

    # ------------------------------------------------------------ intervals

    def raw_interval(self, stability: float, retention: float) -> float:
        if not 0.0 < retention < 1.0:
            raise ValueError(f"retention must be within (0, 1), got {retention}")
        return self.elapsed_for(retention, stability)

    def interval_days(self, stability: float, retention: float, fuzz_key: str | None) -> int:
        """Whole days to the next review (py-fsrs rounding, 1..maximum), fuzzed by key."""
        days = round(self.raw_interval(stability, retention))
        days = min(max(days, 1), self.maximum_interval_days)
        if not self.fuzz or fuzz_key is None or days < 2.5:
            return days
        low, high = self.fuzz_range(days)
        position = _unit_hash(fuzz_key)
        return min(low + math.floor(position * (high - low + 1)), high)

    def fuzz_range(self, days: int) -> tuple[int, int]:
        """py-fsrs's fuzz bounds for an interval (same FUZZ_RANGES table)."""
        delta = 1.0
        for band in FUZZ_RANGES:
            delta += band["factor"] * max(min(float(days), band["end"]) - band["start"], 0.0)
        low = max(2, round(days - delta))
        high = min(round(days + delta), self.maximum_interval_days)
        return min(low, high), high


def _unit_hash(key: str) -> float:
    digest = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64
