#!/usr/bin/env bash
# Runs scripts/mac-run.sh when a build agent leaves a request file, so the Mac checks can run
# without anyone typing in Terminal. launchd starts this whenever .runner/requests changes
# (install it with scripts/install-runner.sh).
#
# A request is a file .runner/requests/<id> whose first line is one of the modes mac-run.sh
# accepts: setup, check, spike or all (empty means all). Nothing in a request is ever run as a
# command; anything else is rejected. Progress goes to .runner/status, the run's output to
# logs/mac-run.log as usual.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=lib.sh
source scripts/lib.sh
is_mac || die "mac-runner.sh starts the Mac checks, so it only runs on macOS (this is $(uname -s))."

dir=.runner
mkdir -p "$dir/requests" logs

# One run at a time (mkdir is atomic). A lock left by a process that died is taken over.
if ! mkdir "$dir/lock" 2>/dev/null; then
  holder="$(cat "$dir/lock/pid" 2>/dev/null || true)"
  if [[ -n "$holder" ]] && kill -0 "$holder" 2>/dev/null; then
    exit 0 # the running loop picks up new requests before it exits
  fi
  rm -rf "$dir/lock"
  mkdir "$dir/lock" 2>/dev/null || exit 0
fi
echo "$$" >"$dir/lock/pid"
trap 'rm -rf "$dir/lock"' EXIT

stamp() { date '+%Y-%m-%d %H:%M:%S %z'; }

write_status() { # id mode state exit_code started finished
  {
    echo "id=$1"
    echo "mode=$2"
    echo "state=$3"
    echo "exit=$4"
    echo "started=$5"
    echo "finished=$6"
  } >"$dir/status.tmp"
  mv "$dir/status.tmp" "$dir/status"
}

while true; do
  next=""
  for f in "$dir"/requests/*; do
    if [[ -f "$f" ]]; then
      next="$f"
      break
    fi
  done
  if [[ -z "$next" ]]; then
    break
  fi

  id="$(basename "$next" | tr -cd 'A-Za-z0-9._-')"
  mode="$(head -n 1 "$next" | tr -d '[:space:]')"
  rm -f "$next"
  if [[ -z "$mode" ]]; then
    mode=all
  fi

  started="$(stamp)"
  case "$mode" in
    setup | check | spike | all) ;;
    *)
      write_status "$id" "rejected" "rejected" 2 "$started" "$started"
      continue
      ;;
  esac

  write_status "$id" "$mode" running "" "$started" ""
  rc=0
  ./scripts/mac-run.sh "$mode" >/dev/null 2>&1 || rc=$?
  write_status "$id" "$mode" done "$rc" "$started" "$(stamp)"
done
