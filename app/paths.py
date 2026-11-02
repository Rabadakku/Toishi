"""Bundled, read-only resources. In the frozen .app these live under sys._MEIPASS/app/."""

from pathlib import Path

WEB_DIST_DIR = Path(__file__).parent / "web_dist"


def index_html() -> Path:
    """Entry page of the built web UI (web/ builds into app/web_dist)."""
    return WEB_DIST_DIR / "index.html"
