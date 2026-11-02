# Shared helpers for scripts/*.sh. Source it; don't run it.
# Must work with macOS's /bin/bash 3.2: no associative arrays, mapfile or ${var,,}.

step() { printf '\n==> %s\n' "$*"; }
note() { printf 'note: %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
is_mac() { [[ "$(uname -s)" == Darwin ]]; }

require_mac_arm64() { # $1 = what needs it
  is_mac || die "$1 builds or runs the macOS app, so it only runs on macOS (this is $(uname -s))."
  [[ "$(uname -m)" == arm64 ]] || die "$1 targets Apple silicon (arm64); this Mac is $(uname -m)."
}

require_uv() {
  command -v uv >/dev/null 2>&1 || die "uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
}

# The app must run on uv's standard (GIL) CPython 3.14, never /usr/bin/python3 (pywebview FAQ)
# and never a free-threaded build (pywebview #1739).
require_good_python() {
  local exe
  exe="$(uv run --no-sync python -c 'import sys; print(sys.executable)')"
  case "$exe" in
    /usr/bin/* | /System/*) die "uv is using the system Python ($exe). Run: uv python install 3.14" ;;
  esac
  uv run --no-sync python -c 'import sys; sys.exit(0 if sys._is_gil_enabled() else 1)' \
    || die "free-threaded Python is not supported (pywebview #1739). Run: uv python install 3.14"
}

# npm ci only when node_modules is missing or older than the lockfile.
web_deps() {
  command -v npm >/dev/null 2>&1 || die "npm not found. Install Node.js 22.12 or newer."
  if [[ ! -f web/node_modules/.package-lock.json || web/package-lock.json -nt web/node_modules/.package-lock.json ]]; then
    npm --prefix web ci --no-audit --no-fund --loglevel=error
  fi
}

build_web() {
  web_deps
  npm --prefix web run --silent build -- --logLevel warn
}
