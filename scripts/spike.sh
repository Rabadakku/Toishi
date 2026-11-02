#!/usr/bin/env bash
# M0 shell spike (ADR-0001): build the pywebview app and the PySide6 + QtWebEngine app,
# measure .app size and launch-to-self-test time, write spike/spike-report.md. macOS only.
# usage: scripts/spike.sh [runs]     (default: 5 launches per app; the first is the coldest)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

runs="${1:-5}"
[[ "$runs" =~ ^[1-9][0-9]*$ ]] || die "runs must be a positive integer, got '$runs'"
require_mac_arm64 "scripts/spike.sh"
require_uv

step "pywebview app (release build)"
scripts/build.sh

step "Qt spike app (PySide6 6.12 + QtWebEngine)"
uv sync --locked --group spike-qt --quiet
uv run --no-sync pyinstaller spike/qt/qt_spike.spec --noconfirm --clean \
  --log-level WARN --distpath dist --workpath build/pyinstaller-qt
codesign --force --sign - dist/ToishiQtSpike.app
codesign --verify --deep --strict dist/ToishiQtSpike.app

step "measure ($runs launches each)"
mkdir -p build/spike
failed=0
uv run --no-sync python scripts/spike_measure.py measure --label "pywebview (WKWebView)" \
  --app dist/Toishi.app --runs "$runs" --out build/spike/pywebview.json || failed=1
uv run --no-sync python scripts/spike_measure.py measure --label "PySide6 + QtWebEngine" \
  --app dist/ToishiQtSpike.app --runs "$runs" --out build/spike/qt.json || failed=1
uv run --no-sync python scripts/spike_measure.py report \
  build/spike/pywebview.json build/spike/qt.json --out spike/spike-report.md

step "restore the dev env (drops PySide6)"
uv sync --locked --quiet

printf '\nwrote spike/spike-report.md - fill in its manual checklist, then update ADR-0001.\n'
[[ "$failed" == 0 ]] || die "a self-test failed; see the Failures section of spike/spike-report.md"
