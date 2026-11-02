"""VerdictPanel: what the student sees beside the correct answer (hand test item 2)."""

from playwright.sync_api import expect

from tests.ui.conftest import Guarded, LocalServer


def test_give_up_after_a_wrong_try_shows_that_try_as_your_answer(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    page.goto(f"{server.origin}/index.html?bridge=mock")
    expect(page.get_by_test_id("start")).to_be_focused()
    key.press("Enter")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    key.type("5x")
    key.press("Enter")
    expect(page.get_by_test_id("verdict-main")).to_contain_text("Not quite")
    key.press("Tab")  # out of the field, so G is a shortcut
    key.press("g")
    expect(page.get_by_test_id("verdict")).to_have_attribute("data-outcome", "incorrect")
    compare = page.get_by_test_id("compare")
    expect(compare).to_contain_text("Your answer")
    expect(compare).not_to_contain_text("No answer")  # the Mac showed "No answer"
    expect(compare.locator(".katex")).to_have_count(2)  # the try and the correct answer
    guarded.assert_clean()
