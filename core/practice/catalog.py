"""The practice catalog: components, problems and courses from the loaded content (wave 2,
docs/design/wave2-integration.md section 3, `catalog.py`).

- **Components.** Every skill is a component (student-model design 2.1). A component is
  *background* when its id carries one of the skills files' background prefixes (alg., trig.,
  pre.: prerequisites from earlier courses, which may sit in a course's own "precalculus"
  sections) or when its skill belongs to no course's sections. Otherwise it is a course
  component of the course whose sections hold it.
- **Problems.** A `ProblemSpec` per gradable problem: an active `problem` card, or one part of a
  multi-part card (`card#part`). Its components are its skill first, then its uses and step
  tags, each once. A part with its own skill is a one-component problem of that skill; a part
  without one keeps the card's components less the other parts' own skills (the steps are the
  card's, and those parts report to their own skills). Find-the-error and which-method cards
  were served by the diagnosis flow, which is gone, so they are not in pools.
- **Courses.** A `core.plan.Course` per course: its skills in course order (unit, section, then
  prerequisites first), their requires, confusable pairs, example cards and pools, the
  background skills its skills require or its sections hold, and the pace standard of its pack.
  A pack without pace data (older packs, the student's own courses) gets a flat standard: every
  section at zero hours, so the whole course is introduced on its anchor day, and the course
  reports no standard hours (`has_pace` False).

The catalog is built from storage once and cached by `PracticeEngine` under a key of what it
was built from (packs, the student's own content); suspended and reported cards are passed to
the planner as unavailable instead, so marking a card does not rebuild the catalog.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from core.cards.components import components as card_components
from core.cards.components import wrong_component
from core.cards.standard_time import standard_minutes
from core.learner.types import ComponentId, ComponentInfo, ProblemSpec
from core.model import Card, CardPart, CardRef, Course, PackPace, Section, Skill, Unit
from core.plan.types import Course as PlanCourse
from core.plan.types import PaceStandard, SectionPace, SkillInfo
from core.storage import Storage
from core.storage.pack_store import USER_SOURCE

# Skills files mark prerequisites from earlier courses with these id prefixes (design 2.1).
BACKGROUND_PREFIXES = ("alg.", "trig.", "pre.")
FLAT_WEEKLY_HOURS = 1.0  # any positive rate: a flat standard has no hours to divide
DEFAULT_MINUTES_PER_STEP = PackPace().minutes_per_step


@dataclass(frozen=True, slots=True)
class SectionRef:
    """A section of a course in course order, with its standard hours (None: no pace data)."""

    deck: str
    title: str
    hours: float | None


@dataclass(frozen=True, slots=True)
class Textbook:
    """The textbook pointer under a problem: "OpenStax Calculus Volume 1" and "§4.3"."""

    book: str
    section: str


@dataclass(frozen=True, slots=True)
class CourseEntry:
    course: PlanCourse
    title: str
    sections: tuple[SectionRef, ...]
    has_pace: bool
    source: str  # the pack id holding the course, or "user"

    @property
    def course_id(self) -> str:
        return self.course.course_id

    def skill(self, skill_id: ComponentId) -> SkillInfo | None:
        return next((s for s in self.course.skills if s.skill_id == skill_id), None)


@dataclass(frozen=True, slots=True)
class Catalog:
    components: Mapping[ComponentId, ComponentInfo]
    courses: Mapping[str, CourseEntry]  # course id -> its plan course
    problems: Mapping[str, ProblemSpec]  # problem id -> spec
    by_card: Mapping[str, tuple[ProblemSpec, ...]]  # card id -> its problems (parts)
    skill_names: Mapping[ComponentId, str]
    skill_decks: Mapping[ComponentId, str]
    textbooks: Mapping[ComponentId, Textbook]
    examples: Mapping[ComponentId, str]  # skill -> its worked example card
    key: tuple[object, ...] = ()

    def course_of(self, skill_id: ComponentId) -> str | None:
        info = self.components.get(skill_id)
        return None if info is None else info.course_id

    def problem(self, card_id: str, part: str | None = None) -> ProblemSpec | None:
        key = card_id if part is None else f"{card_id}#{part}"
        return self.problems.get(key)

    def name(self, skill_id: ComponentId) -> str:
        return self.skill_names.get(skill_id, skill_id)


def is_background_id(skill_id: str) -> bool:
    return skill_id.startswith(BACKGROUND_PREFIXES)


def catalog_key(storage: Storage) -> tuple[object, ...]:
    """What a catalog is built from: the attached packs (by content hash) and the student's
    own courses, skills and cards (their ids, revisions and statuses)."""
    packs = tuple((p.id, p.content_hash, p.schema_version) for p in storage.packs.packs())
    with storage.db.reading() as conn:
        own = tuple(
            conn.execute(
                "SELECT (SELECT count(*) FROM user_course), (SELECT count(*) FROM user_section), "
                "(SELECT count(*) FROM user_skill), (SELECT count(*) FROM user_skill_edge), "
                "(SELECT count(*) FROM user_card), (SELECT coalesce(sum(rev), 0) FROM user_card), "
                "(SELECT count(*) FROM user_card WHERE status = 'retired')"
            ).fetchone()
        )
    return (packs, own)


def build_catalog(storage: Storage) -> Catalog:
    """Read every course, skill and problem card and build the catalog."""
    packs = storage.packs
    key = catalog_key(storage)
    courses = packs.courses()
    units = packs.units()
    sections = packs.sections()
    skills = {s.id: s for s in packs.skills()}
    refs = packs.card_refs()
    pace_of = {p.id: packs.pace(p.id) or PackPace() for p in packs.packs()}

    course_sections = _course_sections(courses, units, sections)
    section_course = {s.id: c for c, ss in course_sections.items() for s in ss}
    components: dict[ComponentId, ComponentInfo] = {}
    for skill in skills.values():
        holder = section_course.get(skill.section_id or "")
        background = is_background_id(skill.id) or holder is None
        components[skill.id] = ComponentInfo(skill.id, background, holder)

    # minutes per step per pack; the student's own cards use the default
    minutes = {source: pace.minutes_per_step for source, pace in pace_of.items()}
    problems: dict[str, ProblemSpec] = {}
    by_card: dict[str, tuple[ProblemSpec, ...]] = {}
    by_skill: dict[ComponentId, list[ProblemSpec]] = defaultdict(list)
    problem_refs: dict[str, list[CardRef]] = defaultdict(list)
    example_refs: dict[str, list[CardRef]] = defaultdict(list)
    for ref in refs:
        if ref.status != "active" or ref.skill_id is None:
            continue
        if ref.kind == "problem":
            problem_refs[ref.skill_id].append(ref)
        elif ref.kind == "example":
            example_refs[ref.skill_id].append(ref)
    for skill_id, group in sorted(problem_refs.items()):
        source_of = {r.id: r.source for r in group}
        for card in packs.cards_for_skill(skill_id):
            if card.id not in source_of or card.kind != "problem" or card.retired:
                continue
            m = minutes.get(source_of[card.id], DEFAULT_MINUTES_PER_STEP)
            specs = problem_specs(card, m)
            by_card[card.id] = specs
            for spec in specs:
                problems[spec.problem_id] = spec
                by_skill[spec.main_skill].append(spec)
    examples = {k: min(r.id for r in group) for k, group in example_refs.items()}

    entries: dict[str, CourseEntry] = {}
    sources = packs.course_sources()
    for course in courses:
        ordered = course_sections.get(course.id, ())
        source = sources.get(course.id, USER_SOURCE)
        pace = pace_of.get(source, PackPace())
        entries[course.id] = _course_entry(
            course, ordered, skills, components, by_skill, examples, pace, source
        )

    return Catalog(
        components=components,
        courses=entries,
        problems=problems,
        by_card=by_card,
        skill_names={k: s.name for k, s in skills.items()},
        skill_decks={k: s.deck or s.section_id or "" for k, s in skills.items()},
        textbooks=_textbooks(skills.values(), sections),
        examples=examples,
        key=key,
    )


def problem_specs(card: Card, minutes_per_step: float) -> tuple[ProblemSpec, ...]:
    """The gradable problems of one card: the card, or each of its parts."""
    family = card.template_id or card.id
    main = card.skill_id or card.id  # design 3.9: no skill tag, the card is its component
    steps = len(card.solution)
    whole = card_components(card) or (main,)
    if not card.parts:
        return (
            ProblemSpec(
                problem_id=card.id,
                card_id=card.id,
                part=None,
                main_skill=main,
                components=_unique((main, *whole)),
                tier=card.tier,
                steps=steps,
                standard_minutes=standard_minutes(card, minutes_per_step),
                wrong_components=_wrong(card, card.wrong, None),
                family=family,
            ),
        )
    own = {p.skill_id for p in card.parts if p.skill_id is not None}
    share = max(1, round(steps / len(card.parts))) if steps else 0
    out = []
    for part in card.parts:
        if part.skill_id is not None:
            parts_components: tuple[ComponentId, ...] = (part.skill_id,)
            part_main = part.skill_id
        else:
            part_main = main
            parts_components = _unique((main, *(k for k in whole if k not in own)))
        out.append(
            ProblemSpec(
                problem_id=f"{card.id}#{part.label}",
                card_id=card.id,
                part=part.label,
                main_skill=part_main,
                components=parts_components,
                tier=card.tier,
                steps=share,
                standard_minutes=standard_minutes(part, minutes_per_step, card=card),
                wrong_components=_wrong(card, part.wrong, part),
                family=family,
            )
        )
    return tuple(out)


def textbook_of(ref: str | None) -> Textbook | None:
    """ "OpenStax Calculus Vol 1 §4.3" -> book "OpenStax Calculus Vol 1", section "§4.3"; the
    first reference of a list ("A §1; B §2"). A reference of one word is a book alone."""
    if not ref or not ref.strip():
        return None
    first = ref.split(";", 1)[0].strip()
    book, _, section = first.rpartition(" ")
    if not book:
        return Textbook(book=first, section="")
    return Textbook(book=book.strip(), section=section.strip())


# ---------------------------------------------------------------------- internals


def _unique(values: Iterable[ComponentId]) -> tuple[ComponentId, ...]:
    return tuple(dict.fromkeys(values))


def _wrong(
    card: Card, wrong: Sequence[object], part: CardPart | None
) -> tuple[tuple[int, ComponentId], ...]:
    label = None if part is None else part.label
    out = []
    for index in range(len(wrong)):
        component = wrong_component(card, index, label)
        if component is not None:
            out.append((index, component))
    return tuple(out)


def _course_sections(
    courses: Sequence[Course], units: Sequence[Unit], sections: Sequence[Section]
) -> dict[str, tuple[Section, ...]]:
    """Each course's sections in course order: unit order, then section order."""
    unit_of = {u.id: u for u in units}
    out: dict[str, list[tuple[tuple[int, int, str], Section]]] = defaultdict(list)
    known = {c.id for c in courses}
    for section in sections:
        unit = unit_of.get(section.unit_id)
        if unit is None or unit.course_id not in known:
            continue
        out[unit.course_id].append(((unit.ord, section.ord, section.id), section))
    return {c: tuple(s for _, s in sorted(group, key=lambda x: x[0])) for c, group in out.items()}


def _course_entry(
    course: Course,
    sections: Sequence[Section],
    skills: Mapping[str, Skill],
    components: Mapping[ComponentId, ComponentInfo],
    by_skill: Mapping[ComponentId, Sequence[ProblemSpec]],
    examples: Mapping[ComponentId, str],
    pace: PackPace,
    source: str,
) -> CourseEntry:
    deck_order = {s.id: i for i, s in enumerate(sections)}
    own = [
        s for s in skills.values() if s.section_id in deck_order and not components[s.id].background
    ]
    ordered = _course_order(own, deck_order)
    background_ids = {
        r for s in own for r in s.requires if r in components and components[r].background
    } | {
        s.id for s in skills.values() if s.section_id in deck_order and components[s.id].background
    }
    infos: list[SkillInfo] = []
    for i, skill in enumerate(ordered):
        infos.append(_skill_info(skill, i, by_skill, examples, background=False))
    for j, skill_id in enumerate(sorted(background_ids)):
        infos.append(
            _skill_info(skills[skill_id], len(ordered) + j, by_skill, examples, background=True)
        )
    hours = {s.deck: s.hours for s in pace.sections}
    has_pace = bool(pace.sections) and pace.weekly_hours is not None
    if has_pace:
        standard = PaceStandard(
            sections=tuple(SectionPace(s.deck, s.hours) for s in pace.sections),
            weekly_hours=float(pace.weekly_hours or FLAT_WEEKLY_HOURS),
            minutes_per_step=pace.minutes_per_step,
        )
    else:
        standard = PaceStandard(
            sections=tuple(SectionPace(s.id, 0.0) for s in sections),
            weekly_hours=FLAT_WEEKLY_HOURS,
            minutes_per_step=pace.minutes_per_step,
        )
    refs = tuple(SectionRef(s.id, s.title, hours.get(s.id) if has_pace else None) for s in sections)
    return CourseEntry(
        course=PlanCourse(course_id=course.id, standard=standard, skills=tuple(infos)),
        title=course.title,
        sections=refs,
        has_pace=has_pace,
        source=source,
    )


def _course_order(own: Sequence[Skill], deck_order: Mapping[str, int]) -> list[Skill]:
    """Course order: by section, and inside a section prerequisites first (then by id)."""
    by_id = {s.id: s for s in own}
    placed: list[Skill] = []
    done: set[str] = set()

    def visit(skill: Skill, stack: set[str]) -> None:
        if skill.id in done or skill.id in stack:
            return
        stack.add(skill.id)
        for r in sorted(skill.requires):
            other = by_id.get(r)
            if other is not None and other.section_id == skill.section_id:
                visit(other, stack)
        stack.discard(skill.id)
        done.add(skill.id)
        placed.append(skill)

    for skill in sorted(own, key=lambda s: (deck_order[s.section_id or ""], s.id)):
        visit(skill, set())
    return sorted(placed, key=lambda s: deck_order[s.section_id or ""])  # stable within sections


def _skill_info(
    skill: Skill,
    order: int,
    by_skill: Mapping[ComponentId, Sequence[ProblemSpec]],
    examples: Mapping[ComponentId, str],
    *,
    background: bool,
) -> SkillInfo:
    return SkillInfo(
        skill_id=skill.id,
        deck=skill.deck or skill.section_id or "",
        order=order,
        requires=tuple(skill.requires),
        confusable=tuple(skill.confusable),
        example_card=examples.get(skill.id),
        pool=tuple(sorted(by_skill.get(skill.id, ()), key=lambda p: p.problem_id)),
        background=background,
    )


def _textbooks(skills: Iterable[Skill], sections: Iterable[Section]) -> dict[str, Textbook]:
    """Each skill's textbook pointer: its own `textbook:` line, else its section's."""
    section_ref = {s.id: s.textbook_ref for s in sections}
    out: dict[str, Textbook] = {}
    for skill in skills:
        found = textbook_of(skill.textbook_ref) or textbook_of(
            section_ref.get(skill.section_id or "")
        )
        if found is not None:
            out[skill.id] = found
    return out
