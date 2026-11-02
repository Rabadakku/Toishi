"""Skill graph checks (GRAPH-1, -4, -5): references, cycles, redundant edges, pool targets."""

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field, replace

from core.cards.problems import Problem
from core.cards.skillfile import SkillEntry
from core.model import Card, Skill


@dataclass(slots=True)
class GraphResult:
    skills: list[Skill]
    problems: list[Problem] = field(default_factory=list)
    removed: list[tuple[str, str]] = field(default_factory=list)  # redundant requires edges


def check_graph(
    entries: list[SkillEntry], external: Collection[str] = (), *, reduce: bool = False
) -> GraphResult:
    """Every edge points at a known skill; prerequisites form a DAG (GRAPH-1). With
    reduce=True, prerequisites implied by others are dropped (chosen methods are kept)."""
    by_id = {e.skill.id: e for e in entries}
    known = set(by_id) | set(external)
    problems: list[Problem] = []
    for e in entries:
        s = e.skill
        for key, others in (
            ("requires", [o for o in s.requires if o not in e.chooses]),
            ("chooses", list(e.chooses)),
            ("encompasses", [o for o, _ in s.encompasses]),
            ("confusable", list(s.confusable)),
        ):
            for other in others:
                if other not in known:
                    line = e.lines.get(key, e.line)
                    problems.append(
                        Problem(e.file, line, f"{key}: unknown skill {other}", card_id=s.id)
                    )
    graph = {sid: [o for o in e.skill.requires if o in by_id] for sid, e in by_id.items()}
    cycle = find_cycle(graph)
    if cycle is not None:
        first = by_id[cycle[0]]
        path = " -> ".join([*cycle, cycle[0]])
        problems.append(
            Problem(
                first.file,
                first.lines.get("requires", first.lines.get("chooses", first.line)),
                f"prerequisites form a cycle: {path}",
                card_id=first.skill.id,
            )
        )
    skills = [e.skill for e in entries]
    removed: list[tuple[str, str]] = []
    if reduce and cycle is None:
        skills, removed = transitive_reduction(entries)
    return GraphResult(skills, problems, removed)


def find_cycle(graph: Mapping[str, Iterable[str]]) -> list[str] | None:
    """One cycle of the requires graph, or None (iterative DFS)."""
    white, grey, black = 0, 1, 2
    color = dict.fromkeys(graph, white)
    for root in sorted(graph):
        if color[root] != white:
            continue
        stack: list[tuple[str, list[str]]] = [(root, sorted(graph[root]))]
        path = [root]
        color[root] = grey
        while stack:
            node, todo = stack[-1]
            if not todo:
                stack.pop()
                path.pop()
                color[node] = black
                continue
            nxt = todo.pop(0)
            if color.get(nxt, black) == grey:
                return path[path.index(nxt) :]
            if color.get(nxt) == white:
                color[nxt] = grey
                path.append(nxt)
                stack.append((nxt, sorted(graph[nxt])))
    return None


def _reachable(graph: Mapping[str, Iterable[str]], start: str) -> set[str]:
    seen: set[str] = set()
    todo = list(graph.get(start, ()))
    while todo:
        node = todo.pop()
        if node not in seen:
            seen.add(node)
            todo.extend(graph.get(node, ()))
    return seen


def transitive_reduction(entries: list[SkillEntry]) -> tuple[list[Skill], list[tuple[str, str]]]:
    graph = {e.skill.id: list(e.skill.requires) for e in entries}
    out: list[Skill] = []
    removed: list[tuple[str, str]] = []
    for e in entries:
        s = e.skill
        implied: set[str] = set()
        for q in s.requires:
            implied |= _reachable(graph, q)
        keep = tuple(p for p in s.requires if p not in implied or p in e.chooses)
        removed += [(s.id, p) for p in s.requires if p not in keep]
        out.append(replace(s, requires=keep) if keep != s.requires else s)
    return out, removed


# ---------------------------------------------------------------- GRAPH-4 pool targets


@dataclass(frozen=True, slots=True)
class PoolLine:
    skill_id: str
    ok: bool
    message: str


def pool_report(skills: Iterable[Skill], cards: Iterable[Card]) -> list[PoolLine]:
    """GRAPH-4: name, section, textbook, confusable, a worked example, and a full pool
    (tiers 1-2: a template or 20+ fixed problems; tier 3: 10+; tiers 4-5: anything)."""
    by_skill: dict[str, list[Card]] = {}
    for card in cards:
        if card.skill_id is not None:
            by_skill.setdefault(card.skill_id, []).append(card)
    out: list[PoolLine] = []
    for s in skills:
        mine = by_skill.get(s.id, [])
        missing: list[str] = []
        if not s.deck:
            missing.append("section")
        if not s.textbook_ref:
            missing.append("textbook reference")
        if not s.confusable:
            missing.append("confusable skills")
        if not any(c.kind == "example" for c in mine):
            missing.append("worked example")
        problems = [c for c in mine if c.kind in {"problem", "find-error", "method"}]
        for tier in sorted({c.tier for c in problems}):
            at = [c for c in problems if c.tier == tier]
            fixed = sum(1 for c in at if c.template_id is None)
            templated = any(c.template_id is not None for c in at)
            if tier <= 2 and not templated and fixed < 20:
                missing.append(f"tier {tier} pool: {fixed} fixed problems, needs a template or 20")
            if tier == 3 and fixed + sum(1 for c in at if c.template_id) < 10:
                missing.append(f"tier 3 pool: {len(at)} problems, needs 10")
        if not problems and not s.method_choice:
            missing.append("no problems")
        message = "meets GRAPH-4" if not missing else "missing " + "; ".join(missing)
        out.append(PoolLine(s.id, not missing, message))
    return out
