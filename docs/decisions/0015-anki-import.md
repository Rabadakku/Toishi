# ADR-0015: Anki import — our own reader and renderer, the anki package only as a test oracle

- Status: Accepted
- Date: 2026-11-01

## Context

M7 brings in students' own Anki decks (IMP-2..8): `.apkg` and `.colpkg` from every Anki
version still in use, Anki's "Notes in Plain Text" export, and optionally the review history.
Anki's templates are not Mustache (empty-field rules, right-to-left filters, FrontSide,
special fields, cloze numbering), and shared decks carry JavaScript. The official `anki`
package (AGPL) can render cards, but its import API was removed and re-shimmed in 26.09, it
pulls in protobuf, orjson and requests, and the app stays MIT-clean if it never ships it.

## Decision

### A pure-Python importer in `core/importers/anki/`

- **Readers.** `read_package` takes both layouts: legacy (`collection.anki2`/`.anki21`, JSON
  media map) and latest (`meta` 08 03, `collection.anki21b` zstd-streamed, protobuf media map,
  zstd media). Without `meta`: `collection.anki21`, else `collection.anki2`; the placeholder
  `collection.anki2` is never read when a real collection is there, and a package holding only
  it is refused. Schema 11 (JSON in `col`) and 15-18 (tables + protobuf blobs, the `unicase`
  collation, fields/templates joined to `notetypes`). A ~60-line protobuf wire reader, no
  `protobuf` dependency. `read_text` reads the plain-text export with every header line
  (`#separator`, `#html`, `#tags`, `#columns`, `#notetype`, `#deck`, the column headers, the old
  `tags:` line) and a CSV parser matching the Rust csv crate Anki uses.
- **Untrusted input.** Entry count, per-entry size, total size and compression ratio are capped
  (`Limits`); zstd is read as a capped stream; duplicate zip entries, unsafe media names (more
  than one path component), unnormalized latest-format names and bad SHA-1s are refused; no
  archive name is ever used as a path (media goes to the content-addressed store); the SQLite
  file is deserialized into memory, read-only, defensive, `trusted_schema` off.
- **Renderer (IMP-8).** `template.py` and `cloze.py` port rslib's `template.rs`,
  `template_filters.rs` and `cloze.rs`. Where Anki's main branch and the 26.09.3 release
  differ (`type:` modifiers), we match 26.09.3, the release students run and the oracle.
  `hint:` is drawn as `<details>` (no script); with `hint_style="anki"` the output is Anki's
  markup byte for byte except the BLAKE3 id.
- **Mapping** (card-format "Anki compatibility"). IDs come from the note GUID
  (`anki.<key>.<card number>`; `anki.<key>` for cloze cards), so .apkg, .colpkg and a text
  export with a GUID column give the same cards and re-imports update in place; a text row
  without a GUID keys on note type + first field (Anki's duplicate test).
  - Normal note types: one flashcard per Anki card (the cards in the package, or the ones
    Anki's cardgen would make for text). Both sides rendered, sanitized and wrapped in
    `<div class="anki-card cardN [anki-nt-<hash>]" [data-anki-css="_anki-nt-<hash>.css"]>`;
    the back is the answer after `<hr id=answer>`. `[[type:F]]` shows F on the back (typing is
    self-graded in Anki too).
  - Stock Cloze (`{{cloze:F}}` / `{{cloze:F}}<br>{{G}}`): one `cloze` card, `text_md` = the
    sanitized field in Anki's cloze syntax, `extra_md` = G; the queue serves one item per
    blank (ADR-0010). Other cloze note types render per blank with their own templates.
  - `Mastery Problem`: fields → card-file text → `core.cards.load` (all card-file checks,
    self-check of the key), so a bad key rejects the card exactly as in a card file.
  - Image Occlusion is rejected (it needs Anki's script).
  - CSS that isn't Anki's stock CSS is scoped to `.anki-nt-<hash>` (`.card`, `body`, `html`,
    `:root`, `.cardN` map onto the wrapper; `.nightMode` becomes `.anki-night`; `@import` and
    remote `url()` dropped) and stored once as a media file every card of the type links.
  - Sanitizing keeps an allow-list of tags and attributes; scripts, styles, frames, objects,
    forms, SVG, event handlers, ids and remote or scheme URLs go. Media refs are normalized
    like Anki's (NFC, disallowed characters, Windows names, 120 bytes); `[sound:x]` becomes
    `<audio controls>`.
- **Dry run, one transaction (IMP-5).** `plan_anki_import` feeds everything through core.cards'
  import plan (`plan_loaded`, new): added / updated / unchanged / rejected with file, line (a
  note's number in a package) and reason, missing cards, media, the course tree.
  `apply_anki_import` runs `apply_import` and the history inside one `UserStore.atomic`.
- **History (IMP-4).** Per Anki card: when its data has `s`/`d` and its preset has FSRS
  parameters, the memory state is imported as it is (`flashcard_state`, never over a state the
  profile already has) and the preset becomes a parameter set (`anki-<params id>`, in the import
  log's summary with the items to replay). Otherwise the revlog is filtered as Anki's
  `reviews_for_fsrs` does (cram, pre-reset, manual/ease-0 rows out; the last learning block;
  incomplete SM-2 histories carry an `sm2_seed`). Every kept review is an append-only attempt
  (verdict `self`, `rules_version` `anki-import-1`, `params_id` = its set) plus a review
  event, with the attempt's `study_day` = the Anki study day: rollover from the colpkg (4 AM
  for an .apkg) in one fixed UTC offset, as Anki counts `delta_t`. Reviews already in the
  profile (same card, item, time) are skipped. A py-fsrs replay over these days equals Anki's
  own `compute_memory_state` in the tests; replaying 24-hour periods does not.
- **Engine hook.** The engine on this branch has no `recompute_memory`. After applying,
  callers run `recompute_memory(storage)` (`ENGINE_RECOMPUTE_HOOK`), which calls
  `Engine.recompute_memory()` once it exists and returns False until then.

### The anki package is dev-only

`anki==26.9.3` is in the `dev` group: `tests/importers/make_fixtures.py` builds the fixture
decks with it, and the tests use it as the oracle (full render, `card.question()` /
`card.answer()`, its CSV import, `compute_memory_state`). import-linter forbids `core` and
`app` from importing `anki`/`aqt`, and the PyInstaller spec excludes both.

### Outside the package

- `core/cards/importer.py`: `plan_loaded` (the dry run after `load`), `ImportPlan.kind` (the
  import log's kind and the scope of "missing") and `ImportPlan.extra` (more summary keys).

## Consequences

- The page must draw `anki-card` HTML (`core.importers.anki.is_anki_html`) instead of passing
  it to the Markdown renderer, sanitize it again with a DOM allow-list, add `anki-night` in
  dark mode, and load each card's `data-anki-css` file and media through the media route that
  ADR-0012 left open.
- The queue's cloze regex doesn't know nested or multi-ordinal clozes (`{{c1,2::x}}`) or
  MathJax-aware closing; `core.importers.anki.cloze` is the exact port it can call.
- Histories without FSRS state wait for the engine's replay (the hook); until then those
  cards are new to the queue though their events are stored.
- Not imported: Image Occlusion notes, `[latex]` (shown as text), history of Mastery Problem
  notes (problems are scheduled through skills), suspension/flags, `#match scope` and
  `#if matches` (updates always win).
- A text export carries no media; importing one after the deck's package keeps the images the
  package stored.
