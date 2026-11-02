"""Errors raised by the storage layer. All derive from StorageError."""

from pathlib import Path


class StorageError(Exception):
    """Base class for storage failures."""


class UnsafeSQLiteError(StorageError):
    """The SQLite library has the WAL-reset corruption bug (DEV-7); nothing is opened."""


class SchemaTooNewError(StorageError):
    """The database was written by a newer app; it is never touched (forward-only)."""


class NotOurDatabaseError(StorageError):
    """The file is not a Toishi user.db or pack (wrong application_id)."""


class MigrationError(StorageError):
    """A migration step failed; it was rolled back and its backup is kept."""


class CorruptDatabaseError(StorageError):
    """PRAGMA quick_check failed. `newest_good_backup` is the restore candidate, if any."""

    def __init__(self, path: Path, problems: list[str], newest_good_backup: Path | None = None):
        self.path = path
        self.problems = problems
        self.newest_good_backup = newest_good_backup
        detail = "; ".join(problems[:5])
        super().__init__(f"{path} failed its integrity check: {detail}")


class MissingDatabaseError(StorageError):
    """user.db is missing for an existing profile (it is never silently recreated)."""


class ProfileInUseError(StorageError):
    """Another Database (in this process or another) holds the profile's lock."""


class UndoConflictError(StorageError):
    """The rows an attempt changed were changed again since; undo would not be exact."""


class NothingToUndoError(StorageError):
    """There is no attempt left to undo."""


class PackError(StorageError):
    """A pack file is invalid, unsealed, or its content hash does not match."""


class ProfileError(StorageError):
    """A profile operation was refused (unknown id, duplicate name, no confirmation)."""


class BackupError(StorageError):
    """A backup could not be written, read or restored."""


class MediaError(StorageError):
    """A media file name or image reference is unsafe, or a referenced file is missing."""
