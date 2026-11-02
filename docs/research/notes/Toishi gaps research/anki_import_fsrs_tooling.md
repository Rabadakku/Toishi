# Importing Anki decks (with review history) and using FSRS from Python without heavy dependencies

Research date: 2026-11-01. Primary sources: the Anki source code (ankitects/anki `main` at commit 136bd42, 2026-10-29, the same code as release 26.09.3), Anki manual and changelogs, PyPI, crates.io, and the open-spaced-repetition repos (fsrs-rs `main` 3be7d2a of 2026-10-28 and tag v6.6.2, fsrs-rs-python 0.9.3 at b013db2 of 2026-08-31, py-fsrs 6.3.2). Statements marked "(verified locally)" come from tests run in a sandbox with `anki==26.9.3`, `fsrs==6.3.2`, `fsrs-rs-python==0.9.3` and `zstandard` installed from PyPI. In those tests, the official `anki` package built real .apkg files, which were then taken apart with plain `zipfile`, `sqlite3` and `zstandard`.

Current versions (Nov 2026): Anki 26.09.3 (git tag 26.09.3; PyPI `anki` 26.9.3, uploaded 2026-09-23) — [PyPI anki](https://pypi.org/project/anki/), [Anki tags](https://github.com/ankitects/anki/tags). py-fsrs `fsrs` 6.3.2 (2026-08-09), MIT — [PyPI fsrs](https://pypi.org/project/fsrs/). `fsrs-rs-python` 0.9.3 (2026-08-31) — [PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/). Rust crate `fsrs` 6.6.2 (2026-08-29) — [crates.io fsrs](https://crates.io/crates/fsrs).

---

## 1. .apkg / .colpkg internals across Anki versions, and how to detect each format

### Takeaway
Both .apkg and .colpkg files are ZIP archives that use the same container code. There are three "package versions". If a `meta` file is present, it is a 2-byte protobuf: `08 02` means legacy (`collection.anki21`), `08 03` means latest (`collection.anki21b`). If `meta` is missing, the file is legacy: `collection.anki21` if that entry exists, otherwise `collection.anki2`. The latest format zstd-compresses the SQLite file, the media map and every media file, and its media map is protobuf. The legacy format stores plain SQLite (schema 11) and a JSON media map such as `{"0":"pic.png"}`. Modern Anki also always writes a dummy `collection.anki2` that holds only a "Please update to the latest Anki version" note. An importer that reads `collection.anki2` first will therefore import garbage.

### Cited Findings
- **Version enum and filenames.** `meta.rs` maps `Legacy1 → "collection.anki2"`, `Legacy2 → "collection.anki21"` and `Latest → "collection.anki21b"`. For schema versions, Legacy1 and Legacy2 map to `SchemaVersion::V11` and Latest maps to `V18`. — [rslib/src/import_export/package/meta.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/meta.rs)
- **Detection logic used by Anki itself.** Anki reads the `meta` zip entry and protobuf-decodes it. If the version is `Unknown` (0), it errors with `ImportError::TooNew`. If `meta` is absent, the version is `Legacy2` when `collection.anki21` exists and `Legacy1` otherwise. Also, `zstd_compressed() = !is_legacy()` and `media_list_is_hashmap() = is_legacy()`. — [meta.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/meta.rs)
- **Protobuf definitions.** `message PackageMetadata { enum Version { VERSION_UNKNOWN = 0; VERSION_LEGACY_1 = 1; /* meta missing, collection.anki2 */ VERSION_LEGACY_2 = 2; /* meta missing, collection.anki21 */ VERSION_LATEST = 3; /* Implies MediaEntry media map, and zstd compression */ } Version version = 1; }` and `message MediaEntries { message MediaEntry { string name = 1; uint32 size = 2; bytes sha1 = 3; optional uint32 legacy_zip_filename = 255; } repeated MediaEntry entries = 1; }` — [proto/anki/import_export.proto](https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto)
- **Write order in `export_collection` (shared by apkg and colpkg).** First `meta` (ZIP stored). Then the collection file: in latest format a stored zip entry containing a zstd stream; in legacy format a normal deflated entry. Then `write_dummy_collection`, which always writes `collection.anki2` as a schema-11 SQLite DB with `page_size=512`, containing one Basic note whose text is the "too new" message. Then the media files, written as zip entries named `"0"`, `"1"`, … by index, and finally the `media` map. — [colpkg/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/colpkg/export.rs)
- **Media map encoding.** Legacy packages use a JSON `{"<index>": "<filename>"}`. Latest packages use protobuf `MediaEntries`, where the index of an entry in the list is its zip filename. In latest format, both the map and each media file are zstd-compressed. — [colpkg/export.rs `write_media_map`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/colpkg/export.rs); [package/media.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/media.rs)
- **Observed layouts (verified locally, Anki 26.9.3 `export_anki_package`).**
  - Latest apkg: zip entries `['meta','collection.anki21b','collection.anki2','0','media']`, all with compress_type 0 (stored). `meta` = `08 03`. The media map decodes to protobuf `0a21 0a07 "pic.png" 1009 1a14 <20-byte sha1>`.
  - Legacy apkg ("support older versions"): `['meta','collection.anki21'(deflate),'collection.anki2','0','media']`. `meta` = `08 02`. `media` = `b'{"0":"pic.png"}'`.
  - In both, the dummy `collection.anki2` note reads "Please update to the latest Anki version, then import the .colpkg/.apkg file again." — [PyPI anki 26.9.3](https://pypi.org/project/anki/) (verified locally)
- **zstd gotcha (verified locally).** Anki compresses with a streaming `zstd::Encoder::new(writer, 0)` and multithreading for large inputs, so the frame header has no content size. In the test, `zstandard.get_frame_parameters(...).content_size` returned "unknown", and one-shot `ZstdDecompressor().decompress()` raised "could not determine content size in frame header". Streaming decompression (`ZstdDecompressor().stream_reader(...)`) works. — [colpkg/export.rs `zstd_copy`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/colpkg/export.rs); [PyPI zstandard](https://pypi.org/project/zstandard/)
- **Missing media map.** If the `media` entry is missing, Anki treats it as `{}`, with the comment "Older AnkiDroid versions wrote colpkg files without a media map". — [package/media.rs `get_media_list_data`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/media.rs)
- **Filename safety on import.** Legacy map names go through `safe_normalized_file_name`, which rejects unsafe names (Corrupt) and NFC-normalizes. Latest-format entries whose names are not already normalized, or that lack a valid 20-byte sha1, are rejected as `ImportError::Corrupt`. — [package/media.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/media.rs)
- **Version history from the changelog.**
  - 2.1.50: "When exporting, you can optionally target Anki 2.1.50+ … media files will be compressed, but the resulting .colpkg will not be readable by older Anki clients."
  - 2.1.52: "a new implementation of apkg importing and exporting … Support for older clients can be optionally disabled, which results in smaller apkg files", behind a feature flag.
  - 2.1.54: enabled.
  - 2.1.55: "The new import/export code is now the default", and "When scheduling is included, filtered decks are no longer converted to normal decks."
  - 2.1.58: fixed a colpkg bug with "compatibility with older clients enabled".
  — [Anki 2.1.50–2.1.59 changes](https://changes.ankiweb.net/changes/2.1.50-59.html)
- **Manual wording.** "Support older Anki versions (slower/larger files)": when checked, "a legacy version of the file is created"; when unchecked, imports and exports are faster and media is compressed, but the file "will not be readable by older Anki clients". `.colpkg` holds the whole collection, and importing it replaces the user's cards. `.apkg` holds one deck plus its children and is added to the collection; for notes already present, Anki keeps the version with the newest modification time. — [Anki manual: Exporting](https://docs.ankiweb.net/exporting.html)
- **apkg export options.** `ExportAnkiPackageOptions { with_scheduling = 1; with_deck_configs = 2; with_media = 3; legacy = 4; }`. The apkg is built by creating a fresh temp collection (`CollectionBuilder::new` followed by `DELETE FROM notetypes`), inserting the gathered data, and closing it at `meta.schema_version()` (V11 for legacy, V18 for latest). — [import_export.proto](https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto); [apkg/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/apkg/export.rs)
- **What "include scheduling" changes.**
  - With scheduling, the revlog of the exported cards is gathered (`get_revlog_entries_for_searched_cards`). If a card's original deck is missing, cards in filtered decks are restored to their home deck.
  - Without scheduling, cards and notes are reset (`reset_cards_and_notes`, `remove_system_tags`) and deck study info and config ids are reset.
  - The manual says excluding scheduling removes "the entire scheduling information, including marked and leech tags".
  — [import_export/gather.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/gather.rs); [Exporting](https://docs.ankiweb.net/exporting.html)
- **Recent changes.**
  - 2026-07-10: "strip FSRS params from deck config on export without scheduling" (#4721, shipped in 26.08).
  - 2026-08-08: "remove legacy importer and exporter" (#5153, in 26.09b1).
  - 2026-09-08: compatibility shims for `AnkiPackageImporter`/`AnkiPackageExporter` (#5547).
  — [commit 8a99c47](https://github.com/ankitects/anki/commit/8a99c47); [commit d4fdbef](https://github.com/ankitects/anki/commit/d4fdbef); [commit b758186](https://github.com/ankitects/anki/commit/b758186); [Anki releases](https://github.com/ankitects/anki/releases)

### Inferences
- **Recommended detection order for a Python importer:**
  1. Open the zip.
  2. If `meta` exists, decode its version. Bytes `08 03` mean latest and `08 02` mean legacy-2; any value of 0 or above 3 means "too new".
  3. If `meta` is absent, use `collection.anki21` if present, otherwise `collection.anki2`.
  4. Never pick `collection.anki2` when a newer file is present, because it is the dummy.
  5. Then decompress with zstd (streaming) only for latest-format packages, write the result to a temp file, and open it with `sqlite3`.
  6. Read `col.ver` to confirm (11 or 18).
- **The same reader handles .apkg and .colpkg**, because both go through `export_collection`. The differences are in content: a colpkg is the whole collection, including global `config` such as rollover and the FSRS toggle; an apkg is a fresh minimal collection holding only the exported subset.
- **Decompression library.** The Python 3.14 standard library has `compression.zstd` ([PEP 784](https://peps.python.org/pep-0784/)). For Python 3.10–3.13, the `zstandard` package has macOS arm64 wheels (0.25.0 `macosx_11_0_arm64` downloaded successfully, verified locally — [PyPI zstandard](https://pypi.org/project/zstandard/)). Either way, decompress as a stream.
- **Packages from Anki older than 2.1.50 (or AnkiDroid)** have no `meta` and are schema 11. Packages from 2.0-era Anki (`collection.anki2` only) may contain v1-scheduler revlog semantics; see §6 about ease=3 meaning "Easy" in v1 learning.

### Gaps
- I did not verify AnkiDroid's or AnkiMobile's current exporters byte-for-byte. AnkiDroid uses the same Rust backend in recent versions, but I found no primary source in this session confirming its current defaults.
- The manual does not state which Anki versions need "Support older Anki versions"; the changelog implies anything below 2.1.50 (colpkg) or below 2.1.52/2.1.55 (apkg).

---

## 2. The collection schema (v11 legacy JSON vs v18 tables): notetypes, fields, templates, decks, notes, cards, revlog, card `data` FSRS state, deck config FSRS parameters

### Takeaway
Read `col.ver`. Schema 11 keeps notetypes, decks and deck options as JSON strings in the single `col` row (`models`, `decks`, `dconf`, `conf`). Schema 18 moves them into `notetypes`, `fields`, `templates`, `decks`, `deck_config` and `config` tables, whose `config` columns are protobuf blobs (JSON for `config.val`), and whose name columns use a custom `unicase` collation that Python's `sqlite3` must register before querying. `notes.flds` is joined by `\x1f`. `cards.data` is JSON holding the FSRS memory state (`s`, `d`, `dr`, `decay`, `lrt`). Revlog `ease` is the button (0 means a manual action), `ivl`/`lastIvl` are days when positive and seconds when negative, and `type` 0–5 distinguishes learning, review, relearning, filtered/cram, manual and rescheduled entries.

### Cited Findings
- **Core tables (schema 11, still present in 18).**
  - `col(id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)`
  - `notes(id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)`
  - `cards(id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)`
  - `revlog(id, cid, usn, ease, ivl, lastIvl, factor, time, type)`
  - `graves`
  — [rslib/src/storage/schema11.sql](https://github.com/ankitects/anki/blob/main/rslib/src/storage/schema11.sql)
- **Upgrades.**
  - Schema 14 adds `deck_config(id, name COLLATE unicase, mtime_secs, usn, config blob)`, `config(KEY, usn, mtime_secs, val blob)` and `tags`.
  - Schema 15 adds `fields(ntid, ord, name COLLATE unicase, config blob)`, `templates(ntid, ord, name, mtime_secs, usn, config blob)`, `notetypes(id, name COLLATE unicase, mtime_secs, usn, config blob)` and `decks(id, name COLLATE unicase, mtime_secs, usn, common blob, kind blob)`.
  - Schema 17 rebuilds `tags` (with `collapsed`, `config`).
  - Schema 18 rebuilds `graves`.
  - Supported range: `SCHEMA_MIN_VERSION = 11`, `SCHEMA_MAX_VERSION = 18`.
  — [storage/upgrades/](https://github.com/ankitects/anki/tree/main/rslib/src/storage/upgrades)
- **Collation (verified locally).** Querying `templates` in an extracted `collection.anki21b` with Python `sqlite3` failed with `sqlite3.OperationalError: no such collation sequence: unicase` until a `unicase` collation was registered (`con.create_collation("unicase", casefold-compare)`). — [schema15_upgrade.sql](https://github.com/ankitects/anki/blob/main/rslib/src/storage/upgrades/schema15_upgrade.sql) (verified locally)
- **Orphan rows (verified locally).** In a latest-format apkg, `notetypes` held only the exported notetype ("Basic"), but `fields` and `templates` also held rows for every stock notetype (Basic and reversed, Cloze, Image Occlusion, …) with `ntid`s that do not exist in `notetypes`. The cause: the exporter creates a default collection and runs only `DELETE FROM notetypes`. Always join `fields`/`templates` to `notetypes.id`. — [apkg/export.rs `new_minimal`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/apkg/export.rs)
- **Notetype protobuf (schema 18 blobs).**
  - `Notetype.Config`: `kind=1` (0 normal, 1 cloze), `sort_field_idx=2`, `css=3`, `latex_pre=5`, `latex_post=6`, `latex_svg=7`, `reqs=8`, `original_stock_kind=9`, `original_id=10`, `other=255`.
  - `Field.Config`: `sticky=1`, `rtl=2`, `font_name=3`, `font_size=4`, `description=5`, `plain_text=6`, `collapsed=7`, `exclude_from_search=8`, `id=9`, `tag=10`, `prevent_deletion=11`.
  - `Template.Config`: `q_format=1`, `a_format=2`, `q_format_browser=3`, `a_format_browser=4`, `target_deck_id=5`, `browser_font_name=6`, `browser_font_size=7`, `id=8`.
  - Verified bytes: template blob `\n\t{{Front}}\x12'{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}@…`, i.e. field 1, field 2, field 8.
  — [proto/anki/notetypes.proto](https://github.com/ankitects/anki/blob/main/proto/anki/notetypes.proto) (verified locally)
- **Notetype JSON (schema 11, `col.models`).**
  - Keys: `id, name, type (0/1), mod, usn, sortf, did, tmpls[], flds[], css, latexPre, latexPost, latexsvg, req, originalStockKind, originalId`.
  - Template keys: `name, ord, qfmt, afmt, bqfmt, bafmt, did, bfont, bsize, id`.
  - Field keys: `name, ord, sticky, rtl, font, size, description, plainText, collapsed, excludeFromSearch, id, tag, preventDeletion`.
  — [notetype/schema11.rs](https://github.com/ankitects/anki/blob/main/rslib/src/notetype/schema11.rs) (key list verified locally on a legacy apkg)
- **Decks.**
  - The `decks.name` column uses `\x1f` as the hierarchy separator in schema 18 (the storage layer runs `.replace('\x1f', "::")` on read). Schema-11 JSON uses `"::"`.
  - `decks.kind` is `Deck.KindContainer { oneof kind { Normal normal = 1; Filtered filtered = 2; } }`. `Normal` has `config_id=1`, `description=4`, `markdown_description=5`, `review_limit=6`, `new_limit=7`.
  - Verified: the kind blob `0A020801` decodes to normal{config_id=1}.
  — [storage/deck/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/storage/deck/mod.rs); [proto/anki/decks.proto](https://github.com/ankitects/anki/blob/main/proto/anki/decks.proto)
- **Deck options (`deck_config.config` protobuf `DeckConfig.Config`).**
  - Steps: `learn_steps=1`, `relearn_steps=2` (minutes, floats).
  - FSRS: `fsrs_params_4=3`, `fsrs_params_5=5`, `fsrs_params_6=6` (packed repeated float), `desired_retention=37` (float), `historical_retention=40`, `ignore_revlogs_before_date=46` (string), `param_search=45`, `easy_days_percentages=4`.
  - Limits: `new_per_day=9`, `reviews_per_day=10`, `maximum_review_interval=16`, `cap_answer_time_to_secs=24`.
  - Schema-11 `dconf` JSON keys (verified): `fsrsWeights`, `fsrsParams5`, `fsrsParams6`, `desiredRetention`, `sm2Retention`.
  — [proto/anki/deck_config.proto](https://github.com/ankitects/anki/blob/main/proto/anki/deck_config.proto) (verified locally)
- **Global config.**
  - The `config` table (schema 18) or `col.conf` JSON (schema 11) has camelCase keys including `rollover`, `creationOffset`, `localOffset`, `schedVer`, `curDeck`, `nextPos`. The global FSRS on/off switch is the boolean key `fsrs`.
  - In a test apkg, the config keys were `activeDecks, addToCur, collapseTime, creationOffset, curDeck, curModel, dayLearnFirst, dueCounts, estTimes, newSpread, nextPos, sched2021, schedVer, sortBackwards, sortType, timeLim`. Neither `fsrs` nor `rollover` was carried over, even though FSRS was on in the source.
  — [config/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/config/mod.rs) (verified locally)
- **Notes.**
  - `flds` is the fields joined with `"\x1f"` (`join_fields`).
  - `tags` is `" t1 t2 "`, with a leading and trailing space, or `""` (`join_tags`). Verified sample: `' t1 t2 '`, `'Q <img src="pic.png">\x1fA [sound:x.mp3]'`.
  - `id` is epoch ms; `mod` is epoch seconds.
  — [storage/note/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/storage/note/mod.rs); [tags/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/tags/mod.rs)
- **Cards.**
  - `CardType` (`type`): New=0, Learn=1, Review=2, Relearn=3.
  - `CardQueue` (`queue`): New=0 (due = position), Learn=1 (due = unix timestamp in seconds), Review=2 (due = days since collection creation), DayLearn=3, PreviewRepeat=4, Suspended=-1, SchedBuried=-2, UserBuried=-3.
  - `odid`/`odue` hold the home deck and due date while a card is in a filtered deck.
  — [card/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/card/mod.rs)
- **Card `data` JSON (`CardData`).**
  - `pos` (original new position), `s` (FSRS stability, rounded to 4 dp), `d` (difficulty, 3 dp), `dr` (desired retention, 2 dp), `decay` (3 dp), `lrt` (last review time, epoch seconds), `cd` (custom-data JSON string, ≤100 bytes, keys ≤8 bytes).
  - Invalid or missing data falls back to defaults. A memory state exists only if both `s` and `d` are present.
  - Verified sample after two Good answers with FSRS on: `{"pos":1,"s":2.3065,"d":2.111,"dr":0.9,"decay":0.154,"lrt":1793547859}`.
  — [storage/card/data.rs](https://github.com/ankitects/anki/blob/main/rslib/src/storage/card/data.rs) (verified locally)
- **Revlog (`RevlogEntry`).**
  - `id`: review timestamp in epoch ms. `cid`: card id.
  - `ease`: button chosen. 1–4 = Again/Hard/Good/Easy. 0 = manual rescheduling. "In the V1 scheduler, 3 represents easy in the learning case."
  - `ivl` / `lastIvl`: "Positive values are in days, negative values in seconds".
  - `factor`: ease ×10 (2500 = 250%). "When FSRS is active, difficulty is normalized to 100-1100 range."
  - `time`: answer time in ms.
  - `type`: Learning=0, Review=1, Relearning=2, Filtered=3 ("Cram"/"Early", or rescheduling disabled), Manual=4, Rescheduled=5.
  - `is_reset()` = type 4 with factor 0 (Forget/reset). `is_cramming()` = type 3 with factor 0. `has_rating_and_affects_scheduling()` = ease > 0 and not cramming.
  — [revlog/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/revlog/mod.rs)
- **Verified revlog sample (FSRS on).** `(id, cid, ease=3, ivl=-600, lastIvl=0, factor=224, time, type=0)`, then `(…, ease=3, ivl=2, lastIvl=-600, factor=223, …, type=0)`. 223 = round((D−1)/9·1000)+100 with D = 2.111, matching the 100–1100 normalization. Anki's own code inverts this as `difficulty = (factor/1000 − 0.1)·9 + 1` when `factor ≤ 1100`. — [scheduler/fsrs/memory_state.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/memory_state.rs) (verified locally)
- **Day boundaries.** The v1 timing is `days_elapsed = (now − crt)/86400`. The v2 timing uses `crt` plus `creationOffset`, the current UTC offset and `rollover` (hour). — [scheduler/timing.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/timing.rs)

### Inferences
- **Protobuf decoding without the `anki` package.** Only a handful of protobuf fields are needed: template q/a (1, 2), notetype kind and css (1, 3), deck `config_id` (1 inside `kind`), deck-config `fsrs_params_6` (6, packed float32), `desired_retention` (37, fixed32) and `learn_steps`/`relearn_steps` (1, 2). Two options:
  - A small hand-written wire-format decoder (varint, length-delimited, fixed32), about 50 lines of Python. This avoids depending on `protobuf`.
  - Vendoring Anki's .proto files and compiling them with `protoc`, which brings in the `protobuf` runtime. Note the .proto files are AGPL too.
- **Simplest route to a uniform reader.** For schema 18, read the tables. For schema 11, read the JSON in `col`. Convert both into the app's own neutral notetype/deck model.
- **Rollover default.** An .apkg has no rollover setting (fresh config). Use Anki's default rollover of 4 am local time unless the user says otherwise; a .colpkg carries the real value.

### Gaps
- The exact JSON layout of schema-11 `decks` and `dconf` entries for filtered decks was not enumerated beyond the FSRS keys.
- How `fsrs_params_4/5/6` are chosen when several are set (FSRS-6 params take precedence in current Anki, per the field names) was not traced in code this session.

---

## 3. Rendering Anki card templates outside Anki; Python libraries; licensing

### Takeaway
Anki's template language looks like Mustache but differs from it:
- `{{Field}}` substitutes the raw field HTML, with no escaping.
- `{{#F}}…{{/F}}` and `{{^F}}…{{/F}}` test whether a field is non-empty, where "empty" means only whitespace and `<br>`/`<div>` tags.
- Filters are chained right-to-left, as in `{{text:cloze:Text}}`.
- `{{FrontSide}}` on the answer side becomes the rendered question.
- Special fields such as `Tags`, `Deck` and `Card` are available.
- Unknown fields raise errors.

Generic Mustache libraries (chevron, used by genanki) get these rules wrong. A faithful static renderer is roughly 200–300 lines of Python porting `template.rs`, `template_filters.rs` and `cloze.rs`. Alternatively, the official `anki` pylib (AGPL) can import a package into a throwaway collection and render cards headlessly at import time. That was verified locally, and the AGPL is not a practical problem for a private, undistributed app.

### Cited Findings
- **Tokenizing.** Handlebars are `{{ … }}`. HTML comments `<!-- … -->` are kept as a Comment token, so handlebars inside them are not processed. A template that starts with `{{=<% %>=}}` switches to the legacy alternative delimiters `<% %>`. `#` opens a conditional, `^` a negated conditional, `/` closes one, and anything else is a replacement. — [rslib/src/template.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Filter order.** A replacement is split with `rsplit(':')`. The last segment is the field name and the remaining segments are filters applied innermost first, so `{{text:cloze:Text}}` runs `cloze`, then `text`. — [template.rs `parse_inner`](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Empty-field rule.** `field_is_empty` matches `^(?:[[:space:]]|</?(?:br|div)\ ?/?>)*$` (case-insensitive). — [template.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Conditionals.** A conditional is true if the field is in `nonempty_fields`. It is false if the field exists but is empty, or if the key is a cloze conditional (`c` followed by digits). Otherwise rendering fails with `NoSuchConditional`. — [template.rs `evaluate_conditional`, `is_cloze_conditional`](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Unknown field.** A replacement naming a field that does not exist yields `TemplateError::FieldNotFound`, and Anki shows an error card. — [template.rs `render_into`](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **FrontSide.** On the answer side, `{{FrontSide}}` is replaced by the first rendered question text. — [template.rs `render_card`](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Empty cards.** For a normal notetype, if the question renders with no non-empty fields, Anki returns an "empty front" message. For a cloze notetype, the card is empty when its cloze number (`card_ord + 1`) does not appear in any field. — [template.rs `render_card`, `cloze_is_empty`](https://github.com/ankitects/anki/blob/main/rslib/src/template.rs)
- **Special fields.** `FrontSide, Card, CardFlag, Deck, Subdeck, Tags, Type, CardID`. When rendering, `Tags` is the note's tags and `Type` is the notetype name. — [notetype/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/notetype/mod.rs); [notetype/render.rs](https://github.com/ankitects/anki/blob/main/rslib/src/notetype/render.rs)
- **Built-in filters.** `text` (strip HTML), `furigana`/`kanji`/`kana` (ruby text for `漢字[かんじ]`), `type` (emits a `[[type:Field]]` placeholder; the modifiers `cloze`, `nc` and `ci` fold into `[[type:cloze:…]]` etc.), `type-cloze`, `type-nc`, `hint`, `cloze`, `cloze-only`, `tts <opts>` (emits `[anki:tts lang=…]…[/anki:tts]`), and the empty filter. Unrecognized filters, such as add-on filters, are skipped in full rendering. — [rslib/src/template_filters.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template_filters.rs)
- **`hint:` output.** If the text is non-empty, it emits `<a class=hint href="#" onclick="this.style.display='none';document.getElementById('hint<id>').style.display='block';return false;">{field_name}</a><div id="hint<id>" class=hint style="display: none">{text}</div>`, where the id is a hash of the text and field name. This needs JavaScript or a CSS/details-based replacement. — [template_filters.rs `hint_filter`](https://github.com/ankitects/anki/blob/main/rslib/src/template_filters.rs)
- **Cloze syntax and numbering.**
  - Opening is `{{c` + comma-separated digits + `::`. Several ordinals are allowed (`{{c1,2::…}}`); they are de-duplicated and sorted. Nested clozes are allowed.
  - A hint follows `::` inside the cloze.
  - A `}}` inside MathJax `\( \)` or `\[ \]` closes only a cloze opened inside the same expression.
  - One card is generated per cloze number found in any field, with `ord = number − 1`, capped at 499.
  — [rslib/src/cloze.rs](https://github.com/ankitects/anki/blob/main/rslib/src/cloze.rs); [notetype/cardgen.rs](https://github.com/ankitects/anki/blob/main/rslib/src/notetype/cardgen.rs)
- **Cloze HTML output.**
  - Active cloze, question side: `<span class="cloze" data-cloze="{html-attr-escaped content}" data-ordinal="N">[{hint or ...}]</span>`.
  - Active cloze, answer side: `<span class="cloze" data-ordinal="N">content</span>`.
  - Inactive cloze: `<span class="cloze-inactive" data-ordinal="N">content</span>`.
  - If the field contains no active cloze, the `cloze:` filter returns an empty string.
  - Inside MathJax, HTML is stripped after cloze rendering.
  - Image-occlusion clozes become `<div class="cloze" …>` with data attributes.
  — [cloze.rs `reveal_cloze`, `reveal_cloze_text`, `cloze_filter`](https://github.com/ankitects/anki/blob/main/rslib/src/cloze.rs)
- **Headless rendering with official pylib (verified locally).**
  - `Collection(tmp)` + `col.import_anki_package(ImportAnkiPackageRequest(package_path=…, options=ImportAnkiPackageOptions(with_scheduling=True, with_deck_configs=True)))` imported a latest-format apkg.
  - `card.question()` returned `'<style>.card {…}</style>Q <img src="pic.png">'`, so the notetype CSS is prepended in a `<style>` tag.
  - A Cloze note rendered `<span class="cloze" data-cloze="Paris" data-ordinal="1">[city]</span> is in <span class="cloze-inactive" data-ordinal="2">France</span>`.
  - `card.memory_state` returned stability 2.3065 and difficulty 2.111, and both revlog rows were imported.
  — [pylib/anki/collection.py](https://github.com/ankitects/anki/blob/main/pylib/anki/collection.py); [PyPI anki 26.9.3](https://pypi.org/project/anki/) (verified locally)
- **`anki` package facts.**
  - 26.9.3, license `AGPL-3.0-or-later`, requires Python ≥3.10.
  - abi3 wheels for macOS arm64 (`macosx_12_0_arm64`, about 9.2 MB) and x86_64.
  - Dependencies: `decorator, markdown, orjson, protobuf>=6,<8, requests[socks], typing-extensions`.
  - The legacy `anki.importing`/`anki.exporting` modules were removed in 26.09b1 (#5153). Use `import_anki_package`/`export_anki_package`; shims were added later (#5547).
  — [PyPI anki](https://pypi.org/project/anki/); [commit d4fdbef](https://github.com/ankitects/anki/commit/d4fdbef); [commit b758186](https://github.com/ankitects/anki/commit/b758186)
- **License headers.** Every Anki source file carries "License: GNU AGPL, version 3 or later". — [meta.rs header](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/meta.rs)
- **genanki** (0.13.1, last release 2023-11-12, MIT) is a writer only. It uses `chevron` (generic Mustache) as a "partial reimplementation of req computing logic from Anki … instead of Anki's custom mustache". Dependencies: `cached-property, frozendict, chevron, pyyaml`. — [PyPI genanki](https://pypi.org/project/genanki/); [genanki/model.py](https://github.com/kerrickstaley/genanki/blob/main/genanki/model.py)
- **ankipandas** (0.3.15, last release 2023-10-11, MIT) reads a profile's `collection.anki2` and needs pandas and numpy. Its `raw.py` handles both "all info in the `col` table" and "separate `notetypes` and `decks` tables" layouts. It does not open .apkg zips or zstd files. — [PyPI ankipandas](https://pypi.org/project/ankipandas/); [ankipandas raw.py](https://github.com/klieret/AnkiPandas/blob/master/ankipandas/raw.py)
- **Other PyPI readers, all MIT and old:** AnkiTools 0.3.7 (last release 2018-07-12), anki-export 0.1.4 (2022-02-06), ankisync2 0.3.4 (2022-02-07). — [PyPI AnkiTools](https://pypi.org/project/AnkiTools/); [PyPI anki-export](https://pypi.org/project/anki-export/); [PyPI ankisync2](https://pypi.org/project/ankisync2/)

### Inferences
- **Two viable architectures:**
  - **(A) Own renderer.** Write a pure-Python reader and renderer: zipfile + zstd + sqlite3 + a small protobuf decoder + a port of the template/cloze rules above. This has the fewest dependencies and the user controls it. The cost is matching edge cases (nested clozes, MathJax-aware closing, `{{=<% %>=}}`, error cards).
  - **(B) Use `anki` pylib at import time only.** Import into a temp collection, call `card.question()`/`card.answer()` to get static HTML, read the revlog and `card.memory_state`, then discard the temp collection. This gives exact fidelity, including add-on-free filters, FrontSide and cloze, for a ~9 MB wheel plus protobuf/orjson.
  - For a private Mac app, B is the fastest way to correct output; A avoids the AGPL and pylib API churn (the importers were just removed and re-shimmed in 26.09).
- **AGPL.** Obligations are triggered by conveying the program to others, or under §13 by letting users interact with it over a network. A private, offline, personal-use app that is never distributed triggers neither. If the app is ever shared, bundling or porting Anki code would require releasing the app under the AGPL. Reimplementing the format from this description, or using the MIT/BSD FSRS libraries, avoids that. This is a general reading of the AGPL, not legal advice.
- **AnkiTools, anki-export and ankisync2 all predate the 2.1.50 zstd/protobuf format** (2018–2022), so they should not be relied on for current exports. This is inferred from their release dates; their code was not tested.
- **Static rendering of `type:`.** The `[[type:Field]]` placeholder should be replaced by the app's own input box, or removed. On the answer side, Anki's GUI swaps the placeholder for a comparison view; see [text.rs `TYPE_TAG`](https://github.com/ankitects/anki/blob/main/rslib/src/text.rs).
- **Mapping to the app's note types:**
  - Basic: one template.
  - Basic and reversed: two templates; the second has q=`{{Back}}`.
  - Basic (optional reversed): card 2's q is wrapped in `{{#Add Reverse}}…{{/Add Reverse}}`. That card only exists if the field is non-empty.
  - Cloze: `kind=1`, one template; cards come from the cloze numbers.
  - A custom "Mastery Problem" type should be matched by notetype name and field names. Use `original_stock_kind` and `original_id` (config fields 9 and 10) to recognize stock types that the user has renamed.
  — [notetypes.proto](https://github.com/ankitects/anki/blob/main/proto/anki/notetypes.proto) (verified template bodies locally)

### Gaps
- How `{{#c1}}`-style cloze conditionals become "non-empty" (whether `nonempty_fields` includes `cN` for the current card) was not traced in `notetype/render.rs`.
- How `card.answer()` turns `[sound:…]` into `[anki:play:…]` tags was observed only partially and was not documented.

---

## 4. Media: where references appear, name mapping, safe handling of HTML/JS in templates

### Takeaway
Fields reference media through HTML `src`/`data` attributes on `img`, `audio`, `video`, `object` and `source` tags, and through `[sound:filename]`. LaTeX images (`latex-*.png`/`.svg`) are referenced as well. Notetype templates and CSS pull in underscore-prefixed files (for example `_font.woff`) through `@import`/`url()` or direct references. Inside packages, media is stored under numeric names mapped by the media map. Filenames are NFC-normalized and unsafe names are rejected. Templates can contain arbitrary JavaScript, so a static renderer should sandbox or strip it.

### Cited Findings
- **HTML media regex.** `HTML_MEDIA_TAGS` matches `<img|audio|video|object|source …>` with `src` or `data` attributes, quoted (double or single) or unquoted. Filenames are HTML-entity-decoded (`fname_decoded`). — [rslib/src/text.rs](https://github.com/ankitects/anki/blob/main/rslib/src/text.rs)
- **Sound tags.** `[sound:(.+?)]` (`AV_TAGS`, `SOUND_TAG`). — [text.rs](https://github.com/ankitects/anki/blob/main/rslib/src/text.rs)
- **Underscore files.** `UNDERSCORED_CSS_IMPORTS` matches `@import "_x.css"` and `url(_x)` in CSS. `Notetype::gather_media_names` exports the underscore-prefixed files referenced in the CSS and in each template's q/a format. — [text.rs](https://github.com/ankitects/anki/blob/main/rslib/src/text.rs); [notetype/mod.rs `gather_media_names`](https://github.com/ankitects/anki/blob/main/rslib/src/notetype/mod.rs)
- **What gets exported.** The apkg exporter collects media names from every field via `extract_media_refs`, plus LaTeX output filenames (`extract_latex`, PNG or SVG depending on the notetype's `latex_svg`), keeping only names that pass `filename_is_safe`. — [import_export/gather.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/gather.rs)
- **Filename normalization.** `normalize_filename`: "The filename is normalized to NFC. Any problem characters are removed. Windows device names like CON and PRN have '_' appended. The filename is limited to 120 bytes." On Apple platforms, NFD names on disk are accepted as NFC. — [rslib/src/media/files.rs](https://github.com/ankitects/anki/blob/main/rslib/src/media/files.rs)
- **Zip naming.** Media files are named `"0"`, `"1"`, … inside the zip and are zstd-compressed in latest-format packages. The legacy map is JSON `{"0":"pic.png"}`; the latest map is protobuf `MediaEntries` with name, size and sha1. — [colpkg/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/package/colpkg/export.rs) (verified locally)
- **Scripts in templates.** Built-in filters emit inline JavaScript (`hint:` uses `onclick`), and `type:` relies on Anki's GUI code. — [template_filters.rs](https://github.com/ankitects/anki/blob/main/rslib/src/template_filters.rs)

### Inferences
- **Import procedure.**
  1. Copy each media file into the app's own media folder under its normalized name.
  2. If the name already exists with different content, rename it (for example add a hash suffix) and rewrite the references in the imported fields and templates.
  3. Use the sha1 in latest-format maps to deduplicate cheaply; legacy maps need hashing.
- **Rewriting references.** Use the same regexes (`src|data` on media tags, `[sound:…]`, underscore files in CSS and templates). Handle HTML entities in filenames: decode them for lookup, re-encode when writing back.
- **Safety for static HTML.**
  - Render in the app's web view with a strict CSP (`script-src 'none'`, or a whitelist), and serve media from a local scheme or directory.
  - Strip `<script>`, `on*=` attributes and `javascript:` URLs from imported templates and fields, or keep them only for templates the user trusts.
  - Replace `hint:` with a `<details>`-based equivalent and `[[type:…]]` with the app's own input.
  - Shared decks from the internet can carry arbitrary JavaScript.
- **Math.** MathJax delimiters `\( \)` and `\[ \]` stay in the HTML. The app needs its own MathJax or KaTeX to display them. Anki's LaTeX (`[latex]…[/latex]`) appears as pre-generated `latex-<hash>.png/svg` media only if the exporter had generated it.

### Gaps
- The exact list of characters removed by `disallowed_char` was not extracted.
- Behavior on Mac filesystems that are case-insensitive but case-preserving, when two media names differ only by case, was not investigated.

---

## 5. Anki "Notes in Plain Text" export/import headers and escaping

### Takeaway
Plain-text exports from Anki 2.1.54 and later start with `#key:value` header lines:
- `#separator:tab` and `#html:true|false`
- optionally `#guid column:N`, `#notetype column:N`, `#deck column:N`, `#tags column:N` (1-based)

The body is CSV produced by the Rust `csv` crate: tab-delimited, RFC-4180-style double-quote quoting with `""` escaping, and `#` lines treated as comments. Note exports put the columns in the order guid, notetype, deck, fields…, tags. When `#html:false`, the importer HTML-escapes field text and converts `\n` to `<br>`.

### Cited Findings
- **Header keys parsed** (key compared case-insensitively after trim): `separator`, `html`, `tags`, `columns`, `notetype`, `deck`, `notetype column`, `deck column`, `tags column`, `guid column`, `match scope`, `if matches`. Unknown keys are ignored. A first line starting with `tags:` (without `#`) is also accepted as global tags. A UTF-8 BOM is stripped. — [text/csv/metadata.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/metadata.rs)
- **Separator values.** Accepted as names (`comma, semicolon, tab, space, pipe, colon`) or the literal character. If not specified, the delimiter is detected by checking the first 8 KB for, in order, Tab, Pipe, Semicolon, Colon, Comma, then falling back to Space. — [metadata.rs `delimiter_from_value`, `delimiter_from_reader`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/metadata.rs); [import_export.proto `Delimiter`](https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto)
- **Header value semantics.**
  - `#notetype:` and `#deck:` take a name or numeric id. A deck name that does not exist is kept as a name and created on import (2.1.55+).
  - `… column:` values are column numbers.
  - The manual says headers were introduced in 2.1.54+ and that `columns` labels are separated by the separator.
  — [metadata.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/metadata.rs); [Anki manual: Text files](https://docs.ankiweb.net/importing/text-files.html); [changes 2.1.50–59](https://changes.ankiweb.net/changes/2.1.50-59.html)
- **Reader settings.** `csv::ReaderBuilder::new().has_headers(false).flexible(true).comment(Some(b'#')).delimiter(...)`. Rows may have different column counts, and any line starting with `#` is skipped. — [text/csv/import.rs `build_csv_reader`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/import.rs)
- **HTML handling.** If `is_html` is true, text is used as-is. Otherwise `htmlescape::encode_minimal(s).replace('\n', "<br>")`, so the test case `"<hr>"` imports as `&lt;hr&gt;`. — [import.rs `stringify_fn`](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/import.rs)
- **Exporter.**
  - The delimiter is always Tab. The file starts with `#separator:tab\n#html:{true|false}\n`, followed by `#guid column:N`, `#notetype column:N`, `#deck column:N` and `#tags column:N` as applicable.
  - Columns: `guid` (1), then notetype, then deck, then the note's fields, padded to the maximum field count across exported notetypes, then tags as space-separated text.
  - `<style>…</style>` blocks and `[[type:…]]` are stripped from fields. With `with_html=false`, fields go through `html_to_text_line`.
  - `ExportNoteCsvRequest` fields: `with_html, with_tags, with_deck, with_notetype, with_guid`.
  — [text/csv/export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/export.rs); [import_export.proto](https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto)
- **Escaping per the manual.** Put fields containing newlines or the separator in double quotes and double any internal `"`. In HTML mode, escape `<`, `>` and `&` as entities. Multi-line cloze fields should use `<br>` rather than quoted newlines. — [Anki manual: Text files](https://docs.ankiweb.net/importing/text-files.html)
- **Duplicates and GUIDs.** The first field identifies duplicates within the notetype (optionally within notetype and deck). "If a GUID is provided, and already exists in the collection, a duplicate will not be created." The `#if matches` header has been settable since 2.1.58 ("Duplicate handling policy can be specified in the csv file header"). — [Text files manual](https://docs.ankiweb.net/importing/text-files.html); [changes 2.1.58](https://changes.ankiweb.net/changes/2.1.50-59.html)
- **Exported deck names** come from `get_all_deck_names()`, which converts `\x1f` to `::`, so hierarchical decks appear as `Parent::Child`. — [export.rs](https://github.com/ankitects/anki/blob/main/rslib/src/import_export/text/csv/export.rs); [storage/deck/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/storage/deck/mod.rs)

### Inferences
- **Python parsing.** Read leading `#` lines yourself, then feed the rest to `csv.reader(f, delimiter=sep, quotechar='"', doublequote=True, strict=False)`, skipping later lines that start with `#`. This matches Anki's settings. Python's `csv` has no comment option, so filter lines before parsing, but make sure a quoted multi-line field whose continuation line begins with `#` is not dropped (only filter at record starts).
- **Notetype resolution.** If `#notetype column` is present, each row names its notetype, and field-to-column mapping is positional after the meta columns. The app needs a name-based mapping to its own types, for example "Basic" or "Mastery Problem". Without that header, the user must choose a notetype.
- **What plain text cannot carry.** A plain-text export has no media files, scheduling, review history or templates. Only field HTML that references media by name survives.

### Gaps
- The exact accepted values for `#if matches` (`DupeResolution::from_text`) and `#match scope` were not extracted from code.

---

## 6. Rebuilding FSRS state from an Anki review log (py-fsrs `reschedule_card` / `ReviewLog`; how Anki itself computes memory state)

### Takeaway
Anki computes memory state with fsrs-rs (version 6.6.2 in Anki 26.09):
1. Take the card's revlog in time order and drop cram entries (type 3, factor 0).
2. Keep the history from the start of the last learning sequence. A Reset entry (type 4, factor 0) cuts off everything before it.
3. Drop entries with ease 0 (manual set-due, reset, reschedule).
4. Convert each entry to `(rating, delta_t)`, where `delta_t` is the number of Anki days (rollover-aware) since the previous review. Same-day reviews get `delta_t = 0`.
5. If the history is incomplete (for example the card started as an SM-2 review), seed the state from the first graded interday review with `memory_state_from_sm2(ease, ivl, historical_retention)`.

py-fsrs 6.3.2's `reschedule_card` simply replays `review_card` in timestamp order and measures elapsed time as `timedelta.days`, i.e. 24-hour blocks. So replaying raw Anki timestamps can disagree with Anki (verified: S = 9.30 vs 12.65 on the same history). Map Anki day numbers to synthetic UTC datetimes before replaying, or compute the state with `fsrs_rs_python.FSRS.memory_state()`.

### Cited Findings
- **History selection** (`reviews_for_fsrs`), walking backwards from the latest entry:
  - Skip cramming entries.
  - Record the first user-graded interday entry (`ivl >= 1` or `ivl <= -86400`) after the cutoff.
  - A user-graded Learning entry marks the start of the last learn block and sets `revlogs_complete = true`.
  - A Reset entry stops the scan, keeping only what came after it. If nothing graded follows the reset, the card has no history.
  - When training, cards without learning entries are ignored. Outside training, history starts at the first graded entry.
  - Then `entries.retain(has_rating_and_affects_scheduling)`.
  - `delta_t = prev.days_elapsed(next_day_at) − cur.days_elapsed(next_day_at)`, where `days_elapsed = (next_day_at − id_secs)/86400`.
  — [scheduler/fsrs/params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- **Training items.** One `FSRSItem` per review with `idx ≥ 1` and `delta_t > 0`, each containing all reviews up to that point. Items are sorted by revlog id. `review_count` counts the filtered revlogs. — [params.rs `reviews_for_fsrs`, `fsrs_items_for_training`](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- **Incomplete history.** If `revlogs_complete` is false, the starting state is `fsrs.memory_state_from_sm2(ease_factor/1000 (2500 if 0), max(ivl,1), historical_retention)`. If the factor is ≤ 1100, the entry was written by FSRS and difficulty is recovered as `(ease − 0.1)·9 + 1`. The first review is removed from the item, having been turned into the starting state. If no revlog is usable and the card is not new and has `ivl > 0`, the state is inferred from the card's current ease and interval (`memory_state_from_sm2`). — [scheduler/fsrs/memory_state.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/memory_state.rs)
- **Relevant revlog flags.**
  - `is_reset()`: type 4 Manual with factor 0, created by Forget/reset.
  - Set Due Date: type 4 with non-zero factor; ease 0, so filtered out as unrated.
  - `is_cramming()`: type 3 with factor 0, i.e. a filtered deck with rescheduling disabled. Type 3 with non-zero factor (early review in a rescheduling filtered deck, or "Grade Now") is kept.
  - Rescheduled: type 5 with ease 0, filtered out.
  — [revlog/mod.rs](https://github.com/ankitects/anki/blob/main/rslib/src/revlog/mod.rs)
- **Ignore cutoff.** Deck option `ignore_revlogs_before_date` (string, field 46) is converted to ms and limits history (`ignore_revlogs_before_ms_from_config`). — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs); [deck_config.proto](https://github.com/ankitects/anki/blob/main/proto/anki/deck_config.proto)
- **Anki pins fsrs 6.6.2** (Cargo.lock; commit "bump fsrs to 6.6.2", 2026-09-02). — [Cargo.toml](https://github.com/ankitects/anki/blob/main/Cargo.toml); [commit b9d69a0](https://github.com/ankitects/anki/commit/b9d69a0)
- **py-fsrs 6.3.2 API.**
  - `Scheduler(parameters=DEFAULT_PARAMETERS (21 floats), desired_retention=0.9, learning_steps=(1m,10m), relearning_steps=(10m,), maximum_interval=36500, enable_fuzzing=True)`.
  - `Card(card_id, state=Learning, step, stability, difficulty, due, last_review)`.
  - `ReviewLog(card_id, rating, review_datetime, review_duration)`.
  - `reschedule_card(card, review_logs)` sorts the logs by `review_datetime`, starts from a fresh `Card(card_id, due=card.due)` and calls `review_card` for each log, raising `ValueError` if a log's `card_id` does not match.
  - `review_card` requires `review_datetime` to be timezone-aware UTC (otherwise `ValueError`).
  - `days_since_last_review = (review_datetime − card.last_review).days`. A value below 1 triggers the short-term stability update. `get_card_retrievability` uses `max(0, (now − last_review).days)`.
  — [py-fsrs scheduler.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py); [card.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/card.py); [review_log.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/review_log.py)
- **py-fsrs changes since 6.3.1:** "Fix same-day Hard stability floor" (#155, 2026-07-28); 6.3.2 was released 2026-08-09. — [py-fsrs commits](https://github.com/open-spaced-repetition/py-fsrs/commits/main); [PyPI fsrs](https://pypi.org/project/fsrs/)
- **Verified equivalence and pitfall** (both libraries with the same default 21 parameters; fuzz off; history Good, Good same day, Good +1d, Again +4d, Good same day, Good +6d, Hard +20d):
  - When later-day reviews happened at an earlier clock time than the previous review, `reschedule_card` gave S = 9.3048, D = 8.2364, while `fsrs_rs_python.FSRS.memory_state` with day-number `delta_t`s gave S = 12.6461, D = 8.2364.
  - With clock times arranged so that floor(24 h) equals the day difference, both gave S = 12.6461, D = 8.2364. Difficulty matched in both runs.
  — [PyPI fsrs](https://pypi.org/project/fsrs/); [PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/) (verified locally)

### Inferences
- **Conversion recipe for Anki revlog → py-fsrs.**
  1. Group the revlog by `cid` and sort by `id`.
  2. Apply Anki's filters: drop type 3 with factor 0; truncate at the last Reset (type 4, factor 0); drop ease 0. Anki's last-learning-block rule is optional; Anki uses it so that relearned-from-scratch cards start clean.
  3. Map ease to `Rating(ease)` (1 = Again, 2 = Hard, 3 = Good, 4 = Easy). For v1-scheduler learning or relearning entries (type 0 or 2), ease 3 meant Easy; detect v1 via `schedVer` = 1 in config, or via pre-2.1 timestamps.
  4. Compute each review's Anki day number `day = floor((id/1000 − rollover_offset − tz_offset)/86400)`, using rollover 4 am and the user's local time zone.
  5. Build `review_datetime = EPOCH_UTC + timedelta(days=day, seconds=k)`, where k is the index within the day. Then `.days` differences equal Anki's `delta_t`, and same-day reviews stay below 1 day.
  6. Call `scheduler.reschedule_card(Card(card_id=cid), logs)`.
  7. Finally set `card.due` from the app's own policy, or from Anki's `cards.due`/`ivl` if the schedule should be preserved exactly.
- **Alternative: compute memory state directly.** `fsrs_rs_python.FSRS(params).memory_state(FSRSItem([FSRSReview(rating, delta_t), …]), starting_state)` reproduces Anki's algorithm, including the SM-2 seed via `memory_state_from_sm2`. Afterwards, set py-fsrs `Card(state=Review, stability=S, difficulty=D, last_review=<real UTC datetime of last review>, due=…)` to continue scheduling with py-fsrs.
- **Cheapest path.** If the package comes from Anki with FSRS enabled, `cards.data` already holds `s`, `d` and `lrt`. These can be imported directly as py-fsrs `stability`, `difficulty` and `last_review`, with no recomputation, as long as the parameters (deck config `fsrs_params_6`) are imported too.
- **Card state mapping.** Anki `type` 0 → new (no state). 1 → Learning, with `left` encoding the remaining steps. 2 → Review. 3 → Relearning. Simplest approach: map learning and relearning cards to py-fsrs Learning or Relearning with step 0, or graduate them.
- **py-fsrs learning steps.** py-fsrs's `learning_steps` affect only the state machine and due date, not S and D for same-day reviews; D matched in the verification. So differing step settings between Anki and the app do not change memory state; only `delta_t` handling matters.

### Gaps
- The exact formula for Anki's `next_day_at` (`sched_timing_today_v2_new`: how `creationOffset`, `localOffset` and `rollover` combine) was not transcribed. The recipe above assumes "local midnight + rollover hour", which is the documented behavior but was not traced line-by-line.
- I did not verify how Anki handles revlog entries whose `id` is not a real timestamp (for example entries imported from other apps).

---

## 7. FSRS optimizer without PyTorch (fsrs-rs-python), optimal retention, minimum data; FSRS-7 status (Nov 2026)

### Takeaway
`fsrs-rs-python` 0.9.3 (2026-08-31) wraps the Rust crate `fsrs` 6.6.2. It ships about 1.3 MB native wheels for macOS arm64 and x86_64 on CPython 3.9–3.14 with no Python dependencies. It provides `compute_parameters`, `memory_state`, `memory_state_from_sm2`, `next_states`, `evaluate`, `simulate` and `optimal_retention` (all verified working locally) and returns standard 21-parameter FSRS-6 weights that py-fsrs accepts. In the Rust code:
- Fewer than 8 training items after filtering returns the defaults unchanged.
- Fewer than 64, or first-review-only data, fits only the 4 initial-stability parameters.
- Full training needs at least 64 items.

The fsrs-rs-python repo and PyPI metadata declare no license (the underlying fsrs-rs is BSD-3-Clause). FSRS-7 is under active development in fsrs-rs `main` (Sept–Oct 2026 commits) but is not in any released crate (latest 6.6.2), not in py-fsrs (6.3.2) and not in Anki 26.09.x, whose deck config has only `fsrs_params_4/5/6`.

### Cited Findings
- **fsrs-rs-python 0.9.3 packaging.**
  - Uploaded 2026-08-31, `Requires-Python >=3.9`, no `requires_dist`.
  - Wheels: `cp311`/`cp312`/`cp313`/`cp314` × `macosx_11_0_arm64` and `macosx_10_12_x86_64`, plus `cp39`; also Linux and Windows.
  - The macOS arm64 cp312 wheel contains a 1,298,368-byte `.so`, an `__init__.pyi` and a CycloneDX SBOM listing `fsrs 6.6.2 (BSD-3-Clause)`, `pyo3 0.29.2` and `ndarray 0.17.2`.
  — [PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/) (wheel downloaded and inspected locally)
- **License status.** The PyPI metadata has empty `license`/`license_expression`. The repo at HEAD b013db2 has no LICENSE file, and its `Cargo.toml`/`pyproject.toml` have no license field. The README still says it uses "burn-rs, instead of pytorch". — [fsrs-rs-python repo](https://github.com/open-spaced-repetition/fsrs-rs-python); [PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/)
- **fsrs-rs license** is BSD 3-Clause ("Copyright (c) 2023, Open Spaced Repetition"). At tag v6.6.2, `burn` is only a dev-dependency; the runtime dependencies are `itertools`, `log`, `ndarray`, … — [fsrs-rs LICENSE](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/LICENSE); [fsrs-rs v6.6.2 Cargo.toml](https://github.com/open-spaced-repetition/fsrs-rs/blob/v6.6.2/Cargo.toml)
- **API (from `fsrs_rs_python.pyi`).**
  - `FSRS(parameters)`; an empty list means defaults.
  - `.compute_parameters(fsrs_items, card_ids=None, enable_short_term=True, num_relearning_steps=None, training_config=None) -> List[float]`.
  - `.memory_state(item, starting_state=None)`, `.memory_state_batch(...)`, `.historical_memory_states(...)`, `.memory_state_from_sm2(ease_factor, interval, sm2_retention)`, `.next_states(memory_state, desired_retention, days_elapsed)`, `.next_interval(...)`, `.evaluate(items) -> ModelEvaluation(log_loss, rmse_bins)`, `.benchmark(...)`.
  - `FSRSItem(reviews)`, `FSRSReview(rating, delta_t)`, `MemoryState(stability, difficulty)`.
  - `TrainingConfig(num_epochs=5, batch_size=512, seed=2023, learning_rate=4e-2, max_seq_len=256, gamma=1.0)`.
  - Module functions: `simulate(w, desired_retention, config, seed)`, `optimal_retention(config: SimulatorConfig, parameters, cards=None, target=None) -> float`, `default_simulator_config()`, `evaluate_with_time_series_splits(...)`, `filter_outlier(...)`, `check_and_fill_parameters(...)`, `DEFAULT_PARAMETERS`.
  — [fsrs_rs_python.pyi](https://github.com/open-spaced-repetition/fsrs-rs-python/blob/main/fsrs_rs_python.pyi)
- **Minimum-data logic** (fsrs-rs v6.6.2 `compute_parameters`):
  - Items must have reviews with ratings in 1..=4, otherwise `InvalidInput`.
  - After `prepare_training_data`: `if train_set.len() < 8 { return Ok(DEFAULT_PARAMETERS) }`.
  - Then `initialize_stability_parameters` (which can return `NotEnoughData`).
  - `if train_set.len() == dataset_for_initialization.len() || train_set.len() < 64 { return Ok(initialized_parameters) }`, i.e. only w0–w3 fitted.
  - Otherwise recency-weighted training, dropping items longer than `max_seq_len`.
  — [fsrs-rs v6.6.2 src/training.rs](https://github.com/open-spaced-repetition/fsrs-rs/blob/v6.6.2/src/training.rs)
- **Local behavior (synthetic random data, verified).**
  - `DEFAULT_PARAMETERS` has 21 values starting `0.212, 1.2931, 2.3065, 8.2956, …, 0.1542`, identical to py-fsrs 6.3.2's `DEFAULT_PARAMETERS`.
  - `compute_parameters` returned defaults unchanged for 13 and 102 items, and changed 17 of 21 parameters for 1,041 items, in well under a second.
  - `optimal_retention(default_simulator_config() with deck_size=500, learn_span=100, DEFAULT_PARAMETERS)` returned 0.70 in about 0.3 s.
  - `memory_state_from_sm2(2.5, 10, 0.9).stability` = 10.0.
  — [PyPI fsrs-rs-python](https://pypi.org/project/fsrs-rs-python/) (verified locally)
- **Example training pipeline in the repo** (`examples/train_csv.py`): group by card, keep entries from the last learning block, build cumulative `FSRSItem`s with day-level `delta_t`, sort by date, then `FSRS([]).compute_parameters(items)`. — [examples/train_csv.py](https://github.com/open-spaced-repetition/fsrs-rs-python/blob/main/examples/train_csv.py)
- **py-fsrs's optimizer** (`fsrs[optimizer]` extra) imports `torch`, `pandas` and `tqdm`, with `mini_batch_size = 512`. — [py-fsrs optimizer.py](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/optimizer.py); [PyPI fsrs](https://pypi.org/project/fsrs/)
- **Anki's minimum data.** Anki's `compute_params` returns the current parameters unchanged when `fsrs_items == 0`, and otherwise relies on fsrs-rs's thresholds. — [params.rs](https://github.com/ankitects/anki/blob/main/rslib/src/scheduler/fsrs/params.rs)
- **FSRS-7 in fsrs-rs `main` (unreleased).**
  - Recent commits: "Remove Burn dependency after FSRS-7 optimization" (#447, 2026-09-15), "fix: default empty parameters to FSRS-7" (#455, 2026-09-18), "Align FSRS-7 training with srs-benchmark" (#463, 2026-09-28), "Remove FSRS-7 parameter pre-training" (#462) and "Train FSRS-7 on two threads…" (#465, 2026-10-01).
  - The README on `main` says "FSRS-6 and FSRS-7 are selected from the parameter count".
  - `main`'s Cargo.toml still says version 6.6.2, and crates.io's latest is 6.6.2 (2026-08-29); there is no 7.x release.
  — [fsrs-rs commits](https://github.com/open-spaced-repetition/fsrs-rs/commits/main); [fsrs-rs README](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/README.md); [crates.io fsrs](https://crates.io/crates/fsrs)
- **FSRS-7 elsewhere.**
  - py-fsrs `main` has no FSRS-7 code (latest commit 2026-08-09).
  - Anki's deck-config proto has only `fsrs_params_4`, `fsrs_params_5` and `fsrs_params_6`, and Anki 26.09 ships fsrs 6.6.2.
  - On the Anki forum (2026-06-05), FSRS-7 was described as an "in-process project" not yet merged or released, with "no PR for it in the Anki repo".
  — [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs); [deck_config.proto](https://github.com/ankitects/anki/blob/main/proto/anki/deck_config.proto); [Anki forum: When will Anki integrate FSRS-7?](https://forums.ankiweb.net/t/when-will-anki-integrate-fsrs-7/69997)

### Inferences
- **Recommended stack:**
  - **Scheduling:** py-fsrs 6.3.2 (pure Python, MIT, only `typing-extensions`).
  - **Optimizer, optimal retention and Anki-exact memory-state rebuild:** `fsrs-rs-python` 0.9.3 (about 1.3 MB, no Python dependencies, macOS arm64 wheels). Both use the same 21-parameter FSRS-6 vector, so optimized parameters can be passed straight to `fsrs.Scheduler(parameters=…)`.
  - **Data volume:** below about 64 training items (graded interday reviews after the first), expect defaults or only initial-stability fitting. Using Anki's history raises the starting data volume immediately.
- **License risk.** fsrs-rs-python has no declared license, so its terms are unclear. For private, undistributed use this is not a practical issue. Before ever redistributing the app, check the repo for a license or ask the maintainers. The underlying Rust crate is BSD-3-Clause, so a self-built binding (maturin + pyo3) would have clear terms.
- **Pinning FSRS-7 code.** If a future fsrs-rs 7.x release enables FSRS-7 by default for empty parameter lists (as `main` now does, #455), pin `fsrs-rs-python==0.9.3` or always pass explicit 21-length FSRS-6 parameters. That keeps the optimizer's output compatible with py-fsrs 6.x.
- **Optimal retention for problem solving.** `optimal_retention` uses a cost simulator (`SimulatorConfig.state_rating_costs`, `first_rating_prob`, etc.). For long, multi-minute problems, set these costs from the app's own review durations rather than the flashcard defaults; otherwise the "optimal" retention (0.70 with defaults) reflects flashcard timing.

### Gaps
- I could not open the fsrs-rs-python GitHub API (blocked in this session), so a license added through GitHub settings only, not as a file, would not have been visible. The cloned repo and PyPI metadata showed none.
- No primary source gives a date for FSRS-7's release or its integration into py-fsrs or Anki. The forum statement dates from June 2026, and the October 2026 fsrs-rs commits show active work but no release.
- The 13- and 102-item local runs used random synthetic data. Real Anki data may cross the 8/64 thresholds differently after `prepare_training_data`/outlier filtering.
