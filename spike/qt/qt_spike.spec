# PyInstaller 6.22.3 spec for the M0 Qt spike (PySide6 6.12 + QtWebEngine). Built by scripts/spike.sh.
# Bundles the same core/ and web UI as the real app so the size comparison is fair.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH).parents[1]  # noqa: F821
WEB_DIST = ROOT / "app" / "web_dist"
if not (WEB_DIST / "index.html").is_file():
    raise SystemExit("app/web_dist is missing: run npm --prefix web run build")

a = Analysis(  # noqa: F821
    [str(ROOT / "spike" / "qt" / "qt_spike.py")],
    pathex=[str(ROOT)],
    datas=[(str(WEB_DIST), "app/web_dist"), *copy_metadata("fsrs"), *copy_metadata("platformdirs")],
    excludes=["webview", "PyQt5", "PyQt6", "tkinter", "_tkinter", "pytest", "playwright", "numpy"],
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ToishiQtSpike",
    console=False,
    argv_emulation=False,
    target_arch="arm64" if sys.platform == "darwin" else None,
    codesign_identity=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ToishiQtSpike")  # noqa: F821

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name="ToishiQtSpike.app",
        bundle_identifier="com.toishi.qtspike",
        info_plist={"LSMinimumSystemVersion": "14.0", "NSHighResolutionCapable": True},
    )
