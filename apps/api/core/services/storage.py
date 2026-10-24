from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from django.conf import settings


class StorageBackend(Protocol):
    def save(self, *, filename: str, stream: BinaryIO) -> str:
        """Return storage key/path."""
        ...

    def open(self, key: str) -> Path: ...

    def delete(self, key: str) -> None: ...


class LocalStorageBackend:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or settings.LOCAL_STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, *, filename: str, stream: BinaryIO) -> str:
        key = f"{uuid.uuid4().hex}_{Path(filename).name}"
        dest = self.root / key
        with dest.open("wb") as out:
            shutil.copyfileobj(stream, out)
        return key

    def open(self, key: str) -> Path:
        path = self.root / key
        if not path.exists():
            raise FileNotFoundError(key)
        return path

    def find_unique_named(self, original_name: str) -> Path | None:
        """Return the only stored file whose name ends with this original filename."""
        name = Path(original_name).name
        if not name or not self.root.exists():
            return None
        suffix = f"_{name}"
        matches = [p for p in self.root.iterdir() if p.is_file() and p.name.endswith(suffix)]
        if len(matches) == 1:
            return matches[0]
        return None

    def delete(self, key: str) -> None:
        path = self.root / key
        if path.exists():
            path.unlink()


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend()
    return LocalStorageBackend()
