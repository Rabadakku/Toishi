"""Stand-ins for `core.learner` and `core.plan` until branches model-core and plan-core merge.

They follow design v1.1 closely enough to exercise the harness and give provisional P1
numbers, which the report labels "stand-in". They are not the implementations under test.

`StandinModel` implements 3.2 to 3.5 (conjunctive prediction with the uncertainty-adjusted
execution term, FSRS-6 memory on a phi clock, per-tier recalibration, the 3.4 update with
blame, memory share, the 7-day memory match, soft counts with the same-day weight, the
observed-information execution step and drift, theta-hat priors, and a running time model).

`StandinPlanner` implements 4.1 and 4.3 to 4.5 in simplified form: section-hour intro dates,
milestones M1-M3, the 3.7 Beta certifier with hysteresis, new material first (worked example
then up to 3 tier 1-2 problems until a success), growth (3 a day at the milestone tier or the
rung below, stop after 2 successes in a row, band [0.70, 0.90] with the bottleneck
preference), maintenance from the next-day readiness forecast, a reference check every 10th
item, missed-milestone work at most 40% of any prefix of the session while other work remains,
the per-skill daily cap of 3 and no card twice a day. Refit (3.6) covers only the per-tier
recalibration (a, b), adopted with the 0.003-nat margin and a bootstrap p < 0.1.

Simplifications, listed so nobody mistakes them for the spec: no slip, delta4, phi, tau or
sigma refit (tau and sigma follow running statistics); no struggling or slip-limited
statuses; no exams, mid-course start or confusable adjacency; no extra problem after an
execution miss; the certifier prior and the maintenance forecast average over the first 3
representative problems instead of up to 10.
"""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Final

from core.learner.types import (
    ComponentId,
    ComponentInfo,
    ComponentState,
    MemoryState,
    Observation,
    Prediction,
    ProblemSpec,
    SharedParams,
    StudentState,
    UpdateRecord,
)
from core.plan.types import (
    Course,
    CourseSettings,
    DayPlan,
    Milestone,
    Role,
    SkillInfo,
    WorkItem,
)
from tools.sim2.common import DAY_MS, EPOCH, logit, normal_cdf, rng_for, sigmoid
from tools.sim2.fsrs6 import AGAIN, DEFAULT, GOOD, Fsrs6

PI_OVER_8: Final = math.pi / 8.0
REPRESENTATIVE: Final = 3  # problems per (skill, tier) for priors and forecasts (design: <= 10)
EXAMPLE_MINUTES: Final = 3.0
TIME_PRIOR_WEIGHT: Final = 4.0
SKILL_SPEED_KAPPA: Final = 5.0
THETA_SHRINK: Final = 20.0
GROWTH_PER_DAY: Final = 3
DAILY_CAP: Final = 3
NEW_BLOCK: Final = 3
CHECK_EVERY: Final = 10
MISSED_SHARE: Final = 0.40
BAND: Final = (0.70, 0.90)


def _day_of(at_ms: int) -> date:
    return EPOCH + timedelta(days=at_ms // DAY_MS)


# ---------------------------------------------------------------- model (design 3)


class StandinModel:
    """Design 3.2-3.5 on the section 8 data types (see the module docstring)."""

    def __init__(self, catalog: Mapping[ComponentId, ComponentInfo], fsrs: Fsrs6 = DEFAULT):
        self.catalog = catalog
        self.background = frozenset(c for c, info in catalog.items() if info.background)
        self.fsrs = fsrs

    def new_state(self, params: SharedParams) -> StudentState:
        return StudentState(params=params)

    # -- pieces

    def _prior(self, state: StudentState, comp: ComponentId) -> tuple[float, float]:
        p = state.params
        if comp in self.background:
            return p.prior_background_mean + state.theta_hat, p.prior_background_var
        return p.prior_new_mean + state.theta_hat, p.prior_new_var

    def _component(self, state: StudentState, comp: ComponentId) -> ComponentState:
        cs = state.components.get(comp)
        if cs is None:
            mu, var = self._prior(state, comp)
            cs = ComponentState(mu=mu, var=var)
            state.components[comp] = cs
        return cs

    @staticmethod
    def _delta(params: SharedParams, tier: int) -> float:
        return params.delta4 if tier == 4 else params.delta5 if tier >= 5 else 0.0

    def _eta(self, params: SharedParams, comp: ComponentId, cs: ComponentState) -> float:
        if comp in self.background:
            return cs.mu
        return cs.mu + params.gamma * math.log1p(cs.c) + params.rho * math.log1p(cs.f)

    def time_params(self, state: StudentState) -> tuple[float, float]:
        """(tau, sigma_T): the priors moved by the running residual statistics."""
        mean, m2, n = state.time_stats
        p = state.params
        tau = (TIME_PRIOR_WEIGHT * p.tau + n * mean) / (TIME_PRIOR_WEIGHT + n)
        sigma = math.sqrt((TIME_PRIOR_WEIGHT * p.sigma_t**2 + m2) / (TIME_PRIOR_WEIGHT + n))
        return tau, sigma

    def skill_offset(self, state: StudentState, skill: ComponentId) -> float:
        total, count = state.skill_speed.get(skill, (0.0, 0))
        return total / (count + SKILL_SPEED_KAPPA)

    def _n_bar(self, state: StudentState, problem: ProblemSpec) -> float:
        course = [c for c in problem.components if c not in self.background]
        if not course:
            return 0.0
        total = 0.0
        for c in course:
            cs = state.components.get(c)
            total += cs.n if cs is not None else 0.0
        return total / len(course)

    # -- the contract

    def predict(self, state: StudentState, problem: ProblemSpec, at_ms: int) -> Prediction:
        params = state.params
        delta = self._delta(params, problem.tier)
        day_ord = _day_of(at_ms).toordinal()
        qs: list[tuple[ComponentId, float]] = []
        es: list[tuple[ComponentId, float]] = []
        rs: list[tuple[ComponentId, float]] = []
        p_raw = 1.0 - params.slip
        for comp in problem.components:
            cs = state.components.get(comp)
            if cs is None:
                mu_eta, var = self._prior(state, comp)
                r = 1.0
            else:
                mu_eta = self._eta(params, comp, cs)
                var = cs.var
                if cs.last_var_day is not None:
                    var += params.q_drift * max(0, day_ord - cs.last_var_day.toordinal())
                r = 1.0
                if comp not in self.background and cs.memory is not None:
                    elapsed = params.phi * (at_ms - cs.memory.last_ms) / DAY_MS
                    r = self.fsrs.retrievability(elapsed, cs.memory.stability)
            e = sigmoid((mu_eta - delta) / math.sqrt(1.0 + PI_OVER_8 * var))
            q = e * r
            p_raw *= q
            qs.append((comp, q))
            es.append((comp, e))
            rs.append((comp, r))
        tier = min(max(problem.tier, 1), 5)
        p = sigmoid(params.calib_a[tier - 1] + params.calib_b * logit(p_raw))
        tau, _ = self.time_params(state)
        median = problem.standard_minutes * math.exp(
            tau
            + self.skill_offset(state, problem.main_skill)
            - params.alpha * math.log1p(self._n_bar(state, problem))
        )
        return Prediction(
            p=p,
            p_raw=p_raw,
            q=tuple(qs),
            e=tuple(es),
            r=tuple(rs),
            median_minutes=median,
            pace_ok=median <= problem.standard_minutes,
        )

    def p_fast(self, state: StudentState, problem: ProblemSpec, prediction: Prediction) -> float:
        """The model's P(time <= T*) from its median and sigma_T."""
        _, sigma = self.time_params(state)
        z = math.log(problem.standard_minutes / prediction.median_minutes) / sigma
        return normal_cdf(z)

    def update(self, state: StudentState, obs: Observation) -> UpdateRecord:
        params = state.params
        problem = obs.problem
        pred = self.predict(state, problem, obs.at_ms)
        failed = obs.aided or not obs.correct
        q = dict(pred.q)
        e = dict(pred.e)
        r = dict(pred.r)
        p_raw = pred.p_raw
        blame: dict[ComponentId, float] = {}
        for comp in problem.components:
            if not failed or p_raw >= 1.0:
                blame[comp] = 0.0
            else:
                blame[comp] = min(1.0, max(0.0, (1.0 - q[comp]) / (1.0 - p_raw)))
        if failed and obs.matched_wrong is not None:
            star = next((c for i, c in problem.wrong_components if i == obs.matched_wrong), None)
            if star is not None and star in blame:
                kappa = params.kappa
                named = blame[star]
                for comp in blame:
                    blame[comp] = (1.0 - kappa) * blame[comp]
                blame[star] = kappa + (1.0 - kappa) * named
        share: dict[ComponentId, float] = {}
        delta = self._delta(params, problem.tier)
        n_bar = self._n_bar(state, problem)
        for comp in problem.components:
            cs = self._component(state, comp)
            course = comp not in self.background
            e_k, r_k = e[comp], r[comp]
            m_k = (1.0 - r_k) / (1.0 - e_k * r_k) if course and e_k * r_k < 1.0 else 0.0
            share[comp] = m_k
            b_k = blame[comp]
            sig = sigmoid(self._eta(params, comp, cs) - delta)  # no uncertainty adjustment
            if course:
                self._memory_update(state, cs, obs, 1.0 - b_k * m_k)
                if cs.today != obs.study_day:
                    cs.today = obs.study_day
                    cs.successes_today = 0
                w_day = 1.0 if cs.successes_today == 0 else params.same_day_weight
                cs.c += (1.0 - b_k) * w_day
                cs.f += b_k * (1.0 - m_k)
                if not failed:
                    cs.successes_today += 1
                cs.n += 1.0
            # execution posterior: one step on the marginal likelihood (3.4 step 3)
            if cs.last_var_day is not None and obs.study_day > cs.last_var_day:
                cs.var += params.q_drift * (obs.study_day - cs.last_var_day).days
            cs.last_var_day = obs.study_day
            if not failed:
                g = 1.0 - sig
                h = sig * (1.0 - sig)
            else:
                a = (1.0 - params.slip) * r_k
                for other, q_other in q.items():
                    if other != comp:
                        a *= q_other
                u = a * sig
                u1 = a * sig * (1.0 - sig)
                u2 = u1 * (1.0 - 2.0 * sig)
                g = -u1 / (1.0 - u)
                h = max(0.0, (u2 * (1.0 - u) + u1 * u1) / (1.0 - u) ** 2)
            cs.var = 1.0 / (1.0 / cs.var + h)
            cs.mu += cs.var * g
            cs.attempts += 1
        if obs.correct and not obs.aided and obs.minutes is not None and obs.minutes > 0:
            resid = math.log(obs.minutes / problem.standard_minutes) + params.alpha * math.log1p(
                n_bar
            )
            mean, m2, n = state.time_stats
            n += 1
            d1 = resid - mean
            mean += d1 / n
            m2 += d1 * (resid - mean)
            state.time_stats = (mean, m2, n)
            tau, _ = self.time_params(state)
            total, count = state.skill_speed.get(problem.main_skill, (0.0, 0))
            state.skill_speed[problem.main_skill] = (total + resid - tau, count + 1)
        state.last_at_ms = obs.at_ms
        return UpdateRecord(
            prediction=pred,
            blame=tuple(blame.items()),
            memory_share=tuple(share.items()),
        )

    def _memory_update(
        self, state: StudentState, cs: ComponentState, obs: Observation, recalled: float
    ) -> None:
        fsrs = self.fsrs
        mem = cs.memory
        if mem is None:
            s_good, d_good = fsrs.initial(GOOD)
            s_again, d_again = fsrs.initial(AGAIN)
        else:
            elapsed = max(0, (obs.study_day - mem.last_day).days)
            r_now = fsrs.retrievability(state.params.phi * elapsed, mem.stability)
            s_good, d_good = fsrs.review(mem.stability, mem.difficulty, GOOD, elapsed, r_now)
            s_again, d_again = fsrs.review(mem.stability, mem.difficulty, AGAIN, elapsed, r_now)
        recalled = min(max(recalled, 0.0), 1.0)
        difficulty = recalled * d_good + (1.0 - recalled) * d_again
        if recalled >= 1.0:
            stability = s_good
        elif recalled <= 0.0:
            stability = s_again
        else:
            target = recalled * fsrs.retrievability(7.0, s_good) + (
                1.0 - recalled
            ) * fsrs.retrievability(7.0, s_again)
            stability = fsrs.stability_for(target, 7.0)
        cs.memory = MemoryState(stability, difficulty, obs.at_ms, obs.study_day)

    def refresh_theta(self, state: StudentState) -> None:
        """theta-hat (3.5): precision-weighted mean offset of components with 3+ attempts,
        shrunk by n / (n + 20)."""
        p = state.params
        num = den = 0.0
        n = 0
        for comp, cs in state.components.items():
            if cs.attempts < 3:
                continue
            base = p.prior_background_mean if comp in self.background else p.prior_new_mean
            w = 1.0 / cs.var
            num += w * (cs.mu - base)
            den += w
            n += 1
        state.theta_hat = (num / den) * n / (n + THETA_SHRINK) if n else 0.0


# ---------------------------------------------------------------- pace schedule (design 4.1)


def intro_dates(course: Course, settings: CourseSettings) -> dict[ComponentId, date]:
    """Section dates from cumulative section hours; a skill waits for its course
    prerequisites to be introduced. Background components never gate."""
    if settings.start is None:
        raise ValueError("the simulator needs a course start date")
    std = course.standard
    section_day: dict[str, date] = {}
    hours = 0.0
    for sec in std.sections:
        offset = hours / std.weekly_hours * 7.0 / settings.pace_factor
        section_day[sec.deck] = settings.start + timedelta(days=round(offset))
        hours += sec.hours
    course_skills = sorted((s for s in course.skills if not s.background), key=lambda s: s.order)
    intro: dict[ComponentId, date] = {}
    for s in course_skills:
        day = section_day[s.deck]
        for req in s.requires:
            if req in intro:
                day = max(day, intro[req])
        intro[s.skill_id] = day
    return intro


def milestones(skill: ComponentId, intro: date, settings: CourseSettings) -> tuple[Milestone, ...]:
    return (
        Milestone("M1", 2, intro + timedelta(days=7)),
        Milestone("M2", 3, intro + timedelta(days=21)),
        Milestone("M3", settings.target_tier, intro + timedelta(days=35)),
    )


# ---------------------------------------------------------------- certifier (design 3.7)


class StandinCertifier:
    """Beta posterior per (skill, tier) over weighted first tries (half-life 30 days), prior
    Beta(4 p, 4 (1 - p)) from the model; certified at mean >= target with n_eff >= 3 or 4,
    revoked below target - 0.10."""

    def __init__(self, target: float, kappa0: float = 4.0, half_life: float = 30.0) -> None:
        self.target = target
        self.kappa0 = kappa0
        self.half_life = half_life
        self.evidence: dict[tuple[ComponentId, int], list[tuple[int, bool]]] = {}
        self.status: dict[tuple[ComponentId, int], bool] = {}

    def add(self, skill: ComponentId, tier: int, day: date, success: bool) -> None:
        self.evidence.setdefault((skill, tier), []).append((day.toordinal(), success))

    def posterior(
        self, skill: ComponentId, tier: int, today: date, prior: float
    ) -> tuple[float, float]:
        ws = wf = 0.0
        now = today.toordinal()
        for day, ok in self.evidence.get((skill, tier), ()):
            w = 2.0 ** (-(now - day) / self.half_life)
            if ok:
                ws += w
            else:
                wf += w
        mean = (self.kappa0 * prior + ws) / (self.kappa0 + ws + wf)
        return mean, ws + wf

    def refresh(
        self, skill: ComponentId, tier: int, today: date, prior: float, needed: float
    ) -> bool:
        mean, n_eff = self.posterior(skill, tier, today, prior)
        key = (skill, tier)
        current = self.status.get(key, False)
        if not current and mean >= self.target and n_eff >= needed:
            current = True
        elif current and mean < self.target - 0.10:
            current = False
        self.status[key] = current
        return current

    def certified(self, skill: ComponentId, tier: int) -> bool:
        return self.status.get((skill, tier), False)


# ---------------------------------------------------------------- planner (design 4)


@dataclass(slots=True)
class _Slot:
    item: WorkItem
    missed: bool = False


class StandinPlanner:
    """One student's planner (stateful; the real `core.plan` is a set of pure functions)."""

    def __init__(
        self, model: StandinModel, course: Course, settings: CourseSettings, seed: int
    ) -> None:
        self.model = model
        self.settings = settings
        self.target = settings.accuracy_target
        self.skills: dict[ComponentId, SkillInfo] = {
            s.skill_id: s for s in sorted(course.skills, key=lambda s: s.order) if not s.background
        }
        self.order = tuple(self.skills)
        self.pools: dict[ComponentId, dict[int, tuple[ProblemSpec, ...]]] = {}
        for sid, info in self.skills.items():
            tiers: dict[int, list[ProblemSpec]] = {}
            for p in info.pool:
                tiers.setdefault(p.tier, []).append(p)
            self.pools[sid] = {
                t: tuple(sorted(ps, key=lambda p: p.problem_id)) for t, ps in tiers.items()
            }
        self.intro = intro_dates(course, settings)
        self.milestones = {s: milestones(s, self.intro[s], settings) for s in self.order}
        self.pace_tiers = frozenset(m.tier for s in self.order for m in self.milestones[s][1:])
        self.cert = StandinCertifier(self.target)
        self.rng = rng_for("standin-planner", seed)
        self.started: set[ComponentId] = set()
        self.last_served: dict[str, int] = {}
        self.last_practice: dict[ComponentId, int] = {}
        self.served_total = 0
        self.refit_log: list[tuple[float, int, bool]] = []  # (p_raw, tier, correct)
        self.last_refit_day: date | None = None
        self.attempts_at_refit = 0
        self.refits_adopted = 0
        # per-day state
        self.today: date | None = None
        self.slots: list[_Slot] = []
        self.checks_left = 0
        self.count_today: dict[ComponentId, int] = {}
        self.streak_today: dict[ComponentId, int] = {}
        self.new_done: set[ComponentId] = set()
        self.maintained: set[ComponentId] = set()
        self.last_skill: ComponentId | None = None

    # -- helpers

    def _reps(self, skill: ComponentId, tier: int) -> tuple[ProblemSpec, ...]:
        return self.pools[skill].get(tier, ())[:REPRESENTATIVE]

    def _readiness(
        self, state: StudentState, skill: ComponentId, tier: int, at_ms: int, pace: bool
    ) -> float:
        reps = self._reps(skill, tier)
        if not reps:
            return 0.0
        total = 0.0
        for p in reps:
            pred = self.model.predict(state, p, at_ms)
            total += pred.p * (self.model.p_fast(state, p, pred) if pace else 1.0)
        return total / len(reps)

    def _current(self, skill: ComponentId) -> Milestone | None:
        for m in self.milestones[skill]:
            if not self.cert.certified(skill, m.tier):
                return m
        return None

    def _eligible(self, pool: Sequence[ProblemSpec], today: date) -> list[ProblemSpec]:
        now = today.toordinal()
        fresh = [p for p in pool if self.last_served.get(p.problem_id, -(10**6)) < now]
        unseen90 = [p for p in fresh if now - self.last_served.get(p.problem_id, -(10**6)) > 90]
        return unseen90 or fresh

    def _item(
        self,
        state: StudentState,
        skill: ComponentId,
        role: Role,
        problem: ProblemSpec | None,
        at_ms: int,
        priority: int,
    ) -> WorkItem:
        if problem is None:
            return WorkItem(
                skill, role, None, self.skills[skill].example_card, EXAMPLE_MINUTES, priority
            )
        minutes = self.model.predict(state, problem, at_ms).median_minutes
        return WorkItem(skill, role, problem, None, minutes, priority)

    # -- planning

    def plan_day(self, state: StudentState, today: date, now_ms: int) -> DayPlan:
        self.model.refresh_theta(state)
        self.today = today
        self.count_today = {}
        self.streak_today = {}
        self.new_done = set()
        self.maintained = set()
        self.last_skill = None
        introduced = [s for s in self.order if self.intro[s] <= today]
        new_today = [s for s in introduced if s not in self.started]
        slots: list[_Slot] = []
        for s in new_today:
            slots.append(_Slot(self._item(state, s, "new", None, now_ms, 0)))
            tentative = self._reps(s, 1) or self._reps(s, 2)
            for _ in range(NEW_BLOCK):
                slots.append(_Slot(self._item(state, s, "new", tentative[0], now_ms, 0)))
        # The design leaves the order among skills open. The stand-in serves maintenance by
        # lowest forecast readiness, alternating with on-time growth by nearest deadline, and
        # rotates missed-milestone skills least recently practised first.
        maintenance: list[tuple[float, ComponentId, list[_Slot]]] = []
        growth: list[tuple[int, ComponentId, list[_Slot]]] = []
        missed: list[tuple[int, ComponentId, list[_Slot]]] = []
        tomorrow_ms = now_ms + DAY_MS
        for s in introduced:
            if s in new_today:
                continue
            current = self._current(s)
            if current is None:
                tier = self.milestones[s][-1].tier
                ready = self._readiness(state, s, tier, tomorrow_ms, pace=False)
                if ready < self.target:
                    rep = self._reps(s, tier)[0]
                    slot = _Slot(self._item(state, s, "maintenance", rep, now_ms, 1))
                    maintenance.append((ready, s, [slot]))
                continue
            rep = (self._reps(s, current.tier) or self._reps(s, current.tier - 1))[0]
            deadline = current.deadline or today
            late = deadline < today
            item = self._item(state, s, "growth", rep, now_ms, 2 if late else 1)
            group = [_Slot(item, missed=late) for _ in range(GROWTH_PER_DAY)]
            if late:
                missed.append((self.last_practice.get(s, -1), s, group))
            else:
                growth.append((deadline.toordinal(), s, group))
        maintenance.sort(key=lambda t: (t[0], t[1]))
        growth.sort(key=lambda t: (t[0], t[1]))
        missed.sort(key=lambda t: (t[0], t[1]))
        regular = _alternate([g for *_, g in maintenance], [g for *_, g in growth])
        slots.extend(self._interleave(regular, [g for *_, g in missed]))
        self.slots = slots
        n_checks = (self.served_total % CHECK_EVERY + len(slots)) // (CHECK_EVERY - 1)
        self.checks_left = n_checks
        items = [s.item for s in slots]
        check_rep = next(iter(items), None)
        for _ in range(n_checks):
            if check_rep is None:
                break
            items.append(replace(check_rep, role="check", priority=1))
        behind = tuple(
            s
            for s in introduced
            if (m := self._current(s)) is not None and m.deadline is not None and m.deadline < today
        )
        return DayPlan(
            day=today,
            items=tuple(items),
            minutes=sum(i.expected_minutes for i in items),
            hours_to_keep_pace=None,
            standard_hours=None,
            behind=behind,
            notes=("stand-in planner",),
        )

    def _interleave(self, regular: list[list[_Slot]], missed: list[list[_Slot]]) -> list[_Slot]:
        """Round-robin over skills so no skill comes twice in a row; missed-milestone items
        take at most 40% of any prefix while other items remain."""
        out: list[_Slot] = []
        reg = _round_robin(regular)
        mis = _round_robin(missed)
        i = j = 0
        while i < len(reg) or j < len(mis):
            room = (j + 1) <= MISSED_SHARE * (len(out) + 1)
            if j < len(mis) and (i >= len(reg) or room):
                out.append(mis[j])
                j += 1
            else:
                out.append(reg[i])
                i += 1
        return out

    # -- serving

    def next_item(
        self,
        state: StudentState,
        today: date,
        now_ms: int,
        served_today: Sequence[WorkItem],
    ) -> WorkItem | None:
        new_pending = any(s.item.role == "new" and self._applicable(s.item) for s in self.slots)
        if (self.served_total + 1) % CHECK_EVERY == 0 and self.checks_left > 0 and not new_pending:
            self.checks_left -= 1
            check = self._check(state, today, now_ms)
            if check is not None:
                return check
        chosen: int | None = None
        for index, slot in enumerate(self.slots):
            if not self._applicable(slot.item):
                continue
            if chosen is None:
                chosen = index
            if slot.item.role == "new" or slot.item.skill_id != self.last_skill:
                chosen = index
                break
        while chosen is not None:
            slot = self.slots.pop(chosen)
            item = slot.item
            if item.problem is None:
                return item
            problem = self._choose(state, item, today, now_ms)
            if problem is not None:
                return self._item(state, item.skill_id, item.role, problem, now_ms, item.priority)
            chosen = next((i for i, s in enumerate(self.slots) if self._applicable(s.item)), None)
        return None

    def _applicable(self, item: WorkItem) -> bool:
        s = item.skill_id
        if item.problem is None:
            return s not in self.started
        if self.count_today.get(s, 0) >= DAILY_CAP:
            return False
        if item.role == "new":
            return s not in self.new_done
        if item.role == "growth":
            return self.streak_today.get(s, 0) < 2
        if item.role == "maintenance":
            return s not in self.maintained
        return True

    def _choose(
        self, state: StudentState, item: WorkItem, today: date, now_ms: int
    ) -> ProblemSpec | None:
        s = item.skill_id
        pools = self.pools[s]
        if item.role == "new":
            cands = self._eligible((*pools.get(1, ()), *pools.get(2, ())), today)
            if not cands:
                return None
            return max(cands, key=lambda p: (self.model.predict(state, p, now_ms).p, p.problem_id))
        if item.role == "maintenance":
            tier = self.milestones[s][-1].tier
            cands = self._eligible(pools.get(tier, ()), today)
            if not cands:
                return None
            return min(
                cands,
                key=lambda p: (
                    abs(self.model.predict(state, p, now_ms).p - self.target),
                    p.problem_id,
                ),
            )
        current = self._current(s)
        tier = current.tier if current is not None else self.milestones[s][-1].tier
        # The 90-day preference applies within each tier, so a seen milestone-tier pool does
        # not push growth down to unseen rung-below problems.
        cands = [
            *self._eligible(pools.get(tier, ()), today),
            *self._eligible(pools.get(tier - 1, ()), today),
        ]
        if not cands:
            return None
        preds = {p.problem_id: self.model.predict(state, p, now_ms) for p in cands}
        bottleneck = self._bottleneck(state, s, tier, now_ms)
        lo, hi = BAND
        band = [p for p in cands if lo <= preds[p.problem_id].p <= hi]
        with_bn = [p for p in band if bottleneck in p.components]
        pick_from = with_bn or band
        if not pick_from:
            # Empty band. Read literally, 4.4 takes the problem closest to 0.80 from both
            # tiers, which for a strong student can be a rung-below problem that never counts
            # toward the milestone. The stand-in keeps to the milestone tier unless every
            # problem there is below the band.
            top = [p for p in cands if p.tier == tier]
            too_hard = all(preds[p.problem_id].p < lo for p in top)
            pick_from = top if top and not too_hard else cands
        return min(pick_from, key=lambda p: (abs(preds[p.problem_id].p - 0.80), p.problem_id))

    def _bottleneck(
        self, state: StudentState, skill: ComponentId, tier: int, now_ms: int
    ) -> ComponentId | None:
        worst: tuple[float, ComponentId] | None = None
        for p in self.pools[skill].get(tier, ()):
            for comp, q in self.model.predict(state, p, now_ms).q:
                if comp in self.model.background:
                    continue
                if worst is None or q < worst[0]:
                    worst = (q, comp)
        return worst[1] if worst else None

    def _check(self, state: StudentState, today: date, now_ms: int) -> WorkItem | None:
        introduced = [s for s in self.order if self.intro[s] <= today and s in self.started]
        if not introduced:
            return None
        skill = self.rng.choice(introduced)
        current = self._current(skill)
        tier = current.tier if current is not None else self.milestones[skill][-1].tier
        pool = self.pools[skill].get(tier, ())
        unseen = [p for p in pool if p.problem_id not in self.last_served]
        cands = unseen or self._eligible(pool, today)
        if not cands:
            return None
        return self._item(state, skill, "check", self.rng.choice(cands), now_ms, 1)

    # -- observing

    def observe(
        self,
        state: StudentState,
        item: WorkItem,
        obs: Observation | None,
        record: UpdateRecord | None,
        minutes: float,
    ) -> None:
        self.served_total += 1
        s = item.skill_id
        self.last_skill = s
        if obs is None:
            self.started.add(s)
            return
        self.started.add(s)
        problem = obs.problem
        self.last_served[problem.problem_id] = obs.study_day.toordinal()
        self.last_practice[s] = obs.study_day.toordinal()
        self.count_today[s] = self.count_today.get(s, 0) + 1
        success = obs.correct and not obs.aided
        self.streak_today[s] = self.streak_today.get(s, 0) + 1 if success else 0
        if item.role == "new" and success:
            self.new_done.add(s)
        if item.role == "maintenance":
            self.maintained.add(s)
        if record is not None:
            self.refit_log.append((record.prediction.p_raw, problem.tier, success))
        main = problem.main_skill
        if main in self.skills and any(m.tier == problem.tier for m in self.milestones[main]):
            fast = obs.minutes is not None and obs.minutes <= problem.standard_minutes
            ok = success and (problem.tier not in self.pace_tiers or fast)
            self.cert.add(main, problem.tier, obs.study_day, ok)
            self._refresh(state, main, problem.tier, obs.study_day, obs.at_ms)

    def _refresh(
        self, state: StudentState, skill: ComponentId, tier: int, today: date, at_ms: int
    ) -> None:
        pace = tier in self.pace_tiers
        prior = self._readiness(state, skill, tier, at_ms, pace)
        needed = 3.0 if tier == self.milestones[skill][0].tier else 4.0
        self.cert.refresh(skill, tier, today, prior, needed)

    def end_day(self, state: StudentState, today: date, now_ms: int) -> None:
        for skill, tier in [k for k, v in self.cert.status.items() if v]:
            self._refresh(state, skill, tier, today, now_ms)
        due = self.last_refit_day is None or (today - self.last_refit_day).days >= 14
        if (due or len(self.refit_log) - self.attempts_at_refit >= 300) and len(
            self.refit_log
        ) >= 50:
            self.last_refit_day = today
            self.attempts_at_refit = len(self.refit_log)
            if _refit_calibration(state, self.refit_log, self.rng.random):
                self.refits_adopted += 1

    def certified(self, state: StudentState, skill: ComponentId, tier: int, today: date) -> bool:
        return self.cert.certified(skill, tier)


def _alternate(a: list[list[_Slot]], b: list[list[_Slot]]) -> list[list[_Slot]]:
    out: list[list[_Slot]] = []
    for i in range(max(len(a), len(b))):
        out.extend(g[i] for g in (a, b) if i < len(g))
    return out


def _round_robin(groups: list[list[_Slot]]) -> list[_Slot]:
    out: list[_Slot] = []
    queues = [list(g) for g in groups if g]
    while queues:
        for q in queues:
            out.append(q.pop(0))
        queues = [q for q in queues if q]
    return out


# ---------------------------------------------------------------- refit (design 3.6, partial)


def _platt(
    log: Sequence[tuple[float, int, bool]], a0: Sequence[float], b0: float
) -> tuple[list[float], float]:
    """MAP per-tier intercepts a_1..a_5 and a shared slope b on logit(p_raw), priors
    N(0, 0.5^2) and N(1, 0.2^2), by Newton steps."""
    a = list(a0)
    b = b0
    for _ in range(12):
        grad = [0.0] * 6
        hess = [[0.0] * 6 for _ in range(6)]
        for p_raw, tier, y in log:
            z = logit(p_raw)
            i = min(max(tier, 1), 5) - 1
            p = sigmoid(a[i] + b * z)
            resid = (1.0 if y else 0.0) - p
            w = p * (1.0 - p)
            grad[i] += resid
            grad[5] += resid * z
            hess[i][i] += w
            hess[i][5] += w * z
            hess[5][i] += w * z
            hess[5][5] += w * z * z
        for i in range(5):
            grad[i] -= a[i] / 0.25
            hess[i][i] += 1.0 / 0.25
        grad[5] -= (b - 1.0) / 0.04
        hess[5][5] += 1.0 / 0.04
        step = _solve(hess, grad)
        a = [a[i] + step[i] for i in range(5)]
        b += step[5]
        if max(abs(x) for x in step) < 1e-6:
            break
    return a, b


def _solve(m: list[list[float]], v: list[float]) -> list[float]:
    n = len(v)
    aug = [[*row, v[i]] for i, row in enumerate(m)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        if abs(aug[col][col]) < 1e-12:
            continue
        for r in range(n):
            if r != col:
                f = aug[r][col] / aug[col][col]
                for c in range(col, n + 1):
                    aug[r][c] -= f * aug[col][c]
    return [aug[i][n] / aug[i][i] if abs(aug[i][i]) > 1e-12 else 0.0 for i in range(n)]


def _losses(log: Sequence[tuple[float, int, bool]], a: Sequence[float], b: float) -> list[float]:
    out = []
    for p_raw, tier, y in log:
        p = sigmoid(a[min(max(tier, 1), 5) - 1] + b * logit(p_raw))
        p = min(max(p, 1e-9), 1.0 - 1e-9)
        out.append(-math.log(p if y else 1.0 - p))
    return out


def _refit_calibration(
    state: StudentState,
    log: Sequence[tuple[float, int, bool]],
    uniform: Callable[[], float],
) -> bool:
    """Fit (a, b) on the first 80%, score on the last 20%; adopt when the held-out log loss
    improves by >= 0.003 nats per attempt with a one-sided bootstrap p < 0.1."""
    params = state.params
    split = int(len(log) * 0.8)
    train, test = log[:split], log[split:]
    if not test:
        return False
    a, b = _platt(train, params.calib_a, params.calib_b)
    current = _losses(test, params.calib_a, params.calib_b)
    candidate = _losses(test, a, b)
    diffs = [c - d for c, d in zip(current, candidate, strict=True)]
    gain = sum(diffs) / len(diffs)
    if gain < 0.003:
        return False
    worse = 0
    n = len(diffs)
    for _ in range(200):
        total = 0.0
        for _ in range(n):
            total += diffs[int(uniform() * n)]
        if total <= 0.0:
            worse += 1
    if worse / 200 >= 0.1:
        return False
    version = f"standin-refit-{len(log)}"
    state.params = replace(
        params,
        version=version,
        calib_a=(a[0], a[1], a[2], a[3], a[4]),
        calib_b=b,
    )
    return True


DEFAULT_PARAMS: Final = SharedParams()
