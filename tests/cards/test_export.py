"""EXP-1: the student's own cards and skills export as card files and re-import unchanged."""

from dataclasses import replace
from pathlib import Path

from core.cards import (
    Source,
    apply_import,
    card_block,
    export_cards,
    export_media,
    export_skills,
    load,
    plan_import,
)
from core.cards.load import skills_in, sources_in
from core.storage import Storage
from tests.cards.test_doc_examples import examples

ROOT = Path(__file__).resolve().parents[2]


def test_export_reimports_unchanged(storage: Storage, tmp_path: Path) -> None:
    store = storage.users
    doc = next(b for b in examples() if "calc1.4-4.method-limit.001" in b)
    sources = [Source("calc1-ch4-sample.cards.md", doc)]
    sources += sources_in(ROOT / "packs" / "test") + sources_in(ROOT / "packs" / "tutorial")
    plan = plan_import(store, sources, skills_in(ROOT / "packs" / "test"))
    assert plan.rejected == []
    assert plan.file_problems == []
    assert plan.skill_problems == []
    apply_import(store, plan)
    cards = store.user_cards()
    assert len(cards) > 100

    files, warnings = export_cards(cards, store.template_sources())
    assert warnings == []
    images, image_warnings = export_media(cards, store.media)
    assert image_warnings == []
    assert images == {"media/parabola.svg": (ROOT / "packs/test/media/parabola.svg").read_bytes()}
    skills_text = export_skills(store.user_skills())
    out = tmp_path / "export"
    out.mkdir()
    for name, text in files.items():
        (out / name).write_text(text)
    (out / "skills.md").write_text(skills_text)
    for path, data in images.items():  # images come from the profile's media store
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_bytes(data)

    again = plan_import(store, sources_in(out), skills_in(out))
    assert again.rejected == []
    assert again.file_problems == []
    assert again.skill_problems == []
    assert again.added == []
    assert again.updated == []
    assert again.retire_instances == []
    assert again.sources_changed == []
    assert again.media_changed == []
    assert again.nothing_to_do
    assert len(again.unchanged) == len(cards)
    assert again.skills_added == []
    assert again.skills_updated == []
    assert again.skills_created == []
    assert {s.id for s in again.skills_unchanged} == {s.id for s in store.user_skills()}


def test_card_block_round_trips_every_field() -> None:
    result = load(sources_in(ROOT / "packs" / "test"))
    fixed = [a.card for a in result.cards if a.card.template_id is None]
    text = (
        "---\nformat: mastery-cards 1\n---\n\n" + "\n\n".join(card_block(c) for c in fixed) + "\n"
    )
    back = load([Source("x.cards.md", text)])
    assert back.errors() == []
    assert [a.card for a in back.cards] == fixed


def test_card_block_writes_standard_times_that_read_back() -> None:
    result = load(sources_in(ROOT / "packs" / "test"))
    cards = [a.card for a in result.cards]
    fixed = [c for c in cards if c.template_id is None and c.kind == "problem"]
    multi = next(c for c in fixed if c.parts)
    single = next(c for c in fixed if not c.parts)
    timed = [
        replace(single, time_minutes=6.5),
        replace(single, id="t.tiny.001", time_minutes=1e-7),  # never written with an exponent
        replace(multi, time_minutes=12.0, parts=(replace(multi.parts[0], time_minutes=2.25),)),
    ]
    blocks = [card_block(c) for c in timed]
    assert "\ntime: 6.5\n" in blocks[0]
    assert "\ntime: 0.0000001\n" in blocks[1]
    assert "\ntime: 12\n" in blocks[2]
    assert "\ntime: 2.25\n" in blocks[2]
    back = load(
        [Source("x.cards.md", "---\nformat: mastery-cards 1\n---\n\n" + "\n\n".join(blocks))]
    )
    assert back.errors() == []
    assert [a.card for a in back.cards] == timed
