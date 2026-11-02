"""Themes, text size, motion, the sidebar shell and focus mode, all offline."""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.ui.conftest import Guarded, LocalServer

DAY_BACKGROUND = "rgb(246, 244, 239)"  # #F6F4EF
NIGHT_BACKGROUND = "rgb(23, 25, 28)"  # #17191C
DAY_SURFACE = "rgb(252, 251, 248)"
NIGHT_SURFACE = "rgb(31, 34, 38)"
ROUTES = ["home", "study", "library", "browse", "stats", "settings"]


def css(page: Page, selector: str, prop: str) -> str:
    value = page.locator(selector).first.evaluate("(el, p) => getComputedStyle(el)[p]", prop)
    assert isinstance(value, str)
    return value


def px(value: str) -> float:
    assert value.endswith("px"), value
    return float(value.removesuffix("px"))


def seconds(value: str) -> list[float]:
    """A computed transition-duration list such as '0.12s, 0.12s' as numbers of seconds."""
    parts = [part.strip() for part in value.split(",")]
    return [
        float(p.removesuffix("ms")) / 1000 if p.endswith("ms") else float(p.removesuffix("s"))
        for p in parts
    ]


def choose_theme(page: Page, label: str) -> None:
    page.locator("label.theme", has_text=label).click()


def test_automatic_follows_the_system_and_explicit_choices_override_it(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.emulate_media(color_scheme="light")
    page.goto(f"{server.origin}/index.html?bridge=mock#/settings")
    expect(page.get_by_test_id("theme-auto")).to_be_checked()
    assert page.evaluate("document.documentElement.hasAttribute('data-theme')") is False
    assert css(page, "body", "backgroundColor") == DAY_BACKGROUND

    # Automatic: the OS switches, the page follows with no reload.
    page.emulate_media(color_scheme="dark")
    assert css(page, "body", "backgroundColor") == NIGHT_BACKGROUND
    page.emulate_media(color_scheme="light")
    assert css(page, "body", "backgroundColor") == DAY_BACKGROUND

    # Explicit Night wins over a light system, and explicit Day over a dark one.
    choose_theme(page, "Night")
    expect(page.locator("html")).to_have_attribute("data-theme", "night")
    assert css(page, "body", "backgroundColor") == NIGHT_BACKGROUND
    assert css(page, "body", "color") == "rgb(228, 225, 218)"  # #E4E1DA, not white
    page.emulate_media(color_scheme="dark")
    choose_theme(page, "Day")
    expect(page.locator("html")).to_have_attribute("data-theme", "day")
    assert css(page, "body", "backgroundColor") == DAY_BACKGROUND
    assert css(page, "body", "color") == "rgb(30, 34, 38)"  # #1E2226, not black

    # Back to Automatic: the attribute goes away and the dark system wins again.
    choose_theme(page, "Automatic")
    assert page.evaluate("document.documentElement.hasAttribute('data-theme')") is False
    assert css(page, "body", "backgroundColor") == NIGHT_BACKGROUND
    guarded.assert_clean()


def test_theme_reaches_the_study_screen_and_the_answer_box(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.emulate_media(color_scheme="light")
    page.goto(f"{server.origin}/index.html?bridge=mock#/settings")
    choose_theme(page, "Night")
    page.evaluate("location.hash = '#/study'")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    assert css(page, "[data-testid=problem]", "color") == "rgb(228, 225, 218)"
    assert (
        css(page, "[data-testid=submit]", "backgroundColor") == "rgb(127, 168, 219)"
    )  # night accent
    page.evaluate("location.hash = '#/settings'")
    choose_theme(page, "Day")
    page.evaluate("location.hash = '#/study'")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    assert css(page, "[data-testid=submit]", "backgroundColor") == "rgb(47, 109, 176)"  # day accent
    assert css(page, "body", "backgroundColor") == DAY_BACKGROUND
    assert css(page, "[data-testid=study-content] .card", "backgroundColor") == DAY_SURFACE
    guarded.assert_clean()


def test_problem_typography_and_text_size_scaling(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(page.get_by_test_id("field-main")).to_be_focused()

    # Source Serif 4 at 18 px / 1.6 for problem text, Inter for the interface, math at 1.05x.
    problem = "[data-testid=problem]"
    assert css(page, problem, "fontSize") == "18px"
    assert px(css(page, problem, "lineHeight")) == pytest.approx(28.8)
    assert "Source Serif 4 Variable" in css(page, problem, "fontFamily")
    assert "Inter Variable" in css(page, "[data-testid=submit]", "fontFamily")
    assert px(css(page, f"{problem} .katex", "fontSize")) == pytest.approx(18 * 1.05)

    # Text size runs 14 to 28 px; the interface and the math scale with it.
    page.evaluate("location.hash = '#/settings'")
    slider = page.get_by_test_id("text-size")
    assert (slider.get_attribute("min"), slider.get_attribute("max")) == ("14", "28")
    sample = "[data-testid=text-sample]"
    for size in (28, 14, 18):
        slider.fill(str(size))
        expect(page.get_by_test_id("text-size-value")).to_have_text(f"{size} px")
        assert px(css(page, f"{sample} p", "fontSize")) == pytest.approx(size)
        assert px(css(page, f"{sample} .katex", "fontSize")) == pytest.approx(size * 1.05)
        assert px(css(page, "html", "fontSize")) == pytest.approx(size / 18 * 16, abs=1e-3)
    slider.focus()  # the keyboard reaches both ends of the range
    page.keyboard.press("End")
    expect(page.get_by_test_id("text-size-value")).to_have_text("28 px")
    page.keyboard.press("Home")
    expect(page.get_by_test_id("text-size-value")).to_have_text("14 px")
    page.keyboard.press("ArrowRight")
    expect(page.get_by_test_id("text-size-value")).to_have_text("15 px")
    guarded.assert_clean()


def test_motion_is_short_and_reduce_motion_is_respected(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.emulate_media(reduced_motion="no-preference")
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    durations = seconds(css(page, "[data-testid=submit]", "transitionDuration"))
    assert 0 < max(durations) <= 0.15  # fades of 150 ms or less

    page.emulate_media(reduced_motion="reduce")
    for selector in (
        "[data-testid=submit]",
        "[data-testid=study-content]",
        "[data-testid=pause-button]",
    ):
        assert max(seconds(css(page, selector, "transitionDuration"))) < 0.001, selector
    assert css(page, "html", "scrollBehavior") == "auto"


def test_focus_rings_are_visible_on_keyboard_focus(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    page.keyboard.press("Tab")
    toggle = page.get_by_test_id("mode-main")
    expect(toggle).to_be_focused()
    assert css(page, "[data-testid=mode-main]", "outlineStyle") == "solid"
    assert px(css(page, "[data-testid=mode-main]", "outlineWidth")) >= 2
    assert css(page, "[data-testid=mode-main]", "outlineColor") == "rgb(47, 109, 176)"
    # The math field shows a ring while it has focus.
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    assert css(page, "[data-testid=field-main]", "outlineStyle") == "solid"


def test_sidebar_routes_placeholders_and_focus_mode(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock")
    nav = page.get_by_role("navigation", name="Main")
    links = nav.get_by_role("link")
    assert links.all_inner_texts() == ["Home", "Study", "Library", "Browse", "Stats", "Settings"]
    expect(nav.get_by_test_id("nav-home")).to_have_attribute("aria-current", "page")

    nav.get_by_test_id("nav-library").click()
    expect(page.get_by_test_id("page-library")).to_contain_text("Sample Calculus")
    for route in ("browse", "stats"):
        nav.get_by_test_id(f"nav-{route}").click()
        expect(page.get_by_test_id(f"page-{route}")).to_contain_text("Not built yet")
        expect(nav.get_by_test_id(f"nav-{route}")).to_have_attribute("aria-current", "page")
    nav.get_by_test_id("nav-settings").click()
    expect(page.get_by_test_id("page-settings")).to_be_visible()

    # Focus mode: Study fills the window with no sidebar; the toggle (or F) brings it back.
    nav.get_by_test_id("nav-study").click()
    expect(page.get_by_test_id("progress")).to_contain_text("1 of 6")
    expect(nav).to_have_count(0)
    page.get_by_test_id("focus-toggle").click()
    expect(page.get_by_role("navigation", name="Main")).to_be_visible()
    expect(page.get_by_test_id("focus-toggle")).to_have_attribute("aria-pressed", "false")
    page.get_by_test_id("focus-toggle").click()
    expect(page.get_by_role("navigation", name="Main")).to_have_count(0)
    guarded.assert_clean()


def test_every_screen_works_offline_and_nothing_leaves_loopback(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock&selftest=1")
    for route in ROUTES:
        page.evaluate(f"location.hash = '#/{route}'")
        expect(page.locator("main")).not_to_be_empty()
    page.evaluate("location.hash = '#/study'")
    expect(page.get_by_test_id("field-main")).to_be_focused()
    # Fonts, KaTeX, MathLive, the figure: everything came from this one origin.
    assert guarded.outbound == []
    foreign = [
        url
        for url in guarded.requests
        if not url.startswith(server.origin) and not url.startswith(("data:", "blob:", "about:"))
    ]
    assert foreign == []
    assert re.search(r"/assets/inter-latin-wght", " ".join(guarded.requests))
    guarded.assert_clean()
