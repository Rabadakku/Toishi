# ADR-0011: Storage schema v2 — real homes for four v1 stop-gaps

- Status: Accepted
- Date: 2026-11-01
- Supersedes: the "Storage (no schema change)" note on check reasons in ADR-0008

## Context

The cards (M2) and diagnosis (M4b) milestones shipped on schema v1 and parked four kinds of
data where they did not belong: template instance parameters as the first line of
`notes_md` ("template parameters: k = 3"), the source text of the student's own templates
in the import log's summary JSON, check reasons in the asking attempt's `extra` JSON, and
no store at all for the images of the student's own cards. This is the first migration of
a real student's progress database, so it has to be exact and crash-safe (DATA-3, BAK-2).

## Decision

### Schema (user.db v2, pack schema v2)

| Data | v1 stop-gap | v2 home |
|---|---|---|
| An instance's parameter set | first line of `notes_md` | `card.params` (packs) and `user_card.params`: the exact text its seed is derived from, `""` for a template without parameters; CHECK: only instances have one |
| An own template's source | `import_record.summary.files.*.templates` | `user_template (id, source_md, updated_at)`, keyed by the instances' `template_id`; kept after its instances retire |
| Own card images | — | files in the profile's `media/` folder, named `<sha256>[.ext]`; `user_media (card_id → user_card, ref, file)` maps each image reference as written in the card to a file |
| A check's reason | the asking attempt's `extra.diagnosis.checks[*].reason` | `pending_check.reason` (diagnostic checks store theirs too) |

- New columns go last (`ALTER TABLE ... ADD COLUMN`), so every table keeps the field order
  of its dataclass, and `user_card` keeps exactly the shape of a v2 pack's `card` table.
  `content_v2.sql` / `pack_v2.sql` build v2 packs whole; `migrate_user_v2.sql` is the user
  delta. The v1 files are untouched.
- `count_rows` (backup previews, export manifests) reads no v2 table, so v1 backups still
  preview.

### Migration (user.db v1 → v2)

- One step, one transaction: the DDL, the data moves and `PRAGMA user_version = 2` commit
  together, after the pre-migration backup (BAK-2), with foreign keys checked before commit.
  A crash anywhere leaves the untouched v1 (still usable by v1 code), or a complete v2; since
  nothing of the step can commit on its own, a retry always starts from that same v1 and
  gives the same v2 (a pre-migration backup is taken again first).
- Only text v1 itself wrote is moved: a `notes_md` is split only when the card is a
  template instance and the text has exactly v1's shape (prefix line, then nothing or a
  blank line and the template's own notes). A hand-written card whose notes happen to begin
  with the prefix keeps them.
- Template sources: the latest per template across `cards` import records in `(at, id)`
  order (what export read before), stamped with that record's time.
- Reasons: the first entry of the asking attempt's `extra.diagnosis.checks` with the same
  skill and kind (what `check_reason` read before); checks with no match stay NULL and are
  still composed, or read from the old place, as before.
- **Copied, not cut.** The attempt log and the import log are append-only (DATA-5, enforced
  by triggers), so the old text stays there as history. The new homes are what the app reads
  and writes from now on: diagnosis no longer puts reasons in `extra`, and new import records
  list template IDs, not their source.
- Media has nothing to move: v1 never kept the image bytes. The first import of a card file
  under v2 stores its images (`ImportPlan.media_changed`), even when its cards are unchanged.

### Packs are never migrated

A pack is a sealed, read-only, hashed file (DATA-1). The builder writes v2; readers take v1
and v2 (`PackInfo.schema_version` → `ContentReader(version=)`). A v1 pack's instances are
split at read time with the same function the migration uses, so a v1 pack reads back card
for card like a v2 pack built from the same sources, its content hash still verifies, and a
rebuild against it as the previous version keeps every revision (PACK-2).

### Media store (`core/storage/media.py`, `UserStore.media`, `Storage.media`)

- Content-addressed names: the same bytes are stored once, files are never changed or
  deleted, so an older backup of user.db (which holds only the table) still finds its images
  after a restore (BAK-3).
- A file is written atomically and fsynced before the rows that point at it commit; a failed
  import or a crash can leave an unreferenced file, never a reference to a missing one.
- Names are checked by the rule .meprofile export and import already applied to every entry
  (`unsafe_name`, now shared), plus the content-address shape, before they become paths.
- .meprofile: export refuses a profile whose cards point at a missing or damaged image
  (rather than write one that cannot be imported); import treats `user_media` as untrusted
  and refuses unsafe names, files the archive lacks, and files whose checksum does not match
  their name, before the profile is moved into place.
- Users: imports (`apply_import`), the editor (`StoredMedia(store.media, card_id, added)` as
  a Source's media; `UserMedia.set_card_media`), EXP-1 export (`export_media`).

### Smaller consequences

- `migrate()` runs the backup hook only for a database that existed before the call: a new
  profile created through baseline + v2 has nothing to back up.
- Undo compares and restores only the columns a snapshot has, so the last answer recorded
  under v1 (its `pending_check` snapshot has no `reason`) can still be undone exactly.
- Every public signature still works; v2 adds fields with defaults, new records, new methods.

## Evidence (tests)

- `tests/storage/test_migration_v2.py`: both frozen v1 databases (`user_v1.sql` and
  `user_v1_cards.sql`, the latter written by the v1 code through real imports and the
  diagnosis hook) are checked row by row and value by value after the migration, with seeds
  re-derived from the moved parameters; re-importing the same files changes nothing; export
  reads the moved sources; reasons read back; the last v1 answer undoes. The process is killed
  at chosen VM instructions throughout the step (SQLite progress handler) and by SIGKILL at
  random moments: before the commit it is always the untouched v1, after it a complete v2.
  The released v1 code (unpacked from git) refuses a v2 user.db, pack and .meprofile and leaves
  the file byte-for-byte untouched.
- `tests/cards/test_pack.py`: the v1 pack fixture reads back exactly like a v2 build.
- `tests/storage/test_media.py`, `tests/cards/test_import.py`: the store, links, the import
  and editor paths, and the .meprofile round trip with crafted archives.
