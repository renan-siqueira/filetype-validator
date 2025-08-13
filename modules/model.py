# modules/model.py

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Represents the result of a file type detection."""
    ext: str          # normalized extension (no dot)
    mime: str         # best-effort MIME type
    confidence: float # confidence score between 0 and 1
    reason: str       # brief explanation (signature/heuristic)


@dataclass
class ScanRow:
    """Represents a row in the scan report CSV."""
    path: str
    size_bytes: int
    current_ext: str
    detected_ext: str
    detected_mime: str
    confidence: float
    is_match: bool
    action: str       # one of: none | rename | error
    new_path: str
    error: str
    reason: str
