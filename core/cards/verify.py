"""Pack-build verification beyond the self-check: differential checks and worked solutions.

- DEV-18 (`differential`): every number and expression key, and every `wrong` answer, is
  graded and then cross-checked by SymPy and our mpmath evaluator side by side
  (core.grader.cross_check). Template operations were cross-checked during the sweep
  (core/cards/differential.py); their tallies are summed here.
- MATH-17 (`solutions`): worked solutions are machine-checked. See check_solutions.

Both return errors (a pack with any does not build) and summary lines for the report.
"""

import re

from core.cards.checks import answer_spec
from core.cards.load import Accepted, LoadResult
from core.cards.sweep import SweepRunner
from core.cards.template import Claim, TemplateError, TemplateJob, parse_claim
from core.grader import AnswerSpec, Status, cross_check, grade
from core.grader.errors import SpecError
from core.grader.spec import MATH_TYPES
from core.model import Card, CardPart

CROSS_TYPES = frozenset({"number", "expression"})


def _targets(card: Card) -> list[tuple[str, CardPart | None]]:
    out: list[tuple[str, CardPart | None]] = []
    if card.answer_type in CROSS_TYPES:
        out.append(("answer", None))
    out += [(f"part {p.label}", p) for p in card.parts if p.answer_type in CROSS_TYPES]
    return out


def differential(loaded: LoadResult) -> tuple[list[str], list[str]]:
    """DEV-18 at pack build: (errors, summary lines)."""
    errors: list[str] = []
    checked = 0
    for item in loaded.cards:
        card = item.card
        for where, part in _targets(card):
            try:
                spec = answer_spec(card, part)
            except SpecError:
                continue  # the self-check reports a broken key
            texts = [t.strip() for t in spec.answer.split(";") if t.strip()]
            texts += [w.answer for w in spec.wrong]
            for text in texts:
                checked += 1
                for problem in cross_check(text, spec):
                    errors.append(f"{_where(item)}: {where} {text!r}: {problem}")
    ops = sum(t.cross_checked for t in loaded.templates.values())
    unverified = sum(t.cross_unverified for t in loaded.templates.values())
    summary = [
        f"differential checks (DEV-18): {checked} answers graded by both engines, "
        f"{ops} template operations agree with mpmath, {unverified} could not be recomputed"
    ]
    return errors, summary


def _where(item: Accepted) -> str:
    return f"{item.file}:{item.line}: card {item.card.template_id or item.card.id}"


# ---------------------------------------------------------------- worked solutions (MATH-17)

_MATH = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", re.DOTALL)


def solutions(loaded: LoadResult, runner: SweepRunner) -> tuple[list[str], list[str], list[str]]:
    """Check every worked solution: (errors, unverified, summary lines).

    In the cheapest form that works: each step's `check:` claims are verified by the CAS
    with an mpmath cross-check (template instances during the sweep, other cards here),
    and the final line must grade correct against the key: the last claim of the last
    step when there is one, else the last math of the last step after its last `=`. A
    step with math that no claim covers, or a final line that can't be matched, is listed
    as unverified, never passed silently.
    """
    errors: list[str] = []
    unverified: list[str] = []
    claims_checked = finals_checked = steps_unverified = 0
    for item in loaded.cards:
        card = item.card
        if not card.solution:
            continue
        where = _where(item)
        last = card.solution[-1].number
        final = item.final
        if card.template_id is None and item.claims:
            try:
                compiled = [parse_claim(c.text, c.step, c.line) for c in item.claims]
            except TemplateError as exc:
                errors.append(f"{item.file}:{exc.line or item.line}: card {card.id}: {exc.message}")
                continue
            sweep = runner.run(_job(card.id, item, compiled, last))
            if sweep.error is not None:
                errors.append(
                    f"{item.file}:{sweep.line or item.line}: card {card.id}: {sweep.error}"
                )
                continue
            final = sweep.instances[0].final if sweep.instances else None
        claims_checked += len(item.claims)
        covered = {c.step for c in item.claims}
        final_ok = False
        spec = _single_spec(card)
        if spec is not None and final is not None:
            result = grade(final, spec)
            if result.status != Status.CORRECT:
                errors.append(
                    f"{where}: the solution's final line {final!r} does not match the key "
                    f"{spec.answer!r} ({result.status.value})"
                )
                continue
            final_ok = True
        elif spec is not None:
            final_ok = _final_line_matches(card, spec)
        finals_checked += final_ok
        missing = [
            s.number
            for s in card.solution
            if _has_math(s.body_md)
            and s.number not in covered
            and not (s.number == last and final_ok)
        ]
        steps_unverified += len(missing)
        notes = []
        if missing:
            notes.append(f"steps {', '.join(map(str, missing))} have no check")
        if spec is not None and not final_ok:
            notes.append("the final line could not be matched to the key")
        if notes:
            unverified.append(f"{where}: {'; '.join(notes)}")
    unverified = list(dict.fromkeys(unverified))  # a template's instances share one line
    summary = [
        f"worked solutions (MATH-17): {claims_checked} step checks hold, "
        f"{finals_checked} final lines match the key, {steps_unverified} steps with math "
        f"unverified"
    ]
    return errors, unverified, summary


def _job(card_id: str, item: Accepted, claims: list[Claim], last: int) -> TemplateJob:
    return TemplateJob(
        template_id=card_id,
        file=item.file,
        first_line=item.line,
        lines=(),
        slots=(),
        claims=tuple(claims),
        final_step=last,
    )


def _single_spec(card: Card) -> AnswerSpec | None:
    if card.parts or card.answer_type not in MATH_TYPES:
        return None
    try:
        return answer_spec(card)
    except SpecError:
        return None


def _has_math(text: str) -> bool:
    return bool(_MATH.search(text))


def _final_line_matches(card: Card, spec: AnswerSpec) -> bool:
    """The last math of the last step, after its last `=`, graded against the key."""
    found = list(_MATH.finditer(card.solution[-1].body_md))
    if not found:
        return False
    tex = found[-1].group(1) if found[-1].group(1) is not None else found[-1].group(2)
    rhs = re.split(r"(?<![<>!\\])=", tex)[-1].strip().rstrip(".,;")
    if not rhs:
        return False
    return grade(rhs, spec, "mathlive").status == Status.CORRECT
