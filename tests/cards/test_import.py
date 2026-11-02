"""Importing into a profile: dry run, one transaction, updates keep history, nothing deleted."""

from pathlib import Path

import pytest

from core.cards import ImportPlan, Source, StoredMedia, apply_import, plan_import, template_sources
from core.model import ImportRecord
from core.storage import FixedClock, Storage, UserStore
from core.storage.media import media_file_name
from tests.cards.helpers import cards_file

CARD_A = """
## Card a.001
skill: s.a
difficulty: 1
answer-type: number
answer: 2

### Question
What is \\(1 + 1\\)?

### Hints
1. Count.

### Solution
0. [s.a] Add: \\(1 + 1 = 2\\).
"""
CARD_B = CARD_A.replace("a.001", "b.001").replace("1 + 1", "3 - 1")
TEMPLATE = """
## Card t.001
skill: s.t
difficulty: 1
answer-type: number
vars: k = int(1, 4)
answer: 2*k

### Question
Double [[k]].

### Hints
1. Add it to itself.

### Solution
0. [s.t] Double: [[2*k]].
"""


def src(body: str, name: str = "deck.cards.md") -> Source:
    return Source(name, cards_file(body))


def run(
    store: UserStore, body: str, name: str = "deck.cards.md", retire: tuple[str, ...] = ()
) -> ImportPlan:
    plan = plan_import(store, [src(body, name)])
    apply_import(store, plan, retire)
    return plan


@pytest.fixture
def store(storage: Storage) -> UserStore:
    return storage.users


def test_dry_run_writes_nothing_and_reports(store: UserStore) -> None:
    bad = "\n## Card c.001\nkind: puzzle\n\n### Question\nQ\n"
    plan = plan_import(store, [src(CARD_A + bad)])
    assert [c.card.id for c in plan.added] == ["a.001"]
    assert [(r.card_id, r.file, r.line) for r in plan.rejected] == [("c.001", "deck.cards.md", 22)]
    assert store.user_cards() == []
    report = plan.report()
    assert "added: 1  updated: 0  unchanged: 0  rejected: 1" in report
    assert "deck.cards.md:22: c.001 rejected: kind: expected" in report


def test_apply_writes_cards_skills_tree_revisions_and_log(store: UserStore) -> None:
    plan = run(store, CARD_A + TEMPLATE)
    cards = {c.id: c for c in store.user_cards()}
    assert len(cards) == 5
    assert "a.001" in cards
    assert all(c.verified == "unverified" and c.rev == 1 for c in cards.values())  # IMP-7
    assert {s.id for s in store.user_skills()} == {"s.a", "s.t"}  # created automatically
    assert {s.name for s in plan.skills_created} == {"s.a", "s.t"}
    (record,) = store.imports()
    assert record.kind == "cards"
    assert record.file == "deck.cards.md"
    files = record.summary["files"]["deck.cards.md"]
    assert files["ids"] == ["a.001", "t.001"]
    assert files["templates"] == ["t.001"]  # the log names it; its source is stored apart
    source = store.user_template("t.001")
    assert source is not None
    assert source.source_md.startswith("## Card t.001\ndeck: Test::Unit::Section")
    assert source.updated_at == store.db.clock.now_ms()
    assert store.template_sources() == {"t.001": source.source_md}
    instances = [c for c in cards.values() if c.template_id == "t.001"]
    assert sorted(c.params or "" for c in instances) == ["k = 1", "k = 2", "k = 3", "k = 4"]
    assert all(c.notes_md is None for c in instances)  # notes_md stays the author's
    with store.db.reading() as conn:
        revs = conn.execute(
            "SELECT card_id, rev, note FROM user_card_revision ORDER BY card_id"
        ).fetchall()
        sections = [r[0] for r in conn.execute("SELECT id FROM user_section")]
    assert ("a.001", 1, "added from deck.cards.md") in [tuple(r) for r in revs]
    assert sections == ["Test::Unit::Section"]


def test_reimport_is_unchanged(store: UserStore) -> None:
    run(store, CARD_A + TEMPLATE)
    plan = plan_import(store, [src(CARD_A + TEMPLATE)])
    assert plan.nothing_to_do
    assert len(plan.unchanged) == 5
    assert plan.added == []
    assert plan.updated == []


def test_changed_key_is_recorded_and_history_kept(store: UserStore) -> None:
    run(store, CARD_A)
    plan = run(store, CARD_A.replace("answer: 2", "answer: 2\nwrong: 3"))
    assert [(c.card.id, c.key_changed) for c in plan.updated] == [("a.001", False)]
    plan = run(store, CARD_A.replace("1 + 1", "1 + 2").replace("answer: 2", "answer: 3"))
    (change,) = plan.updated
    assert change.key_changed
    assert change.card.rev == 3
    assert change.old is not None
    assert change.old.answer == "2"
    assert store.user_card("a.001").answer == "3"  # type: ignore[union-attr]
    with store.db.reading() as conn:
        rows = conn.execute(
            "SELECT rev, note, answer_changed FROM user_card_revision "
            "WHERE card_id = 'a.001' ORDER BY rev"
        ).fetchall()
    assert [tuple(r) for r in rows] == [
        (1, "added from deck.cards.md", 0),
        (2, "content updated from deck.cards.md", 0),
        (3, "answer key updated from deck.cards.md", 1),
    ]


def test_missing_cards_are_listed_and_retired_only_when_chosen(store: UserStore) -> None:
    run(store, CARD_A + CARD_B)
    plan = run(store, CARD_A)
    assert plan.missing == ["b.001"]
    assert store.user_card("b.001").status == "active"  # type: ignore[union-attr]
    plan = run(store, CARD_A, retire=("b.001",))
    assert store.user_card("b.001").status == "retired"  # type: ignore[union-attr]
    again = plan_import(store, [src(CARD_A + CARD_B)])  # a retired card stays retired
    assert [a.card.id for a in again.unchanged] == ["a.001", "b.001"]
    with pytest.raises(ValueError, match="listed as missing"):
        apply_import(store, plan_import(store, [src(CARD_A)]), ["a.001"])


def test_other_files_are_not_missing(store: UserStore) -> None:
    run(store, CARD_A, "one.cards.md")
    plan = plan_import(store, [src(CARD_B, "two.cards.md")])
    assert plan.missing == []


def test_template_instances_follow_the_template(store: UserStore) -> None:
    run(store, TEMPLATE)
    plan = run(store, TEMPLATE.replace("int(1, 4)", "int(1, 2)"))
    assert len(plan.retire_instances) == 2
    active = [c for c in store.user_cards() if c.status == "active"]
    assert sorted(c.answer for c in active) == ["2", "4"]  # type: ignore[type-var]
    plan = run(store, CARD_A, retire=("t.001",))
    assert plan.missing == ["t.001"]
    assert all(c.status == "retired" for c in store.user_cards() if c.template_id == "t.001")


def test_pack_ids_cannot_be_reused(store: UserStore) -> None:
    plan = plan_import(
        store, [src(CARD_A + TEMPLATE)], pack_cards={"a.001": "calc1", "t.001": "calc1"}
    )
    assert plan.added == []
    assert sorted(r.reasons[0] for r in plan.rejected) == [
        "ID a.001 is already used by pack calc1",
        "ID t.001 is already used by pack calc1",
    ]
    plan = plan_import(store, [src(CARD_A)], pack_skills={"s.a": "calc1"})
    assert plan.skills_created == []  # the pack defines it


def test_skills_file(store: UserStore) -> None:
    skills = Source(
        "skills.md",
        "---\nformat: mastery-skills 1\n---\n\n## Skill s.a\nname: Add\nrequires: s.base\n\n"
        "## Skill s.base\nname: Count\ncore: yes\nexam-tier: 2\n",
    )
    plan = plan_import(store, [src(CARD_A)], [skills])
    assert sorted(s.id for s in plan.skills_added) == ["s.a", "s.base"]
    apply_import(store, plan)
    stored = {s.id: s for s in store.user_skills()}
    assert stored["s.a"].requires == ("s.base",)
    assert stored["s.base"].core
    assert stored["s.base"].exam_tier == 2
    again = plan_import(store, [src(CARD_A)], [skills])
    assert sorted(s.id for s in again.skills_unchanged) == ["s.a", "s.base"]


def test_skill_cycles_are_rejected(store: UserStore) -> None:
    skills = Source(
        "skills.md",
        "---\nformat: mastery-skills 1\n---\n\n## Skill s.a\nname: A\nrequires: s.b\n\n"
        "## Skill s.b\nname: B\nrequires: s.a\n",
    )
    plan = plan_import(store, [], [skills])
    assert plan.skills_added == []
    assert [(p.line, p.message) for p in plan.skill_problems] == [
        (7, "prerequisites form a cycle: s.a -> s.b -> s.a")
    ]


def test_claimed_verification_is_ignored(store: UserStore) -> None:
    plan = plan_import(
        store, [src(CARD_A.replace("difficulty: 1", "difficulty: 1\nverified: blind-solve"))]
    )
    assert plan.added[0].card.verified == "unverified"
    assert any("verified: blind-solve is ignored" in w.message for w in plan.warnings)


def test_standard_times_stay_with_content_packs(store: UserStore) -> None:
    """user.db keeps no `time:`: own cards import without it, warned once per card or
    template, and the same file imports again unchanged."""
    timed = CARD_A.replace("difficulty: 1", "difficulty: 1\ntime: 2.5")
    template = TEMPLATE.replace("answer: 2*k", "answer: 2*k\ntime: [[k]]")
    plan = run(store, timed + template)
    warned = [(w.card_id, w.message) for w in plan.warnings if "time:" in w.message]
    message = "time: is kept by content packs only; this card imports without it"
    assert warned == [("a.001", message), ("t.001", message)]
    assert all(c.time_minutes is None for c in store.user_cards())
    assert len(store.user_cards()) == 5
    again = plan_import(store, [src(timed + template)])
    assert again.nothing_to_do


def test_the_import_is_one_transaction(store: UserStore, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = plan_import(store, [src(CARD_A + TEMPLATE)])

    def boom(record: object) -> object:
        raise RuntimeError("disk full")

    monkeypatch.setattr(store, "log_import", boom)
    with pytest.raises(RuntimeError, match="disk full"):
        apply_import(store, plan)
    assert store.user_cards() == []
    assert store.user_skills() == []
    assert store.imports() == []


def test_files_on_disk_with_images(store: UserStore, tmp_path: Path) -> None:
    (tmp_path / "media").mkdir()
    (tmp_path / "media" / "g.svg").write_text("<svg/>")
    path = tmp_path / "deck.cards.md"
    path.write_text(cards_file(CARD_A.replace("What is", "![g](media/g.svg)\nWhat is")))
    plan = plan_import(store, [Source.from_path(path)])
    assert [c.card.id for c in plan.added] == ["a.001"]


# ---------------------------------------------------------------- images (the media store)

IMAGE_CARD = CARD_A.replace("What is", "![g](media/g.svg)\nWhat is")


def image_deck(folder: Path, svg: str, body: str = IMAGE_CARD) -> Source:
    (folder / "media").mkdir(parents=True, exist_ok=True)
    (folder / "media" / "g.svg").write_text(svg)
    (folder / "deck.cards.md").write_text(cards_file(body))
    return Source.from_path(folder / "deck.cards.md")


def test_imported_images_are_stored_and_linked(store: UserStore, tmp_path: Path) -> None:
    first = image_deck(tmp_path / "v1", "<svg>1</svg>")
    plan = plan_import(store, [first])
    assert plan.media == {"a.001": {"media/g.svg": b"<svg>1</svg>"}}
    assert plan.media_changed == ["a.001"]
    assert "cards whose images are stored anew: 1" in plan.report()
    apply_import(store, plan)
    old = media_file_name(b"<svg>1</svg>", "g.svg")
    assert store.media.links("a.001") == {"media/g.svg": old}
    assert store.media.read("a.001", "media/g.svg") == b"<svg>1</svg>"
    assert plan_import(store, [image_deck(tmp_path / "v1", "<svg>1</svg>")]).nothing_to_do
    # the same card, a new picture: only the image changes
    plan = plan_import(store, [image_deck(tmp_path / "v2", "<svg>2</svg>")])
    assert (plan.added, plan.updated, plan.media_changed) == ([], [], ["a.001"])
    assert not plan.nothing_to_do
    apply_import(store, plan)
    assert store.media.read("a.001", "media/g.svg") == b"<svg>2</svg>"
    assert store.media.path(old).is_file()  # never deleted: older backups point at it
    # the image taken out of the card: its reference goes too
    plan = plan_import(store, [image_deck(tmp_path / "v3", "<svg>2</svg>", CARD_A)])
    assert [c.card.id for c in plan.updated] == ["a.001"]
    assert plan.media_changed == ["a.001"]
    apply_import(store, plan)
    assert store.media.links("a.001") == {}


def test_a_failed_import_points_no_card_at_a_missing_file(
    store: UserStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = plan_import(store, [image_deck(tmp_path, "<svg/>")])

    def boom(record: object) -> object:
        raise RuntimeError("disk full")

    monkeypatch.setattr(store, "log_import", boom)
    with pytest.raises(RuntimeError, match="disk full"):
        apply_import(store, plan)
    assert store.media.all_links() == []
    assert store.media.path(media_file_name(b"<svg/>", "g.svg")).is_file()  # harmless


def test_the_editor_resolves_stored_and_added_images(store: UserStore, tmp_path: Path) -> None:
    apply_import(store, plan_import(store, [image_deck(tmp_path, "<svg>stored</svg>")]))
    edited = IMAGE_CARD.replace("### Hints", "![p](plot.png)\n\n### Hints")
    draft = Source(
        "draft.cards.md", cards_file(edited), StoredMedia(store.media, "a.001", {"plot.png": b"P"})
    )
    plan = plan_import(store, [draft])
    assert plan.rejected == []
    assert [c.card.id for c in plan.updated] == ["a.001"]
    assert plan.media["a.001"] == {"media/g.svg": b"<svg>stored</svg>", "plot.png": b"P"}
    apply_import(store, plan)
    assert store.media.read("a.001", "plot.png") == b"P"
    assert store.media.read("a.001", "media/g.svg") == b"<svg>stored</svg>"
    missing = Source("draft.cards.md", cards_file(edited), StoredMedia(store.media, None))
    (rejected,) = plan_import(store, [missing]).rejected
    assert "not found" in rejected.reasons[0]


# ---------------------------------------------------------------- template sources


def test_template_sources_are_stored_and_a_source_only_change_is_applied(
    store: UserStore, clock: FixedClock
) -> None:
    run(store, TEMPLATE)
    first = store.user_template("t.001")
    assert first is not None
    assert "Double [[k]]." in first.source_md
    commented = TEMPLATE.replace("### Hints", "<!-- easy one -->\n### Hints")
    plan = plan_import(store, [src(commented)])
    assert (plan.added, plan.updated, plan.sources_changed) == ([], [], ["t.001"])
    assert not plan.nothing_to_do
    clock.advance(seconds=5)
    apply_import(store, plan)
    second = store.user_template("t.001")
    assert second is not None
    assert "<!-- easy one -->" in second.source_md
    assert second.updated_at == first.updated_at + 5000
    assert plan_import(store, [src(commented)]).nothing_to_do


def test_template_sources_still_read_logs_written_before_v2() -> None:
    v1_summary = {"files": {"a.cards.md": {"ids": ["t.001"], "templates": {"t.001": "## v1"}}}}
    v2_summary = {"files": {"a.cards.md": {"ids": ["t.001"], "templates": ["t.001"]}}}
    records = [
        ImportRecord(id=1, at=1, file="a.cards.md", kind="cards", summary=v1_summary),
        ImportRecord(id=2, at=2, file="a.cards.md", kind="cards", summary=v2_summary),
        ImportRecord(id=3, at=3, file="x.apkg", kind="apkg", summary=v1_summary),
    ]
    assert template_sources(records) == {"t.001": "## v1"}
