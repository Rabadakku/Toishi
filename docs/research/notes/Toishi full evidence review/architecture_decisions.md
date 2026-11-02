# Toishi architecture and technology decisions: evidence review (as of 2026-11-01)

## 0. Scope, method and limits of this review

### Takeaway
This note re-checks ADR-0001 to ADR-0018 against primary sources dated up to 2026-11-01 and against small experiments run on the repo's own pinned dependencies. No ADR needs reversing. Three things need work: the shell/bridge hardening in ADR-0002 and ADR-0012 (cheap, about 50 lines), the unlicensed FSRS fitting package in ADR-0013/0016 (blocks any distribution), and the ad-hoc-signed, unnotarized packaging in ADR-0001 (fine for the owner's Mac, wrong for anyone else's).

### Cited Findings
- Three earlier notes already cover, and are not repeated here: pywebview basics, the PySide6, Tauri, Briefcase and Swift comparison, MathLive/KaTeX on WKWebView, the Python 3.14 choice, running an ad-hoc-signed app locally, and Time Machine/iCloud backups — [mac_stack_tooling.md](/home/claude/research_notes/Toishi gaps research/mac_stack_tooling.md); Anki's architecture, Qt alternatives, PyInstaller vs Nuitka vs Briefcase, and data design — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md); threat modelling, SQLite durability and release engineering ($99/yr Developer ID, hardened runtime, `notarytool`) — [engineering_process.md](/home/claude/research_notes/Practice systems and learning science/engineering_process.md).
- The repo being reviewed: ADRs in [docs/decisions](/docs/decisions), rules in [AGENTS.md](/AGENTS.md), the Mac hand-test results in [docs/backlog.md](/docs/backlog.md) (2026-11-01, macOS 26.6.2).
- Experiments run for this review (all on Linux, all disposable): the repo's real `app.api.Api` driven through the installed pywebview 6.2.1 dispatcher; `fsrs-rs-python==0.9.3` in a scratch venv; the fsrs 6.6.2 crate source; a uv-managed CPython 3.14.10 — probe script at [/tmp/claude-0/-home-claude/69fba741-8000-5b9f-9f3e-784c41d7a692/scratchpad/exp_bridge/probe.py](/tmp/claude-0/-home-claude/69fba741-8000-5b9f-9f3e-784c41d7a692/scratchpad/exp_bridge/probe.py).

### Inferences
- Because the owner stated Mac-only and no-spend, Windows and iPad are hedging concerns (keep the seams clean), not plans, and the $99/yr Developer ID is an explicit decision for the owner, not a default recommendation.
- English-only lowers the priority of IME testing; dead keys and paste still matter for names and math entry.

### Gaps
- The WebSearch budget ran out part-way. Unanswered for that reason: Anki-HTML CVE precedents, F_FULLFSYNC latency on Apple silicon, and field reports on WKWebView message-handler exposure across frames. A follow-up message can resume the search.
- GitHub's API and issue/commit search were not reachable (HTTP 403, robots-disallowed). So: no pywebview commit cadence or contributor counts, no issue-search results for IME, clipboard, printing or drag-and-drop, and the two open issues and PRs on fsrs-rs-python were not read.
- No macOS runtime was available. macOS facts come from the repo's own hand test (2026-11-01), from source reading, and from vendor docs; nothing about WKWebView behaviour was re-run here.

## 1. Is pywebview (ADR-0001, ADR-0002, ADR-0012) still a sound shell, and what do its source and the WebKit docs say about the JS bridge, navigation and the loopback server?

### Takeaway
pywebview 6.2.1 still fits a one-Mac app (43.2 MB and 478 ms median launch measured on the Mac), but it is slow-moving (no release for 200 days; 2 releases in 2026 against 13 in 2023) and the pinned release is thin on bridge security: no token check, no frame check, any attribute name the page sends is dispatched (verified: private and dunder members of the repo's `Api` ran), the API is re-injected after every navigation, and the app installs no navigation policy or drop handling. Today the CSP, the DOM-built renderers and "links never navigate" are the real defence; that is sound but thin, and closing the gaps is small, local work in `app/shell.py`.

### Cited Findings
**Maintenance signals**
- Releases: 5.4 (2025-01-27), 6.0 (2025-08-08), 6.1 (2025-10-21), 6.2 (2026-04-13), 6.2.1 (2026-04-15); nothing since, which is 200 days at 2026-11-01. Releases per calendar year: 13 in 2023, 10 in 2024, 3 in 2025, 2 in 2026 — [PyPI JSON](https://pypi.org/pypi/pywebview/json)
- BSD-3-Clause; PyPI classifiers list Python 3.7 to 3.13 only (no 3.14), `requires_python >=3.8`. The repo runs it on 3.14 and its suite passes (4144 core tests, 79 WebKit page tests, build and `.app` self-test) — [PyPI JSON](https://pypi.org/pypi/pywebview/json); [docs/backlog.md](/docs/backlog.md)
- 6.2 release notes list Cocoa fixes: a use-after-free on ARM64, a single shared AppDelegate, memory leaks on macOS Tahoe, file-picker MIME types, and a drag handler — [pywebview releases](https://github.com/r0x0r/pywebview/releases)
- Master is well ahead of 6.2.1. A `diff` of master against the installed 6.2.1 is about 132 lines in `cocoa.py`, 290 in `util.py`, 59 in `http.py`, 97 in `window.py` and 330 in `js/api.js`. There is no 6.3 yet. Master adds a bridge token check, `removeScriptMessageHandlerForName_` cleanup, a multi-screen coordinate fix and a test-mode activation policy — [master cocoa.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/cocoa.py); [master util.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/util.py); [master http.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/http.py)
- Master `js/api.js` still builds stubs with `new Function(` (line 75), so the repo's CSP patch (`app/csp_compat.py`) would still be needed after the next release — [master api.js](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/js/api.js)
- Maintainers: r0x0r is the principal maintainer; collaborator `smparkes` answered on #1826 — [issue #1826](https://github.com/r0x0r/pywebview/issues/1826)
- Open issue #1866 (opened 2026-10-16; 6.2.1, macOS 26.5.2, Python 3.13): the title overlaps the traffic-light buttons and they become unclickable; the reporter says it also happens on macOS 27 and traced it to `debug=True`; no maintainer reply, last activity 2026-10-23 — [issue #1866](https://github.com/r0x0r/pywebview/issues/1866). The older #1826 is the same symptom; `smparkes` could not reproduce it on Python 3.9 — [issue #1826](https://github.com/r0x0r/pywebview/issues/1826)
- Other open items: #1822 (`Window.show()` steals focus when the window was created hidden) and #1699 (hang in blocking event handlers). The issues list page omitted #1866, so it is a partial snapshot — [pywebview issues](https://github.com/r0x0r/pywebview/issues)
- #1722 (alert beep on key press): r0x0r said a fix on master "seems to work" and named no release; a later commenter reports it still beeps — [issue #1722](https://github.com/r0x0r/pywebview/issues/1722)
- Mac measurements (2026-11-01, macOS 26.6.2): pywebview build 43.2 MB, median launch 478 ms; Qt spike 545.7 MB, 592 ms; both self-tests pass; dark mode follows; the title does not overlap the window buttons; typing, Cmd+Z and Shift+Cmd+Z work in the math field. Not yet checked by hand: paste, dead keys (Option+E then e), alert sound while typing — [docs/backlog.md](/docs/backlog.md)

**What the Cocoa backend does (installed 6.2.1 at `.venv/.../webview/`; master noted where checked)**
- It sets `NSAllowsArbitraryLoads` (App Transport Security off) in the process Info dictionary (6.2.1 line 36; master line 39) — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py); [master cocoa.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/cocoa.py)
- It registers one `WKScriptMessageHandler` named `jsBridge` (line 661) and a second named `browserDelegate` used for `window.print()`; printing uses the underscore selector `_printOperationWithPrintInfo_` (a private WebKit selector) — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py)
- `webView_didFinishNavigation_` calls `inject_pywebview('cocoa', ...)` after every navigation, so the API stubs and token reach whatever page loaded — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py) (lines 380-392)
- `webView_decidePolicyForNavigationAction_decisionHandler_` (line 272) allows every navigation; it only cancels Back/Forward triggered by the Delete key. `target=_blank` links go to `webbrowser.open` when `OPEN_EXTERNAL_LINKS_IN_BROWSER` is true, otherwise they load in the same view — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py)
- Settings defaults: `ALLOW_DOWNLOADS` False, `ALLOW_FILE_URLS` True (applied as the `allowFileAccessFromFileURLs` WKPreferences key, cocoa.py line 654), `OPEN_EXTERNAL_LINKS_IN_BROWSER` True. The repo sets none of them (`app/shell.py` contains no `webview.settings[...]` assignment) — [installed __init__.py](/.venv/lib/python3.14/site-packages/webview/__init__.py); [app/shell.py](/app/shell.py)
- `keyDown_` intercepts only Command-modified keys (x and c with a selection, v, a, z, q, w) and passes everything else to `super`, so dead keys and IME composition reach WebKit unmodified; the context menu is removed unless debug is on; private mode wipes the default data store (`removeDataOfTypes...`) instead of using a non-persistent store; drag-and-drop paths are recorded only when DOM drop listeners exist, then `super` handles the drop — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py) (lines 505-545); [master cocoa.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/cocoa.py)

**The bridge dispatcher**
- In 6.2.1 the `jsBridge` handler does `json.loads(message.body())` and calls `js_bridge_call(window, body['funcName'], body['params'], body['id'])`. It reads no token and never looks at `message.frameInfo` — [installed cocoa.py](/.venv/lib/python3.14/site-packages/webview/platforms/cocoa.py) (lines 158-168)
- `js_bridge_call` resolves the name with `func = window._functions.get(func_name) or get_nested_attribute(window._js_api, func_name)`, where `get_nested_attribute` is a bare `getattr` chain over the dotted name (util.py lines 268-274 and 330). The `startswith('_')` filter exists only in the stub generator that builds the JS-side API (line 193), not on the call path. Master has the same shape (lines 401 and 478, filter only at line 299) and adds `is_js_bridge_token_valid` (lines 364-383) — [installed util.py](/.venv/lib/python3.14/site-packages/webview/util.py); [master util.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/util.py)
- Experiment, repo's real `Api` through 6.2.1's real `js_bridge_call` with a stub window: `ping` ran as intended; a message naming `_close` ran the non-bridge lifecycle method (the profile storage was closed); a message `__setattr__` with params `["_error", "set from the page"]` changed `api._error`; `__init__` with no params re-ran the constructor and replaced `api._lock`; an unknown name was only logged — [probe.py](/tmp/claude-0/-home-claude/69fba741-8000-5b9f-9f3e-784c41d7a692/scratchpad/exp_bridge/probe.py); [app/api.py](/app/api.py) (`Api` has underscore helpers `_open_last`, `_open`, `_close`, `_study`, `_store`, `_storage_or_none`, `_guard`; 29 public bridge methods)
- Return path in 6.2.1: `window.evaluate_js(f'window.pywebview._returnValuesCallbacks["{func_name}"]["{value_id}"]({retval})')` interpolates two strings the page chose (util.py lines 264-266). The repo reroutes bridge returns to `run_js` so the code is not wrapped in `eval` — [installed util.py](/.venv/lib/python3.14/site-packages/webview/util.py); [app/shell.py](/app/shell.py)
- The loopback server also registers `POST /js_api/<uid>` with `Access-Control-Allow-Origin: *`, but in 6.2.1 `server.js_callback` is never assigned anywhere in the package, so the route cannot dispatch. This matches ADR-0002's statement that the route is used only by other platforms — [installed http.py](/.venv/lib/python3.14/site-packages/webview/http.py) (lines 80, 106-118); [ADR-0002](/docs/decisions/0002-offline-and-csp.md)
- pywebview's own security guide covers only HTTPS for the local server and the CSRF token — [pywebview security guide](https://pywebview.flowrl.com/guide/security.html)

**What WebKit and Apple say about who can reach the handler**
- Apple: `add(_:name:)` defines `window.webkit.messageHandlers.<name>.postMessage()` in "the page's main content world"; the page does not say whether subframes can call it and does not mention validating the sender — [Apple: WKUserContentController.add(_:name:)](https://developer.apple.com/tutorials/data/documentation/webkit/wkusercontentcontroller/add(_:name:).json)
- Apple: `WKScriptMessage.frameInfo` is "The frame that sent the message" — [Apple: WKScriptMessage.frameInfo](https://developer.apple.com/tutorials/data/documentation/webkit/wkscriptmessage/frameinfo.json)
- WebKit source: `WebKitNamespace` is constructed per `LocalDOMWindow`, and `UserMessageHandlersNamespace` per `LocalFrame`. `messageHandlers()` and `namedItem()` match by handler name and content world; neither file checks for the main frame or the security origin — [WebKit WebKitNamespace.cpp](https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/page/WebKitNamespace.cpp); [WebKit UserMessageHandlersNamespace.cpp](https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/page/UserMessageHandlersNamespace.cpp)

**What the repo does and does not have**
- CSP in `web/index.html` includes `script-src 'self'`, `frame-src 'none'`, `form-action 'none'`, `base-uri 'none'`, `connect-src 'self'` — [web/index.html](/web/index.html); [ADR-0002](/docs/decisions/0002-offline-and-csp.md)
- The Markdown renderer never creates anchors ("Links never navigate... they are shown as styled text"); the Anki-HTML renderer drops `href` — [web/src/lib/markdown.ts](/web/src/lib/markdown.ts); [ADR-0017](/docs/decisions/0017-card-media-and-imported-html.md)
- A grep of `app/`, `web/src` and `web/index.html` finds no navigation delegate or policy, no `WKContentRuleList`, no `dragover` or `drop` handler, and no Host or Origin validation on the loopback server. ADR-0002 already lists a `WKContentRuleList` as a possible later layer — [app/shell.py](/app/shell.py); [ADR-0002](/docs/decisions/0002-offline-and-csp.md)
- For contrast, Anki's own media server answers 403 to requests whose Host or Origin is not localhost — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md) (section 1)

### Inferences
- **Headline hardening item: allow-list the dispatcher.** The "thin, type-checked bridge" in ADR-0012 holds for the stubs but not for the dispatcher beneath it. Anything that can post to `jsBridge` can invoke every attribute reachable from `Api`, including `_close`, `__setattr__` and `__init__`. Reaching it needs script execution in an app frame, which the CSP currently prevents, so this is defence in depth against a future CSP bypass or a MathLive/KaTeX/sanitizer bug, not a live hole. Fix: in `app/shell.py`, wrap `webview.util.js_bridge_call` and also rebind `webview.platforms.cocoa.js_bridge_call` (cocoa imports it by name) so a name not in `app.api.public_methods()` is dropped; add a test beside `tests/ui/test_pywebview_bridge.py` that sends `_close` and `__setattr__` through the real dispatcher. The wrapper must still pass the few pywebview control names the app really uses (find them by running the self-test).
- **Add a frame and origin check on the native handler.** WebKit's per-frame namespaces mean a subframe could call the handler if one ever existed; `frame-src 'none'` is the only thing preventing it. Overriding `JSBridge.userContentController_didReceiveScriptMessage_` to require `message.frameInfo().isMainFrame()` and a `127.0.0.1` origin would make that structural. Whether PyObjC accepts replacing that method on a Python-defined `NSObject` subclass was not tested (the repo already patches `cocoa.BrowserView._add_edit_menu`, which is a plain Python method), so this needs a Mac test.
- **Add a navigation policy and close the drop and file-URL paths.** Because the API is re-injected into any page that loads, any off-origin navigation hands that page the bridge. The designed-out paths (no anchors, no `href`, `form-action 'none'`) leave drag-and-drop as the likely accidental route: dropping a file or link onto a WKWebView normally navigates to it unless the page cancels the drop (general WebKit behaviour, not verified in this session). Cheap fixes: window-level `dragover`/`drop` handlers that call `preventDefault`; `webview.settings['ALLOW_FILE_URLS'] = False`; a wrapper over `BrowserDelegate.webView_decidePolicyForNavigationAction_decisionHandler_` that cancels anything except `http://127.0.0.1:<port>/`. A `WKContentRuleList` allow-list is an alternative; it needs the block-all-then-`ignore-previous-rules` pattern, which was not tested.
- **Add a Host-header check to `MediaMiddleware`** (reject any Host other than `127.0.0.1:<port>`). DNS rebinding is unlikely to succeed against a random port and unguessable paths, but the check is a few lines and matches Anki's practice.
- **The next pywebview release will break the exact-text patches loudly.** `PywebviewCompatError` fires on any version other than 6.2.1, and master changed `api.js` (330-line diff) and added the token. That is the right failure mode; budget a day for re-verifying `csp_compat.py`, the edit-menu patch and the loopback patch when it ships. The token arrives with that release but does not replace the allow-list: the token is injected into whatever page loaded.
- **Cadence is a risk, not a verdict.** There is no sign of abandonment (issue activity to 2026-10-23, collaborator replies), but 200 days without a release, a 6.2.1 that lists no Python 3.14 classifier, and an unanswered macOS 26/27 title-bar report mean macOS 27 compatibility is unproven. The ADR-0001 decision rule (keep pywebview unless a manual check fails with no workaround in `app/shell.py`) is still the right rule. Keep the `spike-qt` group alive as the tested fallback.
- **Manual-test items that block calling the shell done:** paste, dead keys, alert beep, audio playback with byte ranges (ADR-0017 says "not yet confirmed on the Mac"), print, and a file dropped on the window.

### Gaps
- Commit cadence, contributor counts and release-note detail for pywebview (GitHub API/search blocked).
- Whether the #1722 beep fix shipped in 6.2 or is master-only.
- IME, dead-key, clipboard, printing and drag-and-drop issue reports (issue search blocked); the source shows only Command-modified keys are intercepted.
- Apple documentation or field reports confirming that `WKScriptMessageHandler`s are reachable from subframes; the WebKit source files read here show no main-frame check but do not prove it (the check could live in `UserMessageHandler` or in the UI process).
- Default WKWebView behaviour when a file is dropped on a page that does not cancel the drop, on macOS 26.

## 2. Alternatives to pywebview (Tauri 2 plus a Python sidecar, Electron, PySide6/QtWebEngine, a Swift shell, Briefcase/Toga, Pyodide) and what each implies for a later Windows or iPad version

### Takeaway
None of the alternatives fixes a current problem enough to justify switching: they trade pywebview's slow cadence for more packaging surface, and none gives a free path to iPad, because Python on iOS runs only embedded, with no subprocess or multiprocessing, which breaks the worker-based SymPy isolation and any sidecar design. Keep pywebview behind the `app/shell.py` seam with PySide6 as the documented fallback; a thin Swift shell is the best long-term base if pywebview stalls, and Briefcase/Toga is the only Python-native route that reaches iOS and Windows from one codebase.

### Cited Findings
- Tauri: the start page describes "all major desktop and mobile platforms" on "the system's native webview" — [Tauri start](https://v2.tauri.app/start/). The sidecar page requires one binary per target triple (`externalBin` plus a `-$TARGET_TRIPLE` suffix) and says nothing about iOS or Android — [Tauri sidecar](https://v2.tauri.app/develop/sidecar/). `@tauri-apps/cli` 2.12.4 was published 2026-10-21 — [npm](https://registry.npmjs.org/@tauri-apps/cli)
- Python on iOS: "the only way you can use Python on iOS is in embedded mode"; default minimum iOS 13.0; the App Store is the only distribution route and requires every binary module to be a signed framework — [Python docs: Using Python on iOS](https://docs.python.org/3/using/ios.html). "An iOS app cannot use any form of subprocessing, multiprocessing, or inter-process communication" (it will lock up or crash) — [Python docs: platform availability](https://docs.python.org/3/library/intro.html)
- Briefcase iOS: generates an Xcode project; a package with a binary component needs a wheel compiled for iOS and "most projects do not provide iOS-compatible wheels"; deploying to a physical device needs an Apple Developer account — [Briefcase iOS](https://briefcase.beeware.org/en/stable/reference/platforms/iOS/xcode/)
- Toga's WebView lists macOS, Linux (GTK and Qt), Windows, iOS and Android as supported; it displays only `http://` and `https://` URLs, not `file://`, and suggests a `localhost` server in a background thread; `evaluate_javascript` returns an awaitable; on Windows it needs the WebView2 runtime. The page documents no JS-to-Python message channel — [Toga WebView](https://toga.beeware.org/en/stable/reference/api/widgets/webview/)
- Briefcase 0.4.7 (2026-10-27; releases 0.4.5 on 2026-09-08 and 0.4.6 on 2026-10-13), Python classifiers 3.12 to 3.15, BSD-3-Clause. Toga 0.5.7 (2026-10-01) — [PyPI: briefcase](https://pypi.org/pypi/briefcase/json); [PyPI: toga](https://pypi.org/pypi/toga/json)
- pywebview on Windows needs pythonnet (".NET 4.0") and, for current Chromium, the WebView2 runtime; macOS needs PyObjC; Android is reached through Kivy's packaging; no iOS backend is listed — [pywebview installation](https://pywebview.flowrl.com/guide/installation.html)
- PySide6 6.12.0 was published 2026-10-08 (`requires_python <3.16,>=3.10`) — [PyPI: PySide6](https://pypi.org/pypi/PySide6/json). The earlier note puts the QtWebEngine wheel near 250 MB on macOS — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md). The local spike measured 545.7 MB and 592 ms against pywebview's 43.2 MB and 478 ms — [docs/backlog.md](/docs/backlog.md). ADR-0001 records Qt 6.12.0 on Chromium 140 — [ADR-0001](/docs/decisions/0001-stack-and-shell-spike.md)
- Electron 45.2.1 was published 2026-10-31 — [npm: electron](https://registry.npmjs.org/electron). The earlier note puts Electron at roughly 85 to 250 MB and notes it has the same SymPy-sidecar problem as Tauri — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md)
- Pure-Python wheels (`py3-none-any`) exist for sympy 1.14.0, mpmath 1.4.1, lark 1.3.1, fsrs 6.3.2 and platformdirs 4.14.3; `zstandard` 0.25.0 and `fsrs-rs-python` 0.9.3 are compiled per Python version and platform — [PyPI: sympy](https://pypi.org/pypi/sympy/1.14.0/json); [PyPI: mpmath](https://pypi.org/pypi/mpmath/1.4.1/json); [PyPI: lark](https://pypi.org/pypi/lark/1.3.1/json); [PyPI: fsrs](https://pypi.org/pypi/fsrs/6.3.2/json); [PyPI: fsrs-rs-python](https://pypi.org/pypi/fsrs-rs-python/0.9.3/json)
- Pyodide's package list (Pyodide 314.0.7) includes sympy 1.14.0 and mpmath 1.4.1 — [Pyodide packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)
- Python 3.14 added `compression.zstd` to the standard library (streaming `ZstdDecompressor`, `ZstdFile`, one-shot functions); the docs call it an optional module that distributors may omit — [Python docs: compression.zstd](https://docs.python.org/3/library/compression.zstd.html). The importer uses the third-party `zstandard` package (`stream_reader(..., read_across_frames=True)`) — [core/importers/anki/package.py](/core/importers/anki/package.py)
- The grader runs in a `multiprocessing` spawn worker with a 2 s hard kill — [core/grader/worker.py](/core/grader/worker.py)

### Inferences
- **Tauri or Electron:** a second language and toolchain, plus a frozen Python sidecar per target. Tauri's mobile story does not extend to the sidecar (the sidecar page is silent), and Python cannot spawn processes on iOS anyway, so neither gets Python to an iPad without embedding it in-process.
- **PySide6/QtWebEngine:** the right fallback. It would give a custom URL scheme and request interception (no loopback port, no Host issue) and a fixed engine, which also helps a later Windows port. The costs are about 12 times the bundle size, and bundled Chromium needs its own security patching: ADR-0001 records Chromium 140, and how far behind current stable that is was not measured. For an app that renders imported HTML, an ageing embedded Chromium is a real cost.
- **Swift shell with WKWebView:** the only option that puts frame checks, navigation policy and a custom scheme fully in the project's hands, and the same shell can host iPadOS. It costs a Swift codebase for an agent-built Python project, so it is a "if pywebview stalls or macOS 27 breaks it" option, not a now option. A scheme handler design was not verified against Apple docs in this session.
- **Briefcase/Toga:** active (Briefcase 0.4.5 on 2026-09-08, 0.4.6 on 2026-10-13, 0.4.7 on 2026-10-27) and the only listed Python-native route to Windows, iOS and Android. But Toga's WebView page documents no JS bridge, so the web UI would need a different Python-to-JS channel, and the existing bridge, CSP patches and loopback design would be rewritten. Not worth it for a Mac-only app.
- **iPad is a re-architecture, not a port.** What would carry over: the Svelte/MathLive/KaTeX UI, `core/` (GUI-free by import-linter), SQLite (stdlib), and the pure-Python libraries. What would not: the spawn-and-kill SymPy worker (no subprocess or multiprocessing on iOS), `fsrs-rs-python` and `zstandard` (need iOS builds), PyInstaller, and the loopback server model. A plausible iPad grader is SymPy in Pyodide inside a Web Worker that the page can terminate, since Pyodide lists SymPy 1.14.0; that was not tested on iOS WKWebView and performance is unknown.
- **Windows is feasible with the same Python and web code** (pywebview with pythonnet and WebView2). The Cocoa-specific parts (`_install_edit_menu`, the `cocoa` monkeypatches, F_FULLFSYNC, the `.app` spec) would need Windows counterparts in the shell adapter; `core/` and `web/` should port unchanged.
- **Small simplification worth noting:** with Python pinned to 3.14, `compression.zstd` could replace the `zstandard` binary wheel in the Anki importer, removing one compiled dependency (and one future iOS/Windows wheel). The decompression-bomb budget logic in `package.py` would need to be re-expressed with `ZstdDecompressor.decompress(data, max_length)`, and whether uv's python-build-standalone macOS build ships the module was not checked.

### Gaps
- Whether PySide6 officially supports iOS (the Qt docs page fetched was a redirect stub).
- Toga's JS-to-Python channel, if any, and whether a custom URL scheme is possible there.
- Whether Pyodide's SymPy runs acceptably in iOS WKWebView (WebAssembly performance, memory limits).
- The age of Qt 6.12.0's bundled Chromium relative to current stable.
- Apple documentation for `WKURLSchemeHandler` and `WKContentRuleList` (not fetched).

## 3. Packaging and signing: PyInstaller on macOS 26 with Python 3.14, Briefcase and py2app, ad-hoc signing vs Developer ID and notarization, arm64 vs universal2

### Takeaway
PyInstaller 6.22.3, onedir, arm64-only, ad-hoc signed is sound for a single developer Mac: it supports Python 3.14 since 6.15.0 and the build and self-test pass on macOS 26.6.2. The arm64-only choice is validated by macOS 27 dropping Intel. It is the wrong route for anyone else: Homebrew stopped accepting casks that fail Gatekeeper on 2026-09-01, and everyone else would face the Open Anyway flow, so before distribution the owner must pick between paying for Developer ID plus notarization, asking recipients to build from source, or accepting the friction.

### Cited Findings
- PyInstaller releases: 6.20.0 (2026-04-22), 6.21.0 (2026-06-13), 6.22.0 (2026-08-08), 6.22.1 (2026-08-15), 6.22.2 (2026-08-17), 6.22.3 (2026-09-12); `requires_python <3.16,>=3.8`; classifiers include 3.14 and 3.15 — [PyPI: pyinstaller](https://pypi.org/pypi/pyinstaller/json)
- Changelog: Python 3.14 supported since 6.15.0 (2025-08-03); Python 3.15 since 6.21.0 (2026-06-13); 6.20.0 fixed `forkserver` for 3.14.4; 6.13.0 gave each Mach-O a unique UUID (the TN3178 local-network attribution) and deprecated onefile combined with `.app` (to be blocked in 7.0); 6.22.1 and 6.22.3 mitigate GHSA-9fxf-4qw3-ghmr, which concerns onefile and setuid use — [PyInstaller changelog](https://pyinstaller.org/en/stable/CHANGES.html)
- Options: `--target-architecture` accepts x86_64, arm64 and universal2 and defaults to the running architecture; `--codesign-identity` signs collected binaries and the executable, and "If signing identity is not provided, ad-hoc signing is performed instead"; `--osx-entitlements-file` is the entitlements file for code-signing the collected binaries. Onefile `.app` bundles are "not recommended" and inefficient; UPX output cannot be code-signed; onefile executables will not work signed and notarized with the sandbox on — [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html)
- The repo's spec: `target_arch="arm64"`, `codesign_identity=None`, `entitlements_file=None`, `upx=False`, onedir, excludes anki/aqt/numpy/PySide6, `LSMinimumSystemVersion` 14.0 — [packaging/Toishi.spec](/packaging/Toishi.spec)
- Mac result: `.app` 43.2 MB, median launch 478 ms, self-test passes; this resolves ADR-0001's caveat that PyInstaller with uv's python-build-standalone CPython was unverified — [docs/backlog.md](/docs/backlog.md); [ADR-0001](/docs/decisions/0001-stack-and-shell-spike.md)
- Hardened runtime prohibits writable-and-executable memory (JIT) and loading plug-ins or frameworks signed by other developers; the opt-outs are entitlements such as `com.apple.security.cs.allow-jit`, `...allow-unsigned-executable-memory` and `...disable-library-validation`. The article does not say which an embedded interpreter needs — [Eclectic Light: Notarization: the hardened runtime](https://eclecticlight.co/2021/01/07/notarization-the-hardened-runtime/)
- Apple silicon requires signed code; ad hoc is enough locally; Apple had given no warning of changes (2026-01-17) — [Eclectic Light: code signing and future macOS](https://eclecticlight.co/2026/01/17/whats-happening-with-code-signing-and-future-macos/)
- Homebrew: "we are ending support for all casks that fail Gatekeeper checks on September 1st, 2026" (already past at this review) — [Homebrew/brew #20755](https://github.com/Homebrew/brew/issues/20755)
- macOS 27 drops Intel Macs and full Rosetta support ends with it — [HotHardware, 2026-04-22](https://hothardware.com/news/apple-drops-intel-macs-macos-27)
- Alternatives: py2app 0.28.10 (2026-02-13), earlier 0.28.8 (2024-05-25) and 0.28.9 (2025-11-29), `requires_python >=3.10` — [PyPI: py2app](https://pypi.org/pypi/py2app/json). Briefcase 0.4.7 (2026-10-27), Python 3.12 to 3.15 — [PyPI: briefcase](https://pypi.org/pypi/briefcase/json). Briefcase's macOS app page was a stub with no signing detail — [Briefcase macOS](https://briefcase.beeware.org/en/stable/reference/platforms/macOS/app/)
- A locally built, ad-hoc-signed `.app` carries no quarantine attribute, so Gatekeeper does not prompt; downloaded or AirDropped copies need the Open Anyway step in System Settings; Developer ID, hardened runtime and notarization need the $99/yr Apple Developer Program — [mac_stack_tooling.md](/home/claude/research_notes/Toishi gaps research/mac_stack_tooling.md); [engineering_process.md](/home/claude/research_notes/Practice systems and learning science/engineering_process.md)

### Inferences
- **arm64-only is correct.** macOS 27 is Apple-silicon-only, `LSMinimumSystemVersion` 14.0 is conservative, and universal2 would add size and a fat-binary signing surface for no user.
- **onedir is correct;** onefile plus `.app` is discouraged now and slated to be blocked in PyInstaller 7.
- **PyInstaller remains the best packager here.** Briefcase is more active and has a better mobile story but changes the widget and packaging model; py2app releases about once or twice a year and its Python 3.14 and signing status were not established.
- **Distribution decision (owner's call):** (a) pay $99/yr for Developer ID plus notarization, which makes Gatekeeper clean and reopens the Homebrew cask route; (b) distribute a build-from-source script (`uv sync` plus `scripts/build.sh`), which stays free and avoids quarantine because the user builds locally; (c) ship an ad-hoc `.app` with Open Anyway instructions, which is free but hostile to non-technical users. Given the stated no-spend rule, (b) is the free option that does not fight macOS. Because the project avoids GitHub, the usual GitHub-releases-plus-cask path is also unavailable unless that changes.
- **Before choosing, run a one-hour notarization spike** on a throwaway Developer ID or equivalent to learn which hardened-runtime entitlements the Python 3.14 plus PyObjC bundle needs. Because PyInstaller signs every collected binary with one identity, library validation may pass without `disable-library-validation`, but that is unverified.
- **Python 3.14.x movement:** 6.20.0's `forkserver` fix shows interpreter point releases can break PyInstaller; keep the `.app` self-test (which exercises the spawn worker) in the release gate.

### Gaps
- Which hardened-runtime entitlements a PyInstaller bundle of Python 3.14, PyObjC and the Rust extension needs.
- Briefcase and py2app signing and notarization details; the py2app changelog fetch failed.
- Gatekeeper behaviour changes in macOS 27 and its release date.
- The PyInstaller changelog's last ~1,500 characters were not read.

## 4. SQLite durability and backups (ADR-0004, ADR-0011): F_FULLFSYNC cost, WAL with FULL, the WAL-reset bug fixed in 3.51.3, iCloud and Time Machine, backup API vs VACUUM INTO

### Takeaway
The pragma set (WAL, `synchronous=FULL`, `fullfsync`, `checkpoint_fullfsync`) is the right maximum-durability configuration for macOS, but the code only demands SQLite 3.37 even though 3.51.2 and earlier have a WAL-reset corruption bug (fixed 3.51.3, with backports), and the real per-commit cost of F_FULLFSYNC on the Mac is still unmeasured. Raise the floor and measure; the design itself is sound.

### Cited Findings
- WAL-reset bug: found 2026-03-03, likely present from 3.7.0 through 3.51.2, fixed in 3.51.3 (2026-03-13), with backports 3.44.6 and 3.50.7. It needs two or more connections writing or checkpointing at the same instant. SQLite calls it "not an emergency"; a 2026-08-24 update notes a reproducer without the test hack — [SQLite: WAL](https://www.sqlite.org/wal.html)
- Releases: 3.54.1 (2026-10-16, fixes a 32-bit heap overflow), 3.54.0 (2026-10-09), 3.53.4 (2026-07-24), 3.53.0 (2026-04-09), 3.52.0 (2026-03-06, withdrawn) — [SQLite release history](https://www.sqlite.org/changes.html)
- Pragmas: `fullfsync` "determines whether or not the F_FULLFSYNC syncing method is used on systems that support it" and defaults to off ("Only Mac OS X supports F_FULLFSYNC"); `checkpoint_fullfsync` applies it to checkpoints. `synchronous=FULL` is ACID and durable in WAL mode; EXTRA is no different from FULL in WAL mode; `NORMAL` in WAL "does lose durability" — [SQLite: PRAGMA](https://sqlite.org/pragma.html)
- Apple's `fsync(2)`: fsync flushes to the drive but the drive may still reorder or delay writes, so after power loss "only some or none of their data" may be present; `F_FULLFSYNC` asks the drive to flush to permanent storage and is meant for databases needing strict write ordering. The page gives no cost figures; it is an archive page (copyright 2018) — [Apple fsync(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html)
- Repo: pragmas WAL, `synchronous=FULL`, `foreign_keys=ON`, `busy_timeout` 10000, `trusted_schema=OFF`, `fullfsync=ON`, `checkpoint_fullfsync=ON`; the only version guard is `sqlite3.sqlite_version_info < MIN_SQLITE` with "need 3.37+"; `core/health.py` reports "SQLite {version}, WAL ok" — [core/storage/connection.py](/core/storage/connection.py); [core/health.py](/core/health.py)
- Backups use `src.backup(dst)` and then `PRAGMA journal_mode = DELETE` on the copy — [core/storage/backups.py](/core/storage/backups.py) (line 105). The spec requires 30-minute backups with daily, weekly and monthly retention, an integrity check at launch, and a warning when the data folder is cloud-synced (BAK-1 to BAK-6) — [docs/spec.md](/docs/spec.md)
- The storage layer uses a per-thread read connection plus one writer thread, so more than one connection is active in one process; ADR-0018 records a use-after-free segfault from closing a reader under a running query and its fix — [ADR-0018](/docs/decisions/0018-hand-test-fixes.md); [AGENTS.md](/AGENTS.md)
- A uv-managed CPython 3.14.10 (Linux x86_64, built 2026-10-26) reports `sqlite3.sqlite_version` 3.53.1, which includes the fix. The macOS build was not tested (local check).
- Open backlog item: "Measure the per-commit cost of F_FULLFSYNC on the Mac (only tested on Linux by monkeypatch)" — [docs/backlog.md](/docs/backlog.md)
- Never keep a live SQLite database in iCloud or Dropbox; Time Machine of a live WAL database is crash-consistent at best, so take app-level snapshots (`VACUUM INTO` or the backup API) that Time Machine and iCloud can copy safely; `launchd` is the scheduler — [mac_stack_tooling.md](/home/claude/research_notes/Toishi gaps research/mac_stack_tooling.md)

### Inferences
- **Raise the floor.** Add a startup check that refuses (or loudly warns on) SQLite below 3.51.3 unless it is one of the backported lines (3.44.6+ in the 3.44 series, 3.50.7+ in the 3.50 series). The bug needs concurrent writers or checkpointers, and this app has one writer thread plus readers, which lowers exposure, but the check costs three lines and `core/health.py` already prints the version. A uv-managed 3.14.10 should satisfy it; verify on the Mac build.
- **Measure, then decide.** `fullfsync` should stay on for a data store whose loss costs weeks of review history. The measurement is a 20-line script (200 insert-and-commit cycles under the real pragmas with `fullfsync` on and off, on the Mac's internal SSD). If a commit takes tens of milliseconds it will show up only on rapid-fire answer submission; the common mitigation is to leave `fullfsync` on for `COMMIT` and `checkpoint_fullfsync` on, and batch non-critical writes.
- **Backup API vs `VACUUM INTO`:** both produce consistent snapshots; the backup API already in use is fine. The `journal_mode=DELETE` step on the copy is correct for a snapshot that Time Machine and iCloud will copy as a single file.
- The design is sound: read-only pack databases, one writable `user.db` per profile, append-only logs and forward-only migrations match the earlier notes' recommendations.

### Gaps
- F_FULLFSYNC latency on Apple silicon SSDs (search budget exhausted; no primary measurement found).
- Time Machine's APFS snapshot semantics for a live WAL database, and iCloud behaviour for `~/Library/Application Support`.
- The SQLite version inside the macOS PyInstaller bundle (only the Linux uv build was checked).
- The SQLite Library of Congress long-term-format claim was not verified.

## 5. Rendering imported Anki HTML safely (ADR-0015, ADR-0017): sanitizer vs sandboxed iframe vs separate origin, CSP in WKWebView, known bypass classes, and whether card content can reach the pywebview bridge

### Takeaway
The layered design (import-time allow-list sanitizer in core, a second independent DOM-reconstruction sanitizer in the page, a strict CSP with `frame-src 'none'`, and a media route with `nosniff`, a fixed type table and a sandboxing CSP) is stronger than the string-sanitizer approaches that keep producing advisories elsewhere. The bridge is not reachable by card content today, but the 6.2.1 bridge has no authentication of its own, so card-content safety rests entirely on the CSP and the sanitizers until the dispatcher allow-list and frame/origin check from section 1 are added.

### Cited Findings
- ADR-0017: the page rebuilds imported HTML from a `DOMParser` document (inert) node by node with `createElement` from the same allow-list core uses (compared by `tests/app/test_anki_allowlist.py`); dropped tags lose their content; no `id`, `href`, `on...` or `srcset`; `style` attributes are cleaned (foreign `url()`, CSS escapes, `expression`, `image-set` removed); `src` and `url()` load only through the card's media map; no HTML string is ever inserted; KaTeX runs with `trust: false`; each note type's CSS is scoped by core to `.anki-nt-<hash>` and the host has `contain: layout` — [ADR-0017](/docs/decisions/0017-card-media-and-imported-html.md); [web/src/lib/anki-html.ts](/web/src/lib/anki-html.ts)
- Media route: only `GET`/`HEAD`, names validated before lookup (`<64 hex>[.ext]` for user media; no `.`/`..`/backslash/NUL/control characters for pack names), symlinks not followed, fixed content-type table (no `js`, `html` or `json`; fallback `application/octet-stream`), `X-Content-Type-Options: nosniff`, `Cross-Origin-Resource-Policy: same-origin`, `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` — [app/media.py](/app/media.py); [ADR-0017](/docs/decisions/0017-card-media-and-imported-html.md)
- Test coverage: traversal, listings, ranges and a real PNG and SVG in `tests/app/test_media.py`; hostile HTML, pack images and zero off-127.0.0.1 requests, CSP violations and console errors in `tests/ui/test_anki_cards.py`. Spec DEV-14 requires a negative test that card content cannot reach `window.pywebview` — [ADR-0017](/docs/decisions/0017-card-media-and-imported-html.md); [docs/spec.md](/docs/spec.md)
- Anki serves untrusted media under a no-script CSP (`default-src 'none'` with `sandbox allow-same-origin`, comment "Never add allow-scripts") and rejects non-localhost Host/Origin — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md) (section 1)
- The HTML Sanitizer API's `Element.setHTML()` is marked "Limited availability" (not Baseline), so it cannot be the only defence — [MDN: Element.setHTML](https://developer.mozilla.org/en-US/docs/Web/API/Element/setHTML)
- DOMPurify, the standard string sanitizer, lists 28 advisories, all Low; ten shown span 2026-05-29 to 2026-10-12 and mostly concern `IN_PLACE`, `SAFE_FOR_TEMPLATES`, hooks and `CUSTOM_ELEMENT_HANDLING`; latest release 3.4.17 (2026-10-12). The app does not use DOMPurify (`web/package.json` lists only fontsource, katex, markdown-it and mathlive as runtime dependencies) — [DOMPurify advisories](https://github.com/cure53/DOMPurify/security/advisories); [npm: dompurify](https://registry.npmjs.org/dompurify); [web/package.json](/web/package.json)
- MathLive 0.111.1 (2026-10-09) fixed three XSS issues in LaTeX-to-markup output (`\enclose` shadow attribute, `\htmlData`/`\href` quote handling, MathML `\enclose` notation names) and hardened CSS values taken from LaTeX; the changelog says "input-side HTML sanitizers did not catch it" and "no HTML in the input was needed" — [MathLive changelog](https://raw.githubusercontent.com/arnog/mathlive/master/CHANGELOG.md)
- Markdown path: `markdown-it` runs with `html: false, linkify: false` and the module builds DOM nodes from tokens with fixed tag names; images resolve only through `resolveImage` and any scheme is refused — [web/src/lib/markdown.ts](/web/src/lib/markdown.ts)
- Bridge reachability: see section 1 (no token or frame check in 6.2.1; dispatcher accepts any reachable name; the API is re-injected after every navigation; no navigation policy or drop handling in the app).

### Inferences
- **Sanitizer vs sandboxed iframe vs separate origin.** A sandboxed iframe is blocked by the app's own `frame-src 'none'`, and a separate-origin server would only add a port; neither is needed while the content never becomes an HTML string. Rebuilding from an allow-list with `createElement` removes the mutation-XSS class that drives most string-sanitizer advisories, so it is the better choice here. Keep `tests/app/test_anki_allowlist.py`, which stops the two sanitizers drifting apart.
- **Most likely residual weaknesses**, in order: (1) the unauthenticated 6.2.1 bridge plus the dispatcher's unfiltered name resolution if any script ever runs (section 1); (2) an accidental navigation via drag-and-drop, which hands a foreign page the re-injected bridge; (3) `style-src 'unsafe-inline'` (required by KaTeX and MathLive) leaving CSS as a layout-spoofing channel inside a card box, mitigated by `contain: layout`, the img/font/connect `'self'` rules and the zero-specificity defaults; (4) the media route as a same-origin file server for the open profile's store, mitigated by content-addressed names, `nosniff` and the type table.
- **Add negative tests** that send `_close`, `__setattr__` and an unknown name through the real dispatcher, that post from a second frame (if one can be created in the Playwright harness), and that drop a file on the window.
- **Confirm on the Mac** that `[sound:...]` playback works with the media route's byte ranges (ADR-0017 says not yet confirmed), and that an SVG opened directly as a document runs nothing (the `sandbox` CSP is designed for it).

### Gaps
- Anki-HTML CVE precedents and real-world bypasses against DOM-reconstruction sanitizers (search budget exhausted).
- Field reports on message-handler exposure from subframes.
- Whether WKWebView enforces a `<meta>` CSP on dropped-file navigations (it would not apply: the new document has no meta).
- Whether the HTML Sanitizer API ships in Safari 26 (the MDN compatibility table could not be read).

## 6. MathLive and KaTeX (ADR-0005): maintenance, licences, advisories, accessibility and WKWebView quirks

### Takeaway
Both are healthy, MIT-licensed and pinned at their latest versions (MathLive 0.111.4, KaTeX 0.19.1). MathLive's security fixes in 0.111.1 and 0.111.2 are directly relevant and justify the `>=0.111.1` floor; 0.111.0 removed MathJSON output, which confirms ADR-0005's choice to take LaTeX and lower it with the app's own grammar. The strict CSP is what makes MathLive's XSS history survivable.

### Cited Findings
- MathLive releases: 0.109.0 (2026-03-11), 0.109.1 (2026-04-01), 0.109.2 (2026-04-29), 0.110.0 (2026-06-09), 0.111.0 (2026-09-30), 0.111.1 (2026-10-09), then 0.111.2, 0.111.3 and 0.111.4 all on 2026-10-31; MIT. The master changelog's newest entry is 0.111.2, so what 0.111.3 and 0.111.4 changed was not established — [npm: mathlive](https://registry.npmjs.org/mathlive); [MathLive changelog](https://raw.githubusercontent.com/arnog/mathlive/master/CHANGELOG.md)
- 0.111.0 removed `mathfield.expression` and the `"math-json"` output, changed `<math-field>` to role `group` with an accessible name on the inner textbox, and fixed Safari/Firefox focus-removal handling (the lost last edit when a focused field is removed from the DOM) — [MathLive changelog](https://raw.githubusercontent.com/arnog/mathlive/master/CHANGELOG.md)
- 0.111.1 fixed the three XSS issues quoted in section 5 and notes they are "the same class of issue as GHSA-qwj6-q94f-8425 and GHSA-fm7p-gw32-828p"; 0.111.2 made virtual-keyboard, proxy and mathfield messages default to same-origin validation, bound state-changing messages to the connected window, and stopped treating opaque `"null"` origins as equal — [MathLive changelog](https://raw.githubusercontent.com/arnog/mathlive/master/CHANGELOG.md)
- KaTeX: latest 0.19.1 (2026-10-23); recent releases 0.18.8 and 0.18.9 (2026-09-23), 0.18.10 (2026-09-30), 0.18.11 and 0.19.0 (2026-10-01); MIT — [npm: katex](https://registry.npmjs.org/katex)
- KaTeX advisories: five, all Moderate. The newest is GHSA-cg87-wmx4-v546 (`\htmlData` attribute names, 2025-01-17); four date from 2024-03-24 (`\includegraphics`, `\edef` maxExpand, URL protocol normalization, Unicode sub/superscript maxExpand). None in 2026 — [KaTeX advisories](https://github.com/KaTeX/KaTeX/security/advisories)
- The repo pins `katex` 0.19.1 and `mathlive` 0.111.4 and renders card math with `trust: false` — [web/package.json](/web/package.json); [web/src/lib/markdown.ts](/web/src/lib/markdown.ts)
- Spec text still says MathLive "outputs MathJSON" (MATH-4) and calls the SymPy parsing CVE "critical" (MATH-8), while ADR-0005 supersedes MATH-4 — [docs/spec.md](/docs/spec.md); [ADR-0005](/docs/decisions/0005-math-input-path.md)
- Earlier note: both libraries support Safari, must be self-hosted with fonts reachable, and MathLive should be served from an http origin because of origin validation — [mac_stack_tooling.md](/home/claude/research_notes/Toishi gaps research/mac_stack_tooling.md)
- Mac hand test: typing, Cmd+Z and Shift+Cmd+Z work in the math field; paste and dead keys not yet checked — [docs/backlog.md](/docs/backlog.md)

### Inferences
- **Treat MathLive as security-churning:** two security releases in October 2026 (0.111.1 on 2026-10-09 and 0.111.2 on 2026-10-31), and 0.111.3 and 0.111.4 followed on the same day as 0.111.2 with no changelog entry yet on master. Keep it pinned exactly, read each changelog before bumping, and re-run the answer-fixture tests on every bump (ADR-0005 already lowers LaTeX through the app's own grammar, so MathLive version changes should not change grading).
- **Update the spec text** for MATH-4 and MATH-8 so agents do not rebuild on MathJSON or repeat the "critical CVE" claim (see section 7).
- **Accessibility:** the 0.111.0 role and name changes are a plus; whether keyboard-only and VoiceOver use of the field meets the spec's WCAG goals needs a hand test, because the changelog is the only evidence.

### Gaps
- KaTeX accessibility output in practice (MathML alongside HTML) was not verified against the docs.
- MathLive IME and dead-key behaviour inside WKWebView on macOS 26.
- Whether MathLive's virtual keyboard is disabled in the app (it adds cross-window messaging).
- What MathLive 0.111.3 and 0.111.4 (both 2026-10-31) changed; the master changelog stops at 0.111.2.

## 7. SymPy safety and performance (ADR-0003, ADR-0007): the 2026 parse_expr CVE, worker isolation, timeouts, and Lark maintenance

### Takeaway
The "2026 critical CVE" cited by the spec is real but is in a third-party package (`qwed`), not in SymPy, and the app's no-eval grammar plus a killable spawn worker is the correct defence class. The live concern is SymPy's staleness: no release since 1.14.0 (2025-04-27) and an `mpmath<1.4` cap that forces the pinned mpmath 1.3.0.

### Cited Findings
- CVE-2026-55585 (OSV, published 2026-08-25) affects the `qwed` package, fixed in 5.1.2; the flaw is unsafe `parse_expr()` in a verification API. The CVSS vector computes to 8.8 (High) by my arithmetic, not "critical" — [OSV CVE-2026-55585](https://api.osv.dev/v1/vulns/CVE-2026-55585)
- SymPy has no published GitHub security advisories — [SymPy advisories](https://github.com/sympy/sympy/security/advisories)
- SymPy 1.14.0 (2025-04-27) is still the latest release, about 18 months old; it requires `mpmath<1.4,>=1.1.0`. Master is `1.15.0.dev`, requires `mpmath >= 1.1.0` and Python 3.10 or newer — [PyPI: sympy 1.14.0](https://pypi.org/pypi/sympy/1.14.0/json); [SymPy release.py](https://raw.githubusercontent.com/sympy/sympy/master/sympy/release.py); [SymPy pyproject](https://raw.githubusercontent.com/sympy/sympy/master/pyproject.toml)
- mpmath: 1.4.0 (2026-02-23), 1.4.1 (2026-03-15), then alphas 1.5.0a0 (2026-06-24), a1 (2026-08-21) and a2 (2026-10-30) — [PyPI: mpmath](https://pypi.org/pypi/mpmath/json)
- ADR-0001 records the mpmath 1.3.0 pin as forced by SymPy's `<1.4` cap ("uv cannot resolve 1.4.1") — [ADR-0001](/docs/decisions/0001-stack-and-shell-spike.md)
- Pyodide's package list pairs sympy 1.14.0 with mpmath 1.4.1, despite the cap — [Pyodide packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)
- Lark 1.3.1 (2025-10-27) and 1.3.0 (2025-09-22), MIT, about one release a year — [PyPI: lark](https://pypi.org/pypi/lark/json)
- The grader: reusable worker from `multiprocessing.get_context("spawn")`, a 2 s hard kill that yields an "undecidable" verdict, `SIGALRM` inside the worker, the app process never imports SymPy, `multiprocessing.freeze_support()` in `app/__main__.py`; ADR-0003 forbids evaluating user input and the spec bans `parse_expr` — [core/grader/worker.py](/core/grader/worker.py); [core/grader/symbolic.py](/core/grader/symbolic.py); [ADR-0003](/docs/decisions/0003-no-eval-of-user-input.md); [docs/spec.md](/docs/spec.md)
- An open backlog item: the CAS worker must not fork while holding the profile lock (use spawn) — [docs/backlog.md](/docs/backlog.md)

### Inferences
- **Isolation design is right and portable on macOS and Windows,** but not to iOS (section 2). The kill-on-timeout pattern is the only reliable way to stop a runaway SymPy call.
- **Correct the spec wording:** the CVE was in `qwed`, not SymPy, and is High by the vector. The lesson (never `eval`/`parse_expr` untrusted text) stands.
- **SymPy staleness** is a slow risk: Python 3.15 or a new mpmath could break 1.14.0 before a 1.15 release arrives. Re-check SymPy master's release status before any Python or mpmath bump, and do not chase mpmath 1.4.x by loosening the pin by hand; Pyodide's pairing hints the cap may be overcautious, but nothing here shows it works with the whole grader test suite.
- **Performance** (import time, cold-start of the worker, per-check latency) was not measured here; the repo's launch figure (478 ms) excludes the worker.

### Gaps
- SymPy import time and per-check latency on the Mac.
- Whether SymPy 1.14.0 runs the repo's grader tests with mpmath 1.4.1.
- Lark grammar-size or performance concerns (nothing found, nothing searched deeply).

## 8. FSRS packages and licence (ADR-0006, ADR-0013, ADR-0014, ADR-0016): py-fsrs, fsrs-rs-python, FSRS-7, fitting alternatives

### Takeaway
Scheduling on py-fsrs 6.3.2 (MIT, FSRS-6) is sound. The fitting dependency `fsrs-rs-python` 0.9.3 has no licence at all, must be replaced or licensed before any distribution, can raise a Rust panic that Python's `except Exception` does not catch, and will change its default parameter vector the moment its upstream crate releases FSRS-7. FSRS-7 exists only on fsrs-rs `main`; no released package ships it.

### Cited Findings
- Licence of `fsrs-rs-python`: the repo's `LICENSE` returns 404, `Cargo.toml` has no `license` field, PyPI license metadata is empty (`license` and `license_expression` both None) — [LICENSE (404)](https://raw.githubusercontent.com/open-spaced-repetition/fsrs-rs-python/main/LICENSE); [Cargo.toml](https://raw.githubusercontent.com/open-spaced-repetition/fsrs-rs-python/main/Cargo.toml); [PyPI: fsrs-rs-python 0.9.3](https://pypi.org/pypi/fsrs-rs-python/0.9.3/json)
- Project status: 0.9.3 published 2026-08-31, 37 stars, 2 forks, 69 commits, 2 open issues, 2 open PRs, no GitHub releases; depends on `fsrs` 6.6.2, `pyo3` 0.29.0 and `macerator` 0.3.3; wheels are built per Python version (no abi3; 104 files), including `cp314-macosx_11_0_arm64` at 508,981 bytes; the sdist is about 20 KB — [GitHub: fsrs-rs-python](https://github.com/open-spaced-repetition/fsrs-rs-python); [Cargo.toml](https://raw.githubusercontent.com/open-spaced-repetition/fsrs-rs-python/main/Cargo.toml); [PyPI: fsrs-rs-python 0.9.3](https://pypi.org/pypi/fsrs-rs-python/0.9.3/json)
- The upstream crate `fsrs` is BSD-3-Clause. Releases: 6.6.2 (2026-08-29), 6.6.1 (2026-06-09), 6.6.0 (2026-06-06), 6.5.0 (2026-06-05), 6.4.x (2026-06-04), 6.3.0 and 6.2.0 (2026-06-04), 6.1.0 (2026-06-01), 6.0.0 (2026-05-29), 5.2.0 (2025-09-17), 5.0.0 (2025-07-24) — [crates.io: fsrs](https://crates.io/api/v1/crates/fsrs)
- The fsrs 6.6.2 crate has `pub static DEFAULT_PARAMETERS: [f32; 21]` and no FSRS-7 code (a grep for FSRS-7 terms returns nothing) — [fsrs-6.6.2.crate](https://static.crates.io/crates/fsrs/fsrs-6.6.2.crate)
- fsrs-rs `main` has `pub use inference_v7::DEFAULT_PARAMETERS`, `ComputeParametersVersion::{Fsrs6 (21), Fsrs7 (34)}`, `MemoryState.stability_fast` and a retained `FSRS6_DEFAULT_PARAMETERS`. PR #426 ("FSRS7 + ADR + Optimization") showed as open in the snapshot while Hackage says it was upstreamed; the merge date is unknown — [fsrs-rs inference.rs (main)](https://raw.githubusercontent.com/open-spaced-repetition/fsrs-rs/main/src/inference.rs); [fsrs-rs PR #426](https://github.com/open-spaced-repetition/fsrs-rs/pull/426); [fsrs-rs CHANGELOG](https://raw.githubusercontent.com/open-spaced-repetition/fsrs-rs/main/CHANGELOG.md)
- A third-party implementation, `haskell-fsrs` 7.1.0 (2026-08-21, MIT), describes FSRS-7: 34 weights, two memory traces, a mixture of two power laws as the forgetting curve (no closed-form inverse, so intervals need root-finding), forgetting that depends on difficulty, post-lapse stability independent of difficulty, and continuous intervals; its reference is `Expertium/fsrs-rs-speed-autoresearch` — [Hackage: haskell-fsrs](https://hackage-content.haskell.org/package/haskell-fsrs)
- Anki 26.05 (2026-06-16) and 26.08 (2026-08-01) release notes do not mention FSRS-7; 26.08 uses fsrs-rs 6.6.1 and raises the minimum macOS to 13.0 — [Anki 26.05](https://github.com/ankitects/anki/releases/tag/26.05); [Anki 26.08](https://github.com/ankitects/anki/releases/tag/26.08)
- The awesome-fsrs "The Algorithm" page documents FSRS-6 (21 parameters) as the newest published specification — [awesome-fsrs: The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)
- py-fsrs 6.3.2 (2026-08-09, MIT) implements FSRS-6 with 21 parameters; its optimizer extra needs torch, numpy, pandas and tqdm — [PyPI: fsrs](https://pypi.org/pypi/fsrs/6.3.2/json); [py-fsrs pyproject](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/pyproject.toml); [py-fsrs README](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/main/README.md)
- `fsrs-optimizer` 6.5.0 (2026-02-02) requires Python `<3.14,>=3.11`, so it cannot be installed with the app's Python — [PyPI: fsrs-optimizer](https://pypi.org/pypi/fsrs-optimizer/json)
- Experiment (Linux, Python 3.13, `fsrs-rs-python==0.9.3` with `fsrs==6.3.2`): `len(rs.DEFAULT_PARAMETERS)` is 21 and equals py-fsrs's defaults (first six 0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334); `compute_parameters` on valid items returns 21 values; an item with no `delta_t > 0` review panics inside the crate ("Invalid FSRS item: at least one review with delta_t > 0 is required", `dataset.rs:96`) and surfaces as `PanicException`, whose MRO is `PanicException, BaseException, object`, so `isinstance(e, Exception)` is False and `pyo3_runtime` cannot be imported to catch it by name — [fsrs-6.6.2.crate](https://static.crates.io/crates/fsrs/fsrs-6.6.2.crate) (local experiment)
- The repo catches only `ParameterError` around the Rust call and keeps a `fitter()` seam "for tests and FSRS-7" — [core/engine/fitting.py](/core/engine/fitting.py). Open backlog item: "fsrs-rs-python must be replaced or licensed before any public release" — [docs/backlog.md](/docs/backlog.md)

### Inferences
- **Licence:** with no licence text, default copyright applies, so redistributing the wheel inside an app is not permitted without the author's permission, and the fact that the code is public does not change that. Options in order of effort: (1) open an issue or PR asking the `open-spaced-repetition` maintainers to add BSD-3-Clause to match the crate (not checked whether such an issue exists); (2) write a thin PyO3/maturin binding over the BSD-3-Clause `fsrs` crate (the Python surface the app needs is small: `compute_parameters`, `DEFAULT_PARAMETERS`, a training config); (3) ship without fitting and keep default parameters. Until one of these lands, treat the app as personal-use only.
- **Panic handling:** wrap the fit in `except BaseException` (re-raising `KeyboardInterrupt` and `SystemExit`), and validate items (at least one review with `delta_t > 0`) before the Rust call. A `PanicException` escaping the bridge thread would skip pywebview's `except Exception` and leave the page's promise unresolved; in the auto-fit thread it kills the thread without recording `last_auto_fit`. This is a cheap hardening item.
- **FSRS-7 drift:** when fsrs-rs releases FSRS-7, a bump of `fsrs-rs-python` could change `DEFAULT_PARAMETERS` to 34 values while py-fsrs keeps scheduling with FSRS-6. Add a test asserting `len(rs.DEFAULT_PARAMETERS) == 21` and pin the wheel exactly (already pinned at 0.9.3).
- **FSRS-7 fit with the current design:** continuous intervals and a non-closed-form forgetting curve conflict with ADR-0013's single "whole study days" clock and with py-fsrs's interface, and the fitted parameters are version-specific. The `fitter()` seam is the right place; do not adopt FSRS-7 until a released package and a published spec exist.
- **Fitting alternatives** are weak: the Python optimizer needs torch and an unsupported Python; the pure-Python py-fsrs optimizer path pulls a large ML stack. The Rust binding remains the right architecture, just with a licence fix.

### Gaps
- The two open issues and PRs on fsrs-rs-python (GitHub API blocked); whether a licence request already exists.
- When PR #426 merged and when fsrs-rs will cut a release with FSRS-7.
- Benchmarks comparing FSRS-6 and FSRS-7 on this app's kind of data (nothing found).
- Time to fit and memory use on the Mac (only Linux was run).

## 9. Local-first data: export formats, migration and profile portability (ADR-0003, ADR-0004, ADR-0011, ADR-0015)

### Takeaway
The data design (read-only packs, one `user.db` per profile, append-only logs, forward-only migrations, content-addressed media, automatic backups, plain-text exports) is a sound local-first design with no change needed beyond the SQLite floor and an export-format check. The importer's own-reader choice is correct; the main portability risks are future FSRS-7 presets in imported decks and a hand-written protobuf reader.

### Cited Findings
- Spec: EXP-1 card files, EXP-2 a `.meprofile` export, EXP-3 a CSV review-log export, EXP-4 an optional daily summary; BAK-1 to BAK-6 for backups; DATA-1 to DATA-5 for storage rules — [docs/spec.md](/docs/spec.md)
- ADR-0004 and ADR-0011: read-only pack databases plus one `user.db` per profile; schema v2 gave four v1 stop-gaps real homes; a content-addressed media store; `SchemaTooNewError` stops an older app from opening a newer profile — [ADR-0004](/docs/decisions/0004-data-layout.md); [ADR-0011](/docs/decisions/0011-storage-schema-v2.md); [app/api.py](/app/api.py)
- ADR-0015: the importer is the app's own reader and renderer; the `anki` package (AGPL, `anki==26.9.3`) is a dev-only test oracle; the protobuf media map is read by a hand-written reader; `.apkg` zstd streams are read with the third-party `zstandard` package — [ADR-0015](/docs/decisions/0015-anki-import.md); [pyproject.toml](/pyproject.toml); [core/importers/anki/package.py](/core/importers/anki/package.py)
- Anki 26.08 uses fsrs-rs 6.6.1, so current Anki decks carry FSRS-6 parameters — [Anki 26.08](https://github.com/ankitects/anki/releases/tag/26.08)
- The earlier notes recommend `PRAGMA user_version` with forward-only migrations, app-level snapshots rather than copying a live file, and never placing the live database in iCloud or Dropbox — [desktop_app_engineering.md](/home/claude/research_notes/Toishi build research/desktop_app_engineering.md); [mac_stack_tooling.md](/home/claude/research_notes/Toishi gaps research/mac_stack_tooling.md)

### Inferences
- **Export formats are the owner's escape hatch,** so EXP-3's CSV should use documented column names and a version header; if the Open Spaced Repetition community's review-log CSV is the target, compare against its column list (not verified here).
- **Profile portability** (`.meprofile`) should carry the schema version and be restored through the same migration path as a live open, with the backup API output as the source (never a raw file copy); BAK-6's cloud-sync warning is the right guard.
- **FSRS-7 presets:** a future Anki deck or collection may carry 34-parameter presets. The importer should read the parameter count and refuse or ignore a vector whose length is not 21, rather than silently truncating or padding it.
- **Hand-written protobuf reader:** keep it fuzzed (the package tests already include damaged zstd and decompression-budget cases) and keep the AGPL oracle dev-only.

### Gaps
- The Open Spaced Repetition review-log CSV column specification.
- Anki's `.apkg`/`.colpkg` format documentation was not re-read for format drift in 26.x.
- Whether `.meprofile` round-trips media and the append-only log losslessly (not tested here).

## 10. Verdict for each ADR (0001 to 0018): sound, sound with risks, or should change

### Takeaway
Fifteen decisions stand as written or with small additions; two need action before anyone besides the owner uses the app (packaging and signing in ADR-0001, the unlicensed fitting package in ADR-0013/0016). No decision needs reversing and the pywebview choice is confirmed, provided the bridge hardening in section 1 is done.

### Cited Findings
- ADR set, titles and status as reviewed: 0001 Stack and shell spike; 0002 Offline and CSP; 0003 No eval of user input; 0004 Data layout; 0005 Math input path; 0006 Learning engine core; 0007 Answer checker review; 0008 Error diagnosis; 0009 Daily queue; 0010 Card kinds and practice tests; 0011 Storage schema v2; 0012 Bridge and app integration; 0013 FSRS fitting, clock and memory; 0014 Honest grading and queue parity; 0015 Anki import; 0016 Integrating fitting, grading and import; 0017 Card media and imported HTML; 0018 Hand-test fixes — [docs/decisions](/docs/decisions)
- Evidence for each row is in sections 1 to 9 above; this section contains judgments.

### Inferences
| ADR | Decision | Verdict | Recommendation |
|---|---|---|---|
| 0001 | Python 3.14 + uv, pywebview shell with PySide6 fallback, pinned stack | Sound with risks | Keep. Do the section 1 hardening; re-verify patches on any pywebview/PyObjC bump; mark the "PyInstaller with uv Python unverified" caveat resolved (Mac build passes). Tool pins are current: katex 0.19.1, mathlive 0.111.4, svelte 5.57.3 and vite 8.3.5 are latest; svelte-check 4.7.8 and TypeScript 7.0.2 exist but TypeScript is held back by svelte-check, and playwright 1.64.1 exists but is held back by the workspace's Chromium build. |
| 0001 (packaging) | PyInstaller onedir, arm64, ad-hoc signed | Sound for a single developer Mac; should change before distribution | Decide the distribution route (section 3). Run a notarization spike. Keep arm64-only and onedir. |
| 0002 | Offline, loopback server, strict CSP, tripwires, two eval-free pywebview patches | Sound with risks | Add navigation policy, `ALLOW_FILE_URLS=False`, drop handlers, a Host check, and a frame/origin check on the script-message handler. The ADR's `/js_api` note is confirmed (the route is inert in 6.2.1). Consider a `WKContentRuleList`. |
| 0003 | Nothing typed is ever evaluated | Sound | Keep. Correct the spec: the CVE was in `qwed`, not SymPy. |
| 0004 | Read-only packs + one `user.db` per profile | Sound | Keep. See ADR-0011 for SQLite items. |
| 0005 | MathLive answers reach the checker as LaTeX | Sound | Validated by MathLive 0.111.0 removing MathJSON. Pin MathLive at 0.111.1 or later (now 0.111.4), re-run fixtures on every bump, fix spec MATH-4. |
| 0006 | Scheduling core on py-fsrs | Sound with risks | FSRS-6 only; keep the adapter seam; add `len(DEFAULT_PARAMETERS) == 21` guard. |
| 0007 | Answer checker review (SymPy, forms, precision) | Sound with risks | Keep worker isolation. Track SymPy master for a 1.15 release; do not loosen the mpmath pin by hand. |
| 0008 | Error diagnosis | Sound | Domain logic; nothing in this review's evidence changes it. |
| 0009 | Daily queue and sessions | Sound | Same. |
| 0010 | Card kinds and practice tests | Sound | Same. |
| 0011 | Storage schema v2 | Sound with risks | Raise the SQLite floor to 3.51.3 or the 3.44.6/3.50.7 backports; measure F_FULLFSYNC per commit on the Mac; keep the integrity check and backup API. |
| 0012 | Thin bridge, locked calls, real-data tests | Sound with risks | Add the dispatcher allow-list and a negative test; the thin-bridge claim is true only for stubs today. Keep the Edit-menu patch under the version check. |
| 0013 | FSRS fitting, one clock, memory from the log | Should change before distribution | Resolve the `fsrs-rs-python` licence (ask, or write own binding); catch `BaseException` and validate items; keep the `fitter()` seam; note FSRS-7's continuous intervals will not fit a whole-day clock. |
| 0014 | Honest grading paths, queue parity with Anki | Sound | Domain logic; Anki 26.08 still uses FSRS-6, so parity holds. |
| 0015 | Own Anki reader and renderer; `anki` only as a dev oracle | Sound with risks | Keep. Reject non-21-length FSRS parameter vectors from imports; keep fuzzing the protobuf and zstd readers; consider stdlib `compression.zstd`. |
| 0016 | Integrating fitting, grading and import | Should change before distribution | Same licence blocker as ADR-0013. Otherwise sound. |
| 0017 | Media from the app's origin; second sanitizer | Sound with risks | Add a Host check and a dispatcher allow-list; confirm audio ranges and SVG-as-document on the Mac. |
| 0018 | Hand-test fixes (close-vs-read lock, study-flow fixes) | Sound | Keep; the reader lock plus 30 s wait is a reasonable fix for the sqlite3 use-after-free. |

### Gaps
- ADR-0008, 0009, 0010 and 0014 are product and scheduling-logic decisions, not technology choices; this review did not evaluate their learning-science merits.
- No ADR was re-tested by running the full suite here.

## 11. Top architectural risks for 1.0 (one student, one Mac) and for later distribution

### Takeaway
For 1.0 the real risks are small and fixable: bridge hardening, a SQLite version guard plus one measurement, Rust-panic handling, and a Mac manual-test checklist. For distribution the blockers are structural: no licence on the fitting package, no Developer ID or notarization (and a stated no-spend rule), and, if a Windows or iPad version is ever wanted, the Cocoa-specific shell and the process-based grader.

### Cited Findings
- Evidence summary with pointers: pywebview cadence (200 days, 2 releases in 2026) and the 6.2.1 bridge behaviour — section 1; Homebrew's 2026-09-01 cutoff and macOS 27 dropping Intel — section 3; SQLite's WAL-reset bug and the 3.37 floor — section 4; MathLive's October 2026 security releases — sections 5 and 6; SymPy's 18-month gap — section 7; `fsrs-rs-python`'s missing licence and panic type — section 8; Python-on-iOS limits — section 2.

### Inferences
**Top risks for 1.0, ranked by (damage if it happens) times (likelihood) over effort to fix**
1. **Unauthenticated, over-broad bridge dispatcher.** Any script in an app frame can call private and dunder `Api` members (verified). Fix: allow-list in `app/shell.py` plus a test (about 30 minutes). Add a frame/origin check (needs a Mac test).
2. **Unguarded navigation and drops.** No navigation policy, no drop handler, `ALLOW_FILE_URLS` true; a dropped HTML file or link could load a foreign page that receives the re-injected bridge. Fix: three small changes (about an hour) and one manual test.
3. **SQLite below the WAL-reset fix is accepted silently, and F_FULLFSYNC cost is unmeasured.** Fix: a version check and a timing script (about an hour). Data loss would be the most damaging failure for this app.
4. **A Rust panic is not caught by `except Exception`.** Fix: validate items and catch `BaseException` around fits (about 30 minutes).
5. **Unfinished Mac manual testing:** paste, dead keys, alert beep, audio ranges, printing, file drop. Cheap, high information; the hand test on macOS 26.6.2 covered only part of the checklist.
6. **pywebview drift.** A release that adds the token and rewrites `api.js` will break the exact-text patches (loudly). macOS 27 compatibility is unproven. Mitigation: keep the pins, the version check, the self-test and the tested Qt fallback.
7. **SymPy and mpmath staleness; MathLive security churn.** Slow risks; pin, read changelogs, re-run fixtures.

**Top risks for later distribution**
1. **`fsrs-rs-python` has no licence.** Hard blocker for any redistribution. Ask the maintainers for BSD-3-Clause or write a binding over the BSD-3-Clause `fsrs` crate.
2. **Gatekeeper.** Ad-hoc signing is fine only on the Mac that built the app. Others face Open Anyway friction, Homebrew cask is closed to unsigned apps since 2026-09-01, and notarization costs $99/yr, which conflicts with the stated no-spend rule. Decide among paying, a build-from-source route, or accepting the friction; run a notarization spike first to learn the entitlements.
3. **Content licensing.** The brief says shipped packs will hold only open-source problems; any pack under a share-alike or non-commercial licence needs checking before it ships (see the earlier content-licensing notes).
4. **Security exposure rises when strangers' decks and packs are imported.** Everything in section 5 becomes load-bearing; add the negative tests and consider a native `WKContentRuleList` and the frame/origin check before releasing.
5. **No update channel or compatibility story for a changing macOS and WebKit.** pywebview's cadence and the system WebView mean each macOS release can change behaviour; keep an `.app` self-test in the release gate and a documented minimum macOS.
6. **Windows or iPad.** Windows is feasible with the same Python and web code and a new shell adapter; iPad is a re-architecture (no subprocess or multiprocessing, iOS wheels for compiled dependencies, a different packager). Keep `core/` GUI-free and the shell behind its seam; do not design for either yet.

**Do first (ordered):** dispatcher allow-list and test; navigation policy, drop handler and `ALLOW_FILE_URLS`; SQLite floor; F_FULLFSYNC timing; `BaseException` around fits; the Mac manual checklist; then the licence request for `fsrs-rs-python`; then the notarization spike.

### Gaps
- Probabilities and effort figures above are judgments from the evidence, not measured.
- No source could be found for how often unsigned Python `.app` bundles are blocked in practice on macOS 26 or 27.
- Distribution to other platforms, an update mechanism and crash reporting were not researched beyond the earlier notes.
