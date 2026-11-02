"""The import's engine hook (ADR-0015 -> ADR-0013): deck-group parameter sets and memory
replayed from imported histories (ADR-0016)."""

from core.engine import Engine
from core.engine.fsrs_adapter import FsrsAdapter, clean_parameters
from core.engine.param_sets import DECK_GROUPS_SETTING, params_key
from core.importers.anki import apply_anki_import, plan_anki_import, read_package, recompute_memory
from core.storage import Storage
from tests.importers.conftest import fixture


def _import(storage: Storage):
    plan = plan_anki_import(storage.users, read_package(fixture("history.apkg")))
    return plan, apply_anki_import(storage.users, plan)


def test_hook_registers_the_deck_groups_set_and_replays_histories_with_it(
    storage: Storage,
) -> None:
    plan, result = _import(storage)
    [preset] = plan.history.param_sets
    assert recompute_memory(storage, result.record) is True
    users = storage.users
    group = preset.id.removeprefix("anki-")
    assert users.get_setting(DECK_GROUPS_SETTING) == {"Hist::FSRS": group}
    stored = users.get_setting(params_key(f"anki.{group}"))
    assert stored["source"] == "import"
    assert stored["w"] == list(clean_parameters(preset.fsrs6))
    engine = Engine(storage)
    states = {(s.card_id, s.ord): s for s in users.flashcard_states()}
    days = engine.days()
    for t in plan.history.targets:
        key = (t.card_id, t.ord)
        if not t.complete:  # cut short before its learning block: waits for an SM-2 seed
            assert key not in states
            continue
        state = states[key]
        own = engine.adapter_for_card(t.card_id)
        in_group = t.param_set is not None
        assert (own.parameters[0] == preset.fsrs6[0]) is in_group
        reviews = [(rv.rating, rv.at) for rv in t.reviews]
        expected = own.replay(reviews, days)
        assert expected is not None
        assert (state.stability, state.difficulty) == (expected.stability, expected.difficulty)
        assert state.last_review_at == t.reviews[-1].at
        assert state.due_at is not None
        assert state.due_at > t.reviews[-1].at
        if in_group:
            default = FsrsAdapter(days=days).replay(reviews, days)
            assert default is not None
            assert state.stability != default.stability  # the preset, not the defaults
    # The live rows are what the log says: a recompute changes nothing.
    assert engine.recompute_memory().changed == ()


def test_hook_keeps_a_set_written_since_and_runs_again_without_changes(storage: Storage) -> None:
    plan, result = _import(storage)
    assert recompute_memory(storage, result.record)
    [preset] = plan.history.param_sets
    set_id = f"anki.{preset.id.removeprefix('anki-')}"
    engine = Engine(storage)
    revert = engine.revert_parameters(set_id, "fsrs6-default")  # the student reverts it
    assert revert.changed
    before = storage.users.flashcard_states()
    assert recompute_memory(storage) is True  # every Anki import in the log
    assert storage.users.get_setting(params_key(set_id))["source"] == "revert"
    assert storage.users.flashcard_states() == before
