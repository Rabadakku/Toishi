# PyInstaller 6.22.3 spec: onedir .app, arm64, ad-hoc signed (ADR-0001).
# Build with scripts/build.sh (it builds the web UI first and re-verifies the signature).
import sys
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH).parent  # noqa: F821  (SPECPATH is injected by PyInstaller)
sys.path.insert(0, str(ROOT))
from core import APP_NAME, BUNDLE_ID, __version__  # noqa: E402

from app.packs import SHIPPED  # noqa: E402

WEB_DIST = ROOT / "app" / "web_dist"
if not (WEB_DIST / "index.html").is_file():
    raise SystemExit("app/web_dist is missing: run npm --prefix web ci && npm --prefix web run build")

# Read-only pack databases compiled by scripts/build.sh; app.packs finds them in packs/.
PACKS = ROOT / "build" / "packs"
missing = [p for p in SHIPPED if not (PACKS / f"{p}.db").is_file()]
if missing:
    raise SystemExit(f"build/packs is missing {missing}: run scripts/build.sh (it compiles them)")

# pywebview imports every platform backend by name; only Cocoa is used on macOS.
UNUSED_WEBVIEW_BACKENDS = [
    f"webview.platforms.{name}"
    for name in ("android", "cef", "edgechromium", "gtk", "mshtml", "qt", "win32", "winforms")
]

a = Analysis(  # noqa: F821
    [str(ROOT / "app" / "__main__.py")],
    pathex=[str(ROOT)],
    datas=[
        (str(WEB_DIST), "app/web_dist"),
        (str(ROOT / "core" / "storage" / "sql"), "core/storage/sql"),
        *[(str(PACKS / f"{p}.db"), "packs") for p in SHIPPED],
        *copy_metadata("fsrs"),
        *copy_metadata("platformdirs"),
        *copy_metadata("pywebview"),
    ],
    hiddenimports=["webview.platforms.cocoa"] if sys.platform == "darwin" else [],
    excludes=[
        *UNUSED_WEBVIEW_BACKENDS,
        "PySide6", "PyQt5", "PyQt6", "qtpy", "tkinter", "_tkinter",
        "pytest", "playwright", "mypy", "numpy", "IPython",
        "anki", "aqt",  # AGPL test oracle for the Anki importer, dev only (ADR-0015)
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Toishi",
    console=False,
    debug=False,
    strip=False,
    upx=False,
    argv_emulation=False,  # PyInstaller advises against it with GUI toolkits
    target_arch="arm64" if sys.platform == "darwin" else None,
    codesign_identity=None,  # None = ad-hoc signature
    entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Toishi")  # noqa: F821

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name="Toishi.app",
        icon=None,
        bundle_identifier=BUNDLE_ID,
        version=__version__,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": __version__,
            "LSMinimumSystemVersion": "14.0",
            "LSApplicationCategoryType": "public.app-category.education",
            "NSHighResolutionCapable": True,
        },
    )
