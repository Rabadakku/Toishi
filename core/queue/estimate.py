"""Projected minutes (QUE-3): the student's own median active time per skill and tier,
taken over log times so one long problem doesn't skew it. Pure."""

import math
import statistics
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from core.model import Attempt
from core.queue.config import DEFAULT_PROBLEM_MS, EXAMPLE_MS, FLASHCARD_MS


def log_median(values: Iterable[int]) -> int | None:
    logs = [math.log(v) for v in values if v > 0]
    return round(math.exp(statistics.median(logs))) if logs else None


@dataclass(frozen=True, slots=True)
class TimeTable:
    """Medians in ms: per (skill, tier), per skill, per tier; defaults behind them."""

    by_skill_tier: dict[tuple[str, int], int] = field(default_factory=dict)
    by_skill: dict[str, int] = field(default_factory=dict)
    by_tier: dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_attempts(cls, attempts: Iterable[Attempt]) -> TimeTable:
        st: dict[tuple[str, int], list[int]] = defaultdict(list)
        sk: dict[str, list[int]] = defaultdict(list)
        ti: dict[int, list[int]] = defaultdict(list)
        for a in attempts:
            ms = a.capped_ms if a.capped_ms is not None else a.active_ms
            if (
                not a.final
                or a.voided_by is not None
                or ms is None
                or ms <= 0
                or a.card_kind not in ("problem", "find-error", "method")
                or a.skill_id is None
                or a.tier is None
            ):
                continue
            st[(a.skill_id, a.tier)].append(ms)
            sk[a.skill_id].append(ms)
            ti[a.tier].append(ms)
        return cls(
            {k: m for k, v in st.items() if (m := log_median(v)) is not None},
            {k: m for k, v in sk.items() if (m := log_median(v)) is not None},
            {k: m for k, v in ti.items() if (m := log_median(v)) is not None},
        )

    def problem_ms(self, skill_id: str | None, tier: float) -> int:
        t = min(5, max(1, round(tier)))
        if skill_id is not None:
            if (skill_id, t) in self.by_skill_tier:
                return self.by_skill_tier[(skill_id, t)]
            if skill_id in self.by_skill:
                return self.by_skill[skill_id]
        return self.by_tier.get(t, DEFAULT_PROBLEM_MS[t])

    def item_ms(self, kind: str, skill_id: str | None, tier: float) -> int:
        if kind == "example":
            return EXAMPLE_MS
        if kind == "flashcard":
            return FLASHCARD_MS
        return self.problem_ms(skill_id, tier)
