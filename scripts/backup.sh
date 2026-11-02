#!/usr/bin/env bash
# Full-history backup of this repo: `git bundle --all` into iCloud Drive with a dated
# name, verified, newest 30 kept. Run nightly by launchd (see README) or by hand.
# Env: TOISHI_BACKUP_DEST (destination folder), TOISHI_BACKUP_KEEP (default 30).
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd -P)"
source "$repo/scripts/lib.sh"

keep="${TOISHI_BACKUP_KEEP:-30}"
icloud="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
dest="${TOISHI_BACKUP_DEST:-$icloud/Backups/toishi}"

# The live repo must never sit in a synced folder: iCloud/Dropbox duplicate and drop
# files inside .git ("refs/heads/main 2") and corrupt it. Only the bundles go there.
case "$repo/" in
  "$HOME/Library/Mobile Documents/"* | "$HOME/Library/CloudStorage/"*)
    die "the live repo is inside a synced folder ($repo). Move it to ~/Developer/toishi."
    ;;
  "$HOME/Documents/"* | "$HOME/Desktop/"*)
    [[ "${TOISHI_ALLOW_SYNCED_REPO:-0}" == 1 ]] || die "the live repo is in ~/Documents or ~/Desktop, \
which iCloud Desktop & Documents may sync ($repo). Move it to ~/Developer/toishi \
(or set TOISHI_ALLOW_SYNCED_REPO=1 if that sync is off)."
    ;;
esac
if [[ -z "${TOISHI_BACKUP_DEST:-}" && ! -d "$icloud" ]]; then
  die "iCloud Drive folder not found ($icloud). Turn on iCloud Drive or set TOISHI_BACKUP_DEST."
fi
[[ "$keep" =~ ^[1-9][0-9]*$ ]] || die "TOISHI_BACKUP_KEEP must be a positive integer"

if [[ -n "$(git -C "$repo" status --porcelain)" ]]; then
  note "uncommitted changes are not in the bundle (commit them; Time Machine covers the working tree)."
fi

name="toishi-$(date +%Y-%m-%d).bundle"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/mastery-backup.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

# Write and verify off to the side, then move: iCloud only ever sees a complete file.
git -C "$repo" bundle create -q "$tmp/$name" --all
git -C "$repo" bundle verify -q "$tmp/$name" >/dev/null
mkdir -p "$dest"
mv -f "$tmp/$name" "$dest/$name"

# Keep the newest $keep bundles (dates in the names sort chronologically).
{ ls -1 "$dest" | grep -E '^toishi-[0-9]{4}-[0-9]{2}-[0-9]{2}\.bundle$' || true; } \
  | sort -r | tail -n +"$((keep + 1))" \
  | while IFS= read -r old; do rm -f -- "$dest/$old"; done

printf 'backup: %s/%s (%s); keeping the newest %s\n' \
  "$dest" "$name" "$(du -h "$dest/$name" | cut -f1)" "$keep"
