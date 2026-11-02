"""tools.sim2.fsrs6 gives the same numbers as the app's FSRS adapter."""

import pytest

from core.engine.fsrs_adapter import FsrsAdapter
from tools.sim2.fsrs6 import AGAIN, DEFAULT, EASY, GOOD, HARD

SEQUENCES = [
    [(GOOD, 0), (GOOD, 2), (GOOD, 7), (AGAIN, 20), (GOOD, 1), (GOOD, 0), (EASY, 9)],
    [(AGAIN, 0), (AGAIN, 0), (HARD, 1), (GOOD, 3), (GOOD, 30), (GOOD, 200)],
    [(EASY, 0), (GOOD, 0), (GOOD, 0), (AGAIN, 1), (AGAIN, 5), (GOOD, 60)],
]


@pytest.mark.parametrize("seq", SEQUENCES)
def test_reviews_match_the_adapter(seq: list[tuple[int, int]]) -> None:
    adapter = FsrsAdapter()
    ours: tuple[float, float] | None = None
    theirs: tuple[float, float] | None = None
    for rating, elapsed in seq:
        theirs = adapter.step(theirs, rating, elapsed)
        if ours is None:
            ours = DEFAULT.initial(rating)
        else:
            ours = DEFAULT.review(ours[0], ours[1], rating, elapsed)
        assert ours == pytest.approx(theirs, rel=1e-12)


@pytest.mark.parametrize("days", [0.0, 0.5, 1.0, 7.0, 28.0, 365.0])
@pytest.mark.parametrize("stability", [0.3, 2.3065, 40.0, 900.0])
def test_retrievability_matches_and_inverts(days: float, stability: float) -> None:
    adapter = FsrsAdapter()
    r = DEFAULT.retrievability(days, stability)
    assert r == pytest.approx(adapter.retrievability_after(days, stability), rel=1e-12)
    if days > 0.0 and r < 1.0:
        assert DEFAULT.stability_for(r, days) == pytest.approx(stability, rel=1e-9)
        assert DEFAULT.interval(stability, r) == pytest.approx(days, rel=1e-9)


def test_recall_override_feeds_the_long_term_formula() -> None:
    s, d = DEFAULT.initial(GOOD)
    plain = DEFAULT.review(s, d, GOOD, 4)
    same = DEFAULT.review(s, d, GOOD, 4, DEFAULT.retrievability(4.0, s))
    later = DEFAULT.review(s, d, GOOD, 4, DEFAULT.retrievability(8.0, s))
    assert same == plain
    assert later[0] > plain[0]  # a lower recall at review time earns more stability
