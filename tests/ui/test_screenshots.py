"""Regenerates web/screenshots/*.png. Skipped unless TOISHI_SCREENSHOTS=1.

    TOISHI_SCREENSHOTS=1 TOISHI_BROWSER=chromium uv run pytest tests/ui/test_screenshots.py

The study screen at 1280x800 on the mock bridge, in Day and Night: a typed math answer, a
multi-part card, the step-tagged review of a find-the-error problem, and the pause overlay.
"""

import os
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import Browser, expect

from tests.ui.conftest import LocalServer

OUT = Path(__file__).parents[2] / "web" / "screenshots"
SCHEMES: dict[str, Literal["light", "dark"]] = {"day": "light", "night": "dark"}

pytestmark = pytest.mark.skipif(
    os.environ.get("TOISHI_SCREENSHOTS") != "1", reason="set TOISHI_SCREENSHOTS=1 to regenerate"
)


@pytest.mark.parametrize("theme", SCHEMES)
def test_study_screen_screenshots(browser: Browser, server: LocalServer, theme: str) -> None:
    OUT.mkdir(exist_ok=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800}, color_scheme=SCHEMES[theme]
    )
    page = context.new_page()
    key = page.keyboard
    page.goto(f"{server.origin}/index.html?bridge=mock")
    key.press("Enter")  # Home: Start
    expect(page.get_by_test_id("field-main")).to_be_focused()
    key.type("4x^3")
    key.press("ArrowRight")
    key.type("-4x")
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / f"{theme}-study.png")

    key.press("Enter")
    expect(page.get_by_test_id("verdict")).to_be_visible()
    key.press("Space")  # problem 2: multi-part
    expect(page.get_by_test_id("part-a")).to_be_visible()
    answers = ["(-inf, 0) U (2, inf)", "(0, 0)", "(2, -4)"]
    for index, answer in enumerate(answers):
        key.press("`")  # plain-text entry for this part
        key.type(answer)
        if index < len(answers) - 1:
            for _ in range(3):  # the toggle, the helpers, then the next part
                key.press("Tab")
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / f"{theme}-multipart.png")

    key.press("Enter")
    expect(page.get_by_test_id("verdict")).to_be_visible()
    key.press("Space")  # problem 3: find the error
    expect(page.get_by_test_id("find-error")).to_be_visible()
    key.press("2")  # pick the step, then the reason
    key.press("2")
    key.press("`")
    key.type("6x(x^2+1)^2")
    key.press("Enter")
    expect(page.get_by_test_id("verdict")).to_be_visible()
    page.screenshot(path=OUT / f"{theme}-find-the-error.png", full_page=True)

    key.press("Space")  # problem 4: which method
    expect(page.get_by_test_id("choices")).to_be_visible()
    key.press("Escape")  # pause
    expect(page.get_by_test_id("pause-overlay")).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / f"{theme}-paused.png")
    context.close()
