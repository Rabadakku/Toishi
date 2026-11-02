"""Make pywebview's JS bridge work under our CSP, which has no 'unsafe-eval' (ADR-0002).

pywebview 6.2.1 builds each `window.pywebview.api.<name>` stub with `new Function(...)`
(webview/js/api.js) and sends every return value back through `Window.evaluate_js`,
which wraps the script in `eval(...)`. WebKit applies the page's CSP to both in the
page world, so with a strict CSP the stubs are never created and promises never
resolve. app.shell applies the two eval-free replacements below.

These are exact-text patches against the pinned pywebview version. They raise
PywebviewCompatError if pywebview changes, so an upgrade cannot silently break
the bridge. No pywebview import here: the helpers are tested on Linux.
"""

PYWEBVIEW_VERSION = "6.2.1"

# webview/js/api.js, inside _createApi(): the only dynamic-code site in pywebview's JS.
API_STUB_ORIGINAL = """      nestedObject[functionName] = new Function(
        sanitize_params(params),
        funcBody
      );"""

# Same behaviour as the generated function body, written as a closure.
API_STUB_PATCHED = """      nestedObject[functionName] = (function (name) {
        return function () {
          var __id = (Math.random() + '').substring(2);
          var promise = new Promise(function (resolve, reject) {
            window.pywebview._checkValue(name, resolve, reject, __id);
          });
          window.pywebview._jsApiCallback(name, Array.prototype.slice.call(arguments), __id);
          return promise;
        };
      })(funcName);"""

# webview/util.py js_bridge_call() delivers results with evaluate_js(<this prefix>...).
BRIDGE_RETURN_PREFIX = 'window.pywebview._returnValuesCallbacks["'


class PywebviewCompatError(RuntimeError):
    """pywebview is not the version these patches were written and verified for."""


def check_version(found: str) -> None:
    if found != PYWEBVIEW_VERSION:
        raise PywebviewCompatError(
            f"pywebview {found} installed, CSP patches verified for {PYWEBVIEW_VERSION}. "
            "Re-check app/csp_compat.py against the new webview/js/api.js and util.py "
            "(ADR-0002) before bumping the pin."
        )


def patch_bridge_js(js_code: str) -> str:
    """Replace the `new Function` stub factory in pywebview's injected JS."""
    count = js_code.count(API_STUB_ORIGINAL)
    if count != 1:
        raise PywebviewCompatError(f"expected the api.js stub factory once, found it {count} times")
    return js_code.replace(API_STUB_ORIGINAL, API_STUB_PATCHED)


def is_bridge_return(script: str) -> bool:
    """True for the script pywebview runs to resolve a JS promise with a Python result."""
    return script.startswith(BRIDGE_RETURN_PREFIX)
