"""The day's plan (docs/design/student-model.md, sections 4.3 and 4.6, with the wave 2 changes
of docs/design/wave2-planner.md). Pure: no storage, no clock; today's served items and the
observation history come in as plain values.

What the day holds:
- **New:** a skill whose introduction date has arrived gets its worked example, then up to 3
  tier 1-2 problems in a row until its first first-try success (counted over every day).
- **Growth:** an introduced, uncertified skill gets up to 3 problems a day at its milestone
  tier or the rung below, and stops for the day after 2 consecutive first-try successes.
- **Maintenance:** a certified skill whose calibrated readiness at its certified tier,
  forecast for the next study day (or, within 21 days of an exam covering it, for the exam
  day), falls below target gets one problem at that tier, and one more slot held for the 4.6
  retry: a miss that was mostly execution (top suspect m < 0.5) uses it later in the day.
- **The stuck ladder (wave 2):** after a skill's misses today its next planned item becomes a
  smaller problem (1 miss), a problem of the blamed prerequisite (2), or nothing: the skill is
  set aside until the next study day (3), when it returns with a fresh family.
- **A certification sitting (wave 2, v1.3):** M2 and M3 certify only through one: a closed-book
  block of unseen problems at the milestone tier, after the first 20 minutes of the day.
- **Reference checks:** every 10th item, a uniformly random unseen problem at the current (or
  certified) tier of a uniformly random introduced skill, once the day's new material is done.
- **Caps:** 3 problems per skill per day (reference checks and sittings aside); missed-
  milestone growth at most 40% of the day's items; new material first.

`plan_day` lays out everything left today, as an upper bound: each block and each growth
allowance at its full size, each maintenance problem with its retry slot. `next_item` is its
first item; the caller re-plans after each answer, so blocks end at their first success and
growth stops after two in a row. **Re-plans never add items:** the day's first plan stamps its
size on every item (`WorkItem.day_items`), and a later plan keeps the day's items within it,
leaving out its lowest-priority items when anything new became due.
"""

import random
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, replace
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
    LADDER_PREREQUISITE,
    LADDER_SET_ASIDE,
    MISSED_SHARE,
    NEW_BLOCK_MAX,
    PRIORITY_MISSED,
    PRIORITY_NEW,
    PRIORITY_NORMAL,
    RETRY_MEMORY_SHARE,
    RETURN_FAMILY_DAYS,
    SITTING_MAX_SKILLS,
    SITTING_MILESTONES,
    SITTING_PASS_MIN,
    SITTING_WARMUP_MINUTES,
    SKILL_DAILY_CAP,
    UNCAPPED_ROLES,
)
from core.plan.ladder import (
    Ladder,
    blamed_prerequisite,
    owner,
    owners,
    read_ladder,
    returning,
    top_blamed,
)
from core.plan.order import Ordered, arrange, confusable_pairs
from core.plan.pace import in_scope, milestone_rule, standard_hours
from core.plan.protocol import Predictor
from core.plan.select import (
    Choice,
    Seen,
    SittingPick,
    check_candidates,
    choose_growth_in,
    choose_maintenance,
    choose_new,
    choose_prerequisite,
    choose_return,
    choose_sitting,
    choose_smaller,
    suspects,
)
from core.plan.sitting import (
    block_limits,
    pass_chance,
    practice_ready,
    sat_today,
    sigma_of,
    sitting_id,
    sitting_today,
    waiting,
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
    - `served_today`: the items already served today, in order, with outcomes, each with the
      `WorkItem` as the planner returned it (its `day_items`, `ladder_for` and sitting fields
      keep the day within its first plan and resume a sitting);
    - `rng`: all randomness (reference checks, sittings, confusable adjacency). None: seeded
      from the course, the day and the number of plan items served, so a re-plan at the same
      point gives the same plan;
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
    builder = _Builder(ctx, read_ladder(ctx.served))
    builder.sitting(views, rng)
    builder.new_blocks(views)
    builder.growth(views)
    builder.prerequisites(views)
    builder.maintenance(views)
    builder.apply_ladder()
    builder.returns(views)
    kept, tail = builder.cap_missed()
    mixed = builder.mixed(kept)
    blocks = builder.block_list()
    sitting = list(builder.sitting_items)
    regular = (
        len(mixed)
        + len(tail)
        + sum(len(b) for b in blocks)
        + len(sitting)
        + len(builder.sitting_rest)
    )
    checks = builder.checks(views, rng, regular)
    pairs = confusable_pairs(course.skills)
    served_items = [x.item for x in ctx.plan_served]
    order_seed = rng.random()
    cap = builder.cap
    while True:
        result = arrange(
            blocks,
            mixed,
            checks,
            rng=random.Random(order_seed),  # noqa: S311 - reproducible plans
            served=served_items,
            confusable=pairs,
            continuing=builder.continuing,
            tail=tail,
            sitting=sitting,
            sitting_under_way=builder.sitting_rest,
            warmup=SITTING_WARMUP_MINUTES,
            minutes_served=builder.minutes_served,
        )
        if main_share(served_items, result.items) > MISSED_SHARE + EPS:
            move = max((i for i, it in enumerate(mixed) if it.missed), default=None)
            if move is not None:
                tail = [mixed[move], *tail]
                mixed = mixed[:move] + mixed[move + 1 :]
                continue
        excess = 0 if cap is None else len(served_items) + len(result.items) - cap
        if excess > 0:
            # Re-plans never add items (wave 2): the lowest-priority items give way, the
            # overflow's last first, then the mixed set's last (its last round-robin round),
            # then a sitting not yet started, its last-batched skill.
            before = len(tail) + len(mixed) + len(sitting)
            cut = min(excess, len(tail))
            tail = tail[: len(tail) - cut]
            excess -= cut
            cut = min(excess, len(mixed))
            mixed = mixed[: len(mixed) - cut]
            excess -= cut
            if excess > 0 and sitting:
                last = builder.last_sitting_skill()
                sitting = [i for i in sitting if i.skill_id != last]
                builder.drop_sitting_skill(last)
            if len(tail) + len(mixed) + len(sitting) < before:
                continue  # order what is left (its checks follow the shorter day)
        break
    hours, basis = hours_to_keep_pace(ctx, spent_minutes or {})
    in_tail = {id(i) for i in tail}
    overflow = sum(1 for i in result.items if id(i) in in_tail)
    notes = _notes(ctx, views, result, overflow, builder)
    day_items = cap if cap is not None else len(served_items) + len(result.items)
    items = tuple(replace(i, day_items=day_items) for i in result.items)
    return DayPlan(
        day=today,
        items=items,
        minutes=round(sum(i.expected_minutes for i in items), 6),
        hours_to_keep_pace=hours,
        standard_hours=standard_hours(course.standard, settings),
        behind=tuple(v.skill_id for v in views if v.track == "behind"),
        notes=notes,
        hours_basis=basis,
        statuses=tuple(v.status() for v in views),
        confusable=result.confusable,
        overflow=overflow,
        dropped=result.dropped,
        set_aside=tuple(v.skill_id for v in views if v.skill_id in builder.aside),
        sittings=builder.sittings_log,
        adjacent=result.forced,
        sitting_chances=tuple(builder.chances),
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
    """Collects the day's candidate items, skill by skill, under the per-skill caps.

    Slots: an item uses a daily slot of its `owner` (the stuck skill for a ladder item, else
    its own skill) and counts toward its own skill's 3-a-day cap; reference checks and
    sitting problems use neither.
    """

    def __init__(self, ctx: PlanContext[S], ladder: Ladder) -> None:
        self.ctx = ctx
        self.ladder = ladder
        self.band = ctx.settings.growth_band
        self.aside = frozenset(s for s in ladder.set_aside if s in ctx.skills)
        self.seen = Seen(ctx.history, ctx.today, ctx.served)
        self.served_owned: Counter[ComponentId] = Counter()
        self.served_skill: Counter[ComponentId] = Counter()
        self.served_owned_growth: Counter[ComponentId] = Counter()
        self.served_skill_growth: Counter[ComponentId] = Counter()
        self.day_role: dict[ComponentId, str] = {}  # role of the first slot used today
        for x in ctx.plan_served:
            it = x.item
            if it.problem is None or it.role in UNCAPPED_ROLES:
                continue
            own = owner(it)
            self.served_owned[own] += 1
            self.served_skill[it.skill_id] += 1
            if it.role == "growth":
                self.served_owned_growth[own] += 1
                self.served_skill_growth[it.skill_id] += 1
            self.day_role.setdefault(own, it.role)
        self.planned_owned: Counter[ComponentId] = Counter()
        self.planned_skill: Counter[ComponentId] = Counter()
        self.planned_owned_growth: Counter[ComponentId] = Counter()
        self.planned_skill_growth: Counter[ComponentId] = Counter()
        self.blocks: dict[ComponentId, list[WorkItem]] = {}
        self.lanes: dict[ComponentId, list[WorkItem]] = {}
        self.continuing: ComponentId | None = None
        self.sitting_items: list[WorkItem] = []  # the day's sitting, not started: serve order
        self.sitting_rest: list[WorkItem] = []  # the rest of a sitting under way
        self.sittings_log: tuple[tuple[str, tuple[ComponentId, ...]], ...] = ()
        self.chances: list[tuple[ComponentId, float]] = []
        self.notes: list[str] = []
        self._previous: dict[ComponentId, ProblemSpec | None] = {}
        self.minutes_served = sum(
            x.minutes if x.minutes is not None else x.item.expected_minutes for x in ctx.plan_served
        )
        stamps = [x.item.day_items for x in ctx.plan_served if x.item.day_items is not None]
        self.cap: int | None = min(stamps) if stamps else None

    # ------------------------------------------------------------------ helpers

    def room(self, skill_id: ComponentId) -> int:
        """Problems the skill may still get today: 3 a day outside Focused Practice, counting
        the slots it owns and the problems of its own (a ladder item counts for both)."""
        owned = self.served_owned[skill_id] + self.planned_owned[skill_id]
        own = self.served_skill[skill_id] + self.planned_skill[skill_id]
        return SKILL_DAILY_CAP - max(owned, own)

    def growth_left(self, skill_id: ComponentId) -> int:
        owned = self.served_owned_growth[skill_id] + self.planned_owned_growth[skill_id]
        own = self.served_skill_growth[skill_id] + self.planned_skill_growth[skill_id]
        return GROWTH_ALLOWANCE - max(owned, own)

    def previous(self, skill_id: ComponentId) -> ProblemSpec | None:
        if skill_id not in self._previous:
            self._previous[skill_id] = previous_problem(self.ctx.history, self.ctx.served, skill_id)
        return self._previous[skill_id]

    def stopped(self, skill_id: ComponentId) -> bool:
        """Two consecutive first-try successes today end the skill's growth for the day."""
        streak = 0
        for x in reversed(self.ctx.plan_served):
            if skill_id not in owners(x.item) or x.item.problem is None or x.correct is None:
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

    def _count(self, item: WorkItem, sign: int) -> None:
        if item.problem is None or item.role in UNCAPPED_ROLES:
            return
        own = owner(item)
        self.planned_owned[own] += sign
        self.planned_skill[item.skill_id] += sign
        if item.role == "growth":
            self.planned_owned_growth[own] += sign
            self.planned_skill_growth[item.skill_id] += sign

    def add(self, item: WorkItem, *, to: list[WorkItem] | None = None) -> None:
        """Plan an item: into `to` (a block), else its owner's lane."""
        if item.problem is not None:
            self.seen.add(item.problem.card_id)
            self._previous[item.skill_id] = item.problem
        elif item.example_card is not None:
            self.seen.add(item.example_card)
        self._count(item, 1)
        if to is not None:
            to.append(item)
        else:
            self.lanes.setdefault(owner(item), []).append(item)

    def swap(self, where: list[WorkItem], k: int, new: WorkItem) -> None:
        """Replace the planned item `where[k]` by `new` (a ladder or return item)."""
        old = where[k]
        if old.problem is not None:
            self.seen.discard(old.problem.card_id)
        self._count(old, -1)
        if new.problem is not None:
            self.seen.add(new.problem.card_id)
        self._count(new, 1)
        where[k] = new

    def remove(self, item: WorkItem) -> None:
        for container in (*self.lanes.values(), *self.blocks.values()):
            for k, it in enumerate(container):
                if it is item:
                    del container[k]
                    if item.problem is not None:
                        self.seen.discard(item.problem.card_id)
                    self._count(item, -1)
                    return

    def next_slot(self, skill_id: ComponentId) -> tuple[list[WorkItem], int] | None:
        """The skill's next planned problem: in its new block, else first in its lane."""
        for container in (self.blocks.get(skill_id), self.lanes.get(skill_id)):
            for k, it in enumerate(container or ()):
                if it.problem is not None and it.role not in UNCAPPED_ROLES:
                    return container or [], k
        return None

    def block_list(self) -> list[list[WorkItem]]:
        """The new skills' blocks in course order, a block in progress first."""
        found = [(sid, b) for sid, b in self.blocks.items() if b]
        return [b for sid, b in sorted(found, key=lambda kv: kv[0] != self.continuing)]

    # ------------------------------------------------------------------ the sitting

    def sitting(self, views: Sequence[SkillView], rng: random.Random) -> None:
        """The day's sitting: the rest of one under way, or a new one when skills are due
        (wave 2 section 2, v1.3). Its problems are chosen before any practice, so practice
        never takes the unseen problems a sitting needs."""
        ctx = self.ctx
        today = sitting_today(ctx.served)
        if today.started:
            self._resume(today.sitting, today.block, today.remaining)
            return
        due = [v for v in views if self.sitting_due(v)]
        due.sort(key=lambda v: (_deadline(v), ctx.rank[v.skill_id]))
        sigma = sigma_of(ctx.model, ctx.state)
        chosen: list[tuple[SkillView, SittingPick]] = []
        for v in due:
            if len(chosen) >= SITTING_MAX_SKILLS:
                break
            if v.tier is None:
                continue
            pick = choose_sitting(v.skill, v.tier, self.seen, rng, retired=ctx.retired)
            if pick is None:
                self.notes.append(
                    f"{v.skill_id}: too few tier-{v.tier} problems left for a sitting."
                )
                continue
            chance = pass_chance([ctx.now(p) for p in pick.problems], pick.problems, sigma)
            self.chances.append((v.skill_id, round(chance.chance, 6)))
            if chance.chance < SITTING_PASS_MIN - EPS:
                self.notes.append(
                    f"{v.skill_id}: not yet at pace for its sitting (predicted pass "
                    f"{chance.chance:.2f}: accuracy {chance.accuracy:.2f}, time "
                    f"{chance.pace:.2f}; it needs {SITTING_PASS_MIN:.2f})."
                )
                continue
            if pick.thin:
                self.notes.append(
                    f"{v.skill_id}: few unseen tier-{v.tier} problems are left, so its sitting "
                    "reuses the least recently served ones."
                )
            chosen.append((v, pick))
            for p in pick.problems:
                self.seen.add(p.card_id)
        if not chosen:
            return
        problems = [p for _, pick in chosen for p in pick.problems]
        rng.shuffle(problems)
        sid = sitting_id(ctx.course.course_id, ctx.today)
        block = tuple(p.problem_id for p in problems)
        limits = block_limits(problems)
        self.sitting_items = [self._sitting_item(p, sid, block, limits) for p in problems]
        self.sittings_log = ((sid, tuple(v.skill_id for v, _ in chosen)),)

    def sitting_due(self, v: SkillView) -> bool:
        """Wave 2 section 2's conditions, all but the pass chance: the current milestone is M2
        or M3; readiness at its tier at least the target; 2 or more practice first tries
        there, the last a success; no failed sitting in the 2 study days before today; not
        set aside or sat today."""
        ctx = self.ctx
        current = v.current
        if v.skill_id in self.aside or current is None or v.keep_mode or v.tier is None:
            return False
        if current.name not in SITTING_MILESTONES or not v.introduced or v.state == "new":
            return False
        if v.readiness is None or v.readiness < v.target - EPS:
            return False
        results = ctx.certifier.sittings(v.skill_id, ctx.today)
        if sat_today(results, ctx.today) or waiting(results, ctx.today):
            return False
        at_tier = [o for o in ctx.by_skill.get(v.skill_id, ()) if o.problem.tier == v.tier]
        passed = [r.day for r in results if r.outcome == "pass" and r.tier == v.tier]
        return practice_ready(at_tier, passed)

    def _sitting_item(
        self,
        problem: ProblemSpec,
        sitting: str,
        block: tuple[str, ...],
        limits: Mapping[ComponentId, float],
    ) -> WorkItem:
        pred = self.ctx.now(problem)
        view = self.ctx.view(problem.main_skill)
        milestone = next(
            (
                m.name
                for m in view.milestones
                if m.name in SITTING_MILESTONES and m.tier == problem.tier
            ),
            None,
        )
        return WorkItem(
            skill_id=problem.main_skill,
            role="sitting",
            problem=problem,
            example_card=None,
            expected_minutes=pred.median_minutes,
            priority=PRIORITY_NORMAL,
            tier=problem.tier,
            milestone=milestone,
            p=pred.p,
            reason="sitting",
            sitting=sitting,
            time_limit=round(limits[problem.main_skill], 6),
            sitting_block=block,
        )

    def _resume(self, sitting: str | None, block: Sequence[str], remaining: Sequence[str]) -> None:
        """The rest of the sitting under way, in its order (a set-aside skill's left out)."""
        ctx = self.ctx
        found = {p.problem_id: p for s in ctx.course.skills for p in s.pool}
        problems = [found[pid] for pid in block if pid in found]
        limits = block_limits(problems)
        skills = sorted(
            {p.main_skill for p in problems if p.main_skill in ctx.skills},
            key=lambda s: (_deadline(ctx.view(s)), ctx.rank[s]),
        )  # the batch order: earliest deadline first
        if sitting is not None:
            self.sittings_log = ((sitting, tuple(skills)),)
        for pid in remaining:
            p = found.get(pid)
            if p is None or p.main_skill in self.aside or sitting is None:
                continue
            item = self._sitting_item(p, sitting, tuple(block), limits)
            self.seen.add(p.card_id)
            self.sitting_rest.append(item)

    def last_sitting_skill(self) -> ComponentId:
        """The last skill batched into the sitting not yet started (the latest deadline)."""
        if self.sittings_log and self.sittings_log[0][1]:
            return self.sittings_log[0][1][-1]
        return self.sitting_items[-1].skill_id

    def drop_sitting_skill(self, skill_id: ComponentId) -> None:
        """A skill taken out of a sitting not yet started (the day's plan is full)."""
        self.sitting_items = [i for i in self.sitting_items if i.skill_id != skill_id]
        for log_id, skills in self.sittings_log:
            rest = tuple(s for s in skills if s != skill_id)
            self.sittings_log = ((log_id, rest),) if rest else ()

    # ------------------------------------------------------------------ roles

    def new_blocks(self, views: Sequence[SkillView]) -> None:
        for v in views:
            if v.state != "new" or v.skill_id in self.aside:
                continue
            if v.block.in_progress:
                self.continuing = v.skill_id
            block = self.blocks.setdefault(v.skill_id, [])
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
                self.add(example, to=block)
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
                self.add(self.item(v, "new", choice, block=True), to=block)

    def growth(self, views: Sequence[SkillView]) -> None:
        for v in views:
            sid = v.skill_id
            # A skill whose day began with maintenance keeps to its retry slot (revoked or not).
            if v.growing and v.tier is not None and sid not in self.aside:
                if self.day_role.get(sid) == "maintenance":
                    continue
                self.grow(v, v.tier)

    def grow(self, view: SkillView, tier: int, *, reason: str | None = None) -> None:
        sid = view.skill_id
        if self.stopped(sid):
            return
        suspect = suspects(self.ctx.served, sid)
        missed = view.track == "behind"
        for i in range(min(self.growth_left(sid), self.room(sid))):
            choice = choose_growth_in(
                self.band,
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
            if v.state != "struggling" or v.skill_id in self.aside:
                continue
            for r in v.prerequisites:
                if r in done or r in self.aside:
                    continue
                done.add(r)
                rv = self.ctx.view(r)
                if rv.growing or self.planned_owned_growth[r] > 0:
                    continue  # its own growth covers it
                if self.day_role.get(r) == "maintenance":
                    continue  # its slots today are its maintenance and retry
                tier = rv.tier if rv.tier is not None else _routine_tier(rv.skill)
                if tier is not None:
                    self.grow(rv, tier, reason="prerequisite")

    def maintenance(self, views: Sequence[SkillView]) -> None:
        """One problem for each due skill, and its 4.6 retry slot held from the first plan
        (wave 2: re-plans never add, so a slot an execution miss may need is reserved)."""
        for v in views:
            sid = v.skill_id
            if sid in self.aside or v.tier is None:
                continue
            role = self.day_role.get(sid)
            if role == "maintenance":
                self.retry(v)
                continue
            if role is not None or not v.maintained or self.room(sid) <= 0:
                continue
            if v.assumed and not self.has_own_evidence(v):
                continue  # assumed learned: reference checks test it first
            reason = self.due(v)
            if reason is None:
                continue
            for why in (reason, "retry"):
                if self.room(sid) <= 0:
                    break
                choice = choose_maintenance(
                    v.skill,
                    v.tier,
                    self.ctx.now,
                    self.seen,
                    target=v.target,
                    previous=self.previous(sid),
                    retired=self.ctx.retired,
                )
                if choice is None:
                    break
                self.add(self.item(v, "maintenance", choice, reason=why))

    def retry(self, v: SkillView) -> None:
        """4.6: after the day's maintenance problem was missed and the miss was mostly
        execution (top suspect m < 0.5), its held slot stays for one more problem later (the
        ladder then makes it a smaller one); otherwise the slot is released."""
        sid = v.skill_id
        if self.served_owned[sid] != 1 or self.room(sid) <= 0 or v.tier is None:
            return
        latest = next(
            (
                x
                for x in reversed(self.ctx.plan_served)
                if sid in owners(x.item) and x.item.problem is not None and x.correct is not None
            ),
            None,
        )
        if latest is None or latest.correct or latest.update is None or not latest.update.blame:
            return
        top = max(latest.update.blame, key=lambda kv: (kv[1], kv[0]))[0]
        if dict(latest.update.memory_share).get(top, 0.0) >= RETRY_MEMORY_SHARE - EPS:
            return
        if v.growing:
            choice = choose_growth_in(
                self.band,
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
        elif v.maintained:
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
        else:
            return
        if choice is not None:
            missed = role == "growth" and v.track == "behind"
            self.add(self.item(v, role, choice, missed=missed, reason="retry"))

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

    # ------------------------------------------------------------------ the stuck ladder

    def apply_ladder(self) -> None:
        """Each skill with misses since its last success today: its next planned problem
        becomes the rung's item (it never adds one; set-aside skills have none planned)."""
        ctx = self.ctx
        for sid in sorted(self.ladder.streak, key=lambda s: (ctx.rank.get(s, len(ctx.rank)), s)):
            rung = self.ladder.rung(sid)
            if not 1 <= rung < LADDER_SET_ASIDE or sid not in ctx.skills or sid in self.aside:
                continue
            found = self.next_slot(sid)
            if found is None:
                continue
            where, k = found
            new = self.ladder_item(sid, where[k], rung)
            if new is not None:
                self.swap(where, k, new)

    def ladder_item(self, sid: ComponentId, old: WorkItem, rung: int) -> WorkItem | None:
        ctx = self.ctx
        misses = self.ladder.misses.get(sid, ())
        if not misses:
            return None
        if old.problem is not None:
            self.seen.discard(old.problem.card_id)  # the replaced card may be chosen again
        try:
            if rung >= LADDER_PREREQUISITE:
                found = self.prerequisite_item(sid, old, misses[-2:])
                if found is not None:
                    return found
            last = misses[-1]
            tier = last.item.problem.tier if last.item.problem is not None else (old.tier or 1)
            choice = choose_smaller(
                ctx.skills[sid],
                tier,
                top_blamed(last, sid),
                ctx.now,
                self.seen,
                band=self.band,
                previous=self.previous(sid),
                retired=ctx.retired,
            )
            if choice is None:
                return None
            return replace(
                old,
                problem=choice.problem,
                expected_minutes=ctx.now(choice.problem).median_minutes,
                tier=choice.problem.tier,
                p=choice.p,
                reason=choice.reason,
                ladder=rung,
                ladder_for=sid,
            )
        finally:
            if old.problem is not None:
                self.seen.add(old.problem.card_id)  # swap() takes it back when replaced

    def prerequisite_item(
        self, sid: ComponentId, old: WorkItem, last_two: Sequence[ServedItem]
    ) -> WorkItem | None:
        """Rung 2: a tier 1-2 problem of the component most blamed over the last two misses
        (not the skill itself); when it has no problem to give, the skill's prerequisites in
        course order. It fills the stuck skill's slot (`ladder_for`) and counts toward the
        prerequisite's own 3-a-day cap, taking one of its planned items' places if full."""
        ctx = self.ctx
        skill = ctx.skills[sid]
        top = blamed_prerequisite(last_two, sid, ctx.rank)
        requires = sorted(skill.requires, key=lambda r: (ctx.rank.get(r, len(ctx.rank)), r))
        tried: set[ComponentId] = set()
        for c in [*([top] if top is not None else []), *requires]:
            if c in tried or c == sid or c in self.aside or c not in ctx.skills:
                continue
            tried.add(c)
            info = ctx.skills[c]
            if not info.pool or ctx.view(c).state == "new":
                continue  # no pool, or its own new block covers it
            choice = choose_prerequisite(
                info,
                ctx.now,
                self.seen,
                band=self.band,
                previous=self.previous(c),
                retired=ctx.retired,
            )
            if choice is None or (self.room(c) <= 0 and not self.make_room(c)):
                continue
            return WorkItem(
                skill_id=c,
                role=old.role,
                problem=choice.problem,
                example_card=None,
                expected_minutes=ctx.now(choice.problem).median_minutes,
                priority=old.priority,
                tier=choice.problem.tier,
                milestone=old.milestone,
                missed=old.missed,
                block=old.block,
                p=choice.p,
                reason=choice.reason,
                ladder=LADDER_PREREQUISITE,
                ladder_for=sid,
            )
        return None

    def make_room(self, skill_id: ComponentId) -> bool:
        """Free one of the skill's planned practice slots (its last one) for a ladder item
        that is a problem of this skill; False when it has none to give."""
        lane = self.lanes.get(skill_id, [])
        for it in reversed(lane):
            if it.problem is not None and it.ladder == 0 and it.role not in UNCAPPED_ROLES:
                self.remove(it)
                return self.room(skill_id) > 0
        return False

    def returns(self, views: Sequence[SkillView]) -> None:
        """A skill set aside on its last day of practice returns with a problem from a family
        not served in the last 7 days, at the tier where it was failing (wave 2 section 1)."""
        ctx = self.ctx
        for v in views:
            sid = v.skill_id
            if sid in self.aside or self.ladder.streak.get(sid, 0) > 0:
                continue
            tier = returning(ctx.by_skill.get(sid, ()), ctx.today)
            if tier is None:
                continue
            found = self.next_slot(sid)
            if found is None:
                continue
            where, k = found
            old = where[k]
            if old.problem is not None:
                self.seen.discard(old.problem.card_id)
            choice = choose_return(
                v.skill,
                tier,
                ctx.now,
                self.seen,
                days=RETURN_FAMILY_DAYS,
                band=self.band,
                previous=self.previous(sid),
                retired=ctx.retired,
            )
            if old.problem is not None:
                self.seen.add(old.problem.card_id)
            if choice is None:
                continue
            self.swap(
                where,
                k,
                replace(
                    old,
                    problem=choice.problem,
                    expected_minutes=ctx.now(choice.problem).median_minutes,
                    tier=choice.problem.tier,
                    p=choice.p,
                    reason=choice.reason,
                ),
            )

    # ------------------------------------------------------------------ caps and checks

    def cap_missed(self) -> tuple[set[int], list[WorkItem]]:
        """Which missed-milestone items fit the 40% share of the day's other work: the
        earliest-deadline skills first, one item per skill per round. Returns (ids of the
        items kept in the mixed set, the overflow in that rank order)."""
        ctx = self.ctx
        missed_lanes = [(sid, [i for i in lane if i.missed]) for sid, lane in self.lanes.items()]
        missed_lanes = [(sid, items) for sid, items in missed_lanes if items]

        def urgency(sid: ComponentId) -> tuple[date, int]:
            current = ctx.view(sid).current if sid in ctx.skills else None
            deadline = current.deadline if current and current.deadline else date.max
            return deadline, ctx.rank.get(sid, 0)

        missed_lanes.sort(key=lambda kv: urgency(kv[0]))
        ranked: list[WorkItem] = []
        rounds = max((len(items) for _, items in missed_lanes), default=0)
        for r in range(rounds):
            ranked.extend(items[r] for _, items in missed_lanes if r < len(items))
        others = (
            sum(len(b) for b in self.blocks.values())
            + sum(1 for lane in self.lanes.values() for i in lane if not i.missed)
            + len(self.sitting_items)
            + len(self.sitting_rest)
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
        rank = self.ctx.rank
        lanes = [
            [i for i in lane if not i.missed or id(i) in keep_missed]
            for _, lane in sorted(self.lanes.items(), key=lambda kv: rank.get(kv[0], len(rank)))
        ]
        out: list[WorkItem] = []
        for r in range(max((len(lane) for lane in lanes), default=0)):
            out.extend(lane[r] for lane in lanes if r < len(lane))
        return out

    def checks(
        self, views: Sequence[SkillView], rng: random.Random, regular: int
    ) -> list[WorkItem]:
        """Reference checks in draw order: a uniformly random eligible skill (introduced, past
        its new block, not set aside today, with an unseen problem at its current or certified
        tier), then a uniformly random unseen problem of it. Drawn for every ten the day could
        reach."""
        served = len(self.ctx.plan_served)
        wanted = (served + 2 * regular) // 10 + 1
        out: list[WorkItem] = []
        pool = [
            v
            for v in views
            if v.introduced
            and v.state != "new"
            and not v.skill.background
            and v.tier is not None
            and v.skill_id not in self.aside
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


def _deadline(v: SkillView) -> date:
    current = v.current
    return current.deadline if current is not None and current.deadline else date.max


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
    ctx: PlanContext[S],
    views: Sequence[SkillView],
    result: Ordered,
    overflow: int,
    builder: _Builder[S],
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
        notes.append(f"{len(result.dropped)} item(s) left out: no place for them today.")
    for skill_id, n in Counter(result.forced).items():
        notes.append(
            f"{skill_id}: {n} item(s) right after one of its own: no other skill's item was "
            "left to put between them."
        )
    for v in views:
        if v.skill_id in builder.aside:
            notes.append(
                f"{v.skill_id}: set aside for today after 3 misses in a row. Textbook: "
                f"{v.skill.deck}."
            )
        if v.state == "slip-limited":
            notes.append(f"{v.skill_id}: limited by careless errors. Check your work.")
        elif v.state == "struggling":
            extra = f" Practice added for: {', '.join(v.prerequisites)}." if v.prerequisites else ""
            notes.append(f"{v.skill_id}: struggling. See the textbook section.{extra}")
    notes.extend(dict.fromkeys(builder.notes))
    return tuple(notes)
