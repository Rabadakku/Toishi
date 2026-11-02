"""The day's plan (docs/design/student-model.md v1.1, sections 4.3 and 4.6). Pure: no storage,
no clock; today's served items and the observation history come in as plain values.

What the day holds:
- **New:** a skill whose introduction date has arrived gets its worked example, then up to 3
  tier 1-2 problems in a row until its first first-try success (counted over every day).
- **Growth:** an introduced, uncertified skill gets up to 3 problems a day at its milestone
  tier or the rung below, and stops for the day after 2 consecutive first-try successes.
- **Maintenance:** a certified skill whose calibrated readiness at its certified tier,
  forecast for the next study day (or, within 21 days of an exam covering it, for the exam
  day), falls below target gets one problem at that tier.
- **After a miss (4.6):** a miss that was mostly execution (top suspect m < 0.5) gives the
  skill one more problem later in the session when it has none left.
- **Reference checks:** every 10th item, a uniformly random unseen problem at the current (or
  certified) tier of a uniformly random introduced skill.
- **Caps:** 3 problems per skill per day (reference checks aside, so their draw stays
  uniform); missed-milestone growth at most 40% of the day's items; new material first.

`plan_day` lays out everything left today, as an upper bound: each block and each growth
allowance at its full size. `next_item` is its first item; the caller re-plans after each
answer, so blocks end at their first success and growth stops after two in a row.
"""

import random
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import groupby

from core.learner.types import ComponentId, Observation, ProblemSpec
from core.plan.certify import Certifier, n_eff_needed, readiness, representatives
from core.plan.config import (
    CHECK_EVERY,
    EPS,
    EXAM_HORIZON_DAYS,
    EXAMPLE_MINUTES,
    FEASIBILITY_COMPONENT,
    GROWTH_ALLOWANCE,
    GROWTH_STOP_STREAK,
    HISTORY_MIN_CERTIFICATIONS,
    MISSED_SHARE,
    NEW_BLOCK_MAX,
    PRIORITY_MISSED,
    PRIORITY_NEW,
    PRIORITY_NORMAL,
    RETRY_MEMORY_SHARE,
    SKILL_DAILY_CAP,
)
from core.plan.order import Ordered, confusable_pairs, order
from core.plan.pace import in_scope, milestone_rule, standard_hours
from core.plan.protocol import Predictor
from core.plan.select import (
    Choice,
    Seen,
    check_candidates,
    choose_growth,
    choose_maintenance,
    choose_new,
    suspects,
)
from core.plan.status import PlanContext, SkillView, previous_problem
from core.plan.types import (
    Course,
    CourseSettings,
    DayPlan,
    HoursBasis,
    Role,
    ServedItem,
    SkillInfo,
    WorkItem,
)


def plan_day[S](
    model: Predictor[S],
    state: S,
    certifier: Certifier,
    course: Course,
    settings: CourseSettings,
    today: date,
    now_ms: int,
    served_today: Sequence[ServedItem] = (),
    *,
    rng: random.Random | None = None,
    next_study_day: date | None = None,
    spent_minutes: Mapping[int, float] | None = None,
    examples_seen: Collection[ComponentId] = (),
    retired: Collection[str] = (),
) -> DayPlan:
    """Everything left to do today, in serve order, with minutes and hours to keep pace.

    - `certifier`: `Certifier.from_model` over every first try, today's included (it carries
      the model's priors and a mid-course start's assumed-learned skills;
      `certifier.observations` is the history the variety, struggling and hours rules read);
    - `served_today`: the items already served today, in order, with outcomes;
    - `rng`: all randomness (reference checks, confusable adjacency). None: seeded from the
      course, the day and the number of plan items served, so a re-plan at the same point
      gives the same plan;
    - `next_study_day`: the maintenance forecast horizon (default tomorrow);
    - `spent_minutes`: minutes actually spent per attempt id (hours to keep pace; default the
      valid time of a correct try, else the standard time);
    - `examples_seen`: skills whose worked example the student saw on an earlier day;
    - `retired`: retired card ids, never chosen.
    """
    ctx = PlanContext(
        model,
        state,
        certifier,
        course,
        settings,
        today,
        now_ms,
        served_today,
        next_study_day=next_study_day if next_study_day and next_study_day > today else None,
        examples_seen=examples_seen,
        retired=retired,
    )
    if rng is None:
        seed = f"{course.course_id}|{today.isoformat()}|{len(ctx.plan_served)}"
        rng = random.Random(seed)  # noqa: S311 - reproducible plans, not security
    views = ctx.views()
    builder = _Builder(ctx)
    builder.new_blocks(views)
    builder.growth(views)
    builder.prerequisites(views)
    builder.maintenance(views)
    builder.retries()
    kept, tail = builder.cap_missed()
    mixed = builder.mixed(kept)
    regular = len(mixed) + len(tail) + sum(len(b) for b in builder.blocks)
    checks = builder.checks(views, rng, regular)
    pairs = confusable_pairs(course.skills)
    served_items = [x.item for x in ctx.plan_served]
    order_seed = rng.random()
    while True:
        result = order(
            builder.blocks,
            mixed,
            checks,
            rng=random.Random(order_seed),  # noqa: S311 - reproducible plans
            served=served_items,
            confusable=pairs,
            continuing=builder.continuing,
            tail=tail,
        )
        if main_share(served_items, result.items) <= MISSED_SHARE + EPS:
            break
        move = max((i for i, it in enumerate(mixed) if it.missed), default=None)
        if move is None:
            break
        tail = [mixed[move], *tail]
        mixed = mixed[:move] + mixed[move + 1 :]
    hours, basis = hours_to_keep_pace(ctx, spent_minutes or {})
    in_tail = {id(i) for i in tail}
    overflow = sum(1 for i in result.items if id(i) in in_tail)
    notes = _notes(ctx, views, result, overflow)
    return DayPlan(
        day=today,
        items=result.items,
        minutes=round(sum(i.expected_minutes for i in result.items), 6),
        hours_to_keep_pace=hours,
        standard_hours=standard_hours(course.standard, settings),
        behind=tuple(v.skill_id for v in views if v.track == "behind"),
        notes=notes,
        hours_basis=basis,
        statuses=tuple(v.status() for v in views),
        confusable=result.confusable,
        overflow=overflow,
        dropped=result.dropped,
    )


def next_item[S](
    model: Predictor[S],
    state: S,
    certifier: Certifier,
    course: Course,
    settings: CourseSettings,
    today: date,
    now_ms: int,
    served_today: Sequence[ServedItem] = (),
    *,
    rng: random.Random | None = None,
    next_study_day: date | None = None,
    examples_seen: Collection[ComponentId] = (),
    retired: Collection[str] = (),
) -> WorkItem | None:
    """The next item to serve: the first item of a fresh `plan_day` (call it again after
    each answer, with the answer in `served_today` and in the certifier's history)."""
    plan = plan_day(
        model,
        state,
        certifier,
        course,
        settings,
        today,
        now_ms,
        served_today,
        rng=rng,
        next_study_day=next_study_day,
        examples_seen=examples_seen,
        retired=retired,
    )
    return plan.items[0] if plan.items else None


def main_share(served: Sequence[WorkItem], planned: Sequence[WorkItem]) -> float:
    """The missed-milestone share of the day's items (served, then planned) up to the last
    regular item that is not missed-milestone work: what the 40% cap bounds (design 4.3).
    Missed-milestone items after it are the overflow, served once all else is done."""
    day = [*served, *planned]
    last = max((i for i, it in enumerate(day) if not it.missed and it.role != "check"), default=-1)
    if last < 0:
        return 0.0
    head = day[: last + 1]
    return sum(it.missed for it in head) / len(head)


class _Builder[S]:
    """Collects the day's candidate items, skill by skill, under the per-skill caps."""

    def __init__(self, ctx: PlanContext[S]) -> None:
        self.ctx = ctx
        self.seen = Seen(ctx.history, ctx.today, ctx.served)
        self.served_problems: Counter[ComponentId] = Counter()
        self.served_roles: dict[ComponentId, Counter[str]] = defaultdict(Counter)
        for x in ctx.plan_served:
            if x.item.problem is not None and x.item.role != "check":
                self.served_problems[x.item.skill_id] += 1
                self.served_roles[x.item.skill_id][x.item.role] += 1
        self.planned: Counter[ComponentId] = Counter()
        self.planned_growth: Counter[ComponentId] = Counter()
        self.blocks: list[list[WorkItem]] = []
        self.lanes: dict[ComponentId, list[WorkItem]] = {}
        self.continuing: ComponentId | None = None
        self._previous: dict[ComponentId, ProblemSpec | None] = {}

    # ------------------------------------------------------------------ helpers

    def room(self, skill_id: ComponentId) -> int:
        """Problems the skill may still get today (3 a day outside Focused Practice)."""
        return SKILL_DAILY_CAP - self.served_problems[skill_id] - self.planned[skill_id]

    def previous(self, skill_id: ComponentId) -> ProblemSpec | None:
        if skill_id not in self._previous:
            self._previous[skill_id] = previous_problem(self.ctx.history, self.ctx.served, skill_id)
        return self._previous[skill_id]

    def stopped(self, skill_id: ComponentId) -> bool:
        """Two consecutive first-try successes today end the skill's growth for the day."""
        streak = 0
        for x in reversed(self.ctx.plan_served):
            if x.item.skill_id != skill_id or x.item.problem is None or x.correct is None:
                continue
            if not x.correct:
                return False
            streak += 1
            if streak >= GROWTH_STOP_STREAK:
                return True
        return False

    def item(
        self,
        view: SkillView,
        role: Role,
        choice: Choice,
        *,
        missed: bool = False,
        reason: str | None = None,
        block: bool = False,
    ) -> WorkItem:
        pred = self.ctx.now(choice.problem)
        priority = PRIORITY_NEW if role == "new" else PRIORITY_NORMAL
        if missed:
            priority = PRIORITY_MISSED
        return WorkItem(
            skill_id=view.skill_id,
            role=role,
            problem=choice.problem,
            example_card=None,
            expected_minutes=pred.median_minutes,
            priority=priority,
            tier=choice.problem.tier,
            milestone=None if view.current is None else view.current.name,
            missed=missed,
            block=block,
            p=choice.p,
            reason=reason or choice.reason,
        )

    def add(self, item: WorkItem, *, lane: bool = True) -> None:
        sid = item.skill_id
        if item.problem is not None:
            self.seen.add(item.problem.card_id)
            self.planned[sid] += 1
            self._previous[sid] = item.problem
            if item.role == "growth":
                self.planned_growth[sid] += 1
        elif item.example_card is not None:
            self.seen.add(item.example_card)
        if lane:
            self.lanes.setdefault(sid, []).append(item)

    # ------------------------------------------------------------------ roles

    def new_blocks(self, views: Sequence[SkillView]) -> None:
        for v in views:
            if v.state != "new":
                continue
            if v.block.in_progress:
                self.continuing = v.skill_id
            block: list[WorkItem] = []
            milestone = None if v.current is None else v.current.name
            if not v.block.example_today and v.block.example_card is not None:
                example = WorkItem(
                    skill_id=v.skill_id,
                    role="new",
                    problem=None,
                    example_card=v.block.example_card,
                    expected_minutes=EXAMPLE_MINUTES,
                    priority=PRIORITY_NEW,
                    milestone=milestone,
                    block=True,
                    reason="example",
                )
                self.add(example, lane=False)
                block.append(example)
            for _ in range(min(NEW_BLOCK_MAX - v.block.problems, self.room(v.skill_id))):
                choice = choose_new(
                    v.skill,
                    self.ctx.now,
                    self.seen,
                    previous=self.previous(v.skill_id),
                    retired=self.ctx.retired,
                )
                if choice is None:
                    break
                it = self.item(v, "new", choice, block=True)
                self.add(it, lane=False)
                block.append(it)
            if block:
                self.blocks.append(block)

    def growth(self, views: Sequence[SkillView]) -> None:
        for v in views:
            if v.growing and v.tier is not None:
                self.grow(v, v.tier)

    def grow(self, view: SkillView, tier: int, *, reason: str | None = None) -> None:
        sid = view.skill_id
        if self.stopped(sid):
            return
        allowance = GROWTH_ALLOWANCE - self.served_roles[sid]["growth"] - self.planned_growth[sid]
        suspect = suspects(self.ctx.served, sid)
        missed = view.track == "behind"
        for i in range(min(allowance, self.room(sid))):
            choice = choose_growth(
                view.skill,
                tier,
                self.ctx.now,
                self.seen,
                previous=self.previous(sid),
                bottleneck=view.bottleneck if view.tier == tier else None,
                suspect=suspect if i == 0 else (),
                retired=self.ctx.retired,
            )
            if choice is None:
                return
            self.add(self.item(view, "growth", choice, missed=missed, reason=reason))

    def prerequisites(self, views: Sequence[SkillView]) -> None:
        """Struggling skills: growth for the prerequisites of their weakest component."""
        done: set[ComponentId] = set()
        for v in views:
            if v.state != "struggling":
                continue
            for r in v.prerequisites:
                if r in done:
                    continue
                done.add(r)
                rv = self.ctx.view(r)
                if rv.growing or self.planned_growth[r] > 0:
                    continue  # its own growth covers it
                tier = rv.tier if rv.tier is not None else _routine_tier(rv.skill)
                if tier is not None:
                    self.grow(rv, tier, reason="prerequisite")

    def maintenance(self, views: Sequence[SkillView]) -> None:
        for v in views:
            if not v.maintained or v.tier is None:
                continue
            sid = v.skill_id
            if self.served_roles[sid]["maintenance"] > 0 or self.room(sid) <= 0:
                continue
            if v.assumed and not self.has_own_evidence(v):
                continue  # assumed learned: reference checks test it first
            reason = self.due(v)
            if reason is None:
                continue
            choice = choose_maintenance(
                v.skill,
                v.tier,
                self.ctx.now,
                self.seen,
                target=v.target,
                previous=self.previous(sid),
                retired=self.ctx.retired,
            )
            if choice is not None:
                self.add(self.item(v, "maintenance", choice, reason=reason))

    def has_own_evidence(self, view: SkillView) -> bool:
        post = view.posterior
        return post is not None and post.n_eff >= n_eff_needed(timed=view.timed) - EPS

    def due(self, view: SkillView) -> str | None:
        """'forecast' when readiness at the certified tier, forecast for the next study day,
        is below target; 'exam' when an exam within 21 days covers the skill and the forecast
        for its day is below the exam's target; else None."""
        ctx = self.ctx
        tier = view.tier
        if tier is None:
            return None
        nxt = readiness(ctx.forecast(ctx.moment(ctx.next_study_day)), view.skill, tier, ctx.retired)
        if nxt is not None and nxt < view.target - EPS:
            return "forecast"
        for exam in ctx.settings.exams:
            ahead = (exam.day - ctx.today).days
            if not 0 <= ahead <= EXAM_HORIZON_DAYS or not in_scope(view.skill.deck, exam):
                continue
            target = ctx.settings.accuracy_target if exam.target is None else exam.target
            at_exam = readiness(ctx.forecast(ctx.moment(exam.day)), view.skill, tier, ctx.retired)
            if at_exam is not None and at_exam < target - EPS:
                return "exam"
        return None

    def retries(self) -> None:
        """4.6: after a miss that was mostly execution, one more problem later today."""
        latest: dict[ComponentId, ServedItem] = {}
        for x in self.ctx.plan_served:
            if x.item.problem is not None and x.correct is not None:
                latest[x.item.skill_id] = x
        for sid, x in latest.items():
            if x.correct or x.update is None or not x.update.blame:
                continue
            top = max(x.update.blame, key=lambda kv: (kv[1], kv[0]))[0]
            m = dict(x.update.memory_share).get(top, 0.0)
            if m >= RETRY_MEMORY_SHARE - EPS or sid not in self.ctx.skills:
                continue
            if self.planned[sid] > 0 or self.room(sid) <= 0:
                continue
            v = self.ctx.view(sid)
            if v.tier is None or not v.introduced or v.state == "new":
                continue
            if v.growing:
                choice = choose_growth(
                    v.skill,
                    v.tier,
                    self.ctx.now,
                    self.seen,
                    previous=self.previous(sid),
                    bottleneck=v.bottleneck,
                    suspect=suspects(self.ctx.served, sid),
                    retired=self.ctx.retired,
                )
                role: Role = "growth"
            else:
                choice = choose_maintenance(
                    v.skill,
                    v.tier,
                    self.ctx.now,
                    self.seen,
                    target=v.target,
                    previous=self.previous(sid),
                    retired=self.ctx.retired,
                )
                role = "maintenance"
            if choice is not None:
                missed = role == "growth" and v.track == "behind"
                self.add(self.item(v, role, choice, missed=missed, reason="retry"))

    # ------------------------------------------------------------------ caps and checks

    def cap_missed(self) -> tuple[set[int], list[WorkItem]]:
        """Which missed-milestone items fit the 40% share of the day's other work: the
        earliest-deadline skills first, one item per skill per round. Returns (ids of the
        items kept in the mixed set, the overflow in that rank order)."""
        ctx = self.ctx
        missed_lanes = [(sid, [i for i in lane if i.missed]) for sid, lane in self.lanes.items()]
        missed_lanes = [(sid, items) for sid, items in missed_lanes if items]

        def urgency(sid: ComponentId) -> tuple[date, int]:
            current = ctx.view(sid).current
            deadline = current.deadline if current and current.deadline else date.max
            return deadline, ctx.rank.get(sid, 0)

        missed_lanes.sort(key=lambda kv: urgency(kv[0]))
        ranked: list[WorkItem] = []
        rounds = max((len(items) for _, items in missed_lanes), default=0)
        for r in range(rounds):
            ranked.extend(items[r] for _, items in missed_lanes if r < len(items))
        others = sum(len(b) for b in self.blocks) + sum(
            1 for lane in self.lanes.values() for i in lane if not i.missed
        )
        served = [x.item for x in ctx.plan_served]
        served_missed = sum(i.missed for i in served)
        keep_n = 0
        for k in range(len(ranked), -1, -1):
            total = len(served) + others + k
            total += _checks_in(len(served), others + k)
            if served_missed + k <= MISSED_SHARE * total + EPS:
                keep_n = k
                break
        return {id(i) for i in ranked[:keep_n]}, ranked[keep_n:]

    def mixed(self, keep_missed: set[int]) -> list[WorkItem]:
        """The mixed set in round-robin order over skills (course order), so maintenance and
        growth interleave; missed-milestone items beyond the share left out."""
        lanes = [
            [i for i in lane if not i.missed or id(i) in keep_missed]
            for _, lane in sorted(self.lanes.items(), key=lambda kv: self.ctx.rank[kv[0]])
        ]
        out: list[WorkItem] = []
        for r in range(max((len(lane) for lane in lanes), default=0)):
            out.extend(lane[r] for lane in lanes if r < len(lane))
        return out

    def checks(
        self, views: Sequence[SkillView], rng: random.Random, regular: int
    ) -> list[WorkItem]:
        """Reference checks in draw order: a uniformly random eligible skill (introduced, past
        its new block, with an unseen problem at its current or certified tier), then a
        uniformly random unseen problem of it. Drawn for every ten the day could reach."""
        served = len(self.ctx.plan_served)
        wanted = (served + 2 * regular) // 10 + 1
        out: list[WorkItem] = []
        pool = [
            v
            for v in views
            if v.introduced and v.state != "new" and not v.skill.background and v.tier is not None
        ]
        for _ in range(wanted):
            eligible = [
                (v, v.tier)
                for v in pool
                if v.tier is not None
                and check_candidates(v.skill, v.tier, self.seen, self.ctx.retired)
            ]
            if not eligible:
                break
            v, tier = rng.choice(eligible)
            problem = rng.choice(check_candidates(v.skill, tier, self.seen, self.ctx.retired))
            pred = self.ctx.now(problem)
            item = WorkItem(
                skill_id=v.skill_id,
                role="check",
                problem=problem,
                example_card=None,
                expected_minutes=pred.median_minutes,
                priority=PRIORITY_NORMAL,
                tier=problem.tier,
                milestone=None if v.current is None else v.current.name,
                p=pred.p,
                reason="check",
            )
            self.seen.add(problem.card_id)
            out.append(item)
        return out


def _checks_in(served: int, regular: int) -> int:
    """About how many checks `regular` more items bring after `served` plan items: one at
    every 10th position, always followed by a regular item (an estimate for the share cap;
    the order places them for real)."""
    pos, checks, left = served, 0, regular
    while left > 0:
        pos += 1
        if pos % CHECK_EVERY == 0:
            checks += 1
        else:
            left -= 1
    return checks


def _routine_tier(skill: SkillInfo) -> int | None:
    """A background prerequisite's growth tier: routine homework (tier 2) when it has such
    problems, else its lowest tier."""
    tiers = {p.tier for p in skill.pool}
    if not tiers:
        return None
    return 2 if 2 in tiers else min(tiers)


# ---------------------------------------------------------------------- hours and notes


def attempt_minutes(obs: Observation, spent: Mapping[int, float]) -> float:
    """Minutes an attempt took: as recorded, else its valid solving time, else its standard
    time (a stand-in for a miss, whose time the observation doesn't carry)."""
    found = spent.get(obs.attempt_id)
    if found is not None:
        return found
    if obs.minutes is not None:
        return obs.minutes
    return obs.problem.standard_minutes


@dataclass(frozen=True, slots=True)
class Certified:
    skill_id: ComponentId
    tier: int
    day: date


def certified_milestones[S](ctx: PlanContext[S]) -> list[Certified]:
    """Every milestone (M1-M3) certified from evidence so far, with its first day."""
    out: list[Certified] = []
    for sid, ms in ctx.schedule.milestones.items():
        if sid in ctx.schedule.assumed:
            continue
        for m in ms:
            if m.name == "keep":
                continue
            tier, timed, target = milestone_rule(m, ctx.settings)
            st = ctx.certifier.state(sid, tier, ctx.today, timed=timed, target=target)
            if st.first is not None:
                out.append(Certified(sid, m.tier, st.first))
    return out


def minutes_per_milestone[S](
    ctx: PlanContext[S], certified: Sequence[Certified], spent: Mapping[int, float]
) -> dict[int, float]:
    """Mean minutes actually spent per certified milestone, by tier: a skill's minutes from
    its previous certification (or its first attempt) through the day of this one, split
    evenly among milestones first certified that same day."""
    per_tier: dict[int, list[float]] = defaultdict(list)
    by_skill: dict[ComponentId, list[Certified]] = defaultdict(list)
    for c in certified:
        by_skill[c.skill_id].append(c)
    for sid, certs in by_skill.items():
        obs = ctx.by_skill.get(sid, [])
        prev: date | None = None
        for day, group in groupby(sorted(certs, key=lambda c: c.day), key=lambda c: c.day):
            same_day = list(group)
            mins = sum(
                attempt_minutes(o, spent)
                for o in obs
                if (prev is None or o.study_day > prev) and o.study_day <= day
            )
            for c in same_day:
                per_tier[c.tier].append(mins / len(same_day))
            prev = day
    return {t: sum(v) / len(v) for t, v in per_tier.items()}


def hours_to_keep_pace[S](
    ctx: PlanContext[S], spent: Mapping[int, float]
) -> tuple[float | None, HoursBasis]:
    """Hours per week to keep pace (design 4.3), never capped.

    From the student's history once about 10 milestones are certified: minutes per certified
    milestone by tier, times the milestones the pace schedule brings next week (deadlines in
    the 7 days after today), plus the maintenance the forecasts make due in those days (one
    problem per due skill; every day for a slip-limited skill). Until then the course's
    standard outside-class hours stand in.
    """
    certified = certified_milestones(ctx)
    if len(certified) < HISTORY_MIN_CERTIFICATIONS:
        return standard_hours(ctx.course.standard, ctx.settings), "standard"
    per_tier = minutes_per_milestone(ctx, certified, spent)
    week = [ctx.today + timedelta(days=d) for d in range(1, 8)]
    end = ctx.settings.end
    due: Counter[int] = Counter()
    for sid, ms in ctx.schedule.milestones.items():
        if sid in ctx.schedule.assumed:
            continue
        for m in ms:
            if m.deadline is None or not week[0] <= m.deadline <= week[-1]:
                continue
            if end is not None and m.deadline > end:
                continue
            due[m.tier] += 1
    growth = sum(n * _nearest(per_tier, t) for t, n in due.items())
    upkeep = 0.0
    for v in ctx.views():
        if not v.maintained or v.tier is None:
            continue
        reps = representatives(v.skill, v.tier, ctx.retired)
        if not reps:
            continue
        minutes = sum(ctx.now(p).median_minutes for p in reps) / len(reps)
        if v.state == "slip-limited":
            upkeep += minutes * len(week)
            continue
        for day in week:
            r = readiness(ctx.forecast(ctx.moment(day)), v.skill, v.tier, ctx.retired)
            if r is not None and r < v.target - EPS:
                upkeep += minutes
                break
    return (growth + upkeep) / 60.0, "history"


def _nearest(per_tier: Mapping[int, float], tier: int) -> float:
    """A tier's minutes per milestone, borrowed from the nearest tier with history (the
    higher on a tie) when it has none."""
    if tier in per_tier:
        return per_tier[tier]
    best = min(per_tier, key=lambda t: (abs(t - tier), -t))
    return per_tier[best]


@dataclass(frozen=True, slots=True)
class Feasibility:
    """Design 4.3: the best attainable chance on a typical target-tier problem,
    (1 - s) * 0.99^K, against the accuracy target."""

    tier: int
    slip: float
    components: float  # K: mean component count of the course's target-tier problems
    best: float
    target: float

    @property
    def ok(self) -> bool:
        return self.best >= self.target - EPS

    def note(self) -> str:
        return (
            f"At tier {self.tier} the best attainable first-try chance is "
            f"(1 - {self.slip:.3f}) x 0.99^{self.components:.1f} = {self.best:.3f}, "
            f"below the accuracy target {self.target:.2f}."
        )


def feasibility[S](
    model: Predictor[S], state: S, course: Course, settings: CourseSettings
) -> Feasibility | None:
    """None when the course has no problem at the target tier."""
    problems = [
        p
        for s in course.skills
        if not s.background
        for p in s.pool
        if p.tier == settings.target_tier
    ]
    if not problems:
        return None
    k = sum(len(p.components) for p in problems) / len(problems)
    slip = model.slip(state)
    best = (1.0 - slip) * FEASIBILITY_COMPONENT**k
    return Feasibility(settings.target_tier, slip, k, best, settings.accuracy_target)


def _notes[S](
    ctx: PlanContext[S], views: Sequence[SkillView], result: Ordered, overflow: int
) -> tuple[str, ...]:
    notes: list[str] = []
    feas = feasibility(ctx.model, ctx.state, ctx.course, ctx.settings)
    if feas is not None and not feas.ok:
        notes.append(feas.note())
    if overflow:
        notes.append(
            f"{overflow} catch-up item(s) for missed milestones come after the rest of today's "
            "work: missed-milestone work is held to 40% of the day until then."
        )
    if result.dropped:
        notes.append(
            f"{len(result.dropped)} item(s) left out: no other skill to put between them and "
            "the same skill's items."
        )
    for v in views:
        if v.state == "slip-limited":
            notes.append(f"{v.skill_id}: limited by careless errors. Check your work.")
        elif v.state == "struggling":
            extra = f" Practice added for: {', '.join(v.prerequisites)}." if v.prerequisites else ""
            notes.append(f"{v.skill_id}: struggling. See the textbook section.{extra}")
    return tuple(notes)
