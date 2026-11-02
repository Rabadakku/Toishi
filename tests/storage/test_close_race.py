"""Closing storage while another thread reads (the auto-fit segfault, AGENTS rule 6).

Each test loops in a child process (close_race_child.py): a segfault there shows up as
the exit code instead of killing pytest.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def _run(mode: str, root: Path, rounds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tests.storage.close_race_child", mode, str(root), str(rounds)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


@pytest.mark.slow
@pytest.mark.parametrize(("mode", "rounds"), [("reader", 150), ("autofit", 200)])
def test_closing_storage_never_pulls_a_connection_from_under_a_running_read(
    tmp_path: Path, mode: str, rounds: int
) -> None:
    proc = _run(mode, tmp_path, rounds)
    assert proc.returncode == 0, (proc.returncode, proc.stdout[-2000:], proc.stderr[-2000:])
    assert proc.stdout.strip() == "clean"


def test_a_read_after_close_is_refused_not_crashed(tmp_path: Path) -> None:
    import threading

    from core.storage import Storage, StorageError
    from core.storage.profiles import ProfilePaths
    from tests.storage import data

    storage = Storage.open(ProfilePaths(tmp_path / "p"), clock=data.new_clock(), create=True)
    inside = threading.Event()
    release = threading.Event()
    seen: list[object] = []

    def hold_a_read() -> None:
        with storage.db.reading() as conn:
            inside.set()
            release.wait(5)
            seen.append(conn.execute("SELECT 1").fetchone()[0])  # still open: close waits
        try:
            storage.users.settings()
        except StorageError:
            seen.append("refused")

    thread = threading.Thread(target=hold_a_read)
    thread.start()
    assert inside.wait(5)
    closer = threading.Thread(target=storage.close, kwargs={"backup": False})
    closer.start()
    closer.join(0.2)
    assert closer.is_alive()  # waits for the open read
    release.set()
    closer.join(5)
    thread.join(5)
    assert not closer.is_alive()
    assert seen == [1, "refused"]
