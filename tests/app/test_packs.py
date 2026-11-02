"""Shipped packs: compiled from packs/<id>/ for dev runs, bundled in the built .app."""

import os
import sys
from pathlib import Path

import pytest

from app import packs
from core.storage import read_pack_info


def test_dev_runs_compile_the_shipped_packs_once(tmp_path: Path) -> None:
    out = tmp_path / "packs"
    built = packs.shipped_packs(out_dir=out)
    assert [p.name for p in built] == ["test.db", "tutorial.db"]
    assert {read_pack_info(p).id for p in built} == {"test", "tutorial"}
    stamp = {p: p.stat().st_mtime_ns for p in built}
    assert packs.shipped_packs(out_dir=out) == built  # fresh: not rebuilt
    assert {p: p.stat().st_mtime_ns for p in built} == stamp
    assert not list(out.glob(".*partial"))


def test_stale_or_unreadable_databases_are_rebuilt(tmp_path: Path) -> None:
    folder = packs.source_dir("test")
    db = tmp_path / "test.db"
    assert packs.is_stale(db, folder)  # missing
    db.write_bytes(b"not a pack")
    assert packs.is_stale(db, folder)  # unreadable (an older format, say)
    built = packs.compile_pack(folder, tmp_path)
    assert not packs.is_stale(built, folder)
    os.utime(built, ns=(1, 1))
    assert packs.is_stale(built, folder)  # older than its sources


def test_the_built_app_uses_the_bundled_packs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "packs").mkdir()
    (tmp_path / "packs" / "test.db").write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert packs.shipped_packs() == [tmp_path / "packs" / "test.db"]


def test_the_spec_and_build_script_ship_the_packs() -> None:
    root = Path(__file__).parents[2]
    spec = (root / "packaging/Toishi.spec").read_text()
    build = (root / "scripts/build.sh").read_text()
    assert "PACKS" in spec
    assert "SHIPPED" in spec
    assert "mepack.py build" in build
