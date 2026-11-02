"""The study screen driven like a student: keyboard only, pause, idle note, safe Markdown.

Wave 2 learning design: no hints and no "What went wrong?" picker. A wrong try is "Not
quite" with Retry and Give up; Give up shows the solution (tests/ui/test_learning_design.py
covers the retry, give-up, sitting and ladder flows in detail).
"""

import re
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Locator, Page, expect

from app.shell import WindowSpec
from tests.ui.conftest import Guarded, LocalServer

# The window the app opens (app/shell.py), so layout is tested at the size students see.
WINDOW = WindowSpec(title="t", entry=Path("index.html"))

# Counts every pointer interaction, so "keyboard alone" is checked, not assumed.
POINTER_COUNTER = """
window.__pointerEvents = 0;
for (const type of ['pointerdown', 'mousedown'])
  document.addEventListener(type, () => { window.__pointerEvents += 1; }, true);
"""

TIME_NOTE = re.compile(r"^\d+:\d\d · target \d+:\d\d$")


def tid(page: Page, name: str) -> Locator:
    return page.get_by_test_id(name)


def verdict_outcome(page: Page) -> Locator:
    return tid(page, "verdict")


def type_plain(page: Page, part: str, text: str) -> None:
    """Switch the focused part to plain-text mode with the backtick key and type."""
    page.keyboard.press("`")
    plain = page.locator(f"input[data-testid=field-{part}]")
    expect(plain).to_be_focused()
    page.keyboard.type(text)
    expect(plain).to_have_value(text)


def test_mock_session_completed_by_keyboard_alone(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.context.add_init_script(POINTER_COUNTER)
    key = page.keyboard
    page.goto(f"{server.origin}/index.html?bridge=mock")

    # Home: Start has focus, so Enter begins the session. Focus mode hides the sidebar.
    expect(tid(page, "today-plan")).to_contain_text("6 problems")
    expect(tid(page, "start")).to_be_focused()
    key.press("Enter")
    expect(tid(page, "progress")).to_contain_text("1 of 6")
    expect(page.get_by_role("navigation", name="Main")).to_have_count(0)
    # No clock on screen while working, and no time anywhere before submitting.
    expect(tid(page, "study")).not_to_contain_text("target")

    # 1. Single answer, typed into MathLive. ^ opens an exponent; ArrowRight leaves it.
    expect(tid(page, "field-main")).to_be_focused()
    key.type("4x^3")
    key.press("ArrowRight")
    key.type("-4x")
    expect(tid(page, "preview-main")).to_contain_text("We read your answer as")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    expect(tid(page, "time-note")).to_have_text(TIME_NOTE)
    expect(tid(page, "skill-name")).to_have_text("Power rule")
    key.press("Space")

    # 2. Multi-part: one box and verdict per part; Shift+Enter submits "unsure".
    expect(tid(page, "progress")).to_contain_text("2 of 6")
    answers = [("a", "(-inf, 0) U (2, inf)"), ("b", "(0, 0)"), ("c", "(2, -4)")]
    for part, text in answers:
        expect(tid(page, f"field-{part}")).to_be_focused()
        type_plain(page, part, text)
        if part != "c":
            # Tab to the next box. Chromium stops on the mode toggle and the shape helpers
            # first; WebKit on macOS, by default, tabs only between text fields.
            next_part = chr(ord(part) + 1)
            for _ in range(4):
                key.press("Tab")
                if tid(page, f"field-{next_part}").evaluate("e => e === document.activeElement"):
                    break
    expect(tid(page, "preview-a")).to_contain_text("We read your answer as")
    key.press("Shift+Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    expect(tid(page, "part-verdict-b")).to_contain_text("Correct")
    key.press("Space")

    # 3. A worked example: read it, Space continues.
    expect(tid(page, "progress")).to_have_text("Worked example")
    expect(tid(page, "example")).to_contain_text("Worked example")
    key.press("Space")

    # 4. Find the error: digits pick the step and the reason, then type the corrected value.
    expect(tid(page, "find-error")).to_be_visible()
    expect(tid(page, "field-main")).to_have_count(0)
    key.press("2")
    expect(tid(page, "step-2")).to_have_attribute("aria-pressed", "true")
    key.press("2")
    expect(tid(page, "reason-2")).to_have_attribute("aria-checked", "true")
    expect(tid(page, "field-main")).to_be_focused()
    type_plain(page, "main", "6x(x^2+1)^2")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    expect(tid(page, "find-error-outcome")).to_contain_text("Wrong step found")
    expect(tid(page, "find-error-outcome")).to_contain_text("Reason right")
    expect(tid(page, "side-by-side")).to_contain_text("Their work")
    expect(tid(page, "what-went-wrong")).to_have_count(0)
    key.press("Space")

    # 5. Which method: the digit chooses, Enter submits, E marks it too easy.
    expect(tid(page, "choices")).to_be_visible()
    key.press("4")
    expect(tid(page, "choice-4")).to_have_attribute("aria-checked", "true")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    key.press("e")
    expect(tid(page, "flag-message")).to_contain_text("too easy")
    key.press("Space")

    # 6. A flashcard: Space shows the back, 3 rates it Good and moves on.
    expect(tid(page, "progress")).to_have_text("Flashcard")
    expect(tid(page, "flashcard-back")).to_have_count(0)
    key.press("Space")
    expect(tid(page, "flashcard-back")).to_be_visible()
    key.press("3")

    # 7. Calculator mark; no hints: H out of the answer box does nothing.
    expect(tid(page, "calculator-mark")).to_be_visible()
    expect(tid(page, "degrees-note")).to_have_count(0)
    expect(tid(page, "field-main")).to_be_focused()
    key.press("Tab")  # out of the field, onto the mode toggle
    key.press("h")
    expect(tid(page, "study")).to_have_attribute("data-phase", "answering")
    expect(tid(page, "study")).not_to_contain_text("Hint")
    key.press("Shift+Tab")
    expect(tid(page, "field-main")).to_be_focused()
    key.type("2.4")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    key.press("Space")

    # 8. Degrees note; G gives up: the solution at once, Continue ready. U undoes. A known
    #    wrong answer is only "Not quite" (Enter retries) until the solution shows its feedback.
    expect(tid(page, "degrees-note")).to_be_visible()
    expect(tid(page, "field-main")).to_be_focused()
    key.press("Tab")
    key.press("g")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "incorrect")
    expect(tid(page, "continue")).to_be_enabled()
    expect(tid(page, "progress")).to_contain_text("6 of 6")
    key.press("u")
    expect(tid(page, "verdict")).to_have_count(0)
    expect(tid(page, "turn-note")).to_contain_text("Undone")
    expect(tid(page, "field-main")).to_be_focused()
    type_plain(page, "main", "4.60")
    key.press("Enter")
    expect(tid(page, "verdict-main")).to_have_attribute("data-kind", "incorrect")
    expect(tid(page, "verdict-main")).to_have_text("Not quite")
    expect(tid(page, "study")).not_to_contain_text("cosine")  # no feedback during retries
    expect(tid(page, "retry")).to_be_focused()
    key.press("Enter")  # Retry: the keyboard is back in the answer box
    expect(page.locator("input[data-testid=field-main]")).to_be_focused()
    key.press("Enter")  # the same answer again: still "Not quite", as often as it takes
    expect(tid(page, "retry")).to_be_focused()
    key.press("g")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "incorrect")
    expect(tid(page, "compare")).to_contain_text("Your answer")
    expect(tid(page, "compare")).to_contain_text("Correct answer")
    expect(tid(page, "feedback")).to_contain_text("cosine")
    key.press("d")
    expect(tid(page, "flag-message")).to_contain_text("will not count")
    expect(tid(page, "continue")).to_be_enabled()
    key.press("Space")

    # The session summary, then back Home, still without the pointer.
    expect(tid(page, "summary")).to_be_visible()
    expect(tid(page, "summary-correct")).to_have_text("5 of 6")
    expect(tid(page, "summary-misses")).to_contain_text("Right-triangle trigonometry")
    expect(tid(page, "forecast")).to_contain_text("Tomorrow")
    expect(tid(page, "summary-home")).to_be_focused()
    key.press("Enter")
    expect(tid(page, "page-home")).to_be_visible()

    assert page.evaluate("window.__pointerEvents") == 0
    guarded.assert_clean()
    assert guarded.outbound == []


def test_shortcuts_never_fire_while_typing_except_enter(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()

    # Every letter and digit key of the shortcut list is just text in the answer box.
    text = "hgeudrpf 12345 sinx"
    type_plain(page, "main", text)
    expect(tid(page, "verdict")).to_have_count(0)  # G did not give up
    expect(tid(page, "pause-overlay")).to_have_count(0)
    expect(tid(page, "study")).to_have_attribute("data-phase", "answering")
    expect(tid(page, "progress")).to_contain_text("1 of 6")
    expect(page.get_by_role("navigation", name="Main")).to_have_count(
        0
    )  # F did not toggle focus mode

    # Enter still submits from inside the field (and reports the unreadable answer inline).
    key.press("Enter")
    expect(tid(page, "verdict-main")).to_have_attribute("data-kind", "invalid")
    expect(tid(page, "verdict-main")).to_contain_text("Check your answer")
    # An invalid answer never counts as a try: no "Not quite", no Retry.
    expect(tid(page, "retry")).to_have_count(0)

    # Outside a field the same keys act: Tab onto the toggle, then P pauses and F shows
    # the sidebar.
    expect(tid(page, "field-main")).to_be_focused()
    key.press("Tab")
    key.press("p")
    expect(tid(page, "pause-overlay")).to_be_visible()
    key.press("Escape")
    expect(tid(page, "pause-overlay")).to_have_count(0)
    key.press("Tab")
    key.press("f")  # focus mode off: the sidebar appears
    expect(page.get_by_role("navigation", name="Main")).to_be_visible()
    guarded.assert_clean()


def test_pause_blurs_the_problem_and_resume_restores_it(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    content = tid(page, "study-content")
    expect(tid(page, "field-main")).to_be_focused()
    assert content.evaluate("el => getComputedStyle(el).filter") == "none"

    # The pause button sits at the top right.
    box = tid(page, "pause-button").bounding_box()
    viewport = page.viewport_size
    assert box is not None
    assert viewport is not None
    assert box["x"] > viewport["width"] * 0.6
    assert box["y"] < 80

    # Esc pauses even from the answer box (it types nothing): blur, overlay, nothing focusable.
    key.press("Escape")
    expect(tid(page, "pause-overlay")).to_be_visible()
    expect(tid(page, "study")).to_have_attribute("data-paused", "true")
    expect(content).to_have_attribute("inert", "")
    expect(content).to_have_class(re.compile(r"\bblurred\b"))
    expect(content).to_have_css("filter", re.compile(r"blur\(14px\)"))
    expect(tid(page, "resume-button")).to_be_focused()
    expect(tid(page, "pause-button")).to_have_text(re.compile("Resume"))
    expect(tid(page, "pause-button")).to_have_attribute("aria-pressed", "true")
    key.type("x")  # goes nowhere: the field is inert
    assert page.get_by_test_id("field-main").evaluate("el => el.getValue('latex')") == ""

    key.press("Escape")
    expect(tid(page, "pause-overlay")).to_have_count(0)
    expect(content).to_have_css("filter", "none")
    expect(tid(page, "field-main")).to_be_focused()

    # P pauses when not typing, and the Resume button works with the pointer too.
    expect(tid(page, "field-main")).to_be_focused()
    key.press("Tab")
    key.press("p")
    expect(tid(page, "pause-overlay")).to_be_visible()
    tid(page, "resume-button").click()
    expect(tid(page, "pause-overlay")).to_have_count(0)

    # The top-right button toggles as well.
    tid(page, "pause-button").click()
    expect(tid(page, "pause-overlay")).to_be_visible()
    tid(page, "pause-button").click()
    expect(content).to_have_css("filter", "none")
    guarded.assert_clean()


def test_paused_time_is_not_counted(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    key = page.keyboard
    page.clock.install()
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()
    key.press("Escape")
    page.clock.fast_forward(120_000)  # two minutes of break
    key.press("Escape")
    expect(tid(page, "field-main")).to_be_focused()
    type_plain(page, "main", "4x^3-4x")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    expect(tid(page, "time-note")).to_have_text(re.compile(r"^0:0\d · target 2:30$"))


def test_still_working_note_is_non_modal_and_trims_time(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    key = page.keyboard
    page.clock.install()
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()

    # No target is known while answering, so the note waits the minimum 5 minutes.
    page.clock.fast_forward(5 * 60_000 + 1_000)
    note = tid(page, "still-working")
    expect(note).to_be_visible()
    expect(tid(page, "study-content")).not_to_have_attribute(
        "inert", ""
    )  # the problem stays usable
    expect(tid(page, "pause-overlay")).to_have_count(0)

    # With no answer within 60 seconds the clock pauses and the time is trimmed back.
    page.clock.fast_forward(61_000)
    expect(tid(page, "pause-overlay")).to_contain_text("No activity")
    expect(note).to_have_count(0)
    key.press("Escape")
    expect(tid(page, "pause-overlay")).to_have_count(0)
    expect(tid(page, "field-main")).to_be_focused()
    type_plain(page, "main", "4x^3-4x")
    key.press("Enter")
    expect(verdict_outcome(page)).to_have_attribute("data-outcome", "correct")
    # 5:00 + a moment of work, not 6:01: the unanswered minute is gone.
    expect(tid(page, "time-note")).to_have_text(re.compile(r"^5:0\d · target 2:30$"))


def test_any_input_answers_the_still_working_note(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.clock.install()
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()
    page.clock.fast_forward(5 * 60_000 + 1_000)
    expect(tid(page, "still-working")).to_be_visible()
    page.keyboard.type("4")
    expect(tid(page, "still-working")).to_have_count(0)
    page.clock.fast_forward(90_000)
    expect(tid(page, "pause-overlay")).to_have_count(0)


def test_reason_tag_popover_is_non_modal(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    tag = tid(page, "reason-tag")
    expect(tag).to_have_text(re.compile("Review"))
    tag.click()
    popover = tid(page, "why-popover")
    expect(popover).to_contain_text("Why is this here?")
    expect(popover).to_contain_text("recall")
    expect(tid(page, "study-content")).not_to_have_attribute("inert", "")
    # Esc closes the popover first; it does not pause.
    page.keyboard.press("Escape")
    expect(popover).to_have_count(0)
    expect(tid(page, "study")).to_have_attribute("data-paused", "false")
    tag.click()
    expect(popover).to_be_visible()
    page.mouse.click(20, 500)  # anywhere outside
    expect(popover).to_have_count(0)


def test_math_field_toggle_and_answer_shape_helpers(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    # Move on to the multi-part problem by giving up on the first (keyboard path).
    expect(tid(page, "field-main")).to_be_focused()
    page.keyboard.press("Tab")
    page.keyboard.press("g")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "incorrect")
    page.keyboard.press("Space")
    expect(tid(page, "field-a")).to_be_focused()

    # Interval part: bracket, union, infinity, DNE and none helpers insert LaTeX in math mode.
    for helper in ("open-paren", "infinity", "union", "dne", "none"):
        expect(tid(page, f"helper-a-{helper}")).to_be_visible()
    tid(page, "helper-a-open-paren").click()
    tid(page, "helper-a-infinity").click()
    latex = tid(page, "field-a").evaluate("el => el.getValue('latex')")
    assert latex.replace(" ", "") == r"\left(\infty\right)" or latex.replace(" ", "").startswith(
        "(\\infty"
    )

    # Plain-text mode: the same helpers insert the card format's spelling.
    page.keyboard.press("`")
    plain = page.locator("input[data-testid=field-a]")
    expect(plain).to_be_focused()
    tid(page, "helper-a-infinity").click()
    tid(page, "helper-a-union").click()
    tid(page, "helper-a-dne").click()
    expect(plain).to_have_value("inf U DNE")
    # A point part offers brackets but no union.
    expect(tid(page, "helper-b-union")).to_have_count(0)
    expect(tid(page, "helper-b-open-paren")).to_be_visible()

    # The live preview reports a wrong shape and a syntax slip without using an attempt.
    plain.fill("sinx")
    expect(tid(page, "preview-a")).to_contain_text("Did you mean sin(x)?")
    expect(tid(page, "preview-a")).to_have_attribute("data-status", "error")
    plain.fill("7")
    expect(tid(page, "preview-a")).to_contain_text("Expected an interval")
    plain.fill("(0, 2)")
    expect(tid(page, "preview-a")).to_have_attribute("data-status", "ok")


def test_markdown_renders_math_tables_images_and_never_raw_html(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    hostile = (
        "<script>window.__pwned = 1</script>\n\n"
        '<img src=x onerror="window.__pwned = 2"> <b id="rawbold">raw bold</b>\n\n'
        "[click me](javascript:window.__pwned=3) and [outside](https://example.com/x)\n\n"
        "![remote](http://203.0.113.9/x.png) "
        "![data](data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=)\n\n"
        "Inline \\(x^2 + 1\\) and \\(\\href{javascript:window.__pwned=4}{bad}\\) then\n\n"
        "\\[\\int_0^1 x^2\\,dx = \\frac13\\]\n\n"
        "| \\(x\\) | 1 | 2 |\n| :-- | --: | --: |\n| \\(f(x)\\) | 4 | 9 |\n\n"
        "![A ladder](figures/ladder.svg)\n"
    )
    page.goto(f"{server.origin}/index.html?bridge=mock&prompt={quote(hostile)}#/study")
    problem = tid(page, "problem")
    expect(problem.locator(".katex").first).to_be_visible()

    # Math through KaTeX, display and inline; a table; the bundled figure.
    assert problem.locator(".katex-display").count() == 1
    assert problem.locator(".md-table table th").count() >= 3
    figure = problem.locator("img[src$='.svg']")
    expect(figure).to_have_count(1)
    assert figure.evaluate("img => img.complete && img.naturalWidth > 0")

    # Nothing from the author became an element: no scripts, handlers, links or remote images.
    assert page.evaluate("window.__pwned") is None
    assert problem.locator("script, b, [onerror], a").count() == 0
    assert problem.locator("img").count() == 1
    assert problem.locator(".katex a, .katex [href]").count() == 0  # \href is refused
    text = problem.inner_text()
    assert "<script>" in text  # shown as plain text, not parsed
    assert "<b id=" in text
    assert "[figure: remote]" in text  # a remote image is refused, not loaded
    assert problem.locator("[href]").count() == 0
    sources = problem.locator("[src]").evaluate_all("els => els.map(e => e.src)")
    assert len(sources) == 1
    assert sources[0].startswith(f"{server.origin}/assets/ladder-")
    guarded.assert_clean()
    assert guarded.outbound == []


def test_typing_log_gives_a_plain_logarithm(server: LocalServer, guarded: Guarded) -> None:
    # MathLive's own `log` shortcut inserts \log_{} with an empty base box (backlog).
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    field = tid(page, "field-main")
    expect(field).to_be_focused()
    page.keyboard.type("log(x)")
    latex = field.evaluate("el => el.getValue('latex')").replace(" ", "")
    assert latex.startswith(r"\log"), latex
    assert "_" not in latex, latex
    assert "x" in latex
    guarded.assert_clean()


@pytest.mark.parametrize("height", [WINDOW.height, 600, WINDOW.min_size[1]])
def test_not_quite_and_the_solution_are_in_view_and_have_the_keyboard(
    server: LocalServer, guarded: Guarded, height: int
) -> None:
    page = guarded.page
    page.set_viewport_size({"width": WINDOW.width, "height": height})
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()

    # "Not quite": Retry has the keyboard and, with Give up, sits on screen in the action bar.
    type_plain(page, "main", "4x^3")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict-main")).to_be_in_viewport()
    expect(tid(page, "retry")).to_be_focused()
    expect(tid(page, "retry")).to_be_in_viewport(ratio=1)
    expect(tid(page, "give-up")).to_be_in_viewport(ratio=1)

    # Give up: the verdict is on screen, the review region has the keyboard, Space goes on.
    page.keyboard.press("g")
    expect(tid(page, "verdict")).to_be_in_viewport()
    expect(tid(page, "review")).to_be_focused()
    expect(tid(page, "continue")).to_be_enabled()
    expect(tid(page, "continue")).to_be_in_viewport(ratio=1)
    page.keyboard.press("Space")
    expect(tid(page, "progress")).to_contain_text("2 of 6")
    guarded.assert_clean()


def test_pause_is_not_offered_on_the_summary(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "pause-button")).to_be_visible()
    tid(page, "end-session").click()
    expect(tid(page, "summary")).to_be_visible()
    expect(tid(page, "pause-button")).to_have_count(0)
    guarded.assert_clean()


def test_retry_hands_the_focus_back_to_the_answer_box(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    expect(tid(page, "field-main")).to_be_focused()
    page.keyboard.type("5x")
    page.keyboard.press("Enter")
    expect(tid(page, "retry")).to_be_focused()
    tid(page, "retry").click()  # the pointer works too
    expect(tid(page, "field-main")).to_be_focused()
    expect(tid(page, "submit")).to_be_visible()  # back to Submit, Not sure and Give up
    expect(tid(page, "retry")).to_have_count(0)

    # Several boxes: right parts settle; Retry goes back to the box that was active.
    page.keyboard.press("Tab")
    page.keyboard.press("g")
    expect(tid(page, "verdict")).to_have_attribute("data-outcome", "incorrect")
    page.keyboard.press("Space")
    expect(tid(page, "field-a")).to_be_focused()
    type_plain(page, "a", "(-inf, 0) U (2, inf)")
    tid(page, "field-b").click()
    expect(tid(page, "field-b")).to_be_focused()  # MathLive takes the focus a moment later
    type_plain(page, "b", "(2, -4)")  # a known wrong answer (the minimum)
    tid(page, "field-c").click()
    expect(tid(page, "field-c")).to_be_focused()
    type_plain(page, "c", "(0, 0)")
    page.keyboard.press("Enter")
    expect(tid(page, "verdict-a")).to_have_attribute("data-kind", "correct")
    expect(tid(page, "verdict-b")).to_have_text("Not quite")
    expect(tid(page, "verdict-c")).to_have_text("Not quite")
    expect(tid(page, "study")).not_to_contain_text("That is the minimum")
    expect(tid(page, "retry")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("input[data-testid=field-c]")).to_be_focused()
    guarded.assert_clean()
