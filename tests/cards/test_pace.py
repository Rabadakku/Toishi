"""The pace standard in the skills file (student-model spec 2.4 and 4.1): the pace- header
keys and ## Section blocks are read, checked, and carried into the built pack."""

from pathlib import Path

import pytest

from core.cards import Source, load
from core.cards.mepack import (
    PackBuild,
    PackMeta,
    check_pack,
    compile_mepack,
    write_mepack,
    write_pack_db,
)
from core.cards.skillfile import read_skills, read_skills_file
from core.model import PackPace, PackPaceSection
from core.storage import PackReader, Storage
from core.storage.profiles import ProfilePaths

FIRST = "C::1 Unit::1.1 First"
SECOND = "C::1 Unit::1.2 Second"
SKILLS = f"""---
format: mastery-skills 1
deck: {FIRST}
pace-minutes-per-step: 1.25
pace-weekly-hours: 4
---

## Section {FIRST}
hours: 6

## Skill p.a
name: A

## Skill p.b
name: B
deck: {SECOND}

## Section {SECOND}
hours: 2.5
"""
STANDARD = PackPace(
    minutes_per_step=1.25,
    weekly_hours=4.0,
    sections=(PackPaceSection(deck=FIRST, hours=6.0), PackPaceSection(deck=SECOND, hours=2.5)),
)
CARD = """
## Card p.00N
skill: p.X
difficulty: 1
answer-type: number
answer: 2

### Question
Q \\(1 + 1\\)

### Hints
1. H

### Solution
0. [p.X] Add: \\(2\\).
"""
CARDS = (
    f"---\nformat: mastery-cards 1\ndeck: {FIRST}\nlicense: personal\n---\n"
    + CARD.replace("00N", "001").replace("p.X", "p.a")
    + CARD.replace("00N", "002").replace("p.X", "p.b").replace("skill:", f"deck: {SECOND}\nskill:")
)


def line_of(text: str, marker: str) -> int:
    return next(i for i, line in enumerate(text.split("\n"), start=1) if marker in line)


# ---------------------------------------------------------------- reading skills.md


def test_the_pace_standard_is_read_in_course_order() -> None:
    entries, pace, problems = read_skills(SKILLS, "skills.md")
    assert problems == []
    assert [e.skill.id for e in entries] == ["p.a", "p.b"]  # skills read as before
    assert pace is not None
    assert (pace.file, pace.line, pace.minutes_per_step, pace.weekly_hours) == (
        "skills.md",
        4,
        1.25,
        4.0,
    )
    assert [(s.deck, s.hours, s.line) for s in pace.sections] == [
        (FIRST, 6.0, 8),
        (SECOND, 2.5, 18),
    ]
    assert pace.standard() == STANDARD
    assert read_skills_file(SKILLS, "skills.md") == (entries, problems)


def test_unset_pace_keys_take_the_defaults_and_paths_are_normalized() -> None:
    text = "---\nformat: mastery-skills 1\n---\n\n## Section  C :: 1 Unit :: 1.1 First \nhours: 3\n"
    _, pace, problems = read_skills(text, "skills.md")
    assert problems == []
    assert pace is not None
    assert pace.standard() == PackPace(sections=(PackPaceSection(deck=FIRST, hours=3.0),))
    assert pace.standard().minutes_per_step == 1.5
    _, none, _ = read_skills("---\nformat: mastery-skills 1\n---\n\n## Skill s.a\nname: A\n", "s")
    assert none is None


@pytest.mark.parametrize(
    ("change", "marker", "message"),
    [
        (("pace-weekly-hours: 4", "pace-weekly-hours: lots"), "pace-weekly-hours", "pace-weekly-hours: expected a positive number, got 'lots'"),  # noqa: E501
        (("pace-minutes-per-step: 1.25", "pace-minutes-per-step: 0"), "pace-minutes-per-step", "pace-minutes-per-step: expected a positive number, got '0'"),  # noqa: E501
        (("hours: 6", "hours: -6"), "hours: -6", "hours: expected a positive number, got '-6'"),
        (("hours: 6", "hours: 1e2"), "hours: 1e2", "hours: expected a positive number, got '1e2'"),
        (("hours: 6\n", ""), f"## Section {FIRST}", f"## Section {FIRST} has no hours:"),
        (("hours: 6", "hours: 6\nname: First"), "name: First", f"unknown key 'name' in ## Section {FIRST} (it takes hours: only)"),  # noqa: E501
        (("hours: 6", "hours: 6\n\n### Notes\nN"), "### Notes", f"unknown section '### Notes' in ## Section {FIRST}"),  # noqa: E501
        ((f"## Section {SECOND}", f"## Section {FIRST}"), "hours: 2.5", f"## Section {FIRST} appears twice (first at line 8)"),  # noqa: E501
        ((f"## Section {FIRST}", "## Section C::::S"), "## Section C", "## Section: empty level in 'C::::S'"),  # noqa: E501
        ((f"## Section {FIRST}", "## Section"), "## Section", "'## Section' needs a deck path"),
        ((f"## Section {FIRST}", "## Chapter 1"), "## Chapter", "unknown heading '## Chapter 1': blocks start with '## Skill <id>' or '## Section <deck path>'"),  # noqa: E501
    ],
)  # fmt: skip
def test_pace_mistakes_are_errors_on_their_line(
    change: tuple[str, str], marker: str, message: str
) -> None:
    text = SKILLS.replace(*change)
    _, _, problems = read_skills(text, "skills.md")
    line = line_of(text, marker) - (1 if "appears twice" in message else 0)
    assert [(p.line, p.message) for p in problems if p.is_error] == [(line, message)]


def test_a_broken_pace_header_rejects_the_whole_file() -> None:
    entries, pace, problems = read_skills(SKILLS.replace("hours: 4", "hours: four"), "s.md")
    assert (entries, pace) == ([], None)
    assert [p.line for p in problems] == [5]


# ---------------------------------------------------------------- loading


def test_personal_imports_ignore_the_pace_standard_with_a_warning() -> None:
    result = load([], [Source("skills.md", SKILLS)])
    assert result.pace is None
    assert [(w.line, w.message) for w in result.warnings] == [
        (4, "the pace standard (pace- keys, ## Section blocks) is for content packs only; "
            "ignored here")
    ]  # fmt: skip
    assert len(result.skills) == 2


def test_a_pack_takes_one_pace_standard() -> None:
    result = load([], [Source("skills.md", SKILLS)], pack=True)
    assert result.pace is not None
    assert result.pace.standard() == STANDARD
    assert result.warnings == []
    twice = load([], [Source("skills.md", SKILLS), Source("more.md", SKILLS)], pack=True)
    assert [(p.file, p.line, p.message) for p in twice.skill_problems] == [
        ("more.md", 4, "the pace standard is already set in skills.md")
    ]


# ---------------------------------------------------------------- the pack build


def build(skills: str = SKILLS) -> PackBuild:
    meta = PackMeta("p", "P", "1.0.0", "personal")
    return check_pack(
        meta, [Source("p.cards.md", CARDS)], [Source("skills.md", skills)], built_at=1
    )


def test_the_built_pack_carries_the_pace_standard(tmp_path: Path) -> None:
    built = build()
    assert built.ok, built.errors
    assert built.pace == STANDARD
    assert "pace: 1.25 minutes per step, 4 class hours a week, 2 sections, 8.5 hours" in (
        built.checks
    )
    db = tmp_path / "p.db"
    write_pack_db(db, built, 1)
    with PackReader(db) as pack:
        assert pack.pace() == STANDARD
        assert pack.verify()
    with Storage.open(ProfilePaths(tmp_path / "profile"), pack_paths=[db], create=True) as s:
        assert s.packs.pace("p") == STANDARD  # the loader the planner reads it with
    members = {"p.cards.md": CARDS.encode(), "skills.md": SKILLS.encode()}
    mepack = tmp_path / "p-1.0.0.mepack"
    write_mepack(mepack, built, members, 1)
    _, again = compile_mepack(mepack, tmp_path / "again.db")
    assert again.pace == STANDARD


def test_a_section_must_be_a_deck_of_the_pack() -> None:
    skills = SKILLS.replace(f"## Section {SECOND}", "## Section C::9 Elsewhere")
    built = build(skills)
    assert not built.ok
    assert built.errors == [
        "skills.md:18: ## Section C::9 Elsewhere: no card or skill has this deck"
    ]


def test_a_pack_without_a_pace_standard_gets_the_defaults(tmp_path: Path) -> None:
    plain = SKILLS.replace("pace-minutes-per-step: 1.25\npace-weekly-hours: 4\n", "")
    plain = plain.replace(f"## Section {FIRST}\nhours: 6\n", "").replace(
        f"## Section {SECOND}\nhours: 2.5\n", ""
    )
    built = build(plain)
    assert built.ok, built.errors
    assert built.pace == PackPace()
    assert not any(c.startswith("pace:") for c in built.checks)
    db = tmp_path / "plain.db"
    write_pack_db(db, built, 1)
    with PackReader(db) as pack:
        assert pack.pace() == PackPace()
