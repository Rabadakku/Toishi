"""Write the build manifest from the built app's `--health` line (scripts/build.sh).

usage: dist/Toishi.app/Contents/MacOS/Toishi --health \
         | uv run python scripts/build_manifest.py --out dist/build-manifest.json

Records what the .app really bundles, read from the frozen app itself: its version, Python
and SQLite (DEV-7: the SQLite must have the WAL-reset fix). Exits 1, writing nothing, when
the health check failed or the line can't be read.
"""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

HEALTH_PREFIX = "HEALTH "
_SQLITE = re.compile(r"\bSQLite (\d+\.\d+\.\d+)\b")


class ManifestError(Exception):
    pass


def manifest(health_line: str, *, app_version: str) -> dict[str, Any]:
    if not health_line.startswith(HEALTH_PREFIX):
        raise ManifestError(f"not a HEALTH line: {health_line[:80]!r}")
    report = json.loads(health_line[len(HEALTH_PREFIX) :])
    checks = {c["name"]: c for c in report.get("checks", [])}
    failed = [f"{name}: {c['detail']}" for name, c in checks.items() if not c["ok"]]
    if failed or report.get("ok") is not True:
        raise ManifestError("the built app failed its health check: " + "; ".join(failed))
    found = _SQLITE.search(str(checks.get("sqlite", {}).get("detail", "")))
    if found is None:
        raise ManifestError("the health check did not report the SQLite version")
    return {
        "app_version": app_version,
        "python": checks["python"]["detail"],
        "sqlite": found.group(1),
        "checks": {name: c["detail"] for name, c in checks.items()},
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_manifest", description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import core

    lines = [line for line in sys.stdin.read().splitlines() if line.startswith(HEALTH_PREFIX)]
    try:
        if len(lines) != 1:
            raise ManifestError(f"expected one HEALTH line, got {len(lines)}")
        data = manifest(lines[0], app_version=core.version())
    except (ManifestError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"build manifest: SQLite {data['sqlite']}, Python {data['python']} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
