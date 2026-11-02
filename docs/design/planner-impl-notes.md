# Planner implementation notes (core/plan, design v1.1 sections 3.7, 3.8, 4)

- Branch: plan-core, 2026-11-02. Spec: `docs/design/student-model.md` v1.1; contract: section 8.
- Where the spec leaves room, the planner takes the reading closest to its intent. Each choice is
  listed here with the reason. Items marked **(owner)** change behaviour the owner will see, so
  the coordinator should confirm them.
- The "Wave 2" section at the end (`docs/design/wave2-planner.md`, design v1.3) supersedes some
  of the wave 1 choices below; each one is marked *(wave 2: ...)*.

## Interfaces

- **`core.plan.protocol.Predictor[S]`** is the planner's whole view of the student model:
  - `predict(state, problem, at_ms) -> Prediction`;
  - `copy(state) -> S`;
  - `component_info(component_id) -> ComponentInfo | None`;
  - `slip(state) -> float`.
- `predict` must depend on the problem only through `main_skill`, `components`, `tier`, `steps`
  and `standard_minutes`, as design 3.2-3.3 does. The planner caches predictions on those fields,
  so a template's 200 instances cost one prediction.
- A component the catalog doesn't know counts as background ("outside the course's sections",
  design 2.1).
- `copy` is in the protocol for what-if helpers. No v1 planner rule needs it, because forecasts
  are predictions at later times and never simulated updates (critique 2).
- **Inputs from storage** (wave 2) come in as plain values:
  - `Certifier.observations` is the history: every first try, today's included. Build it with
    `Certifier.from_model`, which takes the model's priors; without them every prior is 0.5,
    and certifying at 0.9 takes 16 straight successes;
  - `served_today` is today's `ServedItem`s in order. Each carries its `WorkItem`, its outcome, the
    `UpdateRecord` (blame and memory share) and the minutes spent;
  - optional: `spent_minutes` (attempt id to minutes), `examples_seen`, `retired`,
    `next_study_day`.
- **Added fields** (none renamed or removed):
  - `WorkItem`: `tier`, `milestone`, `missed`, `block`, `p`, `reason`;
  - `SkillStatus`: `bottleneck`, `prerequisites`, `assumed`;
  - `DayPlan`: `hours_basis`, `statuses`, `confusable`, `overflow`, `dropped`;
  - new types: `ServedItem` and `ConfusableDecision`.
- `choose_problem` returns `ProblemSpec | None`. None means nothing qualifies.
- `order` stays in `core.plan.order`. Re-exporting it from `core.plan` would shadow the module.
- The ruff 0.17 formatter failed on the Python block in the spec's section 8, which broke
  `check.sh` on main. That block is reformatted, with no text changes (first commit).

## Pace schedule (4.1)

- **Calendar.** A section starts after `floor(cumulative hours / (weekly hours x pace factor) x 7)`
  days. "Aligned" anchors the aligned section on its day.
  - With both a start date and an alignment, the alignment wins, as the newer fact.
  - With neither, nothing is introduced.
  - A pace factor outside 0.75-1.5 raises ValueError; the UI validates first.
- **Introduction.** A skill whose section is missing from the pace standard has no date, and
  neither does any skill that requires it (literal "once its prerequisites are introduced").
  - Requirement cycles settle on the latest section date in the cycle.
  - Skills flagged `background` are never introduced or planned. The one exception is growth
    added for a struggling skill's prerequisites.
- **Milestone tiers never exceed the target tier**: M1 = min(2, target), M2 = min(3, target).
  - A milestone at a tier with no problems is left out. It can't be certified from direct
    evidence, the same reason `level` skips such tiers.
  - A skill whose pool is empty therefore has no milestones and shows as maintenance.
- **Exam pull.** An exam pulls M2 only when it falls on or after the introduction and its scope
  lists the skill's deck or a parent deck (a unit covers its sections).
  - M2 is never pulled before the introduction day.
  - M1's deadline is then at most M2's, so deadlines stay in order (M1 <= M2 <= M3).
- **Keep.** "After the end date" means strictly after.
  - Keep certifies at the keep tier, or at the nearest tier with problems.
  - Keep is accuracy-only: untimed, so it needs n_eff >= 3.
  - Keep has no deadline, so a Keep skill is on track, and its growth is not "missed-milestone"
    work.

## Certification (3.7, 3.8)

- **Age** is counted in study days.
- **Timed rule.** A correct first try without a valid time is left out of the timed posterior.
  It shows neither success nor failure at pace, and counting it as a miss would punish the
  timer. An aided first try is a failure. *(Wave 2: posteriors are accuracy only; pace is the
  sitting's.)*
- **Prior.** p is the mean calibrated prediction over the representative problems: at most 10,
  the lowest problem IDs in string order, retired cards left out. It is taken at query time.
  - The same p serves the whole hysteresis replay, because no historical priors are stored.
  - The timed key uses the same p: `Prediction` carries no sigma_T, so P(T <= T*) can't be
    formed. With kappa0 = 4 the prior is weak.
  - With no model prior supplied, p = 0.5.
- **Hysteresis replay.** Certification and revocation are evaluated on every evidence day, both
  before and after that day's attempts, and on the query day.
  - Between those points the mean moves monotonically toward p, so no revocation is missed.
  - A certification reachable only in the middle of an evidence gap is not taken.
  - Comparisons use a 1e-9 tolerance.
- **Level (owner).** Read literally, "every tier ℓ' <= ℓ that has problems is certified" leaves
  almost every skill without a level. Tier 1 drills are served only in the new block, which
  stops at the first success, so tier 1 almost never reaches n_eff 3.
  - Implemented: the highest certified tier such that no lower tier with problems is *judged
    and uncertified*. Judged means it has n_eff at its threshold, or was certified before.
  - Untested tiers neither count nor block. A failed lower tier still blocks, which is the
    critique 17 concern.
  - Tiers 3 and up use the M2/M3 rule (timed, n_eff 4). *(Wave 2: the M2/M3 rule certifies
    only through a sitting; n_eff 4 still marks a tier as judged.)*

## Statuses (4.2)

- **New** lasts until the block is done:
  - a first-try success on the skill in any role;
  - 3 block problems on any days;
  - or no block problem left and the example seen (`examples_seen` covers earlier days), or no
    example exists.

  A skill introduced while the student was away is still new on its first study day. The
  example is shown again at the start of each day's part of the block.
- **Growth targets the next uncertified milestone straight away**, not only near its deadline.
  Maintenance needs every milestone certified, because growth at the milestone tier or one below
  keeps the lower tiers practised.
- **Slip-limited (owner).** All four conditions must hold:
  - every course component's e >= 0.97 over the milestone-tier pool;
  - the posterior is below target, with n_eff at the threshold (the design's "still");
  - "the shortfall explained by s" holds both ways: the model's chance over the representatives
    satisfies P_raw < target <= P_raw / (1 - s), so growing components can't close the gap;
  - and the observed shortfall fits, mean / (1 - s) >= target.

  Without the third condition, the first version marked every near-target skill slip-limited at
  s = 0.02 in simulation.
  - A slip-limited skill gets no growth.
  - It gets one problem a day at its milestone tier (maintenance role, closest to target). Its
    forecast stays below target, so this repeats daily and gives the student a chance to show
    care. With no items at all it could never recover.
- **Struggling.** The skill's last 3 growth days since its current milestone became current must
  each have the full allowance (3 growth problems), and the posterior at the end of the last day
  must be no higher than before the first. A day cut short by two successes in a row resets the
  count.
  - The weakest component is the bottleneck.
  - Its prerequisites get growth at their working tier (background skills with a pool: tier 2):
    course skills that have problems and are introduced.
  - The skill keeps its own growth. The note points to the textbook.
- **Track.** Behind means the current milestone's deadline has passed. Ahead means the current
  milestone lies past the one the schedule is on, or everything was certified before the last
  deadline.

## Daily work (4.3, 4.6)

- **`plan_day` is an upper bound.** Blocks are planned at full size and growth at the full
  allowance; re-plans after answers shrink it.
  - `next_item` is the plan's first item.
  - Without an `rng`, the seed comes from the course, the day and the served count, so a re-plan
    at the same point repeats.
  - A miss can still add an item: the 4.6 retry, or a revoked certification turning maintenance
    into growth. Gate 6.2's "daily items never exceed the reported plan" holds against the latest
    plan. *(Wave 2: re-plans never add items; the gate holds against the first plan.)*
- **Caps.**
  - The 3-a-day per-skill cap counts new, growth and maintenance problems. Examples and
    reference checks are left out; see the checks bullet.
  - The growth allowance counts growth problems.
  - The stop after 2 consecutive successes looks at all of the skill's plan items today.
  - Focused Practice, practice tests and placement are outside the plan, its caps and its
    positions.
- **Maintenance.** Forecasts are taken on the next study day at the current time of day.
  - **Exam horizon (owner):** only exams within 21 days count. Taken literally, a final months
    away would make every skill in its scope due every day. 21 days matches the earlier
    booster and practice-test window.
  - **Mid-course start (owner):** assumed-learned skills get no forecast maintenance until their
    Keep key has evidence of its own (n_eff 3). The model knows nothing of them, so it would make
    every one due every day, the backlog critique 14 removed. Reference checks test them. A
    failed one revokes the assumption: the Keep prior is max(p, 0.80), so one miss gives
    3.2/5 = 0.64 < 0.70, and the skill goes back to growth at the Keep tier.
- **4.6 retry.** When the skill's latest first try today was a miss and its top suspect's memory
  share is below 0.5, one more problem follows later, if the skill has room and nothing else
  planned. It uses the skill's current role. *(Wave 2: its slot is held from the first plan.)*
- **Reference checks.**
  - They are exempt from the per-skill cap. Excluding capped skills would bias the uniform draw
    toward skills that are going well (their growth stopped early).
  - Eligible skills are introduced, past their new block and not background, with a never-served
    problem at their current or certified tier.
  - The draw picks a uniform skill, then a uniform problem.
  - Positions count the day's plan items. Each ten gets at most one check: at its 10th
    position, or at the next boundary when a new block covers it (a block is never split), or
    when the check's skill would sit next to its own skill. A missed ten is not made up.
    Nothing ends on a check. *(Wave 2: no check until the day's new material is done.)*
- **Missed-milestone share (owner).** In simulation, the literal "at most 40% of the day's items"
  starved catch-up: a student behind once no new sections remained got nothing for weeks, since
  40% of no other work is none.
  - Implemented: missed-milestone growth is at most 40% of the day up to its last item of other
    work, spread evenly so no prefix exceeds its share.
  - Anything beyond that comes after all other work (`DayPlan.overflow`, with a note), at
    priority 2.
  - New material always comes first, so the stated purpose (it is never crowded out) holds.
  - Which items fit: earliest deadline first, one per skill per round.
- **No two consecutive items of one skill** is a hard rule, as the property in the brief
  requires.
  - An item that can't be placed is dropped (`DayPlan.dropped`, with a note).
  - The last 8 units of each part are ordered by an exact, bounded search, so drops happen only
    when no valid order exists.
  - **(owner)** With one skill in play (early in a course, or one growing skill left), it gets
    one problem a day. The alternative is to relax the rule when nothing else can go next, as
    the old queue did. *(Wave 2: that alternative, as the spec's 4 Fixes asks.)*
- **Minutes** are the sum of predicted medians. A worked example counts 2 minutes, the earlier
  queue's estimate.
- **Hours to keep pace.** They come from the history once 10 milestones (M1-M3) have been
  certified from evidence.
  - Minutes per milestone are the skill's attempt minutes from its previous certification through
    this one, split evenly among milestones first certified the same day.
  - An attempt's minutes are the recorded time, else its valid time, else T*.
  - The milestones of "next week" are the schedule's deadlines in the 7 days after today,
    certified or not, and none after the end date.
  - A tier with no history borrows the nearest tier's figure (the higher one on a tie).
  - Maintenance adds one problem per skill whose forecast falls below target within the week, and
    every day for a slip-limited skill.
  - The stand-in is the pack's outside hours, or 2 h per weekly class hour (34 CFR 600.2), times
    the pace factor. `hours_basis` says which was used.
- **Feasibility.** K is the mean component count over every target-tier problem of the course.
  The note appears when (1 - s) x 0.99^K is below target.

## Choosing the problem and order (4.4, 4.5)

- **Growth order of preference.**
  - With problems in the band: the suspect rule, then the bottleneck, then a different surface
    form, then the milestone tier over the rung below, then closest to 0.80.
  - With an empty band: closest to 0.80 first.
- **The spread-blame rule** applies to the skill's next growth problem after a miss today. Blame
  comes only from today's `UpdateRecord`s; on later days the model has already absorbed it.
- **Surface form** is `ProblemSpec.family`. A template instance (family != card id) waits 180
  days before it can repeat, any other card 90.
  - When every card in the pool was seen within its window, the rule relaxes. The role's
    criterion still decides first, then a different form, then the least recently seen.
  - The same card never comes twice in a study day, relaxed or not.
- **Confusable pairs.** Every pair present in the mixed set gets one draw.
  - Adjacent (p = 0.5): one item of each is glued together, in random order.
  - Apart: they are kept from touching where there is a choice.
  - Each draw is logged with whether the pair ended up adjacent.

## Tests

- `tests/plan/`: unit tests for each rule, with dates and numbers worked out in docstrings.
- Hypothesis properties: caps; new before missed; the 40% share; no same-skill neighbours; no card
  twice; the check rule; seed determinism; milestone monotonicity.
- One scenario per status, on a deterministic fake predictor (`tests/plan/fakes.py`).
- A purity guard: no storage, clock or I/O imports in `core/plan`.

## Wave 2

Spec: `docs/design/wave2-planner.md`, with the coordinator's design v1.3 correction (pace is
the sitting's block time; posteriors are accuracy only), the corrected struggling rule (it
stays as status.py builds it) and the gate-1 fix (new material first, no checks in between).
Tests: `tests/plan/test_ladder.py`, `test_sitting.py`, and additions to the other files.

### Interfaces

- No public function changed its signature: `plan_day`, `next_item`, `status(es)`, `order`,
  `choose_problem`, the `Certifier` methods, `intro_dates`, `milestones` take the same
  arguments. Types only gained fields with defaults.
- New fields beyond the spec's:
  - `WorkItem.ladder_for`: the stuck skill whose slot a ladder item fills (see the first spec
    problem below);
  - `WorkItem.day_items`: the day's first plan's size, stamped on every item;
  - `WorkItem.sitting_block`: the sitting's problem ids in serve order, on sitting items;
  - `DayPlan.adjacent`: the skills placed next to their own skill (the 4 Fixes);
  - `DayPlan.sitting_chances`: the logged pass chance of every skill that met the other
    sitting conditions (v1.3: "grade C, logged").
- **What the session must keep:** `plan_day` is stateless, so the day's frame rides on the
  served items. Pass each served item's `WorkItem` back exactly as the planner returned it (after
  a restart, rebuild it with `day_items`, `ladder_for`, `sitting` and `sitting_block`).
  Without them the planner degrades rather than breaks: no `day_items` means no cap (the
  structural rules below still hold), and a sitting item without its block is treated as a
  finished sitting.
- New helpers: `core.plan.ladder` (streaks, blame, the return rule), `core.plan.sitting` (the
  pace and pass chances, a sitting under way, the practice and wait rules), `select`'s
  `choose_growth_in` (the course's band), `choose_smaller`, `choose_prerequisite`,
  `choose_return`, `choose_sitting`, `order.arrange` (`order` with the sitting),
  `certify.SittingResult`, `sitting_outcome`, `sitting_results` and `Certifier.sittings`.
- `Predictor` gains an **optional** `sigma_t(state)`; without it the sitting's pace chance uses
  design 3.5's prior 0.45. The adapters' `_PlannerModel` reads `state.params.sigma_t`.

### Re-plans never add items (sections 1 and 4)

- **The day's cap.** The first plan (nothing served yet) stamps its size on every item. A later
  plan reads the stamp from the served items and keeps served + planned within it, leaving out
  the overflow's last items first, then the mixed set's last (the last round of the
  round-robin), then the last-batched skill of a sitting not yet started; new blocks and a
  sitting under way always fit, because they only shrink after the first plan.
  - Why a cap and not only the spec's "reserve every slot": the planner is stateless, and what
    falls due moves during the day (the maintenance forecast is taken at the current time of
    day, the model updates after every answer, a reference check becomes possible once a block
    ends). Structural reservations alone can't promise the gate; the stamp can.
- **Structural reservations** keep the cap from binding: new blocks and growth at full size (as
  before), and the 4.6 retry **held** as a second maintenance slot (reason "retry"). A re-plan
  keeps that slot only after an execution miss (m < 0.5), and the ladder then fills it; any
  other outcome releases it. The cost: the first plan lists up to two problems per due skill.
- **A skill's slots follow its first role of the day:** a skill whose first item today was
  maintenance keeps to its retry slot, even when the miss revoked its certification (it used to
  gain two growth items); a skill that practised today in another role gets no maintenance item
  that day.
- Retries after a reference-check miss are no longer added: a check's slot can't be reserved
  without reserving a retry for every check.
- The cap counts plan items only (Focused Practice and practice tests stay outside the plan).

### The stuck ladder (section 1)

- **Streak**: today's first tries over the skill's items, any role (practice, reference checks,
  sittings, and items outside the plan), a `ServedItem` with `correct` not None; a success
  resets it; reaching 3 sets the skill aside for the rest of the day, even if a later success
  would reset the count. A rung-2 item counts for the stuck skill (`ladder_for`) and for the
  prerequisite (its own `skill_id`).
- **Where a ladder item goes:** in place of the skill's next planned problem (in its new block,
  or first in its lane), keeping that slot's role, block flag, missed flag, priority and
  milestone. Sitting problems and reference checks are never replaced. A skill with nothing
  planned gets nothing (the ladder never adds).
- **Rung 1**, a smaller problem: from the skill's own pool, one tier below the last miss's
  tier (at least tier 1), containing k* when any problem there does (else the skill's other
  problems at that tier, else the tiers below); never served first, then the least recently
  served, then a different form from the previous problem, then closest to the band's
  midpoint. k*: the largest blame of the last miss; ties go to the skill itself, then the
  lowest id; a miss without an `UpdateRecord` blames the skill. If nothing qualifies the
  planned problem stands.
- **Rung 2**, a prerequisite: the component with the largest blame summed over the last two
  misses, other than the skill (ties: course order, then id). "No pool" is read as "no tier
  1-2 problem left for it today", and a prerequisite still in its own new block is skipped
  (its block covers it). Then the skill's requires in course order; then a smaller problem
  again (`ladder=2`, reason `ladder:smaller`). Choice: tier 1-2, never served first, then the
  least recently served, then closest to the band's midpoint. The item counts toward the
  prerequisite's 3-a-day cap; when the prerequisite is full, it takes the place of the
  prerequisite's last planned practice problem.
- **Rung 3**, set aside: everything of the skill or in its slots leaves today's plan, reference
  checks and its part of a sitting included. The note reads "s: set aside for today after 3
  misses in a row. Textbook: <deck>."
- **The return** ("the next study day with a problem from a family not served in the last 7
  days, at the tier where it was failing"): on the first study day after one whose own first
  tries ended with two or more misses in a row, the skill's first problem is at the tier of
  the first miss of that run, from a family with no first try in the last 7 study days (never
  served first, then the least recently served). When every family there was served that
  recently, the normal choice stands. See the second spec problem for why two misses.
- **Interactions:** the spread-blame rule (4.4) still chooses the skill's planned problem, but
  after a miss the ladder replaces it, so the rule now decides only when the ladder finds no
  smaller problem. The struggling rule stays as status.py builds it (coordinator).

### Certification sittings (section 2, design v1.3)

- **Certifier.** Posteriors are accuracy only at every tier (`first_try_success` ignores time;
  its `timed` keyword is kept and does nothing). The M2/M3 rule keeps the name `timed` in the
  certifier's signatures and now means: certified only on the day of a passed sitting, and
  n_eff 4 to count as judged (level, slip-limited). A pass whose posterior is already below
  target - 0.10 does not certify (it would be revoked at once); revocation is unchanged.
- **Pass, fail, void**, per skill and study day (its role "sitting" first tries at the tier):
  pass when all are right, unaided, and their summed valid time is within their summed T*;
  fail on a wrong or aided answer or a slow block; void when all are right but a time is
  unknown, or fewer than 2 were answered (an interrupted sitting). A void sitting needs no wait.
- **When:** the current milestone is M2 or M3 (not Keep); readiness at its tier (the model's,
  now) at least the target; 2 or more practice first tries at that tier and the latest (by time)
  right; no failed sitting on either of the 2 days before today (calendar days, as everywhere
  in the planner); not set aside; no sitting yet today. Practice is every first try at the tier
  except a passed sitting's: a failed or void sitting's problems count (the spec), so after a
  failed sitting a practice success comes before the next one.
- **Pass chance** (v1.3): drawn problems first, then P_pass = (product of their calibrated P)
  x the Fenton-Wilkinson P(summed times <= summed T*) from their predicted medians and
  sigma_T. Below `SITTING_PASS_MIN` the skill keeps growing and the plan has one note for it,
  "not yet at pace" with the accuracy and time parts (one per skill per plan; plans are
  recomputed after every answer, so the session should show the latest).
- **What:** among the skill's problems at the tier that were never served (any role, today
  included), families are drawn uniformly, then a problem in each: 3 when 3 families exist, else
  2. With fewer than 2 such families the least recently served problems stand in, one per family
  while families last, with the thin-pool note. Fewer than 2 problems left: no sitting, and a
  note. The sitting's problems are chosen before any practice, so practice never takes them.
- **Batch:** due skills by deadline, then course order, until 3 are chosen; the block is shuffled
  across skills (rng), so two problems of one skill may be neighbours inside it.
- **Warm-up:** "never in the first 20 minutes of a session's expected time" is read on the study
  day (the planner doesn't see sessions): the block starts at the first boundary after the new
  material where the served minutes (as recorded, else expected) plus the planned expected
  minutes reach 20. On a shorter day it comes after the whole mixed set, before the
  missed-milestone overflow: read literally, the rule would rule out sittings for every
  student whose day is short (a strong student's is), and gate 1 needs those.
- **Serving:** once a sitting item is served, every later plan starts with the rest of the block
  in its order (`sitting_block`), whatever came due meanwhile. Its first problem is rotated to
  avoid the last item's skill when it has another; checks wait for its end like new blocks.
- **Fields:** `sitting` = `sitting:<course>:<day>`; `time_limit` = the item's skill's limit,
  the sum of T* over its sitting problems (v1.3: the pass is judged per skill against that sum;
  the session can sum the skills' limits for one clock); `milestone` = the milestone of that
  tier. Sitting problems are outside the 3-a-day cap and the growth allowance, inside the day's
  positions and its cap.

### The harder growth band (section 3)

- `CourseSettings.growth_band`, validated `0 < low < high < 1`. `choose_growth` keeps its
  signature (and the default band); the planner calls `choose_growth_in(band, ...)`. The empty
  band's fallback is the band's midpoint, which is 0.80 for the default. The ladder's choices
  use the same midpoint as a late tiebreak.

### Order (section 4) and gate 1 (coordinator)

- **Forced adjacency.** A unit that can only follow its own skill is placed there, logged in
  `DayPlan.adjacent` and in a note; `DayPlan.dropped` stays empty (the order no longer drops).
- **Gate 1, "new material is always served on its date".** A calc1-ch4 run (a-model, typical,
  seed 1) on the wave 1 planner had 8 violations, every one a day whose roles read like
  `nnnnnnnnncnnnnn`: a reference check placed between two new blocks (when the 10th position
  fell at a block boundary), after which the 60-minute budget ran out before the later blocks.
  The check made the day "other work served", which is the violation. Fix: no check until the
  day's new material is done; the decade's check then comes at the first position after it, if
  still in that ten. New material is never deferred: the plan has no budget, every new block is
  planned first and whole, and a day whose new blocks alone fill the budget remains the gate's
  "budget-limited" count, not a violation. The same run had 1 day over its plan (13 served, 12
  planned: a check that became possible once a block ended), which the day's cap now prevents.

### Spec problems found (implemented the closest sound version)

1. **The streak can't reach 3 under its own definition.** "Counted over the skill's own items:
   items whose skill_id is the skill" and rung 2's "skill_id is the prerequisite" together mean
   the rung-2 outcome never counts for the stuck skill. Its streak then stays at 2, every later
   slot becomes another prerequisite problem, and rung 3 is unreachable for a skill with the
   usual 3 slots (miss, smaller miss, prerequisite). Fix: `WorkItem.ladder_for`; the rung-2
   item fills the stuck skill's slot and its outcome is that skill's next step.
2. **The return can't see the rung-2 item.** Observations carry the problem (the
   prerequisite's) and the role, not `ladder_for`, so the next day can't tell a set-aside from
   two misses followed by a right prerequisite problem. The return therefore triggers on a day
   that ended with two or more of the skill's own misses in a row (every set-aside day does).
3. **"Never in the first 20 minutes"** is read as "after up to 20 minutes" (see the warm-up).
4. **The v1.3 example numbers.** The specified Fenton-Wilkinson formula gives 0.722 for 3
   problems at a median of 0.8 T* with sigma 0.45 and 0.404 at a median of T* (a Monte Carlo of
   the exact sum agrees: 0.724 and 0.405), not "about 0.68" and "about 0.36". The tests pin the
   formula's values.
5. **The pass-chance gate sets a stricter pace bar than pace_ok.** A student exactly at the
   design's pace (median = T*) has a time chance of 0.40 on 3 problems (0.44 on 2), so with
   any accuracy below 1 its pass chance is under 0.5 and it never sits. With accuracy 0.97 per
   problem the gate needs a median of about 0.91 T* on 3 problems (0.93 T* on 2). That may be
   intended (an exam is a block), but it is not "median <= T*".
6. **The struggling rule and the ladder.** Struggling needs 3 days with 3 growth first tries
   of the skill's own; on a stuck day the third slot is usually the prerequisite's problem, so
   those days count 2 and the rule rarely fires for the skills the ladder is helping.
7. **The simulator's "ready at pace"** (truth readiness x P(T <= T*) per problem, in
   `tools/sim2/harness.py`) is the per-problem product v1.3 calls wrong. It feeds the report's
   ready and false-certification columns (and gate 4 through false certifications); I left the
   simulator's definition alone for the coordinator to decide.
