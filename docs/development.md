# Developing Toishi

Rules for working on the code are in [AGENTS.md](../AGENTS.md).

## Setup (macOS, Apple silicon)

Keep the repo out of iCloud/Dropbox folders (for example `~/Developer/toishi`).

```bash
# once: uv (Python manager) and Node.js 22.12+ (nodejs.org installer or Homebrew)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.14
uv sync                                   # exact versions from uv.lock
npm --prefix web ci
git config core.hooksPath scripts/git-hooks   # pre-commit runs the fast checks
```

The core (`core/`) and its tests also run on Linux; the app itself needs the Mac.

## Everyday commands

| Command | What it does |
|---|---|
| `scripts/check.sh fast` | ruff, mypy, import-linter, pytest |
| `scripts/check.sh` | fast + web build + Playwright page tests (WebKit on the Mac) |
| `scripts/check.sh app` | full + build the .app + run its `--self-test` |
| `scripts/check.sh gates` | the simulator's design gates alone (an hour or more) |
| `npm --prefix web run build && uv run python -m app` | run the app from source |
| `TOISHI_DEBUG=1 uv run python -m app` | same, with the Web Inspector (dev only) |
| `npm --prefix web run dev` then open `http://127.0.0.1:5173/?bridge=mock` | page in a browser, mock bridge |
| `scripts/build.sh` | `dist/Toishi.app` (onedir, arm64, ad-hoc signed) |
| `scripts/spike.sh` | M0 spike: pywebview vs PySide6 builds, sizes, launch times → `spike/spike-report.md` |
| `dist/Toishi.app/Contents/MacOS/Toishi --self-test` | smoke test of the real app |

Install the built app with `ditto dist/Toishi.app /Applications/Toishi.app`. It is built locally, so macOS does not quarantine it and Gatekeeper does not prompt. Never edit files inside the .app afterwards (that breaks its signature): rebuild instead.

App data lives in `~/Library/Application Support/com.toishi.app/` (ADR-0004).

## Letting Claude run the Mac checks

`scripts/mac-run.sh` sets up the tools, runs every check, builds the app and runs its self-test, logging to `logs/mac-run.log`. Install a small launchd helper once and Claude can start it by leaving a request file in `.runner/requests/` (see `scripts/mac-runner.sh`):

```bash
./scripts/install-runner.sh              # install (once)
./scripts/install-runner.sh status       # installed? last run's status
./scripts/install-runner.sh uninstall    # remove it
```

A request only names a mode (`setup`, `check`, `spike`, `gates` or `all`); nothing in it is run as a command. What runs is this repo's own scripts, the same ones you would run by hand. Progress is in `.runner/status`, output in `logs/mac-run.log`.

## Nightly backup

`scripts/backup.sh` writes a verified `git bundle --all` of this repo to `~/Library/Mobile Documents/com~apple~CloudDocs/Backups/toishi/` (iCloud Drive) and keeps the newest 30. Install the launchd agent (runs at 21:37, or on wake if asleep):

```bash
sed -e "s#__REPO__#$PWD#g" -e "s#__HOME__#$HOME#g" \
  packaging/launchd/com.toishi.backup.plist > ~/Library/LaunchAgents/com.toishi.backup.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.toishi.backup.plist
launchctl kickstart -k gui/$(id -u)/com.toishi.backup     # run once now
tail ~/Library/Logs/toishi-backup.log                      # check it worked
```

Remove it with `launchctl bootout gui/$(id -u)/com.toishi.backup`. If the log says "Operation not permitted", macOS blocked access to iCloud Drive: add `/bin/bash` under System Settings → Privacy & Security → Full Disk Access. Uncommitted work is not in the bundle (Time Machine covers the working tree). Restore drill: `git clone <bundle> /tmp/restore && git -C /tmp/restore fsck --full`.
