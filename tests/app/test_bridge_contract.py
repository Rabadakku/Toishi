"""The bridge contract: web/src/lib/types.ts mirrors what app/api.py sends and accepts.

Static: each payload interface in types.ts has exactly the fields of its core dataclass.
Live: the dicts a real session returns have exactly the fields types.ts declares.
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
    "Progress": v.Progress,
    "PartVerdictView": v.PartVerdictView,
    "SolutionView": v.SolutionView,
    "FindErrorView": v.FindErrorView,
    "AttemptResult": v.AttemptResult,
    "HintReveal": v.HintReveal,
    "Diagnosis": v.Diagnosis,
    "FlagResult": v.FlagResult,
    "Tick": v.Tick,
    "CourseLine": v.CourseLine,
    "Forecast": v.Forecast,
    "ExamLine": v.ExamLine,
    "Proposal": v.Proposal,
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


@pytest.mark.parametrize("name", sorted(MIRRORED))
def test_types_ts_mirrors_the_core_payload(name: str) -> None:
    assert ts_fields(name) == py_fields(MIRRORED[name])


def check(payload: Any, name: str) -> None:
    assert isinstance(payload, dict), (name, payload)
    assert set(payload) == ts_fields(name), name


def test_a_live_session_sends_exactly_the_declared_fields(studying: Api) -> None:
    check(studying.profile_get(), "ProfileState")
    library = studying.library_get()
    check(library, "Library")
    check(library["courses"][0], "LibraryCourse")
    check(library["courses"][0]["units"][0], "LibraryUnit")
    check(library["courses"][0]["units"][0]["sections"][0], "LibrarySection")
    check(studying.prefs_get(), "Preferences")
    check(studying.study_today(), "TodayView")
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
            if problem["card"]["hint_count"] and "hint" not in seen:
                check(studying.study_hint({"item_key": key}), "HintReveal")
                seen.add("hint")
            result = studying.study_give_up({"item_key": key, "timing": {"active_ms": 900}})
            check(result, "AttemptResult")
            check(result["solution"], "SolutionView")
            for step in result["solution"]["steps"]:
                check(step, "StepView")
            if "diagnose" not in seen:
                check(
                    studying.study_diagnose({"item_key": key, "choice": "cant-tell"}), "Diagnosis"
                )
                check(studying.study_flag({"item_key": key, "kind": "report"}), "FlagResult")
                seen.add("diagnose")
        turn = studying.study_next({"item_key": key})
        check(turn, "Turn")
    summary = studying.study_end() if turn["type"] == "problem" else turn["summary"]
    check(summary, "Summary")
    check(summary["forecast"], "Forecast")
    for miss in summary["misses"]:
        check(miss, "MissLine")
    assert {"hint", "diagnose"} <= seen
