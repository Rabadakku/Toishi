"""Content packs: the Test pack and the Answer Input Tutorial build and pass every check."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from core.cards import answer_spec, check_pack, compile_mepack, read_mepack, read_meta, self_check
from core.cards.load import Source, skills_in, sources_in
from core.cards.mepack import (
    PackBuild,
    PackBuildError,
    PackMeta,
    source_members,
    write_mepack,
    write_pack_db,
)
from core.model import PackInfo, PackPace
from core.storage import PACK_SCHEMA_VERSION, PackReader, Storage
from core.storage.profiles import ProfilePaths
from tests.storage.data import some
from tests.storage.v1_cards import PACK_APP_ID, PACK_V1, load_fixture
from tests.storage.v2_fixtures import PACK_V2

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "packs"
BUILT_AT = 1_793_577_600_000


def cli() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mepack_cli", ROOT / "content-tools" / "mepack.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class Built:
    result: PackBuild
    mepack: Path
    manifest: dict[str, Any]
    info: PackInfo
    db: Path


def build(folder: Path, out: Path, previous: Path | None = None) -> Built:
    meta = read_meta((folder / "pack.json").read_bytes())
    result = check_pack(
        meta, sources_in(folder), skills_in(folder), previous=previous, built_at=BUILT_AT
    )
    assert result.ok, result.report()
    out.mkdir(parents=True, exist_ok=True)
    mepack = out / f"{meta.id}-{meta.version}.mepack"
    manifest = write_mepack(mepack, result, source_members(folder), BUILT_AT)
    db = out / f"{meta.id}.db"
    info = write_pack_db(db, result, BUILT_AT, overwrite=True)
    return Built(result, mepack, manifest, info, db)


@pytest.fixture(scope="module")
def test_pack(tmp_path_factory: pytest.TempPathFactory) -> Built:
    return build(PACKS / "test", tmp_path_factory.mktemp("test-pack"))


@pytest.fixture(scope="module")
def tutorial(tmp_path_factory: pytest.TempPathFactory) -> Built:
    return build(PACKS / "tutorial", tmp_path_factory.mktemp("tutorial"))


def test_test_pack_exercises_every_kind_and_answer_type(test_pack: Built) -> None:
    result = test_pack.result
    cards = result.cards
    assert {c.kind for c in cards} == {
        "problem",
        "example",
        "flashcard",
        "cloze",
        "find-error",
        "method",
    }
    types = {c.answer_type for c in cards} | {p.answer_type for c in cards for p in c.parts}
    assert types == {
        "number",
        "expression",
        "equation",
        "antiderivative",
        "set",
        "list",
        "interval",
        "point",
        "vector",
        "matrix",
        "choice",
        "truefalse",
        "text",
        "self",
    }  # fmt: skip  (quantity arrives in 1.1: the checker rejects it)
    assert len({c.template_id for c in cards if c.template_id}) == 3
    assert any(c.parts for c in cards)
    assert any(c.cued_question_md for c in cards)
    assert any(c.alternative_solution for c in cards)
    assert any(c.plot for c in cards)
    assert any(c.calculator and c.angles == "degrees" for c in cards)
    assert {c.section_id for c in cards} == {
        "Test Course::1 Algebra::1.1 Linear Equations",
        "Test Course::1 Algebra::1.2 Quadratics",
        "Test Course::2 Calculus::2.1 Derivatives",
    }
    assert all(c.solution for c in cards if c.kind not in {"flashcard", "cloze"})


def test_test_pack_graph(test_pack: Built) -> None:
    result = test_pack.result
    skills = {s.id: s for s in result.skills}
    assert len(skills) == 13
    assert result.graph is not None
    assert result.graph.removed == [("test.alg.quadratic-solve", "test.alg.arithmetic")]
    assert skills["test.alg.quadratic-solve"].requires == (
        "test.alg.factor-quadratic",
        "test.alg.linear-solve",
    )
    method = skills["test.alg.choose-quadratic-method"]
    assert method.method_choice
    assert method.requires == (
        "test.alg.factor-quadratic",
        "test.alg.quadratic-formula",
    )
    assert skills["test.calc.critical-points"].encompasses == (("test.calc.power-rule", 1.0),)
    assert {p.skill_id for p in result.pool} == set(skills)


def test_pack_database_matches_and_every_key_checks(test_pack: Built, tutorial: Built) -> None:
    for built in (test_pack, tutorial):
        result, info = built.result, built.info
        with PackReader(built.db) as reader:
            assert reader.verify()
            assert reader.info.version == "1.0.0"
            assert reader.info.built_at == BUILT_AT
            stored = {c.id: c for c in reader.content.cards()}
            assert stored == {c.id: c for c in result.cards}
            assert {s.id for s in reader.content.skills()} == {s.id for s in result.skills}
            for card in stored.values():
                assert self_check(card) == [], card.id  # read back from the pack, still self-checks
            if info.id == "test":
                assert reader.media_names() == ["media/parabola.svg"]
                assert stored["test.linear.solve.001"].verified == "self-check"
                assert all(c.verified == "template+cas" for c in stored.values() if c.template_id)


def test_tutorial_keys(tutorial: Built) -> None:
    result = tutorial.result
    answers = {c.id: (c.answer_type, c.answer) for c in result.cards}
    assert answers == {
        "tutorial.fractions.001": ("number", "3/4"),
        "tutorial.fractions.002": ("expression", "(x + 1)/(x - 1)"),
        "tutorial.roots.001": ("number", "sqrt(2)"),
        "tutorial.roots.002": ("expression", "root(x, 3)"),
        "tutorial.powers.001": ("expression", "x^10"),
        "tutorial.powers.002": ("expression", "e^(2x)"),
        "tutorial.infinity.001": ("number", "inf"),
        "tutorial.infinity.002": ("number", "-inf"),
        "tutorial.dne.001": ("number", "DNE"),
        "tutorial.equations.001": ("equation", "y = 2x + 1"),
        "tutorial.intervals.001": ("interval", "[1, 3)"),
        "tutorial.intervals.002": ("interval", "(-inf, 2]"),
        "tutorial.unions.001": ("interval", "(-inf, 0) U (1, inf)"),
        "tutorial.points.001": ("point", "(1, -2)"),
        "tutorial.sets.001": ("set", "-1, 2"),
        "tutorial.sets.002": ("set", "none"),
    }


@pytest.mark.parametrize(
    ("card_id", "typed", "status"),
    [
        ("tutorial.fractions.001", "3/4", "correct"),
        ("tutorial.fractions.001", "6/8", "correct"),
        ("tutorial.fractions.002", "x + 1/x - 1", "incorrect"),
        ("tutorial.roots.001", "2^(1/2)", "correct"),
        ("tutorial.roots.002", "x^(1/3)", "correct"),
        ("tutorial.powers.002", "e^2x", "incorrect"),
        ("tutorial.intervals.001", "1 <= x < 3", "correct"),
        ("tutorial.unions.001", "x < 0 or x > 1", "correct"),
        ("tutorial.sets.001", "{2, -1}", "correct"),
        ("tutorial.equations.001", "2x - y + 1 = 0", "correct"),
        ("tutorial.infinity.002", "inf", "incorrect"),
    ],
)
def test_tutorial_accepts_what_it_teaches(
    tutorial: Built, card_id: str, typed: str, status: str
) -> None:
    from core.grader import grade

    card = next(c for c in tutorial.result.cards if c.id == card_id)
    assert grade(typed, answer_spec(card)).status.value == status


def test_mepack_manifest_and_credits(test_pack: Built) -> None:
    result, mepack, manifest = test_pack.result, test_pack.mepack, test_pack.manifest
    assert manifest["id"] == "test"
    assert manifest["version"] == "1.0.0"
    assert manifest["format"] == 1
    assert manifest["courses"] == [{"id": "Test Course", "title": "Test Course"}]
    assert manifest["built_at"] == BUILT_AT
    assert manifest["pipeline"].startswith("toishi")
    assert manifest["licenses"] == {"personal": len(result.cards)}
    with zipfile.ZipFile(mepack) as zf:
        names = sorted(zf.namelist())
        credits = json.loads(zf.read("credits.json"))
    assert names == [
        "1-1-linear.cards.md", "1-2-quadratics.cards.md", "2-1-derivatives.cards.md",
        "credits.json", "manifest.json", "media/parabola.svg", "skills.md",
    ]  # fmt: skip
    assert sum(s["cards"] for s in credits["sources"]) == len(
        {c.template_id or c.id for c in result.cards}
    )


def test_compiling_the_mepack_reproduces_the_database(test_pack: Built, tmp_path: Path) -> None:
    again, _ = compile_mepack(test_pack.mepack, tmp_path / "again.db")
    assert again.content_hash == test_pack.info.content_hash


def _rezip(src: Path, dst: Path, change: dict[str, bytes | None]) -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for item in zin.infolist():
            if item.filename in change:
                continue
            zout.writestr(item, zin.read(item))
        for name, data in change.items():
            if data is not None:
                zout.writestr(name, data)


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"1-1-linear.cards.md": b"tampered"}, "content hash does not match"),
        ({"../evil.cards.md": b"x"}, "unsafe member name"),
        ({"run.py": b"print(1)"}, "unexpected file 'run.py'"),
        ({"media/x.js": b"alert(1)"}, "unexpected file 'media/x.js'"),
        ({"manifest.json": None}, "no manifest.json"),
    ],
)
def test_bad_mepacks_are_refused(
    test_pack: Built, tmp_path: Path, change: dict[str, bytes | None], fragment: str
) -> None:
    bad = tmp_path / "bad.mepack"
    _rezip(test_pack.mepack, bad, change)
    with pytest.raises(PackBuildError, match=fragment.replace("(", r"\(")):
        read_mepack(bad)


def test_a_new_version_keeps_ids_and_records_changes(test_pack: Built, tmp_path: Path) -> None:
    old_db = test_pack.db
    src = tmp_path / "v2"
    shutil.copytree(PACKS / "test", src)
    meta = json.loads((src / "pack.json").read_text())
    meta["version"] = "1.0.1"
    (src / "pack.json").write_text(json.dumps(meta))
    linear = src / "1-1-linear.cards.md"
    text = linear.read_text().replace("Solve \\(3x + 5 = 20\\).", "Solve \\(3x + 5 = 23\\).")
    text = text.replace("answer: 5\nwrong: 25/3", "answer: 6\nwrong: 28/3")
    text = text.replace("Subtract 5: \\(3x = 15\\)", "Subtract 5: \\(3x = 18\\)").replace(
        "\\(x = 5\\).\n\n<!-- equation", "\\(x = 6\\).\n\n<!-- equation"
    )
    start = text.index("<!-- truefalse -->")
    end = text.index("<!-- text -->")
    linear.write_text(text[:start] + text[end:])
    result = build(src, tmp_path / "out", previous=old_db).result
    cards = {c.id: c for c in result.cards}
    assert cards["test.linear.solve.001"].rev == 2
    assert cards["test.linear.solve.001"].answer == "6"
    assert cards["test.linear.check.001"].status == "retired"  # removed from the sources, kept
    assert cards["test.linear.line.001"].rev == 1
    notes = {(r.card_id, r.rev): (r.note, r.answer_changed) for r in result.revisions}
    assert notes[("test.linear.solve.001", 2)] == ("answer key updated in 1.0.1", True)
    assert notes[("test.linear.solve.001", 1)] == ("added in 1.0.0", False)


PACK_CARD = """---
format: mastery-cards 1
deck: P::U::S
license: personal
---

## Card p.001
skill: p.a
difficulty: 1
answer-type: number
answer: 2

### Question
Q \\(1 + 1\\)

### Hints
1. H

### Solution
0. [p.a] Add: \\(2\\).
"""
PACK_SKILLS = "---\nformat: mastery-skills 1\ndeck: P::U::S\n---\n\n## Skill p.a\nname: A\n"
CYCLE = "requires: p.b\n\n## Skill p.b\nname: B\nrequires: p.a\n"
METHOD = "kind: method\nanswer-type: choice\n\n### Choices\n- [x] A\n- [ ] B"


def check(cards: str = PACK_CARD, skills: str | None = PACK_SKILLS) -> list[str]:
    meta = PackMeta("p", "P", "1.0.0", "personal")
    skill_sources = [Source("skills.md", skills)] if skills is not None else []
    return check_pack(meta, [Source("p.cards.md", cards)], skill_sources, built_at=BUILT_AT).errors


@pytest.mark.parametrize(
    ("cards", "skills", "fragment"),
    [
        (PACK_CARD, PACK_SKILLS, None),
        (PACK_CARD, None, "a content pack needs skills.md"),
        (PACK_CARD.replace("p.a", "p.b"), PACK_SKILLS, "skills not in skills.md: p.b"),
        (PACK_CARD.replace("license: personal\n", ""), PACK_SKILLS, "pack cards need a license"),
        (PACK_CARD.replace("deck: P::U::S\n", ""), PACK_SKILLS, "pack cards need a deck"),
        (PACK_CARD.replace("0. [p.a] Add: \\(2\\).", "It is \\(2\\)."), PACK_SKILLS, "skill-tagged steps"),  # noqa: E501
        (PACK_CARD, PACK_SKILLS + "requires: p.zz\n", "requires: unknown skill p.zz"),
        (PACK_CARD, PACK_SKILLS + CYCLE, "prerequisites form a cycle"),
        (PACK_CARD.replace("answer-type: number\nanswer: 2", METHOD), PACK_SKILLS, "method-choice skill"),  # noqa: E501
    ],
)  # fmt: skip
def test_pack_rules(cards: str, skills: str | None, fragment: str | None) -> None:
    errors = check(cards, skills)
    if fragment is None:
        assert errors == []
    else:
        assert any(fragment in e for e in errors), errors


# ---------------------------------------------------------------- the component rule

TWO_SKILLS = PACK_SKILLS + "\n## Skill p.b\nname: B\n"
STEPS = "0. [p.a] Add: \\(2\\)."
PARTS_CARD = """---
format: mastery-cards 1
deck: P::U::S
license: personal
---

## Card p.parts.001
skill: p.a
difficulty: 2

### Question
Q

### Part a
answer-type: number
answer: 2
What is \\(1 + 1\\)?

### Part b
answer-type: number
answer: 3
skill: p.b
What is \\(1 + 2\\)?

### Hints
1. H

### Solution
0. [p.a] Add: \\(1 + 1 = 2\\).
1. [p.b] Add: \\(1 + 2 = 3\\).
"""


def pack_build(cards: str, skills: str = TWO_SKILLS) -> PackBuild:
    meta = PackMeta("p", "P", "1.0.0", "personal")
    return check_pack(
        meta, [Source("p.cards.md", cards)], [Source("skills.md", skills)], built_at=BUILT_AT
    )


@pytest.mark.parametrize(
    ("cards", "error"),
    [
        (PACK_CARD.replace(STEPS, "0. [p.b] Add: \\(2\\)."), "p.cards.md:8: step tags not in skill or uses: p.b"),  # noqa: E501
        (PACK_CARD.replace(STEPS, STEPS + "\n1. [p.b] Check: \\(2\\)."), "p.cards.md:8: step tags not in skill or uses: p.b"),  # noqa: E501
        (PACK_CARD.replace("skill: p.a\n", "skill: p.a\nuses: p.b\n"), "p.cards.md:9: uses: no solution step is tagged p.b"),  # noqa: E501
        (PARTS_CARD.replace("1. [p.b]", "1. [p.a]"), "p.cards.md:22: ### Part b: no solution step is tagged p.b"),  # noqa: E501
    ],
)  # fmt: skip
def test_pack_problems_must_agree_with_their_step_tags(cards: str, error: str) -> None:
    """A problem's components are its skill, its uses and its step tags: every step tag is
    declared, every uses entry and part skill is the tag of a step. A pack build stops on
    any disagreement."""
    build = pack_build(cards)
    assert not build.ok
    assert any(e.endswith(error) for e in build.errors), build.errors


def test_the_component_rule_passes_agreeing_cards_and_counts_part_skills() -> None:
    agreeing = PACK_CARD.replace("skill: p.a\n", "skill: p.a\nuses: p.b\n").replace(
        STEPS, STEPS + "\n1. [p.b] Check: \\(2\\)."
    )
    assert pack_build(agreeing).errors == []
    build = pack_build(PARTS_CARD)  # part b's skill tags step 1 without being in uses
    assert build.errors == []
    assert not any("tagged" in w or "step tags" in w for w in build.warnings)


def test_the_component_rule_only_warns_for_other_kinds_in_packs() -> None:
    example = PACK_CARD.replace("difficulty: 1\nanswer-type: number\nanswer: 2", "kind: example")
    example = example.replace("### Hints\n1. H\n\n", "").replace(STEPS, "0. [p.b] Add: \\(2\\).")
    build = pack_build(example)
    assert build.errors == []
    assert any(w.endswith("step tags not in skill or uses: p.b") for w in build.warnings)


def test_the_report_lists_missing_wrong_answers_and_steps() -> None:
    """Student-model spec 2.3: tier 2+ problems list their common wrong answers, each
    tied to a step. Gaps are reported, not errors (only an author knows what's common)."""
    tier2 = PACK_CARD.replace("difficulty: 1", "difficulty: 2")
    build = pack_build(tier2)
    assert build.ok
    assert build.wrong_answers == ["p.cards.md:7: card p.001: tier 2, no wrong: line"]
    assert "wrong answers: p.cards.md:7: card p.001: tier 2, no wrong: line" in build.report()
    assert (
        "wrong answers: answers of tier 2+ problems with a wrong: line 0/1, "
        "wrong answers without @step 0"
    ) in build.checks
    listed = tier2.replace("answer: 2", "answer: 2\nwrong: 3 => Add again. @0; 1 => Count.")
    assert pack_build(listed).wrong_answers == [
        "p.cards.md:7: card p.001: wrong answer '1' has no @step"
    ]
    assert pack_build(PACK_CARD).wrong_answers == []  # a tier 1 drill needs none
    self_graded = tier2.replace("answer-type: number\nanswer: 2\n", "")
    assert pack_build(self_graded).wrong_answers == []  # nothing to match a wrong answer to


def test_the_wrong_answer_report_looks_at_each_part_and_each_template_once() -> None:
    build = pack_build(PARTS_CARD.replace("answer: 2\n", "answer: 2\nwrong: 3 => Add. @0\n"))
    assert build.wrong_answers == ["p.cards.md:7: card p.parts.001 part b: tier 2, no wrong: line"]
    template = PACK_CARD.replace("difficulty: 1", "difficulty: 2").replace(
        "answer: 2", "vars: k = int(1, 3)\nanswer: k + 1\nwrong: k => Add one."
    )
    build = pack_build(template.replace("Q \\(1 + 1\\)", "Q \\([[k]] + 1\\)"))
    assert len(build.cards) == 3
    (line,) = build.wrong_answers
    assert line.startswith("p.cards.md:7: card p.001: wrong answer ")
    assert line.endswith(" has no @step")


@pytest.mark.parametrize(
    ("cards", "error"),
    [
        (PACK_CARD.replace("answer: 2", "answer: 2\nwrong: 3 => No. @4"), "wrong answer '3' points at @4, but there is no step 4 in ### Solution"),  # noqa: E501
        (PARTS_CARD.replace("answer: 3\n", "answer: 3\nwrong: 4 => No. @7\n"), "### Part b: wrong answer '4' points at @7, but there is no step 7"),  # noqa: E501
    ],
)  # fmt: skip
def test_a_wrong_answers_step_must_be_a_solution_step(cards: str, error: str) -> None:
    """Already a rule of every import (core.cards.cardfile); a pack build stops on it."""
    build = pack_build(cards)
    assert not build.ok
    assert any(error in e for e in build.errors), build.errors


def test_standard_times_go_into_the_pack_database(tmp_path: Path) -> None:
    timed = PARTS_CARD.replace("difficulty: 2", "difficulty: 2\ntime: 5")
    build = pack_build(timed.replace("answer: 3\n", "answer: 3\ntime: 1.5\n"))
    assert build.ok, build.errors
    (card,) = build.cards
    assert (card.time_minutes, [p.time_minutes for p in card.parts]) == (5.0, [None, 1.5])
    db = tmp_path / "p.db"
    write_pack_db(db, build, BUILT_AT)
    with PackReader(db) as pack:
        assert pack.content.card(card.id) == card
        assert pack.verify()


def test_a_template_problem_that_breaks_the_component_rule_is_rejected_once() -> None:
    template = PACK_CARD.replace("answer: 2", "vars: k = int(1, 3)\nanswer: k + 1").replace(
        "skill: p.a\n", "skill: p.a\nuses: p.b\n"
    )
    build = pack_build(template.replace("Q \\(1 + 1\\)", "Q \\([[k]] + 1\\)"))
    tagged = [e for e in build.errors if "no solution step is tagged p.b" in e]
    assert len(tagged) == 1, build.errors
    assert build.cards == []


# ---------------------------------------------------------------- content-tools


def katex_available() -> bool:
    return shutil.which("node") is not None and cli().katex_dir() is not None


@pytest.mark.skipif(
    not katex_available(), reason="needs node and web/node_modules/katex (or TOISHI_KATEX_DIR)"
)
def test_katex_strict_renders_every_card(test_pack: Built, tutorial: Built) -> None:
    tools = cli()
    assert tools.render_check(test_pack.result.cards + tutorial.result.cards) == []
    broken = test_pack.result.cards[0]
    from dataclasses import replace

    bad = replace(broken, question_md="See \\(\\notacommand{x}\\) and \\(\\frac{1}{2}\\)")
    (error,) = tools.render_check([bad])
    assert error.startswith(f"KaTeX: {broken.id}: question: \\notacommand")
    assert "Undefined control sequence" in error


def test_cli_check_and_build(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    script = str(ROOT / "content-tools" / "mepack.py")
    out = subprocess.run(
        [sys.executable, script, "check", str(PACKS / "tutorial"), "--no-render"],
        capture_output=True, text=True, check=False, env=env, cwd=ROOT, timeout=300,
    )  # fmt: skip
    assert out.returncode == 0, out.stdout + out.stderr
    assert "pack tutorial 1.0.0: 16 cards, 10 skills" in out.stdout
    assert out.stdout.rstrip().endswith("OK")
    out = subprocess.run(
        [sys.executable, script, "build", str(PACKS / "tutorial"), "--no-render",
         "--out", str(tmp_path), "--built-at", str(BUILT_AT)],
        capture_output=True, text=True, check=False, env=env, cwd=ROOT, timeout=300,
    )  # fmt: skip
    assert out.returncode == 0, out.stdout + out.stderr
    assert (tmp_path / "tutorial-1.0.0.mepack").is_file()
    assert (tmp_path / "tutorial.db").is_file()


# Cards of packs/test whose sources changed after the v1 freeze: what the v1 pack holds.
# test.deriv.power.001 listed test.calc.limits in uses, a skill only its alternative solution
# uses; the component rule (a uses entry must tag a solution step) dropped it.
CHANGED_AFTER_V1: dict[str, dict[str, Any]] = {
    "test.deriv.power.001": {"uses": ("test.calc.limits",)},
}


def test_v1_packs_read_back_exactly_like_new_packs(tmp_path: Path) -> None:
    """Packs are never migrated (ADR-0009). packs/test as the v1 builder sealed it (its
    instances' parameters in notes_md) reads back card for card like the pack built from
    the same sources today, and a rebuild against it keeps every revision (PACK-2); a card
    changed since the freeze (CHANGED_AFTER_V1) reads back as it was and gets a new one."""
    v1 = load_fixture(PACK_V1, tmp_path / "v1" / "test.db", app_id=PACK_APP_ID)
    v1.chmod(0o444)
    folder = PACKS / "test"
    meta = read_meta((folder / "pack.json").read_bytes())
    built = check_pack(meta, sources_in(folder), skills_in(folder), built_at=1)
    today = tmp_path / "today" / "test.db"
    today.parent.mkdir()
    write_pack_db(today, built, 1)
    with PackReader(v1) as old, PackReader(today) as new:
        assert (old.info.schema_version, new.info.schema_version) == (1, PACK_SCHEMA_VERSION)
        assert old.verify()
        assert new.verify()
        assert old.pace() == new.pace() == PackPace()  # packs/test sets no pace standard
        # The pack may gain cards after the v1 freeze: newer cards are skipped, never v1 ones.
        frozen = {c.id for c in old.content.cards()}
        cards = [c for c in new.content.cards() if c.id in frozen]
        held = [replace(c, **CHANGED_AFTER_V1.get(c.id, {})) for c in cards]  # as v1 holds them
        assert old.content.cards() == held
        instances = [c for c in cards if c.template_id is not None]
        assert len(instances) > 20
        assert all(c.params is not None for c in instances)
        assert not any((c.notes_md or "").startswith("template parameters") for c in cards)
        stored = old._conn.execute("SELECT notes_md FROM card WHERE template_id IS NOT NULL")
        assert all(r[0].startswith("template parameters: ") for r in stored)  # what v1 wrote
        assert old.content.skills() == new.content.skills()
        assert old.content.edges() == new.content.edges()
        assert old.content.courses() == new.content.courses()
        assert old.content.sections() == new.content.sections()
        for card in cards:
            assert old.content.revisions(card.id) == new.content.revisions(card.id)
        assert old.content.card_refs() == [r for r in new.content.card_refs() if r.id in frozen]
        assert old.media_names() == new.media_names() == ["media/parabola.svg"]
        assert old.media("media/parabola.svg") == new.media("media/parabola.svg")
    again = check_pack(meta, sources_in(folder), skills_in(folder), previous=v1, built_at=2)
    assert [(c.id, c.rev) for c in again.cards] == [
        (c.id, c.rev + (c.id in CHANGED_AFTER_V1)) for c in built.cards
    ]
    notes: list[str] = []
    for r in built.revisions:
        notes.append(r.note)
        if r.card_id in CHANGED_AFTER_V1:
            notes.append(f"content updated in {meta.version}")
    assert [r.note for r in again.revisions] == notes
    with Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=[v1], create=True) as storage:
        assert storage.packs.card(instances[0].id) == instances[0]  # attached, read as new
        assert storage.packs.cards_for_skill(some(instances[0].skill_id)) == [
            c for c in held if c.skill_id == instances[0].skill_id and c.status == "active"
        ]


def test_v2_packs_read_back_exactly_like_v3_packs(tmp_path: Path) -> None:
    """Pack schema v3 only adds pack-only tables (card_time, pace, pace_section). packs/test
    as the v2 builder sealed it reads back card for card like the pack built from the same
    sources today, with no standard times and the default pace standard; its hash still
    verifies, and a rebuild against it keeps every revision (PACK-2)."""
    v2 = load_fixture(PACK_V2, tmp_path / "v2" / "test.db", app_id=PACK_APP_ID, version=2)
    v2.chmod(0o444)
    folder = PACKS / "test"
    meta = read_meta((folder / "pack.json").read_bytes())
    built = check_pack(meta, sources_in(folder), skills_in(folder), built_at=1)
    today = tmp_path / "today" / "test.db"
    today.parent.mkdir()
    write_pack_db(today, built, 1)
    with PackReader(v2) as old, PackReader(today) as new:
        assert (old.info.schema_version, new.info.schema_version) == (2, PACK_SCHEMA_VERSION)
        assert old.verify()
        assert new.verify()
        frozen = {c.id for c in old.content.cards()}
        cards = [c for c in new.content.cards() if c.id in frozen]
        assert len(cards) == len(frozen) == 109
        assert old.content.cards() == cards
        assert all(c.time_minutes is None for c in cards)
        assert old.pace() == new.pace() == PackPace()
        assert old.content.skills() == new.content.skills()
        assert old.content.sections() == new.content.sections()
        assert old.content.card_refs() == [r for r in new.content.card_refs() if r.id in frozen]
    again = check_pack(meta, sources_in(folder), skills_in(folder), previous=v2, built_at=2)
    assert [(c.id, c.rev) for c in again.cards] == [(c.id, c.rev) for c in built.cards]
    with Storage.open(ProfilePaths(tmp_path / "p"), pack_paths=[v2], create=True) as storage:
        assert storage.packs.card(cards[0].id) == cards[0]  # attached, read as new
        assert storage.packs.pace(meta.id) == PackPace()
