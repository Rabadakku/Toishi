"""An imported Anki cloze's back shows its answer as Anki does, not as literal `**x**`."""

from collections.abc import Callable

from playwright.sync_api import expect

from tests.ui.test_anki_cards import Studied, decks, studying

__all__ = ["decks", "studying"]  # the fixtures, shared with test_anki_cards


def test_an_imported_cloze_back_has_no_markdown_asterisks(
    studying: Callable[..., Studied],
) -> None:
    s = studying("cloze")
    s.open()
    back = s.reveal()
    expect(back.locator(".cloze").first).to_be_visible()  # the answer, styled by the note type
    expect(back).not_to_contain_text("**")  # the Mac showed "**Paris**"
    s.assert_clean()
