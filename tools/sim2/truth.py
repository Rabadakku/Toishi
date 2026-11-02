"""Truth models: simulated students whose answers the policies never see inside (design 6.2).

A truth student gets a problem (with its real tags), the time and its own hidden practice
history, and returns a first try: correct or not (never aided), the index of the matched
`wrong:` line when a failed component has one on the problem, and the minutes spent.

| Name | Model |
|---|---|
| a-model | the design's own model (3.2): conjunctive, execution x FSRS-6 memory (phi ~0.05) |
| b-additive | Best-LR / DAS3H: ability - difficulty + window terms of each component |
| c-ppe | conjunctive; each component has PPE strength N^c * T^-(b + m * space) |
| d-rohrer-taylor | (a) with memory tuned to Rohrer & Taylor 2006 (massed 4w/1w 0.43, ratio 2) |
| e-slow | (a) learning at half rate (gamma and the speed-up halved) |
| e-careless | (a) with slip 0.12 |
| f-tags | (a); the planner sees 10% of non-main tags dropped, 10% swapped |

Each model has three profiles: `typical` (drawn per seed), `strong` (above the targets from
the start: tier-4 first tries around 0.94 and a median time near half the standard time) and
`weak` (low ability; cannot reach the targets in a semester).

Solve times are shared by all models: ln T = ln T* + tau + tau_s - alpha ln(1 + n) + e,
e ~ N(0, sigma^2), with n the mean practice count over the problem's course components
(the design's 3.3 form with hidden values). A miss also costs a minute to read the solution.
"""

import bisect
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from random import Random
from typing import Final, Protocol

from core.learner.types import ComponentId, ProblemSpec
from tools.sim2.common import DAY_MS, normal_cdf, rng_for, session_ms, sigmoid
from tools.sim2.course import SimCourse
from tools.sim2.fsrs6 import AGAIN, DEFAULT, GOOD, Fsrs6

TRUTH_MODELS: Final = (
    "a-model",
    "b-additive",
    "c-ppe",
    "d-rohrer-taylor",
    "e-slow",
    "e-careless",
    "f-tags",
)
# The default matrix: (c) PPE is implemented but left out for now (coordinator, 2026-11-02).
DEFAULT_TRUTHS: Final = tuple(m for m in TRUTH_MODELS if m != "c-ppe")
PROFILES: Final = ("typical", "strong", "weak")
SOLUTION_MINUTES: Final = 1.0  # reading the worked solution after a miss
LOGIT_065: Final = 0.6190392084062235
LOGIT_097: Final = 3.4760986898352733
STRONG_LOGIT: Final = 6.0  # e = 0.9975 at tiers 1-3, 0.997 at tier 4 (delta4 0.3)
STRONG_FSRS_STABILITY: Final = 1000.0  # days; memory from before the course (R(50 d) = 0.993)
STRONG_RT06_STABILITY: Final = 5000.0  # days; the same R(50 d) on truth (d)'s curve

# Rohrer & Taylor 2006 memory (truth d): R = exp(-t / S), t in days. Fitted so that, for a
# median student on one-component problems, the Exp 1 protocol gives a massed 4-week/1-week
# ratio of 0.43 and spaced/massed at 4 weeks of 2.0 (tests/sim2/test_truth.py checks).
RT06_S0: Final = 24.9  # days, stability after the first session (no same-day gain: Exp 2)
RT06_GAIN: Final = 11.0  # S *= 1 + gain * (1 - R) on a recalled review on a later day

# PPE (truth c), values from student_models.md section 5 (LKT vignette fit): c, b, m, x.
PPE_C: Final = 0.3491901
PPE_B: Final = 0.2045801
PPE_M: Final = 1e-05  # at its lower bound in that fit: decay barely depends on spacing
PPE_X: Final = 0.9734477
PPE_GAIN: Final = 1.0  # logistic coefficient on the PPE strength (this simulator's choice)
PPE_FLOOR_DAYS: Final = 1.0 / 24.0

# Best-LR / DAS3H windows (truth b): (window in days, success weight, attempt weight). A
# median one-component learner goes from 0.58 to about 0.75 in 7 opportunities at 70%
# success and to about 0.81 after 20 spread over a month (Koedinger 2023's median: 0.65 to
# 0.80 in 7); a month without practice takes back the 7- and 30-day terms.
ADDITIVE_WINDOWS: Final = (
    (1.0 / 24.0, 0.05, 0.05),
    (1.0, 0.10, 0.05),
    (7.0, 0.15, 0.05),
    (30.0, 0.15, 0.05),
    (math.inf, 0.40, 0.10),
)
ADDITIVE_TIER: Final = {1: 0.0, 2: 0.4, 3: 0.9, 4: 1.5, 5: 2.1}


@dataclass(frozen=True, slots=True)
class Answer:
    correct: bool
    matched_wrong: int | None
    minutes: float  # active minutes spent, including reading the solution after a miss


class Truth(Protocol):
    name: str
    profile: str

    def answer(self, spec: ProblemSpec, at_ms: int, day: date) -> Answer:
        """Sample a first try and add it to the hidden history."""
        ...

    def p_correct(self, spec: ProblemSpec, at_ms: int) -> float:
        """The true chance of a correct first try at `at_ms`. Changes nothing."""
        ...

    def p_fast(self, spec: ProblemSpec) -> float:
        """The true chance that a solve takes at most the standard time. Changes nothing."""
        ...


# ---------------------------------------------------------------- solve times


class TimeTruth:
    def __init__(
        self,
        tau: float,
        sigma: float,
        alpha: float,
        offsets: Mapping[ComponentId, float],
        background: frozenset[ComponentId],
    ) -> None:
        self.tau = tau
        self.sigma = sigma
        self.alpha = alpha
        self.offsets = offsets
        self.background = background
        self.n: dict[ComponentId, int] = {}

    def log_median(self, spec: ProblemSpec) -> float:
        course = [c for c in spec.components if c not in self.background]
        n_bar = sum(self.n.get(c, 0) for c in course) / len(course) if course else 0.0
        return (
            math.log(spec.standard_minutes)
            + self.tau
            + self.offsets.get(spec.main_skill, 0.0)
            - self.alpha * math.log1p(n_bar)
        )

    def p_fast(self, spec: ProblemSpec) -> float:
        z = (math.log(spec.standard_minutes) - self.log_median(spec)) / self.sigma
        return normal_cdf(z)

    def sample(self, spec: ProblemSpec, rng: Random) -> float:
        return math.exp(self.log_median(spec) + rng.gauss(0.0, self.sigma))

    def practiced(self, spec: ProblemSpec) -> None:
        for c in spec.components:
            if c not in self.background:
                self.n[c] = self.n.get(c, 0) + 1


def _matched(spec: ProblemSpec, failed: Sequence[ComponentId]) -> int | None:
    """The first `wrong:` line of the first failed component that has one."""
    for comp in failed:
        for index, listed in spec.wrong_components:
            if listed == comp:
                return index
    return None


# ---------------------------------------------------------------- memory terms


class Memory(Protocol):
    def recall(self, comp: ComponentId, at_ms: int) -> float: ...

    def event(self, comp: ComponentId, at_ms: int, day: date, recalled: bool) -> None: ...


@dataclass(slots=True)
class _FsrsCard:
    stability: float
    difficulty: float
    last_ms: int
    last_day: date


class FsrsMemory:
    """FSRS-6 with elapsed time scaled by phi; R = 1 before a component's first event (3.2)."""

    def __init__(self, phi: float, fsrs: Fsrs6 = DEFAULT) -> None:
        self.phi = phi
        self.fsrs = fsrs
        self.cards: dict[ComponentId, _FsrsCard] = {}

    def preload(self, comp: ComponentId, stability: float, difficulty: float, day: date) -> None:
        self.cards[comp] = _FsrsCard(stability, difficulty, session_ms(day), day)

    def recall(self, comp: ComponentId, at_ms: int) -> float:
        card = self.cards.get(comp)
        if card is None:
            return 1.0
        return self.fsrs.retrievability(self.phi * (at_ms - card.last_ms) / DAY_MS, card.stability)

    def event(self, comp: ComponentId, at_ms: int, day: date, recalled: bool) -> None:
        rating = GOOD if recalled else AGAIN
        card = self.cards.get(comp)
        if card is None:
            s, d = self.fsrs.initial(rating)
            self.cards[comp] = _FsrsCard(s, d, at_ms, day)
            return
        elapsed = max(0, (day - card.last_day).days)
        # The update reads R on the truth's clock (elapsed whole days scaled by phi).
        r = self.fsrs.retrievability(self.phi * elapsed, card.stability)
        s, d = self.fsrs.review(card.stability, card.difficulty, rating, elapsed, r)
        card.stability, card.difficulty, card.last_ms, card.last_day = s, d, at_ms, day


@dataclass(slots=True)
class _RtCard:
    stability: float
    last_ms: int
    last_day: date


class RohrerTaylorMemory:
    """Exponential forgetting, R = exp(-t / S), with gains only from spaced reviews.

    The first event sets S = s0. A same-day event changes nothing (Rohrer & Taylor 2006
    Exp 2: 9 against 3 problems in one session made no difference). A recalled event on a
    later day multiplies S by 1 + gain * (1 - R), so reviews at lower recall gain more; a
    failed recall re-encodes at s0.
    """

    def __init__(self, s0: float = RT06_S0, gain: float = RT06_GAIN) -> None:
        self.s0 = s0
        self.gain = gain
        self.cards: dict[ComponentId, _RtCard] = {}

    def preload(self, comp: ComponentId, stability: float, day: date) -> None:
        self.cards[comp] = _RtCard(stability, session_ms(day), day)

    def recall(self, comp: ComponentId, at_ms: int) -> float:
        card = self.cards.get(comp)
        if card is None:
            return 1.0
        return math.exp(-max(0, at_ms - card.last_ms) / DAY_MS / card.stability)

    def event(self, comp: ComponentId, at_ms: int, day: date, recalled: bool) -> None:
        card = self.cards.get(comp)
        if card is None:
            self.cards[comp] = _RtCard(self.s0, at_ms, day)
            return
        if day != card.last_day:
            if recalled:
                r = self.recall(comp, at_ms)
                card.stability *= 1.0 + self.gain * (1.0 - r)
            else:
                card.stability = self.s0
        card.last_ms, card.last_day = at_ms, day


# ---------------------------------------------------------------- (a), (d), (e), (f)


class ConjunctiveTruth:
    """P = (1 - s) * prod_k e_k * R_k (design 3.2 without recalibration), sampled per component.

    Each course component is recalled with probability R_k and executed with probability
    e_k = sigmoid(beta_k + gamma ln(1 + C_k) + rho ln(1 + F_k) - delta_tier). A recalled
    component counts a success (weight 1 for its first of the day, then `same_day_weight`)
    or a failure; the memory sees Good or Again. Background components: e_k = sigmoid(beta_k),
    R = 1, no learning.
    """

    def __init__(
        self,
        name: str,
        profile: str,
        *,
        beta: Mapping[ComponentId, float],
        background: frozenset[ComponentId],
        slip: float,
        delta4: float,
        memory: Memory,
        time: TimeTruth,
        rng: Random,
        gamma: float = 0.37,
        rho: float = 0.0,
        delta5: float = 0.7,
        same_day_weight: float = 0.25,
    ) -> None:
        self.name = name
        self.profile = profile
        self.beta = beta
        self.background = background
        self.slip = slip
        self.delta = {1: 0.0, 2: 0.0, 3: 0.0, 4: delta4, 5: delta5}
        self.memory = memory
        self.time = time
        self.rng = rng
        self.gamma = gamma
        self.rho = rho
        self.same_day_weight = same_day_weight
        self.c: dict[ComponentId, float] = {}
        self.f: dict[ComponentId, float] = {}
        self.today: dict[ComponentId, tuple[date, int]] = {}

    def execution(self, comp: ComponentId, tier: int) -> float:
        eta = self.beta.get(comp, LOGIT_065)
        if comp not in self.background:
            eta += self.gamma * math.log1p(self.c.get(comp, 0.0))
            eta += self.rho * math.log1p(self.f.get(comp, 0.0))
        return sigmoid(eta - self.delta[tier])

    def recall(self, comp: ComponentId, at_ms: int) -> float:
        return 1.0 if comp in self.background else self.memory.recall(comp, at_ms)

    def p_correct(self, spec: ProblemSpec, at_ms: int) -> float:
        p = 1.0 - self.slip
        for comp in spec.components:
            p *= self.execution(comp, spec.tier) * self.recall(comp, at_ms)
        return p

    def p_fast(self, spec: ProblemSpec) -> float:
        return self.time.p_fast(spec)

    def answer(self, spec: ProblemSpec, at_ms: int, day: date) -> Answer:
        rng = self.rng
        failed: list[ComponentId] = []
        events: list[tuple[ComponentId, bool, bool]] = []
        for comp in spec.components:
            recalled = rng.random() < self.recall(comp, at_ms)
            executed = rng.random() < self.execution(comp, spec.tier)
            events.append((comp, recalled, executed))
            if not (recalled and executed):
                failed.append(comp)
        slipped = rng.random() < self.slip
        correct = not failed and not slipped
        for comp, recalled, executed in events:
            if comp in self.background:
                continue
            self.memory.event(comp, at_ms, day, recalled)
            if not recalled:
                continue
            if executed:
                seen_day, count = self.today.get(comp, (day, 0))
                count = count if seen_day == day else 0
                weight = 1.0 if count == 0 else self.same_day_weight
                self.c[comp] = self.c.get(comp, 0.0) + weight
                self.today[comp] = (day, count + 1)
            else:
                self.f[comp] = self.f.get(comp, 0.0) + 1.0
        minutes = self.time.sample(spec, rng)
        self.time.practiced(spec)
        if not correct:
            minutes += SOLUTION_MINUTES
        return Answer(correct, None if correct else _matched(spec, failed), minutes)


# ---------------------------------------------------------------- (b) additive


class AdditiveTruth:
    """Best-LR / DAS3H: logit P = ability - difficulty_j + sum_k [beta_k + sum_w (g_w ln(1 +
    successes_kw) - t_w ln(1 + attempts_kw))], over the windows in ADDITIVE_WINDOWS.

    Counts are per component over first tries of problems that contain it (as in DAS3H). On a
    miss, the blamed step is drawn with probability proportional to exp(-term_k), so weaker
    components produce the matched wrong answers more often.
    """

    def __init__(
        self,
        name: str,
        profile: str,
        *,
        ability: float,
        beta: Mapping[ComponentId, float],
        difficulty: Mapping[str, float],
        time: TimeTruth,
        rng: Random,
        windows: Sequence[tuple[float, float, float]] = ADDITIVE_WINDOWS,
    ) -> None:
        self.name = name
        self.profile = profile
        self.ability = ability
        self.beta = beta
        self.difficulty = difficulty
        self.time = time
        self.rng = rng
        self.windows = tuple(windows)
        self.attempts: dict[ComponentId, list[int]] = {}
        self.successes: dict[ComponentId, list[int]] = {}

    def term(self, comp: ComponentId, at_ms: int) -> float:
        value = self.beta.get(comp, 0.0)
        tried = self.attempts.get(comp)
        if not tried:
            return value
        won = self.successes.get(comp, [])
        for days, g, t in self.windows:
            if math.isinf(days):
                a, c = len(tried), len(won)
            else:
                start = at_ms - int(days * DAY_MS)
                a = len(tried) - bisect.bisect_left(tried, start)
                c = len(won) - bisect.bisect_left(won, start)
            value += g * math.log1p(c) - t * math.log1p(a)
        return value

    def _logit(self, spec: ProblemSpec, at_ms: int) -> tuple[float, list[float]]:
        terms = [self.term(c, at_ms) for c in spec.components]
        return self.ability - self.difficulty[spec.problem_id] + sum(terms), terms

    def p_correct(self, spec: ProblemSpec, at_ms: int) -> float:
        return sigmoid(self._logit(spec, at_ms)[0])

    def p_fast(self, spec: ProblemSpec) -> float:
        return self.time.p_fast(spec)

    def answer(self, spec: ProblemSpec, at_ms: int, day: date) -> Answer:
        rng = self.rng
        x, terms = self._logit(spec, at_ms)
        correct = rng.random() < sigmoid(x)
        matched: int | None = None
        if not correct:
            weights = [math.exp(-min(t, 30.0)) for t in terms]
            pick = rng.random() * sum(weights)
            blamed = spec.components[-1]
            for comp, w in zip(spec.components, weights, strict=True):
                pick -= w
                if pick < 0.0:
                    blamed = comp
                    break
            matched = _matched(spec, [blamed])
        for comp in spec.components:
            self.attempts.setdefault(comp, []).append(at_ms)
            if correct:
                self.successes.setdefault(comp, []).append(at_ms)
        minutes = self.time.sample(spec, rng)
        self.time.practiced(spec)
        if not correct:
            minutes += SOLUTION_MINUTES
        return Answer(correct, matched, minutes)


# ---------------------------------------------------------------- (c) PPE


class PpeTruth:
    """Conjunctive over components, each with q_k = sigmoid(beta_k - delta_tier + g * M_k).

    M_k = N^c * Tw^-(b + m * space) (the LKT `ppe` feature): N practices of k, Tw their
    age weighted by age^-x (days, floored at an hour) and `space` the mean over successive
    gaps of 1 / ln(gap + e). Background components have no PPE term.
    """

    def __init__(
        self,
        name: str,
        profile: str,
        *,
        beta: Mapping[ComponentId, float],
        background: frozenset[ComponentId],
        slip: float,
        delta4: float,
        time: TimeTruth,
        rng: Random,
        gain: float = PPE_GAIN,
        c: float = PPE_C,
        b: float = PPE_B,
        m: float = PPE_M,
        x: float = PPE_X,
    ) -> None:
        self.name = name
        self.profile = profile
        self.beta = beta
        self.background = background
        self.slip = slip
        self.delta = {1: 0.0, 2: 0.0, 3: 0.0, 4: delta4, 5: 0.7}
        self.time = time
        self.rng = rng
        self.gain, self.c, self.b, self.m, self.x = gain, c, b, m, x
        self.practice: dict[ComponentId, list[float]] = {}  # practice times in days
        self.gaps: dict[ComponentId, float] = {}  # running sum of 1 / ln(gap + e)
        self.cache: dict[ComponentId, tuple[int, float]] = {}

    def strength(self, comp: ComponentId, at_ms: int) -> float:
        cached = self.cache.get(comp)
        if cached is not None and cached[0] == at_ms:
            return cached[1]
        times = self.practice.get(comp)
        if not times:
            return 0.0
        now = at_ms / DAY_MS
        num = den = 0.0
        x = self.x
        for t in times:
            age = now - t
            if age < PPE_FLOOR_DAYS:
                age = PPE_FLOOR_DAYS
            w = age**-x
            num += w * age
            den += w
        space = self.gaps.get(comp, 0.0) / (len(times) - 1) if len(times) > 1 else 0.0
        decay = self.b + self.m * space
        value = float(len(times) ** self.c * (num / den) ** (-decay))
        self.cache[comp] = (at_ms, value)
        return value

    def _practise(self, comp: ComponentId, at_ms: int) -> None:
        times = self.practice.setdefault(comp, [])
        t = at_ms / DAY_MS
        if times:
            self.gaps[comp] = self.gaps.get(comp, 0.0) + 1.0 / math.log(
                max(t - times[-1], 0.0) + math.e
            )
        times.append(t)
        self.cache.pop(comp, None)

    def component(self, comp: ComponentId, tier: int, at_ms: int) -> float:
        eta = self.beta.get(comp, LOGIT_065) - self.delta[tier]
        if comp not in self.background:
            eta += self.gain * self.strength(comp, at_ms)
        return sigmoid(eta)

    def p_correct(self, spec: ProblemSpec, at_ms: int) -> float:
        p = 1.0 - self.slip
        for comp in spec.components:
            p *= self.component(comp, spec.tier, at_ms)
        return p

    def p_fast(self, spec: ProblemSpec) -> float:
        return self.time.p_fast(spec)

    def answer(self, spec: ProblemSpec, at_ms: int, day: date) -> Answer:
        rng = self.rng
        failed = [c for c in spec.components if rng.random() >= self.component(c, spec.tier, at_ms)]
        correct = not failed and rng.random() >= self.slip
        for comp in spec.components:
            if comp not in self.background:
                self._practise(comp, at_ms)
        minutes = self.time.sample(spec, rng)
        self.time.practiced(spec)
        if not correct:
            minutes += SOLUTION_MINUTES
        return Answer(correct, None if correct else _matched(spec, failed), minutes)


# ---------------------------------------------------------------- Rohrer & Taylor 2006


@dataclass(frozen=True, slots=True)
class Exp1Result:
    """Mean predicted test scores in Rohrer & Taylor 2006 Exp 1, and the ratios they report."""

    massed_1w: float
    massed_4w: float
    spaced_1w: float
    spaced_4w: float

    @property
    def massed_ratio(self) -> float:  # observed 0.43 (32% / 75%)
        return self.massed_4w / self.massed_1w

    @property
    def spaced_over_massed_4w(self) -> float:  # observed 2.0 (64% / 32%)
        return self.spaced_4w / self.massed_4w

    @property
    def spaced_over_massed_1w(self) -> float:  # observed 0.93 (70% / 75%)
        return self.spaced_1w / self.massed_1w


def rohrer_taylor_exp1(
    memory: Callable[[], Memory] = RohrerTaylorMemory, students: int = 2000, seed: int = 0
) -> Exp1Result:
    """Exp 1 on a median student (one-component problems): Massers do 10 problems in one
    session, Spacers 5 and 5 a week apart; the test is 1 or 4 weeks after the last session.
    Scores are the model's expected first-try chance on a fresh problem, averaged over
    `students` simulated practice histories."""
    comp = "rt.procedure"
    spec = ProblemSpec(comp + ".t1", comp + ".t1", None, comp, (comp,), 1, 1, 2.0)
    totals = {"massed_1w": 0.0, "massed_4w": 0.0, "spaced_1w": 0.0, "spaced_4w": 0.0}
    day0 = date(2027, 1, 4)
    for group, sessions in (("massed", ((0, 10),)), ("spaced", ((0, 5), (7, 5)))):
        for i in range(students):
            mem = memory()
            time = TimeTruth(0.0, 0.3, 0.3, {}, frozenset())
            truth = ConjunctiveTruth(
                "rt06",
                "median",
                beta={comp: LOGIT_065},
                background=frozenset(),
                slip=0.03,
                delta4=0.3,
                memory=mem,
                time=time,
                rng=rng_for("rt06", group, seed, i),
            )
            for offset, count in sessions:
                day = day0 + timedelta(days=offset)
                for j in range(count):
                    truth.answer(spec, session_ms(day) + 2 * j * 60_000, day)
            last = day0 + timedelta(days=sessions[-1][0])
            for weeks in (1, 4):
                at = session_ms(last + timedelta(days=7 * weeks))
                totals[f"{group}_{weeks}w"] += truth.p_correct(spec, at) / students
    return Exp1Result(**totals)


# ---------------------------------------------------------------- profiles


@dataclass(frozen=True, slots=True)
class _Draw:
    """A student's hidden values shared by the conjunctive models."""

    beta: dict[ComponentId, float]
    slip: float
    delta4: float
    phi: float
    tau: float
    sigma: float
    offsets: dict[ComponentId, float]
    theta: float
    strong: bool = False


def _draw(profile: str, rng: Random, sim: SimCourse) -> _Draw:
    course = [c for c, info in sim.catalog.items() if not info.background]
    background = [c for c, info in sim.catalog.items() if info.background]
    if profile == "strong":
        beta = {c: STRONG_LOGIT + rng.gauss(0.0, 0.3) for c in (*course, *background)}
        offsets = {c: rng.gauss(0.0, 0.1) for c in course}
        return _Draw(beta, 0.01, 0.3, 0.03, math.log(0.5), 0.35, offsets, 4.9, strong=True)
    theta = -1.3 if profile == "weak" else rng.gauss(0.0, 0.65)
    beta = {c: LOGIT_065 + theta + rng.gauss(0.0, 0.7) for c in course}
    beta |= {c: LOGIT_097 + 0.5 * theta + rng.gauss(0.0, 0.5) for c in background}
    offsets = {c: rng.gauss(0.0, 0.2) for c in course}
    if profile == "weak":
        return _Draw(beta, 0.06, 0.4, 0.08, math.log(2.8), 0.5, offsets, theta)
    if profile != "typical":
        raise ValueError(f"unknown profile {profile!r}")
    return _Draw(
        beta,
        rng.uniform(0.02, 0.05),
        0.3 + rng.gauss(0.0, 0.15),
        0.05 * math.exp(rng.gauss(0.0, 0.5)),  # audit 2026-11-02: procedures forget ~20x slower
        math.log(2.0) + rng.gauss(0.0, 0.2),
        0.45,
        offsets,
        theta,
    )


def make_truth(model: str, profile: str, seed: int, sim: SimCourse, start: date) -> Truth:
    """The truth student `seed` of `profile` under `model`. The same arguments always give
    the same hidden values, so every policy meets the same student; the hidden values depend
    only on (profile, seed), so the variants (d) to (f) change one mechanism of (a) each."""
    if model not in TRUTH_MODELS:
        raise ValueError(f"unknown truth model {model!r}")
    params = rng_for("truth", profile, seed)
    answers = rng_for("answers", model, profile, seed)
    draw = _draw(profile, params, sim)
    background = frozenset(c for c, info in sim.catalog.items() if info.background)
    course = [c for c in sim.catalog if c not in background]
    alpha = 0.025 if model == "e-slow" else 0.05  # audit 2026-11-02: measured 0.03-0.04
    time = TimeTruth(draw.tau, draw.sigma, alpha, draw.offsets, background)
    if model == "b-additive":
        return _additive(profile, draw, sim, time, answers)
    if model == "c-ppe":
        return PpeTruth(
            model,
            profile,
            beta=draw.beta,
            background=background,
            slip=draw.slip,
            delta4=draw.delta4,
            time=time,
            rng=answers,
        )
    memory: FsrsMemory | RohrerTaylorMemory
    before = start - timedelta(days=10)
    if model == "d-rohrer-taylor":
        memory = RohrerTaylorMemory()
        if draw.strong:
            for c in course:
                memory.preload(c, STRONG_RT06_STABILITY, before)
    else:
        memory = FsrsMemory(draw.phi)
        if draw.strong:
            for c in course:
                memory.preload(c, STRONG_FSRS_STABILITY, 3.0, before)
    slow = model == "e-slow"
    return ConjunctiveTruth(
        model,
        profile,
        beta=draw.beta,
        background=background,
        slip=0.12 if model == "e-careless" else draw.slip,
        delta4=draw.delta4,
        memory=memory,
        time=time,
        rng=answers,
        gamma=0.185 if slow else 0.37,
        rho=0.0,  # audit 2026-11-02: failures did not raise later success
    )


def _additive(
    profile: str, draw: _Draw, sim: SimCourse, time: TimeTruth, answers: Random
) -> AdditiveTruth:
    # Component easiness and item difficulty belong to the course, not the student.
    comps = rng_for("additive-components", sim.name)
    beta = {
        c: comps.gauss(0.35, 0.3) if info.background else comps.gauss(-0.35, 0.4)
        for c, info in sorted(sim.catalog.items())
    }
    items = rng_for("additive-items", sim.name)
    difficulty = {
        pid: ADDITIVE_TIER[spec.tier] + items.gauss(0.0, 0.25)
        for pid, spec in sorted(sim.true_specs.items())
    }
    if profile == "strong":
        ability = STRONG_LOGIT
    elif profile == "weak":
        ability = LOGIT_065 - 1.3
    else:
        ability = LOGIT_065 + draw.theta
    return AdditiveTruth(
        "b-additive",
        profile,
        ability=ability,
        beta=beta,
        difficulty=difficulty,
        time=time,
        rng=answers,
    )
