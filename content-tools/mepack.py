"""Content pipeline CLI: check, render-check and build content packs. Never shipped.

    uv run python content-tools/mepack.py check   packs/test             # load + all checks
    uv run python content-tools/mepack.py build   packs/test --out build/packs
    uv run python content-tools/mepack.py compile build/packs/test-1.0.0.mepack --out test.db

`check` and `build` run every card through the import validator in content-pack mode
(step tags, decks, licenses, known skills, a DAG, and the component rule: a problem's skill,
uses and step tags agree), expand templates, self-check every key, cross-check keys and
template results with a second engine (DEV-18), check worked solutions step by step and
their final lines against the keys (MATH-17; unverified steps are listed), check the skill
graph and report pool targets (GRAPH-4), report wrong-answer coverage and standard times that
fall back on a tier default, check the pace standard's sections against the pack's decks,
and render every piece of math with KaTeX in strict mode through node (web/node_modules/katex,
or --katex DIR). `build` writes <id>-<version>.mepack and the sealed pack database <id>.db.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.cards import checks, shutdown  # noqa: E402
from core.cards.load import skills_in, sources_in  # noqa: E402
from core.cards.mepack import (  # noqa: E402
    META,
    PackBuild,
    PackBuildError,
    check_pack,
    compile_mepack,
    read_meta,
    source_members,
    write_mepack,
    write_pack_db,
)
from core.grader import shutdown as grader_shutdown  # noqa: E402
from core.model import Card  # noqa: E402

KATEX_SCRIPT = Path(__file__).with_name("katex_check.mjs")


def katex_dir(explicit: str | None = None) -> Path | None:
    for candidate in (
        explicit,
        os.environ.get("TOISHI_KATEX_DIR"),
        str(ROOT / "web/node_modules/katex"),
    ):
        if candidate and (Path(candidate) / "package.json").is_file():
            return Path(candidate)
    return None


def render_check(cards: list[Card], katex: Path | None = None) -> list[str]:
    """KaTeX strict mode on every piece of math (questions, solutions, hints, steps, ...)."""
    node = shutil.which("node")
    katex = katex or katex_dir()
    if node is None or katex is None:
        return ["KaTeX check needs node and web/node_modules/katex (npm --prefix web ci)"]
    items: list[dict[str, object]] = []
    for card in cards:
        for where, tex, display in checks.math_segments(card):
            items.append(
                {"id": f"{card.id}: {where}: {tex.strip()[:60]}", "tex": tex, "display": display}
            )
    if not items:
        return []
    payload = "\n".join(json.dumps(i) for i in items) + "\n"
    out = subprocess.run(
        [node, str(KATEX_SCRIPT), str(katex.resolve())],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if out.returncode != 0:
        return [f"KaTeX check failed to run: {out.stderr.strip()[:500]}"]
    return [f"KaTeX: {f['id']}: {f['error']}" for f in json.loads(out.stdout)]


def check_folder(
    folder: Path, *, render: bool, katex: Path | None = None, **kwargs: object
) -> PackBuild:
    meta = read_meta((folder / META).read_bytes(), str(folder / META))
    build = check_pack(meta, sources_in(folder), skills_in(folder), **kwargs)  # type: ignore[arg-type]
    if render:
        build.errors += render_check(build.cards, katex)
    return build


def _print(build: PackBuild) -> None:
    print(build.report())
    shapes: dict[str, int] = {}
    for c in build.cards:
        shapes[c.kind] = shapes.get(c.kind, 0) + 1
    print("kinds: " + ", ".join(f"{k} {v}" for k, v in sorted(shapes.items())))
    print("OK" if build.ok else f"FAILED: {len(build.errors)} errors")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mepack", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "build"):
        cmd = sub.add_parser(name)
        cmd.add_argument("folder", type=Path)
        cmd.add_argument("--no-render", action="store_true", help="skip the KaTeX check")
        cmd.add_argument("--katex", help="KaTeX package folder")
        cmd.add_argument("--previous", type=Path, help="the previous version's pack database")
        cmd.add_argument(
            "--built-at", type=int, help="build time in UTC ms (for reproducible builds)"
        )
        if name == "build":
            cmd.add_argument("--out", type=Path, required=True)
    comp = sub.add_parser("compile")
    comp.add_argument("mepack", type=Path)
    comp.add_argument("--out", type=Path, required=True)
    comp.add_argument("--previous", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "compile":
            info, build = compile_mepack(
                args.mepack, args.out, previous=args.previous, overwrite=True
            )
            _print(build)
            print(f"wrote {args.out} ({info.content_hash})")
            return 0
        katex = Path(args.katex) if args.katex else None
        build = check_folder(
            args.folder,
            render=not args.no_render,
            katex=katex,
            previous=args.previous,
            built_at=args.built_at,
        )
        _print(build)
        if not build.ok or args.command == "check":
            return 0 if build.ok else 1
        built_at = args.built_at if args.built_at is not None else time.time_ns() // 1_000_000
        out: Path = args.out
        out.mkdir(parents=True, exist_ok=True)
        members = source_members(args.folder)
        mepack = out / f"{build.meta.id}-{build.meta.version}.mepack"
        manifest = write_mepack(mepack, build, members, built_at)
        info = write_pack_db(out / f"{build.meta.id}.db", build, built_at, overwrite=True)
        print(f"wrote {mepack} ({manifest['content_hash']})")
        print(f"wrote {out / (build.meta.id + '.db')} ({info.content_hash})")
        return 0
    except (PackBuildError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        shutdown()
        grader_shutdown()


if __name__ == "__main__":
    sys.exit(main())
