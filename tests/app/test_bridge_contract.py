"""The bridge contract: web/src/lib/types.ts mirrors what app/api.py sends and accepts.

Static: each payload interface in types.ts has exactly the fields of its core dataclass.
Live: the dicts a real session returns have exactly the fields types.ts declares.

Wave 2 (docs/design/wave2-integration.md section 6) changes the study payloads on both sides
of the bridge: the Python side here (W1), types.ts with the pages (W2, merged on its own).
Until types.ts declares the wave 2 views, the payloads wave 2 changed cannot match it: those
checks are expected failures, strictly, keyed on types.ts itself, so they turn back into
plain checks the moment the page side is merged (and must then pass).
"""

import dataclasses
import re
from pathlib import Path
from typing import Any

import pytest

from app.api import Api
from core import grader
from core.queue import guards
from core.queue import views as v

TYPES = (Path(__file__).parents[2] / "web/src/lib/types.ts").read_text()
WAVE2_PAGES = "export interface SittingView" in TYPES  # the page side of wave 2 is merged
pages_pending = pytest.mark.xfail(
    not WAVE2_PAGES,
    reason="wave 2 study payloads: web/src/lib/types.ts (W2) is not merged yet",
    strict=True,
)


def ts_fields(name: str) -> set[str]:
    match = re.search(rf"^export interface {name} \{{(.*?)^\}}", TYPES, re.MULTILINE | re.DOTALL)
    assert match, f"types.ts has no interface {name}"
    return set(re.findall(r"^  (\w+)\??:", match.group(1), re.MULTILINE))


def py_fields(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


MIRRORED: dict[str, type] = {
    "Reason": v.Reason,
    "ChoiceView": v.ChoiceView,
    "PartView": v.PartView,
    "StepView": v.StepView,
    "CardView": v.CardView,
    "ProblemView": v.ProblemView,
    "Textbook": v.TextbookView,
    "SittingView": v.SittingView,
    "Progress": v.Progress,
    "PartVerdictView": v.PartVerdictView,
    "SolutionView": v.SolutionView,
    "FindErrorView": v.FindErrorView,
    "AttemptResult": v.AttemptResult,
    "FlagResult": v.FlagResult,
    "Tick": v.Tick,
    "CourseLine": v.CourseLine,
    "Forecast": v.Forecast,
    "ExamLine": v.ExamLine,
    "PlannedSitting": v.SittingLine,
    "TodayView": v.TodayView,
    "MissLine": v.MissLine,
    "TestLine": v.TestLine,
    "TestResult": v.TestResult,
    "Summary": v.Summary,
    "Turn": v.Turn,
    "TimingReport": guards.TimingReport,
    "AnswerPreview": grader.Preview,
    "PartAnswer": v.PartAnswer,
    "SubmitRequest": v.SubmitRequest,
    "StartRequest": v.StartRequest,
}
# The payloads wave 2 changed (or added): their mirror waits for the page side.
WAVE2: frozenset[str] = frozenset(
    {
        "CardView",
        "ProblemView",
        "Textbook",
        "SittingView",
        "SolutionView",
        "AttemptResult",
        "PlannedSitting",
        "TodayView",
        "Turn",
        "StartRequest",
    }
)


@pytest.mark.parametrize(
    "name",
    [pytest.param(n, marks=pages_pending) if n in WAVE2 else n for n in sorted(MIRRORED)],
)
def test_types_ts_mirrors_the_core_payload(name: str) -> None:
    assert ts_fields(name) == py_fields(MIRRORED[name])


def check(payload: Any, name: str) -> None:
    assert isinstance(payload, dict), (name, payload)
    assert set(payload) == ts_fields(name), name


@pages_pending
def test_a_live_session_sends_exactly_the_declared_fields(studying: Api) -> None:
    check(studying.profile_get(), "ProfileState")
    library = studying.library_get()
    check(library, "Library")
    check(library["courses"][0], "LibraryCourse")
    check(library["courses"][0]["units"][0], "LibraryUnit")
    check(library["courses"][0]["units"][0]["sections"][0], "LibrarySection")
    check(studying.prefs_get(), "Preferences")
    today = studying.study_today()
    check(today, "TodayView")
    for sitting in today["sittings"]:
        check(sitting, "PlannedSitting")
    check(studying.study_forecast(), "Forecast")

    turn = studying.study_start({"mode": "daily"})
    check(turn, "Turn")
    seen: set[str] = set()
    for _ in range(30):
        if turn["type"] != "problem":
            break
        problem = turn["problem"]
        check(problem, "ProblemView")
        check(problem["card"], "CardView")
        check(problem["reason"], "Reason")
        check(turn["progress"], "Progress")
        if problem["textbook"] is not None:
            check(problem["textbook"], "Textbook")
            seen.add("textbook")
        key = problem["item_key"]
        if problem["kind"] == "flashcard":
            check(studying.study_rate_flashcard({"item_key": key, "rating": 3}), "AttemptResult")
        elif problem["kind"] == "problem" and problem["card"]["parts"][0]["answer_type"] != "self":
            part = problem["card"]["parts"][0]
            check(
                studying.study_read_answer({"item_key": key, "part": part["label"], "value": "2"}),
                "AnswerPreview",
            )
            check(studying.study_tick({"item_key": key, "active_ms": 500, "draft": "x"}), "Tick")
            if "retry" not in seen:
                tried = studying.study_submit(
                    {"item_key": key, "answers": [{"part": part["label"], "value": "987654321"}]}
                )
                check(tried, "AttemptResult")
                for verdict in tried["verdicts"]:
                    check(verdict, "PartVerdictView")
                if tried["outcome"] == "retry":
                    seen.add("retry")
            result = studying.study_give_up({"item_key": key, "timing": {"active_ms": 900}})
            check(result, "AttemptResult")
            check(result["solution"], "SolutionView")
            for step in result["solution"]["steps"]:
                check(step, "StepView")
            if "flag" not in seen:
                check(studying.study_flag({"item_key": key, "kind": "report"}), "FlagResult")
                seen.add("flag")
        turn = studying.study_next({"item_key": key})
        check(turn, "Turn")
    summary = studying.study_end() if turn["type"] == "problem" else turn["summary"]
    check(summary, "Summary")
    check(summary["forecast"], "Forecast")
    for miss in summary["misses"]:
        check(miss, "MissLine")
    assert {"retry", "textbook", "flag"} <= seen
