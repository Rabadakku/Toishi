# ADR-0001: Stack, and the pywebview-vs-Qt shell spike

- Status: Accepted (shell choice provisional until `scripts/spike.sh` has run on the Mac)
- Date: 2026-11-01

## Context

One user, one Apple-silicon Mac, fully offline. The core (scheduling, answer checking) is
Python; the UI needs real math typesetting (KaTeX) and math input (MathLive), which exist
only for the web. So: a Python process plus a web view. Research notes:
`research_notes/Toishi gaps research/mac_stack_tooling.md` (Nov 2026).

## Decision

| Piece | Choice (pinned) |
|---|---|
| Python | CPython 3.14 (uv-managed, GIL build), `requires-python >=3.14,<3.15` |
| Env / lock | uv 0.13.6, `uv.lock` resolved for macOS arm64 + Linux only |
| Shell | pywebview 6.2.1 → system WKWebView via PyObjC 13.0, behind `app/shell.py` |
| Fallback shell | PySide6-Essentials 6.12.0 + PySide6-WebEngine 6.12.0.140 (`spike-qt` group only) |
| Core libs | fsrs 6.3.2, sympy 1.14.0, mpmath **1.3.0**, lark 1.3.1, platformdirs 4.14.2, zstandard 0.25.0 |
| Web | svelte 5.57.3, vite 8.3.5, @sveltejs/vite-plugin-svelte 7.3.1, typescript **6.0.3**, svelte-check 4.7.7, katex 0.19.1, mathlive 0.111.4 |
| Dev | ruff 0.17.3, mypy 2.4.1 (strict), pytest 9.2.0, import-linter 2.15, playwright **1.63.0** |
| Packaging | PyInstaller 6.22.3, onedir `.app`, arm64, ad-hoc signed, `LSMinimumSystemVersion` 14.0 |

Deviations from the research notes' "latest" versions, each forced by installation:
- **mpmath 1.3.0, not 1.4.1**: sympy 1.14.0 requires `mpmath<1.4`; uv cannot resolve 1.4.1.
- **typescript 6.0.3, not 7.x**: svelte-check 4.7.7 supports TypeScript `^5 || ^6` only.
- **playwright 1.63.0, not 1.64.1**: 1.64.1 needs Chromium build 1248; the Linux workspace
  has only build 1243 preinstalled and cannot download browsers. On the Mac,
  `playwright install webkit` fetches 1.63's WebKit (26.6). Bump once the workspace has 1.64.

Why pywebview over PySide6 + QtWebEngine: no bundled Chromium (the QtWebEngine wheel alone
is ~250 MB), native WebKit text input/IME like Safari, smaller signing surface; the app
needs nothing Qt-specific. Accepted risks: slow pywebview releases (last 2026-04), open
macOS 26 title-bar bug with `debug=True` (#1866: release builds force debug off), Cmd-key
interception (Cmd+Z may bypass MathLive's undo), no browser storage on Cocoa, and a JS
bridge that needs `'unsafe-eval'` unless patched (ADR-0002; patched in `app/csp_compat.py`).
Mitigations: exact pins, the one-file shell adapter, `--self-test` of the real `.app`, all
state in SQLite.

## The spike (M0)

`scripts/spike.sh` builds both shells around the same page, the same `app.api.Api` and the
same `core/`, then measures `.app` size and launch-to-self-test-pass time (5 runs; first is
coldest) and writes `spike/spike-report.md` with a manual checklist (Cmd+Z in the math
field, copy/paste, dead keys, alert sound, title bar, Cmd+Q, dark mode).

The Qt app (`spike/qt/qt_spike.py`) serves the page from its own 127.0.0.1 server, blocks
every other request with a `QWebEngineUrlRequestInterceptor`, and exposes the API as
`window.pywebview.api` over QWebChannel. Its self-test already passes headless on Linux
(Qt 6.12.0 / Chromium 140, `QT_QPA_PLATFORM=offscreen`).

Decision rule: keep pywebview unless a manual check fails with no workaround in
`app/shell.py`, or its self-test is flaky. Then switch to PySide6 with a new ADR (the Qt
path also allows a custom URL scheme instead of a loopback server).

## Consequences

- Only `app/shell.py` changes if the shell changes. core/ stays GUI-free (import-linter).
- PyInstaller's support for uv's python-build-standalone CPython on macOS is unverified;
  if the build misbehaves, install python.org's 3.14 and point uv at it.
- Playwright WebKit is close to, not the same as, WKWebView; the `.app` self-test covers
  the real engine.
