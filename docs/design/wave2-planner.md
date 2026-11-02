# Wave 2 planner changes (design v1.2 addendum)

2026-11-02 · owner direction 16:01–16:12 (`docs/backlog.md`, "Learning design").
Implemented in `core/plan/`. The public functions keep their signatures; the types gain fields. Each change comes with tests.

The owner's learning design is the frame:
- Practice is unassisted: no hints and no explanations.
- A wrong answer means try again. The solution shows only on give-up.
- When a student is stuck, the app changes the problem, never explains.
- Certification of the exam-level milestones is a closed-book, timed sitting.

## 1. The stuck ladder

Per skill, per study day, counted over the skill's own items: items whose `skill_id` is the skill, any role, first tries only (a `ServedItem` with `correct` not None). `streak` is the number of consecutive misses since the skill's last success today. A success resets it.

| streak | The skill's next item today |
|---|---|
| 0 | As planned |
| 1 | **Smaller problem.** A problem one tier lower (at least tier 1) whose components include the most-blamed component k* of the last miss (`ServedItem.update.blame`, the largest b). If k* is the skill itself, it is a problem of the skill one tier lower. Prefer problems never served to the student, then the least recently served. `reason="ladder:smaller"`, `ladder=1` |
| 2 | **Prerequisite.** A problem whose main skill is the most-blamed component other than the skill itself, taken from the last two misses' blame summed. If that component has no pool, the skill's `requires` in course order; if there are none, a smaller problem again. Tier 1–2. `reason="ladder:prerequisite"`, `ladder=2`, `skill_id` is the prerequisite |
| 3 | **Set aside.** No more items of the skill today. `DayPlan.set_aside` gains the skill, and `DayPlan.notes` a line naming its deck (the session turns that into the textbook pointer). The skill returns the next study day with a problem from a family not served in the last 7 days, at the tier where it was failing |

- A ladder item **replaces** the skill's next planned item. It never adds one. With rung 3 the day loses items. So the day's count stays at or under its first plan: this fixes the 6.2 gate "daily items never exceed the plan".
- **The first plan holds every slot.** It includes each skill's full growth allowance (up to 3), so a re-plan only removes or substitutes. Where the planner now adds items after a miss, it must reserve them at the start instead.
- A ladder item's outcome counts like any other first try: certification evidence at its tier, and a learner update.
- The struggling state (status.py) stays for the cross-day case: 10 or more first tries on a skill without M1. Its prerequisites get growth.

## 2. Certification sittings for M2 and M3

Practice first tries keep feeding the model and the certifier's posterior, but **M2 and M3 certify only through a sitting**: a closed-book, timed block of unseen problems. M1 and Keep certify from practice as now.

- **When.** A skill gets a sitting when all of these hold:
  - its current milestone is M2 or M3;
  - the model's calibrated readiness at the milestone tier (`readiness`) is at least the target;
  - it has at least 2 practice first tries at that tier, with the last one a success;
  - it has had no failed sitting in the last 2 study days.

  Due skills are batched into one sitting per day, at most 3 skills, earliest deadline first. A sitting is never planned in the first 20 minutes of a session's expected time, so practice warms up first.
- **What.** For each skill, 2 problems at the milestone tier that the student has never been served (any role), from different families; 3 if the skill's pool allows.
  - The problems are served consecutively as one block, in random order across skills, `role="sitting"`, with `sitting` set to a per-day id.
  - Each problem's time limit is its standard time T*. The time is shown, but the attempt isn't cut off.
- **Pass.** Every problem of the skill is correct on the first try, unaided, and within its T*. The milestone certifies on that day.
  - The certifier records the pass: certify.py reads `role == "sitting"` observations for M2 and M3.
  - Revocation is unchanged: the recency-weighted posterior over all evidence at the tier falling below target − 0.10.
- **Fail.** The skill goes back to growth at that tier, and the 2-day wait applies. A failed sitting's problems count as practice evidence.
- **No pool.** If too few unseen problems remain at the tier, the sitting uses the least recently served ones, and `DayPlan.notes` says the pool is thin.
- **Logging.** The sitting's items carry `milestone` and `tier`, and the plan logs which skills sat (`DayPlan.sittings`).

## 3. A harder growth band (owner option)

`CourseSettings.growth_band: tuple[float, float] = (0.70, 0.90)`. The owner can choose `(0.50, 0.75)`. select.py uses it in place of the constant. The fallback becomes the problem closest to the band's midpoint.

## 4. Fixes

- **order.py.** A unit that can't avoid sitting next to its own skill is placed anyway, adjacent to it, instead of dropped. `DayPlan.dropped` stays empty except for a true conflict, and a note records the forced adjacency.
- **Re-plans never add items** beyond the first plan (see 1).

## 5. Type changes (`core/plan/types.py`)

- `Role` adds `"sitting"`.
- `WorkItem`:
  - `ladder: int = 0`;
  - `sitting: str | None = None`;
  - `time_limit: float | None = None` (T* for a sitting item).
- `DayPlan`:
  - `set_aside: tuple[ComponentId, ...] = ()`;
  - `sittings: tuple[tuple[str, tuple[ComponentId, ...]], ...] = ()` (sitting id and its skills).
- `CourseSettings` adds `growth_band`.
- `core.learner.types.ROLES` adds `"sitting"`.

## 6. Tests and gates

- Unit tests for every rule above.
- The sim2 harness learns the sitting role. Its truth students answer sittings like any first try.
- `tests/sim2/test_harness.py` must pass the "daily items" gate without the xfail.
- Run `scripts/check.sh fast`; the coordinator runs `check.sh gates` afterwards.
