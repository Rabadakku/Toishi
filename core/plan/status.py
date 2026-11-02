"""Skill statuses (docs/design/student-model.md v1.1, section 4.2) and the context that one
plan or status query shares.

Each skill is in one state: not yet introduced; new (its worked example and first problems
are still to come); growth at its current milestone tier; maintenance (every milestone
certified); Keep (after the course end date, or assumed learned on a mid-course start, and
certified at the Keep target); **slip-limited** (every course component's execution e >= 0.97
and the direct posterior still below target, the shortfall explained by the slip rate: no
component growth, "check your work"); **struggling** (3 study days at the full growth
allowance with no rise in the direct posterior: the textbook reference, and growth for the
prerequisites of its weakest component). Separately, it is ahead, on track or behind against
its milestone deadlines.
"""

from collections import defaultdict
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.certify import Certifier, Posterior, first_try_success, n_eff_needed, readiness
from core.plan.certify import representatives as reps_of
from core.plan.config import (
    DAY_MS,
    EPS,
    GROWTH_ALLOWANCE,
    NEW_BLOCK_MAX,
    NEW_TIERS,
    PLAN_ROLES,
    SLIP_LIMITED_E,
    STRUGGLE_DAYS,
)
from core.plan.pace import check_settings, milestone_rule, schedule
from core.plan.protocol import Forecast, Predictor, is_course_component
from core.plan.types import (
    Course,
    CourseSettings,
    Milestone,
    ServedItem,
    SkillInfo,
    SkillState,
    SkillStatus,
    Track,
)


@dataclass(frozen=True, slots=True)
class Block:
    """A new skill's block (design 4.3): the worked example, then up to 3 tier 1-2 problems
    until the first first-try success."""

    done: bool
    problems: int  # role-new first tries so far, every day
    example_today: bool  # the worked example was served today
    in_progress: bool  # today's latest plan item is this block's and the block goes on
    example_card: str | None  # the example card, or a tier 1-2 problem's card shown solved


@dataclass(frozen=True, slots=True)
class SkillView:
    """Everything the planner knows about one skill on the day (a SkillStatus and more)."""

    skill: SkillInfo
    intro: date | None
    milestones: tuple[Milestone, ...]
    current: Milestone | None
    state: SkillState
    track: Track
    level: int | None
    posterior: Posterior | None
    readiness: float | None
    pace_ok: bool | None
    tier: int | None  # the working tier: the current milestone's, else the certified one's
    timed: bool
    target: float
    keep_mode: bool
    assumed: bool
    block: Block
    bottleneck: ComponentId | None
    prerequisites: tuple[ComponentId, ...]

    @property
    def skill_id(self) -> ComponentId:
        return self.skill.skill_id

    @property
    def introduced(self) -> bool:
        return self.state != "not-introduced"

    @property
    def growing(self) -> bool:
        """Gets growth problems today (struggling skills keep their own growth)."""
        return self.state in ("growth", "struggling")

    @property
    def maintained(self) -> bool:
        """Gets a maintenance problem when its forecast falls below target."""
        return self.state in ("maintenance", "keep", "slip-limited")

    def status(self) -> SkillStatus:
        return SkillStatus(
            skill_id=self.skill_id,
            intro=self.intro,
            milestones=self.milestones,
            current=self.current,
            state=self.state,
            track=self.track,
            level=self.level,
            posterior_mean=None if self.posterior is None else self.posterior.mean,
            readiness=self.readiness,
            pace_ok=self.pace_ok,
            bottleneck=self.bottleneck,
            prerequisites=self.prerequisites,
            assumed=self.assumed,
        )


class PlanContext[S]:
    """What one plan or status query looks at, with caches shared by its rules.

    `certifier.observations` is the history: every first try, today's included.
    `served_today`: today's served items in order (examples included), with outcomes.
    """

    def __init__(
        self,
        model: Predictor[S],
        state: S,
        certifier: Certifier,
        course: Course,
        settings: CourseSettings,
        today: date,
        now_ms: int,
        served_today: Sequence[ServedItem] = (),
        *,
        next_study_day: date | None = None,
        examples_seen: Collection[ComponentId] = (),
        retired: Collection[str] = (),
    ) -> None:
        check_settings(settings)
        self.model = model
        self.state = state
        self.certifier = certifier
        self.course = course
        self.settings = settings
        self.today = today
        self.now_ms = now_ms
        self.served = tuple(served_today)
        self.plan_served = tuple(x for x in self.served if x.item.role in PLAN_ROLES)
        self.next_study_day = next_study_day or today + timedelta(days=1)
        self.examples_seen = frozenset(examples_seen)
        self.retired = frozenset(retired)
        self.schedule = schedule(course, settings)
        self.skills = {s.skill_id: s for s in course.skills}
        ordered = sorted(course.skills, key=lambda s: (s.order, s.skill_id))
        self.rank = {s.skill_id: i for i, s in enumerate(ordered)}
        self.history = certifier.observations
        by_skill: dict[ComponentId, list[Observation]] = defaultdict(list)
        for obs in self.history:
            by_skill[obs.problem.main_skill].append(obs)
        self.by_skill = dict(by_skill)
        self._forecasts: dict[int, Forecast[S]] = {}
        self._views: dict[ComponentId, SkillView] = {}

    # ------------------------------------------------------------------ helpers

    def forecast(self, at_ms: int) -> Forecast[S]:
        found = self._forecasts.get(at_ms)
        if found is None:
            found = Forecast(self.model, self.state, at_ms)
            self._forecasts[at_ms] = found
        return found

    @property
    def now(self) -> Forecast[S]:
        return self.forecast(self.now_ms)

    def moment(self, day: date) -> int:
        """A moment on `day` at today's time of day (for forecasts)."""
        return self.now_ms + (day - self.today).days * DAY_MS

    def is_course(self, component: ComponentId) -> bool:
        return is_course_component(self.model, component, self.course.course_id)

    def keep_mode(self, skill_id: ComponentId) -> bool:
        end = self.settings.end
        return skill_id in self.schedule.assumed or (end is not None and self.today > end)

    def views(self) -> list[SkillView]:
        """Every skill of the course, in course order."""
        return [self.view(s.skill_id) for s in sorted(self.skills.values(), key=self._key)]

    def _key(self, s: SkillInfo) -> int:
        return self.rank[s.skill_id]

    # ------------------------------------------------------------------ one skill

    def view(self, skill_id: ComponentId) -> SkillView:
        found = self._views.get(skill_id)
        if found is None:
            found = self._view(self.skills[skill_id])
            self._views[skill_id] = found
        return found

    def _view(self, skill: SkillInfo) -> SkillView:
        sid = skill.skill_id
        intro = self.schedule.intro.get(sid)
        ms = self.schedule.milestones.get(sid, ())
        block = self.block(skill)
        if skill.background or intro is None or intro > self.today:
            return SkillView(
                skill=skill,
                intro=intro,
                milestones=ms,
                current=None,
                state="not-introduced",
                track="on-track",
                level=self.certifier.level(sid, self.today),
                posterior=None,
                readiness=None,
                pace_ok=None,
                tier=None,
                timed=False,
                target=self.settings.accuracy_target,
                keep_mode=False,
                assumed=False,
                block=block,
                bottleneck=None,
                prerequisites=(),
            )
        assumed = sid in self.schedule.assumed
        keep_mode = self.keep_mode(sid)
        working = tuple(m for m in ms if (m.name == "keep") == keep_mode)
        current = next((m for m in working if not self.certified(sid, m)), None)
        top = current or (working[-1] if working else None)
        tier: int | None = None
        timed, target = False, self.settings.accuracy_target
        if top is not None:
            tier, timed, target = milestone_rule(top, self.settings)
        posterior = None
        ready: float | None = None
        pace_ok: bool | None = None
        bottleneck: ComponentId | None = None
        if tier is not None:
            posterior = self.certifier.posterior(sid, tier, self.today, timed=timed, target=target)
            ready = readiness(self.now, skill, tier, self.retired)
            pace_ok = self.pace_ok(skill, tier)
            bottleneck = self.bottleneck(skill, tier)
        state: SkillState
        prereqs: tuple[ComponentId, ...] = ()
        if not assumed and not block.done:
            state = "new"
        elif current is None:
            state = "keep" if keep_mode else "maintenance"
        elif (
            tier is not None
            and posterior is not None
            and self.slip_limited(skill, tier, timed, target, posterior)
        ):
            state = "slip-limited"
        elif tier is not None and self.struggling(skill, working, current, tier, timed, target):
            state = "struggling"
            prereqs = self.prerequisites_of(bottleneck, sid)
        else:
            state = "growth"
        return SkillView(
            skill=skill,
            intro=intro,
            milestones=ms,
            current=current,
            state=state,
            track="on-track" if keep_mode else track(working, current, self.today),
            level=self.certifier.level(sid, self.today),
            posterior=posterior,
            readiness=ready,
            pace_ok=pace_ok,
            tier=tier,
            timed=timed,
            target=target,
            keep_mode=keep_mode,
            assumed=assumed,
            block=block,
            bottleneck=bottleneck,
            prerequisites=prereqs,
        )

    def certified(self, skill_id: ComponentId, milestone: Milestone) -> bool:
        tier, timed, target = milestone_rule(milestone, self.settings)
        return self.certifier.certified(skill_id, tier, self.today, timed=timed, target=target)

    def pace_ok(self, skill: SkillInfo, tier: int) -> bool | None:
        """At pace over the representative problems: their predicted medians sum to at most
        their standard times (the pace rule, median <= T*, on a typical set)."""
        reps = reps_of(skill, tier, self.retired)
        if not reps:
            return None
        median = sum(self.now(p).median_minutes for p in reps)
        return median <= sum(p.standard_minutes for p in reps) + EPS

    def bottleneck(self, skill: SkillInfo, tier: int) -> ComponentId | None:
        """The course component with the lowest q_k over the skill's pool at the tier
        (design 4.4). Background components are never the bottleneck (critique 6)."""
        lowest: dict[ComponentId, float] = {}
        for problem in skill.pool:
            if problem.tier != tier or problem.card_id in self.retired:
                continue
            for k, q in self.now(problem).q:
                if self.is_course(k) and q < lowest.get(k, 2.0):
                    lowest[k] = q
        if not lowest:
            return None
        return min(lowest, key=lambda k: (round(lowest[k], 12), k))

    def block(self, skill: SkillInfo) -> Block:
        """The new skill's block from the history and today's served items."""
        sid = skill.skill_id
        mine = self.by_skill.get(sid, [])
        problems = sum(1 for o in mine if o.role == "new")
        success = any(first_try_success(o, timed=False) for o in mine)
        example_today = any(
            x.item.skill_id == sid and x.item.problem is None and x.item.example_card is not None
            for x in self.served
        )
        available = [
            p
            for p in skill.pool
            if p.tier in NEW_TIERS
            and p.card_id not in self.retired
            and not any(
                x.item.problem is not None and x.item.problem.card_id == p.card_id
                for x in self.served
            )
        ]
        example = skill.example_card or _shown_solved(skill, self.retired)
        seen_example = example_today or sid in self.examples_seen
        done = (
            success
            or problems >= NEW_BLOCK_MAX
            or (not available and (seen_example or example is None))
        )
        last = self.plan_served[-1].item if self.plan_served else None
        in_progress = not done and last is not None and last.skill_id == sid and last.block
        return Block(
            done=done,
            problems=problems,
            example_today=example_today,
            in_progress=in_progress,
            example_card=example,
        )

    def slip_limited(
        self, skill: SkillInfo, tier: int, timed: bool, target: float, posterior: Posterior
    ) -> bool:
        """Design 4.2: every course component's e >= 0.97 at the tier, and the direct
        posterior still below target (with the evidence to judge it), the shortfall explained
        by the slip rate s. Explained means both: the model's chance over the representative
        problems reaches the target without slips but not with them,
        P_raw < target <= P_raw / (1 - s), so growing components can't close the gap; and
        the observed shortfall is no larger than slips account for, mean / (1 - s) >= target.
        """
        if posterior.mean >= target - EPS:
            return False
        if posterior.n_eff < n_eff_needed(timed=timed) - EPS:
            return False
        execution: list[float] = []
        for problem in skill.pool:
            if problem.tier == tier and problem.card_id not in self.retired:
                execution.extend(e for k, e in self.now(problem).e if self.is_course(k))
        if not execution or min(execution) < SLIP_LIMITED_E - EPS:
            return False
        reps = reps_of(skill, tier, self.retired)
        slip = self.model.slip(self.state)
        if not reps or slip >= 1.0:
            return False
        p_raw = sum(self.now(p).p_raw for p in reps) / len(reps)
        if not p_raw < target - EPS <= p_raw / (1.0 - slip):
            return False
        return posterior.mean >= (1.0 - slip) * target - EPS

    def growth_days(self, skill_id: ComponentId) -> dict[date, int]:
        """Growth first tries per study day for the skill."""
        out: dict[date, int] = defaultdict(int)
        for obs in self.by_skill.get(skill_id, ()):
            if obs.role == "growth":
                out[obs.study_day] += 1
        return dict(out)

    def struggling(
        self,
        skill: SkillInfo,
        working: tuple[Milestone, ...],
        current: Milestone,
        tier: int,
        timed: bool,
        target: float,
    ) -> bool:
        """The skill's last 3 growth days since its current milestone became current were
        all at the full allowance (3 growth problems), and the direct posterior at the end of
        the last is not above its value before the first."""
        sid = skill.skill_id
        since = self.current_since(sid, working, current)
        days = sorted(d for d in self.growth_days(sid).items() if since is None or d[0] > since)
        last = days[-STRUGGLE_DAYS:]
        if len(last) < STRUGGLE_DAYS or any(n < GROWTH_ALLOWANCE for _, n in last):
            return False
        cert = self.certifier
        before = cert.posterior(sid, tier, last[0][0], timed=timed, target=target, before=True)
        after = cert.posterior(sid, tier, last[-1][0], timed=timed, target=target)
        return after.mean <= before.mean + EPS

    def current_since(
        self, skill_id: ComponentId, working: tuple[Milestone, ...], current: Milestone
    ) -> date | None:
        """The day the current milestone became current: the latest certification day of
        the milestones before it (None: it has been current since the introduction)."""
        days: list[date] = []
        for m in working[: working.index(current)]:
            tier, timed, target = milestone_rule(m, self.settings)
            st = self.certifier.state(skill_id, tier, self.today, timed=timed, target=target)
            found = st.since or st.first
            if found is not None:
                days.append(found)
        return max(days) if days else None

    def prerequisites_of(
        self, component: ComponentId | None, skill_id: ComponentId
    ) -> tuple[ComponentId, ...]:
        """Growth targets for a struggling skill: the prerequisites of its weakest component
        that the course has problems for and that are introduced (or background)."""
        if component is None or component not in self.skills:
            return ()
        out: list[ComponentId] = []
        for r in self.skills[component].requires:
            info = self.skills.get(r)
            if r == skill_id or info is None or not info.pool:
                continue
            intro = self.schedule.intro.get(r)
            if info.background or (intro is not None and intro <= self.today):
                out.append(r)
        return tuple(out)


def _shown_solved(skill: SkillInfo, retired: Collection[str]) -> str | None:
    """Without an example card, the worked example is a tier-1 problem shown solved (the
    lowest tier-1-2 problem ID)."""
    found = sorted(
        (p for p in skill.pool if p.tier in NEW_TIERS and p.card_id not in retired),
        key=lambda p: (p.tier, p.problem_id),
    )
    return found[0].card_id if found else None


def track(working: tuple[Milestone, ...], current: Milestone | None, today: date) -> Track:
    """Behind when the current milestone's deadline has passed; ahead when it lies past the
    milestone the schedule is on now (the first whose deadline is today or later), or when
    every milestone is certified before the last deadline; else on track."""
    if current is not None and current.deadline is not None and current.deadline < today:
        return "behind"
    due = next((m for m in working if m.deadline is not None and m.deadline >= today), None)
    if due is None:
        return "on-track"
    if current is None:
        return "ahead"
    return "ahead" if working.index(current) > working.index(due) else "on-track"


def status[S](
    model: Predictor[S],
    state: S,
    certifier: Certifier,
    course: Course,
    settings: CourseSettings,
    skill_id: ComponentId,
    today: date,
    now_ms: int,
    *,
    served_today: Sequence[ServedItem] = (),
    examples_seen: Collection[ComponentId] = (),
    retired: Collection[str] = (),
) -> SkillStatus:
    """One skill's status (design 4.2)."""
    ctx = PlanContext(
        model,
        state,
        certifier,
        course,
        settings,
        today,
        now_ms,
        served_today,
        examples_seen=examples_seen,
        retired=retired,
    )
    return ctx.view(skill_id).status()


def statuses[S](
    model: Predictor[S],
    state: S,
    certifier: Certifier,
    course: Course,
    settings: CourseSettings,
    today: date,
    now_ms: int,
    *,
    served_today: Sequence[ServedItem] = (),
    examples_seen: Collection[ComponentId] = (),
    retired: Collection[str] = (),
) -> tuple[SkillStatus, ...]:
    """Every skill's status, in course order."""
    ctx = PlanContext(
        model,
        state,
        certifier,
        course,
        settings,
        today,
        now_ms,
        served_today,
        examples_seen=examples_seen,
        retired=retired,
    )
    return tuple(v.status() for v in ctx.views())


def previous_problem(
    history: Sequence[Observation], served: Sequence[ServedItem], skill_id: ComponentId
) -> ProblemSpec | None:
    """The skill's latest problem: served today, else its latest first try."""
    for x in reversed(served):
        if x.item.skill_id == skill_id and x.item.problem is not None:
            return x.item.problem
    for obs in reversed(history):
        if obs.problem.main_skill == skill_id:
            return obs.problem
    return None
