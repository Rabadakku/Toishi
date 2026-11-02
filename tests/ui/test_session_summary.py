"""SessionSummary with the real core (hand test item 5): more learning problems ready today,
and "To revisit" grouped by skill."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import expect

from app.api import Api
from core import cards, grader
from core.model import Card, Course, PackInfo, Section, Skill, SolutionStep, Unit
from core.storage import ProfileManager, build_pack
from tests.app.harness import BridgeHarness, shim_script
from tests.ui.conftest import Guarded


def _pack(path: Path) -> Path:
    """One new skill with a worked example and eight tier 1-2 problems (answer: 1)."""
    records: list[object] = [
        Course(id="tp", title="Tiny", ord=0),
        Unit(id="tp.u1", course_id="tp", title="Unit 1"),
        Section(id="tp.s1", unit_id="tp.u1", title="Section 1", ord=1),
        Skill(id="tp.k1", name="Tiny skill", section_id="tp.s1", exam_tier=3),
        Card(id="tp.k1.ex", kind="example", skill_id="tp.k1", tier=1, question_md="Ex."),
    ]
    for i, tier in enumerate((1, 1, 1, 1, 2, 2, 2, 2)):
        records.append(
            Card(
                id=f"tp.k1.p{i}",
                skill_id="tp.k1",
                tier=tier,
                answer_type="number",
                answer="1",
                question_md=f"Problem {i}: type 1.",
                solution=(SolutionStep(number=1, skill_id="tp.k1", label="Type it"),),
            )
        )
    build_pack(path, PackInfo(id="tiny", title="Tiny", version="1"), records)  # type: ignore[arg-type]
    return path


@pytest.fixture
def api(tmp_path: Path) -> Iterator[Api]:
    pack = _pack(tmp_path / "tiny.db")
    bridge = Api(profiles=ProfileManager(tmp_path / "data"), pack_paths=lambda: [pack])
    bridge.profile_create({"name": "Sam"})
    bridge.library_set_state({"id": "tp.s1", "state": "learning"})
    yield bridge
    bridge._close(backup=False)
    grader.shutdown()
    cards.shutdown()


def test_summary_says_more_is_ready_today_and_groups_misses_by_skill(
    api: Api, web_dist: Path, guarded: Guarded
) -> None:
    # Every learning problem missed through the bridge, the last one left on screen.
    turn = api.study_start({"mode": "daily"})
    timing = {"active_ms": 30_000, "solve_ms": 25_000, "entry_ms": 2_000}
    while True:
        problem = turn["problem"]
        key = problem["item_key"]
        if problem["kind"] == "example":
            turn = api.study_next({"item_key": key})
            continue
        result = {"outcome": "retry"}
        while result["outcome"] == "retry":
            answers = [{"part": None, "value": "0", "source": "text"}]
            result = api.study_submit({"item_key": key, "answers": answers, "timing": timing})
        if turn["progress"]["position"] == turn["progress"]["total"]:
            break  # the last miss is diagnosed on the page
        api.study_diagnose({"item_key": key, "choice": "cant-tell"})
        turn = api.study_next({"item_key": key})
    assert turn["progress"]["position"] >= 2

    harness = BridgeHarness(web_dist, api)
    try:
        page = guarded.page
        page.context.add_init_script(shim_script())
        page.goto(f"{harness.origin}/index.html")
        expect(page.get_by_test_id("start")).to_be_focused()
        page.keyboard.press("Enter")  # resumes on the last verdict
        expect(page.get_by_test_id("verdict")).to_be_visible()
        page.get_by_role("button", name="Can't tell").click()
        page.get_by_test_id("continue").click()
        expect(page.get_by_test_id("summary")).to_be_visible()
        # One line for the skill, however many of its problems were missed (the Mac
        # listed the same skill once per miss).
        expect(page.get_by_test_id("revisit-skill")).to_have_count(1)
        expect(page.get_by_test_id("revisit-skill")).to_contain_text("Tiny skill")
        expect(page.get_by_test_id("revisit-skill")).to_contain_text("missed")
        expect(page.get_by_test_id("summary-missed")).to_have_text("1")
        # The learning phase goes on today (the Mac said only "Tomorrow: ...").
        expect(page.get_by_test_id("ready-today")).to_contain_text("ready today")
        expect(page.get_by_test_id("forecast")).to_contain_text("Tomorrow")
        assert harness.errors == []
    finally:
        harness.close()
