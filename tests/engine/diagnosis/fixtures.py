"""A small skill graph with step-tagged cards for the diagnosis tests.

    c.alg  Factor polynomials          (section c.s0)
    c.pow  Power rule                  requires c.alg
    c.crit Critical numbers            requires c.pow, c.alg; encompasses c.pow 0.5, c.alg 0.25
    c.prod Product rule, c.quot Quotient rule (section c.s3)
    c.mc   Choose a differentiation rule: method-choice skill over c.prod, c.quot

c.crit problems: 0 [c.crit] Set up, 1 [c.pow] Differentiate, 2 [c.alg] Factor;
wrong answer "x = 1" @2 (a factoring mistake).
"""

from dataclasses import replace

from core.engine import AnswerFacts, ProblemOutcome, TimingFacts
from core.engine.config import DAY_MS
from core.model import Card, Choice, Skill, SkillState, SolutionStep, WrongAnswer
from tests.engine.diagnosis.memory import MemoryWorld, ref_of
from tests.engine.helpers import at_day

ALG, POW, CRIT, PROD, QUOT, MC = "c.alg", "c.pow", "c.crit", "c.prod", "c.quot", "c.mc"

SKILLS = [
    Skill(id=ALG, name="Factor polynomials", section_id="c.s0"),
    Skill(id=POW, name="Power rule", section_id="c.s1", requires=(ALG,)),
    Skill(
        id=CRIT,
        name="Critical numbers",
        section_id="c.s2",
        requires=(POW, ALG),
        encompasses=((POW, 0.5), (ALG, 0.25)),
        exam_tier=3,
    ),
    Skill(id=PROD, name="Product rule", section_id="c.s3", requires=(POW,)),
    Skill(id=QUOT, name="Quotient rule", section_id="c.s3", requires=(POW,)),
    Skill(
        id=MC,
        name="Choose a differentiation rule",
        section_id="c.s3",
        method_choice=True,
        requires=(PROD, QUOT),
    ),
]


def _steps(*tags: tuple[str, str]) -> tuple[SolutionStep, ...]:
    return tuple(
        SolutionStep(number=i, skill_id=k, label=label) for i, (k, label) in enumerate(tags)
    )


def cards() -> list[Card]:
    out: list[Card] = []
    for tier in range(1, 5):
        for seed in range(6):
            out.append(
                Card(
                    id=f"crit.t{tier}.{seed}",
                    skill_id=CRIT,
                    uses=(POW, ALG),
                    tier=tier,
                    template_id=f"crit.t{tier}",
                    seed=seed,
                    answer_type="number",
                    answer="0",
                    question_md="Find the critical numbers.",
                    cued_question_md="Set f' = 0 and find the critical numbers.",
                    solution=_steps((CRIT, "Set up"), (POW, "Differentiate"), (ALG, "Factor")),
                    wrong=(WrongAnswer(answer="1", feedback="Check the factoring", step=2),),
                )
            )
            for skill, label in ((POW, "Differentiate"), (ALG, "Factor")):
                out.append(
                    Card(
                        id=f"{skill}.t{tier}.{seed}",
                        skill_id=skill,
                        tier=tier,
                        template_id=f"{skill}.t{tier}",
                        seed=seed,
                        answer_type="number",
                        answer="0",
                        question_md="Solve.",
                        solution=_steps((skill, label)),
                    )
                )
            for skill in (PROD, QUOT):
                out.append(
                    Card(
                        id=f"{skill}.t{tier}.{seed}",
                        skill_id=skill,
                        uses=(POW,),
                        tier=tier,
                        template_id=f"{skill}.t{tier}",
                        seed=seed,
                        answer_type="number",
                        answer="0",
                        question_md="Differentiate.",
                        cued_question_md="Use the rule named and differentiate.",
                        solution=_steps(
                            (MC, "Choose the rule"), (skill, "Apply it"), (POW, "Powers")
                        ),
                    )
                )
    for seed in range(6):
        out.append(
            Card(
                id=f"mc.{seed}",
                kind="method",
                skill_id=MC,
                tier=2,
                answer_type="choice",
                question_md="Which rule?",
                choices=(
                    Choice(text_md="Product", correct=True),
                    Choice(text_md="Quotient", correct=False),
                ),
            )
        )
    out.append(
        Card(
            id="crit.fe",
            kind="find-error",
            skill_id=CRIT,
            tier=2,
            error_step=2,
            answer_type="number",
            answer="0",
            question_md="Find the wrong step.",
            shown_work=_steps((CRIT, "Set up"), (POW, "Differentiate"), (ALG, "Factor")),
            reasons=(
                Choice(text_md="Wrong sign", correct=False),
                Choice(text_md="Dropped a factor", correct=True),
                Choice(text_md="Wrong rule", correct=False),
            ),
        )
    )
    return out


def world(**kw: object) -> MemoryWorld:
    return MemoryWorld(SKILLS, cards(), **kw)  # type: ignore[arg-type]


def seed(
    w: MemoryWorld,
    skill_id: str,
    *,
    stability: float = 20.0,
    days_ago: float = 10.0,
    at: int | None = None,
    theta: float = 1.0,
    level: str = "learned",
    difficulty: float = 5.0,
    **kw: object,
) -> SkillState:
    """A skill in review, last reviewed `days_ago` before day 0 noon."""
    now = at if at is not None else at_day(0)
    last = int(now - days_ago * DAY_MS)
    state = SkillState(
        skill_id=skill_id,
        fsrs_state=2,
        stability=stability,
        difficulty=difficulty,
        last_review_at=last,
        reps=4,
        introduced_at=last - 20 * DAY_MS,
        learned_at=last - 15 * DAY_MS,
        level=level,  # type: ignore[arg-type]
        elo_theta=theta,
        elo_n=10,
        level_evidence={"log": []},
    )
    state = replace(state, **kw)  # type: ignore[arg-type]
    w.states[skill_id] = state
    return state


def answer(
    w: MemoryWorld,
    card_id: str,
    at: int,
    *,
    correct: bool,
    choice: str | None = None,
    step: int | None = None,
    matched: int | None = None,
    check_of: int | None = None,
    unsure: bool = False,
    purpose: str = "review",
    extra: dict[str, object] | None = None,
    **facts: object,
) -> ProblemOutcome:
    card = w.card(card_id)
    assert card is not None
    return ProblemOutcome(
        card=ref_of(card),
        facts=AnswerFacts(correct=correct, unsure=unsure, **facts),  # type: ignore[arg-type]
        at=at,
        timing=TimingFacts(solve_ms=40_000, active_ms=40_000, expected_chars=5),
        purpose=purpose,  # type: ignore[arg-type]
        error_choice=choice,  # type: ignore[arg-type]
        error_step=step,
        matched_wrong=matched,
        check_of=check_of,
        extra=extra or {},
    )


def allow_credit_on(monkeypatch: object) -> None:
    """Let credit On take effect (I9 gates it on held-out log loss) for tests of its mechanics."""
    from core.engine.diagnosis import credit, hook

    def allowed(*_: object, **__: object) -> credit.CreditSwitch:
        return credit.CreditSwitch(
            allowed=True, reviews=0, plain_log_loss=None, credited_log_loss=None, reason="test"
        )

    monkeypatch.setattr(hook, "credit_switch", allowed)  # type: ignore[attr-defined]
