# modules/walk.py

from __future__ import annotations
from pathlib import Path
from typing import Iterator


def iter_files(root: Path) -> Iterator[Path]:
    """Iterate over all files in a path, recursively if it's a directory.

    Args:
        root (Path): File or directory to scan.

    Yields:
        Path: Paths to each file found.
    """
    if root.is_file():
        yield root
        return

    for p in root.rglob("*"):
        if p.is_file():
            yield p
