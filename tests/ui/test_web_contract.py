"""The payload types of the Python bridge, as the page declares them (web/src/lib/types.ts),
and the wave 2 contract's page side (docs/design/wave2-integration.md section 6, with the
resolutions agreed with W1: `plan_reason`, TodayView without proposals and vacation, the
hint and diagnosis fields gone, the sitting's block limit and `block_elapsed_ms`)."""

import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
SRC = ROOT / "web/src"
WEB = SRC / "lib"
TYPES = (WEB / "types.ts").read_text()
PRACTICE_API = (WEB / "practice-api.ts").read_text()
BRIDGE = (WEB / "bridge.ts").read_text()

REQUIRED = [
    "ProblemView",
    "CardView",
    "PartView",
    "StepView",
    "SolutionView",
    "AttemptResult",
    "Progress",
    "AnswerPreview",
    "Summary",
    "Turn",
    "TodayView",
    "TimingReport",
    "ProfileState",
    "Library",
    # wave 2
    "Role",
    "MilestoneName",
    "Textbook",
    "SittingView",
    "ExamIn",
    "Exam",
    "SectionRef",
    "CourseSettings",
    "MilestoneView",
    "SkillRow",
    "SkillsView",
    "Bin",
    "RefitReport",
    "ModelView",
]

WAVE2_METHODS = {
    "course_settings_get",
    "course_settings_set",
    "exam_save",
    "exam_delete",
    "skills_get",
    "model_get",
    "model_refit",
    "model_reset",
}
REMOVED_METHODS = {"study_hint", "study_diagnose", "study_set_lighter"}


def exported_names() -> list[str]:
    return re.findall(r"^export (?:interface|type) (\w+)", TYPES, re.MULTILINE)


def ts_fields(name: str) -> set[str]:
    match = re.search(
        rf"^export interface {name} (?:extends \w+ )?\{{(.*?)^\}}", TYPES, re.MULTILINE | re.DOTALL
    )
    assert match, f"types.ts has no interface {name}"
    return set(re.findall(r"^  (\w+)\??:", match.group(1), re.MULTILINE))


def declared_methods() -> set[str]:
    return set(re.findall(r"^\s+(\w+)\(.*\): Promise<", BRIDGE, re.MULTILINE))


def test_required_payload_types_exist() -> None:
    missing = set(REQUIRED) - set(exported_names())
    assert missing == set()


def test_every_exported_type_is_documented() -> None:
    # Each `export interface/type` must sit directly under a /** ... */ comment.
    for match in re.finditer(r"^export (?:interface|type) (\w+)", TYPES, re.MULTILINE):
        before = TYPES[: match.start()].rstrip()
        assert before.endswith("*/"), f"{match.group(1)} has no doc comment"


def test_payload_fields_are_snake_case() -> None:
    # The bridge is JSON from Python dicts: camelCase fields would never arrive.
    interface_bodies = re.findall(
        r"^export interface \w+ \{(.*?)^\}", TYPES, re.MULTILINE | re.DOTALL
    )
    assert interface_bodies
    for body in interface_bodies:
        for field in re.findall(r"^  (\w+)\??:", body, re.MULTILINE):
            assert field == field.lower(), f"camelCase field {field!r} in types.ts"


def test_study_methods_live_in_the_bridge_api() -> None:
    # tests/test_app.py requires BridgeApi == app.api.Api method for method; the study
    # screen calls the bridge directly (practice-api.ts only picks real or mock).
    study_methods = re.findall(r"^\s+(study_\w+)\(", BRIDGE, re.MULTILINE)
    assert len(study_methods) >= 15
    assert not re.search(r"study_\w+\(", PRACTICE_API)


def test_text_size_range_matches_the_spec() -> None:
    assert "TEXT_SIZE_MIN = 14" in TYPES
    assert "TEXT_SIZE_MAX = 28" in TYPES


def test_the_bridge_has_the_wave2_methods_and_none_of_the_removed_ones() -> None:
    declared = declared_methods()
    assert declared >= WAVE2_METHODS
    assert not declared & REMOVED_METHODS


def test_the_contract_fields_of_the_study_payloads() -> None:
    problem = ts_fields("ProblemView")
    assert {"reason", "role", "plan_reason", "textbook", "sitting"} <= problem
    assert "hints_shown" not in problem
    assert "hint_count" not in ts_fields("CardView")
    assert {"needs_diagnosis", "preselect_step"}.isdisjoint(ts_fields("SolutionView"))
    assert {"can_retry", "first_try_counted"} <= ts_fields("AttemptResult")
    assert ts_fields("SittingView") == {"id", "index", "total", "time_limit_ms", "block_elapsed_ms"}
    assert ts_fields("Textbook") == {"book", "section"}
    for gone in ("HintReveal", "Diagnosis", "DiagnoseRequest", "WentWrongChoice", "Proposal"):
        assert gone not in exported_names()


def test_the_contract_fields_of_home_settings_skills_and_the_model() -> None:
    assert ts_fields("TodayView") == {
        # kept
        "day",
        "problems",
        "minutes",
        "flashcards",
        "courses",
        "exams",
        "session_open",
        "done_today",
        "extra_practice_available",
        "flashcards_to_rewrite",
        # section 6
        "by_role",
        "hours_to_keep_pace",
        "hours_basis",
        "standard_hours",
        "behind",
        "set_aside",
        "sittings",
        "notes",
    }
    assert ts_fields("CourseSettings") == {
        "course_id",
        "course_title",
        "start",
        "aligned",
        "pace_factor",
        "accuracy_target",
        "target_tier",
        "end",
        "keep_target",
        "keep_tier",
        "growth_band",
        "exams",
        "sections",
        "has_pace",
    }
    assert ts_fields("ExamIn") == {
        "exam_id",
        "course_id",
        "name",
        "day",
        "scope_decks",
        "target",
        "minutes",
        "problems",
    }
    assert ts_fields("SectionRef") == {"deck", "title", "hours"}
    assert ts_fields("MilestoneView") == {"name", "tier", "deadline", "certified"}
    assert ts_fields("SkillRow") == {
        "skill_id",
        "name",
        "deck",
        "state",
        "track",
        "intro",
        "milestones",
        "level",
        "readiness",
        "pace_ok",
        "set_aside",
    }
    assert ts_fields("SkillsView") == {"course_id", "day", "skills"}
    assert ts_fields("Bin") == {"label", "n", "predicted", "observed"}
    assert ts_fields("RefitReport") == {"at", "attempts", "adopted", "p_value", "blocks"}
    assert ts_fields("RefitBlock") == {"name", "current", "candidate", "p_value", "adopted"}
    assert ts_fields("ModelView") == {
        "version",
        "source",
        "created_at",
        "params",
        "last_refit",
        "calibration",
        "attempts",
    }
    assert ts_fields("Calibration") == {"by_tier", "by_gap", "by_components"}


def test_the_hint_ladder_and_the_error_picker_are_gone() -> None:
    components = SRC / "components"
    assert not (components / "HintLadder.svelte").exists()
    assert not (components / "WhatWentWrong.svelte").exists()
    for path in SRC.rglob("*"):
        if path.suffix in {".svelte", ".ts"}:
            text = path.read_text()
            assert "HintLadder" not in text, path
            assert "WhatWentWrong" not in text, path


def test_no_page_text_says_mastery() -> None:
    # Wave 2 section 5: plain language, and never the word "mastery" (or "mastered").
    for path in SRC.rglob("*"):
        if path.suffix in {".svelte", ".ts", ".css"}:
            assert "master" not in path.read_text().lower(), path
