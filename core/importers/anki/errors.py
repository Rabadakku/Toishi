"""Errors the Anki importer raises for a whole file (single cards are rejected in the plan)."""


class AnkiImportError(ValueError):
    """The file can't be imported at all: not an Anki file, damaged, too large, unsafe, or
    made by a newer Anki. The message is written for the student."""
