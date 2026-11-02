"""The Skills screen per course (wave 2 section 5), on the mock bridge: one row per skill with
its state and track, its milestones with deadlines and certified marks, its level,
readiness and pace; grouped by section, filterable to behind skills."""

import re

from playwright.sync_api import Locator, Page, expect

from tests.ui.conftest import Guarded, LocalServer


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def skill(page: Page, skill_id: str) -> Locator:
    return page.locator(f'[data-testid=skill][data-id="{skill_id}"]')


def test_skills_are_grouped_by_section_with_state_track_milestones_and_numbers(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    page.locator('[data-testid=course][data-id="Sample Calculus"]').get_by_test_id(
        "course-skills"
    ).click()
    expect(tid(page, "page-skills")).to_be_visible()
    expect(tid(page, "skills-course")).to_contain_text("Sample Calculus on ")
    # Sections in course order.
    expect(tid(page, "skills-section").locator("h2")).to_have_text(
        ["Power rule", "Chain rule", "Shape of a graph"]
    )

    power = skill(page, "calc1.deriv.power-rule")
    expect(power.get_by_test_id("skill-state")).to_have_text("Reviewing")
    expect(power.get_by_test_id("skill-track")).to_have_text("Ahead")
    milestones = power.get_by_test_id("milestone")
    expect(milestones).to_have_count(4)
    expect(milestones.nth(0)).to_have_text(
        re.compile(r"^\s*Homework level, tier 2, by \w{3} \d+, certified$")
    )
    expect(milestones.nth(0)).to_have_attribute("data-certified", "true")
    expect(milestones.nth(1)).to_have_attribute("data-certified", "true")
    expect(milestones.nth(2)).to_contain_text("Target level, tier 4, by ")
    expect(milestones.nth(2)).to_have_attribute("data-certified", "false")
    expect(milestones.nth(3)).to_have_text("Keep, tier 3")
    expect(power.get_by_test_id("skill-level")).to_have_text("Tier 3")
    expect(power.get_by_test_id("skill-readiness")).to_have_text("93%")
    expect(power.get_by_test_id("skill-pace")).to_have_text("At pace")

    chain = skill(page, "calc1.deriv.chain-rule")
    expect(chain.get_by_test_id("skill-track")).to_have_text("Behind")
    expect(chain.get_by_test_id("skill-pace")).to_have_text("Slower than the standard time")

    later = skill(page, "calc1.deriv.implicit")
    expect(later.get_by_test_id("skill-state")).to_have_text("Not started")
    expect(later).to_contain_text("Starts ")
    expect(later.get_by_test_id("skill-level")).to_have_text("None yet")
    expect(later.get_by_test_id("skill-readiness")).to_have_text("Not yet")
    expect(later.get_by_test_id("skill-pace")).to_have_text("No timed first try yet")

    expect(skill(page, "calc1.shape.concavity").get_by_test_id("skill-state")).to_have_text(
        "Careless errors"
    )
    expect(page.locator("main")).not_to_contain_text(re.compile("master", re.IGNORECASE))
    guarded.assert_clean()


def test_the_filter_shows_only_behind_skills(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/skills")
    expect(tid(page, "skill")).to_have_count(6)
    toggle = tid(page, "filter-behind")
    expect(toggle).to_have_text("Only behind (2)")
    expect(toggle).to_have_attribute("aria-pressed", "false")
    toggle.click()
    expect(toggle).to_have_attribute("aria-pressed", "true")
    expect(tid(page, "skill")).to_have_count(2)
    expect(page.locator("[data-testid=skill]:not([data-track=behind])")).to_have_count(0)
    # A section with no behind skill drops out.
    expect(tid(page, "skills-section").locator("h2")).to_have_text(
        ["Chain rule", "Shape of a graph"]
    )
    toggle.click()
    expect(tid(page, "skill")).to_have_count(6)
    guarded.assert_clean()


def test_another_course_is_one_pick_away(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/skills?course=Sample%20Calculus")
    expect(tid(page, "skill")).to_have_count(6)
    tid(page, "skills-course-pick").select_option(label="Sample Statistics")
    expect(tid(page, "skills-course")).to_contain_text("Sample Statistics")
    expect(tid(page, "skill")).to_have_count(1)
    expect(tid(page, "skill")).to_contain_text("Mean and median")
    # No schedule without pace data: milestones have no deadlines.
    expect(tid(page, "milestone").first).to_have_text("Homework level, tier 2")
    guarded.assert_clean()


def test_a_skill_set_aside_today_is_marked(server: LocalServer, guarded: Guarded) -> None:
    # Three first-try misses on the power rule (the ladder scenario) set it aside for today.
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock&scenario=ladder#/study")
    for _ in range(3):
        expect(tid(page, "field-main")).to_be_focused()
        page.keyboard.press("Tab")
        page.keyboard.press("g")
        expect(tid(page, "continue")).to_be_enabled()
        page.keyboard.press("Space")
    expect(tid(page, "turn-note")).to_contain_text("set aside")
    page.evaluate("location.hash = '#/skills'")
    expect(skill(page, "calc1.deriv.power-rule").get_by_test_id("skill-set-aside")).to_have_text(
        "Set aside today"
    )
    expect(skill(page, "calc1.deriv.chain-rule").get_by_test_id("skill-set-aside")).to_have_count(0)
    guarded.assert_clean()
