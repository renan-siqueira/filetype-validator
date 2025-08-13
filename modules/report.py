# modules/report.py

from __future__ import annotations
import csv
from pathlib import Path
from typing import Iterable

from .model import ScanRow


def write_csv(out_path: Path, rows: Iterable[ScanRow]) -> None:
    """Write scan results to a CSV file.

    Args:
        out_path (Path): Destination CSV file path.
        rows (Iterable[ScanRow]): Sequence of scan result rows.

    Returns:
        None
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "path", "size_bytes", "current_ext", "detected_ext", "detected_mime",
            "confidence", "is_match", "action", "new_path", "error", "reason"
        ])
        for r in rows:
            writer.writerow([
                r.path,
                r.size_bytes,
                r.current_ext,
                r.detected_ext,
                r.detected_mime,
                f"{r.confidence:.2f}",
                str(r.is_match).lower(),
                r.action,
                r.new_path,
                r.error,
                r.reason
            ])
