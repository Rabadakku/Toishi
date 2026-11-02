"""Loading card files and skills files: parse, build, expand templates, self-check, warn.

`load()` is the one pipeline behind the dry-run import (importer.py), the live
validator (EDT-2: `load([Source("draft", text)])`), and the pack builder (mepack.py).
Errors reject a card (or, in a broken header, the whole file); warnings never do.
"""

import posixpath
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol

from core.cards import cardfile as cf
from core.cards import checks
from core.cards import text as t
from core.cards.problems import Problem
from core.cards.skillfile import PaceSource, SkillEntry, read_skills
from core.cards.sweep import SweepRunner
from core.cards.sweep import runner as default_runner
from core.cards.template import TemplateError, compile_template
from core.model import Card
from core.storage.media import UserMedia
from core.storage.schema import V1_PARAMS_PREFIX

# Before schema v2 an instance's parameters were the first line of its notes_md, after
# this prefix; they are Card.params now (ADR-0011).
PARAMS_NOTE = V1_PARAMS_PREFIX


class MediaStore(Protocol):
    def resolve(self, file_name: str, ref: str) -> str | None: ...
    def read(self, name: str) -> bytes: ...


class DirMedia:
    """Images on disk, named by their path relative to `root` (never outside it)."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, file_name: str, ref: str) -> str | None:
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(file_name), ref))
        if joined.startswith("../") or joined == ".." or posixpath.isabs(joined):
            return None
        path = self.root / joined
        try:
            ok = path.resolve().is_relative_to(self.root) and path.is_file()
        except OSError:
            ok = False
        return joined if ok else None

    def read(self, name: str) -> bytes:
        return (self.root / name).read_bytes()


class StoredMedia:
    """Images of an own card being edited (EDT-1): its references resolve to the files
    already stored for it, or to images just added in the editor ({ref: bytes})."""

    ADDED = "added:"

    def __init__(
        self, media: UserMedia, card_id: str | None, added: Mapping[str, bytes] | None = None
    ) -> None:
        self.media = media
        self.stored = media.links(card_id) if card_id is not None else {}
        self.added = dict(added or {})

    def resolve(self, file_name: str, ref: str) -> str | None:
        if ref in self.added:
            return self.ADDED + ref
        return self.stored.get(ref)

    def read(self, name: str) -> bytes:
        if name.startswith(self.ADDED):
            return self.added[name.removeprefix(self.ADDED)]
        data = self.media.read_file(name)
        if data is None:
            raise FileNotFoundError(f"media file {name} is not in the store")
        return data


@dataclass(frozen=True, slots=True)
class Source:
    """One card or skills file: a display name (a path relative to its folder), its bytes
    or text, and where its images are found."""

    name: str
    data: bytes | str
    media: MediaStore | None = None

    @classmethod
    def from_path(cls, path: Path, root: Path | None = None) -> Source:
        base = (root or path.parent).resolve()
        return cls(path.resolve().relative_to(base).as_posix(), path.read_bytes(), DirMedia(base))


@dataclass(frozen=True, slots=True)
class Accepted:
    card: Card
    file: str
    line: int
    images: tuple[tuple[str, str], ...] = ()  # (reference as written, media name)
    claims: tuple[cf.StepClaim, ...] = ()  # the worked solution's `check:` lines (MATH-17)
    final: str | None = None  # template instances: the final line's value from the sweep


@dataclass(frozen=True, slots=True)
class Rejected:
    """A card (or template) that won't be imported: every reason with its own line."""

    card_id: str | None
    file: str
    line: int  # the first reason's line
    reasons: tuple[str, ...]
    lines: tuple[int, ...] = ()  # one per reason; empty means all at `line`

    def located(self) -> list[tuple[int, str]]:
        lines = self.lines or (self.line,) * len(self.reasons)
        return list(zip(lines, self.reasons, strict=True))

    def __str__(self) -> str:
        who = f"card {self.card_id}" if self.card_id else "a card"
        return f"{self.file}:{self.line}: {who} rejected: {self.reasons[0]}"


@dataclass(frozen=True, slots=True)
class TemplateInfo:
    id: str
    file: str
    line: int
    source: str  # the block as written, with the file's defaults made explicit (for export)
    instances: tuple[str, ...]
    combinations: int
    rejected_by_require: int
    cross_checked: int = 0  # DEV-18: template operations mpmath agreed with
    cross_unverified: int = 0


@dataclass(slots=True)
class LoadResult:
    cards: list[Accepted] = field(default_factory=list)  # fixed cards and template instances
    templates: dict[str, TemplateInfo] = field(default_factory=dict)
    rejected: list[Rejected] = field(default_factory=list)
    warnings: list[Problem] = field(default_factory=list)
    file_problems: list[Problem] = field(default_factory=list)  # whole files rejected
    skills: list[SkillEntry] = field(default_factory=list)
    skill_problems: list[Problem] = field(default_factory=list)
    pace: PaceSource | None = None  # content packs only: the skills file's pace standard
    media: dict[str, MediaStore] = field(default_factory=dict)  # media name -> where it is
    files: dict[str, list[str]] = field(default_factory=dict)  # file -> card and template ids

    @property
    def ok(self) -> bool:
        return not (self.rejected or self.file_problems or self.skill_problems)

    def errors(self) -> list[str]:
        out = [str(p) for p in self.file_problems + self.skill_problems]
        for r in self.rejected:
            out += [f"{r.file}:{line}: {reason}" for line, reason in r.located()]
        return out


@dataclass(slots=True)
class _Pending:
    card: Card
    file: str
    line: int
    lines: dict[str, int]
    explicit_difficulty: bool
    template: str | None = None  # template id for instances
    images: tuple[tuple[str, str], ...] = ()
    claims: tuple[cf.StepClaim, ...] = ()
    final: str | None = None


def load(
    sources: Iterable[Source],
    skills: Iterable[Source] = (),
    *,
    pack: bool = False,
    self_check: bool = True,
    runner: SweepRunner | None = None,
) -> LoadResult:
    result = LoadResult()
    for source in skills:
        entries, pace, problems = read_skills(source.data, source.name)
        result.skills += entries
        result.skill_problems += [p for p in problems if p.is_error]
        result.warnings += [p for p in problems if not p.is_error]
        if pace is None:
            continue
        if not pack:
            message = (
                "the pace standard (pace- keys, ## Section blocks) is for content packs "
                "only; ignored here"
            )
            result.warnings.append(Problem(source.name, pace.line, message, "warning"))
        elif result.pace is not None:
            message = f"the pace standard is already set in {result.pace.file}"
            result.skill_problems.append(Problem(source.name, pace.line, message))
        else:
            result.pace = pace
    pending: list[_Pending] = []
    for source in sources:
        _load_file(source, result, pending, pack, runner)
    _reject_duplicates(result, pending)
    if self_check:
        pending = _self_check(result, pending)
    _warn(result, pending)
    for item in pending:
        result.cards.append(
            Accepted(item.card, item.file, item.line, item.images, item.claims, item.final)
        )
    instance_ids = {item.card.id for item in pending if item.template}
    for info in list(result.templates.values()):
        if not set(info.instances) <= instance_ids:
            del result.templates[info.id]  # an instance was rejected: so is the template
            result.cards = [a for a in result.cards if a.card.template_id != info.id]
    return result


def _load_file(
    source: Source,
    result: LoadResult,
    pending: list[_Pending],
    pack: bool,
    runner: SweepRunner | None,
) -> None:
    src = cf.read_card_file(source.data, source.name)
    first_block = src.blocks[0].start + 1 if src.blocks else len(src.lines) + 1
    file_errors = [p for p in src.problems if p.line < first_block]
    if file_errors or not src.lines:
        result.file_problems += file_errors or src.problems
        for block in src.blocks:
            result.rejected.append(
                Rejected(
                    block.id or None,
                    source.name,
                    block.line,
                    ("not imported: the file has errors",),
                )
            )
        return
    ids: list[str] = []
    result.files[source.name] = ids

    def media(ref: str) -> str | None:
        if source.media is None:
            return ref
        name = source.media.resolve(source.name, ref)
        if name is not None:
            result.media[name] = source.media
        return name

    ctx = cf.BuildContext(source.name, media if source.media is not None else None, pack)
    for block in src.blocks:
        own = [p for p in src.problems if block.start < p.line <= block.end]
        errors = [p for p in own if p.is_error]
        if not block.id or errors:
            _reject(result, block.id or None, source.name, block.line, errors)
            continue
        if cf.INSTANCE_SEPARATOR in block.id:
            reason = f"IDs can't contain '{cf.INSTANCE_SEPARATOR}' (it marks template instances)"
            result.rejected.append(Rejected(block.id, source.name, block.line, (reason,)))
            continue
        ids.append(block.id)
        built = cf.build_card(block, src.header, ctx)
        result.warnings += [p for p in built.problems if not p.is_error]
        if built.card is None:
            _reject(result, block.id, source.name, built.line, built.problems)
            continue
        if not cf.is_template(block):
            pending.append(
                _Pending(
                    built.card,
                    source.name,
                    built.line,
                    built.lines,
                    built.explicit_difficulty,
                    images=tuple(dict.fromkeys(built.images)),
                    claims=tuple(built.claims),
                )
            )
            continue
        _expand(src, block, built, ctx, result, pending, runner or default_runner())


def _reject(
    result: LoadResult, card_id: str | None, file: str, line: int, problems: list[Problem]
) -> None:
    errors = [p for p in problems if p.is_error] or [Problem(file, line, "rejected")]
    reasons = tuple(p.message for p in errors)
    lines = tuple(p.line for p in errors)
    result.rejected.append(Rejected(card_id, file, lines[0], reasons, lines))


def template_source(src: t.FileSrc, block: t.BlockSrc) -> str:
    """The block as written, with the header defaults it relied on made explicit."""
    end = block.end
    while end > block.start + 1 and not src.lines[end - 1].strip():
        end -= 1  # drop trailing blank and comment-only lines (they belong to the next card)
    lines = list(src.original[block.start : end])
    inherited = [
        f"{k}: {v.value}" for k, v in src.header.items() if k != "format" and k not in block.keys
    ]
    lines[1:1] = inherited
    return t.join_lines(lines)


def _expand(
    src: t.FileSrc,
    block: t.BlockSrc,
    built: cf.Built,
    ctx: cf.BuildContext,
    result: LoadResult,
    pending: list[_Pending],
    runner: SweepRunner,
) -> None:
    try:
        job = compile_template(block, src.lines, src.header, src.name)
    except TemplateError as exc:
        line = exc.line or block.line
        result.rejected.append(Rejected(block.id, src.name, line, (exc.message,)))
        return
    sweep = runner.run(job)
    if sweep.error is not None:
        result.rejected.append(
            Rejected(block.id, src.name, sweep.line or block.line, (sweep.error,))
        )
        return
    instances: list[_Pending] = []
    for inst in sweep.instances:
        new_block, problems = t.reread_block(src, block, list(inst.lines))
        if new_block is None or any(p.is_error for p in problems):
            _reject(result, block.id, src.name, block.line, _prefixed(problems, inst.params))
            return
        again = cf.build_card(new_block, src.header, ctx)
        if again.card is None:
            _reject(result, block.id, src.name, block.line, _prefixed(again.problems, inst.params))
            return
        card = replace(
            again.card,
            id=f"{block.id}{cf.INSTANCE_SEPARATOR}{inst.seed:08x}",
            template_id=block.id,
            seed=inst.seed,
            params=inst.params,
        )
        instances.append(
            _Pending(
                card,
                src.name,
                block.line,
                again.lines,
                built.explicit_difficulty,
                block.id,
                tuple(dict.fromkeys(again.images)),
                tuple(again.claims),
                inst.final,
            )
        )
    pending += instances
    result.templates[block.id] = TemplateInfo(
        block.id,
        src.name,
        block.line,
        template_source(src, block),
        tuple(i.card.id for i in instances),
        sweep.combinations,
        sweep.rejected_by_require,
        sweep.cross_checked,
        sweep.cross_unverified,
    )


def _prefixed(problems: list[Problem], params: str) -> list[Problem]:
    return [replace(p, message=f"instance {params}: {p.message}") for p in problems]


def _reject_duplicates(result: LoadResult, pending: list[_Pending]) -> None:
    where: dict[str, list[tuple[str, int]]] = {}
    for item in pending:
        where.setdefault(item.card.id, []).append((item.file, item.line))
    for info in result.templates.values():
        where.setdefault(info.id, []).append((info.file, info.line))
    for r in result.rejected:
        if r.card_id is not None and r.reasons and not r.reasons[0].startswith("not imported"):
            where.setdefault(r.card_id, []).append((r.file, r.line))
    dupes = {cid for cid, places in where.items() if len(places) > 1}
    if not dupes:
        return
    for cid in sorted(dupes):
        places = where[cid]
        for file, line in places:
            others = ", ".join(f"{f}:{n}" for f, n in places if (f, n) != (file, line))
            result.rejected.append(
                Rejected(cid, file, line, (f"duplicate ID {cid} (also at {others})",))
            )
    keep = [p for p in pending if p.card.id not in dupes and (p.template or "") not in dupes]
    pending[:] = keep
    for cid in dupes:
        result.templates.pop(cid, None)


def _self_check(result: LoadResult, pending: list[_Pending]) -> list[_Pending]:
    keep: list[_Pending] = []
    failed_templates: set[str] = set()
    for item in pending:
        if item.template in failed_templates:
            continue
        found = checks.self_check(item.card)
        if not found:
            keep.append(item)
            continue
        line = item.lines.get(found[0].where, item.line)
        reasons = [k.message for k in found]
        if item.template is not None:
            reasons = [f"instance {item.card.params or ''}: {r}" for r in reasons]
            failed_templates.add(item.template)
            result.templates.pop(item.template, None)
        result.rejected.append(
            Rejected(item.template or item.card.id, item.file, line, tuple(reasons))
        )
    return [p for p in keep if p.template not in failed_templates]


def _warn(result: LoadResult, pending: list[_Pending]) -> None:
    firsts: list[_Pending] = []
    seen_templates: set[str] = set()
    for item in pending:
        if item.template is not None:
            if item.template in seen_templates:
                continue
            seen_templates.add(item.template)
        firsts.append(item)
    for item in firsts:
        card = item.card
        cid = item.template or card.id

        def warn(
            message: str, line: int = item.line, cid: str = cid, file: str = item.file
        ) -> None:
            result.warnings.append(Problem(file, line, message, "warning", cid))

        dollar = checks.dollar_math(card)
        if dollar is not None:
            warn(f"{dollar!r} looks like math: use \\( \\) instead of $")
        if card.kind == "problem" and not card.hints:
            warn("no ### Hints")
        if card.kind in {"problem", "find-error", "method"} and not item.explicit_difficulty:
            warn("no difficulty (it defaults to 2)")
    stems = [(i.template or i.card.id, checks.stem(i.card)) for i in firsts if i.template is None]
    owners = [i for i in firsts if i.template is None]
    for i, j, ratio in checks.near_duplicates(stems):
        a, b = owners[i], owners[j]
        how = "the same text as" if ratio == 1.0 else "nearly the same text as"
        result.warnings.append(
            Problem(
                b.file, b.line, f"{how} card {a.card.id} ({a.file}:{a.line})", "warning", b.card.id
            )
        )


def sources_in(folder: Path, pattern: str = "*.cards.md") -> list[Source]:
    return [Source.from_path(p, folder) for p in sorted(folder.glob(pattern))]


def skills_in(folder: Path, name: str = "skills.md") -> list[Source]:
    path = folder / name
    return [Source.from_path(path, folder)] if path.is_file() else []


def card_ids(result: LoadResult) -> Sequence[str]:
    return [a.card.id for a in result.cards]
