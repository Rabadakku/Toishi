# Mac-only offline Python desktop app: build, package, test, back up (November 2026)

Scope: an Anki-style study app whose whole UI is a Svelte + TypeScript web UI (KaTeX, MathLive, a JS plotting library) in one web view, with a pure-Python core (SQLite, py-fsrs, SymPy + mpmath in a worker process). Target is macOS only (Apple Silicon MacBook Air), fully offline, free tools only, no GitHub or CI. Everything is built and tested on the developer's own Mac, with Linux sandbox runs where possible.

Versions and dates below come from PyPI or npm registry metadata fetched on 2026-11-01 unless noted.

---

## pywebview on macOS: what is it, and how well does it fit this app?

### Takeaway
pywebview 6.2.1 (2026-04-15, BSD-3-Clause) is a thin PyObjC wrapper around the system WKWebView. It has what this app needs: a promise-based JS-to-Python bridge, a built-in loopback static server, native app menus, file dialogs, multiple windows, and window events. It bundles no browser engine. The risks are a slow release cadence (no release since April 2026), an open macOS 26 title-bar bug, website storage that does not persist on Cocoa, and native Cmd-key interception that may bypass MathLive's own undo. These risks are manageable if all state lives in SQLite and the real app gets a smoke test.

### Cited Findings
**Versions, license, Python, dependencies**
- Latest release is 6.2.1 (2026-04-15). Earlier releases: 6.2 (2026-04-13), 6.1 (2025-10-21), 6.0 (2025-08-08), 5.4 (2025-01-27). License is BSD 3-Clause. PyPI `requires_python` is ">=3.8", but the classifiers stop at 3.13. — [PyPI pywebview](https://pypi.org/project/pywebview/)
- On master, `pyproject.toml` now says `requires-python = ">=3.10"`. The macOS dependencies are all `sys_platform=='darwin'`-marked: `pyobjc-core>=9.0`, `pyobjc-framework-Cocoa`, `-Quartz`, `-WebKit`, `-security`, `-UniformTypeIdentifiers` (all >=9.0). The cross-platform dependencies are `bottle`, `proxy_tools` and `typing_extensions`. — [pywebview pyproject.toml (master)](https://raw.githubusercontent.com/r0x0r/pywebview/master/pyproject.toml)
- PyObjC is required. The install docs say that for a standalone Python, the Cocoa, Quartz, WebKit and security framework packages plus `pyobjc-core` are enough. The docs give no minimum macOS. — [pywebview installation](https://pywebview.flowrl.com/guide/installation.html)
- pyobjc-core 13.0 was released 2026-10-30. It requires Python >=3.11 and ships cp311–cp315 universal2 wheels. The cp314/cp315 wheels are tagged macOS 10.15+. — [PyPI pyobjc-core](https://pypi.org/project/pyobjc-core/)

**How it embeds WKWebView**
- The Cocoa backend creates a `WKWebViewConfiguration` and a `WKWebView` subclass (`WebKitHost`). Debug mode sets `developerExtrasEnabled`, which enables the Safari Web Inspector. The JS bridge is registered with `config.userContentController().addScriptMessageHandler_name_(self.js_bridge, 'jsBridge')`, so bridge calls travel over WKScriptMessageHandler, not HTTP. No `WKURLSchemeHandler` (custom scheme) is used. At startup the backend sets `NSAppTransportSecurity = {'NSAllowsArbitraryLoads': YES}`. — [pywebview cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- Private mode does not use a non-persistent store. The backend uses `WKWebsiteDataStore.defaultDataStore()` and clears all website data types. The code comment says the non-persistent store "preserves cookies for some unknown reason". — [pywebview cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- `private_mode` defaults to True ("nothing persists between sessions"). `storage_path` defaults to `~/.pywebview`. — [pywebview API](https://pywebview.flowrl.com/api/)
- Issue #1714 "[Cocoa] storage_path not working": on macOS the directory is created but stays empty. No fix is recorded. — [pywebview #1714](https://github.com/r0x0r/pywebview/issues/1714)
- `window.native` is set to the NSWindow after creation (`self.pywebview_window.native = self.window`). The per-window `BrowserView` instances, which hold `.webview`, are kept in `BrowserView.instances`. — [pywebview window.py](https://github.com/r0x0r/pywebview/blob/master/webview/window.py); [cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- The FAQ says Cocoa requires the GUI loop on the main thread, and suggests `multiprocessing` when other logic needs it. — [pywebview FAQ](https://pywebview.flowrl.com/guide/faq)
- The FAQ says a pywebview window "will have issues with keyboard focus and Cmd+Tab" if the venv was created from the built-in macOS Python. It recommends a non-system (Homebrew) Python. — [pywebview FAQ](https://pywebview.flowrl.com/guide/faq)

**JS-to-Python bridge**
- Pass an object as `js_api=` to expose its methods as `pywebview.api.<method>`; names starting with `_` are hidden. `window.expose(func)` adds functions at runtime and wins on name clashes. Calls return Promises, and Python exceptions reject them as JS `Error`s. "Exposed functions are executed in separate threads and are not thread-safe." Use the `pywebviewready` event, not `onload`. `window.state` (added in 6.0) syncs top-level properties both ways. `evaluate_js` wraps code in `eval`, and `run_js` runs it raw, which matters under a CSP without `unsafe-eval`. — [pywebview interdomain guide](https://pywebview.flowrl.com/guide/interdomain.html)
- 6.0 changed the JS API to use callbacks instead of `setInterval`. 6.2 fixed a `window.expose` race condition and added static-method exposure. — [pywebview releases](https://github.com/r0x0r/pywebview/releases)

**Serving local files offline**
- A relative entry path starts the internal HTTP server automatically, and it cannot be disabled. `file://` "use is discouraged as it comes with a number of inherit limitations". Inline HTML works only with Base64-inlined assets. For a local web server, "protect your API calls against CSRF attacks". — [pywebview architecture](https://pywebview.flowrl.com/guide/architecture.html); [API](https://pywebview.flowrl.com/api/)
- The default server is a Bottle/wsgiref `BottleServer`. The port is random unless `http_port` is set, the address is `http://127.0.0.1:{port}/`, and each window gets its own server. `ssl=True` needs the `cryptography` package. — [pywebview http.py](https://github.com/r0x0r/pywebview/blob/master/webview/http.py); [API](https://pywebview.flowrl.com/api/)
- `settings['ALLOW_FILE_URLS']` maps to WKWebView's `allowFileAccessFromFileURLs`. — [cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- The `request_sent` event fires for every HTTP request, "except on macOS, where it fires only for the main document". — [pywebview API](https://pywebview.flowrl.com/api/)
- WKURLSchemeHandler, Apple's custom-scheme loader registered with `setURLSchemeHandler:forURLScheme:` on `WKWebViewConfiguration`, has been available since macOS 10.13. — [Apple WKURLSchemeHandler](https://developer.apple.com/documentation/webkit/wkurlschemehandler)

**Menus, dialogs, window state, shortcuts, multiple windows**
- Menus are built from `Menu(title, items)`, `MenuAction(title, function)` and `MenuSeparator()`. A title of `"__app__"` targets the macOS application menu (added in 6.1). 6.0 added per-window menus and `SHOW_DEFAULT_MENUS`. — [API](https://pywebview.flowrl.com/api/); [releases](https://github.com/r0x0r/pywebview/releases)
- The Cocoa backend builds a default Edit menu with Copy/Paste etc. — [cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- `create_file_dialog(dialog_type=FileDialog.OPEN, directory, allow_multiple, save_filename, file_types)` returns a tuple of paths or None. 6.0 replaced the old constants with the `FileDialog` enum. 6.2 maps `accept` MIME types to UTIs and adds a "New Folder" button to folder dialogs (6.1). — [API](https://pywebview.flowrl.com/api/); [releases](https://github.com/r0x0r/pywebview/releases)
- `create_window` takes `width`/`height` (default 800x600), `x`/`y`, `min_size`, `resizable`, `fullscreen`, `hidden`, `focus`, `on_top`, `background_color`, `text_select` (default False), `zoomable` (default False), `draggable`, and `vibrancy` (macOS). The events are `before_load`, `loaded`, `closing` (return False to cancel), `closed`, `resized(width, height)`, `moved`, and `request_sent`. Most handlers run in separate threads. — [API](https://pywebview.flowrl.com/api/)
- In `WebKitHost.keyDown_`, Cmd+X/C (only with a native selection), Cmd+V, Cmd+A, Cmd+Z (native `undoManager().undo()`), Cmd+Q (`app.stop_`) and Cmd+W are handled natively and `return` without calling `super`. Other keys pass through to the page. — [cocoa.py](https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py)
- 6.2 switched to one shared app delegate (instead of one per window), fixed a use-after-free crash on macOS ARM64, fixed crashes after a window closes, and released retained instances to fix memory leaks on macOS Tahoe. — [pywebview releases](https://github.com/r0x0r/pywebview/releases)

**Known macOS issues (as of 2026-11-01)**
- #1866 (open, last updated 2026-10-23): on pywebview 6.2.1 under macOS 26.5.2, a normal (non-frameless) window's title overlaps the traffic-light buttons and the buttons are unclickable. The reporter traced it to `debug=True`. There is no maintainer reply. — [pywebview #1866](https://github.com/r0x0r/pywebview/issues/1866)
- #1722 (closed 2026-02-04): keypresses played the macOS alert sound because the webview consumed key events without passing them on. A fix was pushed to master, but the thread names no release. — [pywebview #1722](https://github.com/r0x0r/pywebview/issues/1722)
- Other closed macOS issues by title: #1796 "Cocoa SIGINT handler uses shutdown path that doesn't allow Python's atexit to run" (closed 2026-07-02), #1739 "pywebview error in no-GIL mode" (closed 2026-06-05), #1754 "Getting two titles in pywebview on macOS 15.7.2" (closed 2026-01-10). — [GitHub issue search, r0x0r/pywebview](https://github.com/r0x0r/pywebview/issues)

**Packaging**
- pywebview's freezing guide says "Use py2app" for macOS and points to a reference `py2app_setup.py`. It mentions PyInstaller only for Windows/Linux and gives no bundle sizes. — [pywebview freezing](https://pywebview.flowrl.com/guide/freezing.html)
- 6.1 fixed a Cocoa "`__file__` attribute error after packaging". — [pywebview releases](https://github.com/r0x0r/pywebview/releases)
- py2app 0.28.10 was released 2026-02-13 and requires Python >=3.10. — [PyPI py2app](https://pypi.org/project/py2app/)
- The FAQ says large executables come from unneeded dependencies and suggests `--exclude-module`. — [pywebview FAQ](https://pywebview.flowrl.com/guide/faq)

### Inferences
- **Fit:** the app only needs one window, a bridge, static assets, menus, and an open/save dialog for importing Anki decks and question banks. pywebview covers all of these. The bridge goes through WKScriptMessageHandler, not HTTP, so the loopback server only serves static files and no API is reachable from other local processes.
- **Persistence:** keep all state in Python/SQLite, including UI preferences and window geometry. Never rely on localStorage or IndexedDB: Cocoa private mode wipes website data, `storage_path` is a no-op on Cocoa (#1714), and the random port changes the page origin on every launch unless `http_port` is fixed.
- **Threading:** bridge calls arrive on arbitrary threads. Route every DB write through one owner thread (a queue) or open a connection per call. Never share one `sqlite3.Connection` across threads.
- **Cmd-key interception (needs testing):** Cmd+Z goes to the native undo manager without the page seeing the keydown. MathLive's own undo stack may therefore not run on Cmd+Z inside a math field. Cmd+A and Cmd+V are also handled natively. Native `copy:`/`paste:` should still fire DOM clipboard events, but that is unverified. Test early. If it breaks, the fix is a small subclass or monkeypatch of `WebKitHost.keyDown_` that lets Cmd+Z/Shift+Cmd+Z through to the page.
- **Shutdown:** Cmd+Q calls `NSApp.stop_`, and #1796 shows that atexit may not run on some paths. Commit each review transaction immediately rather than flushing on exit, and handle `closing`/`closed` events for cleanup.
- **Offline enforcement:** ATS is turned off (`NSAllowsArbitraryLoads`) and `request_sent` only sees the main document. Enforce offline with a strict CSP `<meta>` tag in `index.html`: `default-src 'self'; connect-src 'self'; img-src 'self' data: blob:; font-src 'self' data:; style-src 'self' 'unsafe-inline'`. Optionally add a WKContentRuleList, a native WebKit content blocker installed through PyObjC on the `WKWebView` reached via `BrowserView.instances`. The WKContentRuleList API was not verified in this session.
- **Debug mode:** do not ship with `debug=True`. It enables the inspector and, on macOS 26, triggers #1866. Use an environment variable such as `APP_DEBUG=1` for development runs only.
- **Maintenance risk:** six and a half months without a release, with an open macOS 26 bug, makes pywebview the riskiest piece of the stack. Pin the exact version and keep pywebview behind a thin `shell/` adapter (one module) so a later swap to PySide6, or a vendored patch, stays contained.
- Use uv-managed Python or python.org Python, never `/usr/bin/python3`, to avoid the focus and Cmd+Tab problem in the FAQ. Use the standard GIL build, not free-threaded, because of #1739.

### Gaps
- No minimum macOS version is documented for pywebview. The real floor is set by the PyObjC wheels and by the APIs the code calls. Given the pywebview 6.2 Tahoe and ARM64 fixes and the #1754 report on macOS 15.7.2, macOS 14–26 is presumably fine, but this was not verified.
- No measured bundle size for a PyInstaller or py2app pywebview app on macOS was found. Measure with `du -sh dist/<App>.app`.
- Not verified whether pyinstaller-hooks-contrib ships a `webview` hook for 6.x, or whether PyInstaller needs `--collect-submodules webview` / `--collect-data webview`, because pywebview injects JS files from its package.
- Not verified whether the #1722 alert-sound fix shipped in 6.2 (released after the issue closed) or is still master-only.
- No reports found specifically about IME composition or clipboard bugs with pywebview on macOS 14–26.

---

## PySide6 + QtWebEngine on macOS: current state, and an honest comparison with pywebview

### Takeaway
PySide6 6.12.0 (2026-10-08) ships macOS 14+ universal2 abi3 wheels for Python 3.10–3.15. QtWebEngine comes in a separate ~250 MB wheel. Qt gives the most control: a fixed Chromium engine, subresource request interception, QWebChannel, and pytest-qt. In exchange it costs a far larger bundle, multi-process Chromium, and more packaging and signing surface. For a one-user, one-Mac app, pywebview's smaller footprint and native WebKit win. Qt remains the fallback if WKWebView or pywebview bugs block progress.

### Cited Findings
- PySide6 6.12.0 was released 2026-10-08 with `Requires-Python <3.16,>=3.10` and the wheel `pyside6-6.12.0-cp310-abi3-macosx_14_0_universal2.whl`. 6.11.3 followed on 2026-10-26, so the 6.11 line is still getting patches. License is LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only. — [PyPI PySide6](https://pypi.org/project/PySide6/)
- PySide6-Addons 6.12.0's macOS wheel is 90.5 MB (macosx_14_0_universal2). QtWebEngine is not in Addons; it comes from the separate `PySide6_WebEngine` package via `PySide6-Addons[webengine]`. — [PyPI PySide6-Addons](https://pypi.org/project/PySide6-Addons/)
- PySide6-WebEngine 6.12.0.140 (2026-10-08) has the wheel `pyside6_webengine-6.12.0.140-cp310-abi3-macosx_14_0_universal2.whl` at 249.8 MB. — [PyPI PySide6-WebEngine](https://pypi.org/project/PySide6-WebEngine/)
- QWebEngineUrlRequestInterceptor allows "intercepting, blocking, and modifying URL requests". You install it with `QWebEngineProfile::setUrlRequestInterceptor()`. "This method will be stalling the URL request until handled", and profile calls on the main thread block until it finishes. — [Qt WebEngine docs: QWebEngineUrlRequestInterceptor](https://doc-snapshots.qt.io/qtwebengine/qwebengineurlrequestinterceptor.html)
- A minimal PyQt6 PyInstaller .app on macOS is about 50–120 MB. QtWebEngine is called "particularly large" because it bundles Chromium. There is no measured QtWebEngine app size (article updated 2026-04-08). — [Python GUIs: packaged installer sizes](https://www.pythonguis.com/faq/packaged-installer-file-sizes/)
- By default PyInstaller "ad-hoc (re)signs all collected binaries and the generated executable itself". With a real identity it passes `--options=runtime` (hardened runtime), which "requires the codesign identity to be a valid Apple-issued code signing certificate". Self-signed certificates make shared libraries fail Library Validation. When targeting one architecture, fat binaries are thinned to that slice. — [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html)
- pytest-qt 4.5.0 was released 2025-07-01 (Python >=3.9). — [PyPI pytest-qt](https://pypi.org/project/pytest-qt/)
- PyInstaller recommends against argv emulation with UI toolkits. Qt receives open-file events as `QFileOpenEvent`. — [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html)

### Inferences
| Dimension | pywebview 6.2.1 (WKWebView) | PySide6 6.12 + QtWebEngine |
|---|---|---|
| Download / bundle size | No engine bundled; size is Python + PyObjC + SymPy (not measured) | QtWebEngine wheel alone 249.8 MB universal2; PyInstaller thins to arm64, but expect a few hundred MB app (not measured) |
| macOS floor | Set by PyObjC/WebKit; works on 14+ in practice | 14.0 (wheel tag) |
| Engine version | Follows the OS's Safari/WebKit (Safari 26 also ships for macOS 14/15), so it changes under you with OS/Safari updates | Pinned Chromium, so behaviour is deterministic until you upgrade PySide6 |
| Offline enforcement | CSP + optional WKContentRuleList; `request_sent` main-document only on macOS | `QWebEngineUrlRequestInterceptor` sees and can block every subresource |
| Bridge | `js_api`/`expose`, Promises, calls on worker threads | QWebChannel (`qwebchannel.js`), signals/slots, Qt threading model |
| Native feel | Native WebKit text input, IME, spellcheck, scrolling | Chromium inside a Qt window; good, but not native WebKit |
| Startup | One process plus WebKit's own helper processes | Chromium multi-process start; heavier (not measured) |
| Testing | No official driver for the real Cocoa window; test the UI with Playwright WebKit plus a smoke test | pytest-qt for the shell; Playwright Chromium for the UI |
| Maintenance risk | Small project; last release 2026-04; open macOS 26 bug | Qt Company backed; frequent releases (6.12.0, 6.11.3 in Oct 2026) |
| Signing/packaging | Few binaries; ad-hoc signing simple | Huge framework tree (QtWebEngineCore + helper app); more codesign surface |
- Recommendation for this app: pywebview, with a shell adapter so PySide6 stays a fallback. Qt's main advantages, a deterministic engine and request interception, matter less for one user on one Mac whose own data never leaves the machine.
- If Qt is chosen later, prefer the patched 6.12.x over 6.12.0, since 6.11.3 shipped after 6.12.0, which suggests early patch churn. Install only `PySide6-Essentials` plus `PySide6-WebEngine` rather than all of Addons.

### Gaps
- No measured macOS app size or cold-start time was found for PySide6 + QtWebEngine 6.12 built with PyInstaller 6.22.
- The Chromium version inside Qt WebEngine 6.12 was not checked.
- No source was found on QtWebEngine helper-process signing problems with PyInstaller 6.22 ad-hoc builds on macOS 26.

---

## Other Mac-only options: Tauri 2 + Python sidecar, Briefcase/Toga, native Swift + embedded Python

### Takeaway
None of these beats pywebview for this app. Tauri 2 uses the same WKWebView but adds a Rust toolchain and a separately frozen Python sidecar process. Briefcase/Toga is credible and actively released, but it is a different packaging and widget model, and the UI would still be a web view. Native Swift with embedded CPython is the most native and most work.

### Cited Findings
- Tauri CLI `@tauri-apps/cli` 2.12.4 was released 2026-10-21. — [npm @tauri-apps/cli](https://www.npmjs.com/package/@tauri-apps/cli)
- Tauri 2 sidecars are external binaries listed in `bundle.externalBin`. Each needs a `-$TARGET_TRIPLE` suffixed copy and is spawned through the shell plugin, which needs `shell:allow-execute`/`allow-spawn` with `"sidecar": true`. The docs name "Python CLI applications or API servers bundled using `pyinstaller`" as a common use case. — [Tauri v2 sidecar docs](https://v2.tauri.app/develop/sidecar/)
- Briefcase 0.4.7 was released 2026-10-27 (Python >=3.11, BSD-3-Clause). — [PyPI briefcase](https://pypi.org/project/briefcase/)
- Toga 0.5.7 was released 2026-10-01 (Python >=3.11). — [PyPI toga](https://pypi.org/project/toga/)

### Inferences
- **Tauri 2 + Python sidecar:** the web view would be WKWebView, so there is no engine advantage over pywebview. You add Rust/Cargo, a Rust-to-Python IPC protocol over stdin/stdout or a localhost socket, two packaging systems (Tauri bundler plus PyInstaller for the sidecar), and target-triple naming. It makes sense only if the developer wants Rust or Tauri's plugin ecosystem. For a Python-first solo project it adds complexity without solving a problem.
- **Briefcase/Toga:** Briefcase produces a proper macOS .app from a pyproject. Toga has a WebView widget (assumed to be WKWebView on macOS, not verified here). Choosing it means swapping PyInstaller for Briefcase's packaging model and learning Toga's app lifecycle. It is a reasonable plan B if PyInstaller freezing of pywebview causes trouble, but the JS bridge story is weaker and less documented than pywebview's.
- **Native Swift (SwiftUI + WKWebView) with embedded Python:** you get full control of WKWebView, including WKURLSchemeHandler for an `app://` scheme with no loopback server, content rule lists, and real menus and shortcuts. But you must embed and sign a CPython framework (for example BeeWare's Python-Apple-support, not researched here), bridge Swift to Python, and maintain Xcode projects. Free signing works with a Personal Team. This is the best long-term "native" answer, but too much work for a solo developer who wants the core in Python, so it is not recommended now.

### Gaps
- Not verified: Toga WebView's JS-to-Python messaging API, and whether Briefcase can include a SymPy worker subprocess cleanly.
- Not researched: Python-Apple-support or other embedded-CPython options for a Swift host.

---

## MathLive and KaTeX on WKWebView/Safari (macOS 14–26); offline-loading gotchas

### Takeaway
Both libraries support Safari and can be fully self-hosted from npm. The offline pitfalls are fonts and assets: MathLive needs its `fonts/` and `sounds/` reachable, or `mathlive/fonts.css` imported, and KaTeX's `fonts/` must sit next to its CSS. Use MathLive 0.111.x. 0.111.0 fixed Safari losing the last edit when a focused math field is removed from the DOM, which is exactly what happens when a review card advances. Serve from an http origin, not `file://`, because MathLive 0.111.2 tightened origin validation.

### Cited Findings
- MathLive's latest npm release is 0.111.4 (2026-10-31). — [npm mathlive](https://www.npmjs.com/package/mathlive)
- MathLive changelog, 0.111.0 (2026-09-30): "When a mathfield is removed from the DOM while it has the focus, the `change`... `blur` and `focusout` events are now dispatched in all browsers. Previously, they were dispatched only in Chromium, so an application that saved the value in a `change` or `blur` listener lost the last edit in Firefox and Safari." It also fixed #2973, a `TypeError` in Firefox and Safari when a mathfield is focused after another focused one was removed. — [MathLive CHANGELOG](https://github.com/arnog/mathlive/blob/master/CHANGELOG.md)
- MathLive changelog, 0.111.2 (2026-10-31): virtual keyboard, proxy and mathfield messages now default to same-origin validation, and "Same-origin validation no longer equates unrelated opaque (`"null"`) origins." — [MathLive CHANGELOG](https://github.com/arnog/mathlive/blob/master/CHANGELOG.md)
- Older changelog entries fix Safari-specific rendering issues, such as the Insert Matrix submenu and #2152 (fill-in-the-blank prompts containing fractions), so Safari is a tested target. — [MathLive CHANGELOG](https://github.com/arnog/mathlive/blob/master/CHANGELOG.md)
- With an npm install, "Make sure the contents of the `/fonts/` and `/sounds/` folder are copied to your build output directory." Otherwise set `MathfieldElement.fontsDirectory` / `soundsDirectory`. If a bundler hashes asset names, import `mathlive/fonts.css`, and MathLive "will not attempt to dynamically load the fonts". By default MathLive dynamically inserts stylesheets. The page states no minimum Safari version and nothing about CSP. — [MathLive integration guide](https://mathlive.io/mathfield/guides/integration/)
- MathLive issue #2244 is an iOS virtual-keyboard double-tap issue, not relevant to macOS. — [mathlive #2244](https://github.com/arnog/mathlive/issues/2244)
- KaTeX's latest npm release is 0.19.1 (2026-10-23). — [npm katex](https://www.npmjs.com/package/katex)
- KaTeX "supports all major browsers, including ... Safari". `fonts/` (WOFF2/WOFF/TTF) must stay alongside the CSS because `katex.css` uses relative font URLs. The default is `font-display: block`, and `katex-swap.css` gives swap. It can be self-hosted from npm. — [KaTeX browser docs](https://katex.org/docs/browser)
- Safari 26 (released 2025-09-15) is available for macOS Sonoma and Sequoia, not only Tahoe. — [Apple: Safari 26 security content](https://support.apple.com/en-mide/125113)
- Svelte 5.57.3 (2026-10-26), Vite 8.3.5 (2026-10-21), svelte-check 4.7.7 (2026-10-16) and Vitest 5.0.5 (2026-10-15) are the latest npm releases. — npm registry ([svelte](https://www.npmjs.com/package/svelte), [vite](https://www.npmjs.com/package/vite), [svelte-check](https://www.npmjs.com/package/svelte-check), [vitest](https://www.npmjs.com/package/vitest))

### Inferences
- Require `mathlive >= 0.111.0`. Also read the answer explicitly on submit (`mf.getValue()` / `mf.value`) rather than relying on `change`/`blur` when the card is swapped out.
- In Vite, import `mathlive/fonts.css` and `katex/dist/katex.min.css` from npm so that Vite rewrites and emits the font files into `dist/assets`. Set `base: './'` so the built `index.html` works from whatever loopback port pywebview picks. Add a build-time test that greps `dist/` for `http://` / `https://` URLs other than XML namespaces, so no CDN reference sneaks in.
- Serve the UI from pywebview's http://127.0.0.1 server, not `file://`. Under `file://` the origin is opaque `"null"`, and MathLive 0.111.2's same-origin checks no longer treat two `"null"` origins as equal, which could break virtual-keyboard messaging. ES modules and font loading under `file://` are also restricted in WebKit (general knowledge, not verified here).
- Because the WKWebView engine follows the installed Safari (14+ can run Safari 26), engine differences across macOS 14–26 should be small if Safari is kept updated. Still, the app will run on whatever WebKit the Mac has, so smoke-test after each macOS or Safari update.
- MathLive inserts `<style>` elements dynamically, so a CSP needs `style-src 'self' 'unsafe-inline'`, or else a nonce/hash strategy (not verified against MathLive).
- Neither KaTeX nor MathLive appeared to need WASM or Web Workers in the sources read. The plotting library choice should be checked for CDN-loaded fonts, tiles, or workers.

### Gaps
- No explicit minimum Safari version for MathLive or KaTeX was found.
- No source was found on MathLive behaviour specifically inside WKWebView (as opposed to Safari): IME, dead keys, or clipboard permissions. This needs a manual smoke test in the built app.
- The JS plotting library was not named, so its offline behaviour was not researched.

---

## Local testing without CI: tools, versions, one-command check, macOS vs Linux sandbox

### Takeaway
Use uv 0.13.6 to manage Python and a universal lockfile. A single `scripts/check.sh` (or `make check`) runs ruff, mypy, import-linter, pytest + Hypothesis, the frontend checks and build, Playwright WebKit UI tests, and, on macOS only, the PyInstaller build plus a smoke test of the real .app. Everything except the PyObjC/pywebview shell and the .app build runs in a Linux sandbox. Playwright's WebKit is close to, but not the same as, the system WKWebView.

### Cited Findings
- **Tool versions (from PyPI metadata):**

  | Tool | Version | Date | Requires Python | Source |
  |---|---|---|---|---|
  | uv | 0.13.6 | 2026-10-27 | — (MIT OR Apache-2.0) | [PyPI uv](https://pypi.org/project/uv/) |
  | ruff | 0.17.3 | 2026-10-27 | — | [PyPI ruff](https://pypi.org/project/ruff/) |
  | mypy | 2.4.1 | 2026-10-28 | >=3.10 | [PyPI mypy](https://pypi.org/project/mypy/) |
  | pytest | 9.2.0 | 2026-10-27 | >=3.10 | [PyPI pytest](https://pypi.org/project/pytest/) |
  | Hypothesis | 6.170.14 | 2026-10-30 | >=3.11 | [PyPI hypothesis](https://pypi.org/project/hypothesis/) |
  | import-linter | 2.15 | 2026-09-04 | >=3.10 | [PyPI import-linter](https://pypi.org/project/import-linter/) |
  | pytest-xdist | 3.8.0 | 2025-07-01 | — | [PyPI pytest-xdist](https://pypi.org/project/pytest-xdist/) |
  | pytest-playwright | 0.10.0 | 2026-10-08 | — | [PyPI pytest-playwright](https://pypi.org/project/pytest-playwright/) |
  | playwright | 1.64.1 | 2026-10-22 | — | [PyPI playwright](https://pypi.org/project/playwright/) |
  | pre-commit | 4.7.0 | 2026-10-12 | >=3.11 | [PyPI pre-commit](https://pypi.org/project/pre-commit/) |
  | PyInstaller | 6.22.3 | 2026-09-12 | <3.16,>=3.8 | [PyPI pyinstaller](https://pypi.org/project/pyinstaller/) |
  | platformdirs | 4.14.2 | 2026-10-31 | — | [PyPI platformdirs](https://pypi.org/project/platformdirs/) |

- PyInstaller's recent releases: 6.22.0 (2026-08-08), 6.22.1 (2026-08-15), 6.22.2 (2026-08-17), 6.22.3 (2026-09-12). Its classifiers cover 3.8–3.15. — [PyPI pyinstaller](https://pypi.org/project/pyinstaller/)
- Playwright for Python 1.64.1 bundles Chromium 156.0.8078.4, WebKit 27.2 and Firefox 157.0, with macOS 11+ arm64 wheels. — [PyPI playwright](https://pypi.org/project/playwright/)
- Playwright requires "macOS 14 (Sonoma) or later". Install with `pip install pytest-playwright` then `playwright install`. — [Playwright Python intro](https://playwright.dev/python/docs/intro)
- Playwright's WebKit is "derived from the latest WebKit main branch sources, often before these updates are incorporated into Apple Safari". "Playwright doesn't work with the branded version of Safari since it relies on patches." `playwright install webkit` installs only WebKit, which is about 180M and stored in `~/Library/Caches/ms-playwright` on macOS. — [Playwright browsers](https://playwright.dev/python/docs/browsers)
- pywebview's darwin-only dependencies are environment-marked (`sys_platform=='darwin'`). — [pywebview pyproject.toml](https://raw.githubusercontent.com/r0x0r/pywebview/master/pyproject.toml)

### Inferences
**Project layout and enforcement**
- Use a `src/` layout with `app/core` (pure: scheduling, SQLite, checking), `app/checker` (SymPy worker), `app/bridge` (the API object exposed to JS, plain Python, no GUI imports) and `app/shell` (the only package that imports `webview`/PyObjC).
- Add an import-linter contract in `pyproject.toml` so `core`, `checker` and `bridge` must not import `app.shell`, `webview` or `objc`. This keeps everything except `shell` testable on Linux.
- Mark macOS-only tests with `@pytest.mark.skipif(sys.platform != "darwin", reason="Cocoa")` and register a `ui` marker for Playwright tests.

**UI tests without the native window**
- Serve `ui/dist` with a tiny test server, or `vite preview`. Inject a fake `window.pywebview.api` via `page.add_init_script(...)` that forwards calls to the real Python `bridge` object through a test-only HTTP endpoint, or to recorded fixtures. Then dispatch `pywebviewready`.
- Run these with `pytest --browser webkit`. That exercises Svelte + KaTeX + MathLive in a WebKit build on both macOS and Linux.
- Add an offline test: `page.route("**/*", ...)` aborts and fails on any request not to `127.0.0.1`, or the context is set offline after load, so a CDN regression fails the build.

**Real-app smoke test (macOS only)**
- Give the frozen app a `--self-test` flag. It starts pywebview hidden or offscreen, waits for `loaded`, uses `window.evaluate_js` to render one KaTeX formula and one MathLive field, calls one bridge method, checks the SymPy worker answers, and exits 0 or 1.
- This is the only automated test of the actual WKWebView, PyObjC and PyInstaller combination.

**Hypothesis profiles**
- Register `dev` (fast, used by the git hook) and `thorough` (more examples, used by the full check) in `conftest.py`, selected by the `HYPOTHESIS_PROFILE` environment variable.

**uv**
- Run `uv python install 3.14` and pin it in `.python-version`. Use `[dependency-groups] dev = [...]`, `uv lock` (one cross-platform lockfile), and `uv sync --locked` in the check script. `uv run` everywhere means no manual venv activation.
- `uv.lock` resolves for all platforms, so the same lock works in the Linux sandbox; the PyObjC packages are simply skipped there by their markers.

**pre-commit without GitHub**
- The pre-commit framework normally clones hook repositories, typically from GitHub. Either use `repo: local` hooks with `language: system` that run `uv run ruff ...`, or skip the framework and install a 3-line `.git/hooks/pre-commit` that runs `scripts/check.sh fast`.
- The plain hook is simpler and needs no network. Keep a tracked copy at `scripts/git-hooks/pre-commit` and install it with `git config core.hooksPath scripts/git-hooks`.

**One-command check script (`scripts/check.sh`)**
```bash
#!/usr/bin/env bash
# usage: scripts/check.sh [fast|full|app]   (default: full)
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-full}"
uv sync --locked                      # exact env from uv.lock
uv run ruff format --check .
uv run ruff check .
uv run mypy                           # config in pyproject: strict, files = src
uv run lint-imports                   # import-linter contracts
if [[ $MODE == fast ]]; then
  HYPOTHESIS_PROFILE=dev uv run pytest -q -x -m "not ui and not slow"; exit 0
fi
( cd ui && npm ci --prefer-offline && npx svelte-check && npx vitest run && npm run build )
HYPOTHESIS_PROFILE=thorough uv run pytest -q -n auto -m "not ui"
uv run playwright install webkit      # no-op once cached
uv run pytest -q -m ui --browser webkit
if [[ $(uname) == Darwin && ( $MODE == full || $MODE == app ) ]]; then
  uv run pyinstaller packaging/Toishi.spec --noconfirm --clean
  codesign --verify --deep --strict dist/Toishi.app
  dist/Toishi.app/Contents/MacOS/Toishi --self-test
fi
echo "ALL CHECKS PASSED"
```
- A `Makefile` with `check`, `fast`, `app` and `backup` targets wrapping this gives the "one command". Make ships with the Xcode Command Line Tools, which also provide `git` and `codesign`.

**Linux sandbox vs macOS**
- In the Linux sandbox, run everything except the `Darwin` block. Run `uv run playwright install --with-deps webkit` there. Linux WebKit is a different port, so it catches DOM and JS logic bugs but not macOS rendering or input quirks.
- On the Mac, run `make check`, which includes the .app build and smoke test.

### Gaps
- Not verified: compatibility between uv-managed (python-build-standalone) CPython and PyInstaller 6.22 on macOS. Historically there were occasional issues with python-build-standalone builds; the python.org universal2 installer is the safe fallback. Test early.
- Not verified: whether `playwright install webkit` on Linux needs extra system packages in the specific sandbox image (`--with-deps` normally handles it).
- Free Linux VM options on Apple Silicon (UTM, Lima, etc.) were not researched. The "Linux sandbox" is assumed to be the Claude cloud or Cowork container.

---

## Python version choice for a Mac-only app in late 2026

### Takeaway
Use Python 3.14 (bugfix status, supported until 2030-10). Every key dependency supports it: PyInstaller, PyObjC 13 (cp314 wheels), PySide6 (abi3, <3.16), Playwright, pytest, Hypothesis, and SymPy master, whose CI runs on 3.14. 3.15 is only weeks old; skip it for now. 3.13 is security-only.

### Cited Findings
- From python.org's active-release table: 3.15 is bugfix status (first released 2026-10-09, end of support 2031-10); 3.14 is bugfix (2025-10-07, end 2030-10); 3.13 is security (end 2029-10); 3.12 is security (end 2028-10); 3.10 reached end-of-life 2026-10. The latest releases, all on 2026-10-25, are 3.15.2, 3.14.10, 3.13.18 and 3.12.16. — [python.org downloads](https://www.python.org/downloads/)
- SymPy 1.14.0 (2025-04-27) is still the latest release. Its classifiers stop at 3.13. — [PyPI sympy](https://pypi.org/project/sympy/)
- SymPy master is `1.15.0.dev` with `python_requires='>=3.10'`. Most CI jobs use 3.14, and one matrix includes 3.10–3.15 and pypy-3.11. — [sympy setup.py](https://github.com/sympy/sympy/blob/master/setup.py); [sympy CI workflow](https://github.com/sympy/sympy/blob/master/.github/workflows/runtests.yml); [sympy/release.py](https://github.com/sympy/sympy/blob/master/sympy/release.py)
- mpmath 1.4.1 (2026-03-15) requires >=3.9. 1.5.0 alphas also exist. — [PyPI mpmath](https://pypi.org/project/mpmath/)
- py-fsrs (`fsrs`) 6.3.2 (2026-08-09) requires >=3.10. — [PyPI fsrs](https://pypi.org/project/fsrs/)
- pyobjc-core 13.0 ships cp314/cp315 wheels. — [PyPI pyobjc-core](https://pypi.org/project/pyobjc-core/)
- PyInstaller 6.22.3 supports 3.8–3.15. — [PyPI pyinstaller](https://pypi.org/project/pyinstaller/)
- PySide6 6.12 requires <3.16, >=3.10. — [PyPI PySide6](https://pypi.org/project/PySide6/)
- Playwright 1.64.1's classifiers cover 3.10–3.14. — [PyPI playwright](https://pypi.org/project/playwright/)
- pywebview's classifiers list up to 3.13, but the package is pure Python on top of PyObjC. — [PyPI pywebview](https://pypi.org/project/pywebview/)

### Inferences
- 3.14 is the newest version that all tools, including Playwright's classifiers and SymPy's main CI, explicitly target. The only gaps are classifier lag in SymPy 1.14 and pywebview 6.2.1, both pure Python. Pin `requires-python = ">=3.14,<3.15"` and `.python-version = 3.14`.
- Re-evaluate 3.15 around mid-2027, after SymPy 1.15 and a pywebview release with 3.15 classifiers.
- Avoid the free-threaded build (pywebview #1739). The SymPy worker already runs in a separate process, so the GIL is not a bottleneck.

### Gaps
- No pywebview 6.2.1 test reports on 3.14 were found. The classifiers lag, so verify with the self-test.

---

## Running a locally built, ad-hoc-signed app on Apple Silicon; Gatekeeper; app data location

### Takeaway
A PyInstaller .app built on the same Mac is ad-hoc signed automatically and carries no quarantine attribute, so Gatekeeper does not prompt. No paid Apple account and no notarization are needed. Store data in `~/Library/Application Support/<bundle-id>/`. Only apps that arrive by download or AirDrop get quarantined.

### Cited Findings
- Apple DTS (Quinn): "all code on Apple silicon must be at least ad hoc signed". "Gatekeeper typically only kicks in if the app is quarantined". A Safari download would be quarantined and rejected. Apple wants folks "to build and run their own code without too much grief". Ad-hoc signing causes odd behaviour in subsystems that need a stable identity (for example, keychain items prompting across builds). "any Apple ID" can be a free Personal Team. — [Apple Developer Forums 740680](https://developer.apple.com/forums/thread/740680)
- Eclectic Light (2024-10-01): build tools "apply an ad-hoc signature to the app ... but their products aren't put into quarantine". Gatekeeper's notarization check applies to quarantined apps on first run. Sequoia replaced the Control-click bypass with Privacy & Security → "Open Anyway". Stripping quarantine is "a potentially dangerous workaround". — [Eclectic Light: Living with(out) notarization](https://eclecticlight.co/2024/10/01/living-without-notarization/)
- PyInstaller ad-hoc signs all collected binaries and the executable by default, and tries to sign the .app bundle with `--deep`. — [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html)
- Apple: Application Support "Contains all app-specific data and support files ... can include files that contain user data". By convention it goes in a subdirectory named after the bundle identifier (for example `~/Library/Application Support/com.example.MyApp/`), and the app creates it. Caches go in `~/Library/Caches/<bundle-id>/` and must be regenerable. — [Apple File System Programming Guide: macOS directories](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/MacOSXDirectories/MacOSXDirectories.html)
- platformdirs' macOS `user_data_dir` is `~/Library/Application Support/$appname/$version` (platformdirs 4.14.2). — [platformdirs macos.py](https://github.com/tox-dev/platformdirs/blob/main/src/platformdirs/macos.py)

### Inferences
- **Workflow:** run `make app`, then `ditto dist/Toishi.app /Applications/Toishi.app` (or drag it in Finder). It launches with no prompt because nothing quarantined it. If the app ever arrives via AirDrop, a browser, or a zip downloaded from iCloud.com, rebuild it locally rather than stripping xattrs.
- Never modify files inside the .app after the build, for example editing assets in `Contents/Resources`. That invalidates the ad-hoc signature, and Apple Silicon will refuse to run the changed code. Rebuild instead. `codesign --verify --deep --strict` in the check script catches this.
- Use a fixed reverse-DNS bundle ID in the PyInstaller `BUNDLE(bundle_identifier=...)`, for example `com.<name>.toishi`. Use exactly that for the data directory, rather than platformdirs' default app-name/version path, which would split data across versions.
- **Layout:** `~/Library/Application Support/<bundle-id>/` holds `app.db` (plus `-wal`/`-shm`), `backups/` and `logs/`. Bundled read-only assets (the built UI and seed decks) live inside the .app.
- **Notarization:** for a personal, locally built app, notarization and Developer ID are unnecessary. Notarization requires a paid Apple Developer Program membership, which is general knowledge not verified in this session.
- A free Personal Team "Apple Development" identity gives a stable signature if a future feature uses the keychain or TCC prompts. With an identity, PyInstaller enables hardened runtime, which may need entitlements for Python. Untested; stay ad-hoc unless a need appears.

### Gaps
- Not verified: the exact hardened-runtime entitlements a PyInstaller + PyObjC app needs if signed with an Apple Development identity.
- No primary Apple doc was fetched on which processes attach `com.apple.quarantine`. The claim that locally built files are not quarantined rests on Quinn and Eclectic Light.

---

## Backups: git bundle to iCloud Drive, Time Machine + SQLite WAL, scheduled backups (launchd)

### Takeaway
A daily `git bundle create --all` written to a temp file, verified, then moved into iCloud Drive with dated retention is a reliable full-history backup. Never put the live repo or the live SQLite database in iCloud or Dropbox. Time Machine of a live WAL database is crash-consistent at best, so also take an app-level `VACUUM INTO` snapshot that Time Machine and iCloud can copy safely. Schedule with a per-user launchd agent (`StartCalendarInterval`), not cron.

### Cited Findings
- `git bundle create backup.bundle --all` takes "a full backup of the repository in the sense that all refs are included". A bundle without exclusions is self-contained and can be cloned with `git clone file.bundle dir`. `git bundle verify` checks the format and prerequisites and exits nonzero if invalid. Bundles do not include "the index, working tree, the stash, per-repository configuration, hooks, etc." The manual prefers git tooling over `cp -r` because a repo copied mid-change can be corrupt. — [git-bundle docs](https://git-scm.com/docs/git-bundle)
- iCloud Drive can create numbered duplicates of files inside `.git`, such as `refs/heads/main 2`, and sometimes drops the unsuffixed original. Git then fails with "fatal: bad object refs/heads/main 2" and similar errors. — [dev.to: side effect of storing a git repo in iCloud Drive](https://dev.to/architchandra/a-side-effect-of-storing-a-git-repository-in-icloud-drive-7ed)
- A third-party issue title (weak source, title only) describes iCloud FileProvider corruption when a repo sits under `~/Documents`. — [claudeissues.com #47241](https://claudeissues.com/issue/47241-macos-session-snapshot-hook-fossilises-icloud-fileprovider-corruption-when-repo)
- SQLite WAL: "All processes using a database must be on the same host computer; WAL does not work over a network filesystem." The WAL file "is part of the persistent state of the database and should be kept with the database if the database is copied or moved". Separating them can lose committed transactions or corrupt the database. — [SQLite WAL](https://www.sqlite.org/wal.html)
- SQLite "How to corrupt": background backup tools copying mid-transaction can produce a corrupt copy. Copying the database without its journal or WAL is a corruption path. Buggy locking, "especially ... network filesystems", can corrupt. Safe live-database backup methods are `sqlite3_rsync`, `VACUUM INTO filename`, and the backup API: "Any of the above approaches will work even on a live database." — [SQLite: How To Corrupt](https://www.sqlite.org/howtocorrupt.html)
- SQLite forum thread on filesystem backup software (forum posters, not official guidance): "You cannot backup an open, changing, SQLite database and depend on getting a perfect uncorrupted backup" (Simon Slavin). Time Machine's APFS snapshots do not change that. A restored snapshot behaves like a crash (Warren Young). Suggested remedies are the backup API, `VACUUM INTO`, or a full checkpoint with writes paused. — [SQLite forum: backup via filesystem backup software](https://sqlite.org/forum/forumpost/796a192a95)
- Apple: "The preferred way to add a timed job is to use `launchd`." cron "has been deprecated in favor of launchd". With `StartCalendarInterval`, if the Mac is asleep the job runs on wake, but if it is off the job waits for the next scheduled time. cron jobs do not run while asleep or off. — [Apple: Scheduling Timed Jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)
- Per-user agents live in `~/Library/LaunchAgents`. Load them with `launchctl bootstrap gui/<uid> <plist>` (the modern equivalent of `load`), which generally needs no sudo. The plist must be owned by the user and not group- or world-writable. — [ss64 launchctl](https://ss64.com/mac/launchctl.html)

### Inferences
**Repo location**
- Keep the working repo in `~/Developer/<project>` or `~/code/<project>`. Not under `~/Documents` or `~/Desktop`, which iCloud "Desktop & Documents Folders" may sync. Not in iCloud Drive.

**Bundle backup**
- Run `git bundle create "$TMPDIR/x.bundle" --all`, then `git bundle verify`, then `mv` the file into iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs/Backups/<project>/repo-YYYY-MM-DD.bundle`).
- Writing to a temp file then moving it means iCloud only ever sees a complete file. A single immutable file per day avoids the multi-file sync conflicts that break `.git`.
- Keep about 30 dated bundles rather than overwriting one file, so a bad day cannot destroy the only copy.
- Commit or stash-commit work before the nightly run, because uncommitted changes, stashes (possibly), config and hooks are not in the bundle. Time Machine covers the working tree. Track hook scripts in the repo (`core.hooksPath`) so they are in the bundle.
- Monthly restore drill: `git clone repo-DATE.bundle /tmp/restore && git -C /tmp/restore fsck --full`.

**Study data**
- The app's SQLite database stays in `~/Library/Application Support/<bundle-id>/`, never in iCloud.
- The app takes its own daily snapshot with `VACUUM INTO 'backups/app-YYYY-MM-DD.db'` (or Python's `sqlite3.Connection.backup()`), for example on first launch each day, and prunes old snapshots. The backup script copies the newest snapshot into iCloud Drive as a single closed file. Time Machine then backs up both the live database and the consistent snapshots.

**Time Machine with WAL**
- A Time Machine snapshot that captures `app.db`, `-wal` and `-shm` together restores like a power-loss crash. SQLite normally recovers that to the last committed transaction, but forum participants disagree on guarantees, so the `VACUUM INTO` snapshots are the dependable restore point.
- Exclude rebuildable folders from Time Machine to save space (`tmutil addexclusion` on `.venv`, `ui/node_modules`, `build`, `dist`). The command is general knowledge, not verified here.

**Scheduling**
- `~/Library/LaunchAgents/com.<name>.toishi.backup.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.NAME.toishi.backup</string>
  <key>ProgramArguments</key><array>
    <string>/bin/zsh</string><string>/Users/NAME/Developer/toishi/scripts/backup.sh</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>37</integer></dict>
  <key>StandardOutPath</key><string>/Users/NAME/Library/Logs/toishi-backup.log</string>
  <key>StandardErrorPath</key><string>/Users/NAME/Library/Logs/toishi-backup.log</string>
</dict></plist>
```
- Load it with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.NAME.toishi.backup.plist`. Test it with `launchctl kickstart -k gui/$(id -u)/com.NAME.toishi.backup` and check the log.
- `scripts/backup.sh` (zsh; `-u`/`-e` safe):
```zsh
#!/bin/zsh
set -euo pipefail
REPO="$HOME/Developer/toishi"
DATA="$HOME/Library/Application Support/com.NAME.toishi"
DEST="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Backups/toishi"
STAMP=$(date +%F); mkdir -p "$DEST"
TMP=$(mktemp -d)
git -C "$REPO" bundle create "$TMP/repo.bundle" --all
git -C "$REPO" bundle verify "$TMP/repo.bundle" >/dev/null
mv "$TMP/repo.bundle" "$DEST/repo-$STAMP.bundle"
if [[ -f "$DATA/app.db" ]]; then
  /usr/bin/sqlite3 "$DATA/app.db" "VACUUM INTO '$TMP/app.db'"
  mv "$TMP/app.db" "$DEST/app-$STAMP.db"
fi
# keep newest 30 of each
for pat in 'repo-*.bundle' 'app-*.db'; do
  ls -1t "$DEST"/${~pat} 2>/dev/null | tail -n +31 | while read -r f; do rm -f -- "$f"; done
done
rmdir "$TMP" 2>/dev/null || true
```
- A `make backup` target runs the same script on demand.

### Gaps
- Not verified: whether a launchd agent running `/bin/zsh` can write to iCloud Drive (`~/Library/Mobile Documents`) without a TCC privacy prompt, or needs Full Disk Access. The first `kickstart` test run will show it, and the log will contain "Operation not permitted" if access is blocked.
- Not verified: whether iCloud "Optimize Mac Storage" eviction affects reading back old bundles (they would be re-downloaded on access, which needs network at restore time).
- Not verified from Apple docs: whether Time Machine on APFS takes a local snapshot of the source before copying (it determines whether `db` + `-wal` are captured atomically).
- Not verified whether `--all` includes `refs/stash` in practice. The man page lists the stash as excluded local state, but the stash is stored as a ref. Test it with `git bundle list-heads`.

---

## What should the concrete stack and one-command setup be? (synthesis)

### Takeaway
Recommended stack as of November 2026: Python 3.14 via uv 0.13.6, pywebview 6.2.1 (system WKWebView, pinned), PyInstaller 6.22.3 onedir `.app` (arm64, ad-hoc signed by default), and a Svelte 5 / Vite 8 UI built to `ui/dist` with KaTeX 0.19.1 and MathLive ≥0.111.x self-hosted, served from pywebview's loopback server under a strict CSP. SQLite lives in `~/Library/Application Support/<bundle-id>`. `make check` runs lint, types, layering, Python tests, the UI build, Playwright WebKit tests, the .app build, and a smoke test. A launchd agent makes nightly git-bundle and `VACUUM INTO` copies into iCloud Drive, with Time Machine on top. PySide6 6.12 + QtWebEngine is the documented fallback if pywebview blocks progress.

### Cited Findings
- All versions and behaviours in this section are cited in the sections above: [PyPI pywebview](https://pypi.org/project/pywebview/), [PyPI pyinstaller](https://pypi.org/project/pyinstaller/), [PyPI uv](https://pypi.org/project/uv/), [python.org downloads](https://www.python.org/downloads/), [PyInstaller feature notes](https://pyinstaller.org/en/stable/feature-notes.html), [MathLive CHANGELOG](https://github.com/arnog/mathlive/blob/master/CHANGELOG.md), [KaTeX browser docs](https://katex.org/docs/browser), [git-bundle](https://git-scm.com/docs/git-bundle), [SQLite How To Corrupt](https://www.sqlite.org/howtocorrupt.html), [Apple Scheduling Timed Jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html).

### Inferences
**Why pywebview over PySide6 now**
- It avoids roughly 250 MB of Chromium (the QtWebEngine wheel).
- It uses the same native WebKit the user's Safari uses, which is better for macOS text input and IME.
- Both options need macOS 14+ anyway (the PySide6 wheels and Playwright).
- The project needs nothing Qt-specific.
- The costs are accepted with mitigations: pin versions, keep the thin `shell/` adapter, run the `--self-test` smoke, keep debug off in release builds, test Cmd+Z in a math field, and store all state in SQLite.

**PyInstaller spec essentials (onedir .app)**
- `Analysis(['src/app/__main__.py'], datas=[('ui/dist', 'ui')], hiddenimports=[...])`
- `EXE(..., console=False, target_arch='arm64')`
- `COLLECT(...)`
- `BUNDLE(coll, name='Toishi.app', bundle_identifier='com.NAME.toishi', icon='packaging/icon.icns', info_plist={'NSHighResolutionCapable': True, 'LSMinimumSystemVersion': '14.0'})`
- Do not enable `argv_emulation` (PyInstaller warns against it with UI toolkits).
- Collect pywebview's JS and data files if the hook does not; check whether `--collect-data webview` is needed.

**Multiprocessing for the SymPy worker**
- macOS uses the `spawn` start method. In a frozen app, call `multiprocessing.freeze_support()` first in `__main__`. This is a standard PyInstaller requirement, not re-verified here.
- Start the worker after the window is up so the UI appears quickly. Give each check a timeout and kill/restart the worker if it hangs.

**Entry point**
- `if __name__ == "__main__": freeze_support()`
- Resolve the data dir from the bundle ID, open SQLite (WAL, `synchronous=NORMAL` or `FULL`), and start the checker worker.
- `webview.create_window(title, 'ui/index.html', js_api=Api(...), width/height/x/y restored from the settings table, min_size=(900, 600), text_select=True)`.
- `webview.start(private_mode=True, debug=bool(os.getenv('APP_DEBUG')), menu=[...])`.
- `text_select=True` is needed so users can select and copy text in cards. The default is False.

**Makefile targets**
- `make setup`: `uv python install 3.14 && uv sync && (cd ui && npm ci) && uv run playwright install webkit && git config core.hooksPath scripts/git-hooks`.
- `make fast` (git hook), `make check` (everything), `make app` (build + verify + smoke), `make install-app` (`ditto` to /Applications), `make backup`.

**Cost**
- Every tool listed is free and open source or ships with macOS. No GitHub, CI service, Apple Developer membership, or paid sync is required. iCloud Drive's free 5 GB tier comfortably holds a month of compressed git bundles for a code-only repo (inference; size depends on the repo).

### Gaps
- The bundle size and cold-start time of the recommended pywebview + PyInstaller + SymPy build were not measured. The developer should record `du -sh` and time-to-first-paint on the first build to confirm the size and startup advantage over Qt.
