"""An in-memory World for the diagnosis tests and simulations: it grades through the hook
and commits each GradedAnswer the way UserStore.record_answer does (ids, THIS_ATTEMPT)."""

import itertools
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace

from core.engine import EngineSettings, FsrsAdapter, ProblemOutcome, SkillContext, StudyDays
from core.engine.config import DAY_MS
from core.engine.diagnosis import DiagnosisHook, DiagnosisSettings, TapRecord
from core.engine.diagnosis.service import DailyReport, daily_run
from core.engine.diagnosis.world import tap_records
from core.engine.grading import GradeResult, grade_answer
from core.engine.selection import SeenIndex
from core.model import (
    THIS_ATTEMPT,
    Attempt,
    Card,
    CardRef,
    CardUser,
    DiagnosticSet,
    GradedAnswer,
    ImplicitCredit,
    PendingCheck,
    ReviewEvent,
    Skill,
    SkillShadow,
    SkillState,
    SkillTierState,
    StateRecord,
    WeakSpot,
)
from tests.engine.helpers import DAYS, SETTINGS, adapter


def ref_of(card: Card) -> CardRef:
    return CardRef(
        id=card.id,
        rev=card.rev,
        kind=card.kind,
        skill_id=card.skill_id,
        tier=card.tier,
        template_id=card.template_id,
        seed=card.seed,
        status=card.status,
        cue_required=card.cue_required,
        has_cued_question=card.cued_question_md is not None,
        source="pack",
    )


class MemoryWorld:
    def __init__(
        self,
        skills: Iterable[Skill],
        cards: Iterable[Card],
        *,
        settings: EngineSettings = SETTINGS,
        fsrs: FsrsAdapter | None = None,
        days: StudyDays = DAYS,
        config: DiagnosisSettings | None = None,
    ) -> None:
        self._skills = {s.id: s for s in skills}
        self._cards = {c.id: c for c in cards}
        self.settings = settings
        self.fsrs = fsrs or adapter()
        self.days = days
        self.conf = config or DiagnosisSettings()
        self.states: dict[str, SkillState] = {}
        self.tier_rows: dict[str, dict[int, SkillTierState]] = {}
        self.attempts: list[Attempt] = []
        self.events: list[ReviewEvent] = []
        self.credits: list[ImplicitCredit] = []
        self.checks: dict[int, PendingCheck] = {}
        self.sets: dict[int, DiagnosticSet] = {}
        self.spots: dict[int, WeakSpot] = {}
        self.shadows: dict[str, SkillShadow] = {}
        self.card_users: dict[str, CardUser] = {}
        self._ids = itertools.count(1)
        self.retentions: dict[str, float] = {}

    # ------------------------------------------------------------ World

    def config(self) -> DiagnosisSettings:
        return self.conf

    def skills(self) -> Mapping[str, Skill]:
        return self._skills

    def card(self, card_id: str) -> Card | None:
        return self._cards.get(card_id)

    def refs(self, skill_id: str) -> Sequence[CardRef]:
        return [ref_of(c) for c in self._cards.values() if c.skill_id == skill_id]

    def hidden(self) -> frozenset[str]:
        return frozenset()

    def state(self, skill_id: str) -> SkillState | None:
        return self.states.get(skill_id)

    def tiers(self, skill_id: str) -> Mapping[int, SkillTierState]:
        return self.tier_rows.get(skill_id, {})

    def history(self, skill_id: str) -> Sequence[Attempt]:
        return [a for a in self.attempts if a.skill_id == skill_id]

    def attempt(self, attempt_id: int) -> Attempt | None:
        return next((a for a in self.attempts if a.id == attempt_id), None)

    def recent_attempts(self, since: int) -> Sequence[Attempt]:
        return [a for a in self.attempts if a.at >= since]

    def seen(self, skill_id: str) -> SeenIndex:
        seen = {k: v.last_seen_at for k, v in self.card_users.items() if v.last_seen_at}
        return SeenIndex.from_attempts(self.history(skill_id), seen)

    def pending_checks(self) -> Sequence[PendingCheck]:
        return [c for c in self.checks.values() if c.status == "pending"]

    def diagnostic_sets(self) -> Sequence[DiagnosticSet]:
        return list(self.sets.values())

    def weak_spots(self) -> Sequence[WeakSpot]:
        return list(self.spots.values())

    def shadow(self, skill_id: str) -> SkillShadow | None:
        return self.shadows.get(skill_id)

    def last_failure_at(self, skill_id: str) -> int | None:
        fails = [e.at for e in self.events if e.target_id == skill_id and e.rating == 1]
        return max(fails) if fails else None

    def tap_log(self, now: int) -> Sequence[TapRecord]:
        return tap_records(self.attempts)

    def retention(self, skill_id: str) -> float:
        return self.retentions.get(skill_id, 0.90)

    def credits_since(self, at: int) -> Sequence[ImplicitCredit]:
        return [c for c in self.credits if c.at >= at]

    # ------------------------------------------------------------ grading and commits

    def hook(self) -> DiagnosisHook:
        return DiagnosisHook(self, settings=self.settings, adapter=self.fsrs, days=self.days)

    def ctx(self, skill_id: str, card_id: str | None = None) -> SkillContext:
        return SkillContext(
            skill=self._skills[skill_id],
            state=self.states.get(skill_id),
            tiers=self.tier_rows.get(skill_id, {}),
            history=self.history(skill_id),
            card_user=self.card_users.get(card_id) if card_id else None,
            retention=self.retention(skill_id),
        )

    def grade(self, outcome: ProblemOutcome, *, hooks: bool = True) -> GradeResult:
        skill_id = outcome.card.skill_id or ""
        result = grade_answer(
            self.ctx(skill_id, outcome.card.id),
            outcome,
            settings=self.settings,
            adapter=self.fsrs,
            days=self.days,
            hooks=(self.hook(),) if hooks else (),
        )
        self.last = self.commit(result.answer)
        return result

    def _put(self, record: StateRecord, attempt_id: int | None) -> StateRecord:
        if isinstance(record, PendingCheck):
            if record.attempt_id == THIS_ATTEMPT:
                record = replace(record, attempt_id=attempt_id)
            if record.resolved_by == THIS_ATTEMPT:
                record = replace(record, resolved_by=attempt_id)
        if isinstance(record, PendingCheck | WeakSpot | DiagnosticSet) and record.id is None:
            record = replace(record, id=next(self._ids))
        if isinstance(record, SkillState):
            self.states[record.skill_id] = record
        elif isinstance(record, SkillTierState):
            self.tier_rows.setdefault(record.skill_id, {})[record.tier] = record
        elif isinstance(record, CardUser):
            self.card_users[record.card_id] = record
        elif isinstance(record, PendingCheck):
            self.checks[record.id or 0] = record
        elif isinstance(record, WeakSpot):
            self.spots[record.id or 0] = record
        elif isinstance(record, DiagnosticSet):
            self.sets[record.id or 0] = record
        elif isinstance(record, SkillShadow):
            self.shadows[record.skill_id] = record
        return record

    def commit(self, answer: GradedAnswer) -> Attempt:
        attempt_id = next(self._ids)
        for record in answer.changes:
            self._put(record, attempt_id)
        attempt = replace(
            answer.attempt,
            id=attempt_id,
            study_day=answer.attempt.study_day or self.days.day_of(answer.attempt.at).isoformat(),
        )
        self.attempts.append(attempt)
        for e in answer.reviews:
            self.events.append(replace(e, attempt_id=attempt_id, at=e.at or attempt.at))
        for c in answer.credits:
            self.credits.append(replace(c, attempt_id=attempt_id))
        return attempt

    def apply(self, records: Sequence[StateRecord]) -> tuple[StateRecord, ...]:
        return tuple(self._put(r, None) for r in records)

    def daily(self, now: int) -> DailyReport:
        return daily_run(
            self, now=now, study_day=self.days.day_of(now).isoformat(), apply=self.apply
        )

    # ------------------------------------------------------------ conveniences

    def pending(self, skill_id: str | None = None) -> list[PendingCheck]:
        return [c for c in self.pending_checks() if skill_id is None or c.skill_id == skill_id]

    def events_for(self, skill_id: str) -> list[ReviewEvent]:
        return [e for e in self.events if e.target_id == skill_id]

    def recall(self, skill_id: str, at: int) -> float | None:
        state = self.states.get(skill_id)
        if state is None or state.stability is None or state.last_review_at is None:
            return None
        return self.fsrs.retrievability_after((at - state.last_review_at) / DAY_MS, state.stability)
