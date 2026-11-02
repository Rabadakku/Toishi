"""The built page with the REAL core: a damaged profile opens the restore screen (BAK-4),
which restores it in two clicks (BAK-3); and files dropped on the page are ignored (ARC-12).
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import expect

from app.api import Api
from app.packs import shipped_packs
from core import cards, grader
from core.storage import ProfileManager
from tests.app.harness import BridgeHarness, shim_script
from tests.app.test_restore import smash, snapshot, study_some
from tests.ui.conftest import Guarded, LocalServer


@pytest.fixture
def damaged(tmp_path: Path) -> Iterator[tuple[Api, Path, dict[str, Any]]]:
    """Sam's profile with answers and its on-close backup; then user.db is smashed."""
    packs = [p for p in shipped_packs() if p.stem == "test"]
    data = tmp_path / "data"
    first = Api(profiles=ProfileManager(data), pack_paths=lambda: packs)
    first.profile_create({"name": "Sam"})
    section = first.library_get()["courses"][0]["units"][0]["sections"][0]
    first.library_set_state({"id": section["id"], "state": "learning"})
    study_some(first)
    db = first._store().paths.user_db
    first._close(backup=True)
    before = snapshot(db)
    smash(db)
    api = Api(profiles=ProfileManager(data), pack_paths=lambda: packs)
    api._open_last()
    try:
        yield api, db, before
    finally:
        api._close(backup=False)
        grader.shutdown()
        cards.shutdown()


def test_a_damaged_profile_is_restored_from_the_restore_screen(
    damaged: tuple[Api, Path, dict[str, Any]], web_dist: Path, guarded: Guarded
) -> None:
    api, db, before = damaged
    harness = BridgeHarness(web_dist, api)
    page = guarded.page
    page.context.add_init_script(shim_script())
    try:
        page.goto(f"{harness.origin}/index.html")
        expect(page.get_by_test_id("page-restore")).to_be_visible()
        expect(page.get_by_test_id("page-welcome")).to_have_count(0)  # no new profile
        expect(page.get_by_test_id("restore-problem")).to_contain_text("integrity check")
        expect(page.get_by_test_id("restore-backup")).to_have_count(1)
        page.get_by_test_id("restore-choose").first.click()  # click 1: choose (preview)
        page.get_by_test_id("restore-confirm").click()  # click 2: restore
        expect(page.get_by_test_id("page-home")).to_be_visible()
        assert snapshot(db) == before
        assert "profile_create" not in harness.calls
        guarded.assert_clean()
    finally:
        harness.close()


DROP = """
(types) => {
  const data = new DataTransfer();
  if (types.includes('Files')) data.items.add(new File(['x'], 'user.db'));
  if (types.includes('text/uri-list')) data.setData('text/uri-list', 'https://example.com/');
  if (types.includes('text/plain')) data.setData('text/plain', 'x^2');
  const target = document.querySelector('main') ?? document.body;
  const results = {};
  for (const type of ['dragover', 'drop']) {
    const event = new DragEvent(type, {dataTransfer: data, bubbles: true, cancelable: true});
    target.dispatchEvent(event);
    results[type] = event.defaultPrevented;
  }
  return results;
}
"""


def test_files_and_links_dropped_on_the_page_are_ignored(
    server: LocalServer, guarded: Guarded
) -> None:
    page = guarded.page
    page.goto(f"{server.origin}/index.html?bridge=mock")
    expect(page.locator("main")).to_be_visible()
    for types in (["Files"], ["text/uri-list"], ["Files", "text/plain"]):
        assert page.evaluate(DROP, types) == {"dragover": True, "drop": True}, types
    # Text dragged into an answer box is the page's business: not cancelled here.
    assert page.evaluate(DROP, ["text/plain"]) == {"dragover": False, "drop": False}
    assert page.url == f"{server.origin}/index.html?bridge=mock"
    guarded.assert_clean()
