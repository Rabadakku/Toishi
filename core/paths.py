"""Where the app keeps its data (ADR-0004)."""

import contextlib
import os
from pathlib import Path

import platformdirs

from core import BUNDLE_ID

DATA_DIR_ENV = "TOISHI_DATA_DIR"
# Earlier bundle ids of the app. Their data folder moves to the current one on first use.
LEGACY_BUNDLE_IDS = ("com.masteryengine.app",)


def app_data_dir() -> Path:
    """Per-user data directory: ~/Library/Application Support/<bundle id> on macOS.

    Uses the bundle id (not app name + version) so data never splits across versions.
    TOISHI_DATA_DIR overrides it for tests and throwaway runs.
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    path = Path(platformdirs.user_data_dir(BUNDLE_ID, appauthor=False, roaming=False))
    if not path.exists():
        _adopt_legacy(path)
    return path


def _adopt_legacy(path: Path) -> None:
    """Move an earlier name's data folder (same parent) to `path`, once. A rename within one
    folder is atomic, so a second process racing it finds the folder already moved."""
    for old in LEGACY_BUNDLE_IDS:
        legacy = path.with_name(old)
        if legacy.is_dir():
            # OSError: moved by another process, or the new folder appeared meanwhile.
            with contextlib.suppress(OSError):
                legacy.rename(path)
            return
