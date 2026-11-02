"""Measure built .apps for the M0 shell spike and write spike/spike-report.md.

    python scripts/spike_measure.py measure --label NAME --app X.app --runs 5 --out m.json
    python scripts/spike_measure.py report m1.json m2.json --out spike/spike-report.md

Each run launches `<app>/Contents/MacOS/<exe> --self-test` with TOISHI_LAUNCH_T0 set
to the launch time, so the app can report launch-to-self-test-pass in milliseconds.
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SELF_TEST_PREFIX = "SELFTEST "
LAUNCH_T0_ENV = "TOISHI_LAUNCH_T0"

MANUAL_CHECKS = (
    "Cmd+Z / Shift+Cmd+Z inside the math field undo/redo MathLive edits",
    "Cmd+C / Cmd+V copy and paste LaTeX in and out of the math field",
    "Dead keys (Option+E, e) and the emoji/character picker work in the field",
    "Typing does not play the macOS alert sound (pywebview #1722)",
    "Title does not overlap the traffic-light buttons (macOS 26, debug off)",
    "Cmd+Q quits at once; Cmd+W closes the window",
    "Dark mode follows the system setting",
)


def bundle_bytes(path: Path) -> int:
    """Apparent size of a bundle, not following symlinks (like `du -A`)."""
    if path.is_file():
        return path.stat().st_size
    return sum(
        (Path(root) / name).lstat().st_size for root, _, files in os.walk(path) for name in files
    )


def executable_for(app: Path) -> Path:
    if app.suffix != ".app":
        return app
    candidates = [p for p in (app / "Contents" / "MacOS").iterdir() if os.access(p, os.X_OK)]
    if len(candidates) != 1:
        raise SystemExit(f"{app}: expected one executable in Contents/MacOS, found {candidates}")
    return candidates[0]


def parse_self_test(stdout: str) -> dict[str, Any] | None:
    lines = [line for line in stdout.splitlines() if line.startswith(SELF_TEST_PREFIX)]
    if not lines:
        return None
    result: dict[str, Any] = json.loads(lines[-1].removeprefix(SELF_TEST_PREFIX))
    return result


def run_once(exe: Path, timeout_s: float) -> dict[str, Any]:
    env = {**os.environ, LAUNCH_T0_ENV: repr(time.time())}
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [str(exe), "--self-test"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"exit_code": None, "wall_ms": timeout_s * 1000, "result": None, "error": "timeout"}
    return {
        "exit_code": proc.returncode,
        "wall_ms": round((time.perf_counter() - start) * 1000, 1),
        "result": parse_self_test(proc.stdout),
        "stderr_tail": proc.stderr[-1500:],
    }


def _launch_ms(run: dict[str, Any]) -> float | None:
    """Launch-to-report time of a passing run (a failed run only measures the timeout)."""
    result = run.get("result") or {}
    if run.get("exit_code") != 0 or result.get("ok") is not True:
        return None
    value = (result.get("timings") or {}).get("launch_to_report_ms")
    return float(value) if isinstance(value, int | float) else None


def measure(label: str, app: Path, runs: int, timeout_s: float = 90) -> dict[str, Any]:
    exe = executable_for(app)
    results = [run_once(exe, timeout_s) for _ in range(runs)]
    launches = [ms for ms in map(_launch_ms, results) if ms is not None]
    first = results[0].get("result") or {}
    return {
        "label": label,
        "app": str(app),
        "shell": first.get("shell", "unknown"),
        "bundle_bytes": bundle_bytes(app),
        "passed": all(r["exit_code"] == 0 and (r["result"] or {}).get("ok") for r in results),
        "first_launch_ms": launches[0] if launches else None,
        "median_launch_ms": statistics.median(launches) if launches else None,
        "median_wall_ms": statistics.median(r["wall_ms"] for r in results),
        "runs": results,
    }


def _fmt_ms(value: float | None) -> str:
    return "n/a" if value is None else f"{value:,.0f} ms"


def render(measurements: list[dict[str, Any]], machine: dict[str, str]) -> str:
    rows = [
        f"| {m['label']} | {m['shell']} | {m['bundle_bytes'] / 1e6:,.1f} MB | "
        f"{_fmt_ms(m['first_launch_ms'])} | {_fmt_ms(m['median_launch_ms'])} | "
        f"{_fmt_ms(m['median_wall_ms'])} | {'pass' if m['passed'] else '**FAIL**'} |"
        for m in measurements
    ]
    labels = [m["label"] for m in measurements]
    checklist = [f"| {check} |" + " [ ] |" * len(labels) for check in MANUAL_CHECKS]
    failures = [
        f"- {m['label']}, run {i + 1}: exit {r['exit_code']}; "
        f"{json.dumps((r.get('result') or {}).get('page', r.get('error', 'no output')))[:400]}"
        for m in measurements
        for i, r in enumerate(m["runs"])
        if r["exit_code"] != 0
    ]
    lines = [
        "# M0 shell spike report",
        "",
        f"Generated {machine['date']} by scripts/spike.sh on macOS {machine['macos']} "
        f"({machine['machine']}), Python {machine['python']}. See ADR-0001.",
        "",
        "| App | Shell | .app size | First launch to self-test pass | Median | "
        "Median wall (to exit) | Self-test |",
        "|---|---|---|---|---|---|---|",
        *rows,
        "",
        "Launch time is from process start to the page's self-test report arriving in Python",
        "(page loaded, KaTeX and fonts rendered, MathLive mounted, bridge round trip). The",
        "first run follows the build, so it is the coldest measured; `sudo purge` first for a",
        "truly cold start. Both apps bundle the same core/ (SymPy etc.) and web UI.",
        "",
        "## Manual checks (fill in by hand, in each app)",
        "",
        "| Check | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
        *checklist,
        "",
        "## Failures",
        "",
        *(failures or ["None."]),
        "",
    ]
    return "\n".join(lines)


def machine_info() -> dict[str, str]:
    return {
        "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "macos": platform.mac_ver()[0] or platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--label", required=True)
    m.add_argument("--app", type=Path, required=True)
    m.add_argument("--runs", type=int, default=5)
    m.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("report")
    r.add_argument("measurements", type=Path, nargs="+")
    r.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "measure":
        result = measure(args.label, args.app, args.runs)
        args.out.write_text(json.dumps(result, indent=2))
        print(
            f"{args.label}: {result['bundle_bytes'] / 1e6:,.1f} MB, first launch "
            f"{_fmt_ms(result['first_launch_ms'])}, median {_fmt_ms(result['median_launch_ms'])}, "
            f"{'pass' if result['passed'] else 'FAIL'}"
        )
        return 0 if result["passed"] else 1
    data = [json.loads(p.read_text()) for p in args.measurements]
    args.out.write_text(render(data, machine_info()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
