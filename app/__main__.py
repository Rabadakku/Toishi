"""`uv run python -m app` in development; also the PyInstaller entry script."""

import multiprocessing
import sys


def _run() -> None:
    # Required before anything else in a frozen app once a worker process exists (SymPy checker).
    multiprocessing.freeze_support()
    from app.main import main

    sys.exit(main())


if __name__ == "__main__":
    _run()
