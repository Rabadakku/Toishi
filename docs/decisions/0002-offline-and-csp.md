# ADR-0002: Offline at runtime, enforced by CSP and tripwires

- Status: Accepted
- Date: 2026-11-01

## Decision

The app never touches the network at runtime.

1. **Loopback, never `file://`.** pywebview's built-in Bottle server serves `app/web_dist`
   at `http://127.0.0.1:<random port>/` (a local path starts it). `file://` gives an opaque
   origin, which MathLive 0.111.2+ same-origin checks reject, and restricts modules/fonts.
   The JS bridge itself uses WKScriptMessageHandler, not HTTP. (pywebview also mounts a
   `/js_api/<random uid>` POST route used only by other platforms.)
2. **Content-Security-Policy** (meta tag in `web/index.html`; `tests/ui/test_web_dist.py`
   pins the exact text):

   ```
   default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
   font-src 'self'; img-src 'self'; media-src 'self'; connect-src 'self';
   worker-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none';
   form-action 'none'; manifest-src 'none'
   ```

   - `'unsafe-inline'` is **for styles only, and required**: KaTeX writes `style=""`
     attributes on its output, and MathLive inserts `<style>` elements and style attributes
     at runtime. Scripts never get it.
   - **No `'unsafe-eval'`.** Neither KaTeX, MathLive nor Svelte needs it.
   - Fonts and MathLive sounds are bundled files (`assetsInlineLimit: 0`, no `data:` URIs).
   - `frame-ancestors` and `sandbox` cannot be set from a meta tag; nothing frames the page.
3. **pywebview 6.2.1 needed two eval-free patches** (`app/csp_compat.py`, applied by
   `app/shell.py`). Its injected `api.js` builds each `pywebview.api.<name>` with
   `new Function(...)`, and every return value is delivered through `Window.evaluate_js`,
   which wraps the script in `eval(...)`. WebKit applies the page CSP to both in the page
   world, so without the patches the bridge never comes up. The patches (a closure instead
   of `new Function`; `run_js` instead of `evaluate_js` for return values) are exact-text
   and version-checked: any other pywebview version fails at startup until re-verified.
   `tests/ui/test_pywebview_bridge.py` runs pywebview's real JS and Python dispatcher in a
   browser under our CSP and shows the unpatched bridge is blocked and the patched one
   passes the page self-test. The alternative, adding `'unsafe-eval'`, was rejected.
4. **Tripwires.**
   - Python: `tests/offline.py` blocks every non-loopback `connect`/`sendto`/DNS lookup for
     the whole pytest session.
   - Page: Playwright routes every request; anything not to 127.0.0.1 (or data/blob/about)
     is aborted and fails the test, as do CSP violations and console errors.
   - HTML/CSS in `app/web_dist` may only reference relative URLs.
   - Qt spike: `QWebEngineUrlRequestInterceptor` blocks and reports non-local requests.

## Consequences

- pywebview sets `NSAllowsArbitraryLoads` (ATS off); the CSP is the page-level guard. A
  native WKContentRuleList could add a second layer later (not needed for M0).
- Any new web dependency must work under this CSP; widen it only with a new ADR.
