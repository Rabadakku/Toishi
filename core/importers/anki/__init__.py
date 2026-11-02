"""Anki deck import (milestone M7; IMP-2..8, docs/card-format.md "Anki compatibility").

Reading (whole-file problems raise AnkiImportError; nothing in a file is ever run)
    ``read_anki_file(path, deck=None) -> AnkiData``    by suffix: .apkg, .colpkg, or text
    ``read_package(bytes | path, name=, format=, limits=) -> AnkiData``
        legacy (collection.anki2/anki21, JSON media map) and latest (meta 08 03,
        zstd-streamed collection.anki21b, protobuf media map, compressed media); schema 11
        and 15-18; zip bombs, unsafe media names and damaged files refused
    ``read_text(bytes | str | path, name=, deck=, notetype=) -> AnkiData``
        "Notes in Plain Text" with every header line; headerless two-column = Basic

Importing (IMP-5: a dry run, then one transaction; GUIDs keep re-imports idempotent)
    ``plan_anki_import(store, data, with_history=True) -> AnkiImportPlan``
        ``plan.cards`` is core.cards' ImportPlan (added / updated / unchanged / rejected);
        ``plan.history`` the reviews and FSRS states to write; ``plan.report()``
    ``apply_anki_import(store, plan, retire=()) -> AnkiImportResult``
    ``recompute_memory(storage, record=None) -> bool``  the engine hook
        (``ENGINE_RECOMPUTE_HOOK``) to run after applying: the deck groups' parameter sets,
        then memory replayed from the stored histories

Rendering (IMP-8: a port of Anki's rules, checked against the anki package in tests)
    ``render_card(qfmt, afmt, fields, card_ord=, is_cloze=)``, ``card_fields(...)``,
    ``reveal_cloze_text(text, ordinal, question)``, ``sanitize_html``, ``scope_css``
    ``is_anki_html(text)``  card text the importer stored as sanitized HTML

The `anki` package (AGPL) is a dev-only test oracle: nothing here imports it (ADR-0015).
"""

from core.importers.anki.cloze import cloze_numbers, reveal_cloze_text
from core.importers.anki.errors import AnkiImportError
from core.importers.anki.mapping import ANKI_HTML_CLASS, html_to_text, is_anki_html, note_key
from core.importers.anki.model import AnkiData
from core.importers.anki.package import DEFAULT_LIMITS, Limits, read_package
from core.importers.anki.plan import (
    ENGINE_RECOMPUTE_HOOK,
    RULES_VERSION,
    AnkiImportPlan,
    AnkiImportResult,
    apply_anki_import,
    plan_anki_import,
    read_anki_file,
    recompute_memory,
)
from core.importers.anki.sanitize import sanitize_html, scope_css
from core.importers.anki.template import RenderedCard, TemplateError, card_fields, render_card
from core.importers.anki.text_export import read_text

__all__ = [
    "ANKI_HTML_CLASS",
    "DEFAULT_LIMITS",
    "ENGINE_RECOMPUTE_HOOK",
    "RULES_VERSION",
    "AnkiData",
    "AnkiImportError",
    "AnkiImportPlan",
    "AnkiImportResult",
    "Limits",
    "RenderedCard",
    "TemplateError",
    "apply_anki_import",
    "card_fields",
    "cloze_numbers",
    "html_to_text",
    "is_anki_html",
    "note_key",
    "plan_anki_import",
    "read_anki_file",
    "read_package",
    "read_text",
    "recompute_memory",
    "render_card",
    "reveal_cloze_text",
    "sanitize_html",
    "scope_css",
]
