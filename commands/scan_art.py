# commands/scan_art.py
# CLI command: scan art assets from the configured modded client.

import os
import yaml
from tqdm import tqdm

CONFIG_PATH = "config.yaml"


def _load_config() -> dict:
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def scan_art():
    cfg = _load_config()
    client_path = cfg.get("client", {}).get("modded_path", "")
    output_dir = cfg.get("output", {}).get("items_dir", "output/items")
    workers = cfg.get("scanner", {}).get("parallel_workers", 4)

    if not client_path or not os.path.isdir(client_path):
        print(f"[scan-art] Client path not found: {client_path!r}")
        print("Update 'client.modded_path' in config.yaml")
        return

    print(f"[scan-art] Client: {client_path}")
    print(f"[scan-art] Output: {output_dir}")

    from toolkit.asset_registry import AssetRegistry
    from toolkit.client import UOClient
    from toolkit.parallel import parallel_map
    from formats.art import read_art_item
    from exporters.png_exporter import export_image

    client = UOClient(client_path)
    registry = AssetRegistry()

    if client.is_mul():
        _, idx_path = client.get_art_files()
        # idx is the second element for MUL
        art_mul, art_idx = client.get_art_files()
        count = registry.load_from_idx(art_idx)
        print(f"[scan-art] Registry loaded {count} valid entries from index")
    else:
        # UOP fallback: use configured range
        start = cfg.get("scanner", {}).get("art_range_start", 0)
        end = cfg.get("scanner", {}).get("art_range_end", 0x4000)
        registry.load_range(start, end)
        print(f"[scan-art] UOP client detected, using range scan {hex(start)}-{hex(end)}")

    ids = registry.all_ids()
    print(f"[scan-art] Scanning {len(ids)} asset IDs with {workers} workers...")

    def read_fn(asset_id):
        return read_art_item(client_path, asset_id)

    results = parallel_map(read_fn, ids, workers=workers)

    exported = 0
    os.makedirs(output_dir, exist_ok=True)
    for asset_id, img in tqdm(results, desc="Exporting"):
        if img is not None:
            export_image(img, output_dir, asset_id)
            exported += 1

    print(f"[scan-art] Done. Exported {exported}/{len(ids)} assets -> {output_dir}")


if __name__ == "__main__":
    scan_art()
