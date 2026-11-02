"""Schema v2 (ADR-0011): the v1 -> v2 migration of a student's progress, exact and safe.

Two frozen v1 databases go through it: user_v1.sql (the storage layer's own history) and
user_v1_cards.sql, written by the v1 code through card imports and the diagnosis hook, so
it holds all three v1 stop-gaps (tests/storage/v1_cards.py). Every row and value is
checked afterwards; a crash anywhere inside the step leaves either the untouched v1 or a
complete v2; and v1 code refuses a v2 database without touching it.
"""

import copy
import hashlib
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

import pytest

from core.cards import Source, apply_import, export_cards, plan_import
from core.engine.diagnosis import Diagnosis
from core.storage import Database, PackError, SchemaTooNewError, Storage, read_pack_info
from core.storage.backups import BackupManager
from core.storage.clock import FixedClock
from core.storage.connection import integrity_problems
from core.storage.profiles import ProfilePaths
from core.storage.schema import (
    MIGRATIONS,
    PACK_APP_ID,
    PACK_SCHEMA_VERSION,
    USER_SCHEMA_VERSION,
    schema_signature,
    split_v1_notes,
    user_version,
)
from tests.storage import v1_cards
from tests.storage.data import some
from tests.storage.v1_cards import PACK_V1, load_fixture

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
V1_HISTORY = FIXTURES / "user_v1.sql"
V1_CARDS = v1_cards.USER_V1_CARDS
V1_LAST_COMMIT = "16e73c8"  # the last commit with schema v1 (wrote the v1 fixtures)

Rows = dict[str, list[dict[str, Any]]]

# ---------------------------------------------------------------- what v2 must hold

DOUBLE_NOTES = "Watch the sign.\n\nA second paragraph of notes."
PARAMS = {  # each instance's parameter set: its seed is the sha256 of exactly this text
    "mine.alg.const.t01--e3b0c442": "",
    "mine.alg.double.t01--474f709d": "k = 2",
    "mine.alg.double.t01--57028f63": "k = 1",
    "mine.alg.double.t01--6142fb40": "k = 4",
    "mine.alg.double.t01--a66c78da": "k = 3",
    "mine.alg.mul.t01--0b275f42": "a = 2; b = 3",
    "mine.alg.mul.t01--2f3a978c": "a = 2; b = 1/2",
    "mine.alg.mul.t01--58b48d9f": "a = 3; b = 1/2",
    "mine.alg.mul.t01--95a57e89": "a = 3; b = 3",
}
NOTES = {  # notes_md after v2: the template's own notes, or none; other cards keep theirs
    **{cid: (DOUBLE_NOTES if ".double." in cid else None) for cid in PARAMS},
}
REASONS = {  # pending_check id -> reason (diagnostic checks have no asking attempt)
    1: "Check after a miss on Critical numbers: did Power rule at the step “Differentiate” break?",
    2: "Check: Factor polynomials is a prerequisite of Power rule, which was just missed",
    12: "The same kind of Product rule problem with the method named: was it the method, "
    "or choosing it?",
}


def rows_of(db: Path) -> Rows:
    """Every row of every table, as dicts, in rowid order."""
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        tables = [
            str(r[0])
            for r in conn.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            t: [dict(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")]  # noqa: S608
            for t in tables
        }
    finally:
        conn.close()


def version_of(db: Path) -> int:
    conn = sqlite3.connect(db)
    try:
        return user_version(conn)
    finally:
        conn.close()


def v1_sources(v1: Rows) -> dict[str, dict[str, Any]]:
    """The latest source of each template the v1 import log kept, read straight from it."""
    latest: dict[str, dict[str, Any]] = {}
    for record in sorted(v1["import_record"], key=lambda r: (r["at"], r["id"])):
        if record["kind"] != "cards":
            continue
        for info in json.loads(record["summary"])["files"].values():
            for tid, source in info["templates"].items():
                latest[tid] = {"id": tid, "source_md": source, "updated_at": record["at"]}
    return latest


def expected_v2(v1: Rows, *, cards: bool) -> Rows:
    """The v1 rows as v2 must hold them: every row and value kept, the stop-gaps moved."""
    out = copy.deepcopy(v1)
    for row in out["user_card"]:
        row["params"] = PARAMS.get(row["id"]) if cards else None
        if cards and row["id"] in NOTES:
            row["notes_md"] = NOTES[row["id"]]
    for row in out["pending_check"]:
        row["reason"] = REASONS.get(row["id"]) if cards else None
    out["user_template"] = sorted(v1_sources(v1).values(), key=lambda r: r["id"])
    out["user_media"] = []
    return out


def assert_complete_v2(db: Path, v1: Rows, *, cards: bool) -> None:
    assert version_of(db) == USER_SCHEMA_VERSION == 2
    assert integrity_problems(db, full=True) == []
    after = rows_of(db)
    after["user_template"].sort(key=lambda r: r["id"])
    assert after == expected_v2(v1, cards=cards)


def fresh_signature(tmp: Path) -> list[tuple[str, str]]:
    db = Database.open(tmp / "fresh" / "user.db", create=True)
    db.close()
    conn = sqlite3.connect(tmp / "fresh" / "user.db")
    try:
        return schema_signature(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------- the two frozen databases


def test_the_v1_cards_fixture_holds_every_stop_gap() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(V1_CARDS.read_text())
    notes = dict(conn.execute("SELECT id, notes_md FROM user_card WHERE template_id IS NOT NULL"))
    assert set(notes) == set(PARAMS)
    assert all(n.startswith("template parameters: ") for n in notes.values())
    in_extra = conn.execute(
        "SELECT count(*) FROM attempt WHERE extra LIKE '%\"reason\"%'"
    ).fetchone()[0]
    assert in_extra == 4  # three checks still pending or resolved, one undone
    conn.close()


def test_the_v1_history_fixture_migrates_every_row_and_value(tmp_path: Path) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_HISTORY, paths.user_db)
    v1 = rows_of(paths.user_db)
    clock = FixedClock(1_800_000_000_000)
    Storage.open(paths, clock=clock).close(backup=False)
    assert_complete_v2(paths.user_db, v1, cards=False)
    conn = sqlite3.connect(paths.user_db)
    try:
        assert schema_signature(conn) == fresh_signature(tmp_path)
    finally:
        conn.close()
    (backup,) = BackupManager(paths.user_db, paths.backups_dir, clock=clock).all()
    assert backup.reason == "pre-migration"  # BAK-2: the v1 state, kept
    assert rows_of(backup.path) == v1


def test_the_v1_cards_fixture_migrates_every_row_and_value(tmp_path: Path) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_CARDS, paths.user_db)
    v1 = rows_of(paths.user_db)
    clock = FixedClock(1_800_000_000_000)
    Storage.open(paths, clock=clock).close(backup=False)
    assert_complete_v2(paths.user_db, v1, cards=True)
    after = rows_of(paths.user_db)
    # Moved, and checked against more than the expectations above:
    for card in after["user_card"]:
        if card["template_id"] is not None:  # the seed came from exactly this text
            digest = hashlib.sha256(card["params"].encode()).hexdigest()
            assert card["seed"] == int(digest[:8], 16), card["id"]
    sources = {t["id"]: t for t in after["user_template"]}
    assert set(sources) == {"mine.alg.const.t01", "mine.alg.double.t01", "mine.alg.mul.t01"}
    assert "vars: k = int(2, 4)" in sources["mine.alg.double.t01"]["source_md"]  # the latest
    first, _, third = sorted(v1["import_record"], key=lambda r: r["id"])
    assert sources["mine.alg.mul.t01"]["updated_at"] == first["at"]  # retired: kept
    assert sources["mine.alg.double.t01"]["updated_at"] == third["at"]
    # The logs are append-only (DATA-5): the old text stays there as history.
    assert after["attempt"] == v1["attempt"]
    assert after["import_record"] == v1["import_record"]
    conn = sqlite3.connect(paths.user_db)
    try:
        assert schema_signature(conn) == fresh_signature(tmp_path)
    finally:
        conn.close()


def test_migrating_again_finds_nothing_to_do(tmp_path: Path) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_CARDS, paths.user_db)
    v1 = rows_of(paths.user_db)
    Storage.open(paths).close(backup=False)
    with Storage.open(paths) as storage:
        assert storage.backups.all()[0].reason == "pre-migration"
        assert [b.reason for b in storage.backups.all()].count("pre-migration") == 1
    assert_complete_v2(paths.user_db, v1, cards=True)


def test_split_v1_notes_moves_only_what_v1_wrote() -> None:
    p = "template parameters: "
    assert split_v1_notes("t", p + "k = 1") == ("k = 1", None)
    assert split_v1_notes("t", p) == ("", None)
    assert split_v1_notes("t", p + "k = 1\n\nnotes\n\nmore") == ("k = 1", "notes\n\nmore")
    for untouched in (p + "k = 1\nno blank line", p + "k = 1\n\n", "author notes", None):
        assert split_v1_notes("t", untouched) == (None, untouched)
    assert split_v1_notes(None, p + "k = 1") == (None, p + "k = 1")  # not an instance


# ---------------------------------------------------------------- the app on a migrated profile


def write_card_files(folder: Path) -> list[Source]:
    (folder / "media").mkdir(parents=True)
    (folder / "media" / "tri.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    double = v1_cards.DOUBLE.replace("LOW", "2").replace("HIGH", "4")
    (folder / "algebra.cards.md").write_text(v1_cards.card_file("Algebra", double))
    (folder / "geometry.cards.md").write_text(v1_cards.card_file("Geometry", v1_cards.GEOMETRY))
    return [Source.from_path(folder / n) for n in ("algebra.cards.md", "geometry.cards.md")]


@pytest.fixture
def migrated(tmp_path: Path) -> Any:
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_CARDS, paths.user_db)
    pack = tmp_path / "c.db"
    build_diagnosis_pack(pack)
    clock = FixedClock(1_788_000_000_000)
    storage = Storage.open(paths, pack_paths=[pack], clock=clock)
    yield storage
    storage.close(backup=False)


def build_diagnosis_pack(path: Path) -> None:
    from core.model import Course, PackInfo, Section, Unit
    from core.storage import build_pack
    from tests.engine.diagnosis.fixtures import SKILLS, cards

    sections = sorted({k.section_id for k in SKILLS if k.section_id})
    build_pack(
        path,
        PackInfo(id="c", title="Calc", version="1", built_at=1),
        [
            Course(id="c", title="Calc"),
            Unit(id="c.u", course_id="c", title="U"),
            *(Section(id=s, unit_id="c.u", title=s, ord=i) for i, s in enumerate(sections)),
            *SKILLS,
            *cards(),
        ],
    )


def test_reimporting_the_same_files_after_the_migration_changes_nothing(
    migrated: Storage, tmp_path: Path
) -> None:
    users = migrated.users
    for card in users.user_cards():
        assert card.params == PARAMS.get(card.id)
        if card.id in NOTES:
            assert card.notes_md == NOTES[card.id]
    plan = plan_import(users, write_card_files(tmp_path / "files"))
    assert plan.rejected == []
    assert plan.added == []
    assert plan.updated == []  # instances read back exactly as v2 builds them
    assert plan.sources_changed == []  # the moved sources are the files' sources
    assert plan.retire_instances == []
    assert plan.missing == []
    # v1 never stored images: the first import under v2 stores the one this card shows
    assert plan.media_changed == ["mine.geo.tri.001"]
    apply_import(users, plan)
    assert (
        users.media.read("mine.geo.tri.001", "media/tri.svg")
        == (tmp_path / "files" / "media" / "tri.svg").read_bytes()
    )
    again = plan_import(users, write_card_files(tmp_path / "again"))
    assert again.nothing_to_do


def test_export_reads_the_moved_template_sources(migrated: Storage) -> None:
    users = migrated.users
    files, warnings = export_cards(users.user_cards(), users.template_sources())
    assert warnings == []
    text = "\n".join(files.values())
    for tid in ("mine.alg.const.t01", "mine.alg.double.t01", "mine.alg.mul.t01"):
        assert f"## Card {tid}\n" in text
    # no parameter set leaks into an exported card's notes; the hand-written card keeps its
    assert text.count("template parameters") == 1
    assert "### Notes\ntemplate parameters: not a template" in text


def test_check_reasons_read_from_their_column_and_old_rows_still_work(migrated: Storage) -> None:
    users = migrated.users
    diagnosis = Diagnosis(migrated)
    checks = {c.id: c for c in users.pending_checks(None)}
    for check_id, reason in REASONS.items():
        assert checks[check_id].reason == reason
        assert diagnosis.reason(checks[check_id]) == reason
    diagnostic = [c for c in checks.values() if c.kind == "diagnostic"]
    assert diagnostic
    for check in diagnostic:  # nothing to move: composed from the weak spot, as in v1
        assert check.reason is None
        assert "misses on" in diagnosis.reason(check)


def test_the_last_v1_answer_can_still_be_undone(migrated: Storage) -> None:
    """Its snapshot of pending_check was taken without the reason column."""
    users = migrated.users
    last = some(users.last_attempt())
    assert {c.id for c in users.pending_checks() if c.attempt_id == last.id} == {12}
    users.undo_last_answer()
    assert 12 not in {c.id for c in users.pending_checks(None)}
    assert some(users.attempt(some(last.id))).voided_by is not None


# ---------------------------------------------------------------- crashes inside the step


def run_child(*args: str, timeout: float = 120) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "-m", "tests.storage.fault_child", *args],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.splitlines()


def v1_profile(root: Path) -> tuple[ProfilePaths, Rows]:
    paths = ProfilePaths(root)
    load_fixture(V1_CARDS, paths.user_db)
    return paths, rows_of(paths.user_db)


def count_steps(tmp_path: Path) -> int:
    paths, _ = v1_profile(tmp_path / "count")
    code, lines = run_child("v2-count", str(paths.root))
    assert code == 0, lines
    steps = int(lines[-1].split()[1])
    assert steps > 1000
    return steps


def assert_v1_or_complete_v2(paths: ProfilePaths, v1: Rows) -> str:
    """After a crash: the untouched v1 (still usable by v1 code) or a complete v2. Then the
    current app opens it, migrating if needed, and ends at a complete v2 either way."""
    db = paths.user_db
    assert integrity_problems(db, full=True) == []
    if version_of(db) == 1:
        assert rows_of(db) == v1
        old = Database.open(db, migrations=MIGRATIONS[:1], target_version=1)
        with old, old.reading() as conn:  # what the v1 app does on open
            assert conn.execute("SELECT count(*) FROM attempt").fetchone()[0] == 16
        found = "v1"
    else:
        assert_complete_v2(db, v1, cards=True)
        found = "v2"
    Storage.open(paths).close(backup=False)
    assert_complete_v2(db, v1, cards=True)
    backups = BackupManager(db, paths.backups_dir, clock=FixedClock(0)).all()
    assert backups
    assert all(b.reason == "pre-migration" for b in backups)
    assert all(rows_of(b.path) == v1 for b in backups)  # each one the v1 state
    return found


def crash_at(tmp_path: Path, name: str, steps: int) -> str:
    paths, v1 = v1_profile(tmp_path / name)
    code, lines = run_child("v2-die", str(paths.root), str(steps))
    assert code in (0, 9), lines
    return assert_v1_or_complete_v2(paths, v1)


def test_a_crash_inside_the_migration_leaves_v1_or_a_complete_v2(tmp_path: Path) -> None:
    total = count_steps(tmp_path)
    found = [crash_at(tmp_path, f"at-{n}", n) for n in (1, total // 3, 2 * total // 3, total)]
    assert found[:3] == ["v1", "v1", "v1"]  # rolled back, as if it never started
    assert found[3] == "v2"  # its last instruction runs after the commit
    assert crash_at(tmp_path, "never", total + 1) == "v2"


@pytest.mark.slow
def test_crashes_all_through_the_migration(tmp_path: Path) -> None:
    total = count_steps(tmp_path)
    seen = {crash_at(tmp_path, f"at-{n}", n) for n in range(1, total + 400, max(1, total // 40))}
    assert seen == {"v1", "v2"}


@pytest.mark.slow
def test_sigkill_at_random_moments_of_the_migration(tmp_path: Path) -> None:
    rng = random.Random(20261101)  # noqa: S311 -- reproducible timing, not crypto
    found = []
    for round_ in range(8):
        paths, v1 = v1_profile(tmp_path / f"kill-{round_}")
        proc = subprocess.Popen(
            [sys.executable, "-m", "tests.storage.fault_child", "v2-slow", str(paths.root)],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            stdout=subprocess.PIPE,
            text=True,
        )
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "migrating"
        time.sleep(rng.random() * 2.5)  # the slowed step takes about 1.7 s
        proc.kill()
        proc.wait()
        found.append(assert_v1_or_complete_v2(paths, v1))
    assert "v1" in found  # at least one kill landed inside the step


# ---------------------------------------------------------------- v1 code meets v2


def test_the_v1_code_path_refuses_a_v2_database_untouched(tmp_path: Path) -> None:
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_CARDS, paths.user_db)
    Storage.open(paths).close(backup=False)
    digest = hashlib.sha256(paths.user_db.read_bytes()).hexdigest()
    with pytest.raises(SchemaTooNewError, match="v2; this app understands up to v1"):
        Database.open(paths.user_db, migrations=MIGRATIONS[:1], target_version=1)
    assert hashlib.sha256(paths.user_db.read_bytes()).hexdigest() == digest


def v1_code(tmp_path: Path) -> Path:
    """core/ exactly as the last v1 commit had it, unpacked from git."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not installed")
    found = subprocess.run(
        [git, "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{V1_LAST_COMMIT}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    if found.returncode != 0:
        pytest.skip(f"commit {V1_LAST_COMMIT} is not in this clone")
    archive = tmp_path / "v1.tar"
    subprocess.run(
        [git, "-C", str(ROOT), "archive", "-o", str(archive), V1_LAST_COMMIT, "core"],
        check=True,
    )
    out = tmp_path / "v1-code"
    with tarfile.open(archive) as tar:
        tar.extractall(out, filter="data")
    return out


V1_SCRIPT = """
import hashlib, sys
from pathlib import Path
import core.storage.schema as schema
assert schema.USER_SCHEMA_VERSION == 1 and schema.PACK_SCHEMA_VERSION == 1, schema.__file__
from core.storage import PackError, ProfileManager, SchemaTooNewError, Storage, read_pack_info
from core.storage.profiles import ProfilePaths

profile, pack, meprofile, data_dir = map(Path, sys.argv[1:5])
db = profile / "user.db"
before = hashlib.sha256(db.read_bytes()).hexdigest()
try:
    Storage.open(ProfilePaths(profile))
except SchemaTooNewError as error:
    print("refused profile:", error)
assert hashlib.sha256(db.read_bytes()).hexdigest() == before, "the v2 file was changed"
try:
    read_pack_info(pack)
except PackError as error:
    print("refused pack:", error)
try:
    ProfileManager(data_dir).import_profile(meprofile)
except SchemaTooNewError as error:
    print("refused meprofile:", error)
"""


def test_the_released_v1_code_refuses_v2_files_untouched(tmp_path: Path) -> None:
    code = v1_code(tmp_path)
    paths = ProfilePaths(tmp_path / "p")
    load_fixture(V1_CARDS, paths.user_db)
    Storage.open(paths).close(backup=False)  # now v2
    pack = tmp_path / "pack.db"
    build_diagnosis_pack(pack)  # a pack at the current schema (v3)
    from core.storage.export import export_profile

    meprofile = tmp_path / "p.meprofile"
    export_profile(paths.user_db, paths.media_dir, meprofile, name="P", clock=FixedClock(0))
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            V1_SCRIPT,
            str(paths.root),
            str(pack),
            str(meprofile),
            str(tmp_path / "v1-data"),
        ],
        cwd=code,
        env={**os.environ, "PYTHONPATH": str(code)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert lines == [
        "refused profile: user.db is schema v2; this app understands up to v1. "
        "Update the app; the file was left untouched.",
        f"refused pack: {pack} is pack schema v{PACK_SCHEMA_VERSION}; this app reads up to v1",
        "refused meprofile: user.db is schema v2; this app understands up to v1. "
        "Update the app; the file was left untouched.",
    ]


def test_newer_packs_are_refused_by_older_readers_and_v1_packs_still_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Packs built today are v3 (pack-only tables for the student model): v1 and v2
    readers refuse them, and v1 packs still read."""
    new_pack = tmp_path / "v3.db"
    build_diagnosis_pack(new_pack)
    assert read_pack_info(new_pack).schema_version == PACK_SCHEMA_VERSION == 3
    from core.storage import schema

    for older in (1, 2):
        monkeypatch.setattr(schema, "PACK_SCHEMA_VERSION", older)  # what that reader allows
        with pytest.raises(PackError, match=f"reads up to v{older}"):
            read_pack_info(new_pack)
        monkeypatch.undo()
    v1_pack = load_fixture(PACK_V1, tmp_path / "v1.db", app_id=PACK_APP_ID)
    assert read_pack_info(v1_pack).schema_version == 1
