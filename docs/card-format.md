# Math Card Import Format

2026-11-01

## Purpose and principles

Cards come into the app as plain-text card files: Markdown with a few labeled fields, one file per deck, written by hand or by an AI. A card needs only a question and a solution. Optional fields turn on auto-checking, skill scheduling, hints and variants.

There are three ways in:

1. **Card files** (`.cards.md`), described in this doc. Best for writing many cards, and for cards an AI writes.
2. **Anki, using the Mastery Problem note type** (see Anki compatibility). Write cards in Anki, export, import; nothing is lost.
3. **Any Anki deck**: `.apkg`, `.colpkg`, or Anki's plain-text export. These arrive as ordinary flashcards.

The format follows five rules:

- It is plain text you can read, diff and fix in any editor, with no escaping inside math.
- Math is LaTeX between `\(` `\)` (inline) and `\[` `\]` (display), the same delimiters Anki uses. A `$` is always just a dollar sign.
- Each answer is written once, in one plain syntax, and checked by computer algebra, so any equivalent answer counts.
- Every card has a permanent ID, so re-importing a corrected file updates cards without touching review history.
- Files declare a version (`format: mastery-cards 1`), so files written today keep importing later. Format 1.1 (`format: mastery-cards 1.1`) only adds keys and behavior; every format 1 file imports unchanged.

## File layout

A card file is a header followed by cards. Each card starts with `## Card <id>`, then a few `key: value` lines, then `###` sections.

```text
---
format: mastery-cards 1
deck: Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values
source: original
license: personal
---

## Card calc1.4-1.crit-numbers.001
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial
difficulty: 2
answer-type: set
answer: -1, 0, 1
wrong: 0, 1 => x + 1 = 0 gives a critical number too @3

### Question
Find all critical numbers of \(f(x) = x^4 - 2x^2\).

### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers are where \(f'\) is zero or undefined.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 4x^3 - 4x\).
2. [alg.factor.polynomials] Factor: \(f'(x) = 4x(x - 1)(x + 1)\).
3. [alg.solve.polynomial] Solve: \(f'\) is defined everywhere and zero at \(x = -1, 0, 1\).
```

- **Header:** the `key: value` lines between the two `---` lines at the top. They set defaults for every card in the file; any card can override them. `format` is required. Every card key can be a default except `answer`, `wrong`, `error-step`, `plot`, `cue`, `time`, `vars`, `let` and `require`, which belong to one card.
- **Key lines are not YAML.** Everything after the first `: ` is the value, taken literally: no quotes, no type guessing. `answer: {1, 2}` is just that text.
- **Card IDs:** lowercase letters, digits, `.`, `-` and `_`, with no `--` (it marks template instances). Unique across everything you import, and never reused. Suggested pattern: `course.section.topic.number`.
- **Sections** start with `### Name` and run to the next `###` heading or `## Card` line. Their content is Markdown. A line starting with `##` always starts a card, and key lines start at the beginning of the line.
- **Math:** inline `\( ... \)`, display `\[ ... \]`, anything KaTeX supports.
- **Images:** `![a graph of f](media/f-graph.svg)`, with the path relative to the card file. SVG or PNG.
- **Comments:** `<!-- ... -->` is ignored.
- **Encoding:** UTF-8, one deck per file. A card's own `deck` line can place it in a sub-deck.
- **Packs:** a `.mepack` file is a zip of card files, a skills file, a `media/` folder, and the `manifest.json` and `credits.json` the pack builder writes (see Content packs).

## Card fields

Only an ID and a question are required. A problem without an `answer` is self-graded, like an Anki card with a solution on the back.

**Key lines**

| Key | Default | Values | Meaning |
| --- | --- | --- | --- |
| `kind` | `problem` | `problem`, `example`, `flashcard`, `cloze`, find-error, method | What the card is (next table) |
| `skill` | the card itself | a skill ID | The skill the card practices. Cards sharing a skill form one pool. No skill = scheduled alone, like an Anki card |
| `uses` | none | skill IDs, comma-separated | Other skills the problem needs (uses tags). Each one tags a solution step (see Components). They count at 0.4 when the app looks for weak spots |
| `difficulty` | `2` | `1` to `5` | Difficulty tier (table below) |
| `time` | from the steps | minutes, e.g. `6.5` | Format 1.1: the standard time (see Standard times). Also a part key. Not for examples, flashcards or clozes |
| `answer-type` | `self` | see Answer types | How the answer is checked |
| `answer` | none | answer syntax | The correct answer; required unless self-graded |
| `wrong` | none | answer => feedback @step, separated by `;` | Known wrong answers, usually common mistakes (see Known wrong answers). The checker must reject each one. Feedback (no ; inside) shows when the student's answer matches. @step names the solution step the mistake comes from, so a match tells which step's skill failed; the error picker preselects it. Both are optional |
| checker options | none | `vars`, `domain`, `tolerance`, `exact`, `form`, `endpoints`, `require-constant`, `units`, `sig-figs` | Fine-tune checking (see Answer types) |
| `plot` | none | `f(x), x = a..b` | Draws the graph of f above the question, such as `plot: x^3 - 3x^2, x = -2..4`; several functions separated by `;` |
| calculator | no | yes, no | Whether a calculator is allowed; the study screen shows a calculator mark when yes. Problems from exams are no. Same as `tools: calculator` |
| `tools` | none | names, comma-separated, e.g. `calculator` | Format 1.1: the tools a problem allows. It generalizes `calculator`; unknown tool names are kept and shown as a note |
| angles | radians | radians, degrees | Angle unit for trig in the question and the answer; degrees shows a note and compares in degrees |
| cue | none | required | The method named in the question is part of what is asked ("a left Riemann sum with n = 4"), so it is never stripped |
| error-step | none | a step number | find-error cards: the number of the wrong step in ### Shown Work |
| tagged | none | e.g. ai:model-name prompt-v3 0.86 | How the skills were assigned and with what confidence. AI-tagged cards stay unverified until checked |
| `deck` | the header's | `Course::Unit::Section` | Where the card sits in the course tree |
| `tags` | none | words, comma-separated | Free tags for searching |
| `source` | the header's | `original`, `personal`, or a citation | Where the card came from |
| `source-url` | none | URL | Link to the source |
| `license` | the header's | e.g. `CC BY-NC-SA 4.0`, `personal` | License of the source |
| `modified` | `no` | `yes`, `no` | `yes` if changed from the source; a translation counts |
| `verified` | none | text, e.g. `template+cas` | Set by the content pipeline to record how the key was checked |

**Kinds**

| Kind | What the student does | Scheduling |
| --- | --- | --- |
| `problem` | Works it on paper, enters an answer or self-grades | Through its skill |
| `example` | Reads a worked example while first learning a skill | Shown, never graded |
| `flashcard` | Recalls a formula, definition or theorem | Per card, like Anki |
| `cloze` | Fills in blanks marked `{{c1::...}}`, Anki's syntax | Per blank, like Anki |
| find-error | Picks the wrong step in another student's work, chooses why it is wrong, and types the corrected value | Through its skill, once the skill has two successful uncued reviews |
| method | Picks which method fits an uncued problem, without solving it | Through its method-choice skill |

**Sections**

| Section | Used by | Content |
| --- | --- | --- |
| `### Question` | problem, example | The problem statement. Required |
| `### Choices` | `choice` answers | Options as `- [x] right` and `- [ ] wrong`; several `[x]` = select all that apply |
| ### Cued Question | problem | The original wording that names the method. ### Question holds the uncued version used in reviews; this one is used for first exposure and cued-twin checks |
| ### Shown Work | find-error | Another student's numbered, skill-tagged steps with exactly one wrong step, named by error-step |
| ### Reasons | find-error | Three or four explanations as - [x] right and - [ ] wrong, exactly one right |
| `### Part a`, `### Part b`, ... | problem | A sub-question: its own key lines (`answer-type`, `answer`, `wrong`, options, optional `skill` and `time`), then its prompt. A `choice` part lists its options as `- [x]` / `- [ ]` lines after the prompt |
| `### Hints` | problem | A numbered list, mildest first; the last may give the first step |
| `### Answer` | problem | Optional display version of the answer, shown after grading |
| `### Solution` | problem, example | The full worked solution as numbered, skill-tagged steps (see Step-tagged solutions). Required for problems |
| `### Rubric` | self-graded problems | A checklist (`- [ ] ...`) the student ticks when grading their own work |
| ### Alternative Solution | problem | A second valid method, shown when the student says they used a different method |
| `### Front`, `### Back` | flashcard | The two sides. Required |
| `### Text` | cloze | Text with `{{c1::...}}` blanks. Required |
| `### Extra` | flashcard, cloze | More detail shown on the back |
| `### Notes` | any | Author notes; never shown while studying |

**Difficulty tiers**

Tiers are anchored to a good university's exams.

| Tier | Name | Anchor |
| --- | --- | --- |
| 1 | Drill | One step, one skill |
| 2 | Standard | Routine homework on one section |
| 3 | Exam | A standard exam problem at a good university, at the level of MIT 18.01, Berkeley Math 1A or UIUC Math 221 |
| 4 | Challenge | Above the standard exam: combines skills across sections, gives no hint of the method, varies the surface form |
| 5 | Elite | Advanced, in optional sections only |

Tier 4 is the default target. A skill's `exam-tier` (default 3) sets which tier counts as exam level.

**Step-tagged solutions**

A solution written as a numbered list, with each item starting with a skill ID in brackets and a short label, is step-tagged. The app shows these steps after a miss and lets the student tap the first one where their work went differently, which routes the miss to that step's skill.

```text
### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers are where f' is zero or undefined.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 4x^3 - 4x\).
2. [alg.factor.polynomials] Factor: \(f'(x) = 4x(x - 1)(x + 1)\).
```

- Step 0 is "Set up and choose the method". Tag it with the card's skill, or with a method-choice skill when choosing the method is the hard part.
- Every step names exactly one skill: the one that step uses. The card's skill and uses tags must agree with the step tags (see Components).
- Labels are a few words (Differentiate, Factor, Solve). Math and Markdown work after the colon, and a step can run over several lines.
- A solution that isn't a numbered, tagged list still imports, but the app can only offer the card's uses skills after a miss. Content packs require step tags.
- **Checked steps (format 1.1, MATH-17).** A step may carry indented `check:` lines, each an equality in answer syntax that may use the template functions (`diff`, `integrate`, `limit`, `solve`, `subs`, `simplify`, `expand`, `factor`) and, in a template, its names. They are not shown to the student. The pack build checks every claim with the computer algebra system and an independent mpmath recomputation, and grades the final line against the key: the last side of the last step's last claim, or, without one, the last math of the last step after its last `=`. Steps with math that no claim covers, and final lines that can't be matched, are listed as unverified in the build report.

```markdown
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 4x^3 - 4x\).
   check: diff(x^4 - 2x^2, x) = 4x^3 - 4x
2. [alg.factor.polynomials] Factor and solve: \(x = -1, 0, 1\).
   check: solve(4x^3 - 4x, x) = {-1, 0, 1}
```

**Components**

A problem's components are the skills it uses: its `skill`, its `uses` and the tags of its ### Solution steps. The app tracks the student on each one. The three must agree:

- Every step tag is the card's `skill` or in `uses`.
- Every `uses` entry tags at least one step.
- A multi-part problem has one solution for all its parts, so the rule holds for the whole card. A part's own `skill` counts like the card's, and it must tag at least one step: the step that answers that part.
- Only ### Solution steps count. A skill that only the ### Alternative Solution uses stays out of `uses`.

A content pack's build stops on a problem that breaks the rule. Personal decks, and the other kinds in a pack, get warnings.

**Known wrong answers**

A matched wrong answer says which step went wrong, so the app can tell which skill failed instead of only that the answer was wrong.

- List the two or three most common wrong answers on problems of tier 2 and up. A few common errors cover most misses.
- Give each one the `@step` it comes from. It must be a step of the ### Solution; any other number is an error.
- In a template, compute each wrong answer by making one error and doing everything else right: `wrong: -k => sign error @2`.
- The pack build report lists auto-checked problems (and parts) of tier 2 and up with no `wrong:` line, and wrong answers with no `@step`.

**Standard times**

A problem's standard time is how long a well-prepared student at a top school needs for it. The app measures pace against it.

| Case | Standard time in minutes |
| --- | --- |
| The card sets `time:` | That time |
| Otherwise | 0.5 + m × steps, plus m for each tier above 3 |
| No solution steps | The tier's default: 1, 2, 4, 6 or 8 for tiers 1 to 5 |

- `steps` is the number of ### Solution steps. `m` is the course's minutes per step, `pace-minutes-per-step` in the skills file (1.5 by default).
- With m = 1.5, a one-step drill gets 2 minutes and a tier 3 problem of 4 steps gets 6.5.
- A multi-part problem is timed as a whole. With no `time:` of its own, a card whose parts all set one takes their sum. A part without `time:` gets an equal share of its card's standard time.
- The pack build report lists the cards that fall back on a tier default.
- Only content packs keep `time:`. A personal import drops it, with a warning.

## Answer types

Answers use one plain syntax, the same one the student types in the app's text mode. The checker compares meaning, not text, so `x^2 - 4` and `(x-2)(x+2)` match unless a `form` option asks for one of them.

**Common syntax**

- Operators `+ - * / ^` and parentheses; `sqrt(x)`; `root(x, 3)` for a real cube root; `abs(x)` or `|x|`.
- Constants `pi`, `e` and `inf`; the word `DNE` for "does not exist".
- `ln(x)` is the natural log, `log(x)` is base 10, `log_2(x)` is base 2.
- Trig and inverse trig: `sin(x)`, `sec(x)`, `arcsin(x)` or `asin(x)`. Write `sin(x)^2` for sin² x.
- Implicit multiplication only after a number or next to parentheses: `2x`, `3(x+1)`, `(x+1)(x-1)`. Two letters never multiply (`xy` is an error; write `x*y`). `e^2x` means e² times x, so write `e^(2x)`.
- E-notation (format 1.1): `6.02e23`, `1.6e-19`, `3E-5`. Because `e` is Euler's number, a whole number, a lowercase `e` and a signed exponent keep that reading: `2e-1` is 2e − 1, and 0.2 is `2E-1`.
- Lists of alternatives or definitions are separated by `;`.

**Types**

| `answer-type` | Example `answer` | Counts as correct |
| --- | --- | --- |
| `number` | `-2/3`, `sqrt(2)/2`, `pi/4`, `inf`, `DNE` | Any equal value. Exact forms always; decimals, e-notation such as `6.02e23` included, within the default tolerance unless `exact: yes` |
| `expression` | `x^2 - 4` | Any expression equal on the domain, checked at many points and then symbolically |
| `equation` | `y = 2x + 1` | Any equivalent equation, such as `2x - y + 1 = 0` |
| `antiderivative` | `x^3/3 + C` | Anything with the same derivative; `+ C` optional unless `require-constant: yes` |
| `set` | `-1, 0, 1` | The same elements in any order; `none` is the empty set |
| `list` | `1, 2, 3` | The same elements in the same order |
| `interval` | `(-inf, 0) U (2, inf)` | The same set of numbers. `U` joins intervals; `none` and `(-inf, inf)` work; inequalities such as `x < 0 or x > 2` are also accepted when `vars` names the variable |
| `point` | `(2, -4)` | The same coordinates. Several points: `(0, 0), (2, -4)` |
| `vector` | `<1, -2, 3>` | The same components |
| `matrix` | `[[1, 2], [3, 4]]` | The same entries |
| `choice` | marked in `### Choices` | Exactly the marked option or options |
| `truefalse` | `true` | The same value |
| `text` | `concave up; concave upward` | Any listed alternative, ignoring case and extra spaces |
| `quantity` | `9.8 m/s^2` | The same value in compatible units, within `tolerance` or `sig-figs` |
| `self` | none | The student compares their work with the solution (and rubric) and grades it |

**Checker options**

| Option | Example | Effect |
| --- | --- | --- |
| `vars` | `vars: x, t` | Variables allowed in the answer; default is those in the key. Interval and inequality answers must declare theirs (format 1.1), and an undeclared letter makes the answer invalid |
| `domain` | `domain: x > 0` | Where expressions are compared. Needed with `ln`, roots and absolute values |
| `domain-strict` | `domain-strict: yes` | Format 1.1: the domain is strict, so an answer undefined at a point where the key is defined (a removable hole) is wrong. Without it such an answer gets "Your answer is undefined at … where the expected answer isn't; check its form", which uses no attempt (ADR-0019) |
| `tolerance` | `tolerance: 0.01` or `tolerance: 1%` | Absolute, or relative with `%`. Default (format 1.1): half a unit in the last requested place (`form: decimal(n)`, `sig-figs`); with no requested rounding, 1% relative (inclusive) with an absolute floor of 10^-12 (provisional). Exact answers are compared exactly. A part's own `tolerance` line overrides the card's |
| `exact` | `exact: yes` | Decimals are not accepted |
| `form` | `form: factored` | Also requires a form: `factored`, `expanded`, `simplified`, `lowest-terms`, or `decimal(2)` for two decimal places. `simplified` means canonical forms (simplified radicals, rationalized denominators), not a size measure |
| `endpoints` | `endpoints: either` | Intervals: open or closed endpoints both count |
| `require-constant` | `require-constant: yes` | Antiderivatives must include `+ C` |
| `units` | `units: m/s` | Expected units for a `quantity` |
| `sig-figs` | `sig-figs: 3` | Significant figures required for a `quantity` |
| `alternates` | `alternates: 1/2; 0.5` | Format 1.1, reserved: other answers that also count, separated by `;` |
| `sig-figs-mode` | `sig-figs-mode: advise` | Format 1.1, reserved: `off` (ignored), `advise` (a note, still correct) or `strict` (wrong figures fail) |

Two guarantees hold for every type. The app shows how it read the answer, with multiplication made explicit, before grading. A syntax error is flagged before submitting and never counts as a wrong attempt.

## Variants

A variant card is a template: it draws new numbers each time, so the student never sees the same problem twice. Its answer is computed from the numbers, so the key cannot be mistyped. Use variants for every drill-style skill.

```text
## Card calc1.4-1.crit-cubic.t01
skill: calc1.extrema.critical-numbers
difficulty: 1
answer-type: set
vars: k = int(1, 9)
let: f = x^3 - 3*k^2*x
answer: solve(diff(f, x), x)

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Solution
\(f'(x) = 3x^2 - [[3*k^2]] = 3(x - [[k]])(x + [[k]])\), defined everywhere and zero at \(x = \pm [[k]]\).
```

| Key or marker | Meaning |
| --- | --- |
| `vars:` | Random parameters, separated by `;`. Generators: `int(lo, hi)`, `int(lo, hi, not 0)` (repeat `not` to leave out more values), `choice(a, b, c)`, `decimal(lo, hi, places)`. Checker variables can follow: `vars: k = int(1, 9); x` |
| `let:` | Named helpers built from parameters, separated by `;`, each using only names defined before it |
| `require:` | Conditions every instance must meet, such as `a != b; a*c < 0`. Each is checked as soon as its names are defined, so `require: k != 2` protects `let: m = 1/(k - 2)`. Instances that fail are redrawn |
| `answer:` | May use parameters, `let` names, and `diff`, `integrate`, `limit`, `solve` (real solutions), `simplify`, `expand`, `factor`, `subs` |
| `wrong:` | Each wrong answer is computed like `answer` (`wrong: -k => sign error @2`); its feedback may use `[[ ]]` |
| `[[ expr ]]` | In any section or text key: inserts the value as plain text |
| `[[tex(expr)]]` | Inserts it typeset as math, so `1x` and `+ -3` never appear |
| `attachments:` | Format 1.1: files generated per instance with its parameters, such as a figure or a data table, stored with that instance |

Template functions take the variable as their second argument:

| Function | Result |
| --- | --- |
| `diff(f, x)`, `diff(f, x, n)` | The derivative, or the nth derivative (n up to 10) |
| `integrate(f, x)`, `integrate(f, x, a, b)` | An antiderivative (add `+ C` yourself), or the definite integral |
| `limit(f, x, a)`, `limit(f, x, a, left)`, `limit(f, x, a, right)` | The two-sided limit unless a side is named; `inf` allowed for `a`. `DNE` when the sides differ or the function oscillates |
| `solve(f, x)` | The real solutions of `f = 0`, an equation (`a*x + b = c`) or an inequality (`x^2 - k < 0`): a set, `none`, or intervals |
| `simplify(f)`, `expand(f)`, `factor(f)` | The rewritten expression |
| `subs(f, x, v)` | `f` with `x` replaced by `v` |

- Parameter and `let` names are one letter, a Greek letter or a letter with a subscript (`a_1`); `e` and `U` are taken. `choice` items are numbers or expressions in the free variables, never other template names.
- Every value is a real number or a real expression; a value with \(i\) in it (such as `sqrt(k)` for negative `k`) rejects the template.
- In `answer` and `wrong`, write `k`, not `[[k]]`. Parts of an answer that use no template name are kept exactly as written; `[[ ]]` always computes (`[[2 + 3]]` is `5`).
- `decimal()` values, and values computed from them, are shown as decimals (`2.35`); keys stay exact.
- Each `[[ ]]` sits on one line. `[[` right after a backslash (`\[[0, 1]\]`) or inside a `` `code span` `` is written as is.

On import, the app tests each template on up to 200 instances, or every combination if there are fewer. Each must meet `require`, compute its answer in under 2 seconds, and render. One failure rejects the card. The app tracks history and first-try success per template and avoids repeating parameter sets; the pack build also drops instances that are the same problem in disguise. Each instance still allows two attempts. The tested instances are stored as data, so no template code runs while studying.

Each instance is a card of its own, with the ID `<template ID>--<seed>`. The seed (8 hexadecimal digits) comes from the parameter set alone, so the same parameters keep the same ID when a corrected template is imported again; the parameters are recorded with the instance. When there are more than 200 combinations, the 200 draws are the same on every import.

## Skills and decks

Decks give the course structure; skills drive the scheduling. The `deck` path `Course::Unit::Section` builds the tree the student switches on and off, using the same `::` nesting as Anki.

A skill is one thing a student can do, such as "find critical numbers". The app schedules skills, not cards: when a skill is due, it serves a fresh card from that skill's pool. A skill referenced by a card but defined nowhere is created automatically, with no prerequisites.

The skills file is optional for personal decks and required for content packs. It sits in the pack as `skills.md`:

```text
---
format: mastery-skills 1
pace-minutes-per-step: 1.5
pace-weekly-hours: 3
---

## Section Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values
hours: 2

## Skill calc1.extrema.critical-numbers
name: Find critical numbers
deck: Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values
requires: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial
encompasses: calc1.deriv.power-rule = 0.5; alg.factor.polynomials = 0.5
confusable: calc1.shape.inflection-points
textbook: Stewart 4.1
```

| Key | Meaning |
| --- | --- |
| `name` | Shown after answering ("This was: Find critical numbers") |
| `deck` | Where the skill sits in the course tree |
| `requires` | Prerequisites. A skill is introduced only after these are learned, and errors get routed back to them |
| `encompasses` | Skills practiced inside this one, each weighted `0.25`, `0.5` or `1`. Success here gives them partial review credit |
| `confusable` | Skills easily mixed up with this one. The queue places them near each other so the student learns to tell them apart |
| `textbook` | A section reference shown when the skill keeps slipping, such as "re-read Stewart 4.1" |
| `core` | `yes` or `no` (default). Core skills are the ones goal presets such as "Mastered for core skills" count |
| `exam-tier` | `1` to `5`: the difficulty tier at which this skill counts as exam-level (default 3) |
| `chooses` | Skill IDs, comma-separated. Makes this a method-choice skill (for `method` cards): picking among the listed methods. They become prerequisites too |

The header may set a default `deck`. A skill can have a `### Notes` section. The skill IDs in `requires`, `encompasses`, `confusable` and `chooses` must exist, and prerequisites must not form a cycle; a content pack drops prerequisites implied by others (but keeps chosen methods).

**Pace standard.** A content pack's skills file also sets the course's pace, taken from a top school's syllabus. The app plans when each section starts from it.

| Where | Key | Meaning |
| --- | --- | --- |
| Header | `pace-minutes-per-step` | Minutes per solution step in standard times. Default 1.5 |
| Header | `pace-weekly-hours` | Class hours per week. Optional |
| `## Section <deck path>` | `hours` | The section's standard class hours. List the sections in the order the course covers them |

- Every number is positive.
- A section's deck path is the deck of some card or skill in the pack, and each section appears once.
- A `## Section` block has only `hours:`.
- A personal import ignores the pace standard, with a warning.

## Content packs

A pack's source folder holds `pack.json` (`id`, `title`, a semantic `version` such as `1.0.0`, and a `license` summary), `skills.md`, its card files at the top level, and `media/`. The pack builder (`content-tools/mepack.py`) applies stricter rules than a personal import:

- `skills.md` is required, every skill a card names (its `skill`, `uses`, part skills and step tags) is defined there, and every card except flashcards and clozes has a `skill`.
- Every card has a `deck` and a `license`, and every problem, example, find-error and method card has a step-tagged solution.
- A `method` card's skill is a method-choice skill (`chooses:`).
- Every problem passes the component rule (see Components).
- The pace standard's sections are decks of the pack (see Skills and decks).
- The skill graph passes its checks (see Skills and decks), and each skill's pool is reported against its targets.
- The report also lists gaps in the known wrong answers (see Known wrong answers) and cards timed by a tier default (see Standard times).

The builder writes `<id>-<version>.mepack` (the sources plus `manifest.json` with the ID, title, version, format version, courses, licenses, build date, pipeline version and a content hash, and `credits.json` grouped by source and license) and the sealed, read-only pack database the app loads, with the standard times and the pace standard. Templates are expanded into instances at build time. Each card records how its key was checked in `verified`: `template+cas` for template instances, `self-check` for other auto-checked cards, unless the source sets it. Built against the previous version, unchanged cards keep their revision, changed ones get a new revision (a changed key is noted), and cards that disappeared stay in the pack, retired.

## Anki compatibility

To write problems in Anki, create a note type named exactly `Mastery Problem` with these fields. Export as `.apkg` or as Notes in Plain Text, then import; every field maps one to one.

| Anki field | Maps to |
| --- | --- |
| `ID` | The card ID |
| `Kind` | `kind` |
| `Skill` | `skill` |
| `Uses` | `uses` |
| `Difficulty` | `difficulty` |
| `AnswerType` | `answer-type` |
| `Answer` | `answer` |
| `Options` | Checker options, one `key: value` per line |
| `Question` | `### Question` |
| `Hints` | `### Hints`, one hint per line |
| `Solution` | `### Solution` |
| CuedQuestion | ### Cued Question |
| Wrong | wrong |
| Calculator | calculator |
| `Source` | `source` |
| `License` | `license` |

The Anki deck becomes `deck`, and Anki tags become `tags`. Anki stores fields as HTML; the importer turns line breaks back into text and keeps the math. Multi-part problems and variants need card files.

Any other Anki deck imports as flashcards:

| Anki note type | Becomes |
| --- | --- |
| Basic | One flashcard |
| Basic (and reversed card) | Two flashcards |
| Cloze | One cloze card per blank number |
| Mastery Problem | Full problems, as above |
| Any other note type | Flashcards drawn with that note type's own templates and styling |

- **Formats:** `.apkg` and `.colpkg` packages, old and new Anki versions, plus Anki's plain-text export. Its header lines (`#separator`, `#html`, `#notetype column`, `#deck column`, `#tags column`, `#guid column`) are read. A headerless two-column file becomes front/back flashcards.
- **Media:** images and audio come along.
- **Review history:** optional. When included, the app rebuilds each card's memory state from Anki's review log.
- **Scripts:** JavaScript inside imported card templates never runs. It is stripped at import, and Anki's hint fields are drawn by the app itself.

## Import rules and authoring checklist

An import never changes anything until the student approves a preview, and it never deletes a card or its history.

**Import rules**

- **Preview first.** The app checks the whole file and lists what will be added, updated and rejected, with file names and line numbers.
- **Errors reject the card:** a missing or duplicate ID, no question, an unknown kind, an answer that won't parse, math that won't render, a missing image, or a template that fails its test. A duplicate ID rejects every card that uses it. Errors in the header, or text outside a card, reject the whole file. Unknown keys and sections are errors too, so a typo never passes silently.
- **Self-check:** every auto-checked card must grade its own answer as correct, or it is rejected.
- **Warnings don't reject:** a `$` that looks like math, no hints, no difficulty (it defaults to 2), text nearly identical to another card (the same math with nearly the same words), step tags that are neither the card's skill nor in its `uses`, or a `uses` entry or part skill that tags no step (see Components). `time:` and the pace standard are dropped with a warning, since only content packs keep them. In format 1.1 an unknown answer type is a warning too: the card imports as self-graded, and a pack lists the answer types it requires in its manifest.
- **Rendering:** the importer checks that `\(` `\)` and `\[` `\]` pair up and that braces balance; content packs also render every question, solution, hint and step with KaTeX in strict mode.
- **Unverified:** the student's imported cards are marked unverified (any `verified` line is ignored).
- **Same ID means update.** The content changes and review history stays. A changed answer is recorded in the card's history as "answer key updated".
- **Nothing is deleted by re-import.** Cards missing from a new version of a file are listed, and the student chooses whether to retire them. Retiring a template retires its instances, and instances a corrected template no longer makes are retired with the import.
- **Export:** the student's own cards export as one card file per deck, plus `skills.md`, and re-import unchanged.

**Authoring checklist** (for a person or an AI writing cards)

1. One skill per card; list other skills the problem needs in `uses`: the skills its solution steps use, no others.
2. Make answers machine-checkable. Use `self` only for proofs, sketches and explanations.
3. Give exact answers (`sqrt(2)/2`, `pi/3`) unless the problem asks for decimals.
4. Add a `domain` whenever an expression answer contains logs, roots or absolute values.
5. Write a full solution with every step, not just the final answer.
6. Give two or three hints, mildest first; the last may be the first step.
7. Use `\(` `\)` and `\[` `\]` for math, never `$`.
8. Never reuse or change an ID once it has been imported.
9. Write questions in your own words. For anything from an open source, fill in `source` and `license`, and set `modified: yes` if you changed it.
10. Set `difficulty` from the tier table, not by feel.
11. Write the solution as numbered, skill-tagged steps, with Step 0 for setting up or choosing the method.
12. Don't name the method in the question unless it is part of what is asked. Put a source's cued wording in ### Cued Question, or set cue: required when the method is the point.
13. On tier 2 and up, list the two or three most common wrong answers in wrong, with short feedback and the step they come from.
14. Set calculator: yes only when a calculator is truly needed, and angles: degrees only when the problem uses degrees.

## Example file

This file, `calc1-ch4-sample.cards.md`, uses every main feature: a minimal self-graded card, a multi-part auto-checked problem with hints and a step-tagged solution, a flashcard, a variant, a find-the-error card and a which-method card.

```text
---
format: mastery-cards 1
deck: Calculus I::4 Applications of Differentiation::4.3 Shape of a Graph
source: original
license: personal
---

<!-- 1. Minimal card: question and solution only, self-graded -->
## Card calc1.4-1.crit-abs.001
skill: calc1.extrema.critical-numbers
deck: Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values

### Question
Explain why \(x = 0\) is a critical number of \(f(x) = |x|\).

### Solution
\(0\) is in the domain of \(f\), and \(f'(0)\) does not exist: the slope is \(-1\) just left of \(0\) and \(1\) just right of it. A number in the domain where \(f'\) is zero or undefined is a critical number.

<!-- 2. Multi-part, auto-checked, with hints and a step-tagged solution -->
## Card calc1.4-3.cubic-shape.001
skill: calc1.shape.first-derivative-test
uses: calc1.deriv.power-rule, alg.factor.polynomials, calc1.shape.inflection-points
difficulty: 3

### Question
Let \(f(x) = x^3 - 3x^2\).

### Part a
answer-type: interval
answer: (-inf, 0) U (2, inf)
endpoints: either
On what intervals is \(f\) increasing?

### Part b
answer-type: point
answer: (0, 0)
Find the local maximum point.

### Part c
answer-type: point
answer: (2, -4)
Find the local minimum point.

### Part d
answer-type: point
answer: (1, -2)
skill: calc1.shape.inflection-points
Find the inflection point.

### Hints
1. Find where \(f'(x) > 0\).
2. \(f'(x) = 3x(x - 2)\). Make a sign chart.

### Solution
0. [calc1.shape.first-derivative-test] Set up: \(f\) increases where \(f' > 0\), has extremes where \(f'\) changes sign, and inflection points where \(f''\) changes sign.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 - 6x\).
2. [alg.factor.polynomials] Factor: \(f'(x) = 3x(x - 2)\).
3. [calc1.shape.first-derivative-test] Sign chart: \(f' > 0\) for \(x < 0\) and \(x > 2\), so \(f\) increases on \((-\infty, 0)\) and \((2, \infty)\).
4. [calc1.shape.first-derivative-test] Classify: \(f'\) changes from \(+\) to \(-\) at \(x = 0\), so \(f(0) = 0\) is a local maximum; from \(-\) to \(+\) at \(x = 2\), so \(f(2) = 8 - 12 = -4\) is a local minimum.
5. [calc1.shape.inflection-points] Inflection: \(f''(x) = 6x - 6\) changes sign at \(x = 1\), and \(f(1) = 1 - 3 = -2\), so the inflection point is \((1, -2)\).

<!-- 3. Flashcard -->
## Card calc1.4-2.mvt-statement.001
kind: flashcard
skill: calc1.mvt.statement
deck: Calculus I::4 Applications of Differentiation::4.2 The Mean Value Theorem

### Front
State the Mean Value Theorem.

### Back
If \(f\) is continuous on \([a, b]\) and differentiable on \((a, b)\), then there is a number \(c\) in \((a, b)\) with
\[ f'(c) = \frac{f(b) - f(a)}{b - a}. \]

<!-- 4. Variant template -->
## Card calc1.4-1.crit-cubic.t01
skill: calc1.extrema.critical-numbers
uses: calc1.deriv.power-rule, alg.factor.polynomials, alg.solve.polynomial
deck: Calculus I::4 Applications of Differentiation::4.1 Maximum and Minimum Values
difficulty: 1
answer-type: set
vars: k = int(1, 9)
let: f = x^3 - 3*k^2*x
answer: solve(diff(f, x), x)

### Question
Find all critical numbers of \(f(x) = [[tex(f)]]\).

### Solution
0. [calc1.extrema.critical-numbers] Set up: critical numbers are where \(f'\) is zero or undefined.
1. [calc1.deriv.power-rule] Differentiate: \(f'(x) = 3x^2 - [[3*k^2]]\).
2. [alg.factor.polynomials] Factor: \(f'(x) = 3(x - [[k]])(x + [[k]])\).
3. [alg.solve.polynomial] Solve: \(f'\) is defined everywhere and zero at \(x = \pm [[k]]\).

<!-- 5. Find the error -->
## Card calc1.3-4.chain-error.001
kind: find-error
skill: calc1.deriv.chain-rule
uses: alg.simplify
deck: Calculus I::3 Differentiation Rules::3.4 The Chain Rule
difficulty: 2
error-step: 2
answer-type: expression
answer: 6x(x^2 + 1)^2

### Question
Find \(f'(x)\) for \(f(x) = (x^2 + 1)^3\).

### Shown Work
1. [calc1.deriv.chain-rule] Outer function: \(u^3\) with \(u = x^2 + 1\).
2. [calc1.deriv.chain-rule] Differentiate: \(f'(x) = 3(x^2 + 1)^2\).
3. [alg.simplify] Done: \(f'(x) = 3(x^2 + 1)^2\).

### Reasons
- [ ] The power rule was applied to the wrong exponent
- [x] The derivative of the inner function, \(2x\), is missing
- [ ] The inner function should be cubed before differentiating

### Solution
1. [calc1.deriv.chain-rule] Outer function: \(u^3\) with \(u = x^2 + 1\).
2. [calc1.deriv.chain-rule] Chain rule: \(f'(x) = 3(x^2 + 1)^2 \cdot 2x\).
3. [alg.simplify] Simplify: \(f'(x) = 6x(x^2 + 1)^2\).

<!-- 6. Which method? -->
## Card calc1.4-4.method-limit.001
kind: method
skill: calc1.select.limit-technique
deck: Calculus I::4 Applications of Differentiation::4.4 Indeterminate Forms and l'Hospital's Rule
answer-type: choice

### Question
Which method fits? \(\displaystyle \lim_{x \to 0} \frac{\sin 3x}{x}\)

### Choices
- [ ] Direct substitution
- [ ] Factor and cancel
- [ ] Multiply by the conjugate
- [x] L'Hôpital's rule, or the known limit of sin(u)/u

### Solution
0. [calc1.select.limit-technique] Set up: substitution gives 0/0, there is nothing to factor or rationalize, and the top is a sine, so use L'Hôpital's rule or rewrite as \(3 \cdot \frac{\sin 3x}{3x}\). The limit is \(3\).
```
