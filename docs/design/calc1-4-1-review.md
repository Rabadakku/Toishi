# Review: packs/calc1/4-1-related-rates.cards.md (OpenStax Calculus Vol 1 §4.1)

2026-11-02. Independent review of the worktree `agent-a1dfd0a654c90b1ef`. No file in the worktree was edited.
My scripts are in this scratchpad folder: `dump41.py` (dumps every built card with the project loader), `verify41.py` (templates), `verify41_static.py` (static cards and examples), `verify41_choice.py`, `scan41.py` (rendering), `lint41.py` (component rule), `grade_probe.py` and `grade_probe2.py` (the project grader on flagged answers).

## Defects, most serious first

### 1. `calc1.4-1.instant-curve.t03`: a wrong method is graded correct (12 of 16 instances)
- **What is wrong:** the wrong answer "speed of the bead along the wire", c√(1+4q²), is almost equal to the key, c(1+2q²)/√(1+q²). The default number tolerance is 1% relative, so typing that wrong answer as a decimal is graded **correct**.
- **Evidence:**
  - Relative gap between the wrong answer and the key: 2.38% at q = 2, 1.22% at q = 3, 0.73% at q = 4, 0.48% at q = 5.
  - Project grader (`core.grader.grade`):
    - q = 4, c = 2: the key is 66√17/17 ≈ 16.007, and the input "16.12" (the wire speed 2√65 ≈ 16.125) is graded `correct`.
    - q = 5, c = 5: "50.25" (5√101) is graded `correct`.
    - q = 3, c = 2: "12.1", the wire speed 12.17 rounded, is graded `correct`.
  - With `exact: yes`, the same "12.1" is graded `incorrect` and matched to the wrong line.
- **Fix:** add `exact: yes` (no calculator, and the key is a radical) or `tolerance: 0.1%`. Better: also change the target quantity so the two values separate, for example the distance to (0, 1) or the angle of the line to the origin.

### 2. Tiers 3 and 4 in five of the six blocks are fragments, not exam problems (student-model.md §2.2)
There are 25 such cards. Each asks for one sub-step of a related-rates problem, and tier 4 also requires "no hint of the method".
- **select** (one-step choices with 1 solution step, the same as tier 1; the stem names the quantity that picks the option, such as "the volume … never changes" or "the angle of the beam"):
  - tier 3: `select-cone-tank.001`, `select-trough.t01`, `select-boat.001`;
  - tier 4: `select-box.001`, `select-laser.001`.
- **relate** (3 to 4 steps, the same as tiers 1 and 2; the work is one line of an exam problem):
  - tier 3: `relate-bowl.t01`, `relate-rectangle.t01`, `relate-cylinder.001`;
  - tier 4: `relate-plank.001`, `relate-trough.001`.
- **eliminate:**
  - tier 3: `eliminate-trough.001`, `eliminate-cylinder-sphere.001`, `eliminate-cylinder-cone.t03`;
  - tier 4: `eliminate-bucket.001`, `eliminate-funnel.001`.
- **differentiate-time** (the relation is printed in the question):
  - tier 3: `time-triangle.001`, `time-resistors.001`, `time-implicit.t03`;
  - tier 4: `time-elevation.001`, `time-box.001`.
- **values-at-instant** (the differentiated equation, which is the method, is printed in the question):
  - tier 3: `instant-triangle.001`, `instant-trough.001`, `instant-curve.t03`;
  - tier 4: `instant-leak.001`, `instant-rect.001`.

The notes state the convention on purpose: "tier 3 is a typical exam-level instance of that demand, not a whole exam problem". The consequence:
- Milestones M2 (tier 3) and M3 (tier 4) for these five skills can be certified without solving one exam-level problem.
- The only whole problems in the section, the translate block's tiers 3 and 4, all have the skill `translate`.

Smaller tier mismatches:
- `translate-speed.t01` (tier 2) is one step, taking |rate|, so by the anchor it is tier 1.
- Several tier-1 cards use two components (`relate-sphere.001`, `relate-cars.001`, `relate-ladder.t01`, `eliminate-which.t01`, `instant-solve.t03`).

**Fix:** if component tiers are meant to measure the component alone, get a ruling from the process owner and record it in §2.2. Otherwise, re-tier these cards (most become tier 2) and give each skill tier 3 and 4 whole problems whose main skill is that component, as the 4.3 pilot does. Examples: a cone-tank dh/dt problem with the skill `eliminate-variable`; a problem whose instant is given by the volume, with the skill `values-at-instant`.

### 3. Copyright proximity (to the best of my knowledge)
I checked OpenStax 4.1 through the LibreTexts copy of its exercises. I could not read CLP-1 §3.2 here.

- **a. `select-pile.001` (and `eliminate-pile.001`).**
  - The card says: "forms a pile shaped like a cone whose height is always equal to the diameter of its base".
  - That nearly paraphrases Stewart's gravel and conveyor-belt problem: "forms a pile in the shape of a cone whose base diameter and height are always equal".
  - Only the material and the chute changed. `eliminate-pile.001` uses the same constraint (r = h/2).
  - OpenStax 4.1 exercises 35 and 36 (an allowed source) have a gravel cone whose radius is three times its height.
  - **Fix:** adapt OpenStax 35 and 36 with `source`, `source-url` and `modified: yes`, or choose another ratio. Either way, recompute the key of `eliminate-pile.001` (π/12) and its wrong answers (π/6, π/3).
- **b. `eliminate-funnel.001`.**
  - A cone drains through its point into a cylinder below it, and the cone is as deep as it is wide at the top (12 cm deep, 12 cm across).
  - That is the structure and the shape of Thomas's coffee-filter problem: a filter 6 in deep with radius 3 in, draining into a cylindrical pot. The scenario is not in OpenStax 4.1, and renaming it to a funnel and a jar does not change it.
  - **Fix:** a different configuration and different proportions.
- **c. `translate-tank-leak.001`** (lower risk).
  - An inverted cone pumped in and leaking out at the same time is Stewart's leaking-cone scenario, where the unknown is the pump rate. The card's numbers and unknown differ.
  - **Optional fix:** make the leak depend on the depth, as `instant-leak.001` does.
- **d. Attribution missing for an allowed source.** These two cards inherit `source: original`:
  - `relate-cone-water.001` uses the exact tank of OpenStax 4.1 exercises 25–27 ("a height of 16 ft and a radius of 5 ft").
  - `instant-triangle.001` uses OpenStax exercise 23's angle rate and instant (0.1 rad/s at π/6).
  - **Fix:** add `source`, `source-url` and `modified: yes` (CC BY-NC-SA requires attribution), or change the numbers.

### 4. Solution sentences that students see and that contradict the problem's own data
These sentences appear to exist so that the claim checker has math to verify.
- `eliminate-example.001` step 2 says "A cone of radius 3 and height 6 holds 18π". In this tank the water at depth 6 has radius 2, as step 3 says. This is the skill's worked example.
- `eliminate-cone-tank.t02` step 1 has the same sentence. The radius at h = 6 is 6a/b, which equals 3 in only 3 of 36 instances.
- `relate-example.001` step 1 says "For r = 3 that is 9π". The 3 is the problem's rate (3 cm/s), and the radius at the instant is 10. This mixes up a rate and a value, the confusion this section exists to prevent.
- `eliminate-cylinder-sphere.001` step 1 says "For r = 3 and h = 4 it holds 36π". That cylinder is not inscribed in the radius-5 sphere (3² + 2² = 13 ≠ 25).
- `eliminate-cylinder-cone.t03` step 1 uses the same r = 3 and h = 4, which fits the cone in only 3 of 45 instances.
- `eliminate-trough.001` step 1 says "For w = 4 and h = 3 it is 30", but the trough is 2 m wide and 1.5 m deep.
- Order of steps:
  - `eliminate-example.001` step 3 says "At the instant h = 6 the radius is 2".
  - `translate-tank-leak.001` step 1 says "r = 1.5 and h = 3".
  - Both state the radius before the similar-triangles step derives it.

**Fix:** delete these sentences, or replace them with values that satisfy the card's own constraint, as `relate-cone-water.001` does ("h = 16 gives r = 5"), with a matching `check:`. Move values at the instant after the similar-triangles step.

### 5. Templates whose parameter changes nothing the student does
spec PACK-18 says the build drops "the same problem in disguise", but these were kept:
- `select-ladder.t01` (21 instances), `select-kite.t01` (31) and `select-trough.t01` (48) each have one option set and one marked option across all instances. The number in the stem plays no part.
- `time-ladder.t01` (21) has the same correct option in every instance; only one distractor's number changes.
- In `time-ellipse.t01`, c never enters the answer: 124 instances give 4 distinct keys.
- In `instant-values.t02`, a never enters the answer: 22 instances give 5 distinct keys.

**Effect:**
- The 121 choice instances can be answered from memory after one exposure.
- The section's 40% template share (29 of 72) counts these templates.

**Fix:**
- Make the four choice templates static cards (25 of 72, or 35%, would be templates) and add real variety elsewhere.
- Give `time-ellipse.t01` a parameter that enters the answer, for example m x² + k y² = c.
- Make `instant-values.t02` ask for something that depends on a.

### 6. `relate` is tagged inconsistently, and never in the section's whole exam problems
- Four whole problems write the relation in a step tagged with a geometry component, and none lists `relate` in `uses`:
  - `translate-shadow.001` step 1 [similar-triangles];
  - `translate-ships.t01` step 1 [pythagorean]: "so s² = x² + y²";
  - `translate-tank-leak.001` step 1 [area-volume-formulas];
  - `translate-slick.001` step 1 [area-volume-formulas].
- The worked examples tag the same move as a geometry step plus a [relate] step: `translate-example.001`, `instant-example.001`, `eliminate-example.001` and `time-example.001`.
- The `relate` note in skills.md shows the move as one `relate` step.

**Fix:** tag the relation step `relate` in these four cards and add it to their `uses`. Settle one convention for geometry plus relate.

### 7. `wrong:` feedback that names the wrong error or the wrong step
- **`relate-bowl.t01`, wrong sqrt(2Rh + h²) @2.**
  - The feedback says "the middle term of (R - h)^2 is -2Rh".
  - That value comes from the sign of h²: R² − (R² − 2Rh − h²), or a minus sign not distributed. A middle-term error gives R² − (R² + 2Rh + h²) = −2Rh − h².
  - **Fix:** "the minus sign in front of the bracket also changes the sign of h²: R² − (R − h)² = 2Rh − h²".
- **`instant-rect.001`, wrong -7/5 @2.**
  - The feedback says "The width is the shorter side", but the question has no width; it says x < y.
  - **Fix:** "The question says x < y, so x = 6 and y = 8."
- **`time-elevation.001`, wrong (xp − hq)/(x² + h²)² @5.**
  - Dividing by the correct sec²θ cannot produce the square. The value comes from sec²θ = (x² + h²)²/x², that is, forgetting the root in sec θ, which happens in the identity step.
  - **Fix:** point at @4, with feedback that sec²θ = 1 + tan²θ = (x² + h²)/x².
- **`eliminate-funnel.001`, wrong 9 − h³/48 @3.**
  - This is a mixed error: r = h for the water, but the full funnel still holds 144π.
  - The realistic error, reading "12 cm across" as the radius, gives r = h and a full volume of 576π, so 36 − h³/48. That error happens in the similar-triangles step (@2).
  - **Fix:** use 36 − h³/48 @2, with feedback about diameter and radius.
- **`time-resistors.001`, wrong u/x² + w/y² @3.**
  - The first sentence of the feedback ("its rate is minus the rate of R over R squared") describes an error in step 2.
  - **Fix:** point at @2.
- **`instant-curve.t03`, wrong c√(1+4q²) @3.**
  - Answering the speed along the wire is an error about the wanted quantity, not a substitution error.
  - **Fix:** point at @0.

### 8. `instant-solve.t03`: the sign convention is not stated, and a correct magnitude is diagnosed as a sign error
- The question asks "How fast is her y-coordinate changing", and the key is negative.
- It is the only numeric card with a negative key under "how fast" wording. `translate-speed.t01` uses "At what speed" for a magnitude.
- At k = 2, m = 3, n = 1, u = 1, the input "4/3" is matched to the wrong line "the two rates have opposite signs" (grader probe).
- **Fix:** ask "What is dy/dt at that instant?", or add "(negative if y is decreasing)".

### 9. `instant-kite.t01` step 2 covers two components
- The step reads "[alg.solve.linear] Solve: substitute s = S, x = X and dx/dt = w into the differentiated equation, so … ds/dt = …".
- The substitution is the card's own skill, so a substitution slip is routed to algebra.
- **Fix:** split the step into [values-at-instant] Substitute and [alg.solve.linear] Solve, as `instant-solve.t03` does.

### 10. `translate-wanted.001`: the correct option is the only one with a reason
- The correct option adds "since x is increasing … which will be negative since y is decreasing" and is about twice as long as the others, which gives it away.
- **Fix:** give every option a reason, or none.

### 11. `translate-leaky-balloon.001` wording
- The balloon is "slightly porous", but at r = 5 the leak is 10π ≈ 31 cm³/s of the pump's 100 cm³/s. The balloon can never grow past r ≈ 8.9 cm, where the leak equals the pump.
- Step 6's direct check, "with V = 500π/3 + (100 − 10π)t", states a linear V(t) that the problem contradicts, since the net rate changes with r.
- **Fix:**
  - Drop "slightly", or use 0.01 cm³/s per cm². The key then becomes 1/π − 1/100; recompute the wrong answers.
  - Word the check as `instant-leak.001` does: "at this instant V is … and grows at …".

### 12. `select-funnel.001`: the trig-ratio distractor is also a valid relation
- For a cone of fixed shape, r = h·tan α with tan α = 6/12 is the same equation as similar triangles. A student who picks "A trig ratio" is marked wrong.
- The same applies to the multi-select cards `select-cone-tank.001` and `select-trough.t01`.
- **Fix:** state that no angle is given, or reword the option.

### 13. Rendering and units (cosmetic)
- `translate-ships.t01` steps 4–5 print the final rate unreduced in 16 of 81 instances (u = 12, w = 9: "ds/dt = 225/25 km/h").
- `eliminate-which.t01` (in its correct option), `eliminate-cone-tank.t02` and `eliminate-cylinder-cone.t03` print a/b unreduced (4/8, 6/12, 3/9, …).
- `translate-speed.t01` at k = 10 prints "1 meters per minute".
- **Fix:** insert the values with `[[tex(...)]]`.

### 14. Setups with no change over time, or an odd physical premise
- `relate-cylinder.001` and `relate-rectangle.t01` never say that the figure changes; they are optimization constraints. Yet their step 0 asserts that the quantities change, and the skill is the equation between changing quantities.
- `select-box.001`: a "closed box" squeezed so that its volume never changes is physically odd.
- **Fix:** add "as the cylinder changes shape …" to the questions; make the box "a block of clay with a square base".

## Checked and found correct
- **Official check:** `mepack.py check packs/calc1 --katex …` ran in the worktree in 4 min 9 s and reported OK.
  - 1895 cards, 162 skills, 0 errors.
  - 60 warnings, all "no ### Hints" in this file.
  - Wrong-answer coverage: 67/67 pack-wide (41/41 in this file).
  - 0 steps with math unverified; the KaTeX strict render check passed.
- **Built cards:** 1209 = 6 examples + 43 static problems + 1160 instances of 29 templates.
  - Every template is fully enumerated (no sampling), so every parameter extreme is included.
  - Instance counts match the notes, and each skill has tiers 3/4/3/2.
- **Static cards:** 31/31 auto-graded keys and 63/63 wrong values match my independent models (explicit motion in t, geometry, cross-section integration, SymPy implicit differentiation). The 5 worked-example results match too.
- **Templates:** for the 21 auto-graded templates, all 933 instance keys and 1986 wrong values match.
  - No wrong value equals its key, and no two wrong values coincide.
  - One template has near-equal values (defect 1).
- **Choice cards:** 227/227 choice-template instances and 12/12 static choice cards mark the right option or options.
- **Component rule:** 78/78 card families pass in both directions.
  - Every step tag is the skill or in `uses`, and every `uses` entry tags a step.
  - Steps are numbered contiguously, every `@step` is a real step, and step 0 carries the card's skill.
- **Signs, units and decimals:** every question and every `### Answer` states its signs and units. The decimals in `### Answer` match the exact keys.
- **Rendering:** a scan of all 1209 built cards found no unsubstituted `[[ ]]`, and no "+ -", "1x", `^{1}`, raw `*` or `sqrt(` inside math.
