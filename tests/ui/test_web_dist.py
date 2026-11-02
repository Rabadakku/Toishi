"""Static checks on the built page: CSP, no remote references, licenses, assets.

JS bundles are not grepped for hostnames: MathLive, for example, compares
hostnames as strings without loading anything. Remote loads are caught where
they happen instead: the CSP (no remote origins) and the request tripwire in
test_web_page.py.
"""

import re
from pathlib import Path

EXPECTED_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; img-src 'self'; media-src 'self'; connect-src 'self'; "
    "worker-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; "
    "form-action 'none'; manifest-src 'none'"
)


def csp_of(index_html: str) -> str:
    match = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', index_html)
    assert match, "CSP meta tag missing"
    return match.group(1)


def test_csp_is_the_documented_policy(web_dist: Path) -> None:
    policy = csp_of((web_dist / "index.html").read_text())
    assert policy == EXPECTED_CSP  # change only together with ADR-0002
    assert "unsafe-eval" not in policy
    assert "http" not in policy  # no remote origins


def test_html_and_css_reference_only_relative_urls(web_dist: Path) -> None:
    html = (web_dist / "index.html").read_text()
    refs = re.findall(r'(?:src|href)="([^"]+)"', html)
    assert refs
    assert all(r.startswith("./") for r in refs), refs
    for css in web_dist.rglob("*.css"):
        urls = re.findall(r"url\(([^)]+)\)", css.read_text())
        remote = [u for u in urls if re.match(r"['\"]?(https?:)?//", u)]
        assert remote == [], f"{css.name}: {remote}"


def test_vendored_assets_and_licenses_are_shipped(web_dist: Path) -> None:
    names = {p.name for p in (web_dist / "assets").iterdir()}
    assert any(n.startswith("KaTeX_Main-Regular") and n.endswith(".woff2") for n in names)
    sounds = {p.name for p in (web_dist / "mathlive" / "sounds").iterdir()}
    assert {"plonk.wav", "keypress-standard.wav"} <= sounds
    licenses = (web_dist / "licenses" / "THIRD-PARTY-LICENSES.md").read_text()
    for package in ("katex", "mathlive", "svelte"):
        assert f"## {package} " in licenses


def test_fonts_are_bundled_with_their_open_font_licenses(web_dist: Path) -> None:
    names = {p.name for p in (web_dist / "assets").iterdir()}
    for family in ("inter-latin-wght-normal", "source-serif-4-latin-wght-normal"):
        assert any(n.startswith(family) and n.endswith(".woff2") for n in names), family
    licenses = (web_dist / "licenses" / "THIRD-PARTY-LICENSES.md").read_text()
    for package in (
        "@fontsource-variable/inter",
        "@fontsource-variable/source-serif-4",
        "markdown-it",
    ):
        assert f"## {package} " in licenses
    # Both fonts are SIL OFL 1.1 and the license text ships in full, once per font.
    assert licenses.count("SIL OPEN FONT LICENSE Version 1.1") >= 2


def _milliseconds(value: str) -> float:
    return float(value[:-2]) if value.endswith("ms") else float(value.removesuffix("s")) * 1000


def test_no_fixed_motion_longer_than_150_ms(web_dist: Path) -> None:
    """Every duration in the built CSS is the --dur token (120 ms) or at most 150 ms."""
    css = "\n".join(p.read_text() for p in web_dist.rglob("*.css"))
    token = re.search(r"--dur:\s*(\.?\d+(?:\.\d+)?m?s)", css)  # the minifier writes .12s
    assert token
    assert _milliseconds(token.group(1)) == 120
    declared = re.findall(r"(?:transition|animation)(?:-duration)?:([^;}]+)[;}]", css)
    durations = [
        _milliseconds(d)
        for value in declared
        for d in re.findall(r"(?<![\w.-])\d*\.?\d+m?s\b", value)
    ]
    assert all(d <= 150 for d in durations), sorted(set(durations))
