"""The Library flags a skill whose learning pool is too small (hand test item 3, ENG-2)."""

from app.api import Api
from core.engine import Engine


def test_library_names_the_skills_whose_pool_is_too_small(studying: Api) -> None:
    store = studying._store()
    small = Engine(store).small_learning_pools()
    assert small  # the Test pack has one- and two-problem skills
    names = {s.id: s.name for s in store.packs.skills()}
    flagged = {
        name
        for course in studying.library_get()["courses"]
        for unit in course["units"]
        for section in unit["sections"]
        for name in section["small_pool_skills"]
    }
    assert flagged == {names[k] for k in small}
