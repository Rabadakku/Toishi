"""Planner constants (docs/design/student-model.md v1.1, section 7, and the rules of sections
3.7, 3.8 and 4). Grades as in the design: B = indirect evidence, C = a design assumption.

Constants marked "impl" are not in the design; docs/design/planner-impl-notes.md says why each
was chosen.
"""

DAY_MS = 86_400_000
EPS = 1e-9  # tolerance for threshold comparisons on floats

# Pace schedule (4.1).
PACE_FACTOR_MIN = 0.75
PACE_FACTOR_MAX = 1.5
# B: median homework due date, 5 days after a topic's first lecture (top-30 Calc I syllabi)
M1_DAYS = 5
# B: median first exam covering a topic, 16 days after its first lecture, minus EXAM_PULL_DAYS
M2_DAYS = 14
# C+: the median gap between midterms (28 days): above-exam level by the next exam
M3_DAYS = 28
M1_TIER = 2
M2_TIER = 3
EXAM_PULL_DAYS = 2  # an exam pulls M2 (only) to the exam date minus 2 days

# Certification (3.7). B for the thresholds, C for the values.
KAPPA0 = 4.0  # prior strength at the model's calibrated prediction
N_EFF_UNTIMED = 3.0  # M1 (and Keep, which is accuracy only: impl)
N_EFF_TIMED = 4.0  # M2, M3
HALF_LIFE_DAYS = 30.0  # recency weight 2^(-age / 30 days)
REVOKE_MARGIN = 0.10  # revoked below target - 0.10
DEFAULT_PRIOR = 0.5  # impl: prior mean when the caller supplies no model prior
TIMED_FROM_TIER = 3  # impl: level and bare tier queries use the M2/M3 rule from tier 3 up

# Representative problems (3.8).
REPRESENTATIVES_MAX = 10

# Statuses (4.2).
SLIP_LIMITED_E = 0.97  # every course component's execution at or above this
STRUGGLE_DAYS = 3  # study days at the full growth allowance with no rise in the posterior

# Daily work (4.3). C unless noted.
NEW_BLOCK_MAX = 3  # B: worked example + up to 3 blocked tier 1-2 problems until a success
NEW_TIERS = (1, 2)
GROWTH_ALLOWANCE = 3  # growth problems per skill per day (direction A)
GROWTH_STOP_STREAK = 2  # stop for the day after this many consecutive first-try successes
SKILL_DAILY_CAP = 3  # problems per skill per day outside Focused Practice
CHECK_EVERY = 10  # B: every 10th item is a reference check
MISSED_SHARE = 0.40  # missed-milestone growth: at most this share of the day's items
EXAM_HORIZON_DAYS = 21  # impl: exams within this many days add their date as a horizon
RETRY_MEMORY_SHARE = 0.5  # 4.6: a miss whose top suspect has m below this gets one more problem
FEASIBILITY_COMPONENT = 0.99  # best attainable per-component chance in the feasibility check
HISTORY_MIN_CERTIFICATIONS = 10  # "about 10 certifications" before history-based hours
OUTSIDE_HOURS_PER_CLASS_HOUR = 2.0  # 34 CFR 600.2: the stand-in when the pack gives none
EXAMPLE_MINUTES = 2.0  # impl: a worked example, as the earlier queue estimated it (EXAMPLE_MS)

# Choosing the problem (4.4). C.
GROWTH_BAND = (0.70, 0.90)
GROWTH_FALLBACK_P = 0.80  # empty band: the problem closest to this
SPREAD_BLAME = 0.7  # spread blame: the top suspect's blame is below this
REPEAT_DAYS = 90  # no repeat within 90 days when the pool allows
TEMPLATE_REPEAT_DAYS = 180  # a template's parameter set (its instance) not within 180 days

# Order (4.5). B for the adjacency rule.
CONFUSABLE_ADJACENT_P = 0.5

# Priorities of WorkItem.priority (lower is served earlier when the session is cut short).
PRIORITY_NEW = 0
PRIORITY_NORMAL = 1
PRIORITY_MISSED = 2

# Roles that belong to the daily plan (Focused Practice, practice tests and placement are
# outside it: they neither count toward its caps nor toward its every-10th positions).
PLAN_ROLES = frozenset({"new", "growth", "maintenance", "check"})
