# exporters/png_exporter.py
# Exports PIL Images to PNG files with consistent naming and directory structure.

import os
from typing import Optional
from PIL import Image


def export_image(
    img: Image.Image,
    output_dir: str,
    asset_id: int,
    prefix: str = "",
    suffix: str = "",
) -> str:
    """
    Save a PIL Image to output_dir as a PNG.
    Filename format: {prefix}0x{asset_id:04X}{suffix}.png
    Returns the full path of the written file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{prefix}0x{asset_id:04X}{suffix}.png"
    path = os.path.join(output_dir, filename)
    img.save(path, "PNG")
    return path


def export_batch(
    images: list,  # list of (asset_id, PIL.Image) tuples
    output_dir: str,
    prefix: str = "",
) -> list:
    """
    Export a batch of (asset_id, image) pairs to PNG files.
    Returns list of written file paths.
    Skips None images silently.
    """
    written = []
    for asset_id, img in images:
        if img is None:
            continue
        path = export_image(img, output_dir, asset_id, prefix=prefix)
        written.append(path)
    return written
