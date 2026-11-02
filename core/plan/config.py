"""Planner constants (docs/design/student-model.md, section 7, and the rules of sections 3.7,
3.8 and 4; the wave 2 additions of docs/design/wave2-planner.md). Grades as in the design:
B = indirect evidence, C = a design assumption.

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
GROWTH_BAND = (0.70, 0.90)  # CourseSettings.growth_band's default (owner option: 0.50-0.75)
GROWTH_FALLBACK_P = 0.80  # the default band's midpoint: an empty band takes the closest problem
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
PLAN_ROLES = frozenset({"new", "growth", "maintenance", "check", "sitting"})
# Plan roles that are not the skill's practice: outside the 3-a-day cap and the growth allowance
# (a reference check's draw stays uniform; a sitting is certification, not practice: impl).
UNCAPPED_ROLES = frozenset({"check", "sitting"})

# The stuck ladder (wave 2, section 1): the skill's next item today by its streak of misses.
LADDER_SMALLER = 1  # a problem one tier lower on the most-blamed component
LADDER_PREREQUISITE = 2  # a tier 1-2 problem of the most-blamed prerequisite
LADDER_SET_ASIDE = 3  # no more items of the skill today
LADDER_PREREQUISITE_TIERS = (1, 2)
RETURN_FAMILY_DAYS = 7  # a set-aside skill returns with a family not served in the last 7 days

# Certification sittings for M2 and M3 (wave 2, section 2; design v1.3). C unless noted.
SITTING_MILESTONES = frozenset({"M2", "M3"})
SITTING_MAX_SKILLS = 3  # one sitting a day, at most 3 skills, earliest deadline first
SITTING_PROBLEMS = 2  # unseen problems per skill at the milestone tier, different families ...
SITTING_PROBLEMS_MAX = 3  # ... 3 when the skill's pool allows
SITTING_PRACTICE = 2  # practice first tries at the tier first, the last one a success
SITTING_WAIT_DAYS = 2  # no sitting in the 2 study days after a failed one (a void one: no wait)
SITTING_WARMUP_MINUTES = 20.0  # never in the first 20 minutes of the day's expected time
# C, logged (DayPlan.sitting_chances): the model's chance of passing on the chosen problems,
# (product of their calibrated P) x P(their summed times <= their summed T*), needed to sit.
SITTING_PASS_MIN = 0.5
SIGMA_T_DEFAULT = 0.45  # design 3.5's prior for sigma_T, when the model reports none (impl)
