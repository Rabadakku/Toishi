"""Child process for test_close_race.py: close storage while another thread reads.

Before the fix, Database.close() closed every thread's read connection, including one
another thread was running a query on: a use-after-free that killed the interpreter
("Fatal Python error: Segmentation fault" in the auto-fit thread). A segfault can't be
caught in-process, so the loops run here and the test checks the exit code.

usage: python -m tests.storage.close_race_child (reader|autofit) <root> <rounds>
"""

import sys
import tempfile
import threading
from pathlib import Path

from core.storage import Storage, StorageError
from core.storage.profiles import ProfilePaths


def reader_round(root: Path, pack: Path) -> str:
    from tests.storage import data

    storage = Storage.open(
        ProfilePaths(root), pack_paths=[pack], clock=data.new_clock(), create=True
    )
    started = threading.Event()
    outcome: list[str] = []

    def read_forever() -> None:
        try:
            while True:
                started.set()
                storage.packs.sections()
                storage.packs.skills()
        except StorageError:
            outcome.append("refused")
        except BaseException as error:  # anything but a clean refusal is a failure
            outcome.append(f"{type(error).__name__}: {error}")

    thread = threading.Thread(target=read_forever, name="reader")
    thread.start()
    started.wait(5)
    storage.close(backup=False)
    thread.join(10)
    return outcome[0] if outcome else "hung"


def autofit_round(root: Path) -> str:
    from tests.queue.helpers import make_world

    world = make_world(root, ("ca",), sections=2, skills=3, state="solid")
    svc = world.service()
    svc.start_auto_fit()
    world.storage.close(backup=False)  # at once, while the fit reads the catalog
    if not svc.wait_for_auto_fit(10):
        return "hung"
    result = svc.last_auto_fit
    if isinstance(result, (StorageError, list)):
        return "ok"
    return f"{type(result).__name__}: {result}"


def main() -> int:
    mode, base, rounds = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    bad: list[str] = []
    if mode == "reader":
        from core.storage import build_pack
        from tests.storage import data

        pack = base / "pack.db"
        build_pack(pack, data.PACK_INFO, data.pack_records())
    for i in range(rounds):
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            root = Path(tmp)
            got = reader_round(root / "p", pack) if mode == "reader" else autofit_round(root)
        if got not in ("ok", "refused"):
            bad.append(f"round {i}: {got}")
    print("\n".join(bad) if bad else "clean")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
