"""Method-choice skills (ENG-16), which-method and find-the-error items, self-graded problems.

- A method-choice skill's prerequisites (`requires`) are the methods it chooses among; it is
  active once two of them are learned. Uncued problems on those methods count toward it
  (reading: an uncued problem served while it is due counts as its review, Good when the
  method was chosen right; a Step 0 miss is settled by the cued twin); cued ones don't.
- Which-method items (kind "method") are problems of the method-choice skill: base grading
  rates them as its reviews. The queue mixes them in; they never replace a full problem.
- Find-the-error items unlock for a skill after two successful uncued reviews, come at most
  once in every N reviews (setting, 1 in 10), are graded on the step, the reason and the
  corrected value, and count as a review of the skill. Early on a highlighted version is used.
- Self-graded problems: rubric all / all but one / fewer ticked -> Good / Hard / Again;
  without a rubric, Matched / Minor slip / Didn't get it (rating.py does the mapping).
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from core.engine.diagnosis.config import (
    FIND_ERROR_HIGHLIGHT_UNTIL,
    FIND_ERROR_UNLOCK,
    METHOD_ACTIVE_LEARNED,
)
from core.engine.diagnosis.verdict import attempt_success, diagnosis_of
from core.engine.lifecycle import in_learning_phase
from core.engine.rating import AnswerFacts, SelfGrade
from core.model import Attempt, Card, CardKind, Skill, SkillState


def method_choice_skill(skill_id: str, skills: Mapping[str, Skill]) -> Skill | None:
    """The method-choice skill that chooses among methods including `skill_id`: one that
    requires it (same section first), else the method-choice skill of its section."""
    own = skills.get(skill_id)
    if own is None or own.method_choice:
        return None
    section = own.section_id
    choosers = sorted(
        (m for m in skills.values() if m.method_choice and skill_id in m.requires),
        key=lambda m: (m.section_id != section, m.id),
    )
    if choosers:
        return choosers[0]
    same = sorted(m.id for m in skills.values() if m.method_choice and m.section_id == section)
    return skills[same[0]] if same and section is not None else None


def method_choice_active(method: Skill, state_of: Callable[[str], SkillState | None]) -> bool:
    learned = sum(1 for k in method.requires if not in_learning_phase(state_of(k)))
    return learned >= METHOD_ACTIVE_LEARNED


def shown_cued(*, cued_flag: bool, stage: str, check_kind: str | None, cue_required: bool) -> bool:
    """Was the problem shown with its method named? Learning blocks (first exposure),
    cued-twin checks and `cue: required` cards are cued; the queue may also say so."""
    return cued_flag or cue_required or stage == "learning" or check_kind == "cued-twin"


# ---------------------------------------------------------------- find-the-error


def _uncued_review_successes(history: Sequence[Attempt]) -> int:
    count = 0
    for a in history:
        d = diagnosis_of(a)
        if a.voided_by is not None or not a.final or a.card_kind != "problem":
            continue
        if a.extra.get("stage") == "review" and attempt_success(a) and not d.get("cued", False):
            count += 1
    return count


def find_error_unlocked(history: Sequence[Attempt]) -> bool:
    """Two successful uncued reviews of the skill."""
    return _uncued_review_successes(history) >= FIND_ERROR_UNLOCK


def find_error_highlighted(history: Sequence[Attempt]) -> bool:
    """Early on ("Step 3 is wrong. Why?"): until two find-the-error items were solved."""
    solved = sum(
        1
        for a in history
        if a.voided_by is None and a.final and a.card_kind == "find-error" and attempt_success(a)
    )
    return solved < FIND_ERROR_HIGHLIGHT_UNTIL


def find_error_slot_open(recent: Sequence[CardKind], one_in: int | None) -> bool:
    """At most one find-the-error item in every `one_in` reviews: none among the last
    one_in - 1 items served (most recent last). None: the setting is Off."""
    if one_in is None:
        return False
    window = list(recent)[-(one_in - 1) :] if one_in > 1 else []
    return "find-error" not in window


@dataclass(frozen=True, slots=True, kw_only=True)
class FindErrorGrade:
    step_ok: bool
    reason_ok: bool
    value_ok: bool

    @property
    def correct(self) -> bool:
        return self.step_ok and self.reason_ok and self.value_ok

    def facts(self, **kw: object) -> AnswerFacts:
        return AnswerFacts(correct=self.correct, **kw)  # type: ignore[arg-type]


def grade_find_error(
    card: Card, *, step: int | None, reason: int | None, value_correct: bool
) -> FindErrorGrade:
    """Graded on the step (the card's error-step), the reason (the one right choice among
    ### Reasons, by index) and the corrected value (checked by the answer checker)."""
    right = next((i for i, r in enumerate(card.reasons) if r.correct), None)
    return FindErrorGrade(
        step_ok=card.error_step is not None and step == card.error_step,
        reason_ok=right is not None and reason == right,
        value_ok=value_correct,
    )


# ---------------------------------------------------------------- self-graded problems


def self_graded_facts(
    *,
    rubric_total: int | None = None,
    rubric_ticked: int | None = None,
    choice: SelfGrade | None = None,
    **kw: object,
) -> AnswerFacts:
    """Facts for a self-graded problem: rubric ticks when the card has a rubric, else the
    three buttons (Matched / Minor slip / Didn't get it)."""
    if rubric_total is not None:
        ticked = max(0, min(rubric_total, rubric_ticked or 0))
        return AnswerFacts(correct=False, rubric_total=rubric_total, rubric_ticked=ticked, **kw)  # type: ignore[arg-type]
    return AnswerFacts(correct=False, self_grade=choice or "missed", **kw)  # type: ignore[arg-type]
