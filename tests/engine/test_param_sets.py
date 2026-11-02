"""Decision 6: one parameter set per domain, one for flashcards, one per Anki deck group."""

from fsrs.scheduler import DEFAULT_PARAMETERS

from core.engine import Engine
from core.engine.param_sets import (
    deck_group_of,
    kind_of_set,
    load_set,
    params_key,
    set_id_for,
    stored_value,
)
from tests.engine.test_service import learn

FITTED = [*DEFAULT_PARAMETERS[:20], 0.3]
OTHER = [0.5, *DEFAULT_PARAMETERS[1:]]


def test_D6_set_ids():
    assert set_id_for("skill") == "skills"
    assert set_id_for("skill", "math") == "skills.math"
    assert set_id_for("flashcard") == "flashcards"
    assert set_id_for("flashcard", "kanji") == "anki.kanji"
    assert [kind_of_set(s) for s in ("skills", "skills.math", "flashcards", "anki.kanji")] == [
        "skill",
        "skill",
        "flashcard",
        "flashcard",
    ]
    groups = {"fsrs.deck_groups": {"Lang": "lang", "Lang::Kanji": "kanji"}}
    assert deck_group_of(groups, "Lang::Kanji::N5") == "kanji"
    assert deck_group_of(groups, "Lang::Verbs") == "lang"
    assert deck_group_of(groups, "Language") is None
    # The old single setting still feeds the default skill set, never the flashcards.
    legacy = {"fsrs.params.math": {"w": FITTED}}
    assert load_set(legacy, "skills").parameters[20] == 0.3
    assert load_set(legacy, "flashcards").source == "default"


def test_D6_domains_flashcards_and_anki_groups_have_their_own_adapters(storage):
    users = storage.users
    users.set_settings(
        {
            "fsrs.domains": {"calc1": "math"},
            "fsrs.deck_groups": {"Lang::Kanji": "kanji"},
            params_key("skills.math"): stored_value(FITTED, at=0, source="fit"),
            params_key("anki.kanji"): stored_value(OTHER, at=0, source="import"),
        }
    )
    engine = Engine(storage)
    math_id = engine.adapter_for("skill", "math").params_id
    assert math_id.startswith("fit-")
    assert engine.adapter_for_skill("calc1.alg").params_id == math_id
    assert engine.set_of_skill("calc1.alg") == "skills.math"
    assert engine.adapter().params_id == "fsrs6-default"  # courses with no domain
    assert engine.adapter_for("flashcard").params_id == "fsrs6-default"
    kanji = engine.adapter_for("flashcard", "kanji")
    assert kanji.parameters[0] == 0.5
    assert kanji.params_id not in (math_id, "fsrs6-default")
    assert engine.set_of_card("calc1.alg.t1.v0") == "flashcards"  # no deck group
    assert engine.adapter_for_card("calc1.alg.t1.v0").params_id == "fsrs6-default"


def test_D6_flashcards_keep_the_defaults_after_a_skill_fit(storage, clock):
    engine = Engine(storage)
    for skill in ("calc1.alg", "calc1.lim", "calc1.der"):
        learn(engine, clock, skill)
    candidate = [5.0, 10.0, 20.0, 40.0, *DEFAULT_PARAMETERS[4:]]
    clock.advance(days=30)
    from tests.engine.test_service import answer

    for skill in ("calc1.alg", "calc1.lim", "calc1.der"):
        answer(engine, clock, skill)
    assert engine.fit(candidate=candidate).adopted
    assert engine.adapter().params_id.startswith("fit-")
    assert engine.adapter_for("flashcard").params_id == "fsrs6-default"
    assert engine.training_items("flashcards") == []
    assert engine.parameter_sets() == ["skills"]
