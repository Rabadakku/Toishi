"""The page re-sanitizes imported Anki HTML with the allow-list core used at import
(web/src/lib/anki-html.ts vs core/importers/anki/sanitize.py): the two must not drift."""

import re
from pathlib import Path

from core.importers.anki import sanitize

SOURCE = (Path(__file__).parents[2] / "web/src/lib/anki-html.ts").read_text()


def words(text: str) -> set[str]:
    return set(re.findall(r"'([^']+)'", text))


def ts_set(name: str) -> set[str]:
    match = re.search(rf"export const {name}[^=]*= new Set\(\[(.*?)\]\)", SOURCE, re.DOTALL)
    assert match, f"anki-html.ts has no Set {name}"
    return words(match.group(1))


def ts_tag_attrs() -> dict[str, set[str]]:
    match = re.search(r"export const TAG_ATTRS[^=]*= \{(.*?)^\};", SOURCE, re.DOTALL | re.MULTILINE)
    assert match, "anki-html.ts has no TAG_ATTRS"
    return {
        tag: words(values)
        for tag, values in re.findall(r"^\s+(\w+): \[(.*?)\],?$", match.group(1), re.MULTILINE)
    }


def test_allowed_tags_match_core() -> None:
    assert ts_set("ALLOWED_TAGS") == set(sanitize.ALLOWED_TAGS)


def test_tags_dropped_with_their_content_match_core() -> None:
    assert ts_set("DROP_WITH_CONTENT") == set(sanitize.DROP_WITH_CONTENT)


def test_attributes_match_core() -> None:
    assert ts_set("GLOBAL_ATTRS") == set(sanitize._GLOBAL_ATTRS)
    assert ts_tag_attrs() == {tag: set(attrs) for tag, attrs in sanitize._TAG_ATTRS.items()}


def test_nothing_that_runs_or_navigates_is_allowed() -> None:
    tags, attrs = ts_set("ALLOWED_TAGS"), ts_set("GLOBAL_ATTRS")
    assert not tags & {"script", "style", "iframe", "object", "embed", "svg", "math", "form"}
    assert not attrs & {"id", "href", "srcset", "name", "for"}
    assert not any(
        a.startswith("on") for a in attrs | {x for v in ts_tag_attrs().values() for x in v}
    )
