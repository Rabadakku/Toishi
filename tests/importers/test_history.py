"""IMP-4: optional review history, as Anki itself rebuilds FSRS memory from it."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from fsrs import Card as FsrsCard
from fsrs import Rating, Scheduler
from fsrs.scheduler import DEFAULT_PARAMETERS

from core.importers.anki import (
    apply_anki_import,
    plan_anki_import,
    read_package,
    recompute_memory,
)
from core.importers.anki import history as hist
from core.importers.anki.model import Revlog
from core.storage import Storage, UserStore
from tests.importers.conftest import fixture
from tests.importers.oracle import collection, import_package

DAY = 86_400_000
LEARN, REVIEW, RELEARN, FILTERED, MANUAL, RESCHEDULED = range(6)


def r(at: int, ease: int, kind: int, ivl: int = 1, factor: int = 2500) -> Revlog:
    return Revlog(at, 1, ease, ivl, 0, factor, 5000, kind)


# ---------------------------------------------------------------- Anki's revlog filter


def test_cramming_manual_and_rescheduled_rows_are_dropped() -> None:
    entries = [
        r(1, 3, LEARN, -600), r(2, 3, LEARN, 1), r(3, 3, FILTERED, 0, factor=0),
        r(4, 0, MANUAL, 5), r(5, 0, RESCHEDULED, 6), r(6, 4, FILTERED, 3, factor=2500),
        r(7, 2, REVIEW, 4),
    ]  # fmt: skip
    kept = hist.reviews_for_fsrs(entries)
    assert kept is not None
    assert [e.id for e in kept.entries] == [1, 2, 6, 7]  # early review in a rescheduling deck stays
    assert kept.complete


def test_history_restarts_after_a_reset() -> None:
    entries = [r(1, 3, REVIEW, 5), r(2, 0, MANUAL, 0, factor=0), r(3, 1, LEARN, -60),
               r(4, 3, LEARN, 1), r(5, 3, REVIEW, 3)]  # fmt: skip
    kept = hist.reviews_for_fsrs(entries)
    assert kept is not None
    assert ([e.id for e in kept.entries], kept.complete) == ([3, 4, 5], True)
    nothing_since = [r(1, 3, LEARN, 1), r(2, 0, MANUAL, 0, factor=0)]
    assert hist.reviews_for_fsrs(nothing_since) is None


def test_history_without_learning_is_incomplete_and_seeded_from_sm2() -> None:
    entries = [r(1, 3, REVIEW, 8, factor=2600), r(2, 3, REVIEW, 20, factor=2600)]
    kept = hist.reviews_for_fsrs(entries)
    assert kept is not None
    assert not kept.complete
    seed = hist.sm2_seed(kept.entries)
    assert seed == {"ease": 2.6, "ivl": 8, "revlog": 1}
    fsrs_written = hist.sm2_seed([r(1, 3, REVIEW, 8, factor=500)])
    assert fsrs_written is not None
    assert fsrs_written["difficulty"] == pytest.approx((0.5 - 0.1) * 9 + 1)


def test_only_the_last_learning_block_counts() -> None:
    entries = [r(1, 3, LEARN, 1), r(2, 3, REVIEW, 3), r(3, 1, RELEARN, -600),
               r(4, 3, LEARN, 1), r(5, 3, REVIEW, 4)]  # fmt: skip
    kept = hist.reviews_for_fsrs(entries)
    assert kept is not None
    assert [e.id for e in kept.entries] == [4, 5]


def test_ignore_before_date() -> None:
    entries = [r(1000, 3, LEARN, 1), r(5000, 3, REVIEW, 3), r(9000, 3, REVIEW, 9)]
    kept = hist.reviews_for_fsrs(entries, ignore_before_ms=4000)
    assert kept is not None
    assert ([e.id for e in kept.entries], kept.complete) == ([5000, 9000], False)


def test_anki_days_roll_over_at_the_hour_in_a_fixed_offset() -> None:
    day = datetime(2026, 9, 1, tzinfo=UTC)
    at = int(day.timestamp() * 1000)
    hour = 3_600_000
    assert hist.anki_day(at + 3 * hour, 4, 0) == date(2026, 8, 31)
    assert hist.anki_day(at + 4 * hour, 4, 0) == date(2026, 8, 31)  # the rollover instant
    assert hist.anki_day(at + 4 * hour + 1000, 4, 0) == date(2026, 9, 1)
    assert hist.anki_day(at + 3 * hour, 6, 7200) == date(2026, 8, 31)  # 05:00 at UTC+2
    assert hist.anki_day(at + 5 * hour, 6, 7200) == date(2026, 9, 1)  # 07:00 at UTC+2


# ---------------------------------------------------------------- planning and writing


def test_plan_lists_reviews_memory_states_and_parameter_sets(store: UserStore) -> None:
    plan = plan_anki_import(store, read_package(fixture("history.apkg")))
    h = plan.history
    assert (h.review_count, len(h.new_memory), len(h.targets)) == (17, 1, 5)
    [params] = h.param_sets
    assert (params.name, params.desired_retention, params.decks) == (
        "FSRS preset", 0.85, ("Hist::FSRS",),
    )  # fmt: skip
    assert len(params.fsrs6) == 21
    assert params.parameters[0] == 0.2172
    assert params.id.startswith("anki-fit-")
    incomplete = [t for t in h.targets if not t.complete]
    assert len(incomplete) == 1
    assert incomplete[0].sm2_seed is not None
    assert incomplete[0].sm2_seed["ease"] == 2.6
    report = plan.report()
    assert "history: 17 new reviews for 5 study items; 1 FSRS memory states" in report
    summary = plan.summary()["anki"]
    assert summary["reviews"] == 17
    assert summary["param_sets"][0]["parameters"][0] == 0.2172
    assert len(summary["replay"]) == 4


def test_without_history_nothing_but_cards(store: UserStore) -> None:
    plan = plan_anki_import(store, read_package(fixture("history.apkg")), with_history=False)
    assert plan.history.targets == ()
    apply_anki_import(store, plan)
    assert store.review_events() == []


def test_apply_writes_events_on_anki_days_and_imports_fsrs_state(store: UserStore) -> None:
    data = read_package(fixture("history.apkg"))
    plan = plan_anki_import(store, data)
    result = apply_anki_import(store, plan)
    assert (result.reviews, result.memory_states, len(result.needs_replay)) == (17, 1, 4)
    events = store.review_events(target_kind="flashcard")
    assert len(events) == 17
    assert {e.rules_version for e in events} == {"anki-import-1"}
    attempts = store.attempts()
    assert all(a.verdict == "self" and a.explicit_rating for a in attempts)
    assert all(a.extra["source"] == "anki" for a in attempts)
    # Reviews at 03:00 and 05:00 UTC on one calendar day fall on two Anki days (4 AM).
    tres = next(t for t in plan.history.targets if len(t.reviews) == 4 and t.complete
                and t.reviews[0].rating == 3 and t.reviews[2].rating == 4)  # fmt: skip
    days = [a.study_day for a in attempts if a.card_id == tres.card_id]
    assert days[0] != days[1]
    assert days[1] == days[2]  # 02:00 the next morning is still the same Anki day
    [state] = store.flashcard_states()
    fsrs = next(t for t in plan.history.targets if t.memory is not None)
    assert (state.card_id, state.stability, state.difficulty, state.fsrs_state) == (
        fsrs.card_id, 12.5, 5.2, 2,
    )  # fmt: skip
    lrt = next(c for c in data.cards or () if "s" in c.data).data["lrt"]
    assert state.last_review_at == lrt * 1000
    assert state.due_at is not None
    assert state.last_review_at is not None
    assert state.due_at - state.last_review_at > 11 * DAY  # Anki's 12-day interval
    [record] = [r for r in store.imports() if r.kind == "apkg"]
    assert record.summary["anki"]["memory_states"] == 1


def test_reimport_adds_no_history_and_keeps_studied_state(store: UserStore) -> None:
    apply_anki_import(store, plan_anki_import(store, read_package(fixture("history.apkg"))))
    [state] = store.flashcard_states()
    store.apply([type(state)(**{**{f: getattr(state, f) for f in state.__slots__},
                                "stability": 99.0})])  # fmt: skip
    again = plan_anki_import(store, read_package(fixture("history.apkg")))
    assert again.nothing_to_do
    assert (again.history.review_count, len(again.history.new_memory)) == (0, 0)
    result = apply_anki_import(store, again)
    assert (result.reviews, result.memory_states) == (0, 0)
    assert store.flashcard_states()[0].stability == 99.0
    assert len(store.review_events()) == 17


def test_colpkg_days_use_its_rollover_and_offset(store: UserStore) -> None:
    apkg = plan_anki_import(store, read_package(fixture("history.apkg"))).history
    colpkg = plan_anki_import(store, read_package(fixture("history.colpkg"))).history

    def days(h: object) -> dict[int, date]:
        return {rv.entry.id: rv.day for t in h.targets for rv in t.reviews}  # type: ignore[attr-defined]

    a, c = days(apkg), days(colpkg)
    assert a.keys() == c.keys()
    moved = [k for k in a if a[k] != c[k]]
    assert moved  # rollover 6 at UTC+5 (01:00 UTC) instead of 4 at UTC: early reviews move
    for k in a:
        # A review exactly at the rollover still counts on the day before, as in Anki.
        local = datetime.fromtimestamp(k // 1000 - 1, UTC) + timedelta(hours=5 - 6)
        assert c[k] == local.date()


# ---------------------------------------------------------------- against Anki itself


def _replay(reviews: list[hist.AnkiReview], params: tuple[float, ...]) -> FsrsCard:
    """py-fsrs over Anki study days: day boundaries map to synthetic UTC midnights, so
    `.days` differences are Anki's delta_t (the IMP-4 recipe)."""
    scheduler = Scheduler(parameters=params, learning_steps=(), relearning_steps=(),
                          enable_fuzzing=False)  # fmt: skip
    card = FsrsCard()
    for k, review in enumerate(reviews):
        when = datetime.combine(review.day, time(0), tzinfo=UTC) + timedelta(seconds=k)
        card, _ = scheduler.review_card(card, Rating(review.rating), when)
    return card


def _naive(reviews: list[hist.AnkiReview], params: tuple[float, ...]) -> FsrsCard:
    scheduler = Scheduler(parameters=params, learning_steps=(), relearning_steps=(),
                          enable_fuzzing=False)  # fmt: skip
    card = FsrsCard()
    for review in reviews:
        card, _ = scheduler.review_card(
            card, Rating(review.rating), datetime.fromtimestamp(review.at / 1000, UTC)
        )
    return card


def test_replaying_anki_days_gives_ankis_own_memory_state() -> None:
    """Anki's compute_memory_state on the imported deck equals a py-fsrs replay over the
    reviews we convert (complete histories); counting 24-hour periods instead does not."""
    data = read_package(fixture("history.apkg"))
    offset = int((datetime.now().astimezone().utcoffset() or timedelta()).total_seconds())
    by_card: dict[int, list[Revlog]] = {}
    for e in data.revlog:
        by_card.setdefault(e.card_id, []).append(e)
    compared = differs = 0
    with collection() as col:
        import_package(col, fixture("history.apkg"))
        col.set_config("fsrs", True)
        for card in data.cards or ():
            kept = hist.reviews_for_fsrs(by_card.get(card.id, []))
            if kept is None or not kept.complete:
                continue
            reviews = [hist.AnkiReview(e.id, hist.anki_day(e.id, 4, offset), e.ease, e)
                       for e in kept.entries]  # fmt: skip
            config = data.deck_configs.get(card.config_id or 0)
            params = (
                tuple(config.fsrs_params)
                if config and config.fsrs_params
                else tuple(DEFAULT_PARAMETERS)
            )
            theirs = col.compute_memory_state(card.id)
            ours = _replay(reviews, params)
            assert ours.stability == pytest.approx(theirs.stability, rel=1e-4)
            assert ours.difficulty == pytest.approx(theirs.difficulty, rel=1e-4)
            naive = _naive(reviews, params)
            differs += abs(naive.stability - theirs.stability) > 0.01
            compared += 1
    assert compared == 4
    assert differs >= 2  # the 24-hour pitfall IMP-4 warns about


# ---------------------------------------------------------------- the engine hook


def test_recompute_hook_reports_until_the_engine_has_it(
    storage: Storage, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.engine import Engine

    assert hasattr(Engine, "recompute_memory") or recompute_memory(storage) is False
    calls: list[str] = []
    monkeypatch.setattr(Engine, "recompute_memory", lambda self: calls.append("ran"),
                        raising=False)  # fmt: skip
    assert recompute_memory(storage) is True
    assert calls == ["ran"]
