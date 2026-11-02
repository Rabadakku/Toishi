"""Course setup, from the Library (wave 2 section 5), on the mock bridge: the start date or
"my class is at section X today", the end date, exams, the accuracy target, the target tier,
standard or hard practice, the pace factor, and "no pace data" for a pack without it."""

import re

from playwright.sync_api import Locator, Page, expect

from tests.ui.conftest import Guarded, LocalServer

CALCULUS = "Sample Calculus"
TIMES = "\N{MULTIPLICATION SIGN}"  # the pace factor reads "1.25" and this sign


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def choose(page: Page, testid: str) -> None:
    """Pick one of the setup's option cards (the radio inside is visually hidden)."""
    page.locator("label.option").filter(has=tid(page, testid)).click()
    expect(tid(page, testid)).to_be_checked()


def open_setup(page: Page, course: str = CALCULUS) -> None:
    page.locator(f'[data-testid=course][data-id="{course}"]').get_by_test_id("course-setup").click()
    expect(tid(page, "page-course")).to_be_visible()
    expect(tid(page, "course-title")).to_have_text(course)


def test_course_setup_opens_from_the_library_and_keeps_what_is_saved(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    open_setup(page)
    nav = page.get_by_role("navigation", name="Main")
    expect(nav.get_by_test_id("nav-library")).to_have_attribute("aria-current", "page")

    # As loaded: a start date, the standard pace, 90% at tier 4, standard practice.
    expect(tid(page, "schedule-date")).to_be_checked()
    expect(tid(page, "start")).to_have_value(re.compile(r"^\d{4}-\d{2}-\d{2}$"))
    expect(tid(page, "pace-value")).to_have_text(f"1.00{TIMES}")
    expect(tid(page, "accuracy-value")).to_have_text("90%")
    expect(tid(page, "tier-4")).to_be_checked()
    expect(tid(page, "band-standard")).to_be_checked()

    tid(page, "accuracy").fill("85")
    expect(tid(page, "accuracy-value")).to_have_text("85%")
    choose(page, "tier-5")
    choose(page, "band-hard")
    tid(page, "pace").fill("1.25")
    expect(tid(page, "pace-value")).to_have_text(f"1.25{TIMES}")
    tid(page, "save-course").click()
    expect(tid(page, "course-status")).to_have_text("Saved.")

    # Out to the Library and back in: the values were kept.
    tid(page, "back-library").click()
    open_setup(page)
    expect(tid(page, "accuracy-value")).to_have_text("85%")
    expect(tid(page, "tier-5")).to_be_checked()
    expect(tid(page, "band-hard")).to_be_checked()
    expect(tid(page, "pace-value")).to_have_text(f"1.25{TIMES}")
    expect(tid(page, "page-course")).not_to_contain_text(re.compile("master", re.IGNORECASE))
    guarded.assert_clean()


def test_my_class_is_at_a_section_today(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    open_setup(page)
    choose(page, "schedule-aligned")
    expect(tid(page, "start")).to_have_count(0)
    tid(page, "aligned").select_option(label="Chain rule")
    tid(page, "save-course").click()
    expect(tid(page, "course-status")).to_have_text("Saved.")

    tid(page, "back-library").click()
    open_setup(page)
    expect(tid(page, "schedule-aligned")).to_be_checked()
    expect(tid(page, "aligned")).to_have_value("Sample Calculus::Derivatives::Chain rule")
    expect(tid(page, "aligned-day")).to_have_count(0)  # said today, so no older date to show
    guarded.assert_clean()


def test_setup_problems_are_explained_before_saving(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    open_setup(page)
    tid(page, "start").fill("")
    tid(page, "save-course").click()
    expect(tid(page, "course-error")).to_contain_text("Choose the day of the first class")

    tid(page, "start").fill("2026-09-01")
    tid(page, "end").fill("2026-08-01")
    tid(page, "save-course").click()
    expect(tid(page, "course-error")).to_contain_text("ends before it starts")
    expect(tid(page, "course-status")).to_have_count(0)

    choose(page, "schedule-aligned")
    tid(page, "save-course").click()
    expect(tid(page, "course-error")).to_contain_text("Choose the section your class is at")
    guarded.assert_clean()


def test_exams_are_added_edited_and_deleted(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    open_setup(page)
    exams = tid(page, "exam")
    expect(exams).to_have_count(1)
    expect(exams.first).to_contain_text("Midterm")
    expect(exams.first).to_contain_text("on Power rule and Chain rule. 50 minutes, 10 problems")

    tid(page, "add-exam").click()
    tid(page, "exam-name").fill("Final")
    tid(page, "save-exam").click()
    expect(tid(page, "exam-error")).to_have_text("Choose the day of the exam.")
    tid(page, "exam-day").fill("2026-12-14")
    tid(page, "save-exam").click()
    expect(tid(page, "exam-error")).to_have_text("Choose at least one section the exam covers.")
    page.locator('[data-testid=exam-section][data-deck$="Shape of a graph"]').check()
    page.locator('[data-testid=exam-section][data-deck$="Power rule"]').check()
    tid(page, "exam-minutes").fill("120")
    tid(page, "save-exam").click()

    expect(exams).to_have_count(2)
    final = exams.filter(has_text="Final")
    expect(final).to_contain_text("Dec 14")
    # The sections in course order, whatever order they were ticked in.
    expect(final).to_contain_text("on Power rule and Shape of a graph. 120 minutes")

    final.get_by_test_id("edit-exam").click()
    expect(tid(page, "exam-name")).to_have_value("Final")
    expect(page.locator('[data-testid=exam-section][data-deck$="Power rule"]')).to_be_checked()
    tid(page, "exam-name").fill("Final exam")
    tid(page, "save-exam").click()
    expect(exams.filter(has_text="Final exam")).to_have_count(1)

    exams.filter(has_text="Final exam").get_by_test_id("delete-exam").click()
    expect(exams).to_have_count(1)
    expect(tid(page, "course-status")).to_have_text("Final exam deleted.")
    guarded.assert_clean()


def test_a_course_without_pace_data_says_so(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/library")
    open_setup(page, "Sample Statistics")
    expect(tid(page, "no-pace")).to_contain_text("No pace data")
    # Nothing can be dated, so no schedule or pace to set; targets and exams still apply.
    expect(tid(page, "schedule-date")).to_have_count(0)
    expect(tid(page, "pace")).to_have_count(0)
    expect(tid(page, "accuracy")).to_be_visible()
    expect(tid(page, "no-exams")).to_be_visible()
    tid(page, "save-course").click()
    expect(tid(page, "course-status")).to_have_text("Saved.")
    guarded.assert_clean()
