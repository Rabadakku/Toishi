"""Errors that stop grading before any math is done."""

from typing import Literal

type InputErrorKind = Literal["syntax", "shape", "limit"]


class InputError(Exception):
    """The answer can't be read, or has the wrong shape. Never counts as an attempt."""

    def __init__(self, kind: InputErrorKind, message: str, hints: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.kind: InputErrorKind = kind
        self.message = message
        self.hints = hints


class SpecError(Exception):
    """The card itself is broken (bad key, option or domain): an authoring error."""


def syntax(message: str, *hints: str) -> InputError:
    return InputError("syntax", message, hints)


def shape(message: str, *hints: str) -> InputError:
    return InputError("shape", message, hints)


def limit(message: str) -> InputError:
    return InputError("limit", message)
