"""Load the golden suite (tests/grader/data/golden_*.toml) into (spec, input, expected) cases."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.grader import AnswerSpec, Choice, parse_wrong_field

DATA = Path(__file__).with_name("data")
EXPECTED = {"correct", "incorrect", "invalid", "undecidable", "unsupported"}


@dataclass(frozen=True)
class Case:
    id: str
    spec: AnswerSpec
    raw: str
    expected: str
    source: str


def spec_from(group: dict[str, Any]) -> AnswerSpec:
    opts = dict(group.get("opts", {}))
    if "vars" in opts:
        opts["vars"] = tuple(opts["vars"])
    if "choices" in opts:
        opts["choices"] = tuple(Choice(text, bool(ok)) for text, ok in opts["choices"])
    if "wrong" in opts:
        opts["wrong"] = parse_wrong_field(opts["wrong"])
    return AnswerSpec(answer_type=group["type"], answer=group.get("key", ""), **opts)


def load_cases() -> list[Case]:
    cases: list[Case] = []
    for path in sorted(DATA.glob("golden_*.toml")):
        data = tomllib.loads(path.read_text())
        for group in data["group"]:
            spec = spec_from(group)
            for c, row in enumerate(group["cases"]):
                raw, expected = row[0], row[1]
                source = row[2] if len(row) > 2 else "text"
                assert expected in EXPECTED, (path.name, group["name"], row)
                case_id = f"{path.stem[7:]}:{group['name']}:{c}:{raw[:40]}"
                cases.append(Case(case_id, spec, raw, expected, source))
    return cases
