"""Builders shared by the engine tests."""

from dataclasses import replace
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from core.engine import (
    AnswerFacts,
    EngineSettings,
    FsrsAdapter,
    ProblemOutcome,
    SkillContext,
    StudyDays,
    TimingFacts,
)
from core.engine.config import DAY_MS
from core.engine.grading import GradeResult, grade_answer
from core.model import Attempt, CardRef, CardUser, Skill, SkillState, SkillTierState
from core.storage.clock import to_ms

ZONE = ZoneInfo("America/New_York")
DAYS = StudyDays(ZONE, 4)
UTC_DAYS = StudyDays(UTC, 4)
T0 = to_ms(datetime(2026, 9, 1, 16, 0, tzinfo=UTC))  # 12:00 in New York, study day Sep 1
SETTINGS = EngineSettings()
SKILL = Skill(id="calc1.deriv.chain", name="Chain rule", section_id="calc1.s1", exam_tier=3)


def some[T](value: T | None) -> T:
    """Narrow an Optional in tests: the value must be there."""
    assert value is not None
    return value


def adapter(*, fuzz: bool = False) -> FsrsAdapter:
    return FsrsAdapter(fuzz=fuzz)


def day(ms: int) -> date:
    return DAYS.day_of(ms)


def at_day(n: int, hour_offset_ms: int = 0) -> int:
    """Noon (New York) of study day T0 + n."""
    return DAYS.moment(DAYS.add(DAYS.day_of(T0), n)) + hour_offset_ms


def card(
    tier: int = 2,
    *,
    cid: str | None = None,
    template: str | None = None,
    seed: int | None = None,
    kind: str = "problem",
    skill_id: str = SKILL.id,
    source: str = "calc1",
) -> CardRef:
    return CardRef(
        id=cid or f"c.t{tier}.{template or 'x'}.{seed if seed is not None else 0}",
        rev=1,
        kind=kind,  # type: ignore[arg-type]
        skill_id=skill_id,
        tier=tier,
        template_id=template,
        seed=seed,
        status="active",
        cue_required=False,
        has_cued_question=False,
        source=source,
    )


def outcome(
    at: int,
    *,
    tier: int = 2,
    ref: CardRef | None = None,
    correct: bool = True,
    solve_ms: int | None = 30_000,
    **facts: object,
) -> ProblemOutcome:
    purpose = facts.pop("purpose", "review")
    untimed = bool(facts.pop("untimed", False))
    lighter = bool(facts.pop("lighter_set", False))
    stretch = facts.pop("stretch", None)
    timing = facts.pop("timing", None)
    return ProblemOutcome(
        card=ref or card(tier),
        facts=AnswerFacts(correct=correct, **facts),  # type: ignore[arg-type]
        at=at,
        timing=timing  # type: ignore[arg-type]
        if timing is not None
        else TimingFacts(solve_ms=solve_ms, active_ms=solve_ms, expected_chars=5),
        purpose=purpose,  # type: ignore[arg-type]
        untimed=untimed,
        lighter_set=lighter,
        stretch=stretch,  # type: ignore[arg-type]
    )


class Sim:
    """A one-skill in-memory store: grade, then apply the GradedAnswer like storage would."""

    def __init__(
        self,
        state: SkillState | None = None,
        *,
        skill: Skill = SKILL,
        settings: EngineSettings = SETTINGS,
        fsrs: FsrsAdapter | None = None,
        retention: float = 0.90,
    ) -> None:
        self.skill = skill
        self.state = state
        self.tiers: dict[int, SkillTierState] = {}
        self.history: list[Attempt] = []
        self.cards: dict[str, CardUser] = {}
        self.settings = settings
        self.fsrs = fsrs or adapter()
        self.retention = retention
        self.exam_window = False
        self.exam_problem_ms: int | None = None
        self.results: list[GradeResult] = []

    def ctx(self, card_id: str | None = None) -> SkillContext:
        return SkillContext(
            skill=self.skill,
            state=self.state,
            tiers=dict(self.tiers),
            history=tuple(self.history),
            card_user=self.cards.get(card_id) if card_id else None,
            retention=self.retention,
            exam_window=self.exam_window,
            exam_problem_ms=self.exam_problem_ms,
        )

    def grade(self, out: ProblemOutcome) -> GradeResult:
        result = grade_answer(
            self.ctx(out.card.id), out, settings=self.settings, adapter=self.fsrs, days=DAYS
        )
        for change in result.answer.changes:
            if isinstance(change, SkillState):
                self.state = change
            elif isinstance(change, SkillTierState):
                self.tiers[change.tier] = change
            elif isinstance(change, CardUser):
                self.cards[change.card_id] = change
        attempt = replace(result.answer.attempt, id=len(self.history) + 1)
        self.history.append(attempt)
        self.results.append(result)
        return result

    def learn(self, at: int, *, problems: int = 3) -> GradeResult:
        """Show the example and pass the learning phase with clean answers."""
        self.grade(outcome(at, ref=card(1, kind="example", cid="ex.1"), solve_ms=None))
        result = None
        for i in range(problems):
            result = self.grade(
                outcome(at + (i + 1) * 60_000, tier=1 + i % 2, ref=card(1 + i % 2, cid=f"l{i}"))
            )
        assert result is not None
        return result


def learned_state(
    stability: float, *, at: int = T0, level: str = "learned", **kw: object
) -> SkillState:
    return SkillState(
        skill_id=SKILL.id,
        fsrs_state=2,
        stability=stability,
        difficulty=5.0,
        last_review_at=at,
        reps=3,
        introduced_at=at - DAY_MS,
        learned_at=at - DAY_MS,
        level=level,  # type: ignore[arg-type]
        level_at=at - DAY_MS,
        **kw,  # type: ignore[arg-type]
    )
