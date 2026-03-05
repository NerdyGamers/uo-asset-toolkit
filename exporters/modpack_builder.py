# exporters/modpack_builder.py
# Builds a distributable mod pack from diff results.
# Output structure:
#   output/modpack/
#     art/      <- modified item sprites
#     gumps/    <- modified gump images
#     mod.json  <- metadata manifest

import os
import json
from typing import List, Dict, Optional
from PIL import Image
from .png_exporter import export_image


MODPACK_DIR = "output/modpack"


def build_modpack(
    art_changes: List[tuple],    # [(asset_id, PIL.Image or None), ...]
    gump_changes: List[tuple],   # [(asset_id, PIL.Image or None), ...]
    modpack_dir: str = MODPACK_DIR,
    name: str = "Custom Shard Graphics",
    author: str = "",
    version: str = "1.0.0",
) -> str:
    """
    Export modified art and gump assets to modpack_dir and write mod.json.
    Returns path to mod.json.
    """
    art_dir = os.path.join(modpack_dir, "art")
    gump_dir = os.path.join(modpack_dir, "gumps")
    os.makedirs(art_dir, exist_ok=True)
    os.makedirs(gump_dir, exist_ok=True)

    exported_items = []
    for asset_id, img in art_changes:
        if img is not None:
            export_image(img, art_dir, asset_id)
            exported_items.append(asset_id)

    exported_gumps = []
    for asset_id, img in gump_changes:
        if img is not None:
            export_image(img, gump_dir, asset_id)
            exported_gumps.append(asset_id)

    manifest = {
        "name": name,
        "author": author,
        "version": version,
        "items": exported_items,
        "gumps": exported_gumps,
    }

    json_path = os.path.join(modpack_dir, "mod.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[ModpackBuilder] Written {len(exported_items)} items, "
          f"{len(exported_gumps)} gumps -> {json_path}")
    return json_path
