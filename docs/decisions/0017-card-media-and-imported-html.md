# ADR-0017: Card media from the app's own origin; imported Anki HTML drawn by a second sanitizer

- Status: Accepted
- Date: 2026-11-01

## Context

ADR-0012 left card images as "[figure: ...]": the CSP lets the page load images, sound, fonts
and stylesheets from 'self' only (ADR-0002), and pack media live in the pack database while the
student's own media (imported Anki decks, ADR-0015) are files in the profile's media store.
ADR-0015 also asked the page to draw `anki-card` HTML instead of passing it to the Markdown
renderer.

## Decision

### A read-only media route on the loopback server (`app/media.py`)

- `GET /media/user/<sha256 hex>[.ext]`: a file of the open profile's media store, by its
  content-addressed name (`core.storage.media`). `GET /media/pack/<pack id>/<name>`: a row of an
  attached pack's `media` table (`media/graph.svg`). Nothing else under `/media/` answers: not the
  folders (no listing), not a user name that is not exactly `<64 hex>[.ext]`, not a pack name with
  `.`/`..`/empty parts, backslashes, NULs or control characters. Names are checked before any
  lookup, and a pack name is only a key into the database, never a path. A symlink in the store
  is not followed.
- Only GET and HEAD (405 otherwise), one byte range (WKWebView will not play audio or video
  without `Accept-Ranges`), the content type of the extension (fixed table, otherwise
  `application/octet-stream`), `X-Content-Type-Options: nosniff`, `Cross-Origin-Resource-Policy:
  same-origin`, and a `Content-Security-Policy: default-src 'none'; sandbox` that keeps an SVG
  opened as a document from running anything (the page only ever uses them as `<img>`).
  Content-addressed files are cached as immutable; pack media are revalidated.
- `app.media.respond` is the whole route as a function. `MediaMiddleware` (WSGI) puts it in front
  of pywebview's own Bottle routes: `app/shell.py` installs it in the loopback adapter, with the
  open profile (`ProfileMedia`) as the source, no API lock, so a slow answer check never delays
  an image. The test harness calls the same function.
- **The CSP does not change.** `img-src`, `media-src`, `font-src`, `style-src` and `connect-src`
  already say 'self'; the media simply are on that origin now.

### Which file does a reference mean: `library_card_media`

A card's text names media by reference (`pic.png`, `media/graph.svg`, `_anki-nt-....css`), not by
file. New bridge method `library_card_media({card_id}) -> {"files": {reference: URL}}`: for an own
card its `user_media` links; for a pack card the images its Markdown names that the pack holds. The
page asks once per card (cached) and only for text that has an image or is Anki HTML; unknown
references are absent and show as notes, never as requests. `Api._storage_or_none` is the
non-bridge accessor the route uses.

### Drawing imported Anki HTML (`web/src/lib/anki-html.ts`)

- Card text starting `<div class="anki-card` is Anki HTML; everything else keeps the Markdown
  renderer. `Markdown.svelte` chooses, so every place cards are drawn (front, back, solution)
  gets it.
- A second sanitizer, independent of core's: DOMParser (an inert document; scripts do not run and
  nothing loads), then a node-by-node copy with `createElement` from the same allow-list of tags
  and attributes core uses (`tests/app/test_anki_allowlist.py` compares the lists), dropped tags
  with their content, no `id`/`href`/`on...`/`srcset`, `style` attributes cleaned (no foreign
  `url()`, CSS escapes, `expression`, `image-set`...). `src` and `url()` load only through the
  card's media map. No HTML string is ever inserted.
- `\( \)` and `\[ \]` in text nodes (not in `code`/`pre`) become KaTeX with `trust: false`.
- Each note type's stored, scoped CSS (`data-anki-css`, a media file of the card) is fetched
  once, its `url(_bg.png)`/`url(_font.woff)` rewritten to media URLs, and added as a `<style>`.
  The card is held back (up to 3 s) until it is in. Selectors are scoped by core to
  `.anki-nt-<hash>`; `.anki-host` has `contain: layout` so even `position: fixed` stays in the
  card's box. Page defaults for images, `.cloze` and notes have zero specificity, so the note
  type's CSS wins. In the dark theme the card's wrapper gets `anki-night` (core mapped
  `.nightMode` onto it); a theme change toggles the class without redrawing.
- Pack cards' Markdown images resolve through the same map, so `![..](media/parabola.svg)` is
  `/media/pack/test/media/parabola.svg`. Bundled figures (`figures/*.svg`) still win first.

### Tests

`tests/app/test_media.py` (traversal, listings, unknown names, methods, ranges, a real PNG and the
pack's SVG, behind the real pywebview server), `tests/app/test_anki_allowlist.py`, and
`tests/ui/test_anki_cards.py` (a Basic card with an image and scoped CSS, a cloze card, math,
hostile HTML, a pack image; each ends with zero requests off 127.0.0.1, no CSP violation and no
console error).

## Consequences

- A pack card whose card file is not in the pack's root resolves its images by the path as written
  (`posixpath.normpath`), not relative to its file; the shipped packs keep their cards at the root.
- Stock Cloze cards come out of the queue as `**answer**` inside the HTML: the queue marks the
  answer with Markdown bold (`core/queue/cloze.py`), which HTML does not read. The page shows the
  asterisks until the queue renders Anki clozes with `core.importers.anki.cloze` (`<span
  class="cloze">`).
- Unreferenced media files stay in the store (ADR-0011); the route serves any file in it by name.
- `[sound:...]` plays through `<audio controls preload="none">`; the media route's ranges make it
  work in WKWebView, not yet confirmed on the Mac.
