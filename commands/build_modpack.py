# commands/build_modpack.py
# CLI command: diff clean vs modded client, then build a mod pack from changes.

import os
import yaml

CONFIG_PATH = "config.yaml"


def _load_config() -> dict:
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def build_modpack():
    cfg = _load_config()
    clean_path = cfg.get("client", {}).get("clean_path", "")
    modded_path = cfg.get("client", {}).get("modded_path", "")
    modpack_dir = cfg.get("output", {}).get("modpack_dir", "output/modpack")
    workers = cfg.get("scanner", {}).get("parallel_workers", 4)
    mod_name = cfg.get("modpack", {}).get("name", "Custom Shard Graphics")
    mod_author = cfg.get("modpack", {}).get("author", "")
    mod_version = cfg.get("modpack", {}).get("version", "1.0.0")

    for label, path in [("clean", clean_path), ("modded", modded_path)]:
        if not path or not os.path.isdir(path):
            print(f"[build-modpack] {label} client path not found: {path!r}")
            print("Update config.yaml with valid client paths.")
            return

    print(f"[build-modpack] Clean:  {clean_path}")
    print(f"[build-modpack] Modded: {modded_path}")

    from toolkit.client import UOClient
    from toolkit.asset_registry import AssetRegistry
    from toolkit.diff_engine import DiffEngine
    from toolkit.parallel import parallel_map
    from formats.art import read_art_item
    from formats.gumps import read_gump
    from exporters.modpack_builder import build_modpack as _build_modpack

    clean_client = UOClient(clean_path)
    modded_client = UOClient(modded_path)

    # Build art registry from modded index
    registry = AssetRegistry()
    if modded_client.is_mul():
        _, art_idx = modded_client.get_art_files()
        registry.load_from_idx(art_idx)
    else:
        registry.load_range(0, 0x4000)

    ids = registry.all_ids()
    print(f"[build-modpack] Diffing {len(ids)} art assets...")

    diff_engine = DiffEngine()

    def diff_item(asset_id):
        clean_img = read_art_item(clean_path, asset_id)
        modded_img = read_art_item(modded_path, asset_id)
        clean_bytes = clean_img.tobytes() if clean_img else None
        modded_bytes = modded_img.tobytes() if modded_img else None
        result = diff_engine.diff_asset(asset_id, "art", clean_bytes, modded_bytes)
        return (result, modded_img)

    results = parallel_map(diff_item, ids, workers=workers)

    art_changes = []
    for asset_id, (result, modded_img) in results:
        if result.is_changed:
            art_changes.append((asset_id, modded_img))

    print(f"[build-modpack] Found {len(art_changes)} changed art assets")

    _build_modpack(
        art_changes=art_changes,
        gump_changes=[],
        modpack_dir=modpack_dir,
        name=mod_name,
        author=mod_author,
        version=mod_version,
    )

    print(f"[build-modpack] Done. Output: {modpack_dir}")


if __name__ == "__main__":
    build_modpack()
