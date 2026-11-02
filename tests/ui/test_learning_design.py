"""The wave 2 learning design on the study screen, on the mock bridge.

docs/design/wave2-integration.md section 5 and the coordinator's v1.3 changes: no help
during practice (no hints, no "What went wrong?" picker); a wrong try is "Not quite" with
Retry and Give up and nothing else, any number of times, and only the first try counts;
Give up shows the solution, where a matched wrong answer's feedback appears; each problem
names its textbook section; a closed-book sitting shows its place, the skill block's time
limit and the block's time so far, and cuts nothing off; the stuck ladder's items carry a
short reason, and a skill set aside gets a one-line notice with its textbook pointer.
"""

import re

from playwright.sync_api import Locator, Page, expect

from tests.ui.conftest import Guarded, LocalServer


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def study(page: Page, server: LocalServer, scenario: str | None = None) -> None:
    query = f"&scenario={scenario}" if scenario else ""
    page.goto(f"{server.origin}/index.html?bridge=mock{query}#/study")
    expect(tid(page, "field-main")).to_be_focused()


def type_plain(page: Page, text: str) -> None:
    """From the focused math field: ` switches to plain text, then type."""
    page.keyboard.press("`")
    plain = page.locator("input[data-testid=field-main]")
    expect(plain).to_be_focused()
    page.keyboard.type(text)
    expect(plain).to_have_value(text)


def give_up(page: Page) -> None:
    """Out of the answer box, G gives up: the solution, and Continue is ready."""
    expect(tid(page, "field-main")).to_be_focused()
    page.keyboard.press("Tab")
    page.keyboard.press("g")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "incorrect")
    expect(tid(page, "continue")).to_be_enabled()


# --- no help during practice -------------------------------------------------------


def test_no_hint_button_no_hint_key_and_no_error_picker(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server)
    expect(page.get_by_role("button", name=re.compile("Hint"))).to_have_count(0)
    page.keyboard.press("Tab")
    page.keyboard.press("h")  # was the hint key: nothing happens
    expect(tid(page, "study")).to_have_attribute("data-phase", "answering")

    page.keyboard.press("g")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "incorrect")
    expect(page.get_by_text("What went wrong")).to_have_count(0)
    expect(tid(page, "continue")).to_be_enabled()  # nothing to pick first
    for digit in "12345":
        page.keyboard.press(digit)
    expect(tid(page, "study")).to_have_attribute("data-phase", "review")
    page.keyboard.press("Space")
    expect(tid(page, "progress")).to_contain_text("2 of 6")
    guarded.assert_clean()


def test_a_wrong_try_shows_only_not_quite_retry_and_give_up(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server)
    # A known wrong answer: the card has feedback for it, but none shows during retries.
    type_plain(page, "4x^3-2x")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict-main")).to_have_text("Not quite")
    expect(tid(page, "study")).to_have_attribute("data-retry", "ready")
    buttons = tid(page, "actions").get_by_role("button")
    expect(buttons).to_have_text([re.compile(r"^\s*Retry\b"), re.compile(r"^\s*Give up\b")])
    expect(tid(page, "retry")).to_be_focused()
    expect(tid(page, "study")).not_to_contain_text("second term")
    expect(tid(page, "feedback")).to_have_count(0)
    expect(tid(page, "verdict")).to_have_count(0)  # no solution and no correct answer yet
    expect(tid(page, "correct-answer")).to_have_count(0)
    guarded.assert_clean()


def test_retries_are_unlimited_and_only_the_first_try_counts(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    study(page, server)
    plain = page.locator("input[data-testid=field-main]")
    type_plain(page, "4x^3")
    key.press("Enter")
    for wrong in ("4x^3-2x", "5x^3", "4x^2"):
        expect(tid(page, "verdict-main")).to_have_text("Not quite")
        expect(tid(page, "retry")).to_be_focused()
        key.press("Enter")  # Retry: back in the answer box
        expect(plain).to_be_focused()
        expect(tid(page, "submit")).to_be_visible()
        plain.fill(wrong)
        key.press("Enter")
    expect(tid(page, "verdict-main")).to_have_text("Not quite")
    key.press("Enter")
    plain.fill("4x^3-4x")
    key.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    # Right in the end, but the first try is what counts (and it was a miss).
    expect(tid(page, "first-try-note")).to_have_text(
        "Right on a later try. Only the first try counts."
    )
    expect(tid(page, "too-easy")).to_have_count(0)
    tid(page, "end-session").click()
    expect(tid(page, "summary-correct")).to_have_text("0 of 1")
    guarded.assert_clean()


def test_a_first_try_success_has_no_later_try_note(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    study(page, server)
    type_plain(page, "4x^3-4x")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    expect(tid(page, "first-try-note")).to_have_count(0)
    expect(tid(page, "too-easy")).to_be_visible()
    guarded.assert_clean()


def test_give_up_before_any_answer_shows_the_whole_solution(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server)
    give_up(page)
    expect(tid(page, "compare")).to_contain_text("No answer")
    expect(tid(page, "correct-answer")).to_be_visible()
    review = tid(page, "review")
    expect(review).to_contain_text("Worked solution")
    expect(review.get_by_test_id("steps").locator("li")).to_have_count(3)
    # The card's other method is there too, folded away (its summary owns Space while it has
    # the focus, like any disclosure, so Continue is clicked here).
    alternative = tid(page, "alternative")
    expect(alternative).not_to_have_attribute("open", "")
    alternative.locator("summary").click()
    expect(alternative).to_have_attribute("open", "")
    expect(alternative).to_contain_text("product rule")
    tid(page, "continue").click()
    expect(tid(page, "progress")).to_contain_text("2 of 6")
    guarded.assert_clean()


def test_give_up_after_a_wrong_try_shows_its_feedback_in_the_solution(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server)
    type_plain(page, "4x^3-2x")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict-main")).to_have_text("Not quite")
    expect(tid(page, "study")).not_to_contain_text("second term")
    page.keyboard.press("g")  # the keyboard is on Retry, so G gives up
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "incorrect")
    expect(tid(page, "compare")).to_contain_text("Your answer")
    expect(tid(page, "compare")).not_to_contain_text("No answer")
    expect(tid(page, "feedback")).to_contain_text("The second term differentiates")
    guarded.assert_clean()


# --- the textbook pointer ---------------------------------------------------------------


def test_each_problem_names_its_textbook_section(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    study(page, server)
    line = tid(page, "problem").get_by_test_id("textbook")
    expect(line).to_have_text(re.compile(r"OpenStax Calculus Volume 1 §3\.3$"))
    give_up(page)
    expect(line).to_be_visible()  # still there beside the solution
    page.keyboard.press("Space")
    expect(line).to_have_text(re.compile(r"OpenStax Calculus Volume 1 §4\.5$"))
    guarded.assert_clean()


# --- a closed-book sitting --------------------------------------------------------------


def test_a_sitting_is_closed_book_with_its_block_time_and_cuts_nothing_off(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    page.clock.install()
    study(page, server, "sitting")

    # The warm-up first: ordinary practice, with its textbook line and no banner.
    expect(tid(page, "sitting-banner")).to_have_count(0)
    expect(tid(page, "textbook")).to_be_visible()
    type_plain(page, "3x^2+2")
    key.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    key.press("Space")

    # The sitting: closed book, its place, the skill block's limit; no textbook pointer.
    expect(tid(page, "study")).to_have_attribute("data-role", "sitting")
    banner = tid(page, "sitting-banner")
    expect(banner).to_contain_text("Closed-book sitting")
    expect(banner).to_contain_text("Notes and textbook away")
    expect(tid(page, "sitting-index")).to_have_text("Problem 1 of 4")
    expect(tid(page, "sitting-limit")).to_have_text("8:00")
    expect(tid(page, "sitting-used")).to_have_text(re.compile(r"^0:0\d$"))
    expect(tid(page, "textbook")).to_have_count(0)
    expect(tid(page, "reason-tag")).to_contain_text("Sitting")

    # The block's time runs on screen (the installed clock also runs in real time, so the
    # last digit may move on a little), and a pause is left out.
    page.clock.run_for(65_000)
    expect(tid(page, "sitting-used")).to_have_text(re.compile(r"^1:0[5-9]$"))
    key.press("Escape")
    page.clock.run_for(120_000)
    key.press("Escape")
    expect(tid(page, "sitting-used")).to_have_text(re.compile(r"^1:(0[5-9]|1\d)$"))
    expect(tid(page, "field-main")).to_be_focused()
    type_plain(page, "20x^4-2x")
    key.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    key.press("Space")

    # The block's second problem: its time goes on from where the first left it.
    expect(tid(page, "sitting-index")).to_have_text("Problem 2 of 4")
    expect(tid(page, "sitting-used")).to_have_text(re.compile(r"^1:[0-2]\d$"))
    expect(tid(page, "field-main")).to_be_focused()
    page.clock.run_for(4 * 60_000)
    type_plain(page, "24x^3+3")  # typing, so the "Still working?" note stays away
    page.clock.run_for(4 * 60_000)
    # Past the 8:00 limit: said in words, and the problem stays open for its answer.
    expect(tid(page, "sitting-over")).to_have_text("Over the limit")
    expect(tid(page, "study")).to_have_attribute("data-phase", "answering")
    key.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    key.press("Space")

    # The next skill's block has its own limit and starts from nothing.
    expect(tid(page, "sitting-index")).to_have_text("Problem 3 of 4")
    expect(tid(page, "sitting-limit")).to_have_text("10:00")
    expect(tid(page, "sitting-used")).to_have_text(re.compile(r"^0:0\d$"))
    expect(tid(page, "sitting-over")).to_have_count(0)
    guarded.assert_clean()


# --- the stuck ladder -------------------------------------------------------------------


def test_the_ladder_items_say_why_and_a_set_aside_skill_points_to_the_textbook(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server, "ladder")
    expect(tid(page, "ladder-reason")).to_have_count(0)  # a planned problem
    give_up(page)
    page.keyboard.press("Space")

    # One first-try miss: a smaller problem on the same skill.
    expect(tid(page, "study")).to_have_attribute("data-item", "problem:calc1.2-3.power-single.001")
    expect(tid(page, "ladder-reason")).to_have_text("A smaller step first")
    expect(tid(page, "reason-tag")).to_contain_text("Smaller step")
    give_up(page)
    page.keyboard.press("Space")

    # Two in a row: a problem on a prerequisite, from its own textbook.
    expect(tid(page, "ladder-reason")).to_have_text("A prerequisite first")
    expect(tid(page, "textbook")).to_contain_text("OpenStax College Algebra 2e §1.2")
    give_up(page)
    page.keyboard.press("Space")

    # Three: the skill is set aside for today, with its textbook pointer, on the next item.
    note = tid(page, "turn-note")
    expect(note).to_have_text(
        "Power rule is set aside for today. See OpenStax Calculus Volume 1 §3.3."
    )
    expect(tid(page, "ladder-reason")).to_have_count(0)
    expect(tid(page, "progress")).to_contain_text("4 of 4")
    page.keyboard.type("6")
    expect(note).to_be_visible()  # it stays while the student works

    # Home lists it too.
    page.evaluate("location.hash = '#/home'")
    expect(tid(page, "set-aside")).to_contain_text("Power rule, for the rest of today")
    guarded.assert_clean()


def test_a_first_try_success_keeps_the_planned_problem(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    study(page, server, "ladder")
    type_plain(page, "15x^4-12x^2+7")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "correct")
    page.keyboard.press("Space")
    expect(tid(page, "study")).to_have_attribute("data-item", "problem:calc1.2-3.power-sum.002")
    expect(tid(page, "ladder-reason")).to_have_count(0)
    guarded.assert_clean()
