# Calculus I section 0.6: Geometry

Pack `calc1` · file `packs/calc1/0-6-geometry.cards.md` · deck
`Calculus I::0 Precalculus Skills::0.6 Geometry`

## What this is

The precalculus geometry section of the Calculus I pack. Students forget geometry definitions and
formulas often, and related rates and optimization depend on them, so the section is built to make
each fact recallable on demand: one flashcard per definition or formula, a typed-answer twin for
every formula card whose answer is an expression, and application problems that use each fact the
way a related-rates or optimization setup does (a short computation, or the setup step that writes
a quantity in one variable).

- **Size:** 12 worked examples, 97 application problems, 35 typed recall problems and 52
  flashcards: 196 card definitions. The 97 application problems are 61 static and 36 templates
  that expand to 2745 instances, so the section builds to 2905 cards.
- **Components:** the 0.6 block of `packs/calc1/skills.md` grew from 3 to 13 components. The ten
  additions and the reason for each are below. The only other files changed are
  `docs/design/calc1-component-map.md` (a new section on the expanded block, and the counts it
  quotes) and this note.
- **Final build:** `content-tools/mepack.py check packs/calc1 --katex <KaTeX>` reports `OK`; the
  summary is under "Final check".
- **Not done:** nothing is merged. The three skills that point at the umbrella component
  `pre.geometry.area-volume-formulas` are not retargeted (see the follow-ups in the component map).

## The ten components added to `skills.md`

The three original skills keep their IDs and fields: `pre.geometry.area-volume-formulas`,
`.similar-triangles` and `.pythagorean`. The original `area-volume-formulas` bundled at least eight
separate recalls (area of a circle, volume of a cone, of a cylinder, of a box, of a sphere, surface
areas) under one tag, so it could not tell a student who forgot the cone from one who forgot the
sphere. A step that recalls a formula now tags the specific component, and no 0.6 card tags the
umbrella. Prefix `pre.geometry.` is left off below.

| Component | The one thing | Requires | Confusable | Why it is its own component |
|---|---|---|---|---|
| `area-plane-figures` | area of a triangle, parallelogram, trapezoid, circle, ellipse | | `perimeter-circumference` | Knowing \(\pi r^2\) does not give the trapezoid or the triangle with an angle. Every volume and surface step needs an area first. |
| `perimeter-circumference` | perimeter of a polygon, circumference of a circle | | `area-plane-figures` | A fence constraint (perimeter) and the quantity maximized (area) are the pair students swap, and the two steps fail separately. |
| `volume-solids` | volume of a box or prism, cylinder, cone, pyramid, sphere | `area-plane-figures` | `surface-area-solids` | The factors \(\frac{1}{3}\) and \(\frac{4}{3}\) are the facts students misremember. A volume is a base area times a height. |
| `surface-area-solids` | surface area of a box, cylinder, cone, sphere | `area-plane-figures`, `perimeter-circumference` | `volume-solids` | The ends are areas and the side is a perimeter times a height. It is known or not known apart from volume, and it is the usual "material" objective. |
| `arc-sector` | arc length \(r\theta\) and sector area \(\frac{1}{2}r^2\theta\), \(\theta\) in radians | `area-plane-figures`, `perimeter-circumference` | `perimeter-circumference` | The formulas hold only in radians and fail apart from \(\pi r^2\) and \(2\pi r\). A changing angle gives a related-rates problem. |
| `angle-relationships` | an unknown angle from triangle-sum, complementary, supplementary, vertical, parallel-line and isosceles facts | | | The angle that goes into a trig ratio or the law of cosines comes from these facts, and no length formula tests them. No prerequisite, and no genuine confusable. |
| `special-right-triangles` | the sides of a 45-45-90 or 30-60-90 triangle from one side | `pythagorean` | `pythagorean` | The \(\sqrt{2}\) and \(\sqrt{3}\) ratios are memorized facts: a student can know the theorem and not recall them. They give the exact trig values and the height of an equilateral triangle. |
| `distance-formula` | the distance between two points, and the equation of a circle | `pythagorean` | `pythagorean` | Going from coordinates to a length is a different recall from using the theorem on a drawn triangle. The circle's equation is the same fact: the squared distance from the center. |
| `law-of-cosines` | the third side from two sides and the angle between them | `pythagorean` | `pythagorean` | It is the tool for two objects moving along lines at an angle. The usual error is the sign or the missing cosine term, which the theorem does not test. |
| `composite-figures` | build an area, perimeter, volume or surface area from pieces: add, subtract, drop a shared edge | `volume-solids`, `surface-area-solids` | `perimeter-circumference` | A student can know every piece formula and still count the shared edge of a Norman window. *Provisional*: merge it if its misses always coincide with the pieces' misses. |

Tagging rules used in the cards:

- Each solution step carries exactly one component. A step that recalls a formula carries the
  specific one, and the others go in `uses`.
- Finding a missing side with the Pythagorean theorem stays `pythagorean`.
- Putting a figure together from pieces, including which edges count, is `composite-figures`; the
  formulas for the pieces are the other components.
- The radian arc and sector formulas are `arc-sector`; the radian measure itself is
  `trig.angles.radians`.

Seven confusable pairs were added (60 in the pack now, from 53). The map doc has the table and the
status of each split (textbook for nine, provisional for `composite-figures`).

## Cards by component and tier

The application problems are tiers 1 to 3, as this section's brief asked, about 8 per component:
3 / 3 / 2, except `similar-triangles` with 3 / 3 / 3. The typed recall problems are all tier 1 and
are counted apart from the application problems.

| Component | Example | Tier 1 | Tier 2 | Tier 3 | Problems | Templates | Flashcards | Recall |
|---|---|---|---|---|---|---|---|---|
| `area-plane-figures` | 1 | 3 | 3 | 2 | 8 | 3 | 6 | 6 |
| `perimeter-circumference` | 1 | 3 | 3 | 2 | 8 | 3 | 2 | 2 |
| `volume-solids` | 1 | 3 | 3 | 2 | 8 | 3 | 6 | 6 |
| `surface-area-solids` | 1 | 3 | 3 | 2 | 8 | 3 | 5 | 5 |
| `arc-sector` | 1 | 3 | 3 | 2 | 8 | 3 | 2 | 2 |
| `angle-relationships` | 1 | 3 | 3 | 2 | 8 | 3 | 8 | 1 |
| `special-right-triangles` | 1 | 3 | 3 | 2 | 8 | 3 | 4 | 4 |
| `distance-formula` | 1 | 3 | 3 | 2 | 8 | 3 | 2 | 1 |
| `law-of-cosines` | 1 | 3 | 3 | 2 | 8 | 3 | 2 | 1 |
| `composite-figures` | 1 | 3 | 3 | 2 | 8 | 3 | 5 | 2 |
| `similar-triangles` | 1 | 3 | 3 | 3 | 9 | 3 | 4 | 2 |
| `pythagorean` | 1 | 3 | 3 | 2 | 8 | 3 | 6 | 3 |
| Total | 12 | 36 | 36 | 25 | 97 | 36 | 52 | 35 |

`area-volume-formulas` has no card, by design. The 61 static problems are written where the wording
needs care (setups, choices); the 36 templates are 37% of the application problems.

Template instance counts (each template is `calc1.0-6.<name>.t01` to `.t03`, tiers 1 to 3 in that
order):

| Component | `.t01` | `.t02` | `.t03` |
|---|---|---|---|
| `area` | 200 | 132 | 12 |
| `perim` | 200 | 52 | 33 |
| `vol` | 50 | 70 | 13 |
| `surf` | 13 | 84 | 11 |
| `arc` | 40 | 80 | 12 |
| `angle` | 200 | 51 | 200 |
| `special` | 11 | 11 | 12 |
| `dist` | 200 | 144 | 24 |
| `lawcos` | 100 | 98 | 30 |
| `comp` | 200 | 50 | 31 |
| `sim` | 72 | 40 | 40 |
| `pyth` | 6 | 23 | 200 |

That is 2745 instances from 36 templates (smallest 6, largest 200, the cap). `pyth.t01` has 6
because it draws Pythagorean triples so that the answer is a whole number. Every component has a
tier 3 template with at least 9 instances and a static tier 3 problem, as the pool rule asks.

Answer types of the 97 application problems: number 65, expression 24, choice 5, list 1, set 1,
true/false 1. Geometry computations are numeric or are a formula in one variable by nature, so the
mix leans that way. Every recall problem is an expression. Every problem has `wrong:` lines that
point at a step (`@n`), except five tier 1 choice cards and one tier 1 true/false card, which the
builder exempts. Every problem has numbered, tagged steps; none has hints.

## Flashcards and typed recall problems

**Flashcard format.** Each front asks for exactly one thing, named the way a student needs it
mid-problem, for example "Volume of a right circular cone with base radius \(r\) and vertical
height \(h\)". The direction is name or situation on the front, formula or fact on the back.

- A formula card's back is the display formula, then every variable defined (including what a
  "height" means when it matters), then one "In calculus:" line saying where it is used in related
  rates or optimization.
- A card for a definition or theorem has a back of 2 to 4 short idea units, one per line, the last
  one being the calculus use.

**Typed recall problems.** The card format forbids an answer on a flashcard (`kind: flashcard`
cards "are not graded", `core/cards/cardfile.py`), so a flashcard is always self-graded. To let the
app grade the recall of every formula that is an expression, each such flashcard has a twin: a tier
1 `expression` problem whose question asks for the same formula, with a single tagged step and two
or three `wrong:` lines for the usual slips (a missing \(\frac{1}{3}\), the volume for the surface
area). The twins are `calc1.0-6.recall-<name>.<nnn>`, in their own block at the end of the file,
so deleting that block removes them cleanly.

| Component | Flashcards with a typed twin | Self-graded only |
|---|---|---|
| `area-plane-figures` | `fc-area.001` to `.006` | none |
| `perimeter-circumference` | `fc-perim.001`, `.002` | none |
| `volume-solids` | `fc-vol.001` to `.006` | none |
| `surface-area-solids` | `fc-surf.001` to `.005` | none |
| `arc-sector` | `fc-arc.001`, `.002` | none |
| `angle-relationships` | `fc-angle.007` (twin `recall-angle.001`) | `fc-angle.001` to `.006`, `.008` |
| `special-right-triangles` | `fc-special.001` to `.004` | none |
| `distance-formula` | `fc-dist.001` | `fc-dist.002` (circle equation) |
| `law-of-cosines` | `fc-cos.001` | `fc-cos.002` |
| `composite-figures` | `fc-comp.004`, `.005` (twins `recall-comp.001`, `.002`) | `fc-comp.001` to `.003` |
| `similar-triangles` | `fc-sim.003`, `.004` (twins `recall-sim.001`, `.002`) | `fc-sim.001`, `.002` |
| `pythagorean` | `fc-pyth.001`, `.004`, `.005` (twins `recall-pyth.001` to `.003`) | `fc-pyth.002`, `.003`, `.006` |

A twin has its flashcard's number (`fc-area.003` and `recall-area.003`) except where the table
says so. That is 35 flashcards with a typed twin and 17 that are self-graded only. Sixteen of the
17 are definitions and theorems stated in words (complementary and supplementary angles, vertical
and parallel-line angles, isosceles angles, angle of elevation, the converse of the theorem,
Pythagorean triples, inscribed polygons, similarity by two angles, area and volume scaling, which
edges count in a composite figure), which have no single expression as their answer. The 17th is
the circle's equation, which is an equation: an `equation` answer cannot meet the builder's rule
that the last check of a worked solution grades correct against the key.

Each fact is also paired with application problems that use it: tier 1 applies the formula to given
numbers, tier 2 adds a short setup step (a radius from a diameter, the outer radius of a walkway),
and tier 3 writes the area, volume or length as a function of one variable, as related rates and
optimization do.

## Final check

`UV_PROJECT_ENVIRONMENT=<venv> uv run --no-sync python content-tools/mepack.py check packs/calc1
--katex <KaTeX>` on the final cards file, whole pack (the totals include the 686 cards of section
4.3):

```
pack calc1 0.1.0: 3591 cards, 172 skills
wrong answers: answers of tier 2+ problems with a wrong: line 87/87, wrong answers without @step 0
differential checks (DEV-18): 9743 answers graded by both engines, 2043 template operations agree with mpmath, 42 could not be recomputed
worked solutions (MATH-17): 6726 step checks hold, 3518 final lines match the key, 0 steps with math unverified
kinds: example 15, flashcard 52, problem 3524
OK
```

- **Warnings:** "no ### Hints" is the only one, 132 times: once for each of the 97 application
  problems and 35 recall problems here, because the app shows no hints (the 4.3 problems do have
  them). There are no errors, no "unverified:" steps and no near-duplicate warnings.
- **The 42 operations that could not be recomputed** are in section 4.3 (the pilot note lists
  them). None is in this section, so every template operation here is confirmed by mpmath.
- **Pool report:** for this block it lists only `pre.geometry.area-volume-formulas` (no cards, by
  design) and `pre.geometry.angle-relationships` (no confusable). The other 0.6 components need
  nothing.
- **Time:** a full check takes about 7 to 10 minutes on the shared machine, so I ran each one in
  the background.

Checks I ran outside the builder, because it cannot catch these:

- **Formulas.** Each flashcard and recall formula was re-derived or tested numerically in a separate
  script (48 identities, for example the cone and the sphere, the Norman window perimeter and area,
  the shadow equation, the arc and sector fractions).
- **Keys.** Every application key was recomputed from its story, not from the stored answer: the
  56 static problems that are not choice cards, 40 random draws of each of the 36 templates (1440
  draws), the 5 choice cards and the 35 recall problems with their wrong answers. None disagreed.
- **Rendering.** Every built card was scanned for glitches a template can produce: a coefficient 1
  before a letter, a doubled sign, a zero term, leftover brackets, Python text such as `sqrt(` in
  prose, long decimals, empty parentheses, a fraction over 1, a power of 1, "1 meters", and two
  instances of one template with the same question. It found three things (a fraction over 1 when
  the swim speed is 1 m/s, and `sqrt(` in two wrong-answer notes). Reading three rendered instances
  of every template found two more (an unreduced \(\frac{6}{14}\) in the cone templates, and an
  expression written twice when the long leg of a 30-60-90 triangle is not a multiple of 3). All
  were fixed.
- **Read-through.** I read the cards file once end to end as a student.

## Sources

All 196 cards are original (`source: original` and the license are in the file header; no card has
a per-card source line). The coverage was chosen against the facts in OpenStax Calculus Volume 1
(Review of Pre-Calculus, Formulas from Geometry, and section 4.7), CLP-1 Appendix A, OpenStax
Prealgebra 2e sections 9.3 to 9.6, Intermediate Algebra 2e section 11.1 and Precalculus 2e section
8.2, which `skills.md` lists as the `textbook:` lines of the components. Those books were used only
to decide which facts a student needs. No problem, wording, figure or set of numbers was taken from
them or from any other book.

## Components the map lacks

Not added, as asked:

- The midpoint formula (a coordinate pair, used in symmetry and distance setups).
- The law of sines.
- Circle theorems: a tangent is perpendicular to the radius, and an angle in a semicircle is a right
  angle. The inscribed rectangle is covered only as a fact on `fc-pyth.006`.
- The area of a regular polygon (apothem) and Heron's formula. Neither is needed for the section
  4.1 and 4.7 problems this block supports.

## Uncertainties

- **52 flashcards, not "about 40".** The brief asks for one card per definition or formula a student
  needs and says "about 40". I counted 35 formulas that are an expression and 17 definitions and
  theorems, and merging any of them would put two things on one front. If fewer are wanted, the
  least needed for related rates and optimization are `fc-area.005` (ellipse), `fc-angle.004` and
  `.005` (vertical and parallel-line angles), `fc-pyth.002` and `.003` (converse, triples),
  `fc-cos.002`, `fc-comp.003` and `fc-vol.006`.
- **The typed twins are a workaround.** A flashcard cannot be graded, so the twins repeat the
  flashcard as a tier 1 problem. They count as ordinary tier 1 problems of their component. If the
  format later lets a flashcard carry a typed answer, delete the `recall-*` block.
- **"Give an exact answer" is not enforced.** A `number` answer has a 1% tolerance, so 3.46 is
  accepted for \(2\sqrt{3}\). The expression answers are exact.
- **The three umbrella dependents.** `calc1.optimize.objective`, `calc1.defint.geometry` and
  `calc1.select.related-rates-relation` still point at `area-volume-formulas`, which no card tags.
  Until they are retargeted they inherit the open question about problem-less prerequisites in the
  map.
- **`angle-relationships` has no confusable.** None of its facts is mistaken for another component,
  so I set none; the pool report lists it.
- **Two cards sit on the nearest component.** The angle of elevation (`fc-angle.008`) is on
  `angle-relationships` and inscribed polygons (`fc-pyth.006`) on `pythagorean`; no component fits
  better.
- **Broad originals.** `similar-triangles` covers recognizing similar triangles, setting up the
  proportion and scaling areas and volumes, and `pythagorean` covers a hypotenuse, a leg and the
  diagonals of boxes. They were kept as they were, as asked. `special-right-triangles` keeps both
  triangles and the equilateral height. Split them if learning-curve data show the facts fail
  separately.
- **Tier boundaries are my judgment.** Tier 3 here is the setup step of a related-rates or
  optimization problem, two or three components deep, not a full optimization.
- **The map doc was edited beyond a short section.** The counts it quotes (components, pairs,
  chapter table, the 0.6 bullet and open question 2) were updated to match.
