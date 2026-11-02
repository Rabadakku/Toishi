"""Storage: one open profile, wired together. What the app opens at startup.

storage = Storage.open(profile.paths, pack_paths=[...])
storage.users   # UserStore: progress, settings, attempts, undo, sessions ...
storage.packs   # PackStore: skills and cards from the packs and the student's own
storage.media   # UserMedia: the student's own images (media/ beside user.db)
storage.close() # takes the on-close backup (BAK-1)
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from core.model import PackInfo
from core.storage.backups import BackupInfo, BackupManager, BackupPolicy, cloud_sync_warning
from core.storage.clock import Clock, SystemClock
from core.storage.connection import Database
from core.storage.errors import BackupError, CorruptDatabaseError
from core.storage.export import export_attempts_csv, export_review_log_csv
from core.storage.media import UserMedia
from core.storage.pack_store import PackStore
from core.storage.packs import read_pack_info
from core.storage.profiles import ProfilePaths
from core.storage.user_store import UserStore


class Storage:
    def __init__(self, paths: ProfilePaths, db: Database, backups: BackupManager) -> None:
        self.paths = paths
        self.db = db
        self.backups = backups
        self.users = UserStore(db)
        self.packs = PackStore(db)

    @property
    def media(self) -> UserMedia:
        return self.users.media

    @classmethod
    def open(
        cls,
        paths: ProfilePaths,
        *,
        pack_paths: Sequence[Path] = (),
        clock: Clock | None = None,
        create: bool = False,
    ) -> Storage:
        """Open a profile: integrity check, backup before any migration, migrate, attach.

        A failed integrity check raises CorruptDatabaseError carrying the newest good
        backup, which the app offers to restore (BAK-4).
        """
        clock = clock or SystemClock()
        paths.ensure()
        backups = BackupManager(paths.user_db, paths.backups_dir, clock=clock)
        try:
            db = Database.open(
                paths.user_db,
                clock=clock,
                pack_paths=pack_paths,
                create=create,
                # No pruning yet: the student's retention settings are unread until open.
                before_migration=lambda _from, _to: backups.create("pre-migration", prune=False),
            )
        except CorruptDatabaseError as error:
            good = backups.newest_good()
            raise CorruptDatabaseError(
                error.path, error.problems, good.path if good else None
            ) from error
        storage = cls(paths, db, backups)
        values = storage.users.settings()
        backups.policy = BackupPolicy.from_settings(values)
        backups.tz = storage.users.timezone()
        backups.rollover_hour = storage.users.rollover_hour()
        return storage

    def warnings(self) -> list[str]:
        """Things the app should tell the student at startup (BAK-5)."""
        warning = cloud_sync_warning(self.paths.root)
        return [warning] if warning else []

    def note_use(self, active_ms: int) -> BackupInfo | None:
        """Report active use; takes the 30-minute backup when it is due."""
        return self.backups.add_use(active_ms)

    def backup_before(self, what: Literal["pre-import", "pre-pack-update"]) -> BackupInfo:
        """BAK-2: call before an import or a pack update."""
        return self.backups.create(what)

    def update_pack(self, new_path: Path) -> PackInfo:
        """Swap in a new version of a pack (or add a pack), after a backup (BAK-2, PACK-6)."""
        info = read_pack_info(new_path)
        self.backup_before("pre-pack-update")
        if any(p.info.id == info.id for p in self.db.packs):
            self.db.detach_pack(info.id)
        return self.db.attach_pack(new_path)

    def export_csv(self, folder: Path, *, include_voided: bool = False) -> dict[str, int]:
        """EXP-3: review_log.csv and attempts.csv into folder; returns row counts."""
        return {
            "review_log.csv": export_review_log_csv(
                self.db, folder / "review_log.csv", include_voided=include_voided
            ),
            "attempts.csv": export_attempts_csv(
                self.db, folder / "attempts.csv", include_voided=include_voided
            ),
        }

    def close(self, *, backup: bool = True) -> BackupInfo | None:
        if self.db.closed:
            return None
        taken = None
        try:
            if backup:
                try:
                    taken = self.backups.on_close()
                except BackupError:
                    taken = None  # never block closing; the data itself is committed
        finally:
            self.db.close()
        return taken

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
