"""Located problems: every error and warning names its file and line (IMP-5)."""

from dataclasses import dataclass
from typing import Literal

type Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Problem:
    """One finding. Errors reject the card (or the whole file when card_id is None)."""

    file: str
    line: int
    message: str
    severity: Severity = "error"
    card_id: str | None = None

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    def __str__(self) -> str:
        tag = "" if self.is_error else "warning: "
        return f"{self.file}:{self.line}: {tag}{self.message}"


class CardFormatError(ValueError):
    """Raised by helpers that need one located error (the message includes file:line)."""

    def __init__(self, problem: Problem) -> None:
        super().__init__(str(problem))
        self.problem = problem
