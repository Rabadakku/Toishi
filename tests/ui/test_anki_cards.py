"""Imported Anki cards and card images on the study page (ADR-0015, ADR-0017).

The built page runs against the REAL core behind the bridge harness (tests/app/harness.py):
decks are imported by core.importers.anki into a real profile, studied through StudyService,
and every image, sound and card stylesheet comes from the app's own /media route. Every test
ends with the offline tripwire: not one request left 127.0.0.1, no CSP violation, no console
error.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Locator, Page, expect

from app.api import Api
from app.packs import shipped_packs
from core import cards, grader
from core.importers.anki import apply_anki_import, plan_anki_import, read_package
from core.storage import ProfileManager
from tests.app.harness import BridgeHarness, shim_script
from tests.ui import anki_decks
from tests.ui.conftest import Guarded

HOSTILE = """<div class="anki-card card1" data-anki-css="../../etc/passwd">
<img src="x" onerror="window.__pwned = 1" id="victim">
<img src="https://evil.example/track.png"> <img src="//evil.example/t.png">
<img src="paris.png" alt="mine" onload="window.__pwned = 2">
<script>window.__pwned = 3</script>
<b onclick="window.__pwned = 4">bold</b> <a href="javascript:window.__pwned = 5">link</a>
<svg onload="window.__pwned = 6"><script>window.__pwned = 7</script></svg>
<iframe src="https://evil.example/frame"></iframe> <object data="https://evil.example/o"></object>
<style>body { display: none }</style>
<form action="https://evil.example/post"><input name="x" value="stolen"></form>
<div class="fill" style="color: red; background: url(https://evil.example/bg.png)">red</div>
<div class="own" style="background: url(paris.png)">own picture</div>
<div class="expr" style="width: expression(window.__pwned = 8); color: blue">blue</div>
<div class="esc" style="background: u\\72l(https://evil.example/e.png); color: green">green</div>
<audio src="https://evil.example/a.mp3" autoplay></audio>
<video src="https://evil.example/v.mp4"></video>
<p class="overlay" style="position: fixed; inset: 0; z-index: 99999">overlay</p>
<div data-anki-css="_anki-nt-000000000000.css">nested wrapper</div>
\\(x^2\\) <code>\\(not math\\)</code>
</div>"""


# Records every "[image: ...]" note that is ever drawn, even for a moment.
NOTE_WATCH = """
window.__notes = 0;
const isNote = (node) =>
  node.nodeType === 1 && (node.matches('.anki-missing') || node.querySelector('.anki-missing'));
new MutationObserver((records) => {
  for (const record of records)
    for (const node of record.addedNodes) if (isNote(node)) window.__notes += 1;
}).observe(document, {childList: true, subtree: true});
"""


@dataclass
class Studied:
    page: Page
    api: Api
    harness: BridgeHarness
    guarded: Guarded
    responses: list[tuple[str, int]] = field(default_factory=list)

    def tid(self, name: str) -> Locator:
        return self.page.get_by_test_id(name)

    @property
    def card(self) -> Locator:
        """The card on screen, whichever side."""
        return self.tid("problem").locator(".anki-card")

    def open(self) -> None:
        self.page.goto(f"{self.harness.origin}/index.html#/study")
        expect(self.tid("study")).to_have_attribute("data-phase", "front")

    def reveal(self) -> Locator:
        self.page.keyboard.press("Space")
        back = self.tid("flashcard-back")
        expect(back).to_be_visible()
        return back

    def media_paths(self) -> list[str]:
        return [path for path, _status in self.harness.media_requests]

    def assert_clean(self) -> None:
        bad = [(path, status) for path, status in self.responses if status != 200]
        assert bad == [], f"failed media requests: {bad}"
        assert self.harness.errors == []
        self.guarded.assert_clean()
        local = [u for u in self.guarded.requests if urlsplit(u).hostname == "127.0.0.1"]
        assert len(local) == len(self.guarded.requests)  # nothing else was even attempted


@pytest.fixture(scope="module")
def decks(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    base = tmp_path_factory.mktemp("anki-decks")
    return {
        "pictures": anki_decks.picture_deck(base / "pictures"),
        "cloze": anki_decks.cloze_deck(base / "cloze"),
        "math": anki_decks.math_deck(base / "math"),
    }


@pytest.fixture
def studying(
    tmp_path: Path, web_dist: Path, guarded: Guarded, decks: dict[str, Path]
) -> Iterator[Callable[..., Studied]]:
    """start("pictures") -> a profile whose only cards are that deck's, sections on."""
    opened: list[tuple[Api, BridgeHarness]] = []

    def start(*names: str, packs: list[Path] | None = None) -> Studied:
        api = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=lambda: packs or [])
        api.profile_create({"name": "Sam"})
        users = api._store().users
        for name in names:
            apply_anki_import(users, plan_anki_import(users, read_package(decks[name])))
        for course in api.library_get()["courses"]:
            api.library_set_state({"id": course["id"], "state": "learning"})
        harness = BridgeHarness(web_dist, api)
        opened.append((api, harness))
        guarded.page.context.add_init_script(shim_script())
        studied = Studied(guarded.page, api, harness, guarded)
        guarded.page.on(
            "response",
            lambda r: studied.responses.append((r.url, r.status)) if "/media/" in r.url else None,
        )
        return studied

    yield start
    for api, harness in opened:
        harness.close()
        api._close(backup=False)
    grader.shutdown()
    cards.shutdown()


def decoded(img: Locator) -> list[int]:
    """[width, height] of the image as the browser decoded it (waits for the load)."""
    size: list[int] = img.evaluate(
        """el => new Promise((done) => {
             const size = () => done([el.naturalWidth, el.naturalHeight]);
             if (el.complete) size(); else el.addEventListener('load', size, {once: true});
           })"""
    )
    return size


# ---------------------------------------------------------------- Basic card, image, scoped CSS


def test_a_basic_card_shows_its_image_and_only_its_own_css(
    studying: Callable[..., Studied],
) -> None:
    s = studying("pictures")
    s.page.context.add_init_script(NOTE_WATCH)
    s.open()
    page = s.page
    wrapper = s.card.first

    # The front: sanitized HTML drawn as a card (not Markdown text), with its picture.
    expect(wrapper).to_have_class(re.compile(r"anki-card card1 anki-nt-[0-9a-f]{12}"))
    expect(s.tid("problem")).not_to_contain_text("[figure")
    picture = s.tid("problem").locator("img")
    expect(picture).to_have_count(1)
    assert (picture.get_attribute("src") or "").startswith("/media/user/")
    assert (picture.get_attribute("src") or "").endswith(".png")
    expect(picture).to_have_attribute("alt", "a red square")
    assert decoded(picture) == [48, 32]

    # The note type's CSS applies to the card...
    prompt = s.tid("problem").locator(".prompt")
    expect(prompt).to_have_css("color", "rgb(1, 2, 3)")
    expect(prompt).to_have_css("border-top-color", "rgb(4, 5, 6)")
    expect(wrapper).to_have_css("font-family", re.compile("Georgia"))
    # ... including a url(_bg.png) that now points at the stored file ...
    background = wrapper.evaluate("el => getComputedStyle(el).backgroundImage")
    assert "/media/user/" in background
    # ... and a bare `div { ... }` rule stays inside the card.
    assert prompt.evaluate("el => getComputedStyle(el).marginLeft") == "13px"
    leaked = s.page.evaluate(
        """() => [...document.querySelectorAll('div')]
             .filter((d) => !d.closest('.anki-host') && getComputedStyle(d).marginLeft === '13px')
             .length"""
    )
    assert leaked == 0
    assert page.locator("style[data-anki-css]").count() == 1

    # The back is the answer part, in the same CSS.
    back = s.reveal()
    expect(back.locator(".answer")).to_have_css("color", "rgb(7, 8, 9)")
    expect(back).to_contain_text("Paris, the capital")
    expect(back.locator("b")).to_have_text("capital")

    # Night mode: the note type's .nightMode rule applies (mapped onto .anki-night).
    page.emulate_media(color_scheme="dark")
    expect(s.card.first).to_have_class(re.compile(r"anki-night"))
    expect(s.tid("problem").locator(".prompt")).to_have_css("color", "rgb(250, 250, 250)")
    page.emulate_media(color_scheme="light")
    expect(s.card.first).not_to_have_class(re.compile(r"anki-night"))
    expect(s.tid("problem").locator(".prompt")).to_have_css("color", "rgb(1, 2, 3)")

    # The card was never drawn without its files (no "[image: ...]" note, not even briefly).
    assert page.evaluate("window.__notes") == 0

    # Everything came through the app's media route: the picture, the background, the CSS.
    paths = s.media_paths()
    assert sorted({Path(p).suffix for p in paths}) == [".css", ".png"]
    assert len(paths) == 3  # the picture, the background, the stylesheet
    assert all(p.startswith("/media/user/") for p in paths)
    s.assert_clean()


# ---------------------------------------------------------------- cloze


def test_a_cloze_card_hides_the_blank_then_shows_the_answer(
    studying: Callable[..., Studied],
) -> None:
    s = studying("cloze")
    s.open()
    front = s.tid("problem")
    expect(s.card.first).to_be_visible()
    text = front.inner_text()
    assert text.count("[") == 1  # exactly one blank: "[city]" (c1) or "[...]" (c2)
    assert ("Paris" in text) != ("France" in text)  # the blank's answer is hidden
    assert "{{" not in text
    back = s.reveal()
    expect(back).to_contain_text("Paris")
    expect(back).to_contain_text("France")
    expect(back).to_contain_text("Europe")
    s.assert_clean()


# ---------------------------------------------------------------- math


def test_math_in_imported_html_is_typeset_with_katex(studying: Callable[..., Studied]) -> None:
    s = studying("math")
    s.open()
    problem = s.tid("problem")
    expect(problem.locator(".katex")).to_have_count(2)  # \(x^2 = 4\) and \(x\)
    expect(problem).to_contain_text("Solve")
    assert "\\(" not in problem.inner_text()
    assert problem.locator(".katex-display").count() == 0
    # KaTeX's own output, not text: the superscript is an element and the fonts are bundled.
    assert problem.locator(".katex .msupsub").count() >= 1
    back = s.reveal()
    expect(back.locator(".katex-display")).to_have_count(1)  # \[ x = \pm 2 \]
    expect(back.locator(".katex")).to_have_count(2)  # the display one and \frac{4}{2} = 2
    assert "\\[" not in back.inner_text()
    assert "\\frac" not in back.inner_text().replace("\\frac{4}{2}", "")
    s.assert_clean()


# ---------------------------------------------------------------- hostile HTML stays inert


def test_hostile_html_in_a_stored_card_stays_inert(studying: Callable[..., Studied]) -> None:
    s = studying("pictures")
    users = s.api._store().users
    (card,) = users.user_cards()
    links = users.media.links(card.id)
    assert {"paris.png", "_bg.png"} <= set(links)
    users.put_user_content(replace(card, front_md=HOSTILE, back_md=HOSTILE))
    s.open()
    page = s.page
    shown = s.tid("problem")
    expect(shown.locator(".anki-card")).to_have_count(1)

    # Nothing ran: no handler, script, link or frame survived, and no request left.
    page.wait_for_timeout(300)
    assert page.evaluate("window.__pwned") is None
    assert shown.locator("script, style, svg, iframe, object, embed, form, input").count() == 0
    assert shown.locator("[onerror], [onclick], [onload], [id], [srcset]").count() == 0
    assert shown.locator("a[href], [href]").count() == 0
    assert page.locator("body").evaluate("el => getComputedStyle(el).display") != "none"
    # Pictures: only the card's own file loads; the rest are notes, not requests.
    images = shown.locator("img")
    expect(images).to_have_count(1)
    assert (images.get_attribute("src") or "").startswith("/media/user/")
    assert shown.locator(".anki-missing").count() >= 5
    # Styles: foreign url() and CSS escapes are dropped, harmless declarations stay.
    assert shown.locator(".fill").evaluate("el => el.getAttribute('style')") == "color: red"
    assert shown.locator(".expr").evaluate("el => el.getAttribute('style')") == "color: blue"
    assert shown.locator(".esc").evaluate("el => el.getAttribute('style')") == "color: green"
    own = shown.locator(".own").evaluate("el => el.getAttribute('style')")
    assert own.startswith('background: url("/media/user/')
    # The wrapper's stylesheet name must look like core's; a nested one is plain data.
    assert page.locator("style[data-anki-css]").count() == 0
    # Whatever the card's CSS does, it stays in the card's box (position: fixed too).
    host = shown.locator(".anki-host").bounding_box()
    overlay = shown.locator(".overlay").bounding_box()
    assert host is not None
    assert overlay is not None
    assert host["x"] - 1 <= overlay["x"]
    assert overlay["x"] + overlay["width"] <= host["x"] + host["width"] + 1
    # Math still works, except inside <code>.
    expect(shown.locator(".katex")).to_have_count(1)
    expect(shown.locator("code")).to_have_text("\\(not math\\)")
    # The back side takes the same path.
    s.reveal()
    assert page.evaluate("window.__pwned") is None

    media = [p for p in s.media_paths() if not p.endswith(".css")]
    assert media
    assert all(p.startswith("/media/user/") for p in media)
    assert s.guarded.outbound == []
    assert all("evil" not in url for url in s.guarded.requests)
    s.assert_clean()


# ---------------------------------------------------------------- pack cards (Markdown)

PARABOLA = "test.quad.parabola.001"


def test_a_pack_cards_markdown_image_comes_from_the_media_route(
    studying: Callable[..., Studied],
) -> None:
    packs = [p for p in shipped_packs() if p.stem == "test"]
    s = studying(packs=packs)
    api = s.api
    card = api._store().packs.card(PARABOLA)
    assert card is not None
    assert "![The graph of y = x^2 - 1](media/parabola.svg)" in (card.question_md or "")

    # The real pack card's id and text on the first item the real queue serves (reaching a
    # tier-3 card by playing is not what this test is about); the media come from the real
    # library_card_media and the real route.
    def show_parabola(method: Callable[..., Any]) -> Callable[..., Any]:
        def call(*args: Any) -> Any:
            turn = method(*args)
            if turn and turn.get("type") == "problem":
                shown = turn["problem"]["card"]
                shown["id"], shown["prompt_md"] = PARABOLA, card.question_md
            return turn

        return call

    for name in ("study_start", "study_resume", "study_current"):
        setattr(api, name, show_parabola(getattr(api, name)))
    s.page.goto(f"{s.harness.origin}/index.html#/study")
    problem = s.tid("problem")
    figure = problem.locator("img")
    expect(figure).to_have_count(1)
    expect(figure).to_have_attribute("src", "/media/pack/test/media/parabola.svg")
    expect(figure).to_have_attribute("alt", "The graph of y = x^2 - 1")
    assert decoded(figure)[0] > 0
    expect(problem).not_to_contain_text("[figure")
    assert s.media_paths() == ["/media/pack/test/media/parabola.svg"]
    s.assert_clean()


def test_text_without_images_asks_for_no_media(studying: Callable[..., Studied]) -> None:
    packs = [p for p in shipped_packs() if p.stem == "test"]
    s = studying(packs=packs)
    s.page.goto(f"{s.harness.origin}/index.html#/study")
    expect(s.tid("problem")).to_be_visible()
    s.page.wait_for_timeout(200)
    assert "library_card_media" not in s.harness.calls
    assert s.harness.media_requests == []
    s.assert_clean()
