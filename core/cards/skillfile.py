"""Skills files (`format: mastery-skills 1`, usually `skills.md`) -> core.model.Skill.

A skills file may also carry the course's pace standard (student-model spec 2.4 and
4.1): the header keys `pace-minutes-per-step` and `pace-weekly-hours`, and `## Section
<deck path>` blocks with `hours:`, in the order the course covers the sections. A content
pack stores it (core.cards.mepack); a personal import ignores it, with a warning.
"""

from dataclasses import dataclass, field

from core.cards import decks
from core.cards import text as t
from core.cards.problems import Problem
from core.model import (
    DEFAULT_MINUTES_PER_STEP,
    ENCOMPASS_WEIGHTS,
    PackPace,
    PackPaceSection,
    ShapeError,
    Skill,
)

FORMAT = "mastery-skills 1"
SKILL_KEYS = frozenset(
    {
        "name",
        "deck",
        "requires",
        "encompasses",
        "confusable",
        "textbook",
        "core",
        "exam-tier",
        "chooses",
    }
)
PACE_KEYS = ("pace-minutes-per-step", "pace-weekly-hours")
HEADER_KEYS = frozenset({"format", "deck", *PACE_KEYS})
SECTION = "Section"  # `## Section <deck path>`: a section's standard hours
SECTION_KEYS = frozenset({"hours"})


@dataclass(frozen=True, slots=True)
class SkillEntry:
    skill: Skill
    file: str
    line: int
    lines: dict[str, int] = field(default_factory=dict)  # key -> line, for graph errors
    chooses: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PaceEntry:
    """One `## Section <deck path>` block: that section's standard class hours."""

    deck: str  # the deck path
    hours: float
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class PaceSource:
    """A skills file's pace standard as written, with lines for the pack build's checks:
    the header values (None when not set) and the sections in file order (course order)."""

    file: str
    line: int  # its first pace key or ## Section block
    minutes_per_step: float | None = None
    weekly_hours: float | None = None
    sections: tuple[PaceEntry, ...] = ()

    def standard(self) -> PackPace:
        m = self.minutes_per_step
        sections = tuple(PackPaceSection(deck=s.deck, hours=s.hours) for s in self.sections)
        return PackPace(
            minutes_per_step=DEFAULT_MINUTES_PER_STEP if m is None else m,
            weekly_hours=self.weekly_hours,
            sections=sections,
        )


def read_skills_file(data: bytes | str, name: str) -> tuple[list[SkillEntry], list[Problem]]:
    """Every skill that has no errors, plus all problems (each with its line)."""
    entries, _, problems = read_skills(data, name)
    return entries, problems


def read_skills(
    data: bytes | str, name: str
) -> tuple[list[SkillEntry], PaceSource | None, list[Problem]]:
    """The skills that have no errors, the pace standard (None when the file sets none or
    its header is broken), and all problems (each with its line)."""
    src = t.read_file(data, name, "Skill", other_blocks={SECTION: "a deck path"})
    problems = list(src.problems)
    fmt = src.header.get("format")
    if fmt is not None and fmt.value != FORMAT:
        problems.append(
            Problem(name, fmt.line, f"format is {fmt.value!r}; this app reads {FORMAT!r}")
        )
    pace: dict[str, float] = {}
    for key, kl in src.header.items():
        if key not in HEADER_KEYS:
            problems.append(Problem(name, kl.line, f"unknown key {key!r} in the header"))
        elif key in PACE_KEYS:
            value = t.positive_decimal(kl.value)
            if value is None:
                problems.append(
                    Problem(name, kl.line, f"{key}: expected a positive number, got {kl.value!r}")
                )
            else:
                pace[key] = value
    if any(p.line < (src.blocks[0].line if src.blocks else 10**9) for p in problems):
        return [], None, problems  # a broken header: nothing in the file is trusted
    entries: list[SkillEntry] = []
    sections: list[PaceEntry] = []
    seen: dict[str, int] = {}
    seen_sections: dict[str, int] = {}
    for block in src.blocks:
        if not block.id:
            continue
        if block.kind == SECTION:
            section = _section(block, name, seen_sections, problems)
            if section is not None:
                sections.append(section)
            continue
        if block.id in seen:
            problems.append(
                Problem(
                    name,
                    block.line,
                    f"duplicate skill ID {block.id} (first at line {seen[block.id]})",
                    card_id=block.id,
                )
            )
            continue
        seen[block.id] = block.line
        if any(p.is_error and block.start < p.line <= block.end for p in problems):
            continue
        entry, found = _build(block, src.header, name)
        problems.extend(found)
        if entry is not None:
            entries.append(entry)
    starts = [src.header[k].line for k in pace] + [s.line for s in sections]
    if not starts:
        return entries, None, problems
    found_pace = PaceSource(
        file=name,
        line=min(starts),
        minutes_per_step=pace.get("pace-minutes-per-step"),
        weekly_hours=pace.get("pace-weekly-hours"),
        sections=tuple(sections),
    )
    return entries, found_pace, problems


def _section(
    block: t.BlockSrc, file: str, seen: dict[str, int], problems: list[Problem]
) -> PaceEntry | None:
    """A `## Section <deck path>` block: one section's standard hours (hours: only)."""
    before = len(problems)

    def error(line: int, message: str) -> None:
        problems.append(Problem(file, line, message))

    if any(p.is_error and block.start < p.line <= block.end for p in problems):
        return None  # a malformed line inside the block, already reported
    if any(not seg.strip() for seg in block.id.split(decks.SEPARATOR)):
        error(block.line, f"## Section: empty level in {block.id!r}")
        return None
    deck = decks.normalize(block.id)
    if deck in seen:
        error(block.line, f"## Section {deck} appears twice (first at line {seen[deck]})")
        return None
    seen[deck] = block.line
    for key, kl in block.keys.items():
        if key not in SECTION_KEYS:
            error(kl.line, f"unknown key {key!r} in ## Section {deck} (it takes hours: only)")
    for sec in block.sections:
        error(sec.line, f"unknown section '### {sec.name}' in ## Section {deck}")
    hours: float | None = None
    given = block.keys.get("hours")
    if given is None:
        error(block.line, f"## Section {deck} has no hours:")
    else:
        hours = t.positive_decimal(given.value)
        if hours is None:
            error(given.line, f"hours: expected a positive number, got {given.value!r}")
    if hours is None or len(problems) > before:
        return None
    return PaceEntry(deck, hours, file, block.line)


def _build(
    block: t.BlockSrc, header: dict[str, t.KeyLine], file: str
) -> tuple[SkillEntry | None, list[Problem]]:
    problems: list[Problem] = []

    def error(line: int, message: str) -> None:
        problems.append(Problem(file, line, message, card_id=block.id))

    keys = dict(block.keys)
    for key, kl in keys.items():
        if key not in SKILL_KEYS:
            error(kl.line, f"unknown key {key!r}")
    if "deck" not in keys and "deck" in header:
        keys["deck"] = header["deck"]
    lines = {k: kl.line for k, kl in keys.items()}

    def ids(key: str) -> tuple[str, ...]:
        kl = keys.get(key)
        if kl is None:
            return ()
        out: list[str] = []
        for raw in kl.value.split(","):
            item = raw.strip()
            if not t.CONTENT_ID.fullmatch(item):
                error(kl.line, f"{key}: bad skill ID {item!r}")
            elif item in out:
                error(kl.line, f"{key}: {item} is listed twice")
            elif item == block.id:
                error(kl.line, f"{key}: a skill can't point at itself")
            else:
                out.append(item)
        return tuple(out)

    name = keys.get("name")
    if name is None:
        error(block.line, f"skill {block.id} has no name")
    requires = ids("requires")
    chooses = ids("chooses")
    confusable = ids("confusable")
    encompasses: list[tuple[str, float]] = []
    if "encompasses" in keys:
        kl = keys["encompasses"]
        for raw in kl.value.split(";"):
            other, eq, weight = raw.partition("=")
            other = other.strip()
            if not eq or not t.CONTENT_ID.fullmatch(other):
                error(kl.line, f"encompasses: expected skill-id = weight, got {raw.strip()!r}")
                continue
            try:
                value = float(weight.strip())
            except ValueError:
                value = -1.0
            if value not in ENCOMPASS_WEIGHTS:
                error(
                    kl.line,
                    f"encompasses: weight for {other} must be 0.25, 0.5 or 1, "
                    f"got {weight.strip()!r}",
                )
            elif other == block.id:
                error(kl.line, "encompasses: a skill can't point at itself")
            elif any(o == other for o, _ in encompasses):
                error(kl.line, f"encompasses: {other} is listed twice")
            else:
                encompasses.append((other, value))
    core = False
    if "core" in keys:
        flag = keys["core"].value
        if flag not in {"yes", "no"}:
            error(keys["core"].line, f"core: expected yes or no, got {flag!r}")
        core = flag == "yes"
    exam_tier: int | None = None
    if "exam-tier" in keys:
        tier = keys["exam-tier"].value
        if tier not in {"1", "2", "3", "4", "5"}:
            error(keys["exam-tier"].line, f"exam-tier: expected 1 to 5, got {tier!r}")
        else:
            exam_tier = int(tier)
    deck = keys["deck"].value if "deck" in keys else None
    if deck is not None and any(not s.strip() for s in deck.split("::")):
        error(keys["deck"].line, f"deck: empty level in {deck!r}")
    elif deck is not None:
        deck = decks.normalize(deck)
    notes: str | None = None
    for sec in block.sections:
        if sec.name.lower() != "notes":
            error(sec.line, f"unknown section '### {sec.name}' (skills only have ### Notes)")
        else:
            notes = sec.text() or None
    if problems or name is None:
        return None, problems
    all_requires = requires + tuple(c for c in chooses if c not in requires)
    try:
        skill = Skill(
            id=block.id,
            name=name.value,
            deck=deck,
            section_id=deck,
            textbook_ref=keys["textbook"].value if "textbook" in keys else None,
            method_choice=bool(chooses),
            core=core,
            exam_tier=exam_tier,
            requires=all_requires,
            encompasses=tuple(encompasses),
            confusable=confusable,
            notes_md=notes,
        )
    except ShapeError as exc:
        error(block.line, str(exc))
        return None, problems
    return SkillEntry(skill, file, block.line, lines, chooses), problems
