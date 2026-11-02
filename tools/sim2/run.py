"""Command line: run the truth-model matrix and write the report.

    python -m tools.sim2.run --out docs/design/sim2-report.md
    python -m tools.sim2.run --quick --out /tmp/sim2.md          # toy course, one seed

Every (truth model, profile, seed) student meets both policies. Runs go to worker processes
(`--jobs`, default: all cores). Default: Chapter 4 of Calculus I plus its prerequisites over
a 10-week semester, 3 seeds, every truth model but (c) PPE.
"""

import argparse
import os
import sys
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

from tools.sim2.adapters import BackendKind
from tools.sim2.harness import PolicyName, RunConfig, RunSpec, course_named, run
from tools.sim2.metrics import RunSummary, summarize
from tools.sim2.report import ReportInput, render
from tools.sim2.truth import DEFAULT_TRUTHS, PROFILES, TRUTH_MODELS

POLICIES: tuple[PolicyName, ...] = ("P1", "P0")
BACKENDS: tuple[BackendKind, ...] = ("auto", "stand-in", "core")


def specs(
    course: str,
    truths: Sequence[str],
    profiles: Sequence[str],
    seeds: Sequence[int],
    backend: BackendKind = "auto",
) -> list[RunSpec]:
    """The matrix, P1 runs first (they are the slow ones)."""
    return [
        RunSpec(course, truth, profile, seed, policy, backend)
        for policy in POLICIES
        for truth in truths
        for profile in profiles
        for seed in seeds
    ]


def _work(job: tuple[RunSpec, RunConfig]) -> RunSummary:
    return summarize(run(*job))


def run_matrix(jobs: Sequence[RunSpec], config: RunConfig, processes: int) -> list[RunSummary]:
    if processes <= 1:
        return [_work((spec, config)) for spec in jobs]
    with ProcessPoolExecutor(max_workers=processes) as pool:
        return list(pool.map(_work, [(spec, config) for spec in jobs], chunksize=1))


def _csv(value: str, allowed: Sequence[str], what: str) -> list[str]:
    items = [v.strip() for v in value.split(",") if v.strip()]
    bad = [v for v in items if v not in allowed]
    if bad:
        raise argparse.ArgumentTypeError(f"unknown {what}: {', '.join(bad)}")
    return items


def main(argv: Sequence[str] | None = None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="python -m tools.sim2.run", description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="report path (Markdown)")
    parser.add_argument("--course", choices=("calc1-ch4", "calc1", "toy"), default="calc1-ch4")
    parser.add_argument("--seeds", type=int, default=3, help="students per truth and profile")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--truths", default=",".join(DEFAULT_TRUTHS))
    parser.add_argument("--profiles", default=",".join(PROFILES))
    parser.add_argument("--budget", type=float, default=60.0, help="minutes per study day")
    parser.add_argument("--skip", type=float, default=0.15, help="share of days skipped")
    parser.add_argument("--backend", choices=BACKENDS, default="auto")
    parser.add_argument("--quick", action="store_true", help="toy course and one seed")
    args = parser.parse_args(args_in)
    try:
        truths = _csv(args.truths, TRUTH_MODELS, "truth model")
        profiles = _csv(args.profiles, PROFILES, "profile")
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))
    course = "toy" if args.quick else args.course
    seeds = tuple(range(1, (1 if args.quick else args.seeds) + 1))
    config = RunConfig(budget_minutes=args.budget, skip_share=args.skip)
    backend: BackendKind = args.backend
    jobs = specs(course, truths, profiles, seeds, backend)
    started = time.perf_counter()
    summaries = run_matrix(jobs, config, max(1, args.jobs))
    minutes = (time.perf_counter() - started) / 60.0
    text = render(
        ReportInput(
            summaries=summaries,
            config=config,
            course=course_named(course),
            seeds=seeds,
            command="python -m tools.sim2.run " + " ".join(args_in),
            minutes=minutes,
            jobs=max(1, args.jobs),
            today=date.today(),
        )
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({len(summaries)} runs, {minutes:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
