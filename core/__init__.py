"""Toishi core: pure Python, no GUI imports (enforced by import-linter).

Everything here must run under plain pytest on Linux and macOS.
"""

__version__ = "0.1.0"

APP_NAME = "Toishi"
BUNDLE_ID = "com.toishi.app"


def version() -> str:
    """Return the app version (kept equal to pyproject.toml by a test)."""
    return __version__
