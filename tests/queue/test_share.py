"""QUE-11..13: sharing the day across courses (pure)."""

from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from core.model import CourseGoal
from core.queue.share import (
    CourseDemand,
    backlog_factors,
    carry_over,
    floor_size,
    goal_weight,
    split,
    urgency,
)

DAY = date(2026, 10, 1)


def test_goal_weights_and_keep_after_goal_date() -> None:
    assert goal_weight(None, DAY) == 1.5
    assert goal_weight(CourseGoal(course_id="c", goal="A"), DAY) == 1.5
    assert goal_weight(CourseGoal(course_id="c", goal="B"), DAY) == 1.0
    assert goal_weight(CourseGoal(course_id="c", goal="Keep"), DAY) == 0.5
    past = CourseGoal(course_id="c", goal="A", goal_date=date(2026, 9, 1))
    assert goal_weight(past, DAY) == 0.5
    custom = CourseGoal(course_id="c", goal="custom", custom_retention=0.92)
    assert goal_weight(custom, DAY) == 1.5


def test_urgency_rises_from_1_to_3_over_two_weeks() -> None:
    assert urgency(None) == 1.0
    assert urgency(15) == 1.0
    assert urgency(14) == 1.0
    assert urgency(7) == 2.0
    assert urgency(0) == 3.0
    assert urgency(-1) == 1.0


def test_backlog_factor_is_due_work_against_the_others_clamped() -> None:
    f = backlog_factors({"a": 40, "b": 10, "c": 10, "d": 0})
    assert f["a"] == 2.0  # 40 / 10, capped at 2
    assert f["b"] == 0.5  # 10 / mean(40, 10) = 0.4, floored at 0.5
    assert f["d"] == 1.0
    assert backlog_factors({"a": 5})["a"] == 1.0


def test_floor_is_three_or_ten_percent() -> None:
    assert floor_size(20, 3, 0.10) == 3
    assert floor_size(50, 3, 0.10) == 5
    assert floor_size(45, 3, 0.10) == 5  # 4.5 rounds half up


def test_carry_over_is_capped_at_half_a_quota() -> None:
    assert carry_over(10, 2) == 5
    assert carry_over(10, 8) == 2
    assert carry_over(10, 12) == 0
    assert carry_over(3, 0) == 1


def test_floors_then_weights_and_exact_sum() -> None:
    share = split(
        [
            CourseDemand(course_id="a", goal=1.5, due=100),
            CourseDemand(course_id="b", goal=1.0, due=100),
            CourseDemand(course_id="c", goal=0.5, due=100),
        ],
        20,
    )
    assert share.total == 20
    assert share.free == 0
    assert all(q >= 3 for q in share.quotas.values())
    assert share.quotas["a"] > share.quotas["b"] > share.quotas["c"]


def test_surplus_goes_back_to_the_others() -> None:
    share = split(
        [
            CourseDemand(course_id="a", goal=1.5, due=2),
            CourseDemand(course_id="b", goal=0.5, due=50),
        ],
        20,
    )
    assert share.quotas == {"a": 2, "b": 18}
    assert share.free == 0


def test_urgency_shifts_the_share_toward_the_exam() -> None:
    calm = split(
        [
            CourseDemand(course_id="a", goal=1.0, due=50),
            CourseDemand(course_id="b", goal=1.0, due=50),
        ],
        20,
    )
    exam = split(
        [
            CourseDemand(course_id="a", goal=1.0, urgency=urgency(0), due=50),
            CourseDemand(course_id="b", goal=1.0, due=50),
        ],
        20,
    )
    assert calm.quotas["a"] == calm.quotas["b"] == 10
    assert exam.quotas["a"] > exam.quotas["b"] >= 3


def test_carry_is_reserved_inside_the_count() -> None:
    share = split(
        [
            CourseDemand(course_id="a", goal=1.5, due=50),
            CourseDemand(course_id="b", goal=1.0, due=50, carry=4),
        ],
        20,
    )
    assert share.total == 20
    assert share.carried == {"b": 4}
    base = split(
        [
            CourseDemand(course_id="a", goal=1.5, due=50),
            CourseDemand(course_id="b", goal=1.0, due=50),
        ],
        20,
    )
    assert share.quotas["b"] > base.quotas["b"]


def test_more_courses_than_floors_fit() -> None:
    demands = [CourseDemand(course_id=f"c{i}", goal=1.0 + i / 10, due=10) for i in range(9)]
    share = split(demands, 20)
    assert share.total == 20
    assert max(share.quotas.values()) <= 3


@given(
    st.lists(
        st.tuples(
            st.sampled_from([0.5, 1.0, 1.5]),
            st.floats(1.0, 3.0),
            st.integers(0, 40),
            st.integers(0, 6),
        ),
        min_size=1,
        max_size=6,
    ),
    st.integers(0, 60),
)
def test_quotas_sum_to_the_count_or_the_due_work(rows, n) -> None:
    demands = [
        CourseDemand(course_id=f"c{i}", goal=g, urgency=u, due=d, carry=k)
        for i, (g, u, d, k) in enumerate(rows)
    ]
    share = split(demands, n)
    total_due = sum(d.due for d in demands)
    assert share.total == min(n, total_due)
    assert share.total + share.free == n
    floor = floor_size(n, 3, 0.10)
    reserved = sum(min(x.due, floor + x.carry) for x in demands)
    for d in demands:
        q = share.quotas[d.course_id]
        assert 0 <= q <= d.due
        if d.due > 0 and reserved <= n:
            assert q >= min(d.due, floor)  # every course with due work gets its floor
