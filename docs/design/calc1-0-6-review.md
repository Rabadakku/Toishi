# Review: packs/calc1/0-6-geometry.cards.md (section 0.6 Geometry)

Worktree: /home/claude/mastery-engine/.claude/worktrees/agent-a6e5ca1aad5115bd2. No file in the worktree was edited.

Reference note: the worktree's `docs/prompts/write-calc1-section.md` has no flashcard rules. The main checkout's copy (`/home/claude/mastery-engine/docs/prompts/write-calc1-section.md`, lines 39-43) has them, and I reviewed against those:
- a formula that is an expression gets a typed answer;
- a self-graded definition lists its idea units, one per line;
- the front gives the situation and the back the fact;
- every fact is paired with problems that use it.

Evidence scripts and outputs are in scratchpad/rev/:
- `truth.py`: independent keys and wrong values;
- `labels.py` and `labels.txt`: which error each wrong value comes from;
- `exact.py`: exactness scan;
- `gradetest.py`, `gradetest2.py`, `gradetest3.py`: runs of the real grader;
- `lint.py`: tags and tiers;
- `fc.py` and `fcmath.py`: flashcards;
- `choice.py`: choice and true/false keys;
- `dump.py` and `cards.json`: all 2905 built cards.

## Defects, most serious first

1. **"Give an exact answer" is not enforced on 27 cards: 15 static and 12 templates (573 instances).** These are `number` (and one `list`) answers with irrational keys, the question says exact, and there is no `exact: yes`.
   - Cards:
     - static `number`: area.002, area.004, perim.001, vol.001, surf.002, surf.003, arc.004, special.001, special.003, special.005, dist.003, comp.003, comp.005, pyth.005;
     - static `list`: special.002;
     - templates: perim.t02, vol.t01, vol.t02, surf.t01, surf.t02, arc.t01, arc.t02, special.t01, special.t02, special.t03, lawcos.t01, comp.t02.
   - Evidence from the real grader (`core.grader.grade`), all graded **correct**:
     - "153.9" for 49π (area.002);
     - "1.2" and "1.19" for 2√26 − 9 ≈ 1.198 (pyth.005);
     - "10.4" for 6√3 (special.003);
     - "6.93, 8" for the list 4√3, 8 (special.002);
     - "3.6" for √13 (lawcos.t01).
   - With `exact: yes` the grader rejects "153.94" and "6.93, 8" with "Right value, but give an exact answer (no decimals)" and still accepts 49pi and 4sqrt(3), 8.
   - The writer's notes list this as an uncertainty, but the format already provides the option (card-format.md, checker options).
   - Fix: add `exact: yes` to those 27 cards.

2. **Correct answers are graded wrong when the question's angle is in degrees.** No card sets `angles: degrees` (card-format checklist item 14).
   - Affected: area.005, special.003, special.005, lawcos.001, lawcos.004, lawcos.005, lawcos.t01, lawcos.t02 and lawcos.t03 (6 static cards and 228 template instances).
   - Evidence, graded **incorrect** with an empty message:
     - lawcos.t02 (3 and 4 km/h, 60°): "sqrt((3t)^2 + (4t)^2 - 2(3t)(4t)cos(60))";
     - area.005: "1/2*8*12*sin(150)";
     - lawcos.t01 (3, 4): "sqrt(9 + 16 - 24cos(60))".
   - With `angles: degrees` the first two grade correct.
   - Fix: add `angles: degrees` to these nine. The checklist also asks for it on the degree-only angle.* cards, where it changes only the note shown.

3. **Two different `wrong:` entries have the same value in 14 instances of 5 templates.** The grader takes the first match in listed order (core/grader/pipeline.py:105-110), so the other feedback and its `@step` never show.
   - arc.t03, f = 1/2 (R = 12, 24, 36): 2Rf = R. A student who answers the sheet radius is told "divide by 2π, not π" and routed to step 2 (perimeter-circumference), not step 1 (arc-sector).
   - comp.t02, r = h (4 instances): πr²h = ⅓πr²h + ⅔πr³. A student who used the cone factor (step 1, volume-solids) is told to add the roof (step 3, composite-figures).
   - angle.t02 at a = 45: a = 90 − a.
   - angle.t03 at (p, q) = (35, 15), (36, 18), (38, 24), (39, 27), (40, 30): 90 + q − p = 2p.
   - sim.t02 at R = 3, H = 9: Hh/R = Rh.
   - Fix:
     - arc.t03: drop f = 1/2 from the choice, or `require: f != 1/2`;
     - comp.t02: `require: h != r`;
     - angle.t02: `require: a != 45`;
     - angle.t03: `require: 3*p != 90 + q`;
     - sim.t02: `require: H != R^2`.

4. **comp.003: the two `@step`s are swapped, so each miss goes to the other skill.**
   - Step 1 [perimeter-circumference] computes both arcs (60π). Step 2 [composite-figures] chooses the straight sides (200).
   - `200 + 30*pi` (only one arc) is tagged @2, but the error is in step 1.
   - `320 + 60*pi` (counts the two 60 m ends) is tagged @1, but it is the shared-edge error this component exists to catch, in step 2.
   - Fix: give `200 + 30*pi` @1 and `320 + 60*pi` @2.

5. **Component graph: the split is not connected to calculus, and one new component overlaps an old one** (task item 7).
   - (a) Not connected to calculus:
     - `calc1.optimize.objective` (skills.md:1282) and `calc1.defint.geometry` (:1516) still require only the umbrella `pre.geometry.area-volume-formulas`, and `calc1.select.related-rates-relation` (:1001) still chooses it.
     - The umbrella has no cards and is a parent of area-plane-figures, volume-solids and surface-area-solids.
     - No calc1 skill references any of the 10 new IDs (grep of skills.md).
     - So a miss on a cone or sphere formula inside an optimization problem still routes to a component with no pool, and those two skills stay blocked by the problem-less-prerequisite rule (component map, open question 1).
   - (b) Overlap: the original `pre.geometry.pythagorean` is named "Relate lengths with the Pythagorean theorem or the distance formula" (skills.md:363), and `distance-formula` now owns that same demand. That is two names for one move.
   - Among the 10 new components I found no parent/child pair. Both points are in the writer's follow-up list but are unresolved.
   - Fix:
     - retarget the three skills to the specific components (or `encompasses`) and retire the umbrella from their edges;
     - rename `pythagorean` to "Relate lengths with the Pythagorean theorem" (names are not permanent).

6. **vol.005 copies commercial-textbook wording** (task item 8).
   - The card: "Sand falls from a conveyor belt and forms a pile in the shape of a cone whose height is always twice its radius."
   - Thomas' Calculus (14e §3.10): "Sand falls from a conveyor belt at the rate of 10 m³/min onto the top of a conical pile…"
   - Stewart (§3.9): "…forms a pile in the shape of a cone whose base diameter and height are always equal."
   - I could not open either book. Both sentences circulate under those attributions (vaia.com Thomas 14e ch. 3 problem pages, Dartmouth Math 3 lecture notes, physicsforums threads).
   - The allowed source has the scenario in other words: OpenStax 4.1 Exercise 35, "Gravel is being unloaded from a truck and falls into a pile shaped like a cone".
   - Fix: rewrite in original words, for example "A pile of sand has the shape of a cone whose height is twice the radius of its base". Or adapt OpenStax 4.1 Ex. 35 with a source line and `modified: yes`.

7. **Two wrong values don't come from the error their feedback names.**
   - angle.002, `50`:
     - The feedback says "the three angles add up to 180, not 90", but a 90° sum gives (90 − 40)/2 = 25.
     - 50 is 90 − 40, the value from assuming a right angle.
     - Fix: make the value 25, or keep 50 and say "the triangle has no right angle; the base angles are (180 − 40)/2".
   - comp.t03, `P*x/2 - x^2/2`:
     - The feedback says "treats the window as a plain rectangle", but a plain rectangle (2h + 2x = P, A = xh) gives Px/2 − x².
     - The stored value comes from dropping the arc from the perimeter and the semicircle from the area while still leaving the top edge out. That is two errors.
     - Fix: use `P*x/2 - x^2`, or reword the feedback to "leaves the semicircle out of both the perimeter and the area".

8. **Distance = speed × time work is tagged as geometry, so rate errors are diagnosed as geometry errors.**
   - pyth.t03: step 2 ("running takes x/r seconds…") is tagged pre.geometry.pythagorean, and `x*r + sqrt(...)*s` ("Time is distance divided by speed") @2 routes there.
   - lawcos.005: `7` ("paddling for 2 hours") @3 routes to law-of-cosines.
   - lawcos.t02: the missing-t² wrong @2 routes to law-of-cosines.
   - The notes' "Components the map lacks" section does not mention this.
   - Fix: report the missing rate component. Until it exists, drop those wrong lines or move the rate work to a step whose wrong answers are not geometry diagnoses.

9. **The cosine value is handled inconsistently, and one wrong value has two sources.**
   - lawcos.t01, lawcos.001 and lawcos.004 (and lawcos-example) evaluate cos 60° = ½ inside the law-of-cosines step, with no trig.values.exact in `uses`.
   - lawcos.t02, lawcos.t03, lawcos.005 and area.005 give the cosine its own trig.values.exact step.
   - A student who uses cos 60° = √3/2 on the first group is routed to law-of-cosines.
   - lawcos.005 `sqrt(76)` @1: the same value comes from using 60° at step 1 (angle-relationships) or from cos 120° = +½ at step 2 (trig.values.exact), and the feedback names both.
   - Fix: add a cosine step and `uses: trig.values.exact` to the first group (or document that tier 1 folds it). Point √76 at one cause.

10. **fc-angle.006 states a wrong inference.**
    - The back says: "Conversely, equal angles lie opposite equal sides, so an equilateral triangle has three angles of 60°."
    - The 60° fact follows from the forward statement (equal sides give equal opposite angles) plus the angle sum, not from the converse.
    - That line holds two idea units, making five on the card against the 2-4 rule.
    - Fix: put the converse on its own line, and give "an equilateral triangle has three 60° angles" as a consequence of the base-angle line, not of the converse. Drop one line to stay at four.

11. **Other `@step`s point at the wrong step.**
    - Different skill, so the routing is wrong:
      - surf.t03 `2*pi*r^2 + 200*n` @2 (alg.solve.linear): the feedback blames the base area, which is step 1 (volume-solids).
      - perim.004 `36 - x` and perim.t03 `x*(2*p - x)` @2 (alg.solve.linear): the usual source is writing the perimeter as x + y = P, step 1 (perimeter-circumference).
      - arc.t03 `R` @1: answering the sheet radius means skipping the base-circle step, step 2.
    - Same skill, so only the preselected step is wrong:
      - vol.t02 `2*pi*r*h` @1: the formula error is in step 2 (Volume), not step 1 (Radius).
      - angle.t03 `2*p` @3: the missed halving is step 2 (Bisector).

12. **Five flashcard facts have no problem that uses them** (brief rule: every fact is paired with problems).
    - fc-angle.002: complementary angles.
    - fc-angle.005: alternate interior and corresponding angles. Only same-side interior is used, in angle.t02.
    - fc-angle.008: angle of elevation or depression.
    - fc-sim.002: area and volume scaling by k², k³.
    - fc-special.004: area of an equilateral triangle. special.t03, comp.001 and the example use only its height or perimeter.
    - Evidence: a regex search of every problem and example.
    - Fix: add a short problem for each, or drop the card.

13. **Practice instances repeat worked examples or static cards word for word.**
    - surf.t02 (r = 3, h = 10) is surf-example.001's can (78π).
    - vol.t01 (r = 4, h = 9) is vol-example.001's cone (48π).
    - lawcos.t01 (5, 8) and (8, 5) are lawcos-example.001's trails (7). lawcos.t01 (3, 8) and (8, 3) are lawcos.001 and lawcos.002's triangle.
    - angle.002 is step 1 of angle-example.001 (vertex 40°, base angles 70°).
    - Fix: add `require` exclusions, and change angle.002's numbers.

14. **Tiers don't match the anchors** (tier 1 = "one step, one skill").
    - Nine tier-2 problems are one step with one skill by their own solutions: angle.t02, area.003, area.004, dist.t02, pyth.t02, sim.t02, special.t02, surf.004, surf.t02. surf.t02 is as hard as surf.t01, which is tier 1.
    - angle.005 and special.t03 (tier 3) are two-step routine homework: tier 2.

15. **Some tags don't fit their component's definition.**
    - fc-special.004 and recall-special.004 (equilateral area, ½·s·(√3/2)s) are tagged special-right-triangles ("sides of a 45-45-90 or 30-60-90 triangle"). The area step is area-plane-figures work.
    - recall-special.001 and .002 derive the ratio with the Pythagorean theorem under the special tag, which blurs the split from `pythagorean`.
    - comp-example.001 steps 1-2 and comp.002 compute the semicircle's area and arc under composite-figures. This contradicts the stated rule that the piece formulas carry their own components, and it muddies the data meant to decide whether this provisional component merges.
    - In skills.md, composite-figures requires volume-solids and surface-area-solids, so plane composites (window, track) cannot be introduced before solids.
    - arc-sector does not require trig.angles.radians, although its formulas need radians.

16. **Several self-graded backs break "one idea unit per line".**
    - fc-angle.001: one sentence is split across two bullets, and the first bullet only restates the front.
    - fc-angle.005, line 1: two facts.
    - fc-angle.008, line 3: three facts (the definition of depression, the equality, the reason).
    - fc-comp.002, line 3: two facts.
    - fc-pyth.006, line 2: two facts, and x and y are undefined.
    - fc-dist.002: the formula, then a two-fact line, then a two-fact calculus line.

17. **Duplicate flashcards.** fc-pyth.004 (diagonal of a rectangle, √(l² + w²)) asks fc-pyth.001's fact (hypotenuse, √(a² + b²)) again. Their twins recall-pyth.002 and recall-pyth.001 have the same answer with renamed variables. fc-pyth.004 and fc-special.001 also both carry the s√2 square-diagonal fact. Fix: merge, or make fc-pyth.004 a problem.

18. **comp.t01: the 1% decimal tolerance accepts the forgot-to-subtract answer.**
    - With a 2 × 2 pond: (a, b) = (23, 19) gives key 433 against a·b = 437, and (28, 16) gives 444 against 448.
    - The grader accepts "437.0" and "436.9" for 433. The integer "437" is rejected.
    - Fix: `exact: yes`, or `require: c*d >= a*b/50`.

19. **Minor wording and conditions.**
    - angle.001: "Which of these angle measures *also* appear" invites leaving out the given 65°, which is a keyed answer. Fix: "Which of these measures are among the four angles?"
    - fc-surf.002, fc-surf.003, recall-surf.002 and recall-surf.003 say "cylinder" without "right circular". 2πrh needs a right cylinder, and fc-vol.002 says it.
    - fc-sim.004 omits H > h; recall-sim.002 has it.
    - fc-comp.001 says a track is split into "a rectangle and a half circle"; it has two.
    - comp.005: `392 + 28*pi` (circles added) and `392 + 20*pi` (circles not removed) have identical feedback.
    - recall-pyth.001-.003 have no `domain` for lengths (checklist item 4), so a√(1 + (b/a)²) grades incorrect (tested).
    - pyth.t01: two of six instances read "8 m wide and 6 m long" and "15 m wide and 8 m long".
    - fc-sim.002 (k², k³) is an expression fact with no typed twin.
    - perim.005 follows OpenStax 4.7 Ex. 335's wording (a wire cut in two, a circle of radius r and a square) and could carry that source line. This is not a commercial-text problem.

## What I checked and found correct

- **Official check.** `mepack.py check packs/calc1 --katex …` was run in the background and reported **OK**.
  - 3591 cards, 172 skills.
  - Tier 2+ wrong-line coverage 87/87, 0 wrong answers without `@step`.
  - 9743 answers graded by both engines, 2043 template operations agree with mpmath (42 could not be recomputed).
  - 6726 step checks hold, 3518 final lines match the key, 0 steps unverified.
  - Warnings: only the expected 132 "no ### Hints". The pool report for 0.6 lists only the umbrella (no cards) and angle-relationships (no confusable).
- **Build counts.** 2905 cards in this file: 12 examples, 52 flashcards, 61 static application problems, 35 recall problems, and 2745 instances from 36 templates. All match the notes.
- **Keys recomputed independently with SymPy** from each question's geometry, not from the stored answer: 90 static math keys (55 application, 35 recall), the 6 choice and true/false keys, and **every** one of the 2745 template instances, which covers all parameter extremes. 0 mismatches.
- **Wrong answers.**
  - 272 wrong entries were mapped to a named error.
  - All 6194 instance × wrong pairs were checked: 0 equal the key, 14 collide with each other (item 3), and 2 fall within 1% of the key (item 18).
  - All values are produced by some single error except the two in item 7. `@step` problems are listed in items 4 and 11.
- **Solutions.** 349 steps in 196 card definitions. Tags agree with `skill` and `uses` in both directions on every problem and example: 0 stray tags, 0 unused `uses`, 0 duplicates, every `@step` exists. The arithmetic in all 12 worked examples is right.
- **Flashcards.**
  - 35 formulas and identities on the backs verified with SymPy, all correct (cone, pyramid and sphere by slicing; the ellipse area integral; cone lateral area two ways; the triples; the shadow and cone-water relations; and others).
  - Directions are situation → fact, and no front gives away its back.
  - Typed twins exist for the 35 formula cards as the notes state.
- **Rendering.** Every built question, step and feedback line was scanned for template glitches (a coefficient of 1, doubled signs, a power of 1, a fraction over 1, leftover brackets, long decimals, "1 meters"): none beyond intentional "(y − 0)" and "1 m/s".
- **Expression answers are exact.** The grader rejects 3.14r², 0.333πr²h and 0.866s.
- **Units and wording.** Units are stated and consistent, and all quantities are given, except the items above.
- **Provenance.** No card copies a commercial textbook except vol.005. The other optimization and related-rates scenarios match OpenStax 4.1 and 4.7 exercises with new numbers and wording.
