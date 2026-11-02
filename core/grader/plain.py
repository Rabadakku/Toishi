"""choice, truefalse and text answers: exact match on options or normalized text."""

import re
import unicodedata

_TRUE = {"true", "t", "yes", "y"}
_FALSE = {"false", "f", "no", "n"}


def normalize_text(text: str) -> str:
    """Ignore case, accents' composition, extra spaces and a final period."""
    value = unicodedata.normalize("NFKC", text).casefold()
    value = re.sub(r"\s+", " ", value).strip()
    return value.removesuffix(".").strip()


def parse_bool(text: str) -> bool | None:
    value = normalize_text(text)
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    return None


def parse_choice(text: str, count: int) -> frozenset[int] | None:
    """Selected options as 0-based indices, from "a, c" or "1, 3"; None if unreadable."""
    picked: set[int] = set()
    for part in re.split(r"[,\s]+", text.strip()):
        if not part:
            continue
        if part.isdigit():
            index = int(part) - 1
        elif len(part) == 1 and part.isalpha():
            index = ord(part.lower()) - ord("a")
        else:
            return None
        if not 0 <= index < count:
            return None
        picked.add(index)
    return frozenset(picked) if picked else None
