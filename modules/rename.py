# modules/rename.py

from __future__ import annotations
from pathlib import Path


def safe_rename(path: Path, new_ext_no_dot: str) -> Path | None | Exception:
    """Rename a file to have the given extension, avoiding collisions.

    If the target filename already exists, appends `_1`, `_2`, etc.
    Returns the new Path if renamed, `None` if no change is needed,
    or the caught Exception object if an error occurs.

    Args:
        path (Path): Path to the file to rename.
        new_ext_no_dot (str): New extension without the leading dot.

    Returns:
        Path | None | Exception: Result of the rename operation.
    """
    try:
        normalized = (new_ext_no_dot or "").lower()
        cur_ext = path.suffix[1:].lower() if path.suffix else ""
        if normalized == cur_ext:
            return None

        stem = path.stem if cur_ext else path.name
        parent = path.parent
        candidate = parent / f"{stem}.{normalized}" if normalized else parent / stem

        i = 1
        while candidate.exists():
            candidate = (
                parent / f"{stem}_{i}.{normalized}"
                if normalized
                else parent / f"{stem}_{i}"
            )
            i += 1

        path.rename(candidate)
        return candidate
    except Exception as exc:
        return exc
