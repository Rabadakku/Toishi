"""Builders and hypothesis strategies for the student model tests."""

from dataclasses import replace
from datetime import UTC, date, timedelta

from hypothesis import strategies as st

from core.engine.config import DAY_MS
from core.engine.days import StudyDays
from core.learner.types import (
    ComponentInfo,
    ComponentState,
    MemoryState,
    Observation,
    ProblemSpec,
    SharedParams,
    StudentState,
)

COURSE = ("c1", "c2", "c3", "c4")
BACKGROUND = ("alg.b1", "alg.b2")
CATALOG = {cid: ComponentInfo(cid, False, "course") for cid in COURSE} | {
    cid: ComponentInfo(cid, True, None) for cid in BACKGROUND
}
DAYS = StudyDays(UTC)
EPOCH = date(1970, 1, 1)
DAY0 = date(2026, 3, 10)
HOUR_MS = 3_600_000
START_MS = (DAY0 - EPOCH).days * DAY_MS + 12 * HOUR_MS  # noon UTC on DAY0


def noon(day: date) -> int:
    return (day - EPOCH).days * DAY_MS + 12 * HOUR_MS


def problem(
    *components: str,
    tier: int = 2,
    minutes: float = 5.0,
    wrong: tuple[tuple[int, str], ...] = (),
    pid: str = "p",
) -> ProblemSpec:
    return ProblemSpec(
        problem_id=pid,
        card_id=pid,
        part=None,
        main_skill=components[0],
        components=tuple(components),
        tier=tier,
        steps=len(components),
        standard_minutes=minutes,
        wrong_components=wrong,
        family=pid,
    )


def observation(
    attempt_id: int,
    at_ms: int,
    spec: ProblemSpec,
    correct: bool,
    *,
    day: date | None = None,
    aided: bool = False,
    matched_wrong: int | None = None,
    minutes: float | None = None,
) -> Observation:
    return Observation(
        attempt_id=attempt_id,
        at_ms=at_ms,
        study_day=DAYS.day_of(at_ms) if day is None else day,
        problem=spec,
        correct=correct,
        aided=aided,
        matched_wrong=matched_wrong,
        minutes=minutes,
    )


def state_with(params: SharedParams, components: dict[str, ComponentState]) -> StudentState:
    return StudentState(params=params, components=dict(components))


def memory(stability: float, difficulty: float, at_ms: int) -> MemoryState:
    return MemoryState(stability, difficulty, at_ms, DAYS.day_of(at_ms))


# ---------------------------------------------------------------- hypothesis strategies

GAPS_MS = (0, 60_000, 20 * 60_000, 3 * HOUR_MS, DAY_MS // 2, DAY_MS, 3 * DAY_MS, 20 * DAY_MS)


@st.composite
def problems(draw: st.DrawFn) -> ProblemSpec:
    components = draw(
        st.lists(st.sampled_from(COURSE + BACKGROUND), min_size=1, max_size=4, unique=True)
    )
    wrong = draw(
        st.lists(
            st.tuples(st.integers(0, 2), st.sampled_from(components)),
            max_size=2,
            unique_by=lambda w: w[0],
        )
    )
    return problem(
        *components,
        tier=draw(st.integers(1, 5)),
        minutes=draw(st.sampled_from((2.0, 6.5, 11.0))),
        wrong=tuple(wrong),
        pid="p" + "-".join(components),
    )


@st.composite
def logs(draw: st.DrawFn, min_size: int = 1, max_size: int = 25) -> list[Observation]:
    """Observation logs in time order with ids 0..n-1: right answers (some timed), misses,
    matched wrong answers and aided tries, minutes to weeks apart."""
    n = draw(st.integers(min_size, max_size))
    at_ms = START_MS
    out: list[Observation] = []
    for i in range(n):
        at_ms += draw(st.sampled_from(GAPS_MS))
        spec = draw(problems())
        kind = draw(st.sampled_from(("right", "right", "wrong", "matched", "aided")))
        minutes = draw(st.one_of(st.none(), st.sampled_from((1.5, 4.0, 9.0))))
        out.append(
            observation(
                i,
                at_ms,
                spec,
                kind == "right",
                aided=kind == "aided",
                matched_wrong=draw(st.integers(0, 2)) if kind == "matched" else None,
                minutes=minutes if kind == "right" else None,
            )
        )
    return out


def shared_params() -> st.SearchStrategy[SharedParams]:
    unit = st.floats(-1.5, 1.5)
    return st.builds(
        SharedParams,
        version=st.just("h"),
        slip=st.floats(0.0, 0.4),
        delta4=st.floats(-1.0, 2.0),
        delta5=st.floats(-1.0, 3.0),
        calib_a=st.tuples(unit, unit, unit, unit, unit),
        calib_b=st.floats(0.2, 2.0),
        phi=st.floats(0.5, 4.0),
        tau=st.floats(-1.0, 2.0),
        sigma_t=st.floats(0.1, 1.5),
        q_drift=st.sampled_from((0.0, 0.01, 0.2)),
        kappa=st.sampled_from((0.0, 0.5, 0.95, 1.0)),
        same_day_weight=st.sampled_from((0.0, 0.25, 1.0)),
    )


def with_ties(log: list[Observation], per_instant: int = 3) -> list[Observation]:
    """The same log with groups of `per_instant` observations sharing one instant."""
    return [
        replace(
            obs,
            at_ms=START_MS + (i // per_instant) * DAY_MS,
            study_day=DAY0 + timedelta(days=i // per_instant),
        )
        for i, obs in enumerate(log)
    ]
