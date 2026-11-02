"""The student's own media (ADR-0011): content-addressed files beside user.db, a table of
card image references, and an exact round trip through .meprofile export and import."""

import hashlib
import sqlite3
import zipfile
from pathlib import Path

import pytest

from core.model import Card
from core.storage import MediaError, ProfileError, ProfileManager, Storage
from core.storage.export import export_profile
from core.storage.media import check_file_name, media_file_name, unsafe_name
from core.storage.profiles import ProfilePaths
from tests.storage.test_profiles import make_profile_zip

SVG = b"<svg xmlns='http://www.w3.org/2000/svg'/>"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def own_card(storage: Storage, card_id: str = "mine.001") -> str:
    storage.users.put_user_content(Card(id=card_id, question_md="![g](media/g.svg) Q?"))
    return card_id


def test_files_are_content_addressed_in_the_profile_folder(storage: Storage, paths) -> None:
    media = storage.media
    assert media.folder == paths.media_dir
    name = media.add(SVG, "media/G.SVG")
    assert name == f"{sha(SVG)}.svg"
    assert (paths.media_dir / name).read_bytes() == SVG
    assert media.add(SVG, "other/name.svg") == name  # the same bytes are stored once
    assert media.add(PNG, "plot.png") == f"{sha(PNG)}.png"
    assert media.add(PNG, "no-extension") == sha(PNG)
    assert media_file_name(PNG, "x.verylongext") == sha(PNG)
    assert media_file_name(PNG, "a\\b.Png") == f"{sha(PNG)}.png"
    assert sorted(p.name for p in paths.media_dir.iterdir()) == sorted(
        [name, f"{sha(PNG)}.png", sha(PNG)]
    )  # nothing else: no temporary files left behind
    (paths.media_dir / name).write_bytes(b"damaged")
    assert media.add(SVG, "g.svg") == name  # a damaged copy is replaced
    assert media.read_file(name) == SVG


def test_names_are_checked_like_meprofile_entries() -> None:
    good = "a" * 64 + ".svg"
    assert check_file_name(good) == good
    for bad in ("../" + good, "x/" + good, "A" * 64, "a" * 63, good + "/", "a" * 64 + ".", ""):
        with pytest.raises(MediaError):
            check_file_name(bad)
    for bad in ("", "a//b", "./a", "a/../b", "/abs", "a\\b", "nul\x00", "x" * 513):
        assert unsafe_name(bad), bad
    assert not unsafe_name("media/" + good)


def test_card_references_point_at_stored_files(storage: Storage) -> None:
    media = storage.media
    card = own_card(storage)
    names = media.set_card_media(card, {"media/g.svg": SVG, "plot.png": PNG})
    assert (
        media.links(card)
        == names
        == {"media/g.svg": f"{sha(SVG)}.svg", "plot.png": names["plot.png"]}
    )
    assert media.read(card, "media/g.svg") == SVG
    assert media.read(card, "nope.svg") is None
    media.link(card, {"media/g.svg": names["plot.png"]})  # replaces every earlier one
    assert media.links(card) == {"media/g.svg": names["plot.png"]}
    media.link(card, {})
    assert media.links(card) == {}
    assert media.all_links() == []


def test_links_are_refused_unless_safe_stored_and_owned(storage: Storage) -> None:
    media = storage.media
    card = own_card(storage)
    stored = media.add(SVG, "g.svg")
    with pytest.raises(MediaError, match="no stored media file"):
        media.link(card, {"g.svg": "b" * 64 + ".svg"})
    with pytest.raises(MediaError, match="not a media file name"):
        media.link(card, {"g.svg": "../../etc/passwd"})
    with pytest.raises(MediaError, match="not an image reference"):
        media.link(card, {"": stored})
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        media.link("not.an.own.card", {"g.svg": stored})  # own cards only
    assert media.all_links() == []


def test_problems_lists_missing_or_damaged_files(storage: Storage) -> None:
    media = storage.media
    card = own_card(storage)
    names = media.set_card_media(card, {"g.svg": SVG, "p.png": PNG})
    assert media.problems() == []
    media.path(names["g.svg"]).write_bytes(b"changed")
    media.path(names["p.png"]).unlink()
    assert media.problems() == [
        f"card {card}: g.svg -> {names['g.svg']} is missing or damaged",
        f"card {card}: p.png -> {names['p.png']} is missing or damaged",
    ]


def test_an_older_backup_still_finds_its_images(storage: Storage, paths: ProfilePaths) -> None:
    media = storage.media
    card = own_card(storage)
    media.set_card_media(card, {"g.svg": SVG})
    backup = storage.backups.create("manual")
    media.set_card_media(card, {"g.svg": b"<svg>new</svg>"})
    storage.close(backup=False)
    storage.backups.restore(backup)
    with Storage.open(paths) as restored:
        assert restored.media.read(card, "g.svg") == SVG  # files are never deleted


# ---------------------------------------------------------------- .meprofile


@pytest.fixture
def manager(tmp_path: Path, clock) -> ProfileManager:
    return ProfileManager(tmp_path / "data", clock=clock)


def with_images(manager: ProfileManager) -> tuple[str, dict[str, str]]:
    profile = manager.create("Jamie")
    with Storage.open(profile.paths) as storage:
        card = own_card(storage)
        names = storage.media.set_card_media(card, {"media/g.svg": SVG, "plot.png": PNG})
        own_card(storage, "mine.002")
        storage.media.link("mine.002", {"same.svg": names["media/g.svg"]})  # shared file
    return profile.id, names


def test_meprofile_round_trips_own_media(manager: ProfileManager, tmp_path: Path) -> None:
    source, names = with_images(manager)
    out = tmp_path / "jamie.meprofile"
    manifest = manager.export(source, out)
    for name in names.values():
        assert manifest["files"][f"media/{name}"] == name.split(".")[0]  # content address
    copy = manager.import_profile(out)
    with Storage.open(copy.paths) as storage:
        assert storage.media.links("mine.001") == names
        assert storage.media.read("mine.001", "media/g.svg") == SVG
        assert storage.media.read("mine.001", "plot.png") == PNG
        assert storage.media.read("mine.002", "same.svg") == SVG
        assert storage.media.problems() == []


def test_export_refuses_a_missing_or_damaged_image(manager: ProfileManager, tmp_path: Path) -> None:
    source, names = with_images(manager)
    path = manager.get(source).paths.media_dir / names["plot.png"]
    path.write_bytes(b"damaged")
    with pytest.raises(ProfileError, match=r"'plot.png' of card mine.001 .* damaged"):
        manager.export(source, tmp_path / "x.meprofile")
    path.unlink()
    with pytest.raises(ProfileError, match="missing or damaged"):
        manager.export(source, tmp_path / "x.meprofile")
    assert not (tmp_path / "x.meprofile").exists()


def rebuilt(src: Path, dest: Path, sql: str = "", media: dict[str, bytes] | None = None) -> Path:
    """The archive's entries with user.db changed by `sql` and media entries replaced."""
    with zipfile.ZipFile(src) as archive:
        entries = {i.filename: archive.read(i) for i in archive.infolist()}
    del entries["manifest.json"]
    db = dest.with_suffix(".db")
    db.write_bytes(entries["user.db"])
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA ignore_check_constraints = ON")  # a crafted file obeys no CHECK
    conn.execute("PRAGMA foreign_keys = OFF")
    if sql:
        conn.executescript(sql)
    conn.commit()
    conn.close()
    entries["user.db"] = db.read_bytes()
    entries.update(media or {})
    return make_profile_zip(dest, entries, None)


def test_import_refuses_unsafe_missing_or_damaged_media(
    manager: ProfileManager, tmp_path: Path
) -> None:
    source, names = with_images(manager)
    good = tmp_path / "good.meprofile"
    manager.export(source, good)
    svg = names["media/g.svg"]
    absent = "c" * 64 + ".svg"
    no_checks = (  # an attacker writes the file: no CHECK constraint holds them back
        "CREATE TABLE m (card_id TEXT NOT NULL, ref TEXT NOT NULL, file TEXT NOT NULL, "
        "PRIMARY KEY (card_id, ref)) STRICT; INSERT INTO m SELECT * FROM user_media; "
        "DROP TABLE user_media; ALTER TABLE m RENAME TO user_media; "
    )
    bad = {
        "unsafe name, CHECK kept": (
            rebuilt(
                good,
                tmp_path / "checked.meprofile",
                "INSERT INTO user_media VALUES ('mine.001', 'x.svg', '../../user.db')",
            ),
            "damaged: .*CHECK constraint failed in user_media",
        ),
        "unsafe name": (
            rebuilt(
                good,
                tmp_path / "unsafe.meprofile",
                no_checks + "INSERT INTO user_media VALUES ('mine.001', 'x.svg', '../user.db')",  # noqa: S608
            ),
            r"unsafe media file name in profile file: '\.\./user\.db'",
        ),
        "not in the archive": (
            rebuilt(
                good,
                tmp_path / "absent.meprofile",
                "INSERT INTO user_media VALUES ('mine.001', 'x.svg', '" + absent + "')",  # noqa: S608
            ),
            f"'x.svg' of card mine.001 \\(media file {absent}\\) is missing or damaged",
        ),
        "damaged": (  # its manifest checksum matches the bytes, not the name
            rebuilt(
                good, tmp_path / "damaged.meprofile", media={f"media/{svg}": b"<svg>other</svg>"}
            ),
            f"'media/g.svg' of card mine.001 \\(media file {svg}\\) is missing or damaged",
        ),
    }
    for label, (path, message) in bad.items():
        with pytest.raises(ProfileError, match=message):
            manager.import_profile(path)
        assert [p.name for p in manager.list()] == ["Jamie"], label
    assert not [p for p in manager.profiles_dir.iterdir() if p.name.startswith(".")]
    copy = manager.import_profile(rebuilt(good, tmp_path / "same.meprofile"))  # untouched: ok
    assert copy.name == "Evil"  # (the name rebuilt archives get)


def test_import_refuses_a_v2_database_without_the_media_table(
    manager: ProfileManager, tmp_path: Path
) -> None:
    source, _ = with_images(manager)
    good = tmp_path / "good.meprofile"
    manager.export(source, good)
    crafted = rebuilt(good, tmp_path / "crafted.meprofile", "DROP TABLE user_media")
    with pytest.raises(ProfileError, match="not usable"):
        manager.import_profile(crafted)


def test_export_of_a_profile_without_media(tmp_path: Path, clock) -> None:
    paths = ProfilePaths(tmp_path / "p")
    Storage.open(paths, create=True, clock=clock).close(backup=False)
    manifest = export_profile(
        paths.user_db, paths.media_dir, tmp_path / "e.meprofile", name="E", clock=clock
    )
    assert set(manifest["files"]) == {"user.db"}
