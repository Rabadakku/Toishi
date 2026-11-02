"""Builders of the frozen realistic v1 fixtures for the schema v2 migration (ADR-0011).

    python -m tests.storage.v1_cards <user_v1_cards.sql> <pack_v1.sql>

Both were written once by the schema v1 code (commit 16e73c8) through the real pipelines,
so they hold the v1 stop-gaps exactly as that code wrote them:

- user_v1_cards.sql: own cards imported twice from card files (fixed cards, templates with
  and without parameters and notes, a retired template, a hand-written card whose notes
  begin like the old parameter prefix, a card with an image), so template parameters sit in
  notes_md and template sources in the import log; and graded answers through the
  diagnosis hook (step, prerequisite and cued-twin checks, one resolved, one undone, a
  daily run's diagnostic checks), so check reasons sit in the attempts' extra JSON. The
  last answer created a check, so undoing it after the migration is tested too.
- pack_v1.sql: packs/test compiled into a sealed pack, instances' parameters in notes_md.

The code that wrote them is kept here to document what they hold; it only runs at v1.
"""

import sqlite3
import sys
import tempfile
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
FIXTURES = Path(__file__).parent / "fixtures"
USER_V1_CARDS = FIXTURES / "user_v1_cards.sql"
PACK_V1 = FIXTURES / "pack_v1.sql"
USER_APP_ID = 0x4D455553  # "MEUS" (core.storage.schema)
PACK_APP_ID = 0x4D45504B  # "MEPK"


def load_fixture(sql: Path, db: Path, *, app_id: int = USER_APP_ID, version: int = 1) -> Path:
    """Rebuild a frozen v1 database from its dump (a dump keeps no PRAGMAs: set them)."""
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(sql.read_text())
    conn.execute(f"PRAGMA user_version = {version}")
    conn.execute(f"PRAGMA application_id = {app_id}")
    conn.commit()
    conn.close()
    return db


DOUBLE = r"""
## Card mine.alg.fixed.001
skill: mine.alg.double
difficulty: 1
answer-type: number
answer: 2

### Question
What is \(1 + 1\)?

### Hints
1. Count.

### Solution
0. [mine.alg.double] Add: \(1 + 1 = 2\).

### Notes
template parameters: not a template, so these notes stay as written

## Card mine.alg.double.t01
skill: mine.alg.double
difficulty: 1
answer-type: number
vars: k = int(LOW, HIGH)
answer: 2*k

### Question
Double [[k]].

### Hints
1. Add it to itself.

### Solution
0. [mine.alg.double] Double: [[2*k]].

### Notes
Watch the sign.

A second paragraph of notes.

## Card mine.alg.const.t01
skill: mine.alg.double
difficulty: 1
answer-type: number
answer: 2 + 3

### Question
What is [[2 + 3]]?

### Hints
1. Add.

### Solution
0. [mine.alg.double] Add: [[2 + 3]].
"""

MULTIPLY = r"""
## Card mine.alg.mul.t01
skill: mine.alg.multiply
difficulty: 2
answer-type: number
vars: a = int(2, 3); b = choice(1/2, 3)
answer: a*b

### Question
Multiply [[a]] by [[b]].

### Hints
1. Multiply.

### Solution
0. [mine.alg.multiply] Multiply: [[a*b]].
"""

GEOMETRY = r"""
## Card mine.geo.tri.001
skill: mine.geo.area
difficulty: 2
answer-type: number
answer: 6

### Question
![a right triangle with legs 3 and 4](media/tri.svg)
What is the area of the triangle?

### Hints
1. Half the base times the height.

### Solution
0. [mine.geo.area] Area: \(\tfrac12 \cdot 3 \cdot 4 = 6\).
"""

HEADER = "---\nformat: mastery-cards 1\ndeck: Mine::{deck}\n---\n"


def card_file(deck: str, *bodies: str) -> str:
    return HEADER.format(deck=deck) + "\n" + "\n".join(b.strip("\n") + "\n" for b in bodies)


def write_user_v1(out: Path) -> None:
    from core.cards import Source, apply_import, plan_import
    from core.engine import ProblemOutcome
    from core.engine.diagnosis import Diagnosis
    from core.model import Course, GradedAnswer, ImportRecord, PackInfo, Section, Unit
    from core.storage import Storage, build_pack
    from core.storage.clock import FixedClock
    from core.storage.profiles import ProfilePaths
    from core.storage.schema import USER_SCHEMA_VERSION
    from tests.engine.diagnosis.fixtures import ALG, CRIT, POW, PROD, SKILLS, answer, cards, seed
    from tests.engine.diagnosis.memory import MemoryWorld
    from tests.engine.diagnosis.test_weakspots import alg_gap

    assert USER_SCHEMA_VERSION == 1, "this fixture must be written by schema v1"
    clock = FixedClock(datetime(2026, 9, 1, 12, tzinfo=NY), tz=NY)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pack = root / "c.db"
        sections = sorted({k.section_id for k in SKILLS if k.section_id})
        build_pack(
            pack,
            PackInfo(id="c", title="Calc", version="1", built_at=1),
            [
                Course(id="c", title="Calc"),
                Unit(id="c.u", course_id="c", title="U"),
                *(Section(id=s, unit_id="c.u", title=s, ord=i) for i, s in enumerate(sections)),
                *SKILLS,
                *cards(),
            ],
        )
        paths = ProfilePaths(root / "p")
        storage = Storage.open(paths, pack_paths=[pack], clock=clock, create=True)
        users = storage.users
        users.set_setting("study.timezone", "America/New_York")

        # ---- own cards: two imports of the algebra file, one of the geometry file
        files = root / "cards"
        (files / "media").mkdir(parents=True)
        (files / "media" / "tri.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        algebra = files / "algebra.cards.md"
        algebra.write_text(
            card_file("Algebra", DOUBLE.replace("LOW", "1").replace("HIGH", "3"), MULTIPLY)
        )
        (files / "geometry.cards.md").write_text(card_file("Geometry", GEOMETRY))
        first = plan_import(
            users, [Source.from_path(algebra), Source.from_path(files / "geometry.cards.md")]
        )
        assert first.rejected == [], first.report()
        assert first.file_problems == [], first.report()
        apply_import(users, first)
        clock.advance(minutes=10)
        users.log_import(
            # an import of another kind: its summary has no template sources
            ImportRecord(file="deck.apkg", kind="apkg", summary={"added": 3, "files": {"x": {}}})
        )
        clock.advance(minutes=10)
        algebra.write_text(card_file("Algebra", DOUBLE.replace("LOW", "2").replace("HIGH", "4")))
        second = plan_import(users, [Source.from_path(algebra)])
        assert second.rejected == [], second.report()
        assert second.missing == ["mine.alg.mul.t01"], second.report()
        apply_import(users, second, retire=["mine.alg.mul.t01"])
        clock.advance(minutes=10)

        # ---- graded answers through the diagnosis hook
        mem = MemoryWorld(SKILLS, [])
        now = clock.now_ms()
        seed(mem, ALG, stability=2, days_ago=20, at=now, theta=0.0)  # low recall
        seed(mem, POW, stability=30, days_ago=3, at=now, theta=2.0)
        seed(mem, CRIT, stability=20, days_ago=25, at=now, theta=1.0)
        seed(mem, PROD, stability=20, days_ago=25, at=now, theta=1.0)
        users.apply(list(mem.states.values()))
        diag = Diagnosis(storage)
        engine = diag.engine()

        def outcome(card: str, **kw: object) -> ProblemOutcome:
            world = MemoryWorld(SKILLS, [storage.packs.card(card)])  # type: ignore[list-item]
            return answer(world, card, clock.now_ms(), **kw)  # type: ignore[arg-type]

        # a step tap on Differentiate: a step check on the power rule (reason in extra)
        engine.grade(outcome("crit.t2.0", correct=False, choice="step", step=1))
        (step_check,) = users.pending_checks()
        clock.advance(minutes=5)
        # the check fails: prerequisite checks (reasons in the check attempt's extra)
        engine.grade(
            outcome(step_check.card_id, correct=False, check_of=step_check.id)  # type: ignore[arg-type]
        )
        clock.advance(minutes=5)
        # a miss that is undone: its check and its attempt's extra go with it
        engine.grade(outcome("c.prod.t2.1", correct=False, choice="setup"))
        users.undo_last_answer()
        clock.advance(days=1)
        # the daily run: diagnostic checks, no reason stored anywhere
        for a in alg_gap():
            shifted = replace(a, id=None, at=clock.now_ms() - 3600_000, study_day=None)
            users.record_answer(GradedAnswer(attempt=shifted))
        diag.daily(clock.now_ms())
        clock.advance(minutes=5)
        # last: a cued-twin check from a setup miss (undone after the migration in a test)
        engine.grade(outcome("c.prod.t2.2", correct=False, choice="setup"))
        storage.close(backup=False)
        conn = sqlite3.connect(paths.user_db)
        reasons = conn.execute(
            "SELECT count(*) FROM attempt WHERE json_extract(extra, '$.diagnosis.checks') "
            "IS NOT NULL"
        ).fetchone()[0]
        kinds = sorted({r[0] for r in conn.execute("SELECT kind FROM pending_check")})
        lines = list(conn.iterdump())
        conn.close()
    assert reasons >= 3, reasons
    assert kinds == ["cued-twin", "diagnostic", "prerequisite", "step"], kinds
    out.write_text(
        "-- Frozen user.db at schema v1, written by the v1 code (tests/storage/v1_cards.py).\n"
        "-- Never edit.\n" + "\n".join(lines) + "\n"
    )


def write_pack_v1(out: Path) -> None:
    from core.cards import check_pack, read_meta, write_pack_db
    from core.cards.load import skills_in, sources_in
    from core.storage.schema import PACK_SCHEMA_VERSION

    assert PACK_SCHEMA_VERSION == 1, "this fixture must be written by pack schema v1"
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
        "-- Frozen sealed pack at pack schema v1 (packs/test), written by the v1 code\n"
        "-- (tests/storage/v1_cards.py). Never edit.\n" + "\n".join(lines) + "\n"
    )


if __name__ == "__main__":
    write_user_v1(Path(sys.argv[1]))
    write_pack_v1(Path(sys.argv[2]))
