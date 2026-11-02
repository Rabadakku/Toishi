"""From a card to the checker: answer specs per part, and the check of one submission.

The checker is injectable (`Checker`, default core.grader.grade) so the queue can be
tested without the SymPy worker. A syntax or shape error never counts as an attempt; a
case the checker can't decide goes to self-grading and is logged for grader review.
"""

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from core import grader
from core.cards import answer_spec
from core.grader import AnswerSpec, Status
from core.model import Card, CardPart

type Source = Literal["text", "mathlive"]
type Checker = Callable[[str, AnswerSpec, Source], grader.GradeResult]
type Previewer = Callable[[str, AnswerSpec, Source], grader.Preview]


def default_checker(raw: str, spec: AnswerSpec, source: Source) -> grader.GradeResult:
    return grader.grade(raw, spec, source)


def default_previewer(raw: str, spec: AnswerSpec, source: Source) -> grader.Preview:
    return grader.preview(raw, spec, source)


@dataclass(frozen=True, slots=True)
class PartSpec:
    label: str | None  # None for a single-part card
    spec: AnswerSpec
    expected_chars: int


def specs_for(card: Card) -> list[PartSpec]:
    """One spec per answer box: the card's parts, or the card itself (core.cards builds
    the spec from the stored key lines exactly as the importer checked them)."""
    out = []
    for part in card.parts or (None,):
        source: Card | CardPart = part if part is not None else card
        try:
            spec = answer_spec(card, part)
        except grader.errors.SpecError:  # a broken key line: the checker reports it
            spec = AnswerSpec(answer_type=source.answer_type, answer=source.answer or "")
        label = part.label if part is not None else None
        out.append(PartSpec(label, spec, len(source.answer or "")))
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class PartVerdict:
    part: str | None
    status: str  # grader.Status value
    read_as: str | None
    message: str = ""
    feedback: str | None = None  # the known wrong answer's feedback
    wrong_step: int | None = None
    wrong_index: int | None = None  # which of the card's (or part's) `wrong` entries matched


@dataclass(frozen=True, slots=True, kw_only=True)
class Checked:
    verdicts: tuple[PartVerdict, ...]

    @property
    def invalid(self) -> bool:
        return any(v.status == Status.INVALID for v in self.verdicts)

    @property
    def undecided(self) -> bool:
        return any(v.status in (Status.UNDECIDABLE, Status.UNSUPPORTED) for v in self.verdicts)

    @property
    def correct(self) -> bool:
        return bool(self.verdicts) and all(v.status == Status.CORRECT for v in self.verdicts)

    @property
    def matched_wrong(self) -> int | None:
        """The solution step of the first known wrong answer matched."""
        return next((v.wrong_step for v in self.verdicts if v.wrong_step is not None), None)

    @property
    def matched_index(self) -> int | None:
        """Index into the card's `wrong` list of the known wrong answer matched (single-box
        cards; a part's wrong answers are the part's own). ProblemOutcome.matched_wrong."""
        if len(self.verdicts) != 1 or self.verdicts[0].part is not None:
            return None
        return self.verdicts[0].wrong_index


def check_answers(
    card: Card,
    answers: Sequence[tuple[str | None, str]],
    source: Source,
    checker: Checker,
    *,
    only: Collection[str | None] | None = None,
) -> Checked:
    """`answers`: (part label or None, raw text) per box. A missing box is an empty answer.
    `only`: check just these parts (a multi-part problem's parts still open)."""
    given = dict(answers)
    out = []
    for part in specs_for(card):
        if only is not None and part.label not in only:
            continue
        raw = given.get(part.label, given.get(None, "") if part.label is None else "")
        if part.spec.answer_type == "self":
            out.append(PartVerdict(part=part.label, status=Status.UNSUPPORTED, read_as=None))
            continue
        result = checker(raw, part.spec, source)
        wrong = result.matched_wrong
        index = (
            next((i for i, w in enumerate(part.spec.wrong) if w == wrong), None)
            if wrong is not None
            else None
        )
        out.append(
            PartVerdict(
                part=part.label,
                status=str(result.status),
                read_as=result.read_as_latex,
                message=result.message,
                feedback=wrong.feedback if wrong is not None else None,
                wrong_step=wrong.step if wrong is not None else None,
                wrong_index=index,
            )
        )
    return Checked(verdicts=tuple(out))
