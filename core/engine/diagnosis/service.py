"""Diagnosis: the storage-bound facade (grading with the hook, the daily weak-spot run, the
queue's questions about checks)."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from core.engine.config import AGAIN, DAY_MS
from core.engine.diagnosis.blame import TapCalibration, tap_calibration
from core.engine.diagnosis.checks import check_reason
from core.engine.diagnosis.config import CHECK_EXPIRY_DAYS, UNVERIFIED, WEAK_WINDOW_DAYS
from core.engine.diagnosis.hook import DiagnosisHook
from core.engine.diagnosis.items import (
    find_error_highlighted,
    find_error_unlocked,
    method_choice_active,
)
from core.engine.diagnosis.verdict import EXAMPLE_FIRST, Settled, diagnosis_of, hold_of, settle
from core.engine.diagnosis.weakspots import (
    DiagnosticPlan,
    SkillEvidence,
    TierFlagNote,
    busy_skills,
    diagnostic_cards,
    find_weak_spots,
    plan_diagnostics,
    residual_cutoffs,
    sets_left_this_week,
    wrong_tier_flags,
)
from core.engine.diagnosis.world import StorageWorld, World
from core.engine.fsrs_adapter import FsrsAdapter
from core.engine.grading import ProblemOutcome
from core.engine.service import Engine, Recorded
from core.model import (
    Attempt,
    DiagnosticSet,
    PendingCheck,
    ReviewEvent,
    SkillState,
    StateRecord,
    WeakSpot,
)
from core.storage import Storage


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyReport:
    flagged: list[SkillEvidence] = field(default_factory=list)  # Algorithm A's flags
    weak_spots: list[WeakSpot] = field(default_factory=list)  # written, with ids
    sets: list[DiagnosticSet] = field(default_factory=list)
    checks: list[PendingCheck] = field(default_factory=list)
    expired: list[PendingCheck] = field(default_factory=list)
    settled: list[str] = field(default_factory=list)  # skills whose old held miss settled


@dataclass(frozen=True, slots=True, kw_only=True)
class UnverifiedPrerequisite:
    """ENG-6 / STA-11: a prerequisite listed as "unverified" (no problem pool yet)."""

    skill_id: str
    name: str
    textbook_ref: str | None
    needed_by: tuple[str, ...]
    status: str = "unverified"


class Diagnosis:
    """Grading with error diagnosis, plus the daily run. Keeps no state: every call reads
    fresh rows, so one instance per thread (or per call) is fine."""

    def __init__(self, storage: Storage, *, adapter: FsrsAdapter | None = None) -> None:
        self._storage = storage
        self._adapter = adapter

    def world(self) -> StorageWorld:
        base = Engine(self._storage, adapter=self._adapter)
        return StorageWorld(self._storage, retention=base.retention)

    def engine(self) -> Engine:
        """An Engine whose grading runs the diagnosis hook (each answer reads fresh rows;
        settings and FSRS parameters are read now)."""
        base = Engine(self._storage, adapter=self._adapter)
        hook = DiagnosisHook(
            lambda: StorageWorld(self._storage, retention=base.retention),
            settings=base.settings(),
            adapter=base.adapter(),
            days=base.days(),
            adapter_of=base.skill_adapters(),
        )
        return Engine(self._storage, hooks=(hook,), adapter=self._adapter)

    def grade(self, outcome: ProblemOutcome) -> Recorded:
        return self.engine().grade(outcome)

    # ------------------------------------------------------------ the daily run (ENG-15)

    def daily(self, at_ms: int | None = None) -> DailyReport:
        """Once a day: cancel checks nobody served within a week, run the weak-spot finder
        and schedule diagnostic sets (at most the weekly setting). One transaction."""
        now = at_ms if at_ms is not None else self._storage.db.clock.now_ms()
        study_day = Engine(self._storage, adapter=self._adapter).days().day_of(now).isoformat()
        plan = daily_plan(self.world(), now=now, settle_hold=self._settler())
        return self._storage.users.atomic(
            lambda store: plan.write(
                now=now,
                study_day=study_day,
                apply=store.apply,
                settle_attempt=store.settle_attempt,
            )
        )

    def _settler(self) -> Callable[[SkillState], Settled]:
        """ENG-6: a held miss whose check is never answered settles as plain Again at the
        miss's time (rating map default; counts for Level and leeches)."""
        base = Engine(self._storage, adapter=self._adapter)
        settings, days, adapter_of = base.settings(), base.days(), base.skill_adapters()
        users, packs = self._storage.users, self._storage.packs

        def settle_hold(state: SkillState) -> Settled:
            skill = packs.skill(state.skill_id)
            return settle(
                state,
                AGAIN,
                adapter=adapter_of(state.skill_id),
                days=days,
                settings=settings,
                exam_tier=(skill.exam_tier if skill is not None else None) or 3,
                targets={t.tier: t.target_ms for t in users.skill_tiers(state.skill_id)},
                retention=base.retention(state.skill_id),
            )

        return settle_hold

    # ------------------------------------------------------------ for the queue and stats

    def reason(self, check: PendingCheck) -> str:
        """The "Why is this here?" sentence of a pending check."""
        if check.reason is not None:
            return check.reason
        users = self._storage.users
        attempt = users.attempt(check.attempt_id) if check.attempt_id is not None else None
        spot = None
        if check.kind == "diagnostic":
            sets = [d for d in users.diagnostic_sets() if d.skill_id == check.skill_id]
            ids = {d.weak_spot_id for d in sets if check.card_id in d.card_ids}
            spot = next((s for s in users.weak_spots() if s.id in ids), None)
        skills = {k.id: k for k in self._storage.packs.skills()}
        return check_reason(check, skills=skills, attempt=attempt, weak_spot=spot)

    def tap_calibration(self, at_ms: int | None = None) -> TapCalibration:
        now = at_ms if at_ms is not None else self._storage.db.clock.now_ms()
        return tap_calibration(self.world().tap_log(now))

    def tier_flags(self, at_ms: int | None = None) -> list[TierFlagNote]:
        now = at_ms if at_ms is not None else self._storage.db.clock.now_ms()
        return wrong_tier_flags(self._storage.users.attempts(since=now - 90 * DAY_MS), now=now)

    def unverified_prerequisites(self) -> list[UnverifiedPrerequisite]:
        """Weak areas (STA-11) data, ENG-6: prerequisites a check wanted but which have no
        problem pool yet, with the skills that needed them. A skill leaves the list once a
        pack gives it problems (its checks then run as specified)."""
        users, packs = self._storage.users, self._storage.packs
        hidden = {k for k, m in users.card_marks().items() if m.hidden or m.suspended}
        needed: dict[str, list[str]] = {}
        for a in users.attempts():
            for row in diagnosis_of(a).get(UNVERIFIED, ()) or ():
                if isinstance(row, dict) and row.get("skill"):
                    by = needed.setdefault(str(row["skill"]), [])
                    if row.get("needed_by") and str(row["needed_by"]) not in by:
                        by.append(str(row["needed_by"]))
        out: list[UnverifiedPrerequisite] = []
        for skill_id, by in sorted(needed.items()):
            pool = [
                r
                for r in packs.card_refs(skill_id=skill_id)
                if r.kind == "problem" and r.status == "active" and r.id not in hidden
            ]
            if pool:
                continue
            skill = packs.skill(skill_id)
            out.append(
                UnverifiedPrerequisite(
                    skill_id=skill_id,
                    name=skill.name if skill is not None else skill_id,
                    textbook_ref=skill.textbook_ref if skill is not None else None,
                    needed_by=tuple(by),
                )
            )
        return out

    def needs_example(self, skill_id: str) -> bool:
        """A worked example comes before this skill's next problem (unsolved cued twin)."""
        state = self._storage.users.skill_state(skill_id)
        return state is not None and bool(state.level_evidence.get(EXAMPLE_FIRST))

    def method_choice_active(self, skill_id: str) -> bool:
        skill = self._storage.packs.skill(skill_id)
        users = self._storage.users
        return (
            skill is not None
            and skill.method_choice
            and method_choice_active(skill, users.skill_state)
        )

    def find_error_status(self, skill_id: str) -> tuple[bool, bool]:
        """(unlocked, highlighted) for find-the-error items on a skill."""
        history: Sequence[Attempt] = self._storage.users.attempts(skill_id=skill_id)
        return find_error_unlocked(history), find_error_highlighted(history)


type Apply = Callable[[Sequence[StateRecord]], tuple[StateRecord, ...]]
type SettleAttempt = Callable[[int, Sequence[ReviewEvent], Sequence[StateRecord]], object]


@dataclass(frozen=True, slots=True, kw_only=True)
class HeldSettlement:
    """An old held miss settled as Again: its attempt, the event and the new state."""

    attempt_id: int
    event: ReviewEvent | None
    state: SkillState


def daily_run(world: World, *, now: int, study_day: str, apply: Apply) -> DailyReport:
    """The daily run over any World; `apply` writes state rows and returns them stored."""
    return daily_plan(world, now=now).write(now=now, study_day=study_day, apply=apply)


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyPlan:
    expired: list[PendingCheck]
    flagged: list[SkillEvidence]
    plans: list[DiagnosticPlan]
    settled: list[HeldSettlement] = field(default_factory=list)

    def write(
        self,
        *,
        now: int,
        study_day: str,
        apply: Apply,
        settle_attempt: SettleAttempt | None = None,
    ) -> DailyReport:
        """Write it. The weak spot goes first: its set links to its id. Old held misses
        settle through `settle_attempt` (events bound to the held attempt)."""
        report = DailyReport(flagged=self.flagged)
        if self.expired:
            apply(self.expired)
            report.expired.extend(self.expired)
        if settle_attempt is not None:
            for held in self.settled:
                events = [held.event] if held.event is not None else []
                settle_attempt(held.attempt_id, events, [held.state])
                report.settled.append(held.state.skill_id)
        for plan in self.plans:
            (spot,) = apply([plan.weak_spot(now=now, study_day=study_day)])
            if not isinstance(spot, WeakSpot):
                raise TypeError("a weak spot was written as another record")
            diag, checks = plan.records(weak_spot_id=spot.id, now=now)
            written = apply([diag, *checks])
            report.weak_spots.append(spot)
            report.sets.extend(r for r in written if isinstance(r, DiagnosticSet))
            report.checks.extend(r for r in written if isinstance(r, PendingCheck))
        return report


def daily_plan(
    world: World, *, now: int, settle_hold: Callable[[SkillState], Settled] | None = None
) -> DailyPlan:
    """Everything the daily run reads: expired checks, old held misses (ENG-6: settled as
    plain Again at the miss's time after 7 days, whether the check expired or its section
    was switched Off), flags and diagnostic sets."""
    settled = _old_holds(world, now, settle_hold) if settle_hold is not None else []
    triggers = {h.attempt_id for h in settled}
    expired = [
        replace(c, status="cancelled", resolved_at=now)
        for c in world.pending_checks()
        if c.kind != "diagnostic"
        and (now - c.created_at >= CHECK_EXPIRY_DAYS * DAY_MS or c.attempt_id in triggers)
    ]
    spots, sets = list(world.weak_spots()), list(world.diagnostic_sets())
    cutoffs = residual_cutoffs(spots)
    flagged = find_weak_spots(
        world.recent_attempts(now - WEAK_WINDOW_DAYS * DAY_MS),
        now=now,
        busy=busy_skills(spots, sets),
        cutoff_of=cutoffs.get,
    )
    skills = world.skills()

    def cards_for(skill_id: str) -> tuple[str, ...] | None:
        skill = skills.get(skill_id)
        if skill is None:
            return None
        return diagnostic_cards(
            world.refs(skill_id),
            skill=skill,
            state=world.state(skill_id),
            now=now,
            seen=world.seen(skill_id),
            hidden=world.hidden(),
        )

    budget = sets_left_this_week(sets, now=now, per_week=world.config().diagnostic_per_week)
    plans = plan_diagnostics(flagged, budget=budget, skills=skills, cards_for=cards_for)
    return DailyPlan(expired=expired, flagged=flagged, plans=plans, settled=settled)


def _old_holds(
    world: World, now: int, settle_hold: Callable[[SkillState], Settled]
) -> list[HeldSettlement]:
    out: list[HeldSettlement] = []
    for skill_id in world.skills():
        state = world.state(skill_id)
        hold = hold_of(state)
        if state is None or hold is None:
            continue
        at = int(hold["at"])
        if now - at < CHECK_EXPIRY_DAYS * DAY_MS:
            continue
        trigger = next(
            (a for a in world.history(skill_id) if a.at == at and a.id is not None), None
        )
        if trigger is None or trigger.id is None:
            continue  # its miss was voided: nothing to settle
        settled = settle_hold(state)
        out.append(HeldSettlement(attempt_id=trigger.id, event=settled.event, state=settled.state))
    return out
