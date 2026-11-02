# Planner implementation notes (core/plan, design v1.1 sections 3.7, 3.8, 4)

- Branch: plan-core, 2026-11-02. Spec: `docs/design/student-model.md` v1.1; contract: section 8.
- Where the spec leaves room, the planner takes the reading closest to its intent. Each choice is
  listed here with the reason. Items marked **(owner)** change behaviour the owner will see, so
  the coordinator should confirm them.

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
  timer. An aided first try is a failure.
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
  - Tiers 3 and up use the M2/M3 rule (timed, n_eff 4).

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
    plan.
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
  planned. It uses the skill's current role.
- **Reference checks.**
  - They are exempt from the per-skill cap. Excluding capped skills would bias the uniform draw
    toward skills that are going well (their growth stopped early).
  - Eligible skills are introduced, past their new block and not background, with a never-served
    problem at their current or certified tier.
  - The draw picks a uniform skill, then a uniform problem.
  - Positions count the day's plan items. Each ten gets at most one check: at its 10th
    position, or at the next boundary when a new block covers it (a block is never split), or
    when the check's skill would sit next to its own skill. A missed ten is not made up.
    Nothing ends on a check.
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
    the old queue did.
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
