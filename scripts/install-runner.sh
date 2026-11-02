#!/usr/bin/env bash
# Installs, removes or shows the launchd agent that lets the build agents start the Mac checks
# (scripts/mac-run.sh) by leaving a request file in .runner/requests. See scripts/mac-runner.sh.
# usage: scripts/install-runner.sh [install|uninstall|status]   (default: install)
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=lib.sh
source scripts/lib.sh
is_mac || die "install-runner.sh sets up a launchd agent, so it only runs on macOS (this is $(uname -s))."

label=com.toishi.runner
legacy=com.masteryengine.runner # the helper's label before the app was renamed Toishi
repo="$(pwd -P)"
plist="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"

remove_legacy() {
  launchctl bootout "$domain/$legacy" 2>/dev/null || true
  rm -f "$HOME/Library/LaunchAgents/$legacy.plist"
}

case "${1:-install}" in
  install)
    case "$repo$HOME" in
      *[\|\&\<\>\"\']*) die "the repo path can't contain | & < > or quotes: $repo" ;;
    esac
    mkdir -p .runner/requests logs "$HOME/Library/LaunchAgents"
    sed -e "s|__REPO__|$repo|g" -e "s|__HOME__|$HOME|g" "packaging/launchd/$label.plist" >"$plist.tmp"
    plutil -lint "$plist.tmp" >/dev/null || die "the generated plist is invalid: $plist.tmp"
    mv "$plist.tmp" "$plist"
    remove_legacy
    launchctl bootout "$domain/$label" 2>/dev/null || true
    launchctl bootstrap "$domain" "$plist"
    echo "Installed. Claude can now start the Mac checks for $repo."
    echo "macOS may show a 'Background Items Added' notice for bash; that is this helper."
    echo "To remove it: ./scripts/install-runner.sh uninstall"
    ;;
  uninstall)
    remove_legacy
    launchctl bootout "$domain/$label" 2>/dev/null || true
    rm -f "$plist"
    echo "Removed. Claude can no longer start the Mac checks."
    ;;
  status)
    if launchctl print "$domain/$label" >/dev/null 2>&1; then
      echo "installed"
    elif launchctl print "$domain/$legacy" >/dev/null 2>&1; then
      echo "installed under the old name ($legacy); reinstall to rename it"
    else
      echo "not installed"
    fi
    if [[ -f .runner/status ]]; then
      cat .runner/status
    fi
    ;;
  *) die "usage: scripts/install-runner.sh [install|uninstall|status]" ;;
esac
