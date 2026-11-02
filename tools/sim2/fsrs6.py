"""FSRS-6 memory math with plain floats (py-fsrs 6.3.2 formulas and default weights).

The numbers equal `core.engine.fsrs_adapter.FsrsAdapter.step` and `retrievability_after`
(tests/sim2/test_fsrs6.py checks), without the scheduler object, so truth models and the
stand-in model can call them many thousands of times per simulated semester.
"""

import math
from collections.abc import Sequence
from typing import Final

from fsrs.scheduler import DEFAULT_PARAMETERS

AGAIN: Final = 1
HARD: Final = 2
GOOD: Final = 3
EASY: Final = 4
STABILITY_MIN: Final = 0.001
STABILITY_MAX: Final = 36_500.0  # as fsrs-rs and the adapter


class Fsrs6:
    """FSRS-6 with fixed weights (default: py-fsrs 6.3.2 defaults)."""

    __slots__ = ("decay", "factor", "w")

    def __init__(self, weights: Sequence[float] = ()) -> None:
        self.w: tuple[float, ...] = tuple(weights) if weights else tuple(DEFAULT_PARAMETERS)
        if len(self.w) != 21:
            raise ValueError(f"FSRS-6 needs 21 weights, got {len(self.w)}")
        self.decay = self.w[20]
        self.factor = 0.9 ** (-1.0 / self.decay) - 1.0

    def retrievability(self, elapsed_days: float, stability: float) -> float:
        if elapsed_days <= 0.0:
            return 1.0
        return float((1.0 + self.factor * elapsed_days / stability) ** (-self.decay))

    def stability_for(self, recall: float, elapsed_days: float) -> float:
        """The stability whose retrievability after `elapsed_days` is `recall` (0 < recall < 1)."""
        return float(self.factor * elapsed_days / (recall ** (-1.0 / self.decay) - 1.0))

    def interval(self, stability: float, retention: float) -> float:
        """Fractional days until retrievability falls to `retention`."""
        return float(stability / self.factor * (retention ** (-1.0 / self.decay) - 1.0))

    def initial(self, rating: int) -> tuple[float, float]:
        """(stability, difficulty) after the first review."""
        w = self.w
        stability = max(w[rating - 1], STABILITY_MIN)
        return stability, _clamp_d(w[4] - math.exp(w[5] * (rating - 1)) + 1.0)

    def review(
        self,
        stability: float,
        difficulty: float,
        rating: int,
        elapsed_days: int,
        recall: float | None = None,
    ) -> tuple[float, float]:
        """(stability, difficulty) after a review `elapsed_days` whole study days after the
        previous one (0: the same day, FSRS-6's short-term formula). `recall` replaces the
        retrievability the long-term formulas read (for a clock scaled by phi)."""
        w = self.w
        if elapsed_days <= 0:
            inc = math.exp(w[17] * (rating - 3 + w[18])) * stability ** (-w[19])
            if rating >= HARD:
                inc = max(inc, 1.0)
            new_s = stability * inc
        else:
            r = self.retrievability(float(elapsed_days), stability) if recall is None else recall
            if rating == AGAIN:
                long_term = (
                    w[11]
                    * difficulty ** (-w[12])
                    * ((stability + 1.0) ** w[13] - 1.0)
                    * math.exp((1.0 - r) * w[14])
                )
                new_s = min(long_term, stability / math.exp(w[17] * w[18]))
            else:
                hard = w[15] if rating == HARD else 1.0
                easy = w[16] if rating == EASY else 1.0
                new_s = stability * (
                    1.0
                    + math.exp(w[8])
                    * (11.0 - difficulty)
                    * stability ** (-w[9])
                    * (math.exp((1.0 - r) * w[10]) - 1.0)
                    * hard
                    * easy
                )
        easy_d = w[4] - math.exp(w[5] * (EASY - 1)) + 1.0
        delta = -(w[6] * (rating - 3))
        damped = difficulty + (10.0 - difficulty) * delta / 9.0
        new_d = _clamp_d(w[7] * easy_d + (1.0 - w[7]) * damped)
        return min(max(new_s, STABILITY_MIN), STABILITY_MAX), new_d


def _clamp_d(d: float) -> float:
    return min(max(d, 1.0), 10.0)


DEFAULT: Final = Fsrs6()
