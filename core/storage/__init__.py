"""Storage for Toishi (milestone M1): read-only packs + one user.db per profile.

Public entry points:

- Storage.open(paths)     one profile, wired: .users (UserStore), .packs (PackStore)
- ProfileManager          create, list, rename, choose, delete, export, import profiles
- PackWriter, build_pack  build and seal a pack; open_pack / read_pack_info to inspect
- BackupManager           backups, retention, preview, restore; cloud_sync_warning
- UserMedia               the student's own media (Storage.media, UserStore.media)
- Database                the connection layer (single writer, per-thread readers)
- clock                   UTC ms, FixedClock for tests, study_day with the 4 AM rollover
"""

from core.storage.backups import (
    BackupInfo,
    BackupManager,
    BackupPolicy,
    BackupPreview,
    cloud_sync_warning,
    select_keep,
)
from core.storage.clock import Clock, FixedClock, SystemClock, day_start_ms, study_day
from core.storage.connection import Database
from core.storage.errors import (
    BackupError,
    CorruptDatabaseError,
    MediaError,
    MigrationError,
    MissingDatabaseError,
    NothingToUndoError,
    NotOurDatabaseError,
    PackError,
    ProfileError,
    ProfileInUseError,
    SchemaTooNewError,
    StorageError,
    UndoConflictError,
    UnsafeSQLiteError,
)
from core.storage.export import export_attempts_csv, export_review_log_csv
from core.storage.media import UserMedia
from core.storage.pack_store import PackStore
from core.storage.packs import PackReader, PackWriter, build_pack, open_pack, read_pack_info
from core.storage.profiles import ProfileInfo, ProfileManager, ProfilePaths
from core.storage.schema import PACK_SCHEMA_VERSION, USER_SCHEMA_VERSION
from core.storage.store import Storage
from core.storage.user_store import UndoResult, UserStore

__all__ = [
    "PACK_SCHEMA_VERSION",
    "USER_SCHEMA_VERSION",
    "BackupError",
    "BackupInfo",
    "BackupManager",
    "BackupPolicy",
    "BackupPreview",
    "Clock",
    "CorruptDatabaseError",
    "Database",
    "FixedClock",
    "MediaError",
    "MigrationError",
    "MissingDatabaseError",
    "NotOurDatabaseError",
    "NothingToUndoError",
    "PackError",
    "PackReader",
    "PackStore",
    "PackWriter",
    "ProfileError",
    "ProfileInUseError",
    "ProfileInfo",
    "ProfileManager",
    "ProfilePaths",
    "SchemaTooNewError",
    "Storage",
    "StorageError",
    "SystemClock",
    "UndoConflictError",
    "UndoResult",
    "UnsafeSQLiteError",
    "UserMedia",
    "UserStore",
    "build_pack",
    "cloud_sync_warning",
    "day_start_ms",
    "export_attempts_csv",
    "export_review_log_csv",
    "open_pack",
    "read_pack_info",
    "select_keep",
    "study_day",
]
