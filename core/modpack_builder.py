"""
core/modpack_builder.py - Assemble a distributable UO mod-pack from changed assets

A mod-pack is a directory containing:
  manifest.json      - machine-readable list of all changes
  art/               - modified art tile PNGs  (named <id>.png)
  gumps/             - modified gump PNGs      (named <id>.png)
  README.txt         - human-readable change summary

Public API
----------
ModpackBuilder.build(
    art_changes   = [(asset_id, PIL.Image), ...],
    gump_changes  = [(asset_id, PIL.Image), ...],
    modpack_dir   = Path("output/MyMod"),
    name          = "MyMod",
    author        = "Author",
    version       = "1.0.0",
)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError("Pillow is required: pip install Pillow") from exc


# ---------------------------------------------------------------------------
# ModpackBuilder
# ---------------------------------------------------------------------------

class ModpackBuilder:
    """Assembles a finished mod-pack directory from changed asset lists."""

    @staticmethod
    def build(
        art_changes:  list[tuple[int, Optional[Image.Image]]],
        gump_changes: list[tuple[int, Optional[Image.Image]]],
        modpack_dir,
        name:    str = "UOMod",
        author:  str = "Unknown",
        version: str = "1.0.0",
    ) -> Path:
        """
        Build a mod-pack directory.

        Parameters
        ----------
        art_changes  : list of (art_id, PIL.Image or None)
                       None means the tile was deleted.
        gump_changes : list of (gump_id, PIL.Image or None)
                       None means the gump was deleted.
        modpack_dir  : output directory (created if needed)
        name         : mod display name
        author       : mod author name
        version      : version string (semver recommended)

        Returns
        -------
        Path to the finished mod-pack directory.
        """
        out = Path(modpack_dir)
        out.mkdir(parents=True, exist_ok=True)

        art_dir   = out / "art"
        gump_dir  = out / "gumps"
        art_dir.mkdir(exist_ok=True)
        gump_dir.mkdir(exist_ok=True)

        manifest_art   = []
        manifest_gumps = []

        # ---- Art tiles ---------------------------------------------------
        for asset_id, img in art_changes:
            if img is not None:
                filename = f"{asset_id}.png"
                img.save(str(art_dir / filename))
                manifest_art.append({
                    "id":     asset_id,
                    "file":   f"art/{filename}",
                    "status": "modified",
                })
            else:
                manifest_art.append({
                    "id":     asset_id,
                    "file":   None,
                    "status": "deleted",
                })

        # ---- Gumps -------------------------------------------------------
        for gump_id, img in gump_changes:
            if img is not None:
                filename = f"{gump_id}.png"
                img.save(str(gump_dir / filename))
                manifest_gumps.append({
                    "id":     gump_id,
                    "file":   f"gumps/{filename}",
                    "status": "modified",
                })
            else:
                manifest_gumps.append({
                    "id":     gump_id,
                    "file":   None,
                    "status": "deleted",
                })

        # ---- manifest.json -----------------------------------------------
        manifest = {
            "name":       name,
            "author":     author,
            "version":    version,
            "built_at":   datetime.now(timezone.utc).isoformat(),
            "art":        manifest_art,
            "gumps":      manifest_gumps,
            "summary": {
                "art_modified":   sum(1 for e in manifest_art   if e["status"] == "modified"),
                "art_deleted":    sum(1 for e in manifest_art   if e["status"] == "deleted"),
                "gumps_modified": sum(1 for e in manifest_gumps if e["status"] == "modified"),
                "gumps_deleted":  sum(1 for e in manifest_gumps if e["status"] == "deleted"),
            },
        }

        manifest_path = out / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        # ---- README.txt --------------------------------------------------
        readme_lines = [
            f"{name}  v{version}",
            f"Author : {author}",
            f"Built  : {manifest['built_at']}",
            "",
            "Changes",
            "-------",
            f"  Art tiles  modified : {manifest['summary']['art_modified']}",
            f"  Art tiles  deleted  : {manifest['summary']['art_deleted']}",
            f"  Gumps      modified : {manifest['summary']['gumps_modified']}",
            f"  Gumps      deleted  : {manifest['summary']['gumps_deleted']}",
            "",
            "Installation",
            "------------",
            "Copy the contents of this folder into your UO mod-pack loader's",
            "import directory and reload the client.",
            "",
            "Files",
            "-----",
            "  manifest.json  - machine-readable change list",
            "  art/           - modified art tile PNGs",
            "  gumps/         - modified gump PNGs",
        ]
        (out / "README.txt").write_text("\n".join(readme_lines), encoding="utf-8")

        return out
