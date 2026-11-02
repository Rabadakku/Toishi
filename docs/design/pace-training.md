# Pace training (design v1.4 addendum)

2026-11-02. The owner asked for speed to be trained, not only measured: some students would score above 90% with twice the time. He left the design to the coordinator, from data and research (`practice-research-analysis.md` §9). Built after the wave 2 merge and its follow-ups.

Grades as in `student-model.md`: **A** direct evidence in a similar setting, **B** indirect or analogous, **C** a design assumption with the check that tests it.

## 1. The problem

- **Speed is measured but never trained.** An accurate, slow student keeps getting ordinary growth problems.
- **Ordinary practice barely speeds students up.**
  - Log time falls by α ≈ 0.03 per ln(1 + practice) in EdNet and Statics (audit #14), about 2% per doubling.
  - At that rate, halving a solve time takes on the order of 10^8 practices (`speed_training_deep.md` §1).
  - Slow starters close only part of the gap: from 2.1× the fastest third's time to 1.9× (audit #29).
- **The model tracks speed as an all-time average.** Recency-weighted speed predicts held-out times better (audit #28).
- **A student at twice the standard time therefore certifies M1 and never passes M2 or M3.**

## 2. What the evidence supports

| Finding | Source | Grade for us |
|---|---|---|
| Slow-but-accurate solvers mostly use slower strategies by choice (excess caution, counting, not retrieving) rather than running the same steps slowly. Excess caution moves toward the optimal setting with practice and feedback | `speed_training_deep.md` §3 | B |
| Goals and fast pacing early in learning a complex task don't help and may interfere; goals introduced later help, more for lower-ability learners | §2, §6 | B |
| Structure-recognition practice in algebra cut equation-solving time 32–46% with no accuracy change, held at 3 weeks | §2, §4 | B (the closest evidence to calculus) |
| Training on repeated problems left learners slower and less accurate on new problems than varied training; gains in shared steps transfer | §1 | B |
| Time pressure shifts adults to simpler, error-prone strategies on equations and word problems; fast-paced practice gave no gain in a decision task, slow-paced practice did | §6 | B |
| Component speed correlates with whole-problem speed (r = .745), weakly with accuracy (.252); segmenting sequential steps for practice neither helps nor hurts (part-task g ≈ 0); no causal test of algebra or derivative fluency on calculus | §2, §4 | C |
| Recency-weighted current speed (half-life about 50 answers) plus the shared speed-up predicts held-out times best; per-student speed-up rates add little | audit #27, #28 | B (our analysis of real logs) |

## 3. Design

### 3.1 The model tracks current speed

- **Per-skill offsets** τ_s become an exponentially weighted mean of the skill's residuals, with a half-life of 10 timed correct answers on that skill. Shrinkage toward 0 with κ = 5 stays. **B** for recency, **C** for the half-life.
- **The student speed level** τ keeps its refit. Between refits, the running residual mean that the refit check uses is also recency-weighted, with a half-life of 50 answers (audit #28). **B**.
- **α stays shared at 0.05.** Shrunk per-student rates gained little on held-out times (MSE 0.2892 vs 0.2930), against 0.2839 for recency (audit #27).

### 3.2 Who gets pace work

A skill gets pace work when all of these hold:
- its current milestone is M2 or M3;
- it is accuracy-ready at the milestone tier: calibrated readiness ≥ the target;
- time is what blocks the sitting: the predicted sitting pass chance is under 0.5, while the accuracy part alone (Π P_j over the chosen problems) is at least 0.6.

Pace work replaces growth items within the skill's allowance of 3 a day. It never adds items.

### 3.3 What pace work serves

1. **Varied problems at the milestone tier, with an aim.**
   - Problems come from families not served in the last 7 days, never repeats.
   - The header shows an aim before the student starts: "Aim 8:00 · your recent typical 12:30". The time appears after submitting, as now.
   - There is no countdown and no cut-off, because time pressure pushes students toward error-prone strategies (§2).
   - Basis: feedback and goals after accuracy (§2), **B**.
2. **One method-recognition item a day** where the skill's section has them (`kind: method`: "which method fits"), answered quickly.
   - Basis: structure-recognition training, **B**.
3. **A one-time component check, then drills for a slow component.**
   - Once per skill, the tier-1 problems of its components are timed. These are single-component problems, so they show which component is slow.
   - A component whose median is above 1.5× its standard time gets one tier-1 drill a day until it is within 1.25×.
   - This covers background components too: often the algebra is the slow step, not the calculus.
   - Basis: correlational only, **C**. Logged, and stopped if drills don't move whole-problem time.

### 3.4 What the student sees

- **Skills page:** a pace column showing the current typical time against the standard (for example "1.6× → 1.3× over 2 weeks"), and the state "pace work".
- **Home:** "Pace work: 3 skills".
- **Study:** the aim line on pace items.

### 3.5 Logging and evaluation

- **A new role, `pace`.** Each item logs the aim, the recent median and the outcome time.
- **Per skill, the pace trend** is the slope of the recency-weighted median against days. It is compared before and after pace work starts.
- **Optional randomized comparison.** Among a student's slow skills, pace work could be randomized at the skill level to measure its effect within one student, and the owner decides. One student can settle about one such question a semester, so it is not on by default.

## 4. Contract changes (for the builder)

- `core.learner`: an exponentially weighted `skill_speed` and running residual mean (half-lives 10 and 50, constants in `types.py`). Golden tests are updated deliberately.
- `core.plan`:
  - a `pace` role in `Role` and `ROLES`;
  - a `pace_work(skill)` status rule (3.2);
  - item choice for pace work (3.3);
  - `WorkItem.aim_minutes`;
  - `DayPlan.pace_work` (the skills).
- **Session and bridge:** `aim_ms` on the problem view; the Skills row gains `pace_ratio` and `pace_trend`.
- **sim2:** a truth model with strategy-based slowness (a speed offset that shrinks with time feedback) and the existing ones. The gates stay; add "pace work never raises the day's items above the plan".
