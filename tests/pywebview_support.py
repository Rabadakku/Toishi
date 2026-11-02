"""Helpers that reproduce what pywebview 6.2.1 does on Cocoa, without Cocoa."""

import inspect
import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import webview.util


def load_pywebview_js() -> tuple[str, str]:
    """The JS pywebview injects (js_code) and the finish script, as on macOS."""
    stand_in = SimpleNamespace(
        uid="test",
        js_api_endpoint=None,
        text_select=True,
        zoomable=False,
        draggable=False,
        easy_drag=False,
        frameless=False,
        state={},
    )
    load: Callable[..., Any] = webview.util.load_js_files  # really returns a tuple
    js_code, finish = load(stand_in, "cocoa")
    return str(js_code), str(finish)


def finish_script(finish: str, api: object) -> str:
    """finish.js filled with the exposed functions, like util.inject_pywebview."""
    functions = [
        {"func": name, "params": inspect.getfullargspec(member).args[1:]}
        for name, member in inspect.getmembers(api, inspect.ismethod)
        if not name.startswith("_")
    ]
    return finish % {"functions": json.dumps(functions)}
