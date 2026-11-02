"""The student's own media (ADR-0011): the image files of own cards, one store per profile.

- Files sit in the profile's media/ folder, beside user.db (ProfilePaths.media_dir), under
  content-addressed names: the sha256 of the bytes in hex plus the reference's extension,
  e.g. `3f0c...9a.svg`. The same bytes are stored once. A file is never changed or
  deleted, so an older backup of user.db (BAK-3) still finds every image it maps.
- The table user_media maps each image reference of an own card, as written in its text
  (`media/graph.svg`), to the file it shows. Imports, the editor and .meprofile export
  and import all go through UserMedia.
- A file is written (atomically, fsynced) before the rows that point at it commit, so a
  crash can leave a file nothing points at, never a reference to a missing file.
- Names are checked before they become paths: by the rule .meprofile export and import
  apply to every entry (`unsafe_name`), plus the content-address shape. A .meprofile is
  untrusted input, so its user_media rows are checked the same way on import.
"""

# ruff: noqa: S608 -- table and column names come from our own constants; values are always bound parameters.

import hashlib
import os
import re
import sqlite3
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from core.model import CardMedia
from core.storage import rows
from core.storage.connection import Database, fsync_path, full_fsync
from core.storage.errors import MediaError

MEDIA_DIR = "media"
MAX_NAME_BYTES = 512
FILE_NAME = re.compile(r"([0-9a-f]{64})(?:\.([a-z0-9]{1,8}))?")
_EXTENSION = re.compile(r"[a-z0-9]{1,8}")


def unsafe_name(name: str) -> bool:
    """The rule for every entry name of a .meprofile (and so for every stored file): a
    relative POSIX path without empty, '.' or '..' parts, backslashes or NULs, at most
    512 bytes."""
    return (
        not name
        or "\\" in name
        or "\x00" in name
        or PurePosixPath(name).is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
        or len(name.encode()) > MAX_NAME_BYTES
    )


def media_file_name(data: bytes, ref: str) -> str:
    """The content-addressed name of `data`, keeping the extension of the reference."""
    suffix = PurePosixPath(ref.replace("\\", "/")).suffix.lower().removeprefix(".")
    digest = hashlib.sha256(data).hexdigest()
    return f"{digest}.{suffix}" if _EXTENSION.fullmatch(suffix) else digest


def check_file_name(name: str) -> str:
    """`name` if it is a content-addressed media file name safe to use as a path."""
    if not FILE_NAME.fullmatch(name) or unsafe_name(f"{MEDIA_DIR}/{name}"):
        raise MediaError(f"not a media file name: {name!r}")
    return name


def check_ref(ref: str) -> str:
    """`ref` if it can be a card's image reference (a key, never a path)."""
    if not ref or not ref.strip() or "\x00" in ref or len(ref.encode()) > MAX_NAME_BYTES:
        raise MediaError(f"not an image reference: {ref!r}")
    return ref


def digest_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_intact(path: Path, name: str) -> bool:
    """The file exists and its bytes still hash to its name."""
    match = FILE_NAME.fullmatch(name)
    return match is not None and path.is_file() and digest_of(path) == match.group(1)


class UserMedia:
    """One profile's own media: files in `folder` and the user_media rows of `db`."""

    def __init__(self, db: Database, folder: Path | None = None) -> None:
        self._db = db
        self.folder = folder if folder is not None else db.path.parent / MEDIA_DIR

    # ------------------------------------------------------------ files

    def path(self, name: str) -> Path:
        return self.folder / check_file_name(name)

    def add(self, data: bytes, ref: str) -> str:
        """Store `data` (an image `ref` points at) and return its file name. Storing the
        same bytes again finds the file already there; a damaged copy is replaced."""
        check_ref(ref)
        name = media_file_name(data, ref)
        target = self.path(name)
        if file_intact(target, name):
            return name
        self.folder.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.folder, prefix=".incoming-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                full_fsync(handle.fileno())
            Path(tmp).replace(target)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        fsync_path(self.folder)
        return name

    def add_all(self, images: Mapping[str, bytes]) -> dict[str, str]:
        """Store several images: {ref: bytes} -> {ref: file name}."""
        return {ref: self.add(data, ref) for ref, data in images.items()}

    def read_file(self, name: str) -> bytes | None:
        path = self.path(name)
        return path.read_bytes() if path.is_file() else None

    # ------------------------------------------------------------ references

    def links(self, card_id: str) -> dict[str, str]:
        """{image reference: file name} of one own card."""
        with self._db.reading() as conn:
            found = rows.select(conn, CardMedia, "card_id = ?", (card_id,))
        return {m.ref: m.file for m in found}

    def all_links(self) -> list[CardMedia]:
        with self._db.reading() as conn:
            return rows.select(conn, CardMedia)

    def read(self, card_id: str, ref: str) -> bytes | None:
        """The bytes an own card's image reference shows, or None when it has none."""
        name = self.links(card_id).get(ref)
        return None if name is None else self.read_file(name)

    def link(self, card_id: str, files: Mapping[str, str]) -> None:
        """Set an own card's image references to stored files ({ref: file name}),
        replacing its earlier ones. Every file must be in the store already."""
        records = [
            CardMedia(card_id=card_id, ref=check_ref(ref), file=check_file_name(name))
            for ref, name in sorted(files.items())
        ]
        missing = [m.file for m in records if not self.path(m.file).is_file()]
        if missing:
            raise MediaError(f"card {card_id}: no stored media file {missing[0]}")
        table = rows.table_for(CardMedia)

        def write(conn: sqlite3.Connection) -> None:
            conn.execute(f"DELETE FROM {table.name} WHERE card_id = ?", (card_id,))
            for record in records:
                rows.insert_row(conn, table, rows.to_row(record))

        self._db.write(write)

    def set_card_media(self, card_id: str, images: Mapping[str, bytes]) -> dict[str, str]:
        """Store an own card's images ({ref: bytes}) and point its references at them,
        replacing its earlier ones (what the editor saves). Returns {ref: file name}."""
        names = self.add_all(images)
        self.link(card_id, names)
        return names

    def problems(self) -> list[str]:
        """References whose file is missing, misnamed or damaged (none, normally)."""
        out = []
        for m in self.all_links():
            try:
                ok = file_intact(self.path(m.file), m.file)
            except MediaError:
                ok = False
            if not ok:
                out.append(f"card {m.card_id}: {m.ref} -> {m.file} is missing or damaged")
        return out
