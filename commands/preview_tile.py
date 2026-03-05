#!/usr/bin/env python3
"""
preview_tile.py - Render a quick visual preview of a UO art tile

Usage:
  python -m uo_asset_toolkit preview-tile --client <path> --id <art_id> [options]

Options:
  --client PATH     Path to UO client directory
  --id INT          Art tile ID to preview
  --output FILE     Save preview to file instead of showing window
  --scale INT       Display scale factor (default: 2)
  --show-grid       Overlay a pixel grid
  --show-info       Overlay tile metadata (ID, size, mode)
  --compare PATH    Side-by-side comparison with a replacement PNG
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[preview-tile] ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

from core.art_reader import ArtReader


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

CHECKER_LIGHT = (200, 200, 200, 255)
CHECKER_DARK  = (160, 160, 160, 255)
CHECKER_SIZE  = 8


def make_checker(width: int, height: int) -> Image.Image:
    """Create a checkerboard background for alpha-aware preview."""
    bg = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(bg)
    for y in range(0, height, CHECKER_SIZE):
        for x in range(0, width, CHECKER_SIZE):
            col = CHECKER_LIGHT if ((x // CHECKER_SIZE + y // CHECKER_SIZE) % 2 == 0) else CHECKER_DARK
            draw.rectangle([x, y, x + CHECKER_SIZE - 1, y + CHECKER_SIZE - 1], fill=col)
    return bg


def apply_grid(img: Image.Image) -> Image.Image:
    """Draw a 1-pixel grid over each source pixel (after scaling)."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for x in range(0, w, CHECKER_SIZE):
        draw.line([(x, 0), (x, h)], fill=(80, 80, 80, 128))
    for y in range(0, h, CHECKER_SIZE):
        draw.line([(0, y), (w, y)], fill=(80, 80, 80, 128))
    return img


def overlay_info(img: Image.Image, tile_id: int, orig_w: int, orig_h: int, mode: str) -> Image.Image:
    """Stamp tile metadata in the top-left corner."""
    draw = ImageDraw.Draw(img)
    text = f"ID:{tile_id}  {orig_w}x{orig_h}  {mode}"
    # Shadow
    draw.text((2, 2), text, fill=(0, 0, 0, 200))
    draw.text((1, 1), text, fill=(255, 255, 0, 255))
    return img


def build_preview(
    tile_img: Image.Image,
    tile_id: int,
    scale: int,
    show_grid: bool,
    show_info: bool,
) -> Image.Image:
    """Compose the final preview image for a single tile."""
    orig_w, orig_h = tile_img.size

    # Scale up
    new_w, new_h = orig_w * scale, orig_h * scale
    scaled = tile_img.resize((new_w, new_h), Image.NEAREST)

    # Checker background
    bg = make_checker(new_w, new_h)
    bg.paste(scaled, (0, 0), scaled if scaled.mode == "RGBA" else None)
    result = bg.convert("RGBA")

    if show_grid:
        result = apply_grid(result)

    if show_info:
        result = overlay_info(result, tile_id, orig_w, orig_h, tile_img.mode)

    return result


def build_comparison(
    tile_img: Image.Image,
    compare_img: Image.Image,
    tile_id: int,
    scale: int,
    show_info: bool,
) -> Image.Image:
    """Build a side-by-side comparison: original (left) vs replacement (right)."""
    left  = build_preview(tile_img, tile_id, scale, False, show_info)
    right = build_preview(compare_img.convert("RGBA"), tile_id, scale, False, False)

    # Match heights
    max_h = max(left.size[1], right.size[1])
    gap   = 4
    total_w = left.size[0] + gap + right.size[0]

    canvas = Image.new("RGBA", (total_w, max_h), (40, 40, 40, 255))
    canvas.paste(left,  (0, 0))
    canvas.paste(right, (left.size[0] + gap, 0))

    draw = ImageDraw.Draw(canvas)
    draw.text((2,               max_h - 12), "original",    fill=(255, 255, 255, 200))
    draw.text((left.size[0] + gap + 2, max_h - 12), "replacement", fill=(255, 255, 255, 200))

    return canvas


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    client_path = Path(args.client)
    if not client_path.is_dir():
        print(f"[preview-tile] ERROR: Client path not found: {client_path}", file=sys.stderr)
        sys.exit(1)

    reader = ArtReader(client_path)
    tile_img = reader.read_art_item(client_path, args.id)

    if tile_img is None:
        print(f"[preview-tile] ERROR: Tile ID {args.id} not found in client data.", file=sys.stderr)
        sys.exit(1)

    if args.compare:
        compare_path = Path(args.compare)
        if not compare_path.is_file():
            print(f"[preview-tile] ERROR: Compare file not found: {compare_path}", file=sys.stderr)
            sys.exit(1)
        compare_img = Image.open(compare_path)
        result = build_comparison(tile_img, compare_img, args.id, args.scale, args.show_info)
    else:
        result = build_preview(tile_img, args.id, args.scale, args.show_grid, args.show_info)

    if args.output:
        out_path = Path(args.output)
        result.save(str(out_path))
        print(f"[preview-tile] Saved preview to: {out_path}")
    else:
        result.show(title=f"UO Tile Preview - ID {args.id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="preview-tile",
        description="Render a visual preview of a UO art tile.",
    )
    parser.add_argument("--client",   required=True,  help="UO client directory")
    parser.add_argument("--id",       required=True,  type=int, help="Art tile ID")
    parser.add_argument("--output",   default="",     help="Save to file instead of showing")
    parser.add_argument("--scale",    default=2,      type=int, help="Display scale (default: 2)")
    parser.add_argument("--show-grid",   action="store_true", help="Overlay pixel grid")
    parser.add_argument("--show-info",   action="store_true", help="Overlay tile metadata")
    parser.add_argument("--compare",  default="",     help="Side-by-side comparison PNG path")

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
