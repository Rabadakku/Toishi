"""The "What went wrong?" flow and check resolution, as a GradeHook (ADR-0008).

`DiagnosisHook(world, settings=, adapter=, days=)` runs after base grading of every final
answer. In order:

1. Settle first. A diagnostic-set problem is logged, not rated (re-graded as unrated). If
   the graded skill has a held verdict, it is settled before this answer's own rating, so
   FSRS events stay in time order: by this answer when it is the check that decides it,
   otherwise with the rating map's default (Again at the miss's time). A careless slip or
   misread is re-graded with the 30-day cap decided here.
2. Resolve the check this answer serves (`ProblemOutcome.check_of`, or a pending check on
   this skill and card): step checks settle the held problem with Again either way, since
   a wrong final answer never counts as a pass (ADR-0014). A pass is an integration error
   on the problem's own skill: a plain Again that counts for Level and leeches (ADR-0019
   item 4). A fail traces the miss to the checked skill, which takes the lapse, so the
   problem's Again is excused; the problem waits a day, while the checked skill's low-recall
   prerequisites get checks, deepest first; prerequisite checks go one layer deeper on
   failure; a solved cued twin gives the method-choice skill Again, an unsolved one means a
   worked example before the skill's next problem; diagnostic sets confirm or clear.
3. Otherwise, a miss runs the picker's choice (spec table "What went wrong?"); every miss
   logs its blame shares for ENG-15, and every graded problem its tags and Elo prediction.
4. Then ENG-2/ENG-9 prerequisite checks, ENG-6 pull-forward after any lapse, ENG-7
   partial credit (shadow), ENG-16 method-choice reviews from uncued problems, and the
   confident-error redo.
5. Multi-part problems: a part with its own skill reports to it. Answered right, that skill
   gets ENG-7 partial credit (weight PART_CREDIT_WEIGHT, the same Off/Shadow/On setting and
   exclusions; merged with the card's own ENG-7 credit, one credit per skill at the larger
   weight); missed, it gets a prerequisite check. The card's own skill was already rated on
   its remaining parts (parts.card_facts).

Everything goes into the same GradedAnswer, so one transaction commits it and one undo
removes it.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import timedelta
from typing import Any

from core.engine.config import AGAIN, DAY_MS, GOOD, HARD, RULES_VERSION, EngineSettings
from core.engine.days import StudyDays
from core.engine.diagnosis.blame import (
    Tags,
    blame,
    card_tags,
    heaviest,
    tap_calibration,
    untapped_blame,
)
from core.engine.diagnosis.checks import (
    NewCheck,
    check_tiers,
    name_of,
    part_reason,
    pick_check_card,
    prerequisite_reason,
    prerequisite_targets,
    prerequisites_by_depth,
    step_reason,
    twin_reason,
)
from core.engine.diagnosis.config import (
    ABOVE_LEVEL_P,
    CHECK_AFTER_ITEMS,
    PART_CREDIT_WEIGHT,
    UNVERIFIED,
)
from core.engine.diagnosis.credit import (
    credit_switch,
    credit_targets,
    partial_credit,
    pull_forward,
    shadow_after_review,
    shadow_recalls,
)
from core.engine.diagnosis.items import method_choice_active, method_choice_skill, shown_cued
from core.engine.diagnosis.verdict import (
    ADJUST,
    EXAMPLE_FIRST,
    HOLD,
    Settled,
    SlipDecision,
    diagnosis_of,
    hold_of,
    place_hold,
    settle,
    slip_decision,
    with_adjust,
    without,
)
from core.engine.diagnosis.weakspots import diagnostic_step
from core.engine.diagnosis.world import World
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.grading import GradeResult, ProblemOutcome, SkillContext, grade_answer
from core.engine.level import Evidence
from core.engine.lifecycle import due_at, due_day, memory_of, review_answer
from core.engine.parts import own_skill_parts
from core.model import (
    THIS_ATTEMPT,
    Attempt,
    Card,
    CardUser,
    CheckKind,
    ImplicitCredit,
    JsonObject,
    PendingCheck,
    ReviewEvent,
    Skill,
    SkillShadow,
    SkillState,
    StateRecord,
)


@dataclass(frozen=True, slots=True)
class DiagnosisHook:
    """`world`: a World, or a factory called once per graded answer (fresh reads)."""

    world: World | Callable[[], World]
    settings: EngineSettings
    adapter: FsrsAdapter
    days: StudyDays
    # Decision 6 (ADR-0013): each skill's own parameter set; None: `adapter` for every skill.
    adapter_of: Callable[[str], FsrsAdapter] | None = None

    def adapter_for(self, skill_id: str) -> FsrsAdapter:
        return self.adapter if self.adapter_of is None else self.adapter_of(skill_id)

    def __call__(
        self, ctx: SkillContext, outcome: ProblemOutcome, result: GradeResult
    ) -> GradeResult:
        world = self.world if isinstance(self.world, World) else self.world()
        return _Run(self, world, ctx, outcome, result).run()


def find_check(
    pending: Sequence[PendingCheck], outcome: ProblemOutcome, skill_id: str
) -> PendingCheck | None:
    """The pending check this answer serves: by id, else one on this skill and card."""
    if outcome.check_of is not None:
        return next((c for c in pending if c.id == outcome.check_of), None)
    return next(
        (
            c
            for c in pending
            if c.status == "pending" and c.skill_id == skill_id and c.card_id == outcome.card.id
        ),
        None,
    )


@dataclass
class _Changes:
    states: dict[str, SkillState] = field(default_factory=dict)  # skills other than the graded
    records: dict[tuple[str, Any], StateRecord] = field(default_factory=dict)
    before: list[ReviewEvent] = field(default_factory=list)  # settled earlier verdicts
    after: list[ReviewEvent] = field(default_factory=list)
    credits: list[ImplicitCredit] = field(default_factory=list)
    checks: list[NewCheck] = field(default_factory=list)

    def put(self, record: StateRecord) -> None:
        key = getattr(record, "id", None) or getattr(record, "skill_id", None)
        self.records[(type(record).__name__, key)] = record


class _Run:
    def __init__(
        self,
        hook: DiagnosisHook,
        world: World,
        ctx: SkillContext,
        outcome: ProblemOutcome,
        result: GradeResult,
    ) -> None:
        self.h = hook
        self.w = world
        self.ctx = ctx
        self.outcome = outcome
        self.result = result
        self.now = outcome.at
        self.today = hook.days.day_of(outcome.at)
        self.skill_id = ctx.skill.id
        self.skills: Mapping[str, Skill] = {**self.w.skills(), ctx.skill.id: ctx.skill}
        self.card: Card | None = self.w.card(outcome.card.id)
        self.tags: Tags = card_tags(self.card, self.skill_id)
        self.pending = list(self.w.pending_checks())
        self.check = find_check(self.pending, outcome, self.skill_id)
        self.trigger: Attempt | None = (
            self.w.attempt(self.check.attempt_id)
            if self.check is not None and self.check.attempt_id is not None
            else None
        )
        self.c = _Changes()
        self.diag: JsonObject = {}
        self.lapsed: list[str] = []
        self.held = False
        self.slip: SlipDecision | None = None
        self.part_credit: dict[str, float] = {}  # multi-part: own-skill parts answered right

    # ------------------------------------------------------------ helpers

    @property
    def state(self) -> SkillState:
        return self.result.state

    def set_state(self, state: SkillState) -> None:
        changes = tuple(
            state if isinstance(r, SkillState) and r.skill_id == self.skill_id else r
            for r in self.result.answer.changes
        )
        self.result = replace(
            self.result, state=state, answer=replace(self.result.answer, changes=changes)
        )

    def state_of(self, skill_id: str) -> SkillState | None:
        if skill_id == self.skill_id:
            return self.state
        if skill_id in self.c.states:
            return self.c.states[skill_id]
        return self.w.state(skill_id)

    def recall(self, skill_id: str) -> float | None:
        memory = memory_of(self.state_of(skill_id) if skill_id != self.skill_id else self.ctx.state)
        if memory is None:
            return None
        return self.h.adapter_for(skill_id).retrievability(memory, self.now)

    def regrade(self, ctx: SkillContext, outcome: ProblemOutcome) -> None:
        self.ctx, self.outcome = ctx, outcome
        self.result = grade_answer(
            ctx,
            outcome,
            settings=self.h.settings,
            adapter=self.h.adapter_for(ctx.skill.id),
            days=self.h.days,
        )

    def settle_other(self, skill_id: str, rating: int | None, *, excused: bool = False) -> Settled:
        state = self.state_of(skill_id)
        if state is None:
            return Settled(state=SkillState(skill_id=skill_id))
        settled = settle(state, rating, excused=excused, **self._settle_args(skill_id))
        self.c.states[skill_id] = settled.state
        if settled.event is not None:
            self.c.after.append(settled.event)
        if settled.lapse and not excused:
            self.lapsed.append(skill_id)
        if settled.leech:  # ENG-9 repair: checks on every prerequisite
            self.prerequisite_checks(skill_id, depth=0, every=True)
        return settled

    def _settle_args(self, skill_id: str) -> dict[str, Any]:
        skill = self.skills.get(skill_id)
        tiers = self.ctx.tiers if skill_id == self.skill_id else self.w.tiers(skill_id)
        return {
            "adapter": self.h.adapter_for(skill_id),
            "days": self.h.days,
            "settings": self.h.settings,
            "exam_tier": (skill.exam_tier if skill is not None else None) or 3,
            "targets": {t: s.target_ms for t, s in tiers.items()},
            "retention": self.retention(skill_id),
        }

    def retention(self, skill_id: str) -> float:
        return self.ctx.retention if skill_id == self.skill_id else self.w.retention(skill_id)

    def event_for(self, skill_id: str, at: int | None = None) -> ReviewEvent | None:
        return next(
            (
                e
                for e in self.result.answer.reviews
                if e.target_id == skill_id and (at is None or e.at in (0, at))
            ),
            None,
        )

    def review_other(self, skill_id: str, rating: int, *, recall: bool = False) -> None:
        """An FSRS review of another skill, now (a method-choice skill, a diagnostic lapse)."""
        state = self.state_of(skill_id)
        memory = memory_of(state)
        if state is None or memory is None:
            return
        adapter = self.h.adapter_for(skill_id)
        reviewed = review_answer(
            state,
            rating=rating,
            at_ms=self.now,
            adapter=adapter,
            days=self.h.days,
            leech_lapses=self.h.settings.leech_lapses,
        )
        new = reviewed.state
        new = replace(new, due_at=due_at(new, self.retention(skill_id), adapter, self.h.days))
        if skill_id == self.skill_id:
            self.set_state(new)
        else:
            self.c.states[skill_id] = new
        if reviewed.fsrs_event:
            r = adapter.retrievability(memory, self.now) if recall else None
            self.c.after.append(
                ReviewEvent(
                    at=self.now,
                    target_kind="skill",
                    target_id=skill_id,
                    rating=rating,
                    rules_version=RULES_VERSION,
                    params_id=adapter.params_id,
                    retention=self.retention(skill_id),
                    predicted_recall=r,
                )
            )
        if reviewed.lapse:
            self.lapsed.append(skill_id)

    # ------------------------------------------------------------ run

    def run(self) -> GradeResult:
        if self.result.effects.stage == "example":
            if EXAMPLE_FIRST in self.state.level_evidence:
                self.set_state(without(self.state, EXAMPLE_FIRST))
            return self.result
        self.prepare()
        stage = self.result.effects.stage
        elo = self.result.answer.attempt.extra.get("elo", {})
        p = float(elo["p"]) if isinstance(elo, dict) and "p" in elo else None
        cued = shown_cued(
            cued_flag=bool(self.outcome.extra.get("cued", False)),
            stage=stage,
            check_kind=self.check.kind if self.check is not None else None,
            cue_required=self.outcome.card.cue_required,
        )
        self.diag.update(
            {"tags": self.tags.weights(), "p": p, "cued": cued, "choice": self.outcome.error_choice}
        )
        if self.outcome.error_step is not None:
            self.diag["step"] = self.outcome.error_step
        if self.check is not None:
            self.diag["check"] = {"id": self.check.id, "kind": self.check.kind}
        miss = not self.result.decision.success
        if self.check is not None:
            self.resolve_check()
            if miss:
                self.diag["blame"] = self.blame(self.outcome.error_choice)
        elif miss:
            self.miss_flow(p)
        self.part_effects()
        self.after_effects(cued=cued)
        if self.part_credit:  # the card's own review earned no ENG-7 credit to merge with
            self.credit(self.part_credit)
        return self.finish()

    # ------------------------------------------------------------ 1. settle first

    def prepare(self) -> None:
        if self.check is not None and self.check.kind == "diagnostic":
            if self.result.effects.stage in ("review", "stretch"):
                self.regrade(self.ctx, replace(self.outcome, purpose="reinforcement"))
            self.diag["no_evidence"] = True
        hold = hold_of(self.ctx.state)
        if hold is not None and self.ctx.state is not None:
            decides = (
                self.check is not None
                and self.trigger is not None
                and self.trigger.skill_id == self.skill_id
                and self.trigger.at == hold.get("at")
            )
            rating: int | None
            excused = False
            if decides and self.check is not None and self.check.kind == "cued-twin":
                # The miss stays Again (ADR-0014); solved cued, the method choice failed,
                # so Level and leeches ignore it; unsolved, it is the skill's own miss.
                rating = AGAIN
                excused = self.result.decision.success
            elif decides:
                # Its own skill was checked: the miss stays Again (ADR-0014), and a passed
                # step check makes it an integration error that counts for Level and leeches
                # (ADR-0019 item 4); a failed one still waits on the checked skill.
                rating = AGAIN
                excused = False
            else:
                rating = AGAIN  # served again before its check: the rating map's default
            settled = settle(
                self.ctx.state, rating, excused=excused, **self._settle_args(self.skill_id)
            )
            if settled.event is not None:
                self.c.before.append(settled.event)
            if settled.lapse and not excused:
                self.lapsed.append(self.skill_id)
            if settled.leech:
                self.prerequisite_checks(self.skill_id, depth=0, every=True)
            self.diag["settled"] = {"rating": rating, "by_check": decides}
            self.regrade(replace(self.ctx, state=settled.state), self.outcome)
        if (
            self.check is None
            and self.outcome.error_choice in ("slip", "misread")
            and self.result.effects.stage == "review"
            and not self.result.decision.success
        ):
            recall = self.result.answer.attempt.predicted_recall
            self.slip = slip_decision(self.ctx.history, at=self.now, recall=recall)
            want = self.slip.accepted
            if want != self.outcome.facts.slip_within_cap:
                facts = replace(self.outcome.facts, slip_within_cap=want)
                self.regrade(self.ctx, replace(self.outcome, facts=facts))

    # ------------------------------------------------------------ 2. checks

    def resolve_check(self) -> None:
        check = self.check
        if check is None:
            return
        success = self.result.decision.success
        self.c.put(
            replace(
                check,
                status="passed" if success else "failed",
                resolved_at=self.now,
                resolved_by=THIS_ATTEMPT,
            )
        )
        trigger = self.trigger
        tdiag = diagnosis_of(trigger) if trigger is not None else {}
        confirmed = success if check.kind == "cued-twin" else not success
        self.diag["resolved"] = {
            "check": check.id,
            "kind": check.kind,
            "choice": tdiag.get("choice"),
            "skill": check.skill_id,
            "trigger": check.attempt_id,
            "confirmed": confirmed,
        }
        problem = trigger.skill_id if trigger is not None and trigger.skill_id else self.skill_id
        if check.kind == "step":
            if problem != self.skill_id and trigger is not None:
                held = hold_of(self.state_of(problem))
                if held is not None and held.get("at") == trigger.at:
                    # Again either way (ADR-0014). A pass shows an integration error on the
                    # problem's own skill: a plain Again that counts for Level and leeches
                    # (ADR-0019 item 4). A fail traces the miss to the checked skill, which
                    # takes the lapse, so the problem's Again is excused.
                    settled = self.settle_other(problem, AGAIN, excused=not success)
                    if not success:
                        self.c.states[problem] = with_adjust(
                            settled.state,
                            not_before=self.today + timedelta(days=1),
                            reason=(
                                f"Its miss was traced to {name_of(self.skills, self.skill_id)}"
                            ),
                        )
            if not success:
                self.prerequisite_checks(self.skill_id, depth=check.depth)
        elif check.kind == "prerequisite":
            if not success:
                self.prerequisite_checks(self.skill_id, depth=check.depth)
        elif check.kind == "cued-twin":
            if success:
                method = method_choice_skill(problem, self.skills)
                if method is not None:
                    self.diag["method_gap"] = method.id
                    if method_choice_active(method, self.state_of):
                        self.review_other(method.id, AGAIN)
            else:
                self.set_state(
                    replace(
                        self.state,
                        level_evidence={**self.state.level_evidence, EXAMPLE_FIRST: True},
                    )
                )
        elif check.kind == "diagnostic":
            self.diagnostic_answer(missed=not success)

    def diagnostic_answer(self, *, missed: bool) -> None:
        sets = [
            d
            for d in self.w.diagnostic_sets()
            if d.skill_id == self.skill_id and d.status in ("pending", "active")
        ]
        if not sets:
            return
        diag, decision = diagnostic_step(sets[-1], missed=missed)
        if decision is not None:
            diag = replace(diag, resolved_at=self.now)
        self.c.put(diag)
        if decision is None:
            return
        self.diag["diagnostic"] = decision
        spot = next((s for s in self.w.weak_spots() if s.id == diag.weak_spot_id), None)
        if spot is not None:
            self.c.put(replace(spot, status=decision, resolved_at=self.now))
        current = self.check.id if self.check is not None else None
        for other in self.pending:
            if (
                other.kind == "diagnostic"
                and other.skill_id == self.skill_id
                and other.id != current
            ):
                self.c.put(replace(other, status="cancelled", resolved_at=self.now))
        if decision == "confirmed":
            self.review_other(self.skill_id, AGAIN)
            self.prerequisite_checks(self.skill_id, depth=0)

    def has_pool(self, skill_id: str) -> bool:
        """A problem pool exists for the skill (ENG-6: no pool, no check)."""
        hidden = self.w.hidden()
        return any(
            r.kind == "problem" and r.status == "active" and r.id not in hidden
            for r in self.w.refs(skill_id)
        )

    def note_unverified(self, skill_id: str, needed_by: str) -> None:
        """ENG-6: a prerequisite with no problem pool yet gets no check; it is listed as
        unverified under Weak areas (STA-11), read from the attempt's diagnosis."""
        rows = self.diag.setdefault(UNVERIFIED, [])
        entry = {"skill": skill_id, "needed_by": needed_by}
        if entry not in rows:
            rows.append(entry)

    def prerequisite_checks(
        self, skill_id: str, *, depth: int, every_direct: bool = False, every: bool = False
    ) -> None:
        for k in prerequisites_by_depth(skill_id, self.skills):
            if not self.has_pool(k):
                self.note_unverified(k, skill_id)
        targets = prerequisite_targets(
            skill_id,
            self.skills,
            self.state_of,
            self.recall,
            every_direct=every_direct,
            every=every,
        )
        targets = [(k, d) for k, d in targets if self.has_pool(k)]
        for i, (k, d) in enumerate(targets):
            card = self.pick_card(k)
            self.add_check(
                NewCheck(
                    skill_id=k,
                    kind="prerequisite",
                    reason=prerequisite_reason(self.skills, k, skill_id),
                    card_id=card,
                    depth=depth + d,
                    after_items=CHECK_AFTER_ITEMS + i,
                )
            )

    def pick_card(
        self, skill_id: str, *, cued: bool = False, prefer_form: str | None = None
    ) -> str | None:
        state = self.state_of(skill_id)
        pick = pick_check_card(
            self.w.refs(skill_id),
            theta=state.elo_theta if state is not None else 0.0,
            tiers=check_tiers(self.skills.get(skill_id), state),
            now_ms=self.now,
            seen=self.w.seen(skill_id),
            exclude={self.outcome.card.id},
            cued=cued,
            prefer_form=prefer_form,
            hidden=self.w.hidden(),
            today_start_ms=self.h.days.start(self.today),
        )
        return None if pick is None else pick.card.id

    def add_check(self, check: NewCheck) -> None:
        open_ = [c for c in self.pending if self.check is None or c.id != self.check.id]
        if any(c.skill_id == check.skill_id and c.kind == check.kind for c in open_):
            return
        if any(c.skill_id == check.skill_id and c.kind == check.kind for c in self.c.checks):
            return
        self.c.checks.append(check)

    # ------------------------------------------------------------ 3. the miss flow

    def blame(self, choice: Any = None, *, factor: float = 1.0) -> dict[str, float]:
        matched_step: int | None = None
        matched = False
        index = self.outcome.matched_wrong
        if index is not None and self.card is not None and 0 <= index < len(self.card.wrong):
            matched, matched_step = True, self.card.wrong[index].step
        return blame(
            self.tags,
            choice=choice,
            step=self.outcome.error_step,
            matched_step=matched_step,
            matched=matched,
            recall=self.recall,
            tap_factor=factor,
        )

    def miss_flow(self, p: float | None) -> None:
        choice = self.outcome.error_choice
        review_event = self.event_for(self.skill_id, self.now)
        can_hold = (
            self.result.effects.stage == "review"
            and review_event is not None
            and review_event.rating == AGAIN
            and self.ctx.state is not None
        )
        if choice in ("slip", "misread") and self.slip is not None:
            self.diag["slip"] = (
                "accepted" if self.slip.accepted else "second" if self.slip.second else "rejected"
            )
            if self.slip.accepted:
                self.diag["no_evidence"] = True
                return
            shares = untapped_blame(self.tags, self.recall)
            self.diag["blame"] = shares
            target = heaviest(shares) or self.skill_id
            if self.slip.second and can_hold:
                self.hold_with_check(target, kind="step", pass_rating=AGAIN, label=None)
            return
        if choice == "step" and self.tags.step(self.outcome.error_step) is not None:
            factor = tap_calibration(self.w.tap_log(self.now)).factor
            self.diag["tap_factor"] = round(factor, 4)
            self.diag["blame"] = self.blame("step", factor=factor)
            tapped = self.tags.step(self.outcome.error_step)
            if tapped is None:
                return
            self.diag["tapped"] = tapped.skill_id
            if can_hold:
                self.hold_with_check(
                    tapped.skill_id, kind="step", pass_rating=AGAIN, label=tapped.label
                )
            return
        if choice == "setup":
            self.diag["blame"] = self.blame("setup")
            if can_hold:
                self.hold_with_check(self.skill_id, kind="cued-twin", pass_rating=None, label=None)
            return
        if choice == "other-method":
            self.diag["blame"] = self.blame("other-method")
            return
        self.diag["blame"] = self.blame(None)
        if can_hold and p is not None and p < ABOVE_LEVEL_P:
            self.diag["above_level"] = True
            self.hold_with_check(self.skill_id, kind="step", pass_rating=AGAIN, label=None)

    def hold_with_check(
        self, target: str, *, kind: CheckKind, pass_rating: int | None, label: str | None
    ) -> None:
        """Hold the problem's verdict and ask for a check (or a cued twin)."""
        form = self.result.answer.attempt.extra.get("elo", {}).get("form")
        if kind == "cued-twin":
            card = self.pick_card(target, cued=True, prefer_form=form)
            if card is None:  # no cued stem anywhere: check the method behind Step 0
                step0 = self.tags.step(0)
                target = step0.skill_id if step0 is not None else self.skill_id
                kind, pass_rating = "step", AGAIN
                card = self.pick_card(target)
        else:
            card = self.pick_card(target)
        if card is None:
            self.diag["check"] = "no problem available"
            if not self.has_pool(target):
                self.note_unverified(target, self.skill_id)
            return  # nothing to check with: the rating map's Again stands
        if kind == "cued-twin":
            reason = twin_reason(self.skills, self.skill_id)
        else:
            reason = step_reason(self.skills, self.skill_id, target, label)
        before = self.ctx.state
        if before is None:
            return
        attempt = self.result.answer.attempt
        skill = self.ctx.skill
        evidence = Evidence(
            day=self.today.isoformat(),
            tier=self.outcome.card.tier,
            clean=False,
            rating=None,
            speed_ms=attempt.extra.get("speed_ms") if attempt.extra.get("baseline_ok") else None,
            form=str(form),
            recall=attempt.predicted_recall,
            elapsed_days=None
            if before.last_review_at is None
            else (self.now - before.last_review_at) / DAY_MS,
            checkup=self.outcome.purpose == "checkup",
            above_exam_tier=self.outcome.card.tier > (skill.exam_tier or 3),
        )
        held = place_hold(
            before,
            self.state,
            at=self.now,
            today=self.today,
            entry=evidence,
            check_skill=target,
            kind=kind,
            pass_rating=pass_rating,
            reason=f"Waiting for its check after the miss on {self.today.isoformat()}",
        )
        own = self.h.adapter_for(self.skill_id)
        held = replace(held, due_at=due_at(held, self.ctx.retention, own, self.h.days))
        self.set_state(held)
        reviews = tuple(e for e in self.result.answer.reviews if e.target_id != self.skill_id)
        fx = self.result.effects
        self.result = replace(
            self.result,
            answer=replace(
                self.result.answer,
                reviews=reviews,
                attempt=replace(self.result.answer.attempt, rating=None),
            ),
            effects=replace(
                fx,
                lapse=False,
                reinforcement_due=False,
                leech=False,
                prerequisite_checks=False,
                textbook_ref=None,
                level_after=held.level,
                demoted=False,
                shaky=held.shaky,
            ),
        )
        self.held = True
        self.diag["held"] = {"check": target, "kind": kind}
        self.add_check(NewCheck(skill_id=target, kind=kind, reason=reason, card_id=card))

    # ------------------------------------------------------------ 4. after effects

    def after_effects(self, *, cued: bool) -> None:
        fx = self.result.effects
        if fx.prerequisite_checks:
            self.prerequisite_checks(
                self.skill_id, depth=0, every_direct=fx.learning_failed, every=fx.leech
            )
        if fx.lapse and self.skill_id not in self.lapsed:
            self.lapsed.append(self.skill_id)
        for lapsed in dict.fromkeys(self.lapsed):
            for pulled in pull_forward(
                lapsed, today=self.today, skills=self.skills, state_of=self.state_of
            ):
                if pulled.skill_id == self.skill_id:
                    self.set_state(pulled)
                else:
                    self.c.states[pulled.skill_id] = pulled
        explicit = self.event_for(self.skill_id, self.now)
        if explicit is not None and self.result.effects.stage == "review":
            self.shadow_track(explicit.rating)
            if self.result.decision.success and explicit.rating >= HARD:
                targets = dict(credit_targets(self.skill_id, self.skills))
                for k, w in self.part_credit.items():  # one credit per skill, the larger
                    targets[k] = max(targets.get(k, 0.0), w)
                self.part_credit = {}
                self.credit(targets)
        if not cued and self.card is not None and self.card.kind == "problem":
            self.method_choice_review()
        self.confident_redo()

    def shadow_track(self, rating: int) -> None:
        shadow = self.w.shadow(self.skill_id)
        own = self.h.adapter_for(self.skill_id)
        recalls = shadow_recalls(shadow, self.ctx.state, self.now, own)
        if recalls is not None:
            self.diag["shadow"] = recalls
        moved = shadow_after_review(shadow, self.ctx.state, rating, self.now, own, self.h.days)
        if moved is not None:
            self.c.put(moved)

    def credit(self, targets: Mapping[str, float] | None = None) -> None:
        mode = self.w.config().credit
        if mode == "on":  # I9: On only once credited predictions win on held-out data
            own = self.h.adapter_for(self.skill_id)
            switch = credit_switch(self.w.recent_attempts(0), own.params_id)
            if not switch.allowed:
                mode = "shadow"
                self.diag["credit_on"] = switch.reason

        def shadow_of(k: str) -> SkillShadow | None:
            stored = self.c.records.get(("SkillShadow", k))
            return stored if isinstance(stored, SkillShadow) else self.w.shadow(k)

        start = self.h.days.start(self.today)

        def credited_today(k: str) -> ImplicitCredit | None:
            given = [
                c
                for c in (*self.w.credits_since(start), *self.c.credits)
                if c.to_skill == k and c.voided_by is None and c.at >= start
            ]
            return max(given, key=lambda c: c.weight) if given else None

        result = partial_credit(
            self.skill_id,
            now=self.now,
            mode=mode,
            skills=self.skills,
            state_of=self.state_of,
            shadow_of=shadow_of,
            last_failure_at=self.w.last_failure_at,
            adapter=self.h.adapter,
            adapter_of=self.h.adapter_for,
            days=self.h.days,
            targets=targets,
            credited_today=credited_today,
        )
        for s in result.shadows:
            self.c.put(s)
        for st in result.states:
            self.c.states[st.skill_id] = st
        self.c.credits.extend(result.credits)
        if result.forced:
            self.diag["credit_forced"] = [*self.diag.get("credit_forced", []), *result.forced]

    def part_effects(self) -> None:
        """Multi-part problems: each part with its own skill reports to that skill."""
        parts = own_skill_parts(self.outcome.parts, self.skill_id)
        if not parts or (self.check is not None and self.check.kind == "diagnostic"):
            return
        credited: dict[str, float] = {}
        log: dict[str, str] = {}
        for part in parts:
            skill = part.reports_to(self.skill_id)
            if skill not in self.skills:
                continue
            if part.correct and not part.gave_up:
                credited[skill] = PART_CREDIT_WEIGHT
                log[part.label] = "credit"
                continue
            self.add_check(
                NewCheck(
                    skill_id=skill,
                    kind="prerequisite",
                    reason=part_reason(self.skills, skill, self.skill_id, part.label),
                    card_id=self.pick_card(skill),
                    depth=1,
                    after_items=CHECK_AFTER_ITEMS,
                )
            )
            log[part.label] = "check"
        for skill in [k for k in credited if any(c.skill_id == k for c in self.c.checks)]:
            credited.pop(skill)  # a skill missed in another part gets its check, not credit
        self.part_credit = credited  # credited with the card's own ENG-7 credit, if any
        self.diag["parts"] = log

    def method_choice_review(self) -> None:
        method = method_choice_skill(self.skill_id, self.skills)
        if method is None or not method_choice_active(method, self.state_of):
            return
        state = self.state_of(method.id)
        if state is None or memory_of(state) is None or hold_of(state) is not None:
            return
        due = due_day(state, self.retention(method.id), self.h.adapter_for(method.id), self.h.days)
        last = state.last_review_at
        if due is None or due > self.today:
            return
        if last is not None and self.h.days.day_of(last) == self.today:
            return
        chose_right = self.result.decision.success or self.outcome.error_choice in (
            "step",
            "other-method",
            "slip",
            "misread",
        )
        if chose_right and self.result.effects.stage == "review":
            self.diag["method_review"] = method.id
            self.review_other(method.id, GOOD, recall=True)

    def confident_redo(self) -> None:
        """A miss submitted sure guarantees the next-day redo, also for an excused slip."""
        if self.slip is None or not self.slip.accepted or self.outcome.facts.unsure:
            return  # every other miss: base grading already set the redo
        if self.ctx.card_user is not None and self.ctx.card_user.redo_due_at is not None:
            return  # a missed redo does not come back again
        tomorrow = self.h.days.start(self.today + timedelta(days=1))
        changes = []
        for r in self.result.answer.changes:
            if isinstance(r, CardUser) and r.card_id == self.outcome.card.id:
                r = replace(r, redo_due_at=tomorrow, redo_guaranteed=True)
            changes.append(r)
        self.result = replace(
            self.result,
            answer=replace(self.result.answer, changes=tuple(changes)),
            effects=replace(self.result.effects, confident_error=True),
        )

    # ------------------------------------------------------------ assemble

    def finish(self) -> GradeResult:
        state = self.state
        if not self.held and HOLD in state.level_evidence and hold_of(state) is None:
            state = without(state, HOLD)  # a settled hold's leftovers
        adjust = state.level_evidence.get(ADJUST)
        if isinstance(adjust, dict) and adjust.get("last_review_at") != state.last_review_at:
            state = without(state, ADJUST)
        self.set_state(state)
        created = [nc.record(created_at=self.now) for nc in self.c.checks]
        if self.c.checks:
            self.diag["checks"] = [nc.as_json() for nc in self.c.checks]
        changes: list[StateRecord] = list(self.result.answer.changes)
        changes += [s for k, s in self.c.states.items() if k != self.skill_id]
        changes += list(self.c.records.values())
        changes += created
        attempt = self.result.answer.attempt
        extra = {**attempt.extra, "diagnosis": {**self.diag}}
        answer = replace(
            self.result.answer,
            attempt=replace(attempt, extra=extra),
            changes=tuple(changes),
            reviews=(*self.c.before, *self.result.answer.reviews, *self.c.after),
            credits=(*self.result.answer.credits, *self.c.credits),
        )
        return replace(self.result, answer=answer)
