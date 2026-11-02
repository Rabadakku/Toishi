"""Replay speed: 5,000 observations of about 4 components must replay in under 3 s."""

import random
import time
from datetime import timedelta

from core.engine.config import DAY_MS
from core.learner.model import StudentModel
from core.learner.types import ComponentInfo, Observation, ProblemSpec, SharedParams
from tests.learner.helpers import DAY0, START_MS


def _course_and_log(attempts: int = 5000) -> tuple[dict[str, ComponentInfo], list[Observation]]:
    rng = random.Random(5)  # noqa: S311 - reproducible test data
    course = [f"c{i:02d}" for i in range(48)]
    background = [f"alg.{i:02d}" for i in range(12)]
    catalog = {c: ComponentInfo(c, False) for c in course} | {
        b: ComponentInfo(b, True) for b in background
    }
    problems = []
    for i, main in enumerate(course):
        for j in range(8):
            others = rng.sample(course[:i] + background if i >= 3 else background, 3)
            problems.append(
                ProblemSpec(
                    f"{main}#{j}", f"{main}#{j}", None, main, (main, *others), 1 + j % 4, 4, 7.0
                )
            )
    log = []
    for k in range(attempts):
        day = k // 40
        correct = rng.random() < 0.7
        log.append(
            Observation(
                attempt_id=k,
                at_ms=START_MS + day * DAY_MS + (k % 40) * 120_000,
                study_day=DAY0 + timedelta(days=day),
                problem=rng.choice(problems),
                correct=correct,
                minutes=rng.uniform(2.0, 12.0) if correct else None,
            )
        )
    return catalog, log


def test_replaying_5000_observations_of_4_components_takes_under_3_seconds():
    catalog, log = _course_and_log()
    model = StudentModel(catalog)
    start = time.perf_counter()
    _, records = model.replay(SharedParams(), log)
    elapsed = time.perf_counter() - start
    assert len(records) == 5000
    assert elapsed < 3.0, f"replay took {elapsed:.2f} s"
