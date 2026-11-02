"""Parameter sets (ADR-0013, decision 6): one FSRS-6 set per group of similar material.

- Skills: one set per domain. A course joins a domain through the setting `fsrs.domains`
  ({course_id: domain}); courses not listed share the set "skills". Domains are the
  student's own names (the app never assumes a subject).
- Flashcards: the set "flashcards"; cards of an imported Anki deck group use
  "anki.<group>", chosen by the longest deck prefix in `fsrs.deck_groups`
  ({deck prefix: group}). Flashcard sets use the defaults until their own fit; they never
  borrow a skill set.

Each set is stored in the setting "fsrs.params.<set>" ({"w", "id", "at", "items",
"source"}) with its history in "fsrs.params_history.<set>" (newest last) and its fitting
log in "fsrs.fit_log.<set>". The old "fsrs.params.math" still feeds "skills" until that
set is written. Stored values are cleaned (C1); a vector that cannot be cleaned falls back
to the defaults with a notice instead of raising.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from fsrs.scheduler import DEFAULT_PARAMETERS

from core.engine.config import PARAM_HISTORY_LIMIT
from core.engine.fsrs_adapter import ParameterError, clean_parameters, params_id_for
from core.model import TargetKind

SKILLS_SET: Final = "skills"
FLASHCARDS_SET: Final = "flashcards"
ANKI_PREFIX: Final = "anki."
DOMAIN_PREFIX: Final = "skills."
LEGACY_SKILLS_KEY: Final = "fsrs.params.math"
DOMAINS_SETTING: Final = "fsrs.domains"
DECK_GROUPS_SETTING: Final = "fsrs.deck_groups"
DEFAULTS: Final[tuple[float, ...]] = tuple(DEFAULT_PARAMETERS)


def set_id_for(kind: TargetKind, group: str | None = None) -> str:
    """The parameter set for skills of a domain, or flashcards of an Anki deck group."""
    if kind == "flashcard":
        return f"{ANKI_PREFIX}{group}" if group else FLASHCARDS_SET
    return f"{DOMAIN_PREFIX}{group}" if group else SKILLS_SET


def kind_of_set(set_id: str) -> TargetKind:
    return "flashcard" if set_id == FLASHCARDS_SET or set_id.startswith(ANKI_PREFIX) else "skill"


def params_key(set_id: str) -> str:
    return f"fsrs.params.{set_id}"


def history_key(set_id: str) -> str:
    return f"fsrs.params_history.{set_id}"


def recomputed_key(set_id: str) -> str:
    """The params id memory was last rebuilt under (ADR-0019 item 8: launch repairs a set
    adopted without its recompute)."""
    return f"fsrs.recomputed.{set_id}"


def fit_log_key(set_id: str) -> str:
    return f"fsrs.fit_log.{set_id}"


@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterSet:
    set_id: str
    parameters: tuple[float, ...]
    params_id: str
    source: str  # "default", "fit", "revert", "import"
    at: int | None = None
    items: int | None = None
    notice: str | None = None  # why stored parameters were not used


def _stored(settings: Mapping[str, Any], set_id: str) -> Any:
    raw = settings.get(params_key(set_id))
    if raw is None and set_id == SKILLS_SET:
        raw = settings.get(LEGACY_SKILLS_KEY)
    return raw


def load_set(settings: Mapping[str, Any], set_id: str) -> ParameterSet:
    """The set in force (cleaned), or the defaults (with a notice when unusable)."""
    raw = _stored(settings, set_id)
    default = ParameterSet(
        set_id=set_id, parameters=DEFAULTS, params_id=params_id_for(DEFAULTS), source="default"
    )
    if raw is None:
        return default
    try:
        if not isinstance(raw, Mapping) or "w" not in raw:
            raise ParameterError("the stored value has no parameter list")
        params = clean_parameters(raw["w"])
    except ParameterError as error:
        return ParameterSet(
            set_id=set_id,
            parameters=DEFAULTS,
            params_id=params_id_for(DEFAULTS),
            source="default",
            notice=f"Stored memory-model parameters for {set_id!r} were unusable ({error}); "
            "using the defaults.",
        )
    return ParameterSet(
        set_id=set_id,
        parameters=params,
        params_id=params_id_for(params),
        source=str(raw.get("source", "fit")),
        at=raw.get("at"),
        items=raw.get("items"),
    )


def stored_value(
    parameters: Sequence[float], *, at: int, source: str, items: int | None = None
) -> dict[str, Any]:
    params = clean_parameters(parameters)
    return {
        "w": list(params),
        "id": params_id_for(params),
        "at": at,
        "items": items,
        "source": source,
    }


def history(settings: Mapping[str, Any], set_id: str) -> list[dict[str, Any]]:
    raw = settings.get(history_key(set_id))
    return [dict(e) for e in raw if isinstance(e, Mapping)] if isinstance(raw, list) else []


def with_entry(entries: Sequence[Mapping[str, Any]], entry: Mapping[str, Any]) -> list[Any]:
    return [*(dict(e) for e in entries), dict(entry)][-PARAM_HISTORY_LIMIT:]


def domain_of(settings: Mapping[str, Any], course_id: str | None) -> str | None:
    domains = settings.get(DOMAINS_SETTING)
    if course_id is None or not isinstance(domains, Mapping):
        return None
    raw = domains.get(course_id)
    return str(raw) if raw else None


def deck_group_of(settings: Mapping[str, Any], deck: str | None) -> str | None:
    groups = settings.get(DECK_GROUPS_SETTING)
    if deck is None or not isinstance(groups, Mapping):
        return None
    best: tuple[int, str] | None = None
    for prefix, group in groups.items():
        p = str(prefix)
        if (deck == p or deck.startswith(p + "::")) and (best is None or len(p) > best[0]):
            best = (len(p), str(group))
    return None if best is None else best[1]
