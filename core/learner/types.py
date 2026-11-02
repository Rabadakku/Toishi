"""Data contract of the student model (docs/design/student-model.md v1.1, section 8).

Implementations may add fields but must not rename or remove these. Times are UTC epoch
milliseconds; study days are the app's study days (rollover at 4 AM local).
"""

from dataclasses import dataclass, field
from datetime import date

type ComponentId = str

ROLES = ("new", "growth", "maintenance", "check", "practice-test", "focused", "placement")


@dataclass(frozen=True, slots=True)
class ComponentInfo:
    """A component (a skill ID in the skills file).

    A background component comes from an earlier course (alg./trig./pre. prefix, or outside
    the course's own sections): no memory term, a strong prior (design 3.1).
    """

    component_id: ComponentId
    background: bool
    course_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    """One gradable problem (a card, or one part of a multi-part card)."""

    problem_id: str  # card id, or "card_id#part"
    card_id: str
    part: str | None
    main_skill: ComponentId
    components: tuple[ComponentId, ...]  # K_j: main skill first, unique
    tier: int  # 1..5
    steps: int
    standard_minutes: float  # T*_j
    wrong_components: tuple[tuple[int, ComponentId], ...] = ()  # (wrong-line index, component)
    family: str = ""  # template id or card id: variety and family residual checks


@dataclass(frozen=True, slots=True)
class Observation:
    """A first try at a problem (design 3.4). Later tries are not observations."""

    attempt_id: int  # order key together with at_ms
    at_ms: int
    study_day: date
    problem: ProblemSpec
    correct: bool  # first try, unaided
    aided: bool = False  # a hint, the solution or a give-up before the first answer
    matched_wrong: int | None = None  # index of the matched `wrong:` line
    minutes: float | None = None  # valid active time of a correct first try, else None
    role: str = "growth"  # one of ROLES


@dataclass(slots=True)
class MemoryState:
    """FSRS-6 memory of a course component's method."""

    stability: float
    difficulty: float
    last_ms: int
    last_day: date


@dataclass(slots=True)
class ComponentState:
    mu: float  # posterior mean of the execution easiness beta_k
    var: float  # posterior variance
    c: float = 0.0  # soft execution successes (same-day discounted)
    f: float = 0.0  # soft execution failures
    memory: MemoryState | None = None  # None: never practiced here, or a background component
    n: float = 0.0  # practice count for speed
    attempts: int = 0
    successes_today: int = 0
    today: date | None = None
    last_var_day: date | None = None  # last study day the drift was applied


CALIBRATION_TIERS = 5


@dataclass(frozen=True, slots=True)
class SharedParams:
    """Shared parameters (design 3.5). Refit ones: slip, delta4, calib_a, calib_b, phi, tau,
    sigma_t. Fixed in v1: gamma, rho, alpha, delta5."""

    version: str = "prior"
    slip: float = 0.05
    delta4: float = 0.3
    delta5: float = 0.7
    calib_a: tuple[float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0)
    calib_b: float = 1.0
    phi: float = 1.0
    tau: float = 0.6931471805599453  # ln 2
    sigma_t: float = 0.45
    gamma: float = 0.37
    rho: float = 0.10
    alpha: float = 0.3
    q_drift: float = 0.01
    kappa: float = 0.95
    same_day_weight: float = 0.25
    prior_new_mean: float = 0.6190392084062235  # logit(0.65)
    prior_new_var: float = 2.0
    prior_background_mean: float = 3.4760986898352733  # logit(0.97)
    prior_background_var: float = 1.0
    fsrs_weights: tuple[float, ...] = ()  # () = FSRS-6 defaults


@dataclass(slots=True)
class StudentState:
    params: SharedParams
    components: dict[ComponentId, ComponentState] = field(default_factory=dict)
    # per main skill: (sum of time residuals, count) for the shrunk speed offset tau_s
    skill_speed: dict[ComponentId, tuple[float, int]] = field(default_factory=dict)
    # running statistics of time residuals: (mean, M2, count)
    time_stats: tuple[float, float, int] = (0.0, 0.0, 0)
    theta_hat: float = 0.0
    last_at_ms: int | None = None


@dataclass(frozen=True, slots=True)
class Prediction:
    p: float  # calibrated P(correct first try)
    p_raw: float  # before the per-tier recalibration
    q: tuple[tuple[ComponentId, float], ...]
    e: tuple[tuple[ComponentId, float], ...]
    r: tuple[tuple[ComponentId, float], ...]
    median_minutes: float
    pace_ok: bool  # median <= standard time


@dataclass(frozen=True, slots=True)
class UpdateRecord:
    prediction: Prediction  # made before the update
    blame: tuple[tuple[ComponentId, float], ...]
    memory_share: tuple[tuple[ComponentId, float], ...]
    attempt_id: int | None = None  # the observation's (added: replay records follow its order)
