"""Grade one problem outcome into a GradedAnswer for UserStore.record_answer.

`grade_answer` is pure: it reads a SkillContext (the skill's rows and attempt history,
loaded by the caller) and returns every row the answer changes, the attempt and its FSRS
review events. Storage commits them in one transaction (rule 5).

Extension point: `hooks` run in order after the base grading and may return a changed
GradeResult (more PendingChecks, a different rating via `regrade`, ...). The "What went
wrong?" diagnosis, checks after misses, cued twins and partial credit plug in here; the
base grading only reports what they need in `Effects` (lapse, prerequisite_checks, ...).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Literal, Protocol

from core.engine.config import AGAIN, DAY_MS, RULES_VERSION, EngineSettings
from core.engine.days import StudyDays
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.histories import BELOW_BAND_KEY
from core.engine.level import Evidence, rank, update_level
from core.engine.lifecycle import (
    balance,
    due_at,
    due_day,
    example_shown,
    in_learning_phase,
    learning_answer,
    memory_of,
    review_answer,
    start_learning,
    with_adjust,
)
from core.engine.parts import PartOutcome, card_facts
from core.engine.rating import AnswerFacts, RatingDecision, RatingRules, SpeedFacts, rate
from core.engine.selection import (
    TierFlag,
    core_band,
    elo_update,
    exam_band,
    form_key,
    form_stats,
    is_below_band,
    is_stretch,
    learning_streak_needed,
)
from core.engine.timing import (
    TimingFacts,
    cap_ms,
    excluded_from_baseline,
    speed_time_ms,
    tier_update,
)
from core.model import (
    Attempt,
    CardRef,
    CardUser,
    ErrorChoice,
    GradedAnswer,
    JsonObject,
    LevelName,
    ReviewEvent,
    SessionState,
    Skill,
    SkillState,
    SkillTierState,
    StateRecord,
    Verdict,
)

Purpose = Literal[
    "review", "reinforcement", "checkup", "practice-test", "focused", "booster", "relearn", "redo"
]
Stage = Literal["learning", "example", "review", "stretch", "reinforcement"]


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillContext:
    """Everything grading reads about one skill. `history`: its non-voided attempts, oldest
    first. `retention`: the desired retention in force for it today (goals.skill_retention).
    `load`: reviews of other skills due per study day and `easy_days` the Easy Days setting
    (the load balancer, I3)."""

    skill: Skill
    state: SkillState | None
    tiers: Mapping[int, SkillTierState] = field(default_factory=dict)
    history: Sequence[Attempt] = ()
    card_user: CardUser | None = None
    retention: float = 0.90
    exam_window: bool = False
    exam_problem_ms: int | None = None
    load: Mapping[date, int] = field(default_factory=dict)
    easy_days: Mapping[str, float] = field(default_factory=dict)  # weekday -> load percent
    # Distinct tier 1-2 problems a learning phase can serve (ENG-2); None: not counted.
    learning_pool: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ProblemOutcome:
    """What the study screen reports for the final submission of one problem."""

    card: CardRef
    facts: AnswerFacts
    at: int  # submit time, UTC ms
    timing: TimingFacts = field(default_factory=TimingFacts)
    shown_at: int | None = None
    purpose: Purpose = "review"
    stretch: bool | None = None  # None: decided from the skill's core band
    untimed: bool = False
    lighter_set: bool = False
    example_opened: bool = False
    verdict: Verdict | None = None  # None: derived from facts
    pack_id: str | None = None
    part: str | None = None
    session: SessionState | None = None
    presentation_id: str | None = None
    reason_tag: str | None = None
    triage_policy: str | None = None
    raw_input: str | None = None
    parsed: str | None = None
    error_choice: ErrorChoice | None = None
    error_step: int | None = None
    matched_wrong: int | None = None
    check_of: int | None = None  # the PendingCheck this problem answers (diagnosis)
    app_version: str | None = None
    extra: JsonObject = field(default_factory=dict)
    # Multi-part problems: each part's verdict. `facts` then rate the card's own skill on the
    # worst of its remaining parts (grade_answer applies parts.card_facts); parts with their
    # own skill are reported to the diagnosis flow (partial credit, prerequisite checks).
    parts: tuple[PartOutcome, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class Effects:
    """What the queue and the diagnosis flow act on after an answer."""

    stage: Stage
    lapse: bool = False
    slip: bool = False  # an accepted careless slip: Again for FSRS, ignored by Level and leeches
    reinforcement_due: bool = False  # ENG-3: one fresh problem later this session, unrated
    # ENG-4: a failed stretch still owes its core-band review; it comes the next study day,
    # never right after the stretch's worked solution (ADR-0014)
    core_followup_due: bool = False
    learned: bool = False  # ENG-2 passed now
    learning_failed: bool = False  # ENG-2 failed now: restart tomorrow with the example
    prerequisite_checks: bool = False  # ENG-2 failure, ENG-9 leech: check prerequisites
    leech: bool = False  # ENG-9: became a leech now (repair: example, checks, textbook)
    textbook_ref: str | None = None
    provisional_demoted: bool = False
    level_before: LevelName | None = None
    level_after: LevelName | None = None
    demoted: bool = False
    shaky: bool = False
    tier_flag: TierFlag | None = None
    confident_error: bool = False  # a miss submitted "sure": next-day redo guaranteed


@dataclass(frozen=True, slots=True, kw_only=True)
class GradeResult:
    answer: GradedAnswer
    decision: RatingDecision
    effects: Effects
    state: SkillState


class GradeHook(Protocol):
    """Runs after base grading; returns the (possibly changed) result."""

    def __call__(
        self, ctx: SkillContext, outcome: ProblemOutcome, result: GradeResult
    ) -> GradeResult: ...


def _verdict(outcome: ProblemOutcome) -> Verdict:
    if outcome.verdict is not None:
        return outcome.verdict
    f = outcome.facts
    if f.gave_up:
        return "gave-up"
    if f.self_grade is not None or f.rubric_total is not None:
        return "self"
    return "correct" if f.correct else "incorrect"


def record_try(ctx: SkillContext, outcome: ProblemOutcome) -> GradedAnswer:
    """A non-final wrong attempt ("Not quite"): logged, never rated."""
    return GradedAnswer(
        attempt=_attempt(
            ctx, outcome, rating=None, recall=None, params_id=None, final=False, extra={}
        ),
        session=outcome.session,
    )


def record_unrated(ctx: SkillContext, outcome: ProblemOutcome) -> GradedAnswer:
    """A final attempt that changes nothing (C5: a practice-test problem left unanswered):
    logged for the test's score, with no rating, no FSRS event and no state change."""
    extra: JsonObject = {**outcome.extra, "stage": "unrated", "purpose": outcome.purpose}
    return GradedAnswer(
        attempt=_attempt(
            ctx, outcome, rating=None, recall=None, params_id=None, final=True, extra=extra
        ),
        session=outcome.session,
    )


def grade_answer(
    ctx: SkillContext,
    outcome: ProblemOutcome,
    *,
    settings: EngineSettings,
    adapter: FsrsAdapter,
    days: StudyDays,
    hooks: Sequence[GradeHook] = (),
) -> GradeResult:
    if outcome.parts:
        outcome = replace(outcome, facts=card_facts(outcome.facts, outcome.parts, ctx.skill.id))
    result = _grade(ctx, outcome, settings=settings, adapter=adapter, days=days)
    for hook in hooks:
        result = hook(ctx, outcome, result)
    return result


def _grade(
    ctx: SkillContext,
    outcome: ProblemOutcome,
    *,
    settings: EngineSettings,
    adapter: FsrsAdapter,
    days: StudyDays,
) -> GradeResult:
    skill, card, facts, now = ctx.skill, outcome.card, outcome.facts, outcome.at
    today = days.day_of(now)
    state = ctx.state or SkillState(skill_id=skill.id)
    if state.introduced_at is None and in_learning_phase(state):
        state = start_learning(state, skill.id, now)
    level_before = state.level
    memory = memory_of(state)
    tier = card.tier
    exam_tier = skill.exam_tier or 3

    # ---- stage
    stage: Stage
    below_band = False
    if card.kind == "example" or _verdict(outcome) == "shown":
        stage = "example"
    elif in_learning_phase(state):
        stage = "learning"
    elif outcome.purpose == "reinforcement" or (
        outcome.purpose == "redo" and not _due(ctx, adapter, days, today)
    ):
        # I4: a redo repeats one known problem (item memory), so it is rated only when the
        # skill is due and nothing fresher was served; otherwise unrated reinforcement.
        stage = "reinforcement"
    else:
        test = outcome.purpose == "practice-test"
        if ctx.exam_window or test:
            band = exam_band(exam_tier)  # the exam band: each skill's exam tier (ENG-4)
        else:
            band = core_band(memory.stability if memory else None)
        stretch = outcome.stretch if outcome.stretch is not None else is_stretch(tier, band)
        if test and not facts.success:
            stretch = False  # QUE-19: a practice-test miss is Again at every tier
        below_band = not stretch and is_below_band(tier, band)
        stage = "stretch" if stretch else "review"

    if stage == "example":
        new_state = example_shown(state)
        # A problem shown solved in place of an example card (ENG-2) is logged as seen, not
        # as a final answer: answered-problem counts (weak spots, timing baselines) skip it.
        attempt = _attempt(
            ctx, outcome, rating=None, recall=None, params_id=None,
            final=card.kind == "example",
            extra={"stage": stage, "purpose": outcome.purpose},
        )  # fmt: skip
        return GradeResult(
            answer=GradedAnswer(attempt=attempt, changes=(new_state,), session=outcome.session),
            decision=RatingDecision(rating=None, success=False),
            effects=Effects(stage=stage, level_before=level_before, level_after=new_state.level),
            state=new_state,
        )

    # ---- timing
    tier_state = ctx.tiers.get(tier)
    target = tier_state.target_ms if tier_state is not None else None
    timing = outcome.timing
    speed = None if outcome.untimed else speed_time_ms(
        timing.solve_ms, timing.expected_chars, target_ms=target, tier=tier
    )  # fmt: skip
    excluded = excluded_from_baseline(
        timing,
        untimed=outcome.untimed,
        hints_used=facts.hints_used,
        example_opened=outcome.example_opened,
    )
    recall = adapter.retrievability(memory, now) if memory is not None else None
    learned = not in_learning_phase(state) and rank(state.level) >= rank("learned")

    # ---- rating
    rules = RatingRules(
        easy_enabled=settings.too_easy_key,
        slow_rule=settings.slow_rule,
        untimed=outcome.untimed,
        below_band=below_band,
        stretch=stage == "stretch",
    )
    speed_facts = SpeedFacts(
        speed_ms=None if excluded else speed,
        baseline_ms=tier_state.baseline_median_ms if tier_state is not None else None,
        timed_successes=tier_state.baseline_n if tier_state is not None else 0,
        target_ms=target,
        recall=recall,
        learned=learned,
    )
    decision = rate(facts, speed_facts if stage in ("review", "stretch") else None, rules)

    # ---- Elo (every graded problem; never touches the schedule)
    form = form_key(card.id, card.template_id)
    elo = elo_update(
        theta=state.elo_theta,
        n=state.elo_n,
        form=form,
        tier=tier,
        success=decision.success,
        stats=form_stats(ctx.history),
    )
    state = replace(state, elo_theta=elo.theta_after, elo_n=elo.n_after)

    # ---- memory and lifecycle
    fx = Effects(stage=stage, level_before=level_before)
    reviews: list[ReviewEvent] = []
    review_rating = decision.rating if stage in ("learning", "review", "stretch") else None
    if stage == "learning":
        learning = learning_answer(
            state,
            rating=_rated(decision),
            counts=facts.clean and not facts.guessed,
            at_ms=now,
            today=today,
            correct_in_a_row=learning_streak_needed(settings.correct_in_a_row, ctx.learning_pool),
            max_problems=settings.max_learning_problems,
            adapter=adapter,
        )
        state = learning.state
        if learning.passed:
            fx = replace(fx, learned=True)
            reviews = [
                _review(skill.id, r, at, adapter, ctx.retention, None)
                for r, at in learning.replayed
            ]
        elif learning.failed:
            fx = replace(fx, learning_failed=True, prerequisite_checks=True)
    elif stage in ("review", "stretch") and decision.rating is not None:
        reviewed = review_answer(
            state,
            rating=_rated(decision),
            at_ms=now,
            adapter=adapter,
            days=days,
            leech_lapses=settings.leech_lapses,
            excused=decision.slip,
        )
        state = reviewed.state
        if reviewed.fsrs_event:
            # Stretch misses log no event, so stretch successes stay out of calibration
            # (no predicted recall) to keep ENG-11's bins unbiased; the event itself stays.
            predicted = None if stage == "stretch" else recall
            reviews = [_review(skill.id, _rated(decision), now, adapter, ctx.retention, predicted)]
        fx = replace(
            fx,
            lapse=reviewed.lapse and not decision.slip,
            slip=decision.slip,
            reinforcement_due=decision.rating == AGAIN
            and reviewed.fsrs_event
            and not reviewed.leech
            and not decision.slip,
            provisional_demoted=reviewed.provisional_demoted,
        )
        if reviewed.leech:
            fx = replace(fx, leech=True, prerequisite_checks=True, textbook_ref=skill.textbook_ref)
    elif stage == "stretch":
        # No FSRS event (ADR-0014): the skill's rated core-band review is still owed and
        # comes the next study day, so its worked solution can't prompt it.
        fx = replace(fx, core_followup_due=decision.core_followup)
        if memory is not None:
            state = with_adjust(
                state,
                not_before=today + timedelta(days=1),
                reason="Its review comes a day after a stretch problem",
            )

    # ---- Level (not in the learning phase; a reset to a new phase has no Level evidence)
    targets: dict[int, int | None] = {t: s.target_ms for t, s in ctx.tiers.items()}
    new_tier: SkillTierState | None = None
    baseline_ok = not excluded and stage in ("review", "stretch")
    if stage != "learning" and not in_learning_phase(state):
        success_ms = (
            speed
            if decision.success and facts.clean and baseline_ok and speed is not None
            else None
        )
        if learned:
            new_tier = tier_update(
                tier_state,
                skill_id=skill.id,
                tier=tier,
                history=ctx.history,
                learned_at=state.learned_at,
                new_success_ms=success_ms,
                exam_problem=ctx.exam_problem_ms,
                now_ms=now,
            )
            targets[tier] = new_tier.target_ms
        entry = Evidence(
            day=today.isoformat(),
            tier=tier,
            clean=facts.clean and not facts.guessed,
            rating=review_rating if stage in ("review", "stretch") and not decision.slip else None,
            speed_ms=None if excluded else speed,
            form=form,
            recall=recall,
            elapsed_days=None if memory is None else (now - memory.last_review_at) / DAY_MS,
            checkup=outcome.purpose == "checkup",
            above_exam_tier=tier > exam_tier,
        )
        change = update_level(
            state,
            entry,
            exam_tier=exam_tier,
            targets=targets,
            correct_in_a_row=settings.correct_in_a_row,
            pace=ctx.exam_problem_ms is not None,  # ENG-13: only with an exam length
        )
        state = replace(
            state,
            level=change.level,
            level_at=now if change.changed else state.level_at,
            shaky=change.shaky,
            shaky_reviews=change.shaky_reviews,
            learning_streak=change.learning_streak,
            level_evidence=change.evidence,
            mastered_at=now if change.level == "mastered" and change.changed else state.mastered_at,
        )
        fx = replace(fx, demoted=change.demoted)
    if reviews and memory_of(state) is not None:
        state = balance(state, ctx.retention, adapter, days, ctx.load, ctx.easy_days)
    state = replace(state, due_at=due_at(state, ctx.retention, adapter, days))

    # ---- card history and redo
    card_user = _card_user(ctx, outcome, decision, review_rating, stage, days)
    confident_error = is_confident_error(stage, review_rating, facts)

    extra: JsonObject = {
        **outcome.extra,
        "stage": stage,
        "purpose": outcome.purpose,
        "elo": elo.as_extra(),
        "reasons": list(decision.reasons),
        "slow": decision.slow,
        "baseline_ok": baseline_ok,
    }
    if decision.slip:
        extra["slip"] = True
    if speed is not None:
        extra["speed_ms"] = speed
    if outcome.lighter_set:
        extra["lighter_set"] = True
    if below_band:
        extra[BELOW_BAND_KEY] = True  # never a fit target (ENG-4)
    if outcome.parts:
        extra["parts"] = [p.as_json() for p in outcome.parts]
    if elo.tier_flag is not None:
        extra["tier_flag"] = elo.tier_flag
    attempt = _attempt(
        ctx,
        outcome,
        rating=review_rating,
        recall=recall,
        params_id=adapter.params_id,
        final=True,
        extra=extra,
        target_ms=target,
    )
    changes: list[StateRecord] = [state, card_user]
    if new_tier is not None:
        changes.append(new_tier)
    answer = GradedAnswer(
        attempt=attempt, changes=tuple(changes), reviews=tuple(reviews), session=outcome.session
    )
    return GradeResult(
        answer=answer,
        decision=decision,
        effects=replace(
            fx,
            level_after=state.level,
            shaky=state.shaky,
            tier_flag=elo.tier_flag,
            confident_error=confident_error,
        ),
        state=state,
    )


def _due(ctx: SkillContext, adapter: FsrsAdapter, days: StudyDays, today: date) -> bool:
    due = due_day(ctx.state, ctx.retention, adapter, days)
    return due is not None and due <= today


def _rated(decision: RatingDecision) -> int:
    if decision.rating is None:
        raise ValueError("a learning or core-band answer always has a rating")
    return decision.rating


def _review(
    skill_id: str,
    rating: int,
    at: int,
    adapter: FsrsAdapter,
    retention: float,
    recall: float | None,
) -> ReviewEvent:
    return ReviewEvent(
        at=at,
        target_kind="skill",
        target_id=skill_id,
        rating=rating,
        rules_version=RULES_VERSION,
        params_id=adapter.params_id,
        retention=retention,
        predicted_recall=None if recall is None else min(1.0, max(0.0, recall)),
    )


def is_confident_error(stage: Stage, rating: int | None, facts: AnswerFacts) -> bool:
    """A review (or stretch) miss rated Again that was submitted sure: the next-day redo is
    guaranteed and the solution says so. The engine alone decides this; views read it from
    the recorded effect (Effects.confident_error, CardUser.redo_guaranteed)."""
    return stage in ("review", "stretch") and rating == AGAIN and facts.submitted_sure_miss


def _card_user(
    ctx: SkillContext,
    outcome: ProblemOutcome,
    decision: RatingDecision,
    rating: int | None,
    stage: Stage,
    days: StudyDays,
) -> CardUser:
    """Last seen, and the redo: a missed review problem comes back once, 3 days later
    (the next study day, guaranteed, for a confident error)."""
    now = outcome.at
    cu = ctx.card_user or CardUser(card_id=outcome.card.id)
    was_redo = cu.redo_due_at is not None
    cu = replace(
        cu,
        last_seen_at=now,
        times_seen=cu.times_seen + 1,
        last_correct_at=now if decision.success else cu.last_correct_at,
        redo_due_at=None,
        redo_guaranteed=False,
    )
    if stage == "review" and rating == AGAIN and not was_redo:
        confident = is_confident_error(stage, rating, outcome.facts)
        wait = 1 if confident else 3
        cu = replace(
            cu,
            redo_due_at=days.start(days.day_of(now) + timedelta(days=wait)),
            redo_guaranteed=confident,
        )
    return cu


def _attempt(
    ctx: SkillContext,
    outcome: ProblemOutcome,
    *,
    rating: int | None,
    recall: float | None,
    params_id: str | None,
    final: bool,
    extra: JsonObject,
    target_ms: int | None = None,
) -> Attempt:
    card, facts, timing = outcome.card, outcome.facts, outcome.timing
    # I1: the strict outcome label, logged beside every rating (correct on the first try,
    # unaided, on the problem actually served).
    shown = card.kind == "example" or _verdict(outcome) == "shown"
    extra = {**extra, "strict_ok": final and facts.strict_ok and not shown}
    capped = None
    if timing.active_ms is not None:
        capped = min(timing.active_ms, cap_ms(target_ms, card.tier))
    return Attempt(
        at=outcome.at,
        shown_at=outcome.shown_at,
        session_id=None if outcome.session is None else outcome.session.id,
        presentation_id=outcome.presentation_id,
        card_id=card.id,
        card_rev=card.rev,
        pack_id=outcome.pack_id,
        card_kind=card.kind,
        skill_id=ctx.skill.id,
        part=outcome.part,
        tier=card.tier,
        seed=card.seed,
        template_id=card.template_id,
        reason_tag=outcome.reason_tag,
        raw_input=outcome.raw_input,
        parsed=outcome.parsed,
        verdict=_verdict(outcome) if final else (outcome.verdict or "incorrect"),
        attempt_number=facts.attempt_number,
        final=final,
        hints_used=facts.hints_used,
        example_opened=outcome.example_opened,
        confidence="unsure" if facts.unsure else "sure",
        guessed=facts.guessed,
        too_easy=facts.too_easy,
        active_ms=timing.active_ms,
        solve_ms=timing.solve_ms,
        entry_ms=timing.entry_ms,
        raw_ms=timing.raw_ms if timing.raw_ms is not None else timing.active_ms,
        capped_ms=capped,
        pause_count=timing.pause_count,
        longest_pause_ms=timing.longest_pause_ms,
        after_wake=timing.after_wake,
        untimed=outcome.untimed,
        rating=rating,
        explicit_rating=False,
        predicted_recall=None if recall is None else min(1.0, max(0.0, recall)),
        params_id=params_id,
        rules_version=RULES_VERSION if final else None,
        triage_policy=outcome.triage_policy,
        error_choice=outcome.error_choice,
        error_step=outcome.error_step,
        matched_wrong=outcome.matched_wrong,
        check_of=outcome.check_of,
        app_version=outcome.app_version,
        extra=extra,
    )
