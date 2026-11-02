"""Builder of the frozen v2 pack fixture for pack schema v3.

    python -m tests.storage.v2_fixtures <pack_v2.sql>

pack_v2.sql is packs/test compiled into a sealed pack by the pack schema v2 code (commit
6bd20e0), written once so that v3 readers are tested on a pack v2 really wrote. The code
that wrote it is kept here to document what it holds; it only runs at v2.
"""

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
PACK_V2 = FIXTURES / "pack_v2.sql"


def write_pack_v2(out: Path) -> None:
    from core.cards import check_pack, read_meta, write_pack_db
    from core.cards.load import skills_in, sources_in
    from core.storage.schema import PACK_SCHEMA_VERSION

    assert PACK_SCHEMA_VERSION == 2, "this fixture must be written by pack schema v2"
    folder = ROOT / "packs" / "test"
    meta = read_meta((folder / "pack.json").read_text())
    build = check_pack(meta, sources_in(folder), skills_in(folder), built_at=1)
    assert build.ok, build.report()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.db"
        write_pack_db(path, build, 1)
        conn = sqlite3.connect(path)
        lines = list(conn.iterdump())
        conn.close()
    out.write_text(
        "-- Frozen sealed pack at pack schema v2 (packs/test), written by the v2 code\n"
        "-- (tests/storage/v2_fixtures.py). Never edit.\n" + "\n".join(lines) + "\n"
    )


if __name__ == "__main__":
    write_pack_v2(Path(sys.argv[1]))
