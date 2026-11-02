"""Importing card files and skills files into the student's own content (IMP-1, -5, -7).

`plan_import` is the dry run: it loads and checks everything and compares it with
what the profile already has, writing nothing. `apply_import` writes the plan in one
transaction (UserStore.atomic): content, revisions, retirements and the import log.

- Same ID means update: the content changes, the revision goes up, review history stays;
  a changed answer key is recorded as "answer key updated" (PACK-2).
- Nothing is deleted. Cards that vanished from a file imported before are listed in
  `missing`; the student picks which to retire. Template instances a template no
  longer makes are retired with the import (they are listed in `retire_instances`).
- Imported cards are marked verified = "unverified" (IMP-7).
- The import log keeps, per file, the IDs it held (how `missing` is found). Each
  template's source text is stored with the student's templates (UserStore.user_template),
  which is how export (EXP-1) writes templates back and the editor opens them; logs from
  before schema v2 kept it in the log instead (`template_sources`, ADR-0011).
- The images cards show are stored in the profile's media store (UserStore.media), and
  each card's image references are pointed at them.
- `time:` standard times are kept by content packs only (user.db has no place for them):
  own cards import without them, with a warning.
"""

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from core.cards import decks
from core.cards.graph import check_graph
from core.cards.load import Accepted, LoadResult, Rejected, Source, TemplateInfo, load
from core.cards.problems import Problem
from core.cards.skillfile import SkillEntry
from core.cards.sweep import SweepRunner
from core.model import (
    Card,
    CardRevision,
    Course,
    ImportRecord,
    Section,
    Skill,
    TemplateSource,
    Unit,
)
from core.storage import UserStore
from core.storage.media import media_file_name
from core.storage.schema import v1_template_sources

UNVERIFIED = "unverified"
IMPORT_KIND = "cards"


@dataclass(frozen=True, slots=True)
class Change:
    card: Card  # what will be written (rev already set)
    old: Card | None
    key_changed: bool
    file: str
    line: int


@dataclass(slots=True)
class ImportPlan:
    added: list[Change] = field(default_factory=list)
    updated: list[Change] = field(default_factory=list)
    unchanged: list[Accepted] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    warnings: list[Problem] = field(default_factory=list)
    file_problems: list[Problem] = field(default_factory=list)
    skill_problems: list[Problem] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # card or template IDs; student decides
    retire_instances: list[str] = field(default_factory=list)  # retired with the import
    skills_added: list[Skill] = field(default_factory=list)
    skills_updated: list[Skill] = field(default_factory=list)
    skills_unchanged: list[Skill] = field(default_factory=list)
    skills_created: list[Skill] = field(default_factory=list)  # referenced, defined nowhere
    tree: list[Course | Unit | Section] = field(default_factory=list)
    templates: dict[str, TemplateInfo] = field(default_factory=dict)
    files: dict[str, list[str]] = field(default_factory=dict)
    template_instances: dict[str, list[str]] = field(default_factory=dict)  # stored, by template
    sources_changed: list[str] = field(default_factory=list)  # templates whose source is new
    media: dict[str, dict[str, bytes]] = field(default_factory=dict)  # card -> {ref: image}
    media_changed: list[str] = field(default_factory=list)  # cards whose images are new
    kind: str = IMPORT_KIND  # the import log's kind: cards, apkg, colpkg, anki-text
    extra: dict[str, Any] = field(default_factory=dict)  # more summary keys, from the importer

    @property
    def nothing_to_do(self) -> bool:
        return not (
            self.added
            or self.updated
            or self.retire_instances
            or self.skills_added
            or self.skills_updated
            or self.skills_created
            or self.sources_changed
            or self.media_changed
        )

    def summary(self) -> dict[str, Any]:
        return {
            "added": [c.card.id for c in self.added],
            "updated": [c.card.id for c in self.updated],
            "key_updated": [c.card.id for c in self.updated if c.key_changed],
            "unchanged": len(self.unchanged),
            "rejected": [
                {"file": r.file, "line": n, "card": r.card_id, "reason": reason}
                for r in self.rejected
                for n, reason in r.located()
            ],
            "missing": list(self.missing),
            "retired_instances": list(self.retire_instances),
            "skills": {
                "added": [s.id for s in self.skills_added],
                "updated": [s.id for s in self.skills_updated],
                "created": [s.id for s in self.skills_created],
            },
            "files": {
                name: {"ids": ids, "templates": [tid for tid in ids if tid in self.templates]}
                for name, ids in self.files.items()
            },
            "sources_changed": list(self.sources_changed),
            "media_changed": list(self.media_changed),
            **self.extra,
        }

    def report(self) -> str:
        """The dry-run report (IMP-5), one line per finding."""
        lines = [
            f"added: {len(self.added)}  updated: {len(self.updated)}  "
            f"unchanged: {len(self.unchanged)}  rejected: {len(self.rejected)}"
        ]
        lines += [f"updated {c.card.id}: answer key updated" for c in self.updated if c.key_changed]
        lines += [str(p) for p in self.file_problems + self.skill_problems]
        for r in self.rejected:
            who = r.card_id or "card"
            lines += [f"{r.file}:{n}: {who} rejected: {reason}" for n, reason in r.located()]
        lines += [str(w) for w in self.warnings]
        if self.missing:
            lines.append(
                "no longer in the file (choose whether to retire): " + ", ".join(self.missing)
            )
        if self.retire_instances:
            lines.append(f"template instances to retire: {len(self.retire_instances)}")
        if self.media_changed:
            lines.append(f"cards whose images are stored anew: {len(self.media_changed)}")
        return "\n".join(lines)


def key_signature(card: Card) -> tuple[Any, ...]:
    """What counts as the answer key: type, answer, checker options, marked choices."""

    def one(
        answer_type: str, answer: str | None, checker: Any, choices: Iterable[Any]
    ) -> tuple[Any, ...]:
        return (answer_type, answer, checker, tuple((c.text_md, c.correct) for c in choices))

    parts = tuple((p.label, one(p.answer_type, p.answer, p.checker, p.choices)) for p in card.parts)
    return (one(card.answer_type, card.answer, card.checker, card.choices), parts)


def _previous_ids(
    store: UserStore, names: Collection[str], kind: str = IMPORT_KIND
) -> dict[str, list[str]]:
    """For each file name, every ID it held in any earlier import of this kind (oldest
    first)."""
    found: dict[str, list[str]] = {}
    for record in sorted(store.imports(), key=lambda r: (r.at, r.id or 0)):
        if record.kind != kind:
            continue
        for name, info in (record.summary.get("files") or {}).items():
            if name in names and isinstance(info, dict):
                ids = found.setdefault(name, [])
                ids += [i for i in info.get("ids") or [] if i not in ids]
    return found


def template_sources(records: Iterable[ImportRecord]) -> dict[str, str]:
    """The latest source text of every template in import logs written before schema v2,
    which kept it there. The v2 migration moved it; export reads
    UserStore.template_sources() now."""
    out: dict[str, str] = {}
    for record in sorted(records, key=lambda r: (r.at, r.id or 0)):
        out.update(v1_template_sources(record.kind, record.summary))
    return out


def _referenced_skills(card: Card) -> list[str]:
    ids = [card.skill_id, *card.uses, *(p.skill_id for p in card.parts)]
    ids += [s.skill_id for s in (*card.solution, *card.alternative_solution, *card.shown_work)]
    return [i for i in ids if i]


def plan_import(
    store: UserStore,
    sources: Iterable[Source],
    skills: Iterable[Source] = (),
    *,
    pack_skills: Mapping[str, str] | None = None,
    pack_cards: Mapping[str, str] | None = None,
    runner: SweepRunner | None = None,
) -> ImportPlan:
    """Dry run. `pack_skills` / `pack_cards` map IDs already used by packs to the pack ID:
    own cards can't take a pack card's ID, and own skills can't redefine a pack skill."""
    loaded = load(sources, skills, runner=runner)
    return plan_loaded(store, loaded, pack_skills=pack_skills, pack_cards=pack_cards)


def plan_loaded(
    store: UserStore,
    loaded: LoadResult,
    *,
    pack_skills: Mapping[str, str] | None = None,
    pack_cards: Mapping[str, str] | None = None,
    kind: str = IMPORT_KIND,
) -> ImportPlan:
    """The dry run for cards already loaded and checked (`load`, or another importer that
    builds `Accepted` cards itself, such as core.importers.anki). `kind` names the import in
    the log; missing cards are looked for in earlier imports of the same kind and file."""
    pack_skills = pack_skills or {}
    pack_cards = pack_cards or {}
    plan = ImportPlan(
        rejected=list(loaded.rejected),
        warnings=list(loaded.warnings),
        file_problems=list(loaded.file_problems),
        skill_problems=list(loaded.skill_problems),
        files=loaded.files,
        kind=kind,
    )
    accepted, templates = _drop_pack_ids(loaded, pack_cards, plan)
    plan.templates = templates
    stored = {c.id: c for c in store.user_cards()}
    untimed: set[str] = set()  # cards and templates already warned about `time:`
    for item in accepted:
        card = item.card
        if card.time_minutes is not None or any(p.time_minutes is not None for p in card.parts):
            owner = card.template_id or card.id
            if owner not in untimed:
                untimed.add(owner)
                plan.warnings.append(
                    Problem(
                        item.file,
                        item.line,
                        "time: is kept by content packs only; this card imports without it",
                        "warning",
                        owner,
                    )
                )
            parts = tuple(replace(p, time_minutes=None) for p in card.parts)
            card = replace(card, time_minutes=None, parts=parts)
        if card.verified not in (None, UNVERIFIED) and card.template_id is None:
            plan.warnings.append(
                Problem(
                    item.file,
                    item.line,
                    f"verified: {card.verified} is ignored: imported cards are unverified",
                    "warning",
                    card.id,
                )
            )
        card = replace(card, verified=UNVERIFIED)
        old = stored.get(card.id)
        if old is None:
            plan.added.append(Change(replace(card, rev=1), None, False, item.file, item.line))
            continue
        same = replace(card, rev=old.rev, status=old.status)
        if same == old:
            plan.unchanged.append(Accepted(same, item.file, item.line))
            continue
        new = replace(card, rev=old.rev + 1, status=old.status)
        plan.updated.append(
            Change(new, old, key_signature(new) != key_signature(old), item.file, item.line)
        )
    _missing(store, plan, stored)
    stored_sources = store.template_sources()
    plan.sources_changed = [
        tid for tid, info in templates.items() if stored_sources.get(tid) != info.source
    ]
    _plan_media(store, plan, loaded, accepted)
    _plan_skills(store, plan, loaded.skills, accepted, pack_skills)
    all_decks = [c.card.deck for c in accepted] + [
        s.deck for s in plan.skills_added + plan.skills_updated
    ]
    all_decks += [s.deck for s in plan.skills_created]
    plan.tree = decks.tree(all_decks)
    return plan


def _drop_pack_ids(
    loaded: LoadResult, pack_cards: Mapping[str, str], plan: ImportPlan
) -> tuple[list[Accepted], dict[str, TemplateInfo]]:
    templates = dict(loaded.templates)
    clash: set[str] = set()
    for info in loaded.templates.values():
        if info.id in pack_cards:
            clash.add(info.id)
            reason = f"ID {info.id} is already used by pack {pack_cards[info.id]}"
            plan.rejected.append(Rejected(info.id, info.file, info.line, (reason,)))
            del templates[info.id]
    accepted: list[Accepted] = []
    for item in loaded.cards:
        card = item.card
        if card.template_id in clash:
            continue
        if card.id in pack_cards:
            reason = f"ID {card.id} is already used by pack {pack_cards[card.id]}"
            plan.rejected.append(Rejected(card.id, item.file, item.line, (reason,)))
            continue
        accepted.append(item)
    return accepted, templates


def _plan_media(
    store: UserStore, plan: ImportPlan, loaded: LoadResult, accepted: list[Accepted]
) -> None:
    """Read every image the accepted cards show; list the cards whose stored images differ."""
    stored: dict[str, dict[str, str]] = {}
    for link in store.media.all_links():
        stored.setdefault(link.card_id, {})[link.ref] = link.file
    cache: dict[str, bytes] = {}
    for item in accepted:
        images: dict[str, bytes] = {}
        for ref, name in item.images:
            if name not in cache:
                cache[name] = loaded.media[name].read(name)
            images[ref] = cache[name]
        if images:
            plan.media[item.card.id] = images
        wanted = {ref: media_file_name(data, ref) for ref, data in images.items()}
        if wanted != stored.get(item.card.id, {}):
            plan.media_changed.append(item.card.id)


def _missing(store: UserStore, plan: ImportPlan, stored: Mapping[str, Card]) -> None:
    by_template: dict[str, list[str]] = {}
    for card in stored.values():
        if card.template_id is not None and not card.retired:
            by_template.setdefault(card.template_id, []).append(card.id)
    plan.template_instances = by_template
    previous = _previous_ids(store, plan.files, plan.kind)
    for name, before in previous.items():
        now = set(plan.files.get(name, []))
        for cid in before:
            if cid in now or cid in plan.missing:
                continue
            found = stored.get(cid)
            if (found is not None and not found.retired) or by_template.get(cid):
                plan.missing.append(cid)
    for tid, info in plan.templates.items():
        fresh = set(info.instances)
        plan.retire_instances += [cid for cid in by_template.get(tid, []) if cid not in fresh]


def _plan_skills(
    store: UserStore,
    plan: ImportPlan,
    entries: list[SkillEntry],
    accepted: list[Accepted],
    pack_skills: Mapping[str, str],
) -> None:
    stored = {s.id: s for s in store.user_skills()}
    usable: list[SkillEntry] = []
    for e in entries:
        if e.skill.id in pack_skills:
            plan.skill_problems.append(
                Problem(
                    e.file,
                    e.line,
                    f"skill {e.skill.id} is defined by pack {pack_skills[e.skill.id]}",
                    card_id=e.skill.id,
                )
            )
        else:
            usable.append(e)
    external = set(pack_skills) | set(stored)
    graph = check_graph(usable, external - {e.skill.id for e in usable})
    bad = {p.card_id for p in graph.problems}
    plan.skill_problems += graph.problems
    if any("cycle" in p.message for p in graph.problems):
        bad |= {e.skill.id for e in usable}  # a cycle: keep none of the file's skills
    defined: set[str] = set(pack_skills) | set(stored)
    for e in usable:
        if e.skill.id in bad:
            continue
        defined.add(e.skill.id)
        old = stored.get(e.skill.id)
        if old is None:
            plan.skills_added.append(e.skill)
        elif old != e.skill:
            plan.skills_updated.append(e.skill)
        else:
            plan.skills_unchanged.append(e.skill)
    for item in accepted:
        for sid in _referenced_skills(item.card):
            if sid not in defined:
                defined.add(sid)
                plan.skills_created.append(
                    Skill(id=sid, name=sid, deck=item.card.deck, section_id=item.card.deck)
                )


def apply_import(store: UserStore, plan: ImportPlan, retire: Iterable[str] = ()) -> ImportRecord:
    """Write the plan in one transaction. `retire` holds IDs from plan.missing the student
    chose to retire (a template ID retires all its instances)."""
    chosen = list(dict.fromkeys(retire))
    unknown = [cid for cid in chosen if cid not in plan.missing]
    if unknown:
        raise ValueError(f"can only retire cards listed as missing: {', '.join(unknown)}")
    now = store.db.clock.now_ms()
    revisions: list[CardRevision] = []
    for change in plan.added:
        revisions.append(
            CardRevision(
                card_id=change.card.id, rev=1, changed_at=now, note=f"added from {change.file}"
            )
        )
    for change in plan.updated:
        note = "answer key updated" if change.key_changed else "content updated"
        revisions.append(
            CardRevision(
                card_id=change.card.id,
                rev=change.card.rev,
                changed_at=now,
                note=f"{note} from {change.file}",
                answer_changed=change.key_changed,
            )
        )
    to_retire = list(plan.retire_instances)
    for cid in chosen:
        to_retire += plan.template_instances.get(cid, []) or [cid]
    summary = plan.summary()
    summary["retired"] = to_retire
    record = ImportRecord(file=", ".join(plan.files) or "(none)", kind=plan.kind, summary=summary)
    sources = [
        TemplateSource(id=tid, source_md=plan.templates[tid].source, updated_at=now)
        for tid in plan.sources_changed
    ]
    # Image files first, outside the transaction: a failed import can leave a stored file
    # nothing points at, never a card pointing at a missing file.
    files = {cid: store.media.add_all(plan.media.get(cid, {})) for cid in plan.media_changed}

    def work(s: UserStore) -> ImportRecord:
        content: list[Any] = [
            *plan.tree,
            *plan.skills_created,
            *plan.skills_added,
            *plan.skills_updated,
        ]
        content += [c.card for c in plan.added + plan.updated]
        s.put_user_content(*content, *revisions, *sources)
        for cid in dict.fromkeys(to_retire):
            s.retire_user_card(cid)
        for cid, names in files.items():
            s.media.link(cid, names)
        return s.log_import(record)

    return store.atomic(work)
