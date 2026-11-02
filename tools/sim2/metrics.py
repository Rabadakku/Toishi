"""Summaries of runs and the design 6.2 gates.

Definitions (also printed in the report):
- **Certified by the deadline**: a milestone counts when the policy first certifies it on or
  before its deadline (introduction + 7, 21, 35 days). Milestones are cumulative: M2 needs
  M1's tier certified too, M3 needs M1 and M2's.
- **Minutes to M3**: minutes spent on the skill's own items from its introduction until its
  M3 was first certified (skills that reached M3 within the run).
- **Readiness +30 / +90**: the truth's mean first-try chance over the skill's target-tier pool,
  30 and 90 days after the M3 deadline, before that day's session; "at pace" multiplies by the
  chance of finishing within the standard time.
- **Truly ready at the deadline**: the truth's readiness at the milestone tier (with pace for
  M2 and M3) at the end of the deadline day is at or above the target; what a certifier that
  knew the truth would have certified by then.
- **Calibration**: the policy's predicted chance before each first try against the sampled
  outcome (P0 predicts only reviews of learned skills, with the skill card's FSRS recall).
- **False certification**: a certification whose truth readiness at that moment (at the
  milestone tier, with pace for M2 and M3) is below the target minus 0.10, the design's
  revocation line; counted per 100 skill-milestones.
"""

import math
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Final

from tools.sim2.harness import MILESTONES, RunResult, RunSpec

BINS: Final = 10
FALSE_MARGIN: Final = 0.10
STRONG_SHARE: Final = 0.95  # gate 1: share of skill-milestones certified by the deadline
WEAK_TOLERANCE: Final = 0.5  # gate 4: false certifications per 100 skill-milestones


@dataclass(frozen=True, slots=True)
class Calibration:
    n: int
    mean_predicted: float
    mean_observed: float
    ece: float
    brier: float
    log_loss: float
    bins: tuple[tuple[int, float, float], ...]  # (count, sum predicted, sum observed)

    @property
    def bias(self) -> float:
        return self.mean_predicted - self.mean_observed


@dataclass(frozen=True, slots=True)
class RunSummary:
    spec: RunSpec
    backend: str
    final: bool
    skills: int
    by_deadline: dict[str, float]
    ever: dict[str, float]
    m3_reached: int
    minutes_to_m3: float | None  # median over skills that reached M3
    ready_acc: dict[int, float]  # offset -> mean truth readiness (accuracy)
    ready_share: dict[int, float]  # offset -> share of skills at or above the target
    ready_pace: dict[int, float]  # offset -> mean truth readiness at pace
    truly_ready: dict[str, float]  # milestone -> share of skills at the target at its deadline
    deadline_ready: dict[str, float]  # milestone -> mean truth readiness at its deadline
    calibration: Calibration | None
    served_minutes: tuple[float, float]  # (mean, max) per study day
    planned_minutes: tuple[float, float]
    served_items: tuple[float, float]
    planned_items: tuple[float, float]
    cert_events: dict[str, int]
    false_certs: dict[str, int]
    false_per_100: float
    new_on_date: float  # share of skills whose new material started on its first study day
    new_violations: int  # policy-attributable: other work served, or the session stopped early
    new_budget_limited: int  # only new material was served and the budget ran out
    over_plan_days: int
    fast_share: float | None  # correct tier >= 3 first tries within the standard time
    attempts: int
    accuracy: float
    total_minutes: float
    study_days: int
    seconds: float
    extra: dict[str, float] = field(default_factory=dict)
    sittings: int = 0  # skill-sittings (P1, wave 2): one skill's part of one day's sitting
    sitting_passes: int = 0


def calibration(pairs: Iterable[tuple[float, bool]]) -> Calibration | None:
    data = list(pairs)
    if not data:
        return None
    bins = [[0, 0.0, 0.0] for _ in range(BINS)]
    brier = loss = 0.0
    for p, y in data:
        b = min(int(p * BINS), BINS - 1)
        bins[b][0] += 1
        bins[b][1] += p
        bins[b][2] += 1.0 if y else 0.0
        brier += (p - (1.0 if y else 0.0)) ** 2
        q = min(max(p, 1e-6), 1.0 - 1e-6)
        loss -= math.log(q if y else 1.0 - q)
    n = len(data)
    ece = sum(abs(s - o) for c, s, o in bins if c) / n
    return Calibration(
        n=n,
        mean_predicted=sum(p for p, _ in data) / n,
        mean_observed=sum(1 for _, y in data if y) / n,
        ece=ece,
        brier=brier / n,
        log_loss=loss / n,
        bins=tuple((int(c), s, o) for c, s, o in bins),
    )


def pooled_calibration(items: Sequence[Calibration | None]) -> Calibration | None:
    """Calibration over several runs, from their bins (ECE, means; Brier and log loss are
    count-weighted means)."""
    cals = [c for c in items if c is not None]
    if not cals:
        return None
    n = sum(c.n for c in cals)
    bins = [(0, 0.0, 0.0)] * BINS
    for c in cals:
        bins = [(a + x, b + y, d + z) for (a, b, d), (x, y, z) in zip(bins, c.bins, strict=True)]
    return Calibration(
        n=n,
        mean_predicted=sum(c.mean_predicted * c.n for c in cals) / n,
        mean_observed=sum(c.mean_observed * c.n for c in cals) / n,
        ece=sum(abs(s - o) for cnt, s, o in bins if cnt) / n,
        brier=sum(c.brier * c.n for c in cals) / n,
        log_loss=sum(c.log_loss * c.n for c in cals) / n,
        bins=tuple(bins),
    )


def _mean_max(values: Sequence[float]) -> tuple[float, float]:
    return (statistics.fmean(values), max(values)) if values else (0.0, 0.0)


def summarize(result: RunResult) -> RunSummary:
    skills = result.skills
    n = len(skills)
    by_deadline: dict[str, float] = {}
    ever: dict[str, float] = {}
    for m in MILESTONES:
        on_time = sum(
            1
            for s in skills
            if (d := result.first_cert.get((s, m))) is not None and d <= result.deadline(s, m)
        )
        by_deadline[m] = on_time / n
        ever[m] = sum(1 for s in skills if (s, m) in result.first_cert) / n
    reached = [result.minutes_to_m3[s] for s in skills if s in result.minutes_to_m3]
    offsets = sorted({off for _, off in result.readiness})
    ready_acc: dict[int, float] = {}
    ready_share: dict[int, float] = {}
    ready_pace: dict[int, float] = {}
    for off in offsets:
        vals = [v for (s, o), v in result.readiness.items() if o == off]
        ready_acc[off] = statistics.fmean(a for a, _ in vals)
        ready_share[off] = sum(1 for a, _ in vals if a >= result.target) / len(vals)
        ready_pace[off] = statistics.fmean(p for _, p in vals)
    truly_ready: dict[str, float] = {}
    deadline_ready: dict[str, float] = {}
    for m in MILESTONES:
        values = [v for (s, mm), v in result.deadline_ready.items() if mm == m]
        truly_ready[m] = (
            sum(1 for v in values if v >= result.target) / len(values) if values else 0.0
        )
        deadline_ready[m] = statistics.fmean(values) if values else 0.0
    cal = calibration((a.predicted, a.correct) for a in result.attempts if a.predicted is not None)
    studied = [d for d in result.days if d.studied]
    events = [e for e in result.events if e.certified]
    cert_events = {m: sum(1 for e in events if e.milestone == m) for m in MILESTONES}
    line = result.target - FALSE_MARGIN
    false_certs = {
        m: sum(1 for e in events if e.milestone == m and e.truth < line) for m in MILESTONES
    }
    on_date = violations = limited = considered = 0
    by_index = {d.index: d for d in result.days}
    for s in skills:
        first = result.first_study[s]
        if first is None:
            continue
        considered += 1
        if result.first_new.get(s) == first:
            on_date += 1
            continue
        day = by_index[first]
        if any(r != "new" for r in day.roles) or not day.budget_hit:
            violations += 1
        else:
            limited += 1
    hard = [a for a in result.attempts if a.tier >= 3 and a.correct]
    attempts = len(result.attempts)
    return RunSummary(
        spec=result.spec,
        backend=result.backend,
        final=result.final,
        skills=n,
        by_deadline=by_deadline,
        ever=ever,
        m3_reached=len(reached),
        minutes_to_m3=statistics.median(reached) if reached else None,
        ready_acc=ready_acc,
        ready_share=ready_share,
        ready_pace=ready_pace,
        truly_ready=truly_ready,
        deadline_ready=deadline_ready,
        calibration=cal,
        served_minutes=_mean_max([d.served_minutes for d in studied]),
        planned_minutes=_mean_max([d.planned_minutes for d in studied]),
        served_items=_mean_max([float(d.served_items) for d in studied]),
        planned_items=_mean_max([float(d.planned_items) for d in studied]),
        cert_events=cert_events,
        false_certs=false_certs,
        false_per_100=100.0 * sum(false_certs.values()) / (n * len(MILESTONES)),
        new_on_date=on_date / considered if considered else 1.0,
        new_violations=violations,
        new_budget_limited=limited,
        over_plan_days=sum(1 for d in studied if d.served_items > d.planned_items),
        fast_share=sum(1 for a in hard if a.fast) / len(hard) if hard else None,
        attempts=attempts,
        accuracy=sum(1 for a in result.attempts if a.correct) / attempts if attempts else 0.0,
        total_minutes=sum(d.served_minutes for d in studied),
        study_days=len(studied),
        seconds=result.seconds,
        sittings=len(result.sittings),
        sitting_passes=sum(1 for s in result.sittings if s.passed),
    )


# ---------------------------------------------------------------- aggregation and gates


@dataclass(frozen=True, slots=True)
class Stat:
    mean: float
    sd: float
    n: int

    def fmt(self, digits: int = 2) -> str:
        if self.n == 0 or math.isnan(self.mean):
            return "n/a"
        if self.n == 1:
            return f"{self.mean:.{digits}f}"
        return f"{self.mean:.{digits}f} ± {self.sd:.{digits}f}"


def stat(values: Iterable[float | None]) -> Stat:
    vals = [v for v in values if v is not None and not math.isnan(v)]
    if not vals:
        return Stat(float("nan"), 0.0, 0)
    return Stat(statistics.fmean(vals), statistics.stdev(vals) if len(vals) > 1 else 0.0, len(vals))


type GroupKey = tuple[str, str, str]  # (truth, profile, policy)


def group(summaries: Iterable[RunSummary]) -> dict[GroupKey, list[RunSummary]]:
    out: dict[GroupKey, list[RunSummary]] = {}
    for s in summaries:
        out.setdefault((s.spec.truth, s.spec.profile, s.spec.policy), []).append(s)
    for runs in out.values():
        runs.sort(key=lambda r: r.spec.seed)
    return out


@dataclass(frozen=True, slots=True)
class Gate:
    name: str
    policy: str
    passed: bool | None  # None: not evaluated (no runs)
    detail: str
    provisional: bool  # True: P1 on the stand-in

    @property
    def verdict(self) -> str:
        if self.passed is None:
            return "NOT RUN"
        word = "PASS" if self.passed else "FAIL"
        return f"{word} (stand-in)" if self.provisional else word


def gates(summaries: Sequence[RunSummary]) -> list[Gate]:
    """The four 6.2 gates for P1, and the same checks of P0 for reference."""
    groups = group(summaries)
    out: list[Gate] = []
    for policy in ("P1", "P0"):
        runs = [s for s in summaries if s.spec.policy == policy]
        provisional = any(not s.final for s in runs)
        strong = groups.get(("a-model", "strong", policy), [])
        if strong:
            shares = {m: stat(r.by_deadline[m] for r in strong).mean for m in MILESTONES}
            ok = all(v >= STRONG_SHARE for v in shares.values())
            detail = ", ".join(f"{m} {v:.2f}" for m, v in shares.items())
            detail += f" of skills by deadline (threshold {STRONG_SHARE:.2f}; {len(strong)} seeds)"
            out.append(
                Gate(
                    "Strong model-truth student certifies M1-M3 on time",
                    policy,
                    ok,
                    detail,
                    provisional,
                )
            )
        else:
            out.append(
                Gate(
                    "Strong model-truth student certifies M1-M3 on time",
                    policy,
                    None,
                    "no runs",
                    provisional,
                )
            )
        if runs:
            v = sum(r.new_violations for r in runs)
            lim = sum(r.new_budget_limited for r in runs)
            detail = (
                f"{v} skill introductions not served on their first study day by the policy's "
                f"choice; {lim} more only because new material alone filled the budget "
                f"({len(runs)} runs)"
            )
            out.append(
                Gate(
                    "New material is always served on its date", policy, v == 0, detail, provisional
                )
            )
            over = sum(r.over_plan_days for r in runs)
            detail = f"{over} study days served more items than planned ({len(runs)} runs)"
            out.append(
                Gate("Daily items never exceed the plan", policy, over == 0, detail, provisional)
            )
    weak_parts: list[str] = []
    weak_ok: bool | None = None
    truths = sorted({s.spec.truth for s in summaries})
    provisional = any(not s.final for s in summaries if s.spec.policy == "P1")
    for truth in truths:
        p1 = groups.get((truth, "weak", "P1"), [])
        p0 = groups.get((truth, "weak", "P0"), [])
        if not p1 or not p0:
            continue
        a = stat(r.false_per_100 for r in p1).mean
        b = stat(r.false_per_100 for r in p0).mean
        ok = a <= b + WEAK_TOLERANCE
        weak_ok = ok if weak_ok is None else weak_ok and ok
        weak_parts.append(f"{truth}: P1 {a:.1f} vs P0 {b:.1f} {'ok' if ok else 'WORSE'}")
    detail = (
        "false certifications of weak students per 100 skill-milestones (tolerance "
        f"+{WEAK_TOLERANCE}): " + "; ".join(weak_parts)
        if weak_parts
        else "no weak-student runs"
    )
    out.insert(
        3,
        Gate(
            "Weak students are not certified more often than under the baseline",
            "P1 vs P0",
            weak_ok,
            detail,
            provisional,
        ),
    )
    return out
