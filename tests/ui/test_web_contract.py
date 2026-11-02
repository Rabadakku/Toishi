"""The payload types of the Python bridge, as the page declares them (web/src/lib/types.ts)."""

import re
from pathlib import Path

WEB = Path(__file__).parents[2] / "web/src/lib"
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
    "HintReveal",
    "Summary",
    "Turn",
    "TodayView",
    "TimingReport",
    "ProfileState",
    "Library",
]


def exported_names() -> list[str]:
    return re.findall(r"^export (?:interface|type) (\w+)", TYPES, re.MULTILINE)


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
