"""Hypothesis: the parsers never crash and every problem points at a line of the file."""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.cards import Source, load
from core.cards.skillfile import read_skills_file
from core.cards.sweep import SweepRunner
from core.cards.template import (
    SweepResult,
    TemplateError,
    TemplateJob,
    compile_expr,
    find_insertions,
)

PIECES = [
    "---", "format: mastery-cards 1", "format: mastery-skills 1", "deck: A::B::C", "deck: ::",
    "## Card a.001", "## Card a.002", "## Card", "## Card A!", "## Skill s.a", "## Note", "##",
    "### Question", "### Solution", "### Hints", "### Choices", "### Part a", "### Part b",
    "### Shown Work", "### Reasons", "### Front", "### Back", "### Text", "### Rubric", "### X",
    "#### Deep", "kind: find-error", "kind: cloze", "kind: flashcard", "kind: method", "kind: x",
    "answer-type: number", "answer-type: choice", "answer-type: set", "answer: 2", "answer: (1,",
    "answer: solve(x^2 - k, x)", "vars: k = int(1, 3)", "vars: k = int(", "let: f = k*x",
    "require: k != 2", "require: k", "wrong: 3 => no @1", "wrong: => @", "error-step: 1",
    "difficulty: 9", "skill: s.a", "uses: s.a, ,", "requires: s.a", "encompasses: s.a = 0.3",
    "chooses: s.a", "name: A", "core: maybe", "exam-tier: 6", "0. [s.a] Set up: x",
    "1. [s.a] Go: \\(x", "2. text", "1. hint", "- [x] yes", "- [ ] no", "* [x] star",
    "{{c1::blank}}", "{{c1:bad", "\\(x^2\\)", "\\[\\frac{1}{2\\]", "[[k]]", "[[tex(f)]]", "[[",
    "![g](media/g.svg)", "![g](http://x/g.png)", "<!--", "-->", "<!-- c -->", "", " ", "\t",
    "plot: x^2, x = 0..1", "plot: nope", "cue: required", "calculator: maybe", "$x^2$",
    "time: 2.5", "time: 0", "time: [[k]]", "time: soon",
    "## Section A::B::C", "## Section", "## Section ::", "hours: 3", "hours: x",
    "pace-minutes-per-step: 1.5", "pace-weekly-hours: 0",
]  # fmt: skip

lines = st.lists(st.one_of(st.sampled_from(PIECES), st.text(max_size=30)), max_size=40)


class NoSweeps(SweepRunner):
    """Templates are compiled (that is the parser's job) but not evaluated here."""

    def run(self, job: TemplateJob) -> SweepResult:
        return SweepResult(error="not evaluated in this test", line=job.first_line)


def assert_located(problems: list[tuple[int, str]], text: str) -> None:
    count = max(len(text.replace("\r\n", "\n").replace("\r", "\n").split("\n")), 1)
    for line, message in problems:
        assert 1 <= line <= count, (line, message)
        assert message


@settings(
    max_examples=400, deadline=None, database=None, suppress_health_check=[HealthCheck.too_slow]
)
@given(lines, st.booleans())
def test_card_files_never_crash(parts: list[str], pack: bool) -> None:
    text = "\n".join(parts)
    result = load([Source("f.cards.md", text)], pack=pack, self_check=False, runner=NoSweeps())
    found = [(p.line, p.message) for p in result.file_problems + result.warnings]
    for r in result.rejected:
        assert r.reasons
        found += r.located()
    assert_located(found, text)


@settings(max_examples=200, deadline=None, database=None)
@given(lines)
def test_card_files_with_a_header_never_crash(parts: list[str]) -> None:
    text = "---\nformat: mastery-cards 1\n---\n" + "\n".join(parts)
    result = load([Source("f.cards.md", text.encode())], self_check=False, runner=NoSweeps())
    found = [(p.line, p.message) for p in result.file_problems + result.warnings]
    for r in result.rejected:
        found += r.located()
    assert_located(found, text)


@settings(max_examples=200, deadline=None, database=None)
@given(lines)
def test_skills_files_never_crash(parts: list[str]) -> None:
    text = "---\nformat: mastery-skills 1\n---\n" + "\n".join(parts)
    _, problems = read_skills_file(text, "skills.md")
    assert_located([(p.line, p.message) for p in problems], text)


@settings(max_examples=300, deadline=None, database=None)
@given(st.text(alphabet="kx+-*/^()[],;=<> 0123456789.difntegrlmsovpacxbu_'", max_size=60))
def test_template_expressions_only_raise_template_errors(text: str) -> None:
    for attempt in (lambda: compile_expr(text), lambda: find_insertions(f"a [[{text}]] b")):
        try:
            attempt()
        except TemplateError as exc:  # the only error allowed, always with a message
            message = exc.message
            assert message


@settings(max_examples=100, deadline=None, database=None)
@given(st.binary(max_size=200))
def test_any_bytes_give_located_problems(data: bytes) -> None:
    result = load([Source("f.cards.md", data)], self_check=False, runner=NoSweeps())
    text = data.decode("utf-8", errors="replace")
    found = [(p.line, p.message) for p in result.file_problems]
    for r in result.rejected:
        found += r.located()
    assert_located(found, text)
