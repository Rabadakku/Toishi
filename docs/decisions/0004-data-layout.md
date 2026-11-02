# ADR-0004: Data layout — read-only packs + one user.db per profile

- Status: Accepted (schema comes in a later milestone)
- Date: 2026-11-01

## Decision

- **Location**: `~/Library/Application Support/com.toishi.app/` (`core.paths.app_data_dir`,
  platformdirs with the bundle id so data never splits across versions;
  `TOISHI_DATA_DIR` overrides it for tests). Never inside the `.app`, never in iCloud.
- **Packs** (problem/card content): SQLite files built by `content-tools/` into `packs/`
  and bundled or imported. Opened **read-only** (`file:...?mode=ro` URI). A pack is replaced
  as a whole file, never edited in place.
- **User data**: one `profiles/<profile>/user.db` per profile, opened in **WAL** mode with
  `synchronous=FULL`, holding reviews, FSRS state, settings and UI state (window geometry
  too: WKWebView keeps no browser storage here). It refers to pack content by stable ids
  (pack id + card uid), never by rowid, so packs can be rebuilt.
- **Durability**: each graded answer is committed in its own transaction the moment it is
  graded. Cmd+Q can end the process without exit handlers; nothing waits for shutdown.
- **Threads**: bridge calls arrive on worker threads; use one connection per thread (or one
  writer thread), never a shared `sqlite3.Connection`.
- **Backups**: the WAL file is part of the database; never copy `user.db` alone while open.
  Snapshots use `VACUUM INTO` / the backup API; `scripts/backup.sh` will copy those into
  iCloud Drive once `user.db` exists (it bundles the git repo today).

## Consequences

- Packs can be shared/rebuilt without touching progress; progress is a small file per profile.
- `synchronous=FULL` costs a little latency per review; one write per answer makes it negligible.
