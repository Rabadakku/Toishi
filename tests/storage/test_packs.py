import sqlite3
import stat
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from core.model import DEFAULT_MINUTES_PER_STEP, Card, CardPart, PackInfo, PackPace, Skill
from core.storage import (
    Database,
    NotOurDatabaseError,
    PackError,
    PackStore,
    PackWriter,
    Storage,
    StorageError,
    build_pack,
    open_pack,
    read_pack_info,
)
from core.storage.profiles import ProfilePaths
from core.storage.schema import PACK_APP_ID, PACK_SCHEMA_VERSION
from tests.storage import data
from tests.storage.data import some


def test_round_trip_of_every_card_field(pack_path: Path) -> None:
    with open_pack(pack_path) as pack:
        assert pack.content.card(data.CARD) == data.full_card()
        for card in data.other_cards():
            assert pack.content.card(card.id) == card
        assert pack.content.skills() == sorted(data.skills(), key=lambda s: s.id)
        assert pack.content.courses() == [data.tree()[0]]
        assert pack.content.units() == [data.tree()[1]]
        assert pack.content.sections() == data.tree()[2:]
        assert [r.rev for r in pack.content.revisions(data.CARD)] == [2, 3]
        assert pack.content.revisions(data.CARD)[1].answer_changed
        assert pack.media("media/f-graph.svg") == b"<svg/>"
        assert pack.pace() == data.PACE
        assert pack.verify()


def test_standard_times_and_the_pace_standard_live_in_pack_only_tables(pack_path: Path) -> None:
    """Pack schema v3: `time:` minutes in card_time (a card's own under part ''), the pace
    standard in pace and pace_section; the content tables are those of v2."""
    conn = sqlite3.connect(pack_path)
    try:
        times = conn.execute("SELECT card_id, part, minutes FROM card_time ORDER BY part")
        assert times.fetchall() == [(data.CARD, "", 7.5), (data.CARD, "a", 2.5)]
        assert conn.execute("SELECT * FROM pace").fetchall() == [(1, 1.25, 4.0)]
        sections = conn.execute("SELECT * FROM pace_section ORDER BY ord").fetchall()
        assert sections == [(0, "calc1.4-1", 6.0), (1, "calc1.4-4", 2.5)]
        columns = {r[1] for r in conn.execute("PRAGMA table_info(card)")}
        assert not any("time" in c for c in columns)
    finally:
        conn.close()


@pytest.mark.parametrize(
    "tamper",
    [
        "UPDATE card_time SET minutes = 1",
        "DELETE FROM card_time WHERE part = 'a'",
        "UPDATE pace SET weekly_hours = 9",
        "UPDATE pace_section SET hours = 1 WHERE ord = 1",
    ],
)
def test_tampering_with_times_or_pace_is_detected(pack_path: Path, tamper: str) -> None:
    pack_path.chmod(0o644)
    conn = sqlite3.connect(pack_path)
    conn.execute(tamper)
    conn.commit()
    conn.close()
    with open_pack(pack_path) as pack:
        assert not pack.verify()


def test_a_pack_without_a_pace_standard_reads_the_defaults(tmp_path: Path) -> None:
    path = tmp_path / "plain.db"
    build_pack(path, PackInfo(id="plain", title="Plain", version="1"), data.tree())
    with open_pack(path) as pack:
        assert pack.pace() == PackPace(minutes_per_step=DEFAULT_MINUTES_PER_STEP)
        assert pack.verify()


def test_sealed_pack_is_read_only_single_file(pack_path: Path) -> None:
    info = read_pack_info(pack_path)
    assert info.id == "calc1"
    assert info.schema_version == PACK_SCHEMA_VERSION
    assert info.content_hash.startswith("sha256:")
    assert not stat.S_IMODE(pack_path.stat().st_mode) & 0o222
    assert sorted(p.name for p in pack_path.parent.iterdir()) == ["calc1.db"]
    conn = sqlite3.connect(pack_path)
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert conn.execute("PRAGMA application_id").fetchone()[0] == PACK_APP_ID
    finally:
        conn.close()


def test_packs_cannot_be_written_through_the_app(storage: Storage) -> None:
    with storage.db.reading(packs=True) as conn:
        alias = storage.db.packs[0].alias
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(f"DELETE FROM {alias}.card")  # noqa: S608
    with open_pack(storage.db.packs[0].path) as pack:
        with pytest.raises(sqlite3.OperationalError):
            pack._conn.execute("UPDATE card SET tier = 1")
        assert pack.verify()


def test_tampering_is_detected(pack_path: Path) -> None:
    pack_path.chmod(0o644)
    conn = sqlite3.connect(pack_path)
    conn.execute("UPDATE card SET answer = '7' WHERE id = ?", (data.CARD,))
    conn.commit()
    conn.close()
    with open_pack(pack_path) as pack:
        assert not pack.verify()


def test_unsealed_or_foreign_files_are_refused(tmp_path: Path) -> None:
    writer = PackWriter.create(tmp_path / "p.db", PackInfo(id="p", title="P", version="1"))
    with pytest.raises(PackError, match="no pack file"):
        read_pack_info(tmp_path / "p.db")
    writer.abort()
    assert list(tmp_path.iterdir()) == []
    other = tmp_path / "other.db"
    sqlite3.connect(other).close()
    with pytest.raises(NotOurDatabaseError):
        read_pack_info(other)
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"not a database at all" * 100)
    with pytest.raises(PackError):
        read_pack_info(junk)


def test_writer_aborts_on_error_and_refuses_overwrite(tmp_path: Path, pack_path: Path) -> None:
    target = tmp_path / "new.db"

    def crashing_builder() -> None:
        with PackWriter.create(target, data.PACK_INFO) as writer:
            writer.add(*data.tree())
            raise RuntimeError("builder crashed")

    with pytest.raises(RuntimeError, match="builder crashed"):
        crashing_builder()
    assert not target.exists()
    assert not list(tmp_path.glob("*.building"))
    with pytest.raises(FileExistsError):
        PackWriter.create(pack_path, data.PACK_INFO)
    with pytest.raises(TypeError):
        build_pack(target, data.PACK_INFO, [object()])  # type: ignore[list-item]
    v2 = PackInfo(id="calc1", title="Calculus I", version="2026.12")
    with PackWriter.create(pack_path, v2, overwrite=True) as writer:
        writer.add(*data.tree())
        assert writer.seal().version == "2026.12"


def test_dangling_child_rows_fail_the_seal(tmp_path: Path) -> None:
    with PackWriter.create(tmp_path / "bad.db", data.PACK_INFO) as writer:
        writer.conn.execute("PRAGMA defer_foreign_keys = ON")  # FKs are on; check at seal
        writer.conn.execute(
            "INSERT INTO card_use (card_id, ord, skill_id) VALUES ('ghost', 0, 'x')"
        )
        with pytest.raises(PackError, match="missing rows"):
            writer.seal()


def test_pack_store_reads_across_packs_and_own_content(storage: Storage, tmp_path: Path) -> None:
    algebra = tmp_path / "alg.db"
    build_pack(
        algebra,
        PackInfo(id="alg", title="Algebra", version="1"),
        [
            Skill(id="alg.solve.linear", name="Solve linear"),
            Card(id="alg.solve.001", skill_id="alg.solve.linear", question_md="2x = 4"),
        ],
    )
    storage.db.attach_pack(algebra)
    storage.users.put_user_content(
        Card(id="mine.001", skill_id="alg.solve.linear", question_md="3x = 9", answer="3")
    )
    packs = storage.packs
    assert [p.id for p in packs.packs()] == ["calc1", "alg"]
    assert packs.card(data.CARD) == data.full_card()
    assert packs.card_source("alg.solve.001") == "alg"
    assert packs.card_source("mine.001") == "user"
    assert packs.card_source("nope") is None
    pool = packs.card_refs(skill_id="alg.solve.linear")
    assert [(r.id, r.source) for r in pool] == [("alg.solve.001", "alg"), ("mine.001", "user")]
    retired = packs.card_refs(skill_id="calc1.deriv.power-rule", include_retired=True)
    assert [r.status for r in retired] == ["retired"]
    assert packs.card_refs(skill_id="calc1.deriv.power-rule") == []
    assert len(packs.cards_for_skill(data.SKILL)) == 2
    assert {e.kind for e in packs.edges()} == {"requires", "encompasses", "confusable"}
    assert [s.id for s in packs.skills_in_section("calc1.4-4")] == ["calc1.select.limit-technique"]
    assert packs.media("calc1", "media/f-graph.svg") == b"<svg/>"
    assert packs.media("alg", "nope") is None
    with pytest.raises(PackError, match="already attached"):
        storage.db.attach_pack(algebra)
    storage.db.detach_pack("alg")
    assert packs.card("alg.solve.001") is None
    assert PackStore(storage.db, include_user=False).card("mine.001") is None


def test_update_pack_backs_up_and_swaps(storage: Storage, tmp_path: Path) -> None:
    newer = tmp_path / "calc1-v2.db"
    changed = Card(id=data.CARD, rev=4, skill_id=data.SKILL, question_md="new wording")
    build_pack(newer, PackInfo(id="calc1", title="Calculus I", version="v2"), [changed])
    info = storage.update_pack(newer)
    assert info.version == "v2"
    assert storage.packs.card(data.CARD) == changed
    assert [b.reason for b in storage.backups.all()] == ["pre-pack-update"]


def test_pack_reads_are_refused_inside_a_write_job(storage: Storage) -> None:
    from core.storage import StorageError

    with pytest.raises(StorageError, match="before submitting"):
        storage.db.write(lambda _conn: storage.packs.card(data.CARD))


def test_too_new_pack_schema_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    build_pack(path, data.PACK_INFO, data.tree())
    path.chmod(0o644)
    conn = sqlite3.connect(path)
    conn.execute(f"PRAGMA user_version = {PACK_SCHEMA_VERSION + 1}")
    conn.commit()
    conn.close()
    with pytest.raises(PackError, match="reads up to"):
        read_pack_info(path)
    db_path = tmp_path / "u" / "user.db"
    with pytest.raises(PackError):
        Database.open(db_path, create=True, pack_paths=[path])
    Database.open(db_path).close()  # the failed attach released the profile lock


def test_a_damaged_pack_is_refused_as_a_pack_error(tmp_path: Path, pack_path: Path) -> None:
    damaged = tmp_path / "damaged.db"
    damaged.write_bytes(pack_path.read_bytes())
    with damaged.open("r+b") as handle:  # the header survives, the pages behind it do not
        handle.seek(4096)
        handle.write(b"\xff" * 3 * 4096)
    with pytest.raises(PackError):
        read_pack_info(damaged)
    with pytest.raises(PackError):  # so the app can tell a bad pack from bad progress
        Storage.open(ProfilePaths(tmp_path / "profile"), pack_paths=[damaged], create=True)


def test_a_vanished_pack_never_blocks_reading_progress(storage: Storage, pack_path: Path) -> None:
    storage.users.set_setting("daily.problems", 31)
    pack_path.unlink()  # say, an imported pack deleted in Finder while the app runs
    seen: list[object] = []

    def bridge_call() -> None:  # a new thread opens a new reader, which attaches packs
        try:
            seen.append(storage.users.get_setting("daily.problems"))
        except Exception as error:  # reported by the assert below
            seen.append(error)

    thread = threading.Thread(target=bridge_call)
    thread.start()
    thread.join()
    assert seen == [31]


def test_own_cards_have_exactly_the_shape_of_pack_cards(storage: Storage, pack_path: Path) -> None:
    """user_card reaches v2 by ALTER TABLE; a pack's card table is built whole. Pack schema
    v3 adds only pack-only tables, so the shapes still match."""
    with storage.db.reading(packs=True) as conn:
        alias = storage.db.packs[0].alias
        for table in ("card", "card_part", "card_step", "skill", "card_revision"):
            pack = [tuple(r)[1:] for r in conn.execute(f"PRAGMA {alias}.table_info({table})")]
            own = [tuple(r)[1:] for r in conn.execute(f"PRAGMA main.table_info(user_{table})")]
            assert own == pack, table
        for table in ("card_time", "pace", "pace_section"):
            assert conn.execute(f"PRAGMA {alias}.table_info({table})").fetchall()
            assert not conn.execute(f"PRAGMA main.table_info(user_{table})").fetchall()
            assert not conn.execute(f"PRAGMA main.table_info({table})").fetchall()
    assert read_pack_info(pack_path).schema_version == PACK_SCHEMA_VERSION == 3


def test_pack_store_reads_standard_times_and_the_pace_standard(storage: Storage) -> None:
    packs = storage.packs
    card = some(packs.card(data.CARD))
    assert card.time_minutes == 7.5
    assert [p.time_minutes for p in card.parts] == [2.5, None]
    assert packs.pace("calc1") == data.PACE
    assert packs.pace("no-such-pack") is None


def test_own_cards_cannot_hold_standard_times(storage: Storage) -> None:
    """user.db has no card_time table: storing a time would lose it, so it is refused (the
    importer drops `time:` from own cards with a warning first)."""
    timed = Card(id="mine.t.001", question_md="Q", time_minutes=3.0)
    part = CardPart(label="a", prompt_md="P", time_minutes=1.0)
    for card in (timed, replace(timed, time_minutes=None, parts=(part,))):
        with pytest.raises(StorageError, match="kept in packs only"):
            storage.users.put_user_content(card)
    assert storage.users.user_card(timed.id) is None


def test_instance_parameters_round_trip_in_packs_and_own_cards(storage: Storage) -> None:
    card = data.full_card()
    assert storage.packs.card(card.id) == card
    assert card.params == "k = 3; m = 1/2"
    own = Card(id="mine.t--0000002a", template_id="mine.t", seed=42, params="", question_md="Q")
    storage.users.put_user_content(own)
    assert storage.users.user_card(own.id) == own  # "" (no parameters) is not None
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):  # only instances have them
        storage.db.write(
            lambda conn: conn.execute(
                "UPDATE user_card SET template_id = NULL WHERE id = ?", (own.id,)
            )
        )
