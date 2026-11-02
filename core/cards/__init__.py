"""Card files, skills files, templates, imports, exports and content packs (milestone M2).

Implements docs/card-format.md. Public API:

Loading and checking (the import validator; EDT-2 calls `load` on the text being typed)
    ``Source(name, data, media)`` / ``Source.from_path(path, root)``  one input file
    ``load(sources, skills=(), *, pack=False) -> LoadResult``  parse, build, expand
        templates, self-check every key, warn. ``LoadResult.cards`` are ready to store.
    ``Problem``  file, line, message, severity ("error" rejects, "warning" doesn't)
    ``answer_spec(card, part=None) -> AnswerSpec``  the grader spec of a stored card

Importing into a profile (IMP-1, IMP-5, IMP-7)
    ``plan_import(store, sources, skills=()) -> ImportPlan``  dry run; ``plan.report()``
    ``plan_loaded(store, loaded, kind=...)``  the same dry run for cards another importer
        built (core.importers.anki); `kind` names the import in the log
    ``apply_import(store, plan, retire=()) -> ImportRecord``  one transaction; images go
        to the profile's media store, template sources to ``store.user_template(id)``
    ``StoredMedia(store.media, card_id, added)``  the editor's Source media (EDT-1)

Export (EXP-1)
    ``export_cards(cards, store.template_sources())`` -> {file name: text}
    ``export_media(cards, store.media)`` -> {path: image bytes}
    ``export_skills(skills)`` -> skills.md text

Content packs (PACK-1..6, GRAPH-1..7)
    ``check_pack``, ``write_mepack``, ``read_mepack``, ``compile_mepack``, ``write_pack_db``

Components (student-model spec 2.1 and 2.3)
    ``components(card)``  the skill, uses, part skills and step tags, each once
    ``wrong_component(card, matched_wrong, part=None)``  the skill of the step a matched
        known wrong answer names (`matched_wrong` as the attempt column stores it)
    ``step_component(card, step)``  the skill tag of one solution step

Standard times (student-model spec 2.4)
    ``standard_minutes(card_or_part, minutes_per_step, card=None)``  T*: `time:`, or
        0.5 + m * steps + m * max(0, tier - 3), or the tier's default with no steps

Templates are expanded in a separate process (sweep.py), so SymPy never loads in the
caller's process; call ``shutdown()`` at exit.
"""

from core.cards.checks import answer_spec, format_wrong, self_check
from core.cards.components import components, step_component, wrong_component
from core.cards.export import card_block, export_cards, export_media, export_skills
from core.cards.graph import check_graph, pool_report
from core.cards.importer import (
    ImportPlan,
    apply_import,
    plan_import,
    plan_loaded,
    template_sources,
)
from core.cards.load import (
    Accepted,
    DirMedia,
    LoadResult,
    Rejected,
    Source,
    StoredMedia,
    TemplateInfo,
    load,
)
from core.cards.mepack import (
    PackBuild,
    PackBuildError,
    PackMeta,
    check_pack,
    compile_mepack,
    read_mepack,
    read_meta,
    write_mepack,
    write_pack_db,
)
from core.cards.problems import Problem
from core.cards.standard_time import standard_minutes
from core.cards.sweep import shutdown

__all__ = [
    "Accepted",
    "DirMedia",
    "ImportPlan",
    "LoadResult",
    "PackBuild",
    "PackBuildError",
    "PackMeta",
    "Problem",
    "Rejected",
    "Source",
    "StoredMedia",
    "TemplateInfo",
    "answer_spec",
    "apply_import",
    "card_block",
    "check_graph",
    "check_pack",
    "compile_mepack",
    "components",
    "export_cards",
    "export_media",
    "export_skills",
    "format_wrong",
    "load",
    "plan_import",
    "plan_loaded",
    "pool_report",
    "read_mepack",
    "read_meta",
    "self_check",
    "shutdown",
    "standard_minutes",
    "step_component",
    "template_sources",
    "write_mepack",
    "write_pack_db",
    "wrong_component",
]
