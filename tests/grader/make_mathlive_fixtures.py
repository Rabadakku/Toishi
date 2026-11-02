"""Regenerate tests/grader/data/mathlive_fixtures.json from the installed MathLive.

Not a test. Run after upgrading MathLive (needs `npm --prefix web ci` and Playwright):

    uv run python -m tests.grader.make_mathlive_fixtures

Each case types real keystrokes into a fresh <math-field> (or sets its LaTeX) in
Chromium and records what the field reports: `latex-unstyled` (what the app sends to
the checker, ADR-0005) plus `ascii-math`, kept to document why we don't use it.
"""

import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
MATHLIVE = ROOT / "web" / "node_modules" / "mathlive"
OUT = Path(__file__).with_name("data") / "mathlive_fixtures.json"

PAGE = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<div id="host"></div>
<script type="module">
import { MathfieldElement } from './mathlive.min.mjs';
MathfieldElement.soundsDirectory = null;
MathfieldElement.fontsDirectory = null;
window.fresh = () => {
  const host = document.getElementById('host');
  host.replaceChildren();
  const mf = new MathfieldElement();
  host.appendChild(mf);
  mf.focus();
  return true;
};
window.setLatex = (s) => { const mf = document.querySelector('math-field'); mf.value = s; };
window.vals = () => {
  const mf = document.querySelector('math-field');
  return {latex: mf.getValue('latex-unstyled'), ascii: mf.getValue('ascii-math')};
};
window.ready = true;
</script></body></html>"""

# (id, keystrokes or None, latex or None). Keystrokes: plain text is typed; {Key} presses.
CASES: list[tuple[str, list[str] | None, str | None]] = [
    ("fraction", ["1/2"], None),
    ("fraction-then-x", ["1/2", "{ArrowRight}", "x"], None),
    ("fraction-of-sum", ["(x+1)/2"], None),
    ("polynomial", ["x^2", "{ArrowRight}", "-4"], None),
    ("factored", ["(x-2)(x+2)"], None),
    ("sqrt", ["sqrt", "x"], None),
    ("sqrt2-over-2", ["sqrt", "2", "{ArrowRight}", "/2"], None),
    ("cube-root", None, r"\sqrt[3]{x}"),
    ("sinx", ["sinx"], None),
    ("sin-paren", ["sin(x)"], None),
    ("sin2x", ["sin2x"], None),
    ("sin-squared", ["sin", "^2", "{ArrowRight}", "x"], None),
    ("sin-paren-squared", ["sin(x)", "{ArrowRight}", "^2"], None),
    ("arcsin", ["arcsin(x)"], None),
    ("sin-inverse", ["sin", "^-1", "{ArrowRight}", "(x)"], None),
    ("e-squared-x", ["e^2", "{ArrowRight}", "x"], None),
    ("e-power-2x", ["e^2x"], None),
    ("ln", ["ln(x)"], None),
    ("two-ln-abs", None, r"2\ln\left|x\right|"),
    ("two-ln-abs-vert", None, r"2\ln\left\vert x\right\vert"),
    ("log-typed", ["log(x)"], None),
    ("log-arrow", ["log", "{ArrowRight}", "(x)"], None),
    ("log2-typed", ["log", "2", "{ArrowRight}", "(x)"], None),
    ("log2", None, r"\log_2\left(x\right)"),
    ("abs", None, r"\left|x-1\right|"),
    ("abs-bars", None, r"|x-1|"),
    ("pi-over-4", ["pi/4"], None),
    ("infinity", ["oo"], None),
    ("minus-infinity", ["-oo"], None),
    ("open-interval", ["(-oo,0)"], None),
    ("union", None, r"(-\infty,0)\cup(2,\infty)"),
    ("half-open", ["[1,2)"], None),
    ("le", ["x<=2"], None),
    ("or", ["x<0 or x>2"], None),
    ("equation", ["y=2x+1"], None),
    ("point", ["(2,-4)"], None),
    ("points", ["(0,0),(2,-4)"], None),
    ("set", ["-1,0,1"], None),
    ("dne", ["DNE"], None),
    ("none", ["none"], None),
    ("vector", None, r"\langle 1,-2,3\rangle"),
    ("matrix", None, r"\begin{bmatrix}1 & 2\\ 3 & 4\end{bmatrix}"),
    ("cdot", None, r"2\cdot x"),
    ("antiderivative", ["x^3", "{ArrowRight}", "/3", "{ArrowRight}", "+C"], None),
    ("exp-frac", None, r"e^{\frac{x}{2}}"),
    ("decimal", ["0.333"], None),
    ("negative-fraction", ["-2/3"], None),
    ("theta", ["theta"], None),
    ("degrees", None, r"30^{\circ}"),
    ("xy", ["xy"], None),
    ("two-pi-x", ["2pix"], None),
    ("mixed-number", None, r"3\frac{1}{2}"),
    ("fraction-times-x", None, r"\frac{1}{2}x"),
    ("sqrt-over-2-times-sin", None, r"\frac{\sqrt{x}}{2}\sin\left(x\right)"),
    ("empty-set", None, r"\emptyset"),
    ("set-braces", None, r"\left\lbrace 1,2\right\rbrace"),
    ("x-sin-x", ["x", "sin(x)"], None),
]


def generate() -> list[dict[str, Any]]:
    site = OUT.parent / "_site"
    site.mkdir(exist_ok=True)
    (site / "index.html").write_text(PAGE)
    (site / "mathlive.min.mjs").write_bytes((MATHLIVE / "mathlive.min.mjs").read_bytes())

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

    handler = functools.partial(Quiet, directory=str(site))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    out: list[dict[str, Any]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html")
            page.wait_for_function("window.ready === true")
            for case_id, keys, latex in CASES:
                page.evaluate("() => window.fresh()")
                page.click("math-field")
                page.wait_for_function("document.activeElement?.tagName === 'MATH-FIELD'")
                page.wait_for_timeout(150)
                if latex is not None:
                    page.evaluate("s => window.setLatex(s)", latex)
                for seg in keys or []:
                    if seg.startswith("{") and seg.endswith("}"):
                        page.keyboard.press(seg[1:-1])
                    else:
                        page.keyboard.type(seg, delay=20)
                values = page.evaluate("() => window.vals()")
                out.append({"id": case_id, "keys": keys, "set": latex, **values})
            browser.close()
    finally:
        server.shutdown()
        for f in site.iterdir():
            f.unlink()
        site.rmdir()
    return out


if __name__ == "__main__":
    fixtures = generate()
    version = json.loads((MATHLIVE / "package.json").read_text())["version"]
    OUT.write_text(json.dumps({"mathlive": version, "cases": fixtures}, indent=1) + "\n")
    print(f"wrote {len(fixtures)} cases to {OUT}")
