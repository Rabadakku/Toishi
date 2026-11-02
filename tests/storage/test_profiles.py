"""PRO-1/2 profiles, EXP-2 .meprofile export/import, EXP-3 CSV."""

import csv
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from core.paths import DATA_DIR_ENV
from core.storage import (
    ProfileError,
    ProfileInUseError,
    ProfileManager,
    SchemaTooNewError,
    Storage,
)
from core.storage.export import read_manifest
from core.storage.schema import USER_SCHEMA_VERSION
from tests.storage import data
from tests.storage.data import some
from tests.storage.test_user_store import snapshot_everything


@pytest.fixture
def manager(tmp_path: Path, clock) -> ProfileManager:
    return ProfileManager(tmp_path / "data", clock=clock)


def test_create_list_rename_choose(manager: ProfileManager, clock) -> None:
    jamie = manager.create("  Jamie  ")
    assert jamie.name == "Jamie"
    assert jamie.id == "jamie"
    assert jamie.paths.user_db.is_file()
    assert jamie.paths.backups_dir.is_dir()
    assert jamie.paths.media_dir.is_dir()
    with pytest.raises(ProfileError, match="exists"):
        manager.create("JAMIE")
    alex = manager.create("Álex Q.")
    assert alex.id == "alex-q"
    assert [p.name for p in manager.list()] == ["Jamie", "Álex Q."]  # by casefolded name
    renamed = manager.rename(jamie.id, "Jamie (calc)")
    assert renamed.id == jamie.id
    assert renamed.paths == jamie.paths
    with pytest.raises(ProfileError):
        manager.rename(jamie.id, "álex q.")
    assert manager.last_chosen() is None
    clock.advance(seconds=1)
    assert manager.choose(alex.id).last_opened_at == clock.now_ms()
    clock.advance(seconds=1)
    manager.choose(jamie.id)
    assert some(manager.last_chosen()).id == jamie.id
    with pytest.raises(ProfileError):
        manager.get("nobody")
    for bad in ("", "   ", "x" * 81, "bell\x07"):
        with pytest.raises(ProfileError):
            manager.create(bad)


def test_delete_needs_confirmation_and_keeps_the_files(manager: ProfileManager, clock) -> None:
    jamie = manager.create("Jamie")
    with Storage.open(jamie.paths, clock=clock) as storage:
        storage.users.set_setting("daily.problems", 9)
        with pytest.raises(ProfileInUseError):
            manager.delete(jamie.id, confirm=True)
    with pytest.raises(ProfileError, match="confirm"):
        manager.delete(jamie.id)
    with pytest.raises(ProfileError, match="confirm"):
        manager.delete(jamie.id, confirm="yes")  # type: ignore[arg-type]
    moved = manager.delete(jamie.id, confirm=True)
    assert manager.list() == []
    assert (moved / "user.db").is_file()
    assert moved.parent == manager.deleted_dir
    again = manager.create("Jamie")  # the name is free again, with a fresh database
    with Storage.open(again.paths, clock=clock) as storage:
        assert storage.users.get_setting("daily.problems") == 20
    assert (moved / "user.db").is_file()


def test_data_dir_comes_from_the_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "custom"))
    manager = ProfileManager()
    manager.create("Env")
    assert (tmp_path / "custom" / "profiles" / "env" / "user.db").is_file()


def test_registry_is_rebuilt_from_folders(manager: ProfileManager, clock) -> None:
    jamie = manager.create("Jamie")
    registry = manager.data_dir / "profiles.db"
    for suffix in ("", "-wal", "-shm"):
        Path(str(registry) + suffix).unlink(missing_ok=True)
    registry.write_bytes(b"garbage" * 1000)
    found = manager.list()
    assert [(p.id, p.name) for p in found] == [(jamie.id, "jamie")]
    assert list(manager.data_dir.glob("profiles.db.damaged-*"))


def test_profile_export_import_round_trip(manager: ProfileManager, clock, pack_path) -> None:
    jamie = manager.create("Jamie")
    with Storage.open(jamie.paths, pack_paths=[pack_path], clock=clock) as storage:
        data.populate(storage.users, clock)
        (jamie.paths.media_dir / "img").mkdir()
        (jamie.paths.media_dir / "img" / "graph.svg").write_text("<svg/>")
        original = snapshot_everything(storage)
        out = manager.data_dir.parent / "exports" / "jamie.meprofile"
        manifest = manager.export(jamie.id, out)  # works while the profile is open
    assert manifest["counts"]["attempts"] == 12
    assert manifest["schema_version"] == USER_SCHEMA_VERSION
    assert read_manifest(out)["name"] == "Jamie"

    copy = manager.import_profile(out)
    assert copy.name == "Jamie (2)"
    assert copy.id != jamie.id
    assert (copy.paths.media_dir / "img" / "graph.svg").read_text() == "<svg/>"
    with Storage.open(copy.paths, pack_paths=[pack_path], clock=clock) as storage:
        assert snapshot_everything(storage) == original
    named = manager.import_profile(out, name="Jamie backup")
    assert named.name == "Jamie backup"


def test_export_refuses_what_import_would_refuse(manager: ProfileManager) -> None:
    jamie = manager.create("Jamie")
    (jamie.paths.media_dir / "graph\\1.png").write_bytes(b"x")  # a legal macOS file name
    out = manager.data_dir.parent / "exports" / "jamie.meprofile"
    with pytest.raises(ProfileError, match="graph"):  # now, not when the copy is needed
        manager.export(jamie.id, out)
    assert not out.exists()


def make_profile_zip(
    path: Path, entries: dict[str, bytes], manifest: dict[str, object] | None = None
) -> Path:
    files = {name: __import__("hashlib").sha256(body).hexdigest() for name, body in entries.items()}
    manifest = manifest or {"format": "meprofile", "version": 1, "name": "Evil", "files": files}
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        for name, body in entries.items():
            archive.writestr(name, body)
    return path


def test_import_rejects_unsafe_or_damaged_files(manager: ProfileManager, tmp_path: Path) -> None:
    good = manager.create("Source")
    out = tmp_path / "good.meprofile"
    manager.export(good.id, out)
    db_bytes = zipfile.ZipFile(out).read("user.db")

    cases = {
        "traversal": {"user.db": db_bytes, "media/../../evil": b"x"},
        "absolute": {"user.db": db_bytes, "/etc/evil": b"x"},
        "unexpected": {"user.db": db_bytes, "script.sh": b"x"},
        "no-db": {"media/a.png": b"x"},
        "not-sqlite": {"user.db": b"hello" * 100},
    }
    for label, entries in cases.items():
        bad = make_profile_zip(tmp_path / f"{label}.meprofile", entries)
        with pytest.raises(ProfileError):
            manager.import_profile(bad)
    lying = make_profile_zip(
        tmp_path / "lying.meprofile",
        {"user.db": db_bytes},
        {"format": "meprofile", "version": 1, "files": {"user.db": "0" * 64}},
    )
    with pytest.raises(ProfileError, match="checksum"):
        manager.import_profile(lying)
    with pytest.raises(ProfileError):
        manager.import_profile(
            make_profile_zip(tmp_path / "v9.meprofile", {}, {"format": "meprofile", "version": 9})
        )
    (tmp_path / "plain.txt").write_text("hi")
    with pytest.raises(ProfileError):
        manager.import_profile(tmp_path / "plain.txt")
    # newer schema inside
    newer = tmp_path / "newer.db"
    newer.write_bytes(db_bytes)
    conn = sqlite3.connect(newer)
    conn.execute("PRAGMA user_version = 42")
    conn.commit()
    conn.close()
    with pytest.raises(SchemaTooNewError, match=r"v42"):
        manager.import_profile(
            make_profile_zip(tmp_path / "n.meprofile", {"user.db": newer.read_bytes()})
        )
    assert [p.name for p in manager.list()] == ["Source"]
    assert not [p for p in manager.profiles_dir.iterdir() if p.name.startswith(".")]


def test_csv_exports(storage: Storage, clock, tmp_path: Path) -> None:
    data.populate(storage.users, clock)
    storage.users.undo_last_answer()
    counts = storage.export_csv(tmp_path / "csv")
    assert counts == {"review_log.csv": 6, "attempts.csv": 11}
    with (tmp_path / "csv" / "review_log.csv").open() as handle:
        reviews = list(csv.DictReader(handle))
    assert reviews[0]["target_id"] == data.SKILL
    assert reviews[0]["stability_after"] == "2.5"
    assert reviews[0]["at_utc"] == "2026-11-01T15:00:30.000+00:00"
    assert reviews[0]["study_day"] == "2026-11-01"
    assert reviews[0]["voided"] == "0"
    with (tmp_path / "csv" / "attempts.csv").open() as handle:
        attempts = list(csv.DictReader(handle))
    assert list(attempts[0])[:3] == ["id", "at", "at_utc"]
    assert "state_before" not in attempts[0]
    everything = storage.export_csv(tmp_path / "all", include_voided=True)
    assert everything == {"review_log.csv": 6, "attempts.csv": 12}
