#!/usr/bin/env bash
# One command for the student's Mac: set up the tools, run every check, build the app,
# run the M0 spike. Everything is logged to logs/mac-run.log so the build agents can
# read the result from the linked folder without anyone copying output by hand.
# usage: scripts/mac-run.sh [setup|check|spike|all]   (default: all = setup + checks + app build)
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-all}"
mkdir -p logs
log="logs/mac-run.log"
: > "$log"
exec > >(tee -a "$log") 2>&1

say() { printf '\n=== %s ===\n' "$*"; }
status=0
run() {
  say "$*"
  local t0=$SECONDS rc=0
  "$@" || rc=$?
  printf -- '--> exit %s after %ss: %s\n' "$rc" "$((SECONDS - t0))" "$*"
  [[ $rc == 0 ]] || status=1
  return $rc
}

say "machine"
sw_vers 2>/dev/null || echo "not macOS"
uname -m
date

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is for the Mac. Exiting."
  exit 1
fi

# nvm installs node per shell; load it if present so non-interactive bash finds node.
if ! command -v node >/dev/null 2>&1 && [[ -s "$HOME/.nvm/nvm.sh" ]]; then
  # nvm isn't written for set -eu; load it with both off.
  set +eu
  # shellcheck disable=SC1091
  source "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 && { nvm use --lts >/dev/null 2>&1 || nvm use default >/dev/null 2>&1; }
  set -eu
fi
for brew_bin in /opt/homebrew/bin "$HOME/.homebrew/bin" /usr/local/bin; do
  if [[ -x "$brew_bin/brew" ]]; then PATH="$brew_bin:$PATH"; fi
done
export PATH="$HOME/.local/bin:$PATH"

setup() {
  if ! command -v uv >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      run brew install uv || return 1
    else
      echo "uv is missing and Homebrew wasn't found. Install uv: https://docs.astral.sh/uv/getting-started/installation/"
      return 1
    fi
  fi
  # The repo pins a minimum uv (pyproject [tool.uv] required-version). Upgrade an older one.
  local need have
  need="$(sed -n 's/^required-version *= *"[>=]*\([0-9.]*\)".*/\1/p' pyproject.toml | head -1)"
  have="$(uv --version | awk '{print $2}')"
  if [[ -n "$need" ]] && [[ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -1)" != "$need" ]]; then
    echo "uv $have is older than the required $need; upgrading."
    if uv --version | grep -q Homebrew && command -v brew >/dev/null 2>&1; then
      run brew upgrade uv || return 1
    else
      run uv self update || return 1
    fi
  fi
  if ! command -v node >/dev/null 2>&1; then
    echo "node is missing. Install Node 22 or later (nvm install --lts, or brew install node), then re-run."
    return 1
  fi
  say "tool versions"
  uv --version; node --version; npm --version; git --version
  run uv python install 3.14 || return 1
  run uv sync --locked || return 1
  run npm --prefix web ci || return 1
}

case "$mode" in
  setup) setup || status=1 ;;
  check) run ./scripts/check.sh app || true ;;
  spike) run ./scripts/spike.sh || true ;;
  all)
    # Set up, run every check, build the app and run its self-test. The M0 spike is done;
    # run it again with "spike" if ever needed.
    if setup; then
      run ./scripts/check.sh app || true
    else
      status=1
    fi
    ;;
  *) echo "usage: scripts/mac-run.sh [setup|check|spike|all]"; exit 2 ;;
esac

say "done (overall status $status)"
echo "Log saved to $log. Tell Claude it finished; Claude can read the log directly."
exit "$status"
