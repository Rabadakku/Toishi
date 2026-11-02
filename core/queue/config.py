"""Queue constants: the spec's numbers for the daily queue (docs/spec.md, "The daily queue",
"Study screen") and the starting guesses used before the student has logs of his own."""

from collections.abc import Mapping

# Triage classes (the table "What gets picked when more is due than N"); 0 = flashcards,
# which sit outside the problem count.
FLASHCARD = 0
CHECK = 1  # prerequisite checks triggered by recent errors (and diagnostic sets)
RELEARN = 2  # next-day redo after a lapse, relearning reviews, reinforcement
LEARNING = 3  # learning blocks already in progress
PREREQ = 4  # prerequisites of what is being learned or recently failed; QUE-4 escalations
EXAM = 5  # exam-window reviews and boosters
REVIEW = 6  # other due reviews (pluggable policy), mixed check-ups, vacation pull-forwards
NEW = 7  # new skills, cut first

# Ordering (How the session is ordered).
WARMUP_MIN = 2
WARMUP_MAX = 3
WARMUP_PLAN_MIN = 8  # three warm-up reviews only in a plan at least this long
SECTION_MIN_GAP = 2
CONFUSABLE_MAX_GAP = 3
REINFORCEMENT_GAP = 5
CHECK_GAP = 3
REDO_GAP = 2  # a redo after its skill's fresh rated review (I4)
QUICK_TIER = 2.5  # a "quick review" for the warm-up: expected tier at or under this
HARD_TIER = 2.5  # harder/easier alternation: expected tier at or above this is "harder"
FLASHCARD_GROUP = 5
FLASHCARD_RESHOW_GAP = 5  # I5: a missed flashcard comes back at least this many items later

# Fair share (QUE-11..13).
GOAL_WEIGHT: Mapping[str, float] = {"A": 1.5, "B": 1.0, "Keep": 0.5}
URGENCY_DAYS = 14
URGENCY_MAX = 3.0
BACKLOG_MIN = 0.5
BACKLOG_MAX = 2.0
CARRY_SHARE = 0.5  # a shortfall carries into tomorrow, capped at half a quota
OVERLOAD_DAYS = 3  # QUE-13: need above the count this many days running
BACKLOG_DAYS = 7  # QUE-8: backlog above 2N this many days
BACKLOG_MULTIPLE = 2

# Triage inputs.
RECENT_FAIL_DAYS = 7  # "recently failed": an Again within this many days
CHECKUP_SIZE = 4  # skills in a mixed check-up
BENCH_FACTOR = 3  # keep up to this many times N candidates for re-plans

# Minutes (QUE-3): starting guesses per expected tier until the student has his own times.
DEFAULT_PROBLEM_MS: Mapping[int, int] = {1: 90_000, 2: 150_000, 3: 210_000, 4: 300_000, 5: 420_000}
EXAMPLE_MS = 120_000
FLASHCARD_MS = 15_000
METHOD_MS = 15_000  # a which-method item takes about 5 to 15 seconds
TIME_HISTORY_DAYS = 120

# Other ways to study.
FOCUSED_DEFAULT = 10
EXTRA_DEFAULT = 10
PRACTICE_TEST_DEFAULT = 10
DEFAULT_TEST_MINUTES_PER_PROBLEM = 6  # only when the exam has no length entered
# Practice tests (ENG-8): how problems still unanswered when the test ends count. "skip"
# (C5, ADR-0014): an unrated attempt, zero only in the test's score; "again": rated Again.
TEST_UNANSWERED_KEY = "queue.test_unanswered"
TEST_UNANSWERED_DEFAULT = "skip"
TEST_RECALL_FLOOR = 0.2  # a skill's weight in a practice test is 1 - recall + this

# Timing guards (TIME-4/5).
CLOCK_SLACK_MS = 2_000
MAX_REPORTED_MS = 24 * 3_600_000

# Settings the queue keeps (stored as unknown keys; the storage accepts any JSON for them).
DAY_LOG_KEY = "queue.day_log"
DAY_LOG_KEEP = 35
VACATION_KEY = "queue.vacation"
DIAGNOSIS_DAY_KEY = "queue.diagnosis_day"  # the study day Diagnosis.daily() last ran
VACATION_LEAD_MAX = 7

DAY_MS = 86_400_000
MINUTE_MS = 60_000
