"""Export (EXP-1): the student's own cards and skills back to card files and a skills file
that re-import unchanged. Templates are written from their stored source text
(UserStore.template_sources()); their stored instances are not written, since re-import
makes them again. Images come from the profile's media store (`export_media`)."""

import posixpath
import re
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal

from core.cards.cardfile import FORMAT as CARDS_FORMAT
from core.cards.checks import checker_fields, format_wrong
from core.cards.skillfile import FORMAT as SKILLS_FORMAT
from core.model import Card, CardPart, Choice, Skill, SolutionStep
from core.storage.media import UserMedia, unsafe_name

UNVERIFIED = "unverified"


def _choices(items: Iterable[Choice]) -> list[str]:
    return [f"- [{'x' if c.correct else ' '}] {c.text_md}" for c in items]


def _steps(steps: Sequence[SolutionStep]) -> list[str]:
    out: list[str] = []
    for s in steps:
        body = f" {s.body_md}" if s.body_md else ""
        out.append(f"{s.number}. [{s.skill_id}] {s.label}:{body}")
    return out


def _section(name: str, lines: list[str] | str | None) -> list[str]:
    if lines is None or lines == [] or lines == "":
        return []
    body = lines.split("\n") if isinstance(lines, str) else lines
    return ["", f"### {name}", *body]


def decimal_text(value: float) -> str:
    """A positive number as `time:` takes it back: plain digits, no exponent (`2.5`, `6`)."""
    text = format(Decimal(repr(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _part(p: CardPart) -> list[str]:
    keys: list[str] = []
    if p.answer_type != "self":
        keys.append(f"answer-type: {p.answer_type}")
    if p.answer is not None:
        keys.append(f"answer: {p.answer}")
    if p.wrong:
        keys.append(f"wrong: {format_wrong(p.wrong)}")
    if p.skill_id:
        keys.append(f"skill: {p.skill_id}")
    if p.time_minutes is not None:
        keys.append(f"time: {decimal_text(p.time_minutes)}")
    keys += [f"{k}: {v}" for k, v in checker_fields(p.checker).items()]
    return ["", f"### Part {p.label}", *keys, *p.prompt_md.split("\n"), *_choices(p.choices)]


def card_block(card: Card, file_deck: str | None = None) -> str:
    keys: list[str] = [f"## Card {card.id}"]

    def key(name: str, value: object) -> None:
        if value is not None and value != "":
            keys.append(f"{name}: {value}")

    key("kind", card.kind if card.kind != "problem" else None)
    key("skill", card.skill_id)
    key("uses", ", ".join(card.uses) or None)
    key("difficulty", card.tier)
    key("time", decimal_text(card.time_minutes) if card.time_minutes is not None else None)
    key("answer-type", card.answer_type if card.answer_type != "self" else None)
    key("answer", card.answer)
    key("wrong", format_wrong(card.wrong) or None)
    for k, v in checker_fields(card.checker).items():
        key(k, v)
    key("plot", card.plot)
    key("calculator", "yes" if card.calculator else None)
    key("angles", card.angles if card.angles != "radians" else None)
    key("cue", "required" if card.cue_required else None)
    key("error-step", card.error_step)
    key("tagged", card.tagged)
    key("deck", card.deck if card.deck != file_deck else None)
    key("tags", ", ".join(card.tags) or None)
    p = card.provenance
    key("source", p.source)
    key("source-url", p.source_url)
    key("license", p.license)
    key("modified", "yes" if p.modified else None)
    key("verified", card.verified if card.verified != UNVERIFIED else None)
    lines = keys
    lines += _section("Question", card.question_md)
    lines += _section("Cued Question", card.cued_question_md)
    lines += _section("Choices", _choices(card.choices))
    lines += _section("Shown Work", _steps(card.shown_work))
    lines += _section("Reasons", _choices(card.reasons))
    for part in card.parts:
        lines += _part(part)
    lines += _section("Hints", [f"{i}. {h}" for i, h in enumerate(card.hints, start=1)])
    lines += _section("Answer", card.answer_md)
    lines += _section("Solution", _steps(card.solution) or card.solution_md)
    lines += _section("Rubric", [f"- [ ] {r}" for r in card.rubric])
    lines += _section(
        "Alternative Solution", _steps(card.alternative_solution) or card.alternative_solution_md
    )
    lines += _section("Front", card.front_md)
    lines += _section("Back", card.back_md)
    lines += _section("Text", card.text_md)
    lines += _section("Extra", card.extra_md)
    lines += _section("Notes", card.notes_md)
    return "\n".join(lines)


def _slug(deck: str | None) -> str:
    if not deck:
        return "cards"
    return re.sub(r"[^a-z0-9]+", "-", deck.lower()).strip("-") or "cards"


def export_cards(
    cards: Iterable[Card], templates: Mapping[str, str]
) -> tuple[dict[str, str], list[str]]:
    """Card files by deck: {file name: text}, plus warnings (a template whose source is gone)."""
    groups: dict[str | None, list[str]] = {}
    warnings: list[str] = []
    written_templates: set[str] = set()
    for card in sorted(cards, key=lambda c: c.id):
        if card.template_id is not None:
            tid = card.template_id
            if tid in written_templates:
                continue
            written_templates.add(tid)
            source = templates.get(tid)
            if source is None:
                warnings.append(f"template {tid}: its source is not stored; not exported")
                continue
            groups.setdefault(card.deck, []).append(source)
            continue
        groups.setdefault(card.deck, []).append(card_block(card, card.deck))
    files: dict[str, str] = {}
    for deck, blocks in groups.items():
        header = ["---", f"format: {CARDS_FORMAT}"] + ([f"deck: {deck}"] if deck else []) + ["---"]
        name = _slug(deck)
        stem, n = name, 2
        while f"{name}.cards.md" in files:
            name, n = f"{stem}-{n}", n + 1
        files[f"{name}.cards.md"] = "\n".join(header) + "\n\n" + "\n\n".join(blocks) + "\n"
    return files, warnings


def export_media(cards: Iterable[Card], media: UserMedia) -> tuple[dict[str, bytes], list[str]]:
    """The images the exported card files show: {path: bytes}, each at the path its
    reference names. Card files are written at the top of the export folder, so a
    reference that would leave it, or two different images at one path, are warnings."""
    files: dict[str, bytes] = {}
    warnings: list[str] = []
    for card in sorted(cards, key=lambda c: c.id):
        for ref, name in sorted(media.links(card.id).items()):
            path = posixpath.normpath(ref)
            data = media.read_file(name)
            if data is None:
                warnings.append(f"card {card.id}: image {ref} is missing from the media store")
            elif unsafe_name(path):
                warnings.append(f"card {card.id}: image {ref} is outside the export folder")
            elif files.setdefault(path, data) != data:
                warnings.append(f"card {card.id}: another image is already exported as {path}")
    return files, warnings


def _weight(w: float) -> str:
    return "1" if w == 1.0 else f"{w:g}"


def export_skills(skills: Iterable[Skill]) -> str:
    blocks: list[str] = []
    for s in sorted(skills, key=lambda s: s.id):
        lines = [f"## Skill {s.id}", f"name: {s.name}"]
        if s.deck:
            lines.append(f"deck: {s.deck}")
        if s.requires:
            lines.append(f"{'chooses' if s.method_choice else 'requires'}: {', '.join(s.requires)}")
        if s.encompasses:
            lines.append(
                "encompasses: " + "; ".join(f"{o} = {_weight(w)}" for o, w in s.encompasses)
            )
        if s.confusable:
            lines.append(f"confusable: {', '.join(s.confusable)}")
        if s.textbook_ref:
            lines.append(f"textbook: {s.textbook_ref}")
        if s.core:
            lines.append("core: yes")
        if s.exam_tier is not None:
            lines.append(f"exam-tier: {s.exam_tier}")
        if s.notes_md:
            lines += ["", "### Notes", *s.notes_md.split("\n")]
        blocks.append("\n".join(lines))
    return f"---\nformat: {SKILLS_FORMAT}\n---\n\n" + "\n\n".join(blocks) + "\n"
