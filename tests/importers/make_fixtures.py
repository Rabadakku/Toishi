"""Builds the Anki fixture decks in tests/importers/fixtures with the official `anki` package
(AGPL, a dev-only dependency; ADR-0015). Run it again only to change the fixtures:

    uv run python -m tests.importers.make_fixtures

The decks cover: Basic, reversed, optional reversed, type-in, Cloze with several and nested
blanks, a custom note type with its own templates and CSS, media (images, audio, an
underscore font), the Mastery Problem note type, review history with and without FSRS
memory state, a .colpkg with its own rollover hour and UTC offset, and a plain-text export.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from anki.collection import Collection
from anki.import_export_pb2 import ExportAnkiPackageOptions, ExportLimit

FIXTURES = Path(__file__).parent / "fixtures"
DAY = 86_400_000
T0 = 1_788_256_800_000  # 2026-09-01T10:00:00Z
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360f8cfc0f01f0005fe02fea7d6a4c50000000049454e44ae426082"
)
FSRS_PARAMS = [
    0.2172, 1.1771, 3.2602, 16.1507, 7.0114, 0.57, 2.0966, 0.0069, 1.5261, 0.112, 1.0178,
    1.849, 0.1133, 0.3127, 2.2934, 0.2191, 3.0004, 0.7536, 0.3332, 0.1437, 0.2,
]  # fmt: skip


def _collection(folder: Path) -> Any:
    col: Any = Collection(str(folder / "collection.anki2"))
    col.media.write_data("pic.png", PNG)
    col.media.write_data("graph.png", PNG + b"graph")
    col.media.write_data("sound.mp3", b"ID3 not really audio")
    col.media.write_data("_font.woff", b"wOFF not really a font")
    col.media.write_data("_bg.png", PNG + b"bg")
    col.media.write_data("café.png", PNG + b"cafe")
    return col


def _note(col: Any, notetype: str, deck: str, fields: dict[str, str], tags: Any = ()) -> Any:
    model = col.models.by_name(notetype)
    assert model is not None, notetype
    note = col.new_note(model)
    for name, value in fields.items():
        note[name] = value
    note.tags = list(tags)
    col.add_note(note, col.decks.id(deck))
    return note.id


def _export(col: Any, out: Path, deck: str, *, legacy=False, scheduling=False) -> None:
    options = ExportAnkiPackageOptions(
        with_scheduling=scheduling, with_deck_configs=scheduling, with_media=True, legacy=legacy
    )
    limit = ExportLimit(deck_id=col.decks.id(deck, create=False))
    col.export_anki_package(out_path=str(out), options=options, limit=limit)


def basic(folder: Path) -> None:
    col: Any = _collection(folder)
    _note(
        col,
        "Basic",
        "Lang::Spanish",
        {"Front": 'Hola <img src="pic.png">', "Back": "Hello &amp; welcome<br>[sound:sound.mp3]"},
        ["greeting", "es::basics"],
    )
    _note(col, "Basic (and reversed card)", "Lang::Spanish", {"Front": "perro", "Back": "dog"})
    _note(
        col,
        "Basic (optional reversed card)",
        "Lang::Spanish",
        {"Front": "gato", "Back": "cat", "Add Reverse": "y"},
    )
    _note(
        col,
        "Basic (optional reversed card)",
        "Lang::Spanish",
        {"Front": "casa", "Back": "house", "Add Reverse": ""},
    )
    _note(col, "Basic (type in the answer)", "Lang::Spanish", {"Front": "2 + 2", "Back": "cuatro"})
    _note(
        col,
        "Basic",
        "Lang::Math",
        {
            "Front": '<b onclick="steal()">Square</b> \\(x^2\\)<script>alert(1)</script>',
            "Back": '<img src="café.png"> <a href="https://example.com">link</a>',
        },
    )
    _export(col, FIXTURES / "basic.apkg", "Lang")
    _export(col, FIXTURES / "basic-legacy.apkg", "Lang", legacy=True)
    col.export_note_csv(
        out_path=str(FIXTURES / "notes.txt"),
        limit=ExportLimit(deck_id=col.decks.id("Lang")),
        with_html=True,
        with_tags=True,
        with_deck=True,
        with_notetype=True,
        with_guid=True,
    )
    col.close()


def cloze(folder: Path) -> None:
    col: Any = _collection(folder)
    _note(
        col,
        "Cloze",
        "Geo",
        {
            "Text": "{{c1::Paris::city}} is the capital of {{c2::France}}.",
            "Back Extra": "<i>Europe</i>",
        },
        ["capitals"],
    )
    _note(col, "Cloze", "Geo", {"Text": "foo {{c1::bar {{c2::baz}}::qux}} and {{c3,4::both}}"})
    _note(
        col,
        "Cloze",
        "Geo",
        {"Text": "\\({{c1::x}}^2 + {{c2::\\frac{a}{b}}}\\) and \\(a}}b\\) <b>{{c3::bold}}</b>"},
    )
    plus = col.models.copy(col.models.by_name("Cloze"))
    plus["name"] = "Cloze+"
    col.models.add_field(plus, col.models.new_field("Source"))
    plus["tmpls"][0]["qfmt"] = "{{cloze:Text}}<div class=src>{{Source}}</div>"
    plus["tmpls"][0]["afmt"] = "{{cloze:Text}}<hr id=answer>{{Source}} {{cloze-only:Text}}"
    plus["css"] += ".src { font-size: 12px; }\n"
    col.models.update_dict(plus)
    _note(col, "Cloze+", "Geo", {"Text": "{{c1::Rome}} and {{c2::Madrid}}", "Source": "atlas"})
    _export(col, FIXTURES / "cloze.apkg", "Geo")
    col.close()


def custom(folder: Path) -> None:
    col: Any = _collection(folder)
    vocab = col.models.new("Vocab")
    for name in ("Word", "Meaning", "Example", "Audio"):
        col.models.add_field(vocab, col.models.new_field(name))
    recognize = col.models.new_template("Recognize")
    recognize["qfmt"] = (
        "<style>.word { font-size: 40px; }</style><div class=word>{{Word}}</div>"
        "{{#Example}}<div class=ex>{{hint:Example}}</div>{{/Example}}"
        "<script>document.title = 'pwned'</script>"
    )
    recognize["afmt"] = (
        "{{FrontSide}}<hr id=answer>{{Meaning}}<br>{{Audio}}<br>{{Tags}} | {{Deck}} | {{Card}}"
    )
    recall = col.models.new_template("Recall")
    recall["qfmt"] = "{{#Meaning}}{{text:Meaning}}{{/Meaning}}"
    recall["afmt"] = "{{FrontSide}}<hr id=answer>{{furigana:Word}} {{unknownfilter:Word}}"
    col.models.add_template(vocab, recognize)
    col.models.add_template(vocab, recall)
    vocab["css"] = (
        '@import url("https://evil.example/x.css");\n'
        '.card { font-family: "MyFont"; background: url(_bg.png); color: #222; }\n'
        '@font-face { font-family: MyFont; src: url("_font.woff"); }\n'
        ".nightMode .card { color: white; }\n.word { color: red; }\n"
        "@media (max-width: 600px) { .card .ex { display: none; } }\n"
    )
    col.models.add(vocab)
    _note(
        col,
        "Vocab",
        "Japanese::N5",
        {
            "Word": "日本[にほん]",
            "Meaning": "<b>Japan</b>",
            "Example": "日本に行く",
            "Audio": "[sound:sound.mp3]",
        },
        ["jp"],
    )
    _note(col, "Vocab", "Japanese::N5", {"Word": "猫[ねこ]", "Meaning": "", "Example": ""})
    _export(col, FIXTURES / "custom.apkg", "Japanese")
    col.close()


TOISHI_FIELDS = ("ID", "Kind", "Skill", "Uses", "Difficulty", "AnswerType", "Answer", "Options",
                  "Question", "Hints", "Solution", "CuedQuestion", "Wrong", "Calculator", "Source",
                  "License")  # fmt: skip


def mastery(folder: Path) -> None:
    col: Any = _collection(folder)
    nt = col.models.new("Mastery Problem")
    for name in TOISHI_FIELDS:
        col.models.add_field(nt, col.models.new_field(name))
    t = col.models.new_template("Problem")
    t["qfmt"] = "{{Question}}"
    t["afmt"] = "{{FrontSide}}<hr id=answer>{{Solution}}"
    col.models.add_template(nt, t)
    col.models.add(nt)
    base = {
        "Kind": "problem", "Skill": "alg.linear", "Difficulty": "2", "AnswerType": "number",
        "Calculator": "no", "Source": "original", "License": "personal",
    }  # fmt: skip
    _note(col, "Mastery Problem", "Algebra::Linear", base | {
        "ID": "anki.mp.001", "Answer": "3",
        "Question": 'Solve \\(2x + 1 = 7\\).<div>Give \\(x\\).</div><img src="graph.png">',
        "Hints": "Subtract 1 from both sides.<br>Divide by 2.",
        "Solution": "0. [alg.linear] Isolate: \\(2x = 6\\), so \\(x = 3\\).",
        "Wrong": "6 =&gt; forgot to divide by 2", "Options": "tolerance: 0",
    }, ["linear", "unit 1"])  # fmt: skip
    _note(col, "Mastery Problem", "Algebra::Linear", base | {
        "ID": "anki.mp.002", "Answer": "x +", "Question": "What is \\(1 + 1\\)?",
        "Solution": "0. [alg.linear] Add: \\(1 + 1 = 2\\).",
    })  # fmt: skip
    _note(col, "Mastery Problem", "Algebra::Linear", base | {"ID": "", "Question": "No id"})
    _export(col, FIXTURES / "mastery.apkg", "Algebra", legacy=True)
    col.close()


def _revlog(col: Any, cid: int, rows: list[tuple[int, int, int, int, int, int]]) -> None:
    """rows: (ms after T0, ease, ivl, last_ivl, factor, type)."""
    for offset, ease, ivl, last_ivl, factor, kind in rows:
        col.db.execute(
            "insert into revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type) "
            "values (?, ?, -1, ?, ?, ?, ?, ?, ?)",
            T0 + offset, cid, ease, ivl, last_ivl, factor, 8000, kind,
        )  # fmt: skip


def _card_state(col: Any, cid: int, **values: object) -> None:
    sets = ", ".join(f"{k} = ?" for k in values)
    col.db.execute(f"update cards set {sets} where id = ?", *values.values(), cid)  # noqa: S608


def history(folder: Path) -> None:
    col: Any = _collection(folder)
    conf = col.decks.add_config_returning_id("FSRS preset")
    config = col.decks.get_config(conf)
    config["fsrsParams6"] = FSRS_PARAMS
    config["desiredRetention"] = 0.85
    col.decks.update_config(config)
    fsrs_deck = col.decks.get(col.decks.id("Hist::FSRS"))
    fsrs_deck["conf"] = conf
    col.decks.save(fsrs_deck)
    nid = _note(col, "Basic (and reversed card)", "Hist::FSRS", {"Front": "uno", "Back": "one"})
    c1, c2 = (c.id for c in col.get_note(nid).cards())
    lrt = (T0 + 9 * DAY) // 1000
    data = {"pos": 1, "s": 12.5, "d": 5.2, "dr": 0.85, "decay": 0.2, "lrt": lrt}
    _card_state(col, c1, type=2, queue=2, ivl=12, due=40, factor=2500, reps=4, lapses=0,
                data=json.dumps(data))  # fmt: skip
    _revlog(
        col,
        c1,
        [
            (0, 3, -600, 0, 2500, 0),
            (600_000, 3, 1, -600, 2500, 0),
            (DAY + 3_600_000, 3, 4, 1, 2500, 1),
            (9 * DAY, 2, 12, 4, 2400, 1),
        ],
    )
    _card_state(col, c2, type=2, queue=2, ivl=9, due=38, factor=2500, reps=4, lapses=1)
    _revlog(
        col,
        c2,
        [
            (5_000, 1, -60, 0, 2500, 0),
            (300_000, 3, 1, -60, 2500, 0),
            (2 * DAY - 7 * 3_600_000, 3, 3, 1, 2500, 1),
            (6 * DAY - 9 * 3_600_000, 3, 9, 3, 2500, 1),
        ],
    )
    # SM-2 history: an SM-2 era review, cramming, a reset, then learning again.
    nid = _note(col, "Basic", "Hist::SM2", {"Front": "dos", "Back": "two"})
    c3 = col.get_note(nid).cards()[0].id
    _card_state(col, c3, type=2, queue=2, ivl=6, due=30, factor=2500, reps=5, lapses=0)
    _revlog(
        col,
        c3,
        [
            (-40 * DAY, 3, 5, 2, 2500, 1),
            (-35 * DAY, 3, 0, 0, 0, 3),
            (-30 * DAY, 0, 0, 5, 0, 4),
            (-29 * DAY, 1, -600, 0, 2500, 0),
            (-29 * DAY + 700_000, 3, 1, -600, 2500, 0),
            (-28 * DAY + 17 * 3_600_000, 3, 6, 1, 2500, 1),
        ],
    )
    # Day boundaries and manual rows: set due date (type 4, ease 0), rescheduled (type 5).
    nid = _note(col, "Basic", "Hist::SM2", {"Front": "tres", "Back": "three"})
    c4 = col.get_note(nid).cards()[0].id
    _card_state(col, c4, type=2, queue=2, ivl=4, due=20, factor=2300, reps=4, lapses=0)
    _revlog(col, c4, [(-10 * DAY - 7 * 3_600_000, 3, -600, 0, 2500, 0),   # 03:00 UTC
                      (-10 * DAY - 5 * 3_600_000, 3, 1, -600, 2500, 0),   # 05:00 UTC
                      (-9 * DAY - 8 * 3_600_000, 4, 3, 1, 2650, 1),       # 02:00 next day
                      (-8 * DAY, 0, 2, 3, 2650, 4), (-7 * DAY, 0, 5, 2, 2650, 5),
                      (-6 * DAY, 2, 4, 5, 2500, 1)])  # fmt: skip
    # An SM-2 card whose history never had a learning step (incomplete): seeded from SM-2.
    nid = _note(col, "Basic", "Hist::SM2", {"Front": "cuatro", "Back": "four"})
    c5 = col.get_note(nid).cards()[0].id
    _card_state(col, c5, type=2, queue=2, ivl=20, due=50, factor=2600, reps=3, lapses=0)
    _revlog(col, c5, [(-50 * DAY + 1000, 3, 8, 3, 2600, 1), (-30 * DAY + 1000, 3, 20, 8, 2600, 1)])
    _export(col, FIXTURES / "history.apkg", "Hist", scheduling=True)
    col.set_config("rollover", 6)
    col.set_config("localOffset", -300)  # UTC+5, minutes west
    col.export_collection_package(str(FIXTURES / "history.colpkg"), include_media=True,
                                  legacy=False)  # fmt: skip
    col.close()


def main() -> None:
    FIXTURES.mkdir(exist_ok=True)
    for build in (basic, cloze, custom, mastery, history):
        folder = Path(tempfile.mkdtemp())
        try:
            build(folder)
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    for path in sorted(FIXTURES.iterdir()):
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
