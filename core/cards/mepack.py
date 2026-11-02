"""Content packs (PACK-1..6): `.mepack` zips and the sealed pack databases built from them.

A pack source folder holds `pack.json` (id, title, semantic version, license summary),
`skills.md`, card files (`*.cards.md`, at the top level) and `media/`. `check_pack`
loads it under the content-pack rules (step tags, decks, licenses, every skill
defined, the skill graph a DAG) and expands templates; `write_mepack` zips the sources
with `manifest.json` and `credits.json`; `compile_mepack` checks a `.mepack` again
and writes the sealed read-only pack database through core.storage.PackWriter.
"""

import hashlib
import io
import json
import math
import posixpath
import re
import time
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import core
from core.cards import decks
from core.cards import verify as verify_mod
from core.cards.checks import AUTO_TYPES
from core.cards.graph import GraphResult, PoolLine, check_graph, pool_report
from core.cards.load import LoadResult, Source, load
from core.cards.standard_time import TIER_DEFAULTS, TIMED_KINDS, uses_tier_default
from core.cards.sweep import SweepRunner
from core.cards.sweep import runner as sweep_runner
from core.model import (
    Card,
    CardRevision,
    Course,
    Media,
    PackInfo,
    PackPace,
    Section,
    Skill,
    Unit,
)
from core.storage import PackReader, build_pack

PACK_FORMAT = 1
PIPELINE_VERSION = f"toishi {core.__version__} cards-m2"
MANIFEST = "manifest.json"
CREDITS = "credits.json"
META = "pack.json"
SKILLS = "skills.md"
MEDIA_DIR = "media/"
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
_SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class PackBuildError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PackMeta:
    id: str
    title: str
    version: str
    license: str
    description: str = ""


def read_meta(data: bytes | str, name: str = META) -> PackMeta:
    try:
        raw = json.loads(data)
    except ValueError as exc:
        raise PackBuildError(f"{name}: not valid JSON: {exc}") from None
    if not isinstance(raw, dict):
        raise PackBuildError(f"{name}: expected a JSON object")
    missing = [k for k in ("id", "title", "version", "license") if not isinstance(raw.get(k), str)]
    if missing:
        raise PackBuildError(f"{name}: missing {', '.join(missing)}")
    meta = PackMeta(
        raw["id"], raw["title"], raw["version"], raw["license"], str(raw.get("description", ""))
    )
    if not _ID.fullmatch(meta.id):
        raise PackBuildError(f"{name}: bad pack id {meta.id!r}")
    if not _SEMVER.fullmatch(meta.version):
        raise PackBuildError(
            f"{name}: version must be a semantic version like 1.0.0, got {meta.version!r}"
        )
    return meta


class ZipMedia:
    def __init__(self, members: Mapping[str, bytes]) -> None:
        self.members = members

    def resolve(self, file_name: str, ref: str) -> str | None:
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(file_name), ref))
        return joined if joined in self.members and joined.startswith(MEDIA_DIR) else None

    def read(self, name: str) -> bytes:
        return self.members[name]


@dataclass(slots=True)
class PackBuild:
    meta: PackMeta
    loaded: LoadResult
    graph: GraphResult | None = None
    pool: list[PoolLine] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)  # summary lines of the verification passes
    unverified: list[str] = field(default_factory=list)  # what no machine check covers
    wrong_answers: list[str] = field(default_factory=list)  # gaps in wrong: coverage
    standard_times: list[str] = field(default_factory=list)  # cards timed by a tier default
    cards: list[Card] = field(default_factory=list)
    revisions: list[CardRevision] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    tree: list[Course | Unit | Section] = field(default_factory=list)
    media: dict[str, bytes] = field(default_factory=dict)
    pace: PackPace = field(default_factory=PackPace)  # from skills.md

    @property
    def ok(self) -> bool:
        return not self.errors

    def report(self) -> str:
        head = f"pack {self.meta.id} {self.meta.version}"
        lines = [f"{head}: {len(self.cards)} cards, {len(self.skills)} skills"]
        lines += [f"error: {e}" for e in self.errors]
        lines += [f"warning: {w}" for w in self.warnings]
        lines += [f"unverified: {u}" for u in self.unverified]
        lines += [f"wrong answers: {w}" for w in self.wrong_answers]
        lines += [f"standard time: {s}" for s in self.standard_times]
        lines += [f"pool {p.skill_id}: {p.message}" for p in self.pool if not p.ok]
        lines += self.checks
        return "\n".join(lines)


NO_WRONG_ANSWERS = frozenset({"self", "choice"})  # answer types that can't list wrong answers


def wrong_coverage(loaded: LoadResult) -> tuple[list[str], str]:
    """Student-model spec 2.3: problems of tier 2 and up list their common wrong answers,
    each with the `@step` it comes from. One line for each answer (the card's, or each
    part's) of an auto-checked problem of tier 2 or up with no `wrong:` line, and one for
    each wrong answer of a problem without `@step`; a template once, with its first
    instance's answers. Then a summary line."""
    lines: list[str] = []
    answers = covered = unstepped = 0
    seen: set[str] = set()
    for item in loaded.cards:
        card = item.card
        cid = card.template_id or card.id
        if card.kind != "problem" or cid in seen:
            continue
        seen.add(cid)
        where = f"{item.file}:{item.line}: card {cid}"
        boxes = [(f" part {p.label}", p.answer_type, p.wrong) for p in card.parts]
        for label, answer_type, wrong in boxes or [("", card.answer_type, card.wrong)]:
            if answer_type in NO_WRONG_ANSWERS:
                continue
            if card.tier >= 2:
                answers += 1
                covered += bool(wrong)
                if not wrong:
                    lines.append(f"{where}{label}: tier {card.tier}, no wrong: line")
            for w in wrong:
                if w.step is None:
                    unstepped += 1
                    lines.append(f"{where}{label}: wrong answer {w.answer!r} has no @step")
    summary = (
        f"wrong answers: answers of tier 2+ problems with a wrong: line {covered}/{answers}, "
        f"wrong answers without @step {unstepped}"
    )
    return lines, summary


def tier_default_times(loaded: LoadResult) -> list[str]:
    """Student-model spec 2.4: graded cards whose standard time is their tier's default,
    for want of `time:` and of solution steps to count (a template once). Pack problems
    always have steps, so this guards whatever else reaches the report."""
    lines: list[str] = []
    seen: set[str] = set()
    for item in loaded.cards:
        card = item.card
        cid = card.template_id or card.id
        if card.kind in TIMED_KINDS and cid not in seen and uses_tier_default(card):
            seen.add(cid)
            lines.append(
                f"{item.file}:{item.line}: card {cid}: no solution steps, so the tier "
                f"{card.tier} default of {TIER_DEFAULTS[card.tier]:g} minutes"
            )
    return lines


def verification(card: Card) -> str | None:
    """PACK-5: how the key was checked, unless the source says more."""
    if card.verified:
        return card.verified
    if card.template_id is not None:
        return "template+cas"
    if card.answer_type in AUTO_TYPES or any(p.answer_type in AUTO_TYPES for p in card.parts):
        return "self-check"
    return None


def check_pack(
    meta: PackMeta,
    sources: Iterable[Source],
    skills: Iterable[Source],
    *,
    external_skills: Iterable[str] = (),
    previous: Path | None = None,
    built_at: int | None = None,
    runner: SweepRunner | None = None,
    verify: bool = True,
) -> PackBuild:
    skill_sources = list(skills)
    loaded = load(sources, skill_sources, pack=True, runner=runner)
    build = PackBuild(meta, loaded)
    build.errors += loaded.errors()
    build.warnings += [str(w) for w in loaded.warnings]
    if not skill_sources:
        build.errors.append(f"a content pack needs {SKILLS}")
    external = set(external_skills)
    graph = check_graph(loaded.skills, external, reduce=True)
    build.graph = graph
    build.errors += [str(p) for p in graph.problems]
    build.warnings += [
        f"redundant prerequisite dropped: {a} requires {b}" for a, b in graph.removed
    ]
    defined = {s.id: s for s in graph.skills}
    known = set(defined) | external
    for item in loaded.cards:
        card = item.card
        where = f"{item.file}:{item.line}: card {card.template_id or card.id}"
        if card.deck is None:
            build.errors.append(f"{where}: pack cards need a deck")
        if not card.provenance.license:
            build.errors.append(f"{where}: pack cards need a license")
        refs = [card.skill_id, *card.uses, *(p.skill_id for p in card.parts)]
        refs += [s.skill_id for s in (*card.solution, *card.alternative_solution, *card.shown_work)]
        unknown = sorted({r for r in refs if r and r not in known})
        if card.skill_id is None and card.kind not in {"flashcard", "cloze"}:
            build.errors.append(f"{where}: pack cards need a skill")
        if unknown:
            build.errors.append(f"{where}: skills not in {SKILLS}: {', '.join(unknown)}")
        method_skill = defined.get(card.skill_id or "")
        if card.kind == "method" and method_skill is not None and not method_skill.method_choice:
            build.errors.append(f"{where}: method cards need a method-choice skill (chooses: ...)")
    build.wrong_answers, coverage = wrong_coverage(loaded)
    build.checks.append(coverage)
    build.standard_times = tier_default_times(loaded)
    if verify:  # DEV-18 and MATH-17
        found, summary = verify_mod.differential(loaded)
        build.errors += found
        build.checks += summary
        found, unverified, summary = verify_mod.solutions(loaded, runner or sweep_runner())
        build.errors += found
        build.unverified += unverified
        build.checks += summary
    build.errors = list(dict.fromkeys(build.errors))
    cards = [replace(a.card, verified=verification(a.card)) for a in loaded.cards]
    build.pool = pool_report(graph.skills, cards)
    when = built_at if built_at is not None else _now_ms()
    build.cards, build.revisions = _revisions(cards, previous, meta.version, when)
    build.skills = graph.skills
    build.tree = decks.tree([c.deck for c in cards] + [s.deck for s in graph.skills])
    _pace(build, loaded)
    for name, store in loaded.media.items():
        build.media[name] = store.read(name)
    return build


def _pace(build: PackBuild, loaded: LoadResult) -> None:
    """Student-model spec 4.1: the pace standard of skills.md, whose sections must be decks
    of the pack's cards or skills (the parser already checked numbers and duplicates)."""
    pace = loaded.pace
    if pace is None:
        return
    decks_here = {r.id for r in build.tree if isinstance(r, Section)}
    for s in pace.sections:
        if s.deck not in decks_here:
            build.errors.append(
                f"{s.file}:{s.line}: ## Section {s.deck}: no card or skill has this deck"
            )
    build.pace = pace.standard()
    hours = math.fsum(s.hours for s in build.pace.sections)
    summary = f"pace: {build.pace.minutes_per_step:g} minutes per step"
    if build.pace.weekly_hours is not None:
        summary += f", {build.pace.weekly_hours:g} class hours a week"
    build.checks.append(f"{summary}, {len(build.pace.sections)} sections, {hours:g} hours")


def _revisions(
    cards: list[Card], previous: Path | None, version: str, at: int
) -> tuple[list[Card], list[CardRevision]]:
    """PACK-2 against the previous pack: same content keeps its revision, a change adds
    one (noting a changed key), and a card that disappeared is kept, retired."""
    from core.cards.importer import key_signature

    if previous is None:
        revs = [
            CardRevision(card_id=c.id, rev=1, changed_at=at, note=f"added in {version}")
            for c in cards
        ]
        return cards, revs
    out: list[Card] = []
    revisions: list[CardRevision] = []
    with PackReader(previous) as old_pack:
        old_cards = {c.id: c for c in old_pack.content.cards()}
        for card in cards:
            old = old_cards.pop(card.id, None)
            if old is not None:
                revisions += old_pack.content.revisions(card.id)
            if old is None:
                out.append(card)
                revisions.append(
                    CardRevision(card_id=card.id, rev=1, changed_at=at, note=f"added in {version}")
                )
            elif replace(card, rev=old.rev, status="active") == replace(old, status="active"):
                out.append(replace(card, rev=old.rev))
            else:
                changed = key_signature(card) != key_signature(old)
                note = "answer key updated" if changed else "content updated"
                out.append(replace(card, rev=old.rev + 1))
                revisions.append(
                    CardRevision(
                        card_id=card.id,
                        rev=old.rev + 1,
                        changed_at=at,
                        note=f"{note} in {version}",
                        answer_changed=changed,
                    )
                )
        for old in old_cards.values():  # gone from the sources: retired, never deleted
            out.append(replace(old, status="retired"))
            revisions += old_pack.content.revisions(old.id)
    return out, revisions


# ---------------------------------------------------------------- .mepack files


def content_hash(members: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in sorted(members):
        if name in {MANIFEST, CREDITS}:
            continue
        digest.update(name.encode() + b"\0" + hashlib.sha256(members[name]).digest() + b"\n")
    return "sha256:" + digest.hexdigest()


def credits(cards: Iterable[Card], pack_id: str) -> dict[str, Any]:
    """PACK-4: who made what, grouped by source and license (the Credits screen)."""
    groups: dict[tuple[Any, ...], list[str]] = {}
    for c in cards:
        p = c.provenance
        key = (
            p.source,
            p.source_url,
            p.license,
            p.creators,
            p.modified,
            p.translation,
            p.unofficial_solution,
        )
        groups.setdefault(key, []).append(c.template_id or c.id)
    sources = []
    for (source, url, lic, creators, modified, translation, unofficial), ids in sorted(
        groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])
    ):
        unique = list(dict.fromkeys(ids))
        sources.append(
            {
                "source": source,
                "source_url": url,
                "license": lic,
                "creators": list(creators),
                "modified": modified,
                "translation": translation,
                "unofficial_solution": unofficial,
                "cards": len(unique),
                "card_ids": unique,
            }
        )
    return {"pack": pack_id, "sources": sources}


def source_members(folder: Path) -> dict[str, bytes]:
    """The files of a pack source folder that go into its .mepack."""
    members: dict[str, bytes] = {}
    for path in sorted(folder.glob("*.cards.md")):
        members[path.name] = path.read_bytes()
    if (folder / SKILLS).is_file():
        members[SKILLS] = (folder / SKILLS).read_bytes()
    media = folder / MEDIA_DIR
    if media.is_dir():
        for path in sorted(media.rglob("*")):
            if path.is_file():
                members[path.relative_to(folder).as_posix()] = path.read_bytes()
    return members


def sources_of(members: Mapping[str, bytes]) -> tuple[list[Source], list[Source]]:
    media = ZipMedia(members)
    cards = [Source(n, members[n], media) for n in sorted(members) if n.endswith(".cards.md")]
    skills = [Source(SKILLS, members[SKILLS], media)] if SKILLS in members else []
    return cards, skills


def manifest(build: PackBuild, members: Mapping[str, bytes], built_at: int) -> dict[str, Any]:
    courses = [{"id": r.id, "title": r.title} for r in build.tree if isinstance(r, Course)]
    licenses: dict[str, int] = {}
    for c in build.cards:
        if c.status == "active":
            lic = c.provenance.license or "unknown"
            licenses[lic] = licenses.get(lic, 0) + 1
    return {
        "id": build.meta.id,
        "title": build.meta.title,
        "version": build.meta.version,
        "format": PACK_FORMAT,
        "courses": courses,
        "license": build.meta.license,
        "licenses": licenses,
        "built_at": built_at,
        "pipeline": PIPELINE_VERSION,
        "content_hash": content_hash(members),
        "description": build.meta.description,
    }


def write_mepack(
    path: Path, build: PackBuild, members: Mapping[str, bytes], built_at: int
) -> dict[str, Any]:
    """Zip the sources with manifest.json and credits.json (deterministic: sorted, fixed times)."""
    if not build.ok:
        raise PackBuildError("the pack has errors:\n" + "\n".join(build.errors))
    info = manifest(build, members, built_at)
    files = dict(members)
    files[MANIFEST] = (json.dumps(info, indent=2, sort_keys=True) + "\n").encode()
    files[CREDITS] = (
        json.dumps(credits(build.cards, build.meta.id), indent=2, sort_keys=True) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            zinfo = zipfile.ZipInfo(name, _ZIP_TIME)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = 0o644 << 16
            zf.writestr(zinfo, files[name])
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(buffer.getvalue())
    tmp.replace(path)
    return info


def read_mepack(path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Open a .mepack safely: only card files, skills.md, media and the two JSON files; no
    paths outside the pack; size limits; and the content hash must match the manifest."""
    members: dict[str, bytes] = {}
    total = 0
    try:
        with zipfile.ZipFile(path) as zf:
            for zinfo in zf.infolist():
                name = zinfo.filename
                if zinfo.is_dir():
                    continue
                normal = posixpath.normpath(name)
                if normal != name or name.startswith(("/", "../")) or "\\" in name or ":" in name:
                    raise PackBuildError(f"{path.name}: unsafe member name {name!r}")
                if not _allowed_member(name):
                    raise PackBuildError(
                        f"{path.name}: unexpected file {name!r} (packs hold no code)"
                    )
                if zinfo.file_size > MAX_MEMBER_BYTES:
                    raise PackBuildError(f"{path.name}: {name} is too large")
                total += zinfo.file_size
                if total > MAX_TOTAL_BYTES:
                    raise PackBuildError(f"{path.name}: the pack is too large")
                data = zf.read(zinfo)
                if len(data) != zinfo.file_size:
                    raise PackBuildError(f"{path.name}: {name} has the wrong size")
                members[name] = data
    except zipfile.BadZipFile as exc:
        raise PackBuildError(f"{path.name}: not a zip file: {exc}") from None
    if MANIFEST not in members:
        raise PackBuildError(f"{path.name}: no {MANIFEST}")
    try:
        info = json.loads(members[MANIFEST])
    except ValueError as exc:
        raise PackBuildError(f"{path.name}: {MANIFEST} is not JSON: {exc}") from None
    if not isinstance(info, dict) or info.get("format") != PACK_FORMAT:
        found = info.get("format") if isinstance(info, dict) else "?"
        raise PackBuildError(f"{path.name}: pack format {found} is not {PACK_FORMAT}")
    if info.get("content_hash") != content_hash(members):
        raise PackBuildError(f"{path.name}: content hash does not match {MANIFEST}")
    return info, members


def _allowed_member(name: str) -> bool:
    if name in {MANIFEST, CREDITS, SKILLS}:
        return True
    if "/" not in name and name.endswith(".cards.md"):
        return True
    return name.startswith(MEDIA_DIR) and name.lower().endswith((".svg", ".png"))


def compile_mepack(
    path: Path,
    db_path: Path,
    *,
    external_skills: Iterable[str] = (),
    previous: Path | None = None,
    runner: SweepRunner | None = None,
    overwrite: bool = False,
) -> tuple[PackInfo, PackBuild]:
    """Check a .mepack again and write its sealed read-only pack database."""
    info, members = read_mepack(path)
    fields = ("id", "title", "version", "license", "description")
    meta = read_meta(json.dumps({k: info[k] for k in fields if k in info}), MANIFEST)
    cards, skills = sources_of(members)
    built_at = int(info.get("built_at") or _now_ms())
    build = check_pack(
        meta,
        cards,
        skills,
        external_skills=external_skills,
        previous=previous,
        built_at=built_at,
        runner=runner,
    )
    if not build.ok:
        raise PackBuildError("the pack has errors:\n" + "\n".join(build.errors))
    return write_pack_db(db_path, build, built_at, overwrite=overwrite), build


def write_pack_db(
    db_path: Path, build: PackBuild, built_at: int, *, overwrite: bool = False
) -> PackInfo:
    if not build.ok:
        raise PackBuildError("the pack has errors:\n" + "\n".join(build.errors))
    info = PackInfo(
        id=build.meta.id,
        title=build.meta.title,
        version=build.meta.version,
        format=PACK_FORMAT,
        built_at=built_at,
    )
    records: list[Any] = [*build.tree, *build.skills, *build.cards, *build.revisions, build.pace]
    records += [Media(name=name, data=data) for name, data in sorted(build.media.items())]
    if overwrite:
        db_path.unlink(missing_ok=True)
    return build_pack(db_path, info, records)


def _now_ms() -> int:
    return time.time_ns() // 1_000_000
