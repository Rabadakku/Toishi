"""BAK-1..6: consistent backups, retention, preview and restore, integrity, unsafe folders."""

import shutil
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import pytest

from core.model import Attempt, GradedAnswer
from core.storage import (
    BackupError,
    BackupInfo,
    BackupManager,
    BackupPolicy,
    CorruptDatabaseError,
    Database,
    ProfileInUseError,
    Storage,
    cloud_sync_warning,
    connection,
    select_keep,
)
from core.storage import backups as backups_module
from core.storage.backups import backup_name, parse_backup_name
from core.storage.clock import study_day, to_ms
from core.storage.profiles import ProfilePaths
from core.storage.schema import MIGRATIONS, USER_SCHEMA_VERSION, Migration
from tests.storage import data
from tests.storage.data import some

NY = ZoneInfo("America/New_York")


def answer(n: int) -> GradedAnswer:
    return GradedAnswer(attempt=Attempt(card_id=f"c{n}", verdict="correct"))


def test_backup_is_a_consistent_standalone_copy(storage: Storage, clock) -> None:
    data.populate(storage.users, clock, days=1)
    info = storage.backups.create("manual")
    assert info.reason == "manual"
    assert info.created_at == clock.now_ms()
    assert sorted(p.name for p in info.path.parent.iterdir()) == [info.path.name]  # no -wal
    conn = sqlite3.connect(info.path)
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    finally:
        conn.close()
    preview = storage.backups.preview(info)
    assert preview.ok
    assert preview.schema_version == USER_SCHEMA_VERSION
    assert preview.counts == storage.users.counts()


def test_backups_while_writing_are_consistent(storage: Storage) -> None:
    stop = threading.Event()

    def writer() -> None:
        n = 0
        while not stop.is_set():
            storage.users.record_answer(answer(n))
            n += 1

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        made = [storage.backups.create("manual") for _ in range(5)]
    finally:
        stop.set()
        thread.join()
    for info in made:
        assert storage.backups.preview(info).ok


def test_backups_taken_at_the_same_time_do_not_break_each_other(
    storage: Storage, monkeypatch
) -> None:
    # The 30-minute backup (a bridge thread) and a manual or closing one can overlap.
    real_fsync = connection.fsync_path
    reached, go = threading.Event(), threading.Event()

    def slow_fsync(path: Path) -> None:
        if path.name.endswith(".tmp") and not reached.is_set():
            reached.set()  # the first backup has written its .tmp copy and pauses here
            go.wait(5)
        real_fsync(path)

    monkeypatch.setattr(backups_module, "fsync_path", slow_fsync)
    results: dict[str, object] = {}

    def take(reason: Literal["periodic", "manual"]) -> None:
        try:
            results[reason] = storage.backups.create(reason)
        except Exception as error:  # reported by the assert below
            results[reason] = error

    first = threading.Thread(target=take, args=("periodic",))
    first.start()
    assert reached.wait(5)
    second = threading.Thread(target=take, args=("manual",))
    second.start()
    second.join(0.5)  # unserialized, it finishes now and its prune deletes the first .tmp
    go.set()
    first.join()
    second.join()
    made = [r for r in results.values() if isinstance(r, BackupInfo)]
    assert len(made) == 2, results
    assert all(storage.backups.preview(b).ok for b in made)


def test_names_round_trip_and_never_collide(storage: Storage, clock) -> None:
    first = storage.backups.create("periodic")
    second = storage.backups.create("periodic")  # same millisecond
    assert first.path != second.path
    assert second.serial == 1
    assert parse_backup_name(Path(backup_name(1_793_545_200_123, "pre-migration", 2))) == (
        BackupInfo(1_793_545_200_123, 2, Path("x"), "pre-migration")
    )
    assert parse_backup_name(Path("user.db")) is None
    assert storage.backups.all() == [second, first]


def fake(at: datetime, reason: str = "periodic") -> BackupInfo:
    ms = to_ms(at)
    return BackupInfo(ms, 0, Path(backup_name(ms, reason)), reason)


def test_retention_keeps_last_10_daily_7_weekly_4_monthly_6() -> None:
    start = datetime(2025, 1, 1, 12, tzinfo=UTC)
    regular = [fake(start + timedelta(hours=h)) for h in range(0, 24 * 400, 5)]
    extras = [fake(start + timedelta(days=d, minutes=1), "pre-import") for d in range(0, 400, 9)]
    everything = regular + extras
    keep = select_keep(everything, BackupPolicy(), NY)
    newest = sorted(everything, reverse=True)

    def day(b: BackupInfo):
        return study_day(b.created_at, NY)

    def newest_per(bucket, count: int) -> set[Path]:
        chosen: dict[object, Path] = {}
        for b in newest:
            chosen.setdefault(bucket(b), b.path)
        return set(list(chosen.values())[:count])

    expected = {b.path for b in sorted(regular, reverse=True)[:10]}
    expected |= {b.path for b in sorted(extras, reverse=True)[:10]}
    expected |= newest_per(day, 7)
    expected |= newest_per(lambda b: day(b).isocalendar()[:2], 4)
    expected |= newest_per(lambda b: (day(b).year, day(b).month), 6)
    assert keep == expected
    assert len(keep) <= 10 + 10 + 7 + 4 + 6
    kept_months = {(day(b).year, day(b).month) for b in newest if b.path in keep}
    assert len(kept_months) == 6
    assert select_keep([], BackupPolicy(), NY) == set()
    zero = BackupPolicy(keep_last=0, keep_daily=0, keep_weekly=0, keep_monthly=0, keep_extra=0)
    assert select_keep(regular, zero, NY) == {max(regular).path}  # the newest always stays


def test_retention_buckets_follow_study_days(tmp_path: Path) -> None:
    # two backups on the same calendar date but different study days (rollover 4 AM)
    late = fake(datetime(2026, 11, 2, 7, 30, tzinfo=UTC))  # 02:30 EST -> study day 11-01
    early = fake(datetime(2026, 11, 1, 14, tzinfo=UTC))  # 09:00 EST -> study day 11-01
    nextday = fake(datetime(2026, 11, 2, 10, tzinfo=UTC))  # 05:00 EST -> study day 11-02
    policy = BackupPolicy(keep_last=0, keep_daily=2, keep_weekly=0, keep_monthly=0)
    assert select_keep([early, late, nextday], policy, NY) == {late.path, nextday.path}


def test_prune_deletes_only_what_policy_drops(storage: Storage, clock) -> None:
    storage.backups.policy = BackupPolicy(keep_last=3, keep_daily=0, keep_weekly=0, keep_monthly=0)
    stray = storage.paths.backups_dir / "notes.txt"
    stray.write_text("mine")
    for _ in range(6):
        storage.backups.create("periodic")
        clock.advance(minutes=30)
    assert len(storage.backups.all()) == 3
    assert stray.read_text() == "mine"


def test_use_based_schedule_and_close(storage: Storage, clock) -> None:
    assert storage.note_use(29 * 60_000) is None
    made = storage.note_use(60_000)
    assert made is not None
    assert made.reason == "periodic"
    assert storage.note_use(60_000) is None
    closing = storage.close()
    assert closing is not None
    assert closing.reason == "close"


def test_restore_round_trip(paths: ProfilePaths, clock) -> None:
    storage = Storage.open(paths, clock=clock, create=True)
    for n in range(3):
        storage.users.record_answer(answer(n))
    saved = storage.backups.create("manual")
    clock.advance(minutes=5)
    for n in range(3, 8):
        storage.users.record_answer(answer(n))
    with pytest.raises(ProfileInUseError):
        storage.backups.restore(saved)  # never while open
    storage.close(backup=False)

    preview = storage.backups.preview(saved)
    assert preview.ok
    assert preview.counts["attempts"] == 3
    assert preview.backup.created_at == to_ms(data.START)
    kept = storage.backups.restore(saved)
    assert (kept / "user.db").exists()
    with Storage.open(paths, clock=clock) as restored:
        assert restored.users.counts()["attempts"] == 3
        pre = [b for b in restored.backups.all() if b.reason == "pre-restore"]
        assert len(pre) == 1
        assert restored.backups.preview(pre[0]).counts["attempts"] == 8


def test_restoring_an_old_backup_is_safe_from_pruning(paths: ProfilePaths, clock) -> None:
    storage = Storage.open(paths, clock=clock, create=True)
    storage.users.record_answer(answer(1))
    old = storage.backups.create("pre-import")
    clock.advance(minutes=1)
    storage.users.record_answer(answer(2))
    storage.close(backup=False)
    storage.backups.policy = BackupPolicy(
        keep_last=0, keep_daily=0, keep_weekly=0, keep_monthly=0, keep_extra=0
    )
    storage.backups.restore(old)  # the pre-restore backup would otherwise prune `old` first
    with Storage.open(paths, clock=clock) as restored:
        assert restored.users.counts()["attempts"] == 1


def twenty_backups_kept_by_a_bigger_policy(paths: ProfilePaths, clock) -> set[Path]:
    storage = Storage.open(paths, clock=clock, create=True)
    storage.users.set_settings({"backup.keep_last": 40})
    storage.close(backup=False)
    storage = Storage.open(paths, clock=clock)  # the student's policy applies from here
    for n in range(20):
        storage.users.record_answer(answer(n))
        storage.backups.create("periodic")
        clock.advance(minutes=30)
    storage.close(backup=False)
    kept = {b.path for b in storage.backups.all()}
    assert len(kept) == 20
    return kept


def test_restore_never_prunes_with_a_policy_it_was_not_given(paths: ProfilePaths, clock) -> None:
    kept = twenty_backups_kept_by_a_bigger_policy(paths, clock)
    # BAK-4: user.db failed its check, so the app restores through a manager that could
    # not read the student's backup settings: it must not prune with the defaults.
    fresh = BackupManager(paths.user_db, paths.backups_dir, clock=clock)
    fresh.restore(fresh.all()[0])
    assert kept <= {b.path for b in fresh.all()}


def test_pre_migration_backup_keeps_what_the_students_policy_keeps(
    paths: ProfilePaths, clock, monkeypatch
) -> None:
    kept = twenty_backups_kept_by_a_bigger_policy(paths, clock)
    real_open = Database.open

    def add_column(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE exam ADD COLUMN x INTEGER")

    newer = Migration(len(MIGRATIONS) + 1, "add a column", add_column)
    steps = (*MIGRATIONS, newer)

    def open_newer_app(path: Path, **kwargs: object) -> Database:
        return real_open(path, migrations=steps, target_version=newer.version, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Database, "open", open_newer_app)  # an app update with a migration
    Storage.open(paths, clock=clock).close(backup=False)
    monkeypatch.undo()
    after = BackupManager(paths.user_db, paths.backups_dir, clock=clock).all()
    assert kept <= {b.path for b in after}
    assert [b.reason for b in after].count("pre-migration") == 1


def test_a_second_launch_during_a_restore_leaves_it_alone(
    paths: ProfilePaths, clock, monkeypatch
) -> None:
    storage = Storage.open(paths, clock=clock, create=True)
    storage.users.record_answer(answer(1))
    saved = storage.backups.create("manual")
    storage.users.record_answer(answer(2))
    storage.close(backup=False)
    real = Path.replace
    launched: list[bool] = []

    def replace(self: Path, target: Path) -> Path:
        if self == paths.user_db and not launched:  # restore is about to swap the files
            launched.append(True)
            with pytest.raises(ProfileInUseError):  # the app is opened a second time
                Storage.open(paths, clock=clock)
        return real(self, target)

    monkeypatch.setattr(Path, "replace", replace)
    storage.backups.restore(saved)
    monkeypatch.undo()
    assert launched
    with Storage.open(paths, clock=clock) as restored:
        assert restored.users.counts()["attempts"] == 1


def test_an_interrupted_restore_never_meets_the_old_wal(paths: ProfilePaths, clock) -> None:
    storage = Storage.open(paths, clock=clock, create=True)
    for n in range(2):
        storage.users.record_answer(answer(n))
    saved = storage.backups.create("manual")
    for n in range(2, 40):
        storage.users.record_answer(answer(n))
    wal = paths.user_db.with_name("user.db-wal")
    old_wal = wal.read_bytes()  # what a crash of the app leaves beside user.db
    storage.close(backup=False)
    assert old_wal
    # restore() moves user.db aside, then user.db-wal; a crash between the two leaves:
    paths.user_db.unlink()
    wal.write_bytes(old_wal)
    shutil.copyfile(saved.path, paths.user_db.with_name("user.db.incoming"))
    with Storage.open(paths, clock=clock) as restored:
        assert restored.users.counts()["attempts"] == 2  # the backup, not old WAL frames
    assert [p.name for p in paths.root.glob("user.db-wal.*")] == ["user.db-wal.stale"]


def test_corrupt_database_points_at_newest_good_backup(paths: ProfilePaths, clock) -> None:
    storage = Storage.open(paths, clock=clock, create=True)
    storage.users.record_answer(answer(1))
    good = storage.backups.create("manual")
    clock.advance(minutes=1)
    storage.close(backup=False)
    # a bad newer backup and a smashed database
    bad = paths.backups_dir / backup_name(clock.now_ms(), "periodic")
    bad.write_bytes(b"\0" * 8192)
    with paths.user_db.open("r+b") as handle:
        handle.seek(4096)
        handle.write(b"\xff" * 8192)
    with pytest.raises(CorruptDatabaseError) as caught:
        Storage.open(paths, clock=clock)
    assert caught.value.newest_good_backup == good.path
    assert not storage.backups.preview(some(parse_backup_name(bad))).ok
    with pytest.raises(BackupError):
        storage.backups.restore(some(parse_backup_name(bad)))
    storage.backups.restore(good)
    with Storage.open(paths, clock=clock) as restored:
        assert restored.users.counts()["attempts"] == 1


def test_missing_database_is_never_silently_recreated(paths: ProfilePaths, clock) -> None:
    from core.storage import MissingDatabaseError

    with pytest.raises(MissingDatabaseError):
        Storage.open(paths, clock=clock)
    assert not paths.user_db.exists()


@pytest.mark.parametrize(
    ("where", "expected"),
    [
        ("Library/Mobile Documents/com~apple~CloudDocs/ME", "iCloud"),
        ("Library/CloudStorage/OneDrive-Personal/ME", "cloud storage"),
        ("Dropbox/apps/ME", "Dropbox"),
        ("OneDrive - School/ME", "OneDrive"),
        ("Library/Application Support/com.toishi.app", None),
    ],
)
def test_cloud_folders_are_flagged(tmp_path: Path, where: str, expected: str | None) -> None:
    warning = cloud_sync_warning(tmp_path / where, home=tmp_path, mounts=[])
    if expected is None:
        assert warning is None
    else:
        assert warning is not None
        assert expected in warning


def test_network_volumes_are_flagged(tmp_path: Path) -> None:
    mounts = [("/", "apfs"), ("/Volumes/share", "smbfs"), ("/Volumes/share/local", "apfs")]
    warning = cloud_sync_warning(Path("/Volumes/share/me"), home=tmp_path, mounts=mounts)
    assert warning is not None
    assert "network" in warning
    assert cloud_sync_warning(Path("/Volumes/share/local/me"), home=tmp_path, mounts=mounts) is None
    assert cloud_sync_warning(Path("/Users/me"), home=tmp_path, mounts=mounts) is None


def test_storage_reports_folder_warnings(storage: Storage) -> None:
    assert storage.warnings() == []  # pytest's tmp folder is local
