# ADR-0012: The bridge passes the core's views through; the app runs on real data

- Status: Accepted
- Date: 2026-11-01

## Decision

- **The bridge is thin.** `app/api.py` returns `core.queue.to_dict` of the StudyService views
  unchanged, and `web/src/lib/types.ts` mirrors `core/queue/views.py` field for field
  (`tests/app/test_bridge_contract.py` checks both the declarations and a live session).
  This resolves the prototype mismatches ADR-0009 listed by adopting the core's shapes:
  reason tags (`review`, `relearn`, `new-skill`, ...), `item_key` (never a card id),
  milliseconds everywhere, `TimingReport` (`active_ms`, solve/entry, pause count,
  `after_wake`, `idle_trimmed`), `study_tick`, `TodayView`, Lighter set and flashcards. New
  core fields reach the page without bridge changes.
- **Bridge methods** are `study_*` (one per StudyService call), `profile_*`, `prefs_*` and
  `library_*`, each taking at most one JSON object. Arguments are type-checked and capped;
  item calls carry `item_key`, and a call for an item no longer on screen is refused (a
  double key press never skips an item). A refused call raises `UserMessage`; pywebview
  rejects the page's promise with an Error of that name and the page shows its text.
- **Threads.** One re-entrant lock serializes every bridge call that touches the profile;
  storage gives each worker thread its own read connection and writes on its own thread.
- **Profiles.** The app opens the profile used last; on first run the page asks for a name.
  Appearance preferences live in the profile's settings (`ui.theme`, `ui.text_size_px`).
- **Shipped packs** (`app/packs.py`, `SHIPPED`): `scripts/build.sh` compiles them with the
  full content checks into `build/packs/*.db`, which the PyInstaller spec places in the .app;
  dev runs compile them there when missing, unreadable or older than their sources.
- **Loopback only.** pywebview's stdlib-based server looked up names at launch:
  `HTTPServer.server_bind()` calls `socket.getfqdn()`, and `uuid.uuid1()` (its server id
  and every `evaluate_js` id) can fall back to `uuid.getnode()`, whose `_arp_getnode()`
  resolves the Mac's own `<name>.local` over multicast DNS, which triggers macOS's Local
  Network prompt. `app/shell.py` swaps in a server bound to 127.0.0.1 by number that names
  itself by that number, and random ids (`tests/app/test_local_network.py`).
- **Native Edit menu.** Undo and Redo (`undo:`/`redo:` to the first responder) and Undo Last
  Answer, which tells the page through a `toishi:menu` event (run_js, never evaluate_js).
- **Tests on real data.** `tests/app/harness.py` serves the built page and answers bridge
  calls over a local JSON endpoint backed by `app.api.Api`; a test-only init script defines
  `window.pywebview.api`. The shipped page never contains it. The in-page mock stays for
  page tests of the study screen and implements the same contract.

## Consequences

- Images in pack cards are not shown yet (the page draws "[figure: ...]"): the CSP allows
  images from 'self' only, and the pack media live in the pack database. Serving them needs
  a media route on the loopback server or a CSP change, decided in its own ADR.
  (Decided in ADR-0017: a media route; the CSP is unchanged.)
- `--self-test` now also studies through the bridge in a temporary profile; `--no-window`
  runs that part alone (Linux, CI-less checks).
