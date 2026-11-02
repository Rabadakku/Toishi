"""A problem's components and the component a known wrong answer points at.

A component is a skill ID (student-model spec 2.1). A problem's component set is its
`skill`, its `uses`, its parts' own skills and the tags of its ### Solution steps; the
component rule (core.cards.cardfile) makes content packs agree on them. A `wrong:` answer's
`@step` names the solution step it comes from, so matching it is evidence about that
step's component (spec 2.3).
"""

from core.model import Card


def components(card: Card) -> tuple[str, ...]:
    """The card's component set: its skill, its uses, its parts' own skills, then its step
    tags in step order, each once. Empty for a card with no skill tags at all (a personal
    card scheduled on its own)."""
    found = [
        card.skill_id,
        *card.uses,
        *(p.skill_id for p in card.parts),
        *(s.skill_id for s in card.solution),
    ]
    return tuple(dict.fromkeys(c for c in found if c))


def step_component(card: Card, step: int | None) -> str | None:
    """The skill tag of ### Solution step number `step`, or None (no step, or no such step).
    A grader result's matched wrong answer gives it directly: `step_component(card,
    result.matched_wrong.step)`."""
    if step is None:
        return None
    return next((s.skill_id for s in card.solution if s.number == step), None)


def wrong_component(card: Card, matched_wrong: int | None, part: str | None = None) -> str | None:
    """The component of the solution step a matched known wrong answer names with `@step`.

    `matched_wrong` is an index into the card's `wrong` list, as the attempt column
    `matched_wrong` stores it (core.queue.answers.Checked.matched_index), or, with `part`,
    into that part's own list (PartVerdict.wrong_index). None when nothing matched, the
    wrong answer has no `@step`, or the index or part doesn't exist."""
    if matched_wrong is None:
        return None
    if part is None:
        wrong = card.wrong
    else:
        found = next((p for p in card.parts if p.label == part), None)
        if found is None:
            return None
        wrong = found.wrong
    if not 0 <= matched_wrong < len(wrong):
        return None
    return step_component(card, wrong[matched_wrong].step)
