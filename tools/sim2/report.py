"""The Markdown report (`docs/design/sim2-report.md`)."""

# ruff: noqa: RUF001 - the report prints math symbols (minus, times, Greek letters) on purpose

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from tools.sim2.course import SimCourse, perturb_tags
from tools.sim2.harness import MILESTONES, RunConfig
from tools.sim2.metrics import (
    FALSE_MARGIN,
    STRONG_SHARE,
    WEAK_TOLERANCE,
    RunSummary,
    gates,
    group,
    pooled_calibration,
    stat,
)
from tools.sim2.truth import (
    PPE_B,
    PPE_C,
    PPE_GAIN,
    PPE_M,
    PPE_X,
    RT06_GAIN,
    RT06_S0,
    FsrsMemory,
    RohrerTaylorMemory,
    rohrer_taylor_exp1,
)

TRUTH_TEXT = {
    "a-model": "The design's own model (3.2): conjunctive, execution × FSRS-6 memory, hidden "
    "values drawn around the design's priors.",
    "b-additive": "Additive Best-LR / DAS3H learner: logit = ability − difficulty + Σ over "
    "components of [β + Σ_w (g_w ln(1 + successes_w) − t_w ln(1 + attempts_w))], windows "
    "1 h, 1 d, 7 d, 30 d, ∞.",
    "c-ppe": f"Conjunctive over components, each σ(β − δ + {PPE_GAIN:g}·N^c·T_w^−(b + m·space)) "
    f"with c = {PPE_C}, b = {PPE_B}, m = {PPE_M:g}, x = {PPE_X} (LKT vignette fit, "
    "student_models.md §5; m sits at its lower bound, so decay barely depends on spacing).",
    "d-rohrer-taylor": f"(a) with exponential forgetting, S₀ = {RT06_S0} d and spaced-review gain "
    f"{RT06_GAIN:g}, fitted to Rohrer & Taylor 2006 Exp 1.",
    "e-slow": "(a) learning at half rate: γ, ρ and the speed-up exponent halved.",
    "e-careless": "(a) with slip 0.12 (the target of 0.90 is out of reach by construction).",
    "f-tags": "(a) on the real tags while the planner sees 10% of non-main tags dropped and 10% "
    "swapped.",
}
PROFILE_TEXT = {
    "typical": "drawn per seed: ability offset ~ N(0, 0.65²), component offsets ~ N(0, 0.7²), "
    "slip 0.02–0.05, median time ≈ 2·T* before practice",
    "strong": "above the targets from the start: component execution ≈ 0.997, memories from "
    "before the course, slip 0.01, median time ≈ 0.5·T*",
    "weak": "ability offset −1.3, slip 0.06, faster forgetting (φ 1.3), median time ≈ 2.8·T*",
}


@dataclass(frozen=True, slots=True)
class ReportInput:
    summaries: Sequence[RunSummary]
    config: RunConfig
    course: SimCourse
    seeds: tuple[int, ...]
    command: str
    minutes: float
    jobs: int
    today: date


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.0f}%"


def render(data: ReportInput) -> str:
    sums = data.summaries
    provisional = any(not s.final for s in sums if s.spec.policy == "P1")
    p1_backend = next((s.backend for s in sums if s.spec.policy == "P1"), "none")
    lines: list[str] = []
    add = lines.append
    add("# Simulator report: robust evaluation of the student model and planner (design 6.2)")
    add("")
    add(
        f"Generated {data.today.isoformat()} by `{data.command}`: {len(sums)} runs in "
        f"{data.minutes:.1f} minutes on {data.jobs} process{'es' if data.jobs > 1 else ''}. "
        "Code: `tools/sim2/`; tests: `tests/sim2/`."
    )
    add("")
    if provisional:
        add(
            "> **P1 is a stand-in.** `core.learner` and `core.plan` have not merged, so P1 ran "
            "on `tools/sim2/standin.py`, a simplified version of the design written for this "
            "simulator. Every P1 number and every P1 gate below is provisional and labelled "
            '"stand-in". P0 (the baseline) and the truth models are final for this simulator.'
        )
    else:
        add(f"> P1 ran on the `{p1_backend}` backend.")
    add("")
    add("## Gates (design 6.2)")
    add("")
    add("| Gate | Policy | Result | Detail |")
    add("|---|---|---|---|")
    for g in gates(sums):
        add(f"| {g.name} | {g.policy} | **{g.verdict}** | {g.detail} |")
    add("")
    add(
        "P1's rows are the gates. P0's rows apply the same checks to the baseline for "
        "reference. A strong student passes gate 1 when at least "
        f"{STRONG_SHARE:.0%} of its skills reach each milestone by the deadline (mean over "
        "seeds). Gate 2 counts a skill when its new material did not start on its first study "
        "day on or after its introduction date although the policy served other work that day "
        "or stopped before the budget; days where new material alone filled the budget are "
        "reported, not counted. Gate 4 compares false certifications (truth readiness below "
        f"the target − {FALSE_MARGIN:.2f} at the moment of certification) of the weak profile, "
        f"with a tolerance of {WEAK_TOLERANCE} per 100 skill-milestones."
    )
    add("")
    _overview(lines, data)
    _setup(lines, data)
    _results(lines, data)
    _diagnostics(lines, data)
    _standin_notes(lines, data)
    _real_run(lines, data)
    return "\n".join(lines) + "\n"


def _over_models(runs_by_model: Sequence[Sequence[float | None]]) -> float:
    """The mean over truth models of each model's mean over seeds."""
    return stat(stat(values).mean for values in runs_by_model).mean


def _overview(lines: list[str], data: ReportInput) -> None:
    """Each profile and policy, averaged over the truth models (each model weighs the same)."""
    add = lines.append
    groups = group(data.summaries)
    add("## Overview across truth models")
    add("")
    add(
        "Means over truth models of each model's mean over seeds. Certified / ready: the share "
        "of skills certified by the deadline against the share the truth says was at the target "
        "then (with pace for M2 and M3). False: certifications while the truth was below the "
        "target − 0.10, per 100 skill-milestones. Ready +90: truth readiness at the target tier "
        "90 days after the M3 deadline (accuracy / at pace)."
    )
    add("")
    add(
        "| Profile | Policy | M1 certified / ready | M2 certified / ready | M3 certified / ready "
        "| False | Ready +90 | Minutes a day |"
    )
    add("|---|---|---|---|---|---|---|---|")
    for profile in ("typical", "strong", "weak"):
        for policy in ("P1", "P0"):
            models = [runs for k, runs in groups.items() if k[1] == profile and k[2] == policy]
            if not models:
                continue
            final = all(r.final for runs in models for r in runs)
            label = policy + ("" if final else " (stand-in)")
            cells: list[str] = []
            for m in MILESTONES:
                cert = _over_models([[r.by_deadline[m] for r in runs] for runs in models])
                ready = _over_models([[r.truly_ready[m] for r in runs] for runs in models])
                cells.append(f"{cert:.2f} / {ready:.2f}")
            false = _over_models([[r.false_per_100 for r in runs] for runs in models])
            acc = _over_models([[r.ready_acc.get(90) for r in runs] for runs in models])
            pace = _over_models([[r.ready_pace.get(90) for r in runs] for runs in models])
            minutes = _over_models([[r.served_minutes[0] for r in runs] for runs in models])
            add(
                f"| {profile} | {label} | {' | '.join(cells)} | {false:.1f} | "
                f"{acc:.2f} / {pace:.2f} | {minutes:.0f} |"
            )
    add("")


def _setup(lines: list[str], data: ReportInput) -> None:
    add = lines.append
    cfg = data.config
    course = data.course
    n_problems = len(course.true_specs)
    sizes = {t: sum(len(course.pools[s][t]) for s in course.skill_ids) for t in (1, 2, 3, 4)}
    std = course.course.standard
    add("## Setup")
    add("")
    add(
        f"- **Course:** `{course.name}`, {len(course.skill_ids)} course skills and "
        f"{sum(1 for i in course.catalog.values() if i.background)} background components "
        f"from the component map, {len(std.sections)} sections, "
        f"{sum(s.hours for s in std.sections):.1f} class hours at {std.weekly_hours:g} a week "
        f"({course.course_days} days). "
        f"{n_problems} generated problems: "
        + ", ".join(f"tier {t} {n}" for t, n in sizes.items())
        + ". Components: tier 1 the skill; tier 2 plus 0–1 prerequisite or section component; "
        "tier 3 three or four; tier 4 four to six with one from another section. "
        "T* = 0.5 + 1.5·steps + 1.5·max(0, tier − 3) minutes."
    )
    add(
        f"- **Runs:** start {cfg.start.isoformat()}, through each skill's M3 deadline + 90 days "
        f"(self-study, no course end). Budget {cfg.budget_minutes:g} minutes a study day; "
        f"{cfg.skip_share:.0%} of days skipped (the same days for both policies); a worked "
        f"example takes {cfg.example_minutes:g} minutes and a miss 1 more minute to read the "
        f"solution. Target {cfg.accuracy_target:.2f} at tier {cfg.target_tier}. Seeds "
        f"{', '.join(map(str, data.seeds))}; each seed is one student per truth model and "
        "profile, met by both policies."
    )
    add(
        "- **P1** (design): `core.learner` + `core.plan` through `tools/sim2/adapters.py` "
        "(stand-in until the merge). **P0** (baseline): one FSRS-6 card per skill (defaults "
        "of `core/engine/fsrs_adapter.py`), introduced on its pace date with a worked example, "
        "random tier 1–2 problems (at most 8 a day) until 3 in a row are right, then one random "
        "target-tier problem per due review. P0 certifies M1 when learning ends and M2 and M3 "
        "after 3 correct first tries in a row at tier 3+ within T*; it never revokes."
    )
    add("")
    add("| Truth model | What it is |")
    add("|---|---|")
    ran = {s.spec.truth for s in data.summaries}
    for name, text in TRUTH_TEXT.items():
        if name in ran:
            add(f"| {name} | {text} |")
    add("")
    add("Profiles: " + "; ".join(f"**{k}** ({v})" for k, v in PROFILE_TEXT.items()) + ".")
    add("")


def _results(lines: list[str], data: ReportInput) -> None:
    add = lines.append
    groups = group(data.summaries)
    truths = [t for t in TRUTH_TEXT if any(k[0] == t for k in groups)]
    add("## Results by truth model")
    add("")
    add(
        "Mean ± standard deviation over seeds. M1–M3: share of skills certified by the "
        "deadline (cumulative). Min to M3: median minutes on the skill until M3, over skills "
        "that reached it (count in brackets). Ready: truth readiness at the target tier 30 and "
        "90 days after the M3 deadline, and the share of skills at or above the target at +90. "
        "Calibration: expected calibration error and bias (predicted − observed). Minutes: per "
        "study day served (mean / max). False: false certifications per 100 skill-milestones."
    )
    add("")
    for truth in truths:
        add(f"### {truth}")
        add("")
        add(TRUTH_TEXT[truth])
        add("")
        add(
            "| Profile | Policy | M1 | M2 | M3 | Min to M3 | Ready +30 | Ready +90 | ≥ target "
            "+90 | ECE | Bias | Minutes | False |"
        )
        add("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for profile in ("typical", "strong", "weak"):
            for policy in ("P1", "P0"):
                runs = groups.get((truth, profile, policy))
                if not runs:
                    continue
                label = policy + (" (stand-in)" if not runs[0].final else "")
                m = [stat(r.by_deadline[k] for r in runs).fmt() for k in MILESTONES]
                reached = stat(float(r.m3_reached) for r in runs)
                mins = stat(r.minutes_to_m3 for r in runs)
                r30 = stat(r.ready_acc.get(30) for r in runs)
                r90 = stat(r.ready_acc.get(90) for r in runs)
                share90 = stat(r.ready_share.get(90) for r in runs)
                ece = stat(r.calibration.ece if r.calibration else None for r in runs)
                bias = stat(r.calibration.bias if r.calibration else None for r in runs)
                served = stat(r.served_minutes[0] for r in runs)
                peak = max(r.served_minutes[1] for r in runs)
                false = stat(r.false_per_100 for r in runs)
                add(
                    f"| {profile} | {label} | {m[0]} | {m[1]} | {m[2]} | "
                    f"{mins.fmt(0)} ({reached.mean:.0f}) | {r30.fmt()} | {r90.fmt()} | "
                    f"{share90.fmt()} | {ece.fmt()} | {bias.fmt()} | "
                    f"{served.mean:.0f} / {peak:.0f} | {false.fmt(1)} |"
                )
        add("")


def _diagnostics(lines: list[str], data: ReportInput) -> None:
    add = lines.append
    groups = group(data.summaries)
    add("## Diagnostics")
    add("")
    add("### Workload and pace")
    add("")
    add(
        "Planned items and minutes are what the policy reported for the day (the design never "
        "caps them); served is what fit in the budget. Fast: the share of correct tier 3+ first "
        "tries within T*. M2 and M3 certification needs P(correct and within T*) at or above "
        "the target, so with a 0.90 target a student who is always right still needs about "
        "90% of solves within T*."
    )
    add("")
    add(
        "| Truth | Profile | Policy | Planned items | Served items | Planned min | Accuracy "
        "| Fast | Ready +90 at pace | Ever M3 |"
    )
    add("|---|---|---|---|---|---|---|---|---|---|")
    for (truth, profile, policy), runs in sorted(groups.items()):
        label = policy + (" (stand-in)" if not runs[0].final else "")
        add(
            f"| {truth} | {profile} | {label} | "
            f"{stat(r.planned_items[0] for r in runs).mean:.0f} | "
            f"{stat(r.served_items[0] for r in runs).mean:.1f} | "
            f"{stat(r.planned_minutes[0] for r in runs).mean:.0f} | "
            f"{_pct(stat(r.accuracy for r in runs).mean)} | "
            f"{_pct(stat(r.fast_share for r in runs).mean)} | "
            f"{stat(r.ready_pace.get(90) for r in runs).fmt()} | "
            f"{stat(r.ever['M3'] for r in runs).fmt()} |"
        )
    add("")
    add("### Certified against truly ready, at each deadline")
    add("")
    add(
        "Certified: the share of skills the policy certified by the deadline. Ready: the share "
        "whose truth readiness at the milestone tier (with pace for M2 and M3) was at or above "
        "the target at the end of the deadline day, under that policy's practice. A planner "
        "that certifies far less than is ready wastes practice; one that certifies more is "
        "certifying students who are not there. Mean truth readiness in brackets."
    )
    add("")
    add(
        "| Truth | Profile | Policy | M1 certified / ready | M2 certified / ready "
        "| M3 certified / ready |"
    )
    add("|---|---|---|---|---|---|")
    for (truth, profile, policy), runs in sorted(groups.items()):
        label = policy + (" (stand-in)" if not runs[0].final else "")
        cells = []
        for m in MILESTONES:
            cert = stat(r.by_deadline[m] for r in runs).mean
            ready = stat(r.truly_ready[m] for r in runs).mean
            mean = stat(r.deadline_ready[m] for r in runs).mean
            cells.append(f"{cert:.2f} / {ready:.2f} ({mean:.2f})")
        add(f"| {truth} | {profile} | {label} | " + " | ".join(cells) + " |")
    add("")
    add("### Calibration, pooled over seeds and profiles")
    add("")
    add("| Truth | Policy | Attempts | Predicted | Observed | ECE | Brier | Log loss |")
    add("|---|---|---|---|---|---|---|---|")
    truths = sorted({k[0] for k in groups})
    for truth in truths:
        for policy in ("P1", "P0"):
            cals = [
                r.calibration
                for (t, _, p), runs in groups.items()
                if t == truth and p == policy
                for r in runs
            ]
            cal = pooled_calibration(cals)
            if cal is None:
                continue
            add(
                f"| {truth} | {policy} | {cal.n} | {cal.mean_predicted:.3f} | "
                f"{cal.mean_observed:.3f} | {cal.ece:.3f} | {cal.brier:.3f} | {cal.log_loss:.3f} |"
            )
    add("")
    add("### Truth-model checks")
    add("")
    rt = rohrer_taylor_exp1(RohrerTaylorMemory, students=1000)
    fs = rohrer_taylor_exp1(lambda: FsrsMemory(1.0), students=1000)
    add("Rohrer & Taylor 2006 Exp 1 on a median student (one-component problems):")
    add("")
    add("| Memory | Massed 4w/1w | Spaced/massed 4w | Spaced/massed 1w |")
    add("|---|---|---|---|")
    add("| Observed (D4) | 0.43 | 2.0 | 0.93 |")
    add(
        f"| Truth (d) | {rt.massed_ratio:.2f} | {rt.spaced_over_massed_4w:.2f} | "
        f"{rt.spaced_over_massed_1w:.2f} |"
    )
    add(
        f"| FSRS-6 defaults (truth a, φ = 1) | {fs.massed_ratio:.2f} | "
        f"{fs.spaced_over_massed_4w:.2f} | {fs.spaced_over_massed_1w:.2f} |"
    )
    add("")
    if any(s.spec.truth == "f-tags" for s in data.summaries):
        tn = perturb_tags(data.course).tag_noise
        if tn is not None:
            add(
                f"Truth (f) view: of {tn.non_main_tags} non-main tags, {tn.dropped} "
                f"({tn.dropped / tn.non_main_tags:.1%}) were dropped and {tn.swapped} "
                f"({tn.swapped / tn.non_main_tags:.1%}) swapped; main skills are never changed "
                f"({tn.all_tags} tags in all)."
            )
            add("")


STANDIN_CHOICES = (
    "Order among skills when the plan is longer than the session (4.3 says only that "
    "maintenance and growth are interleaved): maintenance by lowest forecast readiness, "
    "alternating with on-time growth by nearest deadline, and missed-milestone skills least "
    "recently practised first. In development runs (a-model, typical, seeds 3 and 4), serving "
    "growth in course order starved later skills: M1 at any time for 13-15% of skills instead "
    "of 28%.",
    "Empty growth band: 4.4 says to take the problem closest to 0.80 from the milestone tier or "
    "the rung below. For a strong student that picks rung-below problems, which never count "
    "toward the milestone (in development, a-model strong seed 1: M1 by its deadline for 72% "
    "of skills instead of 100%). The stand-in keeps to the milestone tier unless all its "
    "problems are below the "
    "band, and applies the 90-day no-repeat preference within each tier for the same reason.",
    "The 40% cap on missed-milestone work holds for every prefix of the session while other "
    "work remains; after that, missed-milestone items continue. Read literally, the cap would "
    "end sessions early once most skills are past a deadline.",
    "A reference check that falls due while new material is pending waits until the new "
    "material is served (new material first).",
    "Certifier priors and maintenance forecasts average the first 3 representative problems "
    "(the design allows up to 10); M2 and M3 priors multiply by the model's chance of "
    "finishing within T*.",
    "Not in the stand-in: refits other than the per-tier recalibration, the struggling and "
    "slip-limited statuses, exams, mid-course starts, confusable adjacency and the extra "
    "problem after an execution miss.",
)


def _standin_notes(lines: list[str], data: ReportInput) -> None:
    if not any(not s.final for s in data.summaries if s.spec.policy == "P1"):
        return
    add = lines.append
    add("## Where the stand-in had to choose")
    add("")
    add(
        "The spec leaves these open, and the stand-in's choices shape the provisional P1 "
        "numbers; the real planner may choose differently:"
    )
    add("")
    for text in STANDIN_CHOICES:
        add(f"- {text}")
    add("")


def _real_run(lines: list[str], data: ReportInput) -> None:
    add = lines.append
    add("## Running P1 for real")
    add("")
    add(
        '1. Merge model-core and plan-core into this branch. `adapters.load_backend("auto")` '
        "switches to `core` once `core.learner.StudentModel` and `core.plan.plan_day`, "
        "`next_item`, `intro_dates` and `Certifier` exist."
    )
    add(
        '2. Run `python -c "from tools.sim2.adapters import core_backend_problems as p; '
        'print(p())"` and fix `_CorePlanner` in `tools/sim2/adapters.py` until it prints `[]`: '
        "the contract leaves the Certifier's constructor and how it takes observations, the "
        "arguments of `next_item` and how a refit is adopted to the implementations."
    )
    add(
        "3. Rerun `python -m tools.sim2.run --backend core --out docs/design/sim2-report.md` "
        "and the slow tests (`pytest -m slow tests/sim2`)."
    )
    add("")
