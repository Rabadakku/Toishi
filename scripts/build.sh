#!/usr/bin/env bash
# Build dist/Toishi.app: PyInstaller onedir, arm64, ad-hoc signed, with the shipped
# packs inside. macOS only.
# SKIP_WEB_BUILD=1 reuses an existing app/web_dist (check.sh just built it).
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

require_mac_arm64 "scripts/build.sh"
require_uv
uv sync --locked --quiet
require_good_python

if [[ "${SKIP_WEB_BUILD:-0}" != 1 ]]; then
  step "web UI -> app/web_dist"
  build_web
fi

# The shipped packs, compiled with the full content checks (keys self-checked, KaTeX render
# check through node) into read-only pack databases that the spec puts inside the .app.
step "shipped packs -> build/packs"
rm -rf build/packs
shipped="$(uv run --no-sync python -c 'from app.packs import SHIPPED; print(" ".join(SHIPPED))')"
for pack in $shipped; do
  uv run --no-sync python content-tools/mepack.py build "packs/$pack" --out build/packs \
    || die "pack $pack failed its checks (see above)"
done

step "PyInstaller (onedir .app, arm64)"
uv run --no-sync pyinstaller packaging/Toishi.spec --noconfirm --clean \
  --log-level WARN --distpath dist --workpath build/pyinstaller

app="dist/Toishi.app"
step "ad-hoc sign and verify"
codesign --force --sign - "$app"
codesign --verify --deep --strict "$app"

# DEV-7: record the SQLite the .app really bundles (read from the frozen app, which also
# refuses to start its storage when that SQLite lacks the WAL-reset fix).
step "build manifest -> dist/build-manifest.json"
"$app/Contents/MacOS/Toishi" --health \
  | uv run --no-sync python scripts/build_manifest.py --out dist/build-manifest.json \
  || die "the built app failed its health check, or its SQLite is unsafe (see above)"

printf '\nbuilt %s (%s)\n' "$app" "$(du -sh "$app" | cut -f1)"
