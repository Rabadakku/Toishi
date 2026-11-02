"""Import rules: every rejection names the exact file and line; warnings never reject."""

from pathlib import Path

import pytest

from core.cards import Source, load
from tests.cards.helpers import HEADER, cards_file, load_text, only_card, rejection

OK_CARD = """
## Card ok.001
skill: s.one
difficulty: 1
answer-type: number
answer: 2

### Question
What is \\(1 + 1\\)?

### Hints
1. Count.

### Solution
0. [s.one] Add: \\(1 + 1 = 2\\).
"""


def line_of(text: str, marker: str, nth: int = 1) -> int:
    hits = [i for i, line in enumerate(text.split("\n"), start=1) if marker in line]
    return hits[nth - 1]


def rejected_at(
    body: str, marker: str, fragment: str, *, header: str = HEADER, nth: int = 1
) -> None:
    text = cards_file(body, header)
    line, reason = rejection(load_text(text))
    assert (line, fragment in reason) == (line_of(text, marker, nth), True), reason


# ---------------------------------------------------------------- the file


def test_header_is_required() -> None:
    result = load_text("## Card a.001\n\n### Question\nQ\n")
    assert [(p.line, p.message) for p in result.file_problems] == [
        (1, "the file must start with a '---' header")
    ]


@pytest.mark.parametrize(
    ("header", "marker", "fragment"),
    [
        ("---\nformat: mastery-cards 2\n---\n", "format:", "this app reads 'mastery-cards 1'"),
        ("---\ndeck: A\n---\n", "---", "the header has no 'format:' line"),
        ("---\nformat: mastery-cards 1\ncolour: red\n---\n", "colour", "unknown key 'colour'"),
        ("---\nformat: mastery-cards 1\nanswer: 2\n---\n", "answer:", "can't be a file default"),
        ("---\nformat: mastery-cards 1\ntime: 5\n---\n", "time:", "can't be a file default"),
        ("---\nformat: mastery-cards 1\n", "---", "never closed"),
        ("---\nformat: mastery-cards 1\nnot a key\n---\n", "not a key", "expected 'key: value'"),
    ],
)
def test_header_errors_reject_the_file(header: str, marker: str, fragment: str) -> None:
    text = header + OK_CARD
    result = load_text(text)
    assert result.cards == []
    problem = result.file_problems[0]
    assert problem.line == line_of(text, marker)
    assert fragment in problem.message


def test_not_utf8_names_the_line() -> None:
    data = (HEADER + OK_CARD).encode() + b"\n\xff\xfe broken\n"
    result = load([Source("bad.cards.md", data)])
    assert [(p.line, p.message) for p in result.file_problems] == [
        (len((HEADER + OK_CARD).split("\n")) + 1, "the file is not UTF-8 text")
    ]


def test_text_outside_a_card() -> None:
    text = HEADER + "stray words\n" + OK_CARD
    result = load_text(text)
    assert [(p.line, p.message) for p in result.file_problems] == [
        (5, "'stray words' outside a block: start one with '## Card <id>'")
    ]


def test_unclosed_comment() -> None:
    text = cards_file("<!-- never closed\n" + OK_CARD)
    result = load_text(text)
    assert result.file_problems[0].line == line_of(text, "<!--")
    assert "never closed" in result.file_problems[0].message


def test_comments_keep_line_numbers() -> None:
    body = "<!-- one\ntwo\nthree -->\n" + OK_CARD.replace("answer: 2", "answer: 2 +")
    rejected_at(body, "answer: 2 +", "answer '2 +'")


# ---------------------------------------------------------------- ids


def test_missing_id() -> None:
    rejected_at("## Card\n\n### Question\nQ\n", "## Card", "needs an ID")


def test_bad_id() -> None:
    rejected_at("## Card Bad_ID\n\n### Question\nQ\n", "## Card", "bad ID 'Bad_ID'")


def test_double_dash_is_reserved_for_instances() -> None:
    rejected_at("## Card a--b\n\n### Question\nQ\n### Solution\nS\n", "## Card", "'--'")


def test_duplicate_ids_in_one_file_reject_both() -> None:
    text = cards_file(OK_CARD + OK_CARD)
    result = load_text(text)
    assert result.cards == []
    lines = sorted(r.line for r in result.rejected)
    assert lines == [line_of(text, "## Card"), line_of(text, "## Card", 2)]
    assert all("duplicate ID ok.001" in r.reasons[0] for r in result.rejected)


def test_duplicate_ids_across_files() -> None:
    result = load(
        [Source("a.cards.md", cards_file(OK_CARD)), Source("b.cards.md", cards_file(OK_CARD))]
    )
    assert result.cards == []
    assert sorted((r.file, r.line) for r in result.rejected) == [
        ("a.cards.md", 6),
        ("b.cards.md", 6),
    ]
    assert (
        "also at b.cards.md:6"
        in next(r for r in result.rejected if r.file == "a.cards.md").reasons[0]
    )


def test_one_bad_card_does_not_reject_the_others() -> None:
    result = load_text(cards_file(OK_CARD + "\n## Card bad.001\nkind: puzzle\n\n### Question\nQ\n"))
    assert [a.card.id for a in result.cards] == ["ok.001"]
    assert [r.card_id for r in result.rejected] == ["bad.001"]


# ---------------------------------------------------------------- keys and sections


def test_unknown_kind() -> None:
    rejected_at("## Card a.001\nkind: puzzle\n\n### Question\nQ\n", "kind:", "kind: expected")


def test_unknown_answer_type() -> None:
    rejected_at(
        "## Card a.001\nanswer-type: fraction\nanswer: 1/2\n\n### Question\nQ\n",
        "answer-type:",
        "fraction",
    )


def test_unknown_key() -> None:
    rejected_at("## Card a.001\nanwser: 2\n\n### Question\nQ\n", "anwser", "unknown key 'anwser'")


def test_duplicate_key() -> None:
    rejected_at(
        "## Card a.001\nskill: a\nskill: b\n\n### Question\nQ\n", "skill: b", "skill appears twice"
    )


def test_key_without_value() -> None:
    rejected_at("## Card a.001\nskill:\n\n### Question\nQ\n", "skill:", "skill has no value")


def test_text_where_keys_belong() -> None:
    rejected_at(
        "## Card a.001\nSome words\n\n### Question\nQ\n", "Some words", "expected 'key: value'"
    )


def test_no_question() -> None:
    rejected_at("## Card a.001\n\n### Solution\nS\n", "## Card", "has no ### Question")


def test_unknown_section() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nQ\n\n### Workings\nW\n", "### Workings", "unknown section"
    )


def test_duplicate_section() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nQ\n\n### Question\nQ2\n",
        "### Question",
        "appears twice",
        nth=2,
    )


def test_section_not_for_this_kind() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nQ\n\n### Front\nF\n", "### Front", "isn't used by problem"
    )


def test_flashcard_needs_back() -> None:
    rejected_at("## Card a.001\nkind: flashcard\n\n### Front\nF\n", "## Card", "has no ### Back")


def test_cloze_needs_a_blank() -> None:
    rejected_at(
        "## Card a.001\nkind: cloze\n\n### Text\nNo blanks here.\n",
        "No blanks",
        "no {{c1::...}} blank",
    )


def test_cloze_must_be_well_formed() -> None:
    rejected_at(
        "## Card a.001\nkind: cloze\n\n### Text\nA\nB {{c1:oops}}\n", "{{c1:oops", "a cloze blank"
    )


def test_choice_needs_choices() -> None:
    rejected_at(
        "## Card a.001\nanswer-type: choice\n\n### Question\nQ\n", "answer-type:", "### Choices"
    )


def test_choices_need_choice_type() -> None:
    body = "## Card a.001\n\n### Question\nQ\n\n### Choices\n- [x] A\n- [ ] B\n"
    rejected_at(body, "### Choices", "needs answer-type: choice")


def test_choices_must_be_a_checklist() -> None:
    body = "## Card a.001\nanswer-type: choice\n\n### Question\nQ\n\n### Choices\n- [x] A\n* B\n"
    rejected_at(body, "* B", "expected '- [x] ...'")


def test_answer_with_self_type() -> None:
    rejected_at("## Card a.001\nanswer: 2\n\n### Question\nQ\n", "answer:", "answer-type is self")


def test_multipart_card_with_its_own_answer() -> None:
    body = (
        "## Card a.001\nanswer-type: number\nanswer: 2\n\n### Question\nQ\n\n"
        "### Part a\nanswer-type: number\nanswer: 1\nPrompt\n"
    )
    rejected_at(body, "answer-type: number", "multi-part card")


def test_part_unknown_key_and_missing_prompt() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nQ\n\n### Part a\nanser: 2\nP\n", "anser", "in ### Part a"
    )
    rejected_at(
        "## Card a.001\n\n### Question\nQ\n\n### Part a\nanswer-type: self\n",
        "### Part a",
        "no prompt",
    )


# ---------------------------------------------------------------- steps


def test_step_numbers_must_follow_on() -> None:
    body = (
        "## Card a.001\n\n### Question\nQ\n\n### Solution\n0. [s.a] Set up: x\n2. [s.a] Next: y\n"
    )
    rejected_at(body, "2. [s.a]", "step 2 should be step 1")


def test_steps_start_at_zero_or_one() -> None:
    body = "## Card a.001\n\n### Question\nQ\n\n### Solution\n3. [s.a] Set up: x\n"
    rejected_at(body, "3. [s.a]", "steps start at 0 or 1")


def test_every_step_needs_a_tag_and_label() -> None:
    body = "## Card a.001\n\n### Question\nQ\n\n### Solution\n0. [s.a] Set up: x\n1. Then this.\n"
    rejected_at(body, "1. Then", "write it as 1. [skill-id] Label: ...")


def test_a_tagged_list_starts_at_the_top() -> None:
    body = "## Card a.001\n\n### Question\nQ\n\n### Solution\nIntro.\n\n1. [s.a] Go: x\n"
    rejected_at(body, "1. [s.a]", "must start at the first line")


def test_wrong_answer_step_must_exist() -> None:
    body = OK_CARD.replace("answer: 2", "answer: 2\nwrong: 3 => no @4")
    rejected_at(body, "wrong:", "points at @4")


# ---------------------------------------------------------------- find-error and method


FIND_ERROR = """
## Card fe.001
kind: find-error
skill: s.a
error-step: 2
answer-type: number
answer: 4

### Question
Compute \\(2 + 2\\).

### Shown Work
1. [s.a] Add: \\(2 + 2 = 5\\).

### Reasons
- [x] It is wrong
- [ ] It is right
- [ ] Both

### Solution
1. [s.a] Add: \\(2 + 2 = 4\\).
"""


def test_find_error_step_must_be_shown() -> None:
    rejected_at(FIND_ERROR, "error-step:", "error-step 2 is not a step of ### Shown Work")


def test_find_error_needs_error_step() -> None:
    rejected_at(FIND_ERROR.replace("error-step: 2\n", ""), "## Card", "needs error-step")


def test_find_error_needs_one_right_reason() -> None:
    body = FIND_ERROR.replace("error-step: 2", "error-step: 1").replace(
        "- [ ] It is right", "- [x] It is right"
    )
    rejected_at(body, "### Reasons", "exactly one [x], not 2")


def test_method_cards_are_choices() -> None:
    body = (
        "## Card m.001\nkind: method\nanswer-type: number\nanswer: 1\n\n"
        "### Question\nQ\n\n### Solution\nS\n"
    )
    rejected_at(body, "answer-type:", "method cards need answer-type: choice")


# ---------------------------------------------------------------- answers (self-check)


def test_answer_that_wont_parse() -> None:
    rejected_at(OK_CARD.replace("answer: 2", "answer: 2 +"), "answer: 2 +", "answer '2 +'")


def test_key_must_have_the_right_shape() -> None:
    rejected_at(OK_CARD.replace("answer: 2", "answer: 1, 2"), "answer: 1, 2", "answer '1, 2'")


def test_wrong_answer_that_grades_correct() -> None:
    body = OK_CARD.replace("answer: 2", "answer: 1/2\nwrong: 0.5 => no")
    rejected_at(body, "answer: 1/2", "wrong answer '0.5' grades correct")


def test_part_key_is_checked_on_its_own_line() -> None:
    body = "## Card a.001\n\n### Question\nQ\n\n### Part a\nanswer-type: point\nanswer: 3\nP\n"
    rejected_at(body, "answer: 3", "### Part a:")


def test_quantity_is_not_supported_yet() -> None:
    body = "## Card a.001\nanswer-type: quantity\nanswer: 9.8 m/s^2\n\n### Question\nQ\n"
    rejected_at(body, "answer:", "not supported until version 1.1")


def test_checker_option_is_validated() -> None:
    rejected_at(
        OK_CARD.replace("answer: 2", "answer: 2\nexact: maybe"),
        "answer: 2",
        "exact: expected yes or no",
    )


# ---------------------------------------------------------------- math and images


def test_math_that_wont_render() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nLine one\nSolve \\(x^2 = 4.\n", "Solve", "never closed"
    )


def test_unbalanced_braces_in_math() -> None:
    rejected_at(
        "## Card a.001\n\n### Question\nFind \\(\\frac{1}{2\\).\n", "Find", "unbalanced braces"
    )


def test_missing_image(tmp_path: Path) -> None:
    from core.cards import DirMedia

    text = cards_file("## Card a.001\n\n### Question\nSee\n![a graph](media/nope.svg)\n")
    result = load([Source("c.cards.md", text, DirMedia(tmp_path))])
    line, reason = rejection(result)
    assert (line, reason) == (
        line_of(text, "!["),
        "image 'media/nope.svg' not found next to c.cards.md",
    )


def test_image_found_and_recorded(tmp_path: Path) -> None:
    from core.cards import DirMedia

    (tmp_path / "media").mkdir()
    (tmp_path / "media" / "g.png").write_bytes(b"\x89PNG")
    text = cards_file("## Card a.001\n\n### Question\n![a graph](media/g.png)\n\n### Solution\nS\n")
    result = load([Source("c.cards.md", text, DirMedia(tmp_path))])
    assert not result.errors()
    assert list(result.media) == ["media/g.png"]


@pytest.mark.parametrize(
    ("ref", "fragment"),
    [
        ("media/g.gif", "SVG or PNG"),
        ("https://example.org/g.png", "relative to the card file"),
        ("/etc/g.png", "relative to the card file"),
    ],
)
def test_bad_image_references(ref: str, fragment: str) -> None:
    rejected_at(f"## Card a.001\n\n### Question\n![g]({ref})\n", "![g]", fragment)


def test_image_outside_the_folder(tmp_path: Path) -> None:
    from core.cards import DirMedia

    (tmp_path / "secret.png").write_bytes(b"x")
    root = tmp_path / "deck"
    root.mkdir()
    text = cards_file("## Card a.001\n\n### Question\n![g](../secret.png)\n")
    _, reason = rejection(load([Source("c.cards.md", text, DirMedia(root))]))
    assert "not found" in reason


# ---------------------------------------------------------------- time:


def test_time_is_a_card_and_part_key() -> None:
    card = only_card(load_text(cards_file(OK_CARD.replace("difficulty: 1", "time: 2.5"))))
    assert card.time_minutes == 2.5
    parts = PARTS_CARD.replace("answer: 3\n", "answer: 3\ntime: 4\n")
    card = only_card(load_text(cards_file(parts.replace("difficulty: 2", "time: 6"))))
    assert (card.time_minutes, [p.time_minutes for p in card.parts]) == (6.0, [None, 4.0])


@pytest.mark.parametrize(
    "value", ["0", "0.0", "-1", "abc", "1e3", "1/2", ".5", "2,5", "inf", "nan", "٣"]
)
def test_time_is_a_positive_number_of_minutes(value: str) -> None:
    body = OK_CARD.replace("difficulty: 1", f"difficulty: 1\ntime: {value}")
    rejected_at(body, "time:", f"time: expected a positive number of minutes, got {value!r}")


def test_a_parts_time_is_checked_on_its_line() -> None:
    body = PARTS_CARD.replace("answer: 3\n", "answer: 3\ntime: soon\n")
    rejected_at(body, "time: soon", "### Part b: time: expected a positive number of minutes")


@pytest.mark.parametrize(
    ("kind", "body"),
    [
        ("flashcard", "\n### Front\nF\n\n### Back\nB\n"),
        ("cloze", "\n### Text\n{{c1::a}}\n"),
        ("example", "skill: s.one\n\n### Question\nQ\n\n### Solution\n0. [s.one] Go: x\n"),
    ],
)
def test_only_graded_kinds_have_a_standard_time(kind: str, body: str) -> None:
    card = f"## Card k.001\nkind: {kind}\ntime: 3\n" + body
    rejected_at(card, "time:", f"time: {kind} cards have no standard time")


def test_a_templates_time_is_checked_in_each_instance() -> None:
    body = OK_CARD.replace("answer: 2", "vars: k = int(1, 3)\nanswer: k + 1\ntime: [[k]]")
    body = body.replace("What is \\(1 + 1\\)?", "What is \\([[k]] + 1\\)?")
    result = load_text(cards_file(body))
    assert not result.errors(), result.errors()
    assert sorted(a.card.time_minutes or 0 for a in result.cards) == [1.0, 2.0, 3.0]
    result = load_text(cards_file(body.replace("time: [[k]]", "time: [[k - 2]]")))
    (rejected,) = result.rejected
    assert "time: expected a positive number of minutes" in rejected.reasons[0]


# ---------------------------------------------------------------- warnings


def warnings_of(body: str) -> list[tuple[int, str]]:
    text = cards_file(body)
    result = load_text(text)
    assert not result.errors(), result.errors()
    return [(w.line, w.message) for w in result.warnings]


def test_dollar_math_warns() -> None:
    found = warnings_of(OK_CARD.replace("What is \\(1 + 1\\)?", "What is $x^2$ at 1?"))
    assert any("$x^2$" in m and "looks like math" in m for _, m in found)


def test_dollars_that_are_money_dont_warn() -> None:
    found = warnings_of(
        OK_CARD.replace("What is \\(1 + 1\\)?", "A pen costs $1 and a pad $2; how much is 1 + 1?")
    )
    assert found == []


def test_no_hints_and_default_difficulty_warn() -> None:
    body = OK_CARD.replace("difficulty: 1\n", "").replace("### Hints\n1. Count.\n", "")
    found = warnings_of(body)
    assert sorted(m for _, m in found) == ["no ### Hints", "no difficulty (it defaults to 2)"]
    assert {line for line, _ in found} == {6}


def test_near_duplicate_text_warns() -> None:
    a = OK_CARD.replace(
        "What is \\(1 + 1\\)?",
        "A farmer has some apples and gives away a few; what is \\(1 + 1\\)?",
    )
    b = a.replace("ok.001", "ok.002").replace("gives away a few", "gives away a few.")
    found = warnings_of(a + b)
    assert any("nearly the same text as card ok.001" in m for _, m in found)


def test_same_wording_different_math_is_not_a_duplicate() -> None:
    a = OK_CARD.replace(
        "What is \\(1 + 1\\)?", "Evaluate the following expression for me please: \\(1 + 1\\)"
    )
    b = a.replace("ok.001", "ok.002").replace("\\(1 + 1\\)", "\\(5 - 3\\)")
    assert not any("same text" in m for _, m in warnings_of(a + b))


def test_step_tags_should_match_skill_and_uses() -> None:
    found = warnings_of(OK_CARD.replace("0. [s.one]", "0. [s.other]"))
    assert (7, "step tags not in skill or uses: s.other") in found


PARTS_CARD = """
## Card parts.001
skill: s.one
uses: s.three
difficulty: 2

### Question
Q

### Part a
answer-type: number
answer: 2
What is \\(1 + 1\\)?

### Part b
answer-type: number
answer: 3
skill: s.two
What is \\(1 + 2\\)?

### Hints
1. Count.

### Solution
0. [s.one] Add: \\(1 + 1 = 2\\).
1. [s.one] Add: \\(1 + 2 = 3\\).
"""


def test_personal_cards_only_warn_when_uses_and_part_skills_tag_no_step() -> None:
    """The component rule stops a pack build (tests/cards/test_pack.py); personal decks
    import with warnings."""
    text = cards_file(PARTS_CARD)
    result = load_text(text)
    assert not result.errors()
    assert [a.card.id for a in result.cards] == ["parts.001"]
    found = [(w.line, w.message) for w in result.warnings]
    assert (line_of(text, "uses: s.three"), "uses: no solution step is tagged s.three") in found
    assert (line_of(text, "skill: s.two"), "### Part b: no solution step is tagged s.two") in found
    tagged = PARTS_CARD.replace("1. [s.one]", "1. [s.two]").replace("uses: s.three\n", "")
    assert not any("tagged" in m or "step tags" in m for _, m in warnings_of(tagged))
