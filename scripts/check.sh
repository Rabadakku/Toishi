#!/usr/bin/env bash
# One-command local check (no CI). Run it before every commit.
# usage: scripts/check.sh [fast|full|app]          (default: full)
#   fast  ruff, mypy, import-linter, pytest without a browser      (git pre-commit hook)
#   full  fast + web type-check and build + Playwright page tests
#   app   full + build the .app and run its --self-test           (macOS only)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

mode="${1:-full}"
case "$mode" in
  fast | full | app) ;;
  *) die "unknown mode '$mode'. usage: scripts/check.sh [fast|full|app]" ;;
esac
if [[ "$mode" == app ]]; then
  require_mac_arm64 "scripts/check.sh app"
fi
require_uv

step "Python env (uv sync --locked)"
uv sync --locked --quiet
require_good_python

step "ruff"
uv run --no-sync ruff format --check --quiet .
uv run --no-sync ruff check --quiet .

step "mypy"
uv run --no-sync mypy

step "import-linter"
contracts="$(uv run --no-sync lint-imports 2>&1)" || {
  printf '%s\n' "$contracts"
  die "import-linter contract broken (see above)"
}
printf '%s\n' "$contracts" | grep -E ' (KEPT|BROKEN)$'

step "pytest (no browser)"
if [[ "$mode" == fast ]]; then
  uv run --no-sync pytest -q -m "not ui and not slow"
else
  uv run --no-sync pytest -q -m "not ui"
fi

if [[ "$mode" == fast ]]; then
  printf '\nFAST CHECKS PASSED\n'
  exit 0
fi

step "web: install, type-check, build -> app/web_dist"
web_deps
npm --prefix web run --silent check
build_web

if is_mac; then
  browser="${TOISHI_BROWSER:-webkit}"
  step "Playwright $browser (downloaded once, then cached)"
  uv run --no-sync playwright install "$browser"
else
  browser="${TOISHI_BROWSER:-chromium}"
  note "not macOS: page tests use the preinstalled $browser; the WebKit run happens on the Mac."
fi

step "page tests (Playwright, $browser)"
TOISHI_REQUIRE_UI=1 TOISHI_BROWSER="$browser" uv run --no-sync pytest -q -m ui

if [[ "$mode" == full ]]; then
  is_mac || note "skipped macOS-only steps (.app build + self-test); run 'scripts/check.sh app' on the Mac."
  printf '\nFULL CHECKS PASSED\n'
  exit 0
fi

step "build the .app"
SKIP_WEB_BUILD=1 scripts/build.sh

step ".app self-test (real WKWebView + PyObjC + PyInstaller)"
dist/Toishi.app/Contents/MacOS/Toishi --self-test

printf '\nALL CHECKS PASSED\n'
