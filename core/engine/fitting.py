"""ENG-12 fitting with Anki's guard rails (C1, C2, I7, I8; ADR-0013).

- Items come from `histories.training_items` (whole study days, the same clock the
  stability update uses).
- The fitter is fsrs-rs-python 0.9.3 (it ships with the app), trained for 8 epochs as Anki
  does, starting from the defaults. Its result is cleaned (C1) before anything uses it.
- A candidate is adopted only when it wins: lower recency-weighted log loss than the
  current set on the same items (fsrs-rs `evaluate`, Anki params.rs L148-180), and above
  300 items also lower held-out log loss on a 5-fold time-ordered split (each fold trains
  on every earlier segment; segment = N/6) plus Anki's health check (adjusted log loss
  <= 1.11 or adjusted RMSE(bins) <= 1.53, params.rs L66-77, L182-198).
- `log_loss` and `rmse_bins` reproduce fsrs-rs's own numbers: they accumulate in float32
  the way fsrs-rs does, so the stats screen and the fitter agree to the last digit.
"""

import math
import struct
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Final

import fsrs_rs_python  # imported statically so PyInstaller bundles it (ADR-0013)

from core.engine.config import (
    FIT_EPOCHS,
    FIT_MIN_ITEMS,
    HEALTH_MAX_LOG_LOSS,
    HEALTH_MAX_RMSE,
    HELD_OUT_FOLDS,
)
from core.engine.fsrs_adapter import FsrsAdapter, ParameterError, clean_parameters, params_id_for
from core.engine.histories import Item

FIT_PACKAGE: Final = "fsrs_rs_python"


class FitUnavailable(RuntimeError):
    """Kept for callers of the old optional fitter; fsrs-rs-python now always ships."""


def fitter() -> Any:
    """The fitter module (kept as a seam for tests and FSRS-7)."""
    return fsrs_rs_python


def fitter_installed() -> bool:
    return True


# ---------------------------------------------------------------- float32 arithmetic


def f32(x: float) -> float:
    """Round to the nearest float32, as fsrs-rs stores every number."""
    return float(struct.unpack("f", struct.pack("f", x))[0])


# ---------------------------------------------------------------- predictions


def predictions(parameters: Sequence[float], items: Sequence[Item]) -> list[float]:
    """Recall FSRS predicts for each item's target from its prefix (whole days)."""
    model = FsrsAdapter(clean_parameters(parameters), fuzz=False)
    cache: dict[tuple[Any, ...], tuple[float, float] | None] = {}
    out: list[float] = []
    for item in items:
        state = _prefix_state(model, item, cache)
        if state is None:  # an item always has a prefix; kept total for safety
            out.append(0.5)
            continue
        out.append(model.retrievability_after(item.reviews[-1][1], state[0]))
    return out


def _prefix_state(
    model: FsrsAdapter, item: Item, cache: dict[tuple[Any, ...], tuple[float, float] | None]
) -> tuple[float, float] | None:
    state: tuple[float, float] | None = None
    for k in range(len(item.reviews) - 1):
        key = (item.key, item.reviews[: k + 1])
        if key in cache:
            state = cache[key]
            continue
        rating, delta = item.reviews[k]
        state = model.step(state, rating, delta if k else 0)
        cache[key] = state
    return state


def labels(items: Sequence[Item]) -> list[float]:
    return [1.0 if item.reviews[-1][0] > 1 else 0.0 for item in items]


def recency_weights(n: int) -> list[float]:
    """fsrs-rs: 0.25 + 0.75 (i / (n - 1))^3, oldest item first."""
    length = f32(max(n - 1.0, 1.0))
    return [f32(0.25 + f32(0.75 * f32(f32(i / length) ** 3))) for i in range(n)]


def log_loss(preds: Sequence[float], ys: Sequence[float], weights: Sequence[float]) -> float:
    """fsrs-rs weighted_binary_cross_entropy, accumulated in float32."""
    loss = 0.0
    total = 0.0
    lo, hi = f32(0.0001), f32(0.9999)
    for p, y, w in zip(preds, ys, weights, strict=True):
        r = min(max(f32(p), lo), hi)
        term = f32(f32(y * f32(math.log(r))) + f32((1.0 - y) * f32(math.log(f32(1.0 - r)))))
        loss = f32(loss + f32(term * f32(w)))
        total = f32(total + f32(w))
    return f32(-loss / total) if total else 0.0


def r_matrix_index(item: Item) -> tuple[int, int, int]:
    """fsrs-rs dataset.rs r_matrix_index: (delta_t bin x100, length bin, lapse bin)."""
    delta_t = float(item.reviews[-1][1])
    dt_bin = round(2.48 * 3.62 ** math.floor(math.log(delta_t, 3.62)) * 100.0)
    length = sum(1 for _, d in item.reviews if d >= 1) + 1.0
    len_bin = round(1.99 * 1.89 ** math.floor(math.log(length, 1.89)))
    lapses = sum(1 for r, d in item.reviews[:-1] if r == 1 and d >= 1)
    if lapses == 0:
        return dt_bin, len_bin, 0
    return dt_bin, len_bin, round(1.65 * 1.73 ** math.floor(math.log(lapses, 1.73)))


def rmse_bins(
    items: Sequence[Item],
    preds: Sequence[float],
    weights: Sequence[float],
) -> float:
    """fsrs-rs RMSE(bins): per-bin mean predicted vs observed, weighted, float32."""
    acc: dict[tuple[int, int, int], list[float]] = {}
    for item, p, y, w in zip(items, preds, labels(items), weights, strict=True):
        v = acc.setdefault(r_matrix_index(item), [0.0, 0.0, 0.0, 0.0])
        v[0] = f32(v[0] + f32(p))
        v[1] = f32(v[1] + y)
        v[2] = f32(v[2] + 1.0)
        v[3] = f32(v[3] + f32(w))
    num = 0.0
    den = 0.0
    for k in sorted(acc):
        pred, real, count, weight = acc[k]
        diff = f32(f32(pred / count) - f32(real / count))
        num = f32(num + f32(f32(diff * diff) * weight))
        den = f32(den + weight)
    return f32(math.sqrt(f32(num / den))) if den else 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class Evaluation:
    log_loss: float
    rmse_bins: float
    items: int


def evaluate(
    parameters: Sequence[float], items: Sequence[Item], *, weighted: bool = True
) -> Evaluation:
    """fsrs-rs `FSRS.evaluate` in Python (recency-weighted unless `weighted` is False, as
    in fsrs-rs's held-out folds)."""
    if not items:
        return Evaluation(log_loss=0.0, rmse_bins=0.0, items=0)
    preds = predictions(parameters, items)
    weights = recency_weights(len(items)) if weighted else [1.0] * len(items)
    return Evaluation(
        log_loss=log_loss(preds, labels(items), weights),
        rmse_bins=rmse_bins(items, preds, weights),
        items=len(items),
    )


# ---------------------------------------------------------------- health check


def retention_of(items: Sequence[Item]) -> float:
    return sum(labels(items)) / len(items) if items else 0.0


def log_loss_adjustment(r: float) -> float:
    return float(0.623 * (4.0 * r * (1.0 - r)) ** 0.738)


def rmse_adjustment(r: float, count: int) -> float:
    return float(0.0135 / (r**0.504 - 1.14) + 0.176 / ((count / 1000.0) ** 0.825 + 2.22) + 0.101)


def health_thresholds(r: float, count: int) -> tuple[float, float]:
    """(log loss, RMSE(bins)) at or under which the health check passes."""
    return (
        HEALTH_MAX_LOG_LOSS * log_loss_adjustment(r),
        HEALTH_MAX_RMSE * rmse_adjustment(r, count),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class HeldOut:
    """Out-of-sample numbers on the 5 time-ordered folds (unweighted, as fsrs-rs)."""

    candidate: Evaluation  # each fold fitted on everything before it
    current: Evaluation  # the parameters in force, on the same test items
    retention: float  # share of all items recalled (Anki's r)
    items: int  # all items (Anki's count)

    @property
    def thresholds(self) -> tuple[float, float]:
        return health_thresholds(self.retention, self.items)

    @property
    def baseline_rmse(self) -> float:
        return rmse_adjustment(self.retention, self.items)

    @property
    def adjusted_log_loss(self) -> float:
        return self.candidate.log_loss / log_loss_adjustment(self.retention)

    @property
    def adjusted_rmse(self) -> float:
        return self.candidate.rmse_bins / rmse_adjustment(self.retention, self.items)

    @property
    def healthy(self) -> bool:
        return (
            self.adjusted_log_loss <= HEALTH_MAX_LOG_LOSS or self.adjusted_rmse <= HEALTH_MAX_RMSE
        )


# ---------------------------------------------------------------- fitting


class FitError(Exception):
    """fsrs-rs-python could not fit or evaluate these items (ADR-0019 item 8)."""


def validate_items(items: Sequence[Item]) -> None:
    """What fsrs-rs-python needs of every item, checked before calling it: ratings 1-4,
    whole days >= 0, and at least one review with delta > 0 (it panics otherwise)."""
    for item in items:
        if not item.reviews:
            raise FitError(f"item {item.key} has no reviews")
        if any(r not in (1, 2, 3, 4) or d < 0 for r, d in item.reviews):
            raise FitError(f"item {item.key} has an invalid review: {item.reviews}")
        if not any(d > 0 for _, d in item.reviews):
            raise FitError(f"item {item.key} has no review with delta > 0")


def guarded[T](call: Callable[[], T]) -> T:
    """Run a call into fsrs-rs-python. Its PanicException derives from BaseException, not
    Exception, so it is caught here and raised as a FitError (ADR-0019 item 8)."""
    try:
        return call()
    except KeyboardInterrupt, SystemExit, GeneratorExit:
        raise
    except FitError:
        raise
    except BaseException as error:  # pyo3_runtime.PanicException
        raise FitError(f"{type(error).__name__}: {error}") from error


def _rs_items(rs: Any, items: Sequence[Item]) -> list[Any]:
    return [rs.FSRSItem([rs.FSRSReview(r, d) for r, d in item.reviews]) for item in items]


def fit(items: Sequence[Item]) -> tuple[float, ...]:
    """Fitted parameters for the items (cleaned, C1). Under 8 items: the defaults. Invalid
    items or a failure inside fsrs-rs-python raise FitError."""
    validate_items(items)
    rs = fitter()
    model = rs.FSRS(list(rs.DEFAULT_PARAMETERS))
    config = rs.TrainingConfig(num_epochs=FIT_EPOCHS)
    raw = guarded(lambda: model.compute_parameters(_rs_items(rs, items), training_config=config))
    return clean_parameters(raw)


def rs_evaluate(parameters: Sequence[float], items: Sequence[Item]) -> Evaluation:
    """fsrs-rs-python's own `evaluate` (recency-weighted log loss and RMSE(bins))."""
    validate_items(items)
    rs = fitter()
    result = guarded(lambda: rs.FSRS(list(parameters)).evaluate(_rs_items(rs, items)))
    return Evaluation(
        log_loss=float(result.log_loss), rmse_bins=float(result.rmse_bins), items=len(items)
    )


def held_out(
    items: Sequence[Item],
    current: Sequence[float],
    *,
    folds: int = HELD_OUT_FOLDS,
    fit_fn: Callable[[Sequence[Item]], Sequence[float]] = fit,
) -> HeldOut | None:
    """Train on each earlier part, test on the next segment (segment = N/(folds+1))."""
    n = len(items)
    segment = n // (folds + 1)
    if segment == 0:
        return None
    tests: list[Item] = []
    cand_preds: list[float] = []
    for i in range(folds):
        start = (i + 1) * segment
        end = n if i == folds - 1 else (i + 2) * segment
        fold_params = fit_fn(items[:start])
        test = list(items[start:end])
        tests.extend(test)
        cand_preds.extend(predictions(fold_params, test))
    ones = [1.0] * len(tests)
    cur_preds = predictions(current, tests)
    ys = labels(tests)
    return HeldOut(
        candidate=Evaluation(
            log_loss=log_loss(cand_preds, ys, ones),
            rmse_bins=rmse_bins(tests, cand_preds, ones),
            items=len(tests),
        ),
        current=Evaluation(
            log_loss=log_loss(cur_preds, ys, ones),
            rmse_bins=rmse_bins(tests, cur_preds, ones),
            items=len(tests),
        ),
        retention=retention_of(items),
        items=n,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Adoption:
    """C2: whether a candidate replaces the parameters in force, and why."""

    current: tuple[float, ...]
    candidate: tuple[float, ...]
    adopted: bool
    reason: str
    items: int
    current_in_sample: Evaluation | None = None
    candidate_in_sample: Evaluation | None = None
    held_out: HeldOut | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def params_id(self) -> str:
        return params_id_for(self.candidate if self.adopted else self.current)


def adoption(
    current: Sequence[float],
    candidate: Sequence[float],
    items: Sequence[Item],
    *,
    fit_fn: Callable[[Sequence[Item]], Sequence[float]] = fit,
    min_items: int = FIT_MIN_ITEMS,
) -> Adoption:
    """Keep the current set unless the candidate wins (C2)."""
    cur = clean_parameters(current)
    try:
        cand = clean_parameters(candidate)
    except ParameterError as error:
        return Adoption(
            current=cur, candidate=cur, adopted=False, reason=f"invalid: {error}", items=len(items)
        )
    if cand == cur:
        return Adoption(current=cur, candidate=cand, adopted=False, reason="unchanged", items=0)
    if not items:
        return Adoption(current=cur, candidate=cand, adopted=False, reason="no items", items=0)
    now = rs_evaluate(cur, items)
    new = rs_evaluate(cand, items)
    base = Adoption(
        current=cur,
        candidate=cand,
        adopted=False,
        reason="",
        items=len(items),
        current_in_sample=now,
        candidate_in_sample=new,
    )
    if not new.log_loss < now.log_loss:
        return _with(base, reason="in-sample log loss is not lower")
    if len(items) <= min_items:
        return _with(base, adopted=True, reason="in-sample log loss is lower")
    split = held_out(items, cur, fit_fn=fit_fn)
    if split is None:
        return _with(base, reason="too few items for the held-out split")
    base = _with(base, held_out=split)
    if not split.candidate.log_loss < split.current.log_loss:
        return _with(base, reason="held-out log loss is not lower")
    if not split.healthy:
        return _with(base, reason="health check failed")
    return _with(base, adopted=True, reason="lower log loss in and out of sample; healthy")


def _with(a: Adoption, **changes: Any) -> Adoption:
    return replace(a, **changes)
