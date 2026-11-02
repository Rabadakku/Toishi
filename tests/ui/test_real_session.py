"""The built page with the REAL core: a whole session on the Test pack, by keyboard.

tests/app/harness.py serves app/web_dist and answers the page's bridge calls with app.api.Api
over StudyService (real storage, real answer checker). The page's `window.pywebview.api` is a
test-only init script; the shipped page never contains it.
"""

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Locator, Page, expect

from app.api import Api
from app.packs import shipped_packs
from core import cards, grader
from core.model import Card
from core.storage import ProfileManager
from tests.app.harness import BRIDGE_PREFIX, BridgeHarness, shim_script
from tests.ui.conftest import Guarded

SECTION = "Test Course::1 Algebra::1.1 Linear Equations"
WRONG = "987654321"
TYPED_TYPES = {"number", "expression", "equation", "set", "list", "interval", "point", "text"}


@dataclass
class Real:
    page: Page
    api: Api
    harness: BridgeHarness
    guarded: Guarded
    log: list[str] = field(default_factory=list)

    def tid(self, name: str) -> Locator:
        return self.page.get_by_test_id(name)

    def current_card(self) -> Card:
        session = self.api._store().users.latest_open_session()
        assert session is not None
        assert session.current is not None
        card = self.api._store().packs.card(str(session.current["card_id"]))
        assert card is not None
        return card


@pytest.fixture
def real(tmp_path: Path, web_dist: Path, guarded: Guarded) -> Iterator[Real]:
    packs = shipped_packs()  # compiled into build/packs when stale
    api = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=lambda: packs)
    harness = BridgeHarness(web_dist, api)
    guarded.page.context.add_init_script(shim_script())
    try:
        yield Real(guarded.page, api, harness, guarded)
    finally:
        harness.close()
        api._close(backup=False)
        grader.shutdown()
        cards.shutdown()


def keys_for(card: Card) -> list[tuple[str, str]]:
    """(answer type, what to type or press) per box, for a student who knows the answer."""
    out: list[tuple[str, str]] = []
    for part in card.parts or (card,):
        kind = part.answer_type
        if kind == "choice":
            out.append((kind, str(next(i + 1 for i, c in enumerate(part.choices) if c.correct))))
        elif kind == "truefalse":
            out.append((kind, "1" if (part.answer or "").strip().lower() == "true" else "2"))
        elif kind == "text":
            out.append((kind, (part.answer or "").split(";")[0].strip()))
        else:
            out.append((kind, part.answer or ""))
    return out


def single_typed(card: Card) -> str | None:
    """The key, when the card has one typed box (else None: answer it another way)."""
    entries = keys_for(card)
    if len(entries) == 1 and entries[0][0] in TYPED_TYPES and card.kind == "problem":
        return entries[0][1]
    return None


def type_plain(r: Real, text: str) -> None:
    """From the focused math field: ` switches to plain text, then type."""
    expect(r.tid("field-main")).to_be_focused()
    r.page.keyboard.press("`")
    plain = r.page.locator("input[data-testid=field-main]")
    expect(plain).to_be_focused()
    plain.press("ControlOrMeta+a")
    r.page.keyboard.type(text)
    expect(plain).to_have_value(text)


def wait_phase(r: Real, *phases: str) -> str:
    study = r.tid("study")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        phase = study.get_attribute("data-phase") or ""
        if phase in phases:
            return phase
        r.page.wait_for_timeout(50)
    raise AssertionError(f"phase stayed {study.get_attribute('data-phase')!r}, wanted {phases}")


SETTLED = ("answering", "example", "front", "back", "review", "self-grade", "summary", "empty")


def until(check: Callable[[], Any], r: Real, timeout_s: float = 10) -> None:
    """Poll a Python-side condition. Waits through Playwright (not time.sleep), so the
    route guard keeps forwarding the page's bridge requests meanwhile."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if check():
            return
        r.page.wait_for_timeout(50)
    raise AssertionError(
        f"condition never held; last calls {r.harness.calls[-8:]}, {r.harness.errors}"
    )


def answer_correctly(r: Real, card: Card) -> None:
    key = r.page.keyboard
    text = single_typed(card)
    if text is not None:
        type_plain(r, text)
        key.press("Enter")
    else:
        for kind, value in keys_for(card):
            if kind in ("choice", "truefalse"):
                key.press(value)
        key.press("Enter")
    expect(r.tid("verdict")).to_have_attribute("data-outcome", "correct")


def give_up(r: Real) -> None:
    key = r.page.keyboard
    if r.page.locator("[data-testid=field-main]").count():
        expect(r.page.locator("[data-testid=field-main]")).to_be_focused()
    key.press("Tab")  # out of the answer box, so G is a shortcut
    key.press("g")
    expect(r.tid("verdict")).to_have_attribute("data-outcome", "incorrect")
    expect(r.tid("continue")).to_be_enabled()  # no "What went wrong?" to answer first


def test_real_session_on_the_test_pack_by_keyboard(real: Real) -> None:
    r, page, key = real, real.page, real.page.keyboard
    page.goto(f"{r.harness.origin}/index.html")

    # First run: a profile needs only a name.
    expect(r.tid("page-welcome")).to_be_visible()
    expect(r.tid("profile-name")).to_be_focused()
    key.type("Sam")
    key.press("Enter")

    # Home: nothing is planned until a section is switched on in the Library.
    expect(r.tid("nothing-due")).to_be_visible()
    expect(r.tid("open-library")).to_be_focused()
    key.press("Enter")
    section = page.locator(f'[data-testid=section][data-id="{SECTION}"]')
    expect(section).to_have_attribute("data-state", "off")
    section.get_by_test_id("state-learning").focus()
    key.press("Enter")
    expect(section).to_have_attribute("data-state", "learning")
    expect(page.get_by_test_id("section").nth(1)).to_have_attribute("data-state", "off")

    # Home: today's problems and minutes, never an overdue count; Enter starts.
    page.goto(f"{r.harness.origin}/index.html#/home")
    expect(r.tid("today-plan")).to_contain_text("problems")
    expect(r.tid("page-home")).not_to_contain_text("overdue")
    expect(r.tid("start")).to_be_focused()
    key.press("Enter")

    done: dict[str, bool] = {"correct": False, "wrong": False, "reload": False}
    for _ in range(40):
        phase = wait_phase(r, *SETTLED)
        if phase in ("summary", "empty"):
            break
        kind = r.tid("study").get_attribute("data-kind")
        if phase == "example":
            key.press("Space")
        elif phase == "front":
            key.press("Space")
            expect(r.tid("flashcard-back")).to_be_visible()
            key.press("3")
        elif phase == "back":
            key.press("3")
        elif phase == "self-grade" or (phase == "answering" and r.tid("parts").count() == 0):
            key.press("1")
            wait_phase(r, "review")
            key.press("Space")
        elif phase == "review":
            key.press("Space")
        elif kind == "flashcard":  # a typed flashcard
            answer_correctly(r, r.current_card())
            key.press("Space")
        else:
            card = r.current_card()
            text = single_typed(card)
            item = r.tid("study").get_attribute("data-item")
            if not done["correct"] and text is not None:
                # No hints to ask for (wave 2): a pause and resume, then the right answer.
                expect(r.page.get_by_role("button", name="Hint")).to_have_count(0)
                key.press("Escape")
                expect(r.tid("pause-overlay")).to_be_visible()
                expect(r.tid("study")).to_have_attribute("data-paused", "true")
                key.press("Escape")
                expect(r.tid("pause-overlay")).to_have_count(0)
                answer_correctly(r, card)
                expect(r.tid("skill-name")).to_be_visible()
                expect(r.tid("time-note")).to_be_visible()
                key.press("Space")
                done["correct"] = True
            elif not done["wrong"] and text is not None:
                # Wrong: "Not quite" with Retry and Give up only. Enter retries (the box gets
                # the keyboard back); G shows the solution. U undoes the answer.
                type_plain(r, WRONG)
                key.press("Enter")
                expect(r.tid("verdict-main")).to_contain_text("Not quite")
                expect(r.tid("retry")).to_be_focused()
                expect(r.tid("submit")).to_have_count(0)
                key.press("Enter")
                expect(page.locator("input[data-testid=field-main]")).to_be_focused()
                key.press("Tab")
                key.press("g")
                expect(r.tid("verdict")).to_have_attribute("data-outcome", "incorrect")
                key.press("u")
                expect(r.tid("turn-note")).to_contain_text("Undone")
                expect(r.tid("study")).to_have_attribute("data-item", item or "")
                wait_phase(r, "answering")
                type_plain(r, WRONG)
                key.press("Enter")
                expect(r.tid("verdict-main")).to_contain_text("Not quite")
                expect(r.tid("retry")).to_be_focused()
                key.press("g")  # the keyboard is on Retry, so G gives up
                expect(r.tid("verdict")).to_have_attribute("data-outcome", "incorrect")
                expect(r.tid("continue")).to_be_enabled()
                key.press("Space")
                done["wrong"] = True
            elif not done["reload"] and text is not None:
                # Type, pause (saves the draft and time), reload: the same problem comes back.
                type_plain(r, text)
                key.press("Escape")
                until(lambda: r.api._store().users.latest_open_session().draft is not None, r)  # type: ignore[union-attr]
                page.reload()
                expect(r.tid("study")).to_have_attribute("data-item", item or "")
                plain = page.locator("input[data-testid=field-main]")
                expect(plain).to_have_value(text)
                expect(plain).to_be_focused()
                key.press("Enter")
                expect(r.tid("verdict")).to_have_attribute("data-outcome", "correct")
                key.press("Space")
                done["reload"] = True
            else:
                give_up(r)
                key.press("Space")
    else:
        pytest.fail("the session never ended")

    assert all(done.values()), done
    expect(r.tid("summary")).to_be_visible()
    expect(r.tid("summary-correct")).to_contain_text(" of ")
    expect(r.tid("forecast")).to_contain_text("Tomorrow")
    stored = [a for a in r.api._store().users.attempts() if a.final]
    assert len(stored) >= 3
    unexpected = [e for e in r.harness.errors if "UserMessage" not in e]
    assert unexpected == []
    r.guarded.assert_clean()


def test_the_shipped_page_has_no_bridge_shim(web_dist: Path) -> None:
    for path in web_dist.rglob("*"):
        if path.suffix in (".js", ".html"):
            assert BRIDGE_PREFIX not in path.read_text(errors="ignore"), path
