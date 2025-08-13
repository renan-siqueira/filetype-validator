# main.py

"""
Orchestrator: read params (JSON + CLI), walk files, detect types, write CSV, optionally rename.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from modules.model import ScanRow
from modules.walk import iter_files
from modules.filetype import detect_filetype
from modules.report import write_csv
from modules.rename import safe_rename


def load_config(path: Path | None) -> Dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        path (Path | None): Path to the JSON configuration file.

    Returns:
        Dict[str, Any]: Configuration dictionary. Empty if no file is provided or read fails.
    """
    if not path:
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[WARN] Failed to read config {path}: {exc}", file=sys.stderr)
        return {}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    p = argparse.ArgumentParser(
        description="Validate and (optionally) fix extensions based on file content."
    )
    p.add_argument("--input", type=str, help="Input file or directory (recursive).")
    p.add_argument("--report", type=str, help="Path to CSV report (default: report.csv).")
    p.add_argument("--rename", action="store_true", help="Rename files to the detected correct extension.")
    p.add_argument("--config", type=str, help="Optional JSON config (flags override).")
    return p.parse_args()


def _get_effective_config(args: argparse.Namespace) -> Tuple[Dict[str, Any], Path]:
    """Load CLI + JSON configuration, giving precedence to CLI flags."""
    script_dir = Path(__file__).parent
    default_config_path = script_dir / "params.json"
    config_path = Path(args.config) if args.config else default_config_path
    cfg = load_config(config_path if config_path.exists() else None)
    return cfg, config_path


def _resolve_paths(args: argparse.Namespace, cfg: Dict[str, Any], config_path: Path) -> Tuple[Path, Path, bool]:
    """Resolve and validate input and output paths."""
    input_path = Path(args.input or cfg.get("input", ""))
    if not str(input_path):
        print(f"[ERR] --input is required (or set 'input' in {config_path.name}).", file=sys.stderr)
        raise SystemExit(2)
    if not input_path.exists():
        print(f"[ERR] Input not found: {input_path}", file=sys.stderr)
        raise SystemExit(2)

    report_path = Path(args.report or cfg.get("report", "report.csv"))
    do_rename = bool(args.rename or cfg.get("rename", False))
    return input_path, report_path, do_rename


def process_file(
    fp: Path,
    do_rename: bool,
    total: int,
    renamed: int,
    mismatches: int,
    errors: int
) -> Tuple[int, int, int, int, ScanRow]:
    """Process a single file and return updated counters plus ScanRow."""
    total += 1
    try:
        det = detect_filetype(fp)
        current_ext = fp.suffix[1:].lower() if fp.suffix else ""
        is_match = (current_ext == det.ext) if current_ext else False

        action = "none"
        new_path_str = ""
        err_str = ""

        if do_rename and det.confidence >= 0.8 and det.ext and current_ext != det.ext:
            new_path = safe_rename(fp, det.ext)
            if isinstance(new_path, Exception):
                action = "error"
                err_str = f"{type(new_path).__name__}: {new_path}"
                errors += 1
            elif new_path is None:
                action = "none"
            else:
                action = "rename"
                new_path_str = str(new_path)
                renamed += 1
                current_ext = det.ext
                is_match = True

        if not is_match:
            mismatches += 1

        row = ScanRow(
            path=str(fp),
            size_bytes=fp.stat().st_size if fp.exists() else 0,
            current_ext=current_ext,
            detected_ext=det.ext,
            detected_mime=det.mime,
            confidence=det.confidence,
            is_match=is_match,
            action=action,
            new_path=new_path_str,
            error=err_str,
            reason=det.reason,
        )
    except Exception as exc:
        errors += 1
        row = ScanRow(
            path=str(fp),
            size_bytes=fp.stat().st_size if fp.exists() else 0,
            current_ext=fp.suffix[1:].lower() if fp.suffix else "",
            detected_ext="",
            detected_mime="",
            confidence=0.0,
            is_match=False,
            action="error",
            new_path="",
            error=f"{type(exc).__name__}: {exc}",
            reason="exception",
        )

    return total, renamed, mismatches, errors, row


def _print_summary(
    report_path: Path,
    total: int,
    mismatches: int,
    renamed: int,
    errors: int,
    do_rename: bool
) -> None:
    """Print summary information to stdout."""
    print(f"[INFO] Done. Total: {total} | Mismatches: {mismatches} | Renamed: {renamed} | Errors: {errors}")
    print(f"[INFO] Report: {report_path.resolve()}")
    if do_rename:
        print("[INFO] Rename was enabled. See 'action' and 'new_path' columns for results.")
    else:
        print("[INFO] Rename was NOT enabled (dry-run mode).")


def main() -> int:
    """Main orchestration function.

    Returns:
        int: Exit code.
    """
    args = parse_args()
    cfg, config_path = _get_effective_config(args)
    input_path, report_path, do_rename = _resolve_paths(args, cfg, config_path)

    rows: List[ScanRow] = []
    total = renamed = mismatches = errors = 0

    print(f"[INFO] Scanning: {input_path}")
    for fp in iter_files(input_path):
        total, renamed, mismatches, errors, row = process_file(fp, do_rename, total, renamed, mismatches, errors)
        rows.append(row)

    write_csv(report_path, rows)
    _print_summary(report_path, total, mismatches, renamed, errors, do_rename)

    if errors:
        return 3
    if mismatches and not do_rename:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
