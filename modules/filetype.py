# modules/filetype.py

from __future__ import annotations
from pathlib import Path
from typing import Tuple
import json
import zipfile

from .model import DetectionResult

# --- basic MIME/extension helpers ------------------------------------------------

_EXT_MIME = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "tiff": "image/tiff",
    "webp": "image/webp",
    "zip": "application/zip",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "epub": "application/epub+zip",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "wav": "audio/wav",
    "avi": "video/x-msvideo",
    "7z": "application/x-7z-compressed",
    "rar": "application/vnd.rar",
    "gz": "application/gzip",
    "bz2": "application/x-bzip2",
    "xz": "application/x-xz",
    "html": "text/html",
    "json": "application/json",
    "txt": "text/plain",
    "bin": "application/octet-stream",
}


def _mime_of(ext: str) -> str:
    """Return the MIME type for a given file extension."""
    return _EXT_MIME.get(ext, "application/octet-stream")


def _result(ext: str, conf: float, reason: str) -> DetectionResult:
    """Create a DetectionResult with normalized extension and clamped confidence."""
    norm = "jpg" if ext == "jpeg" else ext
    return DetectionResult(
        ext=norm,
        mime=_mime_of(norm),
        confidence=max(0.0, min(1.0, conf)),
        reason=reason,
    )


# --- sniffers -------------------------------------------------------------------


def _read_head_tail(p: Path, head_bytes: int = 16384, tail_bytes: int = 2048) -> Tuple[bytes, bytes, int]:
    """Read the head and tail of a file, returning (head, tail, size)."""
    size = p.stat().st_size
    with p.open("rb") as f:
        head = f.read(head_bytes)
        tail = b""
        if size > tail_bytes:
            try:
                f.seek(-tail_bytes, 2)
                tail = f.read(tail_bytes)
            except Exception:
                tail = b""
    return head, tail, size


def _is_pdf(head: bytes, tail: bytes) -> bool:
    return head.startswith(b"%PDF-") and (b"%%EOF" in tail or tail.endswith(b"%%EOF"))


def _is_jpeg(head: bytes) -> bool:
    return head.startswith(b"\xFF\xD8\xFF")


def _is_png(head: bytes) -> bool:
    return head.startswith(b"\x89PNG\r\n\x1a\n")


def _is_gif(head: bytes) -> bool:
    return head.startswith(b"GIF87a") or head.startswith(b"GIF89a")


def _is_tiff(head: bytes) -> bool:
    return head.startswith(b"II*\x00") or head.startswith(b"MM\x00*")


def _is_riff(head: bytes, fourcc: bytes) -> bool:
    return head[:4] == b"RIFF" and len(head) >= 12 and head[8:12] == fourcc


def _is_mp4(head: bytes) -> bool:
    return b"ftyp" in head[:16]


def _is_mp3(head: bytes) -> bool:
    return head.startswith(b"ID3") or (len(head) > 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)


def _is_7z(head: bytes) -> bool:
    return head.startswith(b"7z\xBC\xAF\x27\x1C")


def _is_rar(head: bytes) -> bool:
    return head.startswith(b"Rar!\x1A\x07\x00") or head.startswith(b"Rar!\x1A\x07\x01\x00")


def _is_gz(head: bytes) -> bool:
    return head.startswith(b"\x1F\x8B\x08")


def _is_bz2(head: bytes) -> bool:
    return head.startswith(b"BZh")


def _is_xz(head: bytes) -> bool:
    return head.startswith(b"\xFD7zXZ\x00")


def _maybe_text(ext_hint: str, head: bytes) -> DetectionResult | None:
    """Heuristically detect textual content."""
    try:
        s = head.decode("utf-8", errors="ignore").strip().lower()
    except Exception:
        return None

    if s.startswith("<!doctype html") or s.startswith("<html"):
        return _result("html", 0.8, "html-doctype")

    if s.startswith("{") or s.startswith("["):
        try:
            json.loads(head.decode("utf-8", errors="ignore"))
            return _result("json", 0.7, "json-heuristic")
        except Exception:
            pass

    if ext_hint in ("", "txt") and any(ch in s for ch in ("\n", " ", "\t")):
        return _result("txt", 0.5, "text-heuristic")

    return None


def _zip_family(p: Path) -> DetectionResult | None:
    """Refine generic zip into known subtypes like docx, xlsx, pptx, odt, ods, odp, epub."""
    try:
        with zipfile.ZipFile(p, "r") as z:
            names = set(z.namelist())
            if any(n.startswith("word/") for n in names):
                return _result("docx", 0.98, "zip-ooxml-word")
            if any(n.startswith("xl/") for n in names):
                return _result("xlsx", 0.98, "zip-ooxml-excel")
            if any(n.startswith("ppt/") for n in names):
                return _result("pptx", 0.98, "zip-ooxml-powerpoint")

            if "mimetype" in names:
                try:
                    with z.open("mimetype") as mf:
                        mt = mf.read(200).decode("utf-8", errors="ignore").strip()
                        if mt == "application/vnd.oasis.opendocument.text":
                            return _result("odt", 0.98, "zip-odf-odt")
                        if mt == "application/vnd.oasis.opendocument.spreadsheet":
                            return _result("ods", 0.98, "zip-odf-ods")
                        if mt == "application/vnd.oasis.opendocument.presentation":
                            return _result("odp", 0.98, "zip-odf-odp")
                        if mt == "application/epub+zip":
                            return _result("epub", 0.98, "zip-epub")
                except Exception:
                    pass

            return _result("zip", 0.9, "zip-generic")
    except Exception:
        return None


# --- public API -----------------------------------------------------------------


def detect_filetype(path: Path) -> DetectionResult:
    """Detect the file type of a given path based on magic bytes and heuristics."""
    head, tail, _size = _read_head_tail(path)

    if _is_pdf(head, tail):
        return _result("pdf", 0.99, "pdf-header-trailer")

    if _is_jpeg(head):
        return _result("jpg", 0.99, "jpeg-soi")
    if _is_png(head):
        return _result("png", 0.99, "png-signature")
    if _is_gif(head):
        return _result("gif", 0.99, "gif-signature")
    if _is_tiff(head):
        return _result("tiff", 0.98, "tiff-signature")

    if _is_riff(head, b"WEBP"):
        return _result("webp", 0.98, "riff-webp")
    if _is_riff(head, b"WAVE"):
        return _result("wav", 0.98, "riff-wav")
    if _is_riff(head, b"AVI "):
        return _result("avi", 0.98, "riff-avi")

    if _is_mp4(head):
        return _result("mp4", 0.9, "mp4-ftyp")
    if _is_mp3(head):
        return _result("mp3", 0.85, "mp3-id3-or-framesync")

    if _is_7z(head):
        return _result("7z", 0.99, "7z-signature")
    if _is_rar(head):
        return _result("rar", 0.99, "rar-signature")
    if _is_gz(head):
        return _result("gz", 0.99, "gzip-signature")
    if _is_bz2(head):
        return _result("bz2", 0.99, "bzip2-signature")
    if _is_xz(head):
        return _result("xz", 0.99, "xz-signature")

    if head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        det = _zip_family(path)
        return det if det else _result("zip", 0.9, "zip-generic")

    textish = _maybe_text(path.suffix[1:].lower(), head)
    if textish:
        return textish

    return _result("bin", 0.2, "unknown-fallback")
