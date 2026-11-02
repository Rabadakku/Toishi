"""What the diagnosis reads besides the graded skill's SkillContext.

`World` is the read interface the hook and the daily finder use; `StorageWorld` answers it
from a Storage (fresh reads, cached for the life of one instance, so build one per graded
answer or daily run). Tests and simulations use an in-memory implementation.
"""

from collections.abc import Callable, Mapping, Sequence
from functools import cache
from typing import Protocol, runtime_checkable

from core.engine.config import DAY_MS
from core.engine.diagnosis.blame import TapRecord
from core.engine.diagnosis.config import TAP_LOG_DAYS, DiagnosisSettings
from core.engine.selection import SeenIndex
from core.model import (
    Attempt,
    Card,
    CardRef,
    DiagnosticSet,
    ImplicitCredit,
    PendingCheck,
    Skill,
    SkillShadow,
    SkillState,
    SkillTierState,
    WeakSpot,
)
from core.storage import Storage


@runtime_checkable
class World(Protocol):
    def config(self) -> DiagnosisSettings: ...
    def skills(self) -> Mapping[str, Skill]: ...
    def card(self, card_id: str) -> Card | None: ...
    def refs(self, skill_id: str) -> Sequence[CardRef]: ...
    def hidden(self) -> frozenset[str]: ...
    def state(self, skill_id: str) -> SkillState | None: ...
    def tiers(self, skill_id: str) -> Mapping[int, SkillTierState]: ...
    def history(self, skill_id: str) -> Sequence[Attempt]: ...
    def attempt(self, attempt_id: int) -> Attempt | None: ...
    def recent_attempts(self, since: int) -> Sequence[Attempt]: ...
    def seen(self, skill_id: str) -> SeenIndex: ...
    def pending_checks(self) -> Sequence[PendingCheck]: ...
    def diagnostic_sets(self) -> Sequence[DiagnosticSet]: ...
    def weak_spots(self) -> Sequence[WeakSpot]: ...
    def shadow(self, skill_id: str) -> SkillShadow | None: ...
    def last_failure_at(self, skill_id: str) -> int | None: ...
    def tap_log(self, now: int) -> Sequence[TapRecord]: ...
    def retention(self, skill_id: str) -> float: ...
    def credits_since(self, at: int) -> Sequence[ImplicitCredit]: ...


def tap_records(attempts: Sequence[Attempt]) -> list[TapRecord]:
    """Resolved diagnoses logged on check attempts (extra["diagnosis"]["resolved"])."""
    out: list[TapRecord] = []
    for a in attempts:
        if a.voided_by is not None:
            continue
        raw = a.extra.get("diagnosis", {})
        resolved = raw.get("resolved") if isinstance(raw, dict) else None
        if isinstance(resolved, dict) and resolved.get("choice"):
            out.append(
                TapRecord(
                    at=a.at,
                    choice=str(resolved["choice"]),
                    skill_id=str(resolved.get("skill")),
                    kind=str(resolved.get("kind")),
                    confirmed=bool(resolved.get("confirmed")),
                )
            )
    return out


class StorageWorld:
    """World over a Storage. Reads are cached for this instance's life."""

    def __init__(
        self, storage: Storage, *, retention: Callable[[str], float] | None = None
    ) -> None:
        self._s = storage
        self._retention = retention

    @cache  # noqa: B019 -- one instance per graded answer or daily run
    def config(self) -> DiagnosisSettings:
        return DiagnosisSettings.from_settings(self._s.users.settings())

    @cache  # noqa: B019
    def skills(self) -> Mapping[str, Skill]:
        return {k.id: k for k in self._s.packs.skills()}

    def card(self, card_id: str) -> Card | None:
        return self._s.packs.card(card_id)

    @cache  # noqa: B019
    def refs(self, skill_id: str) -> Sequence[CardRef]:
        return self._s.packs.card_refs(skill_id=skill_id)

    @cache  # noqa: B019
    def hidden(self) -> frozenset[str]:
        return frozenset(
            k for k, m in self._s.users.card_marks().items() if m.hidden or m.suspended
        )

    @cache  # noqa: B019
    def state(self, skill_id: str) -> SkillState | None:
        return self._s.users.skill_state(skill_id)

    @cache  # noqa: B019
    def tiers(self, skill_id: str) -> Mapping[int, SkillTierState]:
        return {t.tier: t for t in self._s.users.skill_tiers(skill_id)}

    @cache  # noqa: B019
    def history(self, skill_id: str) -> Sequence[Attempt]:
        return self._s.users.attempts(skill_id=skill_id)

    def attempt(self, attempt_id: int) -> Attempt | None:
        return self._s.users.attempt(attempt_id)

    @cache  # noqa: B019
    def recent_attempts(self, since: int) -> Sequence[Attempt]:
        return self._s.users.attempts(since=since)

    @cache  # noqa: B019
    def _card_seen(self) -> dict[str, int]:
        return {k: v.last_seen_at for k, v in self._s.users.card_users().items() if v.last_seen_at}

    def seen(self, skill_id: str) -> SeenIndex:
        return SeenIndex.from_attempts(self.history(skill_id), self._card_seen())

    @cache  # noqa: B019
    def pending_checks(self) -> Sequence[PendingCheck]:
        return self._s.users.pending_checks("pending")

    @cache  # noqa: B019
    def diagnostic_sets(self) -> Sequence[DiagnosticSet]:
        return self._s.users.diagnostic_sets()

    @cache  # noqa: B019
    def weak_spots(self) -> Sequence[WeakSpot]:
        return self._s.users.weak_spots()

    @cache  # noqa: B019
    def _shadows(self) -> Mapping[str, SkillShadow]:
        return self._s.users.skill_shadows()

    def shadow(self, skill_id: str) -> SkillShadow | None:
        return self._shadows().get(skill_id)

    def last_failure_at(self, skill_id: str) -> int | None:
        events = self._s.users.review_events(target_kind="skill", target_id=skill_id)
        fails = [e.at for e in events if e.rating == 1]
        return max(fails) if fails else None

    def tap_log(self, now: int) -> Sequence[TapRecord]:
        return tap_records(self.recent_attempts(now - TAP_LOG_DAYS * DAY_MS))

    @cache  # noqa: B019
    def retention(self, skill_id: str) -> float:
        return 0.90 if self._retention is None else self._retention(skill_id)

    @cache  # noqa: B019
    def credits_since(self, at: int) -> Sequence[ImplicitCredit]:
        return [c for c in self._s.users.credits() if c.at >= at]
