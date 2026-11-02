# Engineering a Local, Fully Offline, Anki-Style Desktop App in Python + Qt (PySide6) for Spaced-Repetition Math Practice — notes current to 1 Nov 2026

Scope reminder: these notes cover architecture, the UI toolkit, math rendering and input, answer checking, packaging and signing, data design, problem rendering, a later C++ coding environment, and maintainability. Version numbers and dates are what the cited pages showed when fetched on 2026-11-01. Anything marked "(unverified)" or "(general knowledge)" in Inferences was not confirmed by a source this session and should be checked before relying on it.

---

## 1. How is Anki's desktop app built today, and what lessons apply to a smaller app?

### Takeaway
Anki has three layers: a Rust core (`rslib`) that holds almost all logic, a thin Python library (`pylib`, importable as `anki`) that forwards calls over protobuf, and a PyQt GUI (`aqt`). Its screens are mostly Svelte/TypeScript pages served from a localhost Flask/Waitress server into QtWebEngine and bridged with QWebChannel. Math renders with bundled MathJax, and user data lives in one SQLite collection file per profile, with a media folder and rolling automatic backups. The lessons that carry over to a smaller app: separate the core from the GUI, render web UI from local assets only, treat user-supplied HTML as untrusted, keep one SQLite file for user data, back it up automatically, and never let content updates touch it.

### Cited Findings
**Layering**
- Anki is split into a library layer and a GUI layer. "The majority of backend logic now lives in a Rust library in `rslib/`." Python code in pylib forwards requests to it — [Anki docs/architecture.md](https://github.com/ankitects/anki/blob/main/docs/architecture.md)
- pylib is the `anki` Python package, and command-line programs can use it without the GUI. Its private `rsbridge` module wraps the Rust code — [Anki architecture.md](https://github.com/ankitects/anki/blob/main/docs/architecture.md)
- Protocol Buffers in `proto/anki/` define backend methods and pass data between Python, Rust and some TypeScript code, giving type-safe calls across languages. The protobufs are not a public API — [Anki architecture.md](https://github.com/ankitects/anki/blob/main/docs/architecture.md)
- The GUI is Qt (via PyQt) mixed with TypeScript/HTML/CSS. Qt code is in `qt/aqt/`. New web code goes in `ts/` and is copied into `qt/aqt/data/web/` at build time — [Anki architecture.md](https://github.com/ankitects/anki/blob/main/docs/architecture.md)
- Anki's `package.json` lists Svelte `^5.56.9`, `@sveltejs/kit ^2.70.3` with `adapter-static`, Vite 6, `mathjax ^3.1.2`, `codemirror ^5.63.1`, `@bufbuild/protobuf`, Bootstrap 5.3, and d3 7. Its tests use `vitest ^3` and `@playwright/test ^1.62.1` — [Anki package.json](https://raw.githubusercontent.com/ankitects/anki/main/package.json)

**How web UI reaches QtWebEngine**
- `mediasrv.py` runs a Flask app served by Waitress. It binds to `ANKI_API_HOST` (default `127.0.0.1`) on port `0`, so the OS picks a free port. Requests whose Host or Origin is not localhost get a 403 — [Anki mediasrv.py](https://github.com/ankitects/anki/blob/main/qt/aqt/mediasrv.py)
- User media is served with an `UNTRUSTED_MEDIA_CSP` beginning `default-src 'none'` with `sandbox allow-same-origin`. A code comment warns "Never add allow-scripts". `ensure_safe_path` rejects path traversal. A `/_anki/readyz` endpoint exists for the end-to-end test harness — [Anki mediasrv.py](https://github.com/ankitects/anki/blob/main/qt/aqt/mediasrv.py)
- Page-to-backend calls are POSTs whose bodies are protobuf (`ParseFromString`). Handlers that touch the UI run on the Qt main thread via `aqt.mw.taskman.run_on_main(...)` — [Anki mediasrv.py](https://github.com/ankitects/anki/blob/main/qt/aqt/mediasrv.py)
- `webview.py` injects `qwebchannel.js` and registers a Python `Bridge(QObject)` as `"py"`. JavaScript calls `channel.objects.py.cmd(arg, resultCB)` through `pycmd`/`bridgeCommand`. TypeScript pages load from `http://127.0.0.1:{port}/_anki/pages/<name>.html`. In HMR mode, SvelteKit pages load from a Vite dev server at `127.0.0.1:5173` — [Anki webview.py](https://github.com/ankitects/anki/blob/main/qt/aqt/webview.py)
- External links can be sent to the system browser through `acceptNavigationRequest` — [Anki webview.py](https://github.com/ankitects/anki/blob/main/qt/aqt/webview.py)

**Math rendering**
- "Anki's bundled MathJax support is loaded before card content." It works out of the box and "does not require the installation of any extra software". Syntax is `\(...\)` for inline and `\[...\]` for display — [Anki manual: Math](https://docs.ankiweb.net/math.html)
- Anki's optional LaTeX-to-image mode needs a local LaTeX install plus dvipng. The manual warns that with shared decks "you are potentially giving any shared deck author access to your computer" — [Anki manual: Math](https://docs.ankiweb.net/math.html)

**Data, profiles, backups**
- Data lives in `%APPDATA%\Anki2` (Windows), `~/Library/Application Support/Anki2` (macOS), and `~/.local/share/Anki2` or `$XDG_DATA_HOME/Anki2` (Linux). Program-level preferences are in `prefs.db`. Each profile folder holds `collection.anki2` (SQLite), `collection.media/` and a backups folder — [Anki manual: Files](https://docs.ankiweb.net/files.html)
- Warnings in the manual: "You should never copy or move your collection while Anki is open." "We do not recommend you sync your Anki folder directly with a third-party synchronization service." Store files on a local disk, because network filesystems can cause corruption — [Anki manual: Files](https://docs.ankiweb.net/files.html)
- Automatic backups run every 30 minutes by default, and some risky operations trigger one early (import, Check Database, one-way sync). Users choose how many daily, weekly and monthly backups to keep. Backups "do not include sounds or image files". Restoring goes through File > Switch Profile > Open Backup — [Anki manual: Backups](https://docs.ankiweb.net/backups.html)

**Current release and packaging (2026)**
- Latest stable is 26.08.1 (5 Aug 2026), with betas 26.09b1/b2 out in Aug–Sep 2026. 26.05 updated Qt to 6.11. macOS builds need macOS 13+. Official builds ship Python 3.13, and the minimum Python is 3.10. Windows uses an MSI installer, and there is a Windows ARM64 build — [Anki releases](https://github.com/ankitects/anki/releases)
- 26.05 "replaces the terminal-based launcher introduced in 25.07", and 26.08 includes "Remove the uv launcher and old packaging code". 26.05+ updates itself via Tools > Check for Updates — [Anki releases](https://github.com/ankitects/anki/releases)

### Inferences
- **Keep a GUI-free core package.** Anki keeps its logic in a library that runs without a GUI. The smaller app should do the same: a `core/` Python package with no Qt imports, holding the scheduler wrapper, DB access, answer checking and content-pack loading. That package can be tested with plain pytest and could later get a CLI or a different front end. A Rust core is not needed at this scale; Anki's Rust exists for cross-platform sharing with AnkiDroid/AnkiMobile and sync, which this app does not have.
- **Use a typed message layer.** Anki gets typed cross-language calls from protobuf. A smaller app can get most of that with Pydantic or dataclass message types serialized to JSON over QWebChannel, plus generated TypeScript types if a TS front end is used. Protobuf is optional.
- **Never load app pages from `file://`.** Anki serves everything from a localhost HTTP server. A smaller app can avoid the server entirely by serving bundled assets through a custom URL scheme (`QWebEngineUrlSchemeHandler`) or Qt resources (`qrc:`). This keeps same-origin rules simple and needs no open port (general Qt knowledge, unverified this session). A localhost server also works, but if you use one, copy Anki's Host/Origin checks and path-traversal guard.
- **Treat user-authored problem HTML as untrusted.** Copy Anki's strict CSP approach (no scripts) for user-added problems and any imported content packs.
- **Keep the parts that apply:** one SQLite file per profile, automatic periodic backups with daily/weekly/monthly retention, the warning against cloud-synced folders, and a "restore backup" UI. Content (Anki's shared decks; here, problem packs) must never contain executable code. Anki's LaTeX-image security warning shows the risk.
- **Skip what Anki has because of its scale:** add-on systems, a sync server, a Rust/protobuf build pipeline, and multi-language build tooling. Profiles are cheap to support (one folder per profile) and help when testing a "multiple users" design, even if only one person uses the app.

### Gaps
- `docs/architecture.md` is brief and doesn't describe the build system or Svelte. The details above come from `package.json` and the source files.
- I didn't verify Anki's license this session (believed to be AGPL-3.0-or-later). This matters only if code is copied from Anki: AGPL would then apply.
- Default backup retention counts were not given on the backups page.

---

## 2. PySide6 vs PyQt6, QtWebEngine for offline KaTeX/MathJax, QWebChannel, and non-web alternatives

### Takeaway
Use PySide6 (LGPLv3, Qt's official binding, 6.12.0 released 8 Oct 2026) rather than PyQt6 (GPLv3 or a paid commercial license). Render math with KaTeX 0.19.1 (or MathJax 4) bundled locally inside a QtWebEngine view, and talk to Python through QWebChannel. QtWebEngine is the biggest cost: its wheel alone is about 132 MB on Windows and about 250 MB as a macOS universal2 build. Pure-widget rendering with matplotlib mathtext is much smaller but supports only a subset of TeX and doesn't solve math input.

### Cited Findings
**Bindings, versions, licenses**
- PySide6 6.12.0 was released 8 Oct 2026. PyPI also lists 6.11.3 on 26 Oct 2026, presumably a patch on the older branch. The license is "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only", or a commercial license. It requires Python ≥3.10 and <3.16, with `cp310-abi3` wheels: one per platform for Windows x86-64 and ARM64, Linux, and macOS 14.0+ universal2 — [PyPI PySide6](https://pypi.org/project/PySide6/)
- The `PySide6` package is an alias for `PySide6_Essentials` plus `PySide6_Addons` — [PyPI PySide6](https://pypi.org/project/PySide6/)
- In 6.12.0, QtWebEngine is not listed in PySide6-Addons. It ships as a separate `PySide6_WebEngine` package, installed through a `webengine` extra. Addons wheels are 90.5 MB on macOS universal2 and 40.5 MB on Windows — [PyPI PySide6-Addons](https://pypi.org/project/PySide6-Addons/)
- PySide6-WebEngine 6.12.0.140 (8 Oct 2026) wheels: macOS universal2 249.8 MB, Windows x86-64 131.7 MB, Linux x86-64 116.7 MB, Linux ARM64 114.1 MB — [PyPI PySide6-WebEngine](https://pypi.org/project/PySide6-WebEngine/)
- PyQt6 6.12.0 was released 28 Oct 2026 under "GPL v3" or a commercial license, Python ≥3.10 — [PyPI PyQt6](https://pypi.org/project/PyQt6/)
- Riverbank: GPL-compatible use needs no commercial license, and "There is no functional difference between the GPL versions and the commercial versions" — [Riverbank PyQt commercial](https://www.riverbankcomputing.com/commercial/pyqt)
- Qt's LGPLv3 obligations when distributing: deliver Qt's complete corresponding source (or a written offer) "even if the library has not been modified at all"; let users change and re-link the library; include the LGPL text and disclose that it is used; dynamic linking keeps app code separate — [Qt LGPL obligations](https://www.qt.io/licensing/open-source-lgpl-obligations)

**QtWebEngine deployment facts**
- Deploying QtWebEngine requires `QtWebEngineProcess` (Chromium's multi-process model), `qtwebengine_resources.pak`, `icudtl.dat`, `v8_context_snapshot.bin` (one per architecture on macOS) and the `qtwebengine_locales/*.pak` files — [Qt WebEngine: Deploying](https://doc-snapshots.qt.io/qtwebengine/qtwebengine-deploying.html)
- On macOS, the WebEngine helper process must be signed with an entitlements file containing at least the entries in `QtWebEngineProcess.entitlements` — [Qt WebEngine: Deploying](https://doc-snapshots.qt.io/qtwebengine/qtwebengine-deploying.html)

**QWebChannel (Python↔JS)**
- Inside QtWebEngine, load `qrc:///qtwebchannel/qwebchannel.js`, then construct `new QWebChannel(transport, callback)`. Only one QWebChannel is allowed per transport per page. "All communication between the HTML client and the QML/C++ server is asynchronous", so results come back through callbacks. Properties are cached on the JS side. Signals connect with `.connect()`. Only JSON-convertible types serialize correctly — [Qt WebChannel JavaScript API](https://doc.qt.io/qt-6/qtwebchannel-javascript.html)
- Anki's working pattern: a `Bridge(QObject)` with a `cmd` slot registered as `"py"`, called from JS as `channel.objects.py.cmd(arg, cb)`, and returning `json.dumps(...)` — [Anki webview.py](https://github.com/ankitects/anki/blob/main/qt/aqt/webview.py)

**KaTeX / MathJax offline**
- KaTeX v0.19.1: self-host by taking `katex.tar.gz`/`katex.zip` from the GitHub release assets (not the "Source code" download) or from `node_modules/katex/dist/`. The `fonts/` directory is required because "`katex.css` references the fonts using relative URLs". `contrib/auto-render.min.js` is optional — [KaTeX: Browser](https://katex.org/docs/browser)
- MathJax 4.0.0 (5 Aug 2025) added line breaking for inline and display math, 11 new fonts with a broader default font, and ES-module builds. It removed the "-full" components and the all-packages extension — [MathJax v4.0.0 announcement](https://www.mathjax.org/MathJax-v4.0.0-available/)
- Anki still pins `mathjax ^3.1.2` — [Anki package.json](https://raw.githubusercontent.com/ankitects/anki/main/package.json)

**Non-web alternatives**
- Matplotlib (3.11.2 docs) mathtext is "a lightweight TeX expression parser and layout engine". "TeX does *not* need to be installed." It supports fractions (nestable), radicals, `\left/\right`, accents, Greek, and big operators. Limits: a radical's base "cannot contain layout commands such as fractions or sub/superscripts", and environments such as `align` or matrices are not in the documented command set — [Matplotlib mathtext](https://matplotlib.org/stable/users/explain/text/mathtext.html)
- PythonGUIs reports minimal PyInstaller-packaged PyQt6 apps at 30–80 MB on Windows and 50–120 MB on macOS, calls QtWebEngine "particularly large", and lists excluding it as saving "10–50 MB+" — [PythonGUIs: installer sizes](https://www.pythonguis.com/faq/packaged-installer-file-sizes/)

### Inferences
- **Choose PySide6.** LGPL allows any license for the app's own code, as long as Qt stays dynamically linked (PyInstaller and Nuitka standalone builds ship separate Qt shared libraries) and the LGPL obligations are met: license text, a link to or copy of Qt source, and re-linkability. PyQt6 would force the whole app to be GPLv3 if distributed. That is acceptable if the student wants a GPL open-source app, but it is an unnecessary constraint. Anki uses PyQt, but Anki is itself copyleft.
- **Pin to one Qt line** (e.g., PySide6 6.12.x) and upgrade on purpose. PySide6 6.12 wheels need macOS 14+, which sets the app's minimum macOS. The split of WebEngine into `PySide6_WebEngine` in 6.12 is easy to miss: install `pyside6[webengine]` or `PySide6-WebEngine` explicitly, or `QtWebEngineWidgets` imports will fail.
- **Recommended rendering design:** a single long-lived `QWebEngineView` hosts the "review" surface (problem, answer input, feedback, solution), with HTML/CSS/JS assets bundled in the app. Python pushes data by calling a JS function (`page().runJavaScript(...)`) or by emitting a QWebChannel signal; JS sends answers back through a slot. Use KaTeX for speed and a small footprint, and keep MathJax 4 as a fallback for constructs KaTeX lacks. To make "fully offline" true in practice, block all non-local requests (general Qt knowledge, unverified: `QWebEngineUrlRequestInterceptor` can block any non-app scheme, and `QWebEngineSettings.LocalContentCanAccessRemoteUrls` should be off).
- **Reuse WebEngine views.** Each `QWebEngineView` costs memory and startup time (Chromium renderer processes). Reuse one view per screen rather than creating views per problem; the rest of the UI (deck lists, settings, stats) can use plain Qt widgets.
- **Alternative if the 150–300 MB QtWebEngine footprint is unacceptable:** render math to SVG/PNG ahead of time when building content packs (KaTeX via Node, or matplotlib mathtext) and display it in `QLabel`/`QSvgWidget`. This kills interactive math input (no MathLive) and multi-line or `align`/matrix content in mathtext. For a calculus-to-linear-algebra bank it is not recommended: matrices and aligned derivations are common.

### Gaps
- No authoritative installed-size number for a packaged PySide6+QtWebEngine app was found. The wheel sizes above are compressed; unpacked bundles will be larger. Measure on the first real build.
- I couldn't retrieve the Qt for Python docs pages for `QWebEngineUrlSchemeHandler`, `QWebEngineSettings` and QWebChannel (the fetch returned navigation only). The custom-scheme and settings advice above is general knowledge to confirm.

---

## 3. Math input UX: MathLive, ASCII with live preview, converting to SymPy; what WeBWorK and STACK do

### Takeaway
Use MathLive (MIT, self-hostable, exports LaTeX, MathJSON, ASCIIMath, MathML and Typst) as the main input. Keep a plain-text input with live KaTeX preview as a fallback. Convert to SymPy through a deliberately chosen path:
- MathLive's ASCIIMath or MathJSON output, mapped through a small whitelist translator; or
- LaTeX through `latex2sympy2_extended` or Hugging Face `math-verify`.

SymPy's own `parse_latex` (ANTLR default, experimental Lark) can silently drop input. Copy STACK's two-step pattern: show the student how the input was interpreted, with explicit multiplication dots, before grading, and treat syntax errors as "invalid, try again" rather than wrong.

### Cited Findings
**MathLive / Compute Engine**
- MathLive is MIT-licensed and exports and imports "LaTeX, MathML, ASCIIMath, Typst, or MathJSON". It has screen-reader math-to-speech. Releases come on a "semi-annual cadence with major drops around June and January" — [MathLive GitHub](https://github.com/arnog/mathlive)
- The mathfield supports "800 LaTeX commands" and has a customizable virtual keyboard — [MathLive Mathfield](https://mathlive.io/mathfield/)
- Self-hosting: install from npm and "Make sure the contents of the `/fonts/` and `/sounds/` folder are copied to your build output directory". Set `MathfieldElement.fontsDirectory` (a path relative to the bundled runtime) and `MathfieldElement.soundsDirectory` — [MathLive integration guide](https://mathlive.io/mathfield/guides/integration/)
- CortexJS Compute Engine is MIT-licensed. It does "Symbolic manipulation and numeric evaluation of MathJSON expressions": parsing LaTeX to MathJSON, simplify, evaluate, N, expand, subs and solve. Its README does not mention differentiation or integration — [Compute Engine GitHub](https://github.com/cortex-js/compute-engine)

**SymPy parsing**
- SymPy 1.14.0 (27 Apr 2025) is the latest on PyPI, BSD license, Python ≥3.9 — [PyPI sympy](https://pypi.org/project/sympy/)
- `parse_latex(s, strict=False, backend='antlr')`: the default is ANTLR, with `antlr4-python3-runtime==4.11` pinned in the docs. Lark "is intended to eventually completely replace the ANTLR-based parser" but is experimental — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html)
- The ANTLR parser "may fail to fully parse an expression, yet not throw a warning". For example, `parse_latex(r'x -')` returns `x`. `strict=True` (ANTLR only) raises instead. Lark raises on ill-formed input and does not yet support matrices, higher-order or partial derivatives, or double/triple integrals — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html)
- `parse_expr` uses `eval` and "shouldn't be used on unsanitized input". `implicit_multiplication_application` relaxes syntax (e.g., `3xyz`, `sin 2x`). `convert_xor` maps `^` to `**`. The docs say convert_xor is included in `standard_transformations`, but their own listed tuple and example contradict that, so check the source before relying on `^` working by default — [SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html)
- `latex2sympy2_extended` 1.11.0 (10 Jan 2026) is MIT-licensed and adapted from OrangeX4/latex2sympy. Its parser is generated with ANTLR 4.13.1, with runtime extras for 4.9.3, 4.11.0 and 4.13.2. It adds matrices, eval-at `|_{x=...}`, calculus, sets and binomials, and warns it "will do some irreversible calculations when converting determinants" — [PyPI latex2sympy2-extended](https://pypi.org/project/latex2sympy2-extended/)
- Hugging Face Math-Verify (Apache-2.0) does "Answer Extraction -> Expression Common Representation Conversion (SymPy) -> Gold Comparison". It compares sets and intervals, resolves `x = 1 -> 1`, handles flipped inequalities, strips units and converts percentages, and has timeout protection. `verify` is asymmetric (gold vs prediction order matters). It depends on `latex2sympy2_extended` and recommends always specifying the antlr4 runtime extra — [Math-Verify GitHub](https://github.com/huggingface/math-verify)

**STACK and WeBWorK**
- STACK's "Insert Stars" options control implicit multiplication: none (missing `*` makes the input invalid), implied multiplication for `)(` patterns, single-character variables (splits `xy` into `x*y`), no user functions (`x(t+1)` becomes `x*(t+1)`), and space-as-multiplication. STACK cautions that students eventually need strict syntax, and "It is often very important to have some on-screen representation of multiplication" at the validation step — [STACK Input syntax](https://docs.stack-assessment.org/en/Authoring/Inputs/Input_syntax/)
- WeBWorK optionally enables MathQuill (instructor setting "Assist with the student answer entry process"). It renders the expression as the student types and offers a toolbar for fractions, roots, absolute value, exponents, ∞ and π. Typing `inf` inserts ∞ — [WeBWorK MathQuill](https://openwebwork.org/mathquill/)

### Inferences
- **Recommended input pipeline:**
  1. MathLive mathfield in the WebEngine view, with a virtual keyboard and inline shortcuts.
  2. On submit, send both `getValue('latex')` and a structured form (MathJSON or ASCIIMath) to Python through QWebChannel.
  3. Python parses with a **whitelisted** parser: either a small MathJSON-to-SymPy translator (MathJSON is a JSON tree, so the mapping is explicit and has no `eval`), or `latex2sympy2_extended` with `strict`-style failure handling.
  4. Show the parsed form back, rendered from SymPy's `latex()` with explicit `\cdot`, in STACK style ("We read your answer as: …").
  5. Grade only after the student confirms, or grade straight away when there is no ambiguity.

  A MathJSON route gives a parse tree that MathLive itself built, which avoids LaTeX-parser ambiguity (unverified detail: MathJSON's operator naming has to be mapped by hand).
- **Never call `sympify`/`parse_expr` on raw student text.** Both use `eval`. Tokenize and whitelist symbols and functions first, or use a non-eval parser.
- **Answer checking strategy (general CAS-checking knowledge, not from one source):**
  - Answer types: `expression`, `equation`, `interval/set`, `number` with tolerance, `multiple-choice`, `matrix`, `ordered tuple`.
  - Equivalence: first `simplify(a - b) == 0`. Then add a numeric spot-check at random points inside the stated domain to catch cases `simplify` misses or would hang on. Run checks in a worker process with a timeout, because SymPy can hang on pathological input.
  - Form requirements (e.g., "factored form", "simplified", "exact not decimal") need structural checks, not equivalence.
  - Math-Verify's set, interval and equation handling is a useful reference or dependency, but it was built to grade LLM outputs: test its asymmetry and leniency (e.g., unit stripping) against the app's pedagogy before adopting it.
- **Packaging pin:** the ANTLR runtime version must match the generated parser. Pin `antlr4-python3-runtime` exactly, and confirm PyInstaller/Nuitka include the generated parser modules.
- **Grading in JS (Compute Engine) instead of Python** is possible for simple algebra, but its CAS depth (no confirmed calculus) is far below SymPy's. Keep SymPy as the grader and use Compute Engine at most for instant client-side "is this well-formed" feedback.

### Gaps
- No official MathLive version number or MathJSON-to-SymPy mapping was retrieved. Check the MathLive changelog and the MathJSON standard library spec when implementing.
- WeBWorK's exact text format submitted by MathQuill wasn't documented on the fetched page.
- No benchmark comparing parse accuracy of SymPy `parse_latex` (ANTLR/Lark), `latex2sympy2_extended` and Math-Verify on student input was found.

---

## 4. Alternatives to Python + Qt: Tauri (with a Python sidecar), Electron, Flutter

### Takeaway
Tauri 2 produces tiny installers (single-digit MB), but SymPy grading would need a PyInstaller-built Python sidecar per target triple. That brings back most of the Python packaging work and adds a second language and IPC layer. Electron bundles Chromium (roughly 85–250 MB) and has the same SymPy problem. Doing grading in JavaScript with CortexJS Compute Engine removes Python but gives up CAS depth. For one student building with an AI agent, Python + PySide6 + QtWebEngine is the simplest stack: one language for logic, SymPy and py-fsrs in-process, and a web view only where math needs it.

### Cited Findings
- Tauri v2 sidecars: list binaries under `bundle.externalBin` in `tauri.conf.json`. Each needs a `-$TARGET_TRIPLE` suffixed copy (e.g., `my-sidecar-x86_64-unknown-linux-gnu`). Calling them needs the shell plugin and explicit `shell:allow-execute`/`allow-spawn` capability permissions. The docs name "Python CLI applications or API servers bundled using `pyinstaller`" as a common use — [Tauri v2: Sidecar](https://v2.tauri.app/develop/sidecar/)
- A 2026 comparison article (an aggregator citing a February 2026 benchmark suite and others) reports a Hello World build of 3.2 MB on Tauri 2.x vs 85 MB on Electron 43, a complex 6-window app of 8.6 MB vs 244 MB, idle memory of 42 MB vs 168 MB, and cold start of 380 ms vs 1,420 ms. Electron 43 went stable on 30 Jun 2026 with Chromium 150 and Node 24.17. The article doesn't state test hardware or methodology details, so treat the numbers as indicative — [Tech Insider: Tauri vs Electron 2026](https://tech-insider.org/tauri-vs-electron-2026/)
- Compute Engine (MIT) covers simplify, evaluate, N, expand, subs and solve on MathJSON; calculus isn't mentioned in its README — [Compute Engine GitHub](https://github.com/cortex-js/compute-engine)

### Inferences
- **Tauri + Python sidecar:** the installer is small only before the sidecar. A PyInstaller'd SymPy sidecar adds tens of MB, and it still has to be built on each OS and per architecture (target triples), and signed and notarized on macOS. Rust plus TypeScript plus Python is three languages. Startup cost appears unless the sidecar runs as a long-lived local server. It is worth it only if the developer is already fluent in Rust and web.
- **Electron:** similar to QtWebEngine in footprint (both ship Chromium), and it still needs a Python sidecar for SymPy. No advantage over Qt here unless the whole app, including grading, moves to JS.
- **Flutter:** has no mature in-process LaTeX math input comparable to MathLive (unverified; packages such as `flutter_math_fork` exist for rendering). It would need a webview for MathLive anyway and a sidecar for SymPy, so it isn't recommended.
- **Pure web (PWA) or JS-only (Electron/Tauri with Compute Engine):** possible if the bank's answers are restricted to forms Compute Engine can compare. It is risky for Calc 1–3 and linear algebra, where SymPy's coverage matters.
- **Recommendation:** Python 3.12/3.13 + PySide6 6.12 + QtWebEngine for the review surface + SymPy in a worker process. Revisit Tauri only if bundle size becomes a real problem for users.

### Gaps
- No primary, reproducible benchmark of a PySide6+QtWebEngine bundle against Tauri/Electron was found. The size figures are from different sources and methods.
- I didn't verify Flutter's 2026 math-rendering and input ecosystem this session.

---

## 5. Packaging and distribution: PyInstaller vs Nuitka vs Briefcase vs cx_Freeze; macOS .app/.dmg, Windows installers, CI, signing, notarization, Gatekeeper, SmartScreen, Apple Silicon

### Takeaway
Start with PyInstaller 6.22.x in onedir mode. It has mature PySide6/QtWebEngine hooks, and since PR #7619 it preserves `.framework` bundles on macOS so codesigning works. Build on each OS (PyInstaller isn't a cross-compiler) with GitHub Actions `windows-latest` and `macos-latest` (arm64) runners. Wrap the output as a `.dmg` on macOS and an Inno Setup or NSIS installer (or MSI via WiX/Briefcase) on Windows. Without paying, macOS users must click through System Settings > Privacy & Security > Open Anyway (the Control-click bypass was removed in Sequoia), and Windows users see a SmartScreen warning. Free fixes are limited: on macOS, ad-hoc signing is mandatory on Apple Silicon but doesn't remove the warning. On Windows, the Microsoft Store (free account, MSIX re-signed by Microsoft) is the only no-cost way to avoid SmartScreen; SignPath Foundation offers free signing for qualifying open-source projects.

### Cited Findings
**Freezers**
- PyInstaller 6.22.3 (12 Sep 2026) supports Python 3.8–3.15 and "is not a cross-compiler: to make a Windows app you run PyInstaller in Windows". It supports macOS universal2 only if Python and every dependency are universal2 — [PyPI pyinstaller](https://pypi.org/project/pyinstaller/)
- PyInstaller PR #7619 preserves `.framework` bundles on macOS, which "removes the need for the horrible work-around that we had for QtWebEngine". QtWebEngine now works in onefile macOS builds, data goes in `Contents/Resources` and binaries in `Contents/Frameworks`, and the change addresses "compliance issues w.r.t. code-signing". QML plugins may still need manual signing — [PyInstaller PR #7619](https://github.com/pyinstaller/pyinstaller/pull/7619)
- The old PyInstaller codesigning wiki recipe says it "appears to be long out of date". It notes codesign needs subcomponents signed first and that "Self signed certificates are no longer allowed" — [PyInstaller wiki: OSX Code Signing](https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing)
- Nuitka 4.0 (22 Apr 2026) brings large compile-time scalability gains. It added support for newer PySide6 on macOS. "Unfortunately 3.14 support is not yet ready" — [Nuitka 4.0 release](https://nuitka.net/posts/nuitka-release-40.html)
- Nuitka has `--mode=standalone|onefile|app`, and `--mode=app` or `--macos-create-app-bundle` creates a macOS `.app`. "The PySide6 plugin covers qt-plugins." On Windows it recommends Visual Studio 2022+, and a MinGW64 compiler must be the one Nuitka downloads — [Nuitka user manual](https://nuitka.net/user-documentation/user-manual.html)
- `pyside6-deploy` (in the Qt for Python 6.10 docs) wraps Nuitka (default 2.7.11, changeable in `pysidedeploy.spec`). It defaults to `onefile`, with `standalone` as an option. It warns that heavy modules "like QtWebEngine also gets added to your executable, even when you do not use it". It needs `dumpbin` (from MSVC) on Windows — [pyside6-deploy docs](https://doc.qt.io/qtforpython-6.10/deployment/deployment-pyside6-deploy.html)
- Briefcase (BeeWare) packages for "macOS, as a standalone .app", "Windows, as an MSI installer" and Linux system packages, and has code-signing identity guides per platform. Its docs header showed a 0.4.8 development build — [Briefcase docs](https://briefcase.beeware.org/en/latest/)
- PythonGUIs: minimal PyInstaller PyQt6 apps are 30–80 MB on Windows and 50–120 MB as a macOS .app. QtWebEngine is "particularly large". UPX can cut 20–40% but risks antivirus false positives. Onefile mode doesn't shrink output and starts more slowly — [PythonGUIs: installer sizes](https://www.pythonguis.com/faq/packaged-installer-file-sizes/)

**CI runners**
- The GitHub Actions `macos-13` image was retired by 4 Dec 2025. `macos-15-intel` is the x86_64 label, and "GitHub will no longer support this architecture on macOS after the macOS 15 runner image is retired in Fall 2027" — [GitHub changelog](https://github.blog/changelog/2025-09-19-github-actions-macos-13-runner-image-is-closing-down/)

**macOS: signing, notarization, Gatekeeper**
- In Sequoia, "You used to be able to override Gatekeeper by pressing Control-click while opening an app, but that has been disabled." Users must choose Done, then go to System Settings > Privacy & Security and click **Open Anyway** — [Macworld](https://www.macworld.com/article/2457844/what-to-do-when-you-cant-open-an-app-you-just-installed-in-macos-sequoia.html)
- Free Apple account vs the $99/yr Developer Program (article dated 4 Oct 2026): free gives only ad-hoc signatures, and users see the "could not verify… free of malware" warning. The paid program gives a Developer ID certificate and notarization, so the app opens with the normal dialog. Homebrew's official cask repo won't list apps without Developer ID signing and notarization — [flaviocopes](https://flaviocopes.com/apple-developer-free-vs-paid/)
- Apple's membership page ties "Certificates, Identifiers & Profiles" (where Developer ID certificates come from) to Program membership and lists "Mac software notarization" as a comparison row. The tier checkmarks didn't survive extraction — [Apple: Choosing a Membership](https://developer.apple.com/support/compare-memberships)
- Eclectic Light (11 Aug 2026, tested on macOS Tahoe 26.6.1):
  - "completely unsigned code has never been allowed in Apple silicon Macs", and "All executable code must now be signed, even if only with an ad hoc signature".
  - An ad-hoc-signed app that is **not** quarantined (e.g., built locally) launched normally. A quarantined one with default settings was offered for the Trash.
  - `spctl --master-disable` is "no longer supported" per `man spctl`.
  - The article advises against stripping the quarantine attribute.

  — [Eclectic Light](https://eclecticlight.co/2026/08/11/how-can-you-run-code-that-hasnt-been-notarised/comment-page-1/). Partly in tension with Macworld/flaviocopes, which describe "Open Anyway" as still available; Eclectic Light's test may describe only the Finder launch dialog. Verify on macOS 26.
- QtWebEngine's helper process must be signed with its entitlements file for notarization — [Qt WebEngine: Deploying](https://doc-snapshots.qt.io/qtwebengine/qtwebengine-deploying.html)

**Windows: SmartScreen and signing (Microsoft Learn)**
- Unsigned: "Strong SmartScreen block; enterprises may block entirely", "Not recommended for public distribution". Self-signed certificates block public users — [Microsoft Learn: code signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- Artifact Signing (formerly Trusted Signing) costs about $9.99/month. Individuals are eligible in the USA and Canada only, and it "does **not** provide instant SmartScreen trust": reputation builds over time — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- OV certificates cost $150–300/yr and require a hardware key (since June 2023). EV costs $400+/yr, and EV's SmartScreen bypass "was removed in 2024", so it is "no longer justified" for that purpose — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- For Microsoft Store MSIX, "Microsoft re-signs your package automatically, meaning users never see a SmartScreen warning", and the developer account at storedeveloper.microsoft.com is free. MSI/EXE submitted to the Store must already be CA-signed. SignPath Foundation gives free OV-level signing to qualifying open-source projects — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)

### Inferences
- **Python version:** 3.12 or 3.13. Nuitka 4.0 lacks 3.14 support, SymPy 1.14's classifiers stop at 3.13, and Anki ships 3.13.
- **Freezer choice:**
  - **PyInstaller onedir (recommended).** Its PySide6/QtWebEngine hooks are the most battle-tested and it builds fast. Use `--windowed`, set `--osx-bundle-identifier`, and maintain a checked-in `.spec` file that lists data files (KaTeX, MathLive, content DB) and excludes unused Qt modules (Qt3D, QtQuick3D, QtMultimedia, QtCharts if unused).
  - **Nuitka / `pyside6-deploy`:** faster runtime and somewhat smaller, but compiles take far longer and need a C compiler. Try it later if startup time matters.
  - **Briefcase:** convenient installers (MSI, .app/.dmg) and signing flows, but less control over Qt/WebEngine pruning.
  - **cx_Freeze:** viable, but nothing found suggests it beats PyInstaller here (unverified for 2026).
  - Avoid onefile mode: it unpacks to a temp folder on every launch, which is slow with QtWebEngine and triggers antivirus heuristics.
- **macOS artifact:** build per-architecture (an arm64 `.app` on `macos-latest`, plus an Intel build on `macos-15-intel` until Fall 2027) rather than universal2, to avoid the "every dependency must be universal2" trap and roughly halve download size. Package with `hdiutil create` (built into macOS) or `create-dmg`.
- **Signing without paying:** the build must be at least ad-hoc signed. Run `codesign --force --deep -s - App.app` after any post-build modification (general knowledge; `--deep` is discouraged for production Developer ID signing, but fine for ad-hoc). The README should walk users through "Open Anyway". If the app only runs on the Mac that built it, building locally avoids quarantine entirely, per Eclectic Light. For wide distribution, $99/yr Developer ID plus notarization is the only way to remove the warning. Notarization needs hardened runtime, a secure timestamp, `xcrun notarytool submit --wait` and `xcrun stapler staple` (general knowledge; I couldn't retrieve Apple's notarization page body).
- **Windows artifact:** PyInstaller onedir output wrapped in Inno Setup (free) or NSIS, installing per-user to `%LOCALAPPDATA%\Programs\<App>` so no admin is needed. Also offer a portable `.zip`. Unsigned builds will show "Windows protected your PC", then More info, then Run anyway (well known; the exact UI wording wasn't verified this session). Publishing an MSIX through the free Microsoft Store account is the zero-cost route to no SmartScreen warning, but PyInstaller-in-MSIX packaging needs testing.
- **CI:** a single GitHub Actions workflow with a matrix of `windows-latest`, `macos-latest` (arm64) and optionally `macos-15-intel`. Each job installs pinned dependencies (`uv` or `pip` with a lock file), runs tests, freezes, smoke-tests the frozen app headlessly (launch with a `--self-test` flag that opens the DB, renders one problem offscreen and grades one answer, then exits 0), and uploads artifacts or attaches them to a GitHub Release on tags. GitHub-hosted runners are free for public repos (general knowledge; private repos have monthly minute quotas, and macOS minutes count extra).
- **LGPL compliance checklist for the bundle:** include Qt's LGPL text and a notice; link to the exact Qt/PySide source version; keep Qt as separate shared libraries (the onedir default). Don't statically link or merge Qt into a single binary (onefile is still dynamic at runtime, but onedir makes "replaceability" obvious).

### Gaps
- The PyInstaller version that first shipped PR #7619 wasn't stated on the PR page (believed to be the 5.x/6.0 era).
- Apple's own notarization documentation body couldn't be retrieved. The notarization steps are general knowledge.
- The exact macOS 26 (Tahoe) Gatekeeper flow for a quarantined, ad-hoc-signed downloaded app is ambiguous between sources and needs a hands-on test.
- I found no current numbers for cx_Freeze or for Nuitka bundle size with QtWebEngine.

---

## 6. Data design: shipped read-only content DB + writable user DB, migrations, WAL, review logs, per-OS paths, backups, export/import, versioned content packs and offline updates

### Takeaway
Ship problems in a read-only `content.db` (journal_mode=DELETE, opened `mode=ro`) inside the app or as versioned pack files. Keep everything the user creates in a separate `user.db` (WAL) under `platformdirs.user_data_dir`. Join them via `ATTACH` but write only to `user.db`, since cross-database transactions are not atomic in WAL mode. Reference problems by stable string IDs, never rowids. Version the user schema with `PRAGMA user_version` and forward-only migrations. Store an append-only review log with UTC timestamps and durations, which py-fsrs's optimizer needs (≥512 reviews). Take rolling automatic backups the way Anki does.

### Cited Findings
**SQLite behavior**
- `PRAGMA journal_mode=WAL` is persistent across connections. WAL creates `-wal` and `-shm` files, and "If a database file is separated from its WAL file, then transactions that were previously committed… might be lost, or the database file might become corrupted" — [SQLite WAL](https://www.sqlite.org/wal.html)
- "WAL does not work over a network filesystem" because processes share memory — [SQLite WAL](https://www.sqlite.org/wal.html)
- "Transactions that involve changes against multiple ATTACHed databases are atomic for each individual database, but are not atomic across all databases as a set" — [SQLite WAL](https://www.sqlite.org/wal.html)
- A read-only WAL database can be read only if the `-shm`/`-wal` files exist, or the directory is writable, or it is opened `immutable`. SQLite advises converting to `journal_mode=DELETE` "prior to burning an SQLite database image onto read-only media" — [SQLite WAL](https://www.sqlite.org/wal.html)
- URI `mode=ro` opens read-only. `immutable=1` skips locking and change detection, but "if… a database file is immutable and that file changes anyhow, then SQLite might return incorrect query results and/or SQLITE_CORRUPT errors" — [SQLite URI filenames](https://www.sqlite.org/uri.html)
- `PRAGMA application_id` is a 32-bit header integer apps should set "so that utilities such as file(1) can determine the specific file type". `PRAGMA query_only` blocks writes on a connection — [SQLite PRAGMA](https://www.sqlite.org/pragma.html)

**User data location**
- platformdirs 4.14.2 (31 Oct 2026) returns per-OS directories. Example: `user_data_dir("MyApp", "MyCompany")`, and `~/.local/share/MyApp` on Linux — [PyPI platformdirs](https://pypi.org/project/platformdirs/)
- Anki's convention: `%APPDATA%\Anki2`, `~/Library/Application Support/Anki2`, `~/.local/share/Anki2`. Don't put the folder in a cloud-sync folder or on a network drive — [Anki manual: Files](https://docs.ankiweb.net/files.html)

**FSRS data needs (py-fsrs)**
- `fsrs` 6.3.2 (9 Aug 2026), MIT, Python ≥3.10 — [PyPI fsrs](https://pypi.org/project/fsrs/)
- API: `Scheduler`, `Card`, `Rating` (Again/Hard/Good/Easy = 1–4), `ReviewLog`, and `State` (Learning/Review/Relearning). Objects serialize with `to_json`/`from_json`. `desired_retention` defaults to 0.9, `learning_steps` to 1 min and 10 min, and `enable_fuzzing` is optional. "Py-FSRS uses UTC only" — [py-fsrs GitHub](https://github.com/open-spaced-repetition/py-fsrs)
- The optimizer needs `pip install "fsrs[optimizer]"`, which imports `torch`, `pandas` and `tqdm`. It reads `card_id`, `rating`, `review_datetime` and `review_duration` from each ReviewLog. Below 512 non-same-day reviews it returns the default parameters. `compute_optimal_retention` requires ≥512 logs with non-null `review_duration`. At most the first 64 reviews per card are used — [py-fsrs optimizer.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/optimizer.py)

**Backups (Anki precedent)**
- Every 30 minutes by default, with daily/weekly/monthly retention, early backups before risky operations, and a restore UI. Backups exclude media — [Anki manual: Backups](https://docs.ankiweb.net/backups.html)

### Inferences
**Recommended layout**
- App bundle: `resources/content/core-<packversion>.db` (read-only, journal_mode=DELETE, `application_id` set). Optional downloadable packs `packs/<pack_id>-<version>.mpack` go in the user data dir.
- User data dir (`platformdirs.user_data_dir("Toishi", appauthor=False)`): `profiles/<name>/user.db` (WAL), `profiles/<name>/backups/`, `profiles/<name>/media/` (user-added images), `prefs.json`. Use `user_log_dir` for logs.

**Connections**
- Open `user.db` normally with `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL` (the last is general knowledge: safe with WAL apart from losing the most recent transaction on power loss).
- Then `ATTACH 'file:/path/content.db?mode=ro' AS content` (Python's `sqlite3.connect(..., uri=True)`). Prefer `mode=ro` over `immutable=1`, because an app update could replace the file while it's open.
- On macOS, the signed `.app` is effectively read-only. Writing anything inside it breaks the signature (general knowledge), so the content DB must never be written in place.

**Schema sketch**
- *content DB:*
  - `pack(id, version, title, min_app_version, created_at)`
  - `problem(id TEXT PRIMARY KEY` — a stable slug or UUID, e.g. `calc1.limits.0042` — `, pack_id, course, unit, topic, skill_tags JSON, difficulty, statement TEXT` (Markdown+LaTeX) `, parts JSON, solution TEXT, hints JSON, assets JSON, revision INT, retired INT DEFAULT 0)`
  - `answer_spec` in `parts`: type (expr/eq/interval/set/number/mcq/matrix/tuple), the canonical answer as SymPy-parsable text, variables and their domains for numeric checks, tolerance, and form requirements.
  - Optional `problem_fts` (FTS5) for search.
- *user DB:*
  - `meta(key, value)`, plus `PRAGMA user_version` for the schema version.
  - `card(id INTEGER PK, source TEXT CHECK(source IN ('content','user')), problem_id TEXT, part_idx INT, fsrs_json TEXT, due_utc TEXT, state INT, suspended INT, content_revision_seen INT, UNIQUE(source, problem_id, part_idx))`
  - `review_log(id INTEGER PK, card_id, rating INT, reviewed_at_utc TEXT, duration_ms INT, answer_raw TEXT, answer_parsed TEXT, correct INT, hints_used INT, app_version TEXT, scheduler_params_id INT)` — append-only, never updated.
  - `scheduler_params(id, params_json, desired_retention, created_at)`
  - `user_problem(...)`, with the same shape as the content `problem` table.
  - `setting(key, value)`, and `tag`/`deck` tables as needed.
- Store the FSRS `Card` as JSON from `to_json()` and denormalize `due_utc`/`state` into columns for fast queue queries (`WHERE due_utc <= ? ORDER BY due_utc`).
- Store all times in UTC (py-fsrs requires it). Compute the "study day" boundary in local time with a user-set rollover hour, like Anki's "next day starts at".

**Migrations**
- `migrations/0001_init.sql`, `0002_*.sql`, and so on, applied in order inside one transaction each. Bump `PRAGMA user_version` in the same transaction. Take an automatic backup before migrating.
- Refuse to open a `user.db` whose `user_version` is newer than the app knows, with a clear "this file was created by a newer version" message (Anki has the same downgrade limitation).
- Test every migration against fixture DBs from each prior version.

**Content updates without breaking progress**
- Problem IDs are permanent. A typo fix bumps `revision`. A changed answer gets a new revision flagged `answer_changed`, and the app can prompt to reset that card or leave it. A removed problem is set `retired=1`, never deleted, so its review history stays valid.
- On startup, reconcile cards against the content DB: create cards lazily as the user unlocks topics, and hide orphaned or retired ones.
- Distribution stays offline: users download a new app version, or a `.mpack` file (a zip with `manifest.json` and `content.db`, carrying `pack_id`, `version`, `min_app_version` and a SHA-256), and import it from the menu. The app copies it into the user data dir and attaches the newest compatible version.

**Optimizer**
- Bundling `fsrs[optimizer]` pulls in PyTorch, hundreds of MB (general knowledge), so keep it out of the default build. Log everything the optimizer needs (rating, UTC time, duration) from day one. Options:
  - ship the optimizer as an optional "power-user" add-on or a separate download;
  - let the user export review logs as CSV and optimize in a separate tool;
  - use a lighter optimizer implementation (see Gaps).
- With fewer than 512 reviews it returns defaults anyway, so this can wait months.

**Backups and export**
- Use Python's `sqlite3.Connection.backup()` or `VACUUM INTO 'file'` (both general knowledge) to write `backups/user-YYYYMMDD-HHMM.db` every N minutes and on close. Prune to keep e.g. the last 10 recent copies plus daily, weekly and monthly ones, as Anki does.
- "Export progress" writes a zip containing `user.db` (via the backup API, so it's consistent), media, and a manifest with app and schema versions. Import validates `application_id` and `user_version`, then migrates. Also offer CSV export of `review_log` for transparency and FSRS tooling.

**Robustness**
- Single-instance lock (e.g., `QLockFile` in the data dir; general Qt knowledge) so two app copies don't open the same profile.
- Run `PRAGMA integrity_check` on demand ("Check Database").
- Warn if the data dir sits inside Dropbox, OneDrive or iCloud.

### Gaps
- The `PRAGMA user_version` section, the `VACUUM INTO` docs and Python's `Connection.backup` docs weren't retrieved this session (well-established features, but uncited here).
- Exact platformdirs default paths on Windows/macOS weren't on the fetched page. Typically `C:\Users\<u>\AppData\Local\<Author>\<App>` and `~/Library/Application Support/<App>`; verify, including `roaming=` behavior.
- No lighter-weight FSRS optimizer for Python was verified. The Rust-backed `fsrs-rs-python` bindings or the `fsrs-optimizer` package may avoid PyTorch, but I didn't check them this session.

---

## 7. Problem rendering: LaTeX statements, diagrams/graphs (SVG, function plots), multi-part, multiple choice vs free response

### Takeaway
Render each problem as an HTML fragment in the WebEngine view: Markdown plus KaTeX-delimited math (`\(...\)`/`\[...\]`, matching Anki), static SVG figures stored in the content pack, and parts as an ordered list of sub-questions, each with its own answer widget (MathLive field, multiple-choice radio buttons, numeric field, or interval builder). Generate function-plot figures ahead of time as SVG (e.g., matplotlib at pack-build time), or draw them client-side with a bundled JS plotting library when interactivity (zoom, trace) is needed.

### Cited Findings
- Anki uses `\(`/`\)` for inline and `\[`/`\]` for display math with bundled MathJax — [Anki manual: Math](https://docs.ankiweb.net/math.html)
- KaTeX can be self-hosted with its `fonts/` directory, plus optional `auto-render.min.js` to typeset delimited math in a page — [KaTeX: Browser](https://katex.org/docs/browser)
- MathJax 4 adds automatic line breaking for inline and display equations — [MathJax v4.0.0](https://www.mathjax.org/MathJax-v4.0.0-available/)
- Anki serves user content under a strict no-script CSP — [Anki mediasrv.py](https://github.com/ankitects/anki/blob/main/qt/aqt/mediasrv.py)
- Anki's front end bundles d3 7 for its UI (statistics graphs) — [Anki package.json](https://raw.githubusercontent.com/ankitects/anki/main/package.json)
- Matplotlib mathtext renders TeX-subset labels with no LaTeX install, so pack-build-time plots can carry math axis labels — [Matplotlib mathtext](https://matplotlib.org/stable/users/explain/text/mathtext.html)

### Inferences
- **Authoring format:** keep problems as source files (YAML or Markdown with front matter) in a Git repo, one file per problem, and "compile" them into `content.db` with a build script. The script:
  - validates every LaTeX string by rendering it with KaTeX in strict mode via Node (or headless in CI);
  - checks every `answer_spec` parses into SymPy and that the canonical answer passes its own checker;
  - pre-renders plots to SVG.

  A broken problem then fails CI instead of failing in front of the user.
- **Use one renderer everywhere.** The answer-preview, problem and solution panes should all use KaTeX so the student sees the same typography. Keep MathJax 4 as a fallback only if needed for `\require`-style extensions or line-breaking of long derivations.
- **Diagrams:** prefer SVG (crisp at any DPI, small, styleable for dark mode via `currentColor`). Generate function plots for curve-sketching with matplotlib (`format='svg'`) at build time. For "sketch the curve" problems, grade structured features (intercepts, asymptotes, intervals of increase, concavity) through typed inputs rather than free drawing. Optional later: an interactive graph widget (e.g., JSXGraph or function-plot.js bundled locally; unverified licenses and versions) for exploration.
- **Multi-part:** each part gets its own FSRS card (so the `card` key is `problem_id + part_idx`), or the whole problem is one card graded by the weakest part. Recommended: a card per independently checkable skill, but present parts together when they share a setup, and show part B only after part A is answered so A's answer doesn't leak.
- **Multiple choice vs free response:** store MCQ distractors with the problem, shuffle option order per review, and record which option was chosen in `review_log.answer_raw` so misconceptions can be analysed. Free response uses the CAS pipeline from section 3. MCQ yields weaker evidence of recall, so consider mapping a correct MCQ to "Hard" or "Good", never "Easy".
- **Self-grading:** for proofs or "explain" questions, show the solution and let the user self-rate (Again/Hard/Good/Easy), as Anki does. FSRS only needs a rating.
- **Accessibility and theming:** Qt palette dark mode should flow into the web view through CSS variables. MathLive's speech output is a bonus.

### Gaps
- I didn't research current versions or licenses of JS plotting libraries (JSXGraph, function-plot, Plotly) for an offline bundle.
- No source was found on best practice for FSRS with multi-part problems specifically. The design above is reasoned, not cited.

---

## 8. Later phase: an offline C++ coding environment (compiler bundling, sandboxed test runs, editor widgets)

### Takeaway
On Windows, bundle a portable MinGW-w64 GCC toolchain such as w64devkit (Unlicense wrapper, "No installation required… Fully offline") inside the app or as an optional download. On macOS, rely on Apple's Command Line Tools (`xcode-select --install`, which puts `clang` in `/Library/Developer/CommandLineTools`) rather than shipping a compiler. Run compiled programs in a child process with a wall-clock timeout, CPU and memory limits, a temp working directory, and no network. Use a web code editor in QtWebEngine: CodeMirror 6 (light; Anki uses CodeMirror 5) or Monaco (heavy). QScintilla is tied to PyQt and GPL, so it is a poor fit with PySide6.

### Cited Findings
- w64devkit is a "Portable C and C++ Development Kit for x64 (and x86) Windows" with Mingw-w64 GCC, GDB, GNU Make, busybox-w32 (incl. `sh`), CMake + Ninja, Vim and ccache. "No installation required. Run it anywhere as any user… Fully offline." It uses the Unlicense, but the Mingw-w64 runtime licenses in `COPYING.MinGW-w64-runtime.txt` "should be distributed with your binaries" — [w64devkit GitHub](https://github.com/skeeto/w64devkit)
- Apple's Command Line Tools for Xcode contain "the same macOS SDK, man (manual) pages, and toolchain binaries that ship with Xcode" (e.g., `clang`). They install via `xcode-select --install` to `/Library/Developer/CommandLineTools`, and the user must agree to the Command Line Tools License Agreement. "On a fresh install of macOS, invoking any command… (such as `git`) … prompts you to download and install" them — [Apple: Installing the command-line tools](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools.md)
- QScintilla 2.14.1 (Jun 2023) is GPL v3 or commercial, and its bindings "sit on top of PyQt5" — [PyPI QScintilla](https://pypi.org/project/QScintilla/)
- Anki uses `codemirror ^5.63.1` in its web UI — [Anki package.json](https://raw.githubusercontent.com/ankitects/anki/main/package.json)
- Monaco can be loaded from local files instead of a CDN through loaders such as `@monaco-editor/loader` (search results only; not fetched) — [npm @monaco-editor/loader](https://npmjs.com/package/@monaco-editor/loader)

### Inferences
- **Compiler strategy:**
  - **Windows:** ship w64devkit (or just its GCC/g++ subset) in a `toolchains/` folder, extracted on first use to the user data dir. Invoke `g++ -std=c++20 -O2 -Wall` with an explicit path and never rely on PATH. Download size is likely tens to ~100+ MB (not verified), so make it an optional "C++ module" download rather than part of the base installer.
  - **macOS:** detect `xcrun --find clang++`. If it is missing, show a button that runs `xcode-select --install`. Bundling Apple's toolchain isn't viable: its license is accepted per user, and redistribution terms weren't verified, so treat it as not allowed. Shipping a Homebrew/LLVM clang is possible, but it still needs the macOS SDK headers from CLT.
- **Sandbox and limits (general knowledge, not verified this session):**
  - Run the compiled binary via `subprocess.Popen` with a timeout (e.g., 2 s per test), stdin fed from test input, and stdout/stderr captured with size caps.
  - *macOS/Linux:* use `resource.setrlimit` (RLIMIT_CPU, RLIMIT_AS, RLIMIT_FSIZE, RLIMIT_NPROC) in `preexec_fn`, plus `start_new_session=True` so the whole process group can be killed.
  - *Windows:* put the process in a Job Object with `JOB_OBJECT_LIMIT_PROCESS_MEMORY`, `JOB_OBJECT_LIMIT_JOB_TIME` and `KILL_ON_JOB_CLOSE` (e.g., via `pywin32`). Job-object approaches exist in other projects (e.g., Rust `io-harness`, `RestrictedProcess.NET`), but I only saw search results, not documentation.
  - On both, run in a fresh temp directory.
  - This is resource limiting, not a security sandbox. Since the user runs their own code on their own machine, that is acceptable. Don't ship untrusted third-party code to run.
- **Editor:**
  - **CodeMirror 6** (MIT; general knowledge) is modular and small, and fits next to KaTeX/MathLive in the same WebEngine view. It has C++ syntax highlighting via `@codemirror/lang-cpp` (unverified package name).
  - **Monaco** gives VS Code-like IntelliSense UI but is several MB and has no real C++ language server offline unless you also ship `clangd`.
  - **Pure-Qt option:** `QPlainTextEdit` + `QSyntaxHighlighter`, which is minimal and needs no web dependency.
  - Recommendation: CodeMirror 6.
- **Grading C++ problems:** store test cases (input/expected output, or a checker) in the content pack. Compile once per submission, run each case with limits, and report compile errors, wrong answer, timeout or runtime error. Map pass/fail onto an FSRS rating.

### Gaps
- w64devkit's current version and download size weren't shown on the fetched page.
- I didn't verify the Xcode CLT license terms on redistribution, Windows Job Object docs, or CodeMirror 6/Monaco current versions and sizes.

---

## 9. Testing strategy, project structure, and keeping the app maintainable when much of the code is written by an AI coding agent

### Takeaway
Keep a strict layering (pure-Python `core` → `qt` GUI → `web` assets), give each layer its own fast tests, and make CI the gatekeeper on every OS. The CI suite: unit tests for the scheduler wrapper, DB migrations and answer checker; golden tests that every content-pack problem renders and self-grades; GUI smoke tests; a frozen-app self-test. Written conventions in the repo (an agent instructions file, an architecture doc, ADRs) and small, typed, single-purpose modules keep an AI agent on track. Anki's own setup (vitest, Playwright, a `readyz` endpoint for e2e tests, protobuf-typed boundaries) is a good model.

### Cited Findings
- Anki's front end uses `vitest ^3` for unit tests, `@playwright/test ^1.62.1` for end-to-end tests, `svelte-check`, ESLint, Prettier and dprint — [Anki package.json](https://raw.githubusercontent.com/ankitects/anki/main/package.json)
- Anki exposes `/_anki/readyz` (503 until the collection is open, then 200) so "the e2e harness should poll it" — [Anki mediasrv.py](https://github.com/ankitects/anki/blob/main/qt/aqt/mediasrv.py)
- Anki's pylib can be used "by command-line programs without the GUI", and protobuf definitions give type-safe cross-language calls — [Anki architecture.md](https://github.com/ankitects/anki/blob/main/docs/architecture.md)
- PyInstaller must run on each target OS — [PyPI pyinstaller](https://pypi.org/project/pyinstaller/)

### Inferences
**Suggested repo structure**
```
toishi/
  pyproject.toml            # pinned deps; uv.lock or requirements.lock
  AGENTS.md / CLAUDE.md     # rules for the coding agent (layering, testing, no network, style)
  docs/architecture.md      # layers, data flow, DB schemas, ADRs in docs/adr/
  src/mastery/
    core/                   # NO Qt imports
      db/ (connection.py, migrations/*.sql, repo.py)
      scheduling/ (fsrs_adapter.py, queue.py, day_boundary.py)
      grading/ (parse.py, equivalence.py, specs.py, worker.py)   # SymPy in a subprocess with timeout
      content/ (packs.py, models.py)                             # pydantic/dataclass models
      backup.py, export.py, paths.py (platformdirs)
    qt/                     # PySide6 widgets, windows, QWebChannel bridge
      bridge.py, review_view.py, main_window.py, app.py
    web/                    # HTML/CSS/TS for review surface; vendored katex/, mathlive/
  content-src/              # problem source files (YAML/MD), one per problem
  tools/build_content.py    # compiles content-src → content.db, validates every problem
  tests/ (unit/, migrations/fixtures/, content/, gui/ with pytest-qt, e2e/)
  packaging/ (mastery.spec, installer.iss, dmg script)
  .github/workflows/ci.yml  # matrix: windows-latest, macos-latest (+ macos-15-intel)
```

**Testing layers**
1. `core` unit tests with plain pytest:
   - FSRS adapter: given a fixed clock, rating X leads to due date Y (inject the clock and never call `datetime.now()` directly).
   - Grading: a table of (student input, canonical answer, expected verdict), including traps like `x -`, `2x` vs `2*x`, `sin^2 x`, `e^x` vs `exp(x)`, intervals, ± and equivalent forms.
   - Migrations: open each historic fixture DB, migrate, assert the schema and data.
2. Content golden tests: every problem in every pack parses, its canonical answer passes its own checker, a known-wrong answer fails, and LaTeX renders in KaTeX strict mode.
3. GUI tests: pytest-qt (general knowledge; check the current version) for widget flows, plus a few end-to-end tests that load the WebEngine view offscreen and drive it through QWebChannel or `runJavaScript`. Add a "ready" signal like Anki's `readyz` so tests don't race page load.
4. Packaging smoke test: run the frozen app with `--self-test` on each CI OS. This catches missing hidden imports (ANTLR runtime, KaTeX fonts, QtWebEngine resources) that only appear after freezing.
5. A network-tripwire test that fails if any code path attempts an outbound connection (e.g., a WebEngine request interceptor that records non-local URLs during tests).

**Agent-maintainability practices**
- Write layering rules into the agent instruction file and enforce them mechanically: an import-linter contract ("`mastery.core` must not import `PySide6`"), `ruff` and `mypy --strict` (or pyright) on `core`, and pre-commit hooks. Agents follow rules better when CI fails on violations.
- Use typed boundary models (dataclasses/pydantic) for everything crossing core↔GUI↔JS, with one JSON schema shared by Python and TS, so agent-written changes on either side break loudly.
- Make small PR-sized tasks with a test written first. Ask the agent to add or adjust tests in the same change, and require CI green on both OSes before merge.
- Keep ADRs (architecture decision records) for big choices (PySide6, PyInstaller, KaTeX, DB split) so a future agent session doesn't "helpfully" switch to PyQt or a CDN.
- Pin every dependency and vendor web assets (KaTeX, MathLive) with version and license files in `web/vendor/<lib>-<version>/`. Upgrade one dependency per PR.
- Keep a `THIRD_PARTY_LICENSES` file generated at build time (needed for LGPL Qt, MIT KaTeX/MathLive, BSD SymPy, MIT py-fsrs, Unlicense/mingw runtime notices).

### Gaps
- I didn't research current pytest-qt, import-linter or Playwright-for-QtWebEngine (Chromium remote-debugging port) tooling versions this session.
- No published study was found on maintainability practices specific to AI-agent-written desktop apps. The practices above are engineering judgment.
