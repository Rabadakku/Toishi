"""Home (Today) with the planner, on the mock bridge (wave 2 section 5): the day's minutes and
items by role, the hours that keep pace and where that figure comes from, behind skills,
sittings planned today, set-aside skills and the planner's notes. No Lighter set."""

import re

import pytest
from playwright.sync_api import Locator, Page, expect

from tests.ui.conftest import Guarded, LocalServer


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def test_home_shows_the_days_minutes_roles_pace_behind_and_notes(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock")
    expect(tid(page, "today-plan")).to_contain_text("6 problems, about 14 minutes")
    expect(tid(page, "by-role").locator("li")).to_have_text(
        ["1 New", "1 Building", "3 Review", "1 Check"]
    )
    expect(tid(page, "pace-hours")).to_have_text("About 6.5 hours a week keeps you on pace.")
    expect(tid(page, "behind")).to_contain_text("Chain rule and Concavity.")
    expect(tid(page, "note")).to_have_text(
        "Concavity: careless errors are holding it back. Check your work before you submit."
    )
    expect(tid(page, "set-aside")).to_have_count(0)
    expect(tid(page, "sitting-today")).to_have_count(0)
    # The old engine's Lighter set and proposals are gone; Start still has the keyboard.
    expect(page.get_by_role("button", name=re.compile("Lighter"))).to_have_count(0)
    expect(tid(page, "proposal")).to_have_count(0)
    expect(tid(page, "start")).to_be_focused()
    expect(tid(page, "page-home")).not_to_contain_text(re.compile("master", re.IGNORECASE))
    guarded.assert_clean()


@pytest.mark.parametrize(
    ("hours", "line", "basis"),
    [
        ("history", "About 8 hours a week keeps you on pace.", "your own practice so far"),
        ("standard", "About 6.5 hours a week keeps you on pace.", "This is the course standard"),
        ("none", "No pace figure yet.", "no pace data"),
    ],
)
def test_the_pace_line_says_where_its_figure_comes_from(
    server: LocalServer, guarded: Guarded, hours: str, line: str, basis: str
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock&hours={hours}")
    expect(tid(page, "pace")).to_have_attribute("data-basis", hours)
    expect(tid(page, "pace-hours")).to_have_text(line)
    expect(tid(page, "pace-basis")).to_contain_text(basis)
    if hours == "history":
        expect(tid(page, "pace-basis")).to_contain_text("The course standard is 6.5 hours.")
    guarded.assert_clean()


def test_home_lists_a_sitting_planned_today(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock&scenario=sitting")
    expect(tid(page, "sitting-today")).to_contain_text(
        "A closed-book, timed sitting on Power rule and Chain rule"
    )
    expect(tid(page, "by-role").locator("li")).to_have_text(["1 Building", "4 Sitting"])
    guarded.assert_clean()


def test_behind_opens_the_skills_page_with_only_behind_skills(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock")
    tid(page, "behind-skills").click()
    expect(tid(page, "page-skills")).to_be_visible()
    expect(tid(page, "filter-behind")).to_have_attribute("aria-pressed", "true")
    expect(tid(page, "skill")).to_have_count(2)
    expect(page.locator("[data-testid=skill][data-track=behind]")).to_have_count(2)
    guarded.assert_clean()
