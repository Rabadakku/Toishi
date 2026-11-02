"""The design tokens (web/src/styles/tokens.css) against the spec and WCAG AA.

No browser needed: the CSS file is the single source of truth for the palette, so this
parses it and checks every text/background pair the interface uses, in Day and in Night.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
TOKENS_CSS = ROOT / "web/src/styles/tokens.css"
BASE_CSS = ROOT / "web/src/styles/base.css"
SPEC = ROOT / "docs/spec.md"
SRC = ROOT / "web/src"

AA = 4.5

# Colors shipped by the spec's palette table, by CSS custom property name.
SPEC_TOKENS = [
    "background",
    "surface",
    "border",
    "text",
    "text-muted",
    "accent",
    "correct",
    "incorrect",
    "warning",
    "selection",
]

# Every (foreground, background) pair that appears as text in the interface.
TEXT_PAIRS = [
    ("text", "background"),
    ("text", "surface"),
    ("text", "surface-sunken"),
    ("text", "selection"),
    ("text-muted", "background"),
    ("text-muted", "surface"),
    ("text-muted", "surface-sunken"),
    ("text-muted", "selection"),
    ("accent", "background"),
    ("accent", "surface"),
    ("correct", "background"),
    ("correct", "surface"),
    ("incorrect", "surface"),
    ("warning", "surface"),
    ("on-accent", "accent"),
    ("on-accent", "accent-strong"),
]


def block_after(css: str, opener: str) -> str:
    """The text between the braces of the first block that starts with `opener`."""
    start = css.index(opener)
    depth = 0
    for i in range(css.index("{", start), len(css)):
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        if depth == 0:
            return css[css.index("{", start) + 1 : i]
    raise AssertionError(f"unterminated block after {opener!r}")


def declarations(block: str) -> dict[str, str]:
    return {
        name: value.strip()
        for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block)
        if "{" not in value
    }


def plain_root_declarations(css: str) -> dict[str, str]:
    """Day palette plus the type, spacing and motion tokens: every top-level `:root { ... }`."""
    merged: dict[str, str] = {}
    for match in re.finditer(r"^:root \{", css, re.MULTILINE):
        merged |= declarations(block_after(css[match.start() :], ":root {"))
    return merged


@pytest.fixture(scope="module")
def themes() -> dict[str, dict[str, str]]:
    css = TOKENS_CSS.read_text()
    day = plain_root_declarations(css)
    night = declarations(block_after(css, ":root[data-theme='night']"))
    automatic_media = block_after(css, "@media (prefers-color-scheme: dark)")
    automatic = declarations(block_after(automatic_media, ":root:not([data-theme])"))
    return {"day": day, "night": night, "automatic-dark": automatic}


def luminance(color: str) -> float:
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", color), color
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_palette_matches_the_spec_table(themes: dict[str, dict[str, str]]) -> None:
    spec = SPEC.read_text()
    table = spec[spec.index("## Design and theme") :]
    rows = dict(re.findall(r"^\| (\S+) \| `(#\w{6})` \| `#\w{6}` \|", table, re.MULTILINE))
    night_rows = dict(re.findall(r"^\| (\S+) \| `#\w{6}` \| `(#\w{6})` \|", table, re.MULTILINE))
    assert set(SPEC_TOKENS) <= set(rows), "palette table not found in the spec"
    for name in SPEC_TOKENS:
        assert themes["day"][name].lower() == rows[name].lower(), f"Day {name}"
        assert themes["night"][name].lower() == night_rows[name].lower(), f"Night {name}"


@pytest.mark.parametrize("theme", ["day", "night"])
@pytest.mark.parametrize(("fg", "bg"), TEXT_PAIRS)
def test_every_text_pair_meets_wcag_aa(
    themes: dict[str, dict[str, str]], theme: str, fg: str, bg: str
) -> None:
    colors = themes[theme]
    ratio = contrast(colors[fg], colors[bg])
    assert ratio >= AA, f"{theme}: {fg} on {bg} is {ratio:.2f}:1 (needs {AA}:1)"


@pytest.mark.parametrize("theme", ["day", "night"])
def test_main_text_contrast_is_high_but_not_maximal(
    themes: dict[str, dict[str, str]], theme: str
) -> None:
    # Spec: "about 13 to 15 to 1", which cuts glare.
    ratio = contrast(themes[theme]["text"], themes[theme]["background"])
    assert 13 <= ratio <= 15.5, ratio


def test_no_pure_white_or_black(themes: dict[str, dict[str, str]]) -> None:
    for theme in ("day", "night"):
        for name, value in themes[theme].items():
            if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                assert value.lower() not in {"#ffffff", "#000000"}, f"{theme} {name}"


def test_automatic_night_is_identical_to_explicit_night(
    themes: dict[str, dict[str, str]],
) -> None:
    # Automatic = prefers-color-scheme: dark, which must give exactly the Night tokens.
    colors = {k: v for k, v in themes["night"].items() if not k.startswith("on-")}
    for name, value in colors.items():
        assert themes["automatic-dark"].get(name) == value, name
    assert set(themes["night"]) == set(themes["automatic-dark"])


def test_night_defines_everything_day_does_for_color(themes: dict[str, dict[str, str]]) -> None:
    color_tokens = {k for k, v in themes["day"].items() if v.startswith(("#", "rgb"))}
    missing = color_tokens - set(themes["night"])
    assert missing == set()


def test_type_scale_and_motion_tokens(themes: dict[str, dict[str, str]]) -> None:
    day = themes["day"]
    assert day["fs-problem"] == "1.125rem"  # 18 px at the default 16 px root
    assert day["lh-problem"] == "1.6"
    assert day["math-scale"] == "1.05"
    assert day["text-size"] == "18"
    assert day["dur"] == "120ms"
    assert int(day["dur"].removesuffix("ms")) <= 150
    assert "Source Serif 4" in day["font-text"]
    assert "Inter" in day["font-ui"]
    # An 8 px spacing grid.
    for name in ("sp-1", "sp-2", "sp-3", "sp-4", "sp-5", "sp-6", "sp-8"):
        assert int(day[name].removesuffix("px")) % 8 == 0, name


def test_reduced_motion_is_respected() -> None:
    base = BASE_CSS.read_text()
    block = block_after(base, "@media (prefers-reduced-motion: reduce)")
    assert "--dur: 0ms" in block
    assert "transition-duration" in block
    assert "animation-duration" in block


def test_increase_contrast_is_respected() -> None:
    assert "prefers-contrast: more" in TOKENS_CSS.read_text()


def test_every_var_used_is_defined() -> None:
    defined = set(declarations(TOKENS_CSS.read_text()))
    for path in SRC.rglob("*"):
        if path.suffix in {".svelte", ".css", ".ts"}:
            defined |= set(re.findall(r"(?<![\w-])--([\w-]+)\s*:", path.read_text()))
    used: dict[str, Path] = {}
    for path in SRC.rglob("*"):
        if path.suffix in {".svelte", ".css"}:
            for name in re.findall(r"var\(--([\w-]+)", path.read_text()):
                used.setdefault(name, path)
    undefined = {n: p.name for n, p in used.items() if n not in defined}
    assert undefined == {}
