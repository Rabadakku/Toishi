"""Library: a one-line note on a section whose skill has too few problems (hand test 3)."""

from playwright.sync_api import expect

from tests.ui.conftest import Guarded, LocalServer


def test_library_notes_a_skill_whose_pool_is_too_small(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock")
    page.get_by_role("navigation", name="Main").get_by_test_id("nav-library").click()
    flagged = page.locator(
        '[data-testid=section][data-id="Sample Calculus::Applications::Shape of a graph"]'
    )
    expect(flagged.get_by_test_id("small-pool")).to_have_text(
        "Few problems for Concavity: learned after all of them in a row."
    )
    other = page.locator(
        '[data-testid=section][data-id="Sample Calculus::Derivatives::Power rule"]'
    )
    expect(other.get_by_test_id("small-pool")).to_have_count(0)
    guarded.assert_clean()
