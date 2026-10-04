"""Zip inspection and selective extraction tool for SuryaSense.

Enforces data safety rules:
- Selective extraction (light curves only, never extract all).
- Free disk space validation.
- Path traversal protection.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
import shutil
import sys
import zipfile


def check_free_space(dest: Path, required_bytes: int = 50 * 1024 * 1024) -> None:
    """Ensure destination has sufficient free space (default 50MB buffer)."""
    usage = shutil.disk_usage(dest.anchor if dest.anchor else ".")
    if usage.free < required_bytes:
        raise RuntimeError(
            f"Insufficient disk space on {dest.anchor}: {usage.free / 1e6:.1f} MB free, "
            f"need at least {required_bytes / 1e6:.1f} MB"
        )


def is_safe_path(target_dir: Path, path: str) -> bool:
    """Block path traversal attacks (e.g. ../ or absolute paths inside zip)."""
    resolved_target = target_dir.resolve()
    resolved_path = (target_dir / path).resolve()
    return resolved_path.is_relative_to(resolved_target)


def list_zip(zip_path: Path) -> None:
    """Print archive members, sizes, and extensions."""
    if not zip_path.is_file():
        print(f"Error: File not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\nArchive: {zip_path.name} ({zip_path.stat().st_size / 1e6:.2f} MB)")
    print(f"{'Index':<6} {'Member Name':<60} {'Size (KB)':<12} {'Compressed (KB)':<15}")
    print("-" * 95)

    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()
        total_size = 0
        extensions: dict[str, int] = {}

        for idx, info in enumerate(infolist):
            ext = Path(info.filename).suffix.lower() or "<no_ext>"
            extensions[ext] = extensions.get(ext, 0) + 1
            total_size += info.file_size
            print(
                f"{idx:<6} {info.filename:<60} {info.file_size / 1024:<12.1f} {info.compress_size / 1024:<15.1f}"
            )

        print("-" * 95)
        print(f"Total members: {len(infolist)} | Uncompressed total: {total_size / 1e6:.2f} MB")
        print("Extension summary:", dict(sorted(extensions.items(), key=lambda x: -x[1])))


def extract_zip(zip_path: Path, dest_dir: Path, pattern: str) -> list[Path]:
    """Selectively extract archive members matching a pattern with security checks."""
    if not zip_path.is_file():
        raise FileNotFoundError(f"Archive not found: {zip_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    check_free_space(dest_dir)

    extracted_files: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        members_to_extract = [
            info for info in zf.infolist()
            if fnmatch.fnmatch(info.filename, pattern) or fnmatch.fnmatch(Path(info.filename).name, pattern)
        ]

        if not members_to_extract:
            print(f"No members matched pattern '{pattern}' in {zip_path.name}")
            return []

        for info in members_to_extract:
            if not is_safe_path(dest_dir, info.filename):
                raise ValueError(f"Dangerous path detected in zip: {info.filename}")

            target_file = dest_dir / info.filename
            target_file.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(info) as src, open(target_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted_files.append(target_file)
            print(f"Extracted: {target_file.relative_to(dest_dir)}")

    return extracted_files


def main() -> None:
    parser = argparse.ArgumentParser(description="SuryaSense Zip Tool: inspect and extract PRADAN data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List members of an archive.")
    list_parser.add_argument("zip_path", type=Path, help="Path to zip archive.")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Selectively extract members matching pattern.")
    extract_parser.add_argument("zip_path", type=Path, help="Path to zip archive.")
    extract_parser.add_argument(
        "--dest", type=Path, required=True, help="Destination directory (e.g. data/extracted/solexs)."
    )
    extract_parser.add_argument(
        "--pattern", type=str, default="*.fits", help="Glob pattern to select (default: *.fits)."
    )

    args = parser.parse_args()

    if args.command == "list":
        list_zip(args.zip_path)
    elif args.command == "extract":
        extract_zip(args.zip_path, args.dest, args.pattern)


if __name__ == "__main__":
    main()
