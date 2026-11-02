"""content-tools/similarity_check.py: flags close copies, passes independent problems, never
prints source text. All texts here are made up for the test."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "similarity_check", ROOT / "content-tools" / "similarity_check.py"
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses look the module up
    spec.loader.exec_module(mod)
    return mod


sim = _load()

SOURCE = (
    "A cylindrical water tank of radius 3 meters is being filled at a rate of 7 cubic meters "
    "per minute. How fast is the water level rising when the water is 5 meters deep? "
    "Solution: the volume is pi r squared h, so dV/dt equals 9 pi dh/dt and dh/dt is 7 over 9 pi."
)


def card(
    card_id: str, question: str, solution: str = "0. [calc1.rates] Set up: relate rates."
) -> str:
    return (
        f"## Card {card_id}\n\nskill: calc1.rates\nanswer-type: number\nanswer: 1\n\n"
        f"### Question\n\n{question}\n\n### Solution\n\n{solution}\n\n"
    )


@pytest.fixture
def folders(tmp_path: Path) -> tuple[Path, Path]:
    sources = tmp_path / "sources"
    (sources / "book").mkdir(parents=True)
    (sources / "book" / "p17.txt").write_text(SOURCE)
    (sources / "book" / "p18.txt").write_text("Differentiate the function g of x equals x cubed.")
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    return sources, drafts


def run(folders: tuple[Path, Path], *extra: str) -> int:
    sources, drafts = folders
    return int(sim.main(["--sources", str(sources), "--drafts", str(drafts), *extra]))


def test_a_reworded_copy_with_swapped_numbers_is_flagged(
    folders: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    near = (
        "A cylindrical water tank of radius 4 meters is being filled at a rate of 6 cubic meters "
        "per minute. How fast is the water level rising when the water is 2 meters deep?"
    )
    (folders[1] / "rates.md").write_text(card("calc1.rates.001", near))
    assert run(folders) == 1
    out = capsys.readouterr().out
    assert "FLAG calc1.rates.001 (rates.md) ~ book/p17.txt" in out
    assert "cylindrical" not in out  # never echoes any text


def test_the_same_numbers_in_new_words_are_flagged(folders: tuple[Path, Path]) -> None:
    same_numbers = (
        "Sand pours into a round pit 3 m wide at 7 m^3/min; find the rise rate at depth 5 m."
    )
    (folders[1] / "rates.md").write_text(card("calc1.rates.002", same_numbers))
    assert run(folders, "--json") == 1


def test_an_independent_problem_passes(folders: tuple[Path, Path]) -> None:
    fresh = (
        "Air is pumped into a spherical balloon at 40 cm^3/s. How fast does the radius grow "
        "when the diameter is 30 cm?"
    )
    (folders[1] / "rates.md").write_text(card("calc1.rates.003", fresh))
    assert run(folders) == 0


def test_a_copied_solution_is_flagged_even_with_a_new_question(folders: tuple[Path, Path]) -> None:
    copied = (
        "0. [calc1.rates] Set up: the volume is pi r squared h, so dV/dt equals 9 pi dh/dt "
        "and dh/dt is 7 over 9 pi."
    )
    (folders[1] / "rates.md").write_text(card("calc1.rates.004", "A new tank question.", copied))
    assert run(folders) == 1


def test_json_output_names_only_ids_files_and_scores(
    folders: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    (folders[1] / "rates.md").write_text(card("calc1.rates.005", SOURCE))
    assert run(folders, "--json") == 1
    (flag,) = json.loads(capsys.readouterr().out)
    assert set(flag) == {
        "card",
        "draft_file",
        "source",
        "containment",
        "longest_run",
        "same_numbers",
    }
    assert flag["containment"] >= 0.3


def test_bad_folders_are_an_input_error(tmp_path: Path) -> None:
    assert sim.main(["--sources", str(tmp_path / "nope"), "--drafts", str(tmp_path)]) == 2
