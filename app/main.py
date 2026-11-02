"""App entry point: `uv run python -m app [--self-test]` or the built .app.

Lifecycle: app/__main__.py calls multiprocessing.freeze_support() first (the answer
checker's worker is a spawned process). Then main() opens the profile used last (first
run: the page asks for a name), attaches the shipped packs, warms up the checker in the
background and runs the window. On exit it closes the profile (on-close backup, best
effort: Cmd+Q can end the process before this runs, which is fine because every answer
is committed when it is graded) and stops the checker and card-import workers.
"""

import argparse
import json
import os
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import core
from app import packs, shell
from app.api import Api, SelfTestInbox
from app.media import ProfileMedia
from app.paths import index_html
from core import cards, grader
from core.health import health_check
from core.storage import ProfileManager

DEBUG_ENV = "TOISHI_DEBUG"  # 1 = Web Inspector, dev runs only
LAUNCH_T0_ENV = "TOISHI_LAUNCH_T0"  # epoch seconds set by scripts/spike_measure.py
SELF_TEST_PREFIX = "SELFTEST "
UNDO_ANSWER_EVENT = "undo-answer"  # Edit > Undo Last Answer (QUE-15); the page acts on it


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def debug_enabled(env: Mapping[str, str], frozen: bool) -> bool:
    """Web Inspector only for dev runs that ask for it, never in a built .app.

    pywebview's debug mode puts the title over the traffic lights on macOS 26 (#1866).
    """
    return not frozen and env.get(DEBUG_ENV) == "1"


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="toishi", description=core.APP_NAME)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="study a few answers through the bridge in a temporary profile, then open the "
        "window and check page + bridge + core; print one SELFTEST line, exit 0/1",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="with --self-test: skip the window (the bridge and core checks only)",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="check the Python stack only (no window), print one HEALTH line, exit 0/1",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="self-test timeout (s)")
    parser.add_argument(
        "--hidden", action="store_true", help="self-test without showing the window"
    )
    return parser.parse_args(argv)


def _undo_last_answer(window: shell.ShellWindow) -> None:
    window.send_page_event(UNDO_ANSWER_EVENT)


def _launch_ms(env: Mapping[str, str]) -> float | None:
    raw = env.get(LAUNCH_T0_ENV)
    if not raw:
        return None
    try:
        return round((time.time() - float(raw)) * 1000, 1)
    except ValueError:
        return None


def self_test_result(
    page: dict[str, Any] | None,
    core_report: dict[str, object],
    timings: dict[str, float | None],
    study: dict[str, Any] | None = None,
    *,
    window: bool = True,
) -> dict[str, Any]:
    page_ok = bool(page and page.get("ok") is True) or not window
    study_ok = study is None or study.get("ok") is True
    result: dict[str, Any] = {
        "ok": page_ok and study_ok and core_report.get("ok") is True,
        "shell": shell.SHELL_NAME,
        "core": core_report,
        "timings": timings,
    }
    if window:
        result["page"] = (
            page if page is not None else {"ok": False, "error": "no report from the page"}
        )
    if study is not None:
        result["study"] = study
    return result


def _key_answers(card: Any) -> list[dict[str, Any]]:
    """What a student who knows the answer types (the key; the first text alternative)."""

    def key(answer_type: str, answer: str | None) -> str:
        text = answer or ""
        return text.split(";")[0].strip() if answer_type == "text" else text

    if card.parts:
        return [{"part": p.label, "value": key(p.answer_type, p.answer)} for p in card.parts]
    return [{"part": None, "value": key(card.answer_type, card.answer)}]


def study_self_test(pack_paths: Callable[[], Sequence[Path]]) -> dict[str, Any]:
    """Through the bridge, in a temporary data folder: create a profile, attach the Test
    pack, switch a section on, start a session, answer one problem right and one wrong,
    undo the wrong one. Every step is a call the page makes."""
    steps: list[dict[str, Any]] = []

    def step(name: str, ok: bool, detail: str = "") -> None:
        steps.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    with tempfile.TemporaryDirectory(prefix="mastery-selftest-") as tmp:
        api = Api(profiles=ProfileManager(Path(tmp)), pack_paths=pack_paths)
        try:
            created = api.profile_create({"name": "Self-test"})
            step("profile", created["profile"] is not None, str(created["error"] or ""))
            courses = api.library_get()["courses"]
            sections = [s for c in courses for u in c["units"] for s in u["sections"]]
            step("pack attached", bool(sections), f"{len(sections)} sections")
            api.library_set_state({"id": sections[0]["id"], "state": "learning"})
            today = api.study_today()
            step("today", today["problems"] > 0, f"{today['problems']} problems")
            turn = api.study_start({"mode": "daily"})
            step("start", turn["type"] == "problem", str(turn.get("message")))
            answered: list[str] = []
            for _ in range(40):
                if turn["type"] != "problem" or len(answered) == 2:
                    break
                problem = turn["problem"]
                key = problem["item_key"]
                if problem["kind"] == "example":
                    turn = api.study_next({"item_key": key})
                    continue
                if problem["kind"] == "flashcard":
                    api.study_rate_flashcard({"item_key": key, "rating": 3})
                    turn = api.study_next({"item_key": key})
                    continue
                card = api._store().packs.card(problem["card"]["id"])
                if card is None or problem["card"]["self_graded"]:
                    api.study_give_up({"item_key": key, "timing": {"active_ms": 1000}})
                    turn = api.study_next({"item_key": key})
                    continue
                timing = {"active_ms": 4000, "solve_ms": 3000, "entry_ms": 900}
                if not answered:
                    result = api.study_submit(
                        {"item_key": key, "answers": _key_answers(card), "timing": timing}
                    )
                    step("correct answer", result["outcome"] == "correct", result["outcome"])
                    answered.append(key)
                    turn = api.study_next({"item_key": key})
                    continue
                wrong = [{**a, "value": "987654321"} for a in _key_answers(card)]
                result = {"outcome": "retry"}
                for _try in range(problem["attempts_allowed"]):
                    result = api.study_submit({"item_key": key, "answers": wrong, "timing": timing})
                    if result["outcome"] != "retry":
                        break
                if result["outcome"] == "invalid":
                    result = api.study_give_up({"item_key": key, "timing": timing})
                step("wrong answer", result["outcome"] == "incorrect", result["outcome"])
                answered.append(key)
                undone = api.study_undo()
                back = undone.get("problem") or {}
                step(
                    "undo",
                    back.get("item_key") == key and undone.get("result") is None,
                    str(undone.get("message")),
                )
            step("answered two", len(answered) == 2, f"{len(answered)} answered")
            summary = api.study_end()
            step("summary", summary["correct"] >= 1, f"{summary['correct']} correct")
        except Exception as error:  # reported, not raised: the self-test prints one line
            if not steps or steps[-1]["ok"]:
                steps.append({"name": "error", "ok": False, "detail": repr(error)})
        finally:
            api._close(backup=False)
    return {"ok": all(s["ok"] for s in steps) and bool(steps), "steps": steps}


def _test_pack_only() -> Sequence[Path]:
    return [p for p in packs.shipped_packs() if p.stem == "test"]


def shutdown(api: Api) -> None:
    """Close the profile (on-close backup, best effort), then stop the worker processes."""
    try:
        api._close(backup=True)
    finally:
        grader.shutdown()
        cards.shutdown()


def _print_self_test(result: dict[str, Any]) -> int:
    print(SELF_TEST_PREFIX + json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["ok"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    started = time.perf_counter()
    args = parse_args(argv)
    if args.health:
        report = health_check()
        print("HEALTH " + json.dumps(report.as_dict(), sort_keys=True), flush=True)
        return 0 if report.ok else 1
    if args.self_test and args.no_window:
        try:
            study = study_self_test(_test_pack_only)
        finally:
            grader.shutdown()
            cards.shutdown()
        timings: dict[str, float | None] = {
            "main_to_report_ms": round((time.perf_counter() - started) * 1000, 1)
        }
        return _print_self_test(
            self_test_result(None, health_check().as_dict(), timings, study, window=False)
        )
    entry = index_html()
    if not entry.is_file():
        print(
            f"error: the web UI is not built ({entry} is missing).\n"
            "Run: npm --prefix web ci && npm --prefix web run build",
            file=sys.stderr,
        )
        return 2

    inbox = SelfTestInbox() if args.self_test else None
    spec = shell.WindowSpec(
        title=core.APP_NAME,
        entry=entry,
        hidden=args.hidden,
        focus=not args.self_test,  # don't steal keyboard focus during a smoke test
        debug=debug_enabled(os.environ, is_frozen()),
        # No app_menu: pywebview's default app menu already starts with "About <app>" (the
        # standard panel, which shows the bundle's name and version); adding ours made it twice.
        edit_menu=(shell.MenuItem("Undo Last Answer", _undo_last_answer),),
    )
    if inbox is None:
        api = Api(profiles=ProfileManager(), pack_paths=packs.shipped_packs)
        # Start the checker's worker now so the first answer isn't slow (it imports SymPy).
        threading.Thread(target=grader.warm_up, name="grader-warm-up", daemon=True).start()
        api._open_last()
        try:
            shell.run(spec, api, media=ProfileMedia(api._storage_or_none))
        finally:
            shutdown(api)
        return 0

    study = study_self_test(_test_pack_only)
    api = Api(self_test=inbox)
    result: dict[str, Any] = {}

    def drive(window: shell.ShellWindow) -> None:
        page = inbox.wait(args.timeout)
        timings = {
            "launch_to_report_ms": _launch_ms(os.environ),
            "main_to_report_ms": round((time.perf_counter() - started) * 1000, 1),
        }
        result.update(self_test_result(page, health_check().as_dict(), timings, study))
        window.destroy()

    def give_up() -> None:
        print("SELFTEST: GUI loop did not exit; aborting", file=sys.stderr, flush=True)
        os._exit(3)

    # If the GUI loop never returns, still exit (with failure) instead of hanging.
    watchdog = threading.Timer(args.timeout + 20, give_up)
    watchdog.daemon = True
    watchdog.start()
    try:
        shell.run(spec, api, on_started=drive)
    finally:
        watchdog.cancel()
        grader.shutdown()
        cards.shutdown()

    if not result:
        result = self_test_result(None, {"ok": False}, {}, study)
    return _print_self_test(result)
