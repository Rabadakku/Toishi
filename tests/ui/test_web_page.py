"""The built page in a real browser engine, fully offline, with the dev mock bridge."""

import re

from playwright.sync_api import expect

from tests.ui.conftest import Guarded, LocalServer


def test_page_boots_offline_and_passes_its_self_test(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock&selftest=1#/settings")

    # The bridge round trip (mock bridge mirrors app/api.py).
    expect(page.get_by_test_id("bridge-status")).to_contain_text("v0.0.0-mock")
    page.get_by_test_id("ping").click()
    expect(page.get_by_test_id("ping-reply")).to_have_text("pong: hello from the page")

    # The in-page self-test (same one the .app runs): CSP, KaTeX + fonts, MathLive, bridge.
    selftest = page.get_by_test_id("selftest")
    expect(selftest).to_be_visible()
    assert selftest.get_attribute("data-status") == "pass", selftest.inner_text()
    for name in ("csp", "katex", "katex-fonts", "mathlive", "bridge"):
        assert name in selftest.inner_text()

    # The settings sample renders math with KaTeX's own fonts, all from 127.0.0.1.
    expect(page.locator("[data-testid=text-sample] .katex-html")).to_be_visible()
    assert any("KaTeX_Main" in url for url in guarded.requests)
    guarded.assert_clean()


def test_study_page_loads_bundled_fonts_and_mathlive(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock#/study")
    field = page.get_by_test_id("field-main")
    expect(field).to_be_focused()  # MathLive mounted, editable, focused
    expect(page.locator("[data-testid=problem] .katex-html").first).to_be_visible()
    assert page.locator("[data-testid=problem] .katex-error").count() == 0

    # Both families are bundled files served from 127.0.0.1 (no CDN, no system fallback needed).
    loaded = page.evaluate(
        """async () => ({
          serif: (await document.fonts.load('18px "Source Serif 4 Variable"', 'Aa')).length,
          inter: (await document.fonts.load('16px "Inter Variable"', 'Aa')).length,
        })"""
    )
    assert loaded == {"serif": 1, "inter": 1}
    assert any("source-serif-4-latin-wght" in url for url in guarded.requests)
    assert any("inter-latin-wght" in url for url in guarded.requests)
    guarded.assert_clean()


def test_page_without_bridge_says_so(server: LocalServer, guarded: Guarded) -> None:
    page = guarded.page
    page.clock.install()
    page.goto(f"{server.origin}/index.html#/settings")
    page.clock.run_for(11_000)
    status = page.get_by_test_id("bridge-status")
    expect(status).to_contain_text("Bridge unavailable")
    assert page.get_by_test_id("ping").is_disabled()


def test_study_screen_runs_without_any_bridge(server: LocalServer, guarded: Guarded) -> None:
    # No ?bridge=mock and no pywebview: the study prototype falls back to its sample problems.
    page = guarded.page
    page.goto(f"{server.origin}/index.html#/study")
    # The page waits a few seconds for pywebview (it adds its api after load), then the mock.
    expect(page.get_by_test_id("sample-banner")).to_be_visible(timeout=15_000)
    expect(page.get_by_test_id("progress")).to_contain_text("1 of 6")
    assert re.search(r"f.*x", page.get_by_test_id("problem").inner_text())


def test_tripwire_catches_outbound_requests(server: LocalServer, guarded: Guarded) -> None:
    # A page with no CSP that tries to load a remote image: the route guard must see it.
    url = server.add("/__test__/leaky.html", '<img src="http://203.0.113.7/x.png">', "text/html")
    guarded.page.goto(url)
    guarded.page.wait_for_load_state("load")
    assert guarded.outbound == ["http://203.0.113.7/x.png"]
