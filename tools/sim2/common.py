"""Small shared helpers: seeded random streams, the simulated clock and logistic math."""

import hashlib
import math
import random
from datetime import date
from typing import Final

DAY_MS: Final = 86_400_000
MINUTE_MS: Final = 60_000
SESSION_HOUR_UTC: Final = 18  # every simulated session starts at 18:00 UTC on its study day
EPOCH: Final = date(1970, 1, 1)


def rng_for(*keys: object) -> random.Random:
    """A reproducible random stream named by `keys` (same keys, same stream, any process)."""
    digest = hashlib.sha256(repr(keys).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))  # noqa: S311 - simulation, not security


def unit_hash(*keys: object) -> float:
    """A fixed number in [0, 1) for `keys`."""
    digest = hashlib.sha256(repr(keys).encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def session_ms(day: date) -> int:
    """UTC epoch ms when the study session of `day` starts."""
    return (day - EPOCH).days * DAY_MS + SESSION_HOUR_UTC * 3_600_000


def sigmoid(x: float) -> float:
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    return math.log(p / (1.0 - p))


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
