"""The student model page, in Settings (wave 2 section 5), on the mock bridge: the current
parameters read-only with their source and date; Refit now with its report (held-out log
loss before and after per block, the p value, kept or not); Reset with a confirmation; the
calibration tables by tier, gap and component count. Plain words, numbers alongside."""

import re

from playwright.sync_api import Locator, Page, expect

from tests.ui.conftest import Guarded, LocalServer


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def param(page: Page, key: str) -> Locator:
    return page.locator(f'[data-testid=param][data-key="{key}"]')


def open_model(page: Page, server: LocalServer) -> None:
    page.goto(f"{server.origin}/index.html?bridge=mock#/settings")
    tid(page, "open-model").click()
    expect(tid(page, "page-model")).to_be_visible()


def test_the_model_page_shows_values_refits_and_calibration(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    open_model(page, server)
    nav = page.get_by_role("navigation", name="Main")
    expect(nav.get_by_test_id("nav-settings")).to_have_attribute("aria-current", "page")

    # The starting values, read-only, in plain words with the numbers alongside.
    source = tid(page, "model-source")
    expect(source).to_have_attribute("data-source", "prior")
    expect(source).to_contain_text("The starting values, taken from research")
    expect(source).to_contain_text("212 first tries")
    expect(param(page, "slip")).to_contain_text("Careless-slip rate")
    expect(param(page, "slip")).to_contain_text("0.02 (a 2% chance of a slip")
    expect(param(page, "tau")).to_contain_text("about 2 times the standard time")
    expect(param(page, "calib_a")).to_contain_text("0, 0, 0, 0, 0")
    expect(param(page, "fsrs_weights")).to_contain_text("The FSRS-6 defaults")
    expect(tid(page, "params").locator("input, select, textarea")).to_have_count(0)
    expect(tid(page, "no-refit")).to_be_visible()

    # Calibration by tier, by gap and by number of skills; an empty group shows a dash.
    expect(tid(page, "calibration-tier").get_by_test_id("bin")).to_have_count(5)
    expect(tid(page, "calibration-gap").get_by_test_id("bin")).to_have_count(5)
    expect(tid(page, "calibration-components").get_by_test_id("bin")).to_have_count(3)
    expect(tid(page, "calibration-tier").get_by_test_id("bin").nth(0)).to_have_text(
        re.compile(r"Tier 1\s*48\s*92%\s*94%")
    )
    empty = tid(page, "calibration-tier").get_by_test_id("bin").nth(4)
    expect(empty).to_contain_text("\N{EN DASH}")

    # Refit now: the report, block by block, and the new values in use.
    tid(page, "refit").click()
    report = tid(page, "refit-report")
    expect(report).to_have_attribute("data-adopted", "true")
    expect(tid(page, "refit-outcome")).to_have_text("Kept the new values.")
    expect(report).to_contain_text("from 212 first tries; p = 0.03")
    accuracy = report.locator('[data-testid=refit-block][data-name="accuracy"]')
    expect(accuracy).to_have_text(
        re.compile(r"Accuracy predictions\s*0\.512\s*0\.497\s*0\.03\s*New values kept")
    )
    time = report.locator('[data-testid=refit-block][data-name="time"]')
    expect(time).to_have_text(
        re.compile(r"Time predictions\s*0\.94\s*0\.951\s*0\.62\s*Current values kept")
    )
    expect(source).to_have_attribute("data-source", "refit")
    expect(source).to_contain_text("Fitted to your practice on ")
    expect(param(page, "slip")).to_contain_text("0.031")
    expect(tid(page, "model-status")).to_contain_text("the new values are in use")

    # Again, with nothing clearly better: the current values stay.
    tid(page, "refit").click()
    expect(tid(page, "refit-outcome")).to_have_text("Kept the current values.")
    expect(tid(page, "model-status")).to_contain_text("the current values stay")
    expect(param(page, "slip")).to_contain_text("0.031")
    expect(page.locator("main")).not_to_contain_text(re.compile("master", re.IGNORECASE))
    guarded.assert_clean()


def test_reset_asks_first_and_cancel_changes_nothing(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    open_model(page, server)
    tid(page, "refit").click()
    source = tid(page, "model-source")
    expect(source).to_have_attribute("data-source", "refit")

    tid(page, "reset").click()
    confirm = tid(page, "reset-confirmation")
    expect(confirm).to_contain_text("Reset the model to its starting values?")
    expect(confirm).to_contain_text("Your practice history stays")
    expect(tid(page, "reset-cancel")).to_be_focused()  # the safe choice has the keyboard
    page.keyboard.press("Enter")
    expect(confirm).to_have_count(0)
    expect(tid(page, "reset")).to_be_focused()
    expect(source).to_have_attribute("data-source", "refit")

    tid(page, "reset").click()
    tid(page, "reset-confirm").click()
    expect(source).to_have_attribute("data-source", "reset")
    expect(source).to_contain_text("Reset to the starting values on ")
    expect(param(page, "slip")).not_to_contain_text("0.031")
    expect(param(page, "slip")).to_contain_text("0.02")
    expect(tid(page, "model-status")).to_have_text(
        "Reset: the model uses its starting values again."
    )
    guarded.assert_clean()


def test_back_to_settings(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    open_model(page, server)
    tid(page, "back-settings").click()
    expect(tid(page, "page-settings")).to_be_visible()
    guarded.assert_clean()
