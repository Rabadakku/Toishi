"""Due lists (QUE-4/QUE-5 inputs) and projections (LIB-4, LIB-9)."""

from dataclasses import replace
from datetime import timedelta

import pytest

from core.engine.boosters import BoostTarget, TargetOutlook
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.lifecycle import RELEARNING
from core.engine.projection import load_warning, project_exam, project_load
from core.engine.schedule import due_skills, new_skill_room, scheduled_load
from core.model import SkillState
from tests.engine.helpers import DAYS, at_day, day, learned_state

FSRS = FsrsAdapter(fuzz=False)
TODAY = day(at_day(0))


def st(skill_id: str, stability: float, days_ago: int, **kw: object) -> SkillState:
    return replace(learned_state(stability, at=at_day(-days_ago)), skill_id=skill_id, **kw)  # type: ignore[arg-type]


def test_due_skills_most_overdue_first_with_escalation():
    states = [
        st("a.ontime", 5.0, 5),
        st("b.late", 5.0, 9),
        st("c.verylate", 2.0, 12),
        st("d.future", 30.0, 1),
        replace(st("e.relearn", 1.0, 1), fsrs_state=RELEARNING),
        replace(st("f.new", 1.0, 0), fsrs_state=None),
        st("g.off", 2.0, 30),
    ]
    found = due_skills(
        states,
        TODAY,
        retention_of=lambda _: 0.9,
        adapter=FSRS,
        days=DAYS,
        active=lambda k: k != "g.off",
    )
    assert [d.skill_id for d in found] == ["c.verylate", "b.late", "a.ontime", "e.relearn"]
    assert found[0].days_overdue == 10
    assert found[0].escalated
    assert not found[1].escalated
    assert found[-1].reason == "relearn"
    assert found[0].reason == "review"
    assert all(0 < d.recall <= 1 for d in found)


def test_lower_retention_means_fewer_due_today():
    states = [st(f"s.{i}", 10.0, i) for i in range(20)]
    a = due_skills(states, TODAY, retention_of=lambda _: 0.90, adapter=FSRS, days=DAYS)
    keep = due_skills(states, TODAY, retention_of=lambda _: 0.80, adapter=FSRS, days=DAYS)
    assert len(keep) < len(a)


def test_scheduled_load_and_new_skill_room():
    states = [st(f"s.{i}", 3.0, 0) for i in range(10)] + [st("old", 1.0, 20)]
    load = scheduled_load(states, TODAY, 7, retention_of=lambda _: 0.9, adapter=FSRS, days=DAYS)
    assert load[TODAY] == 1
    assert load[TODAY + timedelta(days=3)] == 10
    assert sum(load.values()) == 11
    # Average 11/7 a day; each new skill a day adds about 5 (block of 4 + one early review).
    assert new_skill_room(load, daily_count=20) == 3
    assert new_skill_room(load, daily_count=20, max_new=2) == 2
    assert new_skill_room(dict.fromkeys(load, 15), daily_count=20) == 1
    assert new_skill_room(dict.fromkeys(load, 16), daily_count=20) == 0
    assert new_skill_room({}, daily_count=20) == 4


def outlook(recalls: dict[str, float | None]) -> TargetOutlook:
    t = BoostTarget(
        key="exam:1",
        name="Final",
        day=TODAY + timedelta(days=10),
        at_ms=at_day(10),
        target=0.95,
        skill_ids=tuple(recalls),
    )
    return TargetOutlook(target=t, recall=recalls, left_alone=())


def test_exam_projection_holding_back_level():
    states = {
        k: st(k, 30.0, 0, level=lv) for k, lv in [("a", "learned"), ("b", "learned"), ("c", "exam")]
    }
    proj = project_exam(outlook({"a": 0.97, "b": 0.97, "c": 0.97}), states, today=TODAY)
    assert proj.share_exam_level == pytest.approx(1 / 3)
    assert proj.projected_score < 0.95
    assert proj.holding_back == "level"
    assert proj.proposed_extra_per_day >= 1
    assert proj.days_left == 10


def test_exam_projection_holding_back_recall():
    states = {k: st(k, 30.0, 0, level="mastered") for k in ("a", "b")}
    proj = project_exam(outlook({"a": 0.70, "b": 0.75}), states, today=TODAY)
    assert proj.holding_back == "recall"
    assert proj.share_exam_level == 1.0


def test_exam_projection_on_target_proposes_nothing():
    states = {k: st(k, 30.0, 0, level="mastered") for k in ("a", "b")}
    proj = project_exam(outlook({"a": 0.97, "b": 0.99}), states, today=TODAY)
    assert proj.holding_back is None
    assert proj.proposed_extra_per_day == 0
    missing = project_exam(outlook({"a": 0.97, "z": None}), states, today=TODAY)
    assert missing.holding_back == "level"
    assert missing.mean_recall < 0.5


def test_load_projection_is_deterministic_and_sane():
    states = {f"s.{i}": st(f"s.{i}", 5.0 + i, i % 5) for i in range(30)}
    new = [f"n.{i}" for i in range(20)]

    def run(seed: int = 0):
        return project_load(
            states,
            new,
            today=TODAY,
            horizon_days=28,
            retention_of=lambda _: 0.9,
            adapter=FSRS,
            days=DAYS,
            seed=seed,
        )

    a, b = run(), run()
    assert a == b
    assert 3 < a.problems_per_day < 25
    assert a.minutes_per_day == pytest.approx(a.problems_per_day * 2.5)
    lighter = project_load(
        states,
        new,
        today=TODAY,
        horizon_days=28,
        retention_of=lambda _: 0.8,
        adapter=FSRS,
        days=DAYS,
    )
    assert lighter.problems_per_day < a.problems_per_day
    assert load_warning([a, a], daily_count=int(a.problems_per_day * 1.5))
    assert not load_warning([a], daily_count=int(a.problems_per_day) + 1)


def test_load_projection_counts_boosters():
    states = {f"s.{i}": st(f"s.{i}", 40.0, 0) for i in range(10)}
    exam = BoostTarget(
        key="exam:1",
        name="x",
        day=TODAY + timedelta(days=20),
        at_ms=at_day(20),
        target=0.95,
        skill_ids=tuple(states),
    )
    base = project_load(
        states,
        [],
        today=TODAY,
        horizon_days=25,
        retention_of=lambda _: 0.9,
        adapter=FSRS,
        days=DAYS,
    )
    boosted = project_load(
        states,
        [],
        today=TODAY,
        horizon_days=25,
        retention_of=lambda _: 0.9,
        adapter=FSRS,
        days=DAYS,
        targets=[exam],
    )
    assert boosted.problems_per_day > base.problems_per_day
