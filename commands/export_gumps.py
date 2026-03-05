#!/usr/bin/env python3
"""
export_gumps.py - Export Ultima Online gump images from gumpart.mul/uop

Usage:
  python -m uo_asset_toolkit export-gumps --client <path> --output <dir> [options]

Options:
  --client PATH     Path to UO client directory
  --output DIR      Output directory for exported PNGs
  --ids LIST        Comma-separated gump IDs to export (default: all)
  --format FMT      Output format: png (default), bmp, tga
  --workers N       Parallel workers (default: 4)
  --no-alpha        Strip alpha channel from output images
  --verbose         Show per-gump export progress
"""

import argparse
import sys
from pathlib import Path

from core.gump_reader import GumpReader
from core.parallel_utils import parallel_map


def parse_ids(ids_str: str) -> list[int]:
    """Parse a comma-separated string of gump IDs."""
    try:
        return [int(x.strip()) for x in ids_str.split(",") if x.strip()]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid ID list: {e}")


def export_gump(
    gump_id: int,
    reader: GumpReader,
    output_dir: Path,
    fmt: str,
    no_alpha: bool,
    verbose: bool,
) -> tuple[int, bool, str]:
    """
    Export a single gump image to disk.

    Returns:
        (gump_id, success, message)
    """
    try:
        img = reader.read(gump_id)
        if img is None:
            return (gump_id, False, "not found")

        if no_alpha and img.mode == "RGBA":
            img = img.convert("RGB")

        filename = output_dir / f"gump_{gump_id:05d}.{fmt}"
        img.save(str(filename))

        if verbose:
            print(f"  [export-gumps] Exported gump {gump_id:05d} -> {filename.name}")

        return (gump_id, True, str(filename))
    except Exception as exc:
        return (gump_id, False, str(exc))


def run(args: argparse.Namespace) -> None:
    client_path = Path(args.client)
    output_dir = Path(args.output)

    if not client_path.is_dir():
        print(f"[export-gumps] ERROR: Client path not found: {client_path}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[export-gumps] Loading gump data from: {client_path}")
    reader = GumpReader(client_path)

    # Determine which IDs to export
    if args.ids:
        ids = parse_ids(args.ids)
    else:
        ids = reader.get_all_ids()

    total = len(ids)
    print(f"[export-gumps] Found {total} gumps to export")

    fmt = args.format.lower()
    no_alpha = args.no_alpha
    verbose = args.verbose

    def export_item(gump_id: int):
        return export_gump(gump_id, reader, output_dir, fmt, no_alpha, verbose)

    results = parallel_map(export_item, ids, workers=args.workers)

    exported = sum(1 for _, ok, _ in results if ok)
    failed = [(gid, msg) for gid, ok, msg in results if not ok]

    print(f"[export-gumps] Done. Exported {exported}/{total} gumps to: {output_dir}")

    if failed:
        print(f"[export-gumps] WARNING: {len(failed)} gumps failed:")
        for gid, msg in failed[:10]:
            print(f"  gump {gid:05d}: {msg}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="export-gumps",
        description="Export UO gump images to PNG/BMP/TGA files.",
    )
    parser.add_argument("--client", required=True, help="UO client directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--ids", default="", help="Comma-separated gump IDs (default: all)")
    parser.add_argument("--format", default="png", choices=["png", "bmp", "tga"],
                        help="Output image format (default: png)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    parser.add_argument("--no-alpha", action="store_true", help="Strip alpha channel")
    parser.add_argument("--verbose", action="store_true", help="Verbose per-gump output")

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
