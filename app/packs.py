"""Shipped content packs: read-only pack databases attached to every profile (PACK-1).

- Built .app: `<bundle>/packs/<id>.db`, compiled by scripts/build.sh before PyInstaller
  (content-tools/mepack.py build, with the KaTeX check) and listed in the PyInstaller spec.
- Dev runs: compiled from `packs/<id>/` into `build/packs/<id>.db` when the database is
  missing, unreadable (an older pack format) or older than any of its source files.

`python -m app.packs --out DIR` compiles the shipped packs (no KaTeX check) for tests.
"""

import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHIPPED: tuple[str, ...] = ("test", "tutorial")  # pack folders under packs/, in attach order
DEV_BUILD_DIR = ROOT / "build" / "packs"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundled_dir() -> Path:
    """Where the built .app keeps its pack databases (PyInstaller puts datas in _MEIPASS)."""
    return Path(getattr(sys, "_MEIPASS", ROOT)) / "packs"


def source_dir(pack_id: str) -> Path:
    return ROOT / "packs" / pack_id


def _newest_source_ns(folder: Path) -> int:
    return max((p.stat().st_mtime_ns for p in folder.rglob("*") if p.is_file()), default=0)


def is_stale(db: Path, folder: Path) -> bool:
    """True when `db` must be (re)built from `folder`."""
    from core.storage import read_pack_info

    if not db.is_file():
        return True
    try:
        read_pack_info(db)
    except Exception:  # an older pack format or a broken file: rebuild it
        return True
    return db.stat().st_mtime_ns < _newest_source_ns(folder)


def compile_pack(folder: Path, out_dir: Path) -> Path:
    """Check a pack folder (every card's key self-checked) and write its sealed database.

    Written beside the target and renamed into place, so a crash never leaves half a pack.
    """
    from core.cards.load import skills_in, sources_in
    from core.cards.mepack import META, PackBuildError, check_pack, read_meta, write_pack_db

    meta = read_meta((folder / META).read_bytes(), str(folder / META))
    build = check_pack(meta, sources_in(folder), skills_in(folder))
    if not build.ok:
        raise PackBuildError(f"pack {folder} has errors:\n" + "\n".join(build.errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{meta.id}.db"
    partial = out_dir / f".{meta.id}.db.partial"
    built_at = _newest_source_ns(folder) // 1_000_000 or time.time_ns() // 1_000_000
    write_pack_db(partial, build, built_at, overwrite=True)
    partial.replace(target)
    return target


def shipped_packs(*, out_dir: Path | None = None, build: bool | None = None) -> list[Path]:
    """The pack databases to attach. In a built .app: those inside the bundle. In a dev run:
    `build/packs/`, compiled first where stale (pass build=False to skip compiling)."""
    if is_frozen() and out_dir is None:
        folder = bundled_dir()
        return [folder / f"{p}.db" for p in SHIPPED if (folder / f"{p}.db").is_file()]
    target = out_dir or DEV_BUILD_DIR
    paths: list[Path] = []
    for pack_id in SHIPPED:
        src = source_dir(pack_id)
        db = target / f"{pack_id}.db"
        if (build is None or build) and src.is_dir() and is_stale(db, src):
            db = compile_pack(src, target)
        if db.is_file():
            paths.append(db)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.packs", description="compile the shipped packs")
    parser.add_argument("--out", type=Path, default=DEV_BUILD_DIR)
    args = parser.parse_args(argv)
    from core import cards, grader

    try:
        for path in shipped_packs(out_dir=args.out, build=True):
            print(f"pack {path}")
    finally:
        cards.shutdown()
        grader.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
