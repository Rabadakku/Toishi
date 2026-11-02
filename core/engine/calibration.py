"""Calibration (ENG-11, I1, I8) and the fit entry points (ENG-12; ADR-0013).

Every rated review stores the recall FSRS predicted for it (ReviewEvent.predicted_recall,
fractional days, as shown) and its outcome (rating > Again). Calibration that doesn't cry
wolf:
- Ten equal-width bins, each with a 95% Wilson interval on its observed rate. Bins under
  30 reviews are greyed out and never alarm. A bin alarms when its mean prediction falls
  outside its continuity-corrected Wilson interval at the Bonferroni-adjusted level
  alpha/m (m = bins shown), so a well-calibrated model alarms in under 5% of runs.
- Series: core reviews, the strict label on the same reviews (first try, no hint, final
  answer correct), and the settled, stretch and post-stretch events, each on its own
  (their predictions are rebuilt from the memory before the event when not logged).
- True retention as in Anki's Stats: the first interday review of each card per study day,
  young (< 21 days since the last review) and mature, with Wilson intervals and the mean
  predicted recall to compare with.

The fit offer counts long-term training items (histories.training_items); fitting is
automatic and guarded (Engine.auto_fit / Engine.fit, fitting.py).
"""

import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from statistics import NormalDist
from typing import Any

from core.engine.config import (
    AGAIN,
    CALIBRATION_ALPHA,
    CALIBRATION_BINS,
    CALIBRATION_MIN_BIN,
    FIT_MIN_ITEMS,
    MATURE_DAYS,
    RULES_VERSION,
)
from core.engine.fitting import FitUnavailable, fitter_installed
from core.engine.fitting import fit as fit_items
from core.engine.fsrs_adapter import FsrsAdapter, Memory, params_id_for
from core.engine.histories import (
    Item,
    Kind,
    build_histories,
    strict_ok_of,
    training_items,
)
from core.engine.param_sets import SKILLS_SET, load_set
from core.model import Attempt, ReviewEvent

__all__ = [
    "CalibrationBin",
    "CalibrationReport",
    "FitOffer",
    "FitResult",
    "FitUnavailable",
    "RetentionRow",
    "TrueRetention",
    "calibrate",
    "calibration_by_course",
    "calibration_series",
    "fit_offer",
    "fit_parameters",
    "fitter_installed",
    "predicted_of",
    "qualifying_reviews",
    "review_histories",
    "review_pairs",
    "stored_parameters",
    "true_retention",
    "wilson",
]


def wilson(
    successes: int, n: int, *, alpha: float = 0.05, continuity: bool = False
) -> tuple[float, float]:
    """Two-sided Wilson score interval; `continuity`: with Newcombe's continuity correction
    (used for the alarm, whose coverage must hold for 30-review bins near 0 or 1)."""
    if n <= 0:
        return 0.0, 1.0
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = successes / n
    if not continuity:
        denom = 1.0 + z * z / n
        centre = (p + z * z / (2 * n)) / denom
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        low = 0.0 if successes == 0 else max(0.0, centre - half)
        return low, 1.0 if successes == n else min(1.0, centre + half)
    q = 1.0 - p
    denom2 = 2.0 * (n + z * z)
    low = 0.0
    if successes > 0:
        root = math.sqrt(z * z - 2 - 1 / n + 4 * p * (n * q + 1))
        low = max(0.0, (2 * n * p + z * z - 1 - z * root) / denom2)
    high = 1.0
    if successes < n:
        root = math.sqrt(z * z + 2 - 1 / n + 4 * p * (n * q - 1))
        high = min(1.0, (2 * n * p + z * z + 1 + z * root) / denom2)
    return low, high


@dataclass(frozen=True, slots=True, kw_only=True)
class CalibrationBin:
    low: float
    high: float
    n: int
    predicted: float
    observed: float
    ci_low: float = 0.0  # 95% interval on the observed rate
    ci_high: float = 1.0
    alarm: bool = False  # mean prediction outside the Bonferroni-adjusted interval

    @property
    def error(self) -> float:
        return self.observed - self.predicted

    @property
    def greyed(self) -> bool:
        return self.n < CALIBRATION_MIN_BIN

    @property
    def notice(self) -> bool:
        return self.alarm


@dataclass(frozen=True, slots=True, kw_only=True)
class CalibrationReport:
    bins: tuple[CalibrationBin, ...]
    total: int
    alpha: float = CALIBRATION_ALPHA

    @property
    def alarm(self) -> bool:
        return any(b.alarm for b in self.bins)

    @property
    def notice(self) -> bool:
        return self.alarm

    @property
    def expected(self) -> float:
        """Mean predicted recall (expected retention)."""
        return sum(b.predicted * b.n for b in self.bins) / self.total if self.total else 0.0

    @property
    def observed(self) -> float:
        return sum(b.observed * b.n for b in self.bins) / self.total if self.total else 0.0

    @property
    def mean_error(self) -> float:
        """Review-weighted observed minus predicted, over all bins."""
        return self.observed - self.expected if self.total else 0.0

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(round(self.observed * self.total), self.total)


def calibrate(
    pairs: Iterable[tuple[float, bool]], *, alpha: float = CALIBRATION_ALPHA
) -> CalibrationReport:
    """Bin (predicted recall, success) pairs into ten equal-width bins."""
    sums: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for predicted, success in pairs:
        i = min(int(predicted * CALIBRATION_BINS), CALIBRATION_BINS - 1)
        acc = sums[i]
        acc[0] += 1
        acc[1] += predicted
        acc[2] += 1.0 if success else 0.0
    shown = sum(1 for acc in sums.values() if acc[0] >= CALIBRATION_MIN_BIN)
    bins = []
    for i, (n, pred_sum, ok) in sorted(sums.items()):
        count = int(n)
        predicted = pred_sum / n
        ci = wilson(int(ok), count)
        alarm = False
        if count >= CALIBRATION_MIN_BIN:
            low, high = wilson(int(ok), count, alpha=alpha / max(shown, 1), continuity=True)
            alarm = not low <= predicted <= high
        bins.append(
            CalibrationBin(
                low=i / CALIBRATION_BINS,
                high=(i + 1) / CALIBRATION_BINS,
                n=count,
                predicted=predicted,
                observed=ok / n,
                ci_low=ci[0],
                ci_high=ci[1],
                alarm=alarm,
            )
        )
    return CalibrationReport(bins=tuple(bins), total=sum(b.n for b in bins), alpha=alpha)


def review_pairs(events: Iterable[ReviewEvent]) -> list[tuple[float, bool]]:
    return [
        (e.predicted_recall, e.rating > AGAIN)
        for e in events
        if e.predicted_recall is not None and e.voided_by is None
    ]


def calibration_by_course(
    events: Iterable[ReviewEvent], course_of: Callable[[str], str | None]
) -> dict[str, CalibrationReport]:
    grouped: dict[str, list[ReviewEvent]] = defaultdict(list)
    for e in events:
        if e.target_kind == "skill":
            grouped[course_of(e.target_id) or ""].append(e)
    return {course: calibrate(review_pairs(evs)) for course, evs in sorted(grouped.items())}


def predicted_of(e: ReviewEvent, adapter: FsrsAdapter) -> float | None:
    """The logged prediction, or the one rebuilt from the memory before the event."""
    if e.predicted_recall is not None:
        return e.predicted_recall
    before = e.state_before or {}
    s, d, last = before.get("stability"), before.get("difficulty"), before.get("last_review_at")
    if s is None or d is None or last is None:
        return None
    return adapter.retrievability(Memory(float(s), float(d), int(last)), e.at)


SERIES = ("core", "strict", "settled", "stretch", "post-stretch")


def calibration_series(
    events: Sequence[ReviewEvent],
    *,
    attempts: Mapping[int, Attempt],
    day_of: Callable[[int], date],
    adapter_of: Callable[[ReviewEvent], FsrsAdapter],
) -> dict[str, CalibrationReport]:
    """I1: ENG-11 over every rated event, with settled, stretch and post-stretch events as
    their own series, and the strict label beside the rated outcome of core reviews."""
    kinds: dict[int, Kind] = {}
    for h in build_histories(events, day_of=day_of, attempts=attempts):
        for step in h.steps:
            if step.event_id is not None:
                kinds[step.event_id] = step.kind
    pairs: dict[str, list[tuple[float, bool]]] = {name: [] for name in SERIES}
    for e in events:
        if e.voided_by is not None or e.id is None:
            continue
        kind = kinds.get(e.id)
        if kind is None or kind in ("learning", "learning-failed"):
            continue
        predicted = predicted_of(e, adapter_of(e))
        if predicted is None:
            continue
        success = e.rating > AGAIN
        series = "core" if kind == "review" else kind
        pairs[series].append((predicted, success))
        attempt = attempts.get(e.attempt_id) if e.attempt_id is not None else None
        if series == "core" and attempt is not None and e.at == attempt.at:
            pairs["strict"].append((predicted, strict_ok_of(attempt)))
    return {name: calibrate(p) for name, p in pairs.items()}


@dataclass(frozen=True, slots=True, kw_only=True)
class RetentionRow:
    n: int
    passed: int
    expected: float  # mean predicted recall of the same reviews
    ci_low: float
    ci_high: float

    @property
    def observed(self) -> float:
        return self.passed / self.n if self.n else 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class TrueRetention:
    young: RetentionRow
    mature: RetentionRow
    total: RetentionRow


def _row(rows: Sequence[tuple[bool, float]]) -> RetentionRow:
    n = len(rows)
    passed = sum(1 for ok, _ in rows if ok)
    low, high = wilson(passed, n)
    expected = sum(p for _, p in rows) / n if n else 0.0
    return RetentionRow(n=n, passed=passed, expected=expected, ci_low=low, ci_high=high)


def true_retention(
    events: Iterable[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    adapter_of: Callable[[ReviewEvent], FsrsAdapter],
) -> TrueRetention:
    """Anki's true retention: per card and study day, the first review at least a day after
    the previous one; Again fails, anything else passes; mature from 21 days."""
    by_target: dict[tuple[str, str, int], list[ReviewEvent]] = defaultdict(list)
    for e in sorted(events, key=lambda e: (e.at, e.id or 0)):
        if e.voided_by is None:
            by_target[(e.target_kind, e.target_id, e.target_ord)].append(e)
    young: list[tuple[bool, float]] = []
    mature: list[tuple[bool, float]] = []
    for evs in by_target.values():
        seen_days: set[date] = set()
        prev: ReviewEvent | None = None
        for e in evs:
            day = day_of(e.at)
            if prev is not None and day not in seen_days:
                elapsed = (day - day_of(prev.at)).days
                if elapsed >= 1:
                    seen_days.add(day)
                    predicted = predicted_of(e, adapter_of(e))
                    row = (e.rating > AGAIN, 0.0 if predicted is None else predicted)
                    (mature if elapsed >= MATURE_DAYS else young).append(row)
            prev = e
    return TrueRetention(young=_row(young), mature=_row(mature), total=_row(young + mature))


# ---------------------------------------------------------------- ENG-12


def _long_term(e: ReviewEvent, day_of: Callable[[int], date]) -> bool:
    before = e.state_before or {}
    last = before.get("last_review_at")
    return last is not None and (day_of(e.at) - day_of(int(last))).days >= 1


def qualifying_reviews(
    events: Iterable[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    rules_version: str = RULES_VERSION,
) -> list[ReviewEvent]:
    """Long-term skill reviews under the current rules (not voided)."""
    return [
        e
        for e in events
        if e.target_kind == "skill"
        and e.voided_by is None
        and e.rules_version == rules_version
        and _long_term(e, day_of)
    ]


@dataclass(frozen=True, slots=True, kw_only=True)
class FitOffer:
    domain: str
    qualifying: int  # long-term training items
    needed: int
    fitter_installed: bool

    @property
    def offer(self) -> bool:
        return self.qualifying >= self.needed


def fit_offer(
    events: Iterable[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    domain: str = SKILLS_SET,
    domain_of: Callable[[str], str] | None = None,
    attempts: Mapping[int, Attempt] | None = None,
) -> FitOffer:
    chosen = [
        e
        for e in events
        if e.target_kind == "skill" and (domain_of is None or domain_of(e.target_id) == domain)
    ]
    items = training_items(build_histories(chosen, day_of=day_of, attempts=attempts))
    return FitOffer(
        domain=domain,
        qualifying=len(items),
        needed=FIT_MIN_ITEMS,
        fitter_installed=fitter_installed(),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class FitResult:
    parameters: tuple[float, ...]
    params_id: str
    items: int
    reviews: int


def review_histories(
    events: Sequence[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    rules_version: str = RULES_VERSION,
    attempts: Mapping[int, Attempt] | None = None,
) -> list[list[tuple[int, int]]]:
    """Per-card (rating, whole days since the previous review) sequences that start at a
    first review (histories.build_histories; seeded histories are left out)."""
    return [
        h.reviews
        for h in build_histories(
            events, day_of=day_of, attempts=attempts, rules_version=rules_version
        )
        if not h.anchored
    ]


def fit_parameters(
    events: Sequence[ReviewEvent],
    *,
    day_of: Callable[[int], date],
    rules_version: str = RULES_VERSION,
    attempts: Mapping[int, Attempt] | None = None,
) -> FitResult:
    """Fit FSRS-6 parameters on the events' training items (cleaned, C1). Adopting them is
    a separate decision (fitting.adoption, C2)."""
    histories = build_histories(
        events, day_of=day_of, attempts=attempts, rules_version=rules_version
    )
    items: list[Item] = training_items(histories)
    params = fit_items(items)
    return FitResult(
        parameters=params,
        params_id=params_id_for(params),
        items=len(items),
        reviews=sum(len(h.steps) for h in histories if not h.anchored),
    )


def stored_parameters(
    settings: Mapping[str, Any], domain: str = SKILLS_SET
) -> tuple[float, ...] | None:
    """Stored parameters of a set, cleaned (C1); None when absent or unusable."""
    found = load_set(settings, domain)
    return None if found.source == "default" else found.parameters
