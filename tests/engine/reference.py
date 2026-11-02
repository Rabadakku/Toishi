"""The audit's pure-Python FSRS-6 reference (docs/research/reference-code/ref_fsrs6.py),
loaded as a test oracle: it matches fsrs-rs-python to 7e-6 and py-fsrs to 1e-14."""

import importlib.util
from pathlib import Path
from typing import Any

_PATH = Path(__file__).parents[2] / "docs" / "research" / "reference-code" / "ref_fsrs6.py"
_spec = importlib.util.spec_from_file_location("ref_fsrs6", _PATH)
assert _spec is not None
assert _spec.loader is not None
ref_fsrs6: Any = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref_fsrs6)
